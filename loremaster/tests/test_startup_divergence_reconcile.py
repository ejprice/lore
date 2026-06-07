"""Contract tests for the store-divergence reconcile slice (idempotent startup).

These tests are RED BY CONSTRUCTION: they reference a NEW API surface that does
NOT yet exist (``QdrantStore.count_points``, ``Manifest.expected_chunks`` /
``indexed_file_count`` / ``reset_tier``, ``CodeGraph.indexed_file_count``, and a
``reconcile_store_divergence`` step wired into ``build_app_context``). Until the
implementation lands they fail BEHAVIORALLY (AssertionError / AttributeError),
not structurally — the test module itself imports cleanly (the new names are
imported lazily inside each test).

The root cause the slice fixes: every "is the index healthy?" decision today
reads the SQLite manifest + filesystem, NEVER the live Qdrant point count or the
graph row count. So a wiped/short Qdrant collection or an empty graph.db that the
manifest still calls ``indexed`` produces a SILENT empty/blind index — the
startup re-creates the collection EMPTY and the initial sweep fast-path-skips
every ``indexed`` file (zero embeds).

The slice owns:
    * FP-02 (Critical) — wiped/short collection heals (re-embed).
    * FP-03 — orphan over-count purges + rebuilds (converge to expected).
    * FP-04 (Critical) — wiped/empty graph.db heals (re-graph).
    * FP-10 — the "empty?" check must read the LIVE count, not the manifest.

The design rests on a VERIFIED fact: point ids are deterministic
(``uuid5(NAMESPACE_URL, "slug:tier:file_path:chunk_type:identity:sub_ordinal:key_version")``),
so a blind re-embed OVERWRITES in place rather than duplicating — making
"purge-then-rebuild a diverged tier" safe.

THE HONEST DIVISION OF LABOUR (why some tests drive the full sweep and some call
the bare reconcile): ``reconcile_store_divergence`` receives NO indexer/embedder,
so it CANNOT produce real vectors. Its honest job is DETECT → ``delete_by_tier``
the diverged tier + ``reset_tier`` its manifest rows; the COUNT is then restored
by the subsequent ``build_app_context`` SWEEP that re-embeds real content. A
reconcile that fabricates points to make ``count_points(tier)`` read ``expected``
without a sweep is ACTIVELY HARMFUL — a crash between the bare reconcile and the
sweep leaves a collection of fake placeholders that the very divergence check we
are building reads as "healthy" (reintroducing FP-02 undetectably) and pollutes
search. So:

    * The heal-to-``expected`` oracle (TestWipedCollectionHeals, TestOrphanOver…,
      TestWipedGraph, TestCountVsMtime) is asserted ONLY after the REAL sweep
      (``build_app_context`` + ``reindex``) — never after a bare reconcile.
    * The bare reconcile (called directly, no sweep) is asserted ONLY on its
      honest outputs: WHICH tiers it purged (the ``delete_by_tier`` spy) and
      WHICH manifest rows it reset — NOT on a fabricated count.
    * TestReconcileDoesNotFabricatePoints PINS the harm shut: after a bare
      reconcile over a wiped tier, ``count_points(tier)`` MUST be 0 (purged, not
      re-seated) and no surviving point may carry a placeholder payload (missing
      ``source_text``). This assertion is RED against the placeholder hack.

Independent oracles (the non-negotiable rule): every "did the heal work?"
assertion reads the LIVE store count (``count_points``) / a real search hit / a
real graph query (``what_imports``), NEVER a manifest read — because the bug is
precisely that the manifest lies. The "no false heal" + tier-scope + idempotence
guards spy ``delete_by_tier`` and read the reset manifest state directly.

How to run:
    PP=<worktree>/loremaster:<worktree>/loresigil:<worktree>/lorescribe
    cd <worktree>/loremaster
    PYTHONPATH=$PP /home/ejprice/PycharmProjects/lore/.venv/bin/python \\
        -m pytest tests/test_startup_divergence_reconcile.py -q -p no:cacheprovider

All tests need the real local Qdrant (http://127.0.0.1:16333) — the divergence
the slice heals (live point count vs. manifest) is a SERVER-side fact that the
in-memory backend cannot represent.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Production symbols — imported freely to ground fixtures in the real
# config / manifest / indexer / store conventions (clause 5: same source of
# truth as production). The NEW symbols under contract are imported LAZILY
# inside each test so this module stays importable while they do not yet exist.
# ---------------------------------------------------------------------------
from loremaster.config import LoreConfig
from loremaster.graph import CodeGraph
from loremaster.index.manifest import STATE_INDEXED, Manifest
from loremaster.server import LoreServer, build_app_context
from loremaster.store.qdrant import QdrantStore
from loresigil.testing import FakeEmbedder
from qdrant_client import AsyncQdrantClient

# ---------------------------------------------------------------------------
# Production-realistic constants (the same values the existing suite uses —
# test_reconcile.py / test_schema_rebuild.py — so fixtures share the real
# unit / scale / convention; clause 1 + clause 5).
# ---------------------------------------------------------------------------

# The production embedding dimensionality the whole suite uses. A vector of the
# WRONG dim is a 4xx (permanent) error against a real collection, so pinning the
# real curve dim is load-bearing, not cosmetic (clause 1: realistic scale).
_DIM = 2048

# Production-canonical TEI embedding config values (mirrors test_reconcile.py).
_TEI_BASE_URL = "http://tei.example:8080"
_TEI_KEY_ENV = "LORE_TEI_KEY"

# Tier names matching the production convention (test_reconcile.py): a watched
# LIVE workspace tier + a pinned STATIC dependency tier. Obtained as named
# constants, never hand-copied literals, so a tier rename can't drift silently
# (clause 5).
_LIVE_TIER = "custom"
_STATIC_TIER = "community"

# The memory collection suffix build_app_context appends for the SEPARATE memory
# store (lore_<slug>_memory). The divergence reconcile must never touch it — it
# is registered for teardown but is out of scope for the corpus heal (clause 3:
# the seam boundary is the corpus collection only).
_MEMORY_SUFFIX = "_memory"


# ---------------------------------------------------------------------------
# Realistic corpus — real Python modules the python_ast chunker splits into
# multiple chunks (so expected_chunks(tier) > files; the count oracle is
# meaningful). NOT foo/bar/x=1 (clause 1).
# ---------------------------------------------------------------------------

# A representative IN-PROJECT import whose presence in the graph after a heal
# proves the re-graph actually happened (the searchability oracle). Under the
# RESOLVED edge contract a stdlib import is dropped, so the rep edge is the
# in-project ``from src.routing import champion_routing`` — which resolves to the
# symbol FQN ``src.routing.champion_routing`` (read straight off _PY_WIDGET).
_REP_MODULE_IMPORT = "src.routing.champion_routing"

_PY_WIDGET = """\
from src.routing import champion_routing


class Widget:
    \"\"\"A render widget.\"\"\"

    def render(self, value):
        return champion_routing(value)


def make_widget():
    return Widget()
"""

_PY_ROUTING = """\
def champion_routing(week):
    \"\"\"Route the 36-week curve champion to its lane.\"\"\"
    return week * 2
"""

_PY_STATIC_CORE = """\
import json


class CoreService:
    \"\"\"A pinned dependency-tier service.\"\"\"

    def load(self, blob):
        return json.loads(blob)
"""


# Docs-only corpus content — realistic multi-section Markdown the markdown
# chunker splits into MULTIPLE chunks (so expected_chunks(tier) > 0 and the
# count oracle is meaningful), and a plain-text file. ZERO ``.py`` files, so the
# code graph is LEGITIMATELY empty (indexer.py:533 only graphs ``.py``) — the
# docs-only shape the false-heal bug fires on. Real project-doc prose, not
# foo/bar (clause 1).
_MD_OVERVIEW = """\
# Routing Engine

The routing engine assigns each inbound load to a lane.

## Lanes

A lane is a directed corridor between two regions. Lanes are ranked by the
36-week demand curve so the champion lane wins ties.

## Champions

The champion of a corridor is the lane with the highest rolling 36-week volume.
Ties break toward the lane with the lower deadhead ratio.
"""

_MD_OPERATIONS = """\
# Operations Runbook

## Nightly cycle

The nightly cycle rebuilds the demand curve and re-ranks every lane.

## Escalation

Page the on-call dispatcher when a corridor has zero eligible lanes for more
than fifteen minutes.
"""

_TXT_NOTES = "Release notes: the curve window widened from 26 to 36 weeks.\n"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _build_live_corpus(root: Path) -> None:
    """A realistic LIVE workspace tree (mirrors test_reconcile.py shape)."""
    _write(root / "src" / "widget.py", _PY_WIDGET)
    _write(root / "src" / "routing.py", _PY_ROUTING)
    _write(root / "README.md", "# Project\n\nSome docs.\n")
    # An excluded glob that must NEVER be indexed (so the count is over REAL
    # included files, not noise).
    _write(root / "src" / "bundle.min.js", "var x=1;")
    # A pruned dir that must never be descended.
    _write(root / ".git" / "config.py", "SECRET = 'do-not-index'\n")


def _build_static_source(root: Path) -> None:
    """A realistic STATIC dependency tree."""
    _write(root / "lib" / "core.py", _PY_STATIC_CORE)


def _build_docs_only_corpus(root: Path) -> None:
    """A realistic LIVE tree with ZERO Python files — only Markdown + text.

    Every file is graph-INELIGIBLE: the indexer only builds graph nodes for
    ``.py`` files (indexer.py:533 skips non-Python), so this corpus indexes into
    the manifest + the vector store but contributes NOTHING to the code graph.
    That is the docs-only shape whose graph is LEGITIMATELY empty while the
    manifest is populated — the exact input the false-heal bug mis-classifies as
    a wiped graph. The ``.py``-excluding glob keeps it strictly Python-free even
    if a stray ``.py`` is ever added under the tree.
    """
    _write(root / "docs" / "overview.md", _MD_OVERVIEW)
    _write(root / "docs" / "operations.md", _MD_OPERATIONS)
    _write(root / "NOTES.txt", _TXT_NOTES)


def _slug() -> str:
    """A throwaway slug → collection ``lore_test_<session>_<uuid>``.

    Uses the same PID-namespaced session prefix the conftest teardown reaps, so
    a leaked collection on the shared server is harmlessly reclaimed and a
    concurrent worktree's run is never nuked.
    """
    return f"test_{uuid.getnode() % 100000}_{uuid.uuid4().hex}"


def _config(
    *,
    slug: str,
    live_path: Path,
    static_source: Path | None = None,
    static_version: str = "1.0.0",
) -> LoreConfig:
    """Build a validated :class:`LoreConfig` from production-realistic values.

    One live ``custom`` tier always; an optional static ``community`` tier for the
    multi-tier per-tier-divergence case. Mirrors the test_reconcile.py builder so
    the fixtures carry the SAME real config conventions as production (clause 5).
    """
    roots: list[dict[str, Any]] = [
        {
            "tier": _LIVE_TIER,
            "watch": "live",
            "path": str(live_path),
            "include": ["**/*.py", "**/*.md"],
            "exclude": ["**/*.min.js"],
        }
    ]
    if static_source is not None:
        roots.append(
            {
                "tier": _STATIC_TIER,
                "watch": "static",
                "source": str(static_source),
                "version": static_version,
                "provider": "local_directory",
                "include": ["**/*.py"],
            }
        )
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
        "roots": roots,
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


# ---------------------------------------------------------------------------
# A delete_by_tier-counting QdrantStore subclass — the spy for the
# "no false heal" guard (invariant 4). It counts the WHOLE-TIER purge the heal
# fires, so a wasteful always-rebuild over a HEALTHY index is caught. The spy
# does NOT mirror the reconcile implementation — it only counts a public method
# call (an independent observation, clause 2).
# ---------------------------------------------------------------------------
class DeleteByTierSpyStore(QdrantStore):
    """A :class:`QdrantStore` that records every ``delete_by_tier`` purge.

    Used by invariant 4 (no false heal), invariant 5 (idempotent second run), and
    the per-tier-scope guard: the heal's purge begins with ``delete_by_tier(tier)``,
    so the set of tiers purged is the independent oracle for "did the reconcile
    decide to rebuild this tier?" — read WITHOUT inspecting the reconcile's
    internals.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Ordered list of tiers passed to delete_by_tier (one entry per purge).
        self.purged_tiers: list[str] = []

    async def delete_by_tier(self, tier: str) -> None:
        self.purged_tiers.append(tier)
        await super().delete_by_tier(tier)


# ---------------------------------------------------------------------------
# AppContext factory — drives the REAL build_app_context with start_tasks=True
# (the PROD path: probe gate → ensure_collection → reconcile → initial sweep),
# with exact-name teardown of every collection it created (clause 3: the real
# handoff, not a mock on each side). Optionally injects a spy store via a
# pre-built qdrant client so the divergence reconcile uses it.
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture()
async def divergence_harness(tmp_path: Path) -> AsyncIterator[Any]:
    """Yield a builder + helpers for driving build_app_context over a real index.

    The builder returns a small bundle exposing the live store handle and graph,
    so a test can: (1) seed a real index, (2) DIVERGE the store/graph behind the
    manifest's back, (3) re-enter build_app_context, (4) assert the heal via the
    LIVE count — never a manifest read.
    """
    from conftest import QDRANT_URL, _qdrant_api_key

    api_key = _qdrant_api_key()
    created_collections: list[str] = []
    open_contexts: list[Any] = []
    open_clients: list[AsyncQdrantClient] = []

    def _register(slug: str) -> None:
        created_collections.append(f"lore_{slug}")
        created_collections.append(f"lore_{slug}{_MEMORY_SUFFIX}")

    async def _build(
        *,
        config: LoreConfig,
        manifest_path: Path,
        graph_path: Path,
        snapshot_root: Path,
        start_tasks: bool = True,
    ) -> Any:
        """Build an AppContext through the REAL prod path; track it for teardown."""
        _register(config.project.slug)
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=api_key)
        open_clients.append(client)
        app_ctx = await build_app_context(
            server=LoreServer(config),
            embedder=FakeEmbedder(dim=_DIM),
            qdrant_client=client,
            manifest_path=manifest_path,
            graph_path=graph_path,
            snapshot_root=snapshot_root,
            start_tasks=start_tasks,
        )
        open_contexts.append(app_ctx)
        return app_ctx

    # A raw client tests use to MUTATE the store behind the manifest's back
    # (drop/recreate a collection empty) — the FP-02 divergence injector.
    mutator_client = AsyncQdrantClient(url=QDRANT_URL, api_key=api_key)

    bundle = {
        "build": _build,
        "config": _config,
        "mutator_client": mutator_client,
        "register": _register,
        "api_key": api_key,
        "url": QDRANT_URL,
    }

    try:
        yield bundle
    finally:
        for app_ctx in open_contexts:
            try:
                await app_ctx.aclose()
            except Exception:
                pass
        for name in created_collections:
            if await mutator_client.collection_exists(name):
                await mutator_client.delete_collection(name)
        await mutator_client.close()
        for client in open_clients:
            await client.close()


async def _live_count(*, slug: str, tier: str, url: str, api_key: str) -> int:
    """Read the LIVE Qdrant point count for one tier — the INDEPENDENT oracle.

    Builds a throwaway :class:`QdrantStore` over the same ``lore_<slug>``
    collection and calls ``count_points(tier)`` — the SERVER count, NOT a
    manifest read. This is the oracle the slice exists to make the startup
    consult (clause 2: independent of the implementation under test).
    """
    client = AsyncQdrantClient(url=url, api_key=api_key)
    try:
        store = QdrantStore(client=client, slug=slug)
        return await store.count_points(tier)  # type: ignore[attr-defined]
    finally:
        await client.close()


# The payload key a REAL indexed point carries verbatim from its chunk
# (records.py:165 — ``"source_text": chunk.source_text``): the actual on-disk
# source the chunk was embedded from. A REAL point always has a non-empty
# ``source_text``; a fabricated zero-vector PLACEHOLDER point
# (server.py:_build_tier_placeholders) carries ONLY ``{"tier", "file_path"}`` —
# NO ``source_text``. Reading this key back distinguishes a genuinely
# re-embedded point from a count-faking placeholder. Obtained from the
# production record builder's own payload convention, never a hand-picked
# literal (clause 5).
_SOURCE_TEXT_PAYLOAD_KEY = "source_text"


async def _tier_point_payloads(
    *, slug: str, tier: str, url: str, api_key: str, limit: int = 500
) -> list[dict[str, Any]]:
    """Scroll the LIVE points for one tier and return their payloads.

    Reads the real Qdrant points back (payload included) via the production
    ``QdrantStore.scroll`` on the ``tier`` keyword index — the same payload field
    the heal's ``delete_by_tier`` and ``count_points(tier)`` key on. Used by the
    anti-fabrication guard to inspect whether the points carrying the count are
    REAL chunks (non-empty ``source_text``) or fabricated placeholders.
    """
    client = AsyncQdrantClient(url=url, api_key=api_key)
    try:
        store = QdrantStore(client=client, slug=slug)
        points = await store.scroll({"tier": tier}, limit=limit)
        return [dict(point.payload) for point in points if point.payload is not None]
    finally:
        await client.close()


# ===========================================================================
# Invariant 1 — Wiped collection heals (FP-02, Critical)
# ===========================================================================
class TestWipedCollectionHeals:
    """A manifest claiming N>0 indexed chunks over an EMPTY/SHORT collection heals.

    Contract: when ``count_points(tier) < expected_chunks(tier)`` at startup, the
    reconcile purges + re-embeds the tier so the LIVE count converges to expected
    and a representative symbol is searchable again. The oracle is the live Qdrant
    count and a real search hit — NEVER a manifest read (the manifest is what lies).
    """

    async def test_wiped_collection_reindexed_to_expected_live_count(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index; WIPE the collection behind the manifest.
        Act: re-enter build_app_context (the restart).
        Assert: live count(tier) == expected_chunks(tier) > 0 (heal re-embedded).
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Step 1: seed a real index through the prod path, then settle + close.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)  # bring every tier current under the lock
        await seed.aclose()

        # The manifest now claims the live tier is indexed with N>0 chunks. Read
        # the EXPECTED chunk count from the manifest (the manifest is honest about
        # what SHOULD be there — it is the LIVE store that will be wiped).
        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        assert expected > 0, (
            f"test setup: the seeded manifest must claim >0 chunks for {_LIVE_TIER!r}; "
            f"got {expected}"
        )

        # Step 2: WIPE the collection behind the manifest's back — drop + recreate
        # it EMPTY (the FP-02 shape: a wiped Qdrant the manifest still calls
        # indexed). The manifest is untouched, so it still lies "indexed".
        mutator = divergence_harness["mutator_client"]
        from qdrant_client import models as qmodels  # local: only the wipe needs it

        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )
        wiped = await _live_count(
            slug=slug, tier=_LIVE_TIER,
            url=divergence_harness["url"], api_key=divergence_harness["api_key"],
        )
        assert wiped == 0, f"test setup: the wiped collection must be empty; got {wiped}"

        # Step 3: RESTART — re-enter build_app_context. The store-divergence
        # reconcile (after ensure_collection, before the index is declared live)
        # must detect count < expected, RESET the tier, and the SWEEP re-embeds.
        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)  # settle any in-flight heal under the lock

        # ASSERT (independent oracle): the LIVE count converged to expected (>0).
        # This holds ONLY because the SWEEP re-embedded real content — the bare
        # reconcile alone cannot produce vectors (see TestReconcileDoesNotFabricate).
        healed = await _live_count(
            slug=slug, tier=_LIVE_TIER,
            url=divergence_harness["url"], api_key=divergence_harness["api_key"],
        )
        assert healed == expected, (
            f"a wiped collection the manifest still calls 'indexed' must be RE-INDEXED "
            f"on restart: live count({_LIVE_TIER}) must converge to expected_chunks "
            f"({expected}); got live count {healed} (FP-02: the blind empty index)"
        )

    async def test_wiped_collection_makes_representative_symbol_searchable_again(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """The heal re-embeds REAL content: a search for a corpus term hits again.

        Searchability oracle (independent of the count): after the heal a search
        finds the widget module's content. Under the bug the index is silently
        empty, so the search returns nothing.
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)

        # Independent oracle: a real search returns at least one hit, and a hit
        # cites a known corpus file. (search_code returns summarised, cited
        # results — the file path rides in ``formatted``.)
        results = await restarted.search_code("render a widget value", k=5)
        assert len(results) >= 1, (
            "after healing a wiped collection, a search for real corpus content "
            "must return hits — a blind empty index returns nothing (FP-02)"
        )
        formatted_blob = "\n".join(r.formatted for r in results)
        assert "widget.py" in formatted_blob, (
            "the healed index must contain the widget module again; a hit must cite "
            f"src/widget.py. Got citations:\n{formatted_blob}"
        )


# ===========================================================================
# Invariant 2 — Over-count / orphans heal (FP-03)
# ===========================================================================
class TestOrphanOverCountHeals:
    """A collection with MORE points than the manifest expects converges to expected.

    The FP-03 shape: a wiped-manifest reindex left orphan points (ids no longer
    produced by any current file). When ``count_points(tier) > expected_chunks(tier)``
    the reconcile purges + rebuilds so the live count converges DOWN to expected.

    Scoping note: this contract treats ANY inequality (``count != expected``) as a
    heal trigger — both the short case (invariant 1) and the over-count case here.
    """

    async def test_orphan_over_count_converges_down_to_expected(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index; inject ORPHAN points the manifest never lists.
        Act: re-enter build_app_context.
        Assert: live count(tier) == expected_chunks(tier) (orphans purged).
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        assert expected > 0, "test setup: the seed must produce >0 expected chunks"

        # Inject ORPHAN points carrying the live tier's payload but file paths that
        # no current file produces (so the manifest never lists them) — the FP-03
        # leftover shape. Use a NUMBER of orphans large enough that count > expected.
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        orphan_count = 5
        orphan_points = [
            qmodels.PointStruct(
                id=str(uuid.uuid4()),
                vector=[0.0] * _DIM,
                payload={
                    "tier": _LIVE_TIER,
                    # A path no real file produces → an orphan the manifest omits.
                    "file_path": f"src/_orphan_{i}.py",
                    "chunk_type": "function",
                    "content_hash": "deadbeef",
                },
            )
            for i in range(orphan_count)
        ]
        await mutator.upsert(collection_name=f"lore_{slug}", points=orphan_points)

        before = await _live_count(
            slug=slug, tier=_LIVE_TIER,
            url=divergence_harness["url"], api_key=divergence_harness["api_key"],
        )
        assert before > expected, (
            f"test setup: orphans must push live count above expected "
            f"({before} should be > {expected})"
        )

        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)

        # ASSERT (independent oracle): the live count converged DOWN to expected —
        # the orphans were purged by the heal's delete_by_tier + the sweep rebuilt.
        healed = await _live_count(
            slug=slug, tier=_LIVE_TIER,
            url=divergence_harness["url"], api_key=divergence_harness["api_key"],
        )
        assert healed == expected, (
            f"an over-counted collection (orphan points) must converge DOWN to "
            f"expected_chunks ({expected}) after the heal purges + the sweep rebuilds; "
            f"got live count {healed} (FP-03: orphan points never reaped)"
        )


# ===========================================================================
# Invariant 3 — Wiped graph heals (FP-04, Critical)
# ===========================================================================
class TestWipedGraphHeals:
    """An EMPTY graph.db the manifest calls 'indexed' is repopulated on restart.

    The FP-04 shape: graph.db wiped/empty while manifest+collection are populated.
    The graph is rebuilt ONLY inside the re-embed path the fast-path skips, and the
    graph is NOT in the schema fingerprint — so it stays empty and what_imports /
    tests_for silently return nothing. Contract: when
    ``code_graph.indexed_file_count() == 0`` while ``manifest.indexed_file_count() > 0``,
    the reconcile repopulates the graph and a graph query returns edges again.
    Oracle: a real ``what_imports`` query (graph rows), NEVER a manifest read.
    """

    async def test_wiped_graph_repopulated_and_query_returns_edges(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index; DELETE the graph rows behind the manifest.
        Act: re-enter build_app_context.
        Assert: graph indexed-file count > 0 again AND what_imports('os') hits.
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # The manifest claims files are indexed; confirm the graph was populated
        # (so the WIPE below is a real divergence, not a no-op). Both reads use the
        # NEW indexed_file_count surface.
        manifest = Manifest(str(manifest_path))
        manifest_indexed = manifest.indexed_file_count()  # type: ignore[attr-defined]
        manifest.close()
        assert manifest_indexed > 0, (
            "test setup: the manifest must claim >0 indexed files after the seed"
        )

        graph = CodeGraph(str(graph_path))
        seeded_graph_files = graph.indexed_file_count()  # type: ignore[attr-defined]
        assert seeded_graph_files > 0, (
            "test setup: the seed must populate the graph with >0 files"
        )
        # WIPE the graph rows behind the manifest's back (the FP-04 divergence:
        # graph empty, manifest + collection populated). Use the real Kùzu node
        # tables the production graph reads (DETACH DELETE over CodeNode + Ref), so
        # the fixture is grounded in the actual DB.
        graph.connection.execute("MATCH (n:CodeNode) DETACH DELETE n")
        graph.connection.execute("MATCH (r:Ref) DETACH DELETE r")
        wiped_graph_files = graph.indexed_file_count()  # type: ignore[attr-defined]
        graph.close()
        assert wiped_graph_files == 0, (
            f"test setup: the wiped graph must report 0 indexed files; got {wiped_graph_files}"
        )

        # RESTART — the reconcile must detect graph==0 < manifest>0 and re-graph.
        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)

        # ASSERT (independent oracle 1): the LIVE graph is repopulated.
        healed_graph = CodeGraph(str(graph_path))
        healed_graph_files = healed_graph.indexed_file_count()  # type: ignore[attr-defined]
        healed_graph.close()
        assert healed_graph_files == seeded_graph_files, (
            f"a wiped graph the manifest calls indexed must be repopulated on restart: "
            f"graph indexed-file count must return to {seeded_graph_files}; got "
            f"{healed_graph_files} (FP-04: the silently-empty graph)"
        )

        # ASSERT (independent oracle 2): a real graph QUERY returns edges again.
        # widget.py imports the in-project ``src.routing.champion_routing`` →
        # what_imports of that resolved FQN must find the importing module node.
        importers = await restarted.what_imports(_REP_MODULE_IMPORT)
        assert len(importers) >= 1, (
            f"after healing a wiped graph, what_imports({_REP_MODULE_IMPORT!r}) must "
            "return the importing module again — an empty graph returns nothing (FP-04)"
        )


# ===========================================================================
# Invariant 4 — No false heal (THE CRITICAL GUARD)
# ===========================================================================
class TestNoFalseHealWhenHealthy:
    """A HEALTHY index (live counts match the manifest) is NOT purged/re-embedded.

    This is the critical guard against an always-rebuild that would defeat the
    incremental startup the whole feature exists to provide. Oracle: a spy that
    counts ``delete_by_tier`` — the heal's purge primitive — proves the reconcile
    did NOT decide to rebuild when the counts already agree.
    """

    async def test_healthy_restart_does_not_purge_any_tier(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real, HEALTHY index (manifest, store, graph all agree).
        Act: restart with a delete_by_tier SPY store wired into build_app_context.
        Assert: the spy recorded ZERO purges (no wasteful rebuild on a healthy index).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Step 1: seed a genuinely healthy index, then close cleanly.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # Sanity (independent oracle): the live count already matches expected, so a
        # heal would be pure waste. Read both from the LIVE store + the manifest.
        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        live_now = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_now == expected and expected > 0, (
            f"test setup: the seeded index must be HEALTHY (live {live_now} == "
            f"expected {expected} > 0) so any purge on restart is a false heal"
        )

        # Step 2: restart, but inject the divergence reconcile's store as a SPY so
        # every delete_by_tier is recorded. We drive build_app_context directly
        # with a hand-built spy store's client so the reconcile uses the spy.
        # The reconcile_store_divergence step must receive THIS store (the same one
        # ensure_collection ran against). We pass it via the public seam: a
        # pre-constructed spy whose client build_app_context shares.
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy_store = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        try:
            # The contract: build_app_context accepts the store divergence reconcile
            # wiring; to spy the purge we call the reconcile step directly with the
            # SAME collaborators build_app_context wires, over the seeded DBs.
            from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

            await spy_store.ensure_collection(_DIM)
            manifest2 = Manifest(str(manifest_path))
            graph2 = _graph_with_roots(config, graph_path, snap)
            try:
                await reconcile_store_divergence(  # type: ignore[misc]
                    store=spy_store,
                    manifest=manifest2,
                    code_graph=graph2,
                    config=config,
                )
            finally:
                manifest2.close()
                graph2.close()

            # ASSERT (independent oracle): NO tier was purged — a healthy index is
            # left alone. THIS IS THE GUARD against an always-rebuild.
            assert spy_store.purged_tiers == [], (
                "a HEALTHY index (live counts match the manifest) must NOT be "
                "purged/re-embedded on restart — the reconcile called delete_by_tier "
                f"on {spy_store.purged_tiers!r}, which would defeat incremental startup"
            )
        finally:
            await client.close()

    async def test_docs_only_corpus_empty_graph_is_not_false_healed(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """A docs-only corpus whose graph is LEGITIMATELY empty must NOT be purged.

        The medium-severity false-heal bug: the graph trigger fires whenever the
        code graph is empty (0 files) while the manifest is populated (> 0). But a
        DOCS-ONLY corpus (pure Markdown / text, ZERO ``.py``) has a legitimately
        empty graph — the indexer only graphs ``.py`` files (indexer.py:533 skips
        non-Python) — while its Markdown indexes into the manifest + store. So the
        ``code_graph.indexed_file_count() == 0 and manifest.indexed_file_count() > 0``
        trigger is TRUE on EVERY boot for such a project, purging + re-embedding the
        whole corpus each startup (a cost-DoS amplification). The graph is empty
        because there is nothing graph-eligible to put in it — NOT because it was
        wiped — so this is a HEALTHY index and the reconcile must leave it alone.

        ``TestWipedGraphHeals`` (Python corpus + wiped graph) MUST still heal — the
        fix gates ``graph_wiped`` on the manifest holding graph-ELIGIBLE (``.py``)
        files, so a real wiped graph over a Python corpus is distinguishable from a
        graph that is empty only because the corpus has no Python.

        Arrange: seed a HEALTHY index over a ZERO-Python (Markdown/text) corpus via
                 the real build_app_context + reindex.
        Act: run reconcile_store_divergence with a delete_by_tier spy.
        Assert: spy.purged_tiers == [] — the empty-but-legitimate graph is NOT
                mistaken for a wiped graph.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_docs_only_corpus(live)  # ZERO .py files → graph legitimately empty
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Step 1: seed a genuinely healthy docs-only index, then close cleanly.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # Sanity (independent oracles): the index is HEALTHY (live count == expected,
        # both > 0 — the Markdown really indexed), AND the graph is LEGITIMATELY
        # EMPTY (0 files — no .py to graph). Together these are the exact
        # empty-graph-but-healthy shape the false-heal bug mis-classifies. A
        # zero-expected setup would make the test vacuous, so we pin expected > 0.
        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest_indexed = manifest.indexed_file_count()  # type: ignore[attr-defined]
        manifest.close()
        live_now = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_now == expected and expected > 0, (
            f"test setup: the docs-only index must be HEALTHY (live {live_now} == "
            f"expected {expected} > 0) — the Markdown must have indexed, so any purge "
            "on restart is a FALSE heal"
        )
        assert manifest_indexed > 0, (
            "test setup: the manifest must claim >0 indexed files (the Markdown corpus)"
        )

        graph = CodeGraph(str(graph_path))
        graph_files = graph.indexed_file_count()  # type: ignore[attr-defined]
        graph.close()
        assert graph_files == 0, (
            f"test setup: a docs-only corpus must have a LEGITIMATELY EMPTY graph "
            f"(no .py files to graph); got {graph_files} graph files — the empty-graph "
            "shape the false-heal bug fires on is not exercised otherwise"
        )

        # Step 2: run the reconcile over this healthy docs-only index with a spy —
        # the SAME pattern as test_healthy_restart_does_not_purge_any_tier.
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy_store = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        try:
            from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

            await spy_store.ensure_collection(_DIM)
            manifest2 = Manifest(str(manifest_path))
            graph2 = _graph_with_roots(config, graph_path, snap)
            try:
                await reconcile_store_divergence(  # type: ignore[misc]
                    store=spy_store,
                    manifest=manifest2,
                    code_graph=graph2,
                    config=config,
                )
            finally:
                manifest2.close()
                graph2.close()

            # ASSERT (independent oracle): NO tier was purged. A legitimately-empty
            # graph (no .py to populate it) over a populated manifest is NOT a wiped
            # graph and must NOT trigger a whole-corpus purge + re-embed on boot.
            assert spy_store.purged_tiers == [], (
                "a DOCS-ONLY corpus whose code graph is LEGITIMATELY empty (no .py "
                "files) must NOT be treated as graph-wiped: the reconcile called "
                f"delete_by_tier on {spy_store.purged_tiers!r}, which would purge + "
                "re-embed the whole corpus on EVERY boot (cost-DoS amplification)"
            )
        finally:
            await client.close()


# ===========================================================================
# Invariant 5 — Healthy unaffected + idempotent (second run is a no-op)
# ===========================================================================
class TestReconcileIdempotent:
    """A second reconcile over a REALLY-healed index is a no-op (no purge).

    Idempotence means "a second reconcile over a genuinely-healthy index does
    nothing" — NOT "a bare reconcile fabricated the count so a re-run sees no
    divergence." So the heal must run through the REAL path first: re-enter
    build_app_context (reset + SWEEP re-embeds real content), bringing the live
    count back to expected with REAL vectors. ONLY THEN is a second bare
    reconcile asserted to purge nothing. A placeholder impl that fakes the count
    on a bare reconcile would pass the OLD (flawed) version of this test; the
    re-framed version routes the heal through the sweep so the second-run no-op
    is asserted over a really-healthy index.
    """

    async def test_second_reconcile_over_really_healed_index_purges_nothing(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: wipe a collection, then HEAL it for real via build_app_context +
                 reindex (the sweep re-embeds real content → live count == expected).
        Act: run reconcile_store_divergence a SECOND time with a delete_by_tier spy.
        Assert: the spy recorded ZERO purges (idempotent over a really-healthy index).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Seed a real index, then close.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        assert expected > 0, "test setup: the seed must produce >0 expected chunks"

        # WIPE the collection (the divergence to heal).
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        # HEAL FOR REAL via the prod path: the reconcile resets + the SWEEP
        # re-embeds genuine content, so the live count returns to expected with
        # REAL vectors (not placeholders). This is the same heal path
        # TestWipedCollectionHeals proves works.
        healed_ctx = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await healed_ctx.reindex(None)
        await healed_ctx.aclose()

        # Confirm the index is GENUINELY healthy now (live count == expected, with
        # real content) — the precondition for asserting the second run no-ops.
        live_after_heal = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_after_heal == expected, (
            f"test setup: the real heal (sweep) must bring the live count back to "
            f"expected ({expected}); got {live_after_heal} — cannot test idempotence "
            "over a still-diverged index"
        )

        # SECOND reconcile over the now-really-healthy index, with a spy — it must
        # find the counts already agree and purge NOTHING (the idempotence oracle).
        from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy = DeleteByTierSpyStore(client=client, slug=slug)
        m = Manifest(str(manifest_path))
        g = CodeGraph(str(graph_path))
        try:
            await spy.ensure_collection(_DIM)
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy, manifest=m, code_graph=g, config=config,
            )
        finally:
            m.close()
            g.close()
            await client.close()

        # ASSERT (independent oracle): the second run is a no-op — zero purges over
        # a genuinely-healthy index.
        assert spy.purged_tiers == [], (
            "a SECOND reconcile over a REALLY-healed index (sweep re-embedded real "
            f"content → counts agree) must be a no-op (idempotent); it purged "
            f"{spy.purged_tiers!r}"
        )


# ===========================================================================
# Per-tier divergence in a MULTI-TIER project (partial heal, sibling untouched)
# ===========================================================================
class TestPartialPerTierDivergence:
    """In a multi-tier project, ONLY the diverged tier heals; the healthy tier is left.

    The seam where unit/scale bugs live: ``count_points(tier)`` filters on the
    ``tier`` payload field, and the heal's ``delete_by_tier`` / ``reset_tier`` are
    tier-scoped. A wiped LIVE tier alongside a HEALTHY STATIC tier must heal ONLY
    the live tier — purging the static tier would be both wasteful and a tier-scope
    bug. Oracles (all honest for a BARE reconcile): the delete_by_tier spy's
    recorded tiers, and the manifest RESET state (live rows knocked out of
    ``indexed``, static rows still ``indexed``). The heal-to-``expected`` count is
    proven SEPARATELY via the REAL sweep path — never asserted off a bare reconcile.
    """

    async def test_bare_reconcile_resets_only_diverged_tier(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """A BARE reconcile is tier-scoped: it purges + resets ONLY the live tier.

        Arrange: build a 2-tier index (live custom + static community), all healthy.
                 Wipe ONLY the live tier's points (delete_by_tier on the live tier).
        Act: run reconcile_store_divergence (bare, no sweep) with a delete_by_tier spy.
        Assert (honest bare-reconcile oracles):
            1. ONLY the live tier appears in the spy's purged_tiers (static never).
            2. The reconcile RESET only the live tier's manifest rows (live rows no
               longer ``indexed``); the static tier's rows are STILL ``indexed``.
        Does NOT assert a post-bare-reconcile count == expected (that would force
        the implementer to fabricate placeholder points).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        static_src = tmp_path / "static"
        _build_live_corpus(live)
        _build_static_source(static_src)
        config = divergence_harness["config"](
            slug=slug, live_path=live, static_source=static_src,
        )
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected_live = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        expected_static = manifest.expected_chunks(_STATIC_TIER)  # type: ignore[attr-defined]
        # Both tiers must start fully indexed (the precondition for "reset only
        # the live tier" being observable).
        live_rows_before = manifest.files_for_tier(_LIVE_TIER)
        static_rows_before = manifest.files_for_tier(_STATIC_TIER)
        manifest.close()
        assert expected_live > 0 and expected_static > 0, (
            f"test setup: both tiers must be indexed with >0 chunks "
            f"(live={expected_live}, static={expected_static})"
        )
        assert live_rows_before and all(r.state == STATE_INDEXED for r in live_rows_before), (
            "test setup: every live-tier row must start 'indexed'"
        )
        assert static_rows_before and all(
            r.state == STATE_INDEXED for r in static_rows_before
        ), "test setup: every static-tier row must start 'indexed'"

        # Wipe ONLY the live tier's points (a tier-scoped filter delete) — the
        # static tier's points survive. This is the partial-divergence shape: one
        # tier diverged, one tier healthy.
        wipe_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        try:
            wipe_store = QdrantStore(client=wipe_client, slug=slug)
            await wipe_store.delete_by_tier(_LIVE_TIER)
        finally:
            await wipe_client.close()

        live_wiped = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        static_before = await _live_count(
            slug=slug, tier=_STATIC_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_wiped == 0, f"test setup: live tier must be wiped; got {live_wiped}"
        assert static_before == expected_static, (
            f"test setup: the static tier must still be healthy after wiping ONLY "
            f"the live tier; got {static_before} != {expected_static} (tier-scope leak)"
        )

        # Run the BARE reconcile with a spy so we can prove which tiers it purged.
        from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        m = Manifest(str(manifest_path))
        g = CodeGraph(str(graph_path))
        try:
            await spy.ensure_collection(_DIM)
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy, manifest=m, code_graph=g, config=config,
            )
        finally:
            m.close()
            g.close()
            await client.close()

        # ASSERT 1 (spy oracle): ONLY the live tier was purged — never the static.
        assert _LIVE_TIER in spy.purged_tiers, (
            f"the diverged live tier must be purged to heal it; purged {spy.purged_tiers!r}"
        )
        assert _STATIC_TIER not in spy.purged_tiers, (
            f"the HEALTHY static tier must NOT be purged (tier-scoped heal); "
            f"purged {spy.purged_tiers!r} — a sibling-tier purge is a tier-scope bug"
        )

        # ASSERT 2 (manifest-reset oracle — the honest direct-call effect): the
        # reconcile RESET the live tier out of 'indexed' (so the subsequent sweep
        # re-embeds it) but left the healthy STATIC tier's rows 'indexed'. This is
        # the tier-scoping proof that does NOT require a fabricated count.
        reread = Manifest(str(manifest_path))
        live_rows_after = reread.files_for_tier(_LIVE_TIER)
        static_rows_after = reread.files_for_tier(_STATIC_TIER)
        reread.close()
        assert live_rows_after, "the live tier's rows must still exist (reset, not deleted)"
        assert not any(r.state == STATE_INDEXED for r in live_rows_after), (
            "the bare reconcile must RESET the diverged live tier out of 'indexed' so "
            "the subsequent sweep re-embeds it (the COUNT divergence drives the reset); "
            f"live row states after = {[r.state for r in live_rows_after]!r}"
        )
        assert static_rows_after and all(
            r.state == STATE_INDEXED for r in static_rows_after
        ), (
            "the HEALTHY static tier's rows must remain 'indexed' — a bare reconcile "
            "must NOT reset a tier whose count already agrees (tier-scoped reset); "
            f"static row states after = {[r.state for r in static_rows_after]!r}"
        )

    async def test_diverged_tier_heals_to_expected_via_real_sweep_sibling_untouched(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """The COUNT heal-to-expected is proven via the REAL sweep (not a bare reconcile).

        Companion to the bare-reconcile tier-scope test: this drives the full prod
        path (build_app_context + reindex) so the SWEEP re-embeds the wiped live
        tier's real content back to expected, and confirms the healthy static
        tier's live count is UNCHANGED. The count oracle is asserted ONLY here,
        where a real sweep produced the vectors — never off a bare reconcile.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        static_src = tmp_path / "static"
        _build_live_corpus(live)
        _build_static_source(static_src)
        config = divergence_harness["config"](
            slug=slug, live_path=live, static_source=static_src,
        )
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected_live = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        expected_static = manifest.expected_chunks(_STATIC_TIER)  # type: ignore[attr-defined]
        manifest.close()
        assert expected_live > 0 and expected_static > 0

        # Wipe ONLY the live tier (tier-scoped) — static survives.
        wipe_client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        try:
            wipe_store = QdrantStore(client=wipe_client, slug=slug)
            await wipe_store.delete_by_tier(_LIVE_TIER)
        finally:
            await wipe_client.close()

        # HEAL via the REAL prod path: reset + SWEEP re-embeds real content.
        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)

        # ASSERT (live-count oracle): the wiped live tier healed back to expected
        # (real sweep), and the static tier's count is UNCHANGED (still exactly its
        # expected — the heal never touched it).
        live_after = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        static_after = await _live_count(
            slug=slug, tier=_STATIC_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_after == expected_live, (
            f"the wiped live tier must heal back to expected_chunks ({expected_live}) "
            f"via the real sweep; got {live_after}"
        )
        assert static_after == expected_static, (
            f"the healthy static tier's live count must be UNCHANGED by a live-tier "
            f"heal ({expected_static}); got {static_after} (the heal leaked across tiers)"
        )


# ===========================================================================
# Anti-fabrication guard — the bare reconcile must PURGE, never FABRICATE
# ===========================================================================
class TestReconcileDoesNotFabricatePoints:
    """A bare reconcile over a wiped tier purges to ZERO — it never re-seats fakes.

    THE GUARD THAT KILLS THE PLACEHOLDER HACK. ``reconcile_store_divergence`` gets
    NO indexer/embedder, so it cannot produce real vectors; restoring the count is
    the subsequent SWEEP's job. An impl that upserts zero-vector placeholder points
    to make ``count_points(tier)`` read ``expected`` after a BARE reconcile is
    actively harmful: a crash between the reconcile and the sweep leaves a
    collection of fakes that the divergence check then reads as 'healthy'
    (reintroducing FP-02 undetectably) and pollutes search with empty-source hits.

    So after a BARE reconcile over a wiped tier (no sweep):
        1. ``count_points(tier)`` MUST be 0 — purged, NOT re-seated to expected.
        2. Any surviving point in the tier MUST be a REAL chunk (non-empty
           ``source_text`` payload) — never a placeholder lacking it.

    Assertion 1 is RED against the placeholder impl (which makes the count
    ``expected``, not 0). Assertion 2 is the belt-and-braces content check: even
    if a future fake achieved a different count, a point without ``source_text`` is
    fabricated. Both are GREEN under the honest impl (reconcile = purge + reset).
    """

    async def test_bare_reconcile_over_wiped_tier_leaves_zero_points(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index; WIPE the collection (count 0).
        Act: run reconcile_store_divergence (bare — NO sweep behind it).
        Assert: count_points(live_tier) == 0 (the reconcile purged, did NOT
                fabricate placeholder points to fake the count), AND no surviving
                point lacks a real ``source_text`` payload.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Seed a real index, then close.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        assert expected > 0, "test setup: the seed must produce >0 expected chunks"

        # WIPE the collection empty behind the manifest (the divergence).
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        # Run the BARE reconcile — NO build_app_context / sweep behind it. Its only
        # honest effect on the store is delete_by_tier (purge); it must NOT upsert
        # anything to fake the count.
        from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        m = Manifest(str(manifest_path))
        g = CodeGraph(str(graph_path))
        try:
            await spy.ensure_collection(_DIM)
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy, manifest=m, code_graph=g, config=config,
            )
        finally:
            m.close()
            g.close()
            await client.close()

        # Precondition sanity: the reconcile DID act on the divergence (it purged
        # the wiped tier). This isn't the guard — the guard is the count below.
        assert _LIVE_TIER in spy.purged_tiers, (
            "test setup: a bare reconcile over a wiped tier must purge it; "
            f"purged {spy.purged_tiers!r}"
        )

        # PRIMARY GUARD (RED against the placeholder hack): after the bare reconcile
        # the live count is 0 — the reconcile purged and did NOT re-seat fabricated
        # placeholder points to make the count read ``expected``. The placeholder
        # impl makes this `expected`, not 0 → this assertion FAILS against it.
        live_after_bare = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_after_bare == 0, (
            "a BARE reconcile (no sweep) over a wiped tier must leave the tier "
            f"PURGED (count 0) — restoring the count to expected ({expected}) is the "
            "SWEEP's job, not the reconcile's. A non-zero count here means the "
            "reconcile FABRICATED placeholder points (the harmful hack): a crash "
            "before the sweep would leave fakes that read as 'healthy' and "
            f"reintroduce FP-02 undetectably. Got count {live_after_bare}"
        )

        # BELT-AND-BRACES (content honesty): any point that DID survive in the tier
        # must be a REAL chunk — carrying a non-empty ``source_text`` payload. A
        # placeholder point carries only {tier, file_path} (no source_text). This
        # catches a fake that somehow reached a different non-zero count.
        surviving = await _tier_point_payloads(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        fabricated = [
            payload for payload in surviving
            if not payload.get(_SOURCE_TEXT_PAYLOAD_KEY)
        ]
        assert fabricated == [], (
            "every point in the tier after a reconcile must be a REAL chunk carrying "
            f"a non-empty {_SOURCE_TEXT_PAYLOAD_KEY!r} payload; found "
            f"{len(fabricated)} fabricated placeholder point(s) lacking it "
            f"(sample payload keys: {[sorted(p) for p in fabricated[:3]]!r}) — "
            "the count-faking placeholder hack"
        )


# ===========================================================================
# Count-vs-mtime interaction — a wiped collection over UNCHANGED files heals
# ===========================================================================
class TestCountVsMtimeInteraction:
    """A wiped collection over files whose mtime+size are UNCHANGED still heals.

    The exact FP-02 trap: ``needs_reindex`` fast-path-skips a file whose mtime+size
    match the manifest — so the initial sweep ALONE re-embeds nothing after a wipe.
    The store-divergence reconcile must ``reset_tier`` (make the rows non-indexed)
    so the subsequent sweep's ``needs_reindex`` returns True and re-embeds. This
    pins that the heal does NOT rely on a file change — the divergence is detected
    from the COUNT, not from mtime.
    """

    async def test_wiped_collection_with_unchanged_mtime_still_reindexes(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index; WIPE the collection but DO NOT touch any file
                 (so mtime+size are byte-identical and needs_reindex would skip).
        Act: re-enter build_app_context.
        Assert: live count(tier) == expected (the count-driven heal beat the
                mtime fast-path).
        """
        # real-Qdrant
        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        # Confirm the manifest rows are in the INDEXED state with unchanged
        # mtime+size — so needs_reindex would fast-path-skip them (the trap).
        rows = manifest.files_for_tier(_LIVE_TIER)
        manifest.close()
        assert expected > 0 and rows, "test setup: the seed must produce indexed rows"
        assert all(row.state == STATE_INDEXED for row in rows), (
            "test setup: every live-tier row must be in the 'indexed' state so the "
            "mtime+size fast-path would skip it (the FP-02 trap the count must beat)"
        )

        # WIPE the collection but DO NOT touch any file on disk — mtime+size stay
        # byte-identical, so a manifest-only startup re-embeds NOTHING.
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        restarted = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await restarted.reindex(None)

        # ASSERT (independent oracle): despite the unchanged mtime+size, the
        # count-driven heal reset the tier and the sweep re-embedded to expected.
        healed = await _live_count(
            slug=slug, tier=_LIVE_TIER,
            url=divergence_harness["url"], api_key=divergence_harness["api_key"],
        )
        assert healed == expected, (
            f"a wiped collection over UNCHANGED files must still heal: the COUNT "
            f"divergence (not mtime) must drive a reset_tier + re-embed back to "
            f"expected ({expected}); got {healed}. A heal that relies on mtime alone "
            "is the FP-02 bug (needs_reindex fast-path-skips → blind empty index)"
        )


# ===========================================================================
# FP-10 — the empty-index decision reads the LIVE count, not the manifest
# ===========================================================================
class TestEmptyDecisionReadsLiveCount:
    """The 'is the index empty?' check must consult the LIVE store, not the manifest.

    FP-10: today the schema-rebuild empty? check is
    ``index_was_empty = len(manifest.all_files()) == 0`` — manifest-based, blind to
    the live count. A NEW ``count_points()`` (total) must report the LIVE store
    count so the empty decision is grounded in reality. This pins the primitive's
    semantics directly (a low-level seam test for the count the slice consults).
    """

    async def test_count_points_total_reflects_live_store_not_manifest(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: build a real index (manifest populated). WIPE the collection.
        Act: read count_points() (total, no tier filter) from the LIVE store.
        Assert: count_points() == 0 even though the manifest still lists files
                (the live count disagrees with the manifest — the FP-10 truth).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # The manifest still lists indexed files (it is NOT consulted for the live
        # truth) — this is the divergence FP-10 says the empty check must not trust.
        manifest = Manifest(str(manifest_path))
        manifest_files = len(manifest.all_files())
        manifest.close()
        assert manifest_files > 0, "test setup: the manifest must list files after seeding"

        # WIPE the collection empty behind the manifest.
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        # ACT: the LIVE total count — the oracle FP-10 says the empty decision must use.
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        try:
            store = QdrantStore(client=client, slug=slug)
            total = await store.count_points()  # type: ignore[attr-defined]  # no tier filter → grand total
        finally:
            await client.close()

        # ASSERT: the live count is 0 even though the manifest lists files. A check
        # that read the manifest would call this index "non-empty" — the FP-10 bug.
        assert total == 0, (
            f"count_points() (total) must report the LIVE store count: a wiped "
            f"collection is 0 even though the manifest lists {manifest_files} files. "
            f"Got {total} — an empty? check grounded in the manifest is FP-10"
        )


# ===========================================================================
# FIX 1 — graph-only heal EFFICIENCY (FP-04 follow-up)
# ===========================================================================
# Today a wiped graph over a HEALTHY collection (graph-only loss) heals by
# delete_by_tier + reset_tier, which forces the subsequent sweep to do a FULL
# VECTOR RE-EMBED of an intact collection just to rebuild the graph rows. That is
# wasteful: the vectors were never lost. The fix pins a smarter heal — when the
# graph is wiped but the LIVE point count AGREES with the manifest (collection
# healthy, graph-only loss), the reconcile rebuilds the GRAPH ONLY (re-chunk +
# re-graph each indexed .py file) WITHOUT re-embedding or purging the vectors. A
# new indexer surface ``Indexer.rebuild_graph_only(tier) -> int`` does the per-file
# _chunk + _refresh_graph (no embed, no upsert, no delete_by_tier).
#
# When the count ALSO diverged (collection wiped/short too), the existing
# purge+reset full-rebuild path still applies (TestWipedCollectionHeals /
# TestWipedGraphHeals) — that path rebuilds the graph anyway, so it is unchanged.


def _graph_with_roots(
    config: LoreConfig, graph_path: Path, snapshot_root: Path
) -> CodeGraph:
    """A CodeGraph wired with the config's project roots (resolution enabled).

    The graph-only heal re-graphs from disk through ``rebuild_graph_only``, which
    needs the SAME astroid resolution the production-constructed graph has, so the
    re-graphed import edges resolve (a rootless graph would emit only structural
    ``defines`` and ``what_imports`` would find nothing). Uses the production
    :func:`graph_roots` so the test graph resolves exactly as the server does.
    """
    from loremaster.index.indexer import graph_roots

    tier_roots, project_roots = graph_roots(config, snapshot_root)
    return CodeGraph(
        str(graph_path), tier_roots=tier_roots, project_roots=project_roots
    )


def _make_graph_wired_indexer(
    *,
    config: LoreConfig,
    store: QdrantStore,
    embedder: Any,
    manifest: Manifest,
    code_graph: CodeGraph,
    snapshot_root: Path,
) -> Any:
    """Wire a real :class:`Indexer` with the code graph injected — the PROD shape.

    Mirrors the production builder at ``build_app_context`` (server.py:1481): the
    SAME registry, source providers, config, snapshot root, AND ``code_graph``
    that the reconcile's graph-only heal will drive. Grounding the fixture in the
    production wiring (clause 5) means the test exercises the real ``_chunk`` +
    ``_refresh_graph`` path, not a hand-rolled double.
    """
    from loremaster.index.indexer import Indexer
    from loremaster.source.local_directory import LocalDirectorySourceProvider

    server = LoreServer(config)
    providers: list[Any] = list(server.source_providers)
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
        code_graph=code_graph,
    )


def _wipe_graph_rows(graph_path: Path) -> int:
    """Delete every graph node/ref row behind the manifest's back; return prior file count.

    The graph-only divergence injector: clears the graph's ``CodeNode`` + ``Ref``
    node tables (leaving the manifest + the vector collection intact). Uses the
    real Kùzu node tables the production graph reads (DETACH DELETE), so the
    fixture is grounded in the actual DB (the same wipe ``TestWipedGraphHeals``
    performs). Returns the graph's indexed-file count BEFORE the wipe so a caller
    can assert the heal restored it.
    """
    graph = CodeGraph(str(graph_path))
    try:
        prior = graph.indexed_file_count()
        graph.connection.execute("MATCH (n:CodeNode) DETACH DELETE n")
        graph.connection.execute("MATCH (r:Ref) DETACH DELETE r")
        return prior
    finally:
        graph.close()


class TestGraphOnlyHealDoesNotReEmbed:
    """A graph-only loss (healthy collection) re-graphs WITHOUT a vector re-embed.

    THE EFFICIENCY WIN. When the graph is wiped but the live point count AGREES
    with the manifest, the reconcile must rebuild the graph ONLY — no
    ``delete_by_tier`` purge, no re-embed. Independent oracles, all read from the
    LIVE store / graph, never the reconcile internals:
        1. The graph repopulates (indexed-file count back to the seeded value) and
           a real ``what_imports`` query returns edges again.
        2. ``delete_by_tier`` is NEVER called for the tier (the spy records ZERO
           purges) — the collection is not blown away.
        3. ``count_points(tier)`` is UNCHANGED across the whole heal (no re-embed,
           no orphaning) — the vectors are exactly the same set.
    """

    async def test_graph_only_loss_regraphs_without_purge_or_count_change(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: seed a real index (collection + graph healthy). WIPE ONLY the
                 graph rows, leaving the collection intact.
        Act: run reconcile_store_divergence (bare) with a delete_by_tier SPY and the
             real graph-wired Indexer wired in (the prod collaborator set).
        Assert: graph healed (file count restored, what_imports hits) AND the spy
                recorded ZERO purges AND count_points(tier) is unchanged.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)  # has .py files → graph genuinely populated
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        # Step 1: seed a real, fully-healthy index (collection + graph), then close.
        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # The collection is healthy: live count == expected, both > 0. This is the
        # precondition that makes a vector re-embed pure waste (clause 1: realistic
        # healthy index, not a convenience shape).
        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        count_before = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert count_before == expected and expected > 0, (
            f"test setup: the seeded collection must be HEALTHY (live {count_before} "
            f"== expected {expected} > 0) — a vector re-embed on a graph-only loss "
            "must therefore be pure waste"
        )

        # Step 2: WIPE ONLY the graph rows (collection untouched) — the graph-only
        # loss shape this fix optimises.
        seeded_graph_files = _wipe_graph_rows(graph_path)
        assert seeded_graph_files > 0, (
            "test setup: the seed must have populated the graph (so the wipe is a "
            "real loss, not a no-op)"
        )

        # Step 3: run the BARE reconcile with a delete_by_tier spy AND the real
        # graph-wired indexer (the new collaborator the graph-only heal drives).
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy_store = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        manifest2 = Manifest(str(manifest_path))
        graph2 = _graph_with_roots(config, graph_path, snap)
        indexer = _make_graph_wired_indexer(
            config=config, store=spy_store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest2, code_graph=graph2, snapshot_root=snap,
        )
        try:
            await spy_store.ensure_collection(_DIM)
            from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

            # The NEW seam: the reconcile accepts the indexer so it can re-graph
            # without re-embedding. The keyword is the contract; the impl wires it
            # from build_app_context's already-constructed indexer.
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy_store,
                manifest=manifest2,
                code_graph=graph2,
                config=config,
                indexer=indexer,
            )
        finally:
            manifest2.close()
            graph2.close()
            await client.close()

        # ASSERT 2 (efficiency oracle): NO tier was purged. A graph-only loss over a
        # healthy collection must NOT blow the vectors away.
        assert spy_store.purged_tiers == [], (
            "a graph-only loss over a HEALTHY collection must re-graph WITHOUT a "
            f"vector purge; the reconcile called delete_by_tier on "
            f"{spy_store.purged_tiers!r} — that forces a wasteful full re-embed of "
            "an intact collection (the FP-04 follow-up the fix removes)"
        )

        # ASSERT 3 (efficiency oracle): the live count is UNCHANGED — no re-embed,
        # no orphaning. The exact same vector set is still there.
        count_after = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert count_after == count_before, (
            f"the graph-only heal must leave the vector collection UNTOUCHED: "
            f"count_points({_LIVE_TIER}) was {count_before} before and {count_after} "
            "after — a changed count means the heal re-embedded/purged an intact "
            "collection (the waste this fix exists to remove)"
        )

        # ASSERT 1 (heal oracle): the graph repopulated and a real query hits again.
        healed_graph = CodeGraph(str(graph_path))
        healed_graph_files = healed_graph.indexed_file_count()
        healed_graph.close()
        assert healed_graph_files == seeded_graph_files, (
            f"the graph-only heal must repopulate the graph: indexed-file count must "
            f"return to {seeded_graph_files}; got {healed_graph_files}"
        )

        # what_imports('os') must find the importer again — proves the re-graph
        # rebuilt real edges, not just node rows. Read via a throwaway graph-wired
        # context so the query runs through the production graph API.
        verify_graph = CodeGraph(str(graph_path))
        try:
            importers = verify_graph.what_imports(_REP_MODULE_IMPORT)
        finally:
            verify_graph.close()
        assert len(importers) >= 1, (
            f"after the graph-only heal, what_imports({_REP_MODULE_IMPORT!r}) must "
            "return the importing module again — an empty graph returns nothing"
        )


class TestRebuildGraphOnlyIndexerMethod:
    """``Indexer.rebuild_graph_only(tier)`` re-graphs a tier's .py files, no embed.

    The new indexer primitive the graph-only heal drives. For each indexed file in
    the tier it does ``_chunk`` + ``_refresh_graph`` — NO embed, NO upsert, NO
    delete_by_tier. Oracles read the LIVE graph + the LIVE store count: the graph
    repopulates (a real what_imports hit) and the vector count is unchanged.
    """

    async def test_rebuild_graph_only_repopulates_graph_without_touching_vectors(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: seed a real index; WIPE ONLY the graph rows.
        Act: call indexer.rebuild_graph_only(live_tier) directly.
        Assert: returns the re-graphed file count (> 0) AND the graph repopulated
                AND count_points(tier) unchanged AND no purge fired.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        count_before = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert count_before > 0, "test setup: the seed must produce >0 points"

        seeded_graph_files = _wipe_graph_rows(graph_path)
        assert seeded_graph_files > 0, "test setup: the seed must populate the graph"

        # Drive the new primitive directly through a graph-wired indexer + a
        # delete_by_tier spy so we can prove it neither embeds nor purges.
        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy_store = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        manifest2 = Manifest(str(manifest_path))
        graph2 = _graph_with_roots(config, graph_path, snap)
        indexer = _make_graph_wired_indexer(
            config=config, store=spy_store, embedder=FakeEmbedder(dim=_DIM),
            manifest=manifest2, code_graph=graph2, snapshot_root=snap,
        )
        try:
            await spy_store.ensure_collection(_DIM)
            # The NEW indexer surface under contract: re-graph the tier's .py files.
            regraphed = await indexer.rebuild_graph_only(_LIVE_TIER)  # type: ignore[attr-defined]
        finally:
            manifest2.close()
            graph2.close()
            await client.close()

        # Return-value oracle: the method reports how many files it re-graphed —
        # the count of indexed graph-eligible (.py) files in the tier, > 0 for the
        # widget/routing corpus. (Pure-logic count of the tier's .py rows; an exact
        # equality to the prior graph file count is the independent oracle.)
        assert regraphed == seeded_graph_files, (
            f"rebuild_graph_only({_LIVE_TIER!r}) must re-graph every indexed .py file "
            f"in the tier and report the count ({seeded_graph_files}); got {regraphed}"
        )

        # The graph repopulated (LIVE graph read).
        healed_graph = CodeGraph(str(graph_path))
        healed_graph_files = healed_graph.indexed_file_count()
        try:
            importers = healed_graph.what_imports(_REP_MODULE_IMPORT)
        finally:
            healed_graph.close()
        assert healed_graph_files == seeded_graph_files, (
            f"rebuild_graph_only must restore the graph file count to "
            f"{seeded_graph_files}; got {healed_graph_files}"
        )
        assert len(importers) >= 1, (
            f"rebuild_graph_only must rebuild real edges: what_imports("
            f"{_REP_MODULE_IMPORT!r}) must hit again"
        )

        # No embed / no purge: the live vector count is byte-identical and the spy
        # saw zero purges.
        count_after = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert count_after == count_before, (
            f"rebuild_graph_only must NOT touch the vectors: count_points({_LIVE_TIER}) "
            f"was {count_before}, now {count_after} — it must do _chunk + _refresh_graph "
            "only (no embed, no upsert)"
        )
        assert spy_store.purged_tiers == [], (
            f"rebuild_graph_only must NOT purge the collection; it called "
            f"delete_by_tier on {spy_store.purged_tiers!r}"
        )


# ===========================================================================
# FIX 2 — rebuilding-notice covers the divergence heal window (forward-safety)
# ===========================================================================
# The divergence heal purges/re-embeds (or graph-only re-graphs) but does NOT set
# the schema_rebuild_status meta, so the read-tools' rebuilding-notice (which
# raises SchemaRebuildingError on an empty result mid-rebuild) does NOT cover the
# heal window — a read landing mid-heal sees a silent empty result rather than the
# rebuilding signal. The fix: when reconcile_store_divergence HEALS a tier (purge
# +reset OR graph-only), it sets the rebuild-status meta to ``in_progress`` for the
# duration and CLEARS it (out of in_progress) on completion; a HEALTHY no-heal
# reconcile leaves the meta untouched.
#
# The independent oracle is the SHARED rebuilding_notice() / SCHEMA_REBUILD_STATUS
# _META_KEY the production read-tools consult (clause 5) — not a hand-copied
# literal. A status-observing manifest captures the in_progress write the instant
# the heal fires (the meta is cleared by the time the reconcile returns, so a
# plain after-the-fact read cannot see the in-progress window).


class _StatusObservingManifest(Manifest):
    """A :class:`Manifest` that records every rebuild-status state the heal writes.

    The heal sets the status to ``in_progress`` then clears it before returning, so
    a plain post-reconcile read would only ever see the cleared state. This spy
    captures the SEQUENCE of states written to ``SCHEMA_REBUILD_STATUS_META_KEY``
    during the reconcile — the independent oracle for "did the heal open and close
    the rebuilding window?" It observes a public ``meta_set``; it does not mirror
    the reconcile internals (clause 2).
    """

    def __init__(self, db_path: str) -> None:
        super().__init__(db_path)
        # Ordered list of (state) values written to the rebuild-status key.
        self.rebuild_status_states_written: list[str | None] = []

    def meta_set(self, key: str, value: str) -> None:
        from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

        if key == SCHEMA_REBUILD_STATUS_META_KEY:
            try:
                parsed = json.loads(value)
                state = parsed.get("state") if isinstance(parsed, dict) else None
            except (ValueError, TypeError):
                state = None
            self.rebuild_status_states_written.append(state)
        super().meta_set(key, value)


def _rebuild_status_state(manifest_path: Path) -> str | None:
    """Read the CURRENT rebuild-status ``state`` from the manifest meta, or None.

    Reads ``SCHEMA_REBUILD_STATUS_META_KEY`` through the SAME parse the production
    ``rebuilding_notice`` uses (clause 5: shared source of truth) and returns the
    ``state`` field — ``in_progress`` / ``done`` / ``idle`` — or ``None`` when no
    status is recorded or the blob is malformed.
    """
    from loremaster.index.schema import SCHEMA_REBUILD_STATUS_META_KEY

    manifest = Manifest(str(manifest_path))
    try:
        raw = manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
    finally:
        manifest.close()
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed.get("state")


# The in_progress state value the production rebuilding_notice keys on — obtained
# by exercising the shared rebuilding_notice() over a known in_progress blob would
# be circular; instead we pin the literal the schema module already exports as the
# contract value the heal must write. Read it from the shared parse helper above.
_IN_PROGRESS_STATE = "in_progress"


class TestDivergenceHealSetsRebuildingNotice:
    """A divergence heal opens + closes the rebuilding-notice window; a no-op leaves it.

    The forward-safety fix: while reconcile_store_divergence HEALS a tier, the
    rebuild-status meta reads ``in_progress`` so a read tool landing mid-heal sees
    the rebuilding signal (and raises SchemaRebuildingError on an empty result)
    rather than a silent empty; the status is cleared (out of in_progress) on
    completion. A HEALTHY no-heal reconcile must NOT touch the meta.
    """

    async def test_heal_writes_in_progress_then_clears_it(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """Arrange: seed a real index; WIPE the collection (a count divergence to heal).
        Act: run reconcile_store_divergence with a status-observing manifest.
        Assert: the heal WROTE an in_progress rebuild-status during the heal
                (captured by the observer) AND the final state is NOT in_progress
                (cleared on completion).
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # WIPE the collection empty behind the manifest (the count divergence).
        from qdrant_client import models as qmodels

        mutator = divergence_harness["mutator_client"]
        await mutator.delete_collection(f"lore_{slug}")
        await mutator.create_collection(
            collection_name=f"lore_{slug}",
            vectors_config=qmodels.VectorParams(size=_DIM, distance=qmodels.Distance.COSINE),
        )

        # Run the reconcile with a status-OBSERVING manifest so the transient
        # in_progress write is captured even though it is cleared before return.
        from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        observing = _StatusObservingManifest(str(manifest_path))
        g = CodeGraph(str(graph_path))
        try:
            await spy.ensure_collection(_DIM)
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy, manifest=observing, code_graph=g, config=config,
            )
            # Precondition sanity: the reconcile DID heal (it purged the wiped tier),
            # so the rebuilding window SHOULD have been opened.
            assert _LIVE_TIER in spy.purged_tiers, (
                "test setup: a wiped tier must be purged by the heal; "
                f"purged {spy.purged_tiers!r}"
            )
            states_written = list(observing.rebuild_status_states_written)
        finally:
            observing.close()
            g.close()
            await client.close()

        # ASSERT 1 (independent oracle): the heal OPENED the rebuilding window — an
        # in_progress status was written during the heal so a concurrent read tool
        # sees the rebuilding signal rather than a silent empty result.
        assert _IN_PROGRESS_STATE in states_written, (
            "a divergence heal must set the schema_rebuild_status to 'in_progress' "
            "for the heal window so the read-tools' rebuilding-notice covers it; the "
            f"heal wrote states {states_written!r} — none of them in_progress (the "
            "read landing mid-heal would see a silent empty, not the rebuilding signal)"
        )

        # ASSERT 2 (independent oracle): the window is CLOSED on completion — the
        # final state is NOT in_progress, so a read AFTER the heal does not get a
        # phantom rebuilding-notice for a finished heal.
        final_state = _rebuild_status_state(manifest_path)
        assert final_state != _IN_PROGRESS_STATE, (
            "the divergence heal must CLEAR the rebuilding-notice on completion (out "
            f"of in_progress); the final schema_rebuild_status state is {final_state!r} "
            "— a heal that leaves in_progress set wedges every read into a phantom "
            "rebuilding-notice"
        )

    async def test_healthy_no_heal_reconcile_leaves_rebuild_status_untouched(
        self, divergence_harness: Any, tmp_path: Path
    ) -> None:
        """A reconcile that heals NOTHING (healthy index) must not write the meta.

        Arrange: seed a genuinely-healthy index (no divergence).
        Act: run reconcile_store_divergence with a status-observing manifest.
        Assert: NO rebuild-status state was written (the no-op heal does not open a
                phantom rebuilding window) AND no tier was purged.
        """
        # real-Qdrant
        from conftest import QDRANT_URL, _qdrant_api_key

        slug = _slug()
        live = tmp_path / "live"
        _build_live_corpus(live)
        config = divergence_harness["config"](slug=slug, live_path=live)
        manifest_path = tmp_path / "m.db"
        graph_path = tmp_path / "graph.kuzu"
        snap = tmp_path / "snap"

        seed = await divergence_harness["build"](
            config=config, manifest_path=manifest_path, graph_path=graph_path,
            snapshot_root=snap, start_tasks=True,
        )
        await seed.reindex(None)
        await seed.aclose()

        # Sanity: the index is genuinely healthy (live == expected, > 0).
        manifest = Manifest(str(manifest_path))
        expected = manifest.expected_chunks(_LIVE_TIER)  # type: ignore[attr-defined]
        manifest.close()
        live_now = await _live_count(
            slug=slug, tier=_LIVE_TIER, url=QDRANT_URL, api_key=_qdrant_api_key(),
        )
        assert live_now == expected and expected > 0, (
            f"test setup: the seeded index must be HEALTHY (live {live_now} == "
            f"expected {expected} > 0) so the reconcile heals nothing"
        )

        from loremaster.server import reconcile_store_divergence  # type: ignore[import-not-found]

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        spy = DeleteByTierSpyStore(client=client, slug=slug)
        divergence_harness["register"](slug)
        observing = _StatusObservingManifest(str(manifest_path))
        g = CodeGraph(str(graph_path))
        try:
            await spy.ensure_collection(_DIM)
            await reconcile_store_divergence(  # type: ignore[misc]
                store=spy, manifest=observing, code_graph=g, config=config,
            )
            states_written = list(observing.rebuild_status_states_written)
        finally:
            observing.close()
            g.close()
            await client.close()

        # ASSERT (independent oracle): a healthy no-heal reconcile must NOT write the
        # rebuild-status meta at all — opening a rebuilding window with no work would
        # wedge reads into a phantom notice on every clean boot.
        assert spy.purged_tiers == [], (
            f"test setup: a healthy index must not be purged; purged {spy.purged_tiers!r}"
        )
        assert states_written == [], (
            "a HEALTHY no-heal reconcile must leave schema_rebuild_status UNTOUCHED; "
            f"it wrote states {states_written!r} — a phantom rebuilding window on a "
            "clean boot would make every read raise SchemaRebuildingError needlessly"
        )
