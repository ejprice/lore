"""Cold-audit probes #2 for packet 04b-2 wave C (coldaudit-04b2-wavec-r2).

B3 — link 1b sharing, proven by RUNTIME MUTATION (routing is not sharing).
B1 — FakeTaskLedger.transitive_blockers vs the REAL TaskLedger, differential
     oracle against the live test store (ws://127.0.0.1:18000).

Run:  uv run python scratchpad/coldaudit_wavec_r2_probe2.py
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
from loremaster.server import AppContext  # noqa: E402

OK, BAD = "PASS", "**FAIL**"
_FAILURES: list[str] = []


def show(label: str, verdict: bool, detail: str = "") -> bool:
    if not verdict:
        _FAILURES.append(label)
    print(f"  [{OK if verdict else BAD}] {label}" + (f"  :: {detail}" if detail else ""))
    return verdict


# ---------------------------------------------------------------------------
# B3 — perturb the SHARED predicate; every consumer must move together.
# ---------------------------------------------------------------------------

_CANARY = "auditcanary"  # charset-legal today; the mutation makes it ILLEGAL.


async def _refuses(dispatcher: str, name: str) -> bool:
    """Did ``dispatcher`` REFUSE ``name`` as agent= (charset gate)?"""
    try:
        await H._write_call(
            dispatcher, agent=(name, None), traffic=(3, 2), registered=(name, "s1")
        )
    except ValueError:
        return True
    return False


async def _fallback_footers(attribution: str) -> bool:
    """Does the R8(2) attribution path produce a footer for ``attribution``?"""
    harness = H._footer_harness(traffic=(3, 2), owner_identity=attribution)
    served = await H._tasks_call_on(
        harness, action="create", agent=None, owner=attribution, created_by=attribution
    )
    return H._has_footer(served)


async def probe_link1b_sharing() -> None:
    print("\n=== B3 : link 1b — ONE predicate, proven by runtime mutation ===")

    original = AppContext.__dict__["_is_comms_charset_legal"]

    # BASELINE (positive control): the canary is legal everywhere.
    base_refusals = {d: await _refuses(d, _CANARY) for d in H.DISPATCHERS}
    base_footer = await _fallback_footers(_CANARY)
    print(f"  BASELINE refusals: {base_refusals}   attribution-footer: {base_footer}")
    show(
        "CONTROL: unmutated — NO dispatcher refuses the canary",
        not any(base_refusals.values()),
    )
    show("CONTROL: unmutated — the attribution gate ADMITS the canary (footers)", base_footer)

    # MUTATION: the shared predicate now refuses anything containing "canary".
    def _perturbed(value: str) -> bool:
        return "canary" not in value and bool(
            __import__("loremaster.server", fromlist=["AGENT_NAME_PATTERN"])
            .AGENT_NAME_PATTERN.fullmatch(value)
        )

    AppContext._is_comms_charset_legal = staticmethod(_perturbed)  # type: ignore[method-assign]
    try:
        mut_refusals = {d: await _refuses(d, _CANARY) for d in H.DISPATCHERS}
        mut_footer = await _fallback_footers(_CANARY)
        print(f"  MUTATED  refusals: {mut_refusals}   attribution-footer: {mut_footer}")
        for dispatcher, refused in mut_refusals.items():
            show(f"MUTATION moved {dispatcher}'s refusal (no private copy)", refused)
        show(
            "MUTATION moved the R8(2) attribution gate too (skips -> no footer)",
            not mut_footer,
        )
        # A name the mutation does NOT touch must still work -> the mutation is
        # a PERTURBATION, not a blanket break.
        show(
            "DISCRIMINATION: an untouched legal name still passes under the mutation",
            not await _refuses("lore_tasks", "othername"),
        )
    finally:
        AppContext._is_comms_charset_legal = original  # type: ignore[method-assign]

    # RESTORE PROOF
    post = {d: await _refuses(d, _CANARY) for d in H.DISPATCHERS}
    show("RESTORED byte-exact (behaviour back to baseline)", post == base_refusals,
         detail=f"{post}")


# ---------------------------------------------------------------------------
# B1 — fake-vs-real differential for transitive_blockers.
# ---------------------------------------------------------------------------

GRAPHS: dict[str, dict[str, list[str]]] = {
    # label -> blocked_by labels
    "chain4": {"a": [], "b": ["a"], "c": ["b"], "d": ["c"]},
    "diamond": {"a": [], "b": ["a"], "c": ["a"], "d": ["b", "c"]},
    "wide": {"a": [], "b": [], "c": [], "d": ["a", "b", "c"]},
    "selfblock": {"a": ["a"]},
    "cycle2": {"a": ["b"], "b": ["a"]},
    "isolated": {"a": []},
}


async def _real_walk(
    graph: dict[str, list[str]], start: str, max_depth: int | None
) -> tuple[list[str], bool, int] | str:
    from _surreal_harness import PRODUCTION_DIM, make_env, unique_database
    from loremaster.tasks import TaskLedger

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(
        url=env.url,
        namespace=env.namespace,
        database=env.database,
        user=env.user,
        password=env.password,
    )
    await ledger.ensure_ready()
    ids: dict[str, str] = {}
    try:
        # Create in dependency order so blocked_by always names a live row.
        remaining = dict(graph)
        while remaining:
            progressed = False
            for label, blockers in list(remaining.items()):
                if all(b in ids or b == label for b in blockers):
                    ids[label] = await ledger.create_task(
                        f"subject {label}",
                        "a real description",
                        created_by="coldaudit",
                        blocked_by=[ids[b] for b in blockers if b in ids],
                    )
                    del remaining[label]
                    progressed = True
            if not progressed:  # a pure cycle — create bare, then wire below
                for label in list(remaining):
                    ids[label] = await ledger.create_task(
                        f"subject {label}", "a real description", created_by="coldaudit"
                    )
                    del remaining[label]
                return "CYCLE-UNWIRABLE-VIA-PUBLIC-API"
        result = await ledger.transitive_blockers(
            ids[start], **({} if max_depth is None else {"max_depth": max_depth})
        )
        label_of = {v: k for k, v in ids.items()}
        return ([label_of.get(i, i) for i in result.ids], result.truncated, result.max_depth_used)
    except Exception as error:  # noqa: BLE001 - differential wants the classification
        return f"{type(error).__name__}: {error}"
    finally:
        from _surreal_harness import drop_database

        try:
            await drop_database(env)
        except Exception:  # noqa: BLE001,S110
            pass


async def _fake_walk(
    graph: dict[str, list[str]], start: str, max_depth: int | None
) -> tuple[list[str], bool, int] | str:
    from _task_fakes import FakeTaskDatabase, FakeTaskLedger

    ledger = FakeTaskLedger(db=FakeTaskDatabase())
    ids: dict[str, str] = {}
    try:
        remaining = dict(graph)
        while remaining:
            progressed = False
            for label, blockers in list(remaining.items()):
                if all(b in ids or b == label for b in blockers):
                    ids[label] = await ledger.create_task(
                        f"subject {label}",
                        "a real description",
                        created_by="coldaudit",
                        blocked_by=[ids[b] for b in blockers if b in ids],
                    )
                    del remaining[label]
                    progressed = True
            if not progressed:
                return "CYCLE-UNWIRABLE-VIA-PUBLIC-API"
        result = await ledger.transitive_blockers(
            ids[start], **({} if max_depth is None else {"max_depth": max_depth})
        )
        label_of = {v: k for k, v in ids.items()}
        return ([label_of.get(i, i) for i in result.ids], result.truncated, result.max_depth_used)
    except Exception as error:  # noqa: BLE001
        return f"{type(error).__name__}: {error}"


def _normalise(outcome: object) -> object:
    """Order-insensitive per-DEPTH comparison is wrong; compare as SET + flags.

    Proximity ORDER is a stated property of both, but the real walk's within-depth
    order is engine-decided, so the differential compares the SET of ids, the
    truncated flag and max_depth_used — a divergence in any of the three is a
    real fidelity gap.
    """
    if isinstance(outcome, tuple):
        ids, truncated, depth = outcome
        return (frozenset(ids), len(ids), truncated, depth)
    return outcome


async def probe_fake_real_parity() -> None:
    print("\n=== B1 : FakeTaskLedger.transitive_blockers vs REAL TaskLedger ===")
    cases: list[tuple[str, str, int | None]] = []
    for name, graph in GRAPHS.items():
        start = "d" if "d" in graph else "a"
        cases.extend([(name, start, None), (name, start, 1), (name, start, 2), (name, start, 3)])
    # bounds cases on a graph that exists
    cases.extend([("chain4", "d", 0), ("chain4", "d", -1), ("chain4", "d", 10**9)])

    agree = disagree = 0
    for name, start, depth in cases:
        real = await _real_walk(GRAPHS[name], start, depth)
        fake = await _fake_walk(GRAPHS[name], start, depth)
        same = _normalise(real) == _normalise(fake)
        agree += same
        disagree += not same
        marker = OK if same else BAD
        if not same:
            _FAILURES.append(f"parity {name}/{start}/depth={depth}")
        print(f"  [{marker}] {name:9s} start={start} max_depth={depth}")
        if not same:
            print(f"        REAL: {real}")
            print(f"        FAKE: {fake}")
    print(f"  -> {agree} agree, {disagree} DISAGREE across {len(cases)} differential cases")

    # POSITIVE CONTROL: the oracle must be able to SEE a divergence.
    print("  CONTROL: injecting a deliberate fake-side divergence...")
    from _task_fakes import FakeTaskLedger

    original = FakeTaskLedger.transitive_blockers

    async def _wrong(self, task_id, *, max_depth=None):  # type: ignore[no-untyped-def]
        result = await original(self, task_id, max_depth=max_depth)
        return type(result)(ids=result.ids[:-1], truncated=result.truncated,
                            max_depth_used=result.max_depth_used)

    FakeTaskLedger.transitive_blockers = _wrong  # type: ignore[method-assign]
    try:
        real = await _real_walk(GRAPHS["chain4"], "d", None)
        fake = await _fake_walk(GRAPHS["chain4"], "d", None)
        show(
            "CONTROL: the differential DETECTS an injected divergence",
            _normalise(real) != _normalise(fake),
            detail=f"real={real} fake={fake}",
        )
    finally:
        FakeTaskLedger.transitive_blockers = original  # type: ignore[method-assign]


async def main() -> None:
    await probe_link1b_sharing()
    await probe_fake_real_parity()
    print(f"\n[done] failures: {len(_FAILURES)}")
    for failure in _FAILURES:
        print(f"   - {failure}")


if __name__ == "__main__":
    asyncio.run(main())
