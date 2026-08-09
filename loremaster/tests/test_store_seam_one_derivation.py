"""Contract: the ONE store-seam derivation (finding #279).

RED before the #279 one-derivation build; authored 2026-08-09 at HEAD ``e1dfa14`` by
``contract-f`` (session ``2026-08-09-fix-344-345``). Design: ``INSTRUMENT F`` / fork ``F5``
in ``docs/plans/v2/design/2026-08-09-defect-class-prevention.md``.

------------------------------------------------------------------------------
THE DEFECT, stated as the wrong build rather than the virtue.

The policy *"what is a module's store-seam set?"* is DERIVED TWICE today, and the two copies
are free to disagree (finding #279):

* ``scripts/forgery_door_sweep.store_seams`` walks ``vars(loremaster.store._txn)`` for PUBLIC
  coroutines that accept a caller-supplied ``statement`` — the DOOR subset
  ({``run_query``, ``execute_transaction``, ``execute_read_transaction``});
* ``loremaster/tests/test_blocks_edge._degrade_every_STORE_seam`` walks
  ``vars(loremaster.tasks)`` for coroutines DEFINED in ``loremaster.store._txn`` — the WIDE
  set as ``loremaster.tasks`` binds it ({those three PLUS ``bootstrap_session``}).

Two walks, two predicates. A 4th public coroutine added to ``_txn`` would be classified by
whichever walk happens to see it, and nothing asserts the two agree. This is the ONE
IMPLEMENTATION law, one level up (CLAUDE.md "ONE IMPLEMENTATION — a pattern to clone is a
defect to clone"): *if two call sites need the same POLICY, it is a FUNCTION THEY CALL.*

------------------------------------------------------------------------------
THE PROPERTY THIS FILE PINS (operator ruling F5 — placement (b) confirmed in the spawn brief).

A single PRODUCTION helper ``loremaster.store._txn_coroutines`` is the ONE walk. It exposes:

* the WIDE superset — every coroutine function defined in ``loremaster.store._txn`` — and
* the DOOR subset — the narrower public + ``statement``-accepting filter of that same walk
  (``forgery_door_sweep.store_seams``).

BOTH callers (``forgery_door_sweep.store_seams`` / ``seam_bindings`` and
``test_blocks_edge._degrade_every_STORE_seam``) ROUTE through it — they do not keep private
copies. ``seam_bindings`` gains a ``seams=`` argument so bindings can be built from EITHER
set; ``_degrade_every_STORE_seam`` derives from the WIDE superset via
``seam_bindings(package="loremaster", seams=<superset>)``.

------------------------------------------------------------------------------
WHY THE MUTATION PROOF IS THE LOAD-BEARING TEST, and consistency is not enough.

CLAUDE.md: *"PROVE SHARING BY MUTATION, never by inspection… ROUTING IS NOT SHARING."* The
consistency pins below (the door subset equals a filter of the core; WIDE ⊇ DOOR) pass
EQUALLY for one shared helper AND for two private copies that merely AGREE today — they
cannot tell DRY from looks-DRY. Only ``TestSharingProvenByMutation`` can: it mutates the
shared core (drops a seam, everywhere the helper is referenced — by identity, exactly as
``seam_bindings`` finds its own bindings) and asserts BOTH callers change. A caller that
stays green under the mutation never read the shared helper — a private copy wearing the
shared name — and that is the exact wrong build these pins exist to fail.

The discriminator itself carries a positive control (``TestTheMutationProofDiscriminates``,
CLAUDE.md "a probe needs a control"): it constructs a router and a private clone and shows
the mutation technique moves the one and not the other, so a green mutation pin is not a
green light with a filename.
"""

from __future__ import annotations

import contextlib
import inspect
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import pytest

# ``scripts`` is not a package; make ``forgery_door_sweep`` importable — the idiom
# ``scripts/test_forgery_door_sweep.py`` already uses. ``loremaster/tests`` is already on
# ``sys.path`` via that directory's ``conftest.py``, so ``test_blocks_edge`` imports as a
# plain top-level module (done lazily below, since it is a 9k-line module).
_SCRIPTS_DIR = str(Path(__file__).resolve().parent.parent.parent / "scripts")
if _SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, _SCRIPTS_DIR)

import forgery_door_sweep as fds  # type: ignore[import-not-found]  # noqa: E402  (scripts/ is not a package)

# The store-seam set, split the way ``_txn.py`` actually defines it (verified at HEAD
# ``e1dfa14``: the public coroutines of ``loremaster.store._txn`` are exactly these five;
# ``run_query`` / ``execute_transaction`` / ``execute_read_transaction`` take a ``statement``
# parameter, ``retry_on_conflict`` / ``bootstrap_session`` do not).
_DOOR_SEAMS = frozenset({"run_query", "execute_transaction", "execute_read_transaction"})
_WIDE_ONLY_PUBLIC_SEAMS = frozenset({"retry_on_conflict", "bootstrap_session"})
_ALL_PUBLIC_SEAMS = _DOOR_SEAMS | _WIDE_ONLY_PUBLIC_SEAMS

# The single WIDE-set element ``_degrade_every_STORE_seam`` sees that the door filter removes:
# ``loremaster.tasks`` binds ``bootstrap_session`` (but not ``retry_on_conflict``), so the
# degrade derivation's set is the three doors PLUS this one.
_DEGRADE_WIDE_ONLY_SEAM = "bootstrap_session"


# ---------------------------------------------------------------------------
# Loaders — deliberately lazy so the RED state is a clean per-test failure
# (the helper does not exist yet) rather than a whole-file collection error.
# ---------------------------------------------------------------------------


def _load_core() -> Any:
    """The ONE derivation, read from its operator-ruled home ``loremaster.store``.

    RED until the build lands: ``loremaster.store._txn_coroutines`` does not exist at HEAD
    ``e1dfa14`` (measured), so this raises ``AttributeError``. Read via ``getattr`` rather
    than a static ``from loremaster.store import _txn_coroutines`` for ONE reason: a RED
    contract that names an unbuilt symbol statically turns the whole typecheck gate RED, and
    this contract's requirement ("the symbol must exist") is carried by the RUNTIME test, so
    mypy need not also carry it. ``getattr(pkg, name)`` is the exact existence check a
    ``from pkg import name`` performs, so the builder exposing it at the package satisfies
    both.
    """
    import loremaster.store as store_package  # noqa: PLC0415

    return getattr(store_package, "_txn_coroutines")


def _load_degrade() -> Callable[..., tuple[str, ...]]:
    """``test_blocks_edge._degrade_every_STORE_seam`` — the WIDE-set caller under test."""
    from test_blocks_edge import _degrade_every_STORE_seam  # noqa: PLC0415

    return _degrade_every_STORE_seam


def _inert_seam_replacement(*_args: Any, **_kwargs: Any) -> Any:
    """The stand-in ``_degrade_every_STORE_seam`` installs over each seam.

    It is only ever SET as a module attribute by the degrade helper, never called, in these
    derivation tests — so it raises if anything actually invokes it, turning a surprise call
    into a loud failure instead of silent nonsense.
    """
    raise AssertionError("the inert seam replacement must never be invoked in a derivation test")


# ---------------------------------------------------------------------------
# The mutation machinery (shared by the real proof AND its positive control)
# ---------------------------------------------------------------------------


@contextlib.contextmanager
def _rebind_everywhere(real: object, fake: object) -> Iterator[None]:
    """Rebind every module attribute that IS ``real`` to ``fake`` for the duration.

    Found BY IDENTITY across ``sys.modules`` — the same technique ``seam_bindings`` uses to
    find seam bindings — so the mutation reaches a caller whether it imported the helper at
    MODULE level (a rebindable global) or re-imports it per call (which re-reads the patched
    canonical ``loremaster.store`` attribute, itself one of the rebound sites). A caller that
    references the helper NOWHERE is unreached by both — which is precisely the private copy
    the mutation proof must catch.
    """
    saved: list[tuple[Any, str]] = []
    for module in list(sys.modules.values()):
        try:
            attributes = list(vars(module).items())
        except TypeError:  # a None placeholder or a module without an ordinary __dict__
            continue
        for attribute, value in attributes:
            if value is real:
                saved.append((module, attribute))
    for module, attribute in saved:
        setattr(module, attribute, fake)
    try:
        yield
    finally:
        for module, attribute in saved:
            setattr(module, attribute, real)


@contextlib.contextmanager
def _core_dropping(seam_name: str) -> Iterator[None]:
    """Make the shared core drop ``seam_name`` from its returned set, everywhere it is read.

    RED until the helper exists (the import below ``ImportError``s). Once it exists, this
    carries its OWN evidence that the mutation LANDED (CLAUDE.md #194 — a mutation proof needs
    proof the mutation took) before any caller is observed: it re-reads the canonical helper
    and asserts the seam is gone.
    """
    import loremaster.store as store_package  # noqa: PLC0415

    real_core = getattr(store_package, "_txn_coroutines")
    real_result = real_core()
    assert seam_name in real_result, (
        f"{seam_name!r} is not in the shared core to begin with, so dropping it mutates "
        f"nothing and this proof would pass vacuously"
    )
    mutated = {name: fn for name, fn in real_result.items() if name != seam_name}

    def fake_core() -> dict[str, Any]:
        return dict(mutated)

    with _rebind_everywhere(real_core, fake_core):
        core_after = getattr(store_package, "_txn_coroutines")
        assert seam_name not in core_after(), (
            "the core mutation did not land at loremaster.store._txn_coroutines — the proof "
            "below would measure nothing"
        )
        yield


def _degrade_derivation_includes(seam_name: str) -> bool:
    """Whether the degrade caller's derived seam set contains ``seam_name`` (healthy path)."""
    degrade = _load_degrade()
    with pytest.MonkeyPatch.context() as monkeypatch:
        return seam_name in degrade(monkeypatch, _inert_seam_replacement)


def _degrade_reflects_core_drop(seam_name: str) -> bool:
    """Whether dropping ``seam_name`` from the shared core changes the degrade derivation.

    Two ways a caller that ROUTES through the core reflects the drop, both accepted:
    ``_degrade_every_STORE_seam``'s own fail-closed guard fires (its ``assert
    "<seam>" in patched`` — an ``AssertionError``), OR its returned set simply no longer
    carries the seam. A PRIVATE COPY does neither: it returns the seam, unchanged — which is
    the ``False`` this predicate reports so the pin fails it.
    """
    degrade = _load_degrade()
    with pytest.MonkeyPatch.context() as monkeypatch, _core_dropping(seam_name):
        try:
            patched = degrade(monkeypatch, _inert_seam_replacement)
        except AssertionError:
            return True
        return seam_name not in patched


# ---------------------------------------------------------------------------
# Live seam surfaces — the ∀-drop (LEG B, section 4) ranges over THESE, re-derived
# from production truth every collection, NEVER the module-level hand-lists above.
#
# ⚠ META-RECURSION (design §9.1): a ∀-mutation whose reach is a fixture constant is a
# hand-list wearing a loop — the very class this contract is about, one level up. So
# the parametrised seam set is DERIVED here from the same production source the shipped
# helper derives from (``vars(loremaster.store._txn)`` for doors; what
# ``loremaster.tasks`` actually binds for the wide set). Section 6's coverage pins tie
# each surface back to the live core (``_load_core``), so a surface that drifts from the
# core reddens rather than silently narrowing the ∀ — the reach is a checked variable.
#
# These are DELIBERATE INDEPENDENT ORACLES (the same idiom as
# ``test_store_seams_is_exactly_the_public_statement_filter_of_the_core`` recomputing
# ``expected_doors``): re-implementing the filter here is what lets the ∀ reach be
# checked against BOTH the subject and the core — it is a test oracle, not a third
# production copy of the derivation. They read production truth that EXISTS at HEAD
# (``_txn`` / ``loremaster.tasks``), so the parametrised tests COLLECT cleanly before
# the build while their bodies stay RED (the core helper they mutate does not exist).
# ---------------------------------------------------------------------------


def _live_door_surface() -> frozenset[str]:
    """The DOOR seam set — public + ``statement``-bearing coroutines defined in ``_txn``.

    The reach of the ``store_seams`` / ``seam_bindings`` ∀-drop. Derived live so a 4th
    door added to ``_txn`` grows the parametrisation automatically.
    """
    from loremaster.store import _txn  # noqa: PLC0415

    return frozenset(
        name
        for name, fn in vars(_txn).items()
        if not name.startswith("_")
        and inspect.iscoroutinefunction(fn)
        and getattr(fn, "__module__", None) == fds.SEAM_MODULE
        and "statement" in inspect.signature(fn).parameters
    )


def _live_degrade_wide_surface() -> frozenset[str]:
    """The WIDE seam set ``_degrade_every_STORE_seam`` must degrade — every coroutine
    defined in ``_txn`` that ``loremaster.tasks`` binds.

    The reach of the ``_degrade`` ∀-drop. Includes ``bootstrap_session`` (a WIDE-only
    seam — dropping it must still move the derivation, proving the WIDE route
    specifically) and excludes ``retry_on_conflict`` (``loremaster.tasks`` does not bind
    it). Derived live so a 4th seam bound in ``loremaster.tasks`` grows the ∀.
    """
    import loremaster.tasks as tasks_module  # noqa: PLC0415

    return frozenset(
        name
        for name, fn in vars(tasks_module).items()
        if inspect.iscoroutinefunction(fn) and getattr(fn, "__module__", None) == fds.SEAM_MODULE
    )


# ===========================================================================
# 1. The ONE derivation exists, and it is the WIDE superset
# ===========================================================================


class TestTheOneDerivationExistsAndIsWide:
    """Kills: no helper at all; a helper that is the DOOR subset (not the superset); a helper
    that walks every NAME in ``_txn`` rather than its coroutines."""

    def test_the_helper_is_importable_from_loremaster_store(self) -> None:
        """Operator ruling F5: the ONE derivation is a production ``loremaster.store`` helper
        both callers import — not a ``scripts`` symbol and not a ``lorerunes`` primitive
        (``_txn_coroutines`` introspects production ``_txn``, so it cannot be stdlib-only)."""
        core = _load_core()
        assert callable(core)

    def test_the_core_returns_a_non_empty_mapping_of_txn_coroutines(self) -> None:
        """Every value is a coroutine defined in ``_txn``; the public seams are all present;
        empty is a broken derivation, never a clean tree (fail closed)."""
        core = _load_core()()
        assert isinstance(core, dict) and core, "the core must return a non-empty mapping"
        missing = _ALL_PUBLIC_SEAMS - set(core)
        assert not missing, f"the WIDE core is missing public store seams: {sorted(missing)}"
        for name, fn in core.items():
            assert inspect.iscoroutinefunction(fn), f"core member {name!r} is not a coroutine"
            assert getattr(fn, "__module__", None) == fds.SEAM_MODULE, (
                f"core member {name!r} is not defined in {fds.SEAM_MODULE}"
            )

    def test_the_core_is_the_wide_set_not_the_door_subset(self) -> None:
        """``bootstrap_session`` / ``retry_on_conflict`` are in the WIDE core yet are NOT
        doors — the exact WIDE ⊋ DOOR distinction a build that returned only doors would
        collapse."""
        core = set(_load_core()())
        doors = set(fds.store_seams())
        assert _WIDE_ONLY_PUBLIC_SEAMS <= core, (
            f"the WIDE core must contain {sorted(_WIDE_ONLY_PUBLIC_SEAMS)}; "
            f"missing {sorted(_WIDE_ONLY_PUBLIC_SEAMS - core)}"
        )
        assert not (_WIDE_ONLY_PUBLIC_SEAMS & doors), (
            f"{sorted(_WIDE_ONLY_PUBLIC_SEAMS & doors)} must not be in the DOOR subset"
        )

    def test_the_core_holds_coroutines_only_not_every_txn_name(self) -> None:
        """A build that walked ``vars(_txn)`` without ``iscoroutinefunction`` would sweep in
        ``compose`` / ``signin_credentials`` / ``is_connection_error`` — plain functions."""
        core = set(_load_core()())
        for non_coroutine in ("compose", "signin_credentials", "is_connection_error"):
            assert non_coroutine not in core, (
                f"{non_coroutine!r} is not a coroutine and must not be in the seam core"
            )


# ===========================================================================
# 2. The DOOR subset is a filter of the ONE walk (consistency — not yet sharing)
# ===========================================================================


class TestTheDoorSubsetIsDerivedFromTheCore:
    """Kills: a door subset that re-walks ``_txn`` independently of the core. NOTE these are
    CONSISTENCY pins — they pass for two agreeing private copies too; SHARING is proven only
    by ``TestSharingProvenByMutation`` below."""

    def test_store_seams_is_exactly_the_public_statement_filter_of_the_core(self) -> None:
        core = _load_core()()
        expected_doors = {
            name
            for name, fn in core.items()
            if not name.startswith("_") and "statement" in inspect.signature(fn).parameters
        }
        doors = fds.store_seams()
        assert set(doors) == expected_doors, (
            f"the door subset {sorted(doors)} is not the public+statement filter of the "
            f"core {sorted(expected_doors)}"
        )
        for name in doors:
            assert doors[name] is core[name], (
                f"door {name!r} is not the SAME function object as the core's — the subset "
                f"was re-derived, not filtered from the one walk"
            )

    def test_the_door_subset_is_contained_in_the_wide_set(self) -> None:
        core = set(_load_core()())
        assert set(fds.store_seams()) <= core, "the DOOR subset must be contained in the WIDE core"

    def test_the_door_subset_is_the_known_three_doors(self) -> None:
        """Oracle for the door set, independent of the core (a positive control: it stays
        green across the refactor, so a build that silently changed the doors is caught)."""
        assert set(fds.store_seams()) == set(_DOOR_SEAMS)


# ===========================================================================
# 3. seam_bindings can build from EITHER set (the mechanism _degrade uses)
# ===========================================================================


class TestSeamBindingsCanBuildFromEitherSet:
    """Kills: a ``seam_bindings`` that cannot be built over the WIDE superset, so
    ``_degrade_every_STORE_seam`` has no shared route to derive its wider set through."""

    def test_seam_bindings_accepts_a_seams_argument(self) -> None:
        """RED now for the RIGHT reason: ``seam_bindings`` has no ``seams=`` parameter at HEAD
        (measured ``TypeError``). Uses the existing ``store_seams()`` as the seam set so the
        ONLY thing missing now is the argument itself — the capability is pinned independent
        of the new core helper."""
        import loremaster.tasks  # noqa: F401, PLC0415  (a module that binds the door seams)

        door_subset = fds.store_seams()
        bindings = fds.seam_bindings(package="loremaster", seams=door_subset)
        assert bindings, "seam_bindings over the given seam set found no bindings"

    def test_wide_bindings_include_bootstrap_in_tasks_but_door_bindings_do_not(self) -> None:
        """With the WIDE superset, ``bootstrap_session``'s binding in ``loremaster.tasks`` is
        found; with the default DOOR subset it is not — and both agree on a genuine door."""
        import loremaster.tasks  # noqa: F401, PLC0415  (ensure its bindings are visible to the scan)

        core = _load_core()()
        wide = fds.seam_bindings(package="loremaster", seams=core)
        door = fds.seam_bindings(package="loremaster")

        def bound_in_tasks(bindings: tuple[Any, ...], seam: str) -> bool:
            return any(
                binding.seam_name == seam and binding.module_name == "loremaster.tasks"
                for binding in bindings
            )

        assert bound_in_tasks(wide, _DEGRADE_WIDE_ONLY_SEAM), (
            f"the WIDE bindings must include {_DEGRADE_WIDE_ONLY_SEAM!r} in loremaster.tasks"
        )
        assert not bound_in_tasks(door, _DEGRADE_WIDE_ONLY_SEAM), (
            f"the DOOR bindings must NOT include {_DEGRADE_WIDE_ONLY_SEAM!r}"
        )
        assert bound_in_tasks(wide, "run_query") and bound_in_tasks(door, "run_query"), (
            "both binding sets must agree on a genuine door (run_query)"
        )


# ===========================================================================
# 4. SHARING proven by MUTATION — the load-bearing discriminator
# ===========================================================================


class TestSharingProvenByMutation:
    """THE test that distinguishes DRY from looks-DRY — ∀ over the live seam surface.

    Each pin: a positive control on the HEALTHY core (the seam is present), then the
    mutation (the seam is dropped from the shared core) and the assertion that the caller
    REFLECTS it. A private copy that ignores the core stays green under the mutation → the
    pin fails it. RED now (the shared core to mutate does not exist).

    ⚠ Parametrised over EVERY door / EVERY wide seam (``_live_door_surface`` /
    ``_live_degrade_wide_surface``), not just ``run_query``. A single-seam drop is defeated
    by a build that ROUTES the one dropped seam through the shared core and keeps PRIVATE
    hardcoded copies of the rest (adversary-f WB7/WB8: route ``run_query``, hardcode
    ``execute_transaction`` / ``execute_read_transaction``) — the undropped seams are never
    tested for routing, so ``_degrade``'s WB8 hybrid passed the whole contract with NO
    consistency backstop. The ∀ drops EACH seam in turn, so the private copy of ANY seam
    reddens its own drop. The reach is the live surface, pinned ``== live core`` by
    ``TestTheMutationSurfaceIsLiveDerivedAndComplete`` (section 6), so growing the surface
    grows this ∀ or reddens a coverage pin — the reach is a checked variable, not a hidden
    constant (design §9.1 IDIOM 1 LEG B).
    """

    @pytest.mark.parametrize("door", sorted(_live_door_surface()))
    def test_dropping_ANY_door_from_the_core_reddens_store_seams(self, door: str) -> None:
        assert door in fds.store_seams(), f"healthy positive control: {door!r} is a door"
        with _core_dropping(door):
            assert door not in fds.store_seams(), (
                f"store_seams did not reflect dropping {door!r} from the shared core — it "
                f"keeps a private copy of the walk for this door (routing is not sharing)"
            )

    @pytest.mark.parametrize("door", sorted(_live_door_surface()))
    def test_dropping_ANY_door_from_the_core_reddens_seam_bindings(self, door: str) -> None:
        def has_binding(seam: str) -> bool:
            return any(binding.seam_name == seam for binding in fds.seam_bindings())

        assert has_binding(door), f"healthy positive control: {door!r} is bound"
        with _core_dropping(door):
            assert not has_binding(door), (
                f"seam_bindings' default set did not reflect dropping {door!r} from the "
                f"shared core"
            )

    @pytest.mark.parametrize("seam", sorted(_live_degrade_wide_surface()))
    def test_dropping_ANY_wide_seam_from_the_core_reddens_the_degrade_derivation(
        self, seam: str
    ) -> None:
        """∀ over the WIDE set (the doors PLUS ``bootstrap_session``): ``_degrade`` must
        route through the WIDE core for EVERY seam it degrades, not just the one the old
        proof dropped. ``bootstrap_session`` in the set proves the WIDE route specifically
        (dropping a WIDE-only seam must still move the derivation); the other doors close
        WB8 (route ``run_query``+``bootstrap_session``, hardcode the rest)."""
        assert _degrade_derivation_includes(seam), (
            f"healthy positive control: {seam!r} is in the degrade derivation"
        )
        assert _degrade_reflects_core_drop(seam), (
            f"_degrade_every_STORE_seam did not reflect dropping {seam!r} from the shared "
            f"core — its wide set keeps a private copy of the walk for this seam"
        )


# ===========================================================================
# 5. Positive control ON THE PROBE — the mutation proof actually discriminates
# ===========================================================================


class TestTheMutationProofDiscriminates:
    """CLAUDE.md "a probe needs a control": prove the mutation technique above actually tells
    a router from a clone, independent of the real build (so this class is GREEN now and
    after). A mutation pin that could not fail a private copy would be decoration."""

    def test_the_mutation_technique_moves_a_router_and_not_a_private_clone(self) -> None:
        import types

        def real_core() -> dict[str, Any]:
            return {"run_query": _sentinel_a, "bootstrap_session": _sentinel_b}

        _sentinel_a, _sentinel_b = object(), object()
        probe_module = types.ModuleType("_seam_derivation_probe_control")
        setattr(probe_module, "shared_core", real_core)  # a module-level reference, like a caller's
        sys.modules[probe_module.__name__] = probe_module
        try:
            def router() -> set[str]:
                return set(getattr(probe_module, "shared_core")())  # reads the ref at call time

            frozen_clone = set(real_core())

            def private_clone() -> set[str]:
                return set(frozen_clone)  # a private copy — never re-reads the shared core

            assert router() == private_clone(), "baseline: both agree before the mutation"

            def dropped_core() -> dict[str, Any]:
                return {"bootstrap_session": _sentinel_b}

            with _rebind_everywhere(real_core, dropped_core):
                assert "run_query" not in router(), (
                    "the router must REFLECT the mutation — the technique is broken otherwise"
                )
                assert "run_query" in private_clone(), (
                    "the private clone must NOT reflect the mutation — so the sharing pins can "
                    "fail it; if this fires, the mutation proof cannot tell DRY from looks-DRY"
                )
        finally:
            del sys.modules[probe_module.__name__]


# ===========================================================================
# 6. The ∀-drop reach is DERIVED and COMPLETE — coverage as a checked variable
#    (design §9.1 IDIOM 1 LEG A + the meta-recursion guard)
# ===========================================================================


class TestTheMutationSurfaceIsLiveDerivedAndComplete:
    """Makes section 4's ∀-drop reach a CHECKED VARIABLE, and adds the ``_degrade``
    LEG-A set-consistency backstop adversary-f found missing.

    WB8 was the BLOCKER precisely because ``_degrade`` had NO consistency pin — only
    per-seam drops of ``run_query`` / ``bootstrap_session`` — so a build that reports the
    right set today by hardcoding it (routing 2 seams, hardcoding 2) was exempt from the
    sharing proof silently and permanently, and would miss a future 4th seam (re-opening
    #279 on the ``_degrade`` axis). LEG B (section 4) catches WB8 today; these LEG-A pins
    catch the divergence a future seam would introduce WITHOUT anyone dropping anything.

    ⚠ META-RECURSION (design §9.1): section 4 ranges over ``_live_door_surface`` /
    ``_live_degrade_wide_surface``. The first two pins here assert each surface EQUALS the
    live core-derived set, so a seam added to ``_txn`` (or bound in ``loremaster.tasks``)
    either grows the ∀ automatically OR reddens a coverage pin — the reach can never
    silently narrow to a hidden constant. RED now (the core does not exist)."""

    def test_the_door_drop_surface_equals_the_live_core_door_filter(self) -> None:
        """The ``store_seams`` / ``seam_bindings`` ∀ reach == the public + ``statement``
        filter of the live core. If they drift, the ∀ is exercising the wrong set."""
        core = _load_core()()
        core_doors = frozenset(
            name
            for name, fn in core.items()
            if not name.startswith("_") and "statement" in inspect.signature(fn).parameters
        )
        assert _live_door_surface() == core_doors, (
            f"the door ∀-drop reach {sorted(_live_door_surface())} has drifted from the live "
            f"core's door filter {sorted(core_doors)} — the parametrised set is no longer the "
            f"surface the shipped helper derives"
        )

    def test_the_degrade_wide_surface_equals_the_live_core_bound_in_tasks(self) -> None:
        """The ``_degrade`` ∀ reach == the wide-core seams ``loremaster.tasks`` binds,
        derived through the shipped ``seam_bindings(seams=core)`` path (not the oracle's own
        walk), so the two derivations are pinned to agree."""
        import loremaster.tasks  # noqa: F401, PLC0415  (ensure its bindings are visible to the scan)

        core = _load_core()()
        bound_in_tasks = frozenset(
            binding.seam_name
            for binding in fds.seam_bindings(package="loremaster", seams=core)
            if binding.module_name == "loremaster.tasks"
        )
        assert _live_degrade_wide_surface() == bound_in_tasks, (
            f"the degrade ∀-drop reach {sorted(_live_degrade_wide_surface())} has drifted "
            f"from the wide core bound in loremaster.tasks {sorted(bound_in_tasks)}"
        )

    def test_the_degrade_set_is_exactly_the_wide_core_bound_in_tasks(self) -> None:
        """LEG A — the missing backstop (adversary-f). ``_degrade``'s OWN derived set equals
        the wide core bound in ``loremaster.tasks``, recomputed live each run. Catches a
        ``_degrade`` whose set diverges from the core WITHOUT dropping anything — e.g. a
        future 4th seam the two derivations disagree about (the exact #279 defect on the
        ``_degrade`` side), which the per-seam drops alone would miss until someone added the
        seam AND remembered to parametrise over it."""
        import loremaster.tasks  # noqa: F401, PLC0415  (ensure its bindings are visible to the scan)

        core = _load_core()()
        expected = frozenset(
            binding.seam_name
            for binding in fds.seam_bindings(package="loremaster", seams=core)
            if binding.module_name == "loremaster.tasks"
        )
        with pytest.MonkeyPatch.context() as monkeypatch:
            actual = frozenset(_load_degrade()(monkeypatch, _inert_seam_replacement))
        assert actual == expected, (
            f"_degrade_every_STORE_seam degraded {sorted(actual)} but the wide core bound in "
            f"loremaster.tasks is {sorted(expected)} — the two derivations disagree (#279)"
        )
