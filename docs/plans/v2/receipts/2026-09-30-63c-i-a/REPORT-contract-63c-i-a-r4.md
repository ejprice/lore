# REPORT-contract-63c-i-a-r4 — the 63c-i-a contract, revision 4 (amendment-6 §W worklist, the LAST pre-build round)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations — amendment-6 §W items 1–6 + amendment-7 (FORK-D riders) in ONE commit. **SAT: FULL SUITE ALONE `-n 12` on the reference → `11428 passed, 62 skipped, 3 xfailed` — 0 failed, exit 0** (measured 2026-09-24 22:57–23:08 EDT); ruff clean + typecheck 0 errors AFTER the lint cleanups and the builder's granted edits (FORK-C guard deletion + the `_IDENTIFIER_CHARSET_PATTERN` rebind); built world = exactly 11 SELF-DESTRUCTs.
- **Mutation:** 10/10 wrong builds PROOF HELD, each on exactly its declared pin(s), 0 unexpected reds — X1, X2, X3, X3b (the RULED guard spelling), X3c (bare `except:`), X3d (`getattr(…, None)`), R5, FX1, TW (rebind forgotten), SLUGDRIFT (exempt text drifts) (§ITEMS).
- **RED@HEAD (main, 22 files):** 0 r3-greens turned red; 7 new reds, all right-reason; the text pin names exactly `agents.py:161` + `surreal_schema.py:490`, not `config.py` (§RED).
- **deviations:** DV-1 a full `--currency` ran pytest at `-n auto` concurrently with my lane (#466/brief breach; verdict unused) · DV-2 first lane on a stale test copy, discarded; my `pkill -f` self-matched (#228) · DV-3 declare-then-diff driver instead of `mutation_proof.py` (multi-edit) · DV-4 FORK-E reading (i) picked with (ii) written.
- **Packages considered:** stdlib `ast`/`re`/`importlib`/`types` (read at use); `pytest.MonkeyPatch.setattr`/`delattr` (the perturbation + unimportability probes); no production mechanism specified (tests only).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 17 new test-substrate symbols, all dispositioned (§DRY): 1 EXTENDED-in-spirit (re-register parity drivers over the r3 harness), REUSED `parse_production_trees` + `assert_scan_reached_every_member`, the rest HAND-ROLLED with the query that proves the search.
- **Graded:** n/a — this is the contract author's report, not a verdict on another agent's artifact.
- **decisions-needed:** FORK-E only if amendment-6 R-3 meant reading (ii) (a newline in the refusal text). Candidate KNOWN BOUNDS KB-1…KB-5 for the sidecar (not pinned — STOP-rule). Builder brief rows: `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` (from `lorerunes`) · delete the fake's guard in REFACTOR (the MP-3 effect pin reds until then; "import at module top" also satisfies it) · delete BOTH `pending_contracts.yaml` entries with the build · the `_REFUSAL_ID_SAMPLE_SIZE` docstring states WHY its value (R-3).
- **receipt pointers:** §FORKS (D ruled, E picked) · §ITEMS · §DUAL (E1–E2) · §DRY · §GATES · §RED · §SAT · Candidate KNOWN BOUNDS · Deviations · §INSTRUMENTS. `REPORT-contract-63c-i-a-r3.md` §CORRECTION NOTE (R-1/R-2/R-5).

## §FORKS (written BEFORE acting on them — brief §ESCALATION)

### FORK-D — item 1's ruled charset TEXT also matches an UNRELATED production constant (`config.SLUG_PATTERN`)
- **Ruling text (amendment-6 STOP-rule §2):** *"the charset text `[a-z0-9][a-z0-9_` occurs in exactly ONE string
  constant in the workspace: `lorerunes`' `AGENT_NAME_PATTERN`. Every other … raw literal carrying it is a private
  decision → RED naming `file:line`."*
- **Measured 2026-09-24 at `3327770` (awk, bare substring over every `git ls-files '*.py'` outside `*/tests/`):**
  `loremaster/loremaster/agents.py` (`AGENT_NAME_PATTERN`, moves in i-a) · `loremaster/loremaster/store/surreal_schema.py`
  (`_IDENTIFIER_CHARSET_PATTERN`, the builder's one-line rebind) · **`loremaster/loremaster/config.py`
  (`SLUG_PATTERN = r"^[a-z0-9][a-z0-9_]*$"` — the PROJECT-SLUG rule: no hyphen, unbounded; a different policy,
  operator directive 2026-07-03 task #32)** · `scripts/c3_wrongbuild_driver.py` (a wrong-build string; outside the
  scan's reach, `include_scripts=False`, same as the r3 AST scan). The sidecar's sweep named only the first two.
- **Consequence of the literal reading:** the text pin is RED on a CORRECT build (it names `config.py`), so the SAT
  receipt ("0 failed") is impossible, and the builder has no granted edit that fixes it — the pin would be a gate that
  refuses honest code (the switched-off-scanner law).
- **Reading (a) — my recommendation, what I built provisionally:** keep the ruled KEY (the substring — it is what
  catches the drifted-dot twin `[a-z0-9][a-z0-9_.-]`) and ALLOWLIST THE SAFE by evidence: the safe set is (i) the ONE
  `AGENT_NAME_PATTERN = re.compile(<const>)` definition inside `lorerunes`, and (ii) `config.SLUG_PATTERN`, exempted by
  (file, binding, EXACT text) and carrying an EVIDENCE leg that it decides a DIFFERENT language (it rejects the legal
  agent name `fixer-b`, which `is_legal_identifier` accepts) — so if its text drifts toward the agent pattern the
  exemption stops matching and the pin reds (re-adjudicate). Re-open trigger stated in the pin.
- **Reading (b):** lengthen the key so the second class must continue past `_` (`[a-z0-9][a-z0-9_` + a char ≠ `]`):
  no exemption list, but a pasted twin that DROPS the hyphen (`[a-z0-9][a-z0-9_]{0,63}`) escapes — a narrower gate
  than ruled.
- **Reading (c):** literal — ask the builder to change `SLUG_PATTERN` (a production edit to an unrelated policy; not
  granted, and wrong on the merits).
- **Status:** RULED — amendment-7 (`3a2975c`) chose reading (a) with riders, all applied: the exemption is keyed on
  (file, binding, EXACT text); the evidence is computed LIVE inside the same pin, in BOTH directions (`fixer-b`:
  agent ✓ / slug ✗; `"a" * 65`: slug ✓ / agent ✗); a drifted text turns the constant PRIVATE (RED → re-adjudicate);
  a convergence failure says "design fork → one `lorerunes` predicate (the `is_blank` precedent)". The separate
  evidence test I had first written was folded INTO the pin (the ruling: "riders of the same pin, not a second pin").

### FORK-E — amendment-6 R-3's "the reason names the FULL count on a separate line" (two readings)
- **Reading (i), what I pinned:** the FULL count is asserted on its own, INDEPENDENTLY of the id sample (a separate
  assertion — `re.search(rf"\b{trap_count}\s+(?:agent\s+)?rows?\b", reason)` beside the `len(named) ==
  min(bound, count)` assertion), so the reader loses nothing at any bound. Already true of r3's pin; r4's
  `perturbed-bound` population exercises it at 18 rows / 3 ids.
- **Reading (ii):** the refusal's TEXT must put the count on its own LINE (a `\n` in the reason). That would be a
  new production-shape requirement no prior ruling states, and the reference builds (r3 author's and adversary-r3's)
  put count and ids on one line.
- **Pick:** (i) — no new pin. Flagged, not escalated as blocking: (ii) is a strict superset a later ruling can add as
  one assertion. **Decision needed only if the sidecar meant (ii).**

## Capability check (brief-base §4)
- Reachable and used (measured 2026-09-24): `Read`/`Edit`/`Write`, `git`, `uv run pytest/ruff`, `./scripts/typecheck.sh`,
  `./scripts/scratch_copy.sh`, `scripts/pending_contract_gate.py`, the lore MCP (`register`/`heartbeat`/`send`,
  `lore_search`), the test store `ws://127.0.0.1:18000`. `:18500` and the production TEI embedder were never touched.
- **grep/rg are hook-blocked (#473)** — every textual sweep here is `awk` over `git ls-files` (bare substring), said per
  the dogfood protocol: the charset-text sweep (FORK-D), the old-pin-name sweep, the D7 comment locate.
- Store reference `docs/reference/surrealdb-31-capabilities.md` read first (whole file). No store/DDL mechanism is
  specified here; the pins lean only on facts the r3 contract already cites (§1.1, §1.4, §2 explicit projection).

## §ITEMS — amendment-6 §W (+ amendment-7), measured 2026-09-24
Wrong builds applied ON TOP of the r4 reference (tag `r4-ref`, §SAT) by `r4_wbs.py`; DECLARED expected-RED ids resolved
from `collected_r4.txt` (`pytest --collect-only` over the 22-file run set → **2601 ids**) BEFORE any wrong-build run,
diffed BOTH ways from junit by `run_lane_r4.sh` (§INSTRUMENTS). Every run: the 22 files, `-n 8`, one pytest session.

| # | class | pin (file::test) | wrong build killed | mutation receipt (tail · declared/observed) |
|---|---|---|---|---|
| 1 | GATING | `test_agent_registry.py::TestTheIdentifierCharsetTextHasOneSpelling63cIA::test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition` (static ∀, threat model in the section header + docstring + failure text; exact-text exemption + live 2-direction evidence, amendment-7) + 9 positive / 4 negative synthetic controls (`test_POSITIVE_CONTROL_every_pasted_spelling_is_named[…]` incl. `drifted-dot-twin-N1c-X1`, `test_POSITIVE_CONTROL_a_second_spelling_INSIDE_lorerunes_is_named_too`, `test_NEGATIVE_CONTROL_the_safe_shapes_are_not_private[dot-pattern-read-is-the-safe-shape, …]`) | **X1** (also), **TW** (builder forgets the `_IDENTIFIER_CHARSET_PATTERN` rebind), **SLUGDRIFT** (the exempt text drifts to admit `-`) | X1 `3 failed, 2575 passed` 3/3 · TW `1 failed, 2577 passed` 1/1 · SLUGDRIFT `1 failed, 2577 passed` 1/1 — all PROOF HELD |
| 1 | GATING | `TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[fixer-b]`, `[wave7]` (BASELINE one read → mutation zero reads) + `…::test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus` (∀ corpus, zero reads, positive control first) | **X1** (the gate decides with a private DRIFTED regex) | in X1's 3/3 above (both mutation legs + the text pin) |
| 1 | GATING | `_IDENTIFIER_DECISION_CONSUMERS` comment states its reach (a HAND-LIST, the effect twin; names the text pin as the ∀ and the SKIP-gate class) | — (prose rider) | n/a |
| 2 | GATING | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]` (constant patched to 3 — or 4 if the build chose 3 — seed bound + 15; full count named, EXACTLY the patched number of ids); positive-`int` (non-`bool`) assert; no ceiling (R-3) | **X2** (constant 10 + restated literal `[:10]`) | `1 failed, 2577 passed` 1/1 PROOF HELD |
| 3 | GATING | `test_agent_registry.py::test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` — EFFECT pin (predicate `delattr`'d → ∀ hostile corpus × {name, session} no fake register succeeds; HEAD CONTROL: the guard visibly skips); REPLACES the FORK-C spelling pin (DUAL) | **X3** `except Exception:`, **X3b** the RULED spelling `except ImportError:`, **X3c** bare `except:`, **X3d** `getattr(lorerunes, …, None)` | each `1 failed, 2577 passed` 1/1 PROOF HELD (4/4) |
| 4 | NON-GATING | `test_message_enforcement_63b_ii_a.py::TestTheGovernedPopulationSetGrows::test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see` — "unswept" DEFINED as *emits a relation the sweep cannot see*, over EVERY derived generator, pinned to ∅ (the adversary's "better still" form); anti-vacuity on the sweep | **R5** (un-ENFORCED `holds(lease → task)` inside `_lease_statements`) | `1 failed, 2577 passed` 1/1 PROOF HELD |
| 5 | NON-GATING | `test_agent_registry.py::TestTheFakeRegistryMirrorsTheWriter63cIA::test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[alpha-then-credentialed | consistent-then-owner-only | consistent-then-keep-only]` — second-call outcome class + the three stamps, real vs fake, plus ABSOLUTE expectations | **FX1** (the fake heals an unstamped row on re-register) | `1 failed, 2577 passed` 1/1 (`[alpha-then-credentialed]`) PROOF HELD |
| 6 | PROSE | MP-P1 `test_ddl_write_target_coverage_124.py::_emit` docstring ("whenever the generator has a `dim` parameter") · R-1 + R-2 + R-5 in an APPENDED correction note in `REPORT-contract-63c-i-a-r3.md` (header line "corrected by r4" + the pasted `r3b_files.txt`, 22 files, recovered from the r3 author's scratchpad) · R-5 also as one sentence in `_governed_contract.py`'s in-place D7 DUAL comment | — | n/a |

**Lane totals:** reference over the 22 files `2578 passed, 23 skipped` (0 failed); **10/10 wrong builds PROOF HELD — every
declared pin red, 0 unexpected reds, 0 declared-still-green** (`lane_r4.log`, §INSTRUMENTS). ⚠ A first lane run is
DISCARDED: it ran a test copy synced BEFORE amendment-7's riders (see deviations); only the final-tree run is cited.

## §DUAL — every pin deleted, inverted or re-keyed (an in-place DUAL comment sits at each)
| # | what changed | virtue it carried | where the virtue now lives |
|---|---|---|---|
| E1 | `test_agent_registry.py::test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists` (AST scan for an `except` NAMING `ImportError`) **DELETED** (amendment-6 MP-3: replaced, not kept beside) | (a) the guard must not outlive its premise; (b) HEAD anti-vacuity — the scan must SEE today's guard | (a) `test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` (EFFECT: reds X3/X3b/X3c/X3d — the old pin red only X3b); (b) its HEAD CONTROL branch (the hostile `"fixer-b\n"` visibly registers while the predicate is absent). References repointed: `_comms_fakes._shared_identifier_predicate` docstring, `pending_contracts.yaml` comment. |
| E2 | r4-draft `test_every_exempt_charset_constant_decides_a_DIFFERENT_language` (never committed) folded INTO the text pin | evidence for the exemption | `_assert_every_exemption_is_a_DIFFERENT_language` called by the text pin (amendment-7: "riders of the same pin, not a second pin"), now two-direction + exact-text |
| — | ADDITIVE, no DUAL needed: R-Q5-1 `[perturbed-bound]`, the SKIP-gate class, the text-pin class, the re-register parity rows, the MP-4 premise pin | — | — |

## §DRY — reuse ledger (brief-base §6), all new symbols are TEST substrate
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_classify_charset_constants`, `_is_charset_carrying_constant` | `lore_search("AST scan of production string constants containing a regex text, classify literal sites")` | only a #210 charset report; no constant-text scanner | HAND-ROLLED — the existing `_pattern_decision_sites` is keyed on the NAME (by design; the ruling says this pin is keyed on the TEXT). Reach reuses `parse_production_trees` + `assert_scan_reached_every_member` (REUSED). |
| `_assigned_binding` | `lore_search("helper returning the Name an assignment binds a value node to …")` + a wider-budget variant | no helper (`_watched_pattern_names` follows re-bindings of a watched name — a different question) | HAND-ROLLED (6 lines) |
| `_LookupCountingRegistry`, `_traffic_line_lookups` | `lore_search("spy agent registry counting get_agent lookups in tests")` + a wider variant | no counting spy (`FakeAgentRegistry` resolves; a counter needs a registry that resolves nobody) | HAND-ROLLED — KP-X1's shape (adversary-r3 §A.7) promoted into the contract |
| `_RE_REGISTER_SEQUENCES`, `_real_re_register_outcome`, `_fake_re_register_outcome` | (same class as the r3 parity helpers) | `_real_outcome`/`_fake_outcome` exist but read ONE register | EXTENDED in spirit, not forked: same harness (`_real_registry`, `_agent_row_count`) and stamp read-back shape; a two-call sequence needs its own driver |
| `_IDENTIFIER_CHARSET_TEXT`, `_CHARSET_DEFINITION_BINDING`, `_UNRELATED_CHARSET_POLICIES`, `_AGENT_ONLY_WITNESS`, `_EXEMPT_ONLY_WITNESS`, `_SYNTHETIC`, `_CONFIG`, `_FAKE_SKIP_HEAD_CONTROL`, `_assert_every_exemption_is_a_DIFFERENT_language` | n/a — constants/witnesses of the ruled pins | — | HAND-ROLLED; the key is asserted to occur in the LIVE `AGENT_NAME_PATTERN.pattern` (a drifted rule reds the key) |

## §GATES (main checkout, measured 2026-09-24, r4 working tree over HEAD `2919ac4`)
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → `Found 20 errors in 10 files` (all missing-seam, test tree): r3's 17 + 3 net new — `test_agent_registry.py` attr-defined 3 → 4 (the SKIP-gate mutation leg reads `lorerunes.is_legal_identifier`; the registry count re-adjudicated in `pending_contracts.yaml` with its reason) and 2 more `session_keep_id` call-args (the re-register rows; covered by the entry's `missing_symbols: ["register.session_keep_id"]`).
- `pending_contract_gate.py --currency --legs typecheck,ruff` → **typecheck RED_ADJUDICATED — 20 residual(s), owned by `packet-63c-i-a-contract-r2` · `packet-63c-i-a-contract-r3`** · **ruff GREEN** · pytest NOT_RUN (the manifest runs it at `-n auto`, which #466 forbids — §RED is this revision's pytest instrument, as r3).
- **Built world (#461):** on `r4-ref` typecheck is clean (0 errors) and currency shows **exactly 11 SELF-DESTRUCTs** (10 registered files + the `lorerunes.is_legal_identifier` symbol) — both entries discharge with the build, none early.

## §RED — main checkout, tests only, production at HEAD `2919ac4` (= `3327770`'s production; `git diff --stat 3327770 2919ac4 -- loremaster lorerunes lorescribe loresigil scripts` is EMPTY). Measured 2026-09-24.
- Run set: the 22 files of `r3b_files.txt` (pasted in the r3 correction note) — it contains every file r4 touched.
- **r4 tests (main):** `153 failed, 2422 passed, 23 skipped, 3 errors` · **r3 tests, SAME production** (scratch at `a71ef32`,
  provenance below): `146 failed, 2406 passed, 23 skipped, 3 errors` — which also REPRODUCES r3 §RED's own r3b numbers
  verbatim (R-2's claim is now re-runnable).
- Diff (`red_diff_r4.py`, §INSTRUMENTS): **GREEN on r3 turned RED on r4: 0.** NEW red ids: **7**, each right-reason:
  `R_Q5_1[perturbed-bound]` → `AttributeError … _REFUSAL_ID_SAMPLE_SIZE`; `…RE_REGISTER_door[×3]` → `TypeError … 'session_keep_id'`;
  `test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[fixer-b|wave7]` → `AttributeError … is_legal_identifier`;
  `test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition` → names EXACTLY `agents.py:161` (the unmoved definition)
  and `surreal_schema.py:490` (the raw-string twin the builder rebinds) — **not** `config.py` (the evidenced exemption).
  r3 ids gone: 1 — `test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists` (DUAL E1; green at HEAD).
- New ids GREEN at HEAD (17, by design): the text pin's 14 synthetic controls, the SKIP-gate corpus leg, the fake effect
  pin's HEAD CONTROL branch, the MP-4 premise pin (true today: no generator emits an unseen relation).
- No red for a wrong reason.

## §SAT — satisfiability (measured 2026-09-24)
- **Reference = adversary-r3's `my_ref_build.py` VERBATIM** (byte-identical to the paste committed in
  `REPORT-adversary-63c-i-a-r3.md` §A.1 at `c22419d` — `diff` clean, md5 `7c06739b…`; it already includes the builder's
  granted FORK-C guard deletion and its lint cleanups) **+ `r4_ref_build_extra.py`** (the ruled one-liner
  `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern`, imported from `lorerunes` in ruff's sorted shape).
- Scratch: `./scripts/scratch_copy.sh …/scratchpad/ref` (exit 0, provenance asserted); `loremaster.__file__` =
  `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/314fdf41-f303-4088-8e43-c8a3f52003dd/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `lorerunes.__file__` = `…/scratchpad/ref/lorerunes/lorerunes/__init__.py`. Tags: `r4-tests` (HEAD production + the
  r4 test tree, byte-identical to the main checkout — `cmp` per file), `r4-ref` (+ the reference build).
- **FULL SUITE ALONE, `-n 12`, on `r4-ref` (22:57:52–23:08:06 EDT; 31 GB available at launch; no other `pytest -n` on
  the box): `11428 passed, 62 skipped, 3 xfailed, 7 warnings in 611.66s` — 0 failed, 0 errors, EXIT=0.** = r3's 11405 +
  the net 23 r4 ids (24 new − the 1 replaced).
- AFTER the lint cleanups and the builder's granted edits: `uv run ruff check .` → `All checks passed!`;
  `./scripts/typecheck.sh` → 0 errors; currency (typecheck, ruff) → exactly 11 SELF-DESTRUCTs, nothing else.

## Candidate KNOWN BOUNDS (doors noticed OUTSIDE §W — surfaced, NOT pinned, per the STOP-rule; the sidecar rules)
- **KB-1 · the hostile corpus has no DOTTED shape.** `_HOSTILE_IDENTIFIERS` carries no `fixer.b`, so the SKIP-gate CORPUS
  leg cannot see X1's specific widening (X1 is killed by the mutation leg + the text pin instead). Closing it = one
  corpus entry, which grows every corpus-parametrised pin by 1–2 ids (store ASSERT legs, NF-2, MOVE, parity). Trigger:
  a ruling that the corpus should carry every character the drifted twins admit.
- **KB-2 · the text pin's threat-model boundary, stated in the instrument:** a REWORDED class (`[0-9a-z]`, `[a-z\d]`) or a
  pattern ASSEMBLED at runtime (`"[a-z0-9]" + "[a-z0-9_-]"`, `"".join(…)`) never forms the key in one constant and
  evades. Adversarial-only shapes (amendment-6 §1: not a defect of the gate). Trigger: the threat model changes.
- **KB-3 · reach excludes `scripts/`** (`include_scripts=False`, as r3's AST scan): `scripts/c3_wrongbuild_driver.py`
  carries the text as a wrong-build fixture string (amendment-7 ruled this correct). Trigger: a `scripts/` module that
  decides identity legality in production.
- **KB-4 · docstrings count.** A production docstring QUOTING the rule text reds the pin (literal to the ruling — "exactly
  ONE string constant"); the failure text teaches "state the rule in words". A possible honest false positive; none
  exists today. Trigger: the first such red on honest prose.
- **KB-5 · re-register parity covers the three ruled sequences only** — a consistent register followed by a DIFFERENT
  consistent pair (another owner/keep) is not a parity row (mint-once says "unchanged"; the real writer's MP-F pins cover
  α + legacy rows). Trigger: a fake/writer divergence found on that door.

## Deviations
- **DV-1 · a `pending_contract_gate.py --currency` run WITHOUT `--legs` executed the manifest's pytest leg at `-n auto`**
  (#466-forbidden) CONCURRENTLY with my wrong-build lane (a second pytest session of mine — against the brief). Measured:
  32 GB available; no OOM. Its pytest verdict is not used anywhere; the lane run it overlapped was on the stale tree and is
  discarded (DV-2). Every cited run afterwards ran alone; currency is cited only with `--legs typecheck,ruff`.
- **DV-2 · the first lane run tested a STALE test copy** (synced to scratch before amendment-7's riders + two mypy fixes).
  Stopped and discarded (`lane_r4_STALE_tests.log`, not cited). Stopping it, my `pkill -f` self-matched its own shell
  (the brief-base §5 #228 hazard) — recovered by PID; 0 stray processes verified. The final lane ran on a tree `cmp`-
  identical to the main checkout.
- **DV-3 · wrong builds ran through my declare-then-diff driver, not `scripts/mutation_proof.py`** — several builds are
  multi-edit or edit non-production files (`_comms_fakes.py`, `config.py`); the driver keeps the tool's discipline
  (declared set from `--collect-only` BEFORE the run, diffed both ways). Same deviation as r3 / adversary-r3.
- **DV-4 · FORK-E picked reading (i) with (ii) written down** (§FORKS).

## §INSTRUMENTS (pasted VERBATIM — scratch-only; `scripts/` is outside my writable set)
Base reference: adversary-r3 `my_ref_build.py` = `REPORT-adversary-63c-i-a-r3.md` §A.1 (committed `c22419d`), used byte-identical — cited, not re-pasted.

### `r4_ref_build_extra.py` (the r4 legs of the SAT reference)
```python
"""contract-63c-i-a-r4 — the r4 legs on top of adversary-r3's my_ref_build.py (the SAT reference).

amendment-6 §W builder row: surreal_schema._IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern (imported
from lorerunes — the production text twin the r4 text pin reds at HEAD). Each edit asserts its anchor occurs
exactly once (#194: a silent no-op edit is a failed setup).
Usage: uv run --no-project python r4_ref_build_extra.py <scratch-root>
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
edit(
    SCHEMA,
    '_IDENTIFIER_CHARSET_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"\n',
    "_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern  # ONE spelling (amendment-6 MP-1)\n",
)
edit(  # the ruff-sorted shape (I001), so the SAT reference holds AFTER the lint cleanups
    SCHEMA,
    "from lorerunes import AGENT_TABLE as AGENT_TABLE  # noqa: PLC0414 - explicit re-export (SEC-R4)\n"
    "from lorerunes import AUDIT_TABLE as AUDIT_TABLE  # noqa: PLC0414 - explicit re-export (D2)\n"
    "from lorerunes import PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLES\n",
    "from lorerunes import AGENT_NAME_PATTERN, PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLES\n"
    "from lorerunes import AGENT_TABLE as AGENT_TABLE  # noqa: PLC0414 - explicit re-export (SEC-R4)\n"
    "from lorerunes import AUDIT_TABLE as AUDIT_TABLE  # noqa: PLC0414 - explicit re-export (D2)\n",
)
print("r4 reference legs applied (_IDENTIFIER_CHARSET_PATTERN rebind)")
```

### `r4_wbs.py` (wrong builds + DECLARED expected-RED sets, written before any run)
```python
"""contract-63c-i-a-r4 — wrong builds against the r4 kill-pins, applied ON TOP of the r4 reference (tag r4-ref).

Usage: r4_wbs.py <scratch-root> <WB>            apply one build (each anchor must occur exactly once — #194)
       r4_wbs.py <scratch-root> <WB> --declared print the DECLARED expected-RED node ids, resolved from
                                                 collected_r4.txt (pytest --collect-only, taken BEFORE any run)
The DECLARED sets below were written BEFORE any wrong-build run.
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
WB = sys.argv[2]
SCR = Path(__file__).parent
REG = "test_agent_registry.py"
GOV = "test_agent_governance_63c_i_a.py"
ENF = "test_message_enforcement_63b_ii_a.py"
TEXT_PIN = "TestTheIdentifierCharsetTextHasOneSpelling63cIA::test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition"
SKIP_MUT = "TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_moves_with_the_SHARED"
FAKE_EFFECT = "test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists"

DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # X1 (adversary-r3): the SKIP gate decides with a private DRIFTED regex. Killed by the SKIP-gate mutation
    # leg (both legal attributions) AND the text pin (the pasted text now sits in server.py).
    "X1": [(REG, [SKIP_MUT, "[fixer-b]"]), (REG, [SKIP_MUT, "[wave7]"]), (REG, [TEXT_PIN])],
    # X2: constant defined, slice restates the literal [:10] — only the perturbation sees it.
    "X2": [(GOV, ["test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]"])],
    # X3 / X3b / X3c / X3d: every silent-skip spelling of the fake's guard — one EFFECT pin kills all four.
    "X3": [(REG, [FAKE_EFFECT])],
    "X3b": [(REG, [FAKE_EFFECT])],
    "X3c": [(REG, [FAKE_EFFECT])],
    "X3d": [(REG, [FAKE_EFFECT])],
    # R5: an un-ENFORCED relation inside an already-unswept emitter — the premise pin, and nothing else.
    "R5": [(ENF, ["test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see"])],
    # FX1: the fake heals an unstamped row on RE-register — the α sequence of the re-register parity rows.
    "FX1": [(REG, ["test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[alpha-then-credentialed]"])],
    # TW: the builder forgets amendment-6's one-liner — surreal_schema keeps its raw-string twin.
    "TW": [(REG, [TEXT_PIN])],
    # SLUG-DRIFT: the exempt constant's text drifts toward the agent rule (hyphen admitted, bounded) — the
    # exact-text exemption stops matching → the constant turns private → the text pin reds (amendment-7).
    "SLUGDRIFT": [(REG, [TEXT_PIN])],
}

SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"
SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
CONFIG = "loremaster/loremaster/config.py"
GUARD_DELETED = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n"
)


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (SCR / "collected_r4.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

if WB == "X1":
    edit(SERVER,
         "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n",
         "        if attribution is None or re.fullmatch(r\"[a-z0-9][a-z0-9_.-]{0,63}\", attribution) is None:\n")
elif WB == "X2":
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:10]")
elif WB in ("X3", "X3b", "X3c"):
    handler = {"X3": "except Exception:  # noqa: BLE001", "X3b": "except ImportError:", "X3c": "except:  # noqa: E722"}[WB]
    edit(FAKES, GUARD_DELETED,
         "        try:\n"
         "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n"
         f"        {handler}\n"
         "            return None\n"
         "        return is_legal_identifier\n")
elif WB == "X3d":
    edit(FAKES, GUARD_DELETED,
         "        import lorerunes  # noqa: PLC0415\n\n"
         "        return getattr(lorerunes, \"is_legal_identifier\", None)\n")
elif WB == "R5":
    edit(SCHEMA,
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         "    statements.append(_define_relation_table(\"holds\", LEASE_TABLE, TASK_TABLE))\n"
         "    return statements\n")
elif WB == "FX1":
    edit(FAKES,
         "        # status resets to active unconditionally (retired already excluded above).\n",
         "        if self.db.scopes.get(agent_id) is None and session_keep_id is not None:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n"
         "        # status resets to active unconditionally (retired already excluded above).\n")
elif WB == "TW":
    edit(SCHEMA,
         "_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern  # ONE spelling (amendment-6 MP-1)\n",
         "_IDENTIFIER_CHARSET_PATTERN = r\"^[a-z0-9][a-z0-9_-]{0,63}$\"\n")
elif WB == "SLUGDRIFT":
    edit(CONFIG, 'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"\n', 'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_-]*$"\n')
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### `run_lane_r4.sh` (declare-then-diff lane driver)
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4 lane driver: for each WB, reset the lane to r4-ref, resolve the DECLARED expected-RED set
# from collected_r4.txt (collect-only, taken BEFORE any wrong-build run), apply the build, run the contract
# files (-n 8, ONE pytest session at a time), diff observed vs declared BOTH ways from junit, restore.
set -u
S=$(dirname "$(readlink -f "$0")"); LANE=$S/ref; FILES=$(cat $S/r3b_files.txt)
for WB in "$@"; do
  cd $LANE && git checkout -q -f r4-ref && git clean -fdq -e REPORT-contract-63c-i-a-r4.md -e REPORT-sidecar-63c.md
  uv run --no-project python $S/r4_wbs.py $LANE $WB --declared | sort > $S/decl_$WB.txt || { echo "$WB: DECLARATION FAILED"; continue; }
  uv run --no-project python $S/r4_wbs.py $LANE $WB || { echo "$WB: APPLY FAILED (anchor)"; continue; }
  git diff --stat | tail -1
  timeout 1500 uv run pytest -n 8 -q -p no:cacheprovider $FILES --junitxml=$S/wb_$WB.xml > $S/wb_$WB.log 2>&1
  tail -1 $S/wb_$WB.log
  uv run --no-project python - "$S/wb_$WB.xml" "$S/decl_$WB.txt" "$WB" <<'PY'
import sys, xml.etree.ElementTree as ET
xml, decl, wb = sys.argv[1:4]
red = set()
for tc in ET.parse(xml).getroot().iter("testcase"):
    if tc.find("failure") is not None or tc.find("error") is not None:
        cls = tc.get("classname"); mod, _, klass = cls.rpartition(".") if "." in cls else ("", "", cls)
        red.add((tc.get("name"), klass))
declared = [line.strip() for line in open(decl) if line.strip()]
def key(node):  # node id: path::Class::name or path::name
    parts = node.split("::"); return (parts[-1], parts[-2] if len(parts) == 3 else parts[0].rsplit("/", 1)[-1].removesuffix(".py"))
dkeys = {key(n) for n in declared}
unexpected = sorted(red - dkeys); still_green = sorted(dkeys - red)
print(f"{wb}: declared={len(dkeys)} observed_red={len(red)} unexpected_red={unexpected} declared_still_green={still_green}")
print(f"{wb}: VERDICT {'PROOF HELD' if not unexpected and not still_green else 'MISMATCH'}")
PY
done
cd $LANE && git checkout -q -f r4-ref && git clean -fdq -e REPORT-contract-63c-i-a-r4.md -e REPORT-sidecar-63c.md && echo "lane restored to $(git log --oneline -1)"
```

### `red_diff_r4.py` (§RED diff)
```python
"""contract-63c-i-a-r4 — RED@HEAD diff: r4 tests (main checkout) vs r3 tests (scratch @ a71ef32), SAME production.

Reports totals; ids GREEN on r3 turned RED on r4 (the claim is ZERO); NEW red ids (absent on r3); r3 ids gone on r4
(deleted/replaced pins); and each new red's first failure line (the right-reason read).
"""
import sys
import xml.etree.ElementTree as ET
from collections import Counter


def load(path: str) -> dict[str, tuple[str, str]]:
    outcome: dict[str, tuple[str, str]] = {}
    for case in ET.parse(path).getroot().iter("testcase"):
        node = f"{case.get('classname')}::{case.get('name')}"
        bad = case.find("failure") if case.find("failure") is not None else case.find("error")
        if bad is not None:
            outcome[node] = ("red", (bad.get("message") or "").splitlines()[0][:170])
        elif case.find("skipped") is not None:
            outcome[node] = ("skip", "")
        else:
            outcome[node] = ("green", "")
    return outcome


r4, r3 = load(sys.argv[1]), load(sys.argv[2])
print("r4:", Counter(v[0] for v in r4.values()), "| r3:", Counter(v[0] for v in r3.values()))
turned = sorted(n for n in r4 if r4[n][0] == "red" and r3.get(n, ("",))[0] == "green")
new_red = sorted(n for n in r4 if r4[n][0] == "red" and n not in r3)
gone = sorted(n for n in r3 if n not in r4)
print(f"GREEN on r3 turned RED on r4: {len(turned)}")
for n in turned:
    print("   TURNED", n, "|", r4[n][1])
print(f"NEW red ids: {len(new_red)}")
for n in new_red:
    print("   NEW", n.split("::", 1)[1][:150], "|", r4[n][1])
print(f"r3 ids gone on r4: {len(gone)}")
for n in gone:
    print("   GONE", n, r3[n][0])
```

### one-off commands (verbatim)
```bash
# declaration universe, taken BEFORE any wrong-build run (lane at r4-ref):
uv run pytest -q -p no:cacheprovider --collect-only $(cat $S/r3b_files.txt) | awk '/::/' > $S/collected_r4.txt   # 2601 ids
# reference + lane:  git checkout -f r4-ref; uv run pytest -n 8 … $(cat r3b_files.txt); run_lane_r4.sh X1 X2 X3 X3b X3c X3d R5 FX1 TW SLUGDRIFT
# SAT:               (lane at r4-ref, ALONE) uv run pytest -n 12 -q -p no:cacheprovider --junitxml=full_sat.xml
# RED:               main: uv run pytest -n 8 … $(cat r3b_files.txt) --junitxml=red_r4.xml ; scratch @ a71ef32 (r3 tests): same → red_r3.xml ; red_diff_r4.py red_r4.xml red_r3.xml
# charset sweep:     git ls-files '*.py' | awk '!/\/tests\//' | while read f; do awk -v F="$f" 'index($0,"[a-z0-9][a-z0-9_"){print F":"NR": "$0}' "$f"; done
```
