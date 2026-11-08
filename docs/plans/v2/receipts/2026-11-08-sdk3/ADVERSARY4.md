brief-base v25 read · brief project v7 read

# ADVERSARY4 — contract-adversary round 4 (adversary-sdk3-r4), packet 66 (SDK3), graded 2026-11-08

## SUMMARY BLOCK
- **State:** done.
- **VERDICT: CONTRACT INSUFFICIENT.** Every finding is in the NEW F6 gate contract (`scripts/test_pending_contract_gate_f6.py`). The retry, index and record-id side of round 8 (MP-1, embed sibling, B-2 letter legs, F-b domain legs, LM1 narrowing, scout attribution, the fold) held against every wrong build I made.
- **UNSATISFIABLE pins: NONE.** My reference control: 805 passed, EXIT=0 over round 8's changed retry/index/record-id files plus F6. The F6 control: 113/113. Both run on `adv4/b1` = `sdk3r8/ref` plus the committed prose.
- **REFERENCE BUG (top finding): the reference F6 calls every listed id outside a scoped run "NOT COLLECTED — renamed or deleted"** (MP-F6-4).
  - `wave_gate.py --wave` passes its scoped run into the same `_currencies_for`, and "a scoped RED_ORPHANED still fails".
  - So once the 302-id entry registers at build step 0, every scoped wave gate in the fleet that omits any of the 27 files fails, the builder's own included.
  - §R3.7(c)(4) supports two readings. A scope-aware variant passes 479/479, so reading (b) is satisfiable. **This needs a ruling and one pin BEFORE build step 0.**
- **P1 headline:** 4 wrong F6 gates survive all 12 F6 pins. Each is PROOF HELD: exactly my probe went red and the 12 F6 pins stayed green.
  - The gates: self-destruct only in files with a red; self-destruct only when the run has any red; hierarchical id matching; a mixed-claim file read file-level.
  - A 5th wrong gate (mixed-claim typecheck exemption) survives in the real registry's shape, with an unsymboled-code claim.
  - Every other build died: 7 of 7 round-3 replays behaved as predicted, and 9 new retry/index/record-id builds.
- **Replays (7):**
  - `b3_no_bound_batch`: KILLED, by exactly MP-1 `[batch]`.
  - `b2_idsample_slice` and `b2_owner_slice`: KILLED, each by its OWN B-2 leg exactly. No longer incidental.
  - `lm1_handloop` (under the staged narrowing): KILLED, 26 = 26 declared.
  - `lm7_private_loop_capped`, `a3_floor16`, `streaming_false`: SURVIVE as in round 3 (NO ROUND).
  - Scout hand-loop sibling: KILLED, exactly the 2 ladder pins.
- **Runs used: 35 pytest runs, all scoped; 0 full-contract-set runs.** 14 builds went through 2 haiku-runner queues; 21 short runs were inline (seconds each). Per-run list in §RECEIPTS.
- **F6 entry** (`sdk3r8/item5/packet66_entry.yaml`):
  - 302 ids in 27 files. 302/302 appear in `pytest --collect-only -q` at HEAD, and all are red in round 8's HEAD junit.
  - Path-prefix mismatches 0; non-ASCII 0; backslashes 0; line-number ids 0.
  - The single-quote builder note is CONFIRMED by a probe.
- **Packages considered:**
  - Junit → node id: stdlib ElementTree, plus the inverse of `_pytest.junitxml.mangle_test_address` (I read the installed source, pytest 9.0.3; the reference's inverse is exact). `pytest-reportlog` would carry `nodeid` natively but is not installed. Verdict: **keep_with_trigger**. Trigger: the operator-ruled `pytest_junit` reader changes, or an id fails to invert.
  - Caller attribution: stdlib `sys._getframe`, bespoke-trivial.
  - Retry: tenacity 9.1.4 `AsyncRetrying` (replace, as the contract demands).
  - YAML: PyYAML 6.0.3 single-quoted vs double-quoted (probed).
- **Odoo-20 portability:** n/a, no Odoo seam touched.
- **Reuse ledger:** none. I wrote no production symbols. My probes are scratch-only and pasted in §INSTRUMENTS.
- **Graded:** `b4e5c77` (contract tests; reference TREE 684c19c4…, my copies TREE 47d51489…) · HEAD-at-report: `0836479` · DIFFERENT (1 behind; docs only: R30 + RULING-8).
- **Decisions needed:**
  - (1) MP-F6-4: rule on the scope reading before build step 0 (sidecar or lead).
  - (2) Lead: route MP-F6-1..3. The contract rounds are spent (R25), so I recommend handing §INSTRUMENTS' probe file to the R23 servicing author, to land beside F6 at build step 0. Otherwise they are named residuals for the builder brief and cold audit (R16).
- **Pointers:** §MISSING PINS · §REPLAY · §NEW BUILDS · §P1b · §P1c · §LANDMINES · §RESIDUALS · §INSTRUMENTS · §RECEIPTS.
- **Capability check:** everything the brief asked for was available.
  - lore was used for the index check and the prior-art search. `lore_index(reconcile=True)` was not needed, since I made no repo edits.
  - Grep was used for the corpse sweep (rename exhaustiveness, dogfood case (a)) and for the cross-cutting apply-site map (case (c)).
  - The haiku-runners ran my queue scripts through their wrapper, and their RAN: lines match. I also verified every log's provenance, TREE, EXIT and count lines myself.

## MISSING PINS (all in the F6 gate contract; none UNSATISFIABLE)
Why these pass the one-question test: F6 is BUILD STEP 0's deliverable (R27-4). Its whole job is to never read an unowned red as owned (#306). The fleet's agents act on its verdict without checking. A false RED_ADJUDICATED is therefore a false clear on a served gate verdict (R17), not hygiene in the contract's own checker. **That classification is for the lead to confirm.** If it is ruled a "checker gap", MP-F6-1..3 become residuals, and MP-F6-4 still needs its ruling.

| id | surviving build + receipt | the pin that kills it (pasted, §INSTRUMENTS) | defect it catches | triage / route |
|---|---|---|---|---|
| **MP-F6-4** (reference bug) | **The reference F6 itself.** `pytest_self_destruct_findings` flags a listed id as stale when `node_id not in run.collected`. With a scoped run, `test_probe_a_scoped_run_that_never_collected_the_file_is_not_stale` goes RED on the reference (`f6_ref_full_control.log`: 1 failed / 478 passed). The scope-aware variant (skip entries whose file the run never collected) passes **479/479**, including gated_ground and wave_gate (`f6_scope_aware_control.log`). | the scope probe | Once the 302 entry registers, every `wave_gate.py --wave` that omits any of the 27 files reads RED_ORPHANED, with up to 302 false "renamed or deleted" lines. That fails every scoped wave gate fleet-wide until packet 66 lands. A gate that refuses honest runs gets switched off. | **NEW PROPERTY** (§R3.7(c)(4) never says "in a run that collected the file"; its parenthetical "(renamed/deleted)" favours reading (b)). **Close before build step 0:** one ruling, one pin. Readings: (a) not collected anywhere in the run (reference); (b) not collected although its file was. I would pick (b): a deleted FILE is still caught by the typecheck leg's file-exists self-destruct, which runs full in wave mode. |
| **MP-F6-1** | `f6_destruct_only_failing_files`: self-destruct and stale are checked only for entries whose file has a red in this run. `f6_destruct_only_when_red`: they are checked only when the run has any red. Each is PROOF HELD: exactly the 2 all-green probes red, 12/12 F6 green (`wb_f6_destruct_only_*.log`). | `test_probe_an_all_green_run_self_destructs_every_listed_node`, `test_probe_an_all_green_run_still_reports_a_stale_id` | At the packet-66 build commit, every listed id goes green at once, which is exactly the moment (3) exists for. A file-gated gate stays GREEN, so 302 stale entries survive, and a later regression on any of those nodes reads RED_ADJUDICATED. Under P1c(2) this is the empty-population BLOCKER: with the failing set emptied, the comparison reads success. | **PINNED PROPERTY, NEW CASE.** Chokepoint: `pytest_self_destruct_findings` iterates the REGISTRY, never the run's outcomes. Can travel as a named residual. |
| **MP-F6-3** | `f6_mixed_file_level`: a file entry that also carries a mypy claim is adjudicated file-level. `f6_mixed_no_typecheck_destruct`: any entry with `red_nodeids` is skipped by the typecheck self-destruct. Each is PROOF HELD, 12/12 F6 green. **This is the planned registry's real shape:** `registry_with_entry.yaml` carries `test_sdk3_refused_file_reason.py` as ONE entry with `unsymboled_codes: attr-defined ×1` AND 4 `red_nodeids`. | `test_probe_a_mixed_claim_file_is_adjudicated_per_node`, `test_probe_a_mixed_claim_file_still_self_destructs_its_mypy_claim` (claim=code) | First build: any NEW red in the MP-1 file is owned file-level, a false clear on the MP-1 pins' own file. Second build: once SDK 3 lands, the attr-defined allowance (count 1, 0 observed) never self-destructs, so a later unsymboled attr-defined error in that file reads owned. | **PINNED PROPERTY, NEW CASE.** Chokepoints: `partition_pytest` keys per-node on `red_nodeids` alone; the typecheck self-destruct keys on `claims_mypy` alone. Can travel. |
| **MP-F6-2** | `f6_hierarchical_ids`: pytest-CLI-style matching, where a listed id adjudicates itself and its `::` children and is "collected" if any child is. PROOF HELD, 12/12 F6 green. The `[`-prefix pin cannot see it. | `test_probe_a_listed_CLASS_id_admits_no_member`, `test_probe_a_listed_FILE_path_admits_no_red` | A class id or a bare path in `red_nodeids` silently owns every red under it. That is the file-only matching the claim refusal exists to forbid, re-entered through the new key. | **PINNED PROPERTY, NEW CASE** ((5) "never by prefix" is pinned for `[` and not for `::`). Chokepoint: exact set membership in both the partition and the stale test. R30's path-prefix validator does not catch leafness. Can travel. |

**CLASS (MP-F6-1..4), one property:** *the pytest leg's adjudication of a listed id depends only on (that exact id) × (did the run collect its file) × (did it fail). It never depends on the other outcomes in the run, the other claims on the entry, or the id's ancestors.*
- **SIBLINGS TRIED:** all-green run; file-gated; run-gated; `[` prefix (pinned); `::` class prefix; bare path; mixed symbol claim (killed by liveness "now RESOLVES"); mixed code claim; scoped run; skipped listed node (residual R4-1).
- **SIBLINGS NOT TRIED:** an `<error>` (setup error) on a listed node with `<failure>` absent (the reference treats error as red, which reads correct); the same path in two bounds (residual R4-2); `xfail` and `xpass` of a listed id.

## REPLAY (round-3 survivors and missing-pin builds → round-8 contract, on `adv4/b1`)
Anchors match exactly once. The 5 touched production files are byte-identical to round 3's base, so the diffs apply verbatim. Expected sets were declared before each run. The lm1 set is round 3's measured 26 against the proposed instrument.

| build | scope | result | verdict |
|---|---|---|---|
| `b3_no_bound_batch` (MP-1) | MP-1 file + B3 | PROOF HELD: exactly `…names_the_row_cap[batch]` (1F/4P) | **KILLED, MP-1 closed** |
| `b2_idsample_slice` | B-2 class only | PROOF HELD: exactly `test_the_id_sample_serves_each_ids_bare_key` (1F/1P) | **KILLED by its own B-2 leg** (no longer incidental) |
| `b2_owner_slice` | B-2 class only | PROOF HELD: exactly `test_the_owner_names_serve_each_principals_bare_key` (1F/1P) | **KILLED by its own B-2 leg** |
| `lm1_handloop` (under the staged narrowing) | 6 files (738) | PROOF HELD 26 = 26: 19 sharing pins, both 16-way live families, window, A3, decorrelation, A1, A4 txn (26F/712P) | **KILLED** |
| `lm7_private_loop_capped` | row_bound + store -k upsert… | 20 passed (EXIT 4, declared pin green) | SURVIVES, NO ROUND (as round 3; builder note R1/R27-2a) |
| `a3_floor16` | 5 retry files | 737 passed | SURVIVES, NO ROUND (as round 3, R3) |
| `streaming_false` | CF4 | 1 passed | SURVIVES, NO ROUND (as round 3, R4; masked by drop-on-timeout) |

NOT TRIED this round: `x18_double` (not in the brief's replay list; round 3: NO ROUND).

## NEW BUILDS (round 4)
| build | landmine | mutation | result | verdict |
|---|---|---|---|---|
| `n_lm1_scout_handloop` | 3 (scout sibling) | scout's `AsyncRetrying` ladder → a hand `while` loop, factory wait called on a `SimpleNamespace(attempt_number)`, `await self._sleep(...)` from scout | PROOF HELD: exactly the 2 ladder pins (2F/66P) | **KILLED by the caller attribution.** GREEN on the native reference: the 805 control and the r8 loop's 20×, which ran the whole native_retry file with the patch |
| `n_lm1_double_retry` | 3 | keeps `AsyncRetrying`, wraps it in an OUTER loop: on `TxnContentionExhaustedError`, sleep(0) from `_txn` and run tenacity again | 140F/598P: ceiling and floor ×16 seams, exhaustion record ×16, typed error ×16, bootstrap ×16, url ×16, exactly-once log ×16, retry_policy ×2… | **KILLED by behaviour.** The narrowing does not see it (a `_txn` sleep is filtered, not flagged; residual R4-5) |
| `n_mp1_shared_wrong_number` | 2 | ONE shared sink (`_mark_file_failed`) rewrites the store reason to name `TXN_ROW_HARD_CAP` (the configured constant, not the exception's) | MP-1 `[batch]` + `[realtime]` red. **B3 stays green**: B3 shrinks the real cap, so a constant-based reason coincides | **KILLED by MP-1** (its faked 1009 discriminates; residual R4-7) |
| `n_fb_domain_unknown_single` | 5 | single-statement domain rejection → `SurrealOutcomeUnknownError` | PROOF HELD: exactly the single-statement domain leg | **KILLED** (confirms r8 `fb_domain`) |
| `r_fb_txn_domain_unknown` (round-3 build, replayed) | 5 | transaction domain rejection → unknown | PROOF HELD: exactly the NEW transaction domain leg | **KILLED by the new leg itself** (round 3 needed the T-family) |
| `n_fb_domain_wrong_class_fbonly` / `_broad` | 5 | single-statement domain rejection → definite `SurrealConnectionError` (wrong class) | F-b class 4/4 green; broad: `test_a_single_statement_throw_is_not_retried` red | F-b legs blind to class; **KILLED elsewhere** (residual R4-6) |
| `n_fb_txn_domain_wrong_class` | 5 | transaction domain rejection → definite `SurrealConnectionError` | F-b class green; 7 T-family reds (`TestADomainRefusalIsNotRetriedAndItsRootCauseSurfaces` ×7) | **KILLED elsewhere** |
| `f6_destruct_only_failing_files`, `f6_destruct_only_when_red`, `f6_hierarchical_ids`, `f6_mixed_file_level`, `f6_mixed_no_typecheck_destruct` | 1 | see §MISSING PINS | 12/12 F6 green each; exactly my probe(s) red | **SURVIVE → MP-F6-1..3** |
| reference F6 (scoped run) | 1 | (none; the reference as built) | scope probe red; scope-aware variant 479/479 | **MP-F6-4** |

## LANDMINES — per-item verdicts
1. **F6 (REACH, P1c):**
   - *Prefix of a parametrised id read as adjudicated?* No for `[` (pinned). YES for `::` and for the bare path (MP-F6-2).
   - *Self-destruct and stale missed?* YES, in an all-green run or a red-free file (MP-F6-1).
   - *An entry with neither symbols nor ids?* Refused: the `red_nodeids: []` pin plus the "neither" message match. A key-presence build is killed by that pin, by inspection.
   - *Filled entry:* clean (see summary).
   - *FORK-R8-1:* ruled per-file (R30). The contract as written assumes per-file, which is consistent. The R30 rider (path-prefix validator) is not in the contract; my check shows 0 mismatches in the entry.
   - *NEW:* the scope over-fire (MP-F6-4).
2. **MP-1 + embed:**
   - Distinct-arm premise HOLDS. The reference arms are `_index_chunks` (realtime) and `_commit_batch_file` (batch), and per-arm builds redden exactly their own legs (round 8 measured both arms; I replayed batch).
   - Wrong number through a shared helper: KILLED by MP-1 (not by B3).
   - Static-snapshot residual verdict is **RIGHT** (MEDIUM-HIGH, inspection):
     - `_index_static_tier` → `_walk_and_index` reaches the same per-file arms.
     - The only other `apply` sites are `resolve_edges` (serves `scopes_failed`), the tier purge, and the reconcile/watcher `file_purge_fragments` purges. None of them serves a per-file reason.
3. **LM1 narrowing:**
   - **Threat model honest:** it states the honest-developer target, the `_portable_async_sleep` non-goal, and the reach as tenacity's default sleep.
   - **Hint teaches "port it, never widen":** yes, verbatim in the patch.
   - **Scout attribution:** RED on a scout hand loop (2 = 2) and GREEN native.
   - **Double retry:** passes the instrument, but 140 behaviour pins kill it.
   - Post-patch prose drift in the module docstring (residual R4-3).
4. **B-2 letter legs:** both slicing builds now die on their own B-2 leg, exactly (PROOF HELD). R26-3's rider is met.
5. **F-b domain legs:**
   - domain → unknown is KILLED on both seams by the new legs themselves.
   - domain → definite-but-wrong-class is NOT seen by the F-b legs (they assert only "not unknown"). It is KILLED by the T-family: 1 pin on the single-statement seam, 7 on the transaction seam.
6. **Fold:**
   - Both former copies `setattr(loresigil.backoff, "full_jitter", …)`, which is the same module object and the same attribute as `mutate_the_wait_factory`, so no site is lost.
   - Empirical: `lm1_handloop` reddens all 16 per-seam sharing pins, the mint, the positive control and the scout claim through the folded helper.
   - `_FactoryMutation` has 0 remaining references.
7. **Q7 raising leg:** "errors ⇒ shared" is UNSOUND as a per-site proof. It proves only that the shared helper is reached on the file's path.
   - Measured from `sdk3r8/mut/q7raise_raised.log`: all 49 of `test_fixwave_a19a_63c_i_a.py`'s raise reds trace through `test_fixwave_a19_63c_i_a.py:135`, a SIBLING file's fixture. a19a's own call sites (`:712`, `:1444`) never execute under the raise.
   - A private parser later in a test is never reached once the fixture raises, so it could not be seen.
   - By inspection, none of the 5 files holds a private id parser. Their remaining `partition`/`rpartition` calls are on fence and SQL text.
   - → residual R4-4, NO ROUND.
8. **Satisfiability spot-check:**
   - My reference control: 805/805 over refused_file_reason, record_ids, outcome_reach, native_retry, backoff_seam, retry_seam, index_batching and F6.
   - The F6 suites: 113/113 and 478+1 (that one red is the reference-bug probe).
   - **No UNSATISFIABLE pin. One REFERENCE BUG** (MP-F6-4: the reference over-fires on a path no contract pin drives).
9. **Concurrency:** round 8's loop is VALID: 20/20 EXIT=0, 33 passed each, all TREE=684c19c4…, run with the staged narrowing. Not re-run.

## P1b — QUANTIFIER TABLE
| # | invariant | class | receipt |
|---|---|---|---|
| 1 | a row-cap refusal is served naming its cap | ∀ sweep shapes | `b3_no_bound_batch` killed `[batch]`; `n_mp1_shared_wrong_number` killed both |
| 2 | an embed failure is served `embed_failed_or_non_finite` | ∀ sweep shapes | round 8 `embed_*` PROOF HELD per arm (not re-run; logs `sdk3r8/mut/m8_embed_*.log`) |
| 3 | migration refusal renderers serve the bare key | ∀ {digit-led, non-word, letter-led} | `b2_*` killed by own legs |
| 4 | an answered error is definite | ∀ {NotAllowed, domain} × {single, txn} for "not unknown"; **guarded on class** | unknown builds ×2 killed by own legs; wrong-class door builds ×2 → killed by T-family (pins named) |
| 5 | F6 (3)(4): a listed id that passes, or is not collected, fails the gate | **GUARDED by "its file has another red in this run"** | `f6_destruct_only_*` SURVIVE → MP-F6-1 |
| 6 | F6 (5): a listed id admits only itself | **GUARDED by "the prefix is a `[` prefix"** | `f6_hierarchical_ids` SURVIVES → MP-F6-2 |
| 7 | F6: per-node partition for node-listed files | **GUARDED by "the entry carries no mypy claim"** | `f6_mixed_file_level` SURVIVES → MP-F6-3 |
| 8 | F6: no typecheck self-destruct for a pytest-only file | **GUARDED by "no mypy claim"** (a mixed entry is not tested) | `f6_mixed_no_typecheck_destruct` SURVIVES with claim=code; killed with claim=symbol (liveness) |
| 9 | F6 (4) stale | **implicitly "∀ runs", over-reaching**: fires on scope | reference RED on the scope probe → MP-F6-4 |
| 10 | conflict-driver sleeps go through tenacity (LM1) | ∀ sleeps via tenacity's default sleep; an added non-tenacity sleep is filtered, not flagged | door `n_lm1_double_retry` → killed by 140 behaviour pins |
| 11 | scout's ladder sleeps through tenacity | ∀ ladder sleeps (injected-sleep caller) | `n_lm1_scout_handloop` killed 2 = 2 |
| 12 | one wait factory reaches every in-66 site | ∀ 16 seams + mint + control + scout | `lm1_handloop` replay: 19 sharing reds via the folded helper |

## P1c — ENFORCEMENT TABLE (empirical unless marked)
| rule | chokepoint | effect vs proxy | sharing by mutation | spelling test? |
|---|---|---|---|---|
| F6 listed → adjudicated / unlisted → orphaned | `PendingContractGate.partition_pytest` (one) | EFFECT (GateCurrency verdict) | n/a (one site) | no |
| F6 self-destruct and stale | `pytest_self_destruct_findings` (one) | effect, but **empty-population leg FAILS**: with the failing set emptied (all-green run), W1/W2 read success → MP-F6-1 | n/a | no |
| F6 claim refusal | `PendingContractRegistry` validator (one) | effect (RegistryError "neither") | n/a | no |
| MP-1 reason naming the cap | **two** cloned arms today; the builder note names ONE helper | effect (served meta) | to be proven at audit (break the helper ⇒ both legs red); `n_mp1_shared_wrong_number` shows the shared-sink form is seen | no |
| LM1: the loop is tenacity's | `_driver_sleeps` attribution plus scout's `_RecordingSleep` | **proxy** (who called sleep; R29 ruled it an instrument, not a scanner) | — | runtime attribution, R29-adjudicated; not a source scan |
| one wait factory | `loresigil.backoff.full_jitter` | effect (slept values) | **PROVEN** in this run: `lm1_handloop` reddens all 19 sharing pins plus A4 | no |
| F-b definiteness | `_raise_attempt_failure` / `_run_verified_transaction` | effect (raised class) | n/a | no |

Legs run empirically: every F6 row; MP-1 (wrong number); LM1 (hand loop ×2, double retry); factory sharing; F-b. By inspection only: the claim refusal (pinned and red at HEAD by round 8's receipt).

## P-PRIOR
- `_driver_sleeps.mutate_the_wait_factory` / `WaitFactoryMutation`: this IS the owner (it folds 2 copies). `_FactoryMutation` has 0 remaining references.
- `test_sdk3_refused_file_reason._refuse_one_commit_at_the_row_cap`: no existing one-shot refusal injector. Searched `lore_search("test helper that makes store.apply raise TxnRowCapExceededError once…")` (only itself) and grepped `_surreal_fakes.py`, `test_indexer_bulk_sweep.py` and `test_sdk3_index_batching.py` (B3 uses the real compose with a shrunk cap). Hand-roll justified.
- `test_pending_contract_gate_f6._testcase` / `_junit`: a near-twin of `test_pending_contract_gate._junit`, which hard-codes `classname="c"`. Extend candidate (round 8 flagged it). Residual R4-9.
- The reference's `junit_node_id` (the builder writes F6's): prior art is pytest's `mangle_test_address` (the forward direction only; pytest ships no inverse). Hand-roll justified.

## P-PKG (my table built before reading round 8's; then DIFFED)
| mechanism | library | what I READ | verdict |
|---|---|---|---|
| junit testcase → pytest node id | stdlib ElementTree + inverse of `_pytest.junitxml.mangle_test_address`; alt. `pytest-reportlog` | installed `mangle_test_address` source (pytest 9.0.3, printed in-session); `uv pip list` (reportlog absent) | keep_with_trigger (ruled `pytest_junit` reader; trigger: a reader change, or an id the inverse cannot render) |
| registry YAML quoting | PyYAML 6.0.3 | probe `adv4/probes/yaml_quote_probe.py`: `"x[—]"` → `x[—]`; `'x[—]'` → `x[\\u2014]` | builder note CORRECT |
| retry loop / ladder | tenacity 9.1.4 `AsyncRetrying` | reference `_txn.retry_on_conflict` and `scout.run` read | replace (the contract's demand) |
| caller attribution | stdlib `sys._getframe` | patch read | bespoke-trivial |

**Diff vs round 8's table:** round 8 surveyed only PyYAML and tenacity. The junit → node-id derivation, a mechanism the F6 contract SPECIFIES ("derived as `<file>::<classes after the module>::<name>`"), has no package row. It is not a defect, because the inverse is exact, but it is a missing row.

## P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (lore repo). My seam count is 0, the same as the author's.

## RESIDUALS (each NO ROUND unless marked)
- **R4-1:** the reference F6 tells a SKIPPED listed node "is green — delete it with the fix". That is false prose; §R3.7(c)(3) says PASSES. It fails loudly, but an agent acting on the text would delete a still-unfixed entry. Cheap: treat a skip as neither red nor green. Probe: `test_probe_RECORD_a_skipped_listed_node`.
- **R4-2:** the reference reads a path file-level if ANY entry for it lacks `red_nodeids`. A future symbol-only entry by another bound on a node-listed file re-opens file-level matching. 0 such overlaps today (27/27 single-bound). Re-open trigger: the first node-listed file registered under a second bound.
- **R4-3:** `_driver_sleeps` module docstring after the patch still says a driver sleeping outside the set gets "a false red on an unusual build… the fix is one line". That one line is widening, which contradicts R29's rewritten hint. It also cites a scratchpad path (`scratchpad/sdk3r7/probes/sleep_caller.py`). Fix it in the servicing patch.
- **R4-4:** the Q7 raising leg proves reachability, not per-site sharing (§LANDMINES 7). By inspection there is no private parser in the 5 files.
- **R4-5:** the LM1 instrument filters, rather than flags, a non-tenacity sleep beside tenacity's. Behaviour pins carry the double-retry case (140 reds).
- **R4-6:** the F-b legs assert "not unknown" only. The T-family carries the class (1 + 7 pins).
- **R4-7:** B3 cannot see a constant-sourced cap, because it shrinks the real cap. MP-1 can. Keep both.
- **R4-8:** the reference test tree differs from the committed contract by 2 prose-only lines.
- **R4-9:** the F6 `_junit` near-twin (above).
- **R4-10:** `lm7_private_loop_capped`, `a3_floor16` and `streaming_false` still survive (round-3 R1/R3/R4; builder notes).
- **R4-11:** round 8's B-2 backtick leg cannot fire on SDK 3.0.0 (their R14).

## LOOP COST
- Adversary round 4 of 5 (R25). 35 scoped pytest runs, 0 full. 2 haiku-runner queues (14 builds); 21 inline runs of seconds each.
- Per R16, after round 5 the open pins travel as named residuals.
- MP-F6-4 is the one item that should not travel unruled, because it changes fleet-wide wave-gate behaviour at build step 0.

## INSTRUMENTS (verbatim; also in `adv4/probes/`, specs in `adv4/wb/<name>/{target,anchor,repl,tests,expect}`, wrapper `adv4/runwb.sh`)
`adv4/probes/test_adv4_f6_probe.py` (copied into a tree's `scripts/` to run):
```python
"""adversary-sdk3-r4 F6 probes (scratch only; copied into a scratch tree's scripts/ to run).

Each probe states a §R3.7(c) semantic over a registry/junit SHAPE the 12 contract pins never build:
an all-green run (the moment the build lands), a non-leaf (class / file) id, and a file whose entry
carries BOTH a mypy claim and red_nodeids (the MP-1 file in the real packet-66 entry is exactly this).
Each must PASS on the reference F6 (P0 control) and go RED on the matching wrong gate build.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pending_contract_gate import (  # noqa: E402
    JUnitReportReader,
    MypyOutputReader,
    PendingContractGate,
    PendingContractRegistry,
)
from test_pending_contract_gate import _mypy_output  # noqa: E402
from test_pending_contract_gate_f6 import (  # noqa: E402
    _BOUND_ID,
    _LISTED_CLASS_NODE,
    _LISTED_PARAM_NODE,
    _NODE_FILE,
    _SIBLING_PARAM_NODE,
    _UNLISTED_NODE,
    _currency,
    _gate,
    _junit,
    _pytest_currency,
)

_ALL_GREEN = [(_LISTED_CLASS_NODE, False), (_LISTED_PARAM_NODE, False), (_SIBLING_PARAM_NODE, False)]


def _mixed_gate(tmp_path: Path, node_ids: list[str], *, claim: str = "symbol") -> PendingContractGate:
    """One file entry carrying a mypy claim AND red_nodeids. ``claim="code"`` is the MP-1 file's real shape
    (an unsymboled attr-defined allowance, count 1); ``claim="symbol"`` a missing-symbol claim."""
    listed = "\n".join(f"          - '{node_id}'" for node_id in node_ids)
    mypy_claim = (
        "        missing_symbols:\n          - loremaster.store._txn.TxnRowCapExceededError\n"
        if claim == "symbol"
        else "        unsymboled_codes:\n          - code: attr-defined\n            count: 1\n"
        "            reason: the SDK-3-only class read through the module alias\n"
    )
    text = (
        "version: 1\nbounds:\n"
        f"  - id: {_BOUND_ID}\n"
        '    owner: "the SDK3 builder (packet 66)"\n'
        '    reopen_trigger: "the build"\n'
        '    ruling: "R30"\n'
        '    rationale: "mixed"\n'
        "    files:\n"
        f"      - path: {_NODE_FILE}\n"
        + mypy_claim
        + "        red_nodeids:\n"
        f"{listed}\n"
    )
    registry_path = tmp_path / "pending_contracts.yaml"
    registry_path.write_text(text)
    tree = tmp_path / "tree"
    (tree / _NODE_FILE).parent.mkdir(parents=True, exist_ok=True)
    (tree / _NODE_FILE).write_text("# registered\n")
    return PendingContractGate(registry=PendingContractRegistry.load(registry_path), repo_root=tree)


# --- all-green run: the build landed and fixed every listed red -------------------------------------


def test_probe_an_all_green_run_self_destructs_every_listed_node(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(tmp_path, gate, _ALL_GREEN)
    assert not currency.ok, (currency.verdict, currency.orphans)
    for node in (_LISTED_CLASS_NODE, _LISTED_PARAM_NODE):
        assert any(node in o and "green" in o.lower() for o in currency.orphans), currency.orphans


def test_probe_an_all_green_run_still_reports_a_stale_id(tmp_path: Path) -> None:
    renamed = f"{_NODE_FILE}::TestAContractAheadPin::test_renamed_away"
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, renamed])
    currency = _pytest_currency(tmp_path, gate, [(_LISTED_CLASS_NODE, True), (_SIBLING_PARAM_NODE, False)])
    # the file still has one red, the stale id must fire; now the run where the FILE has no red at all:
    (tmp_path / "b").mkdir()
    gate2 = _gate(tmp_path / "b", [renamed])
    currency2 = _pytest_currency(tmp_path / "b", gate2, _ALL_GREEN)
    assert not currency.ok and not currency2.ok, (currency.orphans, currency2.orphans)
    assert any("test_renamed_away" in o for o in currency2.orphans), currency2.orphans


# --- non-leaf ids: a class id or the bare file path admits NOTHING and is itself stale ---------------


def test_probe_a_listed_CLASS_id_admits_no_member(tmp_path: Path) -> None:
    class_id = f"{_NODE_FILE}::TestAContractAheadPin"
    gate = _gate(tmp_path, [class_id, _LISTED_PARAM_NODE])
    currency = _pytest_currency(
        tmp_path, gate, [(_LISTED_CLASS_NODE, True), (_UNLISTED_NODE, True), (_LISTED_PARAM_NODE, True)]
    )
    assert not currency.ok
    assert any("test_a_new_regression" in o for o in currency.orphans), currency.orphans


def test_probe_a_listed_FILE_path_admits_no_red(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_NODE_FILE, _LISTED_PARAM_NODE])
    currency = _pytest_currency(tmp_path, gate, [(_UNLISTED_NODE, True), (_LISTED_PARAM_NODE, True)])
    assert not currency.ok
    assert any("test_a_new_regression" in o for o in currency.orphans), currency.orphans


# --- a file entry carrying a mypy claim AND red_nodeids ----------------------------------------------


def test_probe_a_mixed_claim_file_is_adjudicated_per_node(tmp_path: Path) -> None:
    gate = _mixed_gate(tmp_path, [_LISTED_CLASS_NODE])
    currency = _pytest_currency(tmp_path, gate, [(_LISTED_CLASS_NODE, True), (_UNLISTED_NODE, True)])
    assert currency.verdict == "RED_ORPHANED", (currency.verdict, currency.orphans)
    assert any("test_a_new_regression" in o for o in currency.orphans), currency.orphans


def test_probe_a_mixed_claim_file_still_self_destructs_its_mypy_claim(tmp_path: Path) -> None:
    gate = _mixed_gate(tmp_path, [_LISTED_CLASS_NODE], claim="code")
    currency = _currency(tmp_path, gate, "typecheck", MypyOutputReader.read(_mypy_output([])))
    assert not currency.ok, (currency.verdict, currency.orphans)


# --- residual probe (no assertion on the spec; it records what the reference does) -------------------


def test_probe_RECORD_a_skipped_listed_node(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    xml = _junit([(_LISTED_CLASS_NODE, True), (_SIBLING_PARAM_NODE, False)]).replace(
        "</testsuite>",
        f'<testcase classname="loremaster.tests.test_f6_contract_ahead" name="test_a_parametrised_pin[digit-led]" '
        f'file="{_NODE_FILE}"><skipped message="store unreachable"/></testcase></testsuite>',
    )
    currency = _currency(tmp_path, gate, "pytest", JUnitReportReader.read(xml))
    print("SKIPPED-LISTED:", currency.verdict, currency.orphans)
```
`adv4/probes/test_adv4_f6_scope_probe.py` (imports and docstring condensed here; the file's code is otherwise identical):
```python
from __future__ import annotations
import os, sys
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_pending_contract_gate_f6 import _LISTED_CLASS_NODE, _LISTED_PARAM_NODE, _gate, _pytest_currency  # noqa: E402

def test_probe_a_scoped_run_that_never_collected_the_file_is_not_stale(tmp_path: Path) -> None:
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    other = "loremaster/tests/test_some_other_wave.py::test_in_scope"
    currency = _pytest_currency(tmp_path, gate, [(other, False)])
    assert currency.ok, (currency.verdict, currency.orphans)
```
The scope-aware satisfiability variant, applied to `pytest_self_destruct_findings` (`adv4/wb/f6_scope_aware_CONTROL/{anchor,repl}`):
```diff
         failing = {outcome.node_id for outcome in run.outcomes}
         findings: list[str] = []
+        scoped_files = {node.split("::", 1)[0] for node in run.collected}
         for bound in self.registry.bounds:
             for entry in bound.files:
+                if entry.path not in scoped_files:
+                    continue
                 for node_id in entry.red_nodeids:
```
Q7 traceback attribution: an inline python over `sdk3r8/mut/q7raise_raised.log` that splits the `_ … _` blocks and lists `(file, line)` frames per raise. Output for a19a: frames `test_fixwave_a19a_63c_i_a.py:191 → contextlib.py:214 → test_fixwave_a19_63c_i_a.py:135 → sdk3_shape_fakes.py:122`.

## RECEIPTS
| run | command (abbrev.) | log (`adv4/logs/`) | EXIT | count | TREE |
|---|---|---|---|---|---|
| F6 ref control | pytest F6 + probes + gate/currency/wave (b1) | `f6_ref_control.log` | 0 | 113 passed | 9207bfee… (b1 + probe) |
| F6 wrong gates ×5 (×2: second pass after the probe fix) | `runwb.sh b1 f6_*` | `wb_f6_*.log` | 0 ×5 (PROOF HELD) | 2F/17P ×3, 1F/18P ×2 | 47d51489… |
| scope probe on ref | b1 | (inline) | 1 | 1 failed | 47d51489… |
| scope-aware variant | b2, content backup + md5 restore (RESTORED-md5-exact) | `f6_scope_aware_control.log` | 0 | 479 passed | b2 pre-mutation 47d51489… |
| ref full F6 control | b2 | `f6_ref_full_control.log` | 1 | 1 failed (scope probe), 478 passed | 47d51489… |
| out-of-tree variant (instrument failure, discarded) | `adv4/f6scope` | `f6_scope_aware_control.log` (overwritten) | 1 | 4 location-dependent reds (no CLAUDE.md/gates.yaml) | — |
| W5 orphan print | `adv4/f6tmp` | (inline) | 0 | 1 passed ("now RESOLVES") | — |
| entry collect-only | main tree `pytest --collect-only -q <27 files>` | `collect_entry_head.log` | 0 | 1734 collected | 64f3d9d1… (HEAD 0836479) |
| replay queue ×7 | `queue_replay.sh` (haiku-runner; RAN: matches) | `wb_r_*.log` | per §REPLAY | per §REPLAY | 47d51489… pre/post |
| new queue ×7 | `queue_new.sh` (haiku-runner; RAN: matches) | `wb_n_*.log`, `wb_r_fb_txn_domain_unknown.log` | per §NEW BUILDS | per §NEW BUILDS | 47d51489… pre/post |
| txn wrong-class ×2 (first: my repl lacked a newline → SyntaxError, discarded) | `runwb.sh b2 n_fb_txn_domain_wrong_class` | `wb_n_fb_txn_domain_wrong_class.log` | 4 | 7F/14P | 47d51489… |
| reference control r8 set | b1, 8 files, `-n 8 --timeout=300` | `ref_r8_control.log` | 0 | **805 passed** | 47d51489…; `loremaster.__file__` = adv4/b1/… ; surrealdb 3.0.0 |

Every wrong-build log carries its pre-mutation `tree_id`, `loremaster.__file__` inside its own copy (b1 or b2, surrealdb 3.0.0, tenacity 9.1.4), "mutation LANDED (anchor matched exactly once)", a byte-exact restore (md5) and a POST-RESTORE TREE equal to the pre-run TREE.

## ROUTING TABLE (written before the first sweep)
| step | tier | who | reason |
|---|---|---|---|
| reads: rulings R25–R30, RULING-6/7/8, doc §ROUND 7/8, r8 REPORT, ADVERSARY3 | 3 | me | the frame I grade |
| read the r8 contract files | 3 | me | adversarial reading; a sampled draft would miss the door a wrong build walks through |
| reference provenance, tree_id per tree | 1 | me inline | one command each, critical path |
| r8 20× loop validity (20 logs) | 1 | me inline | 20 small greps, read all |
| F6 entry check (collected? escape-mangled?) | 1 | me inline script | set arithmetic, read all |
| design wrong builds, anchors, declared reds | 3 | me | adversarial judgment |
| scratch copies (`scratch_copy.sh`) | 1 | me inline | one command each |
| wrong builds / replays (`mutation_proof.py`, scoped) | 1 | haiku-runner ×2 queues | test runs |
| killed/survived verdict per build | 3 | me | grading |
| F6 wrong gate builds (pure-python, seconds each) | 1 | me inline | seconds each, on my critical path, I read all output |

Fan-out: haiku 2 · sonnet 0 · peak 1. Test runs inline: 21 (each seconds to ~2.5 min: the F6 suites and the 805 control), because they were on my critical path and I read the whole output.
