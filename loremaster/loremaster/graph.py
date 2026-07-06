"""Typed code-graph DERIVATION CORE — astroid-RESOLVED nodes and reference edges.

This module is the pure derivation layer of the code graph: it turns a file's
lorescribe AST chunks into typed graph NODES (:class:`_NodeSpec`) and directed
reference EDGES (:class:`_EdgeSpec`), applying astroid inference to RESOLVE
references to their in-project fully-qualified names. It owns NO storage — the
storage/query engine is the async :class:`~loremaster.graph_surreal.SurrealCodeGraph`
(the live SurrealDB backend), which REUSES this derivation core UNCHANGED through
its ``_AstroidDerivation`` delegate. The derivation is GENERIC over any Python AST
chunks the :class:`~lorescribe.python_ast.PythonAstChunker` emits — there is ZERO
Odoo-specific handling.

Node model. A node's identity is ``(kind, qualified_name)``; ``kind`` is one of
:data:`KIND_MODULE` / :data:`KIND_CLASS` / :data:`KIND_METHOD` /
:data:`KIND_FUNCTION`. The module node is SYNTHESISED (it has no originating
chunk, so its ``chunk_id`` is ``None``); every other node maps to one chunk. The
same fully-qualified name legitimately repeats across files (two modules each
defining ``Config``), so the tier/file_path that DISAMBIGUATE a node across the
corpus are STORAGE stamps applied by the engine, never part of the derived
:class:`_NodeSpec` — the derivation emits only the chunk-intrinsic identity.

Reference model. Each reference is a directed edge ``src -> dst`` of one of the
four :data:`EDGE_DEFINES` / :data:`EDGE_INHERITS` / :data:`EDGE_IMPORTS` /
:data:`EDGE_CALLS` kinds, carrying a ``resolved`` flag. ``dst`` is the resolved
in-project FQN when the reference resolved in-project, else the bare written name
(the conservative unresolved fallback). References are stored as records keyed on
``dst`` STRINGS (not native graph relations) by the storage engine, so an edge can
be created before its endpoints exist (order-independence) and a repeated FQN
across files stays distinct (collision-correctness).

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

  Resolution needs the file ON DISK under the project roots; when the core is
  constructed without roots (the in-memory seam) only structural ``defines`` edges
  are emitted, so the object still works without roots — production passes them.

Shared value objects. :class:`GraphNode` / :class:`ReferenceSummary` /
:class:`DeadCodeNode` are the ENGINE-NEUTRAL decoded-node models the storage
engine and the ``impact`` / ``map`` / ``server`` consumers import; the dead-code
liveness/exclusion helpers (:meth:`CodeGraph._is_excluded_candidate` /
:meth:`CodeGraph._liveness_sources` / :meth:`CodeGraph._dead_code_node`) are pure
logic the engine feeds a pre-built reference index, so the deadness decision lives
here and is reused unchanged across engines.
"""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from lorescribe.astroid_parse import (
    ParseError,
    ResolvedBase,
    ResolvedCall,
    ResolvedImport,
    ResolvedModule,
    clear_resolution_cache,
    evict_resolved_file,
    resolve_module,
)
from lorescribe.python_ast import (
    CHUNK_TYPE_CLASS,
    CHUNK_TYPE_FUNCTION,
    CHUNK_TYPE_METHOD,
)
from pydantic import BaseModel, ConfigDict, Field

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
# ``blast_radius`` max-results discipline the storage engine applies).
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


class GraphNode(BaseModel):
    """A single decoded graph node — the engine-neutral node value object.

    The derivation core emits :class:`_NodeSpec` (chunk-intrinsic identity only);
    the storage engine DECODES a stored row into this fuller shape, adding the
    identity, tier and originating file. Consumers (``impact`` / ``map`` /
    ``server`` and the SurrealDB engine) import this shared model.

    Attributes:
        id: The node's identity as a string. The derivation core assigns no id;
            the storage engine populates it (an int surrogate under the retired
            store, a composite record id under the SurrealDB engine) — typed
            ``str`` so either representation fits the same field.
        kind: One of :data:`KIND_MODULE` / :data:`KIND_CLASS` /
            :data:`KIND_METHOD` / :data:`KIND_FUNCTION`.
        qualified_name: The dotted name (``demo.service.IndexService.boot``).
        file_path: The tier-relative POSIX path the node was derived from.
        chunk_id: The originating chunk's ``identity`` (``None`` for the
            synthesised module node).
        tier: The source tier the node belongs to.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    kind: str
    qualified_name: str
    file_path: str
    chunk_id: str | None
    tier: str


class ReferenceSummary(BaseModel):
    """The reference profile of one symbol, split by reference ORIGIN.

    A reference from a TEST file does NOT count as a true reference, so the counts
    are split by whether the referencing file is a test path. A symbol whose only
    consumers are its tests is DEAD (``production_references == 0``). Built by the
    storage engine's ``references`` query from records the derivation core produced.

    Attributes:
        qualified_name: The symbol the references point at.
        production_references: Distinct references TO the symbol from NON-test
            files (the count that decides liveness).
        test_references: Distinct references TO the symbol from TEST files.
        referencing: The distinct nodes that reference the symbol, deduped.
        bare_fallback_used: Finding #65 (channel honesty). ``True`` iff at
            least one of the counted ``referencing`` sources is reachable
            ONLY through the query's bare-trailing-segment OR-term (or, for a
            genuinely bare query, only through the ``answers_to`` bridge to
            another FQN) — never through the query's own literal exact-name
            dst. This is the RISKY channel: an astroid-unresolvable caller
            anywhere in the corpus with the SAME bare tail rides it too, so a
            ``True`` value means the profile may be a UNION with an unrelated
            same-named symbol's references, not this one's exact profile
            alone. Keyed on the ACTUAL resolution channel a match rode, never
            on the syntactic shape of the query string (a query with no "."
            and a fully-qualified 4-segment query are judged identically).
        bare_fallback_candidates: The OTHER qualified names (never including
            ``qualified_name`` itself) whose ``answers_to`` fan-out shares the
            query's bare trailing segment — named so a caller can point at the
            real collidee(s) instead of a generic "may collide" caveat (finding
            #43). Always empty when :attr:`bare_fallback_used` is ``False``.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    qualified_name: str
    production_references: int
    test_references: int
    referencing: list[GraphNode]
    bare_fallback_used: bool = False
    bare_fallback_candidates: list[str] = Field(default_factory=list)


class DeadCodeNode(BaseModel):
    """A node reported by the dead-code sweep: zero PRODUCTION references.

    Carries the full :class:`GraphNode` shape plus the test-reference count and the
    labelled reason it is considered dead. Constructed by :meth:`CodeGraph._dead_code_node`
    (the reused deadness logic) from a pre-built reference index the storage engine
    supplies.

    Attributes:
        id: The node's identity as a string (as :class:`GraphNode`).
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

    id: str
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
    """The astroid DERIVATION CORE over Python AST chunks — pure, storage-free.

    Turns a file's chunks into node specs (:meth:`_derive_nodes`) and resolved
    reference specs (:meth:`_derive_edges`), and owns the pure dead-code deadness
    logic (:meth:`_is_excluded_candidate` / :meth:`_liveness_sources` /
    :meth:`_dead_code_node`) that a storage engine feeds a pre-built reference
    index. It holds NO database — the async
    :class:`~loremaster.graph_surreal.SurrealCodeGraph` engine reuses this core
    UNCHANGED through its ``_AstroidDerivation`` delegate and persists/queries the
    derived nodes and edges.

    References are astroid-RESOLVED: in-project ``imports`` / ``inherits`` /
    ``calls`` carry the inferred fully-qualified ``dst`` (and ``resolved=True``),
    external resolved references are dropped, and an un-inferable reference falls
    back to its bare written name (``resolved=False``). Resolution requires the
    file on disk under the project roots, so the roots are supplied at
    construction; without them the core emits only structural ``defines`` edges.

    Args:
        tier_roots: Optional mapping ``tier -> on-disk root`` the tier's
            tier-relative file paths are relative to. Used to locate a file on
            disk for astroid resolution. ``None`` ⇒ resolution is skipped.
        project_roots: Optional list of project root directories astroid adds to
            its search path and uses to classify a reference in-project vs
            external. ``None`` ⇒ resolution is skipped.
    """

    def __init__(
        self,
        *,
        tier_roots: Mapping[str, str | Path] | None = None,
        project_roots: Sequence[str | Path] | None = None,
    ) -> None:
        """Set up the resolution state the derivation reads (no database open).

        Resolution is only attempted when the project roots are known — otherwise
        astroid cannot place the file on disk nor classify references, so the core
        degrades to structural ``defines`` only.
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
        resolution seam). Without roots the core still works — it just carries only
        the structural ``defines`` references.
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

    def reset_resolution_cache(self) -> None:
        """Drop astroid's process-global resolution cache at a SWEEP boundary.

        :meth:`_derive_edges` deliberately does NOT clear astroid's cache per file:
        within a build/sweep the in-project DEPENDENCY modules astroid parses are
        REUSED across files, so each dependency is parsed ~once per sweep rather
        than once per file (the old per-file clear made the cold build
        O(files × dependency-fanout) — minutes for ~100 files, hours at Odoo scale,
        and it blocked server-lifespan startup).

        Persisting the cache is only safe because the chunker's structural parse no
        longer poisons it (see :func:`lorescribe.astroid_parse.parse_module`'s
        ``apply_transforms=False`` and the resolution poisoning-guard tests). The
        cache is still BOUNDED — it must not grow without limit across a long-lived
        process — so the indexer calls this ONCE at each full-sweep boundary
        (``rebuild_all`` / ``rebuild_graph_only``) to reset it between sweeps. A
        single watcher-event re-graph reuses the warm cache and does not reset it.
        """
        clear_resolution_cache()

    def _resolve(
        self, module: str, *, tier: str, file_path: str
    ) -> ResolvedModule | None:
        """Resolve a file's references via astroid, or ``None`` to skip resolution.

        Returns ``None`` (structural-only) when resolution is disabled (no project
        roots), the tier's on-disk base is unknown, the file is not on disk, or
        astroid cannot parse it — in every such case the core degrades to structural
        ``defines`` only rather than fabricating or crashing.

        astroid's cache is NOT cleared per file here. The chunker's structural parse
        no longer poisons the shared manager (it parses with transforms off, so it
        caches no failed import — see
        :func:`lorescribe.astroid_parse.parse_module`), so a chunk-then-resolve
        sequence keeps cross-module in-project references at their FQN without a
        clean-slate wipe. Leaving the cache WARM lets every file in a sweep reuse
        the dependency modules astroid already parsed — the speed win. The cache is
        bounded instead at sweep boundaries by :meth:`reset_resolution_cache`.

        Only THIS file is evicted from the warm cache before resolving (via
        :func:`evict_resolved_file`), because astroid caches a module by name with
        NO mtime check: re-graphing an EDITED file (a watcher event, or a file that
        was already parsed as another file's dependency earlier in the sweep) would
        otherwise resolve against the STALE pre-edit AST. Evicting just the target
        guarantees it is read fresh while its dependencies stay warm.
        """
        if not self._resolution_enabled:
            return None
        base = self._tier_roots.get(tier)
        if base is None:
            return None
        absolute_path = Path(base) / PurePosixPath(file_path)
        if not absolute_path.is_file():
            return None
        # Read THIS file fresh (defeats astroid's mtime-blind module cache) while
        # leaving every dependency module warm for reuse across the sweep.
        evict_resolved_file(str(absolute_path))
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

    # -- test-path classification ------------------------------------------

    @staticmethod
    def _is_test_path(file_path: str) -> bool:
        """Report whether ``file_path`` is a test file (glob or ``tests/`` dir)."""
        path = PurePosixPath(file_path)
        if _TESTS_DIR_NAME in path.parts:
            return True
        return any(fnmatch(path.name, glob) for glob in TEST_PATH_GLOBS)

    # -- dead-code deadness logic (pure; fed a pre-built reference index) ---

    def _liveness_sources(
        self,
        node: GraphNode,
        reference_index: Mapping[str, tuple[set[str], set[str]]],
        symbol_qualified_names: Sequence[str],
    ) -> tuple[set[str], set[str]]:
        """The (production, test) source sets deciding ``node``'s liveness.

        For a non-module node this is simply the sources referencing the node itself
        (the symbol-level rule — unchanged). For a MODULE node it is the UNION of
        the module's OWN references AND the references of every symbol it DEFINES —
        a node whose qualified name is dotted-prefix scoped under ``"<module>."``
        (its classes / functions / methods). Symbol-level references made the bare
        module name look orphaned even when the module is heavily used through its
        symbols; the roll-up fixes that while still reporting a genuinely orphaned
        module (no production source across the module or any of its symbols).

        Args:
            node: The candidate node whose liveness is being decided.
            reference_index: The pre-built ``dst`` → (production, test) source index.
            symbol_qualified_names: Every swept node's qualified name (the in-memory
                pool the module's defined-symbol set is scanned from).

        Returns:
            ``(production_sources, test_sources)`` — the unioned distinct source
            sets; the node is dead iff ``production_sources`` is empty.
        """
        production_sources, test_sources = self._sources_for(
            node.qualified_name, reference_index
        )
        if node.kind != KIND_MODULE:
            return production_sources, test_sources
        # Roll up every symbol the module DEFINES — a trailing-dot anchor keeps the
        # match module-scoped so ``pkg.a`` does not swallow a sibling ``pkg.ab``.
        defined_prefix = f"{node.qualified_name}{_QUALIFIER_SEPARATOR}"
        for symbol_qualified_name in symbol_qualified_names:
            if not symbol_qualified_name.startswith(defined_prefix):
                continue
            symbol_production, symbol_test = self._sources_for(
                symbol_qualified_name, reference_index
            )
            production_sources |= symbol_production
            test_sources |= symbol_test
        return production_sources, test_sources

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
