#!/usr/bin/env python3
"""Probe: the packet-61b PDP READ-filter emitter's index behaviour, BY CONSTRUCTION.

WHY (packet 61 — the in-process authorization PDP; design
``docs/design/2026-08-22-packet61-pdp-audit-rulings.md`` Forks C/E/F). The PDP's
``authorize_filter`` emits a SurrealQL WHERE fragment for the governed-row READ
predicate (Fork C):

    (scope='agent-private' AND owner_principal=$p AND owner_agent=$a)
      OR (scope='principal-private' AND owner_principal=$p)
      OR scope='server'
      OR scope IN $my_keep_scopes

Fork E rules ``owner`` as TWO indexed record-link fields (``owner_principal
record<principal>`` + ``owner_agent record<agent>``) rather than one composite ref,
so every disjunct is a flat equality/``IN`` on an indexed column — NO sub-field hop,
NO arrow traversal (store-law §4). But Fork E names THREE things as BELIEVED, not
known, until probed on the live 3.2.4 engine — the #107-class hazard (a query green
on a small/virgin test DB that TableScans in production on a large dirty store):

  E1. Does a defined index on ``scope`` serve ``WHERE scope IN $set`` as an
      IndexScan, or a TableScan?  Store-law §2 proves ``=`` (IndexScan) and range
      (IndexScan) but has NOT probed ``IN``.  The keep-read disjunct
      (``scope IN $my_keep_scopes``) rests on this.
  E2. Composite-index shape.  Store-law §2: composite indexes are LEADING-COLUMN
      only.  Which index SET does the disjunction need — a single composite, or
      separate indexes on ``scope`` and ``owner_principal``?
  E3. ⚠ THE OR-PLANNER (the load-bearing probe).  Does SurrealDB use the indexes
      for an OR of indexed predicates, or does an OR force a whole-table scan?  If
      the OR TableScans while each disjunct alone IndexScans, the emitter (Fork A
      ``to_surql``) MUST be a UNION of per-clause IndexScans (or an accepted bounded
      TableScan) — NOT a flat OR.  This is exactly the #107 shape.

Fork F rules the visible-Keeps resolver as a plain-table read of the EXISTING
``member_of`` edge — ``SELECT out FROM member_of WHERE in = $principal`` (the LEADING
column of the packet-60 ``UNIQUE(in, out)`` index), never an arrow traversal.  So:

  F.  Does ``member_of WHERE in = $p`` (leading column, plain table) IndexScan?  And
      does ``WHERE out = $keep`` (trailing column — what ``list_household`` does)
      TableScan (proving leading-vs-trailing discrimination, store-law §2)?

METHOD (store-law discipline, §2 IndexScan-vs-TableScan-via-EXPLAIN + §4 "a probe
NEEDS a positive control"). Each scan claim is a live EXPLAIN plan on the REAL 3.2.4
engine, classified by the SAME plan-walker the shipped packet-60 pin uses
(``test_keeps_schema.py::TestTheKeeperIndexFires`` — ``operator == 'IndexScan'`` /
``'TableScan'`` with ``attributes.table``).  Every discovery is bracketed by POSITIVE
CONTROLS: a ``WHERE scope = 'x'`` the walker MUST classify IndexScan, and a
``WHERE <unindexed col> = 'x'`` (and an unindexed OR) it MUST classify TableScan — so
an instrument that could not SEE a TableScan is caught, not trusted (store-ref §4:
"the instrument's first run said the opposite … only the positive control exposed it").
E1 and E3 are DISCOVERIES: their scan type is OBSERVED and REPORTED, whatever it is —
an unclassifiable plan is a SURPRISE (we never guess an IndexScan, per the brief).

WHAT MAKES IT FAIL LOUD (exit non-zero):
  * any instrument-integrity control mis-classifies (the walker is blind — worthless);
  * Fork F's leading-column IndexScan assumption is FALSE, or its trailing-column
    control does not TableScan (the resolver's whole design rests on the former);
  * the composite index's leading column does not IndexScan (the E2 probe is vacuous);
  * any probed plan is UNCLASSIFIED (neither IndexScan nor TableScan of the target).
The DISCOVERY results (does IN IndexScan? does the OR IndexScan?) are NOT expectations
— they are reported, and the emitter-shape verdict is derived from them.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000`` —
creds root/spikeroot, matching ``loremaster/tests/_surreal_harness.py``), and drops
it on exit.  It NEVER touches production (lore-surreal :18500).

Store-law compliance: DDL applies through the production ``execute_transaction`` seam
(store-ref §3 — every statement's status checked, never the lax ``.query()`` that
validates only statement[0]); reads/EXPLAINs use ``.query(stmt, params)`` (a single
statement, so the statement[0]-only gap does not bite) with BOUND params, never
interpolation.

Run: ``uv run python scripts/probe_read_filter_61b.py``
Exit 0 iff every control + Fork-F assumption held and every plan was classifiable
(self-checking); non-zero on any surprise.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from typing import Any

from loremaster.store._txn import (
    bootstrap_session,
    execute_transaction,
    signin_credentials,
)
from loremaster.store.surreal_schema import (
    MEMBER_OF_RELATION,
    generate_keep_ddl,
    generate_principal_ddl,
)
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

# The synthetic governed table matching the Fork-E owner shape: two indexed
# record-link owner fields + an indexed ``scope`` + one DELIBERATELY UNINDEXED
# column (``note``) that anchors the TableScan positive controls.
GOV = "gov"
# A second synthetic table carrying a SINGLE composite index over
# ``(scope, owner_principal, owner_agent)`` — to probe leading-column-only (E2).
GOV_COMPOSITE = "gov_composite"

PRINCIPAL_TABLE = "principal"
AGENT_TABLE = "agent"
KEEP_TABLE = "keep"


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# EXPLAIN plan classification — the SAME walker the shipped packet-60 pin uses
# (``test_keeps_schema.py::TestTheKeeperIndexFires``).  Re-expressed here (a probe
# is a self-contained ``scripts/`` script — the precedent ``probe_unique_nullable_48``
# hand-rolls its own helpers rather than importing test scaffolds) and CITED, not
# forked into shared code: this is instrument parsing, not production policy.
# --------------------------------------------------------------------------- #


def _operators(plan: Any) -> list[str]:
    """Every ``operator``/``operation`` string anywhere in the EXPLAIN plan tree."""
    found: list[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, dict):
            for key in ("operator", "operation"):
                op = node.get(key)
                if isinstance(op, str):
                    found.append(op)
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


def _scans_table(plan: Any, table: str) -> bool:
    """True iff the plan carries a ``TableScan`` node targeting ``table``."""
    found = False

    def walk(node: Any) -> None:
        nonlocal found
        if isinstance(node, dict):
            attributes = node.get("attributes")
            if (
                node.get("operator") == "TableScan"
                and isinstance(attributes, dict)
                and attributes.get("table") == table
            ):
                found = True
            for child in node.values():
                walk(child)
        elif isinstance(node, list):
            for child in node:
                walk(child)

    walk(plan)
    return found


@dataclass
class ScanObservation:
    """One EXPLAIN's classified outcome, with the raw plan kept for the report."""

    label: str
    statement: str
    operators: list[str]
    has_index_scan: bool
    scans_target_table: bool
    classification: str  # IndexScan | TableScan | MIXED(index+table) | UNCLASSIFIED
    raw_plan: Any


@dataclass
class ProbeReport:
    observations: list[ScanObservation] = field(default_factory=list)
    surprises: list[str] = field(default_factory=list)

    def get(self, label: str) -> ScanObservation:
        for obs in self.observations:
            if obs.label == label:
                return obs
        raise KeyError(label)


def _classify(plan: Any, table: str) -> tuple[list[str], bool, bool, str]:
    """Return ``(operators, has_index_scan, scans_target, classification)``.

    Classifications, in priority order:

    * ``TableScan`` — a ``TableScan`` node targets ``table`` and no ``IndexScan`` is
      present (a whole-table scan — the perf hazard).
    * ``MIXED(index+table)`` — BOTH an ``IndexScan`` and a ``TableScan`` of the target
      appear (a scan still happens — NOT fully index-served).
    * ``IndexScan`` — an ``IndexScan`` node is present with no TableScan of the target.
      This covers ``IN`` (served as a ``UnionIndexScan`` whose children are ``IndexScan``
      nodes) and same-column ``OR`` — the engine unions per-value index scans.
    * ``EmptyScan`` — an ``EmptyScan`` node with no scan at all (e.g. ``scope IN []``):
      the engine PROVES zero rows and reads nothing.  Ideal, and explicitly NOT a
      TableScan — a valid, safe plan, not an unreadable one.
    * ``UNCLASSIFIED`` — none of the above: a plan shape this instrument cannot read,
      so no honest verdict is possible (we never guess an IndexScan).
    """
    operators = _operators(plan)
    has_index_scan = "IndexScan" in operators
    scans_target = _scans_table(plan, table)
    if scans_target and not has_index_scan:
        classification = "TableScan"
    elif scans_target and has_index_scan:
        classification = "MIXED(index+table)"
    elif has_index_scan:
        classification = "IndexScan"
    elif "EmptyScan" in operators:
        classification = "EmptyScan"
    else:
        classification = "UNCLASSIFIED"
    return operators, has_index_scan, scans_target, classification


async def explain(
    report: ProbeReport,
    connection: Any,
    *,
    label: str,
    select: str,
    where: str,
    table: str,
    params: dict[str, Any] | None = None,
    dump: bool = False,
) -> ScanObservation:
    """Run ``SELECT <select> FROM <table> WHERE <where> EXPLAIN`` and classify the plan.

    An UNCLASSIFIED plan is recorded as a surprise: it means the plan format is one this
    instrument cannot read, so any verdict over it would be a guess.
    """
    statement = f"SELECT {select} FROM {table} WHERE {where} EXPLAIN"
    plan = await connection.query(statement, params or {})
    operators, has_index_scan, scans_target, classification = _classify(plan, table)
    observation = ScanObservation(
        label=label,
        statement=statement,
        operators=operators,
        has_index_scan=has_index_scan,
        scans_target_table=scans_target,
        classification=classification,
        raw_plan=plan,
    )
    report.observations.append(observation)
    print(f"  [{classification:<18}] {label}")
    print(f"      {statement}")
    print(f"      operators={operators}")
    if dump:
        print("      plan=" + json.dumps(plan, default=str, indent=2).replace("\n", "\n      "))
    if classification == "UNCLASSIFIED":
        report.surprises.append(
            f"{label}: plan is UNCLASSIFIED (no IndexScan operator, no TableScan of "
            f"{table!r}) — the plan format is unreadable, so no honest verdict is "
            f"possible. operators={operators} :: {statement}"
        )
    return observation


def _require(report: ProbeReport, observation: ScanObservation, want: str, why: str) -> None:
    """A load-bearing assumption: the observation's classification MUST equal ``want``."""
    if observation.classification != want:
        report.surprises.append(
            f"{observation.label}: LOAD-BEARING assumption false — wanted {want}, got "
            f"{observation.classification}. {why} operators={observation.operators} :: "
            f"{observation.statement}"
        )


async def _apply_ddl(connection: Any, ddl: str) -> None:
    """Apply ``ddl`` through the production ``execute_transaction`` seam (store-ref §3).

    Mirrors ``_enforced_relations_scaffold.apply_ddl``: one ``BEGIN … COMMIT``, every
    statement's status checked — NOT the lax ``.query()`` that inspects only statement[0]
    and would report a green migration over a schema the engine had silently discarded.
    """

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_connection: Any) -> None:
        raise AssertionError("a DDL rejection must never drop the connection")

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=URL
    )


def _ddl(statements: list[str]) -> str:
    """Join into the ``;\\n``-terminated form ``execute_transaction`` expects."""
    return ";\n".join(statements) + ";\n"


async def _setup_schema(connection: Any) -> None:
    """Real ``principal`` + ``keep`` + ``member_of`` schema (Probe F reads the REAL
    edge index), then the two synthetic governed tables (E1/E2/E3)."""
    # The REAL packet-48/60 slices: principal (member_of's IN endpoint + owner links),
    # then keep + member_of (UNIQUE(in, out)).  Applied EXACTLY as production layers them.
    await _apply_ddl(connection, generate_principal_ddl())
    await _apply_ddl(connection, generate_keep_ddl())

    # Synthetic GOV — the Fork-E owner shape with SEPARATE indexes.  ``note`` is
    # deliberately unindexed: it anchors the TableScan positive controls.
    await _apply_ddl(
        connection,
        _ddl(
            [
                f"DEFINE TABLE {GOV} SCHEMAFULL",
                f"DEFINE FIELD owner_principal ON {GOV} TYPE record<{PRINCIPAL_TABLE}>",
                f"DEFINE FIELD owner_agent ON {GOV} TYPE record<{AGENT_TABLE}>",
                f"DEFINE FIELD scope ON {GOV} TYPE string",
                f"DEFINE FIELD note ON {GOV} TYPE string",
                f"DEFINE INDEX {GOV}_owner_principal ON {GOV} FIELDS owner_principal",
                f"DEFINE INDEX {GOV}_owner_agent ON {GOV} FIELDS owner_agent",
                f"DEFINE INDEX {GOV}_scope ON {GOV} FIELDS scope",
                # NOTE: no index on ``note`` — the deliberate TableScan anchor.
            ]
        ),
    )

    # Synthetic GOV_COMPOSITE — a SINGLE composite index over the three columns, to
    # probe store-law §2's leading-column-only rule (E2).
    await _apply_ddl(
        connection,
        _ddl(
            [
                f"DEFINE TABLE {GOV_COMPOSITE} SCHEMAFULL",
                f"DEFINE FIELD owner_principal ON {GOV_COMPOSITE} TYPE record<{PRINCIPAL_TABLE}>",
                f"DEFINE FIELD owner_agent ON {GOV_COMPOSITE} TYPE record<{AGENT_TABLE}>",
                f"DEFINE FIELD scope ON {GOV_COMPOSITE} TYPE string",
                f"DEFINE FIELD note ON {GOV_COMPOSITE} TYPE string",
                (
                    f"DEFINE INDEX {GOV_COMPOSITE}_composite ON {GOV_COMPOSITE} "
                    "FIELDS scope, owner_principal, owner_agent"
                ),
            ]
        ),
    )


# A spread of governed rows: 2 principals x 2 agents each, every scope value, keep
# rows in and out of a caller's keep set.  (principal, agent, scope, note)
_GOV_ROWS: list[tuple[str, str, str, str, str]] = [
    ("g1", "alice", "ag_a", "agent-private", "n1"),
    ("g2", "alice", "ag_b", "agent-private", "n2"),
    ("g3", "alice", "ag_a", "principal-private", "n3"),
    ("g4", "bob", "ag_b", "principal-private", "n4"),
    ("g5", "alice", "ag_a", "server", "n5"),
    ("g6", "bob", "ag_b", "server", "n6"),
    ("g7", "alice", "ag_a", "keep:k1", "n7"),
    ("g8", "bob", "ag_b", "keep:k2", "n8"),
    ("g9", "alice", "ag_b", "keep:k2", "n9"),
    ("g10", "bob", "ag_a", "agent-private", "n10"),
]


async def _seed_rows(connection: Any) -> None:
    """Seed both governed tables + the ``member_of`` edge (real endpoints, ENFORCED)."""
    for table in (GOV, GOV_COMPOSITE):
        for row_id, principal, agent, scope, note in _GOV_ROWS:
            await connection.query(
                f"CREATE type::record('{table}', $id) CONTENT {{ "
                f"owner_principal: type::record('{PRINCIPAL_TABLE}', $op), "
                f"owner_agent: type::record('{AGENT_TABLE}', $oa), "
                f"scope: $scope, note: $note }}",
                {"id": row_id, "op": principal, "oa": agent, "scope": scope, "note": note},
            )

    # member_of endpoints must EXIST (ENFORCED, store-ref §4).  Two principals, two
    # keeps (keeper = a real principal, the keep table's required record<principal>),
    # then RELATE principal --member_of--> keep with endpoints bound as RecordIDs.
    for principal in ("alice", "bob"):
        await connection.query(
            f"CREATE type::record('{PRINCIPAL_TABLE}', $id) CONTENT {{ email: $email }}",
            {"id": principal, "email": f"{principal}@example.test"},
        )
    for keep_id in ("k1", "k2"):
        await connection.query(
            f"CREATE type::record('{KEEP_TABLE}', $id) CONTENT {{ "
            f"keeper: type::record('{PRINCIPAL_TABLE}', $kid), type: 'project', name: $name }}",
            {"id": keep_id, "kid": "alice", "name": f"space-{keep_id}"},
        )
    for principal, keep_id in (("alice", "k1"), ("bob", "k2"), ("alice", "k2")):
        await connection.query(
            f"RELATE $from->{MEMBER_OF_RELATION}->$to",
            {"from": RecordID(PRINCIPAL_TABLE, principal), "to": RecordID(KEEP_TABLE, keep_id)},
        )


# Bound params reused across the READ-predicate probes.
_ALICE = RecordID(PRINCIPAL_TABLE, "alice")
_AGENT_A = RecordID(AGENT_TABLE, "ag_a")
_KEEP_SCOPES = ["keep:k1", "keep:k2"]

# The full Fork-C READ predicate, as the emitter would build it (bound params only).
_READ_PREDICATE = (
    "(scope = 'agent-private' AND owner_principal = $p AND owner_agent = $a) "
    "OR (scope = 'principal-private' AND owner_principal = $p) "
    "OR scope = 'server' "
    "OR scope IN $keeps"
)
_READ_PARAMS = {"p": _ALICE, "a": _AGENT_A, "keeps": _KEEP_SCOPES}


async def probe(connection: Any) -> ProbeReport:
    report = ProbeReport()

    print("\n=== INSTRUMENT INTEGRITY CONTROLS (must classify as stated) ===")
    control_index = await explain(
        report, connection, label="CONTROL scope= (indexed → IndexScan)",
        select="id", table=GOV, where="scope = $s", params={"s": "server"},
    )
    _require(report, control_index, "IndexScan",
             "the walker cannot SEE an IndexScan on an indexed equality — it is blind.")
    control_table = await explain(
        report, connection, label="CONTROL note= (unindexed → TableScan)",
        select="id", table=GOV, where="note = $n", params={"n": "n5"},
    )
    _require(report, control_table, "TableScan",
             "the walker cannot SEE a TableScan on an unindexed column — it is blind (store-ref §4).")
    control_or_table = await explain(
        report, connection, label="CONTROL note= OR note= (unindexed OR → TableScan)",
        select="id", table=GOV, where="note = $n1 OR note = $n2", params={"n1": "n5", "n2": "n6"},
    )
    _require(report, control_or_table, "TableScan",
             "the walker cannot SEE a TableScanned OR — the E3 OR verdict would be untrustworthy.")

    print("\n=== E1 — does `scope IN $set` use the scope index? (DISCOVERY) ===")
    await explain(
        report, connection, label="E1 scope IN $set",
        select="id", table=GOV, where="scope IN $keeps", params={"keeps": _KEEP_SCOPES},
        dump=True,
    )
    # Bonus: the empty-set case (an empty $my_keep_scopes is a real PDP input).
    await explain(
        report, connection, label="E1b scope IN [] (empty keep set)",
        select="id", table=GOV, where="scope IN $keeps", params={"keeps": []},
    )

    print("\n=== E2 — composite (scope, owner_principal, owner_agent): leading-column only? ===")
    composite_leading = await explain(
        report, connection, label="E2 composite leading (scope=)",
        select="id", table=GOV_COMPOSITE, where="scope = $s", params={"s": "server"},
    )
    _require(report, composite_leading, "IndexScan",
             "the composite index's LEADING column must IndexScan or the E2 probe is vacuous.")
    await explain(
        report, connection, label="E2 composite 2nd col alone (owner_principal=)",
        select="id", table=GOV_COMPOSITE, where="owner_principal = $p", params={"p": _ALICE},
        dump=True,
    )
    await explain(
        report, connection, label="E2 composite 3rd col alone (owner_agent=)",
        select="id", table=GOV_COMPOSITE, where="owner_agent = $a", params={"a": _AGENT_A},
    )
    await explain(
        report, connection, label="E2 composite leading+2nd (scope= AND owner_principal=)",
        select="id", table=GOV_COMPOSITE, where="scope = $s AND owner_principal = $p",
        params={"s": "principal-private", "p": _ALICE},
    )
    # And on GOV (SEPARATE indexes): owner_principal alone must IndexScan (its own index).
    await explain(
        report, connection, label="E2 separate owner_principal= (own index)",
        select="id", table=GOV, where="owner_principal = $p", params={"p": _ALICE},
    )

    print("\n=== E3 — THE OR-PLANNER: full 4-way READ predicate + each disjunct alone ===")
    # POSITIVE CONTROL — an index-served OR: a SAME-COLUMN OR (`scope = a OR scope = b`)
    # is expected to union index scans (the engine does this for `IN`).  Paired with the
    # note-OR TableScan control above, this proves the probe DISTINGUISHES an index-served
    # OR from a TableScanned one — so the "the full OR TableScans" verdict is trustworthy,
    # not an artefact of the walker always calling an OR a TableScan.
    same_column_or = await explain(
        report, connection, label="E3 control same-column OR (scope=a OR scope=b → index-served)",
        select="id", table=GOV, where="scope = 'server' OR scope = 'agent-private'",
    )
    _require(report, same_column_or, "IndexScan",
             "a same-column OR must be an index-served UnionIndexScan, else the probe "
             "cannot SEE an index-served OR and the E3 TableScan verdict is untrustworthy.")
    # The general trap, isolated: an OR across TWO DIFFERENT indexed columns.
    await explain(
        report, connection, label="E3 cross-column OR (scope= OR owner_principal=)",
        select="id", table=GOV, where="scope = 'server' OR owner_principal = $p",
        params={"p": _ALICE}, dump=True,
    )
    # BOUNDARY PROBES — pin down WHAT defeats the OR-planner, so the emitter author
    # knows whether a RESTRUCTURED flat OR could stay index-served vs. a genuine UNION
    # being required.  The full READ OR mixes simple equalities, an `IN`, and COMPOUND
    # (`scope=x AND owner=y`) disjuncts; these isolate each ingredient.
    await explain(
        report, connection, label="E3 bound-A OR of two AND-compounds (both owner_principal)",
        select="id", table=GOV,
        where="(scope = 'agent-private' AND owner_principal = $p) "
        "OR (scope = 'principal-private' AND owner_principal = $p)",
        params={"p": _ALICE}, dump=True,
    )
    await explain(
        report, connection, label="E3 bound-B eq OR IN, same column (scope= OR scope IN)",
        select="id", table=GOV, where="scope = 'server' OR scope IN $keeps",
        params={"keeps": _KEEP_SCOPES},
    )
    await explain(
        report, connection, label="E3 bound-C all-scope-only 4-way OR (no compound, no owner)",
        select="id", table=GOV,
        where="scope = 'agent-private' OR scope = 'principal-private' "
        "OR scope = 'server' OR scope IN $keeps",
        params={"keeps": _KEEP_SCOPES},
    )
    await explain(
        report, connection, label="E3 bound-D one compound OR one simple eq",
        select="id", table=GOV,
        where="(scope = 'agent-private' AND owner_principal = $p) OR scope = 'server'",
        params={"p": _ALICE}, dump=True,
    )
    # bound-E: bound-C's semantics with the `IN` EXPANDED to explicit equalities.  If
    # THIS IndexScans while bound-C (identical rows, but via `IN`) TableScans, it PROVES
    # the defeating ingredient is `IN`-inside-OR, and expanding the keep set to equality
    # disjuncts is the fix.
    await explain(
        report, connection, label="E3 bound-E all-scope-only OR, IN EXPANDED to equalities",
        select="id", table=GOV,
        where="scope = 'agent-private' OR scope = 'principal-private' "
        "OR scope = 'server' OR scope = 'keep:k1' OR scope = 'keep:k2'",
    )
    await explain(
        report, connection, label="E3 FULL 4-way OR (the READ predicate)",
        select="id", table=GOV, where=_READ_PREDICATE, params=_READ_PARAMS, dump=True,
    )
    # The decisive EMITTER probe: the FULL READ predicate with the keep-set `IN`
    # EXPANDED to per-keep equality disjuncts (bound params).  If IndexScan, the emitter
    # can stay a FLAT OR by expanding `scope IN $keeps` — no UNION-of-queries needed.
    await explain(
        report, connection, label="E3 FULL OR with IN expanded to equalities (EMITTER candidate)",
        select="id", table=GOV,
        where="(scope = 'agent-private' AND owner_principal = $p AND owner_agent = $a) "
        "OR (scope = 'principal-private' AND owner_principal = $p) "
        "OR scope = 'server' "
        "OR scope = $k1 OR scope = $k2",
        params={"p": _ALICE, "a": _AGENT_A, "k1": "keep:k1", "k2": "keep:k2"},
        dump=True,
    )
    await explain(
        report, connection, label="E3 disjunct1 (agent-private AND owner_principal= AND owner_agent=)",
        select="id", table=GOV,
        where="scope = 'agent-private' AND owner_principal = $p AND owner_agent = $a",
        params={"p": _ALICE, "a": _AGENT_A},
    )
    await explain(
        report, connection, label="E3 disjunct2 (principal-private AND owner_principal=)",
        select="id", table=GOV, where="scope = 'principal-private' AND owner_principal = $p",
        params={"p": _ALICE},
    )
    await explain(
        report, connection, label="E3 disjunct3 (scope='server')",
        select="id", table=GOV, where="scope = 'server'",
    )
    # disjunct4 == E1 (scope IN $keeps), already probed above.

    print("\n=== PROBE F — member_of leading (in=) vs trailing (out=) column ===")
    member_leading = await explain(
        report, connection, label="F leading in=$p (the resolver read)",
        select="out", table=MEMBER_OF_RELATION, where="in = $p", params={"p": _ALICE}, dump=True,
    )
    _require(report, member_leading, "IndexScan",
             "Fork F's resolver rests on the LEADING-column IndexScan of UNIQUE(in, out).")
    member_trailing = await explain(
        report, connection, label="F trailing out=$k (what list_household does)",
        select="in", table=MEMBER_OF_RELATION, where="out = $k",
        params={"k": RecordID(KEEP_TABLE, "k1")},
    )
    _require(report, member_trailing, "TableScan",
             "the trailing-column control must TableScan, proving leading-vs-trailing "
             "discrimination on THIS edge (store-law §2 composite leading-column).")

    return report


def _verdict(report: ProbeReport) -> None:
    """Derive and print the four settled facts + the emitter-shape verdict."""
    e1 = report.get("E1 scope IN $set").classification
    e1_empty = report.get("E1b scope IN [] (empty keep set)").classification
    composite_lead = report.get("E2 composite leading (scope=)").classification
    composite_2nd = report.get("E2 composite 2nd col alone (owner_principal=)").classification
    composite_3rd = report.get("E2 composite 3rd col alone (owner_agent=)").classification
    composite_lead_2 = report.get(
        "E2 composite leading+2nd (scope= AND owner_principal=)"
    ).classification
    gov_owner = report.get("E2 separate owner_principal= (own index)").classification
    same_col_or = report.get(
        "E3 control same-column OR (scope=a OR scope=b → index-served)"
    ).classification
    cross_col_or = report.get("E3 cross-column OR (scope= OR owner_principal=)").classification
    bound_a = report.get(
        "E3 bound-A OR of two AND-compounds (both owner_principal)"
    ).classification
    bound_b = report.get("E3 bound-B eq OR IN, same column (scope= OR scope IN)").classification
    bound_c = report.get(
        "E3 bound-C all-scope-only 4-way OR (no compound, no owner)"
    ).classification
    bound_d = report.get("E3 bound-D one compound OR one simple eq").classification
    bound_e = report.get(
        "E3 bound-E all-scope-only OR, IN EXPANDED to equalities"
    ).classification
    or_full = report.get("E3 FULL 4-way OR (the READ predicate)").classification
    or_expanded = report.get(
        "E3 FULL OR with IN expanded to equalities (EMITTER candidate)"
    ).classification
    d1 = report.get(
        "E3 disjunct1 (agent-private AND owner_principal= AND owner_agent=)"
    ).classification
    d2 = report.get("E3 disjunct2 (principal-private AND owner_principal=)").classification
    d3 = report.get("E3 disjunct3 (scope='server')").classification
    member_leading = report.get("F leading in=$p (the resolver read)").classification
    member_trailing = report.get("F trailing out=$k (what list_household does)").classification

    print("\n=== FOUR SETTLED FACTS (by construction — EXPLAIN pasted above) ===")
    print(f"  (1) `scope IN $set`                    : {e1}  (via UnionIndexScan)")
    print(f"      `scope IN []` (empty keep set)     : {e1_empty}  (zero-row short-circuit, no scan)")
    print(f"  (2) composite leading (scope=)         : {composite_lead}")
    print(f"      composite 2nd-col alone            : {composite_2nd}")
    print(f"      composite 3rd-col alone            : {composite_3rd}")
    print(f"      composite leading+2nd              : {composite_lead_2}")
    print(f"      GOV separate owner_principal index : {gov_owner}")
    print(f"  (3) same-column OR (scope=a OR scope=b): {same_col_or}  (control: index-served)")
    print(f"      cross-column OR (scope OR owner)   : {cross_col_or}")
    print(f"      bound-A: OR of two AND-compounds   : {bound_a}")
    print(f"      bound-B: eq OR IN (same column)    : {bound_b}")
    print(f"      bound-C: all-scope-only OR (w/ IN) : {bound_c}")
    print(f"      bound-D: one compound OR one eq    : {bound_d}")
    print(f"      bound-E: bound-C w/ IN EXPANDED    : {bound_e}  (isolates the `IN`-in-OR cause)")
    print(f"      FULL 4-way OR (READ, uses `IN`)    : {or_full}")
    print(f"      FULL OR, IN EXPANDED to equalities : {or_expanded}  (EMITTER candidate)")
    print(f"      each disjunct ALONE (d1/d2/d3)     : {d1} / {d2} / {d3}")
    print(f"  (4) member_of leading `in = $p`        : {member_leading}")
    print(f"      member_of trailing `out = $k`      : {member_trailing}  (control: latent seam)")

    print("\n=== EMITTER-SHAPE VERDICT ===")
    if or_full == "IndexScan":
        print("  The full flat OR (with `IN`) is INDEX-SERVED → the emitter MAY be a flat OR.")
    elif or_expanded == "IndexScan":
        print(
            f"  The full flat OR that uses `scope IN $keeps` is {or_full} — but the SAME "
            "predicate with the `IN` EXPANDED to per-keep equality disjuncts "
            f"(`scope = $k1 OR scope = $k2 ...`) is {or_expanded}.\n"
            "  => THE DEFEATING INGREDIENT IS `IN` INSIDE AN OR, not the OR itself and not "
            "the compound `AND` disjuncts (bound-A/D index-serve; bound-B/C with `IN` do "
            "not; bound-E expands the `IN` and index-serves).\n"
            "  => EMITTER: emit a FLAT OR, but EXPAND `scope IN $my_keep_scopes` into "
            "N per-keep `scope = $k_i` equality disjuncts (bound params, N = membership "
            "degree; OMIT the clause entirely when the keep set is empty). That keeps every "
            "disjunct an index-served equality and the whole predicate an index union — no "
            "UNION-of-queries needed. A flat OR that leaves `IN` in place is the #107 shape: "
            "green on a small/virgin test DB, a full TableScan on a large dirty store."
        )
    else:
        print(
            f"  The full flat OR is {or_full} AND expanding the `IN` did not rescue it "
            f"({or_expanded}) while each disjunct ALONE IndexScans → the emitter MUST be a "
            "UNION of per-clause IndexScans (or an accepted bounded TableScan), NOT a flat "
            "OR. A flat OR is the #107 shape (green on a virgin DB, TableScan on a dirty one)."
        )
    print(
        "\n  Minimal READ index set (from E2): SEPARATE indexes on `scope` AND "
        "`owner_principal` (a single composite is leading-column only — `owner_principal` "
        "alone TableScans, and the `principal-private` read filters owner_principal)."
    )


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    try:
        await _setup_schema(connection)
        await _seed_rows(connection)
        report = await probe(connection)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001 - cleanup best-effort, never masks the result
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    _verdict(report)

    print("\n=== SELF-CHECK VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All controls held, Fork-F assumptions held, every plan was classifiable.")
    print("The four facts above are established BY CONSTRUCTION.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
