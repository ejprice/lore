"""Cold-audit probe #3 — the CYCLE and PHANTOM legs of the B1 differential.

Probe #2's cycle/self-block cases were VACUOUS: neither side could wire a cycle
through the public create path, so both returned the same sentinel and "agreed"
about nothing. The real suite wires cycles RAW (``test_blocks_edge._seed_cycle``,
bypassing every ledger guard); this mirrors that on both sides and compares.

Run:  uv run python scratchpad/coldaudit_wavec_r2_probe3.py
"""

from __future__ import annotations

import asyncio
import pathlib
import sys
from typing import Any

_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "loremaster" / "tests"))

import loremaster  # noqa: E402

print(f"[provenance] loremaster.__file__ = {loremaster.__file__}")

OK, BAD = "PASS", "**FAIL**"
_FAILURES: list[str] = []


def show(label: str, verdict: bool, detail: str = "") -> bool:
    if not verdict:
        _FAILURES.append(label)
    print(f"  [{OK if verdict else BAD}] {label}" + (f"  :: {detail}" if detail else ""))
    return verdict


async def _real_cycle(length: int) -> tuple[frozenset[str], bool, int]:
    """A raw-seeded ``blocks`` cycle in the LIVE store, walked by the real ledger."""
    import test_blocks_edge as B
    from _surreal_harness import PRODUCTION_DIM, connect_admin, drop_database, make_env, unique_database
    from loremaster.tasks import TaskLedger

    env = make_env(database=unique_database(), dim=PRODUCTION_DIM)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    await ledger.ensure_ready()
    try:
        setup = await connect_admin(env)
        try:
            ids = await B._seed_cycle(setup, length)
        finally:
            await setup.close()
        result = await ledger.transitive_blockers(ids[0])
        index_of = {task_id: f"n{i}" for i, task_id in enumerate(ids)}
        return (
            frozenset(index_of.get(i, i) for i in result.ids),
            result.truncated,
            result.max_depth_used,
        )
    finally:
        try:
            await drop_database(env)
        except Exception:  # noqa: BLE001,S110
            pass


async def _fake_cycle(length: int) -> tuple[frozenset[str], bool, int]:
    """The SAME cycle hand-wired into FakeTaskLedger's db, walked by the fake."""
    from _task_fakes import FakeTaskDatabase, FakeTaskLedger

    ledger = FakeTaskLedger(db=FakeTaskDatabase())
    ids = [
        await ledger.create_task(f"subject {i}", "a real description", created_by="coldaudit")
        for i in range(length)
    ]
    for index, task_id in enumerate(ids):
        blocker = ids[(index - 1) % length]
        _set_blocked_by(ledger.db, task_id, [blocker])
    result = await ledger.transitive_blockers(ids[0])
    index_of = {task_id: f"n{i}" for i, task_id in enumerate(ids)}
    return (
        frozenset(index_of.get(i, i) for i in result.ids),
        result.truncated,
        result.max_depth_used,
    )


def _set_blocked_by(db: Any, task_id: str, blockers: list[str]) -> None:
    """Force a task's ``blocked_by`` column, whatever the model's mutability."""
    task = db.tasks[task_id]
    try:
        object.__setattr__(task, "blocked_by", list(blockers))
    except Exception:  # noqa: BLE001
        db.tasks[task_id] = task.model_copy(update={"blocked_by": list(blockers)})


async def probe_cycles() -> None:
    print("\n=== B1(cycle) : raw-seeded cycles, fake vs real ===")
    for length in (1, 2, 3, 5):
        real = await _real_cycle(length)
        fake = await _fake_cycle(length)
        same = real == fake
        if not same:
            _FAILURES.append(f"cycle length={length}")
        print(f"  [{OK if same else BAD}] cycle length={length}")
        print(f"        REAL: ids={sorted(real[0])} truncated={real[1]} depth={real[2]}")
        print(f"        FAKE: ids={sorted(fake[0])} truncated={fake[1]} depth={fake[2]}")
        # the property the real pin asserts: a task on a cycle is in its OWN reach
        show(f"  real: n0 in its own reach (length={length})", "n0" in real[0])
        show(f"  fake: n0 in its own reach (length={length})", "n0" in fake[0])


async def probe_phantom() -> None:
    """A ``blocked_by`` entry naming NO row: in the COLUMN, never in the walk."""
    print("\n=== B1(phantom) : a blocked_by entry naming no task row ===")
    from _task_fakes import FakeTaskDatabase, FakeTaskLedger

    ledger = FakeTaskLedger(db=FakeTaskDatabase())
    real_blocker = await ledger.create_task("real blocker", "d", created_by="coldaudit")
    subject = await ledger.create_task("subject", "d", created_by="coldaudit")
    _set_blocked_by(ledger.db, subject, [real_blocker, "phantom_does_not_exist"])

    walk = await ledger.transitive_blockers(subject)
    show("fake: the phantom is ABSENT from the walk", "phantom_does_not_exist" not in walk.ids,
         detail=f"ids={walk.ids}")
    show("fake: the LIVE blocker IS present (probe discriminates)", real_blocker in walk.ids)
    claimable = await ledger.claim_task(subject, "someone")
    show("fake: the phantom STILL BLOCKS the claim (fail-closed, as production)",
         not getattr(claimable, "claimed", True), detail=str(claimable)[:120])


async def main() -> None:
    await probe_cycles()
    await probe_phantom()
    print(f"\n[done] failures: {len(_FAILURES)}")
    for failure in _FAILURES:
        print(f"   - {failure}")


if __name__ == "__main__":
    asyncio.run(main())
