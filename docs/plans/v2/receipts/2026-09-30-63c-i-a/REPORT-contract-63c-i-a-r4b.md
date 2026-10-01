# REPORT-contract-63c-i-a-r4b — contract r4b addendum (amendment-11 §W rows 1–5) on r4a (`bf77fb9`)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations · ONE commit `test(63c-i-a): contract r4b — …` on `feat/surreal-unification`.
- **deviations:** (1) idle-gate contract file NOT written — auto-mode classifier DENIED the `/tmp/claude-idle-gate-lore/` write (§0; the hook's default = this report, so nil effect) · (2) FORK-R3 escalated, ruled R-3a by amendment 12 (`f2a3bdd`) — conformed · (3) lane pass 1 ran on the r4b-provisional tests (FXh/FXhS/FXr); amendment-12's 3 controls added after, verified by direct scanner call + REF pass 2 · (4) FXr/RS1srvS killed with +2/+1 right-reason reds beyond my declarations · (5) lane guard changed from abort to wait ≤30 min on a foreign pytest (brief rule) · (6) FORK-MEM widened grant NOT used (both full suites launched at ≥29 GiB, `-n 12`).
- **Packages considered:** stdlib `ast` (`iter_fields`, `Name.ctx` — read) + `re` + pytest → the clause-(iii) scanner is **bespoke, justified** (§7). **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** 2 new helper symbols + 3 fixture constants, all dispositioned (§7). **Graded:** n/a (author, not grader) · built on HEAD `4debd26` (r4a `bf77fb9` + docs only).
- **Rows (§R):** 1 SAT fix — phrase leg DELETED (DUAL D1), SH1 prose PASSES, fixture counts forced off the birth value (SHb18/SHb3 pass), PX2 killed, PX2w = pinned bound · 2 GATING — end-to-end tool-seam invariance pin, GREEN at HEAD, kills RS1srv + RS1srvS · 3 GATING — receiver-blind ALLOWLIST (amendment 12), kills FXh/FXhS/FXr, 14+2+2 controls, FXo = pinned obfuscation bound · 4 — `a-`/`a_`/`00`, kills G3/G3d · 5 — 2 keep-axis sequences, kills C2/C2fake.
- **SAT (§3):** reference = every listed builder edit + SH1 prose; FULL SUITE ALONE `-n 12`: **`11486 passed, 62 skipped, 3 xfailed` — 0 failed**; ruff clean, typecheck OK, built-world currency = 11 SELF-DESTRUCTs. COMBO (FXo+PX2w+TWR) full suite `11486/0` — survivors are the pinned bounds.
- **RED@HEAD (§5):** 0 r4a-greens turned red · 5 new reds, all right-reason · 22 new greens (row 2 GREEN at HEAD).
- **Gates (§6):** ruff GREEN · currency `--legs typecheck,ruff` typecheck RED_ADJUDICATED 20 (unchanged) · pytest NOT_RUN by design.
- **decisions-needed:** none (FORK-R3 ruled). Candidate doors for the lead: §8 (R-1…R-8, none pinned).
- **Receipt pointers:** §FORK-R3 · §1 changes · §R per-row · §2 lane · §3 SAT/full · §4 DUAL · §5 RED · §6 gates · §7 packages/DRY · §8 residuals · §A instruments.

## 0. Capability check (brief-base §4) — measured 2026-09-25
- **Idle-gate contract file NOT written.** Demanded: `/tmp/claude-idle-gate-lore/<session-id>-contract-63c-i-a-r4b.contract`.
  What I have: the write was DENIED by the Claude Code auto-mode classifier ("[Auto-Mode Bypass]"); per the denial's terms
  I did not retry by another route. What I did instead: nothing — the hook falls back to the v1 default
  (`REPORT-contract-63c-i-a-r4b.md`), which is exactly the artifact I owe, so the practical effect is nil. What a lead must
  change: write the contract file for me, or add a permission rule for writes under `/tmp/claude-idle-gate-lore/`.
- lore MCP reachable (`register` OK, session `63c-20260924`). grep/rg hook-blocked (#473): textual sweeps use `awk`.
- Store reference `docs/reference/surrealdb-31-capabilities.md` read in full first.
- Adversary-r4a's scratch instruments survive on disk; copied READ-ONLY into my scratch (`my_ref_build_r4.py` md5
  `3e419c7544454d632b8bbd0c460111e2` = the md5 adversary-r4a recorded).

## FORK-R3 — amendment-11 MP-A1's clause (2) is UNSATISFIABLE by the honest post-build fake it names as a negative control
**The two sentences that conflict (amendment 11 §MP-A1 + §W row 3):**
- (A) *"the name `is_legal_identifier` may appear in exactly two shapes: (1) the ONE module-top `ImportFrom` …, and (2) `Call`
  nodes whose func is the bare `Name`. Any other occurrence — … a `Name` that is not a call — is a violation"*; and
- (B) *"negative controls: the honest post-build fake"* + §W row 3 *"the builder's granted edit is unchanged"*.

**Measured fact:** the builder's granted edit (delete the `try`/`except ImportError`, import at module top) leaves
`FakeAgentRegistry._shared_identifier_predicate` as `return is_legal_identifier` — a bare `Name` in a `Return`, NOT a
`Call`. Both independent references built to date do exactly that: the r4a author's `make_ref_r4a.py`
(`REPORT-contract-63c-i-a-r4a.md` @ `bf77fb9`, its `HELPER_RETURN` anchor) and adversary-r4a's `my_ref_leg_r4a.py`
(`REPORT-adversary-63c-i-a-r4a.md` §A.2 @ `94c31f8`). So reading (A) literally, the honest post-build fake is a VIOLATION,
the pin is RED on every correct build, and the builder — who may not edit tests and whose granted edit is "unchanged" —
is trapped (the C-DEF / satisfiability class; the brief makes SAT non-negotiable).

**Readings:**
- **R-3a (RECOMMENDED):** shape (2) = a **Load-context bare `Name`** anywhere (a call's func, a `return`, an argument) —
  every such read resolves to the module-top binding. DENIED (each a violation naming `file:line`): an `Attribute` with
  `attr == "is_legal_identifier"`; ANY string `Constant` equal to it (`getattr`/`hasattr`/`vars().get`/`sys.modules[…]`/
  `importlib`); any `Import`/`ImportFrom` alias naming it other than the ONE module-top `from lorerunes… import
  is_legal_identifier` (incl. an `as` rebinding to or from the name); a `Name` in **Store/Del** context (a rebind of the
  module global to a private rule); a function **parameter** of that name; a `global`/`nonlocal` naming it. Still an
  allowlist of two shapes (the safe set enumerated); kills FXh, X3d, FXf, FXg and a `vars()` read; the honest
  post-build fake and the builder's granted edit both stand. Soundness: with the module-top import MANDATORY and every
  rebind denied, a Load `Name` can only reach THE object (absence makes the fake's import fail at import time — no
  fallback path exists; the effect pin's delattr at `lorerunes*` homes leaves the fake's own binding, by its own design).
- **R-3b (literal):** keep "(2) Call nodes only" and CHANGE the builder's granted edit to also collapse the helper
  (call `is_legal_identifier(value)` directly and delete `_shared_identifier_predicate` + its `is not None` branch).
  Contradicts §W row 3's "the builder's granted edit is unchanged" and needs a builder-brief change.

I build R-3a (it is the only reading under which both (A)'s intent and (B) hold) and have escalated; if the lead/sidecar
rules R-3b, the delta is: tighten one predicate in the scanner + flip one negative control, and the builder brief grows.
Escalated 2026-09-25 via `lore_comms` #16012 (thread `q:63c-r4b-fork-r3`) + one native micro-format message to the lead.
**RULED R-3a — `docs/design/2026-09-25-packet63c-amendment-12.md` (`f2a3bdd`), relayed by the lead.** Conformed: clause (2)
= Load-context bare `Name`; denied = the grammar complement. Amendment 12's two extra named controls added —
NEGATIVE `the-collapsed-direct-call-post-build-fake` (the builder MAY collapse the helper) and POSITIVE `class-body-shadow`,
`walrus-rebind`. Direct scanner check (no pytest, 2026-09-25): all 14 clause-(iii) positives report an occurrence; all 4
negatives (incl. both honest post-build shapes) report 0; both obfuscated KNOWN-BOUND sources report 0.

## 1. What changed (test tree + yaml only; symbols, not line numbers)
| row | file :: symbol | change |
|---|---|---|
| 1 (MP-A2, SAT fix) | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent` | the sample-size PHRASE leg DELETED (in-place DUAL comment); the surviving birth-value leg now strips every identifier the fixture SEEDED (derived from the `before` snapshot: each row's string values + record ids, longest first; purely-digit strings never stripped) and every occurrence of the full count; under `perturbed-bound` every fixture-introduced COUNT (patched bound, trap count, legacy count, their sum) is forced OFF the birth value, with a self-check assert; docstring: "∀ over DIGIT spellings", PX2w named as the KNOWN BOUND + re-open trigger; failure text suggests `f"first {sample_size} of {count} ids shown"` |
| 2 (MP-A3, GATING) | `test_agent_governance_63c_i_a.py::TestRegisterStampsTheGovernedTriple63cIA::test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched` | NEW. Adversary-r4a's C-3 probe minus its recording, through `AppContext.comms(action="register")` on the credentialed harness; DATA invariance of `owner_principal`/`owner_agent`/`scope` only — the joiner's call outcome is NOT asserted (amendment-10 C-3's refusal is i-b's; any exception is caught and quoted in the failure text). Controls: keeper-owned before; foreign `carol` → `GovernedDenied` + row unchanged; joiner's fresh `joiner-b` owned by bob |
| 3 (MP-A1, GATING) | `test_agent_registry.py::_fake_predicate_import_violations` + new `_predicate_name_occurrence_violations` | clause (iii) ALLOWLIST (R-3a, see FORK-R3): receiver-blind over every string-valued AST field (`ast.iter_fields`); allowed = the first module-top un-aliased import alias + Load-context `Name`s. Docstring narrowed (the r4a "the `try` is the tell … FXf (any fallback)" over-claim) |
| 3 | `…::test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists` | docstring ERRATUM ("cannot outlive its premise in ANY spelling" narrowed to "every guard that SPELLS the name"); failure text names the allowlist |
| 3 | `…::test_the_fake_predicate_ALLOWLIST_names_every_other_occurrence_POSITIVE_CONTROL` (12 params) | NEW. Every source carries the honest module-top import and no `try`, so only clause (iii) can answer; the assertion keys on clause (iii)'s own text. FXh (adversary-r4a verbatim shape), X3d-beside-top-import, `vars`, `sys.modules`, `importlib`, `hasattr`, attribute re-read, module-global rebind, parameter shadow, second import in a function (`as _fresh`), `as`-rebind then reuse, `global` rebind |
| 3 | `…::test_the_fake_import_shape_scanner_stays_quiet_on_the_safe_shape_NEGATIVE_CONTROL[the-honest-post-build-fake]` | NEW param: the builder's granted edit applied to the real helper shape (bare `return is_legal_identifier`, call through the returned object, dotted name in docstring prose) |
| 3 | `…::test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named` (2 params) | NEW pinned bound: concatenated and joined names; pin-the-miss message; #138 re-open trigger verbatim (KB-2's shape) |
| 3 | `_comms_fakes.py::FakeAgentRegistry._shared_identifier_predicate` docstring | one sentence naming the allowlist (docstring only; the builder's granted edit is unchanged). C-5 stays one-file |
| 4 (G3) | `test_comms_schema.py::_LEGAL_IDENTIFIER_WITNESSES` | `"a-"`, `"a_"`, `"00"` appended LAST (param ids unchanged); comment states the HAND-LIST KNOWN BOUND + re-open trigger ("a fourth witness axis found by an adversary → derive the corpus"). Consumers (by value, 3): the SKIP-gate mutation leg, the corpus control, the register accept-control |
| 5 (C2) | `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA::_RE_REGISTER_SEQUENCES` / `_RE_REGISTER_EXPECTED_REAL` + `_PARITY_OTHER_KEEP` | two sequences: `consistent-then-different-keep` `(alice,K)→(alice,K2)` and `consistent-then-different-owner-and-keep` `(alice,K)→(bob,K2)` — the second pairs now span the 2×2 owner×keep grid; expected real = `("re-registered","alice_pid",True, keep:K)`; parity (fake == real) AND absolute real side via the existing row test |
| — | `scripts/pending_contracts.yaml` | comment-only on the `_comms_fakes.py` entry (names the allowlist); no count/symbol changes — currency unbuilt = 20 RED_ADJUDICATED, unchanged |

## R. Per-row table (row · pin · wrong build killed · mutation receipt — §2 lane tails, §3 full-suite leg)
| row | pin (file::test) | wrong build → verdict | receipt |
|---|---|---|---|
| 1 SAT fix | `test_agent_governance_63c_i_a.py::…::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]` | **SH1 (correct prose) now PASSES** (it is in the reference) · SHb18 / SHb3 (correct builds, birth value = a fixture count) PASS · PX2 KILLED · PX2w SURVIVES (pinned bound) | REF `3005 passed`; PX2 `1 failed` exact; SHb18/SHb3/PX2w `3005 passed`; full suite SAT `11486/0`, COMBO (PX2w) `11486/0` |
| 2 GATING | `test_agent_governance_63c_i_a.py::TestRegisterStampsTheGovernedTriple63cIA::test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched` | RS1srv KILLED · RS1srvS (tool clears scope) KILLED | RS1srv `1 failed` exact; RS1srvS `2 failed` (+1 right-reason); GREEN at HEAD (§5) |
| 3 GATING | `test_agent_registry.py::test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists` (+ `…ALLOWLIST…POSITIVE_CONTROL` ×14, `…NEGATIVE_CONTROL` +2, `test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named` ×2) | FXh KILLED · FXhS KILLED (effect + shape) · FXr KILLED · FXo SURVIVES (pinned bound) | FXh `1 failed` exact; FXhS `2 failed` exact; FXr `3 failed` (+2 right-reason); FXo `3005 passed`, COMBO full suite `11486/0`; controls verified by direct scanner call (§FORK-R3) and green in REF |
| 4 fixture | `test_comms_schema._LEGAL_IDENTIFIER_WITNESSES` → `…SKIP_gate_moves…[a-|a_|00]`, `…never_looks_up_any_value_of_the_hostile_corpus`, register accept-control | G3 KILLED · G3d KILLED | G3 `3 failed` exact; G3d `2 failed` exact |
| 5 row | `test_agent_registry.py::…::test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[consistent-then-different-keep|consistent-then-different-owner-and-keep]` | C2 (real+fake) KILLED on the absolute leg · C2fake KILLED on parity | C2 `2 failed` exact; C2fake `2 failed` exact |
A kill on the 25-file subset is a kill on the full suite (the red test is a member); every SURVIVOR (FXo, PX2w, TWR) has
its full-suite leg (COMBO, §3). Declare-then-diff driver (§A.3) for every build; the two SINGLE-ANCHOR builds were ALSO
run through `scripts/mutation_proof.py` on the lane (declared ids from `collected_r4b.txt`, `-p no:xdist`): **PX2** (anchor
= the SH1 prose line → `first 10 of`) `1 failed, 3 passed` → *"PROOF HELD — the declared RED set fired EXACTLY"*, tree restored
byte-exact (`principals.py` md5 `251c7c8a…`); **G3d** (anchor = the SKIP-gate `if` → `… or attribution.isdigit():`)
`2 failed, 9 passed` → *PROOF HELD*, restored byte-exact (`server.py` md5 `65644af6…`).

## 2. Wrong-build lane (INTERIM — measured 2026-09-25 on lane `r4b-ref`; 25 files of `files5.txt`, `-n 8`, declared-then-diffed both ways)
Driver: `run_lane_r4b.sh` (adversary-r4a's `run_lane_r4a.sh` re-pointed; its abort-on-foreign-pytest guard changed to
WAIT ≤30 min per the brief) + `my_wbs_r4b.py` (declarations written before any run). Pass 1 ran on the r4b-provisional
tests (3021 ids); pass 2 on the final tests incl. amendment-12's three controls (3024 ids — universe re-collected before
pass 2). Foreign pytest (another project's `tests/test_cli.py`) forced waits of 240–1120 s before several builds.
| build | tail | declared vs observed |
|---|---|---|
| REF (pass 1) | `3002 passed, 19 skipped` | 0/0 |
| FXh | `1 failed, 3001 passed` | exact: the shape pin (clause iii) |
| FXhS | `2 failed, 3000 passed` | exact: effect pin + shape pin |
| FXr (module-global rebind) | `3 failed, 2999 passed` | declared 1 (shape pin) — +2 UNEXPECTED, right-reason: `TestQ3…::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name-fake|session-fake]` (a rebound fake stops moving with the shared predicate). Declaration narrower than the kill; not re-declared after the fact |
| REF (pass 2, final tests) | `3005 passed, 19 skipped` | 0/0 |
| FXo (obfuscated lookup) | `3005 passed` | SURVIVES as declared — the pinned KNOWN BOUND |
| RS1srv | `1 failed, 3004 passed` | exact: row 2's end-to-end pin |
| RS1srvS (tool clears `scope`) | `2 failed, 3003 passed` | declared 1 (row 2) — +1 UNEXPECTED, right-reason: the r2 `test_re_register_does_not_restamp_the_governed_triple_mint_once` (this build clears scope on EVERY re-register) |
| C2 (real + fake re-stamp on a different keep) | `2 failed, 3003 passed` | exact: `RE_REGISTER_door[consistent-then-different-keep]` + `[…-different-owner-and-keep]` (absolute leg) |
| C2fake (fake only) | `2 failed, 3003 passed` | exact: the same two rows (parity leg) |
| G3 (SKIP gate `endswith(("-","_"))`) | `3 failed, 3002 passed` | exact: `SKIP_gate_moves…[a-]`, `[a_]` + the corpus control |
| G3d (SKIP gate `isdigit()`) | `2 failed, 3003 passed` | exact: `SKIP_gate_moves…[00]` + the corpus control |
| PX2 (`first 10 of {M} ids` — birth value in digits inside the derived prose) | `1 failed, 3004 passed` | exact: `R_Q5_1[perturbed-bound]` birth-value leg |
| PX2w (`first ten of {M} ids`) | `3005 passed` | SURVIVES as declared — the amendment-11 PX2w KNOWN BOUND |
| SHb18 (CORRECT build, birth value 18 = r4a's perturbed trap count) | `3005 passed` | SAT control PASSES (under r4a's leg, "of 18 ids shown" would have read 18 = birth → false RED) |
| SHb3 (CORRECT build, birth value 3 = the legacy count) | `3005 passed` | SAT control PASSES (the fixture-count guard moved legacy/traps off 3) |
| TWR (r4a KB-2 bound) | `3005 passed` | SURVIVES as declared |
Watchdog never fired (lowest MemAvailable over pass 2: 17 GiB). A kill observed on the 25-file subset is a kill on the
full suite (the red test is a member of it); survivors get the full-suite leg in §3.

## 4. DUAL — every pin r4b deletes or re-keys (each with an in-place comment)
| # | pin | what was deleted / re-keyed | virtue it carried | verdict |
|---|---|---|---|---|
| D1 | `test_R_Q5_1_…[perturbed-bound]` sample-size PHRASE leg (`first N` / `N … shown` / `showing N` == PATCHED bound) | DELETED (in-place DUAL comment at its old site) | a stated sample size that is neither the birth value nor the patched bound (a THIRD number) was refused | **dropped-deliberately** (amendment-11 MP-A2): it refused the correct prose `(first 3 of 18 ids shown)` (SH1 — a satisfiability defect); PX2 is killed by the birth-value leg (§2 row PX2). A third unrelated number is not a two-sources-of-one-policy defect and is not ruled |
| D2 | the same pin's birth-value leg — its STRIP set | re-keyed: trap ids → every identifier seeded in the `before` snapshot (string values + record ids, purely-digit strings excluded); the count-beside-noun phrase → every occurrence of the full count | "no integer equal to the birth value survives in the prose" | **preserved-with-pin**: the strip set only GREW over fixture DATA (never over prose), and the full count is forced ≠ birth (fixture self-check), so stripping cannot mask a restated birth value — PX2 still killed (§2); SHb18/SHb3 now pass (SAT) |
| D3 | the same pin's `perturbed-bound` fixture COUNTS | `trap_count` / `legacy_count` bumped off the birth value when they collide (unchanged at the reference birth value 10) | the bound + 15 above-cap population; the patched-≠-birth perturbation | **preserved**: trap count stays > patched bound (above-cap), patched ≠ birth unchanged; bumps fire only on a collision |
| D4 | `_fake_predicate_import_violations` / the shape pin — docstrings | narrowed ("the `try` is the tell … FXf (any fallback)"; "cannot outlive its premise in ANY spelling") | prose only | **erratum** (amendment-11 MP-A1 / amendment-12): both sentences were falsified by adversary-r4a FXh |
Additive only (no DUAL): row 2's new pin; row 3's clause (iii) + 14 positive params + 2 negative params + the KNOWN-BOUND
control; row 4's three witnesses (appended LAST — every pre-existing param id unchanged); row 5's two sequences.

## 3. SATISFIABILITY + full-suite leg (measured 2026-09-25, lane `ref` @ `r4b-ref` = lane-local `652bc8f`)
- **Reference** = adversary-r4's `my_ref_build_r4.py` VERBATIM (md5 `3e419c7544454d632b8bbd0c460111e2`; text in
  `REPORT-adversary-63c-i-a-r4.md` §A.1 @ `86379a4`; carries the lint cleanups + the `_IDENTIFIER_CHARSET_PATTERN =
  AGENT_NAME_PATTERN.pattern` rebind) + adversary-r4a's `my_ref_leg_r4a.py` VERBATIM (`REPORT-adversary-63c-i-a-r4a.md` §A.2
  @ `94c31f8`: guard deleted + `from lorerunes import is_blank, is_legal_identifier` at MODULE TOP; the
  `_REFUSAL_ID_SAMPLE_SIZE` WHY comment; the re-register "from ANY caller" sentence) + my `my_ref_leg_r4b.py` (§A.1: the
  SH1 derived prose `(first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown)` in the refusal). So every
  builder edit the brief lists is in it, and the fake keeps the bare-`Name` return (amendment-12's first honest shape).
- **Provenance** (printed by the tools): `loremaster.__file__ = …/775aa8ec-…/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `lorerunes.__file__ = …/scratchpad/ref/lorerunes/lorerunes/__init__.py`; `_comms_fakes.__file__ =
  …/scratchpad/ref/loremaster/tests/_comms_fakes.py`; `_comms_fakes.is_legal_identifier is lorerunes.is_legal_identifier` → `True`.
  `scratch_copy.sh` rc=0 (asserts every member resolves inside the copy).
- **25 contract files, `-n 8`:** `3005 passed, 19 skipped` — 0 failed (pass 2, final tests, 3024 ids).
- **FULL SUITE ALONE, `-n 12`** (`run_full_r4b.sh SAT`, §A.3; 2026-09-25 11:05:20–11:14:01 EDT; 29 GiB at launch, lowest 23 GiB;
  process table clean; watchdog never fired): **`11486 passed, 62 skipped, 3 xfailed, 9 warnings in 514.57s` — 0 failed, exit 0.**
  (= r4a's 11459 + 27 new ids; 3024 − 2997 = 27 ✓.) Launched under the ORIGINAL ≥23 GiB gate — the widened FORK-MEM grant
  (≥20 GiB at `-n 8`) was not needed.
- **AFTER the lint cleanups (the exact tree that ran):** `uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh`
  → every leg OK; currency `--legs typecheck,ruff` on the built world (my yaml copied in) → typecheck residuals are ONLY the
  11 SELF-DESTRUCT notices (both 63c-i-a entries discharge; 0 real mypy errors — = r4a's 11), ruff GREEN.
- **COMBO — the full-suite leg for every contract SURVIVOR** (`run_full_r4b.sh COMBO FXo PX2w TWR`; anchors pairwise disjoint:
  the fake's helper body · the refusal prose · `agents.py` header + imports; 31 GiB at launch, lowest 24 GiB):
  **`11486 passed, 62 skipped, 3 xfailed` — 0 failed.** All three survive the full suite, each as its PINNED KNOWN BOUND
  declares (FXo = amendment-11 obfuscation bound, `test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named`; PX2w =
  amendment-11 PX2w, the R_Q5_1 docstring; TWR = r4a KB-2).
- SAT controls SHb18 / SHb3 (correct builds whose birth value collides with a fixture count) pass the 25 files (§2); not
  separately full-suited (a pass on the subset + a correct build is not a survivor claim).

## 5. RED receipt — MAIN checkout, unbuilt production at HEAD (`4debd26`; production identical to `1705ea3`), my test edits only (measured 2026-09-25)
- Run: the 25 files of `files5.txt`, `-n 8`, alone (waited 720 s for a foreign pytest; 31 GiB at launch, lowest 29 GiB).
  Tail: **`195 failed, 2759 passed, 19 skipped, 51 errors`** (r4a's tail on the same production: `190 failed, 2737 passed,
  19 skipped, 51 errors` — adversary-r4a §1).
- Diff vs r4a tests on the SAME unbuilt production (`red_diff4.py red_r4b.xml red_r4a_baseline.xml`; 3024 vs 2997 ids):
  **r4a-GREEN turned r4b-RED: 0 · red→green: 0 · ids gone: 0 · NEW red: 5 · NEW green: 22.**
- The 5 new reds, each RIGHT-REASON (an unbuilt i-a seam):
  `…SKIP_gate_moves_with_the_SHARED_is_legal_identifier[a-]`, `[a_]`, `[00]` — `AttributeError: module 'lorerunes' has no
  attribute 'is_legal_identifier'` (the siblings' documented reason) · `…agree_on_the_RE_REGISTER_door[consistent-then-different-keep]`,
  `[consistent-then-different-owner-and-keep]` — `TypeError: AgentRegistry.register() got an unexpected keyword argument
  'session_keep_id'` (the siblings' documented reason).
- The 22 new greens at HEAD: row 2's end-to-end pin (**GREEN at HEAD, as ruled** — also measured alone earlier: 1 passed);
  row 3's 14 clause-(iii) positives + 2 new negative params + 2 KNOWN-BOUND params (pure-AST controls — green by
  construction at HEAD); row 4's three register accept-control params (legal names register at HEAD).
- `R_Q5_1[perturbed-bound]` stays RED at HEAD for its pre-existing reason (`principals._REFUSAL_ID_SAMPLE_SIZE` absent —
  `AttributeError`, amendment-4 MP-C), unchanged class.

## 6. Gate receipts (main checkout, final tree, 2026-09-25)
- `uv run ruff check .` → `All checks passed!`
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck RED_ADJUDICATED — 20
  residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3` · `ruff GREEN` · `pytest NOT_RUN` (by design
  — #466; never a bare `--currency`). = r4a's 20 (r4b adds no mypy error: the scanner parses source text; row 2/5 reuse
  existing seams).
- Built world (lane): ruff GREEN; `typecheck.sh` all legs OK; currency typecheck = exactly 11 SELF-DESTRUCT notices (both
  63c-i-a entries discharge on the build; #461 — no wrong discharge, no residual left behind) — §3.
- `scripts/pending_contracts.yaml`: comment-only edit on the `_comms_fakes.py` entry; entries honest (counts re-measured by the
  two currency runs above, not transcribed).

## 7. Packages / reuse / portability
- **Packages considered:** stdlib `ast` — `ast.iter_fields` (READ: the stdlib API, "yield a tuple of (fieldname, value) for
  each field in node._fields"; used receiver-blind) and `ast.Name.ctx` (`Load`/`Store`/`Del` — the finite grammar amendment 12
  relies on) → used; stdlib `re` → used; libcst/semgrep not installed and not needed (a field walk needs neither); ruff has no
  custom-rule API → verdict for the clause-(iii) scanner: **bespoke, justified** (stdlib AST, one consumer). `pytest` /
  `MonkeyPatch` → used.
- **DRY ledger:**
  | new symbol | lore query run | returned | disposition |
  |---|---|---|---|
  | `test_agent_registry._predicate_name_occurrence_violations` | `lore_search("test helper: AST scan reporting every occurrence of a name (attribute, string constant, rebind) in a source file")` | top hit `test_ast_reach_helpers._member_hand_lists_in` — a NAME-keyed `_SCANNED_MEMBERS` assignment scanner, not an any-field occurrence scan | HAND-ROLLED (the found helper keys on one assignment target; this needs every string-valued field of every node) |
  | `test_agent_registry._unparse_or_type` | `lore_search("safe ast.unparse fallback to node type name for violation messages")` | one weak doc hit (sim 0.51), no helper | HAND-ROLLED (3 lines, violation-text only) |
  | `_PARITY_OTHER_KEEP`, `_HONEST_TOP_IMPORT`, `_PRIVATE_RULE` | — | fixture constants | local fixture data, not policy |
  REUSED: `_is_lorerunes_module` (the r4a shared home test), `_real_re_register_outcome` / `_fake_re_register_outcome`,
  `credentialed_app_context`, `run`, `seed_agent_governed`, `_bare`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.

## 8. Candidate doors / residuals (NOT pinned — scope is closed; each for the lead)
| # | item | verdict / recommendation |
|---|---|---|
| R-1 | post-build, `_shared_identifier_predicate` + its `is not None` branch is a HEAD-RED accommodation's corpse | already routed by amendment 12 (builder MAY collapse; cold-audit residual; owner i-b contract author). Both shapes are green negative controls here |
| R-2 | row 1's strip set excludes purely-digit seeded strings | a fixture seeding a purely-digit identifier equal to the birth value would still false-RED; none is seeded today (ids/names/owners all carry letters). Stated, not pinned |
| R-3 | row 3's reach is ONE file (`_comms_fakes.py`) | as ruled (amendment-11 C-5 stays one-file; trigger: i-b's new test doubles) |
| R-4 | a guard hidden in a `lorerunes` production SHIM module (outside the test tree) | adversarial-only (adversary-r4a R-4); covered by the post-r4b pre-ruling (lead records a KNOWN BOUND if a delta builds it) |
| R-5 | row 2 observes ONE joiner/ONE keep; a takeover conditioned on a non-householded path is SF-63-1's (denied) | not a door within the ruling |
| R-6 | lore friction: one `lore_search` call took >120 s (backgrounded by the client, then completed) | noted, not filed as a defect — it answered correctly |
| R-7 | declared sets narrower than the kill for FXr (+2) and RS1srvS (+1) | my declarations; the extra reds are right-reason (§2); not re-declared after the fact |
| R-8 | another project's pytest (`mobile-pricepaper-smoke`, `tests/test_cli.py`) ran repeatedly on this box, costing ~1.5 h of waits | ops note for the lead; my runs never overlapped it |

## A. Instruments (pasted VERBATIM — scratch lives under my session scratchpad `775aa8ec-…/scratchpad/inst`, disposable)
Reused verbatim, not re-pasted: `my_ref_build_r4.py` (REPORT-adversary-63c-i-a-r4.md §A.1 @ 86379a4), `my_ref_leg_r4a.py` and `red_diff4.py` (REPORT-adversary-63c-i-a-r4a.md §A.2 / A.1 @ 94c31f8).

### A.1 `my_ref_leg_r4b.py`
```python
"""contract-63c-i-a-r4b — the r4b leg on top of my_ref_build_r4.py + my_ref_leg_r4a.py (reference build).

One edit: the refusal's sample-size prose is the CORRECT, DERIVED form amendment-11 MP-A2 says must pass —
``(first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown)`` (adversary-r4a SH1, wrapped to
the line cap so the lint leg of the SAT receipt runs on exactly this tree). Anchor asserted exactly-once (#194).
Usage: uv run --no-project python my_ref_leg_r4b.py <scratch-root>   (AFTER the r4 build and the r4a leg)
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
PRINCIPALS = ROOT / "loremaster/loremaster/principals.py"
OLD = '                "half-applied store; "\n'
NEW = (
    '                f"half-applied store (first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids "\n'
    '                "shown); "\n'
)
text = PRINCIPALS.read_text()
count = text.count(OLD)
assert count == 1, f"anchor occurs {count} times"
PRINCIPALS.write_text(text.replace(OLD, NEW))
print("r4b leg applied (SH1 derived prose in the refusal)")
```

### A.2 `my_wbs_r4b.py`
```python
"""contract-63c-i-a-r4b — wrong builds (and SAT controls) ON TOP of my reference (lane branch r4b-tests +
the reference commit: my_ref_build_r4.py + my_ref_leg_r4a.py + my_ref_leg_r4b.py).

Bodies of FXh / FXhS / G3 / C2 / RS1srv / TWR are adversary-r4a's my_wbs_r4a.py bodies (REPORT-adversary-
63c-i-a-r4a.md §A.3 @ 94c31f8), VERBATIM except where my reference moved an anchor (PX2/PX2w: my reference's
refusal already carries the SH1 derived prose, so the literal is written INTO that prose). New builds are mine.

Usage: uv run --no-project python my_wbs_r4b.py <scratch-root> <WB-id> [--declared]
  --declared  print the DECLARED expected-RED node ids, resolved against collected_r4b.txt (collect-only over
              the 25 files of files5.txt on the reference, taken BEFORE any wrong-build run) and exit.
Each edit asserts its anchor occurs exactly once (#194). A DECLARED set of [] predicts the build PASSES/SURVIVES.
"""

import sys
from pathlib import Path

INST = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"

SKIP_MUT = "test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier"
SKIP_CORPUS = "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus"
FAKE_EFFECT = "test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists"
SHAPE = "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
REREG_PARITY = "test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door"
E2E = "test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched"

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # --- row 3 (MP-A1): the fake-guard family ---
    "FXh": [(REG, [SHAPE])],  # clause (iii): the getattr string constant
    "FXhS": [(REG, [FAKE_EFFECT]), (REG, [SHAPE])],  # silent twin: effect pin AND clause (iii)
    "FXr": [(REG, [SHAPE])],  # module global REBOUND to a private rule after the honest import (Store Name)
    "FXo": [],  # OBFUSCATED getattr name + non-silent private fallback — the KNOWN BOUND: must SURVIVE
    # --- row 2 (MP-A3): the ownership family at the tool seam ---
    "RS1srv": [(GOV, [E2E])],
    "RS1srvS": [(GOV, [E2E])],  # tool re-stamps SCOPE only (owner_principal left) — the pin reads all three
    # --- row 5 (C2): the keep axis at the registry seam, real + fake ---
    "C2": [(REG, [REREG_PARITY, "[consistent-then-different-keep]"]),
           (REG, [REREG_PARITY, "[consistent-then-different-owner-and-keep]"])],
    "C2fake": [(REG, [REREG_PARITY, "[consistent-then-different-keep]"]),
               (REG, [REREG_PARITY, "[consistent-then-different-owner-and-keep]"])],
    # --- row 4 (G3): trailing-separator + all-digit axes ---
    "G3": [(REG, [SKIP_MUT, "[a-]"]), (REG, [SKIP_MUT, "[a_]"]), (REG, [SKIP_CORPUS])],
    "G3d": [(REG, [SKIP_MUT, "[00]"]), (REG, [SKIP_CORPUS])],
    # --- row 1 (MP-A2): the surviving birth-value leg + SAT controls ---
    "PX2": [(GOV, [RQ51, "perturbed-bound"])],  # the birth value restated in DIGITS inside the derived prose
    "PX2w": [],  # the birth value in WORDS — the KNOWN BOUND (amendment-11 PX2w): must SURVIVE
    "SHb18": [],  # SAT control: a CORRECT build whose birth value (18) equals r4a's perturbed trap count
    "SHb3": [],  # SAT control: a CORRECT build whose birth value (3) equals the fixture's legacy count
    # --- r4a's KB-2 bound, carried so the combined full-suite leg composes it ---
    "TWR": [],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (INST / "collected_r4b.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

HELPER_BODY = "        return is_legal_identifier\n"
TOP_IMPORT = "from lorerunes import is_blank, is_legal_identifier\n"
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"
FAKE_REREG = "        # status resets to active unconditionally (retired already excluded above).\n"
PRIVATE_RULE = 'lambda value: re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is not None'
SH1_LINE = '                f"half-applied store (first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids "\n'
BIRTH = "_REFUSAL_ID_SAMPLE_SIZE = 10\n"
AGE_LINE = "        registered_age_s = int((now - result.agent.registered_at).total_seconds())\n"


def fake_restamp(condition: str) -> None:
    edit(FAKES, FAKE_REREG,
         f"        if {condition}:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n" + FAKE_REREG)


def real_restamp(condition: str) -> None:
    edit(AGENTS, "        new_model = model if model is not None else existing.model\n",
         f"        if {condition}:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', $rid) SET owner_principal = $owner, \"\n"
         "                \"scope = $scope\",\n"
         "                {\"rid\": agent_id, \"owner\": RecordID(PRINCIPAL_TABLE, owner_principal_id),\n"
         "                 \"scope\": keep_scope(session_keep_id)},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")


C2_REAL = ('existing_row.get("scope") is not None and session_keep_id is not None '
           'and str(existing_row.get("scope")) != keep_scope(session_keep_id)')
C2_FAKE = ("self.db.scopes.get(agent_id) is not None and session_keep_id is not None "
           "and self.db.scopes[agent_id] != keep_scope(session_keep_id)")


def tool_restamp(assignment: str) -> None:
    edit(SERVER, AGE_LINE,
         AGE_LINE
         + "        if result.re_registered and principal_bare is not None and hasattr(self.agent_registry, \"_query\"):\n"
         "            # 'the owner follows the most recent registrant' — a TAKEOVER at the tool seam\n"
         "            await self.agent_registry._query(  # noqa: SLF001\n"
         f"                \"UPDATE type::record('agent', $rid) SET {assignment}\",\n"
         "                {\"rid\": self.agent_registry._agent_id(session, agent), \"owner\": principal_bare},  # noqa: SLF001\n"
         "            )\n")


if WB in ("FXh", "FXhS"):  # adversary-r4a verbatim
    fallback = PRIVATE_RULE if WB == "FXh" else "None"
    edit(FAKES, HELPER_BODY,
         "        import re  # noqa: PLC0415\n\n"
         "        import lorerunes  # noqa: PLC0415 - call-time read: 'robust' if the predicate is ever absent\n\n"
         "        if getattr(lorerunes, \"is_legal_identifier\", None) is not None:\n"
         "            return is_legal_identifier\n"
         f"        return {fallback}\n")
elif WB == "FXr":
    edit(FAKES, TOP_IMPORT,
         TOP_IMPORT + "import re as _re\n\n"
         "is_legal_identifier = lambda value: _re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None  # noqa: E731\n")
elif WB == "FXo":
    edit(FAKES, HELPER_BODY,
         "        import re  # noqa: PLC0415\n\n"
         "        import lorerunes  # noqa: PLC0415\n\n"
         "        shared = getattr(lorerunes, \"is_legal_\" + \"identifier\", None)\n"
         f"        return shared if shared is not None else {PRIVATE_RULE}\n")
elif WB == "RS1srv":  # adversary-r4a verbatim (owner_principal re-stamp)
    tool_restamp("owner_principal = type::record('principal', $owner)")
elif WB == "RS1srvS":
    tool_restamp("scope = NONE")
elif WB == "C2":  # adversary-r4a verbatim
    real_restamp(C2_REAL)
    fake_restamp(C2_FAKE)
elif WB == "C2fake":
    fake_restamp(C2_FAKE)
elif WB == "G3":  # adversary-r4a verbatim
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         "            or attribution.endswith((\"-\", \"_\"))  # 'a dangling separator is never a real name'\n"
         "        ):\n")
elif WB == "G3d":
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         "            or attribution.isdigit()  # 'an all-digit attribution is a counter, not a name'\n"
         "        ):\n")
elif WB == "PX2":
    edit(PRINCIPALS, SH1_LINE,
         '                f"half-applied store (first 10 of {len(owned_unscoped_ids)} ids "\n')
elif WB == "PX2w":
    edit(PRINCIPALS, SH1_LINE,
         '                f"half-applied store (first ten of {len(owned_unscoped_ids)} ids "\n')
elif WB == "SHb18":
    edit(PRINCIPALS, BIRTH, "_REFUSAL_ID_SAMPLE_SIZE = 18\n")
elif WB == "SHb3":
    edit(PRINCIPALS, BIRTH, "_REFUSAL_ID_SAMPLE_SIZE = 3\n")
elif WB == "TWR":  # adversary-r4 my_wbs4.py body verbatim (via adversary-r4a)
    edit(AGENTS, "class InvalidAgentIdentityError(AgentRegistryError):",
         "_LEGACY_NAME_RE = re.compile(r\"^[0-9a-z][0-9a-z_-]{0,63}$\")  # reworded class (KB-2)\n\n\n"
         "class InvalidAgentIdentityError(AgentRegistryError):")
    edit(AGENTS, "import logging\nimport secrets\n", "import logging\nimport re\nimport secrets\n")
else:
    raise SystemExit(f"unknown WB {WB}")
print(f"{WB} applied")
```

### A.3 `run_lane_r4b.sh` and `run_full_r4b.sh`
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4b lane driver (adversary-r4a run_lane_r4a.sh, re-pointed): for each WB (REF = no build),
# reset LANE to r4b-ref, resolve the DECLARED expected-RED set from collected_r4b.txt (collect-only on
# r4b-ref, taken BEFORE any wrong-build run), apply the build, assert provenance, run the 25 files of
# files5.txt (-n 8, ONE pytest session at a time, memory watchdog kills OUR pytest by PID < 12 GiB), diff
# observed-RED vs declared BOTH ways from junit, restore.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/775aa8ec-d4d7-4979-b3b3-301f9df236be/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/775aa8ec-d4d7-4979-b3b3-301f9df236be/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f r4b-ref && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-contract-63c-i-a-r4b.md
  [ -z "$(git status --porcelain | awk '!/REPORT-/')" ] || { echo "$WB: LANE DIRTY after reset — abort"; exit 2; }
  if [ "$WB" = REF ]; then : > "$INST/wb_${WB}.declared"; else
    uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$WB" --declared | sort > "$INST/wb_${WB}.declared" \
      || { echo "$WB: declaration failed"; exit 2; }
    uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$WB" >/dev/null || { echo "$WB: APPLY FAILED"; exit 2; }
    [ -n "$(git status --porcelain | awk '!/REPORT-/')" ] || { echo "$WB: build left the lane CLEAN"; exit 2; }
  fi
  .venv/bin/python -c "import loremaster,pathlib; assert pathlib.Path(loremaster.__file__).resolve().is_relative_to('$LANE'), loremaster.__file__" \
    || { echo "$WB: PROVENANCE FAILED"; exit 2; }
  waited=0  # brief: another pytest live -> wait up to 30 min, then report blocked
  while ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{f=1} END{exit !f}'; do
    [ "$waited" -ge 1800 ] && { echo "$WB: another pytest still running after 30 min — BLOCKED"; exit 3; }
    sleep 20; waited=$((waited+20))
  done
  [ "$waited" -gt 0 ] && echo "$WB: waited ${waited}s for a foreign pytest to finish"
  .venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/wb_${WB}.xml" $(cat "$INST/files5.txt") \
    > "$INST/wb_${WB}.log" 2>&1 &
  PID=$!; low=999
  while kill -0 "$PID" 2>/dev/null; do
    avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
    if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
    sleep 5
  done
  wait "$PID"
  .venv/bin/python - "$INST/wb_${WB}.xml" > "$INST/wb_${WB}.observed" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print(f"{case.get('classname', '')}::{case.get('name')}")
PY
  sort -o "$INST/wb_${WB}.observed" "$INST/wb_${WB}.observed"
  .venv/bin/python - "$INST/wb_${WB}.declared" "$INST/wb_${WB}.observed" <<'PY' > "$INST/wb_${WB}.diff"
import sys
declared = {l.strip() for l in open(sys.argv[1]) if l.strip()}
observed = {l.strip() for l in open(sys.argv[2]) if l.strip()}
def key(node):  # "path.py::Class::test[p]" / junit "pkg.mod.Class::test[p]" -> "Class::test[p]"; module-level -> "::test"
    parts = node.split("::")
    prefix = parts[-2] if len(parts) >= 2 else ""
    cls = "" if prefix.endswith(".py") else prefix.split(".")[-1]
    return f"{cls if cls[:1].isupper() else ''}::{parts[-1]}"
dk = {key(d): d for d in declared}
ok = {key(o): o for o in observed}
unexpected = sorted(set(ok) - set(dk)); still_green = sorted(set(dk) - set(ok))
print(f"declared={len(dk)} observed_red={len(ok)} unexpected_red={len(unexpected)} declared_still_green={len(still_green)}")
for u in unexpected: print("  UNEXPECTED RED:", ok[u])
for s in still_green: print("  DECLARED BUT GREEN:", dk[s])
PY
  echo "== $WB :: $(tail -1 "$INST/wb_${WB}.log") :: $(head -1 "$INST/wb_${WB}.diff") :: lowest ${low} GiB"
done
git checkout -q -f r4b-ref && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-contract-63c-i-a-r4b.md
# ---------------- run_full_r4b.sh ----------------
#!/usr/bin/env bash
# contract-63c-i-a-r4b (adversary-r4a run_full_r4a.sh, re-pointed): FULL suite ALONE at -n 12 on the ref lane at r4b-ref (+ optional WBs applied in order).
# Launch gate (lead grant FORK-MEM): MemAvailable >= 23 GiB AND no other python/pytest/uv pytest process; polls up to
# 30 min, else exits 4 ("blocked"). Watchdog kills OUR pytest by PID when MemAvailable < 12 GiB (then STOP).
# Usage: run_full_r4a.sh <label> [WB ...]
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/775aa8ec-d4d7-4979-b3b3-301f9df236be/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/775aa8ec-d4d7-4979-b3b3-301f9df236be/scratchpad/ref
LABEL=$1; shift
cd "$LANE" || exit 2
git checkout -q -f r4b-ref && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-contract-63c-i-a-r4b.md
for WB in "$@"; do uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }; done
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{n++} END{print n+0}')
  [ "$avail" -ge "${MINMEM:-23}" ] && [ "$busy" -eq 0 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
  sleep 20
done
echo "state: $(git status --porcelain | awk '!/REPORT-/' | wc -l) dirty paths; WBs: ${*:-none}; available at launch: ${avail} GiB; -n ${NPROC:-12}; launch gate ${MINMEM:-23} GiB; $(date '+%F %T')"
.venv/bin/python -m pytest -n "${NPROC:-12}" -q -p no:cacheprovider --junitxml="$INST/full_${LABEL}.xml" > "$INST/full_${LABEL}.log" 2>&1 &
PID=$!; low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc lowest MemAvailable during run: ${low} GiB; $(date '+%F %T')"
tail -1 "$INST/full_${LABEL}.log"
.venv/bin/python - "$INST/full_${LABEL}.xml" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print("RED:", f"{case.get('classname','')}::{case.get('name')}")
PY
git checkout -q -f r4b-ref && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-contract-63c-i-a-r4b.md
```

### A.4 one-off commands (verbatim)
```bash
# lane: ./scripts/scratch_copy.sh $S/ref (rc=0) ; cd $S/ref ; git checkout -b r4b-tests ; git add loremaster/tests ; commit (bfb68e5, lane-local)
#       uv run --no-project python inst/my_ref_build_r4.py $S/ref ; ... my_ref_leg_r4a.py ; ... my_ref_leg_r4b.py ; ruff ; commit (5699467) ; git branch r4b-ref
#       (after amendment 12) cp main's test_agent_registry.py ; commit on r4b-ref (652bc8f)
# universe BEFORE each lane pass: .venv/bin/python -m pytest --collect-only -q -p no:cacheprovider $(cat files5.txt) | awk '/::/' > collected_r4b.txt  (3021, then 3024)
# lane 1: run_lane_r4b.sh REF FXh FXhS FXr FXo ... (aborted at FXo on a foreign pytest; guard changed to wait) ;
# lane 2: run_lane_r4b.sh REF FXo RS1srv RS1srvS C2 C2fake G3 G3d PX2 PX2w SHb18 SHb3 TWR
# full:   run_full_r4b.sh SAT ; run_full_r4b.sh COMBO FXo PX2w TWR
# built-world gates (lane, my yaml copied in, then restored): uv run ruff check . ; ./scripts/typecheck.sh ;
#         uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff
# amendment-12 control check (main, no pytest): import test_agent_registry; call _fake_predicate_import_violations on every param
# RED@HEAD (main checkout, unbuilt HEAD production + my tests): pytest -n 8 --junitxml=red_r4b.xml $(cat files5.txt) ;
#         red_diff4.py red_r4b.xml red_r4a_baseline.xml   (baseline = adversary-r4a's red_r4a.xml, r4a tests on the SAME
#         unbuilt production at 1705ea3; md5 52376abad89732cefbcb6c6adbfc5170)
```
