brief-base v25 read · brief project v7 read
**RE-GRADE (R35, F6 delta 2 = 64fcdd6) SUMMARY: CONTRACT INSUFFICIENT. 0 UNSATISFIABLE. 2 STOP-tagged: MP6-1, a wrong build that hides every red under a directory --wave, survives all 51 F6 pins; MP6-2, r10ref silences the outcome of COLLECTED ids under a directory/'./'/absolute selector (a ruling-bound question, D3). Both are satisfiable and measured. Round-5 survivors N8/N9/N12 + MP5-4 are all KILLED. See §RE-GRADE.**
# ADVERSARY5: adversary-sdk3-r5 on the F6 gate pins (c01b114), adversary round 5 (the last in budget, R25/R32)

## SUMMARY BLOCK
- **State:** done. **VERDICT: CONTRACT INSUFFICIENT (F6 delta).** UNSATISFIABLE pins: **0**. The reference passes 488/488, and HEAD is red on exactly the 29 F6 nodes, all for the right reason. Every missing pin is satisfiable, and the reference already passes each proposed pin.
- **P1 headline:** 20 wrong gates were built (5 adversary-4 replays rebased onto r9, plus 15 new). **17 died exactly on their declared reds (PROOF HELD), 3 SURVIVED:** N8 (a mixed-claim entry exempt from the pytest self-destruct), N9 (the KEPT note rendered only on a non-GREEN leg) and N12 (self-destruct reaches only the first 3 ids of an entry). All 5 adversary-4 F6 builds and the r8 reference are now KILLED.
- **Missing pins (each satisfiable; tags in §MISSING PINS):**
  - **MP5-1** (N8, R31's CLASS "other claims on the entry", REPEAT CLASS): a stale id in a mixed entry renders as live. **STOP-candidate**, two readings of the brief, lead's call.
  - **MP5-2** (N9 + wave_gate, one class: R31 rider "the render says so"): RESIDUAL.
  - **MP5-3** (N12, small-N reach): RESIDUAL.
  - **MP5-4** (module skip, importorskip and collection error read as "file collected", so every listed id is falsely STALE; measured with live pytest 9.0.3): RESIDUAL. It is the file-granularity sibling of R31's rider.
- **Servicer residuals:** (1) is REAL and reachable through `wave_gate --wave <file>::<Class>`; the stale line over-claims "renamed or deleted"; **decision needed** (below). (2) is CONFIRMED live: wave_gate's render drops the KEPT note in full AND wave mode; folded into MP5-2. (3) a non-strict xpass reads "green, delete it": correct under R31's rule, NO ROUND. Strict XPASS is written as `<failure>`, verified live, so it reads RED_ADJUDICATED, which is correct.
- **Runs used:** 25 = 1 full gate-pin set (reference, 488) + 1 HEAD set (488) + 20 scoped wrong builds (15 F6-only, 5 F6 + 3 gate files) + 1 collect-only + 2 probe-tree runs (live junit, xdist). §RUNS.
- **Deviations:** (a) My wrong-build runs went to one haiku-runner as a single batch, rather than one runner per build (each run ~1 s). (b) HEAD moved during my run (3114183 → 20c5623, REQ-D only). The F6 files are unchanged.
- Packages considered: junit parsing → stdlib `xml.etree` (in use; `junitparser`/`lxml` not installed, so not needed); nodeid derivation → `_pytest.junitxml.mangle_test_address` (READ: private, nodeid→names only, the inverse of what the reader needs) → `keep_with_trigger` (trigger: pytest exposes a public junit→nodeid API). No mechanism specified by me.
- Odoo-20 portability: n/a — no Odoo seam touched. **Reuse ledger:** none (I wrote no production symbols; the pins demand no new symbol, P-PRIOR).
- **Graded:** c01b114 · HEAD-at-report: 20c5623 · DIFFERENT (9 behind). `scripts/pending_contract_gate.py`, `scripts/test_pending_contract_gate_f6.py` and `scripts/wave_gate.py` are byte-unchanged c01b114..HEAD.
- **Decisions needed:**
  - (D1) Is MP5-1 a STOP (the brief's report-tag definition: an R17 false clear on the healthy path) or a named residual (the brief's routing sentence: only UNSATISFIABLE is a STOP)? I pick: one pin added by the servicer before the build, because the reference already passes it.
  - (D2) Reading (b)'s granularity under a node-id `--wave` (servicer residual 1): an operator or sidecar ruling.
- **Pointers:** §MISSING PINS · §REPLAY · §NEW BUILDS · §LIVE-JUNIT · §P1b · §P1c · §RESIDUALS · §LANDMINES · §RUNS · §INSTRUMENTS · §ROUTING

## Routing table (written before the first sweep; amended at the end)
| step | tier | who | reason |
|---|---|---|---|
| read rulings R30–R32, RULING-9, SERVICER-LOG §F6, ADVERSARY4, the F6 pins, the reference gate | 3 | self | the frame I grade |
| reference provenance + sha256 (3 commands) | 1 inline | self | critical path; I read all of it |
| reference over-fire control (5 gate files) | 1 | haiku-runner | test run |
| HEAD RED reproduction (5 gate files) | 1 | haiku-runner | test run |
| wrong-build design + declarations | 3 | self | adversarial judgment |
| 20 wrong-build runs | 1 | haiku-runner (one batch) | test runs; verdicts mine |
| live-junit instrument, wave render probe, survivor demos | 3/1 inline | self | probes I wrote; seconds each; I read all output, and the design is the judgment |
| skip-site sweep (`allow_module_level`/`importorskip`, 533 .py files) | 1 inline | self | one grep. **Grep fallback (non-symbol textual seam), said out loud** |
Fan-out: haiku 3 · sonnet 0 · peak 2.

## Satisfiability + RED honesty (P4/P7), receipts
- Reference provenance: `scratch_copy.sh --verify-only sdk3f6r9/ref` EXIT=0; `loremaster.__file__` = `sdk3f6r9/ref/loremaster/loremaster/__init__.py`. Its gate file `cmp`s equal to `pending_contract_gate.r9ref.py`.
- The F6 sha256 is the same in all three copies: `git show c01b114:…` = the ref copy = the HEAD tree = `60d5f14a…6eafdb`.
- My copy `adv5/b1` (made with `scratch_copy.sh`): TREE=e1ea296c… equals the ref dir's own TREE; `loremaster.__file__` resolves inside adv5/b1.
  - ⚠ The servicer's ref control read TREE=71ecdd52… at DIRTY 19. The ref dir is now DIRTY 20: `loremaster/tests/test_backoff_seam.py` was modified after the F6 runs (the servicer's REQ 2 work was done in that dir). That file is outside the F6 scope. The gate and F6 bytes are sha-verified. RESIDUAL R5-6.
- **Reference: 488 passed, EXIT=0** (`adv5/logs/ref_control.log`, TREE=e1ea296c…). Every F6 pin passes. No over-fire.
- **HEAD 3114183: 29 failed / 459 passed, EXIT=1** (`adv5/logs/head_red.log`, TREE=1c5e1d52…, DIRTY 0). All 29 reds are F6 nodes, i.e. all 29 F6 nodes (29 collected), which matches the servicer's declared RED@HEAD = 29.
  - 28 of them fail with `RegistryError … red_nodeids Extra inputs are not permitted`.
  - The `no_claim_at_all` pin fails on regex `neither` vs the extra-key message, its stated wrong reason.
  - So every red is for the right reason: the feature is absent.

## REPLAY (adversary 4's F6 gates → c01b114, rebased onto r9)
Rebase: R1 swaps r9's `collected_files` derivation for `{outcome.file for outcome in run.outcomes}` (the files with a red). This is r4's "only failing files" expressed over r9's reading-(b) guard. R2 adds `if not run.outcomes: return findings` after r9's prologue. R3 = both r4 hunks re-anchored on r9's text: a pre-patch for stale/green, and mutation_proof for the partition. R4 and R5 apply verbatim.
| build | result | killing pins | verdict |
|---|---|---|---|
| R1 `destruct_only_failing_files` | PROOF HELD 2F/27P | `ALL_GREEN_run_self_destructs…`, `ALL_GREEN_run_still_reports_a_STALE_id` | **KILLED** |
| R2 `destruct_only_when_red` | PROOF HELD 2F/27P | same two | **KILLED** |
| R3 `hierarchical_ids` | PROOF HELD 2F/27P | `listed_CLASS_id…`, `listed_FILE_path…` (`'RED_ADJUDICATED' == 'RED_ORPHANED'`) | **KILLED** |
| R4 `mixed_file_level` | PROOF HELD 2F/27P | `MIXED_claim…PER_NODE[code,symbol]` | **KILLED** |
| R5 `mixed_no_typecheck_destruct` | PROOF HELD 2F/121P | `MIXED_claim…self_destructs_its_mypy_claim[code,symbol]` | **KILLED** |
| N2 = the whole **r8 reference** (reading (a), no rider, old stale text) | PROOF HELD 11F/18P | SCOPED, CONTROL Leg-1, rider ×6, CLASS, FILE, PREFIX | **KILLED** (MP-F6-4 closed) |
| scope bug (reading (a) alone) = N1 | PROOF HELD 1F/28P | `SCOPED_run_that_never_collected…` ("called its listed ids stale or green: RED_ORPHANED") | **KILLED, right reason** |

## NEW BUILDS (round 5). Expected reds were declared before any run: `adv5/DECLARED.sha256` (20 rows, written 07:28 before the batch).
| build | landmine | mutation | result | verdict |
|---|---|---|---|---|
| N3 CLI-hierarchical stale only (`::` and `[` ancestry in stale/green, exact partition) | 2 | the m03b family | 3F: CLASS, FILE, PREFIX ("…not reported stale") | KILLED |
| N4 skip discharges (rider skip removed) | 4 | | 4F: rider1 ×2, rider2 ×2 | KILLED |
| N5 xfail counted red (reader) | 4 | | 2F: rider2[xfail], render[xfail]; rider1[xfail] stays green alone (it cannot tell owned-red from neither) | KILLED (by the pair) |
| N6 KEPT notes dropped | 4 | | 2F: render ×2 | KILLED |
| N7 typecheck skips non-mypy entries BEFORE file-exists | 5 | | 1F: `DELETED_red_nodeids_only_file…` ("caught by NEITHER leg: GREEN") | KILLED. **T12 is red on that gate.** |
| **N8 mixed entry exempt from pytest self-destruct** (`if entry.claims_mypy: continue`) | 3 (other claims on the entry) | | **29 passed (EXIT 4: declared pin stayed green)** | **SURVIVES → MP5-1** |
| **N9 notes rendered only when verdict ≠ GREEN** | 4 | | **123 passed** | **SURVIVES → MP5-2** |
| N10 entry-level discharge (green only when no sibling listed id failed) | 3 (sibling outcome) | | 1F: `listed_node_that_PASSES…` | KILLED |
| N11 first finding per entry, then break | P2 small-N | | 1F: `ALL_GREEN…self_destructs` | KILLED |
| **N12 self-destruct over `red_nodeids[:3]`** | P2 small-N | | **29 passed** | **SURVIVES → MP5-3** |
| N13 no self-destruct when the run has an orphan | 3 (run's other outcomes) | | 3F: CLASS, FILE, PREFIX | KILLED |
| N15 file-level matching when a listed sibling in the file is red | 3 | | 7F: UNLISTED, ONLY-param, PREFIX, CLASS, FILE, MIXED ×2 | KILLED |
| N24 stale reported as "green, delete it" | 7 (message gap) | | 4F: CONTROL Leg-1, CLASS, FILE, PREFIX (the two "ALL_GREEN stale" and original NOT_COLLECTED pins stay green; they check only the id) | KILLED elsewhere |
Survivor receipts (`adv5/logs/wb_N{8,9,12}_*.log`): "mutation LANDED (anchor matched exactly once)", then "DECLARED RED but STAYED GREEN". Each was restored byte-exact (`cmp`): 20/20 RESTORED, and all 40 TREE lines read e1ea296c….

## Survivor consequences: served render vs the reference (in-memory builds, `adv5/probes/survivor_demo.py`; the reference is the positive control)
- **N8:** a mixed entry (attr-defined ×1 + node ids, the real MP-1 file's shape); the listed id passes and one listed id was renamed away.
  - Reference: `pytest RED_ORPHANED` with "…is green — delete it" and "…test_renamed_away … not collected in this run's …".
  - **N8: `pytest GREEN`.**
- **N9:** the listed id is only SKIPPED (RULING-9's all-skip run).
  - Reference: `pytest GREEN` plus `NOTE: KEPT: … was skipped in this run …`.
  - **N9: `pytest GREEN`, no note.**
- **N12:** 5 listed ids, all green. Reference: 5 self-destruct lines. **N12: 3.** Two discharged ids stay registered, so a later regression on them reads RED_ADJUDICATED.

## LIVE-JUNIT (real pytest 9.0.3 → reference reader + gate; `adv5/probes/live/drive.py`, output `ref_live.out`)
A fixture tree has every listed id registered under one bound. Results:
| scenario | what the reference serves | verdict |
|---|---|---|
| S1 full file | strict XPASS = `<failure>` → owned; non-strict xpass → "green, delete it"; skip-body / skip-marker / xfail → KEPT notes; setup `<error>` → owned | correct per R31 |
| **S2 `file::TestA`** (a node-id `--wave` door) | **7 listed ids outside TestA → "not collected in this run's <file> — renamed or deleted; update the registry"** | **false STALE** (servicer residual 1) |
| S3 `-k`, S7 `--maxfail=1`, S8 `--deselect` | the same false STALE (`-k` is not forwarded by wave_gate; maxfail/deselect are not in any gate command) | bound; reachable only by hand |
| **S4 `pytest.skip(allow_module_level=True)`**, **S6 `importorskip` at module level** | junit writes ONE `<skipped>` testcase `file::pkg.tests.mod`, so the file counts as "collected" → **every listed id STALE** | **false STALE: the rider's case at file granularity** (MP5-4) |
| **S5 collection error** (`--continue-on-collection-errors`) | the error is an orphan (correct), **plus every listed id STALE "renamed or deleted"** | misleading instruction beside a correct FAIL (MP5-4) |
| xdist `-n 3` | 1 testsuite, the same 10 testcases as serial | not a door |
Today's reachability (grep, 533 .py, a non-symbol textual seam): module-level skip appears only in `skills/lore-deploy/tests/test_prod_store_guard.py` ("store unreachable", `allow_module_level=True`); `importorskip` appears only inside test bodies in `test_secret_leak_vectors.py`; 0 of the planned entry's 27 files skip at module level. So MP5-4 is a door for the next file, not today's data.

## MISSING PINS (none UNSATISFIABLE; the reference passes every proposed pin)
| id | surviving build + receipt | the test that should exist | defect it catches | tag |
|---|---|---|---|---|
| **MP5-1** | N8, 29/29 F6 green (`wb_N8_…log`); demo: `pytest GREEN` vs the reference's self-destruct + stale | `test_a_MIXED_claim_file_self_destructs_a_PASSING_and_a_STALE_listed_id` (claim=code: listed id passes, a second listed id renamed away, the file collected → both reported, the stale one in Leg-1 words) | A mixed entry's listed ids are never discharged or reported stale. A stale id renders as live (R17's own example of a false clear). At the build commit it is masked on today's ONE mixed entry, because the attr-defined claim self-destructs on the typecheck leg at the same time. It is NOT masked when a node id goes green or is renamed before the mypy claim discharges. | **STOP-candidate / PINNED PROPERTY, NEW CASE, REPEAT CLASS** (R31: "never on the other claims on the entry"; MP-F6-3 pinned only the partition and typecheck sides). D1 |
| **MP5-2** | N9, 123 green (`wb_N9_…log`); **plus the reference itself through `wave_gate._render`** (`probes/wave_render_probe.py`): the NOTE is present in `_render_currency`, absent in wave_gate's full AND wave render, and full mode renders a bare `pytest GREEN` | the render pin parametrised over (a) the all-skip GREEN leg as well as RED_ADJUDICATED, and (b) both renderers (`_render_currency` and `wave_gate._render`) | R31 rider "and the render says so" is dropped on the fleet's own entrypoint (wave_gate, the non-omittable bundle) and on the exact case RULING-9 cites (an all-skip run) | **PINNED PROPERTY, NEW CASE** · RESIDUAL → builder + cold audit |
| **MP5-3** | N12, 29/29 green | `test_an_ALL_GREEN_run_self_destructs_EVERY_listed_node` with ≥ 4 listed ids (today it has 2; no pin lists more than 3 in one entry, while the real entry averages 11/file) | self-destruct reach truncated (a display cap reused, an early exit) | **PINNED PROPERTY, NEW CASE** · RESIDUAL (plausibility LOW–MEDIUM) |
| **MP5-4** | the reference itself (S4/S5/S6) | a registered file whose junit holds only a module-level `<skipped>` (or a collection `<error>`) testcase → its listed ids are KEPT (or not adjudicated), never STALE | false "renamed or deleted; update the registry" on an all-skip or broken-import run. That is exactly the rider's hazard (deleting still-red registrations), reached at file granularity | **PINNED PROPERTY, NEW CASE** (rider sibling) · RESIDUAL |

**CLASS (one property over all four):** *the pytest leg's verdict on a listed id, and the text that announces it, depends only on (exact id) × (did this run ENUMERATE its file's items) × (its observed outcome), and every render of that leg says so.* The four instances:
- MP5-1 breaks the "only" (another claim on the entry).
- MP5-3 breaks the ∀ (reach).
- MP5-4 breaks "enumerated" (a module-level testcase stands in for a file's items).
- MP5-2 breaks "every render".

**CHOKEPOINTS:**
- `pytest_self_destruct_findings`: iterate EVERY entry with `red_nodeids`, regardless of `claims_mypy`, over EVERY id. Count a file as "collected" only from item testcases, not from a module-level collect report (its `name` is the dotted module and its classname is empty).
- `GateCurrency.render()` (or one shared leg-render helper) emits the notes, so `_render_currency` and `wave_gate._render` cannot diverge.

**SIBLINGS TRIED:**
- all-green; file-gated; run-gated; `::` and `[` ancestry (partition and stale);
- mixed partition, mixed typecheck, mixed pytest-self-destruct (survived);
- typecheck ordering; skip discharge; xfail-as-red; notes dropped; notes on non-GREEN only (survived);
- entry-level discharge; first-finding break; cap-3 (survived); run-orphan suppression; sibling-red contagion; stale-as-green;
- reading (a); the r8 reference; xdist split; module skip; importorskip; collection error; `::Class`, `-k`, `--maxfail`, `--deselect`; strict and non-strict xpass; setup error.

**SIBLINGS NOT TRIED:**
- the same path under two bounds (adversary-4 R4-2; 0 overlaps in the planned entry);
- a `junit_prefix` ini option (it changes `classname`; planted config);
- a rootdir mismatch (the `file` attr is relative to another root; the manifest pins the command);
- a timeout-killed run (`--timeout` thread method, no junit → BrokenInstrument, loud).

## Servicer residuals — verdicts
1. **A run narrowed below file level reads stale.** REAL and reachable: `wave_gate --wave` forwards node ids verbatim (its docstring), and S2 shows 7 false STALE lines. R31 rules (b) "keys on the file", so this is not a contract defect, and the pin docstring states it. Under the TRUST definition it is still a Leg-1 over-claim: the line says "renamed or deleted; update the registry". The run measured "not in this selection", and an agent acting on the line deletes still-red registrations. That is loud, not silent: the next full run shows them RED_ORPHANED. It is also the MP-F6-4 harm (honest scoped waves fail) one level down. **D2.** I recommend either of two cheap repairs:
   - (i) wave_gate passes its selectors, so a file named below file level counts as not collected;
   - (ii) the stale text names the bound: "not collected in this run's <file> (renamed, deleted, or outside this run's selector)".
2. **wave_gate's render of the rider is unpinned.** CONFIRMED live → MP5-2.
3. **A non-strict xpass reads "green, delete it".** Correct: it ran and passed, which is R31's "passed ⇒ self-destruct". NO ROUND. Strict XPASS: `<failure>` (live) → RED_ADJUDICATED, also correct under "failed ⇒ adjudicated". NO ROUND.

## LANDMINES — per item
1. Replays: 5/5 KILLED, and the r8 reference KILLED (§REPLAY).
2. Reading (b) by construction: reading (a) dies on SCOPED only, for the right reason. Hierarchical reading dies on CLASS/FILE (R3) and CLASS/FILE/PREFIX (N3), for the right reasons.
3. Class-not-instance:
   - Sibling outcome (N10), run verdict (N13) and sibling contagion (N15) are KILLED.
   - The "other claims on the entry" door SURVIVES on the self-destruct side (MP5-1).
   - -k/-m and xdist cannot be expressed in the fixture junit. Probed live: xdist is not a door; -k is a bound (S3).
   - Position: the cap survives (MP5-3).
4. Rider:
   - skip-as-green (N4), xfail-as-red (N5) and a dropped note (N6) are KILLED.
   - The note conditional on verdict SURVIVES (MP5-2).
   - Strict XPASS = `<failure>` verified live (the servicer's correction stands).
5. Self-destruct reach: it iterates the REGISTRY (R1/R2 killed). T12 is red on a gate that skips red_nodeids-only entries in the typecheck leg (N7, "caught by NEITHER leg").
6. Servicer residuals: see the section above.
7. Message/assert gaps:
   - `ALL_GREEN…self_destructs` promises "green-delete-it" but asserts "green" only. NO ROUND.
   - `ALL_GREEN…STALE_id` and the original `NOT_COLLECTED` promise "stale" but assert only that the id is named. N24 survives both and dies on CONTROL/CLASS/FILE/PREFIX. NO ROUND.
   - `FILE_path` asserts "any `not collected`" without naming the path. In its fixture the bare path is the only stale candidate. NO ROUND.
   - rider1[xfail] alone cannot tell owned-red from neither (N5). Covered by rider2 and render. NO ROUND.
   - T3 and PREFIX now require the Leg-1 words. Verified by N3 and N24.
8. Satisfiability: the reference passes 488/488 and HEAD's 29 reds are exactly the F6 file. 0 UNSATISFIABLE. The proposed pins pass on the reference (the survivor demo controls).

## P1b — QUANTIFIER TABLE
| invariant | class | receipt |
|---|---|---|
| a listed failing id → RED_ADJUDICATED | ∀ over listed ids (exact membership) | N15/R3 killed |
| an unlisted red in a node-listed file → ORPHANED | ∀ | N15 killed (7 pins) |
| a listed id passes → self-destruct | **guarded**: by "entry has no mypy claim" (N8 SURVIVES) and by "first 3 ids" (N12 SURVIVES) | MP5-1, MP5-3 |
| a listed id absent from a collected file → stale | **guarded**: same N8 door; "collected" includes a module-level testcase (S4–S6) | MP5-1, MP5-4 |
| stale only when the file was collected (reading b) | ∀ | N1 killed |
| skip/xfail → neither, KEPT note | **guarded by verdict ≠ GREEN in the render** (N9 SURVIVES); by renderer (wave_gate drops it) | MP5-2 |
| deleted file → typecheck self-destruct ∀ entries | ∀ | N7 killed |
| a mixed mypy claim self-destructs | ∀ | R5 killed |

## P1c — ENFORCEMENT TABLE (E = empirical, I = inspection)
| rule | chokepoint | effect vs proxy | sharing | spelling test? |
|---|---|---|---|---|
| per-node partition | `partition_pytest` (one) | effect: verdict and orphans (E: R3, R4, N15) | n/a | no |
| self-destruct / stale | `pytest_self_destruct_findings` (one) | effect (E: R1, R2, N10–N13, N24); **reach gaps N8, N12** | n/a | no |
| reading (b) | same | effect (E: N1) | n/a | no |
| rider: neither way | same + reader | effect (E: N4, N5) | n/a | no |
| rider: the render says so | **TWO renderers** (`_render_currency`, `wave_gate._render`) over one derivation (`_currencies_for`) | effect in one renderer only (E: N6 kills, N9 survives; wave_gate drops it, E) | **routing-not-sharing at the render**: wave_gate consumes the shared currencies and hand-renders the leg | no (pins drive renders) |
| deleted file caught | `transcript_self_destruct_findings` | effect (E: N7) | n/a | no |
| moved after the body | n/a: the gate is a pure function of (registry, run); there is no mutating body to reorder | I | | |
| empty population | the empty failing set (E: R1, R2 killed); the empty collected set (E: SCOPED → GREEN, which is correct for reading (b), plus the DELETED pin covers that file) | | | |

## P-PKG / P-PRIOR / P-PORT
- P-PKG: my table matches the summary line. The servicer's delta specifies no mechanism, so there is nothing to diff; the reference reader's stdlib ElementTree use predates F6.
- P-PRIOR: the pins import only symbols present at HEAD (`GateCurrency`, `GateManifest`, `JUnitReportReader`, `MypyOutputReader`, `PendingContractGate`, `PendingContractRegistry`, `RegistryError`, `_currencies_for`, `_render_currency`). They demand no new symbol. The reference's new `pytest_kept_notes` / `GateCurrency.notes` have no prior owner (searched: grep "notes" in pending_contract_gate.py and wave_gate.py). MP5-2's fix should make `GateCurrency.render` the one owner.
- P-PORT: n/a (scripts/ gate, no Odoo seam). My count: 0 seams · 0 non-stable · 0 rulings.

## RESIDUALS (individual verdicts)
- R5-1: servicer residual (1) → D2 (above).
- R5-2: the strict/non-strict xpass reading is correct. NO ROUND.
- R5-3: the message/assert gaps in §LANDMINES 7. NO ROUND each.
- R5-4: `-k`/`--maxfail`/`--deselect` false STALE (S3/S7/S8). These are not forwarded by any gate entrypoint. NO ROUND. Fold them into D2's wording if (ii) is chosen.
- R5-5: the reference dir holds 6 stray `test_<pid>_<uuid>.memory.db` at its root (`git status`). That is the #584 class from runs made before f866fbe. NO ROUND (scratch only).
- R5-6: the reference tree drifted after the servicer's F6 receipts (test_backoff_seam.py; TREE 71ecdd52 → e1ea296c). Outside the F6 scope. The bytes I graded are sha-verified. NO ROUND.
- R5-7: rider1[xfail] alone is blind to xfail-as-red (N5). The pair kills it. NO ROUND.

## LOOP COST
This is round 5 of 5 (R25 + R32). It cost 25 runs: 2 of 488 tests, 20 of 29–123 tests (~1 s each), and 3 probe runs. Wall time ≈ 25 min of runs. Closing MP5-1..3 costs 3 pins: the reference passes all of them, so there is no reference change. MP5-4 needs 1 pin + a ~3-line reference change. D2 is a ruling.

## RUNS (each log starts with tree_id; EXIT and count are in the tail)
| run | command (abridged) | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| ref control | `pytest -n 8 --timeout=600` 5 gate files, cgroup 16G | `adv5/logs/ref_control.log` | 0 | 488 passed | e1ea296c… |
| HEAD red | same at the main tree | `adv5/logs/head_red.log` | 1 | 29 failed, 459 passed | 1c5e1d52… |
| 20 builds | `adv5/runwb.sh <n>` (`mutation_proof.py`, `-n 4 --timeout=300`, cgroup) | `adv5/logs/wb_*.log`, `batch_summary.txt` | 17×0, 3×4 | per row above | e1ea296c… before and after each |
| collect | `pytest --collect-only` F6 | `adv5/logs/f6_collect.txt` | 0 | 29 collected | |
| live junit / xdist | `probes/live/drive.py` | `probes/live/ref_live.out` | 0 | 8 scenarios | probe tree |

## INSTRUMENTS (kept under the brief-named dir `adv5/`, which the lead archives)
- `adv5/mkbuilds.py`: all wrong-build specs + declared reds.
- `adv5/runwb.sh`, `adv5/batch.sh`: run and restore, with `cmp`.
- `adv5/probes/live/drive.py`: the live-junit instrument.
- `adv5/probes/wave_render_probe.py`: MP5-2's wave_gate leg.
- `adv5/probes/survivor_demo.py`: in-memory survivor consequences.
- The two load-bearing probes are pasted verbatim below.

### `probes/wave_render_probe.py`
```python
"""adv5 probe (residual 2): does wave_gate's render carry the R31 rider's KEPT note? Uses the F6 contract's own
fixture helpers (registry, junit with a skipped listed id) and renders through BOTH renderers on the same input.
Positive control: _render_currency (the --currency render) must show the NOTE; then wave_gate._render (full and
wave mode) on the identical currencies."""
import sys, tempfile
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import test_pending_contract_gate_f6 as f6  # the committed c01b114 helpers
import pending_contract_gate as pcg
import wave_gate

for kind, cases in (("xfail", [(f6._LISTED_CLASS_NODE, True), (f6._SIBLING_PARAM_NODE, False)]),
                    ("skipped", [(f6._SIBLING_PARAM_NODE, False)])):
    tmp = Path(tempfile.mkdtemp())
    gate = f6._gate(tmp, [f6._LISTED_CLASS_NODE, f6._LISTED_PARAM_NODE] if cases[0][1] else [f6._LISTED_PARAM_NODE])
    run = pcg.JUnitReportReader.read(f6._junit_with_skips(cases, {f6._LISTED_PARAM_NODE: kind}))
    manifest = f6._manifest(tmp)
    results = {"pytest": run}
    cur_lines, _ = pcg._render_currency(gate, manifest, results)
    currencies = pcg._currencies_for(gate, manifest, results)
    print(f"#### {kind}: verdict={[c.verdict for c in currencies]} notes={[len(c.notes) for c in currencies]}")
    print("  --currency render NOTE lines:", [l.strip()[:70] for l in cur_lines if "NOTE" in l])
    for wave in (False, True):
        lines, ok = wave_gate._render(manifest, currencies, results, wave=wave, selector=[f6._NODE_FILE] if wave else [])
        print(f"  wave_gate._render(wave={wave}) ok={ok} NOTE lines:", [l for l in lines if "NOTE" in l or "KEPT" in l],
              "| pytest line:", [l.strip()[:90] for l in lines if l.strip().startswith(("pytest", "SCOPED"))][:2])
```

### `probes/live/drive.py`
```python
"""adv5 live-junit instrument: real pytest 9.0.3 junit (xunit1) for every outcome shape, read by the gate
module found on --gate-dir, partitioned against a registry that lists every id of the fixture tree."""
import argparse, subprocess, sys, textwrap
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--gate-dir", required=True)
ap.add_argument("--python", required=True)
args = ap.parse_args()
sys.path.insert(0, args.gate_dir)
import pending_contract_gate as pcg  # noqa: E402

HERE = Path(__file__).parent
TREE = HERE / "tree"
A = "pkg/tests/test_live_a.py"
LISTED = {
    A: [f"{A}::TestA::test_red", f"{A}::test_param[x]", f"{A}::test_skip_body", f"{A}::test_skip_marker",
        f"{A}::test_xfail_fails", f"{A}::test_xpass_strict", f"{A}::test_xpass_nonstrict", f"{A}::test_setup_error"],
    "pkg/tests/test_live_modskip.py": ["pkg/tests/test_live_modskip.py::test_red"],
    "pkg/tests/test_live_collerr.py": ["pkg/tests/test_live_collerr.py::test_red"],
    "pkg/tests/test_live_importorskip.py": ["pkg/tests/test_live_importorskip.py::test_red"],
}
reg = ["version: 1", "bounds:", "  - id: probe-bound", '    owner: "probe"', '    reopen_trigger: "probe"',
       '    ruling: "probe"', '    rationale: "probe"', "    files:"]
for path, ids in LISTED.items():
    reg.append(f"      - path: {path}")
    reg.append("        red_nodeids:")
    reg += [f"          - '{i}'" for i in ids]
(HERE / "registry.yaml").write_text("\n".join(reg) + "\n")
(HERE / "gates.yaml").write_text(textwrap.dedent("""\
    version: 1
    gates:
      - id: pytest
        description: "the suite"
        command: ["pytest", "--junit-xml={junit_xml}"]
        reader: pytest_junit
        adjudicated_by: pending-contracts
    """))
gate = pcg.PendingContractGate(registry=pcg.PendingContractRegistry.load(HERE / "registry.yaml"), repo_root=TREE)
manifest = pcg.GateManifest.load(HERE / "gates.yaml")

SCENARIOS = {
    "S1_full_file_a": [A],
    "S2_class_narrowed": [f"{A}::TestA"],
    "S3_k_selected": [A, "-k", "test_red or test_param"],
    "S4_module_skip": ["pkg/tests/test_live_modskip.py"],
    "S5_collection_error": ["pkg/tests/test_live_collerr.py", "--continue-on-collection-errors"],
    "S6_importorskip": ["pkg/tests/test_live_importorskip.py"],
    "S7_maxfail1": [A, "--maxfail=1"],
    "S8_lf_like_deselect": [A, "--deselect", f"{A}::test_param[x]"],
}
for name, sel in SCENARIOS.items():
    xml = HERE / f"{name}.xml"
    proc = subprocess.run([args.python, "-m", "pytest", "-q", "-o", "junit_family=xunit1", f"--junit-xml={xml}", *sel],
                          cwd=TREE, capture_output=True, text=True)
    print(f"===== {name}: pytest rc={proc.returncode} :: {proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else ''}")
    try:
        run = pcg.JUnitReportReader.read(xml.read_text())
    except Exception as e:  # noqa: BLE001
        print(f"  READER RAISED {type(e).__name__}: {str(e)[:200]}")
        continue
    print(f"  collected={sorted(run.collected)}")
    print(f"  failing={sorted(o.node_id for o in run.outcomes)} skipped={list(getattr(run, 'skipped', ()))}")
    lines, ok = pcg._render_currency(gate, manifest, {"pytest": run})
    for line in lines:
        if line.startswith("GATE CURRENCY") or line.startswith("  manifest") or line.startswith("  (this"):
            continue
        print("  " + line)
```

DONE · (report in hand-back) · F6 delta INSUFFICIENT, 0 unsatisfiable: 17/20 wrong gates killed, all adv-4 replays + r8 ref killed; 3 survive (mixed-entry self-destruct, KEPT note on GREEN/wave_gate, cap-3) + module-skip false STALE; 2 decisions (MP5-1 STOP?, node-id wave stale)

---------------------------------------------------------------------------------------------------------------
## RE-GRADE — F6 delta 2 (`64fcdd6`), granted by R35; the last round
- **Graded:** 64fcdd6 · HEAD-at-report: 25ef938 · DIFFERENT (1 behind: inventory docs only). The gate, F6 file and wave_gate are byte-unchanged 64fcdd6..HEAD.
- **VERDICT: CONTRACT INSUFFICIENT. 0 UNSATISFIABLE.**
  - **STOP:** MP6-1.
  - **STOP-candidate (ruling-bound, D3):** MP6-2.
  - **RESIDUAL:** MP6-3, MP6-4, MP6-5.
  - The round-5 findings MP5-1..4 are CLOSED. My survivors N8/N9/N12 and the MP5-4 revert each die on their new pins. The reference now passes MP5-4 and the MP5-2 wave_gate leg (live).
- **Runs used (re-grade):** 19. They were: ref control (510), HEAD (510), probe baseline (7), FIX control (517), 10 scoped wrong builds, 2 collect-only, and 3 live probe-tree drivers (D2 selectors, MP5-4 shapes, the Y2 demo).
- Packages considered: none (no mechanism specified). Odoo-20 portability: n/a. Reuse ledger: none. Fan-out: haiku 3 · sonnet 0 · peak 2.

### Provenance and satisfiability (re-measured, not relayed)
- `scratch_copy.sh --verify-only sdk3f6r9/ref`: VERIFIED, and `loremaster.__file__` resolves inside the copy.
- sha256 against 64fcdd6:
  - F6 file: SAME (`b9a1d7bf…`).
  - Gate: ref = r10ref (`074aa36e…`), the reference by design.
  - wave_gate: differs from 64fcdd6 by exactly the 2-line `currency.detail_lines()` render (the reference's MP5-2 fix; `git diff d78baa3` in the ref).
  - `test_backoff_seam.py` = d78baa3 (`f262be2e`): restored, which clears R5-6.
  - `pending_contracts.yaml` in the ref = d78baa3's. The 64fcdd6 registry row (`packet-66-f6-contract`, call-arg ×1) does not apply, because the tests use tmp registries.
- My copy is `adv5/b2` (scratch_copy of the ref), TREE=1d81b9bd… = the ref.
- **Reference: 510 passed, EXIT=0** (`logs/ref10_control.log`), which reproduces the servicer's 510/510.
- **HEAD 25ef938: 51 failed / 459 passed, EXIT=1** (`logs/head10_red.log`, TREE=42781257…). All 51 reds are F6 nodes (F6 collects 51), which reproduces 51 = declared. Reasons:
  - 49 × `RegistryError` (`red_nodeids` extra key);
  - 1 × the "neither" regex;
  - 1 × `AttributeError` (the plumbing pin: `PytestRun` has no `selection` yet).
  - So every red is for the right reason. ⚠ At HEAD every D2 pin dies at registry load, so RED@HEAD proves nothing about the D2 semantics. The mutations below carry that.

### Round-5 survivors and the MP5-4 probe, re-run against r10ref + 64fcdd6 (declared before the run: `adv5/DECLARED2.sha256`, 08:36)
| build | result | verdict |
|---|---|---|
| X1 = N8 (mixed entry exempt from pytest self-destruct) | PROOF HELD: `MIXED…self_destructs_a_PASSING_and_a_STALE…[code,symbol]` | **KILLED** (MP5-1 closed) |
| X2 = N9 (notes only when ≠ GREEN; rebased into `detail_lines`) | PROOF HELD: the 6 `render…[*-all_skip-*]` | **KILLED** (MP5-2 closed) |
| X3 = N12 (`red_nodeids[:3]`) | PROOF HELD: `self_destruct_reaches_EVERY_listed_id_past_the_third` | **KILLED** (MP5-3 closed) |
| X4: MP5-4 reverted (a module testcase counts as collected) | PROOF HELD: `file_pytest_never_ENUMERATED…[collection_error, importorskip, module_skip]` | **KILLED** (MP5-4 closed) |
| X5: wave_gate's non-scoped branch drops notes | PROOF HELD: 6 `render…[*-wave_full / adjudicated-wave_scoped]` | KILLED |
| X6: wave_gate's scoped-GREEN branch drops notes | PROOF HELD: `render…[*-all_skip-wave_scoped]` ×2 | KILLED |
| MP5-4 live (round-1 instrument on r10ref, `probes/live/ref10_live.out`) | S4 module skip → GREEN; S6 importorskip → GREEN; S5 → only the collection error orphaned | fixed in the reference |

### D2 wrong gates (mine, beyond the servicer's five), plus probe pins with controls
The probe pins are in `adv5/b2/scripts/test_adv5_d2_probe.py` (verbatim below).
- **Baseline (r10ref):** exactly the 3 `still_discharges_a_COLLECTED_pass[…]` fail; the other 4 pass (`logs/ctl2_baseline.log`).
- **FIX control** (r10ref with the scope skip limited to NON-collected ids, a one-line change): **517 passed** = 51 F6 + 7 probes + 459 gate pins (`logs/ctl2_fix.log`, restored byte-exact). So my proposed pins are satisfiable, and the fix breaks no contract pin.

| build | mutation | result vs the F6 contract | verdict |
|---|---|---|---|
| Y1 | selection ignored (file-level scope) | red: `D2_a_CLASS_scoped…`, `D2_a_PARAM_leaf…` | **KILLED** (≈ servicer d2b). ⚠ My declaration listed the base-state probe reds, which Y1's mutation removes; that is a declaration error, recorded and not re-declared |
| **Y2** | `partition_pytest` skips an outcome no selector covers: "an id outside the selection gets NO verdict" (RULING-12's sentence, applied to adjudication) | **0 F6 pins red**; only my 3 `never_hides_an_unlisted_red[…]` probes | **SURVIVES → MP6-1** |
| **Y3** | `selecting_selector` without the `::`/`[` boundary (`startswith(selector)`) | **0 F6 pins red**; only my `class_selector_stops_at_the_name_boundary` | **SURVIVES → MP6-3** |
| **Y7** | `_run_selected_gates` records only the first selector | **0 F6 pins red** (the plumbing pin passes one selector) | **SURVIVES → MP6-4** |
| r10ref itself | the scope test runs before the outcome test, so a COLLECTED id under an unrecognised selector gets no verdict | the 3 `still_discharges…` probes red; FIX passes 517 | **→ MP6-2** |

**Live receipts** (real pytest through the gate's own `_run_selected_gates`; `probes/live/drive_d2.py` → `ref10_d2.out`; `probes/y2_live_demo.py`):
- `--wave pkg/tests`, `pkg/tests/`, `./pkg/tests/test_live_a.py` and the absolute path: r10ref serves **no** "green, delete it" for the collected-and-passing `test_green_listed`, and no stale line for 2 renamed ids. `--wave pkg/tests/test_live_a.py` serves all three. **Same run, same outcomes; the verdict differs by the selector's spelling (MP6-2).**
- **Y2, rendered by `wave_gate._render` in `--wave` mode:**
  - r10ref `--wave pkg/tests` → `RED_ORPHANED — 5 residual(s)`, exit 1.
  - **Y2 `--wave pkg/tests` → `pytest SCOPED … NOT a currency clear` · `CURRENCY: PASS`, exit 0, with 5 real unowned reds in the run.**
  - Y2 `--wave <file>` → 8 orphans, exit 1. That is why no file-shaped pin can see Y2.
- `file::TestA` respects the boundary on r10ref: `TestAB::test_renamed_in_AB` is not judged.
- `--wave file::TestA::` (trailing `::`) and a module-skip-only selection → pytest exit 4/5 → BrokenInstrument. Loud, which is correct.

### MISSING PINS (re-grade)
| id | tag | surviving build + receipt | the test that should exist | defect it catches |
|---|---|---|---|---|
| **MP6-1** | **STOP** (R17 false clear on the healthy path; satisfiable; the reference passes it as-is) | Y2: 51/51 F6 green (`logs/wb2_Y2_*.log`); live: wave exit 0 / CURRENCY PASS over 5 unowned reds | `test_D2_an_UNRECOGNISED_selector_never_hides_an_unlisted_red` (selector ∈ {dir, dir/, ./file}: an unlisted red in a collected file stays RED_ORPHANED) = my probe | Scope leaking into ADJUDICATION. RULING-12's own sentence ("neither stale nor adjudicated nor self-destructed") invites it. A directory `--wave` (wave_gate accepts "node-ids/paths") then passes with orphan reds, breaking wave_gate's own contract ("a scoped RED_ORPHANED still fails", #344). A pin on recognised selectors cannot see it, because there every collected id is in scope. |
| **MP6-2** | **STOP-candidate, ruling-bound (D3)** | r10ref itself; probe `still_discharges_a_COLLECTED_pass` ×3 red on ref, green on FIX (517/517) | `test_D2_an_UNRECOGNISED_selector_still_judges_every_COLLECTED_id` = my probe | R31's CLASS ("only exact id × collected × outcome") is broken by the selector's spelling. A directory, `./` or absolute wave that runs a listed id green serves no self-destruct, and exits 0 where the file-spelled wave exits 1. RULING-12's bound reasons "fail-safe toward silence, never toward a false stale", and that holds only for NOT-collected ids: a collected id has no stale risk, and pytest did look at it, which is the ruling's own scope question. **Fix: scope decides only for ids NOT in `run.collected`** (one line, measured). |
| MP6-3 | RESIDUAL | Y3: 0 F6 reds | the boundary pin (`file::TestAContractAheadPin` must not cover `…PinExtra::…`) = my probe; the reference passes | A false STALE for a prefix-sibling class (`TestFoo` vs `TestFooBar`). It is loud, and the stale text's "confirm with --collect-only" mitigates it. |
| MP6-4 | RESIDUAL | Y7: 0 F6 reds | the plumbing pin with ≥ 2 selectors (`--wave a.py b.py`) | Multi-file waves (common) silently lose discharge and stale verdicts for every file after the first. The direction is silence; the SCOPED flag bounds it. |
| MP6-5 | RESIDUAL, NO ROUND (the servicer's stated bound) | r10ref live S4: a module-skipped registered file renders `pytest GREEN` with no KEPT note | a KEPT note for the listed ids of a never-enumerated file | the rider's "render says so" at file granularity |

**CLASS for MP6-1/2:** *the scope walk answers only "is a NOT-collected id's absence evidence?"; it never touches an id the run collected (that id's outcome adjudicates it), and never the partition.*
- **CHOKEPOINT:** `pytest_self_destruct_findings`: `if run.selection and selector is None and node_id not in run.collected: continue`. `partition_pytest` stays scope-blind.
- **SIBLINGS TRIED:**
  - selection ignored; selection used for adjudication (servicer d2c, and my Y2 variant on the partition);
  - no boundary; first-selector-only;
  - dir, dir/, ./, absolute path, trailing `::`;
  - a module-skip-only selection; a multi-file selection.
- **SIBLINGS NOT TRIED:**
  - `--wave=--deselect=…` / `--wave=-x` single-token flags. These are forwarded verbatim; any of them reads as unrecognised (silence), which is the same class as MP6-2.
  - A `::` inside a parameter id (the ruling's named bound).
  - Windows path separators (not this fleet).

### P1b / P1c deltas
- **P1b:** "unlisted red → ORPHANED" was ∀ in round 5. Under D2 it is now **guarded by "selector recognised"** (MP6-1). "A listed id passes → self-destruct" is **guarded by "selector recognised"** (MP6-2). Every other row is unchanged and ∀.
- **P1c:**
  - The rider's render now has ONE chokepoint (`GateCurrency.detail_lines`). X5 and X6 kill both wave_gate branches, so sharing is proven by mutation.
  - The scope decision has one chokepoint (`selecting_selector`). Its effect is pinned for recognised selectors only (MP6-1/2/3).
  - The plumbing is pinned on one selector only (MP6-4).
  - Spelling tests: the plumbing pin reads the `PytestRun.selection` field. That is an interface the ruling names, not a source scan. No verdict needed.

### Message/assert check of the 25 new nodes
- MP5-1, MP5-3, MP5-4 and D2 (1)–(5): each assertion checks what its message promises. MP5-3 bounds the orphans to exactly 2. D2(3) compares the full run byte-for-byte.
- The MP5-2 render pin keeps round 5's form (`kind`, `kept`, no ORPHAN on that line), now ×12.
- No gap found.

### Decisions needed (re-grade)
- **D3 (MP6-2):** confirm that RULING-12's "unrecognised selector → not in scope" bound applies to NOT-collected ids only. My pick: yes. It is one line, measured 517/517, and it removes a selector-spelling dependence from R31's class.
- **MP6-1 routing:** a STOP by the lead's definition. My pick: the servicer adds the one probe pin. The reference already passes it, so there is no reference change and no builder delay.

### Re-grade receipts
| run | log | EXIT | count | TREE |
|---|---|---|---|---|
| ref control (5 gate files) | `logs/ref10_control.log` | 0 | 510 passed | 1d81b9bd… |
| HEAD 25ef938 (5 gate files) | `logs/head10_red.log` | 1 | 51 failed, 459 passed | 42781257… |
| probe baseline (r10ref) | `logs/ctl2_baseline.log` | 1 | 3 failed, 4 passed | 2a9455d6… (b2 + probe file) |
| FIX control | `logs/ctl2_fix.log` | 0 | 517 passed | 5f0e3345… (FIX applied), restored byte-exact |
| 10 builds | `logs/wb2_*.log`, `logs/batch2_summary.txt` | 7×0, 3×4 | per row | 2a9455d6… before each; 10/10 RESTORED byte-exact (`cmp`, gate + wave_gate) |

### Re-grade instrument (verbatim): `adv5/b2/scripts/test_adv5_d2_probe.py`
```python
"""adv5 re-grade probes (scratch only): my proposed D2 pins. An UNRECOGNISED selector (a directory, './file',
an absolute path — all shapes wave_gate forwards and pytest accepts) must (a) never hide an unlisted red, and
(b) never silence the OUTCOME of an id the run COLLECTED (scope is a question only about ids NOT collected);
(c) a class selector covers its class only, on the name boundary."""
import dataclasses
import os
import sys
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from test_pending_contract_gate_f6 import (  # noqa: E402
    _LISTED_CLASS_NODE, _LISTED_PARAM_NODE, _NODE_FILE, _UNLISTED_NODE, JUnitReportReader, _currency, _gate, _junit)

UNRECOGNISED = ["loremaster/tests", "loremaster/tests/", f"./{_NODE_FILE}"]


def _run(cases, selection):
    return dataclasses.replace(JUnitReportReader.read(_junit(cases)), selection=selection)


@pytest.mark.parametrize("selector", UNRECOGNISED)
def test_probe_an_unrecognised_selector_never_hides_an_unlisted_red(tmp_path, selector):
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE])
    cur = _currency(tmp_path, gate, "pytest", _run([(_LISTED_CLASS_NODE, True), (_UNLISTED_NODE, True)], (selector,)))
    assert cur.verdict == "RED_ORPHANED" and any("test_a_new_regression" in o for o in cur.orphans), (cur.verdict, cur.orphans)


@pytest.mark.parametrize("selector", UNRECOGNISED)
def test_probe_an_unrecognised_selector_still_discharges_a_COLLECTED_pass(tmp_path, selector):
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, _LISTED_PARAM_NODE])
    cur = _currency(tmp_path, gate, "pytest", _run([(_LISTED_CLASS_NODE, True), (_LISTED_PARAM_NODE, False)], (selector,)))
    assert not cur.ok and any(_LISTED_PARAM_NODE in o and "green" in o.lower() for o in cur.orphans), (cur.verdict, cur.orphans)


def test_probe_a_class_selector_stops_at_the_name_boundary(tmp_path):
    extra = f"{_NODE_FILE}::TestAContractAheadPinExtra::test_gone"
    gate = _gate(tmp_path, [_LISTED_CLASS_NODE, extra])
    cur = _currency(tmp_path, gate, "pytest", _run([(_LISTED_CLASS_NODE, True)], (f"{_NODE_FILE}::TestAContractAheadPin",)))
    assert cur.ok and not any("PinExtra" in o for o in cur.orphans), (cur.verdict, cur.orphans)
```

Other instruments: `adv5/mkbuilds2.py` (specs + declarations), `adv5/runwb2.sh`, `adv5/control2.sh`, `adv5/probes/live/drive_d2.py`, `adv5/probes/y2_live_demo.py`.

DONE · (report in hand-back) · RE-GRADE 64fcdd6: INSUFFICIENT, 0 unsatisfiable — MP5-1..4 closed (N8/N9/N12/MP5-4 killed); STOP MP6-1 (scope leaks into partition: dir --wave passes over orphan reds, survives all 51 pins); STOP-candidate MP6-2 (r10ref silences collected ids under dir/./abs selector; one-line fix 517/517, D3); residuals MP6-3..5
