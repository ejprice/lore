# REPORT-contractfix-04b1 — closing the findings against packet 04b-1's contract

brief-base v7 read

*Every claim in this file is scoped to branch `feat/surreal-unification`, measured
**2026-07-28** against HEAD **`faf035d`** plus this wave's uncommitted test edits. "RED
today" means RED at `faf035d` + this contract. All live probes ran against spike-surreal
`ws://127.0.0.1:18000` (TEST); `:18500` was never touched. Every number below was
re-derived here, including numbers inherited from `REPORT-adversary-04b1.md` and
`REPORT-contract-04b1-253.md`.*

---

## SUMMARY BLOCK

- **state: done-with-deviations.** Every worklist item dispositioned below; three
  deviations and five escalations, all prominent.
- **Deviation 1 — I edited `test_surreal_harness.py` (outside my writable set).** E-C's
  move puts a new module-level name in `_surreal_harness.py`, which that file's
  ALLOWLIST pin (`_ALLOWED_MODULE_LEVEL_NAMES`) reddens by design. Two lines added; the
  pin's own failure message asks for exactly this ("add it here in a diff a reviewer can
  see"). Brief-base §2's directly-caused-regression exception. §E-C.
- **Deviation 2 — I fixed a PRE-EXISTING RED in `_surreal_harness.py`'s docstring**
  (43→45 importers, 26→28 `connect_admin` callers). RED at `faf035d` before I touched
  anything (proved by `git stash`); caused by the two 04b-1 contract commits, neither of
  which re-derived the counts. §DEV-2.
- **Deviation 3 — I replaced adversary MP-4's proposed persisted-cycle TOOL-SEAM pin**
  with a KNOWN-BOUND pin: that shape is UNREACHABLE through `lore_tasks` (the dispatcher
  pre-mints every id), measured. Pinning it would have shipped a second C-DEF. §MP-4.
- **`Packages considered:`** cycle detection over the `blocked_by` column → SurrealDB
  `@.{n..m+collect}` self-reach (read: adversary §MP-4a + the contract's own
  persisted-cycle fixture, which is *forced* into a column-only write by `ENFORCED`) →
  **bespoke, minimal surface** (a DFS over the column; the closure READ stays on the
  engine — `replace`) · multi-statement READ transaction → `loremaster.store._txn`
  (read: `execute_transaction`'s `-> None` signature + store reference §3's
  `query_raw` ruling) → **extend the shared seam, never a hand-rolled `query_raw`**
  (a hand-rolled one FAILS the repo's runtime SDK-escape guard — measured, §ESC-4) ·
  rows/round-trip instrument → `test_brief_ledger`'s two query-COUNT instruments (read:
  their source) → **keep_with_trigger**, they count queries and #253 is one query.
- **decisions-needed (5):** ESC-1 R5 breaks 2 committed `test_mcp_server` pins ·
  ESC-2 R6 breaks 1 more · ESC-3 R3 breaks 2 `test_task_ledger` pins (the deliberate
  live-verb change) · ESC-4 R7 needs a new SHARED read-txn seam in `_txn.py` ·
  ESC-5 MP-5 is an unruled operator fork (three readings; one pin).
- **The lead's five-item RIDER SET (sidecar `f00ebd5` §2/§3/§4) is DONE, not deferred** —
  I had capacity, so per the don't-kick-the-can law I took it rather than have it landed
  separately. All five are in my writable set. §RIDERS.
- **Pin counts:** `test_blocks_edge.py` **94 → 133** · `test_query_tasks_bounded.py`
  **23 → 29**. Total **117 → 162**.
- **RED honesty at `faf035d`:** blocks-edge **108 RED / 25 GREEN**, bounded **5 RED / 24
  GREEN** — the pre-rider blocks-edge RED set was identical across **5 consecutive
  `-n auto` runs**, no flake.
- **SATISFIABILITY RECEIPT: `162 passed, 0 failed`** on my own known-correct reference
  build, and **`162 passed` again after `ruff check --fix .`**, with
  `ruff` clean and `typecheck.sh` OK (171 loremaster files). §X-SAT.
- **Mutation proofs, declared from `--collect-only` BEFORE each run, diffed both ways —
  nine of them:** W-1 → 6/6 declared fired + 2 disclosed unexpected reds (EXIT=4, reported
  not edited) · R7 per-blocker read → **HELD 2/2** · per-hop cycle walk → **HELD 1/1** ·
  PROOF 5a/5b → **HELD 4/4 each** · RIDER-A locus → **HELD 1/1** · RIDER-B no-write clause
  → **HELD 3/3** · RIDER-C stated cost → **HELD 1/1** · RIDER-D `max_depth_used` → **HELD
  2/2** · RIDER-E elided id → 7/7 declared fired + 8 disclosed unexpected reds (EXIT=4).
  Every tree restored byte-exact. §X-MUT.
- **`loremaster.__file__` = `/home/ejprice/scratch/contractfix-04b1-ref/loremaster/loremaster/__init__.py`**
  (`scratch_copy.sh`, provenance VERIFIED, all four members). I did **not** read
  `/home/ejprice/scratch/adv04b1-ref`.
- **Gates (repo tree, unpiped, exits captured separately):** `./scripts/typecheck.sh`
  **EXIT=0** · `uv run ruff check .` **EXIT=0, "All checks passed!"** · scoped `pytest -n auto`
  **116 failed, 588 passed, 19 skipped** (every failure is a declared RED-by-design pin).
- **Receipt pointers:** §BLOCKERS · §MP-1…5 · §R5 §R6 §R7 · §E-H · §E-C · §R-e ·
  §RIDERS · §X-SAT · §X-MUT · §ESCALATIONS · §RESIDUALS.

---

## §BLOCKERS — the two things that had to go first

### E-A — the unsatisfiable `[owner-filter]` leg. CLOSED, and the fix is not the one proposed.

**Reproduced independently** before changing anything, on the repo tree at `faf035d`:

```
loremaster/tests/test_blocks_edge.py:2753: AssertionError: assert False
    (TestTheReadIsBOUNDEDByTheCallersFilter::_measure -> `assert claim.claimed`)
```

The fixture claims `target` while its only blocker is still `open`; the CAS refuses, so
it dies **before `query_tasks` is called** — RED on every build, correct ones included.
That is the C-DEF class.

**The one-line fix in `REPORT-contract-04b1-253.md` §E-A drives the blocker to
`STATUS_DONE`. I verified it and used `STATUS_WONTFIX` instead**, because `_drive_to(...,
done)` CLAIMS the blocker on its way through (`claim_task(task_id, ACTOR)`), which leaves
it owned by `ACTOR` and puts **two** tasks in the owner leg's answer — contradicting
`_measure`'s own docstring (*"the query filters on a status/owner only the target tasks
have"*). `wontfix` is a single legal transition from `open`, leaves the blocker unowned,
and keeps the answer at the ONE target. Both work; only one keeps the fixture's stated
invariant true.

**And the pin had a second hole the E-A fix does not touch.** Its only size guard was
`assert large < UNRELATED_TASK_COUNT_LARGE` — which `0 < 60` satisfies, so **`return []`
passed it**. `_measure` now returns `(rows, answer_size)` and every leg asserts the
answer is exactly 1 at BOTH sizes, plus `small > 0`. (The sibling file's `_measure`
already did this; SECTION I's did not.)

Measured after the fix, both legs now fail on the REAL assertion — `7 rows` vs `62` —
i.e. they reach `query_tasks` and observe #253.

### R-2 — PROOF 5's declaration block. CLOSED, and it was wrong in TWO ways.

Verbatim execution at `faf035d`:

```
PROOF5a EXIT=4        # PROOF FAILED — the observed RED set is not the declared one
```

1. The block carries **no** "+ this contract's three already-RED `blocks` declaration
   pins" clause that PROOF 3's and PROOF 4's blocks both carry. **Confirmed.**
2. **Second defect, found by running it and NOT in the adversary's report:** the block
   inherits PROOFS 1–2's `-- … "$F" "$G"` scope. Every red PROOF 5 declares lives in
   `$G`; adding `$F` on a pre-build tree contributes ~70 unexpected reds unrelated to the
   mutation. Scoped to `"$G"`.

With both fixed, **executed, both legs**:

```
PROOF5 REFERS_RELATION      EXIT=0   4 failed, 62 passed   PROOF HELD 4/4
PROOF5 ANSWERS_TO_RELATION  EXIT=0   4 failed, 62 passed   PROOF HELD 4/4
tree restored byte-exact (surreal_schema.py md5 dc5dc6f18eb6dc87dbb8cd8d26df417d)
```

**A THIRD finding, mine, written into the block:** the clause is **tree-dependent**.
Those three `blocks` pins are RED *because the build has not landed*; the moment the
builder emits the edge they go GREEN and a declared set still naming them produces
DECLARED-REDS-THAT-STAYED-GREEN — a FAILED verdict for the opposite reason. The block now
states: declare the three BEFORE the build, drop them AFTER, and PROOFS 1–2 (which mutate
code the build ADDS) must never carry the clause at all.

---

## §MP-1 … §MP-5 — the missing pins

### MP-1 — the DEFAULT-bound truncation pair, plus the boundary. `TestTheReadIsHONESTAtItsBound`, 3 new legs.

Re-derived the monoculture: `max_depth` appeared in the whole file exactly twice, both
times as the literal `2`. The new legs pass **no** `max_depth` at all and derive the chain
depth from `TASK_BLOCKER_MAX_DEPTH` itself:

| leg | upstream depth | expects |
|---|---|---|
| `..._DEEPER_than_the_DEFAULT_bound_reports_TRUNCATED` | `bound + 2` | `truncated=True`, `len(ids) == bound` |
| `..._EXACTLY_at_the_DEFAULT_bound_reports_truncated_FALSE` | `bound` | `truncated=False`, `len(ids) == bound` |
| `..._WELL_WITHIN_the_DEFAULT_bound_reports_truncated_FALSE` | 2 | `truncated=False`, both ids |

**The middle leg is mine and it is the sharpest.** The adversary's MP-1 is a pair; a pair
cannot distinguish a correct build from `truncated = len(ids) >= max_depth`, which is the
next plausible wrong build and which answers `True` on a chain that fits exactly. At the
cap it must answer `False` — nothing was cut.

### MP-2 — a REAL, ACCEPTED, bracket-rendered id through the mirror AND the traversal. `TestARealBlockerOfANyIDShapeRoundTrips`, 6 legs.

Re-derived the renderings on SDK 2.0.0 rather than trusting the report:

```
'0199c4f1-7d2a-4e51-9a63-000000000000' -> task:⟨…⟩      '20260728'  -> task:⟨…⟩
'wave-7-charter'                       -> task:⟨…⟩      '0'*32      -> task:⟨…⟩
'real_ab12'                            -> task:real_ab12
uuid4().hex ('633ea3be…')              -> task:633ea3be…   (BARE)
```

Three ACCEPTED shapes, minted through `create_many(ids=…)`, each driven through
`create_task`'s mirror, `_edge_blockers_of`, the traversal's RESULT, **and** — the leg
that actually kills `split_decode` — `get_task(served_id)`. A second class of legs makes
the **waiter's own id** hostile too, because the traversal's START binding is a second
decode site and a mis-bound start returns `[]` silently on both arrows.

`_assert_shape_is_hostile` guards the fixture itself: an id that renders BARE proves
nothing, so the leg refuses to run on one.

### MP-3 — the `max_depth` ARGUMENT bound. `TestTheBOUNDArgumentIsItselfBOUNDED`, 7 legs.

Four refusal legs (`-1`, `0`, `256`, `257`) and three positive controls (`1`, `2`, `255`).
Each refusal asserts four things: it RAISES; it is **not** a `SurrealStoreError` (the
engine's text is withheld by the seam's hygiene, so an agent cannot act on it); the served
sentence equals `_served_max_depth_refusal(value)` **by value**; and
`measure_store_traffic(...).calls == 0` — **no statement reached the engine**, which is the
leg that separates real client-side validation from a prettier translation.

**The 255-vs-256 under-specification the adversary found is DECIDED and both readings are
written down** (in `_served_max_depth_refusal`'s docstring): refuse at or above
`ENGINE_RECURSION_CEILING`. That is satisfiable by BOTH build shapes the adversary
measured (probe-at-N+1 and single-query), which is exactly why it is the right cut — the
public bound stops being a property of an implementation detail the caller cannot see.
The `255` positive control is deliberate: an off-by-one comparison rejects it while
passing every other leg. **One edit to overturn.**

### MP-4 / MP-4a — R6, one cycle detector. `TestTheCyclePolicyHasONEImplementation`, 4 legs + docstring corrections.

Measured at `faf035d` through the real dispatcher (§ESC-2 has the receipt): a batch-key
cycle is refused by `AppContext._find_key_cycle` with a **bare `ValueError`** and its own
sentence, and it fires FIRST.

The four legs, and what each holds:

1. `test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS` — the class is
   **derived from a real ledger refusal**, never named; the message must name both keys.
2. `test_a_PERSISTED_ID_cycle_is_UNREACHABLE_at_the_TOOL_SEAM_by_construction` — **see
   Deviation 3 below.**
3. `test_MUTATION_neutralising_the_SHARED_detector_lets_BOTH_shapes_through` — an
   accept-everything stub (never a raising sentinel — 04a measured why) installed in BOTH
   consuming namespaces; both cycle shapes must then LAND. Routing is not sharing.
4. `test_MUTATION_replacing_the_shared_FORMATTER_changes_BOTH_refusals` — one sentinel,
   two call sites, one run. Pins the SHAPE, not the words: R6 permits the two vocabularies
   to differ, which is why the shared thing is a formatter taking a noun.

**⚠ Deviation 3, and it is a finding.** The adversary's MP-4 proposes a persisted-id cycle
pin at the tool seam. **That shape is unreachable there.** `AppContext._create_many`
pre-mints every id (`uuid4().hex` per item), so a caller cannot name the id it is about to
create — and a cycle closes only when an EXISTING row's `blocked_by` already names that
id. I wrote the pin, ran it on my correct reference build, and it **DID NOT RAISE**;
that is how I found it. Shipping it would have been a second C-DEF. It is replaced by a
**KNOWN BOUND pinned** (repo law: *"when you cannot close a hole, pin it"*) with a NAMED
RE-OPEN TRIGGER: the day `lore_tasks` accepts caller-supplied ids, the pin goes RED and
the persisted-cycle refusal needs its own seam pin.

*(That pin also caught a FALSE GATE of my own on its first run: its original assertion
searched the RENDERED text for the caller's key, and the render legitimately ECHOES the
key — so it fired on an echo while its message promised a check about the ID. Now it
compares the served ID SET. The correct-build control is what exposed it.)*

**MP-4a documentation debt — both halves corrected in place:**

- `TestACycleIsDetectedOverPERSISTEDIds`' docstring no longer teaches that the `+collect`
  self-reach is *"the working acyclicity detector"* full stop. It now says that is true of
  the READ this class exercises and **FALSE of the write-time guard**, and points at the
  class that owns the guard.
- `TestCreateRefusesToFormACycle`'s docstring now states, before any test, **why** the
  guard must walk the COLUMN client-side: its own persisted-cycle fixture is *forced* into
  a column-only write by this packet's own `ENFORCED` (the closing dependency names a task
  that does not exist yet), so **any engine traversal returns "acyclic"**. It also states
  the corrected package verdict — `bespoke`, minimal surface (a DFS over the column; the
  closure read stays on the engine) — and names the R7 composition.

### MP-5 — the superseded-blocker door. `TestASupersededBlockerIsNotASilentBlackHole`, 2 legs. **UNRULED — §ESC-5.**

Reproduced independently on the **current tree** (not inherited):

```
transition->done:    IllegalTransitionError: task '…' is superseded and cannot transition from 'open' to 'done'
transition->wontfix: IllegalTransitionError: task '…' is superseded and cannot transition from 'open' to 'wontfix'
```

The pin is written over the **OUTCOME**, not a mechanism: *refused at create* **or** *the
blocker is escapable*. It is satisfied by reading (a) and by reading (b). It **cannot** be
satisfied by reading (c) — declare the door out of scope — because (a)/(b) and (c) are
opposite behaviours and no pin is green under both. Its docstring says so and says what to
do: **if the operator rules (c), DELETE the class and say so** — the same disposition
`TestTheDuplicateBlockerDivergence` already carries for its own escalation.

---

## §R5 / §R6 / §R7 — the round-2 rulings

### R5 — the `limit` push-down. `TestTheLimitIsPUSHEDINTOTheStatement`, 4 legs (test side only).

**⚠ Escalation E-D's PREMISE is FALSE, and the builder needs the correction more than the
ruling.** E-D (raised by both #253 authors, and repeated in R5's own parenthetical) says
the dispatcher *"slices AFTER materialisation"*. **Re-derived at `faf035d` through the
real handler:**

```
tasks(action='query', limit=5) -> ValueError: 'since'/'limit' apply only to action='rollup' — omit them for 'query'
```

It does not slice at all; it **rejects** `limit` for every non-rollup action. R5 is
therefore not a re-ordering of an existing cap — it makes `limit` a NEWLY ACCEPTED
parameter of `action='query'`, which is a served-surface change with committed pins
against it (§ESC-1).

The legs: the ledger accepts `limit` and serves at most that many · the cap bounds ROWS
READ, not just rows served (a growth comparison at 5 vs 60 **matching** rows, so only a
`LIMIT` in the statement can keep the read flat) · **the TOOL SEAM passes it through** ·
and a positive control that an UNLIMITED query still serves everything (a build that
capped unconditionally would pass all three).

⚠ `query_tasks(limit=…)` is called through `**filters` helpers, not a typed direct call:
the parameter does not exist yet, and a typed call is a **mypy error today**, not a RED
pin — a contract that fails its own gate before a builder sees it. Same posture the
existing `_transitive_blockers` handle uses, and stated in the pin's docstring.

### R6 — see §MP-4 above.

### R7 + its rider — `TestTheTwoReadsShareONESnapshot` (2 legs) and `test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain` (1 leg). **Pinned together, as instructed.**

**The instrument is ROUND TRIPS, and the reasoning is why it is not a text pin.** One round
trip is one snapshot whatever its shape — a `BEGIN … COMMIT` through `query_raw`, or a
single `SELECT` whose blocker resolution is a sub-select. A pin demanding the literal
`BEGIN` would redden the second build, which is *stronger* than what R7 asks for; a
contract must not forbid a better answer than its author imagined. The stated bound: a
2-round-trip build also satisfies a growth comparison, so this instrument proves
*"cost does not grow with the graph"*, not *"there is literally one statement"*.

- **read side**, 2 legs on two different wrong builds: N blockers behind ONE candidate
  (an N+1 over the BLOCKERS) and ONE blocker behind N candidates (an N+1 over the
  ANSWER). Same missing snapshot, different loop, so two fixtures.
- **write side (the rider)**: a create blocked on a 3-deep chain vs a 30-deep one must
  cost the same round trips. Its failure message names the trap explicitly: *do NOT
  satisfy this by dropping back to an engine traversal — the closing dependency cannot
  carry an edge, so that reddens the persisted-cycle pin.* Both rulings, one message.

Rows are deliberately NOT compared on either — a deeper graph legitimately reads more
rows, and a row comparison here would forbid the correct build.

---

## §E-H — Section I's 11 regression pins. CLOSED AT SOURCE, and the fix found a second hole.

Both out-of-filter pins are now parametrised over a `(non-terminal, terminal)` blocker
axis, and both gained a **candidate-set assertion** that makes the fixture prove it can
observe anything at all.

**⚠ And the OWNER pin could not fail — a defect the parametrisation exposed, not one E-H
named.** Its fixture drove the blocker to `claimed`, then attempted to claim the dependent
for `other_owner`, and **asserted the claim was refused**. A refused claim leaves the
dependent UNOWNED — so `query_tasks(owner=other_owner)` could never contain it, whatever
the build did, and *"the dependent is not served"* was true by the OWNER FILTER ALONE.
A task that is both BLOCKED and OWNED is unreachable through the public verbs (the CAS
refuses a blocked claim; no verb adds a dependency after birth), so the row is now
raw-seeded the way production got its own — `_seed_legacy_task` gained an `owner`
parameter.

**Measured (§X-MUT, W-1):** on the naive push-down, both **terminal** legs go RED and both
**non-terminal** legs stay GREEN — the finding's claim reproduced exactly, in both
directions.

---

## §E-C — `_rows_read`'s home. MOVED, and it CHANGED SEAM, which is the part that matters.

It now lives in `_surreal_harness.py` beside `run`, as **`measure_store_traffic`**
returning a `StoreTraffic(calls, rows, statements)`. Both files import it there.

**The seam change is not cosmetic and it is a finding.** The old instrument wrapped
`TaskLedger._query` — ONE of the ledger's doors. Ruling R7 puts the bounded read's two
reads inside one transaction, and a transaction that returns results must ride `query_raw`
(store reference §3: `execute_transaction` returns `None` and cannot serve a READ). **A
`_query`-keyed counter reports ZERO rows for exactly the build R7 demands — and zero reads
as "the read did not grow".** The instrument would have lied in the direction of false
confidence, for a build the contract itself now requires. It counts at the CONNECTION,
which every seam passes through.

Two measured details, both written into its docstring:

- **Only `query_raw` is wrapped, and that is DERIVED, not assumed.** [READ, SDK 2.0.0
  `connections/async_ws.py`] `query()`'s body is `await self.query_raw(...)`, so wrapping
  both DOUBLE-COUNTS: my first version reported `calls=2, rows=4` for one two-row read.
- **Stated bound:** an SDK call reaching the engine without `query_raw` (`select`/`create`/
  `insert`/`upsert`) is invisible to it. No ledger uses one today.

Measurement-neutral on the existing pins: the same `7 rows vs 62` the old instrument
reported. A new positive control
(`test_POSITIVE_CONTROL_the_instrument_ALSO_sees_a_read_inside_a_TRANSACTION`) proves it
sees BOTH doors — it is the control that would have caught the old one.

---

## §R-e — the whole-schema migration gap. CLOSED for every guarded edge.

Re-derived: the pin applied FOUR slices, `generate_message_ddl` absent, and seeded exactly
ONE edge row (`briefed`). Now five slices, plus a `message` row, a second `task` row, and
a ROW on **every** guarded edge (`briefed`, `to`, `blocks`), each asserted to survive the
re-apply — plus `to`'s edge-local `ack_note`, the column that records that a directive was
discharged.

Two things the widening taught, both written into the file:

- `message.sender` is a `record<agent>` LINK: the string `'agent:probe'` is refused
  outright (`Expected record<agent> but found 'agent:probe'`) and a later `UPDATE … SET`
  cannot rescue it, because the CREATE fails first on the missing required column. It is
  bound as a real `RecordID` inside the CREATE's own CONTENT.
- The seeds loop's `len(rows) == 1` is now DERIVED per table (`task` holds two rows since
  the widening). A hardcoded `1` is how a widening quietly turns a survival pin into a
  fixture-arithmetic pin.

`blocks` is named by LITERAL, not imported — finding #133: importing a not-yet-exported
name makes the whole 5000-line file UNCOLLECTABLE rather than RED.

**Honest scope: this is COVERAGE, not a new discriminator against a wrong BUILD** — the
property it adds is about the engine's `OVERWRITE` behaviour, which our code cannot
mutate in one line. I proved the legs are LIVE by perturbation instead (scratch only,
restored byte-exact, md5 verified against the repo):

```
skip the `to` RELATE -> AssertionError: the 'to' edge row did not survive the whole-schema
                        re-apply (got 0 rows) …            1 failed, 177 deselected
```

---

## §R-17 — the `PHANTOM_TASK_ID_NATIVE_SHAPE` prose. CORRECTED.

Re-measured rather than trusted: all four phantom shapes render **bracketed**; a real
`uuid4().hex` renders BARE. The comment claimed all-zeros was *"the shape `TaskLedger`
itself mints"*, which taught the OPPOSITE of the truth about the one axis finding #248 is
about. It now says the id shares the ledger's LENGTH and character class, states that it
renders bracketed and why, and points at the class that pins bracket-rendering ids on the
ACCEPTED side.

---

## §RIDERS — the lead's consolidated five, all landed

Taken rather than deferred: they were contract-shape, entirely inside my writable set, and
I had capacity — *"if the next agent would just do what you could do now, do it now."*
Source read: `docs/design/2026-07-28-04b-model-consumer-audit.md` §2 (R2-a…R2-e), §3
(A3-a/A3-b + the 04b-2 rider), §4. **All five are mutation-proven** (§X-MUT).

### RIDER-A — the batch refusal names the CARRYING ITEM. `test_the_BATCH_refusal_names_the_CARRYING_ITEM_of_every_unknown_blocker`

The rendered identity is now specified by `_served_blocker_identity`: `<id> (item <n>)` on
the batch path, bare `<id>` on the single-task path. **The id stays FIRST and verbatim** —
that is §4's load-bearing half, and it is what makes the token lift-out-able; the locus
rides in the parentheses. The skeleton is untouched, so L3's one-sentence-shape rule holds.

The pin is **by value**, over three items of which only two carry a phantom, with the
phantoms in non-served order and a REAL blocker in the middle as the non-vacuity guard.

⚠ **Escalation — the KEY half is NOT here, and it is not an oversight.** The sidecar's
example is `'step-schma' (item 3, key 'step-migrate')`. `TaskLedger.create_many` takes
`specs`/`ids` and **has never seen a key** — the ledger's key-agnosticism is a pinned
design property. Enriching the refusal with the key is a **third `server.py` touch** beyond
R5's and R6's named exceptions, so it needs a ruling. ⚠ It is also **partly
self-satisfying**, which is why I did not force it: the dispatcher's
`key_to_id.get(ref, ref)` pass-through means a typo'd temp key **arrives as the phantom
id**, so the caller is echoed its own token verbatim either way — the property §4 says is
the one that matters. **Fix now vs defer — the operator's call.**

### RIDER-B — the refusal states that NOTHING was created. `test_the_refusal_TELLS_the_caller_that_NOTHING_was_created`

The task family's `{requirement}` now carries both halves the sidecar asked for — the
acceptance rule stated **positively**, and the no-write fact:

> `unknown task(s): <identities> — every blocked_by entry must name an existing task row or
> a task created in the same call; NOTHING was created, so a corrected resend is safe`

The BEHAVIOUR was already pinned (`test_a_refused_create_writes_NO_task_row` + its batch
twin); what was not pinned is that the caller is TOLD, which is what makes a plain resend
known-safe without a reconnaissance read. Pinned by value in two sentence pins **and** as a
substring in its own leg — so a failure says WHICH clause went missing, which a by-value
diff of a long sentence does not. The leg also re-asserts the row count, so the sentence
cannot become a lie.

⚠ 04a's agent sentence is **byte-identical** afterwards (verified:
`unknown agent(s): lead (a1) — every id must name a registered agent row before a message
or a brief can be written in its name`). Only the TASK family's requirement changed.

### RIDER-C — the create path's cost is STATED. `TestTheCREATEPathsCostIsSTATED`, 3 legs

**The number is DERIVED from the behaviour, not re-stated beside it** (#104). The pin
MEASURES the round trips a real two-blocker create costs, extracts the integer from the
docstring's `Cost:` section, and requires equality. **It does not choose the number** — a
contract pinning "3" would forbid a correct 2-round-trip build. My reference build states
3 (existence probe + acyclicity walk + the one `BEGIN … COMMIT`) and the measurement
agrees; mutating the docstring to "2" reddens it (§X-MUT).

Two further legs close adversary **R-14** (#219's class, sites 2 and 3): both create verbs'
docstrings must carry a `Raises:` section naming `UnknownBlockerError` and `TaskCycleError`,
with the names read off the ledger module rather than typed here.

### RIDER-D — `max_depth_used`, the FLOOR property, and the fabrication trap. `TestTheResultIsSELFDESCRIBING`, 4 legs

- **The bound the read RAN at**, as a discriminating pair: a build hard-coding the module
  default dies on the explicit leg, a build echoing the caller's argument dies on the
  defaulted leg where there is no argument to echo.
- **The re-ask arithmetic**: `truncated is True` ∧ `max_depth_used == 2` ∧
  `len(ids) == max_depth_used`, so a render can say *"shown to depth N, re-run with
  max_depth=2N"* without a schema read — and a caller can tell truncation-on-DEPTH from
  truncation-on-COUNT, the ambiguity that otherwise forces a blind re-run.
- **The NEGATIVE, as an EXACT-SET pin over `TransitiveBlockers.model_fields`**:
  `{ids, truncated, max_depth_used}` and nothing else. Deny-by-default, for CLAUDE.md's
  instrument-lesson reason — the set of names a fabricated count could wear (`remaining`,
  `total`, `more`, `beyond`, `tail_count`, …) is unbounded; the safe set is three. The tail
  beyond a truncated closure is **genuinely uncountable without walking it**, so the house
  `+K more` grammar would force a builder to invent K, which both blind consults rated the
  worst outcome on the table.
- **The FLOOR docstring**, a served-English pin that says so in its own docstring: it
  checks the words are PRESENT and cannot check they are true; what makes them true is
  pinned by `TestTheTransitiveBlockerRead`'s closure/dedup legs.

⚠ The RENDER side of the rider (04b-2's `blockers shown to depth {n} — more exist beyond
(count unknown at this depth); re-run with max_depth=…`) is **deliberately not pinned
here** — it is 04b-2's surface. Routed, not dropped.

### RIDER-E — verbatim, round-trippable, never elided. `test_the_offending_id_is_reproduced_VERBATIM_and_never_ELIDED`, 4 legs

Parametrised over all four id shapes. Each leg asserts the id appears verbatim; that **no
elision marker** (`…`, `...`, ` more`, `+`) appears anywhere in the sentence; that the token
**lifted back out** of the served text equals the id the caller supplied; and — the leg that
makes it a round-trip rather than a substring check — that handing that token to `get_task`
refuses it **by that same token**. A build rendering `task:⟨0199c4f1-…⟩` echoes something an
agent cannot use anywhere: the #248 shape, on the refusal surface.

---

## §X-SAT — THE SATISFIABILITY RECEIPT

A reference build I wrote myself (I did **not** read `/home/ejprice/scratch/adv04b1-ref`):
the `blocks` edge in `_task_statements`; `agent_existence` generalised to
`UnknownRowError` / `format_unknown_row_refusal` / `reject_unknown_rows` with the agent
entry points as DELEGATING adapters (04a's sentence byte-identical); `tasks.py` gaining
`TASK_BLOCKER_MAX_DEPTH`, `TransitiveBlockers`, `UnknownBlockerError`, `TaskCycleError`,
`find_blocked_by_cycle` / `format_cycle_refusal` / `raise_cycle_refusal`, an atomic
`create_task`, a mirroring `create_many` (all CREATEs before all RELATEs), the
column-walking cycle guard, `transitive_blockers`, and a bounded `query_tasks` with the
limit push-down inside ONE `BEGIN … COMMIT`; `_txn.py` gaining
`execute_read_transaction`; `messages.py` gaining `UnknownSenderError` routed through the
shared policy, ordered FIRST; `server.py` routing its cycle policy to the ledger's and
passing `limit`.

Plus the five riders: the identity renderer split (`render_label_first` /
`render_identity_first`, one skeleton, family-chosen order), the widened task requirement,
`max_depth_used`, and the `Cost:` / `Raises:` docstring sections.

```
$ uv run pytest -q -n auto loremaster/tests/test_blocks_edge.py loremaster/tests/test_query_tasks_bounded.py
162 passed in 7.21s

# the HARDER leg — still satisfiable after the cleanups the lint demands:
$ uv run ruff check --fix .     All checks passed!
$ uv run ruff check .           All checks passed!
$ uv run pytest -q -n auto …    162 passed
$ ./scripts/typecheck.sh        lorerunes/lorescribe/loresigil/loremaster (171 files)/skills all OK

$ uv run pytest -q -n auto <the two contract files> + test_surreal_store \
      + test_enforced_relations + test_derivation_source_unification + test_surreal_harness
470 passed, 19 skipped

$ uv run python -c "from loremaster.agent_existence import format_unknown_agent_refusal; \
                    print(format_unknown_agent_refusal({'a1':'lead'}))"
unknown agent(s): lead (a1) — every id must name a registered agent row before a message or a brief can be written in its name
                                                    # 04a's sentence, BYTE-IDENTICAL

$ uv run python -c "import loremaster; print(loremaster.__file__)"
/home/ejprice/scratch/contractfix-04b1-ref/loremaster/loremaster/__init__.py
```

**No pin is RED on a correct build.** `ruff --fix` touched only production files I had
patched — the repo's test files are byte-identical to the scratch copy's after it ran
(verified by `diff`).

### ⚠ The contract killed two of my own builds, as designed

1. The persisted-cycle TOOL-SEAM pin **did not raise** — which is how Deviation 3 was
   found. A pin that could not fail on a correct build would have been invisible.
2. My first `_read_transaction` called `connection.query_raw` directly and the repo's
   **runtime SDK-escape guard** (finding #102's instrument, in `conftest.py`) failed
   **13 tests** with `2 SurrealDB call(s) escaped the retry driver … tasks.py:816 in
   _read_transaction() -> connection.query_raw()`. That is §ESC-4 and it is a real
   constraint on any R7-satisfying build.

---

## §X-MUT — MUTATION PROOFS (declared from `--collect-only` BEFORE each run)

| # | mutation | declared | result |
|---|---|---|---|
| W-1 | blocker statuses built from the CANDIDATE rows only (the naive push-down) | 6 | **6/6 fired**, 0 declared-green, **2 unexpected reds — DISCLOSED, not edited away** (EXIT=4) |
| R7 | blocker resolution as ONE READ PER BLOCKER (`_select_row` loop) | 2 | **PROOF HELD 2/2, EXIT=0** |
| rider | the cycle walk as ONE READ PER HOP (BFS over the column) | 1 | **PROOF HELD 1/1, EXIT=0** |
| PROOF 5a | `refers` IN/OUT swap | 4 | **PROOF HELD 4/4, EXIT=0** |
| PROOF 5b | `answers_to` IN/OUT swap | 4 | **PROOF HELD 4/4, EXIT=0** |
| RIDER-A | drop the item locus from the batch identity | 1 | **PROOF HELD 1/1, EXIT=0** |
| RIDER-B | drop `NOTHING was created` from the requirement | 3 | **PROOF HELD 3/3, EXIT=0** |
| RIDER-C | docstring says `2 round trips`, measurement says 3 | 1 | **PROOF HELD 1/1, EXIT=0** |
| RIDER-D | `max_depth_used` hard-coded to the module default | 2 | **PROOF HELD 2/2, EXIT=0** |
| RIDER-E | elide every id to its first 4 chars | 7 | **7/7 fired**, 0 declared-green, **8 unexpected reds — DISCLOSED** (EXIT=4) |

Every tree restored byte-exact (`surreal_schema.py` md5
`dc5dc6f18eb6dc87dbb8cd8d26df417d`; `tasks.py` md5 `d12fdced9ff6d1102ed81464df70d46c`
pre-riders and `d486529d66d934a013d612ef4772da69` post-riders; `agent_existence.py` md5
`2056e747affc45735a78fc3d9a2fd216`).

**RIDER-E's eight unexpected reds, reported rather than absorbed:** all four legs of
`test_a_create_naming_a_PHANTOM_blocker_is_REFUSED` and all four of
`test_create_many_ALSO_refuses_a_phantom_and_writes_NO_rows` also check that the id appears
in the served message, so an elided id reddens them too. **My prediction was too narrow, in
the safe direction** — the elision mutation is caught by fifteen pins, not seven. The
declared list was not edited to match; this paragraph is the disposition.

**W-1's two unexpected reds, reported rather than absorbed:**
`TestTheTwoReadsShareONESnapshot`'s two legs also redden under W-1 — not on their
round-trip assertion but on their **fixture-integrity guard** (`assert target in served`),
because W-1 drops the target from the answer. Their round-trip property is proven
independently by the R7 proof above, where they fire EXACTLY and alone. The declared set
was not edited to match; this paragraph is the disposition.

**W-1's headline, which is E-H's whole claim, measured in both directions:**

```
RED:   ..._EXCLUDED_by_the_STATUS_filter_still_counts[terminal-blocker]
RED:   ..._EXCLUDED_by_the_OWNER_filter_still_counts[terminal-blocker]
RED:   test_a_DONE_blocker_outside_the_{STATUS,OWNER}_candidate_set_still_RESOLVES
RED:   test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked[status-filter|owner-filter]
GREEN: ..._EXCLUDED_by_the_{STATUS,OWNER}_filter_still_counts[non-terminal-blocker]
```

---

## §ESCALATIONS — five, all outside my writable set

### ESC-1 — **R5 CONTRADICTS TWO COMMITTED PINS. C-DEF for the builder.** (`test_mcp_server.py`)

Measured on the reference build:

```
FAILED TestRollupDispatch::test_limit_on_a_non_rollup_action_is_rejected
FAILED TestRollupDispatch::test_since_on_a_non_rollup_action_is_rejected
FAILED TestTasksTool::test_tasks_query_renders_summarised_rows_not_raw
FAILED TestTasksTool::test_superseded_task_renders_a_chain_marker_not_bare_status
       (TypeError: FakeTaskLedger.query_tasks() got an unexpected keyword argument 'limit')
```

*Tests written before a semantic change certify the OLD world.* The exact edits I would
make: split the strict-param guard (`since` stays rollup-only; `limit` becomes legal for
`rollup` **and** `query`), retarget `test_since_on_a_non_rollup_action_is_rejected`'s
message assertion, **replace** `test_limit_on_a_non_rollup_action_is_rejected` with a
non-query action plus a new pin that `limit` on `query` is ACCEPTED and pushed down, and
give `FakeTaskLedger.query_tasks` a `limit` parameter that slices. **Fix now vs defer —
operator's call.**

### ESC-2 — **R6 CONTRADICTS A THIRD PIN.** `test_mcp_server.py::TestCreateManyDispatch::test_intra_batch_cycle_is_refused_with_the_exact_text`

It pins the retired bare-`ValueError` sentence by value. Under R6 the seam raises
`TaskCycleError` with the shared shape. The pin must be re-authored to the new sentence —
which is the correct outcome (it is the pin that proves the served text is one
implementation), but it is a required edit outside 04b-1's granted `server.py` touch.

### ESC-3 — **R3's deliberate live-verb change breaks two `test_task_ledger.py` pins.**

```
FAILED TestBlockedClaiming::test_never_minted_blocker_id_counts_as_blocked_in_query[real]
FAILED TestBlockedClaiming::test_never_minted_blocker_id_fails_closed_on_claim[real]
```

Both CREATE a task naming a never-minted blocker — which R3 now REFUSES. This is the
change R3 ruled, not a regression, but the two pins certify the old world and must be
re-authored (raw-seed the legacy row, as this contract's `_seed_legacy_task` does, so the
fail-closed READ property stays pinned while the WRITE becomes a refusal).

### ESC-4 — **R7 needs a SHARED read-transaction seam in `loremaster/store/_txn.py`.**

`execute_transaction` returns `None` and cannot serve a read; `query()` validates only
`statement[0]`; so R7's two-read transaction must ride `query_raw` — and a hand-rolled
`query_raw` **FAILS the repo's runtime SDK-escape guard** (measured: 13 tests, *"2
SurrealDB call(s) escaped the retry driver"*). My reference added
`execute_read_transaction` beside `execute_transaction` — same `retry_on_conflict` driver,
same classify/self-heal, returning every statement's result. **This is a production design
decision, not a builder shortcut: it belongs in the builder's brief.**

### ESC-5 — **MP-5 is an UNRULED operator fork.** §MP-5. Three readings; my pin is green
under (a) and (b) and cannot be green under (c). **My recommendation: (a)** — refuse at
create, naming the superseded blocker and pointing at its successor. It is R3's own shape,
it needs no change to a live claim gate, and my reference build implements it. If the
operator prefers (c), **delete the class and say so in the wave report.**

---

## §DEV-2 — the pre-existing RED I fixed

`test_surreal_harness.py::…::test_the_harnesss_docstring_counts_are_the_DERIVED_counts`
was **RED at `faf035d` before I touched anything** (proved by `git stash`): the docstring
said 43 importers / 26 `connect_admin` callers; the derivation says **45 / 28**. The two
04b-1 contract commits each added an importer and neither re-derived the counts — the exact
class the pin exists to catch, in the packet that owns the pin's own repo law. Both numbers
corrected; `test_surreal_harness.py` now **57 passed**.

---

## RESIDUALS — every item, its own line, its own verdict

| # | item | verdict |
|---|---|---|
| R-1 | E-A `[owner-filter]` unsatisfiable | ✅ **CLOSED** (§BLOCKERS). Fixed with `wontfix`, not `done`, and the reason is written into `_measure`'s docstring. |
| R-2 | SECTION I's `_measure` had no answer-cardinality leg (`return []` passed it) | ✅ **CLOSED** — my finding, not on the worklist. Both sizes now assert the answer is exactly 1, plus `small > 0`. |
| R-3 | PROOF 5 declaration clause | ✅ **CLOSED**, and a SECOND defect (the `"$F" "$G"` scope) plus a THIRD (the clause is tree-dependent) fixed with it. Both legs executed, EXIT=0. |
| R-4 | MP-1 default-bound pair | ✅ **CLOSED**, widened to a triple — the cap-exact leg kills `truncated = len(ids) >= max_depth`, which the pair cannot. |
| R-5 | MP-2 bracket-rendered accepted ids | ✅ **CLOSED**, 6 legs across two decode sites (result AND start binding). |
| R-6 | MP-3 `max_depth` argument bound | ✅ **CLOSED**, 7 legs; the 255-vs-256 under-specification DECIDED with both readings written down. |
| R-7 | MP-4 / R6 one cycle detector | ✅ **CLOSED**, 4 legs. ⚠ The proposed persisted-cycle seam pin was UNREACHABLE and is replaced by a KNOWN BOUND with a re-open trigger (Deviation 3). |
| R-8 | MP-4a documentation debt | ✅ **CLOSED** — both docstrings corrected in place; the package verdict for the write-time guard is now `bespoke`, with its minimal surface stated. |
| R-9 | MP-5 superseded blocker | 🔴 **PINNED, UNRULED — §ESC-5.** Operator's call; the pin is deletable in one edit if (c). |
| R-10 | R5 limit push-down | ✅ **PINNED** (4 legs) 🔴 **and it breaks 4 pins in `test_mcp_server.py` — §ESC-1.** E-D's premise was FALSE; re-derived. |
| R-11 | R6 tool-seam vocabulary | ✅ **PINNED** 🔴 **and it breaks 1 more `test_mcp_server.py` pin — §ESC-2.** |
| R-12 | R7 + rider, pinned together | ✅ **CLOSED**, 3 legs, both mutation-proven. 🔴 Needs a new shared `_txn` seam — §ESC-4. |
| R-13 | E-H's 11 regression pins | ✅ **CLOSED AT SOURCE**, and the OWNER pin turned out to be **unable to fail at all** — a hole E-H did not name. Measured RED/GREEN split reproduced. |
| R-14 | E-C `_rows_read`'s home | ✅ **CLOSED**, and the seam changed with it — a `_query`-keyed counter would have gone BLIND on the build R7 requires. Cost: 2 lines in `test_surreal_harness.py` (Deviation 1). |
| R-15 | R-4 / R-e whole-schema migration | ✅ **CLOSED** for all three guarded edges. Honest scope: COVERAGE, not a build discriminator; liveness proved by perturbation instead. |
| R-16 | R-17 prose | ✅ **CLOSED**, renderings re-measured. |
| R-17 | `test_task_ledger.py`'s two never-minted-blocker pins | 🔴 **ESC-3** — they certify the pre-R3 world. Re-authoring is the builder's; the shape is in this report. |
| R-18 | `_surreal_harness` docstring counts | ✅ **FIXED** (pre-existing RED, Deviation 2). |
| R-19 | `TestTheDuplicateBlockerDivergence` (E-6, pre-existing) | 🟡 **UNCHANGED and still RED on the pristine tree.** My reference build implements the class's own one-line recommendation (`array::len(array::distinct(blocked_by))` in the CAS) and it goes green — so it IS satisfiable, but adopting it is a live-CAS change the operator has not ruled. |
| R-20 | `limit` + `blocked` together are unpinned, and they interact | 🟡 **FLAGGED, deliberately not pinned.** A `LIMIT` pushed into the statement cuts rows BEFORE the client-side `blocked` filter, so `query_tasks(status=…, blocked=False, limit=5)` can serve FEWER than 5 while more exist. No pin anywhere combines them. Needs a ruling: is the cap on CANDIDATES or on the ANSWER? |
| R-21 | The R7 instrument proves "cost does not grow", not "one statement" | 🟡 **STATED BOUND**, in the class docstring. A 2-round-trip build passes. A text pin on `BEGIN` would forbid a strictly better single-statement build. |
| R-22 | `measure_store_traffic` is blind to non-`query_raw` SDK calls | 🟡 **STATED BOUND** in its docstring. No ledger uses one today; a build that started to would be measured as free. |
| R-23 | MP-1's cost scales with the builder's own `TASK_BLOCKER_MAX_DEPTH` | 🟡 **ACCEPTED.** At 32 the deepest leg seeds 35 rows + 34 edges (~2s). A default near the 256 ceiling would make these legs slow; the existing `1 < default < 256` pin is the only bound. |
| R-24 | `test_mcp_server.py` / `test_task_ledger.py` were run on the REFERENCE build only | 🟡 **DISCLOSED.** They are unchanged on the repo tree; the failures above are what the BUILD will cause, measured in scratch, not something this contract broke today. |
| R-25 | Scratch tree `/home/ejprice/scratch/contractfix-04b1-ref` | 🟡 **DISPOSITION NEEDED.** It holds a complete, gate-clean 04b-1 reference build (including `execute_read_transaction` and the R5/R6 `server.py` edits). Keep it for the builder to diff, or delete — **your call**; I have not deleted it. I also did not touch `/home/ejprice/scratch/adv04b1-ref`. |
| R-26 | The adversary's §X3 reference build and mine disagree on nothing I can see | 🟡 **UNVERIFIABLE BY ME** — I was forbidden to read it, correctly. Two independent builds both take this contract to 0-failed is a stronger receipt than either alone, but only the lead can state that. |
| R-27 | I did not run the FULL suite | 🟡 **DELIBERATE** (brief-base §3). Scoped to the 7 suites named in §gates plus, in scratch, `test_mcp_server` + `test_task_ledger`. |
| R-28 | RIDER-A's KEY half (`… (item 3, key 'step-migrate')`) | 🔴 **ESCALATED, §RIDERS.** The ledger is key-agnostic by design; the key belongs to `AppContext._create_many` and is a THIRD `server.py` touch. Partly self-satisfying — a typo'd key arrives AS the phantom id, so the caller's own token is echoed verbatim either way. **Operator's call.** |
| R-29 | RIDER-D's 04b-2 RENDER half | 🟡 **ROUTED, not dropped.** The rendered truncation line (*"more exist beyond (count unknown at this depth); re-run with max_depth=…"*) and the ban on a `+K more` form on that line are 04b-2's surface. The LEDGER half — `max_depth_used`, the floor docstring, and the exact-field-set ban on any tail count — is pinned here. |
| R-30 | RIDER-C's `Cost:` docstring section is a NEW convention | 🟡 **DISCLOSED.** No other verb in the package carries one; the pin reads a named section rather than a phrasing precisely so the convention is greppable. If the lead prefers the sentence inside `Raises:`-adjacent prose, that is one edit to `COST_SECTION`. |
| R-31 | The task requirement sentence GREW (RIDER-B) | 🟡 **DELIBERATE, and it is a served surface for an agent.** Both halves the sidecar asked for are in it (positive acceptance rule + no-write). 04a's AGENT sentence is untouched and byte-verified. |
| R-32 | RIDER-E's elision check greps for `+` | 🟡 **STATED BOUND.** It would fire on a legitimate `+` in some future requirement text. That is the deny-side of a served-English pin and it is cheap to loosen; it is here because `+K more` is the exact grammar the fabrication trap wears. |

---

## Gate tails (repo tree, unpiped, exits captured separately)

```
$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK (171 files) · skills OK
EXIT=0

$ uv run ruff check .
All checks passed!
EXIT=0

$ uv run pytest -q -n auto test_blocks_edge test_query_tasks_bounded test_surreal_store \
      test_enforced_relations test_derivation_source_unification test_surreal_harness test_task_ledger
116 failed, 588 passed, 19 skipped in 20.77s
  = 108 (test_blocks_edge, RED-by-design) + 5 (test_query_tasks_bounded, RED-by-design)
  + 3 (test_enforced_relations — the DELIBERATE blocks declaration pins)
  test_surreal_store / test_surreal_harness / test_task_ledger: 0 failed
```

**Stability:** measured BEFORE the rider set, the `test_blocks_edge` RED set was
byte-identical across **5 consecutive** `-n auto` runs (95 each). No flake. The rider pins
added 13 more RED (95 → 108) and 0 GREEN, which is the expected direction: every one
describes behaviour this packet has not built yet.

**There are no failing tests outside this contract's own declared RED-by-design set in the
suites I ran.** I did not run the full suite (brief-base §3). The failures a BUILD will
cause in `test_mcp_server.py` and `test_task_ledger.py` are measured in scratch and
escalated in §ESC-1…§ESC-3 — those two files are GREEN on the repo tree today.
