"""Finding #66 bisect probe — root-cause the hybrid_search hard rejection on
long query text, against the spike-surreal TEST store (ws://127.0.0.1:18000),
never :18500 (production).

Isolates the failure to one of three candidate mechanisms:
  (a) char-length cap on the raw query text fed to search::analyze,
  (b) token-count cap on the analyzed tokens feeding the BM25 OR-predicate,
  (c) something else entirely (e.g. a SurrealQL parser depth/size limit on the
      constructed WHERE clause, independent of the store's own declared caps).

Runs three independent bisections:
  1. End-to-end hybrid_search with a real plain-English sentence, doubled/
     repeated to grow length, to find the exact char-length failure boundary
     matching the informal 245-ok/340-fail report.
  2. Direct _analyze_query calls at varying char lengths (isolates whether
     search::analyze itself, independent of the OR-predicate, ever rejects).
  3. Direct hybrid_search calls with a SYNTHETIC token list of exact, known
     size (bypassing the analyzer + real English text entirely) to find the
     exact TOKEN-COUNT boundary that trips the rejection in the OR-predicate/
     WHERE-clause construction — the strongest candidate mechanism.
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

REAL_SENTENCE = (
    "What was the operator ruling on the P8d closure and how does the slate "
    "cycle get sequenced before the detection layer lands, and which commits "
    "carry the surface flip receipts we should cite when asked."
)


async def bisect_end_to_end(store: SurrealStore, vector: list[float]) -> None:
    print("\n=== 1. end-to-end hybrid_search, real English text, growing length ===")
    lengths = [100, 150, 200, 245, 260, 280, 300, 320, 340, 360, 400, 500, 800, 1200]
    text = (REAL_SENTENCE * 20)
    for length in lengths:
        query_text = text[:length]
        try:
            await store.hybrid_search(query_vector=vector, query_text=query_text, k=5)
            print(f"  len={length:5d}  OK")
        except SurrealStoreError as error:
            print(f"  len={length:5d}  REJECTED: {error}")


async def bisect_analyze_only(store: SurrealStore) -> None:
    print("\n=== 2. _analyze_query direct calls, growing char length ===")
    lengths = [200, 340, 500, 1000, 2000, 4096, 5000]
    text = REAL_SENTENCE * 40
    for length in lengths:
        query_text = text[:length]
        try:
            tokens = await store._analyze_query(query_text)  # noqa: SLF001
            print(f"  len={length:5d}  OK  tokens={len(tokens)}")
        except SurrealStoreError as error:
            print(f"  len={length:5d}  REJECTED: {error}")


async def bisect_synthetic_token_count(store: SurrealStore, vector: list[float]) -> None:
    print("\n=== 3. hybrid_search with SYNTHETIC token counts (bypass analyzer) ===")
    # Monkeypatch _analyze_query to return an exact, known-size synthetic token
    # list, so the OR-predicate/WHERE-clause size is the ONLY thing varying —
    # isolates whether the true limit is token-count-driven (clause count) or
    # something else (statement byte-length).
    counts = [10, 30, 50, 64, 65, 80, 100, 150, 200, 300, 500]
    for count in counts:
        synthetic_tokens = [f"synthtoken{i}" for i in range(count)]

        async def _fake_analyze(_query_text: str, _tokens: list[str] = synthetic_tokens) -> list[str]:
            return _tokens

        store._analyze_query = _fake_analyze  # type: ignore[method-assign]  # noqa: SLF001
        try:
            await store.hybrid_search(query_vector=vector, query_text="placeholder", k=5)
            print(f"  tokens={count:4d}  OK")
        except SurrealStoreError as error:
            print(f"  tokens={count:4d}  REJECTED: {error}")


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
        await bisect_end_to_end(store, vector)
        await bisect_analyze_only(store)
        await bisect_synthetic_token_count(store, vector)
    finally:
        await store.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
