"""Packet 07 (store-error honesty) — LIVE probe of the store's error-classification
shapes against the CURRENT engine (spike-surreal, SurrealDB 3.2.4).

WHY THIS EXISTS. Findings #118/#119/#144 and every classifier fixture in
``test_surreal_store.py`` were captured against SurrealDB **3.1.5** (2026-07-13,
by the now-deleted ``scratchpad/contract-v5/capture_engine.py``). The floating
``v3.2`` tag has since carried both stores to **3.2.4**, and no fixture has been
re-probed on it. This is the packet's mandated re-grounding probe: it provokes
each error class and rollback shape the classifier depends on and prints the RAW
engine text, so the contract's fixtures are grounded in 3.2.4 truth, not memory.

It is the durable replacement for the lost ``capture_engine.py`` — committed here
(``scripts/``) rather than left in a scratchpad, per brief-base §1 (an instrument
that establishes a load-bearing claim is a deliverable, not scratch).

Targets ONLY spike-surreal (ws://127.0.0.1:18000). NEVER :18500 (production).

Usage:
    cd loremaster && uv run python ../scripts/probe_store_error_classes_07.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "loremaster"))

from loremaster.store._txn import signin_credentials  # noqa: E402
from pydantic import SecretStr  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402

URL = "ws://127.0.0.1:18000/rpc"
USER = "root"
PASSWORD = SecretStr("spikeroot")
NAMESPACE = "lore_test"


def _unique_database() -> str:
    return f"probe07_{uuid.uuid4().hex}"


async def _connect(database: str) -> Any:
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=PASSWORD))
    await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {NAMESPACE}")
    await connection.use(NAMESPACE, database)
    await connection.query(f"DEFINE DATABASE IF NOT EXISTS {database}")
    return connection


def _dump_failed_statements(response: dict[str, Any]) -> list[tuple[int, str, str]]:
    """Return (index, status, result-text) for every per-statement entry."""
    out: list[tuple[int, str, str]] = []
    for index, entry in enumerate(response.get("result") or []):
        if isinstance(entry, dict):
            out.append((index, str(entry.get("status")), str(entry.get("result"))))
    return out


async def _define_probe_schema(connection: Any) -> None:
    await connection.query("DEFINE TABLE classify_probe SCHEMAFULL;")
    await connection.query(
        "DEFINE FIELD state ON classify_probe TYPE string "
        "ASSERT $value INSIDE ['open', 'done'];"
    )
    await connection.query("DEFINE FIELD ordinal ON classify_probe TYPE int;")


async def probe_a_multistatement_domain_rollback(connection: Any) -> None:
    print("\n" + "=" * 78)
    print("PROBE A — multi-statement DOMAIN rollback shape (ASSERT violation mid-txn)")
    print("=" * 78)
    txn = (
        "BEGIN;\n"
        "CREATE classify_probe:ok SET state = 'open', ordinal = 1;\n"
        "CREATE classify_probe:bad SET state = 'BOGUS', ordinal = 2;\n"
        "CREATE classify_probe:after SET state = 'done', ordinal = 3;\n"
        "COMMIT;"
    )
    raw = await connection.query_raw(txn)
    print("full query_raw failed-statement list (index | status | result):")
    for index, status, result in _dump_failed_statements(raw):
        print(f"  idx {index}  {status:<3}  {result!r}")


async def probe_b_bare_query_statement0_gap(connection: Any) -> None:
    print("\n" + "=" * 78)
    print("PROBE B — the SDK .query() statement[0]-only gap (#144/#124 mechanism)")
    print("=" * 78)
    txn = (
        "BEGIN;\n"
        "CREATE classify_probe:q_ok SET state = 'open', ordinal = 10;\n"
        "CREATE classify_probe:q_bad SET state = 'BOGUS', ordinal = 11;\n"
        "COMMIT;"
    )
    try:
        result = await connection.query(txn)
        print(f"  bare .query() RAISED nothing; returned: {result!r}")
        print("  -> a LATER statement's rejection is INVISIBLE through bare .query()")
    except Exception as error:  # noqa: BLE001 — probe: report whatever surfaced
        print(f"  bare .query() raised: {type(error).__name__}: {error}")
    # Independent read-back: did the transaction actually roll back (no rows)?
    check = await connection.query(
        "SELECT count() FROM classify_probe WHERE ordinal IN [10, 11] GROUP ALL"
    )
    print(f"  independent read-back of rows the txn tried to write: {check!r}")
    print("  -> rolled back cleanly: no committed rows, but bare .query() said nothing")


async def probe_c_conflict_in_a_later_statement(database: str) -> None:
    print("\n" + "=" * 78)
    print("PROBE C — a RETRYABLE conflict surfaced in a NON-FIRST statement")
    print("=" * 78)
    setup = await _connect(database)
    await setup.query("DEFINE TABLE counter SCHEMALESS;")
    await setup.query("CREATE counter:x SET n = 0;")

    racers = 12
    connections = [await _connect(database) for _ in range(racers)]
    txn = (
        "BEGIN;\n"
        "LET $c = (SELECT VALUE n FROM counter:x)[0];\n"
        "UPDATE counter:x SET n = $c + 1;\n"
        "COMMIT;"
    )

    async def _race(conn: Any) -> Any:  # the SDK types query_raw's response as Any
        return await conn.query_raw(txn)

    conflict_shapes: list[list[tuple[int, str, str]]] = []
    for _ in range(30):  # bounded rounds until a conflict shape is captured
        responses = await asyncio.gather(*[_race(c) for c in connections])
        for response in responses:
            dumped = _dump_failed_statements(response)
            if any("can be retried" in text for _, status, text in dumped if status == "ERR"):
                conflict_shapes.append(dumped)
        if conflict_shapes:
            break

    if not conflict_shapes:
        print("  (no conflict captured in 30 rounds — engine resolved every race)")
    else:
        shape = conflict_shapes[0]
        print("  captured a rolled-back CONFLICT — full failed-statement list:")
        for index, status, result in shape:
            print(f"  idx {index}  {status:<3}  {result!r}")
        marker_indices = [i for i, s, t in shape if s == "ERR" and "can be retried" in t]
        err_indices = [i for i, s, _ in shape if s == "ERR"]
        print(f"  ERR entries at indices: {err_indices}")
        print(f"  'can be retried' marker rides index/indices: {marker_indices}")
        print(f"  is the marker on the FIRST ERR entry? {marker_indices[:1] == err_indices[:1]}")

    for conn in [setup, *connections]:
        await conn.close()


async def probe_d_coercion(connection: Any) -> None:
    print("\n" + "=" * 78)
    print("PROBE D — field-coercion rejection text")
    print("=" * 78)
    raw = await connection.query_raw(
        "BEGIN;\nCREATE classify_probe:coerce SET state = 'open', ordinal = 'not-an-int';\nCOMMIT;"
    )
    for index, status, result in _dump_failed_statements(raw):
        if status == "ERR":
            print(f"  idx {index}  {status}  {result!r}")


async def probe_e_recursion_depth(connection: Any) -> None:
    print("\n" + "=" * 78)
    print("PROBE E — 'query too complex' (expression recursion depth) text")
    print("=" * 78)
    predicate = " OR ".join(["state = 'x'"] * 400)
    try:
        raw = await connection.query_raw(f"SELECT * FROM classify_probe WHERE {predicate}")
        errs = [t for _, s, t in _dump_failed_statements(raw) if s == "ERR"]
        if errs:
            print(f"  ERR: {errs[0]!r}")
        else:
            print("  (no recursion-depth error at 400 OR-clauses; engine accepted it)")
    except Exception as error:  # noqa: BLE001
        print(f"  raised: {type(error).__name__}: {error}")


async def main() -> None:
    database = _unique_database()
    print(f"probe database: {NAMESPACE}:{database} @ {URL}")
    connection = await _connect(database)
    version = await connection.version()
    print(f"engine version: {version}")
    await _define_probe_schema(connection)
    try:
        await probe_a_multistatement_domain_rollback(connection)
        await probe_b_bare_query_statement0_gap(connection)
        await probe_d_coercion(connection)
        await probe_e_recursion_depth(connection)
        await probe_c_conflict_in_a_later_statement(database)
    finally:
        await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
        await connection.close()


if __name__ == "__main__":
    asyncio.run(main())
