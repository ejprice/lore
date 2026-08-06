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
  THREE scenarios (1/1/0, 0/0/0, 2/2/1) — non-monoculture (adversary F5): a build
  that hardcodes one counts line reddens on a differing scenario.
- **C-readonly-runtime** — running the CLI against a seeded store leaves the ENTIRE
  database byte-identical: every table (discovered via ``INFO FOR DB``) and every
  row's full CONTENT, snapshotted before/after (adversary F3/F4 — a 3-table row COUNT
  missed typed SDK writes, writes to other tables, and content-only UPDATE/MERGEs). A
  safety invariant: GREEN now, RED against ANY build that writes while reporting.
- **C-readonly-source** — the module issues NO SurrealQL write verb
  (CREATE/UPDATE/DELETE/RELATE/UPSERT/INSERT) in any code string — allowlist SELECT —
  AND makes NO typed SDK write-method call (``create``/``update``/``merge``/… on a
  store connection: a typed write carries no verb string, adversary F3), an AST
  call-scan scoped to ``AsyncSurreal``-bound receivers. (Both scans EXCLUDE
  docstrings, which legitimately NAME the forbidden verbs.)
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
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

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
from loremaster.briefs import BriefLedger
from loremaster.config import LoreConfig
from loremaster.messages import MessageLedger
from test_config import _CANONICAL_CONFIG

from loremaster import comms_cli

_SESSION = "cli-wave"
_WRITE_VERBS = ("CREATE", "UPDATE", "DELETE", "RELATE", "UPSERT", "INSERT")
# The SurrealDB SDK write surface (``AsyncSurreal``) — every one a WRITE that carries NO
# SurrealQL verb string, so the constant-only scan (test_source_issues_no_write_verb) is
# blind to it. The AST call-scan (test_source_issues_no_typed_write_method) forbids these
# on a store connection (adversary F3).
_SDK_WRITE_METHODS = frozenset(
    {"create", "insert", "insert_relation", "update", "upsert", "merge", "patch", "delete", "relate"}
)


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


def _connection_bound_names(tree: ast.AST) -> set[str]:
    """Local names bound from an ``AsyncSurreal(...)`` constructor call — the store
    connection a direct-SELECT CLI opens (``conn = AsyncSurreal(url)``). The typed-write
    call-scan is SCOPED to these receivers so it catches the exact ``conn.create(...)``
    shape the adversary's WB-CLI uses while never false-positiving on stdlib
    ``dict.update`` / ``list.insert`` (an insult that would get the gate switched off)."""
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
            func = node.value.func
            callee = (
                func.id
                if isinstance(func, ast.Name)
                else func.attr
                if isinstance(func, ast.Attribute)
                else None
            )
            if callee == "AsyncSurreal":
                names.update(
                    target.id for target in node.targets if isinstance(target, ast.Name)
                )
    return names


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

    def test_source_issues_no_typed_write_method(self) -> None:
        # F3 belt-and-braces: a typed SDK write (conn.create/update/merge/delete/insert/
        # upsert/patch/relate) carries NO SurrealQL verb string, so the constant-only scan
        # above is BLIND to it — the adversary's WB-CLI door (conn.create("cli_audit", …)).
        # This AST CALL-scan forbids any write-method call on a store connection, scoped to
        # AsyncSurreal-bound receivers so stdlib dict.update / list.insert never trip it.
        # ⚠ HEURISTIC / early-warning, keyed on a method name-list (the enumerate-the-
        # forbidden hazard): a connection obtained some OTHER way is invisible HERE but
        # STILL caught by the runtime full-DB pin (test_pending_is_read_only_full_db_
        # content_unchanged), which is the exhaustive, method-agnostic guarantee.
        tree = ast.parse(_source())
        connections = _connection_bound_names(tree)
        offenders: list[str] = []
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id in connections
                and node.func.attr in _SDK_WRITE_METHODS
            ):
                offenders.append(f"{node.func.value.id}.{node.func.attr}")
        assert not offenders, (
            "comms_cli is READ-ONLY by construction — no typed SDK WRITE method "
            "(create/insert/update/upsert/merge/patch/delete/relate) may be called on a store "
            "connection; a typed write carries no SurrealQL verb string and evades the "
            f"constant-only scan (adversary F3). Found: {offenders!r}"
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

    def test_default_resolution_routes_through_the_shared_surrealconfig(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # F7 / ONE IMPLEMENTATION (Ruling FORK 2): the default path must ROUTE THROUGH the
        # shared LoreConfig/SurrealConfig resolver — not a cloned yaml.safe_load reader that
        # returns identical values TODAY and silently diverges the day SurrealConfig's
        # resolution changes (a new default, a slug-derivation tweak reaches the server and
        # not this CLI). A value-only assertion cannot tell a clone from the shared resolver
        # (adversary F7). Prove sharing by MUTATION: monkeypatch the shared
        # LoreConfig.effective_surreal_database (the surreal.database-or-slug resolver the
        # ruling names) to a sentinel; a build that derives the database THROUGH it FOLLOWS
        # (GREEN), a cloned resolver reading the yaml directly IGNORES the monkeypatch and
        # stays stale (RED) — reddening the exact clone the adversary's F7 build passed.
        monkeypatch.setenv("COMMS_CLI_TEST_ANTHROPIC_KEY", "dummy-unused")
        sentinel = "shared_surrealconfig_sentinel_db"
        monkeypatch.setattr(
            LoreConfig, "effective_surreal_database", property(lambda _self: sentinel)
        )
        config_path = _write_fixture_config(
            tmp_path,
            url=_FIXTURE_URL,
            namespace=_FIXTURE_NAMESPACE,
            # A VALID SlugStr (underscores, not hyphens) — model_validate still validates
            # surreal.database even though effective_surreal_database is monkeypatched away.
            database="ignored_if_shared",
            anthropic_key_env="COMMS_CLI_TEST_ANTHROPIC_KEY",
        )
        args = comms_cli._build_parser().parse_args(["pending", "--agent", "x"])  # noqa: SLF001
        resolved = comms_cli._resolve_coordinate(args, config_path=config_path)  # noqa: SLF001
        assert resolved.database == sentinel, (
            "the default coordinate resolution must derive the database THROUGH the shared "
            "LoreConfig.effective_surreal_database (ONE IMPLEMENTATION, Ruling FORK 2) — a "
            "resolver that reads lore.yaml directly (a clone) ignores this monkeypatch and "
            f"stays stale; resolved.database={resolved.database!r}. Only a build that ROUTES "
            "through SurrealConfig follows when its resolution changes."
        )


# --------------------------------------------------------------------------- #
# C-counts / C-readonly-runtime — the live integration pins (spike-surreal :18000).
# --------------------------------------------------------------------------- #
async def _seed_scenario(*, directives: int, publish_brief: bool) -> tuple[str, str]:
    """Register ``lead`` + ``x`` on a fresh throwaway DB, send ``x`` ``directives`` unread
    DIRECTIVES, and optionally publish a ``project`` brief AFTER ``x`` registered.

    Returns ``(database, "x")``; the caller reaps the DB. ``publish_brief`` publishes the
    brief AFTER ``x`` registered, so ``x`` is behind the head by one version ⇒ ``skew>0``
    (register auto-acks the head that EXISTS at register time — none, on a fresh DB). Three
    scenarios kill the single-fixture monoculture the adversary flagged (F5):
    ``directives=1``→``1/1/0``, ``directives=0``→``0/0/0``, ``directives=2 publish_brief``→
    ``2/2/1``.
    """
    database = unique_database()
    env = make_env(database=database, dim=PRODUCTION_DIM)
    setup = await connect_admin(env)
    await setup.close()
    coord: dict[str, Any] = {
        "url": env.url,
        "namespace": env.namespace,
        "database": env.database,
        "user": env.user,
        "password": env.password,
    }
    registry = AgentRegistry(**coord)
    messages = MessageLedger(**coord)
    briefs = BriefLedger(**coord)
    try:
        await registry.ensure_ready()
        await messages.ensure_ready()
        await briefs.ensure_ready()
        await registry.register("lead", session=_SESSION, role="lead")
        # x registers when NO project brief exists yet → it auto-acks nothing, so a brief
        # published below leaves it behind the head (skew>0).
        await registry.register("x", session=_SESSION, role="builder")
        lead = await registry.get_agent("lead", session=_SESSION)
        recipient = await registry.get_agent("x", session=_SESSION)
        for _ in range(directives):
            await messages.send(
                sender=lead,
                session=_SESSION,
                body="ack this when done",
                grade="directive",
                recipients=[recipient],
            )
        if publish_brief:
            await briefs.publish("project", "the standing brief body", created_by="lead")
    finally:
        await registry.close()
        await messages.close()
        await briefs.close()
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


def _assert_pending_counts(
    database: str, agent: str, *, unread: int, unacked: int, skew: int
) -> None:
    """Run ``pending --agent`` and assert it exits 0 and reports the three named counts.
    Shared by the three C-counts scenarios (ONE IMPLEMENTATION — the monoculture the
    adversary flagged was a single fixture, not a single helper)."""
    result = _run_cli(database, agent)
    assert result.returncode == 0, (
        f"comms_cli pending must exit 0 on success; got {result.returncode} "
        f"(stdout={result.stdout!r} stderr={result.stderr!r})"
    )
    for token in (f"unread={unread}", f"unacked={unacked}", f"skew={skew}"):
        assert token in result.stdout, (
            f"pending --agent {agent} must report {token!r}; got stdout={result.stdout!r}"
        )


def _canonical(value: object) -> str:
    """Stable, type-tagged serialization so RecordIDs / datetimes / nested structures
    compare deterministically across two reads of the same store."""
    return json.dumps(value, sort_keys=True, default=lambda obj: f"{type(obj).__name__}:{obj!s}")


def _db_table_names(info: object) -> list[str]:
    """Table names from an ``INFO FOR DB`` result (``{'tables': {name: ddl}}``), tolerating
    the SDK wrapping a single statement's result in a one-element list."""
    if isinstance(info, list) and info:
        info = info[0]
    if isinstance(info, dict):
        tables = info.get("tables")
        if isinstance(tables, dict):
            return sorted(tables)
    return []


async def _full_db_content(database: str) -> dict[str, list[str]]:
    """Snapshot the ENTIRE database — every table (discovered via ``INFO FOR DB``) and every
    row's full CONTENT. The read-only proof a 3-table row-COUNT cannot give (adversary
    F3/F4): a typed SDK write (no verb string), a write to a NEW table, or an UPDATE/MERGE
    that changes no count all surface as a content diff here."""
    env = make_env(database=database, dim=PRODUCTION_DIM)
    conn = await connect_admin(env)
    try:
        info = await conn.query("INFO FOR DB")
        content: dict[str, list[str]] = {}
        for table in _db_table_names(info):
            rows = await conn.query(f"SELECT * FROM {table}")
            materialized = rows if isinstance(rows, list) else []
            content[table] = sorted(_canonical(row) for row in materialized)
        return content
    finally:
        await conn.close()


class TestPendingReportsCounts:
    async def test_pending_reports_one_unread_directive(self) -> None:
        # Scenario A (1/1/0): one unread DIRECTIVE ⇒ unread=1, unacked=1; no brief ⇒ skew=0.
        database, agent = await _seed_scenario(directives=1, publish_brief=False)
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            _assert_pending_counts(database, agent, unread=1, unacked=1, skew=0)
        finally:
            await drop_database(env)

    async def test_pending_reports_zero_when_no_traffic(self) -> None:
        # Scenario B (0/0/0) — F5 monoculture fix: DIFFERENT values. A hardcoded
        # print("unread=1 unacked=1 skew=0") build (adversary F5) reddens on all three.
        database, agent = await _seed_scenario(directives=0, publish_brief=False)
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            _assert_pending_counts(database, agent, unread=0, unacked=0, skew=0)
        finally:
            await drop_database(env)

    async def test_pending_reports_multiple_unread_and_brief_skew(self) -> None:
        # Scenario C (2/2/1) — F5 monoculture fix on the skew axis: x registered BEFORE the
        # brief was published, so it is behind the head by one version ⇒ skew=1. Kills a
        # build that hardcodes skew=0 (the only value the single fixture ever exercised).
        database, agent = await _seed_scenario(directives=2, publish_brief=True)
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            _assert_pending_counts(database, agent, unread=2, unacked=2, skew=1)
        finally:
            await drop_database(env)

    async def test_pending_is_read_only_full_db_content_unchanged(self) -> None:
        # F3+F4: snapshot the ENTIRE database (every table via INFO FOR DB, full row
        # CONTENT — not counts of {agent,message,to}) before and after the CLI run and
        # assert byte-identical. Subsumes F3 (a typed SDK write carries no verb string) AND
        # F4 (a write to ANY other table, or an UPDATE/MERGE that changes no count). The
        # adversary's WB-CLI (conn.create("cli_audit", …)) writes 1 real row → reddens here.
        database, agent = await _seed_scenario(directives=1, publish_brief=False)
        env = make_env(database=database, dim=PRODUCTION_DIM)
        try:
            before = await _full_db_content(database)
            _run_cli(database, agent)
            after = await _full_db_content(database)
            deltas = {
                table: (len(before.get(table, [])), len(after.get(table, [])))
                for table in set(before) | set(after)
                if before.get(table) != after.get(table)
            }
            assert before == after, (
                "comms_cli must be READ-ONLY at runtime — reporting pending state must not "
                "mutate ANY table's content (a typed SDK write / a write to a NEW table / an "
                "UPDATE with no count change all surface here). "
                f"new tables: {sorted(set(after) - set(before)) or 'none'}; "
                f"changed (before,after row counts): {deltas!r}"
            )
        finally:
            await drop_database(env)
