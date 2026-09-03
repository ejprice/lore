#!/usr/bin/env python3
"""Probe: the packet-63a governed READ-filter is IndexScan-not-TableScan over the
REAL ``memory`` + ``message`` DDL, BY CONSTRUCTION.

WHY (packet 63 — the governed-tool retrofit; design
``docs/design/2026-08-28-packet63-retrofit-rulings.md`` §4). 63a splices the
packet-61 PDP READ predicate — ``authorize_filter(subject, Action.READ, table)``,
whose member branch is ``lorerunes.pdp._member_filter`` — onto EVERY governed
list-read as ``... AND ({fragment})`` (§1.2 ``read_filter``). Packet 61b
(``scripts/probe_read_filter_61b.py``) already proved that emitter's SHAPE
IndexScans on the live 3.2.4 engine — BUT it probed a **non-option ``scope
string`` on a BARE synthetic ``gov`` fixture table**. 63 changes two things the
plan is BELIEVED-not-known to survive (§4.4), each a #107-class hazard (green on a
small/virgin test DB, a TableScan on a large dirty store):

  * the governed columns are ``option<>`` (``scope option<string>``,
    ``owner_principal option<record<principal>>``), NOT the bare ``string`` /
    ``record<>`` of 61b's fixture — and there are NONE-scope legacy rows present;
  * the columns are spliced onto the REAL ``memory`` table (HNSW vector +
    BM25 FULLTEXT indexes CO-RESIDENT) and the REAL ``message`` table — not a
    bare table whose only indexes are the ones under test.

THE DISCOVERY (§4.4 P1 — the one genuinely unprobed delta): does a PLAIN index on
an ``option<string>`` ``scope`` column, over a table that also carries an HNSW +
FULLTEXT index, with NONE-scope rows present, still serve ``WHERE scope = $s`` as an
IndexScan? Store-ref §1.8 settles UNIQUE-over-``option<>`` (multiple NONE coexist)
but is SILENT on a plain index's PLAN over ``option<>`` + NONE rows. If P1 comes
back a TableScan, the §4.1 index ruling re-opens — the probe SAYS SO loudly and
exits non-zero.

METHOD (store-law discipline: §2 IndexScan-vs-TableScan-via-EXPLAIN + the C1
"a probe NEEDS a positive control" rule). Every scan claim is a live EXPLAIN plan
on the REAL 3.2.4 engine, classified by the SAME plan-walker the shipped packet-60
pin uses (``test_keeps_schema.py::TestTheKeeperIndexFires`` — ``operator ==
'IndexScan'`` / ``'TableScan'`` with ``attributes.table``). The walker + the
``explain``/``_require`` harness are MIRRORED from ``probe_read_filter_61b.py`` and
CITED, not forked into shared code: this is instrument parsing, not production
policy — the same stance 61b took re-expressing ``test_keeps_schema``'s walker
(ROUTING-IS-NOT-SHARING does not demand two throwaway probe scripts share a walker).

The DDL under test is applied through the REAL top-level generators
(``generate_memory_ddl`` / ``generate_message_ddl`` / ``generate_keep_ddl`` — the
EXACT slices ``LocalMemoryBackend.ensure_ready`` / ``MessageLedger.ensure_ready``
apply, each inside one ``BEGIN … COMMIT`` via ``execute_transaction``), then the
§4.1 governed overlay is applied ON TOP by the REAL shipped emitter
(``_governed_field_specs`` / ``_governed_index_statements`` — design §1.2 item 4, the
SAME one ``_memory_statements`` wires in; when this probe was FIRST written that
emitter did not exist and the overlay transcribed §4.1 verbatim — 63a is now CLOSED,
so the probe applies the emitter directly). On ``message`` this overlay is the
LOAD-BEARING step (63b's ``_message_statements`` governed wiring is not yet built, so
the probe applies the emitter directly and the proof is INDEPENDENT of that wiring);
on ``memory`` it is a redundant-but-idempotent re-apply (``generate_memory_ddl``
already bakes the emitter in at 63a). The READ predicate under test is produced by the REAL
emitter (``authorize_filter(subject, Action.READ, table).to_surql()`` — for a
member this IS ``_member_filter``, ``pdp.py:432``), never a hand-typed WHERE (§4.2).

WHAT EACH PROBE EXPECTS (§4.4 table P1–P6 + C+ controls):
  * P1  memory ``scope = $s`` (option<> + NONE rows, HNSW/FULLTEXT co-resident)
        -> REQUIRE IndexScan (``memory_scope``).  THE DISCOVERY.
  * P2  memory FULL emitter READ fragment (member, 2 keeps)
        -> REQUIRE IndexScan, NO TableScan of ``memory`` (#413 fact-3 on the real table).
  * P3  message FULL emitter READ fragment over legacy(NONE)+migrated rows
        -> REQUIRE IndexScan, NO TableScan of ``message``.
  * P4  message ``id IN $ids AND (fragment)`` (the §4.3 step-2 inbox read)
        -> REPORT the plan; a TableScan of ``message`` names the per-id
           ``type::record`` fallback (NOT an exit failure — it is a fallback trigger).
  * P5  ``scope IS NONE`` (the §2.3 boot count) on both tables
        -> REPORTED as a TableScan (expected; so nobody reads the boot count as index-served).
  * P6  keep ``key = $k`` after SF-63-4's UNIQUE index, >=2 NONE-key keeps present
        -> REQUIRE IndexScan (``keep_key``); the two NONE-key rows COEXIST (§1.8).
  * C+  un-indexed equality -> TableScan; ``owner_agent = $a`` alone -> TableScan
        (proves the walker CAN see a TableScan AND documents the un-indexed
        ``owner_agent`` bound of §4.1).

WHAT MAKES IT FAIL LOUD (exit non-zero):
  * any instrument-integrity / C+ control mis-classifies (a walker that cannot see a
    TableScan is blind — worthless);
  * any expected-IndexScan probe (P1/P2/P3/P6) comes back anything but IndexScan
    (P1's TableScan re-opens the §4.1 ruling — flagged as such);
  * the two NONE-key keeps do NOT coexist (§1.8 would be false on THIS column);
  * any REQUIRED plan is UNCLASSIFIED (we never guess an IndexScan — the C1 rule).
P4 and P5 are REPORT-only discoveries: their plans are printed and dumped, never
guessed, and a P4 TableScan prints the fallback rather than failing.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000`` —
creds root/spikeroot, matching ``loremaster/tests/_surreal_harness.py`` and 61b),
and drops it on exit. It NEVER touches production (lore-surreal :18500). Referenced
principal/agent records are NOT created — ``owner_*`` and ``sender`` are plain
``record<>`` links (store-ref §2/§4: a record-link equality needs no live target,
and the EXPLAIN plan is chosen structurally, before any row is read), so the plan
under test is faithful without the referential scaffolding.

Run: ``uv run python scripts/probe_read_filter_63.py``
Exit 0 iff every control + expected-IndexScan held, the NONE keys coexisted, and
every required plan was classifiable; non-zero on any surprise.
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
    KEEP_TABLE,
    MEMORY_TABLE,
    MESSAGE_TABLE,
    _define_field,
    _governed_field_specs,
    _governed_index_statements,
    generate_agent_ddl,
    generate_keep_ddl,
    generate_memory_ddl,
    generate_message_ddl,
    generate_principal_ddl,
)
from lorerunes.pdp import (
    AGENT_TABLE,
    PRINCIPAL_ROLE_MEMBER,
    PRINCIPAL_TABLE,
    Action,
    Subject,
    authorize_filter,
)
from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

# TEST store topology — the spike defaults from ``_surreal_harness.py``. NEVER :18500.
URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

# The embedding width for the ``memory`` HNSW index — any positive width co-resides
# the HNSW/FULLTEXT with the governed ``scope`` index identically (the DISCOVERY is
# co-residence, not dimensionality). 8 keeps seed vectors tiny.
DIM = 8
_EMB = [round(0.11 * (i + 1), 3) for i in range(DIM)]  # a fixed non-zero DIM-vector


def unique_database() -> str:
    """``test_<pid>_<uuid4>`` — the harness pattern, so a parallel run never collides."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


# --------------------------------------------------------------------------- #
# EXPLAIN plan classification — MIRRORED from ``probe_read_filter_61b.py`` (itself
# re-expressing ``test_keeps_schema.py::TestTheKeeperIndexFires``), CITED not forked:
# instrument parsing, not production policy.
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
    classification: str  # IndexScan | TableScan | MIXED(index+table) | EmptyScan | UNCLASSIFIED
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

    Priority: a ``TableScan`` of the target with no ``IndexScan`` is a whole-table
    scan (the hazard); both present is ``MIXED`` (a scan still happens); an
    ``IndexScan`` with no target TableScan is ``IndexScan`` (covers ``IN`` served as
    a ``UnionIndexScan`` of ``IndexScan`` children, and same-column ``OR``);
    ``EmptyScan`` proves zero rows and reads nothing; anything else is
    ``UNCLASSIFIED`` — a plan shape this instrument cannot read, so no honest verdict
    is possible (we never guess an IndexScan).
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
    table: str,
    where: str,
    select: str = "id",
    params: dict[str, Any] | None = None,
    dump: bool = False,
    report_only: bool = False,
) -> ScanObservation:
    """Run ``SELECT <select> FROM <table> WHERE <where> EXPLAIN`` and classify the plan.

    ``report_only`` (P4/P5): an UNCLASSIFIED or TableScan plan is PRINTED, never
    auto-surfaced as a surprise — those probes report the plan, they do not require
    an IndexScan. For every other probe an UNCLASSIFIED plan IS a surprise (a verdict
    over an unreadable plan would be a guess).
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
    if classification == "UNCLASSIFIED" and not report_only:
        report.surprises.append(
            f"{label}: plan is UNCLASSIFIED (no IndexScan operator, no TableScan of "
            f"{table!r}) — unreadable, so no honest verdict is possible. "
            f"operators={operators} :: {statement}"
        )
    return observation


def _require(report: ProbeReport, observation: ScanObservation, want: str, why: str) -> None:
    """A load-bearing expectation: the observation's classification MUST equal ``want``."""
    if observation.classification != want:
        report.surprises.append(
            f"{observation.label}: EXPECTED {want}, got {observation.classification}. {why} "
            f"operators={observation.operators} :: {observation.statement}"
        )


async def _apply_ddl(connection: Any, ddl: str) -> None:
    """Apply ``ddl`` through the production ``execute_transaction`` seam (store-ref §3).

    Mirrors ``LocalMemoryBackend.ensure_ready`` / ``MessageLedger.ensure_ready``:
    one ``BEGIN … COMMIT``, every statement's status checked — NOT the lax
    ``.query()`` that inspects only statement[0] and would report a green migration
    over a schema the engine had silently discarded.
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


def _governed_overlay(table: str) -> str:
    """The §4.1 governed columns + indexes for ``table``, emitted by the REAL
    production seam — ``_governed_field_specs`` (the three ``option<>`` columns) via
    ``_define_field`` (OVERWRITE) + ``_governed_index_statements`` (the two plain
    indexes) — the SAME emitter ``_memory_statements`` wires in (design §1.2 item 4).

    When this probe was first written the emitter did not exist and this overlay
    transcribed §4.1 verbatim; 63a is now CLOSED, so the probe applies the SHIPPED
    emitter directly — the message index-service proof rests on production code, not a
    copy of it (ROUTING-IS-NOT-SHARING / no reference-pattern-to-clone). Applied to
    ``MESSAGE_TABLE`` it is INDEPENDENT of the not-yet-built 63b ``_message_statements``
    governed wiring: the exact columns/indexes 63b will bake in are proven
    index-serving here, by the emitter, before that wiring lands. (On ``MEMORY_TABLE``
    the overlay is now REDUNDANT — ``generate_memory_ddl`` already bakes the same
    emitter in at 63a — but idempotent: OVERWRITE fields re-write an identical def and
    ``IF NOT EXISTS`` indexes no-op.)

    The emitter carries ``option<>`` fields (store-ref §1.4 — a required field poisons
    every legacy row), ``OVERWRITE`` for fields (§1.1 — the only clause that lands a
    changed def), and PLAIN ``IF NOT EXISTS`` indexes on ``scope`` AND
    ``owner_principal`` only (§1.1/§1.5); ``owner_agent`` is deliberately NOT indexed
    at 63 (§4.1 named-trigger bound — its C+ control below documents it).
    """
    statements = [
        _define_field(table, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _governed_field_specs()
    ]
    statements += _governed_index_statements(table)
    return _ddl(statements)


def _keep_key_overlay() -> str:
    """SF-63-4: ``keep.key option<string>`` + a UNIQUE ``IF NOT EXISTS`` index
    (§4.1 keep block). ``option<>`` + UNIQUE => multiple NONE coexist (§1.8)."""
    return _ddl(
        [
            f"DEFINE FIELD OVERWRITE key ON {KEEP_TABLE} TYPE option<string>",
            f"DEFINE INDEX IF NOT EXISTS {KEEP_TABLE}_key ON {KEEP_TABLE} FIELDS key UNIQUE",
        ]
    )


async def _setup_schema(connection: Any) -> None:
    """Apply the REAL production DDL slices in production order, then the §4.1 overlays.

    Order mirrors production: ``principal`` (keep.keeper target), ``agent``
    (message.sender / ``to``-edge target), ``keep``, ``memory`` (HNSW + FULLTEXT),
    ``message`` (+ ``to`` edge + ``message_seq``), then the governed overlay on
    ``memory`` and ``message``, then the SF-63-4 ``keep.key`` overlay.
    """
    await _apply_ddl(connection, generate_principal_ddl())
    await _apply_ddl(connection, generate_agent_ddl())
    await _apply_ddl(connection, generate_keep_ddl())
    await _apply_ddl(connection, generate_memory_ddl(dim=DIM))
    await _apply_ddl(connection, generate_message_ddl())
    await _apply_ddl(connection, _governed_overlay(MEMORY_TABLE))
    message_overlay = _governed_overlay(MESSAGE_TABLE)
    print(
        "\n=== §4.1 GOVERNED OVERLAY on message (REAL emitter, applied ON TOP of "
        "generate_message_ddl) ==="
    )
    print("   " + message_overlay.rstrip().replace("\n", "\n   "))
    await _apply_ddl(connection, message_overlay)
    await _apply_ddl(connection, _keep_key_overlay())


# --------------------------------------------------------------------------- #
# Seeding — memory / message rows spanning every READ disjunct + a NONE-scope legacy
# row; keep rows for the SF-63-4 key probe. Referenced principal/agent records are
# NOT created (plain record<> links; the plan is structural).
# --------------------------------------------------------------------------- #


async def _create_memory(
    connection: Any,
    row_id: str,
    *,
    scope: str | None = None,
    owner_principal: str | None = None,
    owner_agent: str | None = None,
) -> None:
    fields = [
        "note_text: $nt",
        "kind: $k",
        "source: { kind: 'probe' }",
        "importance: 0.5",
        "valid_from: time::now()",
        "created_at: time::now()",
        "embedding: $emb",
    ]
    params: dict[str, Any] = {"id": row_id, "nt": f"note {row_id}", "k": "gotcha", "emb": _EMB}
    if scope is not None:
        # ``$scope``/``$session`` are PROTECTED param names (store-ref §2) — the COLUMN
        # key ``scope`` is fine, but the BOUND param must be spelled safely (``$sc``).
        fields.append("scope: $sc")
        params["sc"] = scope
    if owner_principal is not None:
        fields.append(f"owner_principal: type::record('{PRINCIPAL_TABLE}', $op)")
        params["op"] = owner_principal
    if owner_agent is not None:
        fields.append(f"owner_agent: type::record('{AGENT_TABLE}', $oa)")
        params["oa"] = owner_agent
    await connection.query(
        f"CREATE type::record('{MEMORY_TABLE}', $id) CONTENT {{ {', '.join(fields)} }}", params
    )


async def _create_message(
    connection: Any,
    row_id: str,
    *,
    seq: int,
    sender: str,
    scope: str | None = None,
    owner_principal: str | None = None,
    owner_agent: str | None = None,
) -> None:
    fields = [
        "seq: $seq",
        # ``session`` is a PROTECTED param name (store-ref §2) — column key is fine,
        # bound param must be spelled safely (``$sess``).
        "session: $sess",
        "thread: $thread",
        f"sender: type::record('{AGENT_TABLE}', $sender)",
        "grade: 'signal'",
        "body: $body",
        "created_at: time::now()",
    ]
    params: dict[str, Any] = {
        "id": row_id,
        "seq": seq,
        "sess": "sess1",
        "thread": "t1",
        "sender": sender,
        "body": f"body {row_id}",
    }
    if scope is not None:
        fields.append("scope: $sc")
        params["sc"] = scope
    if owner_principal is not None:
        fields.append(f"owner_principal: type::record('{PRINCIPAL_TABLE}', $op)")
        params["op"] = owner_principal
    if owner_agent is not None:
        fields.append(f"owner_agent: type::record('{AGENT_TABLE}', $oa)")
        params["oa"] = owner_agent
    await connection.query(
        f"CREATE type::record('{MESSAGE_TABLE}', $id) CONTENT {{ {', '.join(fields)} }}", params
    )


async def _create_keep(
    connection: Any, row_id: str, *, name: str, key: str | None = None
) -> None:
    fields = [
        f"keeper: type::record('{PRINCIPAL_TABLE}', $keeper)",
        "type: 'project'",
        "name: $name",
    ]
    params: dict[str, Any] = {"id": row_id, "keeper": "alice", "name": name}
    if key is not None:
        fields.append("key: $key")
        params["key"] = key
    await connection.query(
        f"CREATE type::record('{KEEP_TABLE}', $id) CONTENT {{ {', '.join(fields)} }}", params
    )


async def _seed_rows(connection: Any) -> None:
    # memory: one row per READ disjunct + an out-of-view keep row + a NONE-scope
    # legacy row (owner-less, scope-less — the >=1 required legacy row of §4.4 P1).
    await _create_memory(
        connection, "m_ap", scope="agent-private", owner_principal="alice", owner_agent="ag_a"
    )
    await _create_memory(
        connection, "m_pp", scope="principal-private", owner_principal="alice", owner_agent="ag_b"
    )
    await _create_memory(connection, "m_srv", scope="server", owner_principal="bob", owner_agent="ag_b")
    await _create_memory(connection, "m_k1", scope="keep:k1", owner_principal="alice", owner_agent="ag_a")
    await _create_memory(connection, "m_k2", scope="keep:k2", owner_principal="bob", owner_agent="ag_b")
    await _create_memory(connection, "m_other", scope="keep:k9", owner_principal="carol", owner_agent="ag_c")
    await _create_memory(connection, "m_legacy")  # NONE scope + NONE owner — the legacy row

    # message: migrated rows spanning the disjuncts + a legacy row (real sender link,
    # NONE governed columns) — §4.4 P3's "legacy(NONE)+migrated".
    await _create_message(
        connection, "x_ap", seq=1, sender="ag_a",
        scope="agent-private", owner_principal="alice", owner_agent="ag_a",
    )
    await _create_message(
        connection, "x_pp", seq=2, sender="ag_a",
        scope="principal-private", owner_principal="alice", owner_agent="ag_b",
    )
    await _create_message(
        connection, "x_srv", seq=3, sender="ag_b",
        scope="server", owner_principal="bob", owner_agent="ag_b",
    )
    await _create_message(
        connection, "x_k1", seq=4, sender="ag_a",
        scope="keep:k1", owner_principal="alice", owner_agent="ag_a",
    )
    await _create_message(
        connection, "x_other", seq=5, sender="ag_c",
        scope="keep:k9", owner_principal="carol", owner_agent="ag_c",
    )
    await _create_message(connection, "x_legacy", seq=6, sender="ag_legacy")  # NONE governed cols

    # keep: one keyed project keep + TWO NONE-key manual keeps (must COEXIST, §1.8).
    await _create_keep(connection, "k_proj", name="lore-project", key="project:lore")
    await _create_keep(connection, "k_none1", name="manual-a")
    await _create_keep(connection, "k_none2", name="manual-b")


# The member Subject whose REAL emitter output P2/P3/P4 splice (a member with 2 keeps).
_SUBJECT = Subject(
    principal_id="alice",
    agent_id="ag_a",
    role=PRINCIPAL_ROLE_MEMBER,
    visible_keep_ids=frozenset({"keep:k1", "keep:k2"}),
)


def _read_fragment(table: str) -> tuple[str, dict[str, str]]:
    """The REAL production READ predicate: ``authorize_filter(subject, READ, table)``
    — for a member this delegates to ``_member_filter`` (``pdp.py:432``). Returns the
    ``(fragment, params)`` ``read_filter`` (§1.2) would splice as ``AND ({fragment})``."""
    return authorize_filter(_SUBJECT, Action.READ, table).to_surql()


async def probe(connection: Any) -> ProbeReport:
    report = ProbeReport()

    mem_fragment, mem_params = _read_fragment(MEMORY_TABLE)
    msg_fragment, msg_params = _read_fragment(MESSAGE_TABLE)
    print("\n=== REAL EMITTER OUTPUT (authorize_filter member READ) ===")
    print(f"  memory fragment : {mem_fragment}")
    print(f"  memory params   : {mem_params}")
    print(f"  message fragment: {msg_fragment}")
    print(f"  message params  : {msg_params}")

    print("\n=== INSTRUMENT-INTEGRITY + C+ CONTROLS (must classify as stated) ===")
    # Walker CAN see an IndexScan (indexed equality), on BOTH real tables.
    ctrl_mem_op = await explain(
        report, connection, label="CTRL memory owner_principal= (indexed → IndexScan)",
        table=MEMORY_TABLE, where=f"owner_principal = type::record('{PRINCIPAL_TABLE}', $p)",
        params={"p": "alice"},
    )
    _require(report, ctrl_mem_op, "IndexScan",
             "the memory_owner_principal index must IndexScan or the walker is blind.")
    ctrl_msg_scope = await explain(
        report, connection, label="CTRL message scope= (indexed → IndexScan)",
        table=MESSAGE_TABLE, where="scope = $s", params={"s": "server"},
    )
    _require(report, ctrl_msg_scope, "IndexScan",
             "message_scope must IndexScan or the walker is blind on message.")
    # Walker CAN see a TableScan (unindexed equality), on BOTH real tables.
    ctrl_mem_kind = await explain(
        report, connection, label="CTRL memory kind= (unindexed → TableScan)",
        table=MEMORY_TABLE, where="kind = $k", params={"k": "gotcha"},
    )
    _require(report, ctrl_mem_kind, "TableScan",
             "the walker cannot SEE a TableScan on an unindexed memory column — blind (store-ref §4).")
    ctrl_msg_body = await explain(
        report, connection, label="CTRL message body= (unindexed → TableScan)",
        table=MESSAGE_TABLE, where="body = $b", params={"b": "body x_srv"},
    )
    _require(report, ctrl_msg_body, "TableScan",
             "the walker cannot SEE a TableScan on an unindexed message column — blind.")
    # C+ — owner_agent is NOT indexed at 63 (§4.1). It MUST TableScan on both tables:
    # this is both a walker-sees-TableScan control AND documents the un-indexed bound.
    cplus_mem_oa = await explain(
        report, connection, label="C+ memory owner_agent= alone (un-indexed at 63 → TableScan)",
        table=MEMORY_TABLE, where=f"owner_agent = type::record('{AGENT_TABLE}', $a)",
        params={"a": "ag_a"},
    )
    _require(report, cplus_mem_oa, "TableScan",
             "§4.1: owner_agent is deliberately NOT indexed at 63 — its equality must TableScan.")
    cplus_msg_oa = await explain(
        report, connection, label="C+ message owner_agent= alone (un-indexed at 63 → TableScan)",
        table=MESSAGE_TABLE, where=f"owner_agent = type::record('{AGENT_TABLE}', $a)",
        params={"a": "ag_a"},
    )
    _require(report, cplus_msg_oa, "TableScan",
             "§4.1: owner_agent is deliberately NOT indexed at 63 — its equality must TableScan.")

    print("\n=== P1 — THE DISCOVERY: memory scope= over option<> + NONE rows (HNSW/FT co-resident) ===")
    p1 = await explain(
        report, connection, label="P1 memory scope= (option<> scope index, NONE rows present)",
        table=MEMORY_TABLE, where="scope = $s", params={"s": "server"}, dump=True,
    )
    _require(report, p1, "IndexScan",
             "DISCOVERY FAILED — a plain index on option<string> scope (NONE rows present, "
             "HNSW/FULLTEXT co-resident) did NOT serve equality. This RE-OPENS the §4.1 index "
             "ruling (route to the design sidecar).")

    print("\n=== P2 — memory FULL emitter READ fragment (no memory TableScan) ===")
    p2 = await explain(
        report, connection, label="P2 memory FULL READ fragment (real emitter, member 2 keeps)",
        table=MEMORY_TABLE, where=mem_fragment, params=mem_params, dump=True,
    )
    _require(report, p2, "IndexScan",
             "#413 fact-3 on the REAL memory table: the emitted flat OR (keeps EXPANDED, not IN) "
             "must UnionIndexScan with NO TableScan of memory.")

    print("\n=== P3 — message FULL emitter READ fragment over legacy(NONE)+migrated rows ===")
    p3 = await explain(
        report, connection, label="P3 message FULL READ fragment (real emitter, member 2 keeps)",
        table=MESSAGE_TABLE, where=msg_fragment, params=msg_params, dump=True,
    )
    _require(report, p3, "IndexScan",
             "same verdict as P2 on the REAL message table (legacy NONE + migrated rows present).")

    print("\n=== P4 — §4.3 step-2 inbox read: message `id IN $ids AND (fragment)` (REPORT + LEAK GATE) ===")
    # $ids deliberately mixes an id the fragment ADMITS (x_ap: agent-private/alice/ag_a)
    # with one it EXCLUDES (x_other: scope=keep:k9, not in the subject's keeps). Under the
    # CORRECT `id IN $ids AND (fragment)` precedence the result is EXACTLY {x_ap}. The
    # EXPLAIN renders the predicate with parens FLATTENED (`id IN [...] AND A OR B OR ...`),
    # which — if the engine EVALUATED that flattened form (AND binds tighter than OR) —
    # would apply the id filter to only the FIRST disjunct and LEAK principal-private/
    # server/keep rows OUTSIDE the id set (#416, one level out). The leak gate below reads
    # the ACTUAL rows to prove the sent parens hold, not the lossy EXPLAIN pretty-print.
    inbox_ids = [RecordID(MESSAGE_TABLE, "x_ap"), RecordID(MESSAGE_TABLE, "x_other")]
    p4 = await explain(
        report, connection, label="P4 message id IN $ids AND (READ fragment)",
        table=MESSAGE_TABLE, where=f"id IN $ids AND ({msg_fragment})",
        params={"ids": inbox_ids, **msg_params}, dump=True, report_only=True,
    )
    leak_rows = await connection.query(
        f"SELECT id FROM {MESSAGE_TABLE} WHERE id IN $ids AND ({msg_fragment})",
        {"ids": inbox_ids, **msg_params},
    )
    returned_ids = sorted(_row_ids(leak_rows))
    print(f"  LEAK GATE — id IN [x_ap(admitted), x_other(excluded)] AND (fragment) returned: {returned_ids}")
    if returned_ids != ["message:x_ap"]:
        report.surprises.append(
            "P4 LEAK GATE FAILED — `id IN $ids AND (fragment)` returned "
            f"{returned_ids}, expected exactly ['message:x_ap']. The fragment's outer parens "
            "ESCAPED (the OR is not bounded by the id filter), so the §4.3 step-2 drain would "
            "serve messages OUTSIDE the recipient id set — a cross-principal LEAK. RE-OPENS §4.3: "
            "the two-step shape needs per-id `type::record` reads, not `id IN $ids` + the OR fragment."
        )

    print("\n=== P5 — `scope IS NONE` (the §2.3 boot count) — REPORTED (design expected TableScan) ===")
    p5_mem = await explain(
        report, connection, label="P5 memory scope IS NONE (boot count)",
        select="count()", table=MEMORY_TABLE, where="scope IS NONE", report_only=True, dump=True,
    )
    p5_msg = await explain(
        report, connection, label="P5 message scope IS NONE (boot count)",
        select="count()", table=MESSAGE_TABLE, where="scope IS NONE", report_only=True, dump=True,
    )

    print("\n=== P6 — keep `key = $k` after SF-63-4 UNIQUE index; >=2 NONE-key keeps COEXIST ===")
    none_key_count = await connection.query(
        f"SELECT count() AS n FROM {KEEP_TABLE} WHERE key IS NONE GROUP ALL"
    )
    coexisting = _scalar(none_key_count, "n")
    print(f"  NONE-key keeps present (must be >= 2, §1.8 coexistence): {coexisting}")
    if not isinstance(coexisting, int) or coexisting < 2:
        report.surprises.append(
            f"P6 COEXISTENCE FAILED — expected >=2 NONE-key keeps to coexist under UNIQUE(key) "
            f"(store-ref §1.8), found {coexisting!r}. The two manual keeps did NOT both persist."
        )
    p6 = await explain(
        report, connection, label="P6 keep key= (after keep_key UNIQUE index)",
        table=KEEP_TABLE, where="key = $k", params={"k": "project:lore"}, dump=True,
    )
    _require(report, p6, "IndexScan",
             "SF-63-4: the keep_key UNIQUE index over option<string> must serve `key = $k` as "
             "an IndexScan (the write path resolves the project keep by ONE indexed read, §2.2).")

    # keep the P4/P5 handles used by the verdict (silence unused-var linters)
    _ = (p4, p5_mem, p5_msg)
    return report


def _scalar(result: Any, key: str) -> Any:
    """Pull ``key`` from the first row of a SurrealDB ``SELECT ... GROUP ALL`` result."""
    rows = result
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0].get(key)
    return None


def _row_ids(result: Any) -> list[str]:
    """The stringified ``id`` of every row in a plain ``SELECT id`` result."""
    if not isinstance(result, list):
        return []
    return [str(row["id"]) for row in result if isinstance(row, dict) and "id" in row]


def _verdict(report: ProbeReport) -> None:
    """Print the §4.4 P1–P6 + C+ settled table with a PASS/verdict per row."""
    def cls(label: str) -> str:
        try:
            return report.get(label).classification
        except KeyError:
            return "MISSING"

    print("\n=== §4.4 PROBE TABLE — verdicts (EXPLAINs pasted above) ===")
    rows = [
        ("P1", "memory scope= (option<> + NONE rows, HNSW/FULLTEXT co-resident)",
         "P1 memory scope= (option<> scope index, NONE rows present)", "IndexScan"),
        ("P2", "memory FULL emitter READ fragment",
         "P2 memory FULL READ fragment (real emitter, member 2 keeps)", "IndexScan"),
        ("P3", "message FULL emitter READ fragment (legacy+migrated)",
         "P3 message FULL READ fragment (real emitter, member 2 keeps)", "IndexScan"),
        ("P4", "message id IN $ids AND (fragment) [REPORT+leak gate]",
         "P4 message id IN $ids AND (READ fragment)", "(report)"),
        ("P5m", "memory scope IS NONE [REPORT]",
         "P5 memory scope IS NONE (boot count)", "(report)"),
        ("P5x", "message scope IS NONE [REPORT]",
         "P5 message scope IS NONE (boot count)", "(report)"),
        ("P6", "keep key= after SF-63-4 UNIQUE",
         "P6 keep key= (after keep_key UNIQUE index)", "IndexScan"),
        ("C+m", "memory owner_agent= alone [expect TableScan]",
         "C+ memory owner_agent= alone (un-indexed at 63 → TableScan)", "TableScan"),
        ("C+x", "message owner_agent= alone [expect TableScan]",
         "C+ message owner_agent= alone (un-indexed at 63 → TableScan)", "TableScan"),
    ]
    for tag, desc, label, expected in rows:
        got = cls(label)
        if expected in ("(report)",):
            verdict = "REPORT"
        elif got == expected:
            verdict = "PASS"
        else:
            verdict = f"FAIL (wanted {expected})"
        print(f"  {tag:<4} {got:<18} {verdict:<22} {desc}")

    p1 = cls("P1 memory scope= (option<> scope index, NONE rows present)")
    print("\n=== P1 DISCOVERY VERDICT (the one genuinely unprobed delta, §4.4) ===")
    if p1 == "IndexScan":
        print(
            "  ✅ A PLAIN index on an option<string> `scope` column — with NONE rows present and\n"
            "     the memory HNSW + BM25 FULLTEXT indexes CO-RESIDENT — SERVES `scope = $s` as an\n"
            "     IndexScan. The §4.1 index ruling HOLDS: `memory_scope` / `message_scope` are\n"
            "     sound over option<> + NONE rows. (61b's non-option `scope string` on a bare\n"
            "     table generalises to the real option<> columns on the real tables.)"
        )
    else:
        print(
            f"  🚨 DISCOVERY MISS: `scope = $s` over option<string> came back {p1}, NOT IndexScan.\n"
            "     This RE-OPENS the §4.1 index ruling — a plain index on option<> scope does not\n"
            "     serve equality with NONE rows / HNSW-FULLTEXT co-resident. ROUTE TO THE DESIGN\n"
            "     SIDECAR: the governed read filter would TableScan on a dirty store (#107 shape)."
        )

    p4 = cls("P4 message id IN $ids AND (READ fragment)")
    print("\n=== P4 INBOX-READ VERDICT (§4.3 step-2) ===")
    if p4 == "TableScan":
        print(
            "  ⚠ `id IN $ids AND (fragment)` TableScans `message`. The §4.3 fallback applies:\n"
            "     read per-id via `type::record` (SELECT ... FROM type::record('message', $id) ...)\n"
            "     bounded by the recipient-edge id set, rather than `id IN $ids` + OR."
        )
    else:
        print(
            f"  `id IN $ids AND (fragment)` planned as {p4} (no message TableScan) — the §4.3\n"
            "     two-step drain is index-served AND (LEAK GATE above) correctly scoped: the sent\n"
            "     parens hold, so the id filter bounds the whole OR. No per-id fallback needed."
        )

    p5m = cls("P5 memory scope IS NONE (boot count)")
    p5x = cls("P5 message scope IS NONE (boot count)")
    print("\n=== P5 BOOT-COUNT VERDICT (`scope IS NONE`, §2.3) ===")
    if p5m == "IndexScan" and p5x == "IndexScan":
        print(
            "  `scope IS NONE` is served as an IndexScan (`= NONE` on the `scope` index) on BOTH\n"
            "  tables — exactly as design §2.3/§4.4 records. (The design doc's earlier `TableScan`\n"
            "  expectation was already CORRECTED to IndexScan on 2026-08-28, citing this probe —\n"
            "  a P8d prose-currency fix; there is nothing left to correct here.) The boot count is\n"
            "  index-served (cheaper than a bounded TableScan), run ONCE per boot; it does NOT\n"
            "  re-open the §4.1 index ruling (the read filter is unaffected)."
        )
    else:
        print(
            f"  ⚠ P5 UNEXPECTED (investigate): design §2.3/§4.4 records `scope IS NONE` as an\n"
            f"     IndexScan (`= NONE` on the `scope` index, corrected 2026-08-28); on THIS run it\n"
            f"     is {p5m} (memory) / {p5x} (message). The read filter is unaffected either way\n"
            f"     (§4.1), but the boot-count plan no longer matches the recorded expectation."
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
    print("All controls held; P1–P3 + P6 IndexScanned; NONE keys coexisted; every required")
    print("plan was classifiable. The §4.4 probe table's verdicts are established BY CONSTRUCTION.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
