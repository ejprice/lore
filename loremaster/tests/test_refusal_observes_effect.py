"""CONTRACT (RED at authoring) — finding #295 / INSTRUMENT D (AUTH-INDEPENDENT half).

A pin that asserts "the call was refused" MUST observe the EFFECT (the guarded body did not
run), never a PROXY (the raised exception / the rendered refusal marker). Design:
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §3 INSTRUMENT D + fork F2;
finding #295.

------------------------------------------------------------------------------
THE DEFECT THIS EXISTS TO KILL (finding #295 / WB48, measured, all pins green)

A guard that performs the action and THEN refuses is byte-identical, at every PROXY
observation point, to one that refuses first. WB48 placed the posture guard AFTER
``super().call_tool``: the refusal marker in the response body was byte-identical to the
correct build's, and the mutating tool's body had ALREADY executed. Paired receipt: correct
build ``invocations=0``, WB48 ``invocations=1`` — same bytes, opposite reality. Every one of
55 posture pins observed the marker (the proxy) and passed both.

    THE ASKABLE FORM (finding #295, promoted to INSTRUMENT 0):
        "If the guard ran AFTER the thing it guards, would this pin still pass?"
    If yes, the pin observes the exception/marker, not the effect.

------------------------------------------------------------------------------
THE FIX — ONE shared helper every refusal/posture pin CALLS, so the effect check is ONE
implementation, not re-hand-rolled per pin (which is how WB48 slipped: a new pin with its own
weaker observation). The deliverables this contract pins (the BUILDER creates them; here they
are imported, so this contract is RED — "helper absent" — until they exist):

    async def assert_tool_refused_and_did_not_run(
        call, tool_name, args, *, effect_count, refusal_marker) -> str
        # 1. drives the REAL wire via the BOUNDARY CALLABLE ONLY: `await call(tool_name, args)`,
        #    where `call` IS `WireSession.call`. The helper is handed the CALLABLE, never the
        #    whole session — so `wire.mcp.call_tool(...)` (the WB30 / D-WB2 in-process door, dead
        #    on the wire, indistinguishable from a live guard at every proxy point) is
        #    UNREPRESENTABLE BY CONSTRUCTION, not merely pinned (finding #346 / D R4, §9.2).
        # 2. WEAK leg  — assert refusal_marker in body   (it WAS refused; present, insufficient)
        # 3. STRONG leg — assert effect_count() == 0      (the guarded body did NOT run)
        #    `effect_count` is the pluggable EFFECT observer: an invocation counter, an
        #    unchanged store, an absent row (finding #295 lists all three). It is the one thing
        #    that legitimately varies per tool; the assertion STRUCTURE is shared.
        #
        # AND its module is brought UNDER R16's wire-discipline scan (test_wire_discipline —
        # `posture_modules()`), whose RECEIVER-BLIND AST check mechanically forbids any
        # `<anything>.call_tool(...)` in the helper's body — a second, independent closure of
        # the D-WB2 door that also governs packet 39's future consumers of this helper. The
        # builder must extend R16's `posture_modules()` reach to include the helper's module
        # (see the reach pin below; recorded in the cycle report).

    def assert_sweep_reached_every_refusal_pin(derived, observed) -> None
        # coverage-as-a-checked-variable for the one-time sweep: fail-closed on an empty
        # `derived` set (anti-vacuity), and RED if any derived pin was not observed.

------------------------------------------------------------------------------
SCOPE — AUTH-INDEPENDENT ONLY (operator, this session). This contract does NOT touch auth,
the posture guard, or the #333 WIP. Its controls model the WB48 shape with SYNTHETIC tools on
the auth-free LOOPBACK wire: the "refusal" is a rendered marker returned by the tool body, and
the "effect" is a per-tool counter — exactly the proxy-vs-effect distinction, constructed
without a posture. The STRUCTURAL answer (gate registration/visibility so there is no "after")
is packet 39's; packet 39's posture pins must CONSUME this helper. (Mechanism measured this
cycle, probe_d: over the loopback wire both builds return the byte-identical marker; only the
counter separates ``0`` from ``1``.)
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from _auth_fixtures import wire_session
from mcp.types import ToolAnnotations

# A distinctive rendered "refusal" marker — the PROXY. Distinctive so the weak leg cannot pass
# on an unrelated success string. Both synthetic builds return it byte-for-byte.
PROBE_MARKER = "REFUSED-BY-CONTRACT-PROBE-CD"

REFUSE_FIRST_TOOL = "lore_probe_refuse_first_cd"
RUN_THEN_REFUSE_TOOL = "lore_probe_run_then_refuse_cd"


@dataclass
class _EffectCounter:
    """A stand-in for a guarded side effect (a store write, a ledger mint).

    ``count`` is what an EFFECT observer reads: ``0`` means the body never ran. A real posture
    pin would instead observe an unchanged store / an absent row — the same shape.
    """

    count: int = 0

    def bump(self) -> None:
        self.count += 1


@dataclass
class _ProbeTools:
    """The two synthetic builds, sharing the loopback wire — see :func:`_probe_session`."""

    wire: Any
    refuse_first_effect: _EffectCounter = field(default_factory=_EffectCounter)
    run_then_refuse_effect: _EffectCounter = field(default_factory=_EffectCounter)


@contextlib.asynccontextmanager
async def _probe_session(tmp_path: Path) -> AsyncIterator[_ProbeTools]:
    """Open an AUTH-FREE loopback wire session carrying the two synthetic builds.

    * ``REFUSE_FIRST_TOOL`` — the CORRECT build: renders the refusal marker WITHOUT running its
      effect (counter stays 0).
    * ``RUN_THEN_REFUSE_TOOL`` — the WRONG build (WB48): runs its effect (counter -> 1), THEN
      renders a BYTE-IDENTICAL marker.

    Reuses ``_auth_fixtures.wire_session`` (ONE IMPLEMENTATION — the SDK-client-over-ASGI wire
    harness), on ``posture="loopback", principal=None`` (no auth, no posture, no #333 symbol).
    """
    effects = _ProbeTools(wire=None)

    def _prepare(mcp: Any) -> None:
        def probe_refuse_first() -> str:
            """Correct build: render the refusal marker; the effect never happens."""
            return PROBE_MARKER

        def probe_run_then_refuse() -> str:
            """Wrong build (WB48): run the effect, THEN render a byte-identical marker."""
            effects.run_then_refuse_effect.bump()
            return PROBE_MARKER

        # PACKET 59: fastmcp's add_tool is single-arg; the metadata rides the mcp.tool(...)
        # decorator applied to the fn (coupling #2 / design D6).
        mcp.tool(
            name=REFUSE_FIRST_TOOL,
            annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
        )(probe_refuse_first)
        mcp.tool(
            name=RUN_THEN_REFUSE_TOOL,
            annotations=ToolAnnotations(readOnlyHint=False, openWorldHint=False),
        )(probe_run_then_refuse)

    async with wire_session(
        tmp_path, posture="loopback", principal=None, prepare=_prepare
    ) as wire:
        effects.wire = wire
        yield effects


def _import_effect_helper() -> Any:
    """Lazily import the effect-observing helper (RED "helper absent" until it exists)."""
    try:
        from _refusal_effect import assert_tool_refused_and_did_not_run  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - the RED state at authoring
        pytest.fail(
            "finding #295 deliverable ABSENT: expected a shared "
            "`assert_tool_refused_and_did_not_run(call, tool_name, args, *, effect_count, "
            "refusal_marker)` (suggested home `_refusal_effect.py` — see the cycle's report) "
            "handed ONLY the boundary callable `call` (= WireSession.call), which drives the "
            "WIRE via `await call(tool_name, args)` and observes the EFFECT (effect_count() == "
            "0), not the rendered marker. It is NOT handed the whole session, so the in-process "
            f"`wire.mcp.call_tool` door (D-WB2 / #346) is unrepresentable. ({exc})"
        )
    return assert_tool_refused_and_did_not_run


def _import_coverage_check() -> Any:
    """Lazily import the sweep coverage-as-a-checked-variable primitive."""
    try:
        from _refusal_effect import assert_sweep_reached_every_refusal_pin  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - the RED state at authoring
        pytest.fail(
            "finding #295 sweep-coverage deliverable ABSENT: expected "
            "`assert_sweep_reached_every_refusal_pin(derived, observed)` — fail-closed on an "
            f"empty derived set, RED if any derived refusal pin was not observed. ({exc})"
        )
    return assert_sweep_reached_every_refusal_pin


# --------------------------------------------------------------------------- #
# The effect-observing helper: passes the correct build, fails the WB48 wrong build.
# --------------------------------------------------------------------------- #


async def test_the_helper_passes_a_refuse_first_build(tmp_path: Path) -> None:
    """NEGATIVE control (correct build): refused on the wire AND the effect never ran.

    Proves the helper does not reject honest refusals — a gate that flags everything is a gate
    that gets switched off.
    """
    assert_refused = _import_effect_helper()
    async with _probe_session(tmp_path) as probe:
        body = await assert_refused(
            probe.wire.call,  # R4: ONLY the boundary callable, never the whole session
            REFUSE_FIRST_TOOL,
            {},
            effect_count=lambda: probe.refuse_first_effect.count,
            refusal_marker=PROBE_MARKER,
        )
    assert PROBE_MARKER in body, "the correct build must still render the refusal marker"
    assert probe.refuse_first_effect.count == 0, (
        "the correct build's effect must not have run"
    )


async def test_the_helper_fails_a_run_then_refuse_build_on_the_effect_leg(
    tmp_path: Path,
) -> None:
    """POSITIVE control (WB48 wrong build): refusal marker present, but the effect RAN.

    The helper MUST raise ``AssertionError`` — and specifically on the EFFECT leg (the message
    must name the effect / running), never merely on a missing marker. This is the entire point
    of #295: a proxy-observing pin passes this build; an effect-observing pin fails it. WRONG
    HELPER THIS KILLS: one that asserts only ``marker in body`` (it would pass this build).
    """
    assert_refused = _import_effect_helper()
    async with _probe_session(tmp_path) as probe:
        with pytest.raises(AssertionError) as excinfo:
            await assert_refused(
                probe.wire.call,  # R4: ONLY the boundary callable, never the whole session
                RUN_THEN_REFUSE_TOOL,
                {},
                effect_count=lambda: probe.run_then_refuse_effect.count,
                refusal_marker=PROBE_MARKER,
            )
        # The effect DID run over the wire — proving the helper drove the real dispatch path.
        assert probe.run_then_refuse_effect.count == 1, (
            "precondition: the wrong build's effect must have run exactly once over the wire"
        )
    message = str(excinfo.value).lower()
    assert "effect" in message or "run" in message or "invocation" in message, (
        "the helper raised, but its message does not identify the EFFECT leg as the failure — "
        f"it may be failing on the marker (the proxy) instead. Message: {excinfo.value!r}"
    )


async def test_a_marker_only_proxy_cannot_distinguish_the_two_builds(
    tmp_path: Path,
) -> None:
    """THE #295 PROOF: the proxy is blind; only the effect discriminates.

    Both builds return the marker BYTE-IDENTICALLY, so the proxy check (``marker in body``)
    passes for BOTH — it cannot tell the correct build from the one whose effect already ran.
    The effect counter is what separates ``0`` from ``1``. This is why an
    exception/marker-observing refusal pin is not a refusal pin at all.
    """
    async with _probe_session(tmp_path) as probe:
        correct_body = await probe.wire.call(REFUSE_FIRST_TOOL, {})
        wrong_body = await probe.wire.call(RUN_THEN_REFUSE_TOOL, {})

    # The proxy an exception/marker-observing pin would use.
    def proxy_says_refused(body: str) -> bool:
        return PROBE_MARKER in body

    assert correct_body == wrong_body, (
        "the two builds' rendered bodies must be byte-identical for this proof to hold; "
        f"correct={correct_body!r} wrong={wrong_body!r}"
    )
    assert proxy_says_refused(correct_body) and proxy_says_refused(wrong_body), (
        "the proxy must pass BOTH builds — that is precisely its blindness"
    )
    assert probe.refuse_first_effect.count == 0, "correct build: effect must not have run"
    assert probe.run_then_refuse_effect.count == 1, "wrong build: effect must have run"
    # The ONLY signal that separates them is the effect, not the proxy.
    assert probe.refuse_first_effect.count != probe.run_then_refuse_effect.count, (
        "the effect observation must distinguish the builds the proxy could not"
    )


# --------------------------------------------------------------------------- #
# MP-1 / #346 — the WIRE-driving claim is VERIFIED, not merely asserted in a docstring.
# Two independent closures of the D-WB2 in-process door: (R4) the helper is handed only the
# boundary callable, so the DIRECT `.mcp` handle is unreachable — the `call.__self__.mcp`
# back-door is NOT closed by construction here, it is closed by (R16), the helper's module being
# under `test_wire_discipline`'s receiver-blind scan, which forbids `<any>.call_tool(...)`.
# The two legs together cover the door; neither alone does (reviser-cd R1).
# --------------------------------------------------------------------------- #


async def test_the_helper_is_handed_only_the_boundary_callable_so_the_in_process_door_is_unrepresentable(
    tmp_path: Path,
) -> None:
    """R4 STRONGEST FORM (finding #346, IDIOM 2 §9.2): the in-process door is UNREPRESENTABLE.

    D-WB2 dispatched via ``wire.mcp.call_tool`` — dead on the wire, byte-identical to a live
    guard at every proxy point (that is why the docstring-only WIRE claim let it pass all six
    pins). The strongest fix does not merely PIN that door shut; it removes the handle: the
    helper is handed ONLY the boundary callable (``WireSession.call``), which exposes no
    ``.mcp``, so the DIRECT ``wire.mcp.call_tool(...)`` cannot be written. This pins the helper's
    USAGE — it is driven with only the callable, and that callable carries no in-process dispatch
    handle.

    ⚠ BOUND (reviser-cd R1): R4 removes the DIRECT handle only. A bound method's ``__self__`` still
    reaches the session, so ``call.__self__.mcp.call_tool(...)`` remains writable and is NOT closed
    "by construction" here — it is closed by the R16 receiver-blind scan leg (which flags any
    ``.call_tool(...)`` in this module regardless of receiver). The two legs together cover the
    door; the ``hasattr(call, "mcp")`` check below is only R4's half.

    WRONG BUILD THIS KILLS: a helper whose first parameter is the whole ``WireSession`` (so it
    COULD reach ``.mcp``) — handed ``probe.wire.call`` here, such a build does ``wire.call`` on a
    bound method and ``AttributeError``s. A helper that takes only ``call`` and awaits it passes.
    """
    assert_refused = _import_effect_helper()
    async with _probe_session(tmp_path) as probe:
        call = probe.wire.call
        assert not hasattr(call, "mcp"), (
            "the boundary callable handed to the helper must expose no `.mcp` — otherwise the "
            "in-process dispatch handle (the D-WB2 door) is reachable, not merely pinned"
        )
        body = await assert_refused(
            call,
            REFUSE_FIRST_TOOL,
            {},
            effect_count=lambda: probe.refuse_first_effect.count,
            refusal_marker=PROBE_MARKER,
        )
    assert PROBE_MARKER in body, (
        "the correct build must still refuse over the wire when handed only the callable"
    )
    assert probe.refuse_first_effect.count == 0, (
        "the correct build's effect must not have run — driven through only the callable"
    )


@pytest.mark.skip(
    reason="RETIRED by packet 59 (fastmcp 3.x migration): R16's `test_wire_discipline."
    "posture_modules()` is GONE — the wire-only discipline's `_setup_handlers` derivation "
    "dissolved with the mcp-SDK subclass, so test_wire_discipline is now a superseded-header "
    "tombstone. Per design §7, PACKET 39 re-expresses the wire-only invariant over the "
    "`on_call_tool`/`on_list_tools` middleware substrate this migration delivers, and re-cuts "
    "this reach pin against it. Un-skip when packet 39 re-expresses posture_modules()."
)
def test_the_effect_helper_module_is_within_R16_wire_discipline_reach() -> None:
    """R16 REACH (finding #346): the effect-helper's module is UNDER the wire-discipline scan.

    ``test_wire_discipline``'s R16 invariant (``posture_modules()`` → a RECEIVER-BLIND AST scan)
    already mechanically forbids any ``<anything>.call_tool(...)`` in the modules it governs —
    the exact D-WB2 in-process door. Rather than clone that scan here (that would be a second
    implementation of R16 — the DRY defect this whole cycle exists to kill), this contract
    REUSES it: it imports R16's own site-enumeration and asserts the effect-helper's module is a
    member, so R16's scan (mutation-proven, positive-controlled, in ``testpaths``) covers the
    helper the day the builder brings it under reach. Packet 39 CONSUMES this helper for its
    posture pins, so the reach must hold for its future callers too.

    RED until the builder EXTENDS R16's ``posture_modules()`` reach to include the effect-helper
    module (``_refusal_effect.py`` does not match ``POSTURE_MODULE_GLOB`` = ``test_*posture*.py``
    at HEAD). That extension is the builder's leg on ``test_wire_discipline`` (outside THIS
    reviser's writable set) — RECORDED in REPORT-reviser-cd.md. Do NOT clone R16's scan to make
    this pin green.
    """
    assert_refused = _import_effect_helper()
    import inspect  # noqa: PLC0415
    from pathlib import Path as _Path  # noqa: PLC0415

    # PACKET 59: ``posture_modules`` was retired with the test_wire_discipline tombstone; this
    # whole test is skipped (see the decorator) until packet 39 re-expresses R16 (design §7).
    from test_wire_discipline import posture_modules  # type: ignore[attr-defined]  # noqa: PLC0415

    helper_module = _Path(inspect.getfile(assert_refused)).resolve()
    covered = {module.resolve() for module in posture_modules()}
    assert helper_module in covered, (
        f"the effect-helper's module {helper_module.name!r} is NOT within R16's wire-discipline "
        f"reach (`test_wire_discipline.posture_modules()`); R16's receiver-blind scan therefore "
        f"cannot forbid the D-WB2 in-process `wire.mcp.call_tool` door in it. Extend R16's "
        f"`posture_modules()`/glob to include the effect-helper's module (builder leg — see "
        f"REPORT-reviser-cd.md). Currently covered: {sorted(p.name for p in covered)}"
    )


# --------------------------------------------------------------------------- #
# The one-time sweep's coverage is itself a CHECKED VARIABLE (honest about its reach).
# --------------------------------------------------------------------------- #


def test_coverage_passes_when_the_sweep_observed_every_derived_pin() -> None:
    """The negative-space control: an honest sweep (observed ⊇ derived) is accepted."""
    coverage = _import_coverage_check()
    derived = frozenset({"pin_a", "pin_b", "pin_c"})
    observed = frozenset({"pin_a", "pin_b", "pin_c"})
    coverage(derived, observed)  # must not raise


def test_coverage_fails_when_a_derived_pin_was_not_observed() -> None:
    """COVERAGE AS A CHECKED VARIABLE: a derived refusal pin the sweep did not route is RED.

    This is the exact class the instrument exists to stop — a refusal pin the effect-sweep
    silently never reached (the reach written as a hidden constant). The failure must NAME the
    missed pin, not merely fail.
    """
    coverage = _import_coverage_check()
    derived = frozenset({"pin_a", "pin_b", "pin_c", "pin_d"})
    observed = frozenset({"pin_a", "pin_b", "pin_c"})  # pin_d escaped the sweep
    with pytest.raises(AssertionError) as excinfo:
        coverage(derived, observed)
    assert "pin_d" in str(excinfo.value), (
        "the coverage failure must name the un-swept pin (pin_d); a bare failure hides which "
        f"refusal pin escaped. Message: {excinfo.value!r}"
    )


def test_coverage_fails_closed_on_an_empty_derived_set() -> None:
    """ANTI-VACUITY: an empty enumeration is a BROKEN sweep, not a clean pass.

    Without this, deleting/renaming the refusal-pin enumeration turns the coverage assertion
    into a ∀ over the empty set — the failure mode of a gate that reads as a pass, the direction
    that always costs (``registration_sites.py`` / ``test_wire_discipline`` shape).
    """
    coverage = _import_coverage_check()
    with pytest.raises(AssertionError):
        coverage(frozenset(), frozenset())


# A note the builder must honour, recorded so the class does not recur one level up: the REAL
# `derived` set fed to `assert_sweep_reached_every_refusal_pin` must itself be derived from a
# PROPERTY (a scan of refusal-shaped pins), never a hand-list — and, because "a refusal pin" is
# not AST-crisp (#295 has no permanent structural gate), the enumeration STATES ITS BOUND. The
# standing guard for instance #9 is INSTRUMENT 0's reach-attack, a reasoning pass, said plainly.
_SWEEP_ENUMERATION_MUST_BE_PROPERTY_DERIVED_AND_BOUND_STATED = True
