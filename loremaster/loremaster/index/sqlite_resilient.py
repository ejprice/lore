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
materialises the parent dir, connects, probes integrity, and on a malformed
image deletes the file (with its WAL sidecars) and recreates a fresh empty DB.
Both DB constructors call it instead of a bare ``sqlite3.connect`` so the logic
lives in exactly one place.
"""

from __future__ import annotations

import logging
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


def open_resilient_sqlite(db_path: str) -> sqlite3.Connection:
    """Open a file-backed SQLite database resiliently (FP-01 + FP-08).

    The single source of truth for the local DBs' open. It:

    #. **FP-01** — creates the database file's parent directory
       (``mkdir(parents=True, exist_ok=True)``) so opening over an absent state
       dir succeeds instead of raising ``OperationalError``.
    #. Connects with ``check_same_thread=False`` (the loremaster single-writer /
       multi-reader concurrency contract the callers rely on).
    #. **FP-08** — probes the file with ``PRAGMA integrity_check``. A healthy
       database (including an empty or zero-byte one, which SQLite initialises
       valid-and-fresh) is returned UNCHANGED — its rows survive. A malformed
       image (a PLAIN, non-operational ``DatabaseError`` on the probe, or
       non-``"ok"`` integrity rows) is deleted (with its WAL sidecars) and a
       fresh empty database is recreated in its place, then returned ready for
       the caller's schema setup.

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
    # FP-01: sqlite3.connect cannot create a parent dir, so do it first. Idempotent
    # — an existing dir is left untouched.
    path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path, check_same_thread=False)
    if _is_healthy(connection):
        # The common path: a fresh, empty, or healthy existing db opens unchanged.
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
    return sqlite3.connect(db_path, check_same_thread=False)
