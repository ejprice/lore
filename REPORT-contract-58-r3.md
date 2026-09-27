brief-base v17 read · brief project v7 read

# REPORT — contract-58-r3 (packet 58 contract revision 3: the am-7 / am-8 fold)

## SUMMARY BLOCK
- `brief-base v17 read` · `brief project v7 read` · **BRIEF CONFLICT (refused, brief-base §2):** "every adaptation … with its kill re-proven" would replay the grader's wrong builds; I mutation-prove with MY OWN mutations instead.
- **State: done-with-deviations.** Contract r3 is tests only: 6 new files, 2 edited, 1 deleted, plus the registry and §HELD. The am-7/am-8 fold is complete, and **am-9 (all six forks CONFIRMED), 63c am-34, and am-10 (FK-r3-7: the FATE classifier, committed as `test_exhaustion_fates.py`, green at HEAD, 74 sites with per-row verdicts and 8 pinned holes) are folded** (D-AM9 / D-AM34 / D-AM10). The adversary's graded probes land 13/14 AST-EQUAL; 1 is re-keyed by am-7. RED@HEAD: 82 new reds at `c383edd` → **80 at `4beb79e`** (a28b's index loads; +1 am-9 §5 pin), every one for the right reason. §MUTATION: 23 of my own mutations, all EXACT except 3 individually adjudicated, 0 declared-stayed-green. SAT on HEAD + a28b + §HELD + reference, full suite: `278 failed, 12066 passed`, **0 attributable** (268 are identical at plain HEAD and owned by 64b-i / 63c a28; 8 are owned elsewhere by design; 2 were a scratch artifact). Currency: run 1 caught D-PARSER (fixed). The gate's own later runs were killed by my 15 GB watchdog (its solo policy is `-n auto`), so its three legs were measured separately: typecheck ADJUDICATED · ruff GREEN · pytest at HEAD `e039c64` 521 failed, all in 29 REGISTERED files, **0 orphans** (§CURRENCY D-CURRENCY). **The lead should re-run `--currency` with headroom.**
- **Deviations:** D-AM7KEY (one am-6 probe re-keyed to the class) · D-CTRL (control legs use a real race, not a synthetic instance) · D-SCOPE-A28B (a28b already carries the partition, so §HELD part 2 is smaller) · D-R2CR (r2's CR file deleted, inventoried in R3-D2) · D-BASE (HEAD moved docs-only) · D-REF-BASE (my reference builds on the adversary's ref6) · **D-SHADOW** (a helper name in part 2 shadowed an existing one; caught by typecheck, fixed) · **D-AM9 / D-AM34 / D-AM10 / D-AM10-FAULTS** (the mid-run rulings folded before the one commit) · **D-PARSER** (a whole-tree parse clone; caught by currency, migrated to `parse_production_trees`) · **D-CURRENCY** (the gate's pytest leg was reproduced at `-n 8` + partitioned, because the gate's `-n auto` was killed by the watchdog).
- **Packages considered:** `more_itertools.constrained_batches` → **replace** (BC-r3-1; the builder declares the `more-itertools` dependency). Call graph / stack walk → stdlib `ast` / `inspect` (bespoke test instruments, reused idioms). §Packages considered has the table.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 6 new test-support symbol groups, all dispositioned (3 EXTENDED incl. the ONE walker/resolver `_catch_sites`, the shared tree parser REUSED 4×, 4 HAND-ROLLED with reasons) — §DRY LEDGER.
- **Graded:** n/a (a contract) — measured at `c383edd` → `e039c64` → `4beb79e` (code-identical from `e039c64`; D-BASE / D-BASE2).
- **Decisions needed:** FK-r3-1…7 are RULED (am-9, am-10). Open: am-10 §2 vs §4 on a non-fault translation (I implemented §4, a registered row; D-AM10) · `index/watcher.py::read_events` returns `[]` at DEBUG, am-10 §1's forbidden shape (a pinned hole; its owner decides) · routing: FK-r3-4's 3 drivers and the 8 hole owners · BC-r3-8's timeout value · a `--currency` re-run with host headroom.
- **Receipts:** §FORKS · §REQUIRED-GREEN · §ITEMS · §AST · §DEVIATIONS · §P1c · §DUAL · §BUILDER CONSTRAINTS (esc1 = BC-r3-2, dependency = BC-r3-1) · §ATTACK LIST · §DRY LEDGER · §MUTATION · §RED@HEAD · §SAT · §HELD (part 2 VERBATIM, md5 `986f87df`) · §CURRENCY · §INSTRUMENTS.

## §0 Capability check (brief-base §4), 2026-09-26
- Idle-gate contract: `/tmp/claude-idle-gate-lore/edf4b541-e560-474e-b9d3-47fb8dab87e9-contract-58-r3.contract` = `{"artifact": "REPORT-contract-58-r3.md"}`.
- lore: `ToolSearch "+lore"` loaded 15 tools; registered `contract-58-r3` (session `63c-20260924`, role contract, cadence ≤20m).
- grep/rg are hook-blocked (#473). Every textual sweep in this report is `awk`/`sed`, a fallback said out loud here once. `scripts/` is outside lore's graph (#507).
- Required first read: `docs/reference/surrealdb-31-capabilities.md` §0–§5 (incl. §3 #497 RETURN-in-txn, #501), §4 RELATE.
- Everything the brief demands is reachable (Bash, Read/Write/Edit, lore MCP). One demand is REFUSED on role grounds: see BRIEF CONFLICT.
- **Slip, disclosed:** one `grep -c` in a scratch-only check (the #473 hook let it run). No other grep/rg; every other sweep here is awk.

## BRIEF CONFLICT (brief-base §2 ROLE BOUNDARY — non-overridable)
- The brief's clause *"Every adaptation goes in §DEVIATIONS **with its kill re-proven**"* asks the contract author to re-run the grader's wrong builds (N1–N20, W6a–d) to confirm each now dies. brief-base v17 §2 forbids exactly that transfer (*"contract/test author → grader: … re-running a grader's wrong builds to 'confirm each now dies'"*), and no operator grant is quoted. **Refused.** What I do instead, for every adapted probe: (a) RED@HEAD for the right reason, (b) GREEN on my reference, (c) a mutation proof of MY OWN choosing at the property the pin guards (declare-then-diff), never a replay of the adversary's named build. The delta adversary re-grades its own builds.

## §FORKS — written BEFORE the pins that depend on them
Each fork admits two readings that produce different code (brief-base §2 trigger). I continue on my pick; one native message to the lead names them all.

### FK-r3-1 — am-7 §2 lists `tasks.py::claim_task` in `_TYPED_CAS_CATCHES`, but am-7 §1's own DOMAIN filter excludes it
- **Facts:** am-7 §1: *"Re-read presence is the DOMAIN filter"*, with a28b's derived re-read = *an awaited same-class method whose body carries a `SELECT` literal*, found INSIDE the handler (`test_retry_seam._discover_guarded_cas_handlers` walks `ast.walk(handler)`, measured on the a28b working copy, diff md5 `46427f86`). am-3 §3 rules the claim as `except TxnClaimLostError` with the post-CAS owner read *"as today"* (after the `try`); am-5 REJECTED an inline re-read (FORK-2 Reading A). So a ruled claim has no re-reading handler and is outside the domain. By the same filter, the heal's `except TxnDomainRejectionError: WARNING; continue` is outside it, and am-7 §2 omits the heal (r2 had listed it).
- **Found on the a28b working copy (diff md5 `46427f86`, measured 2026-09-26):** a28b ALREADY lands the partition (`_discover_cas_handlers` → doors / `_discover_typed_cas_catches`, `_TYPED_CAS_CATCHES = {agents.py::register, keeps.py::get_or_create_keyed}`, the union-completeness assertion) per lead #17087, with a comment *"58's §HELD delta adds `tasks.py::claim_task`"*. So 58's delta is smaller than am-7 §3 item 2 describes: the partition, the two moves and the union pin are already in; what is left is the catch forms, the one-resolver pin, the corpse prose, and the runtime↔static cross-check.
- **Reading A (my pick):** the domain filter governs. `_TYPED_CAS_CATCHES` stays a28b's `{agents.py::register, keeps.py::get_or_create_keyed}`. §HELD part 2 REWRITES a28b's *"58 adds claim_task"* comment as a DUAL note saying why it does not. `claim_task` is not listed. Its exhaustion safety is pinned by the driver-seam ∀ (am-8 §3; identity), and its catch-the-TYPE rule by r2's behavioural pin (`RU::…catches_the_TYPE_never_the_text`). A listed `claim_task` would RED every correct build, which is the SAT fragility F5/F8 were about.
- **Reading B:** list `claim_task` as am-7 §2 writes. That needs a domain that admits non-re-reading typed swallows, which contradicts am-7 §1, or a claim that re-reads inline, which am-5 rejected.

### FK-r3-2 — am-7 §4's *"a UNIQUE violation on … RS-5 → exactly one WARNING"* cannot be met: RS-5's CREATE rides `run_query`, which never logs `store.transaction.rolled_back`
- **Facts:** `_log_rollback`'s only callers are in `_run_verified_transaction` (awk over the ref `_txn.py`: two call sites, both inside the transaction attempt/exhaustion path). The a28b fork table (`REPORT-contract-63c-i-a-a28b.md` FK-a28b-1, row R-sdk) measured the agent CREATE's record-id collision *"via `query()` (the run_query path)"*. A `run_query` rejection produces NO rollback record at any level.
- **Reading A (my pick):** pin what the ruling can mean on each path. The **keeps** leg (a `BEGIN…COMMIT` UNIQUE-index collision, a28b U-txn) is a real 8-way race asserting every rollback at WARNING (`TIERS::…[TxnUniqueViolationError-keeps-unique-race]`). For **RS-5**, the class's tier is pinned in the table (`TIERS::test_every_ruled_class_has_its_ruled_tier`) and its producibility through keeps. No RS-5 behavioural leg exists here: the run_query path emits no rollback record, and RS-5's own serve-the-winner behaviour is 63c's pin (a28b K9). Everything that names the class needs 63c-i-a's am-33 build and is owned that way (§CURRENCY).
- **Reading B:** `run_query` gains a rollback log. That is new behaviour nobody ruled, with a 63c-owned blast radius. Not pinned.

### FK-r3-3 — am-8 §3 teaches the static index `with contextlib.suppress(…)`, but a `suppress` site has no handler body, so it can never pass am-7's re-read DOMAIN filter
- **Reading A (my pick):** ONE catch-site walker yields all three forms (`Try`, `TryStar`, a `With` whose context expression resolves BY IMPORT to `contextlib.suppress`). Every site's caught classes are resolved by the ONE resolver `_caught_classes`, extended (am-7 §3 item 4: one resolver, never two). Handler forms feed the re-read domain unchanged. A `suppress` site is a SWALLOW by construction, so it is classified by the closure predicate alone: closure ∋ `TxnContentionExhaustedError` → RED by `file::function` (it swallows exhausted contention, the #102 lie in its purest form); typed → safe and unlisted. Measured at HEAD: 0 store-class `suppress` sites, so no existing red. Discriminators are synthetic sources.
- **Reading B:** list typed `suppress` sites in `_TYPED_CAS_CATCHES`. That would put the F5 claim back into an exact set, where the fork above removes it.

### FK-r3-4 — am-7 §3 item 2: *"every door AND every typed catch has a runtime injection somewhere in the suite"*, yet it routes the missing ones to OTHER owners (*"not 58's file"*)
- **Facts:** the listed set after both landings has `floor_calibration/store.py::record_measurement`, `keeps.py::get_or_create_keyed` and `agents.py::register`. None is a 58 surface, and no injection drives any of them today.
- **Reading A (my pick):** the driver registry is DISCOVERED, not hand-kept in one file. Any test module may declare a module-level `CAS_SEAM_DRIVERS` dict (found by an AST scan of the test tree, then imported). The coverage pin is PARAMETRISED per listed handler and per static CAS verb, so each un-driven one reds BY NAME. The owner adds a driver in THEIR OWN test file, never in 58's. The three reds are owned in `packet-58-contract` with the routing named as their trigger (§CURRENCY). The lead routes them; that is the am-7 §3 wording.
- **Reading B:** 58 writes the three drivers itself. am-7 says not 58's file.

### FK-r3-5 — am-8 §3's call-graph CAS verb: *"some same-module transitive call path from it reaches BOTH the shell and a function that reaches the driver"* also admits every PUBLIC WRAPPER
- **Fact (measured on the ref, prototype `callgraph.py`):** by that wording `findings.py::acknowledge/resolve/wontfix` (each calls only `_transition`) and `tasks.py::ensure_ready` (reaches the heal) are CAS verbs too. The runtime ∀ would then demand an injection under every public wrapper.
- **Reading A (my pick): MINIMAL** — `f` is a CAS verb iff it reaches both, AND no direct callee `g` of `f` itself reaches both. Wrappers fall out; the extract-method refactor (F8) and the helper-applied new verb (N20) stay IN, because their verb calls the shell and a driver-only helper. Receipt: §INSTRUMENTS `derive_cas_verbs` + its synthetic discriminators.
- **Reading B:** the literal transitive wording, where every wrapper needs a driver. Wider registry, same property.

### FK-r3-6 — am-8 F4 *"ONE WARNING PER UNRESOLVABLE ENTRY"*: the cycle record carries `blocker_id` too
- r2 BC-r2-5 required only `task_id` on `task.backfill.straggler_chain_cycle`. am-8 §4 rules one record per unresolvable ENTRY, keyed *"(am-3 §5's `blocker_id` per record)"*. **Pick:** both unresolvable records (phantom, cycle) carry `blocker_id` = the entry, and the per-row records' `blocker_id` set == the row's unresolvable entries. **Other reading:** the cycle record stays per-row with no `blocker_id`, which contradicts the per-entry count.

### RULED — FK-r3-1…6 by packet-58 amendment 9 (`4cb8ce9`), relayed by lead #17098 (acked): ALL SIX picks CONFIRMED
- am-9 withdraws am-4's and am-7 §2's `claim_task` row (erratum). **63c amendment 34 §1 item 1** (`178d236`), which says *"`tasks.py::claim_task` → `_TYPED_CAS_CATCHES` when 58's production lands it"*, predates am-9. am-9 §1 governs, and lead #17098 states the alignment. `claim_task` stays UNLISTED.
- Lead #17094 (acked) + 63c am-34 §5: **the "exactly one scanner function" pin is OWNED by 63c-i-a**. My §HELD part 2 no longer carries `test_exactly_ONE_function_resolves_names_by_import` (see D-AM34). The ONE resolver (`_resolved_by_import`) stays: it is am-9 §3's "ONE resolver".
- am-9 §3 GENERALISES FK-r3-3 into the whole-tree, form-blind SWALLOW RULE, which is folded (below and §HELD part 2). F-r3-1 is ruled into r4. F-r3-3 is ruled `pytest-timeout` (a builder/lead item, BC-r3-8).

### FK-r3-7 (NEW, raised by folding am-9) — am-9 §3's swallow rule is premised on *"a correct build is never RED under it"*, and that premise is MEASURED FALSE at HEAD: 26 pre-existing store-class sites violate it, all outside packet 58
- **Measured 2026-09-26** on the SAT tree (HEAD + a28b + §HELD + my reference; the production modules other than `tasks.py`/`_txn.py` are HEAD's bytes). Instrument: `swallow_measure.py`, pasted §INSTRUMENTS. A catch site whose caught closure contains `TxnContentionExhaustedError`, with no clause catching it ABOVE, and whose body does not end in an unchanged re-raise (no other exit):
  - **Reading (i), literal *"closure ∋ exhaustion"*, which admits `except Exception` / `BaseException` / `suppress(Exception)`: 57 sites** (server shutdown, watchers, the scout loop …).
  - **Reading (ii), am-7 §1's store-class DOMAIN (a caught class inside `SurrealStoreError`'s tree) without the re-read filter: 26 sites.** They are: 17 × `*::_ensure_connection` (bootstrap exhaustion re-raised as `SurrealConnectionError` — a TRANSLATION); `tasks.py::transitive_blockers` and `::_reject_unusable_blockers` (translate); `server.py::_resolve_or_acknowledge_many` (per-item `continue` on exhaustion — a batch fate); `index/indexer.py::_index_chunks` / `_commit_batch_file` / `_resolve_all_extension_edges` (`continue`); `briefs.py::_release_version`; `floor_calibration/store.py::_fence_verdict`; `principals.py::_dispatch_report_unmigrated`.
  - None is 58's code. The 58 reference adds none.
- **Pick (continuing, not a BLOCKER):** Reading (ii), shipped as am-9 rules it (whole tree, form-blind, every catch form) **plus a PINNED KNOWN BOUND** (CLAUDE.md *"WHEN YOU CANNOT CLOSE A HOLE, PIN IT"*): `_KNOWN_EXHAUSTION_SWALLOW_SITES`, the 26, each with a one-line classification, exact BOTH ways. A NEW violator reds by name (this is where am-9 §5's wrapper rider lands). A listed site that stops violating reds with *"delete the entry"*. Re-open trigger: the ruling that decides whether a TRANSLATION of exhaustion (the 19 `raise … from`) is a lie, and which component owns the 7 swallows. **Not decided by me:** whether each is a defect. The pin makes them visible, owned and non-growing.
- **Other reading:** Reading (i) (57 sites, most of them process-lifecycle `except Exception`), or dropping the pre-existing sites from the domain by a hand-list without the both-ways pin. Either one needs a sidecar/lead ruling.
- **Escalated:** one native message to the lead after this entry.
- **RULED — packet-58 amendment 10 (`5b72471`), relayed by lead #17099 (acked). It SUPERSEDES my pick.** The property is *exhausted contention is never a FALSE CLEAR*; the domain is Reading (i); the instrument is a FATE classifier (PASSTHROUGH and TRANSLATE-to-a-fault-`from` DERIVED; every other site a REGISTERED row with classification, owner and AST evidence, exact both ways); none of the 7 swallows is a defect; the home is `test_exhaustion_fates.py` + `_exhaustion_fates.py`, cross-packet. **Folded** (D-AM10, §FATES). My KNOWN-bound pick is withdrawn: nothing of it was committed, and the part-2 swallow rule is gone from `test_retry_seam.py`.

## §REQUIRED-GREEN — correct builds the rulings require green (enumerated FIRST, before any pin was written)
r2's list (`c42eeaf:REPORT-contract-58-r2.md` §REQUIRED-GREEN 1–6) stands. It was measured green again on my reference: r2's 13-file scope + the adversary's probes gave `1172 passed`; the 4 reds are the ones adjudicated in §SAT. r3 adds:
7. **The ruled packer (am-8 §1):** `constrained_batches(items, TXN_STATEMENT_HARD_CAP, get_len=<stored weight>, strict=True)` over rows built ONCE. The sweep pins its exact greedy count (1/1/2 at fit−1/fit/fit+1), which any greedy packer meets.
8. **Any catch spelling (am-8 §3; BC-r2-3/-9 deleted):** a typed catch written as `try`, `try*`, or `contextlib.suppress(<typed class>)`, or placed in an extracted helper, must stay green. Proven by the extract-method CONTROL build **M8**, which must score 0 attributable reds (§MUTATION). The synthetic discriminators prove the `try*` / `suppress` / alias spellings are seen (§HELD part 2 `TestTheCatchFormsAreSeen`, and `TestTheCallGraphDerivationFollowsTheGraphNotTheShape`).
9. **A heal whose per-row weight includes the row's own edge DELETEs and RELATEs**, and whatever fixed per-chunk part the builder composes. The sweep MEASURES `(fixed, weight)` per class off `compose`. It never assumes `fixed == 0`.
10. **A tier table keyed by CLASS** (am-7 §4). Any mapping helper spelling works. The pins read `_txn._ROLLBACK_LOG_TIERS` and the typed classes `_txn` defines; they never read the classifier's internals.
11. **A claim that serves `ClaimResult` from its post-`try` owner read** (FK-r3-1). No inline re-read is required, and `claim_task` is not in `_TYPED_CAS_CATCHES`.
12. **A `run_query` path that logs no rollback** (FK-r3-2). No pin demands a rollback record from RS-5.

## §ITEMS — per worklist item (pin · where · the property it generates over)
Files: `R3P` = `test_reanchor_58_r3_probes.py` · `R3A6` = `test_reanchor_58_r3_am6.py` · `CONV` = `test_reanchor_58_r3_convergence.py` · `TIERS` = `test_reanchor_58_r3_tiers.py` · `REL` = `test_reanchor_58_r3_relate.py` · `SEAM` = `test_reanchor_58_r3_cas_seam.py` · `RU` = `test_reanchor_58_r2_rulings.py` · `SUP` = `_reanchor_58_support.py` · `RS` = `test_retry_seam.py` (§HELD part 2).

| item (source) | pin(s) | generated over (source of truth) · completeness |
|---|---|---|
| **am-8 §2 CLASS** — heal convergence (F1/N3/N15/AM2L) | `CONV::TestOneBootHealsEveryShapeAtTheCapBoundary` (10 classes × {fit−1, fit, fit+1} = 30 legs) + `TestOneBootHealsAMixedPopulation` (2 mixes) + R3P `test_PC_…` (the adversary's hand instance) | SHAPES = the product of the heal's cost ingredients (entries {1,2,3} × heads {distinct, shared} × head {absent, present}). `TestTheShapeSpaceIsNotVacuous` asserts every ingredient value occurs and every fixture realizes its shape. fit is MEASURED per class (1/2/3 rows, linearity asserted), never a literal |
| am-8 §2 edge **F10** (N19) | `CONV::TestARowOverTheCapFailsTheBootLOUD` (typed `StragglerHealPackerError`, names row + weight, NOTHING changes incl. companion rows, twice) + R3P `test_PE_…` | the one impossible shape; the companion rows discriminate a lazy packer (§MUTATION M4) |
| **am-8 §4 F4** (N4/N5) + **am-9 §5** | `CONV::TestAnUnresolvableRowIsSkippedWHOLE` (4 compositions × {phantom, cyclic} = 8 legs, 2 boots each; + am-9 §5's own pin: a row naming {phantom, cyclic, healable} → records {P, C} across BOTH kinds, zero rewrites, uncounted, with the {H}-alone CONTROL) + R3P `test_PD1_`/`test_PD2_` | {one bad, bad+healable, two bad, healable+healable} × {phantom, cyclic}; per-entry `blocker_id` set equality (FK-r3-6) |
| **am-8 §0 (2) F3** (N2) | RU 8-way pin: filter widened to `loremaster` (DUAL R3-D3) + R3P `test_PB_…` | every `loremaster` logger |
| **am-8 §4 F2** + **am-7 §4** + **am-6** (N1, W6a–d) | `TIERS::TestTheTierTableIsKeyedByCLASSAndComplete` (keys are classes == every typed `TxnDomainRejectionError` subclass `_txn` defines, both ways; ruled tier per class; trigger registry == ruled classes) · `TestEachClassRollsBackAtItsTier` (8 generated (class, trigger) legs incl. PA1, PA2, the heal chunk, keeps UNIQUE) · `TestTheEngineAndTheDriverStayAtERROR` (ASSERT, coercion, real exhaustion via a forged always-retryable wire) · `TestDroppingOneKeyMovesOnlyThatTier` (6 generated mutation legs + a sibling unchanged) + R3A6 (adversary's am-6 probes; one re-keyed, D-AM7KEY) + R3P PA1/PA2 | the typed classes `_txn` defines (derived by `__subclasses__`), the ruled table (am-7 §0 row 3) as oracle |
| am-6 FORK-4 **E11** (W6c) | R3A6 `test_P6_E11_…` ×2 (AST-equal) | the adversary's fixture, through supersede and through the heal |
| **am-8 §4 F11** (N17) | `REL::TestTheRELATEVerbsAreDerivedAndDriven` (registry == derived, both ways) + `TestEveryComposedRELATECameFromTheSharedFragment` (5 legs) | RELATE verbs DERIVED by the SAME call-graph walk as the CAS verbs, seeded on `_relate_fragment` (`SUP.cas_verbs_in(…, shell=…)`); it found `_backfill_blocks_edges` too, which am-8's list did not name |
| **am-8 §3 F5/F8/N20** + **am-7 §3 item 2** | `SEAM::TestTheCASPopulationIsDrivenBothWays` (per member: graph verbs ∪ listed handlers ∪ discovered drivers; undriven → RED by name, stale → RED) · `TestExhaustedContentionReachesTheCallerAsTheSAMEInstance` (7 drivers: identity + the real lost-race control + runtime writer attribution ⊆ graph, own verb observed) · `TestTheCallGraphDerivationFollowsTheGraphNotTheShape` (synthetic: inline + extracted verbs derived, wrapper/read-only/fragment-only not) · `TestTheIdentityAssertionDiscriminates` (passthrough passes; translate + swallow caught) | STATIC = `SUP.derive_cas_verbs` (call graph, WHOLE tree, MINIMAL — FK-r3-5) ∪ `RS._GUARDED_CAS_DOORS ∪ _TYPED_CAS_CATCHES`; DRIVEN = every test module's `CAS_SEAM_DRIVERS` (FK-r3-4) |
| am-8 §3 catch forms · **am-9 §3 → am-10 the FATE rule** · am-8 §6 corpse · am-9 §1 claim DUAL | **committed:** `test_exhaustion_fates.py` (+ `_exhaustion_fates.py`, `_catch_sites.py`): registry exact both ways · every row's classification/owner/evidence HOLDS (a pinned hole that gains evidence reds too) · the UNLOGGED hole set pinned · the fault allowlist exact · 8 positive-control shapes · the indexer SIBLING bound + trigger proxy. **§HELD part 2:** test_retry_seam's resolver IMPORTED from `_catch_sites` (identity pin), the TryStar partition, the §8c header (DUAL), a28b's claim comment (DUAL) | every catch site in the production tree (Reading (i), 74 at `4beb79e`), each form; ONE walker, ONE resolver |
| am-10 §3 **indexer SIBLING** | `test_exhaustion_fates::TestTheIndexerStoreFailureReasonIsOneReasonForTwoCauses` (a KNOWN BOUND pin that reds when either half moves, + the trigger proxy: the reason's name/value occur only in `indexer.py`) | the two per-file store handlers; every production module |
| am-8 §1 **P-PKG** | BUILDER CONSTRAINT BC-r3-1 (the contract cannot demand a library; it pins the packer's greedy behaviour) | — |
| am-8 §5 **esc1** | BUILDER CONSTRAINT BC-r3-2 | — |
| am-7 §3 item 3 (mutations agree across layers) | §MUTATION M7/M9/M10 are the runtime-side and static-side legs | — |

**A 4th instance of either routed property?** No. Every heal-sizing and CAS-population shape the adversary named (N3, N15, AM2L, F5, F8, N20, F6, F7) is a member of a domain these pins GENERATE. No new ingredient was found, so there is no escalation to the ruling (amendment 8 §7).

## §AST — the landed probes are AST-EQUAL to the adversary's (am-17's rule), with controls (2026-09-26)
Instrument: contract-58-r2's `ast_receipt.py`, extracted verbatim from `c42eeaf:REPORT-contract-58-r2.md` §INSTRUMENTS. Its md5 `880d05f7` equals the recorded value. The adversary files come from `821be62:REPORT-adversary-58-r2.md` §INSTRUMENTS, each md5 equal to its recorded value: `test_adv58r2_probes.py 55aac187` · `test_adv58r2_probes_e.py 439570bc` · `test_adv58r2_am6_probes.py d3f96789`.
```
EQUAL     test_reanchor_58_r3_probes.py::_levels
EQUAL     test_reanchor_58_r3_probes.py::test_PA1_a_lost_SUPERSEDE_race_logs_its_rollback_at_WARNING
EQUAL     test_reanchor_58_r3_probes.py::test_PA2_an_R1_straggler_rollback_logs_at_WARNING
EQUAL     test_reanchor_58_r3_probes.py::test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger
EQUAL     test_reanchor_58_r3_probes.py::test_PC_stragglers_naming_TWO_superseded_blockers_at_scale_heal_in_ONE_boot
EQUAL     test_reanchor_58_r3_probes.py::test_PD1_a_MIXED_row_phantom_head_plus_healable_blocker_is_skipped_WHOLE
EQUAL     test_reanchor_58_r3_probes.py::test_PD2_a_MIXED_row_cyclic_chain_plus_healable_blocker_is_skipped_WHOLE
EQUAL     test_reanchor_58_r3_probes.py::test_PE_a_single_straggler_that_alone_exceeds_the_cap_fails_the_boot_LOUD_and_changes_nothing
EQUAL     test_reanchor_58_r3_am6.py::_rollback_levels
EQUAL     test_reanchor_58_r3_am6.py::test_P6_each_ruled_tier_and_the_deny_by_default
DIFFERENT test_reanchor_58_r3_am6.py::test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier   ← D-AM7KEY (deliberate)
EQUAL     test_reanchor_58_r3_am6.py::test_P6_E11_a_legacy_duplicate_collapses_WHOLE_column_and_the_claim_then_wins
EQUAL     test_reanchor_58_r3_am6.py::test_P6_E11_through_the_boot_heal
controls OK: re-wrap EQUAL (_levels); one-token mutation DIFFERENT (test_PA1_…)                    [probes]
controls OK: re-wrap EQUAL (test_PE_…); one-token mutation DIFFERENT (test_PE_…)                    [probes_e]
controls OK: re-wrap EQUAL (_rollback_levels); one-token mutation DIFFERENT (test_P6_each_ruled_tier…) [am6]
```
**13 of 14 landed AST-EQUAL; 1 deliberately re-keyed.** Lint rewraps were `ruff format` plus comment reflows only. Comments are invisible to the AST, and implicit string concatenation folds to ONE `Constant`, so the rewraps are admitted by construction and the EQUAL lines above are measured AFTER them. Only the module docstrings and import blocks differ (merged: the three adversary files land as two). The trailing `_UNUSED` tuples are dropped, since they are not functions.

## §DEVIATIONS
- **D-AM7KEY** — `R3A6::test_P6_mutation_dropping_ONE_table_entry_moves_ONLY_that_tier` drops `getattr(_txn, "TxnCasLostError")`, never the string `"cas_lost:"`. amendment 7 §4 (`01565f9`) re-keys `_ROLLBACK_LOG_TIERS` from marker PREFIX to CLASS, so the verbatim `table.pop("cas_lost:")` is a `KeyError` on every am-7-faithful build. Measured: `KeyError: 'cas_lost:'` on my reference, `§SAT` baseline log. What it pins is unchanged: drop one table entry, and that tier falls to ERROR while a sibling stays. **Kill proof (my own mutation, per BRIEF CONFLICT):** §MUTATION M6 (a table keyed by class NAME string) reds it; the class-keyed reference greens it.
- **D-CTRL** — am-8 §3 item 4 says the control leg is *"injected the same way with the verb's own THROW class"*. `SEAM`'s control legs instead drive a REAL lost race through the real driver, carried from r2's CR drivers. That produces the verb's own THROW class at the same seam, which is a stronger control than a synthetic instance, because it proves the THROW is authored and classified for real. Reading B (inject a fresh `TxnCasLostError` etc. at the seam) was not taken. A re-reading door (findings `_transition`) would re-read an UNCHANGED row after a synthetic domain rejection, and its verdict would then depend on its re-read logic rather than on the injected class.
- **D-SCOPE-A28B** — the brief anticipates *"the partition, the moves, the union completeness pin"* as 58's delta. a28b's working copy (md5 `46427f86`) already carries all three (lead #17087). §HELD part 2 is therefore smaller: catch forms, one resolver, corpse prose, and the claim_task comment. The runtime↔static cross-check lives in `SEAM`, a NEW file, not in `test_retry_seam.py`.
- **D-R2CR** — `test_reanchor_58_r2_cas_runtime.py` is DELETED (`git rm`), and `SEAM` replaces it. The removed-behaviour inventory is §DUAL R3-D2. Its pending-contract row is removed with it (§CURRENCY).
- **D-BASE2 — a28b COMMITTED mid-run as `e039c64`** (after `0f69efa`, a 64b report). Its committed `test_retry_seam.py` differs from the working copy I built on (md5 `46427f86`) by exactly ONE line (`doors: dict[str, tuple[str, int, bool, bool]]`, a typing fix inside the block my part 2 replaces). So part 2 was REBASED onto the committed file. The resulting file is byte-identical to the one SAT and §MUTATION ran (`rs_final.py`), and the new part 2 is md5 `6f3b97f5`, with `git apply --check` OK **directly on HEAD `e039c64`**. The registry edit was re-applied onto the COMMITTED a28b registry (the index is built from `HEAD:scripts/pending_contracts.yaml` at `e039c64`, never from the older blob, which would have reverted a28b's entry). RED@HEAD and the currency legs were RE-MEASURED at `e039c64` (§RED@HEAD addendum, §CURRENCY addendum).
- **D-BASE** — HEAD moved `c9e5eb8` → `c383edd` during the run (docs only: `git diff --stat c9e5eb8 c383edd -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock` is empty). The file headers say `c9e5eb8`, and every measurement holds at `c383edd`.
- **D-SHADOW (self-caught, before any commit)** — my first §HELD part 2 defined a helper named `_production_modules`. That name already exists in `test_retry_seam.py` as a DIFFERENT function (the `can be retried` marker scan, which returns paths), so my definition silently SHADOWED it for every later lookup. Three older pins in `TestNoCallerEverReadsAnEngineMessage` would have iterated tuples as paths. The CatchForms-scoped runs could not see it, because those pins sit outside that scope. `scripts/typecheck.sh` on the built tree caught it (`Name "_production_modules" already defined on line 3640 [no-redef]`, plus `"Path" object is not iterable`). The helper is renamed `_production_module_trees`. Part 2 was regenerated (then md5 `375ec0f7`, was `90f8f784`; final `131e505f` after D-PARSER) and re-checked (`git apply --check` OK on the shared tree and on clean HEAD + a28b). The rs-scope mutations M10/M13/M14 were re-run after the rename, all EXACT. ruff did not flag the redefinition, so mypy is the instrument of record for this class. **Lesson, askable:** *"does a NEW module-level name in a shared file already exist in it?"* — the §SAT full suite is the second check.
- **D-PARSER (caught by the currency gate on HEAD + this commit, before committing)** — `--currency` came back `pytest RED_ORPHANED — 1`: `test_ast_reach_helpers::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` flagged `test_reanchor_58_r3_cas_seam.py::discovered_drivers` as a hand-rolled whole-tree parse (finding #279/F4: THE ONE tree parser is `_logging_fixtures.parse_production_trees`). All three of my whole-tree scans now route through it: `SEAM.discovered_drivers` (`include_tests=True`, filtered to the test dir), `SUP.derive_cas_verbs` (`include_scripts=False`, filtered to the package prefix — not flagged, because `_reanchor_58_support.py` is not a `test_*.py`, but it is the same law), and §HELD part 2's one-resolver pin (`include_scripts=True, include_tests=True`, filtered to test trees + scripts; `test_retry_seam.py` is allowlisted, but its allowlist reason says "loremaster-scoped" and a test-tree meta-scan would have drifted from it). Receipt: `test_ast_reach_helpers.py` + `SEAM` + `REL` on the SAT tree → `3 failed, 75 passed, 4 skipped` (the 3 = FK-r3-4's rows); part 2 regenerated, md5 `131e505f`, `git apply --check` OK on both bases. **Askable:** *"does my new scan parse a DIRECTORY?"* — then it goes through the one parser.
- **D-AM34 (lead #17094, 63c am-34 §5; acked)** — my §HELD part 2 had carried `test_exactly_ONE_function_resolves_names_by_import` (am-7 §3 item 4). 63c am-34 §5 assigns that pin to **63c-i-a** (born with the scanner, allowlist-the-safe over *"walks ast over production files AND names a `_txn` store class"*). It is REMOVED from part 2. It was never committed; only the `held_part2.py` draft carried it (M13 retired with it). The ONE resolver it guarded (`_resolved_by_import`) STAYS: that is am-9 §3's "ONE resolver".
- **D-AM9 (fold, before the one commit)** — packet-58 am-9 (`4cb8ce9`) landed at HEAD while this contract was being staged (lead #17098, acked). Folded: the swallow rule is generalised from my suppress-only pin to the whole-tree, form-blind rule over every catch form (`_swallow_sites_in` + `_reraises_unchanged`, one walker), with the FK-r3-7 KNOWN bound. am-9 §5's own {P, C, H} pin was added. F-r3-1 is recorded as r4's and F-r3-3 as BC-r3-8. Receipts: on the SAT tree `test_retry_seam.py` + `test_ast_reach_helpers.py` → `2 failed, 722 passed, 4 skipped` (the 2 = a28b's own); CONV on the ref → `44 passed`; §MUTATION M10/M14/M16/M17 and the re-declared M2 are all EXACT.
- **D-AM10 (fold, before the one commit)** — the FATE classifier lands as NEW committed files, not in §HELD:
  - `_catch_sites.py` holds THE ONE walker/resolver, extracted from my part-2 `_resolved_by_import`/`_caught_classes`/`_suppress_calls`; test_retry_seam now IMPORTS them via §HELD part 2, proven by identity in `test_this_index_resolves_through_THE_ONE_resolver`, M23.
  - `_exhaustion_fates.py` holds the registry: 32 keys / 37 rows, 8 pinned HOLE keys.
  - `test_exhaustion_fates.py` holds the classifier, the 8 evidence predicates, the positive controls, and the indexer SIBLING bound (am-10 §3) with its trigger proxy.
  - It is GREEN at HEAD `86a55eb` (`16 passed`) and on the 58 reference (`16 passed`), so it needs no pending-contract row.
  - My part-2 swallow rule + KNOWN bound (the am-9 draft) were REMOVED from part 2.
  - **Reading of am-10 §2 vs §4, stated:** §2 says *"a translation to any other class → RED by name"* and §4 says the non-derived *"rest get a row"*. I implement §4: a translation to a NON-fault class is non-derived, so it needs a row whose evidence holds (`raises-chained` exists for that). Unregistered, it reds by name. A door translation into a domain verdict therefore reds unless someone writes a row claiming it, and that row is reviewer-visible. The other reading (hard RED, no row possible) would red the three lifecycle translations (`run_probe_gate` → `ProbeGateError`, `_count_live_total` → `_ProbeUnavailableError`, `_eager_build_or_operator_safe_error` → `RuntimeError from None`, all logged) with no way to adjudicate them.
- **D-AM10-FAULTS** — am-10 §2's allowlist names `MemoryBackendError`. **No such class exists** (measured 2026-09-26: `loremaster.memory` and `loremaster.memory.local` define none; `memory.local.remember`'s handler is PASSTHROUGH for exhaustion, and its only translation is under an `isinstance(error, TxnGovernedConflictError)` guard, which the classifier prunes). So `FAULT_CLASS_NAMES` = the other 8, pinned exact. A class-name derivation ("every direct `RuntimeError` subclass") was measured and REJECTED: it admits `agent_existence.UnknownRowError`, a not-found VERDICT.
- **D-REF-BASE** — my reference starts from the adversary's ref6 (`build_ref58.py` + `my_ref.py` + `my_ref_am6.py`, each md5-verified; result md5 `tasks.py 12917da9` / `_txn.py 8c748e4f` / `findings.py 48d8fd7a` = the adversary's recorded values). My am-7/am-8 deltas go on top (`my_ref_r3.py`, pasted §INSTRUMENTS). It is NOT independent of the adversary's reference in its am-1..am-6 half. It is independent in its am-7/am-8 half.

## §P1c — REACH (every guard / scan r3 introduces or relies on; INSTRUMENT-0's question asked of each)
| instrument | set it covers | derived or hand-list? | coverage a checked variable? | effect or proxy? | verdict / named bound |
|---|---|---|---|---|---|
| `SUP.derive_cas_verbs` / `cas_verbs_in` (call graph) | every production module's functions | DERIVED (whole-tree `rglob`; driver seam resolved BY IDENTITY; shell = the ruled name) | synthetic discriminators (inline/extracted derived; wrapper/read-only/fragment-only not); production non-vacuity floor (findings `_transition`/`annotate`) | proxy (source), cross-checked against the EFFECT twin below | bounds: functions keyed by NAME per module (RS-6); dynamic dispatch invisible — the runtime leg names it (§MUTATION M9) |
| `SEAM.DriverSeamInjection` (identity) | every call of `_txn.execute_transaction`/`run_query` through ANY binding in any loaded `loremaster` module | DERIVED bindings (by identity) + a non-vacuity assert (≥ the `_txn` binding) | the population pin: STATIC ⊆ DRIVEN and DRIVEN ⊆ STATIC, per member | **EFFECT** (what reaches the caller) | bound: a write that reaches the SDK without either seam is the R4 `_sdk_guard`'s territory; a runtime gate covers only what its drivers RUN — hence the population pin |
| `SEAM` runtime writer attribution | every write whose guard the shell built during a driver's run | DERIVED (deepest frame common to the shell's stack and the send's stack; frames HELD so no id is reused) | observed ⊆ graph (blind spot named) and own verb ⊆ observed | EFFECT | bound: a CAS whose guard is NOT built by the shell is invisible here (the one-producer pin forbids that shape); cross-task shells (a gather between build and send) unattributed |
| `SEAM.discovered_drivers` | every `loremaster/tests/test_*.py` | DERIVED (AST scan for the registry NAME, then import) | a verb registered twice reds | proxy | bound: a registry under another name is not found — the name is the documented convention |
| `CONV` shape sweep | straggler cost classes × scale | DERIVED product of the heal's ingredients | every ingredient value occurs; every fixture realizes its shape; fit MEASURED per class | EFFECT (compose spy + columns + edges + INFO) | bound: the ingredient list is the heal's cost dimensions as ruled (am-8 §2); a NEW per-row statement kind is a change to the builder's fragment set — the measured weight absorbs it, a new COST DIMENSION needs a new ingredient (am-8 §2 litmus) |
| `CONV` F4 composition sweep | {one bad, bad+healable, two bad, healable+healable} × {phantom, cyclic} | generated | per-entry `blocker_id` SET equality | EFFECT | — |
| `TIERS` completeness | typed domain-rejection classes | DERIVED (`__subclasses__` of `TxnDomainRejectionError` defined in `_txn`) | both ways; ruled tiers as oracle; trigger registry == ruled classes | proxy + EFFECT legs | bound: a typed class defined OUTSIDE `_txn` is not in the domain (none exists) |
| `TIERS` per-class legs | 8 (class, trigger) pairs | registry, completeness-checked against the ruled table | each leg counts its rollbacks exactly | EFFECT (caplog on the real driver) | FK-r3-2: RS-5 has no behavioural leg (run_query logs none) |
| `REL` | RELATE-composing verbs | DERIVED (same walk, seed `_relate_fragment`) | registry == derived both ways; each leg non-vacuous | EFFECT (compose ∩ fragment spy) | — |
| `_catch_sites` walker + `FATES` classifier (am-10) | every catch site in production — `try`, `try*`, `suppress` — whose closure reaches exhaustion (Reading (i)) | DERIVED (one walker, one resolver, by import; the tree through THE ONE parser) | registry exact both ways; evidence per row checked; hole set pinned; 8 positive-control shapes; non-vacuity (all three fates occur) | proxy (source) — its EFFECT twin is `SEAM`'s identity leg for CAS verbs | bounds: `_exits` prunes only `isinstance(<caught>, C)` guards (other disjoint-type guards are unseen → a row is required); `logger.log(level, …)` does not count as a loud log; `_returns_named_outcome` is a text heuristic |
| one-scanner pin | — | — | — | — | **not 58's**: owned by 63c-i-a (63c am-34 §5; D-AM34) |
| RU 8-way F3 filter (edited) | every `loremaster` logger | prefix | — | EFFECT | — |

## §DUAL — r3's removed / changed-behaviour rows (continuing r2's numbering)
| row | behaviour (old → new) | adjudication |
|---|---|---|
| **R3-D1** | `SUP.derive_cas_verbs`: a shell-ledger METHOD that literally calls `self._apply` and reaches the shell, inside `SHELL_LEDGER_MODULES = ("tasks.py", "findings.py")`, ∪ `SINGLE_STATEMENT_CAS_DOORS = ("briefs.py::_relate_briefed",)` → the MINIMAL call-graph verb over the WHOLE tree (seam by identity). `SHELL_LEDGER_MODULES`, `SINGLE_STATEMENT_CAS_DOORS`, `APPLY_SEAM` are DELETED (only consumer: the deleted r2 CR file, measured by awk). | am-8 §3 (F5/F6/F8/N20). Removed-behaviour: (a) the module hand-list — DROPPED DELIBERATELY (am-8 §3 "No hand-listed module set survives"); (b) the named briefs door — PRESERVED-WITH-PIN via the listed handlers (`RS._GUARDED_CAS_DOORS` names it, a28b's derived scanner finds it) — `SEAM` population row `briefs.py::_relate_briefed`; (c) `_apply` shape key — DROPPED DELIBERATELY (am-8: "no instrument may dictate the shape"). |
| **R3-D2** | `test_reanchor_58_r2_cas_runtime.py` DELETED → `test_reanchor_58_r3_cas_seam.py` | inventory, each leg: **(1)** registry == derived both ways → PRESERVED-WITH-PIN (`SEAM::TestTheCASPopulationIsDrivenBothWays`, now per member and over graph ∪ listed ∪ discovered — am-8 §3 item 3); **(2)** injection at `_apply` (the verb's own seam) → RE-HOMED to the driver seam (am-8 §3 item 1); **(3)** `seam_calls_after == 0` (no ledger retry) → PRESERVED by identity (a retry that then succeeds returns normally → "SWALLOWED"; one that fails differently → "REINTERPRETED"); **(4)** `reads_after == 0` → DROPPED DELIBERATELY (am-8 §3 item 2 rules IDENTITY as the assertion; a re-read that still re-raises the same instance tells no lie); **(5)** the real lost-race control per verb → PRESERVED verbatim in behaviour (all 7 drivers); **(6)** `TestTheRuntimeSetAndTheStaticIndexAgree` (listed ⊆ driven; driven ⊆ classified-by-function) → PRESERVED-WITH-PIN as the population pin (listed ⊆ driven) + runtime attribution ⊆ graph; its "driven ⊆ classified" leg (RS-5 of adversary-58-r2: over-tight in the F5 direction) → DROPPED DELIBERATELY (am-8 §3: the static index is reviewer-visible, no longer the ∀). |
| **R3-D3** | RU `test_an_8_way_race_logs_NO_warning_or_error_for_its_7_losers`: loud filter `loremaster.store` → `loremaster` | am-8 §0 row (2) F3 reading (b); DUAL comment in place |
| **R3-D4** (§HELD part 2) | RS §8c header prose (re-read by `_select` prefix, "the population is DISCOVERED …") → the a28b domain + the am-7 partition + catch forms + the bound, stated | am-8 §6 (adversary F6 corpse); DUAL comment in place |
| **R3-D5** (§HELD part 2) | RS `_caught_classes(handler)` → `_caught_classes(site)` over handlers AND `suppress` calls, through the ONE `_resolved_by_import`; `_discover_cas_handlers` walks `Try` AND `TryStar`, per module via `_cas_handlers_in` | am-8 §3 (catch forms) + am-7 §3 item 4; every a28b pin unchanged and green on the SAT tree (the two a28b reds are its own, §SAT) |
| **R3-D6** (§HELD part 2) | a28b's comment *"58's §HELD delta adds `tasks.py::claim_task`"* → a DUAL note that it does not | FK-r3-1 |
| **R3-D7** | am-6's PREFIX-keyed tier table (r2 adversary's W6 pins) → am-7's CLASS key | D-AM7KEY; `TIERS` completeness |
| **R3-D8** | BC-r2-3 / BC-r2-9 (claim `try` shape; heal `try` must not move to a helper) | DELETED by am-8 §3; §BUILDER CONSTRAINTS says so |
| **R3-D10** | (draft only, never committed) my am-9 part-2 swallow rule + KNOWN bound → am-10's FATE classifier in `test_exhaustion_fates.py` | am-10 supersedes; D-AM10 |
| **R3-D9** | r2's heal packer "hand-rolled greedy" (BC-r2-2's packer half) | am-8 §1: `constrained_batches` (BC-r3-1). The ONE-counter half of BC-r2-2 stands |

## §BUILDER CONSTRAINTS (r1 1–9 and r2 BC-r2-1/-2/-4/-5/-6/-7/-8 stand; **BC-r2-3 and BC-r2-9 are DELETED** by am-8 §3; r3 adds)
- **BC-r3-1 (am-8 §1 — the packer + the DEPENDENCY):** the heal packer IS `more_itertools.constrained_batches(items, TXN_STATEMENT_HARD_CAP, get_len=<the stored weight>, strict=True)`. `items` = `(row, fragments, weight)` built ONCE per straggler; the fragments are carried into the chunk and never rebuilt. `weight` = the ONE counter (`_composed_statement_count(fragments)`, shared with the supersede accessor — BC-r2-2), and it includes the row's own edge DELETE(s) and RELATE(s). The `ValueError` from `strict=True` is caught at the ONE call site and re-raised as `StragglerHealPackerError`, naming the row and its weight. **The batches are MATERIALIZED before any apply**, so an over-cap row changes NOTHING (`CONV` F10, §MUTATION M4). **`more-itertools` becomes a DECLARED direct dependency of `loremaster`** (today transitive only, 11.1.0 in `uv.lock` via `jaraco-*`): `uv add --package loremaster more-itertools`, which updates `loremaster/pyproject.toml` + `uv.lock`. It is pre-approved (project package, CLAUDE.md), NOT edited by this contract. Receipt: the reference imports it and the whole r3 scope is green (§SAT). The builder's `Packages considered:` line names it as `replace`.
- **BC-r3-2 (am-8 §5 — esc1, OWNER = the 58 builder):** `scripts/esc1_write_path_cycle_closure.py` has been red since #174. RE-KEY its scenario to the current contract (#174's inherit/`[]`/`[ids]` sentinel + 58's re-anchor + am-3 §4's "refuse only a cycle through X′"; r1 §FLAGS 1's `(await ledger.supersede_task(…)).successor_id`), then re-run it as a receipt in the build report. If the scenario is no longer expressible, ARCHIVE the script under `docs/plans/v2/receipts/…` with a DUAL header naming what replaced it. Never leave it red; never delete it silently.
- **BC-r3-3 (am-7 §4):** `_txn._ROLLBACK_LOG_TIERS` is keyed by the CLASSIFIED CLASS: `{TxnClaimLostError: DEBUG, TxnGovernedConflictError / TxnCasLostError / TxnReanchorStragglerError / TxnHealChunkError / TxnUniqueViolationError: WARNING}`. Every other class and exhaustion fall to ERROR. `_log_rollback` receives the class. The three NEW 58 classes (`TxnCasLostError`, `TxnReanchorStragglerError`, `TxnHealChunkError`) subclass `TxnDomainRejectionError` in `_txn` and are produced by the ONE classifier from the `cas_lost:` / `reanchor_straggler:` / `heal_chunk:` markers (am-6). Every typed subclass defined in `_txn` MUST have a tier (the completeness pin reds an unclassed one).
- **BC-r3-4 (am-8 §4 F4):** a row with ≥ 1 unresolvable entry is skipped WHOLE and uncounted, with ONE WARNING PER UNRESOLVABLE ENTRY. Both `task.backfill.straggler_phantom_head` AND `task.backfill.straggler_chain_cycle` carry `task_id` and `blocker_id` (FK-r3-6). Do not `break` after the first bad entry.
- **BC-r3-5 (am-8 §3):** any catch spelling (`try`, `try*`, `contextlib.suppress`, an extracted helper) is legal. What is pinned is that the injected exhausted-contention INSTANCE reaches the caller. **A `suppress` whose class closure contains `TxnContentionExhaustedError` is RED by name** (§HELD part 2).
- **BC-r3-6 (FK-r3-4 — the lead's routing, not the builder's):** the `SEAM` population rows for `floor_calibration/store.py::record_measurement`, `keeps.py::get_or_create_keyed` and `agents.py::register` stay RED until their OWNERS add a `CAS_SEAM_DRIVERS` entry in their own test modules. The 58 builder must not add them to 58's file (am-7 §3 item 2).
- **BC-r3-8 (am-9 §6 F-r3-3 — `pytest-timeout`; a builder/lead item, like BC-r3-1's dependency):** `uv add --dev pytest-timeout`, a generous suite default in `pyproject.toml` (the NUMBER is the lead's, from the measured slowest test), `timeout_method = "signal"`, and `@pytest.mark.timeout(<tight>)` on `CONV`'s cyclic F4 legs and am-9 §5's pin. It is NOT added in this commit: an unregistered `timeout` mark is a no-op wearing a guard's name (the plugin is not installed at HEAD). Whoever adds the plugin adds the marks in the same change.
- **BC-r3-9 (am-9 F-r3-1 — r4):** the generated marker-vocabulary pin (each marker `_txn` classifies appears only in `_txn` and as the PREFIX of a THROW-message constant) is ruled for r4, not this revision.
- **BC-r3-10 (am-10 §4 — the fate registry is CROSS-PACKET):** 58's build lands nothing more for it (committed here, green at HEAD). Every future packet that adds a catch site reaching exhausted contention either makes it PASSTHROUGH / TRANSLATE-to-a-fault-`from`, or adds a row in `_exhaustion_fates.py` whose evidence HOLDS. Each row's OWNER fixes its own hole; the 8 `UNLOGGED_SITES` keys are the owners' one-line fixes (am-10 §4), routed by the lead.
- **BC-r3-7 (cross-packet, 64b):** 64b-i merges `findings.py::_transition` + `annotate` → `_run_guarded`. The call graph then derives the new name, and `SEAM`'s two findings drivers go STALE by name. Whoever lands SECOND re-keys them (the drivers' bodies stay; only the keys and the armed verb move).

## §ATTACK LIST — for the delta adversary (where I would look first; not graded by me)
1. **The sweep's ingredient set** (`CONV.ENTRIES/HEADS/HEAD_PRESENT`). Is there a per-row cost dimension the heal has that these three do not span? Candidates I did not generate: a row naming the SAME legacy blocker twice (`[L, L]`, E11's shape at scale); a head that is itself `done`/`wontfix` (am-1's reblock path); rows with > 3 entries (k = 3 is the "k" of am-8 §2). Is any of them a new cost CLASS, or only a new weight value (which the measurement absorbs)?
2. **`fit` is measured on 1/2/3 rows and extrapolated linearly.** A builder whose weight is linear on small n but not at scale (a per-chunk fixed part that grows) is caught only by the exact-chunk assertion at fit±1. Is there a packer that meets 1/1/2 at fit−1/fit/fit+1 yet overflows at 2·fit+1?
3. **The mixed sweep checks greedy closure ORDER-FREE** (every chunk but the smallest > cap − heaviest). A non-greedy packer that still satisfies that bound?
4. **`SEAM` runtime attribution** keys the WRITE to the deepest frame common to the shell stack and the send stack, per asyncio task. A verb that builds its guard in one task and sends it from another (`gather`/`create_task`) is unattributed. Is any production verb shaped so?
5. **The injection flags the FIRST armed-seam call under the verb's frame.** A verb whose first write is NOT its CAS (a pre-write, e.g. an audit row) would be injected at the wrong statement. The identity leg still holds, but it pins the wrong write. Which verbs issue > 1 write?
6. **Minimal CAS verb (FK-r3-5).** A verb that calls TWO CAS helpers (each reaching both) is itself excluded, and each helper is driven through it only if its driver arms the helper's frame. Can a wrong build hide an unguarded door in such a parent?
7. **`discovered_drivers` imports every module declaring `CAS_SEAM_DRIVERS`.** A driver in another module that arms the WRONG verb, or returns before arming, would satisfy the population pin. The identity leg only runs for THIS file's registry (`sorted(CAS_SEAM_DRIVERS)`), not for discovered ones.
8. **`TIERS` completeness derives the domain from `__subclasses__` in `_txn`.** A 58 build that raises a typed class defined in `tasks.py` instead would escape the completeness pin (its trigger leg would still log ERROR and red, if a trigger exists).
9. **The one-resolver pin keys on `ast.Expression(`**, which is a stated bound. A second scanner resolving via `getattr(module, name)` walks is unseen.
10. **FK-r3-1..6** are my picks, not rulings. Each is a place a sidecar ruling could invert a pin.
12. **The fate classifier's `_exits` / `derived_fate`** (formerly the am-9 swallow rule's `_reraises_unchanged`) treats a handler as passing exhaustion through iff its body ENDS in a bare `raise` (or `raise <as-name>`) with no other exit. A handler that re-raises unchanged on its last line but MUTATES state first (e.g. rolls something back, which is still a reinterpretation of a kind) is judged safe. Is that a door?
13. **Registry rows are keyed `file::function` + an ORDINAL among that function's non-derived sites.** A new non-derived site inside a registered function changes the count and reds, but a site MOVING within the function could shift which row checks which evidence. Is there a swap that keeps every evidence check green?
14. **The evidence predicates are textual heuristics** (`marks-failed` = a call whose name contains `fail` or an arg containing `FAILED`; `returns-named-outcome` = a return whose text mentions fail/unavailable/error or is `1`). Can a silent site satisfy one by accident?
11. The keeps UNIQUE leg asserts only "≥ 1 rollback, each at WARNING" over up to 20 rounds. Is there a build where keeps logs WARNING for the conflict but ALSO an ERROR from another loremaster logger? The leg reads only `store.transaction.rolled_back`.

## §DRY LEDGER (brief-base §6 — new reusable symbols; test-support only, no production symbol)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `SUP.derive_cas_verbs` (rewritten) + `SUP.cas_verbs_in` | awk over the test tree + the r2 support module (lore_search not used — see note) | r2's shape-keyed `derive_cas_verbs` (same module); `_logging_fixtures.parse_production_trees` (THE ONE tree parser) | **EXTENDED `_reanchor_58_support.derive_cas_verbs`** in place, and its tree walk **REUSES `_logging_fixtures.parse_production_trees`** (D-PARSER). `cas_verbs_in` is the per-module body split out, and REL reuses it with `shell=` (one walker, two seeds) |
| `SEAM.DriverSeamInjection` | awk over `loremaster/tests` for `_degrade_every_STORE_seam` / `Injection(` | `test_blocks_edge._degrade_every_STORE_seam` (tasks-only, replaces ALL `_txn` coroutines, no stack attribution); r2's `Injection` (per-verb `_apply`, deleted with R3-D2) | **HAND-ROLLED**: the existing helper is tasks-scoped and cannot flag a call by stack or observe the shell; r2's `Injection` is the thing am-8 retires |
| `SEAM.discovered_drivers` | awk for `CAS_SEAM_DRIVERS` | no registry-discovery helper exists; the parse REUSES `parse_production_trees` | discovery **HAND-ROLLED** (the FK-r3-4 mechanism), parse **REUSED** (D-PARSER) |
| `RS._resolved_by_import` / `_suppress_calls` / `_cas_handlers_in` / `_suppress_sites_in` / `_production_modules` (§HELD 2) | read a28b's scanner | a28b's `_caught_classes` + `_discover_cas_handlers` | **EXTENDED** a28b's scanner (the ONE resolver refactored out of `_caught_classes`; the walk split per module) — never a second scanner (am-7 §3 item 4, pinned) |
| `_catch_sites.*` (walker + resolver) / `FATES` classifier + evidence predicates | read a28b's `_caught_classes` + my part-2 resolver | a28b's scanner (test_retry_seam, private) | **EXTENDED** into a shared support module (the ONE walker/resolver am-9/am-10 rule), and test_retry_seam re-points to it by IMPORT (identity-pinned). The classifier is **HAND-ROLLED** (no existing fate instrument; `_sdk_guard`'s runtime lens is a different question) |
| `CONV.Shape` / `seed_population` / `measure_weight` | `SUP` read | `SUP.seed_stragglers` / `measure_heal_shape` (ONE-blocker rows only) | **HAND-ROLLED** alongside: those helpers ARE the one-blocker bias F1 named. Generalising them in place would change r2's pins' fixtures (r2 PR18r2/PR19 depend on their exact shape). A merge is a later tidy-up, flagged, not done |
| `TIERS.Trigger` / `TRIGGERS` / `_BeforeTheHealChunk` | `SUP.ApplyHook` read | `ApplyHook` fires on the FIRST `_apply` | `ApplyHook` **REUSED** for every race trigger; `_BeforeTheHealChunk` **HAND-ROLLED** (it must skip the backfill's apply and fire only on a heal-note chunk) |
- **Friction:** `lore_search` was not used for the DRY queries above. `scripts/` is outside lore's graph (#507), and for `loremaster/tests` I read the files directly (awk) because the candidates were in files I already had open. That is a fallback, said out loud. Nothing new to file.

## Packages considered
| mechanism | library | what I READ | verdict |
|---|---|---|---|
| heal packer (the reference; the ruled builder shape) | `more_itertools.constrained_batches` 11.1.0 (installed, transitive) | the adversary's read of the installed source (`821be62` §P-PKG), **confirmed by EXECUTION**: my reference's packer IS the call, and the whole convergence sweep is green on it (43 passed) | **replace** (BC-r3-1; the builder declares the dependency) |
| call-graph derivation | `networkx` (installed, already used by tasks) | not needed: the closure is ~10 lines over a dict, and the graph must key by module-local NAME with seam-identity resolution, which is ours | **bespoke** (test instrument), stdlib `ast` |
| stack walking / frame identity | `inspect` / `sys._getframe` (stdlib) | `_sdk_guard.py`'s own idiom (call-time walk), read | keep (stdlib, reused idiom) |
| everything else | `ast`, `logging`, `pytest` | — | keep |

### §RED@HEAD addendum — re-measured at HEAD `e039c64` (a28b committed), 2026-09-26
- The r3 files alone: **`79 failed, 28 passed in 15.98s`**; after the am-9 §5 pin was added, at HEAD `4beb79e` (code = `e039c64`: `git diff --stat e039c64 4beb79e -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock` is empty): **`80 failed, 28 passed`**. The new pin is RED for the right reason (no heal). **`test_exhaustion_fates.py` is GREEN at HEAD `86a55eb`** (`16 passed`, together with `test_ast_reach_helpers.py` + `scripts/test_gated_ground.py`: `383 passed, 4 skipped`), as am-10 rules. It carries no red, so it needs no pending-contract row (was 82/23 at `c383edd`). The whole delta is `SEAM`. a28b's committed static index now loads, so the population pin's "index failed to load" member is gone, and `SEAM` reds **6**, each for its right reason: the three FK-r3-4 rows (`agents.register`, `keeps.get_or_create_keyed`, `record_measurement` — "NO injection drives"); `tasks.py::claim_task` and `tasks.py::_reanchor_stragglers` — "driver is STALE" (no shell / no heal at HEAD, and claim is not a listed handler, per FK-r3-1); and the heal identity leg — "injection never fired" (no heal). `tasks.py::transition` / `supersede_task` are now GREEN on the population pin, because a28b lists them as doors. Every other r3 file's reds are unchanged.

## §FATES — am-10's per-row verdicts (every domain site at HEAD `4beb79e`, generated by the committed classifier — no wholesale sentence)
Generated by `test_exhaustion_fates.classify` over `_catch_sites.production_catch_sites()` on the shared tree (HEAD production bytes). **74 domain sites:** 18 PASSTHROUGH and 19 TRANSLATE (derived, no row), and 37 REGISTERED rows under 32 keys. Of the 74, 35 are Reading (ii) (store-class catch) and 39 are Reading (i) only (`Exception` / `BaseException` / `RuntimeError` / bare). My earlier "57 / 26" counted only the sites that failed the am-9 rule, not these 74.
**The 8 pinned HOLE keys (`UNLOGGED_SITES`), each reported by name (am-10 §4), with its owner's one-line fix:**
- **`index/watcher.py::read_events`** (watcher) — `except Exception: logger.debug(...); return []`. It serves an **EMPTY ANSWER at DEBUG**, which is am-10 §1's FORBIDDEN shape itself, not merely unlogged: a degraded read looks exactly like "no events". **The sharpest row; I would call it a candidate defect** (its owner's ruling). Fix: log ≥ WARNING, or return a typed "degraded" marker.
- `server.py::aclose` ×2 (server shutdown) — `except (CancelledError, Exception): pass` + a `suppress(Exception)` around ingest-backend close. The shutdown continues, and a failed close is invisible. Fix: log ≥ WARNING.
- `server.py::build_app_context` ×3 (server startup) — `suppress(Exception)` around backend / calibration / ingest close INSIDE handlers that re-raise the ORIGINAL startup error. The primary failure is loud, and the secondary close failures are silent. Fix: log each.
- `server.py::run_startup_hooks` (server startup) — the inner `except BaseException: pass` while rolling back already-started hooks, then the ORIGINAL error re-raised. Same shape as above (M22 fixes it with one line).
- `scout.py::start` (scout) — `suppress(Exception)` around backend close during a failed start (the original re-raised).
- `scout.py::aclose` (scout) — `suppress(Exception)` around backend close at shutdown.
- `scout.py::run` ×2 (scout) — `suppress(NotImplementedError, ValueError, RuntimeError)` around `loop.add/remove_signal_handler`. Exhaustion is unreachable in practice (no store call inside), but `RuntimeError`'s closure contains it. Fix: narrow the tuple, or log.
- `calibration/engine.py::_count_live_total` (calibration) — the `suppress(Exception)` around `counter.aclose()`. (Its other row is a chained translate to `_ProbeUnavailableError`: registered with `raises-chained`, an honest loud fate.)
**Every other registered row's evidence HOLDS** (the committed test checks each, per site), and every verdict is in the table.

| # | site (file::function, line at `4beb79e`) | form · caught | reading | fate | evidence (holds) | owner | verdict |
|---|---|---|---|---|---|---|---|
| 1 | `agents.py::_ensure_connection` L526 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 2 | `audit.py::_ensure_connection` L156 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 3 | `briefs.py::_ensure_connection` L464 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 4 | `briefs.py::_relate_briefed` L1002 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 5 | `briefs.py::_release_version` L759 | try · SurrealStoreError | (ii) | best-effort-compensation | logs>=warning | briefs | honest — the evidence names the failure |
| 6 | `briefs.py::publish` L667 | try · SurrealStoreError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 7 | `calibration/engine.py::_count_live_total` L395 | try · RuntimeError,HTTPError,OSError | (i) only | lifecycle-catch-all | raises-chained | calibration | honest — the evidence names the failure |
| 8 | `calibration/engine.py::_count_live_total` L398 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | calibration | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 9 | `calibration/engine.py::_file_drift_finding_deduped` L552 | try · Exception | (i) only | named-isolation-served | logs>=warning, logs-exc_info, returns-named-outcome | calibration | honest — the evidence names the failure |
| 10 | `calibration/engine.py::_probe_loop` L354 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning, logs-exc_info | calibration | honest — the evidence names the failure |
| 11 | `diff.py::_ensure_connection` L543 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 12 | `findings.py::_ensure_connection` L459 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 13 | `findings.py::_transition` L1082 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 14 | `findings.py::annotate` L1026 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 15 | `floor_calibration/store.py::_ensure_connection` L218 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 16 | `floor_calibration/store.py::_fence_verdict` L707 | try · SurrealStoreError | (ii) | named-isolation-recorded | logs>=warning, returns-named-outcome | floor_calibration | honest — the evidence names the failure |
| 17 | `floor_calibration/store.py::record_measurement` L417 | try · SurrealConnectionError,TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 18 | `graph_surreal.py::_ensure_connection` L417 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 19 | `index/indexer.py::_commit_batch_file` L1820 | try · SurrealStoreError | (ii) | named-isolation-recorded | logs>=warning, logs-exc_info, marks-failed | indexer | honest — the evidence names the failure |
| 20 | `index/indexer.py::_index_chunks` L661 | try · SurrealStoreError | (ii) | named-isolation-recorded | logs>=warning, logs-exc_info, marks-failed | indexer | honest — the evidence names the failure |
| 21 | `index/indexer.py::_resolve_all_extension_edges` L1363 | try · SurrealStoreError | (ii) | named-isolation-recorded | logs>=warning, logs-exc_info, appends-failed | indexer | honest — the evidence names the failure |
| 22 | `index/indexer.py::_walk_and_index` L1228 | try · Exception | (i) only | named-isolation-recorded | marks-failed | indexer | honest — the evidence names the failure |
| 23 | `index/indexer.py::_walk_collect_tier` L1611 | try · Exception | (i) only | named-isolation-recorded | marks-failed | indexer | honest — the evidence names the failure |
| 24 | `index/indexer.py::index_file` L550 | try · Exception | (i) only | named-isolation-recorded | marks-failed | indexer | honest — the evidence names the failure |
| 25 | `index/reconcile.py::_maybe_stamp_snapshot` L256 | try · Exception | (i) only | named-isolation-recorded | logs>=warning, logs-exc_info | indexer | honest — the evidence names the failure |
| 26 | `index/snapshots.py::_ensure_connection` L275 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 27 | `index/surreal_manifest.py::_ensure_connection` L201 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 28 | `index/watcher.py::read_events` L262 | try · Exception | (i) only | lifecycle-catch-all | **NONE** | watcher | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 29 | `keeps.py::_ensure_connection` L267 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 30 | `keeps.py::get_or_create_keyed` L617 | try · SurrealConnectionError,TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 31 | `memory/local.py::_ensure_connection` L387 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 32 | `memory/local.py::remember` L704 | try · Exception | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 33 | `messages.py::_ensure_connection` L565 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 34 | `principal_keys.py::_ensure_connection` L264 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 35 | `principals.py::_dispatch_report_unmigrated` L2190 | try · PrincipalStoreError,SurrealStoreError,ValueError | (ii) | cli-exit | stderr, returns-named-outcome | principals | honest — the evidence names the failure |
| 36 | `principals.py::_ensure_connection` L353 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 37 | `scout.py::_dispatch` L396 | try · Exception | (i) only | named-isolation-recorded | logs>=warning, marks-failed | scout | honest — the evidence names the failure |
| 38 | `scout.py::_open_command_connection` L235 | try · Exception | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 39 | `scout.py::_periodic_reconcile` L899 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning, logs-exc_info | scout | honest — the evidence names the failure |
| 40 | `scout.py::aclose` L953 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | scout | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 41 | `scout.py::run` L978 | suppress · NotImplementedError,ValueError,RuntimeError | (i) only | lifecycle-catch-all | **NONE** | scout | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 42 | `scout.py::run` L985 | suppress · NotImplementedError,ValueError,RuntimeError | (i) only | lifecycle-catch-all | **NONE** | scout | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 43 | `scout.py::start` L861 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 44 | `scout.py::start` L864 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | scout | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 45 | `search.py::_enrichment_lines` L1415 | try · Exception | (i) only | named-isolation-served | returns-named-outcome | search | honest — the evidence names the failure |
| 46 | `server.py::_comms_register` L6795 | try · Exception | (i) only | best-effort-compensation | logs>=warning | comms (server) | honest — the evidence names the failure |
| 47 | `server.py::_eager_build_or_operator_safe_error` L10593 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning, logs-exc_info | server startup | honest — the evidence names the failure |
| 48 | `server.py::_eager_build_with_retry` L10509 | try · BaseException | (i) only | lifecycle-catch-all | logs>=warning | server startup | honest — the evidence names the failure |
| 49 | `server.py::_periodic_reconcile` L10454 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning, logs-exc_info | server | honest — the evidence names the failure |
| 50 | `server.py::_resolve_or_acknowledge_many` L3951 | try · TxnContentionExhaustedError | (ii) | named-isolation-served | appends-failed | findings dispatcher (64b) | honest — the evidence names the failure |
| 51 | `server.py::_run_schema_rebuild` L10428 | try · Exception | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 52 | `server.py::aclose` L9109 | try · CancelledError,Exception | (i) only | lifecycle-catch-all | **NONE** | server shutdown | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 53 | `server.py::aclose` L9137 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | server shutdown | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 54 | `server.py::build_app_context` L9891 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 55 | `server.py::build_app_context` L9895 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | server startup | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 56 | `server.py::build_app_context` L10133 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 57 | `server.py::build_app_context` L10145 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | server startup | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 58 | `server.py::build_app_context` L10153 | suppress · Exception | (i) only | lifecycle-catch-all | **NONE** | server startup | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 59 | `server.py::on_call_tool` L10694 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning, logs-exc_info | server (trace emit) | honest — the evidence names the failure |
| 60 | `server.py::run_probe_gate` L2286 | try · Exception | (i) only | lifecycle-catch-all | logs>=warning | server startup | honest — the evidence names the failure |
| 61 | `server.py::run_startup_hooks` L971 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 62 | `server.py::run_startup_hooks` L978 | try · BaseException | (i) only | lifecycle-catch-all | **NONE** | server startup | **HOLE (pinned, UNLOGGED_SITES)** — no log, no marker |
| 63 | `store/_txn.py::_run_verified_transaction` L1583 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 64 | `store/lease.py::_ensure_connection` L315 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 65 | `store/surreal.py::_ensure_connection` L493 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 66 | `tasks.py::_ensure_connection` L842 | try · TxnContentionExhaustedError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 67 | `tasks.py::_reject_unusable_blockers` L2315 | try · SurrealStoreError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 68 | `tasks.py::supersede_task` L2000 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 69 | `tasks.py::transition` L1672 | try · TxnContentionExhaustedError | (ii) | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 70 | `tasks.py::transitive_blockers` L2501 | try · SurrealStoreError | (ii) | TRANSLATE | — | — | honest — chained translation to a FAULT class |
| 71 | `testing/loopback.py::_loud_teardown` L456 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |
| 72 | `testing/loopback.py::_loud_teardown` L461 | try · Exception | (i) only | lifecycle-catch-all | adds-note | testing harness | honest — the evidence names the failure |
| 73 | `testing/loopback.py::_run` L321 | try · BaseException | (i) only | lifecycle-catch-all | records-on-self | testing harness | honest — the evidence names the failure |
| 74 | `testing/loopback.py::start` L341 | try · BaseException | (i) only | PASSTHROUGH | — | — | honest — re-raised unchanged |

TOTAL 74 domain sites


## §SAT — satisfiability on the RIGHT base (full suite; every red individually adjudicated), 2026-09-26
- **Tree** `scratch/r3/ref` (a `scratch_copy.sh` copy; provenance printed: `loremaster.__file__ = …/scratchpad/r3/ref/loremaster/loremaster/__init__.py`). It is HEAD `c9e5eb8` (code = `c383edd`) + 63c-i-a a28b's `test_retry_seam.py` working copy (md5 `46427f86`; §HELD part 2 is a delta over it) + §HELD part 1 + part 3 + part 2 (md5 `131e505f`) + my reference (ref6 + `my_ref_r3.py` → `tasks.py 017bdb55`, `_txn.py a07f3e30`) + this commit's test files, with r2's CR file deleted.
- **Runner** `sat.sh`: it waits for ≥ 22 GB free, then runs `-n 8` with run.sh's 15 GB process-TREE watchdog. Attempt 0 (`-n 12`, run by hand) was KILLED by the watchdog at `avail=8G` (host pressure from other sessions). Attempt 1 completed.
- **Tail: `278 failed, 12066 passed, 63 skipped, 3 xfailed, 9 warnings in 1232.27s (0:20:32)`**. (The `ERROR loremaster…:_txn.py` lines in the log are captured LOG records, not test errors.)
- **Every red, adjudicated:**
  - **268 in non-58 files, IDENTICAL at plain HEAD.** Same-file baseline on the clean HEAD copy (no §HELD, no reference): `268 failed, 1268 passed, 1 skipped`. `comm` over the two red sets: sat-only = 2 (next bullet), base-only = ∅. The owners: `test_comms_footer` 76 · `test_mcp_server` 28 · `test_findings_{enforcement 4, governance 24, identity 22, migrate 26, schema 17}_64b` · `test_governed_substrate_64b` 26 go to **packet-64b-i-contract** (committed `d8ea4ba`); `test_fixwave_a28_63c_i_a` 41 · `a19a` 2 · `a19b` 2 go to **packet-63c-i-a-a28-contract**. UNRELATED, owned, pre-existing.
  - **2 × `scripts/test_gated_ground.py`** (`…emptiness_is_a_fact_about_the_TREE`, `…no_committed_python_is_ungated…`) are **a SCRATCH ARTIFACT of mine.** The adversary's three probe files had been committed in the SCRATCH copy's git and then deleted from disk, so they read as committed-but-uncollected. Once they were dropped from the scratch copy's index, the file ran `317 passed`. They are NOT in this commit, so there is nothing to attribute.
  - **8 in my scope, each owned ELSEWHERE by design:**
    - `SEAM` ×3 — the population rows `[agents.py::register]`, `[keeps.py::get_or_create_keyed]` and `[floor_calibration/store.py::record_measurement]`: FK-r3-4, the lead's routing to their owners (am-7 §3 item 2).
    - `TIERS` ×3 — `[TxnUniqueViolationError-keeps-unique-race]`, `sibling_alone[TxnUniqueViolationError]` and `test_every_ruled_class_has_its_ruled_tier`: the class does not exist until 63c-i-a's am-33 build, which runs serially BEFORE 58. On the ref the keeps race logs `['ERROR' ×7]`, the right reason.
    - `RS` ×2 — a28b's own `…door_enumeration…` / `…typed_catch_enumeration…`: they need 63c-i-a's build (keeps still broad, RS-5 absent). This is packet-63c-i-a-a28-contract's red. The same two reds, with the same messages, appeared on HEAD + a28b + ref6 before any r3 delta existed (the r2-scope baseline run: `4 failed, 1172 passed`).
  ⇒ **0 reds attributable to the 58 contract, §HELD or my reference.**
- **Typecheck on the built tree** (`scripts/typecheck.sh` on the SAT tree): **0 errors in any file this commit touches.** The errors that remain belong to others' contract-ahead files (64b ×6 files + `test_mcp_server` + `test_comms_footer`, a19a/a19b/a28), a28b's `test_retry_seam.py:200` (`TxnUniqueViolationError`), the scratch-only adversary probe copy, `scripts/esc1_write_path_cycle_closure.py:426` (BC-r3-2, the builder's), and one line in my reference's `_txn.py`, which is not a spec. The typecheck on the built tree is ALSO what caught D-SHADOW.
- **Lint:** `ruff check` over every file this commit touches → `All checks passed!`. §HELD part 2's file on the SAT tree → clean.

## §CURRENCY — every pytest red this commit introduces is OWNED (`scripts/pending_contracts.yaml`, bound `packet-58-contract`, UPDATED)
- **The edit** (the generator is `pc_edit.py`; it touches only `packet-58-contract`): owner/ruling now amendments 1–8 + r3 receipts. The reopen_trigger adds `TaskLedger._reanchor_stragglers`, `loremaster.tasks.StragglerHealPackerError`, `loremaster.store._txn._ROLLBACK_LOG_TIERS` and `TxnCasLostError`, and NAMES the two leg families that discharge on other work (FK-r3-4's three rows; the `TxnUniqueViolationError` legs). `test_reanchor_58_r2_cas_runtime.py` is removed (file deleted). The six r3 files are added, their `missing_symbols` DERIVED by `pending_contract_gate.py --derive` on HEAD + this commit. R3A6 carries ONE `unsymboled_codes` `attr-defined` (count 1, with a reason: the adversary's AST-equal leg reads `_txn._ROLLBACK_LOG_TIERS` through the module alias, which mypy reports without a symbol). `--verify-registry` → clean.
- **Staging (other packets' uncommitted hunks are in this file):** the INDEX blob = `HEAD:scripts/pending_contracts.yaml` + my edit ONLY (written with `git update-index --cacheinfo`). The working copy = a28b's WIP + my edit. Verified with `git diff --cached` (§ below the commit).
- **Run 1 — `pending_contract_gate.py --currency`** on HEAD `c383edd` + this commit (clean `scratch_copy.sh` copy): `typecheck RED_ADJUDICATED` (58 residuals: packet-58 / 64b-i / 63c-a28) · `ruff GREEN` · **`pytest RED_ORPHANED — 1`**: `test_ast_reach_helpers::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist` flagged my `SEAM.discovered_drivers` → **D-PARSER, fixed.**
- **Runs 2–6 — the gate's own run could not complete.** The gate picks its pytest worker count itself, and a forwarded `-n` is refused (#503). With no other lore pytest live it picks `SOLO_PYTEST_WORKERS = "auto"` = 64 workers. On this host that evening (swap 15/15 GB used; two surreal stores ≈ 22 GB RSS; several postgres), MemAvailable fell from ≥ 26 GB to 13–14 GB within ~30 s, and my 15 GB process-TREE watchdog (brief rule) killed 5 attempts (`currency_attempts.txt`: 4 × `rc=98`, plus one earlier `avail=14G`).
- **What stands in its place — the SAME three legs, measured separately (D-CURRENCY):**
  - `--currency --legs typecheck,ruff` → **`typecheck RED_ADJUDICATED` · `ruff GREEN`**. pytest is reported `NOT_RUN`, as the gate honestly must when a leg is not in `--legs`.
  - The pytest leg, reproduced at an explicit `-n 8` under the watchdog, with `-o junit_family=xunit1 --junit-xml` (the gate's own junit contract): **`463 failed, 11864 passed, 63 skipped, 3 xfailed in 846.08s`**. Partitioned with the gate's own rule (a failure is expected iff its FILE is registered; `partition.py`, pasted §INSTRUMENTS): **`TOTAL failed=463 files=27 orphans=0`**. That is 27 files, every one OWNED (packet-58 ×17 files incl. the six r3 files; 64b-i ×8; 63c-a28 ×3 — full table in `partition` output below). `test_ast_reach_helpers.py` is no longer among them.
  ```
  OWNED 1 test_blocks_edge · 76 test_comms_footer · 4/24/22/26/17 test_findings_{enforcement,governance,identity,migrate,schema}_64b · 2 a19a · 2 a19b · 41 a28 · 26 test_governed_substrate_64b · 28 test_mcp_server
  OWNED 3 r2_am2 · 12 r2_probes · 27 r2_rulings · 2 r2_scale · 8 r3_am6 · 9 r3_cas_seam · 41 r3_convergence · 6 r3_probes · 2 r3_relate · 16 r3_tiers
  OWNED 44 test_supersede_reanchor_58 · 5 claimable_partition_58 · 15 guarded_shell_58 · 1 task_read_surface · 3 scripts/test_forgery_door_sweep
  TOTAL failed=463 files=27 orphans=0
  ```
- **RE-MEASURED at HEAD `e039c64` (a28b committed; D-BASE2) — the verdict this commit stands on:** `--currency --legs typecheck,ruff` → **`typecheck RED_ADJUDICATED` (60 residuals, all owned) · `ruff GREEN`** · pytest leg at `-n 8` (junit xunit1) → **`521 failed, 11921 passed, 63 skipped, 3 xfailed in 886.32s`** → partition: **`TOTAL failed=521 files=29 orphans=0`**. The new owned files are a28b's `test_fixwave_a28b_63c_i_a.py` (24) and `test_retry_seam.py` (2), plus a28's grown count (76), all under `packet-63c-i-a-a28-contract`. `SEAM` is at 6.
- **After the `e039c64` partition, what moved and how each move was re-verified (not a re-run of the whole gate):** CONV gained am-9 §5's pin (RED at HEAD for the right reason, in a registered file → owned); `test_exhaustion_fates.py` + `_catch_sites.py` + `_exhaustion_fates.py` are new and GREEN at HEAD `86a55eb` (with `test_ast_reach_helpers` + `test_gated_ground`: `383 passed, 4 skipped`); `scripts/typecheck.sh` on HEAD + this commit shows 0 lines in any new file (the typecheck residuals are the same ruled-symbol lines as before). HEAD `e039c64` → `86a55eb` moved docs only (am-9, am-10, sidecar/lead reports; `git diff --stat` over code is empty).
  ⇒ **Currency, by its own rule, is RED_ADJUDICATED on all three legs, with 0 orphans.** This is NOT the gate's single-invocation receipt. **The lead should re-run `--currency` once the host has headroom** (or once another lore pytest is live, when the gate caps itself at 12). That is the one receipt I could not produce, stated plainly.

## §HELD — the held integration patch, RE-DERIVED at HEAD `c383edd` (= `c9e5eb8` in code) on 2026-09-26
**Three parts, applied in order 1 → 3 → (63c-i-a a28b) → 2.** Parts 1 and 3 are UNCHANGED from r2. Part 2 is NEW: r2's part 2 (the am-5 (B) re-key) is WITHDRAWN. It no longer applies, because it collides with a28b at `test_retry_seam.py:6782`, and a28b already carries its partition. It is replaced by a DELTA over a28b's scanner.
1. **Part 1 = r1's §HELD, VERBATIM**, from `5a43aeb:REPORT-contract-58.md` lines 173–557, md5 `dbba9753cbe960cda178f42687039c2d` (= r2's recorded value). It covers `server.py` (supersede branch + `_render_supersede_result`), `surreal_schema.py` (the `blocked_by.*` index rider), `_task_fakes.py`, `test_link5_render_containment.py`, `test_mcp_server.py` (D7), and the new `test_supersede_render_58.py`. Not re-pasted: cite it at that address.
2. **Part 2 = NEW, the am-7/am-8 DELTA over 63c-i-a a28b's scanner**, `loremaster/tests/test_retry_seam.py` only, md5 `986f87dff6eb7b30c2f3d42b26dca8af`. VERBATIM below. Its generator `held_part2.py` is pasted in §INSTRUMENTS. The patch is the deliverable; the generator is its provenance.
3. **Part 3 = r2's part 3, VERBATIM**, from `c42eeaf:REPORT-contract-58-r2.md` lines 177–195, md5 `15f38e319cb8d3c25456084dda4989b1`. It is `test_surreal_store.py`'s capture level (DEBUG); under am-7 the governed conflict logs WARNING, which part 3's DEBUG capture still sees.

**Receipts (measured 2026-09-26):**
- **At HEAD `86a55eb` (a28b committed; am-9/am-10 folded):** `git apply --check part1` → OK · `part3` → OK · `part2` (md5 `986f87df`, final) → **OK directly on HEAD**. Part 2's final content: test_retry_seam's resolver IMPORTED from the committed `_catch_sites` (identity-pinned); the `try*` walk + its partition discriminator; the §8c header rewritten (DUAL: the retired `_select` key, the partition, where the fate rule now lives); a28b's `claim_task` comment rewritten (DUAL, am-9 §1); `_production_module_trees`/`_parents_of`/`_cas_handlers_in` split per module. It depends on this commit's `_catch_sites.py`, so it applies only AFTER this commit. The earlier receipts below were taken at `c383edd` + the a28b working copy.
- On a CLEAN HEAD copy (`scratch_copy.sh`, `c383edd` + this commit's files): `git apply --check part1` → OK · `part3` → OK · `part2` → **FAILS** (`patch failed: loremaster/tests/test_retry_seam.py:6798`), BY DESIGN: it is a delta over a28b · `a28b` (the working-copy diff, md5 `46427f86`) then `part2` → OK.
- On the SHARED tree (HEAD + a28b WIP md5 `46427f86` + peers' untracked files): `git apply --check` of part1, part2 and part3 → all OK.
- On the SAT tree, all three are applied, and every a28b pin keeps its a28b-owned verdict (§SAT).

**Re-verification steps (the base keeps moving):**
1. **63c-i-a a28b fold (amendments 32/33, `_txn.py`, the `test_retry_seam.py` scanner) — ✅ DONE for the a28b CONTRACT commit `e039c64`** (D-BASE2: part 2 rebased, `--check` OK on HEAD). Still to repeat when 63c-i-a's BUILD (or any later a28 fold) lands: re-run `git apply --check part2` against the committed file. If a28b's scanner moved, re-anchor by SYMBOL (`_caught_classes`, `_discover_cas_handlers`, the §8c header, the `_TYPED_CAS_CATCHES` comment, `class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD`). If a28b's `_caught_classes` signature or body changed, rebuild part 2 with `held_part2.py` (its anchors assert exactly-once and fail loud). Then run `pytest loremaster/tests/test_retry_seam.py -k "GuardedCas or CatchForms or ExhaustionUNREAD"`. EXPECTED before 63c-i-a's BUILD: the two a28b reds only (`doors … keeps.py::get_or_create_keyed`, `typed … agents.py::register, keeps.py::get_or_create_keyed`); all 4 `TestTheCatchFormsAreSeen` legs GREEN. After 63c-i-a's build: all green. When 63c-i-a's build lands `TxnUniqueViolationError`, `TIERS`'s three `TxnUniqueViolationError` legs go green only once 58's table carries the class (BC-r3-3).
2. **64b's §HELD** (committed contract `d8ea4ba`; `REPORT-contract-64b.md` §HELD step 11 and #17072 say 64b re-derives `test_retry_seam.py` AFTER 58). Part B's static G2 hunks (`_GUARDED_CAS_SHARED_RE_READ`, `findings.py::_run_guarded`) must be re-expressed on the post-58 file. Three checks: (a) its re-read via the SHARED `classify_zero_row_cas` is a re-read through a helper OUTSIDE the class, which is a28b's stated bound. It is invisible to the static domain unless 64b widens `_issues_a_read` through the ONE resolver. The runtime leg (`SEAM`) sees it regardless. (b) `test_mcp_server.py`: part 1's D7 hunk and 64b's converted suite touch the same file. Re-run `git apply --check part1` after 64b commits, and re-anchor D7 by its test name (`test_superseded_task_in_leg1_renders_the_chain_marker`). (c) BC-r3-7: the two findings `SEAM` drivers re-key to `findings.py::_run_guarded`.
3. **Bare sweeps (CLAUDE.md rename law), after applying:** `awk '/_select/' <_discover_cas_handlers body>` → 0 (no prefix key). `SHELL_LEDGER_MODULES|SINGLE_STATEMENT_CAS_DOORS|APPLY_SEAM` over `loremaster/` + `scripts/` → exactly 2 hits, both LEGIT: the R3-D1 DUAL comment in `_reanchor_58_support.py` naming them in order to retire them (measured by awk over `git ls-files` + the new files, 2026-09-26). `_TYPED_CAS_CATCHES` never gains `tasks.py::claim_task` (FK-r3-1).

**Part 2, VERBATIM** (md5 `986f87dff6eb7b30c2f3d42b26dca8af`):
```diff
diff --git a/loremaster/tests/test_retry_seam.py b/loremaster/tests/test_retry_seam.py
index 79ddccb..99646ad 100644
--- a/loremaster/tests/test_retry_seam.py
+++ b/loremaster/tests/test_retry_seam.py
@@ -6783,9 +6783,26 @@ class TestEveryConnectionOwnerOpensExactlyOneSocket:
 #
 #     ∀ guarded-CAS handlers: exhausted contention propagates UNREAD.
 #
-# And the population is DISCOVERED, by the property that MAKES a handler a guarded CAS —
-# `except SurrealStoreError` whose body RE-READS state (`await self._select…`). A fifth door
-# is pinned the day it is written, by nobody's memory.
+# ⚠ DUAL (packet 58 contract r3, §HELD part 2 — REPORT-contract-58-r3.md; amendments 7 §1 + 8 §3/§6): this
+# paragraph USED to say the population is found by *"`except SurrealStoreError` whose body RE-READS state
+# (`await self._select…`)"*. Both halves of that sentence were retired (adversary-58-r2 F6: corpse prose):
+#
+#   * the DOMAIN (63c-i-a a28b, amendment 32 §1.3 f + 58 amendment 7 §1) — every catch SITE in the WHOLE
+#     production tree (`try` / `try*` handlers and `with contextlib.suppress(...)`, 58 amendment 8 §3) whose
+#     caught classes resolve BY IMPORT (Name / dotted Attribute / Tuple elements) to a `SurrealStoreError`
+#     subclass; a HANDLER joins the re-read domain iff it awaits a same-class method whose body carries a
+#     `SELECT` literal (a derived re-read, never a `_select` name prefix);
+#   * the PARTITION (58 amendment 7 §0 row 1a) — a DOOR iff exhausted contention can reach it (some caught
+#     class's subclass closure contains `TxnContentionExhaustedError`), else SAFE-BY-TYPE; a `suppress` site
+#     can never re-read (it has no handler body), so it never joins the exact sets (FK-r3-3);
+#   * the FATE RULE (58 amendments 9 §3 + 10) lives in ``test_exhaustion_fates.py``, on the SAME walker and
+#     resolver (``_catch_sites``): every catch site that can reach exhausted contention must PASS it through,
+#     TRANSLATE it to a fault class ``from`` the cause, or carry a registered row proving a named isolation.
+#
+# BOUND (stated, not hidden): a re-read through a helper OUTSIDE the class, or a `SELECT` built without a
+# literal, is invisible to this STATIC domain. The ∀ itself no longer lives here — it is the DRIVER-SEAM
+# injection (58 amendment 8 §3, `test_reanchor_58_r3_cas_seam.py`), which does not care how a catch or a
+# re-read is spelled; this index is the REVIEWER-VISIBLE half, and the two are cross-checked both ways.
 # ---------------------------------------------------------------------------
 
 _GUARDED_CAS_GUARD = "TxnContentionExhaustedError"
@@ -6798,25 +6815,13 @@ def _module_of(key: str) -> Any:
     return importlib.import_module(f"loremaster.{dotted}" if dotted != "__init__" else "loremaster")
 
 
-def _caught_classes(handler: ast.ExceptHandler, module: Any) -> list[type]:
-    """Every class an ``except`` clause catches, RESOLVED BY IMPORT in its module's namespace — each element
-    of
-    a Tuple handler included, a ``Name`` or a dotted ``Attribute`` alike (amendment 32 §1.3 f: the old key
-    read
-    only a bare ``ast.Name`` spelled ``SurrealStoreError``, so a Tuple, a subclass name or an alias was
-    invisible)."""
-    if handler.type is None:
-        return []
-    elements = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
-    resolved: list[type] = []
-    for element in elements:
-        try:
-            value = eval(compile(ast.Expression(element), "<except>", "eval"), vars(module))  # noqa: S307
-        except Exception:  # noqa: BLE001 - an unresolvable name is simply not a store class
-            continue
-        if inspect.isclass(value):
-            resolved.append(value)
-    return resolved
+# ⚠ DUAL (packet 58 contract r3, §HELD part 2 — REPORT-contract-58-r3.md D-AM10): a28b's private
+# ``_caught_classes`` (Name / Attribute / Tuple elements, resolved by import) is now an IMPORT of THE ONE
+# catch-site resolver in ``_catch_sites`` (packet 58 amendments 9 §3 + 10 §2: ONE walker, ONE resolver, every
+# catch form — ``except``, ``except*``, ``contextlib.suppress``).  Same behaviour for every handler this index
+# reads (a bare ``except:`` now resolves to ``BaseException``: outside the store domain, like a28b's ``[]``).
+from _catch_sites import caught_classes as _caught_classes  # noqa: E402
+from _catch_sites import suppress_calls as _suppress_calls  # noqa: E402
 
 
 def _issues_a_read(method: ast.AST) -> bool:
@@ -6843,52 +6848,72 @@ def _discover_cas_handlers() -> dict[str, tuple[str, int, bool, bool]]:
     it (``except`` clauses are tried in order and the typed error SUBCLASSES ``SurrealStoreError``).
     """
     doors: dict[str, tuple[str, int, bool, bool]] = {}
+    for key, tree, module in _production_module_trees():
+        doors.update(_cas_handlers_in(key, tree, module))
+    return doors
+
+
+def _production_module_trees() -> list[tuple[str, ast.Module, Any]]:
+    """``(package-relative path, parsed tree, imported module)`` for every production module — the tree walk
+    the whole index ranges over (the file set is an OUTPUT of the walk, never an input: 58 amendment 7 §0)."""
+    modules: list[tuple[str, ast.Module, Any]] = []
     for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
         if "__pycache__" in path.parts:
             continue
         key = path.relative_to(_PACKAGE_ROOT).as_posix()
-        module = _module_of(key)
-        tree = ast.parse(path.read_text(encoding="utf-8"))
-        parents: dict[int, ast.AST] = {}
-        for parent in ast.walk(tree):
-            for child in ast.iter_child_nodes(parent):
-                parents[id(child)] = parent
-        for node in ast.walk(tree):
-            if not isinstance(node, ast.Try):
+        modules.append((key, ast.parse(path.read_text(encoding="utf-8")), _module_of(key)))
+    return modules
+
+
+def _parents_of(tree: ast.AST) -> dict[int, ast.AST]:
+    parents: dict[int, ast.AST] = {}
+    for parent in ast.walk(tree):
+        for child in ast.iter_child_nodes(parent):
+            parents[id(child)] = parent
+    return parents
+
+
+def _cas_handlers_in(key: str, tree: ast.AST, module: Any) -> dict[str, tuple[str, int, bool, bool]]:
+    """ONE module's slice of the derived domain (see :func:`_discover_cas_handlers`) — split out so the
+    catch-form discriminators can run the SAME walk over a synthetic source (58 amendment 8 §3)."""
+    doors: dict[str, tuple[str, int, bool, bool]] = {}
+    parents = _parents_of(tree)
+    for node in ast.walk(tree):
+        if not isinstance(node, (ast.Try, ast.TryStar)):
+            continue
+        for index, handler in enumerate(node.handlers):
+            caught = _caught_classes(handler, module)
+            if not any(issubclass(cls, SurrealStoreError) for cls in caught):
                 continue
-            for index, handler in enumerate(node.handlers):
-                caught = _caught_classes(handler, module)
-                if not any(issubclass(cls, SurrealStoreError) for cls in caught):
-                    continue
-                scope = _enclosing_callable(handler, parents)
-                owner = scope
-                while owner is not None and not isinstance(owner, ast.ClassDef):
-                    owner = parents.get(id(owner))
-                methods = {
-                    item.name: item
-                    for item in (owner.body if isinstance(owner, ast.ClassDef) else [])
-                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
-                }
-                re_reads = any(
-                    isinstance(awaited, ast.Await)
-                    and isinstance(awaited.value, ast.Call)
-                    and isinstance(awaited.value.func, ast.Attribute)
-                    and isinstance(awaited.value.func.value, ast.Name)
-                    and awaited.value.func.value.id == "self"
-                    and awaited.value.func.attr in methods
-                    and _issues_a_read(methods[awaited.value.func.attr])
-                    for awaited in ast.walk(handler)
-                )
-                if not re_reads:
-                    continue
-                reachable = any(issubclass(TxnContentionExhaustedError, cls) for cls in caught)
-                guarded_above = any(
-                    issubclass(TxnContentionExhaustedError, cls)
-                    for earlier in node.handlers[:index]
-                    for cls in _caught_classes(earlier, module)
-                )
-                where = getattr(scope, "name", "<lambda>") if scope else "<module>"
-                doors[f"{key}::{where}"] = (key, handler.lineno, reachable, guarded_above)
+            scope = _enclosing_callable(handler, parents)
+            owner = scope
+            while owner is not None and not isinstance(owner, ast.ClassDef):
+                owner = parents.get(id(owner))
+            methods = {
+                item.name: item
+                for item in (owner.body if isinstance(owner, ast.ClassDef) else [])
+                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
+            }
+            re_reads = any(
+                isinstance(awaited, ast.Await)
+                and isinstance(awaited.value, ast.Call)
+                and isinstance(awaited.value.func, ast.Attribute)
+                and isinstance(awaited.value.func.value, ast.Name)
+                and awaited.value.func.value.id == "self"
+                and awaited.value.func.attr in methods
+                and _issues_a_read(methods[awaited.value.func.attr])
+                for awaited in ast.walk(handler)
+            )
+            if not re_reads:
+                continue
+            reachable = any(issubclass(TxnContentionExhaustedError, cls) for cls in caught)
+            guarded_above = any(
+                issubclass(TxnContentionExhaustedError, cls)
+                for earlier in node.handlers[:index]
+                for cls in _caught_classes(earlier, module)
+            )
+            where = getattr(scope, "name", "<lambda>") if scope else "<module>"
+            doors[f"{key}::{where}"] = (key, handler.lineno, reachable, guarded_above)
     return doors
 
 
@@ -6941,8 +6966,13 @@ _GUARDED_CAS_DOORS = {
 # The SAFE-BY-TYPE half (packet 58 amendment 7 §0 row 1b + §2, landed by 63c-i-a a28b per lead #17087):
 # handlers
 # in the derived domain whose caught classes exhausted contention can NOT reach. Both identity-taken CAS doors
-# decide from ONE class (amendment 32 §1.2, R-6; the class named by amendment 33). 58's §HELD delta adds
-# ``tasks.py::claim_task`` (TxnClaimLostError, 58 amendment 4). EXACT, both ways.
+# decide from ONE class (amendment 32 §1.2, R-6; the class named by amendment 33). EXACT, both ways.
+# ⚠ DUAL (packet 58 contract r3, §HELD part 2; REPORT-contract-58-r3.md FK-r3-1): this comment USED to say
+# 58's delta adds ``tasks.py::claim_task``. It does NOT: a ruled claim (am-3 §3 ``except
+# TxnClaimLostError``, the
+# owner read AFTER the ``try``; am-5 rejected an inline re-read) has no re-reading handler, so it is outside
+# the DERIVED domain amendment 7 §1 rules (re-read presence is the domain filter) — listing it would RED every
+# correct build.  Its exhaustion safety is pinned by the driver-seam ∀ (58 amendment 8 §3).
 _TYPED_CAS_CATCHES = {
     "agents.py::register": "TxnUniqueViolationError — the identity is taken; the winner is re-read",
     "keeps.py::get_or_create_keyed": (
@@ -7024,6 +7054,97 @@ class TestNoGuardedCasHandlerReinterpretsExhaustedContention:
         )
 
 
+_SYNTHETIC_CATCH_FORMS = """
+import contextlib
+from contextlib import suppress
+from loremaster.store._txn import SurrealStoreError, TxnClaimLostError, TxnContentionExhaustedError
+
+ALIAS = contextlib.suppress
+
+
+class Ledger:
+    async def _reread(self):
+        return await self._query("SELECT * FROM t")
+
+    async def star_door(self):
+        try:
+            await self._apply()
+        except* SurrealStoreError:
+            await self._reread()
+
+    async def star_typed(self):
+        try:
+            await self._apply()
+        except* TxnClaimLostError:
+            await self._reread()
+
+    async def star_guarded(self):
+        try:
+            await self._apply()
+        except* TxnContentionExhaustedError:
+            raise
+        except* SurrealStoreError:
+            await self._reread()
+
+    async def suppress_broad(self):
+        with contextlib.suppress(SurrealStoreError):
+            await self._apply()
+
+    async def suppress_typed(self):
+        with suppress(TxnClaimLostError):
+            await self._apply()
+
+    async def suppress_alias_broad(self):
+        with ALIAS(SurrealStoreError, KeyError):
+            await self._apply()
+
+    async def suppress_unrelated(self):
+        with contextlib.suppress(KeyError):
+            await self._apply()
+
+    async def not_a_suppress(self):
+        with open("x") as handle:
+            await self._apply(handle)
+"""
+
+
+def _synthetic_module() -> tuple[ast.Module, Any]:
+    """The catch-form discriminator source, parsed and EXECUTED into a real module namespace (so every name
+    resolves BY IMPORT exactly as production's do).  The ``except*`` bodies await; Python accepts that only
+    inside an ``async def`` — which is where they are."""
+    import types
+
+    module = types.ModuleType("synthetic_catch_forms_58r3")
+    exec(compile(_SYNTHETIC_CATCH_FORMS, "<synthetic>", "exec"), vars(module))  # noqa: S102
+    return ast.parse(_SYNTHETIC_CATCH_FORMS), module
+
+
+class TestTheCatchFormsAreSeen:
+    """Packet 58 amendments 8 §3 + 9 §3 + 10: the reviewer-visible index learns the catch FORMS — ``try*``
+    handlers — through THE ONE resolver (``_catch_sites``), shared by identity with the fate classifier.  (The
+    "exactly one scanner function" pin is 63c-i-a's — 63c amendment 34 §5.)  ⚠ DUAL: new in contract r3 (§HELD
+    part 2)."""
+
+    def test_try_STAR_handlers_join_the_domain_and_the_partition(self) -> None:
+        tree, module = _synthetic_module()
+        found = _cas_handlers_in("synthetic.py", tree, module)
+        assert found.keys() == {
+            "synthetic.py::star_door", "synthetic.py::star_typed", "synthetic.py::star_guarded"
+        }, sorted(found)
+        _file, _line, reachable, guarded = found["synthetic.py::star_door"]
+        assert reachable and not guarded, "an unguarded `except* SurrealStoreError` re-reader is a door"
+        assert not found["synthetic.py::star_typed"][2], "`except* TxnClaimLostError` is safe BY TYPE"
+        assert all(found["synthetic.py::star_guarded"][2:]), "a `try*` guard clause above counts"
+
+    def test_this_index_resolves_through_THE_ONE_resolver(self) -> None:
+        """Sharing by IDENTITY (CLAUDE.md "prove sharing by mutation"): the index's resolver IS the fate
+        classifier's — change ``_catch_sites.caught_classes`` and both instruments move together."""
+        import _catch_sites
+
+        assert _caught_classes is _catch_sites.caught_classes
+        assert _suppress_calls is _catch_sites.suppress_calls
+
+
 class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:
     """The BEHAVIOURAL half of P-3 — because a guard can exist and guard NOTHING.
 
```

## §MUTATION — every new pin family, killed by a DECLARED mutation of my own (declare-then-diff, both ways; 2026-09-26)
Instrument: `mut58r3.py` (pasted §INSTRUMENTS). It runs on the ref copy (provenance per run: `loremaster.__file__ = …/scratchpad/r3/ref/loremaster/loremaster/__init__.py`, the first line of each log). The declared set is resolved from `--collect-only` BEFORE any run. Every anchor is asserted exactly-once and every edited file asserted CHANGED. The tree is restored by `git checkout`, then asserted clean. Expected = the scope's baseline reds ∪ declared. Diffed both ways: UNEXPECTED reds, and declared reds that STAYED GREEN (a mutation that landed in dead code). Per BRIEF CONFLICT, none of these replays an adversary-named build. Each is my own edit at the property its pin guards.

Scope baselines (unmutated ref): `conv` 50 passed · `tier` 3 failed / 33 passed (the three `TxnUniqueViolationError` legs, 63c-dependent, §SAT) · `cas` 3 failed / 19 passed (FK-r3-4's three rows) · `rs` 4 passed · `rel` 6 passed · `f3` 2 passed.

| # | mutation (production, unless noted) | pin family it proves | declared | result |
|---|---|---|---|---|
| M1 | packer `get_len` under-prices each row by ONE statement | CONV scale sweep + mixes + PC | 13 (10 × `fit+1` + 2 mixes + PC) | **EXACT** · `13 failed, 37 passed` |
| M2 | F4: `break` after the FIRST unresolvable entry (one WARNING per ROW) | CONV F4 per-ENTRY records | 2 (`two_bad-{phantom,cyclic}`) | **EXACT** · `2 failed, 48 passed` |
| M3 | the heal's INFO counts every straggler read, skipped rows included | CONV F4 uncounted + PD1/PD2 | 8 | **EXACT** · `8 failed, 42 passed` |
| M4 | non-strict packer: applies every packable chunk, THEN raises for the monster | CONV F10 "changes NOTHING" | 1 | **EXACT** · `1 failed, 49 passed` (PE, which checks only the monster's column, stays green, as declared) |
| M5 | `TxnReanchorStragglerError` dropped from the tier table | TIERS completeness / ruled tier / its trigger / its mutation leg + R3A6 + PA2 | 6 | **MISMATCH → adjudicated a legitimate extra kill**: `R3A6::test_P6_mutation_…` also reds. It drops `TxnCasLostError` and asserts `reanchor_straggler: x` stays WARNING, and M5 made that sibling ERROR. My declaration missed that the adversary's leg uses reanchor as its sibling. Stayed-green: none |
| M6 | the tier table keyed by class NAME strings (behaviour identical) | TIERS "keys are CLASSES" + every key-reading leg + R3A6 mutation (D-AM7KEY) | 9 | **EXACT** · `10 failed` = 3 baseline + 9 declared − 2 overlapping |
| M7 | `claim_task` also swallows `TxnContentionExhaustedError` | SEAM identity | 1 (`[tasks.py::claim_task]`) | **EXACT** · `4 failed` = 3 baseline + 1 |
| M8 | **CORRECT build (control):** the heal's chunk apply extracted into a helper (F8's shape) | SEAM must NOT red a correct spelling (am-8 §3; BC-r2-9 deleted) | 0 | **EXACT** · `3 failed` = the baseline only |
| M9 | `_transition_fragment` reaches the shell through `getattr` (dynamic dispatch the graph cannot see) | SEAM runtime attribution ⊆ graph (the blind spot, named) | 1 (`[tasks.py::transition]`) | **EXACT** |
| M10 | a production `with contextlib.suppress(SurrealStoreError)` around an apply | §HELD 2 swallow rule (`test_the_whole_tree_swallow_rule_matches_its_pinned_bound_both_ways` after the am-9 fold; `test_no_production_suppress_…` before it) | 1 | **EXACT** (both before and after the fold) |
| M11 | `create_task` hand-rolls its RELATE (own params) beside `_relate_fragment` | REL registry == derived + the verb's leg | 2 | **MISMATCH → adjudicated a legitimate extra kill**: `[supersede_task]` also reds. Its driver creates the dependents through `create_task`, and the spy observes the whole driver. It is loud, and it names the rogue statement. Precision bound: REL attributes a rogue RELATE to the leg whose DRIVER composed it, fixtures included |
| M12 | `claim_task` logs `ERROR` to `loremaster.contention` on a routine loss | RU 8-way (F3 filter, DUAL R3-D3) + PB | 2 | **EXACT** · `2 failed` |
| M13 (test tree) | a second `ast.Expression` resolver function added to `SEAM` | §HELD 2 one-resolver pin | 1 | **EXACT** — ⚠ RETIRED with the pin (D-AM34: 63c-i-a owns it) |
| M14 (test tree) | the index walker reverted to `ast.Try` only | §HELD 2 TryStar discriminator | 1 | **EXACT** |
| M16 (am-9 §3/§5) | a WRAPPER above a minimal verb swallows (`acknowledge_quietly_58r3`: `except SurrealStoreError: return None` around `acknowledge`) | §HELD 2 whole-tree swallow rule (NEW site) | 1 | **EXACT** |
| M17 (am-9 §3, the other direction) | a KNOWN site FIXED (`tasks.py::transitive_blockers` gains `except TxnContentionExhaustedError: raise` above its broad clause) | the bound only SHRINKS (a stale entry reds) | 1 | **EXACT** — ⚠ RETIRED with the am-9 bound (D-AM10): under the fate rule that site is a DERIVED translate needing no row, so there is nothing to shrink |
| M10′ / M16′ (re-targeted by am-10) | as M10 (a production store-class `suppress`) / M16 (a swallowing wrapper) | `FATES::test_every_non_derived_site_has_a_row_and_every_row_a_site` | 1 each | **EXACT** ×2 |
| M18 (am-10) | a NEW silent swallow (`findings.quiet_58r3`: `except SurrealStoreError: return None`) | FATES registry (unregistered site) | 1 | **EXACT** |
| M19 (am-10) | a registered site's fate CHANGES (`briefs._release_version`'s `logger.warning` → `logger.debug`) | FATES evidence (*"the FATE CHANGED"*) | 1 | **EXACT** |
| M20 (am-10, the door) | a translation into a DOMAIN VERDICT (`tasks._reject_unusable_blockers` raises `UnknownBlockerError … from error`) | FATES registry (no longer derived → unregistered) | 1 | **EXACT** |
| M21 (am-10) | a translation DROPS its chain (`diff._ensure_connection`: `… ) from error` → `… )`) | FATES registry | 1 | **EXACT** |
| M22 (am-10 §4) | a pinned HOLE is FIXED (`server.run_startup_hooks`' inner `except BaseException: pass` gains a WARNING) | FATES evidence (*"a pinned HOLE now carries evidence"*) | 1 | **EXACT** |
| M23 (test tree) | test_retry_seam's resolver becomes a private wrapper again | §HELD 2 `test_this_index_resolves_through_THE_ONE_resolver` | 1 | **EXACT** |
| M2 (re-run after am-9 §5) | as M2 | + am-9 §5's {P, C, H} pin | 3 | **EXACT** · `3 failed, 48 passed` |
| M15 | a NEW inline CAS verb `assign_task_58r3` (shell + apply), undriven | SEAM population (STATIC ⊆ DRIVEN) | `[tasks.py::assign_task_58r3]` | **MISMATCH → adjudicated EXACT in substance**: the declared node id does not exist until the mutation adds it, so the pre-run `--collect-only` could not resolve it. That is a limit of my driver for mutations that ADD a parametrisation member. The one observed extra red is exactly that member, and nothing else reds |

**Verdict: 23 mutations (M10/M14/M16 re-run after each fold; M13 and M17 retired with their instruments, stated), all EXACT except the 3 adjudicated. The 3 mismatches are individually adjudicated: two extra kills, both mine to have declared, and one driver limit. No declared red stayed green, and no unexplained red appeared.** Results file: `…/scratchpad/r3/mut/results.json` (session-local; the table above transcribes it).

## §RED@HEAD — measured 2026-09-26 at HEAD `c383edd` (code = `c9e5eb8`), on a clean `scratch_copy.sh` copy + exactly this commit's test files (no §HELD, no build)
Provenance printed by the runner: `loremaster.__file__ = …/scratchpad/r3/head/loremaster/loremaster/__init__.py`.
- **Every file that imports `_reanchor_58_support`** (16 files, `-n 8`): **`192 failed, 611 passed, 1 skipped in 47.88s`**. Per file: `test_supersede_reanchor_58` 44 · `test_task_guarded_shell_58` 15 · `test_task_claimable_partition_58` 5 · `test_blocks_edge` 1 · `test_task_read_surface` 1 · r2 PRB 12 · SC 2 · A2 3 · RU 27. All of these are IDENTICAL to the adversary's r2 per-file table (`821be62` §P7), so the r1/r2 reds are untouched and RU's F3 edit changes no red at HEAD. New in r3: R3A6 8 · SEAM 9 · CONV 41 · R3P 6 · REL 2 · TIERS 16 = **82**. r2's deleted CR file took its 6 reds with it.
- **The 82 r3 reds, by first-exception class** (`--tb=line`, `82 failed, 23 passed in 20.09s`), each a RIGHT reason, meaning an unbuilt 58 mechanism or an un-landed index:
  - 32 × `measuring <shape>: 0 heal chunks for n=1` — no boot heal exists (CONV scale/mix legs).
  - 9 × `_txn has no attribute '_ROLLBACK_LOG_TIERS'` — no tier table (TIERS completeness + mutation legs).
  - 8 × `test_retry_seam has no attribute '_TYPED_CAS_CATCHES'` — the static index's partition is not at HEAD; a28b lands it (SEAM population).
  - 6 × F4 `expected ONE <event> per unresolvable entry` — no heal records.
  - 4 × `[40] == [30]`, 1 × `[40] == [10]`, and 5 × `TxnXError via …: expected … WARNING/DEBUG; got ['ERROR']` / `got []` — every rollback logs ERROR at HEAD, and a HEAD claim loss commits an empty UPDATE, so there is no rollback at all.
  - 2 × `DID NOT RAISE TaskLedgerError` (PA2 / R1 not built) · 1 × `DID NOT RAISE any of (TaskLedgerError, Exception)` (PE) · 1 × `no attribute 'StragglerHealPackerError'` (F10).
  - 2 × `CONTROL: a fully healable row is healed` and 2 × `assert 0 == 1` — no heal.
  - The remainder (the heal driver's `injection never fired`, `_reanchor_stragglers … composed NO RELATE`, `drivers for no derived verb (stale): ['_reanchor_stragglers']`, the heal-chunk trigger's `never composed a chunk`, two column mismatches, one `assert False` in PC) — no heal.
- **GREEN at HEAD, by design (23)**:
  - the shape-space non-vacuity pins (2);
  - the call-graph and identity discriminators, which are the instruments' own controls (5);
  - `REL`'s four non-heal verbs, which already route through `_relate_fragment`;
  - the ERROR-side tier legs (3), the deny-by-default leg, and the trigger-registry completeness;
  - PB: HEAD's claim loss commits an empty UPDATE and logs nothing, so there is no alarm;
  - and **SEAM's six non-heal identity legs**. At HEAD exhausted contention already propagates unchanged from `transition` / `claim_task` / `supersede_task` / the findings doors / the brief ack, and the real-race controls already hold. What is RED for those verbs at HEAD is the POPULATION pin: the tasks verbs are not yet call-graph CAS verbs (no shell), and the static index's partition is absent. So the identity legs guard the BUILD, and that is where they must hold (§SAT).

## §FLAGS — outside my writable set, or needing a decision (the exact edit, never made silently)
- **F-r3-1 (am-6 mechanism note, unpinned):** am-6 FORK-3's parenthetical *"a pin: no production module outside `_txn` compares a THROW text"* is not in am-7/am-8's worklists, and r3 does not build it. r2's one-literal pin covers `claim_lost:` only. Candidate: a generated AST pin over the markers `_txn` classifies (`cas_lost:` / `reanchor_straggler:` / `heal_chunk:` / `claim_lost:` / `governed_conflict:`) — each literal appears only in `_txn` and as the PREFIX of a THROW message constant. **Lead: build it in r4, or rule it covered?**
- **F-r3-2 (r2 fixtures still one-blocker-biased):** `SUP.seed_stragglers` / `measure_heal_shape` (used by r2's PR18r2/PR19/SIX-blockers pins) seed ONE-blocker rows only, which is F1's bias. r3's `CONV` sweep supersedes them as the property's pin. The r2 pins stay as hand instances and are left unedited, since they still pass on a correct build. A later tidy-up could route them through `CONV.seed_population`. Not a defect today.
- **F-r3-3 (RS-2 residual, unchanged):** adversary-58-r2 RS-2. An unbounded synchronous chain-follow HANGS the suite (`asyncio.wait_for` cannot cancel a sync loop), and r3's cyclic F4 legs inherit that hang-not-red shape. The fix is `pytest-timeout` or a subprocess boot. It is a harness decision, not a 58 pin. **Lead's call.**
- **F-r3-4 (the three routed drivers, FK-r3-4):** `floor_calibration` (record_measurement's fence tests), keeps (63c) and agents RS-5 (63c) each need a `CAS_SEAM_DRIVERS = {"<file>::<function>": driver}` entry in THEIR OWN test module. The driver shape is `async (env, ledger, seam: DriverSeamInjection) -> None`, it must call `seam.arm("<key>")` and `await seam.expect_the_SAME_instance(...)`, and it needs a real-verdict control. The routing is the lead's (am-7 §3 item 2).
- **F-r3-5 (cross-packet sequencing, 64b):** see §HELD re-verification step 2 and BC-r3-7.
- **F-r3-6 (`_THROW_RESULT_PREFIX` corpse in my REFERENCE, not a spec):** my `_txn` reference keeps am-6's now-unused `_THROW_RESULT_PREFIX`. That is reference hygiene only; the builder writes its own `_txn`.

## §INSTRUMENTS — pasted VERBATIM (brief-base §1; the scratch root `…/scratchpad/r3/` is session-local)
Re-run recipe:
1. `./scripts/scratch_copy.sh <dest>`, then `git checkout -- . && git clean -fd -e .venv`.
2. `git apply` the a28b working-copy diff of `test_retry_seam.py` (md5 `46427f86`, until a28b commits), then §HELD part 1, then part 3.
3. Run `build_ref58.py` (from `9f2f580:REPORT-adversary-58.md`), then `my_ref.py` + `my_ref_am6.py` (from `821be62:REPORT-adversary-58-r2.md`), then `my_ref_r3.py` (below). Result md5: `tasks.py 017bdb55` · `_txn.py a07f3e30`.
4. `git apply` §HELD part 2, copy this commit's test files in, commit in the copy, and `rm` `test_reanchor_58_r2_cas_runtime.py`.
5. Run `mut58r3.py <copy> <out>` for §MUTATION, or the full suite for §SAT.

`run.sh` is adversary-58-r2's, used unchanged (md5 `781d16b7` = its recorded value, `821be62` §INSTRUMENTS). `extract.py` (md5 `dfdf6e17`) pulls a fenced block out of a report by its `### \`name\`` heading. It is trivial and is described here, not pasted.

### `my_ref_r3.py` (md5 `c5678ba7b849be978b35da0a09a9405a`) — the am-7/am-8 reference deltas (a SAT/mutation host, NOT A SPEC)
```python
#!/usr/bin/env python3
"""contract-58-r3's reference deltas over adversary-58-r2's ref6 (build_ref58 + my_ref + my_ref_am6):
amendment 7 §4 (the rollback tier table keyed by CLASS; three typed classes for the 58 markers) and
amendment 8 §1/§4 (the heal packer = more_itertools.constrained_batches(strict=True) over rows built
ONCE; ONE WARNING per unresolvable ENTRY, the whole row skipped).  A SAT/mutation host — NOT A SPEC.
Usage: my_ref_r3.py <scratch-root>.  Each anchor asserted exactly once."""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
TASKS = ROOT / "loremaster/loremaster/tasks.py"
TXN = ROOT / "loremaster/loremaster/store/_txn.py"


def sub(src: str, old: str, new: str) -> str:
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:80]!r}"
    return src.replace(old, new)


txn = TXN.read_text()
txn = sub(txn, "class RetryableConflictSignal(Exception):", '''class TxnCasLostError(TxnDomainRejectionError):
    """A ledger's guarded CAS lost a race and THREW the ``cas_lost:`` marker (packet 58 am-6/am-7)."""


class TxnReanchorStragglerError(TxnDomainRejectionError):
    """A supersede's re-anchor met a dependent that appeared after its read (R1; ``reanchor_straggler:``)."""


class TxnHealChunkError(TxnDomainRejectionError):
    """A boot-heal chunk's row guard THREW ``heal_chunk:`` (the row moved under the heal)."""


class RetryableConflictSignal(Exception):''')
txn = sub(txn, '_ERROR_CLASS_CLAIM_LOST = "claim lost — another claimant won the compare-and-set"\n',
          '_ERROR_CLASS_CLAIM_LOST = "claim lost — another claimant won the compare-and-set"\n'
          '_ERROR_CLASS_CAS_LOST = "cas lost — a concurrent writer won the compare-and-set"\n'
          '_ERROR_CLASS_REANCHOR_STRAGGLER = "re-anchor straggler — a dependent appeared after the read"\n'
          '_ERROR_CLASS_HEAL_CHUNK = "heal chunk — a straggler row moved under the boot heal"\n')
txn = sub(txn, """_ROLLBACK_LOG_TIERS: dict[str, int] = {
    CLAIM_LOST_MARKER: logging.DEBUG,
    _GOVERNED_CONFLICT_MARKER: logging.WARNING,
    _CAS_LOST_MARKER: logging.WARNING,
    _REANCHOR_STRAGGLER_MARKER: logging.WARNING,
    _HEAL_CHUNK_MARKER: logging.WARNING,
}
""", "")
txn = sub(txn, """    if CLAIM_LOST_MARKER in lowered:
        return _ERROR_CLASS_CLAIM_LOST
""", """    if CLAIM_LOST_MARKER in lowered:
        return _ERROR_CLASS_CLAIM_LOST
    if _CAS_LOST_MARKER in lowered:
        return _ERROR_CLASS_CAS_LOST
    if _REANCHOR_STRAGGLER_MARKER in lowered:
        return _ERROR_CLASS_REANCHOR_STRAGGLER
    if _HEAL_CHUNK_MARKER in lowered:
        return _ERROR_CLASS_HEAL_CHUNK
""")
txn = sub(txn, """    if error_class == _ERROR_CLASS_CLAIM_LOST:
        return TxnClaimLostError(message)
    return TxnDomainRejectionError(message)
""", """    typed = _TYPED_DOMAIN_REJECTIONS.get(error_class)
    return typed(message) if typed is not None else TxnDomainRejectionError(message)


#: am-7 §4: the classifier's label → the typed class it raises (ONE mapping).
_TYPED_DOMAIN_REJECTIONS: dict[str, type[TxnDomainRejectionError]] = {
    _ERROR_CLASS_GOVERNED_CONFLICT: TxnGovernedConflictError,
    _ERROR_CLASS_CLAIM_LOST: TxnClaimLostError,
    _ERROR_CLASS_CAS_LOST: TxnCasLostError,
    _ERROR_CLASS_REANCHOR_STRAGGLER: TxnReanchorStragglerError,
    _ERROR_CLASS_HEAL_CHUNK: TxnHealChunkError,
}
#: am-7 §4: the rollback log tier, keyed by the CLASSIFIED CLASS; anything else ERROR (deny-by-default).
_ROLLBACK_LOG_TIERS: dict[type[SurrealStoreError], int] = {
    TxnClaimLostError: logging.DEBUG,
    TxnGovernedConflictError: logging.WARNING,
    TxnCasLostError: logging.WARNING,
    TxnReanchorStragglerError: logging.WARNING,
    TxnHealChunkError: logging.WARNING,
}
""")
txn = sub(txn, """    text = str(root_cause.raw_result).lower()
    thrown = text[len(_THROW_RESULT_PREFIX):].strip() if text.startswith(_THROW_RESULT_PREFIX) else ""
    level = next(
        (tier for prefix, tier in _ROLLBACK_LOG_TIERS.items() if thrown.startswith(prefix)), logging.ERROR
    )
""", """    level = _ROLLBACK_LOG_TIERS.get(error_type, logging.ERROR)
""")
txn = sub(txn, "            _log_rollback(root_cause, statement_count, failed_statements)\n            raise _domain_rejection_error(\n                error_class,",
          "            rejection = _domain_rejection_error(\n                error_class,")
txn = sub(txn, """                f"({error_class}); {_SERVER_LOG_HINT}",
            )
        last_conflict""", """                f"({error_class}); {_SERVER_LOG_HINT}",
            )
            _log_rollback(root_cause, statement_count, failed_statements, type(rejection))
            raise rejection
        last_conflict""")
txn = sub(txn, "            _log_rollback(*last_conflict)\n", "            _log_rollback(*last_conflict, TxnContentionExhaustedError)\n")
TXN.write_text(txn)
# _log_rollback's signature gains the classified class
txn = TXN.read_text()
import re
m = re.search(r"def _log_rollback\(\n(.*?)\) -> None:", txn, re.S)
assert m, "no _log_rollback signature"
txn = txn.replace(m.group(0), m.group(0).replace(") -> None:", "    error_type: type[BaseException],\n) -> None:"), 1)
TXN.write_text(txn)

src = TASKS.read_text()
src = sub(src, "import networkx\n", "import networkx\nfrom more_itertools import constrained_batches\n")
# am-8 §4 F4: ONE WARNING per unresolvable ENTRY; the whole row skipped (no break)
src = sub(src, """                    logger.warning(
                        _HEAL_CYCLE_EVENT,
                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    break
                if head not in existing:""", """                    logger.warning(
                        _HEAL_CYCLE_EVENT,
                        extra={"database": self._database, "task_id": dependent, "blocker_id": old},
                    )
                    skip = True
                    continue
                if head not in existing:""")
src = sub(src, """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    break
""", """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
""")
# am-8 §1: the packer IS constrained_batches(strict=True) over items built ONCE
src = sub(src, """        cap = _txn_module.TXN_STATEMENT_HARD_CAP
        chunks: list[list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]]] = []
        current: list[tuple[str, list[TxnFragment], list[tuple[str, str]], int]] = []
        used = 0
        for entry in built:
            if entry[3] > cap:
                raise StragglerHealPackerError(
                    f"straggler {render_attributed(entry[0])} alone composes {entry[3]} statements, over the "
                    f"{cap}-statement transaction cap — the heal cannot pack it"
                )
            if current and used + entry[3] > cap:
                chunks.append(current)
                current, used = [], 0
            current.append(entry)
            used += entry[3]
        if current:
            chunks.append(current)
""", """        cap = _txn_module.TXN_STATEMENT_HARD_CAP
        try:
            chunks = [
                list(batch)
                for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=True)
            ]
        except ValueError as error:
            worst = max(built, key=lambda entry: entry[3])
            raise StragglerHealPackerError(
                f"straggler {render_attributed(worst[0])} alone composes {worst[3]} statements, over the "
                f"{cap}-statement transaction cap — the heal cannot pack it"
            ) from error
""")
TASKS.write_text(src)
print("contract-58-r3 reference deltas applied")
```

### `held_part2.py` (md5 `6f3da7ea480cb3cc05ed42a3bb857e65`) — generates §HELD part 2 over a28b; the committed part 2 = its output + E501 rewraps of comments / docstrings and ONE f-string split (AST-neutral), then the `if True:` walker block dedented
```python
#!/usr/bin/env python3
"""Apply contract-58-r3's §HELD part 2 (the am-7/am-8 DELTA over 63c-i-a a28b's scanner) to
<root>/loremaster/tests/test_retry_seam.py.  Each anchor asserted exactly once."""
import sys
from pathlib import Path

PATH = Path(sys.argv[1]) / "loremaster/tests/test_retry_seam.py"
src = PATH.read_text()


def sub(old: str, new: str) -> None:
    global src
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:90]!r}"
    src = src.replace(old, new)


# --- A. the §8c header: the corpse prose rewritten (am-8 §6; adversary-58-r2 §DUAL F6) -----------------
sub("""# THE INVARIANT IS THEREFORE THE UNIVERSAL, not the instance (the PR93 quantifier law):
#
#     ∀ guarded-CAS handlers: exhausted contention propagates UNREAD.
#
# And the population is DISCOVERED, by the property that MAKES a handler a guarded CAS —
# `except SurrealStoreError` whose body RE-READS state (`await self._select…`). A fifth door
# is pinned the day it is written, by nobody's memory.
# ---------------------------------------------------------------------------
""", """# THE INVARIANT IS THEREFORE THE UNIVERSAL, not the instance (the PR93 quantifier law):
#
#     ∀ guarded-CAS handlers: exhausted contention propagates UNREAD.
#
# ⚠ DUAL (packet 58 contract r3, §HELD part 2 — REPORT-contract-58-r3.md; amendments 7 §1 + 8 §3/§6): this
# paragraph USED to say the population is found by *"`except SurrealStoreError` whose body RE-READS state
# (`await self._select…`)"*. Both halves of that sentence were retired (adversary-58-r2 F6: corpse prose):
#
#   * the DOMAIN (63c-i-a a28b, amendment 32 §1.3 f + 58 amendment 7 §1) — every catch SITE in the WHOLE
#     production tree (`try` / `try*` handlers and `with contextlib.suppress(...)`, 58 amendment 8 §3) whose
#     caught classes resolve BY IMPORT (Name / dotted Attribute / Tuple elements) to a `SurrealStoreError`
#     subclass; a HANDLER joins the re-read domain iff it awaits a same-class method whose body carries a
#     `SELECT` literal (a derived re-read, never a `_select` name prefix);
#   * the PARTITION (58 amendment 7 §0 row 1a) — a DOOR iff exhausted contention can reach it (some caught
#     class's subclass closure contains `TxnContentionExhaustedError`), else SAFE-BY-TYPE; a `suppress` site
#     can never re-read (it has no handler body), so it is judged by the closure alone: a suppress that can
#     swallow exhausted contention is RED by name (REPORT-contract-58-r3.md FK-r3-3).
#
# BOUND (stated, not hidden): a re-read through a helper OUTSIDE the class, or a `SELECT` built without a
# literal, is invisible to this STATIC domain. The ∀ itself no longer lives here — it is the DRIVER-SEAM
# injection (58 amendment 8 §3, `test_reanchor_58_r3_cas_seam.py`), which does not care how a catch or a
# re-read is spelled; this index is the REVIEWER-VISIBLE half, and the two are cross-checked both ways.
# ---------------------------------------------------------------------------
""")

# --- B. ONE resolver (58 amendment 7 §3 item 4): the eval site is a single function -----------------------
sub('''def _caught_classes(handler: ast.ExceptHandler, module: Any) -> list[type]:
    """Every class an ``except`` clause catches, RESOLVED BY IMPORT in its module's namespace — each element
    of
    a Tuple handler included, a ``Name`` or a dotted ``Attribute`` alike (amendment 32 §1.3 f: the old key
    read
    only a bare ``ast.Name`` spelled ``SurrealStoreError``, so a Tuple, a subclass name or an alias was
    invisible)."""
    if handler.type is None:
        return []
    elements = handler.type.elts if isinstance(handler.type, ast.Tuple) else [handler.type]
    resolved: list[type] = []
    for element in elements:
        try:
            value = eval(compile(ast.Expression(element), "<except>", "eval"), vars(module))  # noqa: S307
        except Exception:  # noqa: BLE001 - an unresolvable name is simply not a store class
            continue
        if inspect.isclass(value):
            resolved.append(value)
    return resolved
''', '''def _resolved_by_import(expression: ast.expr, module: Any) -> Any:
    """THE ONE resolver (packet 58 amendment 7 §3 item 4 — *"no second scanner, ever"*): evaluate a name /
    dotted attribute expression in its module's namespace, so an alias, a re-export or a dotted path resolves to the
    object it IS, never to how it is spelled.  ``None`` when it does not resolve.  Pinned as the ONLY function
    in the test tree that builds an ``ast.Expression`` to evaluate
    (``TestTheCatchFormsAreSeen::test_exactly_ONE_function_resolves_names_by_import``).
    """
    try:
        return eval(compile(ast.Expression(expression), "<catch-site>", "eval"), vars(module))  # noqa: S307
    except Exception:  # noqa: BLE001 - an unresolvable name is simply not a store class
        return None


def _caught_classes(site: ast.ExceptHandler | ast.Call, module: Any) -> list[type]:
    """Every class a catch SITE catches, RESOLVED BY IMPORT in its module's namespace — each element of a
    Tuple handler included, a ``Name`` or a dotted ``Attribute`` alike (amendment 32 §1.3 f: the old key read only a
    bare ``ast.Name`` spelled ``SurrealStoreError``, so a Tuple, a subclass name or an alias was invisible).

    ⚠ DUAL (packet 58 contract r3, §HELD part 2): ``site`` is now EITHER an ``except``/``except*`` handler OR
    the ``contextlib.suppress(...)`` call of a ``with`` statement (58 amendment 8 §3: the static index learns the
    catch FORMS — a correct build may catch by ``suppress``, a house idiom used 10× in production), resolved
    through the ONE :func:`_resolved_by_import`.
    """
    if isinstance(site, ast.Call):
        elements: list[ast.expr] = list(site.args)
    elif site.type is None:
        return []
    else:
        elements = list(site.type.elts) if isinstance(site.type, ast.Tuple) else [site.type]
    resolved: list[type] = []
    for element in elements:
        value = _resolved_by_import(element, module)
        if inspect.isclass(value):
            resolved.append(value)
    return resolved


def _suppress_calls(node: ast.With | ast.AsyncWith, module: Any) -> list[ast.Call]:
    """The ``contextlib.suppress(...)`` calls a ``with`` statement enters — the context expression resolved BY
    IMPORT (``contextlib.suppress``, ``from contextlib import suppress``, any alias bound to it alike)."""
    return [
        item.context_expr
        for item in node.items
        if isinstance(item.context_expr, ast.Call)
        and _resolved_by_import(item.context_expr.func, module) is contextlib.suppress
    ]
''')

# --- C. the domain walk: per-module, over `try` AND `try*` (am-8 §3) ---------------------------------------
sub('''    doors: dict[str, tuple[str, int, bool, bool]] = {}
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        module = _module_of(key)
        tree = ast.parse(path.read_text(encoding="utf-8"))
        parents: dict[int, ast.AST] = {}
        for parent in ast.walk(tree):
            for child in ast.iter_child_nodes(parent):
                parents[id(child)] = parent
        for node in ast.walk(tree):
            if not isinstance(node, ast.Try):
                continue
''', '''    doors: dict[str, tuple[str, int, bool, bool]] = {}
    for key, tree, module in _production_module_trees():
        doors.update(_cas_handlers_in(key, tree, module))
    return doors


def _production_module_trees() -> list[tuple[str, ast.Module, Any]]:
    """``(package-relative path, parsed tree, imported module)`` for every production module — the tree walk
    the whole index ranges over (the file set is an OUTPUT of the walk, never an input: 58 amendment 7 §0)."""
    modules: list[tuple[str, ast.Module, Any]] = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        key = path.relative_to(_PACKAGE_ROOT).as_posix()
        modules.append((key, ast.parse(path.read_text(encoding="utf-8")), _module_of(key)))
    return modules


def _parents_of(tree: ast.AST) -> dict[int, ast.AST]:
    parents: dict[int, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[id(child)] = parent
    return parents


def _cas_handlers_in(key: str, tree: ast.AST, module: Any) -> dict[str, tuple[str, int, bool, bool]]:
    """ONE module's slice of the derived domain (see :func:`_discover_cas_handlers`) — split out so the
    catch-form discriminators can run the SAME walk over a synthetic source (58 amendment 8 §3)."""
    doors: dict[str, tuple[str, int, bool, bool]] = {}
    parents = _parents_of(tree)
    if True:
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Try, ast.TryStar)):
                continue
''')
sub('''                where = getattr(scope, "name", "<lambda>") if scope else "<module>"
                doors[f"{key}::{where}"] = (key, handler.lineno, reachable, guarded_above)
    return doors
''', '''                where = getattr(scope, "name", "<lambda>") if scope else "<module>"
                doors[f"{key}::{where}"] = (key, handler.lineno, reachable, guarded_above)
    return doors


def _suppress_sites_in(key: str, tree: ast.AST, module: Any) -> dict[str, tuple[str, int, bool]]:
    """ONE module's ``with contextlib.suppress(<store class>)`` sites:
    ``{"<module>::<function>": (file, lineno, reachable)}`` — ``reachable`` = some suppressed class's subclass closure contains
    :class:`TxnContentionExhaustedError` (58 amendment 8 §3; FK-r3-3: a suppress has no handler body, so it
    SWALLOWS whatever it catches — a reachable one swallows exhausted contention)."""
    sites: dict[str, tuple[str, int, bool]] = {}
    parents = _parents_of(tree)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.With, ast.AsyncWith)):
            continue
        for call in _suppress_calls(node, module):
            caught = _caught_classes(call, module)
            if not any(issubclass(cls, SurrealStoreError) for cls in caught):
                continue
            scope = _enclosing_callable(node, parents)
            where = getattr(scope, "name", "<lambda>") if scope else "<module>"
            reachable = any(issubclass(TxnContentionExhaustedError, cls) for cls in caught)
            sites[f"{key}::{where}"] = (key, node.lineno, reachable)
    return sites


def _discover_suppress_sites() -> dict[str, tuple[str, int, bool]]:
    """Every store-class ``suppress`` site in the production tree (see :func:`_suppress_sites_in`)."""
    sites: dict[str, tuple[str, int, bool]] = {}
    for key, tree, module in _production_module_trees():
        sites.update(_suppress_sites_in(key, tree, module))
    return sites
''')

# --- D. the claim_task comment (FK-r3-1) --------------------------------------------------------------------
sub("""# decide from ONE class (amendment 32 §1.2, R-6; the class named by amendment 33). 58's §HELD delta adds
# ``tasks.py::claim_task`` (TxnClaimLostError, 58 amendment 4). EXACT, both ways.
""", """# decide from ONE class (amendment 32 §1.2, R-6; the class named by amendment 33). EXACT, both ways.
# ⚠ DUAL (packet 58 contract r3, §HELD part 2; REPORT-contract-58-r3.md FK-r3-1): this comment USED to say
# 58's delta adds ``tasks.py::claim_task``. It does NOT: a ruled claim (am-3 §3 ``except TxnClaimLostError``, the
# owner read AFTER the ``try``; am-5 rejected an inline re-read) has no re-reading handler, so it is outside
# the DERIVED domain amendment 7 §1 rules (re-read presence is the domain filter) — listing it would RED every
# correct build.  Its exhaustion safety is pinned by the driver-seam ∀ (58 amendment 8 §3).
""")

# --- E. the catch-form pins (am-8 §3) + the one-resolver pin (am-7 §3 item 4) -------------------------------
sub('''class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:
''', '''_SYNTHETIC_CATCH_FORMS = """
import contextlib
from contextlib import suppress
from loremaster.store._txn import SurrealStoreError, TxnClaimLostError, TxnContentionExhaustedError

ALIAS = contextlib.suppress


class Ledger:
    async def _reread(self):
        return await self._query("SELECT * FROM t")

    async def star_door(self):
        try:
            await self._apply()
        except* SurrealStoreError:
            await self._reread()

    async def star_typed(self):
        try:
            await self._apply()
        except* TxnClaimLostError:
            await self._reread()

    async def star_guarded(self):
        try:
            await self._apply()
        except* TxnContentionExhaustedError:
            raise
        except* SurrealStoreError:
            await self._reread()

    async def suppress_broad(self):
        with contextlib.suppress(SurrealStoreError):
            await self._apply()

    async def suppress_typed(self):
        with suppress(TxnClaimLostError):
            await self._apply()

    async def suppress_alias_broad(self):
        with ALIAS(SurrealStoreError, KeyError):
            await self._apply()

    async def suppress_unrelated(self):
        with contextlib.suppress(KeyError):
            await self._apply()

    async def not_a_suppress(self):
        with open("x") as handle:
            await self._apply(handle)
"""


def _synthetic_module() -> tuple[ast.Module, Any]:
    """The catch-form discriminator source, parsed and EXECUTED into a real module namespace (so every name
    resolves BY IMPORT exactly as production's do).  The ``except*`` bodies await; Python accepts that only
    inside an ``async def`` — which is where they are."""
    import types

    module = types.ModuleType("synthetic_catch_forms_58r3")
    exec(compile(_SYNTHETIC_CATCH_FORMS, "<synthetic>", "exec"), vars(module))  # noqa: S102
    return ast.parse(_SYNTHETIC_CATCH_FORMS), module


class TestTheCatchFormsAreSeen:
    """Packet 58 amendment 8 §3 (+ amendment 7 §3 item 4): the reviewer-visible index learns the catch FORMS —
    ``try*`` handlers and ``with contextlib.suppress(...)`` — through the SAME resolver and the SAME closure
    predicate, and there is exactly ONE resolver.  ⚠ DUAL: new in contract r3; RED at HEAD ``c9e5eb8`` only
    for the ``TryStar`` / ``suppress`` legs whose walk does not exist before §HELD part 2 lands."""

    def test_try_STAR_handlers_join_the_domain_and_the_partition(self) -> None:
        tree, module = _synthetic_module()
        found = _cas_handlers_in("synthetic.py", tree, module)
        assert found.keys() == {
            "synthetic.py::star_door", "synthetic.py::star_typed", "synthetic.py::star_guarded"
        }, sorted(found)
        _file, _line, reachable, guarded = found["synthetic.py::star_door"]
        assert reachable and not guarded, "an unguarded `except* SurrealStoreError` re-reader is a door"
        assert not found["synthetic.py::star_typed"][2], "`except* TxnClaimLostError` is safe BY TYPE"
        assert all(found["synthetic.py::star_guarded"][2:]), "a `try*` guard clause above counts"

    def test_suppress_sites_resolve_BY_IMPORT_and_are_judged_by_the_closure(self) -> None:
        tree, module = _synthetic_module()
        sites = _suppress_sites_in("synthetic.py", tree, module)
        assert sites.keys() == {
            "synthetic.py::suppress_broad",
            "synthetic.py::suppress_typed",
            "synthetic.py::suppress_alias_broad",
        }, sorted(sites)
        assert sites["synthetic.py::suppress_broad"][2] is True
        assert sites["synthetic.py::suppress_alias_broad"][2] is True, "an ALIAS of suppress is suppress"
        assert sites["synthetic.py::suppress_typed"][2] is False
        assert not _cas_handlers_in("synthetic.py", tree, module).keys() & sites.keys(), (
            "a suppress site has no handler body: it never enters the RE-READ domain (FK-r3-3)"
        )

    def test_no_production_suppress_can_swallow_exhausted_contention(self) -> None:
        swallowing = {site: where for site, where in _discover_suppress_sites().items() if where[2]}
        assert not swallowing, (
            f"`with contextlib.suppress(...)` sites that can SWALLOW exhausted contention: "
            f"{sorted(swallowing)}. Our write never committed and the driver gave up; a suppress turns that "
            f"into silent success — the #102 lie with no re-read even needed.  Catch a TYPED domain class, or let exhaustion propagate."
        )

    def test_exactly_ONE_function_resolves_names_by_import(self) -> None:
        """58 amendment 7 §3 item 4 — *"No second scanner, ever"*: the test tree + scripts hold exactly ONE
        function that builds an ``ast.Expression`` to evaluate (the resolver).  BOUND: keyed on the
        ``ast.Expression`` constructor — a resolver spelled another way (``getattr`` chains over
        ``vars(module)``) is not seen; the ALLOWLIST is the one symbol, so a second copy of THIS spelling reds by name."""
        from _logging_fixtures import parse_production_trees

        builders: set[str] = set()
        # THE ONE tree parser (finding #279 / F4); the scan's domain = every test tree + scripts.
        trees = parse_production_trees(include_scripts=True, include_tests=True)
        for relative, tree in sorted(trees.items()):
            if "/tests/" not in f"/{relative}" and not relative.startswith("scripts/"):
                continue
            for function in ast.walk(tree):
                if not isinstance(function, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                if any(
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == "Expression"
                    and isinstance(call.func.value, ast.Name)
                    and call.func.value.id == "ast"
                    for call in ast.walk(function)
                ):
                    builders.add(f"{Path(relative).name}::{function.name}")
        assert builders == {"test_retry_seam.py::_resolved_by_import"}, sorted(builders)


class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:
''')
PATH.write_text(src)
print("§HELD part 2 applied")
```

### `held_part2_am9.py` (md5 `82938725ae3a5d44721287dde0ee38b2`) — the am-9 / 63c am-34 fold, applied AFTER `held_part2.py`; the committed part 2 = both, then rebased onto `e039c64` (a one-line base difference inside the replaced block)
```python
#!/usr/bin/env python3
"""contract-58-r3: fold packet-58 amendment 9 (4cb8ce9) + 63c amendment 34 §5 into §HELD part 2 — the whole-tree,
form-blind SWALLOW RULE (am-9 §3) with the pinned KNOWN BOUND (FK-r3-7), and the one-scanner pin REMOVED (owned
by 63c-i-a).  Applied to <root>/loremaster/tests/test_retry_seam.py AFTER held_part2.py.  Anchors exactly once."""
import sys
from pathlib import Path

PATH = Path(sys.argv[1]) / "loremaster/tests/test_retry_seam.py"
src = PATH.read_text()


def sub(old: str, new: str) -> None:
    global src
    count = src.count(old)
    assert count == 1, f"anchor occurs {count}x: {old[:90]!r}"
    src = src.replace(old, new)


def cut(start: str, end: str, new: str) -> None:
    """Replace the span from ``start`` (inclusive) to ``end`` (exclusive)."""
    global src
    assert src.count(start) == 1 and src.count(end) >= 1, (start[:60], end[:60])
    i = src.index(start)
    j = src.index(end, i)
    src = src[:i] + new + src[j:]


cut("def _suppress_sites_in(", "def _discover_guarded_cas_handlers(", '''def _reraises_unchanged(handler: ast.ExceptHandler) -> bool:
    """Whether a handler lets what it caught go UNCHANGED: its body ENDS in a bare ``raise`` (or ``raise
    <its as-name>``) and has no other exit — no ``return`` / ``continue`` / ``break`` and no ``raise`` of
    anything else (nested defs excluded).  A log-then-reraise is unchanged; a translation (``raise X from e``)
    or a conditional re-raise with another exit is NOT."""
    if not handler.body:
        return False
    last = handler.body[-1]

    def _is_same(raise_node: ast.Raise) -> bool:
        return raise_node.exc is None or (
            isinstance(raise_node.exc, ast.Name) and raise_node.exc.id == handler.name
        )

    if not (isinstance(last, ast.Raise) and _is_same(last)):
        return False
    pending: list[ast.AST] = list(handler.body)
    while pending:
        node = pending.pop()
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
            continue
        if isinstance(node, (ast.Return, ast.Continue, ast.Break)):
            return False
        if isinstance(node, ast.Raise) and not _is_same(node):
            return False
        pending.extend(ast.iter_child_nodes(node))
    return True


def _swallow_sites_in(key: str, tree: ast.AST, module: Any) -> dict[str, tuple[str, int, str]]:
    """ONE module's EXHAUSTION-SWALLOW sites (packet 58 amendment 9 §3 — whole tree, FORM-BLIND):
    ``{"<module>::<function>": (file, lineno, form)}`` for every catch site — a ``try`` / ``try*`` handler
    or a ``with contextlib.suppress(...)`` — whose caught classes are in the store DOMAIN (some caught class
    resolves BY IMPORT inside ``SurrealStoreError``'s tree; REPORT-contract-58-r3.md FK-r3-7 Reading (ii)),
    whose closure contains :class:`TxnContentionExhaustedError`, and which does NOT let it through
    unchanged: no clause catching it ABOVE in the same ``try``, and the handler itself does not
    :func:`_reraises_unchanged`.  A ``suppress`` never lets anything through, so every store-class
    ``suppress`` over exhaustion is a site."""
    sites: dict[str, tuple[str, int, str]] = {}
    parents = _parents_of(tree)

    def _record(node: ast.AST, form: str) -> None:
        scope = _enclosing_callable(node, parents)
        where = getattr(scope, "name", "<lambda>") if scope else "<module>"
        sites.setdefault(f"{key}::{where}", (key, getattr(node, "lineno", 0), form))

    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.TryStar)):
            for index, handler in enumerate(node.handlers):
                caught = _caught_classes(handler, module)
                if not any(issubclass(cls, SurrealStoreError) for cls in caught):
                    continue
                if not any(issubclass(TxnContentionExhaustedError, cls) for cls in caught):
                    continue
                guarded_above = any(
                    issubclass(TxnContentionExhaustedError, cls)
                    for earlier in node.handlers[:index]
                    for cls in _caught_classes(earlier, module)
                )
                if guarded_above or _reraises_unchanged(handler):
                    continue
                _record(handler, "try*" if isinstance(node, ast.TryStar) else "try")
        elif isinstance(node, (ast.With, ast.AsyncWith)):
            for call in _suppress_calls(node, module):
                caught = _caught_classes(call, module)
                if any(issubclass(cls, SurrealStoreError) for cls in caught) and any(
                    issubclass(TxnContentionExhaustedError, cls) for cls in caught
                ):
                    _record(node, "suppress")
    return sites


def _discover_swallow_sites() -> dict[str, tuple[str, int, str]]:
    """Every exhaustion-swallow site in the production tree (see :func:`_swallow_sites_in`)."""
    sites: dict[str, tuple[str, int, str]] = {}
    for key, tree, module in _production_module_trees():
        sites.update(_swallow_sites_in(key, tree, module))
    return sites


# THE PINNED KNOWN BOUND (packet 58 amendment 9 §3 × REPORT-contract-58-r3.md FK-r3-7; CLAUDE.md "WHEN YOU
# CANNOT CLOSE A HOLE, PIN IT"). am-9 §3 rules the swallow rule on the premise "a correct build is never RED
# under it"; MEASURED 2026-09-26, the tree already holds these sites — none of them packet 58's.  They are NOT
# declared safe (the rule's SAFE set is: a typed catch whose closure excludes exhaustion, or a site that lets
# it through unchanged); they are declared KNOWN, each classified, so a NEW site reds by name and a FIXED one
# reds until its entry is deleted.  RE-OPEN TRIGGER: the ruling on whether a TRANSLATION of exhausted
# contention (``raise X from e`` — the connection-bootstrap family and the two task reads) is a lie, and who
# owns the swallows.
_BOOTSTRAP_TRANSLATION = "translate: session-bootstrap exhaustion -> SurrealConnectionError"
_KNOWN_EXHAUSTION_SWALLOW_SITES: dict[str, str] = {
    "agents.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "audit.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "briefs.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "briefs.py::_release_version": "swallow: `except SurrealStoreError`, no guard (best-effort release)",
    "diff.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "findings.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "floor_calibration/store.py::_ensure_connection": (
        "translate: session-bootstrap exhaustion -> SurrealConnectionError"
    ),
    "floor_calibration/store.py::_fence_verdict": "swallow: the fence re-read's `except SurrealStoreError`",
    "graph_surreal.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "index/indexer.py::_commit_batch_file": "swallow: `except SurrealStoreError` -> continue (per-file)",
    "index/indexer.py::_index_chunks": "swallow: `except SurrealStoreError` -> continue (per-chunk)",
    "index/indexer.py::_resolve_all_extension_edges": "swallow: `except SurrealStoreError` -> continue",
    "index/snapshots.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "index/surreal_manifest.py::_ensure_connection": (
        "translate: session-bootstrap exhaustion -> SurrealConnectionError"
    ),
    "keeps.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "memory/local.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "messages.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "principal_keys.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "principals.py::_dispatch_report_unmigrated": "swallow: a CLI dispatch's broad store catch",
    "principals.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "server.py::_resolve_or_acknowledge_many": "swallow: per-item batch fate `continue` on exhaustion",
    "store/lease.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "store/surreal.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "tasks.py::_ensure_connection": _BOOTSTRAP_TRANSLATION,
    "tasks.py::_reject_unusable_blockers": "translate: a blocker read's store error -> a domain error",
    "tasks.py::transitive_blockers": "translate: the closure read's store error -> a domain error",
}


''')

sub('''    async def suppress_broad(self):
        with contextlib.suppress(SurrealStoreError):
            await self._apply()
''', '''    async def suppress_broad(self):
        with contextlib.suppress(SurrealStoreError):
            await self._apply()

    async def handler_translates(self):
        try:
            await self._apply()
        except TxnContentionExhaustedError as error:
            raise KeyError("gone") from error

    async def handler_logs_then_reraises(self):
        try:
            await self._apply()
        except SurrealStoreError:
            print("logged")
            raise

    async def handler_reraises_on_one_path(self, flag):
        try:
            await self._apply()
        except SurrealStoreError:
            if flag:
                raise
            return None
''')

sub('''    def test_suppress_sites_resolve_BY_IMPORT_and_are_judged_by_the_closure(self) -> None:
        tree, module = _synthetic_module()
        sites = _suppress_sites_in("synthetic.py", tree, module)
        assert sites.keys() == {
            "synthetic.py::suppress_broad",
            "synthetic.py::suppress_typed",
            "synthetic.py::suppress_alias_broad",
        }, sorted(sites)
        assert sites["synthetic.py::suppress_broad"][2] is True
        assert sites["synthetic.py::suppress_alias_broad"][2] is True, "an ALIAS of suppress is suppress"
        assert sites["synthetic.py::suppress_typed"][2] is False
        assert not _cas_handlers_in("synthetic.py", tree, module).keys() & sites.keys(), (
            "a suppress site has no handler body: it never enters the RE-READ domain (FK-r3-3)"
        )
''', '''    def test_the_swallow_rule_is_FORM_BLIND_and_resolves_BY_IMPORT(self) -> None:
        """am-9 §3 over every catch form: a store-class ``suppress`` (incl. an ALIAS of it), an unguarded
        ``except*`` re-reader, a TRANSLATION, and a conditional re-raise with another exit are sites; a typed
        catch, a guarded ``except*``, a log-then-reraise, a non-store ``suppress`` and a non-suppress ``with``
        are not.  A suppress never enters the RE-READ domain (FK-r3-3)."""
        tree, module = _synthetic_module()
        sites = _swallow_sites_in("synthetic.py", tree, module)
        assert sites.keys() == {
            "synthetic.py::star_door",
            "synthetic.py::suppress_broad",
            "synthetic.py::suppress_alias_broad",
            "synthetic.py::handler_translates",
            "synthetic.py::handler_reraises_on_one_path",
        }, sorted(sites)
        assert sites["synthetic.py::suppress_alias_broad"][2] == "suppress", "an ALIAS of suppress counts"
        assert sites["synthetic.py::star_door"][2] == "try*"
        assert not _cas_handlers_in("synthetic.py", tree, module).keys() & {
            "synthetic.py::suppress_broad", "synthetic.py::suppress_alias_broad"
        }, "a suppress site has no handler body: it never enters the RE-READ domain (FK-r3-3)"
''')

cut("    def test_no_production_suppress_can_swallow_exhausted_contention(self) -> None:",
    "class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:", '''    def test_the_whole_tree_swallow_rule_matches_its_pinned_bound_both_ways(self) -> None:
        """am-9 §3 — ∀ catch sites in the WHOLE production tree, form-blind.  A NEW exhaustion-swallow site
        reds BY NAME (a wrapper above a minimal CAS verb included — am-9 §5's rider); a KNOWN site that stops
        swallowing reds until its bound entry is deleted (the bound only shrinks — FK-r3-7)."""
        found = set(_discover_swallow_sites())
        known = set(_KNOWN_EXHAUSTION_SWALLOW_SITES)
        assert found == known, (
            f"NEW sites that can swallow or reinterpret exhausted contention: {sorted(found - known)} — "
            f"our write never committed and the driver gave up; catch a TYPED domain class, or carry `except "
            f"TxnContentionExhaustedError: raise` ABOVE the broad clause, or re-raise unchanged.  "
            f"KNOWN-bound "
            f"entries that no longer swallow (delete them; the bound only shrinks): {sorted(known - found)}"
        )


''')

sub('''    """Packet 58 amendment 8 §3 (+ amendment 7 §3 item 4): the reviewer-visible index learns the catch FORMS —
    ``try*`` handlers and ``with contextlib.suppress(...)`` — through the SAME resolver and the SAME closure
    predicate, and there is exactly ONE resolver.  ⚠ DUAL: new in contract r3; RED at HEAD ``c9e5eb8`` only
    for the ``TryStar`` / ``suppress`` legs whose walk does not exist before §HELD part 2 lands."""''',
    '''    """Packet 58 amendments 8 §3 + 9 §3: the reviewer-visible index learns the catch FORMS — ``try*`` handlers
    and ``with contextlib.suppress(...)`` — through the ONE resolver and the SAME closure predicate, and the
    whole-tree SWALLOW rule rides the same walker.  (The "exactly one scanner function" pin is 63c-i-a's — 63c
    amendment 34 §5.)  ⚠ DUAL: new in contract r3 (§HELD part 2)."""''')

sub('''#   * the PARTITION (58 amendment 7 §0 row 1a) — a DOOR iff exhausted contention can reach it (some caught
#     class's subclass closure contains `TxnContentionExhaustedError`), else SAFE-BY-TYPE; a `suppress` site
#     can never re-read (it has no handler body), so it is judged by the closure alone: a suppress that can
#     swallow exhausted contention is RED by name (REPORT-contract-58-r3.md FK-r3-3).''',
    '''#   * the PARTITION (58 amendment 7 §0 row 1a) — a DOOR iff exhausted contention can reach it (some caught
#     class's subclass closure contains `TxnContentionExhaustedError`), else SAFE-BY-TYPE; a `suppress` site
#     can never re-read (it has no handler body), so it never joins the exact sets (FK-r3-3);
#   * the SWALLOW RULE (58 amendment 9 §3) — ∀ store-class catch sites in the whole tree, every FORM: one that
#     can catch exhausted contention and does not let it through unchanged is RED by name, against a pinned,
#     only-shrinking KNOWN bound of the sites that pre-date the rule (REPORT-contract-58-r3.md FK-r3-7).''')
PATH.write_text(src)
print("am-9 fold applied to §HELD part 2")
```

### `held_part2_am10.py` (md5 `e2f317dd17d28d6934811f0aca58f3f8`) — the am-10 fold of §HELD part 2 (applied after `held_part2.py` + `held_part2_am9.py`)
```python
#!/usr/bin/env python3
"""contract-58-r3: fold packet-58 amendment 10 (5b72471) into §HELD part 2 — test_retry_seam's resolver becomes an
IMPORT of the ONE walker/resolver (`_catch_sites`, committed by r3), and the swallow rule LEAVES this file (it is
now the repo-level fate classifier, `test_exhaustion_fates.py`).  Applied AFTER held_part2.py + held_part2_am9.py.
Anchors exactly once."""
import sys
from pathlib import Path

PATH = Path(sys.argv[1]) / "loremaster/tests/test_retry_seam.py"
src = PATH.read_text()


def cut(start: str, end: str, new: str) -> None:
    global src
    assert src.count(start) == 1, (src.count(start), start[:70])
    i = src.index(start)
    j = src.index(end, i)
    src = src[:i] + new + src[j:]


def sub(old: str, new: str) -> None:
    global src
    assert src.count(old) == 1, (src.count(old), old[:70])
    src = src.replace(old, new)


# 1. the resolver trio -> imports of THE ONE walker/resolver (am-9 §3; 63c am-34 §5 owns the one-scanner pin)
cut("def _resolved_by_import(", "def _issues_a_read(", '''# ⚠ DUAL (packet 58 contract r3, §HELD part 2 — REPORT-contract-58-r3.md D-AM10): a28b's private
# ``_caught_classes`` (Name / Attribute / Tuple elements, resolved by import) is now an IMPORT of THE ONE
# catch-site resolver in ``_catch_sites`` (packet 58 amendments 9 §3 + 10 §2: ONE walker, ONE resolver, every
# catch form — ``except``, ``except*``, ``contextlib.suppress``).  Same behaviour for every handler this index
# reads (a bare ``except:`` now resolves to ``BaseException``: outside the store domain, like a28b's ``[]``).
from _catch_sites import caught_classes as _caught_classes  # noqa: E402
from _catch_sites import suppress_calls as _suppress_calls  # noqa: E402


''')
# 2. the swallow rule leaves this file (it is test_exhaustion_fates' fate classifier now)
cut("def _reraises_unchanged(", "def _discover_guarded_cas_handlers(", "")
cut("    async def handler_translates(self):", "    async def suppress_typed(self):", "")
cut("    def test_the_swallow_rule_is_FORM_BLIND_and_resolves_BY_IMPORT(self) -> None:",
    "class TestEveryGuardedCasDoorPropagatesExhaustionUNREAD:", '''    def test_this_index_resolves_through_THE_ONE_resolver(self) -> None:
        """Sharing by IDENTITY (CLAUDE.md "prove sharing by mutation"): the index's resolver IS the fate
        classifier's — change ``_catch_sites.caught_classes`` and both instruments move together."""
        import _catch_sites

        assert _caught_classes is _catch_sites.caught_classes
        assert _suppress_calls is _catch_sites.suppress_calls


''')
# 3. prose: the §8c header bullet and the class docstring point at the fate classifier
sub('''#   * the SWALLOW RULE (58 amendment 9 §3) — ∀ store-class catch sites in the whole tree, every FORM: one that
#     can catch exhausted contention and does not let it through unchanged is RED by name, against a pinned,
#     only-shrinking KNOWN bound of the sites that pre-date the rule (REPORT-contract-58-r3.md FK-r3-7).''',
    '''#   * the FATE RULE (58 amendments 9 §3 + 10) lives in ``test_exhaustion_fates.py``, on the SAME walker and
#     resolver (``_catch_sites``): every catch site that can reach exhausted contention must PASS it through,
#     TRANSLATE it to a fault class ``from`` the cause, or carry a registered row proving a named isolation.''')
sub('''    """Packet 58 amendments 8 §3 + 9 §3: the reviewer-visible index learns the catch FORMS — ``try*`` handlers
    and ``with contextlib.suppress(...)`` — through the ONE resolver and the SAME closure predicate, and the
    whole-tree SWALLOW rule rides the same walker.  (The "exactly one scanner function" pin is 63c-i-a's — 63c
    amendment 34 §5.)  ⚠ DUAL: new in contract r3 (§HELD part 2)."""''', '''    """Packet 58 amendments 8 §3 + 9 §3 + 10: the reviewer-visible index learns the catch FORMS — ``try*``
    handlers — through THE ONE resolver (``_catch_sites``), shared by identity with the fate classifier.  (The
    "exactly one scanner function" pin is 63c-i-a's — 63c amendment 34 §5.)  ⚠ DUAL: new in contract r3 (§HELD
    part 2)."""''')
PATH.write_text(src)
print("am-10 fold applied to §HELD part 2")
```

### `swallow_measure.py` (md5 `1cc529005adc63dff178dd855b1454cc`) — FK-r3-7's measurement (26 / 57); run from a scratch copy's `loremaster/tests` dir with the am-9 part-2 helpers
```python
"""Measure am-9 §3's whole-tree SWALLOW rule over the production tree the imported loremaster resolves to."""
import ast, sys
sys.path.insert(0, sys.argv[1])  # the tests dir
import test_retry_seam as rs
from loremaster.store._txn import TxnContentionExhaustedError as EXH

def exits_other(handler):
    for node in ast.walk(ast.Module(body=handler.body, type_ignores=[])):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            continue
        if isinstance(node, (ast.Return, ast.Continue, ast.Break)):
            return True
        if isinstance(node, ast.Raise) and node.exc is not None and not (isinstance(node.exc, ast.Name) and node.exc.id == handler.name):
            return True
    return False

def reraises(handler):
    last = handler.body[-1] if handler.body else None
    ok_last = isinstance(last, ast.Raise) and (last.exc is None or (isinstance(last.exc, ast.Name) and last.exc.id == handler.name))
    return ok_last and not exits_other(handler)

rows = []
for key, tree, module in rs._production_module_trees():
    parents = rs._parents_of(tree)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Try, ast.TryStar)):
            for i, h in enumerate(node.handlers):
                caught = rs._caught_classes(h, module)
                if not any(issubclass(EXH, c) for c in caught):
                    continue
                above = any(issubclass(EXH, c) for e in node.handlers[:i] for c in rs._caught_classes(e, module))
                if above or reraises(h):
                    continue
                scope = rs._enclosing_callable(h, parents)
                rows.append((f"{key}::{getattr(scope,'name','<module>')}", h.lineno, [c.__name__ for c in caught]))
        if isinstance(node, (ast.With, ast.AsyncWith)):
            for call in rs._suppress_calls(node, module):
                if any(issubclass(EXH, c) for c in rs._caught_classes(call, module)):
                    rows.append(("suppress " + key, node.lineno, []))
for r in rows: print(*r)
print("VIOLATIONS", len(rows))
```

### `mut58r3.py` (md5 `42694a18ead5931e0f33ec32294c25ec`) — the declare-then-diff mutation driver (final state: M13/M17 retired; M10/M16 re-targeted to the fate registry; M18–M23 added)
```python
#!/usr/bin/env python3
"""contract-58-r3 mutation driver — DECLARE-then-diff, BOTH ways, on the ref copy.

For each mutation: (1) resolve the DECLARED red set against `pytest --collect-only -q` of its scope (fixed
before any run); (2) apply the edit (each anchor asserted exactly once; each edited file asserted CHANGED);
(3) run the scope; (4) diff observed reds vs (scope baseline reds ∪ declared) both ways — UNEXPECTED reds
and declared reds that stayed GREEN (a mutation that landed in dead code); (5) restore via `git checkout`
and assert the tree is clean.  Usage: mut58r3.py <ref-root> <out-dir> [mutation ids...]"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(sys.argv[1]); OUT = Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
ONLY = set(sys.argv[3:])
PY = str(ROOT / ".venv/bin/python")
T = "loremaster/tests/"
TASKS = "loremaster/loremaster/tasks.py"; TXN = "loremaster/loremaster/store/_txn.py"
SC = {
    "conv": [T + "test_reanchor_58_r3_convergence.py", T + "test_reanchor_58_r3_probes.py"],
    "tier": [T + "test_reanchor_58_r3_tiers.py", T + "test_reanchor_58_r3_am6.py", T + "test_reanchor_58_r3_probes.py"],
    "cas": [T + "test_reanchor_58_r3_cas_seam.py"],
    "rel": [T + "test_reanchor_58_r3_relate.py"],
    "rs": [T + "test_retry_seam.py", "-k", "CatchForms"],
    "fates": [T + "test_exhaustion_fates.py"],
    "f3": [T + "test_reanchor_58_r3_probes.py", T + "test_reanchor_58_r2_rulings.py", "-k", "PB_ or 8_way"],
}
PACKER = """        try:
            chunks = [
                list(batch)
                for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=True)
            ]
        except ValueError as error:
            worst = max(built, key=lambda entry: entry[3])
            raise StragglerHealPackerError(
                f"straggler {render_attributed(worst[0])} alone composes {worst[3]} statements, over the "
                f"{cap}-statement transaction cap — the heal cannot pack it"
            ) from error
        healed = 0
        for chunk_index, chunk in enumerate(chunks):
"""
M = {
 "M1": ("conv", [(TASKS, "get_len=lambda entry: entry[3], strict=True", "get_len=lambda entry: entry[3] - 1, strict=True")],
        ["fit+1]", "test_a_mixed_population", "test_PC_"]),
 "M2": ("conv", [(TASKS, """                    skip = True
                    continue
                if head not in existing:""", """                    skip = True
                    break
                if head not in existing:"""),
                 (TASKS, """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
""", """                            "blocker_id": old, "phantom_head_id": head,
                        },
                    )
                    skip = True
                    break
""")], ["[two_bad-phantom]", "[two_bad-cyclic]", "PHANTOM_and_a_CYCLIC"]),
 "M3": ("conv", [(TASKS, """        if healed:
            logger.info(
                _HEAL_EVENT, extra={"database": self._database, "count": healed, "chunks": len(chunks)}""",
                 """        if stragglers:
            logger.info(
                _HEAL_EVENT, extra={"database": self._database, "count": len(stragglers), "chunks": len(chunks)}""")],
        ["[one_bad-", "[bad_plus_healable-", "[two_bad-", "test_PD1_", "test_PD2_"]),
 "M4": ("conv", [(TASKS, PACKER, """        chunks = [
            list(batch)
            for batch in constrained_batches(built, cap, get_len=lambda entry: entry[3], strict=False)
        ]
        monster = None
        healed = 0
        for chunk_index, chunk in enumerate(chunks):
            if any(entry[3] > cap for entry in chunk):
                monster = chunk[0]
                continue
"""), (TASKS, """        if healed:
            logger.info(
                _HEAL_EVENT,""", """        if monster is not None:
            raise StragglerHealPackerError(
                f"straggler {render_attributed(monster[0])} alone composes {monster[3]} statements, over the "
                f"{cap}-statement transaction cap — the heal cannot pack it"
            )
        if healed:
            logger.info(
                _HEAL_EVENT,""")], ["test_a_single_row_over_the_cap_raises_the_typed_packer_error_and_changes_NOTHING"]),
 "M5": ("tier", [(TXN, "    TxnReanchorStragglerError: logging.WARNING,\n", "")],
        ["test_the_keys_are_classes_and_equal", "test_every_ruled_class_has_its_ruled_tier",
         "[TxnReanchorStragglerError-r1-straggler-PA2]", "sibling_alone[TxnReanchorStragglerError]",
         "[reanchor_straggler]", "test_PA2_"]),
 "M6": ("tier", [(TXN, "    level = _ROLLBACK_LOG_TIERS.get(error_type, logging.ERROR)\n",
                  "    level = _ROLLBACK_LOG_TIERS.get(error_type.__name__, logging.ERROR)  # type: ignore[call-overload]\n"),
                 (TXN, "    TxnHealChunkError: logging.WARNING,\n}\n",
                  "    TxnHealChunkError: logging.WARNING,\n}\n_ROLLBACK_LOG_TIERS = {cls.__name__: tier for cls, tier in _ROLLBACK_LOG_TIERS.items()}  # type: ignore[misc]\n")],
        ["test_the_keys_are_classes_and_equal", "test_every_ruled_class_has_its_ruled_tier", "sibling_alone[",
         "test_P6_mutation_dropping_ONE_table_entry"]),
 "M7": ("cas", [(TASKS, "        except TxnClaimLostError:\n            pass", "        except (TxnClaimLostError, TxnContentionExhaustedError):\n            pass")],
        ["ruled_verdict[tasks.py::claim_task]"]),
 "M8": ("cas", [(TASKS, """            try:
                await self._apply([f for f in fragments if f.statements])
            except TxnDomainRejectionError:""", """            try:
                await self._apply_heal_chunk_58r3([f for f in fragments if f.statements])
            except TxnDomainRejectionError:"""),
                (TASKS, """    @staticmethod
    def _supersede_fragment(""", """    async def _apply_heal_chunk_58r3(self, fragments: list[TxnFragment]) -> None:
        await self._apply(fragments)

    @staticmethod
    def _supersede_fragment(""")], []),
 "M9": ("cas", [(TASKS, """        return TaskLedger._guarded_append_fragment(
            task_id,
            event=event,
            set_parts=set_parts,
            params=params,
            where_conjuncts=[
                f"{_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}",""", """        return getattr(TaskLedger, "_guarded_" + "append_fragment")(
            task_id,
            event=event,
            set_parts=set_parts,
            params=params,
            where_conjuncts=[
                f"{_COL_STATUS} = ${_TRANSITION_EXPECTED_FROM_PARAM}",""")], ["ruled_verdict[tasks.py::transition]"]),
 "M10": ("fates", [(TASKS, "import asyncio\n", "import asyncio\nimport contextlib\n"),
                (TASKS, """    @staticmethod
    def _supersede_fragment(""", """    async def _swallow_58r3(self) -> None:
        with contextlib.suppress(SurrealStoreError):
            await self._apply([])

    @staticmethod
    def _supersede_fragment(""")], ["test_every_non_derived_site_has_a_row_and_every_row_a_site"]),
 "M11": ("rel", [(TASKS, "                self._relate_fragment([(blocker, task_id) for blocker in dependencies]),\n",
                  "                TxnFragment(\n"
                  "                    statements=[f\"RELATE $m58_{i}_a->{BLOCKS_RELATION}->$m58_{i}_b\" for i, _ in enumerate(dependencies)],\n"
                  "                    params={**{f\"m58_{i}_a\": RecordID(TASK_TABLE, b) for i, b in enumerate(dependencies)},\n"
                  "                            **{f\"m58_{i}_b\": RecordID(TASK_TABLE, task_id) for i, _ in enumerate(dependencies)}},\n"
                  "                ),\n")],
         ["test_the_driver_registry_equals_the_derived_RELATE_verbs", "fragment_produced[create_task]"]),
 "M12": ("f3", [(TASKS, "        except TxnClaimLostError:\n            pass", "        except TxnClaimLostError:\n            logging.getLogger(\"loremaster.contention\").error(\"task.claim.contended\")")],
         ["test_PB_", "test_an_8_way_race_logs_NO_warning_or_error"]),
 "M13": ("rs", [(T + "test_reanchor_58_r3_cas_seam.py", "def _frame_key(", "def _second_resolver_58r3(expression: ast.expr, module: Any) -> Any:\n    return eval(compile(ast.Expression(expression), \"<x>\", \"eval\"), vars(module))  # noqa: S307\n\n\ndef _frame_key(")],
         ["test_exactly_ONE_function_resolves_names_by_import"]),
 "M16": ("fates", [("loremaster/loremaster/findings.py", "    async def acknowledge(", """    async def acknowledge_quietly_58r3(self, number: int, actor: str) -> Any:
        try:
            return await self.acknowledge(number, actor)
        except SurrealStoreError:
            return None

    async def acknowledge(""")], ["test_every_non_derived_site_has_a_row_and_every_row_a_site"]),
 "M17": ("rs", [(TASKS, """                )
            )
        except SurrealStoreError as error:
            # A traversal that FAILED mid-flight""", """                )
            )
        except TxnContentionExhaustedError:
            raise
        except SurrealStoreError as error:
            # A traversal that FAILED mid-flight""")], ["test_the_whole_tree_swallow_rule_matches_its_pinned_bound_both_ways"]),
 "M18": ("fates", [("loremaster/loremaster/findings.py", "    async def acknowledge(", """    async def quiet_58r3(self) -> None:
        try:
            await self._apply([])
        except SurrealStoreError:
            return None

    async def acknowledge(""")], ["test_every_non_derived_site_has_a_row_and_every_row_a_site"]),
 "M19": ("fates", [("loremaster/loremaster/briefs.py", """            logger.warning(
                "brief.publish.version_not_released",""", """            logger.debug(
                "brief.publish.version_not_released",""")], ["test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS"]),
 "M20": ("fates", [(TASKS, "            raise TaskLedgerError(\n                f\"could not check the blocked_by entries", "            raise UnknownBlockerError(\n                f\"could not check the blocked_by entries")], ["test_every_non_derived_site_has_a_row_and_every_row_a_site"]),
 "M21": ("fates", [("loremaster/loremaster/diff.py", "the session bootstrap exhausted its retry budget\"\n                ) from error\n", "the session bootstrap exhausted its retry budget\"\n                )\n")], ["test_every_non_derived_site_has_a_row_and_every_row_a_site"]),
 "M22": ("fates", [("loremaster/loremaster/server.py", """                    except BaseException:  # noqa: BLE001 - never mask the startup error
                        pass""", """                    except BaseException:  # noqa: BLE001 - never mask the startup error
                        logger.warning("startup.hook.shutdown_failed_58r3")""")], ["test_every_row_names_a_ruled_classification_an_owner_and_evidence_that_HOLDS"]),
 "M23": ("rs", [(T + "test_retry_seam.py", "from _catch_sites import caught_classes as _caught_classes  # noqa: E402\n", """def _caught_classes(site: Any, module: Any) -> list[type]:
    import _catch_sites

    return list(_catch_sites.caught_classes(site, module))
""")], ["test_this_index_resolves_through_THE_ONE_resolver"]),
 "M14": ("rs", [(T + "test_retry_seam.py", "        if not isinstance(node, (ast.Try, ast.TryStar)):", "        if not isinstance(node, ast.Try):")],
         ["test_try_STAR_handlers_join_the_domain_and_the_partition"]),
 "M15": ("cas", [(TASKS, """    @staticmethod
    def _supersede_fragment(""", """    async def assign_task_58r3(self, task_id: str) -> None:
        await self._apply([
            TaskLedger._guarded_append_fragment(
                task_id, event={}, set_parts=["owner = NONE"], params={}, where_conjuncts=["owner IS NONE"],
                throw_message="cas_lost: assign", namespace="asg",
            )
        ])

    @staticmethod
    def _supersede_fragment(""")], ["[tasks.py::assign_task_58r3]"]),
}


def run(scope: list[str], tag: str) -> set[str]:
    log = OUT / f"{tag}.log"
    cmd = [str(Path(__file__).parent / "run.sh"), str(ROOT), str(log), "-n", "8", "-rf", *scope]
    subprocess.run(cmd, env={"PATH": "/usr/bin:/bin", "RUN_TIMEOUT": "1800", "HOME": str(Path.home())})
    text = log.read_text()
    tail = [line for line in text.splitlines() if re.search(r"\d+ (passed|failed)", line)]
    return {line.split()[1] for line in text.splitlines() if line.startswith("FAILED ")}, (tail[-1] if tail else "NO TAIL")


def collect(scope: list[str]) -> list[str]:
    out = subprocess.run([PY, "-m", "pytest", "-p", "no:cacheprovider", "--collect-only", "-q", *scope],
                         cwd=ROOT, capture_output=True, text=True).stdout
    return [line.strip() for line in out.splitlines() if "::" in line]


baselines: dict[str, set[str]] = {}
results = {}
for mid, (scope_key, edits, patterns) in M.items():
    if ONLY and mid not in ONLY:
        continue
    scope = SC[scope_key]
    collected = collect(scope)
    declared = {node for node in collected for pattern in patterns if pattern in node}
    unmatched = [p for p in patterns if not any(p in node for node in collected)]
    if scope_key not in baselines:
        baselines[scope_key], btail = run(scope, f"baseline-{scope_key}")
        print(f"baseline[{scope_key}]: {btail} · reds {sorted(baselines[scope_key])}")
    originals = {}
    for path, old, new in edits:
        file = ROOT / path
        originals.setdefault(path, file.read_text())
        src = file.read_text()
        assert src.count(old) == 1, f"{mid}: anchor occurs {src.count(old)}x in {path}: {old[:70]!r}"
        file.write_text(src.replace(old, new))
    for path in originals:
        assert (ROOT / path).read_text() != originals[path], f"{mid}: {path} unchanged"
    observed, tail = run(scope, mid)
    subprocess.run(["git", "checkout", "--", *originals], cwd=ROOT, check=True)
    assert subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout == ""
    expected = baselines[scope_key] | declared
    unexpected = sorted(observed - expected)
    stayed_green = sorted(declared - observed)
    verdict = "EXACT" if not unexpected and not stayed_green and not unmatched else "MISMATCH"
    results[mid] = {"verdict": verdict, "tail": tail, "declared": sorted(declared), "unmatched_patterns": unmatched,
                    "unexpected_reds": unexpected, "declared_stayed_green": stayed_green}
    print(f"{mid}: {verdict} · {tail} · declared {len(declared)} · unexpected {unexpected} · stayed-green {stayed_green} · unmatched {unmatched}")
(OUT / "results.json").write_text(json.dumps(results, indent=1))
```

### `partition.py` (md5 `c7b29cf31577a22ef0762371be577bbc`) — the currency gate's pytest-ownership rule, applied to a junit run
```python
"""Partition a junit (xunit1) run's failures against scripts/pending_contracts.yaml's registered paths — the
currency gate's own pytest rule (`partition_pytest`: a failure is EXPECTED iff its file is registered)."""
import sys, xml.etree.ElementTree as ET, yaml
from collections import Counter
junit, registry = sys.argv[1], sys.argv[2]
registered = {f["path"] for b in yaml.safe_load(open(registry))["bounds"] for f in b["files"]}
failed = Counter()
for case in ET.parse(junit).iter("testcase"):
    if any(child.tag in ("failure", "error") for child in case):
        failed[case.get("file")] += 1
orphans = {f: n for f, n in failed.items() if f not in registered}
for f, n in sorted(failed.items()):
    print(f"{'OWNED ' if f in registered else 'ORPHAN'} {n:4d} {f}")
print(f"TOTAL failed={sum(failed.values())} files={len(failed)} orphans={sum(orphans.values())}")
sys.exit(1 if orphans else 0)
```

### `pc_edit.py` (md5 `0579481e3535b605c84baa01edd582a8`) — the registry edit (applied to HEAD's blob for the index AND to the working copy)
```python
"""contract-58-r3's edit to the packet-58-contract bound (applied to a registry text; anchors asserted once)."""
import sys
path = sys.argv[1]
s = open(path).read()


def sub(old: str, new: str) -> None:
    global s
    assert s.count(old) == 1, f"anchor occurs {s.count(old)}x: {old[:70]!r}"
    s = s.replace(old, new)


sub("""  owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-5) — the 58 builder,
    serial after 63c-i-a
  reopen_trigger: the packet-58 build lands TaskLedger.max_reanchor_dependents, loremaster.tasks.SupersedeResult
    and TaskLedger._guarded_append_fragment — then every file below stops erroring, this entry self-destructs and
    must be deleted with the build
  ruling: docs/design/2026-09-26-packet58-kickoff-rulings.md (c8d3241) + packet58 amendments 1-5 (f4e96b4,
    e0760fd, 7266c1b, fd6497d, 67bf2cc); contract receipts REPORT-contract-58.md §RED + REPORT-contract-58-r2.md §RED@HEAD
    (archived with the wave)
""", """  owner: packet 58 (supersede re-anchor + task guarded-append shell + finding 130 + amendments 1-8) — the 58 builder,
    serial after 63c-i-a
  reopen_trigger: the packet-58 build lands TaskLedger.max_reanchor_dependents, loremaster.tasks.SupersedeResult,
    TaskLedger._guarded_append_fragment, TaskLedger._reanchor_stragglers, loremaster.tasks.StragglerHealPackerError,
    loremaster.store._txn._ROLLBACK_LOG_TIERS and loremaster.store._txn.TxnCasLostError — then every file below stops
    erroring, this entry self-destructs and must be deleted with the build. ⚠ Two r3 leg families discharge on OTHER
    work, named so nobody reads their red as 58's — the TxnUniqueViolationError legs of test_reanchor_58_r3_tiers.py
    need 63c-i-a's am-33 build (serial BEFORE 58); the three test_reanchor_58_r3_cas_seam.py population rows for
    listed handlers outside 58 (floor_calibration record_measurement, keeps get_or_create_keyed, agents register)
    need a CAS_SEAM_DRIVERS entry in their OWNERS' test modules — the lead's routing (am-7 §3 item 2;
    REPORT-contract-58-r3.md FK-r3-4)
  ruling: docs/design/2026-09-26-packet58-kickoff-rulings.md (c8d3241) + packet58 amendments 1-8 (f4e96b4,
    e0760fd, 7266c1b, fd6497d, 67bf2cc, dcf6b0f, 01565f9, 03cb6d0); contract receipts REPORT-contract-58.md §RED +
    REPORT-contract-58-r2.md §RED@HEAD + REPORT-contract-58-r3.md §RED@HEAD (archived with the wave)
""")
sub("""  - path: loremaster/tests/test_reanchor_58_r2_cas_runtime.py
    missing_symbols:
    - type[TaskLedger]._guarded_append_fragment
""", """  - path: loremaster/tests/test_reanchor_58_r3_am6.py
    missing_symbols:
    - loremaster.store._txn.TxnCasLostError
    unsymboled_codes:
    - code: attr-defined
      count: 1
      reason: the adversary's AST-equal mutation leg reads `_txn._ROLLBACK_LOG_TIERS` through the module alias, and mypy
        names no symbol for a module-alias attribute ("Module has no attribute"); the same ruled table the tiers file
        names statically
  - path: loremaster/tests/test_reanchor_58_r3_cas_seam.py
    missing_symbols:
    - type[TaskLedger]._guarded_append_fragment
  - path: loremaster/tests/test_reanchor_58_r3_convergence.py
    missing_symbols:
    - loremaster.tasks.StragglerHealPackerError
  - path: loremaster/tests/test_reanchor_58_r3_probes.py
    missing_symbols:
    - loremaster.tasks.StragglerHealPackerError
  - path: loremaster/tests/test_reanchor_58_r3_relate.py
    missing_symbols:
    - type[TaskLedger]._reanchor_stragglers
  - path: loremaster/tests/test_reanchor_58_r3_tiers.py
    missing_symbols:
    - loremaster.store._txn._ROLLBACK_LOG_TIERS
""")
open(path, "w").write(s)
print("pending_contracts: packet-58-contract updated")
```
