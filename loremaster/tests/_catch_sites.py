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


def resolved_by_import(expression: ast.expr, module: Any) -> Any:
    """Evaluate a name / dotted-attribute expression in ``module``'s namespace; ``None`` if it does not "
    "resolve."""
    try:
        return eval(compile(ast.Expression(expression), "<catch-site>", "eval"), vars(module))  # noqa: S307
    except Exception:  # noqa: BLE001 - an unresolvable name is simply not a class we can reason about
        return None


def caught_classes(site: ast.ExceptHandler | ast.Call, module: Any) -> list[type]:
    """Every class a catch SITE catches, resolved BY IMPORT: each element of a Tuple handler, a ``Name`` or a
    dotted ``Attribute`` alike; a ``contextlib.suppress(...)`` call's arguments; a BARE ``except:`` is
    ``BaseException``."""
    if isinstance(site, ast.Call):
        elements: list[ast.expr] = list(site.args)
    elif site.type is None:
        return [BaseException]
    else:
        elements = list(site.type.elts) if isinstance(site.type, ast.Tuple) else [site.type]
    resolved: list[type] = []
    for element in elements:
        value = resolved_by_import(element, module)
        if inspect.isclass(value):
            resolved.append(value)
    return resolved


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
                caught = caught_classes(handler, module)
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
                    )
                )
                earlier.extend(caught)
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for call in suppress_calls(node, module):
                sites.append(
                    CatchSite(
                        key=f"{key}::{_enclosing_function_name(node, parents)}",
                        file=key,
                        lineno=node.lineno,
                        form="suppress",
                        caught=tuple(caught_classes(call, module)),
                        earlier=(),
                        handler=None,
                        module=module,
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
