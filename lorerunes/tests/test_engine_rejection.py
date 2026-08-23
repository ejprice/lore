"""Contract — ``lorerunes.reclassify``, the shared exception-reclassification primitive
(Layer 1 of the two-layer engine-rejection seam, finding #400 / packet-61 Fork I + its
2026-08-23 addendum D2).

RED before the packet-61a-w2 extraction build; authored by ``contract-61a-w2`` (session
``pkt61``) at HEAD ``fb68427``, REVISED per ``docs/design/2026-08-22-packet61-pdp-audit-
rulings.md`` §"Fork I addendum" (D2 — the two-layer seam) + §"Fork I addendum-2" (the
shape-keyed guard + the clone scope).

------------------------------------------------------------------------------
THE TWO-LAYER SEAM (D2). The ruling splits the seam so BOTH the control-flow policy AND the
surreal taxonomy are each ONE thing (else routing-is-not-sharing re-clones the taxonomy):

  * **Layer 1 — ``lorerunes.reclassify`` (THIS file):** a stdlib-only contextmanager,
    parameterised over the exception CLASSES it receives, that applies the classify-and-
    reclassify control flow: re-raise ``passthrough`` FIRST (untouched), then translate a
    ``catch`` into ``make_error()`` chained ``from`` the original. It NEVER names a surreal
    type — ``lorerunes`` depends on nothing but the stdlib.
  * **Layer 2 — ``loremaster.store._txn.wrap_store_rejection`` (pinned in
    ``loremaster/tests/test_engine_rejection_seam.py``):** binds the surreal taxonomy ONCE
    (``passthrough=(SurrealConnectionError, TxnContentionExhaustedError)``,
    ``catch=(SurrealStoreError,)``, ``make_error=lambda: domain_error(context)``) and
    delegates the control flow to ``reclassify``. Every store write-path calls Layer 2.

This file pins Layer 1's SEMANTICS with SYNTHETIC classes that MIRROR the real hierarchy
(``_ConnErr`` / ``_ContentionErr`` SUBCLASS ``_StoreErr``, exactly as the surreal ones
subclass ``SurrealStoreError`` — ``_txn.py:116/120/156``), so the LOAD-BEARING ordering
(re-raise ``passthrough`` BEFORE the ``catch`` translate) is tested where a store is not
needed and where the taxonomy is not baked in.

WHY RED NOW (contract-first): ``lorerunes.reclassify`` does not exist at HEAD ``fb68427``.
The ``_load_reclassify`` gate ``pytest.fail``s CLEANLY (no ImportError at collection, no
mypy-RED static import of an unbuilt symbol — finding #133 idiom), so this file collects +
typechecks clean and every behavioural pin is RED for the RIGHT reason.
"""

from __future__ import annotations

import ast
import importlib
from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest

_SHARED_PACKAGE = "lorerunes"
_RECLASSIFY = "reclassify"


def _load_reclassify() -> Any:
    """Return ``lorerunes.reclassify`` once w2 builds it, else ``pytest.fail`` CLEANLY.

    Reads via ``importlib`` + ``getattr`` (not a static ``from lorerunes import reclassify``)
    so a RED contract naming an unbuilt symbol neither errors at collection nor reddens the
    typecheck gate — the existence requirement rides the RUNTIME test (finding #133 idiom)."""
    package = importlib.import_module(_SHARED_PACKAGE)
    reclassify = getattr(package, _RECLASSIFY, None)
    if reclassify is None:
        pytest.fail(
            f"{_SHARED_PACKAGE}.{_RECLASSIFY} not yet built (packet 61a-w2) — RED until it lands",
            pytrace=False,
        )
    return reclassify


# Synthetic classes mirroring the REAL surreal hierarchy (_txn.py:116/120/156):
# SurrealConnectionError / TxnContentionExhaustedError both SUBCLASS SurrealStoreError.
# The subclassing is the whole point — it is why "catch SurrealStoreError" would swallow
# a connection error unless the passthrough is re-raised FIRST.
class _StoreErr(RuntimeError):
    """Mirrors ``SurrealStoreError`` — the base engine rejection (the ``catch`` set)."""


class _ConnErr(_StoreErr):
    """Mirrors ``SurrealConnectionError`` — a transport fault (a passthrough; SUBCLASS)."""


class _ContentionErr(_StoreErr):
    """Mirrors ``TxnContentionExhaustedError`` — exhausted retry (a passthrough; SUBCLASS)."""


class _DomainErr(RuntimeError):
    """Mirrors a store's domain error (``KeepStoreError`` / ``PrincipalStoreError`` / …)."""


class _UnrelatedErr(Exception):
    """An error OUTSIDE the ``catch`` set — the primitive must NOT touch it."""


_CTX = "could not frob the widget 'w-42': the store rejected it"
_PASSTHROUGH: tuple[type[BaseException], ...] = (_ConnErr, _ContentionErr)
_CATCH: tuple[type[BaseException], ...] = (_StoreErr,)


def _cm(**overrides: Any) -> Any:
    """Build the primitive's context manager with the standard synthetic wiring, allowing a
    per-test override (e.g. an empty ``passthrough``, or a spy ``make_error``)."""
    reclassify = _load_reclassify()
    kwargs: dict[str, Any] = {
        "passthrough": _PASSTHROUGH,
        "catch": _CATCH,
        "make_error": lambda: _DomainErr(_CTX),
    }
    kwargs.update(overrides)
    return reclassify(**kwargs)


# ===========================================================================
# 1. Existence + it is a context manager, with the ruled keyword-only signature
# ===========================================================================


class TestTheHelperExistsAndIsAContextManager:
    def test_reclassify_is_importable_from_lorerunes(self) -> None:
        """D2 Layer 1: the primitive is a ``lorerunes`` symbol (the designated stdlib-only
        shared home), re-exported at package level. RED until the build lands."""
        reclassify = _load_reclassify()
        assert callable(reclassify)

    def test_it_is_usable_as_a_with_statement(self) -> None:
        """The primitive mirrors the existing ``try: … except …`` in-method idiom, so it
        MUST be a context manager (``with reclassify(...):``)."""
        with _cm():
            value = 1 + 1
        assert value == 2

    def test_the_arguments_are_keyword_only(self) -> None:
        """D2 shape: ``reclassify(*, passthrough, catch, make_error)`` — all keyword-only.
        A build with positional params (or the old ``(domain_error_type, context, ...)``
        shape) fails to accept these keywords. Also proves ``catch``/``passthrough`` are
        TUPLES and ``make_error`` a zero-arg callable (the D2 signature)."""
        reclassify = _load_reclassify()
        with reclassify(
            passthrough=_PASSTHROUGH, catch=_CATCH, make_error=lambda: _DomainErr(_CTX)
        ):
            pass


# ===========================================================================
# 2. The happy path — a clean block is untouched, and make_error is NOT called
# ===========================================================================


class TestTheHappyPath:
    def test_no_exception_passes_through_silently(self) -> None:
        ran = False
        with _cm():
            ran = True
        assert ran is True

    def test_make_error_is_not_invoked_on_the_happy_path(self) -> None:
        """``make_error`` is a lazy factory — called ONLY to build the domain error on a
        ``catch``. A build that eagerly evaluated it (or wrapped unconditionally) fails."""
        calls = 0

        def _make() -> _DomainErr:
            nonlocal calls
            calls += 1
            return _DomainErr(_CTX)

        with _cm(make_error=_make):
            pass
        assert calls == 0


# ===========================================================================
# 3. The catch-and-translate — a raw engine rejection becomes make_error()'s result
# ===========================================================================


class TestCatchAndTranslate:
    def test_a_catch_class_is_translated_to_make_errors_result(self) -> None:
        """A ``catch``-class exception is re-raised as ``make_error()``'s result — never a
        raw engine error reaching the consumer (the consumer law). RED against a no-op build
        that let ``_StoreErr`` escape."""
        with pytest.raises(_DomainErr):
            with _cm():
                raise _StoreErr("the engine rejected an ASSERT")

    def test_the_raised_error_is_exactly_make_errors_return(self) -> None:
        """The raised object IS what ``make_error`` returned (identity) — the primitive does
        not construct its own error, it raises the caller's. This is the D2 ``make_error``
        contract; a build that raised some other error fails."""
        sentinel = _DomainErr("the exact instance make_error built")
        with pytest.raises(_DomainErr) as excinfo:
            with _cm(make_error=lambda: sentinel):
                raise _StoreErr("raw engine detail")
        assert excinfo.value is sentinel

    def test_the_from_error_chain_is_preserved(self) -> None:
        """``raise make_error() from error`` — the raw engine error is preserved as
        ``__cause__`` (FR-2 Q2 "chain preserved"; D2 mutation target (i)). A build that
        dropped ``from error`` (bare ``raise`` or ``from None``) fails."""
        original = _StoreErr("the raw engine detail to preserve")
        with pytest.raises(_DomainErr) as excinfo:
            with _cm():
                raise original
        assert excinfo.value.__cause__ is original

    def test_make_error_is_invoked_exactly_once_on_a_catch(self) -> None:
        """``make_error`` is called EXACTLY once (to build the one raised error) on a catch —
        not zero (a build that raised the raw error) and not twice."""
        calls = 0

        def _make() -> _DomainErr:
            nonlocal calls
            calls += 1
            return _DomainErr(_CTX)

        with pytest.raises(_DomainErr):
            with _cm(make_error=_make):
                raise _StoreErr("rejected")
        assert calls == 1

    def test_a_subclass_of_catch_that_is_not_a_passthrough_is_translated(self) -> None:
        """A subclass of a ``catch`` member that is NOT in ``passthrough`` is still
        translated — the translate keys on the ``catch`` hierarchy, not an exact-type match."""

        class _OtherStoreErr(_StoreErr):
            pass

        with pytest.raises(_DomainErr):
            with _cm():
                raise _OtherStoreErr("a new kind of engine rejection")


# ===========================================================================
# 4. THE LOAD-BEARING ORDERING — passthrough re-raised FIRST, before the translate
# ===========================================================================


class TestPassthroughIsReRaisedFirst:
    """⚠ THE LOAD-BEARING PINS (FR-2 Q2 / store ref §3 / D2 mutation target (ii)).
    ``_ConnErr`` / ``_ContentionErr`` SUBCLASS ``_StoreErr`` (a ``catch`` member), exactly as
    the surreal ones subclass ``SurrealStoreError``. A NAIVE build (``except catch:
    translate`` with no ``except passthrough: raise`` FIRST) would TRANSLATE a connection
    error into the domain error — a real regression (a transport fault masqueraded as a
    domain rejection, lost to the retry/lifecycle layer). RED against a catch-all wrong
    build; GREEN with the correct ordering."""

    @pytest.mark.parametrize(
        ("error_factory", "expected"),
        [
            (lambda: _ConnErr("transport fault"), _ConnErr),
            (lambda: _ContentionErr("exhausted contention"), _ContentionErr),
        ],
    )
    def test_a_passthrough_error_propagates_as_itself_not_translated(
        self, error_factory: Callable[[], BaseException], expected: type[BaseException]
    ) -> None:
        with pytest.raises(expected) as excinfo:
            with _cm():
                raise error_factory()
        assert not isinstance(excinfo.value, _DomainErr), (
            f"{expected.__name__} was TRANSLATED to the domain error — passthrough must be "
            "re-raised FIRST (before the catch-and-translate), or a transport fault is lost"
        )

    def test_make_error_is_not_invoked_for_a_passthrough(self) -> None:
        """On a passthrough, ``make_error`` is NOT called at all — the passthrough clause
        re-raises before the translate clause is reached. A build whose ordering was reversed
        would build (and raise) the domain error, calling ``make_error``."""
        calls = 0

        def _make() -> _DomainErr:
            nonlocal calls
            calls += 1
            return _DomainErr(_CTX)

        with pytest.raises(_ConnErr):
            with _cm(make_error=_make):
                raise _ConnErr("transport")
        assert calls == 0

    def test_the_propagated_passthrough_is_the_ORIGINAL_instance(self) -> None:
        """Not merely the right type — the SAME instance, untouched (no re-chaining)."""
        original = _ContentionErr("the exact instance")
        with pytest.raises(_ContentionErr) as excinfo:
            with _cm():
                raise original
        assert excinfo.value is original


# ===========================================================================
# 5. The primitive does NOT over-catch — an unrelated error escapes untouched
# ===========================================================================


class TestUnrelatedErrorsAreNotSwallowed:
    def test_an_error_outside_the_catch_set_propagates_unchanged(self) -> None:
        """An exception OUTSIDE ``catch`` (here ``_UnrelatedErr``) is NOT translated and NOT
        swallowed. This is the anti-bare-Exception pin (catch the engine base SPECIFICALLY,
        never bare ``Exception``). A build that used ``except Exception`` would translate it."""
        with pytest.raises(_UnrelatedErr):
            with _cm():
                raise _UnrelatedErr("a bug unrelated to the store")

    def test_a_KeyError_is_not_translated(self) -> None:
        """A concrete stdlib exception outside ``catch`` — a ``KeyError`` (the SDK's
        in-flight-drop shape, store ref §3) — must escape as itself."""
        with pytest.raises(KeyError):
            with _cm():
                raise KeyError("uuid")


# ===========================================================================
# 6. passthrough / catch are PARAMETERISED — the taxonomy is not baked in (why it is stdlib)
# ===========================================================================


class TestTheTaxonomyIsParameterised:
    def test_with_empty_passthrough_a_catch_subclass_is_translated(self) -> None:
        """With ``passthrough=()`` there is NO passthrough — even a ``_ConnErr`` (a ``catch``
        subclass) is translated. This proves the passthrough set is PARAMETERISED (supplied
        by the caller), not hardcoded into the stdlib primitive — the whole reason it can live
        in stdlib-only ``lorerunes`` (§module docstring). Layer 2 (``wrap_store_rejection``)
        supplies the real surreal passthrough."""
        with pytest.raises(_DomainErr):
            with _cm(passthrough=()):
                raise _ConnErr("no passthrough configured → translated")

    def test_catch_is_honoured_as_supplied(self) -> None:
        """``catch`` is the caller's set: a class NOT in ``catch`` is not translated even if
        it is an engine-ish error. Here ``catch=(_ConnErr,)`` only, so a plain ``_StoreErr``
        (not a ``_ConnErr``) escapes untranslated — proving the primitive honours the supplied
        ``catch`` rather than a baked-in base."""
        with pytest.raises(_StoreErr) as excinfo:
            with _cm(catch=(_ConnErr,), passthrough=()):
                raise _StoreErr("not in the caller's catch set")
        assert not isinstance(excinfo.value, _DomainErr)


# ===========================================================================
# 7. The new module is stdlib-only (confirms the existing rglob guard covers it)
# ===========================================================================


class TestTheNewModuleImportsNoSibling:
    """The primitive's OWN module imports nothing but the stdlib + ``lorerunes`` itself — a
    self-contained confirmation living WITH the helper. The repo-wide
    ``test_secret_typing.py::…depends_on_nothing_but_the_stdlib`` already enforces this over
    every ``lorerunes/*.py`` via ``rglob`` (so the new module is covered there by
    construction too); this beside-the-helper pin reddens a purity break in the same file
    that introduced it."""

    def test_the_module_imports_only_stdlib_and_lorerunes(self) -> None:
        import sys

        reclassify = _load_reclassify()
        module = importlib.import_module(reclassify.__module__)
        source_path = Path(module.__file__)  # type: ignore[arg-type]
        tree = ast.parse(source_path.read_text(encoding="utf-8"), filename=str(source_path))
        offenders: list[str] = []
        allowed = set(sys.stdlib_module_names) | {_SHARED_PACKAGE}
        for node in ast.walk(tree):
            roots: set[str] = set()
            if isinstance(node, ast.Import):
                roots = {alias.name.split(".")[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
                roots = {node.module.split(".")[0]}
            else:
                continue
            for name in roots - allowed:
                offenders.append(f"{source_path.name}:{node.lineno} imports {name}")
        assert not offenders, (
            f"{reclassify.__module__} must import the stdlib only (lorerunes is a stdlib-only "
            f"leaf — it may not drag loremaster/loresigil/lorescribe): {offenders}"
        )


# ===========================================================================
# 8. Package re-export — the __init__ names the new symbol
# ===========================================================================


class TestPackageReExport:
    def test_reclassify_is_re_exported_and_listed_in_dunder_all(self) -> None:
        """Register the new symbol at the package boundary: ``from lorerunes import
        reclassify`` resolves AND ``reclassify`` is in ``lorerunes.__all__`` (the house
        idiom). RED until the __init__ re-export lands."""
        package = importlib.import_module(_SHARED_PACKAGE)
        assert hasattr(package, _RECLASSIFY), (
            f"{_SHARED_PACKAGE}.__init__ must re-export {_RECLASSIFY} (D2 registration)"
        )
        dunder_all = getattr(package, "__all__", ())
        assert _RECLASSIFY in dunder_all, (
            f"{_RECLASSIFY} must be listed in {_SHARED_PACKAGE}.__all__ (the house idiom)"
        )
