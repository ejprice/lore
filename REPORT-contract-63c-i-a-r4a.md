# REPORT-contract-63c-i-a-r4a — the 63c-i-a contract, r4a addendum (amendment-9 §W rows 1–8 + amendment-8 §W)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state: done-with-deviations** — amendment-9 §W rows 1–8 + amendment-8 §W in ONE commit on `f2ba72e` (the base moved
  `92f7091 → f2ba72e` during the run: `REPORT-lead-63c.md` only, docs — no test or production path changed).
  **SAT: FULL SUITE ALONE `-n 12` on my reference → `11459 passed, 62 skipped, 3 xfailed` — 0 failed, exit 0** (= r4's
  11428 + the net +31 new ids; measured 2026-09-25 04:30–04:41 EDT); ruff clean + 0 real mypy errors on the built world
  AFTER the builder's four granted edits (§SAT). **TWR (the KB-2 bound) SURVIVES the full suite: `11459 passed` — 0 failed.**
- **Mutation:** **14/14 wrong builds PROOF HELD**, each red on exactly its declared pin(s), 0 unexpected reds, declared-before-
  run from `--collect-only` (RS1 · FX2 · RS1FX2 · G1 · G2 · FXg · FXf · FXf2 · X3b · X3d · PX2 · MP2DEF · R5 · R5b) + a
  final-text re-proof (§ROWS). RS1FX2 is the receipt that row 1 needed the ABSOLUTE real-side expectation (`fake == real`
  held; the absolute leg reddened).
- **RED@HEAD (main, 25 files):** 0 r4-greens turned red · 13 new reds, all right-reason · 19 new greens · 1 id gone (the
  deleted premise pin) (§RED).
- **deviations:** DV-1 FULL SUITES LAUNCHED AT 24 GB (lead grant FORK-MEM, 2026-09-25: ≥23 GB, one at a time, 12 GB PID
  watchdog): SAT launched 24 GB → lowest 18 GB; TWR launched 24 GB → lowest 16 GB; watchdog never fired; process table
  clean before each launch · DV-2 declare-then-diff driver instead of `mutation_proof.py` (multi-edit builds; the tool's
  discipline kept) · DV-3 §FORKS R-A picked reading (ii) with (i) written · DV-4 the lane graded an earlier text of
  `test_agent_registry.py` (inline predicate → shared `_is_lorerunes_module` + comments), re-proved on the final text.
- **Packages considered:** none — no mechanism specified (tests only). Stdlib `ast`/`re` + `pytest.MonkeyPatch.delattr`
  read at use; `_logging_fixtures.module_level_bindings_of` REUSED.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 7 new test-substrate symbols, all dispositioned (§DRY).
- **Graded:** n/a — the contract author's report, not a verdict on another agent's artifact.
- **decisions-needed:** §FORKS R-A (only if the sidecar meant reading (i)); §CANDIDATES C-1…C-5 (surfaced, NOT pinned).
  Builder brief rows (unchanged + one): delete the fake's guard AND import `is_legal_identifier` at MODULE TOP (the new
  shape pin reds until both) · `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` · `_REFUSAL_ID_SAMPLE_SIZE`
  docstring states WHY · re-register docstring "from ANY caller, including a different householded principal" · delete
  BOTH `pending_contracts.yaml` entries with the build.
- **receipt pointers:** §FORKS · §DUAL (D1–D4) · §DRY · §ROWS · §LANE · §RED · §GATES · §SAT · §CANDIDATES ·
  §INSTRUMENTS. Lore friction: finding #481.

## Capability check (brief-base §4) — measured 2026-09-25
- Demanded / had: lore MCP (register + heartbeat OK), `git`, `uv run pytest/ruff`, `scripts/scratch_copy.sh`,
  `scripts/typecheck.sh`, `scripts/pending_contract_gate.py`, test store `ws://127.0.0.1:18000`. All reachable.
- grep/rg are hook-blocked (#473) — every textual sweep in this report is `awk` over `git ls-files`, said once.
  A `grep -q` inside my own wait-loop tripped the hook once (read-only; rewritten with `awk`).
- Never touched `:18500`; never called the TEI embedder.
- Scratch lanes via `scratch_copy.sh` (provenance asserted by the tool AND re-asserted by every driver run):
  root `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5c239db8-6765-4361-80d9-ccabf55a4d76/scratchpad`
  (my session scratchpad — the lead did not name one; instruments are PASTED in §INSTRUMENTS so nothing the
  report asserts lives only there). `ref` = my working tree + my reference build (branch `r4a-ref`);
  `head` = HEAD `92f7091` exactly (r4 tests, unbuilt production).
  `loremaster.__file__` (ref) = `…/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `lorerunes.__file__` (ref) = `…/scratchpad/ref/lorerunes/lorerunes/__init__.py`;
  (head) = `…/scratchpad/head/loremaster/loremaster/__init__.py`.
- Adversary-r4's scratch instruments survived on disk
  (`/var/tmp/…/bd8e690b-…/scratchpad/inst`); I COPIED them into my scratchpad and derived mine from them
  (`my_ref_build_r4.py` verbatim base; `my_wbs4.py` bodies re-anchored). Their verbatim text is in
  `REPORT-adversary-63c-i-a-r4.md` §A (committed `86379a4`), so the derivation is reproducible from tracked files.

## §FORKS / readings (written BEFORE acting — brief §ESCALATION; none blocks, so none was messaged)
- **FORK-MEM · the full-suite memory floor — MESSAGED, GRANTED.** The brief's ~28 GB floor was never met in a 30-min
  poll (03:58–04:28 EDT, MemAvailable 24–25 GB; the other session's pytest cleared ~04:08). Written here first, sent to the
  lead (native micro-format + `lore_comms` #16009). **Lead ruling (FORK-MEM GRANTED):** launch at ≥ 23 GB, one pytest
  session at a time, 12 GB kill-by-PID watchdog on every run, process table re-checked before each launch; if the watchdog
  fires, STOP. Executed as ruled — see DV-1 and §SAT.
- **R-A · the restored presence pin's "module-level `ImportFrom` of it from `lorerunes`" (amendment-9 MP-R4-5).**
  Reading (i): exactly `from lorerunes import is_legal_identifier`. Reading (ii): from `lorerunes` OR one of its
  submodules (`from lorerunes.identifiers import …`). Both are the SAFE shape for the property the pin exists for
  ("the guard cannot outlive its premise" — an unguarded module-top import cannot skip anything); (i) would red an
  honest builder who imports from the defining submodule, i.e. a false positive on correct code. **Picked (ii)**,
  pinned by the negative control `[submodule-top-import-and-an-unrelated-try]`. If the sidecar meant (i), it is a
  one-token change in `_fake_predicate_import_violations` (`_is_lorerunes_module(node.module)` → `node.module ==
  "lorerunes"`) and that negative control flips to a positive one.
- **R-B · "`_LEGAL_IDENTIFIER_WITNESSES`, beside `_HOSTILE_IDENTIFIERS`" vs the PRE-EXISTING legal lists.**
  `test_comms_schema.py` already carries `_VALID_IDENTIFIERS = ("fixer-b", "fixer_b2", "a", "wave7", "z" * 64)`
  (the brief store-ASSERT accept leg), and `test_agent_registry.py` carries two more local legal lists
  (`test_pattern_accepts_legal_names`: `["fixer-b", "audit-c2", "a", "wave7", "scout_d"]`; the register
  accept-control's `["fixer-b", "a", "wave7", "z" * 64]`). The ruling names a NEW tuple with five exact values;
  merging the old lists into it is a refactor the ruling does not state and that touches pins outside §W.
  **Did (literal reading):** created `_LEGAL_IDENTIFIER_WITNESSES` with exactly the ruled five; APPENDED it to the
  register accept-control's params (kept r4's four values — additive, no DUAL). **Not done, surfaced as a
  candidate (§CANDIDATES C-1):** folding `_VALID_IDENTIFIERS` and the `test_pattern_accepts_legal_names` list into
  the one legal corpus — the ruling's own "ONE corpus" principle points there; the sidecar rules.

## §DUAL — every pin deleted, inverted or re-keyed (an in-place DUAL comment sits at each)
| # | pin | what changed | removed-behaviour inventory → adjudication | in-place comment |
|---|---|---|---|---|
| D1 | `test_message_enforcement_63b_ii_a.py::…::test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see` | **DELETED** (amendment-9 R-1) | (a) "an unswept emitter emits no relation" → PRESERVED-WITH-PIN, strictly stronger: packet-07 `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically::test_this_slice_contains_neither_a_relation_table_nor_a_sequence` (+ `…::test_every_table_definition_is_IF_NOT_EXISTS`) — kills R5 and R5b (§ROWS row 6 receipts); (b) "a relation in a NEW third unswept generator" → PRESERVED by the FORK-A exact-set pin (the set grows); (c) its own anti-vacuity (swept sees ≥ 1 relation) → DROPPED DELIBERATELY (guarded only its own reader; the emitted corpus's ≥ 1 relation stays pinned by `test_the_generator_corpus_is_DERIVED_by_inspection_and_non_vacuous`). FORK-A pin's docstring now cites the packet-07 pins as the premise's observation. | `# DUAL (r4a, amendment-9 R-1 — DELETED, not re-keyed)` where the pin stood |
| D2 | `test_agent_registry.py::test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` | **RE-KEYED reach** (amendment-9 MP-R4-4): "predicate absent" simulated at EVERY `lorerunes*` module-level binding (`module_level_bindings_of`, anti-vacuity ≥ 1) instead of ONE (`monkeypatch.delattr(lorerunes, …)`) | virtues kept: HEAD control (unchanged), ∀ corpus × {name, session}, "any exception is non-silent". The r4 single-binding removal is a SUBSET of the new removal set (the package attribute is one of the `lorerunes*` bindings) — nothing lost. | `DUAL (r4a, amendment-9 MP-R4-4 …)` paragraph in the docstring |
| D3 | r4's DUAL E1 (the deleted r3 spelling pin) | **ERRATUM + RESTORATION** (amendment-9 MP-R4-5, reading (b)): the deletion was a DUAL LOSS — the presence property is restored property-shaped as `test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists` (+ 8 positive / 2 negative synthetic controls) | r3 virtue "the guard's mere PRESENCE reds" → PRESERVED-WITH-PIN in a stronger shape (allowlist of the safe state, not a spelling of the forbidden one); r3's HEAD anti-vacuity → PRESERVED (the new pin's HEAD control: the scanner must SEE the HEAD guard). Cites the amendment-6 MP-3 erratum. | `# ⚠ ERRATUM (r4a, amendment-9 MP-R4-5 — against amendment-6 MP-3)` appended to r4's DUAL block |
| D4 | `test_agent_registry.py::…::test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door` | absolute leg **RE-KEYED** from an `if alpha / else refused` pair to a per-sequence table `_RE_REGISTER_EXPECTED_REAL` | the three r4 sequences' expected values carried byte-for-byte (alpha → `("re-registered", None, True, None)`; each mixed pair → `("refused", "alice_pid", True, keep:K)`) — PRESERVED; the re-key exists so the fourth sequence cannot fall into the `else` branch's REFUSED expectation | `# DUAL (r4a — RE-KEYED, values PRESERVED)` above the table |

**Additive only (no DUAL owed, said so in place):** `"fixer.b"` appended LAST to `_HOSTILE_IDENTIFIERS` (every index-derived id
unchanged); SKIP-gate mutation leg + register accept-control KEEP their r4 params and append the legal corpus; the fourth
re-register sequence; the RS1 real-writer pin; the KB-2 control; the PX2 leg (inside the existing `perturbed-bound` param).
**Prose only (not pins):** KB-3 / R-3 docstring sentences, the KB-4 failure text, the R-4 failure text, the R-2 header, the
`_comms_fakes.py` removal-trigger docstring, the `pending_contracts.yaml` comment.

## §DRY — reuse ledger (brief-base §6); every new symbol is TEST substrate
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `test_comms_schema._LEGAL_IDENTIFIER_WITNESSES` | `lore_search("corpus of valid legal agent identifier values used by tests")` | `test_agent_registry.py:900` `test_pattern_accepts_legal_names`'s local list (+10 elided, budget-named); `_VALID_IDENTIFIERS` found by reading the corpus's own file | **HAND-ROLLED as RULED** (amendment-9 names the tuple and its five values); overlap with `_VALID_IDENTIFIERS` + two local lists → §FORKS R-B / §CANDIDATES C-1 |
| `TestTheFakeRegistryMirrorsTheWriter63cIA._RE_REGISTER_EXPECTED_REAL` | (class-local table beside r4's `_RE_REGISTER_SEQUENCES`) | — | **EXTENDED** r4's `_RE_REGISTER_SEQUENCES` pattern (a sibling table keyed on the same ids) |
| `_is_lorerunes_module` · `_is_lorerunes_import` · `_fake_predicate_import_violations` · `_PREDICATE_NAME` · `_GUARDED_CALL_TIME_IMPORT` | `lore_search("AST helper: is this import statement from the lorerunes package …")`; `lore_search("scan source for try/except ImportError guard around an import …")`; `lore_search("helper that walks ast.Try nodes to find guarded imports …", budget 3000)`; `lore_search("imports executed at module import time, walk skipping function and class scopes", tier=lore)` | lorescribe's imports-chunk test; `test_surreal_harness.py:1683` (a shape-param scanner test, not a reusable import helper); `REPORT-blindreader-150.md:158` — the finding that a `tree.body`-only import scan misses a `try`-wrapped import (my clause (ii) uses `ast.walk` over every `Try` for exactly that reason) | **HAND-ROLLED** — no shared import-shape helper exists; ONE consumer each. `_is_lorerunes_module` is itself shared by BOTH r4a pins (effect sweep + shape scan) — one home test, not two |
| (reused, not new) | — | `_logging_fixtures.module_level_bindings_of` · `_classify_charset_constants` · `_PATTERN_HOME_MEMBER` · `_traffic_line_lookups` · `_real_re_register_outcome` / `_fake_re_register_outcome` | **REUSED** |

Lore friction noticed during these searches: finding **#481** filed (a served memory teaches retired tool names).

## §ROWS — amendment-9 §W rows 1–8 (+ amendment-8 §W), each with its kill receipt (measured 2026-09-25)
Method (all rows): lane `ref` = my reference (branch `r4a-ref`); each build applied by `wbs_r4a.py` (anchors
asserted exactly-once), DECLARED expected-RED ids resolved from `collected_r4a.txt` (collect-only over the 25 files
of `files5.txt`, **2997 ids**, taken on `r4a-ref` BEFORE any wrong-build run), run `-n 8` over the 25 files, observed
vs declared diffed BOTH ways from junit (`run_lane_r4a.sh`). Reference tail on the same 25 files: **`2978 passed,
19 skipped` — 0 failed**. Every build below: **`unexpected_red=0 declared_still_green=0`** (PROOF HELD), every red
message read and right-reason (quoted heads in §LANE). Full-suite leg: a build killed by the 25 contract files is
killed; the only survivor CLAIM (TWR, the bound) gets its own full-suite run (§SAT-B).

| row | pin(s) — file::test | wrong build killed | lane tail (25 files) |
|---|---|---|---|
| **1** (MP-R4-1/-6, GATING) | `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA::test_the_REAL_writer_never_re_stamps_a_stamped_row_from_a_DIFFERENT_householded_principal` (KP-RS1 shape, absolute) · `…::test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[consistent-then-householded-joiner-pair]` (KB-5 row: `fake == real` + ABSOLUTE real side via `_RE_REGISTER_EXPECTED_REAL`) | **RS1** (real writer re-stamps a stamped row from the caller's pair) → both pins red · **FX2** (fake-only re-stamp) → parity row red · **RS1FX2** (BOTH re-stamp — `fake == real` holds) → parity row red **on its ABSOLUTE leg** + the RS1 pin: the proof that a `real == fake`-only row would have passed | RS1 `2 failed, 2976 passed` · FX2 `1 failed, 2977 passed` · RS1FX2 `2 failed, 2976 passed` |
| **2** (MP-R4-3 / R-2, GATING) | `test_comms_schema._LEGAL_IDENTIFIER_WITNESSES` (`"a"`, `"0z"`, `"a_b"`, `"a-b"`, `"a"*64`) · `…::test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[<each witness>]` (baseline "looked up exactly once") · `…::test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus` (control over every witness) · `…::test_register_accepts_a_valid_identifier_positive_control[<each witness>]` · header sentence narrowed | **G1** (`or len(attribution) > 32`) → `[aaaa…(64)]` baseline + the corpus control | G1 `2 failed, 2976 passed` |
| **3** (MP-R4-4) | `test_agent_registry.py::test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` — "predicate absent" at EVERY `lorerunes*` binding (`module_level_bindings_of`, anti-vacuity ≥ 1) | **FXg** (guard kept, `from lorerunes.identifiers import …` inside the `try`) → effect pin + shape pin · **X3b** (ruled guard) → both · **X3d** (`getattr(…, None)`, module-top import kept) → effect pin ONLY (the shape pin is blind to it by construction — the two-pins-two-properties split, measured) | FXg `2 failed, 2976 passed` · X3b `2 failed, 2976 passed` · X3d `1 failed, 2977 passed` |
| **4** (MP-R4-5) | `test_agent_registry.py::test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists` + `test_the_fake_import_shape_scanner_names_every_guard_POSITIVE_CONTROL[8 shapes]` + `…_stays_quiet_on_the_safe_shape_NEGATIVE_CONTROL[2 shapes]` | **FXf** (guard kept with a NON-silent private-regex fallback — the effect pin is blind by construction) → shape pin ONLY · **FXf2** (module-top import KEPT + a guarded call-time fallback beside it) → shape pin ONLY · FXg, X3b above | FXf `1 failed, 2977 passed` · FXf2 `1 failed, 2977 passed` |
| **5** (MP-R4-7) | `test_agent_governance_63c_i_a.py::…::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]` — PX2 leg: birth value (read BEFORE patching) absent from the stripped residue; any stated sample size == the patched bound | **PX2** (`"half-applied store (first 10 ids shown); "`) → red on the BIRTH-value leg (*"restates the BIRTH sample size 10 while the slice follows the PATCHED constant 3"*) | PX2 `1 failed, 2977 passed` |
| **6** (R-1) | premise pin DELETED (DUAL D1); FORK-A pin's docstring cites the packet-07 pins | **R5** (un-ENFORCED `holds` in the lease slice) and **R5b** (the swept `to` re-defined WITHOUT `ENFORCED`) — both killed with the premise pin GONE, by exactly `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically::{test_this_slice_contains_neither_a_relation_table_nor_a_sequence, test_every_table_definition_is_IF_NOT_EXISTS}` | R5 `2 failed, 2976 passed` · R5b `2 failed, 2976 passed` |
| **7** (amendment-8) | KB-1: `"fixer.b"` appended to `_HOSTILE_IDENTIFIERS` · KB-2: `test_agent_registry.py::TestTheIdentifierCharsetTextHasOneSpelling63cIA::test_KNOWN_BOUND_a_REWORDED_or_ASSEMBLED_charset_is_NOT_named[reworded-class-TWR, reworded-digit-escape, runtime-assembled]` with the ruled KNOWN BOUND message + #138 trigger · KB-3 docstring sentence · KB-4 failure text · KB-5 = row 1 | **G2** (reworded dotted disjunct at the gate) → the corpus leg names `{'fixer.b': ['fixer.b']}` · **TWR** — the bound: must SURVIVE (§SAT-B full suite) | G2 `1 failed, 2977 passed` |
| **8** (prose) | R-4: `perturbed-bound` failure text now *"does not read _REFUSAL_ID_SAMPLE_SIZE at CALL time (a restated literal, or a value captured at def time …)"* · R-3: stale-exemption `(path, binding)` trigger sentence in the text pin's docstring | **MP2DEF** (control: ONE source captured at def time) → red, and the message is now the right diagnosis | MP2DEF `1 failed, 2977 passed` |

### Final-text re-proof (the r4a-ref lane's `test_agent_registry.py` changed AFTER the lane: the effect pin now calls
the shared `_is_lorerunes_module` instead of an inline copy of the same predicate, plus comments) — measured 2026-09-25
on `r4a-ref` @ `faed272` (= the committed test text), `-p no:xdist`, the touched pins only:
```
== REF :: 4 passed, 293 deselected
== FXg :: 2 failed, 2 passed  -> effect pin + shape pin
== X3b :: 2 failed, 2 passed  -> effect pin + shape pin
== X3d :: 1 failed, 3 passed  -> effect pin only
== FXf :: 1 failed, 3 passed  -> shape pin only
== RS1 :: 2 failed, 2 passed  -> [consistent-then-householded-joiner-pair] + the RS1 real-writer pin
== PX2 :: 1 failed            -> R_Q5_1[perturbed-bound]
```
The other three touched files are byte-identical between the lane and the commit (their lane receipts stand).

## §LANE — right-reason message heads (junit, verbatim, truncated)
- RS1 · parity: `real=('re-registered', 'bob_pid', True, 'keep:sessionkeep7') fake=('re-registered', 'alice_pid', …)` · RS1 pin: `a re-register from a DIFFERENT householded principal changed the governed triple: ('re-registered', 'bob_pid', True, 'keep:sessionkeep7')`
- FX2 · parity: `real=('re-registered', 'alice_pid', …) fake=('re-registered', 'bob_pid', …)`
- RS1FX2 · parity: `the REAL writer's RE-register outcome for 'consistent-then-householded-joiner-pair' is not the ruled one: ('re-registered', 'bob_pid', …)` — `fake == real` PASSED; the ABSOLUTE leg caught it
- G1 · `BASELINE: the legal attribution 'aaaa…(64)' was not looked up exactly once` · corpus control: `CONTROL: the legal witness 'aaaa…(64)' was not looked up exactly once`
- G2 · `the SKIP gate looked up value(s) that cannot BE an identity …: {'fixer.b': ['fixer.b']}`
- FXg / X3b / X3d · effect: `the fake REGISTERED hostile identities while the shared predicate was unavailable: ["name=''", …]`; FXg / X3b / FXf / FXf2 · shape: `the fake's HEAD-RED guard outlived its premise …`
- PX2 · `the refusal PROSE restates the BIRTH sample size 10 while the slice follows the PATCHED constant 3`
- MP2DEF · `… it named 10 — the bound was PATCHED, so the slice does not read _REFUSAL_ID_SAMPLE_SIZE at CALL time (a restated literal, or a value captured at def time …)`
- R5 / R5b · `plain TABLE definitions must be IF NOT EXISTS (§1.1): ['DEFINE TABLE OVERWRITE holds|to TYPE RELATION …']` and `'TYPE RELATION' not in 'DEFINE TABLE OVERWRITE …'`

## §RED — main checkout, r4a tests only, production at HEAD `92f7091` (unbuilt); baseline = lane `head` = `92f7091` exactly (r4 tests). Measured 2026-09-25.
- Run set: `files5.txt` (25 files — adversary-r4's 24 ∪ `test_floor_calibration_schema.py`), `-n 8`, one session at a time.
- Tails: **r4a (main) `190 failed, 2737 passed, 19 skipped, 51 errors`** · r4 (head lane) `177 failed, 2719 passed, 19 skipped, 51 errors`.
- `red_diff4.py red_r4a.xml red_r4.xml` (its labels read "r4"/"r3" — here r4a/r4): **r4-GREEN turned r4a-RED: 0 · NEW red
  ids: 13 · NEW green ids: 19 · r4 ids gone: 1 (the deleted premise pin, green at HEAD) · red→green: 0.** Id arithmetic:
  2966 + 13 + 19 − 1 = 2997 ✓.
- Every NEW red, classified (all RIGHT reason — the same unbuilt seams r4's reds name):
  - `SKIP_gate_moves_with_the_SHARED_is_legal_identifier[a|0z|a_b|a-b|a×64]` ×5 — `AttributeError: module 'lorerunes' has no attribute 'is_legal_identifier'` (raised AFTER the baseline passed: the gate looks every witness up once at HEAD).
  - `…agree_on_outcome_class_and_stamps[hostile-13-name|session]` ×2 — `TypeError: … unexpected keyword argument 'session_keep_id'` (the new `"fixer.b"` corpus row; same reason as hostile-00…12).
  - `…refuses_a_hostile_identifier_before_any_store_write[fixer.b-name|session]` ×2 — `TxnDomainRejectionError … (assert violation)`: the STORE ASSERT refuses it at HEAD, not the unbuilt app-side MOVE (the documented RED reason of every sibling param).
  - `test_a_hostile_legacy_row_is_refused_on_re_register_and_still_touches[fixer.b-name|session]` ×2 — `Failed: RED-at-HEAD (right reason): the hostile legacy row's RE-register reached the store …` (the pin's own right-reason message).
  - `…RE_REGISTER_door[consistent-then-householded-joiner-pair]` + `…the_REAL_writer_never_re_stamps_…` ×2 — `TypeError: … 'session_keep_id'`.
- NEW green (19): accept-control `[0z|a_b|a-b|a×64]` (4) · KB-2 control ×3 · the shape pin (HEAD control: the scanner SEES the HEAD guard) · scanner controls 8 + 2 · `TestBriefCharsetAssert::test_hostile_name_is_rejected[fixer.b]` (the store ASSERT refuses the dotted twin).

## §GATES (measured 2026-09-25)
- **ruff, main checkout (r4a working tree over `92f7091`):** `uv run ruff check .` → `All checks passed!`
- **currency, main (unbuilt world):** `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` →
  `typecheck RED_ADJUDICATED — 20 residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3` ·
  `ruff GREEN` · `pytest NOT_RUN` (by design — never a bare `--currency`, #466). **20 = r4's 20** — r4a adds no mypy
  error: every new `lorerunes.is_legal_identifier` read in r4a goes through `getattr` (the effect pin, the shape pin), so
  the `test_agent_registry.py` `attr-defined: 4` adjudication stays exact.
- **currency, lane `ref` (BUILT world, `faed272`):** `typecheck RED_ORPHANED — 11 residual(s)`, **all eleven
  `SELF-DESTRUCT`** (10 registered files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES") ·
  `ruff GREEN` → **0 real mypy errors** on the built world; = r4's 11. **#461:** every registered file is mypy-red at
  HEAD (20 residuals, all adjudicated) and self-destructs on the build — no entry discharges wrongly. The builder deletes
  BOTH entries in the build commit (unchanged from r4). `scripts/pending_contracts.yaml` edit in r4a: the
  `_comms_fakes.py` entry's COMMENT names the new shape pin beside the effect pin (no count or symbol changed).

## §SAT — satisfiability (measured 2026-09-25)
- **Reference:** adversary-r4's `my_ref_build_r4.py` verbatim (md5 matches its §A.1) with its FORK-C leg REPLACED by the
  amendment-9 shape (guard deleted AND `from lorerunes import is_blank, is_legal_identifier` at module top) and two legs
  appended (the `_REFUSAL_ID_SAMPLE_SIZE` WHY-docstring; the re-register docstring "from ANY caller, including a different
  householded principal") — `make_ref_r4a.py` → `ref_build_r4a.py`. Its r4 leg carries the `_IDENTIFIER_CHARSET_PATTERN =
  AGENT_NAME_PATTERN.pattern` rebind. So all four builder grants the brief names are IN the reference. Lane `ref`, branch
  `r4a-ref` @ `faed272`; `loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`.
- **Committed test text = graded text:** `cmp` of the four test files + `pending_contracts.yaml` main vs lane → IDENTICAL;
  `_comms_fakes.py` differs by EXACTLY the builder's granted edit (import line + the deleted `try`/`except`).
- **Lint AFTER the cleanups:** `uv run ruff check .` (lane) → GREEN (the currency gate's ruff leg); typecheck → 11
  SELF-DESTRUCT, 0 real errors (§GATES).
- **25 contract files, `-n 8`, alone:** `2978 passed, 19 skipped, 4 warnings in 315.21s` — 0 failed.
- **FULL SUITE ALONE `-n 12` (2026-09-25 04:30:35–04:41:05 EDT; launched at 24 GB under the FORK-MEM grant, lowest 18 GB;
  no other pytest on the box): `11459 passed, 62 skipped, 3 xfailed, 7 warnings in 627.58s` — 0 failed, 0 errors,
  exit 0.** Arithmetic vs r4's `11428`: +32 new ids − 1 deleted = +31 ✓.
- **§SAT-B — TWR full-suite leg (the KB-2 bound; 04:41:20–04:51:31, launched 24 GB, lowest 16 GB):** reference + TWR →
  **`11459 passed, 62 skipped, 3 xfailed` — exit 0**: the reworded-class twin survives everything, exactly as the threat
  model states, and the KB-2 control (`…REWORDED_or_ASSEMBLED_charset_is_NOT_named[reworded-class-TWR]`) is green on it.

## §CANDIDATES — doors noticed OUTSIDE §W (surfaced, NOT pinned — amendment-9 STOP-rule; the sidecar rules)
- **C-1 · one legal corpus.** `_VALID_IDENTIFIERS` (`test_comms_schema.py`, brief store-ASSERT accept leg) and
  `test_agent_registry.py::…::test_pattern_accepts_legal_names`'s local list are two more legal corpora beside the new
  `_LEGAL_IDENTIFIER_WITNESSES` (§FORKS R-B). Recommend: fold them into it (additive params, no DUAL) in whichever
  wave next touches those pins.
- **C-2 · RS1's other axis — a DIFFERENT KEEP.** Row 1 pins `(alice, K) → (bob, K)` as ruled. A build that re-stamps
  `scope` only when the caller's keep DIFFERS (`(alice, K) → (alice, K2)` or `(bob, K2)`) is not observed by any r4a
  row (construction — not built or run). Ruling §2.2 row 2 covers it ("leaves … scope UNTOUCHED"); one more sequence
  would pin it.
- **C-3 · RS1 is pinned at the REGISTRY seam** (KP-RS1's shape, as ruled). The end-to-end tool door — a householded
  joiner calling `lore_comms register` with ANOTHER principal's agent name in the shared session — is not driven by any
  pin; whether `_comms_register` / the capability check refuses earlier is unmeasured by me.
- **C-4 · the PX2 sample-size detector is phrase-bound** (`first N` / `N … shown` / `showing N`) — stated in the pin's
  docstring as its BOUND; the birth-value leg is the ∀ half and is what kills PX2.
- **C-5 · the shape pin's reach is ONE file** (`_comms_fakes.py`, by ruling). A second test double adopting the
  predicate behind a guard would be outside it; the effect pin's reach is likewise the one fake. Named here so it is a
  known reach, not a hidden constant.

## §INSTRUMENTS (pasted VERBATIM — scratch-only; `scripts/` holds only `pending_contracts.yaml` in my writable set)
Root: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5c239db8-6765-4361-80d9-ccabf55a4d76/scratchpad/inst`.
- `my_ref_build_r4.py` = adversary-r4's reference, copied from its surviving scratch; **md5 `3e419c754445…` = the md5 adversary-r4 §A.1 states for its full file** — verbatim, pasted there (`REPORT-adversary-63c-i-a-r4.md` §A.1 @ `86379a4`).
- `ref_build_r4a.py` (md5 `e43320e8e1ec…`) is GENERATED from it by `make_ref_r4a.py` below (one leg replaced, two appended). `red_diff4.py` = adversary-r4 §A.6 verbatim (md5 `7b80fed08299…`).

### `make_ref_r4a.py`
```python
"""contract-63c-i-a-r4a: derive ref_build_r4a.py from adversary-r4's my_ref_build_r4.py (verbatim base) by
replacing its FORK-C leg with the amendment-9 MP-R4-5 shape and appending the builder's two docstring edits."""

from pathlib import Path

INST = Path(__file__).parent
src = (INST / "my_ref_build_r4.py").read_text()
old_fake = '''edit(
    FAKES,
    "        try:\\n"
    "            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\\n"
    "        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate\\n"
    "            return None\\n"
    "        return is_legal_identifier\\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\\n\\n"
    "        return is_legal_identifier\\n",
)'''
assert src.count(old_fake) == 1, src.count(old_fake)
new_fake = '''# r4a (contract-63c-i-a-r4a): the builder's granted edit AS RULED by amendment-9 MP-R4-5 — delete the guard
# AND import the predicate at MODULE TOP (the restored presence pin demands exactly that shape).
edit(
    FAKES,
    "        try:\\n"
    "            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\\n"
    "        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate\\n"
    "            return None\\n"
    "        return is_legal_identifier\\n",
    "        return is_legal_identifier\\n",
)
edit(FAKES, "from lorerunes import is_blank\\n", "from lorerunes import is_blank, is_legal_identifier\\n")'''
src = src.replace(old_fake, new_fake)
src += '''
# ---- r4a (contract-63c-i-a-r4a): the builder's two remaining granted DOCSTRING edits ------------------------
edit(
    PRINCIPALS,
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\\n",
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\\n"
    "#: WHY a bound at all: the refusal is read by an operator at cutover, and an unbounded id list on a large\\n"
    "#: half-applied store would bury the remedy; the FULL count is always stated beside it, so nothing is\\n"
    "#: lost. The slice and any prose describing it READ this constant at call time — never restate it.\\n",
)
edit(
    AGENTS,
    "                re-register does NOT re-stamp it (mint-once-on-create; owner is set at\\n"
    "                birth, and a running agent's owner is not rewritten mid-session).\\n",
    "                re-register does NOT re-stamp it — from ANY caller, including a different\\n"
    "                householded principal (mint-once-on-create; owner is set at birth, and a\\n"
    "                running agent's owner is not rewritten mid-session).\\n",
)
print("r4a legs applied (fake module-top import, sample-size docstring, re-register docstring)")
'''
(INST / "ref_build_r4a.py").write_text(src)
```

### `wbs_r4a.py` (wrong builds + DECLARED expected-RED sets, written before any run)
```python
"""contract-63c-i-a-r4a — wrong builds applied ON TOP of my reference (lane `ref`, branch r4a-ref =
adversary-r4's my_ref_build_r4.py VERBATIM base + the amendment-9 MP-R4-5 fake shape + the builder's two
docstring edits; see make_ref_r4a.py). Bodies are adversary-r4's (REPORT-adversary-63c-i-a-r4.md §A.2),
re-anchored where my reference differs (the fake now imports the predicate at MODULE TOP).

Usage: uv run --no-project python wbs_r4a.py <lane> <WB-id> [--declared]
  --declared  print the DECLARED expected-RED node ids, resolved against collected_r4a.txt (the
              `pytest --collect-only -q` output of files5.txt on r4a-ref, taken BEFORE any wrong-build run).
Each edit asserts its anchor occurs exactly once (a no-op mutation is a failed setup — #194).
A DECLARED set of [] is the prediction that the build SURVIVES the contract.
"""

import sys
from pathlib import Path

INST = Path(__file__).parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
FLOOR = "test_floor_calibration_schema.py"

SKIP_MUT = "test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier"
SKIP_CORPUS = "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus"
FAKE_EFFECT = "test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists"
FAKE_SHAPE = "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
REREG_PARITY = "test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door"
RS1_PIN = "test_the_REAL_writer_never_re_stamps_a_stamped_row_from_a_DIFFERENT_householded_principal"
JOINER = "consistent-then-householded-joiner-pair"
CAP = "a" * 64

DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # row 1 (MP-R4-1 / -6)
    "RS1": [(REG, [REREG_PARITY, JOINER]), (REG, [RS1_PIN])],  # real re-stamps: parity AND the absolute pin
    "FX2": [(REG, [REREG_PARITY, JOINER])],  # fake re-stamps: parity
    "RS1FX2": [(REG, [REREG_PARITY, JOINER]), (REG, [RS1_PIN])],  # BOTH re-stamp: fake == real; absolute reds
    # row 2 (MP-R4-3) + row 7 KB-1
    "G1": [(REG, [SKIP_MUT, f"[{CAP}]"]), (REG, [SKIP_CORPUS])],  # narrowing conjunct: the cap witness
    "G2": [(REG, [SKIP_CORPUS])],  # reworded dotted widening: "fixer.b" is looked up
    # rows 3 + 4 (MP-R4-4 / -5)
    "FXg": [(REG, [FAKE_EFFECT]), (REG, [FAKE_SHAPE])],  # guard kept, submodule import inside the try
    "FXf": [(REG, [FAKE_SHAPE])],  # guard kept with a NON-silent private-regex fallback (effect pin blind)
    "FXf2": [(REG, [FAKE_SHAPE])],  # module-top import KEPT and a guarded call-time fallback beside it
    "X3b": [(REG, [FAKE_EFFECT]), (REG, [FAKE_SHAPE])],  # the originally ruled guard spelling
    "X3d": [(REG, [FAKE_EFFECT])],  # getattr(…, None) with the module-top import kept: shape pin blind
    # row 5 (MP-R4-7) + row 8 R-4
    "PX2": [(GOV, [RQ51, "perturbed-bound"])],
    "MP2DEF": [(GOV, [RQ51, "perturbed-bound"])],  # CONTROL: def-time capture (R-4's failure text)
    # row 6 (R-1): the deleted premise pin's builds — killed by the packet-07 pins
    "R5": [(FLOOR, ["test_this_slice_contains_neither_a_relation_table_nor_a_sequence"]),
           (FLOOR, ["test_every_table_definition_is_IF_NOT_EXISTS"])],
    "R5b": [(FLOOR, ["test_this_slice_contains_neither_a_relation_table_nor_a_sequence"]),
            (FLOOR, ["test_every_table_definition_is_IF_NOT_EXISTS"])],
    # row 7 KB-2: the bound — must SURVIVE
    "TWR": [],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (INST / "collected_r4a.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

HELPER_RETURN = "        return is_legal_identifier\n\n    @staticmethod\n    def _refuse_what_the_writer_refuses("
TOP_IMPORT = "from lorerunes import is_blank, is_legal_identifier\n"
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"
REREG_ANCHOR = "        # status resets to active unconditionally (retired already excluded above).\n"


def guard(except_line: str, *, import_line: str, fallback: str, keep_top_import: bool = False) -> None:
    if not keep_top_import:
        edit(FAKES, TOP_IMPORT, "from lorerunes import is_blank\n")
    edit(FAKES, HELPER_RETURN,
         "        try:\n" + import_line + except_line + fallback + HELPER_RETURN)


PLAIN_IMPORT = "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n"


def fx2() -> None:
    edit(FAKES, REREG_ANCHOR,
         "        if self.db.scopes.get(agent_id) is not None and session_keep_id is not None:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n" + REREG_ANCHOR)


def rs1() -> None:
    edit(AGENTS,
         "        new_model = model if model is not None else existing.model\n",
         "        if existing_row.get(\"scope\") is not None and owner_principal_id is not None:\n"
         "            await self._query(\n"
         "                f\"UPDATE type::record('{AGENT_TABLE}', $rid) SET owner_principal = $owner, \"\n"
         "                \"scope = $scope\",\n"
         "                {\"rid\": agent_id, \"owner\": RecordID(PRINCIPAL_TABLE, owner_principal_id),\n"
         "                 \"scope\": keep_scope(session_keep_id)},\n"
         "            )\n"
         "        new_model = model if model is not None else existing.model\n")


if WB == "RS1":
    rs1()
elif WB == "FX2":
    fx2()
elif WB == "RS1FX2":
    rs1()
    fx2()
elif WB == "G1":
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         "            or len(attribution) > 32  # a 'cheap' private cap on the read budget\n"
         "        ):\n")
elif WB == "G2":
    edit(SERVER, GATE,
         "        if attribution is None or not (\n"
         "            AppContext._is_comms_charset_legal(attribution)\n"
         "            or re.fullmatch(r\"[a-z0-9]+\\.[a-z0-9]+\", attribution)  # dotted service names too\n"
         "        ):\n")
elif WB == "FXg":
    guard("        except ImportError:\n",
          import_line="            from lorerunes.identifiers import is_legal_identifier  # noqa: PLC0415\n",
          fallback="            return None\n")
elif WB == "FXf":
    guard("        except ImportError:  # robustness: fall back to the rule's text\n",
          import_line=PLAIN_IMPORT,
          fallback=("            import re  # noqa: PLC0415\n\n"
                    "            return lambda value: re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"))
elif WB == "FXf2":
    guard("        except ImportError:  # robustness: fall back to the rule's text\n",
          import_line="            from lorerunes import is_legal_identifier as _fresh  # noqa: PLC0415\n",
          fallback=("            import re  # noqa: PLC0415\n\n"
                    "            return lambda value: re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"),
          keep_top_import=True)
elif WB == "X3b":
    guard("        except ImportError:\n", import_line=PLAIN_IMPORT, fallback="            return None\n")
elif WB == "X3d":
    edit(FAKES, HELPER_RETURN,
         "        import lorerunes  # noqa: PLC0415\n\n"
         "        return getattr(lorerunes, \"is_legal_identifier\", None)\n\n"
         "    @staticmethod\n    def _refuse_what_the_writer_refuses(")
elif WB == "PX2":
    edit(PRINCIPALS, "                \"half-applied store; \"\n",
         "                \"half-applied store (first 10 ids shown); \"\n")
elif WB == "MP2DEF":
    edit(PRINCIPALS,
         "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n"
         "    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
         "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n"
         "    principal_store: PrincipalStore,\n    sample_size: int = _REFUSAL_ID_SAMPLE_SIZE,\n"
         ") -> MigrateGovernedResult:")
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:sample_size]")
elif WB in ("R5", "R5b"):
    relation = "\"holds\", LEASE_TABLE, TASK_TABLE" if WB == "R5" else "TO_RELATION, MESSAGE_TABLE, AGENT_TABLE"
    edit(SCHEMA,
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         f"    statements.append(_define_relation_table({relation}))\n"
         "    return statements\n")
elif WB == "TWR":
    edit(AGENTS, "class InvalidAgentIdentityError(AgentRegistryError):",
         "_LEGACY_NAME_RE = re.compile(r\"^[0-9a-z][0-9a-z_-]{0,63}$\")  # reworded class (KB-2)\n\n\n"
         "class InvalidAgentIdentityError(AgentRegistryError):")
    edit(AGENTS, "import logging\nimport secrets\n", "import logging\nimport re\nimport secrets\n")
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### `run_lane_r4a.sh` (declare-then-diff lane driver)
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4a lane driver (adversary-r4's run_lane4.sh, re-pathed): for each WB, reset the lane to
# r4a-ref, resolve the DECLARED expected-RED set from collected_r4a.txt (collect-only on r4a-ref, taken BEFORE
# any wrong-build run), apply the build, assert provenance, run the 25 contract files (-n 8, ONE pytest session
# at a time, memory watchdog), diff observed vs declared BOTH ways from junit, restore.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5c239db8-6765-4361-80d9-ccabf55a4d76/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5c239db8-6765-4361-80d9-ccabf55a4d76/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f r4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
  [ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "$WB: LANE DIRTY after reset — abort"; exit 2; }
  uv run --no-project python "$INST/wbs_r4a.py" "$LANE" "$WB" --declared | sort > "$INST/wb_${WB}.declared" \
    || { echo "$WB: declaration failed"; exit 2; }
  uv run --no-project python "$INST/wbs_r4a.py" "$LANE" "$WB" || { echo "$WB: APPLY FAILED (no-op edit?)"; exit 2; }
  [ -n "$(git status --porcelain --untracked-files=no)" ] || { echo "$WB: build left the lane CLEAN — mutation did not land"; exit 2; }
  "$INST/run_pytest.sh" "$LANE" "wb_${WB}" 8 "$INST/files5.txt" > "$INST/wb_${WB}.driver.log" 2>&1
  uv run --no-project python - "$INST/wb_${WB}.xml" > "$INST/wb_${WB}.observed" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        print(f"{case.get('classname', '')}::{case.get('name')}")
PY
  sort -o "$INST/wb_${WB}.observed" "$INST/wb_${WB}.observed"
  uv run --no-project python - "$INST/wb_${WB}.declared" "$INST/wb_${WB}.observed" <<'PY' > "$INST/wb_${WB}.diff"
import sys
declared = {l.strip() for l in open(sys.argv[1]) if l.strip()}
observed = {l.strip() for l in open(sys.argv[2]) if l.strip()}
def key(node):  # collect "path.py::Class::test[p]" / junit "pkg.mod.Class::test[p]" -> "Class::test[p]"
    parts = node.split("::")
    prefix = parts[-2] if len(parts) >= 2 else ""
    cls = "" if prefix.endswith(".py") else prefix.split(".")[-1]
    return f"{cls if cls[:1].isupper() else ''}::{parts[-1]}"
dk = {key(d): d for d in declared}
ok = {key(o): o for o in observed}
unexpected = sorted(set(ok) - set(dk))
still_green = sorted(set(dk) - set(ok))
print(f"declared={len(dk)} observed_red={len(ok)} unexpected_red={len(unexpected)} declared_still_green={len(still_green)}")
for u in unexpected: print("  UNEXPECTED RED:", ok[u])
for s in still_green: print("  DECLARED BUT GREEN:", dk[s])
PY
  echo "== $WB :: $(tail -1 "$INST/wb_${WB}.driver.log") :: $(head -1 "$INST/wb_${WB}.diff")"
done
git checkout -q -f r4a-ref && git clean -fdq -e REPORT-sidecar-63c.md
```

### `run_pytest.sh` (one pytest session, memory watchdog, provenance)
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4a: ONE pytest session in <lane> with a memory watchdog (kills ITS OWN pytest by PID when
# MemAvailable < 12 GiB), provenance asserted, junit + log written under inst/.
# Usage: run_pytest.sh <lane-dir> <label> <workers> [files-list-file | FULL]
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5c239db8-6765-4361-80d9-ccabf55a4d76/scratchpad/inst
LANE=$1; LABEL=$2; WORKERS=$3; FILES=${4:-FULL}
cd "$LANE" || exit 2
if [ "$LANE" != /home/ejprice/PycharmProjects/lore ]; then
  uv run python -c "import loremaster,pathlib; assert pathlib.Path(loremaster.__file__).resolve().is_relative_to('$LANE'), loremaster.__file__; print('loremaster.__file__ =', loremaster.__file__)" \
    || { echo "PROVENANCE FAILED"; exit 2; }
fi
if [ "$FILES" = FULL ]; then TARGETS=""; else TARGETS=$(cat "$FILES"); fi
echo "state: $(git status --porcelain | wc -l) dirty; HEAD $(git rev-parse --short HEAD); avail $(free -g | awk 'NR==2{print $7}') GiB; $(date '+%F %T')"
uv run pytest -n "$WORKERS" -q -p no:cacheprovider --junitxml="$INST/${LABEL}.xml" $TARGETS > "$INST/${LABEL}.log" 2>&1 &
PID=$!
low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 12 ]; then echo "WATCHDOG: MemAvailable ${avail} GiB < 12 — killing pytest PID $PID"; kill "$PID"; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc lowest MemAvailable: ${low} GiB; $(date '+%F %T')"
tail -1 "$INST/${LABEL}.log"
```

### one-off commands (verbatim)
```bash
# lanes: ./scripts/scratch_copy.sh $S/ref ; ./scripts/scratch_copy.sh $S/head   (both rc=0, provenance asserted)
# ref:   cd $S/ref && git checkout -b r4a-tests && git commit (r4a tests) ; python3 make_ref_r4a.py ; uv run --no-project python ref_build_r4a.py $S/ref ; git checkout -b r4a-ref && git commit ; (later) copy the final main test text in + commit faed272
# head:  cd $S/head && git checkout HEAD -- loremaster/tests        (= 92f7091 exactly: r4 tests, unbuilt production)
# files5.txt = adversary-r4 files4.txt (24) ∪ loremaster/tests/test_floor_calibration_schema.py  (25 files)
# declaration universe (ref, BEFORE any wrong-build run): uv run pytest --collect-only -q -p no:cacheprovider $(cat files5.txt) | awk '/::/' > collected_r4a.txt   # 2997 ids
# reference contract run: run_pytest.sh $S/ref ref_contract 8 files5.txt
# lane: run_lane_r4a.sh RS1 FX2 RS1FX2 G1 G2 FXg FXf FXf2 X3b X3d PX2 MP2DEF R5 R5b
# final-text re-proof (ref @ faed272): per WB: git checkout -f r4a-ref; wbs_r4a.py $S/ref WB; uv run pytest -q -p no:xdist loremaster/tests/test_agent_registry.py -k 'never_silently_skips or predicate_import_is_at_module_top or never_re_stamps_a_stamped_row or householded-joiner'  (PX2: test_agent_governance_63c_i_a.py -k perturbed)
# RED: run_pytest.sh /home/ejprice/PycharmProjects/lore red_r4a 8 files5.txt ; run_pytest.sh $S/head red_r4 8 files5.txt ; python3 red_diff4.py red_r4a.xml red_r4.xml
# currency: uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff   (main; and in $S/ref @ faed272)
# SAT full suite (ALONE, -n 12): run_pytest.sh $S/ref full_sat 12 FULL ; TWR: git checkout -f r4a-ref; wbs_r4a.py $S/ref TWR; run_pytest.sh $S/ref full_twr 12 FULL
```
