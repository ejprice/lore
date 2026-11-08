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
"""Probe: packet-63b wave ii-b (message READ side) store-shape questions, settled
BY CONSTRUCTION on the live engine (built on 3.2.4; re-run on 3.3.5 on 2026-11-07) —
never by reasoning (#107 came from reasoning about engine behaviour instead of measuring it).

WHY. ii-b retrofits the packet-61 governed READ filter onto the message read
surfaces (drain visibility, ``story``, the rollup message leg, ``await`` peek) and
proposes the §4.B "Reading-B" ONE-transaction drain. Three store-shape facts the
read side rests on are BELIEVED-not-known; each is a #107-class hazard (green on a
small/virgin test DB, a fault on a large/dirty long-lived store):

  * LEG A — do ii-b's composed read shapes IndexScan (no TableScan / no #413
    IN-in-OR trap) on the REAL ``message`` + ``to`` DDL?
  * LEG B — does the ruled ONE-txn Reading-B drain work (one round trip,
    snapshot-consistent, the UPDATE's RETURN AFTER stamps, the final RETURN serves
    the visible set)?
  * LEG C — THE HEADLINE (the packet-03b DD-3.c hazard). The ``ack_note`` bound
    (``MESSAGE_BODY_MAX_CHARS``) lives in the ONE writer, ``MessageLedger.ack``
    (``_reject_oversize_note``): 63b-ii-b (ruling
    ``docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md`` §3 R1, §12.7 R16)
    DROPPED the ``to.ack_note`` store ASSERT, but the DEPLOYED store still carries it
    (store reference §0a). ``ack`` can set ``ack_note`` on an edge whose
    ``seen_at IS NONE``, so a LEGACY over-cap edge (written before the bound; a #131
    long-lived dirty store) can sit UNSEEN in a drain window. drain's
    ``UPDATE to SET seen_at=$t WHERE ... seen_at IS NONE`` TOUCHES that row. On a
    SCHEMAFULL table the WHOLE record is re-validated on any write (store reference
    §1.4) — so under an asserted ``ack_note`` stamping ONLY ``seen_at`` re-fires the
    ASSERT and ERRORs, aborting the whole one-txn drain (store reference §3) → TOTAL
    INBOX DENIAL (DD-3.c verbatim). Settled by CONSTRUCTING the dirty edge, landing
    the DEPLOYED bound over it (C0 shows the abort there), migrating with HEAD's
    emitter (which must drop the bound), and OBSERVING the drain.

STORE-REF anchors this probe confirms/extends (CITED, never re-transcribed):
  * §1.4 — a SCHEMAFULL narrowing converges SCHEMA not DATA; a later UPDATE of an
    old row is "rejected loudly ... because the whole record is re-validated on
    write". LEG C extends that [MEASURED]-on-``memory`` fact to the ``to`` EDGE
    table and to the exact ``SET seen_at`` write drain performs.
  * §3 — one failed statement aborts the WHOLE ``BEGIN;…;COMMIT;``. LEG C's one-txn
    verdict rests on this.
  * §2 (``IN``-in-``OR`` #413 TableScan trap; explicit-projection-reads-None;
    ``UPDATE`` of edge ``in``/``out`` is a silent no-op) and §4 (ENFORCED live on
    ``to`` @ df59f76; RELATE needs bound RecordID endpoints; dangling-edge facts).

METHOD (store-law discipline + the C1 "a probe NEEDS a positive control" rule).
Every scan claim is a live EXPLAIN classified by the SAME plan-walker the shipped
pin uses, REUSED from ``probe_read_filter_63.py`` (the ii-a probe) — its
``explain`` / ``_require`` / ``ProbeReport`` / connect constants / ``_create_message``
/ ``_read_fragment`` / ``_SUBJECT``, imported not re-cloned (ROUTING-IS-NOT-SHARING
does not demand two throwaway probes fork a walker). The READ predicate under test
is the REAL emitter output (``authorize_filter(subject, Action.READ, message)``),
never a hand-typed WHERE. LEG C runs raw ``query_raw`` so the EXACT per-statement
engine status is visible (``execute_transaction`` would launder it — store §3).

SELF-CHECKING where a leg has a DEFINITE expected shape (exit non-zero on a
surprise): the LEG-A drain SELECT + bare read_filter must IndexScan; the walker
controls must classify as stated; the LEG-C ``ack_note`` cap must be REAL where it
lives — the ONE writer ``MessageLedger.ack`` REFUSES an over-cap note with nothing
written and ACCEPTS an at-cap one (else the dirty edge is not non-conformant and the
probe is invalid); C0 — under the DEPLOYED bound the drain UPDATE over the dirty window
must ABORT with nothing stamped (else the instrument cannot see the hazard, and a
GRACEFUL verdict would be a false clear); the LEG-B / LEG-C positive controls (clean
window, dirty-outside-window) must serve+stamp with no error. DIAGNOSTIC for the LEG-C
headline: it reports the mechanism and a one-line verdict (ABORTS-WHOLE / GRACEFUL / N/A), it does not
pass/fail the hazard.

SAFETY. Mints its own throwaway database ``test_<pid>_<uuid4>`` under the
``lore_test`` namespace on the spike-surreal TEST store (``ws://127.0.0.1:18000``),
and drops it on exit. NEVER touches production (lore-surreal :18500). Prints its own
db name. Referenced ``agent`` + ``message`` endpoints ARE created as real rows
(``to`` is ENFORCED — RELATE needs existing endpoints, store §4).

Run: ``uv run python scripts/probe_drain_read_63b_ii_b.py``
Exit 0 iff every definite-shape expectation + every positive control held; non-zero
on any surprise. The LEG-C verdict is DIAGNOSTIC (printed, never an exit gate).
"""

from __future__ import annotations

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from typing import Any

# REUSE the ii-a probe's harness (same ``scripts/`` dir → on sys.path when run as a
# file; insert defensively so ``uv run`` cannot surprise us). Its plan-walker,
# ``explain``/``_require`` harness, connect constants, ``_create_message``,
# ``_read_fragment`` and member ``_SUBJECT`` are the SHIPPED ii-a instrument — not
# re-cloned here (store-law C1: do not fork a throwaway walker).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from loremaster.messages import MessageBodyError, MessageLedger  # noqa: E402
from loremaster.store._txn import bootstrap_session, signin_credentials  # noqa: E402
from loremaster.store.surreal_schema import (  # noqa: E402
    MESSAGE_BODY_MAX_CHARS,
    MESSAGE_TABLE,
    TO_RELATION,
    generate_agent_ddl,
    generate_message_ddl,
    generate_principal_ddl,
)
from lorerunes.pdp import AGENT_TABLE  # noqa: E402
from probe_read_filter_63 import (  # noqa: E402 — deferred until sys.path is primed
    NAMESPACE,
    PASSWORD,
    URL,
    USER,
    ProbeReport,
    _apply_ddl,
    _create_message,
    _read_fragment,
    explain,
    unique_database,
)
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal, RecordID  # noqa: E402

# An over-cap ``ack_note``: one char past the DDL ASSERT bound. The bound is IMPORTED
# from production (never re-declared) so this probe cannot drift from the real cap.
_OVER_CAP_NOTE = "x" * (MESSAGE_BODY_MAX_CHARS + 1)
_BOUNDED_NOTE = "acked by probe"  # a legal, in-bound replacement note (for the ack probe)
_AT_CAP_NOTE = "y" * MESSAGE_BODY_MAX_CHARS  # the largest legal note — the writer's positive control


# --------------------------------------------------------------------------- #
# Raw observation helpers — LEG B/C read the EXACT per-statement engine status via
# ``query_raw`` (store §3: ``execute_transaction`` launders the text; a probe must
# not). Normalise both plausible SDK envelope shapes.
# --------------------------------------------------------------------------- #


def _per_statement(raw: Any) -> list[dict[str, Any]]:
    """The per-statement result list from a ``query_raw`` response (dict-with-'result'
    or a bare list — handled defensively so a shape surprise never masks the result)."""
    if isinstance(raw, dict):
        results = raw.get("result")
        if isinstance(results, list):
            return [row for row in results if isinstance(row, dict)]
    if isinstance(raw, list):
        return [row for row in raw if isinstance(row, dict)]
    return []


def _statuses(raw: Any) -> list[str]:
    return [str(row.get("status")) for row in _per_statement(raw)]


def _any_err(raw: Any) -> bool:
    return any(str(row.get("status")) == "ERR" for row in _per_statement(raw))


# An engine ASSERT error ECHOES the offending value — a 4001-char ``ack_note`` makes a
# 4000-char line — so an ERR text is clipped to this many characters, with the clipped count named.
_ERR_TEXT_MAX_CHARS = 300


def _err_texts(raw: Any) -> list[str]:
    texts = [
        str(row.get("result"))
        for row in _per_statement(raw)
        if str(row.get("status")) == "ERR"
    ]
    return [
        text if len(text) <= _ERR_TEXT_MAX_CHARS
        else f"{text[:_ERR_TEXT_MAX_CHARS]}… [{len(text) - _ERR_TEXT_MAX_CHARS} chars clipped]"
        for text in texts
    ]


async def _query_raw(connection: Any, surql: str, params: dict[str, Any]) -> Any:
    return await connection.query_raw(surql, params)


async def _seen_state(connection: Any, agent_id: str) -> list[tuple[str, bool]]:
    """(bare message id, seen_at-IS-set) for every ``to`` edge of ``agent_id``,
    oldest by the message's seq — the ground-truth read-back the verdict rests on."""
    rows = await connection.query(
        f"SELECT in.id AS mid, (seen_at IS NOT NONE) AS seen, in.seq AS seq "
        f"FROM {TO_RELATION} WHERE out = $agent ORDER BY seq",
        {"agent": RecordID(AGENT_TABLE, agent_id)},
    )
    out: list[tuple[str, bool]] = []
    if isinstance(rows, list):
        for row in rows:
            if isinstance(row, dict):
                out.append((str(row.get("mid")), bool(row.get("seen"))))
    return out


async def _ack_note_of(connection: Any, agent_id: str, message_id: str) -> Any:
    rows = await connection.query(
        f"SELECT ack_note, (acked_at IS NOT NONE) AS acked FROM {TO_RELATION} "
        f"WHERE out = $agent AND in = $msg",
        {"agent": RecordID(AGENT_TABLE, agent_id), "msg": RecordID(MESSAGE_TABLE, message_id)},
    )
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        return rows[0]
    return None


# --------------------------------------------------------------------------- #
# Row creation — real ``agent`` + ``message`` endpoints (``to`` is ENFORCED) + the
# bound-RecordID RELATE (store §4/§7). ``_create_message`` is REUSED from ii-a.
# --------------------------------------------------------------------------- #


async def _create_agent(connection: Any, agent_id: str, *, name: str) -> None:
    """A real ``agent`` row (the ``to`` edge's ENFORCED ``OUT`` endpoint). Sets only
    the non-``option`` required fields the SCHEMAFULL ``agent`` table demands."""
    await connection.query(
        f"CREATE type::record('{AGENT_TABLE}', $id) CONTENT {{ "
        f"name: $name, session: $sess, role: 'probe', status: 'active', "
        f"registered_at: time::now(), heartbeat_at: time::now() }}",
        {"id": agent_id, "name": name, "sess": "sess1"},
    )


async def _relate(
    connection: Any,
    message_id: str,
    agent_id: str,
    *,
    seen_at: datetime | None = None,
    acked_at: datetime | None = None,
    ack_note: str | None = None,
) -> None:
    """One ``message->to->agent`` delivery edge, bound-RecordID endpoints (store §4).
    Mirrors production's fan-out RELATE (messages.py) — ``session`` + ``created_at``
    always; ``seen_at``/``acked_at``/``ack_note`` optional (omitted ⇒ NONE)."""
    sets = ["session = $sess", "created_at = time::now()"]
    params: dict[str, Any] = {
        "msg": RecordID(MESSAGE_TABLE, message_id),
        "agent": RecordID(AGENT_TABLE, agent_id),
        "sess": "sess1",
    }
    if seen_at is not None:
        sets.append("seen_at = $seen")
        params["seen"] = seen_at
    if acked_at is not None:
        sets.append("acked_at = $acked")
        params["acked"] = acked_at
    if ack_note is not None:
        sets.append("ack_note = $note")
        params["note"] = ack_note
    await connection.query(
        f"RELATE $msg->{TO_RELATION}->$agent SET " + ", ".join(sets), params
    )


# --------------------------------------------------------------------------- #
# Schema: full CURRENT slice (principal, agent, message[+to current+governed]).
# --------------------------------------------------------------------------- #


async def _setup_current_schema(connection: Any) -> None:
    await _apply_ddl(connection, generate_principal_ddl())
    await _apply_ddl(connection, generate_agent_ddl())
    await _apply_ddl(connection, generate_message_ddl())


async def _land_pre_bound_world(connection: Any) -> None:
    """Simulate the PRE-BOUND world: OVERWRITE ``to.ack_note`` with NO ASSERT ("BEFORE ack_note was
    bounded") — how a #131 legacy over-cap edge came to exist. The definition is the SHARED
    ``unbounded_to_ack_note_ddl`` (ONE IMPLEMENTATION with
    ``test_comms_schema.py::TestALegacyOverCapNoteCannotDenyADrain``). Imported HERE because
    ``_governed_contract`` is importable only once ``probe_read_filter_63`` has put
    ``loremaster/tests`` on sys.path (a module-level import would be re-sorted above it)."""
    from _governed_contract import unbounded_to_ack_note_ddl

    await _apply_ddl(connection, unbounded_to_ack_note_ddl())


async def _land_deployed_bound(connection: Any) -> None:
    """Land the DEPLOYED asserted ``to.ack_note`` over the dirty edges — the store as production
    holds it before the ii-b image boots. Existing rows are NOT retro-validated (store §1.4): the
    dirty edges persist, now write-poisoned. The definition is the SHARED HAND-CAPTURED
    ``frozen_asserted_to_ack_note_ddl`` (literal 4000 — what production froze, never the live cap);
    imported HERE for the same sys.path reason as :func:`_land_pre_bound_world`."""
    from _governed_contract import frozen_asserted_to_ack_note_ddl

    await _apply_ddl(connection, frozen_asserted_to_ack_note_ddl())


async def _migrate_to_current(connection: Any) -> None:
    """THE MIGRATION: re-apply the REAL current DDL (``generate_message_ddl`` — the
    exact slice ``MessageLedger.ensure_ready`` applies at every deploy). Its
    ``DEFINE FIELD OVERWRITE ack_note`` is a FULL REPLACE (store §1.2) with NO ASSERT since
    63b-ii-b, so it must DROP the deployed bound. Existing rows are NOT touched (store §1.4)
    — the dirty edges keep their over-cap notes."""
    await _apply_ddl(connection, generate_message_ddl())


# --------------------------------------------------------------------------- #
# Seeding. Visible = admitted by the member _SUBJECT (agent-private / owner alice /
# owner_agent ag_a — the ii-a P4 admitted shape); excluded = keep:k9 / carol / ag_c.
# --------------------------------------------------------------------------- #

# recipient agents (one per LEG-C scenario, so a full-window drain isolates cleanly)
_R_DENIAL = "rdenial"      # [md_dirty(overcap,unseen), md_good(unseen)] — the hazard
_R_CLEAN = "rclean"        # [mc_g1, mc_g2] all good, unseen — LEG-B + C positive control
_R_OUTSIDE = "routside"    # [mo_dirty(overcap, ALREADY seen), mo_good(unseen)] — control
_R_ACK = "rack"            # [ma_dirty(overcap, unacked, unseen)] — the ack probe
_R_INVIS = "rinvis"        # [mi_dirty(overcap, INVISIBLE), mi_good] — visible-bounding insight
_R_WRITER = "rwriter"      # [m_ap(clean, unacked)] — the writer C-control (MessageLedger.ack)
_SENDER = "agsender"       # a real agent for message.sender links


async def _seed(connection: Any) -> None:
    # agents (endpoints) ------------------------------------------------------
    for agent_id in (_R_DENIAL, _R_CLEAN, _R_OUTSIDE, _R_ACK, _R_INVIS, _R_WRITER, _SENDER):
        await _create_agent(connection, agent_id, name=agent_id)

    # messages ---------------------------------------------------------------
    # visible (admitted): scope=agent-private, owner_principal=alice, owner_agent=ag_a
    visible = dict(scope="agent-private", owner_principal="alice", owner_agent="ag_a")
    seq = 0
    for mid in (
        "md_dirty", "md_good", "mc_g1", "mc_g2", "mo_dirty", "mo_good",
        "ma_dirty", "mi_good", "m_ap",
    ):
        seq += 1
        await _create_message(connection, mid, seq=seq, sender=_SENDER, **visible)
    # excluded (read_filter must NOT admit): scope=keep:k9, owner carol/ag_c
    for mid in ("mi_dirty", "m_excluded"):
        seq += 1
        await _create_message(
            connection, mid, seq=seq, sender=_SENDER,
            scope="keep:k9", owner_principal="carol", owner_agent="ag_c",
        )
    # a NONE-governed legacy message (both option<> columns unset) — a read_filter row.
    seq += 1
    await _create_message(connection, "m_legacy", seq=seq, sender=_SENDER)

    # CLEAN edges (current schema, no ack_note, unseen) — the positive controls.
    await _relate(connection, "mc_g1", _R_CLEAN)
    await _relate(connection, "mc_g2", _R_CLEAN)
    # The writer C-control's edge: clean + unacked, so ``MessageLedger.ack`` has a real edge to win.
    await _relate(connection, "m_ap", _R_WRITER)

    # --- the #131 dirty-store dance: downgrade → write dirty → migrate --------
    await _land_pre_bound_world(connection)
    # DENIAL window: an over-cap dirty edge + a good edge, BOTH unseen.
    await _relate(connection, "md_dirty", _R_DENIAL, ack_note=_OVER_CAP_NOTE)
    await _relate(connection, "md_good", _R_DENIAL)
    # OUTSIDE-window control: the over-cap dirty edge is ALREADY seen (a past stamp),
    # a good edge unseen. drain's ``seen_at IS NONE`` must exclude the dirty one.
    past = datetime.now(UTC) - timedelta(hours=1)
    await _relate(connection, "mo_dirty", _R_OUTSIDE, seen_at=past, ack_note=_OVER_CAP_NOTE)
    await _relate(connection, "mo_good", _R_OUTSIDE)
    # ACK probe: an over-cap dirty edge, unseen AND unacked.
    await _relate(connection, "ma_dirty", _R_ACK, ack_note=_OVER_CAP_NOTE)
    # VISIBLE-BOUNDING insight: an over-cap dirty edge whose MESSAGE is INVISIBLE to
    # the reader + a visible good edge — both unseen.
    await _relate(connection, "mi_dirty", _R_INVIS, ack_note=_OVER_CAP_NOTE)
    await _relate(connection, "mi_good", _R_INVIS)
    # Production's shape over the dirty edges; ``probe`` runs C0 against it, THEN migrates.
    await _land_deployed_bound(connection)


# --------------------------------------------------------------------------- #
# One-txn Reading-B drain — the ruled §4.B shape (brief LEG B).
# --------------------------------------------------------------------------- #

_VISIBLE_PROJECTION = "id, scope, owner_principal, owner_agent"


def _reading_b_txn(msg_fragment: str) -> str:
    """The ruled §4.B one-txn drain: window edges → visible messages (id IN
    edges.in AND read_filter) → stamp the edges of the VISIBLE set → RETURN visible.
    ``$edges.in`` / ``$visible.id`` pluck the array of link/id values (SurrealQL)."""
    return (
        "BEGIN;\n"
        f"LET $edges = (SELECT in, in.seq AS seq FROM {TO_RELATION} "
        "WHERE out = $me AND seen_at IS NONE ORDER BY seq LIMIT $n);\n"
        f"LET $visible = (SELECT {_VISIBLE_PROJECTION} FROM {MESSAGE_TABLE} "
        f"WHERE id IN $edges.in AND ({msg_fragment}));\n"
        f"UPDATE {TO_RELATION} SET seen_at = $t "
        "WHERE out = $me AND in IN $visible.id AND seen_at IS NONE RETURN AFTER;\n"
        "RETURN $visible;\n"
        "COMMIT;\n"
    )


# --------------------------------------------------------------------------- #
# Probe body
# --------------------------------------------------------------------------- #


async def _deployed_world_control(
    connection: Any, report: ProbeReport, findings: dict[str, Any]
) -> None:
    """C0 — INSTRUMENT CONTROL under the DEPLOYED ``to.ack_note`` bound (run BEFORE the migration):
    drain's standalone UPDATE over the denial window [md_dirty(overcap), md_good] must ABORT with
    NOTHING stamped. Without it, a GRACEFUL LEG-C verdict after the migration could be an instrument
    that cannot see the abort, not a fixed hazard. An aborted UPDATE stamps nothing, so LEG C's C1/C2
    then measure the SAME untouched window under HEAD's DDL."""
    print("\n" + "=" * 78)
    print("C0 — DD-3.c under the DEPLOYED to.ack_note bound (instrument control, pre-migration)")
    print("=" * 78)
    denial_ids = [RecordID(MESSAGE_TABLE, "md_dirty"), RecordID(MESSAGE_TABLE, "md_good")]
    c0_raw = await _query_raw(
        connection,
        f"UPDATE {TO_RELATION} SET seen_at = $t "
        "WHERE out = $me AND in IN $ids AND seen_at IS NONE RETURN AFTER",
        {"t": datetime.now(UTC), "me": RecordID(AGENT_TABLE, _R_DENIAL), "ids": denial_ids},
    )
    c0_err = _any_err(c0_raw)
    c0_after = await _seen_state(connection, _R_DENIAL)
    nothing_stamped = bool(c0_after) and not any(seen for _, seen in c0_after)
    print(f"  statuses={_statuses(c0_raw)} errored={c0_err}")
    print(f"  ERR text: {_err_texts(c0_raw)}")
    print(f"  seen-state after (mid, seen): {c0_after}")
    findings["C0_deployed_aborted"] = c0_err and nothing_stamped
    findings["C0_err"] = _err_texts(c0_raw)
    if not (c0_err and nothing_stamped):
        report.surprises.append(
            "C0 FAILED — under the DEPLOYED to.ack_note bound the drain UPDATE over the dirty window "
            f"did not abort with nothing stamped (errored={c0_err}, after={c0_after}). The probe cannot "
            "SEE the DD-3.c abort, so a GRACEFUL LEG-C verdict would be a false clear."
        )


async def _ack_writer_control(
    connection: Any, database: str, report: ProbeReport, findings: dict[str, Any]
) -> None:
    """C-CONTROL, at the bound's HOME since 63b-ii-b (§3 R1; R16 names ``MessageLedger.ack`` the
    ONE ``to.ack_note`` writer): ``ack`` REFUSES an over-cap note with NOTHING written to the edge,
    then ACCEPTS an at-cap note on the same edge (positive control: the refusal is about the length,
    not a writer that refuses everything). Driven through the REAL ledger, never a copy of its check."""
    seq_of_m_ap = await connection.query(
        f"SELECT seq FROM {MESSAGE_TABLE} WHERE id = $mid", {"mid": RecordID(MESSAGE_TABLE, "m_ap")}
    )
    seq = int(seq_of_m_ap[0]["seq"])
    ledger = MessageLedger(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=SecretStr(PASSWORD)
    )
    refused = False
    accepted_count = 0
    try:
        try:
            await ledger.ack(agent_id=_R_WRITER, seqs=[seq], note=_OVER_CAP_NOTE)
        except MessageBodyError as error:
            refused = True
            print(f"  [C-control writer] ack(note={len(_OVER_CAP_NOTE)} chars) REFUSED: {error}")
        after_refusal = await _ack_note_of(connection, _R_WRITER, "m_ap")
        result = await ledger.ack(agent_id=_R_WRITER, seqs=[seq], note=_AT_CAP_NOTE)
        accepted_count = result.acked_count
    finally:
        await ledger.close()
    after_accept = await _ack_note_of(connection, _R_WRITER, "m_ap")
    nothing_written = bool(after_refusal) and not after_refusal.get("acked") and (
        after_refusal.get("ack_note") is None
    )
    at_cap_landed = (
        accepted_count == 1
        and bool(after_accept)
        and len(str(after_accept.get("ack_note") or "")) == MESSAGE_BODY_MAX_CHARS
    )
    print(f"      edge after refusal: acked={after_refusal and after_refusal.get('acked')} "
          f"ack_note={after_refusal and after_refusal.get('ack_note')!r}")
    print(f"      at-cap ack ({MESSAGE_BODY_MAX_CHARS} chars): acked_count={accepted_count} "
          f"stored-note-len={len(str((after_accept or {}).get('ack_note') or ''))}")
    held = refused and nothing_written and at_cap_landed
    findings["C_writer_refused"] = held
    if not held:
        report.surprises.append(
            "LEG C C-CONTROL FAILED — the ONE ack_note writer MessageLedger.ack did not refuse an "
            f"over-cap note with nothing written, or did not accept an at-cap one (refused={refused}, "
            f"nothing-written={nothing_written}, at-cap landed={at_cap_landed}). 63b-ii-b moved the bound "
            "into this writer: if it does not hold, that is a PRODUCTION defect, and the dirty edge is "
            "not genuinely non-conformant, so the LEG-C verdict is INVALID (a false clear)."
        )


async def probe(connection: Any, database: str) -> tuple[ProbeReport, dict[str, Any]]:  # noqa: PLR0915 — a linear diagnostic probe; splitting it hides the leg sequence (ii-a probe precedent)
    report = ProbeReport()
    findings: dict[str, Any] = {}
    # C0 runs against the DEPLOYED bound ``_seed`` left in place; then THE MIGRATION to HEAD's DDL,
    # under which every leg below runs.
    await _deployed_world_control(connection, report, findings)
    await _migrate_to_current(connection)
    msg_fragment, msg_params = _read_fragment(MESSAGE_TABLE)
    print("\n=== REAL EMITTER READ FRAGMENT (authorize_filter member READ, message) ===")
    print(f"  fragment: {msg_fragment}")
    print(f"  params  : {msg_params}")

    # ===================================================================== LEG A
    print("\n" + "=" * 78)
    print("LEG A — EXPLAIN plans for ii-b's composed read shapes")
    print("=" * 78)

    # -- integrity controls: walker sees IndexScan AND TableScan on BOTH tables --
    a_ctrl_to_idx = await explain(
        report, connection, label="CTRL to out=+seen (drain index → IndexScan)",
        table=TO_RELATION, where="out = $agent AND seen_at IS NONE",
        params={"agent": RecordID(AGENT_TABLE, _R_DENIAL)},
    )
    _require_local(
        report, a_ctrl_to_idx, "IndexScan",
        "the to (out, seen_at) drain index must IndexScan or the walker is blind on `to`.",
    )
    a_ctrl_to_ts = await explain(
        report, connection, label="CTRL to session= (unindexed → TableScan)",
        table=TO_RELATION, where="session = $s", params={"s": "sess1"},
    )
    _require_local(
        report, a_ctrl_to_ts, "TableScan",
        "the walker cannot SEE a TableScan on an unindexed `to` column — blind.",
    )
    a_ctrl_msg_ts = await explain(
        report, connection, label="CTRL message body= (unindexed → TableScan)",
        table=MESSAGE_TABLE, where="body = $b", params={"b": "body md_good"},
    )
    _require_local(
        report, a_ctrl_msg_ts, "TableScan",
        "the walker cannot SEE a TableScan on an unindexed `message` column — blind.",
    )

    # A1 — the drain window SELECT (also the `await` peek shape; both = drain SELECT)
    a1 = await explain(
        report, connection, label="A1 drain window: to WHERE out=$agent AND seen_at IS NONE",
        table=TO_RELATION, where="out = $agent AND seen_at IS NONE",
        params={"agent": RecordID(AGENT_TABLE, _R_DENIAL)}, dump=True,
    )
    _require_local(
        report, a1, "IndexScan",
        "the drain/await window SELECT must be served by the (out, seen_at) index.",
    )
    findings["A1"] = a1.classification

    # A2 — the bare message read_filter (re-confirm ii-a P3 on this db)
    a2 = await explain(
        report, connection, label="A2 message bare READ fragment (member, 2 keeps)",
        table=MESSAGE_TABLE, where=msg_fragment, params=dict(msg_params), dump=True,
    )
    _require_local(
        report, a2, "IndexScan",
        "the emitted flat-OR read_filter must be index-served (3.2 UnionIndexScan, 3.3 BitmapOr) "
        "with NO message TableScan (ii-a P3).",
    )
    findings["A2"] = a2.classification

    # A3 — the §4.3 step-2 inbox read: id IN $ids AND (read_filter)  [REPORT]
    inbox_ids = [RecordID(MESSAGE_TABLE, "md_good"), RecordID(MESSAGE_TABLE, "m_excluded")]
    a3 = await explain(
        report, connection, label="A3 message id IN $ids AND (READ fragment)",
        table=MESSAGE_TABLE, where=f"id IN $ids AND ({msg_fragment})",
        params={"ids": inbox_ids, **msg_params}, dump=True, report_only=True,
    )
    findings["A3"] = a3.classification

    # A4 — story: task_id = $t AND (read_filter)  [REPORT; task_id is UNINDEXED]
    a4 = await explain(
        report, connection, label="A4 story: message task_id=$t AND (READ fragment)",
        table=MESSAGE_TABLE, where=f"task_id = $t AND ({msg_fragment})",
        params={"t": "task-1", **msg_params}, dump=True, report_only=True,
    )
    findings["A4"] = a4.classification

    # A5 — rollup message leg: created_at > $since AND (read_filter)  [REPORT; unindexed]
    a5 = await explain(
        report, connection, label="A5 rollup: message created_at>$since AND (READ fragment)",
        table=MESSAGE_TABLE, where=f"created_at > $since AND ({msg_fragment})",
        params={"since": datetime.now(UTC) - timedelta(days=1), **msg_params},
        dump=True, report_only=True,
    )
    findings["A5"] = a5.classification

    # ===================================================================== LEG B
    print("\n" + "=" * 78)
    print("LEG B — the §4.B Reading-B one-txn drain (positive control: CLEAN store)")
    print("=" * 78)
    txn = _reading_b_txn(msg_fragment)
    print("  one-txn shape:\n   " + txn.rstrip().replace("\n", "\n   "))
    clean_params = {
        "me": RecordID(AGENT_TABLE, _R_CLEAN),
        "n": 50,
        "t": datetime.now(UTC),
        **msg_params,
    }
    clean_raw = await _query_raw(connection, txn, clean_params)
    print(f"  per-statement statuses: {_statuses(clean_raw)}")
    if _any_err(clean_raw):
        print(f"  ERR texts: {_err_texts(clean_raw)}")
    clean_after = await _seen_state(connection, _R_CLEAN)
    print(f"  seen-state after (mid, seen): {clean_after}")
    findings["B_clean_statuses"] = _statuses(clean_raw)
    findings["B_clean_after"] = clean_after
    clean_all_seen = clean_after and all(seen for _, seen in clean_after)
    if _any_err(clean_raw) or not clean_all_seen:
        report.surprises.append(
            "LEG B positive control FAILED — the Reading-B one-txn drain over a CLEAN "
            f"store errored ({_err_texts(clean_raw)}) or did not stamp every good edge "
            f"({clean_after}). The proposed one-txn shape is not sound even on a clean store."
        )

    # ===================================================================== LEG C
    print("\n" + "=" * 78)
    print("LEG C — DD-3.c drain-UPDATE dirty-store hazard (DIAGNOSTIC)")
    print("=" * 78)
    # Derived from HEAD's emitter, never restated: since 63b-ii-b this carries NO ASSERT. The shared
    # DDL reader is imported HERE: ``_governed_contract`` is importable only once
    # ``probe_read_filter_63`` has put ``loremaster/tests`` on sys.path, and a module-level import
    # would be re-sorted above that one.
    from _governed_contract import field_statement

    print(f"  HEAD to.ack_note definition: "
          f"{field_statement(generate_message_ddl(), TO_RELATION, 'ack_note')}")
    print(f"  the {MESSAGE_BODY_MAX_CHARS}-char bound lives in MessageLedger.ack (_reject_oversize_note).")

    print("\n  [C-control] the ONE writer MessageLedger.ack against an over-cap / at-cap note:")
    await _ack_writer_control(connection, database, report, findings)

    # STORE FACT (DIAGNOSTIC, not a gate): a raw over-cap RELATE that bypasses the writer is
    # ACCEPTED under HEAD's DDL — the store bound was dropped by design (63b-ii-b §3 R1).
    print("\n  [store fact] raw over-cap RELATE under HEAD DDL (bypassing the writer):")
    ctrl_raw = await _query_raw(
        connection,
        f"RELATE $msg->{TO_RELATION}->$agent SET session=$sess, created_at=time::now(), "
        "ack_note=$note",
        {
            "msg": RecordID(MESSAGE_TABLE, "mc_g1"),  # a distinct pair (mc_g1 not yet → rclean? it is)
            "agent": RecordID(AGENT_TABLE, _R_ACK),
            "sess": "sess1",
            "note": _OVER_CAP_NOTE,
        },
    )
    store_accepted = not _any_err(ctrl_raw)
    print(f"      statuses={_statuses(ctrl_raw)} accepted={store_accepted} "
          "(expected True: no store bound at HEAD)")
    if not store_accepted:
        print(f"      reject text: {_err_texts(ctrl_raw)}")
    findings["C_store_accepts_overcap"] = store_accepted

    # C1 — STANDALONE drain UPDATE over [md_dirty(overcap), md_good], both unseen.
    print("\n  [C1] standalone drain UPDATE over [md_dirty(overcap,unseen), md_good(unseen)]:")
    denial_ids = [RecordID(MESSAGE_TABLE, "md_dirty"), RecordID(MESSAGE_TABLE, "md_good")]
    c1_raw = await _query_raw(
        connection,
        f"UPDATE {TO_RELATION} SET seen_at = $t "
        "WHERE out = $me AND in IN $ids AND seen_at IS NONE RETURN AFTER",
        {"t": datetime.now(UTC), "me": RecordID(AGENT_TABLE, _R_DENIAL), "ids": denial_ids},
    )
    c1_err = _any_err(c1_raw)
    print(f"      statuses={_statuses(c1_raw)} errored={c1_err}")
    if c1_err:
        print(f"      ERR text: {_err_texts(c1_raw)}")
    c1_after = await _seen_state(connection, _R_DENIAL)
    print(f"      seen-state after (mid, seen): {c1_after}")
    findings["C1_errored"] = c1_err
    findings["C1_err"] = _err_texts(c1_raw)
    findings["C1_after"] = c1_after

    # C2 — the ONE-TXN Reading-B drain over the SAME denial window (dirty IS visible).
    print("\n  [C2] one-txn Reading-B drain over the denial window (md_dirty visible):")
    c2_params = {
        "me": RecordID(AGENT_TABLE, _R_DENIAL),
        "n": 50,
        "t": datetime.now(UTC),
        **msg_params,
    }
    c2_raw = await _query_raw(connection, txn, c2_params)
    c2_err = _any_err(c2_raw)
    print(f"      per-statement statuses={_statuses(c2_raw)} errored={c2_err}")
    if c2_err:
        print(f"      ERR text: {_err_texts(c2_raw)}")
    c2_after = await _seen_state(connection, _R_DENIAL)
    print(f"      seen-state after (mid, seen): {c2_after}")
    md_good_stamped = any(mid.endswith("md_good") and seen for mid, seen in c2_after)
    findings["C2_errored"] = c2_err
    findings["C2_err"] = _err_texts(c2_raw)
    findings["C2_after"] = c2_after
    findings["C2_md_good_stamped"] = md_good_stamped

    # C-positive-control-1: the CLEAN store one-txn already stamped (LEG B) — reuse.
    # C-positive-control-2: dirty edge OUTSIDE the window (already seen) → drain unaffected.
    print("\n  [C-control outside-window] full drain over routside "
          "(mo_dirty overcap ALREADY seen, mo_good unseen):")
    outside_raw = await _query_raw(
        connection,
        f"UPDATE {TO_RELATION} SET seen_at = $t "
        "WHERE out = $me AND seen_at IS NONE RETURN AFTER",
        {"t": datetime.now(UTC), "me": RecordID(AGENT_TABLE, _R_OUTSIDE)},
    )
    outside_err = _any_err(outside_raw)
    outside_after = await _seen_state(connection, _R_OUTSIDE)
    print(f"      statuses={_statuses(outside_raw)} errored={outside_err}")
    print(f"      seen-state after (mid, seen): {outside_after}")
    mo_good_stamped = any(mid.endswith("mo_good") and seen for mid, seen in outside_after)
    findings["C_outside_errored"] = outside_err
    findings["C_outside_after"] = outside_after
    if outside_err or not mo_good_stamped:
        report.surprises.append(
            "LEG C outside-window control FAILED — a drain that EXCLUDES the dirty edge "
            f"(seen_at IS NONE filter) still errored ({_err_texts(outside_raw)}) or did not "
            f"stamp the good edge ({outside_after}). The hazard is NOT window-specific as "
            "expected — investigate."
        )

    # C3 — ack UPDATE over the over-cap unacked edge: ack REPLACES ack_note with a
    # bounded $note. Built to ask whether the SET lands (new value conforms) or the ASSERT
    # fires on the OLD value first; under HEAD's ASSERT-free ack_note it measures only that
    # the replacement lands over a legacy over-cap edge.
    print("\n  [C3] ack UPDATE over ma_dirty (overcap, unacked): SET acked_at + a BOUNDED ack_note:")
    c3_raw = await _query_raw(
        connection,
        f"UPDATE {TO_RELATION} SET acked_at = $t, ack_note = $note "
        "WHERE acked_at IS NONE AND out = $me AND in IN $ids",
        {
            "t": datetime.now(UTC),
            "note": _BOUNDED_NOTE,
            "me": RecordID(AGENT_TABLE, _R_ACK),
            "ids": [RecordID(MESSAGE_TABLE, "ma_dirty")],
        },
    )
    c3_err = _any_err(c3_raw)
    c3_state = await _ack_note_of(connection, _R_ACK, "ma_dirty")
    print(f"      statuses={_statuses(c3_raw)} errored={c3_err}")
    if c3_err:
        print(f"      ERR text: {_err_texts(c3_raw)}")
    print(f"      ma_dirty ack state after: {c3_state}")
    findings["C3_errored"] = c3_err
    findings["C3_err"] = _err_texts(c3_raw)
    findings["C3_state"] = c3_state

    # C4 — the VISIBLE-BOUNDING insight (informs the mitigation): a Reading-B one-txn
    # over rinvis, where the dirty edge's MESSAGE is INVISIBLE to the reader. The stamp
    # is bounded by $visible.id — so an invisible dirty edge is NOT touched.
    print("\n  [C4] Reading-B one-txn over rinvis (mi_dirty overcap but INVISIBLE, mi_good visible):")
    c4_params = {
        "me": RecordID(AGENT_TABLE, _R_INVIS),
        "n": 50,
        "t": datetime.now(UTC),
        **msg_params,
    }
    c4_raw = await _query_raw(connection, txn, c4_params)
    c4_err = _any_err(c4_raw)
    c4_after = await _seen_state(connection, _R_INVIS)
    print(f"      per-statement statuses={_statuses(c4_raw)} errored={c4_err}")
    if c4_err:
        print(f"      ERR text: {_err_texts(c4_raw)}")
    print(f"      seen-state after (mid, seen): {c4_after}")
    findings["C4_errored"] = c4_err
    findings["C4_after"] = c4_after

    return report, findings


def _require_local(report: ProbeReport, observation: Any, want: str, why: str) -> None:
    if observation.classification != want:
        report.surprises.append(
            f"{observation.label}: EXPECTED {want}, got {observation.classification}. {why} "
            f"operators={observation.operators} :: {observation.statement}"
        )


def _leg_c_verdict(findings: dict[str, Any]) -> str:
    """The ONE diagnostic verdict, derived from the OBSERVED C1/C2 behaviour — valid only when
    the writer control (the dirty edge is non-conformant) AND C0 (the abort is visible) held."""
    if not findings.get("C_writer_refused"):
        return "DD-3.c: N/A(the ack writer did not enforce the cap — probe invalid, see surprises)"
    if not findings.get("C0_deployed_aborted"):
        return "DD-3.c: N/A(C0 could not see the abort under the deployed bound — see surprises)"
    c1_err = bool(findings.get("C1_errored"))
    c2_err = bool(findings.get("C2_errored"))
    c2_good_stamped = bool(findings.get("C2_md_good_stamped"))
    if (c1_err or c2_err) and not c2_good_stamped:
        return "DD-3.c: ABORTS-WHOLE"
    if not c1_err and not c2_err and c2_good_stamped:
        return "DD-3.c: GRACEFUL(good stamped, bad skipped)"
    return "DD-3.c: MIXED(see C1/C2 detail — standalone vs one-txn differ)"


def _print_verdict(report: ProbeReport, findings: dict[str, Any]) -> None:
    print("\n" + "=" * 78)
    print("VERDICTS")
    print("=" * 78)
    print("\n-- LEG A (composed read plans) --")
    for tag, note in (
        ("A1", "drain/await window SELECT (to out+seen_at) — REQUIRE IndexScan"),
        ("A2", "message bare READ fragment — REQUIRE IndexScan"),
        ("A3", "message id IN $ids AND (fragment) — REPORT"),
        ("A4", "story task_id=$t AND (fragment) — REPORT (task_id unindexed)"),
        ("A5", "rollup created_at>$since AND (fragment) — REPORT (created_at unindexed)"),
    ):
        print(f"  {tag}: {findings.get(tag, 'MISSING'):<20} {note}")

    print("\n-- LEG B (Reading-B one-txn, clean store) --")
    print(f"  statuses={findings.get('B_clean_statuses')}  after={findings.get('B_clean_after')}")

    print("\n-- LEG C (DD-3.c dirty-store drain-UPDATE) --")
    print(f"  C0 deployed bound: drain over dirty window aborted, nothing stamped: "
          f"{findings.get('C0_deployed_aborted')}")
    print(f"     err: {findings.get('C0_err')}")
    print(f"  C-control (cap real: MessageLedger.ack refuses over-cap, accepts at-cap): "
          f"{findings.get('C_writer_refused')}")
    print(f"  store fact (raw over-cap RELATE accepted under HEAD DDL): "
          f"{findings.get('C_store_accepts_overcap')}")
    print(f"  C1 standalone drain UPDATE errored: {findings.get('C1_errored')}")
    print(f"     err: {findings.get('C1_err')}")
    print(f"     after (denial window): {findings.get('C1_after')}")
    print(f"  C2 one-txn drain errored: {findings.get('C2_errored')}  "
          f"md_good stamped: {findings.get('C2_md_good_stamped')}")
    print(f"     err: {findings.get('C2_err')}")
    print(f"     after (denial window): {findings.get('C2_after')}")
    print(f"  C-control outside-window errored: {findings.get('C_outside_errored')}  "
          f"after: {findings.get('C_outside_after')}")
    print(f"  C3 ack UPDATE (replace over-cap with bounded note) errored: {findings.get('C3_errored')}")
    print(f"     err: {findings.get('C3_err')}")
    print(f"     ma_dirty after: {findings.get('C3_state')}")
    print(f"  C4 visible-bounding one-txn (invisible dirty edge) errored: {findings.get('C4_errored')}")
    print(f"     after: {findings.get('C4_after')}")

    print("\n" + "=" * 78)
    print(f"LEG-C HEADLINE VERDICT: {_leg_c_verdict(findings)}")
    print("=" * 78)


async def main() -> int:
    database = unique_database()
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=SecretStr(PASSWORD)))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    print(f"probe database: {NAMESPACE}:{database}  (TEST store {URL})")
    try:
        await _setup_current_schema(connection)
        await _seed(connection)
        report, findings = await probe(connection, database)
    finally:
        try:
            await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        except Exception as error:  # noqa: BLE001 - cleanup best-effort, never masks the result
            print(f"[cleanup warning] {type(error).__name__}: {error}")
        await connection.close()

    _print_verdict(report, findings)

    print("\n=== SELF-CHECK VERDICT ===")
    if report.surprises:
        print(f"SURPRISES ({len(report.surprises)}) — a claimed clear is NOT trustworthy:")
        for surprise in report.surprises:
            print(f"  - {surprise}")
        return 1
    print("All definite-shape expectations held (LEG-A REQUIREs + walker controls);")
    print("C0 + the ack-writer control + the LEG-B / LEG-C positive controls held; the LEG-C")
    print("headline is DIAGNOSTIC above.")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
