"""Packet 58 contract r3 — amendment 8 §3: the guarded-CAS ∀ at the DRIVER SEAM, runtime-derived coverage.

*Every claim in this file is scoped to the tree at ``c9e5eb8`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r3``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-26-packet58-amendment-8.md`` @ ``03cb6d0`` §3 (+ amendment 7 ``01565f9`` §3
item 2).
It REPLACES r2's ``test_reanchor_58_r2_cas_runtime.py`` (deleted by this commit — removed-behaviour
inventory in
``REPORT-contract-58-r3.md`` §DUAL R3-D2).  Three instruments of three rounds each keyed on a code SHAPE (the
``_select`` prefix, the ``try`` node, a literal ``self._apply(`` in the verb body); each RED on a correct
build
spelled differently and GREEN on a wrong one spelled differently.  So the ∀ moves to the STATE — the one point
every store write passes through:

1. **Injection at the driver seam.**  Every binding of ``loremaster.store._txn.execute_transaction`` /
   ``run_query`` in every loaded ``loremaster`` module is wrapped (BY IDENTITY — an alias or
   ``_txn_module.execute_transaction`` alike).  On the ARMED call — the first call of the named seam made
   while
   the target verb's frame is on the stack (optionally matching a statement predicate) — the wrapper raises a
   FRESH :class:`TxnContentionExhaustedError` INSTANCE instead of running the write.
2. **Identity.**  The exception that reaches the test's call boundary must BE that instance.  A passthrough
   re-raise preserves identity; a re-read-and-report, a ``ClaimResult``, a domain error ``from`` it, a ledger
   retry that then succeeds, a swallow (``try`` / ``except*`` / ``suppress`` / a helper) — each breaks it.
   The
   property does not care how the catch is spelled (am-8 §3: *"no instrument may dictate the shape"*).
3. **Coverage is a CHECKED VARIABLE, both ways.**  STATIC = the call-graph CAS verbs
   (``_reanchor_58_support.derive_cas_verbs``, the whole tree) ∪ the static index's listed handlers
   (``test_retry_seam._GUARDED_CAS_DOORS`` ∪ ``_TYPED_CAS_CATCHES``).  DRIVEN = the discovered driver registry
   (every test module's ``CAS_SEAM_DRIVERS``; FK-r3-4).  Every STATIC member must be DRIVEN (a CAS nobody
   injects reds BY NAME); every driver must name a STATIC member (a stale driver reds).  At RUNTIME, the shell
   is observed too: every WRITE during a driver's run is attributed to the DEEPEST frame common to the stack
   that built its guard (the shell call) and the stack that sent it (the driver-seam call) — the runtime twin
   of the graph's minimal verb.  Every observed writer must be in the graph's set (an observed writer the
   graph
   did not derive = the graph's blind spot, named), and every driver's own verb must be observed writing.
4. **The ledger's own verdict** stays the CONTROL leg per verb (a REAL lost race through the real driver:
   ``IllegalTransitionError`` / ``ClaimResult(claimed=False)`` / the finding verdicts / ``already_acked`` /
   the
   heal's isolated-chunk WARNING) — so the seam demonstrably CAN change the outcome (§DEVIATIONS D-CTRL: am-8
   §3 item 4's "injected the same way" is honoured by driving the verb's own THROW class through the same
   seam from a real racer, which is stronger than a synthetic instance of it).

RED at HEAD ``c9e5eb8``: ``tasks.py`` has no shell, so its four drivers are STALE against the graph; the three
listed handlers outside 58 (``floor_calibration`` ``record_measurement``, ``keeps``, ``agents.register``) have
no driver anywhere (am-7 §3 item 2 — routed by the lead to their owners, FK-r3-4).
"""

from __future__ import annotations

import ast
import asyncio
import importlib
import inspect
import logging
import sys
import types
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _reanchor_58_support import (
    CAS_SHELL,
    CLAIMANT,
    DRIVER_SEAM_NAMES,
    WORKER,
    ApplyHook,
    cas_verbs_in,
    create,
    derive_cas_verbs,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store._txn import TxnContentionExhaustedError
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_BLOCKED, IllegalTransitionError, TaskLedger

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (the #461 shape): a
    # mypy error at HEAD owned by `scripts/pending_contracts.yaml` bound `packet-58-contract`.  Runtime-inert.
    _RULED_58: tuple[object, ...] = (TaskLedger._guarded_append_fragment,)
    # packet 58 amendment 12 §4 item 3: the discovered 64b driver's population row reds until 64b-i's build —
    # owned by bound ``packet-64b-i-contract`` through this ruled symbol.  Runtime-inert.
    from loremaster.findings import FindingLedger

    _RULED_64B: tuple[object, ...] = (FindingLedger._run_guarded,)

__all__ = ["ledger58"]

PACKAGE_ROOT = Path(importlib.import_module("loremaster").__file__ or "").parent
TESTS_ROOT = Path(__file__).parent
HEAL_CHUNK_REJECTED_EVENT = "task.backfill.straggler_chunk_rejected"
#: The module-level name a test module declares its driver registry under (FK-r3-4: discovered, never a list
#: kept in one file — an owner adds a driver for THEIR handler in THEIR test file).
REGISTRY_NAME = "CAS_SEAM_DRIVERS"


def _frame_key(frame: types.FrameType) -> str | None:
    """``"<package-relative file>::<function>"`` for a PRODUCTION frame, else ``None``."""
    try:
        relative = Path(frame.f_code.co_filename).resolve().relative_to(PACKAGE_ROOT.resolve())
    except ValueError:
        return None
    return f"{relative.as_posix()}::{frame.f_code.co_name}"


def _stack() -> list[types.FrameType]:
    """The live frames above the caller, innermost first (frame OBJECTS — held, so no id is reused)."""
    frames: list[types.FrameType] = []
    frame: types.FrameType | None = sys._getframe(2)  # noqa: SLF001 - the call-time walk (`_sdk_guard` idiom)
    while frame is not None:
        frames.append(frame)
        frame = frame.f_back
    return frames


def _root_of(stack: list[types.FrameType], verb: str | None) -> str:
    """The RUNTIME root of a write (packet 58 amendment 12 §1): the OUTERMOST production frame, in the armed
    verb's own module, on the stack that sent it — the entry the caller actually called, observed rather than
    declared.  Derived twin: ``_reanchor_58_support.derive_cas_roots`` (same-module reverse call graph)."""
    if verb is None:
        return "<unarmed>"
    module = verb.split("::", 1)[0]
    keys = [key for key in map(_frame_key, stack) if key is not None and key.split("::", 1)[0] == module]
    return keys[-1] if keys else "<no production frame>"


class DriverSeamInjection:
    """The am-8 §3 instrument: wrap the driver seams (and observe the shell) for ONE driver's run."""

    def __init__(self) -> None:
        self.armed: tuple[str | None, str, Callable[[dict[str, Any]], bool]] | None = None
        self.injected: TxnContentionExhaustedError | None = None
        self.flagged_stack: list[str] = []
        self.observed_writers: set[str] = set()
        self.seam_bindings: list[str] = []
        self._shell_stacks: dict[int, list[list[types.FrameType]]] = {}
        # ⚠ DUAL (packet 58 contract r4 — amendment 12 §1, REPORT-contract-58-r4.md §ITEMS 1): r3 fired on the
        # FIRST armed write only (F-D's hidden constant k = 1), stopped observing the seam once it fired (F-C:
        # a retry-then-reraise kept identity), and recorded no FIRED fact (F-NOOP: a declared driver counted
        # as
        # coverage).  r4 adds the STATE: the write index ``k`` the injection fires at, a MEASURE mode that
        # counts
        # the armed-seam writes of an unarmed run (WRITES(R, v) is measured, never assumed), every statement
        # the
        # seam receives AFTER the injection (E2 ∪ E3 — erratum am-8 §3 item 2), and the FIRED triples
        # ``(root, verb, k)`` the seam itself records (the reach ledger).
        self.write_index = 1
        self.measuring = False
        self.matched_writes = 0
        self.statements_after: list[str] = []
        self.fired: list[tuple[str, str, int]] = []
        self.snapshot: Callable[[], Awaitable[Any]] | None = None
        self.snapshot_at_injection: Any = None
        self._after_open = False
        self._quiet = False

    # -- installation ---------------------------------------------------------------------------------------
    def install(self, monkeypatch: pytest.MonkeyPatch, *, observe_shell: bool = True) -> None:
        """Wrap every binding of each driver seam BY IDENTITY, and every shell holder's shell (observed).

        ``observe_shell=False`` (packet 58 amendment 12 §4 item 2 — 63c-i-a a28c decision (4) / F-3): a driver
        for a handler that does not ride the shell installs the identity half ONLY (no shell holder is
        required
        and no writer is attributed) — the ONE install, so a28c's ``_arm_the_driver_seams`` need not reach
        into
        :meth:`_seam_wrapper`."""
        for seam_name in DRIVER_SEAM_NAMES:
            original = getattr(_txn, seam_name)
            wrapper = self._seam_wrapper(seam_name, original)
            for module_name, module in list(sys.modules.items()):
                if module is None or not module_name.startswith("loremaster"):
                    continue
                for attribute, value in list(vars(module).items()):
                    if value is original:
                        monkeypatch.setattr(module, attribute, wrapper)
                        self.seam_bindings.append(f"{module_name}.{attribute}")
        assert any(binding.endswith("_txn.execute_transaction") for binding in self.seam_bindings), (
            f"the injection wrapped no `_txn.execute_transaction` binding: {self.seam_bindings}"
        )
        if not observe_shell:
            return
        holders = 0
        for module_name, module in list(sys.modules.items()):
            if module is None or not module_name.startswith("loremaster"):
                continue
            for value in list(vars(module).values()):
                if inspect.isclass(value) and value.__module__ == module_name and CAS_SHELL in vars(value):
                    self._wrap_shell(monkeypatch, value)
                    holders += 1
        assert holders, f"no class holds the shell `{CAS_SHELL}` — the runtime writer observation is blind"

    def _wrap_shell(self, monkeypatch: pytest.MonkeyPatch, holder: type) -> None:
        descriptor = inspect.getattr_static(holder, CAS_SHELL)
        function = descriptor.__func__ if isinstance(descriptor, (staticmethod, classmethod)) else descriptor
        recorder = self

        def _observed(*args: Any, **kwargs: Any) -> Any:
            recorder._shell_stacks.setdefault(recorder._task_key(), []).append(_stack())
            return function(*args, **kwargs)

        if isinstance(descriptor, staticmethod):
            monkeypatch.setattr(holder, CAS_SHELL, staticmethod(_observed))
        elif isinstance(descriptor, classmethod):
            monkeypatch.setattr(holder, CAS_SHELL, classmethod(_observed))
        else:
            monkeypatch.setattr(holder, CAS_SHELL, _observed)

    @staticmethod
    def _task_key() -> int:
        try:
            return id(asyncio.current_task())
        except RuntimeError:
            return 0

    # -- the seam -------------------------------------------------------------------------------------------
    def _seam_wrapper(self, seam_name: str, original: Callable[..., Awaitable[Any]]) -> Callable[..., Any]:
        recorder = self

        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            # A plain `def`: the stack is walked at CALL time, while the caller's frames are live (the
            # `_sdk_guard` lesson — an `async def` wrapper walks at await time, after they are gone).
            if recorder._quiet:  # the instrument's OWN snapshot reads — never part of the verb's call
                return original(*args, **kwargs)
            stack = _stack()
            if recorder._after_open:
                # am-12 §1 (1): E2 ∪ E3 at the STATE — every statement the seam receives after the injection,
                # from anywhere, until the call returns to the test's boundary (a re-read, a retry, a
                # compensation alike).  Recorded, then allowed to run (the lie must be observable, not
                # masked).
                recorder.statements_after.append(f"{seam_name}: {str(args[0] if args else kwargs)[:160]}")
            recorder._attribute_write(stack)
            if recorder._should_fire(seam_name, stack, args, kwargs):
                injected = TxnContentionExhaustedError(
                    "injected-58r3 exhausted contention at the driver seam", attempts=64, elapsed_seconds=2.0
                )
                recorder.injected = injected
                recorder.flagged_stack = [key for key in map(_frame_key, stack) if key is not None]
                verb = recorder.armed[0] if recorder.armed is not None else None
                recorder.fired.append((_root_of(stack, verb), verb or "<unarmed>", recorder.write_index))

                async def _raise() -> Any:
                    if recorder.snapshot is not None:
                        recorder._quiet = True
                        try:
                            recorder.snapshot_at_injection = await recorder.snapshot()
                        finally:
                            recorder._quiet = False
                    recorder._after_open = True
                    raise injected

                return _raise()
            return original(*args, **kwargs)

        return _wrapped

    def _attribute_write(self, stack: list[types.FrameType]) -> None:
        """Attribute a WRITE to the deepest frame common to its shell stack and its send stack."""
        shell_stacks = self._shell_stacks.pop(self._task_key(), [])
        live = {id(frame) for frame in stack}
        for shell_stack in shell_stacks:
            common = next((frame for frame in shell_stack if id(frame) in live), None)
            key = _frame_key(common) if common is not None else None
            if key is not None:
                self.observed_writers.add(key)

    def arm(
        self,
        verb: str | None,
        *,
        seam: str = "execute_transaction",
        matches: Callable[[dict[str, Any]], bool] = lambda _kwargs: True,
    ) -> None:
        """Fire on the first ``seam`` call made while ``verb`` (``"<file>::<function>"``) is on the stack
        (``None``: on the first ``seam`` call at all — the instrument's own discriminators only)."""
        assert seam in DRIVER_SEAM_NAMES, seam
        self.armed = (verb, seam, matches)
        self.injected = None
        self.flagged_stack = []
        self.matched_writes = 0
        self.statements_after = []
        self.snapshot_at_injection = None
        self._after_open = False

    def _should_fire(
        self, seam_name: str, stack: list[types.FrameType], args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> bool:
        if self.armed is None or self.injected is not None:
            return False
        verb, seam, matches = self.armed
        if seam_name != seam:
            return False
        if verb is not None and verb not in {_frame_key(frame) for frame in stack}:
            return False
        call = dict(kwargs)
        if args:
            call.setdefault("statement", args[0])
        if not matches(call):
            return False
        # am-12 §1 (F-D): the armed write is the k-th MATCHING write of the call, never "the first" — and in
        # MEASURE mode nothing fires; the matching writes are only counted (WRITES(R, v), measured).
        self.matched_writes += 1
        return not self.measuring and self.matched_writes == self.write_index

    def disarm(self) -> None:
        self.armed = None
        self._after_open = False

    async def expect_the_SAME_instance(self, verb: str, call: Callable[[], Awaitable[Any]]) -> None:
        """Run ``call``; the injected instance itself must reach this boundary (am-8 §3 item 2), the seam must
        receive NO further statement after the injection, and nothing may commit after it (am-12 §1 (1)).

        In MEASURE mode (:attr:`measuring`) nothing is injected: the call runs unarmed and
        :attr:`matched_writes` is its WRITES(R, v) — the count every armed leg ``k ∈ 1..n`` is generated
        from."""
        if self.measuring:
            try:
                await call()
            finally:
                self.armed = None
            return
        outcome: object = None
        try:
            outcome = await call()
        except BaseException as reached:  # noqa: BLE001 - the identity check IS the assertion
            assert self.injected is not None, (
                f"{verb}: the injection never fired at write k={self.write_index} — the verb raised "
                f"{reached!r} before reaching its armed driver seam (or never reached it)"
            )
            assert reached is self.injected, (
                f"{verb}: exhausted contention was REINTERPRETED — the caller received "
                f"{type(reached).__name__}({reached}) instead of the injected TxnContentionExhaustedError "
                f"instance.  Our write never committed and the driver gave up; a re-read, a translation or a "
                f"verdict built from it is a story about a race that never happened (#102)."
            )
            self._after_open = False
            assert not self.statements_after, (
                f"{verb} (k={self.write_index}): the seam received {len(self.statements_after)} statement(s) "
                "AFTER the injected exhaustion — a re-read, a retry or a compensation (packet 58 amendment "
                "12 "
                f"§1 (1): statements_after == 0; the driver owns retries, #102): {self.statements_after}"
            )
            if self.snapshot is not None:
                self._quiet = True
                try:
                    after = await self.snapshot()
                finally:
                    self._quiet = False
                assert after == self.snapshot_at_injection, (
                    f"{verb} (k={self.write_index}): the store CHANGED after the injected exhaustion — "
                    f"something committed that the caller is being told did not (am-12 §1, F-C's redundant "
                    f"half: catches a compensation the seam did not see, e.g. a second connection)"
                )
            return
        finally:
            self.disarm()
        assert self.injected is not None, (
            f"{verb}: the injection never fired at write k={self.write_index} (armed seam not reached)"
        )
        raise AssertionError(
            f"{verb}: exhausted contention was SWALLOWED — the call returned {outcome!r} instead of raising "
            f"the injected TxnContentionExhaustedError (a swallow, a local retry that then succeeded, or a "
            f"verdict served from a re-read)"
        )


# --------------------------------------------------------------------------- #
# the DRIVERS — one per 58-owned (or r2-carried) CAS verb: the injection leg + the real lost-race control
# (the controls are r2's `test_reanchor_58_r2_cas_runtime.py` legs, carried verbatim in behaviour).
# --------------------------------------------------------------------------- #

Driver = Callable[[SurrealEnv, TaskLedger, DriverSeamInjection], Awaitable[None]]


async def _drive_task_transition(env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    task_id = await create(ledger, "a row to transition")
    seam.arm("tasks.py::transition")
    await seam.expect_the_SAME_instance(
        "tasks.py::transition", lambda: ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
    )
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: racer.transition(task_id, STATUS_BLOCKED, actor="racer-58r3"))
    try:
        with hook.installed(), pytest.raises(IllegalTransitionError):
            await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
    finally:
        await racer.close()
    assert hook.fired


async def _drive_task_claim(env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    task_id = await create(ledger, "a claimable row")
    seam.arm("tasks.py::claim_task")
    await seam.expect_the_SAME_instance("tasks.py::claim_task", lambda: ledger.claim_task(task_id, CLAIMANT))
    racer = new_ledger(env)

    async def _racer_claims() -> None:
        assert (await racer.claim_task(task_id, "racer-58r3")).claimed

    hook = ApplyHook(ledger, _racer_claims)
    try:
        with hook.installed():
            result = await ledger.claim_task(task_id, CLAIMANT)
    finally:
        await racer.close()
    assert hook.fired and result.claimed is False and result.task.owner == "racer-58r3", result


async def _drive_task_supersede(env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    old = await create(ledger, "X")
    await create(ledger, "Y", [old])
    seam.arm("tasks.py::supersede_task")
    await seam.expect_the_SAME_instance("tasks.py::supersede_task", lambda: supersede(ledger, old))
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: supersede(racer, old))
    try:
        with hook.installed(), pytest.raises(IllegalTransitionError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired


async def _drive_task_heal(env: SurrealEnv, ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    head = await create(ledger, "the successor")
    legacy = "casseamlegacy0000000000000000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    straggler = "casseamstraggler0000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[legacy])
    await raw_relate(ledger, legacy, straggler)  # the backfill mints nothing: the heal's write is the first
    booted = new_ledger(env)
    seam.arm("tasks.py::_reanchor_stragglers")
    try:
        await seam.expect_the_SAME_instance("tasks.py::_reanchor_stragglers", booted.ensure_ready)
    finally:
        await booted.close()
    # CONTROL: a chunk's DOMAIN rejection (a server-side THROW) is the heal's ruled verdict — isolated.
    await raw(
        ledger,
        f"DEFINE EVENT casseam58 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
        f"record::id($after.id) = '{straggler}' THEN {{ THROW 'injected-58r3-domain' }}",
    )
    control = new_ledger(env)
    records: list[logging.LogRecord] = []

    class _Grab(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    grab = _Grab(level=logging.DEBUG)
    logging.getLogger("loremaster").addHandler(grab)
    try:
        await control.ensure_ready()
    finally:
        logging.getLogger("loremaster").removeHandler(grab)
        await control.close()
    assert [r.getMessage() for r in records].count(HEAL_CHUNK_REJECTED_EVENT) == 1


async def _finding_ledger(env: SurrealEnv) -> Any:
    from loremaster.findings import FindingLedger

    findings = FindingLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await findings.ensure_ready()
    return findings


async def _report(findings: Any) -> int:
    result = await findings.report(
        "a finding to race", "body", area="casseam-58r3", category="test", created_by="reporter-58r3"
    )
    return int(result.number)


async def _drive_finding_transition(env: SurrealEnv, _ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    from loremaster.findings import IllegalTransitionError as FindingIllegalTransitionError

    findings = await _finding_ledger(env)
    racer = await _finding_ledger(env)
    try:
        number = await _report(findings)
        seam.arm("findings.py::_transition")
        await seam.expect_the_SAME_instance(
            "findings.py::_transition", lambda: findings.acknowledge(number, "actor-58r3")
        )
        hook = ApplyHook(findings, lambda: racer.resolve(number, "racer-58r3"))
        with hook.installed(), pytest.raises(FindingIllegalTransitionError):
            await findings.wontfix(number, "actor-58r3")
        assert hook.fired
    finally:
        await findings.close()
        await racer.close()


async def _drive_finding_annotate(env: SurrealEnv, _ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    from loremaster.findings import FindingNotFoundError

    findings = await _finding_ledger(env)
    try:
        number = await _report(findings)
        seam.arm("findings.py::annotate")
        await seam.expect_the_SAME_instance(
            "findings.py::annotate", lambda: findings.annotate(number, "actor-58r3", "a note")
        )
        row_id = (await findings.get(number)).id

        async def _vanish() -> None:
            await findings._query("DELETE type::record('finding', $id)", {"id": row_id})  # noqa: SLF001

        hook = ApplyHook(findings, _vanish)
        with hook.installed(), pytest.raises(FindingNotFoundError):
            await findings.annotate(number, "actor-58r3", "a note")
        assert hook.fired
    finally:
        await findings.close()


async def _drive_brief_ack(env: SurrealEnv, _ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    from loremaster.briefs import BriefLedger
    from test_brief_ledger import BODY_V1, _seed_agent_rows

    agent_id = "casseam-agent-58r3"
    await _seed_agent_rows(env, [agent_id])
    briefs = BriefLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await briefs.ensure_ready()
    try:
        version = (await briefs.publish("casseam58r3", BODY_V1, created_by="publisher-58r3")).brief.version
        seam.arm(
            "briefs.py::_relate_briefed",
            seam="run_query",
            matches=lambda call: str(call.get("statement", "")).lstrip().startswith("RELATE"),
        )
        await seam.expect_the_SAME_instance(
            "briefs.py::_relate_briefed",
            lambda: briefs.ack(
                agent_id=agent_id, agent_name="a", name="casseam58r3", version=version, via="explicit"
            ),
        )
        await briefs.ack(agent_id=agent_id, agent_name="a", name="casseam58r3", version=version,
        via="explicit")
        again = await briefs.ack(
            agent_id=agent_id, agent_name="a", name="casseam58r3", version=version, via="explicit"
        )
        assert again.already_acked is True, "CONTROL: a real duplicate RELATE is the idempotent verdict"
    finally:
        await briefs.close()


#: THIS module's slice of the discovered registry (FK-r3-4).  Keys are ``"<file>::<function>"``.
CAS_SEAM_DRIVERS: dict[str, Driver] = {
    "tasks.py::transition": _drive_task_transition,
    "tasks.py::claim_task": _drive_task_claim,
    "tasks.py::supersede_task": _drive_task_supersede,
    "tasks.py::_reanchor_stragglers": _drive_task_heal,
    "findings.py::_transition": _drive_finding_transition,
    "findings.py::annotate": _drive_finding_annotate,
    "briefs.py::_relate_briefed": _drive_brief_ack,
}


def discovered_drivers() -> dict[str, Driver]:
    """EVERY test module's ``CAS_SEAM_DRIVERS`` — found by an AST scan of the test tree (through THE ONE tree
    parser, ``_logging_fixtures.parse_production_trees``) for a module-level assignment to
    :data:`REGISTRY_NAME`, then imported.  A key declared twice reds (one owner per verb)."""
    from _logging_fixtures import _workspace_root, parse_production_trees

    tests_prefix = TESTS_ROOT.resolve().relative_to(_workspace_root().resolve()).as_posix() + "/"
    drivers: dict[str, Driver] = {}
    owners: dict[str, str] = {}
    for relative, tree in sorted(parse_production_trees(include_scripts=False, include_tests=True).items()):
        path = Path(relative)
        if not relative.startswith(tests_prefix) or "/" in relative[len(tests_prefix):]:
            continue
        if not path.name.startswith("test_"):
            continue
        declares = any(
            isinstance(node, (ast.Assign, ast.AnnAssign))
            and any(
                isinstance(target, ast.Name) and target.id == REGISTRY_NAME
                for target in (node.targets if isinstance(node, ast.Assign) else [node.target])
            )
            for node in tree.body
        )
        if not declares:
            continue
        registry = getattr(importlib.import_module(path.stem), REGISTRY_NAME)
        for verb, driver in registry.items():
            assert verb not in owners, f"{verb} has drivers in both {owners[verb]} and {path.name}"
            owners[verb] = path.name
            drivers[verb] = driver
    return drivers


def listed_handlers() -> set[str]:
    """The static index's reviewer-visible lists (58 am-7 §3 item 2: every door AND every typed catch)."""
    index = importlib.import_module("test_retry_seam")
    # ⚠ DUAL (63c-i-a contract a28c, deviation D-5 — REPORT-contract-63c-i-a-a28c.md FK-a28c-6): the index is
    # keyed PER HANDLER now (``<file>::<function>::<n>``, 63c amendment 35 §3); this frame-keyed population
    # maps each entry to its FUNCTION through the index's OWN accessor (the key format is read back in ONE
    # place).
    return {
        index._handler_function(key)  # noqa: SLF001
        for key in (*index._GUARDED_CAS_DOORS, *index._TYPED_CAS_CATCHES)  # noqa: SLF001
    }


def _collection_population() -> list[str]:
    """Graph verbs ∪ listed handlers ∪ driver keys — computed at COLLECTION so each member reds BY NAME."""
    population = set(derive_cas_verbs(PACKAGE_ROOT)) | set(CAS_SEAM_DRIVERS)
    try:
        population |= listed_handlers()
        population |= set(discovered_drivers())
    except Exception as error:  # noqa: BLE001 - a broken index must RED, never shrink the population
        population.add(f"<the static index or the driver discovery failed to load: {error!r}>")
    return sorted(population)


class TestTheCASPopulationIsDrivenBothWays:
    """am-8 §3 item 3 + am-7 §3 item 2: STATIC ⊆ DRIVEN and DRIVEN ⊆ STATIC, per member, by name."""

    @pytest.mark.parametrize("member", _collection_population())
    def test_every_static_CAS_member_has_a_driver_and_every_driver_a_static_member(self, member: str) -> None:
        static = derive_cas_verbs(PACKAGE_ROOT) | listed_handlers()
        drivers = discovered_drivers()
        assert member in drivers, (
            f"{member} is a guarded CAS (call-graph verb or listed handler) that NO injection drives — add a "
            f"`{REGISTRY_NAME}` entry for it in its OWNER's test module (am-7 §3 item 2: a listed handler "
            f"outside packet 58 is routed to its module's owner, never to 58's file)"
        )
        assert member in static, (
            f"{member}'s driver is STALE: neither the call graph (shell + driver seam) nor the static index "
            f"names it — the verb stopped reaching the shell, or the driver names a function that is gone"
        )


class TestExhaustedContentionReachesTheCallerAsTheSAMEInstance:
    """am-8 §3 items 1, 2, 4 — per driver: the identity leg, the control leg, the runtime attribution."""

    @pytest.mark.parametrize("verb", sorted(CAS_SEAM_DRIVERS))
    async def test_the_injected_instance_reaches_the_caller_and_a_real_loss_is_the_ruled_verdict(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, verb: str
    ) -> None:
        ledger, env = ledger58
        seam = DriverSeamInjection()
        seam.install(monkeypatch)
        await CAS_SEAM_DRIVERS[verb](env, ledger, seam)
        assert verb in seam.flagged_stack, (
            f"{verb}: the injection fired under {seam.flagged_stack}, not under the verb it was armed for"
        )
        graph = derive_cas_verbs(PACKAGE_ROOT)
        blind = seam.observed_writers - graph
        assert not blind, (
            f"writers OBSERVED at runtime (deepest frame common to a shell call and its driver-seam send) "
            f"that the call graph did not derive: {sorted(blind)} — the static derivation's blind spot, named"
        )
        if verb in graph:
            assert verb in seam.observed_writers, (
                f"{verb} is a call-graph CAS verb but no write during its driver was attributed to it at "
                f"runtime (observed: {sorted(seam.observed_writers)}) — the graph and the running code "
                f"disagree about who composes this CAS"
            )


# --------------------------------------------------------------------------- #
# the instruments' own discriminators — each shape a builder may legitimately write (am-8 §3: "no instrument
# may dictate the shape") and each wrong shape, over SYNTHETIC sources / fakes.
# --------------------------------------------------------------------------- #

_SYNTHETIC_LEDGER = """
from loremaster.store._txn import execute_transaction
from loremaster.store import _txn as txn_alias


class Ledger:
    @staticmethod
    def _guarded_append_fragment(*a):
        return a

    async def _apply(self, fragments):
        await execute_transaction("BEGIN; COMMIT;", {})

    async def inline_verb(self):
        await self._apply([self._guarded_append_fragment()])

    def _build(self):
        return [self._guarded_append_fragment()]

    async def _commit(self, fragments):
        await txn_alias.execute_transaction("BEGIN; COMMIT;", {})

    async def extracted_verb(self):
        await self._commit(self._build())

    async def public_wrapper(self):
        return await self.inline_verb()

    async def read_only(self):
        await self._apply([])

    def fragment_only(self):
        return self._build()
"""


class TestTheCallGraphDerivationFollowsTheGraphNotTheShape:
    """am-8 §3: the population is the call graph's — the F8 extract-method refactor and the N20 helper-applied
    verb are DERIVED; a public wrapper is not a second verb (MINIMAL, FK-r3-5); a seam-only or shell-only
    function is not a verb.  The seam resolves BY IDENTITY (a module alias counts)."""

    def test_the_synthetic_ledger_derives_exactly_the_minimal_verbs(self) -> None:
        namespace: dict[str, Any] = {}
        exec(compile(_SYNTHETIC_LEDGER, "<synthetic-ledger>", "exec"), namespace)  # noqa: S102
        derived = cas_verbs_in(ast.parse(_SYNTHETIC_LEDGER), namespace)
        assert derived == {"inline_verb", "extracted_verb"}, sorted(derived)

    def test_the_production_derivation_is_not_vacuous(self) -> None:
        derived = derive_cas_verbs(PACKAGE_ROOT)
        assert {"findings.py::_transition", "findings.py::annotate"} <= derived, sorted(derived)


class _FakeVerbs:
    """Fakes that call the REAL seam binding path through a wrapped module attribute."""

    def __init__(self, send: Callable[[], Awaitable[Any]]) -> None:
        self._send = send

    async def passthrough(self) -> None:
        await self._send()

    async def reinterprets(self) -> None:
        try:
            await self._send()
        except _txn.SurrealStoreError as error:
            raise IllegalTransitionError("a lost race") from error

    async def swallows(self) -> str:
        try:
            await self._send()
        except _txn.SurrealStoreError:
            return "lost"
        return "won"


class TestTheIdentityAssertionDiscriminates:
    """The instrument's own positive controls: a passthrough PASSES, a translation and a swallow both FAIL."""

    @staticmethod
    def _armed(monkeypatch: pytest.MonkeyPatch) -> tuple[DriverSeamInjection, _FakeVerbs]:
        seam = DriverSeamInjection()
        seam.install(monkeypatch)
        this = sys.modules[__name__]
        verbs = _FakeVerbs(lambda: this._txn.execute_transaction("BEGIN; COMMIT;", {}))
        return seam, verbs

    async def test_a_passthrough_preserves_identity(self, monkeypatch: pytest.MonkeyPatch) -> None:
        seam, verbs = self._armed(monkeypatch)
        seam.arm(None)
        await seam.expect_the_SAME_instance("fake.passthrough", verbs.passthrough)

    @pytest.mark.parametrize("shape", ["reinterprets", "swallows"])
    async def test_a_reinterpretation_or_a_swallow_is_caught(
        self, monkeypatch: pytest.MonkeyPatch, shape: str
    ) -> None:
        seam, verbs = self._armed(monkeypatch)
        seam.arm(None)
        with pytest.raises(AssertionError, match="REINTERPRETED|SWALLOWED"):
            await seam.expect_the_SAME_instance(f"fake.{shape}", getattr(verbs, shape))
