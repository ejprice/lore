# REPORT — adversary-58-r5-2 (packet 58 r5 + r5.1 delta grade, graded commit `805a687`)

brief-base v27 read · brief project v7 read

## SUMMARY BLOCK
- **VERDICT: CONTRACT INSUFFICIENT** — 5 missing pins (MP-1…MP-5, each with a surviving, landed-and-probed wrong build) + 1 SAT over-fire (r5.1's straggler legs (i)/(ii) RED on the reference).
- **State:** done-with-deviations. **Deviations:** (1) my reference is r5's reconstructed md5-exact, not independent (§INDEPENDENCE); (2) I over-parallelised runs, so 5 heal legs timed out under load — corrected with a P0 baseline and quiet re-runs (§LOAD/§QUIET); (3) §MUTATION ran on `wb` (switch unset) not `ref`, to avoid mutating a tree under a live SAT.
- **P1 — did a wrong build survive? YES, 5:** WD17 (refusal serves false rows/cap + "a smaller supersede will succeed"; the reference itself serves neither fact) · WD16B (compose's refusal re-wrapped with a plain `raise` — pin checks `__cause__` only) · WD9 (kind guard dropped for 58's four markers — 63c's typed-kind hand-lists omit them) · WD15D (`rows=` under-declared on RELATE fragments > 1 500 statements — silences am-15 §1.3's WARN trigger) · WD12K (heal swallows a store/transport fault at chunk ≥ 2 — both door fixtures hold ONE straggler). **Killed (29):** WD1 WD1H WD2 WD3 WD3B WD4 WD5 WD6 WD7 WD7A WD7C WD8 WD12 WD13 WD14 WD15 WD15C(by L3's size only) WD16 WD19 WD21 WD22H X7B + all seven re-anchored W-* (TUPLE IMPLICIT REBIND HEAL2 F4-PREFIX F3-ROOT NOOP-DRIVERS). Quiet-run verdicts (am-16 §3): WD22H, W-HEAL2, W-F3-ROOT, W-F4-PREFIX, W-NOOP-DRIVERS KILLED; WD22 GREEN (a correct build); the r4 heal leg is SLOW (302.55 s), not hung (§QUIET-VERDICTS). All 7 r3 W-* re-anchored builds die.
- **Reference / SAT (one full-set run):** `195 failed, 8412 passed, 47 skipped` on r5's reference at `805a687` — 188 packet-64b-i, 1 known probe signin, 1 #615 pin (red at `805a687` by design), 3 load timeouts, **2 attributable: r5.1 sweep legs (i)/(ii)** (`straggler.control_calls == legacy + 1`; the reference adds 4 doors: 3 heal reads + the apply, all LOUD).
- **Runs used:** 1 full contract set (REF SAT) + 1 BASE declared-set + 1 plain registry run + 45 scoped wrong-build / control runs (incl. 7 quiet re-runs; batches 5/6/11 stopped by me for run budget) + 3 mutation proofs + 6 offline/one-test probes; per-run lines in §RUNS / §W-STAR / §MUTATION.
- **QUANTIFIER (P1b):** 13 invariants; 5 GUARDED-with-surviving-door (Q4 `__cause__`, Q6 unpinned, Q8 size, Q9 kind, Q11 one chunk), 1 unsatisfiable (Q13), rest ∀ with kill receipts — table §P1b.
- **ENFORCEMENT (P1c):** chokepoints named per rule; PROXY on the hub refusal (`__cause__`); sharing of `fragment_rows` unprovable by behaviour (ruled; cold audit) — table §P1c; legs empirical except the gate-partition row (inspection).
- **P-PKG:** `more_itertools.constrained_batches` keep (installed 11.1.0 source read; NOT declared in pyproject — BC-r4-1 owed), `_txn.fragment_rows` reuse; diff vs r5: none. **P-PRIOR:** 0 new rule symbols (the counter retired to `fragment_rows`). **Odoo-20 portability:** n/a — no Odoo seam touched (author's line agrees).
- **Registry (§10.2):** node lists EXACT both ways at plain `805a687` (547 red = 232 + 315 listed, 0 listed-green, 0 uncollected). **§MUTATION:** 3/3 `PROOF HELD` (L1/L2, un-annotated, WARN), declared from `--collect-only`.
- **Reuse ledger:** none (no production code). **Packages considered:** see P-PKG. **Graded:** `805a687` · HEAD-at-report: `d3344ad` · DIFFERENT (3 ahead: gate per-node fix, probe signin, f6 prose — no 58 test or sweep file changed).
- **Decisions needed (sidecar-58-1):** bucket MP-1…MP-5 + the SAT over-fire (my tags: MP-1 NEW PROPERTY; MP-2/3/4/5 PINNED PROPERTY, NEW CASE; MP-3 REPEAT CLASS of r5 F-4; over-fire = an unsatisfiable r5.1 pin, must be fixed before any build).
- **Pointers:** §WB-OWN · §DECLINED-DIFF · §RUNS · §W-STAR · §SAT · §SAT FINDING · §MISSING PINS · §P1b · §P1c · §P2 · §WD18 · §MUTATION · §LOAD/§QUIET · §RESIDUALS · §INSTRUMENTS. Fan-out: haiku-runner 18 · sonnet 0 · peak ~8.

## Capability check (brief-base §4)
- What the brief demands and what I have: lore tools (loaded), Bash, Agent (haiku-runner), SendMessage, store `:18000`. Nothing missing.
- Task row `2cb8d4ff…` is held by lead-58 (in_progress), so I do not claim it (§5: not my row).

## Routing table (written before the first sweep — brief-base §3)
| step | tier | who | reason |
|---|---|---|---|
| read am-15, r5 report, diff | 3 | me | grading needs the frame |
| scratch copies + reference reconstruction | 1-ish, done inline | me | needs judgment on anchor misses; short |
| pytest runs (reference SAT, wrong builds) | 1 | haiku-runner | test runs |
| wrong-build construction (patching scratch) | 3 | me | a mis-built wrong build is a self-sealing error |
| verdicts on each run | 3 | me | adversarial grading |
| retired-name / node-id diffs | 1 | me inline, parallel batch | small, read in full anyway |

## §WB-OWN — my wrong-build set, enumerated BEFORE reading r5 §DECLINED (am-15 §10.5), 2026-11-09 ~23:35Z
Derived from am-15 §1–§2, §3, §4.1, §8, §10 only.

| id | wrong build | the pin I expect to kill it |
|---|---|---|
| WD1 | accessor = `min(5000-derived statement bound, row-derived bound)` (am-15 §1.4) | L1 (unpatched cap arithmetic), L2 |
| WD2 | accessor uses a literal 50 000 (no live read) | L4 (shrink by per·d) + every 5 000-fixture leg |
| WD3 | `tasks.py` copies `TXN_ROW_HARD_CAP` at IMPORT (F21) for the accessor | the 5 000-fixture cap+1 refusal |
| WD3b | import-time copy only in the HEAL PACKER (accessor live) | packer chunk-boundary legs under the fixture |
| WD4 | packer keeps the retired statement bound (`max_size=5000`) | L3 |
| WD5 | packer prices every straggler at ONE unit (`get_len=lambda _: 1`) | over-weight row / chunk ≤ cap spy |
| WD6 | accessor K-blind: `fixed` measured at K=0 for every K | PR16 K-set legs |
| WD7 | private WARN comparison in `_apply` (own 800 / own 10 000 / import-time copy of threshold) | fixture-800 WARN crossing |
| WD7b | WARN keyed on `statement_count` (not `row_count`) | none behaviourally (58 un-annotated) — expected bound |
| WD7c | WARN emitted twice (house fn + private) | "exactly ONE WARNING" |
| WD8 | the four classes classified by SUBSTRING (`marker in lowered`) | 63c echoed-phrase sweep over the 4 hosts |
| WD9 | prefix match but kind not checked (a non-THROWN kind with the prefix classifies) | echoed sweep / typed instance legs |
| WD10 | a class raised by a second `if label ==` at the raise site, bypassing `_domain_rejection_error` | maybe none (spelling) — expected bound |
| WD11 | heal invoked through a callback table (BC-r4-3(c)) | to read |
| WD12 | heal swallows its APPLY fault (§10.3) | forgery-door sweep straggler legs (iii) |
| WD13 | heal swallows its READ fault | forgery-door sweep (ii) |
| WD14 | refusal AFTER the stamp at cap+1 (mutating then refuse) | byte-inert SELECT before==after |
| WD15 | a 58 fragment under-declares `rows=` | the compose-spy `fragment_rows == Σ len(statements)` |
| WD16 | refusal lets `compose`'s `TxnRowCapExceededError` reach the caller | A-9 type check |
| WD17 | refusal row count served ≠ fragment_rows (e.g. hand formula 4+K+3N) | "served == fragment_rows" pin |
| WD18 | gate partition still adjudicates an unlisted red in a 58 file | node lists exact vs `--collect-only` |
| WD19 | `proven_no_key` FALSE for one of the four classes | §DUAL-63c pins |
| WD20 | WARN emitted only from supersede path, not heal (or the reverse) | to read |
| WD21 | heal door reports success but skips stragglers beyond first chunk | convergence count == |healable| |

## §DECLINED-DIFF — my §WB-OWN vs r5 §DECLINED (read AFTER §WB-OWN was on disk, 2026-11-09 ~23:45Z)
| r5 §DECLINED | mine | verdict |
|---|---|---|
| X1 (min / literal 5 000) | WD1, WD2 (literal 50 000), WD1H (hidden 10 000) | covered; WD2b literal-5 000 added |
| X2 (import-time copy) | WD3 (accessor), WD3B (packer) | covered |
| X3 (private `len(statements)` counter) | — (I listed the WARN twin WD7b) | am-15 §2 ruled bound; cold-audit mutation. Not built (unprovable by behaviour, by ruling) |
| X4 (`rows=` under-declaration) | WD15 | covered |
| X5 (private WARN) | WD7, WD7A; + WD7C (double warn) | covered + 1 |
| X6 (substring classifier) | WD8; + WD9 (kind-blind prefix) | covered + 1 |
| X7 (bypass `_domain_rejection_error` / class on unspecified label) | WD10 (I expected a spelling bound); + WD19 (`proven_no_key` false) | X7b ("class left on the unspecified label") ADDED to my set |
| X8 (rewrap `raise … from error`) | WD16 (no pre-check), **WD16B (rewrap with a PLAIN `raise` inside `except` → `__cause__` is None)** | **WD16B not anticipated by r5** — built |
| X9 (refusal after the stamp) | WD14 | covered |
| X10 (unit-weight packer) | WD5 | covered |
| X11 (heal boundary read at import) | WD3B | covered |
| X12 (B-6 two-arg call) | — | a crash, not a silent wrong; exhibited by r5's ref1; not re-built |
| X13 (58 tier dropped from `_ROLLBACK_LOG_TIERS`) | — | ADDED to my set as not-delta (r3 property); not built (time) |
| X14 (W-* replay) | — | am-15 §5 item 3 — mine |
| X15 (gate partition adjudicates an unlisted red) | WD18 | covered — graded as node-list exactness vs a plain run |
| X16 (heal swallows APPLY fault) | WD12; + WD13 (swallows READ) | covered + 1 |
| — | **WD17: refusal serves a WRONG row count / promises a smaller supersede succeeds** | **not anticipated; am-15 §1.2 rider "the row count the refusal serves == fragment_rows" + BC-r5-4** — built |
| — | WD21: heal stops after its first chunk | not anticipated (likely killed by convergence count) — built |
| — | WD6: K-blind accessor | r2 PR16's graded property; re-run on the re-keyed legs |

## §TREES — what each scratch tree is (provenance receipts)
- All under `…/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/`, each made by `./scripts/scratch_copy.sh` (EXIT=0, provenance asserted by the tool), then `git checkout 805a687 --` of the gate/registry/probe files that peers had dirty or moved (HEAD moved `805a687` → `c7f8f1d` (fix(615), scripts only) → `5ff9209` (REPORTs only) during my copies; `git diff --stat 805a687` over `loremaster/ scripts/` in each tree = only what I applied below).
- `base` = `805a687` + §HELD parts 1/3/4 (md5 `dbba9753…`/`15f38e31…`/`f4048e2d…`, each equal to its `git show <sha>:REPORT…` extraction). TREE `0b9c0a2d…` before HELD.
- `ref` = base + `build_ref_r5.py` v4 (md5 `c2c9a273…` = r5's recorded value) over r5's chain dir (every chain md5 equal to r5 §RE-BASE-STEP1's). Output `chain replayed; skipped exactly the 5 declared anchors`; result `_txn.py 8d37d2f4…`, `tasks.py 3360a9cf…` = r5 §INSTRUMENTS' v4 values. **This is r5's reference, reconstructed md5-exact — not an independent one** (see §INDEPENDENCE).
- `wb` = ref + `wb_patch.py` (env-switched delta wrong builds; `tasks.py 2e57b0a2…`, `_txn.py 3eefaae5…`). `wb2` = ref + `wstar_patch.py` + the W-NOOP-DRIVERS test edit (r3's seven W-* re-anchored; md5s in `wb2.md5`). `plain` = `805a687`, no HELD (the registry's own world).
- `loremaster.__file__` is printed in every run log header and resolves inside the run's tree (receipts in each `run-*.log`).

## Packages considered (P-PKG — my table first, then the diff)
| mechanism | library | what I READ | verdict |
|---|---|---|---|
| heal packing by weight under a max | `more_itertools.constrained_batches` 11.1.0 | installed signature `(iterable, max_size, max_count=None, get_len=len, strict=True)` + body (greedy; `strict` raises `ValueError` on an over-size item) in `ref/.venv` | keep (= r5/am-8). ⚠ `more-itertools` is still NOT declared in either `pyproject.toml` at `805a687` (grep: 0 hits) — BC-r4-1 owed; transitively installed |
| the one row counter | `_txn.fragment_rows` (in-house) | its source at `805a687` (`sum(len(f.statements) if f.rows is None else f.rows …)`) | reuse (= r5) |
| shrinking a module constant per test | `pytest.MonkeyPatch.setattr(raising=True)` | — | keep (= r5) |
| the probe's timing | none | — | n/a |
- **Diff vs r5's table:** identical rows; nothing marked bespoke; no hand-roll one level down found (the packer calls `constrained_batches` directly with `get_len=lambda entry: entry[3]`, a stored weight).

## P-PRIOR — new rule-deciding symbols the contract demands
- `TaskLedger.max_reanchor_dependents`, `HubSupersedeRefusedError`, `StragglerHealPackerError`, the four `Txn*Error` classes: all r1–r4 symbols already graded; r5 adds none. The counter (`_composed_statement_count`) was RETIRED in favour of the existing owner `_txn.fragment_rows` (am-15 §2) — correct prior-art call. The WARN routes to the existing owner `SurrealStore._log_transaction_size`. Test-support: `shrunk_row_caps` fixture — `test_sdk3_row_bound.py` uses inline `monkeypatch.setattr` (read by r5; I re-read `_reanchor_58_support.py`), no shared fixture exists → hand-rolled is right.
- Searches: r5's DRY ledger + my reading of `_reanchor_58_support.py`, `_txn.py` (`fragment_rows`, `_THROWN_DOMAIN_MARKERS`, `proven_no_key`) at the reference. No duplicate owner found.

## P-PORT
- `Odoo-20 portability: n/a — no Odoo seam touched` (lore repo; no Odoo model/field/view in the contract or fixtures). Author's line: same. No diff.

## P6 — corpse sweep (grep: rename exhaustiveness, the sanctioned case), `plain` tree = `805a687`, 2026-11-09 ~23:40Z
Pattern (bare): `STATEMENT_HARD_CAP|STATEMENT_WARN|statements, exceeding|statement[- ]cap|-statement transaction cap|_composed_statement_count` over `git ls-files 'loremaster/tests/*.py' 'scripts/*.py' 'lore*/tests/*.py'` — **files_opened=381 hits=33**. No hit is a live assertion on a retired name or retired message text. Per hit:
| file:line | verdict |
|---|---|
| `_reanchor_58_support.py:84` | keep — the one re-export comment of `RETIRED_STATEMENT_CAP` |
| `_surreal_fakes.py:28,108,287,424` | history prose (SDK3/66's fake; not 58) — keep; :424 docstring says "statement cap is a SurrealStoreError" — stale prose in a fake, 66's, residual |
| `test_exhaustion_fates.py:583` | history — keep |
| `test_indexer.py:31,688` | indexer prose (66) — stale wording, not 58's; residual for 66 |
| `test_ingest_entity_seam.py:589,591` | history naming the retired constant — keep |
| `test_reanchor_58_r2_scale.py:76,77` | keep — names the bound L3 kills |
| `test_reanchor_58_r3_convergence.py:138` | keep |
| `test_sdk3_connection_factory.py:406` | history — keep |
| `test_sdk3_index_batching.py:5,26,182,194` | history (R3/R4 receipts) — keep |
| `test_sdk3_row_bound.py:5,6,7,10,12,22,41,45,125,137,279` | the SDK3 kill pins for a surviving statement cap/warn — keep (load-bearing, alive) |
| `test_supersede_reanchor_58.py:625,626,633,709` | keep — L2 docstring/subject + A-9 comment |
| `test_surreal_apply.py:556,1442,1505` | history — keep |
- **Production-side corpse (reference, NOT the contract):** the reference heal's `StragglerHealPackerError` text still says *"composes N statements, over the {cap}-statement transaction cap"* (`ref/…/tasks.py` `_reanchor_stragglers`). The contract's PE check (R5-D7) accepts `"cap" or "row"`, so a builder that copies that stale prose passes — the served error names the wrong bound. Residual (§RESIDUALS R-3).

## §RUNS — wrong-build results (each: ADV_WB switch on a reference tree; log `adv58r5b/run-wb*-<tag>.log`; header prints `ADV_WB seen = <id>` and `loremaster.__file__` inside the tree)
| build | tree · tests run | count line · EXIT | killed by | verdict |
|---|---|---|---|---|
| P0 control (ADV_WB unset) | wb · CLS set (r5_rows, a28c, am37_13_3, q1b, q1c) | `1132 passed` · 0 | — | the switch tree IS the reference when unset |
| WD1 `min(5000-derived,row-derived)` | wb · HUB set (TestTheHubBoundIsDERIVED, r2_probes, r2_rulings, r2_scale) | `3 failed, 56 passed` · 1 | L1[0], L1[2], L2 — exactly the declared L-legs | KILLED |
| WD14 stamp written, then refuse | wb2 · HUB set | `8 failed, 51 passed` · 1 | r1 cap+1 ×2, r2 K-set cap+1 ×6 (byte-inert snapshot) | KILLED |
| WD2 literal `50_000` (no live read) | wb · HUB set | `16 failed, 43 passed` · 1 (2 of the 16 by pytest-timeout >300 s: the wrong accessor sized ~16 665-dependent fixtures) | L4 (`PR14`), `PR2`, MUTATION leg, cap/cap−1 ×4, r2 K-set ×6, PR16, r2 packer MUTATION + cap+1 ×6-blocker | KILLED |
| WD8 substring classifier for the four markers | wb · CLS set | `112 failed, 1020 passed` · 1 | a28c `test_am36_1_2_an_echoed_phrase_moves_nothing` ×108 (the four `fifty-eight-throw-*` hosts × phrases) + r5_rows echoed-marker ×4 | KILLED (two independent pins) |
| WD15C `rows=1` on any RELATE fragment > 1 000 statements | wb2 · HUB set + r5_rows + supersede_reanchor_58 + sdk3_row_bound | `1 failed, 117 passed` · 1 | ONLY L3 (`got [3754]` heal rows < 5 000) — the un-annotated pin (3 dependents) and L2 (asserts success only) stay GREEN | KILLED **by accident of L3's size** (P2: see WD15D) |
| X7B heal-chunk marker dropped from the classifier (class left on the unspecified label) | wb2 · r5_rows, r3_tiers, a28c, am37_13_3, q1b, q1c, r2_rulings | `5 failed, 52 passed, 32 errors` · 1 | collection ERROR in the four 63c files (`exactly ONE marker must classify to TxnHealChunkError's label … found []` — the derived marker set) + r3_tiers ×1 + r5_rows led-THROW ×4 | KILLED (loud) |
| **WD15D** `rows=1` on any RELATE fragment > 1 500 statements (between L3's 1 251-pair chunk and L2's 1 666) | wb2 · supersede_reanchor_58 (whole), r2_scale, r5_rows, r2_probes, sdk3_row_bound | **`91 passed` · 0** | nothing | **SURVIVES** |
- **WD15D landed (P0 probe `adv58r5b/probe_wd15d.py`, offline, builds the supersede fragments exactly as the accessor does):** `ADV_WB=None n=1666 statements=5003 fragment_rows=5003` · `ADV_WB=WD15D n=1666 statements=5003 fragment_rows=3338` · `ADV_WB=WD15D n=3400 statements=10205 fragment_rows=6806` — `loremaster.__file__` inside `wb2` each time. So at a 3 400-dependent hub (past am-15 §1.3's 10 000-row WARN, ≈3 332 dependents) the house WARN — **the ruled re-open trigger of the accepted timeout bound** — does not fire, and `compose`'s own bound under-counts by ⅓.
| **WD9** the four markers matched by the anchored prefix for ANY kind (the `untyped or kind == THROWN` guard dropped for 58's markers only) | wb · CLS set | **`1132 passed` · 0** | nothing | **SURVIVES** |
- **WD9 landed (P0 probe `adv58r5b/probe_wd9.py`, offline, `surrealdb.errors.parse_query_error`):** reference: typed `Query`/`NotFound` errors with text `An error occurred: claim_lost:t:1` → `'unspecified rejection'`; under `ADV_WB=WD9` → `'claim lost — another claimant won the compare-and-set'`; the governed twin (`governed_conflict:`) → `'unspecified rejection'` on both (control: only 58's markers lost the guard). Why nothing sees it: 63c's `test_fixwave_a28c_63c_i_a.py::…::test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch` is GENERATED over every typed kind × `_HOSTILE_TEXTS` against `text_labels` — **both hand-listed, and neither holds 58's four markers or labels** (`_HOSTILE_TEXTS["governed"] = "An error occurred: governed_conflict:t:1"` is the governed twin). r5 §DUAL-63c grew `hosted` and `_ECHO_HOSTS` in that file but not these two sets.
| WD3 accessor reads an import-time copy of `TXN_ROW_HARD_CAP` | wb · HUB set | `16 failed, 43 passed` · 1 | the same 16 as WD2 (the shrink never reaches the copy) | KILLED |
| WD19 `proven_no_key` FALSE for `TxnCasLostError` | wb · CLS set | `23 failed, 1109 passed` · 1 | q1c predicate cells ×18, am37 CREATE-fault ×2, q1b ×2, r5_rows construction ×1 | KILLED |
| WD16 no ledger pre-check (compose's `TxnRowCapExceededError` reaches the caller) | wb · HUB set | `8 failed, 51 passed` · 1 | r1 cap+1 ×2, r2 K-set ×6 (the TYPE check) | KILLED |
## WD18 / X15 — registry node lists vs a plain-`805a687` run, both ways (am-15 §10.2)
- Run: `adv58r5b/plain_run.sh` on `plain` (= `805a687`, no §HELD; TREE `1d3001fa…` header in `run-plain.log`), all 34 registered files: `--collect-only` **1924 collected**; run **`547 failed, 1375 passed, 2 skipped`** EXIT=1, no cap kill / no timeout.
- Diff (`adv58r5b/registry_diff.py`, junit node ids vs `registry_805.json` = `scripts/pending_contracts.yaml` at `805a687`): `[58] files=21 listed=232 listed_not_collected=0 listed_but_GREEN=0` · `[64b-i] files=15 listed=315 listed_not_collected=0 listed_but_GREEN=0` · `red=547 red_unlisted_anywhere=0`.
- **Verdict: the node lists are EXACT both ways at `805a687`.** Control on the instrument: the reconstructed red set equals the union of the listed sets to the node (547 = 232 + 315 with both differences empty), which a mis-reconstructed id would break. With `c7f8f1d`'s per-node-only partition (builder-615-1, not graded here), any NEW red in a 58 file is RED_ORPHANED. Not graded: whether each id is listed under the RIGHT owner (r5.1 split shared files by failure reason; I did not re-adjudicate reasons).
| WD6 K-blind accessor (`fixed` measured at K=0 for every K) | wb · HUB set | `9 failed, 50 passed` · 1 | L1[2], PR2, r2 K-set [1,2,3,per,per+1], cap[K=2], PR16 | KILLED |
| WD15 `rows=1` on EVERY non-empty RELATE fragment | wb · CLS set (incl. r5_rows) | `1 failed, 1131 passed` · 1 | r5_rows `test_every_supersede_and_heal_transaction_counts_one_row_per_statement` | KILLED |
| **WD16B** no pre-check; compose's `TxnRowCapExceededError` caught and re-raised as `HubSupersedeRefusedError(...)` with a PLAIN `raise` (no `from`) | wb · HUB set | **`59 passed` · 0** | nothing | **SURVIVES** |
- **WD16B landed (P0 probe `adv58r5b/probe_wd16b_test.py`, run in `wb` then removed):** reference → `PROBE type=HubSupersedeRefusedError cause=NoneType context=NoneType` (probe `1 failed` — the refusal is decided before compose); `ADV_WB=WD16B` → `context=TxnRowCapExceededError` (probe `1 passed`). The A-9 pin checks `__cause__` only; a plain `raise` inside `except` sets `__context__`. The pin's own message names exactly this build ("the ledger re-wrapped compose()'s row-cap refusal").

## ⚠ SAT FINDING — r5.1's straggler legs (i) and (ii) are RED on the reference (over-fire), 2026-11-09 ~23:55Z
- Run: `adv58r5b/run.sh ref ref-fds scripts/test_forgery_door_sweep.py` → **`2 failed, 22 passed`** EXIT=1 (`run-ref-fds.log`; `loremaster.__file__` in `ref`). Red: `TestTheHealDOORSAreOnTheStragglerPath::test_i_…` and `::test_ii_…` (iii, iv and both former-#614 ids GREEN).
- Reason, from the sweep's own render: the straggler world makes **8** store calls vs the legacy world's **5** (doors k=5,6,7 `run_query` = the heal's superseded-row read is k=5 in both worlds; k=6 straggler read, k=7 head-existence read `resolve_existing_rows`, k=8 the apply `execute_transaction`). Leg (i) asserts `straggler.control_calls == legacy.control_calls + 1` and `doors[:-1] == legacy.doors`; leg (ii)'s non-vacuity asserts the same `+ 1`. **All 8 doors are LOUD on the reference** ("ALL 8 DERIVED DOORS FAIL LOUD") — the property am-15 §10.3 rules holds; the pins encode a door COUNT nobody ruled.
- Provenance: r5.1 STEP 2 "measured once at HEAD … both worlds give the SAME 4 doors" — at HEAD the heal does not exist, so "+1" was an assumption about the unbuilt heal's read shape, never measured on a reference; r5.1 has no SAT row for these four legs. am-15 §10.3 (i) says the observed doors "include the heal's read and the heal's apply, by name — and the observed count equals the derived count"; it does not say the straggler adds exactly one.
- Consequence: a builder implementing the graded r1–r4 heal (three reads, then chunked applies) can never green (i)/(ii) without collapsing the heal's reads into the apply — a design change no ruling makes. This is the C-DEF class (a pin red on a correct build), found in round 1 of this delta as the brief's "Round 1 grades contract + REFERENCE together" rule intends.
| **WD17** refusal serves a FALSE row count + FALSE row cap and promises "A smaller supersede will succeed." | wb · HUB set | **`59 passed` · 0** | nothing | **SURVIVES** |
- **WD17 landed (P0 probe `adv58r5b/probe_wd17_test.py`, run in `wb` then removed):** `ADV_WB=WD17` served `… has 1666 dependents; one supersede re-anchors at most 1665 dependents; it would compose 7 rows, over the 3-row cap — refused, nothing changed. A smaller supersede will succeed.` and the leg passed. The REFERENCE serves `… re-anchors at most 1665 dependents (the store's transaction bound, derived) — refused, nothing changed. This is a pinned KNOWN BOUND …` — **it names neither the rows it would compose nor the row cap**, so the reference itself does not meet am-15 §1.2 / BC-r5-4, and no pin notices.
| WD7 private WARN comparison (own literal 10 000) in `_apply` | wb · WARN set (crossing leg, r2_probes, r2_rulings, sdk3_row_bound) | `2 failed, 53 passed` · 1 | r1 `test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS`, `test_PR13_CONTROL_the_house_policy_DOES_warn_at_that_size` | KILLED |
| WD1H accessor `min(row-derived, 10 000-derived)` (a hidden bound ABOVE L2's 5 003 rows) | wb · HUB set | `2 failed, 57 passed` · 1 | L1[0], L1[2] only (L2 passes — its hub is below 10 000 rows) | KILLED — by the L1 arithmetic alone; r5 §FORALL's "GUARDED by size" applies to the PACKER, not the accessor |
| WD7A private WARN against an import-time copy of `TXN_ROW_WARN_THRESHOLD` | wb · WARN set | `2 failed, 53 passed` · 1 | same two as WD7 | KILLED |
| WD7C a SECOND WARN (house fn + a private one at the live threshold) | wb · WARN set | `3 failed, 52 passed` · 1 | PR13 (stubbed house fn ⇒ the private one shows), PR13 CONTROL, the crossing leg ("exactly ONE") | KILLED |
| WD12 heal swallows a non-domain store/transport fault at its APPLY (every chunk) | wb · DOOR set (forgery sweep, r2_rulings, heal class, r3_probes) | `4 failed, 58 passed` · 1 | r2 `TestAHealStoreFaultIsLOUD::test_every_heal_door_after_the_backfill_RAISES[store,transport]` — the sweep's legs (i)/(ii) are red too but are red on the REFERENCE as well (§SAT FINDING), so they earn no kill credit; leg (iii) is GREEN (it tests the instrument, not the build) | KILLED (by r2's pin, not by r5.1's) |
| WD13 heal swallows its first READ fault (returns, heals nothing) | wb · DOOR set | `6 failed, 56 passed` · 1 | the legacy-world sweep (`…legacy_store_FAILS_LOUD`, `…SWALLOWS_its_backfill_failure_is_CAUGHT`) + r2 heal-door ×2 (+ the reference-red (i)/(ii)) | KILLED (two independent pins) |
| WD4 packer keeps the retired statement bound (`min(cap, 5000)`) | wb · PACK set (r2_scale, convergence, r2_am2, r3_probes, heal class, r4_state) | `8 failed, 89 passed` · 1 (6 pytest-timeouts in this run — host loaded by ~7 concurrent runs) | L3 + convergence `2fit+1` ×5 (+ two r4_state legs also red on the loaded host — see §LOAD) | KILLED (L3, the ruled leg) |

## MISSING PINS (each: the test that should exist · the defect it catches · CLASS / CHOKEPOINT / SIBLINGS; bucket for the sidecar)
### MP-1 (WD17) — the hub refusal's served facts are unpinned; the reference itself omits them · bucket **NEW PROPERTY** (am-15 §1.2 rider never pinned)
- **Surviving build:** WD17 serves `…it would compose 7 rows, over the 3-row cap — refused, nothing changed. A smaller supersede will succeed.` — false rows, false cap, and the promise am-15 §1.2 forbids ("It does not say a smaller supersede succeeds (§1.3)" — near the cap a smaller supersede TIMES OUT). `59 passed`. The reference serves no row count and no row cap at all and passes too.
- **Rider dropped:** am-15 §1.2 "cap+1 is refused … with the ledger's teaching error; **the row count the refusal serves == `fragment_rows` of the fragments it built**"; §6 item 1 "served row count == `fragment_rows` of the built fragments"; BC-r5-4. r5 §FOLD item 1 is marked DONE, but `test_one_past_the_cap_is_REFUSED_byte_inert_and_TEACHES` asserts only `old`, `str(cap+1)`, `str(cap)`, "nothing changed".
- **The test that should exist:** in the cap+1 leg (both K), the refusal carries the derived facts as TYPED attributes (or plain integers parsed from fixed slots) and they EQUAL derived values: `rows == fixed(K) + per·(cap+1)` measured off the compose spy at N=1,2,3 (the `_derive` the class already has), `row_cap == _txn.TXN_ROW_HARD_CAP` (the shrunk 5 000), `dependents == cap+1`, `cap == max_reanchor_dependents(K)`; and the text makes no claim that a smaller supersede succeeds (assert on a typed carrier, not a phrase, so it cannot be re-spelled — e.g. the refusal exposes `rows`, `row_cap`, `dependents`, `cap_dependents` and its message is rendered FROM them).
- **CLASS:** a served teaching refusal states only derived facts, each equal to the computation that produced it (trust doctrine: a served count describes the set its label claims). **CHOKEPOINT:** the one raise site of `HubSupersedeRefusedError` in `supersede_task` (rendered from the same `fragment_rows` call the accessor uses). **SIBLINGS TRIED:** wrong rows + wrong cap + false promise (WD17, survives); omitted rows/cap (the reference, survives). **NOT TRIED:** `StragglerHealPackerError`'s "names the row and its weight" — the reference's text says "statements"/"statement transaction cap" (R-3); same class, its weight check is numeric in the convergence twin (r5 R5-D7), not re-attacked.

### MP-2 (WD16B) — "decided before compose" is pinned on `__cause__` only · bucket **PINNED PROPERTY, NEW CASE** (chokepoint: the ledger's pre-check)
- **Surviving build:** WD16B drops the pre-check; compose raises `TxnRowCapExceededError`; the ledger catches it and raises `HubSupersedeRefusedError(…)` with a plain `raise` (no `from`) → `__cause__` None, `__context__` the compose error. `59 passed`; landed per probe. The pin's own message names this build ("the ledger re-wrapped compose()'s row-cap refusal") — a failure message that promises a check the assertion does not perform (CLAUDE.md, the P2 2026-07-14 false-gate class).
- **What a user sees differently:** the same refusal text and a byte-inert store; the difference is that the decision is compose's (the shared cap) instead of the ledger's derived cap, and the cycle/read pre-checks run on the over-cap hub first (a hub that also closes a cycle gets the cycle refusal). Low visibility — I tag it a NEW CASE, not a new property; the sidecar may bucket it NO ROUND.
- **The test that should exist (cheap, behaviour not spelling):** in the same cap+1 leg, a `compose` spy (the class already has one) records that NO compose call was made for the over-cap supersede — the outcome form r5's own A-9 proposal named ("`compose` was never asked to build the over-cap transaction (spy)") and §FOLD dropped. Equivalent minimal patch: walk `__cause__ or __context__` (the chain), not `__cause__`.
- **CLASS:** a ledger-level bound is enforced before the shared one fires. **SIBLINGS TRIED:** no pre-check (WD16, killed by the type check), `raise … from` (r5 X8, killed by `__cause__`), plain raise (WD16B, survives). **NOT TRIED:** `raise … from None` (sets `__suppress_context__`; the chain-walk fix covers it, the spy fix covers all three).

### MP-3 (WD9) — the four markers' kind guard is unpinned: 63c's typed-kind pin hand-lists omit them · bucket **PINNED PROPERTY, NEW CASE** · **REPEAT CLASS** (r5 §FLAGS F-4: "MORE closed 63c exact-set pins than fold item 7 named")
- **Surviving build:** WD9 matches the four markers by the anchored prefix for ANY kind (drops `untyped or kind == THROWN` for 58's markers only; the governed marker keeps it). `1132 passed` over r5_rows + the four 63c files. Landed per probe: typed `Query`/`NotFound` errors led by `An error occurred: claim_lost:` → *claim lost* (reference: unspecified).
- **Why it matters:** am-15 §4.1 / BC-r5-5 rule the guard; a misclassified typed non-THROW error becomes `TxnClaimLostError` (`claim_task` swallows it as a routine loss — the #102 "fault reported as a lost race" shape) and is `proven_no_key` TRUE on the mint path.
- **The test that should exist:** `test_fixwave_a28c_63c_i_a.py::…::test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch` with `_HOSTILE_TEXTS` and `text_labels` grown by DERIVATION from `_txn` (r5's own `fifty_eight_thrown_markers()` / constructed labels, as §DUAL-63c did for `hosted` and `_ECHO_HOSTS`): one hostile text `An error occurred: <marker>t:1` per 58 marker, and the four labels in `text_labels`. GREEN on the reference (the guard is there), RED on WD9.
- **CLASS:** every 63c exact set keyed on `_txn`'s labels/markers must contain 58's members — the lead should restate fold item 7 as "every 63c pin whose domain is `_txn`'s labels or markers grows by derivation", not add this one case. **CHOKEPOINT:** `_classify_engine_error`'s kind guard. **SIBLINGS TRIED:** substring (WD8, killed ×112), heal marker dropped (X7B, killed), kind-blind prefix (WD9, survives). **NOT TRIED:** other hand-listed 63c sets in `test_fixwave_a28b_63c_i_a.py` / `test_sdk3_txn_classification.py` (not swept — a sweep for `_txn` label/marker hand-lists in 63c files is the class fix's first step).

### MP-4 (WD15D) — the un-annotated rider is pinned only at 3 dependents (small-N) · bucket **PINNED PROPERTY, NEW CASE** (chokepoint: `_relate_fragment` / every 58 fragment builder)
- **Surviving build:** WD15D declares `rows=1` on any RELATE fragment over 1 500 statements. `91 passed` over supersede_reanchor_58 (all), r2_scale (L3), r5_rows, r2_probes, sdk3_row_bound. Landed per probe: at 3 400 dependents the supersede composes 10 205 statements but `fragment_rows` = 6 806, so the house WARN (`row_count > 10 000`) — **am-15 §1.3's ruled re-open trigger for the accepted timeout band** — never fires before ~5 000 dependents, and `compose`'s bound under-counts by a third. WD15C (threshold 1 000) died only because L3's single chunk happens to hold 1 251 pairs.
- **The test that should exist:** assert `spy.annotated_calls() == []` inside the two REAL-SIZE legs that already install a spy or can — L2 (1 666 dependents) and L3 (1 251-row heal) — i.e. the un-annotated property ∀ sizes the contract already builds, not only at 3. Zero new fixtures.
- **CLASS:** 58's fragments are un-annotated at every size (am-15 §2 rider, ∀ transactions). **SIBLINGS TRIED:** annotate all (WD15, killed), > 1 000 (WD15C, killed by L3 by size accident), > 1 500 (WD15D, survives). **NOT TRIED:** annotating only the DELETE/guard fragments (one statement each — `rows=1` is not an under-declaration there).


## §LOAD — a run-environment caveat I created and must correct for (2026-11-10 ~00:06Z)
- I ran up to ~8 targeted runs concurrently (each `-n 8`) on one 64-core host and one TEST store. The `wb2` P0 control (`w-NONE`, switch UNSET = the reference + inert switch code) took 25 min and went **8 red**: `test_exhaustion_fates.py::…::test_no_production_handler_element_is_unresolved` (my scaffolding: the switch code's local tuples `_tolerated` / `_heal_isolated` are unresolvable catch elements — an artifact of `wstar_patch.py`, red for EVERY switch value), 2 × 64b-i `findings.py::_run_guarded` (owned by packet-64b-i), and **5 pytest-timeouts (>300 s)**: convergence `…[e1-distinct,e2-distinct,e2-shared,e3-distinct-present-2fit+1]` and r4_state `…[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]`.
- **Consequences for verdicts:** a W-* or WD build's red on any of those 8 ids earns NO kill credit. WD22 / WD22H (heal via `getattr`) were "red" only on exactly those ids (+ the reference-red sweep legs) → **NOT a kill; re-run quietly** (§QUIET). WD4's convergence `2fit+1` reds overlap the timeout set; its kill stands on L3 (not timing-sensitive, asserted on the chunk count).
| WD3B heal packer reads an import-time copy of the cap | wb · PACK set | `29 failed, 68 passed` · 1 (0 timeouts) | convergence ×23 (every shape × scale, mixes, the over-weight row), PR17, PR18r2, PR19, PC, r4_state ×2 — compose's live 5 000 refuses the 50 000-packed chunk (`TxnRowCapExceededError` is NOT a domain rejection, so the boot fails loud) | KILLED |
| **WD12K** heal swallows a store/transport fault (not exhaustion) at chunk ≥ 2 only | wb2 · r4_state, r2_rulings, heal class, forgery sweep, convergence, r3_probes, r2_scale, r2_am2 | `8 failed, 140 passed` · 1 — **every red is baseline**: the 5 load timeouts, 64b-i `_run_guarded`, the reference-red sweep (i)/(ii) (`comm` vs `w-NONE`: only (i)/(ii) differ, and they are red on `ref`) | nothing | **SURVIVES** |
- **WD12K landed (P0 probe `adv58r5b/probe_wd12k_test.py`, run in `wb2` then removed; the 5 000 shrink, fit 1 250, 2 501 one-blocker stragglers, `SurrealConnectionError` injected at the 2nd heal chunk's `_apply`):** reference → `heal_chunks_seen=2 raised=SurrealConnectionError healed=1250` (probe `1 passed` — the fault reaches the boot, am-3 §2); `ADV_WB=WD12K` → `heal_chunks_seen=3 raised=NoneType healed=1251` (probe fails: **the boot completes, 1 250 stragglers stay un-healed, nothing raises**).

### MP-5 (WD12K) — "a store fault at any heal door RAISES" is pinned only on a ONE-chunk heal · bucket **PINNED PROPERTY, NEW CASE** (chokepoint: the heal's per-chunk `except` in `_reanchor_stragglers`)
- **Why no pin sees it:** both store-fault door pins drive a heal of ONE straggler → ONE chunk: r2 `TestAHealStoreFaultIsLOUD._world` (one straggler) and r5.1's straggler world (one straggler). The multi-chunk legs (convergence `2fit+1`, r4 `[ensure_ready -> _reanchor_stragglers]` = Q-HEAL2) inject EXHAUSTION, which WD12K re-raises. The §10.3 class (a heal that swallows its APPLY fault) walks through the door at chunk ≥ 2 — the P1b quantifier attack: the door property is GUARDED by "the first chunk".
- **What a user/the app sees:** a boot that hits a transport blip mid-heal reports success; every straggler in the faulted chunk still names a superseded task, so its dependent stays blocked on a task that can never complete, until some later boot happens to heal it — and the boot's heal INFO under-counts nothing it claims, so nobody is told.
- **The test that should exist:** r2's `test_every_heal_door_after_the_backfill_RAISES[store,transport]` run over a `2·fit+1` world under the 5 000 fixture (it already derives its doors from a control boot and faults each k in turn) — every derived door, including the 2nd and 3rd chunk applies, must raise and write nothing more. One fixture change; the door derivation is already ∀ k.
- **CLASS:** a heal door's loudness ∀ chunks (the ∀-writes rule BC-r4-3(a) states for exhaustion, applied to store faults). **SIBLINGS TRIED:** swallow at every chunk (WD12, killed by r2), swallow the READ (WD13, killed), swallow at chunk ≥ 2 (WD12K, survives). **NOT TRIED:** swallow only `SurrealOutcomeUnknownError` (the SDK3 `SurrealConnectionError` subclass) at chunk ≥ 2 — same door, a narrower catch.

## P1b — QUANTIFIER TABLE (r5/r5.1's NEW or re-keyed invariants)
| # | invariant | ∀ or GUARDED | receipt |
|---|---|---|---|
| Q1 | no statement bound survives in the ACCESSOR | ∀ over hidden bounds < the real cap (L1 is exact arithmetic at 50 000, K∈{0,2}) | WD1 (5 000) killed by L1+L2; WD1H (10 000) killed by L1 alone |
| Q2 | no statement bound survives in the PACKER | **GUARDED by L3's size** (one 5 004-row chunk): a packer bound in (5 004, 50 000) is not killed | WD4 (5 000) killed by L3. Not built: a packer `min(cap, 10_000)` — r5 §FORALL names this bound; consequence is MORE chunks, each atomic, the heal still converges → residual R-1, not a missing pin |
| Q3 | the cap is read LIVE | ∀ over the consumers the fixture legs reach (accessor, packer, WARN) | WD2, WD3 (accessor) killed ×16; WD3B (packer) killed ×29; WD7A (warn) killed |
| Q4 | the hub refusal is decided BEFORE compose | **GUARDED by the `__cause__` spelling** of the rewrap | WD16 killed; **WD16B survives** → MP-2 |
| Q5 | the refusal is byte-inert | ∀ K in r2's set | WD14 killed ×8 |
| Q6 | the refusal serves only derived facts | **NOT PINNED** (rider dropped) | **WD17 survives; the reference omits the facts** → MP-1 |
| Q7 | the WARN is the house row warn, exactly once | ∀ over the boundary pair | WD7, WD7A, WD7C killed |
| Q8 | 58's fragments are un-annotated | **GUARDED by fixture size** (3 dependents / 3 stragglers) | WD15 killed; WD15C killed only by L3's size; **WD15D survives** → MP-4 |
| Q9 | the four classes: typed + anchored + mapped + proven | ∀ 4 classes for substring / mapping / proven; **the KIND guard is not covered** (63c's typed-kind pin hand-lists omit 58's members) | WD8, X7B, WD19 killed; **WD9 survives** → MP-3 |
| Q10 | heal chunks ≤ cap by weight; one boot heals all | ∀ generated shapes × SCALES under the fixture | WD3B, WD4 killed; WD5 / WD21 pending (§RUNS) |
| Q11 | a store fault at any heal door RAISES | **GUARDED by "one chunk"** (both door fixtures hold one straggler) | WD12, WD13 killed; **WD12K (chunk ≥ 2 only) survives** → MP-5 |
| Q12 | registry node lists own exactly their reds | ∀ registered files (exact both ways at `805a687`) | §WD18 — 547 = 232 + 315, both differences empty |
| Q13 | the straggler world exposes the heal's doors | **UNSATISFIABLE as written** (+1 door) | legs (i)/(ii) RED on the reference → §SAT FINDING |

## P1c — ENFORCEMENT TABLE (legs run: EMPIRICAL wrong builds unless marked "inspection")
| rule | the ONE chokepoint | effect vs proxy | sharing by mutation | spelling-test verdict |
|---|---|---|---|---|
| row cap, live | `_txn.TXN_ROW_HARD_CAP` read in `compose`, the accessor, the packer | effect (fixture shrink moves every consumer) | WD2/WD3/WD3B are the mutations: each consumer reddened on its own | none |
| one row counter | `_txn.fragment_rows` | effect only on un-annotated fragments | **unprovable by behaviour** (am-15 §2 ruled bound) — the cold audit's mutation of `fragment_rows`; NOT run by me (it is assigned to the cold audit, r5 §COLD-AUDIT SET 2) | none |
| hub refusal before compose | `supersede_task`'s pre-check | **PROXY**: `__cause__` attribute, not "compose was never called" | — | the `__cause__` check is an exception-chain spelling; MP-2 proposes the spy (effect) |
| refusal's served facts | the `HubSupersedeRefusedError` raise site | **no pin** | — | MP-1 asks for typed attributes (behaviour), not a phrase |
| WARN via the house function | `SurrealStore._log_transaction_size` | effect (records at the boundary pair) | WD7/WD7A/WD7C: a private copy reds the crossing leg; the cold-audit mutation of the house comparison (BC-r5-2) not run by me | none |
| un-annotated fragments | each 58 fragment builder | effect at the compose spy — **at 3 dependents only** | — | none; MP-4 widens the size |
| four classes | `_classify_engine_error` + `_domain_rejection_error` | effect (real THROW through the ledger's door + echo hosts) | X7B (one marker dropped) reddened r5_rows, r3_tiers and collection of the four 63c files in one run | 63c's hand-listed sets (`_HOSTILE_TEXTS`, `text_labels`, `hosted`, …) are hand-lists in TESTS where `vars(_txn)` derives them — said by am-15 §9.2; MP-3 is a member missing from one |
| heal doors loud | the heal's chunk `except` | effect (fault injection at derived doors) — **one chunk only** | — | none; MP-5 |
| heal reached by name (BC-r4-3(c)) | `ensure_ready` → `_reanchor_stragglers` | the r4_state root derivation reads the same-module call graph — a SPELLING dependency (operator-ruled, r4) | WD22 / WD22H: **unresolved under load** (the leg timed out on the baseline too) — §QUIET | ruled spelling test (r4); not re-graded |
| registry partition per node | `pending_contract_gate.partition_pytest` (`c7f8f1d`) | effect (`--currency --legs pytest`) | not run (gate code is builder-615-1's; brief: grade the lists) | inspection |
| WD5 packer prices every straggler at ONE unit | wb · PACK set | `29 failed, 68 passed` · 1 | the same 29 as WD3B (over-packed chunks → compose's live refusal, loud) | KILLED |
| WD21 heal stops after its first chunk (reports only what it healed) | wb · PACK set | `27 failed, 70 passed` · 1 | convergence (every multi-chunk shape/mix), PR18r2, PR19, PC, … (count == |healable| / "all heal in ONE boot") | KILLED |

## §W-STAR — adversary-58-r3's seven W-* builds, re-anchored onto the r5 reference (am-15 §5 item 3) — instrument `adv58r5b/wstar_patch.py` (pasted in §INSTRUMENTS)
Judged against the `w-NONE` baseline on the same tree (§LOAD): only a red NOT in that baseline counts.
| W-* | tests | count · EXIT | reds beyond baseline | verdict |
|---|---|---|---|---|
| W-TUPLE (resolve swallows via a tuple constant, serves the row) | all 58 files + exhaustion_fates | `8 failed, 325 passed` · 1 | r4 `TestTheFiredLedgerEqualsTheDerivedDomain::…[findings.py::resolve -> findings.py::_transition]` — `exhausted contention was SWALLOWED — the call returned Finding(…)` | KILLED (r4 Q-WRAP) |

## §INDEPENDENCE — what my "reference" is (deviation, said plainly)
- am-15 §5 item 1 asks the adversary to "build its OWN reference on HEAD". I **reconstructed r5's reference md5-exact** (chain + `build_ref_r5.py` v4), rather than writing an independent one, because the brief asks for exactly that reconstruction and the 120-min budget went to wrong builds. Consequence: my SAT receipt is a **second run of the same reference** (a re-measurement of r5's SAT on `805a687`), not an independent reference. Where my wrong builds relied on reference behaviour, each P0 control (switch UNSET on the same tree) shows the reference-side outcome. An independent reference remains UNDONE — say so to the sidecar; it is cheapest at the cold audit, where a real build exists.

## P2 — fixture discrimination verdicts (perturbation in my own runs/probes, each with its reference control)
| fixture | can it tell right from wrong? | receipt |
|---|---|---|
| r5_rows un-annotated pin: 3 dependents + 3 stragglers | **NO, past ~1 000 statements** (small-N) | WD15D survives; probe shows the under-declaration only bites at > 1 500 statements; reference control `fragment_rows == statements` at 1 666 |
| r2 `TestAHealStoreFaultIsLOUD._world`: ONE straggler | **NO, for any chunk > 1** | WD12K survives; probe at `2·fit+1` = 2 501 stragglers: reference raises at chunk 2, WD12K completes silently |
| r5.1 straggler world: ONE straggler | same as above (one chunk); plus its door COUNT is over-specified (§SAT FINDING) | — |
| the 5 000/800 fixture (am-15 §8.1) | YES for import-copies and literals (WD2/WD3/WD3B/WD7A killed); NO for a statement bound by itself — covered by the unpatched L-legs as ruled | WD1 killed by L1+L2 only |
| L3 (1 251 stragglers, one 5 004-row chunk) | YES for a 5 000 packer bound (WD4); NO for a packer bound above 5 004 | r5 §FORALL names it; residual R-1 |
| cap+1 refusal leg (message checks `str(cap+1)`, `str(cap)`, "nothing changed") | NO for the served row facts | WD17 + the reference both pass |

## P5 — can the test doubles fail?
- `ComposeSpy` (support) — its own control `test_CONTROL_the_check_sees_an_annotated_fragment` fires on a `rows=1` fragment (r5); my WD15 confirms the spy sees a real one in production paths. ✔
- The forgery-door sweep's swallow control (iii) wraps the whole heal at runtime and is caught — it can fail (I did not mutate the sweep; r5.1 shows it red at HEAD for the missing heal). It proves the INSTRUMENT, not the build (WD12 was killed by r2's pin while (iii) stayed green on it).
- 63c's `_ECHO_HOSTS` doubles — X7B and WD8 show they redden. ✔
- Not attacked: `_task_fakes.py` (§HELD part 1's fake) — out of the delta.

## P7 — RED honesty (BASE = `805a687` + §HELD; `run-base-red.log`)
- BASE over my declared 119-file set: `435 failed, 7745 passed, 47 skipped` (EXIT=1, no cap kill/timeout). The registry's honesty is graded at PLAIN `805a687` (§WD18: exact both ways, 547/547 over the 34 registered files). The forgery-sweep legs' RED@HEAD reasons (r5.1: "door set … is 4, not the 5", `'TaskLedger' has no attribute '_reanchor_stragglers'`) are right-reason reds at HEAD — but (i)/(ii) stay red on a correct build for a WRONG reason (§SAT FINDING), which a RED@HEAD check cannot see.

## §RESIDUALS (NO ROUND unless a sidecar ruling says otherwise; each with its own verdict)
- **R-1 packer hidden bound above L3's 5 004 rows** — not killed (no fixture reaches it; F19 forbids huge ones). Effect: more heal chunks, each atomic, convergence intact → NO ROUND. Named by r5 §FORALL.
- **R-2 private `len(statements)` counter** — am-15 §2's ruled bound; cold-audit mutation of `fragment_rows`. NO ROUND (by ruling).
- **R-3 the reference's `StragglerHealPackerError` prose says "statements … statement transaction cap"** and r5's PE check accepts `"cap" or "row"` — a builder copying the reference serves the retired unit in a teaching error. Cheap fix in the same pass: the PE check asserts "row" (the convergence twin's numeric weight check already holds). Served prose → I would NOT call it trivia under the trust doctrine; NO ROUND only because the row/weight numbers are pinned elsewhere.
- **R-4 my W-* scaffolding reds `test_exhaustion_fates.py::TestTheResolverFailsClosed::test_no_production_handler_element_is_unresolved`** (local tuples in my switch code) — instrument artifact, not a contract finding; it means any W-* "kill" by that test is discounted (§LOAD).
- **R-5 `more-itertools` not declared** in either `pyproject.toml` at `805a687` (BC-r4-1, owed by the builder; no pin — a declared-dependency check would be a spelling test). Cold-audit item.
- **R-6 A-9's positive control composes a synthetic `TXN_ROW_HARD_CAP + 1`-statement fragment** (r5 D-R5-3), not the ledger's own cap+1 fragments — it proves compose refuses at that size, not that the ledger's built transaction would be refused. NO ROUND (MP-2's spy fix subsumes it).
- **R-7 `str(cap) in message`** substring checks can be satisfied by a different number containing the digits (e.g. `16650` contains `1665`). NO ROUND; MP-1's typed attributes subsume it.

## §INSTRUMENTS — pasted VERBATIM (scratch root `…/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/`; md5 beside each)
Reconstruction inputs are r5's (§TREES, md5-checked). Trees: `ref` = r5's reference; `wb` = ref + wb_patch.py (+ WD16B inline edit below); `wb2` = ref + wstar_patch.py + the W-NOOP-DRIVERS test edit + wb2_extra_patch.py + wb2_extra2_patch.py.

### `wb_patch.py` (md5 `e2d9dbbce49e826972eebca51317ac21`)
```python
#!/usr/bin/env python3
"""adversary-58-r5-2: install ENV-SWITCHED wrong builds into a reference tree (ADV_WB=<id>; unset = reference).
Every edit is an exact-once anchor replacement; aborts (non-zero) on any anchor miss. Usage: wb_patch.py <tree>"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
tasks = root / "loremaster/loremaster/tasks.py"
txn = root / "loremaster/loremaster/store/_txn.py"


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{path.name}: anchor count {count}: {old[:80]!r}"
    path.write_text(text.replace(old, new))


# --- tasks.py: module-level switch + import-time copies (F21 wrong builds)
sub(tasks, "from more_itertools import constrained_batches\n",
    "from more_itertools import constrained_batches\nimport os as _adv_os\n")
sub(tasks, "class StragglerHealPackerError(TaskLedgerError):",
    "_ADV_IMPORT_CAP = _txn_module.TXN_ROW_HARD_CAP  # WD3/WD3b: an import-time copy\n"
    "_ADV_IMPORT_WARN = _txn_module.TXN_ROW_WARN_THRESHOLD  # WD7a\n\n\n"
    "def _adv(wb: str) -> bool:\n    return _adv_os.environ.get('ADV_WB') == wb\n\n\n"
    "class StragglerHealPackerError(TaskLedgerError):")
# accessor
sub(tasks,
    "        fixed = _count(0)\n        per = _count(1) - fixed\n        return (_txn_module.TXN_ROW_HARD_CAP - fixed) // per\n",
    "        fixed = _count(0)\n        per = _count(1) - fixed\n"
    "        if _adv('WD1'):\n            return min((_txn_module.TXN_ROW_HARD_CAP - fixed) // per, (5000 - fixed) // per)\n"
    "        if _adv('WD2'):\n            return (50_000 - fixed) // per\n"
    "        if _adv('WD3'):\n            return (_ADV_IMPORT_CAP - fixed) // per\n"
    "        if _adv('WD1H'):\n            return min((_txn_module.TXN_ROW_HARD_CAP - fixed) // per, (10_000 - fixed) // per)\n"
    "        return (_txn_module.TXN_ROW_HARD_CAP - fixed) // per\n")
sub(tasks, "        deps = [f\"k{index}\" for index in range(successor_blocked_by_count)]\n",
    "        deps = [f\"k{index}\" for index in range(0 if _adv('WD6') else successor_blocked_by_count)]\n")
# refusal: WD16 (no pre-check: compose refuses), WD16B (rewrap compose's refusal with a plain raise),
# WD17 (refusal serves a wrong row count)
sub(tasks, "        cap = self.max_reanchor_dependents(len(dependencies))\n        if len(dependent_ids) > cap:\n",
    "        cap = self.max_reanchor_dependents(len(dependencies))\n"
    "        if _adv('WD17') and len(dependent_ids) > cap:\n"
    "            raise HubSupersedeRefusedError(\n"
    "                f\"task {render_attributed(task_id)} has {len(dependent_ids)} dependents; one \"\n"
    "                f\"supersede re-anchors at most {cap} dependents; it would compose 7 rows, over the 3-row cap \"\n"
    "                f\"— refused, nothing changed. A smaller supersede will succeed.\"\n"
    "            )\n"
    "        if len(dependent_ids) > cap and not (_adv('WD16') or _adv('WD16B')):\n")
# heal packer: WD3b import-time cap, WD4 surviving statement bound, WD5 unit weight
sub(tasks, "        cap = _txn_module.TXN_ROW_HARD_CAP\n        try:\n",
    "        cap = _txn_module.TXN_ROW_HARD_CAP\n"
    "        if _adv('WD3B'):\n            cap = _ADV_IMPORT_CAP\n"
    "        if _adv('WD4'):\n            cap = min(cap, 5000)\n"
    "        if _adv('WD5'):\n            built = [(e[0], e[1], e[2], 1) for e in built]\n"
    "        try:\n")
# heal chunk loop: WD12 swallow APPLY fault, WD21 stop after first chunk
sub(tasks, "            try:\n                await self._apply([f for f in fragments if f.statements])\n            except TxnDomainRejectionError:\n",
    "            if _adv('WD21') and chunk_index > 0:\n                break\n"
    "            try:\n                await self._apply([f for f in fragments if f.statements])\n"
    "            except Exception as _adv_error:\n"
    "                if not isinstance(_adv_error, TxnDomainRejectionError):\n"
    "                    if _adv('WD12'):\n"
    "                        logger.warning('adv.heal.apply.swallowed', extra={'database': self._database})\n"
    "                        continue\n"
    "                    raise\n")
# heal READ: WD13 swallow the straggler read fault
sub(tasks,
    "        rows = self._as_rows(\n            await self._query(\n                f\"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} \"\n                f\"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE\"\n            )\n        )\n",
    "        try:\n"
    "            rows = self._as_rows(\n                await self._query(\n                    f\"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} \"\n                    f\"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE\"\n                )\n            )\n"
    "        except Exception:\n"
    "            if not _adv('WD13'):\n                raise\n"
    "            return\n")
# _apply: WD7 private literal warn; WD7A import-time copy; WD7C double warn
sub(tasks,
    "        SurrealStore._log_transaction_size(\n            sum(len(fragment.statements) for fragment in fragments),\n            len(merged_params),\n            _txn_module.fragment_rows(fragments),\n        )\n",
    "        _adv_rows = _txn_module.fragment_rows(fragments)\n"
    "        _adv_private = 10_000 if _adv('WD7') else _ADV_IMPORT_WARN if _adv('WD7A') else None\n"
    "        if _adv_private is not None:\n"
    "            if _adv_rows > _adv_private:\n"
    "                logger.warning('store.apply.large_transaction', extra={'statement_count': _adv_rows, 'param_count': len(merged_params), 'row_count': _adv_rows})\n"
    "        else:\n"
    "            SurrealStore._log_transaction_size(\n                sum(len(fragment.statements) for fragment in fragments),\n                len(merged_params),\n                _adv_rows,\n            )\n"
    "            if _adv('WD7C') and _adv_rows > _txn_module.TXN_ROW_WARN_THRESHOLD:\n"
    "                logger.warning('task.apply.large_transaction', extra={'row_count': _adv_rows})\n")
# relate fragment: WD15 rows= under-declaration
sub(tasks, "            params[to_param] = RecordID(TASK_TABLE, blocked)\n        return TxnFragment(statements=statements, params=params)\n",
    "            params[to_param] = RecordID(TASK_TABLE, blocked)\n"
    "        if _adv('WD15') and statements:\n            return TxnFragment(statements=statements, params=params, rows=1)\n"
    "        return TxnFragment(statements=statements, params=params)\n")

# --- _txn.py: WD8 substring classifier, WD9 kind-blind prefix, WD19 proven_no_key false for one class
sub(txn, "    if untyped or kind == ErrorKind.THROWN:\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n",
    "    import os as _adv_os\n"
    "    if _adv_os.environ.get('ADV_WB') == 'WD8':\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if marker in lowered:\n                return label\n"
    "    if _adv_os.environ.get('ADV_WB') == 'WD9':\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n"
    "    if untyped or kind == ErrorKind.THROWN:\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n")
sub(txn, "    if isinstance(error, _PROVEN_NO_KEY_CLASSES):\n        return True\n    if not isinstance(error, TxnDomainRejectionError):\n        return False\n",
    "    if isinstance(error, _PROVEN_NO_KEY_CLASSES):\n        return True\n    if not isinstance(error, TxnDomainRejectionError):\n        return False\n"
    "    import os as _adv_os\n"
    "    if _adv_os.environ.get('ADV_WB') == 'WD19' and error.error_class == _ERROR_CLASS_CAS_LOST:\n        return False\n")
print("wrong-build switches installed")
```

### `wstar_patch.py` (md5 `2559ef36041b37e61da2cb75903b6bbf`)
```python
#!/usr/bin/env python3
"""adversary-58-r5-2: adversary-58-r3's seven W-* wrong builds, RE-ANCHORED by hand onto the r5 reference as
ENV switches (ADV_WB=<id>; unset = reference). Shapes from REPORT-adversary-58-r3.md §A (W-TUPLE, W-IMPLICIT,
W-REBIND, W-HEAL2, W-F4-PREFIX, W-F3-ROOT); W-NOOP-DRIVERS is a test-tree file written by wstar_noop.py.
Exact-once anchors; aborts on a miss. Usage: wstar_patch.py <tree>"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
tasks = root / "loremaster/loremaster/tasks.py"
findings = root / "loremaster/loremaster/findings.py"


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{path.name}: anchor count {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


# findings.py — W-TUPLE (resolve swallows via a tuple constant, serves the row), W-IMPLICIT (resolve re-reads
# through a helper and raises a lost-race verdict), W-REBIND (wontfix rebinds the caught name and re-raises it)
sub(findings, "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n",
    "        import os as _adv_os\n"
    "        _wb = _adv_os.environ.get('ADV_WB')\n"
    "        _tolerated = (SurrealStoreError,)\n"
    "        if _wb == 'W-TUPLE':\n"
    "            try:\n                return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n"
    "            except _tolerated:\n                return await self.get(id_or_number)\n"
    "        if _wb == 'W-IMPLICIT':\n"
    "            try:\n                return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n"
    "            except SurrealStoreError:\n                await self._adv_raise_if_already_terminal(id_or_number)\n                raise\n"
    "        return await self._transition(id_or_number, STATUS_RESOLVED, actor, note)\n\n"
    "    async def _adv_raise_if_already_terminal(self, id_or_number: int | str) -> None:\n"
    "        await self.get(id_or_number)\n"
    "        raise IllegalTransitionError(f'finding {id_or_number} is already resolved (lost a race)')\n")
sub(findings, "        return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)\n",
    "        import os as _adv_os\n"
    "        if _adv_os.environ.get('ADV_WB') == 'W-REBIND':\n"
    "            try:\n                return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)\n"
    "            except SurrealStoreError as error:\n"
    "                error = IllegalTransitionError('wontfix lost a concurrent race')  # noqa: PLW2901\n"
    "                raise error\n"
    "        return await self._transition(id_or_number, STATUS_WONTFIX, actor, note)\n")
# tasks.py — W-F3-ROOT (claim loss warned on the ROOT logger)
sub(tasks, "        except TxnClaimLostError:\n            pass  # a routine loss (am-3 §3) — the owner read below decides the verdict\n",
    "        except TxnClaimLostError:\n"
    "            import logging as _adv_logging\n            import os as _adv_os\n"
    "            if _adv_os.environ.get('ADV_WB') == 'W-F3-ROOT':\n"
    "                _adv_logging.warning('task claim lost: %s', task_id)\n")
# tasks.py — W-HEAL2 (chunk >= 2 swallows exhaustion / store faults via a tuple; chunk 0 propagates)
sub(tasks, "            try:\n                await self._apply([f for f in fragments if f.statements])\n            except TxnDomainRejectionError:\n",
    "            import os as _adv_os\n"
    "            _heal_isolated = (TxnDomainRejectionError, SurrealStoreError)\n"
    "            try:\n                await self._apply([f for f in fragments if f.statements])\n"
    "            except _heal_isolated as _adv_error:\n"
    "                if not isinstance(_adv_error, TxnDomainRejectionError) and not (\n"
    "                    _adv_os.environ.get('ADV_WB') == 'W-HEAL2' and chunk_index > 0\n"
    "                ):\n                    raise\n")
# tasks.py — W-F4-PREFIX (heal the resolvable prefix before the first bad entry, and COUNT the row)
sub(tasks, "            if skip:\n                continue\n            final = list(columns)\n",
    "            import os as _adv_os\n"
    "            if skip and _adv_os.environ.get('ADV_WB') == 'W-F4-PREFIX':\n"
    "                _good: list[str] = []\n"
    "                for _old in olds:\n"
    "                    _h, _c = heads[_old]\n"
    "                    if _c or _h not in existing:\n                        break\n"
    "                    _good.append(_old)\n"
    "                if _good:\n                    olds = _good\n                    skip = False\n"
    "            if skip:\n                continue\n            final = list(columns)\n")
print("W-* switches installed")
```

### `wb2_extra_patch.py` (md5 `3625c93f8a5f8f71b77b314a8afc6bf6`)
```python
#!/usr/bin/env python3
"""adversary-58-r5-2: three more delta wrong builds on wb2 (ADV_WB): WD14 refusal AFTER a stamp write; WD15C a
size-conditional rows= under-declaration (only fragments > 1000 statements); X7B the heal-chunk marker dropped
from the classifier (its class left on the unspecified label). Exact-once anchors. Usage: <tree>"""
import sys
from pathlib import Path

root = Path(sys.argv[1])
tasks = root / "loremaster/loremaster/tasks.py"
txn = root / "loremaster/loremaster/store/_txn.py"


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{path.name}: anchor count {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


sub(tasks, "        cap = self.max_reanchor_dependents(len(dependencies))\n        if len(dependent_ids) > cap:\n",
    "        cap = self.max_reanchor_dependents(len(dependencies))\n"
    "        import os as _adv_os\n"
    "        if _adv_os.environ.get('ADV_WB') == 'WD14' and len(dependent_ids) > cap:\n"
    "            await self._query(\n"
    "                f\"UPDATE $adv_x SET {_COL_SUPERSEDED_BY} = 'adv14stamp'\", {'adv_x': RecordID(TASK_TABLE, task_id)}\n"
    "            )\n"
    "        if len(dependent_ids) > cap:\n")
sub(tasks, "            params[to_param] = RecordID(TASK_TABLE, blocked)\n        return TxnFragment(statements=statements, params=params)\n",
    "            params[to_param] = RecordID(TASK_TABLE, blocked)\n"
    "        import os as _adv_os\n"
    "        if _adv_os.environ.get('ADV_WB') == 'WD15C' and len(statements) > 1000:\n"
    "            return TxnFragment(statements=statements, params=params, rows=1)\n"
    "        return TxnFragment(statements=statements, params=params)\n")
sub(txn, "    if untyped or kind == ErrorKind.THROWN:\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n",
    "    if untyped or kind == ErrorKind.THROWN:\n        import os as _adv_os\n"
    "        for marker, label in _THROWN_DOMAIN_MARKERS:\n"
    "            if _adv_os.environ.get('ADV_WB') == 'X7B' and marker == _HEAL_CHUNK_MARKER:\n                continue\n")
print("wb2 extra switches installed")
```

### `wb2_extra2_patch.py` (md5 `c9c4b121b3293939b90b8b75d30a5343`)
```python
#!/usr/bin/env python3
"""adversary-58-r5-2, wb2 round 2: WD22 heal reached through getattr (BC-r4-3(c)); WD22H = WD22 + W-HEAL2's
later-chunk swallow; WD15D rows=1 on RELATE fragments > 1500 statements (between L3's 1251 and L2's 1666)."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
tasks = root / "loremaster/loremaster/tasks.py"


def sub(old: str, new: str) -> None:
    text = tasks.read_text()
    count = text.count(old)
    assert count == 1, f"anchor count {count}: {old[:90]!r}"
    tasks.write_text(text.replace(old, new))


sub("        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
    "        await self._backfill_blocks_edges()\n"
    "        import os as _adv_os\n"
    "        if _adv_os.environ.get('ADV_WB') in ('WD22', 'WD22H'):\n"
    "            _boot_steps = {'heal': '_reanchor_' + 'stragglers'}\n"
    "            await getattr(self, _boot_steps['heal'])()\n"
    "        else:\n"
    "            await self._reanchor_stragglers()\n")
sub("                    _adv_os.environ.get('ADV_WB') == 'W-HEAL2' and chunk_index > 0\n",
    "                    _adv_os.environ.get('ADV_WB') in ('W-HEAL2', 'WD22H') and chunk_index > 0\n")
sub("        if _adv_os.environ.get('ADV_WB') == 'WD15C' and len(statements) > 1000:\n",
    "        if (_adv_os.environ.get('ADV_WB') == 'WD15C' and len(statements) > 1000) or (\n"
    "            _adv_os.environ.get('ADV_WB') == 'WD15D' and len(statements) > 1500\n"
    "        ):\n")
print("wb2 round-2 switches installed")

# WD12K: a heal that swallows a STORE/TRANSPORT fault (not exhaustion) at chunk >= 2 only — the §10.3 class at a
# door no one-straggler fixture reaches.
sub("                    _adv_os.environ.get('ADV_WB') in ('W-HEAL2', 'WD22H') and chunk_index > 0\n                ):\n                    raise\n",
    "                    _adv_os.environ.get('ADV_WB') in ('W-HEAL2', 'WD22H') and chunk_index > 0\n                ) and not (\n"
    "                    _adv_os.environ.get('ADV_WB') == 'WD12K' and chunk_index > 0\n"
    "                    and not isinstance(_adv_error, TxnContentionExhaustedError)\n"
    "                ):\n                    raise\n")
print("WD12K installed")
```

### `run_wb.sh` (md5 `dfae19a98ddec804915294f8d3ebe0d3`)
```bash
#!/usr/bin/env bash
# run_wb.sh <WB-id|NONE> <tag> <pytest targets...> — run targets on the wb tree with ADV_WB set (NONE = unset, the
# P0 control). Logs run-wb-<tag>.log with ADV_WB echoed in the header, as seen by a pytest-time python.
set -uo pipefail
D=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b
WB=$1; TAG=$2; shift 2
if [ "$WB" = NONE ]; then unset ADV_WB; else export ADV_WB=$WB; fi
LOG=$D/run-wb-$TAG.log
cd $D/wb
{ ~/.claude/orchestration/tree_id.sh $D/wb; echo "tag=$TAG ADV_WB=${ADV_WB:-<unset>} $(date -u +%FT%TZ)";
  uv run python -c 'import os, loremaster; print("loremaster.__file__ =", loremaster.__file__, "| ADV_WB seen =", os.environ.get("ADV_WB"))'; } > "$LOG" 2>&1
systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 \
  uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE "$@" >> "$LOG" 2>&1
echo "EXIT=$?" >> "$LOG"
```

### `registry_diff.py` (md5 `bd64ced636b43eecfa327abc728fc842`)
```python
"""adversary-58-r5-2: the registry's red_nodeids (805a687) vs the reds of a plain-805a687 run, both ways, per owner;
plus listed ids absent from --collect-only. Usage: registry_diff.py <junit.xml> <collect.txt> <registry.json>"""
import json
import sys
import xml.etree.ElementTree as ET

junit, collect, registry = sys.argv[1:4]
red = set()
for case in ET.parse(junit).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        path = case.get("file") or case.get("classname", "").replace(".", "/") + ".py"
        cls = case.get("classname", "")
        # rebuild the pytest node id: <path>::[Class::]name
        module = cls.split(".")
        name = case.get("name")
        parts = [p for p in module]
        # find where the module path ends: the last part that starts with "test_" or "_"
        idx = max(i for i, p in enumerate(parts) if p.startswith("test_"))
        node = "/".join(parts[: idx + 1]) + ".py::" + "::".join(parts[idx + 1 :] + [name])
        red.add(node.replace(".py::::", ".py::"))
collected = {line.strip() for line in open(collect) if "::" in line}
reg = json.load(open(registry))
listed_any = set()
for owner, entries in reg.items():
    ids = {i for e in entries for i in (e.get("red_nodeids") or [])}
    files = {e["path"] for e in entries}
    listed_any |= ids
    short = owner.split(" ")[1]
    print(f"[{short}] files={len(files)} listed={len(ids)} listed_not_collected={len(ids - collected)} "
          f"listed_but_GREEN={len((ids & collected) - red)}")
    for i in sorted(ids - collected)[:10]:
        print(f"   NOT-COLLECTED {i}")
    for i in sorted((ids & collected) - red)[:20]:
        print(f"   LISTED-GREEN {i}")
unlisted = sorted(red - listed_any)
print(f"red={len(red)} red_unlisted_anywhere={len(unlisted)} collected={len(collected)}")
for i in unlisted[:60]:
    print(f"   UNLISTED-RED {i}")
```

### `probe_wd9.py` (md5 `f249e70a1b213fa82c71d01aa492c157`)
```python
"""adversary-58-r5-2 P0 probe for WD9: a TYPED non-THROW error whose text starts with the THROW wrapper + a 58 marker.
Reference: unspecified (the kind guard). WD9: classified as the 58 label. Control: the governed twin is unspecified on both."""
import os

import loremaster
from loremaster.store import _txn
from surrealdb import errors as sdk_errors

for kind in ("Query", "NotFound"):
    for marker in (_txn.CLAIM_LOST_MARKER, _txn._GOVERNED_CONFLICT_MARKER):
        error = sdk_errors.parse_query_error({"status": "ERR", "kind": kind, "result": f"An error occurred: {marker}t:1"})
        print(f"ADV_WB={os.environ.get('ADV_WB')} kind={kind} marker={marker!r} -> {_txn._classify_engine_error(error)!r}")
print(loremaster.__file__)
```

### `probe_wd15d.py` (md5 `d1cd83e4a4967ef994aacbb7cdfefbb3`)
```python
"""adversary-58-r5-2 P0 probe: does ADV_WB=WD15D actually under-declare the composed L2-size supersede?
Builds the supersede fragments offline (as max_reanchor_dependents does) and prints rows vs statements."""
import os
import sys
from datetime import UTC, datetime

import loremaster
from loremaster.store import _txn
from loremaster.tasks import TaskLedger

n = int(sys.argv[1])
now = datetime.now(UTC).isoformat()
fragments = TaskLedger._supersede_transaction("x", "y", {}, {}, [], [f"d{i}" for i in range(n)], actor="a", at=now)
statements = sum(len(f.statements) for f in fragments)
print(f"ADV_WB={os.environ.get('ADV_WB')} n={n} statements={statements} fragment_rows={_txn.fragment_rows(fragments)} file={loremaster.__file__}")
```

### `probe_wd16b_test.py` (md5 `5a94058af15135157ee66fafe61eeaaa`)
```python
"""adversary-58-r5-2 P0 probe (scratch only): at cap+1 under the 5 000 shrink, what does the refusal CHAIN to?
WD16B (rewrap with a plain raise) => __context__ is compose's TxnRowCapExceededError and __cause__ is None;
the reference refuses BEFORE compose => no TxnRowCapExceededError anywhere in the chain."""
from __future__ import annotations

import pytest
from _reanchor_58_support import bulk_seed_dependents, create, ledger58, shrunk_row_caps, supersede
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import TaskLedger, TaskLedgerError

__all__ = ["ledger58", "shrunk_row_caps"]


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_probe_the_refusal_chains_to_compose(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    cap = ledger.max_reanchor_dependents(0)
    old = await create(ledger, "the hub")
    await bulk_seed_dependents(ledger, old, cap + 1, tag="advprobe16b")
    with pytest.raises(TaskLedgerError) as caught:
        await supersede(ledger, old)
    error = caught.value
    print(f"PROBE type={type(error).__name__} cause={type(error.__cause__).__name__} context={type(error.__context__).__name__}")
    assert error.__cause__ is None
    assert isinstance(error.__context__, _txn.TxnRowCapExceededError), "the refusal did NOT come from compose"
```

### `probe_wd17_test.py` (md5 `1090c319d157dda95ed7710e347fb7e2`)
```python
"""adversary-58-r5-2 P0 probe (scratch only): at cap+1 under the 5 000 shrink, what does the refusal CHAIN to?
WD16B (rewrap with a plain raise) => __context__ is compose's TxnRowCapExceededError and __cause__ is None;
the reference refuses BEFORE compose => no TxnRowCapExceededError anywhere in the chain."""
from __future__ import annotations

import pytest
from _reanchor_58_support import bulk_seed_dependents, create, ledger58, shrunk_row_caps, supersede
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.tasks import TaskLedger, TaskLedgerError

__all__ = ["ledger58", "shrunk_row_caps"]


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_probe_the_refusal_message(ledger58: tuple[TaskLedger, SurrealEnv]) -> None:
    ledger, _env = ledger58
    cap = ledger.max_reanchor_dependents(0)
    old = await create(ledger, "the hub")
    await bulk_seed_dependents(ledger, old, cap + 1, tag="advprobe17x")
    with pytest.raises(TaskLedgerError) as caught:
        await supersede(ledger, old)
    error = caught.value
    print(f"PROBE message={str(error)!r}")
```

### `probe_wd12k_test.py` (md5 `51cfe440c3496518864ab450eda95dfb`)
```python
"""adversary-58-r5-2 P0 probe (scratch only): a TRANSPORT fault at the SECOND heal chunk's apply.
am-3 §2: a store fault at any heal door RAISES. Reference => ensure_ready raises; WD12K => the boot completes silently."""
from __future__ import annotations

from typing import Any

import pytest
from _reanchor_58_support import (
    bulk_seed_dependents,
    column,
    create,
    ledger58,
    measure_heal_shape,
    new_ledger,
    raw_seed_row,
    shrunk_row_caps,
)
from _surreal_harness import SurrealEnv
from loremaster.store import _txn
from loremaster.store._txn import SurrealConnectionError
from loremaster.tasks import TaskLedger

__all__ = ["ledger58", "shrunk_row_caps"]


@pytest.mark.usefixtures("shrunk_row_caps")
async def test_probe_a_fault_at_heal_chunk_two(ledger58: tuple[TaskLedger, SurrealEnv], monkeypatch: pytest.MonkeyPatch) -> None:
    ledger, env = ledger58
    fixed, per = await measure_heal_shape(ledger, env, "adv12kshape")
    fit = (_txn.TXN_ROW_HARD_CAP - fixed) // per
    head = await create(ledger, "the head")
    legacy = "adv12klegacyblocker0000000000000"
    await raw_seed_row(ledger, legacy, blocked_by=[], superseded_by=head)
    stragglers = await bulk_seed_dependents(ledger, legacy, 2 * fit + 1, tag="adv12k")
    real_apply = TaskLedger._apply
    heal_chunks: list[int] = []

    async def _faulting(self: TaskLedger, fragments: list[Any]) -> None:
        if any("DELETE blocks WHERE in = $hd" in s for f in fragments for s in f.statements):
            heal_chunks.append(len(heal_chunks))
            if len(heal_chunks) == 2:
                raise SurrealConnectionError("adv12k injected transport fault at heal chunk 2")
        await real_apply(self, fragments)

    monkeypatch.setattr(TaskLedger, "_apply", _faulting)
    booted = new_ledger(env)
    raised: BaseException | None = None
    try:
        await booted.ensure_ready()
    except BaseException as error:  # noqa: BLE001 - the probe records what reached the boot
        raised = error
    finally:
        await booted.close()
    healed = sum([await column(ledger, s) == [head] for s in stragglers])
    print(f"PROBE fit={fit} stragglers={len(stragglers)} heal_chunks_seen={len(heal_chunks)} raised={type(raised).__name__} healed={healed}")
    assert len(heal_chunks) >= 2, "non-vacuity: the heal must send at least two chunks"
    assert isinstance(raised, SurrealConnectionError), f"the chunk-2 transport fault did not reach the boot (healed={healed})"
```

### `mutation_proofs.sh` (md5 `6f7322fee7fd374196307d8c76fd5247`)
```bash
#!/usr/bin/env bash
# adversary-58-r5-2 §MUTATION — scripts/mutation_proof.py on the ref tree; declared-RED ids were taken from
# --collect-only (mut_collect.txt) BEFORE this script ran. Each proof restores byte-exact (the tool asserts it).
set -uo pipefail
cd /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/ref
LOG=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/mutation_proofs.log; : > $LOG
run() { echo "=== $1" >> $LOG; shift; uv run python scripts/mutation_proof.py "$@" >> $LOG 2>&1; echo "PROOF_EXIT=$?" >> $LOG; }
PYT="systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -q -p no:cacheprovider --timeout=300 -n 4"
# M1 — L1/L2: a surviving statement bound beside the row bound
run M1-L1L2 --file loremaster/loremaster/tasks.py   --anchor '        return (_txn_module.TXN_ROW_HARD_CAP - fixed) // per'   --replacement '        return min((_txn_module.TXN_ROW_HARD_CAP - fixed) // per, (5000 - fixed) // per)'   --expect-red 'loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[0]'   --expect-red 'loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_the_accessor_equals_the_cap_the_COMPOSED_transaction_implies[2]'   --expect-red 'loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_REAL_CAP_a_supersede_past_the_RETIRED_statement_cap_SUCCEEDS'   -- $PYT loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED
# M2 — fold item 3: a rows= under-declaration on the RELATE fragment
run M2-unannotated --file loremaster/loremaster/tasks.py   --anchor '            params[to_param] = RecordID(TASK_TABLE, blocked)
        return TxnFragment(statements=statements, params=params)'   --replacement '            params[to_param] = RecordID(TASK_TABLE, blocked)
        return TxnFragment(statements=statements, params=params, rows=max(len(statements) - 1, 0) if statements else None)'   --expect-red 'loremaster/tests/test_reanchor_58_r5_rows.py::TestFiftyEightsFragmentsAreUnannotated::test_every_supersede_and_heal_transaction_counts_one_row_per_statement'   -- $PYT loremaster/tests/test_reanchor_58_r5_rows.py
# M3 — fold item 5: the WARN fed a row_count that never crosses (the house function still called)
run M3-warn --file loremaster/loremaster/tasks.py   --anchor '            len(merged_params),
            _txn_module.fragment_rows(fragments),
        )'   --replacement '            len(merged_params),
            0,
        )'   --expect-red 'loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS'   --expect-red 'loremaster/tests/test_reanchor_58_r2_probes.py::test_PR13_CONTROL_the_house_policy_DOES_warn_at_that_size'   -- $PYT loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED::test_crossing_the_WARN_threshold_logs_ONE_warning_and_SUCCEEDS loremaster/tests/test_reanchor_58_r2_probes.py::test_PR13_the_task_WARN_rides_the_ONE_telemetry_policy loremaster/tests/test_reanchor_58_r2_probes.py::test_PR13_CONTROL_the_house_policy_DOES_warn_at_that_size
md5sum loremaster/loremaster/tasks.py >> $LOG
```

### WD16B inline edit to `wb`'s tasks.py (applied by a heredoc python after wb_patch.py; anchor = the `except SurrealConnectionError:` after supersede's `_apply`)
```python
except _txn_module.TxnRowCapExceededError:
    if not _adv("WD16B"):
        raise
    raise HubSupersedeRefusedError(f"task {render_attributed(task_id)} has {len(dependent_ids)} dependents; one supersede re-anchors at most {cap} dependents (the store's transaction bound, derived) — refused, nothing changed.")
```
### W-NOOP-DRIVERS test edit (`wb2/loremaster/tests/test_fixwave_a28c_63c_i_a.py`): each `CAS_SEAM_DRIVERS` value wrapped by `_adv_noop_or(driver)` which returns None when `ADV_WB=W-NOOP-DRIVERS`.
| W-IMPLICIT (resolve re-reads through a helper, raises a lost-race verdict) | r4 `TestTheFiredLedgerEqualsTheDerivedDomain` + r3 cas_seam (scoped) | `4 failed, 32 passed` · 1 | r4 `…[findings.py::resolve -> findings.py::_transition]` — `exhausted contention was REINTERPRETED — the caller received IllegalTransitionError(finding 1 is already resolved (lost a race))` (the other 3 = baseline: 64b-i ×2, the load-timed heal leg) | KILLED (r4 Q-WRAP) |
- **§QUIET (00:36Z):** `run-wb2-q-heal-NONE.log` (switch UNSET = reference, 3 concurrent runs on the host): convergence `…2fit+1` ×10 **passed** (their earlier reds were load timeouts), but r4 `…[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` **timed out again (>300 s) on the reference**. So the heal leg r4 graded (Q-HEAL2 at `2·fit+1`) cannot be shown GREEN on the reference within the 300 s per-test timeout this repo mandates for reference runs. Isolated re-run with `--timeout=1500 --durations=5` launched (`run-wb2-q-heal-long.log`) to separate slow from hung.
| W-REBIND (wontfix rebinds the caught name to a lost-race verdict and re-raises it) | r4 `TestTheFiredLedgerEqualsTheDerivedDomain` + cas_seam (scoped) | `3 failed, 33 passed` · 1 | r4 `…[findings.py::wontfix -> findings.py::_transition]` — `exhausted contention was REINTERPRETED — the caller received IllegalTransitionError(wontfix lost a concurrent race)` (other 2 = 64b-i baseline). **In this run the r4 heal leg `[ensure_ready -> _reanchor_stragglers]` PASSED** (heal untouched) — evidence its reference timeouts were load-induced | KILLED (r4 Q-WRAP) |

## §MUTATION — `scripts/mutation_proof.py`, declared-RED from `--collect-only` (`adv58r5b/mut_collect.txt`, 39 ids, written before the run), diffed both ways (`adv58r5b/mutation_proofs.log`; tree `wb`, ADV_WB UNSET = reference; `loremaster.__file__` in `wb`)
| proof | mutation | declared RED | observed | result |
|---|---|---|---|---|
| M1 (L1/L2, fold item 2) | accessor `return min(row-derived, (5000 − fixed)//per)` | L1[0], L1[2], L2 | `3 failed, 8 passed` — exactly those | `PROOF HELD`, restored byte-exact (md5 `2e57b0a2…`) · PROOF_EXIT=0 |
| M2 (un-annotated, fold item 3) | every non-empty RELATE fragment `rows=1` | `test_every_supersede_and_heal_transaction_counts_one_row_per_statement` | `1 failed, 9 passed` — exactly it | `PROOF HELD`, restored · PROOF_EXIT=0 |
| M3 (WARN, fold item 5) | `_apply` passes `row_count=0` to the ONE house function | the crossing leg, `test_PR13_CONTROL_…` | `2 failed, 1 passed` — exactly those (PR13's stubbed-policy leg stays green, as it should) | `PROOF HELD`, restored · PROOF_EXIT=0 |
- Not proven by me (assigned to the cold audit by r5 §COLD-AUDIT SET): the `fragment_rows` sharing mutation (BC-r5-1) and the house-comparison mutation (BC-r5-2).

## §SAT — the full contract set on the reference (the ONE full-set run; brief: "run the full contract tag set ONCE")
- Run: `adv58r5b/run.sh ref ref-sat` over the 119-file declared set (`declare_set_r5.py` on `ref` + the two gate test files + `test_supersede_render_58.py`); log `adv58r5b/run-ref-sat.log`, junit `run-ref-sat.xml`; header `loremaster.__file__` in `ref`; md5 tasks `3360a9cf…`, `_txn` `8d37d2f4…`.
- Count: **`195 failed, 8412 passed, 47 skipped` in 4028 s, EXIT=1**, no cap kill (it ran under ~8 concurrent runs — §LOAD).
- Every red classified by its own failure message (`adv58r5b/ref-sat-reds.json`):
  | group | n | owner / verdict |
  |---|---|---|
  | `test_findings_*_64b.py`, `test_governed_substrate_64b.py`, `test_mcp_server.py` (28), cas_seam / r4_state `findings.py::_run_guarded` | 188 | **packet-64b-i** (UNBUILT / `title=` / `arm_finding_identity` messages) — owned elsewhere |
  | `test_secret_typing.py::…::test_no_module_outside_the_seam_hand_rolls_the_payload` | 1 | `scripts/probe_hub_txn_58.py` signin hand-roll — **KNOWN** (brief: being fixed by contract-58-r5) |
  | `scripts/test_pending_contract_gate_f6.py::test_615_an_entry_with_no_red_nodeids_owns_NO_pytest_red` | 1 | #615's contract-ahead pin, RED at `805a687` by design; GREEN at `c7f8f1d` (builder-615-1) — not 58 |
  | convergence `…2fit+1` ×2, r4 `…[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` ×1 | 3 | **pytest-timeout under load** — convergence `2fit+1` ×10 GREEN in the quiet `q-heal-NONE` run; the r4 heal leg GREEN in the `q-W-REBIND` run (heal untouched); isolated long-timeout run in flight |
  | `scripts/test_forgery_door_sweep.py::TestTheHealDOORSAreOnTheStragglerPath::test_i_…`, `::test_ii_…` | 2 | **58 — the SAT FINDING (over-fire)** |
- **SAT verdict: 2 attributable reds on the reference** — r5.1's legs (i)/(ii). Everything else in r5/r5.1 is satisfiable on the reference (am-15 §9's 67 63c cells, L1–L4, the fixture legs, the WARN legs, the four-class legs: all GREEN here).

### MP-0 (SAT) — r5.1 legs (i)/(ii) are unsatisfiable on the reference · must be fixed before a builder starts (C-DEF class)
- **The pins as written:** (i) `straggler.control_calls == legacy.control_calls + 1` and `[d.seam_called for d in straggler.doors[:-1]] == [d.seam_called for d in legacy.doors]`; (ii) the same `+ 1` as its non-vacuity gate.
- **On the reference:** legacy 5 doors, straggler 8 — the heal's superseded-row read is door 5 in BOTH worlds; the straggler adds the straggler read (k=6), the head-existence read `resolve_existing_rows` (k=7) and the apply (k=8). All 8 LOUD. A correct build must read the stragglers and resolve their heads before it can apply, so "+1" forbids the graded heal shape.
- **The pins that should exist (am-15 §10.3 (i) as ruled — "include the heal's read and the heal's apply, by name; observed count equals derived count"):** (i) the straggler world's doors are a SUPERSET of the legacy world's (as a prefix, in order) **and** add ≥ 1 write-seam door after them, and `len(doors) == control_calls` (reach checked) — no fixed `+1`; (ii) non-vacuity = "the straggler world has strictly more write-seam doors than the legacy world" (exactly what (iv) already measures), then `all_doors_loud`. Satisfiable on the reference (8 ⊇ 5, write doors 2 vs 1, all loud) and still RED at HEAD (no heal: 4 vs 4).
- **CLASS:** a reach pin keyed on a door COUNT the ruling never fixed (an assumption about an unbuilt shape, never measured on a reference). **CHOKEPOINT:** the sweep's door-derivation comparison in `TestTheHealDOORSAreOnTheStragglerPath`. **SIBLINGS:** (iii) and (iv) are sound on the reference (GREEN); the cited legacy leg `control_calls == 5` (former #614 id) is GREEN on the reference — but it too fixes a COUNT (5) that a heal with one more boot read would break; flag for the same rewrite.
- **§QUIET result (00:45Z):** `run-wb2-q-heal-long.log` (reference, switch UNSET, `--timeout=1500`): r4 `…[tasks.py::ensure_ready -> tasks.py::_reanchor_stragglers]` **`1 passed` in 314.85 s** — SLOW, not hung, and over the 300 s per-test timeout this repo mandates for reference/mutation runs. → **Residual R-8:** that one leg cannot be shown GREEN under the standard reference timeout; every adversary/cold-audit run with `--timeout=300` will see it red for a fixture-cost reason. Cheap fix: a per-test `@pytest.mark.timeout(900)` on it (or a smaller `2·fit+1` via the fixture), named in the test.
| W-NOOP-DRIVERS (every owner driver in a28c's `CAS_SEAM_DRIVERS` becomes a no-op) | r4_state (whole) + cas_seam (scoped) | `5 failed, 36 passed` · 1 | r4 `…[agents.py::register …]`, `…[keeps.py::get_or_create_keyed …]`, `…[floor_calibration/store.py::record_measurement …]` — `WRITES(R, v) measured 0 — the driver's unarmed call sent no write through the armed seam` (other 2 = 64b-i baseline) | KILLED (r4 Q-DRIVEN) |
| W-F3-ROOT (claim loss WARNED on the ROOT logger) | r3_probes `test_PB_an_8_way_claim_race_raises_no_alarm_from_ANY_lore_logger` (scoped) | `1 failed` · 1 | PB (the r4 DUAL widened it to ANY logger name) | KILLED |
| W-F4-PREFIX (heals and COUNTS the resolvable prefix before the first bad entry) | convergence `TestAnUnresolvableRowIsSkippedWHOLE` (scoped; GREEN in the `w-NONE` baseline) | `6 failed, 11 passed` · 1 | exactly the bad-middle / bad-last positions × {phantom, cyclic} — `a row with an unresolvable phantom entry was (half-)healed` (bad-first legs stay green, as they should) | KILLED (r4 Q-F4-ORDER) |

## §QUIET-VERDICTS (am-16 §3, lead directive #20031; 2026-11-10)
| item | quiet run | verdict |
|---|---|---|
| r4 heal leg `[ensure_ready -> _reanchor_stragglers]` slow vs hung | `run-wb2-q-heal-long.log`: reference (switch unset), one test, `--timeout=1500`, 2 other runs on the host → `1 passed` · EXIT=0 · `302.55s call` | **SLOW, not hung — settled.** The leg is GREEN on the reference but needs ~303 s of call time on a near-quiet host, i.e. it cannot pass under the 300 s per-test timeout. Per am-16 §3: it takes §2.5's in-test shrink. |
| W-F3-ROOT | `run-wb2-q-W-F3.log` (scoped to PB) | KILLED (PB: root-logger WARNINGs) |
| W-F4-PREFIX | `run-wb2-q-W-F4.log` (scoped to `TestAnUnresolvableRowIsSkippedWHOLE`) | KILLED ×6 (bad-middle/bad-last × phantom/cyclic) |
| W-NOOP-DRIVERS | `run-wb2-q-W-NOOP.log` (r4_state + cas_seam) | KILLED ×3 (r4 Q-DRIVEN `WRITES(R, v) measured 0`) |
| WD22 heal reached via `getattr(self, '_reanchor_' + 'stragglers')` from a dict (BC-r4-3(c)'s callback-table shape), heal itself correct | `run-wb2-q-long-WD22.log` (r4 heal leg, `--timeout=1500`) → `1 passed` · EXIT=0 (201.66 s) | **GREEN — correct behaviour, so not a finding.** Note for the record: BC-r4-3(c) says such a heal "derives no root and its legs red"; on the reference it is still driven and passes — that constraint over-states the derivation (r4 prose; no effect on any build) |
| WD22H = WD22 + W-HEAL2's later-chunk exhaustion swallow | `run-wb2-q-long-WD22H.log` → `1 failed` · EXIT=1 (158 s): `tasks.py::_reanchor_stragglers: exhausted contention was SWALLOWED — the call returned None instead of raising the injected TxnContentionExhaustedError` | **KILLED (r4 Q-HEAL2)** — the getattr dispatch hides nothing from the runtime injection |
| W-HEAL2 (later heal chunks swallow exhaustion via a tuple; chunk 0 propagates) | `run-wb2-q-long-W-HEAL2.log` (r4 heal leg, `--timeout=1500`) → `1 failed` · EXIT=1 (158 s): `exhausted contention was SWALLOWED` | **KILLED (r4 Q-HEAL2)** |
- **All six am-16 §3 items now have a quiet-run verdict:** WD22 GREEN (correct build), WD22H KILLED, W-HEAL2 KILLED, W-F3-ROOT KILLED, W-F4-PREFIX KILLED, W-NOOP-DRIVERS KILLED; the r4 heal leg is SLOW (302.55 s call), not hung. **No W-* survivor → no STOP for sidecar-58-1.** All seven re-anchored r3 W-* builds die on the r5 reference.

## §STATE (2026-11-10 ~00:50Z, inside the 120-min deadline that ends ~01:27Z)
- Done: all brief items (own set first → §DECLINED diff; the brief's minimum set; REACH P1c; P1b; P2; §MUTATION; §10.2 node lists; SAT; W-* replay; am-16 §3 quiet verdicts).
- NOT TRIED: an independent reference (§INDEPENDENCE — accepted by am-16 §3); the `fragment_rows` and house-comparison sharing mutations (assigned to the cold audit); X13 (58 tier dropped from `_ROLLBACK_LOG_TIERS` — r3 property, not delta); WD20 (WARN only on one path — both paths go through `_apply`, so not a distinct door); MP-3's sibling sweep over other 63c hand-lists (am-16 §4 owns it).
- Scratch trees intact for the r5.2 replay (am-16 §5): `adv58r5b/{base,ref,wb,wb2,plain}`; switches documented in §INSTRUMENTS; `wb`/`wb2` md5s recorded. Standing by per lead directive #20031.

# §REPLAY — the r5.2 re-grade (am-16 §5 items 1–4; lead directive #20036; graded commit `1292287`)
- **Scope (exhaustive, as ruled):** (1) SAT of r5.2's new/rewritten legs on r5.2's reference; (2) replay WD17, WD16B, WD9, WD15D, WD12K, each against the pin am-16 §2 names; (3) the §3 builds on a quiet host + the author's flag (4): W-HEAL2 and WD22H on the SHRUNK r4 heal leg; (4) the §4 grown sets against WD8 / WD9 / X7B; plus the lead's three deviation checks. No new enumeration, no new P1b rows.
- **Trees (2026-11-10 ~01:40Z):** `adv58r5b/ref52` and `adv58r5b/wb52`, each `scratch_copy.sh` of the main tree at `1292287` (clean), + §HELD 1/3/4 + `build_ref_r5.py` v4 + `my_ref_r5.py` (md5 `b54d8d75…` = r5.2's recorded, extracted by heading) → `tasks.py 401fb950…`, `_txn.py 8d37d2f4…` = r5.2's recorded REF md5s. `wb52` += `wb52_patch.py` (pasted below) → `tasks.py 89c5556b…`, `_txn.py 0a5d5b5c…`. Host: at most 2 concurrent runs (the §LOAD lesson).
- **Replay-shape notes (my reading, written before the runs):** WD17 cannot append text to the ruled render any more (the error renders itself), so it is replayed as its two halves: **WD17** = false typed facts (`rows=7, row_cap=3`), **WD17P** = true facts + `args` overwritten with the sentence + " A smaller supersede will succeed.". WD16B = no pre-check + compose's refusal re-raised as a correctly-typed `HubSupersedeRefusedError` with a plain `raise`. Deviation (3)'s wrong build = **WD23** (the heal builds chunks and never applies — what deleted leg (iv)'s write-door comparison killed). Deviation (2)'s = **WD13** (heal swallows its READ fault, the neighbour of the SWALLOWS control). Deviation (1) is exercised by WD12K itself (fit 4 → 9 stragglers / 3 chunks).

### §REPLAY instruments (verbatim)

#### `wb52_patch.py` (md5 `f436160d44fc9ef28b3db07bae20ece6`)
```python
#!/usr/bin/env python3
"""adversary-58-r5-2 r5.2 REPLAY: env-switched wrong builds (ADV_WB) on r5.2's reference (tasks 401fb950, _txn 8d37d2f4).
Replays (am-16 §5 item 2/3/4): WD17 (false typed facts), WD17P (true facts + appended promise), WD16B (rewrap compose's
refusal with a plain raise), WD9 / WD8 / X7B (classifier), WD15D (rows=1 on RELATE > 1500), WD12K (swallow a non-exhaustion
store fault at chunk >= 2), W-HEAL2 (swallow exhaustion/store at chunk >= 2), WD22H (getattr dispatch + W-HEAL2);
deviation checks: WD23 (heal never applies — what deleted leg (iv) killed), WD13 (heal swallows its READ — the SWALLOWS
control's neighbour). Unset = the reference. Exact-once anchors; aborts on a miss."""
import sys
from pathlib import Path

root = Path(sys.argv[1])
tasks = root / "loremaster/loremaster/tasks.py"
txn = root / "loremaster/loremaster/store/_txn.py"


def sub(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{path.name}: anchor count {count}: {old[:90]!r}"
    path.write_text(text.replace(old, new))


sub(tasks, "from more_itertools import constrained_batches\n",
    "from more_itertools import constrained_batches\nimport os as _adv_os\n")
sub(tasks, "class StragglerHealPackerError(TaskLedgerError):",
    "def _adv(wb: str) -> bool:\n    return _adv_os.environ.get('ADV_WB') == wb\n\n\nclass StragglerHealPackerError(TaskLedgerError):")
# refusal: WD17 false facts; WD17P an appended promise; WD16B no pre-check (compose refuses, re-wrapped below)
sub(tasks,
    "        if len(dependent_ids) > cap:\n            raise HubSupersedeRefusedError(\n                task_id=task_id,\n"
    "                dependents=len(dependent_ids),\n                rows=self._supersede_rows(len(dependencies), len(dependent_ids)),\n"
    "                row_cap=_txn_module.TXN_ROW_HARD_CAP,\n                cap_dependents=cap,\n            )\n",
    "        if len(dependent_ids) > cap and _adv('WD17'):\n"
    "            raise HubSupersedeRefusedError(task_id=task_id, dependents=len(dependent_ids), rows=7, row_cap=3, cap_dependents=cap)\n"
    "        if len(dependent_ids) > cap and _adv('WD17P'):\n"
    "            _adv_e = HubSupersedeRefusedError(task_id=task_id, dependents=len(dependent_ids),\n"
    "                rows=self._supersede_rows(len(dependencies), len(dependent_ids)), row_cap=_txn_module.TXN_ROW_HARD_CAP, cap_dependents=cap)\n"
    "            _adv_e.args = (str(_adv_e) + ' A smaller supersede will succeed.',)\n"
    "            raise _adv_e\n"
    "        if len(dependent_ids) > cap and not _adv('WD16B'):\n            raise HubSupersedeRefusedError(\n                task_id=task_id,\n"
    "                dependents=len(dependent_ids),\n                rows=self._supersede_rows(len(dependencies), len(dependent_ids)),\n"
    "                row_cap=_txn_module.TXN_ROW_HARD_CAP,\n                cap_dependents=cap,\n            )\n")
sub(tasks, "                    actor=created_by, at=now.isoformat(),\n                )\n            )\n        except SurrealConnectionError:\n",
    "                    actor=created_by, at=now.isoformat(),\n                )\n            )\n"
    "        except _txn_module.TxnRowCapExceededError:\n"
    "            if not _adv('WD16B'):\n                raise\n"
    "            raise HubSupersedeRefusedError(task_id=task_id, dependents=len(dependent_ids),\n"
    "                rows=self._supersede_rows(len(dependencies), len(dependent_ids)), row_cap=_txn_module.TXN_ROW_HARD_CAP, cap_dependents=cap)\n"
    "        except SurrealConnectionError:\n")
# WD15D: size-conditional rows= under-declaration on RELATE fragments
sub(tasks, "            params[to_param] = RecordID(TASK_TABLE, blocked)\n        return TxnFragment(statements=statements, params=params)\n",
    "            params[to_param] = RecordID(TASK_TABLE, blocked)\n"
    "        if _adv('WD15D') and len(statements) > 1500:\n            return TxnFragment(statements=statements, params=params, rows=1)\n"
    "        return TxnFragment(statements=statements, params=params)\n")
# heal chunk loop: WD23 never applies; W-HEAL2 / WD22H swallow exhaustion + store at chunk >= 2; WD12K swallow non-exhaustion at chunk >= 2
sub(tasks, "            try:\n                await self._apply([f for f in fragments if f.statements])\n            except TxnDomainRejectionError:\n",
    "            if _adv('WD23'):\n                continue\n"
    "            try:\n                await self._apply([f for f in fragments if f.statements])\n"
    "            except (TxnDomainRejectionError, SurrealStoreError) as _adv_error:\n"
    "                _later = chunk_index > 0\n"
    "                _swallow = (_later and (_adv('W-HEAL2') or _adv('WD22H'))) or (\n"
    "                    _later and _adv('WD12K') and not isinstance(_adv_error, TxnContentionExhaustedError))\n"
    "                if not isinstance(_adv_error, TxnDomainRejectionError) and not _swallow:\n"
    "                    raise\n")
# WD13: swallow the heal's first READ fault
sub(tasks,
    "        rows = self._as_rows(\n            await self._query(\n                f\"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} \"\n                f\"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE\"\n            )\n        )\n",
    "        try:\n"
    "            rows = self._as_rows(\n                await self._query(\n                    f\"SELECT record::id({_ID_KEY}) AS {_ID_KEY}, {_COL_SUPERSEDED_BY} FROM {TASK_TABLE} \"\n                    f\"WHERE {_COL_SUPERSEDED_BY} IS NOT NONE\"\n                )\n            )\n"
    "        except Exception:\n            if not _adv('WD13'):\n                raise\n            return\n")
# WD22H: heal reached through getattr from a dict
sub(tasks, "        await self._backfill_blocks_edges()\n        await self._reanchor_stragglers()\n",
    "        await self._backfill_blocks_edges()\n"
    "        if _adv('WD22H'):\n            await getattr(self, {'heal': '_reanchor_' + 'stragglers'}['heal'])()\n"
    "        else:\n            await self._reanchor_stragglers()\n")
# _txn: WD8 substring, WD9 kind-blind prefix, X7B heal marker dropped
sub(txn, "    if untyped or kind == ErrorKind.THROWN:\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n",
    "    import os as _adv_os\n    _wb = _adv_os.environ.get('ADV_WB')\n"
    "    if _wb == 'WD8':\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if marker in lowered:\n                return label\n"
    "    if _wb == 'WD9':\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n"
    "    if untyped or kind == ErrorKind.THROWN:\n        for marker, label in _THROWN_DOMAIN_MARKERS:\n"
    "            if _wb == 'X7B' and marker == _HEAL_CHUNK_MARKER:\n                continue\n"
    "            if lowered.startswith(_ENGINE_THROW_PREFIX + marker):\n                return label\n")
print("r5.2 replay switches installed")
```

#### `replay_a.sh` (md5 `313b71e404eda83720bee925184e576e`)
```bash
#!/usr/bin/env bash
# replay_a.sh: SAT of r5.2's new/rewritten legs on ref52 = every test file r5.2 changed (805a687..1292287), whole files.
mapfile -t F < /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/r52_changed_tests.txt
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run.sh /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/ref52 r52-sat "${F[@]}"
```

#### `replay_b.sh` (md5 `a496250a80c73631ad7a4e4d11df88cb`)
```bash
#!/usr/bin/env bash
# replay_b.sh (wb52): switch-UNSET control over every replay target, then each replay scoped to the pin am-16 §2 names.
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh NONE r-NONE loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED loremaster/tests/test_reanchor_58_r2_rulings.py::TestTheHubCapFollowsKAcrossFloorBoundaries loremaster/tests/test_reanchor_58_r2_scale.py loremaster/tests/test_fixwave_a28c_63c_i_a.py loremaster/tests/test_reanchor_58_r5_rows.py loremaster/tests/test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD scripts/test_forgery_door_sweep.py loremaster/tests/test_supersede_reanchor_58.py::TestTheBootHealReanchorsStragglers loremaster/tests/test_reanchor_58_r4_state.py::TestTheFiredLedgerEqualsTheDerivedDomain loremaster/tests/test_reanchor_58_r2_scale.py
for wb in WD17 WD17P WD16B; do /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh $wb r-$wb loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED loremaster/tests/test_reanchor_58_r2_rulings.py::TestTheHubCapFollowsKAcrossFloorBoundaries loremaster/tests/test_reanchor_58_r2_scale.py; done
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh WD15D r-WD15D loremaster/tests/test_supersede_reanchor_58.py::TestTheHubBoundIsDERIVED loremaster/tests/test_reanchor_58_r2_scale.py loremaster/tests/test_reanchor_58_r5_rows.py
for wb in WD9 WD8 X7B; do /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh $wb r-$wb loremaster/tests/test_fixwave_a28c_63c_i_a.py loremaster/tests/test_reanchor_58_r5_rows.py; done
/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh WD12K r-WD12K loremaster/tests/test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD
for wb in W-HEAL2 WD22H; do /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh $wb r-$wb loremaster/tests/test_reanchor_58_r4_state.py::TestTheFiredLedgerEqualsTheDerivedDomain; done
for wb in WD23 WD13; do /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/27ef6c0a-0069-4ed2-8167-9ed0ff6d05f3/scratchpad/adv58r5b/run_wb52.sh $wb r-$wb loremaster/tests/test_reanchor_58_r2_rulings.py::TestAHealStoreFaultIsLOUD scripts/test_forgery_door_sweep.py loremaster/tests/test_supersede_reanchor_58.py::TestTheBootHealReanchorsStragglers; done
```

### §REPLAY results
| run | tree · tests | count · EXIT | reds | verdict |
|---|---|---|---|---|
| P0 control (ADV_WB unset) | wb52 · every replay target (HUB, CLS, DOOR, r4 heal class, r2_scale) | `1 failed, 751 passed` · 1 (129 s; the shrunk r4 heal leg GREEN and fast) | 64b-i `findings.py::_run_guarded` (`report() … 'title'`) only — baseline | the switch tree IS r5.2's reference when unset |
| **WD17** (false typed facts `rows=7, row_cap=3`) | wb52 · HUB | `2 failed, 18 passed` · 1 | the cap+1 leg [0], [2]: `the refusal's typed facts must EQUAL their derivations … served {…'rows': 7, 'row_cap': 3…}, derived {…'rows': 5003…}` | **DIES by am-16 §2.1's pin** |
| **WD17P** (true facts + " A smaller supersede will succeed." appended to the message) | wb52 · HUB | `2 failed, 18 passed` · 1 | the cap+1 leg [0], [2] — the exact ruled-sentence equality | **DIES by am-16 §2.1's exact-text pin** |
| **WD16B** (no pre-check; compose's refusal re-raised, correctly typed, with a plain `raise`) | wb52 · HUB | `2 failed, 18 passed` · 1 | the cap+1 leg [0], [2]: `a transaction over the 5000-row cap reached compose ([5003] rows) … the refusal was compose's` | **DIES by am-16 §2.2's compose-spy pin** (the facts and text were right, so §2.1 alone would not have caught it — the spy is the load-bearing half) |
| **WD15D** (`rows=1` on RELATE fragments > 1 500 statements) | wb52 · TestTheHubBoundIsDERIVED, r2_scale, r5_rows | `3 failed, 21 passed` · 1 | **L2**: `(rows, statements) of transactions whose fragment_rows ≠ statement count at 1666 dependents: [(3338, 5003)]`; + the cap+1 leg ×2 (the served `rows` 3 338 ≠ derived 5 003 — §2.1 catches it independently). L3 stays green: its 1 251-pair chunk is below this build's threshold, as expected | **DIES by am-16 §2.4's L2 pin** (plus §2.1) |
| **WD9** (kind-blind anchored prefix for 58's four markers) | wb52 · a28c + r5_rows | `20 failed, 667 passed` · 1 | a28c `test_am36_1_2_3_a_typed_kind_never_reaches_the_text_branch` ×20 (typed kinds × the 4 derived 58 hostile texts): `a typed 'Configuration' error carrying 'fifty-eight-TxnCasLostError' words was labelled 'cas lost — …' BY ITS TEXT` | **DIES by am-16 §2.3's grown sets** (§5 item 4: the §4 sweep's grown sets vs WD9 — killed) |
| WD8 (substring classifier for the four markers) | wb52 · a28c + r5_rows | `132 failed, 555 passed` · 1 | a28c echo sweep + the grown typed-kind cells + r5_rows (see log) | **DIES** (§5 item 4 vs WD8) |
| X7B (heal-chunk marker dropped from the classifier) | wb52 · a28c + r5_rows | `4 failed, 6 passed, 8 errors` · 1 | a28c collection ERROR (the derived marker set: `exactly ONE marker must classify to TxnHealChunkError's label … found []`) + r5_rows ×4 | **DIES, loudly** (§5 item 4 vs X7B) |
| **WD12K** (swallow a non-exhaustion store fault at chunk ≥ 2) | wb52 · r2 `TestAHealStoreFaultIsLOUD` | `3 failed, 2 passed` · 1 | `test_every_heal_door_after_the_backfill_RAISES[store, transport, outcome_unknown]` — `the completing boot opened 6 doors, expected 4` (the boot ran on past the faulted chunk-2 door; expected = k−1, derived) | **DIES by am-16 §2.5's 9-straggler / 3-chunk pin**, all three fault classes — deviation (1)'s `fixed + 4·per` (fit 4) reading is the shape that exposes chunk 2 and 3 |
