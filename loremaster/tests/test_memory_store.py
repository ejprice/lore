"""Contract tests for ``loremaster.memory.store`` against the REAL Qdrant server.

The project-memory layer generalises odoo-code's ``correction.py`` into a
domain-neutral note store: a :class:`~loremaster.memory.store.MemoryStore` over a
dedicated ``lore_<slug>_memory`` collection where **the note text itself is the
recallable content**. ``save_memory`` embeds the note (document side) and upserts
a point whose payload carries that text verbatim; ``recall_memory`` embeds a query
(query side), searches the memory collection, and returns *summarised* notes
(text + metadata + score), never a raw ``ScoredPoint`` dump.

These run against the live local Qdrant (``http://127.0.0.1:16333``), NOT
``:memory:`` — durability across two independently-constructed stores and real
nearest-neighbour ranking are server-side behaviours an in-memory backend would
not faithfully exercise. Each test uses a UNIQUE throwaway collection
(slug ``test_<uuid4>`` → collection ``lore_test_<uuid4>_memory``). The embedder is
the shipped :class:`~loresigil.testing.FakeEmbedder` at the production dim (2048).

**Concurrency-safe teardown (deliberately NOT the inherited global sweep).** A
sibling agent may be creating/deleting ``lore_test_*`` collections on this SAME
server at the same time. The inherited ``conftest.qdrant_client`` fixture tears
down by a GLOBAL ``lore_test_*`` prefix sweep — under concurrency that would
delete the *other* run's in-flight collections (and vice-versa), so a copy of
that pattern here would be mutually destructive. Instead, this module owns its
own :func:`tracking_client` fixture that records the EXACT collection names it
creates (via the :func:`new_memory_store` factory) and, on teardown, deletes only
those by name. Foreign collections are never touched, so two runs cannot corrupt
each other; this module's collections still never leak.

Pinned invariants (the Deliverable-3 *Memory* contract):

* **Note text is the recallable content.** ``save_memory(text)`` then
  ``recall_memory(query)`` returns the saved ``text`` verbatim — not an id, not a
  reference to some other chunk.
* **Round-trip carries metadata + score.** A recalled note exposes its caller
  metadata and a similarity score; it is a summarised value object, never a raw
  ``ScoredPoint``.
* **Durability.** A *second* ``MemoryStore`` constructed over the same collection
  recalls a note the first one saved (the point is persisted server-side, not
  held in process state).
* **``k`` is respected.** ``recall_memory(query, k=n)`` returns at most ``n``.
* **Versioned refs.** ``refs`` may reference chunk-keys, each carrying a
  ``key_version`` so a keying change is migratable, never a silent orphan. The
  stored note round-trips that ``(chunk_key, key_version)`` pair.
* **Relevance ranking.** A note semantically near the query ranks ABOVE an
  irrelevant note (proven with FakeEmbedder vectors whose ordering we control by
  choosing query text equal to one note's text).
* **Idempotent id.** Saving the SAME note text (+ refs) twice yields the SAME id
  and does not multiply points in the collection.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable

import pytest_asyncio

# Reuse the inherited harness's URL + key reader (NOT its global-sweep teardown).
# ``conftest`` resolves as a top-level module because conftest.py inserts the
# tests dir onto ``sys.path`` (see loremaster/tests/conftest.py).
from conftest import QDRANT_URL, _qdrant_api_key
from loremaster.memory.store import MemoryRef, MemoryStore, RecalledMemory
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import VectorParams

# Production embedding dim per the owner directive (FakeEmbedder at 2048).
_DIM = 2048

# The memory-collection slug suffix the store appends to the project slug.
_MEMORY_SUFFIX = "_memory"

# A factory that builds (and ``ensure_ready``-s) a MemoryStore over a fresh
# throwaway collection whose name is registered for exact-name teardown.
EnsuredStoreFactory = Callable[[str], Awaitable[MemoryStore]]


def _unique_slug() -> str:
    """A per-test slug yielding a throwaway ``lore_test_<uuid4>_memory`` collection."""
    return f"test_{uuid.uuid4().hex}"


@pytest_asyncio.fixture()
async def embedder() -> FakeEmbedder:
    """The shipped deterministic embedder at the production dim."""
    return FakeEmbedder(dim=_DIM)


@pytest_asyncio.fixture()
async def tracking_client() -> AsyncIterator[AsyncQdrantClient]:
    """A real-server client whose teardown deletes ONLY the collections it created.

    Concurrency-safe by construction: it never sweeps by the shared ``lore_test_*``
    prefix (that would race a sibling run on the same server). The companion
    :func:`new_memory_store`/:func:`make_store` helpers register every collection
    name they create on :attr:`AsyncQdrantClient._tracked_collections`; on exit we
    delete exactly those, leaving foreign collections untouched and our own
    reaped.
    """
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    tracked: set[str] = set()
    # Stash the tracking set on the client so helper factories can register names.
    client._tracked_collections = tracked  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        for name in tracked:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


def make_store(
    client: AsyncQdrantClient, embedder: FakeEmbedder, slug: str
) -> MemoryStore:
    """Build a MemoryStore over a throwaway memory collection AND track its name.

    The injected :class:`QdrantStore` is named for the *memory* collection
    (``lore_<slug>_memory``); ``MemoryStore`` owns no collection-naming of its own
    — it reuses the store's ensure/upsert/search verbatim. The collection name is
    registered on the tracking client so teardown deletes exactly it (never a
    global prefix sweep).
    """
    inner = QdrantStore(client=client, slug=f"{slug}{_MEMORY_SUFFIX}")
    store = MemoryStore(store=inner, embedder=embedder)
    tracked: set[str] = client._tracked_collections  # type: ignore[attr-defined]
    tracked.add(store.collection_name)
    return store


@pytest_asyncio.fixture()
async def new_memory_store(
    tracking_client: AsyncQdrantClient, embedder: FakeEmbedder
) -> EnsuredStoreFactory:
    """A factory: build (and ``ensure_ready``) a fresh tracked MemoryStore for ``slug``.

    Returning a factory (rather than a single store) lets the durability test
    build a *second* store over the *same* slug — both share the tracking client,
    so both names (identical here) are reaped without a global sweep.
    """

    async def _factory(slug: str) -> MemoryStore:
        store = make_store(tracking_client, embedder, slug)
        await store.ensure_ready()
        return store

    return _factory


@pytest_asyncio.fixture()
async def memory_store(new_memory_store: EnsuredStoreFactory) -> MemoryStore:
    """A MemoryStore over a fresh throwaway memory collection, collection ensured."""
    return await new_memory_store(_unique_slug())


class TestCollectionNaming:
    """The memory collection is dedicated and ``_memory``-suffixed."""

    async def test_collection_name_is_lore_slug_memory(
        self, memory_store: MemoryStore
    ) -> None:
        # ``lore_`` prefix (the QdrantStore convention) + the ``_memory`` suffix.
        assert memory_store.collection_name.startswith("lore_test_")
        assert memory_store.collection_name.endswith("_memory")


class TestEnsureReady:
    """The collection is created at the embedder's dim (COSINE)."""

    async def test_ensure_ready_creates_collection_at_embedder_dim(
        self, tracking_client: AsyncQdrantClient, embedder: FakeEmbedder
    ) -> None:
        store = make_store(tracking_client, embedder, _unique_slug())
        await store.ensure_ready()
        info = await tracking_client.get_collection(store.collection_name)
        # Single unnamed vector config sized to the embedder dim. Narrow the union
        # (lore never uses named vectors) so the size read is type-safe.
        vectors = info.config.params.vectors
        assert isinstance(vectors, VectorParams)
        assert vectors.size == _DIM


class TestSaveRecallRoundTrip:
    """The note text is the recallable content."""

    async def test_recall_returns_the_saved_note_text(
        self, memory_store: MemoryStore
    ) -> None:
        note = "The snapshot root is bind-mounted read-only; never write through it."
        await memory_store.save_memory(note)
        recalled = await memory_store.recall_memory(note, k=5)
        assert recalled, "a saved note must be recallable"
        assert any(item.text == note for item in recalled)

    async def test_recall_returns_summarised_value_objects_not_raw_points(
        self, memory_store: MemoryStore
    ) -> None:
        note = "Versioned keys keep a correction migratable instead of orphaned."
        await memory_store.save_memory(note)
        recalled = await memory_store.recall_memory(note, k=5)
        # A summarised value object: typed text + score, never a raw ScoredPoint.
        assert all(isinstance(item, RecalledMemory) for item in recalled)
        top = next(item for item in recalled if item.text == note)
        assert isinstance(top.score, float)

    async def test_recall_carries_caller_metadata(
        self, memory_store: MemoryStore
    ) -> None:
        note = "Prefer SDKs over homegrown solutions; reuse code."
        metadata = {"author": "lore", "topic": "style"}
        await memory_store.save_memory(note, metadata=metadata)
        recalled = await memory_store.recall_memory(note, k=5)
        top = next(item for item in recalled if item.text == note)
        # Caller metadata round-trips intact (a superset is fine; the pair we put
        # in must come back out, unmangled).
        assert top.metadata["author"] == "lore"
        assert top.metadata["topic"] == "style"

    async def test_save_memory_returns_a_uuid_id(
        self, memory_store: MemoryStore
    ) -> None:
        note = "Silent on success, loud on failure."
        memory_id = await memory_store.save_memory(note)
        # A canonical UUID string (uuid5 over the note + stamp).
        assert str(uuid.UUID(memory_id)) == memory_id


class TestDurability:
    """A second store over the SAME collection recalls a note the first saved."""

    async def test_second_store_recalls_first_stores_note(
        self,
        tracking_client: AsyncQdrantClient,
        embedder: FakeEmbedder,
        new_memory_store: EnsuredStoreFactory,
    ) -> None:
        slug = _unique_slug()
        first = await new_memory_store(slug)
        note = "Durability: the point is persisted server-side, not in process state."
        await first.save_memory(note)

        # A brand-new MemoryStore object over the same collection — no shared
        # in-process state (a fresh QdrantStore on the same client + slug). It
        # must still recall the persisted note.
        second = make_store(tracking_client, embedder, slug)
        recalled = await second.recall_memory(note, k=5)
        assert any(item.text == note for item in recalled)


class TestKLimit:
    """``recall_memory`` honours the ``k`` ceiling."""

    async def test_recall_respects_k_limit(self, memory_store: MemoryStore) -> None:
        for index in range(6):
            await memory_store.save_memory(f"distinct memory note number {index}")
        recalled = await memory_store.recall_memory("memory note", k=2)
        assert len(recalled) <= 2


class TestVersionedRefs:
    """A ref references a chunk-key carrying a migration-safe ``key_version``."""

    async def test_ref_round_trips_chunk_key_and_key_version(
        self, memory_store: MemoryStore
    ) -> None:
        note = "This query should match account.move, not account.account."
        ref = MemoryRef(chunk_key="odoo:custom:models/account.py:symbol:AccountMove:0", key_version=3)
        await memory_store.save_memory(note, refs=[ref])
        recalled = await memory_store.recall_memory(note, k=5)
        top = next(item for item in recalled if item.text == note)
        assert len(top.refs) == 1
        # Both the key AND its version survive the round-trip — the key_version is
        # what makes a keying change migratable rather than a silent orphan.
        assert top.refs[0].chunk_key == ref.chunk_key
        assert top.refs[0].key_version == 3

    def test_memory_ref_defaults_key_version_to_the_base_default(self) -> None:
        # A ref with no explicit version stamps the base DEFAULT_KEY_VERSION, so a
        # ref is never silently unversioned.
        from loremaster.extension import DEFAULT_KEY_VERSION

        ref = MemoryRef(chunk_key="some:key")
        assert ref.key_version == DEFAULT_KEY_VERSION


class TestRelevanceRanking:
    """A note near the query outranks an irrelevant note."""

    async def test_relevant_note_ranks_above_irrelevant(
        self, memory_store: MemoryStore
    ) -> None:
        relevant = "Qdrant payload indexes are no-ops on the in-memory backend."
        irrelevant = "The kitchen sink faucet drips on alternate Tuesdays."
        await memory_store.save_memory(relevant)
        await memory_store.save_memory(irrelevant)

        # FakeEmbedder is deterministic: a query equal to the relevant note's text
        # embeds to that note's exact vector (cosine 1.0), so it MUST rank first.
        recalled = await memory_store.recall_memory(relevant, k=2)
        assert recalled
        assert recalled[0].text == relevant
        # And it is strictly more similar than the irrelevant note (independent
        # ordering oracle: identical-text cosine == 1.0 > any distinct vector).
        scores = {item.text: item.score for item in recalled}
        if irrelevant in scores:
            assert scores[relevant] > scores[irrelevant]


class TestIdempotentId:
    """Saving the same note (+ refs) twice does not multiply points."""

    async def test_same_note_twice_yields_same_id(
        self, memory_store: MemoryStore
    ) -> None:
        note = "Idempotency: a duplicate note collapses onto the same point id."
        first_id = await memory_store.save_memory(note)
        second_id = await memory_store.save_memory(note)
        assert first_id == second_id

    async def test_duplicate_note_does_not_multiply_points(
        self, memory_store: MemoryStore, tracking_client: AsyncQdrantClient
    ) -> None:
        note = "Saved three times, counted once."
        await memory_store.save_memory(note)
        await memory_store.save_memory(note)
        await memory_store.save_memory(note)
        count = await tracking_client.count(memory_store.collection_name)
        assert count.count == 1

    async def test_same_note_different_refs_is_a_distinct_memory(
        self, memory_store: MemoryStore, tracking_client: AsyncQdrantClient
    ) -> None:
        # The id folds in the refs, so the same prose pointing at a DIFFERENT chunk
        # is a genuinely different memory (two distinct corrections), not a clobber.
        note = "Same prose, different target chunk."
        await memory_store.save_memory(
            note, refs=[MemoryRef(chunk_key="mod:tier:a.py:sym:A:0", key_version=1)]
        )
        await memory_store.save_memory(
            note, refs=[MemoryRef(chunk_key="mod:tier:b.py:sym:B:0", key_version=1)]
        )
        count = await tracking_client.count(memory_store.collection_name)
        assert count.count == 2
