"""Packet 58 contract r2 — amendment 5 (C): exhausted contention propagates UNREAD from EVERY guarded CAS.

*Every claim in this file is scoped to the tree at ``66868bc`` (branch ``feat/surreal-unification``),
2026-09-26, authored by ``contract-58-r2``.  "RED at HEAD" means RED at that commit.*

Spec: ``docs/design/2026-09-26-packet58-amendment-5.md`` @ ``67bf2cc`` §1 (the RUNTIME ∀) + §3 (the
cross-check with the class-keyed static index, B — the §HELD re-key of ``test_retry_seam.py``).  The
property is *"the code DOES not reinterpret exhausted contention"* — a fact about what RUNS, so it is
pinned by EXECUTION, never by a handler's shape (the instrument lesson, row 7's sibling):

* inject ``TxnContentionExhaustedError`` at the verb's ONE CAS seam (``_apply``; the brief ack's RELATE
  ``_query``) → the typed error reaches the caller UNCHANGED, the seam is called ONCE (never retried in
  the ledger), and ZERO store reads follow the injection (never re-read, never reinterpreted);
* CONTROL, per verb: a REAL lost race (a racer commits first, the verb's own THROW rolls back) → the
  verb's RULED verdict (claim: ``ClaimResult(claimed=False)``; transition / supersede / finding
  transition: ``IllegalTransitionError``; annotate: ``FindingNotFoundError``; brief ack:
  ``already_acked``; the boot heal: an isolated chunk WARNING) — so the seam CAN see a rollback.

REACH is a CHECKED VARIABLE (INSTRUMENT-0): the driven set is DERIVED
(``_reanchor_58_support.derive_cas_verbs`` — every shell-ledger method that calls ``_apply`` and reaches
the shell, ∪ the named single-statement door) and must EQUAL the driver registry below, both ways: a
derived verb with no driver reds by NAME (57's ``assign`` cannot arrive undriven); a driver whose verb
is not derived is a STALE fixture and reds.  RED at HEAD: ``tasks.py`` has no shell yet, so its four
drivers are stale against the derived set.

⚠ Cross-packet: 64b-i's build reshapes ``findings.py`` (``_transition`` + ``annotate`` → one guarded
runner, identity kwargs).  The derived set follows it automatically; this registry's findings DRIVERS do
not — 64b's builder re-keys them (flagged in ``REPORT-contract-58-r2.md`` §FLAGS).
"""

from __future__ import annotations

import importlib
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import TYPE_CHECKING, Any

import pytest
from _reanchor_58_support import (
    CLAIMANT,
    WORKER,
    ApplyHook,
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
from loremaster.store._txn import TxnContentionExhaustedError
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_BLOCKED, IllegalTransitionError, TaskLedger

if TYPE_CHECKING:
    # ⚠ packet 58's RULED, not-yet-built symbol, named STATICALLY for the typecheck gate (lead directive
    # #17055, the #461 shape): until the build lands the shell this is a mypy error OWNED by
    # `scripts/pending_contracts.yaml` bound `packet-58-contract`, which owns this file's RED@HEAD pytest legs
    # too and self-destructs with the build.  Runtime-inert: no pin changed.
    _RULED_58: tuple[object, ...] = (TaskLedger._guarded_append_fragment,)

__all__ = ["ledger58"]

PACKAGE_ROOT = Path(importlib.import_module("loremaster").__file__ or "").parent
HEAL_CHUNK_REJECTED_EVENT = "task.backfill.straggler_chunk_rejected"


def _exhaustion() -> TxnContentionExhaustedError:
    return TxnContentionExhaustedError("injected-58r2 exhausted contention", attempts=64, elapsed_seconds=2.0)


class Injection:
    """Raise exhausted contention at the FIRST matching call of ``seam`` on ``target``, then COUNT every
    later call of ``seam`` (a retry) and of ``_query`` (a read).  ``armed`` gates the injection so a verb
    whose pre-reads use the same seam (the brief ack) is faulted only at its CAS statement."""

    def __init__(self, target: Any, seam: str, matches: Callable[..., bool] = lambda *a, **k: True) -> None:
        self.target = target
        self.seam = seam
        self.matches = matches
        self.fired = False
        self.seam_calls_after = 0
        self.reads_after = 0
        self._originals: dict[str, Any] = {}

    def install(self, monkeypatch: pytest.MonkeyPatch) -> None:
        names = {self.seam, "_query"}
        for name in names:
            original = getattr(self.target, name)
            self._originals[name] = original
            monkeypatch.setattr(self.target, name, self._wrap(name, original))

    def _wrap(self, name: str, original: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        async def _call(*args: Any, **kwargs: Any) -> Any:
            if self.fired:
                if name == self.seam:
                    self.seam_calls_after += 1
                if name == "_query":
                    self.reads_after += 1
            elif name == self.seam and self.matches(*args, **kwargs):
                self.fired = True
                raise _exhaustion()
            return await original(*args, **kwargs)

        return _call

    def assert_unread(self, verb: str) -> None:
        assert self.fired, f"{verb}: the injection never fired — the verb did not reach its CAS seam"
        assert self.seam_calls_after == 0, (
            f"{verb}: the CAS seam was called {self.seam_calls_after} more time(s) after exhausted "
            f"contention — the LEDGER retried (the driver owns retries; #102)"
        )
        assert self.reads_after == 0, (
            f"{verb}: {self.reads_after} store read(s) followed exhausted contention — our write never "
            f"committed, so whatever the store holds is somebody else's; re-reading it is the first step "
            f"of reinterpreting it (amendment 5 §1, the #102 invariant)"
        )


# --------------------------------------------------------------------------- #
# the DRIVERS — one per derived CAS verb.  Each: (1) the injection leg, (2) the REAL lost-race control.
# --------------------------------------------------------------------------- #


async def _drive_task_transition(env: SurrealEnv, ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    task_id = await create(ledger, "a row to transition")
    injection = Injection(ledger, "_apply")
    with mp.context() as scoped:
        injection.install(scoped)
        with pytest.raises(TxnContentionExhaustedError):
            await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
    injection.assert_unread("tasks.py::transition")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: racer.transition(task_id, STATUS_BLOCKED, actor="racer-58r2"))
    try:
        with hook.installed(), pytest.raises(IllegalTransitionError):
            await ledger.transition(task_id, STATUS_BLOCKED, actor=WORKER)
    finally:
        await racer.close()
    assert hook.fired


async def _drive_task_claim(env: SurrealEnv, ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    task_id = await create(ledger, "a claimable row")
    injection = Injection(ledger, "_apply")
    with mp.context() as scoped:
        injection.install(scoped)
        with pytest.raises(TxnContentionExhaustedError):
            await ledger.claim_task(task_id, CLAIMANT)
    injection.assert_unread("tasks.py::claim_task")
    racer = new_ledger(env)

    async def _racer_claims() -> None:
        assert (await racer.claim_task(task_id, "racer-58r2")).claimed

    hook = ApplyHook(ledger, _racer_claims)
    try:
        with hook.installed():
            result = await ledger.claim_task(task_id, CLAIMANT)
    finally:
        await racer.close()
    assert hook.fired and result.claimed is False and result.task.owner == "racer-58r2", result


async def _drive_task_supersede(env: SurrealEnv, ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    old = await create(ledger, "X")
    await create(ledger, "Y", [old])
    injection = Injection(ledger, "_apply")
    with mp.context() as scoped:
        injection.install(scoped)
        with pytest.raises(TxnContentionExhaustedError):
            await supersede(ledger, old)
    injection.assert_unread("tasks.py::supersede_task")
    racer = new_ledger(env)
    hook = ApplyHook(ledger, lambda: supersede(racer, old))
    try:
        with hook.installed(), pytest.raises(IllegalTransitionError):
            await supersede(ledger, old)
    finally:
        await racer.close()
    assert hook.fired


async def _drive_task_heal(env: SurrealEnv, ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    head = await create(ledger, "the successor")
    legacy = "casrtlegacyblocker00000000000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    straggler = "casrtstraggler000000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[legacy])
    await raw_relate(ledger, legacy, straggler)  # the backfill mints nothing: the heal's apply is the first
    booted = new_ledger(env)
    injection = Injection(booted, "_apply")
    with mp.context() as scoped:
        injection.install(scoped)
        try:
            with pytest.raises(TxnContentionExhaustedError):
                await booted.ensure_ready()
        finally:
            await booted.close()
    injection.assert_unread("tasks.py::_reanchor_stragglers")
    # CONTROL: a chunk's DOMAIN rejection (a server-side THROW) is the heal's ruled verdict — isolated.
    await raw(
        ledger,
        f"DEFINE EVENT casrt58 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
        f"record::id($after.id) = '{straggler}' THEN {{ THROW 'injected-58r2-domain' }}",
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


async def _drive_finding_transition(env: SurrealEnv, _ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    findings = await _finding_ledger(env)
    racer = await _finding_ledger(env)
    try:
        number = await _report(findings)
        injection = Injection(findings, "_apply")
        with mp.context() as scoped:
            injection.install(scoped)
            with pytest.raises(TxnContentionExhaustedError):
                await findings.acknowledge(number, "actor-58r2")
        injection.assert_unread("findings.py::_transition")
        from loremaster.findings import IllegalTransitionError as FindingIllegalTransitionError

        hook = ApplyHook(findings, lambda: racer.resolve(number, "racer-58r2"))
        with hook.installed(), pytest.raises(FindingIllegalTransitionError):
            await findings.wontfix(number, "actor-58r2")
        assert hook.fired
    finally:
        await findings.close()
        await racer.close()


async def _drive_finding_annotate(env: SurrealEnv, _ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    from loremaster.findings import FindingNotFoundError

    findings = await _finding_ledger(env)
    try:
        number = await _report(findings)
        injection = Injection(findings, "_apply")
        with mp.context() as scoped:
            injection.install(scoped)
            with pytest.raises(TxnContentionExhaustedError):
                await findings.annotate(number, "actor-58r2", "a note")
        injection.assert_unread("findings.py::annotate")
        row_id = (await findings.get(number)).id

        async def _vanish() -> None:
            await findings._query("DELETE type::record('finding', $id)", {"id": row_id})  # noqa: SLF001

        hook = ApplyHook(findings, _vanish)
        with hook.installed(), pytest.raises(FindingNotFoundError):
            await findings.annotate(number, "actor-58r2", "a note")
        assert hook.fired
    finally:
        await findings.close()


async def _drive_brief_ack(env: SurrealEnv, _ledger: TaskLedger, mp: pytest.MonkeyPatch) -> None:
    from loremaster.briefs import BriefLedger
    from test_brief_ledger import BODY_V1, _seed_agent_rows

    agent_id = "casrt-agent-58r2"
    await _seed_agent_rows(env, [agent_id])
    briefs = BriefLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await briefs.ensure_ready()
    try:
        published = await briefs.publish("casrt58r2", BODY_V1, created_by="publisher-58r2")
        version = published.brief.version
        injection = Injection(
            briefs, "_query", matches=lambda statement, *a, **k: str(statement).lstrip().startswith("RELATE")
        )
        with mp.context() as scoped:
            injection.install(scoped)
            with pytest.raises(TxnContentionExhaustedError):
                await briefs.ack(
                    agent_id=agent_id, agent_name="a", name="casrt58r2", version=version, via="explicit"
                )
        # the RELATE seam IS `_query`: a later `_query` is both a retry and a read — assert it directly.
        assert injection.fired and injection.reads_after == 0, (
            f"briefs.py::_relate_briefed re-read ({injection.reads_after} `_query` call(s)) after exhausted "
            f"contention"
        )
        await briefs.ack(agent_id=agent_id, agent_name="a", name="casrt58r2", version=version, via="explicit")
        again = await briefs.ack(
            agent_id=agent_id, agent_name="a", name="casrt58r2", version=version, via="explicit"
        )
        assert again.already_acked is True, "CONTROL: a real duplicate RELATE is the idempotent verdict"
    finally:
        await briefs.close()


async def _finding_ledger(env: SurrealEnv) -> Any:
    from loremaster.findings import FindingLedger

    findings = FindingLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await findings.ensure_ready()
    return findings


async def _report(findings: Any) -> int:
    result = await findings.report(
        "a finding to race", "body", area="casrt-58r2", category="test", created_by="reporter-58r2"
    )
    return int(result.number)


#: THE registry: one driver per derived CAS verb.  Keys are compared to ``derive_cas_verbs`` BOTH ways.
DRIVERS: dict[str, Callable[[SurrealEnv, TaskLedger, pytest.MonkeyPatch], Awaitable[None]]] = {
    "tasks.py::transition": _drive_task_transition,
    "tasks.py::claim_task": _drive_task_claim,
    "tasks.py::supersede_task": _drive_task_supersede,
    "tasks.py::_reanchor_stragglers": _drive_task_heal,
    "findings.py::_transition": _drive_finding_transition,
    "findings.py::annotate": _drive_finding_annotate,
    "briefs.py::_relate_briefed": _drive_brief_ack,
}


class TestTheDrivenSetIsTheDerivedSet:
    """RED at HEAD (``tasks.py`` has no shell — its four drivers are STALE against the derived set)."""

    def test_every_derived_CAS_verb_has_a_driver_and_every_driver_a_derived_verb(self) -> None:
        derived = derive_cas_verbs(PACKAGE_ROOT)
        assert set(DRIVERS) == derived, (
            f"derived CAS verbs with NO driver: {sorted(derived - set(DRIVERS))} (a new guarded CAS arrived "
            f"undriven — add its injection fixture); drivers for NO derived verb: "
            f"{sorted(set(DRIVERS) - derived)} (a stale fixture — or the shell a verb routes through is "
            f"missing)"
        )


class TestExhaustedContentionPropagatesUNREADFromEveryCASVerb:
    """∀ derived CAS verbs (amendment 5 §1): the injection leg + the real lost-race control.  A verb
    derived but undriven reds HERE by name too (the parametrisation is the DERIVED set)."""

    @pytest.mark.parametrize("verb", sorted(derive_cas_verbs(PACKAGE_ROOT) | set(DRIVERS)))
    async def test_the_typed_error_propagates_unread_and_a_real_loss_is_the_ruled_verdict(
        self, ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch, verb: str
    ) -> None:
        ledger, env = ledger58
        assert verb in DRIVERS, f"{verb} is a derived CAS verb with no runtime driver"
        assert verb in derive_cas_verbs(PACKAGE_ROOT), f"{verb}'s driver is stale: not a derived CAS verb"
        await DRIVERS[verb](env, ledger, monkeypatch)


class TestTheRuntimeSetAndTheStaticIndexAgree:
    """Amendment 5 §3 — the cross-check, both directions, against the §HELD class-keyed index
    (``test_retry_seam._GUARDED_CAS_DOORS`` / ``_TYPED_CAS_CATCHES`` / ``_classified_cas_handlers``).
    RED until §HELD lands the re-keyed index (the names are imported at CALL time, never at collection —
    finding #133: an import error at collection deletes pins instead of failing them)."""

    def test_every_statically_listed_handler_is_runtime_driven_and_every_driven_verb_is_indexed(self) -> None:
        index = importlib.import_module("test_retry_seam")
        listed = set(index._GUARDED_CAS_DOORS) | set(index._TYPED_CAS_CATCHES)
        classified = set(index._classified_cas_handlers()["doors"]) | set(
            index._classified_cas_handlers()["typed"]
        )
        assert listed <= set(DRIVERS), (
            f"(B)-listed handlers no injection drives: {sorted(listed - set(DRIVERS))}"
        )
        assert set(DRIVERS) <= classified, (
            f"(C)-driven verbs whose try/except the static index did not classify: "
            f"{sorted(set(DRIVERS) - classified)} — the scanner's reach, measured by the runtime set"
        )
