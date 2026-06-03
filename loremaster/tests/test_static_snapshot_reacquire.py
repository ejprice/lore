"""Contract tests for FP-05 — static-tier snapshot RE-ACQUIRE when the
materialisation dir is gone.

These tests are a CONTRACT for a fix that does NOT yet exist. They are expected
to be RED (an ``AssertionError`` / ``ReadFileError`` / ``FileNotFoundError``)
until the implementation is written. They are written blind to the future
implementation — the behavioural expectations come from the requirement, not
from how ``_index_static_tier`` happens to behave today.

The bug (current behaviour, the thing this contract forbids):
    ``Indexer._index_static_tier`` is version-stamp gated. A manifest stamp
    (``tier_version:<tier>``) that MATCHES the tier's configured version SKIPS
    the tier with ZERO walk and ZERO acquisition — WITHOUT checking that the
    snapshot materialisation dir (``SnapshotLayout.materialization_dir(tier)``)
    still exists on disk. If the snapshot dir is lost (a container/volume event)
    while the stamp survives in the manifest DB, the tier is skipped, the
    snapshot is never re-materialised, and ``read_file(static_tier, ...)`` fails
    for every path — the index claims the tier is current while its files are
    physically gone.

The invariant this contract pins:
    * matching stamp + PRESENT (non-empty) snapshot dir  → SKIP (zero walk, zero
      acquire — today's optimisation, preserved).
    * matching stamp + ABSENT or EMPTY snapshot dir       → RE-ACQUIRE (the
      provider re-materialises the dir; ``read_file`` works again).

The setup deliberately MIRRORS the existing static-tier fixtures in
``test_indexer.py`` (``_build_static_source`` / ``_config`` / ``_make_indexer`` /
``ExplodingProvider`` / ``TestStaticTierFreshness``) so the fixtures stay grounded
in the production-realistic config + provider wiring (clause 5: same source of
truth as the existing suite and as the CLI's composition).

How to run:
    PP=<worktree>/loremaster:<worktree>/loresigil:<worktree>/lorescribe
    cd <worktree>/loremaster
    PYTHONPATH=$PP /home/ejprice/PycharmProjects/lore/.venv/bin/python \\
        -m pytest tests/test_static_snapshot_reacquire.py -q -p no:cacheprovider
"""

from __future__ import annotations

import shutil
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

# Production symbols — imported freely to ground fixtures in the real config /
# indexer / snapshot-layout conventions (clause 5). None of these is the
# not-yet-built fix; the fix lives INSIDE _index_static_tier, whose public
# contract (index_tier) is exercised here without naming any new private symbol.
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.manifest import Manifest
from loremaster.read_file import FileSpan, ReadFileError, ReadFileTool
from loremaster.server import LoreServer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.source.snapshot import SnapshotLayout
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# Production embedding dimensionality — every FakeEmbedder fixture uses it
# (clause 1: real scale, not a convenience value). Same as test_indexer.py.
_DIM = 2048

# Production-canonical TEI config values (same as test_indexer.py — clause 5).
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# The static tier under test and its configured version. A real Odoo-style
# series string (the production shape for a static tier's version) rather than a
# round synthetic — the stamp is an opaque string compared for equality, so the
# realistic value documents intent without changing the logic (clause 1).
_STATIC_TIER = "community"
_STATIC_VERSION = "15.0.1"

# The tier-relative path the provider materialises and the contract reads back.
# Mirrors test_indexer.py's _build_static_source layout exactly (clause 5).
_STATIC_FILE_REL = "lib/core.py"


# A real Python module the python_ast chunker splits into multiple chunks
# (imports + class + method + function) — identical to test_indexer.py's
# corpus so the static tier is chunked for real, not stubbed (clause 1).
_PY_MODULE = """\
import os

class Widget:
    \"\"\"A widget.\"\"\"

    def render(self, value):
        return os.linesep.join(str(value))


def make_widget():
    return Widget()
"""


def _write(path: Path, text: str) -> None:
    """Create parents and write ``text`` to ``path`` (UTF-8)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_static_source(root: Path) -> None:
    """Build a small static-tier source tree the provider materialises.

    Mirrors ``test_indexer.py._build_static_source`` so the snapshot the provider
    writes is the SAME realistic shape the existing static-tier suite uses.
    """
    _write(root / _STATIC_FILE_REL, _PY_MODULE)


def _slug() -> str:
    """A per-test slug → throwaway ``lore_test_<uuid4>`` collection."""
    return f"test_{uuid.uuid4().hex}"


def _config(*, slug: str, static_source: Path, static_version: str = _STATIC_VERSION) -> LoreConfig:
    """Build a validated :class:`LoreConfig` with a single STATIC tier.

    Mirrors the static-root shape of ``test_indexer.py._config`` (clause 5): a
    ``community`` tier, ``watch: static``, ``provider: local_directory``, a
    version string, and ``**/*.py`` includes. The embedding block carries the
    production-realistic TEI values so the fingerprint / chunker wiring is real.
    """
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": _TEI_BASE_URL,
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _DIM,
            "truncate": False,
            "max_input_tokens": 8192,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": _TEI_KEY_ENV,
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        "roots": [
            {
                "tier": _STATIC_TIER,
                "watch": "static",
                "source": str(static_source),
                "version": static_version,
                "provider": "local_directory",
                "include": ["**/*.py"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js"],
        "chunkers": {".py": {"chunker": "python_ast"}, ".md": {"chunker": "markdown"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


class _CountingProvider:
    """A ``SourceProvider`` that DELEGATES to the real local-directory provider
    and COUNTS how many times ``acquire`` is called.

    The oracle for "was the tier re-acquired?" is ``acquire_calls`` — an
    independent observation of the production seam (the provider boundary), not a
    restatement of the indexer's internal branch. Delegating to the real
    :class:`LocalDirectorySourceProvider` means a counted acquire ACTUALLY
    re-materialises the snapshot dir on disk, so the downstream ``read_file``
    assertion exercises the genuine end-to-end handoff (clause 3: real seam).
    """

    def __init__(self, tier: str, source: Path) -> None:
        self.tier = tier
        self._delegate = LocalDirectorySourceProvider(tier, source)
        self.acquire_calls = 0

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        self.acquire_calls += 1
        self._delegate.acquire(tier, snapshot_root)


class _ExplodingProvider:
    """A ``SourceProvider`` whose ``acquire`` raises if EVER called.

    Mirrors ``test_indexer.py.ExplodingProvider`` (clause 5). Proves the
    matching-stamp + PRESENT-snapshot path STILL skips with zero acquisition —
    the optimisation the fix must not regress: calling acquire is the failure
    signal.
    """

    def __init__(self, tier: str) -> None:
        self.tier = tier
        self.acquired = False

    def acquire(self, tier: str, snapshot_root: Path) -> None:
        self.acquired = True
        raise AssertionError(
            f"acquire({tier!r}) must NOT run when the stamp matches AND the "
            f"snapshot materialisation dir is present"
        )


@pytest_asyncio.fixture()
async def store_factory() -> AsyncIterator[Any]:
    """Build :class:`QdrantStore` instances with concurrency-safe exact-name teardown.

    Same pattern as ``test_indexer.py`` — owns its own client and deletes ONLY
    the exact collection names this test created (never a prefix sweep), so a
    sibling agent's ``lore_test_*`` collections are never reaped (clause 5).
    """
    from conftest import QDRANT_URL, _qdrant_api_key

    client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
    created: list[str] = []

    def _make(slug: str) -> QdrantStore:
        store = QdrantStore(client=client, slug=slug)
        created.append(store.collection_name)
        return store

    try:
        yield _make
    finally:
        for name in created:
            if await client.collection_exists(name):
                await client.delete_collection(name)
        await client.close()


def _make_indexer(
    *,
    config: LoreConfig,
    store: QdrantStore,
    embedder: Any,
    manifest: Manifest,
    snapshot_root: Path,
    providers: list[Any] | None = None,
) -> Indexer:
    """Wire an :class:`Indexer` exactly as the CLI does (composed registry/providers).

    Mirrors ``test_indexer.py._make_indexer`` (clause 5). When ``providers`` is
    given it REPLACES the built-in per-static-root provider wiring, so a test can
    inject a counting / exploding provider to observe the acquire seam.
    """
    server = LoreServer(config)
    if providers is None:
        providers = list(server.source_providers)
        for root in config.roots:
            if root.watch == "static" and root.source is not None:
                providers.append(LocalDirectorySourceProvider(root.tier, Path(root.source)))
    return Indexer(
        store=store,
        embedder=embedder,
        manifest=manifest,
        registry=server.registry,
        source_providers=providers,
        config=config,
        snapshot_root=snapshot_root,
    )


def _read_file_tool(config: LoreConfig, snapshot_root: Path) -> ReadFileTool:
    """A :class:`ReadFileTool` wired exactly as ``build_app_context`` wires it.

    Reuses the SAME live-root / snapshot-layout / known-tier composition the
    server uses (clause 5), so the ``read_file`` assertion exercises the real
    consumer of the snapshot dir — not a hand-rolled stand-in. For a
    static-only config there are no live roots; the static tier is read through
    :meth:`SnapshotLayout.resolve` against the materialisation dir.
    """
    snapshot_layout = SnapshotLayout(snapshot_root)
    live_roots = {
        root.tier: Path(root.path)
        for root in config.effective_roots
        if root.watch == "live" and root.path is not None
    }
    known_tiers = {root.tier for root in config.effective_roots}
    return ReadFileTool(
        live_roots=live_roots,
        snapshot_layout=snapshot_layout,
        known_tiers=known_tiers,
    )


class TestStaticSnapshotReacquire:
    """FP-05 — a matching version stamp must RE-ACQUIRE when the snapshot dir is gone.

    The contract: the version-stamp skip is an optimisation that assumes the
    snapshot it stamped is still materialised. When the materialisation dir is
    absent or empty (a lost container/volume), a matching stamp must NOT short-
    circuit the tier — it must re-acquire the snapshot so the served files exist
    again. A matching stamp over a PRESENT, non-empty snapshot still skips (the
    optimisation is preserved).
    """

    async def test_matching_stamp_reacquires_when_snapshot_dir_absent(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """Arrange: build the tier once (stamp + snapshot present); then DELETE the
        snapshot dir, leaving the stamp behind (the lost-volume shape).
        Act: index_tier again with a counting provider.
        Assert: the provider's ``acquire`` ran (re-acquire), the materialisation
                dir is repopulated, and the tier is reported rebuilt — NOT skipped.
        """
        # real-Qdrant
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        materialized = layout.materialization_dir(_STATIC_TIER)
        root = next(r for r in config.roots if r.tier == _STATIC_TIER)

        # Step 1: initial build — stamps the version AND materialises the snapshot.
        first_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await first_indexer.index_tier(root)
        assert first_indexer.tier_version_stamp(_STATIC_TIER) == _STATIC_VERSION
        assert (materialized / _STATIC_FILE_REL).exists(), (
            "test setup: the initial build must materialise the snapshot file"
        )

        # Step 2: simulate the lost container/volume — the materialisation dir is
        # removed from disk while the manifest stamp survives. This is the exact
        # production shape the fix targets (clause 1: a real failure mode).
        shutil.rmtree(materialized)
        assert not materialized.exists(), "test setup: snapshot dir must be gone"
        # The stamp STILL matches the config version — the trap the bug falls into.
        assert first_indexer.tier_version_stamp(_STATIC_TIER) == _STATIC_VERSION

        # Step 3: re-index the tier with a COUNTING provider so the acquire seam is
        # observable. The stamp matches but the snapshot is gone → must re-acquire.
        counting = _CountingProvider(_STATIC_TIER, static_src)
        second_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root, providers=[counting],
        )
        summary = await second_indexer.index_tier(root)

        # The provider's acquire MUST have run (the re-acquire) — the independent
        # oracle observed at the real provider seam, not a restatement of the
        # indexer's branch (clause 2 / clause 3).
        assert counting.acquire_calls >= 1, (
            "a matching stamp over an ABSENT snapshot dir must RE-ACQUIRE the "
            "snapshot via the provider; acquire was never called"
        )
        # The snapshot file is materialised again on disk.
        assert (materialized / _STATIC_FILE_REL).exists(), (
            "after re-acquire, the snapshot materialisation dir must hold the file"
        )
        # The tier is reported REBUILT (re-acquired + re-walked), not skipped.
        assert _STATIC_TIER in summary.tiers_rebuilt, (
            "a re-acquired tier must be reported rebuilt, not skipped; "
            f"tiers_rebuilt={summary.tiers_rebuilt}, tiers_skipped={summary.tiers_skipped}"
        )
        assert _STATIC_TIER not in summary.tiers_skipped

    async def test_read_file_works_again_after_reacquire(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """The END-TO-END consumer contract: read_file recovers after re-acquire.

        Arrange: build the tier (snapshot present), then delete the snapshot dir.
                 Confirm read_file is BROKEN in that lost-volume state (the bug's
                 user-visible symptom).
        Act: re-index the tier (the fix re-acquires).
        Assert: read_file returns the file's real content again — the served
                files physically exist once more.
        """
        # real-Qdrant
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        materialized = layout.materialization_dir(_STATIC_TIER)
        root = next(r for r in config.roots if r.tier == _STATIC_TIER)
        read_tool = _read_file_tool(config, snapshot_root)

        # Step 1: build + materialise, then prove read_file works initially.
        indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await indexer.index_tier(root)
        span = read_tool.read_file(_STATIC_TIER, _STATIC_FILE_REL)
        assert isinstance(span, FileSpan)
        # The served content is the real source — an independent oracle (the bytes
        # we wrote into _build_static_source), not a restatement of any formula.
        assert "class Widget" in span.text, (
            "the initial read_file must return the materialised source content"
        )

        # Step 2: lose the snapshot dir (stamp survives) → read_file is now BROKEN.
        shutil.rmtree(materialized)
        with pytest.raises(ReadFileError):
            # The user-visible symptom of the bug: the file is physically gone.
            read_tool.read_file(_STATIC_TIER, _STATIC_FILE_REL)

        # Step 3: re-index — a matching stamp + absent snapshot must re-acquire.
        recover_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await recover_indexer.index_tier(root)

        # read_file recovers: the served file exists again and carries its content.
        recovered = read_tool.read_file(_STATIC_TIER, _STATIC_FILE_REL)
        assert "class Widget" in recovered.text, (
            "after the tier is re-acquired, read_file must return the file content "
            "again (the snapshot is re-materialised) — not raise / not empty"
        )
        # The recovered span covers real lines (sanity bound on a derived span,
        # clause 4): a non-empty file spans at least line 1.
        assert recovered.line_start == 1
        assert recovered.line_end >= 1

    async def test_matching_stamp_with_present_snapshot_still_skips_zero_acquire(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """The optimisation MUST be preserved: present snapshot + matching stamp → SKIP.

        The false-positive guard for the fix. When the materialisation dir is
        present AND the stamp matches, the tier is skipped with ZERO acquisition
        and ZERO walk, exactly as today — the fix must add the absent-dir
        re-acquire WITHOUT making every matching-stamp index re-acquire.

        Mirrors ``test_indexer.py.TestStaticTierFreshness.test_matching_stamp_
        skips_with_zero_walk`` (clause 5): the exploding provider is the failure
        signal — if acquire runs, the optimisation regressed.
        """
        # real-Qdrant
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        materialized = layout.materialization_dir(_STATIC_TIER)
        root = next(r for r in config.roots if r.tier == _STATIC_TIER)

        # Step 1: real build → stamp set + snapshot dir present and non-empty.
        first_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await first_indexer.index_tier(root)
        assert (materialized / _STATIC_FILE_REL).exists(), (
            "test setup: the snapshot dir must be present + non-empty for the "
            "skip-path guard"
        )

        # Step 2: re-index with an EXPLODING provider — a matching stamp over a
        # PRESENT snapshot must skip without ever calling acquire.
        exploding = _ExplodingProvider(_STATIC_TIER)
        second_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root, providers=[exploding],
        )
        summary = await second_indexer.index_tier(root)

        assert exploding.acquired is False, (
            "a matching stamp over a PRESENT snapshot must NOT re-acquire (the "
            "zero-walk optimisation must be preserved)"
        )
        assert _STATIC_TIER in summary.tiers_skipped, (
            "a matching stamp over a present snapshot must report the tier skipped"
        )
        assert _STATIC_TIER not in summary.tiers_rebuilt

    async def test_matching_stamp_reacquires_when_snapshot_dir_empty(
        self, tmp_path: Path, store_factory: Any
    ) -> None:
        """An EMPTY snapshot dir (present but no files) also forces a re-acquire.

        A volume that was remounted empty — the directory exists but holds no
        files — is as broken as an absent dir for serving: every ``read_file``
        misses. The invariant treats absent OR empty identically: re-acquire.
        This case pins the EMPTY half of "absent/empty" so a fix that only checks
        ``dir.exists()`` (and misses the empty case) is caught.
        """
        # real-Qdrant
        slug = _slug()
        static_src = tmp_path / "community_src"
        _build_static_source(static_src)
        config = _config(slug=slug, static_source=static_src)
        store = store_factory(slug)
        await store.ensure_collection(_DIM)
        manifest = Manifest(str(tmp_path / "m.db"))
        snapshot_root = tmp_path / "snap"
        layout = SnapshotLayout(snapshot_root)
        materialized = layout.materialization_dir(_STATIC_TIER)
        root = next(r for r in config.roots if r.tier == _STATIC_TIER)

        # Step 1: initial build → stamp + materialised snapshot.
        first_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root,
        )
        await first_indexer.index_tier(root)
        assert (materialized / _STATIC_FILE_REL).exists()

        # Step 2: empty the dir but LEAVE it present (the remounted-empty-volume
        # shape) — the stamp still matches.
        shutil.rmtree(materialized)
        materialized.mkdir(parents=True, exist_ok=True)
        assert materialized.exists() and not any(materialized.iterdir()), (
            "test setup: the snapshot dir must be present but EMPTY"
        )
        assert first_indexer.tier_version_stamp(_STATIC_TIER) == _STATIC_VERSION

        # Step 3: re-index with a counting provider → must re-acquire on EMPTY.
        counting = _CountingProvider(_STATIC_TIER, static_src)
        second_indexer = _make_indexer(
            config=config, store=store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest, snapshot_root=snapshot_root, providers=[counting],
        )
        summary = await second_indexer.index_tier(root)

        assert counting.acquire_calls >= 1, (
            "a matching stamp over an EMPTY snapshot dir must RE-ACQUIRE — an "
            "empty dir serves no files, so it is as broken as an absent one"
        )
        assert (materialized / _STATIC_FILE_REL).exists(), (
            "after re-acquire, the (formerly empty) snapshot dir must hold the file"
        )
        assert _STATIC_TIER in summary.tiers_rebuilt
        assert _STATIC_TIER not in summary.tiers_skipped
