"""Contract tests for the RESOLUTION API of ``lorescribe.astroid_parse``.

This is the second, purely-additive capability of ``astroid_parse``: alongside
the fast STRUCTURAL parser (:func:`parse_module`, used by the chunker), a slow
INFERENCE-based resolver turns a module's references — imports, inherited bases,
and call sites — into fully-qualified names, classifying each target as
in-project vs external and flagging whether astroid actually resolved it.

The contract pinned here (from the architect's pre-approved spec, NOT from the
implementation — the resolution API does not exist when these tests are
written):

* ``resolve_module(path, *, project_roots, qualified_name=None) -> ResolvedModule``
  parses the on-disk module with astroid, configures the module search path from
  ``project_roots`` so cross-module in-project inference works, and returns a
  tree of frozen value objects. NO astroid node escapes (same discipline as the
  structural API).

* ``ResolvedModule``: ``qualified_name`` (dotted module name), ``imports``
  (list[ResolvedImport]), ``classes`` (list[ResolvedClass]), ``functions``
  (list[ResolvedFunction] — top-level functions only; methods live under their
  class).

* ``ResolvedImport``: ``target`` (FQN — module or symbol), ``in_project``,
  ``resolved``, ``is_symbol`` (True when the target names a symbol like
  ``a.foo``, False when it names a module like ``a.b``).
    - ``import a.b`` -> module target ``a.b`` (is_symbol=False).
    - ``from a import foo`` -> symbol target ``a.foo`` (is_symbol=True) when
      in-project; else module target ``a`` (is_symbol=False).
    - relative ``from .mod import X`` / ``from . import x`` resolved against the
      module's package via ``level``.
    - ``__future__`` imports are skipped entirely.

* ``ResolvedBase`` (one per class base): ``target`` (base FQN, or the bare name
  when unresolvable), ``in_project``, ``resolved``.

* ``ResolvedCall`` (one per call site): ``target`` (callee FQN when inferred,
  else the bare ``Name`` id / trailing ``Attribute`` attr), ``in_project``,
  ``resolved``.
    - astroid infers the callee -> ``(callee_fqn, in_project, resolved=True)``,
      where ``in_project`` is decided by the inferred node's DEFINING FILE
      (``root().file``) lying under one of ``project_roots``.
    - ``Uninferable`` / inference failure -> ``(bare_name, in_project=False,
      resolved=False)``. The reference is NEVER silently dropped.
    - a self / recursive call resolves to the caller's OWN qualified name
      (in-project).

* ``ResolvedClass``: ``qualified_name``, ``inherits`` (list[ResolvedBase]),
  ``methods`` (list[ResolvedFunction]).

* ``ResolvedFunction``: ``qualified_name``, ``calls`` (list[ResolvedCall]).

* ``clear_resolution_cache()`` clears astroid's process-global manager cache and
  undoes any search-path mutation, so resolving two unrelated modules in
  sequence cannot cross-contaminate.

ORACLE INDEPENDENCE: the fixtures are a small on-disk package this test file
authors, so the TRUE fully-qualified names are known a-priori from the package
layout the test wrote — not re-derived from the resolver's own logic.
"""

from __future__ import annotations

import sys
import textwrap
from collections.abc import Iterator
from pathlib import Path

import pytest

# Target resolution API under contract.
from lorescribe.astroid_parse import (
    ResolvedBase,
    ResolvedCall,
    ResolvedClass,
    ResolvedFunction,
    ResolvedImport,
    ResolvedModule,
    clear_resolution_cache,
    resolve_module,
)

# --------------------------------------------------------------------------- #
# On-disk multi-file fixture. A small package the test AUTHORS, so the true     #
# FQNs are known from the layout the test wrote (independent oracle).           #
#                                                                               #
#   demo/                                                                       #
#     __init__.py            -> VALUE = 1                                       #
#     registry.py            -> class Registry: def register(self, item)        #
#     external_stub/                                                            #
#       __init__.py          -> class FakeBaseModel  (separate "external" pkg)  #
#     service.py             -> imports + Service(Registry-using) + helpers      #
#     models.py              -> class Widget(FakeBaseModel)  (external base)     #
#     relativeuser.py        -> relative imports against demo                    #
# --------------------------------------------------------------------------- #


@pytest.fixture
def project(tmp_path: Path) -> Iterator[dict[str, object]]:
    """Author the on-disk ``demo`` package and return paths + the project root.

    ``external_stub`` is a SEPARATE top-level package placed OUTSIDE the project
    root. To mirror a real installed third-party dependency (importable, but not
    part of the project), its root is put directly on ``sys.path`` for the test —
    it is NOT passed as a project root — so a call/inheritance into it RESOLVES
    yet classifies external. That is an in-project oracle distinct from
    stdlib/builtins: astroid CAN resolve it, but it lies outside ``project_root``.
    """
    project_root = tmp_path / "src"
    project_root.mkdir()

    demo = project_root / "demo"
    demo.mkdir()
    (demo / "__init__.py").write_text("VALUE = 1\n")

    (demo / "registry.py").write_text(
        textwrap.dedent(
            """\
            class Registry:
                def register(self, item):
                    return item
            """
        )
    )

    # An "external" package authored OUTSIDE the project root.
    external_root = tmp_path / "ext"
    external_root.mkdir()
    external_stub = external_root / "external_stub"
    external_stub.mkdir()
    (external_stub / "__init__.py").write_text(
        textwrap.dedent(
            """\
            class FakeBaseModel:
                pass
            """
        )
    )

    (demo / "service.py").write_text(
        textwrap.dedent(
            """\
            from __future__ import annotations

            import json
            from demo.registry import Registry
            from external_stub import FakeBaseModel

            class Service:
                def __init__(self):
                    self._registry = Registry()

                def boot(self):
                    self._registry.register(1)
                    json.dumps({})
                    return self.boot()

                def dynamic(self, obj, name):
                    return getattr(obj, name)()

                def builtin_call(self):
                    return len([1, 2, 3])

            def top_level_helper():
                return Service().boot()
            """
        )
    )

    (demo / "models.py").write_text(
        textwrap.dedent(
            """\
            from external_stub import FakeBaseModel

            class Widget(FakeBaseModel):
                def shape(self):
                    return 1
            """
        )
    )

    (demo / "relativeuser.py").write_text(
        textwrap.dedent(
            """\
            from . import VALUE
            from .registry import Registry
            import demo.registry
            """
        )
    )

    # Put the external package's root on sys.path directly — as if it were an
    # installed third-party dependency — so astroid resolves it WITHOUT it being
    # a project root. The project root itself is added by resolve_module().
    sys.path.insert(0, str(external_root))
    try:
        yield {
            "project_root": project_root,
            "external_root": external_root,
            "demo": demo,
            "service": demo / "service.py",
            "models": demo / "models.py",
            "registry": demo / "registry.py",
            "relativeuser": demo / "relativeuser.py",
            # ONLY the true project root is the project root. external_stub is
            # importable (above) but outside it -> classified external.
            "roots": (str(project_root),),
        }
    finally:
        try:
            sys.path.remove(str(external_root))
        except ValueError:
            pass


@pytest.fixture(autouse=True)
def _clean_manager() -> object:
    """Reset astroid's global cache + search path around every test.

    Resolution touches a process-global ``astroid.MANAGER`` and mutates the
    module search path; without this autouse reset, one test's fixture package
    leaks into the next and FQNs cross-contaminate.
    """
    clear_resolution_cache()
    yield None
    clear_resolution_cache()


def _resolve_service(project: dict[str, object]) -> ResolvedModule:
    return resolve_module(str(project["service"]), project_roots=project["roots"])  # type: ignore[arg-type]


def _resolve_models(project: dict[str, object]) -> ResolvedModule:
    return resolve_module(str(project["models"]), project_roots=project["roots"])  # type: ignore[arg-type]


def _calls_of(module: ResolvedModule, class_name: str, method_name: str) -> list[ResolvedCall]:
    qname_suffix = f"{class_name}.{method_name}"
    for parsed_class in module.classes:
        for method in parsed_class.methods:
            if method.qualified_name.endswith(qname_suffix):
                return method.calls
    raise AssertionError(f"method {qname_suffix} not found")


class TestReturnsValueObjects:
    """The resolver returns only frozen value objects, never astroid nodes."""

    def test_returns_resolved_module(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        assert isinstance(module, ResolvedModule)

    def test_module_qualified_name_is_dotted_fqn(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        # The file is demo/service.py under the project root -> demo.service.
        assert module.qualified_name == "demo.service"

    def test_value_object_types(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        assert all(isinstance(imp, ResolvedImport) for imp in module.imports)
        assert all(isinstance(cls, ResolvedClass) for cls in module.classes)
        assert all(isinstance(fn, ResolvedFunction) for fn in module.functions)
        for parsed_class in module.classes:
            assert all(isinstance(m, ResolvedFunction) for m in parsed_class.methods)
            assert all(isinstance(b, ResolvedBase) for b in parsed_class.inherits)
            for method in parsed_class.methods:
                assert all(isinstance(c, ResolvedCall) for c in method.calls)

    def test_no_astroid_node_leaks(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)

        def is_astroid_node(value: object) -> bool:
            return type(value).__module__.startswith("astroid")

        def check(obj: object) -> None:
            for value in vars(obj).values():
                assert not is_astroid_node(value)
                if isinstance(value, list):
                    for item in value:
                        if hasattr(item, "__dict__"):
                            check(item)

        check(module)


class TestCrossModuleCallResolution:
    """A call into another in-project module resolves to the callee's FQN."""

    def test_method_call_on_in_project_type_resolves_to_fqn(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        boot_calls = _calls_of(module, "Service", "boot")
        targets = {call.target for call in boot_calls}
        # self._registry.register -> demo.registry.Registry.register
        assert "demo.registry.Registry.register" in targets

    def test_cross_module_call_is_in_project_and_resolved(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        boot_calls = _calls_of(module, "Service", "boot")
        register = next(
            c for c in boot_calls if c.target == "demo.registry.Registry.register"
        )
        assert register.in_project is True
        assert register.resolved is True

    def test_top_level_function_calls_resolve(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        helper = next(
            fn for fn in module.functions if fn.qualified_name.endswith("top_level_helper")
        )
        targets = {call.target for call in helper.calls}
        # Service().boot() -> demo.service.Service.boot (in-project).
        assert "demo.service.Service.boot" in targets


class TestInProjectVsExternalClassification:
    """In-project calls flag in_project=True; stdlib/builtin/separate-pkg = False."""

    def test_builtin_call_is_external(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        calls = _calls_of(module, "Service", "builtin_call")
        # len([...]) -> builtins.len, external (a consumer may drop it).
        builtin = next(c for c in calls if c.target.endswith("len"))
        assert builtin.in_project is False

    def test_stdlib_call_is_external(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        boot_calls = _calls_of(module, "Service", "boot")
        # json.dumps -> json.dumps, external.
        stdlib = next(c for c in boot_calls if "dumps" in c.target)
        assert stdlib.in_project is False

    def test_separate_external_package_call_is_external(
        self, project: dict[str, object]
    ) -> None:
        # A call resolving into external_stub (outside project_root) is external
        # even though astroid CAN resolve it — classification is by defining file.
        module = _resolve_models(project)
        widget = next(c for c in module.classes if c.qualified_name.endswith("Widget"))
        base = widget.inherits[0]
        assert base.resolved is True
        assert base.in_project is False

    def test_in_project_call_is_in_project(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        boot_calls = _calls_of(module, "Service", "boot")
        register = next(
            c for c in boot_calls if c.target == "demo.registry.Registry.register"
        )
        assert register.in_project is True


class TestUnresolvedCallFallsBackToBareName:
    """A dynamic, uninferable call falls back to a bare name — never dropped."""

    def test_dynamic_call_not_dropped(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        calls = _calls_of(module, "Service", "dynamic")
        # getattr(obj, name)() is uninferable; SOMETHING must still be recorded.
        assert calls, "uninferable call must not be silently dropped"

    def test_dynamic_call_marked_unresolved_and_external(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        calls = _calls_of(module, "Service", "dynamic")
        unresolved = [c for c in calls if not c.resolved]
        assert unresolved, "the uninferable call must be present with resolved=False"
        for call in unresolved:
            assert call.in_project is False
            assert call.target  # a non-empty bare-name fallback


class TestRecursionResolvesToOwnFqn:
    """A function calling itself resolves to its own qualified name (in-project)."""

    def test_self_recursive_call_resolves_to_caller_fqn(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        boot_calls = _calls_of(module, "Service", "boot")
        # return self.boot() -> demo.service.Service.boot (the caller itself).
        recursive = next(
            (c for c in boot_calls if c.target == "demo.service.Service.boot"), None
        )
        assert recursive is not None
        assert recursive.in_project is True
        assert recursive.resolved is True


class TestImportResolution:
    """Imports resolve to module/symbol FQNs; relatives use level; __future__ skipped."""

    def test_plain_import_is_module_target(self, project: dict[str, object]) -> None:
        module = resolve_module(
            str(project["relativeuser"]),
            project_roots=[str(project["project_root"])],
        )
        # import demo.registry -> module target demo.registry.
        plain = next(i for i in module.imports if i.target == "demo.registry")
        assert plain.is_symbol is False
        assert plain.in_project is True

    def test_symbol_import_in_project_is_symbol_target(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        # from demo.registry import Registry -> symbol demo.registry.Registry.
        symbol = next(
            (i for i in module.imports if i.target == "demo.registry.Registry"), None
        )
        assert symbol is not None
        assert symbol.is_symbol is True
        assert symbol.in_project is True
        assert symbol.resolved is True

    def test_external_symbol_import_classified_external(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_service(project)
        # from external_stub import FakeBaseModel: external -> per the contract a
        # `from a import foo` that is NOT in-project collapses to the MODULE
        # target `a` (is_symbol=False), not a deepened symbol target.
        ext = next(
            (i for i in module.imports if i.target == "external_stub"), None
        )
        assert ext is not None
        assert ext.in_project is False
        assert ext.is_symbol is False

    def test_relative_symbol_import_resolves_against_package(
        self, project: dict[str, object]
    ) -> None:
        module = resolve_module(
            str(project["relativeuser"]),
            project_roots=[str(project["project_root"])],
        )
        # from .registry import Registry (in demo) -> demo.registry.Registry.
        rel = next(
            (i for i in module.imports if i.target == "demo.registry.Registry"), None
        )
        assert rel is not None
        assert rel.is_symbol is True
        assert rel.in_project is True

    def test_relative_package_import_resolves(self, project: dict[str, object]) -> None:
        module = resolve_module(
            str(project["relativeuser"]),
            project_roots=[str(project["project_root"])],
        )
        # from . import VALUE (in demo) -> demo.VALUE.
        rel = next((i for i in module.imports if i.target == "demo.VALUE"), None)
        assert rel is not None
        assert rel.in_project is True

    def test_future_import_is_skipped(self, project: dict[str, object]) -> None:
        module = _resolve_service(project)
        # service.py opens with `from __future__ import annotations`.
        assert all("__future__" not in imp.target for imp in module.imports)


class TestInheritsResolution:
    """Class bases resolve to FQN; external base flagged external; unresolvable -> bare."""

    def test_external_base_resolves_to_fqn_flagged_external(
        self, project: dict[str, object]
    ) -> None:
        module = _resolve_models(project)
        widget = next(c for c in module.classes if c.qualified_name.endswith("Widget"))
        base = widget.inherits[0]
        # Resolves to external_stub.FakeBaseModel but classified external.
        assert base.target == "external_stub.FakeBaseModel"
        assert base.resolved is True
        assert base.in_project is False

    def test_unresolvable_base_falls_back_to_bare_name(self, tmp_path: Path) -> None:
        root = tmp_path / "p"
        root.mkdir()
        pkg = root / "mod"
        pkg.mkdir()
        (pkg / "__init__.py").write_text("")
        target = pkg / "thing.py"
        target.write_text(
            textwrap.dedent(
                """\
                class Thing(NameThatDoesNotExist):
                    pass
                """
            )
        )
        module = resolve_module(str(target), project_roots=[str(root)])
        thing = next(c for c in module.classes if c.qualified_name.endswith("Thing"))
        base = thing.inherits[0]
        assert base.resolved is False
        assert base.target == "NameThatDoesNotExist"


class TestStateLeakageBetweenModules:
    """Resolving two different modules in sequence does not cross-contaminate."""

    def test_two_modules_resolved_in_sequence_are_isolated(
        self, project: dict[str, object]
    ) -> None:
        service = _resolve_service(project)
        models = resolve_module(
            str(project["models"]),
            project_roots=[str(project["project_root"]), str(project["external_root"])],
        )
        # Each module reports its OWN qualified name and its OWN classes — no
        # bleed of Service into models or vice-versa.
        assert service.qualified_name == "demo.service"
        assert models.qualified_name == "demo.models"
        assert any(c.qualified_name.endswith("Service") for c in service.classes)
        assert all(not c.qualified_name.endswith("Widget") for c in service.classes)
        assert any(c.qualified_name.endswith("Widget") for c in models.classes)
        assert all(not c.qualified_name.endswith("Service") for c in models.classes)

    def test_resolution_repeatable_after_cache_clear(
        self, project: dict[str, object]
    ) -> None:
        first = _resolve_service(project)
        clear_resolution_cache()
        second = _resolve_service(project)
        first_targets = {
            c.target for c in _calls_of(first, "Service", "boot")
        }
        second_targets = {
            c.target for c in _calls_of(second, "Service", "boot")
        }
        assert first_targets == second_targets
        assert "demo.registry.Registry.register" in second_targets

    def test_clear_resolution_cache_does_not_pollute_search_path(
        self, project: dict[str, object]
    ) -> None:
        import sys

        before = list(sys.path)
        _resolve_service(project)
        clear_resolution_cache()
        # The resolver must not permanently leak its roots onto sys.path.
        leaked = [p for p in sys.path if p not in before]
        assert leaked == [], f"resolver leaked search-path entries: {leaked}"


class TestSeparableFromStructuralApi:
    """The new resolution API does not disturb the structural parse_module."""

    def test_structural_api_still_importable_and_callable(self) -> None:
        from lorescribe.astroid_parse import ParsedModule, parse_module

        module = parse_module("class A:\n    def m(self):\n        return 1\n")
        assert isinstance(module, ParsedModule)
        assert [c.name for c in module.classes] == ["A"]
