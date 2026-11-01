brief-base v16 read · brief project v7 read

# REPORT — adversary-58 (contract-adversary, packet 58: supersede re-anchor · task guarded-append shell · #130)

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — 14 MISSING PIN · 3 SAT DEFECT · 6 NEW DOOR (ruling needed) · rest NOT A DEFECT (§MISSING PINS, §RESIDUALS).
- **State: done-with-deviations** — D-LANE (lore-scoped lane; later ratified by lead #17046) · D-SPEC (graded against amendment 2 `e0760fd`, which post-dates the contract; lead #17041) · my two SAT full suites ran `-n auto` before I drained #17046's `-n 12` rule.
- **P1 headline: YES — 13 of my wrong builds SURVIVE the whole contract** (WB1–WB9, WB12, WB14–WB16; + K16 and WB18), each caught only by an adversary probe that passes on my independent reference build. Worst: WB1 (a genuine store fault served as the R1 "retry" teaching), WB2 (a K-ignoring cap on a legit layout ⇒ compose's bare error at K=3 — harm constructed), WB6/PR17 (the heal fails the BOOT: phantom head / 1300 stragglers), WB7 (#130 under a LIMIT serves a short answer). All 15 of the brief's / author's kill-claims re-derived on my build: KILLED.
- **Amendment 2 is itself defective (needs a RULING):** its heal chunk = the SUPERSEDE's cap in ROWS; a chunk spanning ≥6 superseded blockers composes >5000 ⇒ refused every boot, never converges (PR19: 1 of 1666 healed); its own ruled pin (one blocker) passes the defective build and reds a correct one (PR18). Its fail-OPEN heal also contradicts the unedited `ensure_ready` FAILS_LOUD door sweep.
- **SAT on the RIGHT base (HEAD+63c `b23f3e43`+§HELD+my build):** `22 failed, 11743 passed, 62 skipped, 3 xfailed, 2 errors`; REF-ONLY vs baseline = 1. Of 24 reds: 14 #466 contract-ahead (identical in both runs ✓), 7 UNRELATED HEAD reds (`restore_prod_dump.py`, `concurrent_wire_acceptance.py`), **3 attributable to 58's CONTRACT** (over-tight shell-count pin; D12's unruled heal order; `test_retry_seam` canonical door set lacks `tasks.py::claim_task`). NOT 0 failed. §HELD applies clean over 63c; hunks disjoint.
- **Author claims re-derived:** RED@HEAD = 68 ✓ (36 Assertion · 22 Attribute · 9 DID-NOT-RAISE · 1 ImportError, all right-reason) · 14/14 mutations — not refuted (7 re-derived as independent K-builds) · SAT "set-equal, 0 attributable" — true on THEIR base/build only · DUAL — 3 items missing (E5 supersede fault classification, E11, the claim-loss ERROR log) · P1c table — 6 rows understated (§P1c).
- Packages considered: survey table §P-PKG — no mechanism a library provides was specified; `tenacity`/`networkx`/`sqlglot`/SDK read live; verdicts keep_with_trigger / bespoke-justified / reuse.
- Odoo-20 portability: n/a — no Odoo seam touched.
- Reuse ledger: none — this agent introduced no production symbol (scratch instruments only, pasted §INSTRUMENTS).
- Graded: `5a43aeb` · HEAD-at-report: `ee4b80d` · DIFFERENT (20 behind) — the 20 commits are docs/reports + #466's contract tests (`37de0a7`); `tasks.py` and every 58 test file are byte-identical at both; amendment 2 (`e0760fd`) is among them and is graded as spec.
- Decisions needed: (1) am-2 heal chunk-size source (§AM2 #1); (2) am-2 fail-open vs the loud door sweep + D12's heal order (§AM2 #2, SD2); (3) the claim-loss ERROR log (MP14); (4) a dependent already on a legacy loop (MP8); (5) a phantom chain head at boot (MP5); (6) 7 unrelated HEAD reds + esc1 red since #174 — owners.
- Receipt pointers: §MISSING PINS · §P1 · §P1b · §P1c · §AM2 · §SAT · §P7 · §P5 · §P6b · §P6 · §FLAGS · §RESIDUALS · §INSTRUMENTS (every probe/driver/build pasted verbatim).

## §0 Capability check / setup (2026-09-26)
- idle-gate contract written: `/tmp/claude-idle-gate-lore/974aab4b-…-adversary-58.contract` = `{"artifact": "REPORT-adversary-58.md"}` (OK, not denied).
- lore tools loaded (`ToolSearch "+lore"`), registered `adversary-58` / session `63c-20260924`; drained + acked directive #17038 (grade as diff vs HEAD baseline; #466 contract-ahead reds must be identical in both runs).
- HEAD moved during spawn: graded `5a43aeb`; HEAD at start of work `a66c95e` (4 commits: 3dfed69 docs, 40c188d docs, 37de0a7 #466 contract tests, a66c95e docs). None touch `tasks.py` or the 58 test files.
- grep/rg hook-blocked (#473): all text search via awk/sed — a fallback, said out loud.

## §P6b stage 1 — INDEPENDENT enumeration of to-be-replaced behaviour (written BEFORE opening the contract's §DUAL)
Source read at `5a43aeb`, `loremaster/loremaster/tasks.py` (symbols cited, not lines).

E1 `_transition_fragment`: SET status=$to, updated_at=time::now(), provenance.events += [$event]; release (target open) ⇒ owner=NONE, claimed_at=NONE; target done ⇒ summary=$s, report_path=$r (report_path bound EVEN WHEN None — an explicit write of NONE); WHERE status=$from AND superseded_by IS NONE; THROW `_TRANSITION_ALREADY_MESSAGE` on zero rows; LET var `$tr_updated`; event {actor, action=transition, to, at}.
E2 `_supersede_fragment`: stamp SET superseded_by=$new, updated_at, provenance.events += [$ev] WHERE superseded_by IS NONE — NO status conjunct (a done/wontfix X is supersedable); THROW `_SUPERSEDE_ALREADY_MESSAGE`; the CREATE is ORDERED AFTER the guard (a successor can never outlive an un-landed stamp); 3 statements.
E3 `_claim_fragment`: LET $clm_resolved over the CALLER-SUPPLIED (pre-read) `blocked_by` list ∩ terminal statuses; UPDATE owner/status=claimed/claimed_at/updated_at WHERE status=open ∧ owner IS NONE ∧ superseded_by IS NONE ∧ len(distinct(blocked_by)) = len($clm_resolved) (T5 dedupe tolerance); NO provenance event; a LOSS commits an empty UPDATE (no THROW); terminal param sorted.
E4 `claim_task`: pre-reads `blocked_by` under the documented assumption *"blocked_by never changes after creation"* — **FALSE after 58** (re-anchor rewrites it) ⇒ the resolved set is computed over a possibly-STALE list (the pre-read race); victory by owner identity; `superseded_blockers` read only on a loss with blockers; a genuine store fault PROPAGATES (no except ladder today).
E5 `supersede_task`: pre-read; sequential already-superseded → IllegalTransitionError; #174 sentinel (None inherit / [] clear / [ids] replace), dedupe order-preserving; self-dependency guard → TaskCycleError; `_reject_unusable_blockers` + `_refuse_a_cycle({new_id: deps})`; event {created_by, supersede, successor, at}; returns `str`; except ladder: transport + contention-exhausted pass through; SurrealStoreError → re-read, superseded ⇒ IllegalTransitionError, else RE-RAISE AS-IS (a new THROW class — the R1 straggler — must be classified without swallowing a genuine store fault).
E6 `direct_dependents`: one hop, store-side CONTAINS, sorted; docstring teaches R10(iii) strand + "dependency transfer DEFERRED" + "blocked_by immutable after creation".
E7 `_candidate_statement` / `query_tasks`: status= filter serves superseded rows; `_is_blocked` ignores the row's own `superseded_by` ⇒ blocked=False serves superseded rows with terminal blockers (#130).
E8 `_backfill_blocks_edges`: mirrors ∀ rows ∀ blocker states (incl. superseded blockers — explicitly NOT filtered), phantom skip recorded, legacy cycles recorded (networkx), idempotent vs store edge set; 2–3 round trips.
E9 edges: X's INCOMING edges (Z→blocks→X for X.blocked_by ∋ Z) must SURVIVE the supersede (X still blocked_by Z) — a DELETE keyed on `in = X OR out = X` is a plausible wrong build.
E10 server `_render_supersede_result` STRANDED warning via post-write `direct_dependents`.
E11 dedupe side effect: `array::distinct` on the rewritten column also collapses LEGACY duplicate entries of OTHER blockers ([A, A, X] → [A, X']) — changes a legacy row beyond the X entry (benign for the CAS after T5; a behaviour change nonetheless).
E12 txn size O(K) → O(K + 3N) (+1 closing guard, +1 DELETE).
E13 claim-loss render `superseded_blockers` branch (R10(iii)) reachable today for every strand; after 58 only for legacy / R2-window strands.

## §P6b stage 2 — DIFF against the author's §DUAL (B1–B20, D1–D12), opened only after stage 1
| mine | author | verdict |
|---|---|---|
| E1 transition shell details (release clears owner/claimed_at; done writes summary+report_path) | B8 | matched (caller detail; existing suites cover — SAT) |
| E2 stamp has no status conjunct (terminal X supersedable) | FORK-A / B16 | matched |
| E3 claim resolves over the PRE-READ list | B20 | matched, pinned (K15 below) |
| E4 claim: a genuine store fault propagates | B6-sub | matched, pinned (`G::TestAClaimThatFailsForANonCASReasonIsLOUD`) |
| **E5 supersede: a non-lost-race store fault is RE-RAISED AS-IS** — the new R1 classification must not launder it | **ABSENT** | **inventory miss → MISSING PIN (WB1)** — the author pinned the claim-side twin (B6-sub) but not the supersede side; every atomicity pin uses `pytest.raises(Exception)` |
| E6 direct_dependents prose | B4 | matched |
| E7 #130 | B9 | matched (+ WB7 limit door) |
| E8 backfill ESC-4 records legacy cycles; the heal can CLOSE one after/before it runs | ABSENT | residual (exotic, raw-only) — heal order vs `_record_legacy_cycles` unruled; see §D12 order finding |
| E9 X's INCOMING edges survive | implicit | pinned by `S::TestRequiredGreen` (#174 inherit ∀-row mirror; zero-dependents edge set) — NOT A DEFECT |
| E10 render | B5 | matched |
| **E11 `array::distinct` also collapses LEGACY duplicates of OTHER blockers** (`[A, A, X]` → `[A, X']`) | ABSENT | inventory miss; benign for the CAS after T5; contradicts the contract's own "only the X entry is rewritten" wording for legacy dup rows — NOT A DEFECT (record only) |
| E12 txn size | B14 | matched |
| E13 legacy render branch | 7.10 | matched |
| **NEW (found while diffing): a routine claim LOSS now logs `store.transaction.rolled_back` at ERROR** (`_txn._log_rollback`) — before 58 a loss was an empty committed UPDATE, silent | ABSENT (B6 says "zero writes either way" and never mentions the log) | **NEW DOOR (needs ruling)** — PR10 below |
Author items with no stage-1 twin (B3, B7, B10, B11, B12, B13, B15, B16, B17, B18, B19) are ADDED behaviour, each grounded in the reference diff — no finding.

## §P6 corpse sweep (bare, anchor-free; awk — grep hook-blocked) at `a66c95e` pre-HELD
- `server.py` `STRANDED` / `stranded` / `re-point` / `WARNS, never` (render + docstring) → removed by §HELD; post-HELD the R-file's bare sweep pins it. VERDICT: corpse, retired by the patch.
- `test_task_read_surface.py` `TestSupersedeWARNSWhenThePredecessorHasDEPENDENTS` failure-message prose (`"stranded … re-point these at the successor"`) and `test_superseding_a_task_with_NO_dependents_warns_about_NOTHING` message (`"only one stranded a dependent"`) — ASSERTIONS still hold in the new world (render names the dependents; the receipt line is the extra line); PROSE is a corpse. VERDICT: corpse PROSE (no assertion pins the old world) — builder rewrites.
- `test_blocks_edge.py` `MIRROR_IMMUTABLE_VERBS` comment + docstring ("blocked_by never changes after creation") — author FLAG 2 confirmed; corpse PROSE.
- `tasks.py` `direct_dependents` + `claim_task` docstrings (DEFERRED / immutable) — author BUILDER CONSTRAINT 8; corpse PROSE owed by the build.
- `stranded` hits in `lore_deploy.py`, `test_comms_tool.py:6603` — unrelated domain. VERDICT: NOT corpses.
- `DEFERRED` hits outside tasks/server (extension.py, render.py, `DEFERRED_TO_PACKET_43` family, 04b3 CA-11) — unrelated. VERDICT: NOT corpses.

## §FLAG verdicts (early notes — final verdicts in §FLAGS)
- **F3 `scripts/test_forgery_door_sweep.py` (D12):** outside kickoff §8's writable class by its letter (§8 names `test_task_*`/`test_tasks_*`); not weakening (4→5 doors, re-keyed with reason). **BUT it silently rules an UNRULED ORDER:** `assert report.control_calls not in silent` + `len(silent) == calls − 2` require the heal door to be LAST, i.e. `_reanchor_stragglers` AFTER `_backfill_blocks_edges`. Amendment 1 says only "beside". A heal-FIRST build (mine) is RED there — see SAT. The order is not neutral: heal-first lets the SAME boot's `_record_legacy_cycles` see a cycle the heal closes; heal-last defers that record one boot.
- **D9 (`test_blocks_edge.py` supersede-routes-through pin):** its DUAL comment claims *"a hand-rolled RELATE in a helper still reds"* — the assertion is PRESENCE-only (`"_relate_fragment" in called_attrs` over one hop). A message promising a check the assertion does not perform (CLAUDE.md P2 2026-07-14 class). Wrong build queued (K16).

## §DECLARED — expected RED sets fixed BEFORE any wrong-build run (2026-09-26)
Instruments (scratch, md5 at declaration): `declared.py` 6df71751 · `wrong_builds.py` 847f80f3 (K16/K17 appended) · `test_adversary58_probes.py` 2cf0d5f4 · reference `tasks.py` 9c254944.
Batch-2 (declared here, not in declared.py): REFERENCE → PR16 GREEN, **PR17 RED** (the DECISIONS-2 construct: 1300 stragglers × 4 heal statements > 5000 ⇒ boot fails); WB2 → PR16 RED; K16 → ALL GREEN (D9 over-claim survives); K17 (heal after backfill) → `scripts/test_forgery_door_sweep.py` GREEN (control: D12 keys the ORDER); P5 fake re-anchor removed → fake-consuming suites ALL GREEN (the fake cannot fail).
REFERENCE-build doors declared RED on the correct build itself: PR9 (scanner reach), PR10 (ERROR log on a routine claim loss). PR11 observational (index use of production statements — no prediction).

## §0b Deviations (recorded when taken)
- **D-LANE (2026-09-26 ~16:25Z):** the brief's lane rule is "ONE pytest session on the box". A different project (`mobile-pricepaper-smoke`) ran pytest continuously (`tests/test_harness.py` ≥10 min at 28 s CPU, then `tests/test_inventory.py`, …), so a box-wide wait never freed. Switched my waiter to LORE-SCOPED (waits for any pytest / `lane_pytest.sh` whose cmdline or cwd is under the lore tree or a lore session scratch) — the same mode contract-64b (same lead) records. #466's rationale (lore's uvicorn ports + per-test DBs on spike) is lore-local; the other project's pytest opens no lore listener. The 15 GB watchdog is unchanged. Instrument: `lane58cmd.sh` (pasted in §INSTRUMENTS).
- **D-SPEC (found mid-review):** HEAD moved past the graded `5a43aeb` to `17c52b7`; among the commits is **`e0760fd` — packet 58 AMENDMENT 2**, which rules the contract's §DECISIONS 1 and 2. "Later wins" (brief) ⇒ graded against amendments 1 AND 2. The 63c amendment 28 (`eb75f57`, `17c52b7`) changes the 63c fix but lands in the audit's fix pass; my SAT base stays the brief's `b23f3e43` patch.
- **D-HEAD for SAT:** reference tree `ref58` sits at `37de0a7` (+63c+HELD+ref58 build); baseline tree `base58` at `17c52b7` (+63c). `git diff --stat 37de0a7 17c52b7` = docs + REPORT files only (7 files: three amendment docs, store-ref §6.7, reports) — code-identical bases.

## §P-PKG — my OWN package table (built before reading the author's line), then the diff
Mechanisms the contract (+ amendments 1–2) specifies, what I READ, verdict:
| mechanism | candidates evaluated | what I READ (installed) | verdict |
|---|---|---|---|
| cycle check over the REWIRED graph (a cycle through X') | `graphlib` (already the shared detector), `networkx` 3.6.1 (`simple_cycles`, `find_cycle`, `has_path`) | `tasks.find_blocked_by_cycle` (graphlib `TopologicalSorter.prepare()` → `CycleError.args[1]`); `networkx` attrs introspected live (`find_cycle`, `simple_cycles` present) | **keep_with_trigger** — the shared R6 detector + its step-over loop are shipped and mutation-proven (MP-1); 58 only OVERLAYS rewired columns and narrows `minted` to {X'}. Trigger: a third cycle-query shape (then `networkx.has_path(G, X'-blockers, X')` answers "a cycle through X'" directly, no drop-loop). |
| derived hub cap | none applicable (integer arithmetic over `compose`'s own count) | `_txn.compose` body-count check; `TXN_STATEMENT_HARD_CAP` | **bespoke-trivial, REUSING `compose`** — correct; the risk is SHARING (WB15), not a package |
| guarded-append SurrealQL builder | SurrealDB SDK 2.0.0 (no builder: modules `cbor, connections, data, errors, request_message, types`), `sqlglot` 30.8.0 (no SurrealQL dialect — introspected), `pypika` (not installed; no SurrealQL) | installed module lists | **bespoke-justified** — extends the in-house `TxnFragment`/`compose` seam (findings' shell is the precedent; #489 ledgers the unification) |
| R1: NO retry (refuse + teach) | `tenacity` 9.1.4 (installed) | — | **n/a by ruling** — amendment 1 forbids a ledger retry; the store driver `retry_on_conflict` remains the only retry (correctly untouched) |
| heal chain-follow to HEAD | `networkx` descendants / engine recursive path `@.{..}` | store ref §4 recursive paths (cap 256, needs TIMEOUT) | **bespoke acceptable** (a dict walk) — but MUST be bounded (PR15/WB17): the author's `_head` is bounded by `seen` (returns a loop member, not None — see residual R-HEADLOOP) |
| heal chunking (am-2) | none (arithmetic) | — | bespoke; the defect is the ruled SIZE SOURCE, not a package (§AM2) |
| WARN telemetry | `SurrealStore._log_transaction_size` (in-house, ONE policy) | `store/surreal.py` body | **REUSE** — sharing unproven by mutation (WB14) |
| one-producer AST scan | `ast` (stdlib), `libcst` / `semgrep` (NOT installed) | installed metadata | bespoke acceptable; the defect is REACH (WB12), not the package |
| EXPLAIN walker | `test_keeps_schema.TestTheKeeperIndexFires` | its `_operators` / `_scans_table` | REUSE (author's choice confirmed) |
| mutation driver | `mutmut` / `cosmic-ray` (NOT installed); in-house `scripts/mutation_proof.py` | its docstring + `--help` | REUSE in-house (single-anchor; my multi-edit builds used its declare-then-diff discipline in `wb_driver.py`) |
**Diff vs the author's line** (`Packages considered: none — no production mechanism specified`): the contract DOES specify mechanisms (it pins a derived cap, a shell signature, a chunk-free heal, an AST scanner); "none" is the wrong answer to the question even though every verdict above lands on reuse/bespoke-justified. No `bespoke` verdict of the author's asserts a package limitation without a read — because the author asserted none at all. **P-PKG: no mechanism a library already provides was specified — NOT A DEFECT; the author's line is imprecise (records "none" instead of the table).**

## §P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` (lore repo; my own enumeration found 0 Odoo seams; the author's line agrees).

## §RUN1 — the contract against adversary-58's OWN reference build (scoped), 2026-09-26 16:25Z
Tree: `ref58` = `37de0a7` (+ 63c-i-a patch `b23f3e43` + §HELD + my build `tasks.py` md5 `9c254944`); `loremaster.__file__` = `…/974aab4b-…/scratchpad/ref58/loremaster/loremaster/__init__.py`.
Files: the four 58 files + every DUAL-edited file (`test_blocks_edge`, `test_task_ledger`, `test_task_read_surface`, `test_link5_render_containment`, `test_mcp_server`, `scripts/test_forgery_door_sweep.py`).
Tail: **`2 failed, 1501 passed, 1 skipped, 3 warnings in 160.78s`**. Both reds reject a CORRECT build (over-tight pins):
1. **`G::TestParamNamesDoNotCollideAcrossComposedShells::test_three_reanchors…`** — `assert calls.count(ACTION_REANCHORED) == 3` got **4**: my build DERIVES the cap per call by building the real fragments through the shell (kickoff F-1: *"the ledger BUILDS the fragments, COUNTS the composed body statements"*), so the spy sees the derivation's shell calls too (`[None, None, 'dependency_reanchored', 'supersede', …]`). The class docstring promises *"the composition really contained ≥ N+1 shell outputs"*; the assertion demands `==`. A message/assertion mismatch in the over-tight direction — it forbids a ruled mechanism. **SAT DEFECT (over-tight)**; fix: `>= 3` / count only shell outputs that reached `compose` (spy on `compose`, not on the shell).
2. **`scripts/test_forgery_door_sweep.py::…::test_a_ledger_that_SWALLOWS_its_backfill_failure_is_CAUGHT`** — `assert 5 not in [3, 4, 5]`: with the heal FIRST, the heal's read is door k=2 (RAISED, loud) and the swallowed backfill is k=3..5; D12's edit hard-codes the heal as the LAST door. Amendment 1 says only "beside". **SAT DEFECT (pins an unruled order)** — control K17 (heal after backfill) in batch 2.
Everything else — including every DUAL-edited existing file and all 108 of the 58 contract tests other than #1 — GREEN on an independently-written build.

## §P1 — WRONG BUILDS vs the contract (declare-then-diff against the reference's own reds; 2026-09-26 16:28–16:35Z)
Instrument: `wb_driver.py` + `wb_delta.py` (pasted in §INSTRUMENTS); builds = exact-anchor substitutions over my reference `tasks.py` (`wrong_builds.py`, each anchor asserted to occur exactly once — #194). The reference build's own reds are the baseline: **PR9, PR10 (declared doors) + `G::TestParamNamesDoNotCollide…` (over-tight, RUN1 #1)**; every row below is the DELTA over that baseline. Every declared set fired, **0 declared-but-green across all 30 builds**.

### Survivors — contract GREEN, only my probe RED (each a MISSING PIN unless marked)
| build | the wrong behaviour | contract delta | probe that sees it |
|---|---|---|---|
| **WB1** | every non-lost-race rollback of a supersede is served as the R1 teaching (*"… was created while … nothing changed; retry"*) — a genuine store fault LAUNDERED into a false cause | none | PR1 |
| **WB2** | cap accessor ignores K, on a LEGIT layout whose R1 guard is 2 statements (`LET` + `IF`; fixed₀ = 6) — contract samples K ∈ {0, 2} and `(5000−6−K)//3` is 1664 for K = 0,1,2 | none | PR2 (K ∈ {0, per, per+1}); **HARM (PR16, batch 2): at K = 3 the accessor says 1664; a 1664-dependent supersede composes 5001 statements → compose's BARE error served** (*"composed transaction has 5001 statements, exceeding the hard cap …"*) |
| WB2a (control) | the legit 2-statement layout alone | none | none — PR2 is not over-tight |
| **WB3** | heal log `count` = (row, blocker) PAIRS, not rows | none | PR3 |
| **WB4** | heal re-anchors only the FIRST superseded entry of a row | none | PR3 (row still names chain_b[0]) |
| **WB5** | heal RELATEs head→Y even when Y already names the head ⇒ DOUBLED edge | none | PR4 |
| **WB6** | heal RELATEs to a PHANTOM chain head ⇒ ENFORCED rejects ⇒ the whole boot fails | none | PR5 — NEW DOOR (am-2 now rules fail-OPEN: see §AM2) |
| **WB7** | #130 exclusion done CLIENT-SIDE after a `LIMIT`'d candidate read ⇒ `status=open limit=3` returns FEWER while claimable rows exist (T1 broken) | none | PR6 |
| **WB8** | `reblocked` only when X is `done` (a `wontfix` X re-blocks silently) | none | PR7 (author's own door 5 residue, confirmed) |
| **WB9** | cycle check with `minted = all pending` ⇒ a dependent already on a LEGACY loop (not closed by this rewire) REFUSES the supersede — forever (no verb edits `blocked_by`) | none | PR8 — NEW DOOR (spec-silent; recommend: refuse only cycles through X') |
| **WB12** | a 57-shaped 4th hand-rolled guarded append whose THROW template is a MODULE CONSTANT (`_ASSIGN_GUARD_FMT.format(...)`) | none — the one-producer pins stay GREEN | PR9 (the scanner itself misses it — RED on EVERY build, reach defect) |
| **WB14** | task WARN via a CLONED threshold compare (`task.apply.large_transaction`) instead of `SurrealStore._log_transaction_size` | none | PR13 (silence the shared policy ⇒ a private copy still warns) |
| **WB15** | accessor uses a LITERAL `5000` copy of `TXN_STATEMENT_HARD_CAP` | none | PR14 (mutate the shared cap ⇒ the accessor must move) |
| **WB16** | re-anchor note `at` is a constant (`2000-01-01…`) | none | PR12 (low severity) |
| **K16** (batch 2) | dependents' `X'→Y` RELATEs HAND-ROLLED in the supersede builder (successor RELATEs still via `_relate_fragment`) | none (`b2_K16`: `1 failed, 85 passed` — the 1 is the reference's over-tight pin) | none — D9's comment *"a hand-rolled RELATE in a helper still reds"* is FALSE (presence-only assertion) |

### Killed — the brief's list + the author's M-claims re-derived on MY build (P4)
| build | brief item / author claim | killed by (delta) |
|---|---|---|
| K1 | re-anchor outside the supersede txn | all 6 `TestTheSupersedeIsONETransaction` legs + R1 + hub accessor pins + REANCHOR sharing |
| K2 | a skipped terminal dependent (F-2) | the `world` fixture (12 errors) + A1 all-status + note/∀ pins |
| K3 | literal cap in place of the derived cap (M4) | accessor[2], MUTATION, cap[K=2] — ⚠ caught ONLY because fixed₀ = 5 on my layout; see WB2 |
| K4 | cycle check over the UN-rewired graph (M6) | cycle refusal + backfill-after-refused |
| K5 | dedupe missing (`[X,X]`) | `TestTheRewireDedupes` (+ PR4) |
| K6 | provenance note mis-sourced (actor) | note pin + heal-note pin |
| K7 | routing-not-sharing: private re-anchor clone | one-producer ×2 + ALWAYSTHROW + APPEND ×2 |
| K8 | claimable partition disagrees with the CAS (#130, M3) | status sweep, both partitions, both directions |
| K9 | heal not idempotent (logs every boot) | second-boot-silent |
| K10 | heal stops at the first hop (M10) | 3-hop + done-head |
| K11 | heal counts chains | count pin |
| K12 | R1 auto-retry | `apply_calls == 1` |
| K13 | `reblocked` includes W (M11) | A1 reblocked + held render end-to-end |
| K14 | no R1 closing guard (M5) | R1 refusal |
| K15 | claim CAS on the stale pre-read (M7) | A1 pre-read race |
**P4 verdict on the author's "14/14 mutation proofs HELD":** re-derived for M3/M4/M5/M6/M7/M10/M11 and the brief's list on an INDEPENDENT build — each held. M1/M2/M8/M9/M12/M13/M14 not re-run as single mutations; their classes are covered by K7 (sharing), K1 (atomicity), the RUN1 green of the edge/sharing pins, and M14's HELD index pins (GREEN on my tree). Not refuted.

### Batch 2 constructs
- **PR17 — §DECISIONS 2 CONSTRUCTED at scale** on my (amendment-1-faithful, one-transaction) heal: 1300 raw stragglers of one superseded blocker → `ensure_ready` raises `SurrealStoreError: composed transaction has 5200 statements, exceeding the hard cap of 5000` — **the boot fails**. The graded contract has NO pin for this (it predates amendment 2). See §AM2.
- **K17 (heal AFTER backfill)**: `scripts/test_forgery_door_sweep.py` → `20 passed` (vs 1 failed heal-first) — D12 keys ONLY on the heal-vs-backfill ORDER.

## §AM2 — amendment 2 (`e0760fd`, later than the graded contract) — what the contract now OWES, and where the RULING itself is defective
The graded contract (`5a43aeb`) predates amendment 2 and carries **no pin** for either ruling. Constructed (batch 3, 2026-09-26 16:36Z, `ref58`):
| probe | REFERENCE (am-1 single-txn heal) | AM2L (am-2 LITERAL: chunks of `max_reanchor_dependents(0)` ROWS, fail-open) | AM2C (control: chunks packed against the HEAL's own composed count, verified per chunk) | WB18 (owner= also excludes superseded) |
|---|---|---|---|---|
| PR18 — am-2's OWN ruled pin shape: `cap+1` stragglers of ONE blocker ⇒ `count == cap+1`, `chunks == 2` | RED (boot fails) | count ✓ chunks ✓ — then MY probe's last line errored (`await` in a genexp → `TypeError`: a P0 defect in my instrument, fixed, re-run queued §FOLLOWUP) | **RED: `chunks == 1`** — 1 DELETE + 1666×2 + 1666 = 4999 ≤ 5000 fits ONE chunk; the ruled pin DEMANDS the literal sizing and so reds a CORRECT chunker | — |
| PR19 — the SAME `cap+1` population over TEN superseded blockers ⇒ all healed in one boot; second boot silent | RED (boot fails) | **RED: `count == 1`, `chunks == 2`, WARNING `task.backfill.straggler_chunk_failed`** — chunk 1 = 1665 rows × 3 + 10 DELETEs = 5005 > 5000 ⇒ `compose` refuses it at BUILD time; 1665 stragglers stay stranded; the next boot builds the SAME chunk ⇒ **the sweep never converges** ("the sweep is the retry" retries a deterministic refusal forever) | GREEN | — |
| PR20 — am-2 (a): `owner=` serves a HELD superseded row decorated; `owner=+status=claimed` excludes it; two-row discriminator | GREEN | — | — | **RED** — and the whole 58 contract stays GREEN (delta: none) |
| `scripts/test_forgery_door_sweep.py` | 1 red (D12 order) | **2 red** — incl. the UNEDITED `test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD` | **2 red** — same | 1 red (D12 order) |

**Findings (am-2):**
1. **SPEC PRESCRIBES THE BUG — am-2 (b)'s chunk SIZE SOURCE.** *"partitioned into chunks of `max_reanchor_dependents(0)` rows (the SAME derived accessor F-1 uses — one constant, one derivation)"* sizes a HEAL chunk by the SUPERSEDE's per-dependent cost. A heal row costs the same 3 statements PLUS one edge-DELETE per DISTINCT superseded blocker in the chunk (a supersede needs ONE DELETE because all its dependents share X; a heal chunk spans many X's). Exact arithmetic on my layout (the author's heal has the same shape — §APPENDIX-REF: one `DELETE … WHERE in = $old` per distinct old): a full chunk overflows iff distinct blockers ≥ 6 (4995 + 6 > 5000), and a row naming two superseded blockers costs 5. **"One constant, one derivation" is the defect: two different statement shapes share one accessor.** And am-2's own pin (cap+1 of ONE blocker) is the arithmetic-aligned fixture that cannot see it (PR18 GREEN on the defective build, RED on the correct one). **Needs a RULING (sidecar/operator), not a contract edit**: size heal chunks from the HEAL's own composed count (PR19's control AM2C does exactly that), and pin with a multi-blocker population.
2. **am-2 (b)'s fail-OPEN contradicts the standing `ensure_ready` forgery-sweep invariant.** *"The boot itself never fails on a heal fault"* makes the heal's read door RETURN over an injected store fault; the 04b-1 instrument (`test_every_store_door_in_ensure_ready_over_a_legacy_store_FAILS_LOUD`, unedited) demands every door RAISE — AND the contract's own D12 edit demands the heal door be LOUD. Three sources disagree. **Needs a RULING**: either the heal's store faults stay loud (fail-open covers only per-chunk `compose`/row CAS faults, logged), or the sweep allowlists the heal door with WARNING-observed loudness (an evidence-backed exemption + re-open trigger).
3. **MISSING PINS owed by the contract for am-2 (a)/(b)** (none exist at `5a43aeb`): PR20's shape (WB18 survives the whole contract); chunking + `chunks` field + per-chunk fault isolation + convergence (the single-transaction reference passes the whole contract while failing the boot at 1300 stragglers — PR17).

## §FLAGS — verdicts (brief focus 3)
- **F1 `scripts/esc1_write_path_cycle_closure.py` breaks post-build typecheck — CONFIRMED.** On `ref58` (build applied), `./scripts/typecheck.sh` → `scripts/esc1_write_path_cycle_closure.py:426: error: Argument 1 to "transitive_blockers" of "TaskLedger" has incompatible type "SupersedeResult"; expected "str" [arg-type]` → `typecheck: scripts FAILED`. The author's exact edit (wrap the call, read `.successor_id`) → `mypy` on the file: `Success: no issues found`. **Edit confirmed exact.** ⚠ **ADDITIONAL, PRE-EXISTING (not 58's):** the script's RUN exits 1 at HEAD — `FAIL [boundary-5] successor is born with NO dependencies and NO edges [ids=['leg_c','leg_b','leg_a']]` on BOTH `base58` (HEAD+63c, no 58) and `ref58` — a corpse assertion since packet 05b's #174 made the successor INHERIT `blocked_by`. A committed instrument that has been red since 05b, outside every gate (not a test file). Surfaced per scope law; owner: whoever owns #174/esc1 (lead's call).
  - Same typecheck run, OTHER legs (not 58's, recorded so they are not mistaken for it): `loremaster` leg — `test_no_raw_listener_in_test_trees.py` 2 errors; `skills` leg — `test_loopback_home.py:24-25` import-untyped ×2 — the #466 contract-ahead set (committed `37de0a7`), RED_ADJUDICATED per the lead's directive #17038.
- **F3 `scripts/test_forgery_door_sweep.py` (D12)** — legitimacy: outside kickoff §8's writable CLASS by its letter (not `test_task_*`); the edit itself is re-keyed with a reason and does not WEAKEN the 04b-1 pin. **But it is not neutral**: it pins the unruled heal-vs-backfill ORDER (RUN1 #2; K17 control 20/20 green), and under amendment 2's fail-OPEN heal BOTH it and the UNEDITED `…FAILS_LOUD` pin go red (§AM2 #2). Verdict: **needs a ruling (order + fail-open-vs-loud)**, not a revert.
- **§DECISIONS 1 (`owner=`-only over a superseded row)** — now RULED by amendment 2 (a) (serve it, decorated; `status=` still excludes). The contract has NO pin; WB18 (exclude on `owner=` too) passes the whole contract (PR20 catches it). **MISSING PIN.**
- **§DECISIONS 2 (heal txn size)** — CONSTRUCTED (PR17: boot fails at 1300 stragglers, 5200 statements) and now RULED by amendment 2 (b) — whose chunk-size source is itself defective (§AM2 #1).

## §P1b — QUANTIFIER TABLE (every invariant the contract pins; receipts = §P1 builds/probes)
| # | invariant | class | receipt |
|---|---|---|---|
| Q1 | ∀ dependents of X (every status, superseded, inherited, dual, phantom-bearing, `[X,X]`) are rewired to X' | ∀-over-inputs (9-shape fixture self-checked against `direct_dependents`) | door attempts KILLED: K2 (skip terminal), K5 (no dedupe) |
| Q2 | `edge ≡ blocked_by` ∀ rows | ∀-rows, derived + coverage-checked (`row_count`) — **but evaluated only in fixtures where the heal's dedupe branch cannot fire** | **WB5 SURVIVES** (heal RELATEs head→Y when Y already names the head ⇒ doubled edge); PR4 |
| Q3 | ∀ dependents get ONE note {from X, to X', actor = superseder, at} | ∀ on actor/from/to; **`at` guarded only by "parses as ISO"** | K6 KILLED (actor); **WB16 SURVIVES** (constant `at`); PR12 |
| Q4 | a failed supersede changes NOTHING — regardless of cause | ∀ over causes enumerated (injected row/edge k∈{1,2,3}, hub, R1, cycle) — ✓ | K1 KILLED |
| Q5 | a failed supersede REPORTS its true cause | **guarded-by-failure-mode**: only the R1 straggler (typed refusal) and the lost stamp race (`IllegalTransitionError`) are pinned; every other cause is `pytest.raises(Exception)` | **WB1 SURVIVES** (any rollback served as the R1 "retry" teaching); PR1 |
| Q6 | no row names X after a successful supersede | ∀-rows scan | K14 KILLED (R1) |
| Q7 | served-as-claimable ⇔ CAS-claimable (#130, both directions) | ∀ over the served set — **guarded by `limit=None`** | K8 KILLED; **WB7 SURVIVES** (client-side post-filter under a `LIMIT` ⇒ short answer); PR6 |
| Q8 | hub cap == derived cap | **guarded by arithmetic alignment**: K ∈ {0, 2} only; discriminates a K-ignoring accessor iff fixed₀ ≢ 0 (mod 3) | K3 KILLED on my layout (fixed₀ = 5); **WB2 SURVIVES** on a legit layout (fixed₀ = 6) with real harm (PR16: bare compose error at K = 3); PR2 |
| Q9 | the heal re-anchors ∀ stragglers ∀ superseded entries, counts ROWS | **guarded**: every fixture straggler names exactly ONE superseded blocker (rows ≡ pairs) | K10/K11 KILLED; **WB3, WB4 SURVIVE**; PR3 |
| Q10 | the heal never fails the boot (am-2) / skips a phantom head (backfill's R11 posture) | **unpinned** | **WB6 SURVIVES**; PR5; PR17 (scale) |
| Q11 | `reblocked` == previously-claimable subset, ∀ terminal predecessor statuses | **guarded**: X is `done` only | K13 KILLED; **WB8 SURVIVES** (`wontfix` X); PR7 |
| Q12 | a cycle is refused iff the REWIRE closes it | pinned for "closes via X'" and "legacy loop upstream of X"; **a legacy loop THROUGH a dependent is unpinned** | K4 KILLED; **WB9 SURVIVES** (over-refusal); PR8 — NEW DOOR |
| Q13 | exactly one guarded-append producer ∀ ledger modules | ∀ modules (derived) — **but "producer" = THROW ∧ UPDATE co-occurring in ONE function's string constants** | K7 KILLED; **WB12 SURVIVES** (guard template as a module constant); PR9 |
| Q14 | sharing ∀ callers (transition, stamp, claim, re-anchor, heal) | ruled hand-list (author-stated bound) | K7 KILLED |
| Q15 | the WARN is ONE policy | effect-observed only | **WB14 SURVIVES**; PR13 |
| Q16 | the accessor follows the shared compose cap | effect-observed at one value of the constant | **WB15 SURVIVES**; PR14 |
| Q17 | claim loss = RESULT, zero writes, no event (∀ 4 causes) | hand-list (author-stated) | GREEN on my build; K15 KILLED (pre-read race) |
| Q18 | `owner=` serves a held superseded row; `status=` excludes (am-2 a) | **unpinned** | **WB18 SURVIVES**; PR20 |
| Q19 | the heal chunks, converges, isolates faults (am-2 b) | **unpinned** | reference single-txn heal passes the whole contract and fails the boot at 1300 (PR17) |

## §P1c — REACH TABLE (every guard/scan the contract introduces or relies on)
Legs: E = empirical (built the wrong version in scratch), C = construction-inspection.
| instrument | reach (set) | derived? | coverage checked? | effect vs proxy | one source, mutation-proven? | verdict |
|---|---|---|---|---|---|---|
| one-producer AST scan (`G`) | functions/module scopes of every `.py` under the package | modules DERIVED (`rglob`, floor checked); **producer = token co-occurrence per scope — a hidden shape** | floor only (tasks+findings found) | PROXY (source text, not the composed transaction) | n/a | **MISSING PIN (E: WB12/PR9)** — a clone whose THROW lives in a module constant escapes; the author's door 1 (split across helpers) is a second instance. Runtime alternative: spy `compose` while driving every verb and assert every THROW-bearing statement came from the shell's output (tag it). |
| sharing mutations ALWAYSTHROW / APPEND | 4 ruled callers + heal | hand-list (ruled; bound stated by author) | `perturbed ≥ 1` per leg ✓ | EFFECT ✓ | ✓ (E: K7 killed) | SAFE within its stated bound |
| derived hub cap | K ∈ {0,2} × {cap−1, cap, cap+1} | per/fixed DERIVED from a `compose` spy ✓ | **K sampled below a floor boundary** | EFFECT ✓ | per-dependent padding ✓; **the shared `TXN_STATEMENT_HARD_CAP` NOT mutation-proven** | **MISSING PINS (E: WB2/PR2/PR16; WB15/PR14)** |
| R1 closing guard | rows naming X in the txn snapshot | DERIVED (engine `CONTAINS`) ✓ | one straggler; byte-inert ✓ | EFFECT ✓ | n/a | SAFE (E: K14 killed) |
| hub refusal | the dependents read | derived ✓ | cap+1 byte-inert ✓ | EFFECT (refusal before write) ✓ | via the accessor | SAFE |
| WARN telemetry | every task transaction | n/a | one crossing + one below ✓ | EFFECT ✓ | **✗ ROUTING-NOT-SHARING undetectable** | **MISSING PIN (E: WB14/PR13)** |
| `edge ≡ column` helper | every row | DERIVED ✓ | `row_count` ✓ | EFFECT ✓ | n/a | SAFE as an instrument; its FIXTURES miss the heal dedupe shape (Q2/WB5) |
| #130 status sweep | `TASK_STATUSES` | DERIVED ✓ | ✓ | EFFECT ✓ | n/a | SAFE; the `limit` path is outside its reach (WB7) |
| boot heal (∀ stragglers) | rows with `superseded_by` | DERIVED ✓ | **one blocker per row** | EFFECT ✓ | through the shell ✓ | **MISSING PINS (E: WB3/WB4/WB5/WB6)** |
| index rider EXPLAIN pin | ONE hand-typed statement | — | control TableScan ✓ | **PROXY** (not the production statements) | n/a | **NOT A DEFECT today (E: PR11 GREEN — `direct_dependents`, the R1 count, and the heal `CONTAINSANY` spellings are all index-served with the rider)**; residual: pin EXPLAINs a statement production does not run — re-key to the production strings |
| `ApplyHook` (constructed interleavings) | the verb's FIRST `_apply` | n/a | `fired` asserted ✓ (fail-closed) | EFFECT ✓ | n/a | SAFE |
| forgery door sweep (D12) | ensure_ready's store calls | DERIVED by fault injection ✓ | count pinned ✓ | EFFECT ✓ | n/a | **pins an UNRULED order; conflicts with am-2's fail-open (E: RUN1, K17, AM2L/AM2C)** |
| D9 routing pin (`test_blocks_edge`) | supersede + 1 hop of private helpers | hand-shaped (one hop) | presence only | PROXY (call-site names) | ✗ | **message over-claims (E: K16)** — "a hand-rolled RELATE in a helper still reds" is false |
Legs run: E for every row marked E; C for the sharing hand-list bound and the hub-refusal/R1 rows (also E via K12/K14).

## §SAT — satisfiability on the RIGHT base (brief focus 1), 2026-09-26 16:38–16:51Z
**Required-green builds, enumerated FIRST:** (a) 05b/#174 blocker semantics + the successor sentinel — `test_blocks_edge.py` SECTIONS incl. `TestSupersedeCarriesBlockedBy174`, `TestASupersededBlockerIsNotASilentBlackHole`, `S::TestRequiredGreen::test_the_174_*`; (b) the claim CAS — `test_task_ledger.py` race suites + `G::TestTheClaimCASStillDecidesOnlyOnce` (8-way); (c) `transitive_blockers` — `test_blocks_edge.py` F/K + `test_task_read_surface.py`; (d) the findings ledger's `_guarded_append_fragment` — `test_findings*.py` + `G::…ONEGuardedAppendProducer` (findings stays at one producer); (e) 57's future consumer shape — the shell's kw-only signature pin `G::TestTheShellIsTheSeam64aGoverns` (57 consumes it; no 57 test exists yet — stated bound). **All GREEN on my reference** (per-file in the run below; none in either red set).
**§HELD over 63c:** `git apply --check` of the 385-line §HELD (extracted verbatim, `REPORT-contract-58.md` lines 173–557) on HEAD + `b23f3e43` → clean for all 6 files; hunks DISJOINT (63c: `AppContext` agents region ~6573–6790; §HELD: the `tasks()` supersede branch + `_render_supersede_result` ~4551–4870). ⚠ Residual: §HELD also edits `test_mcp_server.py` (D7), which contract-64b's pending commit edits too (lead's D-SAT ruling) — re-run the apply-check after 64b lands.
**Trees:** REFERENCE `ref58` = `37de0a7` + 63c `b23f3e43` + §HELD + my build (`loremaster.__file__` = `…/974aab4b-…/scratchpad/ref58/loremaster/loremaster/__init__.py`); BASELINE `base58` = `17c52b7` + 63c `b23f3e43` (`…/scratchpad/base58/loremaster/loremaster/__init__.py`); code-identical bases (docs-only delta). Both `uv run pytest -n auto`, full suite, lore-scoped lane, watchdog never fired, #486 not observed (no `Resource busy`).
- REFERENCE: **`22 failed, 11743 passed, 62 skipped, 3 xfailed, 9 warnings, 2 errors in 374.92s`**
- BASELINE: **`87 failed, 11671 passed, 62 skipped, 3 xfailed, 7 warnings, 2 errors in 376.06s`**
- `comm` both ways: **REF-ONLY = 1**, BASE-ONLY = 66 (58 reds the build turns green), COMMON = 23.
**Every red on the reference, individually adjudicated (24 = 22 F + 2 E):**
| red(s) | in baseline too? | verdict |
|---|---|---|
| `test_loopback_serving.py` ERROR, `skills/…/test_loopback_home.py` ERROR, `test_no_raw_listener_in_test_trees.py` ×5, `scripts/test_gated_ground.py` ×7 (its collector subprocess sees the two collection errors → "the GUARD is blind") | yes, identical | #466 contract-ahead (`37de0a7`) — directive #17038's set, IDENTICAL in both runs ✓ |
| `test_secret_resolution_seam.py` ×2, `test_secret_typing.py` ×3 (all name `scripts/restore_prod_dump.py`), `test_anchored_pattern_seam.py` ×1 (names `scripts/concurrent_wire_acceptance.py:67` + `restore_prod_dump.py:429,735`), `test_ast_reach_helpers.py[test_anchored_pattern_seam]` ×1 | yes, identical | **NOT 58, NOT in #17038's adjudicated sets** — `restore_prod_dump.py` (probe-64, `80409f4`) trips five secret-seam invariants + the anchored-pattern seam; `concurrent_wire_acceptance.py` (#466) trips the anchored-pattern seam. **7 unrelated HEAD reds — flagged to the lead** |
| `G::TestParamNamesDoNotCollide…` | yes (as a contract-ahead red) | **58-attributable, over-tight pin** (RUN1 #1) — a set-equality SAT HIDES it, since it is red in both |
| `scripts/test_forgery_door_sweep.py::…SWALLOWS…` | yes (as a contract-ahead red) | **58-attributable, unruled-order pin** (RUN1 #2) — likewise hidden by set-equality |
| **`test_retry_seam.py::TestNoGuardedCasHandlerReinterpretsExhaustedContention::test_the_door_enumeration_matches_the_canonical_set`** | **NO — REF-ONLY** | **58-attributable, SAT DEFECT (missing DUAL row):** `doors with NO entry in the canonical set: ['tasks.py::claim_task']`. Routing claim through the THROW shell makes `claim_task` a guarded-CAS door (a rollback handler that re-reads state) — kickoff §4 prescribes exactly that ladder — and `_GUARDED_CAS_DOORS` (the #102-class registry) must gain it. The author's SAT did not see it because their reference re-reads through a HELPER (`_still_claimable`) and the enumerator only matches a re-read call written INLINE in the handler (`call.func.attr.startswith(_GUARDED_CAS_RE_READ)` over `ast.walk(handler)`) — the door exists in their build too, unenumerated. Two reach bounds in that pre-existing enumerator, recorded as residuals: helper-indirected re-reads escape; a TUPLE `except (A, B)` guard is not recognised (`isinstance(handler.type, ast.Name)`) |
**SAT verdict:** NOT 0 failed on the right base. With the reds above: **3 attributable to 58's CONTRACT** (two over-tight/unruled pins, one missing DUAL row) on an independently-written correct build; **0 attributable to the build**. The author's "set-equal to the HEAD baseline, 0 attributable failures" was measured on a DIFFERENT base (no 63c patch; 63c-i-a reds reverted) and on THEIR build — whose spelling happens to satisfy the two over-tight pins and escape the door enumerator. Set-equality did not hide anything in the AUTHOR's run (their 108 were all 63c-i-a ids), but on MY build it would hide two 58 pins that are red in both runs.

## §P7 — RED@HEAD reproduced
On `base58` (HEAD `17c52b7` + 63c, full suite): reds in the contract's files = **68** (S 44 · G 15 · P 5 · `test_blocks_edge` 1 (D10) · `test_task_read_surface` 1 (D1) · `test_forgery_door_sweep` 2 (D12)) — matches the author's 68. First exception per failure block: **36 AssertionError · 22 AttributeError · 9 `Failed: DID NOT RAISE` · 1 ImportError** (`TestTheSupersedeItselfIsUnchanged::test_the_result_is_the_typed_carrier` — `cannot import name 'SupersedeResult'`: the author's "67 classified" + this one). All right-reason (a missing 58 symbol or mechanism); none is a fixture/typo/path error.

## §P5 — can the fake fail?
`_task_fakes.FakeTaskLedger.supersede_task` (§HELD lockstep) with its ENTIRE re-anchor loop removed (`for dependent in []`) → `test_task_ledger.py`, `test_mcp_server.py`, `test_query_tasks_bounded.py`, `test_comms_footer.py`, `test_task_read_surface.py`: **`1299 passed, 1 skipped`** (`p5_fake.out`). **The fake's re-anchor/`reblocked` code CANNOT go red** — no test drives a supersede-with-dependents through the fake (the 58 files are real-only; D7 reads `.successor_id`). The author's B7 flag (no `claim` event in the fake) is the same class. MISSING PIN (low): parametrise one re-anchor pin `[fake, real]` (the house parity idiom) or drop the fake's lockstep code.

## §MISSING PINS — the test that should exist · the defect it catches · receipt · class
| id | the test that should exist | the defect it catches | receipt | class |
|---|---|---|---|---|
| MP1 | an injected NON-straggler rollback (server-side `DEFINE EVENT … THROW` on dependent k, no concurrent create) ⇒ the error is NOT the R1 teaching (no "retry", no "was created while"); supersede twin of B6's claim-loud pin | a build that serves EVERY rollback as *"a task was created while … retry"* — a false cause; an agent retries a persistent fault forever | WB1 survives; PR1 | MISSING PIN |
| MP2 | the cap accessor checked at K ∈ {0, per, per+1} (per MEASURED), or a supersede at `max_reanchor_dependents(K)` dependents for K = per that must not serve compose's bare error | a K-ignoring (cached) accessor; K ∈ {0,2} discriminates only when fixed₀ ≢ 0 (mod 3) | WB2 survives on a legit fixed₀ = 6 layout; PR2; harm PR16 (`5001 statements`) | MISSING PIN (P2 alignment) |
| MP3 | a straggler naming TWO superseded blockers from different chains ⇒ both entries rewritten to their heads, edges mirror, `count == 1` | heal rewrites only the first superseded entry; heal counts (row, blocker) pairs | WB4, WB3 survive; PR3 | MISSING PIN (Q9 small-N) |
| MP4 | a legacy straggler naming X AND its head X' ⇒ `[X']`, exactly ONE `X'→Y` edge | heal RELATEs unconditionally ⇒ doubled edge (no `UNIQUE(in,out)`) | WB5 survives; PR4 | MISSING PIN (Q2 reach) |
| MP5 | a straggler whose chain head names NO row ⇒ the boot completes, the strand is left + RECORDED (backfill's R11 phantom posture) | ENFORCED rejects the RELATE ⇒ the heal txn (or, under am-2, its chunk every boot) fails | WB6 survives; PR5 | NEW DOOR (needs ruling: skip+record vs chunk-fail) |
| MP6 | `query_tasks(status="open", limit=k)` with superseded open rows sorting FIRST ⇒ returns k genuine rows | #130 exclusion applied client-side after a `LIMIT`'d read ⇒ a short answer while more exist (T1) | WB7 survives; PR6 | MISSING PIN |
| MP7 | a `wontfix` X with one open, unowned dependent ⇒ `reblocked == [Y]` | `reblocked` keyed on `done` instead of `TERMINAL_STATUSES` | WB8 survives; PR7 (author's own door 5 residue) | MISSING PIN |
| MP8 | a dependent already on a LEGACY loop through its OTHER blocker ⇒ supersede of X succeeds (or is refused — rule it) | refusing a supersede for a cycle the rewire did not close ⇒ X can never be superseded (no verb edits `blocked_by`) | WB9 survives; PR8 | NEW DOOR (spec-silent) |
| MP9 | a RUNTIME one-producer pin: spy `compose` while driving every task verb and assert every THROW-bearing statement came from the shell's output (tagged) — or extend the AST scan to module constants flowing into a function | a 4th hand-rolled guarded append whose guard template is a module constant (and the author's door 1: split across helpers) | WB12 survives; PR9 red on EVERY build | MISSING PIN (P1c reach) |
| MP10 | silence `SurrealStore._log_transaction_size` in-suite ⇒ the task WARN pin must go quiet | a cloned threshold compare (routing-not-sharing on the WARN policy) | WB14 survives; PR13 | MISSING PIN (one-source unproven) |
| MP11 | monkeypatch `_txn.TXN_STATEMENT_HARD_CAP` ⇒ `max_reanchor_dependents` moves by exactly `Δ // per` | a literal `5000` copy (two sources of the compose cap) | WB15 survives; PR14 | MISSING PIN (one-source unproven) |
| MP12 | re-anchor note `at` ∈ [before, after] the supersede call | a stale / constant `at` | WB16 survives; PR12 | MISSING PIN (low) |
| MP13 | the supersede transaction's RELATE statements all come from `_relate_fragment` (compose spy) — or delete D9's claim *"a hand-rolled RELATE in a helper still reds"* | dependents' RELATEs hand-rolled beside the shared seam | K16 survives (`1 failed, 85 passed` — the 1 is SD1) | MISSING PIN (low) / false prose |
| MP14 | a routine claim LOSS emits no ERROR-level record (or a ruling that it may) | every lost claim now logs `store.transaction.rolled_back` at ERROR via `_txn._log_rollback` (THROW-on-loss); before 58 a loss was silent | PR10 red on my reference AND by construction on the author's (same THROW path) | NEW DOOR (needs ruling) |
| MP15 | am-2 (a): alice holds Y (superseded) and Z ⇒ `owner=alice` serves both, Y decorated; `owner=alice status=claimed` serves only Z | `owner=` also excludes superseded rows | WB18 survives the whole contract; PR20 | MISSING PIN (am-2 rider) |
| MP16 | am-2 (b): heal chunking over a MULTI-blocker population (≥ per+… distinct superseded blockers in one chunk) ⇒ all healed, `chunks` logged, second boot silent; + chunk-fault isolation | single-txn heal (fails the boot at 1300 — PR17); am-2-literal chunking (never converges — PR19) | PR17, PR18, PR19 | MISSING PIN + RULING (§AM2 #1) |
| MP17 | one re-anchor pin parametrised `[fake, real]` (the house parity idiom) | the fake's §HELD re-anchor lockstep cannot fail (removing it: `1299 passed`) | P5 | MISSING PIN (low) |
| MP18 | a legacy `superseded_by` LOOP ⇒ the boot completes in bounded time, no note appended per boot | unbounded chain-follow HANGS the boot (WB17 killed at 120 s); the author's bounded `_head` returns a LOOP MEMBER ⇒ a self-rewrite + a new note every boot (C, not run) | WB17 (`rc=137`); PR15 | NEW DOOR (low; raw-only legacy) |
**SAT DEFECTS (the contract reds a correct build):** SD1 `G::TestParamNamesDoNotCollide…` asserts `== 3` shell calls while its docstring promises `≥ N+1`; a build deriving the cap by building fragments (the ruled F-1 mechanism) is red. SD2 D12 (`scripts/test_forgery_door_sweep.py`) pins an UNRULED heal-after-backfill order (heal-first red; K17 green) and, under am-2's fail-open, contradicts the unedited FAILS_LOUD pin. SD3 `test_retry_seam.py` canonical `_GUARDED_CAS_DOORS` lacks `tasks.py::claim_task` — every build that re-reads inline in claim's rollback handler (kickoff §4's ladder) is red; the contract owes the DUAL row.

## §RESIDUALS — individual verdicts
| # | item | verdict |
|---|---|---|
| R1 | E11: the ruled `array::distinct` rewrite also collapses LEGACY duplicates of OTHER blockers | NOT A DEFECT (benign after T5; record only) |
| R2 | `scripts/esc1_write_path_cycle_closure.py` run exits 1 at HEAD (`[boundary-5] successor is born with NO dependencies`) since #174 | UNRELATED pre-existing red instrument — owner: lead |
| R3 | 7 HEAD reds from `scripts/restore_prod_dump.py` (5 secret-seam + anchored-pattern) and `scripts/concurrent_wire_acceptance.py` (anchored-pattern) — not in directive #17038's sets | UNRELATED — flagged |
| R4 | coldaudit-63c-i-a-2's lane waiter self-matched (#228) | reported #17044; lead ruled #17046 |
| R5 | `test_retry_seam._discover_guarded_cas_handlers` reach: a helper-indirected re-read escapes; a TUPLE `except (…, TxnContentionExhaustedError)` guard is not recognised | pre-existing instrument reach bound — flag (the author's claim handler is unenumerated because of the first) |
| R6 | the index-rider EXPLAIN pin observes a hand-typed statement | NOT A DEFECT today — PR11 GREEN: `direct_dependents`, the R1 count, and the heal `CONTAINSANY` spellings are all index-served; re-key to production strings |
| R7 | §HELD's `test_mcp_server.py` D7 hunk vs contract-64b's pending `test_mcp_server` edits | re-run `git apply --check` after 64b commits |
| R8 | corpse PROSE: `test_task_read_surface` failure messages ("stranded … re-point"), `MIRROR_IMMUTABLE_VERBS` comment, `tasks.py` docstrings (DEFERRED / immutable) | builder-owned prose (author's B8/FLAG 2 confirmed) |
| R9 | author's `Packages considered: none` | NOT A DEFECT (imprecise wording; §P-PKG) |
| R10 | `TaskLedger._apply` now emits `store.apply.*` DEBUG per task txn | NOT A DEFECT (B11, intentional reuse) |
| R11 | the R1 pin fixes the refusal MECHANISM (a set-based in-txn rewire would close R1 without refusing) | NOT A DEFECT — consistent with amendment 1 |
| R12 | kickoff's "a dependent already naming X'" is unreachable in supersede | author correct; the reachable twin is in the HEAL (MP4) |
| R13 | my own P0 slips, stated: the first driver lane self-matched (#228) and never freed (fixed: comm-keyed); an unquoted heredoc corrupted a queued script (rewritten before it ran); PR18's `await`-in-genexp crashed on AM2L (fixed, re-run: `1 passed`); my AM2C PR18 declaration was wrong (I had not done the 4999 arithmetic) — the observed red is itself a finding (§AM2 #1) | disclosed |

## §FOLLOWUP (2026-09-26 16:57–16:59Z, lore-scoped lane)
- PR18 (probe bug fixed: the genexp `await` replaced by a loop; md5 `cdb99104`) on **AM2L** (am-2 literal) → `1 passed` — **the ruled pin shape passes the defective sizing**; on **AM2C** (correct, heal-sized chunks) → `1 failed` (`assert 1 == 2` on `chunks`) — **the ruled pin reds the correct chunker**.
- PR15 on the reference → `1 passed in 0.63s`; on WB17 (unbounded chain-follow) → killed by `timeout -s KILL 120` (`rc=137`) — **a legacy `superseded_by` loop HANGS the boot**. No orphaned process left (checked).
- Reference `tasks.py` restored and re-verified (`9c254944…`) after every swap; the `_task_fakes.py` P5 mutation restored (`1a13f30c…` = §HELD's version).

## §INSTRUMENTS — pasted VERBATIM (brief-base §1: an instrument behind a load-bearing claim is a deliverable; nothing committed — the brief says commit nothing)
Scratch root (session-local, not durable): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/974aab4b-d082-4a22-92d0-f781857af668/scratchpad/`. To re-run: `./scripts/scratch_copy.sh <dest>` → `git checkout -- . && git clean -fd` → `git apply builder-63c-i-a-fix.patch` (md5 `b23f3e43…`) → `git apply` §HELD (`REPORT-contract-58.md` lines 173–557) → `build_ref58.py <dest>` → copy the probe files into `loremaster/tests/` → `lane58cmd.sh <dest> <log> -- bash all_runs.sh`.

### `build_ref58.py` (md5 5915c12e)
```python
#!/usr/bin/env python3
"""adversary-58's OWN packet-58 reference build — applied to a SCRATCH copy's tasks.py only.

Usage: build_ref58.py <scratch-root>
Each edit asserts its anchor occurs exactly once, so a drifted base fails loudly.
"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
src = TASKS.read_text()


def sub(old: str, new: str) -> None:
    global src
    count = src.count(old)
    assert count == 1, f"anchor found {count}x: {old[:80]!r}"
    src = src.replace(old, new)


# --- imports ------------------------------------------------------------------
sub(
    "from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE, generate_task_ddl\n",
    "from loremaster.store import _txn as _txn_module\n"
    "from loremaster.store.surreal import SurrealStore\n"
    "from loremaster.store.surreal_schema import BLOCKS_RELATION, TASK_TABLE, generate_task_ddl\n",
)

# --- constants ------------------------------------------------------------------
sub(
    '_ACTION_SUPERSEDE = "supersede"\n',
    '_ACTION_SUPERSEDE = "supersede"\n'
    '_ACTION_REANCHORED = "dependency_reanchored"\n'
    '_ACTION_CLAIM = "claim"\n'
    '_PROV_FROM = "from"\n'
    '_PROV_REASON = "reason"\n'
    '_HEAL_ACTOR = "boot-heal"\n'
    '_HEAL_REASON = "straggler"\n'
    '_HEAL_EVENT = "task.backfill.stragglers_reanchored"\n'
    '_HEAL_SKIPPED_EVENT = "task.backfill.straggler_skipped"\n'
    '_REANCHOR_LOST_MESSAGE = "a dependent no longer names the superseded task"\n'
    '_STRAGGLER_MESSAGE = "a dependent of the superseded task appeared after the dependents read"\n'
    '_CLAIM_LOST_MESSAGE = "task claim lost its compare-and-set"\n',
)

# --- models / errors ------------------------------------------------------------
sub(
    "class TransitiveBlockers(BaseModel):\n",
    '''class SupersedeResult(BaseModel):
    """What :meth:`TaskLedger.supersede_task` returns (packet 58)."""

    model_config = ConfigDict(extra="forbid")

    successor_id: str
    reanchored: list[str] = Field(default_factory=list)
    reblocked: list[str] = Field(default_factory=list)


class SupersedeStragglerError(TaskLedgerError):
    """A dependent of the superseded task appeared after the dependents read (R1)."""


class HubSupersedeRefusedError(TaskLedgerError):
    """A supersede whose re-anchor would exceed the derived transaction bound (F-1)."""


class TransitiveBlockers(BaseModel):
''',
)

# --- #130 candidate statement -----------------------------------------------------
sub(
    '''    def _candidate_statement(
        *, status: str | None, owner: str | None, limit: int | None
    ) -> tuple[str, dict[str, Any]]:''',
    '''    def _candidate_statement(
        *, status: str | None, owner: str | None, limit: int | None,
        exclude_superseded: bool = False,
    ) -> tuple[str, dict[str, Any]]:''',
)
sub(
    '''        if owner is not None:
            clauses.append(f"{_COL_OWNER} = ${_QUERY_OWNER_PARAM}")
            params[_QUERY_OWNER_PARAM] = owner
        statement = f"SELECT * FROM {TASK_TABLE}"''',
    '''        if owner is not None:
            clauses.append(f"{_COL_OWNER} = ${_QUERY_OWNER_PARAM}")
            params[_QUERY_OWNER_PARAM] = owner
        if exclude_superseded or status is not None:
            clauses.append(f"{_COL_SUPERSEDED_BY} IS NONE")
        statement = f"SELECT * FROM {TASK_TABLE}"''',
)
sub(
    '''        statement, params = self._candidate_statement(
            status=status, owner=owner, limit=None if blocked is not None else cap
        )''',
    '''        statement, params = self._candidate_statement(
            status=status, owner=owner, limit=None if blocked is not None else cap,
            exclude_superseded=blocked is not None,
        )''',
)

# --- _apply: WARN through the ONE telemetry policy ---------------------------------
sub(
    '''        statement_text, merged_params = compose(*fragments)
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- create / read''',
    '''        statement_text, merged_params = compose(*fragments)
        SurrealStore._log_transaction_size(
            sum(len(fragment.statements) for fragment in fragments), len(merged_params)
        )
        await execute_transaction(
            statement_text,
            merged_params,
            acquire=self._ensure_connection,
            drop=self._drop_connection,
            url=self._url,
        )

    # -- create / read''',
)

# --- ensure_ready: the boot heal ---------------------------------------------------
sub(
    '''        logger.debug("task.schema.ready", extra={"database": self._database})
        await self._backfill_blocks_edges()
''',
    '''        logger.debug("task.schema.ready", extra={"database": self._database})
        await self._reanchor_stragglers()
        await self._backfill_blocks_edges()
''',
)

# --- claim: through the shell, CAS on the current column, loud on inexplicable rollback --
sub(
    '''        await self._apply([self._claim_fragment(task_id, owner, blocked_by)])

        # The winner''',
    '''        event = {
            _PROV_ACTOR: owner,
            _PROV_ACTION: _ACTION_CLAIM,
            _PROV_AT: datetime.now(UTC).isoformat(),
        }
        try:
            await self._apply([self._claim_fragment(task_id, owner, blocked_by, event)])
        except SurrealConnectionError:
            raise
        except TxnContentionExhaustedError:
            raise
        except SurrealStoreError:
            fresh = await self._select_row(task_id)
            if fresh is None:
                raise
            if await self._still_claimable(fresh, blocked_by):
                raise

        # The winner''',
)
sub(
    '''    @staticmethod
    def _claim_fragment(task_id: str, owner: str, blocked_by: list[str]) -> TxnFragment:''',
    '''    async def _still_claimable(self, row: Mapping[str, Any], pre_read: list[str]) -> bool:
        """Whether ``row`` would STILL pass the claim CAS — a rollback on such a row is inexplicable."""
        if str(row.get(_COL_STATUS)) != STATUS_OPEN or row.get(_COL_OWNER) is not None:
            return False
        if row.get(_COL_SUPERSEDED_BY) is not None:
            return False
        current = [str(b) for b in (row.get(_COL_BLOCKED_BY) or ())]
        if current != pre_read:
            return False
        distinct = list(dict.fromkeys(current))
        if not distinct:
            return True
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_STATUS} FROM {TASK_TABLE} "
                f"WHERE record::id({_ID_KEY}) IN $sc_ids",
                {"sc_ids": distinct},
            )
        )
        resolved = {str(r.get(_ID_KEY)) for r in rows if str(r.get(_COL_STATUS)) in TERMINAL_STATUSES}
        return resolved == set(distinct)

    @staticmethod
    def _claim_fragment(
        task_id: str, owner: str, blocked_by: list[str], event: dict[str, Any] | None = None
    ) -> TxnFragment:''',
)
sub(
    '''        guarded_claim = (
            f"UPDATE type::record('{TASK_TABLE}', ${_CLAIM_ID_PARAM}) SET "
            f"{_COL_OWNER} = ${_CLAIM_OWNER_PARAM}, "
            f"{_COL_STATUS} = ${_CLAIM_CLAIMED_PARAM}, "
            f"{_COL_CLAIMED_AT} = time::now(), "
            f"{_COL_UPDATED_AT} = time::now() "
            f"WHERE {_COL_STATUS} = ${_CLAIM_OPEN_PARAM} "
            f"AND {_COL_OWNER} IS NONE "
            f"AND {_COL_SUPERSEDED_BY} IS NONE "
            f"AND array::len(array::distinct({_COL_BLOCKED_BY})) = "
            f"array::len(${_CLAIM_RESOLVED_VAR})"
        )
        return TxnFragment(
            statements=[resolve_blockers, guarded_claim],
            params={
                _CLAIM_ID_PARAM: task_id,
                _CLAIM_OWNER_PARAM: owner,''',
    '''        return TaskLedger._guarded_append_fragment(
            task_id,
            event=event,
            preamble=[resolve_blockers],
            set_parts=[
                f"{_COL_OWNER} = ${_CLAIM_OWNER_PARAM}",
                f"{_COL_STATUS} = ${_CLAIM_CLAIMED_PARAM}",
                f"{_COL_CLAIMED_AT} = time::now()",
            ],
            where_conjuncts=[
                f"{_COL_STATUS} = ${_CLAIM_OPEN_PARAM}",
                f"{_COL_OWNER} IS NONE",
                f"{_COL_SUPERSEDED_BY} IS NONE",
                f"{_COL_BLOCKED_BY} = ${_CLAIM_BLOCKED_BY_PARAM}",
                f"array::len(array::distinct({_COL_BLOCKED_BY})) = array::len(${_CLAIM_RESOLVED_VAR})",
            ],
            throw_message=_CLAIM_LOST_MESSAGE,
            namespace="clmg",
            params={
                _CLAIM_OWNER_PARAM: owner,''',
)

# --- transition through the shell ----------------------------------------------------
sub(
    '''        set_parts = [
            f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}",
            f"{_COL_UPDATED_AT} = time::now()",
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_TRANSITION_EVENT_PARAM}]",
        ]
        params: dict[str, Any] = {
            _TRANSITION_ID_PARAM: task_id,
            _TRANSITION_STATUS_PARAM: target,
            _TRANSITION_EVENT_PARAM: event,
            _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
        }''',
    '''        set_parts = [f"{_COL_STATUS} = ${_TRANSITION_STATUS_PARAM}"]
        params: dict[str, Any] = {
            _TRANSITION_STATUS_PARAM: target,
            _TRANSITION_EXPECTED_FROM_PARAM: expected_from,
        }''',
)
sub(
    '''        guarded_transition = (
            f"LET ${_TRANSITION_UPDATED_VAR} = (UPDATE "
            f"type::record('{TASK_TABLE}', ${_TRANSITION_ID_PARAM}) SET "
            f"{', '.join(set_parts)} "
            f"WHERE {_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM} "
            f"AND {_COL_SUPERSEDED_BY} IS NONE)"
        )
        guard_updated = (
            f"IF array::len(${_TRANSITION_UPDATED_VAR}) == 0 "
            f"{{ THROW '{_TRANSITION_ALREADY_MESSAGE}' }}"
        )
        return TxnFragment(statements=[guarded_transition, guard_updated], params=params)''',
    '''        return TaskLedger._guarded_append_fragment(
            task_id,
            event=event,
            set_parts=set_parts,
            params=params,
            where_conjuncts=[
                f"{_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}",
                f"{_COL_SUPERSEDED_BY} IS NONE",
            ],
            throw_message=_TRANSITION_ALREADY_MESSAGE,
            namespace="trg",
        )''',
)

# --- supersede_task ------------------------------------------------------------------
sub(
    '''        blocked_by: list[str] | None = None,
    ) -> str:
        """Reframe a task: create a fresh open successor, stamp the old row.''',
    '''        blocked_by: list[str] | None = None,
    ) -> SupersedeResult:
        """Reframe a task: create a fresh open successor, stamp the old row.''',
)
sub(
    '''        await self._reject_unusable_blockers([(entry, entry) for entry in dependencies])
        await self._refuse_a_cycle({new_id: dependencies})

        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, dependencies, created_by, now)
        event = {
            _PROV_ACTOR: created_by,
            _PROV_ACTION: _ACTION_SUPERSEDE,
            _PROV_SUCCESSOR: new_id,
            _PROV_AT: now.isoformat(),
        }
        try:''',
    '''        await self._reject_unusable_blockers([(entry, entry) for entry in dependencies])
        dependent_rows = await self._dependent_rows(task_id)
        dependent_ids = sorted(dependent_rows)
        cap = self.max_reanchor_dependents(len(dependencies))
        if len(dependent_ids) > cap:
            raise HubSupersedeRefusedError(
                f"task {render_attributed(task_id)} has {len(dependent_ids)} dependents; one "
                f"supersede re-anchors at most {cap} dependents (the store's transaction bound, "
                f"derived) — refused, nothing changed. This is a pinned KNOWN BOUND (58 F-1); a hub "
                f"this size is not expected in the fleet — file it; this refusal is the bound's "
                f"re-open trigger"
            )
        rewired = {
            dependent: list(
                dict.fromkeys(new_id if entry == task_id else entry for entry in columns)
            )
            for dependent, (columns, _row) in dependent_rows.items()
        }
        await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})
        reblocked = await self._reblocked(row, dependent_rows, task_id)

        now = datetime.now(UTC)
        content = self._new_task_content(subject, description, dependencies, created_by, now)
        event = {
            _PROV_ACTOR: created_by,
            _PROV_ACTION: _ACTION_SUPERSEDE,
            _PROV_SUCCESSOR: new_id,
            _PROV_AT: now.isoformat(),
        }
        try:''',
)
sub(
    '''            await self._apply(
                [
                    self._supersede_fragment(task_id, new_id, content, event),
                    self._relate_fragment(
                        [(blocker, new_id) for blocker in dependencies]
                    ),
                ]
            )
        except SurrealConnectionError:''',
    '''            await self._apply(
                self._supersede_transaction(
                    task_id, new_id, content, event, dependencies, dependent_ids,
                    actor=created_by, at=now.isoformat(),
                )
            )
        except SurrealConnectionError:''',
)
sub(
    '''            settled = await self._select_row(task_id)
            if settled is not None and settled.get(_COL_SUPERSEDED_BY) is not None:
                raise IllegalTransitionError(
                    f"task {render_attributed(task_id)} is already superseded by "
                    f"{settled.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
                ) from error
            raise
        return new_id''',
    '''            settled = await self._select_row(task_id)
            if settled is not None and settled.get(_COL_SUPERSEDED_BY) is not None:
                raise IllegalTransitionError(
                    f"task {render_attributed(task_id)} is already superseded by "
                    f"{settled.get(_COL_SUPERSEDED_BY)!r} and cannot be superseded again"
                ) from error
            if sorted(await self.direct_dependents(task_id)) != dependent_ids:
                raise SupersedeStragglerError(
                    f"a task blocked on {render_attributed(task_id)} was created while this "
                    f"supersede was being prepared — nothing changed; retry the supersede"
                ) from error
            raise
        return SupersedeResult(
            successor_id=new_id, reanchored=dependent_ids, reblocked=sorted(reblocked)
        )

    async def _dependent_rows(
        self, task_id: str
    ) -> dict[str, tuple[list[str], dict[str, Any]]]:
        """Every row whose ``blocked_by`` names ``task_id``: id -> (column, row)."""
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY}, {_COL_STATUS}, "
                f"{_COL_OWNER}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINS $dr_id",
                {"dr_id": task_id},
            )
        )
        return {
            str(r.get(_ID_KEY)): ([str(b) for b in (r.get(_COL_BLOCKED_BY) or ())], r)
            for r in rows
        }

    async def _reblocked(
        self,
        predecessor: Mapping[str, Any],
        dependent_rows: Mapping[str, tuple[list[str], dict[str, Any]]],
        task_id: str,
    ) -> list[str]:
        """The dependents that were CLAIMABLE before (amendment 1 FORK-A rider), pre-write."""
        if str(predecessor.get(_COL_STATUS)) not in TERMINAL_STATUSES:
            return []
        others = sorted(
            {b for columns, _row in dependent_rows.values() for b in columns if b != task_id}
        )
        status_by_id: dict[str, str] = {}
        if others:
            rows = self._as_rows(
                await self._query(
                    f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_STATUS} FROM {TASK_TABLE} "
                    f"WHERE record::id({_ID_KEY}) IN $rb_ids",
                    {"rb_ids": others},
                )
            )
            status_by_id = {str(r.get(_ID_KEY)): str(r.get(_COL_STATUS)) for r in rows}
        out = []
        for dependent, (columns, row) in dependent_rows.items():
            if str(row.get(_COL_STATUS)) != STATUS_OPEN or row.get(_COL_OWNER) is not None:
                continue
            if row.get(_COL_SUPERSEDED_BY) is not None:
                continue
            if all(
                status_by_id.get(b) in TERMINAL_STATUSES for b in columns if b != task_id
            ):
                out.append(dependent)
        return out

    def max_reanchor_dependents(self, successor_blocked_by_count: int) -> int:
        """The most dependents ONE supersede can re-anchor — DERIVED from the builder's counts."""
        deps = [f"k{index}" for index in range(successor_blocked_by_count)]
        now = datetime.now(UTC).isoformat()

        def _count(n: int) -> int:
            fragments = self._supersede_transaction(
                "x", "y", {}, {}, deps, [f"d{index}" for index in range(n)], actor="a", at=now
            )
            return sum(len(fragment.statements) for fragment in fragments)

        fixed = _count(0)
        per = _count(1) - fixed
        return (_txn_module.TXN_STATEMENT_HARD_CAP - fixed) // per

    @staticmethod
    def _reanchor_fragments(
        pairs: Sequence[tuple[str, str, str]],
        *,
        actor: str,
        at: str,
        reason: str | None = None,
        prefix: str = "ra",
    ) -> list[TxnFragment]:
        """Rewrite each ``(dependent, old, new)`` through the ONE shell, with its note."""
        fragments = []
        for index, (dependent, old, new) in enumerate(pairs):
            old_param = f"{prefix}{index}_old"
            new_param = f"{prefix}{index}_new"
            note: dict[str, Any] = {
                _PROV_ACTOR: actor,
                _PROV_ACTION: _ACTION_REANCHORED,
                _PROV_FROM: old,
                _PROV_TO: new,
                _PROV_AT: at,
            }
            if reason is not None:
                note[_PROV_REASON] = reason
            fragments.append(
                TaskLedger._guarded_append_fragment(
                    dependent,
                    event=note,
                    set_parts=[
                        f"{_COL_BLOCKED_BY} = array::distinct(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END))"
                    ],
                    params={old_param: old, new_param: new},
                    where_conjuncts=[f"{_COL_BLOCKED_BY} CONTAINS ${old_param}"],
                    throw_message=_REANCHOR_LOST_MESSAGE,
                    namespace=f"{prefix}{index}g",
                )
            )
        return fragments

    @staticmethod
    def _supersede_transaction(
        old_id: str,
        new_id: str,
        content: dict[str, Any],
        event: dict[str, Any],
        dependencies: Sequence[str],
        dependents: Sequence[str],
        *,
        actor: str,
        at: str,
    ) -> list[TxnFragment]:
        """The WHOLE supersede: stamp, CREATE, retire X's edges, re-anchor, relate, close."""
        fragments = [TaskLedger._supersede_fragment(old_id, new_id, content, event)]
        fragments.append(
            TxnFragment(
                statements=[f"DELETE {BLOCKS_RELATION} WHERE in = $ssx_old_rec"],
                params={"ssx_old_rec": RecordID(TASK_TABLE, old_id), "ssx_old": old_id},
            )
        )
        fragments.extend(
            TaskLedger._reanchor_fragments(
                [(dependent, old_id, new_id) for dependent in dependents], actor=actor, at=at
            )
        )
        fragments.append(
            TaskLedger._relate_fragment(
                [(blocker, new_id) for blocker in dependencies]
                + [(new_id, dependent) for dependent in dependents]
            )
        )
        fragments.append(
            TxnFragment(
                statements=[
                    f"IF (SELECT count() FROM {TASK_TABLE} WHERE {_COL_BLOCKED_BY} CONTAINS "
                    f"$ssx_old GROUP ALL)[0].count > 0 {{ THROW '{_STRAGGLER_MESSAGE}' }}"
                ],
                params={},
            )
        )
        return fragments

    @staticmethod
    def _guarded_append_fragment(
        row_id: str,
        *,
        event: Mapping[str, Any] | None,
        set_parts: Sequence[str] = (),
        params: Mapping[str, Any],
        where_conjuncts: Sequence[str] = (),
        preamble: Sequence[str] = (),
        throw_message: str,
        namespace: str | None = None,
    ) -> TxnFragment:
        """THE task-side guarded-append shell (packet 58): guarded UPDATE + THROW on zero rows."""
        space = namespace or f"ga{uuid4().hex[:12]}"
        id_param = f"{space}_id"
        event_param = f"{space}_ev"
        result_var = f"{space}_upd"
        merged: dict[str, Any] = {**params, id_param: row_id}
        sets = [*set_parts, f"{_COL_UPDATED_AT} = time::now()"]
        if event is not None:
            sets.append(f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${event_param}]")
            merged[event_param] = dict(event)
        update = f"UPDATE type::record('{TASK_TABLE}', ${id_param}) SET {', '.join(sets)}"
        if where_conjuncts:
            update = f"{update} WHERE " + " AND ".join(f"({c})" for c in where_conjuncts)
        return TxnFragment(
            statements=[
                *preamble,
                f"LET ${result_var} = ({update})",
                f"IF array::len(${result_var}) == 0 {{ THROW '{throw_message}' }}",
            ],
            params=merged,
        )

    async def _reanchor_stragglers(self) -> None:
        """Boot heal (amendment 1 R2): re-anchor every row still naming a superseded task."""
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE"
            )
        )
        successor = {str(r.get(_ID_KEY)): str(r.get(_COL_SUPERSEDED_BY)) for r in rows}
        if not successor:
            return
        stragglers = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINSANY $hs_ids",
                {"hs_ids": sorted(successor)},
            )
        )
        existing = await resolve_existing_rows(
            self._query, TASK_TABLE, sorted(set(successor.values()))
        )

        def _head(start: str) -> str | None:
            seen = {start}
            current = successor[start]
            while current in successor:
                if current in seen:
                    return None
                seen.add(current)
                current = successor[current]
            return current if current in existing else None

        pairs: list[tuple[str, str, str]] = []
        deletes: list[tuple[str, str]] = []
        relates: list[tuple[str, str]] = []
        healed: set[str] = set()
        for straggler in stragglers:
            dependent = str(straggler.get(_ID_KEY))
            columns = [str(b) for b in (straggler.get(_COL_BLOCKED_BY) or ())]
            final = list(columns)
            for old in dict.fromkeys(b for b in columns if b in successor):
                head = _head(old)
                if head is None:
                    logger.warning(
                        _HEAL_SKIPPED_EVENT,
                        extra={"database": self._database, "task_id": dependent, "blocker": old},
                    )
                    continue
                pairs.append((dependent, old, head))
                deletes.append((old, dependent))
                if head not in final:
                    relates.append((head, dependent))
                final = list(dict.fromkeys(head if b == old else b for b in final))
                healed.add(dependent)
        if not pairs:
            return
        fragments = [
            TxnFragment(
                statements=[
                    f"DELETE {BLOCKS_RELATION} WHERE in = $hd{index}_in AND out = $hd{index}_out"
                    for index in range(len(deletes))
                ],
                params={
                    key: value
                    for index, (blocker, dependent) in enumerate(deletes)
                    for key, value in (
                        (f"hd{index}_in", RecordID(TASK_TABLE, blocker)),
                        (f"hd{index}_out", RecordID(TASK_TABLE, dependent)),
                    )
                },
            ),
            *self._reanchor_fragments(
                pairs, actor=_HEAL_ACTOR, at=datetime.now(UTC).isoformat(),
                reason=_HEAL_REASON, prefix="hr",
            ),
            self._relate_fragment(relates),
        ]
        await self._apply([fragment for fragment in fragments if fragment.statements])
        logger.info(_HEAL_EVENT, extra={"database": self._database, "count": len(healed)})''',
)

# --- supersede stamp through the shell -------------------------------------------------
sub(
    '''        stamp_old = (
            f"LET ${_SUPERSEDE_STAMPED_VAR} = (UPDATE "
            f"type::record('{TASK_TABLE}', ${_SUPERSEDE_OLD_ID_PARAM}) SET "
            f"{_COL_SUPERSEDED_BY} = ${_SUPERSEDE_NEW_ID_PARAM}, "
            f"{_COL_UPDATED_AT} = time::now(), "
            f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [${_SUPERSEDE_EVENT_PARAM}] "
            f"WHERE {_COL_SUPERSEDED_BY} IS NONE)"
        )
        guard_stamped = (
            f"IF array::len(${_SUPERSEDE_STAMPED_VAR}) == 0 "
            f"{{ THROW '{_SUPERSEDE_ALREADY_MESSAGE}' }}"
        )
        create_successor = (
            f"CREATE type::record('{TASK_TABLE}', ${_SUPERSEDE_NEW_ID_PARAM}) "
            f"CONTENT ${_SUPERSEDE_CONTENT_PARAM}"
        )
        return TxnFragment(
            statements=[stamp_old, guard_stamped, create_successor],
            params={
                _SUPERSEDE_NEW_ID_PARAM: new_id,
                _SUPERSEDE_CONTENT_PARAM: content,
                _SUPERSEDE_OLD_ID_PARAM: old_id,
                _SUPERSEDE_EVENT_PARAM: event,
            },
        )''',
    '''        stamp = TaskLedger._guarded_append_fragment(
            old_id,
            event=event,
            set_parts=[f"{_COL_SUPERSEDED_BY} = ${_SUPERSEDE_NEW_ID_PARAM}"],
            params={_SUPERSEDE_NEW_ID_PARAM: new_id, _SUPERSEDE_CONTENT_PARAM: content},
            where_conjuncts=[f"{_COL_SUPERSEDED_BY} IS NONE"],
            throw_message=_SUPERSEDE_ALREADY_MESSAGE,
            namespace="supg",
        )
        create_successor = (
            f"CREATE type::record('{TASK_TABLE}', ${_SUPERSEDE_NEW_ID_PARAM}) "
            f"CONTENT ${_SUPERSEDE_CONTENT_PARAM}"
        )
        return TxnFragment(
            statements=[*stamp.statements, create_successor], params=stamp.params
        )''',
)

# --- _refuse_a_cycle: minted override ---------------------------------------------------
sub(
    '''    async def _refuse_a_cycle(self, pending: Mapping[str, Sequence[str]]) -> None:''',
    '''    async def _refuse_a_cycle(
        self, pending: Mapping[str, Sequence[str]], *, minted: set[str] | None = None
    ) -> None:''',
)
sub(
    '''        for task_id, blockers in pending.items():
            graph[task_id] = set(blockers)
        minted = set(pending)''',
    '''        for task_id, blockers in pending.items():
            graph[task_id] = set(blockers)
        minted = set(pending) if minted is None else minted''',
)

TASKS.write_text(src)
print("ref58 build applied:", TASKS)
```

### `wrong_builds.py` (md5 790e0309)
```python
#!/usr/bin/env python3
"""adversary-58 WRONG BUILDS — each is a set of exact substitutions over the reference tasks.py.

Usage: wrong_builds.py <name> <reference tasks.py> <out tasks.py>     |  wrong_builds.py --list
Every anchor must occur exactly once in the reference (a drifted anchor is a loud failure, never a
silent no-op — the "mutation must LAND" rule, #194).
"""
import sys
from pathlib import Path

HEAL_LOOP_GUARD = "                if current in seen:\n                    return None\n"

BUILDS: dict[str, list[tuple[str, str]]] = {
    # ---- doors (expected to SURVIVE the contract) -------------------------------------------
    "WB1_launder_any_rollback_as_R1": [
        ("            if sorted(await self.direct_dependents(task_id)) != dependent_ids:\n",
         "            if True:  # WB1: every non-lost-race rollback served as the R1 teaching\n"),
    ],
    "WB2a_legit_two_statement_R1_guard": [
        ('''                statements=[
                    f"IF (SELECT count() FROM {TASK_TABLE} WHERE {_COL_BLOCKED_BY} CONTAINS "
                    f"$ssx_old GROUP ALL)[0].count > 0 {{ THROW '{_STRAGGLER_MESSAGE}' }}"
                ],''',
         '''                statements=[
                    f"LET $ssx_n = (SELECT count() FROM {TASK_TABLE} WHERE {_COL_BLOCKED_BY} "
                    f"CONTAINS $ssx_old GROUP ALL)",
                    f"IF $ssx_n[0].count > 0 {{ THROW '{_STRAGGLER_MESSAGE}' }}",
                ],'''),
    ],
    "WB3_heal_counts_pairs": [
        ('extra={"database": self._database, "count": len(healed)}',
         'extra={"database": self._database, "count": len(pairs)}'),
    ],
    "WB4_heal_first_blocker_only": [
        ("                healed.add(dependent)\n",
         "                healed.add(dependent)\n                break\n"),
    ],
    "WB5_heal_relate_without_dedupe": [
        ("                if head not in final:\n                    relates.append((head, dependent))\n",
         "                if True:\n                    relates.append((head, dependent))\n"),
    ],
    "WB6_heal_no_phantom_head_check": [
        ("            return current if current in existing else None\n",
         "            return current\n"),
    ],
    "WB7_130_client_side_postfilter": [
        ("        if exclude_superseded or status is not None:\n",
         "        if exclude_superseded:\n"),
        ("        candidates = [self._row_to_task(row) for row in self._as_rows(payloads[0] if payloads else [])]\n",
         "        candidates = [self._row_to_task(row) for row in self._as_rows(payloads[0] if payloads else [])]\n"
         "        if status is not None:\n"
         "            candidates = [t for t in candidates if t.superseded_by is None]\n"),
    ],
    "WB8_reblocked_done_only": [
        ("        if str(predecessor.get(_COL_STATUS)) not in TERMINAL_STATUSES:\n",
         "        if str(predecessor.get(_COL_STATUS)) != STATUS_DONE:\n"),
    ],
    "WB9_cycle_minted_all_pending": [
        ("        await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})\n",
         "        await self._refuse_a_cycle({new_id: dependencies, **rewired})\n"),
    ],
    "WB12_fourth_clone_module_level_guard": [
        ('_CLAIM_LOST_MESSAGE = "task claim lost its compare-and-set"\n',
         '_CLAIM_LOST_MESSAGE = "task claim lost its compare-and-set"\n'
         '_ASSIGN_GUARD_FMT = "IF array::len(${var}) == 0 {{ THROW \'{msg}\' }}"\n'),
        ("    async def _reanchor_stragglers(self) -> None:\n",
         '''    @staticmethod
    def _assign_fragment(task_id: str, owner: str) -> TxnFragment:
        """WB12: a 57-shaped 4th hand-rolled guarded append whose guard lives in a module constant."""
        return TxnFragment(
            statements=[
                f"LET $asg_upd = (UPDATE type::record('{TASK_TABLE}', $asg_id) SET owner = $asg_owner, "
                f"{_COL_PROVENANCE}.{_PROV_EVENTS} += [$asg_ev])",
                _ASSIGN_GUARD_FMT.format(var="asg_upd", msg="assign lost"),
            ],
            params={"asg_id": task_id, "asg_owner": owner, "asg_ev": {}},
        )

    async def _reanchor_stragglers(self) -> None:
'''),
    ],
    "WB14_warn_threshold_cloned": [
        ('''        SurrealStore._log_transaction_size(
            sum(len(fragment.statements) for fragment in fragments), len(merged_params)
        )''',
         '''        statement_count = sum(len(fragment.statements) for fragment in fragments)
        if statement_count > _txn_module.TXN_STATEMENT_WARN_THRESHOLD:
            logger.warning("task.apply.large_transaction", extra={"statement_count": statement_count})'''),
    ],
    "WB15_literal_hard_cap_copy": [
        ("        return (_txn_module.TXN_STATEMENT_HARD_CAP - fixed) // per\n",
         "        return (5000 - fixed) // per\n"),
    ],
    "WB16_note_at_constant": [
        ("                _PROV_AT: at,\n            }\n            if reason is not None:",
         '                _PROV_AT: "2000-01-01T00:00:00+00:00",\n            }\n            if reason is not None:'),
    ],
    "WB17_heal_unbounded_chain_follow": [
        (HEAL_LOOP_GUARD, ""),
    ],
    # ---- the brief's list / the author's M-claims (expected to be KILLED) ------------------------
    "K1_reanchor_outside_the_supersede_txn": [
        ('''            await self._apply(
                self._supersede_transaction(
                    task_id, new_id, content, event, dependencies, dependent_ids,
                    actor=created_by, at=now.isoformat(),
                )
            )''',
         '''            _all = self._supersede_transaction(
                task_id, new_id, content, event, dependencies, dependent_ids,
                actor=created_by, at=now.isoformat(),
            )
            await self._apply(_all[:2])
            await self._apply(_all[2:])'''),
    ],
    "K2_skip_terminal_dependents": [
        ('''        return {
            str(r.get(_ID_KEY)): ([str(b) for b in (r.get(_COL_BLOCKED_BY) or ())], r)
            for r in rows
        }''',
         '''        return {
            str(r.get(_ID_KEY)): ([str(b) for b in (r.get(_COL_BLOCKED_BY) or ())], r)
            for r in rows
            if str(r.get(_COL_STATUS)) not in TERMINAL_STATUSES
        }'''),
    ],
    "K3_literal_cap": [
        ("        return (_txn_module.TXN_STATEMENT_HARD_CAP - fixed) // per\n",
         "        return 1665\n"),
    ],
    "K4_cycle_over_unrewired_graph": [
        ("        await self._refuse_a_cycle({new_id: dependencies, **rewired}, minted={new_id})\n",
         "        await self._refuse_a_cycle({new_id: dependencies})\n"),
    ],
    "K5_no_dedupe_in_rewrite": [
        ('''                        f"{_COL_BLOCKED_BY} = array::distinct(array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END))"''',
         '''                        f"{_COL_BLOCKED_BY} = array::map({_COL_BLOCKED_BY}, "
                        f"|$b| IF $b = ${old_param} THEN ${new_param} ELSE $b END)"'''),
    ],
    "K6_note_actor_missourced": [
        ("                _PROV_ACTOR: actor,\n                _PROV_ACTION: _ACTION_REANCHORED,\n",
         '                _PROV_ACTOR: "system",\n                _PROV_ACTION: _ACTION_REANCHORED,\n'),
    ],
    "K7_reanchor_private_clone_not_shell": [
        ('''            fragments.append(
                TaskLedger._guarded_append_fragment(
                    dependent,
                    event=note,''',
         '''            fragments.append(
                TaskLedger._private_reanchor(
                    dependent,
                    event=note,'''),
        ("    async def _reanchor_stragglers(self) -> None:\n",
         '''    @staticmethod
    def _private_reanchor(row_id: str, *, event: Any, set_parts: Any, params: Any,
                          where_conjuncts: Any, throw_message: str, namespace: str) -> TxnFragment:
        """K7: routing-not-sharing — a private guarded append for the re-anchor."""
        merged = {**params, f"{namespace}_id": row_id, f"{namespace}_ev": dict(event)}
        return TxnFragment(
            statements=[
                f"LET ${namespace}_upd = (UPDATE type::record('{TASK_TABLE}', ${namespace}_id) SET "
                f"{', '.join(set_parts)}, updated_at = time::now(), provenance.events += [${namespace}_ev] "
                f"WHERE " + " AND ".join(f"({c})" for c in where_conjuncts) + ")",
                f"IF array::len(${namespace}_upd) == 0 {{ THROW '{throw_message}' }}",
            ],
            params=merged,
        )

    async def _reanchor_stragglers(self) -> None:
'''),
    ],
    "K8_130_partition_unchanged": [
        ("        if exclude_superseded or status is not None:\n",
         "        if False:\n"),
    ],
    "K9_heal_logs_every_boot": [
        ("        if not pairs:\n            return\n        fragments = [",
         '        if not pairs:\n            logger.info(_HEAL_EVENT, extra={"database": self._database, "count": 0})\n'
         "            return\n        fragments = ["),
    ],
    "K10_heal_stops_at_first_hop": [
        ("            current = successor[start]\n            while current in successor:\n",
         "            current = successor[start]\n            while False:\n"),
    ],
    "K11_heal_counts_chains": [
        ('extra={"database": self._database, "count": len(healed)}',
         'extra={"database": self._database, "count": len({h for _d, _o, h in pairs})}'),
    ],
    "K12_R1_auto_retry": [
        ('''                raise SupersedeStragglerError(
                    f"a task blocked on {render_attributed(task_id)} was created while this "''',
         '''                return await self.supersede_task(
                    task_id, subject=subject, description=description, created_by=created_by,
                    blocked_by=blocked_by,
                )
                raise SupersedeStragglerError(
                    f"a task blocked on {render_attributed(task_id)} was created while this "'''),
    ],
    "K13_reblocked_ignores_other_blockers": [
        ('''            if all(
                status_by_id.get(b) in TERMINAL_STATUSES for b in columns if b != task_id
            ):''',
         '''            if True:'''),
    ],
    "K14_no_R1_closing_guard": [
        ('''        fragments.append(
            TxnFragment(
                statements=[
                    f"IF (SELECT count() FROM {TASK_TABLE} WHERE {_COL_BLOCKED_BY} CONTAINS "
                    f"$ssx_old GROUP ALL)[0].count > 0 {{ THROW '{_STRAGGLER_MESSAGE}' }}"
                ],
                params={},
            )
        )
        return fragments''',
         "        return fragments"),
    ],
    "K15_claim_cas_on_stale_preread": [
        ('''                f"{_COL_BLOCKED_BY} = ${_CLAIM_BLOCKED_BY_PARAM}",\n''', ""),
    ],
}
# WB2 = the legit layout + an accessor that ignores K (cached at K=0).
BUILDS["WB2_cap_ignores_K_on_the_legit_layout"] = [
    *BUILDS["WB2a_legit_two_statement_R1_guard"],
    ('        deps = [f"k{index}" for index in range(successor_blocked_by_count)]\n',
     "        deps: list[str] = []  # WB2: K ignored\n"),
]

BUILDS["K16_dependent_relates_hand_rolled"] = [
    ("""        fragments.append(
            TaskLedger._relate_fragment(
                [(blocker, new_id) for blocker in dependencies]
                + [(new_id, dependent) for dependent in dependents]
            )
        )""",
     """        fragments.append(TaskLedger._relate_fragment([(blocker, new_id) for blocker in dependencies]))
        fragments.append(
            TxnFragment(
                statements=[f"RELATE $hr{i}_f->{BLOCKS_RELATION}->$hr{i}_t" for i in range(len(dependents))],
                params={
                    k: v
                    for i, dependent in enumerate(dependents)
                    for k, v in ((f"hr{i}_f", RecordID(TASK_TABLE, new_id)),
                                 (f"hr{i}_t", RecordID(TASK_TABLE, dependent)))
                },
            )
        )"""),
]
BUILDS["K17_heal_after_backfill"] = [
    ("        await self._reanchor_stragglers()\n        await self._backfill_blocks_edges()\n",
     "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n"),
]

BUILDS["WB18_owner_filter_excludes_superseded"] = [
    ("        if exclude_superseded or status is not None:\n",
     "        if exclude_superseded or status is not None or owner is not None:\n"),
]


def main() -> None:
    if sys.argv[1] == "--list":
        print("\n".join(BUILDS))
        return
    name, reference, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    src = reference.read_text()
    for old, new in BUILDS[name]:
        count = src.count(old)
        assert count == 1, f"{name}: anchor found {count}x: {old[:90]!r}"
        src = src.replace(old, new)
    out.write_text(src)


if __name__ == "__main__":
    main()
```

### `am2_builds.py` (md5 0bf51844)
```python
#!/usr/bin/env python3
"""adversary-58 — amendment-2 heal variants over the reference tasks.py (scratch instrument).

AM2L = amendment 2 (b) LITERALLY: chunks of `max_reanchor_dependents(0)` ROWS, one txn per chunk, a chunk
       fault -> WARNING + continue, the whole heal fail-OPEN, `count` + `chunks` logged once.
AM2C = the same, but each chunk is packed GREEDILY against the heal's OWN composed statement count
       (the control: a chunker whose size is derived from the heal, not from the supersede).
Usage: am2_builds.py <AM2L|AM2C> <reference tasks.py> <out tasks.py>
"""
import sys
from pathlib import Path

name, reference, out = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
src = reference.read_text()
start = src.index("    async def _reanchor_stragglers(self) -> None:\n")
end_marker = '        logger.info(_HEAL_EVENT, extra={"database": self._database, "count": len(healed)})\n'
end = src.index(end_marker, start) + len(end_marker)

BODY = '''    async def _reanchor_stragglers(self) -> None:
        """Boot heal, amendment 2 (b): chunked convergence sweep, fail-OPEN, loud in the log."""
        try:
            await self._reanchor_stragglers_inner()
        except Exception as error:  # noqa: BLE001 - am-2: the boot never fails on a heal fault
            logger.warning("task.backfill.straggler_heal_failed", extra={"error": repr(error)})

    async def _reanchor_stragglers_inner(self) -> None:
        rows = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE"
            )
        )
        successor = {str(r.get(_ID_KEY)): str(r.get(_COL_SUPERSEDED_BY)) for r in rows}
        if not successor:
            return
        stragglers = self._as_rows(
            await self._query(
                f"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_BLOCKED_BY} FROM {TASK_TABLE} "
                f"WHERE {_COL_BLOCKED_BY} CONTAINSANY $hs_ids",
                {"hs_ids": sorted(successor)},
            )
        )
        existing = await resolve_existing_rows(
            self._query, TASK_TABLE, sorted(set(successor.values()))
        )

        def _head(start: str) -> str | None:
            seen = {start}
            current = successor[start]
            while current in successor:
                if current in seen:
                    return None
                seen.add(current)
                current = successor[current]
            return current if current in existing else None

        plans: list[tuple[str, list[tuple[str, str]], list[str]]] = []
        for straggler in stragglers:
            dependent = str(straggler.get(_ID_KEY))
            columns = [str(b) for b in (straggler.get(_COL_BLOCKED_BY) or ())]
            final = list(columns)
            moves: list[tuple[str, str]] = []
            relates: list[str] = []
            for old in dict.fromkeys(b for b in columns if b in successor):
                head = _head(old)
                if head is None:
                    continue
                moves.append((old, head))
                if head not in final:
                    relates.append(head)
                final = list(dict.fromkeys(head if b == old else b for b in final))
            if moves:
                plans.append((dependent, moves, relates))
        if not plans:
            return
        chunks = self._heal_chunks(plans)
        healed = 0
        at = datetime.now(UTC).isoformat()
        for index, chunk in enumerate(chunks):
            fragments = self._heal_chunk_fragments(chunk, at, index)
            try:
                await self._apply(fragments)
                healed += len(chunk)
            except SurrealStoreError:
                logger.warning(
                    "task.backfill.straggler_chunk_failed",
                    extra={"chunk": index, "rows": [plan[0] for plan in chunk]},
                )
        logger.info(
            _HEAL_EVENT,
            extra={"database": self._database, "count": healed, "chunks": len(chunks)},
        )

    @staticmethod
    def _heal_chunk_fragments(chunk, at, index):  # type: ignore[no-untyped-def]
        """ONE chunk's fragments: a DELETE per DISTINCT old blocker, the shells, the relates."""
        by_old: dict[str, list[str]] = {}
        pairs: list[tuple[str, str, str]] = []
        relates: list[tuple[str, str]] = []
        for dependent, moves, heads in chunk:
            for old, head in moves:
                by_old.setdefault(old, []).append(dependent)
                pairs.append((dependent, old, head))
            relates.extend((head, dependent) for head in heads)
        deletes = TxnFragment(
            statements=[
                f"DELETE {BLOCKS_RELATION} WHERE in = $hc{index}d{i}_in AND out IN $hc{index}d{i}_out"
                for i in range(len(by_old))
            ],
            params={
                key: value
                for i, (old, deps) in enumerate(sorted(by_old.items()))
                for key, value in (
                    (f"hc{index}d{i}_in", RecordID(TASK_TABLE, old)),
                    (f"hc{index}d{i}_out", [RecordID(TASK_TABLE, d) for d in deps]),
                )
            },
        )
        return [
            deletes,
            *TaskLedger._reanchor_fragments(
                pairs, actor=_HEAL_ACTOR, at=at, reason=_HEAL_REASON, prefix=f"hc{index}r"
            ),
            *( [TaskLedger._relate_fragment(relates)] if relates else [] ),
        ]
'''

LITERAL_CHUNKS = '''
    def _heal_chunks(self, plans):  # type: ignore[no-untyped-def]
        """am-2 LITERAL: chunks of max_reanchor_dependents(0) ROWS (the supersede's derived cap)."""
        size = self.max_reanchor_dependents(0)
        return [plans[i : i + size] for i in range(0, len(plans), size)]
'''

GREEDY_CHUNKS = '''
    def _heal_chunks(self, plans):  # type: ignore[no-untyped-def]
        """CONTROL: pack rows greedily against the heal's OWN statement count (incremental), then
        VERIFY every chunk by composing its real fragments (never trust the formula)."""
        cap = _txn_module.TXN_STATEMENT_HARD_CAP
        chunks: list[list] = []
        current: list = []
        olds: set[str] = set()
        count = 0
        for plan in plans:
            _dep, moves, heads = plan
            new_olds = {old for old, _h in moves} - olds
            cost = 2 * len(moves) + len(heads) + len(new_olds)
            if current and count + cost > cap:
                chunks.append(current)
                current, olds, count = [], set(), 0
                new_olds = {old for old, _h in moves}
                cost = 2 * len(moves) + len(heads) + len(new_olds)
            current.append(plan)
            olds |= new_olds
            count += cost
        if current:
            chunks.append(current)
        for index, chunk in enumerate(chunks):
            composed = sum(len(f.statements) for f in self._heal_chunk_fragments(chunk, "t", index))
            assert composed <= cap, (index, composed)
        return chunks
'''

body = BODY + (LITERAL_CHUNKS if name == "AM2L" else GREEDY_CHUNKS)
out.write_text(src[:start] + body + src[end:])
```

### `declared.py` (md5 6df71751)
```python
"""adversary-58 — DECLARED RED sets, written 2026-09-26 BEFORE any wrong build was run.

Keys: build name.  Value: node-id PREFIXES (file::Class::test or file::test) expected to go RED.
A build is a SURVIVOR finding iff no contract file reddens AND its paired probe does.
`REFERENCE` declares the probes that measure a NEW DOOR / reach gap on the correct build itself.
"""

S = "loremaster/tests/test_supersede_reanchor_58.py::"
G = "loremaster/tests/test_task_guarded_shell_58.py::"
P = "loremaster/tests/test_task_claimable_partition_58.py::"
R = "loremaster/tests/test_supersede_render_58.py::"
X = "loremaster/tests/test_adversary58_probes.py::"

REFERENCE_DOORS = [X + "test_PR9_", X + "test_PR10_"]  # PR11 is OBSERVATIONAL (declared: unknown)

DECLARED: dict[str, list[str]] = {
    "REFERENCE": REFERENCE_DOORS,
    "WB1_launder_any_rollback_as_R1": [X + "test_PR1_"],
    "WB2a_legit_two_statement_R1_guard": [],
    "WB2_cap_ignores_K_on_the_legit_layout": [X + "test_PR2_"],
    "WB3_heal_counts_pairs": [X + "test_PR3_"],
    "WB4_heal_first_blocker_only": [X + "test_PR3_"],
    "WB5_heal_relate_without_dedupe": [X + "test_PR4_"],
    "WB6_heal_no_phantom_head_check": [X + "test_PR5_"],
    "WB7_130_client_side_postfilter": [X + "test_PR6_"],
    "WB8_reblocked_done_only": [X + "test_PR7_"],
    "WB9_cycle_minted_all_pending": [X + "test_PR8_"],
    "WB12_fourth_clone_module_level_guard": [],
    "WB14_warn_threshold_cloned": [X + "test_PR13_"],
    "WB15_literal_hard_cap_copy": [X + "test_PR14_"],
    "WB16_note_at_constant": [X + "test_PR12_"],
    "K1_reanchor_outside_the_supersede_txn": [S + "TestTheSupersedeIsONETransaction::"],
    "K2_skip_terminal_dependents": [S + "TestEveryDependentFollowsTheWorkToTheSuccessor::"],
    "K3_literal_cap": [
        S + "TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]",
        S + "TestTheHubBoundIsDERIVED::test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap",
    ],
    "K4_cycle_over_unrewired_graph": [
        S + "TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed",
    ],
    "K5_no_dedupe_in_rewrite": [
        S + "TestTheRewireDedupes::test_a_legacy_duplicate_X_X_becomes_ONE_successor_entry_and_ONE_edge",
    ],
    "K6_note_actor_missourced": [
        S + "TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent",
    ],
    "K7_reanchor_private_clone_not_shell": [
        G + "TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell",
        G + "TestSharingIsProvenByMutationTHEAPPEND::test_transition_stamp_claim_and_reanchor_events",
        G + "TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_every_guarded_append_ledger",
        G + "TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_task_ledgers_one_producer",
    ],
    "K8_130_partition_unchanged": [P + "TestASupersededRowMatchesNoStatusFilter::test_no_status_filter"],
    "K9_heal_logs_every_boot": [
        S + "TestTheBootHealReanchorsStragglers::test_a_second_boot_changes_NOTHING_and_is_SILENT",
    ],
    "K10_heal_stops_at_first_hop": [
        S + "TestTheBootHealReanchorsStragglers::test_a_three_hop_chain_reanchors_to_the_HEAD",
        S + "TestTheBootHealReanchorsStragglers::test_a_DONE_head_frees_the_straggler",
    ],
    "K11_heal_counts_chains": [
        S + "TestTheBootHealReanchorsStragglers::test_a_boot_heals_every_straggler_to_its_successor",
    ],
    "K12_R1_auto_retry": [S + "TestAConcurrentCreateIsRefusedNotStranded::"],
    "K13_reblocked_ignores_other_blockers": [
        S + "TestSupersedeOfATerminalPredecessorA1::test_reblocked_names_exactly_the_previously_CLAIMABLE",
    ],
    "K14_no_R1_closing_guard": [S + "TestAConcurrentCreateIsRefusedNotStranded::"],
    "K15_claim_cas_on_stale_preread": [
        S + "TestSupersedeOfATerminalPredecessorA1::test_a_claim_whose_PRE_READ_predates_the_reanchor",
    ],
}
```

### `wb_driver.py` (md5 8e476786)
```python
#!/usr/bin/env python3
"""adversary-58 wrong-build DRIVER — declare-then-diff, both ways, restore byte-exact after each.

Usage (from the scratch root): python wb_driver.py <scratch-root> <results.jsonl> [build ...]
Installs each wrong build's tasks.py, runs the 58 contract files + the adversary probes, parses pytest's
short-summary FAILED/ERROR ids, diffs them against declared.py BOTH ways, restores the reference and
asserts its md5.  WB17 (a hang) runs PR15 alone under a process timeout.
"""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from declared import DECLARED  # noqa: E402

SCRATCH = Path(sys.argv[1])
RESULTS = Path(sys.argv[2])
WB_DIR = Path(__file__).parent / "wb"
REFERENCE = Path(__file__).parent / "tasks_ref58.py"
TARGET = SCRATCH / "loremaster/loremaster/tasks.py"
FILES = [
    "loremaster/tests/test_supersede_reanchor_58.py",
    "loremaster/tests/test_task_guarded_shell_58.py",
    "loremaster/tests/test_task_claimable_partition_58.py",
    "loremaster/tests/test_supersede_render_58.py",
    "loremaster/tests/test_adversary58_probes.py",
]
PROBES = "loremaster/tests/test_adversary58_probes.py::"
SUMMARY = re.compile(r"^(FAILED|ERROR) (\S+)")


def md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


REF_MD5 = md5(REFERENCE)


def install(source: Path) -> None:
    shutil.copyfile(source, TARGET)
    for pyc in (SCRATCH / "loremaster/loremaster/__pycache__").glob("tasks.*.pyc"):
        pyc.unlink()


def run(args: list[str], timeout: int | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(
            ["uv", "run", "--offline", "pytest", "-p", "no:cacheprovider", "-q", "-rfE",
             "--color=no", *args],
            cwd=SCRATCH, capture_output=True, text=True, timeout=timeout,
        )
        return proc.returncode, proc.stdout + proc.stderr
    except subprocess.TimeoutExpired as expired:
        return 124, f"TIMEOUT after {timeout}s\n{expired.stdout or ''}"


def reds(output: str) -> list[str]:
    in_summary = False
    found = []
    for line in output.splitlines():
        if "short test summary info" in line:
            in_summary = True
            continue
        if in_summary:
            match = SUMMARY.match(line)
            if match:
                found.append(match.group(2))
    return sorted(set(found))


def tail(output: str) -> str:
    lines = [line for line in output.splitlines() if line.strip()]
    return lines[-1] if lines else ""


builds = sys.argv[3:] or ["REFERENCE", *[n for n in DECLARED if n != "REFERENCE"]]
for name in builds:
    started = time.time()
    source = REFERENCE if name == "REFERENCE" else WB_DIR / f"{name}.py"
    install(source)
    assert md5(TARGET) == md5(source), f"{name}: install did not land"
    if name == "WB17_heal_unbounded_chain_follow":
        code, output = run([f"{FILES[-1]}::test_PR15_a_superseded_by_loop_does_not_hang_the_boot"], 180)
    else:
        code, output = run(["-n", "auto", *FILES])
    observed = reds(output)
    declared = DECLARED.get(name, [])
    declared_green = [d for d in declared if not any(r.startswith(d) for r in observed)]
    unexpected = [r for r in observed if not any(r.startswith(d) for d in declared)]
    contract_reds = [r for r in observed if not r.startswith(PROBES)]
    install(REFERENCE)
    assert md5(TARGET) == REF_MD5, "restore failed"
    record = {
        "build": name, "exit": code, "tail": tail(output), "seconds": round(time.time() - started),
        "observed_red": observed, "declared": declared, "declared_but_green": declared_green,
        "unexpected_red": unexpected, "contract_reds": contract_reds,
        "verdict": "TIMEOUT(hang)" if code == 124 else (
            "SURVIVES-CONTRACT" if not contract_reds else "KILLED-BY-CONTRACT"),
    }
    with RESULTS.open("a") as handle:
        handle.write(json.dumps(record) + "\n")
    (RESULTS.parent / f"out_{name}.log").write_text(output)
    print(f"{name}: {record['verdict']} | {record['tail']} | declared_green={declared_green} "
          f"unexpected={unexpected}", flush=True)
print("DRIVER DONE; reference restored md5", md5(TARGET))
```

### `wb_delta.py` (md5 f2e26ac7)
```python
"""Recompute each wrong build's RED set as a DELTA against the reference build's reds, then diff both ways."""
import json, sys
sys.path.insert(0, sys.argv[1])
from declared import DECLARED
rows = [json.loads(l) for l in open(sys.argv[2])]
ref = next(r for r in rows if r["build"] == "REFERENCE")
base = set(ref["observed_red"])
PROBES = "loremaster/tests/test_adversary58_probes.py::"
print(f"REFERENCE reds ({len(base)}): {sorted(base)}  tail: {ref['tail']}")
for r in rows:
    if r["build"] == "REFERENCE":
        continue
    obs = set(r["observed_red"])
    new = sorted(obs - base); healed = sorted(base - obs)
    decl = DECLARED.get(r["build"], [])
    decl_green = [d for d in decl if not any(x.startswith(d) for x in new)]
    unexpected = [x for x in new if not any(x.startswith(d) for d in decl)]
    contract_new = [x for x in new if not x.startswith(PROBES)]
    verdict = ("TIMEOUT(hang)" if r["exit"] == 124 else
               "SURVIVES" if not contract_new else "KILLED")
    short = lambda xs: [x.split("::", 1)[1][:95] for x in xs]
    print(f"\n{r['build']}: {verdict} | {r['tail']}\n  new_red={short(new)}\n  declared_but_green={decl_green}\n  unexpected={short(unexpected)}\n  healed_vs_ref={short(healed)}")
```

### `lane58cmd.sh` (md5 e525ff1b)
```bash
#!/usr/bin/env bash
# lane58cmd.sh <workdir> <logfile> -- <command...>   (adversary-58, LORE-SCOPED lane)
# BUSY = a process whose EXECUTABLE (comm) is uv / python* / pytest AND whose args mention pytest AND whose
# cmdline or cwd is under the lore tree / a lore session scratch.  Keying on comm (never on a bash wrapper's
# text) is what stops the waiter matching ITSELF or another agent's waiter (#228: a pattern-in-cmdline
# watcher observes its own corpus).  Clear = 2 consecutive clear checks 15 s apart.
# Then confirms spike-surreal is active and runs <command> in its OWN process group with a 5 s watchdog
# that kills that group (by PGID) below 15 GB MemAvailable.  Exit: 97 lane never freed · 98 watchdog · 95 spike down.
set -u
workdir="$1"; logfile="$2"; shift 2
[ "${1:-}" = "--" ] && shift
busy_now() {
  ps -eo pid=,comm=,args= | while read -r pid comm args; do
    case "$comm" in uv|python*|pytest) ;; *) continue;; esac
    case "$args" in *pytest*) ;; *) continue;; esac
    where="$(tr '\0' ' ' < /proc/$pid/cmdline 2>/dev/null) $(readlink /proc/$pid/cwd 2>/dev/null)"
    case "$where" in *PycharmProjects/lore*|*PycharmProjects-lore/*) echo "$pid";; esac
  done
}
deadline=$(( $(date +%s) + 90*60 )); clear=0
while :; do
  if [ -z "$(busy_now)" ]; then clear=$((clear+1)); else clear=0; fi
  [ "$clear" -ge 2 ] && break
  if [ "$(date +%s)" -ge "$deadline" ]; then echo "LANE_BLOCKED busy=$(busy_now | tr '\n' ' ')" >>"$logfile"; exit 97; fi
  sleep 15
done
systemctl --user is-active --quiet spike-surreal.service || { echo "SPIKE_INACTIVE" >>"$logfile"; exit 95; }
cd "$workdir" || exit 96
echo "START $(date -Is) pwd=$(pwd) args: $*" >>"$logfile"
setsid "$@" >>"$logfile" 2>&1 &
pid=$!
fired=0
while kill -0 "$pid" 2>/dev/null; do
  avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  if [ "$avail_kb" -lt $((15*1024*1024)) ]; then
    echo "WATCHDOG_FIRED MemAvailable=${avail_kb}kB — killing pgid $pid" >>"$logfile"
    kill -TERM -- "-$pid" 2>/dev/null; fired=1; break
  fi
  sleep 5
done
wait "$pid"; rc=$?
echo "END $(date -Is) rc=$rc" >>"$logfile"
[ "$fired" = 1 ] && exit 98
exit "$rc"
```

### `all_runs.sh` (md5 d93acc4e)
```bash
#!/usr/bin/env bash
# adversary-58: every pytest this agent runs, strictly SEQUENTIAL inside ONE lane acquisition.
set -u
W=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/974aab4b-d082-4a22-92d0-f781857af668/scratchpad
S=$W/ref58
cd $S
PY="uv run --offline pytest -p no:cacheprovider -q -rfE --color=no"
REFMD5=9c254944572abedd21c75d5ff0ab778d
reset_ref() { cp $W/tasks_ref58.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc;
  [ "$(md5sum < loremaster/loremaster/tasks.py | cut -d' ' -f1)" = "$REFMD5" ] || { echo "RESTORE FAILED"; exit 90; }; }
install() { cp $W/wb/$1.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc; }

echo "== RUN1 scoped reference (58 files + DUAL-edited files) $(date -Is)"
reset_ref
$PY -n auto loremaster/tests/test_supersede_reanchor_58.py loremaster/tests/test_task_guarded_shell_58.py \
  loremaster/tests/test_task_claimable_partition_58.py loremaster/tests/test_supersede_render_58.py \
  loremaster/tests/test_blocks_edge.py loremaster/tests/test_task_ledger.py loremaster/tests/test_task_read_surface.py \
  loremaster/tests/test_link5_render_containment.py loremaster/tests/test_mcp_server.py scripts/test_forgery_door_sweep.py \
  > $W/run1_scoped_ref.out 2>&1; echo "RUN1 rc=$? $(tail -1 $W/run1_scoped_ref.out)"

echo "== DRIVER $(date -Is)"
uv run --quiet python $W/wb_driver.py $S $W/wb_results.jsonl
reset_ref

echo "== BATCH2 $(date -Is)"
$PY loremaster/tests/test_adversary58_batch2.py > $W/b2_reference.out 2>&1; echo "B2 REFERENCE rc=$? $(tail -1 $W/b2_reference.out)"
install WB2_cap_ignores_K_on_the_legit_layout
$PY "loremaster/tests/test_adversary58_batch2.py::test_PR16_a_hub_at_the_accessors_cap_with_K3_is_never_the_bare_compose_error" > $W/b2_WB2.out 2>&1; echo "B2 WB2 PR16 rc=$? $(tail -1 $W/b2_WB2.out)"
install K16_dependent_relates_hand_rolled
$PY -n auto "loremaster/tests/test_blocks_edge.py::TestSupersedeCarriesBlockedBy174" loremaster/tests/test_supersede_reanchor_58.py loremaster/tests/test_task_guarded_shell_58.py > $W/b2_K16.out 2>&1; echo "B2 K16 rc=$? $(tail -1 $W/b2_K16.out)"
install K17_heal_after_backfill
$PY scripts/test_forgery_door_sweep.py > $W/b2_K17.out 2>&1; echo "B2 K17 forgery-sweep rc=$? $(tail -1 $W/b2_K17.out)"
reset_ref

echo "== P5 fake mutation $(date -Is)"
cp -a loremaster/tests/_task_fakes.py $W/_task_fakes.held.py
python3 - <<'PYEOF'
from pathlib import Path
p = Path("loremaster/tests/_task_fakes.py"); s = p.read_text()
old = "        for dependent in list(self.db.tasks.values()):\n            if dependent.id == new_id or task_id not in dependent.blocked_by:"
assert s.count(old) == 1, "P5 anchor"
p.write_text(s.replace(old, "        for dependent in []:  # P5: fake re-anchor removed\n            if dependent.id == new_id or task_id not in dependent.blocked_by:"))
PYEOF
$PY -n auto loremaster/tests/test_task_ledger.py loremaster/tests/test_mcp_server.py loremaster/tests/test_query_tasks_bounded.py \
  loremaster/tests/test_comms_footer.py loremaster/tests/test_task_read_surface.py > $W/p5_fake.out 2>&1; echo "P5 rc=$? $(tail -1 $W/p5_fake.out)"
cp -a $W/_task_fakes.held.py loremaster/tests/_task_fakes.py; echo "fake restored $(md5sum loremaster/tests/_task_fakes.py)"

echo "== BATCH3 amendment 2 $(date -Is)"
B3=loremaster/tests/test_adversary58_batch3.py
$PY $B3 > $W/b3_REFERENCE.out 2>&1; echo "B3 REFERENCE rc=$? $(tail -1 $W/b3_REFERENCE.out)"
for v in AM2L AM2C WB18_owner_filter_excludes_superseded; do
  install $v
  $PY -n auto $B3 loremaster/tests/test_supersede_reanchor_58.py loremaster/tests/test_task_guarded_shell_58.py \
    loremaster/tests/test_task_claimable_partition_58.py scripts/test_forgery_door_sweep.py > $W/b3_$v.out 2>&1
  echo "B3 $v rc=$? $(tail -1 $W/b3_$v.out)"
done
reset_ref
echo "restored $(md5sum loremaster/loremaster/tasks.py)"

echo "== SAT: park adversary probes out of the reference tree $(date -Is)"
mkdir -p $W/probes_parked && mv loremaster/tests/test_adversary58_*.py $W/probes_parked/
echo "== SAT REFERENCE full suite (HEAD+63c+HELD+ref58) $(date -Is)"
uv run --quiet python -c "import loremaster; print('loremaster.__file__ =', loremaster.__file__)"
uv run --offline pytest -n auto -q -p no:cacheprovider -rfE --color=no > $W/sat_reference.out 2>&1; echo "SAT REF rc=$? $(tail -1 $W/sat_reference.out)"
echo "== SAT BASELINE full suite (HEAD+63c) $(date -Is)"
cd $W/base58
uv run --quiet python -c "import loremaster; print('loremaster.__file__ =', loremaster.__file__)"
uv run --offline pytest -n auto -q -p no:cacheprovider -rfE --color=no > $W/sat_baseline.out 2>&1; echo "SAT BASE rc=$? $(tail -1 $W/sat_baseline.out)"
echo "== ALL DONE $(date -Is)"
```

### `followup.sh` (md5 9d1688a2)
```bash
#!/usr/bin/env bash
# adversary-58 follow-up (after SAT): fixed PR18 on AM2L; WB17 hang probe under a process timeout.
set -u
W=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/974aab4b-d082-4a22-92d0-f781857af668/scratchpad
cd $W/ref58
PY="uv run --offline pytest -p no:cacheprovider -q -rfE --color=no"
cp $W/test_adversary58_batch3.py $W/test_adversary58_probes.py loremaster/tests/
cp $W/wb/AM2L.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc
$PY "loremaster/tests/test_adversary58_batch3.py::test_PR18_am2_ruled_shape_cap_plus_one_of_ONE_blocker_heals_in_two_chunks" > $W/fu_PR18_AM2L.out 2>&1; echo "FU PR18 AM2L rc=$? $(tail -1 $W/fu_PR18_AM2L.out)"
cp $W/wb/AM2C.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc
$PY "loremaster/tests/test_adversary58_batch3.py::test_PR18_am2_ruled_shape_cap_plus_one_of_ONE_blocker_heals_in_two_chunks" > $W/fu_PR18_AM2C.out 2>&1; echo "FU PR18 AM2C rc=$? $(tail -1 $W/fu_PR18_AM2C.out)"
cp $W/tasks_ref58.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc
$PY "loremaster/tests/test_adversary58_probes.py::test_PR15_a_superseded_by_loop_does_not_hang_the_boot" > $W/fu_PR15_ref.out 2>&1; echo "FU PR15 REF rc=$? $(tail -1 $W/fu_PR15_ref.out)"
cp $W/wb/WB17_heal_unbounded_chain_follow.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc
timeout -s KILL 120 $PY "loremaster/tests/test_adversary58_probes.py::test_PR15_a_superseded_by_loop_does_not_hang_the_boot" > $W/fu_PR15_WB17.out 2>&1; echo "FU PR15 WB17 rc=$? (124/137 = killed by timeout = HANG)"
cp $W/tasks_ref58.py loremaster/loremaster/tasks.py; rm -f loremaster/loremaster/__pycache__/tasks.*.pyc
echo "restored $(md5sum loremaster/loremaster/tasks.py)"
mv loremaster/tests/test_adversary58_*.py $W/probes_parked/
echo "== FOLLOWUP DONE $(date -Is)"
```

### `test_adversary58_probes.py` (md5 2cf0d5f4)
```python
"""adversary-58 PROBES — each asserts the CORRECT behaviour the packet-58 contract leaves unpinned.

Instrument (brief-base §1): copied into a SCRATCH tree's ``loremaster/tests/`` only; never the repo.
P0 discipline: every probe must PASS on adversary-58's reference build (positive control) and FAIL on
its paired wrong build (discrimination); the contract's own files must stay GREEN on that wrong build
for the pair to be a survivor finding.  Written 2026-09-26 against HEAD a66c95e + 63c b23f3e43 + §HELD.
"""

from __future__ import annotations

import ast
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest
from _reanchor_58_support import (
    ACTION_REANCHORED,
    CLAIMANT,
    all_columns,
    assert_edge_mirrors_column_for_every_row,
    bulk_seed_dependents,
    column,
    create,
    drive_to,
    edge_pairs,
    events_of,
    ledger58,
    new_ledger,
    raw,
    raw_relate,
    raw_seed_row,
    snapshot,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store.surreal_schema import TASK_TABLE
from loremaster.tasks import STATUS_DONE, STATUS_WONTFIX, TaskLedger, TaskLedgerError

__all__ = ["ledger58"]


async def _boot(env: SurrealEnv) -> None:
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()
    finally:
        await booted.close()


def _chain(tag: str, length: int) -> list[str]:
    return [f"{tag}{index:02d}chainadv5800000000000" for index in range(length)]


async def _seed_chain(ledger: TaskLedger, ids: list[str]) -> None:
    for index, task_id in reversed(list(enumerate(ids))):
        nxt = ids[index + 1] if index + 1 < len(ids) else None
        await raw_seed_row(ledger, task_id, blocked_by=[], superseded_by=nxt)


# ---------------------------------------------------------------------------------------------
# PR1 — a NON-straggler rollback must NOT be served as the R1 "retry" teaching (supersede twin of B6)
# ---------------------------------------------------------------------------------------------
async def test_PR1_a_genuine_store_fault_is_not_laundered_into_the_R1_retry_teaching(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    dependent = await create(ledger, "Y", [old])
    await raw(
        ledger,
        f"DEFINE EVENT adv58 ON TABLE {TASK_TABLE} WHEN $event = 'UPDATE' AND "
        f"record::id($after.id) = '{dependent}' THEN {{ THROW 'adv58-injected' }}",
    )
    with pytest.raises(Exception) as caught:  # noqa: PT011
        await supersede(ledger, old)
    text = str(caught.value).lower()
    assert "retry" not in text and "was created while" not in text, (
        f"a store fault with NO concurrent create was served as the R1 straggler teaching: {caught.value!r}"
    )


# ---------------------------------------------------------------------------------------------
# PR2 — the derived cap must follow K across a floor boundary (K = per always crosses one)
# ---------------------------------------------------------------------------------------------
async def test_PR2_the_cap_moves_with_K_across_a_floor_boundary(
    ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
) -> None:
    import importlib

    ledger, _env = ledger58
    tasks_module = importlib.import_module("loremaster.tasks")
    real = tasks_module.compose
    counts: list[int] = []

    def _spy(*fragments: Any) -> Any:
        counts.append(sum(len(f.statements) for f in fragments))
        return real(*fragments)

    async def _count(n: int, k: int) -> int:
        old = await create(ledger, "X")
        for i in range(n):
            await create(ledger, f"d{i}", [old])
        blockers = [await create(ledger, f"b{i}") for i in range(k)]
        monkeypatch.setattr(tasks_module, "compose", _spy)
        try:
            await supersede(ledger, old, blocked_by=blockers)
        finally:
            monkeypatch.setattr(tasks_module, "compose", real)
        return counts[-1]

    per = await _count(2, 0) - await _count(1, 0)
    for k in (0, per, per + 1):
        c1 = await _count(1, k)
        fixed = c1 - per
        assert ledger.max_reanchor_dependents(k) == (_txn.TXN_STATEMENT_HARD_CAP - fixed) // per, k


# ---------------------------------------------------------------------------------------------
# PR3 — the heal re-anchors EVERY superseded entry of a row, and counts ROWS (not pairs)
# ---------------------------------------------------------------------------------------------
async def test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    chain_a, chain_b = _chain("pa", 2), _chain("pb", 2)
    await _seed_chain(ledger, chain_a)
    await _seed_chain(ledger, chain_b)
    straggler = "adv58twoblockers0000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[chain_a[0], chain_b[0]])
    await raw_relate(ledger, chain_a[0], straggler)
    await raw_relate(ledger, chain_b[0], straggler)
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await _boot(env)
    assert await column(ledger, straggler) == [chain_a[-1], chain_b[-1]]
    await assert_edge_mirrors_column_for_every_row(ledger, where="two-blocker straggler")
    records = [r for r in caplog.records if r.getMessage() == "task.backfill.stragglers_reanchored"]
    assert len(records) == 1 and getattr(records[0], "count", None) == 1, [
        getattr(r, "count", None) for r in records
    ]


# ---------------------------------------------------------------------------------------------
# PR4 — the heal must not DOUBLE an edge when the straggler already names the head
# ---------------------------------------------------------------------------------------------
async def test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    chain = _chain("pd", 2)
    await _seed_chain(ledger, chain)
    straggler = "adv58alreadyhead000000000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[chain[0], chain[1]])
    await raw_relate(ledger, chain[0], straggler)
    await raw_relate(ledger, chain[1], straggler)
    await _boot(env)
    assert await column(ledger, straggler) == [chain[1]]
    await assert_edge_mirrors_column_for_every_row(ledger, where="straggler already naming head")


# ---------------------------------------------------------------------------------------------
# PR5 — a straggler whose chain head names NO row must not kill the boot (backfill's R11 twin)
# ---------------------------------------------------------------------------------------------
async def test_PR5_a_phantom_chain_head_does_not_fail_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    blocker = "adv58phantomheadblocker00000000"
    await raw_seed_row(ledger, blocker, blocked_by=[], superseded_by="adv58nosuchrow000000000000000000")
    straggler = "adv58phantomheadstraggler000000"
    await raw_seed_row(ledger, straggler, blocked_by=[blocker])
    await raw_relate(ledger, blocker, straggler)
    healthy_old = await create(ledger, "an ordinary X")
    await _boot(env)  # must not raise
    assert await column(ledger, straggler) == [blocker]
    assert healthy_old in await all_columns(ledger)


# ---------------------------------------------------------------------------------------------
# PR6 — #130 exclusion must hold under a LIMIT (T1: a short answer is a TRUE short answer)
# ---------------------------------------------------------------------------------------------
async def test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    for index in range(6):
        task_id = f"0000adv58sup{index:02d}0000000000000000"
        await raw_seed_row(ledger, task_id, blocked_by=[], superseded_by="zzzzsuccessor")
    genuine = [await create(ledger, f"genuine {i}") for i in range(3)]
    served = await ledger.query_tasks(status="open", limit=3)
    assert sorted(t.id for t in served) == sorted(genuine), [t.id for t in served]


# ---------------------------------------------------------------------------------------------
# PR7 — a WONTFIX predecessor re-blocks exactly like a DONE one (TERMINAL_STATUSES, not "done")
# ---------------------------------------------------------------------------------------------
async def test_PR7_a_WONTFIX_predecessor_reports_its_reblocked_dependent(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X, abandoned")
    await drive_to(ledger, old, STATUS_WONTFIX)
    dependent = await create(ledger, "Y, claimable while X is wontfix", [old])
    result = await supersede(ledger, old)
    assert list(result.reblocked) == [dependent]


# ---------------------------------------------------------------------------------------------
# PR8 — a dependent already on a LEGACY loop (not closed by this rewire) — spec-silent; the probe
#       records what the reference does (succeeds) so a refusing build is visible.
# ---------------------------------------------------------------------------------------------
async def test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    loop_l, loop_y = "adv58loopl00000000000000000000", "adv58loopy00000000000000000000"
    await raw_seed_row(ledger, loop_l, blocked_by=[loop_y])
    await raw_seed_row(ledger, loop_y, blocked_by=[old, loop_l])
    await raw_relate(ledger, loop_y, loop_l)
    await raw_relate(ledger, loop_l, loop_y)
    await raw_relate(ledger, old, loop_y)
    successor = successor_of(await supersede(ledger, old))
    assert await column(ledger, loop_y) == [successor, loop_l]


# ---------------------------------------------------------------------------------------------
# PR9 — the one-producer scan's REACH: a clone whose THROW guard is a module constant
# ---------------------------------------------------------------------------------------------
def test_PR9_a_clone_with_a_MODULE_LEVEL_guard_template_is_found() -> None:
    from test_task_guarded_shell_58 import guarded_shell_producers

    source = (
        '_ASSIGN_GUARD = "IF array::len(${var}) == 0 {{ THROW \'{msg}\' }}"\n'
        "class Ledger:\n"
        "    @staticmethod\n"
        "    def _guarded_append_fragment(row_id, *, event):\n"
        "        return ['LET $v = (UPDATE t SET provenance.events += [$ev] WHERE x)',\n"
        "                \"IF array::len($v) == 0 { THROW 'lost' }\"]\n"
        "    @staticmethod\n"
        "    def _assign_fragment(row_id, owner):\n"
        "        return ['LET $a = (UPDATE t SET owner = $o, provenance.events += [$e])',\n"
        "                _ASSIGN_GUARD.format(var='a', msg='lost')]\n"
    )
    found = guarded_shell_producers(source)
    assert "Ledger._assign_fragment" in found, found


# ---------------------------------------------------------------------------------------------
# PR10 — a ROUTINE claim loss must not emit an ERROR-level log record (it did not before 58)
# ---------------------------------------------------------------------------------------------
async def test_PR10_a_routine_claim_loss_logs_no_ERROR(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, _env = ledger58
    blocker = await create(ledger, "an open blocker")
    blocked = await create(ledger, "blocked", [blocker])
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        result = await ledger.claim_task(blocked, CLAIMANT)
    assert not result.claimed
    errors = [(r.name, r.getMessage()) for r in caplog.records if r.levelno >= logging.ERROR]
    assert not errors, errors


# ---------------------------------------------------------------------------------------------
# PR11 — the index rider must serve the PRODUCTION containment statements, not a hand-typed one
# ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize(
    "statement",
    [
        "SELECT record::id(id) AS id FROM task WHERE blocked_by CONTAINS $x",
        "SELECT count() FROM task WHERE blocked_by CONTAINS $x GROUP ALL",
        "SELECT record::id(id) AS id, blocked_by FROM task WHERE blocked_by CONTAINSANY [$x]",
    ],
    ids=["direct_dependents", "R1_closing_guard_count", "heal_containsany"],
)
async def test_PR11_production_containment_statements_are_index_served(
    ledger58: tuple[TaskLedger, SurrealEnv], statement: str
) -> None:
    import test_keeps_schema as keeps_schema

    walker = keeps_schema.TestTheKeeperIndexFires
    ledger, _env = ledger58
    blocker = await create(ledger, "a blocker")
    await create(ledger, "a dependent", [blocker])
    plan = await raw(ledger, f"{statement} EXPLAIN", {"x": blocker})
    assert not walker._scans_table(plan, TASK_TABLE), walker._operators(plan)


# ---------------------------------------------------------------------------------------------
# PR12 — the re-anchor note's ``at`` is the supersede's time, not a stale/constant stamp
# ---------------------------------------------------------------------------------------------
async def test_PR12_the_note_at_is_the_supersede_time(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    old = await create(ledger, "X")
    dependent = await create(ledger, "Y", [old])
    before = datetime.now(UTC)
    await supersede(ledger, old)
    after = datetime.now(UTC)
    notes = [e for e in await events_of(ledger, dependent) if e.get("action") == ACTION_REANCHORED]
    stamp = datetime.fromisoformat(notes[0]["at"])
    assert before <= stamp <= after, (before, stamp, after)


# ---------------------------------------------------------------------------------------------
# PR13 — the WARN policy is SHARED: silencing SurrealStore._log_transaction_size silences the task WARN
# ---------------------------------------------------------------------------------------------
async def test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy(
    ledger58: tuple[TaskLedger, SurrealEnv],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from loremaster.store.surreal import SurrealStore

    ledger, _env = ledger58
    old = await create(ledger, "a hub above the warn threshold")
    await bulk_seed_dependents(ledger, old, 300, tag="adv58warn")
    monkeypatch.setattr(SurrealStore, "_log_transaction_size", staticmethod(lambda *a, **k: None))
    caplog.clear()
    with caplog.at_level(logging.DEBUG):
        await supersede(ledger, old)
    warned = [r for r in caplog.records if r.levelno == logging.WARNING and hasattr(r, "statement_count")]
    assert not warned, "the task ledger warned through a PRIVATE copy of the threshold policy"


# ---------------------------------------------------------------------------------------------
# PR14 — the hub cap follows the SHARED compose cap (mutate it; the accessor must move)
# ---------------------------------------------------------------------------------------------
async def test_PR14_the_accessor_follows_the_shared_hard_cap(
    ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch
) -> None:
    ledger, _env = ledger58
    baseline = ledger.max_reanchor_dependents(0)
    monkeypatch.setattr(_txn, "TXN_STATEMENT_HARD_CAP", _txn.TXN_STATEMENT_HARD_CAP - 300)
    assert ledger.max_reanchor_dependents(0) == baseline - 100


# ---------------------------------------------------------------------------------------------
# PR15 — a legacy superseded_by LOOP must not hang the boot (bounded chain follow)
# ---------------------------------------------------------------------------------------------
async def test_PR15_a_superseded_by_loop_does_not_hang_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    import asyncio

    ledger, env = ledger58
    first, second = "adv58suploopa00000000000000000", "adv58suploopb00000000000000000"
    await raw_seed_row(ledger, first, blocked_by=[], superseded_by=second)
    await raw_seed_row(ledger, second, blocked_by=[], superseded_by=first)
    straggler = "adv58suploopstraggler0000000000"
    await raw_seed_row(ledger, straggler, blocked_by=[first])
    await raw_relate(ledger, first, straggler)
    await asyncio.wait_for(_boot(env), timeout=60)
```

### `test_adversary58_batch2.py` (md5 1328e035)
```python
"""adversary-58 BATCH-2 PROBES (scratch-only instrument; see test_adversary58_probes.py header)."""

from __future__ import annotations

import pytest
from _reanchor_58_support import (
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    new_ledger,
    raw_seed_row,
)
from _surreal_harness import SurrealEnv
from loremaster.store._txn import SurrealStoreError
from loremaster.tasks import TaskLedger, TaskLedgerError

__all__ = ["ledger58"]


# PR16 — WB2's HARM: with the accessor over-stating the cap at K=3, a supersede of exactly `cap`
# dependents must still be a TEACHING refusal or a success — never compose's bare count error.
async def test_PR16_a_hub_at_the_accessors_cap_with_K3_is_never_the_bare_compose_error(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    k = 3
    cap = ledger.max_reanchor_dependents(k)
    old = await create(ledger, "the hub")
    blockers = [await create(ledger, f"successor blocker {i}") for i in range(k)]
    await bulk_seed_dependents(ledger, old, cap, tag="adv58k3cap")
    try:
        await ledger.supersede_task(
            old, subject="s", description="d", created_by="adv58", blocked_by=blockers
        )
    except SurrealStoreError as error:
        assert "exceeding the hard cap" not in str(error), (
            f"the derived cap ({cap} at K={k}) over-states the bound: compose's bare error served: {error}"
        )


# PR17 — DECISIONS 2 CONSTRUCTED: a large legacy straggler population vs the heal's ONE transaction.
async def test_PR17_the_boot_heal_at_scale_does_not_fail_the_boot(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, env = ledger58
    head = await create(ledger, "the successor")
    legacy = "adv58scalelegacyblocker00000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    stragglers = await bulk_seed_dependents(ledger, legacy, 1300, tag="adv58scale")
    booted = new_ledger(env)
    try:
        await booted.ensure_ready()  # the probe's claim: a boot survives 1300 legacy stragglers
    finally:
        await booted.close()
    assert await column(ledger, stragglers[0]) == [head]
```

### `test_adversary58_batch3.py` (md5 cdb99104)
```python
"""adversary-58 BATCH-3 PROBES — amendment 2 (e0760fd), which post-dates the graded contract (scratch-only)."""

from __future__ import annotations

import logging

import pytest
from _reanchor_58_support import (
    CLAIMANT,
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    new_ledger,
    raw_seed_row,
    successor_of,
    supersede,
)
from _surreal_harness import SurrealEnv
from loremaster.tasks import TaskLedger

__all__ = ["ledger58"]
HEAL_EVENT = "task.backfill.stragglers_reanchored"


async def _boot(env: SurrealEnv, caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    booted = new_ledger(env)
    caplog.clear()
    try:
        with caplog.at_level(logging.DEBUG):
            await booted.ensure_ready()
    finally:
        await booted.close()
    return [r for r in caplog.records if r.getMessage() == HEAL_EVENT]


async def _stragglers(ledger: TaskLedger, total: int, blockers: int, tag: str) -> list[str]:
    head = await create(ledger, f"{tag} head")
    ids: list[str] = []
    per = -(-total // blockers)
    for index in range(blockers):
        legacy = f"{tag}legacy{index:03d}0000000000000000"
        await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
        count = min(per, total - len(ids))
        if count <= 0:
            break
        ids += await bulk_seed_dependents(ledger, legacy, count, tag=f"{tag}{index:03d}x")
    return ids


# PR18 — amendment 2's OWN ruled pin shape: cap + 1 stragglers of ONE superseded blocker.
async def test_PR18_am2_ruled_shape_cap_plus_one_of_ONE_blocker_heals_in_two_chunks(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    cap = ledger.max_reanchor_dependents(0)
    ids = await _stragglers(ledger, cap + 1, 1, "am2one")
    records = await _boot(env, caplog)
    assert len(records) == 1 and getattr(records[0], "count", None) == cap + 1, [
        (getattr(r, "count", None), getattr(r, "chunks", None)) for r in records
    ]
    assert getattr(records[0], "chunks", None) == 2
    for task_id in (ids[0], ids[-1]):
        assert len(await column(ledger, task_id)) == 1, task_id


# PR19 — the SAME population spread over TEN distinct superseded blockers (the fleet's real shape).
async def test_PR19_cap_plus_one_stragglers_over_TEN_blockers_all_heal_in_ONE_boot(
    ledger58: tuple[TaskLedger, SurrealEnv], caplog: pytest.LogCaptureFixture
) -> None:
    ledger, env = ledger58
    cap = ledger.max_reanchor_dependents(0)
    await _stragglers(ledger, cap + 1, 10, "am2ten")
    records = await _boot(env, caplog)
    assert records and getattr(records[-1], "count", None) == cap + 1, [
        (getattr(r, "count", None), getattr(r, "chunks", None)) for r in records
    ]
    second = await _boot(env, caplog)
    assert not second, "the sweep did not converge: a second boot still found stragglers to heal"


# PR20 — amendment 2 (a): owner= serves a HELD superseded row, decorated; owner=+status= excludes it.
async def test_PR20_owner_query_serves_a_held_superseded_row_and_status_excludes_it(
    ledger58: tuple[TaskLedger, SurrealEnv],
) -> None:
    ledger, _env = ledger58
    held = await create(ledger, "Y — alice holds it, then it is reframed")
    kept = await create(ledger, "Z — alice holds it, never reframed")
    assert (await ledger.claim_task(held, CLAIMANT)).claimed
    assert (await ledger.claim_task(kept, CLAIMANT)).claimed
    successor = successor_of(await supersede(ledger, held))
    by_owner = {t.id: t for t in await ledger.query_tasks(owner=CLAIMANT)}
    assert set(by_owner) == {held, kept}, sorted(by_owner)
    assert by_owner[held].superseded_by == successor and by_owner[kept].superseded_by is None
    with_status = {t.id for t in await ledger.query_tasks(owner=CLAIMANT, status="claimed")}
    assert with_status == {kept}, sorted(with_status)
```

### raw wrong-build delta receipt (`wb_delta.py` over `wb_results.jsonl`, batch 1)
```text
REFERENCE reds (3): ['loremaster/tests/test_adversary58_probes.py::test_PR10_a_routine_claim_loss_logs_no_ERROR', 'loremaster/tests/test_adversary58_probes.py::test_PR9_a_clone_with_a_MODULE_LEVEL_guard_template_is_found', 'loremaster/tests/test_task_guarded_shell_58.py::TestParamNamesDoNotCollideAcrossComposedShells::test_three_reanchors_the_stamp_and_two_successor_edges_compose']  tail: 3 failed, 107 passed in 11.52s

WB1_launder_any_rollback_as_R1: SURVIVES | 4 failed, 106 passed in 12.39s
  new_red=['test_PR1_a_genuine_store_fault_is_not_laundered_into_the_R1_retry_teaching']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB2a_legit_two_statement_R1_guard: SURVIVES | 3 failed, 107 passed in 11.92s
  new_red=[]
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB2_cap_ignores_K_on_the_legit_layout: SURVIVES | 4 failed, 106 passed in 11.83s
  new_red=['test_PR2_the_cap_moves_with_K_across_a_floor_boundary']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB3_heal_counts_pairs: SURVIVES | 4 failed, 106 passed in 11.42s
  new_red=['test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB4_heal_first_blocker_only: SURVIVES | 4 failed, 106 passed in 11.44s
  new_red=['test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB5_heal_relate_without_dedupe: SURVIVES | 4 failed, 106 passed in 12.14s
  new_red=['test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB6_heal_no_phantom_head_check: SURVIVES | 4 failed, 106 passed in 11.78s
  new_red=['test_PR5_a_phantom_chain_head_does_not_fail_the_boot']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB7_130_client_side_postfilter: SURVIVES | 4 failed, 106 passed in 11.54s
  new_red=['test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB8_reblocked_done_only: SURVIVES | 4 failed, 106 passed in 12.19s
  new_red=['test_PR7_a_WONTFIX_predecessor_reports_its_reblocked_dependent']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB9_cycle_minted_all_pending: SURVIVES | 4 failed, 106 passed in 11.62s
  new_red=['test_PR8_a_dependent_on_a_legacy_loop_does_not_block_the_supersede']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB12_fourth_clone_module_level_guard: SURVIVES | 3 failed, 107 passed in 11.60s
  new_red=[]
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB14_warn_threshold_cloned: SURVIVES | 4 failed, 106 passed in 11.88s
  new_red=['test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB15_literal_hard_cap_copy: SURVIVES | 4 failed, 106 passed in 11.53s
  new_red=['test_PR14_the_accessor_follows_the_shared_hard_cap']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

WB16_note_at_constant: SURVIVES | 4 failed, 106 passed in 11.84s
  new_red=['test_PR12_the_note_at_is_the_supersede_time']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

K1_reanchor_outside_the_supersede_txn: KILLED | 15 failed, 95 passed in 11.57s
  new_red=['test_PR2_the_cap_moves_with_K_across_a_floor_boundary', 'TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES', 'TestTheHubBoundIsDERIVED::test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap', 'TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[0]', 'TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[edge_crea', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[edge_crea', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[edge_crea', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[row_updat', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[row_updat', 'TestTheSupersedeIsONETransaction::test_a_failure_at_dependent_k_rolls_back_EVERYTHING[row_updat', 'TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell']
  declared_but_green=[]
  unexpected=['test_PR2_the_cap_moves_with_K_across_a_floor_boundary', 'TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES', 'TestTheHubBoundIsDERIVED::test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap', 'TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[0]', 'TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]', 'TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell']
  healed_vs_ref=[]

K2_skip_terminal_dependents: KILLED | 4 failed, 94 passed, 12 errors in 11.74s
  new_red=['TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent_naming_X_X_pr', 'TestEachDependentCarriesTheReanchorNote::test_the_note_lands_on_the_DEPENDENT_never_on_X_or_the', 'TestEachDependentCarriesTheReanchorNote::test_updated_at_is_stamped_on_every_rewired_dependent', 'TestEveryDependentFollowsTheWorkToTheSuccessor::test_direct_dependents_of_X_is_EMPTY_and_of_the', 'TestEveryDependentFollowsTheWorkToTheSuccessor::test_every_dependent_names_the_successor_and_NO', 'TestEveryDependentFollowsTheWorkToTheSuccessor::test_only_the_X_entry_is_rewritten_order_and_ot', 'TestEveryDependentFollowsTheWorkToTheSuccessor::test_the_bystander_row_is_byte_unchanged', 'TestEveryDependentFollowsTheWorkToTheSuccessor::test_the_edge_mirrors_the_column_for_EVERY_row_', 'TestSupersedeOfATerminalPredecessorA1::test_every_status_is_rewired_including_claimed', 'TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_reanchor_the_backfill_mints_nothing_and_', 'TestTheSupersedeItselfIsUnchanged::test_X_is_stamped_and_the_successor_is_open_unowned', 'TestTheSupersedeItselfIsUnchanged::test_the_result_is_the_typed_carrier', 'TestTheSupersedeItselfIsUnchanged::test_the_result_names_exactly_the_reanchored_dependents']
  declared_but_green=[]
  unexpected=['TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent_naming_X_X_pr', 'TestEachDependentCarriesTheReanchorNote::test_the_note_lands_on_the_DEPENDENT_never_on_X_or_the', 'TestEachDependentCarriesTheReanchorNote::test_updated_at_is_stamped_on_every_rewired_dependent', 'TestSupersedeOfATerminalPredecessorA1::test_every_status_is_rewired_including_claimed', 'TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_reanchor_the_backfill_mints_nothing_and_', 'TestTheSupersedeItselfIsUnchanged::test_X_is_stamped_and_the_successor_is_open_unowned', 'TestTheSupersedeItselfIsUnchanged::test_the_result_is_the_typed_carrier', 'TestTheSupersedeItselfIsUnchanged::test_the_result_names_exactly_the_reanchored_dependents']
  healed_vs_ref=[]

K3_literal_cap: KILLED | 8 failed, 102 passed in 11.52s
  new_red=['test_PR14_the_accessor_follows_the_shared_hard_cap', 'test_PR2_the_cap_moves_with_K_across_a_floor_boundary', 'TestTheHubBoundIsDERIVED::test_MUTATION_an_extra_per_dependent_statement_MOVES_the_cap', 'TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-2]', 'TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]']
  declared_but_green=[]
  unexpected=['test_PR14_the_accessor_follows_the_shared_hard_cap', 'test_PR2_the_cap_moves_with_K_across_a_floor_boundary', 'TestTheHubBoundIsDERIVED::test_at_and_just_below_the_cap_EVERY_dependent_is_reanchored[cap-2]']
  healed_vs_ref=[]

K4_cycle_over_unrewired_graph: KILLED | 5 failed, 105 passed in 11.72s
  new_red=['TestACycleClosingRewireIsRefusedWhole::test_refused_as_a_cycle_naming_it_and_NOTHING_changed', 'TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_not']
  declared_but_green=[]
  unexpected=['TestTheBootBackfillAfterAReanchorIsANoOp::test_after_a_REFUSED_supersede_the_backfill_mints_not']
  healed_vs_ref=[]

K5_no_dedupe_in_rewrite: KILLED | 5 failed, 105 passed in 11.66s
  new_red=['test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge', 'TestTheRewireDedupes::test_a_legacy_duplicate_X_X_becomes_ONE_successor_entry_and_ONE_edge']
  declared_but_green=[]
  unexpected=['test_PR4_a_straggler_already_naming_the_head_gets_ONE_entry_and_ONE_edge']
  healed_vs_ref=[]

K6_note_actor_missourced: KILLED | 5 failed, 105 passed in 11.89s
  new_red=['TestEachDependentCarriesTheReanchorNote::test_exactly_ONE_new_event_per_dependent_naming_X_X_pr', 'TestTheBootHealReanchorsStragglers::test_a_boot_heals_every_straggler_to_its_successor_and_COUN']
  declared_but_green=[]
  unexpected=['TestTheBootHealReanchorsStragglers::test_a_boot_heals_every_straggler_to_its_successor_and_COUN']
  healed_vs_ref=[]

K7_reanchor_private_clone_not_shell: KILLED | 8 failed, 102 passed in 11.86s
  new_red=['TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_every_guarded_append_ledger_has_ON', 'TestEachLedgerModuleHasExactlyONEGuardedAppendProducer::test_the_task_ledgers_one_producer_IS_t', 'TestSharingIsProvenByMutationALWAYSTHROW::test_the_REANCHOR_routes_through_the_shell', 'TestSharingIsProvenByMutationTHEAPPEND::test_the_BOOT_HEAL_note_comes_from_the_shell_too', 'TestSharingIsProvenByMutationTHEAPPEND::test_transition_stamp_claim_and_reanchor_events_all_com']
  declared_but_green=[]
  unexpected=['TestSharingIsProvenByMutationTHEAPPEND::test_the_BOOT_HEAL_note_comes_from_the_shell_too']
  healed_vs_ref=[]

K8_130_partition_unchanged: KILLED | 9 failed, 101 passed in 11.89s
  new_red=['test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist', 'TestASupersededRowIsInNeitherPartition::test_blocked_False_excludes_superseded_rows', 'TestASupersededRowIsInNeitherPartition::test_blocked_True_excludes_superseded_rows', 'TestASupersededRowMatchesNoStatusFilter::test_no_status_filter_serves_a_superseded_row', 'TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_every_row_served_as_claimable_is_W', 'TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_nothing_the_CAS_refuses_is_served_']
  declared_but_green=[]
  unexpected=['test_PR6_status_open_with_a_limit_is_not_short_while_claimable_rows_exist', 'TestASupersededRowIsInNeitherPartition::test_blocked_False_excludes_superseded_rows', 'TestASupersededRowIsInNeitherPartition::test_blocked_True_excludes_superseded_rows', 'TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_every_row_served_as_claimable_is_W', 'TestEverythingServedAsClaimableIsClaimableAndViceVersa::test_nothing_the_CAS_refuses_is_served_']
  healed_vs_ref=[]

K9_heal_logs_every_boot: KILLED | 4 failed, 106 passed in 11.88s
  new_red=['TestTheBootHealReanchorsStragglers::test_a_second_boot_changes_NOTHING_and_is_SILENT']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

K10_heal_stops_at_first_hop: KILLED | 5 failed, 105 passed in 11.97s
  new_red=['TestTheBootHealReanchorsStragglers::test_a_DONE_head_frees_the_straggler', 'TestTheBootHealReanchorsStragglers::test_a_three_hop_chain_reanchors_to_the_HEAD']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

K11_heal_counts_chains: KILLED | 5 failed, 105 passed in 11.95s
  new_red=['test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once', 'TestTheBootHealReanchorsStragglers::test_a_boot_heals_every_straggler_to_its_successor_and_COUN']
  declared_but_green=[]
  unexpected=['test_PR3_a_straggler_naming_TWO_superseded_blockers_is_healed_fully_and_counted_once']
  healed_vs_ref=[]

K12_R1_auto_retry: KILLED | 4 failed, 106 passed in 11.88s
  new_red=['TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

K13_reblocked_ignores_other_blockers: KILLED | 5 failed, 105 passed in 11.80s
  new_red=['TestSupersedeOfATerminalPredecessorA1::test_reblocked_names_exactly_the_previously_CLAIMABLE_de', 'TestTheRenderEndToEnd::test_a_supersede_through_the_tool_seam_serves_the_receipt']
  declared_but_green=[]
  unexpected=['TestTheRenderEndToEnd::test_a_supersede_through_the_tool_seam_serves_the_receipt']
  healed_vs_ref=[]

K14_no_R1_closing_guard: KILLED | 4 failed, 106 passed in 11.60s
  new_red=['TestAConcurrentCreateIsRefusedNotStranded::test_the_supersede_is_REFUSED_byte_inert_and_TEACHES']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]

K15_claim_cas_on_stale_preread: KILLED | 4 failed, 106 passed in 11.86s
  new_red=['TestSupersedeOfATerminalPredecessorA1::test_a_claim_whose_PRE_READ_predates_the_reanchor_can_NO']
  declared_but_green=[]
  unexpected=[]
  healed_vs_ref=[]
```

## §P1c-DIFF — my reach table vs the author's §REACH
- Author rows I **confirm**: `edge ≡ column` helper (instrument sound), sharing mutations (hand-list bound, stated), #130 "served ⇒ claimable" (sound within `limit=None`), ∀ claim-loss hand-list (bound, stated).
- Author rows **understated**: (1) one-producer scan — "a new module joins automatically" is true of MODULES; the PRODUCER predicate is a per-scope token co-occurrence shape (WB12); (2) hub cap — "a changed builder moves the measured cap" is true of the per-dependent count; K-dependence is sampled below a floor boundary (WB2) and the shared `TXN_STATEMENT_HARD_CAP` is not mutation-proven (WB15); (3) "every dependent rewired" — true of supersede; the HEAL's ∀ (entries per row, dedupe, phantom head) has no fixture (WB3–WB6); (4) #130 status sweep — reach excludes the `limit` path (WB7).
- Instruments **absent** from the author's table: the WARN telemetry policy (WB14), the index-rider EXPLAIN (proxy; PR11), D12's door count (order + fail-open conflict), D9's routing pin (presence-only, K16), `test_retry_seam`'s door enumeration (SD3).

## VERDICT
**CONTRACT INSUFFICIENT.**
- **P1:** 13 wrong builds survive the whole contract on an independently-written reference (+ K16, WB18) — each with a named missing pin (§MISSING PINS MP1–MP17), each probe proven to pass on the correct build and fail on the wrong one (P0 pairs; declared-before-run; 0 declared-but-green).
- **P1b:** 14 of 19 invariants carry a door — guarded-by-fixture/failure-mode (Q2, Q3 `at`, Q5, Q7, Q8, Q9, Q11, Q12, Q13), effect-only with sharing unproven (Q15, Q16), or unpinned (Q10, Q18, Q19) — each with a surviving-build receipt in §P1b; Q1, Q4, Q6, Q14, Q17 are ∀ (or a stated hand-list bound) and every door-build against them was KILLED.
- **P1c:** 6 instruments carry a MISSING PIN (one-producer reach, hub-cap K + shared-constant, WARN sharing, heal ∀, #130 limit, D9); 1 pins an unruled order (D12); legs empirical where marked.
- **SAT:** not 0 failed on HEAD+63c+§HELD+an independent correct build — 3 contract-attributable reds (SD1–SD3); plus 7 unrelated HEAD reds flagged.
- **Spec:** amendment 2 post-dates the contract: its two rulings are unpinned (MP15, MP16), and its heal chunk-size source is itself defective and its fail-open contradicts the standing door sweep — **route §AM2 #1/#2 to the design sidecar before the contract revision pins them**, or the revision will faithfully pin the bug (PR18 shows the ruled pin already does).
- **What held:** atomicity (all 6 injections), R1 closing guard + no auto-retry, derived-cap padding mutation, cycle refusal over the rewired graph, dedupe of `[X,X]`, claim pre-read race, #130 both directions at `limit=None`, the A1 `reblocked` subset for `done`, heal chain-to-head + idempotence + chain-vs-row count, sharing by mutation for the four ruled callers + heal, RED@HEAD 68 right-reason, §HELD apply over 63c.
