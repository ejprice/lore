"""Manifest vocabulary — ``FileRow`` + the lifecycle states + the amendment history.

The manifest is the authority on per-file, per-tier indexing state — never the
vector store. Only a relational ledger can express *partial-embed failure*
(``state`` + expected ``n_chunks``) and make a per-file update transactional —
the two things a vector store or a merkle root cannot do. The store's payloads
carry ``tier``/``content_hash``/``file_path``/``mtime_ns`` redundantly so the
manifest is rebuildable by scroll if it is ever lost.

The SQLite ``Manifest`` class that once lived here was DELETED post-P5:
:class:`~loremaster.index.surreal_manifest.SurrealManifest` is the live
implementation now, reading/writing this exact ``FileRow`` shape against the
unified SurrealDB database. This module survives as the shared VOCABULARY both
ports speak — :class:`FileRow` and the ``STATE_*`` constants — plus the
amendment-history record :mod:`~loremaster.index.surreal_manifest` cites for
its own behavioural contract:

* **C1 — composite primary key ``(tier, file_path)``.** A module-relative path
  is not globally unique across tiers (a ``custom`` override and the
  ``community`` original can share a path), so the key is ``(tier, file_path)``
  and two tiers' rows for one path coexist. Every accessor is tier-scoped.
* **D10 — WAL mode** + ``check_same_thread=False`` (the SQLite-era answer;
  superseded by the Surreal port's own connection lifecycle). WAL let N
  concurrent readers (freshness + graph lookups in MCP handlers) see a
  consistent snapshot without ever blocking the single writer.

The row shape, one row per ``(tier, file)`` and mirrored by :class:`FileRow`:
``tier, file_path, sha512, mtime_ns, size, n_chunks, chunk_ids, state,
updated_at``. ``chunk_ids`` is a list of point ids. ``state`` is one of
``indexed | dirty | embedding | failed``. A ``meta(k, v)`` auxiliary key/value
store holds e.g. per-tier version stamps.

The DDL below is the SQLite schema the deleted ``Manifest`` executed — kept as
the documented origin of the row shape :class:`FileRow` decodes, not as live
code (nothing constructs a connection against it anymore).
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

# The lifecycle states a file row may occupy.
STATE_INDEXED = "indexed"
STATE_DIRTY = "dirty"
STATE_EMBEDDING = "embedding"
STATE_FAILED = "failed"

# Historical SQLite DDL — the schema the deleted ``Manifest`` class executed on
# every connection open. Kept as the documented origin of the row shape
# :class:`FileRow` still decodes; the PK was the (tier, file_path) pair (C1) so
# the same path could live under multiple tiers. Not executed by anything today.
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

