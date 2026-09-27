"""Contract r2 — packet 64b-i: the finding ledger's slice of packet 58's DISCOVERED driver-seam registry
(packet-64 amendment 8 ``53563e7`` §4 S-4; packet 58 amendment 9 FK-r3-4). Authored by ``contract-64b-r2``
(Opus 5.5 — contract tests ONLY).

WHY THIS FILE EXISTS: 64b-i MERGES the finding ledger's two guarded-CAS rollback handlers (``_transition``'s
and ``annotate``'s) into ONE shell, ``findings.py::_run_guarded``, whose zero-row rollback re-reads through
the SHARED ``governed.classify_zero_row_cas``. 64b owns that change, so 64b owns its consequence (amendment 8
§4 S-4): the finding entries of 58's ``CAS_SEAM_DRIVERS`` registry are declared HERE, in 64b's own module
(58's ``discovered_drivers()`` finds every test module's ``CAS_SEAM_DRIVERS`` by AST; one owner per key).

MEASURED (2026-09-26, the r2 reference on the am-8 SAT base): 58's call-graph derivation
(``derive_cas_verbs`` — the MINIMAL verb reaching both the CAS shell and the driver seam, am-9 FK-r3-5) still
derives ``findings.py::_transition`` and ``findings.py::annotate`` after the merge (the shell fragment is
BUILT in each verb; ``_run_guarded`` only applies it), while the static retry-seam index
(``test_retry_seam._GUARDED_CAS_DOORS`` — keyed by the HANDLER's function) moves to
``findings.py::_run_guarded`` (§HELD Part B item G2). So all THREE keys are static members and each needs a
driver (REPORT-contract-64b-r2 §FORKS FK-r2-9: amendment 8 §4 names ``_run_guarded`` alone).

⚠ DECLARED ≠ RUN (adversary-58-r3 F-NOOP, ``706a1bf``): under 58's committed SEAM a DISCOVERED driver is
COUNTED by the population pin but never EXECUTED (the identity leg is parametrised over 58's in-file dict
only), so the driver below is a declaration until 58 r4 lands the Q-DRIVEN pin (every discovered driver fires
its injection under its verb). The class fix is 58's instrument, not a runner cloned here (copy #2 of the
identity leg). Hence G12 is SEQUENCED: it may move 58's two driven finding drivers into this module ONLY
after Q-DRIVEN has landed — before it, the move would turn two driven verbs into declared ones
(REPORT-contract-64b-r2 §HELD step 4 / BC-r2-13).

THIS COMMIT declares only ``findings.py::_run_guarded`` (the handler 64b creates). 58's module still owns the
``_transition`` / ``annotate`` drivers at HEAD — declaring them here too would RED 58's discovery ("declared
twice"). §HELD Part B item G12 MOVES them here (retiring 58's two entries with a DUAL note) with
identity-bearing bodies: at HEAD they call the ledger with NO Subject, which the 64b build DENIES (a governed
finding write requires a verified identity) — they would red for a reason unrelated to exhaustion.

Every driver: the INJECTION leg (the armed seam's ``TxnContentionExhaustedError`` instance reaches the caller
UNREAD — never re-read into a lost-race or not-found verdict, #102) + the REAL-VERDICT control (a genuine
lost race is the ledger's own ruled verdict). Live TEST store ``:18000`` (NEVER :18500); the ``ledger58``
fixture's database.
"""

from __future__ import annotations

import inspect
import re
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

import pytest
from _reanchor_58_support import ApplyHook

import lorerunes as pdp

if TYPE_CHECKING:
    from _surreal_harness import SurrealEnv
    from loremaster.tasks import TaskLedger
    from test_reanchor_58_r3_cas_seam import DriverSeamInjection

#: ONE Subject for every driver: an exact creator pair on a ``principal-private`` row it owns (no project
#: keep, no household — the drivers exercise the CAS, never the gate). Record links need no live target (the
#: PDP compares ids).
DRIVER_SUBJECT = pdp.Subject(
    principal_id="p64cas", agent_id="a64cas", role=pdp.PRINCIPAL_ROLE_MEMBER, visible_keep_ids=frozenset()
)


async def _finding_ledger(env: SurrealEnv) -> Any:
    from loremaster.findings import FindingLedger  # noqa: PLC0415

    findings = FindingLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    await findings.ensure_ready()
    return findings


async def _report(findings: Any) -> int:
    """A finding the driver's Subject owns — the REAL governed ``report`` (``subject=``, explicit scope)."""
    result = await findings.report(
        title="a finding to race",
        body="body",
        area="casseam-64b",
        category="test",
        created_by="reporter-64b",
        subject=DRIVER_SUBJECT,
        scope=pdp.SCOPE_PRINCIPAL_PRIVATE,
    )
    return int(result.number)


async def _drive_finding_run_guarded(env: SurrealEnv, _ledger: TaskLedger, seam: DriverSeamInjection) -> None:
    """``findings.py::_run_guarded`` — THE merged rollback handler: the injection armed on its frame must
    reach the caller as the SAME instance; CONTROL — a racer's resolve landing between the gate and the CAS
    makes our ``wontfix`` the ledger's own lost-race verdict (``IllegalTransitionError`` naming the fresh
    state)."""
    from loremaster.findings import IllegalTransitionError  # noqa: PLC0415

    findings = await _finding_ledger(env)
    racer = await _finding_ledger(env)
    try:
        number = await _report(findings)
        seam.arm("findings.py::_run_guarded")
        await seam.expect_the_SAME_instance(
            "findings.py::_run_guarded",
            lambda: findings.acknowledge(number, "actor-64b", subject=DRIVER_SUBJECT),
        )
        hook = ApplyHook(findings, lambda: racer.resolve(number, "racer-64b", subject=DRIVER_SUBJECT))
        with hook.installed(), pytest.raises(IllegalTransitionError, match="resolved"):
            await findings.wontfix(number, "actor-64b", subject=DRIVER_SUBJECT)
        assert hook.fired, "CONTROL: the racer never ran (the verb stopped routing through _apply)"
    finally:
        await findings.close()
        await racer.close()


Driver = Callable[["SurrealEnv", "TaskLedger", "DriverSeamInjection"], Awaitable[None]]

#: THIS module's slice of 58's discovered registry (FK-r3-4) — keys ``"<file>::<function>"``. §HELD Part B
#: item G12 adds ``findings.py::_transition`` / ``findings.py::annotate`` here (moved from 58's module,
#: identity-bearing).
CAS_SEAM_DRIVERS: dict[str, Driver] = {
    "findings.py::_run_guarded": _drive_finding_run_guarded,
}


#: The key shape 58's discovery (``discovered_drivers()``, am-9 FK-r3-4) reads: ``"<file>::<function>"``.
_DRIVER_KEY = re.compile(r"findings\.py::[A-Za-z_][A-Za-z0-9_]*")


def test_the_driver_registry_is_well_formed() -> None:
    """GREEN at HEAD and after — the instrument's own shape: every key is ``findings.py::<function>`` (the
    ONE ledger this module owns), and every driver is an ``async def`` of exactly ``(env, ledger, seam)`` —
    the signature 58's identity leg calls (in-file drivers today; every DISCOVERED driver once 58 r4's
    Q-DRIVEN pin lands — until then a discovered driver is declared, not run: adversary-58-r3 F-NOOP). It
    pins the SHAPE only, never that the driver ran. Also what makes this module a COLLECTED test file:
    ``scripts/test_gated_ground.py`` LEG B reds a committed test-shaped ``.py`` no gate collects (measured on
    the r2 SAT tree — the registry-only r2 draft of this file was ungated ground)."""
    assert CAS_SEAM_DRIVERS, "non-vacuity: the registry is empty"
    malformed = sorted(key for key in CAS_SEAM_DRIVERS if not _DRIVER_KEY.fullmatch(key))
    assert not malformed, f"driver keys not of the form findings.py::<function>: {malformed}"
    for key, driver in CAS_SEAM_DRIVERS.items():
        assert inspect.iscoroutinefunction(driver), f"{key}: the driver is not an async def"
        assert len(inspect.signature(driver).parameters) == 3, (
            f"{key}: the driver must take (env, ledger, seam)"
        )
