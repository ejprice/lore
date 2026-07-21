"""Empirical probe: sequence::nextval() as ONE statement inside a real write
transaction, under >=8-way REAL concurrency, checking for the "hot-row"
retryable-conflict marker the harness already knows about
(_surreal_harness._RETRYABLE_CONFLICT_MARKER = "can be retried").

Ad-hoc probe script (probe-sequence-1). NOT a test, NOT production code.
Targets ONLY spike-surreal (ws://127.0.0.1:18000). NEVER :18500.

This is the realistic usage shape: mint a sequence value AND use it to write a
row, atomically, while many other transactions do the same thing concurrently
against the SAME sequence.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
import traceback
import uuid
from typing import Any

from surrealdb import AsyncSurreal
from surrealdb.errors import SurrealError

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

WORKER_COUNT = 16
TXNS_PER_WORKER = 30
SEQUENCE_NAME = "txn_concurrency_probe_seq"
TABLE_NAME = "txn_concurrency_probe_row"

# Mirrors loremaster/tests/_surreal_harness.py's local copy of the marker text
# for the engine's retryable optimistic-concurrency-conflict error.
RETRYABLE_CONFLICT_MARKER = "can be retried"


def unique_database() -> str:
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


async def connect(database: str) -> AsyncSurreal:
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASSWORD})
    await connection.use(NAMESPACE, database)
    return connection


async def worker(worker_id: int, database: str, txn_count: int) -> dict[str, Any]:
    connection = await connect(database)
    minted_values: list[int] = []
    retryable_conflicts: list[str] = []
    other_errors: list[str] = []
    try:
        for i in range(txn_count):
            tag = f"{worker_id}-{i}-{uuid.uuid4().hex}"
            statement = (
                "BEGIN TRANSACTION;\n"
                f'LET $a = sequence::nextval("{SEQUENCE_NAME}");\n'
                f"CREATE {TABLE_NAME} SET seq_value = $a, tag = '{tag}';\n"
                "COMMIT TRANSACTION;\n"
            )
            try:
                await connection.query(statement)
                readback = await connection.query(
                    f"SELECT seq_value FROM {TABLE_NAME} WHERE tag = '{tag}';"
                )
                minted_values.append(readback[0]["seq_value"])
            except SurrealError as error:
                text = str(error)
                if RETRYABLE_CONFLICT_MARKER in text:
                    retryable_conflicts.append(f"{type(error).__name__}: {text}")
                else:
                    other_errors.append(f"{type(error).__name__}: {text}")
            except Exception as error:  # noqa: BLE001 - probe: surface any crash
                other_errors.append(f"UNEXPECTED {type(error).__name__}: {error}")
    finally:
        await connection.close()
    return {
        "worker_id": worker_id,
        "minted_values": minted_values,
        "retryable_conflicts": retryable_conflicts,
        "other_errors": other_errors,
    }


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")
    print(f"=== workers: {WORKER_COUNT}, txns/worker: {TXNS_PER_WORKER} ===")

    setup = await connect(database)
    await setup.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await setup.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await setup.query(f"DEFINE SEQUENCE {SEQUENCE_NAME} BATCH 1000 START 0;")
    await setup.close()

    start = time.monotonic()
    results = await asyncio.gather(
        *(worker(worker_id, database, TXNS_PER_WORKER) for worker_id in range(WORKER_COUNT))
    )
    elapsed = time.monotonic() - start

    all_values: list[int] = []
    all_retryable_conflicts: list[str] = []
    all_other_errors: list[str] = []
    for result in results:
        all_values.extend(result["minted_values"])
        all_retryable_conflicts.extend(result["retryable_conflicts"])
        all_other_errors.extend(result["other_errors"])
        print(
            f"  worker {result['worker_id']}: "
            f"{len(result['minted_values'])} committed, "
            f"{len(result['retryable_conflicts'])} retryable-conflicts, "
            f"{len(result['other_errors'])} other-errors"
        )

    distinct_values = set(all_values)
    expected_total = WORKER_COUNT * TXNS_PER_WORKER

    print("-" * 80)
    print(f"elapsed_seconds: {elapsed:.3f}")
    print(f"expected_total_txns: {expected_total}")
    print(f"committed_txns: {len(all_values)}")
    print(f"distinct_seq_values_committed: {len(distinct_values)}")
    print(f"retryable_conflicts_total: {len(all_retryable_conflicts)}")
    print(f"other_errors_total: {len(all_other_errors)}")
    if all_retryable_conflicts:
        print("first_5_retryable_conflicts:")
        for error in all_retryable_conflicts[:5]:
            print(f"  {error}")
    if all_other_errors:
        print("first_5_other_errors:")
        for error in all_other_errors[:5]:
            print(f"  {error}")
    print(f"DUPLICATES_FOUND: {len(all_values) != len(distinct_values)}")

    admin = await connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()
    print("\n=== DONE (transactional concurrency phase) ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001 - probe: surface any crash verbatim
        traceback.print_exc()
        sys.exit(1)
