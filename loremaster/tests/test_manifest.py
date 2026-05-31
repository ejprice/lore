"""Contract tests for ``loremaster.index.manifest`` under the C1/D10 deltas.

The SQLite manifest is the *authority* on indexing state — only it can detect a
partial-embed failure and make a per-file update transactional. The amendment
adds:

* **C1 — composite primary key ``(tier, file_path)``.** A module-relative path
  is not unique across tiers, so two tiers' rows for one path must coexist.
* **D10 — WAL mode**, ``check_same_thread=False``. WAL lets N concurrent readers
  (freshness + graph lookups) see a consistent snapshot without blocking the
  single writer.

REAL DB: every test uses a real temp-FILE database (via ``tmp_path``), NOT
``:memory:`` — ``:memory:`` cannot exercise WAL across connections, so the
concurrent-reader test would be a no-op there.

Pinned invariants:

* CRUD round-trips keyed by ``(tier, file_path)``, including JSON ``chunk_ids``.
* Same path under two tiers keeps BOTH rows (the C1 coexistence guarantee).
* The mtime+size **fast-path** is tier-scoped.
* ``set_state`` / ``delete`` are tier-scoped.
* ``replace`` is one transaction: a mid-tx failure rolls back, leaving the
  PRIOR row intact (no orphan, no gap).
* WAL is actually enabled, and a reader on a second connection sees a consistent
  snapshot while a writer holds an open (uncommitted) transaction.
* ``meta_get`` / ``meta_set`` round-trips (e.g. a per-tier version stamp).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest
from loremaster.index.manifest import Manifest

# Representative file-row values reused across tests.
_PATH = "src/pkg/mod.py"
_TIER = "custom"
_OTHER_TIER = "community"
_SHA = "a" * 128  # a plausible 128-hex-char sha512 digest
_MTIME = 1_700_000_000_000_000_000
_SIZE = 4096
_CHUNK_IDS = [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
]


@pytest.fixture()
def manifest(tmp_path: Path) -> Manifest:
    """A fresh real temp-FILE manifest in WAL mode with its schema initialized."""
    return Manifest(str(tmp_path / "lore.db"))


def _upsert_indexed(manifest: Manifest, **overrides: object) -> None:
    """Insert a representative file row in the ``indexed`` state."""
    params: dict[str, object] = {
        "tier": _TIER,
        "file_path": _PATH,
        "sha512": _SHA,
        "mtime_ns": _MTIME,
        "size": _SIZE,
        "n_chunks": len(_CHUNK_IDS),
        "chunk_ids": _CHUNK_IDS,
        "state": "indexed",
    }
    params.update(overrides)
    manifest.upsert(**params)  # type: ignore[arg-type]


class TestCrud:
    """Basic create/read/delete behaviour, keyed by (tier, file_path)."""

    def test_get_missing_returns_none(self, manifest: Manifest) -> None:
        assert manifest.get(_TIER, "does/not/exist.py") is None

    def test_upsert_then_get_roundtrips(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.tier == _TIER
        assert row.file_path == _PATH
        assert row.sha512 == _SHA
        assert row.mtime_ns == _MTIME
        assert row.size == _SIZE
        assert row.n_chunks == len(_CHUNK_IDS)
        assert row.chunk_ids == _CHUNK_IDS
        assert row.state == "indexed"
        assert row.updated_at

    def test_upsert_is_idempotent_on_composite_key(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        _upsert_indexed(manifest, sha512="b" * 128, n_chunks=1, chunk_ids=["x"])
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.sha512 == "b" * 128
        assert row.n_chunks == 1
        assert row.chunk_ids == ["x"]
        # No duplicate row was created for this (tier, path).
        assert [(item.tier, item.file_path) for item in manifest.all_files()] == [(_TIER, _PATH)]

    def test_chunk_ids_persist_as_json(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        raw = manifest.connection.execute(
            "SELECT chunk_ids FROM files WHERE tier = ? AND file_path = ?", (_TIER, _PATH)
        ).fetchone()[0]
        assert json.loads(raw) == _CHUNK_IDS

    def test_delete_removes_only_the_tier_row(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest, tier=_TIER)
        _upsert_indexed(manifest, tier=_OTHER_TIER)
        manifest.delete(_TIER, _PATH)
        assert manifest.get(_TIER, _PATH) is None
        # The other tier's row for the same path survives.
        assert manifest.get(_OTHER_TIER, _PATH) is not None

    def test_delete_missing_is_a_noop(self, manifest: Manifest) -> None:
        manifest.delete(_TIER, "nope.py")  # must not raise

    def test_all_files_lists_every_row(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest, file_path="a.py")
        _upsert_indexed(manifest, file_path="b.py")
        paths = sorted(item.file_path for item in manifest.all_files())
        assert paths == ["a.py", "b.py"]

    def test_all_files_empty_initially(self, manifest: Manifest) -> None:
        assert manifest.all_files() == []


class TestTierCoexistence:
    """C1: two tiers' rows for ONE path must coexist (composite PK)."""

    def test_same_path_two_tiers_keeps_both_rows(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest, tier=_TIER, sha512="a" * 128)
        _upsert_indexed(manifest, tier=_OTHER_TIER, sha512="c" * 128)

        row_custom = manifest.get(_TIER, _PATH)
        row_community = manifest.get(_OTHER_TIER, _PATH)
        assert row_custom is not None and row_community is not None
        # Distinct rows with their own content hashes — neither overwrote the
        # other despite sharing a file_path.
        assert row_custom.sha512 == "a" * 128
        assert row_community.sha512 == "c" * 128
        # Two physical rows for the path.
        count = manifest.connection.execute(
            "SELECT COUNT(*) FROM files WHERE file_path = ?", (_PATH,)
        ).fetchone()[0]
        assert count == 2

    def test_files_for_tier_filters_by_tier(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest, tier=_TIER, file_path="a.py")
        _upsert_indexed(manifest, tier=_TIER, file_path="b.py")
        _upsert_indexed(manifest, tier=_OTHER_TIER, file_path="a.py")
        custom_paths = sorted(item.file_path for item in manifest.files_for_tier(_TIER))
        community_paths = sorted(item.file_path for item in manifest.files_for_tier(_OTHER_TIER))
        assert custom_paths == ["a.py", "b.py"]
        assert community_paths == ["a.py"]


class TestSetState:
    """The tier-scoped state-transition helper."""

    def test_set_state_updates_only_state(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        manifest.set_state(_TIER, _PATH, "dirty")
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.state == "dirty"
        assert row.sha512 == _SHA
        assert row.n_chunks == len(_CHUNK_IDS)

    @pytest.mark.parametrize("state", ["indexed", "dirty", "embedding", "failed"])
    def test_all_documented_states_are_accepted(self, manifest: Manifest, state: str) -> None:
        _upsert_indexed(manifest)
        manifest.set_state(_TIER, _PATH, state)
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.state == state

    def test_set_state_only_touches_the_named_tier(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest, tier=_TIER)
        _upsert_indexed(manifest, tier=_OTHER_TIER)
        manifest.set_state(_TIER, _PATH, "failed")
        assert manifest.get(_TIER, _PATH).state == "failed"  # type: ignore[union-attr]
        # The other tier's row is untouched.
        assert manifest.get(_OTHER_TIER, _PATH).state == "indexed"  # type: ignore[union-attr]

    def test_set_state_on_missing_row_is_a_noop(self, manifest: Manifest) -> None:
        manifest.set_state(_TIER, "ghost.py", "failed")  # must not raise
        assert manifest.get(_TIER, "ghost.py") is None


class TestNeedsReindex:
    """The tier-scoped mtime+size fast-path."""

    def test_unchanged_indexed_file_does_not_need_reindex(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        assert manifest.needs_reindex(_TIER, _PATH, _MTIME, _SIZE) is False

    def test_absent_file_needs_reindex(self, manifest: Manifest) -> None:
        assert manifest.needs_reindex(_TIER, "never/seen.py", _MTIME, _SIZE) is True

    def test_same_path_other_tier_still_needs_reindex(self, manifest: Manifest) -> None:
        # An indexed row under ``custom`` must NOT make ``community``'s copy of
        # the same path look already-indexed — the fast-path is tier-scoped.
        _upsert_indexed(manifest, tier=_TIER)
        assert manifest.needs_reindex(_OTHER_TIER, _PATH, _MTIME, _SIZE) is True

    def test_changed_mtime_needs_reindex(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        assert manifest.needs_reindex(_TIER, _PATH, _MTIME + 1, _SIZE) is True

    def test_changed_size_needs_reindex(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        assert manifest.needs_reindex(_TIER, _PATH, _MTIME, _SIZE + 1) is True

    @pytest.mark.parametrize("state", ["dirty", "embedding", "failed"])
    def test_non_indexed_state_needs_reindex_even_when_unchanged(
        self, manifest: Manifest, state: str
    ) -> None:
        _upsert_indexed(manifest, state=state)
        assert manifest.needs_reindex(_TIER, _PATH, _MTIME, _SIZE) is True


class TestReplace:
    """The transactional, tier-scoped row-swap that leaves no orphan rows."""

    def test_replace_swaps_the_row_atomically(self, manifest: Manifest) -> None:
        _upsert_indexed(manifest)
        manifest.replace(
            tier=_TIER,
            file_path=_PATH,
            sha512="c" * 128,
            mtime_ns=_MTIME + 10,
            size=_SIZE + 10,
            n_chunks=1,
            chunk_ids=["only-one"],
            state="indexed",
        )
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.sha512 == "c" * 128
        assert row.mtime_ns == _MTIME + 10
        assert row.chunk_ids == ["only-one"]
        count = manifest.connection.execute(
            "SELECT COUNT(*) FROM files WHERE tier = ? AND file_path = ?", (_TIER, _PATH)
        ).fetchone()[0]
        assert count == 1

    def test_replace_inserts_when_absent(self, manifest: Manifest) -> None:
        manifest.replace(
            tier=_TIER,
            file_path="fresh.py",
            sha512=_SHA,
            mtime_ns=_MTIME,
            size=_SIZE,
            n_chunks=2,
            chunk_ids=_CHUNK_IDS,
            state="indexed",
        )
        row = manifest.get(_TIER, "fresh.py")
        assert row is not None
        assert row.chunk_ids == _CHUNK_IDS

    def test_replace_does_not_touch_other_tier_same_path(self, manifest: Manifest) -> None:
        # Replacing the custom tier's row for a path must leave the community
        # tier's row for the SAME path intact (composite-PK scoping).
        _upsert_indexed(manifest, tier=_OTHER_TIER, chunk_ids=["keep"])
        manifest.replace(
            tier=_TIER,
            file_path=_PATH,
            sha512=_SHA,
            mtime_ns=_MTIME,
            size=_SIZE,
            n_chunks=1,
            chunk_ids=["z"],
            state="indexed",
        )
        kept = manifest.get(_OTHER_TIER, _PATH)
        assert kept is not None
        assert kept.chunk_ids == ["keep"]

    def test_replace_rolls_back_on_failure_leaving_old_row_intact(self, manifest: Manifest) -> None:
        # A replace must be one transaction: if the insert half fails, the delete
        # half must roll back so the prior row survives rather than vanishing.
        _upsert_indexed(manifest)
        with pytest.raises(Exception):
            manifest.replace(
                tier=_TIER,
                file_path=_PATH,
                sha512=_SHA,
                mtime_ns=_MTIME,
                size=_SIZE,
                n_chunks=1,
                chunk_ids=[object()],  # type: ignore[list-item]  # not JSON-serializable
                state="indexed",
            )
        row = manifest.get(_TIER, _PATH)
        assert row is not None
        assert row.sha512 == _SHA
        assert row.chunk_ids == _CHUNK_IDS


class TestWalMode:
    """D10: WAL is enabled and supports a consistent concurrent-reader snapshot."""

    def test_journal_mode_is_wal(self, manifest: Manifest) -> None:
        mode = manifest.connection.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_reader_sees_consistent_snapshot_during_open_write_tx(
        self, tmp_path: Path
    ) -> None:
        # REAL concurrency (the D10 contract): the writer opens a transaction and
        # INSERTs a row but has NOT committed; a separate reader connection (a
        # freshness/graph lookup in an MCP handler) reads concurrently and must
        # see the prior, consistent snapshot — never blocked, never the
        # half-applied write. This pins the cross-connection isolation behaviour
        # the concurrent-reader design relies on; ``test_journal_mode_is_wal``
        # separately pins that WAL itself is enabled (the mechanism that keeps
        # readers from ever being blocked by the single writer at commit time).
        db_path = tmp_path / "lore.db"
        writer = Manifest(str(db_path))
        writer.upsert(
            tier=_TIER,
            file_path=_PATH,
            sha512=_SHA,
            mtime_ns=_MTIME,
            size=_SIZE,
            n_chunks=len(_CHUNK_IDS),
            chunk_ids=_CHUNK_IDS,
            state="indexed",
        )

        # A second, independent reader connection on the same file (WAL allows
        # concurrent readers across connections — impossible with :memory:). A
        # short busy_timeout makes the discriminator sharp: under a rollback
        # journal the reader would hit "database is locked" while the writer
        # holds the lock; under WAL it proceeds immediately on its snapshot.
        reader = sqlite3.connect(str(db_path), timeout=0.5)
        reader.row_factory = sqlite3.Row
        reader.execute("PRAGMA busy_timeout = 200")

        # Begin an UNcommitted write of a brand-new path on the writer and force
        # the write lock to be taken (BEGIN IMMEDIATE + the INSERT).
        writer.connection.execute("BEGIN IMMEDIATE")
        writer.connection.execute(
            """
            INSERT INTO files
                (tier, file_path, sha512, mtime_ns, size, n_chunks, chunk_ids, state, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (_TIER, "uncommitted.py", _SHA, _MTIME, _SIZE, 0, "[]", "embedding", "now"),
        )

        try:
            # The reader must NOT block (no OperationalError), must NOT see the
            # uncommitted row, and MUST see the already-committed one — a
            # consistent snapshot served concurrently with the open writer.
            uncommitted = reader.execute(
                "SELECT COUNT(*) FROM files WHERE file_path = ?", ("uncommitted.py",)
            ).fetchone()[0]
            committed = reader.execute(
                "SELECT COUNT(*) FROM files WHERE file_path = ?", (_PATH,)
            ).fetchone()[0]
            assert uncommitted == 0
            assert committed == 1
        finally:
            writer.connection.rollback()
            reader.close()
            writer.close()


class TestMeta:
    """The auxiliary key/value meta table (e.g. per-tier version stamps)."""

    def test_meta_get_missing_returns_none(self, manifest: Manifest) -> None:
        assert manifest.meta_get("tier_version:community") is None

    def test_meta_set_then_get(self, manifest: Manifest) -> None:
        manifest.meta_set("tier_version:community", "15.0.20260420")
        assert manifest.meta_get("tier_version:community") == "15.0.20260420"

    def test_meta_set_overwrites(self, manifest: Manifest) -> None:
        manifest.meta_set("tier_version:community", "15.0.20260420")
        manifest.meta_set("tier_version:community", "15.0.20260501")
        assert manifest.meta_get("tier_version:community") == "15.0.20260501"


class TestPersistence:
    """A file-backed manifest persists across connections (rebuildable authority)."""

    def test_data_survives_reopen(self, tmp_path: Path) -> None:
        db_path = tmp_path / "lore.db"
        first = Manifest(str(db_path))
        first.upsert(
            tier=_TIER,
            file_path=_PATH,
            sha512=_SHA,
            mtime_ns=_MTIME,
            size=_SIZE,
            n_chunks=len(_CHUNK_IDS),
            chunk_ids=_CHUNK_IDS,
            state="indexed",
        )
        first.close()

        second = Manifest(str(db_path))
        row = second.get(_TIER, _PATH)
        assert row is not None
        assert row.chunk_ids == _CHUNK_IDS
        second.close()
