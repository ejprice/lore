"""Packet 58 contract r4 — amendment 12 §1: FK-r3-5 re-ruled AT THE STATE (root × verb × write index).

*Every claim in this file is scoped to the tree at ``a77dc00`` (branch ``feat/surreal-unification``),
2026-09-29, authored by ``contract-58-r4``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-29-packet58-amendment-12.md`` @ ``5419448`` §1 (supersedes am-9 §5's MINIMAL-verb
domain; erratum am-8 §3 item 2).  Four rounds relocated a hidden constant one level at a time (``_select*`` →
the ``try`` node → ``self._apply(`` → the WRAPPER catch).  The property now lives at the STATE:

    ∀ root R, ∀ verb v under R, ∀ write index k ∈ 1..WRITES(R, v): when the driver seam raises
    ``TxnContentionExhaustedError`` at write k of the call, (1) the seam receives NO further statement from
    the
    call (``statements_after == 0`` — E2 ∪ E3) and nothing commits after it (the store is byte-identical to
    its state at the injection), and (2) the caller observes the SAME instance.

* **ROOTS × verbs — DERIVED**: the population the r3 seam pin derives (the call-graph CAS verbs ∪ the static
  index's listed handlers ∪ every discovered ``CAS_SEAM_DRIVERS`` key) × each verb's roots in its module's
  reverse call graph (``_reanchor_58_support.derive_cas_roots`` — the SAME edge extraction the verbs are read
  off).  So ``findings.py::resolve`` / ``wontfix`` over ``_transition`` — where W-IMPLICIT / W-REBIND /
  W-TUPLE
  lived — are legs by derivation, not by anyone's memory.
* **WRITES(R, v) — MEASURED**: each leg first runs its driver UNARMED in MEASURE mode (the armed seam's
  matching writes are counted, nothing fires), then arms every k ∈ 1..n.  The heal's n ≥ 2 by fixture
  (``2·fit + 1`` straggler rows, fit measured off ``compose``).
* **REACH IS A CHECKED VARIABLE — the FIRED ledger**: the seam itself records ``(root, verb, k)`` for every
  injection that fired (the root = the OUTERMOST production frame of the verb's module on the sending stack —
  observed, never declared).  Per derived ``(R, v)``: the fired set must EQUAL ``{(R, v, k) : k ∈ 1..n}``,
  both ways; a declared driver that never fires, fires under another root, or fires under another verb reds
  BY NAME — never a skip (F-NOOP).  §DEVIATIONS D-R4-1: the ledger is asserted per ``(R, v)`` leg rather
  than once at session end, because ``-n 8`` splits a session across processes; the parametrisation IS the
  derived domain, so the equality is the same set equality, computed where it can be.

Drivers: a root with an entry in :data:`CAS_ROOT_DRIVERS` (``"<R> -> <v>"``) runs that driver; otherwise the
verb's DISCOVERED driver (``test_reanchor_58_r3_cas_seam.discovered_drivers``) runs, and the fired ledger
proves it actually reached the verb through THAT root.  RED at HEAD ``a77dc00``: ``tasks.py`` has no shell,
so its verbs' legs fire under the r3 drivers but their roots are not yet the build's (and the heal does not
exist); the findings legs are GREEN (a correct wrapper at HEAD).
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import AsyncIterator, Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _reanchor_58_support import (
    DESCRIPTION,
    boot,
    derive_cas_roots,
    derive_cas_verbs,
    ledger58,
    new_ledger,
    raw,
    shrunk_row_caps,
)
from _surreal_harness import PRODUCTION_DIM, SurrealEnv, drop_database, make_env, unique_database
from loremaster.tasks import TaskLedger
from test_reanchor_58_r3_cas_seam import (
    PACKAGE_ROOT,
    DriverSeamInjection,
    _finding_ledger,
    _report,
    discovered_drivers,
    listed_handlers,
)

if TYPE_CHECKING:
    # ⚠ RULED, not-yet-built symbols named STATICALLY for the typecheck gate (the #461 shape): packet 58's
    # heal
    # (owned by ``scripts/pending_contracts.yaml`` bound ``packet-58-contract``) and packet 64b-i's
    # ``FindingLedger._run_guarded`` (the discovered 64b driver's leg — bound ``packet-64b-i-contract``, am-12
    # §4 item 3).  Runtime-inert.
    from loremaster.findings import FindingLedger

    _RULED: tuple[object, ...] = (TaskLedger._reanchor_stragglers, FindingLedger._run_guarded)

__all__ = ["DESCRIPTION", "ledger58", "shrunk_row_caps"]  # re-exported fixtures (the r3 idiom)

HEAL_VERB = "tasks.py::_reanchor_stragglers"
HEAL_ROOT = "tasks.py::ensure_ready"
#: The one multi-write CAS verb (a chunk per transaction).  Every OTHER verb is single-transaction: n == 1
#: and the pin says so by measuring (a verb whose n grows silently GAINS legs — it never loses coverage).
MULTI_WRITE_VERBS = frozenset({HEAL_VERB})

RootDriver = Callable[[SurrealEnv, TaskLedger, DriverSeamInjection], Awaitable[None]]


class Measured(Exception):  # noqa: N818 - a control-flow signal, not an error
    """Raised by :func:`_measured_expect` to unwind a driver after its MEASURE pass (its control legs assume
    the armed call did NOT commit, which an unarmed measuring call does)."""


@contextlib.asynccontextmanager
async def fresh_world() -> AsyncIterator[tuple[TaskLedger, SurrealEnv]]:
    """A fresh throwaway database per leg (``ledger58``'s recipe, THE harness's minting): the drivers seed
    fixed ids and store-level EVENTs, so each (R, v, k) run gets its own world — never a shared one."""
    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = new_ledger(env)
    await ledger.ensure_ready()
    try:
        yield ledger, env
    finally:
        await ledger.close()
        await drop_database(env)


async def db_snapshot(ledger: TaskLedger) -> dict[str, list[Any]]:
    """Every row of every table of the database — the byte-comparable STORE state (am-12 §1, F-C)."""
    info = await raw(ledger, "INFO FOR DB")
    info = info[0] if isinstance(info, list) else info
    tables = sorted((info or {}).get("tables", {}))
    state: dict[str, list[Any]] = {}
    for table in tables:
        rows = await raw(ledger, "SELECT * FROM type::table($table)", {"table": table})
        state[table] = sorted(repr(row) for row in rows or [])
    return state


# --------------------------------------------------------------------------- #
# ROOT drivers — roots the verb drivers do not reach (derived: findings' wrappers; the multi-chunk heal)
# --------------------------------------------------------------------------- #


def _finding_root(verb_call: str) -> RootDriver:
    async def _drive(env: SurrealEnv, _ledger: TaskLedger, seam: DriverSeamInjection) -> None:
        findings = await _finding_ledger(env)
        try:
            number = await _report(findings)
            seam.arm("findings.py::_transition")
            await seam.expect_the_SAME_instance(
                f"findings.py::{verb_call}",
                lambda: getattr(findings, verb_call)(number, "actor-58r4"),
            )
        finally:
            await findings.close()

    return _drive


async def _drive_heal_multi_chunk(env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    """The heal at ``2·fit + 1`` rows of the one-entry shape: ≥ 2 heal transactions (am-12 §1 WRITES; F-E's
    scale).  Every leg seeds a FRESH population (distinct tag) and, after it, converges the store with an
    unarmed boot, so every leg sees the same n.

    r5.2 (packet 58 amendment 16 §3 — this leg was SLOW, ~303 s at the 5 000 shrink's fit of ~1 250): the
    row cap is shrunk INSIDE the leg to the measured ``fixed + fit·weight`` with
    fit = :data:`_HEAL_DRIVER_FIT` (§2.5's shrink), so ``2·fit + 1`` is 9 rows in 3 chunks — the same
    multi-chunk shape, in seconds."""
    from loremaster.store import _txn as txn_module
    from test_reanchor_58_r3_convergence import SHAPES, seed_population

    shape = next(shape for shape in SHAPES if shape.label == "e1-distinct-absent")
    measured = _HEAL_SHAPE.get("measured")
    if measured is None:
        measured = await _measure_shape(ledger, env, shape)
        _HEAL_SHAPE["measured"] = measured
    fixed, weight = measured
    tag = f"r4k{seam.write_index}{'m' if seam.measuring else ''}{len(_HEAL_SHAPE)}"
    _HEAL_SHAPE[tag] = measured
    with pytest.MonkeyPatch.context() as shrink:
        shrink.setattr(txn_module, "TXN_ROW_HARD_CAP", fixed + _HEAL_DRIVER_FIT * weight, raising=True)
        await seed_population(ledger, shape, 2 * _HEAL_DRIVER_FIT + 1, tag)
        booted = new_ledger(env)
        seam.arm(HEAL_VERB)
        try:
            await seam.expect_the_SAME_instance(HEAL_VERB, booted.ensure_ready)
        finally:
            await booted.close()
            await boot(env)  # converge the remainder, unarmed — the next leg starts from a healed store


#: r5.2 (am-16 §2.5 / §3): the straggler rows one heal chunk fits under the driver's in-leg shrink.
_HEAL_DRIVER_FIT = 4
_HEAL_SHAPE: dict[str, tuple[int, int]] = {}


async def _measure_shape(ledger: TaskLedger, env: SurrealEnv, shape: Any) -> tuple[int, int]:
    """``(fixed, weight)`` of the shape's heal chunk, MEASURED off ``compose`` at 1 and 2 rows."""
    from _reanchor_58_support import ComposeSpy
    from test_reanchor_58_r3_convergence import _heal_chunks, seed_population

    counts: list[int] = []
    for rows in (1, 2):
        await seed_population(ledger, shape, rows, f"r4fit{rows}")
        spy = ComposeSpy()
        with spy.installed():
            await boot(env)
        chunks = _heal_chunks(spy)
        assert len(chunks) == 1, chunks
        counts.append(chunks[0])
    weight = counts[1] - counts[0]
    fixed = counts[0] - weight
    assert weight > 0, counts
    return fixed, weight


#: THIS module's ROOT drivers, keyed ``"<root> -> <verb>"``.  A key the derivation does not produce reds BY
#: NAME (stale); a derived pair with neither a key here nor a discovered verb driver reds BY NAME.
CAS_ROOT_DRIVERS: dict[str, RootDriver] = {
    "findings.py::resolve -> findings.py::_transition": _finding_root("resolve"),
    "findings.py::wontfix -> findings.py::_transition": _finding_root("wontfix"),
    f"{HEAL_ROOT} -> {HEAL_VERB}": _drive_heal_multi_chunk,
}


def _population() -> set[str]:
    """The seam pin's population (``test_reanchor_58_r3_cas_seam._collection_population``'s members), read
    through the SAME accessors."""
    population = set(derive_cas_verbs(PACKAGE_ROOT))
    population |= listed_handlers()
    population |= set(discovered_drivers())
    return population


def derived_pairs() -> set[tuple[str, str]]:
    """am-12 §1 ROOTS × verbs, DERIVED (``derive_cas_roots``).  The heal verb is seeded even before it exists
    (its root is the boot): a correct build derives ``(ensure_ready, _reanchor_stragglers)``."""
    return derive_cas_roots(PACKAGE_ROOT, _population() | {HEAL_VERB})


def _collection_pairs() -> list[str]:
    try:
        pairs = {f"{root} -> {verb}" for root, verb in derived_pairs()}
    except Exception as error:  # noqa: BLE001 - a broken derivation must RED, never shrink the domain
        return [f"<the root derivation failed to load: {error!r}>"]
    return sorted(pairs | set(CAS_ROOT_DRIVERS))


def _driver_for(pair: str) -> RootDriver | None:
    if pair in CAS_ROOT_DRIVERS:
        return CAS_ROOT_DRIVERS[pair]
    _root, _, verb = pair.partition(" -> ")
    return discovered_drivers().get(verb)


async def _run_leg(
    driver: RootDriver, env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection
) -> None:
    try:
        await driver(env, ledger, seam)
    except Measured:
        return


class TestTheFiredLedgerEqualsTheDerivedDomain:
    """am-12 §1: per derived ``(R, v)`` — measure n, arm every k, the seam's FIRED triples equal
    ``{(R, v, k) : k ∈ 1..n}``; identity, ``statements_after == 0`` and a byte-identical store at every k."""

    @pytest.mark.usefixtures("shrunk_row_caps")
    @pytest.mark.parametrize("pair", _collection_pairs())
    async def test_every_root_verb_and_write_index_fires_and_the_caller_gets_the_SAME_instance(
        self, monkeypatch: pytest.MonkeyPatch, pair: str
    ) -> None:
        derived = {f"{root} -> {verb}" for root, verb in derived_pairs()}
        assert pair in derived, (
            f"{pair}: a ROOT driver for a (root, verb) the call graph does not derive — STALE (the verb "
            "moved, "
            f"or the root is no longer its module's entry)"
        )
        driver = _driver_for(pair)
        assert driver is not None, (
            f"{pair}: a derived (root, verb) that NO driver reaches — add a `CAS_ROOT_DRIVERS` entry (this "
            "file) "
            "or the verb's `CAS_SEAM_DRIVERS` driver in its OWNER's module (am-12 §1: the unit of coverage "
            "is "
            f"the FIRED triple)"
        )
        root, _, verb = pair.partition(" -> ")
        seam = DriverSeamInjection()
        seam.install(monkeypatch, observe_shell=False)

        original_expect = seam.expect_the_SAME_instance

        async def _measured_expect(label: str, call: Callable[[], Awaitable[Any]]) -> None:
            await original_expect(label, call)
            raise Measured

        seam.measuring = True
        seam.expect_the_SAME_instance = _measured_expect  # type: ignore[method-assign,assignment]
        async with fresh_world() as (ledger, env):
            await _run_leg(driver, env, ledger, seam)
        seam.expect_the_SAME_instance = original_expect  # type: ignore[method-assign]
        seam.measuring = False
        writes = seam.matched_writes
        assert writes >= 1, (
            f"{pair}: WRITES(R, v) measured {writes} — the driver's unarmed call sent no write through the "
            "armed "
            f"seam under {verb} (a driver that declares and never drives)"
        )
        if verb in MULTI_WRITE_VERBS and pair in CAS_ROOT_DRIVERS:
            assert writes >= 2, (
                f"{pair}: the multi-chunk fixture measured {writes} heal transactions (need ≥ 2)"
            )

        for write_index in range(1, writes + 1):
            seam.write_index = write_index
            async with fresh_world() as (ledger, env):
                seam.snapshot = lambda ledger=ledger: db_snapshot(ledger)
                await driver(env, ledger, seam)
        expected = {(root, verb, write_index) for write_index in range(1, writes + 1)}
        assert set(seam.fired) == expected, (
            f"{pair}: the FIRED ledger {sorted(seam.fired)} != the derived legs {sorted(expected)} — an "
            "injection "
            f"fired under another root/verb/k, or a leg never fired (am-12 §1: reach is a checked variable)"
        )


class TestTheStateInstrumentDiscriminates:
    """The r4 instrument's own positive controls, over fakes that ride the REAL wrapped seam binding."""

    @staticmethod
    def _armed(monkeypatch: pytest.MonkeyPatch) -> DriverSeamInjection:
        seam = DriverSeamInjection()
        seam.install(monkeypatch, observe_shell=False)
        seam.arm(None)
        return seam

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_a_retry_then_reraise_of_the_SAME_instance_is_caught_by_statements_after(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """W-RETRY-RERAISE's shape (F-C): identity holds, the retried write is a statement AFTER."""
        from loremaster.store import _txn as txn_module

        _txn: Any = txn_module  # the seam wrapper takes any call shape; the fake sends no real transaction
        seam = self._armed(monkeypatch)
        sent: list[str] = []

        async def verb() -> None:
            try:
                await _txn.execute_transaction("BEGIN; COMMIT;", {})
            except _txn.TxnContentionExhaustedError as exhausted:
                try:
                    await _txn.execute_transaction("BEGIN; COMMIT;", {})
                except Exception as retry_error:  # noqa: BLE001 - the fake store has no connection
                    sent.append(repr(retry_error))
                raise exhausted

        with pytest.raises(AssertionError, match="statement\\(s\\) AFTER"):
            await seam.expect_the_SAME_instance("fake.retry_reraise", verb)

    @pytest.mark.usefixtures("shrunk_row_caps")
    async def test_the_write_index_fires_on_the_kth_matching_write_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """F-D: k is honoured — writes before k run untouched, write k is the injection."""
        seam = self._armed(monkeypatch)
        seam.write_index = 2
        calls: list[int] = []

        def _ok(*_args: Any, **_kwargs: Any) -> bool:
            calls.append(1)
            return True

        seam.armed = (None, "execute_transaction", _ok)
        assert seam._should_fire("execute_transaction", [], ("s",), {}) is False  # noqa: SLF001
        assert seam._should_fire("execute_transaction", [], ("s",), {}) is True  # noqa: SLF001
        assert len(calls) == 2

    def test_measure_mode_never_fires(self) -> None:
        seam = DriverSeamInjection()
        seam.measuring = True
        seam.armed = (None, "execute_transaction", lambda _call: True)
        assert not any(
            seam._should_fire("execute_transaction", [], ("s",), {}) for _ in range(3)  # noqa: SLF001
        )
        assert seam.matched_writes == 3

    def test_the_derivation_reaches_the_wrappers_above_a_minimal_verb(self) -> None:
        """Non-vacuity at HEAD: the r3 survivors' doors (``resolve`` / ``wontfix`` over ``_transition``) are
        derived ROOTS, not hand-listed ones."""
        pairs = derived_pairs()
        assert {
            ("findings.py::acknowledge", "findings.py::_transition"),
            ("findings.py::resolve", "findings.py::_transition"),
            ("findings.py::wontfix", "findings.py::_transition"),
            ("findings.py::annotate", "findings.py::annotate"),
        } <= pairs, sorted(pairs)

    def test_a_noop_driver_is_red_by_the_fired_ledger(self) -> None:
        """F-NOOP's control: a driver that never arms leaves ``fired`` empty — the per-pair equality cannot
        hold for any n ≥ 1 (and the measure leg already reds on n == 0)."""
        seam = DriverSeamInjection()
        assert seam.fired == [] and seam.matched_writes == 0


_UNUSED: tuple[object, ...] = (logging, Path)
