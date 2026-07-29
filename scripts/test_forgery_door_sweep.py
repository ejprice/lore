"""Contract for ``scripts/forgery_door_sweep.py`` (finding #278).

**WHAT THIS FILE IS GUARDING AGAINST, stated as the wrong build rather than as a virtue.**
A door sweep is an instrument whose failure mode is *reporting clean*. Four wrong builds of
it all print the same reassuring last line:

1. it patches NOTHING, so no call is ever faulted and every door "fails loud";
2. it derives an EMPTY seam set, so there are no doors to fail;
3. it faults a door the entry point swallows and calls the swallow a pass;
4. it derives doors from a NAME LIST, so a door nobody listed is invisible — which is
   exactly the state ``BACKFILL_FAILURE_DOORS`` was in when a third door existed.

Every test below exists to kill one of those. The load-bearing ones are the DISCRIMINATION
tests: a subject that swallows its fault must make the sweep FAIL. A sweep that cannot be
shown failing is not a sweep, it is a green light with a filename.

⚠ The live legs need the TEST SurrealDB (``ws://127.0.0.1:18000``, ``LORE_TEST_SURREAL_URL``
overrides) and create/REMOVE a throwaway database per leg. They are LOUD when the server is
unreachable, never skipped — a green suite must mean the sweep really ran against an engine.
"""

from __future__ import annotations

import inspect
import os
import sys
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from types import ModuleType
from typing import Any

import pytest

# ``scripts`` is not a package (and this module's target is a CLI, not an installed
# package), so make that directory importable before importing it — the idiom
# ``test_token_survey.py`` already uses.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import forgery_door_sweep as fds  # noqa: E402  (path insert must precede the import)

_FAKE_PACKAGE = "forgery_door_sweep_fake_seam_package"


# ---------------------------------------------------------------------------
# The DERIVATION, tested as a property — never against a hardcoded name set
# ---------------------------------------------------------------------------


def _public_seam_coroutines() -> dict[str, Any]:
    """Every public coroutine DEFINED in the seam module, independent of this script."""
    from loremaster.store import _txn

    return {
        name: value
        for name, value in vars(_txn).items()
        if not name.startswith("_")
        and inspect.iscoroutinefunction(value)
        and getattr(value, "__module__", None) == fds.SEAM_MODULE
    }


class TestTheSeamSetIsDERIVEDAndPARTITIONSTheSeamModule:
    """The derivation must be a PROPERTY over the seam module, not a list someone typed.

    So these tests never name ``run_query`` or ``execute_transaction``. They assert the
    partition holds: swept ⟺ takes a caller statement, and swept ∪ not-swept is exactly the
    module's public coroutine surface. A seam added tomorrow joins one side or the other and
    these stay green; a derivation replaced by a hand-list goes red the day the module grows.
    """

    def test_every_swept_seam_takes_a_CALLER_SUPPLIED_statement(self) -> None:
        seams = fds.store_seams()
        assert seams, (
            "the store-seam derivation is EMPTY, so every entry point trivially has no "
            "doors and every sweep certifies nothing"
        )
        for name, function in seams.items():
            parameters = inspect.signature(function).parameters
            assert fds._CALLER_STATEMENT_PARAMETER in parameters, (
                f"{name} is swept as a door but takes no "
                f"{fds._CALLER_STATEMENT_PARAMETER!r} parameter, so the derivation is no "
                f"longer the property it claims to be"
            )

    def test_every_EXCLUDED_public_coroutine_takes_no_caller_statement(self) -> None:
        for name in fds.public_coroutines_not_swept():
            parameters = inspect.signature(_public_seam_coroutines()[name]).parameters
            assert fds._CALLER_STATEMENT_PARAMETER not in parameters, (
                f"{name} is reported as NOT SWEPT while it does take a caller statement — "
                f"a door is being excluded for a reason the code does not hold"
            )

    def test_the_swept_and_NOT_SWEPT_sets_PARTITION_the_modules_public_coroutines(
        self,
    ) -> None:
        """⛔ The anti-silence pin: a public coroutine in NEITHER set is a door nobody is
        told about — the shape of every defeat in this repo's instrument-lesson table."""
        swept = set(fds.store_seams())
        excluded = set(fds.public_coroutines_not_swept())
        assert swept & excluded == set(), f"a seam is both swept and excluded: {swept & excluded}"
        assert swept | excluded == set(_public_seam_coroutines()), (
            f"the sweep's two sets do not cover the seam module's public coroutines. "
            f"unaccounted={sorted(set(_public_seam_coroutines()) - swept - excluded)}"
        )

    def test_the_DRIVER_is_not_a_door(self) -> None:
        """⛔ ``retry_on_conflict`` RUNS every door, so counting it would double every door
        and the derived count would be 2N. Named here because the consequence is a wrong
        NUMBER rather than an error, which is the kind that ships."""
        assert "retry_on_conflict" not in fds.store_seams()
        assert "retry_on_conflict" in fds.public_coroutines_not_swept()


class TestTheBindingScanIsByIDENTITYNotByNAME:
    """⛔ *"When you catch yourself enumerating what is FORBIDDEN, you have already lost."*

    A scan keyed on the attribute NAME is defeated by an alias; a scan keyed on the FUNCTION
    OBJECT is not, and is not fooled by an impostor wearing the name either. Both directions
    are pinned, because each alone admits a wrong build the other catches.
    """

    def test_a_seam_bound_under_an_ALIAS_is_found(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seam = next(iter(fds.store_seams().values()))
        module = ModuleType(_FAKE_PACKAGE)
        module.a_name_nobody_would_grep_for = seam  # type: ignore[attr-defined]
        monkeypatch.setitem(sys.modules, _FAKE_PACKAGE, module)
        bindings = fds.seam_bindings(package=_FAKE_PACKAGE)
        assert [binding.attribute for binding in bindings] == ["a_name_nobody_would_grep_for"]

    def test_an_IMPOSTOR_wearing_a_seam_name_is_NOT_found(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        seam_name = next(iter(fds.store_seams()))

        async def _impostor(*_args: Any, statement: str = "", **_kwargs: Any) -> None:
            """Same name, same signature, different function — not a door."""

        module = ModuleType(_FAKE_PACKAGE)
        setattr(module, seam_name, _impostor)
        monkeypatch.setitem(sys.modules, _FAKE_PACKAGE, module)
        assert fds.seam_bindings(package=_FAKE_PACKAGE) == ()

    def test_the_seam_module_itself_is_never_a_binding_site(self) -> None:
        """⛔ Its own internals reference these as globals; patching there would count one
        store operation twice the day a seam composes another."""
        assert all(
            binding.module_name != fds.SEAM_MODULE for binding in fds.seam_bindings()
        )


# ---------------------------------------------------------------------------
# The ENGINE, on a fake seam — counting, faulting, refusing
# ---------------------------------------------------------------------------


def _install_fake_seam(
    monkeypatch: pytest.MonkeyPatch, *, seam_name: str = "fake_seam"
) -> ModuleType:
    """A one-seam world the sweep can drive without touching a store.

    ``store_seams`` is redirected so :func:`forgery_door_sweep.seam_bindings` matches the
    fake by identity, exactly as it matches a real seam.
    """

    async def _seam(*_args: Any, statement: str = "", **_kwargs: Any) -> None:
        """A store call that succeeds and touches nothing."""

    _seam.__name__ = seam_name
    module = ModuleType(_FAKE_PACKAGE)
    setattr(module, seam_name, _seam)
    monkeypatch.setitem(sys.modules, _FAKE_PACKAGE, module)
    monkeypatch.setattr(fds, "store_seams", lambda: {seam_name: _seam})
    return module


def _subject_factory(
    call: Callable[[], Any], observe: Callable[[], Any]
) -> fds.SubjectFactory:
    """Wrap two coroutine functions as the async-context-manager factory the sweep takes."""

    @asynccontextmanager
    async def _factory() -> AsyncIterator[fds.Subject]:
        yield fds.Subject(call=call, observe=observe)

    return _factory


def _calling_seam_n_times(
    module: ModuleType, seam_name: str, n: int, *, swallow_at: int | None = None
) -> Callable[[], Any]:
    """An entry point making ``n`` store calls, optionally SWALLOWING the fault at one."""

    async def _call() -> None:
        for index in range(1, n + 1):
            try:
                await getattr(module, seam_name)(statement=f"statement {index}")
            except fds.InjectedStoreFault:
                if swallow_at is None or index != swallow_at:
                    raise
                # The single most-written defensive line in any migration:
                # "this must never stop the service booting".

    return _call


async def _observe_zero() -> int:
    return 0


class TestTheSweepDerivesTheDoorCountFromTheCONTROL:
    async def test_the_control_is_what_yields_N_and_every_door_is_faulted_at_its_own_k(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        module = _install_fake_seam(monkeypatch)
        factory = _subject_factory(
            _calling_seam_n_times(module, "fake_seam", 3), _observe_zero
        )
        report = await fds.sweep_doors(
            factory, entry_point="entry", world="a fake world", package=_FAKE_PACKAGE
        )
        assert report.control_calls == 3
        assert [door.k for door in report.doors] == [1, 2, 3]
        assert [door.calls_observed for door in report.doors] == [1, 2, 3], (
            "a door whose observed call count is not k did not stop execution where the "
            "fault was injected, so the door it names is not the door it measured"
        )
        assert report.all_doors_loud

    async def test_the_restore_is_TOTAL_so_a_sweep_leaves_no_wrapper_behind(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ A leaked wrapper would fault an unrelated later caller — and the sweep runs
        N+1 legs, so a leak is a corruption that grows with the door count."""
        module = _install_fake_seam(monkeypatch)
        before = module.fake_seam
        factory = _subject_factory(
            _calling_seam_n_times(module, "fake_seam", 2), _observe_zero
        )
        await fds.sweep_doors(
            factory, entry_point="entry", world="a fake world", package=_FAKE_PACKAGE
        )
        assert module.fake_seam is before


class TestASWALLOWEDDoorIsAFAILURE:
    """⛔ THE DISCRIMINATION PIN. Without it every test above is satisfied by a sweep that
    never faults anything, and the whole file is decoration."""

    async def test_a_subject_that_swallows_one_fault_is_reported_as_a_SILENT_door(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        module = _install_fake_seam(monkeypatch)
        factory = _subject_factory(
            _calling_seam_n_times(module, "fake_seam", 4, swallow_at=2), _observe_zero
        )
        report = await fds.sweep_doors(
            factory, entry_point="entry", world="a fake world", package=_FAKE_PACKAGE
        )
        assert not report.all_doors_loud
        assert [door.k for door in report.silent_doors] == [2]
        rendered = report.render()
        assert "RETURNED" in rendered and "k=2" in rendered
        assert "⛔" in rendered, "a silent door must be visible in the render, not only in the API"

    async def test_a_swallowed_door_is_visible_even_though_the_run_CONTINUED(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The swallowing subject makes ALL 4 calls, so ``calls_observed`` for door 2 is 4,
        not 2. That is the tell, and it is rendered."""
        module = _install_fake_seam(monkeypatch)
        factory = _subject_factory(
            _calling_seam_n_times(module, "fake_seam", 4, swallow_at=2), _observe_zero
        )
        report = await fds.sweep_doors(
            factory, entry_point="entry", world="a fake world", package=_FAKE_PACKAGE
        )
        assert report.doors[1].calls_observed == 4


class TestTheSweepREFUSESAVerdictItCannotSubstantiate:
    """Each of these states would otherwise print the same last line as a clean build."""

    async def test_no_binding_site_is_a_REFUSAL_not_a_clean_report(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _seam(*_args: Any, statement: str = "", **_kwargs: Any) -> None: ...

        monkeypatch.setattr(fds, "store_seams", lambda: {"fake_seam": _seam})
        monkeypatch.setitem(sys.modules, _FAKE_PACKAGE, ModuleType(_FAKE_PACKAGE))

        async def _call() -> None: ...

        with pytest.raises(fds.SweepCannotSubstantiate, match="patched NOTHING"):
            await fds.sweep_doors(
                _subject_factory(_call, _observe_zero),
                entry_point="entry",
                world="a fake world",
                package=_FAKE_PACKAGE,
            )

    async def test_an_EMPTY_seam_derivation_is_a_REFUSAL(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(fds, "store_seams", dict)

        async def _call() -> None: ...

        with pytest.raises(fds.SweepCannotSubstantiate, match="came back EMPTY"):
            await fds.sweep_doors(
                _subject_factory(_call, _observe_zero),
                entry_point="entry",
                world="a fake world",
                package=_FAKE_PACKAGE,
            )

    async def test_an_entry_point_making_NO_store_call_is_a_REFUSAL(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ Zero doors is the state in which "all doors fail loud" is true the way "no
        unicorns escaped" is true."""
        _install_fake_seam(monkeypatch)

        async def _call() -> None: ...

        with pytest.raises(fds.SweepCannotSubstantiate, match="ZERO store calls"):
            await fds.sweep_doors(
                _subject_factory(_call, _observe_zero),
                entry_point="entry",
                world="a fake world",
                package=_FAKE_PACKAGE,
            )

    async def test_a_CONTROL_that_raises_is_a_REFUSAL(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ A world broken independently of the fault makes every door raise for a reason
        that has nothing to do with the door."""
        module = _install_fake_seam(monkeypatch)

        async def _call() -> None:
            await module.fake_seam(statement="one")
            raise ValueError("this world was broken before anybody faulted it")

        with pytest.raises(fds.SweepCannotSubstantiate, match="POSITIVE CONTROL raised"):
            await fds.sweep_doors(
                _subject_factory(_call, _observe_zero),
                entry_point="entry",
                world="a fake world",
                package=_FAKE_PACKAGE,
            )


class TestTheRenderCarriesItsOwnSCOPE:
    async def test_the_render_names_the_seams_swept_AND_the_ones_excluded(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔ A count with no set is the shape this repo has the most receipts against: a
        reader told "4 doors, all loud" and not told WHICH seams that covers has been handed
        a number they cannot bound."""
        module = _install_fake_seam(monkeypatch)
        factory = _subject_factory(
            _calling_seam_n_times(module, "fake_seam", 1), _observe_zero
        )
        report = await fds.sweep_doors(
            factory, entry_point="entry", world="a fake world", package=_FAKE_PACKAGE
        )
        rendered = report.render()
        assert "DERIVATION:" in rendered and "fake_seam" in rendered
        assert "NOT SWEPT" in rendered
        for excluded in fds.public_coroutines_not_swept():
            assert excluded in rendered, (
                f"{excluded} is excluded from the sweep and the render does not say so, so "
                f"the bound is invisible to the reader acting on the verdict"
            )


# ---------------------------------------------------------------------------
# The LIVE legs — the reproduction this file exists to make re-runnable
# ---------------------------------------------------------------------------


class TestThisInstrumentIsTYPECHECKED:
    """⛔ ``scripts/`` is OUTSIDE ``scripts/typecheck.sh`` (#188 measured 41 mypy errors
    there), so nothing in the canonical gate reads these two files.

    A "mypy-clean" claim that no gate re-derives is the same shape as a guard nobody runs.
    Rather than add ``scripts`` to the gate (which would import 41 unrelated errors and turn
    it red) or hand-list files inside it (the enumeration this repo has the most receipts
    against), the check is scoped to exactly the two files this contract owns and lives
    where they do. ``mypy_path`` is READ from ``pyproject.toml`` rather than re-typed — a
    copied path list is a registration site that goes stale silently.
    """

    def test_mypy_is_clean_over_the_sweep_and_its_contract(self) -> None:
        import subprocess
        import tomllib
        from pathlib import Path

        repository_root = Path(__file__).resolve().parent.parent
        configuration = tomllib.loads((repository_root / "pyproject.toml").read_text())
        declared_path = configuration["tool"]["mypy"]["mypy_path"]
        targets = [str(Path(__file__).resolve()), str(fds.__file__)]
        completed = subprocess.run(
            [sys.executable, "-m", "mypy", *targets],
            cwd=repository_root,
            env={**os.environ, "MYPYPATH": f"scripts:{declared_path}"},
            capture_output=True,
            text=True,
            check=False,
        )
        assert completed.returncode == 0, (
            f"mypy is not clean over this instrument, and the canonical gate cannot see it "
            f"(scripts/ is outside scripts/typecheck.sh MEMBERS):\n{completed.stdout}"
            f"{completed.stderr}"
        )


class TestTheLegacyWorldIsGenuinelyOlder:
    def test_the_legacy_DDL_drops_the_blocks_relation_the_production_DDL_emits(self) -> None:
        """⛔ Anti-vacuity: if the removal removed nothing, the "legacy" store is today's
        store, the backfill has nothing to do, and doors 3 and 4 are unreachable."""
        from loremaster.store.surreal_schema import BLOCKS_RELATION, generate_task_ddl

        assert f" {BLOCKS_RELATION} TYPE RELATION" in generate_task_ddl()
        assert f" {BLOCKS_RELATION} TYPE RELATION" not in fds.legacy_task_ddl()


class TestTheDoorSweepOverTheRealLedger:
    """The 04b-1 cold audit's measurement, as a command instead of a paragraph (#278)."""

    async def test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD(
        self,
    ) -> None:
        report = await fds.sweep_doors(
            fds.legacy_task_store,
            entry_point="ensure_ready",
            world="a legacy store",
            observable="edges",
        )
        assert report.control_calls == 4, (
            f"the derived door set for ensure_ready over a legacy store is "
            f"{report.control_calls}, not the 4 the 04b-1 cold audit measured "
            f"(docs/plans/v2/receipts/2026-07-28-packet04b1/REPORT-coldaudit-04b1.md §2.3). "
            f"A CHANGE IN THIS NUMBER IS A FINDING, not a number to update: either a store "
            f"call was added to the boot path or one was removed. Doors seen: "
            f"{[door.seam_called for door in report.doors]}"
        )
        assert report.control_observation == fds._LEGACY_EXPECTED_EDGES, (
            "the unfaulted control did not mint the edges this world implies, so the mint "
            "door the sweep faults is not on the path and door k=4 is vacuous"
        )
        assert report.all_doors_loud, report.render()
        assert [door.calls_observed for door in report.doors] == [1, 2, 3, 4]

    async def test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """⛔⛔ THE POSITIVE CONTROL FOR THE INSTRUMENT ITSELF, on the real ledger.

        This is the wrong build ``BACKFILL_FAILURE_DOORS = ("existence-read", "mint")``
        could not see: a ``try/except`` around the WHOLE backfill, which is the single most
        common defensive line in any migration (*"it must never stop the service booting"*)
        and the exact false clear R11 exists to delete. A boot that survives its own failed
        migration serves every legacy row a confident empty forever.

        The wrong build is INSTALLED AT RUNTIME over the captured original and restored by
        ``monkeypatch`` — no shipped line is edited, and the original is called directly
        rather than through ``super()`` (a subclass method assigned onto its own base
        recurses into itself, which silently makes the backfill never run at all: measured
        here, and it turned this pin's first draft into a control that proved nothing).
        """
        from loremaster.tasks import TaskLedger

        original = TaskLedger._backfill_blocks_edges

        async def _swallowing_backfill(ledger: TaskLedger) -> None:
            """The defensive line that makes a failed migration silent."""
            try:
                await original(ledger)
            except Exception:  # noqa: BLE001 - the wrong build catches everything
                return

        monkeypatch.setattr(TaskLedger, "_backfill_blocks_edges", _swallowing_backfill)
        report = await fds.sweep_doors(
            fds.legacy_task_store,
            entry_point="ensure_ready",
            world="a legacy store",
            observable="edges",
        )

        silent = [door.k for door in report.silent_doors]
        assert silent, (
            "a ledger that swallows EVERY backfill failure was swept and the sweep found no "
            "silent door. The instrument cannot see the defect it exists to find, and every "
            "green verdict it has ever returned is worthless.\n" + report.render()
        )
        assert report.control_observation == fds._LEGACY_EXPECTED_EDGES, (
            "the swallowing build's UNFAULTED control must still migrate correctly — "
            "otherwise the doors below are failing for a reason other than the swallow"
        )
        # The swallow is scoped to the BACKFILL, so the DDL door (which runs before it) must
        # still be loud. A sweep reporting EVERY door silent would be one that had simply
        # stopped working, and would pass the assertion above just as happily.
        assert 1 not in silent, (
            "the DDL door is outside the swallowed region and must still fail loud; a sweep "
            "that calls it silent is broken, not discriminating.\n" + report.render()
        )
        assert len(silent) == report.control_calls - 1, (
            f"every door INSIDE the swallowed backfill must be reported silent. "
            f"silent={silent} of {report.control_calls} doors.\n" + report.render()
        )
        # ⛔ THE ONE THAT MATTERS. ``BACKFILL_FAILURE_DOORS = ("existence-read", "mint")``
        # is a two-element hand-list; the mirror-state read is a THIRD door it cannot see,
        # and a build swallowing it passes that contract 234/234. Here it is, derived.
        assert any(door.seam_called == "execute_read_transaction" for door in report.silent_doors), (
            "the mirror-state read — the door the hand-list in test_blocks_edge.py cannot "
            "see — was not among the silent doors, so this sweep is no better than the list "
            "it replaces.\n" + report.render()
        )
