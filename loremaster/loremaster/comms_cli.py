"""Read-only comms CLI (packet 05a-iii) — the idle-gate hook bridge.

Reports a registered agent's PENDING state — unread messages, unacked directives,
and brief-ack skew — against the CONFIGURED store coordinate, so a ``TeammateIdle``
hook can gate on real fleet state inside its ~10s budget without spinning up the
full MCP server.

Two invariants are load-bearing and are pinned in ``test_comms_cli.py``:

* **READ-ONLY BY CONSTRUCTION.** This module never issues ``CREATE`` / ``UPDATE`` /
  ``DELETE`` / ``RELATE`` / ``UPSERT`` / ``INSERT`` — it composes over the shipped
  ledgers' READ methods (``AgentRegistry.get_agent``,
  ``MessageLedger.pending_traffic``, ``BriefLedger.get_head`` / ``acked_version``),
  each a plain ``SELECT``. A hook that could mutate the fleet ledger while merely
  *checking* it is a footgun; the forbidden verbs are asserted absent from this
  source, and the whole-database content is asserted byte-identical across a run.
* **STORE COORDINATE COMES FROM CONFIG, NEVER HARDCODED.** The production store
  coordinate (``:18500``) must NEVER appear as a literal here — the coordinate is
  resolved from the project ``lore.yaml`` via the SHARED
  :class:`loremaster.config.SurrealConfig` +
  :attr:`loremaster.config.LoreConfig.effective_surreal_database` resolver (ONE
  IMPLEMENTATION — never a cloned coordinate resolver), or from explicit
  ``--url``/``--namespace``/``--database`` overrides. A dev/test invocation reads
  the dev/test store and a production invocation reads production, without a code
  change.

The default (no ``--url``) config load uses the ENV-FREE
:meth:`loremaster.config.LoreConfig.model_validate`, NOT
:func:`loremaster.config.load_config`: this creds-free read-only bridge never uses
the Anthropic key, yet ``load_config`` resolves ``anthropic.api_key_env`` EAGERLY
and would abort boot when that key is unset (the idle-gate hook's stripped-env
reality — Fable ruling FORK 2 rider 3).

Unix philosophy: SILENT on success (the counts line only), LOUD on failure.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple

import yaml
from pydantic import SecretStr

from loremaster.agents import AgentRegistry
from loremaster.briefs import STANDING_BRIEF, BriefLedger, UnknownBriefError
from loremaster.config import LoreConfig, resolve_config_value, resolve_secret
from loremaster.messages import MessageLedger


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m loremaster.comms_cli",
        description="Read-only pending-traffic reporter for the comms subsystem.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    pending = subcommands.add_parser(
        "pending",
        help="report an agent's unread / unacked-directive / brief-skew counts",
    )
    pending.add_argument(
        "--agent",
        required=True,
        help="the registered agent name whose pending state to report",
    )
    # Explicit store-coordinate OVERRIDES. Each defaults to None ⇒ resolve from
    # the project ``lore.yaml`` (via the shared SurrealConfig resolver). The
    # overrides exist so a hook (and the contract's integration pin) can target a
    # specific store/database deterministically. ⚠ A production coordinate is
    # passed HERE, never hardcoded.
    pending.add_argument("--url", default=None, help="store RPC URL override")
    pending.add_argument("--namespace", default=None, help="store namespace override")
    pending.add_argument("--database", default=None, help="store database override")
    pending.add_argument("--user", default=None, help="store user override")
    pending.add_argument("--password", default=None, help="store password override")
    # The project lore.yaml the DEFAULT (no --url) coordinate/credential resolution
    # reads. Passed EXPLICITLY (the idle-gate hook's shell resolves $LORE_CONFIG and
    # forwards it) — so this tool never reads the environment itself (the one
    # secret-resolution module owns env access; packet 42).
    pending.add_argument("--config", default=None, help="path to the project lore.yaml")
    return parser


class _ResolvedCoordinate(NamedTuple):
    """The store LOCATION a ``pending`` run connects to — the triple that decides
    WHICH store/database (the safety-relevant identity: never ``:18500`` by
    accident, and dev/test reads dev/test). Resolved either from explicit
    ``--url/--namespace/--database`` overrides or (default) from the project's
    ``lore.yaml`` surreal block via the SHARED
    :class:`loremaster.config.SurrealConfig` resolver — never a cloned resolver.
    Credential resolution is a separate connect-time concern and not part of this
    location triple.
    """

    url: str | None
    namespace: str | None
    database: str | None


def _load_surreal_config(config_path: Path) -> LoreConfig:
    """Parse ``config_path`` into a :class:`LoreConfig` WITHOUT touching the
    environment — the env-free :meth:`LoreConfig.model_validate`, NEVER
    :func:`load_config` (which resolves the REQUIRED Anthropic key eagerly and
    would abort this creds-free read-only CLI). Fable ruling FORK 2 rider 3.
    """
    raw = yaml.safe_load(Path(config_path).read_text(encoding="utf-8"))
    return LoreConfig.model_validate(raw)


def _effective_config_path(args: argparse.Namespace, config_path: Path | None) -> Path:
    """The project ``lore.yaml`` the DEFAULT (no ``--url``) path reads. ``config_path``
    is the tests' injection point; production passes it via ``--config`` (the hook's
    shell forwards ``$LORE_CONFIG`` — this tool never reads the environment). Loud
    failure when neither a ``--url`` override nor a ``--config`` path is supplied."""
    if config_path is not None:
        return config_path
    if args.config is not None:
        return Path(args.config)
    raise SystemExit(
        "comms_cli: no store coordinate — pass --url (with --namespace/--database) "
        "or --config <path to lore.yaml>"
    )


def _resolve_coordinate(
    args: argparse.Namespace, *, config_path: Path | None = None
) -> _ResolvedCoordinate:
    """Resolve WHICH store ``pending`` reads from.

    Explicit ``--url`` (with its sibling overrides) WINS. Otherwise the DEFAULT
    path reads the project's ``lore.yaml`` and derives the coordinate from the
    SHARED :class:`loremaster.config.SurrealConfig` +
    :attr:`loremaster.config.LoreConfig.effective_surreal_database` resolver —
    ONE IMPLEMENTATION, never a cloned coordinate resolver (a cloned resolver is
    where a config change reaches the server and not this CLI). ``config_path``
    is the discovery injection point tests use; production ``main`` passes the
    project's ``lore.yaml`` via ``--config``.
    """
    if args.url is not None:
        return _ResolvedCoordinate(
            url=args.url, namespace=args.namespace, database=args.database
        )
    config = _load_surreal_config(_effective_config_path(args, config_path))
    return _ResolvedCoordinate(
        url=config.surreal.url,
        namespace=config.surreal.namespace,
        # DERIVE the database THROUGH the shared resolver (F7 / ONE IMPLEMENTATION):
        # ``effective_surreal_database`` is ``surreal.database`` or the project slug,
        # so a config change reaches this CLI exactly as it reaches the server.
        database=config.effective_surreal_database,
    )


def _resolve_credentials(
    args: argparse.Namespace, *, config_path: Path | None = None
) -> tuple[str, SecretStr]:
    """The (user, password) to sign in with — explicit ``--user``/``--password``
    override first, else the project ``lore.yaml`` surreal block's env-var NAMES
    resolved through the SHARED config resolvers, exactly as the server's
    ``build_app_context`` does: the username via
    :func:`loremaster.config.resolve_config_value` (a plain str — never unwrapped
    from a ``SecretStr``) and the password via
    :func:`loremaster.config.resolve_secret` (a ``SecretStr`` — never unwrapped
    here; the ledger's own SDK-signin seam unwraps it). The config is loaded
    lazily, so the fully-explicit path (the contract's integration pins) opens no
    config file."""
    surreal = None

    def _surreal() -> LoreConfig:
        nonlocal surreal
        if surreal is None:
            surreal = _load_surreal_config(_effective_config_path(args, config_path))
        return surreal

    user = args.user if args.user is not None else resolve_config_value(_surreal().surreal.user_env)
    password = (
        SecretStr(args.password)
        if args.password is not None
        else resolve_secret(_surreal().surreal.password_env)
    )
    return user, password


async def _brief_skew(brief_ledger: BriefLedger, *, agent_id: str) -> int:
    """How many versions behind the STANDING brief head this agent is (0 when no
    standing brief exists, or the agent is current). A read composition over the
    shared BriefLedger — no cloned skew arithmetic."""
    try:
        head = (await brief_ledger.get_head(STANDING_BRIEF)).version
    except UnknownBriefError:
        return 0
    acked = await brief_ledger.acked_version(agent_id=agent_id, name=STANDING_BRIEF)
    return max(0, head - (acked or 0))


def _require_resolved(value: str | None, field: str) -> str:
    """A resolved coordinate field must be concrete before a connection opens —
    loud failure (never a ``None`` silently reaching the SDK) when, e.g., ``--url``
    was passed without its ``--namespace``/``--database`` siblings."""
    if value is None:
        raise SystemExit(
            f"comms_cli: store {field} unresolved — pass --{field} (with its siblings) "
            "or --config <path to a lore.yaml that names it>"
        )
    return value


async def _run_pending(args: argparse.Namespace) -> int:
    """Resolve the agent's pending state and print the counts line. READ-ONLY:
    every store touch is a ``SELECT`` through a shipped ledger method."""
    coordinate = _resolve_coordinate(args)
    url = _require_resolved(coordinate.url, "url")
    namespace = _require_resolved(coordinate.namespace, "namespace")
    database = _require_resolved(coordinate.database, "database")
    user, password = _resolve_credentials(args)
    agent_registry = AgentRegistry(
        url=url, namespace=namespace, database=database, user=user, password=password
    )
    message_ledger = MessageLedger(
        url=url, namespace=namespace, database=database, user=user, password=password
    )
    brief_ledger = BriefLedger(
        url=url, namespace=namespace, database=database, user=user, password=password
    )
    try:
        agent = await agent_registry.get_agent(args.agent)
        traffic = await message_ledger.pending_traffic(agent_id=agent.id)
        skew = await _brief_skew(brief_ledger, agent_id=agent.id)
        print(
            f"unread={traffic.unread} unacked={traffic.unacked_directives} skew={skew}"
        )
    finally:
        await agent_registry.close()
        await message_ledger.close()
        await brief_ledger.close()
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point. Returns a process exit code (0 = success, non-zero = failure)."""
    args = _build_parser().parse_args(argv)
    if args.command == "pending":
        return asyncio.run(_run_pending(args))
    return 2


if __name__ == "__main__":  # pragma: no cover - exercised via `python -m` subprocess
    sys.exit(main())
