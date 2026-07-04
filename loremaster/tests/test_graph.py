"""Contract tests for ``loremaster.graph.CodeGraph`` — the astroid DERIVATION CORE.

After the P8 Kùzu-shell surgery, :class:`~loremaster.graph.CodeGraph` is a PURE
astroid derivation core: it turns a file's lorescribe AST chunks into typed graph
NODES (:class:`~loremaster.graph._NodeSpec`) and reference EDGES
(:class:`~loremaster.graph._EdgeSpec`) and owns ZERO storage. The KùzuDB
storage/query shell (``CREATE``/``MATCH``, ``build_file_graph``, the query methods)
was removed; the live engine is the async
:class:`~loremaster.graph_surreal.SurrealCodeGraph`, which REUSES this exact
derivation core through its ``_AstroidDerivation`` delegate and pins the STORAGE +
QUERY behaviour in ``test_graph_surreal.py``.

THE SEAM UNDER CONTRACT — ``_derive_nodes`` / ``_derive_edges``
--------------------------------------------------------------
These tests drive the derivation core at the SAME seam ``graph_surreal.py``
consumes (``self._derivation._derive_nodes`` / ``_derive_edges``): they assert on
the returned ``_NodeSpec`` / ``_EdgeSpec`` lists, NOT on any stored row. This is
what preserves the CONTRACT meaning after the kuzu shell is gone — the derivation
produces exactly the nodes/edges the store used to persist. Tier/file_path are
STORAGE stamps applied by the shell, so the node specs carry only the derived
identity (kind + qualified_name + chunk_id); the reference specs carry only
src/dst/kind/resolved.

THE DELIBERATE CONTRACT — RESOLVED edges
----------------------------------------
``imports`` / ``inherits`` / ``calls`` are derived from astroid INFERENCE
(:func:`lorescribe.astroid_parse.resolve_module`) with a keep/drop rule:

* ``(resolved and in_project)`` → KEEP, ``dst`` = the inferred fully-qualified
  name (an in-project base is ``demo.service.BaseService``, NOT bare
  ``BaseService``; an in-project ``from demo.errors import LoadError`` is the
  symbol ``demo.errors.LoadError``).
* ``(not resolved)`` → KEEP, ``dst`` = the bare written name (the conservative
  fallback so an un-inferable reference is never dropped).
* ``(resolved and not in_project)`` → DROP (``json``, ``pathlib.Path``,
  ``pydantic.BaseModel`` — stdlib / third-party noise).

Every expected FQN is an INDEPENDENT oracle: the fixtures are authored here on
disk, so the true FQNs are known from the source, never re-derived from the
engine's own logic. Resolution requires the file ON DISK under project roots, so
the resolved-edge fixtures write a real package to ``tmp_path`` and construct
``CodeGraph`` with ``tier_roots`` + ``project_roots``. The structural ``defines``
/ node tests need no roots (they are derived from the chunk set alone).
"""

from __future__ import annotations

import textwrap
from collections.abc import Iterator
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
from lorescribe.astroid_parse import clear_resolution_cache, reset_search_path_memo
from lorescribe.models import Chunk, ChunkContext
from lorescribe.python_ast import PythonAstChunker


@pytest.fixture(autouse=True)
def _reset_astroid_resolution_state() -> Iterator[None]:
    """Reset astroid's process-global resolution state around EVERY graph test.

    astroid's manager (module cache + import-spec caches) and this package's
    ``sys.path`` / package-parent-dir memo are PROCESS-GLOBAL. Production bounds
    them at sweep boundaries via :meth:`CodeGraph.reset_resolution_cache`; the
    derivation core no longer wipes the cache per file (that was the O(files ×
    deps) cold-build cost this change removes). Without this autouse reset, one
    test's throwaway ``tmp_path`` package would leak its warm cache / search-path
    entries into the next test's resolution and cross-contaminate it. Resetting
    before AND after each test keeps every case hermetic regardless of order or
    selection.
    """
    clear_resolution_cache()
    reset_search_path_memo()
    yield
    clear_resolution_cache()
    reset_search_path_memo()


# ---------------------------------------------------------------------------
# Construction seam. The derivation core is a PURE object (no on-disk database);
# every construction routes through these two helpers so the whole file speaks a
# single vocabulary for building/tearing-down a derivation core.
# ---------------------------------------------------------------------------


def _new_graph(
    tmp_path: Path,
    *,
    tier_roots: dict[str, Path] | None = None,
    project_roots: list[Path] | None = None,
) -> CodeGraph:
    """Construct a derivation-core :class:`CodeGraph` for a test.

    ``tmp_path`` is retained in the signature for call-site stability (the demo
    packages the resolved-edge tests write live under it); the derivation core
    itself owns no on-disk database.
    """
    return CodeGraph(tier_roots=tier_roots, project_roots=project_roots)


def _close_graph(graph: CodeGraph) -> None:
    """Tear down a derivation core — a no-op (the core owns no database)."""


# ---------------------------------------------------------------------------
# Real fixtures: production-realistic Python sources chunked via the REAL
# PythonAstChunker (the producer↔consumer seam). The derivation consumes exactly
# what the chunker emits; hand-rolling Chunk objects would let a chunker-shape
# drift slip past, so we drive the real chunker. Resolved-edge tests additionally
# write the same sources to disk so astroid can infer their references.
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
# test glob, ``test_boot`` references ``boot``, and it imports the app module. It
# is written to disk so the demo package resolves as a whole.
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

# The importable module names the indexer derives and passes to the derivation.
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
def graph(tmp_path: Path) -> CodeGraph:
    """A structural-only derivation core (no roots).

    Used by tests that only need the structural ``defines`` edges and the node set
    — they pass no project roots, so the core emits no resolved references.
    """
    return _new_graph(tmp_path)


@pytest.fixture()
def resolved_graph(tmp_path: Path) -> Iterator[tuple[CodeGraph, Path]]:
    """A resolution-enabled derivation core over an on-disk demo package.

    Yields ``(graph, project_root)``. The package is written to disk and the core
    is wired with ``tier_roots`` + ``project_roots`` so astroid resolves the demo
    module's references; deriving ``APP_PATH``'s edges therefore emits RESOLVED
    ``imports`` / ``inherits`` / ``calls`` per the keep/drop rule.
    """
    project_root = tmp_path / "project"
    _write_project(project_root)
    graph = _new_graph(
        tmp_path,
        tier_roots={SAMPLE_TIER: project_root, OTHER_TIER: project_root},
        project_roots=[project_root],
    )
    try:
        yield graph, project_root
    finally:
        _close_graph(graph)


@pytest.fixture()
def app_chunks() -> list[Chunk]:
    """The real chunk set for the application module."""
    return _chunk(APP_PATH, APP_SOURCE)


# ---------------------------------------------------------------------------
# Derivation-read helpers — the kuzu-free seam. They read the derived node/edge
# specs directly (the exact ``_derive_nodes`` / ``_derive_edges`` surface
# ``graph_surreal`` consumes), replacing the old ``kz_query``-backed row readers.
# ---------------------------------------------------------------------------


def _derived_qnames(graph: CodeGraph, module: str, chunks: list[Chunk], kind: str) -> set[str]:
    """The qualified-name set of derived node specs of ``kind``."""
    return {
        node.qualified_name
        for node in graph._derive_nodes(module, chunks)  # noqa: SLF001 - derivation seam
        if node.kind == kind
    }


def _derived_refs(
    graph: CodeGraph,
    module: str,
    chunks: list[Chunk],
    kind: str,
    src: str,
    *,
    tier: str,
    file_path: str,
) -> set[str]:
    """The ``dst`` set of derived edge specs of ``kind`` with ``src == src``."""
    edges = graph._derive_edges(  # noqa: SLF001 - derivation seam
        module, chunks, tier=tier, file_path=file_path
    )
    return {edge.dst for edge in edges if edge.kind == kind and edge.src == src}


class TestDerivedNodes:
    """``_derive_nodes`` derives the right node set from real AST chunks."""

    def test_synthesises_a_module_node(self, graph: CodeGraph, app_chunks: list[Chunk]) -> None:
        """A file yields exactly one ``module`` node, qualified from its module name.

        Tier/file_path are storage stamps the shell applies, so the derived module
        node's identity is its qualified name alone.
        """
        nodes = graph._derive_nodes(APP_MODULE, app_chunks)  # noqa: SLF001 - derivation seam
        module_nodes = [node for node in nodes if node.kind == KIND_MODULE]
        assert len(module_nodes) == 1
        assert module_nodes[0].qualified_name == APP_MODULE

    def test_creates_a_class_node_per_class(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level class becomes a ``class`` node with a dotted qualified name."""
        assert _derived_qnames(graph, APP_MODULE, app_chunks, KIND_CLASS) == {FQN_BASE, FQN_INDEX}

    def test_creates_a_method_node_per_method(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each method becomes a ``method`` node qualified by its class."""
        assert _derived_qnames(graph, APP_MODULE, app_chunks, KIND_METHOD) == {FQN_START, FQN_BOOT}

    def test_creates_a_function_node_per_top_level_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Each top-level function becomes a ``function`` node."""
        assert _derived_qnames(graph, APP_MODULE, app_chunks, KIND_FUNCTION) == {FQN_LOAD_CONFIG}

    def test_module_node_chunk_id_is_none(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The synthesised module node carries ``chunk_id is None`` (it has no chunk)."""
        nodes = graph._derive_nodes(APP_MODULE, app_chunks)  # noqa: SLF001 - derivation seam
        module_nodes = [node for node in nodes if node.kind == KIND_MODULE]
        assert module_nodes, "a module node must be derived"
        assert all(node.chunk_id is None for node in module_nodes)


class TestStructuralDefinesEdges:
    """``defines`` is structural — derived from chunks alone, no resolution needed."""

    def test_defines_edges_module_to_class_and_function(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """The module ``defines`` each top-level class and function (not methods)."""
        assert _derived_refs(
            graph, APP_MODULE, app_chunks, EDGE_DEFINES, APP_MODULE,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == {FQN_BASE, FQN_INDEX, FQN_LOAD_CONFIG}

    def test_defines_edges_class_to_its_methods(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """A class ``defines`` exactly its own methods."""
        assert _derived_refs(
            graph, APP_MODULE, app_chunks, EDGE_DEFINES, FQN_INDEX,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == {FQN_BOOT}

    def test_defines_emitted_without_project_roots(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Structural ``defines`` work with NO roots — the rootless degrade path.

        The ``graph`` fixture has no project roots, so resolution is skipped; the
        structural ``defines`` edges must still be present (the object stays useful
        without roots), while the resolution-only kinds are absent.
        """
        assert _derived_refs(
            graph, APP_MODULE, app_chunks, EDGE_DEFINES, APP_MODULE,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        )  # structural defines present
        # No resolution → no inherits/imports for this file.
        assert _derived_refs(
            graph, APP_MODULE, app_chunks, EDGE_INHERITS, FQN_INDEX,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == set()
        assert _derived_refs(
            graph, APP_MODULE, app_chunks, EDGE_IMPORTS, APP_MODULE,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == set()


class TestResolvedEdges:
    """``imports`` / ``inherits`` / ``calls`` are astroid-RESOLVED (the contract change)."""

    def test_inherits_edge_is_the_resolved_fqn_not_bare(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """``IndexService`` inherits ``demo.service.BaseService`` — the FQN, NOT bare.

        Independent oracle: ``BaseService`` is defined in APP_SOURCE in the SAME
        module, so its FQN is ``demo.service.BaseService``. The deliberate contract
        change: the old engine stored the bare ``BaseService``; this one stores the
        resolved FQN.
        """
        graph, _root = resolved_graph
        bases = _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_INHERITS, FQN_INDEX,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        )
        assert bases == {FQN_BASE}
        assert "BaseService" not in bases, "the bare name must NOT be stored — resolution wins"

    def test_in_project_import_resolves_to_symbol_fqn(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """``from demo.errors import LoadError`` resolves to the symbol FQN.

        Independent oracle: ERRORS_SOURCE defines ``LoadError`` in ``demo/errors.py``
        → ``demo.errors.LoadError``. An in-project from-import becomes the SYMBOL
        target, not the bare module name.
        """
        graph, _root = resolved_graph
        assert FQN_LOAD_ERROR in _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_IMPORTS, APP_MODULE,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        )

    def test_external_imports_are_dropped(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """``json`` and ``pathlib`` (resolved + external) are DROPPED, not kept.

        Independent oracle: both are stdlib, so they resolve EXTERNAL and the
        keep/drop rule drops them. The old engine kept every import; this is the
        precision win.
        """
        graph, _root = resolved_graph
        imports = _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_IMPORTS, APP_MODULE,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        )
        assert "json" not in imports
        assert "pathlib" not in imports
        # Only the in-project symbol import survives.
        assert imports == {FQN_LOAD_ERROR}

    def test_in_project_call_resolves_to_callee_fqn(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """``IndexService.boot`` calls resolve to in-project callee FQNs.

        Independent oracle: ``boot`` calls ``load_config(path)`` (→ the top-level
        ``demo.service.load_config``) and ``self.start()`` (→ the inherited
        ``demo.service.BaseService.start``). Both are in-project, so both are KEPT
        as resolved FQNs.
        """
        graph, _root = resolved_graph
        called = _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_CALLS, FQN_BOOT,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        )
        assert FQN_LOAD_CONFIG in called
        assert FQN_START in called

    def test_external_calls_are_dropped(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """``load_config``'s stdlib calls (``json.loads`` / ``Path``) are DROPPED.

        Independent oracle: ``load_config`` calls only stdlib (``json.loads``,
        ``Path(...).read_text()``), all resolved EXTERNAL, so it has NO kept calls.
        """
        graph, _root = resolved_graph
        assert _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_CALLS, FQN_LOAD_CONFIG,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == set()

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
        graph = _new_graph(
            tmp_path,
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            bases = _derived_refs(
                graph, "pkg.widget", _chunk("pkg/widget.py", mystery_source),
                EDGE_INHERITS, "pkg.widget.Widget",
                tier=SAMPLE_TIER, file_path="pkg/widget.py",
            )
            # The bare written base is kept (never dropped) because astroid could
            # not infer it — the conservative fallback.
            assert "MysteryBase" in bases
        finally:
            _close_graph(graph)

    def test_resolved_flag_records_resolution_status(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """The ``resolved`` flag is ``True`` on the in-project inferred inherits edge."""
        graph, _root = resolved_graph
        edges = graph._derive_edges(  # noqa: SLF001 - derivation seam
            APP_MODULE, _chunk(APP_PATH, APP_SOURCE), tier=SAMPLE_TIER, file_path=APP_PATH
        )
        resolved_by_dst = {
            edge.dst: edge.resolved
            for edge in edges
            if edge.kind == EDGE_INHERITS and edge.src == FQN_INDEX
        }
        assert resolved_by_dst.get(FQN_BASE) is True


class TestDerivationFreshness:
    """The derivation is deterministic and re-derives fresh from the current chunks.

    The kuzu shell's per-file replace semantics (delete + rebuild leaves no orphan)
    reduce, at the derivation seam, to two properties: the derivation is a pure,
    self-deduped function of the chunk set, and re-deriving from EDITED chunks
    yields ONLY the surviving symbols/edges — no fabricated leftover. The storage
    delete/tier-scoping behaviour is pinned against the live SurrealDB engine in
    ``test_graph_surreal.py`` (it has no derivation analog — the specs carry no
    tier/file_path).
    """

    def test_derivation_is_deterministic_and_deduped(
        self, graph: CodeGraph, app_chunks: list[Chunk]
    ) -> None:
        """Deriving the same file twice yields identical, non-duplicated node specs."""
        first = graph._derive_nodes(APP_MODULE, app_chunks)  # noqa: SLF001 - derivation seam
        second = graph._derive_nodes(APP_MODULE, app_chunks)  # noqa: SLF001 - derivation seam
        first_keys = [(node.kind, node.qualified_name) for node in first]
        second_keys = [(node.kind, node.qualified_name) for node in second]
        assert first_keys == second_keys  # deterministic
        assert len(first_keys) == len(set(first_keys))  # no duplicate (kind, qualified_name)
        assert first_keys  # sanity: the file actually produced nodes

    def test_fresh_derivation_drops_removed_symbols(
        self, resolved_graph: tuple[CodeGraph, Path]
    ) -> None:
        """Re-deriving from EDITED chunks drops removed symbols AND their resolved edges.

        The freshness contract: a re-derive from the trimmed chunks must leave NO
        node or reference pointing at a symbol that no longer exists in the file.
        Run on the resolution-enabled core so the removed ``inherits`` edge is a
        RESOLVED one (the disk edit is re-read via astroid's per-target evict).
        """
        graph, project_root = resolved_graph
        assert _derived_refs(
            graph, APP_MODULE, _chunk(APP_PATH, APP_SOURCE), EDGE_INHERITS, FQN_INDEX,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == {FQN_BASE}, "seed: inherits edge present"

        # Edit on disk AND re-derive from the trimmed chunks: only the helper survives.
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
        trimmed_chunks = _chunk(APP_PATH, trimmed)

        remaining = (
            _derived_qnames(graph, APP_MODULE, trimmed_chunks, KIND_CLASS)
            | _derived_qnames(graph, APP_MODULE, trimmed_chunks, KIND_METHOD)
            | _derived_qnames(graph, APP_MODULE, trimmed_chunks, KIND_FUNCTION)
        )
        assert FQN_INDEX not in remaining
        assert FQN_START not in remaining
        assert FQN_LOAD_CONFIG in remaining
        # No orphan inherits edge to the deleted subclass is derived.
        assert _derived_refs(
            graph, APP_MODULE, trimmed_chunks, EDGE_INHERITS, FQN_INDEX,
            tier=SAMPLE_TIER, file_path=APP_PATH,
        ) == set()


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
    """The derivation is generic over any Python AST chunks — zero Odoo coupling."""

    def test_handles_an_arbitrary_python_module(self, tmp_path: Path) -> None:
        """A plain, non-Odoo module derives cleanly with no domain-specific handling."""
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
        graph = _new_graph(
            tmp_path,
            tier_roots={SAMPLE_TIER: project_root},
            project_roots=[project_root],
        )
        try:
            chunks = _chunk("util/paths.py", source)
            kinds = {node.kind for node in graph._derive_nodes("util.paths", chunks)}  # noqa: SLF001
            # Only the four generic kinds appear — no Odoo-flavoured node kind.
            assert kinds <= {KIND_MODULE, KIND_CLASS, KIND_METHOD, KIND_FUNCTION}
            assert kinds  # something was derived
            # ``os`` is stdlib → resolved external → DROPPED (the precision win).
            assert "os" not in _derived_refs(
                graph, "util.paths", chunks, EDGE_IMPORTS, "util.paths",
                tier=SAMPLE_TIER, file_path="util/paths.py",
            )
        finally:
            _close_graph(graph)


class TestResolutionCachePoisoningGuard:
    """The chunker must NOT poison resolution — without any per-file cache wipe.

    The real :class:`PythonAstChunker` parses with astroid while chunking, and
    astroid's manager is a process-global borg. The OLD guard was a brute
    whole-cache ``clear_resolution_cache()`` before AND after every file's resolve
    — correct, but O(files × dependency-fanout): each clear threw away every
    dependency module, forcing astroid to re-parse them for the next file. At Odoo
    scale (30–50k files) that made the cold graph build take hours and blocked
    server startup.

    The fix moves the guarantee UPSTREAM: the chunker's structural parse no longer
    follows / resolves imports, so it leaves NO cached import FAILURE in astroid's
    shared manager. With the poison gone, the derivation drops the per-file
    whole-cache wipe and the dependency cache PERSISTS across files within a sweep
    — parsed ~once per sweep, not once per file.

    These tests pin the POST-FIX property DIRECTLY at the derivation seam: a
    cross-module in-project reference still resolves to its FQN after the real
    chunker has run over many in-project modules — and it does so WITHOUT any
    per-file cache clear. They fail if the chunker's structural parse ever starts
    poisoning the resolver again.
    """

    @staticmethod
    def _write_two_module_pkg(root: Path) -> tuple[str, str]:
        """A two-module in-project package: ``service`` INHERITS from + CALLS ``base``.

        Cross-module inheritance/call inference is the cache-sensitive path — it
        (unlike a plain import) is what degrades to bare names when the chunker
        poisons astroid's shared manager. Returns ``(base_src, service_src)``.
        """
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
        return base_src, service_src

    def test_cross_module_call_and_inherit_resolve_after_chunker_poisons_cache(
        self,
        tmp_path: Path,
    ) -> None:
        root = tmp_path / "proj"
        base_src, service_src = self._write_two_module_pkg(root)
        graph = _new_graph(
            tmp_path,
            tier_roots={SAMPLE_TIER: root},
            project_roots=[root],
        )
        try:
            # Production order: run the REAL chunker over BOTH modules first
            # (the structural parse that USED to poison the manager), THEN derive.
            _chunk("pkg/base.py", base_src)
            _chunk("pkg/service.py", service_src)
            inherits = _derived_refs(
                graph, "pkg.service", _chunk("pkg/service.py", service_src),
                EDGE_INHERITS, "pkg.service.Service",
                tier=SAMPLE_TIER, file_path="pkg/service.py",
            )
            calls = _derived_refs(
                graph, "pkg.service", _chunk("pkg/service.py", service_src),
                EDGE_CALLS, "pkg.service.Service.run",
                tier=SAMPLE_TIER, file_path="pkg/service.py",
            )
            # Cross-module references must carry the in-project FQN. The bare name is
            # the degraded form that appears iff the chunker poisons the resolver.
            assert "pkg.base.Base" in inherits, (
                f"inherits degraded — chunker poisoned resolution; got {inherits!r}"
            )
            assert "pkg.base.helper" in calls, (
                f"call degraded — chunker poisoned resolution; got {calls!r}"
            )
            assert "Base" not in inherits and "helper" not in calls
        finally:
            _close_graph(graph)

    def test_resolution_survives_without_a_per_file_cache_clear(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """The FQN survives even if the per-file whole-cache wipe is a no-op.

        This is the anti-regression that pins the fix's PROVENANCE: it neuters
        :func:`clear_resolution_cache` (the per-file wipe) so the ONLY thing that
        can keep resolution correct is the chunker NOT poisoning the manager. If a
        future change reintroduces chunker poisoning, this fails even though the
        old test (which still benefits from any incidental clears) might not.
        """
        import loremaster.graph as graph_module

        monkeypatch.setattr(graph_module, "clear_resolution_cache", lambda: None)

        root = tmp_path / "proj"
        base_src, service_src = self._write_two_module_pkg(root)
        graph = _new_graph(
            tmp_path,
            tier_roots={SAMPLE_TIER: root},
            project_roots=[root],
        )
        try:
            _chunk("pkg/base.py", base_src)
            _chunk("pkg/service.py", service_src)
            inherits = _derived_refs(
                graph, "pkg.service", _chunk("pkg/service.py", service_src),
                EDGE_INHERITS, "pkg.service.Service",
                tier=SAMPLE_TIER, file_path="pkg/service.py",
            )
            calls = _derived_refs(
                graph, "pkg.service", _chunk("pkg/service.py", service_src),
                EDGE_CALLS, "pkg.service.Service.run",
                tier=SAMPLE_TIER, file_path="pkg/service.py",
            )
            assert "pkg.base.Base" in inherits, (
                "with the per-file clear neutered, the chunker poisoned resolution; "
                f"got {inherits!r}"
            )
            assert "pkg.base.helper" in calls, (
                "with the per-file clear neutered, the chunker poisoned resolution; "
                f"got {calls!r}"
            )
        finally:
            _close_graph(graph)

    def test_common_dependency_is_parsed_once_across_a_sweep(
        self,
        tmp_path: Path,
    ) -> None:
        """A dependency shared by N files is parsed ~once per sweep, not once per file.

        The performance invariant. ``N`` in-project consumers all inherit from one
        common ``base`` module. Deriving all N file slices in one sweep must parse
        ``base.py`` from disk AT MOST ONCE — the warm dependency cache is reused
        across files. Under the OLD per-file whole-cache wipe this was ``N`` (the
        clear threw ``base`` away between every file), so this test FAILS pre-fix
        and PASSES post-fix.
        """
        import astroid.builder as astroid_builder

        root = tmp_path / "proj"
        (root / "pkg").mkdir(parents=True)
        (root / "pkg" / "__init__.py").write_text("", encoding="utf-8")
        (root / "pkg" / "base.py").write_text(
            "class Base:\n    def greet(self):\n        return 1\n", encoding="utf-8"
        )
        base_path = str(root / "pkg" / "base.py")
        consumer_count = 5
        for index in range(consumer_count):
            (root / "pkg" / f"c{index}.py").write_text(
                f"from pkg.base import Base\n\n\n"
                f"class C{index}(Base):\n    def m(self):\n        return self.greet()\n",
                encoding="utf-8",
            )

        # Spy on astroid building base.py FROM FILE — the expensive re-parse the
        # per-file clear used to force. file_build is astroid's path->module parse.
        base_parse_count = {"n": 0}
        original_file_build = astroid_builder.AstroidBuilder.file_build

        def counting_file_build(self, path, modname=None):  # type: ignore[no-untyped-def]
            if path == base_path:
                base_parse_count["n"] += 1
            return original_file_build(self, path, modname)

        graph = _new_graph(
            tmp_path,
            tier_roots={SAMPLE_TIER: root},
            project_roots=[root],
        )
        try:
            # Chunk everything first (production order), then derive each consumer
            # in one sweep. The dependency must be parsed from file at most once.
            for index in range(consumer_count):
                src = (root / "pkg" / f"c{index}.py").read_text(encoding="utf-8")
                _chunk(f"pkg/c{index}.py", src)
            astroid_builder.AstroidBuilder.file_build = counting_file_build  # type: ignore[method-assign]
            try:
                for index in range(consumer_count):
                    src = (root / "pkg" / f"c{index}.py").read_text(encoding="utf-8")
                    inherits = _derived_refs(
                        graph, f"pkg.c{index}", _chunk(f"pkg/c{index}.py", src),
                        EDGE_INHERITS, f"pkg.c{index}.C{index}",
                        tier=SAMPLE_TIER, file_path=f"pkg/c{index}.py",
                    )
                    # Sanity: each consumer still resolves its base in-project.
                    assert "pkg.base.Base" in inherits, (
                        f"c{index} failed to resolve base in-project: {inherits!r}"
                    )
            finally:
                astroid_builder.AstroidBuilder.file_build = original_file_build  # type: ignore[method-assign]
            assert base_parse_count["n"] <= 1, (
                "the common dependency was re-parsed once per file — the per-file "
                f"cache wipe was not removed; parsed {base_parse_count['n']} times "
                f"across {consumer_count} files (expected <= 1)"
            )
        finally:
            _close_graph(graph)
