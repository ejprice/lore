# coldaudit-58-delta-ca58d-blind — contract-blind read of the packet 58 fix-wave diff (aa4ea04..cdf1ce4)

## SUMMARY BLOCK
- brief-base v27 read · brief project v7 read · landmines recalled (10 returned, k=50)
- State: done-with-deviations
- Deviations: (1) one lore_search hit surfaced a TEST-file docstring chunk (loremaster/tests/test_query_tasks_bounded.py, TestTheBlockedPartitionIsONEHOPNeverTransitive) — withheld material, read incidentally, used for nothing; (2) I briefly copied my probe files into the live tree beside this file and removed them at once (the brief allows ONE writable file); the instruments are pasted verbatim below instead.
- Packages considered: none — no mechanism specified (audit). Read networkx SCC/shortest_path usage only as the graded code's choice.
- Odoo-20 portability: n/a — no Odoo seam touched
- Reuse ledger: none (no symbols written; 3 probe scripts pasted below)
- Graded: cdf1ce4 · HEAD-at-report: cdf1ce4 · SAME
- VERDICT (dimension: contract-blind diff read): **NO-GO** — the diff's central claim ("the heal / every writer never writes a blocked_by cycle; ONE predicate answers it") is false at cdf1ce4 through two doors the predicate itself cannot see, both reproduced live with controls: **F1** concurrent supersedes write a cycle 20/20 (#634); **F2** a loop longer than 32 hops is written by a live supersede AND by the heal (#635). The predicate itself is correct and deterministic over the graph it is given (oracle 20 000 trials × 2 modes, 0 failures).
- Decisions needed: (a) F1/F2 — fix in this packet, or record each as a named bound (finding + docstring + served-text naming) with a re-open trigger: operator/lead call; (b) F3 the served cycle-refusal arrow now points opposite ways for the two vocabularies.
- Receipt pointers: §Findings F1–F5 · §Q1 writer map · §Removed-behaviour inventory · §Instruments (verbatim)

## Routing table (written before the first sweep, brief-base v27 §3)
| step | tier | who | reason |
|---|---|---|---|
| scratch copy + checkout cdf1ce4 + provenance | 1 | self (inline) | 3 commands on the critical path, output read whole |
| read the production diff aa4ea04..cdf1ce4 | 3 | self | the audit itself; contract-blind frame cannot be delegated without re-installing a frame |
| sweep: every write of the blocked_by column in loremaster/loremaster | 1 | self, ONE parallel grep batch | small set (one package, a few patterns), output read whole; coverage line carried |
| removed-behaviour inventory + adjudication | 3 | self | adjudication from code is audit judgment; a sampled draft would miss the per-field provenance the inventory exists to catch |
| prior-art search for new functions | 2→self | self via lore_search + grep | set is <=5 new symbols; inline |
| determinism / soundness probes of the predicate (in-memory) | 3 (write) / 1 (run) | self | probe output is a verdict I judge; tiny run |

Fan-out: haiku 0 · sonnet 0 · peak 0 — every row was either the audit judgment itself or a small sweep run as one parallel batch whose whole output I read; the three probe runs were single short commands on my critical path (run inline; no Agent tool used).

## Provenance
- Scratch copy: `scripts/scratch_copy.sh` EXIT=0, then `git checkout cdf1ce4 -- .`; HEAD=cdf1ce40680aafcb0ffe8d836ff3ae0e506eca68, status: untracked files only.
- `loremaster.__file__` = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/ca58d/ca58d-blind/loremaster/loremaster/__init__.py
- `tree_id.sh` on the copy (header of every probe log): HEAD=cdf1ce4… DIRTY_FILES=6 (the untracked REPORT/receipt files) TREE=1ae664a962bdc87f3d97146d03fb9b055f0bb5fd54525faa6d2c1d451e97f50e
- No pytest run (dimension withholds test runs). Probes ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 timeout 600` on ws://127.0.0.1:18000 only.

## Probe receipts
| probe | command (cwd = scratch copy) | log (scratch, not durable — counts pasted here) | EXIT | count / result lines |
|---|---|---|---|---|
| in-memory oracle | `uv run python ../probes/predicate_inmemory.py` | scratchpad/ca58d/probes/predicate_inmemory.log | 0 | `trials=20000 modes=2 failures=0`; direction: graphlib `['D','X','S','D']` vs new `['S','X','D','S']` |
| depth bound (live) | `systemd-run … uv run python ../probes/probe_depth_bound_cycle.py` | scratchpad/ca58d/probes/probe_depth_bound_cycle.log | 0 | S k=3 REFUSED/none · **S k=40 WRITTEN, cycle len=43** · H k=3 SKIPPED (1 record)/none · **H k=40 REANCHORED (0 records), cycle len=43** · controls_ok=True |
| concurrent supersede (live) | `systemd-run … uv run python ../probes/probe_concurrent_supersede_cycle.py` | scratchpad/ca58d/probes/probe_concurrent_supersede_cycle.log | 0 | CONTROL sequential `(('ok','cycle-refused'), False)` · **ONE ledger concurrent ('ok','ok') cycle=True 20/20** · two ledgers 20/20 · barrier-forced 20/20 |

## Findings

### F1 — MAJOR (product defect, confidence HIGH) — concurrent supersedes jointly write a blocked_by cycle (write skew); lore #634
- Location: `loremaster/loremaster/tasks.py` `TaskLedger.supersede_task` (guard `_refuse_a_cycle` runs on a READ, then `_apply(self._supersede_transaction(...))`); `TaskLedger._refuse_a_cycle`; same read-then-write shape in `_reanchor_stragglers` → `_skip_cycle_closing_rows`.
- Claim: the cycle answer is computed over a closure read outside the write transaction, and the transaction re-checks only `blocked_by CONTAINS old` and the straggler count. Two supersedes over disjoint rows each pass the guard on the pre-state and both commit, closing S1 -> X -> S2 -> D1 -> S1. Run sequentially the second is refused.
- Evidence: probe table row 3 — 20/20 on ONE TaskLedger/connection via `asyncio.gather` (the served shape: one lore server, two concurrent `lore_tasks supersede` calls), with the sequential control refused and acyclic.
- What it breaks: every task on the loop is unclaimable forever, which is the consequence #623/#631 were filed for. No docstring names this bound: `supersede_task`'s Raises (`TaskCycleError: The resolved blocked_by would put the successor on a blocked_by cycle`) and `find_row_blocked_by_cycles`' "The ONE answer" both read as unconditional.
- Packet-58 provenance: the re-anchor that makes supersede a cycle-closing writer is packet 58's. aa4ea04 had the same read-then-write guard, so the fix wave did not introduce this, but its closing claim does not hold against it.
- Reproduce: §Instruments probe_concurrent_supersede_cycle.py.

### F2 — MAJOR (product defect, confidence HIGH) — loops longer than TASK_BLOCKER_MAX_DEPTH (32) are invisible to the guard; supersede and heal both write one; lore #635
- Location: `tasks.py` `TaskLedger._bounded_dependency_graph` (`@.{1..TASK_BLOCKER_MAX_DEPTH+collect}(<-blocks<-task)`, which truncates silently), feeding `find_row_blocked_by_cycles` for all four writers.
- Claim: `_bounded_dependency_graph`'s docstring says "Bounding to the closure therefore loses no cycle; it is sound, not a heuristic". That is false whenever the closing path is more than 32 hops, and `find_row_blocked_by_cycles` names the bound only as the word "bounded".
- Evidence: probe table row 2. Leg S uses public verbs only (create ×43, one supersede): the k=3 control is refused, and at k=40 the supersede commits a 43-member loop. Leg H plants a straggler of the shape a create racing a supersede leaves: at k=3 the heal skips it and records it, and at k=40 it re-anchors it into a 43-member loop with 0 would_close_cycle records. The heal leg is #623's consequence, reopened through a different door.
- Reproduce: §Instruments probe_depth_bound_cycle.py.

### F3 — MINOR (served-text change, confidence HIGH) — the cycle-refusal arrow now points opposite ways for the two vocabularies
- Location: `find_row_blocked_by_cycles` (persisted ids, `[row, blocker, …, row]`, so each arrow reads "is blocked_by") vs `find_blocked_by_cycle` (graphlib, server.py batch keys, `CycleError.args[1]`, so each arrow reads "blocks"). Both are served through `format_cycle_refusal`'s one sentence, "blocked_by cycle among <noun>: a -> b -> …".
- Evidence: in-memory probe leg A on one graph {S:[X], X:[D], D:[S]}: graphlib gives `['D','X','S','D']` and the new predicate gives `['S','X','D','S']`. At aa4ea04 the persisted refusal came from graphlib, so the two refusals agreed. They no longer do.
- Impact: a consumer that learns the arrow meaning from one refusal misreads the other. Every member is still named, so the loop can still be broken. The new direction matches `_record_legacy_cycles` and the heal's record. Removed-behaviour item R2.

### F4 — MINOR (false docstrings, confidence HIGH) — R6 "ONE shared detector" prose is false at cdf1ce4
- `tasks.py` `find_blocked_by_cycle` docstring: "BOTH the write-time guard over PERSISTED ids and server.py's batch-local temp-KEY check route through it … neutralise this and BOTH shapes must stop being refused". At cdf1ce4 only the server.py batch-key check calls it; the persisted guard calls `find_row_blocked_by_cycles`.
- `tasks.py` comment above `CYCLE_NOUN_PERSISTED_IDS`: "over … the ONE shared detector (:func:`find_blocked_by_cycle`)". False.
- `tasks.py` `TaskLedger._record_legacy_cycles` docstring: "DETECTION stays the shared `find_blocked_by_cycle` (R6, one ledger-owned detector)". False. The same docstring says "every legacy cycle the backfill is about to mirror", which is stale now that it runs before the nothing-missing return.
- `server.py` comment above `find_blocked_by_cycle(edges)` in the create_many dispatcher: "ONE cycle detector … both ledger-owned". False.
- The commit message says R6 was "amended to one detector per question (flagged for the operator)". The code prose was not amended.

### F5 — RESIDUAL (reuse, confidence MEDIUM) — the "seed the closure from every proposed blocker, read, ask the predicate" composition is written twice
- `_refuse_a_cycle` and `_skip_cycle_closing_rows` each compute `seeds = {every proposed blocker}`, call `_bounded_dependency_graph(seeds)`, then call `find_row_blocked_by_cycles`. They differ only in `all_or_nothing` and in what they do with a hit (raise vs skip and record). A fix to the seeding or to the closure read (F2's fix lives there) has to land in both. Routing is not sharing: the predicate is shared, but the read that feeds it is cloned. Low cost today (3 lines).

## Q1 — every writer of blocked_by, and whether it reaches the predicate first
Sweep, grep (a non-symbol textual seam: column writes inside SurrealQL strings. The scratch copy is not indexed, so lore cannot answer this): `_COL_BLOCKED_BY|blocked_by` over loremaster/loremaster (76 .py files, 56 hits in production), plus every `CREATE|UPDATE … TASK_TABLE` statement (3 hits), plus scripts/ lorerunes/ loresigil/ lorescribe/ (87 non-test .py files scanned, 12 mention blocked_by, all probes or audit scripts, none a production writer).
| writer | write site | predicate call before the write | mode / asked |
|---|---|---|---|
| `create_task` | `_create_fragment` via `_new_task_content` | `_refuse_a_cycle({task_id: deps})` | replace / the new row |
| `create_many` | `_create_fragment` per spec | `_refuse_a_cycle(dict(zip(minted_ids, deps)))` (the server.py batch-key `find_blocked_by_cycle` also runs first on the served path) | replace / every minted row |
| `supersede_task` successor CREATE + dependents' re-anchor (`_reanchor_fragments` → `_guarded_append_fragment` `array::map` UPDATE) | `_supersede_transaction` | `_refuse_a_cycle({new_id: deps, **rewired}, minted={new_id})` | replace / successor only. Sound: every new edge is D->new_id, so any new loop passes through new_id and lands in its SCC |
| boot heal `_reanchor_stragglers` (`_reanchor_fragments`) | chunks via `_pack_heal_chunks` | `_skip_cycle_closing_rows` → `find_row_blocked_by_cycles(stored, proposed, proposed, all_or_nothing=False)`, once, before packing | stored-plus-proposed / every pending straggler. Sound for any subset of chunks applied: the real post-state is a subgraph of stored ∪ proposed, so a new loop through an applied row P's proposed edge puts that blocker in P's SCC |
| `_backfill_blocks_edges` | writes the `blocks` EDGE only, never the column | n/a (mirror) | — |
Verdict: there is exactly ONE function answering the question, and all four column writers reach it before they write. It does not hold at write time: F1 shows the answer can be stale, and F2 shows the read that feeds it is depth-truncated.

## Q2 — input fates of the changed functions
- `find_row_blocked_by_cycles`: each asked row is either a hit (returned with its cycle) or absent from the result. An asked row with no proposed column is never a hit; callers always ask proposed rows. Stored rows replaced under `all_or_nothing=True` lose their stored edges, which is correct for one transaction. Duplicates are deduped by `sorted(set())`. Oracle (leg B): hit set equals brute-force reachability in 20 000 random graphs × 2 modes. Leg D: every returned cycle is a real path in the graph answered over.
- `_skip_cycle_closing_rows`: each built row is either kept or skipped with one WARNING. `superseded_blockers[dependent]` cannot KeyError: the hit keys are a subset of the proposed keys, which equal the built dependents, which equal the keys of superseded_blockers. An empty built list returns as is.
- `_plan_heal_rows`: phantom or cycled-head rows are skipped and recorded, unchanged from aa4ea04, and they are absent from `proposed`, so their stored column correctly stays in the graph when reached. A planned row lands in both `built` and `proposed`.
- `_refuse_a_cycle`: pending with all-empty values returns early (no wire). Otherwise it raises on `cycles[min(cycles)]` (deterministic) or returns.

## Removed-behaviour inventory (from code and docstrings only)
| # | removed / replaced | verdict |
|---|---|---|
| R1 | `_drop_one_cycle_edge` and the `while True` step-over loop in `_refuse_a_cycle`, including its silent `return` (allow) when no edge could be dropped | dropped deliberately. Old bug: unsound (#631). The replacement equals reachability by oracle |
| R2 | the persisted refusal's cycle order (graphlib: blocker→dependent) | CHANGED to dependent→blocker. See F3 (unflagged served-text change) |
| R3 | which loop is reported among several (graphlib's first containing a minted node) | now the min asked row, its first sorted SCC blocker and the shortest path back. Deterministic (leg C) |
| R4 | `_still_claimable` | dropped. Dead at aa4ea04: `git grep -c _still_claimable aa4ea04` gives 1 in production (the def only) |
| R5 | `_record_legacy_cycles` call after the `if not missing: return` | moved before it. At aa4ea04 a store with every mirror edge present never recorded legacy loops, so the "every boot" claim was false there and is true now. The docstring is stale (F4) |
| R6 | `_CLAIM_LOST_PREFIX`, `_CAS_LOST_MARKER`, `_REANCHOR_STRAGGLER_MARKER`, `_HEAL_CHUNK_MARKER` | replaced by public `_txn` constants with the same values. Every message the f-strings build is byte-identical to the old literals (read). Grep for the old names across members and scripts: 0 hits |
| R7 | claim refusal "…so this claim can never win: block on the successor instead" | now "…a SUPERSEDED blocker can never resolve: block on the successor instead". True. #629 already ledgers the skipped-straggler case |
| R8 | hub refusal "This is a pinned KNOWN BOUND (58 F-1); file it with lore_findings." | replaced with a #628 citation. "A hub near that size can … time out" is loose: the measured timeout band starts at ~5 700 dependents, about one third of the 16 665 cap. Not a false clear, since the refused caller is above the cap. Noted, not a finding |
| R9 | `StragglerHealPackerError` "transaction cap" | "heal chunk bound". `row_cap` passed is `min(TXN_ROW_WARN_THRESHOLD, TXN_ROW_HARD_CAP)`, which matches the docstring (read in `_pack_heal_chunks`) |
| R10 | query `status` docs | the new "a status (or blocked) filter excludes SUPERSEDED" matches the code: `exclude_superseded or status is not None` → `superseded_by IS NONE`, and `exclude_superseded=blocked is not None` |
| R11 | claim / dependents / rollup / supersede docstrings | verified true: the claim CAS conjunct `blocked_by = $clm_blocked_by`; `direct_dependents` is called by supersede for straggler detection; re-anchor UPDATEs go through `_guarded_append_fragment`, which stamps `updated_at = time::now()`; `_dependent_rows` has no status filter (terminal dependents included); `SupersedeStragglerError` / `HubSupersedeRefusedError` are raised by supersede |
| R12 | `max_reanchor_dependents` measured timings | NOT re-measured by this dimension (they cite `probe_heal_curve_58.py` part C). Unverified here, not refuted |

## Q4 — prior art for each new symbol
- `find_row_blocked_by_cycles`: nearest are `find_blocked_by_cycle` (graphlib, any-cycle question) and `_record_legacy_cycles` (networkx `simple_cycles`, enumeration). The row-scoped "does THIS row's write close a loop" question is answered by neither, so a new function is justified. The R6 one-detector law now has two detectors, an operator flag per the commit.
- `TaskLedger._skip_cycle_closing_rows`: prior art is `_refuse_a_cycle`. The read-and-ask composition is cloned (F5).
- `_HEAL_WOULD_CLOSE_CYCLE_EVENT`: distinct from `_HEAL_CYCLE_EVENT` (chain-head cycle). No duplicate.
- `CAS_LOST_MARKER` / `REANCHOR_STRAGGLER_MARKER` / `HEAL_CHUNK_MARKER` (made public): these now remove the #624 duplication. findings.py and tasks.py both build from them.

## Q6 — determinism
Leg C: the same inputs with shuffled dict order, shuffled lists and injected duplicates, 20 000 trials × 2 modes, gave identical output (hit set AND cycle path). The construction adds nodes and edges in sorted order, and `shortest_path` tie-breaks on that insertion order, so the result is deterministic for a given input set. The heal's skip SET depends only on SCC membership, so it does not depend on id assignment. Only the recorded path text can depend on ids (sorted order). No counterexample found.

## Instruments (verbatim; run from the scratch copy root, which carries scripts/probe_query_complexity_07.py for the TEST-store wiring)

### predicate_inmemory.py
```python
"""ca58d-blind in-memory probe of tasks.find_row_blocked_by_cycles at cdf1ce4.

Legs: (A) arrow DIRECTION of the new predicate vs the batch-key detector find_blocked_by_cycle on one graph;
(B) brute-force oracle equality over random graphs, both modes; (C) determinism under shuffled dict/list order;
(D) every returned cycle is a real cycle of the graph the predicate claims to answer over.
Exit 0 iff B, C, D hold; prints A's observation."""
import random, sys
import loremaster
from loremaster.tasks import find_row_blocked_by_cycles, find_blocked_by_cycle

print("loremaster.__file__ =", loremaster.__file__)

# (A) direction: S blocked_by X, X blocked_by D, D blocked_by S
g = {"S": ["X"], "X": ["D"], "D": ["S"]}
print("A graphlib batch-key detector:", find_blocked_by_cycle(g))
print("A new persisted predicate     :", find_row_blocked_by_cycles({"X": ["D"], "D": ["S"]}, {"S": ["X"]}, ["S"], all_or_nothing=True))

def reach(graph, src, dst):
    seen, stack = set(), [src]
    while stack:
        n = stack.pop()
        if n == dst:
            return True
        if n in seen:
            continue
        seen.add(n)
        stack.extend(graph.get(n, ()))
    return False

def oracle(stored, proposed, asked, aon):
    graph = {}
    for n, bs in stored.items():
        if aon and n in proposed:
            continue
        graph.setdefault(n, set()).update(bs)
    for n, bs in proposed.items():
        graph.setdefault(n, set()).update(bs)
    hits = set()
    for row in set(asked):
        for b in proposed.get(row, ()):
            if b == row or reach(graph, b, row):
                hits.add(row)
                break
    return hits, graph

rng = random.Random(58)
bad = 0
trials = 20000
for t in range(trials):
    n = rng.randint(2, 9)
    nodes = [f"n{i}" for i in range(n)]
    stored = {x: rng.sample(nodes, rng.randint(0, min(3, n))) for x in nodes if rng.random() < 0.8}
    proposed = {x: rng.sample(nodes, rng.randint(0, min(3, n))) for x in rng.sample(nodes, rng.randint(1, n))}
    asked = rng.sample(sorted(proposed), rng.randint(1, len(proposed)))
    for aon in (True, False):
        got = find_row_blocked_by_cycles(stored, proposed, asked, all_or_nothing=aon)
        want, graph = oracle(stored, proposed, asked, aon)
        if set(got) != want:
            bad += 1; print("B MISMATCH", aon, stored, proposed, asked, got, want); break
        for row, cyc in got.items():  # (D) a real cycle row -> ... -> row along graph edges
            ok = cyc[0] == row and cyc[-1] == row and all(cyc[i + 1] in graph.get(cyc[i], ()) for i in range(len(cyc) - 1))
            if not ok:
                bad += 1; print("D NOT A CYCLE", aon, stored, proposed, row, cyc); break
        # (C) shuffle insertion orders of dicts and lists
        def shuf(m):
            items = list(m.items()); rng.shuffle(items)
            return {k: rng.sample(list(v), len(v)) + list(v)[:1] for k, v in items}  # also inject a duplicate
        again = find_row_blocked_by_cycles(shuf(stored), shuf(proposed), list(reversed(asked)), all_or_nothing=aon)
        if again != got:
            bad += 1; print("C NONDETERMINISTIC", aon, got, again); break
print(f"trials={trials} modes=2 failures={bad}")
sys.exit(1 if bad else 0)
```

### probe_depth_bound_cycle.py
```python
"""ca58d-blind live probe (TEST store only): does a blocked_by cycle LONGER than the closure walk's depth bound
(TASK_BLOCKER_MAX_DEPTH) get written by (S) a live supersede and (H) the boot heal, at cdf1ce4?

Construction, per leg and per chain length k (control k=3, subject k=40):
  S: T0; D blocked_by [T0]; X_k blocked_by [D]; X_{i} blocked_by [X_{i+1}] ... X_0; supersede T0 -> S with
     blocked_by=[X_0]. The re-anchor writes D -> S, closing S -> X_0 -> ... -> X_k -> D -> S.
  H: D (no deps); the same X chain onto D; T0; supersede T0 -> S blocked_by=[X_0] (no dependents, no cycle);
     then a STRAGGLER is planted (D.blocked_by = [T0] + its T0->blocks->D mirror edge, the shape of a create that
     raced the supersede) and the heal _reanchor_stragglers() runs. Re-anchoring D -> S closes the same loop.
Verdict per run: whether the write was refused/skipped, and a WHOLE-TABLE cycle check afterwards
(find_blocked_by_cycle over every row's column — the positive control that the instrument sees a written loop).
Each run mints its own test_<pid>_<uuid> database on ws://127.0.0.1:18000 and removes it."""
import asyncio, logging, os, sys, uuid
import loremaster
from surrealdb import RecordID
from loremaster.tasks import TaskLedger, TaskCycleError, find_blocked_by_cycle, TASK_BLOCKER_MAX_DEPTH
sys.path.insert(0, os.path.join(os.path.dirname(loremaster.__file__), "..", "..", "scripts"))
from probe_query_complexity_07 import NAMESPACE, PASSWORD, URL, USER

assert ":18500" not in URL, URL
print("loremaster.__file__ =", loremaster.__file__, "| TASK_BLOCKER_MAX_DEPTH =", TASK_BLOCKER_MAX_DEPTH, "| store =", URL)

class Grab(logging.Handler):
    def __init__(self):
        super().__init__(); self.events = []
    def emit(self, record):
        self.events.append(record.getMessage())

grab = Grab(); logging.getLogger("loremaster").addHandler(grab); logging.getLogger("loremaster").setLevel(logging.INFO)

async def whole_table_cycle(ledger):
    rows = ledger._as_rows(await ledger._query("SELECT record::id(id) AS id, blocked_by FROM task"))
    return find_blocked_by_cycle({str(r["id"]): [str(b) for b in (r.get("blocked_by") or ())] for r in rows})

async def chain(ledger, onto, k):
    prev = await ledger.create_task("X_k", "probe", blocked_by=[onto], created_by="ca58d-blind")
    for i in range(k - 1, -1, -1):
        prev = await ledger.create_task(f"X_{i}", "probe", blocked_by=[prev], created_by="ca58d-blind")
    return prev  # X_0

async def run(leg, k):
    database = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    ledger = TaskLedger(url=URL, namespace=NAMESPACE, database=database, user=USER, password=PASSWORD)
    grab.events.clear()
    try:
        await ledger.ensure_ready()
        if leg == "S":
            t0 = await ledger.create_task("T0", "probe", created_by="ca58d-blind")
            d = await ledger.create_task("D", "probe", blocked_by=[t0], created_by="ca58d-blind")
            x0 = await chain(ledger, d, k)
            try:
                res = await ledger.supersede_task(t0, subject="S", description="probe", created_by="ca58d-blind", blocked_by=[x0])
                outcome = f"WRITTEN reanchored={len(res.reanchored)}"
            except TaskCycleError as error:
                outcome = f"REFUSED TaskCycleError ({str(error)[:60]}...)"
        else:
            d = await ledger.create_task("D", "probe", created_by="ca58d-blind")
            x0 = await chain(ledger, d, k)
            t0 = await ledger.create_task("T0", "probe", created_by="ca58d-blind")
            await ledger.supersede_task(t0, subject="S", description="probe", created_by="ca58d-blind", blocked_by=[x0])
            await ledger._query("UPDATE $d SET blocked_by = [$t]", {"d": RecordID("task", d), "t": t0})
            await ledger._query("RELATE $t->blocks->$d", {"d": RecordID("task", d), "t": RecordID("task", t0)})
            before = (await ledger.get_task(d)).blocked_by
            await ledger._reanchor_stragglers()
            after = (await ledger.get_task(d)).blocked_by
            skipped = [e for e in grab.events if "would_close_cycle" in e]
            outcome = (f"straggler D before={'[T0]' if before == [t0] else before} after="
                       f"{'[T0] (SKIPPED)' if after == [t0] else 'REANCHORED'} would_close_cycle_records={len(skipped)}")
        cyc = await whole_table_cycle(ledger)
        print(f"leg={leg} k={k} chain_hops_to_D={k + 1}: {outcome} | whole-table cycle after: "
              f"{'YES len=' + str(len(cyc) - 1) if cyc else 'none'}")
        return cyc
    finally:
        try:
            await ledger._query(f"REMOVE DATABASE {database}")
        finally:
            await ledger.close()

async def main():
    results = {}
    for leg in ("S", "H"):
        for k in (3, 40):
            results[(leg, k)] = await run(leg, k)
    # controls must show NO cycle (refused / skipped); subjects are the question
    bad_control = [key for key in results if key[1] == 3 and results[key]]
    print("controls_ok =", not bad_control)
    return 0 if not bad_control else 2

sys.exit(asyncio.run(main()))
```

### probe_concurrent_supersede_cycle.py
```python
"""ca58d-blind live probe (TEST store only): can TWO CONCURRENT supersedes jointly write a blocked_by cycle that
either one alone (sequentially) is refused for? (write skew across the read-then-write cycle guard, cdf1ce4)

Fixture per attempt: T1, T2; D1 blocked_by [T1]; X blocked_by [T2].
  supersede A: T1 -> S1 blocked_by [X]   (re-anchors D1 -> S1)
  supersede B: T2 -> S2 blocked_by [D1]  (re-anchors X  -> S2)
After both: S1 -> X -> S2 -> D1 -> S1. A alone: S1 -> X -> T2 (no loop). B alone: S2 -> D1 -> T1 (no loop).
CONTROL (sequential, same fixture): the second supersede must be REFUSED with TaskCycleError and no loop exists.
SUBJECT (concurrent, two ledgers = two connections, asyncio.gather): count attempts where BOTH commit and a
whole-table cycle exists. Each attempt mints and removes its own test_<pid>_<uuid> database on :18000."""
import asyncio, os, sys, uuid
import loremaster
from loremaster.tasks import TaskLedger, TaskCycleError, find_blocked_by_cycle
sys.path.insert(0, os.path.join(os.path.dirname(loremaster.__file__), "..", "..", "scripts"))
from probe_query_complexity_07 import NAMESPACE, PASSWORD, URL, USER
assert ":18500" not in URL, URL
print("loremaster.__file__ =", loremaster.__file__, "| store =", URL)
ATTEMPTS = 20

def mk(db):
    return TaskLedger(url=URL, namespace=NAMESPACE, database=db, user=USER, password=PASSWORD)

async def cyc(ledger):
    rows = ledger._as_rows(await ledger._query("SELECT record::id(id) AS id, blocked_by FROM task"))
    return find_blocked_by_cycle({str(r["id"]): [str(b) for b in (r.get("blocked_by") or ())] for r in rows})

async def fixture(ledger):
    t1 = await ledger.create_task("T1", "p", created_by="ca58d-blind")
    t2 = await ledger.create_task("T2", "p", created_by="ca58d-blind")
    d1 = await ledger.create_task("D1", "p", blocked_by=[t1], created_by="ca58d-blind")
    x = await ledger.create_task("X", "p", blocked_by=[t2], created_by="ca58d-blind")
    return t1, t2, d1, x

async def outcome(coro):
    try:
        await coro
        return "ok"
    except TaskCycleError:
        return "cycle-refused"
    except Exception as error:  # noqa: BLE001 - report every other fate by class
        return type(error).__name__

async def attempt(concurrent, barrier=False, one_ledger=False):
    db = f"test_{os.getpid()}_{uuid.uuid4().hex}"
    a = mk(db)
    b = a if one_ledger else mk(db)
    try:
        await a.ensure_ready()
        t1, t2, d1, x = await fixture(a)
        await b._query("RETURN 1")  # warm b's connection so neither racer pays a connect inside the race
        if barrier:
            # FORCE the interleaving "both guard reads, then both writes": each ledger waits after its own
            # cycle guard (_reblocked runs after _refuse_a_cycle and before _apply) until both have passed it.
            gate = asyncio.Barrier(2)
            for ledger in (a, b):
                original = ledger._reblocked
                async def held(*args, _original=original, **kwargs):
                    result = await _original(*args, **kwargs)
                    await asyncio.wait_for(gate.wait(), 10)
                    return result
                ledger._reblocked = held
        sa = a.supersede_task(t1, subject="S1", description="p", created_by="ca58d-blind", blocked_by=[x])
        sb = b.supersede_task(t2, subject="S2", description="p", created_by="ca58d-blind", blocked_by=[d1])
        if concurrent:
            fates = await asyncio.gather(outcome(sa), outcome(sb))
        else:
            fates = [await outcome(sa), await outcome(sb)]
        loop = await cyc(a)
        return tuple(fates), bool(loop)
    finally:
        try:
            await a._query(f"REMOVE DATABASE {db}")
        finally:
            await a.close()
            if b is not a:
                await b.close()

async def main():
    control = await attempt(False)
    print("CONTROL sequential:", control)
    for label, barrier, one in (("CONCURRENT ONE ledger/connection (the served shape)", False, True),
                                ("CONCURRENT two ledgers warm", False, False),
                                ("CONCURRENT barrier-forced interleave", True, False)):
        tally = {}
        for _ in range(ATTEMPTS):
            key = await attempt(True, barrier, one)
            tally[key] = tally.get(key, 0) + 1
        for key, count in sorted(tally.items(), key=str):
            print(f"{label} fates={key[0]} whole_table_cycle={key[1]} : {count}/{ATTEMPTS}")
    return 0 if control == (("ok", "cycle-refused"), False) else 2

sys.exit(asyncio.run(main()))
```
