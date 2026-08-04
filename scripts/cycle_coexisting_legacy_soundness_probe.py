#!/usr/bin/env python3
"""MP-1 — the coexisting-legacy-cycle SOUNDNESS fixture, as a durable probe.

Reconstructed byte-faithfully from `adversary-cycle-04b3-1`'s `/tmp/unsoundness_probe.py`
(REPORT-adversary-cycle-04b3-1.md §2/§6) and committed here per brief-base §1's perversity
clause — an instrument that establishes a load-bearing claim is a deliverable, never scratch,
and `/tmp` is unrecoverable by construction. Ruled into the CYCLE contract by
`REPORT-design-sidecar-04b3-1.md` §CYCLE-TRILEMMA MP-1 (variant D).

WHAT IT PROVES: the ONLY build that passed the pre-fix CYCLE contract (variant S — ESC-1's
bounded read with a SINGLE `find_blocked_by_cycle` + `minted.intersection`) is UNSOUND. When a
LEGACY 2-cycle coexists with a minted cycle in the bounded closure, `find_blocked_by_cycle`
returns the LEGACY cycle first, `minted ∩ = ∅`, and S ACCEPTS a create that forms a real
persisted-id cycle `N → seed → X → N` — an unclaimable-forever task. Variant D (the ruled build:
bounded read + the KEPT drop-loop through the shared `find_blocked_by_cycle`) steps over the
legacy cycle and refuses, exactly as the shipped whole-population guard at HEAD does.

THE WORLD (ids chosen so `find_blocked_by_cycle`'s SORT returns the legacy cycle first — the
`aaa*` legacy ids sort before the `zzz*` minted ids; this ordering is the discrimination):
  seed <- X            (X blocks seed)
  X.blocked_by = [P, new_id]   (P is a real ancestor; new_id is the COLUMN-ONLY closing link —
                                no `blocks` edge, ENFORCED forbids an edge to a non-existent id)
  P <-> Q              (the legacy 2-cycle, with edges — backfilled, never removed in production)
Then `create_many([blocked_by=[seed]], ids=[new_id])`: the minted cycle is N→seed→X→N.

RUN against the SHIPPED build (spike :18000, TEST store — NEVER :18500): exit 0 when the guard
REFUSES (sound — HEAD and variant D), exit 2 when it ACCEPTS (unsound — variant S). Output IS the
receipt.
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE
from loremaster.tasks import STATUS_OPEN, TaskCycleError, TaskLedger, TaskSpec
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
    """RAW-CREATE a column-bearing row (bypass the guard, exactly as history can)."""
    now = datetime.now(UTC)
    await connection.query(
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {
            "id": task_id,
            "content": {
                "subject": f"row {task_id}",
                "description": "MP-1 coexisting-legacy-cycle soundness probe",
                "status": STATUS_OPEN,
                "blocked_by": blocked_by,
                "provenance": {"created_by": "mp1", "created_at": now.isoformat(), "events": []},
                "created_at": now,
            },
        },
    )


async def edge(connection: Any, blocker: str, blocked: str) -> None:
    """RAW-RELATE one `blocks` edge (bound RecordIDs, store ref §4)."""
    await connection.query(
        f"RELATE $b->{BLOCKS_RELATION}->$t",
        {"b": RecordID(TASK_TABLE, blocker), "t": RecordID(TASK_TABLE, blocked)},
    )


async def probe() -> int:
    print(f"loremaster.__file__ = {loremaster.__file__}  (the REAL tree)")
    env = _fresh_env()
    connection = await _HARNESS.connect_admin(env)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    try:
        await ledger.ensure_ready()  # the blocks table exists (a healthy, long-lived world)

        tag = uuid.uuid4().hex[:8]
        legp, legq = f"aaap_{tag}", f"aaaq_{tag}"  # legacy cycle — sorts FIRST
        seed, node_x = f"zseed_{tag}", f"zzzx_{tag}"
        new_id = f"zzzn_{tag}"  # the caller-supplied id about to be created

        await create_row(connection, seed, [node_x])
        await create_row(connection, node_x, [legp, new_id])  # X.blocked_by names N — closing link
        await create_row(connection, legp, [legq])  # legacy 2-cycle P <-> Q
        await create_row(connection, legq, [legp])

        await edge(connection, node_x, seed)  # X blocks seed
        await edge(connection, legp, node_x)  # P blocks X
        await edge(connection, legp, legq)  # P blocks Q
        await edge(connection, legq, legp)  # Q blocks P
        # NO edge for (new_id -> X): new_id has no row (ENFORCED forbids it) — COLUMN only.

        before = len(await connection.query(f"SELECT id FROM {TASK_TABLE}"))

        refused = False
        try:
            await ledger.create_many(
                [TaskSpec(subject="closes a minted cycle", description="d", blocked_by=[seed])],
                created_by="mp1",
                ids=[new_id],
            )
        except TaskCycleError as exc:
            refused = True
            print(f"REFUSED (correct): {exc}")

        after = len(await connection.query(f"SELECT id FROM {TASK_TABLE}"))
        landed = after == before + 1
        served = {
            str(row["id"])
            for row in await connection.query(f"SELECT record::id(id) AS id FROM {TASK_TABLE}")
        }
        print(
            f"rows before={before} after={after}  new task landed? {landed}  "
            f"new_id in store? {new_id in served}"
        )
        if refused and not landed:
            print("VERDICT: guard REFUSED the cyclic create — SOUND (HEAD / variant D).")
            return 0
        if landed and new_id in served:
            print(
                "VERDICT: guard ACCEPTED a create that forms a persisted-id cycle "
                "(N -> seed -> X -> N). *** UNSOUND build (variant S) — the pin MP-1 kills. ***"
            )
            return 2
        print(f"VERDICT: ambiguous (refused={refused} landed={landed}) — investigate.")
        return 3
    finally:
        await ledger.close()
        await connection.close()
        await _HARNESS.drop_database(env)


if __name__ == "__main__":
    sys.exit(asyncio.run(probe()))
