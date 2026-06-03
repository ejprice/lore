"""Resilient SQLite open — the shared building block for FP-01 + FP-08.

Both local DBs (the :class:`~loremaster.index.manifest.Manifest` and the
:class:`~loremaster.graph.CodeGraph`) open a real file-backed SQLite database at
construction. Two production failure modes wedge a bare ``sqlite3.connect``:

* **FP-01 — absent parent dir.** On a clean container the state volume is empty,
  so the directory holding ``<slug>.db`` does not exist. ``sqlite3.connect``
  cannot create a parent directory, so it raises
  ``OperationalError: unable to open database file`` and the server can never
  start on a clean volume.

* **FP-08 — corrupt existing file.** A torn write / partial fsync (a volume that
  lost power) leaves a NON-EMPTY malformed image on disk. The first statement on
  it raises ``DatabaseError: file is not a database`` and every restart
  re-wedges until a human deletes the file.

Both DBs are fully rebuildable (a fresh empty manifest triggers a reindex; a
fresh graph is rebuilt by reindex), so the correct recovery for a corrupt image
is delete-and-recreate. A VALID database — including a zero-byte file SQLite
treats as valid-and-fresh — must open UNCHANGED; the recovery path must never
nuke a healthy database.

:func:`open_resilient_sqlite` is the single source of truth for that open: it
materialises the parent dir (owner-only — the state dir holds the plaintext
memory ledger), connects, probes integrity, and on a malformed image deletes the
file (with its WAL sidecars) and recreates a fresh empty DB. Both DB
constructors call it instead of a bare ``sqlite3.connect`` so the logic lives in
exactly one place.

**Owner-only on disk (defense-in-depth).** The state dir holds the manifest AND
the plaintext memory ledger ``<slug>.memory.db`` (user-authored memory TEXT), so
neither the directory nor the database file may be group/world-readable:

* Every directory the open CREATES is mode ``0o700``. The mkdir runs under a
  tightly-scoped ``os.umask(0o077)`` so a newly-created dir/file is owner-only
  ATOMICALLY — closing the brief world-readable window between ``mkdir`` and the
  explicit ``os.chmod`` (the TOCTOU the audit flagged). The explicit chmod is
  KEPT as the deterministic, umask-independent guarantee; the umask just removes
  the transient window. An already-existing dir is left untouched.
* The database FILE is ``chmod`` 0o600 on EVERY open. ``sqlite3.connect`` creates
  a new file at ``0o666 & ~umask`` (== 0o644, world-readable), and a file written
  by a prior default-mode build stays 0o644 forever. Chmodding on every open both
  sets a freshly-created file owner-only AND retro-tightens an inherited
  world-readable file from an older deploy — WHY: the plaintext memory ledger /
  manifest must never be readable by other local users, and the dir mode is the
  only other protection (a shared mount / inherited dir loosens it).
"""

from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# The single row a healthy ``PRAGMA integrity_check`` returns. SQLite reports a
# clean database — including a freshly created empty one and a zero-byte file it
# initialises in place — as exactly this one-row, one-column result. Anything
# else (or a raised ``DatabaseError`` probing it) means a malformed image.
_INTEGRITY_CHECK_OK: str = "ok"

# The SQLite write-ahead-log sidecar suffixes that live beside ``<path>`` for a
# WAL-mode database. They must be removed together with the main file when a
# corrupt image is deleted, or stale sidecars would corrupt the recreated DB.
_WAL_SIDECAR_SUFFIXES: tuple[str, ...] = ("-wal", "-shm")

# Owner-only (rwx for the owner, nothing for group/other) permission bits for a
# state directory the open CREATES. The state dir holds the manifest AND the
# memory ledger ``<slug>.memory.db`` — a plaintext SQLite file containing
# user-authored memory text — so a created dir must NOT be group/world-readable
# (the default 0o755 under a 022 umask is an information-disclosure hole). Only
# dirs the open brings into being are tightened; an already-existing dir is left
# at its current mode (re-permissioning an inherited/shared mount is out of
# scope and would silently re-tighten an operator's deliberate sharing).
_OWNER_ONLY_DIR_MODE: int = 0o700

# Owner-only (rw for the owner, nothing for group/other) permission bits for the
# database FILE the open creates or opens. ``sqlite3.connect`` creates a new file
# world-readable (0o666 & ~umask == 0o644), and a file written by a prior
# default-mode build stays 0o644 on disk. The file is chmod'd to this on EVERY
# open so a fresh file lands owner-only AND an inherited world-readable file is
# retro-tightened — the plaintext memory ledger / manifest must not leak to other
# local users (the dir mode alone is not enough: a shared/inherited dir loosens
# it). From the security requirement, not the impl's current mode.
_OWNER_ONLY_FILE_MODE: int = 0o600

# The umask applied (tightly scoped, restored immediately) around the directory
# mkdir so a newly-created dir/file is owner-only the instant it appears on disk —
# closing the brief world-readable window between ``mkdir`` and the explicit
# ``os.chmod`` (the TOCTOU the audit flagged). 0o077 masks off ALL group/other
# bits. Defense-in-depth: the explicit chmod is the deterministic guarantee; this
# only removes the transient window.
_OWNER_ONLY_UMASK: int = 0o077


def _is_healthy(connection: sqlite3.Connection) -> bool:
    """Return whether ``connection`` opens onto a structurally valid database.

    Runs ``PRAGMA integrity_check`` and treats the database as healthy only when
    it returns the single canonical ``"ok"`` row.

    The catch is NARROWED on the exception CLASS, which is the only honest
    corruption signal:

    * A ``sqlite3.OperationalError`` (a ``DatabaseError`` SUBCLASS) is TRANSIENT
      — ``database is locked``, ``disk I/O error``, a read-only filesystem. It
      says nothing about the on-disk image being malformed, so it is RE-RAISED
      (fail-closed): the caller never deletes a possibly-healthy db on a passing
      blip. Returning ``False`` here would mis-classify a locked HEALTHY db as
      corrupt and destroy it (an irreplaceable-data-loss bug for the memory
      ledger, FP-06).
    * A PLAIN, non-operational ``sqlite3.DatabaseError`` (the malformed-header /
      ``file is not a database`` case, where the first statement on a torn write
      / partial fsync fails) IS genuine corruption — report unhealthy so the
      caller deletes and recreates (FP-08).

    Args:
        connection: An open connection to the database file under probe.

    Raises:
        sqlite3.OperationalError: A transient probe failure (lock / disk-IO /
            read-only FS). Propagated so the open fails closed and never deletes
            a possibly-healthy database.

    Returns:
        ``True`` if the integrity check returns the single ``"ok"`` row, else
        ``False`` (a non-``"ok"`` result or a non-operational ``DatabaseError`` —
        genuine corruption).
    """
    try:
        rows = connection.execute("PRAGMA integrity_check").fetchall()
    except sqlite3.OperationalError:
        # Locked / disk-IO / read-only FS: TRANSIENT, never corruption. Fail
        # closed — propagate so the eager startup aborts and the orchestrator
        # retries; NEVER delete a possibly-healthy db on a transient condition.
        # (OperationalError is a DatabaseError subclass, so this except must
        # come FIRST to win over the broader handler below.)
        raise
    except sqlite3.DatabaseError:
        # The malformed-header image: the first statement on it raises a PLAIN,
        # non-operational DatabaseError. A torn write / partial fsync produces
        # exactly this — treat as corrupt (delete + recreate, FP-08).
        return False
    # A healthy db returns exactly one row whose single column is "ok".
    return len(rows) == 1 and rows[0][0] == _INTEGRITY_CHECK_OK


def _delete_database_files(db_path: Path) -> None:
    """Delete a corrupt database file together with its WAL sidecars.

    Removes ``<path>`` and any ``<path>-wal`` / ``<path>-shm`` companions so a
    recreated WAL database never inherits a stale write-ahead log from the
    corrupt image. Each unlink tolerates an already-absent file.

    Args:
        db_path: The path to the main database file to remove.
    """
    db_path.unlink(missing_ok=True)
    for suffix in _WAL_SIDECAR_SUFFIXES:
        sidecar = db_path.with_name(f"{db_path.name}{suffix}")
        sidecar.unlink(missing_ok=True)


def _create_state_dir_owner_only(directory: Path) -> None:
    """Create ``directory`` (and any missing ancestors) owner-only (0o700).

    ``Path.mkdir(mode=0o700, parents=True)`` is NOT sufficient on its own: it
    applies the mode only to the FINAL directory and even that is masked by the
    process umask (so a 0o700 request lands as 0o700 & ~umask), while the
    intermediate ancestors brought into being by ``parents=True`` get the
    DEFAULT mode. Because the created dirs hold the plaintext memory ledger,
    EVERY directory this brings into being — the leaf AND every intermediate
    ancestor — must be owner-only, umask regardless.

    So we first compute which ancestors are missing (the set of dirs this call
    will CREATE), then ``mkdir`` and explicitly ``os.chmod`` each one to
    :data:`_OWNER_ONLY_DIR_MODE`. An ALREADY-EXISTING directory is never created
    and never chmod'd: the open tightens only what it creates, it must not
    re-permission an inherited/shared dir (re-tightening an operator's
    deliberately-shared mount point is a behaviour change beyond this fix).

    The mkdir itself runs under a tightly-scoped ``os.umask(0o077)`` (saved and
    restored in a ``finally`` so it never leaks to unrelated operations). That
    closes the brief world-readable window between the mkdir and the explicit
    chmod (the TOCTOU the audit flagged): a created dir is owner-only the instant
    it exists, and any sidecar SQLite creates while the umask is in effect is
    owner-only too. The explicit chmod below is KEPT as the deterministic,
    umask-independent guarantee — the umask only removes the transient window.

    Args:
        directory: The database file's parent directory to materialise.
    """
    # Snapshot which dirs are MISSING before we touch the filesystem. These — and
    # only these — are the dirs this call will create and is responsible for
    # tightening; any ancestor that already exists is left at its current mode.
    missing_ancestors = [
        ancestor
        for ancestor in (directory, *directory.parents)
        if not ancestor.exists()
    ]

    # Tighten the umask ONLY around the mkdir so a newly-created dir is owner-only
    # atomically (no world-readable window), then restore it immediately so the
    # change cannot leak to any unrelated operation. mkdir(parents=True) is
    # idempotent: an existing dir is left untouched, so the pre-existing-dir
    # boundary (no re-chmod of inherited dirs) is preserved.
    prior_umask = os.umask(_OWNER_ONLY_UMASK)
    try:
        directory.mkdir(parents=True, exist_ok=True)
    finally:
        os.umask(prior_umask)

    # Explicitly tighten each dir we just created. os.chmod is umask-independent,
    # so this lands an exact 0o700 on every created ancestor regardless of the
    # process umask — closing the world/group-readable plaintext-memory hole.
    for created in missing_ancestors:
        os.chmod(created, _OWNER_ONLY_DIR_MODE)


def open_resilient_sqlite(db_path: str) -> sqlite3.Connection:
    """Open a file-backed SQLite database resiliently (FP-01 + FP-08).

    The single source of truth for the local DBs' open. It:

    #. **FP-01** — creates the database file's parent directory so opening over
       an absent state dir succeeds instead of raising ``OperationalError``.
       Every directory the open BRINGS INTO BEING (the leaf parent and any
       intermediate ancestor created by ``parents=True``) is created owner-only
       (mode ``0o700``, umask regardless), under a tightly-scoped
       ``os.umask(0o077)`` so there is no world-readable window between the mkdir
       and the chmod. The state dir holds the plaintext memory ledger
       ``<slug>.memory.db`` and must not be group/world-readable. An
       ALREADY-EXISTING dir is left at its current mode — the open tightens only
       what it creates.
    #. Connects with ``check_same_thread=False`` (the loremaster single-writer /
       multi-reader concurrency contract the callers rely on).
    #. **FP-08** — probes the file with ``PRAGMA integrity_check``. A healthy
       database (including an empty or zero-byte one, which SQLite initialises
       valid-and-fresh) is returned UNCHANGED — its rows survive. A malformed
       image (a PLAIN, non-operational ``DatabaseError`` on the probe, or
       non-``"ok"`` integrity rows) is deleted (with its WAL sidecars) and a
       fresh empty database is recreated in its place, then returned ready for
       the caller's schema setup.
    #. **Owner-only file (defense-in-depth)** — ``chmod`` 0o600 the database file
       on EVERY successful open. ``sqlite3.connect`` creates a new file
       world-readable (0o666 & ~umask == 0o644) and a file from a prior
       default-mode build stays 0o644, so chmodding unconditionally both sets a
       freshly-created file owner-only AND retro-tightens an inherited
       world-readable file. WHY: the plaintext memory ledger / manifest must not
       be readable by other local users; the dir mode alone is not enough (a
       shared/inherited dir loosens it). This runs on both the healthy path (just
       tightens the existing file — it does NOT delete or recreate it, so a
       healthy db's data survives) and the delete-recreate path (tightens the
       freshly recreated file).

    **Fail-closed on a transient fault.** A ``sqlite3.OperationalError`` from
    the probe (``database is locked`` / ``disk I/O error`` / read-only FS) is
    TRANSIENT, not corruption, so :func:`_is_healthy` re-raises it and this
    function lets it PROPAGATE — it is never re-caught into the delete path. The
    eager startup aborts and the orchestrator retries, which is correct: a
    possibly-healthy database (e.g. the irreplaceable memory ledger, FP-06) is
    NEVER destroyed on a transient condition.

    The caller is responsible for the WAL pragma and ``executescript`` of its
    schema — this helper only guarantees a connection onto a structurally valid,
    writable database file.

    Args:
        db_path: The SQLite database path (a real file, not ``:memory:``).

    Raises:
        sqlite3.OperationalError: A transient probe failure (lock / disk-IO /
            read-only FS), propagated unmodified so the open fails closed
            instead of deleting a possibly-healthy database.

    Returns:
        An open :class:`sqlite3.Connection` onto a valid, writable database.
    """
    path = Path(db_path)
    # FP-01: sqlite3.connect cannot create a parent dir, so do it first — and
    # any dir we create lands owner-only so the plaintext memory ledger beside
    # the manifest is not group/world-readable. Idempotent: an existing dir is
    # left untouched (mode and all).
    _create_state_dir_owner_only(path.parent)

    connection = sqlite3.connect(db_path, check_same_thread=False)
    if _is_healthy(connection):
        # The common path: a fresh, empty, or healthy existing db opens unchanged.
        # Tighten the file to owner-only (chmod only — the healthy db is NOT
        # deleted/recreated, so its data survives) before returning.
        _set_owner_only_file_mode(path)
        return connection

    # FP-08: a corrupt image. Close the bad connection, delete the file and its
    # WAL sidecars, and recreate a fresh empty database in its place. Logged at
    # WARNING so the recovery is observable (the path is not a secret).
    connection.close()
    logger.warning(
        "Corrupt SQLite database detected at %s; deleting and recreating a fresh "
        "empty database (it is rebuildable by reindex)",
        db_path,
    )
    _delete_database_files(path)
    # Reconnect onto the now-absent path — sqlite3 creates a fresh empty db file.
    fresh_connection = sqlite3.connect(db_path, check_same_thread=False)
    # Tighten the freshly recreated file to owner-only too (the recreate went
    # through the default-mode connect, so it is 0o644 until chmod'd).
    _set_owner_only_file_mode(path)
    return fresh_connection


def _set_owner_only_file_mode(db_path: Path) -> None:
    """Tighten the database FILE at ``db_path`` to owner-only (0o600).

    Runs on every successful open, so it both sets a freshly-created file
    owner-only AND retro-tightens an inherited world-readable (0o644) file from a
    prior default-mode build. ``os.chmod`` is umask-independent, so it lands an
    exact 0o600. It does NOT delete or recreate the file — a healthy db's data is
    untouched — so it composes with the healthy-db-survives path.

    Args:
        db_path: The main database file to tighten (the WAL sidecars are created
            by SQLite at runtime under the owner-only umask, so the explicit
            target is the main file the security contract pins).
    """
    os.chmod(db_path, _OWNER_ONLY_FILE_MODE)
