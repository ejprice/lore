# REPORT-adversary-04b1-r6 — grading the r6 contract delta (19 new pins)

brief-base v8 read

**comms receipt: NONE — I COULD NOT REGISTER. See the capability check immediately below.**

---

## CAPABILITY CHECK (brief-base v8 §4) — **GAP, AND IT BLOCKS TWO NAMED DELIVERABLES**

*Reported first, per §4, because a lead cannot see my toolset.*

- **What was demanded:** `ToolSearch "select:mcp__lore_lore__lore_comms,…lore_findings,…lore_search,
  …lore_get_symbol,…lore_read"`, then `lore_comms action=register …`, `drain` at turn boundaries,
  and *"file your own findings via `lore_findings` — no lead transcription this time."*
- **What I actually have:** `ToolSearch` IS present in my toolset — the fix at issue landed — but it
  **resolves nothing**. Three queries returned `No matching deferred tools found`: the exact
  `select:` line from the brief, a keyword query (`lore comms register findings file a finding`), and
  a control query for an unrelated deferred server (`navigate browser tab`). A control matters here:
  the empty result is not specific to lore, so this is not "lore is down", it is **ToolSearch
  resolving an empty index for me**. A direct call confirms it:

```
$ mcp__lore_lore__lore_comms(action=register, agent=adversary-04b1-r6, …)
Error: No such tool available: mcp__lore_lore__lore_comms
```

- **What I did instead:** ran the whole audit on `Bash`/`Read`/`Write`, which were sufficient for
  every *empirical* obligation (scratch builds, mutation runs, gates, live store). Every structural
  question was answered by `grep(1)` + `Read` — **declared as a lore fallback out loud, per §4**, and
  covering more than the three cases repo law reserves for grep, because no index was reachable.
- **A SECOND, SEPARATE GAP: I have no `SendMessage` tool either.** My whole toolset is `Read`,
  `Write`, `Edit`, `Bash`, `ToolSearch`, and the `mcp__claude-in-chrome__*` browser tools. So I
  cannot register, cannot `drain`, cannot `ack`, and **cannot message the lead at all** — this
  report file is my only channel. Per brief-base §1 that is the durable one anyway, but the lead
  should not wait on a ping that cannot be sent.
- **What a lead must change:** (a) `contract-adversary`'s tool grant needs the `mcp__lore_lore__*`
  tools **directly**, not via `ToolSearch` — the 2026-07-28 fix added the *searcher* but my index is
  empty, so finding #266 is **NOT closed for this agent**; (b) it needs `SendMessage`; (c) until
  then, briefs must not assign `lore_findings` filing or comms duties to this role. **The findings
  below are UNFILED and need lead transcription — exactly the thing this brief tried to stop.**
- Everything else the brief demanded was satisfiable: `scratch_copy.sh`, spike-surreal
  `ws://127.0.0.1:18000`, `ruff`, `typecheck.sh`, `git` (read-only). `:18500` was never touched.

**trust hard-definition read.** Its two askable questions, quoted verbatim from `CLAUDE.md`
§ *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"***

> **Ask: *"what broken state of this tool would serve exactly these bytes?"***

*Every number in this report was DERIVED by running, on **2026-07-28**, on branch
`feat/surreal-unification` at HEAD **`5e6a1d2`**. Every store call hit spike-surreal
`ws://127.0.0.1:18000` (TEST). I mutated no git state in the repo and edited no file in it except
this report. No number is inherited — where I re-derived somebody else's, I say whether it matched.*

**Scratch provenance (#140):** `./scripts/scratch_copy.sh /home/ejprice/scratch-adversary-04b1-r6`,
EXIT=0.

```
loremaster.__file__ = /home/ejprice/scratch-adversary-04b1-r6/loremaster/loremaster/__init__.py
```

Pristine `tasks.py` md5 `532ca7564374b8671111daf45ed48a0d`, re-verified byte-exact after every
mutation. I read none of the pre-existing `/home/ejprice/scratch*` reference builds.

---

## SUMMARY BLOCK

- **VERDICT ON THE DELTA: CONTRACT INSUFFICIENT.** The 19 new pins are well-built and three of
  them are the strongest in the packet — but **FOUR wrong builds survive the contract whole,
  247 passed / 0 failed each**, and two of them walk through the very holes r6 was written to close.
- **R-13's SEVENTH DIRECTION — FOUND, and it is worse than r6 feared: it is TWO directions.**
  **WB-DOOR3** satisfies A1/A2 and breaks A2's own ∀-claim (a third backfill door,
  `BACKFILL_FAILURE_DOORS` names two). **WB-CHUNK** satisfies A1's coverage and breaks R11's
  one-transaction rationale; A1's stated bound hands round-trips to a sibling whose fixture
  ceiling (30) is **below A1's own floor (61)**, so the handoff is false.
- **WRONG BUILDS THAT SURVIVED (all 247 passed / 0 failed, each with a positive control):**
  1 `WB-DOOR3` try/except on the mirror-state read · 2 `WB-CHUNK` mint chunked at 50 ·
  3 `WB-EXIST-CAP(40)` cap on the existence read · 4 `WB-LIMIT200` cap on the pending read.
- **QUANTIFIER TABLE (P1b): 13 invariants classified, every guarded row carrying a receipt.**
  §QUANT. Three guarded rows carry a **surviving wrong build**, not a killed door-build.
- **MISSING PINS, ranked:** M1 ∀-door derived (not hand-listed) · M2 the backfill's mint is ONE
  transaction **at A1's scale** · M3 A1's scale on the DISTINCT-BLOCKER axis · M4 the pending read
  carries no `LIMIT` (statement pin, ∀-scale). §PINS.
- **LEG-1 RE-MEASUREMENT: row 1's CORRECTION IS STILL FALSE (measured), row 2 is now TRUE
  (measured), and NEW row 7 is FALSE.** A virgin boot mirrors 0 edges yet the read serves one;
  row 7 asserts ∀-doors over a 2-of-3 hand-list. §LEG1.
- **SATISFIABILITY, BOTH LEGS, WITH COUNTS. Leg A (contract vs the SHIPPED build): 247 passed /
  0 failed** (two contract files) **+ 881 passed / 0 failed** (`test_task_ledger.py` +
  `test_mcp_server.py`), ruff EXIT=0, typecheck EXIT=0 → **NO FOURTH C-DEF. Leg B:** 3 of r6's 6
  mutation proofs re-derived and all 3 reproduce EXACTLY; 3 not re-run and named as such. §SAT.
- **COUNTS RE-DERIVED from `--collect-only`: 247 and 240 — r6's numbers are correct.**
- **A3's oracle is genuinely test-side** (production has zero `networkx` imports) **but the
  dependency is mis-placed: `networkx` sits in `loremaster`'s RUNTIME `[project] dependencies`**
  while nothing shipped imports it — against the house idiom stated verbatim in the same repo. §E1.
- **FIXTURE MONOCULTURE, this delta's axis: `_seed_star` holds DISTINCT BLOCKERS at 1 at every
  scale.** Secondary: every new `limit` pin uses 5; every new legacy fixture is `STATUS_OPEN`. §P2.
- **ESCALATIONS: 2** (E1 networkx placement · E2 my own capability gap). **FINDINGS FILED BY ME: 0
  — I could not; four need lead transcription.** §FINDINGS.
- **A4's narrowing is CORRECT and I could not break it** — receipts in §A4.

---

## §SAT — satisfiability, both sides, with counts

**Leg A — the whole contract against the CURRENT SHIPPED production build.** This is the
two-sided half of the gate: any pin that reddens `b8607c4`'s code is a C-DEF that would trap a
builder. Run in the scratch copy, production byte-identical to the repo (md5 above).

```
$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py
247 passed in 9.64s                                                    PYTEST_EXIT=0

$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_task_ledger.py \
      loremaster/tests/test_mcp_server.py
881 passed in 108.87s (0:01:48)                                        PYTEST_EXIT=0

$ uv run ruff check .          -> All checks passed!                   RUFF_EXIT=0
$ ./scripts/typecheck.sh       -> lorerunes/lorescribe/loresigil/loremaster/skills OK
                                                                       MYPY_EXIT=0

$ uv run pytest -q -p no:randomly --collect-only test_blocks_edge.py test_query_tasks_bounded.py
247 tests collected in 0.20s
$ uv run pytest -q -p no:randomly --collect-only test_task_ledger.py
240 tests collected in 0.17s
```

**VERDICT: NO FOURTH C-DEF.** r6's 247/240 counts and its 0-failed claim both reproduce
independently. `test_mcp_server.py`'s 641 is included in the 881 above.

**Leg B — each new pin RED against the build it targets.** I re-derived **3 of r6's 6** proofs
rather than inheriting them; all three reproduced EXACTLY, both ways.

| r6 proof | mutation | r6 declared | I observed | verdict |
|---|---|---|---|---|
| #1 WB-E | `LIMIT 50` on the pending read | 2 | **2, exact** (the two A1 pins) | **REPRODUCES** |
| #3 WB-CYCLE1 | record only the first cycle | 4 | **4, exact** (3 topologies + per-cycle) | **REPRODUCES** |
| PROOF 11 | drop the write guard's dependency filter | 1 RED + 1 stays GREEN | **1 failed, 6 passed** — exactly as declared | **REPRODUCES** |
| #2 WB-O, #4 WB-RENDER, #5 WB-FAKE, #6 WB-BOUNDED | — | — | **NOT RE-RUN** | **UNVERIFIED BY ME** — stated, not waved through |

WB-E receipt (verbatim), which is also the positive control for §P1-4:

```
FAILED …TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE::test_a_legacy_store_LARGER_than_every_other_fixture_is_backfilled_ENTIRELY
FAILED …TestTheBackfillCoversALegacyStoreLARGERThanEveryOtherFIXTURE::test_NO_row_of_a_LARGE_legacy_store_is_served_a_CONFIDENT_EMPTY
2 failed, 245 passed in 9.06s
```

---

## §P1 — the wrong builds. Four survived; each is paired with a positive control.

### P1-1 · **WB-DOOR3 — the third backfill door. BLOCKER.**

`BACKFILL_FAILURE_DOORS = ("existence-read", "mint")` is a **hand-list**. The shipped
`TaskLedger._backfill_blocks_edges` has **three** failure doors, and the missing one is the
**first line of the function**: `columns, existing = await self._read_mirror_state()`.

The mutation is the single most-written defensive line in any migration — the same sentence WB-O
used, moved up two statements:

```python
try:  # WB-DOOR3: "the backfill must never stop the service booting"
    columns, existing = await self._read_mirror_state()
except Exception:
    logger.warning('task.backfill.read_failed_boot_continues')
    return
```

```
$ uv run pytest -q -n auto -p no:randomly test_blocks_edge.py test_query_tasks_bounded.py
247 passed in 8.83s          <-- THE WHOLE CONTRACT, GREEN
```

**Why A1 does not catch it (and why I expected it to):** the `except` only fires when the read
raises. Undegraded, the backfill works normally, so every coverage pin passes. The defect is
LATENT — and **nothing in this contract degrades the mirror-state read.** A2 degrades the other
two doors and only those.

**Proof it is genuinely wrong — the required pair.** A probe degrading that door in A2's own
name-free idiom (keyed on the statement's property, not a method name):

```
LEG 1, on WB-DOOR3:
  PROBE-DOOR3 refused_statements=1 ensure_ready_raised=None edges_after=[]
  FAILED  -> ensure_ready RETURNED NORMALLY over a failed backfill read

LEG 2, on the CORRECT build (tasks.py md5 532ca756… verified):
  PROBE-DOOR3 refused_statements=1
              ensure_ready_raised=SurrealStoreError('the mirror-state read was rejected…')
              edges_after=[]
  1 passed in 0.31s
```

So the pin is writable, it discriminates, and **it is missing**. The consequence is WB-O's
consequence verbatim: the service boots, the legacy edge set is entirely absent, every legacy row
is served `ids=[] truncated=False` — sidecar S3, the false clear R11 exists to delete.

⚠ **This is the QUANTIFIER LAW recurring inside the class written to fix the quantifier law.**
A2's own header says it is *"stated as a PARAMETRISATION so the next door added here is an entry
rather than a hole."* It is — for doors somebody adds. It is not, for the door already there. And
this is `CLAUDE.md`'s instrument lesson exactly: *"when you catch yourself enumerating what is
FORBIDDEN, you have already lost."* A2 enumerates doors by name; the safe set here is derivable
(§PINS M1).

### P1-2 · **WB-CHUNK — R-13's seventh direction. BLOCKER.**

Chunk the backfill's mint. Coverage is untouched, so A1 is satisfied by construction:

```python
_CHUNK = 50  # WB-CHUNK
for _start in range(0, len(mintable), _CHUNK):
    await self._apply([self._relate_fragment(mintable[_start : _start + _CHUNK])])
```

```
$ uv run pytest -q -n auto -p no:randomly test_blocks_edge.py test_query_tasks_bounded.py
247 passed in 13.03s         <-- THE WHOLE CONTRACT, GREEN
```

**The reproduction, using the contract's OWN instrument** (`TestTheBackfillIsONETransaction.
_boot_traffic`) at four scales:

```
PROBE-CHUNK edges/calls: 2/4   30/4   61/5   122/6
PROBE-CHUNK sibling comparison (2 vs 30):        4 == 4  -> True    <-- what the pin RUNS
PROBE-CHUNK same comparison at A1 scale (61/122): 5 == 6 -> False   <-- what nothing runs
```

**The pin, the instrument and the scale all exist — and are never composed.** A1's stated bound
says it *"measures COVERAGE, never round trips — its sibling `TestTheBackfillIsONETransaction`
owns that question."* That sibling's fixture ceiling is `LEGACY_BACKFILL_EDGES_LARGE = 30`;
A1's floor is 61. **The handoff is false at exactly the scale A1 introduces** — the same class as
Leg-1 row 1's *"CLOSED"*, one level up: a bound stated by pointing at a sibling nobody checked
could reach.

**Positive control** — the sibling pin CAN fire; it is a real pin, merely blind above 30:

```
$ # _CHUNK = 1  (WB-C, one RELATE per edge)
FAILED …TestTheBackfillIsONETransaction::test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges
1 failed
```

**Why it is a genuinely wrong build, beyond hygiene:** a chunked backfill is **not atomic**. A
failure in chunk 2 leaves chunk 1 committed and raises — a half-mirrored store, which is a state
neither A1 (coverage) nor A2 (raises) describes, and which R11's own rationale asserts cannot
happen. `TestTheBackfillIsONETransaction`'s docstring already says an N-writes build makes
PROOF 10b's declared RED set wrong; a chunked build does the same thing at production scale only.

### P1-3 · **WB-EXIST-CAP(40) — A1 adds scale on ONE of the backfill's THREE reads.**

`resolve_existing_rows(self._query, TASK_TABLE, sorted({…})[:40])`.

```
$ uv run pytest -q -n auto -p no:randomly test_blocks_edge.py test_query_tasks_bounded.py
247 passed in 9.15s          <-- THE WHOLE CONTRACT, GREEN
```

**Root cause — this delta's fixture monoculture.** A1's `_seed_star` is a STAR: `count` rows, all
blocked by **one shared root**. So at 61 and at 122 rows the existence read is exercised over
**exactly 1 distinct id**. The only distinct-blocker scale anywhere in the file is the 30-row
CHAIN in `TestTheBackfillIsONETransaction` — **below A1's own floor**. Any cap ≥ 31 is invisible.

**Positive control** — the contract can see this door, at scale ≤ 3:

```
$ # [:3]
9 failed, 196 passed        (incl. TestTheBACKFILLClosesTheLEGACYEdgeGap, TestTheBackfillIsIDEMPOTENT,
                             TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS, both A2/A3 positive controls)
```

**P2 PERTURBATION PAIR — A1's own pin with one axis changed (STAR → FAN, same scale):**

```
LEG 1, on WB-EXIST-CAP(40):
  AssertionError: PROBE-FAN: 21 of 61 legacy edges were NOT minted over a store with 61
  DISTINCT blockers (A1's own scale, one axis perturbed). missing=21
  [+ 21 x WARNING loremaster.tasks task.backfill.phantom_blocker_skipped]

LEG 2, on the CORRECT build (md5 verified):  1 passed in 0.72s
```

⚠ **Second-order harm worth naming:** the wrong build does not merely miss 21 edges — it emits
21 `phantom_blocker_skipped` WARNINGs naming **live** blockers as phantoms. It poisons the exact
operator record A3 exists to make trustworthy, and the packet has no pin on the record's
*truthfulness*, only on its *completeness*.

### P1-4 · **WB-LIMIT200 — A1's discrimination is bounded by a number.**

`… WHERE array::len(blocked_by) > 0 LIMIT 200`.

```
247 passed in 9.84s          <-- GREEN.   (control: LIMIT 50 -> 2 failed, r6's declared WB-E set)
```

A1 compares 61 and 122 with exact-set assertions, so it kills any cap ≤ 122 and no cap above it.
The class docstring's mitigation — *"a cap set above both dies the day the derived floor rises
past it"* — is a promise about a **future edit**, not a property of the pin. This is the weakest
of the four (a builder must type a bigger number), but it is the same defect the whole class was
written to catch, and the fix is cheap (§PINS M4).

**On A1's derived floor, since the brief asked whether the derivation is real:** it is.
`max(30, 2, 60, 5, len(LEGACY_COLUMN_DAG)+2=7) + 1 = 61`, dominated by `UNRELATED_TASK_COUNT_LARGE
= 60`. r6's surveyed claim that the only larger integer constant is `ENGINE_RECURSION_CEILING`
(256, a depth bound) reproduces under my own `grep -nE '^[A-Z_]+ = [0-9]+'`. **The floor is a real
derivation, not a number wearing one** — its bound is stated honestly, and the bound is exactly
what P1-4 and P1-3 exploit.

---

## §QUANT — P1b quantifier table. 13 invariants; every guarded row carries a receipt.

| # | invariant (delta pins only) | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| 1 | A1: every dependency-bearing legacy row is mirrored | **GUARDED** — by scale ≤122 **and** by topology (distinct blockers = 1) | **WB-LIMIT200 survives** (247/0); **WB-EXIST-CAP(40) survives** + FAN pair |
| 2 | A1: no legacy row served a confident empty | **GUARDED** — same two bounds | same two surviving builds |
| 3 | A2: **ANY** backfill failure makes `ensure_ready` raise | **GUARDED — hand-list, 2 of 3 doors** | **WB-DOOR3 survives**, pair proven (§P1-1) |
| 4 | A2: an undegraded boot completes and mints the exact set | ∀ over that fixture | door-build killed: `WB-EXIST-CAP(3)` reddens it (9-failed control) |
| 5 | A2: the mint degradation actually reached its door | ∀ (fails CLOSED — vacuity reddens) | design verified by read; `refused` assertion present |
| 6 | A3: every cycle member is named ∀ topology | **∀ over 3 topologies**, expected set from an INDEPENDENT oracle | WB-CYCLE1 → 4 RED, exact |
| 7 | A3: each DISJOINT cycle gets its own record | **GUARDED to the disjoint topology — bound STATED + re-open trigger** | WB-CYCLE1 reddens it; the guard is deliberate and correct (set-equality would be a C-DEF; §A3) |
| 8 | A3: the disjoint fixture really holds 3 cycles and all edges mirror | ∀ | reddened by `WB-EXIST-CAP(3)` control |
| 9 | A4: write-path read does not grow with the DEPENDENCY-FREE population | ∀ over that population | PROOF 11 → 1 failed / 6 passed, reproduced |
| 10 | A4: write-path read DOES grow with the BLOCKED population (asserts a MISS) | known bound, ∀ over that population | stays GREEN under PROOF 11 — **re-derived by me**, as r6's updated comment claims |
| 11 | A5: a capped listing is byte-identical to a complete one (asserts a MISS) | **GUARDED** to `limit=5`, population 40, one subject | green on shipped build; row-count guard verified to fire first (r6's own §MUT-4 self-catch); **not re-mutated by me** |
| 12 | A5: the normaliser can see a difference | ∀ (positive control) | green |
| 13 | A6: `limit` windows the answer / caps the ANSWER not the scan, ∀ backend | **GUARDED** to `limit=5` on both `[real]` and `[fake]`; short-answer direction probabilistic (≈7e-7) under record-id order — **stated** | r6's WB-FAKE (2 RED) **not re-run by me**; the double's reorder-then-slice verified by read |

**Three guarded rows (1, 2, 3) carry a SURVIVING WRONG BUILD rather than a killed door-build.**
Per the role's rule, that is the INSUFFICIENT verdict.

---

## §PINS — missing pins, ranked. Each: the test that should exist + the defect it catches.

**M1 — `test_a_FAILED_backfill_makes_ensure_ready_LOUD` must be ∀ over a DERIVED door set, not a
hand-list.** *Catches:* WB-DOOR3 (§P1-1) and every future door. *Shape:* the safe set here is
small and enumerable — the backfill's doors are exactly *the store-seam calls reachable from
`_backfill_blocks_edges`*. Derive them (AST over the method's call graph, or — stronger, and the
repo's own preferred instrument — a RUNTIME wrapper that intercepts every `execute_transaction` /
`execute_read_transaction` / `_query` issued during `ensure_ready`, fails the **k-th** one, and
asserts `ensure_ready` raises **for every k**, with the observed k-count asserted so reach is a
*checked* variable). `BACKFILL_FAILURE_DOORS` then becomes an assertion about the derived set's
size, not a curated list. ⚠ Minimum viable version if the derivation is deferred: add
`"mirror-read"` to the tuple with the construction in §P1-1 — but that is the hand-list again, so
name it as an interim with a trigger.

**M2 — `test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges` must run at A1's
scale.** *Catches:* WB-CHUNK (§P1-2). *Shape:* one extra comparison pair at
`LEGACY_BACKFILL_SCALE_FLOOR` and `2 × floor`, in `TestTheBackfillIsONETransaction` — the helper
already exists and takes the count as an argument, so this is a two-line addition. Then A1's
"my sibling owns round trips" handoff becomes TRUE. Measured cost: the 122-edge boot ran in well
under a second.

**M3 — A1 must scale the DISTINCT-BLOCKER axis, not only the row axis.** *Catches:*
WB-EXIST-CAP (§P1-3) and any bound on the existence read. *Shape:* parametrise
`_backfill_at_scale` over topology `{"star", "fan"}` — `_seed_fan` is ~6 lines (my probe is a
working draft) and reuses the same exact-set assertion. The FAN also makes A1 ∀ over the
existence read's own scale for free.

**M4 — the backfill's pending read carries NO `LIMIT`/`START`.** *Catches:* WB-LIMIT200 (§P1-4)
∀ scale rather than up to 122. *Shape:* `measure_store_traffic` already captures `statements`;
assert no statement issued during `ensure_ready` that names the dependency-bearing filter also
matches `\bLIMIT\b|\bSTART\b`. ⚠ **Fair warning, and it is why I rank this LAST:**
`TestTheBackfillIsONETransaction`'s docstring records a deliberate decision *against* statement-text
pins (*"a pin demanding the literal token `BEGIN` would redden a build that composes the same
guarantee differently"*). That reasoning is weaker here — `LIMIT` is a *forbidden* token, not a
required one, so an honest build composing differently does not trip it — but it is a live design
tension and **the lead should rule rather than have a builder guess.**

---

## §LEG1 — re-measurement. Rows 1 and 2 were rewritten after being measured false.

**ROW 1 — the correction is STILL FALSE. MEASURED.** The rewritten predicate reads
*"the tasks reachable UPSTREAM over the `blocks` EDGES **this ledger's last completed
`ensure_ready` mirrored** … at this ledger, as of this read."*

```
PROBE-LEG1  (virgin ledger: ensure_ready mirrors 0 edges, there are no legacy columns)
  ensure_ready()  ->  0 edges mirrored
  create_task(blocker); create_task(dependent, blocked_by=[blocker])
  transitive_blockers(dependent).ids = ['1921f38e0d23401a8be1cf799a72684c']
  1 passed
```

The response is non-empty over a mirrored set that is **empty**. The read rides *every* edge the
ledger holds — those `ensure_ready` mirrored **plus every dependency written since** (`create_task`
/ `create_many` mint edges in the same transaction as the row). The row now names a strict
**subset** of the set the response is true of.

⚠ **Why this is not pedantry, and why the brief's warning was right.** Row 1's whole job is
difference (a): *edges vs the `blocked_by` COLUMN agree*. As written, it says the read covers only
the boot-mirrored subset — which would mean edge ≢ column for **every post-boot write**, the exact
opposite of the invariant SECTION K pins. A consumer acting on it without checking concludes a
dependency created after boot is invisible to `transitive_blockers`. r6 replaced a false
one-word claim (*"CLOSED"*) with a false predicate, and the predicate now carries a measurement
receipt, which makes it harder to doubt. **Suggested true form:** *"…over the `blocks` edges this
ledger holds — every `blocked_by` column the last completed `ensure_ready` mirrored, plus every
dependency written since — at this ledger, as of this read"*, keeping difference (a)'s existing
⚠ clause about a PARTIAL or swallowed migration unchanged.

**ROW 1, second defect: the row misquotes its own predicate.** Its commentary says *"⚠ The
predicate above says *'a COMPLETED migration'*…"*. The predicate above says
*"this ledger's last completed `ensure_ready` mirrored"*. Same class, one level smaller: prose
describing prose, unchecked.

**ROW 2 — CORRECTED AND NOW TRUE. Re-measured, two ways.** (i) The construction is pinned and
green on the shipped build (`TestACappedListingDISCLOSESNothingAboutItsOwnBOUND`, inside my 247).
(ii) Its sub-claim *"nor which five (no ORDER is pinned, so the choice is arbitrary and
unstable)"* — verified against production: `_candidate_statement` composes
`SELECT * FROM task [WHERE …] [LIMIT $k]` with **no `ORDER BY`**, and on the `blocked is None`
path the `LIMIT` is pushed to the engine. The claim is a FACT about the code. ✅

**ROW 3 — unchanged, and it remains the model.** *"at this ledger"* + *"as of the check"*, both
facts, no disclaimer word. Nothing to report.

**ROW 4 (`send` sender guard) — unchanged, verified unchanged by diff. No verdict owed.**

**ROW 5 (cycle refusal) — NEW, and I could not falsify it.** It claims the guard walks the COLUMN
so an edge-only cycle is invisible; `_read_dependency_graph` reads
`blocked_by` and nothing else. The R7-rider justification (a closing dependency cannot carry an
edge) is the packet's own ruling, cited not re-argued. ✅

**ROW 6 (migration's operator record) — NEW, TRUE as far as it goes, with an unnamed difference
I am escalating as a residual.** It correctly names per-BOOT/per-READ scope and the now-∀ cycle
record. ⚠ It does **not** name that the record can be **false** as well as partial: §P1-3 measured
21 live blockers reported as `phantom_blocker_skipped`. The row describes the record's
completeness; nothing describes its truthfulness. See §RESID-1.

**ROW 7 (`ensure_ready`'s normal return) — NEW, and FALSE.** It says *"DIFFERENCE: none is
carried, and none needs to be — because the claim is enforced rather than disclosed: any failure
of the backfill, at ANY of its doors, makes the call RAISE."* **WB-DOOR3 falsifies that sentence
directly** (§P1-1): a failure at the mirror-state door returns normally. The row inherited A2's
hand-list and restated it as a universal — the quantifier law, propagating from a pin into the
scope diff that cites it. **Fixing M1 fixes this row; fixing this row without M1 is a rewording.**

**Leg 1's own stated bound is preserved and I did not weaken it** — sound on *set* and
*predicate-as-WRITTEN* only. Note that rows 1 and 7 failed on **set** and on
**predicate-as-WRITTEN** respectively, i.e. inside the two things Leg 1 claims soundness on, not
in the believed part.

---

## §A3 — the oracle, and the networkx question the brief asked

- **Is `networkx.simple_cycles` genuinely a TEST-side oracle?** **YES, verified.** The expected
  set is computed from the FIXTURE SPEC (`_independent_cycles(spec)` takes
  `LEGACY_CYCLE_TOPOLOGIES[topology]`), never from production output, so the contract cannot hand
  the build its own answer key. **Does a build that hard-codes cycle enumeration pass?** No — the
  disjoint per-cycle leg is asserted against a hard-coded `LEGACY_DISJOINT_CYCLE_MEMBERS`, and the
  positive control asserts *the oracle agrees with that constant*, so the two enumerations are
  cross-checked rather than either trusted. This is the strongest new class in the delta.
- **Has networkx leaked into a production import path?** **No import has.** Grep over
  `loremaster/loremaster`, `lorescribe`, `loresigil`, `lorerunes`, `scripts`: zero hits. Every hit
  in the repo is in `loremaster/tests/test_blocks_edge.py`. **But the DEPENDENCY has — see §E1.**
- **The complete-triangle bound (shipped 4 records vs `nx`'s 5) is correctly handled.** Pinning
  set-equality would redden an honest build; r6 pins member coverage ∀ topology + per-cycle
  records on the disjoint topology only, states the bound, and names a re-open trigger. I tried to
  break this and could not: WB-CYCLE1 reddens all four legs.

## §A4 — the narrowing. Verified, and it holds.

The brief asked whether narrowing a pin's *name and message* left it still catching something,
and whether the message now matches the assertion. Both check out.

```
$ # PROOF 11's mutation: drop `WHERE array::len(blocked_by) > 0` from _read_dependency_graph
FAILED …TestCreateRefusesToFormACycle::test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_DEPENDENCY_FREE_population
        assert 64 == 9   (rows read: 9 -> 64)
1 failed, 6 passed, 198 deselected
```

- The **renamed** pin still fires under the mutation it was written for. ✅
- The **new KNOWN_BOUND** pin stays GREEN under that same mutation — exactly as r6's updated
  PROOF 11 comment predicts, **re-derived here rather than inherited.** ✅
- **Message vs assertion:** the assertion is `large.rows == small.rows` over
  `_seed_unrelated_tasks` (UNBLOCKED rows); the message now says *"unrelated DEPENDENCY-FREE
  tasks"* and explicitly hands the other axis to the KNOWN_BOUND sibling **by name**. The false
  gate is closed — the message no longer promises a ∀-ledger check the assertion cannot perform. ✅

**A4 is the one item on the attack list that came back clean, and I am saying so with receipts
rather than omitting it.**

## §A6 — the shared seeder

Sharing is real by construction: `_task_fakes.seed_answer_cap_sandwich` is the single
implementation, `test_query_tasks_bounded.py`'s `_sandwich_ledger` binds it to a live ledger and
`test_task_ledger.py`'s `_sandwich` to both backends; the constants stay per-caller so each file's
probability argument still describes its own fixture. I did **not** re-run r6's PROOF 7 (5 reds
spanning both files) — stated, not inherited. What I did verify by read: the fake's
`query_tasks` computes the `blocked` partition over ALL rows and slices **last**, so `[fake]` is
held to T1 rather than teaching around it, and the reverse-id sort makes the sandwich shape
load-bearing rather than decorative.

---

## §P2 — fixture discrimination. This delta's monoculture axis.

| fixture | can it tell right from wrong? | verdict |
|---|---|---|
| `_seed_star` (A1, 61/122 rows) | **NO on the distinct-blocker axis** — 1 distinct blocker at every scale | **FINDING.** Perturbation pair proven (STAR→FAN): RED on WB-EXIST-CAP(40), GREEN on the correct build. §P1-3 |
| `_seed_star` (row-count axis) | YES up to 122, NO above | **BOUNDED.** WB-LIMIT200 survives; control at 50 reddens. §P1-4 |
| `legacy_column_store` (A2's fixture) | YES for the 2 listed doors, **NO for the third** | **FINDING.** WB-DOOR3. §P1-1 |
| `LEGACY_CYCLE_TOPOLOGIES` (A3, 3 topologies) | **YES** — a record-the-first build fails all three, differently | **DISCRIMINATES.** WB-CYCLE1 → 4 RED |
| `LEGACY_DISJOINT_CYCLE_MEMBERS` | YES, and cross-checked against the oracle by the positive control | **DISCRIMINATES** |
| `_blocked_noise_traffic` (A4 KNOWN_BOUND, 5 vs 60 pairs) | YES — growth comparison, not a threshold | **DISCRIMINATES**; stays green under PROOF 11 as designed |
| `_create_many_traffic` (A4 renamed pin) | YES | **DISCRIMINATES** — PROOF 11 → 1 RED |
| A5's two worlds (40-capped-to-5 vs 5) | YES for row-count differences (positive control proves the normaliser is not flattening) | **DISCRIMINATES** within its stated bound |
| `seed_answer_cap_sandwich` (A6, 66 rows / 6 unblocked / cap 5) | YES — population strictly exceeds the cap on both backends | **DISCRIMINATES** |
| **`limit` VALUE across the whole delta** | `_ANSWER_CAP = 5`, `_LIMIT_CAP = 5`, A5 reuses `_ANSWER_CAP` — **every new limit pin uses 5** | **RESIDUAL, secondary.** §RESID-2 |
| legacy row STATUS in the new fixtures | `_seed_star` and `_seed_topology` are both `STATUS_OPEN`-only | **COVERED ELSEWHERE** — `LEGACY_TERMINAL_TASK` owns that axis in SECTION K; noted, not a finding |

**The axis, stated once:** r6 was asked for SCALE and delivered scale **on the axis the defect had
been measured on** (row count). The backfill has three reads; A1 scales one of them.

---

## §E — escalations

**E1 — `networkx` is in the RUNTIME dependency set for a TEST-ONLY oracle. LEAD/OPERATOR CALL.**

```
loremaster/pyproject.toml:39:    "networkx>=3.6.1",     <- [project] dependencies
```

Every use is in `loremaster/tests/test_blocks_edge.py`; production imports it nowhere (grepped,
§A3). The repo's own house idiom is stated verbatim two files away, for `markdown-it-py` in root
`pyproject.toml` `[dependency-groups] dev`: *"It is dev-only because nothing shipped imports it."*
Consequence: networkx is now installed into the deployed image as a `loremaster` runtime
dependency. **I am not calling this settled** — the operator authorised the install at `54d0585`,
and r6's finding #273 proposes moving production's hand-rolled all-cycle enumeration ONTO
networkx, which would make the runtime placement correct in advance. The fork:
(i) move to `[dependency-groups] dev` now, and move it back if #273 is ruled in; or
(ii) leave it, on the strength of #273. **My recommendation: (i)** — a runtime dependency with
zero runtime importers is exactly the state a future `dead_code`/image audit will flag, and #273
is unruled. Either way this is one line and it is **outside the contract author's writable set**,
which is why it survived r6.

**E2 — my own capability gap (see the header).** `contract-adversary` still cannot reach
`lore_comms`/`lore_findings`. Finding #266 is not closed for this role. **A lead must transcribe
the findings below.**

---

## §FINDINGS — four, UNFILED, needing lead transcription (I could not file them; §E2)

| # | category | area | body |
|---|---|---|---|
| F1 | defect (contract) | `loremaster/tests/test_blocks_edge.py` | `BACKFILL_FAILURE_DOORS` is a hand-list of 2 doors; `_backfill_blocks_edges` has 3. WB-DOOR3 (`try/except` on `_read_mirror_state`) passes 247/0. Pair proven. Fix = M1 (derived/runtime door set). |
| F2 | defect (contract) | `loremaster/tests/test_blocks_edge.py` | A1's stated bound delegates round trips to `TestTheBackfillIsONETransaction`, whose fixture ceiling (30) is below A1's floor (61). WB-CHUNK(50) passes 247/0; round trips 4/4/5/6 at 2/30/61/122. Fix = M2. |
| F3 | defect (contract) | `loremaster/tests/test_blocks_edge.py` | A1's `_seed_star` holds distinct blockers at 1 at every scale, so the backfill's existence read is unscaled. WB-EXIST-CAP(40) passes 247/0; FAN perturbation pair proven. Fix = M3. |
| F4 | defect (docs/contract) | `test_blocks_edge.py` module docstring (Leg 1) | Row 1's corrected predicate names only `ensure_ready`-mirrored edges; measured, a virgin boot mirrors 0 and the read serves 1. Row 7 asserts ∀-doors over a 2-of-3 hand-list. Row 1 also misquotes its own predicate. |

---

## §RESID — residuals, one line each, individually adjudicated

| # | item | verdict |
|---|---|---|
| RESID-1 | The operator record can be FALSE, not merely partial — WB-EXIST-CAP made 21 live blockers report as `phantom_blocker_skipped`; A3 pins the record's completeness, nothing pins its truthfulness | **OPEN, ESCALATED.** Closed as a side effect of M3; if M3 is deferred, this wants its own pin (no `phantom_blocker_skipped` may name a row that EXISTS). |
| RESID-2 | Every new `limit` pin in the delta uses 5 (`_ANSWER_CAP`, `_LIMIT_CAP`, A5) — parameter-value monoculture on the exact parameter the delta is about | **ACCEPTED, LOW.** I could not construct a plausible build that branches on the limit VALUE; recording it because repo law says one pin should use a different value, and none does. |
| RESID-3 | `_record_legacy_cycles` is unreachable on a re-boot: `_backfill_blocks_edges` returns early when `missing` is empty, so a store whose edges already exist records no cycles | **NOT A DEFECT of the delta — but UNPINNED and UNNAMED.** Leg-1 row 6 says "per-BOOT", which is *weaker* than the truth ("per boot that has work to do"). Flagging, not fixing. |
| RESID-4 | r6's proofs #2 (WB-O), #4 (WB-RENDER), #5 (WB-FAKE), #6 (WB-BOUNDED) | **NOT RE-RUN BY ME.** Stated rather than relayed as verified. The 3 I did re-run reproduced exactly, which is weak positive evidence for the other 3, not proof. |
| RESID-5 | r6's R-10 (the delta adversary's `_ENGINE_REJECTION_MODES` prose: four "engine reasons" where there are three classes; a timeout described as "ran and was cut off" where the engine says "was not executed") | **STILL OPEN**, unchanged by r6 by its own admission. Both are one-line docstring corrections. Lead's call; cheap. |
| RESID-6 | r6's R-11 (mis-indented `subject=` continuation in `TestCreateRefusesToFormACycle`) | **STILL OPEN**, cosmetic, `ruff` clean over it. Confirmed still present. |
| RESID-7 | r6's R-12 (the `wrong-instance` verb named as a re-open trigger but never CONSTRUCTED) | **STILL OPEN.** r6 mitigated it in PROSE only (row 1 gained "at this ledger"). The Leg-2 construction is still owed; ⚠ and row 1's prose is now false for a different reason (§LEG1). |
| RESID-8 | r6's R-1/#272 (`types-networkx` absent → inline `# type: ignore[import-untyped]` where the house idiom is a `pyproject.toml` override) | **CONFIRMED PRESENT**, gates green (`typecheck.sh` EXIT=0). Same one-line-outside-writable-set shape as §E1 and should be fixed in the same commit. |
| RESID-9 | r6's ESC-1 (write-path rows vs the BLOCKED population) and ESC-5 (who closes the capped-listing false clear) | **CORRECTLY ESCALATED, NOT MINE TO SETTLE.** I confirm both are real design forks and that r6 implemented only the unambiguous half of each. No new information from me. |
| RESID-10 | `test_mcp_server.py` 641 / whole-tree suite | **641 REPRODUCED** (inside my 881). I did **not** re-run the whole tree (the delta adversary's 7707); out of my scoped set and stated rather than implied. |

---

## VERDICT: **CONTRACT INSUFFICIENT**

Four wrong builds survive the r6 delta at **247 passed / 0 failed** each, three of them through
holes in the pins r6 wrote, and R-13's seventh direction is real in two independent forms. The
minimum to reach SUFFICIENT is **M1 + M2 + M3** (M4 needs a lead ruling first, and Leg-1 rows 1
and 7 follow from M1).

**What I could NOT break, said plainly so the lead knows where the strength is:** A3's ∀-topology
cycle class (I attacked its oracle, its decomposition bound and its fixture and it held on all
three); A4's narrowing (both directions re-derived); A5's normaliser (its positive control is
real); and the satisfiability of the whole contract against the shipped build — **there is no
fourth C-DEF.** r6 built six good pins. It also inherited, in `BACKFILL_FAILURE_DOORS` and in
`_seed_star`, the exact shape of the defect it was closing.
