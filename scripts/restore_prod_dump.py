#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.14"
# dependencies = [
#     "loremaster",
#     "httpx>=0.28",
#     "python-dotenv>=1.2",
#     "pydantic>=2.13",
#     "pytest-asyncio",
# ]
# [tool.uv.sources]
# loremaster = { path = "../loremaster", editable = true }
# ///
"""restore_prod_dump.py — restore the GOVERNED SLICE of a production ``surreal export`` into a minted,
throwaway TEST database, and prove what landed. Packet 64's F1 **S2** instrument.

SPEC (binding): ``docs/design/2026-09-26-packet64-amendment-3.md`` §D-3 (``aea2a9d``). S2 is the
REAL-prod-dump leg the 63a migration contract ruled *"a COMMITTED build-time integration script, NOT
pinned as a unit test"* (``loremaster/tests/test_governed_migration_63a.py`` module docstring) — and
that nobody wrote until packet 64 (probe-64, 2026-09-26). Its consumer is the marker-gated S2 leg of
``test_findings_migrate_64b.py`` (and 64a's task leg, and 65's dress rehearsal), which reads the ONE
stdout line this script prints: ``LORE_PROD_DUMP_DB=<name>``.

USAGE (stdout carries exactly that one line on success; every receipt goes to stderr)::

    ./scripts/restore_prod_dump.py                  # newest /backups/lore/lore-prod-*.surql, governed slice
    ./scripts/restore_prod_dump.py --dump PATH          # any `surreal export` (65: a FRESH export of prod)
    ./scripts/restore_prod_dump.py --tables finding,finding_counter   # an explicit slice (all REQUIRED)
    ./scripts/restore_prod_dump.py --full               # every section (chunk/snapshot_entry: GBs, slow)
    ./scripts/restore_prod_dump.py --reap test_dump_…   # tear the minted DB down (refuses foreign names)
    ./scripts/restore_prod_dump.py --self-test [--offline]   # the controls (exit 0 iff all hold)

Also runnable as ``uv run python scripts/restore_prod_dump.py …`` from the repo root (the project venv
carries every dependency), which is how ``scripts/test_restore_prod_dump.py`` imports it.

WHAT IT GUARANTEES, BY CONSTRUCTION (§D-3 numbered requirements):

1. **The endpoint is a CONSTANT** (:data:`STORE_PORT` = 18000, the spike-surreal TEST store). There is
   no ``--endpoint`` / ``--port`` / ``--db`` flag (``allow_abbrev=False``, so no prefix spelling reaches
   ``--dump`` either); the harness's ``LORE_TEST_SURREAL_URL`` override is never consulted (the
   connection topology is built HERE from the constant); and every HTTP request passes an event hook
   that refuses any host:port other than the constant BEFORE the transport is reached. The production
   port appears in this file only as :data:`PRODUCTION_PORT`, the value the self-test proves is refused.
   Credentials come from the env file both store quadlets name (:data:`STORES_ENV_FILE`; the self-test
   cross-checks the quadlet's ``EnvironmentFile=``). Secrets are held as ``SecretStr`` and never printed.
2. **The target DB is MINTED** ``test_dump_<UTC stamp>_<uuid4 hex>`` under the suite's test namespace,
   asserted ABSENT (``INFO FOR NS``) and then created with a plain ``DEFINE DATABASE`` (which itself
   errors on an existing name — a second, engine-side guard). ``--db`` does not exist. ``--reap`` refuses
   any name outside :data:`DATABASE_NAME_PATTERN`. On ANY failure after the mint the DB is reaped before
   exit; on success it is left for the caller (the S2 test) and named on stdout.
3. **The dump is VERIFIED** before anything is imported: its first SurrealQL statement is
   ``OPTION IMPORT;`` and it carries a ``-- TABLE: <t>`` section for every REQUIRED table, else REFUSE
   naming the missing ones (exit 2). This refusal is the re-open alarm for *"the day the export format
   changes"*.
4. **Governed-slice import by default**: a streaming text pass copies the preamble (OPTION / ANALYZERS /
   SEQUENCES / … — every section before the first table) plus the DDL + DATA sections of the slice into a
   temp ``.surql``, which ``POST /import`` streams (``Surreal-NS``/``Surreal-DB`` headers,
   ``--data-binary`` semantics — the vendor's endpoint; see the MEASURED facts below).
5. **Receipts**: per-table rows DECLARED by the dump (an exact top-level row count of each ``INSERT``,
   tokenised past quoted strings) vs rows READ BACK over a SECOND connection (the WS SDK, through
   ``loremaster``'s ONE ``run_query`` driver — never the HTTP connection that imported); the
   ``scope IS NONE`` count per governed node table via the REAL
   :func:`loremaster.governed.report_unmigrated_governed_rows` (asserted == rows when the dump's own DDL
   for that table lacks the governed trio, i.e. a pre-63 legacy table; reported otherwise); elapsed
   times; the DB name. Any declared-vs-read-back mismatch is a silent partial import → exit 4.
6. **Positive controls** in ``--self-test``: a 40-line synthetic export with two tables (precision:
   un-requested table omitted; recall: requested table's DDL + DATA present; a missing table refused;
   a row-shaped forgery inside a string NOT counted); the endpoint constant and its guard; the DB-name
   pattern and the reap refusal; and live on :18000 — an import VISIBLE via a second connection, the
   reap REMOVES it, a second import into a fresh DB yields IDENTICAL counts, and three negative controls
   (a mid-file runtime error, a mid-file parse error, and a tampered declared count) each go RED.

THE SLICE (§D-3 step 4), DERIVED at run time, each table carrying its provenance in the receipt:

* ``derived``   — :func:`_governed_contract.governed_populations` over the EMITTED schema DDL (the ONE
  derivation of the governed set in this repo — ``{t : the emitted DDL defines every governed-trio
  column on t}`` ∪ the relation tables whose IN/OUT endpoint is such a t). §D-3 names it
  ``surreal_schema.governed_node_tables(generate_ddl())``; no such production function exists at
  ``90ada74`` — the derivation lives in the test tree, so this script CALLS it there (ONE
  IMPLEMENTATION) rather than cloning it. At ``90ada74`` it yields ``agent, briefed, memory, message, to``.
* ``pending``   — :data:`PENDING_GOVERNED_TABLES`: node tables a named, not-yet-landed packet governs
  (``finding`` 64b, ``task`` 64a, ``brief`` 63c-ii). The S2 legs of those packets need them restored
  BEFORE their builds emit the trio. When the derivation grows to include one, the receipt says so
  (``derived`` wins) and the entry is dead weight to delete — never a second source of truth.
* ``relation``  — relation tables whose emitted endpoints touch a ``pending`` table (``blocks``).
* ``dependency``— :data:`SLICE_DEPENDENCIES`, each with its reason (the migration verb's reads).

A ``derived``/``pending`` NODE table missing from the dump is a REFUSAL. A ``relation``/``dependency``
table missing from the dump is reported ``ABSENT (the dump predates it)`` and NOT refused: the two
2026-07/08 dumps predate packets 60/61 (keep, member_of, principal, principal_key, audit) and the
04b-3 ``blocks`` edge, so refusing them would make the instrument unusable on exactly the legacy shape
S2 exists to test. ``--tables`` makes every named table REQUIRED.

MEASURED FACTS about ``POST /import`` on surrealdb 3.2.4 (probe-64, 2026-09-26, spike-surreal :18000;
receipts ``REPORT-probe-64.md`` §3 — the vendor page ``reference/rest-api/http-protocol.mdx`` §import
is SILENT on every one of the first five):

* **HTTP 200 is NOT success.** A statement that fails at runtime is reported as an ``ERR`` entry in a
  200 body, and the import CONTINUES with the next statement (non-atomic: rows after the failure land).
  With ``OPTION IMPORT`` successful statements return NOTHING, so a clean import's body is exactly
  ``[]`` — this script accepts that and nothing else.
* **A parse error mid-file STOPS the import** — statements before it are applied, the rest silently
  are not — still HTTP 200, one ``ERR`` entry.
* **Importing into a DB that does not exist depends on the FIRST statement**: a leading ``DEFINE
  ANALYZER`` / ``DEFINE SEQUENCE`` silently creates the DB and the import is clean (``[]``, SCHEMAFULL
  kept); a leading ``DEFINE TABLE`` errors ``NotFound``, a later statement creates the DB, and that
  SCHEMAFULL table comes back ``TYPE ANY SCHEMALESS`` — a schema downgrade reported by ONE ``ERR`` line
  (so the ``[]`` rule rejects it). The DB is DEFINEd first, always, so neither path is ever taken; the
  ``leg_live_define_database_refuses_an_existing_name`` control is the pin for that step.
* **``OPTION IMPORT`` disables field processing**: an ``ASSERT``-violating value and a ``VALUE``
  clause's input both land verbatim, and an ``EVENT`` does not fire (vendor-documented; measured).
  A restored legacy row is therefore byte-faithful to the dump, not re-validated.
* **The raw export is NOT importable as written**: ``surreal export`` captured with its log stream
  begins and ends with tracing log lines (``…Z  INFO surrealdb::method::export: Exporting bytes``);
  the leading one is rejected HTTP 400 (*"Invalid statement: Parse error"*). The text pass strips
  exactly that line shape (:data:`EXPORT_LOG_LINE_PATTERN`) and counts what it stripped.
* Vendor-confirmed: a body whose first statement is not ``OPTION IMPORT;`` → HTTP 400 (*"Import requires
  `OPTION IMPORT;` as the first statement"*); wrong credentials → HTTP 401.
* Vendor-WRONG: the reference page's example ``curl … -d file.surql …/import`` sends the literal string
  ``file.surql`` (HTTP 400); ``-d @file`` strips newlines, so a leading ``--`` comment swallows the file
  (HTTP 400). The tutorial's ``--data-binary @file`` is the working form. The ``Accept`` header the page
  marks *required* is not enforced.

THE BOUND (§D-3, named): S2 is NOT in the standard gate — a multi-GB backup is an environment
dependency. The driver RUNS at 64b-i's and 64a's close-outs and in 65's dress rehearsal; a close-out
without its receipt is ``done-with-deviations``. The row-count tokeniser knows the export's CURRENT
quoting (``'…'``, ``"…"``, ``⟨…⟩``, backticks, backslash escapes) and its one-``INSERT``-per-line data
shape; a change to either is refused (a data line that is not ``INSERT …;``, or unbalanced brackets) or
surfaces as a declared-vs-read-back mismatch — loud, never a silent pass. RE-OPEN TRIGGER: *the day
the export format changes* — step 3's refusal is the alarm.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import functools
import io
import json
import logging
import os
import re
import sys
import tempfile
import time
import uuid
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, TextIO

import httpx
from dotenv import dotenv_values
from pydantic import SecretStr

# --------------------------------------------------------------------------- #
# Constants — the endpoint is one of them BY CONSTRUCTION (§D-3 step 1).
# --------------------------------------------------------------------------- #

#: The spike-surreal TEST store. There is deliberately no flag, env var, or parameter that changes it.
STORE_HOST = "127.0.0.1"
STORE_PORT = 18000
#: Named ONLY so the self-test can prove a request to it is refused. Never a connection target.
PRODUCTION_PORT = 18500
HTTP_ENDPOINT = f"http://{STORE_HOST}:{STORE_PORT}"
RPC_ENDPOINT = f"ws://{STORE_HOST}:{STORE_PORT}/rpc"

#: The env file both store quadlets name as ``EnvironmentFile=`` (self-test cross-checks the TEST quadlet).
STORES_ENV_FILE = Path.home() / "docker" / "mcp" / "lore-secrets" / "lore.env"
TEST_STORE_QUADLET = Path.home() / ".config" / "containers" / "systemd" / "spike-surreal.container"
PRODUCTION_STORE_QUADLET = Path.home() / ".config" / "containers" / "systemd" / "lore-surreal.container"
ENV_USER_KEY = "SURREAL_USER"
ENV_PASS_KEY = "SURREAL_PASS"

DUMP_DIRECTORY = Path("/backups/lore")
DUMP_GLOB = "lore-prod-*.surql"
#: Where the temp slice is written. /var/tmp is disk-backed; /tmp may be tmpfs (RAM) and ``--full`` is GBs.
SLICE_SCRATCH_ROOT = Path("/var/tmp")

DATABASE_PREFIX = "test_dump_"
DATABASE_NAME_PATTERN = re.compile(r"^test_dump_\d{8}T\d{6}Z_[0-9a-f]{32}$")
DATABASE_STAMP_FORMAT = "%Y%m%dT%H%M%SZ"
#: The ONE stdout line a consumer reads.
DATABASE_ENV_VAR = "LORE_PROD_DUMP_DB"
#: The harness env var that retargets the TEST suite — named so the self-test proves it is NOT consulted.
HARNESS_URL_OVERRIDE_VAR = "LORE_TEST_SURREAL_URL"

#: Refuse to start an import below this much available memory (probe-64 brief: stop under 15 GB).
MIN_AVAILABLE_MEMORY_BYTES = 15 * 1024**3
MEMINFO_PATH = Path("/proc/meminfo")

HTTP_CONNECT_TIMEOUT_SECONDS = 10.0
HTTP_POOL_TIMEOUT_SECONDS = 10.0
#: Carried by the harness's connection topology; the read-back applies no DDL, so it is never used.
READBACK_EMBEDDING_DIM = 8
#: How many ERR entries of a rejected import to render (the rest are counted, never silently dropped).
RENDERED_ERROR_LIMIT = 5
RENDERED_ERROR_CHARS = 400

EXIT_OK = 0
EXIT_REFUSED = 2
EXIT_IMPORT_REJECTED = 3
EXIT_VERIFY_MISMATCH = 4
EXIT_SELF_TEST_FAILED = 5

#: Node tables a named, not-yet-landed packet will govern — restored so that packet's S2 leg has them.
PENDING_GOVERNED_TABLES: dict[str, str] = {
    "finding": "packet 64b governs the finding ledger (its S2 leg migrates these rows)",
    "task": "packet 64a governs the task ledger (its S2 leg migrates these rows)",
    "brief": "packet 63c-ii governs the brief ledger",
}

#: Tables the slice needs that are not themselves governed populations — each with its reason (§D-3).
SLICE_DEPENDENCIES: dict[str, str] = {
    "finding_counter": "the finding number mint — a finding restored without it re-mints colliding numbers",
    "keep": "migrate_governed mints/reads the project keep (key='project:lore') every backfill scopes to",
    "member_of": "principal->keep membership the READ filter consults (member-visible vs admin-visible)",
    "principal": "the operator principal / keeper the migration resolves",
    "principal_key": "principal credentials (packet 48) the principal rows reference",
    "audit": "the append-only trail governed writes append to",
}

#: §D-3 step 4's named slice, verbatim — a FLOOR the self-test asserts the derived slice still covers.
AMENDMENT_3_NAMED_SLICE = frozenset(
    {
        "memory",
        "message",
        "to",
        "agent",
        "briefed",
        "brief",
        "task",
        "blocks",
        "finding",
        "finding_counter",
        "keep",
        "member_of",
        "principal",
        "principal_key",
        "audit",
    }
)

#: The export's section rule line (``-- ------------------------------``).
SECTION_RULE_PATTERN = re.compile(r"^-- -{10,}\s*$")
#: The name line between two rules: ``-- OPTION`` / ``-- TABLE: agent`` / ``-- TABLE DATA: agent``.
SECTION_NAME_PATTERN = re.compile(r"^-- (?P<kind>TABLE DATA|TABLE|[A-Z][A-Z _]*?)(?::\s*(?P<table>\S+))?\s*$")
TABLE_DDL_KIND = "TABLE"
TABLE_DATA_KIND = "TABLE DATA"
#: The tracing log line ``surreal export`` interleaves with its output (first and last line of both dumps).
EXPORT_LOG_LINE_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z\s+(?:TRACE|DEBUG|INFO|WARN|ERROR)\s+surrealdb\S*:"
)
REQUIRED_FIRST_STATEMENT = "OPTION IMPORT;"
DATA_STATEMENT_PREFIX = "INSERT "
TABLE_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")
#: One token of an INSERT line: a quoted region (skipped whole) or a bracket.
INSERT_TOKEN_PATTERN = re.compile(
    r"'(?:[^'\\]|\\.)*'|\"(?:[^\"\\]|\\.)*\"|⟨(?:[^⟩\\]|\\.)*⟩|`(?:[^`\\]|\\.)*`|[\[\]{}]",
    re.DOTALL,
)
_OPENERS = {"[": "]", "{": "}"}

LOGGER = logging.getLogger("restore_prod_dump")


# --------------------------------------------------------------------------- #
# Errors — each maps to one exit code.
# --------------------------------------------------------------------------- #


class RestoreRefusedError(RuntimeError):
    """The input (dump, flag, name, environment) is refused before any store write."""


class ImportRejectedError(RuntimeError):
    """``POST /import`` answered anything other than HTTP 200 with an empty ``[]`` body."""


class VerifyMismatchError(RuntimeError):
    """What the dump declared and what the store reads back disagree — a silent partial import."""


class ForeignEndpointError(RuntimeError):
    """A request addressed anything other than the TEST store constant."""


class SelfTestFailure(AssertionError):
    """A self-test control did not hold."""


# --------------------------------------------------------------------------- #
# Test-tree helpers, imported the way conftest makes them importable (house idiom:
# scripts/forgery_door_sweep.py::_harness) — REUSED, never re-derived.
# --------------------------------------------------------------------------- #


def _repository_root() -> Path:
    """This checkout's root, derived from this file's location."""
    return Path(__file__).resolve().parent.parent


def _test_helpers() -> tuple[Any, Any, Any]:
    """``(_surreal_harness, _governed_contract, _enforced_relations_scaffold)`` from ``loremaster/tests``."""
    tests_directory = str(_repository_root() / "loremaster" / "tests")
    if tests_directory not in sys.path:
        sys.path.insert(0, tests_directory)
    import _enforced_relations_scaffold
    import _governed_contract
    import _surreal_harness

    return _surreal_harness, _governed_contract, _enforced_relations_scaffold


# --------------------------------------------------------------------------- #
# The slice — derived, with provenance.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class SliceTable:
    """One table of the requested slice: its provenance, and whether the dump MUST carry it."""

    name: str
    provenance: str
    required: bool
    reason: str = ""
    governed_node: bool = False


@dataclass(frozen=True)
class SliceRequest:
    """The set of tables to import (``full`` = every section the dump carries)."""

    tables: tuple[SliceTable, ...]
    full: bool = False

    def names(self) -> frozenset[str]:
        """The requested table names."""
        return frozenset(table.name for table in self.tables)

    def wants(self, table: str) -> bool:
        """Whether a ``-- TABLE[ DATA]: table`` section is part of the slice."""
        return self.full or table in self.names()

    def by_name(self) -> dict[str, SliceTable]:
        """The requested tables keyed by name."""
        return {table.name: table for table in self.tables}


class SliceDeriver:
    """Derives the default governed slice from the EMITTED schema DDL (§D-3 step 4)."""

    def __init__(self, emitted_ddl: str | None = None) -> None:
        _, contract, scaffold = _test_helpers()
        self._contract = contract
        self._emitted_ddl: str = emitted_ddl if emitted_ddl is not None else scaffold.emitted_schema_ddl()

    def governed_slice(self) -> SliceRequest:
        """``derived`` ∪ ``pending`` ∪ relations over pending ∪ named dependencies, each with provenance."""
        derived_nodes: set[str] = set(self._contract.governed_node_tables(self._emitted_ddl))
        derived_all: set[str] = set(self._contract.governed_populations(emitted_ddl=self._emitted_ddl))
        pending_nodes = set(PENDING_GOVERNED_TABLES) - derived_nodes
        relations_over_pending: set[str] = (
            set(self._contract.governed_relation_tables(self._emitted_ddl, pending_nodes)) - derived_all
        )
        tables: list[SliceTable] = []
        for name in sorted(derived_all):
            node = name in derived_nodes
            tables.append(
                SliceTable(
                    name=name,
                    provenance="derived",
                    required=node,
                    reason="governed node (emitted trio)" if node else "relation over a governed node",
                    governed_node=node,
                )
            )
        for name in sorted(pending_nodes):
            tables.append(
                SliceTable(
                    name=name,
                    provenance="pending",
                    required=True,
                    reason=PENDING_GOVERNED_TABLES[name],
                    governed_node=True,
                )
            )
        for name in sorted(relations_over_pending):
            tables.append(
                SliceTable(
                    name=name, provenance="relation", required=False, reason="relation over a pending node"
                )
            )
        taken = {table.name for table in tables}
        for name, reason in sorted(SLICE_DEPENDENCIES.items()):
            if name not in taken:
                tables.append(SliceTable(name=name, provenance="dependency", required=False, reason=reason))
        return SliceRequest(tables=tuple(tables))

    def is_governed_shape(self, table: str, table_ddl: str) -> bool:
        """Whether the dump's OWN DDL for ``table`` defines the whole governed trio (i.e. is post-63)."""
        return table in set(self._contract.governed_node_tables(table_ddl))


def explicit_slice(names: Iterable[str]) -> SliceRequest:
    """``--tables a,b``: every named table REQUIRED; governed-node status taken from the derivation."""
    deriver = SliceDeriver()
    governed_nodes = {table.name for table in deriver.governed_slice().tables if table.governed_node}
    tables = []
    for name in names:
        _validate_table_name(name)
        tables.append(
            SliceTable(
                name=name,
                provenance="explicit",
                required=True,
                reason="named by --tables",
                governed_node=name in governed_nodes,
            )
        )
    return SliceRequest(tables=tuple(tables))


def _validate_table_name(name: str) -> str:
    """Refuse a table name that is not a plain identifier (it is interpolated into SurrealQL)."""
    if not TABLE_NAME_PATTERN.match(name):
        raise RestoreRefusedError(
            f"table name {name!r} is not a plain identifier ({TABLE_NAME_PATTERN.pattern})"
        )
    return name


# --------------------------------------------------------------------------- #
# The export scanner — verifies the format and writes the slice in ONE streaming pass.
# --------------------------------------------------------------------------- #


def count_insert_rows(statement: str) -> int:
    """The number of top-level rows an export ``INSERT [ {…}, … ];`` line inserts.

    Quoted regions (``'…'``, ``"…"``, ``⟨…⟩``, backticks, backslash escapes) are skipped whole, so a
    row-shaped string (``"}, { id: t:forged }"``) is never counted. Raises :class:`RestoreRefusedError`
    on unbalanced or mismatched brackets, or more than one top-level structure — the tokeniser's
    assumptions no longer hold, which is the format-change alarm, never a guess.
    """
    stack: list[str] = []
    rows = 0
    top_level_structures = 0
    for match in INSERT_TOKEN_PATTERN.finditer(statement):
        token = match.group(0)
        if token in _OPENERS:
            if not stack:
                top_level_structures += 1
                if top_level_structures > 1:
                    raise RestoreRefusedError("an INSERT line carries more than one top-level structure")
                if token == "{":
                    rows += 1
            elif token == "{" and stack == ["["]:
                rows += 1
            stack.append(token)
        elif token in ("]", "}"):
            if not stack or _OPENERS[stack[-1]] != token:
                raise RestoreRefusedError(f"unbalanced {token!r} in an INSERT line at offset {match.start()}")
            stack.pop()
    if stack:
        raise RestoreRefusedError(f"an INSERT line ends with {len(stack)} unclosed bracket(s)")
    return rows


@dataclass
class ScanResult:
    """What one pass over a dump found."""

    dump: Path
    dump_bytes: int
    first_statement: str | None = None
    log_lines_stripped: int = 0
    tables_seen: list[str] = field(default_factory=list)
    preamble_sections: list[str] = field(default_factory=list)
    declared_rows: dict[str, int] = field(default_factory=dict)
    table_ddl: dict[str, str] = field(default_factory=dict)
    slice_bytes: int = 0


class ExportScanner:
    """Streams a ``surreal export`` once: verifies its shape and copies the requested slice.

    Section grammar (both 2026-07/08 dumps, 3.2.x ``surreal export``): a three-line header
    ``-- ----`` / ``-- <NAME>[: <table>]`` / ``-- ----``; every section before the first ``TABLE`` is
    PREAMBLE (copied whole); ``-- TABLE: t`` holds DDL; ``-- TABLE DATA: t`` holds one ``INSERT …;`` per
    line. Anything else is refused.
    """

    def __init__(self, request: SliceRequest) -> None:
        self._request = request

    def scan(self, dump: Path, output: TextIO) -> ScanResult:
        """Verify ``dump`` and write its slice to ``output``. Raises :class:`RestoreRefusedError`."""
        result = ScanResult(dump=dump, dump_bytes=dump.stat().st_size)
        with dump.open(encoding="utf-8", newline="") as source:
            self._scan_lines(source, output, result)
        self._check(result)
        return result

    def _scan_lines(self, source: Iterable[str], output: TextIO, result: ScanResult) -> None:
        kind: str | None = None
        table: str | None = None
        include = False
        seen_table_section = False
        pending_rule: str | None = None
        seen_tables: set[str] = set()

        def emit(text: str) -> None:
            if include:
                output.write(text)
                result.slice_bytes += len(text.encode("utf-8"))

        for line in source:
            stripped = line.rstrip("\r\n")
            if EXPORT_LOG_LINE_PATTERN.match(stripped):
                result.log_lines_stripped += 1
                continue
            if pending_rule is not None:
                name_match = SECTION_NAME_PATTERN.match(stripped)
                if name_match is not None:
                    kind = name_match.group("kind")
                    table = name_match.group("table")
                    if kind in (TABLE_DDL_KIND, TABLE_DATA_KIND):
                        if table is None:
                            raise RestoreRefusedError(f"section header {stripped!r} names no table")
                        seen_table_section = True
                        include = self._request.wants(table)
                        if table not in seen_tables:
                            seen_tables.add(table)
                            result.tables_seen.append(table)
                    else:
                        if seen_table_section:
                            raise RestoreRefusedError(
                                f"a non-table section {stripped!r} follows the table sections — the export "
                                "format changed"
                            )
                        include = True
                        result.preamble_sections.append(kind)
                    emit(pending_rule)
                    emit(line)
                    pending_rule = None
                    continue
                emit(pending_rule)
                pending_rule = None
            if SECTION_RULE_PATTERN.match(stripped):
                pending_rule = line
                continue
            self._content_line(line, stripped, kind, table, include, result, emit)
        if pending_rule is not None:
            emit(pending_rule)

    @staticmethod
    def _content_line(
        line: str,
        stripped: str,
        kind: str | None,
        table: str | None,
        include: bool,
        result: ScanResult,
        emit: Callable[[str], None],
    ) -> None:
        is_filler = not stripped.strip() or stripped.lstrip().startswith("--")
        if kind is None:
            if not is_filler:
                raise RestoreRefusedError(f"content before the first section header: {stripped[:120]!r}")
            return
        if not is_filler and result.first_statement is None:
            result.first_statement = stripped.strip()
        if kind == TABLE_DATA_KIND and not is_filler:
            if not (stripped.startswith(DATA_STATEMENT_PREFIX) and stripped.rstrip().endswith(";")):
                raise RestoreRefusedError(
                    f"a TABLE DATA line for {table!r} is not one `INSERT …;` statement — the export format "
                    f"changed: {stripped[:120]!r}"
                )
            if include and table is not None:
                result.declared_rows[table] = result.declared_rows.get(table, 0) + count_insert_rows(stripped)
        if kind == TABLE_DDL_KIND and include and table is not None:
            result.table_ddl[table] = result.table_ddl.get(table, "") + line
        emit(line)

    def _check(self, result: ScanResult) -> None:
        if result.first_statement != REQUIRED_FIRST_STATEMENT:
            raise RestoreRefusedError(
                f"the dump's first statement is {result.first_statement!r}, not {REQUIRED_FIRST_STATEMENT!r} "
                "— not a `surreal export`, or the export format changed"
            )
        if not result.tables_seen:
            raise RestoreRefusedError(
                "the dump carries no `-- TABLE: <t>` sections — the export format changed"
            )
        missing = sorted(
            table.name
            for table in self._request.tables
            if table.required and table.name not in result.tables_seen
        )
        if missing:
            raise RestoreRefusedError(
                f"the dump carries no `-- TABLE:` section for required table(s): {', '.join(missing)}"
            )


# --------------------------------------------------------------------------- #
# The store client — the ONLY path to the network, guarded to the constant.
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class StoreCredentials:
    """Root credentials for the TEST store, read from the stores' env file. The password never prints."""

    user: str
    password: SecretStr

    @classmethod
    def from_env_file(cls, env_file: Path = STORES_ENV_FILE) -> StoreCredentials:
        """Parse ``env_file`` (python-dotenv); refuse naming a missing KEY, never echoing a value."""
        if not env_file.is_file():
            raise RestoreRefusedError(f"the stores' env file {env_file} does not exist")
        values = dotenv_values(env_file)
        user, password = values.get(ENV_USER_KEY), values.get(ENV_PASS_KEY)
        missing = [key for key, value in ((ENV_USER_KEY, user), (ENV_PASS_KEY, password)) if not value]
        if missing or user is None or password is None:
            raise RestoreRefusedError(f"{env_file} carries no value for: {', '.join(missing)}")
        return cls(user=user, password=SecretStr(password))


def _refuse_foreign_endpoint(request: httpx.Request) -> None:
    """httpx request hook: refuse any host:port but the TEST store constant, BEFORE the transport runs."""
    if (request.url.host, request.url.port) != (STORE_HOST, STORE_PORT):
        raise ForeignEndpointError(
            f"refused a request to {request.url.host}:{request.url.port} — this driver only ever addresses "
            f"the TEST store {STORE_HOST}:{STORE_PORT}"
        )


class StoreClient:
    """HTTP access to the TEST store: ``/sql`` for control statements, ``/import`` for the slice."""

    def __init__(
        self,
        credentials: StoreCredentials,
        namespace: str,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.namespace = namespace
        self._credentials = credentials
        self._http = httpx.Client(
            base_url=HTTP_ENDPOINT,
            auth=(credentials.user, credentials.password.get_secret_value()),
            headers={"Accept": "application/json", "Surreal-NS": namespace},
            event_hooks={"request": [_refuse_foreign_endpoint]},
            timeout=httpx.Timeout(
                connect=HTTP_CONNECT_TIMEOUT_SECONDS, read=None, write=None, pool=HTTP_POOL_TIMEOUT_SECONDS
            ),
            transport=transport,
        )

    def close(self) -> None:
        """Close the HTTP client."""
        self._http.close()

    def sql(self, statement: str, *, database: str | None = None) -> list[Any]:
        """Run ``statement`` on ``/sql``; raise on a non-200 or any ``ERR`` statement result."""
        headers = {"Surreal-DB": database} if database is not None else {}
        response = self._http.post("/sql", content=statement.encode("utf-8"), headers=headers)
        if response.status_code != httpx.codes.OK:
            raise RestoreRefusedError(f"/sql answered HTTP {response.status_code}: {response.text[:300]!r}")
        results: list[dict[str, Any]] = response.json()
        failed = [result for result in results if result.get("status") != "OK"]
        if failed:
            raise RestoreRefusedError(f"/sql statement failed: {str(failed[0].get('result'))[:300]!r}")
        return [result.get("result") for result in results]

    def databases(self) -> set[str]:
        """The database names in this client's namespace (``INFO FOR NS``)."""
        info = self.sql("INFO FOR NS;")[0]
        return set(info.get("databases", {}))

    def import_file(self, database: str, slice_path: Path) -> None:
        """``POST /import`` the file, streamed. Clean iff HTTP 200 + a body of exactly ``[]`` (module doc)."""
        with slice_path.open("rb") as body:
            response = self._http.post(
                "/import",
                content=body,
                headers={"Surreal-DB": database, "Content-Length": str(slice_path.stat().st_size)},
            )
        self.check_import_response(response.status_code, response.text)

    @staticmethod
    def check_import_response(status_code: int, text: str) -> None:
        """Raise :class:`ImportRejectedError` unless ``status_code`` is 200 and ``text`` parses to ``[]``."""
        try:
            body: Any = json.loads(text)
        except ValueError:
            body = None
        if status_code == httpx.codes.OK and body == []:
            return
        if isinstance(body, list):
            errors = [entry for entry in body if isinstance(entry, dict)]
            rendered = "\n".join(
                f"  - [{entry.get('status')}] {str(entry.get('result'))[:RENDERED_ERROR_CHARS]}"
                for entry in errors[:RENDERED_ERROR_LIMIT]
            )
            elided = len(errors) - min(len(errors), RENDERED_ERROR_LIMIT)
            tail = f"\n  (+{elided} more ERR entries not shown)" if elided else ""
            raise ImportRejectedError(
                f"/import answered HTTP {status_code} with {len(errors)} ERR entr(y/ies) — the import is NOT "
                f"atomic, so statements after a failure may have landed:\n{rendered}{tail}"
            )
        raise ImportRejectedError(f"/import answered HTTP {status_code}: {text[:RENDERED_ERROR_CHARS]!r}")


# --------------------------------------------------------------------------- #
# DB minting, reaping, read-back.
# --------------------------------------------------------------------------- #


def mint_database_name(now: datetime | None = None) -> str:
    """``test_dump_<UTC stamp>_<uuid4 hex>`` — never an existing name (the caller asserts absence)."""
    stamp = (now or datetime.now(UTC)).strftime(DATABASE_STAMP_FORMAT)
    return f"{DATABASE_PREFIX}{stamp}_{uuid.uuid4().hex}"


def validate_reapable(name: str) -> str:
    """Refuse any name outside :data:`DATABASE_NAME_PATTERN` (``--reap`` never touches a foreign DB)."""
    if not DATABASE_NAME_PATTERN.match(name):
        raise RestoreRefusedError(
            f"refusing to reap {name!r}: only databases this driver mints ({DATABASE_NAME_PATTERN.pattern}) "
            "may be reaped"
        )
    return name


def _test_namespace() -> str:
    harness, _, _ = _test_helpers()
    namespace: str = harness.TEST_NAMESPACE
    return namespace


def _harness_env(credentials: StoreCredentials, database: str) -> Any:
    """The harness's connection topology, built from the CONSTANT — its env-override readers are bypassed."""
    harness, _, _ = _test_helpers()
    return harness.SurrealEnv(
        url=RPC_ENDPOINT,
        user=credentials.user,
        password=credentials.password,
        namespace=harness.TEST_NAMESPACE,
        database=database,
        dim=READBACK_EMBEDDING_DIM,
    )


def mint_database(client: StoreClient) -> str:
    """Mint a name, assert it absent, and ``DEFINE DATABASE`` it (a plain DEFINE errors if it exists)."""
    name = mint_database_name()
    if name in client.databases():
        raise RestoreRefusedError(f"minted database {name} already exists — refusing to import into it")
    client.sql(f"DEFINE DATABASE {name};")
    return name


def reap_database(credentials: StoreCredentials, client: StoreClient, name: str) -> None:
    """Remove a minted DB through the harness's retry-seamed teardown, then PROVE it is gone."""
    validate_reapable(name)
    harness, _, _ = _test_helpers()
    asyncio.run(harness.drop_database(_harness_env(credentials, name)))
    if name in client.databases():
        raise RestoreRefusedError(f"reap of {name} did not remove it (still listed by INFO FOR NS)")


async def _read_back(
    credentials: StoreCredentials, database: str, tables: Sequence[str], governed: Sequence[str]
) -> tuple[dict[str, int], dict[str, int]]:
    """Counts over a SECOND connection (WS SDK), through loremaster's ONE ``run_query`` driver."""
    harness, contract, _ = _test_helpers()
    from loremaster.store._txn import run_query

    from loremaster import governed as governed_module

    connection = await harness.connect_admin(_harness_env(credentials, database))
    try:
        handle, _calls = contract.store_handle(connection, url=RPC_ENDPOINT)
        counts: dict[str, int] = {}
        for table in tables:
            rows = await run_query(
                acquire=handle.acquire,
                drop=handle.drop,
                url=handle.url,
                noun="restore read-back count",
                label="restore_prod_dump.readback.rejected",
                statement=f"SELECT count() FROM {_validate_table_name(table)} GROUP ALL",
                params={},
                logger=LOGGER,
            )
            counts[table] = int(rows[0]["count"]) if isinstance(rows, list) and rows else 0
        unmigrated = {
            table: await governed_module.report_unmigrated_governed_rows(handle, table) for table in governed
        }
        return counts, unmigrated
    finally:
        await connection.close()


# --------------------------------------------------------------------------- #
# The run.
# --------------------------------------------------------------------------- #


@dataclass
class RestoreReport:
    """Everything a run measured, for the receipt."""

    database: str
    scan: ScanResult
    request: SliceRequest
    readback: dict[str, int]
    unmigrated: dict[str, int]
    legacy_shape: dict[str, bool]
    elapsed: dict[str, float]


def _available_memory_bytes() -> int | None:
    try:
        for line in MEMINFO_PATH.read_text().splitlines():
            if line.startswith("MemAvailable:"):
                return int(line.split()[1]) * 1024
    except OSError:
        return None
    return None


def newest_dump() -> Path:
    """The newest ``lore-prod-*.surql`` in :data:`DUMP_DIRECTORY` (names carry a sortable UTC stamp)."""
    dumps = sorted(DUMP_DIRECTORY.glob(DUMP_GLOB))
    if not dumps:
        raise RestoreRefusedError(f"no {DUMP_GLOB} in {DUMP_DIRECTORY}")
    return dumps[-1]


def verify(report: RestoreReport) -> list[str]:
    """Every declared-vs-read-back disagreement, as sentences (empty = clean)."""
    problems: list[str] = []
    for table in report.scan.tables_seen:
        if not report.request.wants(table):
            continue
        declared = report.scan.declared_rows.get(table, 0)
        actual = report.readback.get(table)
        if actual != declared:
            problems.append(f"{table}: the dump declares {declared} row(s), the store reads back {actual}")
    for table, unmigrated in report.unmigrated.items():
        if report.legacy_shape.get(table) and unmigrated != report.readback.get(table):
            problems.append(
                f"{table}: a pre-63 table (no governed trio in the dump's DDL) must read back ALL rows "
                f"unmigrated; read {unmigrated} of {report.readback.get(table)}"
            )
    return problems


def render_report(report: RestoreReport, stream: TextIO) -> None:
    """The receipt, to ``stream`` (stderr)."""
    scan = report.scan
    by_name = report.request.by_name()
    print(f"restore_prod_dump: dump {scan.dump} ({scan.dump_bytes} B)", file=stream)
    print(
        f"restore_prod_dump: mode {'full' if report.request.full else 'slice'} — slice {scan.slice_bytes} B; "
        f"preamble sections {', '.join(scan.preamble_sections)}; export log lines stripped "
        f"{scan.log_lines_stripped}",
        file=stream,
    )
    print(f"restore_prod_dump: endpoint {HTTP_ENDPOINT} (import) + {RPC_ENDPOINT} (read-back)", file=stream)
    header = f"{'table':<16} {'provenance':<11} {'declared':>9} {'readback':>9} {'scope NONE':>10}  note"
    print(header, file=stream)
    names = [table for table in scan.tables_seen if report.request.wants(table)]
    for name in names:
        spec = by_name.get(name)
        unmigrated = report.unmigrated.get(name)
        if unmigrated is None:
            note = ""
        elif report.legacy_shape.get(name):
            note = "pre-63 shape: scope NONE must == rows"
        else:
            note = "governed shape in dump: reported only"
        print(
            f"{name:<16} {spec.provenance if spec else 'full':<11} {scan.declared_rows.get(name, 0):>9} "
            f"{report.readback.get(name, '-')!s:>9} {'' if unmigrated is None else unmigrated!s:>10}  {note}",
            file=stream,
        )
    absent = [table for table in report.request.tables if table.name not in scan.tables_seen]
    for table in absent:
        print(
            f"{table.name:<16} {table.provenance:<11} {'ABSENT':>9}  the dump predates it ({table.reason})",
            file=stream,
        )
    elapsed = ", ".join(f"{phase} {seconds:.1f}s" for phase, seconds in report.elapsed.items())
    print(f"restore_prod_dump: elapsed {elapsed}", file=stream)
    print(f"restore_prod_dump: database {report.database} (namespace {_test_namespace()})", file=stream)


def restore(
    dump: Path,
    request: SliceRequest,
    *,
    credentials: StoreCredentials,
    stream: TextIO = sys.stderr,
    enforce_memory_floor: bool = True,
    scanner_type: type[ExportScanner] = ExportScanner,
    on_mint: Callable[[str], None] | None = None,
) -> RestoreReport:
    """Scan → mint → import → read back → verify. Reaps the DB on ANY failure after the mint.

    ``scanner_type`` exists for ONE caller: the self-test's tampered-count control, which substitutes a
    scanner that misdeclares a count so the verify-mismatch path is proven to fire (and to reap).
    ``on_mint`` receives the minted name the moment it exists, so a caller can prove THAT database was
    reaped on failure (a before/after set diff of the namespace races concurrent minters under xdist)."""
    started = time.monotonic()
    elapsed: dict[str, float] = {}
    deriver = SliceDeriver()
    with tempfile.TemporaryDirectory(prefix="restore_prod_dump_", dir=SLICE_SCRATCH_ROOT) as scratch:
        slice_path = Path(scratch) / "slice.surql"
        with slice_path.open("w", encoding="utf-8", newline="") as output:
            scan = scanner_type(request).scan(dump, output)
        elapsed["scan"] = time.monotonic() - started
        if enforce_memory_floor:
            available = _available_memory_bytes()
            if available is not None and available < MIN_AVAILABLE_MEMORY_BYTES:
                raise RestoreRefusedError(
                    f"available memory {available / 1024**3:.1f} GiB is under the "
                    f"{MIN_AVAILABLE_MEMORY_BYTES / 1024**3:.0f} GiB floor — refusing to start an import"
                )
        client = StoreClient(credentials, _test_namespace())
        database: str | None = None
        try:
            database = mint_database(client)
            if on_mint is not None:
                on_mint(database)
            phase = time.monotonic()
            client.import_file(database, slice_path)
            elapsed["import"] = time.monotonic() - phase
            imported = [table for table in scan.tables_seen if request.wants(table)]
            by_name = request.by_name()
            governed = [
                table for table in imported if (spec := by_name.get(table)) is not None and spec.governed_node
            ]
            phase = time.monotonic()
            readback, unmigrated = asyncio.run(_read_back(credentials, database, imported, governed))
            elapsed["readback"] = time.monotonic() - phase
            elapsed["total"] = time.monotonic() - started
            legacy_shape = {
                table: not deriver.is_governed_shape(table, scan.table_ddl.get(table, ""))
                for table in governed
            }
            report = RestoreReport(database, scan, request, readback, unmigrated, legacy_shape, elapsed)
            render_report(report, stream)
            problems = verify(report)
            if problems:
                raise VerifyMismatchError("; ".join(problems))
            return report
        except BaseException:
            if database is not None:
                reap_database(credentials, client, database)
                print(f"restore_prod_dump: FAILED — reaped {database}", file=stream)
            raise
        finally:
            client.close()


# --------------------------------------------------------------------------- #
# Self-test — the controls (§D-3 step 6 + the rider table's driver row).
# --------------------------------------------------------------------------- #

#: A 40-line synthetic export: two tables, the export's log lines at both ends, a preamble, and hostile
#: rows (a row-shaped forgery inside a string, brackets/quotes/⟨⟩/backticks/escapes inside strings, and a
#: section-header-shaped string mid-line). Declared rows: alpha 4, beta 2.
SYNTHETIC_EXPORT = "\n".join(
    [
        "2026-09-26T00:00:00.000000Z  INFO surrealdb::method::export: Exporting bytes",
        "-- ------------------------------",
        "-- OPTION",
        "-- ------------------------------",
        "",
        "OPTION IMPORT;",
        "",
        "-- ------------------------------",
        "-- SEQUENCES",
        "-- ------------------------------",
        "",
        "DEFINE SEQUENCE alpha_seq BATCH 1000 START 0;",
        "",
        "-- ------------------------------",
        "-- TABLE: alpha",
        "-- ------------------------------",
        "",
        "DEFINE TABLE alpha TYPE NORMAL SCHEMAFULL PERMISSIONS NONE;",
        "DEFINE FIELD OVERWRITE body ON alpha TYPE string PERMISSIONS FULL;",
        "DEFINE FIELD OVERWRITE tags ON alpha TYPE array<string> PERMISSIONS FULL;",
        "",
        "-- ------------------------------",
        "-- TABLE DATA: alpha",
        "-- ------------------------------",
        "",
        (
            "INSERT [ { body: 'plain', id: alpha:one, tags: [] }, { body:"
            ' "it\'s {not} a row: }, { id: alpha:forged }", id: alpha:two,'
            " tags: ['[', '{'] }, { body: 'line\\\\nbreak \\\\\\\\ `tick` ⟨x⟩ ]"
            "]', id: alpha:⟨three-x⟩, tags: ['}'] } ];"
        ),
        "INSERT [ { body: '-- TABLE: beta', id: alpha:four, tags: [] } ];",
        "",
        "-- ------------------------------",
        "-- TABLE: beta",
        "-- ------------------------------",
        "",
        "DEFINE TABLE beta TYPE NORMAL SCHEMALESS PERMISSIONS NONE;",
        "",
        "-- ------------------------------",
        "-- TABLE DATA: beta",
        "-- ------------------------------",
        "",
        'INSERT [ { id: beta:one }, { id: beta:two, note: "{ id: beta:forged }" } ];',
        "2026-09-26T00:00:01.000000Z  INFO surrealdb_server::cli::export: "
        "The SurrealQL file was exported successfully",
        "",
    ]
)
SYNTHETIC_DECLARED = {"alpha": 4, "beta": 2}


class _MisdeclaringScanner(ExportScanner):
    """A scanner that declares ONE extra ``beta`` row — the tampered-count control's wrong input."""

    def _check(self, result: ScanResult) -> None:
        super()._check(result)
        result.declared_rows["beta"] = result.declared_rows.get("beta", 0) + 1


class SelfTest:
    """The driver's controls. Each ``leg_*`` raises :class:`SelfTestFailure` when its control fails."""

    OFFLINE_LEGS = (
        "leg_slice_precision_recall_and_missing_refusal",
        "leg_row_count_skips_quoted_forgeries",
        "leg_format_alarms_refuse",
        "leg_endpoint_is_a_constant_and_guarded",
        "leg_stores_env_file_and_ports_match_the_quadlets",
        "leg_database_name_pattern_and_reap_refusal",
        "leg_derived_slice_covers_amendment_3",
        "leg_import_response_rule",
    )
    LIVE_LEGS = (
        "leg_live_import_visible_reaped_and_deterministic",
        "leg_live_runtime_error_mid_file_is_rejected",
        "leg_live_parse_error_mid_file_is_rejected",
        "leg_live_tampered_declared_count_is_a_mismatch",
        "leg_live_define_database_refuses_an_existing_name",
    )

    def __init__(self, scratch: Path) -> None:
        self.scratch = scratch

    # -- helpers ---------------------------------------------------------- #

    def _write(self, name: str, text: str) -> Path:
        path = self.scratch / name
        path.write_text(text, encoding="utf-8")
        return path

    @staticmethod
    def _request(*names: str, required: bool = True) -> SliceRequest:
        return SliceRequest(
            tables=tuple(SliceTable(name=n, provenance="explicit", required=required) for n in names)
        )

    def _scan(self, text: str, *names: str) -> tuple[ScanResult, str]:
        dump = self._write("synthetic.surql", text)
        out_path = self.scratch / "synthetic.slice.surql"
        with out_path.open("w", encoding="utf-8", newline="") as output:
            result = ExportScanner(self._request(*names)).scan(dump, output)
        return result, out_path.read_text(encoding="utf-8")

    @staticmethod
    def _expect(condition: bool, message: str) -> None:
        if not condition:
            raise SelfTestFailure(message)

    def _expect_refused(self, action: Callable[[], object], needle: str) -> None:
        try:
            action()
        except RestoreRefusedError as error:
            self._expect(needle in str(error), f"refused for the WRONG reason (wanted {needle!r}): {error}")
            return
        raise SelfTestFailure(f"expected a refusal naming {needle!r}; the action succeeded")

    # -- offline legs ------------------------------------------------------ #

    def leg_slice_precision_recall_and_missing_refusal(self) -> None:
        """Requested table found (DDL + DATA); un-requested omitted; a missing required one refused."""
        result, text = self._scan(SYNTHETIC_EXPORT, "alpha")
        self._expect(
            "DEFINE TABLE alpha" in text and "id: alpha:four" in text, "recall: alpha DDL/DATA missing"
        )
        self._expect(
            "OPTION IMPORT;" in text and "alpha_seq" in text, "recall: preamble missing from the slice"
        )
        self._expect("DEFINE TABLE beta" not in text and "beta:one" not in text, "precision: beta leaked in")
        self._expect(not EXPORT_LOG_LINE_PATTERN.search(text), "the export log lines were not stripped")
        self._expect(result.log_lines_stripped == 2, f"stripped {result.log_lines_stripped} log lines, not 2")
        self._expect(result.tables_seen == ["alpha", "beta"], f"tables seen {result.tables_seen}")
        both, both_text = self._scan(SYNTHETIC_EXPORT, "alpha", "beta")
        self._expect("beta:one" in both_text, "recall: requested beta missing")
        self._expect(both.declared_rows == SYNTHETIC_DECLARED, f"declared rows {both.declared_rows}")
        self._expect_refused(lambda: self._scan(SYNTHETIC_EXPORT, "alpha", "gamma"), "gamma")

    def leg_row_count_skips_quoted_forgeries(self) -> None:
        """Row counts are exact past strings holding brackets, quotes, ⟨⟩, backticks and escapes."""
        cases = {
            "INSERT [ { a: 1 } ];": 1,
            "INSERT [ ];": 0,
            "INSERT [ { a: '}, { b: 2' }, { c: \"it's ] }\" } ];": 2,
            "INSERT RELATION [ { id: e:1, in: a:⟨x}y⟩, out: b:`{`, w: [ { n: 1 }, { n: 2 } ] } ];": 1,
            "INSERT [ { a: 'esc \\' { quote' }, { a: 'x' } ];": 2,
        }
        for statement, expected in cases.items():
            counted = count_insert_rows(statement)
            self._expect(counted == expected, f"counted {counted}, expected {expected}: {statement}")
        for broken in (
            "INSERT [ { a: 1 ];",
            "INSERT [ { a: 1 } ] ];",
            "INSERT [ { a: 1 } ]; INSERT [ { } ];",
        ):
            self._expect_refused(functools.partial(count_insert_rows, broken), "")

    def leg_format_alarms_refuse(self) -> None:
        """No OPTION IMPORT, junk before the first section, a non-INSERT data line, no sections → refused."""
        no_option = SYNTHETIC_EXPORT.replace("OPTION IMPORT;", "DEFINE PARAM $x VALUE 1;")
        self._expect_refused(lambda: self._scan(no_option, "alpha"), "first statement")
        junk = "garbage line\n" + SYNTHETIC_EXPORT
        self._expect_refused(lambda: self._scan(junk, "alpha"), "before the first section")
        bad_data = SYNTHETIC_EXPORT.replace("INSERT [ { id: beta:one }", "UPSERT [ { id: beta:one }")
        self._expect_refused(lambda: self._scan(bad_data, "beta"), "format changed")
        rule = "-- ------------------------------"
        no_sections = f"{rule}\n-- OPTION\n{rule}\nOPTION IMPORT;\n"
        self._expect_refused(lambda: self._scan(no_sections), "no `-- TABLE")

    def leg_endpoint_is_a_constant_and_guarded(self) -> None:
        """No endpoint/port/db flag; the harness URL override is ignored; :18500 refused pre-transport."""
        self._expect(STORE_PORT != PRODUCTION_PORT, "the store constant IS the production port")
        for url in (HTTP_ENDPOINT, RPC_ENDPOINT):
            self._expect(httpx.URL(url).port == STORE_PORT, f"{url} does not address {STORE_PORT}")
        parser = build_parser()
        for flags in (["--endpoint", "x"], ["--port", "18500"], ["--db", "lore"], ["--d", "lore"]):
            try:
                with contextlib.redirect_stderr(io.StringIO()):
                    parser.parse_args(flags)
            except SystemExit:
                continue
            raise SelfTestFailure(f"the parser ACCEPTED {flags} — the endpoint/DB must be unrepresentable")
        saved = os.environ.get(HARNESS_URL_OVERRIDE_VAR)
        os.environ[HARNESS_URL_OVERRIDE_VAR] = f"ws://{STORE_HOST}:{PRODUCTION_PORT}/rpc"
        try:
            env = _harness_env(StoreCredentials(user="u", password=SecretStr("p")), "test_dump_x")
            self._expect(env.url == RPC_ENDPOINT, f"the harness override retargeted the driver to {env.url}")
        finally:
            if saved is None:
                os.environ.pop(HARNESS_URL_OVERRIDE_VAR, None)
            else:
                os.environ[HARNESS_URL_OVERRIDE_VAR] = saved
        sent: list[str] = []

        def record(request: httpx.Request) -> httpx.Response:
            sent.append(str(request.url))
            return httpx.Response(httpx.codes.OK, json=[])

        client = StoreClient(
            StoreCredentials(user="u", password=SecretStr("p")),
            "lore_test",
            transport=httpx.MockTransport(record),
        )
        try:
            try:
                client._http.post(f"http://{STORE_HOST}:{PRODUCTION_PORT}/sql", content=b"RETURN 1;")
            except ForeignEndpointError:
                pass
            else:
                raise SelfTestFailure("a request to the production port was NOT refused")
            self._expect(sent == [], f"the refused request still reached the transport: {sent}")
            client._http.post("/sql", content=b"RETURN 1;")  # positive control: the constant passes
            self._expect(len(sent) == 1 and f":{STORE_PORT}/" in sent[0], f"control request not sent: {sent}")
        finally:
            client.close()

    def leg_stores_env_file_and_ports_match_the_quadlets(self) -> None:
        """The TEST quadlet binds :18000 and names STORES_ENV_FILE; the PRODUCTION one binds :18500."""
        for quadlet, port in ((TEST_STORE_QUADLET, STORE_PORT), (PRODUCTION_STORE_QUADLET, PRODUCTION_PORT)):
            if not quadlet.is_file():
                raise SelfTestFailure(f"{quadlet} is missing — cannot cross-check the endpoint constant")
            lines = quadlet.read_text(encoding="utf-8").splitlines()
            self._expect(
                any(line.startswith("Exec=") and f"--bind {STORE_HOST}:{port}" in line for line in lines),
                f"{quadlet.name} does not bind {STORE_HOST}:{port}",
            )
            self._expect(
                f"EnvironmentFile={STORES_ENV_FILE}" in lines, f"{quadlet.name} names another env file"
            )

    def leg_database_name_pattern_and_reap_refusal(self) -> None:
        """Minted names match the pattern; the reap refuses every foreign name."""
        for _ in range(3):
            name = mint_database_name()
            self._expect(DATABASE_NAME_PATTERN.match(name) is not None, f"minted {name!r} misses the pattern")
            validate_reapable(name)
        for foreign in (
            "lore",
            "test_123_abc",
            "test_dump_x",
            f"{mint_database_name()};REMOVE NS lore_test",
            "",
        ):
            self._expect_refused(functools.partial(validate_reapable, foreign), "refusing to reap")

    def leg_derived_slice_covers_amendment_3(self) -> None:
        """The derived default slice ⊇ §D-3's named set; every table carries a provenance."""
        request = SliceDeriver().governed_slice()
        names = request.names()
        self._expect(
            AMENDMENT_3_NAMED_SLICE <= names, f"slice lacks {sorted(AMENDMENT_3_NAMED_SLICE - names)}"
        )
        derived = {table.name for table in request.tables if table.provenance == "derived"}
        self._expect(
            "memory" in derived, f"the derivation lost memory (governed since 63a): {sorted(derived)}"
        )
        grown = SliceDeriver(
            "DEFINE FIELD OVERWRITE owner_principal ON zeta TYPE option<string>;\n"
            "DEFINE FIELD OVERWRITE owner_agent ON zeta TYPE option<string>;\n"
            "DEFINE FIELD OVERWRITE scope ON zeta TYPE option<string>;\n"
        ).governed_slice()
        self._expect("zeta" in grown.names(), "a synthetic governed table did not grow the derived slice")

    def leg_import_response_rule(self) -> None:
        """Only HTTP 200 + ``[]`` is clean; a 200 carrying ERR entries is rejected."""
        StoreClient.check_import_response(httpx.codes.OK, "[]")
        for status, text in (
            (200, '[{"status":"ERR","result":"Database record `b:1` already exists"}]'),
            (400, '{"code":400,"information":"Invalid statement"}'),
            (200, "not json"),
        ):
            try:
                StoreClient.check_import_response(status, text)
            except ImportRejectedError:
                continue
            raise SelfTestFailure(f"HTTP {status} {text!r} was accepted as a clean import")

    # -- live legs (:18000) ------------------------------------------------ #

    def _live_restore(
        self,
        text: str,
        name: str,
        scanner_type: type[ExportScanner] = ExportScanner,
        minted: list[str] | None = None,
    ) -> RestoreReport:
        return restore(
            self._write(name, text),
            self._request("alpha", "beta"),
            credentials=StoreCredentials.from_env_file(),
            stream=io.StringIO(),
            enforce_memory_floor=False,
            scanner_type=scanner_type,
            on_mint=None if minted is None else minted.append,
        )

    def _databases(self) -> set[str]:
        client = StoreClient(StoreCredentials.from_env_file(), _test_namespace())
        try:
            return client.databases()
        finally:
            client.close()

    def _reap(self, name: str) -> None:
        credentials = StoreCredentials.from_env_file()
        client = StoreClient(credentials, _test_namespace())
        try:
            reap_database(credentials, client, name)
        finally:
            client.close()

    def leg_live_import_visible_reaped_and_deterministic(self) -> None:
        """Import VISIBLE over a second connection; identical counts in a fresh DB; the reap removes both."""
        first = self._live_restore(SYNTHETIC_EXPORT, "live-1.surql")
        second: RestoreReport | None = None
        try:
            self._expect(first.readback == SYNTHETIC_DECLARED, f"read back {first.readback}")
            self._expect(first.database in self._databases(), "the imported DB is not listed")
            second = self._live_restore(SYNTHETIC_EXPORT, "live-2.surql")
            self._expect(second.database != first.database, "the second run reused the first DB")
            self._expect(
                second.readback == first.readback, f"non-deterministic: {first.readback} vs {second.readback}"
            )
        finally:
            for report in (first, second):
                if report is not None:
                    self._reap(report.database)
        listed = self._databases()
        self._expect(first.database not in listed, "the reap did not remove the first DB")
        self._expect(second is None or second.database not in listed, "the reap did not remove the second DB")

    def _expect_failure_reaped(
        self,
        text: str,
        name: str,
        error_type: type[Exception],
        scanner_type: type[ExportScanner] = ExportScanner,
    ) -> Exception:
        """Run a restore that MUST fail with ``error_type``; prove the DB it minted is gone afterwards."""
        minted: list[str] = []
        try:
            self._live_restore(text, name, scanner_type=scanner_type, minted=minted)
        except error_type as error:
            self._expect(len(minted) == 1, f"{name}: expected exactly one minted DB, saw {minted}")
            self._expect(minted[0] not in self._databases(), f"{name}: the failed restore left {minted[0]}")
            return error
        for database in minted:  # an unexpected SUCCESS leaves its DB for the caller — reap it here
            self._reap(database)
        raise SelfTestFailure(f"{name}: a broken restore was accepted as clean (minted and reaped {minted})")

    def leg_live_runtime_error_mid_file_is_rejected(self) -> None:
        """A runtime ERR mid-file (HTTP 200!) is rejected, and the minted DB is reaped."""
        broken = SYNTHETIC_EXPORT.replace(
            "DEFINE TABLE beta TYPE NORMAL SCHEMALESS PERMISSIONS NONE;",
            "DEFINE TABLE beta TYPE NORMAL SCHEMALESS PERMISSIONS NONE;\n"
            "CREATE beta:clash;\nCREATE beta:clash;",
        )
        self._expect_failure_reaped(broken, "live-runtime-error.surql", ImportRejectedError)

    def leg_live_parse_error_mid_file_is_rejected(self) -> None:
        """A parse error mid-file truncates the import (HTTP 200!) — rejected, DB reaped."""
        broken = SYNTHETIC_EXPORT.replace(
            "DEFINE TABLE beta TYPE NORMAL SCHEMALESS PERMISSIONS NONE;",
            "DEFINE TABLE beta TYPE NORMAL SCHEMALESS PERMISSIONS NONE;\nSELECT FROM WHERE };",
        )
        self._expect_failure_reaped(broken, "live-parse-error.surql", ImportRejectedError)

    def leg_live_tampered_declared_count_is_a_mismatch(self) -> None:
        """A clean import whose declared count disagrees with the read-back is a STOP (and is reaped)."""
        error = self._expect_failure_reaped(
            SYNTHETIC_EXPORT, "live-tampered.surql", VerifyMismatchError, scanner_type=_MisdeclaringScanner
        )
        self._expect(
            "beta" in str(error) and "alpha" not in str(error), f"mismatch named the wrong table: {error}"
        )

    def leg_live_define_database_refuses_an_existing_name(self) -> None:
        """The engine-side second guard: a plain ``DEFINE DATABASE`` on an existing name errors."""
        credentials = StoreCredentials.from_env_file()
        client = StoreClient(credentials, _test_namespace())
        name = mint_database(client)
        try:
            try:
                client.sql(f"DEFINE DATABASE {name};")
            except RestoreRefusedError as error:
                self._expect("already exists" in str(error), f"refused for another reason: {error}")
            else:
                raise SelfTestFailure("a second plain DEFINE DATABASE on an existing name succeeded")
        finally:
            reap_database(credentials, client, name)
            client.close()

    # -- runner ------------------------------------------------------------ #

    def run(self, *, offline: bool, stream: TextIO) -> bool:
        """Run every leg; print PASS/FAIL per leg; True iff all held."""
        legs = self.OFFLINE_LEGS + (() if offline else self.LIVE_LEGS)
        failures = 0
        for leg in legs:
            try:
                getattr(self, leg)()
            except Exception as error:
                failures += 1
                print(f"FAIL {leg}: {type(error).__name__}: {error}", file=stream)
            else:
                print(f"PASS {leg}", file=stream)
        print(f"self-test: {len(legs) - failures}/{len(legs)} legs held", file=stream)
        return failures == 0


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def build_parser() -> argparse.ArgumentParser:
    """The CLI. No endpoint, port or DB flag exists — by construction (§D-3 steps 1-2)."""
    parser = argparse.ArgumentParser(
        prog="restore_prod_dump.py",
        description="Restore the governed slice of a `surreal export` into a minted TEST database.",
        allow_abbrev=False,
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--full", action="store_true", help="import every section (GBs; slow)")
    mode.add_argument("--tables", help="comma-separated explicit slice (every named table REQUIRED)")
    mode.add_argument("--reap", metavar="NAME", help="remove a database this driver minted")
    mode.add_argument("--self-test", action="store_true", help="run the controls")
    parser.add_argument(
        "--dump", type=Path, help=f"the export (default: newest {DUMP_DIRECTORY}/{DUMP_GLOB})"
    )
    parser.add_argument("--offline", action="store_true", help="with --self-test: skip the live legs")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Entry point; returns the exit code."""
    arguments = build_parser().parse_args(argv)
    logging.getLogger("loremaster.governed").setLevel(logging.ERROR)  # the receipt renders that count itself
    try:
        if arguments.self_test:
            with tempfile.TemporaryDirectory(
                prefix="restore_prod_dump_selftest_", dir=SLICE_SCRATCH_ROOT
            ) as scratch:
                held = SelfTest(Path(scratch)).run(offline=arguments.offline, stream=sys.stderr)
            return EXIT_OK if held else EXIT_SELF_TEST_FAILED
        if arguments.reap:
            validate_reapable(arguments.reap)  # refuse a foreign name before reading any credential
        credentials = StoreCredentials.from_env_file()
        if arguments.reap:
            client = StoreClient(credentials, _test_namespace())
            try:
                reap_database(credentials, client, arguments.reap)
            finally:
                client.close()
            print(f"restore_prod_dump: reaped {arguments.reap} (absent from INFO FOR NS)", file=sys.stderr)
            return EXIT_OK
        dump: Path = arguments.dump or newest_dump()
        if not dump.is_file():
            raise RestoreRefusedError(f"{dump} is not a file")
        if arguments.full:
            request = SliceRequest(tables=(), full=True)
        elif arguments.tables:
            request = explicit_slice(name.strip() for name in arguments.tables.split(",") if name.strip())
        else:
            request = SliceDeriver().governed_slice()
        report = restore(dump, request, credentials=credentials)
    except RestoreRefusedError as error:
        print(f"restore_prod_dump: REFUSED — {error}", file=sys.stderr)
        return EXIT_REFUSED
    except ImportRejectedError as error:
        print(f"restore_prod_dump: IMPORT REJECTED — {error}", file=sys.stderr)
        return EXIT_IMPORT_REJECTED
    except VerifyMismatchError as error:
        print(f"restore_prod_dump: VERIFY MISMATCH (silent partial import) — {error}", file=sys.stderr)
        return EXIT_VERIFY_MISMATCH
    print(f"{DATABASE_ENV_VAR}={report.database}")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
