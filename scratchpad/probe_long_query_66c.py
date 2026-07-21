"""Finding #66 — exact SurrealQL OR-chain recursion-depth boundary.

Bypasses the store's field/token multiplier entirely and bisects the RAW
number of ``OR``-chained boolean clauses SurrealDB 3.1.5 accepts in one WHERE
predicate, via the store's own ``_query`` seam (same self-healing/classify
path production traffic uses). This is the authoritative parser bound the
fix's lexical-arm truncation constant is derived from (with margin), not the
informal token count from probe_long_query_66b.py (which is confounded by the
3-fields-per-token multiplier).
"""

from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "loremaster/tests")

from _surreal_harness import (  # noqa: E402
    PRODUCTION_DIM,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
)
from loremaster.store._txn import SurrealStoreError  # noqa: E402
from loremaster.store.surreal import SurrealStore  # noqa: E402


async def try_clause_count(store: SurrealStore, count: int) -> bool:
    clauses = " OR ".join(f"a = {i}" for i in range(count))
    statement = f"RETURN ({clauses})" if clauses else "RETURN true"
    try:
        await store._query(statement)  # noqa: SLF001
        return True
    except SurrealStoreError:
        return False


async def main() -> None:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    store = SurrealStore(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
    )
    try:
        await store.ensure_ready()

        lo, hi = 1, 500
        # Establish hi actually fails first.
        while await try_clause_count(store, hi):
            lo = hi
            hi *= 2
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            ok = await try_clause_count(store, mid)
            print(f"  clauses={mid:4d}  {'OK' if ok else 'REJECTED'}")
            if ok:
                lo = mid
            else:
                hi = mid
        print(f"\nEXACT BOUNDARY: clauses={lo} OK, clauses={hi} REJECTED")
    finally:
        await store.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
