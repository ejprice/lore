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
- **state: REVISED per §CYCLE-TRILEMMA (variant D) — re-finalized for a FRESH adversary.** History: the three
  §C forks were ruled (§CYCLE-FORKS, 2026-08-03; A/B=Reading 1, C=defer); an adversary then graded that
  revision INSUFFICIENT (`REPORT-adversary-cycle-04b3-1.md`, finding #326) with a PROVEN trilemma, and Fable
  elected **VARIANT D** + retracted its own FORK-B from-minted reformulation (§CYCLE-TRILEMMA, 2026-08-04;
  directive #2086, acked). This revision applies D. Details in §TRILEMMA-REVISION.
- deviations: (1) I EDIT `test_blocks_edge.py` (legal under this packet + the rulings; disclosed): the FORK-A
  KNOWN_BOUND reshape (DELETE `test_KNOWN_BOUND_...`, ADD `test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE`
  reusing `_blocked_noise_traffic` #102), the #273 enumeration class `TestTheEnumerationEQUALSNetworkxAfterTheSwap`
  + its **MP-4 routing** leg (reusing the networkx oracle), the **MP-1 soundness pin**
  `test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED` in `TestCreateRefusesToFormACycle`,
  a sibling-docstring RE-OPEN note (P8d), and 3 P8d fixes for the deleted-pin name. (2) I COMMIT the durable
  MP-1 fixture `scripts/cycle_coexisting_legacy_soundness_probe.py` (reconstructed from the adversary's probe —
  brief-base §1: instrument-is-a-deliverable, never `/tmp`). (3) The helper-absence pin was REMOVED (MP-3
  dissolved — variant D keeps `_drop_one_cycle_edge`). (4) NO "columns→RED" pin, NO from-minted reformulation,
  NO CA-11 atomicity pin — all ruled C-DEFs/unsound. (5) The ESC-1 harness got non-semantic lint fixes earlier;
  re-run 58 PASS/0 FAIL. The MP-1 probe refuses on HEAD (exit 0, sound).
- **Packages considered:** `networkx` 3.6.1 (installed, operator-authorised @`54d0585`; READ finding #273's
  four-topology oracle table + #272's resolved edit) → **replace** the hand-rolled all-cycle walk in
  `_record_legacy_cycles` (moves it to a PRODUCTION import ⇒ dep dev→runtime + mypy-override re-scope, §273-FLAGS).
  `graphlib.TopologicalSorter` (stdlib) → **keep** — it is the shared write-time DETECTOR
  `find_blocked_by_cycle`, UNCHANGED (variant D: the guard keeps its drop-loop through it; R6 forbids a second
  detector). `_txn.retry_on_conflict` (in-house shared driver) → **keep** — unchanged; CA-11's atomicity is
  DEFERRED (no pin). `_drop_one_cycle_edge` → **kept** (variant D — the guard's single legit caller after #273
  deletes `_record_legacy_cycles`'s use); NOT a #102 violation (single-use helper, not a cloned policy).
- **Graded:** 9983191 · HEAD-at-report: 9983191 · SAME. (My prior RED contract landed @`1164133`; the trilemma
  ruling landed @`9983191`. Every code fact re-derived live: the MP-1 world REFUSES on HEAD — exit 0, sound;
  the 4-RED/16-green revised run.)
- decisions-needed: **none** — forks + trilemma ruled. Residual FLAGS for the BUILDER (not decisions): (a) the
  §273-FLAGS production edits (networkx dev→runtime = an IMAGE change; mypy comment re-scope); (b) the
  networkx-in-production pin drives the `import networkx` MODULE form (MP-4 patches `networkx.simple_cycles`) —
  a `from networkx import simple_cycles` build would satisfy the import pin but escape MP-4's patch; flagged.
- receipt pointers: rulings `REPORT-design-sidecar-04b3-1.md` §CYCLE-FORKS + §CYCLE-TRILEMMA · adversary
  `REPORT-adversary-cycle-04b3-1.md` §2/§6 + finding #326 · trilemma revision §TRILEMMA-REVISION · revised RED
  run §CONTRACT · MP-1 durable fixture `scripts/cycle_coexisting_legacy_soundness_probe.py` (exit 0 @HEAD) ·
  ESC-1 harness `scripts/esc1_write_path_cycle_closure.py` · §273-FLAGS · store ref §3/§4/§5/§6.4 · #273 #272.

---

# §TRILEMMA-REVISION — the adversary's INSUFFICIENT, and variant D (2026-08-04)

A fresh adversary (`REPORT-adversary-cycle-04b3-1.md`, finding #326) graded the forks-ruled contract
INSUFFICIENT with a **proven trilemma** on the FORK-B guard reformulation, and Fable ruled it (§CYCLE-TRILEMMA),
electing **variant D** and retracting its own from-minted reformulation. What the adversary found and what I
changed:
- **The unsoundness (MP-1, the blocker):** the forks-ruled FORK-B reformulated the guard to a from-minted
  reachability check — but a NAIVE bounded read done as a SINGLE `find_blocked_by_cycle` call (variant S) is
  **UNSOUND**: when a LEGACY 2-cycle coexists with a minted cycle in the bounded closure, `find_blocked_by_cycle`
  returns the legacy cycle first, `minted∩=∅`, and the guard ACCEPTS a create forming a real persisted-id cycle
  `N→seed→X→N` — an unclaimable-forever task. The adversary PROVED it through the real write path (§2, exit 2).
  My existing `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` tested a cycle in
  ISOLATION — the QUANTIFIER LAW: a ∀-claim evaluated on the one input where every build agrees.
- **The R6 conflict (MP-2):** from-minted introduces a SECOND ledger cycle-detector, reddening R6's MUTATION
  pin (one ledger-owned detector = `find_blocked_by_cycle`). Fable ruled R6 STANDS → **variant D**: the guard
  KEEPS its drop-loop through the shared `find_blocked_by_cycle` (already HEAD's behaviour; sound — it steps
  over the legacy cycle and finds the minted one). ESC-1's ONLY guard change is FORK-A's bounded read.
- **The revision I applied:**
  - **REMOVED** the helper-absence pin (MP-3 dissolved — D keeps `_drop_one_cycle_edge`; the pin was false +
    name-keyed / rename-defeatable).
  - **ADDED MP-1** — `test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED` in
    `TestCreateRefusesToFormACycle`: GREEN at HEAD/variant D, RED on variant S. The load-bearing id-ordering
    (`aaa*` legacy < `zzz*` minted) makes `find_blocked_by_cycle` return the legacy cycle first. Durable fixture
    committed: `scripts/cycle_coexisting_legacy_soundness_probe.py` (reconstructed from the adversary's probe;
    refuses on HEAD, exit 0 — sound).
  - **ADDED MP-4** — `test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record`: neutralise
    `networkx.simple_cycles` → a routing build records ZERO cycles; the hand-rolled HEAD loop ignores the patch
    and records the full set → RED. Closes routing-is-not-sharing (import-string + count-equality don't prove
    the library is CALLED).
  - **NARROWED #273** — swap ONLY `_record_legacy_cycles`'s enumeration to `networkx.simple_cycles` (deletes ITS
    drop-loop); `_drop_one_cycle_edge` STAYS (the guard's single legit caller). Not a #102 violation.
  - **KEPT** — the FORK-A bounded-read pin, networkx-in-production, count-equality, FORK-C tripwire + 8-way
    liveness (the adversary VERIFIED the FORK-C deferral is honest, §4).

The §FORKS escalation record below is preserved as history; §CYCLE-TRILEMMA supersedes its FORK-B.

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

# §CONTRACT — the FINALIZED pins (variant D; contract-first; run @`9983191`)

Three writable files (the module + `test_blocks_edge.py` + the two `scripts/` probes). Run receipt (scoped):

```
$ .venv/bin/python -m pytest test_cycle_write_path_04b3.py \
    "test_blocks_edge.py::TestCreateRefusesToFormACycle" \
    "test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap" \
    "test_blocks_edge.py::TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST" -n auto -q
4 failed, 16 passed in 4.91s   # (variant D; @9983191)
```
**The 4 RED pins (each drives one specific build change; RED for the right reason @HEAD):**
1. `test_cycle_..::TestTheAllCycleEnumeratorIsNetworkxInPRODUCTION::test_networkx_is_imported_by_the_PRODUCTION_tasks_module`
   — `import networkx` absent from production `tasks.py`. Drives #273's swap (the MODULE-import form MP-4 patches).
2. `test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap::test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record`
   (**MP-4, routing**) — neutralise `networkx.simple_cycles` → a routing build records 0 cycles; the hand-rolled
   HEAD loop records 4 (ignores the patch). Proves the swap ROUTES through the library, not just imports it.
3. `test_blocks_edge.py::TestCreateRefusesToFormACycle::test_the_write_paths_rows_READ_is_BOUNDED_by_the_ancestor_CLOSURE`
   (FORK A) — `large.rows == small.rows` fails (63≠8: the guard scans the whole dependency-bearing population).
   Drives the bounded-closure read. **No "columns→RED" pin** — the guard keeps the column for closing links.
4. `test_blocks_edge.py::TestTheEnumerationEQUALSNetworkxAfterTheSwap::…[complete-triangle]` (#273) — recorded
   cycles **4** ≠ networkx **5** on a fully-connected component (exactly #273's measured 4-vs-5). Drives the
   enumeration to networkx; the `[disjoint]`/`[overlapping]` legs pass as positive controls.
**The green pins (soundness + guards + controls, must stay green through the build):**
- **MP-1 (the soundness blocker)** `…TestCreateRefusesToFormACycle::test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED`
  — GREEN at HEAD/variant D (the guard's drop-loop steps over the legacy cycle and refuses the minted one);
  **RED on variant S** (the single-witness build that passed the pre-revision contract). Durable fixture:
  `scripts/cycle_coexisting_legacy_soundness_probe.py` (refuses on HEAD, exit 0).
- `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth` (FORK-C tripwire) · `test_LIVENESS_eight_way…`
  (no-storm/no-loss ≥8-way) · the two kept-green ESC-1 siblings · the enumeration positive controls · the
  member-coverage class (unchanged behaviour).

`ruff check` on all three writable files + both `scripts/` probes: **All checks passed.** The MP-1 probe was
RUN against HEAD (exit 0, REFUSED — sound). (Full mypy not run — outside a contract author's required scope;
the builder/adversary gate it. Flag if you want it re-run.)

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
1. In `loremaster/loremaster/tasks.py`: swap ONLY `_record_legacy_cycles`'s enumeration to
   `networkx.simple_cycles` (deletes ITS drop-loop). **`_drop_one_cycle_edge` STAYS** (variant D — the write
   guard `_refuse_a_cycle`'s single legit caller; the guard is NOT reformulated). DETECTION stays `graphlib`
   via the shared `find_blocked_by_cycle`. ESC-1's ONLY guard change is FORK-A's bounded read (§ESC-1-FLAGS).
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
| #273 networkx.simple_cycles in `_record_legacy_cycles` (NARROWED, variant D) | **RED pin** (`test_networkx_is_imported_by_the_PRODUCTION_tasks_module`) + §273-FLAGS |
| #273 ROUTES through the library, not just imports it (MP-4) | **RED pin** — `test_MUTATION_neutralising_networkx_simple_cycles_SILENCES_the_record` (routing-is-not-sharing) |
| #273 helper absence (`_drop_one_cycle_edge`) | **REMOVED (MP-3 dissolved)** — variant D KEEPS the helper (guard's single caller); it was false + rename-defeatable |
| #273 cycle-enumeration equivalence on adversarial shapes | **RED pin** — `TestTheEnumerationEQUALSNetworkxAfterTheSwap` (count == networkx ∀ topology; complete-triangle 4≠5). Member coverage still pinned by the sibling class (green both sides). |
| **MP-1 — coexisting-legacy-cycle soundness (the blocker)** | **GREEN pin** — `test_a_MINTED_cycle_COEXISTING_with_a_LEGACY_cycle_in_the_closure_is_REFUSED` (green@HEAD/D, RED on variant S) + durable fixture `scripts/cycle_coexisting_legacy_soundness_probe.py` |
| #272 mypy override + dep dev→runtime | **§273-FLAGS** (builder; outside my writable set) |
| CA-11 atomicity / served-cycle-under-load | **DEFERRED (FORK C, adversary-VERIFIED honest)** — no pin; tripwire `test_PIN_THE_MISS_a_tasks_blocked_by_is_FIXED_at_birth` (green) reddens the day a `blocked_by`-mutating verb lands. |
| CA-11 ≥8-way overlapping liveness | **green guard** — no-storm/no-loss; run-discipline (20 greens) is the builder's |
| CA-12 supporting index | **DEFERRED** (§C-CA-12: measure-then-tune) |

---
*Written 2026-08-03 by `contract-cycle-04b3-1` (Opus 4.8), REVISED 2026-08-04 to **variant D** after an
adversary (finding #326) proved the forks-ruled FORK-B unsound and Fable ruled §CYCLE-TRILEMMA. Graded against
`9983191`. Every code fact re-derived live: the MP-1 world REFUSES on HEAD (exit 0 — sound, the fixture is in
`scripts/`); the revised 4-RED/16-green run; ruff clean on all writable files. This is a fix wave — a FRESH
adversary re-grades it. The two self-retractions in this fork chain (from-minted, and before it §C-A/§C-C) were
each caught by the adversarial layer BEFORE a builder built the wrong thing — the process working as designed.*
