"""Probe (sidecar-58-1, 2026-11-09): wall-clock of ONE supersede-shaped transaction at hub scale.

Question: under the ROW bound (TXN_ROW_HARD_CAP = 50_000, one row per un-annotated statement), a hub
supersede composes fixed + 3N statements. Does a cap-sized one finish inside the 30 s request timeout?

Shape (kickoff rulings §1): stamp shell (2) + CREATE successor (1) + DELETE blocks WHERE in = $old (1)
+ per dependent: guarded UPDATE in a LET (1) + IF .. THROW (1) + RELATE (1).
Store: the TEST store ws://127.0.0.1:18000 only; one throwaway database under lore_test, removed after.
Approximation, stated: `task` here is SCHEMALESS with no indexes (the real table is schemafull with
ASSERTs and indexes), so these timings are a LOWER bound on the real cost.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import uuid
from typing import Any

from surrealdb import AsyncSurreal, RecordID

URL = "ws://127.0.0.1:18000/rpc"
NAMESPACE = "lore_test"
SEED_BATCH = 2000
REQUEST_TIMEOUT_SECONDS = 900.0
#: PROBE_TXN_TIMEOUT=<seconds> runs the timed transaction under that request timeout (streaming ON, as
#: lore's shared factory sets it) and then re-reads the store after PROBE_SETTLE seconds on the same
#: connection: did a timed-out supersede commit anything?
TXN_TIMEOUT_SECONDS = float(os.environ.get("PROBE_TXN_TIMEOUT", "0")) or None
SETTLE_SECONDS = float(os.environ.get("PROBE_SETTLE", "75"))


async def run_one(dependents: int) -> None:
    database = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    connection = AsyncSurreal(URL, timeout=REQUEST_TIMEOUT_SECONDS, streaming=True)
    await connection.connect()
    await connection.signin({"username": "root", "password": os.environ.get("SURREAL_PASSWORD", "spikeroot")})
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await connection.use(NAMESPACE, database)
    try:
        await connection.query("DEFINE TABLE task SCHEMALESS")
        await connection.query("DEFINE TABLE blocks TYPE RELATION IN task OUT task ENFORCED")
        old, new = RecordID("task", "old"), RecordID("task", "new")
        await connection.query(
            "CREATE $old CONTENT {status: 'open', blocked_by: [], events: []}", {"old": old}
        )
        for start in range(0, dependents, SEED_BATCH):
            ids = range(start, min(start + SEED_BATCH, dependents))
            rows: list[Any] = [
                {"id": RecordID("task", f"y{i}"), "status": "open", "blocked_by": [old], "events": []}
                for i in ids
            ]
            edges: list[Any] = [{"in": old, "out": RecordID("task", f"y{i}")} for i in ids]
            await connection.query("INSERT INTO task $rows", {"rows": rows})
            await connection.query("INSERT RELATION INTO blocks $edges", {"edges": edges})

        statements = [
            "LET $stamp = (UPDATE $old SET superseded_by = $new, updated_at = time::now(), "
            "events += [$ev] WHERE (superseded_by IS NONE))",
            "IF array::len($stamp) == 0 { THROW 'stamp lost' }",
            "CREATE $new CONTENT {status: 'open', blocked_by: [], events: []}",
            "DELETE blocks WHERE in = $old",
        ]
        params: dict[str, Any] = {"old": old, "new": new, "ev": {"action": "superseded"}}
        note = {"action": "dependency_reanchored", "from": "task:old", "to": "task:new"}
        for i in range(dependents):
            params[f"y{i}"] = RecordID("task", f"y{i}")
            params[f"n{i}"] = note
            statements.append(
                f"LET $u{i} = (UPDATE $y{i} SET blocked_by = array::distinct(array::map(blocked_by, "
                f"|$b| IF $b = $old THEN $new ELSE $b END)), updated_at = time::now(), events += [$n{i}] "
                f"WHERE (blocked_by CONTAINS $old))"
            )
            statements.append(f"IF array::len($u{i}) == 0 {{ THROW 'reanchor lost' }}")
            statements.append(f"RELATE $new->blocks->$y{i}")
        text = "BEGIN;\n" + ";\n".join(statements) + ";\nCOMMIT;"

        started = time.monotonic()
        outcome = "committed"
        try:
            if TXN_TIMEOUT_SECONDS is None:
                await connection.query(text, params)
            else:
                with connection.timeout(TXN_TIMEOUT_SECONDS):
                    await connection.query(text, params)
        except Exception as error:  # noqa: BLE001 - a probe reports whatever the engine says
            outcome = f"RAISED {type(error).__name__}: {str(error)[:200]}"
        elapsed = time.monotonic() - started
        if TXN_TIMEOUT_SECONDS is not None:
            await asyncio.sleep(SETTLE_SECONDS)

        rewired = await connection.query(
            "RETURN array::len((SELECT id FROM task WHERE blocked_by CONTAINS $new))", {"new": new}
        )
        new_edges = await connection.query(
            "RETURN array::len((SELECT id FROM blocks WHERE in = $new))", {"new": new}
        )
        old_edges = await connection.query(
            "RETURN array::len((SELECT id FROM blocks WHERE in = $old))", {"old": old}
        )
        stamped = await connection.query("RETURN (SELECT VALUE superseded_by FROM ONLY $old)", {"old": old})
        print(
            f"timeout={TXN_TIMEOUT_SECONDS} settle={SETTLE_SECONDS if TXN_TIMEOUT_SECONDS else 0} "
            f"old.superseded_by={stamped} "
            f"N={dependents} statements={len(statements)} params={len(params)} text_bytes={len(text)} "
            f"elapsed_s={elapsed:.2f} outcome={outcome} rewired={rewired} new_edges={new_edges} "
            f"old_edges={old_edges} over_30s={elapsed > 30.0}",
            flush=True,
        )
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        await connection.close()


async def main() -> None:
    for dependents in [int(argument) for argument in sys.argv[1:]]:
        await run_one(dependents)


if __name__ == "__main__":
    asyncio.run(main())
