"""Snapshot stamping (P5-C4, ledger #25) — full-project index generation markers.

Versioning is first-class in v1.0: a ``snapshot`` row is a full-project index
GENERATION marker, and its ``snapshot_entry`` children are the per-file
digest/chunk-identity ledger that later powers ``lore_diff`` and a
``changed_since`` query. The DDL for both tables landed in P5-C1b
(:func:`~loremaster.store.surreal_schema._snapshot_statements` /
:func:`~loremaster.store.surreal_schema._snapshot_entry_statements`, part of
the full :func:`~loremaster.store.surreal_schema.generate_ddl` schema every
:class:`~loremaster.store.surreal.SurrealStore` applies via ``ensure_ready``).
This module is the WRITER layer above that schema: it decides what a
snapshot row/entry set actually contains and builds it on demand.

Two independent pieces:

* :func:`capture_git_identity` — a pure, never-raising helper that reads
  ``(git_ref, git_branch)`` from a project root's OWN git state via a
  subprocess ``git`` invocation rooted at that path (``git -C <root> ...``,
  never the caller's cwd).
* :class:`SnapshotStamper` — owns its OWN SurrealDB connection (mirroring
  :class:`~loremaster.store.surreal.SurrealStore` /
  :class:`~loremaster.index.surreal_manifest.SurrealManifest` /
  :class:`~loremaster.graph_surreal.SurrealCodeGraph`'s identical
  connect-lock + CAS-drop + ``KeyError``-classification self-heal idiom),
  and reads the ``store``/``manifest`` collaborators it is constructed with
  to build a snapshot. ``stamp()`` is UNCONDITIONAL — it does not decide
  "should I stamp right now"; that gate (full sweep success, sweep did
  something) is the CALLER's job (see the indexer/reconcile wiring in
  ``index/indexer.py`` / ``index/reconcile.py``, pinned by
  ``test_indexer_snapshot_wiring.py``).

Schema-ownership note: unlike :class:`~loremaster.index.surreal_manifest.
SurrealManifest` (its own ``file``/``meta`` DDL slice) and
:class:`~loremaster.graph_surreal.SurrealCodeGraph` (its own S13 Model-A DDL
slice), the ``snapshot``/``snapshot_entry`` tables are NOT a separate schema
slice — they are part of the ONE full :func:`~loremaster.store.surreal_schema.
generate_ddl` schema :class:`~loremaster.store.surreal.SurrealStore.
ensure_ready` already applies. Every caller (both this module's own tests and
the indexer/reconcile wiring) constructs and readies a :class:`SurrealStore`
before a :class:`SnapshotStamper`, so :meth:`SnapshotStamper.ensure_ready`
only needs to establish ITS OWN connection — there is no second DDL
application to own.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import uuid
from pathlib import Path
from typing import Any

from surrealdb import AsyncSurreal, InvalidRecordIdError, RecordID

from loremaster.index.surreal_manifest import STATE_INDEXED, SurrealManifest
from loremaster.store._txn import (
    _CONNECTION_ERRORS,
    TxnFragment,
    compose,
    execute_transaction,
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
# capture_git_identity
# ---------------------------------------------------------------------------

# git's own literal sentinel for "no real branch" (a detached HEAD). This
# module's OWN design decision (not git's) is to map that sentinel to
# ``None`` rather than let it leak through as a fake branch name.
_DETACHED_HEAD_SENTINEL = "HEAD"

# A generous bound on how long one ``git`` subprocess call may run — defends
# against a wedged/hung git process (e.g. a corrupt repo prompting for input)
# from blocking a stamp indefinitely; every real invocation here is a cheap
# local metadata read that completes in milliseconds.
_GIT_SUBPROCESS_TIMEOUT_S = 10


def _run_git_rev_parse(repo_root: Path, *args: str) -> str | None:
    """Run ``git -C <repo_root> rev-parse <args>``, returning stripped stdout.

    NEVER raises: a missing ``git`` binary, a nonexistent/non-directory
    ``repo_root``, a non-git directory, or a git subprocess failure all
    collapse to ``None`` — the caller decides what that means. ``-C`` (not a
    ``cwd=`` kwarg) is git's OWN "run rooted at this directory" flag, so a
    bad path is git's error to report (a clean non-zero exit), never a raw
    Python ``OSError`` escaping this helper.

    Args:
        repo_root: The directory to root the git invocation at.
        args: The ``rev-parse`` arguments (e.g. ``"HEAD"``).

    Returns:
        The stripped stdout, or ``None`` if the invocation failed or the
        binary is missing, or produced empty output.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", *args],
            capture_output=True,
            text=True,
            check=False,
            timeout=_GIT_SUBPROCESS_TIMEOUT_S,
        )
    except (OSError, subprocess.SubprocessError):
        # A missing ``git`` binary, a permission fault, or a timeout — never
        # let a subprocess-launch failure propagate out of this helper.
        return None
    if result.returncode != 0:
        return None
    output = result.stdout.strip()
    return output or None


def capture_git_identity(repo_root: Path) -> tuple[str | None, str | None]:
    """Read ``(git_ref, git_branch)`` from ``repo_root``'s OWN git state.

    ``git_ref`` is the full, un-abbreviated commit sha (never ``--short``);
    ``git_branch`` is the branch name, or ``None`` for a detached HEAD (git's
    own ``"HEAD"`` sentinel is deliberately mapped away — see
    :data:`_DETACHED_HEAD_SENTINEL`). ``(None, None)`` for a non-git,
    nonexistent, or non-directory ``repo_root`` — never raises.

    Args:
        repo_root: The project root whose OWN git state to read (rooted via
            ``git -C``, never the caller's process cwd).

    Returns:
        ``(git_ref, git_branch)``, either or both ``None`` when unavailable.
    """
    git_ref = _run_git_rev_parse(repo_root, "HEAD")
    if git_ref is None:
        return None, None
    branch = _run_git_rev_parse(repo_root, "--abbrev-ref", "HEAD")
    if branch is None or branch == _DETACHED_HEAD_SENTINEL:
        branch = None
    return git_ref, branch


# ---------------------------------------------------------------------------
# SnapshotStamper
# ---------------------------------------------------------------------------

# A defensive bound on how many chunk rows a single file's fidelity read may
# pull from the store (see :meth:`SurrealStore.scroll`, whose ``limit`` is a
# REQUIRED bound — a read is never unbounded). Real files sit far below this;
# it exists to cap one pathological file rather than to reflect a realistic
# chunk count. Hitting the cap EXACTLY is itself a signal worth a WARNING
# (see :meth:`SnapshotStamper.stamp`) — the read may have silently truncated
# a pathological file's real chunk count down to this ceiling.
_MAX_CHUNKS_PER_FILE = 50_000

# The client-generated snapshot record id's alpha tag. A stamp's snapshot row
# needs a KNOWN id BEFORE the transaction runs (every entry's ``snapshot``
# link is built from it) — this prefix, not the engine's own auto-id, is what
# makes that possible. Guarantees ``RecordID.__str__`` never needs to escape
# the identifier (see ``RecordID._escape_identifier``: a bare hex string
# could — vanishingly rarely — contain zero alphabetic characters and be
# escaped as "looks numeric"; a fixed alpha prefix rules that out entirely),
# so :meth:`stamp`'s returned id string round-trips cleanly through
# :meth:`delete_snapshot`'s ``RecordID.parse``.
_SNAPSHOT_ID_PREFIX = "sn"

# The composed-transaction fragment's param-name prefix (mirrors
# ``CHUNK_FRAGMENT_PARAM_PREFIX`` / ``FILE_TEXT_FRAGMENT_PARAM_PREFIX`` in
# ``store/surreal.py``) — distinct from every other producer's prefix so a
# stamp fragment could, in principle, be composed alongside another
# producer's fragment without a param collision.
_SNAPSHOT_FRAGMENT_PARAM_PREFIX = "sn_"


class SnapshotStamper:
    """Writes ``snapshot`` + ``snapshot_entry`` rows over a per-project database.

    Owns its OWN lazily-opened, signed-in connection (mirroring
    :class:`~loremaster.index.surreal_manifest.SurrealManifest` /
    :class:`~loremaster.graph_surreal.SurrealCodeGraph`) for the
    ``CREATE``/``DELETE`` writes below, and reads through the injected
    ``store``/``manifest`` collaborators (their OWN connections) to gather
    what a snapshot should contain — never touching their connection state.

    Args:
        url: The SurrealDB RPC URL (e.g. ``ws://127.0.0.1:18000/rpc``).
        namespace: The namespace the database lives under.
        database: The per-project database name.
        user: The root/username to sign in with.
        password: The password to sign in with.
        store: The async :class:`~loremaster.store.surreal.SurrealStore`
            whose chunk rows back each entry's ``chunk_hashes`` fidelity.
        manifest: The async :class:`~loremaster.index.surreal_manifest.
            SurrealManifest` whose ``indexed`` rows drive the file set.
        project_root: The on-disk project root :func:`capture_git_identity`
            reads git state from.
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
        project_root: Path,
    ) -> None:
        self._url = url
        self._namespace = namespace
        self._database = database
        self._user = user
        self._password = password
        self._store = store
        self._manifest = manifest
        self._project_root = project_root
        # Opened on first use; ``None`` means "not yet connected / closed".
        self._connection: _SurrealConnection | None = None
        # Guards the connect-time check-then-set below (mirrors
        # ``SurrealManifest._connect_lock`` / ``SurrealCodeGraph._connect_lock``):
        # without it, N concurrent first-callers on a fresh instance all pass
        # the ``self._connection is not None`` check before any of them
        # finishes connecting, each opening its OWN underlying SDK connection.
        # Safe to construct here (unbound to any running loop) on Python
        # >= 3.10.
        self._connect_lock = asyncio.Lock()

    # -- connection lifecycle (mirrors SurrealManifest / SurrealCodeGraph) --

    async def _ensure_connection(self) -> _SurrealConnection:
        """Return the live connection, opening + signing in on first use.

        Double-checked locking, identical to the sibling ports: the fast path
        (already connected) never touches the lock; a first caller acquires
        :attr:`_connect_lock` and re-checks. A down server or bad password is
        a LOUD, typed failure, never a hang or a silently empty stamp.

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
                "snapshot_stamper.connected",
                extra={"namespace": self._namespace, "database": self._database},
            )
            return connection

    async def ensure_ready(self) -> None:
        """Connect this stamper's OWN connection — idempotent.

        No DDL of its own to apply (see the module docstring): the
        ``snapshot``/``snapshot_entry`` tables are part of the full store
        schema, which every caller applies via ``SurrealStore.ensure_ready``
        before constructing a :class:`SnapshotStamper`. A second call is a
        safe no-op (the fast path in :meth:`_ensure_connection`).

        Raises:
            SurrealConnectionError: The server is unreachable or rejected auth.
        """
        await self._ensure_connection()
        logger.debug("snapshot_stamper.ready", extra={"database": self._database})

    async def close(self) -> None:
        """Close the live connection (if any); safe to call more than once."""
        if self._connection is not None:
            await self._safe_close(self._connection)
            self._connection = None

    async def _drop_connection(self, connection: _SurrealConnection) -> None:
        """Drop the cached handle so the NEXT call reconnects (the self-heal).

        A COMPARE-AND-SWAP, not an unconditional null — mirrors
        :meth:`SurrealManifest._drop_connection` exactly: ``self._connection``
        is cleared only when ``connection`` IS STILL the currently cached
        handle, so a late caller holding a stale reference can never wipe out
        a freshly-reconnected handle out from under an in-flight caller.
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
            logger.debug("snapshot_stamper.close.already_closed")

    async def _query(self, statement: str, params: dict[str, Any] | None = None) -> Any:
        """Run a single statement on the (lazily opened) connection.

        The stamper's self-heal seam, mirroring :meth:`SurrealManifest._query`
        / :meth:`SurrealCodeGraph._query`: a transport/socket/auth failure
        drops the cached handle so the NEXT call transparently reconnects,
        surfaced as a typed, LOUD :class:`SurrealConnectionError`; a
        domain/schema rejection keeps the healthy connection and surfaces as
        :class:`SurrealStoreError`. A raw ``KeyError`` (the installed SDK's
        own response-routing fault on a socket drop mid-query — probe-verified
        on the sibling ports) is ALWAYS classified as a connection fault.
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
            raise SurrealStoreError(
                f"SurrealDB query rejected against {self._url!r}: {error}"
            ) from error

    # -- stamping -------------------------------------------------------

    async def stamp(self) -> str:
        """Write ONE new ``snapshot`` row + its ``snapshot_entry`` children,
        ATOMICALLY (P5-C4 hardening #3: composed as ONE transaction).

        Reads EVERY currently-``indexed`` row from ``manifest``, captures git
        identity from ``project_root``, and for each indexed
        ``(tier, file_path)`` reads that file's REAL chunk rows from ``store``
        (identity + content_hash) to build ``chunk_hashes``. UNCONDITIONAL —
        this method itself does not decide "should I stamp right now"; a
        manifest with zero indexed rows still produces a well-formed,
        zero-total, zero-entry snapshot rather than raising.

        The parent row's id is generated CLIENT-SIDE (see
        :data:`_SNAPSHOT_ID_PREFIX`) rather than read back from the engine's
        own auto-id — that is what lets every entry's ``snapshot`` link be
        built BEFORE anything is sent to the server, so the parent row and
        every child entry compose into a SINGLE ``BEGIN … COMMIT`` (see
        :meth:`_stamp_fragment`) run through the shared
        :func:`~loremaster.store._txn.execute_transaction`. A mid-stamp
        connection drop or ANY entry's rejection rolls the WHOLE stamp back —
        never an orphan snapshot row with only some of its entries.

        Returns:
            The new snapshot's stringified record id (e.g. ``"snapshot:abc123"``).

        Raises:
            SurrealConnectionError: The server is unreachable or the socket died.
            SurrealStoreError: The write was rejected by the engine (nothing
                is left half-applied).
        """
        indexed_rows = [
            row for row in await self._manifest.all_files() if row.state == STATE_INDEXED
        ]
        git_ref, git_branch = capture_git_identity(self._project_root)

        entries: list[dict[str, Any]] = []
        chunks_total = 0
        for row in indexed_rows:
            chunk_rows = await self._store.scroll(
                {"tier": row.tier, "file_path": row.file_path}, limit=_MAX_CHUNKS_PER_FILE
            )
            if len(chunk_rows) == _MAX_CHUNKS_PER_FILE:
                # Hitting the cap EXACTLY means the read may have silently
                # truncated this file's real chunk count — surfaced loudly so
                # an operator can investigate, rather than trusting a
                # possibly-partial chunk_hashes list.
                logger.warning(
                    "snapshot.chunk_scroll_truncated",
                    extra={
                        "tier": row.tier,
                        "file_path": row.file_path,
                        "limit": _MAX_CHUNKS_PER_FILE,
                    },
                )
            chunk_hashes = [
                {"identity": chunk_row["identity"], "hash": chunk_row["content_hash"]}
                for chunk_row in chunk_rows
            ]
            chunks_total += len(chunk_hashes)
            entries.append(
                {
                    "tier": row.tier,
                    "file_path": row.file_path,
                    "sha512": row.sha512,
                    "chunk_hashes": chunk_hashes,
                }
            )

        snapshot_content: dict[str, Any] = {
            "git_ref": git_ref,
            "git_branch": git_branch,
            "files_total": len(indexed_rows),
            "chunks_total": chunks_total,
        }
        snapshot_record_id = RecordID(
            SNAPSHOT_TABLE, f"{_SNAPSHOT_ID_PREFIX}{uuid.uuid4().hex}"
        )
        fragment = self._stamp_fragment(snapshot_record_id, snapshot_content, entries)
        statement_text, merged_params = compose(fragment)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )
        return str(snapshot_record_id)

    def _stamp_fragment(
        self,
        snapshot_record_id: RecordID,
        snapshot_content: dict[str, Any],
        entries: list[dict[str, Any]],
    ) -> TxnFragment:
        """Build the ONE composable fragment for a full stamp.

        A PURE builder (no I/O): the snapshot row's ``CREATE`` and every
        entry's ``CREATE`` are emitted as sibling statements bound to
        namespaced params (:data:`_SNAPSHOT_FRAGMENT_PARAM_PREFIX`), so
        :func:`~loremaster.store._txn.compose` merges them into ONE
        ``BEGIN … COMMIT`` — the parent snapshot row and every per-file entry
        land, or roll back, together. Mirrors the ``type::record(table, $id)``
        idiom every other producer in ``store/surreal.py`` uses for a
        client-known id.

        Args:
            snapshot_record_id: The client-generated parent record id (see
                :meth:`stamp`).
            snapshot_content: The parent row's field payload.
            entries: The per-file entry payloads (``snapshot`` NOT yet set —
                :meth:`_entry_content` adds that link).

        Returns:
            The stamp's single :class:`~loremaster.store._txn.TxnFragment`.
        """
        prefix = _SNAPSHOT_FRAGMENT_PARAM_PREFIX
        snapshot_key_param = f"{prefix}snapshot_key"
        snapshot_content_param = f"{prefix}snapshot_content"
        params: dict[str, Any] = {
            snapshot_key_param: snapshot_record_id.id,
            snapshot_content_param: snapshot_content,
        }
        statements = [
            f"CREATE type::record('{SNAPSHOT_TABLE}', ${snapshot_key_param}) "
            f"CONTENT ${snapshot_content_param}"
        ]
        for index, entry in enumerate(entries):
            entry_content_param = f"{prefix}entry_content{index}"
            params[entry_content_param] = self._entry_content(entry, snapshot_record_id)
            statements.append(
                f"CREATE {SNAPSHOT_ENTRY_TABLE} CONTENT ${entry_content_param}"
            )
        return TxnFragment(statements=statements, params=params)

    @staticmethod
    def _entry_content(entry: dict[str, Any], snapshot_record_id: RecordID) -> dict[str, Any]:
        """Build one ``snapshot_entry``'s CONTENT dict, linked to its parent.

        The ONLY place a single entry's content is assembled — small and
        separately testable (see ``test_snapshots.py::
        TestStampIsOneAtomicTransaction``, which splices an unrelated poison
        statement into the SAME composed transaction to prove a later
        rejection rolls back everything, not just itself).
        """
        return {**entry, "snapshot": snapshot_record_id}

    async def delete_snapshot(self, snapshot_id: str) -> None:
        """Delete the ``snapshot`` row AND every ``snapshot_entry`` referencing it.

        Record links do NOT auto-clean on delete (docs-audit constraint), so
        the entries are deleted explicitly, scoped to ``snapshot_id`` — a
        sibling snapshot's row and entries are untouched. Idempotent: an
        unknown or malformed ``snapshot_id`` is a no-op, never an error.

        Args:
            snapshot_id: The stringified snapshot record id (as returned by
                :meth:`stamp`).
        """
        try:
            record_id = RecordID.parse(snapshot_id)
        except InvalidRecordIdError:
            # A malformed id names nothing to delete — idempotent no-op, not
            # a caller-facing error (a GC sweep may race a concurrent delete).
            return
        # ORDERING IS LOAD-BEARING: children before the parent row. Record
        # links do NOT auto-clean on delete (docs-audit constraint), so if the
        # parent were deleted FIRST and this call crashed/dropped mid-way, the
        # entries would be ORPHANED with no ``snapshot`` row left to filter by
        # — invisible to any future GC sweep. Deleting entries first means a
        # crash between the two statements leaves, at worst, a parentless
        # snapshot row whose entries are ALREADY gone — a state a RETRY of
        # this same idempotent call (or a future GC sweep keyed on the row)
        # can still clean up correctly.
        await self._query(
            f"DELETE {SNAPSHOT_ENTRY_TABLE} WHERE snapshot = $snapshot_id",
            {"snapshot_id": record_id},
        )
        await self._query("DELETE $snapshot_id", {"snapshot_id": record_id})
