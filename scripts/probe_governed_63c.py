#!/usr/bin/env python3
# ⚠ SDK-3 BOUND (packet 66, operator ruling R19 Q5) — NOT PORTED, NOT RE-RUN on surrealdb 3.0.0.
# Written and last run against surrealdb 2.0.0. No cron or timer runs it (the R19 Q5 finding), so it was
# left unported; its results describe the SDK and engine it ran on. SDK 3.0.0 differences a re-run meets:
#   * ``query()`` answers ONE ENTRY PER STATEMENT (2.0 answered the first statement's bare result) — select a
#     single statement's result with ``loremaster.store._txn.one_statement_result``;
#   * a connection built with ``AsyncSurreal(url)`` bypasses lore's shared policy (reconnect-forever, finite
#     request timeout, streaming) — build it with ``loremaster.store._txn.open_surreal_connection``;
#   * ``str(RecordID)`` brackets a digit-led or non-word key (``keep:⟨01J…⟩``) — compare record ids by their
#     parts (``loremaster.store._txn.record_key`` / ``record_text``), never by that text;
#   * a dropped request raises ``ConnectionUnavailableError`` (2.0 raised a raw ``KeyError``).
# Re-open trigger: the next re-run of this script — port it first, then re-run.
# Built to measure the PRE-63c-i-a world; PART D's prose ("agent has NO scope column") still
# describes that world. PART C-agent was RE-POINTED 2026-11-07 at where the rule now lives:
# 63c-i-a (ruling §4.2 Q3 DROP + MOVE) dropped the agent.role store ASSERT into the ONE writer
# (``AgentRegistry.register``), so the C-control proves the WRITER refuses the poison, and the
# DD-3.c legs run the real migration path: the deployed asserted world -> HEAD's emitter.
"""Probe: packet-63c store + code FACTS (govern the comms REMAINDER — the ``brief``
+ ``agent`` populations), settled BY CONSTRUCTION on the live engine (built on
3.2.4; re-run on 3.3.5 on 2026-11-07) — never by reasoning (#107 came from
reasoning about engine behaviour instead of measuring it). This is the ii-a/ii-b
method (``scripts/probe_read_filter_63.py`` / ``scripts/probe_drain_read_63b_ii_b.py``)
turned on the two populations 63c owns.

WHY. 63c retrofits the packet-61 governance onto the comms REMAINDER: the ``brief``
ledger (``brief_get``/``brief_publish``/``brief_ack``) and the ``agent`` ROSTER
(``fleet``/``heartbeat``). Three store/code facts the design sidecar + contract
author will rule on are BELIEVED-not-known; each is a #107/#131-class hazard (green
on a small/virgin test DB, a fault on a large/dirty long-lived store):

  * PART C — THE HEADLINE (the packet-03b DD-3.c hazard, the ii-b shape). Both
    ``agent`` and ``brief`` are POPULATED SCHEMAFULL tables; on a SCHEMAFULL table the
    WHOLE record is re-validated on ANY write (store reference §1.4). So a LEGACY row
    that violates a store ASSERT (written before the ASSERT was landed/narrowed — a
    #131 long-lived dirty store) is write-poisoned: does a whole-window UPDATE (the 63c
    owner/scope BACKFILL) — or a single-row UPDATE (``heartbeat``'s ``touch``) — re-fire
    that ASSERT and ERROR, aborting the statement (store reference §3)? For a
    whole-window backfill that is TOTAL DENIAL of the migration (DD-3.c verbatim).
    Settled by CONSTRUCTING the dirty row and OBSERVING which ASSERTs re-fire.
    ``brief`` still carries its name/body/created_by store ASSERTs at HEAD (their DROP
    is 63c-ii), so C-brief measures them live. ``agent.role`` does NOT any more:
    63c-i-a (ruling ``docs/design/2026-09-13-packet63c-remainder-ruling.md`` §4.2 Q3)
    DROPPED it and MOVED the non-empty rule into ``AgentRegistry.register``. So C-agent
    proves the rule at the WRITER, then runs the real migration: a legacy role='' row
    under the DEPLOYED asserted world (the shared frozen capture) re-fires there, and
    HEAD's emitter, re-applied over it, must drop the ASSERT (the §4.4 two-leg shape).
  * PART D — the governed READ-filter plans (mirror ii-a probe-63). Does the packet-61
    ``authorize_filter(subject, READ, table)`` member filter IndexScan on ``brief``
    once the three governed columns + their two plain indexes are spliced on? And on
    ``agent`` — which has ``owner_principal`` (indexed) but NO ``scope`` column — what
    do the CANDIDATE fleet read-filters plan? (REPORT-only: the sidecar rules the
    mechanism on these MEASURED facts.)
  * PART E — finding #467 (the agent-registry cross-principal residual). The two
    measured behaviours (touch-before-deny; the UnknownAgent roster leak) reproduced
    at the REGISTRY level on the wire, plus the EXACT code sites each fix lands at.

STORE-REF anchors this probe confirms/extends (CITED, never re-transcribed):
  * §1.4 — a SCHEMAFULL narrowing converges SCHEMA not DATA; a later UPDATE of an old
    row is "rejected loudly ... because the whole record is re-validated on write",
    and the fixture trap: a legacy row written AFTER the migration cannot see the
    hazard — write it UNDER the old DDL, then migrate. PART C extends that
    [MEASURED]-on-``memory``/``to`` fact to ``agent`` + ``brief`` and to the exact 63c
    backfill/heartbeat writes.
  * §3 — one failed statement aborts the WHOLE ``BEGIN;…;COMMIT;`` / whole UPDATE.
    PART C's total-denial verdict rests on this.
  * §1.1 — OVERWRITE-for-fields (the only clause that lands a changed/re-landed def;
    IF NOT EXISTS is the #107 silent no-op); §1.5/§4 — a plain index over ``option<>``
    with NONE rows still IndexScans equality (ii-a P1); a graph field-through-hop is
    un-indexable (agent.session→keep).

METHOD (store-law discipline + the C1 "a probe NEEDS a positive control" rule).
Every scan claim is a live EXPLAIN classified by the SAME plan-walker the shipped
pins use, REUSED from ``probe_read_filter_63.py`` (its ``explain`` / ``_require`` /
``ProbeReport`` / ``_apply_ddl`` / connect constants), never re-cloned
(ROUTING-IS-NOT-SHARING does not demand two throwaway probes fork a walker). The
raw per-statement status helpers are REUSED from ``probe_drain_read_63b_ii_b.py``
(the DD-3.c probe this one mirrors). The READ predicate under test is the REAL
emitter output (``authorize_filter``), the DDL is the REAL top-level generators
(``generate_agent_ddl`` / ``generate_brief_ddl``) + the REAL governed overlay
(``_governed_field_specs`` / ``_governed_index_statements``), never hand-typed.

SELF-CHECKING where a leg has a DEFINITE expected shape (exit non-zero on a
surprise): every C+ walker control classifies as stated; the PART-C C-controls prove
each rule is REAL where it LIVES — for ``brief`` a fresh violating write under the
CURRENT DDL is REJECTED by the store; for ``agent`` the ONE writer
(``AgentRegistry.register``) REFUSES role='' / role='   ' with nothing written and
ACCEPTS a real role — else the poison is not genuinely non-conformant and the probe is
INVALID; under the deployed asserted ``agent`` world a heartbeat over the poisoned row
ERRORs while one over a conforming row does not (the instrument can SEE the abort); each
CONFORMING positive-control UPDATE succeeds; the PART-D REQUIRE legs (brief scope=, brief
full READ fragment, agent owner_principal=) IndexScan. Whether each poisoned-row UPDATE
under the CURRENT DDL errors is the measurement itself — printed, never an exit gate —
as are the PART-D agent candidate fleet filters and PART-E.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000`` —
creds root/spikeroot, matching ``loremaster/tests/_surreal_harness.py`` and the ii-a/
ii-b probes), and drops it on exit. It NEVER touches production (lore-surreal :18500).
Referenced principal/agent records for the READ-filter EXPLAINs are NOT created
(plain ``record<>`` links; the plan is chosen structurally, store-ref §2/§4); the
PART-E registry repro DOES register real agent rows (the real ``touch``/``fleet``).

Run: ``uv run python scripts/probe_governed_63c.py``
Exit 0 iff every control + every definite-shape expectation held; non-zero on any
surprise. The PART-D agent candidate-filter plans and the PART-E behaviours are
DIAGNOSTIC (reported; #467 is already MEASURED over the full wire by
secaudit-63b-iii — this probe adds the registry-level minimal repro + the code sites).
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime
from typing import Any

# REUSE the ii-a probe's EXPLAIN harness (same ``scripts/`` dir → on sys.path when run
# as a file; insert defensively so ``uv run`` cannot surprise us). Its plan-walker,
# ``explain``/``_require``/``ProbeReport``/``_apply_ddl`` and connect constants are the
# SHIPPED ii-a instrument — not re-cloned here (store-law C1: do not fork a throwaway
# walker). The raw per-statement status helpers are the ii-b DD-3.c instrument.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loremaster.agents import AgentRegistry, InvalidAgentIdentityError  # noqa: E402
from loremaster.store._txn import bootstrap_session, signin_credentials  # noqa: E402
from loremaster.store.surreal_schema import (  # noqa: E402
    BRIEF_TABLE,
    _define_field,
    _governed_field_specs,
    _governed_index_statements,
    generate_agent_ddl,
    generate_brief_ddl,
)
from lorerunes.pdp import (  # noqa: E402
    AGENT_TABLE,
    PRINCIPAL_ROLE_MEMBER,
    PRINCIPAL_TABLE,
    Action,
    Subject,
    authorize_filter,
)
from probe_drain_read_63b_ii_b import (  # noqa: E402 — the ii-b DD-3.c raw-status helpers
    _any_err,
    _err_texts,
    _query_raw,
)
from probe_read_filter_63 import (  # noqa: E402 — deferred until sys.path is primed
    NAMESPACE,
    PASSWORD,
    URL,
    USER,
    ProbeReport,
    _apply_ddl,
    _ddl,
    _require,
    explain,
    unique_database,
)
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal, RecordID  # noqa: E402

# The member Subject whose REAL emitter output PART D splices — the SAME member as the
# ii-a probe (alice/ag_a, 2 keeps), so the brief fragment is byte-identical to what a
# governed brief_get would splice.
_SUBJECT = Subject(
    principal_id="alice",
    agent_id="ag_a",
    role=PRINCIPAL_ROLE_MEMBER,
    visible_keep_ids=frozenset({"keep:k1", "keep:k2"}),
)

_SCOPE_SERVER = "server"  # a fixed scope every disjunct's IndexScan can key on


# --------------------------------------------------------------------------- #
# DDL helpers — the REAL generators + governed overlay, plus the #131 downgrade
# path for PART C. ``_governed_overlay`` is the SAME emitter the ii-a probe applies
# to ``message`` (design §1.2 item 4), applied here to ``brief`` (ROUTING-IS-NOT-
# SHARING: production code, not a copy of it).
# --------------------------------------------------------------------------- #


def _governed_overlay(table: str) -> str:
    """The three governed columns + their two plain indexes for ``table``, emitted by
    the REAL production seams (``_governed_field_specs`` via ``_define_field`` → OVERWRITE,
    ``_governed_index_statements`` → plain ``IF NOT EXISTS`` on scope + owner_principal)."""
    statements = [
        _define_field(table, name, type_expr, constraint=constraint)
        for name, type_expr, constraint in _governed_field_specs()
    ]
    statements += _governed_index_statements(table)
    return _ddl(statements)


async def _create_conforming_brief(
    connection: Any, row_id: str, *, name: str, version: int, scope: str | None = None
) -> None:
    """A schema-conforming ``brief`` row (all ASSERTs satisfied). ``scope`` optional
    (NONE = an un-migrated legacy row)."""
    fields = [
        "name: $name",
        "version: $version",
        "body: $body",
        "created_by: $created_by",
        "created_at: time::now()",
    ]
    params: dict[str, Any] = {
        "id": row_id,
        "name": name,
        "version": version,
        "body": "a real standing instruction body with several words",
        "created_by": "probe-63c",
    }
    if scope is not None:
        fields.append("scope: $sc")  # $scope is a PROTECTED param name (store-ref §2)
        params["sc"] = scope
    await connection.query(
        f"CREATE type::record('{BRIEF_TABLE}', $id) CONTENT {{ {', '.join(fields)} }}", params
    )


async def _create_conforming_agent(
    connection: Any, row_id: str, *, name: str, session: str, status: str = "active"
) -> None:
    """A schema-conforming ``agent`` row (all ASSERTs satisfied), owner_principal NONE
    (an un-migrated legacy row for the owner backfill)."""
    await connection.query(
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT {{ "
        "name: $name, session: $sess, role: $role, status: $status, "
        "registered_at: time::now(), heartbeat_at: time::now() }",
        {"id": row_id, "name": name, "sess": session, "role": "probe", "status": status},
    )


# --------------------------------------------------------------------------- #
# PART C — DD-3.c reachability on ``agent`` + ``brief`` (the load-bearing fact).
# For EACH rule: downgrade the field (drop its ASSERT), write a LEGACY row that
# VIOLATES it (store-ref §1.4 — under the OLD DDL, before the migrate), land the
# asserted definition over it (brief: HEAD's emitter, which still asserts; agent: the
# DEPLOYED asserted world, then HEAD's emitter, which drops the role ASSERT), then run
# the relevant whole-window / single-row UPDATE and OBSERVE whether whole-record
# re-validation aborts. Every negative is paired with a CONFORMING positive control.
# --------------------------------------------------------------------------- #


async def _downgrade(connection: Any, table: str, column: str, type_expr: str) -> None:
    """OVERWRITE ``table.column`` back to a NO-ASSERT definition — the #131 pre-bound
    world (store-ref §1.1 OVERWRITE is the only clause that lands the changed def)."""
    await _apply_ddl(connection, f"DEFINE FIELD OVERWRITE {column} ON {table} TYPE {type_expr};\n")


async def _agent_names_present(connection: Any, names: list[str]) -> list[str]:
    """The subset of ``names`` that has an ``agent`` row — the read-back a writer refusal
    is checked against ("nothing was written" is observed, never assumed)."""
    rows = await connection.query(
        f"SELECT name FROM {AGENT_TABLE} WHERE name IN $names", {"names": names}
    )
    return sorted(str(row.get("name")) for row in rows or [] if isinstance(row, dict))


async def _agent_writer_control(database: str, connection: Any, report: ProbeReport) -> bool:
    """C-CONTROL, at the rule's HOME since 63c-i-a (ruling §4.2 Q3 MOVE): the ONE writer
    ``AgentRegistry.register`` REFUSES the poison (role='' and the whitespace-only role the
    dropped store ASSERT's ``string::trim`` also refused) with NOTHING written, and ACCEPTS a
    real role (positive control: the refusal is about the role, not a writer that refuses
    everything). False ⇒ the DD-3.c poison is not non-conformant under the current rules."""
    registry = AgentRegistry(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=SecretStr(PASSWORD)
    )
    refused: dict[str, bool] = {}
    try:
        await registry.ensure_ready()
        for label, name, role in (("empty", "agwriterempty", ""), ("blank", "agwriterblank", "   ")):
            try:
                await registry.register(name, session="sess1", role=role)
                refused[label] = False
            except InvalidAgentIdentityError as error:
                refused[label] = True
                print(f"  [C-control writer] register(role={role!r}) REFUSED: {error}")
        await registry.register("agwriterok", session="sess1", role="probe")
    finally:
        await registry.close()
    leaked = await _agent_names_present(connection, ["agwriterempty", "agwriterblank"])
    accepted = await _agent_names_present(connection, ["agwriterok"]) == ["agwriterok"]
    held = all(refused.values()) and not leaked and accepted
    print(f"  [C-control writer] refused={refused} rows-written-by-refusals={leaked} "
          f"real-role accepted+written={accepted}")
    if not held:
        report.surprises.append(
            "PART C-agent C-CONTROL FAILED — the ONE writer AgentRegistry.register did not refuse a "
            f"blank role with nothing written, or refused a real one (refused={refused}, "
            f"written-by-refusals={leaked}, real-role accepted={accepted}). The 63c-i-a MOVE says the "
            "writer enforces what the dropped store ASSERT did: if it does not, that is a PRODUCTION "
            "defect, and the DD-3.c poison below is not genuinely non-conformant (a false clear)."
        )
    return held


async def _agent_deployed_world_control(connection: Any, report: ProbeReport, now: datetime) -> bool:
    """C0 — INSTRUMENT CONTROL: land the DEPLOYED asserted ``agent`` world over the legacy rows,
    then a heartbeat over the poisoned row must ERROR (whole-record re-validation re-fires role's
    ASSERT) and one over a conforming row must not. Without it, a non-erroring C1 under HEAD's DDL
    could be a blind instrument, not a fixed hazard. Returns whether the poisoned heartbeat errored."""
    # The DEPLOYED world (name/session charset, role non-empty, status domain), HAND-CAPTURED once in
    # the shared contract helper — the capture the 63c-i-a §4.4 dirty-store legs use, so this probe and
    # those pins cannot drift about production's asserted shape. Imported HERE because the module is
    # importable only once ``probe_read_filter_63`` has put ``loremaster/tests`` on sys.path (a
    # module-level import would be re-sorted above it).
    from _governed_contract import frozen_asserted_agent_ddl

    await _apply_ddl(connection, frozen_asserted_agent_ddl())
    c0_raw = await _query_raw(
        connection,
        f"UPDATE type::record('{AGENT_TABLE}', $id) SET heartbeat_at = $t",
        {"id": "ag_poison", "t": now},
    )
    c0_ok_raw = await _query_raw(
        connection,
        f"UPDATE type::record('{AGENT_TABLE}', $id) SET heartbeat_at = $t",
        {"id": "ag_ok1", "t": now},
    )
    print(f"\n  [C0 DEPLOYED world: heartbeat over POISONED] errored={_any_err(c0_raw)}")
    print(f"      err: {_err_texts(c0_raw)}")
    print(f"  [C0-control DEPLOYED world: heartbeat over CONFORMING] errored={_any_err(c0_ok_raw)}")
    if not _any_err(c0_raw) or _any_err(c0_ok_raw):
        report.surprises.append(
            "PART C-agent C0 FAILED — under the DEPLOYED asserted agent world a heartbeat over the "
            f"role='' row did not error ({_err_texts(c0_raw)}) or one over a conforming row did "
            f"({_err_texts(c0_ok_raw)}). The probe cannot SEE the DD-3.c abort, so a non-erroring C1 "
            "below would be a false clear."
        )
    return _any_err(c0_raw)


async def _agent_dd3c(database: str, connection: Any, report: ProbeReport) -> dict[str, Any]:
    """DD-3.c on ``agent``: heartbeat (single-row ``touch``) + the owner backfill
    (whole-window). The poison is ``role = ''`` (non-conformant under the writer's rule and
    a field ``touch`` does NOT set, so it cannot be repaired by the write)."""
    findings: dict[str, Any] = {}
    print("\n" + "=" * 78)
    print("PART C-agent — DD-3.c on the `agent` table (heartbeat touch + owner backfill)")
    print("=" * 78)

    # NB: NO governed overlay on agent — agent already ships owner_principal + its plain
    # index in generate_agent_ddl (pkt 62), and — BEFORE 63c-i-a — agent deliberately had NO scope
    # column (PART D measured that fact; 63c-i-a adds one). The owner backfill needs only owner_principal.
    await _apply_ddl(connection, generate_agent_ddl())

    findings["agent_cap_real"] = await _agent_writer_control(database, connection, report)

    # STORE FACT (DIAGNOSTIC, not a gate): HEAD's DDL carries NO role store ASSERT (dropped by
    # design, 63c-i-a §4.2), so a raw role='' CREATE that bypasses the writer is ACCEPTED.
    store_raw = await _query_raw(
        connection,
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT {{ name: $n, session: $s, "
        "role: '', status: 'active', registered_at: time::now(), heartbeat_at: time::now() }",
        {"id": "ag_ctrl_reject", "n": "agctrlreject", "s": "sess1"},
    )
    findings["agent_store_accepts_blank_role"] = not _any_err(store_raw)
    print(f"  [store fact] raw role='' CREATE under HEAD DDL accepted={not _any_err(store_raw)} "
          "(expected True: the store bound was dropped into the writer)")

    # #131 dance: downgrade role → write the dirty legacy row (role='') → land the DEPLOYED asserted
    # world over it (production's shape before 63c-i-a deploys) → then migrate to HEAD below.
    await _downgrade(connection, AGENT_TABLE, "role", "string")
    await connection.query(
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT {{ name: $n, session: $s, "
        "role: '', status: 'active', registered_at: time::now(), heartbeat_at: time::now() }",
        {"id": "ag_poison", "n": "agpoison", "s": "sess1"},
    )
    await _create_conforming_agent(connection, "ag_ok1", name="agok1", session="sess1")
    await _create_conforming_agent(connection, "ag_ok2", name="agok2", session="sess1")
    now = datetime.now(UTC)
    findings["agent_deployed_heartbeat_poisoned_errored"] = await _agent_deployed_world_control(
        connection, report, now
    )

    # THE MIGRATION: HEAD's emitter, re-applied over the deployed world (OVERWRITE is a FULL
    # REPLACE, store-ref §1.2 — it must DROP the stored role ASSERT; the legacy row stays as it is).
    await _apply_ddl(connection, generate_agent_ddl())

    # C1 — heartbeat's SINGLE-ROW touch UPDATE over the poisoned row under HEAD's DDL (a bare
    # heartbeat stamp — role is NOT a field touch sets, so the stamp cannot repair it). An ERR
    # here means a store ASSERT on role still re-fires and that agent can NEVER heartbeat.
    c1_raw = await _query_raw(
        connection,
        f"UPDATE type::record('{AGENT_TABLE}', $id) SET heartbeat_at = $t",
        {"id": "ag_poison", "t": now},
    )
    findings["agent_heartbeat_poisoned_errored"] = _any_err(c1_raw)
    findings["agent_heartbeat_err"] = _err_texts(c1_raw)
    print(f"\n  [C1 heartbeat single-row over POISONED] errored={_any_err(c1_raw)}")
    print(f"      err: {_err_texts(c1_raw)}")
    # C1-control: the SAME single-row heartbeat over a CONFORMING row succeeds.
    c1_ok_raw = await _query_raw(
        connection,
        f"UPDATE type::record('{AGENT_TABLE}', $id) SET heartbeat_at = $t",
        {"id": "ag_ok1", "t": now},
    )
    findings["agent_heartbeat_conforming_errored"] = _any_err(c1_ok_raw)
    print(f"  [C1-control heartbeat over CONFORMING] errored={_any_err(c1_ok_raw)}")
    if _any_err(c1_ok_raw):
        report.surprises.append(
            "PART C-agent C1-control FAILED — a heartbeat over a CONFORMING agent row errored "
            f"({_err_texts(c1_ok_raw)}); the walker cannot see a clean single-row UPDATE."
        )

    # C2 — the OWNER BACKFILL as a WHOLE-WINDOW UPDATE over [poison + conforming] under HEAD's
    # DDL. If any store ASSERT still re-fired, one poisoned row would abort the WHOLE statement
    # (store-ref §3) => TOTAL backfill denial, the conforming rows NOT stamped either.
    op = RecordID(PRINCIPAL_TABLE, "alice")
    c2_raw = await _query_raw(
        connection,
        f"UPDATE {AGENT_TABLE} SET owner_principal = $op WHERE owner_principal IS NONE",
        {"op": op},
    )
    stamped_after = await connection.query(
        f"SELECT count() AS n FROM {AGENT_TABLE} WHERE owner_principal IS NOT NONE GROUP ALL"
    )
    n_stamped = _scalar(stamped_after, "n") or 0
    findings["agent_backfill_errored"] = _any_err(c2_raw)
    findings["agent_backfill_err"] = _err_texts(c2_raw)
    findings["agent_backfill_stamped_after"] = n_stamped
    print(f"\n  [C2 owner backfill WHOLE-WINDOW over poison+conforming] errored={_any_err(c2_raw)}")
    print(f"      err: {_err_texts(c2_raw)}")
    print(f"      rows stamped owner_principal after (0 = total denial): {n_stamped}")

    # C2-control: the SAME backfill scoped by id to CONFORMING-only rows succeeds+stamps.
    ids_ok = [RecordID(AGENT_TABLE, "ag_ok1"), RecordID(AGENT_TABLE, "ag_ok2")]
    c2_ok_raw = await _query_raw(
        connection,
        f"UPDATE {AGENT_TABLE} SET owner_principal = $op WHERE owner_principal IS NONE AND id IN $ids",
        {"op": op, "ids": ids_ok},
    )
    stamped2 = await connection.query(
        f"SELECT count() AS n FROM {AGENT_TABLE} WHERE owner_principal IS NOT NONE GROUP ALL"
    )
    findings["agent_backfill_control_errored"] = _any_err(c2_ok_raw)
    findings["agent_backfill_control_stamped"] = _scalar(stamped2, "n") or 0
    print(f"  [C2-control backfill over CONFORMING-only ids] errored={_any_err(c2_ok_raw)}, "
          f"stamped now={_scalar(stamped2, 'n') or 0}")
    if _any_err(c2_ok_raw) or (_scalar(stamped2, "n") or 0) < 2:
        report.surprises.append(
            "PART C-agent C2-control FAILED — the owner backfill over CONFORMING-only rows "
            f"errored ({_err_texts(c2_ok_raw)}) or did not stamp both ({_scalar(stamped2, 'n')}). "
            "The walker cannot see a clean whole-window backfill."
        )
    return findings


async def _brief_dd3c(connection: Any, report: ProbeReport) -> dict[str, Any]:
    """DD-3.c on ``brief``: the scope BACKFILL (whole-window ``UPDATE brief SET scope
    WHERE scope IS NONE``). ONE legacy row per re-validated ASSERT (name charset / body
    non-empty / created_by non-empty), each attributed by a SINGLE-ROW targeted UPDATE,
    then the WHOLE-WINDOW total-denial run."""
    findings: dict[str, Any] = {}
    print("\n" + "=" * 78)
    print("PART C-brief — DD-3.c on the `brief` table (the scope backfill migration)")
    print("=" * 78)

    await _apply_ddl(connection, generate_brief_ddl())
    await _apply_ddl(connection, _governed_overlay(BRIEF_TABLE))  # adds scope/owner cols + indexes

    # C-CONTROL: each ASSERT is REAL under the CURRENT DDL (a fresh violating CREATE is
    # REJECTED). Three fresh writes, one per ASSERT.
    caps: dict[str, bool] = {}
    for label, name, body, created_by in (
        ("body", "capbody", "", "probe-63c"),
        ("name", "Bad Name!", "a real body with several words", "probe-63c"),
        ("created_by", "capcreatedby", "a real body with several words", ""),
    ):
        raw = await _query_raw(
            connection,
            f"CREATE type::record('{BRIEF_TABLE}', $id) CONTENT {{ name: $name, version: 1, "
            "body: $body, created_by: $cb, created_at: time::now() }",
            {"id": f"b_cap_{label}", "name": name, "body": body, "cb": created_by},
        )
        caps[label] = _any_err(raw)
        print(f"  [C-control] fresh {label}-violating CREATE under CURRENT DDL rejected={_any_err(raw)}")
    findings["brief_caps_real"] = caps
    for label, rejected in caps.items():
        if not rejected:
            report.surprises.append(
                f"PART C-brief C-CONTROL FAILED — a fresh brief violating the {label} ASSERT was "
                f"NOT rejected under the CURRENT DDL; the ASSERT is not live, so the {label} "
                "DD-3.c poison is not genuinely non-conformant (a false clear)."
            )

    # #131 dance: downgrade name/body/created_by → write ONE dirty row per ASSERT → re-land.
    await _downgrade(connection, BRIEF_TABLE, "name", "string")
    await _downgrade(connection, BRIEF_TABLE, "body", "string")
    await _downgrade(connection, BRIEF_TABLE, "created_by", "string")
    # one poisoned row per ASSERT (each violates exactly ONE; the others valid) — so a
    # single-row UPDATE attributes the abort to that ASSERT. scope NONE (un-migrated).
    poisoned = {
        "body": ("b_poison_body", "poisonbody", 1, "", "probe-63c"),
        "name": ("b_poison_name", "Bad Name!", 1, "a real body with several words", "probe-63c"),
        "created_by": ("b_poison_cb", "poisoncb", 1, "a real body with several words", ""),
    }
    for _label, (row_id, name, version, body, cb) in poisoned.items():
        await connection.query(
            f"CREATE type::record('{BRIEF_TABLE}', $id) CONTENT {{ name: $name, version: $v, "
            "body: $body, created_by: $cb, created_at: time::now() }",
            {"id": row_id, "name": name, "v": version, "body": body, "cb": cb},
        )
    await _create_conforming_brief(connection, "b_ok", name="briefok", version=1)  # scope NONE
    await _apply_ddl(connection, generate_brief_ddl())  # re-lands name/body/created_by ASSERTs
    await _apply_ddl(connection, _governed_overlay(BRIEF_TABLE))  # scope col persists (no assert)

    server = _SCOPE_SERVER
    # Per-ASSERT single-row backfill: whole-record re-validation aborts, naming the field.
    for label, (row_id, *_rest) in poisoned.items():
        raw = await _query_raw(
            connection,
            f"UPDATE type::record('{BRIEF_TABLE}', $id) SET scope = $sc",
            {"id": row_id, "sc": server},
        )
        findings[f"brief_{label}_errored"] = _any_err(raw)
        findings[f"brief_{label}_err"] = _err_texts(raw)
        print(f"\n  [C single-row scope-set over {label}-poisoned] errored={_any_err(raw)}")
        print(f"      err: {_err_texts(raw)}")
    # positive control: single-row scope-set over the CONFORMING row succeeds.
    ok_raw = await _query_raw(
        connection,
        f"UPDATE type::record('{BRIEF_TABLE}', $id) SET scope = $sc",
        {"id": "b_ok", "sc": server},
    )
    findings["brief_conforming_errored"] = _any_err(ok_raw)
    print(f"\n  [C-control single-row scope-set over CONFORMING] errored={_any_err(ok_raw)}")
    if _any_err(ok_raw):
        report.surprises.append(
            "PART C-brief C-control FAILED — a scope-set over a CONFORMING brief row errored "
            f"({_err_texts(ok_raw)}); the walker cannot see a clean single-row UPDATE."
        )

    # Whole-window TOTAL-DENIAL run: reset the conforming row to scope NONE, then
    # ``UPDATE brief SET scope WHERE scope IS NONE`` over [poison + conforming]. One
    # poisoned row aborts the WHOLE statement (store-ref §3) — the conforming row is NOT
    # stamped either (all-or-nothing).
    await connection.query(
        f"UPDATE type::record('{BRIEF_TABLE}', $id) SET scope = NONE", {"id": "b_ok"}
    )
    ww_raw = await _query_raw(
        connection, f"UPDATE {BRIEF_TABLE} SET scope = $sc WHERE scope IS NONE", {"sc": server}
    )
    remaining_none = await connection.query(
        f"SELECT count() AS n FROM {BRIEF_TABLE} WHERE scope IS NONE GROUP ALL"
    )
    n_none = _scalar(remaining_none, "n") or 0
    findings["brief_backfill_errored"] = _any_err(ww_raw)
    findings["brief_backfill_err"] = _err_texts(ww_raw)
    findings["brief_backfill_none_remaining"] = n_none
    print(f"\n  [C whole-window scope backfill over poison+conforming] errored={_any_err(ww_raw)}")
    print(f"      err: {_err_texts(ww_raw)}")
    print(f"      brief rows still scope=NONE after (all remain = total denial): {n_none}")
    return findings


# --------------------------------------------------------------------------- #
# PART D — governed READ-filter EXPLAINs (brief REQUIRE; agent REPORT).
# --------------------------------------------------------------------------- #


async def _part_d(connection: Any, report: ProbeReport) -> dict[str, Any]:
    findings: dict[str, Any] = {}
    print("\n" + "=" * 78)
    print("PART D — governed READ-filter EXPLAINs")
    print("=" * 78)

    # brief already carries governed cols + indexes (PART C-brief applied them). Seed
    # brief rows spanning the READ disjuncts + a NONE-scope legacy so option<>+NONE is
    # exercised (ii-a P1). These are ADDITIONAL rows (distinct ids/names/versions).
    briefs = [
        ("d_ap", "dbriefap", "agent-private"),
        ("d_pp", "dbriefpp", "principal-private"),
        ("d_srv", "dbriefsrv", "server"),
        ("d_k1", "dbriefk1", "keep:k1"),
        ("d_other", "dbriefother", "keep:k9"),
        ("d_legacy", "dbrieflegacy", None),
    ]
    for row_id, name, scope in briefs:
        await _create_conforming_brief(connection, row_id, name=name, version=2, scope=scope)

    mem_fragment, mem_params = authorize_filter(_SUBJECT, Action.READ, BRIEF_TABLE).to_surql()
    print("\n=== REAL EMITTER OUTPUT: authorize_filter(member, READ, brief) ===")
    print(f"  fragment: {mem_fragment}")
    print(f"  params  : {mem_params}")

    print("\n=== brief — instrument controls + REQUIRE legs ===")
    ctrl_scope = await explain(
        report, connection, label="CTRL brief scope= (indexed → IndexScan)",
        table=BRIEF_TABLE, where="scope = $s", params={"s": _SCOPE_SERVER},
    )
    _require(report, ctrl_scope, "IndexScan",
             "brief_scope must IndexScan or the walker is blind on brief.")
    ctrl_op = await explain(
        report, connection, label="CTRL brief owner_principal= (indexed → IndexScan)",
        table=BRIEF_TABLE, where=f"owner_principal = type::record('{PRINCIPAL_TABLE}', $p)",
        params={"p": "alice"},
    )
    _require(report, ctrl_op, "IndexScan",
             "brief_owner_principal must IndexScan or the second governed index is dead/mis-defined.")
    ctrl_ts = await explain(
        report, connection, label="CTRL brief created_by= (unindexed → TableScan)",
        table=BRIEF_TABLE, where="created_by = $c", params={"c": "probe-63c"},
    )
    _require(report, ctrl_ts, "TableScan",
             "the walker cannot SEE a TableScan on an unindexed brief column — blind.")
    d_scope = await explain(
        report, connection, label="D-brief-1 scope= (option<> + NONE rows present)",
        table=BRIEF_TABLE, where="scope = $s", params={"s": _SCOPE_SERVER}, dump=True,
    )
    _require(report, d_scope, "IndexScan",
             "a plain index on option<string> scope (NONE rows present) must serve equality on brief.")
    d_full = await explain(
        report, connection, label="D-brief-2 FULL READ fragment (real emitter, member 2 keeps)",
        table=BRIEF_TABLE, where=mem_fragment, params=mem_params, dump=True,
    )
    _require(report, d_full, "IndexScan",
             "the emitted flat-OR read_filter must be index-served (3.2 UnionIndexScan, 3.3 "
             "BitmapOr) with NO TableScan of brief "
             "(same verdict as ii-a P3 on message).")
    findings["brief_scope"] = d_scope.classification
    findings["brief_full"] = d_full.classification

    print("\n=== agent — owner_principal REQUIRE + candidate fleet filters (REPORT) ===")
    a_op = await explain(
        report, connection, label="D-agent-1 owner_principal= (agent_owner_principal index)",
        table=AGENT_TABLE, where=f"owner_principal = type::record('{PRINCIPAL_TABLE}', $p)",
        params={"p": "alice"}, dump=True,
    )
    _require(report, a_op, "IndexScan",
             "agent already carries the pkt-62 agent_owner_principal plain index — "
             "'which agents does principal X own' must be index-served (store-ref §4).")
    findings["agent_owner_principal"] = a_op.classification

    # Candidate fleet read-filters — REPORT-only (agent had NO scope column before 63c-i-a; the sidecar
    # rules the mechanism on these MEASURED plans, not this probe).
    agent_fragment, agent_params = authorize_filter(_SUBJECT, Action.READ, AGENT_TABLE).to_surql()
    print("\n  authorize_filter(member, READ, agent) fragment (agent has NO scope column):")
    print(f"    {agent_fragment}")
    a_full = await explain(
        report, connection, label="D-agent-2 FULL member READ fragment on agent (REPORT)",
        table=AGENT_TABLE, where=agent_fragment, params=agent_params, dump=True, report_only=True,
    )
    findings["agent_full_member_filter"] = a_full.classification
    a_session = await explain(
        report, connection, label="D-agent-3 session= (leading col of (session,status) index) (REPORT)",
        table=AGENT_TABLE, where="session = $s", params={"s": "sess1"}, dump=True, report_only=True,
    )
    findings["agent_session"] = a_session.classification
    return findings


# --------------------------------------------------------------------------- #
# PART E — finding #467 registry-level minimal repro (the full-wire repro is
# secaudit-63b-iii's; this adds the REGISTRY primitives each behaviour rests on).
# --------------------------------------------------------------------------- #


async def _part_e(database: str, report: ProbeReport) -> dict[str, Any]:
    findings: dict[str, Any] = {}
    print("\n" + "=" * 78)
    print("PART E — finding #467 registry-level repro (touch-before-deny + roster leak)")
    print("=" * 78)
    registry = AgentRegistry(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=SecretStr(PASSWORD)
    )
    try:
        await registry.ensure_ready()
        # Two SESSIONS, two agents each — the #467 F3-style 2-session shape.
        await registry.register("alice_w1", session="asess", role="probe")
        await registry.register("bob_w1", session="bsess", role="probe")
        await registry.register("bob_w2", session="bsess", role="probe")

        # BEHAVIOUR 1 — touch stamps heartbeat UNCONDITIONALLY. The comms dispatcher
        # (server.py AppContext.comms) runs ``agent_registry.touch(agent, ...)`` for EVERY
        # requires_registration action BEFORE spec.handler's §4.D capability check — so a
        # DENIED governed call naming a foreign agent still stamps that agent's heartbeat.
        # Registry-level primitive: touch writes heartbeat_at before any gate exists here.
        before = await registry.fleet(session="bsess", limit=50)
        hb_before = {row.name: row.heartbeat_at for row in before.rows}
        await asyncio.sleep(0.01)
        touched = await registry.touch("bob_w1", session="bsess")
        moved = touched.heartbeat_at > hb_before.get("bob_w1", touched.heartbeat_at)
        findings["touch_stamps_heartbeat"] = moved
        print(f"\n  [B1] touch('bob_w1') moved heartbeat_at ({hb_before.get('bob_w1')} -> "
              f"{touched.heartbeat_at}): {moved}")
        print("      (the §4.D capability DENY is downstream in spec.handler, server.py:6223;")
        print("       the touch at server.py:6216 runs FIRST — touch-before-deny, code-read.)")
        if not moved:
            report.surprises.append(
                "PART E B1 FAILED — touch did not advance heartbeat_at; the touch-before-deny "
                "write primitive could not be demonstrated at the registry level."
            )

        # BEHAVIOUR 2 — the roster leak. ``_comms_enrich_unknown_agent`` (server.py:6649)
        # calls ``fleet(session=<CALLER-SUPPLIED session>)`` and appends the non-retired
        # roster to the error. fleet is NOT caller-scoped: a foreign session returns THAT
        # session's roster; session=None returns the WHOLE fleet.
        foreign = await registry.fleet(session="bsess", limit=50)  # an 'alice' caller naming bsess
        foreign_names = sorted(row.name for row in foreign.rows)
        whole = await registry.fleet(session=None, limit=50)
        whole_names = sorted(row.name for row in whole.rows)
        findings["foreign_session_roster"] = foreign_names
        findings["whole_fleet_roster"] = whole_names
        print(f"\n  [B2] fleet(session='bsess') from an 'alice'-session caller -> {foreign_names}")
        print(f"       fleet(session=None) -> whole fleet across sessions -> {whole_names}")
        leak_foreign = "bob_w1" in foreign_names and "bob_w2" in foreign_names
        leak_whole = "alice_w1" in whole_names and "bob_w1" in whole_names
        findings["roster_leak_reproduced"] = leak_foreign and leak_whole
        if not (leak_foreign and leak_whole):
            report.surprises.append(
                "PART E B2 FAILED — fleet did not return a foreign session's roster / the whole "
                f"fleet (foreign={foreign_names}, whole={whole_names}); the roster-leak primitive "
                "the enrichment exposes could not be demonstrated."
            )
    finally:
        await registry.close()
    return findings


# --------------------------------------------------------------------------- #
# small helpers + orchestration
# --------------------------------------------------------------------------- #


def _scalar(result: Any, key: str) -> Any:
    rows = result
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0].get(key)
    return None


def _verdict(report: ProbeReport, c_agent: dict[str, Any], c_brief: dict[str, Any],
             d: dict[str, Any], e: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("VERDICTS")
    print("=" * 78)
    print("\n-- PART C (DD-3.c) --")
    print(f"  agent  cap-real(WRITER refuses role='')  : {c_agent.get('agent_cap_real')}")
    print(f"  agent  store accepts raw role='' (HEAD)  : {c_agent.get('agent_store_accepts_blank_role')}")
    print(f"  agent  DEPLOYED-world heartbeat POISONED : errored="
          f"{c_agent.get('agent_deployed_heartbeat_poisoned_errored')}")
    print(f"  agent  heartbeat single-row over POISONED: errored="
          f"{c_agent.get('agent_heartbeat_poisoned_errored')} (conforming="
          f"{c_agent.get('agent_heartbeat_conforming_errored')})")
    print(f"  agent  owner backfill WHOLE-WINDOW       : errored="
          f"{c_agent.get('agent_backfill_errored')}, rows stamped="
          f"{c_agent.get('agent_backfill_stamped_after')} (control stamped="
          f"{c_agent.get('agent_backfill_control_stamped')})")
    print(f"  brief  caps-real (name/body/created_by)  : {c_brief.get('brief_caps_real')}")
    for label in ("name", "body", "created_by"):
        print(f"  brief  scope-set over {label:<11} POISONED : errored="
              f"{c_brief.get(f'brief_{label}_errored')}")
    print(f"  brief  conforming single-row scope-set   : errored="
          f"{c_brief.get('brief_conforming_errored')}")
    print(f"  brief  scope backfill WHOLE-WINDOW       : errored="
          f"{c_brief.get('brief_backfill_errored')}, rows still NONE="
          f"{c_brief.get('brief_backfill_none_remaining')}")
    print("\n-- PART D (read-filter plans) --")
    print(f"  brief scope=            : {d.get('brief_scope')}")
    print(f"  brief FULL member filter: {d.get('brief_full')}")
    print(f"  agent owner_principal=  : {d.get('agent_owner_principal')}")
    print(f"  agent FULL member filter: {d.get('agent_full_member_filter')}  (REPORT — no scope col)")
    print(f"  agent session=          : {d.get('agent_session')}  (REPORT — (session,status) lead)")
    print("\n-- PART E (#467 registry-level) --")
    print(f"  B1 touch stamps heartbeat (touch-before-deny primitive): {e.get('touch_stamps_heartbeat')}")
    print(f"  B2 roster leak reproduced (foreign session + whole fleet): {e.get('roster_leak_reproduced')}")


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    report = ProbeReport()
    try:
        c_agent = await _agent_dd3c(database, connection, report)
        c_brief = await _brief_dd3c(connection, report)
        d = await _part_d(connection, report)
    finally:
        await connection.close()
    # PART E uses its own AgentRegistry connection against the SAME throwaway database.
    e = await _part_e(database, report)

    # cleanup
    cleanup = AsyncSurreal(URL)
    try:
        await cleanup.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
        await bootstrap_session(cleanup, NAMESPACE, database, url=URL)
        await cleanup.query(f"REMOVE DATABASE IF EXISTS {database}")
    except Exception as error:  # noqa: BLE001 - cleanup best-effort, never masks the result
        print(f"[cleanup warning] {type(error).__name__}: {error}")
    finally:
        await cleanup.close()

    _verdict(report, c_agent, c_brief, d, e)

    print("\n=== SELF-CHECK VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All controls held: each brief store ASSERT was real; the agent writer refused role=''")
    print("and accepted a real role; the deployed agent world showed the abort; every conforming")
    print("control succeeded; brief read-filter index-served; agent owner_principal index-served.")
    print("The poisoned-row UPDATE outcomes, PART-D agent-candidate plans and PART-E behaviours are")
    print("DIAGNOSTIC above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
