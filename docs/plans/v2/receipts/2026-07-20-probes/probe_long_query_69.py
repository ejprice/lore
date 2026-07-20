"""Finding #69 — token-count boundary bisect for MemoryBackend._hybrid_search's
OWN predicate shape, against spike-surreal (never production).

Follow-up to finding #66/#67's chunk-store bisection (probe_long_query_66b.py /
probe_long_query_66c.py): `LocalMemoryBackend._hybrid_search`'s fulltext
predicate is a DIFFERENT SHAPE from `SurrealStore.hybrid_search`'s —

* `MEMORY_FULLTEXT_FIELDS` has 1 field (`note_text`) vs. the chunk store's 3
  (`CHUNK_FULLTEXT_FIELDS`), so each token contributes 1 clause here, not 3;
* the memory predicate is CONJUNCTIVE (an AND-chain of per-token single-field
  terms — "every query word must be present"), not the chunk store's flat
  OR-chain ("any token matches") — a deliberate divergence documented in
  `LocalMemoryBackend._build_fulltext_predicate`'s own docstring.

So the chunk store's measured 39-token/117-clause boundary does NOT transfer
directly; this script measures the recall path's OWN boundary end-to-end
through `LocalMemoryBackend.recall` (patching `_analyze_query` to return
synthetic tokens, exactly as `probe_long_query_66b.py` patches
`SurrealStore._analyze_query`), so the fix's constants are derived from a
live measurement of the ACTUAL statement shape, not by analogy.
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
import loremaster.memory.local as local_module  # noqa: E402
from loremaster.memory.local import LocalMemoryBackend  # noqa: E402
from loremaster.store._txn import SurrealStoreError  # noqa: E402
from loresigil.testing import FakeEmbedder  # noqa: E402

# CRITICAL: the CURRENT (unfixed) module already clamps
# ``tokens[:_MAX_QUERY_TOKENS]`` (value 64) in ``_hybrid_search`` — a fixed
# module-level constant, read by name at call time, NOT an instance
# attribute. A naive probe that only patches ``_analyze_query`` (mirroring
# probe_long_query_66b.py) is silently capped at 64 tokens by this
# pre-existing clamp for any requested count above 64 (confirmed live: a
# 500,000-synthetic-token request produced a 65-param statement — 64
# fulltext + 1 vector — proving the clamp, not the requested count, decided
# the query shape). To measure the ENGINE's true boundary for this
# predicate shape we neutralize the clamp for the probe's duration.
_UNCLAMPED_MAX_QUERY_TOKENS = 10_000_000


async def _no_existing_chunks(_chunk_keys: object) -> set[str]:
    return set()


async def try_token_count(backend: LocalMemoryBackend, count: int) -> bool:
    synthetic_tokens = [f"synthtoken{i}" for i in range(count)]

    async def _fake_analyze(_query_text: str, _tokens: list[str] = synthetic_tokens) -> list[str]:
        return _tokens

    backend._analyze_query = _fake_analyze  # type: ignore[method-assign]  # noqa: SLF001
    try:
        await backend.recall("placeholder", k=5)
        return True
    except SurrealStoreError:
        return False


async def main() -> None:
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    setup_connection = await connect_admin(env)
    await setup_connection.close()
    backend = LocalMemoryBackend(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        dim=env.dim,
        user=env.user,
        password=env.password,
        embedder=FakeEmbedder(dim=env.dim),
        existing_chunks=_no_existing_chunks,
        ledger=None,
    )
    original_max_query_tokens = local_module._MAX_QUERY_TOKENS
    local_module._MAX_QUERY_TOKENS = _UNCLAMPED_MAX_QUERY_TOKENS
    try:
        await backend.ensure_ready()

        # Establish hi actually fails first — memory has only 1 fulltext field
        # and an AND-chain (not chunk's 3-field OR-chain), so the boundary is
        # expected to sit far higher than the chunk store's ~40 tokens.
        lo, hi = 30, 60
        while await try_token_count(backend, hi):
            lo = hi
            hi *= 2
            print(f"  tokens={hi:6d}  OK (doubling)")
            if hi > 200_000:
                print(f"no rejection found up to {hi} tokens — stopping")
                return
        while lo + 1 < hi:
            mid = (lo + hi) // 2
            ok = await try_token_count(backend, mid)
            print(f"  tokens={mid:4d}  {'OK' if ok else 'REJECTED'}")
            if ok:
                lo = mid
            else:
                hi = mid
        print(f"\nBOUNDARY: tokens={lo} OK, tokens={hi} REJECTED")
        print(f"clauses at boundary (1 field/token, AND-chained): ok={lo}, rejected={hi}")

        # Capture the RAW pre-classification engine error at the failing boundary.
        synthetic_tokens = [f"synthtoken{i}" for i in range(hi)]

        async def _fake_analyze(_query_text: str) -> list[str]:
            return synthetic_tokens

        backend._analyze_query = _fake_analyze  # type: ignore[method-assign]  # noqa: SLF001
        try:
            await backend.recall("placeholder", k=5)
        except SurrealStoreError as error:
            print(f"\nClassified (laundered) error: {error}")
            print(f"Raw underlying cause: {error.__cause__!r}")
    finally:
        local_module._MAX_QUERY_TOKENS = original_max_query_tokens
        await backend.close()
        await drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
