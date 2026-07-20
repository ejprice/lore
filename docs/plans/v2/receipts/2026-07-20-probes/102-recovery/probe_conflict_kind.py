"""probe-conflict-kind: empirically settle whether SurrealDB 3.1.5 (via the
pinned Python SDK ``surrealdb==2.0.0``) exposes a STRUCTURED conflict signal
(server-side ``kind``/``details``/error-code) instead of forcing English
substring-matching for retryable transaction-conflict detection.

Three phases against a single throwaway spike-surreal database:

  PHASE 1 (query_raw / multi-statement transaction path) — the path
  ``loremaster.store._txn.execute_transaction`` actually uses:
    1a. Force a genuine write-write conflict: N concurrent tasks, each on its
        OWN connection, hammering ``BEGIN; UPSERT type::record('some_counter',
        'singleton') SET next += 1; COMMIT;`` via ``connection.query_raw``.
        Dump the FULL raw response envelope for the first conflicted attempt.
    1b. POSITIVE CONTROL: dump the full raw response envelope for a
        SUCCESSFUL attempt via the exact same ``query_raw`` call shape.
    1c. DISCRIMINATING CONTROL: a domain rejection (ASSERT violation) inside
        a ``BEGIN … COMMIT`` via ``query_raw``. Dump its full raw response.

  PHASE 2 (single-statement path) — the path ``is_connection_error`` /
  ``_query`` seams use:
    Force the same hot-row race but with a single statement (no BEGIN/COMMIT)
    via ``connection.query()`` across concurrent connections, which RAISES an
    SDK exception. Catch it and introspect exhaustively: type, MRO, .kind,
    .details (+ type), .code, vars(), dir().

Targets ONLY spike-surreal (ws://127.0.0.1:18000). NEVER ws://127.0.0.1:18500
(production).
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import traceback
import uuid
from typing import Any

from surrealdb import AsyncSurreal
from surrealdb.errors import ServerError, SurrealError

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = "spikeroot"
NAMESPACE = "lore_test"

CONFLICT_MARKER = "can be retried"

# Concurrency degree for the hot-row race — repo law: raise concurrency until
# conflicts appear; 8-16 way is the proven recipe.
WORKER_COUNT = 16
MAX_ROUNDS_PER_WORKER = 60


def unique_database() -> str:
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


async def connect(database: str) -> AsyncSurreal:
    connection = AsyncSurreal(URL)
    await connection.signin({"username": USER, "password": PASSWORD})
    await connection.use(NAMESPACE, database)
    return connection


def dump(label: str, obj: Any) -> None:
    print(f"\n{'=' * 20} {label} {'=' * 20}")
    try:
        print(json.dumps(obj, indent=2, default=repr, sort_keys=False))
    except TypeError:
        print(repr(obj))


# --------------------------------------------------------------------------
# PHASE 1: query_raw / transaction path
# --------------------------------------------------------------------------


async def hammer_query_raw(
    worker_id: int,
    database: str,
    found: dict[str, Any],
    stop: asyncio.Event,
) -> None:
    """One worker's loop of BEGIN/COMMIT UPSERTs via query_raw.

    Populates ``found["conflict"]`` with the first raw response containing an
    ERR-status statement whose result carries the conflict marker, and
    ``found["success"]`` with the first raw response where every statement
    succeeded. Stops once BOTH are captured (or ``stop`` is set by the phase
    driver after a global round budget).
    """
    connection = await connect(database)
    statement = (
        "BEGIN;\n"
        "UPSERT type::record('some_counter', 'singleton') SET next += 1;\n"
        "COMMIT;\n"
    )
    try:
        for _ in range(MAX_ROUNDS_PER_WORKER):
            if stop.is_set():
                return
            response = await connection.query_raw(statement, {})
            results = response.get("result") or []
            statuses = [entry.get("status") for entry in results if isinstance(entry, dict)]
            has_err = "ERR" in statuses
            if has_err:
                err_texts = [
                    str(entry.get("result"))
                    for entry in results
                    if isinstance(entry, dict) and entry.get("status") == "ERR"
                ]
                is_conflict = any(CONFLICT_MARKER in text for text in err_texts)
                if is_conflict and "conflict" not in found:
                    found["conflict"] = response
                    found["conflict_worker"] = worker_id
            else:
                if "success" not in found:
                    found["success"] = response
                    found["success_worker"] = worker_id
            if "conflict" in found and "success" in found:
                stop.set()
                return
    finally:
        await connection.close()


async def phase1_query_raw_conflict_and_success(database: str) -> dict[str, Any]:
    found: dict[str, Any] = {}
    stop = asyncio.Event()
    await asyncio.gather(
        *(hammer_query_raw(worker_id, database, found, stop) for worker_id in range(WORKER_COUNT))
    )
    return found


async def phase1c_assert_violation(database: str) -> dict[str, Any]:
    """A domain rejection (ASSERT violation) inside BEGIN/COMMIT via query_raw."""
    connection = await connect(database)
    try:
        await connection.query(
            "DEFINE TABLE IF NOT EXISTS assert_probe SCHEMAFULL;\n"
            "DEFINE FIELD IF NOT EXISTS val ON assert_probe TYPE int "
            "ASSERT $value > 10;"
        )
        statement = (
            "BEGIN;\n"
            f"CREATE assert_probe:{uuid.uuid4().hex} SET val = 1;\n"
            "COMMIT;\n"
        )
        response = await connection.query_raw(statement, {})
        return response
    finally:
        await connection.close()


# --------------------------------------------------------------------------
# PHASE 2: single-statement path (no BEGIN/COMMIT) -> SDK raises
# --------------------------------------------------------------------------


async def hammer_single_statement(
    worker_id: int,
    database: str,
    found: dict[str, Any],
    stop: asyncio.Event,
) -> None:
    connection = await connect(database)
    statement = "UPSERT type::record('some_counter_2', 'singleton') SET next += 1;"
    try:
        for _ in range(MAX_ROUNDS_PER_WORKER):
            if stop.is_set():
                return
            try:
                await connection.query(statement, {})
            except SurrealError as error:
                text = str(error)
                if CONFLICT_MARKER in text and "exception" not in found:
                    found["exception"] = error
                    found["exception_worker"] = worker_id
                    stop.set()
                    return
    finally:
        await connection.close()


async def phase2_single_statement_conflict(database: str) -> dict[str, Any]:
    found: dict[str, Any] = {}
    stop = asyncio.Event()
    await asyncio.gather(
        *(
            hammer_single_statement(worker_id, database, found, stop)
            for worker_id in range(WORKER_COUNT)
        )
    )
    return found


def introspect_exception(error: BaseException) -> None:
    print(f"\n{'=' * 20} PATH 2 EXCEPTION INTROSPECTION {'=' * 20}")
    print(f"repr(error): {error!r}")
    print(f"str(error): {error!s}")
    print(f"type(error): {type(error)}")
    print(f"type(error).__name__: {type(error).__name__}")
    print(f"type(error).__mro__: {type(error).__mro__}")
    print(f"isinstance ServerError: {isinstance(error, ServerError)}")
    kind = getattr(error, "kind", "<NO kind ATTR>")
    details = getattr(error, "details", "<NO details ATTR>")
    code = getattr(error, "code", "<NO code ATTR>")
    print(f"error.kind: {kind!r}")
    print(f"error.details: {details!r}")
    print(f"type(error.details): {type(details)}")
    print(f"error.code: {code!r}")
    if isinstance(details, dict):
        print(f"error.details.get('kind'): {details.get('kind')!r}")
        print(
            "error.details.get('kind') == 'TransactionConflict': "
            f"{details.get('kind') == 'TransactionConflict'}"
        )
    print(f"vars(error): {vars(error) if hasattr(error, '__dict__') else '<no __dict__>'}")
    print(f"dir(error): {[d for d in dir(error) if not d.startswith('_')]}")
    server_cause = getattr(error, "server_cause", None)
    print(f"error.server_cause: {server_cause!r}")


async def main() -> None:
    database = unique_database()
    print(f"=== database: {database} ===")

    setup = await connect(database)
    await setup.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await setup.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    await setup.query("DEFINE TABLE IF NOT EXISTS some_counter SCHEMALESS;")
    await setup.query("DEFINE TABLE IF NOT EXISTS some_counter_2 SCHEMALESS;")
    await setup.close()

    # --- PHASE 1a/1b: conflict + success via query_raw ---
    print("\n### PHASE 1a/1b: hammering hot row via query_raw (BEGIN/COMMIT) ###")
    found1 = await phase1_query_raw_conflict_and_success(database)
    if "conflict" in found1:
        dump("PATH 1 CONFLICT — FULL RAW query_raw RESPONSE", found1["conflict"])
    else:
        print("!!! NO CONFLICT CAPTURED IN PHASE 1a/1b — widen concurrency/rounds !!!")
    if "success" in found1:
        dump("PATH 1 SUCCESS (positive control) — FULL RAW query_raw RESPONSE", found1["success"])
    else:
        print("!!! NO SUCCESS CAPTURED IN PHASE 1a/1b (unexpected) !!!")

    # --- PHASE 1c: ASSERT violation (discriminating control) ---
    print("\n### PHASE 1c: ASSERT-violation rollback via query_raw ###")
    assert_response = await phase1c_assert_violation(database)
    dump("PATH 1 ASSERT-VIOLATION (discriminating control) — FULL RAW query_raw RESPONSE", assert_response)

    # --- PHASE 2: single-statement path raises ---
    print("\n### PHASE 2: hammering hot row via single-statement query() (no envelope) ###")
    found2 = await phase2_single_statement_conflict(database)
    if "exception" in found2:
        introspect_exception(found2["exception"])
    else:
        print("!!! NO CONFLICT EXCEPTION CAPTURED IN PHASE 2 — widen concurrency/rounds !!!")

    admin = await connect(database)
    await admin.query(f"REMOVE DATABASE IF EXISTS {database};")
    await admin.close()
    print("\n=== DONE ===")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception:  # noqa: BLE001
        traceback.print_exc()
        sys.exit(1)
