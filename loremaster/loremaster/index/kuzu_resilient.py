"""Resilient KùzuDB open — the FP-01 + FP-08 analogue for the code-graph.

The :class:`~loremaster.graph.CodeGraph` opens a single-file KùzuDB database at
construction. The two production failure modes that wedge the SQLite manifest
(see :mod:`loremaster.index.sqlite_resilient`) wedge a bare ``kuzu.Database``
open in exactly the same way:

* **FP-01 — absent parent dir.** On a clean container the state volume is empty,
  so the directory holding ``<slug>.graph.kuzu`` does not exist. Opening fails
  because the parent directory cannot be created on the fly, and the server can
  never start on a clean volume.

* **FP-08 — corrupt existing file.** A torn write / partial fsync leaves a
  NON-EMPTY malformed image on disk. ``kuzu.Database`` raises a ``RuntimeError``
  (``"... not a valid Kuzu database file!"``) on open and every restart re-wedges
  until a human deletes the file.

The code-graph is fully rebuildable (a reindex repopulates it), so the correct
recovery for a corrupt image is delete-and-recreate. A VALID database must open
UNCHANGED — its records must survive; the recovery path must never nuke a healthy
database.

:func:`open_resilient_kuzu` is the single source of truth for that open: it
materialises the parent dir owner-only (reusing the same hardened mkdir as the
SQLite open), opens the Kùzu database, and on a malformed image deletes the file
(with its WAL/temp sidecars) and recreates a fresh empty database.

**Owner-only on disk (defense-in-depth).** The state dir holds the manifest AND
the plaintext memory ledger, so any directory this open CREATES is mode ``0o700``
— delegated to :func:`loremaster.index.sqlite_resilient._create_state_dir_owner_only`
so the directory-hardening logic lives in exactly one place. The Kùzu database
file itself is chmod'd ``0o600`` on every open for the same reason the SQLite file
is: a default-mode create lands world-readable, and the graph file sits beside the
sensitive plaintext memory ledger.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

import kuzu

from loremaster.index.sqlite_resilient import _create_state_dir_owner_only

logger = logging.getLogger(__name__)

# Owner-only (rw for the owner, nothing for group/other) permission bits for the
# Kùzu database FILE. Mirrors the SQLite file mode: the graph db sits in the same
# state dir as the plaintext memory ledger, so it must not be group/world-readable
# even though the graph itself is rebuildable.
_OWNER_ONLY_FILE_MODE: int = 0o600

# Sidecar suffixes Kùzu may leave beside ``<path>`` (the write-ahead log and any
# temp/shadow files). They must be removed together with the main file when a
# corrupt image is deleted, or stale sidecars would corrupt the recreated DB.
_KUZU_SIDECAR_SUFFIXES: tuple[str, ...] = (".wal", ".tmp", ".shadow")

# The distinctive substrings of Kùzu's corruption error message. ``kuzu.Database``
# raises a plain ``RuntimeError`` for BOTH genuine on-disk corruption AND transient
# faults (a Kùzu version-mismatch, an I/O error, a permission problem), with no
# distinct exception type to tell them apart. Deleting on EVERY RuntimeError would
# destroy a possibly-healthy database on a transient blip (the irreplaceable-data
# hazard the SQLite open fails-closed against). So the delete-and-recreate path is
# gated on the message matching one of these CORRUPTION signatures; any other
# RuntimeError is re-raised (fail-closed) so the open never nukes a db it cannot
# prove is malformed. Lower-cased before matching to be robust to phrasing case.
_CORRUPTION_SIGNATURES: tuple[str, ...] = (
    "not a valid kuzu database",
    "incompatible",
    "storage version",
)


def _is_corruption_error(error: RuntimeError) -> bool:
    """Whether a Kùzu open ``RuntimeError`` indicates a MALFORMED on-disk image.

    Matches the error text against the known corruption / incompatible-image
    signatures. Returns ``False`` for any other ``RuntimeError`` so the caller
    fails closed (re-raises) rather than deleting a possibly-healthy database on a
    transient fault — the same data-loss guard the SQLite open enforces.
    """
    message = str(error).lower()
    return any(signature in message for signature in _CORRUPTION_SIGNATURES)


def _delete_database_files(db_path: Path) -> None:
    """Delete a corrupt Kùzu database file together with its sidecars.

    Removes ``<path>`` and any ``<path>.wal`` / ``<path>.tmp`` / ``<path>.shadow``
    companions so a recreated database never inherits a stale write-ahead log from
    the corrupt image. Each unlink tolerates an already-absent file. A Kùzu db is
    a single file, but a defensive ``rmtree`` covers a future directory-format db.

    Args:
        db_path: The path to the main database file to remove.
    """
    if db_path.is_dir():  # pragma: no cover - defensive (current Kùzu is a file)
        import shutil

        shutil.rmtree(db_path, ignore_errors=True)
    else:
        db_path.unlink(missing_ok=True)
    for suffix in _KUZU_SIDECAR_SUFFIXES:
        sidecar = db_path.with_name(f"{db_path.name}{suffix}")
        sidecar.unlink(missing_ok=True)


def _set_owner_only_file_mode(db_path: Path) -> None:
    """Tighten the Kùzu database FILE at ``db_path`` to owner-only (0o600).

    Runs on every successful open so it both sets a freshly-created file owner-only
    AND retro-tightens an inherited world-readable file from a prior default-mode
    build. Tolerates a still-absent file (an in-memory Kùzu db has no on-disk path)
    so the in-memory test seam does not raise.

    Args:
        db_path: The main database file to tighten.
    """
    try:
        os.chmod(db_path, _OWNER_ONLY_FILE_MODE)
    except FileNotFoundError:
        # An in-memory db ("" / ":memory:") or a db Kùzu has not yet flushed to
        # disk — nothing to tighten, and the security contract targets real files.
        pass


def _is_in_memory(db_path: str) -> bool:
    """Whether ``db_path`` names an in-memory Kùzu database (no on-disk file)."""
    return db_path in ("", ":memory:")


def open_resilient_kuzu(db_path: str) -> kuzu.Database:
    """Open a single-file KùzuDB database resiliently (FP-01 + FP-08).

    The single source of truth for the code-graph's open. It:

    #. **FP-01** — creates the database file's parent directory owner-only (mode
       ``0o700``, umask regardless) via the shared
       :func:`~loremaster.index.sqlite_resilient._create_state_dir_owner_only`, so
       opening over an absent state dir succeeds. An in-memory db
       (``""`` / ``":memory:"``) skips all on-disk handling and opens directly.
    #. Opens ``kuzu.Database(db_path)``.
    #. **FP-08** — a corrupt on-disk image makes the open raise
       ``RuntimeError`` (Kùzu's "not a valid Kuzu database file"). That is caught,
       the bad file and its sidecars are deleted, and a fresh empty database is
       opened in its place. A healthy database (including a fresh empty one) opens
       UNCHANGED — its records survive.
    #. **Owner-only file (defense-in-depth)** — ``chmod`` 0o600 the database file
       on every successful on-disk open (a no-op for an in-memory db).

    Args:
        db_path: The Kùzu database path (a single real file), or ``""`` /
            ``":memory:"`` for an in-memory database.

    Returns:
        An open :class:`kuzu.Database`.
    """
    if _is_in_memory(db_path):
        return kuzu.Database(db_path)

    path = Path(db_path)
    # FP-01: materialise the parent dir owner-only before opening. Idempotent: an
    # existing dir is left untouched. Reuses the SQLite open's hardened mkdir.
    _create_state_dir_owner_only(path.parent)

    try:
        database = kuzu.Database(db_path)
    except RuntimeError as error:
        if not _is_corruption_error(error):
            # FAIL CLOSED: a RuntimeError that is NOT a recognised corruption /
            # incompatible-image signature is treated as TRANSIENT (an I/O error,
            # a permission problem, a lock). Re-raise so the open never deletes a
            # possibly-healthy database on a blip — the irreplaceable-data guard.
            raise
        # FP-08: a corrupt / incompatible image. Delete the bad file (+ sidecars)
        # and recreate a fresh empty database. Logged at WARNING so the recovery is
        # observable (the path is not a secret).
        logger.warning(
            "Corrupt Kùzu database detected at %s (%s); deleting and recreating a "
            "fresh empty database (it is rebuildable by reindex)",
            db_path,
            error,
        )
        _delete_database_files(path)
        database = kuzu.Database(db_path)

    _set_owner_only_file_mode(path)
    return database
