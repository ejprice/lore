"""CONTRACT tests for the memory write-through durability slice (FP-06).

Owns the headline failure mode the operator flagged as CRITICAL and PERMANENT:
the ``lore_<slug>_memory`` Qdrant collection holds USER-AUTHORED project
memories (``save_memory``) and today has **no second copy**. ``save_memory``
writes only to Qdrant; ``MemoryStore.ensure_ready`` re-creates the collection
EMPTY on startup. A Qdrant wipe therefore destroys every saved memory forever
— and, unlike code vectors, a memory cannot be re-derived from source.

The remedy the operator chose is a **SQLite write-through mirror**: every
``save_memory`` persists the memory to a local SQLite ledger on the state
volume *as the durable source of truth*, then upserts Qdrant; on startup, if
the Qdrant memory collection is empty or short, it is REBUILT by re-embedding
from the ledger. The deterministic ``uuid5`` point id (verified fact, mirrored
independently as :func:`expected_memory_id` below) means re-embedding the same
memory OVERWRITES in place, so a restore never multiplies points.

These tests pin the OBSERVABLE behaviour of the NEW API surface, written blind
to its implementation:

* ``loremaster.memory.ledger.MemoryLedger`` — a durable SQLite ledger:
  ``__init__(db_path)`` (resilient open, mirroring the manifest's posture and
  the resilient-db slice — a corrupt or missing-parent path must not crash on
  construction), ``record(*, memory_id, text, metadata, refs_stamp)`` (an
  idempotent upsert keyed by ``memory_id``), ``all_records()`` (each carrying
  ``memory_id`` / ``text`` / ``metadata`` / ``refs_stamp``), and ``count()``.
* ``MemoryStore`` gains the ledger and a write-through ``save_memory``: the
  ledger row (the durable copy) is written **even if the Qdrant upsert fails**,
  so a later restore can re-embed it.
* ``MemoryStore.restore_if_diverged()`` (async) — when ``store.count_points()``
  is below the ledger's count, re-embed ALL ledger records into the memory
  collection (deterministic ids overwrite) and return the number restored; a
  no-op (returns ``0``, embeds nothing) when already in sync.

INDEPENDENCE: behavioural expectations come from the operator's requirement,
not from any (not-yet-written) implementation. Numeric/identity oracles are
independent — the round-trip count, a recall returning the saved prose after a
wipe, and a uuid5 recomputed here from the documented convention (not read back
from the code under test).

HERMETIC HARNESS: a real local Qdrant collection (durability across a wipe is a
server-side behaviour ``:memory:`` would not faithfully exercise), the shipped
deterministic :class:`~loresigil.testing.FakeEmbedder` at the production dim,
and a ``tmp_path`` ledger db. Collection teardown reuses the concurrency-safe
exact-name tracking pattern from ``test_memory_store.py`` (NEVER the global
``lore_test_*`` prefix sweep — that would race a sibling worktree's suite on
the shared server).

RED posture: the ledger/restore APIs do not exist yet. Tests reference them so
RED surfaces behaviourally (``AttributeError`` / ``NotImplementedError`` /
``AssertionError``), coordinated with the STUB phase — not a bare top-level
``ImportError`` that would abort collection.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import Any

import pytest_asyncio

# Reuse the inherited harness URL + key reader (NOT its global-sweep teardown).
# ``conftest`` resolves as a top-level module because conftest.py inserts the
# tests dir onto ``sys.path`` (see loremaster/tests/conftest.py).
from conftest import QDRANT_URL, _qdrant_api_key
from loremaster.memory.store import MemoryRef, MemoryStore
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, VectorParams

# Production embedding dim per the owner directive (FakeEmbedder at 2048), the
# SAME value the sibling memory suite pins — not a convenience dim.
_DIM = 2048

# The memory-collection slug suffix the store appends to the project slug. This
# is the production convention (``_MEMORY_SLUG_SUFFIX`` in server.py /
# ``_MEMORY_SUFFIX`` in test_memory_store.py); duplicated here only because the
# server module is heavy to import in a unit test, and asserted-against only
# structurally (``endswith`` below), never as a hand-tuned magic value.
_MEMORY_SUFFIX = "_memory"

# --- The deterministic-id convention, reconstructed INDEPENDENTLY -----------
# These mirror store.py:211-232 (a VERIFIED FACT in the slice brief, a shared
# domain convention — the point id is uuid5(NAMESPACE_URL,
# "memory:{text}:{refs_stamp}")). They are reproduced here so the test can
# compute the expected id from the convention WITHOUT reading it back from the
# code under test (which would be tautological). If the production id scheme
# ever drifts from this, the restore-overwrite oracle below breaks loudly —
# which is the point: the ledger's refs_stamp MUST agree with the id scheme.
_ID_PREFIX = "memory"
_ID_SEPARATOR = ":"
_REF_FIELD_SEPARATOR = "@"
_REF_JOIN = ","


def expected_refs_stamp(refs: list[MemoryRef]) -> str:
    """The order-insensitive refs stamp folded into a memory's deterministic id.

    Independent reconstruction of the documented convention: each ref becomes
    ``chunk_key@key_version``, the set is sorted (order-insensitive), and joined
    by ``,``. An empty ref list stamps the empty string. This is exactly the
    ``refs_stamp`` the ledger must persist so a restore re-mints the SAME id.
    """
    stamped = sorted(
        f"{ref.chunk_key}{_REF_FIELD_SEPARATOR}{ref.key_version}" for ref in refs
    )
    return _REF_JOIN.join(stamped)


def expected_memory_id(text: str, refs: list[MemoryRef] | None = None) -> str:
    """The deterministic ``uuid5`` id for a memory, computed from the convention.

    Independent oracle for the dedup/overwrite invariants: ``uuid5(NAMESPACE_URL,
    "memory:{text}:{refs_stamp}")``. Used to assert that the ledger keys on the
    SAME id the store mints (no duplicate points on restore / repeated save).
    """
    refs_stamp = expected_refs_stamp(list(refs or ()))
    name = _ID_SEPARATOR.join((_ID_PREFIX, text, refs_stamp))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


# Production-representative memory prose — the kind of operator note that
# actually lands in this store (drawn from the project's own memory domain:
# deploy gotchas, conventions, host-specific facts). NOT ``foo``/``bar``.
MEMORY_NOTES: tuple[str, ...] = (
    "lore container runs the baked localhost/lore:latest image, not the mounted "
    "source; a loremaster fix needs an image rebuild + recreate, not a restart.",
    "PG 18 moved the data dir: mount the volume at /var/lib/postgresql, NOT "
    "/var/lib/postgresql/data, or pg_ctlcluster errors at startup.",
    "On this host `hostname -I` is GNU inetutils, not net-tools — use "
    "`ip -4 -o addr show scope global` to list LAN IPs.",
    "SELinux bind mounts need :Z (-v /host:/container:Z) or the container sees "
    "Permission denied on files it clearly owns.",
    "TEI endpoint prompts are ['query','document']; changing them needs a full "
    "reindex because v0.3.0 prompts asymmetrically.",
)

# A realistic versioned ref — a memory pointing at an indexed chunk-key, the
# migration-safe correction case. The key_version is the long-tail non-default
# value (a keying-scheme bump), not the convenience default.
CORRECTION_REF = MemoryRef(
    chunk_key="odoo:custom:models/account_move.py:symbol:AccountMove:0",
    key_version=3,
)

# A factory: build (and ``ensure_ready``) a ledger-backed MemoryStore for a slug.
EnsuredStoreFactory = Callable[[str], Awaitable[MemoryStore]]


def _unique_slug() -> str:
    """A per-test slug yielding a throwaway ``lore_test_<uuid4>_memory`` collection."""
    return f"test_{uuid.uuid4().hex}"


class CountingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that counts how many texts it embeds, document-side.

    The spy oracle for the no-op-when-in-sync and write-through-on-failure
    invariants: a restore that needlessly re-embeds every memory on every boot
    is a real bug, and the only way to prove "embedded nothing" is to watch the
    embedder. Subclasses production code (the shipped fake) so determinism /
    normalization / dim are unchanged; it only tallies calls.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.documents_embedded = 0

    async def embed_documents(self, texts: list[str]):  # type: ignore[override]
        self.documents_embedded += len(texts)
        return await super().embed_documents(texts)


@pytest_asyncio.fixture()
def ledger_path(tmp_path) -> str:
    """A throwaway SQLite ledger db path on a tmp volume (alongside a fake manifest).

    Mirrors the production layout: the manifest lives at ``<slug>.db`` and the
    memory ledger alongside at ``<slug>.memory.db`` in the state dir. The parent
    dir EXISTS here (the common case); the missing-parent / corrupt cases are
    exercised in :class:`TestLedgerResilientOpen` with their own paths.
    """
    return str(tmp_path / "lore_test.memory.db")


@pytest_asyncio.fixture()
async def embedder() -> CountingEmbedder:
    """The shipped deterministic embedder at the production dim, with a call spy."""
    return CountingEmbedder(dim=_DIM)


@pytest_asyncio.fixture()
async def tracking_client() -> AsyncIterator[AsyncQdrantClient]:
    """A real-server client whose teardown deletes ONLY the collections it created.

    Concurrency-safe by construction (the pattern from ``test_memory_store.py``):
    it never sweeps the shared ``lore_test_*`` prefix (that would race a sibling
    worktree's suite on the same server). The helper factories register every
    collection name they create on ``_tracked_collections``; teardown deletes
    exactly those, leaving foreign collections untouched and our own reaped.
    """
    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    tracked: set[str] = set()
    client._tracked_collections = tracked  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        for name in tracked:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


def make_store(
    client: AsyncQdrantClient,
    embedder: FakeEmbedder,
    slug: str,
    ledger_path: str,
) -> MemoryStore:
    """Build a ledger-backed MemoryStore over a tracked throwaway memory collection.

    The injected :class:`QdrantStore` is named for the *memory* collection
    (``lore_<slug>_memory``). The NEW contract: ``MemoryStore`` also takes a
    durable ``ledger`` (the SQLite source of truth). Keyword-only ``ledger=`` is
    proposed so the existing positional-free ``__init__(*, store, embedder)``
    signature extends without breaking call sites. The collection name is tracked
    for exact-name teardown (never a global prefix sweep).
    """
    from loremaster.memory.ledger import MemoryLedger

    inner = QdrantStore(client=client, slug=f"{slug}{_MEMORY_SUFFIX}")
    ledger = MemoryLedger(ledger_path)
    store = MemoryStore(store=inner, embedder=embedder, ledger=ledger)
    tracked: set[str] = client._tracked_collections  # type: ignore[attr-defined]
    tracked.add(store.collection_name)
    return store


async def count_points(client: AsyncQdrantClient, collection_name: str) -> int:
    """Independent point count read straight off the server (not via the store).

    The durability oracle reads Qdrant directly so it is independent of whatever
    ``store.count_points()`` reports — proving the *collection itself* holds N
    points after a restore, not merely that a store method returns N.
    """
    result = await client.count(collection_name)
    return result.count


async def wipe_collection(
    client: AsyncQdrantClient, collection_name: str, dim: int
) -> None:
    """Simulate a Qdrant wipe: DROP the memory collection and re-create it EMPTY.

    This is the headline disaster — a Qdrant data loss event. Dropping and
    recreating empty (rather than deleting points) faithfully reproduces a fresh
    container/volume loss: the collection exists at the right dim but holds zero
    memories. The ledger on the state volume survives; restore must rebuild.
    """
    await client.delete_collection(collection_name)
    await client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )


@pytest_asyncio.fixture()
async def new_memory_store(
    tracking_client: AsyncQdrantClient,
    embedder: CountingEmbedder,
    ledger_path: str,
) -> EnsuredStoreFactory:
    """A factory: build (and ``ensure_ready``) a fresh tracked ledger-backed store.

    Returning a factory (not a single store) lets a test rebuild a *second*
    store over the SAME slug + SAME ledger path (the restart simulation) — both
    share the tracking client so both names are reaped without a global sweep.
    """

    async def _factory(slug: str) -> MemoryStore:
        store = make_store(tracking_client, embedder, slug, ledger_path)
        await store.ensure_ready()
        return store

    return _factory


@pytest_asyncio.fixture()
async def memory_store(new_memory_store: EnsuredStoreFactory) -> MemoryStore:
    """A ledger-backed MemoryStore over a fresh throwaway collection, ensured."""
    return await new_memory_store(_unique_slug())


class TestWriteThroughPersistsToLedger:
    """Invariant 1 — ``save_memory`` writes the durable ledger row.

    The ledger is the source of truth a Qdrant wipe cannot touch. After a save,
    the ledger has a row for that memory whose text / metadata / refs_stamp
    round-trip. Oracle: read the ledger DIRECTLY, independent of Qdrant.
    """

    async def test_save_memory_writes_a_ledger_row(
        self, memory_store: MemoryStore
    ) -> None:
        from loremaster.memory.ledger import MemoryLedger  # noqa: F401 - API anchor

        note = MEMORY_NOTES[0]

        await memory_store.save_memory(note)

        # The durable copy exists, read off the ledger — NOT off Qdrant. One save
        # ⇒ exactly one ledger row (pure-count oracle, independent of the store).
        ledger = memory_store.ledger
        assert ledger.count() == 1
        records = ledger.all_records()
        assert any(record.text == note for record in records)

    async def test_ledger_row_round_trips_text_metadata_and_refs_stamp(
        self, memory_store: MemoryStore
    ) -> None:
        note = MEMORY_NOTES[1]
        metadata = {"author": "operator", "topic": "postgres", "severity": "high"}

        await memory_store.save_memory(note, metadata=metadata, refs=[CORRECTION_REF])

        record = next(r for r in memory_store.ledger.all_records() if r.text == note)
        # Text + caller metadata survive verbatim; a superset is fine, but the
        # pairs we put in must come back unmangled (the restore re-embeds these).
        assert record.text == note
        assert record.metadata["author"] == "operator"
        assert record.metadata["topic"] == "postgres"
        assert record.metadata["severity"] == "high"
        # The refs_stamp must equal the INDEPENDENTLY-computed stamp, so a restore
        # re-mints the SAME deterministic id. A drift here = duplicate points.
        assert record.refs_stamp == expected_refs_stamp([CORRECTION_REF])

    async def test_ledger_keys_on_the_deterministic_memory_id(
        self, memory_store: MemoryStore
    ) -> None:
        note = MEMORY_NOTES[2]

        returned_id = await memory_store.save_memory(note)

        # The id the store returns equals the convention-derived id, and the
        # ledger row is keyed on that SAME id — the seam that makes restore an
        # in-place overwrite rather than a duplicate. (Independent oracle: the
        # uuid5 recomputed here from the documented convention.)
        assert returned_id == expected_memory_id(note)
        record = next(r for r in memory_store.ledger.all_records() if r.text == note)
        assert record.memory_id == expected_memory_id(note)


class TestRestoreAfterQdrantWipe:
    """Invariant 2 (HEADLINE) — a Qdrant wipe loses ZERO memories.

    Save N memories (ledger=N, Qdrant=N) → WIPE the memory collection (drop +
    recreate empty) → restore → the memories are recallable AGAIN and the
    collection holds N points. Oracle: a recall returning the saved prose after
    the wipe, plus a direct server-side point count == ledger count == N.
    """

    async def test_restore_recovers_all_memories_after_a_full_wipe(
        self,
        memory_store: MemoryStore,
        tracking_client: AsyncQdrantClient,
    ) -> None:
        for note in MEMORY_NOTES:
            await memory_store.save_memory(note)
        saved_count = len(MEMORY_NOTES)
        collection = memory_store.collection_name

        # Sanity: before the wipe, Qdrant and the ledger agree.
        assert await count_points(tracking_client, collection) == saved_count
        assert memory_store.ledger.count() == saved_count

        # DISASTER: the Qdrant memory collection is wiped (fresh-volume loss).
        await wipe_collection(tracking_client, collection, _DIM)
        assert await count_points(tracking_client, collection) == 0

        # RECOVERY: restore from the ledger.
        restored = await memory_store.restore_if_diverged()

        # Every memory came back: the headline "zero loss" guarantee.
        assert restored == saved_count
        assert await count_points(tracking_client, collection) == saved_count
        assert memory_store.ledger.count() == saved_count

    async def test_a_wiped_memory_is_recallable_again_after_restore(
        self,
        memory_store: MemoryStore,
        tracking_client: AsyncQdrantClient,
    ) -> None:
        target = MEMORY_NOTES[3]
        for note in MEMORY_NOTES:
            await memory_store.save_memory(note)

        await wipe_collection(tracking_client, memory_store.collection_name, _DIM)
        await memory_store.restore_if_diverged()

        # The behavioural oracle: a recall of the saved prose returns that exact
        # text after the wipe. FakeEmbedder is deterministic, so a query equal to
        # the note text embeds to its vector (cosine 1.0) and ranks it first.
        recalled = await memory_store.recall_memory(target, k=5)
        assert recalled, "a restored memory must be recallable"
        assert any(item.text == target for item in recalled)

    async def test_restore_on_a_fresh_restart_store_recovers_the_ledger(
        self,
        tracking_client: AsyncQdrantClient,
        embedder: CountingEmbedder,
        ledger_path: str,
        new_memory_store: EnsuredStoreFactory,
    ) -> None:
        # Save through one store, then simulate a process RESTART against a wiped
        # Qdrant: a brand-new MemoryStore over the SAME slug + SAME ledger file.
        # This is the build_app_context re-entry the operator wires restore into.
        slug = _unique_slug()
        first = await new_memory_store(slug)
        for note in MEMORY_NOTES:
            await first.save_memory(note)
        collection = first.collection_name

        await wipe_collection(tracking_client, collection, _DIM)

        # A fresh store object (no shared in-process state) over the same ledger.
        second = make_store(tracking_client, embedder, slug, ledger_path)
        await second.ensure_ready()
        restored = await second.restore_if_diverged()

        assert restored == len(MEMORY_NOTES)
        assert await count_points(tracking_client, collection) == len(MEMORY_NOTES)


class TestRestoreIsANoOpWhenInSync:
    """Invariant 3 — restore re-embeds NOTHING when the ledger and Qdrant agree.

    Guards against a restore that re-embeds every memory on every boot (slow +
    pointless). Spy oracle: the embedder's document-embed counter must not move
    across a no-op restore, and the return value is 0.
    """

    async def test_restore_returns_zero_and_embeds_nothing_when_counts_match(
        self,
        memory_store: MemoryStore,
        embedder: CountingEmbedder,
    ) -> None:
        for note in MEMORY_NOTES:
            await memory_store.save_memory(note)
        embeds_after_save = embedder.documents_embedded

        # Counts already match (no wipe) → restore must be a pure no-op.
        restored = await memory_store.restore_if_diverged()

        assert restored == 0
        # Not a single extra document embedded — the spy proves no re-embed.
        assert embedder.documents_embedded == embeds_after_save

    async def test_restore_is_idempotent_second_call_after_recovery_is_a_noop(
        self,
        memory_store: MemoryStore,
        tracking_client: AsyncQdrantClient,
        embedder: CountingEmbedder,
    ) -> None:
        for note in MEMORY_NOTES:
            await memory_store.save_memory(note)
        await wipe_collection(tracking_client, memory_store.collection_name, _DIM)

        first_restore = await memory_store.restore_if_diverged()
        embeds_after_first = embedder.documents_embedded
        # A second restore — now back in sync — must re-embed nothing.
        second_restore = await memory_store.restore_if_diverged()

        assert first_restore == len(MEMORY_NOTES)
        assert second_restore == 0
        assert embedder.documents_embedded == embeds_after_first


class TestWriteThroughSurvivesQdrantFailure:
    """Invariant 4 — a failed Qdrant upsert still leaves the durable ledger row.

    The whole point of write-through: if Qdrant is unavailable at save time, the
    memory is NOT lost — the ledger row persists so a later restore re-embeds it.
    The contract pins ledger-first ordering as the oracle (write the durable copy
    before the volatile one), proven by injecting a permanent embed/upsert failure
    and reading the ledger back.
    """

    async def test_ledger_row_persists_when_the_qdrant_side_raises(
        self,
        tracking_client: AsyncQdrantClient,
        ledger_path: str,
    ) -> None:
        # Inject a PERMANENT failure for exactly this note on the document side
        # (FakeEmbedder.fail_inputs → None vector → save_memory raises ValueError
        # at the Qdrant-bound step). The ledger write must already have happened.
        doomed_note = MEMORY_NOTES[4]
        failing_embedder = CountingEmbedder(dim=_DIM, fail_inputs={doomed_note})
        store = make_store(tracking_client, failing_embedder, _unique_slug(), ledger_path)
        await store.ensure_ready()

        # The Qdrant-bound save fails (no usable vector). We don't assert the
        # exact exception type (that is impl-defined); we assert the SIDE EFFECT.
        with __import__("pytest").raises(Exception):
            await store.save_memory(doomed_note)

        # DURABILITY: despite the Qdrant-side failure, the ledger kept the memory,
        # so a future restore can re-embed it. Zero loss is the guarantee.
        records = store.ledger.all_records()
        assert any(record.text == doomed_note for record in records), (
            "write-through must persist the ledger row even when Qdrant upsert fails"
        )
        # And nothing reached Qdrant (the failed upsert left the collection empty).
        assert await count_points(tracking_client, store.collection_name) == 0


class TestDeterminismNoDuplicatesOnRestore:
    """Invariant 5 — restoring twice (or saving twice) never multiplies points.

    The deterministic uuid5 id means re-embedding the same memory overwrites in
    place. Saving the same prose twice collapses to one ledger row and one point;
    a restore after a wipe re-mints the same ids, so the count is exactly right.
    """

    async def test_duplicate_save_collapses_to_one_ledger_row_and_one_point(
        self,
        memory_store: MemoryStore,
        tracking_client: AsyncQdrantClient,
    ) -> None:
        note = MEMORY_NOTES[0]
        first_id = await memory_store.save_memory(note)
        second_id = await memory_store.save_memory(note)

        # Same convention-derived id both times → one ledger row, one Qdrant point.
        assert first_id == second_id == expected_memory_id(note)
        assert memory_store.ledger.count() == 1
        assert await count_points(tracking_client, memory_store.collection_name) == 1

    async def test_restore_does_not_create_duplicate_points(
        self,
        memory_store: MemoryStore,
        tracking_client: AsyncQdrantClient,
    ) -> None:
        for note in MEMORY_NOTES:
            await memory_store.save_memory(note)
        collection = memory_store.collection_name

        # Wipe then restore TWICE in a row (the second restore is a no-op once in
        # sync, but even a redundant re-embed must overwrite by deterministic id).
        await wipe_collection(tracking_client, collection, _DIM)
        await memory_store.restore_if_diverged()
        await memory_store.restore_if_diverged()

        # Exactly N points — no duplicates, no inflation past the ledger count.
        assert await count_points(tracking_client, collection) == len(MEMORY_NOTES)
        assert memory_store.ledger.count() == len(MEMORY_NOTES)


class TestRecallSemanticsUnchanged:
    """Invariant 6 — the mirror does not regress the normal save→recall path.

    A regression guard: with NO wipe, a saved memory is recallable as before,
    carries its metadata, and the deterministic-id dedup still holds. The
    write-through must be transparent to the existing flow.
    """

    async def test_saved_memory_is_recallable_without_any_wipe(
        self, memory_store: MemoryStore
    ) -> None:
        note = MEMORY_NOTES[1]
        metadata = {"author": "operator", "topic": "postgres"}
        await memory_store.save_memory(note, metadata=metadata)

        recalled = await memory_store.recall_memory(note, k=5)
        assert recalled, "a saved memory must still be recallable on the normal path"
        top = next(item for item in recalled if item.text == note)
        # Metadata still round-trips through the unchanged recall path.
        assert top.metadata["author"] == "operator"
        assert top.metadata["topic"] == "postgres"

    async def test_normal_path_does_not_diverge_so_restore_is_a_noop(
        self,
        memory_store: MemoryStore,
        embedder: CountingEmbedder,
    ) -> None:
        # After ordinary saves (no wipe), the store is in sync, so restore must
        # neither re-embed nor change the recallable set — transparency guard.
        await memory_store.save_memory(MEMORY_NOTES[2])
        embeds_after_save = embedder.documents_embedded

        assert await memory_store.restore_if_diverged() == 0
        assert embedder.documents_embedded == embeds_after_save
        recalled = await memory_store.recall_memory(MEMORY_NOTES[2], k=5)
        assert any(item.text == MEMORY_NOTES[2] for item in recalled)


class TestLedgerResilientOpen:
    """The ledger opens resiliently — a missing parent or a corrupt file.

    Mirrors the manifest's posture and the resilient-db slice: construction must
    not crash on a missing parent dir, and a corrupted ledger file is recreated
    (the durable copy degrades to empty rather than taking the process down). A
    fresh project's ledger is empty (count 0) — the inert-baseline case.
    """

    def test_open_on_a_missing_parent_dir_does_not_crash(self, tmp_path) -> None:
        from loremaster.memory.ledger import MemoryLedger

        # A path whose parent directory does not yet exist (fresh state volume).
        nested = tmp_path / "does" / "not" / "exist" / "lore_test.memory.db"
        ledger = MemoryLedger(str(nested))
        # A brand-new ledger on a fresh project is empty — the inert baseline that
        # makes restore a no-op on first boot (count 0 == Qdrant count 0).
        assert ledger.count() == 0

    def test_open_on_a_corrupt_ledger_file_recreates_it(self, tmp_path) -> None:
        from loremaster.memory.ledger import MemoryLedger

        # Pre-seed the path with garbage that is NOT a valid SQLite database.
        corrupt = tmp_path / "lore_test.memory.db"
        corrupt.write_bytes(b"this is not a sqlite database header at all\x00\xff")

        # Resilient open: recreate rather than crash; the durable copy degrades to
        # empty (a corrupt ledger has already lost its contents) but stays usable.
        ledger = MemoryLedger(str(corrupt))
        assert ledger.count() == 0
        ledger.record(
            memory_id=expected_memory_id(MEMORY_NOTES[0]),
            text=MEMORY_NOTES[0],
            metadata={"author": "operator"},
            refs_stamp=expected_refs_stamp([]),
        )
        assert ledger.count() == 1

    def test_record_is_idempotent_keyed_by_memory_id(self, tmp_path) -> None:
        from loremaster.memory.ledger import MemoryLedger

        ledger = MemoryLedger(str(tmp_path / "lore_test.memory.db"))
        note = MEMORY_NOTES[0]
        memory_id = expected_memory_id(note)

        # Recording the SAME memory_id twice upserts (one row), not appends two.
        ledger.record(memory_id=memory_id, text=note, metadata={}, refs_stamp="")
        ledger.record(memory_id=memory_id, text=note, metadata={"author": "op"}, refs_stamp="")

        assert ledger.count() == 1
        record = next(r for r in ledger.all_records() if r.memory_id == memory_id)
        # The second write wins (upsert), so the latest metadata is present.
        assert record.metadata.get("author") == "op"
