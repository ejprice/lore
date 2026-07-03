"""Live integration contract for P5-C4 (ledger #25) WIRING: ``Indexer.
index_all()``, ``ReconcileEngine.reconcile()`` (the watcher's ``run_sweep``
path) and ``Indexer.rebuild_all()`` must stamp a :class:`~loremaster.index.
snapshots.SnapshotStamper` snapshot ON FULL SWEEP SUCCESS ONLY.

THIS FILE DOES NOT RE-PIN ``SnapshotStamper``'S OWN BEHAVIOUR (entry
fidelity, git identity, GC) — that contract lives in ``test_snapshots.py``.
This file pins ONLY what the wiring at the indexer/reconcile seam adds:

* A fully-successful sweep (``files_failed == 0``, something was genuinely
  indexed) stamps EXACTLY ONE new snapshot.
* A sweep containing a deliberately failing file stamps NOTHING — not even a
  partial snapshot for the files that DID succeed.
* A NO-OP sweep (every file fast-path-skipped, zero changes) does NOT create
  a new snapshot — snapshots mark real generations, not heartbeats (this also
  keeps the table from growing every 600s under the periodic reconcile).
* A GENUINE second change (something actually re-indexed) DOES produce a
  second, distinct snapshot — proving the no-op guard isn't just "never
  stamp twice".
* ``ReconcileEngine.reconcile()`` and ``Indexer.rebuild_all()`` follow the
  identical stamp-on-full-success rule.

THE PINNED WIRING SURFACE (this contract's own design decision, named here,
blind to any implementation)
-----------------------------------------------------------------------
``Indexer.__init__`` and ``ReconcileEngine.__init__`` each gain one new
OPTIONAL keyword-only collaborator, mirroring the existing ``code_graph:
Any = None`` optional-dependency pattern::

    Indexer(..., snapshot_stamper: Any = None)
    ReconcileEngine(..., snapshot_stamper: Any = None)

When wired, ``index_all()`` / ``reconcile()`` / ``rebuild_all()`` call
``await snapshot_stamper.stamp()`` iff the sweep's own
:class:`~loremaster.index.indexer.IndexSummary` shows ``files_failed == 0``
AND ``files_indexed > 0`` (something was genuinely (re-)embedded, not merely
fast-path-skipped). ``snapshot_stamper=None`` is a no-op (back-compat).

RED STRATEGY
------------
Neither ``Indexer`` nor ``ReconcileEngine`` accepts a ``snapshot_stamper``
keyword yet, so constructing either with it raises ``TypeError`` — a
behavioural RED at fixture-setup time, not a collection error (``Indexer``/
``ReconcileEngine`` themselves already import cleanly). This is DELIBERATE:
per the CONTRACT-phase brief, ``indexer.py``/``reconcile.py`` are NOT modified
by this contract — the implementer wires the hook in a later phase.
``loremaster.index.snapshots`` also does not exist yet, so that import is
guarded the same way ``test_snapshots.py`` guards it.

Runs against the REAL 3.1.5 dev server (``_surreal_harness`` per-test DB
isolation) — mirrors ``test_indexer_surreal_integration.py``'s ``bench``
fixture pattern, minus the code-graph collaborator (irrelevant here).
"""

from __future__ import annotations

import subprocess
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    SurrealEnv,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
)
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer
from loremaster.index.reconcile import ReconcileEngine
from loremaster.index.surreal_manifest import SurrealManifest
from loremaster.server import LoreServer
from loremaster.store.surreal import SurrealStore
from loremaster.store.surreal_schema import SNAPSHOT_TABLE
from loresigil.testing import FakeEmbedder

try:
    from loremaster.index.snapshots import SnapshotStamper

    _SNAPSHOTS_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P5-C4 RED: the module does not exist
    _SNAPSHOTS_API_AVAILABLE = False
    SnapshotStamper = None  # type: ignore[assignment,misc]


_DIM = PRODUCTION_DIM

_PRICING_SOURCE = "def compute_margin(cost, price):\n    return price - cost\n"
_PRICING_SOURCE_V2 = (
    "def compute_margin(cost, price):\n    return price - cost\n\n"
    "def compute_discount(price, rate):\n    return price * (1 - rate)\n"
)
_BROKEN_SOURCE = "def poison():\n    return 1\n"

# A well-formed SHA-256-shaped fingerprint literal — its FORMAT (a stable
# opaque token `rebuild_all` threads through), not its content, is what
# matters to this contract.
_FINGERPRINT = "f" * 64


def _init_git_repo(repo_root: Path, *, branch: str) -> None:
    """Create a real, empty git repo at ``repo_root`` on ``branch``."""
    repo_root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", str(repo_root)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "checkout", "-b", branch], check=True, capture_output=True
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.email", "lore-test@example.com"],
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "-C", str(repo_root), "config", "user.name", "Lore Test"],
        check=True,
        capture_output=True,
    )


def _commit_file(repo_root: Path, filename: str, content: str, message: str) -> None:
    (repo_root / filename).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", message], check=True, capture_output=True
    )


def _config(*, slug: str, live_path: Path) -> LoreConfig:
    """A minimal single-live-root config at the real production embedding dim."""
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
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
        "roots": [
            {
                "tier": TIER_A,
                "watch": "live",
                "path": str(live_path),
                "include": ["**/*.py"],
                "exclude": [],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": [],
        "chunkers": {".py": {"chunker": "python_ast"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9202},
    }
    return LoreConfig.model_validate(payload)


async def _snapshot_rows(env: SurrealEnv) -> list[dict[str, Any]]:
    connection = await connect_admin(env)
    try:
        result = await run(connection, f"SELECT * FROM {SNAPSHOT_TABLE}")
    finally:
        await connection.close()
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


@dataclass(frozen=True)
class _WiringBench:
    """The rewired Indexer + ReconcileEngine, wired to a REAL SnapshotStamper."""

    indexer: Indexer
    engine: ReconcileEngine
    store: SurrealStore
    manifest: SurrealManifest
    stamper: Any
    env: SurrealEnv
    config: LoreConfig
    live_root: Path


@pytest_asyncio.fixture()
async def wiring_bench(
    surreal_env: SurrealEnv,  # noqa: F811 - imported fixture
    tmp_path: Path,
) -> AsyncIterator[_WiringBench]:
    live_root = tmp_path / "live"
    live_root.mkdir(parents=True)
    project_root = tmp_path / "project"
    _init_git_repo(project_root, branch="feat/pricing-refactor")
    _commit_file(project_root, "README.md", "# demo project\n", "initial commit")

    config = _config(slug=surreal_env.database, live_path=live_root)

    store = SurrealStore(
        url=surreal_env.url, namespace=surreal_env.namespace,
        database=surreal_env.database, dim=_DIM,
        user=surreal_env.user, password=surreal_env.password,
    )
    manifest = SurrealManifest(
        url=surreal_env.url, namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user, password=surreal_env.password,
    )
    await store.ensure_ready()
    await manifest.ensure_ready()

    stamper = SnapshotStamper(
        url=surreal_env.url, namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user, password=surreal_env.password,
        store=store, manifest=manifest, project_root=project_root,
    )
    await stamper.ensure_ready()

    server = LoreServer(config)
    indexer = Indexer(
        store=store,
        embedder=FakeEmbedder(dim=_DIM),
        manifest=manifest,
        registry=server.registry,
        source_providers=[],
        config=config,
        snapshot_root=tmp_path / "snap",
        snapshot_stamper=stamper,
    )
    engine = ReconcileEngine(
        indexer=indexer, manifest=manifest, store=store, config=config,
        snapshot_stamper=stamper,
    )
    try:
        yield _WiringBench(
            indexer=indexer, engine=engine, store=store, manifest=manifest,
            stamper=stamper, env=surreal_env, config=config, live_root=live_root,
        )
    finally:
        await stamper.close()
        await store.close()
        await manifest.close()


def _write_pricing_file(live_root: Path, source: str = _PRICING_SOURCE) -> Path:
    (live_root / "src").mkdir(parents=True, exist_ok=True)
    path = live_root / "src" / "pricing.py"
    path.write_text(source, encoding="utf-8")
    return path


# ===========================================================================
# Full success → exactly one snapshot.
# ===========================================================================


class TestIndexAllStampsExactlyOneSnapshotOnFullSuccess:
    async def test_index_all_stamps_a_snapshot_matching_the_indexed_files(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)

        summary = await wiring_bench.indexer.index_all()
        assert summary.files_failed == 0
        assert summary.files_indexed >= 1

        rows = await _snapshot_rows(wiring_bench.env)
        assert len(rows) == 1
        assert rows[0]["files_total"] == summary.files_indexed


class TestReconcileStampsExactlyOneSnapshotOnFullSuccess:
    async def test_reconcile_stamps_a_snapshot_matching_the_indexed_files(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)

        summary = await wiring_bench.engine.reconcile()
        assert summary.files_failed == 0
        assert summary.files_indexed >= 1

        rows = await _snapshot_rows(wiring_bench.env)
        assert len(rows) == 1
        assert rows[0]["files_total"] == summary.files_indexed


class TestRebuildAllStampsAfterFullSuccess:
    async def test_rebuild_all_stamps_a_snapshot_reflecting_the_rebuilt_state(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)

        summary = await wiring_bench.indexer.rebuild_all(_FINGERPRINT)
        assert summary.files_failed == 0
        assert summary.files_indexed >= 1

        rows = await _snapshot_rows(wiring_bench.env)
        assert len(rows) == 1
        assert rows[0]["files_total"] == summary.files_indexed


# ===========================================================================
# A failing file stamps NOTHING.
# ===========================================================================


class TestIndexAllDoesNotStampWhenAnyFileFails:
    async def test_index_all_creates_no_snapshot_when_one_file_fails_to_embed(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)
        (wiring_bench.live_root / "src" / "broken.py").write_text(
            _BROKEN_SOURCE, encoding="utf-8"
        )

        # Learn broken.py's real chunk text, then swap in an embedder that
        # PERMANENTLY fails exactly that text (reuses the production chunk
        # path — mirrors test_indexer_surreal_integration.py's own pattern).
        texts = wiring_bench.indexer.chunk_texts(TIER_A, "src/broken.py", _BROKEN_SOURCE)
        assert texts
        failing_indexer = Indexer(
            store=wiring_bench.store,
            embedder=FakeEmbedder(dim=_DIM, fail_inputs=set(texts)),
            manifest=wiring_bench.manifest,
            registry=LoreServer(wiring_bench.config).registry,
            source_providers=[],
            config=wiring_bench.config,
            snapshot_root=wiring_bench.live_root.parent / "snap",
            snapshot_stamper=wiring_bench.stamper,
        )

        summary = await failing_indexer.index_all()
        assert summary.files_failed >= 1

        # NOTHING was stamped — not even a partial snapshot for pricing.py,
        # which succeeded.
        assert await _snapshot_rows(wiring_bench.env) == []


# ===========================================================================
# A no-op sweep stamps nothing (again); a genuine change stamps again.
# ===========================================================================


class TestNoOpSweepDoesNotCreateANewSnapshot:
    async def test_second_index_all_with_zero_changes_does_not_add_a_snapshot(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)

        first_summary = await wiring_bench.indexer.index_all()
        assert first_summary.files_indexed >= 1
        first_rows = await _snapshot_rows(wiring_bench.env)
        assert len(first_rows) == 1
        first_id = str(first_rows[0]["id"])

        # Nothing on disk changed — the mtime+size fast-path skips every file.
        second_summary = await wiring_bench.indexer.index_all()
        assert second_summary.files_indexed == 0
        assert second_summary.files_failed == 0

        second_rows = await _snapshot_rows(wiring_bench.env)
        assert len(second_rows) == 1  # still just the one — no heartbeat snapshot
        assert str(second_rows[0]["id"]) == first_id


class TestReconcileNoOpSweepDoesNotCreateANewSnapshot:
    async def test_second_reconcile_with_zero_changes_does_not_add_a_snapshot(
        self, wiring_bench: _WiringBench
    ) -> None:
        _write_pricing_file(wiring_bench.live_root)

        await wiring_bench.engine.reconcile()
        assert len(await _snapshot_rows(wiring_bench.env)) == 1

        second_summary = await wiring_bench.engine.reconcile()
        assert second_summary.files_indexed == 0
        assert second_summary.files_failed == 0
        assert second_summary.files_purged == 0

        assert len(await _snapshot_rows(wiring_bench.env)) == 1  # unchanged


class TestAGenuineChangeDoesStampAgain:
    async def test_a_real_content_change_produces_a_second_distinct_snapshot(
        self, wiring_bench: _WiringBench
    ) -> None:
        pricing_path = _write_pricing_file(wiring_bench.live_root)

        await wiring_bench.indexer.index_all()
        first_rows = await _snapshot_rows(wiring_bench.env)
        assert len(first_rows) == 1

        pricing_path.write_text(_PRICING_SOURCE_V2, encoding="utf-8")
        summary = await wiring_bench.indexer.index_all()
        assert summary.files_indexed >= 1  # genuinely re-embedded, not skipped
        assert summary.files_failed == 0

        second_rows = await _snapshot_rows(wiring_bench.env)
        assert len(second_rows) == 2
        ids = {str(row["id"]) for row in second_rows}
        assert len(ids) == 2  # two DISTINCT snapshots, never a re-used id
