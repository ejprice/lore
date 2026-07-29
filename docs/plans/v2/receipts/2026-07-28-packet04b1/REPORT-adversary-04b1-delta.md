# REPORT-adversary-04b1-delta — grading the r5 DELTA, and Leg 1 for the first time

brief-base v7 read

trust hard-definition read

Its two askable questions, quoted verbatim from `CLAUDE.md` § *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"*** (Leg 1 — SCOPE DIFF)

> **Ask: *"what broken state of this tool would serve exactly these bytes?"*** (Leg 2 — FORGERY
> PINS)

*Every claim in this file was DERIVED by running, on **2026-07-28**, against branch
`feat/surreal-unification` at commit **`0782450`** (`078245087525e3958af3664a9a9b216e7975b88d`).
Every live probe hit spike-surreal `ws://127.0.0.1:18000` (TEST); `:18500` was never touched. No
number below is inherited — where I re-derived somebody else's number and it differed, I say so.*

**Scratch provenance (finding #140):** baseline extracted from the COMMIT, never the working
tree (`git archive 0782450 | tar -x`), then `uv sync --all-packages`, then the repo's own guard:

```
$ /home/ejprice/scratch-adv-04b1-delta/.venv/bin/python scripts/scratch_provenance.py /home/ejprice/scratch-adv-04b1-delta
  loremaster  -> /home/ejprice/scratch-adv-04b1-delta/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch-adv-04b1-delta/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch-adv-04b1-delta/lorescribe/lorescribe/__init__.py
  lorerunes   -> /home/ejprice/scratch-adv-04b1-delta/lorerunes/lorerunes/__init__.py
PROV_EXIT=0
loremaster.__file__ = /home/ejprice/scratch-adv-04b1-delta/loremaster/loremaster/__init__.py
```

I made no edit of any kind inside `/home/ejprice/PycharmProjects/lore` except this report, and I
ran no git state-mutating command there.

---

## SUMMARY BLOCK

- **VERDICT ON THE DELTA: CONTRACT INSUFFICIENT.** The six r5 pins are *correctly built* — all
  three of the wave's mutation proofs reproduce EXACTLY, both ways — but two NEW wrong builds
  survive the committed contract whole, and Leg 1 carries two claims measurement contradicts.
- **P1 HEADLINE — TWO wrong builds survived, 234 passed / 0 failed each.** **WB-E**: a backfill
  with `LIMIT 50` on its pending read — measured to serve **10 of 60** legacy rows
  `ids=[] truncated=False` while the claim CAS refuses them, sidecar S3's exact false clear.
  **WB-O**: a `try/except` around the backfill's MINT only — `ensure_ready` returns OK with the
  whole legacy edge set silently absent. §P1.
- **LEG-1 VERDICT (the first anyone has given): INCOMPLETE, 2 of 4 rows FALSE, 3 surfaces
  missing a row.** Row 1 says the edge-vs-column difference is *"CLOSED"* — WB-E and WB-O both
  re-open it while passing the contract. Row 2 says *"No unnamed difference remains"* for
  `query_tasks` — MEASURED: `lore_tasks action=query limit=5` against a 40-row ledger renders 5
  rows and **nothing** saying the listing is partial. Row 3 is the strongest row in the repo and
  I say why. §LEG1.
- **MISSING PINS, ranked** (each with a reproduction): 1 backfill coverage above the 30-row
  fixture ceiling · 2 a failed MINT makes `ensure_ready` loud · 3 **every** legacy cycle is
  recorded, not just the first · 4 the write path's rows-read vs the BLOCKED population · 5 a
  capped `query` render discloses its own bound · 6 the double's new `limit` slice is
  unexercised. §PINS.
- **P1b QUANTIFIER TABLE — 13 invariants classified, every guarded row carrying a receipt.**
  §QUANT.
- **P-PKG DIFF — the survey is honest and reproduces on all six graph shapes; ONE mechanism is
  unsurveyed:** *enumerate ALL cycles*, which ESC-4's RECORD half needs. `graphlib` reports
  exactly one (measured). `networkx` is NOT INSTALLED → escalate for authorization, never code
  around. §PKG.
- **SATISFIABILITY: 234 passed / 0 failed** on my own reference build, **and after `ruff --fix`**;
  ruff clean; `typecheck.sh` EXIT=0; neighbours 73 passed / 19 skipped. §SAT.
- **ITEM 8, THE FOURTH C-DEF OPPORTUNITY: NO FOURTH C-DEF.** `test_mcp_server.py` **641 passed**
  independently, and the whole tree **7707 passed / 36 skipped / 3 xfailed / 0 failed**. §CDEF.
- **P4 — r5's own numbers: the mutation proofs reproduce EXACTLY (2/2, 3/3, 2/2). Its headline
  RED count does NOT: `163 failed / 69 passed` (=232) where the committed contract collects 234
  and runs 165 failed / 69 passed.** §P4.
- **Escalations: 4** (§ESC-1 write-path rows may be undecidable under R7 · §ESC-2 the R7 read
  sibling trips the retry-label gate, undisclosed · §ESC-3 `networkx` install · §ESC-4 Leg-1
  row 1's wording). **Friction for the lead to transcribe: 2** (§FRICTION).

---

## §SAT — satisfiability, on MY OWN reference build

The brief forbids grading with the fixer's build, so my reference build's production code is the
**prior adversary's** (`/home/ejprice/scratch/adv04b1f-ref`, an independent author), copied into
my `0782450` baseline — production is byte-identical between `bce3042` and `0782450`
(`git diff --stat bce3042..0782450 -- loremaster/loremaster/` is empty), so the transplant is
sound. I then repaired one genuine defect in it (§ESC-2). I did not read
`REPORT-contractfix-04b1-r5.md` before designing my probes.

```
$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py
234 passed in 8.44s

$ uv run ruff check --fix .   ;   uv run ruff check .
All checks passed!                RUFF_EXIT=0

$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK (171 files) · skills OK
MYPY_EXIT=0

$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_enforced_relations.py \
      loremaster/tests/test_derivation_source_unification.py
73 passed, 19 skipped in 6.16s
```

The three pins `test_enforced_relations.py` is *deliberately* reddened by are GREEN on a correct
build, exactly as the contract's RED-BY-DESIGN section says.

**Collection is 234 node ids at `0782450`, with pristine production AND with the reference
build** (`--collect-only` run under both) — so no parametrisation is production-derived and the
counts below compare like with like.

---

## §CDEF — item 8: the fourth opportunity, and there is no fourth C-DEF

r5 claims *"a builder now meets ZERO red tests outside this contract"*, citing
`test_mcp_server.py` 641 passed. That claim is **suite-wide in scope**, so I verified it
suite-wide rather than in the one file it cites.

```
$ uv run pytest -q -n auto -p no:randomly loremaster/tests/test_mcp_server.py
641 passed in 107.00s (0:01:46)

$ uv run pytest -q -n auto -p no:randomly loremaster/tests lorescribe loresigil lorerunes
7707 passed, 36 skipped, 3 xfailed, 1 warning in 359.09s (0:05:59)
```

**VERDICT: item 8 holds.** Independently reproduced, and no C-DEF anywhere in the tree.

Two failures appeared on my FIRST suite run and both were mine, not the contract's — recording
them because a P0 control that fires on the auditor is the only kind worth trusting:

1. `test_text_hygiene.py::test_no_tracked_text_file_contains_a_NUL` — *"the file enumeration
   (git ls-files) found only 0 text files"*. My `git archive` baseline had no git index. **The
   pin's own coverage guard caught my instrument**, which is exactly what that guard is for.
   Fixed by tracking the tree; re-run green.
2. `test_retry_seam.py::TestEveryCallIntoTheRetryDriverIsAttributable::test_every_call_into_the_driver_passes_a_label`
   — `store/_txn.py … execute_read_transaction()` passes no `label=`. That is a defect in the
   **reference build**, not the contract; its failure message names the fix verbatim. Repaired
   (`retry_on_conflict(_attempt, label="store.read_transaction", url=url)`); re-run:
   `567 passed` over `test_retry_seam.py` + `test_text_hygiene.py`. See §ESC-2 — it is
   undisclosed, and every 04b-1 builder will meet it.

**Re-authored pins, individually adjudicated** (item 8 weakened assertions in a file it does not
own; each needs its own verdict, not a bulk pass):

| pin | what changed | verdict |
|---|---|---|
| `test_since_on_a_non_rollup_action_is_rejected` | exact-equality → `"since" in message` | **ACCEPTABLE.** The exact-value corpse check moved, and I verified it is really there: `test_query_tasks_bounded.py::TestLimitIsLEGALForQueryAtTheToolSeam` holds `RETIRED_CLAIM = "'since'/'limit' apply only to action='rollup'"` and asserts `RETIRED_CLAIM not in message`. |
| `test_limit_on_a_non_query_non_rollup_action_is_rejected` | `action="query"` → `action="create"` | **ACCEPTABLE.** R9 makes the old assertion false; the guard-ordering rationale (strict-parameter guard runs before required-arg checks) is stated and correct. |
| `test_intra_batch_cycle_is_refused_and_NAMES_every_member` | `raises(ValueError)` → `raises(Exception)`, message → substring | **ACCEPTABLE, on evidence.** `raises(Exception)` alone would admit a build that misclassifies the cycle as unknown-keys. It does not, because the CLASS is pinned against a REAL ledger by `TestTheCyclePolicyHasONEImplementation::test_a_BATCH_KEY_cycle_at_the_TOOL_SEAM_raises_the_LEDGERS_cycle_CLASS`, which asserts `type(caught.value) is expected` where `expected` is DERIVED from the ledger's own raised value. Verified present and asserting exactly that. |
| `_task_fakes.FakeTaskLedger.query_tasks` gains `limit` | new parameter + slice | **DEFECT — decoration.** See §PINS-6. |

---

## §P1 — the wrong builds. Two survived the whole contract.

### WB-E — the CAPPED backfill (BLOCKER)

One token, in the backfill's pending read, for the most plausible reason in this packet: 04b-1
is *about* bounded reads (#253, R9, R7), and a builder who has just been told "no read may scale
with the ledger" writes a cap.

```python
f"FROM {TASK_TABLE} WHERE array::len({_COL_BLOCKED_BY}) > 0 LIMIT 50"
```

```
$ uv run pytest -q -n auto -p no:randomly test_blocks_edge.py test_query_tasks_bounded.py
234 passed in 11.24s
```

**Its consequence, MEASURED** (probe: 60 legacy `blocked_by` rows, columns only, no edges, then
one `ensure_ready`, then traversal-vs-CAS per row):

```
AssertionError: 10 of 60 legacy rows were served a CONFIDENT EMPTY (ids=[] truncated=False)
while the claim CAS refuses them — sidecar S3's false clear, restored at a scale no contract
fixture reaches. first=['wait5_0aaec9f9…', 'wait6_68050404…', 'wait7_7f50f9ba…']
```

**POSITIVE CONTROL — the probe can see a cap, and this is where the ceiling is.** With
`LIMIT 25`:

```
FAILED …TestTheBackfillIsONETransaction::test_the_BOOTs_round_trips_do_NOT_grow_with_the_number_of_LEGACY_edges
E  AssertionError: the two boots minted 2 and 25 edges where their columns call for 2 and 30.
1 failed, 233 passed in 10.57s
```

Exactly ONE pin, and it fires only through its own *fixture-drift* guard — a check written for a
different purpose. **So the contract's entire ceiling on backfill coverage is
`LEGACY_BACKFILL_EDGES_LARGE = 30`, and it is incidental.** Any cap ≥ 31 is invisible; so is any
partial backfill from any cause. `TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS` says in its own
docstring that *"any backfill filter — present, future, or not yet imagined — whose skip makes
the traversal disagree with the CAS dies here"*. It is ∀ over five SHAPES and its fixture holds
six rows; it is not ∀ over SCALE, and WB-E walks straight through it.

### WB-O — the SWALLOWED MINT (BLOCKER)

The single most-written defensive line in any migration: *"the backfill must never stop the
service booting."*

```python
        if fragments:
            try:
                await self._apply(fragments)
            except Exception:
                logger.warning("task.backfill.mint_failed_boot_continues", extra={"pending": len(fragments)})
```

```
234 passed in 12.42s
```

**POSITIVE CONTROL — the same swallow, one level out** (around the whole
`_backfill_blocks_edges()` call, so it also covers the existence read):

```
FAILED …TestTheBackfillRoutesThroughTheSHAREDExistencePolicy::test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill
FAILED …TestTheBackfillRoutesThroughTheSHAREDExistencePolicy::test_a_FAILED_existence_read_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL
2 failed, 232 passed in 11.93s
```

That is the quantifier attack landing cleanly. The invariant the contract *needs* is **"any
failure of the backfill makes `ensure_ready` raise"**; what it pins is **"a failure of the
EXISTENCE READ makes `ensure_ready` raise"** — conditioned on the failure mode that was
debugged. Same bad outcome (boot succeeds, edge set silently partial, S3 restored on every
legacy row), different door, no pin.

---

## §PINS — the missing pins, ranked. Each is a test the author can go write.

**1. `test_a_legacy_store_LARGER_THAN_EVERY_OTHER_FIXTURE_is_backfilled_ENTIRELY`**
*Catches:* WB-E and every other partial backfill. Seed N legacy dependency-bearing rows where N
is derived from *"one more than the largest fixture in this file"* rather than typed, boot once,
assert the minted edge set is EXACTLY the column's — and assert no row is served a confident
empty it cannot claim. Discriminate by GROWTH (two sizes) so a builder cannot tune a threshold.
*Receipt:* WB-E → 234/0; the 10-of-60 probe above; `LIMIT 25` control → 1 red, via a drift guard.

**2. `test_a_FAILED_MINT_makes_ensure_ready_LOUD_not_SILENTLY_PARTIAL`**
*Catches:* WB-O. Degrade the WRITE seam (not the existence read) — the file already owns
`_degrade_every_STORE_seam` — and require `ensure_ready` to raise. Better still, restate the
invariant ∀ over the backfill's failure modes and parametrise over `{existence read, mint}`, so
the next door added is a parametrisation entry rather than a new hole.
*Receipt:* WB-O → 234/0; WB-O2 control → 2 red.

**3. `test_EVERY_legacy_cycle_is_RECORDED_not_just_the_FIRST`**
*Catches:* the operator log's own confident empty. ESC-4's load-bearing half is *"The RECORD is
what stops it being silent"*, and every cycle fixture in the contract — `TestALEGACYCycleIsMINTEDAndRECORDED`
and `TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED` alike — holds **exactly one cycle**. That
is a third monoculture axis, beside the two r5 closed (ARITY, LIFECYCLE STATE): **CYCLE COUNT.**
*Receipt, on the CORRECT reference build (no mutation needed — this is what a correct build
does):*

```
test_POSITIVE_CONTROL_ONE_legacy_cycle_IS_recorded                     PASSED
test_PROBE_TWO_disjoint_legacy_cycles_are_BOTH_recorded                FAILED
E  AssertionError: a legacy store with TWO disjoint cycles left 2 of 4 cycle members unnamed
   at WARNING: unnamed=['grp1_0_8185ced3…', 'grp1_1_e90c239b…']
   loud=["task.backfill.legacy_cycle_mirrored {'cycle': 'grp0_0_7490… -> grp0_1_7af3… -> grp0_0_7490…',
         'members': ['grp0_0_7490…', 'grp0_1_7af3…']}"]
```

The edges for BOTH cycles minted correctly; only the RECORD is short. And this is not bad luck —
§PKG shows it is precisely what the contract's own recommended library does.

**4. `test_the_WRITE_paths_rows_READ_does_NOT_grow_with_the_BLOCKED_population`**
*Catches:* #253 on the write path, for the population that actually grows. r5's new pin is named
*"…does NOT grow with the size of the LEDGER"* and its failure message says *"the write path is
scaling with the LEDGER — that is #253, on the WRITE side"*, but its noise helper
(`_seed_unrelated_tasks`) mints **unblocked** rows, and the guard's read is filtered
`WHERE array::len(blocked_by) > 0`. So the pin varies the one population the filter excludes.
*Receipt, on the CORRECT reference build:*

```
E  AssertionError: a create_many naming ONE blocker read 9 rows against 5 blocked noise pairs
   and 64 against 60.
   statements=('SELECT id FROM $agent_ids', 'SELECT … superseded_by FROM task WHERE … IN $sup_ids',
               'SELECT record::id(id) AS id, blocked_by FROM task WHERE array::len(blocked_by) > 0',
               'BEGIN; CREATE …; RELATE …; COMMIT;')
```

⚠ **This one is an ESCALATION as well as a missing pin** — see §ESC-1. The fix may not be
available to a builder. But the pin's *message* promising a check the assertion cannot perform
is a false gate under this repo's own P2 law regardless of how the design question lands.

**5. `test_a_CAPPED_query_render_DISCLOSES_that_the_listing_is_PARTIAL`**
*Catches:* the Leg-1 hole in §LEG1 row 2. *Receipt:* §LEG1.

**6. `test_the_fakes_limit_applies_to_the_ANSWER_after_the_BLOCKED_partition`**
*Catches:* the double teaching a contract it is never held to. §PINS-6 receipt:

```
mutation A — delete the fake's `limit` slice entirely:
  $ pytest -q -n auto test_mcp_server.py test_task_ledger.py     875 passed in 184.08s
mutation B (CONTROL) — delete the fake's `status` filter, same files:
  FAILED test_task_ledger.py::TestQueryTasks::test_status_filter_is_exact[fake]
  FAILED test_task_ledger.py::TestQueryTasks::test_filter_matching_nothing_is_honest_empty_list[fake]
  2 failed, 873 passed in 104.75s
```

So the `[fake]` half **can** go RED — the control proves it — and the new `limit` slice **cannot**.
Worse, the loss is directional: r5 added the parameter to fix two pins that drove it
(`tasks(action="query", limit=5)`), then re-pointed both of those pins to `action="create"`. Net,
the `[fake]` seam **lost its only `limit` coverage and gained an unexercised slice**, whose
docstring nonetheless teaches *"THE CAP APPLIES TO THE ANSWER, NEVER TO THE CANDIDATE SCAN"*.
(The end-to-end property is still pinned once, against a real ledger, by
`TestTheLimitIsPUSHEDINTOTheStatement::test_the_TOOL_SEAM_passes_the_limit_through_to_the_ledger` —
so this is a decoration defect, not an open door.)

---

## §QUANT — P1b: every invariant classified, every guarded row with a receipt

| # | invariant | ∀-over-inputs / GUARDED | receipt |
|---|---|---|---|
| 1 | the backfill mirrors the column, ∀ rows | **GUARDED — by ROW COUNT** (no fixture exceeds 30) | **WB-E survives 234/0**; 10/60 rows confidently empty; `LIMIT 25` control reddens 1 pin via a drift guard. **BLOCKER** |
| 2 | a backfill failure makes `ensure_ready` LOUD | **GUARDED — by FAILURE MODE** (the existence read only) | **WB-O survives 234/0**; WB-O2 control reddens 2. **BLOCKER** |
| 3 | a legacy cycle is RECORDED | **GUARDED — by CYCLE COUNT = 1** | 2 of 4 members unnamed on the *correct* build; 1-cycle control passes. **BLOCKER** |
| 4 | the mirror holds ∀ blocker LIFECYCLE states | **∀** (r5 closed this axis) | WB-B declared 3 → observed 3, exact; WB-H declared 2 → observed 2, exact |
| 5 | the mirror holds ∀ cycle ARITIES | **∀ over {1,2,3}** | WB-A declared 2 → observed 2, exact; **both `[arity-3]` legs stayed GREEN**, the asymmetry that proves the arities discriminate different doors |
| 6 | the traversal AGREES with the claim CAS | **∀ over 5 SHAPES, GUARDED by SCALE** | WB-E walks through it (row 1); WB-H also does, and the contract *records that itself* under PROOF 10h |
| 7 | the write path's rows-read does not grow with the ledger | **GUARDED — by the noise being UNBLOCKED** | 9 → 64 rows on the correct build |
| 8 | a rejected read RAISES, never `[]` | **∀ over 4 constructed modes** (3 distinct engine classes — §RESID-1) | all four raise `SurrealStoreError` through `_query`; the ONE `[]`-returning shape is pinned as a bound with a re-open trigger and a working positive control |
| 9 | `query_tasks` serves no invented TOTAL | **∀** (asserted emptiness + `return []` control) | reproduced GREEN; the control is real |
| 10 | ONE cycle policy, shared | **∀, proved by MUTATION** | the shared-formatter sentinel pin reproduced; both call sites observe one substitution |
| 11 | ONE row-existence policy, shared | **∀, proved by MUTATION** | `test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill` reddens under WB-O2 |
| 12 | the served `query` render names its own scope | **UNPINNED** | measured: no disclosure at `limit=5` of 40 (§LEG1) |
| 13 | the double's `limit` applies to the ANSWER | **UNPINNED — decoration** | slice deleted → 875 passed; control → 2 red |

---

## §LEG1 — the SCOPE DIFF, graded for the first time

**Where it lives.** Only in `test_blocks_edge.py`'s module docstring (the *"LEG 1 — the scope
diff for the surfaces THIS packet serves"* block). `test_query_tasks_bounded.py` has **no Leg-1
material at all** (`grep -n "LEG 1\|SCOPE DIFF\|leg 1\|scope diff"` → only a leg-2 mention). Its
surface is covered by reference from the other file's row 2, which is acceptable — but a reader
opening the `#253` addendum alone meets no scope diff, and that should be a pointer at minimum.

**Row-by-row.**

**Row 1 — `transitive_blockers(task_id)`. VERDICT: the row's own difference (a) is FALSE as
written.** It says the *edges vs the `blocked_by` COLUMN* difference is *"**CLOSED** by ruling
R11's backfill"*. Leg 1 is a claim about the RESPONSE, and two builds that pass this contract
whole leave it open (WB-E, WB-O). The honest wording is a FACT, not a widening: *"…over the
`blocks` edges **this ledger's last completed migration mirrored**"*. Differences (b) `truncated`
/ `max_depth_used` and (c) the phantom residue are correct, carried, and pinned — (c) especially,
which is a model bound: asserted, controlled, and carrying a named re-open trigger.
Minor: unlike row 3, row 1's predicate does not say *"at this ledger"*, so a wrong-database read
is an unnamed difference here where row 3 names it.

**Row 2 — `query_tasks(…, limit=…)`. VERDICT: *"No unnamed difference remains"* is FALSE,
measured.** The named differences (one-hop-not-transitive, answer-cap-not-scan-cap) are real and
pinned. The unnamed one is the difference a *consumer* actually faces:

```
$ lore_tasks action=query limit=5   # against a ledger holding 40 matching tasks
- [open] backlog 6 (id 0923dbbb…, owner None, blocked_by [])
- [open] backlog 8 (id 0b333236…, owner None, blocked_by [])
- [open] backlog 33 (id 0f7b603b…, owner None, blocked_by [])
- [open] backlog 26 (id 2217978d…, owner None, blocked_by [])
- [open] backlog 20 (id 270c2f48…, owner None, blocked_by [])
```

Five rows. Nothing says the listing is partial; nothing says which five (the file explicitly
declines to pin ORDER, so the choice is arbitrary and unstable). **The reader is an AGENT.** One
that acts on this without checking concludes the ledger holds five open tasks — wrong in a way
the response did not name, which is the hard definition's failure condition verbatim. Note the
tell is `len(rows) == limit`, and note what the fix is **not**: `TestNoTOTALIsServedThatWasNotMEASURED`
is right that the LEDGER must not invent a total, and nothing here asks it to. A FACT suffices —
*"showing the 5 you asked for; there may be more"* — which needs no count and no extra read.
Missing pin 5.

**Row 3 — the blocker pre-check refusal. VERDICT: CORRECT, and the best row of the four.**
*"these ids name no LIVE task row **at this ledger**, **as of the check**"* names both the
wrong-instance difference (a mis-set `database` serves the same bytes) and the TOCTOU window,
without a single disclaimer word. This is what the other three rows should look like.

**Row 4 — the `send` sender guard. VERDICT: CORRECT.** *"this sender id names no `agent` row"*,
in the message ledger's own vocabulary; E-4's rationale is sound and pinned.

**MISSING ROWS — three served surfaces with no row at all:**
1. **The cycle refusal** (`format_cycle_refusal` / `TaskCycleError`). Answers *"these ids close a
   cycle in the `blocked_by` COLUMN as of one snapshot"*; asked *"why was my create refused?"*.
   Differences that need naming: it walks the COLUMN, so a cycle present only in EDGES is
   invisible; and the batch-key and persisted-id vocabularies deliberately differ (R6 permits it)
   — which is exactly a scope difference a caller must be told about.
2. **The migration's operator record** (the WARNING stream). r5 itself treats this as a served
   surface — pin 3 exists precisely so the record does not teach something false — yet it has no
   Leg-1 row, and missing pin 3 is the difference that row would have caught: it answers *"ONE
   cycle I found"* while the operator reads *"the cycles in your store"*.
3. **`ensure_ready`'s own normal return.** Its consumer is the booting service, which reads it as
   *"this store is migrated"*. WB-O makes that false.

**On Leg 1's stated bound:** the contract states it correctly and does not over-claim — *sound on
set and predicate-as-WRITTEN only; time, environment and predicate-as-EXECUTED are BELIEVED*.
Credit where due. But rows 1 and 2 fail on the axis Leg 1 *is* sound on — the predicate as
written — so the bound does not rescue them.

---

## §P4 — verifying r5's claims rather than relaying them

**The three mutation proofs the wave wrote for the wrong builds it inherited, run against the
COMMITTED contract, diffed both ways:**

```
WB-A / PROOF 10e (skip the SELF-loop: `if blocker == task_id: continue`)
  declared RED 2 → observed RED 2, exact match:
    TestALegacyCycleOfEVERYARITYIsMINTEDAndRECORDED::…MINTED_as_an_EXACT_edge_set[arity-1]
    TestTheTRANSITIVEReadAGREESWithTheCLAIMCAS::…CLAIMABLE_whenever_the_traversal_is_EMPTY
  both [arity-3] legs stayed GREEN, as declared.        2 failed, 232 passed

WB-B / PROOF 10f (subtract SUPERSEDED before the skip record)
  declared RED 3 → observed RED 3, exact match, including the placement-sensitive third leg:
    …SUPERSEDED_task_is_STILL_MIRRORED · …CLAIMABLE_whenever… · …SKIP_is_never_RECORDED_as_a_PHANTOM…
                                                          3 failed, 231 passed

WB-H / PROOF 10h (skip TERMINAL blockers)
  declared RED 2 → observed RED 2, exact match:
    …TERMINAL_task_is_STILL_MIRRORED[done-blocker] · [wontfix-blocker]
  $W stayed GREEN, exactly as the contract PREDICTS and records as its own finding.
                                                          2 failed, 232 passed
```

**VERDICT: the six pins were implemented AS SPECIFIED, not subtly narrower — including pin 2,**
the R10(ii)×R11 interaction the brief singled out. Its three-leg declared set reproduces
exactly, and the third leg is placement-sensitive in the way the contract says it is. This is
genuinely good work and I could not weaken it.

**The one number that does NOT reproduce.** `REPORT-contractfix-04b1-r5.md` §DECLARED reports
`total failed: 163 passed: 69` (= 232). The committed contract collects **234** and, against
pristine `0782450` production, runs:

```
$ uv run pytest -q -n auto -p no:randomly test_blocks_edge.py test_query_tasks_bounded.py
165 failed, 69 passed in 8.31s
```

The 19-node declared/observed diff the report actually leans on is sound (19 declared, 19
matched — I have no quarrel with it). But the headline total describes a tree with two fewer node
ids than the one that was committed: the measurement predates the final edit. Per this repo's own
law — *re-derive every number you inherit* — the number that describes the artifact is
**165 failed / 69 passed over 234 collected**.

---

## §PKG — my table first, then the diff

Built before opening r5's. Mechanisms the contract specifies:

| mechanism | evaluated | what I **READ / RAN** | verdict |
|---|---|---|---|
| detect a cycle in `blocked_by`, name its members | `graphlib.TopologicalSorter` (stdlib); `networkx` | RAN six shapes: 2-cycle `['a','b','a']`, self-loop `['x','x']`, 3-cycle `['a','c','b','a']`, diamond `None`, outside-ref `None`; `issubclass(CycleError, ValueError) == True`. `inspect.getsourcefile` → `/usr/lib/python3.14/graphlib.py` | **replace** (stdlib) |
| **enumerate ALL cycles** (ESC-4's RECORD half) | `graphlib`; `networkx.simple_cycles` | RAN `{a↔b, p↔q}` → `graphlib` returns `['a','b','a']` — **one cycle, silently**. `prepare()`'s own docstring: *"If any cycle is detected, CycleError will be raised"*. `importlib.util.find_spec('networkx')` → **NOT INSTALLED** | **UNSURVEYED BY THE CONTRACT — see below** |
| transitive closure of the DAG | the engine's `+collect` | the packet's own probe receipts (P4, settled) | **replace** (engine-native) — agrees |
| retry / conflict classification at the store seam | `tenacity` (installed); the repo's `retry_on_conflict` | repo law #102 + `test_retry_seam.py`'s runtime gate | **keep_with_trigger** — trigger: a second retry policy appearing anywhere outside the driver |
| round-trip / rows instrumentation | `_surreal_harness.measure_store_traffic` | its docstring + `doors`/`unobserved` reach check | **reuse, no new copy** — agrees |
| degraded-state construction | `pytest` `monkeypatch` + `caplog` | the file's `_degrade_every_STORE_seam`, conftest caplog propagation | **replace** — agrees |
| order-preserving dedup | `dict.fromkeys` (stdlib) | used throughout | **replace** — agrees |

**THE DIFF.** r5's survey line is honest, has a real read-column, and reproduces exactly on all
six graph shapes — I re-ran every one. **The gap is a mechanism neither table names:**
*enumerate ALL cycles*. The recorded verdict answers *"is there a cycle, and name one"*, which is
what the write-time GUARD needs; ESC-4's rider is *"MINTS legacy cycles **and RECORDS them**"*,
plural, which is a different question. The survey answered the narrower one, and missing pin 3 is
that same gap seen from the code side — **the recommended library, used exactly as recommended,
produces the defect.** `networkx` is not installed; per the packages rule that is grounds to
escalate for authorization (§ESC-3), never to code around — and a bespoke Tarjan/SCC pass is the
legitimate other side of the rule only after that escalation is answered.

---

## §RESID — residuals, each with its own verdict

- **RESID-1 — `_ENGINE_REJECTION_MODES` claims four DIFFERENT engine reasons; there are THREE
  classes.** Measured at the RPC layer: `malformed-statement` → `{"error":{"kind":"Validation",
  "message":"Parse error: Unexpected token `AT`…"}}` and `unknown-function` → `{"error":
  {"kind":"Validation","message":"Parse error: Invalid function/constant path…"}}` are the **same
  class**, and both are the parse-error shape item 7 exists to retire. `absent-table-SCANNED` →
  per-statement `status=ERR kind=NotFound`; `cut-off-by-TIMEOUT` → per-statement `status=ERR
  kind=Query`. **VERDICT: an inaccurate claim in an instrument's own docstring, harmless to the
  property** — the two classes a FIXED statement string can actually take are both covered, so
  item 7's correction is real. Fix the sentence, not the set.
- **RESID-2 — the same table calls the timeout mode *"a statement that ran and was cut off"*.**
  Engine text: *"The query was **not executed** because it exceeded the timeout: 1ns"*.
  **VERDICT: false description; one-line fix.**
- **RESID-3 — item 7's KNOWN BOUND is a real bound, not a hole in a bound's clothes.**
  Independently constructed with its own control: absent table → `status=OK result=[]`; existing
  table + missing row → `status=OK result=[]`; existing table + real row → resolves. Byte-identical
  worlds, correctly characterised, correctly scoped to *"the table exists"* (which `ensure_ready`
  guarantees by applying DDL before the backfill reads), and carrying a re-open trigger that
  really would redden. **VERDICT: SOUND. The best single artifact in the delta.**
- **RESID-4 — corpse sweep, 12 hits for the retired sentence, individually adjudicated.**
  `REPORT-contractfix-04b1-r3.md:327`, `REPORT-contractfix-04b1.md:269`,
  `REPORT-contractfix-04b1-r5.md:269`, `REPORT-adversary-04b1-final.md:584` → historical record,
  correct. `docs/design/2026-07-28-04b-model-consumer-audit.md:47` and `:326` → the audit's own
  narrative of the pre-R9 world, correct. `test_query_tasks_bounded.py:119`, `:1042`, `:1147`,
  `:1402` → prose describing the world the fix leaves, each explicitly dated/labelled, correct.
  `test_query_tasks_bounded.py:1427` → the `RETIRED_CLAIM` constant, used in a **negative**
  assertion at `:1462`, correct and load-bearing. `test_blocks_edge.py:8095` → PROOF 9's
  `--anchor`, correct. `test_mcp_server.py:6959` → a `RE-AUTHORED` docstring quoting what it used
  to assert, correct. **VERDICT: ZERO live assertions pin the corpse.** Corpse 2
  (`create_many items contain a blocked_by cycle among batch keys` / `a cyclic batch can never be
  claimed`) → one hit, `test_blocks_edge.py:2069`, a class docstring quoting the pre-R6 behaviour
  it is retiring. Correct.
- **RESID-5 — the law's `wrong-instance` verb is NAMED as a re-open trigger for the existence
  probe but never CONSTRUCTED.** §11.1 is a declared curated interim, so this is inside the
  contract's stated bound. **VERDICT: within bound, but flag it** — the trigger is reachable
  *today* by a mis-set `database` in config, not hypothetically, and Leg-1 row 3's *"at this
  ledger"* wording is currently the only thing standing between that state and a false clear.
- **RESID-6 — `TestCreateRefusesToFormACycle::test_POSITIVE_CONTROL_a_legal_CHAIN_in_one_batch_LANDS`
  has a mis-indented `subject=` continuation line.** `ruff check` is clean over it.
  **VERDICT: cosmetic; tidy at leisure.**
- **RESID-7 — branch reachability (P3) of the persisted-id cycle guard.** I suspected it was
  unreachable through the real entry points (`create_task`/`create_many` mint `uuid4` ids, so a
  fresh id cannot already be named by a persisted `blocked_by`). It is **reachable at the LEDGER**
  via `create_many(..., ids=[caller_supplied])`, which the contract's own pin uses, and it is
  **honestly pinned as UNREACHABLE at the TOOL SEAM** by
  `test_a_PERSISTED_ID_cycle_is_UNREACHABLE_at_the_TOOL_SEAM_by_construction`.
  **VERDICT: considered and cleared — the scope narrowing is stated, not silent.**
- **RESID-8 — the dangling-edge hazard (store reference §6.4).** `TaskLedger` exposes no delete
  or purge verb (`ensure_ready`, `close`, `create_task`, `get_task`, `query_tasks`,
  `transitive_blockers`, `claim_task`, `transition`, `supersede_task`, `updated_since`,
  `create_many`), so a `blocks` edge cannot outlive its endpoint through this surface.
  **VERDICT: considered and cleared.**
- **RESID-9 — the `[fake]` half CAN fail** (control: 2 reds from the `status` filter), so the
  parametrisation is not decoration in general. Only the r5 addition is. **VERDICT: see
  §PINS-6.**

---

## §ESC — escalations. I settled none of these.

**ESC-1 — is a ledger-independent write-path cycle read even AVAILABLE under R7's rider?** The
guard reads `SELECT … FROM task WHERE array::len(blocked_by) > 0` — every dependency-bearing row
in the ledger, on every create. R7's rider mandates ONE round trip, and the class docstring
argues (correctly) that an ENGINE traversal cannot serve as the detector because the closing
dependency cannot carry an edge. Those two constraints together may make a bounded client-side
walk impossible. Two readings, both written down as brief-base §2 requires:
 (i) *the property is achievable* — bound the read to the ancestor closure of the NEW
 dependencies (they are persisted, so their upstream chains DO carry edges after this packet),
 leaving only the batch-local part client-side. Then missing pin 4 is a real defect and the
 reference build is wrong.
 (ii) *the property is not achievable at one round trip* — then the pin's NAME and failure
 message must be narrowed to what it measures (*"does not grow with the UNBLOCKED population"*),
 and the residual cost documented as a bound with a re-open trigger.
**I would pick (i)** and ask for it to be measured before it is ruled. Either way the current
message is a false gate. **Lead's call; this is a design question, not mine.**

**ESC-2 — the R7 read sibling trips a gate the contract does not disclose.** ESC-2 of the prior
wave put `store/_txn.py` in the builder's writable set. Any `execute_read_transaction` that calls
`retry_on_conflict` without `label=` reddens
`test_retry_seam.py::TestEveryCallIntoTheRetryDriverIsAttributable::test_every_call_into_the_driver_passes_a_label`
— reproduced here, on the reference build, naming `store/_txn.py:…execute_read_transaction()`. It
is **not a C-DEF** (the builder fixes it in production, and the failure message is excellent), so
item 8's claim survives — but it is a red test outside the contract that a correct build meets,
and the RED-BY-DESIGN section should say so in one line: *"pass `label=` and `url=`."*

**ESC-3 — `networkx` install authorization** for §PKG's unsurveyed mechanism. Not to be coded
around by an agent; the operator rules.

**ESC-4 — Leg-1 row 1's *"CLOSED"*.** A one-word claim doing a lot of work. My recommendation is
the row 3 treatment: state the fact (*"over the edges this ledger's last completed migration
mirrored"*), and let missing pins 1 and 2 do the closing.

---

## §FRICTION — for the lead to transcribe (I have no MCP tools; see below)

**F-1 — the brief's own prescribed baseline breaks 65 tests at COLLECTION.** `git archive <sha> |
tar -x` yields a tree with no `.git`, and `loremaster/tests/test_surreal_schema.py` calls
`subprocess.check_output(["git", "rev-parse", "HEAD"])` at **module import time** (`GIT_REF` /
`GIT_BRANCH` are module-level). Result: 64 collection errors in that file plus one in
`test_trace_telemetry.py` (which imports it), and `test_text_hygiene.py` scans **0** files —
caught only because that pin has a coverage guard (`assert len(paths) > 200`). `scratch_copy.sh`
does not have this problem because it keeps `.git`. Suggested brief wording for next time:
*"`./scripts/scratch_copy.sh <abs-dest>` then `git -C <dest> checkout <sha> -- .`"*, or an explicit
`git init && git add -A && git commit` step after `git archive`. Two notes worth keeping: the
test's git dependency is #131's shape one level up (a tool the environment may not provide, at
import time), and the text-hygiene guard is a model of why coverage must be a *checked variable*.

**F-2 — tool honesty.** As my brief anticipated, this agent has no `ToolSearch` and no
`mcp__lore_*` tools. Every code-structure question in this report was answered by `grep` +
direct file reads, and every claim by execution. Nothing was filed to `lore_findings`; F-1 and
the numbered findings above need a human or tool-equipped agent to ledger them.

---

## §HOW-I-TRIED — the probes that did NOT break it

Recorded because a verdict with only successes is not believable.

- **The no-op fix.** Looked for a symbol the contract demands that nothing requires the code to
  CALL. `TestTheBackfillRoutesThroughTheSHAREDExistencePolicy` is name-free by construction — it
  neutralises the shared module's coroutines and requires the backfill to notice — so the L3
  sharing cannot be faked by a call that goes nowhere. Reproduced RED under WB-O2.
- **The cosmetic fix.** Tried to make the edge set *look* right while the state was wrong: the
  MINTED pins assert **exact sets**, so a superset (closure-minting) and a subset (skip) both die.
  Confirmed on WB-A/WB-B/WB-H.
- **Fixture arithmetic alignment.** Checked whether `LEGACY_BACKFILL_EDGES_SMALL=2` /
  `LARGE=30` make any branch unreachable — they do not for the round-trip property, and the pin
  asserts the minted count at both sizes before comparing. Sound. (The 30 does cap coverage — but
  that is finding 1, a scale hole, not an arithmetic one.)
- **Cycle-arity discrimination.** Verified `[arity-1]` and `[arity-3]` are not one pin wearing two
  ids: under WB-A, `[arity-1]` reddens and `[arity-3]` stays GREEN — the asymmetry the contract
  claims, measured.
- **The `∀`-agreement pin's vacuity guards.** It asserts `any(confident_empty)`,
  `not all(confident_empty)`, and `any(claimed) and not all(claimed)`. I tried to construct a
  fixture drift that would make the implication vacuous; the three guards close it. Good pin.
- **The `RETIRED_CLAIM` negative assertion.** Tried to satisfy it with a build that merely
  reworded the sentence — it asserts the substring `'since'/'limit' apply only to
  action='rollup'` is ABSENT, so a reword passes, which is correct: the claim is what is retired,
  not a spelling.
- **`_ENGINE_REJECTION_MODES` reachability.** Attacked it as *"did item 7 repeat the failure it
  fixed?"* — partially yes (RESID-1) but not consequentially: the two reachable classes are both
  covered and both raise.

---

## §REPRO — every command, in order, for anyone re-running this

```bash
mkdir -p /home/ejprice/scratch-adv-04b1-delta
git -C /home/ejprice/PycharmProjects/lore archive 0782450 | tar -x -C /home/ejprice/scratch-adv-04b1-delta
cd /home/ejprice/scratch-adv-04b1-delta && uv sync --all-packages
./.venv/bin/python /home/ejprice/PycharmProjects/lore/scripts/scratch_provenance.py "$PWD"   # EXIT 0
git init -b feat/surreal-unification . && git add -A -- . ':!.venv' && git commit -m base     # F-1
# reference build: production files from the PRIOR ADVERSARY's independent build at bce3042
#   (production is byte-identical bce3042..0782450), plus the label repair of §ESC-2.
uv run pytest -q -n auto -p no:randomly loremaster/tests/test_blocks_edge.py \
    loremaster/tests/test_query_tasks_bounded.py            # 234 passed
uv run pytest -q -n auto -p no:randomly loremaster/tests lorescribe loresigil lorerunes
                                                            # 7707 passed, 36 skipped, 3 xfailed
# wrong builds: WB-E (LIMIT 50 on the backfill's pending read) and WB-O (try/except around
#   `await self._apply(fragments)`), each re-running the two contract files.
```

---

## VERDICT

# CONTRACT INSUFFICIENT (on the DELTA)

Not because the r5 wave did poor work — it did unusually good work, and I could not weaken any
of the six pins it added: three mutation proofs reproduced exactly, both directions, and the
fourth C-DEF opportunity came back clean at 7707/0. It is INSUFFICIENT because closing six named
holes did not close the CLASS, and the class is the same one every time: **an invariant stated
over a set, verified over one member of it.** Row count ≤ 30. Failure mode = the existence read.
Cycle count = 1. Noise population = unblocked. And Leg 1, graded here for the first time, carries
the same shape in prose — *"CLOSED"* and *"no unnamed difference remains"* are both claims about a
whole set, and both are contradicted by a measurement.

The six missing pins in §PINS are the concrete work. §ESC-1 is a design fork the lead must rule
before pin 4 can be written honestly.
