# REPORT-coldaudit-04b1 — the independent COLD REFUTE audit of packet 04b-1

brief-base v8 read
brief project v7 read

**comms:** registered `coldaudit-04b1` (session `pkt04b-20260728`, role `auditor`, model
claude-opus-5, task `e48347a9020945efb5725e16ae1e73c3`); `drain` → no unread messages.
**Findings filed BY ME: #275, #276** (not lead-transcribed).

## CAPABILITY CHECK (brief-base v8 §4) — **NO GAP**

Every instrument the brief demands was reachable and used: `ToolSearch` resolved the five
`mcp__lore_lore__*` tools on the first call (so the `contract-adversary` gap reported in
`REPORT-adversary-04b1-r6.md` §CAPABILITY CHECK does **not** reproduce for this agent type);
`lore_comms` register/drain and `lore_findings report` both worked; `Bash`, `Read`, `Write`,
`git` (read-only), `ruff`, `typecheck.sh`, `pytest`, and spike-surreal
`ws://127.0.0.1:18000` were all available. **`:18500` (PRODUCTION) was never contacted, not
even read-only.** I mutated no git state and read none of the `/home/ejprice/scratch*`
reference builds. I did not need `./scripts/scratch_copy.sh`: every probe I ran is
**read-only against the production tree** (constructed stores in throwaway databases, plus
runtime instrumentation of a live object) — no production file was mutated, so the #140
poison modes do not arise. `loremaster.__file__` is printed as a receipt on every probe.

*One honest fallback, said out loud (§4): several structural questions — the ruling-vs-code
sweep, the `BACKFILL_FAILURE_DOORS` hand-list, the `networkx` placement — were answered by
`grep`/`Read` rather than by lore. Two of the three are repo-law-sanctioned grep cases
(non-symbol textual seams: a tuple literal's members, a `pyproject.toml` section, prose in
docstrings). The third (the rulings sweep) is a cross-cutting multi-question map, also
sanctioned. No lore weakness was routed around.*

**trust hard-definition read.** Its two askable questions, verbatim from `CLAUDE.md`
§ *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"***

> **Ask: *"what broken state of this tool would serve exactly these bytes?"***

*Every number in this report was DERIVED by running it, on **2026-07-29**, on branch
`feat/surreal-unification` at HEAD **`2116c9f`**, against spike-surreal 3.2.1
(`ws://127.0.0.1:18000`, TEST). Nothing is inherited; where I re-derived somebody else's
number I say whether it matched.*

```
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
```

---

## SUMMARY BLOCK

- **VERDICT: GO.** No packet-blocking defect. The shipped build does what the rulings say.
- **#274's CLEAN-BUILD CLAIM — I INDEPENDENTLY CONFIRM IT, and by a stronger instrument than
  the two before me.** All six survivor shapes absent, established three ways: a DERIVED AST
  call-closure (39 fns, not a hand-list); RUNTIME capture of the actual wire statements at
  N=60 (no `LIMIT` on any read, all 60 `RELATE`s in ONE txn, round trips constant 3 at N=3
  and N=60); and a **DERIVED DOOR SWEEP** — fail the k-th store call for every k, reach
  asserted — **4 doors, ALL RAISE**, with a positive control. §2.
- **#274 QUANTIFIED (new, filed as #276): the pin's hand-list reaches 2 of the 4 doors that
  exist**, and the derived instrument that closes it is ~40 lines and already written. Leg-1
  row 7 is therefore **TRUE of the shipped build** (measured) — r6 graded it FALSE against the
  builds the *contract* admits, which is a different question. §2.3.
- **CONFIRMED DEFECT, ranked #1 and the only one: Leg-1 row 1's predicate is FALSE at HEAD**
  (filed #275). Measured: a virgin `ensure_ready` mirrors **0** edges, yet `transitive_blockers`
  serves a post-boot dependency. The row names a strict SUBSET of what the response is true of,
  and as written it asserts the INVERSE of the invariant SECTION K pins. It survived r6's
  grading unfixed. **Prose defect in the contract, not a build defect; 04b-1 does not deploy.** §4.
- **R11 DIRTY-STORE MIGRATION: PASSES, all six legs**, on a legacy world I constructed myself
  (pre-04b-1 schema → raw column-bearing rows → new boot): 8 edges minted · phantom SKIPPED and
  RECORDED at WARNING naming both ids · **both** a 2-cycle and a 3-cycle MINTED and RECORDED ·
  idempotent on second boot · ONE transaction · S3's confident empty gone. §3.
- **LEG 2 re-runs, both load-bearing ones, by CONSTRUCTION:** world A (no backfill) serves
  `ids=[] truncated=False` vs world B's `ids=['c','b','a']` — **byte-different, no false
  clear**; pre-check degraded to `{empty}` over a store that HOLDS the row → fail-CLOSED,
  blocker named, **nothing written** (counted on a separate admin connection), with a positive
  control that DID write. §5.
- **GATES, all three re-run by me, unpiped, exits captured:** `typecheck.sh` **EXIT=0** (all 5
  members OK) · `ruff check .` **`All checks passed!` EXIT=0** · full suite
  **`8256 passed, 36 skipped, 3 xfailed` in 210.62s, EXIT=0**. ⚠ Builder reported 8237;
  **8237 + r6's 19 new pins = 8256** — reconciles exactly, no discrepancy. §1.
- **T5:** 6 further consecutive runs, **3 passed / exit 0 each**, corroborating 20/20. §6.
- **Removed-behaviour inventory: 8/8 verdicts TRUE of the code.** §7.
- **Rulings vs code: R3/R5/R6/R7/R9/R10/T1/T5/E-1/E-3/E-4/L3 all verified in the build.** §8.
- **escalations: 3** (all §9) — none blocking, none silently settled.
- **receipt pointers:** §1 gates · §2 the #274 verdict · §3 dirty store · §4 the defect ·
  §5 Leg 2 · §6 T5 · §7 inventory · §8 rulings · §9 escalations · §10 RESIDUALS (one line each).
- **Packages considered:** none — no mechanism specified. This audit built no production
  mechanism; its probes are stdlib-only (`ast`, `asyncio`, `logging`) plus the repo's own
  `_surreal_harness`. The build's own package choices (`graphlib.TopologicalSorter` for both
  cycle detectors; the engine's `+collect` for closure; `_txn`'s shared driver for the read
  transaction; `networkx` as a TEST-only oracle) I verified rather than re-surveyed — see §8.5.

---

## 1. The gates, re-run by me

```
$ ./scripts/typecheck.sh
Success: no issues found in 3 source files      typecheck: lorerunes  OK
Success: no issues found in 27 source files     typecheck: lorescribe OK
Success: no issues found in 35 source files     typecheck: loresigil  OK
Success: no issues found in 171 source files    typecheck: loremaster OK
Success: no issues found in 12 source files     typecheck: skills     OK
TYPECHECK_EXIT=0

$ uv run ruff check .
All checks passed!                              RUFF_EXIT=0

$ uv run pytest -q -n auto                      # unpiped, exit captured
8256 passed, 36 skipped, 3 xfailed, 1 warning in 210.62s (0:03:30)
SUITE_EXIT=0
```

**On the count delta.** `REPORT-builder-04b1.md` reports `8237 passed`. I measure **8256**.
The difference is **+19**, which is exactly the size of r6's contract delta (19 new pins,
landed after the builder's run). Re-derived rather than assumed: the builder's number and mine
are both correct at their own trees. **There is no unexplained discrepancy** — and I record the
reconciliation because an inherited count that merely *looks* wrong is how a real one hides.

---

## 2. #274 — my independent verdict on the clean-build claim

**The brief named this the place to look hardest, and it is where most of my effort went.**
The operator's acceptance of finding #274 rests on one claim: *the shipped build is clean of
every known survivor shape.* The lead checked it by AST; the stage-2 adversary re-checked it.
**I am the third instrument, and I did not repeat their method** — a third AST read by a third
reader is a third opinion, not a third instrument.

### 2.1 A DERIVED closure, not a hand-list

I derived the call closure from `TaskLedger.ensure_ready` by binding `self.X` against
`TaskLedger`'s own members and bare names against the module's imports — **39 functions**
(a bare-name over-approximation gave 266; both were run, and the precise one is reported
because the loose one is noise, not rigour). Survivor-class constructs on that closure, each
with its own verdict — *no wholesale classification*:

| construct | site | verdict |
|---|---|---|
| `try/except TxnContentionExhaustedError` | `_txn._run_verified_transaction` | **re-raises** (`raise` bare, after logging). Not a swallow. |
| `try/except (*_CONNECTION_ERRORS, KeyError)` | `_txn._txn_query_raw` | **re-raises** as `SurrealConnectionError ... from error`. |
| `try/except _CONNECTION_ERRORS` ×3 | `_txn.bootstrap_session` | session bootstrap self-heal; re-raises. |
| `try/except RetryableConflictSignal` | `_txn.retry_on_conflict` | **IS the retry driver** — the mechanism, not a door. |
| `try/except graphlib.CycleError` | `tasks.find_blocked_by_cycle` | **IS the detection mechanism** (the library signals a cycle by raising). |
| `try/except TxnContentionExhaustedError, _CONNECTION_ERRORS` | `tasks._ensure_connection` | connection hygiene; re-raises. |
| `try/except _CONNECTION_ERRORS` | `tasks._safe_close` | close-path tolerance; no backfill reachability. |
| slice `stripped[:-len(_STATEMENT_TERMINATOR)]` | `_txn._assert_envelope_integrity` | strips ONE trailing `;`. Not a cap. |
| `range(len(cycle) - 1)` | `tasks._drop_one_cycle_edge` | walks a cycle's own members. Not chunking. |
| int literal `2` | `_txn._txn_conflict_backoff_seconds` | the exponential-backoff base. Not a cap. |
| `'TIMEOUT'` in a string | `agent_existence.resolve_existing_rows` | **docstring prose**, not emitted SQL. |

**`_backfill_blocks_edges`, `_read_mirror_state`, `_record_legacy_cycles`, `_relate_fragment`
and `resolve_existing_rows` carry ZERO try/except, zero `LIMIT`, zero chunking.**

**The one cap that IS on the path**, surfaced by scanning ALL_CAPS constants rather than by
eyeballing: `_txn.TXN_STATEMENT_HARD_CAP = 5000`. It is **loud, not silent** —
`compose()` raises `SurrealStoreError("composed transaction has N statements, exceeding the
hard cap ... refused before anything was sent to the server")`. A store with >5000 un-mirrored
edges fails the BOOT; it does not mint a silent short set. That is escalation E-C's bound,
correctly characterised, and it fails in the safe direction.

### 2.2 RUNTIME capture — what actually goes on the wire

Stronger than any AST read, because it observes what *executes*. Instrumenting `query_raw` on
a live ledger over a constructed legacy store of **60** edges:

```
scale= 60 edges -> 3 round trips
  BEGIN; SELECT record::id(id) AS id, blocked_by FROM task WHERE array::len(blocked_by) > 0;
         SELECT record::id(in) AS blocker, record::id(out) AS blocked FROM blocks; COMMIT;
  SELECT id FROM $row_ids
  BEGIN; RELATE $rel0_from->blocks->$rel0_to; ... ; RELATE $rel59_from->blocks->$rel59_to; COMMIT;
scale=  3 edges -> 3 round trips        (identical statement shapes)
```

- **No `LIMIT` / `START` on the pending read.** (kills WB-LIMIT200 ∀ scale)
- **No `LIMIT` on the edge read or the existence read.** (kills WB-EXIST-CAP)
- **All 60 `RELATE`s in ONE `BEGIN … COMMIT`.** (kills WB-CHUNK)
- **Round trips constant at 3 across a 20× edge-count change.** R11's one-transaction
  rationale is TRUE of this build, measured at scale rather than at a fixture ceiling.

### 2.3 The DERIVED DOOR SWEEP — and it settles r6's Leg-1 row 7

`BACKFILL_FAILURE_DOORS = ("existence-read", "mint")` is a **two-element hand-list**, and
r6's WB-DOOR3 showed a third door (`_read_mirror_state`) that the contract cannot see. Rather
than add a third name — *"when you catch yourself enumerating what is FORBIDDEN, you have
already lost"* — I built the receiver-blind runtime instrument the repo's own instrument
lesson prescribes: intercept **every** store call issued during `ensure_ready` over a legacy
store, fail the **k-th**, assert `ensure_ready` RAISES, **for every k**, with the observed
call count asserted so **reach is a checked variable**.

```
POSITIVE CONTROL: ensure_ready made 4 store calls, raised=None, edges=2
DERIVED DOOR SET: 4 store calls during ensure_ready over a legacy store.
  door k=1: RAISED  InjectedStoreFault  (calls observed 1, edges after -1)   # DDL apply
  door k=2: RAISED  InjectedStoreFault  (calls observed 2, edges after  0)   # mirror-state read
  door k=3: RAISED  InjectedStoreFault  (calls observed 3, edges after  0)   # existence read
  door k=4: RAISED  InjectedStoreFault  (calls observed 4, edges after  0)   # the mint
ALL 4 DERIVED DOORS FAIL LOUD — no silent backfill door on the shipped build.
```

**Two conclusions, and the distinction between them is the point:**

1. **Leg-1 row 7's sentence — *"any failure of the backfill, at ANY of its doors, makes the
   call RAISE"* — is TRUE OF THE SHIPPED BUILD.** Measured over the derived door set, with a
   positive control. r6 graded that row **FALSE**; **I do not concur, and the disagreement is
   about the question, not the fact.** r6 graded it against the space of builds the *contract*
   admits (WB-DOOR3 passes 247/247), which is a true and important finding about the
   *instrument*. It is not a finding about the *build*. Row 7 is a Leg-1 row, and Leg 1 is a
   claim about the **response this code serves** — which is what I measured.
2. **The instrument is nonetheless insufficient, exactly as #274 says**, and now with a number:
   **the pin reaches 2 of the 4 doors that exist.** Filed as **#276**, together with the
   working sweep, so 04b-2 inherits a build rather than a design problem.

**VERDICT ON #274's ACCEPTANCE: the claim it rests on holds.** Clean of `LIMIT`/cap on the
pending read, cap on the existence read, chunked mint, `try/except` swallowing a door, and —
by derivation rather than by a longer hand-list — **any door beyond the two named**. Not a
NO-GO.

---

## 3. R11's backfill on a DIRTY store — constructed by me, six legs

I did not use the contract's fixtures (that would re-install the contract's blind spot). I
built production's real sequence: **apply the 14 pre-04b-1 DDL statements** (every task
statement except the `blocks` relation table, which did not exist before this packet) → **raw
CREATE** column-bearing rows with no edges → **boot the new code**.

The world: a 3-chain (`a`→`b`→`c`), a row with a **phantom** blocker (`p` blocked by
`ghost_does_not_exist`), a legacy **2-cycle** (`x`↔`y`), a legacy **3-cycle** (`m`→`n`→`o`→`m`),
and a row with a **duplicated** blocker (`d` blocked by `["a","a"]` — T5's axis, on the
migration path).

```
PRE-STATE: applied 14 pre-04b-1 DDL statements; `blocks` absent
EDGES BEFORE ensure_ready: []
EDGES AFTER  ensure_ready: [(a,b), (a,d), (b,c), (m,o), (n,m), (o,n), (x,y), (y,x)]
PASS 1: every resolvable (blocker, task) pair minted; cycles MINTED; phantom absent
PASS 2: phantom RECORDED level=WARNING task_id='p' phantom='ghost_does_not_exist'
PASS 3: 2 legacy cycle record(s), members=[('m','n','o'), ('x','y')], levels=['WARNING','WARNING']
PASS 4: second boot IDEMPOTENT — edge set unchanged (8 edges), no raise
PASS 5: transitive_blockers('c') -> ids=['b','a'] truncated=False
ALL DIRTY-STORE CHECKS PASSED
```

Every leg the brief named:

| leg | result |
|---|---|
| edges minted | ✅ 8, exactly the resolvable set; the duplicated blocker collapses to ONE edge (`a`→`d`) |
| phantom skipped **and recorded** | ✅ `WARNING`, naming **both** the phantom id and the task it was skipped for |
| cycle minted **and recorded** | ✅ **both** cycles — ESC-4's ∀-arity requirement, not just the first |
| idempotent on a second boot | ✅ edge set byte-identical, no raise, no duplicate |
| ONE transaction | ✅ §2.2 — 3 round trips at N=3 and at N=60 |
| S3's defect actually fixed | ✅ a legacy row serves its real upstream set, not `ids=[]` |

**Direction (E-1) confirmed as a by-product:** `b` has `blocked_by=['a']` and the minted edge
is `in=a, out=b` — `RELATE $blocker->blocks->$task`, as ruled.

---

## 4. THE ONE CONFIRMED DEFECT — Leg-1 row 1's predicate is FALSE (#275)

`test_blocks_edge.py`'s module-docstring LEG 1 table, row 1, states the answered predicate as
*"the tasks reachable UPSTREAM over the `blocks` EDGES **this ledger's last completed
`ensure_ready` mirrored** …"*. **I re-derived r6's measurement independently and it holds:**

```
edges mirrored by ensure_ready: 0          # a VIRGIN store — there are no legacy columns
transitive_blockers(dependent).ids = ['44f1cced1b9c474bab958b9217666ba3']
```

The read rides **every edge the ledger holds** — those `ensure_ready` mirrored **plus every
dependency written since** (`create_task`/`create_many` mint the edge in the same transaction
as the row). The predicate names a **strict subset** of what the response is true of.

**Why it is not pedantry.** Row 1's whole job is difference (a): *edges vs the `blocked_by`
COLUMN agree*. As written, it says the read covers only the boot-mirrored subset — i.e. that
edge ≢ column for **every post-boot write**, the exact **inverse** of the invariant SECTION K
pins. A consumer acting on it without checking concludes a dependency created after boot is
invisible to `transitive_blockers`. That is the trust definition's own failure: *wrong in a way
the response did not name*.

**The provenance chain is the instructive part.** The delta adversary found row 1's original
wording false (*"CLOSED"* — a one-word claim about a whole set), **recommended this wording**;
the r6 contract adopted it; the r6 adversary then measured the adopted wording false. **A false
one-word claim was replaced by a false predicate that now carries a measurement receipt**,
which makes it harder to doubt — and it was not fixed before close-out.

**A second, smaller defect in the same row:** its commentary says *"the predicate above says
'a COMPLETED migration'"*; the predicate says *"this ledger's last completed `ensure_ready`
mirrored"*. Prose describing prose, unchecked — the same class one level down.

**SEVERITY: not packet-blocking, and I say so deliberately rather than by omission.** It is a
contract/prose defect; the production code is correct; 04b-1 does not deploy, so no consumer
can meet it. But the Leg-1 table **is** this packet's trust artifact, it is committed and
semantically searchable, and it is precisely the class repo law is most emphatic about. **It
should be fixed before the archive `git mv`, which costs one edit.** Suggested true form
(r6's, which I concur with) is in #275.

---

## 5. Leg 2 — the two most load-bearing degraded states, re-run by CONSTRUCTION

### 5.1 The legacy edge-less world × the backfill (S3 — the packet's reason for existing)

Two databases seeded **identically**, differing only in whether the backfill ran:

```
world A (backfill NOT run): ids=[] truncated=False max_depth_used=32
world B (backfill run):     ids=['c','b','a'] truncated=False max_depth_used=32
```

**Byte-different. No false clear.** World A reproduces S3 exactly — *clean, confident, wrong* —
which also proves the probe discriminates rather than passing vacuously.

### 5.2 The blocker pre-check × `{empty}` over a store that GENUINELY HOLDS the blocker

The degradation is a forgery in the truest sense: the existence read returns `[]` while the row
is really there.

```
degraded pre-check raised: UnknownBlockerError
message: unknown task(s): 9ba6bbf7… — every blocked_by entry must name an existing task row
         or a task created in the same call; NOTHING was created
task rows before=1 after=1     (a WRITE would show after>before)
PASS C: fail-CLOSED, blocker NAMED, nothing written
POSITIVE CONTROL: undegraded create succeeded (id=63324261…); rows 1 -> 2
```

Fail-**closed**, the blocker **named**, and **nothing written** — counted on a **separate admin
connection**, because the ledger's own seam is the one being degraded. The positive control
proves the probe can see writes at all.

### 5.3 A third construction I ran unprompted — the truncation honesty pair (E-3)

Because a `truncated` flag that is *inferred* rather than *measured* is a false clear in the
same bytes:

```
5-chain @ max_depth=2 -> ids=[2 ids] truncated=True  depth=2
3-chain @ max_depth=2 -> ids=[2 ids] truncated=False depth=2
5-chain @ default     -> ids=[4 ids] truncated=False
```

**Both legs discriminate** — a build hard-coding either value dies on one. The FLOOR property
holds (the truncated answer is complete at every depth reached).

---

## 6. T5 — concurrency spot-check

A single green run never clears a concurrency test here, and 20/20 was the builder's standard.
I re-ran the class six further times, unpiped, exits captured, with a **passed-COUNT**:

```
RUN 1 exit=0 :: 3 passed in 0.98s      RUN 4 exit=0 :: 3 passed in 0.88s
RUN 2 exit=0 :: 3 passed in 0.93s      RUN 5 exit=0 :: 3 passed in 0.86s
RUN 3 exit=0 :: 3 passed in 0.97s      RUN 6 exit=0 :: 3 passed in 0.88s
```

6/6 green, zero red. Corroborates the builder's 20/20; it does not replace it, and I do not
claim it does. The CAS fix itself is verified in code:
`array::len(array::distinct(blocked_by)) = array::len($clm_resolved)` inside `_claim_fragment`'s
guarded UPDATE — **one atomic statement**, not a de-duplication elsewhere.

---

## 7. The removed-behaviour inventory — is each verdict TRUE of the code?

| # | verdict claimed | my check |
|---|---|---|
| 1 | `create_task`'s non-transactional write → **preserved-with-pin, strengthened** | **TRUE.** `create_task` now ends in `self._apply([_create_fragment(...), _relate_fragment(...)])` — CREATE + every RELATE in ONE `execute_transaction`, which verifies **every** statement where `query()` checked only the first. |
| 1b | its rejection LOG EVENT → **dropped-deliberately, escalated** | **TRUE and correctly escalated.** The event genuinely moves to `store.transaction.rolled_back` on `loremaster.store._txn`; no pin covers it either way. Operator ruling still owed (§9). |
| 2 | fail-open `blocked_by` → **dropped-deliberately** (R3) | **TRUE.** `_reject_unusable_blockers` runs BEFORE the write; measured live in §5.2 — refusal names the id and writes nothing. |
| 3 | `supersede_task` dropping deps → **old-behaviour-preserved DELIBERATELY** | **TRUE.** `supersede_task` calls `_new_task_content(subject, description, **None**, created_by, now)`; `_supersede_fragment` emits UPDATE→THROW-guard→CREATE and **no RELATE**. Successor born unblocked, predecessor keeps its own. |
| 4 | `SELECT * FROM task` → **preserved-with-pin** for the property | **TRUE.** Blocker statuses still resolve against the whole table via a separate read over the candidates' `blocked_by` ids; no default cap was added. |
| 5 | `AppContext._find_key_cycle` → **dropped-deliberately** (R6) | **TRUE.** Zero production hits repo-wide; `server.py` imports and calls `find_blocked_by_cycle` + `raise_cycle_refusal` with `CYCLE_NOUN_BATCH_KEYS`. Every surviving mention is historical prose in test docstrings. |
| 6 | `execute_transaction`'s inline attempt body → **preserved-with-pin** (extracted) | **TRUE.** Both verbs ride `_run_verified_transaction`; the deviation is disclosed (§9). |
| 7 | `reject_unknown_agents`' own probe → **preserved-with-pin** (thin adapter) | **TRUE.** It is now a 6-line adapter supplying `AGENT_TABLE` + vocabulary to `reject_unknown_rows`; it keeps no probe and no decision. |
| 8 | `MessageLedger.send`'s validation ORDER → **dropped-deliberately** (E-4) | **TRUE, including the sub-claim.** Order is: oversize-pointer guard → **empty-recipient guard** → `_reject_a_ghost_sender(sender)` → `_reject_unknown_recipients(recipients)`. The sender has its OWN method and vocabulary, so §H's predicted `_reject_unknown_recipients` naming hazard does **not** materialise — the adjudication is correct as written. |

**8 of 8 verdicts are true of the code.**

---

## 8. The rulings vs the build

| ruling | check |
|---|---|
| **R3** — `blocks` `ENFORCED` from birth + app pre-check | ✅ `DEFINE TABLE OVERWRITE blocks TYPE RELATION IN task OUT task ENFORCED SCHEMAFULL`, emitted from `_task_statements` (the ONE site feeding both `generate_task_ddl` and `generate_ddl`). Pre-check measured live §5.2. |
| **R5** — the tool `limit` PUSHES DOWN | ✅ `server.py`'s `query` branch calls `query_tasks(..., limit=limit)`; no dispatcher-side slice. |
| **R6** — ONE cycle detector, ledger-owned | ✅ `_find_key_cycle` deleted; `server.py` calls the ledger's `find_blocked_by_cycle` / `raise_cycle_refusal`. One class (`TaskCycleError`), one sentence shape, two nouns — as R6 permits. |
| **R7** — both reads in ONE `BEGIN…COMMIT` | ✅ `query_tasks` composes `LET $rows = (…)`, `$rows`, and the blocker read into one `execute_read_transaction`. |
| **R7 rider** — the write guard walks the COLUMN | ✅ `_read_dependency_graph` reads `blocked_by` only, filtered `WHERE array::len(blocked_by) > 0`. |
| **R9** — `limit` legal for `rollup` **and** `query` | ✅ `_TASK_ACTIONS_ACCEPTING_LIMIT = (_TASK_ACTION_ROLLUP, _TASK_ACTION_QUERY)`; a SET, so a `limit` on `transition` is still a teaching refusal. |
| **R10(ii)** — superseded blocker named with successor | ✅ `_superseded_blocker_clause` rides the shared refusal's `clauses` parameter. |
| **R11** — backfill in `ensure_ready` | ✅ §3, all six legs. |
| **T1** — cap on the ANSWER, not the scan | ✅ `limit=None if blocked is not None else cap` into `_candidate_statement`, then `selected[:cap]`. The scan is capped **only** where candidates ARE the answer. |
| **T5** — `array::distinct` in the CAS | ✅ in `_claim_fragment`'s guarded UPDATE; §6. |
| **E-1** — `RELATE $blocker->blocks->$task` | ✅ measured in §3 (`in`=blocker, `out`=task). |
| **E-3** — honest at its bound, discriminating pair | ✅ §5.3. |
| **E-4** — sender validated FIRST, own vocabulary | ✅ §7 item 8. |
| **L3** — existence policy GENERALISED, not cloned | ✅ `agent_existence` holds `resolve_existing_rows` / `reject_unknown_rows` / `format_unknown_row_refusal`; 04a's entry points are thin adapters. Sharing is mutation-proved by the contract, and my §5.2 degradation reached the task family through the shared probe. |

**8.5 — the build's package choices, verified not re-surveyed.** `graphlib.TopologicalSorter`
is genuinely used for both detectors (`find_blocked_by_cycle`, one implementation, both call
sites); the transitive read genuinely uses the engine's `@.{1..N+collect}` rather than a
client-side BFS (§2.2 shows the wire statements); `_txn`'s shared driver is genuinely extended
rather than hand-rolled. **`networkx` is correctly placed** — `loremaster/pyproject.toml`
`[dependency-groups] dev` (not `[project] dependencies`), and a grep over `loremaster/loremaster`,
`lorescribe`, `loresigil`, `lorerunes` and `scripts` finds **zero** production imports. The
`f0f4561` fix landed and is correct.

---

## 9. Escalations (3) — none blocking

- **ESC-A — Leg-1 row 1 (#275) should be fixed before the archive `git mv`.** One edit; the
  wording is in the finding. It is the only confirmed defect and it is prose. **Recommend fix
  now** rather than carrying a knowingly-false trust artifact into the receipts directory,
  where it becomes semantically searchable as if current. *(Operator's call — it is a scope
  decision, not mine.)*
- **ESC-B — the builder's E-A / E-B / E-E are still UNRULED and I did not settle them.**
  `limit=0` refused vs accepted (E-A); the rejected-create log event change and its Mezmo
  alerting consequence (E-B); pre-existing legacy cycles stepped over at write time (E-E). All
  three were escalated correctly with both readings; **none has an operator ruling recorded in
  the packet doc.** They are not audit findings — they are open decisions the packet should not
  close over silently.
- **ESC-C — #274 is RECORDED, NOT PINNED, and the packet doc says so itself.** Repo law is that
  a bound you keep gets a test asserting the hole, which reddens when someone closes it. That
  pin was not written. **I am not asking to reverse the acceptance** — the build is clean and
  does not deploy — but #276 now carries a working instrument that makes closing it cheap, so
  04b-2's entry condition can be *build it* rather than *decide whether to*.

**The deviation I inherited (`test_retry_seam.py` re-keyed, 2 lines, finding #269) still needs
the lead to ratify or revert.** I verified the claim: the gate keys on the enclosing function's
NAME, ESC-2's grant required exactly one shared body, the exemption COUNT is unchanged, and
`test_retry_seam.py` is green in my full-suite run. There is no production-only fix. It looks
correct to me, but it is outside my authority to ratify.

---

## 10. RESIDUALS — one line each, own verdict

| id | item | verdict |
|---|---|---|
| CA-1 | Leg-1 row 1 predicate FALSE at HEAD | **CONFIRMED DEFECT, filed #275.** Prose, not build. Fix before archive. |
| CA-2 | Leg-1 row 1's commentary misquotes its own predicate | **CONFIRMED, minor.** Same edit as CA-1. |
| CA-3 | Leg-1 row 7 graded FALSE by r6 | **I DO NOT CONCUR.** Measured TRUE of the shipped build (§2.3). r6's finding is about the instrument, and is correct about that. |
| CA-4 | `BACKFILL_FAILURE_DOORS` reaches 2 of 4 derived doors | **KNOWN BOUND (#274), now quantified and filed as #276** with a working instrument. |
| CA-5 | `TXN_STATEMENT_HARD_CAP=5000` bounds the backfill | **LOUD, verified** — `compose()` raises before anything is sent. E-C's characterisation is correct. |
| CA-6 | full-suite count 8256 vs builder's 8237 | **RECONCILED**, +19 = r6's new pins. No discrepancy. |
| CA-7 | `ensure_ready` fails if `task` rows exist but the schema never ran | **NOT PRODUCTION-REACHABLE.** My first probe hit it by seeding into a virgin schemaless DB; the DDL then fails at `DEFINE FIELD OVERWRITE provenance`. Every real caller runs `ensure_ready` before any write. Noted, not filed. |
| CA-8 | `_read_mirror_state` raises when `blocks` is absent | **CORRECT and desirable** — a loud failure, never a silent empty. Observed while building CA-7. |
| CA-9 | builder R-9 / R-10 (PROOFs 10b, 10d not run) | **STILL NOT RUN by me either.** 10b's premise is independently pinned by `TestTheBackfillIsONETransaction` (which I re-measured at scale, §2.2); 10d's ruled behaviour I verified from the other side by constructing **both** legacy cycle arities live (§3). I consider both discharged by construction, and say so rather than claiming the proofs ran. |
| CA-10 | builder R-7 (PROOF 8 leg 2 never fires, #268) | **UNCHANGED, contract defect, still open.** Not fixed in this packet; the arithmetic in #268 is the fix. |
| CA-11 | builder R-4 (write-time cycle guard TOCTOU) | **FLAGGED, still open.** Real, correctly characterised, closing it is a contract change. Not this packet's. |
| CA-12 | builder R-16 (cycle-graph read has no supporting index) | **UNCHANGED.** Bounded by the dependency-bearing population; the engine still scans `task`. Worth revisiting if the ledger grows. |
| CA-13 | builder R-17 (`blocks` carries no `UNIQUE(in,out)`) | **DELIBERATE and verified** — idempotence comes from diffing the store's own edge set; my second-boot leg (§3) confirms both directions. |
| CA-14 | `test_query_tasks_bounded.py` carries no Leg-1 material | **CORRECT as observed by the delta adversary.** Covered by reference from the other file's row 2; a pointer would be cheap. Not a defect. |
| CA-15 | 04b-1 does not deploy; `:18500` never contacted | **CONFIRMED by me** — every probe ran against spike-surreal `:18000` in throwaway databases, each dropped after use. |
| CA-16 | the `test_retry_seam.py` deviation (#269) | **UNRATIFIED.** Verified sound; the lead owns the ratify-or-revert call. |

---

*Written 2026-07-29 by `coldaudit-04b1` against branch `feat/surreal-unification` at HEAD
`2116c9f`. Every count, statement text and verdict above was produced by running the thing in
this session; none was inherited from `REPORT-builder-04b1.md`, `REPORT-adversary-04b1-r6.md`
or any sibling report without re-deriving it, and where my number differs from an inherited one
I reconcile it explicitly (§1, §2.3). I mutated no git state and contacted no production store.*
