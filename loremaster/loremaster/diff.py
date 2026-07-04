"""Snapshot diffing (P8b, ledger #diff) — "what changed between two index
generations (or a generation and the live 'now' state)?"

Versioning is first-class in v1.0: :class:`~loremaster.index.snapshots.
SnapshotStamper` writes a ``snapshot`` row per full-project index GENERATION and
one ``snapshot_entry`` child per indexed file, each carrying that file's
``sha512`` plus a ``chunk_hashes`` ledger of per-chunk ``{identity, hash}`` pairs
(the DDL landed in P5-C1b — :func:`~loremaster.store.surreal_schema.
_snapshot_statements` / :func:`~loremaster.store.surreal_schema.
_snapshot_entry_statements`). THIS module is the READER above that ledger: it
compares two generations and reports what changed at two granularities.

* **File level** — added / removed / modified ``(tier, file_path)`` files, where
  *modified* means the SAME ``(tier, file_path)`` carried a DIFFERENT ``sha512``
  between the two states.
* **Function level** — for the files present in both states, the per-file
  ``chunk_hashes`` maps are compared, yielding the chunk identities *added*,
  *removed*, and *changed* (same chunk, different hash). The map key is the
  ``(identity, sub_ordinal)`` WITHIN-FILE natural key, NOT ``identity`` alone
  (P8b/F1): a windowed long function / split markdown section emits several
  chunks that SHARE one ``identity`` and differ only by ``sub_ordinal``, so
  keying on ``identity`` alone would collapse the siblings last-write-wins and
  silently mask a within-window drift. Such an identity is rendered once per
  changed window with a ``[window N]`` marker so the siblings stay legible. A
  renamed identity legitimately reads as one *removed* + one *added* — a diff
  cannot see through a rename, and that is documented, not papered over. A
  snapshot stamped BEFORE F1 whose ``chunk_hashes`` predate ``sub_ordinal`` had
  its siblings collapsed AT WRITE TIME (unrecoverable); a diff touching such a
  legacy entry degrades HONESTLY to per-identity comparison for that side and
  flags the file under ``DiffResult.legacy_files`` (serve-and-say-so), never a
  silent pretend-precision.

A file mid-reindex (``dirty``/``embedding``/``failed`` in the manifest) is NOT a
deletion: in the ``until=None`` view it is EXCLUDED from added/removed/modified
and surfaced explicitly under ``DiffResult.in_flight`` (P8b/F2), rather than
mis-reported as ``removed`` because it momentarily left the ``indexed`` set.

:class:`DiffEngine` mirrors :class:`~loremaster.index.snapshots.SnapshotStamper`
exactly: it owns its OWN lazily-opened, signed-in SurrealDB connection (the same
connect-lock + CAS-drop + ``KeyError``-classification self-heal idiom every
sibling port uses) for the read queries below, and reads through the injected
``store`` / ``manifest`` collaborators (their OWN connections) for the live
"now" state — never touching their connection lifecycle.

Two comparison modes:

* ``until`` is a snapshot id ⇒ **snapshot ↔ snapshot**. Both states come from
  ``snapshot_entry`` rows, so every file's ``chunk_hashes`` is already in hand;
  function-level comparison runs for every file present in both — including a
  file whose ``sha512`` is UNCHANGED but whose ``chunk_hashes`` drifted (a
  chunker-version change between generations), which is deliberately surfaced at
  function level rather than silently hidden (belt-and-braces).
* ``until=None`` ⇒ **snapshot ↔ now**. The live file set is the manifest's
  currently-``indexed`` rows (file-level sha512s); chunk identities are read from
  ``store.scroll`` — but ONLY for the files whose ``sha512`` actually changed, so
  a three-file change never triggers a full-store scan. CAVEAT (not a guarantee):
  this same-``sha512`` skip is sound only WHILE the chunker is unchanged — a fixed
  byte stream chunked by one deterministic lorescribe version yields identical
  chunks, so an unchanged-``sha512`` file carries no NEW chunk drift. A lorescribe
  chunker-VERSION upgrade between the snapshot and now breaks that premise: the
  same bytes could re-chunk differently, and this live path would skip past it.
  The belt-and-braces same-``sha512``-different-``chunk_hashes`` case is therefore
  surfaced ONLY in the snapshot↔snapshot mode above (both sides carry a stored
  ``chunk_hashes``), which stays the fidelity path across a chunker upgrade; the
  live path trades that tail case for read efficiency, by design.

Direction is literal: ``diff(since, until)`` computes the transition FROM
``since`` TO ``until``. Passing a newer ``since`` than ``until`` is not an error
and is not reordered — it computes the reverse transition (what was *added*
going forward reads as *removed* going back).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict
from surrealdb import AsyncSurreal, InvalidRecordIdError, RecordID

from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest

# F4: every store-derived string that flows into the multi-line render (chunk
# identities, file paths, snapshot ids) is laundered through the SAME hostile-char
# sanitiser the search renderer uses, so a newline/ZWSP-bearing identity can never
# forge a fake section or smuggle a hidden payload. Deliberate cross-module private
# import THIS wave (accepted): the sanitiser is not yet a public shared seam —
# promoting it (and sweeping impact.py, which shares this render archetype) is a
# P8d item recorded in FRICTION.md. Re-implementing it here would fork the
# hostile-char class and let the two drift.
from loremaster.search import _sanitise_line
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    _SERVER_LOG_HINT,
    _classify_engine_error,
    is_connection_error,
)
from loremaster.store.surreal import (
    _SIGNIN_PASS_KEY,
    _SIGNIN_USER_KEY,
    SurrealConnectionError,
    SurrealStore,
    SurrealStoreError,
    _SurrealConnection,
)
from loremaster.store.surreal_schema import SNAPSHOT_ENTRY_TABLE, SNAPSHOT_TABLE

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Bounds / constants
# ---------------------------------------------------------------------------

# ``list_snapshots``' default page size and its clamped inclusive range. ``limit``
# is a REQUIRED bound (a snapshot listing is never unbounded); an out-of-range
# request is clamped rather than rejected — the tool-surface convention already
# used for k/depth-style params elsewhere (see ``impact._clamp_depth``).
_DEFAULT_LIST_LIMIT = 20
_MIN_LIST_LIMIT = 1
_MAX_LIST_LIMIT = 500

# The bound ``LIMIT`` param name for ``list_snapshots`` — namespaced so it can
# never collide with a caller-supplied filter param on the same statement.
_LIMIT_PARAM = "diff_limit"

# A defensive bound on how many chunk rows a single changed file's live-fidelity
# read may pull from the store — mirrors ``SnapshotStamper._MAX_CHUNKS_PER_FILE``.
# Real files sit far below this; hitting it EXACTLY is a possible-truncation
# signal worth a WARNING (see :meth:`DiffEngine._live_chunk_map`).
_MAX_CHUNKS_PER_FILE = 50_000

# The default per-section render cap: how many files (or per-file chunk
# identities) :meth:`DiffResult.render` enumerates before eliding the rest with
# an EXPLICIT ``+K more`` marker (no-silent-truncation doctrine — mirrors
# ``impact._DEFAULT_MAX_CONSUMERS``).
_DEFAULT_MAX_PER_SECTION = 25

# The explicit elision-marker fragment rendered when the per-section cap squeezes
# entries out of a rendered list (mirrors ``impact._ELISION_TEMPLATE``).
_ELISION_TEMPLATE = "+{count} more (elided by max_per_section={cap})"

# The rendered stand-in for the live "now" state (``until=None``) in a diff view.
_NOW_LABEL = "(now)"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class DiffError(Exception):
    """Base class for every caller-facing error :class:`DiffEngine` raises for a
    bad *diff request* (as opposed to an infrastructure fault like
    :class:`~loremaster.store.surreal.SurrealConnectionError`, which propagates
    from the connection seam)."""


class SnapshotNotFoundError(DiffError):
    """A ``since``/``until`` id resolves to no snapshot.

    Raised for BOTH a well-formed-but-unknown id (nothing in the ``snapshot``
    table matches) AND an outright malformed id (the SDK could not even parse it
    into a record id) — one clean error family, so a caller can catch the single
    type and never has a raw ``surrealdb.errors.InvalidRecordIdError`` leak out.
    The message names the offending id and teaches the next step (list the real
    snapshots first) — the teaching-miss standard mirroring
    :class:`~loremaster.impact.ImpactTargetNotFoundError`.
    """


# ---------------------------------------------------------------------------
# Value objects (summarised, extra="forbid" — never a raw store dump)
# ---------------------------------------------------------------------------


class SnapshotSummary(BaseModel):
    """One row of :meth:`DiffEngine.list_snapshots` — a snapshot's headline facts.

    Attributes:
        id: The stringified snapshot record id (e.g. ``"snapshot:sn<hex>"``),
            the exact form :meth:`DiffEngine.diff` accepts as ``since``/``until``.
        created_at: The snapshot's ISO-8601 creation timestamp (the ``snapshot``
            row's ``DEFAULT time::now()`` value, rendered as a string).
        git_ref: The full commit sha captured at stamp time, or ``None`` for a
            non-git (tarball-imported) codebase.
        git_branch: The branch name captured at stamp time, or ``None`` (detached
            HEAD or non-git root).
        files_total: The number of indexed files the snapshot captured.
        chunks_total: The total number of chunk identities across those files.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    created_at: str
    git_ref: str | None
    git_branch: str | None
    files_total: int
    chunks_total: int


class FileRef(BaseModel):
    """One ``(tier, file_path)`` file identity in a file-level diff section."""

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str


class InFlightFile(BaseModel):
    """One file the ``until=None`` live view EXCLUDED because it is mid-reindex.

    A manifest row whose ``state`` is NOT ``indexed`` (``dirty``/``embedding``/
    ``failed``) is being re-processed, NOT deleted — surfacing it here (rather
    than letting it vanish from the live set and read as ``removed``) is the
    P8b/F2 fix.

    Attributes:
        tier: The tier the file belongs to.
        file_path: The file being re-processed.
        state: Its transient manifest lifecycle state (``dirty`` / ``embedding``
            / ``failed``) — carried so a caller can tell a routine reindex apart
            from a ``failed`` one worth investigating.
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str
    state: str


class FunctionDelta(BaseModel):
    """One file's function/chunk-level identity changes between two states.

    Attributes:
        tier: The tier the file belongs to.
        file_path: The file whose chunk identities changed.
        added: Chunk identities present in ``until`` but not ``since`` (sorted).
        removed: Chunk identities present in ``since`` but not ``until`` (sorted).
        changed: Chunk identities present in BOTH whose content hash differs
            (sorted). A renamed identity is NOT detected as a rename — it reads
            as one :attr:`removed` + one :attr:`added`. An identity split into
            WINDOW siblings (same identity, distinct ``sub_ordinal``) renders one
            entry PER changed window with a ``<identity> [window N]`` marker, so
            a within-window drift is never collapsed away.
        legacy: ``True`` when this delta was computed at DEGRADED per-identity
            precision because one of the compared snapshot entries predates the
            ``sub_ordinal`` ledger (its window siblings were already collapsed at
            write time). In that case the entries carry NO ``[window N]`` marker
            — the window information was unrecoverable — and the file is also
            listed under :attr:`DiffResult.legacy_files`.
    """

    model_config = ConfigDict(extra="forbid")

    tier: str
    file_path: str
    added: list[str]
    removed: list[str]
    changed: list[str]
    legacy: bool = False


class DiffResult(BaseModel):
    """The full answer to "what changed between ``since`` and ``until``?".

    Attributes:
        since: The ``since`` snapshot id the diff was computed FROM.
        until: The ``until`` snapshot id the diff was computed TO, or ``None``
            when the comparison target was the live "now" state.
        added: Files present in ``until`` but not ``since`` (sorted by
            ``(tier, file_path)``).
        removed: Files present in ``since`` but not ``until`` (sorted).
        modified: Files present in BOTH with a DIFFERENT ``sha512`` (sorted). A
            file whose ``sha512`` is unchanged but whose chunk_hashes drifted is
            NOT listed here — it surfaces only under :attr:`function_deltas`.
        function_deltas: Per-file chunk-identity changes (sorted by
            ``(tier, file_path)``); a file appears iff it has ANY chunk add /
            remove / change.
        in_flight: Files the live (``until=None``) view EXCLUDED from the
            comparison because they are mid-reindex (``dirty``/``embedding``/
            ``failed``) — surfaced explicitly so a transient state is never
            mis-reported as a deletion (P8b/F2). Always empty for a
            snapshot↔snapshot diff. Sorted by ``(tier, file_path)``.
        legacy_files: Files whose function-level comparison was DEGRADED to
            per-identity precision because a compared snapshot entry predates the
            ``sub_ordinal`` ledger (P8b/F1). Listed even when no delta surfaced,
            so the loss of window-level precision is always visible (a file here
            with no matching :attr:`function_deltas` entry means "compared, but at
            reduced precision, and found no per-identity change"). Sorted.
    """

    model_config = ConfigDict(extra="forbid")

    since: str
    until: str | None
    added: list[FileRef]
    removed: list[FileRef]
    modified: list[FileRef]
    function_deltas: list[FunctionDelta]
    in_flight: list[InFlightFile] = []
    legacy_files: list[FileRef] = []

    def render(self, max_per_section: int = _DEFAULT_MAX_PER_SECTION) -> str:
        """Render the compact, token-efficient human view of this diff.

        Counts FIRST (a one-glance summary), then per-section file lists, then
        the function-level changes grouped under their file. Every list is capped
        at ``max_per_section`` with an EXPLICIT ``+K more`` elision marker — a
        section is never silently truncated (no-silent-caps doctrine).

        Args:
            max_per_section: The cap on how many files (and, within a function
                delta, how many chunk identities) are enumerated before the rest
                are elided with a named marker.

        Returns:
            The rendered multi-line block.
        """
        until_label = self.until if self.until is not None else _NOW_LABEL
        lines = [
            f"diff: {_sanitise_line(self.since)} -> {_sanitise_line(until_label)}",
            f"files: +{len(self.added)} / -{len(self.removed)} / ~{len(self.modified)}",
            f"functions: {len(self.function_deltas)} file(s) with chunk-level changes",
        ]
        if self.in_flight:
            lines.append(
                f"in-flight: {len(self.in_flight)} file(s) excluded from comparison "
                f"(mid-reindex: dirty/embedding/failed)"
            )
        if self.legacy_files:
            lines.append(
                f"legacy: {len(self.legacy_files)} file(s) compared at per-identity "
                f"precision (snapshot predates the window ledger)"
            )
        self._render_file_section(lines, "added", self.added, max_per_section)
        self._render_file_section(lines, "removed", self.removed, max_per_section)
        self._render_file_section(lines, "modified", self.modified, max_per_section)
        self._render_in_flight_section(lines, max_per_section)
        self._render_function_section(lines, max_per_section)
        return "\n".join(lines)

    @staticmethod
    def _cap(items: list[Any], cap: int) -> tuple[list[Any], int]:
        """Bound ``items`` at ``cap``, returning ``(kept, elided_count)`` — never
        a silent cap (mirrors ``impact.ImpactEngine._cap``)."""
        if len(items) <= cap:
            return items, 0
        return items[:cap], len(items) - cap

    @classmethod
    def _render_file_section(
        cls, lines: list[str], label: str, refs: list[FileRef], cap: int
    ) -> None:
        """Append one capped file-list section (skipped entirely when empty).

        Each ``tier:file_path`` is run through :func:`_sanitise_line` (F4) so a
        hostile store-derived path cannot break the line it sits on or forge a
        fake section; the indent is applied AFTER sanitising (which strips the
        field's own leading/trailing whitespace)."""
        if not refs:
            return
        kept, elided = cls._cap(refs, cap)
        lines.append(f"{label}:")
        lines.extend(f"  {_sanitise_line(f'{ref.tier}:{ref.file_path}')}" for ref in kept)
        if elided:
            lines.append(f"  {_ELISION_TEMPLATE.format(count=elided, cap=cap)}")

    def _render_in_flight_section(self, lines: list[str], cap: int) -> None:
        """Append the capped in-flight section (F2): the mid-reindex files the
        live view excluded, each with its transient state — never silently
        dropped, never mistaken for a deletion. Empty ⇒ omitted."""
        if not self.in_flight:
            return
        kept, elided = self._cap(self.in_flight, cap)
        lines.append("in-flight (excluded, mid-reindex):")
        lines.extend(
            f"  {_sanitise_line(f'{entry.tier}:{entry.file_path}')} "
            f"({_sanitise_line(entry.state)})"
            for entry in kept
        )
        if elided:
            lines.append(f"  {_ELISION_TEMPLATE.format(count=elided, cap=cap)}")

    def _render_function_section(self, lines: list[str], cap: int) -> None:
        """Append the function-level section: per-file counts, then the capped,
        signed (``+``/``-``/``~``) identity enumeration grouped under each file.

        A file whose comparison was degraded (F1 legacy tolerance) is annotated
        inline so the reduced precision is visible right where its deltas render;
        every identity/path is sanitised (F4)."""
        if not self.function_deltas:
            return
        legacy_keys = {(ref.tier, ref.file_path) for ref in self.legacy_files}
        kept_files, elided_files = self._cap(self.function_deltas, cap)
        lines.append("function changes:")
        for delta in kept_files:
            head = _sanitise_line(f"{delta.tier}:{delta.file_path}")
            legacy_marker = (
                "  (legacy: per-identity precision)"
                if (delta.tier, delta.file_path) in legacy_keys
                else ""
            )
            lines.append(
                f"  {head}  "
                f"+{len(delta.added)}/-{len(delta.removed)}/~{len(delta.changed)}{legacy_marker}"
            )
            signed = (
                [("+", identity) for identity in delta.added]
                + [("-", identity) for identity in delta.removed]
                + [("~", identity) for identity in delta.changed]
            )
            kept_ids, elided_ids = self._cap(signed, cap)
            lines.extend(f"    {sign} {_sanitise_line(identity)}" for sign, identity in kept_ids)
            if elided_ids:
                lines.append(f"    {_ELISION_TEMPLATE.format(count=elided_ids, cap=cap)}")
        if elided_files:
            lines.append(f"  {_ELISION_TEMPLATE.format(count=elided_files, cap=cap)}")


# ---------------------------------------------------------------------------
# Internal per-file state (not part of the public surface)
# ---------------------------------------------------------------------------


class _FileState:
    """One file's diffable state in a snapshot (or live) generation.

    Bundles the file-level ``sha512`` with the function-level chunk map, so a
    single ``(tier, file_path)`` keyed lookup carries both granularities. The
    chunk map is keyed on the ``(identity, sub_ordinal)`` WITHIN-FILE natural key
    (P8b/F1) — never ``identity`` alone — so same-identity window siblings never
    collapse. A ``sub_ordinal`` of ``None`` marks a LEGACY chunk (a pre-F1
    snapshot entry that predates the disambiguator); :attr:`legacy` is derived
    from the presence of any such key, and drives the honest per-identity
    degradation in :meth:`DiffEngine._chunk_delta`. Deliberately NOT a pydantic
    model — a purely internal aggregate never crossing the public boundary.
    """

    __slots__ = ("sha512", "chunk_map", "legacy")

    def __init__(self, sha512: str, chunk_map: dict[tuple[str, int | None], str]) -> None:
        self.sha512 = sha512
        self.chunk_map = chunk_map
        # A pre-F1 entry stored no ``sub_ordinal`` (key component is ``None``);
        # its window siblings were already collapsed at write time.
        self.legacy = any(sub_ordinal is None for _identity, sub_ordinal in chunk_map)


# ---------------------------------------------------------------------------
# DiffEngine
# ---------------------------------------------------------------------------


class DiffEngine:
    """Read snapshot generations and report what changed between them.

    Owns its OWN lazily-opened, signed-in connection (mirroring
    :class:`~loremaster.index.snapshots.SnapshotStamper` /
    :class:`~loremaster.index.surreal_manifest.SurrealManifest`) for the
    ``snapshot`` / ``snapshot_entry`` read queries, and reads through the
    injected ``store`` / ``manifest`` collaborators (their OWN connections) for
    the live "now" state — never touching their connection state.

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
        store: The async :class:`~loremaster.store.surreal.SurrealStore` whose
            chunk rows back the live "now" state's per-file chunk identities.
        manifest: The async :class:`~loremaster.index.surreal_manifest.
            SurrealManifest` whose ``indexed`` rows drive the live "now" file set.
    """

    def __init__(
        self,
        *,
        url: str,
        namespace: str,
        database: str,
        user: str,
        password: str,
        store: SurrealStore,
        manifest: SurrealManifest,
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._store = store
        self._manifest = manifest
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set (mirrors every sibling port):
        # without it, N concurrent first-callers each open their OWN underlying
        # SDK connection. Safe to construct here (unbound to any running loop) on
        # Python >= 3.10.
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle (mirrors SnapshotStamper / SurrealManifest) ----

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking, identical to the sibling ports: the fast path
        (already connected) never touches the lock; a first caller acquires
        :attr:`_connect_lock` and re-checks. A down server or bad password is a
        LOUD, typed failure, never a hang.

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        if self._connection is not None:
            return self._connection
        async with self._connect_lock:
            if self._connection is not None:
                return self._connection  # type: ignore[unreachable]
            connection = AsyncSurreal(self._url)
            credentials: dict[str, Any] = {
                _SIGNIN_USER_KEY: self._user,
                _SIGNIN_PASS_KEY: self._password,
            }
            try:
                await connection.signin(credentials)
                await connection.query(f"DEFINE NAMESPACE IF NOT EXISTS {self._namespace}")
                await connection.use(self._namespace, self._database)
                await connection.query(f"DEFINE DATABASE IF NOT EXISTS {self._database}")
            except _CONNECTION_ERRORS as error:
                await self._safe_close(connection)
                raise SurrealConnectionError(
                    f"could not connect to SurrealDB at {self._url!r} "
                    f"(namespace={self._namespace!r}, database={self._database!r}): {error}"
                ) from error
            self._connection = connection
            logger.debug(
                "diff_engine.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect this engine's OWN connection — idempotent.

        No DDL of its own to apply: the ``snapshot`` / ``snapshot_entry`` tables
        are part of the full store schema every caller applies via
        ``SurrealStore.ensure_ready`` before constructing a :class:`DiffEngine`.
        A second call is a safe no-op (the fast path in
        :meth:`_ensure_connection`).

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._ensure_connection()
        logger.debug("diff_engine.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); safe to call more than once."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A COMPARE-AND-SWAP, not an unconditional null — mirrors every sibling
        port: ``self._connection`` is cleared only when ``connection`` IS STILL
        the currently cached handle, so a late caller holding a stale reference
        can never wipe out a freshly-reconnected handle.
        """
        if self._connection is connection:
            self._connection = None
        await self._safe_close(connection)

    @staticmethod
    async def _safe_close(connection: _SurrealConnection) -> None:
        """Close ``connection``, swallowing an already-dead-socket failure."""
        try:
            await connection.close()
        except _CONNECTION_ERRORS:
            logger.debug("diff_engine.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection.

        The engine's self-heal seam, mirroring :meth:`SnapshotStamper._query`: a
        transport/socket/auth failure drops the cached handle so the NEXT call
        transparently reconnects, surfaced as a typed, LOUD
        :class:`SurrealConnectionError`; a domain/schema rejection keeps the
        healthy connection and surfaces as :class:`SurrealStoreError`. A raw
        ``KeyError`` (the installed SDK's own response-routing fault on a socket
        drop mid-query) is ALWAYS classified as a connection fault.

        Message hygiene (ledger #31, mirroring ``execute_transaction`` and
        b262ab4's sibling seams): the raw engine text can echo a bound VALUE back
        verbatim and flows to MCP clients, so a domain rejection's FULL detail is
        logged server-side and the RAISED error carries only a CLASSIFIED,
        generic label plus a "see the server log" hint — never the raw text.
        """
        connection = await self._ensure_connection()
        try:
            return await connection.query(statement, params or {})
        except (*_CONNECTION_ERRORS, KeyError) as error:
            if isinstance(error, KeyError) or is_connection_error(error):
                await self._drop_connection(connection)
                raise SurrealConnectionError(
                    f"SurrealDB query failed against {self._url!r}: {error}"
                ) from error
            error_class = _classify_engine_error(error)
            logger.error(
                "diff.query.rejected",
                extra={"url": self._url, "error_class": error_class, "engine_error": str(error)},
            )
            raise SurrealStoreError(
                f"SurrealDB query rejected against {self._url!r} ({error_class}); "
                f"{_SERVER_LOG_HINT}"
            ) from error

    @staticmethod
    def _as_rows(result: Any) -> list[dict[str, Any]]:
        """Narrow a ``SELECT``-shaped result to its list of dict rows (mirrors
        :meth:`SurrealManifest._as_rows`)."""
        if not isinstance(result, list):
            return []
        return [row for row in result if isinstance(row, dict)]

    # -- listing --------------------------------------------------------

    async def list_snapshots(self, limit: int = _DEFAULT_LIST_LIMIT) -> list[SnapshotSummary]:
        """Return the newest ``limit`` snapshots, newest-first.

        Ordered by ``created_at`` DESCENDING, then ``id`` descending as a
        deterministic tie-breaker (two stamps within the same ``time::now()``
        tick would otherwise order arbitrarily). ``limit`` is a REQUIRED bound
        clamped to ``[_MIN_LIST_LIMIT, _MAX_LIST_LIMIT]`` (an out-of-range value
        is a best-effort request, never a hard error), emitted as a bound
        ``LIMIT`` param so the listing is never unbounded.

        Args:
            limit: The maximum number of summaries to return (clamped).

        Returns:
            The snapshot summaries, newest first; ``[]`` for an empty store —
            never an error.

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
        """
        clamped = max(_MIN_LIST_LIMIT, min(_MAX_LIST_LIMIT, limit))
        rows = self._as_rows(
            await self._query(
                f"SELECT * FROM {SNAPSHOT_TABLE} "
                f"ORDER BY created_at DESC, id DESC LIMIT ${_LIMIT_PARAM}",
                {_LIMIT_PARAM: clamped},
            )
        )
        return [self._row_to_summary(row) for row in rows]

    @staticmethod
    def _row_to_summary(row: dict[str, Any]) -> SnapshotSummary:
        """Decode one raw ``snapshot`` row into a :class:`SnapshotSummary`.

        ``created_at`` is converted from the stored native ``datetime`` to the
        ISO-8601 string the public contract carries (mirrors
        :meth:`SurrealManifest._row_to_model`'s ``updated_at`` handling).
        """
        created_at = row["created_at"]
        return SnapshotSummary(
            id=str(row["id"]),
            created_at=(
                created_at.isoformat() if isinstance(created_at, datetime) else str(created_at)
            ),
            git_ref=row.get("git_ref"),
            git_branch=row.get("git_branch"),
            files_total=row["files_total"],
            chunks_total=row["chunks_total"],
        )

    # -- diffing --------------------------------------------------------

    async def diff(self, since: str, until: str | None = None) -> DiffResult:
        """Report what changed FROM ``since`` TO ``until`` (or the live "now").

        Args:
            since: The base snapshot id (``"snapshot:sn<hex>"``), exactly as
                :meth:`~loremaster.index.snapshots.SnapshotStamper.stamp` /
                :meth:`list_snapshots` return it.
            until: The target snapshot id, or ``None`` for the CURRENT live state
                (the manifest's ``indexed`` rows + the store's chunk rows). When a
                snapshot id, both states come from ``snapshot_entry`` rows.

        Returns:
            The composed :class:`DiffResult`. ``since == until`` is a well-formed
            EMPTY diff; a reversed (``since`` newer than ``until``) order computes
            the literal reverse transition, NOT a reordered forward one.

        Raises:
            SnapshotNotFoundError: ``since`` or ``until`` is malformed or names no
                snapshot the store has ever recorded.
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: A read was rejected by the engine.
        """
        since_state = await self._snapshot_state(since)

        in_flight: list[InFlightFile] = []
        if until is None:
            until_state, changed_keys, in_flight = await self._live_state(since_state)
            until_label: str | None = None
        else:
            until_state = await self._snapshot_state(until)
            # Snapshot ↔ snapshot: every common file's chunk map is already in
            # hand, so function-level comparison runs for ALL common files — the
            # belt-and-braces same-sha-different-chunks case surfaces naturally.
            changed_keys = set(since_state) & set(until_state)
            until_label = until

        # A file mid-reindex (F2) is EXCLUDED from removed — it is transient, not
        # deleted. It is never in ``until_state`` (that holds only ``indexed``
        # rows), so added/modified already omit it; only ``removed`` (a base file
        # now absent from the live set) would otherwise mis-claim it.
        in_flight_keys = {(entry.tier, entry.file_path) for entry in in_flight}
        added = self._file_refs(set(until_state) - set(since_state))
        removed = self._file_refs((set(since_state) - set(until_state)) - in_flight_keys)
        modified = self._file_refs(
            key
            for key in (set(since_state) & set(until_state))
            if since_state[key].sha512 != until_state[key].sha512
        )
        function_deltas, legacy_keys = self._function_deltas(
            since_state, until_state, changed_keys
        )

        return DiffResult(
            since=since,
            until=until_label,
            added=added,
            removed=removed,
            modified=modified,
            function_deltas=function_deltas,
            in_flight=in_flight,
            legacy_files=self._file_refs(legacy_keys),
        )

    async def _snapshot_state(self, snapshot_id: str) -> dict[tuple[str, str], _FileState]:
        """Load one snapshot generation's per-file diffable state.

        Verifies the snapshot row EXISTS first (a valid snapshot may legitimately
        have zero entries, so entry-presence alone cannot prove existence), then
        reads its ``snapshot_entry`` rows into ``{(tier, file_path): _FileState}``.

        Raises:
            SnapshotNotFoundError: ``snapshot_id`` is malformed or names no
                ``snapshot`` row.
        """
        record_id = self._parse_snapshot_id(snapshot_id)
        existing = self._as_rows(
            await self._query(
                f"SELECT id FROM {SNAPSHOT_TABLE} WHERE id = $snapshot_id",
                {"snapshot_id": record_id},
            )
        )
        if not existing:
            raise SnapshotNotFoundError(
                f"no snapshot {snapshot_id!r} exists (never stamped, or already "
                f"deleted). Next step: call list_snapshots() to see the real ids."
            )
        entry_rows = self._as_rows(
            await self._query(
                f"SELECT tier, file_path, sha512, chunk_hashes FROM {SNAPSHOT_ENTRY_TABLE} "
                f"WHERE snapshot = $snapshot_id",
                {"snapshot_id": record_id},
            )
        )
        return {
            (row["tier"], row["file_path"]): _FileState(
                sha512=row["sha512"], chunk_map=self._chunk_map_from_entry(row.get("chunk_hashes"))
            )
            for row in entry_rows
        }

    @staticmethod
    def _parse_snapshot_id(snapshot_id: str) -> RecordID:
        """Parse a snapshot id string into a :class:`RecordID`.

        A malformed id (the SDK cannot parse it) is folded into the SAME clean
        :class:`SnapshotNotFoundError` family as a well-formed-but-unknown id, so
        a raw ``surrealdb.errors.InvalidRecordIdError`` never escapes to a caller.

        Raises:
            SnapshotNotFoundError: ``snapshot_id`` is not a parseable record id.
        """
        try:
            return RecordID.parse(snapshot_id)
        except InvalidRecordIdError as error:
            raise SnapshotNotFoundError(
                f"{snapshot_id!r} is not a valid snapshot id. Next step: call "
                f"list_snapshots() to see the real ids."
            ) from error

    @staticmethod
    def _chunk_map_from_entry(chunk_hashes: Any) -> dict[tuple[str, int | None], str]:
        """Build a ``{(identity, sub_ordinal): hash}`` map from a
        ``snapshot_entry.chunk_hashes`` list (tolerant of a missing/empty list).

        The composite ``(identity, sub_ordinal)`` key is what keeps same-identity
        window siblings distinct (P8b/F1). A LEGACY entry (a pre-F1 snapshot whose
        objects carry no ``sub_ordinal``) yields keys with ``sub_ordinal=None``,
        which :class:`_FileState` reads as ``legacy`` and
        :meth:`_chunk_delta` degrades to per-identity comparison — never a silent
        pretend-precision, and never a crash. A modern entry yields real int
        ``sub_ordinal``s. Malformed items (missing ``identity``/``hash``) are
        skipped."""
        if not isinstance(chunk_hashes, list):
            return {}
        result: dict[tuple[str, int | None], str] = {}
        for item in chunk_hashes:
            if not (isinstance(item, dict) and "identity" in item and "hash" in item):
                continue
            # ``.get`` — ``None`` for a legacy (pre-``sub_ordinal``) object.
            result[(item["identity"], item.get("sub_ordinal"))] = item["hash"]
        return result

    async def _live_state(
        self, since_state: dict[tuple[str, str], _FileState]
    ) -> tuple[
        dict[tuple[str, str], _FileState], set[tuple[str, str]], list[InFlightFile]
    ]:
        """Build the live "now" state, the files to chunk-compare, and the
        in-flight set.

        File-level state comes from the manifest's currently-``indexed`` rows. A
        row in ANY other state (``dirty``/``embedding``/``failed``) is mid-reindex,
        NOT deleted — it is collected into ``in_flight`` and EXCLUDED from the
        comparison (P8b/F2), so it can never silently vanish from the live set and
        be mis-reported as a removal.

        Chunk identities are read from the store ONLY for files whose ``sha512``
        changed relative to ``since_state`` — see the module docstring's
        ``until=None`` caveat: this skip is a SAME-CHUNKER invariant (a fixed byte
        stream re-chunks identically), traded for read efficiency; a chunker
        upgrade breaks it, and snapshot↔snapshot stays the fidelity path.

        Returns:
            ``(live_state, changed_keys, in_flight)`` where ``changed_keys`` is
            exactly the common files whose ``sha512`` differs (the ONLY files
            whose live chunk map was read), and ``in_flight`` names the excluded
            mid-reindex files with their transient states.
        """
        all_rows = await self._manifest.all_files()
        indexed_rows = [row for row in all_rows if row.state == STATE_INDEXED]
        in_flight = sorted(
            (
                InFlightFile(tier=row.tier, file_path=row.file_path, state=row.state)
                for row in all_rows
                if row.state != STATE_INDEXED
            ),
            key=lambda entry: (entry.tier, entry.file_path),
        )
        live_shas = {(row.tier, row.file_path): row.sha512 for row in indexed_rows}
        changed_keys = {
            key
            for key, sha512 in live_shas.items()
            if key in since_state and since_state[key].sha512 != sha512
        }
        live_state: dict[tuple[str, str], _FileState] = {}
        for key, sha512 in live_shas.items():
            chunk_map: dict[tuple[str, int | None], str] = (
                await self._live_chunk_map(key[0], key[1]) if key in changed_keys else {}
            )
            live_state[key] = _FileState(sha512=sha512, chunk_map=chunk_map)
        return live_state, changed_keys, in_flight

    async def _live_chunk_map(
        self, tier: str, file_path: str
    ) -> dict[tuple[str, int | None], str]:
        """Read one file's live ``{(identity, sub_ordinal): content_hash}`` map
        from the store.

        Keyed on the ``(identity, sub_ordinal)`` natural key (P8b/F1) so a live
        file's window siblings stay distinct. The live side is ALWAYS modern (the
        ``chunk`` table carries a first-class ``sub_ordinal`` column), so these
        keys never carry a legacy ``None``. Bounded by
        :data:`_MAX_CHUNKS_PER_FILE` (a scroll is never unbounded); hitting the
        cap EXACTLY is a possible-truncation signal, surfaced as a WARNING naming
        the file rather than trusting a maybe-partial map (mirrors
        :meth:`SnapshotStamper.stamp`).
        """
        chunk_rows = await self._store.scroll(
            {"tier": tier, "file_path": file_path}, limit=_MAX_CHUNKS_PER_FILE
        )
        if len(chunk_rows) == _MAX_CHUNKS_PER_FILE:
            logger.warning(
                "diff.chunk_scroll_truncated",
                extra={"tier": tier, "file_path": file_path, "limit": _MAX_CHUNKS_PER_FILE},
            )
        return {(row["identity"], row["sub_ordinal"]): row["content_hash"] for row in chunk_rows}

    @staticmethod
    def _file_refs(keys: Any) -> list[FileRef]:
        """Sorted :class:`FileRef` list from an iterable of ``(tier, file_path)``."""
        return [FileRef(tier=tier, file_path=file_path) for tier, file_path in sorted(keys)]

    @classmethod
    def _function_deltas(
        cls,
        since_state: dict[tuple[str, str], _FileState],
        until_state: dict[tuple[str, str], _FileState],
        changed_keys: set[tuple[str, str]],
    ) -> tuple[list[FunctionDelta], set[tuple[str, str]]]:
        """Per-file chunk deltas over ``changed_keys`` (sorted; a file appears iff
        it has ANY add / remove / change), plus the set of files whose comparison
        was DEGRADED because a compared side is legacy (pre-``sub_ordinal``).

        The legacy set is returned INDEPENDENTLY of whether a delta surfaced, so a
        degraded-but-unchanged file is still flagged (serve-and-say-so): the
        precision loss is visible even when the per-identity view found no drift.
        """
        deltas: list[FunctionDelta] = []
        legacy_keys: set[tuple[str, str]] = set()
        for key in sorted(changed_keys):
            tier, file_path = key
            since_file = since_state.get(key)
            until_file = until_state.get(key)
            if (since_file is not None and since_file.legacy) or (
                until_file is not None and until_file.legacy
            ):
                legacy_keys.add(key)
            delta = cls._chunk_delta(
                tier,
                file_path,
                since_file.chunk_map if since_file is not None else {},
                until_file.chunk_map if until_file is not None else {},
            )
            if delta is not None:
                deltas.append(delta)
        return deltas, legacy_keys

    @classmethod
    def _chunk_delta(
        cls,
        tier: str,
        file_path: str,
        since_map: dict[tuple[str, int | None], str],
        until_map: dict[tuple[str, int | None], str],
    ) -> FunctionDelta | None:
        """Compare two ``(identity, sub_ordinal)`` → hash maps, or ``None`` if
        identical.

        Modern path: compare on the composite key, so same-identity WINDOW
        siblings never collapse; an identity carrying more than one window is
        rendered per-window with a ``<identity> [window N]`` marker (a
        single-window identity stays a plain identity, keeping the common case
        legible). Legacy path: if EITHER side predates ``sub_ordinal``
        (:meth:`_is_legacy`), the window information is unrecoverable, so BOTH
        sides are collapsed to identity-level and compared per-identity — an
        honest degradation, flagged via ``legacy=True`` (and, at the caller,
        ``DiffResult.legacy_files``), never a silent pretend-precision. A renamed
        identity is NOT reconciled — it reads as one removed + one added.
        """
        legacy = cls._is_legacy(since_map) or cls._is_legacy(until_map)
        if legacy:
            since_by_identity = cls._collapse_to_identity(since_map)
            until_by_identity = cls._collapse_to_identity(until_map)
            added = sorted(set(until_by_identity) - set(since_by_identity))
            removed = sorted(set(since_by_identity) - set(until_by_identity))
            changed = sorted(
                identity
                for identity in (set(since_by_identity) & set(until_by_identity))
                if since_by_identity[identity] != until_by_identity[identity]
            )
        else:
            windowed = cls._windowed_identities(since_map, until_map)
            added = sorted(
                cls._display_key(key, windowed) for key in (set(until_map) - set(since_map))
            )
            removed = sorted(
                cls._display_key(key, windowed) for key in (set(since_map) - set(until_map))
            )
            changed = sorted(
                cls._display_key(key, windowed)
                for key in (set(since_map) & set(until_map))
                if since_map[key] != until_map[key]
            )
        if not (added or removed or changed):
            return None
        return FunctionDelta(
            tier=tier,
            file_path=file_path,
            added=added,
            removed=removed,
            changed=changed,
            legacy=legacy,
        )

    @staticmethod
    def _is_legacy(chunk_map: dict[tuple[str, int | None], str]) -> bool:
        """``True`` iff any key lacks a real ``sub_ordinal`` (a pre-F1 entry)."""
        return any(sub_ordinal is None for _identity, sub_ordinal in chunk_map)

    @staticmethod
    def _collapse_to_identity(
        chunk_map: dict[tuple[str, int | None], str],
    ) -> dict[str, str]:
        """Fold a composite-keyed map down to ``{identity: hash}`` for a legacy
        (degraded) comparison — deterministic last-write-wins by ascending
        ``sub_ordinal`` (``None`` sorts first). Precision is knowingly lost: a
        legacy side was ALREADY collapsed at write time, and a modern side must
        meet it at the same identity-level granularity."""
        collapsed: dict[str, str] = {}
        for (identity, sub_ordinal), digest in sorted(
            chunk_map.items(), key=lambda item: (item[0][0], item[0][1] is not None, item[0][1])
        ):
            collapsed[identity] = digest
        return collapsed

    @staticmethod
    def _windowed_identities(
        since_map: dict[tuple[str, int | None], str],
        until_map: dict[tuple[str, int | None], str],
    ) -> set[str]:
        """The identities that carry MORE THAN ONE window across both sides — the
        ones whose deltas need a ``[window N]`` marker to stay unambiguous. A
        single-window identity is left as a plain identity so the common case
        never grows a marker."""
        sub_ordinals_by_identity: dict[str, set[int | None]] = {}
        for identity, sub_ordinal in set(since_map) | set(until_map):
            sub_ordinals_by_identity.setdefault(identity, set()).add(sub_ordinal)
        return {
            identity
            for identity, sub_ordinals in sub_ordinals_by_identity.items()
            if len(sub_ordinals) > 1
        }

    @staticmethod
    def _display_key(key: tuple[str, int | None], windowed: set[str]) -> str:
        """Render one composite key as a human display string: a plain identity
        for a single-window identity, or ``<identity> [window N]`` for one that
        has sibling windows (so a within-window change names WHICH window)."""
        identity, sub_ordinal = key
        if identity in windowed:
            return f"{identity} [window {sub_ordinal}]"
        return identity
