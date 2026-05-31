"""SQLite manifest — the authority on per-file, per-tier indexing state.

The manifest, not Qdrant, is the source of truth for what has been indexed and
in what state. Only a relational ledger can express *partial-embed failure*
(``state`` + expected ``n_chunks``) and make a per-file update transactional —
the two things a vector store or a merkle root cannot do. Qdrant payloads carry
``tier``/``content_hash``/``file_path``/``mtime_ns`` redundantly so the manifest
is rebuildable by scroll if it is ever lost.

Amendment deltas:

* **C1 — composite primary key ``(tier, file_path)``.** A module-relative path
  is not globally unique across tiers (a ``custom`` override and the
  ``community`` original can share a path), so the PK is ``(tier, file_path)``
  and two tiers' rows for one path coexist. Every accessor is tier-scoped.
* **D10 — WAL mode** + ``check_same_thread=False``. WAL lets N concurrent
  readers (freshness + graph lookups in MCP handlers) see a consistent snapshot
  without ever blocking the single writer (the indexer/watcher).

The schema is two tables:

* ``files(tier, file_path, sha512, mtime_ns, size, n_chunks, chunk_ids, state,
  updated_at, PRIMARY KEY (tier, file_path))`` — one row per (tier, file).
  ``chunk_ids`` is a JSON-encoded list of point ids. ``state`` is one of
  ``indexed | dirty | embedding | failed``.
* ``meta(k PK, v)`` — auxiliary key/value store (e.g. per-tier version stamps).
"""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from pydantic import BaseModel, ConfigDict

# The lifecycle states a file row may occupy.
STATE_INDEXED = "indexed"
STATE_DIRTY = "dirty"
STATE_EMBEDDING = "embedding"
STATE_FAILED = "failed"

# Schema DDL. Executed idempotently on every connection open so a fresh db and a
# reopened file-backed db both arrive at the same schema. The PK is the
# (tier, file_path) pair (C1) so the same path can live under multiple tiers.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS files (
    tier       TEXT NOT NULL,
    file_path  TEXT NOT NULL,
    sha512     TEXT NOT NULL,
    mtime_ns   INTEGER NOT NULL,
    size       INTEGER NOT NULL,
    n_chunks   INTEGER NOT NULL,
    chunk_ids  TEXT NOT NULL,
    state      TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (tier, file_path)
);
CREATE TABLE IF NOT EXISTS meta (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL
);
"""


class FileRow(BaseModel):
    """A single decoded row from the ``files`` table.

    Attributes:
        tier: The source tier/root this row belongs to (half the composite PK).
        file_path: The indexed file's path (the other half of the PK).
        sha512: The file's SHA-512 hex digest at index time.
        mtime_ns: The file's modification time, in nanoseconds.
        size: The file's size, in bytes.
        n_chunks: The number of chunks the file produced.
        chunk_ids: The point ids of those chunks (decoded from JSON).
        state: The lifecycle state (``indexed`` / ``dirty`` / ``embedding`` /
            ``failed``).
        updated_at: ISO-8601 timestamp of the last write to this row.
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str
    sha512: str
    mtime_ns: int
    size: int
    n_chunks: int
    chunk_ids: list[str]
    state: str
    updated_at: str


class Manifest:
    """A SQLite-backed ledger of per-(tier, file) indexing state, in WAL mode.

    The database path is configurable; pass a real file path. The schema is
    created on construction. WAL is enabled so concurrent readers never block
    the single writer (D10).
    """

    def __init__(self, db_path: str) -> None:
        """Open (or create) the manifest database, enable WAL, ensure schema.

        Args:
            db_path: The SQLite database path (a real file — WAL across
                connections is meaningless for ``:memory:``).
        """
        # ``check_same_thread=False`` so the single-writer manifest can be driven
        # from the asyncio loop thread and a watcher thread under the caller's
        # own ``asyncio.Lock`` (the loremaster concurrency contract).
        self._connection = sqlite3.connect(db_path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        # WAL (D10): readers see a consistent committed snapshot and never block
        # the single writer. ``PRAGMA journal_mode`` is connection-persistent for
        # a file-backed db, set once at open.
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying SQLite connection (for diagnostics and tests)."""
        return self._connection

    def close(self) -> None:
        """Close the underlying database connection."""
        self._connection.close()

    @staticmethod
    def _row_to_model(row: sqlite3.Row) -> FileRow:
        """Decode a raw ``files`` row (with JSON ``chunk_ids``) into a model."""
        return FileRow(
            tier=row["tier"],
            file_path=row["file_path"],
            sha512=row["sha512"],
            mtime_ns=row["mtime_ns"],
            size=row["size"],
            n_chunks=row["n_chunks"],
            chunk_ids=json.loads(row["chunk_ids"]),
            state=row["state"],
            updated_at=row["updated_at"],
        )

    @staticmethod
    def _now() -> str:
        """Return the current UTC time as an ISO-8601 string."""
        return datetime.now(UTC).isoformat()

    def get(self, tier: str, file_path: str) -> FileRow | None:
        """Return the row for ``(tier, file_path)``, or ``None`` if absent.

        Args:
            tier: The tier the file belongs to.
            file_path: The path to look up within the tier.

        Returns:
            The decoded :class:`FileRow`, or ``None``.
        """
        row = self._connection.execute(
            "SELECT * FROM files WHERE tier = ? AND file_path = ?", (tier, file_path)
        ).fetchone()
        return self._row_to_model(row) if row is not None else None

    def all_files(self) -> list[FileRow]:
        """Return every file row, ordered by ``(tier, file_path)``."""
        rows = self._connection.execute(
            "SELECT * FROM files ORDER BY tier, file_path"
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def files_for_tier(self, tier: str) -> list[FileRow]:
        """Return every file row for ``tier``, ordered by path.

        The per-tier listing the reconcile pass walks and that a per-tier rebuild
        (``delete_by_tier`` + re-add) iterates.

        Args:
            tier: The tier to list.

        Returns:
            The decoded rows for that tier.
        """
        rows = self._connection.execute(
            "SELECT * FROM files WHERE tier = ? ORDER BY file_path", (tier,)
        ).fetchall()
        return [self._row_to_model(row) for row in rows]

    def upsert(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        """Insert or replace the row for ``(tier, file_path)``.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path within the tier.
            sha512: The file's SHA-512 hex digest.
            mtime_ns: The file's modification time, in nanoseconds.
            size: The file's size, in bytes.
            n_chunks: The number of chunks produced.
            chunk_ids: The point ids of those chunks (JSON-encoded on write).
            state: The lifecycle state.
        """
        encoded = json.dumps(chunk_ids)
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO files
                    (tier, file_path, sha512, mtime_ns, size, n_chunks, chunk_ids, state, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(tier, file_path) DO UPDATE SET
                    sha512     = excluded.sha512,
                    mtime_ns   = excluded.mtime_ns,
                    size       = excluded.size,
                    n_chunks   = excluded.n_chunks,
                    chunk_ids  = excluded.chunk_ids,
                    state      = excluded.state,
                    updated_at = excluded.updated_at
                """,
                (tier, file_path, sha512, mtime_ns, size, n_chunks, encoded, state, self._now()),
            )

    def set_state(self, tier: str, file_path: str, state: str) -> None:
        """Transition ``(tier, file_path)`` to ``state`` (no-op if row absent).

        Args:
            tier: The tier the file belongs to.
            file_path: The file path to transition.
            state: The new lifecycle state.
        """
        with self._connection:
            self._connection.execute(
                "UPDATE files SET state = ?, updated_at = ? WHERE tier = ? AND file_path = ?",
                (state, self._now(), tier, file_path),
            )

    def delete(self, tier: str, file_path: str) -> None:
        """Delete the row for ``(tier, file_path)`` (no-op if absent).

        Tier-scoped: the same path's rows under *other* tiers are untouched.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path to delete within the tier.
        """
        with self._connection:
            self._connection.execute(
                "DELETE FROM files WHERE tier = ? AND file_path = ?", (tier, file_path)
            )

    def needs_reindex(self, tier: str, file_path: str, mtime_ns: int, size: int) -> bool:
        """Decide whether ``(tier, file_path)`` must be re-indexed.

        Fast-path: a file already in the ``indexed`` state whose ``mtime_ns`` and
        ``size`` are both unchanged needs no work — return ``False``. Anything
        else — an absent row (including the same path under a *different* tier),
        a changed mtime or size, or any non-``indexed`` state — must be
        re-attempted, so return ``True``.

        Args:
            tier: The tier the file belongs to.
            file_path: The file to check within the tier.
            mtime_ns: The file's current modification time, in nanoseconds.
            size: The file's current size, in bytes.

        Returns:
            ``True`` if the file must be re-indexed, ``False`` otherwise.
        """
        row = self.get(tier, file_path)
        if row is None:
            return True
        if row.state != STATE_INDEXED:
            return True
        return row.mtime_ns != mtime_ns or row.size != size

    def replace(
        self,
        *,
        tier: str,
        file_path: str,
        sha512: str,
        mtime_ns: int,
        size: int,
        n_chunks: int,
        chunk_ids: list[str],
        state: str,
    ) -> None:
        """Atomically replace the row for ``(tier, file_path)`` in one transaction.

        The old row is deleted and the new row inserted inside one transaction,
        so a concurrent reader never sees a half-applied update and a failure
        mid-swap (e.g. a non-serializable ``chunk_ids``) rolls the whole thing
        back, leaving the prior row intact rather than an orphan or a gap. The
        delete is tier-scoped, so another tier's copy of the same path survives.

        Args:
            tier: The tier the file belongs to.
            file_path: The file path being replaced within the tier.
            sha512: The new SHA-512 hex digest.
            mtime_ns: The new modification time, in nanoseconds.
            size: The new size, in bytes.
            n_chunks: The new chunk count.
            chunk_ids: The new point ids (JSON-encoded inside the transaction so
                a serialization failure aborts the swap).
            state: The new lifecycle state.
        """
        # Encode *inside* the transaction so a non-serializable chunk_ids raises
        # after BEGIN, triggering rollback of the DELETE half — the old row
        # survives. ``with self._connection`` commits on success, rolls back on
        # any exception escaping the block.
        with self._connection:
            self._connection.execute(
                "DELETE FROM files WHERE tier = ? AND file_path = ?", (tier, file_path)
            )
            encoded = json.dumps(chunk_ids)
            self._connection.execute(
                """
                INSERT INTO files
                    (tier, file_path, sha512, mtime_ns, size, n_chunks, chunk_ids, state, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (tier, file_path, sha512, mtime_ns, size, n_chunks, encoded, state, self._now()),
            )

    def meta_get(self, key: str) -> str | None:
        """Return the meta value for ``key``, or ``None`` if absent.

        Args:
            key: The meta key to read (e.g. ``"tier_version:community"``).

        Returns:
            The stored value, or ``None``.
        """
        row = self._connection.execute("SELECT v FROM meta WHERE k = ?", (key,)).fetchone()
        return row["v"] if row is not None else None

    def meta_set(self, key: str, value: str) -> None:
        """Insert or overwrite the meta value for ``key``.

        Args:
            key: The meta key to write (e.g. a per-tier version stamp).
            value: The value to store.
        """
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO meta (k, v) VALUES (?, ?)
                ON CONFLICT(k) DO UPDATE SET v = excluded.v
                """,
                (key, value),
            )
