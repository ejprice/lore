"""Typed code-graph — a SQLite side-structure derived from python_ast chunks.

This is Deliverable 3, the capability layer: a typed code-graph built as a
SQLite SIDE-structure (there is NO new vector index — the graph lives alongside
the manifest, not inside Qdrant). It is GENERIC over any Python AST chunks the
lorescribe :class:`~lorescribe.python_ast.PythonAstChunker` emits — there is
ZERO Odoo-specific handling. A watcher / reconcile pass keeps it fresh by
rebuilding one file's slice transactionally (delete + rebuild), exactly the way
the indexer refreshes a file's vector points.

Schema (two tables, real SQLite, WAL):

* ``nodes(id, kind, qualified_name, file_path, chunk_id, tier)`` — one row per
  graph node. ``id`` is an autoincrement surrogate; the natural key is
  ``(tier, file_path, qualified_name, kind)``. ``kind`` is one of
  :data:`KIND_MODULE` / :data:`KIND_CLASS` / :data:`KIND_METHOD` /
  :data:`KIND_FUNCTION`. ``qualified_name`` is the dotted name
  (``demo.service``, ``demo.service.IndexService``,
  ``demo.service.IndexService.boot``). ``chunk_id`` is the originating chunk's
  ``identity`` (the within-file natural key) — ``NULL`` for the synthesised
  module node, which has no chunk of its own.
* ``edges(src, dst, kind)`` — one directed edge per row. ``kind`` is one of
  :data:`EDGE_DEFINES` / :data:`EDGE_INHERITS` / :data:`EDGE_IMPORTS` /
  :data:`EDGE_CALLS`. An edge also carries ``tier`` and ``file_path`` (the file
  whose rebuild owns it) so a per-file rebuild can purge exactly its own edges
  with no orphans and no collateral damage to sibling files/tiers.

**What each edge kind is derived from (and what it cannot be):**

* ``defines`` — FULLY derived from the chunk set's structure. The module node
  ``defines`` every top-level class and top-level function; each class node
  ``defines`` its own methods (via the ``method`` chunk's ``class_name``
  metadata). ``dst`` is the fully-qualified node name.
* ``inherits`` — FULLY derived from the ``class`` chunk's ``inherits`` metadata
  list (the bare base names the AST captured as ``ast.Name`` bases). ``dst`` is
  the bare base name (``BaseService``); a dotted base like ``ast.NodeVisitor``
  is NOT captured by the chunker and so produces no edge — we never fabricate a
  resolution we cannot prove. Read ONLY from ``class`` chunks: a ``method``
  chunk also carries its class's ``inherits`` list (it is inherited context),
  so reading it there would fabricate a spurious method→base edge.
* ``imports`` — FULLY derived, but the imported names live ONLY in the
  ``imports`` chunk's ``source_text`` (the chunker puts none in metadata), so
  they are re-parsed from that source with ``ast``. ``dst`` is the imported
  module / dotted name (``json``, ``pathlib``, ``demo.errors``). A
  ``from x import y`` records ``x`` (the module pulled in); a bare ``import a.b``
  records ``a.b``. ``__future__`` is skipped (a compiler directive, not a real
  dependency).
* ``calls`` — BEST-EFFORT, parsed from each ``method`` / ``function`` chunk's
  ``source_text`` by walking ``ast.Call`` nodes. ``dst`` is the called NAME — a
  bare ``Name`` func (``load_config``) or the trailing attribute of an
  ``Attribute`` func (``loads`` from ``json.loads``). It is NOT resolved to a
  defining node, because one file's chunk set cannot resolve a cross-module
  callee; the call graph is a hint, not a proof. We do not guess at dynamic
  dispatch, ``getattr`` calls, or calls assembled at runtime.

Query functions:

* :meth:`CodeGraph.what_imports` — the reverse of the import edge: every module
  node with an ``imports`` edge whose ``dst`` equals the target.
* :meth:`CodeGraph.blast_radius` — the BOUNDED reverse-edge transitive closure.
  Walks edges backwards from the target (an edge ``a -kind-> b`` means "a
  depends on b", so b's dependents are the ``src`` of edges whose ``dst`` is b)
  across ALL edge kinds, stopping at ``depth`` hops and clamping the result set
  at ``max_results`` so a pathological fan-out cannot blow up. Frontier matching
  spans the name-resolution seam: an edge ``dst`` may be a bare name
  (``inherits`` / ``calls`` / ``imports``) or a qualified name (``defines``), so
  a node is reached when an edge ``dst`` equals EITHER its qualified name OR its
  bare last segment.
* :meth:`CodeGraph.tests_for` — test nodes related to a symbol or file. A node
  is a test node when its ``file_path`` matches a test glob
  (:data:`TEST_PATH_GLOBS`). It is returned when EITHER it sits in a test file
  with an edge into the target's file/symbol, OR the ``test_x`` ↔ ``x`` name
  heuristic links it (a ``test_boot`` function is a test for symbol ``boot``).
"""

from __future__ import annotations

import ast
import sqlite3
import textwrap
from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from lorescribe.python_ast import (
    CHUNK_TYPE_CLASS,
    CHUNK_TYPE_FUNCTION,
    CHUNK_TYPE_IMPORTS,
    CHUNK_TYPE_METHOD,
)
from pydantic import BaseModel, ConfigDict

from loremaster.index.sqlite_resilient import open_resilient_sqlite

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from lorescribe.models import Chunk

# -- Node kinds ------------------------------------------------------------
KIND_MODULE = "module"
KIND_CLASS = "class"
KIND_METHOD = "method"
KIND_FUNCTION = "function"

# -- Edge kinds ------------------------------------------------------------
EDGE_IMPORTS = "imports"
EDGE_CALLS = "calls"
EDGE_INHERITS = "inherits"
EDGE_DEFINES = "defines"

# The dotted-name separator joining module → class → method qualified names.
_QUALIFIER_SEPARATOR = "."

# The Python source-file suffix whose stem becomes the module qualified name.
_PYTHON_SUFFIX = ".py"

# The package-marker file. A directory containing this is an importable package;
# the SHALLOWEST such directory in a file's path chain is the package TOP, and
# everything to its left (a workspace-member / src dir) is NOT part of the
# importable dotted path. This is how ``loremaster/loremaster/config.py`` (under
# a repo root whose ``loremaster/`` member dir has no ``__init__.py``) resolves to
# the importable ``loremaster.config`` rather than the doubled
# ``loremaster.loremaster.config``.
_PACKAGE_MARKER = "__init__.py"

# The stem an ``__init__.py`` collapses to its package under.
_INIT_STEM = "__init__"

# Import statements naming this module are compiler directives, never real
# dependencies, so they are not turned into ``imports`` edges.
_FUTURE_MODULE = "__future__"

# Globs (matched against the POSIX file path) that mark a node as a TEST node.
# A path is a test if its basename matches ``test_*.py`` / ``*_test.py`` OR any
# path segment is a ``tests`` directory. These mirror pytest's own discovery.
TEST_PATH_GLOBS: tuple[str, ...] = ("test_*.py", "*_test.py")
_TESTS_DIR_NAME = "tests"

# The conventional prefix a test function carries for the symbol it exercises:
# ``test_boot`` tests ``boot`` (the ``test_x`` ↔ ``x`` heuristic).
_TEST_NAME_PREFIX = "test_"

# Schema DDL. Executed idempotently on every open so a fresh and a reopened db
# both arrive at the same schema. WAL is enabled (see __init__) so concurrent
# readers (MCP graph lookups) never block the single writer (watcher/reconcile).
# Edges carry (tier, file_path) so a per-file rebuild purges exactly its own.
_SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    kind           TEXT NOT NULL,
    qualified_name TEXT NOT NULL,
    file_path      TEXT NOT NULL,
    chunk_id       TEXT,
    tier           TEXT NOT NULL,
    UNIQUE (tier, file_path, kind, qualified_name)
);
CREATE TABLE IF NOT EXISTS edges (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    src       TEXT NOT NULL,
    dst       TEXT NOT NULL,
    kind      TEXT NOT NULL,
    tier      TEXT NOT NULL,
    file_path TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_nodes_tier_file ON nodes (tier, file_path);
CREATE INDEX IF NOT EXISTS idx_nodes_qname ON nodes (qualified_name);
CREATE INDEX IF NOT EXISTS idx_edges_tier_file ON edges (tier, file_path);
CREATE INDEX IF NOT EXISTS idx_edges_dst_kind ON edges (dst, kind);
"""


class GraphNode(BaseModel):
    """A single decoded ``nodes`` row.

    Attributes:
        id: The surrogate autoincrement row id.
        kind: One of :data:`KIND_MODULE` / :data:`KIND_CLASS` /
            :data:`KIND_METHOD` / :data:`KIND_FUNCTION`.
        qualified_name: The dotted name (``demo.service.IndexService.boot``).
        file_path: The tier-relative POSIX path the node was derived from.
        chunk_id: The originating chunk's ``identity`` (``None`` for the
            synthesised module node).
        tier: The source tier the node belongs to.
    """

    model_config = ConfigDict(extra="forbid")

    id: int
    kind: str
    qualified_name: str
    file_path: str
    chunk_id: str | None
    tier: str


class _NodeSpec(BaseModel):
    """An intermediate node-to-insert, before it acquires a row id."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    qualified_name: str
    chunk_id: str | None


class _EdgeSpec(BaseModel):
    """An intermediate edge-to-insert."""

    model_config = ConfigDict(extra="forbid")

    src: str
    dst: str
    kind: str


class CodeGraph:
    """A typed code-graph over Python AST chunks, backed by WAL SQLite.

    The database path is configurable; pass a real file path (WAL across
    connections is meaningless for ``:memory:``). The schema is created on
    construction. Every mutation is tier- and file-scoped so a per-file rebuild
    or delete never touches a sibling file or tier (the C1 discipline the
    manifest already follows).

    Args:
        db_path: The SQLite database path (a real file).
    """

    def __init__(self, db_path: str) -> None:
        """Open (or create) the graph database, enable WAL, ensure schema.

        The open is RESILIENT (FP-01 + FP-08): an absent parent dir is created
        and a corrupt on-disk image is deleted and recreated, both via
        :func:`~loremaster.index.sqlite_resilient.open_resilient_sqlite`. A
        valid existing graph — including a zero-byte file — opens UNCHANGED.
        """
        # ``check_same_thread=False`` (inside the resilient helper) so the
        # single-writer graph can be driven from the asyncio loop thread and a
        # watcher thread under the caller's own lock — the same concurrency
        # contract the manifest follows.
        self._connection = open_resilient_sqlite(db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA journal_mode = WAL")
        self._connection.executescript(_SCHEMA)
        self._connection.commit()

    @property
    def connection(self) -> sqlite3.Connection:
        """The underlying SQLite connection (for diagnostics and tests)."""
        return self._connection

    def close(self) -> None:
        """Close the underlying database connection."""
        self._connection.close()

    def indexed_file_count(self) -> int:
        """Return the number of distinct files the graph currently holds nodes for.

        The graph's view of "how many files are live", across every tier. The
        store-divergence reconcile compares it against the manifest's
        ``indexed_file_count`` to detect a wiped/empty ``graph.db`` the manifest
        still calls indexed (FP-04): a zero graph count over a positive manifest
        count triggers a re-graph so ``what_imports`` / ``tests_for`` stop
        silently returning nothing.

        Returns:
            The count of distinct ``(tier, file_path)`` files with graph nodes
            (``0`` for a fresh or wiped graph).
        """
        # A file's identity in the graph is the same (tier, file_path) pair the
        # node rows are scoped by (C1), so DISTINCT over that pair is the file
        # count. A wiped graph (no node rows) yields 0 — the FP-04 trigger.
        row = self._connection.execute(
            "SELECT COUNT(DISTINCT tier || ? || file_path) AS n FROM nodes",
            (_QUALIFIER_SEPARATOR,),
        ).fetchone()
        return int(row["n"])

    # -- naming helpers ----------------------------------------------------

    @staticmethod
    def module_qualified_name(file_path: str) -> str:
        """Derive the dotted module name from a tier-relative POSIX path.

        ``demo/service.py`` → ``demo.service``; an ``__init__.py`` collapses to
        its package (``demo/__init__.py`` → ``demo``). The suffix is stripped and
        the path separators become dots.

        Args:
            file_path: The tier-relative POSIX file path.

        Returns:
            The dotted module qualified name.
        """
        path = PurePosixPath(file_path)
        parts = list(path.parts)
        stem = path.stem
        if stem == "__init__":
            parts = parts[:-1]
        else:
            parts[-1] = stem
        return _QUALIFIER_SEPARATOR.join(parts)

    @staticmethod
    def importable_module_name(base: Path, file_path: str) -> str:
        """Derive the TRUE importable dotted module name from an on-disk layout.

        The fix for the split-brain module identity: :meth:`module_qualified_name`
        joins EVERY segment of the tier-relative path, so a workspace-member
        layout (``loremaster/loremaster/config.py`` under a repo root whose
        ``loremaster/`` member dir has no ``__init__.py``) yields the DOUBLED,
        non-importable ``loremaster.loremaster.config`` — which never matches the
        ``imports``-edge ``dst`` strings (the real import ``loremaster.config``).

        This resolver strips leading path segments up to the top of the package:
        the SHALLOWEST directory in ``file_path``'s chain that contains an
        ``__init__.py`` (probed under ``base`` on disk) is the package top, and
        everything to its left is dropped. From the package top, ``/`` → ``.``,
        the ``.py`` suffix is dropped, and an ``__init__.py`` collapses to its
        package — yielding the importable dotted path
        (``loremaster/loremaster/config.py`` → ``loremaster.config``).

        Fallback (documented): if NO directory in the chain contains an
        ``__init__.py`` — a namespace / ``src`` layout, or a path with no file on
        disk (the direct ``index_file`` test seam) — nothing is stripped and the
        full tier-relative path is joined, exactly as
        :meth:`module_qualified_name` does. The derivation degrades gracefully
        rather than crashing, and the bare-package and top-level-module cases fall
        out of the same logic.

        Args:
            base: The tier's on-disk root that ``file_path`` is relative to (the
                directory probed for ``__init__.py`` package markers).
            file_path: The tier-relative POSIX file path.

        Returns:
            The importable dotted module qualified name.
        """
        path = PurePosixPath(file_path)
        parts = list(path.parts)
        # The directories in the chain, left → right (exclude the file itself).
        directories = parts[:-1]

        # Find the SHALLOWEST directory that is a package (has __init__.py on
        # disk). Everything left of it is a non-package member/src dir to strip.
        package_top_index: int | None = None
        for index in range(len(directories)):
            candidate_dir = base / PurePosixPath(*parts[: index + 1])
            if (candidate_dir / _PACKAGE_MARKER).is_file():
                package_top_index = index
                break

        # Fallback: no package marker anywhere → strip nothing (namespace/src
        # layout, or a path with no file on disk). Matches module_qualified_name.
        start = package_top_index if package_top_index is not None else 0
        kept = parts[start:]

        # Collapse __init__.py to its package; otherwise drop the .py suffix.
        if path.stem == _INIT_STEM:
            kept = kept[:-1]
        else:
            kept[-1] = path.stem
        return _QUALIFIER_SEPARATOR.join(kept)

    @staticmethod
    def _bare_name(qualified_name: str) -> str:
        """The last dotted segment of a qualified name (``a.b.c`` → ``c``)."""
        return qualified_name.rsplit(_QUALIFIER_SEPARATOR, 1)[-1]

    # -- per-file build / delete -------------------------------------------

    def build_file_graph(
        self,
        tier: str,
        file_path: str,
        chunks: Sequence[Chunk],
        *,
        module_name: str | None = None,
    ) -> None:
        """Derive and store the nodes/edges for one file, transactionally.

        A per-file rebuild: the file's prior nodes and edges are deleted and the
        freshly-derived set inserted inside ONE transaction, so a concurrent
        reader never sees a half-applied graph and a removed symbol leaves no
        orphan edge behind. The delete and the insert are both tier- and
        file-scoped, so another tier's copy of the same path (C1) and sibling
        files are untouched.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path (still the tier-scoping
                key for the node/edge rows — deletes and C1 isolation key on it).
            chunks: The file's lorescribe AST chunks (any python_ast chunk set).
            module_name: The module prefix every node/edge ``src`` is qualified
                under. The indexer passes the TRUE importable dotted path (derived
                from the on-disk package layout via
                :meth:`importable_module_name`), so node names match the
                ``imports``-edge ``dst`` strings. When ``None`` (direct in-memory
                test calls with no filesystem behind ``file_path``), it falls back
                to the pure path-join :meth:`module_qualified_name`.
        """
        module = module_name if module_name is not None else self.module_qualified_name(file_path)
        nodes, edges = self._derive(module, chunks)
        with self._connection:
            self._delete_file_rows(tier, file_path)
            for node in nodes:
                self._connection.execute(
                    """
                    INSERT INTO nodes (kind, qualified_name, file_path, chunk_id, tier)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (node.kind, node.qualified_name, file_path, node.chunk_id, tier),
                )
            for edge in edges:
                self._connection.execute(
                    """
                    INSERT INTO edges (src, dst, kind, tier, file_path)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (edge.src, edge.dst, edge.kind, tier, file_path),
                )

    def delete_file_graph(self, tier: str, file_path: str) -> None:
        """Remove every node and edge owned by ``(tier, file_path)``.

        Tier-scoped: the same path's rows under other tiers survive (C1). Used by
        the watcher when a file is removed, and internally by the rebuild.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path to purge.
        """
        with self._connection:
            self._delete_file_rows(tier, file_path)

    def _delete_file_rows(self, tier: str, file_path: str) -> None:
        """Delete a file's nodes and edges (caller owns the transaction)."""
        self._connection.execute(
            "DELETE FROM nodes WHERE tier = ? AND file_path = ?", (tier, file_path)
        )
        self._connection.execute(
            "DELETE FROM edges WHERE tier = ? AND file_path = ?", (tier, file_path)
        )

    # -- derivation (pure: chunks → node/edge specs) -----------------------

    def _derive(
        self, module: str, chunks: Sequence[Chunk]
    ) -> tuple[list[_NodeSpec], list[_EdgeSpec]]:
        """Derive the node and edge specs for a file from its AST chunks.

        Pure with respect to the database: takes the module qualified name and
        the chunk set, returns the node/edge specs to insert. The module node is
        synthesised (no chunk of its own); every other node maps to one chunk.
        """
        nodes: list[_NodeSpec] = [
            _NodeSpec(kind=KIND_MODULE, qualified_name=module, chunk_id=None)
        ]
        edges: list[_EdgeSpec] = []

        for chunk in chunks:
            if chunk.chunk_type == CHUNK_TYPE_IMPORTS:
                edges.extend(self._import_edges(module, chunk))
            elif chunk.chunk_type == CHUNK_TYPE_CLASS:
                nodes.append(self._class_node(module, chunk))
                edges.extend(self._class_edges(module, chunk))
            elif chunk.chunk_type == CHUNK_TYPE_METHOD:
                nodes.append(self._method_node(module, chunk))
                edges.extend(self._method_edges(module, chunk))
            elif chunk.chunk_type == CHUNK_TYPE_FUNCTION:
                nodes.append(self._function_node(module, chunk))
                edges.extend(self._function_edges(module, chunk))
            # Any other chunk_type (e.g. the syntax-error ``python_window``
            # fallback) carries no derivable structure and is skipped — the
            # graph degrades to "no edges for this file" rather than guessing.

        return self._dedupe_nodes(nodes), edges

    @staticmethod
    def _dedupe_nodes(nodes: list[_NodeSpec]) -> list[_NodeSpec]:
        """Drop duplicate node specs (same kind + qualified_name), keeping the first.

        A method reachable via a conditional ``def`` can be chunked twice (the
        chunker disambiguates the *chunk* identity with ``#N``, but the symbol's
        qualified name is the same), and the module node is synthesised once;
        the UNIQUE constraint would otherwise abort the whole rebuild.
        """
        seen: set[tuple[str, str]] = set()
        unique: list[_NodeSpec] = []
        for node in nodes:
            key = (node.kind, node.qualified_name)
            if key in seen:
                continue
            seen.add(key)
            unique.append(node)
        return unique

    # -- per-chunk-kind node builders --------------------------------------

    def _class_node(self, module: str, chunk: Chunk) -> _NodeSpec:
        """A ``class`` node, qualified ``module.ClassName``."""
        class_name = str(chunk.metadata["class_name"])
        return _NodeSpec(
            kind=KIND_CLASS,
            qualified_name=f"{module}{_QUALIFIER_SEPARATOR}{class_name}",
            chunk_id=chunk.identity,
        )

    def _method_node(self, module: str, chunk: Chunk) -> _NodeSpec:
        """A ``method`` node, qualified ``module.ClassName.method``."""
        class_name = str(chunk.metadata["class_name"])
        method_name = str(chunk.metadata["method_name"])
        qualified = _QUALIFIER_SEPARATOR.join((module, class_name, method_name))
        return _NodeSpec(kind=KIND_METHOD, qualified_name=qualified, chunk_id=chunk.identity)

    def _function_node(self, module: str, chunk: Chunk) -> _NodeSpec:
        """A ``function`` node, qualified ``module.function``."""
        function_name = str(chunk.metadata["method_name"])
        return _NodeSpec(
            kind=KIND_FUNCTION,
            qualified_name=f"{module}{_QUALIFIER_SEPARATOR}{function_name}",
            chunk_id=chunk.identity,
        )

    # -- per-chunk-kind edge builders --------------------------------------

    def _class_edges(self, module: str, chunk: Chunk) -> list[_EdgeSpec]:
        """``module defines Class`` plus one ``Class inherits Base`` per base.

        ``inherits`` is read ONLY here (from the ``class`` chunk's ``inherits``
        metadata), never from a ``method`` chunk, so a method does not fabricate
        a spurious edge to its class's bases.
        """
        class_name = str(chunk.metadata["class_name"])
        class_qualified = f"{module}{_QUALIFIER_SEPARATOR}{class_name}"
        edges: list[_EdgeSpec] = [
            _EdgeSpec(src=module, dst=class_qualified, kind=EDGE_DEFINES)
        ]
        for base in self._inherits_list(chunk):
            # ``dst`` is the bare base name the AST captured; we do not invent a
            # dotted resolution the chunker never proved.
            edges.append(_EdgeSpec(src=class_qualified, dst=base, kind=EDGE_INHERITS))
        return edges

    def _method_edges(self, module: str, chunk: Chunk) -> list[_EdgeSpec]:
        """``Class defines method`` plus best-effort ``method calls callee``."""
        class_name = str(chunk.metadata["class_name"])
        method_name = str(chunk.metadata["method_name"])
        class_qualified = f"{module}{_QUALIFIER_SEPARATOR}{class_name}"
        method_qualified = f"{class_qualified}{_QUALIFIER_SEPARATOR}{method_name}"
        edges: list[_EdgeSpec] = [
            _EdgeSpec(src=class_qualified, dst=method_qualified, kind=EDGE_DEFINES)
        ]
        edges.extend(self._call_edges(method_qualified, chunk))
        return edges

    def _function_edges(self, module: str, chunk: Chunk) -> list[_EdgeSpec]:
        """``module defines function`` plus best-effort ``function calls callee``."""
        function_name = str(chunk.metadata["method_name"])
        function_qualified = f"{module}{_QUALIFIER_SEPARATOR}{function_name}"
        edges: list[_EdgeSpec] = [
            _EdgeSpec(src=module, dst=function_qualified, kind=EDGE_DEFINES)
        ]
        edges.extend(self._call_edges(function_qualified, chunk))
        return edges

    # -- source re-parsing (imports + calls) -------------------------------

    def _import_edges(self, module: str, chunk: Chunk) -> list[_EdgeSpec]:
        """Re-parse the imports chunk's source into ``module imports target`` edges.

        The chunker stores no import names in metadata, so the raw ``source_text``
        is parsed with ``ast``. ``import a.b`` → ``a.b``; ``from x import y`` →
        ``x`` (the module pulled in). ``__future__`` is skipped. An unparseable
        fragment yields no edges (best-effort, never raises).
        """
        targets = self._parse_imported_modules(chunk.source_text)
        return [
            _EdgeSpec(src=module, dst=target, kind=EDGE_IMPORTS)
            for target in self._unique_preserving_order(targets)
        ]

    def _call_edges(self, caller: str, chunk: Chunk) -> list[_EdgeSpec]:
        """Best-effort ``caller calls callee`` edges from the chunk's source.

        Walks ``ast.Call`` nodes in the chunk's source: a bare ``Name`` func
        yields its id (``load_config``); an ``Attribute`` func yields the trailing
        attribute (``loads`` from ``json.loads``). Not resolved to a node — the
        call graph is a hint. Unparseable source yields no edges.
        """
        callees = self._parse_called_names(chunk.source_text)
        return [
            _EdgeSpec(src=caller, dst=callee, kind=EDGE_CALLS)
            for callee in self._unique_preserving_order(callees)
        ]

    @staticmethod
    def _inherits_list(chunk: Chunk) -> list[str]:
        """The base-class names from a class chunk's ``inherits`` metadata."""
        raw = chunk.metadata.get("inherits", [])
        if not isinstance(raw, list):
            return []
        return [str(base) for base in raw]

    @staticmethod
    def _parse_imported_modules(source_text: str) -> list[str]:
        """Parse import statements into the module names they pull in.

        Best-effort: a fragment that does not parse cleanly yields ``[]`` rather
        than raising — the imports chunk is real source, but a sub-split piece
        could be a partial statement.
        """
        try:
            tree = ast.parse(source_text)
        except SyntaxError:
            return []
        modules: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                modules.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                # ``from . import x`` (relative, no module) carries no target;
                # ``from x import y`` records the module ``x``.
                if node.module is not None and node.module != _FUTURE_MODULE:
                    modules.append(node.module)
        return [module for module in modules if module != _FUTURE_MODULE]

    @staticmethod
    def _parse_called_names(source_text: str) -> list[str]:
        """Parse the called names out of a function/method body, best-effort.

        A leading-indented method body does not parse on its own, so the source
        is dedented first. An unparseable fragment yields ``[]``.
        """
        try:
            tree = ast.parse(textwrap.dedent(source_text))
        except SyntaxError:
            return []
        names: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Name):
                names.append(func.id)
            elif isinstance(func, ast.Attribute):
                names.append(func.attr)
        return names

    @staticmethod
    def _unique_preserving_order(items: Iterable[str]) -> list[str]:
        """De-duplicate ``items`` while preserving first-seen order."""
        seen: set[str] = set()
        unique: list[str] = []
        for item in items:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)
        return unique

    # -- row decoding ------------------------------------------------------

    @staticmethod
    def _row_to_node(row: sqlite3.Row) -> GraphNode:
        """Decode a raw ``nodes`` row into a :class:`GraphNode`."""
        return GraphNode(
            id=row["id"],
            kind=row["kind"],
            qualified_name=row["qualified_name"],
            file_path=row["file_path"],
            chunk_id=row["chunk_id"],
            tier=row["tier"],
        )

    def _nodes_by_qualified_name(self, qualified_name: str) -> list[GraphNode]:
        """Every node (across tiers/files) whose qualified name matches exactly."""
        rows = self._connection.execute(
            "SELECT * FROM nodes WHERE qualified_name = ?", (qualified_name,)
        ).fetchall()
        return [self._row_to_node(row) for row in rows]

    # -- queries -----------------------------------------------------------

    def what_imports(self, target: str) -> list[GraphNode]:
        """Return the module nodes that import ``target``.

        The reverse of the ``imports`` edge: every ``module`` node that is the
        ``src`` of an ``imports`` edge whose ``dst`` equals ``target``.

        Args:
            target: The imported module / dotted name to find importers of
                (``demo.errors``).

        Returns:
            The importing module nodes (empty if nobody imports the target).
        """
        rows = self._connection.execute(
            """
            SELECT DISTINCT n.* FROM nodes n
            JOIN edges e ON e.src = n.qualified_name AND e.tier = n.tier
            WHERE e.kind = ? AND e.dst = ? AND n.kind = ?
            """,
            (EDGE_IMPORTS, target, KIND_MODULE),
        ).fetchall()
        return [self._row_to_node(row) for row in rows]

    def blast_radius(self, target: str, depth: int, max_results: int) -> list[GraphNode]:
        """Return the BOUNDED reverse-edge transitive closure from ``target``.

        Everything that (transitively) depends on ``target``: walk edges
        backwards (the dependents of a node are the ``src`` of edges whose ``dst``
        is that node) across ALL edge kinds, breadth-first. Bounded two ways so a
        pathological graph cannot blow up:

        * ``depth`` caps the number of reverse hops from the target.
        * ``max_results`` is a hard ceiling on the returned node count.

        Frontier matching spans the name-resolution seam: an edge ``dst`` may be
        a bare name (``inherits`` / ``calls`` / ``imports``) or a qualified name
        (``defines``), so the next reverse hop follows any edge whose ``dst``
        equals EITHER the frontier node's qualified name OR its bare last
        segment.

        Args:
            target: The qualified name to compute the blast radius of.
            depth: The maximum number of reverse hops (>= 0).
            max_results: The maximum number of nodes to return (the hard cap).

        Returns:
            Up to ``max_results`` dependent nodes, never the target itself.
        """
        if depth < 0 or max_results <= 0:
            return []

        # Frontier holds qualified names whose dependents we still need to find;
        # ``found`` collects the qualified names of reached dependents (the
        # target itself is excluded). Both are kept as names so cycles terminate.
        frontier: set[str] = {target}
        found: dict[str, GraphNode] = {}
        visited_frontier: set[str] = {target}

        for _hop in range(depth):
            if not frontier or len(found) >= max_results:
                break
            next_frontier: set[str] = set()
            for node in self._reverse_neighbours(frontier):
                if node.qualified_name == target or node.qualified_name in found:
                    continue
                found[node.qualified_name] = node
                if node.qualified_name not in visited_frontier:
                    visited_frontier.add(node.qualified_name)
                    next_frontier.add(node.qualified_name)
                if len(found) >= max_results:
                    break
            frontier = next_frontier

        return list(found.values())[:max_results]

    def _reverse_neighbours(self, frontier: set[str]) -> list[GraphNode]:
        """The dependent NODES one reverse hop back from any name in ``frontier``.

        A name in the frontier is matched against an edge ``dst`` by its full
        value AND by its bare last segment (the name-resolution seam), then the
        edge's ``src`` is resolved to the node(s) bearing that qualified name.
        """
        match_values: set[str] = set()
        for name in frontier:
            match_values.add(name)
            match_values.add(self._bare_name(name))

        placeholders = ",".join("?" for _ in match_values)
        rows = self._connection.execute(
            f"SELECT DISTINCT src FROM edges WHERE dst IN ({placeholders})",  # noqa: S608
            tuple(match_values),
        ).fetchall()

        neighbours: list[GraphNode] = []
        for row in rows:
            neighbours.extend(self._nodes_by_qualified_name(row["src"]))
        return neighbours

    def tests_for(self, symbol_or_file: str) -> list[GraphNode]:
        """Return the test nodes related to ``symbol_or_file``.

        A node is a TEST node when its ``file_path`` matches a test glob
        (:data:`TEST_PATH_GLOBS` or a ``tests/`` directory segment). A test node
        is related to the target when EITHER:

        * it has an edge (any kind) whose ``dst`` matches the target by qualified
          name or bare name, OR an ``imports`` edge to the target's module
          (a test importing the module under test); OR
        * the ``test_x`` ↔ ``x`` name heuristic links it: a ``test_boot`` node is
          a test for any symbol whose bare name is ``boot``.

        Args:
            symbol_or_file: A qualified symbol name (``demo.service.X.boot``) or a
                module name (``demo.service``).

        Returns:
            The related test nodes (de-duplicated by row id).
        """
        target_bare = self._bare_name(symbol_or_file)
        related: dict[int, GraphNode] = {}

        # 1) Test nodes whose file has an edge to the target (by qualified or bare
        #    name). A test file's edges all carry that file's (tier, file_path),
        #    so an edge into the target marks the whole test file as related.
        edge_rows = self._connection.execute(
            """
            SELECT DISTINCT n.* FROM nodes n
            JOIN edges e ON e.tier = n.tier AND e.file_path = n.file_path
            WHERE e.dst IN (?, ?)
            """,
            (symbol_or_file, target_bare),
        ).fetchall()
        for row in edge_rows:
            node = self._row_to_node(row)
            if self._is_test_path(node.file_path):
                related[node.id] = node

        # 2) The ``test_x`` ↔ ``x`` name heuristic: a test node whose bare name is
        #    ``test_<target_bare>``. This catches a test that exercises a symbol
        #    without a statically-visible edge to it.
        heuristic_name = f"{_TEST_NAME_PREFIX}{target_bare}"
        for row in self._connection.execute("SELECT * FROM nodes").fetchall():
            node = self._row_to_node(row)
            if not self._is_test_path(node.file_path):
                continue
            if self._bare_name(node.qualified_name) == heuristic_name:
                related[node.id] = node

        return list(related.values())

    @staticmethod
    def _is_test_path(file_path: str) -> bool:
        """Report whether ``file_path`` is a test file (glob or ``tests/`` dir)."""
        path = PurePosixPath(file_path)
        if _TESTS_DIR_NAME in path.parts:
            return True
        return any(fnmatch(path.name, glob) for glob in TEST_PATH_GLOBS)
