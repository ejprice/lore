"""Contract tests for the *resilient local-DB open* slice (FP-01 + FP-08).

These tests define the behaviour of a feature that does NOT yet exist. They are
written BLIND to the eventual implementation: the expectations come from the
idempotent-startup requirement, never from how the current code happens to
behave. Every test is expected to be RED until the resilient-open work lands,
and it is RED *behaviourally* — the current code raises / wedges and an explicit
assertion catches that — NOT structurally (no missing-import / missing-attribute
errors: ``Manifest``, ``CodeGraph`` and ``build_app_context`` already exist and
import cleanly; we pin new behaviour onto those existing public constructors).

The two bugs this contract closes
---------------------------------

* **FP-01 — clean container wedge.** On a fresh deploy the state volume is empty,
  so ``_DEFAULT_MANIFEST_DIR`` does not exist. The server passes
  ``_DEFAULT_MANIFEST_DIR / f"{slug}.db"`` straight to ``Manifest(...)`` →
  ``sqlite3.connect`` which raises ``OperationalError: unable to open database
  file`` when the parent dir is absent (only the CLI ever ``mkdir``s it). The
  server can never start on a clean volume. Pinned end-state: opening a manifest
  / graph whose PARENT DIR is absent must SUCCEED, and ``build_app_context`` over
  a nonexistent state dir must not raise and must produce a working manifest +
  graph.

* **FP-08 — corruption wedge loop.** A corrupt / truncated ``<slug>.db`` (or
  ``<slug>.graph.db``) makes ``Manifest.__init__`` / ``CodeGraph.__init__`` raise
  ``sqlite3.DatabaseError: file is not a database`` on the first statement. There
  is NO integrity check / recovery, so EVERY startup re-wedges until a human
  deletes the file. Both DBs are REBUILDABLE (a fresh empty manifest → full
  reindex; a fresh graph → rebuilt by reindex), so the correct behaviour is
  delete-and-recreate. Pinned end-state: opening a corrupt manifest / graph must
  SUCCEED by detecting the corruption, deleting the bad file, and recreating a
  fresh empty DB; afterwards the DB is queryable (``all_files() == []`` / an
  empty graph) and a subsequent normal write works.

The critical anti-regression guard
-----------------------------------

A VALID existing DB must open UNCHANGED — its rows must survive. The recovery
path must not be over-eager and nuke a healthy database. ``test_healthy_*`` pins
this; without it a "recreate on every open" implementation would pass FP-08 while
silently destroying every real index.

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

How to run (worktree shadowing is REQUIRED — the venv lives in the sibling repo)::

    cd /home/ejprice/PycharmProjects/lore.worktrees/fix-idempotent
    PYTHONPATH=loremaster:loresigil:lorescribe \\
        /home/ejprice/PycharmProjects/lore/.venv/bin/python \\
        -m pytest loremaster/tests/test_resilient_db.py -q -p no:cacheprovider
"""

from __future__ import annotations

import os
import sqlite3
import stat
import textwrap
from pathlib import Path
from typing import Any

import pytest

# Production constructors under test — these EXIST and import cleanly today, so
# referencing them keeps the suite RED on *behaviour*, never on a missing symbol.
from loremaster.graph import CodeGraph
from loremaster.index.manifest import STATE_INDEXED, Manifest
from loremaster.index.sqlite_resilient import open_resilient_sqlite

# The real producer the indexer uses to derive graph chunks — grounds the
# "subsequent write works" assertion in the production chunk path (clause 1/5).
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker

# ---------------------------------------------------------------------------
# Production-realistic constants — same conventions as test_manifest.py /
# test_graph.py (clause 5: a single source of truth for domain conventions).
# ---------------------------------------------------------------------------

# The SQLite file header magic. A valid SQLite db ALWAYS begins with these exact
# 16 bytes; clobbering them is what makes the on-disk image "not a database".
# Pulled from the SQLite file-format spec, not from any lore code (independent).
_SQLITE_HEADER_MAGIC: bytes = b"SQLite format 3\x00"

# The on-disk file names the SERVER passes (server.py ~1904-1905): the manifest
# is ``<slug>.db`` and the graph ``<slug>.graph.db`` under the state dir. A
# realistic slug from a real lore.yaml deployment, not a ``foo`` placeholder.
_SLUG: str = "lore-loremaster"
_MANIFEST_FILENAME: str = f"{_SLUG}.db"
_GRAPH_FILENAME: str = f"{_SLUG}.graph.db"

# Representative manifest file-row values, mirroring test_manifest.py exactly so
# the "healthy DB survives" and "post-recovery write" rows are production-shaped
# (clause 1 + clause 5). A real sha512 is 128 hex chars; mtime_ns is a real
# nanosecond epoch; chunk_ids are real UUID4 point-ids.
_TIER: str = "custom"
_FILE_PATH: str = "src/pkg/mod.py"
_SHA512: str = "a" * 128
_MTIME_NS: int = 1_700_000_000_000_000_000
_SIZE_BYTES: int = 4096
_CHUNK_IDS: list[str] = [
    "11111111-1111-1111-1111-111111111111",
    "22222222-2222-2222-2222-222222222222",
]
_N_CHUNKS: int = len(_CHUNK_IDS)

# A real Python module the production PythonAstChunker splits into chunks — the
# graph's input lives at the lorescribe→loremaster producer↔consumer seam.
_GRAPH_TIER: str = "local"
_GRAPH_FILE_PATH: str = "demo/service.py"
_GRAPH_SOURCE: str = textwrap.dedent(
    '''\
    """A demo service module."""
    from __future__ import annotations

    import json


    class IndexService:
        """Indexes documents."""

        def boot(self, path):
            """Boot the service from a config file."""
            return json.loads(path)
    '''
)

# The embedder's ~4-chars-per-token stand-in and a real Voyage cap (clause 1).
_VOYAGE_MAX_INPUT_TOKENS: int = 8192


def _approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter (~4 cpt)."""
    return max(1, len(text) // 4)


def _graph_chunks() -> list[Chunk]:
    """Chunk the demo module through the REAL PythonAstChunker (clause 1/3 seam)."""
    context = ChunkContext(
        slug=_SLUG,
        file_path=_GRAPH_FILE_PATH,
        count_tokens=_approx_token_count,
        max_input_tokens=_VOYAGE_MAX_INPUT_TOKENS,
    )
    return PythonAstChunker().chunk(_GRAPH_SOURCE, context)


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
# FP-01 — absent parent dir must not wedge the open
# ---------------------------------------------------------------------------
class TestAbsentStateDirManifest:
    """FP-01: a Manifest opened under an absent parent dir must SUCCEED.

    On a clean container the state volume is empty, so the dir holding
    ``<slug>.db`` does not exist. ``sqlite3.connect`` cannot create a parent dir,
    so the open must create it (or the constructor must ``mkdir`` defensively).
    The end-state pinned here: the open does not raise and the manifest is a
    working, empty ledger.
    """

    def test_manifest_open_under_absent_parent_dir_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """Arrange: a manifest path under a state dir that does NOT exist.
        Act: construct a Manifest over it.
        Assert: construction succeeds (no OperationalError).
        """
        absent_state_dir = tmp_path / "state" / "lore"
        manifest_path = absent_state_dir / _MANIFEST_FILENAME
        # Precondition: the parent dir really is absent (this is the FP-01 trigger).
        assert not absent_state_dir.exists(), "fixture must start with an absent state dir"

        manifest: Manifest | None = None
        try:
            # Today this raises OperationalError: unable to open database file.
            manifest = Manifest(str(manifest_path))
        except sqlite3.OperationalError as error:
            pytest.fail(
                "Manifest over an absent parent dir must create the dir and open, "
                f"not raise OperationalError: {error}"
            )
        finally:
            if manifest is not None:
                manifest.close()

    def test_manifest_open_under_absent_parent_dir_yields_empty_queryable_ledger(
        self, tmp_path: Path
    ) -> None:
        """A freshly created manifest under an absent dir is an EMPTY working ledger.

        The end-state must be a usable manifest, not merely a non-raising open: a
        fresh ledger has zero file rows and accepts a normal write.
        """
        manifest_path = tmp_path / "state" / "lore" / _MANIFEST_FILENAME

        manifest = Manifest(str(manifest_path))
        try:
            # A brand-new manifest is empty (independent oracle: a fresh ledger
            # has indexed nothing yet — from the requirement, not the impl).
            assert manifest.all_files() == [], "a freshly created manifest must be empty"

            # And a subsequent normal write works end-to-end (the dir was created
            # and the schema is live).
            manifest.upsert(
                tier=_TIER,
                file_path=_FILE_PATH,
                sha512=_SHA512,
                mtime_ns=_MTIME_NS,
                size=_SIZE_BYTES,
                n_chunks=_N_CHUNKS,
                chunk_ids=_CHUNK_IDS,
                state=STATE_INDEXED,
            )
            rows = manifest.all_files()
            assert len(rows) == 1, "the post-create write must land exactly one row"
            assert rows[0].file_path == _FILE_PATH
            assert rows[0].chunk_ids == _CHUNK_IDS  # JSON round-trip survives
        finally:
            manifest.close()

    def test_manifest_open_actually_creates_the_missing_state_dir(
        self, tmp_path: Path
    ) -> None:
        """The recovery must materialise the missing dir AND the db file on disk.

        A side-effect assertion: after the open, both the parent dir and the db
        file exist — proving the dir was created, not merely that the open didn't
        raise.
        """
        state_dir = tmp_path / "state" / "lore"
        manifest_path = state_dir / _MANIFEST_FILENAME

        manifest = Manifest(str(manifest_path))
        try:
            assert state_dir.is_dir(), "the absent state dir must be created on open"
            assert manifest_path.is_file(), "the manifest db file must exist after open"
        finally:
            manifest.close()


class TestAbsentStateDirGraph:
    """FP-01: a CodeGraph opened under an absent parent dir must SUCCEED.

    Same clean-container failure as the manifest, on the ``<slug>.graph.db`` path.
    """

    def test_graph_open_under_absent_parent_dir_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """A CodeGraph over an absent parent dir must create the dir and open."""
        graph_path = tmp_path / "state" / "lore" / _GRAPH_FILENAME
        assert not graph_path.parent.exists(), "fixture must start with an absent state dir"

        graph: CodeGraph | None = None
        try:
            graph = CodeGraph(str(graph_path))
        except sqlite3.OperationalError as error:
            pytest.fail(
                "CodeGraph over an absent parent dir must create the dir and open, "
                f"not raise OperationalError: {error}"
            )
        finally:
            if graph is not None:
                graph.close()

    def test_graph_open_under_absent_parent_dir_yields_empty_queryable_graph(
        self, tmp_path: Path
    ) -> None:
        """A freshly created graph under an absent dir is EMPTY and queryable."""
        graph_path = tmp_path / "state" / "lore" / _GRAPH_FILENAME

        graph = CodeGraph(str(graph_path))
        try:
            # Empty via the public query API (independent of internal row counts):
            # nothing imports anything, nothing has a blast radius.
            assert graph.what_imports("json") == [], "a fresh graph imports nothing"
            assert graph.blast_radius("IndexService", depth=2, max_results=50) == [], (
                "a fresh graph has no reverse-dependency edges"
            )
        finally:
            graph.close()


# ---------------------------------------------------------------------------
# FP-08 — corrupt existing DB must self-heal (delete + recreate)
# ---------------------------------------------------------------------------
class TestCorruptManifestRecovers:
    """FP-08: a corrupt ``<slug>.db`` must be deleted and recreated, not raised.

    The current code raises ``sqlite3.DatabaseError`` on the first statement and
    every restart re-wedges. Because the manifest is rebuildable (a fresh empty
    ledger triggers a full reindex), the resilient open must detect the corruption
    (integrity check fails / open raises), delete the bad file, and recreate a
    fresh empty manifest that is immediately queryable and writable.
    """

    def test_corruption_fixture_genuinely_raises_on_raw_open(
        self, tmp_path: Path
    ) -> None:
        """RED witness: the fixture's malformed image really is a DatabaseError.

        Guards against a no-op corruption fixture (clause 2 tautology guard): if
        this passes, a later green on the resilient open means real recovery.
        """
        corrupt_path = tmp_path / _MANIFEST_FILENAME
        size = _write_corrupt_sqlite(corrupt_path)
        assert size > 0, "corruption fixture must be a NON-EMPTY malformed image"

        _assert_raises_on_raw_open(corrupt_path)

    def test_manifest_open_over_corrupt_file_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """Opening a Manifest over a corrupt file must recover, not raise."""
        corrupt_path = tmp_path / _MANIFEST_FILENAME
        _write_corrupt_sqlite(corrupt_path)
        _assert_raises_on_raw_open(corrupt_path)  # confirm it IS corrupt first

        manifest: Manifest | None = None
        try:
            # Today: sqlite3.DatabaseError "file is not a database".
            manifest = Manifest(str(corrupt_path))
        except sqlite3.DatabaseError as error:
            pytest.fail(
                "Manifest over a corrupt file must delete-and-recreate, "
                f"not raise DatabaseError: {error}"
            )
        finally:
            if manifest is not None:
                manifest.close()

    def test_manifest_recovered_from_corruption_is_empty_and_writable(
        self, tmp_path: Path
    ) -> None:
        """After recovery the manifest is a FRESH empty ledger that accepts writes.

        The recreated db must be queryable (``all_files() == []`` — the prior
        garbage is gone, not partially recovered) and a normal write must land.
        """
        corrupt_path = tmp_path / _MANIFEST_FILENAME
        _write_corrupt_sqlite(corrupt_path)

        manifest = Manifest(str(corrupt_path))
        try:
            assert manifest.all_files() == [], (
                "a manifest recreated from corruption must be a FRESH empty ledger"
            )
            manifest.upsert(
                tier=_TIER,
                file_path=_FILE_PATH,
                sha512=_SHA512,
                mtime_ns=_MTIME_NS,
                size=_SIZE_BYTES,
                n_chunks=_N_CHUNKS,
                chunk_ids=_CHUNK_IDS,
                state=STATE_INDEXED,
            )
            rows = manifest.all_files()
            assert len(rows) == 1, "a write after recovery must land exactly one row"
            assert rows[0].file_path == _FILE_PATH
        finally:
            manifest.close()


class TestCorruptGraphRecovers:
    """FP-08: a corrupt ``<slug>.graph.db`` must be deleted and recreated.

    Same self-heal contract for the code-graph, which is fully rebuildable by a
    reindex, so a fresh empty graph after recovery is correct.
    """

    def test_corruption_fixture_genuinely_raises_on_raw_open(
        self, tmp_path: Path
    ) -> None:
        """RED witness for the graph corruption fixture (clause 2 tautology guard)."""
        corrupt_path = tmp_path / _GRAPH_FILENAME
        size = _write_corrupt_sqlite(corrupt_path)
        assert size > 0, "corruption fixture must be a NON-EMPTY malformed image"
        _assert_raises_on_raw_open(corrupt_path)

    def test_graph_open_over_corrupt_file_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """Opening a CodeGraph over a corrupt file must recover, not raise."""
        corrupt_path = tmp_path / _GRAPH_FILENAME
        _write_corrupt_sqlite(corrupt_path)
        _assert_raises_on_raw_open(corrupt_path)

        graph: CodeGraph | None = None
        try:
            graph = CodeGraph(str(corrupt_path))
        except sqlite3.DatabaseError as error:
            pytest.fail(
                "CodeGraph over a corrupt file must delete-and-recreate, "
                f"not raise DatabaseError: {error}"
            )
        finally:
            if graph is not None:
                graph.close()

    def test_graph_recovered_from_corruption_is_empty_and_writable(
        self, tmp_path: Path
    ) -> None:
        """After recovery the graph is empty and accepts a real per-file build.

        The "subsequent normal write works" guarantee, exercised through the
        production producer↔consumer seam: real PythonAstChunker chunks → the
        recreated graph's ``build_file_graph`` → a query that finds the symbol.
        """
        corrupt_path = tmp_path / _GRAPH_FILENAME
        _write_corrupt_sqlite(corrupt_path)

        graph = CodeGraph(str(corrupt_path))
        try:
            # Fresh empty graph after recovery (public query API, no row peeking).
            assert graph.what_imports("json") == [], (
                "a graph recreated from corruption must start empty"
            )

            # A subsequent normal write works end-to-end across the seam.
            graph.build_file_graph(_GRAPH_TIER, _GRAPH_FILE_PATH, _graph_chunks())

            # The demo module imports ``json`` — after the build, the reverse
            # import edge must resolve (independent oracle: _GRAPH_SOURCE's own
            # ``import json`` statement, not the graph's internal counts).
            importers = graph.what_imports("json")
            assert importers, "the post-recovery build must register the json import edge"
            assert any(node.file_path == _GRAPH_FILE_PATH for node in importers), (
                "the importing module node must be the demo file we just built"
            )
        finally:
            graph.close()


# ---------------------------------------------------------------------------
# Anti-regression — a VALID existing DB must open UNCHANGED
# ---------------------------------------------------------------------------
class TestHealthyManifestSurvives:
    """The critical guard: a VALID manifest opens UNCHANGED — its rows survive.

    Without this guard a "recreate on every open" implementation would pass FP-08
    while silently destroying every real index on restart. We write a real row,
    close, reopen via the SAME resilient constructor, and assert the row is still
    there (NOT recreated). This is RED today only against a not-yet-existing
    recovery path that over-recreates; against the current code it passes — so it
    is the regression tripwire the GREEN phase must keep green while making the
    corruption tests pass.
    """

    def test_reopening_a_healthy_manifest_preserves_its_rows(
        self, tmp_path: Path
    ) -> None:
        """Arrange: a manifest with one real row, then closed.
        Act: reopen the same path via the resilient constructor.
        Assert: the row is still present (the open did NOT nuke a healthy db).
        """
        manifest_path = tmp_path / _MANIFEST_FILENAME

        seed = Manifest(str(manifest_path))
        seed.upsert(
            tier=_TIER,
            file_path=_FILE_PATH,
            sha512=_SHA512,
            mtime_ns=_MTIME_NS,
            size=_SIZE_BYTES,
            n_chunks=_N_CHUNKS,
            chunk_ids=_CHUNK_IDS,
            state=STATE_INDEXED,
        )
        seed.close()

        reopened = Manifest(str(manifest_path))
        try:
            rows = reopened.all_files()
            assert len(rows) == 1, (
                "a healthy manifest must reopen UNCHANGED — the row must survive, "
                "the resilient open must NOT recreate a valid db"
            )
            assert rows[0].file_path == _FILE_PATH
            assert rows[0].sha512 == _SHA512
            assert rows[0].chunk_ids == _CHUNK_IDS
            assert rows[0].state == STATE_INDEXED
        finally:
            reopened.close()


class TestHealthyGraphSurvives:
    """A VALID code-graph opens UNCHANGED — its nodes/edges survive a reopen."""

    def test_reopening_a_healthy_graph_preserves_its_edges(
        self, tmp_path: Path
    ) -> None:
        """A graph with a real import edge must reopen with that edge intact."""
        graph_path = tmp_path / _GRAPH_FILENAME

        seed = CodeGraph(str(graph_path))
        seed.build_file_graph(_GRAPH_TIER, _GRAPH_FILE_PATH, _graph_chunks())
        # Sanity: the seed graph really did register the json import edge.
        assert seed.what_imports("json"), "seed graph must have the json import edge"
        seed.close()

        reopened = CodeGraph(str(graph_path))
        try:
            importers = reopened.what_imports("json")
            assert importers, (
                "a healthy graph must reopen UNCHANGED — its import edge must "
                "survive, the resilient open must NOT recreate a valid db"
            )
            assert any(node.file_path == _GRAPH_FILE_PATH for node in importers)
        finally:
            reopened.close()


# ---------------------------------------------------------------------------
# Empty-file boundary — a zero-byte file is valid-and-fresh, NOT corruption
# ---------------------------------------------------------------------------
class TestEmptyFileIsNotCorruption:
    """Boundary: a ZERO-BYTE db file is valid-and-fresh — it must NOT be 'recovered'.

    The corruption detector must distinguish a malformed IMAGE (delete + recreate)
    from an empty file SQLite legitimately initialises in place. An over-eager
    detector that deletes empty files would churn on every fresh deploy. This is a
    sanity boundary on the FP-08 detector, not a recovery case.
    """

    def test_manifest_open_over_empty_file_is_a_plain_fresh_open(
        self, tmp_path: Path
    ) -> None:
        """A 0-byte manifest file opens as an empty ledger with no error or churn."""
        empty_path = tmp_path / _MANIFEST_FILENAME
        empty_path.write_bytes(b"")
        assert empty_path.stat().st_size == 0, "fixture must be a true zero-byte file"

        manifest = Manifest(str(empty_path))
        try:
            assert manifest.all_files() == [], "an empty file is a valid fresh manifest"
        finally:
            manifest.close()


# ---------------------------------------------------------------------------
# FP-01 at the SERVER seam — build_app_context over an absent state dir
# ---------------------------------------------------------------------------
#
# The unit-level Manifest/CodeGraph tests above pin the building blocks; this
# class pins the END-STATE the requirement actually cares about: the SERVER
# startup path (build_app_context) over a nonexistent state dir must not raise
# and must produce a working manifest + graph. It mirrors the hermetic harness
# in test_schema_rebuild.py (FakeEmbedder + a real throwaway Qdrant collection +
# tmp paths) so it drives the SAME construction path the server runs.
#
# Marked ``real-Qdrant``: build_app_context runs the probe gate + ensure_collection,
# which require a reachable Qdrant at conftest.QDRANT_URL with the API key. When
# Qdrant is unavailable the probe gate fails BEFORE the manifest/graph are built,
# so this case cannot witness the FP-01 fix — it is then xfail-skipped, and the
# unit-level absent-dir tests above remain the authoritative FP-01 coverage.
# ---------------------------------------------------------------------------
class TestBuildAppContextCreatesStateDir:
    """FP-01 server seam: build_app_context over an absent state dir must succeed."""

    @pytest.mark.asyncio
    async def test_build_app_context_under_absent_state_dir_does_not_raise(
        self, tmp_path: Path
    ) -> None:
        """Arrange: manifest_path/graph_path under a state dir that does NOT exist.
        Act: build_app_context with that path, a FakeEmbedder, a throwaway Qdrant.
        Assert: it does not raise, the manifest is empty/queryable, the graph empty.
        """
        # real-Qdrant — the probe gate + ensure_collection need a live Qdrant.
        from loremaster.server import LoreServer, build_app_context

        try:
            from conftest import QDRANT_URL, _qdrant_api_key
            from loresigil.testing import FakeEmbedder
            from qdrant_client import AsyncQdrantClient
        except Exception as import_error:  # pragma: no cover - harness wiring
            pytest.skip(f"hermetic Qdrant harness unavailable: {import_error}")

        config = _build_realistic_config(tmp_path)
        slug = config.project.slug

        # The state dir does NOT exist — this is the FP-01 clean-container trigger.
        absent_state_dir = tmp_path / "state" / "lore"
        manifest_path = absent_state_dir / f"{slug}.db"
        graph_path = absent_state_dir / f"{slug}.graph.db"
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
                    graph_path=graph_path,
                    snapshot_root=tmp_path / "snap",
                    start_tasks=False,
                )
            except sqlite3.OperationalError as error:
                pytest.fail(
                    "build_app_context over an absent state dir must mkdir the parent "
                    f"and build, not raise OperationalError: {error}"
                )

            # End-state: the manifest and graph files were created under the dir
            # that did not exist, and the manifest is a working empty ledger.
            assert absent_state_dir.is_dir(), "build_app_context must create the state dir"
            assert manifest_path.is_file(), "the manifest db must exist after startup"
            assert graph_path.is_file(), "the graph db must exist after startup"

            reread = Manifest(str(manifest_path))
            try:
                assert reread.all_files() == [], (
                    "a fresh-deploy manifest built under a created dir must be empty"
                )
            finally:
                reread.close()
        finally:
            if app_context is not None:
                await app_context.aclose()
            for name in created_collections:
                if await client.collection_exists(name):
                    await client.delete_collection(name)
            await client.close()


# The production embedding dimensionality used across the hermetic harnesses
# (matches test_schema_rebuild.py's _DIM — clause 5: same source of truth).
_CONFIG_DIM: int = 2048


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
    slug = f"test-{uuid.uuid4().hex}"
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

        real_connect = impl.sqlite3.connect
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

        monkeypatch.setattr(impl.sqlite3, "connect", _faulting_connect)


def _seed_healthy_manifest_row(db_path: Path) -> None:
    """Create a HEALTHY manifest with one real row, then close it.

    The pre-degradation healthy state: a valid db on disk holding data that MUST
    survive a transient blip on the next open.
    """
    seed = Manifest(str(db_path))
    seed.upsert(
        tier=_TIER,
        file_path=_FILE_PATH,
        sha512=_SHA512,
        mtime_ns=_MTIME_NS,
        size=_SIZE_BYTES,
        n_chunks=_N_CHUNKS,
        chunk_ids=_CHUNK_IDS,
        state=STATE_INDEXED,
    )
    seed.close()


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

    def test_locked_database_propagates_and_does_not_delete_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A "database is locked" blip on a healthy manifest must NOT nuke it.

        Arrange: a healthy manifest with one real row on disk.
        Act: open it again while the integrity probe raises OperationalR(locked).
        Assert: the OperationalError PROPAGATES (fail-closed) AND the file and its
                row survive (after the fault clears, the row is still there).
        """
        manifest_path = tmp_path / _MANIFEST_FILENAME
        _seed_healthy_manifest_row(manifest_path)
        size_before = manifest_path.stat().st_size

        injector = _IntegrityCheckFaultInjector(sqlite3.OperationalError(_LOCKED_MESSAGE))
        injector.install(monkeypatch)

        # Fail-closed: the transient OperationalError must propagate, not be
        # swallowed-then-delete. (Current impl swallows it → no raise → DELETE.)
        with pytest.raises(sqlite3.OperationalError, match="locked"):
            Manifest(str(manifest_path))

        assert injector.fired, "the injected integrity-probe fault must have fired"

        # The healthy db file must STILL EXIST — a transient blip never deletes.
        assert manifest_path.is_file(), (
            "a transient OperationalError must NOT delete a healthy manifest "
            "(the file was unlinked — data-loss bug)"
        )
        # And once the transient condition clears, the prior row is intact — the
        # data was never destroyed (not merely "a file exists", but the SAME data).
        monkeypatch.undo()
        recovered = Manifest(str(manifest_path))
        try:
            rows = recovered.all_files()
            assert len(rows) == 1, (
                "the healthy manifest row must SURVIVE a transient blip "
                "(it was deleted/recreated empty — data-loss bug)"
            )
            assert rows[0].file_path == _FILE_PATH
            assert rows[0].sha512 == _SHA512
            assert rows[0].chunk_ids == _CHUNK_IDS
        finally:
            recovered.close()
        assert manifest_path.stat().st_size >= size_before, (
            "the recovered db must be at least as large as before — not a fresh empty one"
        )

    def test_disk_io_error_propagates_and_does_not_delete_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A "disk I/O error" blip on a healthy manifest must NOT nuke it."""
        manifest_path = tmp_path / _MANIFEST_FILENAME
        _seed_healthy_manifest_row(manifest_path)

        injector = _IntegrityCheckFaultInjector(sqlite3.OperationalError(_DISK_IO_MESSAGE))
        injector.install(monkeypatch)

        with pytest.raises(sqlite3.OperationalError):
            Manifest(str(manifest_path))

        assert manifest_path.is_file(), (
            "a transient disk-IO OperationalError must NOT delete a healthy manifest"
        )
        monkeypatch.undo()
        recovered = Manifest(str(manifest_path))
        try:
            assert len(recovered.all_files()) == 1, "the row must survive a disk-IO blip"
        finally:
            recovered.close()

    def test_readonly_filesystem_propagates_and_does_not_delete_graph(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A read-only-FS OperationalError on a healthy CodeGraph must NOT nuke it.

        The graph carries the same fail-closed contract: a transient probe fault
        on a healthy graph must propagate and leave the file (and its edges)
        intact. Exercised through the real lorescribe→loremaster chunk seam.
        """
        graph_path = tmp_path / _GRAPH_FILENAME
        seed = CodeGraph(str(graph_path))
        seed.build_file_graph(_GRAPH_TIER, _GRAPH_FILE_PATH, _graph_chunks())
        assert seed.what_imports("json"), "seed graph must carry the json import edge"
        seed.close()

        injector = _IntegrityCheckFaultInjector(sqlite3.OperationalError(_READONLY_MESSAGE))
        injector.install(monkeypatch)

        with pytest.raises(sqlite3.OperationalError):
            CodeGraph(str(graph_path))

        assert graph_path.is_file(), (
            "a transient readonly-FS OperationalError must NOT delete a healthy graph"
        )
        monkeypatch.undo()
        recovered = CodeGraph(str(graph_path))
        try:
            assert recovered.what_imports("json"), (
                "the graph's import edge must SURVIVE a transient blip (not recreated empty)"
            )
        finally:
            recovered.close()

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


class TestGenuineCorruptionStillRecreates:
    """The other side of the contract: GENUINE corruption STILL deletes+recreates.

    Narrowing the catch must not regress FP-08. A plain ``DatabaseError`` that is
    NOT an ``OperationalError`` (the malformed-image / "file is not a database"
    signal), or non-"ok" integrity rows, must still delete-and-recreate. The first
    test injects a plain non-operational DatabaseError on the probe (the cleanest
    class distinction); the second confirms a real malformed image on disk still
    recreates (the end-to-end FP-08 path).
    """

    def test_non_operational_database_error_on_probe_still_recreates_manifest(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A plain DatabaseError (NOT OperationalError) on the probe → recreate.

        This is the genuine-corruption class. The seed row must be GONE (the db was
        deleted and recreated empty) — proving the narrowed catch still recovers
        true corruption, distinguished from the transient case purely by the
        exception class on the SAME seam.
        """
        manifest_path = tmp_path / _MANIFEST_FILENAME
        _seed_healthy_manifest_row(manifest_path)

        # A plain DatabaseError — NOT an OperationalError. This is what a malformed
        # header raises; isinstance(error, OperationalError) is False (audited).
        corruption_error = sqlite3.DatabaseError("file is not a database")
        assert not isinstance(corruption_error, sqlite3.OperationalError), (
            "fixture must be a NON-operational DatabaseError (the corruption class)"
        )
        injector = _IntegrityCheckFaultInjector(corruption_error)
        injector.install(monkeypatch)

        # Genuine corruption recreates — construction must SUCCEED (no raise).
        manifest = Manifest(str(manifest_path))
        try:
            assert injector.fired, "the injected probe fault must have fired"
            assert manifest.all_files() == [], (
                "genuine corruption must delete-and-recreate a FRESH empty manifest "
                "(the seed row must be gone)"
            )
        finally:
            manifest.close()

    def test_malformed_image_on_disk_still_recreates_manifest(
        self, tmp_path: Path
    ) -> None:
        """End-to-end FP-08: a real malformed image on disk still recreates empty.

        No monkeypatch — a genuine non-empty malformed file. Confirms the
        unpatched recovery path is unchanged by the transient-case narrowing.
        """
        corrupt_path = tmp_path / _MANIFEST_FILENAME
        _write_corrupt_sqlite(corrupt_path)
        _assert_raises_on_raw_open(corrupt_path)  # RED witness: it IS corrupt

        manifest = Manifest(str(corrupt_path))
        try:
            assert manifest.all_files() == [], (
                "a real malformed image must still delete-and-recreate a fresh empty db"
            )
        finally:
            manifest.close()


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
# through the REAL production constructors (Manifest / CodeGraph / MemoryLedger),
# not only the bare helper, so the guarantee covers the path the server runs
# (clause 3/4: the production open seam, with the memory ledger as the at-risk
# artifact).
#
# These mode assertions are BEHAVIOURALLY RED today: a default-mode connect yields
# 0o644, which ``== 0o600`` and ``& 0o077 == 0`` both reject. They are NOT
# structurally red — ``open_resilient_sqlite`` / ``Manifest`` / ``CodeGraph`` /
# ``MemoryLedger`` all exist and import cleanly; only the FILE permission is wrong.
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


def _make_world_readable_healthy_manifest(db_path: Path) -> None:
    """Write a HEALTHY manifest with one real row, then ``chmod`` it world-readable.

    Reproduces the production pre-condition this fix retro-tightens: a valid db
    file left at 0o644 by a prior default-mode build, holding real data that MUST
    survive the next (tightening) open. Uses the same production-shaped row as the
    other healthy fixtures (clause 1/5).
    """
    _seed_healthy_manifest_row(db_path)
    os.chmod(db_path, _WORLD_READABLE_FILE_MODE)
    # Precondition guard: the fixture really starts world-readable, so a later
    # 0o600 assertion proves the open TIGHTENED it (not that it was already tight).
    assert _file_mode(db_path) == _WORLD_READABLE_FILE_MODE, (
        "fixture must start at 0o644 (a prior default-mode build's world-readable file)"
    )


class TestDatabaseFilesAreOwnerOnly:
    """SECURITY: a DB file the resilient open creates/opens is mode 0o600 (owner-only).

    The dir-0700 hardening protects the directory; this guards the FILE. The
    plaintext memory ledger ``<slug>.memory.db`` and the manifest must be owner-rw
    only — never group/world-readable — on both a freshly created file and an
    existing world-readable one (the deploy-time tighten guarantee). Pinned both at
    the bare ``open_resilient_sqlite`` helper and through the real Manifest /
    CodeGraph / MemoryLedger production constructors.
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
        contract (TestHealthyManifestSurvives) and this tighten contract must hold
        together: the chmod must not trip the resilient open into a delete/recreate.

        Arrange: a healthy manifest with one real row, chmod'd to 0o644.
        Act: open it again via the bare resilient helper.
        Assert: the file is now 0o600 AND its row survived (not recreated empty).
        """
        db_path = tmp_path / _MANIFEST_FILENAME
        _make_world_readable_healthy_manifest(db_path)

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
        # Read back through the production Manifest constructor (the consumer that
        # interprets the bytes), proving the row is the SAME data, not a fresh empty
        # ledger (the anti-regression seam: tighten ≠ delete-recreate).
        reopened = Manifest(str(db_path))
        try:
            rows = reopened.all_files()
            assert len(rows) == 1, (
                "tightening an existing healthy db must NOT delete it — the row "
                "must survive (the 0o600 chmod must not trip the resilient recreate)"
            )
            assert rows[0].file_path == _FILE_PATH
            assert rows[0].sha512 == _SHA512
            assert rows[0].chunk_ids == _CHUNK_IDS
        finally:
            reopened.close()

    def test_manifest_constructor_yields_owner_only_db_file(self, tmp_path: Path) -> None:
        """A db file created through the real ``Manifest(path)`` is 0o600.

        Pins the hardening through the PRODUCTION open path, not only the bare
        helper — Manifest.__init__ calls open_resilient_sqlite, so the server's
        manifest db must land owner-only (clause 3/4: the real consumer seam).
        """
        manifest_path = tmp_path / "state" / "lore" / _MANIFEST_FILENAME

        manifest = Manifest(str(manifest_path))
        try:
            assert _file_mode(manifest_path) == _OWNER_ONLY_FILE_MODE, (
                f"a Manifest-created db file must be {_OWNER_ONLY_FILE_MODE:#o} "
                f"(owner-only), got {_file_mode(manifest_path):#o}"
            )
        finally:
            manifest.close()

    def test_graph_constructor_yields_owner_only_db_file(self, tmp_path: Path) -> None:
        """A db file created through the real ``CodeGraph(path)`` is 0o600.

        The graph db carries the same open path; pinning it confirms the hardening
        is in open_resilient_sqlite (shared by both constructors), not bolted onto
        one caller (clause 3/4: the production open seam, second consumer).
        """
        graph_path = tmp_path / "state" / "lore" / _GRAPH_FILENAME

        graph = CodeGraph(str(graph_path))
        try:
            assert _file_mode(graph_path) == _OWNER_ONLY_FILE_MODE, (
                f"a CodeGraph-created db file must be {_OWNER_ONLY_FILE_MODE:#o} "
                f"(owner-only), got {_file_mode(graph_path):#o}"
            )
        finally:
            graph.close()

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
