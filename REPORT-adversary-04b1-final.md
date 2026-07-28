# REPORT-adversary-04b1-final — grading packet 04b-1's COMPLETE contract by construction

brief-base v7 read

comms brief receipt: **NOT OBTAINED — the lore MCP tools were unavailable in my context.**
`ToolSearch` itself is not enabled for this agent ("No such tool available: ToolSearch"), and
every `mcp__lore_lore__*` call returned "No such tool available" (verified on `lore_comms` and
`lore_index`). I therefore could NOT `register`, could not `drain`, and could not file findings
via `lore_findings`. **Treat every dogfood/ledger obligation in my brief as UNDISCHARGED**, and
see §ESCALATION-1 — this is itself friction that needs filing by someone who can reach the tool.
Consequence for tool honesty (brief-base §4): every code-structure question below was answered by
grep + direct reads, declared here rather than in passing.

trust hard-definition read

Its two askable questions, quoted verbatim from `CLAUDE.md` § *TRUST — THE HARD DEFINITION*:

> **Ask: *"what question did I actually answer, and is it the one the consumer thinks they
> asked?"*** (Leg 1 — SCOPE DIFF)

> **Ask: *"what broken state of this tool would serve exactly these bytes?"*** (Leg 2 — FORGERY
> PINS)

*Every claim in this file is scoped to branch `feat/surreal-unification` at HEAD **`bce3042`**,
measured **2026-07-28**. All live probes ran against spike-surreal `ws://127.0.0.1:18000` (TEST);
`:18500` was never touched. Every number was DERIVED here by running, never inherited.*

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 HEADLINE — FOUR wrong builds survived the WHOLE contract, 215 passed / 0 failed each.**
  Two of them are BLOCKERS that restore sidecar finding S3's exact false clear
  (`ids=[] truncated=False` on a task that is NOT claimable) through doors SECTION K does not
  guard: **WB-A** a backfill that skips a legacy SELF-loop · **WB-B** a backfill that also filters
  SUPERSEDED blockers. **WB-D** reintroduces #253's unbounded read on the WRITE path (rows read
  10→65 with ledger size) · **WB-C** makes the backfill N separate writes, falsifying R11's own
  one-transaction rationale and PROOF 10b's declared set. §P1.
- **SECTION L's "no false clear to STOP on" — I CONCUR with the verdict, and REJECT one of its
  instruments.** No construction I built produced identical bytes. But
  `TestTheSTORESeamRAISESRatherThanReturningEMPTY` — the linchpin closing the `{empty}` mode —
  measures a **PARSE ERROR**, a shape the fixed existence statement can never take, while the
  existence read's ACTUAL shape (direct record access) returns **OK + `[]`** against an absent
  table where a table scan RAISES. I closed the gap myself by measuring 4 rejection modes
  (parse error · absent table · TIMEOUT · unknown function) — all RAISE through `_query`. So the
  CLAIM holds and the PIN passes for a narrower reason than it reads. §SECL.
- **MISSING PINS, ranked** (each proven RED-on-wrong / GREEN-on-correct, §PINS):
  1. a legacy SELF-loop is MIRRORED (kills WB-A) — ESC-4 rules cycles MINTED; only 2-cycles pinned.
  2. a legacy dependency on a SUPERSEDED blocker is still mirrored (kills WB-B).
  3. a skip is never RECORDED as a "phantom" when the row EXISTS (kills WB-B's false log).
  4. the write path's rows-read does not grow with ledger size (kills WB-D).
  5. the backfill is ONE transaction (kills WB-C; PROOF 10b's premise is unpinned).
  6. `transitive_blockers` agrees with the claim CAS (pinned for `query_tasks`, never the traversal).
- **P-PKG DIFF — the contract's `bespoke` cycle-detector verdict evaluates NO library.**
  `graphlib.TopologicalSorter` is **stdlib**, and `CycleError.args[1]` IS the cycle in the exact
  `[a,b,…,a]` / `['x','x']` shape both call sites need. **Swapped in: 215 passed.** §PKG.
- **FIXTURE MONOCULTURE, two NEW axes:** legacy-blocker LIFECYCLE STATE (every blocker in
  `legacy_column_store` is `open`, none superseded) and CYCLE ARITY (only 2-cycles). §P2.
- **SATISFIABILITY RECEIPT: 215 passed / 0 failed** on my own reference build, **and after
  `ruff --fix`**; `typecheck.sh` EXIT=0; neighbours **697 passed / 33 skipped**. §SAT.
- **C-DEF, THIRD INSTANCE — a correct build breaks FIVE committed pins in `test_mcp_server.py`
  and the contract discloses TWO.** The three undisclosed: R6's cycle class vs a `pytest.raises(
  ValueError)`, and `_task_fakes.FakeTaskLedger.query_tasks` not accepting R5's `limit` (×2).
  All five measured GREEN at pristine `bce3042`. §CDEF.
- **`loremaster.__file__` = `/home/ejprice/scratch/adv04b1f-ref/loremaster/loremaster/__init__.py`**
- **RED honesty REPRODUCED: 152 failed / 63 passed at `bce3042`** — matches the brief exactly.
- **Escalations: 3** (§ESCALATION-1 lore MCP unreachable · §ESCALATION-2 `_txn.py` writable-set ·
  §ESCALATION-3 the served-English pins admit the INVERSE sentence). **Findings filed: 0 — I
  could not reach `lore_findings`.**

---

## §SAT — SATISFIABILITY RECEIPT (the gate the lead named)

I built my own reference implementation. I did NOT read `/home/ejprice/scratch/adv04b1-ref` or
`/home/ejprice/scratch/contractfix-04b1-ref` (forbidden), and I did not read
`REPORT-contract-04b1.md` before designing it.

Scratch tree minted with the blessed tool, provenance asserted by it and re-asserted by me:

```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch/adv04b1f-ref
scratch copy READY: /home/ejprice/scratch/adv04b1f-ref
  loremaster  -> /home/ejprice/scratch/adv04b1f-ref/loremaster/loremaster/__init__.py
$ uv run python -c "import loremaster; print(loremaster.__file__)"
loremaster.__file__ = /home/ejprice/scratch/adv04b1f-ref/loremaster/loremaster/__init__.py
```

What I built (production files touched): `store/surreal_schema.py` (the `blocks` edge in
`_task_statements`, `ENFORCED`, after the task table) · `agent_existence.py` (L3's
`format_unknown_row_refusal` / `reject_unknown_rows`, ESC-2's non-raising `probe_existing_rows`,
`UnknownRowError` as the shared base, `reject_unknown_agents` demoted to a delegating adapter) ·
`tasks.py` (`TASK_BLOCKER_MAX_DEPTH=32`, `TransitiveBlockers`, `transitive_blockers` probing at
`bound+1`, `find_blocked_by_cycle` + `format_cycle_refusal` + `TaskCycleError`,
`UnknownBlockerError`, `SupersededBlockerError`, atomic `create_task`, the mirror at both write
paths, R11's `_backfill_blocks_edges`, the bounded one-snapshot `query_tasks(limit=…)`, T5's
`array::distinct` in the CAS) · `messages.py` (#247's `UnknownSenderError`, sender-first) ·
`server.py` (R9's split guard, R5's pass-through, R6's cycle unification) ·
`store/_txn.py` (`execute_read_transaction`, the read sibling R7 needs — see §ESCALATION-2).

```
$ uv run pytest -q -n auto --show-capture=no loremaster/tests/test_blocks_edge.py \
      loremaster/tests/test_query_tasks_bounded.py
215 passed in 8.50s
PYTEST_EXIT=0
```

The harder leg the C-DEF clause demands — **still satisfiable after the lint's own cleanups**:

```
$ uv run ruff check --fix .       # removed an orphaned import + reordered; I named 2 magic values
Found 2 errors (2 fixed, 0 remaining).
$ uv run ruff check .
All checks passed!
RUFF_EXIT=0
$ ./scripts/typecheck.sh
typecheck: lorerunes OK · lorescribe OK · loresigil OK · loremaster OK (171 files) · skills OK
MYPY_EXIT=0
$ uv run pytest -q -n auto ... (both contract files, POST ruff --fix)
215 passed in 12.60s
```

Neighbouring suites on the same build:

```
$ uv run pytest -q -n auto --show-capture=no loremaster/tests/test_enforced_relations.py \
    loremaster/tests/test_task_ledger.py loremaster/tests/test_derivation_source_unification.py \
    loremaster/tests/test_message_ledger.py loremaster/tests/test_surreal_store.py
697 passed, 33 skipped in 45.81s
PYTEST_EXIT=0
```

**So the contract is SATISFIABLE.** The three deliberate reddenings in
`test_enforced_relations.py` go green as the module docstring predicts, and 04a residual **R-e**
(`test_surreal_store.py`'s populated-store migration) needed **no** change — it passed as-is,
which is one of the packet's owed items answered by measurement rather than by argument.

### §CDEF — but a correct build breaks FIVE pins outside the writable set, and the contract discloses TWO

```
$ uv run pytest -q -n auto --show-capture=no loremaster/tests/test_mcp_server.py
5 failed, 636 passed in 101.85s
```

| # | pin | why a CORRECT build breaks it | disclosed? |
|---|---|---|---|
| 1 | `TestRollupDispatch::test_limit_on_a_non_rollup_action_is_rejected` | R9 makes `limit` legal for `query` | ✅ ESC-1 |
| 2 | `TestRollupDispatch::test_since_on_a_non_rollup_action_is_rejected` | the guard's sentence must split | ✅ ESC-1 |
| 3 | `TestCreateManyDispatch::test_intra_batch_cycle_is_refused_with_the_exact_text` | it asserts `pytest.raises(ValueError)`; **R6 rules ONE error class, the ledger's**, and `TaskCycleError` is a `RuntimeError`. The TEXT is byte-identical on my build — the failure is purely the CLASS R6 mandates | ❌ **NO** |
| 4 | `TestTasksTool::test_tasks_query_renders_summarised_rows_not_raw` | `TypeError: FakeTaskLedger.query_tasks() got an unexpected keyword argument 'limit'` — R5 requires the dispatcher to pass it | ❌ **NO** |
| 5 | `TestTasksTool::test_superseded_task_renders_a_chain_marker_not_bare_status` | same `TypeError` | ❌ **NO** |

All five are **GREEN at pristine `bce3042`** (measured, so this is a consequence of the build and
not pre-existing rot):

```
$ uv run pytest -q -p no:randomly <the five node ids>
5 passed in 6.29s
```

**Why this is the C-DEF class and not bookkeeping.** #4/#5 are the *identical* ripple ESC-1
reasoned about and then mis-scoped: its own words are *"it retypes a method **five test doubles
implement**"* — for `ensure_ready`. R5 does exactly that to `query_tasks`, and nobody looked.
`_task_fakes.py:308` is the site. #3 is R6's ruling colliding with a committed pin: the contract
pins the tool seam raising *the ledger's cycle CLASS* and never says that a pin one file away
asserts `ValueError`. **A builder meets three red tests it may not edit, with no note.**
The contract needs the ESC-1 escalation WIDENED from two edits to five.

---

## §P1 — THE WRONG BUILDS. Four survived; two are BLOCKERS.

Method: mutate the reference build in place (permission was denied on a second `cp -a` scratch
path — declared as a deviation), with a **content** backup taken first per standing law, and
restore + `md5sum -c` after every probe. Final restore verified:

```
$ md5sum -c /tmp/adv04b1f_backup/MD5
loremaster/loremaster/tasks.py: OK
loremaster/loremaster/agent_existence.py: OK
```

### WB-A — a backfill that skips a legacy SELF-loop. **BLOCKER.**

The mutation is one plausible defensive line inside `_backfill_blocks_edges`:

```python
if blocker == task_id:
    continue          # "a task cannot block itself, so don't mint that edge"
```

```
$ uv run pytest -q -n auto ... test_blocks_edge.py test_query_tasks_bounded.py
215 passed in 8.56s
```

**Every pin green.** And the defect is real — a legacy self-blocked row (production-real:
`blocked_by` was FAIL-OPEN, and this contract's own `TestCreateRefusesToFormACycle` calls the
self-loop *"the 1-cycle … which `ENFORCED` alone cannot stop"*):

```
LOG[WARNING] task.backfill.legacy_cycle_mirrored
  blocked_by COLUMN     : ['selfloop_65a6b7d4508c462386595012d78703e8']
  blocks EDGE set       : []
  MIRROR HOLDS?         : False
  transitive_blockers   : ids=[] truncated=False max_depth_used=32
  claimable?            : False
```

`ids=[] truncated=False` on a task that is **not claimable** is S3 verbatim — a positive
assertion of completeness that is false — and a consumer acting on it *without checking* is wrong
in a way the response did not name. ESC-4 was ruled precisely to prevent this; its pin
(`TestALEGACYCycleIsMINTEDAndRECORDED`) constructs a **2-member** cycle only, so the 1-cycle door
is open. Note the cycle WARNING still fires, so even the RECORD leg is satisfied.

### WB-B — a backfill that also filters SUPERSEDED blockers. **BLOCKER.**

R10(ii) tells a builder a superseded blocker is *"NEVER legitimate"*. Reusing that notion as the
MIGRATION's filter is a one-hop inference:

```python
resolved = resolved - superseded     # after the shared existence probe
```

```
215 passed in 8.51s
```

The scenario is the one **R10(iii) itself names** — *"supersession can happen AFTER dependents
exist"*:

```
LOG[WARNING] task.backfill.phantom_blocker_skipped
  its blocked_by COLUMN : ['72eb7f71510f450eacf9c50009a23b5c']   (superseded by 24c53935…)
  its blocks EDGE set   : []
  MIRROR HOLDS?         : False
  transitive_blockers   : ids=[] truncated=False
  claimable?            : False
```

Worse than WB-A in one respect: the operator log **actively lies**, recording an existing task as
`phantom_blocker_skipped`. R11's rider says skips are RECORDED so an operator can act; here the
record sends them after a row that is right there.

### WB-D — the write-path cycle guard reads the WHOLE task table. **SURVIVES.**

Dropping the dependency-bearing filter from `_reject_a_cycle`'s single read:

```
create_many(1 item, 1 blocker) against a ledger of  5 unrelated tasks: calls=4 rows=10
create_many(1 item, 1 blocker) against a ledger of 60 unrelated tasks: calls=4 rows=65
ROUND TRIPS grew? False    ROWS READ grew? True
215 passed in 7.90s
```

**#253's exact defect — the finding this packet was widened to fix — reintroduced on the WRITE
path, invisible.** `TestTheReadIsBOUNDEDByTheCallersFilter` measures `query_tasks` only, and
`test_the_cycle_WALK_is_ONE_round_trip_however_DEEP_the_chain` says in its own docstring *"Rows
are deliberately NOT asserted"* — correct for its question (depth), blind to this one (ledger
size). R7's rider forces a client-side walk in one round trip and nothing bounds what that one
round trip READS. Control: the same measurement on my correct build gives `rows=4` at both N.

### WB-C — the backfill is N separate writes, not one transaction. **SURVIVES.**

```
for fragment in fragments:
    await self._query(fragment.statements[0], fragment.params)
215 passed in 7.97s
```

R11's pre-filter rationale is *"a naked backfill rolls back the whole **one-transaction**
migration"* — **false of this build**, and no pin requires one transaction.
`TestTheNakedBackfillWouldRollTheMigrationBack` measures the ENGINE, not the build. Severity is
below WB-A/WB-B (a partial backfill self-heals at the next boot, because the backfill is
state-keyed and idempotent), but the consequence is concrete: **PROOF 10b comes back with FEWER
reds than declared → `PROOF FAILED`, and the builder's next move is to edit the declared list —
the exact anti-pattern `mutation_proof.py` exists to prevent**, which this contract already names
for PROOF 5.

### Wrong builds I built that the contract KILLED (the doors that are shut)

| attempted door | the pin that killed it |
|---|---|
| `truncated = len(ids) >= max_depth` (single-query build) | `test_a_chain_EXACTLY_at_the_DEFAULT_bound_reports_truncated_FALSE` — forced probe-at-`bound+1` |
| a second existence copy in `tasks.py` (not routed through the policy) | `test_MUTATION_neutralising_the_shared_policy_STOPS_the_backfill` |
| the traversal on a non-`_txn` door (invisible to the degradation) | `test_a_FAILED_traversal_NEVER_renders_as_a_COMPLETE_answer` — degraded ≡ healthy ⇒ RED |
| a backfill keyed on *"did I already run"* | `test_the_backfill_does_NOT_re_mint_over_edges_a_WRITE_PATH_already_made` |
| a raw `SurrealStoreError` out of the failed pre-check | ESC-3's `pytest.raises(TaskLedgerError)` + both hygiene markers |
| a per-blocker / per-candidate read in `query_tasks` | `TestTheTwoReadsShareONESnapshot`, both axes |
| the naive R5+#253 composition (cap on the candidate scan) | `TestTheCapAppliesToTheANSWERNotTheCandidateScan`, both legs |
| the engine's `<-blocks<-` traversal as the write-time cycle detector | `test_a_create_that_would_close_a_cycle_through_PERSISTED_tasks_is_REFUSED` |
| `from … import format_cycle_refusal` in `server.py` | `TestTheCyclePolicyHasONEImplementation::test_MUTATION_replacing_the_shared_FORMATTER…` |
| a fabricated tail count on the traversal result | `test_the_result_type_carries_NO_field_that_would_COUNT_the_unknown_tail` |

Those ten are real teeth, and several are unusually good. The contract is strong. It is
insufficient anyway, in the specific places below.

---

## §P1b — THE QUANTIFIER TABLE. Every invariant, ∀-over-inputs vs guarded, receipt on every guarded row.

| # | invariant | ∀ / guarded | receipt |
|---|---|---|---|
| 1 | edge ≡ `blocked_by` at every WRITE path | **∀ over VERBS** (AST adjudication pin), **guarded over blocker STATE** | WB-B: a superseded blocker's edge dropped, green |
| 2 | edge ≡ `blocked_by` at MIGRATION (R11) | **GUARDED** — fixture is acyclic-or-2-cycle, `open`-or-`done`, resolvable-or-phantom | **WB-A + WB-B, BLOCKERS** |
| 3 | a legacy CYCLE is MINTED (ESC-4) | **GUARDED to arity 2** | **WB-A, BLOCKER** (the 1-cycle door) |
| 4 | a phantom skip is RECORDED | **GUARDED** — pins that a phantom IS recorded; nothing forbids recording a NON-phantom as one | WB-B logs `phantom_blocker_skipped` for an existing row, green |
| 5 | the migration is ONE transaction | **NOT PINNED AT ALL** | WB-C survives; PROOF 10b's premise unpinned |
| 6 | backfill idempotence | **∀ over boots × provenance sources** | door attempted (keyed on "did I run") → killed by the mixed-provenance leg |
| 7 | the traversal is HONEST at its bound | **∀ over {default, explicit} × {under, AT, over}** | door attempted (`len>=bound`) → killed at the cap boundary |
| 8 | a FAILED traversal never renders as complete | **GUARDED to the derived `_txn` seam set** — but derived name-free and fail-CLOSED on `run_query` | door attempted (non-`_txn` door) → killed (degraded ≡ healthy) |
| 9 | the pre-check fails CLOSED on a degraded read | **∀ over {empty, error}**, `{empty}` closed one level down | §SECL: the closing pin measures the WRONG STATEMENT SHAPE; I re-closed it by measuring 4 modes |
| 10 | no fabricated count / no invented total | **∀ by EXACT-SET, deny-by-default** | door attempted (add a field) → killed |
| 11 | the `blocked` PARTITION never disagrees with the CAS | **∀ over the known modes** (out-of-filter, phantom, duplicate, terminal set) | door attempted (naive push-down) → killed |
| 11b | the **TRAVERSAL** agrees with the CAS | **NOT PINNED** — #11 covers `query_tasks` only | WB-A/WB-B: traversal says unblocked, CAS says blocked. **MISSING PIN 6** |
| 12 | rows read do not grow with ledger size | **GUARDED to `query_tasks`** | **WB-D survives** on the write path |
| 13 | ONE round trip / ONE snapshot | **∀ over blocker-count AND candidate-count growth** | door attempted (per-blocker reads) → killed |
| 14 | the refusal names EVERY unresolved id | **∀ over 4 id SHAPES** | door attempted (one-literal policy) → killed |
| 15 | no engine hygiene text reaches a caller | **∀ over a rejection-path table + deny-by-default adjudication** | door attempted (re-raise verbatim) → killed |
| 16 | a cycle is refused at WRITE time | **∀ over reachable inputs** (`create_task` cannot form one — the id is a fresh uuid4 no caller has seen) | reasoned + measured: no door |
| 17 | ONE cycle implementation, shared | **∀ by mutation in BOTH namespaces** | door attempted (`from … import`) → killed |
| 18 | ONE existence implementation, shared | **GUARDED** — the mutation patches ANY public coroutine in the module, so a second *decision* beside the shared call passes | WB-B is exactly that shape, green |

---

## §SECL — SECTION L graded: is the no-false-clear claim earned?

The lead asked four things. Answers, each measured:

**1. Is each degraded state genuinely CONSTRUCTED, not simulated by a fake that cannot fail?**
**YES, and better than that.** `_degrade_every_STORE_seam` and
`_patch_every_shared_policy_COROUTINE` **derive** their targets (`vars(module)` × coroutine ×
`__module__`) and patch at **both** addresses because `from … import` copies the reference. Both
fail CLOSED — an empty derivation reddens, and the store one additionally asserts `run_query` is
in the set. I attacked the derivation by building a traversal on a door outside `_txn`: the pin
went RED (degraded bytes ≡ healthy bytes). **The construction can fail. It is not decoration.**

**2. Is the byte-diff over the SERVED bytes or something upstream of the render?** Over what the
CALLER HOLDS. `_served_shape` renders a `TransitiveBlockers` *and a raised exception* into one
string, which is the only way a healthy result and a degraded raise can be compared at all. At
this layer the ledger's return value IS the served surface (the render is 04b-2's), so the unit is
right. Accepted as `R-16` in the r4 report and I agree.

**3. Is the healthy-path control real?** **YES.** `_seed_then_degrade` computes the healthy bytes
on a real 4-chain **before** breaking anything, and the pin asserts
`healthy.startswith("OK ")` — so a run where both sides failed cannot pass as a diff. The two
sides are the same code path over **two different worlds**, which is what leg 2 asks for; they are
not two renders of one state.

**4. Does the byte-diff prove anything?** Yes for F1–F5. **But its `{empty}` linchpin does not.**
`TestTheSTORESeamRAISESRatherThanReturningEMPTY` is the pin that makes app-layer `{empty}` mean
*ran-and-empty* (a TRUE clear). Its leg 1 is:

```python
await _raw(ledger, "SELECT * FROM task WHERE THIS IS NOT SURQL AT ALL")
```

That is a **PARSE ERROR** — the one failure mode a fixed statement string can never take. The
existence read's real shape is direct record access, and I measured that shape behaving
*differently from a table scan*:

```
'read of an ABSENT table'         (table scan)     -> ERR   "The table 'x' does not exist"
'record read of an ABSENT row'    (direct access)  -> OK    []          <-- OK + empty
  probe_existing_rows(absent table) -> set()   <== NO RAISE
```

So the pin's message promises *"a REJECTED read RAISES"* and its assertion demonstrates *"a
malformed statement raises"*. **This is my own role's P0 lesson turned on the contract**, and it
is the same shape the r4 report itself was bitten by (its 13 fixture errors from assuming an
absent-table read returns `[]`).

**I closed the gap rather than merely naming it.** Through the real ledger seam, on the live test
store:

| degraded state | `TaskLedger._query` behaviour |
|---|---|
| parse garbage | raised `SurrealStoreError` |
| unknown function (RPC-level `error`, no result list) | raised `SurrealStoreError` |
| absent table (table scan) | raised `SurrealStoreError` |
| `TIMEOUT 1ns` on a plain SELECT | raised `SurrealStoreError` (`ERR`, *"exceeded the timeout"*) |
| `TIMEOUT 1ns` on the recursive path | raised `SurrealStoreError` |

**Positive control that the probe can see the other outcome:** a legal read matching nothing
returned `[]`; `SELECT id FROM task:does_not_exist` returned `OK []`. So the probe distinguishes
raise from empty, and distinguishes them for *different reasons*.

**VERDICT on SECTION L: the claim "no construction produced identical bytes; there is no false
clear to STOP on" is TRUE, and I could not overturn it.** But it rests on an instrument whose
reach is one mode of at least five, and the mode the existence read can actually exhibit
(`OK + []` from direct record access) is **not** the one measured. That is a **narrowness
finding with a re-open trigger**, not a false clear: I could not construct a reachable
production state in which the app-layer `{empty}` arises from a FAILED read
(`ensure_ready` applies the DDL before the backfill, so the `task` table always exists on the
migration path; a wrong-DATABASE world has no rows to back-fill and returns early). **Re-open
trigger: the first degraded state in which `probe_existing_rows` returns a PARTIAL set.**

### Two SECTION L residuals, each its own verdict

- `test_the_FAILURE_teaches_the_OPERATION_the_BOUND_and_the_RECOVERY` — **STRONG.** The
  id-redaction before looking for the bound is a genuinely good instrument (a uuid4 hex usually
  contains any given 2-digit substring). My first reference build failed it for the right
  reason: the existence read on the same seam raised *before* the traversal, so a build must
  classify both. Verdict: keep, no change.
- `TestTheScopeOfTheTransitiveReadIsSTATED` and `test_the_helpers_docstring_states_the_FLOOR_property`
  — **DISCLOSED BOUND, and the disclosure understates it.** Both check token PRESENCE. Measured:
  a docstring reading *"Ignores the `blocked_by` column entirely; a **phantom** entry IS included
  in this answer, which is a **floor**"* satisfies **all three tokens** and asserts the inverse of
  the truth. See §ESCALATION-3.

---

## §PINS — the missing pins, as a runnable PAIR (RED on wrong, GREEN on correct, cross-controlled)

I wrote them and proved them. The file lives OUTSIDE the repo:
`/tmp/advpins/test_adv_missing_pins.py` — **and because `/tmp` is an unrecoverable address by
standing law, the full body is reproduced in §PINS-BODY below** so the author can lift it.
It imports the contract's own instruments (`_seed_legacy_task`, `_blocks_edge_pairs`,
`_recorded_text`, `_transitive_blockers`, `migration_db`) — it clones nothing.

```
CORRECT reference build      : 4 passed
WB-A (skips the self-loop)   : 2 failed, 2 passed   <- the SELF-LOOP legs RED, superseded legs GREEN
WB-B (filters superseded)    : 2 failed, 2 passed   <- the SUPERSEDED legs RED, self-loop legs GREEN
```

The cross-controls matter: each wrong build reddens **only its own** pair, so the four legs
discriminate two distinct defects rather than being one pin wearing four names.

| # | the test that should exist | the defect it catches |
|---|---|---|
| 1 | `TestTheBackfillMirrorsALegacySELFLoopToo::test_a_legacy_SELF_LOOP_is_MIRRORED_onto_the_edge_table` | a backfill that skips `blocker == task` — breaks edge ≡ `blocked_by` on the smallest legacy cycle, which ESC-4 ruled MUST be minted |
| 2 | `…::test_the_SELF_LOOP_row_does_not_serve_a_CONFIDENT_EMPTY` | S3's false clear on that row: `ids=[] truncated=False` while the task is unclaimable |
| 3 | `TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask::test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED` | a builder carrying R10(ii)'s WRITE-time refusal into the MIGRATION filter, silently dropping a real dependency in exactly the situation R10(iii) names |
| 4 | `…::test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS` | a skip log that names an existing task as a phantom — the operator record actively teaches something false |
| 5 | `test_the_WRITE_paths_rows_read_does_NOT_grow_with_the_size_of_the_LEDGER` (growth comparison at 5 vs 60 unrelated tasks, on `create_many` with one blocker; assert `rows` equal, not `calls`) | WB-D: #253's unbounded read reintroduced on the write path by R7's client-side walk |
| 6 | `test_the_TRANSITIVE_read_AGREES_with_the_CLAIM_CAS` (∀ a legacy row: `transitive_blockers(...).ids == [] and truncated is False` ⇒ `claim_task(...).claimed is True`) | every divergence WB-A and WB-B produce, and any future one — this is the OUTCOME property, where #11 is the cause-specific one |
| 7 | `test_the_BACKFILL_is_ONE_transaction` (e.g. assert the migration's edge writes arrive in one round trip via `measure_store_traffic`) | WB-C; and it is what makes PROOF 10b's declared-red set true rather than hoped |

**Pin 6 is the one I would write first if only one were written.** Pins 1–4 close two named
doors; pin 6 is the ∀-over-outcomes that closes the class — *any* backfill filter, present or
future, whose skip makes the traversal disagree with the CAS. That is THE QUANTIFIER LAW applied
to R11: the contract pins the causes it debugged (phantom, cycle-arity-2) instead of the outcome
(*no row may be served as unblocked while the CAS holds it blocked*).

---

## §P2 — fixture discrimination, with perturbation results and correct-build controls

| fixture | verdict |
|---|---|
| `legacy_column_store` (4-deep diamond + mixed-phantom row + terminal row) | **DISCRIMINATES on depth, branching, dedup, and row STATUS — and is a MONOCULTURE on blocker LIFECYCLE STATE.** Every blocker in it is `open` and non-superseded. Perturbation = add a superseded legacy blocker; proven pair in §PINS (RED on WB-B, GREEN on correct). **NEW AXIS.** |
| `TestALEGACYCycleIsMINTEDAndRECORDED::_cyclic_legacy_store` | **DISCRIMINATES for arity 2 only — MONOCULTURE on CYCLE ARITY.** Perturbation = a 1-cycle; proven pair in §PINS (RED on WB-A, GREEN on correct). **NEW AXIS.** |
| `branching_dag` (4 deep, diamond, isolated control) | **DISCRIMINATES.** Kills the bare idiom, kills a non-dedup closure. No perturbation found that blinds it. |
| the honest-bound pair (default path × under/AT/over) | **DISCRIMINATES, exemplary.** The AT-the-bound leg is the only thing that kills `len>=bound`; I hit it building the reference. |
| `_sandwich_ledger` (30 blocked / 5 unblocked / 30 blocked) | **DISCRIMINATES, with its own stated 7e-7 record-id-order bound.** I confirmed the arithmetic direction: a candidate-cap build serves 1 or 0 under the two deterministic orderings. |
| `PHANTOM_TASK_IDS` (4 id shapes) | **DISCRIMINATES.** Kills a one-literal policy. A prior axis, correctly closed. |
| `task_ledger` (one real blocker, 4 phantoms asserted absent) | **DISCRIMINATES.** The absence assertions are load-bearing. |
| `_seed_chain` / `_seed_cycle` (raw, bypassing the guards) | **DISCRIMINATES.** Holding the detector to account over graphs the guard would refuse to build is the right call and it is why WB-D was even measurable. |
| `TestTheTwoReadsShareONESnapshot::_traffic_for` (3 vs 30 blockers) | **DISCRIMINATES.** Growth, not threshold. |
| `TestTheSTORESeamRAISESRatherThanReturningEMPTY`'s parse-error statement | **DOES NOT DISCRIMINATE THE THING IT CLAIMS.** §SECL. The perturbation that blinds it: swap the statement for the shape the existence read actually uses. |
| `TestTheCREATEPathsCostIsSTATED` (derives the number, does not choose it) | **DISCRIMINATES, and is a model.** My build measured 3; the docstring had to say 3. |

---

## §PKG — MY package table, built BEFORE reading the contract's, then DIFFED

| mechanism the contract specifies | library I evaluated | what I **READ** | my verdict |
|---|---|---|---|
| transitive closure over a graph edge | SurrealDB's own `@.{1..N+collect}` recursive path | probe receipt §5 (`docs/plans/v2/receipts/2026-07-27-packet04a/REPORT-probe-pkt04-store.md`) + the v3.2.0 spec `language/graph/path_collect.surql` it cites | **replace** (engine-side) |
| **cycle detection over a dependency map** | **`graphlib.TopologicalSorter` (STDLIB)** | `/usr/lib/python3.14/graphlib.py`; `CycleError.__doc__`; and I RAN it on 6 graph shapes | **replace** |
| bounded retry / backoff at the store seam | the repo's own `_txn.retry_on_conflict` | `_txn.py::retry_on_conflict` docstring + body | reuse (no new copy) |
| a transaction that RETURNS results | the SDK's `query_raw` through `_txn::_txn_query_raw` | `_txn.py::_txn_query_raw`, `execute_transaction` | reuse + a thin public wrapper (§ESCALATION-2) |
| degraded-dependency construction in tests | `pytest`'s `monkeypatch` | `_pytest.monkeypatch.MonkeyPatch.setattr` | replace |
| structured-log-record assertion | `pytest`'s `caplog` | `conftest.py`'s propagation-restoring autouse fixture | replace |
| existence probe + refusal rendering | none — domain policy over our own schema | — | bespoke, minimal surface |

### The DIFF against the contract's table — one real gap

The contract's own verdict, in `TestCreateRefusesToFormACycle`'s docstring:

> **PACKAGE VERDICT, CORRECTED:** … The guard's verdict is `bespoke`, with the minimal surface
> the rule demands: a DFS over the column, nothing more …

**Its read-column evaluates no library at all.** It only corrects an earlier *"replace with the
engine operator"* verdict to `bespoke` — and the correction is right about the engine (the closing
dependency cannot carry an edge). But that is the *hand-roll one level down* this role exists to
catch: **a correction is a specification too.** No general-purpose graph library is named, and
the stdlib one does the job exactly:

```
graphlib is STDLIB, python 3.14.6 -> /usr/lib/python3.14/graphlib.py
CycleError: 'Subclass of ValueError raised by TopologicalSorter.prepare if cycles exist'
  2-cycle a<->b          -> ['a', 'b', 'a']
  SELF loop x            -> ['x', 'x']
  3-cycle                -> ['a', 'c', 'b', 'a']
  acyclic diamond        -> None
  chain + closer         -> ['c1', 'c2', 'new', 'c0', 'c1']
  dangling dependency    -> None
```

Note the third and sixth rows especially: `['x','x']` is **byte-for-byte the format
`AppContext._find_key_cycle`'s existing docstring already promises** (*"a self-reference yields
`["x", "x"]"`*), and a dependency naming an id outside the graph is tolerated — exactly what a
`blocked_by` entry pointing outside the read needs. **`CycleError` is a `ValueError` subclass**,
which also happens to be what the existing tool seam raises.

**PROVEN, not argued** — I replaced the hand-rolled DFS with `graphlib` in the reference build
and ran the real contract:

```
$ uv run pytest -q -n auto ... test_blocks_edge.py test_query_tasks_bounded.py
215 passed in 8.44s
```

**Verdict: the cycle detector should be `replace`, not `bespoke`.** It is stdlib, so there is no
install to authorise; R6's *"ONE detection ALGORITHM, shared"* is satisfied better by a stdlib
call two modules make than by a DFS one module owns; and the mutation proof still works (the
shared thing becomes the wrapper both call). Everything else in the contract's survey I concur
with — `keep_with_trigger` on the SDK-error-by-message catch is a legitimate verdict for the
#133 reason given, and the `caplog` / `monkeypatch` replacements are correct.

---

## §P3 — branch reachability of the code the contract demands

| branch the build will have | the pin that FAILS if it is deleted |
|---|---|
| `max_depth` out of range (4 values) | `test_an_OUT_OF_RANGE_max_depth_is_REFUSED_with_a_TEACHING_error` + `traffic.calls == 0` |
| `max_depth` in range (incl. `255`) | `test_POSITIVE_CONTROL_an_IN_RANGE_max_depth_is_ACCEPTED[255]` — the off-by-one killer |
| traversal truncated / not truncated | the 5-leg honest-bound pair |
| task absent | `test_an_UNKNOWN_task_id_raises_TaskNotFoundError` |
| store failure during the traversal | `TestTheTraversalIsLOUDWhenTheSTOREFails`, 2 legs |
| pre-check: unknown / superseded / all-fine | 3 classes, each with a positive control |
| pre-check: degraded read `{empty}` / `{error}` | 2 legs + a positive control |
| cycle: batch keys / batch ids / self / persisted | 4 legs + a 4-deep legal control |
| backfill: nothing to do | `test_POSITIVE_CONTROL_a_store_with_NOTHING_to_backfill_never_reaches_it` |
| backfill: phantom skip / clean store | 2 legs, opposite directions |
| backfill: **`blocker == task` (self)** | **NONE — WB-A** |
| backfill: **blocker superseded** | **NONE — WB-B** |
| backfill: edge already present (idempotence) | 2 legs, opposite failure modes |
| `query_tasks`: limit pushed / not pushed (`blocked` in play) | R5 legs + T1's two legs |
| `query_tasks`: `limit` invalid | `test_the_caller_receives_a_TEACHING_refusal…[query_tasks-negative_limit]` |
| `server.py`: `since` refused / `limit` allowed for `query` / `limit` refused elsewhere | 3 legs (R9) — surgical, as the class claims |

Unreachable through the real entry point, honestly: a `create_task`-only cycle (the new id is a
fresh `uuid4` no caller has seen), so the write-time cycle guard is pinned only through
`create_many`. That is correct scope narrowing, not a hole — stated because it determines whether
pin #16's reach is honest.

---

## §P4 — the author's claims, reproduced

| claim (r4 report / brief) | my measurement | verdict |
|---|---|---|
| **152 RED / 63 passed** at HEAD | `152 failed, 63 passed in 8.34s` | ✅ EXACT |
| contract total **215** pins | 152 + 63 = 215; my green run = 215 | ✅ |
| `typecheck.sh` EXIT=0, `ruff` clean on the repo tree | reproduced on my build post-`--fix` | ✅ |
| *"an absent-table SELECT RAISES, it does not return `[]`"* | reproduced: `ERR "The table 'x' does not exist"` | ✅ — **and I extend it: direct record access on the same absent table returns `OK []`**, which is the §SECL gap |
| *"`+collect` terminates on cycles"* (probe P4, inherited) | reproduced live on a backfilled 2-cycle and a 1-cycle | ✅ |
| ESC-1's *"two committed pins in `test_mcp_server.py`"* | **FIVE**, three undisclosed | ❌ **UNDER-COUNTED** (§CDEF) |
| PROOF 10b: *"the whole migration rolls back, so nothing lands at all"* | premise unpinned; WB-C green | ❌ **UNSOUND for a legal build** |
| §11.1 row: a traversal timeout error *"naming the timeout"* is unachievable (their #263) | I re-derived it: `_classify_engine_error` has no timeout label, and the engine's own `ERR` text is withheld | ✅ CONCUR |

---

## §P5 — can the test doubles FAIL?

`test_blocks_edge.py` contains **zero** references to `Fake`/`_task_fakes`/`_comms_fakes`/
`_message_fakes`; `test_query_tasks_bounded.py` has one (a comment). **This contract is
store-live end to end** — there is no `[fake]` half to mutate, and that is the right choice for a
packet whose defects are all store-shaped. Verdict: **N/A by construction, and correctly so.**

The one double that DOES matter is `_task_fakes.FakeTaskLedger`, and it matters because it
**cannot accept R5's `limit`** — §CDEF #4/#5. That is the fake failing in the wrong direction: not
"it blesses the implementation" but "it blocks a ruled change and nobody surveyed it."

---

## §P6 — corpse sweep (BARE, anchor-free patterns). Every hit, its own verdict.

`grep -rn "apply only to action" --include=*.py loremaster/ scripts/` — **9 hits:**

| # | site | verdict |
|---|---|---|
| 1 | `server.py:3499` | the retired claim itself — the TARGET of R9, not a corpse |
| 2 | `test_query_tasks_bounded.py:119` | docstring prose, correctly dated to `5a2dca9` — OK |
| 3 | `test_query_tasks_bounded.py:1137` | failure-message prose, correctly framed — OK |
| 4 | `test_query_tasks_bounded.py:1391` | class-docstring prose quoting the pre-R9 refusal — OK |
| 5 | `test_query_tasks_bounded.py:1413` `RETIRED_CLAIM` | **this IS the guard** — asserts the sentence is GONE. Correct. |
| 6 | `test_query_tasks_bounded.py:1448` | failure message — OK |
| 7 | `test_mcp_server.py:6961` | **LIVE CORPSE** — asserts the retired sentence BY VALUE. Disclosed (ESC-1). |
| 8 | `test_mcp_server.py:6970` | **LIVE CORPSE** — same. Disclosed. |
| 9 | `test_blocks_edge.py:6998` | PROOF 9's shell anchor comment — OK |

`grep -rn "blocked_by cycle"` outside production — **1 hit:**

| # | site | verdict |
|---|---|---|
| 10 | `test_mcp_server.py:7339` | **LIVE CORPSE, UNDISCLOSED.** Under `pytest.raises(ValueError)`; R6 mandates the ledger's class. Text byte-identical on my build; only the CLASS breaks. |

`grep -rn "array::len(blocked_by)"` (the pre-T5 CAS) — **10 hits:**

| # | site | verdict |
|---|---|---|
| 11 | `tasks.py:182` (module comment) | **STALE AFTER T5** — the builder must update it; #219's class. FLAG. |
| 12 | `tasks.py:739` (`_claim_fragment` docstring) | **STALE AFTER T5** — same. FLAG. |
| 13 | `test_query_tasks_bounded.py:540` | prose describing the CAS's semantics; still true of the `distinct` form — OK |
| 14 | `test_blocks_edge.py:4541` | prose citing the pre-fix CAS as context — OK |
| 15 | `test_blocks_edge.py:4696` | failure-message prose — OK |
| 16 | `test_blocks_edge.py:4811` | `TestTheDuplicateBlockerDivergence` docstring, describing the DEFECT — OK, that is its subject |
| 17 | `test_blocks_edge.py:4890` | failure message — OK |
| 18 | `test_blocks_edge.py:4979` | failure message naming the T5 defect — OK |
| 19 | `test_blocks_edge.py:5692` | a live FIXTURE query (`WHERE array::len(blocked_by) > 0`) — correct, unrelated |
| 20 | `test_blocks_edge.py:6930` | PROOF 7's anchor/replacement pair — correct |

`grep -rn "def query_tasks"` — **2 hits:** `tasks.py:634` (production, gains `limit`) and
`_task_fakes.py:308` (**the undisclosed R5 ripple**, §CDEF).

`grep -rn "transitive_blockers|BLOCKS_RELATION"` in the test tree outside the contract —
**4 hits**, all in `test_surreal_store.py` (`_BLOCKS_RELATION_LITERAL = "blocks"` at 4719 and its
`RELATE` at 5393–5394): **NOT a corpse** — it is 04a residual **R-e**'s site, and it passed
unchanged on my reference build (697 passed), so R-e needs no edit. One owed item answered.

---

## §P6b — independent enumeration of REPLACED behaviour, then the diff

Stage 1, from the source alone, before reading any inventory. `query_tasks`'s replaced body
(`SELECT * FROM task` + a Python loop) has these observable behaviours:

1. every column of every row is materialised (`SELECT *`, no projection);
2. `status_by_id` is built from **every** row, so an out-of-filter blocker still contributes;
3. a `blocked_by` id absent from `status_by_id` is UNRESOLVED (fail-closed);
4. terminal = `{done, wontfix}`;
5. filters are AND-combined;
6. filter values never enter query text (they are Python comparisons);
7. no result ORDER is promised;
8. one round trip, one snapshot — trivially, because there is one read;
9. `blocked=None` skips the partition entirely;
10. a duplicate `blocked_by` id counts once client-side (`_is_blocked` short-circuits) while the
    CAS counted it twice — **the divergence**;
11. no cap of any kind at this layer.

Also replaced: `create_task`'s non-transactional single `_query`; the fail-open `blocked_by`;
`_find_key_cycle`'s own sentence and its bare `ValueError`; `_reject_unknown_recipients`' name
and docstring (which say "recipients" and will also cover the sender).

Stage 2, diffing against the contract's inventory (the `#253` block's "Removed-behaviour
inventory REQUIRED" list + the addendum's W-1…W-6):

- 1 → W-4 ✅ · 2 → W-1 ✅ · 3 ✅ · 4 ✅ · 5 → W-6 ✅ · 6 → W-5 ✅ · 7 explicitly *"a REPORTED
  RISK, not an invented requirement"* ✅ · 8 → R7, adjudicated as a hazard the fix INTRODUCES ✅ ·
  9 → W-2 ✅ · 10 → T5, adjudicated with the CAS-side fix ✅ · 11 → R5/T1 ✅.
- `create_task`'s non-transactional write, the fail-open `blocked_by`, and `supersede_task`
  dropping dependencies are all named in the packet's inventory clause ✅.
- **`_find_key_cycle`'s bare `ValueError` is inventoried as a THING TO CHANGE (R6) but its
  CONSUMER is not** — `test_mcp_server.py:7339`. §CDEF #3. **A behaviour I found that the
  inventory's adjudication does not reach.**
- **`_reject_unknown_recipients`' prose:** the contract *flags* this (`TestSendRefusesAGhostSENDER`'s
  docstring: *"Adjudicate it in the removed-behaviour inventory; do not leave the prose teaching a
  contract the code no longer has"*) and **pins nothing**. On my build the name stayed accurate
  because I gave the sender its own call (E-4), so the flag resolves itself — but only under E-4's
  reading. Verdict: adjudicated-with-no-pin, and harmless under the ruled design. Noted, not
  escalated.

Nothing in the inventory failed to ground in the code. **The `#253` inventory is good work; its
one gap is a consumer, not a behaviour.**

---

## §PINS-BODY — the proposed pins, in full (durable copy; `/tmp` is not an address)

```python
"""The pins packet 04b-1's contract does NOT have — written as a runnable PAIR.

Each must be GREEN on a correct build and RED on the wrong build named in its docstring.
Proven 2026-07-28: correct build 4 passed; WB-A 2 failed/2 passed; WB-B 2 failed/2 passed.
"""
from __future__ import annotations

import logging
import uuid

import pytest
from _enforced_relations_scaffold import apply_ddl, migration_db  # noqa: F401
from _surreal_harness import SurrealConnection, SurrealEnv, run
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_OPEN
from test_blocks_edge import (
    TestTheLedgersOwnMigrationPathLandsTheGuard as _MigrationHelpers,
    _blocks_edge_pairs,
    _recorded_text,
    _seed_legacy_task,
    _task_ddl_without_blocks,
    _transitive_blockers,
)

CREATOR = "adversary-04b1-final"
DESCRIPTION = "a legacy dependency the backfill must mirror, whatever its shape."


async def _column_of(connection: SurrealConnection, task_id: str) -> list[str]:
    rows = await run(
        connection,
        f"SELECT VALUE blocked_by FROM type::record('{TASK_TABLE}', $i)",
        {"i": task_id},
    )
    return [str(entry) for entry in (rows[0] if rows else [])]


class TestTheBackfillMirrorsALegacySELFLoopToo:
    """RED on WB-A (a backfill that skips ``blocker == task``).

    ESC-4 ruled that the backfill MINTS legacy cycles.  SECTION K's cycle fixture
    constructs only a TWO-member cycle, yet this contract's own
    ``TestCreateRefusesToFormACycle`` calls the SELF-loop *"the 1-cycle … which ENFORCED
    alone cannot stop"* — and ``blocked_by`` was FAIL-OPEN, so production holds them.
    """

    @staticmethod
    async def _legacy_self_blocked(connection: SurrealConnection, env: SurrealEnv) -> str:
        await apply_ddl(connection, _task_ddl_without_blocks(), url=env.url)
        task_id = f"selfloop_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, task_id, blocked_by=[task_id], status=STATUS_OPEN)
        return task_id

    async def test_a_legacy_SELF_LOOP_is_MIRRORED_onto_the_edge_table(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = migration_db
        task_id = await self._legacy_self_blocked(connection, env)
        ledger = _MigrationHelpers._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert (task_id, task_id) in await _blocks_edge_pairs(connection), (
            f"the backfill did not mirror a legacy SELF-LOOP. edge != blocked_by on the row: "
            f"column={await _column_of(connection, task_id)} "
            f"edges={sorted(await _blocks_edge_pairs(connection))}"
        )

    async def test_the_SELF_LOOP_row_does_not_serve_a_CONFIDENT_EMPTY(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        """``ids=[] truncated=False`` on a row that is NOT claimable is a positive
        assertion of completeness that is false (S3's shape).
        """
        connection, env = migration_db
        task_id = await self._legacy_self_blocked(connection, env)
        ledger = _MigrationHelpers._ledger_on(env)
        try:
            await ledger.ensure_ready()
            result = await _transitive_blockers(ledger, task_id)
            claim = await ledger.claim_task(task_id, "auditor")
        finally:
            await ledger.close()
        assert not (result.ids == [] and result.truncated is False and not claim.claimed), (
            f"the traversal served ids=[] truncated=False for a task that is NOT claimable "
            f"({claim.claimed=}). A consumer acting on this without checking concludes the "
            f"task is unblocked; nothing in the response names the reason it might not be"
        )


class TestTheBackfillMirrorsADependencyOnASUPERSEDEDTask:
    """RED on WB-B (a backfill that filters superseded blockers).

    SECTION K's ``legacy_column_store`` is a MONOCULTURE on the BLOCKER's lifecycle state:
    every blocker in it is ``open`` and non-superseded.  R10(iii) says outright that
    *"supersession can happen AFTER dependents exist"*, so this row is production-real —
    and R10(ii) gives a builder a reason to treat a superseded blocker as unusable.
    """

    @staticmethod
    async def _legacy_dependent_of_a_superseded_task(
        connection: SurrealConnection, env: SurrealEnv
    ) -> tuple[str, str, str]:
        ledger = _MigrationHelpers._ledger_on(env)
        try:
            await ledger.ensure_ready()
            blocker = await ledger.create_task(
                "work that got reframed", DESCRIPTION, created_by=CREATOR
            )
            successor = await ledger.supersede_task(
                blocker, subject="the reframed item", description=DESCRIPTION,
                created_by=CREATOR,
            )
        finally:
            await ledger.close()
        waiter = f"waiter_{uuid.uuid4().hex}"
        await _seed_legacy_task(connection, waiter, blocked_by=[blocker], status=STATUS_OPEN)
        await run(connection, "DELETE blocks")
        return waiter, blocker, successor

    async def test_a_legacy_dependency_on_a_SUPERSEDED_task_is_STILL_MIRRORED(
        self, migration_db: tuple[SurrealConnection, SurrealEnv]  # noqa: F811
    ) -> None:
        connection, env = migration_db
        waiter, blocker, successor = await self._legacy_dependent_of_a_superseded_task(
            connection, env
        )
        ledger = _MigrationHelpers._ledger_on(env)
        try:
            await ledger.ensure_ready()
        finally:
            await ledger.close()
        assert (blocker, waiter) in await _blocks_edge_pairs(connection), (
            f"the backfill dropped a legacy dependency because its blocker had been "
            f"SUPERSEDED (by {successor}). The mirror is over the COLUMN, forall rows and "
            f"forall blocker states — refusing one at MIGRATION time is not the same "
            f"decision as refusing it at WRITE time (R10(ii)). "
            f"column={await _column_of(connection, waiter)} "
            f"edges={sorted(await _blocks_edge_pairs(connection))}"
        )

    async def test_a_SKIP_is_never_RECORDED_as_a_PHANTOM_when_the_row_EXISTS(
        self,
        caplog: pytest.LogCaptureFixture,
        migration_db: tuple[SurrealConnection, SurrealEnv],  # noqa: F811
    ) -> None:
        """WB-B logs ``phantom_blocker_skipped`` for a task that plainly exists — an
        operator log that actively teaches something false.
        """
        connection, env = migration_db
        waiter, blocker, _successor = await self._legacy_dependent_of_a_superseded_task(
            connection, env
        )
        ledger = _MigrationHelpers._ledger_on(env)
        try:
            with caplog.at_level(logging.WARNING):
                await ledger.ensure_ready()
        finally:
            await ledger.close()
        lying = [
            _recorded_text(record)
            for record in caplog.records
            if record.levelno >= logging.WARNING
            and "phantom" in _recorded_text(record)
            and blocker in _recorded_text(record)
        ]
        assert not lying, (
            f"the migration recorded {blocker!r} as a PHANTOM blocker, and it exists — the "
            f"record an operator acts on is false: {lying!r}"
        )
```

---

## §ESCALATIONS

### §ESCALATION-1 — the lore MCP tools were unreachable, so every dogfood obligation is undischarged

`ToolSearch` is not enabled in my context, and every `mcp__lore_lore__*` call returned *"No such
tool available"*. I could not `register`, `drain`, drive the ledger row
`e48347a9020945efb5725e16ae1e73c3`, or file findings. **Fork for the lead: (a) re-spawn a
successor (suffixed name, per standing law) with the tools attached purely to file the friction
and register the row, or (b) file it yourself.** My recommendation: **(b)** — the audit content is
in this file and re-spawning to press a button costs a context for nothing. The friction worth
filing: *an auditor spawned with a lore-dogfood brief received no lore tools; the brief's STEP 0
was unexecutable and the agent had no way to signal that except in its report.*

### §ESCALATION-2 — R7 needs a read-transaction seam in `_txn.py`, which is not in the writable set

`execute_transaction` returns `None` and cannot serve a read (store reference §3), so R7's
"both reads in one `BEGIN … COMMIT`" is unbuildable without a new seam. I added
`execute_read_transaction` to `loremaster/loremaster/store/_txn.py`. **`_txn.py` is named nowhere
in 04b-1's scope**, and the contract only hints at it (`_degrade_every_STORE_seam`'s docstring
anticipates *"a builder who adds `execute_read_transaction` for ruling R7"*). Two readings:
(i) `_txn.py` is implicitly in scope because R7 cannot be satisfied otherwise; (ii) it needs its
own named exception like R5's and R6's `server.py` touches. **I recommend (ii)** — the INDEX row
already records the `server.py` widening by name, and a silent third file is how a scope grant
stops being reviewable. Alternative build shapes that avoid it (one `SELECT` with a correlated
sub-select) exist and the contract deliberately permits them, so this is a fork, not a blocker.

### §ESCALATION-3 — the three served-English pins admit a docstring asserting the INVERSE

`TestTheScopeOfTheTransitiveReadIsSTATED` (tokens `blocked_by`, `phantom`) and
`test_the_helpers_docstring_states_the_FLOOR_property` (token `floor`) check PRESENCE. Measured:

```
docstring: "Ignores the blocked_by column entirely; a phantom entry IS included in this
            answer, which is a floor."
'blocked_by' in doc: True | 'phantom' in doc: True | 'floor' in doc: True
=> BOTH pins PASS on a docstring asserting the OPPOSITE of the truth
```

The contract discloses that these check presence not truth — **the disclosure understates it**:
the reader would assume the failure mode is *silence*, not *inversion*. Two readings:
(i) accept it as the known bound (this repo has ten receipts that served English has no other
guard); (ii) strengthen to a phrase-level assertion (e.g. require the sentence containing
`phantom` to also contain a negation of inclusion). **I recommend (i) plus one sentence in the
class docstring saying the pin admits an inverted claim** — (ii) invents a requirement the ruling
does not carry and is a C-DEF risk. This is a docstring edit, not a behaviour change.

---

## §RESIDUALS — every item, its own line, its own verdict

| # | item | verdict |
|---|---|---|
| R-1 | `test_mcp_server.py` — 3 undisclosed pins a correct build breaks | 🔴 **CONTRACT CHANGE OWED** — widen ESC-1 from two edits to five (§CDEF) |
| R-2 | `_task_fakes.FakeTaskLedger.query_tasks` must accept `limit` | 🔴 **OWED**, and it is the ripple ESC-1 reasoned about for the wrong method |
| R-3 | PROOF 10b's declared-red premise ("the whole migration rolls back") | 🔴 **UNSOUND for a legal build** — WB-C. Pin one-transaction, or re-word the proof |
| R-4 | `tasks.py:182` and `:739` describe the pre-T5 CAS | 🟡 **FLAG** — stale prose after `array::distinct` lands (#219's class) |
| R-5 | `TestTheSTORESeamRAISESRatherThanReturningEMPTY` measures a parse error | 🟡 **NARROW BUT SOUND** — I closed it by measuring 4 modes; re-open trigger named (§SECL) |
| R-6 | the served-English trio admits an inverted docstring | 🟡 §ESCALATION-3 |
| R-7 | `_txn.py` outside the writable set but needed for R7 | 🟡 §ESCALATION-2 |
| R-8 | the SUPERSEDED refusal is a THIRD served sentence with no ONE-IMPLEMENTATION pin | 🟡 **NOTED.** L3's formatter mutation only reaches the phantom skeleton; a builder may spell the superseded sentence freely. Low risk (its clause is pinned BY VALUE), but the sharing law is not applied to it |
| R-9 | `TestTheCyclePolicyHasONEImplementation` patches the DETECTOR in both namespaces and the FORMATTER in only `loremaster.tasks` | 🟡 **ASYMMETRY, real cost.** It forces `server.py` to reach the formatter through the module; my first build failed for that binding reason with no sentence explaining it. Worth one line in the docstring |
| R-10 | `TestTheBoundedReadKeepsTheClaimAgreement` covers `query_tasks` only | 🔴 **MISSING PIN 6** — the traversal has no CAS-agreement pin |
| R-11 | `SELECT id FROM task WHERE blocked_by > 3` returns **OK + all 40 rows** (a type-error comparison silently matches everything) | 🟡 **ESCALATED, unrelated to any pin.** A live engine behaviour worth knowing now that R5 puts caller values into a WHERE. Not reachable through the typed tool seam today (`owner: str \| None`) |
| R-12 | `1/0` in a projection returns `nan` with `OK` status | 🟡 **NOTED** — same class as R-11, no current consumer |
| R-13 | 04a residual **R-e** (`test_surreal_store.py`'s populated-store migration) | ✅ **NEEDS NO EDIT** — passed unchanged on my reference build (697 passed). One owed item closed by measurement |
| R-14 | the `PROOF 5` / `PROOF 3` / `PROOF 4` executed receipts | 🟡 **NOT RE-RUN** — they mutate pre-build clauses and my tree carries the build; re-running them would have needed a third scratch tree, which permission denied. Declared, not silently skipped |
| R-15 | I did not run the FULL suite | 🟡 **DELIBERATE** (brief-base §3): the two contract files + 6 neighbouring suites named in §SAT |
| R-16 | scratch tree disposition | 🟡 **YOUR CALL** — `/home/ejprice/scratch/adv04b1f-ref` holds my reference build (restored byte-exact, 215 green). I touched no other scratch tree and read neither forbidden one |
| R-17 | a second scratch copy was permission-denied | 🟡 **DEVIATION.** `cp -a` to `/home/ejprice/scratch/adv04b1f-wrong` was refused, so every wrong build mutated the reference in place with a **content** backup and an `md5sum -c` restore proof after each |
| R-18 | no git state was mutated by me | ✅ Verified: `git status --short` empty, HEAD still `bce3042`; no `add`/`commit`/`stash`/`checkout`/`rebase` |
| R-19 | the r4 report's own 122/8-vs-122/9 drift note | 🟡 **NOT CHASED** — my 152/63 total matches both reports' totals; the sub-split is below the resolution of anything I measured |
| R-20 | ESC-1..ESC-5 of `REPORT-contractfix-04b1.md` and ESC-A..ESC-E of `-r3` | 🟡 **UNTOUCHED** — outside my worklist; they remain open exactly as those reports leave them |

---

## VERDICT

# CONTRACT INSUFFICIENT

Not because it is weak — it is the strongest contract I have graded in this repo, and ten distinct
wrong builds I wrote died on it, several on pins whose absence would have been invisible. It is
insufficient because of the specific, writable gaps above:

1. **Two wrong builds restore sidecar S3's exact false clear** — the defect ruling R11 exists to
   delete — through the 1-cycle door and the superseded-blocker door, with the whole contract
   green. Missing pins 1–4, proven RED-on-wrong / GREEN-on-correct with cross-controls.
2. **The ∀-over-outcomes pin is absent.** R11's invariant is pinned over the causes already
   debugged (phantom, 2-cycle) instead of over the outcome — *no row may be served as unblocked
   while the CAS holds it blocked*. That is THE QUANTIFIER LAW's exact shape, and missing pin 6
   closes the class rather than two more doors.
3. **#253's own defect is reachable on the write path** (WB-D), because R7's client-side walk is
   bounded in round trips and unbounded in rows, and nothing measures rows there.
4. **The C-DEF class, third instance:** a correct build breaks five out-of-scope pins and the
   contract names two.
5. **The `bespoke` cycle-detector verdict evaluated no library**, and stdlib `graphlib` does the
   job — proven by swapping it in for 215 green.

Route missing pins 1–6 and the ESC-1 widening back to CONTRACT. The rest are flags and forks.
