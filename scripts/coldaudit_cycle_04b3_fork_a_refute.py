#!/usr/bin/env python3
"""coldaudit-cycle-04b3-1 — an INDEPENDENT REFUTE of variant-D FORK-A's closure bound.

Written 2026-08-04 by the cold auditor of packet 04b-3's CYCLE change (HEAD 496a95e),
per the brief's "REFUTE the soundness claims — CONSTRUCT, don't reason" mandate. This is
NOT the builder's ESC-1 harness or MP-1 probe (those CONFIRM); this one ATTEMPTS TO BREAK
FORK-A by placing a cycle-closing row where the bounded ancestor-closure read cannot reach.

FORK-A's claim (tasks.py::_bounded_dependency_graph docstring): bounding the write-guard's
read to the pending task's ANCESTOR CLOSURE, walked over persisted ``blocks`` EDGES, "loses
no cycle" — because every row that could close a cycle through pending N is an ancestor of
one of N's blockers, hence edge-reachable upstream. The proof RESTS on ESC-1's measured
invariant: every persisted ``blocked_by`` column link has a corresponding ``blocks`` edge
(maintained atomically on the write path, restored by ensure_ready's backfill for legacy
rows).

THE ADVERSARIAL MOVE: a MULTI-HOP chain whose cycle-closing row ``far`` is TWO hops upstream
of the seed, reached only THROUGH an intermediate link ``mid.blocked_by ∋ far``. If that one
intermediate EDGE is missing (a legacy/un-backfilled column), the edge-walk truncates at
``mid`` and never reads ``far``'s column — so the guard would MISS the real cycle
N -> seed -> mid -> far -> N.

  WORLD A (edges present — the healthy invariant): all intermediate edges minted. Positive
      control: the closure walk must reach ``far`` (2 hops) and the guard must REFUSE.
  WORLD B (one intermediate edge MISSING, backfill NOT run): the exact invariant violation.
      Does the raw bounded read miss the cycle? This LOCATES the soundness dependency.
  WORLD B + ensure_ready backfill: the edge is minted -> the read reaches ``far`` -> REFUSE.
      Self-healing: soundness is restored the moment the invariant is.

Run against spike :18000 (TEST store — NEVER :18500). Output IS the receipt. Exit 0 iff the
mapping is exactly: A refuses, B (raw, invariant violated) behaves as the bound predicts, and
B-after-backfill refuses. A guard that refused in A but SILENTLY (no backfill) in B on the raw
path would be UNCONDITIONALLY sound — a stronger result; the probe reports whichever it finds.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import STATUS_OPEN, TaskLedger, TaskLedgerError
from surrealdb import RecordID

import loremaster


def _repository_root() -> Path:
    """This checkout's root, derived from this file's location."""
    return Path(__file__).resolve().parent.parent


def _harness() -> Any:
    """The suite's real-SurrealDB harness (``scripts/forgery_door_sweep.py::_harness``).

    ``loremaster/tests`` is a plain directory, not a package; the suite reaches its
    shared helpers as top-level modules by putting that directory on ``sys.path``.
    This script is not run by pytest, so it does the same insert and reuses the
    connection topology, unique-database minting, signin + session bootstrap and
    retry-aware teardown the harness already owns — which is also why the env read
    and the ``SecretStr`` mint live in the harness (a test module the secret-boundary
    scans exclude), never here (SEAMS-OVER-HAND-ROLLING; #211).
    """
    tests_directory = str(_repository_root() / "loremaster" / "tests")
    if tests_directory not in sys.path:
        sys.path.insert(0, tests_directory)
    import _surreal_harness

    return _surreal_harness


_HARNESS = _harness()
_SURREAL_URL = _HARNESS.surreal_url()
assert "18500" not in _SURREAL_URL, f"REFUSING: {_SURREAL_URL!r} looks like production lore-surreal"
assert "127.0.0.1:18000" in _SURREAL_URL, f"REFUSING: {_SURREAL_URL!r} is not the spike test store"


def _fresh_env() -> Any:
    """A ``SurrealEnv`` on a fresh unique test database, via the shared harness seam."""
    return _HARNESS.make_env(database=_HARNESS.unique_database(), dim=_HARNESS.PRODUCTION_DIM)


async def create_row(connection: Any, task_id: str, blocked_by: list[str]) -> None:
    """RAW-CREATE a column-bearing row (bypass the guard, exactly as legacy history can)."""
    now = datetime.now(UTC)
    await connection.query(
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {
            "id": task_id,
            "content": {
                "subject": f"row {task_id}",
                "description": "fork-A refutation probe",
                "status": STATUS_OPEN,
                "blocked_by": blocked_by,
                "provenance": {
                    "created_by": "forka",
                    "created_at": now.isoformat(),
                    "events": [],
                },
                "created_at": now,
            },
        },
    )


async def edge(connection: Any, blocker: str, blocked: str) -> None:
    """RAW-RELATE one `blocks` edge (blocker ->blocks-> blocked; bound RecordIDs, §4)."""
    await connection.query(
        f"RELATE $b->{BLOCKS_RELATION}->$t",
        {"b": RecordID(TASK_TABLE, blocker), "t": RecordID(TASK_TABLE, blocked)},
    )


async def build_world(connection: Any, tag: str, *, mid_far_edge: bool) -> dict[str, str]:
    """seed.bb=[mid], mid.bb=[far], far.bb=[N]  (N = the pending id, column-only closing link).

    Cycle if N is created blocked_by [seed]:  N -> seed -> mid -> far -> N.
    ``far`` is TWO hops upstream of the seed. With ``mid_far_edge=False`` the far->mid edge is
    omitted (mid's column names far, but no edge) — the invariant violation under test.
    """
    seed, mid, far = f"seed_{tag}", f"mid_{tag}", f"far_{tag}"
    new_id = f"newn_{tag}"  # the caller-supplied id about to be created; NO row yet
    await create_row(connection, seed, [mid])
    await create_row(connection, mid, [far])
    await create_row(connection, far, [new_id])  # column-only closing link (N has no row)
    await edge(connection, mid, seed)  # mid blocks seed        (seed.bb ∋ mid)  — always present
    if mid_far_edge:
        await edge(connection, far, mid)  # far blocks mid      (mid.bb ∋ far)  — the hop under test
    # NEVER an edge for (N -> far): N has no row, ENFORCED forbids it — column only, as in prod.
    return {"seed": seed, "mid": mid, "far": far, "new_id": new_id}


async def guard_refuses(ledger: TaskLedger, w: dict[str, str]) -> bool:
    """Run the SHIPPED write guard in isolation for pending {N: [seed]}. True iff it REFUSES."""
    try:
        await ledger._refuse_a_cycle({w["new_id"]: [w["seed"]]})
    except TaskLedgerError as exc:
        print(f"    guard REFUSED: {type(exc).__name__}: {str(exc).splitlines()[0]}")
        return True
    return False


async def closure_of(ledger: TaskLedger, w: dict[str, str]) -> list[str]:
    """What the shipped bounded read actually returns for seeds={seed} — the read's REACH."""
    graph = await ledger._bounded_dependency_graph({w["seed"]})
    return sorted(graph)


async def _world_a(verdicts: list[tuple[str, bool]]) -> None:
    """Edges present (healthy invariant) — the positive control: closure must reach far."""
    env = _fresh_env()
    conn = await _HARNESS.connect_admin(env)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    try:
        await ledger.ensure_ready()
        world = await build_world(conn, uuid.uuid4().hex[:8], mid_far_edge=True)
        reach = await closure_of(ledger, world)
        far_reached = world["far"] in reach
        print(f"WORLD A (edges present): closure reach from seed = {reach}  far? {far_reached}")
        refused = await guard_refuses(ledger, world)
        print(
            f"  => far is 2 hops up; guard {'REFUSED' if refused else 'ACCEPTED'} "
            f"(expect REFUSED: multi-hop closure must reach the cycle-closing row)\n"
        )
        verdicts.append(("A: edges present -> REFUSE + far reached", refused and far_reached))
    finally:
        await ledger.close()
        await conn.close()
        await _HARNESS.drop_database(env)


async def _world_b(verdicts: list[tuple[str, bool]]) -> None:
    """One intermediate edge MISSING (invariant violated), then self-healed by backfill."""
    env = _fresh_env()
    conn = await _HARNESS.connect_admin(env)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    try:
        await ledger.ensure_ready()  # blocks table exists; then we inject a legacy column-row
        world = await build_world(conn, uuid.uuid4().hex[:8], mid_far_edge=False)
        reach_raw = await closure_of(ledger, world)
        far_raw = world["far"] in reach_raw
        print(f"WORLD B (far->mid edge MISSING, no backfill): reach = {reach_raw}  far? {far_raw}")
        refused_raw = await guard_refuses(ledger, world)
        print(
            f"  => raw bounded read {'REACHES' if far_raw else 'TRUNCATES BEFORE'} far; "
            f"guard {'REFUSED' if refused_raw else 'ACCEPTED'}."
        )
        # The bound predicts: no edge => truncated read => MISS. That is the invariant dependency,
        # NOT a defect in the shipped guard: production maintains the invariant (atomic writes +
        # backfill). We assert the MECHANISM is exactly as documented (miss <=> not reached).
        mechanism = refused_raw == far_raw
        print(f"     mechanism (guard-refuses <=> far-reached) holds? {mechanism}\n")
        verdicts.append(("B raw: refusal tracks reach exactly", mechanism))

        await ledger._backfill_blocks_edges()  # mints the missing far->mid edge
        reach_bf = await closure_of(ledger, world)
        far_bf = world["far"] in reach_bf
        print(f"WORLD B + ensure_ready backfill: reach = {reach_bf}  far? {far_bf}")
        refused_bf = await guard_refuses(ledger, world)
        print(
            f"  => backfill minted the missing edge; guard "
            f"{'REFUSED' if refused_bf else 'ACCEPTED'} (expect REFUSED: self-healing)\n"
        )
        verdicts.append(("B+backfill: edge restored -> REFUSE + far reached", refused_bf and far_bf))
    finally:
        await ledger.close()
        await conn.close()
        await _HARNESS.drop_database(env)


async def probe() -> int:
    print(f"loremaster.__file__ = {loremaster.__file__}")
    print(f"store = {_SURREAL_URL}  namespace = {_HARNESS.TEST_NAMESPACE}\n")
    verdicts: list[tuple[str, bool]] = []
    await _world_a(verdicts)
    await _world_b(verdicts)

    print("=" * 64)
    ok = True
    for label, passed in verdicts:
        print(f"  [{'PASS' if passed else 'FAIL'}] {label}")
        ok = ok and passed
    if ok:
        print(
            "\nVERDICT: FORK-A's closure bound is SOUND, and its soundness is EXACTLY the "
            "edge==column invariant — violated only by a legacy column with no edge, which "
            "the backfill self-heals. Could NOT construct a cycle-closing row that the guard "
            "misses on an invariant-satisfying store."
        )
        return 0
    print("\nVERDICT: a leg did NOT behave as the bound predicts — INVESTIGATE (see above).")
    return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(probe()))
