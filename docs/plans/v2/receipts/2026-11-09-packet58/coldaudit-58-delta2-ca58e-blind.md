# Cold audit, packet 58, second delta: contract-blind diff read (ca58e-blind)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read
- State: done. Dimension: a contract-blind read of `git diff cdf1ce4 8679385 -- loremaster/loremaster`, set against `aa4ea04..8679385`.
- Deviations: (1) No `Agent` tool in this run, so the FAN-OUT routing (probe runs to a haiku-worker) was impossible and every probe ran inline. (2) Read the 12-line header diff of `coldaudit_cycle_04b3_fork_a_refute.py` because the brief's inventory item 4 names it; the body was not read. (3) Read the builder's report only for lines that mention `probe_guard_input`.
- Packages considered: none, no mechanism specified (probes use the stdlib, the ledger and the harness env).
- Odoo-20 portability: n/a, no Odoo seam touched.
- Reuse ledger: none (no production code written).
- Graded: 8679385 · HEAD-at-report: 8679385 · SAME
- Verdict: no product defect found in this round's delta. All four `blocked_by` writers call the one predicate over the one input. The lock serialises in-process supersedes: 20/20, with a two-ledger positive control writing the cycle 20/20. A create cannot close a cycle jointly with a supersede: 0/20.
- Findings: F1 MAJOR (not a product defect). `scripts/probe_guard_input_58.py` is named as the `task.guard.graph_large` re-open instrument in two production comments, and it is not in the tree. F2 and F3 MINOR stale or false prose. F4 MINOR archive header. Residuals R1 to R3.
- Decisions needed: F1. Commit the probe, which exists only in session scratchpad `6538f73f…/scratchpad/probe_guard_input_58.py`, or re-point both comments at a committed instrument.
- Receipt pointers: §Probes (P1 cost, P2 joint cycle, P3 cancel vs lock; instruments pasted verbatim in §Instruments), §Findings, §Removed-behaviour inventory.

## Routing table (written before the sweeps; FAN-OUT clause)
| step | tier | who | reason |
|---|---|---|---|
| sweep of `blocked_by` writes / retired names | 1 (small parallel batch) | self, inline | 3 greps over 76 prod files, output read in full; no `Agent` tool |
| diff read, writer-to-guard map, docstring claims | 3 | self | audit judgment |
| probes P1 to P3 (TEST store) | 1 | self, inline | no `Agent` tool; on the critical path |
Fan-out: haiku 0 · sonnet 0 · peak 0 (capability: no `Agent` tool).

## Provenance
Scratch copy built with `scripts/scratch_copy.sh` (EXIT=0), then `git checkout 8679385 -- .`. `HEAD=86793850c0563a52c9d4f74961ef522d444a2386`, `TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73` (DIRTY_FILES=5 are the untracked root `REPORT-*.md` that `cp` carried). `loremaster.__file__` = `<scratch>/ca58e/ca58e-blind/loremaster/loremaster/__init__.py`, printed by every probe. No pytest was run.

## Q1: every `blocked_by` writer reads the guard input and calls the one predicate (CONFIRMED at 8679385)
Grep sweep (scratch copy, not indexed; grep case (c), a cross-cutting map): 76 prod files; `blocked_by` appears in tasks.py (139), server.py (51) and surreal_schema.py (7). Write sites in tasks.py:
- `create_task`: `_refuse_a_cycle({task_id: dependencies})`, then `_new_task_content`.
- `create_many`: `_refuse_a_cycle(dict(zip(minted_ids, dependencies)))`, then `_new_task_content`.
- `supersede_task`: `_refuse_a_cycle({new_id: deps, **rewired}, minted={new_id})` inside `async with self._supersede_lock`. The successor `_new_task_content` and `_reanchor_fragments` (the `array::map` rewrite) ride one transaction.
- the boot heal: `_reanchor_stragglers` → `_skip_cycle_closing_rows` → `_read_dependency_graph` + `find_row_blocked_by_cycles(all_or_nothing=False)`, then `_plan_heal_rows` → `_reanchor_fragments`.
- `claim_task` mentions `blocked_by = $param` only as a CAS conjunct and writes nothing. `transition` does not touch the column.
`_refuse_a_cycle` and `_skip_cycle_closing_rows` both call `_read_dependency_graph()`, which runs `_DEPENDENCY_COLUMNS_STATEMENT`. The boot mirror read `_read_mirror_state` uses the same constant, and `len(columns)` feeds the `graph_large` WARNING, so the count and the guard input are the same population.

## Q2 and Q3: input completeness, the lock, racing writers (constructed, P2)
The input is every row with a non-empty column, whatever its status. A row with an empty column is a leaf. Pending rows are overlaid as `proposed`: create_many siblings, and the supersede successor through `minted`. The lock is held only by `supersede_task`, from `_select_row` through the transaction and its lost-race reads. `claim_task`, `transition`, `create_task`, `create_many` and reads do not take it, which matches the docstring. Argument for why that suffices in-process: a freshly minted row has no in-edge, so a create cannot be an interior node of a cycle. Only the supersede rewrite and the heal rewrite change an existing row's column, and the heal runs once at boot, awaited before serving (`server.py` awaits `task_ledger.ensure_ready()`). The live `lore-lore` container runs one python process (`podman top`), with HTTP transport (`.mcp.json`).
P2, 20 reps per leg, a fresh TEST database each. Shape: X' -> Dy -> Y' -> Dx -> X', which neither supersede closes alone.
- Leg A, ONE ledger, both supersedes concurrent: `cycles_written=0`, outcomes `('ok','TaskCycleError')` x20.
- Leg B, TWO ledgers (the #634 two-process bound), as a POSITIVE CONTROL for the detector: `cycles_written=20`, `('ok','ok')` x20. The docstring's KNOWN BOUND is real and the detector sees cycles.
- Leg C, ONE ledger, supersede X racing 4x `create_task(blocked_by=[X])`: `cycles_written=0`. Outcomes `('SupersedeStragglerError','ok'x4)` x20, and no straggler left naming a superseded X.

## Q4: removed-behaviour inventory (cdf1ce4..8679385)
| removed | verdict |
|---|---|
| `_bounded_dependency_graph` closure read (seeded ancestor closure over `blocks` edges) | dropped deliberately and replaced by a superset (every column). No cycle the closure saw is lost, and rows with a column but no edge (stragglers) are now seen. |
| closure seed computation in `_refuse_a_cycle` / `_skip_cycle_closing_rows` | dropped. The early returns are preserved: `if not any(pending.values())` and `if not built`. |
| `TIMEOUT 5s` on the guard read | dropped deliberately. The read now runs under the 30 s request timeout (`SURREAL_REQUEST_TIMEOUT_SECONDS`), so a huge graph becomes a slow write rather than a loud refusal at 5 s. `_TRAVERSAL_TIMEOUT` survives for `transitive_blockers` (tasks.py `FROM $tb_start TIMEOUT`). |
| depth bound `TASK_BLOCKER_MAX_DEPTH` in the guard (the #635 truncation) | dropped (closes #635). The constant survives for `transitive_blockers`. |
| `_CLOSURE_START_PARAM` | deleted; bare grep finds 0 residual references in prod. |
| `record::id(id)` decode | preserved in `_DEPENDENCY_COLUMNS_STATEMENT`. |
| phantom-seed tolerance | moot (no seeds); a phantom blocker is a leaf. |
| the dependency on the ESC-1 premise (edges backfilled before the guard runs) | removed; the guard is column-only. |
| FORK A probe | moved to `docs/plans/v2/receipts/2026-11-09-packet58/` with a DUAL header; see F4. |

## Q5: prose that claims what the code does not do
See F1 to F4. Checked and true: the supersede docstring's lock scope and its unlocked-verb list. "a 3 332-dependent hub holds it about 10 s" matches the `max_reanchor_dependents` measurement (10.15 s); P3's 3 001-dependent control ran 7.2 to 7.9 s. "about 0.18 s with the predicate at 19 200 rows" matches P1 (0.106 + 0.074 at 20 000). The `find_blocked_by_cycle` direction reversal is true: graphlib gives `['a','c','b','a']` for a->b->c->a, and the ledger returns `['a','b','c','a']`, the same direction as `find_row_blocked_by_cycles`. No served tool text names the closure, the 32 hops or FORK A (bare grep of server.py).

## Q6: cost (P1, TEST store, 20 000 dependency-bearing rows, median of 5)
`_read_dependency_graph` = 0.106 s · predicate = 0.074 s · `create_task` with 1 blocker = 0.209 s against 0.003 s with none (about 70x, all of it the guard). Adding 100 000 EMPTY-column rows moved the read to 0.112 s and the create to 0.223 s. So the WARNING's metric (dependency-bearing rows) is the right cost driver; the sibling hypothesis that total table size dominates was tried and refuted. `TASK_GUARD_GRAPH_LARGE_ROWS` (20 000) has exactly one use site (`_backfill_blocks_edges`); no other copy of the threshold exists in prod or scripts.

## Findings
- **F1 MAJOR, product_defect=false, HIGH.** The `task.guard.graph_large` re-open instrument does not exist in the tree. The comment above `TASK_GUARD_GRAPH_LARGE_ROWS` and the `_read_dependency_graph` docstring both say a boot that emits the WARNING must re-run `scripts/probe_guard_input_58.py`. Checks at 8679385: `git ls-files | grep guard_input` is empty, `git log --all -- '*probe_guard_input*'` is empty, and `find` over the repo is empty. The only copy is `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/6538f73f-516b-432a-a2c8-634ee44d39c9/scratchpad/probe_guard_input_58.py`, a session scratchpad that is unrecoverable by construction. The builder's report flagged this at 9fd7f8c and it shipped anyway. The trigger fires, but its remedy names nothing runnable: the dropped-rider class.
- **F2 MINOR, product_defect=false, HIGH.** Two engineer-facing docstrings still describe the deleted closure read. `find_row_blocked_by_cycles` Args says ``stored: … — the bounded ancestor closure of the proposed blockers``. `_skip_cycle_closing_rows` says "ONE closure read seeded by every proposed blocker". At 8679385 both callers pass `_read_dependency_graph()`, every dependency-bearing row, unseeded. These are natural-language residues of the rename that the sweep missed.
- **F3 MINOR, product_defect=false, HIGH.** The `TASK_GUARD_GRAPH_LARGE_ROWS` comment calls 20 000 "the largest size the guard's input was measured at", then lists 300 / 2 400 / 19 200. The constant is not a measured size. P1 now supplies a 20 000-row measurement (0.18 s), so the cost claim holds; the sentence does not.
- **F4 MINOR, product_defect=false, HIGH.** The FORK A archive header says the probe "fails at line 161 on the deleted attribute", but the `_bounded_dependency_graph` call is at line 171, because the 10 added header lines shifted it (the cite-symbols-not-lines class). It also says "(The lead moves it … at commit.)" although it is already at that path.

## Residuals
- **R1 PLAUSIBLE, LOW, product_defect=false.** Cancellation releases `_supersede_lock` before the transaction's outcome is known. In P3, 3 of 22 supersedes that raised `CancelledError` mid-transaction COMMITTED anyway (delays 6.5 s, 6.71 s and 7.2 s); the docstring's "held … until the transaction returns" is literal-true, but a cancelled MCP request returns before the engine does. No joint cycle was constructed: in every such rep, the following supersede saw the commit and was refused with `TaskCycleError`. Whether a guard read can land inside the commit window is unproven either way. Re-open: any cycle record whose first member is a successor whose creating request was cancelled.
- **R2.** The `graph_large` WARNING is evaluated at boot only. A ledger that crosses 20 000 rows between boots is invisible until the next deploy. The comment says "a boot that emits it", so the claim is honest.
- **R3.** `find_row_blocked_by_cycles` runs synchronously on the server's single event loop: about 74 ms at 20 000 rows per create-with-deps or supersede, growing linearly.
- Sibling not new this round: the guard statement's `array::len(blocked_by)` on a legacy row with a NONE column is the same statement the boot mirror read has run since before aa4ea04. Not probed.

## Probes
Logs in `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/*.log`, each headed by `tree_id.sh` (TREE=aafce77a…) and ending `EXIT=0`. Every run used `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0`, and the TEST store is asserted (`:18000`).
- P1 `probe_guard_cost.py`: LEG1 `read=0.106s predicate=0.074s create(1 dep)=0.209s create(no dep)=0.003s`; LEG2 `(+100000 empty-column rows) dependency-bearing=20005 read=0.112s create(1 dep)=0.223s`.
- P2 `probe_joint_cycle.py`: legs A, B and C as in §Q2.
- P3 `probe_cancel_lock.py`: a CONTROL leg (X committed, then Y refused) and 22 CANCEL reps (delays 1.0, 4.0, 6.5 and a sweep from 6.0 to 7.65 s) gave 0 cycles. Cancelled but committed: 3.

## Instruments (pasted verbatim; per brief-base §1)

### probe_guard_cost.py
```python
"""ca58e-blind probe: cost of the cycle guard's ONE input at 8679385, and what drives it.

Leg 1: 20 000 dependency-bearing task rows (chains of 10). Time _read_dependency_graph, the predicate, and
an end-to-end create_task with one blocker (guard on) vs none (guard skipped).
Leg 2: add N_EMPTY rows with an EMPTY blocked_by (invisible to task.guard.graph_large's count) and re-time
the same read. TEST store only (asserted). Run from the scratch copy root:
    uv run python <this file>
"""
import asyncio
import statistics
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT / "scripts"))
from probe_hub_txn_58 import _surreal_harness, fresh_test_store_env  # noqa: E402

harness = _surreal_harness()
import loremaster  # noqa: E402
from loremaster.tasks import (  # noqa: E402
    TASK_GUARD_GRAPH_LARGE_ROWS,
    TaskLedger,
    find_row_blocked_by_cycles,
)
from surrealdb import RecordID  # noqa: E402

N_DEP = 20_000
CHAIN = 10
N_EMPTY = 100_000
BATCH = 2_000
REPS = 5


async def seed(ledger: TaskLedger, rows: list[tuple[str, list[str]]]) -> None:
    now = datetime.now(UTC)
    for start in range(0, len(rows), BATCH):
        chunk = rows[start : start + BATCH]
        content = []
        for task_id, deps in chunk:
            body = ledger._new_task_content("s", "d", deps, "probe", now)
            body["id"] = RecordID("task", task_id)
            content.append(body)
        await ledger._query("INSERT INTO task $rows RETURN NONE", {"rows": content})


async def timed(coro_factory, reps: int = REPS) -> float:
    samples = []
    for _ in range(reps):
        t0 = time.perf_counter()
        await coro_factory()
        samples.append(time.perf_counter() - t0)
    return statistics.median(samples)


async def main() -> None:
    print("loremaster.__file__", loremaster.__file__)
    env = fresh_test_store_env()
    assert ":18000" in env.url, "TEST store only"
    ledger = TaskLedger(
        url=env.url, namespace=env.namespace, database=env.database, user=env.user, password=env.password
    )
    try:
        await ledger.ensure_ready()
        dep_rows: list[tuple[str, list[str]]] = []
        for index in range(N_DEP):
            task_id = f"d{index:06d}"
            deps = [] if index % CHAIN == 0 else [f"d{index - 1:06d}"]
            dep_rows.append((task_id, deps))
        # chain heads (index % CHAIN == 0) have no deps -> make them depend on a root so every row counts
        dep_rows = [(t, d or ["root"]) for t, d in dep_rows]
        await seed(ledger, [("root", [])])
        await seed(ledger, dep_rows)
        graph = await ledger._read_dependency_graph()
        print("dependency-bearing rows read:", len(graph), "threshold:", TASK_GUARD_GRAPH_LARGE_ROWS)
        read_s = await timed(ledger._read_dependency_graph)
        pred_s = await timed(
            lambda: asyncio.to_thread(
                find_row_blocked_by_cycles, graph, {"new": ["d019999"]}, ["new"], all_or_nothing=True
            )
        )
        create_dep_s = await timed(lambda: ledger.create_task("c", "c", blocked_by=["d019999"], created_by="probe"))
        create_nodep_s = await timed(lambda: ledger.create_task("c", "c", created_by="probe"))
        print(f"LEG1 read={read_s:.3f}s predicate={pred_s:.3f}s create(1 dep)={create_dep_s:.3f}s "
              f"create(no dep)={create_nodep_s:.3f}s")
        await seed(ledger, [(f"e{index:06d}", []) for index in range(N_EMPTY)])
        graph2 = await ledger._read_dependency_graph()
        read2_s = await timed(ledger._read_dependency_graph)
        create2_dep_s = await timed(lambda: ledger.create_task("c", "c", blocked_by=["d019999"], created_by="probe"))
        print(f"LEG2 (+{N_EMPTY} empty-column rows) dependency-bearing={len(graph2)} read={read2_s:.3f}s "
              f"create(1 dep)={create2_dep_s:.3f}s")
    finally:
        await ledger.close()
        await harness.drop_database(env)


if __name__ == "__main__":
    asyncio.run(main())
```

### probe_joint_cycle.py
```python
"""ca58e-blind probe: can a blocked_by write close a cycle jointly with a supersede at 8679385?

Shape (each supersede alone is acyclic; together they close X' -> Dy -> Y' -> Dx -> X'):
    X, Y open; Dx.blocked_by=[X]; Dy.blocked_by=[Y]
    supersede X -> X' blocked_by=[Dy]   (re-anchors Dx onto X')
    supersede Y -> Y' blocked_by=[Dx]   (re-anchors Dy onto Y')
Legs (REPS each, fresh database per rep, TEST store only):
  A  ONE ledger, both supersedes concurrent      -> expect exactly one TaskCycleError, no cycle (the lock)
  B  TWO ledgers (= two processes), concurrent   -> POSITIVE CONTROL for the detector: the #634 bound
  C  ONE ledger, supersede X racing create_task(blocked_by=[X]) x4 (the unlocked verb) -> expect no cycle
After every rep the WHOLE blocked_by column set is read and checked with the ledger's own key-cycle detector.
"""
import asyncio
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts"))
from probe_hub_txn_58 import _surreal_harness, fresh_test_store_env  # noqa: E402

harness = _surreal_harness()
import loremaster  # noqa: E402
from loremaster.tasks import TaskLedger, find_blocked_by_cycle  # noqa: E402

REPS = 20


def new_ledger(env) -> TaskLedger:
    return TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user,
                      password=env.password)


async def all_columns(ledger: TaskLedger) -> dict[str, list[str]]:
    rows = await ledger._query("SELECT record::id(id) AS id, blocked_by FROM task")
    rows = rows if isinstance(rows, list) else [rows]
    return {str(r["id"]): [str(b) for b in (r.get("blocked_by") or [])] for r in rows}


def outcome(result: object) -> str:
    return "ok" if not isinstance(result, BaseException) else type(result).__name__


async def rep(leg: str) -> tuple[tuple[str, ...], bool, int]:
    env = fresh_test_store_env()
    assert ":18000" in env.url, "TEST store only"
    first = new_ledger(env)
    second = new_ledger(env) if leg == "B" else first
    try:
        await first.ensure_ready()
        if second is not first:
            await second.ensure_ready()
        x = await first.create_task("X", "x", created_by="p")
        y = await first.create_task("Y", "y", created_by="p")
        dx = await first.create_task("Dx", "dx", blocked_by=[x], created_by="p")
        dy = await first.create_task("Dy", "dy", blocked_by=[y], created_by="p")
        if leg in ("A", "B"):
            results = await asyncio.gather(
                first.supersede_task(x, subject="X2", description="x2", created_by="p", blocked_by=[dy]),
                second.supersede_task(y, subject="Y2", description="y2", created_by="p", blocked_by=[dx]),
                return_exceptions=True,
            )
        else:
            results = await asyncio.gather(
                first.supersede_task(x, subject="X2", description="x2", created_by="p", blocked_by=[dy]),
                *(first.create_task(f"N{i}", "n", blocked_by=[x], created_by="p") for i in range(4)),
                return_exceptions=True,
            )
        columns = await all_columns(first)
        cycle = find_blocked_by_cycle(columns)
        superseded_refs = sum(1 for deps in columns.values() if x in deps)
        return tuple(outcome(r) for r in results), cycle is not None, superseded_refs
    finally:
        await first.close()
        if second is not first:
            await second.close()
        await harness.drop_database(env)


async def main() -> None:
    print("loremaster.__file__", loremaster.__file__)
    for leg in ("A", "B", "C"):
        outcomes: Counter[tuple[str, ...]] = Counter()
        cycles = 0
        stragglers = 0
        for _ in range(REPS):
            outs, has_cycle, refs = await rep(leg)
            outcomes[outs] += 1
            cycles += has_cycle
            stragglers += refs
        print(f"LEG {leg}: reps={REPS} cycles_written={cycles} rows_still_naming_X={stragglers} "
              f"outcomes={dict(outcomes)}")


if __name__ == "__main__":
    asyncio.run(main())
```

### probe_cancel_lock.py
```python
"""ca58e-blind probe: does a CANCELLED supersede release _supersede_lock while its transaction still commits?

Shape: X has dependent Dx plus FILLERS seeded dependents (to make its supersede's transaction slow); Y has
dependent Dy. supersede X -> X' blocked_by=[Dy] and supersede Y -> Y' blocked_by=[Dx] close
X' -> Dy -> Y' -> Dx -> X' jointly. ONE ledger (the in-process case the lock is meant to close).
  CONTROL  : await supersede X fully, then supersede Y      -> expect TaskCycleError for Y, no cycle
  CANCEL   : start supersede X, cancel its asyncio task after CANCEL_AFTER s (an MCP request cancel does
             exactly this to the handler), then supersede Y at once; settle SETTLE s; read every column.
TEST store only (asserted). Run from the scratch copy root: uv run python <this file>
"""
import asyncio
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts"))
from probe_hub_txn_58 import _surreal_harness, fresh_test_store_env  # noqa: E402

harness = _surreal_harness()
import loremaster  # noqa: E402
from loremaster.tasks import TaskLedger, find_blocked_by_cycle  # noqa: E402
from surrealdb import RecordID  # noqa: E402

FILLERS = 3_000
CANCEL_AFTER = float(sys.argv[1]) if len(sys.argv) > 1 else 1.0
SETTLE = 30.0
REPS = 3


async def seed_fillers(ledger: TaskLedger, blocker: str) -> None:
    now = datetime.now(UTC)
    for start in range(0, FILLERS, 1_000):
        rows = []
        for index in range(start, min(start + 1_000, FILLERS)):
            body = ledger._new_task_content("f", "f", [blocker], "probe", now)
            body["id"] = RecordID("task", f"f{index:05d}")
            rows.append(body)
        await ledger._query("INSERT INTO task $rows RETURN NONE", {"rows": rows})


async def columns(ledger: TaskLedger) -> dict[str, list[str]]:
    rows = await ledger._query("SELECT record::id(id) AS id, blocked_by FROM task")
    rows = rows if isinstance(rows, list) else [rows]
    return {str(r["id"]): [str(b) for b in (r.get("blocked_by") or [])] for r in rows}


async def rep(mode: str) -> str:
    env = fresh_test_store_env()
    assert ":18000" in env.url, "TEST store only"
    ledger = TaskLedger(url=env.url, namespace=env.namespace, database=env.database, user=env.user,
                        password=env.password)
    try:
        await ledger.ensure_ready()
        x = await ledger.create_task("X", "x", created_by="p")
        y = await ledger.create_task("Y", "y", created_by="p")
        dx = await ledger.create_task("Dx", "dx", blocked_by=[x], created_by="p")
        dy = await ledger.create_task("Dy", "dy", blocked_by=[y], created_by="p")
        await seed_fillers(ledger, x)
        sup_x = ledger.supersede_task(x, subject="X2", description="x2", created_by="p", blocked_by=[dy])
        t0 = time.perf_counter()
        if mode == "CONTROL":
            await sup_x
            x_note = f"X done in {time.perf_counter() - t0:.2f}s"
        else:
            task = asyncio.create_task(sup_x)
            await asyncio.sleep(CANCEL_AFTER)
            task.cancel()
            try:
                await task
                x_note = "X finished before cancel"
            except asyncio.CancelledError:
                x_note = f"X cancelled at {time.perf_counter() - t0:.2f}s"
            except BaseException as error:  # noqa: BLE001
                x_note = f"X raised {type(error).__name__}"
        try:
            await ledger.supersede_task(y, subject="Y2", description="y2", created_by="p", blocked_by=[dx])
            y_note = "Y ok"
        except BaseException as error:  # noqa: BLE001
            y_note = f"Y {type(error).__name__}"
        await asyncio.sleep(SETTLE if mode == "CANCEL" else 0)
        cols = await columns(ledger)
        x_row = await ledger._select_row(x)
        cycle = find_blocked_by_cycle({k: v for k, v in cols.items() if not k.startswith("f")})
        return (f"{mode}: x={x}; {x_note}; {y_note}; X.superseded_by={x_row.get('superseded_by') if x_row else None}; "
                f"Dx.blocked_by={cols.get(dx)}; Dy.blocked_by={cols.get(dy)}; cycle={cycle}")
    finally:
        await ledger.close()
        await harness.drop_database(env)


async def main() -> None:
    global CANCEL_AFTER, SETTLE
    print("loremaster.__file__", loremaster.__file__)
    if len(sys.argv) > 2:  # sweep mode: one CANCEL rep per listed delay, shorter settle
        SETTLE = 10.0
        for delay in sys.argv[1:]:
            CANCEL_AFTER = float(delay)
            print(f"delay={delay}", await rep("CANCEL"))
        return
    print(await rep("CONTROL"))
    for _ in range(REPS):
        print(await rep("CANCEL"))


if __name__ == "__main__":
    asyncio.run(main())
```

### P3 sweep log (filtered)
```
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:CONTROL: x=1e381cd2e2c0496695c8d85329444b35; X done in 7.90s; Y TaskCycleError; X.superseded_by=376f7477519b4137a56b7bffa27d37b2; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:CANCEL: x=0fa3bda52a024e248b37fd9f4c40fc8f; X finished before cancel; Y TaskCycleError; X.superseded_by=ca205d08f7f84d2b9aa5eb3395329373; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:CANCEL: x=1a877605218a480ab04d317d7372b40e; X cancelled at 6.57s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:CANCEL: x=56a3dcd2910f468db055a2db320ce295; X cancelled at 6.71s; Y TaskCycleError; X.superseded_by=5bdfee06206a42e1b868214e11661498; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_6.5.log:EXIT=0
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:CONTROL: X done in 7.24s; Y TaskCycleError; X.superseded_by=44aba743360f46fd8b13a1ab75deb247; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:CANCEL: X cancelled at 1.08s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:CANCEL: X cancelled at 1.37s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:CANCEL: X cancelled at 1.05s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock.log:EXIT=0
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.0 CANCEL: x=602a1502d062402185449f0d66a8ccaa; X cancelled at 6.04s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.15 CANCEL: x=e0d3ad83f0b146d8b7f23ad45d148672; X cancelled at 6.42s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.3 CANCEL: x=7f38abc724a54ae7b6b22ccef29bd998; X cancelled at 6.37s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.45 CANCEL: x=9ae25745672748ab998db80dce1b5187; X finished before cancel; Y TaskCycleError; X.superseded_by=047c38b869a44c0887e47184b63d76f8; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.6 CANCEL: x=0aff875c6fad437e80b6dcb76239a75c; X finished before cancel; Y TaskCycleError; X.superseded_by=0075496f93bc4defa19caa0d1603e954; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.75 CANCEL: x=4bc698cab6a34876bcf2e8e40e73d2e8; X cancelled at 7.09s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.9 CANCEL: x=bbeaa1b6356f442687c9d15decc440c8; X cancelled at 7.02s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.05 CANCEL: x=febf7132cb14423dbd7c1c4932cbe484; X cancelled at 7.15s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.2 CANCEL: x=2e6d5a72a7644b0883d152140bcd6020; X cancelled at 7.35s; Y TaskCycleError; X.superseded_by=a24956ef2223490b9f159e92e402c7cf; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.35 CANCEL: x=ea2f46d09a57473caae8ffed0b3af5f9; X finished before cancel; Y TaskCycleError; X.superseded_by=9ca7131ae5524b5db0d0524117e73fd2; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.5 CANCEL: x=642a88db9fce47c89764a58dea1c9fec; X finished before cancel; Y TaskCycleError; X.superseded_by=38e870491436445a94249b0fd1637d44; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.65 CANCEL: x=f21e48e706fc42e88e0564939ea2aa22; X finished before cancel; Y TaskCycleError; X.superseded_by=491c60773a3a40b792972dfa0a38cb0d; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.5 CANCEL: x=59c419d354cd40478eb917c599a4d521; X cancelled at 6.54s; Y TaskCycleError; X.superseded_by=ceee0039cc524054b8363a434dc012fb; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.7 CANCEL: x=2da87d2e7cd3462d8a91f4bfd6cc4884; X cancelled at 6.77s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=6.9 CANCEL: x=d8e1a20f8533431ebdb7cd5f5487a7fd; X cancelled at 7.32s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:delay=7.1 CANCEL: x=2564bdbe1678453eade89140469216f1; X cancelled at 7.41s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_sweep.log:EXIT=0
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:TREE=aafce77a0d9d9dd0f34679445d171b14e873622f35041ccad5ff81b4ceb04d73
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:CONTROL: x=897182044796443f8433a009dedc0325; X done in 7.54s; Y TaskCycleError; X.superseded_by=5182da22aca740a19f7e3ed769ba22c2; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:CANCEL: x=0e7d92a5085f434ca22cde47549d88fe; X cancelled at 4.11s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:CANCEL: x=cd4647fdbf63493baa683f6576f4fe4c; X cancelled at 4.35s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:CANCEL: x=eeb62255d9d14c72a804aee9b3c96511; X cancelled at 4.12s; Y ok; X.superseded_by=None; cycle=None
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58e/ca58e-blind-probes/probe_cancel_lock_4.0.log:EXIT=0
```
