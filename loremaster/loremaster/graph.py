"""Typed code-graph — a KùzuDB side-structure with astroid-RESOLVED edges.

This is the capability layer: a typed code-graph built as a KùzuDB SIDE-structure
(there is NO new vector index — the graph lives alongside the manifest, not inside
Qdrant). It is GENERIC over any Python AST chunks the lorescribe
:class:`~lorescribe.python_ast.PythonAstChunker` emits — there is ZERO
Odoo-specific handling. A watcher / reconcile pass keeps it fresh by rebuilding
one file's slice transactionally (delete + rebuild), exactly the way the indexer
refreshes a file's vector points.

**Why Kùzu, and why edges-as-records.** The store is a single Kùzu database file
(``<slug>.graph.kuzu``). Kùzu's native RELs require BOTH endpoints to exist at
create-time, which breaks two invariants the code-graph must hold:

* **Order-independence.** A caller may be indexed before its callee (one file's
  rebuild cannot wait for another's). A REL ``caller -> callee`` cannot be created
  until ``callee`` exists.
* **Collision-correctness.** The SAME fully-qualified name legitimately repeats
  across files (two modules each defining ``Config``), so a node's identity is its
  surrogate ``id``, not its qname — a REL keyed on qname would conflate them.

So references are stored as RECORDS in a second node table :data:`_REF_TABLE`
carrying a STRING ``dst`` (the resolved FQN when the reference resolved in-project,
else the bare written name). A reference "lands" on a target node when a ``Ref``
record's ``dst`` equals that node's ``qualified_name`` (resolved edges) OR its bare
last segment (the conservative unresolved fallback) — exactly the proven SQLite
name-resolution seam, now with resolution PRECISION on top.

Schema (two node tables):

* :data:`_NODE_TABLE` ``CodeNode(id, kind, qualified_name, file_path, chunk_id,
  tier)`` — one row per graph node. ``id`` is a surrogate ``SERIAL`` primary key;
  the natural key is ``(tier, file_path, kind, qualified_name)``. ``kind`` is one
  of :data:`KIND_MODULE` / :data:`KIND_CLASS` / :data:`KIND_METHOD` /
  :data:`KIND_FUNCTION`. ``chunk_id`` is the originating chunk's ``identity`` (the
  synthesised module node has none, stored as an empty string).
* :data:`_REF_TABLE` ``Ref(id, src_qname, dst, kind, resolved, tier, file_path)``
  — one directed reference per row. ``kind`` is one of :data:`EDGE_DEFINES` /
  :data:`EDGE_INHERITS` / :data:`EDGE_IMPORTS` / :data:`EDGE_CALLS`. ``resolved``
  is ``True`` when ``dst`` is an astroid-inferred in-project FQN, ``False`` for the
  bare-name fallback. ``(tier, file_path)`` is the owning file so a per-file
  rebuild purges exactly its own records.

**What each edge kind is derived from (RESOLVED):**

* ``defines`` — FULLY derived from the chunk set's structure (no astroid needed).
  The module node ``defines`` every top-level class and top-level function; each
  class node ``defines`` its own methods. ``dst`` is the fully-qualified node name;
  ``resolved`` is ``True`` (structural defines are always exact).
* ``inherits`` / ``imports`` / ``calls`` — derived from astroid INFERENCE via
  :func:`lorescribe.astroid_parse.resolve_module`. The mapping rule per resolved
  reference:

  - ``(resolved and in_project)`` → KEEP, ``dst`` = the inferred FQN,
    ``resolved=True``. (An in-project base is now its FQN ``demo.service.Base``,
    NOT the bare ``Base`` the old stdlib-``ast`` engine stored — the deliberate
    contract change.)
  - ``(not resolved)`` → KEEP, ``dst`` = the bare written name, ``resolved=False``
    (the conservative fallback so a reference astroid could not infer is never
    silently dropped).
  - ``(resolved and not in_project)`` → DROP (builtins / stdlib / third-party
    noise — ``json``, ``pathlib.Path``, ``pydantic.BaseModel``).

  Resolution needs the file ON DISK under the project roots; when the graph is
  constructed without roots (the in-memory test seam) only structural ``defines``
  edges are emitted, so the object still works without roots — production passes
  them.

Query methods:

* :meth:`CodeGraph.what_imports` — module nodes with an ``imports`` reference whose
  ``dst`` matches the target (by FQN or bare name).
* :meth:`CodeGraph.blast_radius` — the BOUNDED reverse-reference transitive closure
  across ALL reference kinds, capped at ``depth`` hops and ``max_results`` nodes.
* :meth:`CodeGraph.tests_for` — test-path nodes related to a symbol/file via a
  reference into it, plus the ``test_x`` ↔ ``x`` name heuristic.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

import kuzu
from lorescribe.astroid_parse import (
    ParseError,
    ResolvedBase,
    ResolvedCall,
    ResolvedImport,
    ResolvedModule,
    clear_resolution_cache,
    resolve_module,
)
from lorescribe.python_ast import (
    CHUNK_TYPE_CLASS,
    CHUNK_TYPE_FUNCTION,
    CHUNK_TYPE_METHOD,
)
from pydantic import BaseModel, ConfigDict

from loremaster.index.kuzu_resilient import open_resilient_kuzu

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

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
# importable dotted path.
_PACKAGE_MARKER = "__init__.py"

# The stem an ``__init__.py`` collapses to its package under.
_INIT_STEM = "__init__"

# Globs (matched against the POSIX file path) that mark a node as a TEST node.
TEST_PATH_GLOBS: tuple[str, ...] = ("test_*.py", "*_test.py")
_TESTS_DIR_NAME = "tests"

# The conventional prefix a test function carries for the symbol it exercises:
# ``test_boot`` tests ``boot`` (the ``test_x`` ↔ ``x`` heuristic).
_TEST_NAME_PREFIX = "test_"

# The reference kinds that count as a TRUE reference TO a node (the structural
# ``defines`` parent edge is DELIBERATELY excluded — counting it would make nothing
# ever dead, since every node is ``defines``-pointed-at by its structural parent).
_REFERENCE_KINDS: tuple[str, ...] = (EDGE_IMPORTS, EDGE_CALLS, EDGE_INHERITS)

# Dead-code sweep bounds. The default caps a single sweep at a sane, reviewable
# size; the hard ceiling guards against a pathological request (mirrors the
# ``blast_radius`` max-results discipline).
DEFAULT_DEAD_CODE_MAX_RESULTS = 100
MAX_DEAD_CODE_MAX_RESULTS = 1000

# The two reasons a node is reported dead, by its test-reference profile.
REASON_NO_REFERENCES = "no_references"
REASON_ONLY_REFERENCED_BY_TESTS = "only_referenced_by_tests"

# A ``method`` whose bare name matches this glob is a dunder (``__init__`` /
# ``__repr__`` / …): runtime/protocol-invoked, never an explicit call edge, so it
# always looks orphaned. Excluded from the dead-code sweep unless asked for.
_DUNDER_GLOB = "__*__"

# The bare module name of a ``__main__`` entry module (a CLI entrypoint, run as a
# script, never imported by dotted name → always looks orphaned).
_MAIN_MODULE_NAME = "__main__"

# Kùzu table names. CodeNode holds graph nodes; Ref holds reference records (the
# edges-as-records design — see the module docstring for why Kùzu RELs are unfit).
_NODE_TABLE = "CodeNode"
_REF_TABLE = "Ref"

# A SERIAL primary key cannot be NULL and a Kùzu STRING column has no NULL literal
# in our INSERT path, so the synthesised module node (which has no originating
# chunk) stores the empty string for ``chunk_id`` and is decoded back to ``None``.
_NO_CHUNK_ID = ""

# Schema DDL, executed idempotently on every open (CREATE ... IF NOT EXISTS) so a
# fresh and a reopened db both arrive at the same schema. References are stored as
# node-table RECORDS (not RELs) so an edge can be created before its endpoints
# exist (order-independence) and a repeated FQN across files stays distinct
# (collision-correctness) — see the module docstring.
_SCHEMA_STATEMENTS: tuple[str, ...] = (
    f"""
    CREATE NODE TABLE IF NOT EXISTS {_NODE_TABLE}(
        id SERIAL,
        kind STRING,
        qualified_name STRING,
        file_path STRING,
        chunk_id STRING,
        tier STRING,
        PRIMARY KEY(id)
    )
    """,
    f"""
    CREATE NODE TABLE IF NOT EXISTS {_REF_TABLE}(
        id SERIAL,
        src_qname STRING,
        dst STRING,
        kind STRING,
        resolved BOOL,
        tier STRING,
        file_path STRING,
        PRIMARY KEY(id)
    )
    """,
)


class GraphNode(BaseModel):
    """A single decoded ``CodeNode`` row.

    Attributes:
        id: The surrogate ``SERIAL`` row id.
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


class ReferenceSummary(BaseModel):
    """The reference profile of one symbol, split by reference ORIGIN.

    A reference from a TEST file does NOT count as a true reference, so the counts
    are split by whether the referencing file (``Ref.file_path``) is a test path. A
    symbol whose only consumers are its tests is DEAD (``production_references ==
    0``).

    Attributes:
        qualified_name: The symbol the references point at.
        production_references: Distinct references TO the symbol from NON-test
            files (the count that decides liveness).
        test_references: Distinct references TO the symbol from TEST files.
        referencing: The distinct nodes that reference the symbol (every node whose
            ``qualified_name`` is a referencing ``Ref.src_qname``), deduped.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    qualified_name: str
    production_references: int
    test_references: int
    referencing: list[GraphNode]


class DeadCodeNode(BaseModel):
    """A node reported by the dead-code sweep: zero PRODUCTION references.

    Carries the full :class:`GraphNode` shape plus the test-reference count and the
    labelled reason it is considered dead.

    Attributes:
        id: The surrogate ``SERIAL`` row id (as :class:`GraphNode`).
        kind: One of :data:`KIND_MODULE` / :data:`KIND_CLASS` /
            :data:`KIND_METHOD` / :data:`KIND_FUNCTION`.
        qualified_name: The dotted name of the dead symbol.
        file_path: The tier-relative POSIX path the node was derived from.
        chunk_id: The originating chunk's ``identity`` (``None`` for the module).
        tier: The source tier the node belongs to.
        test_references: The number of references TO the node from TEST files.
        reason: :data:`REASON_ONLY_REFERENCED_BY_TESTS` when
            ``test_references > 0``, else :data:`REASON_NO_REFERENCES`.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: int
    kind: str
    qualified_name: str
    file_path: str
    chunk_id: str | None
    tier: str
    test_references: int
    reason: str


class _NodeSpec(BaseModel):
    """An intermediate node-to-insert, before it acquires a row id."""

    model_config = ConfigDict(extra="forbid")

    kind: str
    qualified_name: str
    chunk_id: str | None


class _EdgeSpec(BaseModel):
    """An intermediate reference-record-to-insert.

    Attributes:
        src: The referring node's qualified name.
        dst: The referenced target — the resolved in-project FQN when
            ``resolved``, else the bare written name (the conservative fallback).
        kind: One of the four ``EDGE_*`` kinds.
        resolved: ``True`` when ``dst`` is an astroid-inferred in-project FQN.
    """

    model_config = ConfigDict(extra="forbid")

    src: str
    dst: str
    kind: str
    resolved: bool


class CodeGraph:
    """A typed code-graph over Python AST chunks, backed by KùzuDB.

    The database path is a single Kùzu file (a real path). The schema is created
    on construction. Every mutation is tier- and file-scoped so a per-file rebuild
    or delete never touches a sibling file or tier (the C1 discipline the manifest
    already follows).

    References are astroid-RESOLVED: in-project ``imports`` / ``inherits`` /
    ``calls`` carry the inferred fully-qualified ``dst`` (and ``resolved=True``),
    external resolved references are dropped, and an un-inferable reference falls
    back to its bare written name (``resolved=False``). Resolution requires the
    file on disk under the project roots, so the roots are supplied at
    construction; without them the graph emits only structural ``defines`` edges.

    Args:
        db_path: The Kùzu database path (a single real file).
        tier_roots: Optional mapping ``tier -> on-disk root`` the tier's
            tier-relative file paths are relative to. Used to locate a file on
            disk for astroid resolution. ``None`` ⇒ resolution is skipped.
        project_roots: Optional list of project root directories astroid adds to
            its search path and uses to classify a reference in-project vs
            external. ``None`` ⇒ resolution is skipped.
    """

    def __init__(
        self,
        db_path: str,
        *,
        tier_roots: Mapping[str, str | Path] | None = None,
        project_roots: Sequence[str | Path] | None = None,
    ) -> None:
        """Open (or create) the graph database resiliently and ensure the schema.

        The open is RESILIENT (FP-01 + FP-08 analogues): an absent parent dir is
        created owner-only and a corrupt on-disk image is deleted and recreated,
        both via :func:`~loremaster.index.kuzu_resilient.open_resilient_kuzu`. A
        valid existing graph opens UNCHANGED — its records survive.
        """
        self._tier_roots: dict[str, str] = (
            {tier: str(root) for tier, root in tier_roots.items()}
            if tier_roots is not None
            else {}
        )
        self._project_roots: list[str] = (
            [str(root) for root in project_roots] if project_roots is not None else []
        )
        # Resolution is only attempted when BOTH a tier's root and the project
        # roots are known — otherwise astroid cannot place the file on disk nor
        # classify references, so we degrade to structural ``defines`` only.
        self._resolution_enabled = bool(self._project_roots)

        self._database = open_resilient_kuzu(db_path)
        self._connection = kuzu.Connection(self._database)
        for statement in _SCHEMA_STATEMENTS:
            self._execute(statement)

    @property
    def connection(self) -> kuzu.Connection:
        """The underlying Kùzu connection (for diagnostics, tests, divergence-wipe)."""
        return self._connection

    def _execute(
        self, cypher: str, params: dict[str, object] | None = None
    ) -> kuzu.QueryResult:
        """Execute a SINGLE-statement Cypher query, narrowing the result type.

        ``kuzu.Connection.execute`` is typed ``QueryResult | list[QueryResult]``
        because a multi-statement string yields one result per statement; every
        query this class issues is a single statement, so the list form never
        occurs and is asserted away to keep the call sites strongly typed.
        """
        result = self._connection.execute(cypher, parameters=params or {})
        assert isinstance(result, kuzu.QueryResult)  # noqa: S101 - single-statement invariant
        return result

    def close(self) -> None:
        """Close the underlying database connection and database."""
        self._connection.close()
        self._database.close()

    def indexed_file_count(self) -> int:
        """Return the number of distinct files the graph currently holds nodes for.

        The graph's view of "how many files are live", across every tier — the
        store-divergence reconcile compares it against the manifest to detect a
        wiped/empty graph the manifest still calls indexed (FP-04). A wiped graph
        (no node rows) yields ``0`` — the FP-04 trigger.

        Returns:
            The count of distinct ``(tier, file_path)`` files with graph nodes.
        """
        result = self._execute(
            f"MATCH (n:{_NODE_TABLE}) RETURN count(DISTINCT [n.tier, n.file_path])"
        )
        return self._single_int(result)

    # -- naming helpers ----------------------------------------------------

    @staticmethod
    def module_qualified_name(file_path: str) -> str:
        """Derive the dotted module name from a tier-relative POSIX path.

        ``demo/service.py`` → ``demo.service``; an ``__init__.py`` collapses to its
        package (``demo/__init__.py`` → ``demo``).

        Args:
            file_path: The tier-relative POSIX file path.

        Returns:
            The dotted module qualified name.
        """
        path = PurePosixPath(file_path)
        parts = list(path.parts)
        stem = path.stem
        if stem == _INIT_STEM:
            parts = parts[:-1]
        else:
            parts[-1] = stem
        return _QUALIFIER_SEPARATOR.join(parts)

    @staticmethod
    def importable_module_name(base: Path, file_path: str) -> str:
        """Derive the TRUE importable dotted module name from an on-disk layout.

        Strips leading path segments up to the top of the package: the SHALLOWEST
        directory in ``file_path``'s chain that contains an ``__init__.py`` (probed
        under ``base`` on disk) is the package top, and everything to its left is
        dropped. ``loremaster/loremaster/config.py`` (under a repo root whose
        ``loremaster/`` member dir has no ``__init__.py``) resolves to the
        importable ``loremaster.config`` rather than the doubled
        ``loremaster.loremaster.config``.

        Fallback: if NO directory in the chain contains an ``__init__.py`` (a
        namespace / ``src`` layout, or a path with no file on disk), nothing is
        stripped and the full tier-relative path is joined, exactly as
        :meth:`module_qualified_name` does.

        Args:
            base: The tier's on-disk root that ``file_path`` is relative to.
            file_path: The tier-relative POSIX file path.

        Returns:
            The importable dotted module qualified name.
        """
        path = PurePosixPath(file_path)
        parts = list(path.parts)
        directories = parts[:-1]

        package_top_index: int | None = None
        for index in range(len(directories)):
            candidate_dir = base / PurePosixPath(*parts[: index + 1])
            if (candidate_dir / _PACKAGE_MARKER).is_file():
                package_top_index = index
                break

        start = package_top_index if package_top_index is not None else 0
        kept = parts[start:]

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
        """Derive and store the nodes/references for one file.

        A per-file rebuild: the file's prior nodes and references are deleted and
        the freshly-derived set inserted, so a removed symbol leaves no orphan
        reference behind. The delete and the insert are both tier- and
        file-scoped, so another tier's copy of the same path (C1) and sibling
        files are untouched.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path (the tier-scoping key).
            chunks: The file's lorescribe AST chunks (any python_ast chunk set).
            module_name: The module prefix every node/reference ``src`` is
                qualified under (the TRUE importable dotted path). ``None`` ⇒ the
                pure path-join :meth:`module_qualified_name`.
        """
        module = module_name if module_name is not None else self.module_qualified_name(file_path)
        nodes = self._derive_nodes(module, chunks)
        edges = self._derive_edges(module, chunks, tier=tier, file_path=file_path)

        self._delete_file_rows(tier, file_path)
        for node in nodes:
            self._execute(
                f"""
                CREATE (n:{_NODE_TABLE} {{
                    kind: $kind, qualified_name: $qualified_name,
                    file_path: $file_path, chunk_id: $chunk_id, tier: $tier
                }})
                """,
                {
                    "kind": node.kind,
                    "qualified_name": node.qualified_name,
                    "file_path": file_path,
                    "chunk_id": node.chunk_id if node.chunk_id is not None else _NO_CHUNK_ID,
                    "tier": tier,
                },
            )
        for edge in edges:
            self._execute(
                f"""
                CREATE (r:{_REF_TABLE} {{
                    src_qname: $src, dst: $dst, kind: $kind,
                    resolved: $resolved, tier: $tier, file_path: $file_path
                }})
                """,
                {
                    "src": edge.src,
                    "dst": edge.dst,
                    "kind": edge.kind,
                    "resolved": edge.resolved,
                    "tier": tier,
                    "file_path": file_path,
                },
            )

    def delete_file_graph(self, tier: str, file_path: str) -> None:
        """Remove every node and reference owned by ``(tier, file_path)``.

        Tier-scoped: the same path's rows under other tiers survive (C1). Used by
        the watcher when a file is removed, and internally by the rebuild.

        Args:
            tier: The source tier the file belongs to.
            file_path: The tier-relative POSIX file path to purge.
        """
        self._delete_file_rows(tier, file_path)

    def _delete_file_rows(self, tier: str, file_path: str) -> None:
        """Delete a file's nodes and reference records (tier+file scoped)."""
        params: dict[str, object] = {"tier": tier, "file_path": file_path}
        self._execute(
            f"MATCH (n:{_NODE_TABLE}) WHERE n.tier = $tier AND n.file_path = $file_path "
            "DETACH DELETE n",
            params,
        )
        self._execute(
            f"MATCH (r:{_REF_TABLE}) WHERE r.tier = $tier AND r.file_path = $file_path "
            "DETACH DELETE r",
            params,
        )

    # -- derivation: nodes (structural, no astroid) ------------------------

    def _derive_nodes(self, module: str, chunks: Sequence[Chunk]) -> list[_NodeSpec]:
        """Derive the node specs for a file from its AST chunks (structural).

        The module node is synthesised (no chunk of its own); every other node maps
        to one chunk. Deduped on ``(kind, qualified_name)`` — a method reachable via
        a conditional ``def`` can be chunked twice under the same qualified name.
        """
        nodes: list[_NodeSpec] = [
            _NodeSpec(kind=KIND_MODULE, qualified_name=module, chunk_id=None)
        ]
        for chunk in chunks:
            if chunk.chunk_type == CHUNK_TYPE_CLASS:
                nodes.append(self._class_node(module, chunk))
            elif chunk.chunk_type == CHUNK_TYPE_METHOD:
                nodes.append(self._method_node(module, chunk))
            elif chunk.chunk_type == CHUNK_TYPE_FUNCTION:
                nodes.append(self._function_node(module, chunk))
        return self._dedupe_nodes(nodes)

    @staticmethod
    def _dedupe_nodes(nodes: list[_NodeSpec]) -> list[_NodeSpec]:
        """Drop duplicate node specs (same kind + qualified_name), keeping the first."""
        seen: set[tuple[str, str]] = set()
        unique: list[_NodeSpec] = []
        for node in nodes:
            key = (node.kind, node.qualified_name)
            if key in seen:
                continue
            seen.add(key)
            unique.append(node)
        return unique

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

    # -- derivation: edges -------------------------------------------------

    def _derive_edges(
        self, module: str, chunks: Sequence[Chunk], *, tier: str, file_path: str
    ) -> list[_EdgeSpec]:
        """Derive the reference records: structural ``defines`` + RESOLVED refs.

        ``defines`` is structural (module→class/func, class→method) and always
        emitted. ``imports`` / ``inherits`` / ``calls`` are obtained from astroid
        :func:`resolve_module` and mapped per the keep/drop rule; they are emitted
        only when the file can be located on disk under the project roots (the
        resolution seam). Without roots the graph still works — it just carries
        only the structural ``defines`` references.
        """
        edges: list[_EdgeSpec] = self._define_edges(module, chunks)
        resolved = self._resolve(module, tier=tier, file_path=file_path)
        if resolved is not None:
            edges.extend(self._reference_edges(module, resolved))
        return edges

    def _define_edges(self, module: str, chunks: Sequence[Chunk]) -> list[_EdgeSpec]:
        """The structural ``defines`` references derived from the chunk set."""
        edges: list[_EdgeSpec] = []
        for chunk in chunks:
            if chunk.chunk_type == CHUNK_TYPE_CLASS:
                class_name = str(chunk.metadata["class_name"])
                class_qualified = f"{module}{_QUALIFIER_SEPARATOR}{class_name}"
                edges.append(self._defines(module, class_qualified))
            elif chunk.chunk_type == CHUNK_TYPE_METHOD:
                class_name = str(chunk.metadata["class_name"])
                method_name = str(chunk.metadata["method_name"])
                class_qualified = f"{module}{_QUALIFIER_SEPARATOR}{class_name}"
                method_qualified = f"{class_qualified}{_QUALIFIER_SEPARATOR}{method_name}"
                edges.append(self._defines(class_qualified, method_qualified))
            elif chunk.chunk_type == CHUNK_TYPE_FUNCTION:
                function_name = str(chunk.metadata["method_name"])
                function_qualified = f"{module}{_QUALIFIER_SEPARATOR}{function_name}"
                edges.append(self._defines(module, function_qualified))
        return edges

    @staticmethod
    def _defines(src: str, dst: str) -> _EdgeSpec:
        """A structural ``defines`` reference (always exact, ``resolved=True``)."""
        return _EdgeSpec(src=src, dst=dst, kind=EDGE_DEFINES, resolved=True)

    def _resolve(
        self, module: str, *, tier: str, file_path: str
    ) -> ResolvedModule | None:
        """Resolve a file's references via astroid, or ``None`` to skip resolution.

        Returns ``None`` (structural-only graph) when resolution is disabled (no
        project roots), the tier's on-disk base is unknown, the file is not on
        disk, or astroid cannot parse it — in every such case the graph degrades to
        structural ``defines`` only rather than fabricating or crashing.
        """
        if not self._resolution_enabled:
            return None
        base = self._tier_roots.get(tier)
        if base is None:
            return None
        absolute_path = Path(base) / PurePosixPath(file_path)
        if not absolute_path.is_file():
            return None
        # Clear astroid's process-global manager cache BEFORE resolving so a dirty
        # prior state cannot corrupt this resolution. The chunker (PythonAstChunker
        # → parse_module → astroid.parse) populates the manager WITHOUT putting the
        # project roots on the import search path, so a chunk-then-resolve sequence
        # (exactly the indexer's order) would otherwise leave a half-built module in
        # the cache and make a cross-module in-project reference infer to its bare
        # name (resolved=False) instead of its FQN. A pre-clear gives resolution a
        # clean manager + a fresh search-path mutation every time.
        clear_resolution_cache()
        try:
            return resolve_module(
                str(absolute_path),
                project_roots=self._project_roots,
                qualified_name=module,
            )
        except ParseError:
            # An unparseable file yields no resolved references — the structural
            # ``defines`` edges already derived from the chunks still stand.
            return None
        finally:
            # Bound the cache AFTER resolving too, so one file's package cannot leak
            # into the next file's resolution (or into a later chunker parse).
            clear_resolution_cache()

    def _reference_edges(
        self, module: str, resolved: ResolvedModule
    ) -> list[_EdgeSpec]:
        """Map a :class:`ResolvedModule`'s references to kept reference records.

        The reference ``src`` (and the src-side class/function/method FQNs) are
        RE-BASED from astroid's own module name (:attr:`ResolvedModule.qualified_name`,
        which degrades to the file PATH when astroid cannot place the file in a
        package — e.g. a ``tests/`` dir with no ``__init__.py``) onto the caller's
        importable ``module`` qname, so they MATCH the node qualified names (which
        are built from ``module``). The ``dst`` of an in-project reference keeps
        astroid's inferred FQN unchanged — it is resolved against the TARGET's
        package, which production indexes with proper roots.

        The keep/drop rule is applied uniformly to imports, class bases, and call
        sites: keep ``(resolved and in_project)`` [dst = FQN] or ``(not resolved)``
        [dst = bare name]; drop ``(resolved and not in_project)``.
        """
        astroid_module = resolved.qualified_name
        edges: list[_EdgeSpec] = []

        for imported in resolved.imports:
            edge = self._reference_edge(module, imported, EDGE_IMPORTS)
            if edge is not None:
                edges.append(edge)

        for resolved_class in resolved.classes:
            class_src = self._rebase(resolved_class.qualified_name, astroid_module, module)
            for base in resolved_class.inherits:
                edge = self._reference_edge(class_src, base, EDGE_INHERITS)
                if edge is not None:
                    edges.append(edge)
            for method in resolved_class.methods:
                method_src = self._rebase(method.qualified_name, astroid_module, module)
                edges.extend(self._call_edges(method_src, method.calls))

        for function in resolved.functions:
            function_src = self._rebase(function.qualified_name, astroid_module, module)
            edges.extend(self._call_edges(function_src, function.calls))

        return edges

    @staticmethod
    def _rebase(fqn: str, astroid_module: str, module: str) -> str:
        """Re-base ``fqn`` from astroid's module prefix onto the importable ``module``.

        ``resolve_module`` builds src-side FQNs off astroid's module name, which is
        the file PATH when astroid cannot place the file in a package. Replacing
        that prefix with the caller's importable ``module`` qname makes the src
        names match the structurally-built node qualified names. An ``fqn`` that
        does not carry the astroid prefix (already importable) is returned as-is.
        """
        if fqn == astroid_module:
            return module
        prefix = f"{astroid_module}{_QUALIFIER_SEPARATOR}"
        if fqn.startswith(prefix):
            return f"{module}{_QUALIFIER_SEPARATOR}{fqn[len(prefix):]}"
        return fqn

    def _call_edges(self, caller: str, calls: Sequence[ResolvedCall]) -> list[_EdgeSpec]:
        """The kept ``calls`` references for one caller, deduped preserving order."""
        edges: list[_EdgeSpec] = []
        seen: set[tuple[str, bool]] = set()
        for call in calls:
            edge = self._reference_edge(caller, call, EDGE_CALLS)
            if edge is None:
                continue
            key = (edge.dst, edge.resolved)
            if key in seen:
                continue
            seen.add(key)
            edges.append(edge)
        return edges

    @staticmethod
    def _reference_edge(
        src: str,
        reference: ResolvedImport | ResolvedBase | ResolvedCall,
        kind: str,
    ) -> _EdgeSpec | None:
        """Apply the keep/drop rule to one resolved reference.

        Returns the reference record to insert, or ``None`` when the reference is
        ``(resolved and not in_project)`` — the dropped external noise.
        """
        if reference.resolved and not reference.in_project:
            return None
        # KEEP: an in-project resolved ref carries its inferred FQN; an unresolved
        # ref carries its bare written ``target`` (the conservative fallback).
        return _EdgeSpec(
            src=src, dst=reference.target, kind=kind, resolved=reference.resolved
        )

    # -- row decoding ------------------------------------------------------

    @staticmethod
    def _row_to_node(row: Mapping[str, object]) -> GraphNode:
        """Decode a Kùzu ``CodeNode`` row dict into a :class:`GraphNode`.

        The synthesised module node's empty-string ``chunk_id`` is decoded back to
        ``None`` (its on-the-wire representation, see :data:`_NO_CHUNK_ID`).
        """
        chunk_id = row["chunk_id"]
        return GraphNode(
            id=int(str(row["id"])),
            kind=str(row["kind"]),
            qualified_name=str(row["qualified_name"]),
            file_path=str(row["file_path"]),
            chunk_id=None if chunk_id == _NO_CHUNK_ID else str(chunk_id),
            tier=str(row["tier"]),
        )

    @staticmethod
    def _row_values(result: kuzu.QueryResult) -> list[object]:
        """The next row as a positional ``list``.

        ``kuzu.QueryResult.get_next`` is typed ``list[Any] | dict[str, Any]``; a
        positional ``RETURN`` always yields the list form, so the dict branch (only
        produced by the unused dict cursor) is coerced to its values to keep the
        return total and strongly typed.
        """
        row = result.get_next()
        return list(row.values()) if isinstance(row, dict) else list(row)

    @staticmethod
    def _single_int(result: kuzu.QueryResult) -> int:
        """Return the first column of the first row as an ``int``, or ``0`` if empty."""
        if result.has_next():
            return int(str(CodeGraph._row_values(result)[0]))
        return 0

    def _nodes_matching(self, where: str, params: dict[str, object]) -> list[GraphNode]:
        """Decode every ``CodeNode`` row satisfying a WHERE clause into GraphNodes."""
        result = self._execute(
            f"""
            MATCH (n:{_NODE_TABLE}) WHERE {where}
            RETURN n.id AS id, n.kind AS kind, n.qualified_name AS qualified_name,
                   n.file_path AS file_path, n.chunk_id AS chunk_id, n.tier AS tier
            """,
            params,
        )
        return self._decode_node_rows(result)

    @staticmethod
    def _decode_node_rows(result: kuzu.QueryResult) -> list[GraphNode]:
        """Decode an id/kind/qualified_name/file_path/chunk_id/tier result set."""
        columns = result.get_column_names()
        nodes: list[GraphNode] = []
        while result.has_next():
            row: dict[str, object] = dict(
                zip(columns, CodeGraph._row_values(result), strict=True)
            )
            nodes.append(CodeGraph._row_to_node(row))
        return nodes

    def _nodes_by_qualified_name(self, qualified_name: str) -> list[GraphNode]:
        """Every node (across tiers/files) whose qualified name matches exactly."""
        return self._nodes_matching(
            "n.qualified_name = $qname", {"qname": qualified_name}
        )

    # -- queries -----------------------------------------------------------

    def what_imports(self, target: str) -> list[GraphNode]:
        """Return the module nodes that import ``target``.

        The reverse of the ``imports`` reference: every ``module`` node that is the
        ``src`` of an ``imports`` reference whose ``dst`` matches ``target`` across
        the name-resolution seam, which is BIDIRECTIONAL so the resolution change
        does not break either query style:

        * ``dst == target`` — an exact match (a module import ``import pkg.a``
          resolves to the module FQN ``pkg.a``, matched by a ``pkg.a`` query).
        * ``dst ENDS WITH ".<bare(target)>"`` — a bare query reaches a RESOLVED
          symbol FQN ``dst`` (a ``LoadError`` query reaches
          ``demo.errors.LoadError``).
        * ``dst == bare(target)`` — an FQN query reaches a bare unresolved ``dst``
          fallback.

        Args:
            target: The imported module / dotted name to find importers of.

        Returns:
            The importing module nodes (empty if nobody imports the target).
        """
        bare = self._bare_name(target)
        result = self._execute(
            f"""
            MATCH (n:{_NODE_TABLE}), (r:{_REF_TABLE})
            WHERE n.kind = $module_kind AND r.kind = $imports_kind
              AND r.src_qname = n.qualified_name AND r.tier = n.tier
              AND (r.dst = $target OR r.dst ENDS WITH $dotted_bare OR r.dst = $bare)
            RETURN DISTINCT n.id AS id, n.kind AS kind,
                   n.qualified_name AS qualified_name, n.file_path AS file_path,
                   n.chunk_id AS chunk_id, n.tier AS tier
            """,
            {
                "module_kind": KIND_MODULE,
                "imports_kind": EDGE_IMPORTS,
                "target": target,
                "dotted_bare": f"{_QUALIFIER_SEPARATOR}{bare}",
                "bare": bare,
            },
        )
        return self._decode_node_rows(result)

    def blast_radius(self, target: str, depth: int, max_results: int) -> list[GraphNode]:
        """Return the BOUNDED reverse-reference transitive closure from ``target``.

        Everything that (transitively) depends on ``target``: walk references
        backwards (the dependents of a node are the ``src`` of references whose
        ``dst`` is that node) across ALL reference kinds, breadth-first. Bounded by
        ``depth`` reverse hops and a hard ``max_results`` ceiling so a pathological
        fan-out cannot blow up.

        Frontier matching spans the resolution seam: a reference ``dst`` may be a
        bare name (unresolved fallback) or a qualified name (resolved / defines),
        so the next reverse hop follows any reference whose ``dst`` equals EITHER
        the frontier node's qualified name OR its bare last segment.

        Args:
            target: The qualified name to compute the blast radius of.
            depth: The maximum number of reverse hops (>= 0).
            max_results: The maximum number of nodes to return (the hard cap).

        Returns:
            Up to ``max_results`` dependent nodes, never the target itself.
        """
        if depth < 0 or max_results <= 0:
            return []

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

        A name in the frontier is matched against a reference ``dst`` by its full
        value AND by its bare last segment (the resolution seam), then the
        reference's ``src`` is resolved to the node(s) bearing that qualified name.
        """
        match_values: set[str] = set()
        for name in frontier:
            match_values.add(name)
            match_values.add(self._bare_name(name))

        result = self._execute(
            f"MATCH (r:{_REF_TABLE}) WHERE r.dst IN $match_values "
            "RETURN DISTINCT r.src_qname",
            {"match_values": list(match_values)},
        )
        source_names: list[str] = []
        while result.has_next():
            source_names.append(str(self._row_values(result)[0]))

        neighbours: list[GraphNode] = []
        for source_name in source_names:
            neighbours.extend(self._nodes_by_qualified_name(source_name))
        return neighbours

    def tests_for(self, symbol_or_file: str) -> list[GraphNode]:
        """Return the test nodes related to ``symbol_or_file``.

        A node is a TEST node when its ``file_path`` matches a test glob
        (:data:`TEST_PATH_GLOBS` or a ``tests/`` directory segment). A test node is
        related to the target when EITHER:

        * it sits in a test file with a reference (any kind) whose ``dst`` matches
          the target by qualified name or bare name; OR
        * the ``test_x`` ↔ ``x`` name heuristic links it: a ``test_boot`` node is a
          test for any symbol whose bare name is ``boot``.

        Args:
            symbol_or_file: A qualified symbol name or a module name.

        Returns:
            The related test nodes (de-duplicated by row id).
        """
        target_bare = self._bare_name(symbol_or_file)
        related: dict[int, GraphNode] = {}

        # 1) Test nodes whose file has a reference to the target (by FQN or bare).
        edge_result = self._execute(
            f"""
            MATCH (n:{_NODE_TABLE}), (r:{_REF_TABLE})
            WHERE r.tier = n.tier AND r.file_path = n.file_path
              AND r.dst IN $match_values
            RETURN DISTINCT n.id AS id, n.kind AS kind,
                   n.qualified_name AS qualified_name, n.file_path AS file_path,
                   n.chunk_id AS chunk_id, n.tier AS tier
            """,
            {"match_values": [symbol_or_file, target_bare]},
        )
        for node in self._decode_node_rows(edge_result):
            if self._is_test_path(node.file_path):
                related[node.id] = node

        # 2) The ``test_x`` ↔ ``x`` name heuristic.
        heuristic_name = f"{_TEST_NAME_PREFIX}{target_bare}"
        all_result = self._execute(
            f"""
            MATCH (n:{_NODE_TABLE})
            RETURN n.id AS id, n.kind AS kind, n.qualified_name AS qualified_name,
                   n.file_path AS file_path, n.chunk_id AS chunk_id, n.tier AS tier
            """
        )
        for node in self._decode_node_rows(all_result):
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

    # -- reference counting / dead-code detection --------------------------

    def references(self, name: str) -> ReferenceSummary:
        """Return the reference profile of the symbol ``name``, split by origin.

        A reference TO ``name`` is a ``Ref`` row whose ``kind`` is a true reference
        kind (:data:`_REFERENCE_KINDS` — ``imports`` / ``calls`` / ``inherits``, NOT
        the structural ``defines`` parent edge), whose ``dst`` matches ``name`` by
        exact qualified name OR by bare last segment (the conservative
        unresolved/bare seam, mirroring :meth:`what_imports`), and whose
        ``src_qname`` is not ``name`` itself (self-reference — e.g. recursion — is
        not external use).

        The matching references are split by ORIGIN: a reference from a TEST file
        (``Ref.file_path`` is a test path) counts toward ``test_references``, every
        other matching reference toward ``production_references``. A symbol with zero
        references is a valid, non-error result (all-zero summary).

        Args:
            name: The qualified name of the symbol to profile.

        Returns:
            The :class:`ReferenceSummary` for ``name`` (counts split by origin plus
            the distinct referencing nodes).
        """
        production_sources, test_sources = self._reference_sources(name)
        referencing: list[GraphNode] = []
        seen_node_ids: set[int] = set()
        for source_name in production_sources | test_sources:
            for node in self._nodes_by_qualified_name(source_name):
                if node.id not in seen_node_ids:
                    seen_node_ids.add(node.id)
                    referencing.append(node)
        return ReferenceSummary(
            qualified_name=name,
            production_references=len(production_sources),
            test_references=len(test_sources),
            referencing=referencing,
        )

    def _reference_sources(self, name: str) -> tuple[set[str], set[str]]:
        """The distinct ``src_qname`` sets that reference ``name``, split by origin.

        Returns ``(production_sources, test_sources)`` — the distinct referring
        qualified names whose reference rows originate in a production file vs a test
        file. Applies the true-reference-kind filter, the FQN-or-bare ``dst`` match,
        and the self-reference exclusion. Splitting on the DISTINCT source (not the
        raw row) means several call sites from the same caller count once.
        """
        bare = self._bare_name(name)
        result = self._execute(
            f"""
            MATCH (r:{_REF_TABLE})
            WHERE r.kind IN $reference_kinds
              AND (r.dst = $name OR r.dst = $bare)
              AND r.src_qname <> $name
            RETURN DISTINCT r.src_qname AS src_qname, r.file_path AS file_path
            """,
            {
                "reference_kinds": list(_REFERENCE_KINDS),
                "name": name,
                "bare": bare,
            },
        )
        production_sources: set[str] = set()
        test_sources: set[str] = set()
        columns = result.get_column_names()
        while result.has_next():
            row = dict(zip(columns, self._row_values(result), strict=True))
            source_name = str(row["src_qname"])
            if self._is_test_path(str(row["file_path"])):
                test_sources.add(source_name)
            else:
                production_sources.add(source_name)
        return production_sources, test_sources

    def dead_code(
        self,
        tiers: Sequence[str],
        *,
        include_tests: bool = False,
        include_dunders: bool = False,
        include_entrypoints: bool = False,
        max_results: int = DEFAULT_DEAD_CODE_MAX_RESULTS,
    ) -> list[DeadCodeNode]:
        """Return the dead/orphaned nodes in ``tiers`` — zero PRODUCTION references.

        A node is DEAD ⇔ it has zero production references (regardless of how many
        test references it has — a symbol whose only consumers are its tests is
        dead). Each kept node becomes a :class:`DeadCodeNode` whose ``reason`` is
        :data:`REASON_ONLY_REFERENCED_BY_TESTS` when it has test references, else
        :data:`REASON_NO_REFERENCES`.

        Candidate nodes are the ``CodeNode`` rows whose ``tier`` is in ``tiers``
        (the caller passes the project's LIVE tiers). The following are excluded by
        default, each re-includable via its flag, to suppress known non-dead false
        positives:

        * ``include_tests=False`` — exclude nodes whose OWN ``file_path`` is a test
          path (a test isn't dead because nothing calls it).
        * ``include_dunders=False`` — exclude ``method`` nodes whose bare name is a
          dunder (``__*__``): runtime/protocol-invoked, never an explicit call edge.
        * ``include_entrypoints=False`` — exclude ``module`` nodes that are package
          / entry modules (a ``__main__`` module or an ``__init__`` package module),
          which are not imported by dotted name and so always look orphaned.

        Args:
            tiers: The tiers whose nodes are swept (empty ⇒ empty result).
            include_tests: Keep test-path nodes when ``True``.
            include_dunders: Keep dunder methods when ``True``.
            include_entrypoints: Keep package / entry modules when ``True``.
            max_results: The hard cap on the number of dead nodes returned (clamped
                to :data:`MAX_DEAD_CODE_MAX_RESULTS`).

        Returns:
            Up to ``max_results`` :class:`DeadCodeNode` entries.
        """
        if not tiers or max_results <= 0:
            return []
        cap = min(max_results, MAX_DEAD_CODE_MAX_RESULTS)

        # One bulk pass over the reference rows builds a name → (prod, test) source
        # index, so the per-candidate liveness check is an in-memory lookup rather
        # than a query per node (avoids the N+1 the per-symbol ``references`` path
        # would incur over a whole-tier sweep).
        reference_index = self._reference_source_index()

        dead: list[DeadCodeNode] = []
        for node in self._candidate_nodes(tiers):
            if self._is_excluded_candidate(
                node,
                include_tests=include_tests,
                include_dunders=include_dunders,
                include_entrypoints=include_entrypoints,
            ):
                continue
            production_sources, test_sources = self._sources_for(node.qualified_name, reference_index)
            if production_sources:
                continue  # has a production reference → alive
            reason = (
                REASON_ONLY_REFERENCED_BY_TESTS if test_sources else REASON_NO_REFERENCES
            )
            dead.append(self._dead_code_node(node, len(test_sources), reason))
            if len(dead) >= cap:
                break
        return dead

    def _reference_source_index(self) -> dict[str, tuple[set[str], set[str]]]:
        """Index every true reference's ``dst`` → its (production, test) source sets.

        One pass over the ``Ref`` rows of the true reference kinds. A row contributes
        its ``src_qname`` to the bucket keyed by its ``dst`` (a resolved FQN or a bare
        fallback name), split by whether the row's ``file_path`` is a test path. A
        per-symbol liveness check then looks the symbol up by BOTH its FQN and its
        bare last segment (the same FQN-or-bare seam :meth:`_reference_sources` uses),
        with the self-reference exclusion applied at lookup time.

        Returns:
            ``dst`` → ``(production_sources, test_sources)`` distinct ``src_qname``
            sets.
        """
        result = self._execute(
            f"""
            MATCH (r:{_REF_TABLE}) WHERE r.kind IN $reference_kinds
            RETURN DISTINCT r.dst AS dst, r.src_qname AS src_qname,
                   r.file_path AS file_path
            """,
            {"reference_kinds": list(_REFERENCE_KINDS)},
        )
        index: dict[str, tuple[set[str], set[str]]] = {}
        columns = result.get_column_names()
        while result.has_next():
            row = dict(zip(columns, self._row_values(result), strict=True))
            dst = str(row["dst"])
            production_sources, test_sources = index.setdefault(dst, (set(), set()))
            target = test_sources if self._is_test_path(str(row["file_path"])) else production_sources
            target.add(str(row["src_qname"]))
        return index

    @classmethod
    def _sources_for(
        cls, name: str, index: Mapping[str, tuple[set[str], set[str]]]
    ) -> tuple[set[str], set[str]]:
        """The (production, test) source sets that reference ``name`` from the index.

        Matches the symbol by its exact qualified name AND its bare last segment (the
        FQN-or-bare seam), unions the buckets, and drops the self-reference
        (``src_qname == name``) — exactly the semantics of the per-symbol query, but
        served from the pre-built index.
        """
        production_sources: set[str] = set()
        test_sources: set[str] = set()
        for key in (name, cls._bare_name(name)):
            bucket = index.get(key)
            if bucket is not None:
                production_sources |= bucket[0]
                test_sources |= bucket[1]
        production_sources.discard(name)
        test_sources.discard(name)
        return production_sources, test_sources

    def _candidate_nodes(self, tiers: Sequence[str]) -> list[GraphNode]:
        """The ``CodeNode`` rows whose ``tier`` is in ``tiers`` (the sweep candidates)."""
        return self._nodes_matching("n.tier IN $tiers", {"tiers": list(tiers)})

    def _is_excluded_candidate(
        self,
        node: GraphNode,
        *,
        include_tests: bool,
        include_dunders: bool,
        include_entrypoints: bool,
    ) -> bool:
        """Whether a candidate node is excluded from the sweep by a default rule."""
        if not include_tests and self._is_test_path(node.file_path):
            return True
        if (
            not include_dunders
            and node.kind == KIND_METHOD
            and fnmatch(self._bare_name(node.qualified_name), _DUNDER_GLOB)
        ):
            return True
        if (
            not include_entrypoints
            and node.kind == KIND_MODULE
            and self._is_entry_module(node)
        ):
            return True
        return False

    @staticmethod
    def _is_entry_module(node: GraphNode) -> bool:
        """Whether a ``module`` node is a package / entry module (always orphan-looking).

        ``True`` for a ``__main__`` module (a CLI entrypoint run as a script) and an
        ``__init__`` package module (collapsed to its package qualified name) — both
        identified from the node's ``file_path`` stem, which survives the qualified
        name collapse that erases the ``__init__`` segment.
        """
        stem = PurePosixPath(node.file_path).stem
        return stem in (_MAIN_MODULE_NAME, _INIT_STEM)

    @staticmethod
    def _dead_code_node(node: GraphNode, test_references: int, reason: str) -> DeadCodeNode:
        """Build a :class:`DeadCodeNode` from a node plus its test-reference profile."""
        return DeadCodeNode(
            id=node.id,
            kind=node.kind,
            qualified_name=node.qualified_name,
            file_path=node.file_path,
            chunk_id=node.chunk_id,
            tier=node.tier,
            test_references=test_references,
            reason=reason,
        )
