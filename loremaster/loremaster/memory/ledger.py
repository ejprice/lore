"""Durable SQLite write-through ledger for project memories (FP-06).

The ``lore_<slug>_memory`` Qdrant collection holds USER-AUTHORED project
memories, and today there is no second copy: a Qdrant wipe destroys every saved
memory forever (unlike code vectors, a memory cannot be re-derived from source).
This ledger is the durable source of truth — every ``save_memory`` write-through
persists the memory here on the state volume BEFORE the volatile Qdrant upsert,
so a later restore can re-embed it.

The ledger is keyed on the deterministic ``uuid5`` memory id (the same id the
:class:`~loremaster.memory.store.MemoryStore` mints), so :meth:`record` is an
idempotent upsert and a restore re-mints the SAME id — overwriting in place
rather than multiplying points.

Resilient-open posture (mirrors the manifest / resilient-db slice): construction
must NOT crash on a missing parent dir or a corrupt file. The durable copy
degrades to empty rather than taking the process down.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any

from loremaster.index.sqlite_resilient import open_resilient_sqlite

# Schema DDL. Executed idempotently on every connection open so a fresh db and a
# reopened file-backed db both arrive at the same schema. The PK is the
# deterministic ``memory_id`` so :meth:`record` upserts (ON CONFLICT) rather than
# appending a duplicate row — mirroring the Qdrant deterministic-id dedup.
# ``metadata`` is stored as JSON text (a SQLite cell is scalar; the caller's
# metadata is a nested dict, so it round-trips through ``json``).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS memories (
    memory_id  TEXT PRIMARY KEY,
    text       TEXT NOT NULL,
    metadata   TEXT NOT NULL,
    refs_stamp TEXT NOT NULL
);
"""

# Column names, referenced once each in the upsert / read so a rename is a single
# edit and never a hand-copied literal drifting between statements.
_COLUMN_MEMORY_ID = "memory_id"
_COLUMN_TEXT = "text"
_COLUMN_METADATA = "metadata"
_COLUMN_REFS_STAMP = "refs_stamp"


@dataclass(frozen=True)
class MemoryRecord:
    """A single durable memory row read back from the ledger.

    The restore path re-embeds these verbatim, re-minting the deterministic
    ``uuid5`` id from ``text`` + ``refs_stamp`` so the rebuild overwrites in
    place rather than duplicating points.

    Attributes:
        memory_id: The deterministic ``uuid5`` point id this memory is keyed on
            (the natural key — :meth:`MemoryLedger.record` upserts on it).
        text: The memory's note text — the recallable content the restore
            re-embeds document-side.
        metadata: The caller-supplied metadata stored alongside the note.
        refs_stamp: The order-insensitive stamp of the memory's versioned refs
            folded into its deterministic id, so a restore re-mints the SAME id.
    """

    memory_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)
    refs_stamp: str = ""


class MemoryLedger:
    """A durable SQLite ledger of project memories — the write-through source of truth.

    Construction is resilient: a missing parent dir or a corrupt file must not
    crash the open (the durable copy degrades to empty rather than wedging the
    process). The resilient open, WAL pragma, and schema migration all mirror the
    :class:`~loremaster.index.manifest.Manifest`'s posture.

    Args:
        db_path: The SQLite ledger path on the state volume (alongside the
            manifest at ``<slug>.memory.db``). A real file — never ``:memory:``.
    """

    def __init__(self, db_path: str) -> None:
        """Open (or create) the ledger database resiliently, enable WAL, ensure schema.

        The open is RESILIENT (FP-01 + FP-08) via the SHARED
        :func:`~loremaster.index.sqlite_resilient.open_resilient_sqlite`: an
        absent parent dir is created and a corrupt on-disk image is deleted and
        recreated (the durable copy degrades to empty rather than crashing). A
        valid existing ledger opens UNCHANGED. WAL is enabled so concurrent
        readers never block the single writer, mirroring the manifest (D10).

        Args:
            db_path: The SQLite ledger path on the state volume.
        """
        self._db_path = db_path
        # ``check_same_thread=False`` (inside the resilient helper) so the ledger
        # can be driven from the asyncio loop thread and a watcher thread under
        # the same single-writer concurrency contract the manifest uses.
        self._connection = open_resilient_sqlite(db_path)
        self._connection.row_factory = sqlite3.Row
        # WAL: readers see a consistent committed snapshot and never block the
        # single writer. Connection-persistent for a file-backed db, set once.
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    @property
    def db_path(self) -> str:
        """The ledger's SQLite database path."""
        return self._db_path

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying SQLite connection (for diagnostics and tests)."""
        return self._connection

    def record(
        self,
        *,
        memory_id: str,
        text: str,
        metadata: dict[str, Any],
        refs_stamp: str,
    ) -> None:
        """Idempotently upsert a memory row keyed on ``memory_id``.

        Recording the same ``memory_id`` twice upserts (one row, latest write
        wins) via ``ON CONFLICT ... DO UPDATE``, never appends — so a
        write-through on a re-saved note collapses to a single durable row,
        matching the deterministic-id dedup the store does against Qdrant.

        Args:
            memory_id: The deterministic ``uuid5`` point id (the natural key).
            text: The note text — the recallable content the restore re-embeds.
            metadata: The caller-supplied metadata to store with the note.
            refs_stamp: The order-insensitive refs stamp folded into the id, so a
                restore re-mints the SAME id.
        """
        # Metadata is a nested dict; a SQLite cell is scalar, so serialise to JSON
        # text (round-tripped on read via ``json.loads`` in :meth:`all_records`).
        metadata_json = json.dumps(metadata)
        self._connection.execute(
            f"""
            INSERT INTO memories ({_COLUMN_MEMORY_ID}, {_COLUMN_TEXT},
                                  {_COLUMN_METADATA}, {_COLUMN_REFS_STAMP})
            VALUES (?, ?, ?, ?)
            ON CONFLICT({_COLUMN_MEMORY_ID}) DO UPDATE SET
                {_COLUMN_TEXT} = excluded.{_COLUMN_TEXT},
                {_COLUMN_METADATA} = excluded.{_COLUMN_METADATA},
                {_COLUMN_REFS_STAMP} = excluded.{_COLUMN_REFS_STAMP}
            """,
            (memory_id, text, metadata_json, refs_stamp),
        )
        self._connection.commit()

    def all_records(self) -> list[MemoryRecord]:
        """Return every durable memory row.

        The restore path iterates these and re-embeds each, re-minting the
        deterministic id from ``text`` + ``refs_stamp``.

        Returns:
            Every :class:`MemoryRecord` in the ledger (empty for a fresh ledger).
        """
        rows = self._connection.execute(
            f"""
            SELECT {_COLUMN_MEMORY_ID}, {_COLUMN_TEXT},
                   {_COLUMN_METADATA}, {_COLUMN_REFS_STAMP}
            FROM memories
            """
        ).fetchall()
        return [self._row_to_record(row) for row in rows]

    def count(self) -> int:
        """Return the number of durable memory rows.

        The independent divergence oracle: when ``store.count_points()`` is below
        this count, the memory collection is short and a restore re-embeds. A
        fresh ledger reports ``0`` (the inert first-boot baseline).

        Returns:
            The total durable memory-row count.
        """
        row = self._connection.execute("SELECT COUNT(*) FROM memories").fetchone()
        return int(row[0])

    def close(self) -> None:
        """Close the underlying database connection."""
        self._connection.close()

    @staticmethod
    def _row_to_record(row: sqlite3.Row) -> MemoryRecord:
        """Decode a raw ``memories`` row (with JSON ``metadata``) into a record."""
        return MemoryRecord(
            memory_id=row[_COLUMN_MEMORY_ID],
            text=row[_COLUMN_TEXT],
            metadata=json.loads(row[_COLUMN_METADATA]),
            refs_stamp=row[_COLUMN_REFS_STAMP],
        )
