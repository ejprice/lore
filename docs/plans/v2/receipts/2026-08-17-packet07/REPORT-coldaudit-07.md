# REPORT — coldaudit-07 (COLD REFUTE AUDIT, packet 07: store error-honesty)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **VERDICT: GO.** Every load-bearing claim independently re-established by a command I ran
  (builder ≠ grader). The build is test-infrastructure + docs + probe scripts only —
  **ZERO changes under `loremaster/loremaster/`** (production proper), so the deploy story
  is intact (the #118/#119 production fix is already at HEAD via `8f24e11`).
- Regression **623 passed, 0 failed, 0 error** (26.13s) — matches the builder EXACTLY. The
  1 `RuntimeWarning` is pre-existing (`_empty_subscription`, `TestEverySdkCallSiteActuallyRetries`
  `test_retry_seam.py:3216`), not a packet-07 symbol.
- **F0 load-bearing guarantee REPRODUCED under attack:** a scratch-copy inline `;`-clone that
  ignores the shared predicate turns `test_the_runtime_leg_shares_the_txn_predicate_by_mutation`
  RED (`assert []`), while the other 8 pins stay GREEN — a real discriminating pin, not a
  green-because-everyone-said-so. Provenance asserted inside the scratch tree.
- ruff clean (9 files); mypy 191 errors, **ALL** in 11 auth/roster/permission/email WIP files
  (#333 adjudicated-RED baseline), **ZERO** in any packet-07 file or new symbol. The brief's
  "~102" is stale — real HEAD baseline is 191 (builder D4 confirmed).
- #118/#119 "already fixed @ `8f24e11`" confirmed: ancestor of HEAD, dated Jul 13 2026, touches
  `_txn.py` (464 lines); live suite 11/11 on 3.2.4. Removed-behavior: git confirms **exactly ONE**
  file held the `{"query","query_raw"}` shape; its 54-line class is deleted; retry-escape lint
  reach over floor_cal+lease independently verified. #124 pin genuinely DERIVED (`inspect.getmembers`,
  not the 9-entry hand-list). Doc edits accurate + house-style. Corpse sweep CLEAN.
- **Packages considered:** none — no mechanism specified (audit-only; I built no reusable symbol).
- **Reuse ledger:** none — I introduced no production symbols (audit; scratch attack in
  `/tmp/coldaudit07-scratch-a`, disposable).
- **Graded:** `82e2587` (uncommitted working tree on HEAD) · `git rev-parse HEAD` = `82e2587` · **SAME**.
- **Decisions needed (LEAD) — none block the GO; all are lead EXIT tasks / confirmations:**
  1. Finding **#124's row STILL carries its false headline** ("SurrealDB 3.1.5 SILENTLY LOSES…",
     state `acknowledged`) — the packet EXIT owes the mechanism amendment + carry-forward of the
     coverage-pin deferral note (design sidecar §4 has exact wording). Store-ref §5 account already correct.
  2. Findings **#118/#119/#144 resolution-with-notes** (EXIT), not yet done.
  3. Builder's D3 question — provenance edits in `test_surreal_store.py`/`test_memory_backend.py`
     WERE brief-authorized (docs-step 2), are accurate, comment-only: **confirmed intended & correct.**
- **Receipt pointers:** regression §1 · F0 attack §2 · gates §3 · #118/#119 §4 · removed-behavior
  §5 · #124 derivation §6 · doc edits §7 · corpse+diff §8 · outstanding EXIT §9.

---

## Capability check (brief-base §4)
All tools the brief assumes are present: lore MCP (`ToolSearch "+lore"`), `lore_comms` (registered
`coldaudit-07`/`packet07-20260817`/cold-audit), spike-surreal 3.2.4 test store (`:18000`, up 39h),
pytest/ruff/mypy, git (read-only — I created no git state; the lead commits). `scratch_copy.sh`
present and used. One friction: `rm -rf /tmp/coldaudit07-scratch` was permission-denied, so I used a
fresh dir (`/tmp/coldaudit07-scratch-a`) — no impact on the audit. No blockers.

---

## §1 — Regression re-run (independent)
```
$ cd loremaster && uv run python -m pytest tests/test_retry_seam.py \
    tests/test_ddl_write_target_coverage_124.py tests/test_floor_calibration_schema.py -q
623 passed, 1 warning in 26.13s   [exit 0]
```
Matches the builder's claim (623p/0f/0e) EXACTLY. The single warning:
`test_retry_seam.py:3216 RuntimeWarning: coroutine '_empty_subscription' was never awaited` — in
`TestEverySdkCallSiteActuallyRetries` (a pre-existing test, NOT a packet-07 file/symbol; line 3216
is far outside the packet's diff, which is a pure append at line 9422+). Not a defect of this packet.

The 4 adversary-added share/keystone pins pass in isolation on the current tree:
```
$ uv run python -m pytest tests/test_retry_seam.py -k "<the 4 F0/F5/F2/offline-share pins>" -v
4 passed, 572 deselected in 1.74s
```

## §2 — F0: the load-bearing guarantee, reproduced UNDER ATTACK (not on faith)
The whole packet rests on the runtime multi-statement verdict coming from the SHARED
`_txn._assert_envelope_integrity`, not a private clone (routing-is-not-sharing, #102/#120).

**Read the production code myself** (`loremaster/tests/_sdk_guard.py`, `_is_multi_statement_query`,
`_sdk_guard.py:219-249`): it does `from loremaster.store import _txn` **inside** the function and
calls `_txn._assert_envelope_integrity(query_text)`, catching `_txn.TxnEnvelopeViolationError` —
genuine **call-time** module lookup, never an import-captured reference. And `compose()`
(`_txn.py:314-373`) calls the SAME `_assert_envelope_integrity(statement)` on every fragment — so
the guard routes to the one predicate `compose` uses (ONE IMPLEMENTATION, provable by mutation). The
runtime multi-statement check is inside `if site is not None:` (`_sdk_guard.py:374`) → scoped to
production frames, as the adversary's "Minor" noted.

**Independent scratch-copy attack** (`scripts/scratch_copy.sh /tmp/coldaudit07-scratch-a`, provenance
asserted: `loremaster.__file__ -> /tmp/coldaudit07-scratch-a/loremaster/loremaster/__init__.py`).
Replaced the shared-predicate call in `_is_multi_statement_query` with an inline private `;`-clone
(peel one trailing `;`, then any remaining `;` or a BEGIN/COMMIT keyword ⇒ multi) that does NOT call
`_txn._assert_envelope_integrity`:
```
tests/test_retry_seam.py::TestBareQueryMustCarryExactlyOneStatement
  ::test_the_runtime_leg_shares_the_txn_predicate_by_mutation   FAILED   (assert [])
1 failed, 8 passed, 567 deselected
```
FAILED for **exactly the right reason** — with `_assert_envelope_integrity` inverted, the clone did
not see the inversion, so the single-statement `.query()` was NOT flagged (`assert []`). The other 8
pins passed (the clone is behaviourally identical on the ordinary fixtures — precisely the adversary's
`inline_predicate` that survived all 6 pins BEFORE F0 existed). **Correct build → F0 GREEN (§1);
clone → F0 RED.** The pin genuinely discriminates. The offline-share pin
(`test_the_offline_leg_shares_the_txn_predicate_by_mutation`) carries a pre-mutation control
(single NOT flagged) then inverts and asserts single IS flagged — a proper mutation-share proof.

## §3 — Gates (ruff + mypy), independently
```
$ uv run ruff check <9 touched .py files>        -> All checks passed!
$ ./scripts/typecheck.sh                          -> EXIT=1; 191 error lines
```
The 191 mypy errors live in EXACTLY these 11 files (all auth/roster/permission/email WIP, the #333
adjudicated-RED baseline): `_auth_fixtures.py`, `test_allowlist_roster.py`, `test_auth_composition.py`,
`test_auth_identity_seam.py`, `test_auth.py`, `test_google_token_verifier.py`,
`test_hosted_readonly_posture.py`, `test_permission_resolver_seam.py`, and lorerunes'
`test_email_normalisation.py` / `test_posture.py` / `test_roster_parser.py`. **ZERO** reference any
packet-07 touched file or new symbol (`multi_statement_violations` / `_is_multi_statement_query` /
`GuardReport`) — grep filter returned nothing. The RED typecheck leg is the pre-existing owned bound
(repo CLAUDE.md: currency requires ADJUDICATION, not greenness), not a packet-07 regression. The
brief's "~102" is stale; real HEAD baseline is 191 (builder D4, independently confirmed).

## §4 — #118/#119 "already fixed" — verified
`git`: `8f24e11` is an **ancestor of HEAD**, `Mon Jul 13 2026`, subject *"the rollback verdict becomes
semantic … (#102, #118, #119)"*, touches `loremaster/loremaster/store/_txn.py` (+464 lines). Live suite
on 3.2.4:
```
$ uv run pytest tests/test_surreal_store.py -k "TestLiveEngineClassification or TestTxnRootCauseSelection" -v
11 passed, 167 deselected
```
Includes `TestLiveEngineClassification::test_a_real_assert_violation_is_classified_as_an_assert_violation`,
`::test_a_real_coercion_failure_is_classified_as_field_coercion`, `::test_the_unit_fixtures_still_match_the_live_engine`
and `TestTxnRootCauseSelection` (7, incl. cascade-skip + all-cascade degrade). These are live-engine
instruments that PASS only if the engine's real texts still match — so #118/#119 have no live defect
on 3.2.4, and the "resolve-no-builder" call is correct. No fabricated RED.

## §5 — Removed-behavior (F1 correction) — verified independently
`git grep` at HEAD for the `{"query", "query_raw"}` attr-set AST-ban shape across the whole test tree:
`test_floor_calibration_schema.py` is the **ONLY** file. The diff removes exactly 54 lines
(`class TestNoMultiStatementDdlRidesABareQuery` + `test_neither_module_calls_query_on_a_connection_directly`
with the `attr in {"query","query_raw"}` shape). Every surviving mention of the class name is a
comment/doc (the corrected re-derivation note, the DESIGN-sidecar, an archived report) — no live pin.

**The subsumption claim is real, verified myself** (not on the adversary's word): both
`floor_calibration/store.py` and `store/lease.py` `import surrealdb` AND `loremaster.store._txn`
(⇒ scanned by the `_talks_to_surrealdb` retry-escape lint), and their ONLY direct connection-receiver
SDK calls are `connection.signin(...)` / `connection.close()` — both in the SAFE set; everything else
routes through the seam. So the pre-existing retry-escape lint+guard already bans every unseamed SDK
call in both modules → deleting the one pin loses no route-through-seam coverage. The `not-self` →
`_is_connection_receiver` narrowing is the accepted repo-wide bound (zero current impact: no oddly-named
direct receivers). F1's "exactly ONE pin; the offline leg is NOT its subsumer; the retry-escape lint is"
matches my ground truth.

## §6 — #124 DDL-coverage pin — genuinely derived, not a hand-list
Read `test_ddl_write_target_coverage_124.py` in full: `_ddl_generators()` uses
`inspect.getmembers(surreal_schema, inspect.isfunction)` filtered to `generate_*_ddl` — deliberately
NOT `_enforced_relations_scaffold.ALL_DDL_GENERATORS` (the 9-entry hand-list missing lease+floor);
`_declared_tables()` parses `DEFINE TABLE` from generator output; `_table_constants()` reads
`vars(surreal_schema)`; and `_undeclared_constants()` is the ONE shared expression the invariant AND
its positive control both call (F3 fix — `if value not in declared` appears once). The reach pin
asserts `>= 11` generators incl. lease/floor. `5 passed` on the current tree. Both sides DERIVED
(reach a checked variable); the STATED BOUND (literal-table write uncovered) + re-open trigger are
present and honest.

## §7 — Documentation edits — accurate + house style
- **Store-ref `surrealdb-31-capabilities.md` §8** (+20 lines): a `[PROBED 2026-08-17, spike-surreal
  3.2.4]` bullet — the QUERY-TOO-COMPLEX recursion-depth branch is LIVE on 3.2.4 but ONLY for the
  fulltext `@@`/RRF shape (~120 clauses), NOT simple-operator chains (probed to 40000). Same
  provenance-label format as neighbouring §8 entries; cites the committed
  `scripts/probe_query_complexity_07.py` (negative-space receipt) + the standard-gate live instrument
  `test_bypassing_both_clamps_still_raises_a_classified_store_error` as both proof and drift alarm.
  Accurate and consistent with the file's version-provenance-honesty rule.
- **Provenance comments** (`test_surreal_store.py:1355`, `test_memory_backend.py:2048`): comment-only,
  honest — add the missing `3.1.5` capture label, note the 3.2.4 re-confirmation via the sibling bypass
  test, and DISCLOSE that the 3.2.4 raw text was not re-captured (only reachable via the full RRF
  query). Item-4 live suite still green: `4 passed`.
- **DESIGN-sidecar `5 pins` fix**: self-contained corrections header (lines 8-33) + in-body `⚠ CORRECTED`
  markers in §5.2/§RECOMMENDATION; every "5 scattered"/"five pins" occurrence is inside a correction
  context; the corrected count "exactly ONE" matches my independent git-grep (§5). Landed and accurate.

## §8 — Corpse sweep + diff-first pass
- **Corpse sweep CLEAN** (bare-anchor greps over touched files): no fictional `"fulfil the following
  assertion"`; no `_ASSERT_VIOLATION_MARKER = "assert"` resurrection; no live pin asserting the retired
  `[0]`/`[-1]` positional selection as if still buggy. Every "5 pins" hit is a correction note.
- **Diff-first pass**: `test_retry_seam.py` is a **pure append** (single hunk `@@ -9422,3 +9422,591 @@`)
  — nothing above line 9422 touched (so the "five pins" at `:3937` is pre-existing and unrelated: an
  ack-path double, not the #144 fabrication). Read the full 591-line append: clean, discriminating
  pins with proper positive/negative controls, accurate corrected comment blocks, a documented KNOWN
  BOUND + re-open trigger. **No stray debug code, no commented-out blocks, no TODOs.** The two new
  probe scripts (`scripts/probe_*_07.py`) target ONLY `ws://127.0.0.1:18000` (TEST store) with explicit
  "NEVER :18500 (production)" headers.

## §9 — Outstanding EXIT items (lead tasks; NOT build defects)
These are correctly deferred to the lead per the contract (they are finding/docs tasks, not test pins)
and do NOT block the build GO:
1. **Finding #124's row** still reads *"SurrealDB 3.1.5 SILENTLY LOSES concurrent first-writes…"*
   (state `acknowledged`). The packet EXIT owes the mechanism amendment (the `query()` statement[0]-only
   gap hid retryable conflicts — the misdiagnosis was already read FIRST against the surviving
   `scratchpad/102-recovery/` harness per contract-author §3) and carry-forward of the deferred
   coverage-pin note (design sidecar §4 gives the exact wording). Store-reference §5 account is already
   correct; the finding ROW is not.
2. **Findings #118/#119/#144** resolution-with-notes (packet EXIT ritual). Verified their code state is
   correct; the ledger transitions are the lead's.
3. **Deploy**: since the only production-runtime fix (#118/#119) is already at HEAD (`8f24e11`, ancestor),
   the uncommitted tree adds NO new production code — the deploy ships already-committed classification
   code + the doc. Flagging so the lead knows the "DEPLOY: yes" is not gated on new production logic.

## Scratch cleanup
`/tmp/coldaudit07-scratch-a` — a `scratch_copy.sh` copy (provenance asserted) carrying my inline-clone
attack in `tests/_sdk_guard.py`. Disposable by design; safe to `rm -rf`. No repo file was mutated.

## Bottom line
The packet-07 build is correct and green. I re-established each load-bearing claim myself — the
regression count, the ruff/mypy state, the #118/#119 already-fixed provenance, the removed-behavior
subsumption, the #124 derivation, and — most importantly — the F0 sharing guarantee, by BUILDING the
clone the pin exists to catch and watching it redden. The only open items are lead EXIT tasks (finding
amendments + resolutions), which the contract correctly leaves to the lead.

**GO.**
