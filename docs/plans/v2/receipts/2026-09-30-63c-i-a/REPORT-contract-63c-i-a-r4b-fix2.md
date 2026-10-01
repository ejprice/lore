# REPORT-contract-63c-i-a-r4b-fix2 — contract fix2 addendum for 63c-i-a (amendment 16 §W 1–5, as amended by 17 and 18)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done — committed on `feat/surreal-unification` over HEAD `62b01c0` (2026-09-25 ~19:40 EDT). SAT on the FINAL bytes (with the twin): U + C `11498 passed, 62 skipped, 3 xfailed`, 0 failed each, full suite ALONE `-n 12`; lint clean on both built trees (no cleanup needed).
- **deviations:** DEV-1 (the verbatim hunks fail `ruff check`) → escalated before landing, ruled (A) by amendment 17 (`d6e8bbc`): lint-clean form landed, AST-equivalent with controls. N-1 (G5's `target` loses the Nmixed kill) → escalated before commit, ruled (b) by amendment 18 (`a8f71cb`): untargeted twin landed. N-2 (amendment 18's "by construction" premise is false under hypothesis's seed rule) → twin landed as ruled, the premise corrected in its docstring as a KNOWN BOUND, and the kill set MEASURED (§REG) — the twin kills every build the old leg killed, Nmixed included.
- **Packages considered:** `hypothesis` 6.168.1 — `target(observation, *, label="")` (read: `inspect.signature` + source of `hypothesis/control.py`) → **replace** (G5, as ruled); `derandomize` seeding (read: `hypothesis/core.py` `Random(int_from_bytes(function_digest(test)))` + `internal/reflection.py::function_digest` / `_clean_source`) → informs N-2, no mechanism specified from it; G6's exhaustive single-character leg → **bespoke** (adversary's verdict, measured by it: sampling scored 0 on `@`; an exhaustive loop over a stated alphabet is not a sampling package's job).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new reusable symbol in the repo (two new test functions, no helpers); scratch instruments pasted §A.
- **Graded:** n/a (author report).
- **decisions-needed:** none open (DEV-1, N-1 ruled). FLAGS for the lead: N-2 (§N-2 — the seed rule makes EVERY derandomized leg's kill set a property of its exact source bytes; the twin's docstring carries the bound + re-open trigger) · candidate door C-1 (§CAND).
- **receipt pointers:** §0 capability · §ITEMS · §VERBATIM + §AST (amendment-17 chain) · §TWIN (amendment-18 cond. 1) · §MUTATION (drivers) · §REG (removed-behaviour table, both legs) · §SAT · §RED · §GATES · §DUAL · §N-2 · §CAND · §A instruments.

## 0. Capability check (brief-base §4) — 2026-09-25
- Idle-gate contract written without denial, under BOTH candidate session ids (the lead's `297217bd-…`, matching the sibling contracts in that directory, and this agent's own scratchpad id `9188504e-…`): `/tmp/claude-idle-gate-lore/<id>-contract-63c-i-a-r4b-fix2.contract` = `{"artifact": "REPORT-contract-63c-i-a-r4b-fix2.md"}`.
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `contract`, cadence `≤20m`). The lead's ledger name is `lead-63c-2` (`team-lead` is not registered there; the first send to it was refused and re-addressed).
- grep/rg hook-blocked (#473; the WORD in a command string trips it — one `grep -c` in a driver draft did, replaced by `awk`): every textual sweep here is `awk` (non-symbol prose seams — the docstring over-claims), said here.
- Store reference `docs/reference/surrealdb-31-capabilities.md`: read the banner and section map. fix2 touches no DDL and no store code — tests + one yaml allowance only.
- The adversary's scratch root survived: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/54ee5b75-304f-4da7-94a9-0d383933e627/scratchpad/inst`; every §A instrument md5-matches `REPORT-adversary-63c-i-a-r4b-fix.md` §A (`my_variants.py` `5bb7ef4a…`, `run_lane.sh` `78e3a7f3…`, `closure_runs.sh` `7ae87e3d…`, `batch_wb.sh` `ce9a2d40…`, `declared.py` `73af36b7…`, `closure_declared.txt` `b56905f7…`, `norm.py` `47ec6298…`, `my_ref_build_r4.py` `3e419c75…`, `my_ref_leg_r4a.py` `0058ae3c…`, `my_ref_leg_r4b.py` `7bf387f2…`, `my_wbs_r4b.py` `2de4368c…`). Copied into this agent's scratch `…/9188504e-…/scratchpad/inst` before use.
- **Slips, disclosed:** (1) one `cp` of two scratch files into `/tmp/` (a stray target in a compound command) and (2) one `sort … > /tmp/.x` — all three files mine, removed at once. (3) One `rm -rf` of a scratch dir was classifier-denied; not retried by any deleting route (a fresh dir name was used). (4) `mixed_probe.py` (a read-only non-pytest python process, hypothesis home redirected into scratch) ran briefly in lane `fixU` while the PRE-twin SAT U was running — that SAT was later discarded (§SAT), so no counted run is affected.

## ITEMS — amendment 16 §W 1–5 (+ amendments 17, 18), what landed where
| # | item | landed (symbols) | grading |
|---|---|---|---|
| 1 | F-A1 fix (12-line block) | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent`, inserted before `stated_integers = …` — lint-clean form (comment re-wrapped; the self-check f-string split at a literal boundary) | §VERBATIM/§AST: AST-equal to §8's block; §MUTATION: correct builds GREEN, PXlie/PX2 RED |
| 1b | non-agent-count bound line | same test's docstring: *"⚠ KNOWN BOUND (adversary-r4b-fix F-A1): the admitted set is the agent-table counts and the result's own counts; a true count of another table (principals, keeps) is refused. RE-OPEN TRIGGER: a correct refusal stating a non-agent count."* + a line naming what `admitted` now carries | prose |
| 2 | G5 `hypothesis.target(float(len(attribution)), label="length")` | `TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language` (the TARGETED leg); `from hypothesis import target` ordered per ruff I001 | §AST; §MUTATION: Nmid RED, Ncap48/64 RED exactly as declared |
| 2b | two narrowed prose lines | `test_comms_schema.py` `_LEGAL_IDENTIFIER_WITNESSES` comment → amendment 16's sentence verbatim (*"the generator's sample space is the language; ``target`` steers the sample up the length axis; the other axes are covered probabilistically at 200 examples"*) + in-place DUAL erratum; the targeted leg's docstring → *"every narrowing conjunct on an axis a draw REACHES"* + in-place DUAL erratum | prose |
| 3 | G6 exhaustive single-character leg | module-level `test_ADV_single_char_neighbourhood_the_predicate_rejects_is_never_looked_up` (appended at the end of `test_agent_registry.py`, as the adversary's function did; its docstring line 2 re-wrapped) | §AST; §MUTATION: Wat/Wplus/Wtab RED (SC), Wspace/Wnl RED (SC + HC) |
| 3b | multi-edit bound line | a `#` comment block directly above the leg (kept outside the adversary's hunk): *"⚠ KNOWN BOUND (amendment 16 G6): multi-character widenings (``@@``, a two-edit neighbour) are outside this leg. RE-OPEN TRIGGER: a widening with a served consequence beyond one registry read — which, by construction of ``register``'s refusal, cannot arise while the shared predicate is the registry's gate."* + the read-budget-only sizing | prose |
| 4 | FXtVE / FXand / FXname bound | `test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists` docstring: the adversary's §8 text, trigger *"a fake found consulting any rule besides ``is_legal_identifier``"*, CLOSURE-IF-REOPENED (UNMEASURED): WIDENING direction in the SHARING pin (FXand); sentinel subclassing `ValueError, TypeError, LookupError` (FXtVE); FXname adversarial-only | prose |
| 4 | RS1combo bound | `test_agent_governance_63c_i_a.py::TestRegisterStampsTheGovernedTriple63cIA::test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched` docstring: the adversary's §8 text + trigger; CLOSURE-IF-REOPENED (UNMEASURED): four single-optional params; **MOOT AT i-b** (amendment-10 C-3 closes the whole 2⁴ lattice; i-b's author deletes the bound deliberately) | prose |
| 5 | delete "whatever the handler spells" | effect-leg docstring; replaced by *"What it OBSERVES, precisely: the shared decision is REACHED and ITS exception propagates."* + in-place DUAL erratum | prose |
| 5 | delete "REACHED and TRUSTED" | `_fake_predicate_import_violations` docstring → *"REACHED and ITS exception propagates"* + in-place DUAL erratum naming FXdisc | prose |
| am.18 | UNTARGETED TWIN | `…::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_UNTARGETED_GENERATED_identity_language`, directly after the targeted leg: 10a33ef's decorators + body byte-exact (`twin_apply.py`, §A), new id, docstring = why two samples + the N-2 KNOWN BOUND | §TWIN; §REG |
| — | `scripts/pending_contracts.yaml` | `packet-63c-i-a-contract-r2` → `test_agent_registry.py` `attr-defined` 7 → 9 (the G6 leg's + the twin's direct `lorerunes.is_legal_identifier` reads, error lines 3150 / 2096 at report time); reason text updated; not a carrier for bounds | §GATES |

## DEVIATION — DEV-1 (ruled (A), amendment 17 `d6e8bbc`)
Measured 2026-09-25 at HEAD `3aa889c`: HEAD's two touched files → `ruff check` `All checks passed!`. With items 1–3 applied BYTE-VERBATIM (the adversary's own `my_variants.py` `Tfix2` / `Tgen_target` / `Tsinglechar`, run against the main checkout; byte-equality §VERBATIM):
```
E501 (112 > 110) test_agent_governance_63c_i_a.py  F-A1 comment line 2
E501 (111 > 110) test_agent_governance_63c_i_a.py  F-A1 comment line 3
E501 (116 > 110) test_agent_governance_63c_i_a.py  F-A1 self-check f-string
I001            test_agent_registry.py             G5: `import lorerunes` before `from hypothesis import target`
E501 (114 > 110) test_agent_registry.py            G6 docstring line 2
Found 5 errors.
```
The adversary's lint claim (its §1) covered its REFERENCE builds, not its scratch-only closure proposals (§4d/§4f report no lint leg). `ruff check` is manifested (`scripts/gates.yaml`); `ruff format` is not (HEAD itself fails `--check`). The brief demanded byte-equality AND SAT "after the lint cleanups" — incompatible here — so I wrote this, messaged, and landed nothing until amendment 17 ruled (A): *"verbatim" = the graded PROGRAM, AST-equivalent under `ast_equiv.py`'s rule with positive controls*. The four rewraps (`lintclean_apply.py`, §A) are the ones proposed then, unchanged.

## VERBATIM + AST — the amendment-17 chain (report hunks ==BYTES== reconstruction ==AST== committed) — amendment 17 condition (1)
**Run 2026-09-25 ~19:35 EDT against the STAGED blobs** (`git show :path`) — the exact blobs this commit records: `test_agent_governance_63c_i_a.py` `093833262ec5…`, `test_agent_registry.py` `4e724a690379…` (`git ls-tree <commit>` shows them; the same blob shas are what lanes `fixU` `8ce9da7` and `fixC` `9cae126` tested — `git rev-parse <lane-commit>:<path>` SAME for all three test files). Reconstruction = the staged file with `lintclean_apply.py --reverse` (asserted anchors) — i.e. the adversary's verbatim bytes + fix2's prose.
```
--- (a) report hunks ==BYTES== reconstruction   (verbatim_proof2.py; hunks extracted from `git show dcc88c6:REPORT-adversary-63c-i-a-r4b-fix.md`)
A.3 pasted my_variants.py md5: 5bb7ef4ad7d1da3645606ad20bc3488a
item1_FA1: 13 lines — byte-substring of test_agent_governance_63c_i_a.py at line 1079 (x1)
item2_G5: 5 lines — byte-substring of test_agent_registry.py at line 2048 (x1)
item3_G6: 19 lines — byte-substring of test_agent_registry.py at line 3137 (x1)
$ diff item1_FA1.report item1_FA1.landed      (empty)
$ diff item2_G5.report item2_G5.landed        (empty)
$ diff item3_G6.report item3_G6.landed        (empty)
--- (b) reconstruction ==AST== staged   (ast_equiv.py)
EQUIVALENT recon/test_agent_governance_63c_i_a.py == staged/test_agent_governance_63c_i_a.py (222051 dump chars)
EQUIVALENT recon/test_agent_registry.py == staged/test_agent_registry.py (339826 dump chars)
--- (b) positive controls, each a one-token mutation of the STAGED copy — every one DIFFERENT
--control  range(128) -> range(127)                                   DIFFERENT at 337780
--mutate   "exhaustive over a STATED alphabet" -> "… GIVEN …"          DIFFERENT (docstring WORDS are not normalised away)
--mutate   "from hypothesis import target" -> "… import given"        DIFFERENT (import sorting hides no NAME change)
--mutate   label="length" -> label="size"                              DIFFERENT
--mutate   "result.backfilled," -> "result.backfilled + 1,"            DIFFERENT (gov)
--mutate   f"{sorted(admitted_counts)}" -> f"{sorted(admitted_counts)}!"  DIFFERENT (gov; the split f-string)
--- control: the STAGED files are NOT byte-verbatim (so the equivalence above is doing work)
item1_FA1 / item2_G5 / item3_G6: NOT a byte-substring (hits=0) each
```
Earlier receipts, kept for the record — the original byte-verbatim landing (~17:40 EDT, before DEV-1), `verbatim_proof.py HEAD`:
```
# the byte-verbatim landing (before DEV-1), verbatim_proof.py HEAD:
A.3 pasted my_variants.py md5: 5bb7ef4ad7d1da3645606ad20bc3488a      (= the report's stated md5 = the script executed)
== item1 F-A1 (§8 block vs gov '+' lines): 13 expected / 13 landed lines -> diff EMPTY
== item2 G5 (target_length new-lines vs reg '+' lines [0:len]): 2 expected / 2 landed lines -> diff EMPTY
== item3 G6 (single_char_leg text vs reg '+' lines [len:]): 21 expected / 21 landed lines -> diff EMPTY
```

## TWIN — amendment 18 condition (1): the twin is the 10a33ef leg, AST-equal (measured 2026-09-25 ~18:34 EDT, working tree)
`twin_equiv.py` (§A): `ast.dump` of the twin's `FunctionDef` vs the leg's at `git show 10a33ef:…`, with the NAME blanked and the leading docstring removed (both required new by the ruling); decorators, signature and body compared.
```
EQUIVALENT — twin vs 10a33ef::test_the_SKIP_gate_agrees_with_the_SHARE… (name+docstring excluded; 2671 dump chars; decorators 2=2; body stmts 5=5)
--mutate "max_examples=200" -> "max_examples=199"                          DIFFERENT
--mutate "        import lorerunes" -> "        import lorerunes, re"        DIFFERENT
--mutate "lookups in ([], [attribution])" -> "lookups in ([],)"            DIFFERENT
--mutate "_the_identity_language)" -> "_text_the_shared_predicate_rejects)"  DIFFERENT
control: the TARGETED leg renamed into the twin's slot                     DIFFERENT
```
**Re-run against the STAGED blob `4e724a690379…` (~19:36 EDT) — identical result:** `EQUIVALENT … (name+docstring excluded; 2671 dump chars; decorators 2=2; body stmts 5=5)`; the four `--mutate` controls and the targeted-leg-in-the-twin's-slot control → `DIFFERENT` each.

## N-2 — amendment 18's "restores the exact pre-fix2 kill set BY CONSTRUCTION" is false; the kills are MEASURED instead
- **Read, not assumed** (installed hypothesis 6.168.1): `hypothesis/core.py` — under `derandomize`, `Random(int_from_bytes(function_digest(test)))`; `internal/reflection.py::function_digest` hashes `_clean_source(inspect.getsource(fn))`, which drops decorators, comments, blank lines and trailing whitespace but KEEPS the `def` line (the NAME) and the docstring, plus `repr(get_signature(fn))`. So a twin with a second id and a new docstring draws a DIFFERENT 200 examples from the leg the adversary graded — as does the targeted leg itself, whose docstring and import order fix2 changed.
- **Consequence:** neither leg's kill set is implied by an earlier measurement of a different source. Both were MEASURED on the landed bytes (§REG), with the twin's entries declared as guesses. Result: the twin kills EVERY build the old untargeted leg killed (Nmixed included) and additionally Nmid.
- **Durable form:** the twin's docstring carries this as a KNOWN BOUND (the seed rule, cited), with RE-OPEN TRIGGER *"any edit to this function's name, docstring or body — re-run the regression table (the adversary-r4b-fix narrowings, declared before the run) over BOTH legs."* The same fact applies to every derandomized hypothesis leg in the repo (the hostile companion too); stated here for the lead, not pinned (scope closed).

## REG — the removed-behaviour table (amendment 18 condition 3), BOTH legs, declared BEFORE the run
Declared 2026-09-25 18:35:49 EDT (`reg3/DECLARED_AT`): per build, fix2's MEASURED targeted-leg set on the landed contract (the pre-twin leg `reg2`, below) ∪ {GLu} wherever the ADVERSARY's untargeted GL killed the build (its `run_wb_*.observed`); GLu entries marked (G) — the twin's seed is its own. Lane `fixU` @ `8ce9da7` (final test bytes + the adversary's reference build, uncollapsed), touched 3 files (639 ids), `-n 8`, `run_lane_fix2.sh`, `loremaster.__file__` inside `fixU` every run. GLt = targeted leg, GLu = untargeted twin, MW = hand-listed accept-control, HC = hostile corpus, SC = single-char leg.
| build (SKIP-gate narrowing) | untargeted r4b-fix contract (adversary, observed) | fix2 pre-twin (`reg2`, `a4ae7c1`) | **fix2 FINAL (`reg3`, `8ce9da7`)** | declared vs observed |
|---|---|---|---|---|
| V0 (correct) | — | — | `639 passed` | 0/0 |
| r4b:G4 (`--`/`__`) | GL | GLt | GLt GLu (`2 failed`) | = |
| N3sep (`---`/`___`) | GL | GLt | GLt GLu | = |
| **Nmixed** (`-` and `_`) | **GL** | **— (`638 passed`, LOST)** | **GLu** (`1 failed`) | = |
| Ndigit | GL MW[00] HC | GLt MW[00] HC | GLt GLu MW[00] HC | = |
| Ntrail | GL MW[a-] MW[a_] HC | + SC | GLt GLu MW[a-] MW[a_] HC SC | = |
| Nsingle | GL MW[a] HC | GLt MW[a] HC | GLt GLu MW[a] HC | = |
| Nlen20 | GL MW[a×64] HC | GLt MW[a×64] HC | GLt GLu MW[a×64] HC | = |
| Ncap48 | MW[a×64] HC | GLt MW[a×64] HC | GLt MW[a×64] HC | = |
| Ncap64 | MW[a×64] HC | GLt MW[a×64] HC | GLt MW[a×64] HC | = |
| Nmid (28–63 chars) | — (survivor) | GLt | GLt **GLu** | **+1 unexpected red: GLu** — the twin's new seed reaches 28–63 chars; a wrong build killed by one more leg; a declaration miss in the SAFE direction, explained by N-2 |
**Union kill set ⊇ the untargeted contract's ∪ G5's gain, every row.** Raw lines (`fix2_reg3.log`): `reg3_Nmixed | 1 failed, 638 passed in 60.67s` · `reg3_V0 | 639 passed in 57.99s` · `reg3_Nmid | 2 failed, 637 passed in 62.30s | declared=1 observed=2 | unexpected-red=1` · all others `unexpected-red=0 declared-but-green=0`, watchdog 0.
**Pre-twin regression leg (`reg2`, declared 17:47:53 EDT — the run that found N-1):** Nmixed `638 passed` (declared-but-green 1); every other row = declared (Ntrail's first diff was a sort-locale artefact in my declared file — `comm` under `LC_ALL=C`; re-sorted: 0/0).
**Mechanism probe** (`mixed_probe.py`, §A — replays the leg's STRATEGY + SETTINGS, not its seed): untargeted → max 46 chars, 4 ≥ 28, 0 at cap, 4 mixed, 10 doubled, 23 trailing; targeted → max 64, 84 ≥ 28, 30 at cap, **0 mixed**, **1 doubled**, 6 trailing.

## MUTATION — the adversary's drivers on the landed bytes (declare-then-diff, both ways)
Declared sets = the adversary's own, written before its runs (`declared.py` `"Tfix2 <WB>"` rows; `closure_declared.txt` via `declared_closure.py`, keyed without the now-landed `T*` prefix). Runner = the adversary's `run_lane.sh` with exactly two changes (`run_lane_fix2.sh`, diff §A): kill-line 12 → 15 GiB (brief), and the launch gate also waits for `spike-surreal.service` = active.
**Pre-twin lanes** (`fixU` `a4ae7c1`, `fixC` `bb34952`; 2026-09-25 17:44–18:20 EDT), `fix2_drivers.log`:
```
fa1_U_V0 [fixU touched: V0] | 638 passed in 62.51s (0:01:02) | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_Vstamped [fixU touched: Vstamped] | 638 passed in 59.10s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_Valready [fixU touched: Valready] | 638 passed in 61.00s (0:01:01) | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_Vb15legacy [fixU touched: Vb15legacy] | 638 passed in 57.97s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_r4b_PXrem15 [fixU touched: r4b:PXrem15] | 638 passed in 58.31s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_r4b_PXlie [fixU touched: r4b:PXlie] | 1 failed, 637 passed in 58.41s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_U_r4b_PX2 [fixU touched: r4b:PX2] | 2 failed, 636 passed in 61.42s (0:01:01) | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
fa1_C_V0 [fixC touched: V0] | 638 passed in 62.75s (0:01:02) | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
g5_U_V0 [fixU reg: V0] | 333 passed in 12.95s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
g5_U_Nmid [fixU reg: Nmid] | 1 failed, 332 passed in 14.71s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
g5_U_Ncap48 [fixU reg: Ncap48] | 3 failed, 330 passed in 17.78s | declared=3 observed=3 | unexpected-red=0 declared-but-green=0 | watchdog=0
g5_U_Ncap64 [fixU reg: Ncap64] | 3 failed, 330 passed in 16.46s | declared=3 observed=3 | unexpected-red=0 declared-but-green=0 | watchdog=0
g6_U_Wat [fixU reg: Wat] | 1 failed, 332 passed in 11.56s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
g6_U_Wplus [fixU reg: Wplus] | 1 failed, 332 passed in 12.46s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
g6_U_Wtab [fixU reg: Wtab] | 1 failed, 332 passed in 11.65s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
g6_U_Wspace [fixU reg: Wspace] | 2 failed, 331 passed in 11.35s | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
g6_U_Wnl [fixU reg: Wnl] | 2 failed, 331 passed in 12.45s | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
```
`loremaster.__file__` = `…/9188504e-…/scratchpad/fixU/loremaster/loremaster/__init__.py` (16 runs) / `…/fixC/…` (1 run). Observed ids: PXlie → `[below-cap]`; PX2 → `[below-cap]`, `[perturbed-bound]`; Nmid → the (targeted) generated leg; Wat → SC.
**Final lanes (with the twin: `fixU` `8ce9da7`, `fixC` `9cae126`; 2026-09-25 18:44–18:57 EDT), `fix2_final.log` — the brief's required set (F-A1: correct variants GREEN, PXlie + PX2 RED; G6: Wat, Wplus, Wtab RED) on the FINAL bytes; G5's Nmid is in §REG (`reg3_Nmid`, final lane):**
```
final_fa1_U_V0 [fixU touched: V0] | 639 passed in 57.36s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_Vstamped [fixU touched: Vstamped] | 639 passed in 57.90s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_Valready [fixU touched: Valready] | 639 passed in 56.04s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_Vb15legacy [fixU touched: Vb15legacy] | 639 passed in 60.49s (0:01:00) | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_r4b_PXrem15 [fixU touched: r4b:PXrem15] | 639 passed in 58.91s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_r4b_PXlie [fixU touched: r4b:PXlie] | 1 failed, 638 passed in 59.14s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_U_r4b_PX2 [fixU touched: r4b:PX2] | 2 failed, 637 passed in 57.97s | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_fa1_C_V0 [fixC touched: V0] | 639 passed in 57.52s | declared=0 observed=0 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_g6_U_Wat [fixU reg: Wat] | 1 failed, 333 passed in 11.38s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_g6_U_Wplus [fixU reg: Wplus] | 1 failed, 333 passed in 11.68s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_g6_U_Wtab [fixU reg: Wtab] | 1 failed, 333 passed in 10.95s | declared=1 observed=1 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_g6_U_Wspace [fixU reg: Wspace] | 2 failed, 332 passed in 11.41s | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
final_g6_U_Wnl [fixU reg: Wnl] | 2 failed, 332 passed in 12.45s | declared=2 observed=2 | unexpected-red=0 declared-but-green=0 | watchdog=0
```
**Every diff EMPTY both ways, pre-twin and final.** `loremaster.__file__` inside the lane on every run (§A.1's assertion).

**Nmixed on the FULL suite — amendment 18 condition (2)** (`fixU` `8ce9da7`, `-n 12`, ALONE, 18:57:39–19:06:24 EDT, 63 GiB at launch, lowest 55; declared = `reg3`'s touched observed, the twin only):
```
FULL_Nmixed | 1 failed, 11497 passed, 62 skipped, 3 xfailed, 7 warnings in 519.15s (0:08:39) | unexpected-red=0 declared-but-green=0
RED: loremaster.tests.test_agent_registry.TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_UNTARGETED_GENERATED_identity_language
```
Nmixed is RED on the full suite, and ONLY the twin kills it — the pre-twin contract's `638 passed` on touched (§REG) plus this single red is the measured case for amendment 18.

## SAT — the FINAL bytes (with the twin), BOTH helper shapes, full suite ALONE `-n 12` (2026-09-25)
Reference = the ADVERSARY'S reference build, run verbatim (`my_ref_build_r4.py` + `my_ref_leg_r4a.py` + `my_ref_leg_r4b.py --prose=shown`, `--collapse` for C; md5s §0), applied on `scratch_copy.sh` lanes of fix2's tree; runner = its `run_lane.sh` (+ the two fix2 changes, §A). Builder item 6 reads *"N = the number of ids actually named, `min(_REFUSAL_ID_SAMPLE_SIZE, count)`"* — `--prose=shown` is exactly that.
| shape | lane @ base | tail (verbatim) | RED | window · memory |
|---|---|---|---|---|
| **U** uncollapsed | `fixU` @ `8ce9da7` | `11498 passed, 62 skipped, 3 xfailed, 7 warnings in 514.72s (0:08:34)` exit 0 | **0** | 19:06:24–19:15:05 EDT · 62 GiB at launch, lowest 55 |
| **C** collapsed | `fixC` @ `9cae126` | `11498 passed, 62 skipped, 3 xfailed, 7 warnings in 524.40s (0:08:44)` exit 0 | **0** | 19:15:05–19:23:56 EDT · 62 GiB at launch, lowest 55 |
11498 = r4b-fix's 11496 + SC + the twin. Launch gate each run: MemAvailable ≥ 23 GiB, no other pytest (comm-anchored awk), `spike-surreal.service` active; PID watchdog at < 15 GiB, 5 s poll, never fired. `loremaster.__file__` = `…/scratchpad/fixU/loremaster/loremaster/__init__.py` / `…/fixC/…`.
**After the lint cleanups:** on both built trees `uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → 0 errors, rc 0 (last legs `typecheck: scripts OK`, `typecheck: shellcheck OK (7 tracked .sh)`). No cleanup was needed, so the SAT above IS the after-lint SAT.
Pre-twin SAT U was STOPPED by PID mid-run (amendment-18 addition: pre-twin SAT does not count); no pre-twin full-suite number is claimed.

## RED — the contract on UNBUILT production, MAIN checkout (fix2's edits only), 3 touched files, `-n 8` (2026-09-25 19:23:56–19:25:06 EDT, `redhead_main.sh` — non-mutating)
`159 failed, 477 passed, 3 errors in 57.11s` (162 reds; `loremaster.__file__` = the main checkout). Diffed by id (`red_diff_fix.py`, the adversary's §A.10, verbatim) against the adversary's RED@HEAD of the r4b-fix contract (`run_redhead.xml`, unbuilt @ `4dca89e`; `git diff --stat 4dca89e HEAD -- loremaster/loremaster lorerunes lorescribe loresigil` EMPTY):
```
r4b ids=637 fix ids=639 | r4b reds=160 fix reds=162
TURNED RED: 0
TURNED GREEN: 0
NEW ids: 2 — red 2, green 0
   red   …::TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_UNTARGETED_GENERATED_identity_language
   red   …test_agent_registry::test_ADV_single_char_neighbourhood_the_predicate_rejects_is_never_looked_up
GONE ids: 0
```
**0 r4b-fix greens turned red.** Both new reds are RED for the right reason: the twin → `AttributeError: module 'lorerunes' has no attribute 'AGENT_NAME_PATTERN'` (its deferred strategy), SC → `AttributeError: … 'is_legal_identifier'` — the not-yet-MOVED symbols the i-a build lands.

## GATES (main checkout, working tree = the bytes to be committed; 2026-09-25 ~18:37 EDT)
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → 25 errors = r4b-fix's 23 + 2 (`test_agent_registry.py` `attr-defined` 9 = `is_legal_identifier` ×6 + `AGENT_NAME_PATTERN` ×3; the new two are the G6 leg's and the twin's oracle reads).
- `pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck RED_ADJUDICATED — 25 residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3` · `ruff GREEN` · pytest NOT_RUN (by design, #466 — never a bare `--currency`).
- **Built world** (lane `fixC` @ `9cae126`, the main checkout's yaml copied in, `cmp` identical, restored after): `typecheck RED_ORPHANED — 11 residual(s)`, **all 11 `SELF-DESTRUCT`** (10 registered files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"), `ruff GREEN` — **11/11 SELF-DESTRUCT (#461)**; with the builder's own yaml edit (the reference build's `bounds: []`) typecheck is 0 errors (above).

## DUAL — every deletion / re-key (all in-place erratum comments present)
| # | site | removed | adjudication |
|---|---|---|---|
| D1 | `test_comms_schema.py` `_LEGAL_IDENTIFIER_WITNESSES` comment | *"every axis of the language (cap, …) is in its sample space by construction"* | dropped-deliberately — amendment 16 G5 erratum (space ≠ sample); in-place DUAL line |
| D2 | targeted leg docstring | *"on an axis of the language, named or not"* | dropped-deliberately — amendment 16 G5; in-place DUAL line |
| D3 | effect-leg docstring | *"and whatever the handler spells"* | dropped-deliberately — amendment 16 (FXtVE falsifies it); in-place DUAL line |
| D4 | `_fake_predicate_import_violations` docstring | *"REACHED and TRUSTED"* | dropped-deliberately — amendment 16 (FXdisc is reached, not trusted); in-place DUAL line |
| D5 | the generated leg's SAMPLE (behaviour, not text) | the untargeted 200-draw sample (its kills: G4, N3sep, **Nmixed**, Ndigit, Ntrail, Nsingle, Nlen20) | preserved-with-pin — amendment 18 (b): the untargeted twin; kills MEASURED (§REG) |
| D6 | `test_R_Q5_1` admitted set | the refusal of a correct reason stating `already_migrated` / `backfilled` / scanned-total counts | dropped-deliberately — amendment 16 §W-1 / adversary F-A1 (SAT); PXlie + PX2 kills preserved (§MUTATION) |
No test id deleted or re-keyed; two ids ADDED (SC, GLu).

## CAND — candidate doors noticed, NOT pinned (scope closed)
- **C-1 (prose, same class as D1/D2):** the `test_agent_registry.py` section-header comment above `_LookupCountingRegistry` still ends *"… so a narrowing conjunct on an axis NO hand-listed witness carries (adversary-r4b G4: doubled separators) is in its sample space."* Literally true of the SPACE, but it reads as a sample claim — the amendment-16 erratum names only D1/D2. Suggested: *"… is reachable by the generator (whether a draw reaches it is measured — §REG of REPORT-contract-63c-i-a-r4b-fix2)"*. Lead's call.
- **C-2 (N-2's generalisation):** every derandomized hypothesis leg's kill set is a property of its exact source bytes; a docstring edit silently re-draws. The twin's docstring carries the bound; the targeted leg's and the hostile companion's do not.

## A. Instruments (pasted VERBATIM, md5 at report time — brief-base §1: scratch is disposable, so every instrument a claim here rests on is below)
Scratch root (disposable): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/9188504e-429e-4d88-96c2-784d25ffe2a0/scratchpad` (`inst/` = the adversary's instruments, copied, md5-checked, plus fix2's). Reused VERBATIM, NOT re-pasted (md5-matched to REPORT-adversary-63c-i-a-r4b-fix.md §A, committed `dcc88c6`): `my_variants.py`, `declared.py`, `closure_declared.txt`, `norm.py`, `red_diff_fix.py`, `run_lane.sh`, and the reference-build legs `my_ref_build_r4.py` / `my_ref_leg_r4a.py` / `my_ref_leg_r4b.py` / `my_wbs_r4b.py`. Superseded and not pasted: `fix2_tail.sh` / `fix2_nmixed_full.sh` (pre-twin chain, stopped by PID — no receipt here rests on them).

### A.1 `run_lane_fix2.sh` — md5 `927954d7071356e00aa8f31bf113036d`
The adversary's `run_lane.sh` (md5 `78e3a7f3e8d23fae29c974d4b4223cdd`) with exactly these changes (`diff run_lane.sh run_lane_fix2.sh`):
```diff
5c5
< # Watchdog kills OUR pytest by PID below 12 GiB. Asserts loremaster.__file__ inside the lane.
---
> # Watchdog kills OUR pytest by PID below 15 GiB (fix2: brief kill-line, was 12). fix2: also waits for spike-surreal active. Asserts loremaster.__file__ inside the lane.
30,31c30,32
<   [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && break
<   [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
---
>   surreal=$(systemctl --user is-active spike-surreal.service)
>   [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && [ "$surreal" = active ] && break
>   [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} spike-surreal=${surreal} after 30 min"; exit 4; }
34c35
< echo "label=$LABEL base=$BASE edits=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | wc -l); avail ${avail} GiB; $(date '+%F %T')"
---
> echo "spike-surreal=$surreal label=$LABEL base=$BASE edits=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | wc -l); avail ${avail} GiB; $(date '+%F %T')"
39c40
<   if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
---
>   if [ "$avail" -lt 15 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
```
Full text:
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b-fix: pytest ALONE on <lane> at <base> (+ edits: my_variants.py names V*/W*, my_wbs_r4b.py names
# prefixed r4b:). Launch gate: MemAvailable >= $MINMEM GiB (23 for -n 12, 20 for -n 8) AND no other pytest process
# (python/pytest/uv comm, bracket-free awk on comm so it cannot self-match); polls 30 min, else exit 4 (blocked).
# Watchdog kills OUR pytest by PID below 15 GiB (fix2: brief kill-line, was 12). fix2: also waits for spike-surreal active. Asserts loremaster.__file__ inside the lane.
# Usage: run_lane.sh <label> <lane-dir> <base> <nproc> <scope: full | touched | gov | reg> [EDIT ...]
set -uo pipefail
INST=$(dirname "$(readlink -f "$0")")
LABEL=$1; LANE=$2; BASE=$3; NPROC=$4; SCOPE=$5; shift 5
MINMEM=${MINMEM:-$([ "$NPROC" -ge 12 ] && echo 23 || echo 20)}
cd "$LANE" || exit 2
git checkout -q -f "$BASE" && git clean -fdq
for E in "$@"; do
  case "$E" in
    r4b:*) uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "${E#r4b:}" >/dev/null || { echo "$E apply failed"; exit 2; } ;;
    *) uv run --no-project python "$INST/my_variants.py" "$LANE" "$E" >/dev/null || { echo "$E apply failed"; exit 2; } ;;
  esac
done
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
case "$SCOPE" in
  full) TARGETS=() ;;
  touched) TARGETS=(loremaster/tests/test_agent_governance_63c_i_a.py loremaster/tests/test_agent_registry.py loremaster/tests/test_comms_schema.py) ;;
  gov) TARGETS=(loremaster/tests/test_agent_governance_63c_i_a.py) ;;
  reg) TARGETS=(loremaster/tests/test_agent_registry.py) ;;
esac
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)$/ && $0 ~ /pytest/{n++} END{print n+0}')
  surreal=$(systemctl --user is-active spike-surreal.service)
  [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && [ "$surreal" = active ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} spike-surreal=${surreal} after 30 min"; exit 4; }
  sleep 20
done
echo "spike-surreal=$surreal label=$LABEL base=$BASE edits=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | wc -l); avail ${avail} GiB; $(date '+%F %T')"
.venv/bin/python -m pytest -n "$NPROC" -q -p no:cacheprovider --junitxml="$INST/run_${LABEL}.xml" "${TARGETS[@]}" > "$INST/run_${LABEL}.log" 2>&1 &
PID=$!; low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 15 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc lowest MemAvailable: ${low} GiB; $(date '+%F %T')"
tail -1 "$INST/run_${LABEL}.log"
.venv/bin/python - "$INST/run_${LABEL}.xml" <<'PY' | sort > "$INST/run_${LABEL}.observed"
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print(f"{case.get('classname','')}::{case.get('name')}")
PY
echo "RED count: $(wc -l < "$INST/run_${LABEL}.observed")"; sed 's/^/RED: /' "$INST/run_${LABEL}.observed" | head -40
git checkout -q -f "$BASE" && git clean -fdq
```

### A.2 `lintclean_apply.py` — md5 `d3352967d651d765fbcc765ccc2730cf`
```python
"""fix2: apply the MINIMAL ruff-check cleanup to the verbatim-landed adversary hunks (E501 x4, I001 x1).
Each edit asserts its anchor occurs exactly once (#194). Usage: python lintclean_apply.py <tests-dir> [--reverse]  (--reverse restores the adversary's verbatim bytes)"""
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])


REVERSE = "--reverse" in sys.argv


def edit(name: str, old: str, new: str) -> None:
    if REVERSE:
        old, new = new, old
    path = ROOT / name
    text = path.read_text()
    assert text.count(old) == 1, f"{name}: anchor occurs {text.count(old)} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
edit(GOV,
     "        # may state — rows ALREADY migrated (scope set; derived from ``before``, where ``SELECT *`` omits a NONE\n"
     "        # column), rows STAMPED (``result.backfilled``, asserted 0 above: the ruling's own \"ZERO stamped\"), and\n"
     "        # the scanned total. None can be the birth value (birth >= 1; the total is count + legacy + already).\n",
     "        # may state — rows ALREADY migrated (scope set; derived from ``before``, where ``SELECT *`` omits a\n"
     "        # NONE column), rows STAMPED (``result.backfilled``, asserted 0 above: the ruling's own \"ZERO\n"
     "        # stamped\"), and the scanned total. None can be the birth value (birth >= 1; the total is count +\n"
     "        # legacy + already).\n")
edit(GOV,
     "            f\"fixture self-check: the birth value {birth_bound} is an admitted TRUE count {sorted(admitted_counts)}\"\n",
     "            f\"fixture self-check: the birth value {birth_bound} is an admitted TRUE count \"\n"
     "            f\"{sorted(admitted_counts)}\"\n")
edit(REG,
     "        import lorerunes\n        from hypothesis import target\n\n        target(",
     "        from hypothesis import target\n\n        import lorerunes\n\n        target(")
edit(REG,
     "    predicate rejects (a{c}b, {c}a, a{c}) is never looked up — exhaustive over a STATED alphabet, derived from the\n"
     "    predicate, no hand-list. POSITIVE CONTROL: the legal neighbours ARE looked up once.\"\"\"\n",
     "    predicate rejects (a{c}b, {c}a, a{c}) is never looked up — exhaustive over a STATED alphabet, derived from\n"
     "    the predicate, no hand-list. POSITIVE CONTROL: the legal neighbours ARE looked up once.\"\"\"\n")
print("lint-clean REVERSED" if REVERSE else "lint-clean applied")
```

### A.3 `ast_equiv.py` — md5 `cf8bd6853ba30b04e8c295ad376fbe5a`
```python
"""fix2: prove two module sources are the SAME PROGRAM modulo (a) comments, (b) docstring whitespace
(runs of whitespace collapsed), (c) the order of a run of consecutive import statements, (d) implicit
string-literal concatenation (the parser already folds it). Prints EQUIVALENT or the first differing dump.
POSITIVE CONTROL: --control mutates one token in B (``range(128)`` -> ``range(127)``) and must print DIFFERENT.
Usage: python ast_equiv.py A.py B.py [--control | --mutate OLD NEW]  (--mutate: OLD must occur exactly once in B)"""
import ast
import re
import sys


class _Normalise(ast.NodeTransformer):
    def _body(self, body: list[ast.stmt]) -> list[ast.stmt]:
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
                and isinstance(body[0].value.value, str):
            body[0].value.value = re.sub(r"\s+", " ", body[0].value.value).strip()
        out: list[ast.stmt] = []
        run: list[ast.stmt] = []
        for stmt in body + [None]:  # type: ignore[list-item]
            if isinstance(stmt, (ast.Import, ast.ImportFrom)):
                run.append(stmt)
                continue
            out.extend(sorted(run, key=ast.dump))
            run = []
            if stmt is not None:
                out.append(stmt)
        return out

    def generic_visit(self, node: ast.AST) -> ast.AST:
        super().generic_visit(node)
        for field in ("body", "orelse", "finalbody"):
            value = getattr(node, field, None)
            if isinstance(value, list) and value and isinstance(value[0], ast.stmt):
                setattr(node, field, self._body(value))
        return node


def dump(source: str) -> str:
    return ast.dump(_Normalise().visit(ast.parse(source)), include_attributes=False)


a_src, b_src = open(sys.argv[1]).read(), open(sys.argv[2]).read()
if "--control" in sys.argv:
    assert b_src.count("range(128)") == 1, "control anchor missing"
    b_src = b_src.replace("range(128)", "range(127)")
if "--mutate" in sys.argv:
    old, new = sys.argv[sys.argv.index("--mutate") + 1: sys.argv.index("--mutate") + 3]
    assert b_src.count(old) == 1, f"mutate anchor occurs {b_src.count(old)} times"
    b_src = b_src.replace(old, new)
da, db = dump(a_src), dump(b_src)
if da == db:
    print(f"EQUIVALENT {sys.argv[1]} == {sys.argv[2]} ({len(da)} dump chars)")
else:
    i = next(k for k in range(min(len(da), len(db))) if da[k] != db[k])
    print(f"DIFFERENT at {i}: A={da[i-80:i+80]!r}\n B={db[i-80:i+80]!r}")
```

### A.4 `verbatim_proof.py` — md5 `0d7b011bd1c395b24fd177b46c2bd91a`
```python
"""fix2 §VERBATIM: extract the adversary's pasted hunks from the COMMITTED report (git show dcc88c6:...) and
compare them byte-for-byte with the '+' lines a working tree adds to <base>. Prints one diff per item; EMPTY
diff = byte-equal. Usage: python verbatim_proof.py <base-sha> [<tests-dir-override>]"""
import ast
import difflib
import subprocess
import sys

BASE = sys.argv[1]
REPORT = subprocess.run(["git", "show", "dcc88c6:REPORT-adversary-63c-i-a-r4b-fix.md"], capture_output=True,
                        text=True, check=True).stdout.splitlines(keepends=True)


def fence_after(marker: str, lang: str) -> list[str]:
    start = next(i for i, line in enumerate(REPORT) if marker in line)
    open_ = next(i for i in range(start, len(REPORT)) if REPORT[i].strip() == f"```{lang}")
    close = next(i for i in range(open_ + 1, len(REPORT)) if REPORT[i].strip() == "```")
    return REPORT[open_ + 1:close]


def added_lines(path: str) -> list[str]:
    diff = subprocess.run(["git", "diff", "-U0", BASE, "--", path], capture_output=True, text=True,
                          check=True).stdout.splitlines(keepends=True)
    return [line[1:] for line in diff if line.startswith("+") and not line.startswith("+++")]


# item 1 — F-A1: the §8 fenced block (indented 2 under its markdown bullet)
fa1 = [line[2:] if line.startswith("  ") else line for line in fence_after("**Minimal fix (test-side", "python")]
# items 2/3 — the §A.3 my_variants.py source; md5 must equal the report's stated md5 AND the executed script
variants_src = "".join(fence_after("### A.3 `my_variants.py`", "python"))
import hashlib
print("A.3 pasted my_variants.py md5:", hashlib.md5(variants_src.encode()).hexdigest())
tree = ast.parse(variants_src)
funcs = {node.name: node for node in tree.body if isinstance(node, ast.FunctionDef)}
g5_call = funcs["target_length"].body[0].value  # edit(REGTEST, old, new)
g5_old, g5_new = (ast.literal_eval(arg) for arg in g5_call.args[1:3])
g5_added = [line + "\n" for line in g5_new.splitlines() if line + "\n" not in g5_old.splitlines(keepends=True)]
g6_write = next(n for n in ast.walk(funcs["single_char_leg"]) if isinstance(n, ast.BinOp) and isinstance(n.right, ast.Constant))
g6_added = ast.literal_eval(g6_write.right).splitlines(keepends=True)

gov = added_lines("loremaster/tests/test_agent_governance_63c_i_a.py")
reg = added_lines("loremaster/tests/test_agent_registry.py")
for label, expected, landed in (
    ("item1 F-A1 (§8 block vs gov '+' lines)", fa1, gov),
    ("item2 G5 (target_length new-lines vs reg '+' lines [0:len])", g5_added, reg[: len(g5_added)]),
    ("item3 G6 (single_char_leg text vs reg '+' lines [len:])", g6_added, reg[len(g5_added):]),
):
    out = "".join(difflib.unified_diff(expected, landed, "adversary", "landed"))
    print(f"== {label}: {len(expected)} expected / {len(landed)} landed lines -> diff {'EMPTY' if not out else 'NON-EMPTY'}")
    print(out, end="")
```

### A.5 `verbatim_proof2.py` — md5 `77f47cfc186b125fb28f414f0aae6964`
```python
"""fix2 §VERBATIM v2: extract the adversary's pasted hunks from the COMMITTED report (git show dcc88c6:...) and check
each is a CONTIGUOUS byte-substring of the given files (prose added by fix2 sits OUTSIDE the hunks); writes the
report-extracted hunk and the file window to <outdir>/<item>.{report,landed} for a plain `diff`.
Usage: python verbatim_proof2.py <gov.py> <reg.py> <outdir>"""
import ast
import hashlib
import subprocess
import sys
from pathlib import Path

gov_path, reg_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
out.mkdir(parents=True, exist_ok=True)
REPORT = subprocess.run(["git", "-C", "/home/ejprice/PycharmProjects/lore", "show",
                         "dcc88c6:REPORT-adversary-63c-i-a-r4b-fix.md"], capture_output=True, text=True,
                        check=True).stdout.splitlines(keepends=True)


def fence_after(marker: str, lang: str) -> list[str]:
    start = next(i for i, line in enumerate(REPORT) if marker in line)
    open_ = next(i for i in range(start, len(REPORT)) if REPORT[i].strip() == f"```{lang}")
    close = next(i for i in range(open_ + 1, len(REPORT)) if REPORT[i].strip() == "```")
    return REPORT[open_ + 1:close]


fa1 = "".join(line[2:] if line.startswith("  ") else line
              for line in fence_after("**Minimal fix (test-side", "python"))
variants_src = "".join(fence_after("### A.3 `my_variants.py`", "python"))
print("A.3 pasted my_variants.py md5:", hashlib.md5(variants_src.encode()).hexdigest())
funcs = {n.name: n for n in ast.parse(variants_src).body if isinstance(n, ast.FunctionDef)}
g5_new = ast.literal_eval(funcs["target_length"].body[0].value.args[2])
g6 = next(n for n in ast.walk(funcs["single_char_leg"]) if isinstance(n, ast.BinOp)
          and isinstance(n.right, ast.Constant))
g6_text = ast.literal_eval(g6.right).lstrip("\n")
for item, expected, path in (("item1_FA1", fa1, gov_path), ("item2_G5", g5_new, reg_path),
                             ("item3_G6", g6_text, reg_path)):
    text = path.read_text()
    (out / f"{item}.report").write_text(expected)
    hits = text.count(expected)
    if hits == 1:
        at = text.index(expected)
        (out / f"{item}.landed").write_text(text[at:at + len(expected)])
        line = text[:at].count("\n") + 1
        print(f"{item}: {len(expected.splitlines())} lines — byte-substring of {path.name} at line {line} (x1)")
    else:
        (out / f"{item}.landed").write_text("")
        print(f"{item}: NOT a byte-substring of {path.name} (hits={hits})")
```

### A.6 `twin_apply.py` — md5 `640b54c30b03005e976418ea944af70e`
```python
"""fix2 (amendment 18, N-1 ruled (b)): insert the UNTARGETED TWIN of the generated leg right after the targeted leg.
Decorators + body are taken BYTE-EXACT from the leg as committed at 10a33ef (git show), so the twin is that graded
program; only the def NAME and the DOCSTRING are new (the ruling requires both). Anchors asserted exactly once.
Usage: python twin_apply.py <repo-root>"""
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
REG = ROOT / "loremaster/tests/test_agent_registry.py"
OLD_NAME = "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language"
NEW_NAME = "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_UNTARGETED_GENERATED_identity_language"
old_src = subprocess.run(["git", "-C", str(ROOT), "show", "10a33ef:loremaster/tests/test_agent_registry.py"],
                         capture_output=True, text=True, check=True).stdout
old_lines = old_src.splitlines(keepends=True)
node = next(n for n in ast.walk(ast.parse(old_src)) if isinstance(n, ast.FunctionDef) and n.name == OLD_NAME)
decorators = "".join(old_lines[node.decorator_list[0].lineno - 1: node.lineno - 1])
signature_end = node.body[0].lineno - 1  # the docstring's first line
body_start = node.body[1].lineno - 1
signature = "".join(old_lines[node.lineno - 1: signature_end]).replace(OLD_NAME, NEW_NAME)
assert signature.count(NEW_NAME) == 1
body = "".join(old_lines[body_start: node.end_lineno])
docstring = '''        """⚠ RED before i-a (the pattern has not MOVED to ``lorerunes``). r4b-fix2 (amendment 18, FINDING N-1
        ruled (b)): the UNTARGETED twin of the targeted leg above — the r4b-fix generated leg (``10a33ef``),
        restored AST-equal under this second id. WHY TWO SAMPLES, so nobody folds them believing one covers
        the other: ``target`` thins the untargeted axes; this leg is the untargeted sample whose kills the
        targeted one measurably loses (adversary-r4b-fix builds re-run on the landed contract: Nmixed, a SKIP
        gate skipping names carrying both ``-`` and ``_``, went from killed to ``638 passed`` under ``target``
        alone). Two samples of one language, two budgets, one oracle: the targeted leg reaches the length axis
        (the cap), this one keeps the untargeted spread. Same property as the leg above — ∀ GENERATED values,
        the gate looks the value up EXACTLY when ``lorerunes.is_legal_identifier`` accepts it, never more
        than once.
        ⚠ KNOWN BOUND (hypothesis 6.168.1 ``derandomize``, read in ``hypothesis/core.py`` +
        ``internal/reflection.py::function_digest``): the seed is derived from this function's cleaned
        SOURCE — its name and this docstring included, comments and decorators excluded — so editing either
        re-draws the 200 examples, and a kill measured on one draw is not guaranteed on the next. The kills
        this leg carries are MEASURED on the bytes that landed (fix2 report, regression table), not implied by
        construction. RE-OPEN TRIGGER: any edit to this function's name, docstring or body — re-run the
        regression table (the adversary-r4b-fix narrowings, declared before the run) over BOTH legs."""
'''
twin = "\n" + decorators + signature + docstring + body
text = REG.read_text()
assert text.count(f"def {NEW_NAME}(") == 0, "twin already present"
anchor = ('            f"witness carries)"\n        )\n\n    @settings(derandomize=True, max_examples=200, database=None, '
          'deadline=None)\n    @given(value=st.deferred(_text_the_shared_predicate_rejects))\n')
assert text.count(anchor) == 1, f"anchor occurs {text.count(anchor)} times"
insert_at = text.index(anchor) + len('            f"witness carries)"\n        )\n')
REG.write_text(text[:insert_at] + twin + text[insert_at:])
print(f"twin inserted: {NEW_NAME}")
```

### A.7 `twin_equiv.py` — md5 `a89351e095fc8085102108e9d18008be`
```python
"""fix2 (amendment 18 condition 1): the untargeted TWIN is AST-equal to the generated leg as committed at 10a33ef,
EXCEPT its name and docstring (both required new by the ruling). Compares ast.dump of the FunctionDef with name
blanked and the leading docstring removed (decorators, signature, body all compared). Controls via --mutate.
Usage: python twin_equiv.py <landed test_agent_registry.py> [--mutate OLD NEW]  (OLD once in the TWIN's source)"""
import ast
import subprocess
import sys

OLD = "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language"
TWIN = "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_UNTARGETED_GENERATED_identity_language"
ref_src = subprocess.run(["git", "-C", "/home/ejprice/PycharmProjects/lore", "show",
                          "10a33ef:loremaster/tests/test_agent_registry.py"], capture_output=True, text=True,
                         check=True).stdout
landed_src = open(sys.argv[1]).read()


def func(src: str, name: str) -> tuple[ast.FunctionDef, str]:
    tree = ast.parse(src)
    hits = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    assert len(hits) == 1, f"{name}: {len(hits)} definitions"
    return hits[0], ast.get_source_segment(src, hits[0]) or ""


if "--mutate" in sys.argv:
    old, new = sys.argv[sys.argv.index("--mutate") + 1: sys.argv.index("--mutate") + 3]
    node, _ = func(landed_src, TWIN)
    lines = landed_src.splitlines(keepends=True)
    start, end = node.decorator_list[0].lineno - 1, node.end_lineno
    segment = "".join(lines[start:end])
    assert segment.count(old) == 1, f"mutate anchor occurs {segment.count(old)} times in the twin"
    landed_src = "".join(lines[:start]) + segment.replace(old, new) + "".join(lines[end:])


def normal(node: ast.FunctionDef) -> str:
    node.name = "_"
    body = node.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
        node.body = body[1:]
    return ast.dump(node, include_attributes=False)


ref, _ = func(ref_src, OLD)
twin, _ = func(landed_src, TWIN)
a, b = normal(ref), normal(twin)
print(("EQUIVALENT" if a == b else "DIFFERENT") + f" — twin vs 10a33ef::{OLD[:40]}… (name+docstring excluded; "
      f"{len(a)} dump chars; decorators {len(ref.decorator_list)}={len(twin.decorator_list)}; body stmts "
      f"{len(ref.body)}={len(twin.body)})")
```

### A.8 `declared_closure.py` — md5 `f18b1b1a5f56c0a4bbbb5e500d915b53`
```python
"""fix2: the adversary's closure_declared.txt (md5 b56905f7…, declared BEFORE its runs) as node ids, keyed WITHOUT the
contract-edit prefix (Tgen_target / Tsinglechar are LANDED in fix2's tree). Usage: python declared_closure.py <WB>"""
import sys
from pathlib import Path

P = "loremaster/tests/test_agent_registry.py::TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::"
IDS = {
    "GL": P + "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language",
    "MW64": P + f"test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[{'a' * 64}]",
    "HC": P + "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus",
    "SC": "loremaster/tests/test_agent_registry.py::"
    "test_ADV_single_char_neighbourhood_the_predicate_rejects_is_never_looked_up",
}
table = {}
for line in Path(__file__).with_name("closure_declared.txt").read_text().splitlines():
    if line.startswith("#") or "->" not in line:
        continue
    left, right = line.split("->")
    key = left.split()[1]
    table[key] = [] if right.strip() == "(none)" else [IDS[t] for t in right.split()]
print("\n".join(sorted(table[sys.argv[1]])))
```

### A.9 `fix2_drivers.sh` — md5 `716ffb6deddca9b9d1b3c7dfc3a358d5`
```bash
#!/usr/bin/env bash
# fix2: re-run the adversary-r4b-fix drivers against fix2's LANDED contract (lanes fixU/fixC = fix2 working tree +
# the adversary's reference build). Same shape as batch_wb.sh / closure_runs.sh, minus the T* contract edits
# (landed). Declared sets are the adversary's own, written before its runs. Diff BOTH ways.
export LC_ALL=C
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
one() {  # one <label> <lane> <base> <scope> <declared-cmd> <edits...>
  local label=$1 lane=$2 base=$3 scope=$4 decl=$5; shift 5
  "$INST/run_lane_fix2.sh" "$label" "$S/$lane" "$base" 8 "$scope" "$@" > "$INST/driver_$label.log" 2>&1
  local rc=$?; [ $rc -eq 4 ] && { echo "$label BLOCKED"; return; }
  eval "$decl" | sed '/^$/d' | sort > "$INST/$label.declared"
  python3 "$INST/norm.py" < "$INST/run_$label.observed" | sed '/^$/d' | sort > "$INST/$label.obsnorm"
  local tailline; tailline=$(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_$label.log" | tail -1)
  echo "$label [$lane $scope: $*] | $tailline | declared=$(wc -l < "$INST/$label.declared") observed=$(wc -l < "$INST/$label.obsnorm") | unexpected-red=$(comm -13 "$INST/$label.declared" "$INST/$label.obsnorm" | wc -l) declared-but-green=$(comm -23 "$INST/$label.declared" "$INST/$label.obsnorm" | wc -l) | watchdog=$(awk '/WATCHDOG FIRED/{n++} END{print n+0}' "$INST/driver_$label.log") | $(awk '/loremaster.__file__/' "$INST/driver_$label.log")"
}
UB=${UB:?}; CB=${CB:?}
for WB in V0 Vstamped Valready Vb15legacy r4b:PXrem15 r4b:PXlie r4b:PX2; do
  one "fa1_U_$(echo $WB | tr ':' '_')" fixU "$UB" touched "python3 $INST/declared.py 'Tfix2 $WB'" $WB
done
one fa1_C_V0 fixC "$CB" touched "python3 $INST/declared.py 'Tfix2 V0'" V0
for WB in V0 Nmid Ncap48 Ncap64; do one "g5_U_$WB" fixU "$UB" reg "python3 $INST/declared_closure.py $WB" $WB; done
for WB in Wat Wplus Wtab Wspace Wnl; do one "g6_U_$WB" fixU "$UB" reg "python3 $INST/declared_closure.py $WB" $WB; done
echo DRIVERS_DONE
```

### A.10 `fix2_drivers2.sh` — md5 `04d867cefb780a0b0d66971e3d8bfee8`
```bash
#!/usr/bin/env bash
# fix2 G5 REGRESSION leg (removed-behaviour check): `hypothesis.target` changes WHICH 200 examples the generated legal leg
# draws. Every narrowing the UNTARGETED sample killed (adversary-r4b-fix observed REDs, run_wb_*.observed) must still
# be killed. Declared = adversary's OBSERVED set on the untargeted contract ∪ fix2's predicted additions (reg2/*.declared,
# written before this runs). Touched scope, lane fixU, -n 8. Waits for fix2_drivers.sh to finish first.
export LC_ALL=C
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
until awk '/DRIVERS_DONE/{f=1} END{exit !f}' "$INST/fix2_drivers.log" 2>/dev/null; do sleep 15; done
for W in r4b_G4 N3sep Nmixed Ndigit Ntrail Nsingle Nlen20 Ncap48 Ncap64; do
  EDIT=$W; [ $W = r4b_G4 ] && EDIT=r4b:G4
  label="reg2_$W"
  "$INST/run_lane_fix2.sh" "$label" "$S/fixU" "${UB:?}" 8 touched $EDIT > "$INST/driver_$label.log" 2>&1
  [ $? -eq 4 ] && { echo "$label BLOCKED"; continue; }
  python3 "$INST/norm.py" < "$INST/run_$label.observed" | sed '/^$/d' | sort > "$INST/reg2/$W.observed"
  echo "$label | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_$label.log" | tail -1) | declared=$(wc -l < "$INST/reg2/$W.declared") observed=$(wc -l < "$INST/reg2/$W.observed") | unexpected-red=$(comm -13 "$INST/reg2/$W.declared" "$INST/reg2/$W.observed" | wc -l) declared-but-green=$(comm -23 "$INST/reg2/$W.declared" "$INST/reg2/$W.observed" | wc -l) | watchdog=$(awk '/WATCHDOG FIRED/{n++} END{print n+0}' "$INST/driver_$label.log")"
done
echo DRIVERS2_DONE
```

### A.11 `fix2_reg3.sh` — md5 `f40a42131ee42005c59201e137f466f5`
```bash
#!/usr/bin/env bash
# fix2 amendment-18 condition (3): the regression table over BOTH generated legs (targeted GLt + untargeted twin GLu),
# declared before the run (reg3/*.declared), touched scope, final lane fixU, -n 8. Diff both ways.
export LC_ALL=C
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
for W in V0 r4b_G4 N3sep Nmixed Ndigit Ntrail Nsingle Nlen20 Ncap48 Ncap64 Nmid; do
  EDIT=$W; [ $W = r4b_G4 ] && EDIT=r4b:G4
  label="reg3_$W"
  "$INST/run_lane_fix2.sh" "$label" "$S/fixU" "${UB:?}" 8 touched $EDIT > "$INST/driver_$label.log" 2>&1
  [ $? -eq 4 ] && { echo "$label BLOCKED"; continue; }
  python3 "$INST/norm.py" < "$INST/run_$label.observed" | sed '/^$/d' | sort > "$INST/reg3/$W.observed"
  echo "$label | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_$label.log" | tail -1) | declared=$(wc -l < "$INST/reg3/$W.declared") observed=$(wc -l < "$INST/reg3/$W.observed") | unexpected-red=$(comm -13 "$INST/reg3/$W.declared" "$INST/reg3/$W.observed" | wc -l) declared-but-green=$(comm -23 "$INST/reg3/$W.declared" "$INST/reg3/$W.observed" | wc -l) | watchdog=$(awk '/WATCHDOG FIRED/{n++} END{print n+0}' "$INST/driver_$label.log") | $(awk '/loremaster.__file__/{print $NF}' "$INST/driver_$label.log" | awk -F/ '{print $(NF-3)}')"
done
echo REG3_DONE
```

### A.12 `fix2_final.sh` — md5 `8828447b5253d54c59f605e458f15d51`
```bash
#!/usr/bin/env bash
# fix2 FINAL-BYTES chain (lanes at the twin commit): F-A1 + G6 adversary drivers (declared sets unchanged — the twin
# draws only LEGAL values, so it cannot red on these builds), then FULL-suite Nmixed (amendment 18 condition 2), then
# SAT full U / C (-n 12 ALONE), then RED@HEAD on main. One pytest at a time; every run gated + 15 GiB watchdog.
export LC_ALL=C
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
source <(sed -n '/^one() {/,/^}/p' "$INST/fix2_drivers.sh")
UB=${UB:?}; CB=${CB:?}
for WB in V0 Vstamped Valready Vb15legacy r4b:PXrem15 r4b:PXlie r4b:PX2; do
  one "final_fa1_U_$(echo $WB | tr ':' '_')" fixU "$UB" touched "python3 $INST/declared.py 'Tfix2 $WB'" $WB
done
one final_fa1_C_V0 fixC "$CB" touched "python3 $INST/declared.py 'Tfix2 V0'" V0
for WB in Wat Wplus Wtab Wspace Wnl; do one "final_g6_U_$WB" fixU "$UB" reg "python3 $INST/declared_closure.py $WB" $WB; done
echo FINAL_DRIVERS_DONE
"$INST/run_lane_fix2.sh" FULL_Nmixed "$S/fixU" "$UB" 12 full Nmixed > "$INST/driver_FULL_Nmixed.log" 2>&1
python3 "$INST/norm.py" < "$INST/run_FULL_Nmixed.observed" | sed '/^$/d' | sort > "$INST/FULL_Nmixed.obsnorm"
echo "FULL_Nmixed | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_FULL_Nmixed.log" | tail -1) | unexpected-red=$(comm -13 "$INST/FULL_Nmixed.declared" "$INST/FULL_Nmixed.obsnorm" | wc -l) declared-but-green=$(comm -23 "$INST/FULL_Nmixed.declared" "$INST/FULL_Nmixed.obsnorm" | wc -l)"
"$INST/run_lane_fix2.sh" SATfinal_U "$S/fixU" "$UB" 12 full > "$INST/driver_SATfinal_U.log" 2>&1
echo "SATfinal_U | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_SATfinal_U.log" | tail -1)"
"$INST/run_lane_fix2.sh" SATfinal_C "$S/fixC" "$CB" 12 full > "$INST/driver_SATfinal_C.log" 2>&1
echo "SATfinal_C | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_SATfinal_C.log" | tail -1)"
"$INST/redhead_main.sh" > "$INST/driver_redhead_main.log" 2>&1
echo "REDHEAD_main | $(tail -1 "$INST/driver_redhead_main.log")"
echo FINAL_DONE
```

### A.13 `redhead_main.sh` — md5 `5f974ffc4fb9ebd4b9104f661190087c`
```bash
#!/usr/bin/env bash
# fix2: RED@HEAD — the 3 touched test files on the MAIN checkout (unbuilt production + fix2's uncommitted test edits),
# -n 8. NON-MUTATING (no checkout/clean). Same launch gate + 15 GiB PID watchdog as run_lane_fix2.sh.
set -uo pipefail
INST=$(dirname "$(readlink -f "$0")"); MAIN=/home/ejprice/PycharmProjects/lore; cd "$MAIN" || exit 2
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)$/ && $0 ~ /pytest/{n++} END{print n+0}')
  surreal=$(systemctl --user is-active spike-surreal.service)
  [ "$avail" -ge 20 ] && [ "$busy" -eq 0 ] && [ "$surreal" = active ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED avail=$avail busy=$busy surreal=$surreal"; exit 4; }
  sleep 20
done
echo "redhead_main: HEAD=$(git rev-parse --short HEAD) dirty=$(git status --porcelain -- loremaster lorerunes scripts | wc -l) avail ${avail} GiB spike-surreal=$surreal $(date '+%F %T')"
.venv/bin/python -c "import loremaster,pathlib; print('loremaster.__file__ =', pathlib.Path(loremaster.__file__).resolve())"
.venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/run_redhead_main.xml" loremaster/tests/test_agent_governance_63c_i_a.py loremaster/tests/test_agent_registry.py loremaster/tests/test_comms_schema.py > "$INST/run_redhead_main.log" 2>&1 &
PID=$!; low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 15 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; fi
  sleep 5
done
wait "$PID"; echo "exit=$? lowest MemAvailable ${low} GiB $(date '+%F %T')"; tail -1 "$INST/run_redhead_main.log"
```

### A.14 `mixed_probe.py` — md5 `e4c7fb76488f077acf0091abdc1f3b35`
```python
"""fix2: why Nmixed escapes the TARGETED generated leg. Replays the leg's strategy + settings (from_regex over the
lane's lorerunes.AGENT_NAME_PATTERN, derandomize=True, max_examples=200, database=None) with and without
hypothesis.target(len), and counts the draws each axis REACHES. Hypothesis home redirected into scratch.
Usage: <lane>/.venv/bin/python mixed_probe.py <scratch-home>"""
import sys

from hypothesis import configuration, given, settings, target
from hypothesis import strategies as st

configuration.set_hypothesis_home_dir(sys.argv[1])
import lorerunes  # noqa: E402

for targeted in (False, True):
    draws: list[str] = []

    @settings(derandomize=True, max_examples=200, database=None, deadline=None)
    @given(attribution=st.from_regex(lorerunes.AGENT_NAME_PATTERN, fullmatch=True))
    def leg(attribution: str) -> None:
        if targeted:
            target(float(len(attribution)), label="length")
        draws.append(attribution)

    leg()
    mixed = [d for d in draws if "-" in d and "_" in d]
    print(f"targeted={targeted}: draws={len(draws)} max_len={max(map(len, draws))} "
          f"len>=28={sum(len(d) >= 28 for d in draws)} at_cap={sum(len(d) == 64 for d in draws)} "
          f"mixed('-' and '_')={len(mixed)} doubled('--'|'__')={sum('--' in d or '__' in d for d in draws)} "
          f"all_digit={sum(d.isdigit() for d in draws)} trailing_sep={sum(d[-1] in '-_' for d in draws)} "
          f"example_mixed={mixed[:2]!r}")
```

### A.15 reg3 declarations (`reg3/DECLARED_AT`, written before any reg3 run)
```
declared at 2026-09-25 18:35:49 (before any reg3 run)
Rule: declared = fix2's MEASURED targeted-leg set on the landed contract (reg2/*.observed; Nmid = GLt from g5_U_Nmid)
  ∪ {GLu} wherever the ADVERSARY's untargeted GL killed the build (run_wb_*.observed). GLu entries are (G): the twin's
  derandomize seed is its own function digest, not 10a33ef's, so its draw set is NOT the graded one.
```

## Unrelated failures
None observed in fix2's runs: every correct-build run (SAT U/C final, driver V0 controls, reg V0) ended 0 failed. Noted, NOT measured by me: `surreal-memcap-2`'s ledger signal (#17001) reports `test_comms_schema.py` `-n 4` on the re-budgeted test store as `215 passed / 1 failed / 3 errors`, "unrelated … schema field-derivation" — my SAT runs of that same file (inside the full suite, both shapes, after the store restart) were green, so I could not reproduce it; it is that agent's to classify. **There are 0 failing tests unrelated to our present scope** in fix2's own measurements.

## VERDICT
fix2 lands amendment 16 §W 1–5 as amended by 17 and 18: F-A1 (SAT defect fixed, kills kept), G5 (length axis reached), G6 (single-edit class closed exhaustively), the four SAME-FAMILY bounds with closure-if-reopened (RS1combo moot at i-b), both over-claims deleted, and the untargeted twin restoring every kill the old sample had (measured, N-2). SAT 0 failed on both shapes on the final bytes; RED@HEAD 0 turned red; 11/11 SELF-DESTRUCT. Next: the BUILDER.
