# REPORT-contract-cycle-04b3-1 — the CYCLE contract (ESC-1 · #273/#272 · CA-11)

brief-base v10 read
brief project v7 read

## CAPABILITY CHECK (brief-base §4 — first thing)
- **lore tools:** reachable and used (registered `contract-cycle-04b3-1`/`pkt04b3`; `lore_index`
  live — 3259 files, watching `/workspace` @ `4b952f3`; `lore_get_symbol`/`lore_search`/`lore_findings`
  all returned). Index fresh (last sweep this session pre-edit; my edits are TEST files + a script).
- **spike-surreal :18000:** reachable (`/dev/tcp` open; the ESC-1 harness ran 58 PASS/0 FAIL against it).
- **write tests:** yes (new module + staged harness written and run).
- **No unmeetable demand.** One SCOPE note, not a capability gap: the mission's pins for ESC-1/#273-helper/CA-11
  all center on the write-time guard `_refuse_a_cycle`, whose §C mechanism is contradicted by measured pins —
  that is a design fork I ESCALATE (below), not a tooling limit.

## SUMMARY BLOCK
- **state: DONE — forks RULED, contract FINALIZED for the adversary.** All three forks were ruled by Fable
  (§CYCLE-FORKS in `REPORT-design-sidecar-04b3-1.md`, 2026-08-03; directive #2081, acked): the contract
  author was confirmed right on all three (A/B = Reading 1; C = defer), and §C-A/§C-C were retracted. The
  contested skip-stubs are converted to the ruled pins; the deferred CA-11 stubs are dropped.
- deviations: (1) I EDIT `test_blocks_edge.py` (legal under this packet + the FORK-A ruling; disclosed as a
  one-concern change): DELETE `test_KNOWN_BOUND_..._rows_READ_DOES_grow_with_the_BLOCKED_population`, ADD its
  bounded-closure replacement `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (reusing
  `_blocked_noise_traffic`, #102), ADD `TestTheEnumerationEQUALSNetworkxAfterTheSwap` (#273 enumeration
  discriminator, reusing the existing networkx oracle), and a one-line RE-OPEN note on the sibling class's
  stated count bound (P8d prose consistency). (2) NO "columns→RED" pin and NO CA-11 atomicity pin exist,
  deliberately — the ruling confirms both would be C-DEFs (§FORK-A / §FORK-C). (3) The staged harness got 6
  trivial lint auto-fixes (I001/F541) + one `# noqa: PLR0915` — non-semantic; re-run confirmed 58 PASS/0 FAIL.
- **Packages considered:** `networkx` 3.6.1 (installed, operator-authorised @`54d0585`; READ finding #273's
  four-topology oracle table + #272's resolved edit) → **replace** the hand-rolled all-cycle walk in
  `_record_legacy_cycles` (moves it to a PRODUCTION import ⇒ dep dev→runtime + mypy-override re-scope, §273-FLAGS).
  `graphlib.TopologicalSorter` (stdlib) → **keep** for write-time cycle DETECTION (`find_blocked_by_cycle`,
  one witness; unchanged by this contract). `_txn.retry_on_conflict` (in-house shared driver) → **keep** — CA-11's
  atomic check-write must ride it, proved by mutation (§FORK-A pin, skip-stub pending ruling).
- **Graded:** 4b952f3 · HEAD-at-report: 4b952f3 · SAME. (The §C ruling I execute was graded @`338abe0`; every
  code fact below I RE-derived live @`4b952f3` — the three `SET` sites, the two `_drop_one_cycle_edge` callers,
  the ESC-1 harness YES.)
- decisions-needed: **none** — all three forks ruled (§CYCLE-FORKS). One residual FLAG stands for the
  builder, not a decision: the FORK-B STOP-and-flag rider — if the guard's from-minted reachability
  reformulation proves unsound, fall back to Reading 2 (keep `_drop_one_cycle_edge`; #273 deletes only its own
  loop), NEVER a silent copy #2.
- receipt pointers: ruling `REPORT-design-sidecar-04b3-1.md` §CYCLE-FORKS · fork escalation record (both
  readings) §FORKS · finalized RED run §CONTRACT · ESC-1 + #273 reshape in `test_blocks_edge.py` §ESC-1-FLAGS ·
  #273 prod edits §273-FLAGS · harness `scripts/esc1_write_path_cycle_closure.py` (58 PASS/0 FAIL @`4b952f3`) ·
  store ref §3/§4/§5/§6.4 · findings #273 #272.

---

# §FORKS — three interlocking design questions, all on the write-time guard `_refuse_a_cycle`

> **✅ ALL THREE RULED 2026-08-03 — the contract author was confirmed right on all three** (Fable ground-truthed
> @`4b952f3` and RETRACTED its own §C-A and §C-C). **A = Reading 1** (bound the read, keep the column); **B =
> Reading 1** (from-minted reachability frees `_drop_one_cycle_edge` → deleted); **C = defer CA-11** to the
> "`blocked_by`-mutating verb" trigger. Full ruling: `REPORT-design-sidecar-04b3-1.md` §CYCLE-FORKS. The
> escalation record below is preserved as the reasoning that produced the ruling; the finalized pins are in
> §CONTRACT / §ESC-1-FLAGS.

The §C rulings for ESC-1, #273-helper-deletion, and CA-11 all rework, or depend on the rework of, ONE method:
`TaskLedger._refuse_a_cycle` (`tasks.py`, the write-time cycle guard). Each fork is a place where the §C
sentence, taken literally, forces a pin that reddens the correct build or contradicts an existing MEASURED
pin. Per brief-base §2 and repo law (FIXTURES MUST DISCRIMINATE; spec ambiguity is a STOP-and-flag), I write
both readings, recommend one, and escalate — I do NOT improvise the contested reading into an assertion.

## FORK A — ESC-1's mechanism: "ride edges, columns→RED" is contradicted by measured pins
**§C-ESC-1 says:** the write-path cycle read "rides persisted `blocks` EDGES, not the `blocked_by` column
ledger; WRONG build = reads `blocked_by` columns → RED. Self-reachability is the signal."

**What the codebase already PINS (measured, @`4b952f3`):** `test_blocks_edge.py::TestCreateRefusesToFormACycle`
says the OPPOSITE, with a receipt in its own docstring: *"a build whose cycle check walks the EDGE fails
exactly this one pin"* — `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`. The
structural reason (module header `tasks.py:74-77`; `_refuse_a_cycle` docstring): **a cycle's CLOSING dependency
names a task that does not exist yet, and `ENFORCED` forbids a `RELATE` to a non-existent task — so that link
can only ever be a COLUMN, has no `blocks` edge, and any engine traversal returns "acyclic."** The
"self-reachability / +collect" signal is TRUE of the transitive READ (`transitive_blockers`, already built,
pinned by `TestACycleIsDetectedOverPERSISTEDIds`) and FALSE of the write GUARD — **exactly the conflation
adversary MP-4a already corrected on 2026-07-28** (that class's docstring: *"THIS CLASS IS ABOUT THE READ, NOT
THE WRITE-TIME GUARD, AND ITS DOCSTRING USED TO CONFLATE THEM"*).

The ESC-1 probe measured a TRUE but DIFFERENT property: *every persisted ANCESTOR of a new dependency is
edge-reachable*. That does NOT imply the guard can abandon the column, because cycles for a new task do not
close on an ancestor edge — they close on a column-only forward link (or a batch-local/self link with no row).

- **Reading 1 (my RECOMMENDATION):** ESC-1's honest deliverable is **BOUNDING** the guard's read to the new
  dependency's ancestor closure — seed from the new task's blockers, walk the closure via `blocks` edges for
  reachability, read those BOUNDED nodes' `blocked_by` columns for closing-link detection, run the shared
  `find_blocked_by_cycle`. This **deletes the whole-population column scan** (the KNOWN_BOUND, §ESC-1-FLAGS)
  and keeps every `TestCreateRefusesToFormACycle` refusal green — because it still reads columns, bounded. No
  "columns→RED" pin is written.
- **Reading 2 (ruling literal):** the guard reads ONLY edges; a build reading any column goes RED. **REJECTED**
  as a C-DEF — this build serves the very cycle the measured persisted-cycle pin catches, i.e. it fails an
  existing pin. Adopting it re-commits the MP-4a conflation.
- **DIRECTIVE:** confirm Reading 1 (bound the read, keep the column for closing links). Then ESC-1's pin is
  the KNOWN_BOUND replacement (rows-read bounded by closure, not blocked population) — writable and
  fork-independent — and NOT a "columns→RED" pin.

## FORK B — #273's "DELETE the hand-rolled helpers" is entangled with Fork A
**§C-#273 says:** swap `_record_legacy_cycles` to `networkx.simple_cycles` and "DELETE the hand-rolled helpers
(`_drop_one_cycle_edge` + drop-and-retry loop)."

**Fact @`4b952f3`:** `_drop_one_cycle_edge` (`tasks.py:707`) has **TWO callers** — `_record_legacy_cycles`
(the backfill enumeration #273 swaps, `:1037`) **AND `_refuse_a_cycle`** (the write guard, Fork-A's locus,
`:2292`, where it steps over legacy cycles a caller did not write). It cannot be deleted by the #273 swap
alone; the swap only removes `_record_legacy_cycles`'s use.

- **Reading 1 (RECOMMENDATION):** do #273's swap AND Fork-A's guard rework together (they are ONE CYCLE
  session by the §A partition; one adversary pass). ESC-1's bounded read replaces `_refuse_a_cycle`'s
  step-over-legacy loop, freeing `_drop_one_cycle_edge` for deletion. Then the helper-absence pin is valid.
- **Reading 2:** #273 swaps only `_record_legacy_cycles`; `_drop_one_cycle_edge` STAYS (one caller left). The
  §C "delete the helpers" is then partially wrong — only the drop-and-retry LOOP inside `_record_legacy_cycles`
  goes.
- **DIRECTIVE:** confirm the helpers' fate is decided WITH Fork-A. `find_blocked_by_cycle` (the shared DETECTOR,
  used by the guard AND `server.py`'s batch-key check, pinned by `TestTheCyclePolicyHasONEImplementation`) is
  **unchanged** either way — #273 touches ENUMERATION, not DETECTION.

## FORK C — CA-11's concurrent joint cycle is UNREACHABLE through the verbs
**§C-CA-11 says:** a concurrent racer "can write a jointly-cyclic edge no single check saw ⇒ a served
blocker/critical-path render can then show a cycle: a served correctness hole." Ruled: "YES it can."

**What I verified @`4b952f3`:** a persisted-id cycle is UNREACHABLE through the ledger verbs.
- No `TaskLedger` verb mutates `blocked_by` after birth: the three `SET` sites write owner/status/claimed_at
  (claim CAS, `:1533`), status (transition, `:1751`), superseded_by/provenance (supersede, `:1975`) — **never
  `blocked_by`**. Confirmed by reading each.
- Every created task is a fresh SINK: `create_task` mints a `uuid4` no one has seen; `create_many` blockers
  resolve to persisted rows or same-batch siblings, and the existence pre-check **fails CLOSED** on a forward
  reference to a not-yet-persisted id. So a task's ancestor set is FIXED at birth, and no create — concurrent
  or not — can place a task on a cycle.
- The ledger's own pin agrees: `test_a_PERSISTED_ID_cycle_is_UNREACHABLE_at_the_TOOL_SEAM_by_construction`
  states *"a cycle closes only when an EXISTING row's `blocked_by` already names the id about to be created."*
  Two concurrent creates cannot manufacture that entry.
- Empirical corroboration: my 8-way liveness pin (8 concurrent creates on a shared blocker, overlapping
  lifetimes) is GREEN today — the current (check-outside-txn) build already has no storm and no loss on this
  path. A "served cycle under load" pin therefore cannot DISCRIMINATE: the wrong build serves no cycle either.

- **Reading 1 (RECOMMENDATION):** CA-11's atomicity is **defence-in-depth** against a FUTURE
  `blocked_by`-mutating verb (an `add_blocker`/re-parent), which WOULD make joint cycles reachable. Build the
  atomic guard now (cohesive with Fork-A's bounded read; one adversary pass), pinned by a SYNTHETIC concurrent
  raw forward-pointing write injected between check and write (the injection is verb-unreachable, so it stands
  in for the future verb), and DISCLOSE that it defends a verb-unreachable-today scenario. The PIN-THE-MISS
  (`test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth`, green today) reddens the day that verb lands.
- **Reading 2:** CA-11 is latency-only — the `create_task` docstring already frames "fold the acyclicity walk
  into the write txn" as a LATENCY re-open trigger, not a correctness fix — so no atomicity pin is owed until a
  `blocked_by`-mutating verb exists; CA-11 stays DEFERRED with that trigger.
- **DIRECTIVE:** rule between "build defensive atomicity now (synthetic-adversary pin)" vs "defer CA-11 to the
  `blocked_by`-mutating-verb trigger." Either way the "served-cycle-under-8-way-load" discriminator as written
  in §C cannot be built (nothing to serve).

---

# §CONTRACT — the FINALIZED pins (contract-first; run @`4b952f3`)

Two writable files. Run receipt (scoped: the new module + the three edited `test_blocks_edge.py` classes):

```
$ .venv/bin/python -m pytest test_cycle_write_path_04b3.py \
    "test_blocks_edge.py::TestCreateRefusesToFormACycle" \
    "test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap" \
    "test_blocks_edge.py::TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST" -n auto -q
4 failed, 15 passed in 4.92s
```
**The 4 RED pins (each drives one specific build change; RED for the right reason @`4b952f3`):**
1. `test_cycle_..::TestTheAllCycleEnumeratorIsNetworkxInPRODUCTION::test_networkx_is_imported_by_the_PRODUCTION_tasks_module`
   — `import networkx` absent from production `tasks.py` (only the test-oracle imports it). Drives #273's swap.
2. `test_cycle_..::…::test_the_hand_rolled_cycle_helper_drop_one_cycle_edge_is_GONE` (FORK B) — `_drop_one_cycle_edge`
   still defined in `loremaster.tasks` (two callers). Drives the guard's from-minted reformulation + the swap,
   after which the helper is deleted. Carries the STOP-and-flag rider (Reading 2 fallback if from-minted unsound).
3. `test_blocks_edge.py::TestCreateRefusesToFormACycle::test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE`
   (FORK A) — `large.rows == small.rows` fails today (the guard scans the whole dependency-bearing population).
   Drives the bounded-closure read. **No "columns→RED" pin** — the guard keeps the column for closing links.
4. `test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap::…[complete-triangle]` (FORK B) — recorded
   cycles **4** ≠ networkx **5** on a fully-connected component (exactly #273's measured 4-vs-5). Drives the
   enumeration to networkx. The `[disjoint-1-2-3]`/`[overlapping]` legs pass — positive controls (the
   enumerators already agree there).
**The green pins (guards + controls, must stay green through the build):** `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth`
(FORK-C tripwire — reddens the day a `blocked_by`-mutating verb lands, the CA-11 deferral trigger) ·
`test_LIVENESS_eight_way_concurrent_creates_on_a_SHARED_blocker_all_land` (no-storm/no-loss under ≥8-way;
its green IS the FORK-C evidence) · the two kept-green ESC-1 siblings (`..._does_NOT_grow_with_the_DEPENDENCY_FREE_population`,
`test_the_cycle_WALK_is_ONE_round_trip`) · the enumeration positive controls · the member-coverage class
(`TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST`, unchanged behaviour; docstring RE-OPEN note only).

`ruff check` on both writable files + the harness: **All checks passed.** (Full mypy not run — outside a
contract author's required scope; the builder/contract-adversary gate it. Flag if you want it re-run.)

# §ESC-1-FLAGS — the KNOWN_BOUND reshape (DONE, per the FORK-A ruling)
Executed in `test_blocks_edge.py::TestCreateRefusesToFormACycle` (a one-concern edit, disclosed):
1. **DELETED** `test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population` — its own
   docstring authorised the deletion (*"if you CLOSED it deliberately, DELETE this pin and say so"*) and named
   the fork (*"an ancestor-closure seed, say — is a DESIGN question"*, now Reading 1). Said here, as required.
2. **ADDED** `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` in its place, reusing
   `_blocked_noise_traffic` (#102): asserts `large.rows == small.rows` (RED on the whole-population build,
   GREEN on the bounded-closure build). No "columns→RED" pin — the guard KEEPS the column for closing links.
3. The two siblings (`..._DEPENDENCY_FREE_population`, `test_the_cycle_WALK_is_ONE_round_trip`) stay GREEN as
   the ruling requires — the bounded read touches no dependency-free row and is still one round trip (R7).

# §273-FLAGS — production edits the builder owes (outside my writable set)
1. In `loremaster/loremaster/tasks.py`: swap `_record_legacy_cycles`'s drop-an-edge loop for
   `networkx.simple_cycles` (ADOPT `REPORT-design-sidecar-04b2-1.md` §B4 verbatim; DETECTION stays `graphlib`).
2. `pyproject.toml`: move `networkx` from the dev dependency group to **runtime** (`[project] dependencies`) —
   it becomes a production import. **This makes 04b-3 an IMAGE change** (design §A-deploy): 05a's deploy smoke
   owes an "import networkx in the deployed image" line, and the Containerfile/`conformance_provenance` path
   must carry it (the #131/#139 in-image class).
3. `pyproject.toml` `[[tool.mypy.overrides]]`: the `module = ["networkx", "networkx.*"]` block already exists
   (resolved @`af3551c` for the TEST tree, #272). Its COMMENT currently scopes it "test-side oracle only,
   production imports it nowhere" — that comment is now FALSE and must be updated to "production import
   (#273)"; the module list itself is unchanged. (P8d rename-sweep: a prose surface no gate checks.)

# §PINS-OWED (from §C + §CYCLE-FORKS, mapped to their FINALIZED state — nothing dropped)
| §C rider | state (RULED) |
|---|---|
| ESC-1 bound the read to the ancestor closure; NO columns→RED | **RED pin written** — `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE` (§ESC-1-FLAGS). "columns→RED" ruled a C-DEF, not written. |
| ESC-1 residue = batch-local siblings + legacy phantoms | covered by the harness (58 PASS) + existing `TestCreateRefusesToFormACycle` refusal pins (batch-local + self) — stay green |
| ESC-1 deletes the known-bound pin | **DONE** — KNOWN_BOUND deleted, bounded-closure leg added (§ESC-1-FLAGS) |
| ESC-1 keep dependency-free + one-round-trip pins green | **kept green** (verified in the finalized run) |
| #273 networkx.simple_cycles in `_record_legacy_cycles` | **RED pin written** (production import) + §273-FLAGS |
| #273 helper absence (`_drop_one_cycle_edge`) | **RED pin written** — `test_the_hand_rolled_cycle_helper_drop_one_cycle_edge_is_GONE`; STOP-and-flag rider carried |
| #273 cycle-enumeration equivalence on adversarial shapes | **RED pin written** — `TestTheEnumerationEQUALSNetworkxAfterTheSwap` (count == networkx ∀ topology; complete-triangle 4≠5 RED). Member coverage still pinned by the sibling class (green both sides). |
| #272 mypy override + dep dev→runtime | **§273-FLAGS** (builder; outside my writable set) |
| CA-11 check-write atomicity / retry-of-the-unit / served-cycle-under-load | **DEFERRED (FORK C)** — no atomicity pin; ruled unbuildable (verb-unreachable). Tripwire `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth` (green) reddens the day a `blocked_by`-mutating verb lands. |
| CA-11 ≥8-way overlapping liveness | **green guard written** — no-storm/no-loss; run-discipline (20 greens) is the builder's |
| CA-12 supporting index | **DEFERRED** (§C-CA-12: measure-then-tune) |

---
*Written 2026-08-03 by `contract-cycle-04b3-1` (Opus 4.8) against `feat/surreal-unification` @ `4b952f3`;
FINALIZED same day after §CYCLE-FORKS ruled all three escalated forks (contract author confirmed right on all
three; A/B=Reading 1, C=defer). Every code fact re-derived live (the three `SET` sites; `_drop_one_cycle_edge`'s
two callers; `find_blocked_by_cycle`'s three; the ESC-1 harness 58 PASS/0 FAIL; the finalized 4-RED/15-green run).
No structural claim fell back to grep except deletion-exhaustiveness of `_drop_one_cycle_edge`'s callers (grep's
honest case, corroborated by lore). The escalation of the three forks — and the fact that every contested pin
would have reddened the correct build — was the deliverable's core; the ruling vindicated it.*
