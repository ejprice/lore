"""Contract pins for the P7 CUTOVER — the server + boot move off the Qdrant
``MemoryStore`` onto the SurrealDB ``LocalMemoryBackend``, and the fleet
task ledger lands on ``AppContext``.

This file owns the WIRING + BOOT-MIGRATION half of the cutover (the tool-surface
half — the ``save_memory`` / ``recall_memory`` handler re-shape and the two new
``lore_claim_task`` / ``lore_tasks`` tools — is pinned in ``test_mcp_server.py``).

The pinned contract (decided by the CONTRACT phase, blind to the implementation):

* **AppContext wiring (contract §3).** A built :class:`~loremaster.server.AppContext`
  gains a ``memory_backend`` conforming to the
  :class:`~loremaster.memory.backend.MemoryBackend` protocol and a ``task_ledger``
  that is a :class:`~loremaster.tasks.TaskLedger`; it LOSES the vestigial ``store``
  attribute and the ``_memory_store_handle`` (both are dead weight after the read
  path moved to the unified SurrealDB store and memory moved to the backend). The
  Qdrant probe-gate path is UNCHANGED and is NOT pinned here.

* **Boot ledger restore (contract §4 — the load-bearing pin).** A durable
  :class:`~loremaster.memory.ledger.MemoryLedger` pre-populated (in the v0.3
  ``text`` / ``metadata`` / ``refs_stamp`` shape) BEFORE the server boots — with
  NO SurrealDB memory rows yet — is fully recallable through the new backend's
  recall path AFTER ``build_app_context`` (``restore_from_ledger`` ran once at
  boot). A SECOND boot over the same database + ledger re-embeds NOTHING (the
  FP-06 divergence guard: an in-sync store is a pure no-op, zero document
  embeds), observed through a counting embedder.

These are REAL-INFRA tests (Qdrant at ``127.0.0.1:16333`` + the SurrealDB dev
harness at ``ws://127.0.0.1:18000/rpc``): they drive the genuine
``build_app_context`` boot, the real seam where a unit/scale/restore bug lives —
mocks on each side would miss the producer↔consumer handoff (the durable ledger's
v0.3 row shape crossing into the backend's replay).

How to run:
    PP=<worktree>/loremaster:<worktree>/loresigil:<worktree>/lorescribe
    cd <worktree>/loremaster
    SURREAL_USER=root SURREAL_PASS=spikeroot PYTHONPATH=$PP \\
        uv run --frozen pytest tests/test_memory_cutover.py -q
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    drop_database as drop_surreal_database,
)
from _surreal_harness import (
    make_env,
    surreal_password,
    surreal_url,
    surreal_user,
)
from loremaster.config import LoreConfig
from loremaster.memory.backend import MemoryBackend, derive_memory_id, derive_refs_stamp
from loremaster.memory.ledger import MemoryLedger
from loremaster.server import AppContext, LoreServer, build_app_context
from loremaster.tasks import TaskLedger
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# The production embedding dimensionality every FakeEmbedder fixture uses.
_DIM = 2048

# The namespace every throwaway per-test SurrealDB database lives under (mirrors
# ``test_mcp_server.py`` / ``test_cli.py`` — one shared namespace per dev server).
_SURREAL_TEST_NAMESPACE = "lore_test"

# The env-var NAMES the default SurrealConfig references credentials by — matching
# the production default config so the real ``build_app_context`` resolves them.
_SURREAL_USER_ENV = "SURREAL_USER"
_SURREAL_PASS_ENV = "SURREAL_PASS"


# --------------------------------------------------------------------------- #
# Per-test slug tracking + SurrealDB credential export / database reap.
# --------------------------------------------------------------------------- #
_pending_surreal_slugs: list[str] = []


def _slug() -> str:
    """A unique per-test slug — ALSO the throwaway SurrealDB database name."""
    slug = f"test_{uuid.uuid4().hex}"
    _pending_surreal_slugs.append(slug)
    return slug


@pytest_asyncio.fixture(autouse=True)
async def _surreal_test_env(monkeypatch: pytest.MonkeyPatch) -> AsyncIterator[None]:
    """Export the harness root credentials; reap every slug-named database."""
    monkeypatch.setenv(_SURREAL_USER_ENV, surreal_user())
    monkeypatch.setenv(_SURREAL_PASS_ENV, surreal_password())
    try:
        yield
    finally:
        for slug in _pending_surreal_slugs:
            await drop_surreal_database(make_env(database=slug, dim=_DIM))
        _pending_surreal_slugs.clear()


@pytest_asyncio.fixture()
async def qdrant() -> AsyncIterator[AsyncQdrantClient]:
    """A real Qdrant client with exact-name (concurrency-safe) teardown.

    Registers created project + ``<name>_memory`` collections on ``_lore_created``
    for exact-name reaping — mirrors ``test_mcp_server.py``'s identical fixture.
    """
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []
    client._lore_created = created  # type: ignore[attr-defined]
    try:
        yield client
    finally:
        for name in created:
            for candidate in (name, f"{name}_memory"):
                if await client.collection_exists(candidate):
                    await client.delete_collection(candidate)
        await client.close()


def _config(slug: str, live_path: Path) -> LoreConfig:
    """A validated config with an explicit ``surreal`` block on the dev harness.

    ``surreal.database`` is left UNSET so it derives from the (uuid4-unique) slug —
    every ``build_app_context`` in this test writes its own throwaway database.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://localhost:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "surreal": {
            "url": surreal_url(),
            "namespace": _SURREAL_TEST_NAMESPACE,
            "user_env": _SURREAL_USER_ENV,
            "password_env": _SURREAL_PASS_ENV,
        },
        "roots": [
            {"tier": "custom", "watch": "live", "path": str(live_path), "include": ["**/*.py"]}
        ],
        "include": [],
        "exclude_dirs": [".git"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9244},
    }
    return LoreConfig.model_validate(payload)


class _CountingEmbedder(FakeEmbedder):
    """A :class:`FakeEmbedder` that counts ``embed_documents`` calls (the boot spy).

    The FP-06 divergence guard is observable ONLY through the DOCUMENT-embed side:
    a restore re-embeds each replayed ledger row document-side, so ``embed_doc_calls``
    is the independent oracle for "how much work did this boot's restore actually
    do". Opts out of the grouped/contextualized path so every embed flows through
    this counted method.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.embed_doc_calls = 0

    @property
    def supports_contextualized(self) -> bool:
        """Instrument the FLAT embed path — opt out of grouped dispatch."""
        return False

    async def embed_documents(self, texts: list[str]) -> Any:
        self.embed_doc_calls += 1
        return await super().embed_documents(texts)


async def _build(
    config: LoreConfig,
    *,
    client: AsyncQdrantClient,
    manifest_path: Path,
    snapshot_root: Path,
    embedder: FakeEmbedder | None = None,
) -> AppContext:
    """Drive the REAL ``build_app_context`` boot (mirrors ``test_mcp_server._make_context``).

    Registers the project + ``_memory`` Qdrant collection names for the fixture's
    exact-name reap. ``start_tasks=False`` gives the watcher-free boot path while
    still running the memory-boot (ledger restore) wiring under test.
    """
    slug = config.project.slug
    client._lore_created.append(f"lore_{slug}")  # type: ignore[attr-defined]
    client._lore_created.append(f"lore_{slug}_memory")  # type: ignore[attr-defined]
    return await build_app_context(
        server=LoreServer(config),
        embedder=embedder or FakeEmbedder(dim=_DIM),
        qdrant_client=client,
        manifest_path=manifest_path,
        snapshot_root=snapshot_root,
        start_tasks=False,
    )


def _ledger_path(manifest_path: Path, slug: str) -> Path:
    """The durable-ledger path ``build_app_context`` derives from the manifest path.

    Production sites the ledger alongside the manifest at ``<slug>.memory.db``
    (see ``build_app_context``'s ``manifest_path.with_name(...)``) — this is the
    SAME source of truth, so a pre-seeded ledger here is the exact file the boot
    restore reads (clause 5: no hand-copied path literal).
    """
    return manifest_path.with_name(f"{slug}.memory.db")


# --------------------------------------------------------------------------- #
# A realistic project-memory note (a durable correction about THIS codebase —
# not a foo/bar synthetic). Its deterministic id is minted via the SAME
# production helper the ledger + backend both use, so a wrong id here would be a
# wrong id in the shared source of truth, never a fake-only drift (clause 5).
# --------------------------------------------------------------------------- #
_SEED_MEMORY_TEXT = "the champion routing warehouse curve lives in pkg/routing.py, not pricing.py"
_SEED_MEMORY_METADATA: dict[str, Any] = {"topic": "routing"}  # v0.3 free-form metadata shape
# A SECOND note so a restore has more than one row to replay (a non-degenerate
# driver table — an "inert on a single row" bug cannot hide).
_SEED_MEMORY_TEXT_2 = "quarterly tiered pricing is computed in pkg/pricing.py by quarterly_pricing"


def _seed_ledger(path: Path) -> list[str]:
    """Write the two seed notes into a fresh v0.3-shape ledger; return their ids.

    Rows are written DIRECTLY via :class:`MemoryLedger` in the v0.3 shape (text /
    metadata / refs_stamp, no v2 wire fields) — the exact legacy shape a pre-P7
    deploy left on disk, so the boot restore exercises the real pre-v2 default-fill
    path. Each ``memory_id`` is the production deterministic id for its (text,
    refs) so the restore keys + re-mints in place.
    """
    ledger = MemoryLedger(str(path))
    ids: list[str] = []
    try:
        for text in (_SEED_MEMORY_TEXT, _SEED_MEMORY_TEXT_2):
            refs_stamp = derive_refs_stamp([])  # no refs → the empty stamp
            memory_id = derive_memory_id(text, refs_stamp)
            ledger.record(
                memory_id=memory_id,
                text=text,
                metadata=_SEED_MEMORY_METADATA,
                refs_stamp=refs_stamp,
            )
            ids.append(memory_id)
    finally:
        ledger.close()
    return ids


# =========================================================================== #
# Contract §3 — AppContext gains memory_backend + task_ledger; loses store +
# _memory_store_handle.
# =========================================================================== #
class TestAppContextCutoverWiring:
    """A built AppContext carries the SurrealDB memory backend + the task ledger,
    and no longer holds the vestigial Qdrant read handle / memory-store handle."""

    @pytest_asyncio.fixture()
    async def built_context(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> AsyncIterator[AppContext]:
        """A real AppContext over an EMPTY corpus (memory + task wiring only)."""
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)  # empty — the wiring is corpus-independent
        config = _config(slug, live)
        ctx = await _build(
            config, client=qdrant, manifest_path=tmp_path / "m.db",
            snapshot_root=tmp_path / "snap",
        )
        try:
            yield ctx
        finally:
            await ctx.aclose()

    async def test_app_context_exposes_a_memory_backend(
        self, built_context: AppContext
    ) -> None:
        # The cutover replaces the Qdrant MemoryStore with a MemoryBackend-shaped
        # object the pipeline + memory tools dispatch through.
        backend = getattr(built_context, "memory_backend", None)
        assert backend is not None, "AppContext must expose a 'memory_backend' after the cutover"
        # runtime_checkable structural check: it satisfies the backend protocol
        # (remember / recall / invalidate / restore_from_ledger / ensure_ready).
        assert isinstance(backend, MemoryBackend), (
            "AppContext.memory_backend must conform to the MemoryBackend protocol"
        )

    async def test_app_context_exposes_a_task_ledger(
        self, built_context: AppContext
    ) -> None:
        # The fleet-coordination spine: the two new task tools ride this ledger.
        ledger = getattr(built_context, "task_ledger", None)
        assert ledger is not None, "AppContext must expose a 'task_ledger' after the cutover"
        assert isinstance(ledger, TaskLedger), (
            "AppContext.task_ledger must be a TaskLedger over the unified SurrealDB store"
        )

    async def test_app_context_drops_vestigial_store_attribute(
        self, built_context: AppContext
    ) -> None:
        # The read path moved to the unified SurrealDB store (``write_store``); the
        # legacy Qdrant read handle ``store`` is dead weight the cutover removes.
        assert not hasattr(built_context, "store"), (
            "the vestigial Qdrant read handle 'store' must be gone after the cutover"
        )

    async def test_app_context_drops_memory_store_handle(
        self, built_context: AppContext
    ) -> None:
        # The Qdrant memory collection handle is gone with the MemoryStore it fed.
        assert not hasattr(built_context, "_memory_store_handle"), (
            "the Qdrant '_memory_store_handle' must be gone after the memory cutover"
        )


# =========================================================================== #
# Contract §4 — BOOT MIGRATION: a pre-populated durable ledger is recallable
# through the new backend after boot; a second boot re-embeds nothing.
# =========================================================================== #
class TestBootLedgerRestore:
    """A durable ledger seeded BEFORE boot survives into the SurrealDB backend and
    is recallable; a second boot is an inert no-op (the FP-06 divergence guard)."""

    async def test_prepopulated_ledger_is_recallable_after_boot(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # Arrange: seed the durable ledger (v0.3 shape) at the path the boot reads,
        # with NO SurrealDB memory rows yet — the legacy-restore precondition.
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)  # empty corpus: only memory restore embeds
        manifest_path = tmp_path / "m.db"
        seeded_ids = _seed_ledger(_ledger_path(manifest_path, slug))
        assert len(seeded_ids) == 2, "test setup: two durable rows must be seeded"

        config = _config(slug, live)
        ctx = await _build(
            config, client=qdrant, manifest_path=manifest_path, snapshot_root=tmp_path / "snap"
        )
        try:
            backend = getattr(ctx, "memory_backend", None)
            assert backend is not None, (
                "the boot must expose a memory_backend the restored notes live in"
            )
            # Act: recall by the exact seed text — under the deterministic
            # FakeEmbedder the query embeds to the stored note's own vector (cosine
            # 1.0), an independent ranking oracle. The restore ran at boot, so the
            # note is present WITHOUT this test ever calling save_memory.
            recalled = await getattr(ctx, "memory_backend").recall(_SEED_MEMORY_TEXT, k=5)

            # Assert: the seeded note is recalled (the boot restore replayed it into
            # the SurrealDB backend). The FIRST seed carries the query's own text.
            recalled_texts = [getattr(memory, "text", "") for memory in recalled]
            assert any(_SEED_MEMORY_TEXT in text for text in recalled_texts), (
                "a memory pre-seeded in the durable ledger must be recallable after "
                f"boot (restore_from_ledger ran once); recalled texts were {recalled_texts!r}"
            )
            # Sanity bound (clause 4): recall returns a bounded, non-negative number
            # of notes (never a flood) — at most the two seeded rows under k=5.
            assert 0 < len(recalled) <= 2, (
                f"recall must return the bounded seeded set, got {len(recalled)}"
            )
        finally:
            await ctx.aclose()

    async def test_second_boot_over_synced_store_reembeds_nothing(
        self, tmp_path: Path, qdrant: AsyncQdrantClient
    ) -> None:
        # Arrange: the SAME slug (⇒ same SurrealDB database) + the SAME manifest path
        # (⇒ same durable ledger) across two boots, so the second boot finds the
        # store already covers the ledger — the steady-state restart the guard pins.
        slug = _slug()
        live = tmp_path / "live"
        live.mkdir(parents=True, exist_ok=True)  # empty corpus: the ONLY embeds are memory restore
        manifest_path = tmp_path / "m.db"
        snapshot_root = tmp_path / "snap"
        _seed_ledger(_ledger_path(manifest_path, slug))
        config = _config(slug, live)

        # Boot 1: the restore re-embeds the seeded rows document-side.
        first_embedder = _CountingEmbedder(dim=_DIM)
        first_ctx = await _build(
            config, client=qdrant, manifest_path=manifest_path,
            snapshot_root=snapshot_root, embedder=first_embedder,
        )
        await first_ctx.aclose()  # persists the SurrealDB database (never dropped here)
        assert first_embedder.embed_doc_calls >= 1, (
            "the FIRST boot must re-embed the seeded ledger rows (restore did real work)"
        )

        # Boot 2: same database + ledger ⇒ the store already covers the ledger.
        second_embedder = _CountingEmbedder(dim=_DIM)
        second_ctx = await _build(
            config, client=qdrant, manifest_path=manifest_path,
            snapshot_root=snapshot_root, embedder=second_embedder,
        )
        try:
            backend = getattr(second_ctx, "memory_backend", None)
            assert backend is not None, "the second boot must still expose a memory_backend"
            # The divergence guard: an in-sync store re-embeds NOTHING at boot — a
            # zero-embed magnitude bound (clause 4) that catches a re-embed-everything
            # regression (which would make every restart O(catalog) embeds).
            assert second_embedder.embed_doc_calls == 0, (
                "a SECOND boot over an already-synced store + ledger must re-embed "
                f"NOTHING (the FP-06 divergence guard); got {second_embedder.embed_doc_calls} "
                "document-embed calls"
            )
            # And the memory is still recallable (the second boot did not lose it).
            recalled = await getattr(second_ctx, "memory_backend").recall(_SEED_MEMORY_TEXT, k=5)
            assert any(_SEED_MEMORY_TEXT in getattr(m, "text", "") for m in recalled), (
                "the seeded memory must still be recallable after the inert second boot"
            )
        finally:
            await second_ctx.aclose()
