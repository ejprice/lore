"""CONTROL for the v2 anomaly: identical shape (16 workers x 30 explicit
BEGIN/COMMIT transactions, own connection per worker, fresh-connection
ground-truth scan at the end) but with sequence::nextval() REMOVED from the
transaction body. If rows still go missing here, the anomaly is a general
engine/transaction artifact, NOT specific to the sequence mechanism. If rows
do NOT go missing here, the sequence call is implicated.

Ad-hoc probe script (probe-sequence-1). Targets ONLY spike-surreal
(ws://127.0.0.1:18000). NEVER :18500.
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
TABLE_NAME = "txn_control_no_sequence_row"

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
    committed_tags: list[str] = []
    commit_retryable_conflicts: list[str] = []
    commit_other_errors: list[str] = []
    try:
        for i in range(txn_count):
            tag = f"{worker_id}-{i}-{uuid.uuid4().hex}"
            # NOTE: no sequence::nextval() at all - a plain counter-free write.
            statement = (
                "BEGIN TRANSACTION;\n"
                f"CREATE {TABLE_NAME} SET tag = '{tag}', worker_id = {worker_id}, i = {i};\n"
                "COMMIT TRANSACTION;\n"
            )
            try:
                await connection.query(statement)
                committed_tags.append(tag)
            except SurrealError as error:
                text = str(error)
                if RETRYABLE_CONFLICT_MARKER in text:
                    commit_retryable_conflicts.append(f"{type(error).__name__}: {text}")
                else:
                    commit_other_errors.append(f"{type(error).__name__}: {text}")
            except Exception as error:  # noqa: BLE001
                commit_other_errors.append(f"UNEXPECTED {type(error).__name__}: {error}")
    finally:
        await connection.close()
    return {
        "worker_id": worker_id,
        "committed_tags": committed_tags,
        "commit_retryable_conflicts": commit_retryable_conflicts,
        "commit_other_errors": commit_other_errors,
    }


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")
    print(f"=== workers: {WORKER_COUNT}, txns/worker: {TXNS_PER_WORKER} (NO sequence::nextval) ===")

    setup = await connect(database)
    await setup.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await setup.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await setup.close()

    start = time.monotonic()
    results = await asyncio.gather(
        *(worker(worker_id, database, TXNS_PER_WORKER) for worker_id in range(WORKER_COUNT))
    )
    elapsed = time.monotonic() - start

    all_committed_tags: list[str] = []
    all_commit_retryable: list[str] = []
    all_commit_other: list[str] = []
    for result in results:
        all_committed_tags.extend(result["committed_tags"])
        all_commit_retryable.extend(result["commit_retryable_conflicts"])
        all_commit_other.extend(result["commit_other_errors"])

    expected_total = WORKER_COUNT * TXNS_PER_WORKER

    verifier = await connect(database)
    all_rows = await verifier.query(f"SELECT tag FROM {TABLE_NAME};")
    row_count = len(all_rows)
    tags_in_table = {row["tag"] for row in all_rows}
    committed_tags_set = set(all_committed_tags)
    missing_from_table = committed_tags_set - tags_in_table

    print("-" * 80)
    print(f"elapsed_seconds: {elapsed:.3f}")
    print(f"expected_total_txns: {expected_total}")
    print(f"commit_step_succeeded: {len(all_committed_tags)}")
    print(f"commit_step_retryable_conflicts: {len(all_commit_retryable)}")
    print(f"commit_step_other_errors: {len(all_commit_other)}")
    print(f"row_count_in_table (fresh connection): {row_count}")
    print(f"tags_committed_but_MISSING_from_table: {len(missing_from_table)}")
    if missing_from_table:
        print(f"sample_missing_tags: {list(missing_from_table)[:10]}")
        missing_iteration_indices = sorted({tag.split('-')[1] for tag in missing_from_table})
        print(f"missing_iteration_indices (the 'i' in worker-i-uuid): {missing_iteration_indices}")

    admin = await connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()
    print("\n=== DONE (control: no sequence) ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
