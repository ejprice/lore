"""Finding #66 — precise token-count boundary bisect + raw engine error capture.

Follow-up to probe_long_query_66.py (which established the mechanism is
TOKEN COUNT in the BM25 OR-predicate, not char length): binary-search the exact
synthetic-token-count boundary, and print the RAW (pre-classification) engine
error text for one failing case so the true SurrealQL rejection reason is
visible (never surfaced to a real caller — this is store-side diagnostics only,
against the spike TEST store).
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
    unit_vector,
)
from loremaster.store._txn import SurrealStoreError  # noqa: E402
from loremaster.store.surreal import SurrealStore  # noqa: E402


async def try_token_count(store: SurrealStore, vector: list[float], count: int) -> bool:
    synthetic_tokens = [f"synthtoken{i}" for i in range(count)]

    async def _fake_analyze(_query_text: str, _tokens: list[str] = synthetic_tokens) -> list[str]:
        return _tokens

    store._analyze_query = _fake_analyze  # type: ignore[method-assign]  # noqa: SLF001
    try:
        await store.hybrid_search(query_vector=vector, query_text="placeholder", k=5)
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
        vector = unit_vector(0, PRODUCTION_DIM)

        # Binary search the exact ok/reject boundary between 30 (ok) and 50 (reject).
        lo, hi = 30, 50
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            ok = await try_token_count(store, vector, mid)
            print(f"  tokens={mid:4d}  {'OK' if ok else 'REJECTED'}")
            if ok:
                lo = mid
            else:
                hi = mid
        print(f"\nBOUNDARY: tokens={lo} OK, tokens={hi} REJECTED")
        print(f"OR-clauses at boundary: ok={lo * 3}, rejected={hi * 3} (3 fulltext fields/token)")

        # Capture the RAW pre-classification engine error at the failing boundary.
        synthetic_tokens = [f"synthtoken{i}" for i in range(hi)]

        async def _fake_analyze(_query_text: str) -> list[str]:
            return synthetic_tokens

        store._analyze_query = _fake_analyze  # type: ignore[method-assign]  # noqa: SLF001
        try:
            await store.hybrid_search(query_vector=vector, query_text="placeholder", k=5)
        except SurrealStoreError as error:
            print(f"\nClassified (laundered) error: {error}")
            print(f"Raw underlying cause: {error.__cause__!r}")
    finally:
        await store.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
