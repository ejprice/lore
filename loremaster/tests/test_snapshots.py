"""Contract tests for P5-C4 (ledger #25): ``loremaster.index.snapshots`` —
snapshot + snapshot_entry stamping on sweep completion.

Versioning is first-class in v1.0: a ``snapshot`` row is a full-project index
GENERATION marker, and its ``snapshot_entry`` children are the per-file
digest/chunk-identity ledger that later powers ``lore_diff`` and a
``changed_since`` query. The DDL for both tables already landed (P5-C1b,
``surreal_schema._snapshot_statements`` / ``_snapshot_entry_statements``,
pinned raw at ``test_surreal_schema.py::TestSnapshotRoundTrip`` /
``TestSnapshotEntryRoundTrip``). THIS file pins the layer ABOVE that schema —
the production WRITER that decides what a snapshot row/entry set actually
contains and when it is safe to create one.

THE PINNED PUBLIC API SURFACE (named here, blind to any implementation)
-----------------------------------------------------------------------
``loremaster.index.snapshots``::

    def capture_git_identity(repo_root: Path) -> tuple[str | None, str | None]:
        # (git_ref, git_branch) read from `repo_root`'s OWN git state (not the
        # caller's cwd). (None, None) for a non-git / nonexistent / non-directory
        # `repo_root` — NEVER raises. A detached HEAD yields (full_sha, None).

    class SnapshotStamper:
        def __init__(
            self, *, url: str, namespace: str, database: str, user: str,
            password: str, store: SurrealStore, manifest: SurrealManifest,
            project_root: Path,
        ) -> None: ...

        async def ensure_ready(self) -> None: ...
        async def close(self) -> None: ...

        async def stamp(self) -> str:
            # Reads EVERY currently-``indexed`` row from `manifest`, captures git
            # identity from `project_root`, and for each indexed (tier, file_path)
            # reads that file's REAL chunk rows from `store` (identity +
            # content_hash) to build `chunk_hashes`. Writes ONE `snapshot` row
            # (files_total/chunks_total/git_ref/git_branch) + one `snapshot_entry`
            # per indexed file (tier/file_path/sha512/chunk_hashes), and returns
            # the new snapshot's stringified record id (e.g. "snapshot:abc123").
            # UNCONDITIONAL: `stamp()` itself does not decide "should I stamp
            # right now" — that gate (full sweep success, sweep did something)
            # is the CALLER's job (see ``test_indexer_snapshot_wiring.py``). A
            # manifest with zero indexed rows still produces a well-formed,
            # zero-total, zero-entry snapshot rather than raising.

        async def delete_snapshot(self, snapshot_id: str) -> None:
            # Deletes the `snapshot` row AND every `snapshot_entry` referencing
            # it (record links do NOT auto-clean on delete — docs-audit
            # constraint). Scoped to `snapshot_id` only; a sibling snapshot's row
            # and entries are untouched. Idempotent: deleting an unknown
            # `snapshot_id` is a no-op, never an error.

Lifecycle convention: like its sibling ports (``SurrealStore`` /
``SurrealManifest`` / ``SurrealCodeGraph``), ``SnapshotStamper`` owns its OWN
connection (same ``url``/``namespace``/``database``/``user``/``password``
construction), exposed at ``self._connection`` for the same mid-life-drop
self-heal contract those three already have (mirrors
``test_surreal_manifest.py::TestMidLifeConnectionRecovery``).

RED STRATEGY
------------
``loremaster.index.snapshots`` does not exist yet, so the import below is
guarded (mirrors ``test_surreal_apply.py``'s pattern for a brand-new top-level
API): the file COLLECTS, and every test that actually exercises the missing
API fails on ITS OWN behaviour (calling ``None(...)`` raises ``TypeError``)
rather than one collection error hiding the whole contract. The pure
``TestCaptureGitIdentity`` cases need no live server; every other class runs
against the REAL 3.1.5 dev server (``_surreal_harness`` per-test DB isolation)
— chunk-table reads, snapshot writes, and the GC delete are all server-side
properties with no in-memory shortcut worth faking.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
import pytest_asyncio
from _surreal_harness import (
    PRODUCTION_DIM,
    TIER_A,
    SurrealEnv,
    call_until_recovered,
    chunk_record,
    connect_admin,
    run,
    surreal_env,  # noqa: F401 - re-exported pytest fixture
    unit_vector,
)
from loremaster.index.records import sha512_hex
from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest
from loremaster.store._txn import TxnFragment, compose
from loremaster.store.surreal import (
    _CONNECTION_ERRORS,
    SurrealStore,
    SurrealStoreError,
)
from loremaster.store.surreal_schema import (
    FILE_STATES,
    FILE_TABLE,
    SNAPSHOT_ENTRY_TABLE,
    SNAPSHOT_TABLE,
)

try:
    from loremaster.index.snapshots import SnapshotStamper, capture_git_identity

    _SNAPSHOTS_API_AVAILABLE = True
except ImportError:  # pragma: no cover - pre-P5-C4 RED: the module does not exist
    _SNAPSHOTS_API_AVAILABLE = False
    SnapshotStamper = None  # type: ignore[assignment,misc]
    capture_git_identity = None  # type: ignore[assignment]


_DIM = PRODUCTION_DIM
_TIER = TIER_A

# A file.state value deliberately OUTSIDE the schema's closed domain — reused
# from ``test_surreal_apply.py``'s own verified poison: a CREATE setting
# ``state`` to this value is guaranteed rejected by the ``file.state`` field
# ASSERT (``surreal_schema._file_statements``), independent of anything this
# module implements. Used to prove ``SnapshotStamper.stamp()`` composes ONE
# real transaction — an unrelated statement's rejection must roll back the
# WHOLE thing, including the snapshot row and entries that would otherwise
# already have landed under the old N+1-CREATE implementation.
_INVALID_FILE_STATE = "__definitely_not_a_valid_state__"

# The self-heal error vocabulary a healthy, self-healing port may surface
# across a mid-life socket drop — mirrors
# ``test_surreal_manifest.py``'s identical ``_HEALABLE_ERRORS``.
_HEALABLE_ERRORS: tuple[type[BaseException], ...] = (SurrealStoreError, *_CONNECTION_ERRORS)


# ===========================================================================
# Git-repo test helpers — build REAL repos on disk; every "expected" value
# below comes from an INDEPENDENT `git` subprocess invocation, never routed
# through `capture_git_identity` itself.
# ===========================================================================


def _run_git(repo_root: Path, *args: str) -> str:
    """Run a git subcommand rooted at ``repo_root``; the test's OWN oracle."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _init_git_repo(repo_root: Path, *, branch: str) -> None:
    """Create a real, empty git repo at ``repo_root`` on ``branch`` (no commits)."""
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
    """Write ``filename`` under ``repo_root`` and commit it (a real commit)."""
    (repo_root / filename).write_text(content, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_root), "add", "-A"], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_root), "commit", "-m", message], check=True, capture_output=True
    )


# ===========================================================================
# capture_git_identity — pure helper, no live server needed.
# ===========================================================================


class TestCaptureGitIdentity:
    """``capture_git_identity(repo_root)`` reads (git_ref, git_branch) from
    ``repo_root``'s OWN git state — gracefully, never raising, and never
    silently reading the CALLER's cwd instead."""

    def test_returns_none_none_for_a_directory_that_is_not_a_git_repo(
        self, tmp_path: Path
    ) -> None:
        plain_dir = tmp_path / "plain_project"
        plain_dir.mkdir()
        assert capture_git_identity(plain_dir) == (None, None)

    def test_returns_none_none_for_a_nonexistent_directory(self, tmp_path: Path) -> None:
        missing = tmp_path / "does_not_exist_at_all"
        assert capture_git_identity(missing) == (None, None)

    def test_returns_none_none_for_a_regular_file_path(self, tmp_path: Path) -> None:
        # A degenerate/wrong-type input: a FILE, not a directory.
        not_a_dir = tmp_path / "not_a_directory.txt"
        not_a_dir.write_text("hello\n", encoding="utf-8")
        assert capture_git_identity(not_a_dir) == (None, None)

    def test_returns_full_sha_and_branch_name_for_a_repo_on_a_named_branch(
        self, tmp_path: Path
    ) -> None:
        repo = tmp_path / "pricing_service"
        _init_git_repo(repo, branch="release/2026.07")
        _commit_file(
            repo,
            "pricing.py",
            "def compute_margin(cost, price):\n    return price - cost\n",
            "add margin calculator",
        )
        expected_sha = _run_git(repo, "rev-parse", "HEAD")

        ref, branch = capture_git_identity(repo)

        assert ref == expected_sha
        assert branch == "release/2026.07"
        # Format sanity bound: a FULL, un-abbreviated sha (40 lowercase hex
        # chars) — catches an implementation that silently truncates via
        # ``--short`` or similar.
        assert ref is not None
        assert len(ref) == 40
        assert all(char in "0123456789abcdef" for char in ref)

    def test_returns_none_branch_for_a_detached_head_checkout(self, tmp_path: Path) -> None:
        repo = tmp_path / "detached_repo"
        _init_git_repo(repo, branch="main")
        _commit_file(
            repo,
            "service.py",
            "def start():\n    return True\n",
            "initial commit",
        )
        expected_sha = _run_git(repo, "rev-parse", "HEAD")
        subprocess.run(
            ["git", "-C", str(repo), "checkout", expected_sha], check=True, capture_output=True
        )

        ref, branch = capture_git_identity(repo)

        assert ref == expected_sha
        # Design decision (this contract's own choice, not git's): a detached
        # HEAD carries no real branch name, so the mapping is None — never
        # git's own "HEAD" sentinel string leaking through as a fake branch.
        assert branch is None

    def test_uses_repo_roots_own_git_state_not_the_callers_cwd(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # The load-bearing seam test: a naive `subprocess.run(["git", ...])`
        # with no `cwd=`/`-C` reads the CALLER's process cwd, not `repo_root`.
        repo_a = tmp_path / "repo_a_widgets"
        repo_b = tmp_path / "repo_b_inventory"
        _init_git_repo(repo_a, branch="feat/widgets")
        _commit_file(repo_a, "widget.py", "class Widget:\n    pass\n", "add widget")
        _init_git_repo(repo_b, branch="feat/inventory")
        _commit_file(
            repo_b, "inventory.py", "class Inventory:\n    pass\n", "add inventory"
        )
        sha_a = _run_git(repo_a, "rev-parse", "HEAD")
        sha_b = _run_git(repo_b, "rev-parse", "HEAD")
        assert sha_a != sha_b  # guards the premise: two genuinely different repos

        monkeypatch.chdir(repo_b)
        ref, branch = capture_git_identity(repo_a)

        assert ref == sha_a
        assert branch == "feat/widgets"
        assert ref != sha_b  # never silently read the cwd repo instead


# ===========================================================================
# SnapshotStamper — direct contract (live SurrealDB; store + manifest wired
# exactly like production, no Indexer involved).
# ===========================================================================

_ORDER_SERVICE_PATH = "src/order_service.py"
_ORDER_SERVICE_CHUNK_SOURCES: dict[str, str] = {
    "OrderService": 'class OrderService:\n    """Confirms and cancels purchase orders."""\n',
    "OrderService.confirm": (
        'def confirm(self, order):\n    order.state = "purchase"\n    return order\n'
    ),
    "OrderService.cancel": (
        'def cancel(self, order):\n    order.state = "cancel"\n    return order\n'
    ),
}
_ORDER_SERVICE_SOURCE = "".join(_ORDER_SERVICE_CHUNK_SOURCES.values())

_PRICING_PATH = "src/pricing.py"
_PRICING_CHUNK_SOURCES_V1: dict[str, str] = {
    "compute_margin": "def compute_margin(cost, price):\n    return price - cost\n",
}
_PRICING_SOURCE_V1 = "".join(_PRICING_CHUNK_SOURCES_V1.values())

_PRICING_CHUNK_SOURCES_V2: dict[str, str] = {
    **_PRICING_CHUNK_SOURCES_V1,
    "compute_discount": "def compute_discount(price, rate):\n    return price * (1 - rate)\n",
}
_PRICING_SOURCE_V2 = "".join(_PRICING_CHUNK_SOURCES_V2.values())


def _as_utc(value: datetime) -> datetime:
    """Normalise a possibly-naive ``datetime`` to UTC for ordering comparisons."""
    return value if value.tzinfo else value.replace(tzinfo=UTC)


async def _write_chunk_rows(
    store: SurrealStore,
    *,
    tier: str,
    file_path: str,
    chunk_sources: Mapping[str, str],
    dim: int,
) -> None:
    """Write one REAL chunk row per ``(identity, source_text)`` pair for
    ``(tier, file_path)`` — replaces any prior rows under it (the store's own
    replace-fragment semantics). Each source text is distinct, so each chunk's
    ``content_hash`` (``chunk_record`` hashes ``source_text``) is genuinely
    distinguishable — a prerequisite for a meaningful per-chunk fidelity check.
    """
    records_with_vectors = [
        (
            chunk_record(
                tier=tier,
                file_path=file_path,
                identity=identity,
                ident_text=identity,
                source_text=source_text,
            ),
            unit_vector(axis=index % dim, dim=dim),
        )
        for index, (identity, source_text) in enumerate(chunk_sources.items())
    ]
    fragment = store.replace_file_fragment(tier, file_path, records_with_vectors)
    await store.apply([fragment])


async def _upsert_manifest_row(
    manifest: SurrealManifest, *, tier: str, file_path: str, source: str, n_chunks: int
) -> str:
    """Upsert an ``indexed`` manifest row for ``(tier, file_path)``; returns its sha512."""
    sha512 = sha512_hex(source)
    await manifest.upsert(
        tier=tier,
        file_path=file_path,
        sha512=sha512,
        mtime_ns=1_751_000_000_000_000_000,
        size=len(source.encode("utf-8")),
        n_chunks=n_chunks,
        chunk_ids=[f"chunk_{i}" for i in range(n_chunks)],
        state=STATE_INDEXED,
    )
    return sha512


async def _raw_rows(env: SurrealEnv, table: str) -> list[dict[str, Any]]:
    """Every row of ``table``, read on a FRESH admin connection."""
    connection = await connect_admin(env)
    try:
        result = await run(connection, f"SELECT * FROM {table}")
    finally:
        await connection.close()
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


async def _snapshot_rows(env: SurrealEnv) -> list[dict[str, Any]]:
    return await _raw_rows(env, SNAPSHOT_TABLE)


async def _entry_rows_for(env: SurrealEnv, snapshot_id: str) -> list[dict[str, Any]]:
    rows = await _raw_rows(env, SNAPSHOT_ENTRY_TABLE)
    return [row for row in rows if str(row["snapshot"]) == snapshot_id]


@dataclass(frozen=True)
class _StampBench:
    """A real store + manifest + :class:`SnapshotStamper`, on one shared database."""

    store: SurrealStore
    manifest: SurrealManifest
    stamper: Any
    env: SurrealEnv
    project_root: Path


@pytest_asyncio.fixture()
async def stamp_bench(
    surreal_env: SurrealEnv,  # noqa: F811 - imported fixture
    tmp_path: Path,
) -> AsyncIterator[_StampBench]:
    project_root = tmp_path / "project"
    _init_git_repo(project_root, branch="feat/pricing-refactor")
    _commit_file(project_root, "README.md", "# demo project\n", "initial commit")

    store = SurrealStore(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        dim=_DIM,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    manifest = SurrealManifest(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
    )
    await store.ensure_ready()
    await manifest.ensure_ready()

    stamper = SnapshotStamper(
        url=surreal_env.url,
        namespace=surreal_env.namespace,
        database=surreal_env.database,
        user=surreal_env.user,
        password=surreal_env.password,
        store=store,
        manifest=manifest,
        project_root=project_root,
    )
    await stamper.ensure_ready()
    try:
        yield _StampBench(
            store=store, manifest=manifest, stamper=stamper, env=surreal_env,
            project_root=project_root,
        )
    finally:
        await stamper.close()
        await store.close()
        await manifest.close()


class TestSnapshotStamperWritesSnapshotAndEntries:
    """``stamp()`` writes ONE ``snapshot`` row + one ``snapshot_entry`` per
    indexed file, with correct totals, git identity, and chunk-level fidelity
    cross-checked against the REAL chunk table (the seam)."""

    async def test_stamp_writes_one_snapshot_row_with_correct_totals_and_git_identity(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            chunk_sources=_ORDER_SERVICE_CHUNK_SOURCES, dim=_DIM,
        )
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            source=_ORDER_SERVICE_SOURCE, n_chunks=len(_ORDER_SERVICE_CHUNK_SOURCES),
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )

        # Independent oracle: git identity read directly via subprocess, never
        # through `capture_git_identity` (that helper's own correctness is
        # pinned separately in `TestCaptureGitIdentity`).
        expected_ref = _run_git(stamp_bench.project_root, "rev-parse", "HEAD")
        expected_branch = _run_git(stamp_bench.project_root, "rev-parse", "--abbrev-ref", "HEAD")

        snapshot_id = await stamp_bench.stamper.stamp()
        assert snapshot_id
        assert snapshot_id.startswith(f"{SNAPSHOT_TABLE}:")

        rows = await _snapshot_rows(stamp_bench.env)
        assert len(rows) == 1
        row = rows[0]
        assert str(row["id"]) == snapshot_id
        assert row["files_total"] == 2
        expected_chunks_total = len(_ORDER_SERVICE_CHUNK_SOURCES) + len(_PRICING_CHUNK_SOURCES_V1)
        assert row["chunks_total"] == expected_chunks_total
        assert row["git_ref"] == expected_ref
        assert row["git_branch"] == expected_branch
        assert len(row["git_ref"]) == 40  # a full sha, never abbreviated

    async def test_stamp_writes_one_entry_per_indexed_file_matching_the_chunk_table(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            chunk_sources=_ORDER_SERVICE_CHUNK_SOURCES, dim=_DIM,
        )
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        sha_order_service = await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            source=_ORDER_SERVICE_SOURCE, n_chunks=len(_ORDER_SERVICE_CHUNK_SOURCES),
        )
        sha_pricing = await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )

        snapshot_id = await stamp_bench.stamper.stamp()
        entries = await _entry_rows_for(stamp_bench.env, snapshot_id)
        assert len(entries) == 2
        by_path = {entry["file_path"]: entry for entry in entries}
        assert set(by_path) == {_ORDER_SERVICE_PATH, _PRICING_PATH}

        for file_path, chunk_sources, expected_sha in (
            (_ORDER_SERVICE_PATH, _ORDER_SERVICE_CHUNK_SOURCES, sha_order_service),
            (_PRICING_PATH, _PRICING_CHUNK_SOURCES_V1, sha_pricing),
        ):
            entry = by_path[file_path]
            assert entry["tier"] == _TIER
            assert entry["sha512"] == expected_sha

            # Independent, hand-computed oracle (no DB read at all).
            hand_computed_pairs = {
                (identity, sha512_hex(text)) for identity, text in chunk_sources.items()
            }
            # Independent, LIVE oracle: read the REAL chunk table directly (the
            # producer↔consumer seam) rather than trusting the stamper's own
            # internal bookkeeping.
            chunk_rows = await stamp_bench.store.scroll(
                {"tier": _TIER, "file_path": file_path}, limit=100
            )
            live_pairs = {(row["identity"], row["content_hash"]) for row in chunk_rows}
            assert hand_computed_pairs == live_pairs  # guards the fixture itself

            stored_pairs = {
                (item["identity"], item["hash"]) for item in entry["chunk_hashes"]
            }
            assert stored_pairs == hand_computed_pairs
            assert stored_pairs == live_pairs


class TestSnapshotStamperHandlesEmptyManifest:
    """A degenerate driver table: zero indexed files still yields a
    well-formed, zero-total snapshot with zero entries — never a crash."""

    async def test_stamp_with_no_indexed_files_creates_an_empty_snapshot(
        self, stamp_bench: _StampBench
    ) -> None:
        snapshot_id = await stamp_bench.stamper.stamp()

        rows = await _snapshot_rows(stamp_bench.env)
        assert len(rows) == 1
        row = rows[0]
        assert row["files_total"] == 0
        assert row["chunks_total"] == 0
        assert await _entry_rows_for(stamp_bench.env, snapshot_id) == []


class TestSnapshotStamperNonGitProjectRoot:
    """A non-git project root still stamps files/chunks correctly; git_ref /
    git_branch are simply absent (``None``), never a crash or a fabricated
    value."""

    async def test_stamp_omits_git_identity_for_a_non_git_project_root(
        self,
        surreal_env: SurrealEnv,  # noqa: F811 - imported fixture
        tmp_path: Path,
    ) -> None:
        project_root = tmp_path / "tarball_imported_project"
        project_root.mkdir()

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
        try:
            await _write_chunk_rows(
                store, tier=_TIER, file_path=_PRICING_PATH,
                chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
            )
            await _upsert_manifest_row(
                manifest, tier=_TIER, file_path=_PRICING_PATH,
                source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
            )

            snapshot_id = await stamper.stamp()
            rows = await _snapshot_rows(surreal_env)
            row = next(r for r in rows if str(r["id"]) == snapshot_id)

            assert row.get("git_ref") is None
            assert row.get("git_branch") is None
            # Absence of git identity must never suppress the file/chunk stamp.
            assert row["files_total"] == 1
            assert row["chunks_total"] == len(_PRICING_CHUNK_SOURCES_V1)
        finally:
            await stamper.close()
            await store.close()
            await manifest.close()


class TestSnapshotChangeFidelityAcrossTwoSuccessfulStamps:
    """Two successful stamps produce two ordered snapshots, each preserving
    its OWN generation's sha512/chunk_hashes — the load-bearing versioning
    property ``lore_diff`` / ``changed_since`` depend on."""

    async def test_two_stamps_are_ordered_and_each_keeps_its_own_generation(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        sha_v1 = await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )
        snapshot_a = await stamp_bench.stamper.stamp()

        # A tiny, deliberate pause so `created_at` orders measurably later —
        # NOT a retry loop, a single fixed wait between two sequential writes.
        await asyncio.sleep(0.05)

        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V2, dim=_DIM,
        )
        sha_v2 = await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V2, n_chunks=len(_PRICING_CHUNK_SOURCES_V2),
        )
        snapshot_b = await stamp_bench.stamper.stamp()

        assert snapshot_a != snapshot_b
        assert sha_v1 != sha_v2  # guards the premise: the file genuinely changed

        rows = await _snapshot_rows(stamp_bench.env)
        assert len(rows) == 2
        by_id = {str(row["id"]): row for row in rows}
        assert _as_utc(by_id[snapshot_a]["created_at"]) < _as_utc(by_id[snapshot_b]["created_at"])

        entries_a = await _entry_rows_for(stamp_bench.env, snapshot_a)
        entries_b = await _entry_rows_for(stamp_bench.env, snapshot_b)
        assert len(entries_a) == 1
        assert len(entries_b) == 1
        entry_a, entry_b = entries_a[0], entries_b[0]

        assert entry_a["sha512"] == sha_v1
        assert entry_b["sha512"] == sha_v2
        identities_a = {item["identity"] for item in entry_a["chunk_hashes"]}
        identities_b = {item["identity"] for item in entry_b["chunk_hashes"]}
        assert identities_a == set(_PRICING_CHUNK_SOURCES_V1)
        assert identities_b == set(_PRICING_CHUNK_SOURCES_V2)
        # v2 both KEEPS a member and GAINS one — a partial/aliased write would
        # equal neither v1's nor v2's set.
        assert "compute_discount" not in identities_a
        assert "compute_discount" in identities_b


class TestDeleteSnapshotRemovesChildEntriesAtomically:
    """GC seam: deleting a snapshot removes every ``snapshot_entry`` that
    references it — record links do NOT auto-clean on delete (docs-audit
    constraint), so the stamper must clean them up explicitly and scoped."""

    async def test_delete_snapshot_removes_the_row_and_all_its_entries(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            chunk_sources=_ORDER_SERVICE_CHUNK_SOURCES, dim=_DIM,
        )
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            source=_ORDER_SERVICE_SOURCE, n_chunks=len(_ORDER_SERVICE_CHUNK_SOURCES),
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )
        snapshot_id = await stamp_bench.stamper.stamp()
        # Sanity: entries genuinely exist before the delete.
        assert len(await _entry_rows_for(stamp_bench.env, snapshot_id)) == 2

        await stamp_bench.stamper.delete_snapshot(snapshot_id)

        assert await _snapshot_rows(stamp_bench.env) == []
        assert await _entry_rows_for(stamp_bench.env, snapshot_id) == []

    async def test_delete_snapshot_is_scoped_and_leaves_sibling_snapshot_intact(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )
        snapshot_a = await stamp_bench.stamper.stamp()

        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V2, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V2, n_chunks=len(_PRICING_CHUNK_SOURCES_V2),
        )
        snapshot_b = await stamp_bench.stamper.stamp()

        await stamp_bench.stamper.delete_snapshot(snapshot_a)

        remaining = await _snapshot_rows(stamp_bench.env)
        assert len(remaining) == 1
        assert str(remaining[0]["id"]) == snapshot_b
        # Sibling B's entries are untouched — a SCOPED delete, not a table wipe.
        assert len(await _entry_rows_for(stamp_bench.env, snapshot_b)) == 1
        assert await _entry_rows_for(stamp_bench.env, snapshot_a) == []

    async def test_delete_snapshot_is_idempotent_for_an_unknown_id(
        self, stamp_bench: _StampBench
    ) -> None:
        bogus_id = f"{SNAPSHOT_TABLE}:definitely_never_created"
        # Must not raise — a GC sweep may race a concurrent delete of the same id.
        await stamp_bench.stamper.delete_snapshot(bogus_id)
        assert await _snapshot_rows(stamp_bench.env) == []


class TestSnapshotStamperMidLifeConnectionRecovery:
    """A mid-life connection drop must self-heal — degradation → recovery
    (CLAUDE.md). Mirrors the IDENTICAL contract already pinned for
    ``SurrealStore`` / ``SurrealManifest`` / ``SurrealCodeGraph``
    (``test_surreal_manifest.py::TestMidLifeConnectionRecovery``): the socket
    dies, the NEXT call transparently reconnects rather than wedging forever.
    """

    async def test_stamp_recovers_from_a_mid_life_socket_drop(
        self, stamp_bench: _StampBench
    ) -> None:
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_PRICING_PATH,
            chunk_sources=_PRICING_CHUNK_SOURCES_V1, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_PRICING_PATH,
            source=_PRICING_SOURCE_V1, n_chunks=len(_PRICING_CHUNK_SOURCES_V1),
        )

        first_id = await stamp_bench.stamper.stamp()
        assert first_id  # baseline: connection healthy, first stamp succeeds

        # Degradation: kill the stamper's OWN underlying socket.
        connection = stamp_bench.stamper._connection
        assert connection is not None, "expected an established connection to kill"
        await connection.close()

        # Recovery: heal within a bounded number of calls (never wedge).
        second_id = await call_until_recovered(
            stamp_bench.stamper.stamp, _HEALABLE_ERRORS, label="snapshot_stamper"
        )
        assert second_id and second_id != first_id
        assert len(await _snapshot_rows(stamp_bench.env)) == 2  # both stamps landed


# ===========================================================================
# Fix #2 (audit hardening): stamp() composes ONE atomic transaction.
# ===========================================================================


class TestStampIsOneAtomicTransaction:
    """``stamp()`` must compose the snapshot row + every entry into ONE
    ``BEGIN … COMMIT`` (P5-C4 hardening #3): a mid-stamp connection drop or a
    later statement's rejection must never leave an orphan snapshot row with
    only SOME of its entries persisted."""

    async def test_poison_state_is_genuinely_out_of_domain(self) -> None:
        # Guards the poison itself, independent of any implementation here.
        assert _INVALID_FILE_STATE not in FILE_STATES

    async def test_a_rejected_statement_rolls_back_the_whole_stamp(
        self, stamp_bench: _StampBench, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # A real, would-otherwise-succeed indexed file — proving the poison
        # rolls back genuinely GOOD work too, not merely itself.
        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            chunk_sources=_ORDER_SERVICE_CHUNK_SOURCES, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            source=_ORDER_SERVICE_SOURCE, n_chunks=len(_ORDER_SERVICE_CHUNK_SOURCES),
        )

        # An UNRELATED poison statement (a distinct ``file`` record, its own
        # id so it can never id-clash with a manifest row) spliced into the
        # SAME composed transaction ``stamp()`` builds — mirrors
        # ``test_surreal_apply.py``'s ``_invalid_state_fragment``.
        poison_path = "demo/__poison_snapshot_stamp__.py"
        poison_fragment = TxnFragment(
            statements=[
                f"CREATE type::record('{FILE_TABLE}', $px_id) SET "
                "sha512 = $px_sha, mtime_ns = $px_mtime, size = $px_size, "
                "n_chunks = $px_n, chunk_ids = $px_ids, state = $px_state, "
                "updated_at = $px_when"
            ],
            params={
                "px_id": [_TIER, poison_path],
                "px_sha": "0" * 128,
                "px_mtime": 0,
                "px_size": 0,
                "px_n": 0,
                "px_ids": [],
                "px_state": _INVALID_FILE_STATE,
                "px_when": datetime.now(UTC),
            },
        )

        def _compose_with_poison(*fragments: TxnFragment) -> tuple[str, dict[str, Any]]:
            return compose(*fragments, poison_fragment)

        monkeypatch.setattr("loremaster.index.snapshots.compose", _compose_with_poison)

        with pytest.raises(SurrealStoreError):
            await stamp_bench.stamper.stamp()

        # NOTHING landed — not the snapshot row, not its entry. Under the OLD
        # N+1-CREATE implementation the snapshot row (and this entry) would
        # have already committed BEFORE the poison ever ran.
        assert await _snapshot_rows(stamp_bench.env) == []
        assert await _raw_rows(stamp_bench.env, SNAPSHOT_ENTRY_TABLE) == []


# ===========================================================================
# Nit #4: a file whose chunk scroll hits the cap warns (possible truncation).
# ===========================================================================


class TestSnapshotStamperWarnsOnPossibleChunkTruncation:
    """A file whose chunk_hashes list exactly equals the scroll cap is a
    possible-truncation signal — the WARNING names the file so an operator
    can investigate, rather than silently trusting a maybe-partial list."""

    async def test_stamp_warns_when_a_files_chunk_scroll_hits_the_lowered_cap(
        self,
        stamp_bench: _StampBench,
        monkeypatch: pytest.MonkeyPatch,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        # Lower the cap below the fixture's 3 real chunk rows so the scroll
        # genuinely hits it exactly.
        monkeypatch.setattr("loremaster.index.snapshots._MAX_CHUNKS_PER_FILE", 2)

        await _write_chunk_rows(
            stamp_bench.store, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            chunk_sources=_ORDER_SERVICE_CHUNK_SOURCES, dim=_DIM,
        )
        await _upsert_manifest_row(
            stamp_bench.manifest, tier=_TIER, file_path=_ORDER_SERVICE_PATH,
            source=_ORDER_SERVICE_SOURCE, n_chunks=len(_ORDER_SERVICE_CHUNK_SOURCES),
        )

        with caplog.at_level(logging.WARNING, logger="loremaster.index.snapshots"):
            await stamp_bench.stamper.stamp()

        events = [
            record
            for record in caplog.records
            if record.message == "snapshot.chunk_scroll_truncated"
        ]
        assert len(events) == 1
        assert events[0].levelno == logging.WARNING
        assert events[0].file_path == _ORDER_SERVICE_PATH  # type: ignore[attr-defined]
