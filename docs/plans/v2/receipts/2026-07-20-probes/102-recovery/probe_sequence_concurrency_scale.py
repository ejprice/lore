"""Empirical probe: sequence::nextval() under >=8-way REAL concurrency.

Ad-hoc probe script (probe-sequence-1). NOT a test, NOT production code.
Targets ONLY spike-surreal (ws://127.0.0.1:18000) on a throwaway database.
NEVER point this at :18500 (production lore-surreal).

Each "worker" opens its OWN WebSocket connection (genuine concurrent
connections, not one connection driving concurrent coroutines) and repeatedly
calls sequence::nextval() against a SHARED, previously-DEFINE'd sequence. All
workers run truly concurrently via asyncio.gather.
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

WORKER_COUNT = 32
CALLS_PER_WORKER = 100
SEQUENCE_NAME = "concurrency_probe_seq"


def unique_database() -> str:
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


async def connect(database: str) -> AsyncSurreal:
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASSWORD})
    await connection.use(NAMESPACE, database)
    return connection


async def worker(
    worker_id: int, database: str, calls: int
) -> dict[str, Any]:
    """One independent connection hammering the shared sequence `calls` times."""
    connection = await connect(database)
    values: list[int] = []
    errors: list[str] = []
    try:
        for _ in range(calls):
            try:
                result = await connection.query(
                    f'RETURN sequence::nextval("{SEQUENCE_NAME}");'
                )
                values.append(result)
            except SurrealError as error:
                errors.append(f"{type(error).__name__}: {error}")
            except Exception as error:  # noqa: BLE001 - probe: surface any crash
                errors.append(f"UNEXPECTED {type(error).__name__}: {error}")
    finally:
        await connection.close()
    return {"worker_id": worker_id, "values": values, "errors": errors}


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")
    print(f"=== workers: {WORKER_COUNT}, calls/worker: {CALLS_PER_WORKER} ===")

    setup = await connect(database)
    await setup.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await setup.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await setup.query(f"DEFINE SEQUENCE {SEQUENCE_NAME} BATCH 1000 START 0;")
    await setup.close()

    start = time.monotonic()
    results = await asyncio.gather(
        *(worker(worker_id, database, CALLS_PER_WORKER) for worker_id in range(WORKER_COUNT))
    )
    elapsed = time.monotonic() - start

    all_values: list[int] = []
    all_errors: list[str] = []
    for result in results:
        all_values.extend(result["values"])
        all_errors.extend(result["errors"])
        print(
            f"  worker {result['worker_id']}: "
            f"{len(result['values'])} values, {len(result['errors'])} errors"
        )

    distinct_values = set(all_values)
    expected_total = WORKER_COUNT * CALLS_PER_WORKER

    print("-" * 80)
    print(f"elapsed_seconds: {elapsed:.3f}")
    print(f"expected_total_calls: {expected_total}")
    print(f"values_minted: {len(all_values)}")
    print(f"distinct_values: {len(distinct_values)}")
    print(f"errors_total: {len(all_errors)}")
    if all_errors:
        print("first_10_errors:")
        for error in all_errors[:10]:
            print(f"  {error}")
    print(f"min_value: {min(all_values) if all_values else None}")
    print(f"max_value: {max(all_values) if all_values else None}")
    print(
        f"contiguous_no_gaps: "
        f"{sorted(all_values) == list(range(min(all_values), max(all_values) + 1)) if all_values else None}"
    )
    print(f"DUPLICATES_FOUND: {len(all_values) != len(distinct_values)}")

    # Cleanup: reap the throwaway database via a fresh admin connection.
    admin = await connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()
    print("\n=== DONE (concurrency phase) ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001 - probe: surface any crash verbatim
        traceback.print_exc()
        sys.exit(1)
