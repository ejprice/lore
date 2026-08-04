#!/usr/bin/env python3
"""probe-esc1-closure-1 — ESC-1's named measurement, by CONSTRUCTION (2026-08-01).

QUESTION (packet 04-comms-blocks-footer, ESC-1): when a new task naming blockers B*
is created, is every PERSISTED ancestor of B* reachable via persisted ``blocks``
edges at write time — so a write-path cycle read could ride edges, with batch-local
``create_many`` siblings the only expected residue?

METHOD: construct worlds on throwaway DBs on spike-surreal (ws://127.0.0.1:18000,
TEST store — NEVER :18500) and MEASURE. Never reason from the invariant pins.

  DB1 (legacy continuum):
    - legacy DDL derived BY REMOVAL from generate_task_ddl() (the
      scripts/forgery_door_sweep.py::legacy_task_ddl pattern; RAISES if the removal
      removes nothing) — a store that never had the ``blocks`` table;
    - raw-CREATE column-bearing rows, NO edges: a 3-deep branching diamond chain,
      a 3-cycle, a phantom blocker (the _seed_legacy_task pattern);
    - boot TaskLedger.ensure_ready() -> backfill;
    - verbs on top: create_task chains, a create_many batch with sibling AND
      persisted deps (pre-minted ids), supersede_task on a task with dependents;
    - at EVERY commit boundary: edge≡column set diff BOTH WAYS over
      (blocker, task) pairs — edge ROWS via SELECT FROM blocks, never traversals
      (store reference §6.4: a traversal lists a DANGLING endpoint as first-class);
    - load-bearing leg: ancestor closures via (i) client column walk,
      (ii) shipped transitive_blockers, (iii) a raw @.{1..n+collect}(<-blocks<-task)
      traversal — equal for every PERSISTED ancestor; residue named individually.
  DB2 (negative control): a healthy world, DELETE one blocks edge row directly,
    prove the diff AND the closure comparison both CATCH the divergence
    (RETURN BEFORE asserts the mutation LANDED — #194).

Exit 0 with a PASS line per check; any unexpected divergence prints FAIL and
exits 1. Output IS the receipt.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from loremaster.store._txn import execute_transaction
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE, generate_task_ddl
from loremaster.tasks import STATUS_OPEN, TaskLedger
from surrealdb import RecordID

import loremaster


# --- topology (via the shared harness seam; spike defaults; PRODUCTION REFUSED) ---
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

PHANTOM_BLOCKER = f"phantom_{uuid.uuid4().hex}"  # names NO task row, ever
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILURES.append(label)


def _fresh_env() -> Any:
    """A ``SurrealEnv`` on a fresh unique test database, via the shared harness seam."""
    return _HARNESS.make_env(database=_HARNESS.unique_database(), dim=_HARNESS.PRODUCTION_DIM)


def legacy_task_ddl() -> str:
    """Today's task DDL minus the blocks RELATION statement — DERIVED by removal
    (scripts/forgery_door_sweep.py::legacy_task_ddl pattern), never hand-written."""
    current = generate_task_ddl()
    kept = [
        statement
        for statement in current.split(";\n")
        if statement.strip() and f" {BLOCKS_RELATION} TYPE RELATION" not in statement
    ]
    legacy = ";\n".join(kept) + ";\n"
    if legacy == current:
        raise RuntimeError(
            "removal removed NOTHING — the 'legacy' world would be today's world; "
            "the emitter's wording moved, re-derive the removal"
        )
    return legacy


async def apply_ddl(connection: Any, ddl: str) -> None:
    """Apply exactly as production does — ONE BEGIN..COMMIT, every status verified."""

    async def _acquire() -> Any:
        return connection

    async def _never_drop(_c: Any) -> None:
        pass

    await execute_transaction(
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=_SURREAL_URL
    )


async def seed_legacy_task(connection: Any, task_id: str, blocked_by: list[str]) -> None:
    """RAW-CREATE a column-bearing row, NO edge — the pre-04b-1 production state
    (test_blocks_edge.py::_seed_legacy_task pattern; CONTENT per store ref §2)."""
    now = datetime.now(UTC)
    content = {
        "subject": f"legacy row {task_id}",
        "description": "written under the fail-open blocked_by, before the blocks edge",
        "status": STATUS_OPEN,
        "blocked_by": blocked_by,
        "provenance": {"created_by": "legacy", "created_at": now.isoformat(), "events": []},
        "created_at": now,
    }
    await connection.query(
        f"CREATE type::record('{TASK_TABLE}', $id) CONTENT $content",
        {"id": task_id, "content": content},
    )


# --- the instrument: edge≡column diff + three closure readers ------------------


async def read_world(connection: Any) -> tuple[set[str], dict[str, list[str]], set[tuple[str, str]]]:
    """(real task-row ids, blocked_by columns, blocks edge ROWS as (blocker, task)).

    Edges are counted as ROWS of the edge table (SELECT in, out FROM blocks) —
    NEVER via a traversal, which lists a dangling endpoint as a first-class member
    (store reference §6.4) and would hide exactly the divergence this probe hunts.
    """
    id_rows = await connection.query(f"SELECT record::id(id) AS id FROM {TASK_TABLE}")
    real_ids = {str(row["id"]) for row in id_rows}
    column_rows = await connection.query(
        f"SELECT record::id(id) AS id, blocked_by FROM {TASK_TABLE} "
        f"WHERE array::len(blocked_by) > 0"
    )
    columns = {
        str(row["id"]): [str(entry) for entry in (row.get("blocked_by") or [])]
        for row in column_rows
    }
    # Branch on the FACT of the table's existence (INFO FOR DB), never on a caught
    # exception: on the legacy world the blocks table does not exist and the engine
    # raises NotFoundError on the SELECT — swallowing that would also swallow a real
    # fault on a world where the table SHOULD exist.
    info = await connection.query("INFO FOR DB")
    tables = info.get("tables", {}) if isinstance(info, dict) else {}
    if BLOCKS_RELATION not in tables:
        return real_ids, columns, set()
    edge_rows = await connection.query(
        f"SELECT record::id(in) AS b, record::id(out) AS t FROM {BLOCKS_RELATION}"
    )
    edges = {(str(row["b"]), str(row["t"])) for row in edge_rows}
    return real_ids, columns, edges


async def diff_boundary(connection: Any, boundary: str) -> None:
    """Edge≡column set diff BOTH WAYS; phantom column entries named individually."""
    real_ids, columns, edges = await read_world(connection)
    wanted: set[tuple[str, str]] = set()
    phantoms: list[tuple[str, str]] = []
    for task_id, blockers in columns.items():
        for blocker in dict.fromkeys(blockers):
            if blocker in real_ids:
                wanted.add((blocker, task_id))
            else:
                phantoms.append((blocker, task_id))
    missing_edges = wanted - edges  # column says blocked, edge table silent
    extra_edges = edges - wanted  # edge exists, column does not imply it
    check(
        f"[{boundary}] column⇒edge: every (blocker,task) with a REAL blocker row has an edge",
        not missing_edges,
        f"missing={sorted(missing_edges)}" if missing_edges else f"{len(wanted)} pairs",
    )
    check(
        f"[{boundary}] edge⇒column: no edge row the columns do not imply",
        not extra_edges,
        f"extra={sorted(extra_edges)}" if extra_edges else f"{len(edges)} edges",
    )
    for phantom, task_id in phantoms:
        print(
            f"NOTE  [{boundary}] column-side residue (EXPECTED, phantom names no row): "
            f"blocked_by entry {phantom!r} on task {task_id!r} — no edge possible (ENFORCED)"
        )


async def closure_by_columns(connection: Any, task_id: str) -> tuple[set[str], set[str]]:
    """Client-side BFS over blocked_by columns: (persisted ancestors, phantom entries)."""
    real_ids, columns, _edges = await read_world(connection)
    seen: set[str] = set()
    phantoms: set[str] = set()
    frontier = [task_id]
    while frontier:
        current = frontier.pop()
        for blocker in columns.get(current, []):
            if blocker not in real_ids:
                phantoms.add(blocker)
                continue
            if blocker not in seen:
                seen.add(blocker)
                frontier.append(blocker)
    return seen, phantoms


async def closure_by_raw_traversal(connection: Any, task_id: str, depth: int = 32) -> set[str]:
    """The brief's raw cross-check: @.{1..n+collect}(<-blocks<-task).id, start BOUND
    as a RecordID (store ref §7: always sound; never a bare literal)."""
    rows = await connection.query(
        f"SELECT @.{{1..{depth}+collect}}(<-{BLOCKS_RELATION}<-{TASK_TABLE}).id "
        f"AS upstream FROM $start TIMEOUT 5s",
        {"start": RecordID(TASK_TABLE, task_id)},
    )
    if not rows:
        return set()
    return {
        str(node.id) if isinstance(node, RecordID) else str(node)
        for node in (rows[0].get("upstream") or [])
    }


async def closure_leg(
    connection: Any,
    ledger: TaskLedger,
    task_id: str,
    label: str,
    expected_phantoms: set[str] | None = None,
) -> None:
    """The load-bearing comparison: column walk vs shipped verb vs raw traversal."""
    column_closure, phantoms = await closure_by_columns(connection, task_id)
    shipped = await ledger.transitive_blockers(task_id)
    shipped_ids = set(shipped.ids)
    raw_ids = await closure_by_raw_traversal(connection, task_id)
    check(
        f"[{label}] closure({task_id}): shipped transitive_blockers not truncated",
        not shipped.truncated,
        f"max_depth_used={shipped.max_depth_used}",
    )
    check(
        f"[{label}] closure({task_id}): edges (shipped) == persisted column closure",
        shipped_ids == column_closure,
        f"edge-only={sorted(shipped_ids - column_closure)} "
        f"column-only={sorted(column_closure - shipped_ids)}"
        if shipped_ids != column_closure
        else f"{len(shipped_ids)} ancestors",
    )
    check(
        f"[{label}] closure({task_id}): raw traversal cross-check == shipped",
        raw_ids == shipped_ids,
        f"raw-only={sorted(raw_ids - shipped_ids)} shipped-only={sorted(shipped_ids - raw_ids)}"
        if raw_ids != shipped_ids
        else "agree",
    )
    for phantom in sorted(phantoms):
        expected = expected_phantoms is not None and phantom in expected_phantoms
        print(
            f"NOTE  [{label}] closure({task_id}) column-side residue "
            f"({'EXPECTED' if expected else 'UNEXPECTED'}): phantom {phantom!r} "
            f"— in the column walk, absent from every edge answer"
        )
        if not expected:
            FAILURES.append(f"[{label}] unexpected phantom {phantom!r}")


@dataclass
class Spec:
    """Duck-typed TaskSpecLike (subject/description/blocked_by is the whole contract)."""

    subject: str
    description: str
    blocked_by: list[str] = field(default_factory=list)


async def legacy_continuum() -> None:  # noqa: PLR0915 - a linear construction+measurement probe
    """DB1: constructions 1–4 + positive control (a)."""
    env = _fresh_env()
    print(f"\n=== DB1 (legacy continuum): {env.database} ===")
    connection = await _HARNESS.connect_admin(env)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    # Capture the backfill's WARNING stream — the phantom skip and the legacy-cycle
    # record are part of what ESC-1's world must show (loud, never silent).
    captured: list[logging.LogRecord] = []

    class _Capture(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            captured.append(record)

    handler = _Capture(level=logging.WARNING)
    logging.getLogger("loremaster.tasks").addHandler(handler)
    try:
        # -- construction 1: LEGACY WORLD ------------------------------------
        legacy = legacy_task_ddl()
        await apply_ddl(connection, legacy)
        info = await connection.query("INFO FOR DB")
        tables = info.get("tables", {}) if isinstance(info, dict) else {}
        check(
            "[legacy] blocks table ABSENT under the derived legacy DDL",
            BLOCKS_RELATION not in tables,
            f"tables={sorted(tables)}",
        )
        # diamond chain (≥3 deep AND branching): e -> d -> {b, c} -> a
        await seed_legacy_task(connection, "leg_a", [])
        await seed_legacy_task(connection, "leg_b", ["leg_a"])
        await seed_legacy_task(connection, "leg_c", ["leg_a"])
        await seed_legacy_task(connection, "leg_d", ["leg_b", "leg_c"])
        await seed_legacy_task(connection, "leg_e", ["leg_d"])
        # a legacy 3-cycle
        await seed_legacy_task(connection, "leg_x", ["leg_y"])
        await seed_legacy_task(connection, "leg_y", ["leg_z"])
        await seed_legacy_task(connection, "leg_z", ["leg_x"])
        # a phantom blocker beside a real one
        await seed_legacy_task(connection, "leg_p", [PHANTOM_BLOCKER, "leg_a"])
        _real, _cols, edges_before = await read_world(connection)
        check("[legacy] ZERO edges before boot", not edges_before, f"edges={edges_before}")

        # -- boot: ensure_ready backfills ------------------------------------
        await ledger.ensure_ready()
        phantom_events = [r for r in captured if "phantom" in r.getMessage()]
        cycle_events = [r for r in captured if "cycle" in r.getMessage()]
        check(
            "[backfill] phantom skip RECORDED at WARNING",
            len(phantom_events) >= 1,
            f"events={[r.getMessage() for r in phantom_events]}",
        )
        check(
            "[backfill] legacy cycle RECORDED at WARNING",
            len(cycle_events) >= 1,
            f"events={[r.getMessage() for r in cycle_events]}",
        )
        await diff_boundary(connection, "boundary-1 backfill")
        await closure_leg(connection, ledger, "leg_e", "boundary-1 backfill")
        await closure_leg(connection, ledger, "leg_x", "boundary-1 backfill (cycle member)")
        await closure_leg(
            connection, ledger, "leg_p", "boundary-1 backfill (phantom-bearing)",
            expected_phantoms={PHANTOM_BLOCKER},
        )

        # -- construction 2a: create_task chains off persisted tasks ---------
        task_f = await ledger.create_task(
            "F", "chains off persisted leg_e and leg_d",
            blocked_by=["leg_e", "leg_d"], created_by="probe-esc1-closure-1",
        )
        await diff_boundary(connection, "boundary-2 create_task F")
        await closure_leg(connection, ledger, task_f, "boundary-2 create_task F")
        task_g = await ledger.create_task(
            "G", "chains off F", blocked_by=[task_f], created_by="probe-esc1-closure-1"
        )
        await diff_boundary(connection, "boundary-3 create_task G")
        await closure_leg(connection, ledger, task_g, "boundary-3 create_task G")

        # -- construction 2b + THE LOAD-BEARING MID-BATCH LEG ----------------
        # Pre-minted ids so siblings can reference each other (the dispatcher shape).
        m1, m2, m3 = (f"batch_m{i}_{uuid.uuid4().hex[:8]}" for i in (1, 2, 3))
        specs = [
            Spec("M1", "depends on persisted G", [task_g]),
            Spec("M2", "depends on sibling M1 AND persisted leg_e", [m1, "leg_e"]),
            Spec("M3", "depends on siblings M2 and M1 only", [m2, m1]),
        ]
        batch_ids = {m1, m2, m3}
        batch_deps = {d for spec in specs for d in spec.blocked_by}
        persisted_deps = sorted(batch_deps - batch_ids)
        sibling_deps = sorted(batch_deps & batch_ids)
        print(
            f"NOTE  [boundary-4 PRE-commit] batch B* = {sorted(batch_deps)}; "
            f"persisted = {persisted_deps}; batch-local (EXPECTED residue) = {sibling_deps}"
        )
        # ESC-1's question, measured AT WRITE TIME: for every PERSISTED member of
        # B*, its whole persisted ancestor closure must already ride edges.
        for blocker in persisted_deps:
            await closure_leg(
                connection, ledger, blocker, "boundary-4 PRE-commit persisted blocker"
            )
        for sibling in sibling_deps:
            rows = await connection.query(
                "SELECT record::id(id) AS id FROM $r", {"r": RecordID(TASK_TABLE, sibling)}
            )
            check(
                f"[boundary-4 PRE-commit] batch-local {sibling} has NO row yet "
                f"(client-side is the only place it can live)",
                not rows,
            )
        created = await ledger.create_many(
            specs, created_by="probe-esc1-closure-1", ids=[m1, m2, m3]
        )
        check("[boundary-4] create_many returned the pre-minted ids", created == [m1, m2, m3])
        await diff_boundary(connection, "boundary-4 POST create_many")
        await closure_leg(connection, ledger, m3, "boundary-4 POST create_many (deep B*)")

        # -- construction 2c: supersede_task on a task WITH dependents -------
        d_successor = await ledger.supersede_task(
            "leg_d", subject="D2", description="successor of leg_d",
            created_by="probe-esc1-closure-1",
        )
        await diff_boundary(connection, "boundary-5 supersede leg_d")
        await closure_leg(connection, ledger, "leg_e", "boundary-5 dependent of superseded")
        await closure_leg(connection, ledger, task_f, "boundary-5 dependent of superseded")
        successor_closure = await ledger.transitive_blockers(d_successor)
        check(
            "[boundary-5] successor is born with NO dependencies and NO edges",
            successor_closure.ids == [] and not successor_closure.truncated,
            f"ids={successor_closure.ids}",
        )
        # the superseded row KEEPS its column and its edges (no cascade — row kept)
        _real, cols, edges = await read_world(connection)
        check(
            "[boundary-5] superseded leg_d keeps its blocked_by column",
            cols.get("leg_d") == ["leg_b", "leg_c"],
            f"col={cols.get('leg_d')}",
        )
        check(
            "[boundary-5] superseded leg_d keeps its incoming edges",
            {("leg_b", "leg_d"), ("leg_c", "leg_d")} <= edges,
        )
    finally:
        logging.getLogger("loremaster.tasks").removeHandler(handler)
        await ledger.close()
        await connection.close()
        await _HARNESS.drop_database(env)
        print(f"=== DB1 dropped: {env.database} ===")


async def negative_control() -> None:
    """DB2: control (b) — prove the instrument SEES a divergence."""
    env = _fresh_env()
    print(f"\n=== DB2 (negative control): {env.database} ===")
    connection = await _HARNESS.connect_admin(env)
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database,
        user=env.user, password=env.password,
    )
    try:
        await ledger.ensure_ready()
        a2 = await ledger.create_task("A2", "root", created_by="probe-esc1-closure-1")
        b2 = await ledger.create_task("B2", "x", blocked_by=[a2], created_by="probe-esc1-closure-1")
        c2 = await ledger.create_task("C2", "x", blocked_by=[a2], created_by="probe-esc1-closure-1")
        d2 = await ledger.create_task(
            "D2", "join", blocked_by=[b2, c2], created_by="probe-esc1-closure-1"
        )
        await diff_boundary(connection, "control healthy")
        await closure_leg(connection, ledger, d2, "control healthy")

        # DELETE one edge ROW directly; RETURN BEFORE proves the mutation LANDED (#194).
        deleted = await connection.query(
            f"DELETE FROM {BLOCKS_RELATION} WHERE in = $b AND out = $t RETURN BEFORE",
            {"b": RecordID(TASK_TABLE, b2), "t": RecordID(TASK_TABLE, d2)},
        )
        check("[control] the edge deletion LANDED (exactly one row returned)", len(deleted) == 1)

        # (1) the diff must now report exactly the missing pair
        real_ids, columns, edges = await read_world(connection)
        wanted = {
            (blocker, task_id)
            for task_id, blockers in columns.items()
            for blocker in blockers
            if blocker in real_ids
        }
        missing = wanted - edges
        check(
            "[control] diff CATCHES the divergence (exactly the deleted pair missing)",
            missing == {(b2, d2)},
            f"missing={sorted(missing)}",
        )
        # (2) both closure readers must now DISAGREE with the column walk by {b2}
        column_closure, _ = await closure_by_columns(connection, d2)
        shipped = set((await ledger.transitive_blockers(d2)).ids)
        raw = await closure_by_raw_traversal(connection, d2)
        check(
            "[control] closure comparison CATCHES it (column-only == {b2}; a2 kept via c2)",
            column_closure - shipped == {b2} and shipped == {c2, a2} and raw == shipped,
            f"column={sorted(column_closure)} shipped={sorted(shipped)} raw={sorted(raw)}",
        )
    finally:
        await ledger.close()
        await connection.close()
        await _HARNESS.drop_database(env)
        print(f"=== DB2 dropped: {env.database} ===")


async def main() -> int:
    print(f"probe-esc1-closure-1  {datetime.now(UTC).isoformat()}")
    print(f"loremaster.__file__ = {loremaster.__file__}  (the REAL tree, deliberately)")
    print(f"store = {_SURREAL_URL}  namespace = {_HARNESS.TEST_NAMESPACE}")
    await legacy_continuum()
    await negative_control()
    print(f"\n{'=' * 60}")
    if FAILURES:
        print(f"VERDICT INPUT: {len(FAILURES)} FAILED check(s):")
        for name in FAILURES:
            print(f"  - {name}")
        return 1
    print("VERDICT INPUT: every check PASSED; residue limited to the named phantom "
          "and the named batch-local siblings.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
