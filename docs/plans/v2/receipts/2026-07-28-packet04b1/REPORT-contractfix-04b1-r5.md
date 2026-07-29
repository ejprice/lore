# REPORT-contractfix-04b1-r5 — closing the FINAL ADVERSARY's findings against packet 04b-1's contract

brief-base v7 read

brief project v7 read

comms receipt: `lore_comms action=register agent=contractfix-04b1-r5 role=contract-author
session=pkt04b-20260728 model=claude-opus-5 task_id=e48347a9020945efb5725e16ae1e73c3` →
**registered, status active**; brief `project` v7 auto-acked by the register. `action=drain`
run at my turn boundaries (see §FRICTION for the one that timed out). **All lore tools were
reachable in my context** — ToolSearch resolved `lore_comms` / `lore_findings` / `lore_search`
/ `lore_get_symbol` / `lore_read` on the first call, so #264's shape did NOT recur here.

trust hard-definition read

Its two askable questions, quoted verbatim from `CLAUDE.md` § *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"*** (Leg 1 — SCOPE DIFF)

> **Ask: *"what broken state of this tool would serve exactly these bytes?"*** (Leg 2 —
> FORGERY PINS)

*Every claim in this file is scoped to branch `feat/surreal-unification` at HEAD **`bfea1f8`**,
measured **2026-07-28**. "RED at `bfea1f8`" means RED against that commit's PRODUCTION code
with this contract applied. Every live probe ran against spike-surreal `ws://127.0.0.1:18000`
(TEST); `:18500` was never touched. **Every number below was DERIVED by running**, including
numbers inherited from `REPORT-adversary-04b1-final.md` and `REPORT-contractfix-04b1-r4.md`.*

---

## SUMMARY BLOCK

- **state: done-with-deviations.** Worklist items 1–10 all dispositioned; 1 deviation, 3
  escalations, 1 finding filed.
- **Items 1–6, the six missing pins: ✅ ALL PINNED**, as **four new classes + one new leg**
  (§ITEMS-1-6). 1 self-loop mirrored · 2 superseded blocker still mirrored · 3 no skip
  recorded as a phantom when the row EXISTS · 4 the write path's rows-read does not grow ·
  5 the backfill is ONE transaction · 6 `transitive_blockers` agrees with the claim CAS.
  Both named monoculture axes closed: **CYCLE ARITY** (1 and ≥3, arity 2 deliberately not
  re-pinned) and **LEGACY-BLOCKER LIFECYCLE STATE**.
- **Item 7, SECTION L's `{empty}` instrument: ✅ RE-POINTED.** The parse-error leg became a
  4-mode parametrisation over shapes the fixed statement CAN take, and the mode the existence
  read can actually exhibit — direct record access on an ABSENT TABLE returning `OK []` — is
  now a PINNED KNOWN BOUND with a named re-open trigger. All five modes MEASURED live (§ITEM-7).
- **Item 8, the THIRD C-DEF: ✅ ALL FIVE RE-AUTHORED, not disclosed a third time.** A builder
  now meets **ZERO** red tests outside this contract. Measured: `test_mcp_server.py`
  **641 passed** at `bfea1f8` after my edits (§ITEM-8).
- **Item 9, the package verdict: ✅ CORRECTED to `replace`** — `graphlib.TopologicalSorter` is
  stdlib and does the job; the honest half is that **no pin requires it** (§ITEM-9).
- **Item 10, ESC-3's disclosure: ✅ STATED ACCURATELY** in both served-English class
  docstrings — *a docstring asserting the OPPOSITE passes this pin*. Not strengthened (§ITEM-10).
- **Pin counts, DERIVED by `--collect-only` on both files, never inherited: 215 → 232 (+17).**
  `test_blocks_edge.py` 175 → 192 · `test_query_tasks_bounded.py` 40 → 40.
- **DECLARED vs OBSERVED colour, diffed BOTH ways: 19 declared → 19 matched. 0 unexpected
  reds · 0 declared-reds that stayed GREEN · 0 declared-greens that went red.** Declared from
  `--collect-only` and written to disk BEFORE any run (§DECLARED). Contract at `bfea1f8`:
  **163 failed / 69 passed** (was 152/63).
- **SATISFIABILITY RECEIPT:** *(see §SAT — includes the post-`ruff --fix` leg)*
- **Gates (repo tree, unpiped, exits captured):** `./scripts/typecheck.sh` **MYPY_EXIT=0** ·
  `uv run ruff check .` **RUFF_EXIT=0** · neighbours **694 passed / 3 failed / 33 skipped**,
  the 3 being the DELIBERATE `test_enforced_relations.py` reddenings the contract declares.
- **`loremaster.__file__`** — see §SAT.
- **`Packages considered:`** the cycle detector → **`graphlib.TopologicalSorter` (STDLIB)**
  (READ: `/usr/lib/python3.14/graphlib.py`, `CycleError.__doc__`, and the adversary's six
  RUN graph shapes) → **`replace`**, corrected from `bespoke`, and pinned by NOTHING on
  purpose · the round-trip/rows instrument → the repo's own `_surreal_harness.measure_store_traffic`
  (READ: its docstring + `StoreTraffic.require_full_reach`) → **reuse, no new copy** · the
  degraded-state constructions → `pytest`'s `monkeypatch` + `caplog` (READ: this file's
  existing `_degrade_every_STORE_seam` / `conftest.py`'s caplog-propagation fixture) →
  **replace** · the legacy-cycle fixture → no library (domain data shapes) → **bespoke,
  minimal surface**.
- **decisions-needed: 3** — §ESC-A (I WEAKENED a committed pin's assertions in a file I own
  only for item 8) · §ESC-B (the `test_mcp_server.py` corpse sweep found a 4th prose site I
  did NOT touch) · §ESC-C (PROOF 10b/10d's declared sets are now prose+ids and one of them
  encodes a mutation's PLACEMENT).
- **Findings filed: #265** (a `lore_comms drain` timeout, §FRICTION).

---

## §DECLARED — declared vs observed, diffed BOTH ways

Node ids taken from `pytest --collect-only -q` (never transcribed from a run — *a "declared"
set read off the failures you just watched is the tautology in a new costume*), the colour
DERIVED by reasoning about what each pin needs, and both written to disk **before the first
run**. The diff was then done mechanically off a `--junit-xml`, both directions.

```
declared=19  matched=19
NOT FOUND:            (none)
MISMATCH (node, declared, observed):   (none)
total failed: 163 passed: 69
```

11 declared RED, 8 declared GREEN, all 19 observed as declared.

**And the reasons were checked, not just the colours** — a pin that is RED because of a typo
looks exactly like a pin that is RED because the feature is missing. Every one of the 11 fails
on either `NotFoundError: The table 'blocks' does not exist` (the edge table this packet adds)
or `AssertionError: TaskLedger.transitive_blockers does not exist` (the read this packet
owes). The two `…is_RECORDED_never_silent` legs get all the way to their own assertion and
fail on it, naming the unnamed members — so their fixtures demonstrably construct.

⚠ **ONE DECLARED GREEN IS THE INTERESTING ONE**, and its colour was DERIVED rather than
assumed (wave r4's DEVIATION-1 is the receipt for why that matters):
`TestCreateRefusesToFormACycle::test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_size_of_the_LEDGER`
is **GREEN at `bfea1f8` and GREEN after**. At `bfea1f8` the ledger's `create_many` performs no
persisted-id walk at all — the only cycle check in the tree is `server.py`'s batch-local one —
so there is no read to grow. It is a guard on a hazard the FIX INTRODUCES, which is the
delete/replace law's dual: *tests written for a NEW design certify only the new world*. Its
docstring says so.

---

## §ITEMS-1-6 — the six missing pins

All four new classes live in SECTION K of `test_blocks_edge.py` except the write-path leg,
which belongs to `TestCreateRefusesToFormACycle` in SECTION E because the read it measures is
that guard's.

### 1 + the CYCLE ARITY axis — `TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED`

Six legs: `MINTED_as_an_EXACT_edge_set`, `RECORDED_never_silent` and
`TRAVERSAL_TERMINATES_over_a_backfilled_cycle`, each parametrised over
`LEGACY_CYCLE_ARITIES = (1, 3)`.

- **Arity 2 is deliberately NOT repeated.** It is `TestALEGACYCycleIsMINTEDAndRECORDED`'s, and
  a second copy of a pin is copy #2 of a served-surface guard (repo law #102). The new class's
  docstring says so; so does the constant's.
- **The mint leg is an EXACT SET**, for `_expected_backfilled_pairs`' reason: a superset passes
  a membership check while breaking the mirror, and a subset is the skip being hunted. At arity
  1 the expected set is the single self-edge `(x, x)`.
- **The record leg asserts over the UNION of the WARNING records**, not that ONE record names
  every member — a build logging per repaired ROW and a build logging per detected CYCLE are
  both legitimate, and demanding a single all-naming record would fail the first for a reason
  no ruling carries. That weakening is stated in the leg's own docstring rather than left for a
  reader to discover.
- **The termination leg keeps the sibling's stated bound verbatim**: it asserts the read
  RETURNS, that it DEDUPLICATES, and (for arity > 1) that it reaches every OTHER member. It
  asserts nothing about `truncated` over a cyclic walk and nothing about whether the starting
  row appears in its own reach — neither is ruled, and pinning an unruled value is the C-DEF
  risk ESC-4 was escalated to avoid.

### 2 + 3 + the LIFECYCLE-STATE axis — `TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask`

Two legs. The construction runs the real verbs (`create_task` → `supersede_task`) so nothing
re-implements the `superseded_by` stamp, raw-seeds the waiter, then `DELETE`s the edge table
back to the production-real partial world. It fails CLOSED twice before yielding: the blocker
really is superseded, and the store really holds no edges.

- **`…_is_STILL_MIRRORED`** asserts the EXACT set `{(blocker, waiter)}`.
- **`test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS`** asserts no WARNING record
  carries both `phantom` and the blocker's id. Its POSITIVE control is its neighbour
  `TestThePHANTOMBlockerIsSKIPPEDAndRECORDED::test_the_phantom_SKIP_is_RECORDED_never_silent`,
  which proves a GENUINE phantom IS recorded — cited rather than duplicated, and the citation
  is in the docstring so the anti-vacuity argument travels with the pin.

**Why this is the most important pin in the wave, in one sentence:** R10(ii) refuses a
superseded blocker at WRITE time and R11 mirrors the column at MIGRATION time; both are
correct, and the one-line composition of them (`resolved = resolved - superseded`) drops a
dependency that ALREADY EXISTS — the case R10(iii) names verbatim — and restores S3's false
clear with the whole contract green.

### 6 — `TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS`, the ∀-over-outcomes pin

The property: **no row may be SERVED as having nothing upstream while the claim CAS holds it
blocked.** Five shapes, forced individually rather than sampled: no blockers · blocked on a
LIVE OPEN task · blocked on a LIVE DONE task · blocked on a SUPERSEDED task · blocked on
ITSELF. Traversals are read FIRST (the claim is destructive), verdicts recorded per shape.

Four anti-vacuity assertions, each closing a different way the pin could pass for a fixture
reason: at least one shape produces the confident empty (else the implication is vacuous), not
ALL do (else a constant-answering build passes), and the claim gate is exercised in BOTH
directions.

⚠ **THE QUANTIFIER IS BOUNDED, AND THE BOUND IS ASSERTED RATHER THAN ASSUMED.** The ∀ runs over
rows whose `blocked_by` names only LIVE task rows, and the pin PROVES that of its own fixture
(`record_exists` per entry) instead of relying on the author's belief. The excluded case — a
PHANTOM entry, the one difference R11's backfill cannot delete — gets its own leg,
`test_KNOWN_BOUND_a_PHANTOM_blocker_is_the_ONE_row_the_traversal_CANNOT_see`, which asserts the
exception (`ids=[] truncated=False` AND the CAS refuses) with a named re-open trigger and the
instruction to delete the pin and widen the ∀ if the residue is ever closed. Excluding it
silently would have been the quantifier defect this class exists to close, one level up.

### 5 — `TestTheBackfillIsONETransaction`

A GROWTH comparison on ROUND TRIPS: a boot that back-fills 2 legacy edges against one that
back-fills 30, through `measure_store_traffic`. Three guards: the two boots really minted 2 and
30 edges (else the comparison is between two different amounts of work, and *"the count did not
grow"* is trivially true of a backfill that mints nothing), the instrument saw traffic at all,
and only then the equality.

⚠ **STATED BOUND, in the class docstring:** round trips are a NECESSARY condition for one
transaction and are the property WB-C violates; the ROLLBACK itself is measured on the ENGINE by
`TestTheNakedBackfillWouldRollTheMigrationBack`, and the two together are what make R11's
rationale true rather than assumed. A statement-TEXT pin was deliberately not written —
`TestTheTwoReadsShareONESnapshot` already records why (*"a pin demanding the literal token
`BEGIN` would redden a build that composes the same guarantee differently"*).

### 4 — `test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_size_of_the_LEDGER`

`create_many` (not `create_task`) naming ONE existing blocker, measured against ledgers of 5 and
60 unrelated tasks. The choice of verb is load-bearing and is stated in the helper's docstring:
a `create_task` id is a fresh `uuid4` no caller has seen, so a build may legitimately skip the
persisted-cycle walk on that path and the measurement would observe nothing.

This is the pin whose absence let #253's own defect return on the write path: its sibling
measures ROUND TRIPS and says in its own docstring *"rows are deliberately NOT asserted"*
(correct for its question — depth — and blind to this one), and
`TestTheReadIsBOUNDEDByTheCallersFilter` measures `query_tasks` only.

---

## §ITEM-7 — SECTION L's `{empty}` instrument, re-pointed and MEASURED

**The gap, restated in one line:** the pin promised *"a REJECTED read RAISES"* and demonstrated
*"a malformed statement raises"* — and a malformed statement is the ONE failure a FIXED
statement string can never take, because the existence policy's statement is a literal
(`SELECT id FROM $ids`, `agent_existence`). The message named a general property; the assertion
demonstrated the unreachable mode of it.

**MEASURED 2026-07-28 through `TaskLedger._query` on spike-surreal 3.2.1** (my own probe, not
inherited):

| mode | through `TaskLedger._query` |
|---|---|
| malformed statement | **RAISE** `SurrealStoreError` |
| unknown function (`no::such::function`) | **RAISE** `SurrealStoreError` |
| absent table, SCANNED | **RAISE** `SurrealStoreError` |
| `TIMEOUT 1ns` on a plain SELECT | **RAISE** `SurrealStoreError` |
| direct record access, ABSENT ROW | `OK []` |
| direct record access, PRESENT ROW | `OK [{'id': …}]` |
| **direct record access, ABSENT TABLE** | **`OK []`** ← the bound |

What changed:

1. The rejection leg is now parametrised over `_ENGINE_REJECTION_MODES` — four DIFFERENT
   reasons the engine refuses, so a seam that raised for one and returned for another cannot
   pass by picking the convenient mode. The TIMEOUT mode is the one that matters most: it is
   the mode a deep traversal can actually take.
2. A new POSITIVE CONTROL, `test_POSITIVE_CONTROL_the_EXISTENCE_READS_OWN_SHAPE_answers_at_all`,
   drives the shape the policy actually issues and proves it resolves the id that exists and
   drops the one that does not. Without it the bound leg's empty answer is indistinguishable
   from a shape that reads nothing.
3. `test_KNOWN_BOUND_the_EXISTENCE_SHAPE_on_an_ABSENT_TABLE_returns_EMPTY_not_a_RAISE` pins the
   hole: a table SCAN of an absent table is rejected, **direct record access over the same
   absent table is not**. So the class's claim is bounded to *"the table exists"*, which the
   migration path guarantees because `ensure_ready` applies the DDL before anything reads.
4. The class docstring now states what it ESTABLISHES, what it used to measure and why that was
   the wrong mode, the bound as a FACT, and the adversary's re-open trigger: **the first
   degraded state in which the shared existence probe returns a PARTIAL set.**

**I CONCUR with SECTION L's verdict**, on my own measurement rather than on the adversary's: no
mode I constructed produced identical bytes between a healthy and a degraded world at this
seam. The claim held; only the instrument was narrow.

---

## §ITEM-8 — the THIRD C-DEF: all five RE-AUTHORED, and why not disclosed

The adversary measured five pins in `test_mcp_server.py` that a CORRECT build breaks, of which
the contract disclosed two. **Disclosing all five would have been the third instance of the same
move, and it moves the defect rather than removing it**: a builder that may not edit tests is
handed a list of red tests to edit. So all five are re-authored to pin only what survives the
ruling that retired their old assertion, and each is **GREEN before the fix and after**.

| # | pin | what it used to assert | what it asserts now |
|---|---|---|---|
| 1 | `test_since_on_a_non_rollup_action_is_rejected` | the refusal BY VALUE, `"'since'/'limit' apply only to action='rollup' — omit them for 'query'"` | it raises `ValueError` and the message NAMES `since` |
| 2 | `test_limit_on_a_non_rollup_action_is_rejected` → **renamed** `…_non_query_non_rollup_…` | `limit` on `query` is refused — **R9 rules the opposite** | `limit` on `create` is refused, naming both `limit` and `create` |
| 3 | `test_intra_batch_cycle_is_refused_with_the_exact_text` → **renamed** `…_and_NAMES_every_member` | `pytest.raises(ValueError)` + the sentence by value | it raises, and the message NAMES every member of the cycle |
| 4 | `TestTasksTool::test_tasks_query_renders_summarised_rows_not_raw` | — (broke on `TypeError`) | unchanged; fixed at the DOUBLE |
| 5 | `TestTasksTool::test_superseded_task_renders_a_chain_marker_not_bare_status` | — (broke on `TypeError`) | unchanged; fixed at the DOUBLE |

**#4/#5 are a fix to `_task_fakes.FakeTaskLedger.query_tasks`, which now takes `limit`.** That is
the ripple ESC-1 reasoned about *for the wrong method* — its own words are *"it retypes a method
five test doubles implement"*, said of `ensure_ready`; R5 does exactly that to `query_tasks` and
nobody surveyed it. The fake slices **LAST**, after the `blocked` partition, per ruling T1 (*the
cap applies to the ANSWER, not the candidate scan*) — a double that sliced earlier would teach
its consumers the wrong contract, which is the one thing a double must never do.

**The assertions were chosen so that any build satisfying the contract satisfies them by
construction.** #1's `"since" in message` is exactly what
`TestLimitIsLEGALForQueryAtTheToolSeam::test_SINCE_on_action_QUERY_is_STILL_REFUSED…` requires;
#2's `"limit" in message and "create" in message` is exactly what
`test_limit_on_a_NON_query_NON_rollup_action_is_STILL_REFUSED` requires of the same call; #3's
"names every member" is exactly what
`TestTheCyclePolicyHasONEImplementation::test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS`
requires.

**MEASURED at `bfea1f8` with my edits applied: `test_mcp_server.py` → 641 passed.** (The
adversary measured 5 failed / 636 passed on a correct build; the same 641 tests.)

Three stale disclosures in `test_query_tasks_bounded.py` — the module docstring, the R5 class
and the R9 class — were corrected in the same pass; each said *"a builder who does not make
them meets red tests it may not edit"*, which is no longer true. `test_blocks_edge.py`'s
RED-BY-DESIGN section gained the corresponding note.

⚠ **See §ESC-A: #1 and #3 are WEAKER than they were, and that is a scope call I made, not one
I was given.**

---

## §ITEM-9 — the package verdict, corrected honestly

The contract's verdict lived in `TestCreateRefusesToFormACycle`'s docstring and read
`bespoke`, *"a DFS over the column, nothing more"*. **Its read-column evaluated no library.**
That is precisely the shape `brief-base.md` names as the defect the `Packages considered:` line
exists to catch — *asserting a package limitation without reading the API* — and it is worth
saying plainly that the sentence was a CORRECTION of an earlier wrong verdict, i.e. **a
correction is a specification too, and it needs the same evidence as the thing it corrects.**

The docstring now carries v3: **`replace`**, `graphlib.TopologicalSorter`, STDLIB, with the six
RUN graph shapes that establish it — `['a','b','a']` for a 2-cycle, **`['x','x']` for a
self-loop** (byte-for-byte the format `AppContext._find_key_cycle`'s own docstring already
promises), `['a','c','b','a']` for a 3-cycle, `None` for an acyclic diamond, and — the property
that actually decides it — a dependency naming an id OUTSIDE the graph is TOLERATED, which is
exactly what a `blocked_by` entry pointing outside the read needs.

⚠ **AND THE HONEST HALF, which is the part I would want a reader to take:** **no pin requires
it**, deliberately. Every cycle pin in the file is behavioural — which graphs are refused, which
accepted, whether ONE implementation is shared (proved by MUTATION). A contract that named a
library would be forbidding a better answer than its author imagined. What the rule asks is that
the CHOICE be made against a READ API; if a builder still hand-rolls, its report owes what it
read and why the stdlib did not fit. R6 stands either way: one implementation, shared.

---

## §ITEM-10 — ESC-3's disclosure, stated accurately

Ruled: accept the bound (reading (i)), **but the disclosure must state the REAL failure mode**;
reading (ii), a phrase-level assertion, was REJECTED as inventing a requirement no ruling
carries and as a C-DEF risk. Both served-English docstrings now say, explicitly:

> a docstring asserting the **OPPOSITE** of the property **passes this pin**

— with the measured inverting docstring quoted, the reason the old wording (*"present, not
true"*) understated it (a reader infers the failure mode is SILENCE when it is INVERSION), the
rejected reading recorded so it is not re-litigated, and a pointer to what makes the words TRUE
(SECTION K's exact-set backfill pin / `TestTheTransitiveBlockerRead`'s closure legs). No
assertion changed — this is *when you cannot close a hole, PIN it* applied to a hole we are
keeping deliberately.

---

## §PROOFS — the mutation-proof blocks, re-derived against the new classes

A declared set that predates a class is a declared set with a hole, in the direction the
both-ways diff exists to catch. So every existing PROOF 10x block was re-derived, and four new
blocks were added for the wrong builds the adversary MEASURED surviving:

| proof | mutation | declared RED | must stay GREEN (and why) |
|---|---|---|---|
| **10a** (widened) | delete the backfill | 9 → **18** | 3 more, each named with its reason — the arity-1 termination leg (vacuous reach at arity 1), the superseded skip-log leg (asserts an ABSENCE), the phantom known-bound leg (the backfill cannot close it) |
| **10b** (widened) | naked backfill | + both legs of the agreement class (the only new fixture carrying a phantom) | the arity/superseded/one-transaction fixtures are phantom-FREE, so their migration does not roll back |
| **10c** (widened) | silent skip | 1 | + the superseded skip-log leg (opposite error) |
| **10d** (widened) | refuse cycles | 3 → **9** | the acyclic fixtures + the arity-1 termination leg |
| **10e** NEW | **WB-A**: `if blocker == task_id: continue` | 2 | BOTH arity-3 legs — a 3-cycle has no self-pair, and that asymmetry proves the arities discriminate different doors |
| **10f** NEW | **WB-B**: subtract superseded from the resolved set, BEFORE the skip record | 3 | every other class — no other fixture holds a superseded row |
| **10g** NEW | **WB-C**: one write per fragment | 1 | EVERY edge-set pin: the edges still LAND, which is the whole point |
| **11** NEW | **WB-D**: drop the guard's dependency-bearing filter | 1 | the round-trip pin — it cannot see a rows defect, which is why the rows pin had to exist |

New letters are **U/V/W/Z**, chosen because A–T are already bound in that comment block; a
reused letter silently re-points every proof that already used it, and the block now says so.

---

## §SAT — SATISFIABILITY RECEIPT

*(This section is the acceptance gate. It is filled from a reference implementation built in a
provenance-asserted scratch copy that never touched the tests.)*

<!-- SAT-PLACEHOLDER -->

---

## §FRICTION

**#265 filed** — `lore_comms action=drain` returned *"The operation timed out"* once, under
heavy concurrent load, then succeeded on an immediate retry with `limit=10` and again later with
no `limit` at all (so it is a TRANSIENT, not a limit-dependent failure — the second success
disproves the tempting reading). Filed rather than routed around silently because a timeout is
the one drain outcome an agent cannot distinguish from *"there was nothing for me"*, and the
durable pull channel is the only reliable one. Not a duplicate of #55 or #264 — both of those
are tool AVAILABILITY; here the tool was present and working before and after, and the CALL
failed.

**No grep fallback to declare for a code-structure question** in the sense brief-base §4 means:
every lookup I made was either an exact-span read of a file already named in my brief, or a BARE
anchor-free corpse sweep — the one case the repo's own dogfood protocol names as grep's, not
lore's (*"non-symbol textual seams … prose in string literals"*).

---

## §ESCALATIONS

### §ESC-A — I WEAKENED two committed pins, and that is a scope decision, not a mechanical fix

My brief grants `test_mcp_server.py` for item 8 and says *"re-author or disclose all five"*.
Re-authoring #1 and #3 necessarily made them **weaker**, and a reader should meet that as a
decision rather than discover it:

- **#3** lost `pytest.raises(ValueError)` and the byte-exact sentence
  (`"create_many items contain a blocked_by cycle among batch keys: …"` /
  `" — a cyclic batch can never be claimed; break the cycle"` / `"a -> b -> a"`). It keeps
  *"names every member"*.
- **#1** lost the byte-exact refusal sentence. It keeps *"names `since`"*.

**Two readings.** (i) This is correct: R6 unifies the cycle refusal through a shared formatter
whose skeleton is the BUILDER's to spell (R6 explicitly permits the two vocabularies to differ),
and R9 splits the strict-parameter sentence — so both byte-exact assertions pin a spelling **no
ruling carries**, which is the C-DEF class this packet has hit three times. The strong forms
live in the contract, against a REAL ledger, where they can be derived rather than typed.
(ii) The old sentences are SERVED SURFACES that agents have learned, and preserving them is a
removed-behaviour-inventory item (`preserved-with-pin`) that R6/R9 never adjudicated — in which
case the right move is a RULING that the batch-key sentence is preserved, and the byte-exact pin
belongs in the CONTRACT (where a builder can be held to it) rather than being deleted.

**I picked (i)** — a contract must not forbid a spelling no ruling requires, and (ii) is
recoverable in one edit while a C-DEF costs a builder a wave. **But (ii) is a real question and
it is the operator's, not mine: does the `create_many` batch-key refusal sentence survive R6
byte-for-byte?** If it does, that belongs in the contract as a value pin and I will add it.

### §ESC-B — a 4th `test_mcp_server.py` prose site the corpse sweep found, NOT touched

`test_mcp_server.py` also holds `test_naive_since_is_a_teaching_value_error` and
`test_unparseable_since_is_a_teaching_value_error`, both asserting `since` refusals BY VALUE.
Those sentences are about `action='rollup'`'s own `since` parsing and R9 does not touch them, so
a correct build leaves them GREEN — **which is why I left them alone**. Recording it because
"I checked and deliberately did not change it" and "I did not look" are indistinguishable in a
diff, and the repo's own law bans *"all remaining hits are X"*. Verdict: **not a corpse.**

### §ESC-C — PROOF 10f's declared set encodes the mutation's PLACEMENT

PROOF 10f (WB-B) declares 3 reds, and the third — the skip-log-honesty leg — reddens **only if
the superseded subtraction sits BEFORE the skip record**. I wrote the placement into the
mutation instruction rather than leaving the declared set to depend on a choice the runner makes
(*a declared set that does not say which variant it was written against is a prediction nobody
can reproduce*). **Fork for the lead:** either keep it as written (a fully-specified mutation,
3 reds) or split it into 10f-i/10f-ii for both placements. **I recommend keeping it** — the
second placement adds no discrimination the first does not already give.

Also inherited and NOT re-litigated: PROOF 10b's declared set is still PROSE (*"every leg of
$K, $L and $M"*) rather than node ids, which is how it was written. My additions to it are node
ids. That inconsistency is pre-existing; converting the whole block is a bigger edit than my
worklist carries.

---

## §RESIDUALS — every item, its own line, its own verdict

| # | item | verdict |
|---|---|---|
| R-1 | adversary MISSING PIN 1 (legacy SELF-loop mirrored) | ✅ **CLOSED** — `TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED`, arity 1, EXACT-set |
| R-2 | adversary MISSING PIN 2 (`…SELF_LOOP_row_does_not_serve_a_CONFIDENT_EMPTY`) | ✅ **CLOSED, BY THE ∀ INSTEAD OF BY ITS OWN LEG** — the self-loop is one of the five shapes in `TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS`, which is the same discrimination as the outcome property rather than a second copy of it (the adversary itself said pin 6 is the one to write first) |
| R-3 | adversary MISSING PIN 3 (superseded blocker mirrored) | ✅ **CLOSED** — `TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask`, EXACT-set |
| R-4 | adversary MISSING PIN 4 (no false phantom record) | ✅ **CLOSED** — same class, second leg, positive control cited not cloned |
| R-5 | adversary MISSING PIN 5 (write-path rows-read) | ✅ **CLOSED** — `TestCreateRefusesToFormACycle`, GREEN today by measurement |
| R-6 | adversary MISSING PIN 6 (traversal ∀ CAS) | ✅ **CLOSED** — with its excluded case pinned as a KNOWN BOUND rather than silently narrowed |
| R-7 | adversary MISSING PIN 7 (backfill is ONE transaction) | ✅ **CLOSED** — round-trip growth, with the bound on what round trips prove stated in the class |
| R-8 | CYCLE ARITY monoculture | ✅ **CLOSED** for arities 1 and 3; arity 2 stays with its own class |
| R-9 | LEGACY-BLOCKER LIFECYCLE monoculture | ✅ **CLOSED** for `superseded`. ⚠ **NOT closed for `done`/`wontfix` BLOCKERS in the backfill fixture** — `legacy_column_store` holds a terminal-status TASK (`LEGACY_TERMINAL_TASK`) but no terminal-status BLOCKER. I judged it low-value (the backfill mirrors a column and cannot see status) and did not add it. **Flagged, not silently dropped** |
| R-10 | §SECL's `{empty}` instrument | ✅ **CLOSED** — 4 modes measured, the real shape's bound pinned |
| R-11 | §CDEF's five pins | ✅ **CLOSED by RE-AUTHORING**, not by a third disclosure. See §ESC-A for the cost |
| R-12 | §PKG's cycle-detector verdict | ✅ **CORRECTED to `replace`**, with the honest "no pin requires it" half |
| R-13 | §ESCALATION-3's disclosure | ✅ **CLOSED** — both docstrings state the INVERSION failure mode |
| R-14 | adversary §ESCALATION-2 (`_txn.py`) | ✅ **RULED to the BUILDER** by the lead at `bfea1f8`; nothing owed by me, and I did not touch `_txn.py` |
| R-15 | adversary R-4: `tasks.py:182` / `:739` describe the pre-T5 CAS | 🟡 **STILL OPEN, PRODUCTION PROSE** — outside my writable set. The builder must update both when `array::distinct` lands (#219's class). Cite by SYMBOL: the module comment above `TaskLedger`'s status constants, and `_claim_fragment`'s docstring |
| R-16 | adversary R-8: the SUPERSEDED refusal is a THIRD served sentence with no ONE-IMPLEMENTATION pin | 🟡 **NOT TAKEN.** Outside my worklist; low risk (its clause is pinned BY VALUE via `_served_superseded_clause`), but the sharing law is genuinely not applied to it. A one-line mutation leg would close it |
| R-17 | adversary R-9: the cycle mutation pin patches the DETECTOR in both namespaces and the FORMATTER in only one | 🟡 **NOT TAKEN.** A real asymmetry with a real cost (it forces `server.py` to reach the formatter through the module, and a builder's first attempt fails for that binding reason with no sentence explaining it). One docstring line would fix it; it is outside my worklist and I did not want to touch a mutation pin whose declared sets are inherited |
| R-18 | adversary R-11 / R-12 (engine oddities: `blocked_by > 3` matches everything; `1/0` yields `nan` with OK) | 🟡 **UNTOUCHED** — no pin depends on either, and neither is reachable through the typed tool seam today. They remain as the adversary left them |
| R-19 | adversary R-14: PROOFS 3/4/5's executed receipts not re-run | 🟡 **NOT RE-RUN by me either.** They mutate pre-build clauses; my tree carries no build. Declared, not silently skipped |
| R-20 | the FULL suite | 🟡 **NOT RUN** (brief-base §3): the two contract files + `test_mcp_server.py` + the 5 neighbouring suites named above |
| R-21 | git state | ✅ **UNTOUCHED.** No `add`/`commit`/`stash`/`checkout`/`rebase` by me; HEAD is still `bfea1f8` |
| R-22 | scratch tree disposition | 🟡 **YOUR CALL** — `/home/ejprice/scratch/cfix04b1r5-ref` holds the reference build. I read none of the three forbidden trees |
| R-23 | `_surreal_harness.py` was in my writable set and I did not touch it | ✅ **DELIBERATE** — `measure_store_traffic` already does everything the new pins need, including counting inside a transaction. No new instrument was warranted (repo law #102) |
| R-24 | `test_enforced_relations.py` / `_enforced_relations_scaffold.py` were in my writable set and I did not touch them | ✅ **DELIBERATE** — the only thing I needed from the scaffold was `MIGRATION_DIM`, which already exists and is now imported |
