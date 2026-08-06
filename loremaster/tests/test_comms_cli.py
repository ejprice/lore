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

⚠ ESCALATION (surfaced to lead-05a, NOT silently resolved). The design plan
(``one-of-claude-codes-nifty-garden.md`` §"Hook bridge") specifies
``python -m loremaster.comms_cli pending --agent <name>`` + "direct SurrealDB
SELECTs", but does NOT specify HOW the standalone CLI resolves its store coordinate
and TARGET DATABASE (lore's config carries ONE configured database; a fleet may live
in another; the harness mints a unique throwaway DB per test). This contract pins the
EXPLICIT-override path (``--url/--namespace/--database/--user/--password``, passed
deterministically by C-counts); the DEFAULT resolution (read lore config? require the
args? read an env contract?) is a fork for the operator/lead. See
REPORT-contract-05aiii.md §Escalations.

Tests hit spike-surreal ``ws://127.0.0.1:18000`` ONLY (per-test throwaway DB); the
production store ``:18500`` is NEVER touched.
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest
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
