"""Shared astroid-based parser for Python source: structure AND resolution.

This module is the single place in production that touches astroid — downstream
consumers (the ``python_ast`` chunker, the graph deriver) read its value objects
and never import astroid, touch a raw astroid node, or catch an astroid
exception. It exposes two SEPARABLE capabilities so each consumer pays only for
what it needs:

* **Structure (fast).** :func:`parse_module` parses a source STRING with astroid
  exactly once and returns a tree of value objects describing top-level
  structure: classes (with their methods), top-level functions, and the import
  span. No inference — this is what the chunker uses, and it pays no inference
  cost.

* **Resolution (slow).** :func:`resolve_module` loads a module ON DISK, drives
  astroid INFERENCE, and returns value objects whose references — imports, class
  bases, and call sites — are resolved to fully-qualified names, each classified
  in-project vs external against the provided project roots and flagged
  ``resolved``. Resolution is intentionally PARTIAL: a reference astroid cannot
  infer is kept as a bare-name fallback rather than dropped. This feeds the code
  graph; the chunker never invokes it. :func:`clear_resolution_cache` bounds
  astroid's process-global manager cache between resolution batches.

Design notes:

* **Internals are hidden behind value objects.** Every public return is a frozen
  dataclass carrying only plain Python types (``str`` / ``int`` / ``list`` /
  ``None``). No astroid node ever escapes this module's boundary.

* **Syntax errors are this module's own typed failure.** astroid raises
  :class:`astroid.exceptions.AstroidSyntaxError`; we catch it and re-raise
  :class:`ParseError` so callers branch to their fallback WITHOUT importing
  stdlib ``ast`` or knowing astroid exists.

* **Structural parity with the historic stdlib-``ast`` extraction.** Class
  ``inherits`` keeps bare-``Name`` bases only; methods are discovered descending
  into ``if``/``else``, ``try`` (body / handlers / orelse / finalbody), and
  ``with`` / ``async with`` blocks but NOT into nested classes; a decorated def's
  ``line_start`` is its first decorator's line; a class's ``line_start`` is the
  ``class`` keyword line (decorators are not folded into a class's span).

* **The manager cache is shared and bounded deliberately.** astroid keeps a
  process-global :class:`~astroid.manager.AstroidManager` cache keyed by module
  name. :func:`parse_module` derives structure only from the freshly returned
  tree, so the cache never leaks state into a STRUCTURAL result.
  :func:`resolve_module` instead RELIES on that cache (and on the project roots
  being on the search path) to infer cross-module references, so it grows with
  each distinct module resolved; :func:`clear_resolution_cache` empties it and
  undoes the search-path mutation between unrelated resolution batches to keep
  it bounded and prevent cross-contamination.

astroid node-shape gotchas handled here (vs stdlib ``ast``):

* ``Name.name`` (not ``.id``); ``Attribute.attrname`` + ``Attribute.expr``
  (not ``.attr`` / ``.value``).
* ``FunctionDef.decorators`` is a :class:`~astroid.nodes.Decorators` node whose
  ``.nodes`` is the decorator list, or ``None`` when undecorated.
* ``AsyncFunctionDef`` subclasses ``FunctionDef``, so a single ``isinstance``
  check against ``FunctionDef`` captures both.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import astroid
from astroid import nodes
from astroid.bases import Proxy
from astroid.exceptions import (
    AstroidError,
    AstroidSyntaxError,
    TooManyLevelsError,
)
from astroid.util import Uninferable


class ParseError(Exception):
    """A Python source string could not be parsed.

    This is the module's own typed failure, raised in place of astroid's
    :class:`~astroid.exceptions.AstroidSyntaxError` so callers can branch to a
    fallback path without importing stdlib ``ast`` or catching astroid's
    exception types. The originating astroid error is chained as ``__cause__``.
    """


@dataclass(frozen=True)
class ParsedFunction:
    """A function or method, reduced to its structural facts.

    Attributes:
        name: The bare function / method name.
        decorators: Decorator names in source order (see
            :func:`_decorator_names` for the extraction rule).
        line_start: 1-based first source line — the first decorator's line when
            the def is decorated, otherwise the ``def`` (or ``async def``) line.
        line_end: 1-based last source line of the def's body.
    """

    name: str
    decorators: list[str]
    line_start: int
    line_end: int


@dataclass(frozen=True)
class ParsedClass:
    """A top-level class, reduced to its structural facts.

    Attributes:
        name: The bare class name.
        inherits: Base-class names — bare ``Name`` bases only, mirroring the
            historic chunker behaviour (attribute bases such as ``a.B`` are
            dropped).
        decorators: Class-decorator names in source order.
        line_start: 1-based ``class`` keyword line. Class decorators are NOT
            folded into the start (matching the chunker's historic class span).
        line_end: 1-based last source line of the class body.
        methods: The class's methods in source order, discovered descending into
            control-flow blocks but not into nested classes.
    """

    name: str
    inherits: list[str]
    decorators: list[str]
    line_start: int
    line_end: int
    methods: list[ParsedFunction]


@dataclass(frozen=True)
class ParsedImports:
    """The min->max line span of a module's top-level import statements.

    Attributes:
        line_start: 1-based first line of the earliest top-level import.
        line_end: 1-based last line of the latest top-level import.
    """

    line_start: int
    line_end: int


@dataclass(frozen=True)
class ParsedModule:
    """A module's top-level structure as plain value objects.

    Attributes:
        classes: Top-level classes in source order.
        functions: Top-level functions (sync and async) in source order.
        imports: The top-level import span, or ``None`` when the module has no
            top-level imports.
    """

    classes: list[ParsedClass] = field(default_factory=list)
    functions: list[ParsedFunction] = field(default_factory=list)
    imports: ParsedImports | None = None


# Last-resort line number when astroid leaves a node's ``lineno`` unset
# (typed ``int | None``). 1 is the smallest valid 1-based line, so it can never
# yield a zero/negative span; in practice the def/class/import nodes this module
# reads always carry a real line, exactly as they did under stdlib ``ast``.
_FALLBACK_LINENO: int = 1


def _lineno(node: nodes.NodeNG) -> int:
    """Return a node's 1-based ``lineno`` as a definite ``int``.

    astroid types ``lineno`` as ``int | None``; the ``None`` fallback keeps the
    return total without ever fabricating an out-of-range line.
    """
    return node.lineno if node.lineno is not None else _FALLBACK_LINENO


def _line_end(node: nodes.NodeNG) -> int:
    """Return a node's 1-based ``end_lineno``, defaulting to its start line.

    astroid normally populates ``end_lineno``; the fallback to ``lineno`` mirrors
    the chunker's historic ``node.end_lineno or node.lineno`` defence so a node
    that somehow lacks an end line still yields a sane single-line span.
    """
    return node.end_lineno if node.end_lineno is not None else _lineno(node)


def _definition_start_line(node: nodes.FunctionDef) -> int:
    """Return a def's decorator-inclusive 1-based start line.

    A decorated def starts at its first decorator so the decorator travels with
    the unit; an undecorated def starts at its ``def`` (or ``async def``) line.
    """
    if node.decorators and node.decorators.nodes:
        return _lineno(node.decorators.nodes[0])
    return _lineno(node)


def _decorator_names(node: nodes.FunctionDef | nodes.ClassDef) -> list[str]:
    """Extract decorator names from a def or class, mirroring the historic rule.

    For each decorator (unwrapping a ``Call`` to its called target first):

    * a bare ``Name`` -> its ``name`` (``classmethod``);
    * an ``Attribute`` whose value is a simple ``Name`` -> ``"value.attr"``
      (``api.depends``);
    * an ``Attribute`` whose value is anything else -> just the final
      ``attrname`` (``mod.sub.deep`` -> ``deep``).

    Anything that resolves to neither shape is skipped, exactly as the stdlib
    implementation skipped non-``Name`` / non-``Attribute`` targets.
    """
    if node.decorators is None:
        return []
    names: list[str] = []
    for decorator in node.decorators.nodes:
        target = decorator.func if isinstance(decorator, nodes.Call) else decorator
        if isinstance(target, nodes.Attribute):
            if isinstance(target.expr, nodes.Name):
                names.append(f"{target.expr.name}.{target.attrname}")
            else:
                names.append(target.attrname)
        elif isinstance(target, nodes.Name):
            names.append(target.name)
    return names


def _class_inherits(class_node: nodes.ClassDef) -> list[str]:
    """Return bare-``Name`` base-class names only (drops attribute bases)."""
    return [base.name for base in class_node.bases if isinstance(base, nodes.Name)]


def _iter_methods(class_node: nodes.ClassDef) -> list[nodes.FunctionDef]:
    """Return a class's methods in source order, descending into control flow.

    A method may be a direct child of the class body or nested inside an
    ``if``/``else``, ``try`` (body / handlers / orelse / finalbody), or
    ``with`` / ``async with`` block (conditional definitions). Nested classes
    are NOT descended into — their methods belong to the nested class.

    ``AsyncFunctionDef`` subclasses ``FunctionDef``, so the single
    ``isinstance(stmt, nodes.FunctionDef)`` check captures async methods too.
    """
    methods: list[nodes.FunctionDef] = []

    def visit(body: list[nodes.NodeNG]) -> None:
        for stmt in body:
            if isinstance(stmt, nodes.FunctionDef):
                methods.append(stmt)
            elif isinstance(stmt, nodes.If):
                visit(stmt.body)
                visit(stmt.orelse)
            elif isinstance(stmt, nodes.Try):
                visit(stmt.body)
                for handler in stmt.handlers:
                    visit(handler.body)
                visit(stmt.orelse)
                visit(stmt.finalbody)
            elif isinstance(stmt, (nodes.With, nodes.AsyncWith)):
                visit(stmt.body)
            # nodes.ClassDef is intentionally skipped: a nested class's methods
            # are not this class's methods.

    visit(class_node.body)
    # Source order: control-flow recursion can interleave; sort by line.
    methods.sort(key=_lineno)
    return methods


def _build_parsed_function(node: nodes.FunctionDef) -> ParsedFunction:
    """Reduce an astroid def node to a :class:`ParsedFunction` value object."""
    return ParsedFunction(
        name=node.name,
        decorators=_decorator_names(node),
        line_start=_definition_start_line(node),
        line_end=_line_end(node),
    )


def _build_parsed_class(class_node: nodes.ClassDef) -> ParsedClass:
    """Reduce an astroid class node to a :class:`ParsedClass` value object."""
    return ParsedClass(
        name=class_node.name,
        inherits=_class_inherits(class_node),
        decorators=_decorator_names(class_node),
        line_start=_lineno(class_node),
        line_end=_line_end(class_node),
        methods=[_build_parsed_function(method) for method in _iter_methods(class_node)],
    )


def _build_imports(module_node: nodes.Module) -> ParsedImports | None:
    """Return the top-level import line span, or ``None`` when there are none."""
    import_nodes = [
        node
        for node in module_node.body
        if isinstance(node, (nodes.Import, nodes.ImportFrom))
    ]
    if not import_nodes:
        return None
    line_start = min(_lineno(node) for node in import_nodes)
    line_end = max(_line_end(node) for node in import_nodes)
    return ParsedImports(line_start=line_start, line_end=line_end)


# --------------------------------------------------------------------------- #
# RESOLUTION API (additive) — value objects.                                    #
# These are the slow, inference-based counterpart to the structural objects     #
# above. They carry only plain types; no astroid node escapes them.             #
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class ResolvedImport:
    """A module's import reference, resolved to a fully-qualified target.

    Attributes:
        target: The fully-qualified name the import refers to. For ``import a.b``
            this is the module ``a.b``; for an in-project ``from a import foo``
            it is the symbol ``a.foo``; for an external ``from a import foo`` it
            is the module ``a``. An unresolvable relative import falls back to
            the bare written name (never dropped).
        in_project: ``True`` when the import's defining module lives under one of
            the provided project roots, ``False`` for stdlib / third-party.
        resolved: ``True`` when astroid located the imported module/symbol on the
            search path, ``False`` when it could not be resolved.
        is_symbol: ``True`` when ``target`` names a symbol (``a.foo``), ``False``
            when it names a module (``a.b``).
    """

    target: str
    in_project: bool
    resolved: bool
    is_symbol: bool


@dataclass(frozen=True)
class ResolvedBase:
    """A class base, resolved to its defining class's fully-qualified name.

    Attributes:
        target: The base class's FQN (``pkg.mod.Base``) when astroid inferred it,
            else the bare written base name (never dropped).
        in_project: ``True`` when the base is defined under a project root.
        resolved: ``True`` when astroid inferred the base to a class definition.
    """

    target: str
    in_project: bool
    resolved: bool


@dataclass(frozen=True)
class ResolvedCall:
    """A call site, resolved to its callee's fully-qualified name.

    Attributes:
        target: The callee's FQN (``pkg.mod.Class.method`` / ``builtins.len``)
            when astroid inferred it, else a bare-name fallback (the ``Name`` id
            or the trailing ``Attribute`` attr) so the reference is never lost.
        in_project: ``True`` when the inferred callee's DEFINING FILE lies under a
            project root. Always ``False`` for an unresolved bare-name fallback.
        resolved: ``True`` when astroid inferred the callee, ``False`` on a
            ``Uninferable`` / inference-failure fallback.
    """

    target: str
    in_project: bool
    resolved: bool


@dataclass(frozen=True)
class ResolvedFunction:
    """A function or method keyed by its FQN, with its resolved call sites.

    Attributes:
        qualified_name: The function/method's dotted FQN
            (``pkg.mod.func`` / ``pkg.mod.Class.method``).
        calls: One :class:`ResolvedCall` per call site in source order.
    """

    qualified_name: str
    calls: list[ResolvedCall]


@dataclass(frozen=True)
class ResolvedClass:
    """A class keyed by its FQN, with its resolved bases and methods.

    Attributes:
        qualified_name: The class's dotted FQN (``pkg.mod.Class``).
        inherits: One :class:`ResolvedBase` per declared base in source order.
        methods: One :class:`ResolvedFunction` per method (including
            control-flow-nested methods, excluding nested classes' methods).
    """

    qualified_name: str
    inherits: list[ResolvedBase]
    methods: list[ResolvedFunction]


@dataclass(frozen=True)
class ResolvedModule:
    """A module's references resolved to FQNs, as plain value objects.

    Attributes:
        qualified_name: The module's own dotted FQN (``pkg.mod``).
        imports: The module's import references (``__future__`` excluded).
        classes: Top-level classes, each with resolved bases and methods.
        functions: Top-level functions (sync and async), each with resolved
            calls. Methods live under their class, not here.
    """

    qualified_name: str
    imports: list[ResolvedImport] = field(default_factory=list)
    classes: list[ResolvedClass] = field(default_factory=list)
    functions: list[ResolvedFunction] = field(default_factory=list)


# A search-path entry this module pushed onto ``sys.path`` so astroid can resolve
# in-project cross-module references. Tracked so :func:`clear_resolution_cache`
# can undo the mutation and never permanently pollute the process search path.
_ADDED_SEARCH_PATHS: list[str] = []


def clear_resolution_cache() -> None:
    """Clear astroid's process-global cache and undo search-path mutation.

    astroid keeps a single process-wide :class:`~astroid.manager.AstroidManager`
    whose cache grows with every distinct module resolved; resolving many files
    in one process would otherwise grow it unbounded and let one file's package
    leak into another's resolution. This empties that cache and removes any
    search-path entries :func:`resolve_module` added, restoring a clean slate so
    sequential resolutions cannot cross-contaminate.
    """
    astroid.MANAGER.clear_cache()
    for entry in _ADDED_SEARCH_PATHS:
        try:
            sys.path.remove(entry)
        except ValueError:
            # Already gone (e.g. cleared twice) — nothing to undo.
            pass
    _ADDED_SEARCH_PATHS.clear()


def _ensure_on_search_path(project_roots: list[str] | tuple[str, ...]) -> None:
    """Add each project root to ``sys.path`` so astroid resolves in-project refs.

    astroid's manager imports referenced modules off the ordinary import search
    path; without the roots on it, a cross-module in-project callee infers to
    ``Uninferable``. Roots already present are left alone (so we never remove an
    entry we did not add); newly added ones are tracked for
    :func:`clear_resolution_cache` to undo.
    """
    for root in project_roots:
        absolute_root = os.path.abspath(root)
        if absolute_root not in sys.path:
            sys.path.insert(0, absolute_root)
            _ADDED_SEARCH_PATHS.append(absolute_root)


def _is_under_roots(file_path: str | None, project_roots: list[str] | tuple[str, ...]) -> bool:
    """Return whether ``file_path`` lies under any of the project roots.

    ``file_path`` is the inferred node's defining file (``root().file``). It is
    ``None`` for builtins (which therefore classify external), and a stdlib /
    third-party path that lies outside every project root, so the containment
    check is the in-project vs external classifier.
    """
    if not file_path:
        return False
    absolute_file = os.path.abspath(file_path)
    for root in project_roots:
        absolute_root = os.path.abspath(root)
        if os.path.commonpath([absolute_file, absolute_root]) == absolute_root:
            return True
    return False


def _node_defining_file(inferred: object) -> str | None:
    """Return the on-disk file that defines an inferred node, or ``None``.

    astroid's ``infer()`` yields a union (``NodeNG`` / a ``Proxy`` such as a
    ``BoundMethod`` / an ``UninferableBase``); every concrete inferred node that
    survives this module's ``qname()``-callable guard exposes ``root()``, whose
    ``file`` is the defining path used to classify in-project vs external. The
    ``getattr`` walk keeps this total across that union without leaking an
    astroid type into the signature. ``None`` (e.g. builtins) classifies as
    external.
    """
    root_attr = getattr(inferred, "root", None)
    if not callable(root_attr):
        return None
    root = root_attr()
    file_path: str | None = getattr(root, "file", None)
    return file_path


def _bare_callee_name(call_func: nodes.NodeNG) -> str:
    """Return the bare fallback name for a callee astroid could not infer.

    A ``Name`` callee falls back to its id; an ``Attribute`` callee to its
    trailing attr; anything else (e.g. ``getattr(o, n)()`` whose callee is itself
    a ``Call``) falls back to the nested callee's name so the reference is still
    recorded rather than silently dropped.
    """
    if isinstance(call_func, nodes.Name):
        return call_func.name
    if isinstance(call_func, nodes.Attribute):
        return call_func.attrname
    if isinstance(call_func, nodes.Call):
        return _bare_callee_name(call_func.func)
    return call_func.as_string()


def _infer_fqn_and_scope(
    node: nodes.NodeNG | Proxy, project_roots: list[str] | tuple[str, ...]
) -> tuple[str, bool] | None:
    """Infer ``node`` to ``(fully_qualified_name, in_project)`` or ``None``.

    The single inference primitive shared by call-site and base-class resolution:
    it asks astroid to infer ``node`` to a definite definition, reads that
    definition's ``qname()`` as the FQN, and classifies it in-project vs external
    by the definition's defining file. Returns ``None`` when astroid yields
    ``Uninferable``, raises an inference error, or produces a node without a
    ``qname()`` — the caller then applies its own bare-name fallback so a
    reference is never silently dropped.
    """
    try:
        # ``infer()`` is a generator; an inference failure surfaces here as an
        # AstroidError (InferenceError is one). The ``None`` default means a
        # callee with no inference results yields ``None`` rather than raising.
        inferred = next(node.infer(), None)
    except AstroidError:
        return None
    if inferred is None or inferred is Uninferable:
        return None
    qname_attr = getattr(inferred, "qname", None)
    if not callable(qname_attr):
        return None
    fully_qualified_name: str = qname_attr()
    in_project = _is_under_roots(_node_defining_file(inferred), project_roots)
    return fully_qualified_name, in_project


def _resolve_call(
    call: nodes.Call, project_roots: list[str] | tuple[str, ...]
) -> ResolvedCall:
    """Resolve one call site's callee to a :class:`ResolvedCall`.

    On a successful inference the callee's FQN and in-project flag are taken from
    :func:`_infer_fqn_and_scope`; otherwise the call falls back to a bare name
    (``resolved=False``) so the reference is never dropped.
    """
    resolution = _infer_fqn_and_scope(call.func, project_roots)
    if resolution is None:
        return ResolvedCall(
            target=_bare_callee_name(call.func), in_project=False, resolved=False
        )
    target, in_project = resolution
    return ResolvedCall(target=target, in_project=in_project, resolved=True)


def _resolve_calls_in(
    func_node: nodes.FunctionDef, project_roots: list[str] | tuple[str, ...]
) -> list[ResolvedCall]:
    """Resolve every call site lexically inside ``func_node`` in source order.

    Nested function/lambda call sites are included — they belong to the same
    written unit. Call sites are ordered by their source line so the result is
    stable across runs.
    """
    calls = sorted(func_node.nodes_of_class(nodes.Call), key=_lineno)
    return [_resolve_call(call, project_roots) for call in calls]


def _resolve_base(
    base: nodes.NodeNG | Proxy, project_roots: list[str] | tuple[str, ...]
) -> ResolvedBase:
    """Resolve one class base to a :class:`ResolvedBase`.

    On a successful inference the base's FQN and in-project flag are taken from
    :func:`_infer_fqn_and_scope`; an unresolvable base falls back to its written
    name (``resolved=False``).
    """
    resolution = _infer_fqn_and_scope(base, project_roots)
    if resolution is None:
        return ResolvedBase(target=base.as_string(), in_project=False, resolved=False)
    target, in_project = resolution
    return ResolvedBase(target=target, in_project=in_project, resolved=True)


def _absolute_import_modname(
    import_from: nodes.ImportFrom, module_node: nodes.Module
) -> str | None:
    """Return the absolute dotted module a ``from ... import`` refers to.

    A plain (``level``-less) import is already absolute. A relative one
    (``from .mod import X`` / ``from . import x``) is made absolute against the
    importing module's package via astroid's
    :meth:`~astroid.nodes.Module.relative_to_absolute_name`. An over-deep
    relative import (more parents than the package nesting allows) cannot be
    resolved, yielding ``None`` so the caller falls back to a bare name.
    """
    level = import_from.level
    written_modname = import_from.modname or ""
    if not level:
        return written_modname or None
    try:
        return module_node.relative_to_absolute_name(written_modname, level)
    except TooManyLevelsError:
        # More parent levels than the package nesting allows — unresolvable.
        return None


def _resolve_import_from(
    import_from: nodes.ImportFrom,
    module_node: nodes.Module,
    project_roots: list[str] | tuple[str, ...],
) -> list[ResolvedImport]:
    """Resolve a ``from ... import a, b`` statement to one record per name.

    ``__future__`` imports are skipped. The source module is resolved to its
    absolute FQN (relative imports via ``level``); if it is in-project each
    imported name becomes a SYMBOL target (``mod.name``), otherwise a single
    MODULE target (``mod``) is emitted (external symbols are not deepened, per
    the spec). An unresolvable relative module yields a bare-name module record.
    """
    if import_from.modname == "__future__":
        return []
    absolute_modname = _absolute_import_modname(import_from, module_node)
    if absolute_modname is None:
        # Unresolvable relative import — keep the bare written name, never drop.
        written = "." * (import_from.level or 0) + (import_from.modname or "")
        return [
            ResolvedImport(target=written, in_project=False, resolved=False, is_symbol=False)
        ]
    defining_file = _imported_module_file(absolute_modname)
    in_project = _is_under_roots(defining_file, project_roots)
    resolved = defining_file is not None
    if in_project:
        return [
            ResolvedImport(
                target=f"{absolute_modname}.{name}",
                in_project=True,
                resolved=resolved,
                is_symbol=True,
            )
            for name, _alias in import_from.names
        ]
    return [
        ResolvedImport(
            target=absolute_modname,
            in_project=False,
            resolved=resolved,
            is_symbol=False,
        )
    ]


def _resolve_plain_import(
    import_node: nodes.Import, project_roots: list[str] | tuple[str, ...]
) -> list[ResolvedImport]:
    """Resolve an ``import a.b, c`` statement to one MODULE record per name."""
    records: list[ResolvedImport] = []
    for name, _alias in import_node.names:
        defining_file = _imported_module_file(name)
        records.append(
            ResolvedImport(
                target=name,
                in_project=_is_under_roots(defining_file, project_roots),
                resolved=defining_file is not None,
                is_symbol=False,
            )
        )
    return records


def _imported_module_file(modname: str) -> str | None:
    """Return the on-disk file backing ``modname`` via astroid, or ``None``.

    Used to classify an import in-project vs external by where its module is
    defined. A module astroid cannot import (typo, missing dependency) yields
    ``None``, marking the import unresolved.
    """
    try:
        imported = astroid.MANAGER.ast_from_module_name(modname)
    except AstroidError:
        # astroid could not import/build the module (typo, missing dependency,
        # not on the search path) -> unresolved. astroid raises AstroidImportError
        # / AstroidBuildingError here, both AstroidError subclasses.
        return None
    file_path: str | None = getattr(imported, "file", None)
    return file_path


def resolve_module(
    path: str,
    *,
    project_roots: list[str] | tuple[str, ...],
    qualified_name: str | None = None,
) -> ResolvedModule:
    """Resolve a module's references to fully-qualified names via astroid inference.

    This is the slow, inference-based counterpart to the fast structural
    :func:`parse_module`. It loads the module ON DISK with astroid (configuring
    the search path from ``project_roots`` so cross-module in-project references
    resolve) and returns a tree of frozen value objects describing the module's
    resolved imports, class bases, and call sites. No astroid node escapes.

    Args:
        path: On-disk path of the module to resolve.
        project_roots: Root directories of the project. They are added to the
            module search path so in-project cross-module references resolve, and
            they classify each resolved target in-project (defined under a root)
            vs external (stdlib / third-party / builtin).
        qualified_name: Unused for resolution (the module's FQN is read from the
            astroid module astroid builds from ``path``); accepted for signature
            symmetry with :func:`parse_module`.

    Returns:
        A :class:`ResolvedModule`. Resolution is intentionally PARTIAL: a
        reference astroid cannot infer is kept as a bare-name fallback with
        ``resolved=False`` rather than dropped.

    Raises:
        ParseError: If the module's source is not parseable Python. The
            originating astroid error is chained as ``__cause__``.

    Note:
        astroid's manager cache is process-global and grows per distinct module.
        Call :func:`clear_resolution_cache` between unrelated resolution batches
        to bound it and prevent cross-contamination.
    """
    _ensure_on_search_path(project_roots)
    try:
        module_node = astroid.MANAGER.ast_from_file(path)
    except AstroidSyntaxError as exc:
        raise ParseError(str(exc)) from exc

    imports: list[ResolvedImport] = []
    classes: list[ResolvedClass] = []
    functions: list[ResolvedFunction] = []
    for node in module_node.body:
        if isinstance(node, nodes.ImportFrom):
            imports.extend(_resolve_import_from(node, module_node, project_roots))
        elif isinstance(node, nodes.Import):
            imports.extend(_resolve_plain_import(node, project_roots))
        elif isinstance(node, nodes.ClassDef):
            classes.append(_build_resolved_class(node, project_roots))
        elif isinstance(node, nodes.FunctionDef):
            functions.append(_build_resolved_function(node, project_roots))

    return ResolvedModule(
        qualified_name=module_node.name,
        imports=imports,
        classes=classes,
        functions=functions,
    )


def _build_resolved_function(
    func_node: nodes.FunctionDef, project_roots: list[str] | tuple[str, ...]
) -> ResolvedFunction:
    """Reduce a def node to a :class:`ResolvedFunction` with resolved call sites."""
    return ResolvedFunction(
        qualified_name=func_node.qname(),
        calls=_resolve_calls_in(func_node, project_roots),
    )


def _build_resolved_class(
    class_node: nodes.ClassDef, project_roots: list[str] | tuple[str, ...]
) -> ResolvedClass:
    """Reduce a class node to a :class:`ResolvedClass` with bases and methods."""
    return ResolvedClass(
        qualified_name=class_node.qname(),
        inherits=[_resolve_base(base, project_roots) for base in class_node.bases],
        methods=[
            _build_resolved_function(method, project_roots)
            for method in _iter_methods(class_node)
        ],
    )


def parse_module(
    source: str,
    *,
    qualified_name: str | None = None,
    path: str | None = None,
) -> ParsedModule:
    """Parse Python ``source`` into a structural value tree.

    Args:
        source: The full Python source text.
        qualified_name: Optional dotted module name. Currently used only to name
            the astroid module (it does not affect the returned structure); it
            is a forward hook so a later phase can enable astroid cross-module
            resolution without changing this signature.
        path: Optional on-disk path of the source. Accepted for the same forward
            hook; unused for structure today.

    Returns:
        A :class:`ParsedModule` describing the module's top-level classes
        (with methods), top-level functions, and import span.

    Raises:
        ParseError: If ``source`` is not parseable Python. The originating
            astroid error is chained as ``__cause__``.
    """
    module_name = qualified_name or ""
    try:
        module_node = astroid.parse(source, module_name=module_name, path=path)
    except AstroidSyntaxError as exc:
        raise ParseError(str(exc)) from exc

    classes: list[ParsedClass] = []
    functions: list[ParsedFunction] = []
    for node in module_node.body:
        if isinstance(node, nodes.ClassDef):
            classes.append(_build_parsed_class(node))
        elif isinstance(node, nodes.FunctionDef):
            # AsyncFunctionDef subclasses FunctionDef -> async functions included.
            functions.append(_build_parsed_function(node))

    return ParsedModule(
        classes=classes,
        functions=functions,
        imports=_build_imports(module_node),
    )
