"""THE ONE catch-site walker + THE ONE caught-class resolver for the production tree (non-collected support).

*Scoped to the tree at ``4beb79e`` (branch ``feat/surreal-unification``), 2026-09-26, authored by
``contract-58-r3``.*

Packet 58 amendment 9 §3 (``4cb8ce9``) rules ONE walker and ONE resolver for every catch FORM — an
``except`` handler, an ``except*`` handler, and a ``with contextlib.suppress(...)`` item — and amendment 10
(``5b72471``) builds the FATE classifier (``test_exhaustion_fates.py``) on them.  They live HERE, in a
support module, so every consumer imports them rather than re-deriving: the fate rule, and (through §HELD
part 2 of ``REPORT-contract-58-r3.md``) ``test_retry_seam``'s guarded-CAS index, whose private
``_caught_classes`` becomes an import of :func:`caught_classes`.  (The pin that exactly ONE scanner exists
is 63c-i-a's — 63c amendment 34 §5; this module is the thing it will allowlist.)

Names resolve BY IMPORT in the site's own module namespace, so an alias, a re-export, a dotted path or a
Tuple element resolves to the object it IS, never to how it is spelled (the instrument lesson: a key on a
class NAME is defeated by the next spelling).  The tree is parsed through THE ONE tree parser,
``_logging_fixtures.parse_production_trees`` (finding #279 / F4)."""

from __future__ import annotations

import ast
import contextlib
import importlib
import inspect
from dataclasses import dataclass
from pathlib import Path
from typing import Any


def resolved_by_import(expression: ast.expr, module: Any, local: dict[str, Any] | None = None) -> Any:
    """Evaluate a name / dotted-attribute expression in ``module``'s namespace (plus ``local``: the names the
    enclosing function binds by its own ``import`` statements); ``None`` if it does not resolve."""
    namespace = {**vars(module), **(local or {})}
    try:
        return eval(compile(ast.Expression(expression), "<catch-site>", "eval"), namespace)  # noqa: S307
    except Exception:  # noqa: BLE001 - an unresolvable name is simply not a class we can reason about
        return None


def local_import_bindings(function: ast.AST | None, module: Any) -> dict[str, Any]:
    """The names a function binds by ``import`` / ``from … import`` statements in its OWN body (packet 58
    amendment 12 §2: a handler naming a function-local import is resolved where Python resolves it, not
    dropped) — imported through :mod:`importlib`, never executed."""
    bindings: dict[str, Any] = {}
    if function is None:
        return bindings
    for node in ast.walk(function):
        if isinstance(node, ast.ImportFrom):
            try:
                source = (
                    importlib.import_module("." * node.level + (node.module or ""), module.__package__)
                    if node.level
                    else importlib.import_module(node.module or "")
                )
            except Exception:  # noqa: BLE001 - an import that fails here is simply not a binding
                continue
            for alias in node.names:
                with contextlib.suppress(AttributeError):
                    bindings[alias.asname or alias.name] = getattr(source, alias.name)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                with contextlib.suppress(Exception):
                    target = alias.name if alias.asname else alias.name.split(".", 1)[0]
                    importlib.import_module(alias.name)
                    bindings[alias.asname or target] = importlib.import_module(target)
    return bindings


def _flatten(value: Any, label: str, classes: list[type], unresolved: list[str]) -> None:
    """What Python catches: a class, or a (nested) tuple of classes.  Anything else is UNRESOLVED, by name."""
    if inspect.isclass(value):
        classes.append(value)
    elif isinstance(value, tuple) and value:
        for member in value:
            _flatten(member, f"{label}[…]", classes, unresolved)
    else:
        unresolved.append(label)


def resolve_caught(
    site: ast.ExceptHandler | ast.Call, module: Any, local: dict[str, Any] | None = None
) -> tuple[list[type], list[str]]:
    """``(classes, unresolved)`` for a catch SITE, FAIL-CLOSED (packet 58 amendment 12 §2, F-A): each handler
    element is evaluated in its module (plus the function's local imports), a Name bound to a TUPLE constant,
    a nested Tuple and a ``*starred`` element are FLATTENED to their classes, and an element that does not
    resolve to classes is returned in ``unresolved`` as its source text — never silently dropped.  A BARE
    ``except:`` is ``BaseException``."""
    if isinstance(site, ast.Call):
        elements: list[ast.expr] = list(site.args)
    elif site.type is None:
        return [BaseException], []
    else:
        elements = list(site.type.elts) if isinstance(site.type, ast.Tuple) else [site.type]
    classes: list[type] = []
    unresolved: list[str] = []
    for element in elements:
        target = element.value if isinstance(element, ast.Starred) else element
        value = resolved_by_import(target, module, local)
        _flatten(value, ast.unparse(element), classes, unresolved)
    return classes, unresolved


def caught_classes(
    site: ast.ExceptHandler | ast.Call, module: Any, local: dict[str, Any] | None = None
) -> list[type]:
    """Every class a catch SITE catches, resolved BY IMPORT (the classes half of :func:`resolve_caught`).

    ⚠ DUAL (packet 58 contract r4 — amendment 12 §2; REPORT-contract-58-r4.md §ITEMS 2): this function USED
    to keep an element only ``if inspect.isclass(value)`` — a Name bound to a tuple constant
    (``except _CONNECTION_ERRORS:``) resolved to a tuple and was DISCARDED, so 12 exhaustion-catching sites
    fell out of every domain with no signal (adversary-58-r3 F-A).  It now flattens; the unresolvable
    remainder is :func:`resolve_caught`'s second half, which the fate census reds BY NAME."""
    return resolve_caught(site, module, local)[0]


def suppress_calls(node: ast.With | ast.AsyncWith, module: Any) -> list[ast.Call]:
    """The ``contextlib.suppress(...)`` calls a ``with`` statement enters — resolved BY IMPORT
    (``contextlib.suppress``,
    ``from contextlib import suppress``, or any alias bound to it)."""
    return [
        item.context_expr
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
        and resolved_by_import(item.context_expr.func, module) is contextlib.suppress
    ]


@dataclass(frozen=True)
class CatchSite:
    """One catch site.  ``handler`` is set for ``try``/``try*`` forms (``None`` for ``suppress``);
    ``earlier`` = the classes every clause ABOVE it in the same ``try`` catches (empty for ``suppress``)."""

    key: str
    file: str
    lineno: int
    form: str
    caught: tuple[type, ...]
    earlier: tuple[type, ...]
    handler: ast.ExceptHandler | None
    module: Any
    #: packet 58 amendment 12 §2: the handler elements that did NOT resolve to classes (source text) — the
    #: fail-closed half; ``test_exhaustion_fates`` reds every one BY NAME.
    unresolved: tuple[str, ...] = ()


def _parents_of(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _enclosing_function_name(node: ast.AST, parents: dict[int, ast.AST]) -> str:
    current = parents.get(id(node))
    while current is not None:
        if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return current.name
        if isinstance(current, ast.Lambda):
            return "<lambda>"
        current = parents.get(id(current))
    return "<module>"


def _enclosing_function(node: ast.AST, parents: dict[int, ast.AST]) -> ast.AST | None:
    current = parents.get(id(node))
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        current = parents.get(id(current))
    return current


def catch_sites_in(key: str, tree: ast.AST, module: Any) -> list[CatchSite]:
    """ONE module's catch sites, in source order — every ``try`` / ``try*`` handler and every ``suppress`` "
    "item."""
    parents = _parents_of(tree)
    sites: list[CatchSite] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.TryStar)):
            form = "try*" if isinstance(node, ast.TryStar) else "try"
            earlier: list[type] = []
            for handler in node.handlers:
                local = local_import_bindings(_enclosing_function(handler, parents), module)
                caught, unresolved = resolve_caught(handler, module, local)
                sites.append(
                    CatchSite(
                        key=f"{key}::{_enclosing_function_name(handler, parents)}",
                        file=key,
                        lineno=handler.lineno,
                        form=form,
                        caught=tuple(caught),
                        earlier=tuple(earlier),
                        handler=handler,
                        module=module,
                        unresolved=tuple(unresolved),
                    )
                )
                earlier.extend(caught)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for call in suppress_calls(node, module):
                local = local_import_bindings(_enclosing_function(node, parents), module)
                suppressed, unresolved = resolve_caught(call, module, local)
                sites.append(
                    CatchSite(
                        key=f"{key}::{_enclosing_function_name(node, parents)}",
                        file=key,
                        lineno=node.lineno,
                        form="suppress",
                        caught=tuple(suppressed),
                        earlier=(),
                        handler=None,
                        module=module,
                        unresolved=tuple(unresolved),
                    )
                )
    return sorted(sites, key=lambda site: (site.lineno, site.form))


def production_catch_sites() -> list[CatchSite]:
    """Every catch site of the ``loremaster`` production package, keyed ``"<package-relative "
    "path>::<function>"``."""
    from _logging_fixtures import _workspace_root, parse_production_trees

    import loremaster

    package_root = Path(loremaster.__file__ or "").parent
    prefix = package_root.resolve().relative_to(_workspace_root().resolve()).as_posix() + "/"
    sites: list[CatchSite] = []
    for relative, tree in sorted(parse_production_trees(include_scripts=False).items()):
        if not relative.startswith(prefix):
            continue
        key = relative[len(prefix) :]
        dotted = key[: -len(".py")].replace("/", ".")
        dotted = dotted[: -len(".__init__")] if dotted.endswith(".__init__") else dotted
        module = importlib.import_module(f"loremaster.{dotted}" if dotted != "__init__" else "loremaster")
        sites.extend(catch_sites_in(key, tree, module))
    return sites
