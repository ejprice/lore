# REPORT-probe-esc1-closure-1 — ESC-1's measurement: is the ancestor closure of NEW dependencies fully PERSISTED at write time?

*Persistence note (added by `design-sidecar-04b2-1`, 2026-08-01): the probe ran as an
Agent-tool subagent and the harness REFUSED its report-file Write with a hard tool policy
("Subagents should return findings as text, not write report files") — a behaviour the
teammate-spawned probes earlier this session did not hit. The probe returned this full
report as its final text; the sidecar persisted it here byte-faithfully (HTML entities
de-escaped) so the instrument and receipts survive. Everything below the line is the
probe's own report, verbatim.*

---

brief-base v9 read
brief project v7 read
state: done-with-deviations
deviations: (1) report FILE blocked by harness policy — content returned as text; (2) probe
script lives in a scratchpad (unrecoverable address) → pasted VERBATIM in §6; (3) the
harness/sweep patterns (`_seed_legacy_task`, `legacy_task_ddl`) were RE-DERIVED with
citations rather than imported — neither `loremaster/tests/` nor `scripts/` is importable
from a standalone script, and the spawn brief directed the derive-by-removal explicitly;
(4) the probe's edge read branches on `INFO FOR DB` table presence (fact-shaped), because
`SELECT … FROM blocks` RAISES `NotFoundError` on the legacy world rather than returning
`[]` (§5.4).
Packages considered: none bespoke — the probe RIDES the shipped mechanisms it measures
(`TaskLedger` verbs, `loremaster.store._txn.bootstrap_session`/`execute_transaction`,
`surrealdb` SDK 2.0.0; all read in-tree) — verdict: reuse; the only hand-rolled pieces are
the stdlib BFS column walk and the set diff, which ARE the instrument.
decisions-needed: none for the measurement; the CONSEQUENCE (ESC-1: known-bound pin →
defect report deleted-with-fix; write-path cycle read rides edges + client-side batch-local
part) is the 04b-2 kickoff's ruling, not this probe's.
receipts: §6 (verbatim instrument) · §7 (verbatim run output, 58 PASS / 0 FAIL,
grep-derived) · tool-honesty §5.6.

## 1. VERDICT: **YES** — stated with its bound, as a fact

**Measured 2026-08-01 on spike-surreal 3.2.1 (`ws://127.0.0.1:18000`, throwaway DBs
`test_<pid>_<uuid4>`, all dropped), tree `f72e538` (branch `feat/surreal-unification`), by
CONSTRUCTION — three consecutive green runs on fresh DBs.**

When a new task naming blockers B\* is created through the shipped verbs, **every PERSISTED
ancestor of B\* is reachable via persisted `blocks` edges at write time**, with exactly two
residues, both named, both expected:

1. **Batch-local `create_many` siblings** — pre-commit they have NO task row at all
   (measured: bound-RecordID `SELECT` on each → zero rows), so client-side is the only
   place their links CAN live. Post-commit their edges are fully persisted in the same
   transaction (17 pairs ≡ 17 edges at the POST boundary).
2. **Phantom `blocked_by` entries** (legacy fail-open rows naming no task row) —
   column-side only, forever; `ENFORCED` forbids the edge and the backfill skips it LOUDLY
   (`task.backfill.phantom_blocker_skipped` at WARNING, captured live). A phantom has no
   row and therefore no ancestors, so it removes nothing from any *persisted-ancestor*
   closure.

**Bound:** the verdict covers the constructed set in §3 — the legacy-world backfill plus
`create_task` / `create_many` / `supersede_task` on a ≥3-deep branching diamond, a legacy
3-cycle, and a phantom-bearing row — nothing wider. One scoping fact widens its reach
honestly: **no `TaskLedger` verb mutates `blocked_by` after birth** (checked 2026-08-01 at
`f72e538`: the only `SET` sites in `loremaster/loremaster/tasks.py` are the claim CAS's
`owner`/`status`/`claimed_at`/`updated_at` and the supersede stamp's
`superseded_by`/`updated_at`/provenance-event; nothing writes `blocked_by` outside
`CREATE`). So the constructed verbs are the COMPLETE column-writing surface of the shipped
ledger — the residue class cannot grow from a verb this probe did not run, only from raw
writes outside the ledger.

**"What broken state would serve exactly these bytes?"** The negative control (§4) answers:
a store with a deleted edge row does NOT serve these bytes — both instruments visibly
diverge on it, naming the exact pair.

## 2. Question and method

Packet `docs/plans/v2/04-comms-blocks-footer.md`, `### ✅ r6's TWO ESCALATIONS — RULED`
(ESC-1) + the `INHERITED FROM 04b-1` ESC-1 row: *"is the ancestor closure of the NEW
dependencies fully PERSISTED at write time?"* Answered by CONSTRUCTION (trust doctrine
Leg-2), never by reasoning from the invariant pins. Store law honoured: edge sets counted
as edge ROWS (`SELECT record::id(in), record::id(out) FROM blocks`) — never traversals, per
`docs/reference/surrealdb-31-capabilities.md` §6.4 (a traversal lists a DANGLING endpoint
as a first-class member); all endpoints and traversal starts BOUND as `RecordID`s per
§2/§4/§7.

## 3. Constructions and boundaries (DB1, one continuum, as briefed)

**Legacy world** (pre-04b-1 DDL derived by REMOVAL from `generate_task_ddl()`, predicate
`" blocks TYPE RELATION"`, RAISES if removal removes nothing; verified `blocks` absent from
`INFO FOR DB`, ZERO edges): raw-CREATE rows, no edges — diamond
`leg_e → leg_d → {leg_b, leg_c} → leg_a` (3 deep, branching both directions); 3-cycle
`leg_x → leg_y → leg_z → leg_x`; phantom-bearing `leg_p ← [phantom_<hex>, leg_a]`.

- **Boundary 1 — `ensure_ready()` backfill:** 9/9 edges minted (cycle edges INCLUDED — the
  mirror mirrors reality); phantom skip AND legacy cycle both RECORDED at WARNING
  (`task.backfill.phantom_blocker_skipped`, `task.backfill.legacy_cycle_minted`, captured
  live). Diff clean both ways. Closures: `leg_e` (4 ancestors), cycle member `leg_x` (3 —
  including ITSELF via the loop, `truncated=False`), phantom-bearing `leg_p` (1 persisted +
  named phantom residue) — column walk ≡ shipped `transitive_blockers` ≡ raw
  `@.{1..32+collect}(<-blocks<-task)`, all three, every leg.
- **Boundaries 2–3 — `create_task` chains:** `F ← [leg_e, leg_d]`, `G ← [F]`. Diff clean at
  each commit; closure(F)=5, closure(G)=6, three-way agreement.
- **Boundary 4 — `create_many`, THE LOAD-BEARING LEG:** pre-minted ids; `M1 ← [G]`,
  `M2 ← [M1, leg_e]`, `M3 ← [M2, M1]` (forward sibling refs AND persisted ancestors).
  **PRE-commit (the write-time view a guard would read):** B\* = {G, M1, leg_e, M2}; for
  BOTH persisted members (G, leg_e) the full persisted ancestor closure was already
  edge-reachable (three-way agreement, 6 and 4 ancestors); both batch-local members had NO
  row — the named, expected residue. **POST-commit:** all 5 new edges landed in the same
  transaction; diff clean; closure(M3)=9 ancestors, three-way agreement.
- **Boundary 5 — `supersede_task` on a task WITH dependents (`leg_d`):** diff clean; the
  superseded row KEEPS its `blocked_by` column `['leg_b','leg_c']` AND its incoming edges
  (row kept, no §4 cascade); successor born with zero deps/edges (`ids=[]`); dependents'
  closures unchanged and three-way agreed. No rewiring, no divergence.

## 4. Controls

- **Positive:** every healthy leg above (58 checks).
- **Negative (fresh DB2, healthy diamond via the verbs):** one edge row (`b2→d2`) deleted
  directly with `RETURN BEFORE` asserting exactly one row — the mutation LANDED (#194's
  law). The pair diff then reported **exactly** `{(b2, d2)}` missing; the closure
  comparison diverged **exactly** by `{b2}` with `a2` correctly retained via `c2` (shipped
  and raw agreeing with each other, disagreeing with the column walk). Both instruments SEE
  the thing they elsewhere report absent — the §3 clears are not blind.

## 5. Facts found on the way (each dated 2026-08-01, `f72e538`, spike-surreal 3.2.1)

1. **The backfill mints legacy-cycle edges**, so a write-path cycle read riding edges WILL
   see legacy cycles; measured: a cycle member's edge closure contains ITSELF
   (`leg_x ∈ closure(leg_x)`, `truncated=False`) — self-reachability is the usable cycle
   signal for whoever builds that read.
2. **Supersession neither rewires nor severs** — dependents keep pointing (column AND edge)
   at the superseded row; the successor starts clean.
3. **No verb mutates `blocked_by` after birth** — the constructed verb set is the complete
   shipped column-writing surface (§1's scoping fact).
4. **`SELECT … FROM blocks` on a store whose DDL predates the relation RAISES
   `NotFoundError`** (it does NOT return `[]`). Any reader that could run before
   `ensure_ready` must branch on the fact (`INFO FOR DB`), not a caught exception. Not
   filed as friction: no shipped read runs before `ensure_ready`.
5. **`create_task` ids are `uuid4().hex` and can begin with a digit** — store reference
   §7's numeric-looking-literal trap applies to any hand-written query over task ids; bind
   `RecordID`s (this probe does throughout).
6. **Tool honesty:** lore tools available but not needed for structure questions — the
   brief named every file/symbol exactly, so orientation used Read/grep on named files only
   (no semantic where-is arose; no lore weakness hit, nothing to file). `lore_comms
   action=register` done (session `pkt04b2-sidecar`, role `probe`); brief `project` v7
   acked via register.

## 6. The instrument, VERBATIM (deliverable — `scripts/` was outside my writable set; run with `/home/ejprice/PycharmProjects/lore/.venv/bin/python <file>`; exits 0 iff every check passes; refuses any URL that is not the spike test store)

```python
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
import os
import sys
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from pydantic import SecretStr
from surrealdb import AsyncSurreal, RecordID

import loremaster
from loremaster.store._txn import bootstrap_session, execute_transaction, signin_credentials
from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE, generate_task_ddl
from loremaster.tasks import STATUS_OPEN, TaskLedger

# --- topology (harness conventions; spike defaults; PRODUCTION REFUSED) -------
URL = os.environ.get("LORE_TEST_SURREAL_URL", "ws://127.0.0.1:18000/rpc")
USER = os.environ.get("LORE_TEST_SURREAL_USER", "root")
PASSWORD = SecretStr(os.environ.get("LORE_TEST_SURREAL_PASS", "spikeroot"))
NAMESPACE = "lore_test"
assert "18500" not in URL, f"REFUSING: {URL!r} looks like production lore-surreal"
assert "127.0.0.1:18000" in URL, f"REFUSING: {URL!r} is not the spike test store"

PHANTOM_BLOCKER = f"phantom_{uuid.uuid4().hex}"  # names NO task row, ever
FAILURES: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"{'PASS' if ok else 'FAIL'}  {label}" + (f"  [{detail}]" if detail else ""))
    if not ok:
        FAILURES.append(label)


def unique_database() -> str:
    """Mirror _surreal_harness.unique_database(): test_<pid>_<uuid4>."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"


async def connect_admin(database: str) -> Any:
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=PASSWORD))
    await bootstrap_session(connection, NAMESPACE, database, url=URL)
    return connection


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
        f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=_acquire, drop=_never_drop, url=URL
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


async def teardown(database: str) -> None:
    connection = AsyncSurreal(URL)
    await connection.signin(signin_credentials(user=USER, password=PASSWORD))
    await connection.use(NAMESPACE, database)
    await connection.query(f"REMOVE DATABASE IF EXISTS {database}")
    await connection.close()


async def legacy_continuum() -> None:
    """DB1: constructions 1–4 + positive control (a)."""
    database = unique_database()
    print(f"\n=== DB1 (legacy continuum): {database} ===")
    connection = await connect_admin(database)
    ledger = TaskLedger(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=PASSWORD
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
                connection, ledger, blocker, f"boundary-4 PRE-commit persisted blocker"
            )
        for sibling in sibling_deps:
            rows = await connection.query(
                f"SELECT record::id(id) AS id FROM $r", {"r": RecordID(TASK_TABLE, sibling)}
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
        await teardown(database)
        print(f"=== DB1 dropped: {database} ===")


async def negative_control() -> None:
    """DB2: control (b) — prove the instrument SEES a divergence."""
    database = unique_database()
    print(f"\n=== DB2 (negative control): {database} ===")
    connection = await connect_admin(database)
    ledger = TaskLedger(
        url=URL, namespace=NAMESPACE, database=database, user=USER, password=PASSWORD
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
        await teardown(database)
        print(f"=== DB2 dropped: {database} ===")


async def main() -> int:
    print(f"probe-esc1-closure-1  {datetime.now(UTC).isoformat()}")
    print(f"loremaster.__file__ = {loremaster.__file__}  (the REAL tree, deliberately)")
    print(f"store = {URL}  namespace = {NAMESPACE}")
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
```

## 7. Run receipts (third run, 2026-08-01, tree `f72e538`; counts DERIVED: `grep -c '^PASS'` = 58, `grep -c '^FAIL'` = 0, exit 0; runs 1 and 2 reached the identical verdict on different throwaway DBs)

Key lines (full output was 90 lines; the decisive ones):

```
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py  (the REAL tree, deliberately)
PASS  [legacy] blocks table ABSENT under the derived legacy DDL  [tables=['task']]
PASS  [legacy] ZERO edges before boot  [edges=set()]
PASS  [backfill] phantom skip RECORDED at WARNING  [events=['task.backfill.phantom_blocker_skipped']]
PASS  [backfill] legacy cycle RECORDED at WARNING  [events=['task.backfill.legacy_cycle_minted']]
PASS  [boundary-1 backfill] column⇒edge: every (blocker,task) with a REAL blocker row has an edge  [9 pairs]
PASS  [boundary-1 backfill] edge⇒column: no edge row the columns do not imply  [9 edges]
NOTE  [boundary-4 PRE-commit] batch B* = ['b212a24f…', 'batch_m1_2ce521e6', 'batch_m2_a50409ad', 'leg_e']; persisted = ['b212a24f…', 'leg_e']; batch-local (EXPECTED residue) = ['batch_m1_2ce521e6', 'batch_m2_a50409ad']
PASS  [boundary-4 PRE-commit persisted blocker] closure(b212a24f…): edges (shipped) == persisted column closure  [6 ancestors]
PASS  [boundary-4 PRE-commit persisted blocker] closure(leg_e): edges (shipped) == persisted column closure  [4 ancestors]
PASS  [boundary-4 PRE-commit] batch-local batch_m1_2ce521e6 has NO row yet (client-side is the only place it can live)
PASS  [boundary-4 POST create_many] column⇒edge … [17 pairs] / edge⇒column … [17 edges]
PASS  [boundary-4 POST create_many (deep B*)] closure(batch_m3_9e1a94ad): edges (shipped) == persisted column closure  [9 ancestors]
PASS  [boundary-5] superseded leg_d keeps its blocked_by column  [col=['leg_b', 'leg_c']]
PASS  [boundary-5] superseded leg_d keeps its incoming edges
PASS  [control] the edge deletion LANDED (exactly one row returned)
PASS  [control] diff CATCHES the divergence (exactly the deleted pair missing)  [missing=[('98ec336b…', '0075ddce…')]]
PASS  [control] closure comparison CATCHES it (column-only == {b2}; a2 kept via c2)
VERDICT INPUT: every check PASSED; residue limited to the named phantom and the named batch-local siblings.
```

---

**VERDICT: YES** — the ancestor closure of new dependencies IS fully persisted at write
time, on the constructed set named above (measured 2026-08-01, `f72e538`, spike-surreal
3.2.1); batch-local `create_many` siblings and legacy phantom entries are the only residue,
both enumerated.
