# REPORT-contractfix-04b1-r6 — closing the delta adversary's findings

brief-base v8 read

brief project v7 read

comms: registered `contractfix-04b1-r6` (session `pkt04b-20260728`, role `contract-author`,
model `claude-opus-5`, task `e48347a9020945efb5725e16ae1e73c3`).

**CAPABILITY CHECK (brief-base §4) — NO GAP. Everything the brief demands, I can do.**
Demanded vs held: `lore_comms`/`lore_findings`/`lore_search`/`lore_get_symbol`/`lore_read` —
loaded via `ToolSearch` and USED (register above; findings #271–#273 filed). Bash, Read, Write,
Edit — held; the four writable test files were edited and every gate run. `spike-surreal
ws://127.0.0.1:18000` — reachable; `:18500` never touched. `scripts/scratch_copy.sh` and
`scripts/mutation_proof.py` — both ran, receipts below. **One partial, declared rather than
silent:** I have no `Grep`/`Glob` tools, so every textual sweep in this report was `grep(1)`
through Bash. That is a substitute, not a gap — the three cases repo law reserves for grep
(rename exhaustiveness, non-symbol textual seams, cross-cutting maps) are exactly what I used
it for, and I say so here per brief-base §4. **What a lead must change: nothing.**

**trust hard-definition read.** Its two askable questions, quoted verbatim from `CLAUDE.md`
§ *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"***

> **Ask: *"what broken state of this tool would serve exactly these bytes?"***

*Every number in this report was DERIVED by running, on **2026-07-28**, on branch
`feat/surreal-unification` at working-tree HEAD `121f1f2` (the shipped build is `b8607c4`).
Every store call hit spike-surreal `ws://127.0.0.1:18000` (TEST); `:18500` was never touched.
I mutated no git state. No number is inherited — where I re-derived somebody else's and it
differed, I say so.*

**Scratch provenance (finding #140):** `./scripts/scratch_copy.sh
/home/ejprice/scratch-contractfix-04b1-r6`, EXIT=0, then my four edited test files copied in.

```
loremaster.__file__ = /home/ejprice/scratch-contractfix-04b1-r6/loremaster/loremaster/__init__.py
```

I read none of the pre-existing `/home/ejprice/scratch*` reference builds.

⚠ **A NOTE ON GIT, so a later reader is not confused by the history.** I ran no git
state-mutating command. **The LEAD committed this wave's four test files while I was writing
this report**, as `710adea` (*"test(04b-1): close the delta adversary's six pins + correct
Leg 1 (stage 1 of 4)"*), on top of `121f1f2`. Every measurement below was taken on the working
tree whose content is now that commit; the gate re-runs after my last docstring amendment
(§A1's stated bound) are the ones pasted in §SAT, and they were re-run AFTER that amendment.

---

## SUMMARY BLOCK

- **state: done-with-deviations (one, named below).** All six missing pins written, Leg 1
  corrected and widened, four escalations disposed + one new one raised.
- **A1 backfill coverage above the fixture ceiling — DONE, 2 pins.** Scale floor is DERIVED
  (`max(this file's legacy row constants) + 1` = **61**), asserted at 61 AND 122.
- **A2 a failed MINT makes `ensure_ready` LOUD — DONE, 3 pins**, ∀ over
  `BACKFILL_FAILURE_DOORS = ("existence-read", "mint")` + a positive control.
- **A3 EVERY legacy cycle recorded — DONE, 5 pins**, ∀ over three cycle TOPOLOGIES, oracle =
  `networkx.simple_cycles` (test-side only; the PROPERTY is pinned, not the library).
- **A4 write-path rows vs the BLOCKED population — DONE, 1 new pin + 1 rename.** The false
  gate is closed by NARROWING the old pin's name and message to what it measures; the residual
  growth is asserted as a KNOWN BOUND with a re-open trigger. **The design fork is ESCALATED,
  not settled (§ESC-1).**
- **A5 a capped `query` render discloses its bound — DONE as a KNOWN-BOUND FALSE-CLEAR pin,
  2 pins.** The render is 04b-2's file; 04b-1 may not touch it. **§ESC-5 is new and is the
  lead's call.**
- **A6 the double's `limit` slice — DONE, 6 pins** (3 × `[real]`/`[fake]`), on ONE seeder
  shared with the live suite, sharing PROVEN BY MUTATION across both files (5/5 exact).
- **B Leg 1 — rows 1 and 2 CORRECTED (both were measurably false), row 3 kept verbatim as the
  model, THREE missing surfaces added** (cycle refusal · migration operator record ·
  `ensure_ready`'s normal return). A Leg-1 POINTER added to `test_query_tasks_bounded.py`.
- **C escalations: ESC-2 and ESC-3 DISCHARGED with receipts; ESC-4 IMPLEMENTED as recommended;
  ESC-1 and the new ESC-5 go to the lead with a recommendation each.** §ESC.
- **PIN COUNTS, DERIVED from `--collect-only`, never from the source:** the two contract files
  **234 → 247** collected (+13); `test_task_ledger.py` **234 → 240** (+6). Total new pins
  **19**. ⚠ I re-derived 234 myself; it matches the delta adversary and NOT r5's 232.
- **SATISFIABILITY LEG 1 (whole contract vs the CURRENT shipped build): 0 failed** — see §SAT
  for the pasted counts, including the post-`ruff check --fix` leg (a no-op; tree unchanged).
- **SATISFIABILITY LEG 2 (each new pin RED against the build it targets): 6 mutation proofs,
  ALL HELD EXACTLY, both ways.** §MUT.
- **Gates:** `uv run ruff check .` → `All checks passed!` EXIT=0 · `./scripts/typecheck.sh` →
  every member OK, EXIT=0.
- **deviation (one):** I re-pointed the EXISTING
  `TestTheCapAppliesToTheANSWERNotTheCandidateScan._sandwich_ledger` at the new shared seeder
  rather than writing copy #2 of it. In the writable set, but it touches a load-bearing
  pre-existing pin — verified green and mutation-proven. §DEV.
- **findings filed: #271** (the archive-baseline collection trap, transcribed for the
  tool-less adversary), **#272** (`types-networkx`), **#273** (the hand-rolled all-cycle
  enumeration now that networkx is authorised).
- **Packages considered:** `networkx.simple_cycles` for the CYCLE-ENUMERATION oracle — READ
  `nx.simple_cycles`' behaviour by RUNNING it on four graph topologies against the shipped
  `graphlib` loop (table in §A3) → **replace** for the test oracle (it is the independent
  second enumeration a diff needs); for PRODUCTION it is a `bespoke`→`replace` question whose
  premise changed at `54d0585`, filed as **#273**, NOT settled here (production is outside a
  contract author's writable set). `graphlib.TopologicalSorter` for cycle DETECTION — READ its
  `prepare()` docstring (*"If any cycle is detected, CycleError will be raised"* — singular)
  → **keep_with_trigger**; trigger: the day a per-cycle CONSUMER exists. `pytest.MonkeyPatch`
  for every degraded-state construction, `_surreal_harness.measure_store_traffic` for the rows
  instrument, `re` for the render normaliser — **reuse, no new copy** in all three.
- **receipt pointers:** §A1–§A6 (per-item detail) · §B (Leg 1) · §SAT · §MUT · §ESC · §DEV ·
  §RESIDUALS.

---

## §SAT — satisfiability, BOTH sides

**Leg A — the whole contract against the CURRENT shipped build (`b8607c4`'s production code,
which is what is in this tree).**

```
$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py
247 passed in 9.49s                                                    EXIT=0

$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py loremaster/tests/test_task_ledger.py \
      loremaster/tests/test_mcp_server.py loremaster/tests/test_enforced_relations.py \
      loremaster/tests/test_derivation_source_unification.py
1201 passed, 19 skipped in 115.16s (0:01:55)                           PYTEST_EXIT=0

$ uv run ruff check .
All checks passed!                                                     RUFF_EXIT=0

$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK · skills OK
                                                                       MYPY_EXIT=0

$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_retry_seam.py   # §ESC-2
562 passed
```

⚠ **The neighbour set is DELIBERATE, not incidental** — `_task_fakes.py` is imported by
`test_mcp_server.py` and `test_task_ledger.py`, so a change there that only the contract files
were run against would be an unmeasured blast radius. The three deliberately-reddened
`test_enforced_relations.py` pins are GREEN on this build, exactly as the RED-BY-DESIGN section
says they are after the fix.

`ruff check --fix .` → `FIX_EXIT=0`, `All checks passed!`, and `git status --porcelain`
afterwards named **only my four writable files** — so the post-`--fix` leg is that the fixer
changed nothing and the counts above stand unaltered.

**Leg B — each new pin RED against the specific wrong build it targets.** §MUT.

---

## §MUT — the six mutation proofs, run through `scripts/mutation_proof.py`

Every one ran in the scratch copy (`loremaster.__file__` receipt at the top), with the
declared RED set taken from `pytest --collect-only` BEFORE the run, and the tool's both-ways
diff (unexpected reds AND declared-reds-that-stayed-green). Every restore was byte-exact.

| # | wrong build | mutated | declared RED | observed | verdict |
|---|---|---|---|---|---|
| 1 | **WB-E** — `LIMIT 50` on the backfill's pending read | `tasks.py` | 2 | 2, exact | **HELD** |
| 2 | **WB-O** — `try/except` around the backfill's MINT only | `tasks.py` | 1 | 1, exact | **HELD** |
| 3 | **WB-CYCLE1** — record only the FIRST cycle | `tasks.py` | 4 | 4, exact | **HELD** |
| 4 | **WB-RENDER** — CLOSE the capped-listing bound (count + elision line) | `server.py` | 1 | 1, exact | **HELD** |
| 5 | **WB-FAKE** — delete the double's `limit` slice | `_task_fakes.py` | 2 | 2, exact | **HELD** |
| 6 | **WB-BOUNDED** — `LIMIT 0` on the write guard's read (closes the known bound) | `tasks.py` | 2 | 2, exact | **HELD** (scoped, see below) |

Plus a seventh, which is a SHARING proof rather than a wrong-build proof:

| # | mutation | declared RED | observed | verdict |
|---|---|---|---|---|
| 7 | **SHARED-SEEDER** — drop `blocked_by=[root]` from `seed_answer_cap_sandwich`'s noise | 5, **spanning BOTH suites** | 5, exact | **HELD** |

Selected receipts, verbatim:

```
# 1 — WB-E, the exact defect the adversary measured, now caught
E  AssertionError: a boot over 61 legacy dependency-bearing rows minted 50 blocks edges
   where the COLUMNS call for 61. …
E  AssertionError: 11 of 61 legacy rows were served a CONFIDENT EMPTY — 'ids=[] truncated=False'
   … sample='OK ids=[] truncated=False max_depth_used=32'
2 failed, 245 passed in 8.92s
PROOF HELD — the declared RED set fired EXACTLY

# 2 — WB-O
WARNING  loremaster.tasks:tasks.py:878 task.backfill.mint_failed_boot_continues
FAILED …TestANYBackfillFailureMakesEnsureReadyLOUD::…_LOUD_not_SILENTLY_PARTIAL[mint]
1 failed, 246 passed in 8.34s        PROOF HELD

# 3 — WB-CYCLE1 (all three topologies + the per-cycle leg)
4 failed, 243 passed in 9.00s        PROOF HELD

# 7 — the shared seeder, proven shared: pins in test_query_tasks_bounded.py AND
#     test_task_ledger.py[real] AND test_task_ledger.py[fake] all moved
5 failed, 277 passed in 7.77s        PROOF HELD
```

⚠ **PROOF 6's SCOPE IS STATED, because a scoped proof reported as a whole-suite one is the
thing this repo has receipts against.** Its command was
`pytest … test_blocks_edge.py -k TestCreateRefusesToFormACycle` (7 tests), not the whole
contract: a `LIMIT 0` on the write guard's read also disables persisted-id cycle detection,
so a whole-file declared set would have been a guess about a dozen unrelated pins rather than
a prediction. Within that scope the diff is still both-ways and it fired exactly:
`test_KNOWN_BOUND_…_DOES_grow_with_the_BLOCKED_population` and
`test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED`, `2 failed,
5 passed`.

⚠ **PROOF 4 CAUGHT A DEFECT IN MY OWN PIN, and I am recording it because a proof that only
ever confirms is not evidence.** On its first run the known-bound pin went red at the WRONG
assertion — a guard counting EVERY rendered line, whose message says *"the construction did not
produce the state it is named after"*. A builder who had just CLOSED the bound would have been
told their fixture drifted. That is the false-gate class verbatim (*a failure message that
promises a check the assertion does not perform*), caught only because I ran the mutation. The
guard now counts ROW lines (`startswith("- ")`) and the byte-diff is what fires, with the
message that names the real event. Re-proved: HELD.

---

## §A1 — backfill coverage above the fixture ceiling

`test_blocks_edge.py::TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE`, 2 pins.

- **The floor is DERIVED, not typed** — `LEGACY_BACKFILL_SCALE_FLOOR =
  max(LEGACY_BACKFILL_EDGES_LARGE, LEGACY_BACKFILL_EDGES_SMALL, UNRELATED_TASK_COUNT_LARGE,
  UNRELATED_TASK_COUNT_SMALL, len(LEGACY_COLUMN_DAG) + 2) + 1` = **61 today**. It RISES the day
  anyone raises a fixture, so a cap cannot come to sit just above a stale hard-coded number.
- **Discrimination is by GROWTH (61 and 122) with an EXACT-SET assertion at each**, per the
  adversary's specification — not a threshold, which is a value a builder can tune.
- **Two legs, neither implying the other:** the edge set is exactly the column's (the STORE's
  view), and no row is served `OK ids=[] truncated=False` (the CONSUMER's view). An edge set
  can be complete while the read is broken and vice versa.
- **Stated bound in the class docstring:** it measures COVERAGE, never round trips — its
  sibling `TestTheBackfillIsONETransaction` owns that, and a build can be perfectly bounded to
  one transaction while covering half the store.

## §A2 — a failed backfill makes `ensure_ready` LOUD, ∀ DOOR

`test_blocks_edge.py::TestANYBackfillFailureMakesEnsureReadyLOUD`, 3 pins.

Written as the adversary's *"better still"*: a PARAMETRISATION over
`BACKFILL_FAILURE_DOORS = ("existence-read", "mint")`, so the next door added is an entry
rather than a hole. An unknown door name raises inside the test rather than passing vacuously.

**How the MINT door is degraded, and why it is not a method name.** The existence door reuses
the derived, name-free `_patch_every_shared_policy_COROUTINE`. The mint door has no such
derivation, so it is keyed on a property of the STATEMENT: *a transaction whose text names the
`blocks` relation table and contains no `DEFINE` is an edge WRITE*, whatever the builder called
the method that composed it — `ENFORCED` gives that property for free, since an edge cannot be
minted without naming its own table. It fails CLOSED twice: if no such statement is ever seen
the leg reddens as vacuous, and the post-condition asserts no edges exist.

The **positive control** (undegraded boot over the same fixture completes AND mints the exact
expected set) is what stops the whole class being satisfied by an `ensure_ready` that raises
unconditionally, or by a fixture whose backfill has nothing to mint.

## §A3 — EVERY legacy cycle is RECORDED, ∀ TOPOLOGY

`test_blocks_edge.py::TestEVERYLegacyCycleIsRECORDEDNotJustTheFIRST`, 5 pins.

**MEASURED before the fixture was chosen** (`loremaster.tasks.find_blocked_by_cycle` +
`_drop_one_cycle_edge`, the shipped enumeration, against `networkx.simple_cycles`):

| topology | shipped records | `nx.simple_cycles` | members named |
|---|---|---|---|
| two disjoint 2-cycles | 2 | 2 | 4 / 4 |
| self-loop + 2-cycle + 3-cycle | 3 | 3 | 6 / 6 |
| `a↔b` overlapping `a→b→c→a` | 2 | 2 | 3 / 3 |
| complete triangle | **4** | **5** | 3 / 3 |

That measurement is why the pinned property is **MEMBER COVERAGE ∀ topology** plus **one record
per cycle on the DISJOINT topology only**. Pinning simple-cycle-set equality would make a
correct, honest build RED on the complete triangle — a C-DEF, not a catch — and what an operator
needs is *which rows to repair*, not a particular decomposition of an overlapping component.
The bound is stated in the class docstring with a **named re-open trigger**: the day the record
grows a per-cycle CONSUMER (a repair tool, a count served to an agent).

The disjoint fixture is also the first place arities 1, 2 and 3 co-exist — the sibling classes
hold one cycle each, which was the monoculture. `networkx` is the TEST's oracle only: two
independent enumerations are DIFFED, so the contract never hands the build its own answer key.

## §A4 — the write path's rows-read vs the BLOCKED population

Two changes in `test_blocks_edge.py::TestCreateRefusesToFormACycle`.

1. **The false gate is closed by NARROWING, which is what the adversary's own finding demands
   and all that is available without a ruling.** `test_the_WRITE_paths_rows_READ_does_NOT_grow_
   with_the_size_of_the_LEDGER` → `…_with_the_DEPENDENCY_FREE_population`, with the failure
   message rewritten to stop claiming a ∀-ledger property the assertion cannot perform and to
   name its sibling. The `PROOF 11` block at the foot of the file is updated with the new node
   id, a note that the mutation and its declared set are unchanged, and the new pin's expected
   colour under that same mutation.
2. **`test_KNOWN_BOUND_the_write_paths_rows_READ_DOES_grow_with_the_BLOCKED_population`** — a
   new pin that seeds DEPENDENCY-BEARING noise (the population the guard's
   `WHERE array::len(blocked_by) > 0` INCLUDES, which nothing had ever varied) at two sizes and
   asserts the read **grows**. GREEN today; RED the day anyone closes it, carrying *"if you
   closed it deliberately, DELETE this pin and say so"*, its rationale, and a **named re-open
   trigger**.

I did **not** widen the boundedness assertion to the blocked population. That would be RED
against the shipped build, i.e. a C-DEF, and the fix may not exist under R7's rider — **§ESC-1**.

## §A5 — a capped listing discloses nothing about its own bound

`test_query_tasks_bounded.py`, HOLE 8 + `TestACappedListingDISCLOSESNothingAboutItsOwnBOUND`,
2 pins.

This is a **leg-2 forgery construction in the law's literal sense**: two genuinely different
worlds — 40 matching tasks capped to 5, and a ledger holding exactly 5 — serve **byte-identical
responses** once the opaque ids are normalised. *Identical bytes = a false clear = STOP.*

I cannot close it: `server.py` is 04b-2's file and R5/R6 are the only named exceptions, the
render half of T1 and all of R9's elision line were routed to 04b-2 by an earlier wave, and
**04b-1 does not deploy** — so no consumer meets this surface before the packet that owes the
line. What a contract CAN do is make the false clear impossible to inherit silently, which is
`CLAUDE.md` § *WHEN YOU CANNOT CLOSE A HOLE, PIN IT* exactly. **Owner: 04b-2. Named decision
point: the wave that builds R9's elision line. §ESC-5 offers the lead the alternative.**

The **positive control** proves the normaliser can see a difference at all (a genuinely shorter
world renders differently through it) — without it, a normaliser that flattened everything
would pass the main leg for the wrong reason.

## §A6 — the double's `limit`, exercised for the first time

`test_task_ledger.py::TestQueryTasksHonoursTheLIMIT`, 3 tests × `[real]`/`[fake]` = 6 pins, on
the existing parity-pin fixture so BOTH implementations are held to the same contract.

- `test_the_limit_WINDOWS_the_answer` — deterministic on both backends; kills the exact
  mutation the adversary ran (delete the slice → 875 passed).
- `test_the_cap_applies_to_the_ANSWER_never_to_the_CANDIDATE_scan` — T1 at the ledger layer,
  with the subset assertion so a build that caps first and back-fills from the wrong side
  cannot pass a pure count.
- `test_POSITIVE_CONTROL_the_sandwich_really_holds_blocked_rows`.

**ONE seeder, not copy #2** (repo law #102 / brief-base §6): `_task_fakes.seed_answer_cap_
sandwich` is ledger-agnostic (it touches only `create_task`/`create_many`) and is called by
BOTH this class and the pre-existing live-ledger class. It lives beside the double because that
is the one module both suites may import without dragging SurrealDB into the fake-only legs.
**Sharing is proven by MUTATION, not by inspection** — PROOF 7, 5 declared reds spanning both
files, exact.

**Stated bound, inherited from the surface rather than invented:** `query_tasks` promises no
ordering, so T1's *short-answer* direction is deterministic under insertion order and its
reverse and probabilistic (≈7e-7 per run at these sizes) under record-id order. That is the
same analysis the live-ledger class states; it is RESTATED because these constants differ, and
the constants are deliberately NOT shared — that file's probability argument is computed from
ITS numbers, and a shared constant would silently re-open it the day someone tuned this
suite's cost.

---

## §B — LEG 1, corrected and widened

In `test_blocks_edge.py`'s module docstring, which is where the packet's whole scope-diff table
lives.

- **Row 1 (`transitive_blockers`) — CORRECTED.** *"CLOSED by ruling R11's backfill"* is gone.
  The predicate now names the fact: *"…over the `blocks` EDGES **this ledger's last completed
  `ensure_ready` mirrored** … **at this ledger** …"*, and difference (a) says explicitly that a
  PARTIAL or swallowed migration re-opens it — pointing at the two constructions (§A1, §A2)
  that now make those states measurable rather than arguable. A new difference **(d)** names the
  wrong-instance case (`at this ledger`), which row 3 had and this row did not.
- **Row 2 (`query_tasks`) — CORRECTED.** *"No unnamed difference remains"* is gone and replaced
  with the measurement: `limit=5` against 40 matching tasks renders five rows and nothing saying
  the listing is partial, nor which five (no ORDER is pinned, so the choice is arbitrary and
  unstable). It names the owner (04b-2), the pin that holds the bound, and §ESC-5.
- **Row 3 (blocker pre-check) — KEPT VERBATIM**, with one addition: a note saying it is the
  model for the other four and why (*at this ledger* = wrong-instance, *as of the check* =
  TOCTOU, both FACTS, no disclaimer word), and *"do not weaken it."* I read the adversary's
  reasoning before touching anything in that block; I changed nothing in row 3's own text.
- **Row 4 (`send` sender guard) — unchanged**, it was correct.
- **THREE NEW ROWS**, the surfaces that had none: the **cycle refusal** (walks the COLUMN, so an
  edge-only cycle is invisible — a difference, not a defect, because R7's rider establishes the
  closing dependency cannot carry an edge; and the batch-key vs persisted-id vocabularies
  deliberately differ per R6); the **migration's operator record** (per-BOOT and per-READ, not a
  survey — and it *used* to name only the first cycle, now ∀, §A3); and **`ensure_ready`'s
  normal return** (no difference is carried because the claim is ENFORCED rather than
  disclosed — ∀ doors raise, ∀ rows are covered — and both pins exist because WB-O made this row
  false while passing the whole contract).
- **The stated bound is preserved and not weakened:** Leg 1 is sound on *set* and
  *predicate-as-WRITTEN* only; time, environment and *predicate-as-EXECUTED* are BELIEVED. A new
  header above the table says, in one sentence, why rows 1 and 2 were false and what the general
  correction is: *a row may state only what the response is TRUE of; where a guarantee depends
  on something having happened, name that something as a FACT rather than asserting the
  difference away.*
- **`test_query_tasks_bounded.py` gains a LEG-1 POINTER section** (the adversary's note that a
  reader opening the #253 addendum alone meets no scope diff), naming where the row lives, the
  two named differences, the unnamed one, and Leg 1's own bound.

---

## §ESC — the escalations. I settled the two that were mine to settle; three go to the lead.

**ESC-1 — is a ledger-independent write-path cycle read AVAILABLE under R7's rider? UNSETTLED,
LEAD'S CALL.** I implemented the half that is unambiguously mine (the false gate is closed by
narrowing; the residual is pinned as a bound) and did NOT decide the design question.
- *(i) the property is achievable* — bound the read to the ancestor closure of the NEW
  dependencies. Those are persisted, so after this packet their upstream chains DO carry edges,
  and only the batch-local part need stay client-side. Then the KNOWN-BOUND pin is a defect
  report and should be deleted with the fix.
- *(ii) it is not achievable at one round trip* — then the bound stands as pinned and the
  re-open trigger is the mechanism.
- **MY RECOMMENDATION: (i), but MEASURE before ruling** — and note the routing rule
  (`CLAUDE.md`: *a design problem never reaches a builder*): this is a property to INVENT, not a
  spec to implement, so it belongs with the operator or an Opus author required to attack its
  own design, never in a fix-wave brief saying *"build the general form"*.
- ⚠ Whichever way it lands, the false gate itself is already closed — that half needed no ruling.

**ESC-2 — the R7 read sibling and the retry-label gate: DISCHARGED, with a receipt.** The
adversary hit this on ITS OWN reference build, not on the shipped one. Re-derived here: at
`b8607c4` the shared attempt body was EXTRACTED (`store/_txn.py::_run_verified_transaction`,
which both `execute_transaction` and `execute_read_transaction` ride), so there is one labelled
call into the driver rather than two. `uv run pytest -q -n auto -p no:randomly
loremaster/tests/test_retry_seam.py` → **`562 passed`**. Nothing is owed. Recording it because
"the adversary reported a red test" would otherwise be inherited as an open item.

**ESC-3 — `networkx` install authorization: DISCHARGED, and it opened a NEW question.** The
operator authorised and installed it at `54d0585` (networkx 3.6.1, verified in the venv), which
is what let me build the independent oracle in §A3. The new question is production's: the
shipped `_record_legacy_cycles` hand-rolls all-cycle enumeration with a drop-an-edge loop, and
the builder's `bespoke` verdict rested on *"networkx is not a dependency"* — TRUE when written,
FALSE now. Filed as **#273** with the four-topology measurement and a recommendation
(`replace` the enumeration, `keep` `graphlib` for DETECTION). **Not settled here: production is
outside a contract author's writable set, and two libraries for two questions should be a
deliberate ruling.** Two consequences either way: **#272** (`types-networkx` / the pyproject
mypy override, with the exact edit) is owed by whoever owns `pyproject.toml`.

**ESC-4 — Leg-1 row 1's *"CLOSED"*: IMPLEMENTED as the adversary recommended.** The row-3
treatment: state the fact, and let the new pins do the closing. §B.

**ESC-5 — NEW, and it is the one I most want ruled: who closes the capped-listing false clear?**
- *(i) 04b-2 closes it* — the render is that packet's file, R9's counted-elision grammar is
  already ruled, the store-side count it needs does not exist at 04b-1's layer, and 04b-1 does
  not deploy, so no consumer meets the surface first. Cost: the false clear exists in the tree
  between the two packets, held only by a pin.
- *(ii) widen 04b-1's writable set by one more named exception* (as R5 and R6 already are) and
  close it now. Cost: a store-side count is a second read on the query path — a real
  performance decision on a served surface, which is exactly the kind of thing R7/#253 have been
  fighting all packet, and it lands in a packet whose gates are already green.
- **MY RECOMMENDATION: (i)**, on the operator's own trust principle read narrowly — the harm
  requires a DEPLOY, 04b-1 has none, and the pin makes the hole impossible to inherit silently.
  **But the operator's tiebreaker is *"AGENT CONFIDENCE AND TRUST TRUMP EVERYTHING"* and T1 is
  titled *NO SILENT SHORT ANSWERS*, so I am not willing to call this one myself.**

---

## §DEV — the one deviation

`TestTheCapAppliesToTheANSWERNotTheCandidateScan._sandwich_ledger` — a pre-existing,
load-bearing pin's fixture in `test_query_tasks_bounded.py` (in my writable set) — was
**re-pointed at the new shared seeder** rather than left as copy #1 of two. Disclosed because it
edits a pin I did not author and the brief's worklist did not name it.

- **Why:** §A6 needs the identical sandwich against the DOUBLE. Writing a second one is copy #2
  of a policy whose SHAPE carries the discrimination argument — brief-base §6 says escalate
  rather than quietly write it, and §6 also says *"if the existing thing almost fits, propose
  extending it; do not fork it."* Extending it fitted exactly.
- **Its constants did NOT move** (`_BLOCKED_NOISE_EACH_SIDE`, `_ANSWER_CAP` stay in that file
  and are passed in), so its probability analysis still describes its own fixture.
- **Verified:** the class is `3 passed` on the current build, and PROOF 7 shows a mutation to the
  shared seeder reddens its pins AND `test_task_ledger.py`'s, `[real]` and `[fake]` — which is
  the only evidence that distinguishes sharing from looks-like-sharing.

---

## §RESIDUALS — one line per item, individually adjudicated

| # | item | verdict |
|---|---|---|
| R-1 | `types-networkx` absent → an inline `# type: ignore[import-untyped]` at ONE import site where the house idiom is a `pyproject.toml` mypy override | **FLAGGED, not fixed — `pyproject.toml` is outside the writable set.** Exact edit in finding **#272**; the ignore MUST be deleted in the same commit as the override (mypy reports unused ignores — measured this wave). |
| R-2 | Production hand-rolls all-cycle enumeration now that networkx is authorised | **FLAGGED, finding #273 + §ESC-3.** Not a defect: the pinned property holds either way, measured on four topologies. |
| R-3 | The complete-triangle decomposition (shipped 4 records, `nx` 5) | **DELIBERATE BOUND**, stated in the class docstring with a named re-open trigger. Pinning set-equality would be a C-DEF. |
| R-4 | The write path's growth with the BLOCKED population | **OPEN BOUND, pinned** (§A4) + **§ESC-1**. Not settled by me. |
| R-5 | The capped-listing false clear | **OPEN BOUND, pinned** (§A5) + **§ESC-5**. Owner 04b-2; named decision point recorded in HOLE 8. |
| R-6 | T1's short-answer direction is probabilistic (≈7e-7) under record-id order, on both the new double pins and the pre-existing live one | **WITHIN A STATED BOUND, restated rather than inherited.** It is a probability, not a proof; it cannot be closed without pinning an ORDER this contract deliberately does not pin. |
| R-7 | The MINT-door degradation is keyed on statement TEXT (`blocks` table named, no `DEFINE`) rather than on a derivation | **ACCEPTED, and it fails CLOSED**: an unseen statement reddens the leg as vacuous. A name-free derivation was not available; `ENFORCED` makes "an edge write names its own table" a property rather than a convention. |
| R-8 | `PROOF 11`'s comment block in `test_blocks_edge.py` names a renamed node id | **UPDATED in the same edit**, plus the new pin's expected colour under that mutation. Re-derived by `--collect-only`; not transcribed from the source. |
| R-9 | r5's headline RED count (163/69) does not reproduce; the delta adversary derived 165/69 over 234 | **RE-DERIVED INDEPENDENTLY: 234 collected at HEAD before my edits, 247 after.** I did not re-run the pristine-production RED count (this wave's build is GREEN, so there is no pristine tree to run it against); the COLLECTED number is mine and it matches the adversary, not r5. |
| R-10 | The delta adversary's §RESID-1/-2 (`_ENGINE_REJECTION_MODES` claims four engine reasons where there are three classes; the timeout described as *"ran and was cut off"* where the engine says *"was not executed"*) | **NOT FIXED — outside my six-item worklist and they are prose in a pin I did not author.** Both are one-line docstring corrections; I would make them exactly as the adversary words them. **Lead's call whether to fold them into this wave.** |
| R-11 | The delta adversary's §RESID-6 (a mis-indented `subject=` continuation in `TestCreateRefusesToFormACycle`) | **NOT FIXED**, cosmetic, `ruff` clean over it. Named here so it is not re-found. |
| R-12 | The delta adversary's §RESID-5 (the `wrong-instance` verb is named as a re-open trigger but never CONSTRUCTED) | **STILL OPEN, and now partly mitigated in PROSE only:** Leg-1 row 1 gained the *"at this ledger"* wording row 3 had. The CONSTRUCTION is still owed and is inside §11.1's declared curated-interim bound. |
| R-13 | Six mutation proofs ran; a seventh direction — a wrong build that satisfies the new §A1/§A2 pins while breaking something else — was NOT hunted | **STATED, not claimed away.** I graded the pins I wrote against the builds they target; I am not the adversary, and the brief's own ruling is that an adversary grades this before a builder touches it. |
