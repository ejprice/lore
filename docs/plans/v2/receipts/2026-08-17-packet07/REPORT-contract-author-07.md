# REPORT — contract-author-07 (packet 07: store error-honesty / classification)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State:** done — **ADVERSARY FIX-WAVE complete** (adversary-07 returned CONTRACT
  INSUFFICIENT; all findings addressed — F0/F1/F5/F2 fixed, F3 fixed, F4/F6/Minor noted; §9).
  Ready for a delta-adversary pass. Consolidated new pins: **17 (6 RED / 11 GREEN)**, all
  ruff+mypy clean. Prior state (CHECKPOINT 2) preserved below.
- Prior CHECKPOINT 2 (post operator-rulings #5010, items 3+4 folded in): all four items
  covered — #144 posture RED contract; #118/#119 verdicts; item 3 (#124 DDL-coverage) GREEN +
  right-sized; item 4 (query-too-complex) investigated — branch is LIVE, no change.
- **⚠ ITEM 4 COURSE-CORRECTION (honesty):** my first item-4 probe concluded the
  recursion-depth branch was DEAD on 3.2.4 — a FALSE-NEGATIVE (proxy operator shapes). The
  EXISTING live tests were the control that caught it: the branch is LIVE on 3.2.4. I retracted
  the item-4 design fork I had sent the sidecar (#5012) the moment I caught it. No harm — flagged
  immediately; the lesson (a probe needs a control) is in §8.
- **HEADLINE FINDING — the packet's fix work was already done.** #118 and #119 were fixed
  at **`8f24e11` (2026-07-13)**, the same day the findings were filed (inside the #102
  audit cycle), and their live-derived pins + the standard-gate `[real]`-tier
  `TestLiveEngineClassification` instrument are **GREEN on the CURRENT engine (3.2.4)** —
  re-run + independently probed. **There is no live classification defect for #118/#119
  and no honest RED for them.** I did NOT fabricate a RED (that would fabricate a defect).
- **The one genuine RED is #144's posture** — the multi-statement-through-bare-`.query()`
  bound is enforced only by a per-module hand-list; the runtime guard has no
  single-statement check today. That is a real, RED-able, low-cost consolidation.
- **Deviation:** the mandated probe instrument `scratchpad/contract-v5/capture_engine.py`
  is gone (scratchpad). Durable replacement written: `scripts/probe_store_error_classes_07.py`.
- **Packages considered:** `surrealdb` SDK statement splitter/parser — READ the installed
  source (`surrealdb/request_message/sql_adapter.py`: only a naive `.split(";")` joiner,
  no statement-count validation, no literal handling) → **bespoke** (the internal-`;`
  single-statement predicate; and reuse `_txn._assert_envelope_integrity`, which already
  implements it — keep_with_trigger on the SDK: re-open if a future SDK ships a parser).
- **Reuse ledger:** new test-local symbols, all dispositioned — #144 offline leg:
  `_bare_query_multi_statement_literals_in`/`_..._sites` (**REUSED** `_talks_to_surrealdb` +
  `_is_connection_receiver` + `_txn._assert_envelope_integrity`); `_multi_statement_violations`
  (getattr shim, HAND-ROLLED). Item 3 (#124): `_ddl_generators`/`_declared_tables` (**REUSED**
  `_enforced_relations_scaffold.statements`; DERIVED the generator set rather than reuse
  `ALL_DDL_GENERATORS`, which is a hand-list missing 2 generators) · `_table_constants`
  (HAND-ROLLED — a `vars()` filter, nothing to reuse). Builder flags: promote
  `_talks_to_surrealdb` to a shared scaffold (it lives in a contract file); the runtime detector
  must REUSE `_txn._assert_envelope_integrity`.
- **Graded:** verdicts rest on HEAD `82e2587` · `git rev-parse HEAD` = `82e2587` · SAME.
- **Decisions needed (LEAD/operator) — decisions 1-3 below were RESOLVED by rulings #5010;
  the OPEN one is #4:**
  1. (RESOLVED #5010) Reduced shape approved — #118/#119 resolve-no-builder.
  2. (RESOLVED #5010) #144 posture Option A-cheap approved (two legs + delete scattered pins).
  3. (RESOLVED #5010) #124 coverage pin PULLED IN (item 3), NOT deferred.
  4. **OPEN — item 3 depth trade (a value-vs-depth fork I right-sized; operator ratifies).**
     I built #124's coverage at the **CONSTANT level** (every `*_TABLE`/`*_RELATION` constant ∈
     declared) rather than a **string-level write-SITE scanner**. Reason (reach-attack STOP-rule):
     every production write targets a table via a constant (discovery §B.2), so the realistic
     regression (new table+write, no DDL) reddens the constant pin — WITHOUT a brittle SurrealQL
     string parser that false-matches prose/docstrings (the reach-attack antipattern). STATED
     BOUND: a hypothetical LITERAL-table production write (not an idiom) is uncovered; re-open
     trigger named (§7). **Ratify the constant-level shape, or ask for the deeper string-level
     write-site scan?** (§7). Also confirms fork 1 (extensions scoped OUT, #375-owned).
- **Receipt pointers:** #144 contract = `test_retry_seam.py::TestBareQueryMustCarryExactlyOneStatement`
  (runtime) + `::TestNoBareQueryCarriesAMultiStatementLiteral` (offline) — 3 RED/5 GREEN (§5);
  item-3 contract = `test_ddl_write_target_coverage_124.py` — 5 GREEN (§7); probes =
  `scripts/probe_store_error_classes_07.py` (§4), `scripts/probe_query_complexity_07.py`
  (§8, item 4); sidecar ruling = `docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md`;
  item-3 discovery = `ddl-coverage-scout-07` (map in §7); fix commit `8f24e11`;
  findings #118/#119/#144/#124.

---

## 1. Per-finding verdict (the brief's central ask)

| Finding | Underlying CODE defect | Instrument | Re-grounded on 3.2.4 | **Verdict** |
|---|---|---|---|---|
| **#118** (ASSERT marker was `"assert"`; engine says `"must conform to"`) | **FIXED** @ `8f24e11` — `_ASSERT_VIOLATION_MARKER = "must conform to"` (`_txn.py:539`) | **PRESENT** — `TestLiveEngineClassification` provokes a real ASSERT violation + cross-controls + anti-drift pin, runs in the standard gate | **GREEN** (live suite 4/4 + probe A/D) | **already-fixed, pins present & live-grounded, confirmed 3.2.4. No live defect; no RED possible.** |
| **#119** (`failed_statements[0]` is a cascade entry; #93's premise false) | **FIXED** @ `8f24e11` — `_domain_root_cause`/`_rollback_verdict` semantic (first non-cascade; degrade to last), positional selection banned both ends (`_txn.py:683-766`) | **PRESENT** — `TestTxnRootCauseSelection`, live-derived cascade shapes; #93's pins already re-grounded | **GREEN** (probe A+C confirm the exact shapes) | **already-fixed, #93's pins re-grounded, confirmed 3.2.4. No live defect; no RED possible.** |
| **#144** (#124 misdiagnosed: not silent data loss — `query()`'s statement[0]-only validation hid retryable conflicts) | Mechanism CLOSED — `execute_transaction`→`query_raw`+`_failed_statements` checks EVERY statement; `_is_retryable_conflict` `any()` sees a conflict at any position | "retry sees conflict in a LATER statement" **PINNED** (`test_surreal_store.py:2921`, both positions); **posture pin was the OPEN gap → now written RED**; #124 row amend OUTSTANDING | probe B confirms the `query()` gap on 3.2.4; probe C confirms the conflict shape | **misdiagnosis confirmed live; mechanism closed; posture consolidation is the genuine RED contract (this deliverable).** |

Every "FIXED" grounds on `8f24e11` (2026-07-13), *"the rollback verdict becomes semantic —
the hot-row mint stops dying at 8-way (#102, #118, #119)"*, ancestor of HEAD. Findings dated
2026-07-13; fix landed same day, predates the 2026-07-22 split that created packet 07.

**Rename-sweep law (bare-anchor sweep):** no live pin certifies the retired world (the
`"assert"` marker, the fictional `"fulfil the following assertion"` text, `[0]`/`[-1]`
positional selection) — only explanatory comments. The one live `failed_statements[-1]`
(`_txn.py:766`) is the legitimate degenerate-case degradation, not the old bug.

---

## 2. Re-grounding on the CURRENT engine (mandatory probe — passed)

`spike-surreal ws://127.0.0.1:18000` runs **`surrealdb-3.2.4+20260803.93ab219`** (floating
`v3.2` drifted 3.1.5→3.2.1→3.2.4; every fixture is provenance-stamped 3.1.5 and had never
been re-probed on 3.2.4). The `[real]`-tier `TestLiveEngineClassification` suite runs in the
**standard gate** (`addopts` has no `-m "not real"`; no skip marker; harness raises, never
skips):

```
$ cd loremaster && uv run python -m pytest tests/test_surreal_store.py -k TestLiveEngineClassification -q
4 passed, 174 deselected in 0.61s
```

So on 3.2.4: real ASSERT → `assert violation`; real coercion → `field coercion`; no
collision; the anti-drift pin confirms `"must conform to"` / cascade / commit-abort texts +
`>=3` ERR statuses still match. **Markers have NOT drifted on 3.2.4.**

---

## 3. #144 — the posture, settled

The `query()` statement[0]-only gap is closed *at `execute_transaction`*. #144's "settle the
full-statement validation posture" concerns the ENFORCEMENT of the invariant *a
multi-statement string must never ride bare `.query()`* — currently a **scattered per-module
hand-list** (`TestNoMultiStatementDdlRidesABareQuery` scans only `floor_calibration.store` +
`lease`; `comms_schema`/`message_ledger`/`graph_surreal` carry their own copies). That is the
"reach is a hand-list" antipattern. Production bare-SDK-`.query()` sites (`scout._scout_query`,
`inbox_awaiter`, `run_query`, `bootstrap_session`'s DEFINEs) are ALL single-statement — **no
live defect**; the gap is a hypothetical future multi-statement bare-query helper.

**Sidecar ruling** (`fable-sidecar-07`, `DESIGN-sidecar-144-posture.md`, via consult #5005):
**Option A-cheap** — add ONE predicate to the autouse `_sdk_guard` (which already observes
every bare `.query()`, reach already a checked variable): when a bare `.query()` (NOT
`.query_raw()`) carries more than one top-level statement, flag it. ⚠ **CORRECTED in §9 (F1):
this paragraph's "5 copies / scattered per-module pins" is a FABRICATED count — there is exactly
ONE such pin (`TestNoMultiStatementDdlRidesABareQuery`, floor_cal+lease), and the offline leg is
NOT its subsumer; read §9.** Original text preserved below as the record. Not a sweep
(nothing to sweep), not a bespoke package-wide AST guard (right-sizing rejects that). Detector
= positive "exactly one top-level statement" (internal-`;`), packages-checked, scoped to
`.query()`, with a stated `;`-in-literal bound + re-open trigger. Fallback if it entangles with
`query_raw`: Option B + file the hand-list as a finding; never A-expensive. **#124's coverage
pin stays DEFERRED with #124; #144's #124-row amendment carries it forward as a named still-open
item so "mechanism corrected" ≠ "#124 closed".** I asked the meta-question; the sidecar
decides-with-recommendation (mundane pin shape); the operator owns importance.

**Sidecar sharpenings (design doc §5), both incorporated into the contract:** (1) the
`query`-vs-`query_raw` distinction is BY METHOD NAME (the guard already records
`escape.method`) — `query_raw` (execute_transaction's path) is EXEMPT, `query` gets the
single-statement assertion; and the check is ORTHOGONAL to the escape check (assert on EVERY
intercepted `query` call, not just flagged escapes). (2) The runtime leg needs a PAIRED offline
AST leg (mirroring the retry-escape guard's own two-leg structure) — REQUIRED so the scattered
OFFLINE pins can be deleted without a coverage regression, reusing `_talks_to_surrealdb`/
`_is_connection_receiver` (derived reach), not a new hand-list. Both delivered (§5).

**#124 amendment (deliverable 2):** #124's row STILL carries the false headline *"SurrealDB
3.1.5 SILENTLY LOSES concurrent first-writes…"*. It needs amending to the real mechanism
(the `query()` gap hid retryable conflicts). ⚠ #144's honesty bound requires reading the
original harness FIRST — **it EXISTS** at `scratchpad/102-recovery/` (`probe_txn_control_no_sequence.py`
/ `_predefined_table.py` / `_warmup.py`), so the reconciliation is dischargeable. This is a
lead/builder docs+finding task (not a test pin). Store reference §5 already carries the
correction + the open-reconciliation note.

---

## 4. Probe transcript (3.2.4) — receipt

Instrument: `scripts/probe_store_error_classes_07.py` (committed; durable replacement for the
lost `capture_engine.py`). Run: `cd loremaster && uv run python ../scripts/probe_store_error_classes_07.py`.

```
engine version: surrealdb-3.2.4+20260803.93ab219

PROBE A — multi-statement DOMAIN rollback shape (ASSERT violation mid-txn)
  idx 0  OK   'None'
  idx 1  ERR  'The query was not executed due to a failed transaction'
  idx 2  ERR  "Found 'BOGUS' for field `state`, with record `classify_probe:bad`, but field must conform to: $value INSIDE ['open', 'done']"
  idx 3  ERR  'The query was not executed due to a cancelled transaction'
  idx 4  ERR  'Cannot COMMIT: the transaction was aborted due to a prior error'

PROBE B — the SDK .query() statement[0]-only gap (#144/#124 mechanism)
  bare .query() RAISED nothing; returned: None
  independent read-back of rows the txn tried to write: [{'count': 0}]
  -> rolled back cleanly: no committed rows, but bare .query() said nothing

PROBE D — field-coercion rejection text
  idx 1  ERR  "Couldn't coerce value for field `ordinal` of `classify_probe:coerce`: Expected `int` but found `'not-an-int'`"

PROBE E — 'query too complex' (expression recursion depth) text
  (no recursion-depth error at 400 OR-clauses; engine accepted it)

PROBE C — a RETRYABLE conflict surfaced in a NON-FIRST statement
  idx 0  OK   'None'
  idx 1  ERR  'The query was not executed due to a failed transaction'
  idx 2  ERR  'The query was not executed due to a failed transaction'
  idx 3  ERR  'Cannot COMMIT: Transaction conflict: Resource busy. This transaction can be retried'
  'can be retried' marker rides index/indices: [3]   is the marker on the FIRST ERR entry? False
```

Each read maps to a fixture it grounds (all confirmed byte-shape-accurate on 3.2.4):
Probe A = `TestTxnRootCauseSelection._live_domain_rollback_response`; Probe B = the
#144/#124 mechanism reproduced live (a later statement's rejection is invisible through bare
`.query()`; txn rolled back, 0 rows); Probe C = `_live_conflict_rollback_response` (marker on
the LAST entry, non-first); Probe D = `_COERCION_ENGINE_TEXT`.
**Residual (Probe E):** 400 OR-clauses no longer trips the recursion-depth rejection on 3.2.4;
`_ERROR_CLASS_QUERY_TOO_COMPLEX` has no live provocation (fake-pinned only). Out of
#118/#119/#144's core scope — flagged for a lead scope call.

---

## 5. The RED contract — two legs in `test_retry_seam.py`

Per the sidecar's sharpenings (§5 of its design doc): the invariant needs the SAME two-leg
structure the retry-escape guard already has (an offline AST lint + a runtime gate — *"the
lint covers all code weakly, the gate covers executed code absolutely"*). Both legs reuse
existing machinery — **no new hand-list, no new AST walker, no new predicate** (ONE
IMPLEMENTATION). Verified against HEAD `82e2587` (spike-surreal 3.2.4), ruff+mypy clean:

```
$ uv run python -m pytest tests/test_retry_seam.py \
    -k "TestBareQueryMustCarryExactlyOneStatement or TestNoBareQueryCarriesAMultiStatementLiteral" -v
FAILED  TestBareQueryMustCarryExactlyOneStatement::test_a_multi_statement_bare_query_is_flagged_even_inside_the_driver
FAILED  TestBareQueryMustCarryExactlyOneStatement::test_a_semicolon_joined_non_BEGIN_pair_is_also_flagged
FAILED  TestBareQueryMustCarryExactlyOneStatement::test_the_semicolon_in_a_literal_is_a_KNOWN_BOUND
PASSED  TestBareQueryMustCarryExactlyOneStatement::test_a_single_statement_bare_query_is_NOT_flagged
PASSED  TestBareQueryMustCarryExactlyOneStatement::test_a_multi_statement_query_RAW_is_NOT_flagged
PASSED  TestBareQueryMustCarryExactlyOneStatement::test_the_runtime_guard_OBSERVES_the_bootstrap_define_statements
PASSED  TestNoBareQueryCarriesAMultiStatementLiteral::test_no_production_bare_query_site_passes_a_multi_statement_literal
PASSED  TestNoBareQueryCarriesAMultiStatementLiteral::test_the_scan_actually_SEES_a_multi_statement_literal
3 failed, 5 passed, 564 deselected in 2.92s
```

**RUNTIME leg — `TestBareQueryMustCarryExactlyOneStatement` (the invariant).** Reuses the
runtime-guard test infra (`_install_guard_aimed_at_this_file`, `_driver()`, `live_env`,
`connect_admin`). New surface `GuardReport.multi_statement_violations` read via a `getattr`
shim → RED is BEHAVIOURAL (not AttributeError), file stays collectable.
- **3 RED (right reason — surface not built):** a multi-statement bare `.query()` (BEGIN AND
  `;`-joined non-BEGIN — the discriminator against a `BEGIN`-keyed detector) must be flagged;
  the `;`-in-literal known-bound must hold. Made INSIDE a driver attempt on purpose — the
  invariant is ORTHOGONAL to the escape check (sidecar sharpening #1: assert on EVERY
  intercepted `query` call, keyed on method name, not just flagged escapes).
- **3 GREEN controls/proofs:** single-statement `.query()` NOT flagged; multi-statement
  `.query_raw()` (the safe path) NOT flagged (scopes to `.query()` by METHOD NAME); and the
  **derived-reach proof** — the guard observes `bootstrap_session`'s `_define_namespace`/
  `_define_database` bare `.query()` DEFINEs (`intercepted=3`) — proving a checked-reach guard
  covers what the `scout+inbox_awaiter` hand-list omits.

**OFFLINE leg — `TestNoBareQueryCarriesAMultiStatementLiteral`.** Mirrors
`TestNoProductionCodeCallsTheSdkOutsideTheSeam`. Exists so a NEW multi-statement bare-`.query()`
literal at an untested-branch site is caught (the runtime leg is executed-only). ⚠ **CORRECTED
in §9 (F1): this is NOT a "consolidation target" for scattered pins — there is ONE such pin and
this leg is NOT its subsumer (narrower in 3 dims); the retry-escape lint+guard preserves that
pin's coverage.** Original "consolidation/REQUIRED-so-scattered-pins-can-delete" text preserved
below as the record.
Reuses `_talks_to_surrealdb` (deny-by-default derived reach) + `_is_connection_receiver` +
`_txn._assert_envelope_integrity` (the SAME single-statement predicate `compose` uses).
- **2 GREEN:** the consolidation pin (**no production bare-`.query()` site passes a
  multi-statement literal** — independently grounds the "no live defect" verdict via a concrete
  scan); + a positive/negative control proving the scanner fires on a planted literal and spares
  single-statement / `query_raw`.
- ⚠ STATED LIMIT (inherited from the retry lint): receiver-NAME-keyed (`_is_connection_receiver`)
  and blind to runtime-composed strings — that blind spot is precisely the RUNTIME leg's job
  (receiver-blind, patches the class). Two legs, each blind where the other is strong.

**Builder job (encoded in the contract prose, NOT done here):** add
`GuardReport.multi_statement_violations`; add the single-statement predicate to `_sdk_guard._guard`
scoped to method `query` — **REUSING `_txn._assert_envelope_integrity`, not cloning it** (both
legs + `compose` then share ONE predicate); extend the autouse fixture to assert `not
report.multi_statement_violations`; DELETE the scattered `TestNoMultiStatementDdlRidesABareQuery`-
family pins (a removed-behaviour item for the adversary to adjudicate — safe now that the offline
leg replaces their coverage).

**Fixtures-must-discriminate self-check** — what wrong build survives?
- flags ALL `.query()` → killed by the single-statement controls (both legs).
- flags on statement count ignoring the method (would flag `query_raw`) → killed by the
  `query_raw` controls (both legs).
- keys on the `BEGIN` literal → killed by the non-BEGIN pair pins (both legs) + the
  `;`-in-literal bound.
- Handed to the **contract-adversary's REACH ATTACK** deliberately (checkpoint before adversary):
  confirm each leg's reach is a checked variable, and perturb the `;`-in-literal bound.

Touched files ruff+mypy clean: `test_retry_seam.py`, `scripts/probe_store_error_classes_07.py`.

---

## 6. Open items / flags for the lead
- The one OPEN decision is #4 (item-3 depth trade — see SUMMARY BLOCK / §7). Decisions 1-3 are
  resolved by #5010.
- #124's row STILL carries a false headline ("SurrealDB SILENTLY LOSES concurrent first-writes")
  and needs amending to the real mechanism, carrying the coverage-pin note forward. The
  reconciliation harness `scratchpad/102-recovery/` EXISTS (dischargeable). Docs/finding task.
- Store-reference note owed (docs, flagging not deciding): §5/§8 should record that the 3.1.5
  parser recursion-depth limit PERSISTS on 3.2.4 for the fulltext `@@`/RRF query shape (~120
  clauses) but NOT for simple-operator chains (probed to 40000) — the shape-specificity is new.
- Nothing touches production code. Probes read/write throwaway `probe07*` DBs on the TEST store
  (`:18000`), dropped on exit; production `:18500` untouched. I created no git state (lead commits).

---

## 7. Item 3 — #124 DDL-coverage contract (`test_ddl_write_target_coverage_124.py`)

Operator ruling #5010 pulled in #124's owed instrument: *every table production writes to is
DEFINEd before first write.* A read-only discovery scout (`ddl-coverage-scout-07`) mapped it —
key findings, all cited to file:line in its report (delivered inline; the Write was blocked by
subagent policy, so its map lives in this section):
- **Declared side:** 11 `generate_*_ddl` in `surreal_schema.py`, NO single union point. The
  reusable sweep `_enforced_relations_scaffold.ALL_DDL_GENERATORS` is a **9-entry hand-list
  MISSING `generate_lease_ddl` + `generate_floor_calibration_ddl`** — so I DERIVE the generator
  set from the module instead (closing the hole by construction).
- **Write side:** production write targets are, without exception, a `*_TABLE`/`*_RELATION`
  **constant** interpolated into the write f-string (`type::record('{AGENT_TABLE}',…)` /
  `UPSERT {META_TABLE}` / `RELATE $a->{TO_RELATION}->$b`). Two escapes not statically
  recoverable: bound-RecordID-param writes (target `name`/`snapshot`, both declared) and the
  runtime extension `entity_tables()` loop. **No existing helper extracts table names.**

**What I built (right-sized — the key decision #4):** the invariant at the **CONSTANT level** —
`test_every_table_constant_value_is_a_declared_table` asserts every `*_TABLE`/`*_RELATION`
constant ∈ the derived declared set. **Why not a string-level write-SITE scanner:** the
reach-attack STOP-rule. A SurrealQL string parser that extracts targets from every write
statement would false-match prose/docstrings mentioning a verb, and is precisely the
brittle-reach antipattern the repo has the most receipts against. Since every production write
goes through a constant, the realistic regression — *a new table constant + a write, and the
`generate_*_ddl` forgotten* — reddens the constant pin directly. Both sides DERIVED (reach = a
checked variable): constants from `vars(surreal_schema)`, declared from every `generate_*_ddl`.

- **5 GREEN** (regression-prevention, production already holds the property): the invariant; the
  generator-reach pin (`test_the_declared_generator_reach_covers_every_generate_ddl_symbol` —
  RED if the derivation loses a generator); an anti-vacuity constant-reach pin; a POSITIVE
  CONTROL (`test_a_planted_undeclared_constant_would_redden_the_invariant` — the invariant's own
  comparison flags a planted ghost, proving green ≠ vacuous); a declared-side parse control.
- **FORK 1 (extensions scoped OUT — discovery-recommended, drafted so):** extension tables own
  no `*_TABLE` constant here (runtime, from `IngestBackend.entity_tables()`) and the #124
  property for that path is enforced at RUNTIME by `extension.ExtensionLifecycleNotReadyError`
  (#375) — the constant-level pin scopes them out by construction. **FORK 2 (bound-param):** moot
  at constant level — bound-param writes target `NAME_TABLE`/`SNAPSHOT_TABLE`, which are
  constants, hence covered.
- **STATED BOUND + re-open trigger:** a hypothetical production write with a LITERAL table name
  (not a constant) is uncovered — not a production idiom. Re-open: the day any write targets a
  table by literal name → make it a constant, or add the string-level write-site scan.
- Ruff + mypy clean.

**Decision #4 for you/operator:** ratify the constant-level shape (my recommendation, right-sized)
OR ask for the deeper string-level write-site scanner (broader — catches literal-table writes —
but reach-attack-prone; the discovery §C mapped it and I began it before the STOP-rule pivot).

---

## 8. Item 4 — `_ERROR_CLASS_QUERY_TOO_COMPLEX` investigation: the branch is LIVE (no change)

Operator ruling #5010 folded in: investigate the recursion-depth classifier branch on 3.2.4,
then settle its shape (pin-as-known-bound vs delete) with the sidecar.

**Verdict: the branch is LIVE on 3.2.4 — no dead branch, no design fork, no contract change.**

- My probe (`scripts/probe_query_complexity_07.py`) first concluded the limit was LIFTED: simple
  OR-chains to 40000, nested parens to 64000, fn-nesting to 32000, subqueries to 1000, even a
  bare `@@`-chain to 400 clauses — all execute FINE on 3.2.4. **This was a FALSE-NEGATIVE.**
- **The control that caught it was the EXISTING live tests**, not my probe:
  `test_bypassing_both_clamps_still_raises_a_classified_store_error` in
  `test_surreal_store.py::TestResidualRejectionStillLaunders` +
  `test_memory_backend.py::TestRecursionDepthClassificationAtRecallSeam` both **PASS on 3.2.4** —
  they run the REAL `hybrid_search`/`recall` RRF-fusion query with the clamps bypassed and assert
  the laundered `"query too complex"` label, which passes ONLY if the engine still emits
  `"recursion depth"`. So the marker matches and the branch fires on 3.2.4.
- **Root cause of my false-negative:** the recursion-depth limit is a WHOLE-QUERY parse-depth
  property. It is tripped by the full `@@`-chain EMBEDDED in `search::score`/`search::rrf`/the
  dual-arm UNION (finding #66's ~40-token/120-clause boundary), NOT by any isolated construct —
  parser recursion is NOT operator-agnostic, my working assumption. The "a probe needs a control"
  law, exactly: my probe lacked a positive control; the existing live tests were it.
- **Coverage is already adequate + green:** the 4 tests give both a unit pin (classifier maps
  "recursion depth" → label) AND a live provocation (the clamps-bypassed real query) that
  doubles as an anti-drift guard (RED if the engine rewords the marker OR lifts the limit).
- **No new pin needed.** Residue (docs, not contract): the unit fixtures' provenance says
  "captured live 3.1.5" — a refresh to "re-confirmed live 3.2.4 via the passing bypass tests"
  would be honest; and the store-reference note in §6. My probe is committed as an honest
  NEGATIVE-SPACE receipt (which shapes do NOT trigger it), docstring corrected in full.

**⚠ Reconciliation with the sidecar's #5013 (DESIGN doc §6) — I do NOT follow its Opt 3, and
here is why.** The sidecar recommended Opt 3 (keep the branch + an "inverse-live pin asserting
UNREACHABLE" + retire the "lying" fixtures). That recommendation was composed on my RETRACTED
dead-branch premise (it inherited the false-negative before my #5012/#5015 correction landed),
and it is **refuted by ground truth**: the branch is LIVE on 3.2.4 (the bypass tests pass). So:
- An inverse pin asserting UNREACHABLE **would FAIL on 3.2.4** — the query IS rejected. Not built.
- The 2 unit fixtures are **NOT the #118 disease** — the 3.2.4 engine DOES emit "recursion depth"
  (proven by the passing bypass tests), so they pin VALID classifier logic. Only the provenance
  comment is stale; no delete/replace.
- The live-provocation anti-drift guard the sidecar wanted **already exists and passes**
  (`test_bypassing_both_clamps` — RED if the engine rewords the marker or lifts the limit, the
  exact #336-drift alarm).
The sidecar's VALID residuals survive and I adopt them: commit the probe (lead), and the
store-ref note (§6) — with content "the limit PERSISTS on 3.2.4 for the RRF/@@ shape, NOT simple
chains". This is a case of running-test ground truth correcting a design inference; the operator
gets the CORRECT disposition (branch live, no change), not Opt 3.

---

## 9. Adversary fix-wave (adversary-07 → CONTRACT INSUFFICIENT → addressed)

adversary-07 (`REPORT-adversary-07.md`) verified the core invariants STRONG (4 wrong runtime
builds killed; #124 derivation genuinely derived; item 4 re-confirmed live) but found real gaps.
All addressed. New consolidated pin count: **17 (6 RED / 11 GREEN)**, ruff+mypy clean.

- **F0 (BLOCKER — routing-is-not-sharing) — FIXED.** A runtime detector that CLONED the `;`-logic
  instead of calling `_txn._assert_envelope_integrity` passed all 6 runtime tests (the adversary's
  `inline_predicate` build) AND silently broke the `;`-in-literal re-open trigger (measured on the
  runtime leg). Added **`test_the_runtime_leg_shares_the_txn_predicate_by_mutation`** (RED) — inverts
  the shared predicate, drives a single-statement bare `.query()`, asserts the verdict FLIPS; RED on
  a clone or an import-captured reference, GREEN only on a genuinely-shared call-time lookup. Also
  added **`test_the_offline_leg_shares_the_txn_predicate_by_mutation`** (GREEN — the offline leg
  already shares by construction, now mutation-proven, with a pre-mutation control). Mirrors the
  existing `test_the_two_scans_SHARE_their_predicates_rather_than_cloning_them`.
- **F1 (REQUIRED CORRECTION — fabricated count) — FIXED.** My "5 scattered per-module pins" was a
  FABRICATION inherited un-derived from the discovery/sidecar (the exact re-derive-inherited-numbers
  failure). **I independently RE-DERIVED it** (grep of the whole test tree for the
  `attr in {"query","query_raw"}` AST-ban shape → `test_floor_calibration_schema.py` ONLY): there is
  exactly **ONE** such pin (`TestNoMultiStatementDdlRidesABareQuery`, floor_cal+lease). Corrected the
  runtime + offline comment blocks + the builder-job: the offline leg is NOT its subsumer (it is
  narrower in 3 dimensions); the pre-existing **retry-escape lint+guard** preserves its
  route-through-seam coverage; deletion is SAFE (adversary-verified) but a separate, broader-property
  removed-behaviour decision; the `not-self`→`_is_connection_receiver` narrowing is accepted-with-note.
  ⚠ This correction also propagates to §5/§7 of this report and to
  `DESIGN-sidecar-144-posture.md` §5.2 (which carries the same fabricated "5 pins"/subsumer framing
  — a doc-fix owed there too, flagged for the lead).
- **F5 — FIXED.** Added **`test_a_multi_statement_bare_query_on_an_oddly_named_receiver_is_flagged`**
  (a `db`-named receiver, RED) — pins the runtime leg's receiver-blindness, the two-leg design's
  keystone (previously every runtime test used a `connection`-named receiver).
- **F2 — FIXED.** Added `_MULTI_STATEMENT_WITH_QUOTES_QUERY` + a pin (RED) that a multi-statement
  string whose statements contain quoted literals (real `;` separators, no `;` inside a literal)
  stays flagged — guards a future literal-aware detector against over-stripping.
- **F3 (residual) — FIXED.** Factored the #124 invariant comparison into a shared `_undeclared_constants`
  helper both the invariant pin and its positive control call (no longer a parallel copy).
- **F4 (residual) — NOTED** (adversary ruled note-not-pin): a corrupted `_declared_tables()` unioning
  all constants defeats the invariant + passes anti-vacuity — a TEST-helper sabotage, not a production
  regression; the realistic regression is caught. Documented in the declared-side control's docstring.
- **F6 + Minor (residuals) — NOTED**: the two-leg joint reach bound (oddly-named receiver OR
  runtime-composed string that no test executes) is INHERITED from the retry-escape guard and
  documented in the offline-leg bounds; the production-frame scoping of the runtime check is a
  self-correcting build-time concern. Both left for the builder, per the adversary's ranking.

**F1 self-note (the lesson):** I shipped a fabricated count into a contract about NOT shipping
un-derived counts — and it survived the sidecar, my brief, and my own report until the adversary's
independent grep. The fix that worked was re-derivation, exactly as the repo's law prescribes.
Pin counts after the fix-wave: runtime leg 9 (6 RED/3 GREEN) · offline leg 3 (GREEN) · item 3
5 (GREEN) — total 17 (6 RED/11 GREEN).
