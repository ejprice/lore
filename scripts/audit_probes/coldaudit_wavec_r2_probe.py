"""Cold-audit probes for packet 04b-2 wave C (coldaudit-04b2-wavec-r2).

EXECUTES the wave's claims against the real dispatchers + the real footer seam,
using the suite's own hostile harness. Every negative result is paired with a
POSITIVE CONTROL showing the probe can fire.

Run:  uv run python scratchpad/coldaudit_wavec_r2_probe.py
"""

from __future__ import annotations

import asyncio
import pathlib
import sys

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")

import test_comms_footer as H  # noqa: E402

OK = "PASS"
BAD = "**FAIL**"


def show(label: str, verdict: bool, detail: str = "") -> bool:
    print(f"  [{OK if verdict else BAD}] {label}" + (f"  :: {detail}" if detail else ""))
    return verdict


async def probe_mp6() -> None:
    """B2 — MP-6: the ONE except clause must serve BOTH registry classifications."""
    print("\n=== B2 / MP-6 : ambiguous vs unknown identity teaching ===")

    # --- UNKNOWN: a name registered nowhere -------------------------------
    unknown = await H._tasks_call(
        action="create", agent=("ghostagent", None), traffic=(3, 2), registered=H.CALLER_A
    )
    print(f"  UNKNOWN served tail: {unknown.splitlines()[-1]!r}")
    show("unknown: names the offending value", "ghostagent" in unknown)
    show("unknown: NO footer", not H._has_footer(unknown))
    show("unknown: carries the no-footer teaching", "no pending-traffic line" in unknown)

    # --- AMBIGUOUS: the SAME name registered in TWO sessions --------------
    ambiguous = await H._tasks_call(
        action="create",
        agent=("twinagent", None),
        traffic=(3, 2),
        registered=("twinagent", "session-one"),
        also_registered=(("twinagent", "session-two", (1, 1)),),
    )
    tail = ambiguous.splitlines()[-1]
    print(f"  AMBIGUOUS served tail: {tail!r}")
    show("ambiguous: names the offending value", "twinagent" in ambiguous)
    show("ambiguous: names session= as the remedy", "session=" in ambiguous)
    show(
        "ambiguous: does NOT say 'is not registered'",
        "is not registered" not in ambiguous,
        detail=tail,
    )
    show("ambiguous: NO footer", not H._has_footer(ambiguous))
    show("ambiguous: carries the no-footer teaching", "no pending-traffic line" in ambiguous)

    # --- the two teachings must DIFFER (one classifier, two classifications)
    show(
        "the two classifications serve DIFFERENT bytes (not one collapsed message)",
        unknown.splitlines()[-1] != tail,
    )

    # --- POSITIVE CONTROL: a RESOLVED caller on the same vehicle DOES footer
    control = await H._tasks_call(
        action="create", agent=H.CALLER_A, traffic=(3, 2), registered=H.CALLER_A
    )
    show(
        "CONTROL: a resolvable agent on the same vehicle DOES footer (probe can see footers)",
        H._has_footer(control),
        detail=control.splitlines()[-1],
    )


async def probe_r8_split() -> None:
    """B6 — RESOLVED names action=drain; FALLBACK is third-person, no imperative."""
    print("\n=== B6 : R8(2) resolved-vs-fallback footer split ===")
    for dispatcher in H.DISPATCHERS:
        resolved = await H._write_call(
            dispatcher, agent=H.CALLER_A, traffic=(3, 2), registered=H.CALLER_A
        )
        fallback = await H._fallback_write_call(dispatcher, traffic=(3, 2))
        r_line = H._footer_line(resolved)
        f_line = H._footer_line(fallback)
        print(f"  {dispatcher}")
        print(f"    RESOLVED: {r_line!r}")
        print(f"    FALLBACK: {f_line!r}")
        show(f"{dispatcher}: RESOLVED names action=drain", "action=drain" in (r_line or ""))
        show(
            f"{dispatcher}: FALLBACK has NO drain imperative",
            "drain" not in (f_line or ""),
        )
        show(
            f"{dispatcher}: FALLBACK marks itself un-authenticated",
            "not an authenticated caller" in (f_line or ""),
        )
        show(
            f"{dispatcher}: both name the identity (third-person form)",
            "pending traffic for" in (r_line or "") and "pending traffic for" in (f_line or ""),
        )


async def probe_outcome_keying() -> None:
    """B4 — the footer is keyed on WRITES, not on the verb."""
    print("\n=== B4 : footer outcome-keying ===")

    # --- a LOSING claim writes nothing -> READ, no footer -----------------
    losing = await H._claim_call(agent=H.CALLER_A, traffic=(3, 2), wins=False)
    show("LOSING claim (writes=0): NO footer", not H._has_footer(losing),
         detail=losing.splitlines()[-1])
    winning = await H._claim_call(agent=H.CALLER_A, traffic=(3, 2), wins=True)
    show("CONTROL: WINNING claim (writes=1): footer present", H._has_footer(winning),
         detail=(H._footer_line(winning) or ""))

    # --- best-effort batch: force each fate -------------------------------
    for wrote in (0, 1, H.BATCH_SIZE):
        harness = H._footer_harness(traffic=(3, 2), registered=H.CALLER_A)
        kwargs = await H._finding_action_kwargs(harness, "resolve_many", batch_writes=wrote)
        served = await H._findings_call_on(
            harness, action="resolve_many", agent=H.CALLER_A, **kwargs
        )
        has = H._has_footer(served)
        expected = wrote >= 1
        show(
            f"batch resolve_many wrote {wrote}/{H.BATCH_SIZE}: footer={has} (expected {expected})",
            has == expected,
        )

    # --- create_many (atomic) footers on len(items) -----------------------
    for count in (1, 2, 5):
        harness = H._footer_harness(traffic=(3, 2), registered=H.CALLER_A)
        served = await H._tasks_call_on(
            harness,
            action="create_many",
            agent=H.CALLER_A,
            items=[
                {"subject": f"subject {i}", "description": "a real description"}
                for i in range(count)
            ],
            created_by=H._UNREGISTERED_ATTRIBUTION,
        )
        show(f"create_many with {count} items: footer present", H._has_footer(served))

    # --- READS never footer ------------------------------------------------
    for action in ("query", "get", "blockers", "rollup"):
        harness = H._footer_harness(traffic=(3, 2), registered=H.CALLER_A)
        kwargs = await H._task_action_kwargs(harness, action)
        served = await H._tasks_call_on(harness, action=action, agent=H.CALLER_A, **kwargs)
        show(f"READ tasks action={action}: NO footer", not H._has_footer(served))
        # the read budget half: a read must not even resolve the registry
        show(
            f"READ tasks action={action}: ZERO registry reads",
            H._registry_reads(harness) == 0,
            detail=f"reads={H._registry_reads(harness)}",
        )


async def main() -> None:
    await probe_mp6()
    await probe_r8_split()
    await probe_outcome_keying()
    print("\n[done]")


if __name__ == "__main__":
    asyncio.run(main())
