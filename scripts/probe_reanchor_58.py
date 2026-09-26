#!/usr/bin/env python3
"""Probe: packet 58's two contract-phase questions, answered LIVE on the TEST store.

WHY (``docs/plans/v2/58-supersede-reanchor.md`` ENTRY CHECK 3 + kickoff rulings
``docs/design/2026-09-26-packet58-kickoff-rulings.md`` §1/§8, authored by ``contract-58``):

  LEG A — THE STRAND (#356), reproduced through the PUBLIC verbs at the tree this runs on:
      Y blocked_by [X]; supersede X → X'.  At a PRE-58 tree Y stays ``blocked_by [X]``, the
      ``X→blocks→Y`` edge survives, ``claim_task(Y)`` loses, and ``direct_dependents(X) == [Y]``.
      POSITIVE CONTROL: an ordinary waiter on a blocker driven to ``done`` IS claimable — so
      "Y stays blocked" is not a can-never-claim instrument.
      The leg REPORTS which world it saw (``strand`` = pre-58, ``reanchored`` = post-58) and
      fails only if it saw NEITHER (an incoherent state).

  LEG B — THE REWRITE SPELLING (§1 FLAG: *"the ``array::map`` closure with a conditional is
      UNPROBED on 3.2.4"*).  ``array::distinct(array::map(blocked_by, |$b| IF $b = $old THEN $new
      ELSE $b END))`` inside a guarded ``UPDATE … WHERE (blocked_by CONTAINS $old)`` composed
      with its ``IF array::len(…) == 0 { THROW … }`` guard, through the PRODUCTION
      ``compose`` / ``execute_transaction`` seam.  Rows: ``[a, old, b]`` → ``[a, new, b]`` (order
      kept), ``[old, old]`` → ``[new]`` (dedupe — the legacy T5 duplicate), ``[old, new]`` →
      ``[new]`` (dedupe against an already-present successor).  NEGATIVE CONTROL: the same guarded
      UPDATE aimed at a row that does NOT name ``old`` THROWs and rolls a preceding witness write
      back.  The alternative ``{ … } ELSE { … }`` block spelling is probed too and REPORTED.

  LEG C — ``DELETE blocks WHERE in = $old`` removes EVERY outgoing edge of ``old`` and NO other
      edge (the kickoff's one-statement edge retire), with a positive control that an unrelated
      edge survives.

SAFETY.  Mints a throwaway ``test_<pid>_<uuid4>`` database under ``lore_test`` on the
spike-surreal TEST store (``ws://127.0.0.1:18000``; creds from ``loremaster/tests/_surreal_harness``)
and drops it on exit.  NEVER touches production (lore-surreal :18500).  Reads use single statements;
every multi-statement write rides ``execute_transaction`` (store-ref §3).

Run: ``uv run python scripts/probe_reanchor_58.py``
Exit 0 iff every control held and every leg saw a coherent world; non-zero (LOUD) otherwise.
"""

from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import UTC, datetime
from typing import Any

from loremaster.store._txn import TxnFragment, compose, execute_transaction
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import STATUS_DONE, STATUS_IN_PROGRESS, TaskLedger

# The TEST-store credential is REUSED from an allowlisted sibling probe's ORIGIN (the hardcoded
# spike-surreal dev literal, ``test_secret_typing.py``'s adjudicated list) — this probe mints no
# SecretStr and reads no environment, so neither secret-seam scan has anything new to adjudicate.
from probe_query_complexity_07 import NAMESPACE, PASSWORD, URL, USER
from surrealdb import RecordID

PRODUCTION_PORT_MARKER = ":18500"
CREATOR = "probe-58"
DESCRIPTION = "probe_reanchor_58 fixture"

#: The rewrite spelling the kickoff §1 proposes (the load-bearing one).
REWRITE_THEN_ELSE = (
    "array::distinct(array::map(blocked_by, |$b| IF $b = $p58_old THEN $p58_new ELSE $b END))"
)
#: The block spelling, probed and REPORTED (a discovery, not a gate).
REWRITE_BLOCKS = (
    "array::distinct(array::map(blocked_by, |$b| IF $b = $p58_old { $p58_new } ELSE { $b }))"
)


def _guarded_rewrite(row_id: str, old: str, new: str, rewrite: str) -> TxnFragment:
    """The kickoff §4 shell shape for ONE re-anchor: LET-bound guarded UPDATE + THROW-on-zero."""
    return TxnFragment(
        statements=[
            (
                f"LET $p58_v = (UPDATE type::record('{TASK_TABLE}', $p58_id) SET "
                f"blocked_by = {rewrite}, updated_at = time::now() "
                f"WHERE (blocked_by CONTAINS $p58_old))"
            ),
            "IF array::len($p58_v) == 0 { THROW 'p58 guarded rewrite matched zero rows' }",
        ],
        params={"p58_id": row_id, "p58_old": old, "p58_new": new},
    )


async def _column(ledger: TaskLedger, row_id: str) -> list[str]:
    rows = await ledger._query(  # noqa: SLF001 - a probe reads the raw column
        f"SELECT blocked_by FROM type::record('{TASK_TABLE}', $id)", {"id": row_id}
    )
    return list(rows[0].get("blocked_by") or []) if rows else []


async def _edges(ledger: TaskLedger) -> set[tuple[str, str]]:
    rows = await ledger._query(  # noqa: SLF001
        f"SELECT record::id(in) AS blocker, record::id(out) AS blocked FROM {BLOCKS_RELATION}"
    )
    return {(str(row["blocker"]), str(row["blocked"])) for row in rows}


async def _run_txn(ledger: TaskLedger, fragments: list[TxnFragment]) -> BaseException | None:
    statement_text, params = compose(*fragments)
    try:
        await execute_transaction(
            statement_text,
            params,
            acquire=ledger._ensure_connection,  # noqa: SLF001
            drop=ledger._drop_connection,  # noqa: SLF001
            url=URL,
        )
    except Exception as error:  # noqa: BLE001 - the probe classifies the raise itself
        return error
    return None


async def _leg_a(ledger: TaskLedger, failures: list[str], report: list[str]) -> None:
    blocker = await ledger.create_task("X (to be superseded)", DESCRIPTION, created_by=CREATOR)
    dependent = await ledger.create_task(
        "Y blocked_by X", DESCRIPTION, blocked_by=[blocker], created_by=CREATOR
    )
    result: Any = await ledger.supersede_task(
        blocker, subject="X'", description=DESCRIPTION, created_by=CREATOR
    )
    successor = result if isinstance(result, str) else str(result.successor_id)
    column = await _column(ledger, dependent)
    edges = await _edges(ledger)
    claim = await ledger.claim_task(dependent, "probe-claimant")
    dependents_of_old = await ledger.direct_dependents(blocker)
    report.append(
        f"A: Y.blocked_by={column} edge X->Y={(blocker, dependent) in edges} "
        f"edge X'->Y={(successor, dependent) in edges} claim(Y).claimed={claim.claimed} "
        f"direct_dependents(X)={dependents_of_old}"
    )
    strand = (
        column == [blocker]
        and (blocker, dependent) in edges
        and not claim.claimed
        and dependents_of_old == [dependent]
    )
    reanchored = (
        column == [successor]
        and (successor, dependent) in edges
        and (blocker, dependent) not in edges
        and not claim.claimed
        and dependents_of_old == []
    )
    report.append(
        "A: WORLD = "
        + ("STRAND (pre-58: #356 reproduced)" if strand else "")
        + ("REANCHORED (post-58)" if reanchored else "")
        + ("" if strand or reanchored else "INCOHERENT")
    )
    if not (strand or reanchored):
        failures.append(f"A: neither the strand nor the re-anchor was observed: {report[-2]}")

    # POSITIVE CONTROL — an ordinary waiter IS freed by done.
    ordinary = await ledger.create_task("ordinary blocker", DESCRIPTION, created_by=CREATOR)
    waiter = await ledger.create_task(
        "ordinary waiter", DESCRIPTION, blocked_by=[ordinary], created_by=CREATOR
    )
    if (await ledger.claim_task(waiter, "probe-claimant")).claimed:
        failures.append("A control: the waiter was claimable while its blocker was OPEN")
    await ledger.claim_task(ordinary, "probe-worker")
    await ledger.transition(ordinary, STATUS_IN_PROGRESS, actor="probe-worker")
    await ledger.transition(ordinary, STATUS_DONE, actor="probe-worker", summary="control done")
    if not (await ledger.claim_task(waiter, "probe-claimant")).claimed:
        failures.append("A control: a waiter whose only blocker is DONE was NOT claimable")
    else:
        report.append("A control: ordinary waiter freed by done — instrument can see a win")


async def _seed(ledger: TaskLedger, row_id: str, blocked_by: list[str]) -> None:
    await ledger._query(  # noqa: SLF001 - a raw seed bypasses the pre-checks by design
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {
            "id": row_id,
            "content": {
                "subject": row_id,
                "description": DESCRIPTION,
                "status": "open",
                "blocked_by": blocked_by,
                "provenance": {"created_by": CREATOR, "events": []},
                "created_at": datetime.now(UTC),
            },
        },
    )


async def _leg_b(ledger: TaskLedger, failures: list[str], report: list[str]) -> None:
    tag = uuid.uuid4().hex[:8]
    old, new, alpha, beta = (f"b{tag}old", f"b{tag}new", f"b{tag}a", f"b{tag}b")
    for row_id in (old, new, alpha, beta):
        await _seed(ledger, row_id, [])
    cases = {
        f"b{tag}order": ([alpha, old, beta], [alpha, new, beta]),
        f"b{tag}dup": ([old, old], [new]),
        f"b{tag}already": ([old, new], [new]),
    }
    for row_id, (seeded, _want) in cases.items():
        await _seed(ledger, row_id, seeded)
    for spelling_name, rewrite in (("THEN/ELSE/END", REWRITE_THEN_ELSE), ("{ } ELSE { }", REWRITE_BLOCKS)):
        for row_id, (seeded, want) in cases.items():
            await ledger._query(  # noqa: SLF001 - reset the row between spellings
                f"UPDATE type::record('{TASK_TABLE}', $id) SET blocked_by = $v",
                {"id": row_id, "v": seeded},
            )
            error = await _run_txn(ledger, [_guarded_rewrite(row_id, old, new, rewrite)])
            got = await _column(ledger, row_id)
            ok = error is None and got == want
            report.append(
                f"B[{spelling_name}] {seeded} -> {got} (want {want}) "
                f"{'OK' if ok else 'MISMATCH'}{'' if error is None else f' raised {error!r}'}"
            )
            if spelling_name == "THEN/ELSE/END" and not ok:
                failures.append(f"B: the kickoff §1 spelling failed on {row_id}: {report[-1]}")

    # NEGATIVE CONTROL — a guarded rewrite matching ZERO rows THROWs and rolls a witness back.
    witness = f"b{tag}witness"
    control_row = f"b{tag}unrelated"
    await _seed(ledger, control_row, [alpha])
    witness_fragment = TxnFragment(
        statements=[f"CREATE type::record('{TASK_TABLE}', $p58w_id) CONTENT $p58w_content"],
        params={
            "p58w_id": witness,
            "p58w_content": {
                "subject": witness,
                "description": DESCRIPTION,
                "status": "open",
                "blocked_by": [],
                "provenance": {"created_by": CREATOR, "events": []},
                "created_at": datetime.now(UTC),
            },
        },
    )
    error = await _run_txn(
        ledger, [witness_fragment, _guarded_rewrite(control_row, old, new, REWRITE_THEN_ELSE)]
    )
    exists = bool(
        await ledger._query(  # noqa: SLF001
            f"SELECT id FROM type::record('{TASK_TABLE}', $id)", {"id": witness}
        )
    )
    report.append(
        f"B control: zero-match guarded rewrite raised={error is not None} witness_survived={exists}"
    )
    if error is None or exists:
        failures.append("B control: a zero-match guarded rewrite did NOT throw-and-roll-back")
    if await _column(ledger, control_row) != [alpha]:
        failures.append("B control: the non-matching row's blocked_by CHANGED")


async def _leg_c(ledger: TaskLedger, failures: list[str], report: list[str]) -> None:
    old = await ledger.create_task("C old", DESCRIPTION, created_by=CREATOR)
    other = await ledger.create_task("C other", DESCRIPTION, created_by=CREATOR)
    first = await ledger.create_task("C dep 1", DESCRIPTION, blocked_by=[old], created_by=CREATOR)
    second = await ledger.create_task(
        "C dep 2", DESCRIPTION, blocked_by=[old, other], created_by=CREATOR
    )
    before = await _edges(ledger)
    error = await _run_txn(
        ledger,
        [
            TxnFragment(
                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $p58c_old"],
                params={"p58c_old": RecordID(TASK_TABLE, old)},
            )
        ],
    )
    after = await _edges(ledger)
    removed = before - after
    report.append(f"C: DELETE blocks WHERE in=$old raised={error!r} removed={sorted(removed)}")
    if error is not None or removed != {(old, first), (old, second)}:
        failures.append(f"C: the one-statement retire removed {sorted(removed)}, want exactly old's two")
    if (other, second) not in after:
        failures.append("C control: an unrelated edge (other->dep2) did NOT survive the retire")


async def _main() -> int:
    if PRODUCTION_PORT_MARKER in URL:
        print(f"REFUSED: {URL} is the PRODUCTION store", file=sys.stderr)
        return 2
    database = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    ledger = TaskLedger(url=URL, namespace=NAMESPACE, database=database, user=USER, password=PASSWORD)
    failures: list[str] = []
    report: list[str] = [f"store={URL} ns={NAMESPACE} db={database}"]
    try:
        await ledger.ensure_ready()
        connection = await ledger._ensure_connection()  # noqa: SLF001 - the SDK names the engine
        report.append(f"engine={await connection.version()}")
        await _leg_a(ledger, failures, report)
        await _leg_b(ledger, failures, report)
        await _leg_c(ledger, failures, report)
    finally:
        try:
            await ledger._query(f"REMOVE DATABASE {database}")  # noqa: SLF001
        finally:
            await ledger.close()
    print("\n".join(report))
    if failures:
        print("\nFAILURES:\n" + "\n".join(failures), file=sys.stderr)
        return 1
    return 0


def main() -> int:
    return asyncio.run(_main())


if __name__ == "__main__":
    sys.exit(main())
