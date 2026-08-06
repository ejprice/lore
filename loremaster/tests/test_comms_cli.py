"""Contract — ``comms_cli.py``: the read-only idle-gate bridge (packet 05a-iii, scope C).

RED contract (author: contract-05aiii). The builder greens ``pending``; the two
SAFETY invariants (read-only, no hardcoded production coordinate) are GREEN from the
first commit — they are properties of what the module does NOT do, and a wrong build
that writes or hardcodes ``:18500`` reddens them.

Pins:
- **C-cmd** — the command surface is exactly ``pending --agent <name>`` (+ optional
  store-coordinate overrides). Parser-level; no store. GREEN against the stub.
- **C-counts** — ``pending`` reports ``unread=<n> unacked=<n> skew=<n>`` for the
  named agent, computed from the live store. RED against the stub (unimplemented).
- **C-readonly-runtime** — running the CLI against a seeded store leaves every comms
  table's row COUNT byte-identical (a safety invariant: GREEN now, RED against any
  build that writes while merely reporting).
- **C-readonly-source** — the module issues NO SurrealQL write verb
  (CREATE/UPDATE/DELETE/RELATE/UPSERT/INSERT) in any code string — allowlist SELECT.
  (The scan EXCLUDES docstrings, which legitimately NAME the forbidden verbs.)
- **C-coordinate-safety** — the production coordinate ``18500`` never appears as a
  code literal; the coordinate is resolved/passed, never baked in. (Docstrings, which
  name ``:18500`` to explain the rule, are excluded.)
- **C-default-resolution** — with NO ``--url`` override, the coordinate resolves from
  the project's ``lore.yaml`` surreal block via the SHARED
  :class:`loremaster.config.SurrealConfig` resolver (never a hardcoded default, never
  a cloned resolver). Tested as a PURE resolution against a FIXTURE config pointed at
  ``:18000`` — never the default path against a live production store (rider 2). RED
  against the stub (default path unbuilt).
- **C-anthropic-independence** — the default coordinate resolution succeeds with the
  REQUIRED Anthropic key UNSET: this creds-free read-only CLI never uses it, so the
  surreal block loads via the env-free
  :meth:`loremaster.config.LoreConfig.model_validate` (or a surreal-only parse), NEVER
  :func:`loremaster.config.load_config` (which resolves ``anthropic.api_key_env``
  eagerly and would block boot). RED against the stub; RED against a ``load_config``
  build.

RULING — FORK (comms_cli default coordinate/database), RESOLVED. The design plan
(``one-of-claude-codes-nifty-garden.md`` §"Hook bridge") specified the command +
"direct SurrealDB SELECTs" but NOT how the standalone CLI resolves its store
coordinate + TARGET DATABASE with no explicit override. Fable ruling FORK 2
(2026-08-06, operator-delegated; ``REPORT-fable-design-05a.md`` §Follow-up rulings,
``lore_recall("Fable rulings 05a-iii forks")``): resolve via the server's OWN
``SurrealConfig`` — reused, NOT cloned — read off the project ``lore.yaml``; ONE
IMPLEMENTATION. comms_cli is the idle-gate HOOK BRIDGE, so in a live session it reads
the REAL fleet (production ``:18500``, read-only SELECTs) — the "tests → :18000, never
:18500" law binds TEST code, not this production tooling, so the DEFAULT path is
tested only by pure resolution against a fixture config (never against a live prod
store). Riders folded: (1) the no-hardcoded-``:18500`` AST guard STAYS
(C-coordinate-safety); (2) CLI tests assert default-resolution READS config, never
exercise it against prod, and keep the explicit ``--url`` override to ``:18000``;
(3) the creds-free CLI must not be blocked by the eager Anthropic key
(C-anthropic-independence). Contract folded by contract-revise-05aiii; see
REPORT-contract-revise-05aiii.md.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY (per-test throwaway DB); the
production store ``:18500`` is NEVER touched.
"""

from __future__ import annotations

import ast
import copy
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
import yaml
from _surreal_harness import (
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
    unique_database,
)
from loremaster.agents import AgentRegistry
from loremaster.messages import MessageLedger
from test_config import _CANONICAL_CONFIG

from loremaster import comms_cli

_SESSION = "cli-wave"
_WRITE_VERBS = ("CREATE", "UPDATE", "DELETE", "RELATE", "UPSERT", "INSERT")


def _source() -> str:
    return Path(comms_cli.__file__).read_text(encoding="utf-8")


def _non_docstring_string_constants(source: str) -> list[str]:
    """Every string ``ast.Constant`` in ``source`` that is NOT a module/func/class
    docstring — so a scan can key on the CODE without the docstrings that (correctly)
    NAME the forbidden verbs and the production coordinate."""
    tree = ast.parse(source)
    docstrings: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef):
            doc = ast.get_docstring(node, clean=False)
            if doc is not None:
                docstrings.add(doc)
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in docstrings:
                continue
            out.append(node.value)
    return out


# --------------------------------------------------------------------------- #
# C-cmd — the command surface (parser-level; no store).
# --------------------------------------------------------------------------- #
class TestCommandSurface:
    def test_pending_with_agent_parses(self) -> None:
        parser = comms_cli._build_parser()  # noqa: SLF001 - test-only parser reuse
        args = parser.parse_args(["pending", "--agent", "fixer-b"])
        assert args.command == "pending"
        assert args.agent == "fixer-b"

    def test_pending_accepts_the_coordinate_overrides(self) -> None:
        parser = comms_cli._build_parser()  # noqa: SLF001
        args = parser.parse_args(
            ["pending", "--agent", "x", "--url", "ws://h/rpc", "--database", "db"]
        )
        assert args.url == "ws://h/rpc"
        assert args.database == "db"

    def test_pending_requires_agent(self) -> None:
        parser = comms_cli._build_parser()  # noqa: SLF001
        with pytest.raises(SystemExit):
            parser.parse_args(["pending"])


# --------------------------------------------------------------------------- #
# C-readonly-source / C-coordinate-safety — structural safety invariants.
# --------------------------------------------------------------------------- #
class TestReadOnlyByConstruction:
    def test_source_issues_no_write_verb(self) -> None:
        write_re = re.compile(r"\b(" + "|".join(_WRITE_VERBS) + r")\b", re.IGNORECASE)
        offenders = [
            text for text in _non_docstring_string_constants(_source()) if write_re.search(text)
        ]
        assert not offenders, (
            "comms_cli is READ-ONLY by construction — no SurrealQL write verb "
            f"(CREATE/UPDATE/DELETE/RELATE/UPSERT/INSERT) may appear in a code string; found: {offenders!r}"
        )

    def test_source_never_hardcodes_the_production_coordinate(self) -> None:
        tree = ast.parse(_source())
        docstrings = {
            ast.get_docstring(node, clean=False)
            for node in ast.walk(tree)
            if isinstance(node, ast.Module | ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef)
        }
        offenders: list[object] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    if node.value in docstrings:
                        continue
                    if "18500" in node.value:
                        offenders.append(node.value)
                elif isinstance(node.value, int) and node.value == 18500:
                    offenders.append(node.value)
        assert not offenders, (
            "comms_cli must NEVER hardcode the production store coordinate (:18500) — "
            f"the coordinate is config-resolved / passed, never baked in; found: {offenders!r}"
        )


# --------------------------------------------------------------------------- #
# C-default-resolution / C-anthropic-independence — the DEFAULT store-coordinate
# resolution (RULED FORK 2). PURE resolution against a FIXTURE config pointed at
# :18000 — NEVER the default path against a live production store (rider 2). No
# store connection is opened here; these are offline resolution pins.
# --------------------------------------------------------------------------- #
def _write_fixture_config(
    tmp_path: Path,
    *,
    url: str,
    namespace: str,
    database: str,
    anthropic_key_env: str,
) -> Path:
    """Write a VALID ``lore.yaml`` whose surreal block names ``url``/``namespace``/
    ``database`` and whose (REQUIRED) anthropic block references
    ``anthropic_key_env`` by NAME only.

    Reuses ``test_config._CANONICAL_CONFIG`` as the ONE canonical valid config
    shape (ONE IMPLEMENTATION — never a second hand-rolled full config that would
    drift from the real schema), overriding only the two blocks these pins turn
    on. Credentials are referenced by the harness's own env-var NAMES
    (``SURREAL_USER`` / ``SURREAL_PASS``) — the shared ``SurrealConfig`` discipline.
    """
    payload = copy.deepcopy(_CANONICAL_CONFIG)
    payload["anthropic"] = {"api_key_env": anthropic_key_env}
    payload["surreal"] = {
        "url": url,
        "namespace": namespace,
        "database": database,
        "user_env": "SURREAL_USER",
        "password_env": "SURREAL_PASS",
    }
    config_path = tmp_path / "lore.yaml"
    config_path.write_text(yaml.safe_dump(payload), encoding="utf-8")
    return config_path


# The spike-surreal test coordinate the FIXTURE config names — the resolution pins
# assert the CLI reads THIS out of config, never a hardcoded default. It is only a
# fixture value: no connection is opened, so no store (test OR prod) is touched.
_FIXTURE_URL = "ws://127.0.0.1:18000/rpc"
_FIXTURE_NAMESPACE = "lore"


class TestDefaultCoordinateResolution:
    """RULED FORK 2 — with no ``--url`` override, the coordinate is READ FROM the
    project ``lore.yaml`` via the shared ``SurrealConfig`` resolver (never a
    hardcoded default, never a cloned resolver), and that load never requires the
    Anthropic key this read-only CLI does not use. Both pins are PURE resolution:
    they assert the resolved coordinate and open NO connection, so the default
    path is never exercised against a live production store (rider 2).
    """

    def test_no_override_resolves_the_config_surreal_coordinate(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Isolate the COORDINATE-reading property: set the config's anthropic key
        # so this pin turns ONLY on "does the default path read the config's
        # surreal coordinate, or ignore it and hardcode one?" (the anthropic
        # concern is the sibling pin's, with a DIFFERENT database value).
        monkeypatch.setenv("COMMS_CLI_TEST_ANTHROPIC_KEY", "dummy-unused")
        config_path = _write_fixture_config(
            tmp_path,
            url=_FIXTURE_URL,
            namespace=_FIXTURE_NAMESPACE,
            database="cli_default_probe",
            anthropic_key_env="COMMS_CLI_TEST_ANTHROPIC_KEY",
        )
        args = comms_cli._build_parser().parse_args(["pending", "--agent", "x"])  # noqa: SLF001
        resolved = comms_cli._resolve_coordinate(args, config_path=config_path)  # noqa: SLF001
        assert resolved.url == _FIXTURE_URL, (
            "with NO --url override, comms_cli must resolve its store coordinate "
            "FROM the project's lore.yaml surreal block (the shared SurrealConfig "
            f"resolver), never a hardcoded default; resolved={resolved!r}"
        )
        assert resolved.namespace == _FIXTURE_NAMESPACE, resolved
        assert resolved.database == "cli_default_probe", resolved

    def test_default_resolution_does_not_require_an_anthropic_key(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Rider 3: load_config resolves anthropic.api_key_env EAGERLY and
        # ``anthropic:`` is REQUIRED (loremaster/config.py load_config + LoreConfig)
        # — but this creds-free read-only CLI never uses the key. Point the config's
        # anthropic block at a GUARANTEED-UNSET variable and prove the default
        # coordinate resolution STILL succeeds: the surreal block must load env-free
        # (model_validate / surreal-only), never via load_config. A load_config
        # build raises ValueError on the unset key -> RED.
        unresolvable = "COMMS_CLI_TEST_ANTHROPIC_KEY_DEFINITELY_UNSET"
        monkeypatch.delenv(unresolvable, raising=False)
        config_path = _write_fixture_config(
            tmp_path,
            url=_FIXTURE_URL,
            namespace=_FIXTURE_NAMESPACE,
            database="cli_credfree_probe",
            anthropic_key_env=unresolvable,
        )
        args = comms_cli._build_parser().parse_args(["pending", "--agent", "x"])  # noqa: SLF001
        # Must NOT raise about the missing Anthropic key (a load_config build does),
        # and must still read the surreal coordinate out of config.
        resolved = comms_cli._resolve_coordinate(args, config_path=config_path)  # noqa: SLF001
        assert resolved.url == _FIXTURE_URL, (
            "a creds-free read-only CLI must resolve its store coordinate WITHOUT "
            "an Anthropic key configured — load the surreal block via env-free "
            "model_validate / a surreal-only parse, never load_config (which "
            "eagerly resolves the REQUIRED anthropic.api_key_env and would block "
            f"boot); resolved={resolved!r}"
        )


# --------------------------------------------------------------------------- #
# C-counts / C-readonly-runtime — the live integration pins (spike-surreal :18000).
# --------------------------------------------------------------------------- #
async def _seed_one_unread_directive() -> tuple[str, str]:
    """Register ``lead`` + ``x`` on a fresh throwaway DB and send ``x`` ONE directive.

    Returns ``(database, x_name)``. The caller reaps the DB. This yields the minimal
    scenario ``pending --agent x`` must report: ``unread=1 unacked=1 skew=0``.
    """
    database = unique_database()
    env = make_env(database=database, dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    await setup.close()
    registry = AgentRegistry(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    messages = MessageLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    try:
        await registry.ensure_ready()
        await messages.ensure_ready()
        await registry.register("lead", session=_SESSION, role="lead")
        await registry.register("x", session=_SESSION, role="builder")
        lead = await registry.get_agent("lead", session=_SESSION)
        recipient = await registry.get_agent("x", session=_SESSION)
        await messages.send(
            sender=lead,
            session=_SESSION,
            body="ack this when done",
            grade="directive",
            recipients=[recipient],
        )
    finally:
        await registry.close()
        await messages.close()
    return database, "x"


def _run_cli(database: str, agent: str) -> subprocess.CompletedProcess[str]:
    env = make_env(database=database, dim=PRODUCTION_DIM)
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "loremaster.comms_cli",
            "pending",
            "--agent",
            agent,
            "--url",
            surreal_url(),
            "--namespace",
            env.namespace,
            "--database",
            database,
            "--user",
            surreal_user(),
            "--password",
            surreal_password().get_secret_value(),
        ],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


async def _comms_row_counts(database: str) -> dict[str, int]:
    env = make_env(database=database, dim=PRODUCTION_DIM)
    conn = await connect_admin(env)
    try:
        counts: dict[str, int] = {}
        for table in ("agent", "message", "to"):
            result = await conn.query(f"SELECT count() AS n FROM {table} GROUP ALL")
            rows = result if isinstance(result, list) else []
            counts[table] = int(cast(int, rows[0]["n"])) if rows and isinstance(rows[0], dict) else 0
        return counts
    finally:
        await conn.close()


class TestPendingReportsCounts:
    async def test_pending_reports_unread_unacked_and_skew(self) -> None:
        database, agent = await _seed_one_unread_directive()
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            result = _run_cli(database, agent)
            assert result.returncode == 0, (
                f"comms_cli pending must exit 0 on success; got {result.returncode} "
                f"(stdout={result.stdout!r} stderr={result.stderr!r})"
            )
            # One unread DIRECTIVE ⇒ unread=1, unacked=1; no brief published ⇒ skew=0.
            assert "unread=1" in result.stdout, result.stdout
            assert "unacked=1" in result.stdout, result.stdout
            assert "skew=0" in result.stdout, result.stdout
        finally:
            await drop_database(env)

    async def test_pending_is_read_only_row_counts_unchanged(self) -> None:
        database, agent = await _seed_one_unread_directive()
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            before = await _comms_row_counts(database)
            _run_cli(database, agent)
            after = await _comms_row_counts(database)
            assert before == after, (
                "comms_cli must be READ-ONLY at runtime — reporting pending state must "
                f"not mutate any comms table (before={before} after={after})"
            )
        finally:
            await drop_database(env)
