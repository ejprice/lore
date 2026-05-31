"""Contract tests for ``loremaster.store.qdrant`` against the REAL Qdrant server.

These run against the live local Qdrant (``http://127.0.0.1:16333``), NOT
``:memory:`` — the whole point of the C1 fix is server-side: payload indexes and
filter-based deletes are *no-ops* in the in-memory backend but take real effect
on the server. Each test uses a UNIQUE throwaway collection (slug
``test_<uuid4>`` → collection ``lore_test_<uuid4>``); the autouse ``qdrant_client``
fixture's teardown deletes every ``lore_test_*`` collection, so nothing leaks.

Pinned invariants (the amendment store deltas):

* ``ensure_collection(dim)`` creates the collection (size=``dim``, COSINE) and
  registers KEYWORD indexes on ``tier``/``file_path``/``content_hash``/
  ``chunk_type`` — PLUS any extension-declared extra indexes. The extra index is
  actually created on the server (queryable via the collection's index info).
* ``collection_dim()`` returns the configured size (mismatch detectable) or
  ``None`` when absent.
* ``upsert`` persists records; over-batch input is chunked but all points land.
* **C1 on REAL Qdrant:** the SAME ``file_path`` upserted under two tiers leaves
  BOTH points alive (distinct ids, distinct ``tier`` payloads).
* ``delete_by_tier(A)`` purges ONLY tier A; ``delete_by_file(B, path)`` purges
  only tier B's copy of that path.
"""

from __future__ import annotations

import os
import uuid
from typing import Any

import pytest_asyncio
from loremaster.index.records import Record, point_id
from loremaster.store.qdrant import QdrantStore
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import ScoredPoint

_DIM = 8
_SLUG = "demo"
_TIER_A = "custom"
_TIER_B = "community"
_HASH = "h" * 128


def _unique_slug() -> str:
    """A per-test slug → collection ``lore_test_<pid>_<uuid4>``.

    The ``<pid>`` matches the conftest ``qdrant_client`` teardown's per-process
    prefix (computed identically via ``os.getpid()``, no conftest import), so the
    teardown reaps this collection while a CONCURRENT pytest process — a different
    PID — never sweeps it. Concurrency-safe by construction.
    """
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


def _vec(seed: float) -> list[float]:
    """A simple deterministic dim-length vector for tests."""
    return [seed] + [0.0] * (_DIM - 1)


def _payload_of(hit: ScoredPoint) -> dict[str, Any]:
    """Return a hit's payload, asserting it is present (every lore point has one)."""
    assert hit.payload is not None
    return hit.payload


def _record(
    *,
    slug: str = _SLUG,
    tier: str,
    file_path: str,
    identity: str,
    chunk_type: str = "python_symbol",
    extra_payload: dict[str, Any] | None = None,
) -> Record:
    """Build a Record with a real tiered point id and a tiered payload."""
    payload: dict[str, Any] = {
        "tier": tier,
        "file_path": file_path,
        "content_hash": _HASH,
        "chunk_type": chunk_type,
        "identity": identity,
        "sub_ordinal": 0,
    }
    if extra_payload:
        payload.update(extra_payload)
    return Record(
        point_id=point_id(slug, tier, file_path, chunk_type, identity, 0),
        embedding_text=f"text-{tier}-{identity}",
        payload=payload,
    )


@pytest_asyncio.fixture()
async def store(qdrant_client: AsyncQdrantClient) -> QdrantStore:
    """A QdrantStore on a fresh throwaway collection on the REAL server."""
    return QdrantStore(client=qdrant_client, slug=_unique_slug())


class TestCollectionNaming:
    """The collection name is derived from the injected slug."""

    def test_collection_name_is_lore_slug(self, store: QdrantStore) -> None:
        assert store.collection_name.startswith("lore_test_")


class TestEnsureCollection:
    """Collection + payload-index creation on the real server."""

    async def test_creates_collection_with_configured_dim(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        assert await store.collection_dim() == _DIM

    async def test_is_idempotent(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.ensure_collection(_DIM)
        assert await store.collection_dim() == _DIM

    async def test_base_keyword_indexes_are_created_on_the_server(
        self, store: QdrantStore, qdrant_client: AsyncQdrantClient
    ) -> None:
        # On the REAL server, payload indexes are visible in the collection's
        # ``payload_schema`` — proving they were actually created (not a no-op).
        await store.ensure_collection(_DIM)
        info = await qdrant_client.get_collection(store.collection_name)
        indexed = set(info.payload_schema.keys())
        assert {"tier", "file_path", "content_hash", "chunk_type"} <= indexed

    async def test_extension_declared_index_is_created_on_the_server(
        self, qdrant_client: AsyncQdrantClient
    ) -> None:
        # An extension declares an extra KEYWORD index (e.g. a model_name-like
        # field). It must actually appear in the server's payload schema.
        store = QdrantStore(
            client=qdrant_client,
            slug=_unique_slug(),
            extra_keyword_indexes=["model_name"],
        )
        await store.ensure_collection(_DIM)
        info = await qdrant_client.get_collection(store.collection_name)
        assert "model_name" in info.payload_schema

    async def test_extension_declared_bool_index_is_created_on_the_server(
        self, qdrant_client: AsyncQdrantClient
    ) -> None:
        # BOOL-typed extension index (e.g. an is_installed-like flag).
        store = QdrantStore(
            client=qdrant_client,
            slug=_unique_slug(),
            extra_bool_indexes=["is_installed"],
        )
        await store.ensure_collection(_DIM)
        info = await qdrant_client.get_collection(store.collection_name)
        assert "is_installed" in info.payload_schema


class TestCollectionDim:
    """The dim accessor that feeds the startup coherence gate."""

    async def test_returns_none_when_collection_absent(self, store: QdrantStore) -> None:
        assert await store.collection_dim() is None

    async def test_returns_configured_dim_when_present(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        assert await store.collection_dim() == _DIM

    async def test_mismatch_is_detectable(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        observed = await store.collection_dim()
        assert observed is not None
        assert observed != 2048


class TestUpsertAndSearch:
    """Point persistence and nearest-neighbour retrieval on the real server."""

    async def test_upsert_then_search_finds_the_point(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        record = _record(tier=_TIER_A, file_path="src/a.py", identity="id-1")
        await store.upsert([(record, _vec(1.0))])
        hits = await store.search(_vec(1.0), k=5)
        assert any(_payload_of(hit)["file_path"] == "src/a.py" for hit in hits)

    async def test_search_respects_k_limit(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert(
            [
                (_record(tier=_TIER_A, file_path=f"src/f{seed}.py", identity=f"id-{seed}"),
                 _vec(float(seed) / 10))
                for seed in range(1, 6)
            ]
        )
        hits = await store.search(_vec(0.1), k=2)
        assert len(hits) <= 2

    async def test_search_filters_by_tier(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert(
            [
                (_record(tier=_TIER_A, file_path="src/a.py", identity="id-1"), _vec(1.0)),
                (_record(tier=_TIER_B, file_path="src/a.py", identity="id-1"), _vec(0.9)),
            ]
        )
        hits = await store.search(_vec(1.0), k=10, filters={"tier": _TIER_B})
        assert hits
        assert all(_payload_of(hit)["tier"] == _TIER_B for hit in hits)

    async def test_upsert_batches_large_input(self, qdrant_client: AsyncQdrantClient) -> None:
        store = QdrantStore(client=qdrant_client, slug=_unique_slug(), batch_size=2)
        await store.ensure_collection(_DIM)
        records = [
            (_record(tier=_TIER_A, file_path=f"src/f{seed}.py", identity=f"id-{seed}"),
             _vec(float(seed)))
            for seed in range(7)
        ]
        await store.upsert(records)
        count = await qdrant_client.count(store.collection_name)
        assert count.count == 7


class TestTierCollisionC1:
    """C1 on REAL Qdrant: one path under two tiers — both points survive."""

    async def test_same_path_two_tiers_both_survive(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        path = "models/account.py"
        record_a = _record(tier=_TIER_A, file_path=path, identity="acct")
        record_b = _record(tier=_TIER_B, file_path=path, identity="acct")
        # Distinct ids despite the identical (slug, file_path, chunk_type,
        # identity, sub_ordinal) — this is what makes both survive on the server.
        assert record_a.point_id != record_b.point_id
        await store.upsert([(record_a, _vec(1.0)), (record_b, _vec(0.99))])

        hits = await store.search(_vec(1.0), k=50)
        tiers = sorted({_payload_of(hit)["tier"] for hit in hits if _payload_of(hit)["file_path"] == path})
        assert tiers == [_TIER_B, _TIER_A]  # both tiers present for the shared path


class TestDeleteByTier:
    """The per-tier-rebuild primitive purges only one tier."""

    async def test_delete_by_tier_purges_only_that_tier(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert(
            [
                (_record(tier=_TIER_A, file_path="a.py", identity="x"), _vec(1.0)),
                (_record(tier=_TIER_A, file_path="b.py", identity="y"), _vec(0.9)),
                (_record(tier=_TIER_B, file_path="a.py", identity="x"), _vec(0.8)),
            ]
        )
        await store.delete_by_tier(_TIER_A)

        hits = await store.search(_vec(1.0), k=50)
        survivors = sorted({_payload_of(hit)["tier"] for hit in hits})
        # Only tier B remains; tier A (both files) is gone.
        assert survivors == [_TIER_B]
        # And the surviving B point for the shared path is intact.
        assert any(
            _payload_of(hit)["file_path"] == "a.py" and _payload_of(hit)["tier"] == _TIER_B
            for hit in hits
        )

    async def test_delete_missing_tier_is_a_noop(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert([(_record(tier=_TIER_A, file_path="a.py", identity="x"), _vec(1.0))])
        await store.delete_by_tier("nonexistent")  # must not raise
        hits = await store.search(_vec(1.0), k=10)
        assert any(_payload_of(hit)["tier"] == _TIER_A for hit in hits)


class TestDeleteByFile:
    """Purge-by-(tier, file) removes only the targeted tier's copy of a path."""

    async def test_purges_only_the_named_tier_and_file(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        path = "shared.py"
        await store.upsert(
            [
                (_record(tier=_TIER_A, file_path=path, identity="x"), _vec(1.0)),
                (_record(tier=_TIER_B, file_path=path, identity="x"), _vec(0.95)),
                (_record(tier=_TIER_A, file_path="other.py", identity="y"), _vec(0.9)),
            ]
        )
        # Purge ONLY tier B's copy of the shared path.
        await store.delete_by_file(_TIER_B, path)

        hits = await store.search(_vec(1.0), k=50)
        # Tier A's shared.py survives; tier A's other.py survives; tier B's
        # shared.py is gone.
        survivors = sorted(
            (_payload_of(hit)["tier"], _payload_of(hit)["file_path"]) for hit in hits
        )
        assert survivors == [(_TIER_A, "other.py"), (_TIER_A, "shared.py")]

    async def test_delete_missing_file_is_a_noop(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert([(_record(tier=_TIER_A, file_path="a.py", identity="x"), _vec(1.0))])
        await store.delete_by_file(_TIER_A, "never.py")  # must not raise
        hits = await store.search(_vec(1.0), k=10)
        assert any(_payload_of(hit)["file_path"] == "a.py" for hit in hits)


class TestDeletePoints:
    """Id-level purge — the ``upsert new BEFORE purge stale`` enabler.

    Per-file update upserts the NEW chunks first (so a concurrent reader never
    sees a gap), then purges ONLY the stale point ids (old − new). Deleting by
    ``(tier, file_path)`` would purge the just-upserted new points too; deleting
    by the explicit stale ids is what lets the new content stay continuously
    visible. This primitive is therefore distinct from ``delete_by_file``.
    """

    async def test_deletes_only_the_named_ids(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        stale = _record(tier=_TIER_A, file_path="m.py", identity="old")
        fresh = _record(tier=_TIER_A, file_path="m.py", identity="new")
        await store.upsert([(stale, _vec(1.0)), (fresh, _vec(0.9))])

        # Purge ONLY the stale id — the fresh point (same tier+file) must survive.
        await store.delete_points([stale.point_id])

        hits = await store.search(_vec(1.0), k=50)
        identities = {_payload_of(hit)["identity"] for hit in hits}
        assert "new" in identities
        assert "old" not in identities

    async def test_empty_ids_is_a_noop(self, store: QdrantStore) -> None:
        await store.ensure_collection(_DIM)
        await store.upsert([(_record(tier=_TIER_A, file_path="a.py", identity="x"), _vec(1.0))])
        await store.delete_points([])  # must not raise, must delete nothing
        hits = await store.search(_vec(1.0), k=10)
        assert any(_payload_of(hit)["identity"] == "x" for hit in hits)


class TestNoLeak:
    """Hygiene: confirm the throwaway collection is real and inspectable."""

    async def test_collection_is_listed_on_the_server(
        self, store: QdrantStore, qdrant_client: AsyncQdrantClient
    ) -> None:
        await store.ensure_collection(_DIM)
        names = {c.name for c in (await qdrant_client.get_collections()).collections}
        assert store.collection_name in names
        # Cross-check it carries the sweep-able prefix so teardown will reap it.
        assert store.collection_name.startswith("lore_test_")
