"""Embedding-schema fingerprint + schema-rebuild helpers.

This module owns the pure helpers the schema-rebuild feature needs:

* :data:`EMBEDDING_SCHEMA_VERSION` — the monotonically-increasing schema epoch.
* :func:`embedding_schema_fingerprint` — a deterministic SHA-256 hex digest of
  the embedding-schema-relevant config fields.  Two deployments with identical
  schema fields produce the same fingerprint; a schema change (model, dim, etc.)
  produces a different one.
* :func:`rebuild_needed` — pure three-case decision: stored vs. current
  fingerprint → bool.
* :func:`rebuilding_notice` — reads the manifest's schema-rebuild status and
  returns a human-readable progress message when a rebuild is in progress, or
  ``None`` when idle.

The two manifest meta-key constants (:data:`SCHEMA_FINGERPRINT_META_KEY`,
:data:`SCHEMA_REBUILD_STATUS_META_KEY`) live here so the tools, the indexer, and
``index_status`` import ONE source of truth (the contract's clause-5 convention).
"""

from __future__ import annotations

import hashlib
import json
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from loremaster.config import LoreConfig
    from loremaster.index.manifest import Manifest

# ---------------------------------------------------------------------------
# Manifest meta keys — the single shared source of truth (clause 5)
# ---------------------------------------------------------------------------

SCHEMA_FINGERPRINT_META_KEY = "embedding_schema_fingerprint"
"""Manifest ``meta`` key holding the stamped embedding-schema fingerprint.

Stamped by :meth:`~loremaster.index.indexer.Indexer.rebuild_all` only after a
full rebuild completes; read at startup to decide whether a rebuild is needed.
"""

SCHEMA_REBUILD_STATUS_META_KEY = "schema_rebuild_status"
"""Manifest ``meta`` key holding the JSON rebuild-status blob.

Written by ``build_app_context`` (state ``in_progress``) before spawning the
background rebuild and by :meth:`~loremaster.index.indexer.Indexer.rebuild_all`
as it progresses / completes; read by ``index_status`` and
:func:`rebuilding_notice`.
"""

# The rebuild-status JSON field names + the state values, named so the producer
# (indexer / server) and the consumers (index_status / rebuilding_notice) never
# disagree on a literal.
_STATUS_STATE_KEY = "state"
_STATUS_DONE_KEY = "done"
_STATUS_TOTAL_KEY = "total"
_STATE_IN_PROGRESS = "in_progress"


# ---------------------------------------------------------------------------
# Schema epoch
# ---------------------------------------------------------------------------

EMBEDDING_SCHEMA_VERSION: int = 1
"""The current embedding-schema epoch.

Increment this integer whenever a schema change requires that ALL existing
indexes be rebuilt from scratch (e.g. a new vector dimension tier, a change to
the canonical embedding-text format).  Client code that needs to store the epoch
alongside the fingerprint reads this constant directly.
"""


# ---------------------------------------------------------------------------
# Fingerprint
# ---------------------------------------------------------------------------

def embedding_schema_fingerprint(config: LoreConfig) -> str:
    """Return the SHA-256 hex digest of the embedding-schema-relevant config fields.

    The fingerprint is DETERMINISTIC: the same config always produces the same
    64-char lowercase hex string regardless of call order, process restart, or
    dict iteration order.  Determinism comes from a CANONICAL JSON encoding
    (``sort_keys=True`` + compact separators) over a fixed field set.

    Schema-relevant fields (changes flip the fingerprint):
        * ``embedding.backend``
        * ``embedding.model``
        * ``embedding.dim``
        * ``embedding.endpoint``
        * ``embedding.max_input_tokens``
        * ``embedding.tokenizer``
        * ``embedding.truncate``
        * ``embedding.query_prompt_name``
        * ``embedding.document_prompt_name``
        * ``chunkers`` (the full mapping, canonicalised for stability)
        * :data:`EMBEDDING_SCHEMA_VERSION` (the epoch)

    Unrelated fields (changes do NOT flip the fingerprint):
        * ``embedding.concurrency``
        * ``server.port``
        * ``qdrant.url``
        * project slug, roots, watchers, auth, logging

    Args:
        config: The validated :class:`~loremaster.config.LoreConfig`.

    Returns:
        A 64-character lowercase hex string (SHA-256 digest).
    """
    embedding = config.embedding
    # Exactly the schema-relevant fields, in a flat mapping. ``sort_keys`` makes
    # ordering irrelevant, so the literal order here is documentation, not data.
    payload = {
        "embedding_schema_version": EMBEDDING_SCHEMA_VERSION,
        "backend": embedding.backend,
        "model": embedding.model,
        "dim": embedding.dim,
        "endpoint": embedding.endpoint,
        "max_input_tokens": embedding.max_input_tokens,
        "tokenizer": embedding.tokenizer,
        "truncate": embedding.truncate,
        "query_prompt_name": embedding.query_prompt_name,
        "document_prompt_name": embedding.document_prompt_name,
        "chunkers": config.chunkers,
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Rebuild decision
# ---------------------------------------------------------------------------

def rebuild_needed(stored: str | None, current: str) -> bool:
    """Decide whether a schema rebuild is needed from the stored and current fingerprints.

    Pure three-case logic — no I/O:

    * ``(None, X)``  → ``True``  (provenance unknown → fail safe)
    * ``(X, X)``     → ``False`` (fingerprints match → no rebuild)
    * ``(X, Y)``     → ``True``  (fingerprints differ → rebuild)

    Args:
        stored: The fingerprint stored in the manifest, or ``None`` if the
            manifest has no stamp yet (fresh deploy or legacy index).
        current: The fingerprint computed from the current config.

    Returns:
        ``True`` when a rebuild is required; ``False`` when the index is
        already up to date.
    """
    return stored is None or stored != current


# ---------------------------------------------------------------------------
# Rebuild-in-progress notice
# ---------------------------------------------------------------------------

def rebuilding_notice(manifest: Manifest) -> str | None:
    """Return a human-readable rebuild-progress message, or ``None`` when idle.

    Reads the :data:`SCHEMA_REBUILD_STATUS_META_KEY` meta key from ``manifest``.
    When the stored state is ``"in_progress"``, returns a message that mentions
    rebuilding (so :func:`_mentions_rebuilding` in the tests returns ``True``) and
    carries the ``done``/``total`` progress numbers so the agent knows to retry.

    Returns ``None`` when no status is recorded, when the JSON is malformed, or
    when the state is anything other than ``"in_progress"`` (e.g. ``"idle"`` or
    ``"done"``) — so an idle empty result stays a plain empty result.

    Args:
        manifest: The open :class:`~loremaster.index.manifest.Manifest` to read.

    Returns:
        A progress string, or ``None`` when not rebuilding.
    """
    raw = manifest.meta_get(SCHEMA_REBUILD_STATUS_META_KEY)
    if raw is None:
        return None
    try:
        status = json.loads(raw)
    except (ValueError, TypeError):
        # A malformed blob is treated as "no rebuild in progress" — better a
        # missing notice than a crash inside a read tool.
        return None
    if not isinstance(status, dict) or status.get(_STATUS_STATE_KEY) != _STATE_IN_PROGRESS:
        return None
    done = status.get(_STATUS_DONE_KEY, 0)
    total = status.get(_STATUS_TOTAL_KEY, 0)
    return (
        f"lore store is rebuilding its index ({done}/{total} files re-embedded) — "
        "results are temporarily incomplete; retry shortly."
    )
