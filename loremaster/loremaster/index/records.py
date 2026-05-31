"""Chunk → Qdrant-record translation and the tier-keyed point-ID scheme (C1).

This module is the *single* place the natural key is turned into a Qdrant point
id. C1 makes ``tier`` a **first-class key dimension**: a module-relative
``file_path`` is not globally unique across tiers (a ``custom`` override and the
``community`` original can share a path), so without ``tier`` in the key one
tier would silently overwrite another's point. Folding ``tier`` in — and
stamping it into the payload — is what lets two tiers' copies of one path
coexist and what makes per-tier purges (``delete_by_tier``) and ``(tier,
file_path)`` deletes correct.

The documented key string (this exact ordering is load-bearing — a drift guard
test pins it)::

    "{slug}:{tier}:{file_path}:{chunk_type}:{identity}:{sub_ordinal}:{key_version}"

``tier`` sits immediately after ``slug`` — the project → tier → file ownership
ordering. The id is a UUID5 over the URL namespace, so it is deterministic
across processes and hosts yet collision-resistant. Centralising the derivation
here makes incremental upsert idempotent (re-indexing an unchanged chunk
overwrites the *same* point) and makes the sibling-collapse bug structurally
impossible: a chunker physically cannot emit a record whose id is not a function
of its full identity.

``KEY_VERSION`` is ``2`` — bumped from the parked foundation's ``1`` because
adding ``tier`` is a *breaking* re-key of the scheme. Greenfield, so there is no
migration; the bump simply keeps the change detectable for any future consumer.
"""

from __future__ import annotations

import hashlib
import uuid
from typing import Any

from lorescribe.models import Chunk
from pydantic import BaseModel, ConfigDict

# Baseline key-version stamped into every point id. Bumped to 2 when ``tier`` was
# folded into the key (C1). Bumping it again, on a future scheme change, yields
# different ids for the same chunks, triggering a deliberate re-key/invalidate
# pass instead of a silent orphan.
KEY_VERSION = 2

# The natural-key components, joined by this separator, form the UUID5 name. A
# colon never appears inside a slug/tier/chunk_type/identity component in
# practice; the fields are positional so even an empty component keeps the
# layout stable.
_KEY_SEPARATOR = ":"

# Encoding used when hashing a ``str`` payload, so the str and bytes paths agree.
_HASH_ENCODING = "utf-8"


class Record(BaseModel):
    """A single Qdrant point: its id, the text to embed, and the stored payload.

    Attributes:
        point_id: The deterministic UUID5 point id (see :func:`point_id`).
        embedding_text: The exact string handed to the embedder (carried verbatim
            from :attr:`Chunk.embedding_text`).
        payload: The Qdrant payload — every structural field (including ``tier``)
            plus the chunk's own ``metadata`` merged on top.
    """

    model_config = ConfigDict(extra="forbid")

    point_id: str
    embedding_text: str
    payload: dict[str, Any]


def point_id(
    slug: str,
    tier: str,
    file_path: str,
    chunk_type: str,
    identity: str,
    sub_ordinal: int,
    key_version: int = KEY_VERSION,
) -> str:
    """Derive the deterministic Qdrant point id for a chunk's tiered natural key.

    The id is
    ``uuid5(NAMESPACE_URL, "slug:tier:file_path:chunk_type:identity:sub_ordinal:key_version")``.
    Identical inputs always yield the identical id (the incremental-upsert
    enabler); a change to *any* component — including ``tier`` (the C1
    collision) and ``key_version`` — yields a different id.

    Args:
        slug: The project slug owning the collection.
        tier: The source tier/root the chunk belongs to (the C1 key dimension).
        file_path: The chunk's source file path.
        chunk_type: The chunker's category for the chunk.
        identity: The within-file natural key (heading path, qualified name, ...).
        sub_ordinal: Disambiguator for sibling chunks sharing an ``identity``.
        key_version: The keying-scheme version; defaults to :data:`KEY_VERSION`.

    Returns:
        The point id as a canonical UUID string.
    """
    name = _KEY_SEPARATOR.join(
        (slug, tier, file_path, chunk_type, identity, str(sub_ordinal), str(key_version))
    )
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


def sha512_hex(data: bytes | str) -> str:
    """Return the lowercase hex SHA-512 digest of ``data``.

    SHA-512 (faster than SHA-256 on 64-bit CPUs; matches the host's ``.sha512``
    backup tooling) is the content hash that drives staleness detection. A
    ``str`` input is hashed as its UTF-8 encoding so the str and bytes paths
    agree.

    Args:
        data: The content to hash, as bytes or text.

    Returns:
        The 128-character lowercase hex digest.
    """
    payload = data.encode(_HASH_ENCODING) if isinstance(data, str) else data
    return hashlib.sha512(payload).hexdigest()


def chunk_to_record(
    chunk: Chunk,
    *,
    slug: str,
    tier: str,
    file_path: str,
    content_hash: str,
    mtime_ns: int,
) -> Record:
    """Translate a :class:`~lorescribe.models.Chunk` into a tiered :class:`Record`.

    The payload stamps ``tier`` (C1 — powers ``delete_by_tier`` and tier
    filtering) and carries every structural field needed to rebuild the manifest
    by scroll — ``chunk_type``, ``identity``, ``sub_ordinal``, ``file_path``,
    ``content_hash``, ``mtime_ns``, ``line_start``, ``line_end``,
    ``source_text`` — with the chunk's own ``metadata`` merged on top. The
    payload is a fresh dict, never an alias of ``chunk.metadata``.

    Args:
        chunk: The source chunk to translate.
        slug: The project slug (a point-id component).
        tier: The source tier/root the chunk belongs to (point-id + payload).
        file_path: The chunk's source file path.
        content_hash: The file's SHA-512 hex digest at index time.
        mtime_ns: The file's modification time in nanoseconds at index time.

    Returns:
        The fully-populated :class:`Record`.
    """
    payload: dict[str, Any] = {
        "chunk_type": chunk.chunk_type,
        "identity": chunk.identity,
        "sub_ordinal": chunk.sub_ordinal,
        "tier": tier,
        "file_path": file_path,
        "content_hash": content_hash,
        "mtime_ns": mtime_ns,
        "line_start": chunk.line_start,
        "line_end": chunk.line_end,
        "source_text": chunk.source_text,
        # Merge the chunk's own metadata last so a chunker can enrich the record;
        # ``dict(chunk.metadata)`` copies so the payload never aliases the chunk.
        **dict(chunk.metadata),
    }
    return Record(
        point_id=point_id(
            slug, tier, file_path, chunk.chunk_type, chunk.identity, chunk.sub_ordinal
        ),
        embedding_text=chunk.embedding_text,
        payload=payload,
    )
