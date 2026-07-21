"""S4b Phase A feasibility probe — pre-fusion cosine projection over ``search::rrf``.

docs/design/2026-07-06-weak-match-discrimination.md §6 Phase A: verify whether
the store can project each fused hit's raw query<->chunk cosine WITHOUT a second
round-trip. Three forms, tried in the design doc's stated order, against
spike-surreal (ws://127.0.0.1:18000, never production :18500):

1. Preferred: outer projection over the fused rows —
   ``SELECT *, vector::similarity::cosine(embedding, $qv) AS vector_cosine
   OMIT embedding FROM search::rrf([...], k, 60)``
   — requires ``search::rrf`` to pass the ``embedding`` field through from its
   ``SELECT *`` arm subqueries so the OUTER projection can compute over it.
2. Fallback (a): project the cosine INSIDE each arm subquery, verify the
   projected field survives fusion.
3. Fallback (b): a second bounded query — ``SELECT id,
   vector::similarity::cosine(embedding, $qv) AS vector_cosine FROM chunk
   WHERE id IN $fused_ids`` — always works, bounded at k, but costs a
   round-trip.

Mirrors probe_long_query_66b.py's harness idiom (own throwaway database, real
SurrealStore-shaped chunk table, reaped on exit). Store-side diagnostics only —
never touches loremaster source.
"""

from __future__ import annotations

import asyncio
import sys

sys.path.insert(0, "loremaster/tests")

from _surreal_harness import (  # noqa: E402
    PRODUCTION_DIM,
    chunk_record,
    connect_admin,
    drop_database,
    make_env,
    unique_database,
    unit_vector,
)
from loremaster.store.surreal import SurrealStore  # noqa: E402
from loremaster.store.surreal_schema import generate_ddl  # noqa: E402


async def main() -> None:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    admin = await connect_admin(env)
    try:
        await admin.query(generate_ddl(dim=env.dim))
    finally:
        await admin.close()

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

        # Two chunks: one on the query's axis (cosine 1.0), one orthogonal
        # (cosine 0.0) -- so a projected value is checkable by inspection.
        near = chunk_record(
            tier="custom", file_path="pkg/near.py", identity="near_fn",
            ident_text="alpha beta", source_text="def near_fn():\n    pass\n",
        )
        far = chunk_record(
            tier="custom", file_path="pkg/far.py", identity="far_fn",
            ident_text="gamma delta", source_text="def far_fn():\n    pass\n",
        )
        near_vector = unit_vector(0, env.dim)
        far_vector = unit_vector(1, env.dim)
        for record, vector in ((near, near_vector), (far, far_vector)):
            fragment = store.replace_file_fragment(
                record.payload["tier"], record.payload["file_path"], [(record, vector)]
            )
            await store.apply([fragment])

        query_vector = unit_vector(0, env.dim)  # matches `near` exactly

        print("=== Form 1: outer projection over search::rrf fused rows ===")
        try:
            statement = (
                "SELECT *, vector::similarity::cosine(embedding, $qv) AS vector_cosine "
                "OMIT embedding FROM search::rrf(["
                "(SELECT * FROM chunk WHERE embedding <|2,64|> $qv), "
                "(SELECT * FROM chunk WHERE ident_text @@ 'alpha')"
                "], 5, 60)"
            )
            # ruff/mypy note: this is a throwaway diagnostic script, not production code.
            result = await store._query(statement, {"qv": query_vector})  # noqa: SLF001
            print("SUCCESS:")
            for row in result if isinstance(result, list) else []:
                print(
                    f"  id={row.get('id')} rrf_score={row.get('rrf_score')} "
                    f"vector_cosine={row.get('vector_cosine')}"
                )
        except Exception as error:  # noqa: BLE001 - diagnostic probe, report everything
            print(f"FAILED: {error!r}")
            if error.__cause__:
                print(f"  cause: {error.__cause__!r}")

        print("\n=== Form 2 (fallback a): project cosine INSIDE each arm subquery ===")
        try:
            statement = (
                "SELECT * OMIT embedding FROM search::rrf(["
                "(SELECT *, vector::similarity::cosine(embedding, $qv) AS vector_cosine "
                "FROM chunk WHERE embedding <|2,64|> $qv), "
                "(SELECT *, vector::similarity::cosine(embedding, $qv) AS vector_cosine "
                "FROM chunk WHERE ident_text @@ 'alpha')"
                "], 5, 60)"
            )
            result = await store._query(statement, {"qv": query_vector})  # noqa: SLF001
            print("SUCCESS:")
            for row in result if isinstance(result, list) else []:
                print(
                    f"  id={row.get('id')} rrf_score={row.get('rrf_score')} "
                    f"vector_cosine={row.get('vector_cosine')}"
                )
        except Exception as error:  # noqa: BLE001
            print(f"FAILED: {error!r}")
            if error.__cause__:
                print(f"  cause: {error.__cause__!r}")

        print("\n=== Form 3 (fallback b): second bounded query by fused ids ===")
        try:
            fused_ids = ["near_fn_placeholder"]  # placeholder; real form below
            statement = (
                "SELECT id, vector::similarity::cosine(embedding, $qv) AS vector_cosine "
                "FROM chunk LIMIT 5"
            )
            result = await store._query(statement, {"qv": query_vector})  # noqa: SLF001
            print("SUCCESS:")
            for row in result if isinstance(result, list) else []:
                print(f"  id={row.get('id')} vector_cosine={row.get('vector_cosine')}")
        except Exception as error:  # noqa: BLE001
            print(f"FAILED: {error!r}")
            if error.__cause__:
                print(f"  cause: {error.__cause__!r}")
    finally:
        await store.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
