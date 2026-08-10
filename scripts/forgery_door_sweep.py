#!/usr/bin/env python3
"""forgery_door_sweep.py — DERIVE the doors a served surface can fail at, and prove each one FAILS LOUD.

**WHY THIS FILE EXISTS AT ALL, and it is the point (finding #278).** This instrument has
now been produced THREE times. ``design-sidecar-04b`` derived the property; ``coldaudit-04b1``
BUILT a working sweep, used it to settle the central claim #274's operator-accepted bound
rests on, and reported the RESULT — and the instrument evaporated with its scratch tree, so
the measurement cannot be re-run and the next surface has to start over. Two agents, two
productions, zero surviving artifacts. This is the third production and it is committed, so
the reproduction below is a command rather than a paragraph.

------------------------------------------------------------------------------
THE PROPERTY, and why it is DERIVED rather than listed

``CLAUDE.md``'s HARD DEFINITION of trust has two legs, and this is the instrument for leg 2
(FORGERY PINS): *"what broken state of this tool would serve exactly these bytes?"* Its
input is the surface's **failure set** — the stateful dependencies of the surface, crossed
with the ways each can be broken — and the law is explicit that the set is **derived like**
``registration_sites.py``, **never a curated list of things that might go wrong.**

The prior art it replaces is exactly such a list. ``test_blocks_edge.py`` carries
``BACKFILL_FAILURE_DOORS = ("existence-read", "mint")`` — a two-element hand-list of the
doors somebody had thought of — and a third door (the mirror-state read) was invisible to
it, so a build that swallowed that door passed the whole contract. *"When you catch yourself
enumerating what is FORBIDDEN, you have already lost."*

So the door set here is derived, from a property that is true of a store door and false of
everything else:

    A DOOR IS ONE INVOCATION OF A STORE SEAM — a PUBLIC coroutine of
    ``loremaster.store._txn`` that EXECUTES A CALLER-SUPPLIED ``statement`` —
    made while the entry point under test is running.

Three things make that derivation available in THIS repo rather than in most:

* ``loremaster.store._txn`` is the ONE door to the store, and that is not an opinion: the
  #136 runtime SDK-escape guard (``loremaster/tests/_sdk_guard.py``) watches every call on a
  live SDK connection and names, by ``file:line``, any that runs without the driver above
  it. The seam registry is an allowlist in the six-defeats sense — small, enumerable, SAFE.
* The ``statement`` PARAMETER is what separates a door from the machinery around it. It
  admits ``run_query`` / ``execute_transaction`` / ``execute_read_transaction`` and excludes
  ``retry_on_conflict`` (the DRIVER — it runs every door, so counting it would double every
  door) and ``bootstrap_session`` (the session bootstrap, whose statements are the seam's
  own, not the caller's). Those two exclusions are PRINTED on every run, so what is out of
  scope is visible rather than assumed. See BOUNDS below: ``bootstrap_session`` is a real
  door that this sweep does NOT cover.
* Nothing is keyed on a RECEIVER or on a METHOD NAME. A door is found because a seam was
  CALLED, whatever the method that called it is called, and a new seam that takes a
  ``statement`` joins the set with nobody editing anything.

------------------------------------------------------------------------------
WHAT IT DOES

For one entry point over one constructed world:

1. **POSITIVE CONTROL** — run it UNFAULTED. It must complete, and it must be observed making
   at least one store call. ``N`` = the number it made. That number IS the derived door set,
   and it is a CHECKED variable, not an assumption: if the control observes zero calls the
   sweep REFUSES to report (a clean verdict from an instrument that saw nothing is
   blindness wearing cleanliness — ``_sdk_guard``'s ``require_observations``, one level up).
2. **THE SWEEP** — for every ``k`` in ``1..N``, on a FRESH world, fail the ``k``-th store
   call and nothing else. The entry point MUST raise. The observed call count must be ``k``
   (so the fault landed at the door it is named after and execution stopped there).
3. **THE VERDICT** — a worklist, never a certificate. Any door that RETURNED is a silent
   door: the surface swallowed a store failure and served a normal response over it, which
   is a forged response in the trust definition's exact sense.

------------------------------------------------------------------------------
USAGE

    ./scripts/forgery_door_sweep.py           # sweep TaskLedger.ensure_ready over a legacy store

Exit 0: every derived door failed loud. Exit 1: at least one door did not — with its ``k``,
what it returned, and what the world looked like afterwards.

The sweep needs the TEST SurrealDB at ``ws://127.0.0.1:18000`` (``LORE_TEST_SURREAL_URL``
overrides). ``:18500`` is PRODUCTION; never point this at it — it creates, seeds and REMOVES
a throwaway database per leg.

Reused as a library:

    from forgery_door_sweep import Subject, sweep_doors
    report = await sweep_doors(my_factory, entry_point="serve", world="a dirty store")

------------------------------------------------------------------------------
⚠ BOUNDS — stated so this file does not over-claim about itself

* **This is the DOOR SWEEP, not the full forgery-site matrix.** The design that implies it
  (``docs/design/2026-07-28-04b-model-consumer-audit.md`` §12.2) also calls for a
  verb × seam × mode walk crossing every tool verb with the law's four modes
  ({stale, empty, wrong-instance, partial}). **That is not built here.** This covers ONE
  mode — the store dependency, faulted — for ONE entry point at a time, supplied by the
  caller.
* **The CLOCK and FS seams are not covered, and their "only door" status is reasoning
  rather than construction** (§12.3): no deny-by-default sweep exists for either, so this
  script cannot derive their doors even in principle. It sweeps the STORE class only.
* **``bootstrap_session`` is a real door this sweep excludes.** A failure to materialise or
  select the namespace/database is a genuine way the surface can break, and the
  ``statement``-parameter property does not admit it. It is PRINTED as NOT SWEPT on every
  run. Closing it is a separate leg, not a silent omission.
* **The sweep sees seams bound in ``loremaster.*`` module namespaces that are IMPORTED when
  it runs.** A seam reached through a module nothing has imported yet is invisible. The
  binding sites are printed and counted for exactly that reason — reach is reported, never
  assumed. It is an invariant over EXECUTED paths, the same honest limit ``_sdk_guard``
  states about itself.
* **Ordering is observed at AWAIT time**, so an entry point that issues store calls
  CONCURRENTLY (``asyncio.gather``) has no stable ``k``-th call and this sweep's per-door
  attribution would be meaningless for it. Every entry point swept so far is sequential;
  a concurrent one needs a different instrument, not a rerun of this one.
* **A door that RAISED is loud; this script does not grade WHAT it raised.** It records the
  exception type and whether the injected fault is traceable in the chain, because a
  surface that translates a store fault into its own typed error is still failing loud —
  but a surface that raises something with no connection to the fault is worth a human
  look, and the note says so.

Its verdict is *"these doors were swept and this is what they did"*, never *"there are no
other doors"*.
"""

from __future__ import annotations

import argparse
import asyncio
import contextlib
import inspect
import sys
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable, Iterator
from contextlib import AbstractAsyncContextManager, asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

#: The module that IS the store seam. Every door lives here; nothing else is a door.
#: Proven the ONLY door by the #136 runtime SDK-escape guard, not asserted by this file.
SEAM_MODULE = "loremaster.store._txn"

#: The parameter whose presence makes a public seam coroutine a DOOR: it executes a
#: statement the CALLER composed. ``retry_on_conflict`` (the driver) and
#: ``bootstrap_session`` (the session's own DDL) both lack it, and both are printed as
#: NOT SWEPT rather than quietly dropped.
_CALLER_STATEMENT_PARAMETER = "statement"

#: The package whose module namespaces are searched for seam bindings.
_DEFAULT_PACKAGE = "loremaster"

#: ``observe`` returns this when the thing being observed does not exist at all — e.g. the
#: ``blocks`` relation table on a store whose DDL apply was the door that failed.
TABLE_ABSENT = -1

_EXIT_OK = 0
_EXIT_SILENT_DOOR = 1

#: The legacy world's shape. ``root`` blocks BOTH dependents; ``dependent_b`` additionally
#: names a PHANTOM blocker, so the existence read has something to filter and the mint has
#: exactly TWO edges to write. A world where every blocker resolves cannot tell a
#: pre-filtered backfill from a naked one.
_LEGACY_ROOT = "root"
_LEGACY_DEPENDENT_A = "dependent_a"
_LEGACY_DEPENDENT_B = "dependent_b"
_LEGACY_EXPECTED_EDGES = 2


class InjectedStoreFault(Exception):
    """The fault this sweep injects at one door, and NOTHING in production catches it.

    Deliberately outside every exception family the store seam handles
    (``OSError``/``SurrealError``/``WebSocketException``, ``KeyError``,
    ``RetryableConflictSignal``, ``SurrealStoreError``): a fault that production could
    classify would be answering a question about the CLASSIFIER. This one asks the only
    question the sweep is for — *does an unhandled store failure at this door reach the
    caller, or does the surface serve a normal response over it?*
    """


class SweepCannotSubstantiate(RuntimeError):
    """The sweep was asked for a verdict it has no evidence for (the #136 shape).

    Three ways it could, and all three RAISE rather than reporting clean:

    * **The seam derivation came back EMPTY** — then no call is ever a door, every entry
      point trivially "has no silent doors", and the verdict is about nothing.
    * **No module binds a seam** — the interception would patch nothing, the entry point
      would run undisturbed, and every door would look loud because none was ever faulted.
    * **The positive control observed ZERO store calls, or itself raised** — then either
      the sweep cannot see the code, or the world is broken independently of any fault. In
      both states every door's "it raised" is true for a reason having nothing to do with
      the door.
    """


@dataclass(frozen=True)
class Subject:
    """One freshly constructed world, plus the entry point to sweep over it.

    Attributes:
        call: The entry point. Awaited once per leg, under interception.
        observe: An observable of the world, read AFTER the entry point returns or raises
            and OUTSIDE the interception, so reading it is never itself a door. Return
            :data:`TABLE_ABSENT` for "the thing being observed does not exist".
    """

    call: Callable[[], Awaitable[None]]
    observe: Callable[[], Awaitable[int]]


SubjectFactory = Callable[[], AbstractAsyncContextManager[Subject]]


@dataclass(frozen=True)
class SeamBinding:
    """One module attribute that holds a store seam — a place a door can be reached from."""

    module_name: str
    attribute: str
    seam_name: str
    original: Callable[..., Any]

    def __str__(self) -> str:
        return f"{self.module_name}.{self.attribute}"


@dataclass(frozen=True)
class DoorOutcome:
    """What the entry point did when its ``k``-th store call was made to fail."""

    k: int
    raised: str | None
    calls_observed: int
    seam_called: str | None
    observation: int
    fault_traceable: bool

    @property
    def loud(self) -> bool:
        """Whether this door failed LOUD — i.e. the fault reached the caller."""
        return self.raised is not None

    @property
    def note(self) -> str:
        """Anything about this door a reader must not miss, or the empty string."""
        if not self.loud:
            return "  ⛔ RETURNED NORMALLY — a store failure was swallowed at this door"
        notes: list[str] = []
        if self.calls_observed != self.k:
            notes.append(
                f"the fault was injected at call {self.k} but {self.calls_observed} calls "
                f"ran, so execution did not stop at this door"
            )
        if not self.fault_traceable:
            notes.append(
                "the injected fault is not in the raised exception's cause/context chain — "
                "it raised, but for a reason worth reading"
            )
        return f"  ⚠ {'; '.join(notes)}" if notes else ""


@dataclass(frozen=True)
class DoorSweepReport:
    """Everything one sweep measured. Rendered by :meth:`render`; judged by a human."""

    entry_point: str
    world: str
    observable: str
    seam_names: tuple[str, ...]
    not_swept: tuple[str, ...]
    bindings: tuple[str, ...]
    control_calls: int
    control_observation: int
    doors: tuple[DoorOutcome, ...]

    @property
    def all_doors_loud(self) -> bool:
        """Whether EVERY derived door made the entry point raise."""
        return all(door.loud for door in self.doors)

    @property
    def silent_doors(self) -> tuple[DoorOutcome, ...]:
        """The doors that swallowed their fault — the actionable half of the report."""
        return tuple(door for door in self.doors if not door.loud)

    def render(self) -> str:
        """The report, in the shape the 04b-1 cold audit published it in.

        The derivation is rendered FIRST and the exclusions are rendered BESIDE it: a
        reader who is told "4 doors, all loud" and not told which seams that covers has
        been handed a number without its set.
        """
        lines = [
            f"DERIVATION: {len(self.seam_names)} store seam(s) — "
            f"{', '.join(self.seam_names)} — bound at {len(self.bindings)} site(s).",
            f"NOT SWEPT (public {SEAM_MODULE} coroutines executing no caller statement): "
            f"{', '.join(self.not_swept) or 'none'}.",
            f"POSITIVE CONTROL: {self.entry_point} made {self.control_calls} store calls, "
            f"raised=None, {self.observable}={self.control_observation}",
            f"DERIVED DOOR SET: {self.control_calls} store calls during {self.entry_point} "
            f"over {self.world}.",
        ]
        for door in self.doors:
            verdict = f"RAISED  {door.raised}" if door.loud else "RETURNED"
            # The seam name is DERIVED from the call that was faulted, never a hand-written
            # annotation. The cold audit's original render carried `# the mint` style
            # comments beside each door — a name-list one edit away from being wrong about
            # its own output.
            lines.append(
                f"  door k={door.k}: {verdict}  (calls observed {door.calls_observed}, "
                f"{self.observable} after {door.observation})  via {door.seam_called}"
                f"{door.note}"
            )
        if self.all_doors_loud:
            lines.append(
                f"ALL {len(self.doors)} DERIVED DOORS FAIL LOUD — no silent door in "
                f"{self.entry_point} on the shipped build."
            )
        else:
            lines.append(
                f"⛔ {len(self.silent_doors)} OF {len(self.doors)} DERIVED DOORS DID NOT "
                f"FAIL LOUD — {self.entry_point} serves a normal response over a failed "
                f"store call at "
                f"{', '.join(f'k={door.k}' for door in self.silent_doors)}."
            )
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# The derivation
# ---------------------------------------------------------------------------


def store_seams() -> dict[str, Callable[..., Any]]:
    """Every DOOR-BEARING coroutine of :data:`SEAM_MODULE`, derived from a property.

    The property: PUBLIC (a private helper is reached only through a public one, so
    counting it would double a door), a coroutine function DEFINED in the seam module (a
    re-export is not a new door), and accepting a caller-supplied
    ``statement`` — which is what makes a call a store OPERATION rather than the machinery
    that runs one.

    Returns:
        ``{name: function}``. Empty is a broken derivation, never a clean tree — the
        callers below raise on it rather than reporting no doors.

    Routes through the ONE store-seam walk ``loremaster.store._txn_coroutines`` (finding
    #279): the DOOR subset is the public + ``statement``-bearing filter of that WIDE core,
    not a second independent walk of ``vars(_txn)``. The lazy call-time import is deliberate
    — it re-reads the (possibly mutation-rebound) package attribute, so the sharing proof
    (``test_store_seam_one_derivation.TestSharingProvenByMutation``) reaches this filter.
    """
    from loremaster.store import _txn_coroutines

    return {
        name: function
        for name, function in _txn_coroutines().items()
        if not name.startswith("_")
        and _CALLER_STATEMENT_PARAMETER in inspect.signature(function).parameters
    }


def public_coroutines_not_swept() -> dict[str, str]:
    """The public seam coroutines this sweep does NOT treat as doors, each with its reason.

    Printed on every run. An exclusion nobody is told about is indistinguishable from a
    door nobody found — which is the failure this whole file exists to stop.

    Routes through the SAME ONE walk as :func:`store_seams` (``_txn_coroutines``, #279): the
    public non-door coroutines are the complement filter of the WIDE core, never a third
    private walk of ``vars(_txn)``.
    """
    from loremaster.store import _txn_coroutines

    return {
        name: "executes no caller-supplied statement"
        for name, function in _txn_coroutines().items()
        if not name.startswith("_")
        and _CALLER_STATEMENT_PARAMETER not in inspect.signature(function).parameters
    }


def seam_bindings(
    *,
    package: str = _DEFAULT_PACKAGE,
    seams: dict[str, Callable[..., Any]] | None = None,
) -> tuple[SeamBinding, ...]:
    """Every place an IMPORTED ``package`` module holds a store seam, found BY IDENTITY.

    By identity, never by name: a module that imported ``execute_transaction`` under an
    alias is still holding the same function object, and a module that happens to define
    something *called* ``run_query`` is not.

    ``seams`` selects WHICH seam set to bind over (finding #279): omit it for the DOOR subset
    (``store_seams()``, the default — back-compatible), or pass the WIDE superset
    (``loremaster.store._txn_coroutines()``) so a caller like
    ``_degrade_every_STORE_seam`` can build bindings over every ``_txn`` coroutine
    ``loremaster.tasks`` binds, not only the doors. Either way the bindings are found by
    identity against the given set.

    The seam module itself is skipped. Its own internals reference these functions as
    globals, so patching there would intercept a seam calling a seam — one store operation
    counted twice.
    """
    if seams is None:
        seams = store_seams()
    by_identity = {id(function): name for name, function in seams.items()}
    found: list[SeamBinding] = []
    for module_name, module in list(sys.modules.items()):
        if module is None or module_name == SEAM_MODULE:
            continue
        if module_name != package and not module_name.startswith(f"{package}."):
            continue
        for attribute, value in list(vars(module).items()):
            seam_name = by_identity.get(id(value))
            if seam_name is not None:
                found.append(
                    SeamBinding(
                        module_name=module_name,
                        attribute=attribute,
                        seam_name=seam_name,
                        original=value,
                    )
                )
    return tuple(found)


# ---------------------------------------------------------------------------
# The interception
# ---------------------------------------------------------------------------


@dataclass
class _Interceptor:
    """Counts store calls and fails exactly one of them.

    ``depth`` is the re-entrancy guard: a seam reached from INSIDE another seam call is the
    same store operation, not a second door. No such nesting exists on today's paths (the
    session bootstrap is not a door by the derivation above), but a derivation that grows is
    the whole point of a derivation, and a future seam that composes another must not make
    every door count double.
    """

    fail_at: int | None
    calls: list[str] = field(default_factory=list)
    depth: int = 0

    def wrap(self, seam_name: str, original: Callable[..., Any]) -> Callable[..., Any]:
        """A stand-in for ``original`` that counts, optionally faults, then calls through."""

        async def _intercepted(*args: Any, **kwargs: Any) -> Any:
            if self.depth:
                return await original(*args, **kwargs)
            self.calls.append(seam_name)
            if self.fail_at is not None and len(self.calls) == self.fail_at:
                raise InjectedStoreFault(
                    f"forgery_door_sweep failed store call {self.fail_at} "
                    f"({seam_name}) deliberately"
                )
            self.depth += 1
            try:
                return await original(*args, **kwargs)
            finally:
                self.depth -= 1

        return _intercepted


@contextmanager
def _intercepting(
    bindings: tuple[SeamBinding, ...], interceptor: _Interceptor
) -> Iterator[None]:
    """Install ``interceptor`` at every binding for the duration, then restore all of them."""
    for binding in bindings:
        setattr(
            sys.modules[binding.module_name],
            binding.attribute,
            interceptor.wrap(binding.seam_name, binding.original),
        )
    try:
        yield
    finally:
        for binding in bindings:
            setattr(sys.modules[binding.module_name], binding.attribute, binding.original)


def _fault_is_traceable(error: BaseException) -> bool:
    """Whether the injected fault is anywhere in ``error``'s cause/context chain.

    Both chains, because a surface that re-raises WITHOUT ``from`` still carries the fault
    in ``__context__``, and calling that untraceable would flag correct code.
    """
    seen: set[int] = set()
    current: BaseException | None = error
    while current is not None and id(current) not in seen:
        if isinstance(current, InjectedStoreFault):
            return True
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return False


@dataclass(frozen=True)
class _Leg:
    """One run of the entry point — the control, or one faulted door."""

    raised: BaseException | None
    calls: tuple[str, ...]
    observation: int
    bindings: tuple[SeamBinding, ...]


async def _run_leg(
    subject_factory: SubjectFactory, *, fail_at: int | None, package: str
) -> _Leg:
    """Build a fresh world, run the entry point (faulting call ``fail_at``), observe, tear down.

    A FRESH world per leg on purpose: door ``k``'s fault leaves the store in whatever state
    ``k-1`` successful calls put it in, so a shared world would make every door after the
    first a measurement of its predecessor's wreckage rather than of itself.

    ⚠ The bindings are derived AFTER the world is built, never before. Building the world
    is what IMPORTS the module under test, and a binding scan that runs first finds an
    empty ``sys.modules`` and patches nothing — which is a sweep that faults no door and
    calls every one of them loud. (Measured on this script's own first run: the refusal in
    :func:`sweep_doors` fired, which is why it is a refusal and not a warning.)
    """
    interceptor = _Interceptor(fail_at=fail_at)
    raised: BaseException | None = None
    async with subject_factory() as subject:
        bindings = seam_bindings(package=package)
        with _intercepting(bindings, interceptor):
            try:
                await subject.call()
            except Exception as error:  # the vocabulary belongs to the build, not to us
                raised = error
        observation = await subject.observe()
    return _Leg(
        raised=raised,
        calls=tuple(interceptor.calls),
        observation=observation,
        bindings=bindings,
    )


async def sweep_doors(
    subject_factory: SubjectFactory,
    *,
    entry_point: str,
    world: str,
    observable: str = "observation",
    package: str = _DEFAULT_PACKAGE,
) -> DoorSweepReport:
    """Derive ``entry_point``'s store doors over ``world`` and prove each one fails loud.

    Args:
        subject_factory: An async context manager yielding a FRESH :class:`Subject` each
            time it is entered. Called once for the control and once per door.
        entry_point: What to call the entry point in the render (e.g. ``"ensure_ready"``).
        world: What to call the constructed world (e.g. ``"a legacy store"``).
        observable: What :meth:`Subject.observe` returns, for the render (e.g. ``"edges"``).
        package: The package whose imported modules are searched for seam bindings.

    Returns:
        A :class:`DoorSweepReport`. A report is a WORKLIST — read
        :attr:`DoorSweepReport.silent_doors`, not just the last line.

    Raises:
        SweepCannotSubstantiate: The sweep cannot back a verdict — see that class.
    """
    seams = store_seams()
    if not seams:
        raise SweepCannotSubstantiate(
            f"the store-seam derivation over {SEAM_MODULE} came back EMPTY, so no call "
            f"could ever be a door and this sweep would certify {entry_point} against "
            f"nothing at all. Either the seam module moved or its public coroutines no "
            f"longer take a {_CALLER_STATEMENT_PARAMETER!r} parameter — re-derive before "
            f"trusting any verdict from this file."
        )
    control = await _run_leg(subject_factory, fail_at=None, package=package)
    if not control.bindings:
        raise SweepCannotSubstantiate(
            f"no imported {package!r} module binds any of the derived seams "
            f"({', '.join(sorted(seams))}), so the interception patched NOTHING and "
            f"{entry_point} ran undisturbed. Every door would then look loud because no "
            f"door was ever faulted. The subject factory must import the module under test."
        )
    if control.raised is not None:
        raise SweepCannotSubstantiate(
            f"the POSITIVE CONTROL raised {type(control.raised).__name__} on an UNFAULTED "
            f"run of {entry_point} over {world}: {control.raised!r}. The world is broken "
            f"independently of any injected fault, so every door's 'it raised' would be "
            f"true for a reason having nothing to do with the door."
        )
    if not control.calls:
        raise SweepCannotSubstantiate(
            f"the POSITIVE CONTROL observed ZERO store calls while running {entry_point} "
            f"over {world}, across {len(control.bindings)} binding site(s). Either this entry point "
            f"reaches the store through a module the sweep does not watch, or it makes no "
            f"store call at all. A sweep of an empty door set reports 'all doors fail loud' "
            f"in exactly the words a correct build uses, so it refuses instead."
        )

    doors: list[DoorOutcome] = []
    for k in range(1, len(control.calls) + 1):
        leg = await _run_leg(subject_factory, fail_at=k, package=package)
        doors.append(
            DoorOutcome(
                k=k,
                raised=None if leg.raised is None else type(leg.raised).__name__,
                calls_observed=len(leg.calls),
                seam_called=leg.calls[k - 1] if len(leg.calls) >= k else None,
                observation=leg.observation,
                fault_traceable=leg.raised is not None and _fault_is_traceable(leg.raised),
            )
        )

    excluded = public_coroutines_not_swept()
    return DoorSweepReport(
        entry_point=entry_point,
        world=world,
        observable=observable,
        seam_names=tuple(sorted(seams)),
        not_swept=tuple(sorted(excluded)),
        bindings=tuple(str(binding) for binding in control.bindings),
        control_calls=len(control.calls),
        control_observation=control.observation,
        doors=tuple(doors),
    )


# ---------------------------------------------------------------------------
# The subject this script ships with: TaskLedger.ensure_ready over a legacy store
# ---------------------------------------------------------------------------


def _harness() -> Any:
    """The suite's real-SurrealDB harness, imported the way ``conftest.py`` makes it importable.

    ``loremaster/tests`` is a plain directory, not a package, and the suite reaches its
    shared helpers as top-level modules by putting that directory on ``sys.path``
    (``loremaster/tests/conftest.py``). This script is not run by pytest, so it does the
    same insert itself rather than re-deriving the connection topology, the unique-database
    minting and the retry-aware teardown that harness already owns.
    """
    tests_directory = str(_repository_root() / "loremaster" / "tests")
    if tests_directory not in sys.path:
        sys.path.insert(0, tests_directory)
    import _surreal_harness

    return _surreal_harness


def _repository_root() -> Any:
    """This checkout's root, derived from this file's location."""
    from pathlib import Path

    return Path(__file__).resolve().parent.parent


def legacy_task_ddl() -> str:
    """Today's task DDL with the ``blocks`` RELATION statement REMOVED — the OLD WORLD.

    DERIVED from the production emitter by REMOVAL, never hand-written: a hand-copied
    old-DDL string tests a COPY of the code and stays green while production changes
    underneath it. ``blocks``' old world is a store that never had the relation table at
    all, which is what the production store was measured to be at 04b's kickoff.

    Raises:
        SweepCannotSubstantiate: The removal removed nothing — then the "legacy" world is
            today's world and every door below is measured against a store that needs no
            migration.
    """
    from loremaster.store.surreal_schema import BLOCKS_RELATION, generate_task_ddl

    current = generate_task_ddl()
    kept = [
        statement
        for statement in current.split(";\n")
        if statement.strip() and f" {BLOCKS_RELATION} TYPE RELATION" not in statement
    ]
    legacy = ";\n".join(kept) + ";\n"
    if legacy == current:
        raise SweepCannotSubstantiate(
            f"stripping the {BLOCKS_RELATION!r} relation statement from the production "
            f"task DDL changed NOTHING, so the 'legacy' world this sweep builds is "
            f"identical to today's. The emitter's wording moved — re-derive the removal "
            f"in the same commit, or the backfill under test has nothing to do."
        )
    return legacy


async def _apply_ddl(connection: Any, ddl: str, *, url: str) -> None:
    """Apply ``ddl`` exactly as production does — ONE ``BEGIN … COMMIT``, every status verified."""
    from loremaster.store._txn import execute_transaction

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_connection: Any) -> None:
        """A DDL rejection is not a dead socket, and must never be treated as one."""

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=url
    )


async def _seed_legacy_task(connection: Any, task_id: str, *, blocked_by: list[str]) -> None:
    """RAW-CREATE a ``task`` row carrying an arbitrary ``blocked_by``, bypassing every guard.

    Not a contrivance — the PRODUCTION state. Every task row written before packet 04b was
    written under a FAIL-OPEN ``blocked_by``, so a long-lived store holds exactly these
    rows, phantom blockers and all. ``CONTENT`` with a bound object, per the store
    reference's DML idioms.
    """
    from loremaster.store.surreal_schema import TASK_TABLE
    from loremaster.tasks import STATUS_OPEN

    now = datetime.now(UTC)
    content: dict[str, Any] = {
        "subject": "a legacy row written under the fail-open blocked_by",
        "description": "seeded by scripts/forgery_door_sweep.py",
        "status": STATUS_OPEN,
        "blocked_by": blocked_by,
        "provenance": {"created_by": "forgery_door_sweep", "created_at": now.isoformat()},
        "created_at": now,
    }
    await connection.query(
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {"id": task_id, "content": content},
    )


async def _blocks_edge_count(connection: Any) -> int:
    """How many ``blocks`` edges exist, or :data:`TABLE_ABSENT` if the table does not.

    The distinction matters and a plain ``SELECT count()`` cannot make it: SurrealDB serves
    an EMPTY result for a table that was never defined, so "no edges" and "no table" read
    identically — and telling them apart is exactly how the DDL door is distinguished from
    the three that follow it.

    Counted from the edge ROWS rather than from a traversal: store reference §6.4 measured
    that a traversal lists a dangling endpoint as a first-class member, so only the row
    count answers "did an edge land".
    """
    from loremaster.store.surreal_schema import BLOCKS_RELATION

    info = await connection.query("INFO FOR DB")
    tables = info.get("tables") if isinstance(info, dict) else None
    if not isinstance(tables, dict) or BLOCKS_RELATION not in tables:
        return TABLE_ABSENT
    rows = await connection.query(f"SELECT count() FROM {BLOCKS_RELATION} GROUP ALL")
    if not isinstance(rows, list) or not rows or not isinstance(rows[0], dict):
        return 0
    return int(rows[0].get("count", 0))


@asynccontextmanager
async def legacy_task_store() -> AsyncIterator[Subject]:
    """A throwaway store in the world 04b-1 DEPLOYS INTO, and ``ensure_ready`` over it.

    ``blocked_by`` COLUMNS on three rows, ZERO ``blocks`` edges, no ``blocks`` table at all,
    and one PHANTOM blocker — so an unfaulted ``ensure_ready`` has a real migration to do
    (two mintable edges, one phantom to skip) rather than an early return that would make
    the later doors unreachable.

    Every leg gets its own database under the TEST server, removed on the way out.
    """
    from loremaster.tasks import TaskLedger

    harness = _harness()
    env = harness.make_env(database=harness.unique_database(), dim=harness.PRODUCTION_DIM)
    connection = await harness.connect_admin(env)
    try:
        await _apply_ddl(connection, legacy_task_ddl(), url=env.url)
        ids = {
            name: f"{name}_{uuid.uuid4().hex}"
            for name in (_LEGACY_ROOT, _LEGACY_DEPENDENT_A, _LEGACY_DEPENDENT_B)
        }
        phantom = f"phantom_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, ids[_LEGACY_ROOT], blocked_by=[])
        await _seed_legacy_task(
            connection, ids[_LEGACY_DEPENDENT_A], blocked_by=[ids[_LEGACY_ROOT]]
        )
        await _seed_legacy_task(
            connection, ids[_LEGACY_DEPENDENT_B], blocked_by=[ids[_LEGACY_ROOT], phantom]
        )
        ledger = TaskLedger(
            url=env.url,
            namespace=env.namespace,
            database=env.database,
            user=env.user,
            password=env.password,
        )

        async def _call() -> None:
            await ledger.ensure_ready()

        async def _observe() -> int:
            return await _blocks_edge_count(connection)

        try:
            yield Subject(call=_call, observe=_observe)
        finally:
            await ledger.close()
    finally:
        with contextlib.suppress(Exception):
            await connection.close()
        await harness.drop_database(env)


def main(argv: list[str] | None = None) -> int:
    """Sweep ``TaskLedger.ensure_ready`` over a legacy store and print the derived door set."""
    parser = argparse.ArgumentParser(
        description=(
            "Derive the store doors TaskLedger.ensure_ready passes through on a legacy "
            "store, and prove each one makes it RAISE. Needs the TEST SurrealDB "
            "(ws://127.0.0.1:18000 by default; LORE_TEST_SURREAL_URL overrides). "
            "NEVER point this at :18500 — it creates and REMOVES databases."
        )
    )
    parser.parse_args(argv)
    report = asyncio.run(
        sweep_doors(
            legacy_task_store,
            entry_point="ensure_ready",
            world="a legacy store",
            observable="edges",
        )
    )
    print(report.render())
    if report.control_observation != _LEGACY_EXPECTED_EDGES:
        print(
            f"⚠ the positive control minted {report.control_observation} edges where this "
            f"world implies {_LEGACY_EXPECTED_EDGES} (root blocks both dependents; the "
            f"phantom is skipped). The fixture drifted — read the sweep above with that in "
            f"mind.",
            file=sys.stderr,
        )
    return _EXIT_OK if report.all_doors_loud else _EXIT_SILENT_DOOR


if __name__ == "__main__":
    sys.exit(main())
