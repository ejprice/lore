"""Contract tests for ``loremaster.memory.ledger.MemoryLedger`` resilient open.

These unit tests pin the LIVE :class:`~loremaster.memory.ledger.MemoryLedger` —
the durable SQLite spine the SurrealDB ``LocalMemoryBackend`` (P7) write-throughs
before the volatile store and replays from at boot. They exercise the ledger's
resilient construction (missing parent dir, corrupt file, empty file, a genuine
non-operational corruption on the integrity probe) INDEPENDENTLY of any vector
store, so a ledger that degrades to empty rather than crashing is proven here.

Provenance: these were carried over from ``test_memory_durability.py`` when that
module retired with the Qdrant-era ``MemoryStore`` at P8a (the Qdrant purge). The
durability write-through / restore-after-wipe / no-op-when-in-sync semantics that
lived alongside them are covered for the LIVE backend in ``test_memory_backend.py``
(``TestDurabilityWriteThrough`` / ``TestLedgerReplay`` / ``TestBackfillLedgerFromStore``);
what those did NOT cover — and what survives here — is the ledger's own resilient
open, which is store-agnostic.

The fault-injection pattern mirrors ``test_resilient_db.py``'s
``_IntegrityProbeFaultingConnection`` / ``_IntegrityCheckFaultInjector`` (the
generic ``open_resilient_sqlite`` primitive the ledger opens through); it is
duplicated here rather than cross-imported, matching this suite's no-cross-import
convention.
"""

from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

import pytest

from loremaster.memory.backend import MemoryRef
from loremaster.memory.ledger import MemoryLedger

# --- The deterministic-id convention, reconstructed INDEPENDENTLY -----------
# The memory point id is uuid5(NAMESPACE_URL, "memory:{text}:{refs_stamp}") — a
# shared domain convention reproduced here so a test computes the expected id
# from the convention WITHOUT reading it back from the code under test (which
# would be tautological).
_ID_PREFIX = "memory"
_ID_SEPARATOR = ":"
_REF_FIELD_SEPARATOR = "@"
_REF_JOIN = ","


def expected_refs_stamp(refs: list[MemoryRef]) -> str:
    """The order-insensitive refs stamp folded into a memory's deterministic id.

    Each ref becomes ``chunk_key@key_version``, the set is sorted
    (order-insensitive) and joined by ``,``. An empty ref list stamps the empty
    string — the ``refs_stamp`` the ledger must persist so a restore re-mints the
    SAME id.
    """
    stamped = sorted(
        f"{ref.chunk_key}{_REF_FIELD_SEPARATOR}{ref.key_version}" for ref in refs
    )
    return _REF_JOIN.join(stamped)


def expected_memory_id(text: str, refs: list[MemoryRef] | None = None) -> str:
    """The deterministic ``uuid5`` id for a memory, computed from the convention.

    Independent oracle: ``uuid5(NAMESPACE_URL, "memory:{text}:{refs_stamp}")`` —
    used to assert the ledger keys on the SAME id the backend mints (so a repeated
    record upserts one row rather than appending a duplicate).
    """
    refs_stamp = expected_refs_stamp(list(refs or ()))
    name = _ID_SEPARATOR.join((_ID_PREFIX, text, refs_stamp))
    return str(uuid.uuid5(uuid.NAMESPACE_URL, name))


# Production-representative memory prose — the kind of operator note that actually
# lands in this store (deploy gotchas, host-specific facts). NOT ``foo``/``bar``.
MEMORY_NOTES: tuple[str, ...] = (
    "lore container runs the baked localhost/lore:latest image, not the mounted "
    "source; a loremaster fix needs an image rebuild + recreate, not a restart.",
    "PG 18 moved the data dir: mount the volume at /var/lib/postgresql, NOT "
    "/var/lib/postgresql/data, or pg_ctlcluster errors at startup.",
)


# ---------------------------------------------------------------------------
# Integrity-probe fault injection — deterministically raise on the resilient
# open's ``PRAGMA integrity_check`` probe, mirroring test_resilient_db.py 1:1.
# The pattern is generic to ``open_resilient_sqlite`` and carries no
# ledger-specific logic.
# ---------------------------------------------------------------------------

# The exact probe statement the resilient open issues, pinned so the injected
# fault lands on the integrity probe and nothing else.
_INTEGRITY_CHECK_SQL: str = "PRAGMA integrity_check"


class _IntegrityProbeFaultingConnection:
    """A delegating proxy over a real connection that faults ONLY on the probe.

    ``sqlite3.Connection`` is an immutable C type, so its ``execute`` cannot be
    monkeypatched directly. Instead we wrap a real connection: every attribute
    and method delegates to the genuine connection EXCEPT ``execute``, which
    raises the configured error the first time the SQL is exactly
    ``PRAGMA integrity_check`` and otherwise passes through.
    """

    def __init__(self, real_connection: sqlite3.Connection, error: sqlite3.DatabaseError) -> None:
        object.__setattr__(self, "_real_connection", real_connection)
        object.__setattr__(self, "_error", error)
        object.__setattr__(self, "fired", False)

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        if not self.fired and sql == _INTEGRITY_CHECK_SQL:
            object.__setattr__(self, "fired", True)
            raise self._error
        return self._real_connection.execute(sql, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._real_connection, name)

    def __setattr__(self, name: str, value: Any) -> None:
        setattr(self._real_connection, name, value)


class _IntegrityCheckFaultInjector:
    """Patches ``loremaster.index.sqlite_resilient``'s ``sqlite3.connect`` to fault.

    ``open_resilient_sqlite`` calls ``sqlite3.connect`` (module-global in
    ``loremaster.index.sqlite_resilient``) and then probes the result with
    ``PRAGMA integrity_check``. We patch that module-global to return a
    :class:`_IntegrityProbeFaultingConnection` wrapping the genuine connection,
    so the probe raises the injected error while every other operation —
    including the real file open and the post-detection ``close()`` — behaves
    exactly as in production.
    """

    def __init__(self, error: sqlite3.DatabaseError) -> None:
        self._error = error
        self.proxy: _IntegrityProbeFaultingConnection | None = None

    @property
    def fired(self) -> bool:
        """Whether the injected integrity-probe fault actually fired."""
        return self.proxy is not None and bool(self.proxy.fired)

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Patch ``sqlite3.connect`` AS THE IMPLEMENTATION MODULE references it."""
        import loremaster.index.sqlite_resilient as impl

        real_connect = impl.sqlite3.connect  # type: ignore[attr-defined]
        injector = self

        def _faulting_connect(*args: Any, **kwargs: Any) -> Any:
            real_connection = real_connect(*args, **kwargs)
            if injector.proxy is None:
                proxy = _IntegrityProbeFaultingConnection(real_connection, injector._error)
                injector.proxy = proxy
                return proxy
            return real_connection

        monkeypatch.setattr(impl.sqlite3, "connect", _faulting_connect)  # type: ignore[attr-defined]


class TestLedgerResilientOpen:
    """The ledger opens resiliently — a missing parent or a corrupt file.

    Mirrors the manifest's posture and the resilient-db slice: construction must
    not crash on a missing parent dir, and a corrupted ledger file is recreated
    (the durable copy degrades to empty rather than taking the process down). A
    fresh project's ledger is empty (count 0) — the inert-baseline case.
    """

    def test_open_on_a_missing_parent_dir_does_not_crash(self, tmp_path: Path) -> None:
        # A path whose parent directory does not yet exist (fresh state volume).
        nested = tmp_path / "does" / "not" / "exist" / "lore_test.memory.db"
        ledger = MemoryLedger(str(nested))
        # A brand-new ledger on a fresh project is empty — the inert baseline that
        # makes a boot restore a no-op on first boot (count 0 == store count 0).
        assert ledger.count() == 0

    def test_open_on_a_corrupt_ledger_file_recreates_it(self, tmp_path: Path) -> None:
        # Pre-seed the path with garbage that is NOT a valid SQLite database.
        corrupt = tmp_path / "lore_test.memory.db"
        corrupt.write_bytes(b"this is not a sqlite database header at all\x00\xff")

        # Resilient open: recreate rather than crash; the durable copy degrades to
        # empty (a corrupt ledger has already lost its contents) but stays usable.
        ledger = MemoryLedger(str(corrupt))
        assert ledger.count() == 0
        ledger.record(
            memory_id=expected_memory_id(MEMORY_NOTES[0]),
            text=MEMORY_NOTES[0],
            metadata={"author": "operator"},
            refs_stamp=expected_refs_stamp([]),
        )
        assert ledger.count() == 1

    def test_record_is_idempotent_keyed_by_memory_id(self, tmp_path: Path) -> None:
        ledger = MemoryLedger(str(tmp_path / "lore_test.memory.db"))
        note = MEMORY_NOTES[0]
        memory_id = expected_memory_id(note)

        # Recording the SAME memory_id twice upserts (one row), not appends two.
        ledger.record(memory_id=memory_id, text=note, metadata={}, refs_stamp="")
        ledger.record(memory_id=memory_id, text=note, metadata={"author": "op"}, refs_stamp="")

        assert ledger.count() == 1
        record = next(r for r in ledger.all_records() if r.memory_id == memory_id)
        # The second write wins (upsert), so the latest metadata is present.
        assert record.metadata.get("author") == "op"

    def test_open_on_an_empty_file_is_a_plain_fresh_open_not_corruption(
        self, tmp_path: Path
    ) -> None:
        """A 0-byte ledger file opens as an empty ledger — NOT corruption-recreate.

        The corruption detector must distinguish a malformed IMAGE (delete+recreate)
        from an empty file SQLite legitimately initialises in place. An over-eager
        detector would churn on every fresh deploy.
        """
        empty_path = tmp_path / "lore_test.memory.db"
        empty_path.write_bytes(b"")
        assert empty_path.stat().st_size == 0, "fixture must be a true zero-byte file"

        ledger = MemoryLedger(str(empty_path))
        assert ledger.count() == 0, "an empty file is a valid fresh ledger"

    def test_non_operational_database_error_on_probe_still_recreates_ledger(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A plain DatabaseError (NOT OperationalError) on the probe → recreate.

        The genuine-corruption class must still delete-and-recreate, distinguished
        from a transient lock/IO blip purely by the exception class on the SAME
        integrity-probe seam ``open_resilient_sqlite`` shares with the manifest.
        """
        ledger_path = tmp_path / "lore_test.memory.db"
        note = MEMORY_NOTES[0]
        seed = MemoryLedger(str(ledger_path))
        seed.record(memory_id=expected_memory_id(note), text=note, metadata={}, refs_stamp="")
        assert seed.count() == 1, "seed ledger must hold the durable memory"
        seed.close()

        # A plain DatabaseError — NOT an OperationalError. This is what a malformed
        # header raises; isinstance(error, OperationalError) is False.
        corruption_error = sqlite3.DatabaseError("file is not a database")
        assert not isinstance(corruption_error, sqlite3.OperationalError), (
            "fixture must be a NON-operational DatabaseError (the corruption class)"
        )
        injector = _IntegrityCheckFaultInjector(corruption_error)
        injector.install(monkeypatch)

        # Genuine corruption recreates — construction must SUCCEED (no raise).
        ledger = MemoryLedger(str(ledger_path))
        assert injector.fired, "the injected probe fault must have fired"
        assert ledger.count() == 0, (
            "genuine corruption must delete-and-recreate a FRESH empty ledger "
            "(the seed row must be gone)"
        )
