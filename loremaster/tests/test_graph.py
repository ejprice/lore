"""Contract tests for ``loremaster.graph.CodeGraph`` — the typed code-graph.

The code-graph is a SQLite **side-structure** (NO new vector index) derived
from the AST chunks lorescribe's :class:`~lorescribe.python_ast.PythonAstChunker`
emits. It is generic over *any* Python AST chunks (zero Odoo) and is kept fresh
by a transactional per-file rebuild (delete + rebuild) so the live watcher /
reconcile pass can refresh one file at a time.

The contract pinned here, from the feature spec (NOT from any implementation —
``loremaster.graph`` does not exist when these tests are written):

Schema
------
Two tables, real SQLite (a path or connection is injected; WAL is enabled):

* ``nodes(id, kind, qualified_name, file_path, chunk_id, tier)`` — one row per
  graph node. ``kind ∈ {module, class, method, function}``. ``qualified_name``
  is the dotted identity (``mod``, ``mod.Settings``, ``mod.Settings.from_file``,
  ``mod.helper``). ``chunk_id`` is the originating chunk's identity (the
  within-file natural key) or ``None`` for a synthesised module node.
* ``edges(src, dst, kind)`` — one row per directed edge.
  ``kind ∈ {imports, calls, inherits, defines}``.

Edge derivation (exactly what the python_ast chunks expose)
-----------------------------------------------------------
* ``defines`` — module → class, module → top-level function, class → method.
  Derived from the chunk set's structure (``class`` / ``method`` / ``function``
  chunk types and their ``class_name`` metadata). FULLY derivable.
* ``inherits`` — class → each base-class name, from the ``class`` chunk's
  ``inherits`` metadata list. FULLY derivable (the bases the AST captured as
  bare ``ast.Name`` — dotted bases like ``ast.NodeVisitor`` are not captured by
  the chunker and so are not asserted).
* ``imports`` — module → each imported module/name, parsed from the ``imports``
  chunk's ``source_text`` (the raw import statements; the chunker does not put
  the imported names in metadata, so they are re-parsed from source). FULLY
  derivable.
* ``calls`` — caller (method/function) → callee name, parsed BEST-EFFORT from
  the method/function chunk's ``source_text`` (``ast.Call`` with a ``Name`` or
  ``Attribute`` func). Best-effort: a call edge's ``dst`` is the called *name*
  (``loads``, ``json.loads``) — it is NOT resolved to a defining node, because
  the chunk set for one file cannot resolve a cross-module callee. The contract
  asserts a call edge exists for a call that is unambiguously present in source.

Query functions
----------------
* ``what_imports(target)`` — every module node with an ``imports`` edge whose
  ``dst`` matches ``target`` (the reverse of the import edge). Returns the
  importing module nodes.
* ``blast_radius(target, depth, max_results)`` — the reverse-edge transitive
  closure from ``target``: everything that (transitively) depends on ``target``
  via ANY edge kind, walking edges backwards (``dst`` matches the frontier).
  BOUNDED: never descends past ``depth`` hops, and never returns more than
  ``max_results`` nodes — a huge fan-out must not blow up. **Name-matching
  seam:** edge ``dst`` lands at the resolution the AST exposed — ``defines``
  stores a fully-qualified ``dst``, but ``inherits`` / ``calls`` / ``imports``
  store the bare-ish name the source carried (``BaseService``, ``load_config``,
  ``json``). So the frontier matches an edge whose ``dst`` equals EITHER the
  node's qualified name OR its bare (last-dotted-segment) name; this is what
  lets a reverse ``inherits`` hop (``dst == "BaseService"``) connect to the
  qualified ``demo.service.BaseService`` node.
* ``tests_for(symbol_or_file)`` — test nodes related to the target. A node is a
  test node when its ``file_path`` matches a test glob (``test_*.py`` /
  ``*_test.py`` / under a ``tests/`` dir). It is returned when EITHER it has an
  edge to the target OR the ``test_x`` ↔ ``x`` name heuristic links it (a test
  function ``test_foo`` is a test for symbol ``foo``).

Adversarial pre-flight (each item maps to a covering case or a scoped-out note)
is recorded in the final report, not here.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# Target module under contract: ``CodeGraph`` is the unit being defined. It does
# not exist yet — these names ARE the contract.
from loremaster.graph import (
    EDGE_CALLS,
    EDGE_DEFINES,
    EDGE_IMPORTS,
    EDGE_INHERITS,
    KIND_CLASS,
    KIND_FUNCTION,
    KIND_METHOD,
    KIND_MODULE,
    CodeGraph,
)
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker

# ---------------------------------------------------------------------------
# Real fixtures: production-realistic Python sources chunked via the REAL
# PythonAstChunker (clause 1 + clause 3 — the producer↔consumer seam). The graph
# consumes exactly what the chunker emits; hand-rolling Chunk objects would let a
# chunker-shape drift slip past, so we drive the real chunker.
# ---------------------------------------------------------------------------

# Hard token cap from the embedder spec — over-length inputs are rejected, never
# truncated. Used as the ChunkContext cap so chunking matches production.
VOYAGE4_MAX_INPUT_TOKENS: int = 8192

SAMPLE_SLUG: str = "demo-project"
SAMPLE_TIER: str = "local"
OTHER_TIER: str = "community"

# A realistic application module: imports, a base class, a subclass that inherits
# from it AND calls a top-level helper, plus a module-level function. Dedented to
# column 0 so AST line/identity assertions hold.
APP_SOURCE: str = textwrap.dedent(
    '''\
    """A small but realistic service module."""
    from __future__ import annotations

    import json
    from pathlib import Path

    from demo.errors import LoadError


    def load_config(path):
        """Module-level helper: read and parse a config file."""
        return json.loads(Path(path).read_text())


    class BaseService:
        """Common service plumbing."""

        def start(self):
            """Start the service."""
            return True


    class IndexService(BaseService):
        """Indexes documents; inherits plumbing from BaseService."""

        def boot(self, path):
            """Boot the service from a config file."""
            config = load_config(path)
            return self.start()
    '''
)

# A realistic test module exercising ``IndexService`` — its file path matches the
# test glob, and ``test_boot`` references ``boot`` (the test_x ↔ x heuristic) and
# imports the app module (an import edge to the target).
TEST_SOURCE: str = textwrap.dedent(
    '''\
    """Tests for the index service."""
    from __future__ import annotations

    from demo.service import IndexService


    def test_boot():
        """A test that boots the service."""
        service = IndexService()
        return service.boot("/tmp/config.json")
    '''
)

# Tier-relative file paths (POSIX), as the indexer stores them.
APP_PATH: str = "demo/service.py"
TEST_PATH: str = "tests/test_service.py"


def approx_token_count(text: str) -> int:
    """Behavioural stand-in for the embedder's injected token counter (~4 cpt)."""
    return max(1, len(text) // 4)


def _chunk(path: str, source: str) -> list[Chunk]:
    """Chunk ``source`` through the REAL PythonAstChunker (the production producer)."""
    ctx = ChunkContext(
        slug=SAMPLE_SLUG,
        file_path=path,
        count_tokens=approx_token_count,
        max_input_tokens=VOYAGE4_MAX_INPUT_TOKENS,
    )
    return PythonAstChunker().chunk(source, ctx)


@pytest.fixture()
def graph(tmp_path) -> CodeGraph:  # type: ignore[no-untyped-def]
    """A CodeGraph backed by a real on-disk SQLite file (WAL is meaningless for :memory:)."""
    db_path = tmp_path / "graph.db"
    return CodeGraph(str(db_path))


@pytest.fixture()
def app_chunks() -> list[Chunk]:
    """The real chunk set for the application module."""
    return _chunk(APP_PATH, APP_SOURCE)


@pytest.fixture()
def test_chunks() -> list[Chunk]:
    """The real chunk set for the test module."""
    return _chunk(TEST_PATH, TEST_SOURCE)


class TestSchemaAndConstruction:
    """The graph is a real WAL SQLite side-structure with the documented schema."""

    def test_creates_nodes_and_edges_tables(self, graph: CodeGraph) -> None:
        """A fresh graph has exactly the ``nodes`` and ``edges`` tables."""
        names = {
            row[0]
            for row in graph.connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        assert {"nodes", "edges"} <= names

    def test_nodes_table_has_documented_columns(self, graph: CodeGraph) -> None:
        """The ``nodes`` table carries id, kind, qualified_name, file_path, chunk_id, tier."""
        columns = {
            row[1] for row in graph.connection.execute("PRAGMA table_info(nodes)").fetchall()
        }
        assert {"id", "kind", "qualified_name", "file_path", "chunk_id", "tier"} <= columns

    def test_edges_table_has_documented_columns(self, graph: CodeGraph) -> None:
        """The ``edges`` table carries src, dst, kind."""
        columns = {
            row[1] for row in graph.connection.execute("PRAGMA table_info(edges)").fetchall()
        }
        assert {"src", "dst", "kind"} <= columns

    def test_enables_wal_journal_mode(self, graph: CodeGraph) -> None:
        """WAL is enabled so readers (MCP graph lookups) never block the writer."""
        mode = graph.connection.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"


class TestBuildFileGraphNodes:
    """``build_file_graph`` derives the right node set from real AST chunks."""

    def test_synthesises_a_module_node(self, graph: CodeGraph, app_chunks: list[Chunk]) -> None:
        """A file yields exactly one ``module`` node, qualified from its path."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        modules = graph.connection.execute(
            "SELECT qualified_name, tier, file_path FROM nodes WHERE kind = ?",
            (KIND_MODULE,),
        ).fetchall()
        assert len(modules) == 1
        # The module qualified name is the dotted path sans the .py suffix.
        assert modules[0][0] == "demo.service"
        assert modules[0][1] == SAMPLE_TIER
        assert modules[0][2] == APP_PATH

    def test_creates_a_class_node_per_class(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level class becomes a ``class`` node with a dotted qualified name."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        class_names = {
            row[0]
            for row in graph.connection.execute(
                "SELECT qualified_name FROM nodes WHERE kind = ?", (KIND_CLASS,)
            ).fetchall()
        }
        assert class_names == {"demo.service.BaseService", "demo.service.IndexService"}

    def test_creates_a_method_node_per_method(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each method becomes a ``method`` node qualified by its class."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        method_names = {
            row[0]
            for row in graph.connection.execute(
                "SELECT qualified_name FROM nodes WHERE kind = ?", (KIND_METHOD,)
            ).fetchall()
        }
        assert method_names == {
            "demo.service.BaseService.start",
            "demo.service.IndexService.boot",
        }

    def test_creates_a_function_node_per_top_level_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level function becomes a ``function`` node."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        function_names = {
            row[0]
            for row in graph.connection.execute(
                "SELECT qualified_name FROM nodes WHERE kind = ?", (KIND_FUNCTION,)
            ).fetchall()
        }
        assert function_names == {"demo.service.load_config"}


class TestBuildFileGraphEdges:
    """``build_file_graph`` derives the four documented edge kinds from real chunks."""

    def test_defines_edges_module_to_class_and_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The module ``defines`` each top-level class and function."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        defined = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ? AND src = ?",
                (EDGE_DEFINES, "demo.service"),
            ).fetchall()
        }
        # The module defines both classes and the top-level helper (NOT the
        # methods — a method is defined by its class, not the module).
        assert defined == {
            "demo.service.BaseService",
            "demo.service.IndexService",
            "demo.service.load_config",
        }

    def test_defines_edges_class_to_its_methods(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A class ``defines`` exactly its own methods."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        defined_by_index = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ? AND src = ?",
                (EDGE_DEFINES, "demo.service.IndexService"),
            ).fetchall()
        }
        assert defined_by_index == {"demo.service.IndexService.boot"}

    def test_inherits_edge_from_metadata(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """``IndexService`` ``inherits`` from the base name the chunk metadata captured."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        bases = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ? AND src = ?",
                (EDGE_INHERITS, "demo.service.IndexService"),
            ).fetchall()
        }
        # The base is the bare name the AST captured (``BaseService``); the graph
        # does not fabricate a dotted resolution it cannot prove.
        assert "BaseService" in bases

    def test_imports_edges_parsed_from_imports_chunk_source(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """``imports`` edges are parsed from the imports chunk's raw source text.

        The chunker stores the imported names ONLY in the imports chunk's
        ``source_text`` (metadata carries none), so the graph must re-parse them.
        The module imports ``json``, ``pathlib`` (``from pathlib import Path``),
        and ``demo.errors`` (``from demo.errors import LoadError``); ``__future__``
        is a compiler directive, scoped out below.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        imported = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ? AND src = ?",
                (EDGE_IMPORTS, "demo.service"),
            ).fetchall()
        }
        # Independent oracle: read straight off the source's import statements.
        assert "json" in imported
        assert "pathlib" in imported
        assert "demo.errors" in imported

    def test_calls_edge_best_effort_from_function_source(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A ``calls`` edge is parsed best-effort from the caller's source text.

        ``IndexService.boot`` calls ``load_config(path)`` — an unambiguous
        ``ast.Call`` with a ``Name`` func in the method body. The edge's ``dst``
        is the called NAME (best-effort, not resolved to the defining node).
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        called = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ? AND src = ?",
                (EDGE_CALLS, "demo.service.IndexService.boot"),
            ).fetchall()
        }
        # ``load_config`` is called by name in the body — the canonical best-effort
        # call. (``self.start()`` is an attribute call; ``json.loads`` lives in the
        # helper, not boot — neither is required by this assertion.)
        assert "load_config" in called


class TestPerFileRebuildTransactional:
    """A per-file rebuild (delete + rebuild) leaves correct state and NO orphans."""

    def test_rebuild_replaces_nodes_no_duplicates(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Building the same file twice does not double its nodes."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        first = graph.connection.execute(
            "SELECT COUNT(*) FROM nodes WHERE tier = ? AND file_path = ?",
            (SAMPLE_TIER, APP_PATH),
        ).fetchone()[0]
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        second = graph.connection.execute(
            "SELECT COUNT(*) FROM nodes WHERE tier = ? AND file_path = ?",
            (SAMPLE_TIER, APP_PATH),
        ).fetchone()[0]
        assert first == second
        assert first > 0  # sanity: the file actually produced nodes

    def test_rebuild_after_edit_drops_removed_symbols(self, graph: CodeGraph) -> None:
        """Editing a file to remove a class drops that class's nodes and edges.

        This is the freshness contract: a delete + rebuild must leave NO orphan
        edges pointing at a symbol that no longer exists in the file.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE))
        # Edit: a trimmed module with only the helper, no classes at all.
        trimmed = textwrap.dedent(
            '''\
            """Trimmed: only the helper survives."""
            import json


            def load_config(path):
                """Read and parse a config file."""
                return json.loads(path)
            '''
        )
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, trimmed))
        remaining = {
            row[0]
            for row in graph.connection.execute(
                "SELECT qualified_name FROM nodes WHERE tier = ? AND file_path = ?",
                (SAMPLE_TIER, APP_PATH),
            ).fetchall()
        }
        # The removed classes/methods are gone; the helper and module survive.
        assert "demo.service.IndexService" not in remaining
        assert "demo.service.BaseService.start" not in remaining
        assert "demo.service.load_config" in remaining
        # No orphan inherits edge to the deleted subclass survives.
        orphan_inherits = graph.connection.execute(
            "SELECT COUNT(*) FROM edges WHERE kind = ? AND src = ?",
            (EDGE_INHERITS, "demo.service.IndexService"),
        ).fetchone()[0]
        assert orphan_inherits == 0

    def test_delete_file_graph_removes_all_rows(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """``delete_file_graph`` removes every node and edge for that (tier, file)."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        graph.delete_file_graph(SAMPLE_TIER, APP_PATH)
        node_count = graph.connection.execute(
            "SELECT COUNT(*) FROM nodes WHERE tier = ? AND file_path = ?",
            (SAMPLE_TIER, APP_PATH),
        ).fetchone()[0]
        assert node_count == 0
        # And the file's own edges are gone (its module/class/method srcs removed).
        edge_count = graph.connection.execute(
            "SELECT COUNT(*) FROM edges WHERE src LIKE 'demo.service%'"
        ).fetchone()[0]
        assert edge_count == 0

    def test_delete_is_tier_scoped(self, graph: CodeGraph, app_chunks: list[Chunk]) -> None:
        """Deleting one tier's copy of a path leaves another tier's copy intact (C1)."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        graph.build_file_graph(OTHER_TIER, APP_PATH, app_chunks)
        graph.delete_file_graph(SAMPLE_TIER, APP_PATH)
        surviving = graph.connection.execute(
            "SELECT COUNT(*) FROM nodes WHERE tier = ? AND file_path = ?",
            (OTHER_TIER, APP_PATH),
        ).fetchone()[0]
        assert surviving > 0


class TestWhatImports:
    """``what_imports`` reverses the import edge: who pulls in a target?"""

    def test_returns_modules_that_import_target(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The app module imports ``demo.errors``; ``what_imports`` finds it."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        importers = graph.what_imports("demo.errors")
        # The result names the importing module (by qualified name).
        importer_names = {node.qualified_name for node in importers}
        assert "demo.service" in importer_names

    def test_returns_empty_for_unimported_target(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A target nobody imports yields an empty result, not an error."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        assert list(graph.what_imports("nonexistent.module")) == []


class TestBlastRadius:
    """``blast_radius`` is a BOUNDED reverse-edge transitive closure."""

    def test_finds_direct_reverse_dependents(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A symbol's direct dependents (one hop back) are in its blast radius.

        ``IndexService`` inherits from ``BaseService`` (edge
        IndexService -inherits-> BaseService). The blast radius of
        ``BaseService`` therefore includes ``IndexService`` (a reverse hop).
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        affected = {
            node.qualified_name
            for node in graph.blast_radius(
                "demo.service.BaseService", depth=3, max_results=100
            )
        }
        assert "demo.service.IndexService" in affected

    def test_respects_depth_bound(self, graph: CodeGraph) -> None:
        """A deep dependency chain is truncated at ``depth`` hops, never beyond.

        Build a synthetic linear chain longer than the depth bound by editing the
        source into a chain of N classes each inheriting the previous, then assert
        the closure from the chain's root stops exactly at ``depth`` reverse hops.
        """
        chain_length = 8
        depth_bound = 3
        # n0 is the base; n1 inherits n0; n2 inherits n1; ... a linear chain so
        # the reverse closure depth equals the hop distance from n0 exactly.
        lines = ['"""A deep linear inheritance chain."""', "", "", "class N0:", "    pass", ""]
        for index in range(1, chain_length):
            lines += ["", f"class N{index}(N{index - 1}):", "    pass", ""]
        chain_source = "\n".join(lines) + "\n"
        chain_path = "demo/chain.py"
        graph.build_file_graph(SAMPLE_TIER, chain_path, _chunk(chain_path, chain_source))

        affected = {
            node.qualified_name
            for node in graph.blast_radius(
                "demo.chain.N0", depth=depth_bound, max_results=1000
            )
        }
        # Within ``depth_bound`` reverse hops of N0 we reach N1..N{depth_bound};
        # N{depth_bound+1} and beyond are STRICTLY past the bound.
        assert "demo.chain.N1" in affected  # 1 hop
        assert f"demo.chain.N{depth_bound}" in affected  # exactly at the bound
        assert f"demo.chain.N{depth_bound + 1}" not in affected  # beyond the bound
        assert f"demo.chain.N{chain_length - 1}" not in affected  # far beyond

    def test_respects_max_results_cap(self, graph: CodeGraph) -> None:
        """A huge fan-out is capped at ``max_results`` — the closure cannot blow up.

        Build a star: N classes all inheriting one base. The base's reverse
        closure has N dependents; the cap must clamp the returned set so a
        pathological fan-out is bounded.
        """
        fan_out = 200
        cap = 25
        lines = ['"""A wide fan-out: many subclasses of one base."""', "", "class Hub:", "    pass", ""]
        for index in range(fan_out):
            lines += ["", f"class Leaf{index}(Hub):", "    pass", ""]
        star_source = "\n".join(lines) + "\n"
        star_path = "demo/star.py"
        graph.build_file_graph(SAMPLE_TIER, star_path, _chunk(star_path, star_source))

        affected = list(graph.blast_radius("demo.star.Hub", depth=5, max_results=cap))
        # The cap is a hard ceiling: never more than ``cap`` results even though
        # ``fan_out`` (200) dependents exist.
        assert len(affected) <= cap
        # And it actually found dependents (not empty) — the cap clamps, not zeroes.
        assert len(affected) > 0


class TestTestsFor:
    """``tests_for`` links test nodes to a target by edge OR the name heuristic."""

    def test_finds_test_by_import_edge(
        self,
        graph: CodeGraph,
        app_chunks: list[Chunk],
        test_chunks: list[Chunk],
    ) -> None:
        """A test module importing the target's module is a test for it.

        ``tests/test_service.py`` imports ``demo.service`` (``from demo.service
        import IndexService``). It is a test-glob path with an import edge to the
        target module, so it is a test for ``demo.service``.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        graph.build_file_graph(SAMPLE_TIER, TEST_PATH, test_chunks)
        related = graph.tests_for("demo.service")
        related_files = {node.file_path for node in related}
        assert TEST_PATH in related_files

    def test_finds_test_by_name_heuristic(
        self,
        graph: CodeGraph,
        app_chunks: list[Chunk],
        test_chunks: list[Chunk],
    ) -> None:
        """``test_boot`` is linked to symbol ``boot`` by the test_x ↔ x heuristic.

        The app defines ``IndexService.boot``; the test file defines
        ``test_boot``. Asked for tests of the symbol whose bare name is ``boot``,
        the name heuristic returns the ``test_boot`` node.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        graph.build_file_graph(SAMPLE_TIER, TEST_PATH, test_chunks)
        related = graph.tests_for("demo.service.IndexService.boot")
        related_names = {node.qualified_name for node in related}
        # The test function ``test_boot`` is surfaced for the ``boot`` symbol.
        assert any(name.endswith("test_boot") for name in related_names)

    def test_does_not_return_non_test_nodes(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """With no test file indexed, a symbol has no tests — non-test nodes excluded.

        ``BaseService`` is defined and depended upon, but no test-glob file
        references it, so ``tests_for`` returns nothing — it must not leak the
        ordinary application nodes that merely have edges.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks)
        related = list(graph.tests_for("demo.service.BaseService"))
        assert related == []


class TestImportableModuleName:
    """``importable_module_name`` derives the TRUE importable dotted path.

    The bug this pins: the old ``module_qualified_name`` joined EVERY segment of
    the tier-relative path, so a workspace-member layout
    (``loremaster/loremaster/config.py`` under repo root) produced the DOUBLED
    name ``loremaster.loremaster.config`` — a module that is not importable and
    that never matches the import-edge ``dst`` strings (the real import
    ``loremaster.config``). The fix strips leading path segments up to the top of
    the package: the shallowest directory in the chain that contains an
    ``__init__.py`` is the package top; everything to its left is dropped.
    """

    def _make_pkg(self, base: Path) -> Path:
        """Create the doubled-layout fixture package on disk under ``base``.

        ``base/loremaster/loremaster/config.py`` where ``loremaster/`` has NO
        ``__init__.py`` but ``loremaster/loremaster/`` does — exactly the
        workspace-member layout that triggered the split-brain bug.
        """
        inner = base / "loremaster" / "loremaster"
        (inner / "index").mkdir(parents=True)
        (inner / "__init__.py").write_text("", encoding="utf-8")
        (inner / "config.py").write_text("X = 1\n", encoding="utf-8")
        (inner / "index" / "__init__.py").write_text("", encoding="utf-8")
        (inner / "index" / "indexer.py").write_text("Y = 2\n", encoding="utf-8")
        return base

    def test_strips_leading_member_dir_to_package_top(self, tmp_path: Path) -> None:
        """``loremaster/loremaster/config.py`` → ``loremaster.config`` (NOT doubled)."""
        self._make_pkg(tmp_path)
        derived = CodeGraph.importable_module_name(
            tmp_path, "loremaster/loremaster/config.py"
        )
        assert derived == "loremaster.config"

    def test_strips_to_package_top_for_nested_subpackage(self, tmp_path: Path) -> None:
        """A subpackage module keeps its sub-path below the package top."""
        self._make_pkg(tmp_path)
        derived = CodeGraph.importable_module_name(
            tmp_path, "loremaster/loremaster/index/indexer.py"
        )
        assert derived == "loremaster.index.indexer"

    def test_init_collapses_to_its_package(self, tmp_path: Path) -> None:
        """An ``__init__.py`` collapses to its package below the package top."""
        self._make_pkg(tmp_path)
        derived = CodeGraph.importable_module_name(
            tmp_path, "loremaster/loremaster/index/__init__.py"
        )
        assert derived == "loremaster.index"

    def test_package_top_init_is_the_bare_package(self, tmp_path: Path) -> None:
        """The package top's own ``__init__.py`` is the bare package name."""
        self._make_pkg(tmp_path)
        derived = CodeGraph.importable_module_name(
            tmp_path, "loremaster/loremaster/__init__.py"
        )
        assert derived == "loremaster"

    def test_top_level_module_keeps_bare_name(self, tmp_path: Path) -> None:
        """A module directly under a package top keeps a bare-package-rooted name."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text("Z = 3\n", encoding="utf-8")
        derived = CodeGraph.importable_module_name(tmp_path, "pkg/a.py")
        assert derived == "pkg.a"

    def test_namespace_layout_with_no_init_degrades_to_full_join(
        self, tmp_path: Path
    ) -> None:
        """No ``__init__.py`` anywhere → strip nothing (the documented fallback).

        A namespace/src layout with no ``__init__.py`` chain must degrade
        gracefully — strip nothing, joining the full tier-relative path — rather
        than crash. This is the behaviour the existing in-memory unit tests and
        the wiring tests (``src/widget.py`` with no package) rely on.
        """
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "widget.py").write_text("W = 1\n", encoding="utf-8")
        derived = CodeGraph.importable_module_name(tmp_path, "src/widget.py")
        assert derived == "src.widget"

    def test_missing_file_on_disk_degrades_to_full_join(self, tmp_path: Path) -> None:
        """A path with no file on disk (the direct ``index_file`` test seam) is safe.

        ``index_file`` is called in tests with a source string and no on-disk
        file, so the package probe finds no ``__init__.py`` → the fallback keeps
        the pure path-join, never raising.
        """
        derived = CodeGraph.importable_module_name(tmp_path, "src/widget.py")
        assert derived == "src.widget"


class TestGenericNoOdoo:
    """The graph is generic over any Python AST chunks — zero Odoo coupling."""

    def test_handles_an_arbitrary_python_module(self, graph: CodeGraph) -> None:
        """A plain, non-Odoo module graphs cleanly with no domain-specific handling."""
        source = textwrap.dedent(
            '''\
            """A generic utility module — nothing Odoo about it."""
            import os


            class PathTool:
                def join(self, a, b):
                    return os.path.join(a, b)
            '''
        )
        path = "util/paths.py"
        graph.build_file_graph(SAMPLE_TIER, path, _chunk(path, source))
        kinds = {
            row[0] for row in graph.connection.execute("SELECT DISTINCT kind FROM nodes").fetchall()
        }
        # Only the four generic kinds appear — no Odoo-flavoured node kind.
        assert kinds <= {KIND_MODULE, KIND_CLASS, KIND_METHOD, KIND_FUNCTION}
        imported = {
            row[0]
            for row in graph.connection.execute(
                "SELECT dst FROM edges WHERE kind = ?", (EDGE_IMPORTS,)
            ).fetchall()
        }
        assert "os" in imported
