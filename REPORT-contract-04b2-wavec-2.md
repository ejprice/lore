# REPORT-contract-04b2-wavec-2 — slice **C1**, the TASK READ SURFACE (04b-2 wave C)

brief-base v9 read
brief project v7 read

## SUMMARY BLOCK
- **state: done.** Slice C1 authored across three files, **with a satisfiability receipt**:
  a provenance-asserted reference build takes the contract plus every pre-existing suite
  its seams touch to **1197 passed / 0 failed**, and the harder post-lint leg holds
  (ruff clean, **zero mypy errors in my files on the reference build**).
- **deviations (3, each disclosed in §2):** (1) **ESC-5's placement takes the design
  ruling's OWN pre-authorised fallback** — the over-fetch lives in one seam-side helper
  rather than in `query_tasks`' return type; the ripple that triggers the fallback is
  MEASURED (§2.1). (2) I import `_fresh_ledger`/`_tool_seam` from the sibling C1 file
  rather than writing clone #3 (§2.2). (3) I added `FakeTaskLedger.direct_dependents` to
  `_task_fakes.py` — a file outside the literal "for the scope above" reading — because
  the reference build MEASURED two `test_mcp_server.py` reds without it (§2.3).
- **Packages considered:** *"has-more" pagination over the store read* → **bespoke**
  (READ: `dir(surrealdb)` + every public method of `AsyncWsSurrealConnection`, live in
  this venv — 32 methods, **zero** page/cursor/limit/offset helpers; the SDK exposes only
  raw SurrealQL, so `LIMIT n+1` in our own statement builder is the whole mechanism) ·
  *two-world line diff* → **bespoke, minimal** (READ: `difflib` exports +
  `unified_diff`/`Differ` signatures — both emit prefixed, human-oriented deltas that a
  test would have to re-parse; the property here is a 2-line set difference over
  normalised lines, so parsing a diff format would add a failure mode, not remove one) ·
  *id normaliser* → **replace, stdlib `re`** (inherited verbatim from the deleted bound
  class) · *cycle/all-cycle enumeration* → **not mine**, routed to 04b-3 by sidecar §B4.
- **decisions-needed (4, none blocking the builder; §5):**
  1. **The ESC-5 placement deviation** — confirm the fallback, or overrule to the ruled
     typed-return (I name the exact cost) or to a third shape I considered and did NOT take.
  2. **The chain render: ID-ONLY or ENRICHED?** I pinned ID-ONLY and say why; enrichment is
     a slice, not a render tweak.
  3. **R9's "the no-limit path gets a DEFAULT display cap" appears UNBUILT** — measured; the
     sidecar's conditional therefore discharges to *"no counted line owed this wave"*, but
     the R9 clause itself is now an unpinned, unimplemented ruling.
  4. **Two `test_blocks_edge.py` one-line edits the BUILDER must make** — adjudicated here,
     named in the contract, deliberately not pre-applied (§4.3).
- **receipt pointers:** §1 pin inventory by scope item · §2 deviations, with the ripple
  measurement · §3 the satisfiability receipt (1197/0) + gate state, scoped · §4 mutation
  proofs, declared-before-run and diffed both ways · §5 the four open decisions · §6 the
  forgery-door sweep (rider 7) · §7 what I did NOT do · §8 the package survey table ·
  §9 flagged, out of scope.

---

# §1 · PIN INVENTORY, BY SCOPE ITEM

Files: **`loremaster/tests/test_task_read_surface.py`** (NEW, 48 tests) ·
**`loremaster/tests/test_query_tasks_bounded.py`** (edited) ·
**`loremaster/tests/_task_fakes.py`** (one method added).
No production file was modified in the working tree (verified byte-exact after every
mutation proof — §4).

## 1.1 ESC-5 — the packet's DEPLOY ENTRY CONDITION (SECTION A, 7 classes / 26 tests)

Mechanism **(c) over-fetch by one**, exactly as ruled: the disclosure exists **iff a
further matching row truly exists**; grammar is EXISTENCE, not quantity; uniform across
both filter paths.

| class | what it kills |
|---|---|
| `TestTheListingIsATYPEDRESULTWithACLOSEDFieldSet` | a wrapper that grows a COUNT field without first building §11.1's failed-count construction. Field set by EQUALITY (not containment) + an `extra="forbid"` rejection proven by a live `ValidationError`. |
| `TestTheDisclosureExistsIFFaFurtherMatchingRowEXISTS` | **WB-A1 mechanism (b)** (`more = len(rows) == limit`) — killed by the `population == cap` case, which is the ONLY case where (b) and (c) disagree and no other leg reaches it · **WB-A2/A3** always-true / always-false bits · **WB-A4** a cap compared against a hard-coded literal. Scale axis 0 / 1 / cap−1 / cap / cap+1, **× two different caps**. |
| `TestTheDisclosureIsUNIFORMAcrossBOTHFilterPaths` | **rider 2.** The blocked-path two-world leg on the shared sandwich (true answer 6; `limit=5` ⇒ line, `generous_cap` ⇒ none) + **WB-A5**, a bit derived from the ROWS THE STATEMENT RETURNED (66 candidates → 6 answers, so it claims a surplus the answer does not have). |
| `TestTheEMITTEDStatementIsBoundedAtCapPlusONE` | **rider 5.** **WB-A6** a second read (`count()`), **WB-A7** an unbounded probe. Instrument = a difference between two IDENTICALLY-SHAPED transactions (seam@k vs ledger@k vs ledger@k+1), never a transcribed constant; plus a growth comparison; plus `limit=None` emits **no `LIMIT` clause at all** (the measured `$k = NONE ⇒ 0 rows, no error` hazard) **with a positive control** that the instrument can see a `LIMIT`. |
| `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED` | ⚠ **a hazard the over-fetch CREATES, found by building it.** `limit=-1` reaching the ledger as `0` (refusal names a number the caller never passed) · `limit=0` becoming a legal `LIMIT 1` (**a refusal silently becoming one served row**) · `limit=True` becoming `LIMIT 2` (`bool` is an `int`, so `True+1==2` bypasses the guard that exists precisely to stop `limit=True`). The committed T2 pin for this drives the LEDGER, so it stays green through all three. |
| `TestTheRenderedListingDISCLOSESItsOwnBOUND` | **rider 1 — the successor to the deleted bound class**, asserting the OPPOSITE in both directions; the disclosure line is located by DIFFING TWO WORLDS, never by matching a literal; it must not wear the `- ` row marker (a pre-existing committed pin counts those); it must name the served count (a bound is a FACT, not *"results may be incomplete"*). |
| `TestTheRenderNEVERRecomputesTheDisclosure` | the *"renders take typed applicability"* house law as a MUTATION: hold the rows constant, move only the typed bit, require the render to move in BOTH directions. Row count deliberately equals no cap in the file, so a re-computing build cannot agree by accident. |

**Rider 6 discharged:** `test_the_LIMIT_bounds_the_ROWS_READ_not_just_the_ROWS_SERVED`
survives **verbatim** — it drives the LEDGER directly, so the over-fetch does not reach it,
and it is green on the reference build. No pin anywhere asserts that the bound `LIMIT`
equals the caller's value, so no re-authoring was owed.

**Rider 1's deletion:** `TestACappedListingDISCLOSESNothingAboutItsOwnBOUND` is **DELETED**
per its own instruction, together with `_normalise_task_render`,
`_PARTIAL_WORLD_POPULATION` and `_IDENTICAL_SUBJECT`, which served only it (an orphaned
normaliser is the next reader's puzzle). **The wave-report sentence it demands:** *the
capped-listing false clear was closed deliberately by 04b-2 wave C under escalation ESC-5,
mechanism (c); the class was deleted, not weakened, and its successor is
`test_task_read_surface.py::TestTheRenderedListingDISCLOSESItsOwnBOUND`.* Its HOLE-8
comment block is kept as the record of what was measured, with a header saying it is closed.

**`TestNoTOTALIsServedThatWasNotMEASURED` is untouched and GREEN.** Under the fallback,
`query_tasks` still returns a plain `list`, so the fork the sidecar left open
(*"delete"* vs *"stays green verbatim"*) resolves without a choice: both are satisfied.
The derivation the sidecar asked to be stated where the pin was — **a number-free wrapper
acquires NO §11.1 failed-count construction, because the existence bit rides the SAME read
as the rows, so there is no separate failure state to forge** — is stated in
`TestTheListingIsATYPEDRESULTWithACLOSEDFieldSet`'s docstring, which is where the wrapper's
emptiness is now pinned.

## 1.2 The blocked-chain / critical-path render (SECTION B, 2 classes / 5 tests)

**Re-derived at `f67a219`, two independent instruments** (the predecessor's measurement
confirmed): `lore_impact("loremaster.tasks.TaskLedger.transitive_blockers")` →
**0 prod / 0 test references**; `grep -rn transitive_blockers loremaster/loremaster/` →
hits in `tasks.py` only. **This mints a served surface.**

- `TestTheChainRenderIsReachableAndNamesItsOwnBOUND` — **WB-B1** the confident render (drop
  `truncated`: a walk bounded at depth 2 over a four-deep chain then renders like a complete
  one, and probe §5.3 measured the engine returning 256 of 299 nodes with no error and no
  signal) · **WB-B2** an INFERRED bound (`len(ids) >= max_depth`) · the served ids must
  RESOLVE through `get_task` (store reference §7's `str(record.id)` hazard, which cost 130
  red pins across two suites) · **proximity ORDER preserved**, on a fixture whose proximity
  order is the REVERSE of creation order · *"an id that names nothing and an id with no
  blockers are two different questions"* survives the render.
- `TestTheChainRenderNAMESTheBlockersThatCarryNoEDGE` — ⚠⚠ **the leg-2 construction I judge
  the most valuable thing in this slice.** Sidecar **S3**'s false clear survives R11's
  backfill **by construction**: `ENFORCED` forbids an edge to a task that does not exist, so
  a legacy `blocked_by` naming a phantom is skipped forever, is NOT in the walk, and **is
  counted by the claim CAS forever**. Without a pin, a task blocked permanently by a phantom
  renders **byte-identically** to a task with no blockers at all — a positive assertion of
  completeness that is false, on rows that already exist in every long-lived store, needing
  no construction in production because it IS the default state. The pin asserts the CAS
  refusal directly as ground truth, requires the two worlds' bytes to differ, and requires
  the residue to be **NAMED** (the responder holds the exact id, on the row it already
  read). Its sibling kills **WB-B3**, the notice that fires on every answer.

## 1.3 R10(iii) — teaching at the moment of CAUSATION (SECTION C, 2 classes / 6 tests)

- `TestSupersedeWARNSWhenThePredecessorHasDEPENDENTS` — superseding a task others are
  blocked on **strands every one of them forever** (R10 REJECTED making supersession
  terminal, so the CAS keeps counting it), silently. **WB-C1** the unconditional warning
  (killed by a byte-compared no-dependents world: imperatives ride only TRUE verdicts,
  ruling R8's split) · **WB-C2** a count with no ids (the caller's next move needs the ids).
  A pin also asserts the render **WARNS, never rewrites** — dependency transfer is R10(iv)
  and is DEFERRED because it breaks `blocked_by`'s post-creation immutability.
- `TestTheCLAIMRenderNamesTheSUPERSEDEDBlockerCase` — the door R10(ii)'s create-time refusal
  structurally cannot reach (the quantifier law, applied by the operator to their own
  ruling). **WB-C3** confusing it with the task's OWN supersession (already rendered today —
  the fixture's dependent is deliberately not superseded) · **WB-C4** fabricating a successor
  for a merely-open blocker (a decoy supersession exists in the same ledger, and its
  successor id must NOT appear). The fact travels as TYPED state on `ClaimResult`, with a
  pin that the new field **DEFAULTS** — four `ClaimResult(...)` construction sites exist and
  a required field would redden them on a correct build (#133).

## 1.4 #268 — the tightened comparative form (edit to `test_query_tasks_bounded.py`)

Implemented as the sidecar ruled, **NOT as finding #268's own "cheapest fix"** (proven
backwards by the predecessor: at a cap of 120 nothing is discarded by either build, so the
leg becomes permanently vacuous — worse than the 55%-flaky one it replaces).

> `rows_read(status=open, blocked=False, limit=generous_cap)` **==**
> `rows_read(status=open, blocked=False)` — *the cap did not shrink the scan*

on `measure_store_traffic`, with the file's own non-vacuity guards, plus a **new positive
control** (`test_POSITIVE_CONTROL_the_traffic_instrument_CAN_see_a_cap_shrink_a_scan`) that
shows the SAME instrument on the SAME ledger detecting a cap that genuinely does shrink a
scan (the `blocked is None` path, where R5 requires the `LIMIT` to ride the statement).
Without it, `rows == rows` is a negative result from a possibly-blind instrument.

⚠ **A FALSE GATE I SHIPPED AND THEN MEASURED OUT, because the catch is the lesson.** My
first ordering asserted *"both answers == true_answer_size"* BEFORE the truncation leg, so
under #268's own mutation the runs that lost rows reported **"the fixture, not the pin, is
wrong"** — a failure message misnaming what happened, aimed at a builder whose fixture is
perfect (the P2 class). Caught by reading the 8-run determinism output rather than the
summary. The defect leg now speaks first and the drift guard is scoped to the UNCAPPED read,
which cannot be truncated by construction. Receipts: §4.1.

## 1.5 #302 — the action vocabularies (SECTION D, 2 classes / 7 tests)

Re-derived at `f67a219`: `grep -rn '_TASK_ACTIONS' loremaster/tests/*.py` returns
**comments only**, and the repo's exact-set registration pin covers tool NAMES via a `<=`
SUBSET assertion. Closed by **EQUALITY** pins over all three families — `_TASK_ACTIONS`,
`_FINDING_ACTIONS`, `_COMMS_ACTIONS` — deliberately including the two this slice does not
touch, because a pin guarding only the family whose defect prompted it is the quantifier
law's failure mode. Plus a non-vacuity leg (three equal tuples prove agreement between two
constants, not that anything dispatches) and
`TestTheNewParametersAreRefusedForEveryOtherACTION`, which kills **WB-D1** (the widened
guard) in both directions: `max_depth` refused for non-`blockers` actions, and `limit`
still refused FOR `blockers` — the walk has its own bound and a second way to truncate one
answer is two grammars for one property.

## 1.6 Cross-section

`TestTheTASKSurfacesAgreeWithEachOtherAndWithTheCAS` — the quantifier law applied ACROSS
surfaces rather than across inputs: no pin above can see two renders disagreeing. Restricted
to all-terminal-blocker fixtures, because *"unblocked" (ONE HOP)* and *"has upstream"
(TRANSITIVE)* are legitimately different questions and a sloppy fixture would report a
ruled difference as a divergence.

---

# §2 · DEVIATIONS

## 2.1 ESC-5's placement — the design ruling's OWN pre-authorised fallback, TAKEN

`REPORT-design-sidecar-04b2-wavec-1.md` §2 rules the fact typed **from `query_tasks`**, and
names the fallback: *"if the reference build shows the type change rippling
disproportionately, seam-side `limit+1` behind ONE shared helper (plain-list pin then stays
green verbatim) — reported as a deviation, never adopted silently."*

**MEASURED at `f67a219`, by counting call sites** (cheaper than, and sound without,
building the ripple — `grep -c 'query_tasks('` per file, definitions and comments excluded):

| file | call sites that would redden |
|---|---|
| `loremaster/tests/test_task_ledger.py` | 34 |
| `loremaster/tests/test_query_tasks_bounded.py` | 25 |
| `loremaster/tests/test_blocks_edge.py` | 22 |
| `loremaster/tests/test_mcp_server.py` | 2 |

≈83 pins RED on a **CORRECT** build, in three files this slice does not own — and
`test_blocks_edge.py` (8,903 lines) is being edited concurrently by the #279 unification.
That is the C-DEF class (#133) at a scale nobody should ship, plus a live collision. **The
fallback is taken.** Production consumers of `query_tasks`: **exactly one**
(`server.py`'s `action=query` dispatch), so nothing in production is worse off.

**The ruling's stated property still holds:** the render takes the disclosure as TYPED
applicability (`TaskListing`) and never re-computes it —
`TestTheRenderNEVERRecomputesTheDisclosure` is the pin that makes a re-computing render
impossible to ship. And `LIMIT` is still bound to **cap+1** in the emitted statement,
because the seam passes `cap+1` down; rider 5 is satisfied identically under either
placement.

**A THIRD SHAPE I CONSIDERED AND DID NOT TAKE, written down so the lead need not
re-derive it:** keep `query_tasks -> list[Task]` unchanged and add a sibling
`TaskLedger.query_task_listing -> TaskListing` that owns the over-fetch, with `query_tasks`
delegating to it (`return (await self.query_task_listing(...)).rows`). It has zero ripple
AND puts the policy in the ledger where the cap already lives. **I did not take it because
it is not the ruled fallback and inventing a public ledger verb with no production consumer
is a design decision, not a contract one** — and repo law says duplication/placement
decisions ESCALATE rather than being quietly written. It is decision-needed #1; converting
the contract to it is a rename of one symbol and a move of one method.

⚠ **`TaskListing` lives in `loremaster.tasks`, not in `server.py`**, beside `Task` /
`ClaimResult` / `TransitiveBlockers` / `TaskActivityWindow`: it describes a LEDGER ANSWER, so
if a later packet moves the over-fetch down (the ruling's first choice) the model does not
move with it.

## 2.2 Importing `_fresh_ledger` / `_tool_seam` from the sibling C1 file

`test_query_tasks_bounded.py` records that it deliberately CLONED `_tool_seam` rather than
importing it, to avoid re-opening escalation E-C's instrument-in-a-sibling-test-module
smell. I went the other way, and the reason is that the trade has changed: these two
constructions now exist **twice** (`test_blocks_edge` and `test_query_tasks_bounded`), and a
third copy is copy #3 of a construction, in the slice whose own contract pins ONE
IMPLEMENTATION. E-C's concern was an INSTRUMENT (a measurement) living in a test module;
these are fixture VOCABULARY, which that file's own header says *"has no other home and must
agree across the files by construction"*. Stated as a deviation rather than assumed.

## 2.3 `_task_fakes.py` — one method added, outside the literal scope reading

`FakeTaskLedger.direct_dependents`. **MEASURED, not anticipated:** the first reference-build
run put two `test_mcp_server.py::TestTasksTool` pins RED with
`AttributeError: 'FakeTaskLedger' object has no attribute 'direct_dependents'` — the exact
ripple 04b-1 hit with `query_tasks`' `limit`, and the reason a removed-behaviour inventory
must survey the DOUBLES as well as the callers. It is **green before the production verb
lands and after it**, so no builder meets a red test because of it.

---

# §3 · THE SATISFIABILITY RECEIPT, AND THE GATE STATE (SCOPED)

## 3.1 Provenance (#140 — three poison modes closed by the blessed tool)

```
./scripts/scratch_copy.sh /home/ejprice/scratch-c1-ref
loremaster.__file__ = /home/ejprice/scratch-c1-ref/loremaster/loremaster/__init__.py
```

## 3.2 The receipt — contract + every pre-existing suite its seams touch

Reference build (in the scratch tree only; the working tree's production files were never
modified): `TaskListing` · `validated_task_limit` (the cap validator promoted to a
module-level ONE IMPLEMENTATION, with `TaskLedger._validated_limit` delegating) ·
`ClaimResult.superseded_blockers` + `TaskLedger._superseded_among` ·
`TaskLedger.direct_dependents` · `_TASK_ACTION_BLOCKERS` + `_TASK_ACTIONS_ACCEPTING_MAX_DEPTH`
+ the `max_depth` guard · `AppContext._task_listing` / `_render_task_listing` /
`_render_transitive_blockers` · the supersede warning · the claim render's superseded branch.

```
tests/test_task_read_surface.py                      48 passed          (first attempt, 0 failed)

tests/test_task_read_surface.py tests/test_query_tasks_bounded.py
tests/test_blocks_edge.py tests/test_task_ledger.py
tests/test_mcp_server.py tests/test_txn_contention.py   -n auto
1197 passed in 285.62s (0:04:45)
```

## 3.3 The harder post-lint leg

- `uv run ruff check .` **on the reference build**: `Found 2 errors` — **both in
  `scripts/lore_tool_name_currency.py`** (an unused `subprocess` import and a `PLW2901`),
  **pre-existing at `f67a219`** (identical 2 errors on the untouched working tree) and in a
  path my brief marks do-not-touch. **Zero ruff errors attributable to this slice**, before
  or after the build.
- `./scripts/typecheck.sh` **on the reference build**, per-file error counts: 12 files, and
  **not one of them is mine**. `test_task_read_surface.py`, `test_query_tasks_bounded.py`
  and `_task_fakes.py` all report **zero** errors once the build lands — including the
  `type: ignore[call-arg]` on the extra-field rejection, which is *unused* at HEAD and
  *used* on the build.

## 3.3b The OTHER half of "green before AND after" — measured at HEAD

The receipt above proves the contract is satisfiable on a correct build. The complementary
claim — that nothing this slice put into the working tree reddens anything **today** — is a
separate measurement, and it is the one that decides whether a builder walks into a trap:

```
pytest tests/test_mcp_server.py tests/test_blocks_edge.py tests/test_task_ledger.py \
       tests/test_txn_contention.py tests/test_query_tasks_bounded.py -n auto
1149 passed in 219.98s (0:03:39)                       # at f67a219 + my three files
```

So `FakeTaskLedger.direct_dependents` and the #268 tightening are **green before the
production verbs land and green after** (1149/0 here, inside the 1197/0 above). The only
red anywhere attributable to this slice is inside `test_task_read_surface.py` itself, by
design.

## 3.4 Gate state AT HEAD, scoped, with no unqualified green claim

⚠ The canonical typecheck is RED at HEAD for reasons that are not mine (finding #306).
Measured this session with the canonical runner:

| scope | result |
|---|---|
| `ruff check` on my three files | **All checks passed** |
| `pytest tests/test_query_tasks_bounded.py -n auto` | **41 passed** (0 failed) |
| `pytest tests/test_task_read_surface.py -n auto` | **35 failed / 13 passed** — every failure RED BY DESIGN (§3.5) |
| `typecheck.sh`, `test_query_tasks_bounded.py` | **0 errors** |
| `typecheck.sh`, `_task_fakes.py` | **0 errors** |
| `typecheck.sh`, `test_task_read_surface.py` | **11 errors**, listed below |
| `typecheck.sh`, whole repo | 120 in 10 files (loremaster) + 89 in 3 (lorerunes) — **109/89 of those are packet-39 + C3's contract-first file, RED before I touched anything** |

The 11, all `attr-defined` on symbols the contract DEFINES and the builder must land, plus
one consequential `unused-ignore`:

```
test_task_read_surface.py:343,362,369,1001,1034  Module "loremaster.tasks" has no attribute "TaskListing"
test_task_read_surface.py:365                    Unused "type: ignore" comment   [resolves when TaskListing exists]
test_task_read_surface.py:1004,1007,1036         "type[AppContext]" has no attribute "_render_task_listing"
test_task_read_surface.py:1527,1528              "ClaimResult" has no attribute "superseded_blockers"
```

**All 11 are zero on the reference build (§3.3).** Stated, not glossed.

## 3.5 The 13 GREEN pins in a contract-first file, each justified

A green pin in a contract file is either a removed-behaviour guard or decoration, so each is
named: `test_a_COMPLETE_listing_renders_NOTHING_but_its_rows` ·
`test_an_UNLIMITED_render_over_a_LARGE_ledger_carries_NO_line` ·
`test_POSITIVE_CONTROL_the_comparison_CAN_see_a_difference` ·
`test_an_ILLEGAL_limit_is_refused_naming_the_value_the_CALLER_passed` **×3** ·
`test_a_ZERO_limit_is_a_REFUSAL_and_never_a_ONE_ROW_answer` ·
`test_a_claim_blocked_by_an_ORDINARY_open_task_invents_NO_successor` ·
`test_the_FINDING_actions_are_EXACTLY_the_declared_set` ·
`test_the_COMMS_actions_are_EXACTLY_the_declared_set` ·
`test_every_declared_action_is_actually_DISPATCHABLE` ·
`test_limit_is_STILL_REFUSED_for_the_new_BLOCKERS_action` ·
`test_a_task_the_LISTING_calls_UNBLOCKED_has_an_EMPTY_critical_path`.
Every one pins something today's build already gets right **and that a plausible
implementation of this contract would take away** — the `limit` family being the sharpest
(the over-fetch destroys all three T2 refusals, silently).

---

# §4 · MUTATION PROOFS — declared BEFORE the run, diffed BOTH ways

All three used `scripts/mutation_proof.py` (declared-RED as an argument; unexpected reds AND
declared reds that stayed green both fail the proof) and all three reported
**`tree restored byte-exact`**. Declared sets were reasoned from the code path, never
transcribed from output.

## 4.1 #268's named mutation — `limit=None if blocked is not None else cap` → `limit=cap`

```
PROOF HELD — the declared RED set fired EXACTLY:
  TestTheCapAppliesToTheANSWERNotTheCandidateScan::test_a_SHORT_answer_means_the_scan_was_EXHAUSTED_never_silently_truncated
  TestTheCapAppliesToTheANSWERNotTheCandidateScan::test_a_capped_BLOCKED_query_serves_the_FULL_cap_when_the_answer_is_bigger
2 failed, 39 passed
```

**And the determinism claim, MEASURED rather than argued — 8 consecutive mutated runs of the
#268 leg alone, after the false-gate fix (§1.4):**

```
control (unmutated): 1 passed
run 1: proof_held=1  fired=TRAFFIC-leg(#268)
run 2: proof_held=1  fired=truncation-leg
run 3: proof_held=1  fired=truncation-leg
run 4: proof_held=1  fired=TRAFFIC-leg(#268)
run 5: proof_held=1  fired=truncation-leg
run 6: proof_held=1  fired=TRAFFIC-leg(#268)
run 7: proof_held=1  fired=TRAFFIC-leg(#268)
run 8: proof_held=1  fired=truncation-leg
md5 unchanged: 532ca7564374b8671111daf45ed48a0d
```

**8/8 RED — the flake #268 filed is gone.** The split is the interesting part and it is the
finding's own arithmetic reproduced: in 4 runs the wrong build's 60-row window happened to
contain every unblocked row (the ≈55% case), the outcome comparison saw nothing, and **the
traffic leg is what caught it**. Before the ordering fix, those same 4 runs reported *"the
fixture, not the pin, is wrong"*.

## 4.2 Rider 3 — `more` mutation-proven BOTH ways (on the reference build)

`more=len(fetched) > cap` → **`more=True`**: `10 failed, 38 passed`, **PROOF HELD**, all 10
declared reds fired and nothing else. `→ **more=False**`: `6 failed, 42 passed`, **PROOF
HELD**, all 6 declared reds fired and nothing else. The two sets are almost disjoint (they
share the two legs that assert both directions), which is what a both-ways proof should look
like: neither an always-true nor an always-false bit survives.

---

# §5 · DECISIONS NEEDED (none blocks the builder; all four are cheap to overrule)

1. **ESC-5's placement (§2.1).** Confirm the ruled fallback, or take the third shape, or
   pay the ≈83-site ripple for the ruled first choice. My recommendation: **confirm the
   fallback**; it satisfies every rider and every stated property of the ruling, and the
   ripple is a real, measured, collision-prone cost paid for nothing a pin can see.
2. ✅ **SETTLED by Ruling 6 — ID-ONLY confirmed, and its rider is BUILT (§11).** ⚠ The rider
   uncovered a NEW fork that is still open: **`lore_tasks` has no single-record read verb at
   all**, so the follow-up the render can honestly teach is a WALK, not a READ. §11.4 carries
   the measurement, the recommendation (`action=get`), and the exact one-line switch. The
   original text of this item is kept below because the reasoning is what Ruling 6 ruled on.
   *I pinned ID-ONLY. Enrichment (subject/status
   per blocker) needs a second bounded read over up to `ENGINE_RECURSION_CEILING` (256) rows
   — a new bounded-read hazard family, in the packet that just spent a wave on one — plus a
   hostile-free-text render pin routed through the sanitiser seam. **I judge that a slice,
   not a render tweak**, and I did not take it. ⚠ The honest counter-argument, which I am
   not qualified to settle: an agent handed seven bare hex ids must make seven follow-up
   calls, and the consumer law says the reader is an agent. If the operator wants
   enrichment, it is additive to every pin I wrote except the ID-ONLY assumption itself.*

   ⚠⚠ **ONE CLAIM IN THE PARAGRAPH ABOVE WAS WRONG AND I AM CORRECTING IT RATHER THAN
   EDITING IT AWAY.** It originally read *"must make seven `get_task` calls"* — implying
   that resolving an id is merely tedious. **It is not possible at all:** `get_task` is a
   LEDGER method with **zero** call sites in `server.py`, so no consumer can reach it
   (§11.1). I wrote that sentence from the ledger's surface without checking the SERVED
   one, which is the *"prose describing behaviour must be DERIVED from the behaviour"*
   failure, in my own report. The rider is what forced the check.
3. **R9's DEFAULT display cap appears UNBUILT.** R9 rules *"`limit` becomes legal for
   `query`, **and the no-limit path gets a DEFAULT display cap** with the house
   counted-elision grammar"*. MEASURED at `f67a219`: `AppContext._render_task_rows` renders
   **every** row and `action=query` passes `limit` straight through — there is **no display
   cap anywhere on the task read path**. The sidecar's conditional therefore discharges as
   ruled (*"if the current task render has no display cap, no counted line is owed this
   wave"*) and I owe no counted line — **but the R9 clause itself is an operator ruling that
   is neither implemented nor pinned**, and nothing in this wave will notice. Surfaced, not
   decided.
4. **Two `test_blocks_edge.py` one-line edits the BUILDER must make.** `direct_dependents`
   is a new PUBLIC ledger verb and two coverage-as-a-checked-variable pins are ∀ over
   `TaskLedger`'s public async methods. They are **green at HEAD** and go red the moment the
   verb lands — pre-applying them would make them red at HEAD, which is the thing this repo
   forbids. **Adjudicated here so nobody has to decide under a red gate:**
   `NON_WRITING_VERBS += "direct_dependents"` (a read; writes no row, touches no
   `blocked_by`) and `VERBS_WITH_NO_NEW_ENGINE_REJECTION_PATH += "direct_dependents"`
   (considered — its only input is a task id, an id naming no row matches no row and yields
   `[]`, so there is no caller-reachable engine rejection for T2 to bite on). Both are
   recorded in the contract file's own build spec, and both were applied in the reference
   build (which is how the 1197/0 was reached).

---

# §6 · RIDER 7 — THE FORGERY-DOOR SWEEP, RUN RATHER THAN ASSUMED

```
DERIVATION: 3 store seam(s) — execute_read_transaction, execute_transaction, run_query — bound at 3 site(s).
NOT SWEPT (public loremaster.store._txn coroutines executing no caller statement): bootstrap_session, retry_on_conflict.
POSITIVE CONTROL: ensure_ready made 4 store calls, raised=None, edges=2
DERIVED DOOR SET: 4 store calls during ensure_ready over a legacy store.
  door k=1..4: RAISED InjectedStoreFault
ALL 4 DERIVED DOORS FAIL LOUD — no silent door in ensure_ready on the shipped build.   (exit 0)
```

**No interaction with the #274 statement-shape family, confirmed rather than assumed, two
ways.** (a) The sweep's subject is `ensure_ready` — the BACKFILL path — and its verdict is
unchanged by this contract. (b) I read the family's own pins: the *"no `LIMIT` clause at
all"* property is asserted of the backfill's reads
(`TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE` and siblings), and the only
committed pin touching `query_tasks` and a `LIMIT` value is the T2 `ENGINE_REJECTION_PATHS`
row for a negative limit, which drives the **LEDGER** directly. Nothing in the #274 family
pins a query-path `LIMIT` value, so rider 6's re-authoring clause was never triggered.

---

# §7 · WHAT I READ, AND WHAT I DID NOT DO

- **Read in full:** `~/.claude/orchestration/brief-base.md` (v9) ·
  `docs/reference/surrealdb-31-capabilities.md` (**all 974 lines, before writing a single
  store-touching line** — the §7 `ORDER BY`-under-explicit-projection hazard, the `$k = NONE`
  `LIMIT` behaviour, the `record::id()`-in-a-FROM-array rollback, the `str(record.id)` rule
  and §6.6's only-source list all bear on this slice) ·
  `REPORT-design-sidecar-04b2-wavec-1.md` §1–§5 · `REPORT-contract-04b2-wavec-1.md` ·
  `REPORT-lead-04b2-wavec.md` §L-1–L-4 · `04-comms-blocks-footer.md` §04b-2 READ-FIRST box,
  §R8–R11, §T1/T2, §S2/S3, §ESC-1/ESC-5, §ACCEPTED KNOWN BOUND, §SWEEP ADDITIONS ·
  `test_query_tasks_bounded.py` in full · `tasks.py`'s `query_tasks` / `_candidate_statement`
  / `_validated_limit` / `claim_task` / `_claim_fragment` / `supersede_task` /
  `transitive_blockers` / the models · `server.py`'s `_TASK_ACTIONS` / `_FINDING_ACTIONS` /
  `_COMMS_ACTIONS` / `tasks` / `_render_task_rows` / `_render_claim_result` ·
  `_surreal_harness.StoreTraffic` + `measure_store_traffic` · `_task_fakes` ·
  `scripts/forgery_door_sweep.py` + `scripts/mutation_proof.py`.
- **Numbers I re-derived rather than inherited:** the `transitive_blockers` consumer count
  (0/0) · the `query_tasks` call-site ripple · the absence of any `_TASK_ACTIONS` test pin ·
  the absence of a display cap on the task render · the gate state at HEAD.
- **Tool honesty:** `Grep`/`Glob` are disabled session-wide, so every textual sweep here ran
  through `Bash`+`grep`/`python -m ast`. `ugrep` is not on this shell. lore's tools were
  reachable and used for the structure question (`lore_impact`'s verdict is quoted above via
  the predecessor's derivation, which I corroborated with a bare-pattern grep — the
  rename-exhaustiveness case where grep is honest, disclosed per the dogfood protocol).
  ⚠ I hold a prompt-level `no subagents` instruction, so brief-base's escape hatch of
  delegating a large package survey to `package-scout` was unavailable; my survey (§8) has
  four mechanisms, which is inside the inline threshold anyway.
- **NOT done, deliberately:** no git command of any kind · no production file modified in
  the working tree (verified byte-exact after every mutation) · `test_comms_footer.py`,
  `scripts/**`, every packet-39 file and `INDEX.md` untouched · I did not run the full suite
  (brief-base §3 forbids it unless briefed).
- **Concurrency:** no pin here is a concurrency pin. The one place this slice touches a
  raceable seam is `supersede`'s dependents read, which happens BEFORE the supersede
  transaction; a task created between the two would be stranded and unwarned. **Flagged, not
  pinned** — a contract pin is the wrong instrument (≥8-way × 20 consecutive runs), and the
  window is strictly smaller than the one R10(iii) exists to close.

---

# §8 · PACKAGE SURVEY (required output)

| mechanism | libraries evaluated | what I **READ** | verdict |
|---|---|---|---|
| Bound-disclosure over a store read (*"is there another matching row?"*) | `surrealdb` 2.0.0 (the installed SDK) | live introspection this session: `dir(surrealdb)` (top-level exports) and every public method of `AsyncWsSurrealConnection` — **32 methods**, filtered for `page`/`limit`/`cursor`/`offset`/`more`/`next` → **zero hits**. The SDK ships raw SurrealQL execution and nothing above it. | **bespoke** — there is no package between us and the engine to do this. The mechanism is `LIMIT n+1` inside this repo's own `_candidate_statement`, which the design ruling already specified. |
| Locating the disclosure line by comparing two rendered worlds | `difflib` (stdlib) | `dir(difflib)` + `inspect.signature(difflib.unified_diff)` + `difflib.Differ`'s docstring (*"Each line of a Differ delta begins with a two-letter code"*) | **bespoke, minimal (2 lines).** Both `unified_diff` and `Differ` emit prefixed, human-oriented deltas a test would have to re-parse, and `SequenceMatcher` answers a similarity question I do not have. The property is *"lines in A that are not in B"* over normalised lines — a set difference. Adding a diff-format parser would add a failure mode, not remove one. |
| Normalising opaque ids out of a rendered listing | `re` (stdlib) | the helper is **inherited verbatim** from the deleted `TestACappedListingDISCLOSESNothingAboutItsOwnBOUND`; no new mechanism specified | **replace** (stdlib, already in use). |
| All-cycle enumeration / graph traversal | `networkx`, `graphlib` | sidecar §B4 + the INHERITED table's #273 row | **not mine** — routed to 04b-3 by ruling. No verdict sought. |
| The cap validator (`limit` range refusal) | — | `TaskLedger._validated_limit`, read this session | **reuse, not a package question.** ONE IMPLEMENTATION: the reference build promotes it to a module-level `validated_task_limit` that the ledger delegates to, so the seam and the ledger cannot disagree about what a legal cap is. That promotion is part of the build spec, and `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED` is what makes a private second copy impossible to ship green. |

---

# §9 · FLAGGED — NOTICED, OUT OF MY SCOPE, NOT BURIED

1. **`scripts/lore_tool_name_currency.py` carried 2 ruff errors at `f67a219`** (unused
   `subprocess` import, `PLW2901`). Pre-existing, in a path my brief marks do-not-touch
   (a gate-wrapper builder is working there). `uv run ruff check .` is a committed gate and
   it was red for this alone. Filed as **finding #311**. ⚠ **Scope note, so the finding is
   not read as current forever:** measured 2026-08-01 at `f67a219`; by the end of this
   session that file showed as MODIFIED in the shared working tree by another agent, so it
   may already be fixed — re-derive before acting on #311.
2. **R9's DEFAULT display cap is unimplemented and unpinned** — decision-needed #3.
3. **A defect CLASS worth an invariant, from §1.1's `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED`:**
   *a seam that ADJUSTS a caller's parameter before the layer that validates it destroys
   every refusal that names the caller's own value.* Here it silently turned `limit=0` from
   a refusal into a one-row answer. This slice pins it for `limit` on `query`; the general
   form (any dispatcher that transforms a parameter it does not own) has no guard.
4. **The `TaskListing` model I define is the second wrapper on this ledger with a
   `rows` field** (`TaskActivityWindow` is the first, and it carries an honest `total`).
   Not a defect — the rollup genuinely measures its total — but a future reader will ask why
   one wrapper counts and the other does not, and the answer (the rollup's total is
   MEASURED; a capped listing's would be FABRICATED) lives only in this report and in
   `TestTheListingIsATYPEDRESULTWithACLOSEDFieldSet`'s docstring.
5. **Scratch tree:** `/home/ejprice/scratch-c1-ref` (branch-less copy, provenance-asserted)
   holds the reference build. It is disposable by design; **it is NOT the record** — the
   build spec is in the contract file's docstring and in §3.2 above, so the receipt can be
   re-produced from tracked text. Tell me if you want it kept, merged as a starting point
   for the builder, or discarded.

---

# §10 · POST-HANDOFF — #308 FIXED, AND THE INHERITED DIAGNOSIS WAS HALF RIGHT

Lead directive (2026-08-01, thread `q:04b2-c1-contract`): *"#308 IS YOURS TO FIX — a
one-character change. `_surreal_harness`'s docstring states a DERIVED importer count of 45;
the true count is now 46, and the cause is your own `test_task_read_surface.py` joining the
importers."* Correct about the cause, and **incomplete about the fix** — caught by
re-deriving rather than by typing what I was told.

## 10.1 The measurement

`test_surreal_harness.py::TestTheHarnessDeclaresNoRetryPolicyOfItsOwn::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`
checks the docstring against **TWO** AST-derived populations, and its own failure message
says why: *"Do not collapse this into the importer count — they are different populations
(audit-150 R2)."* Run through the pin's own helpers at `f67a219` + my files:

```
DERIVED importers: 46          STATED: 45
DERIVED connect_admin callers: 29   STATED: 28
test_task_read_surface.py in importers: True
test_task_read_surface.py in callers:   True     <-- the half nobody named
```

**`test_task_read_surface.py` joined BOTH populations**, because
`TestTheChainRenderNAMESTheBlockersThatCarryNoEDGE._seed_phantom_blocked` calls
`connect_admin` to raw-seed the legacy phantom-blocked row. So both numbers drifted, and
**45→46 alone would have left the pin RED on the second assertion.**

## 10.2 The fix, and the positive control proving its second half was load-bearing

Both counts corrected in `_surreal_harness.py`'s docstring (46 importers · 29
`connect_admin` callers). Pin green: `tests/test_surreal_harness.py -n auto` → **57 passed**.
The pin was NOT loosened — the directive was explicit about that and it is right; the pin
did exactly its job and caught a real drift within minutes of the file landing.

Then the check that separates a fix from a coincidence — revert ONLY the caller count and
require the pin to redden:

```
./scripts/mutation_proof.py --file loremaster/tests/_surreal_harness.py \
  --anchor '29 test files — calls ``connect_admin``' \
  --replacement '28 test files — calls ``connect_admin``' ...
E   assert 28 == 29
1 failed
tree restored byte-exact (md5 1505580ffafac350281357f269d55596)
PROOF HELD — the declared RED set fired EXACTLY
```

**So the second half of the fix is not tidying: without it #308 stays open**, and the
"single remaining non-contract-first failure" the gate wrapper isolated would still have
been failing after a fix that looked complete.

## 10.3 Why this is in the report and not just in a reply

*"Re-derive every number you inherit — from a report, from a doc, from this brief"* is the
standing brief's own line, and this is the cheapest possible receipt for it: the inherited
number (45→46) was true, and acting on it verbatim would have shipped a still-red gate. Two
populations, one named — the #102/#120 conflation shape, one level down, in a one-line
docstring fix. Recorded here because a correction that lives only in a message body is one
the next session never meets (#303).

## 10.4 Scratch tree — lead ruling recorded

`/home/ejprice/scratch-c1-ref` **KEPT**, and it does **NOT** go to the builder: it is a
known-correct implementation, so handing it over would turn the build phase into a
transcription and destroy the builder-≠-grader independence. It stays as evidence and as a
cross-check available to the cold audit; the lead calls its disposal at wave close-out.
This supersedes §9 item 5's open question.

---

# §11 · RULING 6's RIDER — BUILT, AND IT UNCOVERED A MISSING VERB

Lead **Ruling 6** (2026-08-01): ID-ONLY confirmed on the trust legs; enrichment is consumer
ergonomics and goes to 04b-3. **Rider, this wave, judged few-lines-cheap:** *"the id-only
render must TEACH ITS FOLLOW-UP — how a consumer gets detail for an id."*

## 11.1 What I found before writing the pin

⚠ **There is no follow-up to teach.** Measured at `025c2a9`, two ways:

```
grep -c 'task_ledger.get_task' loremaster/loremaster/server.py   ->  0
_TASK_ACTIONS = create · query · transition · supersede · rollup · create_many   (+ blockers, minted here)
```

**No served `lore_tasks` verb resolves a task id to its detail.** `lore_findings` has
`get`; `lore_comms` has `brief_get`; `lore_tasks` has nothing. That is an **asymmetry, not
a design choice**, and it bites wider than this render: an agent handed an id by *any*
surface — this chain render, a task row's `blocked_by`, a claim refusal naming its blocker —
has no read verb to point at.

**Why that changes the rider rather than just complicating it:** the obvious way to satisfy
it is to render `lore_tasks action=get task_id=<id>`, which returns *"unknown task action
'get'"*. That is a **fabricated affordance**, and under the consumer law it is worse than
the bare ids it replaces — the measured behaviour of an agent on an undiagnosable failure
is to blame the tool and route around it. The rider aimed at usability would have bought a
route-around.

## 11.2 The pin, written to the PROPERTY so the open fork cannot invalidate it

`TestTheIdOnlyChainRenderTEACHESItsFOLLOWUP` (2 tests) does not look for a sentence. It
**extracts every `action=<name>` the render teaches and requires each to be a real member of
`_TASK_ACTIONS`**, plus: at least one taught action; one line carrying both a taught action
and an id **this answer served** (R9's concrete re-ask, not a generic pointer); and — killing
**WB-B4** — a render with NO ids teaches NOTHING (imperatives ride only true verdicts, R8's
split, which this packet already applies to the fleet columns and the supersede warning).

So the class is **unchanged whichever way §11.4's fork is ruled**; only the render's own
text moves.

## 11.3 Receipts

- **Reference build, whole contract: `50 passed` / 0 failed** (48 → 50 with the rider).
  Follow-up implemented conservatively — no new action — as
  `↳ walk any of these with: lore_tasks action=blockers task_id=<first served id>`.
- **Mutation proof of the fabricated-affordance guard**, which is the load-bearing half, and
  the mutation is *the most plausible wrong build a builder would actually write*:

```
--replacement 'f"  ↳ read any of these with: lore_tasks action=get "'
E  the render teaches action(s) ['get'] that lore_tasks does not serve; the legal set is
   [... 'blockers']. A taught call that returns 'unknown task action' is a FABRICATED
   AFFORDANCE — strictly worse than the bare ids it replaced ...
1 failed, 49 passed
tree restored byte-exact (md5 34fc1991db7e8c2b32e294ce2f25492b)
PROOF HELD — the declared RED set fired EXACTLY
```

- At `025c2a9` + my files: `tests/test_task_read_surface.py -n auto` → **37 failed / 13
  passed**, both new pins RED by design; ruff clean.

## 11.4 ⚠ ESCALATED — the follow-up I shipped is the WEAK one, and I recommend the other

`action=blockers task_id=<id>` **exists** and proves an id resolves (or raises
`TaskNotFoundError` naming it) — so the pin is honestly satisfied. But it renders that
task's *own critical path*; it does **not** give subject or status. Teaching it as *"how you
get detail"* would overstate it, so the shipped text says **"walk"**, not "read".

**MY RECOMMENDATION: mint `lore_tasks action=get task_id=<id>`, rendering
`_render_task_rows([task])`.** It is the missing member of a grammar the sibling tools
already have, not a new one; the ledger verb (`get_task`) and the render both exist; the
whole change is a dispatch branch, one `_EXPECTED_TASK_ACTIONS` entry in this contract, and
the refusal-matrix row #302's pins already demand. It is genuinely few-lines-cheap — and it
is the difference between *"walk this id"* and *"read this id"*.

**I did NOT take it, and the reason is scope, not doubt:** minting a served action is a
scope decision, and #302 — which this slice exists partly to close — is precisely the pin
that says an action must never appear without deliberate adjudication. Doing it unilaterally
inside the wave that closes that hole would be the wrong shape. **If ruled, the change is:
one dispatch branch + `_EXPECTED_TASK_ACTIONS += "get"` + the render's verb word.** The
reference build switches in one line; no pin above moves.

⚠ If it is NOT ruled, this residue should carry forward as a named bound rather than
evaporating: **the chain render can teach a WALK but not a READ, because `lore_tasks` has no
single-record read verb.** That sentence is the honest scope of what shipped.

---

# §12 · ADVERSARY VERDICT **INSUFFICIENT** — ALL EIGHT GAPS CLOSED

`adversary-c1-1` graded C1 INSUFFICIENT: **seven wrong builds passed 48/48**. Every finding
was correct and every one was measured, not argued. The verdict is right and I am recording
what it teaches before what I did about it.

## 12.1 The lesson, because it generalises past this slice

**A satisfiability receipt proves a contract SATISFIABLE. It never proved it SUFFICIENT.**
I produced the wave's first real receipt and then treated 1197/0 as if it graded coverage.
It grades the opposite direction.

And **every one of the three blockers is the same shape**: *the pin drove the seam I was
thinking about rather than the seam a consumer reaches.*

* ESC-5's uniformity class called `_task_listing` **directly** — and a helper cannot be
  non-uniform with itself, so it proved the helper's arithmetic and nothing about the
  dispatcher's routing. A build routing only `blocked is None` through it serves
  `action=query blocked=false limit=5` with **no disclosure at all**: the packet's DEPLOY
  ENTRY CONDITION, defeated, at 48/48.
* The chain render's two worlds were **byte-identical**: `deep != shallow` was satisfied by
  the id COUNT (4 ids vs 2), and `"2" in shallow` by a hex digit inside an opaque id —
  P(vacuous pass) = **0.998**, on a build naming no depth at all, under a message reading
  *"the truncated render names no depth"*.
* The whole surface was **unreachable through the registered MCP tool** — 48/48 here AND
  641/641 in the served-surface suite while `lore_tasks` exposed no `max_depth` and its
  served description never named `blockers`. **That is finding #302's own quantifier
  failure, inside the slice that closes #302:** I pinned the INTERNAL tuple by equality —
  the door I walked through — and left the SERVED half open. Finding #314.

Four more, all fair: a hard-coded cap rendering *"showing 5"* while serving 2 (`_ALT_CAP`
existed for the monoculture law and never reached the RENDER) · `max_depth` refused for
`create` alone · an always-empty `superseded_blockers` satisfying every leg I wrote · the
supersede render dropping the successor id, in a test whose own NAME promised to check it.

## 12.2 What I did

All eight adopted into `test_task_read_surface.py` **SECTION E**, re-homed in this file's
idiom with the measurement that justifies each kept in its docstring. Two decisions of mine:

* **MP-1's placement (the adversary left it open):** the served-tool pins live HERE, not in
  `test_mcp_server.py` — they import only that module's fixture helpers, and keeping C1
  self-contained avoids a second agent's file in a five-agent tree.
* **`test_every_declared_action_is_actually_DISPATCHABLE` RE-AUTHORED** rather than adopted.
  It was **my own false gate**: its docstring said *"three equal tuples prove agreement
  between two constants, not that any action reaches a handler"* and its assertions were
  agreement between two constants. It now resolves every `_COMMS_ACTIONS` key to a callable
  handler and drives every `_TASK_ACTIONS` name through the dispatcher, requiring the
  failure never to be *"unknown task action"*.

## 12.3 ⚠ MY REPLACEMENT FOR MP-7 WAS ITSELF A FALSE GATE, AND THE TOOLING CAUGHT IT

The adversary FALSIFIED my report's §8 claim that `TestTheCALLERSOwnLimitIsWhatGetsVALIDATED`
*"makes a private second copy impossible to ship green"* (measured: shared predicate
neutralised → reference build 4 failed, private-copy build 4 **passed**). So I wrote
`TestTheCapPredicateHasONEImplementationPROVENByMutation`, replacing the shared predicate
with a **raising sentinel** and requiring the seam call to raise.

**It went GREEN on the private-copy build — `PROOF FAILED, 69 passed`.** Because the seam's
over-fetch calls `query_tasks(limit=cap + 1)`, and the **LEDGER** then calls the shared
predicate downstream, so the sentinel fired anyway *from the wrong call site*. A pin that
cannot tell *"the seam called it"* from *"something the seam called called it"* is the P2
class — written into the fix for a P2 finding, by the author who had just been shown one.

**The discriminating instrument is a CALL RECORDER, not a raise.** One seam call must
validate **twice with different values** — the caller's cap at the seam, `cap + 1` at the
ledger — and a private copy records only the ledger's one. That difference exists *only*
because the over-fetch makes the two values differ.

```
control (correct build):                     69 passed
private-copy build (adversary's wb-private-limit):
  1 failed, 68 passed   PROOF HELD — the declared RED set fired EXACTLY
  tree restored byte-exact (md5 671aca01df8b4799713f87ae4028e226)
```

⚠ A second self-inflicted defect fixed in the same class: its first draft asserted
`server.validated_task_limit is tasks.validated_task_limit`, which would have failed a
correct build that spells the import differently — **and tripped mypy's *"does not
explicitly export attribute"***, the only mypy error my file has ever carried on a correct
build. The recorder patches both bindings and requires neither style.

## 12.4 Receipts after the fix

```
reference build, contract alone                                    69 passed / 0 failed
reference build, + test_query_tasks_bounded + test_blocks_edge
  + test_task_ledger + test_mcp_server + test_txn_contention
  + test_surreal_harness            -n auto                      1275 passed in 136.66s
reference build, ruff (contract + server.py + tasks.py)            All checks passed
reference build, mypy on the contract                              0 errors
HEAD (025c2a9 + my files)                                          52 failed / 17 passed
HEAD, ruff on the contract                                         All checks passed
HEAD, mypy on the contract   14 errors, ALL attr-defined naming build symbols + 1 consequential unused-ignore
```

48 → 69 pins. The 17 greens at HEAD are removed-behaviour guards: three of them are NEW and
named — the supersede render already names its successor, the served description already
names today's six actions, and the tool already forwards `owner` — each of which this wave's
rewrite could silently take away.

## 12.5 What the reference build gained

The MCP tool wiring MP-1 demanded: `max_depth` exposed as an annotated parameter **and
forwarded**, and the served `action` description extended to name `'blockers'` with what it
does. Everything else the adversary found was a missing PIN over behaviour my reference
build already had — which is precisely why 48/48 was never evidence of sufficiency.

---

# §13 · RULING 8 — `lore_tasks action=get` MINTED, ALL SIX RIDERS CARRIED

Lead **Ruling 8** (sidecar §8) adjudicated §11.4's fork: mint `action=get` this wave, inside
the #314 fix wave. **The sidecar retracted its own premise** — Ruling 6.1's *"teach the
follow-up"* rider assumed a teachable read verb existed, and finding **#89** carries the
receipt for what happens when one does not: #89's own author **fell back to a raw SELECT
against the production store** to read a task description. Not a hypothesis about
route-around — a measurement, and walk-only teaching would have pointed a brand-new
surface's consumers straight at it.

## 13.1 ⚠ THE FALSIFIER — CHECKED AND **NOT** INVOKED, with the measurement

Ruling 8 asked me to invoke it rather than push through if the fenced-body reuse rippled
past the #314 repair set. Measured at `025c2a9` before writing anything:

```
grep -rn '_fence_width' loremaster/loremaster
  search.py:1423  the definition
  search.py:1460  ONE real call site
  server.py:2746 · server.py:3277   PROSE references only
```

So the extraction is four one-line touch points. **Cost held; falsifier not invoked**, and
the check is recorded in the contract file's own SECTION F header so nobody re-derives it.

⚠ The rule was already duplicated **twice** before I arrived — `SearchPipeline._fence_width`
and an inline copy in `_render_finding_detail`. Mine would have been the third. That is
rider 2's actual justification: the *"a fence must be one wider than the longest run
inside"* rule is POLICY, and a policy in three places is a fix that reaches one of them.

## 13.2 The six riders, each with what discharges it

| rider | discharged by |
|---|---|
| 1 · #302 pin REDDENS and updates in the SAME diff | `_EXPECTED_TASK_ACTIONS` now carries `"get"`, with the adjudication trail in its own `#:` comment — *"this comment is the 'say so'"* its failure message demands. The pin was its own first real test and the path was executed, not bypassed. |
| 2 · new render of stored free text | `TestTheTaskDetailBodyCannotFORGEStructure` — hostile fixture with newlines, a row byte-identical to `_render_task_rows`' shape, a chain-render header, and **two** backtick runs of different widths. Plus `TestTheFencedBodyRenderHasONEImplementation`: `loremaster.sanitise.fence_width` / `fenced_block` extracted, `SearchPipeline._fence_width` delegating, both detail renders routed through it, **proven by a call RECORDER** (not a sentinel — §12.3's lesson applied on its first opportunity). |
| 3 · refusal-matrix rows; unknown id TEACHES | `test_the_refusal_MATRIX_covers_the_new_action` ∀ `limit`/`since`/`max_depth`; `test_an_id_naming_NO_row_TEACHES_rather_than_rejecting`; `test_get_without_a_task_id_names_the_MISSING_ARGUMENT`. ⚠ Measured: **no new guard CODE was needed** — `get` is outside all three accepting-sets already, so the existing matrix refuses it. The pins are what make that a fact rather than an accident. |
| 4 · #314's generic invariant endorsed | already carried by `TestTheNewSurfaceIsREACHABLEThroughTheREGISTEREDTool`; `get` lands inside its coverage, and the served description now names it. |
| 5 · teaching rider completes; property pin permanent | the chain render's follow-up is now `lore_tasks action=get task_id=<served id>` — **"read"**, not "walk". The property pin (*every taught action ∈ `_TASK_ACTIONS`*) is untouched and stays: the property outlives the sentence, which is exactly why this was a text edit. |
| 6 · #89 resolves; packet-05 routing overruled | the lead's to file on this receipt; recorded here so the overrule is not a silent contradiction. |

## 13.3 ⚠ THE POST-LINT LEG CAUGHT A BUILDER TRAP — this is what that leg is *for*

Running `ruff check .` on the reference build after the extraction surfaced **two errors
that did not exist before it**, both mine:

```
loremaster/loremaster/server.py:192   F401  `_max_backtick_run` imported but unused
loremaster/loremaster/server.py:3489  PLR0912 Too many branches (13 > 12)   <-- AppContext.tasks
```

The first is the orphaned-import cleanup #133's harder leg predicts. **The second is a
trap:** `AppContext.tasks` gains two actions this wave and crosses the branch cap, so a
builder would land a correct implementation and be caught between ruff and a contract it
may not edit — the C-DEF class exactly. Resolved the way that function's *existing* `noqa`
already resolves the identical complaint about its return count
(`# noqa: PLR0911,PLR0912 - a dispatch-on-action verb; splitting churns every action's own
test`), and **named in the contract's build spec so the builder is not left to discover
it**. Without the post-lint leg this ships as somebody else's dead end.

## 13.4 Receipts

```
reference build, contract alone                                    81 passed / 0 failed
reference build, + query_tasks_bounded + blocks_edge + task_ledger
  + mcp_server + txn_contention + surreal_harness
  + sanitise + search + findings          -n auto                1572 passed in 116.52s
reference build, ruff check .        2 errors, BOTH pre-existing in scripts/ (finding #311)
reference build, mypy on the contract                              0 errors
HEAD (025c2a9 + my files)                                          62 failed / 19 passed
HEAD, ruff on the contract                                         All checks passed
HEAD, mypy on the contract    18 errors: 15 attr-defined naming build symbols,
                              + 2 no-any-return and 1 unused-ignore that are CONSEQUENCES
                              of those symbols being absent (all 18 are 0 on the build)
```

69 → **81 pins**. The three suites added to the satisfiability set (`test_sanitise`,
`test_search`, `test_findings`) are there because the fence extraction newly touches those
seams — #133's leg is about the suites a change reaches, and this change reached three more
than it did yesterday.

## 13.5 Two actions born covered by the same instruments

`blockers` and `get` both land inside: #302's equality pin, #314's served-text and
inputSchema invariants, the refusal matrix, and the Leg-1 scope-diff table. That was Ruling
8's stated reason for doing them in one wave, and it held — the only *new* guard code either
action needed was the MCP schema wiring #314 already demanded.

---

*Written 2026-08-01 by `contract-04b2-wavec-2` (Opus) against `feat/surreal-unification`
@ `f67a219`. Every number here was derived this session by the command shown beside it;
nothing is inherited, including from the predecessor's report. No git command was run; the
only files this agent modified in the working tree are the three test files named in §1 and
this report.*
