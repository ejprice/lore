"""The store-backed span reader — a hash-verified, freshness-aware twin of
``read_file`` that serves a file's verbatim body straight from the unified
SurrealDB store instead of from disk.

``StoreReadTool.read(tier, path, line_start, line_end)`` is the store-side half
of the Deliverable-3 read surface: an anti-hallucination primitive returning the
EXACT indexed text of a file span with a ``[SOURCE:...]`` provenance header, so
the model quotes real source rather than recalling it. Where
:class:`~loremaster.read_file.ReadFileTool` reads the live filesystem, this tool
reads the ``file_text`` row the indexer persisted (writer:
:meth:`~loremaster.store.surreal.SurrealStore.file_text_fragment`) and cross-
checks it against the manifest — so it can serve the exact bytes lore INDEXED
even when the working tree has since moved on, and say so when it has.

This is ADDITIVE (P8b): the filesystem-backed :class:`ReadFileTool` stays fully
intact and no MCP tool is wired here — a later wave wires ``lore_read`` onto this
engine, and the P8d flip retires nothing yet. Because the P8d flip must be
seamless, this tool's INPUT contract and span semantics are byte-identical to
:class:`ReadFileTool`'s:

* **Span addressing** is 1-based inclusive, reusing
  :meth:`ReadFileTool._resolve_span` VERBATIM (never a reimplementation):
  ``line_start`` omitted ⇒ line 1, ``line_end`` omitted ⇒ EOF, an end past EOF
  is clamped, and a non-positive start / inverted span / start past EOF is a hard
  error.
* **Containment** rejects an absolute path or a ``../`` traversal up front — the
  same clean rejection :class:`ReadFileTool` gives. The store lookup is a keyed
  ``[tier, path]`` read that *cannot* traverse, but the contract must match so
  the flip changes no caller-visible behaviour. (The escaping-symlink arm of the
  filesystem guard has no analogue here — there is no filesystem to escape.)

Two store-only guarantees the filesystem tool cannot make:

* **INTEGRITY (hard fail).** The stored body's SHA-512 is recomputed
  (:func:`~loremaster.index.records.sha512_hex`) and compared to the digest
  stored alongside it. A mismatch means the store copy is CORRUPT, and a
  corrupted copy must NEVER serve silently — it raises
  :class:`StoreReadIntegrityError`, never a span.
* **FRESHNESS (soft flag).** The manifest is the authority on per-file state; if
  its row is not ``indexed`` or its ``sha512`` disagrees with the ``file_text``
  digest, the file on disk has moved past what was indexed. The span is still
  served — degraded-honesty, the same serve-but-say-so posture the search path
  takes — but carries an explicit ``stale`` flag and a visible notice in the
  rendered header. A manifest row that is missing ENTIRELY means the file is not
  tracked at all: a not-found, not a stale serve.

A miss — an unknown ``(tier, path)`` (no ``file_text`` body, or no manifest row)
— raises :class:`StoreReadNotFoundError` naming the tier and path and pointing
the caller at ``lore_search``: a teaching miss, not a bare error. A downed store
connection propagates loudly as
:class:`~loremaster.store.surreal.SurrealConnectionError` (it is never caught
here), so a dead server can never masquerade as a not-found.
"""

from __future__ import annotations

import os

from pydantic import BaseModel, ConfigDict

from loremaster.index.records import sha512_hex
from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest
from loremaster.read_file import ReadFileError, ReadFileTool
from loremaster.store.surreal import SurrealStore

# The provenance-header format the tool stamps on every result — byte-identical
# to :data:`loremaster.read_file._SOURCE_HEADER_TEMPLATE` so a store-served
# citation is indistinguishable from a disk-served one (the flip is seamless):
# a [SOURCE:...] citation naming the tier, the tier-relative path, and the
# resolved 1-based inclusive line span.
_SOURCE_HEADER_TEMPLATE = "[SOURCE:{tier}:{path}:{line_start}-{line_end}]"

# The visible degraded-honesty notice appended to a STALE serve's header, so a
# reader sees at a glance that the served bytes are what lore INDEXED, which may
# now be behind the working tree — and how to reconcile it. Uppercase ``STALE``
# is the load-bearing token a caller/renderer keys off.
_STALE_HEADER_NOTICE = (
    "STALE: served from the index, which may be behind the file on disk — "
    "run lore_index(reconcile=True) to refresh, or verify with lore_search"
)

# The keys of the ``{text, sha512}`` row :meth:`SurrealStore.file_text` returns —
# named once here so the tool never hand-writes the string literals the store's
# schema owns.
_FILE_TEXT_TEXT_KEY = "text"
_FILE_TEXT_SHA_KEY = "sha512"


class StoreReadError(Exception):
    """Base class for every failure :class:`StoreReadTool` raises.

    A caller that catches this catches every store-read failure mode — a
    not-found, a containment rejection, an integrity failure, or an out-of-range
    span — without needing to enumerate the subclasses.
    """


class StoreReadNotFoundError(StoreReadError):
    """The store has no complete, tracked copy of ``(tier, path)``.

    Raised when there is no ``file_text`` body for the pair, OR when the manifest
    carries no row for it at all (an untracked file). The message names the tier
    and path and points the caller at ``lore_search`` — a teaching miss, never a
    bare error.
    """


class StoreReadContainmentError(StoreReadError):
    """The requested path is an absolute path or a ``../`` traversal.

    The store lookup is a keyed read that cannot traverse, but the input contract
    is rejected up front regardless, so it stays byte-identical to
    :class:`~loremaster.read_file.ReadFileTool`'s containment rejection (the P8d
    flip must change no caller-visible behaviour).
    """


class StoreReadIntegrityError(StoreReadError):
    """The stored body's recomputed SHA-512 disagrees with its stored digest.

    A corrupted store copy: the ``file_text`` row's ``text`` and the ``sha512``
    recorded with it no longer agree. A corrupted copy must NEVER serve silently,
    so this is a HARD failure — no span is ever produced. The message names the
    tier and path but never echoes the (corrupt) body.
    """


class StoreFileSpan(BaseModel):
    """A store-served file span: the exact text, its provenance, and its marks.

    The store-side analogue of :class:`~loremaster.read_file.FileSpan`, extended
    with the two marks only the store can supply: an INTEGRITY mark (the served
    bytes were hash-verified against their stored digest) and a FRESHNESS mark
    (whether the index is behind the working tree).

    Attributes:
        tier: The tier the span was read from.
        path: The tier-relative path that was read.
        line_start: First line (1-based, inclusive) the ``text`` covers.
        line_end: Last line (1-based, inclusive) the ``text`` covers.
        text: The exact stored text of the span, byte-for-byte.
        stale: The FRESHNESS mark — ``True`` when the manifest reports the file
            as not ``indexed`` or its digest disagrees with the served body's, so
            the served bytes may be behind the file on disk (a degraded-honesty
            serve). ``False`` when the index is in step with what was indexed.
        integrity_verified: The INTEGRITY mark — always ``True`` on a returned
            span. A body whose recomputed digest disagreed with its stored digest
            raises :class:`StoreReadIntegrityError` and never produces a span, so
            this records that the served bytes ARE hash-verified, not merely
            fetched.
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    path: str
    line_start: int
    line_end: int
    text: str
    stale: bool
    integrity_verified: bool

    @property
    def header(self) -> str:
        """The ``[SOURCE:tier:path:start-end]`` citation, plus a STALE notice when stale.

        On a fresh serve this is byte-identical to
        :attr:`~loremaster.read_file.FileSpan.header`. On a stale serve the
        citation is followed by a visible ``[STALE: …]`` notice so the degraded
        freshness is impossible to miss in the rendered output.
        """
        citation = _SOURCE_HEADER_TEMPLATE.format(
            tier=self.tier,
            path=self.path,
            line_start=self.line_start,
            line_end=self.line_end,
        )
        if self.stale:
            return f"{citation} [{_STALE_HEADER_NOTICE}]"
        return citation

    def render(self) -> str:
        """Render the full tool output: the provenance header, then the span text."""
        return f"{self.header}\n{self.text}"


class StoreReadTool:
    """Hash-verified, freshness-aware store-backed span reader (dependency-injected).

    Serves a file's verbatim body straight from the unified SurrealDB store
    (``file_text`` table), cross-checked against the manifest for freshness and
    against its own stored digest for integrity. Both the store and the manifest
    are injected so the tool is exercised identically against the real ports and
    the in-memory fakes.

    Args:
        store: The :class:`~loremaster.store.surreal.SurrealStore` whose
            ``file_text`` bodies this tool serves.
        manifest: The :class:`~loremaster.index.surreal_manifest.SurrealManifest`
            consulted for the per-file freshness/tracking state.
    """

    def __init__(self, *, store: SurrealStore, manifest: SurrealManifest) -> None:
        self._store = store
        self._manifest = manifest

    async def read(
        self,
        tier: str,
        path: str,
        line_start: int | None = None,
        line_end: int | None = None,
    ) -> StoreFileSpan:
        """Return the requested span of ``(tier, path)`` from the store, verified.

        Rejects an uncontained path, fetches the stored body, HARD-fails on an
        integrity mismatch, marks the span stale when the manifest reports the
        index behind disk, and slices the 1-based inclusive ``[line_start,
        line_end]`` span with the SAME semantics :class:`ReadFileTool` uses.

        Args:
            tier: The tier to read from.
            path: The tier-relative file path.
            line_start: First line (1-based, inclusive); ``None`` ⇒ 1.
            line_end: Last line (1-based, inclusive); ``None`` ⇒ EOF.

        Returns:
            The resolved :class:`StoreFileSpan`.

        Raises:
            StoreReadContainmentError: ``path`` is absolute or a ``../`` traversal.
            StoreReadNotFoundError: No ``file_text`` body, or no manifest row.
            StoreReadIntegrityError: The stored body's digest does not verify.
            StoreReadError: The requested span is out of range / inverted.
            SurrealConnectionError: The store or manifest connection is down (it
                propagates loudly — never masqueraded as a not-found).
        """
        # (1) INPUT CONTRACT — reject an absolute path / ``../`` traversal up front,
        # before the store is even consulted (the store lookup cannot traverse, but
        # the rejection must match ReadFileTool's so the P8d flip is seamless).
        self._reject_uncontained(tier, path)

        # (2) Fetch the stored body. A downed connection RAISES here (never caught)
        # so it can never masquerade as a not-found; an absent row IS a not-found.
        row = await self._store.file_text(tier, path)
        if row is None:
            raise self._not_found_error(tier, path)
        text = row[_FILE_TEXT_TEXT_KEY]
        stored_sha512 = row[_FILE_TEXT_SHA_KEY]

        # (3) INTEGRITY (hard fail) — verify the body against the digest stored WITH
        # it, on the bytes we hold, before anything else decides to serve them. A
        # corrupted store copy must NEVER serve silently.
        if sha512_hex(text) != stored_sha512:
            raise self._integrity_error(tier, path)

        # (4) FRESHNESS — the manifest is the authority on per-file state. A row
        # missing ENTIRELY means the file is untracked: a not-found, not a stale
        # serve. Otherwise the span is served, flagged stale when the index is
        # behind disk (non-``indexed`` state, or a manifest digest that disagrees
        # with the served body's).
        manifest_row = await self._manifest.get(tier, path)
        if manifest_row is None:
            raise self._not_found_error(tier, path)
        stale = manifest_row.state != STATE_INDEXED or manifest_row.sha512 != stored_sha512

        # (5) SPAN — slice with the SAME 1-based inclusive semantics ReadFileTool
        # uses, reusing its ``_resolve_span`` VERBATIM (single source of truth), and
        # re-homing its span-range rejection into this tool's own error family.
        lines = text.splitlines(keepends=True)
        try:
            start, end = ReadFileTool._resolve_span(tier, path, len(lines), line_start, line_end)
        except ReadFileError as error:
            raise StoreReadError(str(error)) from error
        span_text = "".join(lines[start - 1 : end])
        return StoreFileSpan(
            tier=tier,
            path=path,
            line_start=start,
            line_end=end,
            text=span_text,
            stale=stale,
            integrity_verified=True,
        )

    @staticmethod
    def _reject_uncontained(tier: str, path: str) -> None:
        """Reject an absolute path or a ``../`` traversal (the input contract).

        Mirrors the lexical step (1) of the audited C4 guard
        (:meth:`~loremaster.source.snapshot.SnapshotLayout._safe_path`): an
        absolute path, or any ``..`` path component, is refused. The
        filesystem-only arms of that guard (normpath containment, escaping
        symlinks) have no analogue here — the store lookup is a keyed
        ``[tier, path]`` read with no directory tree to escape — so ONLY the two
        lexical checks apply, keeping the rejection byte-identical to
        :class:`~loremaster.read_file.ReadFileTool`'s for these two shapes.

        Raises:
            StoreReadContainmentError: ``path`` is absolute or carries a ``..``.
        """
        if os.path.isabs(path) or any(part == ".." for part in path.split("/")):
            raise StoreReadContainmentError(
                f"path {path!r} in tier {tier!r} is rejected by the containment guard "
                f"(an absolute path or a '../' traversal). Pass a tier-relative path "
                f"that stays within the tier."
            )

    @staticmethod
    def _not_found_error(tier: str, path: str) -> StoreReadNotFoundError:
        """A not-found error naming the tier/path and pointing at ``lore_search``.

        Covers both a missing ``file_text`` body and a missing manifest row (an
        untracked file) — either way the store has no complete, tracked copy to
        serve. A teaching miss, never a bare error.
        """
        return StoreReadNotFoundError(
            f"file {path!r} not found in tier {tier!r} (no indexed body in the store). "
            f"Run lore_search to locate the current file, or lore_index(reconcile=True) "
            f"if the path should exist — the index may be ahead of or behind this path."
        )

    @staticmethod
    def _integrity_error(tier: str, path: str) -> StoreReadIntegrityError:
        """A hard integrity error — names the tier/path, never echoes the body."""
        return StoreReadIntegrityError(
            f"stored body for {path!r} in tier {tier!r} is CORRUPT: its recomputed "
            f"SHA-512 does not match the digest stored with it — refusing to serve a "
            f"corrupted store copy. Reindex the file to repair it."
        )
