"""Contract tests for ``lorescribe.astroid_parse``.

``astroid_parse`` is the single shared module that parses Python source with
**astroid** exactly once and exposes a clean, astroid-internals-hiding API of
value objects. It exists so downstream consumers (the chunker now, the graph
deriver later) never touch raw astroid nodes and never import stdlib ``ast`` or
catch astroid exceptions themselves.

The contract pinned here (from the architect's pre-approved spec, NOT from any
implementation — the module does not exist when these tests are written):

* ``parse_module(source, *, qualified_name=None, path=None) -> ParsedModule``
  parses with astroid exactly once and returns a value-object tree. A syntax
  error surfaces as the module-owned typed exception ``ParseError`` (wrapping
  astroid's ``AstroidSyntaxError``) so callers branch to a fallback WITHOUT
  importing stdlib ``ast`` or catching astroid exceptions.

* ``ParsedModule`` exposes:
    - ``classes: list[ParsedClass]`` — top-level classes in source order.
    - ``functions: list[ParsedFunction]`` — top-level sync AND async functions
      in source order.
    - ``imports: ParsedImports | None`` — the min->max line span of all
      top-level ``Import`` / ``ImportFrom`` nodes, or ``None`` when there are
      none.

* ``ParsedClass``: ``name``, ``inherits`` (bare-``Name`` base names only,
  mirroring the chunker's historic behaviour — attribute bases like
  ``a.B`` are dropped), ``decorators`` (decorator-name list),
  ``line_start`` / ``line_end`` (1-based, the ``class`` keyword line through
  the class's last line — decorators are NOT folded into a class's start, just
  as the chunker never did), and ``methods: list[ParsedFunction]``.

* ``methods`` are discovered in source order, DESCENDING into ``if``/``else``,
  ``try`` (body / handlers / orelse / finalbody), and ``with`` / ``async with``
  blocks, but NOT into nested classes.

* ``ParsedFunction`` (a method or a top-level function): ``name``,
  ``decorators``, ``line_start`` (the first decorator's line when decorated,
  else the ``def`` line — decorator-inclusive), ``line_end``.

* **Decorator-name extraction parity**: a bare ``Name`` -> its name; an
  ``Attribute`` ``a.b`` -> ``"a.b"`` when the value is a simple name, else just
  ``"b"``; a ``Call`` decorator -> the called target's name (recursing the same
  rules). This mirrors the chunker's historic stdlib-``ast`` extraction exactly.

The strongest oracle here is **cross-parser parity**: the same structural facts
read independently via stdlib ``ast`` in this test file must match what
``astroid_parse`` returns. ``ast`` is used ONLY in the test as an independent
oracle — never in production.
"""

from __future__ import annotations

import ast
import textwrap

import pytest

# Target module under contract.
from lorescribe.astroid_parse import (
    ParsedClass,
    ParsedFunction,
    ParsedImports,
    ParsedModule,
    ParseError,
    parse_module,
)

# --------------------------------------------------------------------------- #
# Independent stdlib-``ast`` oracles. These re-derive the same structural facts #
# the production astroid parser must produce, using a DIFFERENT parser, so a    #
# parity assertion can fail on a real wrong implementation. Never imported by   #
# production code — test-only.                                                  #
# --------------------------------------------------------------------------- #


def _ast_decorator_names(node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> list[str]:
    """Oracle: decorator-name list via stdlib ast (the chunker's historic rule)."""
    names: list[str] = []
    for decorator in node.decorator_list:
        target = decorator.func if isinstance(decorator, ast.Call) else decorator
        if isinstance(target, ast.Attribute):
            if isinstance(target.value, ast.Name):
                names.append(f"{target.value.id}.{target.attr}")
            else:
                names.append(target.attr)
        elif isinstance(target, ast.Name):
            names.append(target.id)
    return names


def _ast_def_start(node: ast.FunctionDef | ast.AsyncFunctionDef) -> int:
    """Oracle: decorator-inclusive 1-based start line via stdlib ast."""
    if node.decorator_list:
        return node.decorator_list[0].lineno
    return node.lineno


def _ast_methods(class_node: ast.ClassDef) -> list[ast.FunctionDef | ast.AsyncFunctionDef]:
    """Oracle: a class's methods in source order, descending into control flow.

    Mirrors the chunker's historic descent: into ``if``/``else``, ``try``
    (body / handlers / orelse / finalbody), ``with`` / ``async with``; NOT into
    nested classes.
    """
    methods: list[ast.FunctionDef | ast.AsyncFunctionDef] = []

    def visit(body: list[ast.stmt]) -> None:
        for stmt in body:
            if isinstance(stmt, ast.FunctionDef | ast.AsyncFunctionDef):
                methods.append(stmt)
            elif isinstance(stmt, ast.If):
                visit(stmt.body)
                visit(stmt.orelse)
            elif isinstance(stmt, ast.Try):
                visit(stmt.body)
                for handler in stmt.handlers:
                    visit(handler.body)
                visit(stmt.orelse)
                visit(stmt.finalbody)
            elif isinstance(stmt, ast.With | ast.AsyncWith):
                visit(stmt.body)

    visit(class_node.body)
    methods.sort(key=lambda node: node.lineno)
    return methods


def _ast_class_inherits(class_node: ast.ClassDef) -> list[str]:
    """Oracle: bare-``Name`` base names only (drops attribute bases)."""
    return [base.id for base in class_node.bases if isinstance(base, ast.Name)]


# --------------------------------------------------------------------------- #
# Fixture sources. Representative production-shaped Python, not toys.          #
# --------------------------------------------------------------------------- #

REALISTIC_SOURCE: str = textwrap.dedent(
    '''\
    """A small but realistic module."""
    from __future__ import annotations

    import json
    import logging
    from dataclasses import dataclass
    from pathlib import Path

    logger = logging.getLogger(__name__)


    @dataclass(frozen=True)
    class Settings:
        """Immutable runtime settings."""

        root: Path

        @classmethod
        def from_file(cls, path: Path) -> "Settings":
            """Load settings from a JSON file."""
            return cls(root=Path(json.loads(path.read_text())["root"]))

        def with_root(self, root: Path) -> "Settings":
            """Return a copy with a different root."""
            return Settings(root=root)


    class IndexService(BaseService, dict):
        """Indexes documents; multiple bases."""

        def start(self) -> None:
            """Override start."""
            super().start()


    async def warm_cache(service: IndexService) -> None:
        """Top-level async helper."""
        service.start()


    def build_manifest(settings: Settings) -> dict[str, int]:
        """Top-level sync helper."""
        return {"root": str(settings.root)}
    '''
)


class TestParseModuleReturnsValueObjects:
    """The parse entry point returns only value objects, never astroid nodes."""

    def setup_method(self) -> None:
        self.module = parse_module(REALISTIC_SOURCE)

    def test_returns_parsed_module(self) -> None:
        assert isinstance(self.module, ParsedModule)

    def test_classes_are_parsed_class_value_objects(self) -> None:
        assert self.module.classes
        assert all(isinstance(cls, ParsedClass) for cls in self.module.classes)

    def test_functions_are_parsed_function_value_objects(self) -> None:
        assert self.module.functions
        assert all(isinstance(fn, ParsedFunction) for fn in self.module.functions)

    def test_methods_are_parsed_function_value_objects(self) -> None:
        for parsed_class in self.module.classes:
            assert all(
                isinstance(method, ParsedFunction) for method in parsed_class.methods
            )

    def test_no_astroid_node_leaks_into_value_objects(self) -> None:
        # Defensive: a value object must not carry a live astroid node under any
        # public attribute. astroid node classes live in the ``astroid`` package.
        def is_astroid_node(value: object) -> bool:
            return type(value).__module__.startswith("astroid")

        for parsed_class in self.module.classes:
            for value in vars(parsed_class).values():
                assert not is_astroid_node(value)
            for method in parsed_class.methods:
                for value in vars(method).values():
                    assert not is_astroid_node(value)
        for fn in self.module.functions:
            for value in vars(fn).values():
                assert not is_astroid_node(value)


class TestTopLevelClassParity:
    """Top-level classes match the independent stdlib-ast oracle."""

    def setup_method(self) -> None:
        self.source = REALISTIC_SOURCE
        self.module = parse_module(self.source)
        self.ast_tree = ast.parse(self.source)
        self.ast_classes = [
            node for node in self.ast_tree.body if isinstance(node, ast.ClassDef)
        ]

    def test_class_names_and_order_match_oracle(self) -> None:
        assert [c.name for c in self.module.classes] == [
            c.name for c in self.ast_classes
        ]

    def test_class_inherits_match_oracle(self) -> None:
        by_name = {c.name: c for c in self.module.classes}
        for ast_class in self.ast_classes:
            assert by_name[ast_class.name].inherits == _ast_class_inherits(ast_class)

    def test_inherits_drops_attribute_bases_keeps_bare_names(self) -> None:
        # IndexService(BaseService, dict): both are bare Names -> both kept.
        index = {c.name: c for c in self.module.classes}["IndexService"]
        assert index.inherits == ["BaseService", "dict"]

    def test_class_decorators_match_oracle(self) -> None:
        by_name = {c.name: c for c in self.module.classes}
        for ast_class in self.ast_classes:
            assert by_name[ast_class.name].decorators == _ast_decorator_names(ast_class)

    def test_class_line_span_matches_oracle(self) -> None:
        # Class start is the ``class`` keyword line (decorators NOT folded in),
        # mirroring the chunker's historic class-header start.
        by_name = {c.name: c for c in self.module.classes}
        for ast_class in self.ast_classes:
            parsed = by_name[ast_class.name]
            assert parsed.line_start == ast_class.lineno
            assert parsed.line_end == ast_class.end_lineno

    def test_decorated_class_start_is_class_keyword_not_decorator(self) -> None:
        # @dataclass(frozen=True) decorates Settings; the class line span must
        # start at the ``class Settings`` line, not the decorator line.
        settings = {c.name: c for c in self.module.classes}["Settings"]
        settings_ast = {c.name: c for c in self.ast_classes}["Settings"]
        assert settings.line_start == settings_ast.lineno
        # The decorator line is strictly above the class line.
        assert settings_ast.decorator_list[0].lineno < settings.line_start


class TestMethodParity:
    """Methods (including control-flow-nested) match the stdlib-ast oracle."""

    def setup_method(self) -> None:
        self.source = REALISTIC_SOURCE
        self.module = parse_module(self.source)
        self.ast_tree = ast.parse(self.source)
        self.ast_classes = {
            node.name: node
            for node in self.ast_tree.body
            if isinstance(node, ast.ClassDef)
        }

    def test_method_names_and_order_match_oracle(self) -> None:
        for parsed_class in self.module.classes:
            ast_methods = _ast_methods(self.ast_classes[parsed_class.name])
            assert [m.name for m in parsed_class.methods] == [
                m.name for m in ast_methods
            ]

    def test_method_decorators_match_oracle(self) -> None:
        for parsed_class in self.module.classes:
            ast_methods = {m.name: m for m in _ast_methods(self.ast_classes[parsed_class.name])}
            for method in parsed_class.methods:
                assert method.decorators == _ast_decorator_names(ast_methods[method.name])

    def test_method_line_span_is_decorator_inclusive_and_matches_oracle(self) -> None:
        for parsed_class in self.module.classes:
            ast_methods = {m.name: m for m in _ast_methods(self.ast_classes[parsed_class.name])}
            for method in parsed_class.methods:
                ast_method = ast_methods[method.name]
                assert method.line_start == _ast_def_start(ast_method)
                assert method.line_end == ast_method.end_lineno

    def test_classmethod_decorator_captured(self) -> None:
        settings = {c.name: c for c in self.module.classes}["Settings"]
        from_file = {m.name: m for m in settings.methods}["from_file"]
        assert from_file.decorators == ["classmethod"]


class TestControlFlowNestedMethods:
    """Methods nested in if/else, try, with are surfaced; nested classes are not."""

    SOURCE: str = textwrap.dedent(
        '''\
        class Toggle:
            if True:
                def run(self):
                    return "a"
            else:
                def run(self):
                    return "b"

            try:
                def in_try(self):
                    return 1
            except ValueError:
                def in_handler(self):
                    return 2
            else:
                def in_orelse(self):
                    return 3
            finally:
                def in_finally(self):
                    return 4

            with open("x") as f:
                def in_with(self):
                    return 5

            class Nested:
                def nested_method(self):
                    return "should not surface as Toggle's method"
        '''
    )

    def setup_method(self) -> None:
        self.module = parse_module(self.SOURCE)
        self.toggle = {c.name: c for c in self.module.classes}["Toggle"]
        self.method_names = [m.name for m in self.toggle.methods]
        ast_tree = ast.parse(self.SOURCE)
        toggle_ast = next(
            n for n in ast_tree.body if isinstance(n, ast.ClassDef) and n.name == "Toggle"
        )
        self.oracle_names = [m.name for m in _ast_methods(toggle_ast)]

    def test_method_names_match_control_flow_oracle(self) -> None:
        assert self.method_names == self.oracle_names

    def test_conditional_def_both_branches_surface(self) -> None:
        # The if/else conditional ``run`` appears twice (one per branch).
        assert self.method_names.count("run") == 2

    def test_try_handler_orelse_finally_methods_surface(self) -> None:
        for name in ("in_try", "in_handler", "in_orelse", "in_finally"):
            assert name in self.method_names

    def test_with_block_method_surfaces(self) -> None:
        assert "in_with" in self.method_names

    def test_nested_class_method_does_not_surface(self) -> None:
        # ``nested_method`` belongs to ``Nested``, not ``Toggle``.
        assert "nested_method" not in self.method_names
        # ``Nested`` is not a top-level class either.
        assert "Nested" not in [c.name for c in self.module.classes]


class TestTopLevelFunctionParity:
    """Top-level sync and async functions match the stdlib-ast oracle."""

    def setup_method(self) -> None:
        self.source = REALISTIC_SOURCE
        self.module = parse_module(self.source)
        ast_tree = ast.parse(self.source)
        self.ast_functions = [
            node
            for node in ast_tree.body
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef)
        ]

    def test_function_names_and_order_match_oracle(self) -> None:
        assert [f.name for f in self.module.functions] == [
            f.name for f in self.ast_functions
        ]

    def test_async_function_is_included(self) -> None:
        # ``warm_cache`` is ``async def`` — it must appear as a top-level fn.
        assert "warm_cache" in [f.name for f in self.module.functions]

    def test_function_line_span_matches_oracle(self) -> None:
        by_name = {f.name: f for f in self.module.functions}
        for ast_fn in self.ast_functions:
            parsed = by_name[ast_fn.name]
            assert parsed.line_start == _ast_def_start(ast_fn)
            assert parsed.line_end == ast_fn.end_lineno


class TestDecoratorNameExtractionParity:
    """Every decorator shape resolves identically to the stdlib-ast oracle."""

    SOURCE: str = textwrap.dedent(
        '''\
        @bare
        @mod.attr
        @mod.sub.deep
        @called(1, 2)
        @mod.attr_called(x=1)
        def target():
            return 1
        '''
    )

    def setup_method(self) -> None:
        self.module = parse_module(self.SOURCE)
        self.target = {f.name: f for f in self.module.functions}["target"]
        ast_tree = ast.parse(self.SOURCE)
        self.ast_target = next(
            n for n in ast_tree.body if isinstance(n, ast.FunctionDef)
        )

    def test_decorator_names_match_oracle_exactly(self) -> None:
        assert self.target.decorators == _ast_decorator_names(self.ast_target)

    def test_bare_name_decorator(self) -> None:
        assert "bare" in self.target.decorators

    def test_simple_attribute_decorator(self) -> None:
        assert "mod.attr" in self.target.decorators

    def test_deep_attribute_decorator_uses_attrname_only(self) -> None:
        # ``mod.sub.deep``: value is an Attribute (not a simple Name), so the
        # chunker's historic rule yields just the final attribute ``deep``.
        assert "deep" in self.target.decorators
        assert "mod.sub.deep" not in self.target.decorators

    def test_call_decorator_uses_called_target_name(self) -> None:
        # ``@called(1, 2)`` -> ``called``.
        assert "called" in self.target.decorators

    def test_attribute_call_decorator(self) -> None:
        # ``@mod.attr_called(x=1)`` -> ``mod.attr_called``.
        assert "mod.attr_called" in self.target.decorators


class TestImportsSpan:
    """The imports value object spans min->max top-level import lines, else None."""

    def test_imports_span_matches_oracle(self) -> None:
        source = REALISTIC_SOURCE
        module = parse_module(source)
        ast_tree = ast.parse(source)
        import_nodes = [
            node
            for node in ast_tree.body
            if isinstance(node, ast.Import | ast.ImportFrom)
        ]
        expected_start = min(n.lineno for n in import_nodes)
        expected_end = max(n.end_lineno or n.lineno for n in import_nodes)
        assert isinstance(module.imports, ParsedImports)
        assert module.imports.line_start == expected_start
        assert module.imports.line_end == expected_end

    def test_no_imports_yields_none(self) -> None:
        source = textwrap.dedent(
            """\
            def ping():
                return "pong"
            """
        )
        module = parse_module(source)
        assert module.imports is None

    def test_imports_only_module_spans_all_imports(self) -> None:
        source = textwrap.dedent(
            """\
            import os
            import sys
            from pathlib import Path
            """
        )
        module = parse_module(source)
        assert module.imports is not None
        assert module.imports.line_start == 1
        assert module.imports.line_end == 3
        assert module.classes == []
        assert module.functions == []


class TestSyntaxErrorRaisesTypedError:
    """Unparseable source raises the module-owned ParseError, not astroid's."""

    BROKEN_SOURCE: str = "def broken(:\n    pass\n"

    def test_raises_parse_error(self) -> None:
        with pytest.raises(ParseError):
            parse_module(self.BROKEN_SOURCE)

    def test_parse_error_is_not_stdlib_syntax_error(self) -> None:
        # The whole point: callers branch on ParseError without importing ast or
        # knowing about astroid. ParseError is the module's own type.
        try:
            parse_module(self.BROKEN_SOURCE)
        except ParseError as exc:
            # It is the module's own type, distinct from builtins.SyntaxError.
            assert type(exc).__name__ == "ParseError"
            assert isinstance(exc, Exception)
        else:
            raise AssertionError("expected ParseError")

    def test_parity_with_ast_on_unparseable(self) -> None:
        # Cross-parser parity on the error path: stdlib ast also rejects this.
        with pytest.raises(SyntaxError):
            ast.parse(self.BROKEN_SOURCE)
        with pytest.raises(ParseError):
            parse_module(self.BROKEN_SOURCE)


class TestEmptyAndTrivialSources:
    """Empty / whitespace / no-symbol sources parse to an empty value tree."""

    def test_empty_source_parses_to_empty_module(self) -> None:
        module = parse_module("")
        assert module.classes == []
        assert module.functions == []
        assert module.imports is None

    def test_whitespace_only_source_parses_to_empty_module(self) -> None:
        module = parse_module("   \n\n   ")
        assert module.classes == []
        assert module.functions == []
        assert module.imports is None

    def test_module_with_only_statements_has_no_symbols(self) -> None:
        module = parse_module("x = 1\ny = x + 2\n")
        assert module.classes == []
        assert module.functions == []
        assert module.imports is None


class TestOptionalQualifiedNameAccepted:
    """The parse entry point accepts (and tolerates) qualified_name / path."""

    def test_qualified_name_kwarg_is_accepted(self) -> None:
        module = parse_module(REALISTIC_SOURCE, qualified_name="pkg.services")
        assert isinstance(module, ParsedModule)
        # Structure is identical whether or not a qualified name is supplied.
        assert [c.name for c in module.classes] == [
            c.name for c in parse_module(REALISTIC_SOURCE).classes
        ]

    def test_path_kwarg_is_accepted(self) -> None:
        module = parse_module(REALISTIC_SOURCE, path="src/pkg/services.py")
        assert isinstance(module, ParsedModule)

    def test_both_kwargs_accepted_together(self) -> None:
        module = parse_module(
            REALISTIC_SOURCE, qualified_name="pkg.services", path="src/pkg/services.py"
        )
        assert isinstance(module, ParsedModule)


class TestRepeatedParsingIsStable:
    """Parsing many modules does not leak state via astroid's global cache."""

    def test_same_source_parsed_twice_is_structurally_identical(self) -> None:
        first = parse_module(REALISTIC_SOURCE, qualified_name="pkg.a")
        second = parse_module(REALISTIC_SOURCE, qualified_name="pkg.a")
        assert [c.name for c in first.classes] == [c.name for c in second.classes]
        assert [
            m.name for c in first.classes for m in c.methods
        ] == [m.name for c in second.classes for m in c.methods]

    def test_different_modules_do_not_cross_contaminate(self) -> None:
        # Parse a different-shaped module between two parses of the realistic
        # source; the realistic parse must be unaffected by astroid's manager
        # cache holding the other module.
        baseline = parse_module(REALISTIC_SOURCE)
        parse_module("class Other:\n    def m(self):\n        return 1\n", qualified_name="pkg.b")
        after = parse_module(REALISTIC_SOURCE)
        assert [c.name for c in baseline.classes] == [c.name for c in after.classes]


class TestStructuralParseLeavesNoNegativeImportResidue:
    """The structural parse MUST NOT poison astroid's shared import cache.

    ``parse_module`` is the chunker's purely-STRUCTURAL parse: it reads a module's
    top-level classes / functions / import span by name and never needs astroid to
    RESOLVE an import. astroid's manager is a process-global borg, though, so if the
    structural parse let astroid's brain transforms FOLLOW a ``from pkg.dep import X``
    statement, that resolution would fail (the project roots are not on the search
    path during chunking) and astroid would cache the FAILURE in its shared
    ``_mod_file_cache`` as an ``AstroidImportError``. A later
    :func:`lorescribe.astroid_parse.resolve_module` would then re-use that cached
    NEGATIVE result and degrade the cross-module reference to its bare name.

    This pins the no-poison property at the parser level: after the structural
    parse, astroid's manager holds NO cached import FAILURE for the named
    dependency. It is the unit-level guarantee that lets the graph drop its
    per-file whole-cache wipe.
    """

    SOURCE_WITH_CROSS_MODULE_IMPORT: str = (
        "from somepkg.dependency import Thing, helper\n\n\n"
        "class Consumer(Thing):\n    def run(self):\n        return helper()\n"
    )

    def test_parse_does_not_cache_a_failed_import(self) -> None:
        import astroid
        from astroid.exceptions import AstroidImportError
        from lorescribe.astroid_parse import clear_resolution_cache

        # Start from a clean manager so the assertion sees only THIS parse's residue.
        clear_resolution_cache()
        try:
            parse_module(
                self.SOURCE_WITH_CROSS_MODULE_IMPORT,
                qualified_name="somepkg.consumer",
                path="somepkg/consumer.py",
            )
            # No entry in the shared module-file cache may be a cached IMPORT
            # FAILURE — that negative cache is exactly the poison a downstream
            # resolution would inherit. (A successful ModuleSpec would be fine;
            # what must never appear is the cached AstroidImportError.)
            failures = {
                key: value
                for key, value in astroid.MANAGER._mod_file_cache.items()
                if isinstance(value, AstroidImportError)
            }
            assert failures == {}, (
                "structural parse poisoned astroid's import cache with a cached "
                f"failure (a later resolve would inherit it): {failures!r}"
            )
        finally:
            clear_resolution_cache()
