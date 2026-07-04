"""Contract tests for the *resilient local-DB open* slice (FP-01 + FP-08).

These tests defined the behaviour of a feature that did NOT yet exist when the
contract was authored. They were written BLIND to the eventual implementation:
the expectations came from the idempotent-startup requirement, never from how
the then-current code happened to behave — RED *behaviourally*, pinned onto the
public constructors that existed at the time (the SQLite ``Manifest`` and
``build_app_context``).

HISTORICAL NOTE (post-P5): the SQLite ``Manifest`` class named throughout the
bug narrative below was DELETED after the Surreal port — its half of this
contract now lives on through ``MemoryLedger`` (the surviving
``open_resilient_sqlite`` consumer; see ``test_memory_durability.py``'s
``TestLedgerResilientOpen``) and ``test_surreal_manifest.py``. The Kùzu
``CodeGraph`` half that once shared this file was RETIRED in P8: the code-graph
is now a derivation over SurrealDB with no on-disk single-file DB, so its
resilient-open helper and resilience contract are gone. Only the SQLite /
memory-ledger half remains here. The narrative is kept as-written: it documents
WHY the resilient open exists.

The two bugs this contract closed
---------------------------------

* **FP-01 — clean container wedge.** On a fresh deploy the state volume is empty,
  so ``_DEFAULT_MANIFEST_DIR`` does not exist. The server passes
  ``_DEFAULT_MANIFEST_DIR / f"{slug}.memory.db"`` straight to ``sqlite3.connect``
  which raises ``OperationalError: unable to open database file`` when the parent
  dir is absent (only the CLI ever ``mkdir``s it). The server can never start on
  a clean volume. Pinned end-state: opening a sqlite DB whose PARENT DIR is
  absent must SUCCEED, and ``build_app_context`` over a nonexistent state dir
  must not raise and must produce a working memory ledger.

* **FP-08 — corruption wedge loop.** A corrupt / truncated ``<slug>.memory.db``
  makes ``sqlite3.connect`` raise ``sqlite3.DatabaseError: file is not a
  database`` on the first statement. There is NO integrity check / recovery, so
  EVERY startup re-wedges until a human deletes the file. Pinned end-state:
  opening a corrupt sqlite DB must SUCCEED by detecting the corruption, deleting
  the bad file, and recreating a fresh empty DB; afterwards the DB is queryable
  and a subsequent normal write works. THE exception — the memory ledger is the
  ONLY durable copy of user memories, so a TRANSIENT open fault must never delete
  it (see ``TestTransientErrorDoesNotDeleteHealthyDatabase``).

The critical anti-regression guard
-----------------------------------

A VALID existing DB must open UNCHANGED — its rows must survive. The recovery
path must not be over-eager and nuke a healthy database. Without this guard a
"recreate on every open" implementation would pass FP-08 while silently
destroying every real memory ledger.

Realistic corruption fixture (independent oracle)
-------------------------------------------------

The corruption fixture writes a GENUINE SQLite file (a table + a row, so it has
real pages) and then clobbers the 16-byte ``"SQLite format 3\\000"`` header magic
with garbage AND truncates the tail. That produces a NON-EMPTY malformed image —
the production failure mode (a torn write / partial fsync on a volume that lost
power), distinct from an EMPTY file which SQLite treats as valid-and-fresh. Each
corruption test FIRST proves, against ``sqlite3`` directly, that the fixture
genuinely triggers ``DatabaseError`` (the RED witness that "today it raises"),
THEN asserts the resilient constructor recovers.

How to run::

    uv run pytest loremaster/tests/test_resilient_db.py -q -p no:cacheprovider
"""

from __future__ import annotations

import os
import sqlite3
import stat
from pathlib import Path
from typing import Any

import pytest

# The surviving production constructor under test — it EXISTS and imports cleanly
# today, so referencing it keeps the suite RED on *behaviour*, never on a missing
# symbol.
from loremaster.index.sqlite_resilient import open_resilient_sqlite

# ---------------------------------------------------------------------------
# Production-realistic constants — same conventions as test_manifest.py /
# test_graph.py (clause 5: a single source of truth for domain conventions).
# ---------------------------------------------------------------------------

# The SQLite file header magic. A valid SQLite db ALWAYS begins with these exact
# 16 bytes; clobbering them is what makes the on-disk image "not a database".
# Pulled from the SQLite file-format spec, not from any lore code (independent).
_SQLITE_HEADER_MAGIC: bytes = b"SQLite format 3\x00"

# The on-disk file names the SERVER passes: the manifest / memory ledger are
# ``<slug>.db`` / ``<slug>.memory.db`` under the state dir. A realistic slug from
# a real lore.yaml deployment, not a ``foo`` placeholder.
_SLUG: str = "lore-loremaster"
_MANIFEST_FILENAME: str = f"{_SLUG}.db"

# A real Voyage per-input token cap, consumed by the build_app_context server-seam
# harness below (clause 1: a real cap, not a placeholder).
_VOYAGE_MAX_INPUT_TOKENS: int = 8192


# ---------------------------------------------------------------------------
# Corruption fixture builder — the independent oracle for FP-08.
# ---------------------------------------------------------------------------

def _write_corrupt_sqlite(path: Path) -> int:
    """Write a NON-EMPTY malformed SQLite image at ``path`` and return its size.

    Builds a genuine SQLite database (a table + a row, so the file has real
    pages), then clobbers the 16-byte header magic with garbage and truncates
    the tail. The result is the realistic production corruption — a torn write /
    partial fsync — NOT an empty file (an empty file is valid-and-fresh and must
    NOT be treated as corruption). The caller asserts this fixture genuinely
    raises ``DatabaseError`` before relying on the recovery contract.

    Args:
        path: The file path to write the corrupt image to.

    Returns:
        The size in bytes of the written corrupt image (always > 0).
    """
    connection = sqlite3.connect(str(path))
    connection.execute("CREATE TABLE seed (value INTEGER)")
    connection.execute("INSERT INTO seed VALUES (42)")
    connection.commit()
    connection.close()

    original = bytearray(path.read_bytes())
    # Clobber the header magic — this is exactly what makes SQLite report
    # "file is not a database" on open.
    original[0 : len(_SQLITE_HEADER_MAGIC)] = b"NOT-A-SQLITE-DB\x00"
    # Truncate to half (but keep a non-trivial body) so it is a malformed IMAGE,
    # not a zero-byte file.
    truncated = bytes(original[: max(100, len(original) // 2)])
    path.write_bytes(truncated)
    return path.stat().st_size


def _assert_raises_on_raw_open(path: Path) -> None:
    """RED witness: prove ``path`` genuinely fails a raw SQLite integrity probe.

    Independent of any lore code — opens with the stdlib ``sqlite3`` and asserts
    the corruption is real (open or ``PRAGMA integrity_check`` raises
    ``DatabaseError``). This anchors the corruption fixture so a later green on
    the resilient constructor means real recovery, not a no-op fixture.
    """
    with pytest.raises(sqlite3.DatabaseError):
        raw = sqlite3.connect(str(path))
        # The header clobber makes the very first statement fail.
        raw.execute("PRAGMA integrity_check").fetchall()
        raw.close()


# ---------------------------------------------------------------------------
# FP-01 at the SERVER seam — build_app_context over an absent state dir
# ---------------------------------------------------------------------------
#
# The manifest side is covered at the unit level in test_surreal_manifest.py;
# this class pins the END-STATE the requirement actually cares about: the SERVER
# startup path (build_app_context) over a nonexistent state dir must not raise
# and must produce a working memory ledger + Surreal manifest. It mirrors the
# hermetic harness in test_schema_rebuild.py (FakeEmbedder + a real throwaway
# Qdrant collection + tmp paths) so it drives the SAME construction path the
# server runs.
#
# Marked ``real-Qdrant``: build_app_context runs the probe gate + ensure_collection,
# which require a reachable Qdrant at conftest.QDRANT_URL with the API key. When
# Qdrant is unavailable the probe gate fails BEFORE the memory ledger is built,
# so this case cannot witness the FP-01 fix — it is then xfail-skipped, and the
# unit-level owner-only-dir tests below remain the authoritative FP-01 coverage.
# ---------------------------------------------------------------------------
class TestBuildAppContextCreatesStateDir:
    """FP-01 server seam: build_app_context over an absent state dir must succeed."""

    @pytest.mark.asyncio
    async def test_build_app_context_under_absent_state_dir_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """Arrange: a manifest_path (memory-ledger anchor) under a state dir that
        does NOT exist. Act: build_app_context with that path, a FakeEmbedder, a
        throwaway Qdrant. Assert: it does not raise, the state dir + memory ledger
        are created, and the Surreal manifest is empty/queryable.
        """
        # real-Qdrant — the probe gate + ensure_collection need a live Qdrant.
        from loremaster.server import LoreServer, build_app_context

        try:
            from conftest import QDRANT_URL, _qdrant_api_key
            from loresigil.testing import FakeEmbedder
            from qdrant_client import AsyncQdrantClient
        except Exception as import_error:  # pragma: no cover - harness wiring
            pytest.skip(f"hermetic Qdrant harness unavailable: {import_error}")

        import os

        from _surreal_harness import drop_database, make_env, surreal_password, surreal_user

        os.environ.setdefault("SURREAL_USER", surreal_user())
        os.environ.setdefault("SURREAL_PASS", surreal_password())
        config = _build_realistic_config(tmp_path)
        slug = config.project.slug

        # The state dir does NOT exist — this is the FP-01 clean-container trigger.
        absent_state_dir = tmp_path / "state" / "lore"
        manifest_path = absent_state_dir / f"{slug}.db"
        assert not absent_state_dir.exists(), "fixture must start with an absent state dir"

        client = AsyncQdrantClient(url=QDRANT_URL, api_key=_qdrant_api_key())
        created_collections = [f"lore_{slug}", f"lore_{slug}_memory"]
        app_context: Any = None
        try:
            try:
                app_context = await build_app_context(
                    server=LoreServer(config),
                    embedder=FakeEmbedder(dim=_CONFIG_DIM),
                    qdrant_client=client,
                    manifest_path=manifest_path,
                    snapshot_root=tmp_path / "snap",
                    start_tasks=False,
                )
            except sqlite3.OperationalError as error:
                pytest.fail(
                    "build_app_context over an absent state dir must mkdir the parent "
                    f"and build, not raise OperationalError: {error}"
                )

            # End-state (P5 successor contract): the manifest/graph live in
            # SurrealDB (no local files), so FP-01's surviving server-seam
            # surface is the SQLite MEMORY LEDGER under the absent dir — the
            # dir must have been created for it — and a fresh-deploy Surreal
            # manifest must be empty/queryable.
            assert absent_state_dir.is_dir(), (
                "build_app_context must create the state dir for the memory ledger"
            )
            assert manifest_path.with_name(f"{slug}.memory.db").is_file(), (
                "the memory ledger must exist after startup"
            )
            assert await app_context.manifest.all_files() == [], (
                "a fresh-deploy manifest must be empty"
            )
        finally:
            if app_context is not None:
                await app_context.aclose()
            await drop_database(make_env(database=slug, dim=_CONFIG_DIM))
            for name in created_collections:
                if await client.collection_exists(name):
                    await client.delete_collection(name)
            await client.close()


# The production embedding dimensionality used across the hermetic harnesses
# (matches test_schema_rebuild.py's _DIM — clause 5: same source of truth).
_CONFIG_DIM: int = 2048


def _surreal_url() -> str:
    from _surreal_harness import surreal_url

    return surreal_url()


def _build_realistic_config(tmp_path: Path) -> Any:
    """Build a validated LoreConfig grounded in production-realistic values.

    Mirrors test_schema_rebuild.py's ``_config`` (same TEI/Voyage shape) so the
    server seam test drives the SAME construction path the server runs (clause 5).
    A unique slug per call avoids cross-test Qdrant-collection collisions.
    """
    import uuid

    from loremaster.config import LoreConfig

    live_root = tmp_path / "live"
    live_root.mkdir(parents=True, exist_ok=True)
    slug = f"test_{uuid.uuid4().hex}"
    payload: dict[str, Any] = {
        "schema_version": 1,
        "project": {"slug": slug, "root": "."},
        "embedding": {
            "backend": "tei",
            "base_url": "http://tei.example:8080",
            "endpoint": "/embed",
            "model": "voyageai/voyage-4-nano",
            "dim": _CONFIG_DIM,
            "truncate": False,
            "max_input_tokens": _VOYAGE_MAX_INPUT_TOKENS,
            "max_batch_texts": 32,
            "concurrency": 2,
            "connect_timeout_s": 5,
            "api_key_env": "LORE_TEI_KEY",
            "tokenizer": "voyage-4-nano",
        },
        "qdrant": {"url": "http://127.0.0.1:16333", "api_key_env": "QDRANT__SERVICE__API_KEY"},
        # P5 write stack: throwaway per-call database on the dev server (the
        # unique slug doubles as the database name; reaped in the test finally).
        "surreal": {
            "url": _surreal_url(),
            "namespace": "lore_test",
            "database": slug,
            "user_env": "SURREAL_USER",
            "password_env": "SURREAL_PASS",
        },
        "roots": [
            {
                "tier": "custom",
                "watch": "live",
                "path": str(live_root),
                "include": ["**/*.py", "**/*.md"],
                "exclude": ["**/*.min.js"],
            }
        ],
        "include": [],
        "exclude_dirs": [".git", ".venv", "__pycache__"],
        "exclude_globs": ["**/*.min.js"],
        "chunkers": {".py": {"chunker": "python_ast"}, ".md": {"chunker": "markdown"}},
        "watcher": {
            "enabled": True,
            "observer": "inotify",
            "debounce_ms": 1500,
            "reconcile_interval_s": 600,
        },
        "server": {"host": "127.0.0.1", "path": "/mcp", "port": 9201},
    }
    return LoreConfig.model_validate(payload)


# ---------------------------------------------------------------------------
# SECURITY — transient-error misclassification (data-loss bug)
# ---------------------------------------------------------------------------
#
# HIGH-severity finding the original contract missed: ``_is_healthy`` runs
# ``PRAGMA integrity_check`` and catches a BARE ``sqlite3.DatabaseError`` as
# "unhealthy" → ``open_resilient_sqlite`` then DELETES the file. But
# ``sqlite3.OperationalError`` (raised for TRANSIENT conditions — "database is
# locked", "disk I/O error", a read-only FS) is a SUBCLASS of
# ``sqlite3.DatabaseError``, whereas GENUINE corruption ("file is not a
# database") raises a PLAIN ``DatabaseError`` that is NOT an OperationalError.
# So a transient lock/IO blip on a perfectly HEALTHY db is misclassified as
# corrupt and the db is DELETED. For the MemoryLedger — the ONLY durable copy of
# user-authored memories (FP-06) — that silently destroys irreplaceable data.
#
# The exception hierarchy is a stdlib fact, verified live against this interpreter
# in the audit, not assumed (clause 2 independent oracle):
#   issubclass(sqlite3.OperationalError, sqlite3.DatabaseError) is True
#   "file is not a database" raises a plain DatabaseError, NOT an OperationalError.
#
# Desired contract (fail-CLOSED): a transient OperationalError from the integrity
# probe must PROPAGATE out of the open (the eager startup aborts → the
# orchestrator retries once the lock/IO blip clears) — it must NEVER delete the
# file. Genuine corruption (a non-OperationalError DatabaseError, or non-"ok"
# integrity rows) STILL deletes-and-recreates.
#
# The seam under test is the integrity probe inside ``_is_healthy``: the FIRST
# ``execute`` call on the freshly-opened connection runs ``PRAGMA
# integrity_check``. We monkeypatch ``sqlite3.Connection.execute`` so that ONLY
# that PRAGMA raises the injected error — connect / mkdir / schema setup are
# untouched — which deterministically distinguishes the two error classes
# (clause 3: the exact handoff where the unit decides delete-vs-keep).
# ---------------------------------------------------------------------------

# The exact probe statement ``_is_healthy`` issues. Pinned to the same string the
# implementation runs so the injected fault lands on the integrity probe and
# nothing else (clause 5: a single source of truth, not a drifting literal).
_INTEGRITY_CHECK_SQL: str = "PRAGMA integrity_check"

# Production-canonical transient error messages SQLite raises as OperationalError
# under contention / a flaky volume — the realistic inputs this guard exists for
# (clause 1). These are real SQLite error strings, not invented placeholders.
_LOCKED_MESSAGE: str = "database is locked"
_DISK_IO_MESSAGE: str = "disk I/O error"
_READONLY_MESSAGE: str = "attempt to write a readonly database"

# A production-shaped durable memory row (clause 1): a real uuid5-style id, a real
# user note, real metadata, and a refs stamp — the irreplaceable FP-06 content
# whose loss is the whole point of this guard.
_MEMORY_ID: str = "5f6d3c2b-1a09-5e8d-9c7b-6a5f4e3d2c1b"
_MEMORY_TEXT: str = "The payroll export must round commission to the nearest cent, never truncate."
_MEMORY_METADATA: dict[str, Any] = {"source": "save_memory", "tier": "custom"}
_MEMORY_REFS_STAMP: str = "src/payroll/export.py@a1b2c3"


class _IntegrityProbeFaultingConnection:
    """A delegating proxy over a real connection that faults ONLY on the probe.

    ``sqlite3.Connection`` is an immutable C type, so its ``execute`` cannot be
    monkeypatched directly. Instead we wrap a real connection: every attribute
    and method delegates to the genuine connection EXCEPT ``execute``, which
    raises the configured error the first time the SQL is exactly
    ``PRAGMA integrity_check`` (the statement ``_is_healthy`` issues) and
    otherwise passes through. This injects the transient condition on the exact
    integrity-probe seam — deterministically, with no real lock — which is where
    ``_is_healthy`` catches ``DatabaseError`` too broadly.

    The proxy is what a patched ``sqlite3.connect`` (see
    :class:`_IntegrityCheckFaultInjector`) hands back to ``open_resilient_sqlite``,
    so the unit under test exercises the proxy exactly as it would a real
    connection — including the ``connection.close()`` it does before deleting a
    file, which we forward so a real DELETE on the bug path still happens.
    """

    def __init__(self, real_connection: sqlite3.Connection, error: sqlite3.DatabaseError) -> None:
        # ``object.__setattr__`` so we never recurse through ``__getattr__``.
        object.__setattr__(self, "_real_connection", real_connection)
        object.__setattr__(self, "_error", error)
        object.__setattr__(self, "fired", False)

    def execute(self, sql: str, *args: Any, **kwargs: Any) -> Any:
        if not self.fired and sql == _INTEGRITY_CHECK_SQL:
            object.__setattr__(self, "fired", True)
            raise self._error
        return self._real_connection.execute(sql, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        # Everything else (executescript, commit, close, cursor, ...) delegates.
        return getattr(self._real_connection, name)

    def __setattr__(self, name: str, value: Any) -> None:
        # row_factory etc. set by the caller must land on the real connection.
        setattr(self._real_connection, name, value)


class _IntegrityCheckFaultInjector:
    """Patches the implementation's ``sqlite3.connect`` to fault on the probe.

    ``open_resilient_sqlite`` calls ``sqlite3.connect`` (module-global in
    ``loremaster.index.sqlite_resilient``) and then probes the result with
    ``PRAGMA integrity_check`` inside ``_is_healthy``. We patch that module-global
    ``sqlite3.connect`` to return a :class:`_IntegrityProbeFaultingConnection`
    wrapping the genuine connection, so the probe raises the injected error while
    every other operation — including the real file open and the post-detection
    ``close()`` — behaves exactly as in production. This is the robust,
    deterministic seam (the immutable C ``Connection.execute`` cannot be patched).
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
            # Only the FIRST connect (the integrity-probe open) is wrapped; a
            # recreate-reconnect on the corruption path returns a plain connection.
            if injector.proxy is None:
                proxy = _IntegrityProbeFaultingConnection(real_connection, injector._error)
                injector.proxy = proxy
                return proxy
            return real_connection

        monkeypatch.setattr(impl.sqlite3, "connect", _faulting_connect)  # type: ignore[attr-defined]


class TestTransientErrorDoesNotDeleteHealthyDatabase:
    """A TRANSIENT OperationalError during the integrity probe must NOT delete.

    Lifecycle: create a healthy db with real data (the resource), wire it in,
    then DEGRADE the next open with a transient lock/IO/readonly fault on the
    integrity probe — and assert the open fails CLOSED (propagates) WITHOUT
    destroying the healthy file. Recovery: once the transient condition clears, a
    fresh open finds the data intact.

    These are RED against the current impl, which swallows the OperationalError
    (as a DatabaseError subclass) and DELETES the healthy db.
    """

    def test_locked_database_does_not_destroy_durable_memory_ledger(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """THE data-loss case: a transient blip must NOT wipe the durable memory ledger.

        The MemoryLedger is the ONLY durable copy of user-authored memories (FP-06)
        — a memory cannot be re-derived from source the way code vectors can. If a
        transient lock on startup deletes it, the memories are gone forever. This
        pins that a transient OperationalError propagates and the durable note
        survives intact.
        """
        from loremaster.memory.ledger import MemoryLedger

        ledger_path = tmp_path / f"{_SLUG}.memory.db"
        seed = MemoryLedger(str(ledger_path))
        seed.record(
            memory_id=_MEMORY_ID,
            text=_MEMORY_TEXT,
            metadata=_MEMORY_METADATA,
            refs_stamp=_MEMORY_REFS_STAMP,
        )
        assert seed.count() == 1, "seed ledger must hold the durable memory"
        seed.close()

        injector = _IntegrityCheckFaultInjector(sqlite3.OperationalError(_LOCKED_MESSAGE))
        injector.install(monkeypatch)

        with pytest.raises(sqlite3.OperationalError):
            MemoryLedger(str(ledger_path))

        assert ledger_path.is_file(), (
            "a transient OperationalError must NOT delete the durable memory ledger "
            "(FP-06 data loss — the only copy of user memories destroyed)"
        )
        monkeypatch.undo()
        recovered = MemoryLedger(str(ledger_path))
        try:
            records = recovered.all_records()
            assert len(records) == 1, (
                "the user's durable memory must SURVIVE a transient startup blip "
                "(it was deleted — irreplaceable FP-06 data loss)"
            )
            assert records[0].memory_id == _MEMORY_ID
            assert records[0].text == _MEMORY_TEXT
            assert records[0].metadata == _MEMORY_METADATA
        finally:
            recovered.close()


class TestSqliteExceptionHierarchyIsTheBugSurface:
    """Pin the stdlib facts the whole guard rests on (independent oracle, clause 2).

    These are the exact properties that make the over-broad catch a bug. If a
    future Python changed them, this guard's reasoning would silently rot — so we
    assert them against the live interpreter rather than trusting a comment.
    """

    def test_operational_error_is_a_subclass_of_database_error(self) -> None:
        """OperationalError ⊂ DatabaseError — why ``except DatabaseError`` over-catches."""
        assert issubclass(sqlite3.OperationalError, sqlite3.DatabaseError), (
            "the bug exists precisely because OperationalError is a DatabaseError subclass"
        )

    def test_genuine_corruption_raises_a_non_operational_database_error(
        self, tmp_path: Path
    ) -> None:
        """A malformed image raises a PLAIN DatabaseError that is NOT OperationalError.

        This is the class distinction the narrowed catch keys on: delete only on a
        non-OperationalError DatabaseError.
        """
        corrupt_path = tmp_path / _MANIFEST_FILENAME
        _write_corrupt_sqlite(corrupt_path)
        with pytest.raises(sqlite3.DatabaseError) as exc_info:
            raw = sqlite3.connect(str(corrupt_path))
            raw.execute(_INTEGRITY_CHECK_SQL).fetchall()
            raw.close()
        assert not isinstance(exc_info.value, sqlite3.OperationalError), (
            "genuine corruption must raise a NON-operational DatabaseError — "
            "the signal that distinguishes it from a transient lock/IO blip"
        )


# ---------------------------------------------------------------------------
# FIX 2 — the state dir created by the open must be owner-only (mode 0700)
# ---------------------------------------------------------------------------
#
# ``open_resilient_sqlite`` materialises the database file's parent directory via
# ``path.parent.mkdir(parents=True, exist_ok=True)`` (FP-01). Today that mkdir
# uses the default mode, so the new dir lands world- and group-readable (0755
# under a typical 022 umask). That state dir holds the manifest AND — critically —
# the memory ledger ``<slug>.memory.db``, a plaintext SQLite file containing
# user-authored memory TEXT (e.g. internal notes, paths, business rules). Anything
# readable by other local users is an information-disclosure hole.
#
# Pinned end-state: a directory the open CREATES is created with mode 0o700
# (owner read/write/execute only). The check is the canonical
# ``stat.S_IMODE(os.stat(parent).st_mode) == 0o700``.
#
# IMPORTANT scoping — only a dir the open CREATES is asserted on:
#   * An ALREADY-EXISTING dir's permissions are NOT forced. ``mkdir(exist_ok=True)``
#     leaves an existing dir untouched, and chmod-on-existing would silently
#     re-tighten an operator's deliberately-shared deployment dir (or a mount
#     point) — a behaviour change beyond the security fix's remit. So the
#     "existing dir is left alone" case is pinned as the complementary boundary,
#     NOT as a 0700 assertion. The contract: tighten what we create, never
#     re-permission what we inherit.
#
# These tests are BEHAVIOURALLY RED today: the default-mode mkdir yields 0755 (or
# whatever ``0777 & ~umask`` gives), which ``== 0o700`` rejects. The oracle is the
# requirement (owner-only), not the implementation's current mode (clause 2).
# ---------------------------------------------------------------------------

# The required owner-only permission bits for a state dir the open creates: rwx
# for the owner, nothing for group/other. From the security requirement (a state
# dir holding plaintext memory must not be world-readable), not from the code.
_OWNER_ONLY_DIR_MODE: int = 0o700


def _dir_mode(path: Path) -> int:
    """Return the permission bits (``S_IMODE``) of ``path`` — the canonical check.

    Strips the file-type bits so the comparison is against the raw rwx triplet,
    exactly as the requirement states (``stat.S_IMODE(os.stat(dir).st_mode)``).
    """
    return stat.S_IMODE(os.stat(path).st_mode)


class TestStateDirCreatedOwnerOnly:
    """FIX 2: a state dir the resilient open CREATES is mode 0700 (owner-only).

    ``open_resilient_sqlite`` mkdir's the db file's missing parent (FP-01). That
    parent holds the plaintext memory ledger, so it must be created owner-only
    (0o700), not world-readable. A dir that ALREADY exists is left untouched — the
    fix tightens what it creates, it does not re-permission inherited dirs.
    """

    def test_created_parent_dir_is_mode_0700(self, tmp_path: Path) -> None:
        """The leaf parent the open creates has owner-only permissions.

        Arrange: a db path under a parent dir that does NOT yet exist.
        Act: open the resilient sqlite over it (which mkdir's the parent).
        Assert: the created parent dir is mode 0o700.
        """
        # A realistic state-dir layout + the real ``<slug>.db`` filename the server
        # passes (clause 1/5: production-shaped path, not a placeholder).
        state_dir = tmp_path / "state" / "lore"
        db_path = state_dir / _MANIFEST_FILENAME
        assert not state_dir.exists(), "fixture must start with an absent state dir"

        connection = open_resilient_sqlite(str(db_path))
        try:
            assert state_dir.is_dir(), "the open must create the missing parent dir"
            # Today this is 0o755 (default-mode mkdir) — RED. The requirement is
            # owner-only so the plaintext memory ledger is not world-readable.
            assert _dir_mode(state_dir) == _OWNER_ONLY_DIR_MODE, (
                f"created state dir must be {_OWNER_ONLY_DIR_MODE:#o} (owner-only), "
                f"got {_dir_mode(state_dir):#o} — plaintext memory must not be "
                "group/world-readable"
            )
        finally:
            connection.close()

    def test_created_dir_grants_no_group_or_other_access(self, tmp_path: Path) -> None:
        """No group/other permission bits are set on a created state dir.

        A direct security-boundary assertion: the disclosure risk is ANY group/
        other read or traversal bit. This pins the boundary independently of the
        exact owner bits, so a future 'owner gets rw only' tweak still satisfies
        the real invariant (nothing leaks to other local users).
        """
        state_dir = tmp_path / "state" / "lore"
        db_path = state_dir / _MANIFEST_FILENAME

        connection = open_resilient_sqlite(str(db_path))
        try:
            mode = _dir_mode(state_dir)
            # The disclosure bits: group rwx + other rwx. None may be set.
            group_and_other = mode & 0o077
            assert group_and_other == 0, (
                f"state dir leaks {group_and_other:#o} to group/other; the plaintext "
                "memory ledger must be owner-only"
            )
        finally:
            connection.close()

    def test_memory_ledger_filename_parent_is_owner_only(self, tmp_path: Path) -> None:
        """The MEMORY-LEDGER path's created parent is owner-only too.

        The disclosure risk is specifically ``<slug>.memory.db`` (user-authored
        memory text in plaintext SQLite). This drives the same open over the real
        memory-ledger filename so the guard is anchored to the file that actually
        carries the sensitive content (clause 1: the real at-risk artifact).
        """
        # The server names the memory ledger ``<slug>.memory.db`` alongside the
        # manifest under the same state dir (clause 5: same naming convention).
        state_dir = tmp_path / "state" / "lore"
        memory_db_path = state_dir / f"{_SLUG}.memory.db"
        assert not state_dir.exists(), "fixture must start with an absent state dir"

        connection = open_resilient_sqlite(str(memory_db_path))
        try:
            assert _dir_mode(state_dir) == _OWNER_ONLY_DIR_MODE, (
                "the memory-ledger's created parent dir must be owner-only — it "
                "holds user-authored memory text in plaintext SQLite"
            )
        finally:
            connection.close()

    def test_nested_created_ancestors_are_all_owner_only(self, tmp_path: Path) -> None:
        """Every ancestor dir the open CREATES (parents=True) is owner-only.

        ``mkdir(parents=True)`` may create several missing ancestors at once. Each
        one the open brings into being holds (or leads to) the state dir, so none
        may be group/world-traversable — an exec bit on an intermediate dir is
        enough to reach the leaf. Only ancestors UNDER tmp_path that did not exist
        before are checked (tmp_path itself is pre-existing — see the existing-dir
        boundary test for why inherited dirs are out of scope).
        """
        # Two missing levels: both ``deep`` and ``deep/state`` (and the leaf) are
        # created by this single open.
        leaf_dir = tmp_path / "deep" / "state" / "lore"
        db_path = leaf_dir / _MANIFEST_FILENAME
        created_ancestors = [tmp_path / "deep", tmp_path / "deep" / "state", leaf_dir]
        for ancestor in created_ancestors:
            assert not ancestor.exists(), "fixture: all target ancestors must be absent"

        connection = open_resilient_sqlite(str(db_path))
        try:
            for ancestor in created_ancestors:
                assert _dir_mode(ancestor) == _OWNER_ONLY_DIR_MODE, (
                    f"created ancestor {ancestor} must be owner-only "
                    f"({_OWNER_ONLY_DIR_MODE:#o}), got {_dir_mode(ancestor):#o}"
                )
        finally:
            connection.close()

    def test_existing_dir_permissions_are_not_forced(self, tmp_path: Path) -> None:
        """An ALREADY-EXISTING state dir is left at its current mode (not re-tightened).

        Scoping boundary: the fix tightens dirs it CREATES, it must NOT chmod a
        dir it inherits — re-permissioning an operator's deliberately-shared mount
        point or deploy dir is a behaviour change beyond the security fix. Here the
        state dir pre-exists at a group-readable 0o755; after the open it must be
        UNCHANGED (still 0o755), proving the open does not touch inherited perms.
        """
        state_dir = tmp_path / "state" / "lore"
        # Pre-create the dir at a group-readable mode, defeating the umask with an
        # explicit chmod so the starting mode is deterministic.
        state_dir.mkdir(parents=True)
        preexisting_mode = 0o755
        state_dir.chmod(preexisting_mode)
        assert _dir_mode(state_dir) == preexisting_mode, "fixture: dir starts at 0o755"

        db_path = state_dir / _MANIFEST_FILENAME
        connection = open_resilient_sqlite(str(db_path))
        try:
            # exist_ok=True leaves it untouched: the open must NOT re-permission it.
            assert _dir_mode(state_dir) == preexisting_mode, (
                "an already-existing state dir must be left at its current mode; "
                "the fix tightens only dirs it CREATES, never inherited ones"
            )
        finally:
            connection.close()


# ---------------------------------------------------------------------------
# SECURITY FIX — the DB FILE the open creates/opens must be owner-only (0o600)
# ---------------------------------------------------------------------------
#
# The dir-0700 hardening above (TestStateDirCreatedOwnerOnly) tightens the
# PARENT directory, but the database FILE itself is still created by
# ``sqlite3.connect`` at the default ``0o666 & ~umask`` == 0o644 — WORLD-READABLE.
# So the dir-0700 mode is the SOLE protection for the plaintext memory ledger
# ``<slug>.memory.db`` and the manifest: if that dir mode is ever loosened (a
# shared mount, an operator chmod, an inherited pre-existing dir the open is
# scoped NOT to re-tighten), every byte of user-authored memory text is readable
# by other local users. Defense-in-depth requires the FILE be owner-only too.
#
# Pinned end-state (from the security requirement, NOT the current 0o644 the impl
# happens to produce — clause 2): after ``open_resilient_sqlite`` returns, the db
# file is mode 0o600 (owner rw, nothing for group/other), on BOTH:
#   * a FRESHLY-CREATED file (today 0o644 → RED), and
#   * an EXISTING world-readable (0o644) HEALTHY file — the "tighten on next
#     deploy" guarantee that retro-fixes files written by a prior 0o644 build,
#     and which must NOT delete the healthy file or lose its data (today the open
#     leaves the inherited 0o644 untouched → RED).
#
# The disclosure-bit boundary (``mode & 0o077 == 0``) is pinned independently of
# the exact owner bits so a future "owner rw only" formulation still satisfies the
# real invariant: nothing leaks to other local users. And the hardening is pinned
# through the REAL production constructor (MemoryLedger), not only the bare
# helper, so the guarantee covers the path the server runs (clause 3/4: the
# production open seam, with the memory ledger as the at-risk artifact).
#
# These mode assertions are BEHAVIOURALLY RED today: a default-mode connect yields
# 0o644, which ``== 0o600`` and ``& 0o077 == 0`` both reject. They are NOT
# structurally red — ``open_resilient_sqlite`` / ``MemoryLedger`` both exist and
# import cleanly; only the FILE permission is wrong.
# ---------------------------------------------------------------------------

# The required owner-only permission bits for a DB FILE the open creates or opens:
# owner read+write, nothing for group/other. From the security requirement (a
# plaintext memory ledger / manifest must not be group/world-readable), NOT from
# the implementation's current mode (clause 2: an independent oracle).
_OWNER_ONLY_FILE_MODE: int = 0o600

# A deliberately world-readable starting mode for the "tighten an existing file"
# case — the exact 0o644 a prior default-mode ``sqlite3.connect`` build wrote to
# disk (clause 1: the real artifact this deploy-time fix exists to retro-tighten).
_WORLD_READABLE_FILE_MODE: int = 0o644


def _file_mode(path: Path) -> int:
    """Return the permission bits (``S_IMODE``) of the FILE at ``path``.

    Strips the file-type bits so the comparison is the raw rwx triplet, exactly
    as the requirement states (``stat.S_IMODE(os.stat(file).st_mode)``). The file
    sibling of :func:`_dir_mode`, reused across every case in this class.
    """
    return stat.S_IMODE(os.stat(path).st_mode)


def _make_world_readable_healthy_db(db_path: Path) -> None:
    """Write a HEALTHY sqlite db with one real row, then ``chmod`` it world-readable.

    Reproduces the production pre-condition this fix retro-tightens: a valid db
    file left at 0o644 by a prior default-mode build, holding real data that MUST
    survive the next (tightening) open. A generic sqlite table (mirroring the
    corruption fixture's own seed shape) — the file-permission guarantee is
    backend-agnostic, so it does not need any particular consumer's schema.
    """
    connection = sqlite3.connect(str(db_path))
    connection.execute("CREATE TABLE seed (value INTEGER)")
    connection.execute("INSERT INTO seed VALUES (42)")
    connection.commit()
    connection.close()
    os.chmod(db_path, _WORLD_READABLE_FILE_MODE)
    # Precondition guard: the fixture really starts world-readable, so a later
    # 0o600 assertion proves the open TIGHTENED it (not that it was already tight).
    assert _file_mode(db_path) == _WORLD_READABLE_FILE_MODE, (
        "fixture must start at 0o644 (a prior default-mode build's world-readable file)"
    )


class TestDatabaseFilesAreOwnerOnly:
    """SECURITY: a DB file the resilient open creates/opens is mode 0o600 (owner-only).

    The dir-0700 hardening protects the directory; this guards the FILE. A
    plaintext DB file — most critically the memory ledger ``<slug>.memory.db`` —
    must be owner-rw only — never group/world-readable — on both a freshly
    created file and an existing world-readable one (the deploy-time tighten
    guarantee). Pinned both at the bare ``open_resilient_sqlite`` helper and
    through the real MemoryLedger production constructor.
    """

    def test_freshly_created_db_file_is_mode_0600(self, tmp_path: Path) -> None:
        """A brand-new db file the open creates has owner-only (0o600) permissions.

        Arrange: a db path that does NOT yet exist.
        Act: open the resilient sqlite over it (which creates the file).
        Assert: the created file is mode 0o600.
        """
        state_dir = tmp_path / "state" / "lore"
        db_path = state_dir / _MANIFEST_FILENAME
        assert not db_path.exists(), "fixture must start with an absent db file"

        connection = open_resilient_sqlite(str(db_path))
        try:
            assert db_path.is_file(), "the open must create the db file"
            # Today this is 0o644 (default-mode sqlite3.connect under a 022 umask)
            # — RED. The requirement is owner-only so the plaintext memory ledger /
            # manifest is not group/world-readable.
            assert _file_mode(db_path) == _OWNER_ONLY_FILE_MODE, (
                f"freshly created db file must be {_OWNER_ONLY_FILE_MODE:#o} "
                f"(owner-only), got {_file_mode(db_path):#o} — a plaintext DB file "
                "must not be group/world-readable"
            )
        finally:
            connection.close()

    def test_freshly_created_db_file_grants_no_group_or_other_access(
        self, tmp_path: Path
    ) -> None:
        """No group/other permission bits are set on a freshly created db file.

        A direct security-boundary assertion pinned independently of the exact
        owner bits: the disclosure risk is ANY group/other read bit, so a future
        'owner rw only' tweak still satisfies the real invariant (nothing leaks to
        other local users). This is the magnitude/sanity bound on the mode value —
        it survives a reformulation that exact-equality on 0o600 would not.
        """
        db_path = tmp_path / "state" / "lore" / _MANIFEST_FILENAME

        connection = open_resilient_sqlite(str(db_path))
        try:
            mode = _file_mode(db_path)
            group_and_other = mode & 0o077  # group rwx + other rwx — none may be set
            assert group_and_other == 0, (
                f"db file leaks {group_and_other:#o} to group/other; a plaintext DB "
                "file must be owner-only"
            )
        finally:
            connection.close()

    def test_existing_world_readable_healthy_db_is_tightened_to_0600_on_open(
        self, tmp_path: Path
    ) -> None:
        """An existing 0o644 HEALTHY db is tightened to 0o600 on open — data intact.

        THE deploy-time guarantee: a valid db file written world-readable by a
        prior default-mode build is re-permissioned to owner-only on the next open,
        WITHOUT being deleted and WITHOUT losing its data. The healthy-db-survives
        contract and this tighten contract must hold together: the chmod must not
        trip the resilient open into a delete/recreate.

        Arrange: a healthy sqlite db with one real row, chmod'd to 0o644.
        Act: open it again via the bare resilient helper.
        Assert: the file is now 0o600 AND its row survived (not recreated empty).
        """
        db_path = tmp_path / _MANIFEST_FILENAME
        _make_world_readable_healthy_db(db_path)

        connection = open_resilient_sqlite(str(db_path))
        try:
            # The file is the SAME inode tightened in place, not a recreated one —
            # so its mode is now owner-only. Today the open leaves the inherited
            # 0o644 untouched → RED.
            assert _file_mode(db_path) == _OWNER_ONLY_FILE_MODE, (
                f"an existing world-readable db must be tightened to "
                f"{_OWNER_ONLY_FILE_MODE:#o} on open (the deploy-time fix), got "
                f"{_file_mode(db_path):#o}"
            )
        finally:
            connection.close()

        # And the healthy data SURVIVED — the tighten must not have deleted the db.
        # Read back with a raw sqlite3 connection (the file-permission guarantee is
        # backend-agnostic), proving the row is the SAME data, not a fresh empty db
        # (the anti-regression seam: tighten ≠ delete-recreate).
        raw = sqlite3.connect(str(db_path))
        try:
            rows = raw.execute("SELECT value FROM seed").fetchall()
            assert rows == [(42,)], (
                "tightening an existing healthy db must NOT delete it — the row "
                "must survive (the 0o600 chmod must not trip the resilient recreate)"
            )
        finally:
            raw.close()

    def test_memory_ledger_db_file_is_owner_only(self, tmp_path: Path) -> None:
        """The MEMORY-LEDGER db file — the at-risk plaintext artifact — is 0o600.

        ``<slug>.memory.db`` holds user-authored memory TEXT in plaintext SQLite —
        the specific file whose world-readability is the disclosure hole this fix
        closes. Drive the real MemoryLedger constructor over it and pin owner-only,
        anchoring the guard to the file that actually carries the sensitive content
        (clause 1/4: the real at-risk consumer).
        """
        from loremaster.memory.ledger import MemoryLedger

        # The server names the memory ledger ``<slug>.memory.db`` (clause 5: same
        # naming convention as the other harness tests in this file).
        ledger_path = tmp_path / "state" / "lore" / f"{_SLUG}.memory.db"

        ledger = MemoryLedger(str(ledger_path))
        try:
            # Write a production-shaped durable memory so the file holds real
            # sensitive content (clause 1) — the very bytes that must not leak.
            ledger.record(
                memory_id=_MEMORY_ID,
                text=_MEMORY_TEXT,
                metadata=_MEMORY_METADATA,
                refs_stamp=_MEMORY_REFS_STAMP,
            )
            assert _file_mode(ledger_path) == _OWNER_ONLY_FILE_MODE, (
                f"the memory-ledger db must be {_OWNER_ONLY_FILE_MODE:#o} "
                f"(owner-only) — it holds user-authored memory text in plaintext "
                f"SQLite, got {_file_mode(ledger_path):#o}"
            )
            # Disclosure-bit boundary on the at-risk file specifically.
            assert _file_mode(ledger_path) & 0o077 == 0, (
                "the plaintext memory ledger must not grant any group/other access"
            )
        finally:
            ledger.close()
