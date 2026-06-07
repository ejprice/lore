"""Contract tests for ``loremaster.graph.CodeGraph`` — the typed code-graph.

The code-graph is a KùzuDB **side-structure** (NO new vector index) derived from
the AST chunks lorescribe's :class:`~lorescribe.python_ast.PythonAstChunker` emits.
It is generic over *any* Python AST chunks (zero Odoo) and is kept fresh by a
transactional per-file rebuild (delete + rebuild) so the live watcher / reconcile
pass can refresh one file at a time.

THE DELIBERATE CONTRACT CHANGE — RESOLVED edges
-----------------------------------------------
The previous SQLite engine derived ``imports`` / ``inherits`` / ``calls`` from
stdlib ``ast`` re-parsing of chunk source, so an edge ``dst`` was the BARE written
name (``BaseService``, ``json``, ``load_config``) and every reference — even a
stdlib/third-party one — was kept. This engine derives them from astroid INFERENCE
(:func:`lorescribe.astroid_parse.resolve_module`) and applies a keep/drop rule:

* ``(resolved and in_project)`` → KEEP, ``dst`` = the inferred fully-qualified
  name (an in-project base is now ``demo.service.BaseService``, NOT bare
  ``BaseService``; an in-project ``from demo.errors import LoadError`` is now the
  symbol ``demo.errors.LoadError``).
* ``(not resolved)`` → KEEP, ``dst`` = the bare written name (the conservative
  fallback so an un-inferable reference is never dropped).
* ``(resolved and not in_project)`` → DROP (``json``, ``pathlib.Path``,
  ``pydantic.BaseModel`` — stdlib / third-party noise).

These tests pin the RESOLVED contract. Every expected FQN is an INDEPENDENT oracle:
the fixtures are authored here on disk, so the true FQNs are known from the source,
never re-derived from the engine's own logic.

Resolution requires the file ON DISK under project roots, so the resolved-edge
fixtures write a real package to ``tmp_path`` and construct ``CodeGraph`` with
``tier_roots`` + ``project_roots``. The structural ``defines`` / node tests need no
roots (they are derived from the chunk set alone).

Schema
------
Two Kùzu NODE tables (references are stored as RECORDS, not RELs, so an edge can be
created before its endpoints exist — order-independence — and a repeated FQN across
files stays a distinct node — collision-correctness):

* ``CodeNode(id, kind, qualified_name, file_path, chunk_id, tier)`` —
  ``kind ∈ {module, class, method, function}``.
* ``Ref(id, src_qname, dst, kind, resolved, tier, file_path)`` —
  ``kind ∈ {imports, calls, inherits, defines}``; ``resolved`` flags an
  astroid-inferred in-project FQN ``dst``.
"""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

# Target module under contract.
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
# PythonAstChunker (the producer↔consumer seam). The graph consumes exactly what
# the chunker emits; hand-rolling Chunk objects would let a chunker-shape drift
# slip past, so we drive the real chunker. Resolved-edge tests additionally write
# the same sources to disk so astroid can infer their references.
# ---------------------------------------------------------------------------

# Hard token cap from the embedder spec — over-length inputs are rejected.
VOYAGE4_MAX_INPUT_TOKENS: int = 8192

SAMPLE_SLUG: str = "demo-project"
SAMPLE_TIER: str = "local"
OTHER_TIER: str = "community"

# The in-project dependency the app module imports a symbol FROM. Authored as part
# of the on-disk fixture package so astroid resolves the import in-project.
ERRORS_SOURCE: str = textwrap.dedent(
    '''\
    """The demo project's error types."""


    class LoadError(Exception):
        """Raised when a config file cannot be loaded."""
    '''
)

# A realistic application module: imports (one in-project symbol, two external), a
# base class, a subclass that inherits from it AND calls a top-level helper +
# inherited method, plus a module-level function calling stdlib.
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
# test glob, ``test_boot`` references ``boot``, and it imports the app module.
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
ERRORS_PATH: str = "demo/errors.py"
APP_PATH: str = "demo/service.py"
TEST_PATH: str = "tests/test_service.py"

# The importable module names the indexer derives and passes to build_file_graph.
APP_MODULE: str = "demo.service"
TEST_MODULE: str = "tests.test_service"

# Independent oracles — the TRUE fully-qualified names of the app module's symbols,
# read straight off APP_SOURCE / ERRORS_SOURCE (NOT re-derived from the engine).
FQN_BASE: str = "demo.service.BaseService"
FQN_INDEX: str = "demo.service.IndexService"
FQN_LOAD_CONFIG: str = "demo.service.load_config"
FQN_BOOT: str = "demo.service.IndexService.boot"
FQN_START: str = "demo.service.BaseService.start"
FQN_LOAD_ERROR: str = "demo.errors.LoadError"


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


def _write_project(root: Path) -> None:
    """Materialise the demo package on disk under ``root`` for astroid resolution.

    ``demo/`` is a real package (has ``__init__.py``) holding ``errors.py`` (the
    in-project import target) and ``service.py``; ``tests/`` holds the test module.
    Resolution classifies a reference in-project iff its defining file lies under
    ``root``, so the import of ``demo.errors.LoadError`` resolves in-project while
    ``json`` / ``pathlib`` resolve external.
    """
    (root / "demo").mkdir(parents=True, exist_ok=True)
    (root / "demo" / "__init__.py").write_text("", encoding="utf-8")
    (root / "demo" / "errors.py").write_text(ERRORS_SOURCE, encoding="utf-8")
    (root / "demo" / "service.py").write_text(APP_SOURCE, encoding="utf-8")
    (root / "tests").mkdir(parents=True, exist_ok=True)
    (root / "tests" / "test_service.py").write_text(TEST_SOURCE, encoding="utf-8")


@pytest.fixture()
def graph(tmp_path) -> CodeGraph:  # type: ignore[no-untyped-def]
    """A structural-only CodeGraph (no roots) backed by an on-disk Kùzu file.

    Used by tests that only need the structural ``defines`` edges and the node set
    — they pass no project roots, so the graph emits no resolved references.
    """
    return CodeGraph(str(tmp_path / "graph.kuzu"))


@pytest.fixture()
def resolved_graph(tmp_path):  # type: ignore[no-untyped-def]
    """A resolution-enabled CodeGraph over an on-disk demo package.

    Yields ``(graph, project_root)``. The package is written to disk and the graph
    is wired with ``tier_roots`` + ``project_roots`` so astroid resolves the demo
    module's references; building ``APP_PATH`` therefore emits RESOLVED ``imports``
    / ``inherits`` / ``calls`` edges per the keep/drop rule.
    """
    project_root = tmp_path / "project"
    _write_project(project_root)
    graph = CodeGraph(
        str(tmp_path / "graph.kuzu"),
        tier_roots={SAMPLE_TIER: project_root, OTHER_TIER: project_root},
        project_roots=[project_root],
    )
    try:
        yield graph, project_root
    finally:
        graph.close()


@pytest.fixture()
def app_chunks() -> list[Chunk]:
    """The real chunk set for the application module."""
    return _chunk(APP_PATH, APP_SOURCE)


@pytest.fixture()
def test_chunks() -> list[Chunk]:
    """The real chunk set for the test module."""
    return _chunk(TEST_PATH, TEST_SOURCE)


def _refs(graph: CodeGraph, kind: str, src: str) -> set[str]:
    """The ``dst`` set of ``Ref`` records of ``kind`` with ``src_qname == src``."""
    result = graph.connection.execute(
        "MATCH (r:Ref) WHERE r.kind = $kind AND r.src_qname = $src RETURN r.dst",
        {"kind": kind, "src": src},
    )
    dsts: set[str] = set()
    while result.has_next():
        dsts.add(str(result.get_next()[0]))
    return dsts


def _node_qnames(graph: CodeGraph, kind: str) -> set[str]:
    """The qualified-name set of ``CodeNode`` rows of ``kind``."""
    result = graph.connection.execute(
        "MATCH (n:CodeNode) WHERE n.kind = $kind RETURN n.qualified_name",
        {"kind": kind},
    )
    names: set[str] = set()
    while result.has_next():
        names.add(str(result.get_next()[0]))
    return names


class TestSchemaAndConstruction:
    """The graph is a Kùzu side-structure with the documented node tables."""

    def test_creates_codenode_and_ref_tables(self, graph: CodeGraph) -> None:
        """A fresh graph has exactly the ``CodeNode`` and ``Ref`` node tables."""
        result = graph.connection.execute("CALL show_tables() RETURN *")
        columns = result.get_column_names()
        name_index = columns.index("name")
        names = set()
        while result.has_next():
            names.add(str(result.get_next()[name_index]))
        assert {"CodeNode", "Ref"} <= names

    def test_codenode_table_has_documented_columns(self, graph: CodeGraph) -> None:
        """``CodeNode`` carries id, kind, qualified_name, file_path, chunk_id, tier."""
        assert self._column_names(graph, "CodeNode") >= {
            "id",
            "kind",
            "qualified_name",
            "file_path",
            "chunk_id",
            "tier",
        }

    def test_ref_table_has_documented_columns(self, graph: CodeGraph) -> None:
        """``Ref`` carries src_qname, dst, kind, resolved, tier, file_path."""
        assert self._column_names(graph, "Ref") >= {
            "src_qname",
            "dst",
            "kind",
            "resolved",
            "tier",
            "file_path",
        }

    def test_connection_property_returns_a_live_kuzu_connection(
        self, graph: CodeGraph
    ) -> None:
        """The ``connection`` property exposes a usable Kùzu connection.

        The divergence-reconcile wipe and the lifecycle close-probe both drive this
        property, so it must return a live connection that answers a trivial query.
        """
        result = graph.connection.execute("RETURN 1 AS one")
        assert result.has_next()
        assert int(result.get_next()[0]) == 1

    @staticmethod
    def _column_names(graph: CodeGraph, table: str) -> set[str]:
        """The property-name set of a Kùzu node table, via ``CALL table_info``."""
        result = graph.connection.execute(f"CALL table_info('{table}') RETURN *")
        columns = result.get_column_names()
        name_index = columns.index("name")
        names: set[str] = set()
        while result.has_next():
            names.add(str(result.get_next()[name_index]))
        return names


class TestBuildFileGraphNodes:
    """``build_file_graph`` derives the right node set from real AST chunks."""

    def test_synthesises_a_module_node(self, graph: CodeGraph, app_chunks: list[Chunk]) -> None:
        """A file yields exactly one ``module`` node, qualified from its module name."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        result = graph.connection.execute(
            "MATCH (n:CodeNode) WHERE n.kind = $kind "
            "RETURN n.qualified_name, n.tier, n.file_path",
            {"kind": KIND_MODULE},
        )
        rows = []
        while result.has_next():
            rows.append(tuple(result.get_next()))
        assert len(rows) == 1
        assert rows[0] == (APP_MODULE, SAMPLE_TIER, APP_PATH)

    def test_creates_a_class_node_per_class(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level class becomes a ``class`` node with a dotted qualified name."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _node_qnames(graph, KIND_CLASS) == {FQN_BASE, FQN_INDEX}

    def test_creates_a_method_node_per_method(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each method becomes a ``method`` node qualified by its class."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _node_qnames(graph, KIND_METHOD) == {FQN_START, FQN_BOOT}

    def test_creates_a_function_node_per_top_level_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level function becomes a ``function`` node."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _node_qnames(graph, KIND_FUNCTION) == {FQN_LOAD_CONFIG}

    def test_module_node_chunk_id_is_none(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The synthesised module node carries ``chunk_id is None`` (it has no chunk).

        The empty-string on-the-wire encoding for the chunk-less module node must
        round-trip back to ``None`` through the public node decode.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        # blast_radius decodes nodes via the public path; the module node is reached
        # as a reverse dependent of one of its own defined symbols.
        modules = [
            node
            for node in graph.blast_radius(FQN_BASE, depth=3, max_results=50)
            if node.kind == KIND_MODULE
        ]
        assert modules, "the module node must be reachable as a reverse dependent"
        assert all(node.chunk_id is None for node in modules)


class TestStructuralDefinesEdges:
    """``defines`` is structural — derived from chunks alone, no resolution needed."""

    def test_defines_edges_module_to_class_and_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The module ``defines`` each top-level class and function (not methods)."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _refs(graph, EDGE_DEFINES, APP_MODULE) == {
            FQN_BASE,
            FQN_INDEX,
            FQN_LOAD_CONFIG,
        }

    def test_defines_edges_class_to_its_methods(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A class ``defines`` exactly its own methods."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _refs(graph, EDGE_DEFINES, FQN_INDEX) == {FQN_BOOT}

    def test_defines_emitted_without_project_roots(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Structural ``defines`` work with NO roots — the rootless degrade path.

        The ``graph`` fixture has no project roots, so resolution is skipped; the
        structural ``defines`` edges must still be present (the object stays useful
        without roots), while the resolution-only kinds are absent.
        """
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        assert _refs(graph, EDGE_DEFINES, APP_MODULE)  # structural defines present
        # No resolution → no inherits/imports/calls for this file.
        assert _refs(graph, EDGE_INHERITS, FQN_INDEX) == set()
        assert _refs(graph, EDGE_IMPORTS, APP_MODULE) == set()


class TestResolvedEdges:
    """``imports`` / ``inherits`` / ``calls`` are astroid-RESOLVED (the contract change)."""

    def test_inherits_edge_is_the_resolved_fqn_not_bare(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``IndexService`` inherits ``demo.service.BaseService`` — the FQN, NOT bare.

        Independent oracle: ``BaseService`` is defined in APP_SOURCE in the SAME
        module, so its FQN is ``demo.service.BaseService``. The deliberate contract
        change: the old engine stored the bare ``BaseService``; this one stores the
        resolved FQN.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        bases = _refs(graph, EDGE_INHERITS, FQN_INDEX)
        assert bases == {FQN_BASE}
        assert "BaseService" not in bases, "the bare name must NOT be stored — resolution wins"

    def test_in_project_import_resolves_to_symbol_fqn(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``from demo.errors import LoadError`` resolves to the symbol FQN.

        Independent oracle: ERRORS_SOURCE defines ``LoadError`` in ``demo/errors.py``
        → ``demo.errors.LoadError``. An in-project from-import becomes the SYMBOL
        target, not the bare module name.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        assert FQN_LOAD_ERROR in _refs(graph, EDGE_IMPORTS, APP_MODULE)

    def test_external_imports_are_dropped(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``json`` and ``pathlib`` (resolved + external) are DROPPED, not kept.

        Independent oracle: both are stdlib, so they resolve EXTERNAL and the
        keep/drop rule drops them. The old engine kept every import; this is the
        precision win.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        imports = _refs(graph, EDGE_IMPORTS, APP_MODULE)
        assert "json" not in imports
        assert "pathlib" not in imports
        # Only the in-project symbol import survives.
        assert imports == {FQN_LOAD_ERROR}

    def test_in_project_call_resolves_to_callee_fqn(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``IndexService.boot`` calls resolve to in-project callee FQNs.

        Independent oracle: ``boot`` calls ``load_config(path)`` (→ the top-level
        ``demo.service.load_config``) and ``self.start()`` (→ the inherited
        ``demo.service.BaseService.start``). Both are in-project, so both are KEPT
        as resolved FQNs.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        called = _refs(graph, EDGE_CALLS, FQN_BOOT)
        assert FQN_LOAD_CONFIG in called
        assert FQN_START in called

    def test_external_calls_are_dropped(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``load_config``'s stdlib calls (``json.loads`` / ``Path``) are DROPPED.

        Independent oracle: ``load_config`` calls only stdlib (``json.loads``,
        ``Path(...).read_text()``), all resolved EXTERNAL, so it has NO kept calls.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        assert _refs(graph, EDGE_CALLS, FQN_LOAD_CONFIG) == set()

    def test_unresolvable_reference_falls_back_to_bare_name(self, tmp_path: Path) -> None:
        """An un-inferable reference is KEPT as its bare name (``resolved=False``).

        Independent oracle: a class inheriting from an UNDEFINED, never-imported
        name ``MysteryBase`` cannot be inferred by astroid, so the reference must be
        kept with its bare written name rather than dropped — the conservative
        fallback that the resolution precision must not sacrifice.
        """
        project_root = tmp_path / "project"
        (project_root / "pkg").mkdir(parents=True)
        (project_root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        mystery_source = textwrap.dedent(
            '''\
            """A class with an unresolvable base."""


            class Widget(MysteryBase):  # noqa: F821 - intentionally undefined
                def run(self):
                    return 1
            '''
        )
        (project_root / "pkg" / "widget.py").write_text(mystery_source, encoding="utf-8")
        graph = CodeGraph(
            str(tmp_path / "graph.kuzu"),
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            graph.build_file_graph(
                SAMPLE_TIER,
                "pkg/widget.py",
                _chunk("pkg/widget.py", mystery_source),
                module_name="pkg.widget",
            )
            bases = _refs(graph, EDGE_INHERITS, "pkg.widget.Widget")
            # The bare written base is kept (never dropped) because astroid could
            # not infer it — the conservative fallback.
            assert "MysteryBase" in bases
        finally:
            graph.close()

    def test_resolved_flag_records_resolution_status(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """The ``resolved`` flag is ``True`` on the in-project inferred inherits edge."""
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        result = graph.connection.execute(
            "MATCH (r:Ref) WHERE r.kind = $kind AND r.src_qname = $src "
            "RETURN r.dst, r.resolved",
            {"kind": EDGE_INHERITS, "src": FQN_INDEX},
        )
        rows = {}
        while result.has_next():
            dst, resolved = result.get_next()
            rows[str(dst)] = bool(resolved)
        assert rows.get(FQN_BASE) is True


class TestPerFileRebuildTransactional:
    """A per-file rebuild (delete + rebuild) leaves correct state and NO orphans."""

    def test_rebuild_replaces_nodes_no_duplicates(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Building the same file twice does not double its nodes."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        first = self._file_node_count(graph, SAMPLE_TIER, APP_PATH)
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        second = self._file_node_count(graph, SAMPLE_TIER, APP_PATH)
        assert first == second
        assert first > 0  # sanity: the file actually produced nodes

    def test_rebuild_after_edit_drops_removed_symbols(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """Editing a file to remove a class drops its nodes AND its resolved edges.

        The freshness contract: a delete + rebuild must leave NO orphan reference
        pointing at a symbol that no longer exists in the file. Run on the
        resolution-enabled graph so the removed ``inherits`` edge is a RESOLVED one.
        """
        graph, project_root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        assert _refs(graph, EDGE_INHERITS, FQN_INDEX) == {FQN_BASE}, "seed: inherits edge present"

        # Edit on disk AND rebuild from the trimmed chunks: only the helper survives.
        trimmed = textwrap.dedent(
            '''\
            """Trimmed: only the helper survives."""
            import json


            def load_config(path):
                """Read and parse a config file."""
                return json.loads(path)
            '''
        )
        (project_root / "demo" / "service.py").write_text(trimmed, encoding="utf-8")
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, trimmed), module_name=APP_MODULE)

        remaining = _node_qnames(graph, KIND_CLASS) | _node_qnames(graph, KIND_METHOD) | _node_qnames(
            graph, KIND_FUNCTION
        )
        assert FQN_INDEX not in remaining
        assert FQN_START not in remaining
        assert FQN_LOAD_CONFIG in remaining
        # No orphan inherits edge to the deleted subclass survives.
        assert _refs(graph, EDGE_INHERITS, FQN_INDEX) == set()

    def test_delete_file_graph_removes_all_rows(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """``delete_file_graph`` removes every node and reference for that (tier, file)."""
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, app_chunks, module_name=APP_MODULE)
        graph.delete_file_graph(SAMPLE_TIER, APP_PATH)
        assert self._file_node_count(graph, SAMPLE_TIER, APP_PATH) == 0
        # And the file's own references are gone (its module/class/method srcs removed).
        result = graph.connection.execute(
            "MATCH (r:Ref) WHERE r.tier = $tier AND r.file_path = $file_path RETURN count(r)",
            {"tier": SAMPLE_TIER, "file_path": APP_PATH},
        )
        assert int(result.get_next()[0]) == 0

    def test_delete_is_tier_scoped(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """Deleting one tier's copy of a path leaves another tier's copy intact (C1)."""
        graph, _root = resolved_graph
        chunks = _chunk(APP_PATH, APP_SOURCE)
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, chunks, module_name=APP_MODULE)
        graph.build_file_graph(OTHER_TIER, APP_PATH, chunks, module_name=APP_MODULE)
        graph.delete_file_graph(SAMPLE_TIER, APP_PATH)
        assert self._file_node_count(graph, OTHER_TIER, APP_PATH) > 0

    @staticmethod
    def _file_node_count(graph: CodeGraph, tier: str, file_path: str) -> int:
        """The number of ``CodeNode`` rows for one ``(tier, file_path)``."""
        result = graph.connection.execute(
            "MATCH (n:CodeNode) WHERE n.tier = $tier AND n.file_path = $file_path "
            "RETURN count(n)",
            {"tier": tier, "file_path": file_path},
        )
        return int(result.get_next()[0])


class TestIndexedFileCount:
    """``indexed_file_count`` counts DISTINCT ``(tier, file_path)`` over CodeNode."""

    def test_zero_for_fresh_graph(self, graph: CodeGraph) -> None:
        """A fresh/wiped graph reports zero indexed files (the FP-04 trigger)."""
        assert graph.indexed_file_count() == 0

    def test_counts_distinct_tier_file_pairs(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """The same path under two tiers counts as two distinct files (C1)."""
        graph, _root = resolved_graph
        chunks = _chunk(APP_PATH, APP_SOURCE)
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, chunks, module_name=APP_MODULE)
        assert graph.indexed_file_count() == 1
        graph.build_file_graph(OTHER_TIER, APP_PATH, chunks, module_name=APP_MODULE)
        assert graph.indexed_file_count() == 2


class TestWhatImports:
    """``what_imports`` reverses the import edge: who pulls in a target?"""

    def test_returns_modules_that_import_the_resolved_symbol(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """The app imports ``demo.errors.LoadError``; ``what_imports`` finds it by FQN.

        Under the resolved contract the in-project import dst is the SYMBOL FQN, so
        a query for that FQN finds the importing module.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        importers = {node.qualified_name for node in graph.what_imports(FQN_LOAD_ERROR)}
        assert APP_MODULE in importers

    def test_what_imports_matches_by_bare_name_seam(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """A bare-name query reaches the resolved symbol import via the bare seam.

        ``what_imports`` matches a ``dst`` by FQN OR bare last segment, so a query
        for the bare ``LoadError`` reaches the ``demo.errors.LoadError`` import.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        importers = {node.qualified_name for node in graph.what_imports("LoadError")}
        assert APP_MODULE in importers

    def test_returns_empty_for_unimported_target(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """A target nobody imports yields an empty result, not an error."""
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        assert list(graph.what_imports("nonexistent.module")) == []


class TestBlastRadius:
    """``blast_radius`` is a BOUNDED reverse-reference transitive closure."""

    def test_finds_direct_reverse_dependents(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """A symbol's direct dependents (one hop back) are in its blast radius.

        ``IndexService`` inherits ``demo.service.BaseService`` (a RESOLVED reverse
        edge), so the blast radius of ``BaseService`` includes ``IndexService``.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        affected = {
            node.qualified_name
            for node in graph.blast_radius(FQN_BASE, depth=3, max_results=100)
        }
        assert FQN_INDEX in affected

    def test_respects_depth_bound(self, tmp_path: Path) -> None:
        """A deep inheritance chain is truncated at ``depth`` hops, never beyond.

        Build a linear chain ``N0 <- N1 <- ... <- N7`` on disk (each inherits the
        previous, RESOLVED in-project edges) and assert the reverse closure from
        ``N0`` stops exactly at ``depth`` hops.
        """
        chain_length = 8
        depth_bound = 3
        lines = ['"""A deep linear inheritance chain."""', "", "", "class N0:", "    pass", ""]
        for index in range(1, chain_length):
            lines += ["", f"class N{index}(N{index - 1}):", "    pass", ""]
        chain_source = "\n".join(lines) + "\n"

        project_root = tmp_path / "project"
        (project_root / "demo").mkdir(parents=True)
        (project_root / "demo" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "demo" / "chain.py").write_text(chain_source, encoding="utf-8")
        graph = CodeGraph(
            str(tmp_path / "graph.kuzu"),
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            graph.build_file_graph(
                SAMPLE_TIER, "demo/chain.py", _chunk("demo/chain.py", chain_source),
                module_name="demo.chain",
            )
            affected = {
                node.qualified_name
                for node in graph.blast_radius("demo.chain.N0", depth=depth_bound, max_results=1000)
            }
            assert "demo.chain.N1" in affected  # 1 hop
            assert f"demo.chain.N{depth_bound}" in affected  # exactly at the bound
            assert f"demo.chain.N{depth_bound + 1}" not in affected  # beyond the bound
            assert f"demo.chain.N{chain_length - 1}" not in affected  # far beyond
        finally:
            graph.close()

    def test_respects_max_results_cap(self, tmp_path: Path) -> None:
        """A huge fan-out is capped at ``max_results`` — the closure cannot blow up.

        A star: many subclasses of one base (all RESOLVED in-project inherits). The
        base's reverse closure has ``fan_out`` dependents; the cap clamps it.
        """
        fan_out = 200
        cap = 25
        lines = ['"""A wide fan-out: many subclasses of one base."""', "", "class Hub:", "    pass", ""]
        for index in range(fan_out):
            lines += ["", f"class Leaf{index}(Hub):", "    pass", ""]
        star_source = "\n".join(lines) + "\n"

        project_root = tmp_path / "project"
        (project_root / "demo").mkdir(parents=True)
        (project_root / "demo" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "demo" / "star.py").write_text(star_source, encoding="utf-8")
        graph = CodeGraph(
            str(tmp_path / "graph.kuzu"),
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            graph.build_file_graph(
                SAMPLE_TIER, "demo/star.py", _chunk("demo/star.py", star_source),
                module_name="demo.star",
            )
            affected = list(graph.blast_radius("demo.star.Hub", depth=5, max_results=cap))
            assert len(affected) <= cap  # hard ceiling
            assert len(affected) > 0  # clamps, not zeroes
        finally:
            graph.close()


class TestTestsFor:
    """``tests_for`` links test nodes to a target by reference OR the name heuristic."""

    def test_finds_test_by_reference_edge(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """A test module referencing the target's symbol is a test for it.

        ``tests/test_service.py`` imports ``demo.service.IndexService`` and calls
        ``boot``; it is a test-glob path with a resolved reference into the target,
        so it is a test for ``IndexService``.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        graph.build_file_graph(
            SAMPLE_TIER, TEST_PATH, _chunk(TEST_PATH, TEST_SOURCE), module_name=TEST_MODULE
        )
        related_files = {node.file_path for node in graph.tests_for(FQN_INDEX)}
        assert TEST_PATH in related_files

    def test_finds_test_by_name_heuristic(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """``test_boot`` is linked to symbol ``boot`` by the test_x ↔ x heuristic.

        The app defines ``IndexService.boot``; the test file defines ``test_boot``.
        Asked for tests of the symbol whose bare name is ``boot``, the heuristic
        returns the ``test_boot`` node.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        graph.build_file_graph(
            SAMPLE_TIER, TEST_PATH, _chunk(TEST_PATH, TEST_SOURCE), module_name=TEST_MODULE
        )
        related_names = {node.qualified_name for node in graph.tests_for(FQN_BOOT)}
        assert any(name.endswith("test_boot") for name in related_names)

    def test_does_not_return_non_test_nodes(self, resolved_graph) -> None:  # type: ignore[no-untyped-def]
        """With no test file indexed, a symbol has no tests — non-test nodes excluded.

        ``BaseService`` is defined and depended upon, but no test-glob file
        references it, so ``tests_for`` returns nothing — it must not leak ordinary
        application nodes that merely have references.
        """
        graph, _root = resolved_graph
        graph.build_file_graph(SAMPLE_TIER, APP_PATH, _chunk(APP_PATH, APP_SOURCE), module_name=APP_MODULE)
        assert list(graph.tests_for(FQN_BASE)) == []


class TestImportableModuleName:
    """``importable_module_name`` derives the TRUE importable dotted path.

    The bug this pins: the old ``module_qualified_name`` joined EVERY segment of
    the tier-relative path, so a workspace-member layout
    (``loremaster/loremaster/config.py`` under repo root) produced the DOUBLED name
    ``loremaster.loremaster.config``. The fix strips leading path segments up to
    the package top (the shallowest dir with an ``__init__.py``).
    """

    def _make_pkg(self, base: Path) -> Path:
        """Create the doubled-layout fixture package on disk under ``base``."""
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
        assert (
            CodeGraph.importable_module_name(tmp_path, "loremaster/loremaster/config.py")
            == "loremaster.config"
        )

    def test_strips_to_package_top_for_nested_subpackage(self, tmp_path: Path) -> None:
        """A subpackage module keeps its sub-path below the package top."""
        self._make_pkg(tmp_path)
        assert (
            CodeGraph.importable_module_name(
                tmp_path, "loremaster/loremaster/index/indexer.py"
            )
            == "loremaster.index.indexer"
        )

    def test_init_collapses_to_its_package(self, tmp_path: Path) -> None:
        """An ``__init__.py`` collapses to its package below the package top."""
        self._make_pkg(tmp_path)
        assert (
            CodeGraph.importable_module_name(
                tmp_path, "loremaster/loremaster/index/__init__.py"
            )
            == "loremaster.index"
        )

    def test_package_top_init_is_the_bare_package(self, tmp_path: Path) -> None:
        """The package top's own ``__init__.py`` is the bare package name."""
        self._make_pkg(tmp_path)
        assert (
            CodeGraph.importable_module_name(tmp_path, "loremaster/loremaster/__init__.py")
            == "loremaster"
        )

    def test_top_level_module_keeps_bare_name(self, tmp_path: Path) -> None:
        """A module directly under a package top keeps a bare-package-rooted name."""
        pkg = tmp_path / "pkg"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("", encoding="utf-8")
        (pkg / "a.py").write_text("Z = 3\n", encoding="utf-8")
        assert CodeGraph.importable_module_name(tmp_path, "pkg/a.py") == "pkg.a"

    def test_namespace_layout_with_no_init_degrades_to_full_join(self, tmp_path: Path) -> None:
        """No ``__init__.py`` anywhere → strip nothing (the documented fallback)."""
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "widget.py").write_text("W = 1\n", encoding="utf-8")
        assert CodeGraph.importable_module_name(tmp_path, "src/widget.py") == "src.widget"

    def test_missing_file_on_disk_degrades_to_full_join(self, tmp_path: Path) -> None:
        """A path with no file on disk is safe — the fallback keeps the path-join."""
        assert CodeGraph.importable_module_name(tmp_path, "src/widget.py") == "src.widget"


class TestGenericNoOdoo:
    """The graph is generic over any Python AST chunks — zero Odoo coupling."""

    def test_handles_an_arbitrary_python_module(self, tmp_path: Path) -> None:
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
        project_root = tmp_path / "project"
        (project_root / "util").mkdir(parents=True)
        (project_root / "util" / "__init__.py").write_text("", encoding="utf-8")
        (project_root / "util" / "paths.py").write_text(source, encoding="utf-8")
        graph = CodeGraph(
            str(tmp_path / "graph.kuzu"),
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            graph.build_file_graph(
                SAMPLE_TIER, "util/paths.py", _chunk("util/paths.py", source),
                module_name="util.paths",
            )
            kinds = (
                {KIND_MODULE} if _node_qnames(graph, KIND_MODULE) else set()
            ) | (
                {KIND_CLASS} if _node_qnames(graph, KIND_CLASS) else set()
            ) | (
                {KIND_METHOD} if _node_qnames(graph, KIND_METHOD) else set()
            ) | (
                {KIND_FUNCTION} if _node_qnames(graph, KIND_FUNCTION) else set()
            )
            # Only the four generic kinds appear — no Odoo-flavoured node kind.
            assert kinds <= {KIND_MODULE, KIND_CLASS, KIND_METHOD, KIND_FUNCTION}
            assert kinds  # something was graphed
            # ``os`` is stdlib → resolved external → DROPPED (the precision win).
            assert "os" not in _refs(graph, EDGE_IMPORTS, "util.paths")
        finally:
            graph.close()


class TestResolutionCachePoisoningGuard:
    """Resolution survives the chunker poisoning astroid's process-global cache.

    The real :class:`PythonAstChunker` calls astroid while chunking, populating the
    process-global astroid ``MANAGER`` with context-poor module entries. If the
    graph resolved a module WITHOUT first resetting that shared state, in-project
    references would silently degrade from their FQN to the bare written name
    (``resolved=False``) — which would later inflate false "dead code". The guard
    is :meth:`CodeGraph.build_file_graph` clearing the resolution cache before it
    resolves.

    This pins the guard DETERMINISTICALLY in one test. The degradation only
    manifests once MORE THAN ONE module has been chunked in the process, so a
    single-module test cannot pin it; here several in-project modules are chunked
    through the real chunker first (reproducing the production indexer's
    chunk-everything-then-graph order) before the app module is graphed — so the
    assertion fails if the clear-before-resolve guard is ever removed, regardless
    of test ordering or selection.
    """

    def test_cross_module_call_and_inherit_resolve_after_chunker_poisons_cache(
        self,
        tmp_path,  # type: ignore[no-untyped-def]
    ) -> None:
        # A two-module in-project package: ``service`` INHERITS from and CALLS
        # ``base``. Cross-module inheritance/call inference is the cache-sensitive
        # path — it (unlike imports) degrades to bare names when the chunker has
        # poisoned astroid's shared manager and the guard is absent.
        root = tmp_path / "proj"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        (root / "pkg" / "base.py").write_text(
            "class Base:\n    def greet(self):\n        return 1\n\n\ndef helper():\n    return 2\n",
            encoding="utf-8",
        )
        (root / "pkg" / "service.py").write_text(
            "from pkg.base import Base, helper\n\n\n"
            "class Service(Base):\n    def run(self):\n        return self.greet() + helper()\n",
            encoding="utf-8",
        )
        base_src = (root / "pkg" / "base.py").read_text(encoding="utf-8")
        service_src = (root / "pkg" / "service.py").read_text(encoding="utf-8")
        graph = CodeGraph(
            str(tmp_path / "graph.kuzu"),
            tier_roots={SAMPLE_TIER: root},
            project_roots=[root],
        )
        try:
            # Production order: run the REAL chunker over BOTH modules first
            # (poisoning the process-global astroid manager), THEN graph service.
            _chunk("pkg/base.py", base_src)
            _chunk("pkg/service.py", service_src)
            graph.build_file_graph(
                SAMPLE_TIER, "pkg/service.py", _chunk("pkg/service.py", service_src),
                module_name="pkg.service",
            )
            inherits = _refs(graph, EDGE_INHERITS, "pkg.service.Service")
            calls = _refs(graph, EDGE_CALLS, "pkg.service.Service.run")
            # Cross-module references must carry the in-project FQN. The bare name is
            # the degraded form that appears iff the clear-before-resolve guard is
            # removed (verified: without the guard these become 'Base' / 'helper').
            assert "pkg.base.Base" in inherits, (
                f"inherits degraded — cache guard failed; got {inherits!r}"
            )
            assert "pkg.base.helper" in calls, (
                f"call degraded — cache guard failed; got {calls!r}"
            )
            assert "Base" not in inherits and "helper" not in calls
        finally:
            graph.close()
