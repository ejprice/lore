"""INSTRUMENT D (finding #295 / #346) — refusal pins observe the EFFECT, not a proxy.

Contract: ``loremaster/tests/test_refusal_observes_effect.py``. Design doc
``docs/plans/v2/design/2026-08-09-defect-class-prevention.md`` §INSTRUMENT D (F2).

THE DEFECT THIS KILLS (finding #295 / WB48). A guard that performs the mutating action and THEN
refuses is byte-identical, at every PROXY observation point (the raised exception, the rendered
refusal marker), to one that refuses first. WB48 placed the posture guard AFTER
``super().call_tool``: the refusal marker was byte-identical to the correct build's, and the tool's
body had ALREADY executed. Every one of 55 posture pins observed the marker (the proxy) and passed
both builds. The only thing that separates ``the body ran`` from ``it did not`` is the EFFECT —
an invocation counter, an unchanged store, an absent row.

    THE ASKABLE FORM (finding #295, promoted to INSTRUMENT 0):
        "If the guard ran AFTER the thing it guards, would this pin still pass?"

THE FIX — ONE shared helper every refusal/posture pin CALLS, so the effect check is ONE
implementation, not re-hand-rolled per pin (which is how WB48 slipped: a new pin with its own
weaker observation). Packet 39's posture pins CONSUME this helper for their refusal assertions.

TWO INDEPENDENT CLOSURES of the D-WB2 in-process door (``wire.mcp.call_tool`` — dead on the wire,
byte-identical to a live guard at every proxy point), so the WIRE-driving claim is VERIFIED, not
merely asserted in a docstring:
  * **R4** — the helper is handed ONLY the boundary callable (``WireSession.call``), never the whole
    session, so ``wire.mcp.call_tool(...)`` cannot be written here at all.
  * **R16** — this module is UNDER ``test_wire_discipline``'s receiver-blind AST scan
    (``posture_modules()``), which mechanically forbids any ``<anything>.call_tool(...)`` in it.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from typing import Any


async def assert_tool_refused_and_did_not_run(
    call: Callable[[str, dict[str, Any]], Awaitable[str]],
    tool_name: str,
    args: dict[str, Any],
    *,
    effect_count: Callable[[], int],
    refusal_marker: str,
) -> str:
    """Assert ``tool_name`` was refused over the REAL wire AND its guarded body did NOT run.

    Args:
        call: the BOUNDARY CALLABLE ONLY — ``WireSession.call``. The helper is handed the callable,
            never the whole session, so the in-process ``wire.mcp.call_tool`` door (D-WB2 / #346) is
            UNREPRESENTABLE here by construction (R4). The dispatch goes over the wire via
            ``await call(tool_name, args)``.
        tool_name: the tool to attempt.
        args: the tool arguments.
        effect_count: the pluggable EFFECT observer — ``() -> int`` reading the guarded side
            effect's count (an invocation counter, or a store-row count; ``0`` means the body never
            ran). This is the one thing that legitimately varies per tool; the assertion STRUCTURE
            is shared.
        refusal_marker: the rendered refusal marker (the PROXY) — present but insufficient.

    Returns:
        The rendered response body (so a caller may make further, tool-specific assertions on it).

    Raises:
        AssertionError: if the marker is absent (WEAK leg — it was not refused at all), or if the
            effect ran (STRONG leg — the guarded body executed, the #295 defect). The STRONG-leg
            message NAMES the effect, so a reader can tell it apart from a mere missing-marker
            failure.
    """
    body = await call(tool_name, args)

    # WEAK leg — it WAS refused (marker present). Necessary but INSUFFICIENT: WB48 renders this
    # byte-identically while its effect has already run.
    assert refusal_marker in body, (
        f"the refusal marker {refusal_marker!r} is absent from the response body — the call was "
        f"NOT refused. Body: {body!r}"
    )

    # STRONG leg — the #295 fix: the guarded body did NOT run. This is the ONLY observation that
    # separates a refuse-first build from a run-then-refuse (WB48) build; both pass the weak leg.
    ran = effect_count()
    assert ran == 0, (
        f"the guarded EFFECT RAN (effect_count() == {ran}, expected 0): the tool body executed "
        f"before it was refused. The refusal marker is present but it is a PROXY — a guard placed "
        f"AFTER the mutating body renders an identical marker while the invocation has already "
        f"happened (finding #295 / WB48). Observe the effect, not the proxy."
    )
    return body


def assert_sweep_reached_every_refusal_pin(
    derived: Iterable[str], observed: Iterable[str]
) -> None:
    """Coverage-as-a-checked-variable for the one-time refusal-effect sweep.

    Fail-closed on an empty ``derived`` set (anti-vacuity), and RED if any derived refusal pin was
    not observed routing through the effect helper — naming the un-swept pin, so a reader can see
    WHICH pin escaped rather than merely that coverage failed.

    Args:
        derived: the refusal-shaped pins derived from a PROPERTY (a scan), not a hand-list.
        observed: the pins the sweep actually routed through the effect helper.

    Raises:
        AssertionError: if ``derived`` is empty (an enumeration that certifies nothing while reading
            as a clean pass — the failure direction that always costs), or if any derived pin is
            absent from ``observed`` (a refusal pin the sweep silently never reached — the reach
            written as a hidden constant, the exact class this instrument exists to stop).
    """
    derived_set = frozenset(derived)
    observed_set = frozenset(observed)
    assert derived_set, (
        "anti-vacuity: the derived refusal-pin set is EMPTY. An effect-sweep over zero pins "
        "certifies nothing while reading as a clean pass — deleting or renaming the enumeration "
        "must fail CLOSED here, not pass silently."
    )
    missed = derived_set - observed_set
    assert not missed, (
        f"the effect-sweep did not reach {sorted(missed)}: these refusal pin(s) were DERIVED but "
        "never OBSERVED routing through the effect helper. Coverage is a checked variable — every "
        "derived refusal pin must be observed, or the sweep's reach is a silent exemption."
    )
