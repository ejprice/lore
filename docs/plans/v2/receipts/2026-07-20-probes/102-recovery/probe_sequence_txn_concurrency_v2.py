"""v2: separates the COMMIT step from the same-connection immediate readback,
to chase down the IndexError anomaly seen in v1 (readback-after-commit
sometimes found zero rows for a tag that had just committed). Adds a final
FRESH-connection full-table count/scan so a genuinely vanished row (real
defect) can be told apart from same-connection read staleness (probe
artifact, not a sequence defect).

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
SEQUENCE_NAME = "txn_concurrency_probe_seq_v2"
TABLE_NAME = "txn_concurrency_probe_row_v2"

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
    readback_empty_count = 0
    readback_other_errors: list[str] = []
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
                committed_tags.append(tag)
            except SurrealError as error:
                text = str(error)
                if RETRYABLE_CONFLICT_MARKER in text:
                    commit_retryable_conflicts.append(f"{type(error).__name__}: {text}")
                else:
                    commit_other_errors.append(f"{type(error).__name__}: {text}")
                continue
            except Exception as error:  # noqa: BLE001
                commit_other_errors.append(f"UNEXPECTED {type(error).__name__}: {error}")
                continue

            try:
                readback = await connection.query(
                    f"SELECT seq_value FROM {TABLE_NAME} WHERE tag = '{tag}';"
                )
                if not readback:
                    readback_empty_count += 1
            except Exception as error:  # noqa: BLE001
                readback_other_errors.append(f"UNEXPECTED {type(error).__name__}: {error}")
    finally:
        await connection.close()
    return {
        "worker_id": worker_id,
        "committed_tags": committed_tags,
        "commit_retryable_conflicts": commit_retryable_conflicts,
        "commit_other_errors": commit_other_errors,
        "readback_empty_count": readback_empty_count,
        "readback_other_errors": readback_other_errors,
    }


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")
    print(f"=== workers: {WORKER_COUNT}, txns/worker: {TXNS_PER_WORKER} ===")

    setup = await connect(database)
    await setup.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await setup.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await setup.query(f"DEFINE SEQUENCE {SEQUENCE_NAME} BATCH 1000 START 0;")
    await setup.query(f"DEFINE TABLE {TABLE_NAME} SCHEMALESS;")  # isolate: rule out auto-schema race
    await setup.close()

    start = time.monotonic()
    results = await asyncio.gather(
        *(worker(worker_id, database, TXNS_PER_WORKER) for worker_id in range(WORKER_COUNT))
    )
    elapsed = time.monotonic() - start

    all_committed_tags: list[str] = []
    all_commit_retryable: list[str] = []
    all_commit_other: list[str] = []
    total_readback_empty = 0
    all_readback_other: list[str] = []
    for result in results:
        all_committed_tags.extend(result["committed_tags"])
        all_commit_retryable.extend(result["commit_retryable_conflicts"])
        all_commit_other.extend(result["commit_other_errors"])
        total_readback_empty += result["readback_empty_count"]
        all_readback_other.extend(result["readback_other_errors"])

    expected_total = WORKER_COUNT * TXNS_PER_WORKER

    # Fresh-connection, independent-of-any-worker ground truth: how many rows
    # actually exist in the table, and are their seq_values all distinct?
    verifier = await connect(database)
    all_rows = await verifier.query(f"SELECT seq_value, tag FROM {TABLE_NAME};")
    row_count = len(all_rows)
    seq_values = [row["seq_value"] for row in all_rows]
    distinct_seq_values = set(seq_values)
    tags_in_table = {row["tag"] for row in all_rows}
    committed_tags_set = set(all_committed_tags)
    missing_from_table = committed_tags_set - tags_in_table
    extra_in_table = tags_in_table - committed_tags_set

    print("-" * 80)
    print(f"elapsed_seconds: {elapsed:.3f}")
    print(f"expected_total_txns: {expected_total}")
    print(f"commit_step_succeeded: {len(all_committed_tags)}")
    print(f"commit_step_retryable_conflicts: {len(all_commit_retryable)}")
    print(f"commit_step_other_errors: {len(all_commit_other)}")
    print(f"same_connection_readback_empty_count: {total_readback_empty}")
    print(f"same_connection_readback_other_errors: {len(all_readback_other)}")
    print("-- FRESH-CONNECTION GROUND TRUTH --")
    print(f"row_count_in_table: {row_count}")
    print(f"distinct_seq_values_in_table: {len(distinct_seq_values)}")
    print(f"DUPLICATES_IN_TABLE: {row_count != len(distinct_seq_values)}")
    print(f"tags_committed_but_MISSING_from_table (real vanished-write count): {len(missing_from_table)}")
    print(f"tags_in_table_but_NOT_marked_committed (should be 0): {len(extra_in_table)}")
    if all_commit_other:
        print("first_5_commit_other_errors:")
        for error in all_commit_other[:5]:
            print(f"  {error}")
    if missing_from_table:
        print(f"sample_missing_tags: {list(missing_from_table)[:5]}")

    admin = await connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()
    print("\n=== DONE (v2 diagnostic phase) ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
