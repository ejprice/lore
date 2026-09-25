# REPORT-adversary-63c-i-a-r4 — contract-adversary DELTA pass on revision 4 of the 63c-i-a contract

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done-with-deviations · **VERDICT: CONTRACT INSUFFICIENT — with NEW-CLASS survivors** (not only SAME-CLASS); **no LIVE-PRODUCTION-DEFECT** (measured 2026-09-24/25).
- **Graded:** `e80a854` · HEAD-at-report: `3e8566c` · DIFFERENT (3 ahead: `ba8b4c9`, `2f16ac9` amendment-8, `3e8566c` — docs only; `git diff --stat e80a854 3e8566c -- loremaster lorerunes lorescribe loresigil scripts` is EMPTY, so no pin or symbol this verdict rests on moved).
- **deviations:** R-9 — declare-then-diff driver (not `mutation_proof.py`); full suites launched at 28–29 GiB (1–2 under the ~30 guideline; watchdog, lowest 22 GiB); one API-error turn (state re-verified, ref rebuilt); my first full-suite guard self-refused on the lead's watcher (#228 class, fixed).
- **Packages considered:** stdlib `ast`/`re`; `unittest.mock.AsyncMock` for the spy → keep_with_trigger (spec-less mock fabricates methods); `pytest.MonkeyPatch.setattr/delattr` — used. Diff vs author: agreement (§9). **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (no repo symbols; scratch instruments pasted §A). Author's "17 new symbols" re-counted: 17 ✓.
- **P1 (§4):** **r3 floor 5/5 KILLED exactly** (X1, X2, X3, R5, FX1) + the ruled guard spelling X3b and X3c/X3d/X3e. **8 NEW builds survive the FULL suite** (§4.5): RS1, FX2, G1, G2, FXg, FXf, PX2, TWR. R5b survives the contract, dies in the full suite (a packet-07 pin).
- **SAT (own reference, §2):** 24 contract files `2905 passed, 19 skipped`; **FULL SUITE ALONE `-n 12`: `11428 passed, 62 skipped, 3 xfailed` — 0 failed, exit 0** (= author); ruff clean; built world = exactly 11 SELF-DESTRUCTs, 0 real mypy errors (§7). **RED@HEAD (§1):** 0 r3-greens turned red, 7 new reds all right-reason, text pin names exactly `agents.py:161` + `surreal_schema.py:490` — author CONFIRMED.
- **MISSING PINS (§6):** **MP-R4-1** RS1 — the REAL writer re-stamps an already-stamped row from a DIFFERENT consistent pair (ownership takeover by a householded joiner; mint-once pinned ∀ rows, not ∀ callers) · NEW-CLASS · GATING. **MP-R4-4** FXg — MP-3's effect pin removes the predicate at ONE binding; a guard importing from the submodule outlives its premise · NEW-CLASS. **MP-R4-5** FXf — DUAL: the deleted spelling pin's "presence reds" virtue is lost; a guard with a private-regex fallback survives · NEW-CLASS (SAME-CLASS reading written). **MP-R4-3** G1 — the SKIP-gate legs test two short legal values; a narrowing conjunct survives · SAME-CLASS, closable by one witness (`"a"*64`). **MP-R4-6** FX2 (= am-8 KB-5, r4a). **MP-R4-7** PX2 — refusal prose restates the bound · NEW-CLASS, NON-GATING. SAME-CLASS bounds constructed: TWR (KB-2), G2 (closed by r4a's `"fixer.b"`).
- **P1b (§5):** 8 invariants — Q2/Q8 SAFE; Q1, Q3, Q4, Q5, Q6 GUARDED with surviving door-builds; Q7 SAFE at suite level (packet-07 pin). **P1c (§6a):** 9 instruments — text pin reach DERIVED + coverage CHECKED (MEM1/MEM2 empirical), exemption evidence live both ways (SLUGDRIFT/CONVERGE); MISSING on the SKIP-gate legal axis (G1) and the MP-3 simulation reach/presence (FXg/FXf); MP-4 key is a proxy but redundant.
- **KB-1…KB-5 (§6b):** KB-1 → G2 (r4a kills it, not G1) · KB-2 → TWR (bound) · KB-3 accepted, self-revealing · KB-4 red is correct (TWQ) · **KB-5 → FX2 AND RS1; amendment-8's premise "the real writer is pinned mint-once on it" is FALSE** — r4a's row must carry the ABSOLUTE real-side expectation.
- **decisions-needed:** sidecar rules MP-R4-1 (recommend GATING — r4a row with absolute expectation, or KP-RS1), MP-R4-4/-5 (restore the presence pin beside the effect pin, or delattr at every binding), MP-R4-3 (one r4a witness), MP-R4-7; R-1 — r3's MP-4 was a scoped-file-set artifact (packet 07 already pinned the premise): keep, re-key, or delete r4's premise pin.
- **Receipt pointers:** §0 capability · §1 RED · §2 SAT · §3/§3.1 DUAL · §4.1 floor · §4.2 new builds · §4.3–4.4 controls + reach · §4.5 full-suite leg · §5 P1b · §6 MISSING PINS · §6a P1c · §6b KBs · §7 pending_contracts · §8 residuals · §9 P-PKG · §10 P-PORT · §11 corpses · §A instruments · VERDICT.

## 0. Capability check (brief-base §4)
- Reachable 2026-09-24: lore MCP (`register`, `heartbeat` OK), `git`, `uv run pytest/ruff`, `scripts/scratch_copy.sh`,
  test store `ws://127.0.0.1:18000`. Never touched `:18500` or the TEI embedder.
- grep/rg are hook-blocked (#473): every textual sweep is `awk` over `git ls-files` — said here once, applies throughout.
- One API-server error killed a turn mid-run (lead resume ping); state re-verified: the reference commit written just
  before the error was the lint-failing variant (a heredoc-quoting failure in my own edit); rebuilt from `2f16ac9`
  and re-committed as `3b6a12a` (branch `adv4-ref`) — §2.
- Scratch lanes (all via `scratch_copy.sh`, provenance asserted by the tool), root
  `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad`:
  `ref` (`loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`, `lorerunes.__file__ =
  …/scratchpad/ref/lorerunes/lorerunes/__init__.py`), `head` (same shape, unbuilt production).
- Lanes were copied at `2f16ac9`; `git diff --stat e80a854 2f16ac9 -- loremaster lorerunes lorescribe loresigil scripts`
  is EMPTY, so the tests and production graded are exactly `e80a854`'s.

## 3. DUAL — my independent enumeration of r4's deletions (written BEFORE opening the author's §DUAL)
Method: `git diff 39935f6 e80a854` over all 9 files, every `-` hunk read. Production untouched by r4.

| # | deleted / replaced | virtue it carried | my verdict (before reading §DUAL) |
|---|---|---|---|
| E1 | `test_agent_registry.py::test_the_fakes_HEAD_RED_import_guard_is_deleted_once_the_predicate_exists` (AST: any `except` naming `ImportError` in `_comms_fakes.py`; HEAD control: the scan sees today's guard) → replaced by the EFFECT pin `test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` | (a) no silent skip once the predicate exists; (b) HEAD anti-vacuity; **(c) the guard's mere PRESENCE reds, whatever its handler DOES** — so a guard kept with a NON-silent fallback (a private regex) or a guard whose `try` imports from a DIFFERENT binding than the one the effect pin removes (the `lorerunes.identifiers` submodule) was RED under the old pin | (a) moves to the effect pin (strengthened for X3/X3c/X3d); (b) moves to the effect pin's HEAD branch; **(c) is DROPPED and nobody says so** — the effect pin simulates "predicate absent" by `delattr` on ONE binding (`lorerunes.is_legal_identifier`) and observes only SILENT registration. Tested empirically as FXg / FXf (§4). |
| E2 | `from pathlib import Path` in `test_agent_registry.py` | none (orphaned by E1) | lint cleanup; no virtue |
| E3 | R-Q5-1 message tail `: {reason[:400]!r}` → re-emitted after an optional clause; `isinstance(bool)` exclusion added | message content | kept verbatim + strengthened (a `True` bound now reds) |
| E4 | `_IDENTIFIER_DECISION_CONSUMERS` comment reworded ("EVERY consumer" → "consumer ENTRY POINTS", reach stated) | an over-claim ("EVERY") | the over-claim is REMOVED — a truth fix, no virtue lost |
| E5 | `pending_contracts.yaml` attr-defined 3→4 + comment repoint; `_comms_fakes` docstring repoint; coverage_124 `_emit` docstring | adjudication / prose | §7 / prose; no virtue lost |

## 9. P-PKG — my table FIRST (from the r4 diff, before reading the author's `Packages considered:`), then the diff
| mechanism r4 specifies | candidates | what I READ | verdict |
|---|---|---|---|
| text ∀ over production string constants (`_classify_charset_constants`) | stdlib `ast`; `tokenize` (would also see comments — wrong population); semgrep/libcst (not installed, not needed for a `Constant` walk); ruff (no custom-rule API) | the pin's source (e80a854); `ast.Constant` covers implicit concatenation (joined at parse) and f-string literal parts | **bespoke — justified**; reach REUSES `parse_production_trees` + `assert_scan_reached_every_member` (read, §6a) |
| exemption evidence (two-direction language witness) | stdlib `re` | pin source | stdlib — fine |
| registry-read spy (`_LookupCountingRegistry`) | `unittest.mock.AsyncMock` (stdlib) with `await_args_list` | stdlib mock semantics (HIGH confidence, not re-probed): a spec-less `AsyncMock` fabricates ANY attribute, so a gate that read through a DIFFERENT registry method would be silently "satisfied"; `create_autospec(AgentRegistry)` would keep fail-loud | **keep_with_trigger** — the 8-line spy fails LOUD on any other method (AttributeError). Trigger: a second spy of the same shape appears (then one `create_autospec`-based helper). |
| constant perturbation / predicate removal | `pytest.MonkeyPatch.setattr` / `.delattr` | installed pytest API | package — used |
| re-register parity drivers | in-house r3 harness | `_real_registry`, `_agent_row_count` | REUSE |

**Diff vs author** (`stdlib ast/re/importlib/types; MonkeyPatch setattr/delattr; no production mechanism`): agreement on
every verdict; mine adds the `AsyncMock` alternative, rejected with a reason. No `bespoke` rests on an unread API.

## 10. P-PORT
`Odoo-20 portability: n/a — no Odoo seam touched` — my own enumeration over the r4 diff (tests + fixtures): 0 Odoo
models/fields/methods/views/ACLs/ORM paths. Author's line matches (0 = 0).

## 4. P1 — wrong builds (lane `ref` @ `adv4-ref` = `3b6a12a`, my reference; tests at `e80a854`)
Method: `run_lane4.sh` (§A.3) — per build: reset lane (0 dirty paths asserted), resolve the DECLARED expected-RED ids
from `collected4.txt` (collect-only over the 24 files of `files4.txt`, **2924 ids**, taken on `adv4-ref` BEFORE any
wrong-build run), apply the build via `my_wbs4.py` (§A.2 — exactly-once anchors; a build that leaves the lane clean
aborts), assert `loremaster.__file__` inside the lane, run the 24 files `-n 8` (one pytest session at a time), diff
observed-RED vs declared BOTH ways from junit. Reference tail on the same 24 files: **`2905 passed, 19 skipped` —
0 failed** (§2). Measured 2026-09-24/25.

### 4.1 The r3 floor — ALL KILLED, each EXACTLY on its declared r4 pin (0 unexpected reds, 0 declared-still-green)
| build | the door (adversary-r3) | tail (24 files) | killed by |
|---|---|---|---|
| **X1** | SKIP gate decides with private drifted `re.fullmatch(r"[a-z0-9][a-z0-9_.-]{0,63}", …)` | `3 failed, 2902 passed, 19 skipped` | `test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[fixer-b]`, `[wave7]` + `test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition` |
| **X2** | constant defined, slice restates `[:10]` | `1 failed, 2904 passed, 19 skipped` | `test_R_Q5_1_…[perturbed-bound]` |
| **X3** | fake guard kept as `except Exception:` | `1 failed, 2904 passed, 19 skipped` | `test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` |
| X3b | guard kept as RULED (`except ImportError`) | `1 failed, 2904 passed, 19 skipped` | same effect pin |
| X3c | bare `except:` | `1 failed, 2904 passed, 19 skipped` | same effect pin |
| X3d | `getattr(lorerunes, "is_legal_identifier", None)` | `1 failed, 2904 passed, 19 skipped` | same effect pin |
| X3e | `except builtins.ImportError:` (not in the author's set) | `1 failed, 2904 passed, 19 skipped` | same effect pin |
| **R5** | un-ENFORCED `holds(lease→task)` inside `_lease_statements` | `1 failed, 2904 passed, 19 skipped` | `test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see` |
| **FX1** | the FAKE heals an unstamped row on re-register | `1 failed, 2904 passed, 19 skipped` | `test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door[alpha-then-credentialed]` |

**r3 floor: 5/5 survivors (X1, X2, X3, R5, FX1) KILLED, plus the four ruled/alternate guard spellings.** The author's
"10/10 PROOF HELD" claim is reproduced on the 8 of its builds I re-ran (X1 X2 X3 X3b X3c X3d R5 FX1); TW/SLUGDRIFT in §4.3.

### 4.2 NEW wrong builds against r4's instruments (declared BEFORE the run; tails over the 24 files, 2924 ids)
| build | instrument attacked | the door | tail (24 files) | verdict · kill-pin pair (§A.4, `-n 4`) |
|---|---|---|---|---|
| **G1** | MP-1 SKIP-gate effect legs | gate keeps the home call but adds a private conjunct `or len(attribution) > 32` — legal 33–64-char identities are never looked up (R8 footer silently lost for them) | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). KP-G1 (`"a"*64` looked up once): REF green, G1 red |
| **G2** | MP-1 SKIP-gate effect legs + text pin | gate keeps the home call OR a reworded private `re.fullmatch(r"[a-z0-9]+\.[a-z0-9]+", …)` (dotted service names) — neither witness matches it, the corpus has no dot, the text pin's key is absent | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). KP-G2 (`"fixer.b"` never looked up — = amendment-8 KB-1's r4a corpus entry): REF green, G2 red |
| **FXg** | MP-3 effect pin (replaced the spelling pin) | the fake's guard is KEPT (`except ImportError: return None`) but its `try` imports `from lorerunes.identifiers import is_legal_identifier` — `monkeypatch.delattr(lorerunes, …)` removes the PACKAGE binding only, so the simulated "predicate absent" never reaches the guard | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). KP-FXg (delattr at EVERY `lorerunes*` binding via `module_level_bindings_of`) and KP-E1c (the DELETED r3 spelling pin, body verbatim): REF green, FXg red on both |
| **FXf** | MP-3 effect pin | guard KEPT with a non-silent fallback: `except ImportError: return lambda v: re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", v) is not None` — a private COPY of the rule in the test tree, which the text pin does not scan | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). KP-E1c (deleted spelling pin): REF green, FXf red. The effect pin cannot see it by construction (the fallback refuses) |
| **RS1** | MP-5 re-register parity rows; MP-F mint-once | the REAL writer: on re-register, when the row ALREADY carries a scope and a consistent pair is supplied, re-stamps `owner_principal` + `scope` from the CALLER — a householded joiner (bob, same session keep) re-registering alice's agent TAKES IT OVER. Unstamped (α / legacy) rows untouched, so MP-F's rows stay green; the r2 mint-once pin re-registers with the SAME principal, so re-stamping writes identical values | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). KP-RS1 (`_real_re_register_outcome(("alice_pid",K),("bob_pid",K)) == ("re-registered","alice_pid",True,keep:K)`): REF green, RS1 red |
| **FX2** | MP-5 parity | the same re-stamp, FAKE side only (amendment-8 KB-5's door) | **`2905 passed, 19 skipped`** | **SURVIVES at `e80a854`** (declared). KP-FX2: REF green, FX2 red |
| R5b | MP-4 premise pin | `_lease_statements` re-emits the SWEPT `to` relation with the same name + endpoints but WITHOUT `ENFORCED`. The premise pin keys "seen" on `(edge, (IN, OUT))` and `relation_endpoints` drops the ENFORCED clause, so the re-definition is "seen"; the ∀-ENFORCED sweep reads only `ALL_DDL_GENERATORS` | **`2905 passed, 19 skipped`** — but **KILLED by the FULL suite** (§4.5) | survives the CONTRACT only. KP-R5b (every relation statement any generator emits is byte-identical to the swept one): REF green, R5b red. **KP-R5b-live, on the TEST store (`ws://127.0.0.1:18000`, throwaway DB):** agent+message DDL → `to` carries ENFORCED (control); then the lease slice, applied after the schema exactly as `LeaseStore.ensure_ready` does → **`DEFINE TABLE to TYPE RELATION IN message OUT agent SCHEMAFULL PERMISSIONS NONE`** — ENFORCED gone. REF green, R5b red |
| **PX2** | MP-2 perturbed bound | the slice reads the constant, but the refusal PROSE restates it: `"half-applied store (first 10 ids shown); "` — under the perturbation the served text says 10 while naming 3 | **`2905 passed, 19 skipped`** | **SURVIVES** (declared). No runnable kill-pin (the fixture lives inside the R-Q5-1 class); pin text in §6 MP-R4-7, construction receipt |
| **TWR** | text pin — KB-2 | a REWORDED charset twin `re.compile(r"^[0-9a-z][0-9a-z_-]{0,63}$")` at a new site in `agents.py` | **`2905 passed, 19 skipped`** | SURVIVES — **as the instrument's stated threat model says it must** (amendment-6 §1, amendment-8 KB-2): the bound, measured |

My first live-probe draft read `INFO FOR TABLE to` (which omits the table's own definition) and was RED on the
reference — a P0 control failure of MY instrument, caught by the REF leg; fixed to read `INFO FOR DB` →
`tables.to` with an in-test control that ENFORCED is visible BEFORE the lease slice. Re-run: REF `8 passed`; R5b red.

### 4.3 Controls (P0 — each probe shown able to FIRE), narrow lane (`run_lane4_ctl.sh`: `test_agent_registry.py` + `test_agent_governance_63c_i_a.py`, 350 ids)
| build | what it proves | tail | result |
|---|---|---|---|
| TWP | verbatim paste in **loresigil** (a non-loremaster member) is named | `1 failed, 349 passed` | text pin RED: `loresigil/loresigil/__init__.py:4: _re.compile('^[a-z0-9][a-z0-9_-]{0,63}$')` |
| TWS | verbatim raw-literal in **lorescribe** | `1 failed, 349 passed` | text pin RED: `lorescribe/lorescribe/__init__.py:3` |
| TWQ | a production DOCSTRING quoting the rule (KB-4) | `1 failed, 349 passed` | text pin RED: `agents.py:405` — amendment-8 KB-4 rules this red CORRECT |
| SLUGDRIFT | the exempt constant's text drifts (`*` → `{0,127}`) | `1 failed, 349 passed` | text pin RED (exemption stops matching → private) — author's SLUGDRIFT reproduced |
| MP2DEF | a ONE-source build that captures the constant at DEF time (`sample_size: int = _REFUSAL_ID_SAMPLE_SIZE`) | `1 failed, 349 passed` | `R_Q5_1[perturbed-bound]` RED — see §8 R-4 (a satisfiability hazard, not a survivor) |
| GS | gate decides with `config.SLUG_PATTERN` (honest "slugs = names" confusion) | `3 failed, 347 passed` | KILLED — declared `[fixer-b]` only; ALSO `[wave7]` + the corpus leg (`"z"*65` is slug-legal). Safe-direction misprediction, recorded not re-declared |

**Reach legs (`mem_reach.sh`, §A.5; the venv's pytest, one test id, alone):** MEM0 (reference) `1 passed`; **MEM1** — a
NEW member `loreglyph` added to `[tool.uv.workspace] members` with a pasted twin → `1 failed`, naming
`loreglyph/loreglyph/__init__.py:2` (reach is DERIVED from `pyproject.toml`, not a hand-list); **MEM2** — the member
declared but shipped src-layout → `1 failed`, `declared-not-scanned … ['loreglyph']` (coverage is a CHECKED variable,
fails closed).

### 4.4 Text-pin one-source + evidence legs (single test id, venv pytest, on `adv4-ref` + one edit each)
- **KEYDRIFT** — the lorerunes definition re-spelled `^[a-z0-9][-a-z0-9_]{0,63}$` (same language, key text gone): `1 failed`
  — *"the gate's KEY '[a-z0-9][a-z0-9_' no longer occurs in the live rule …"*. The key is checked against the LIVE rule.
- **CONVERGE** — the lorerunes definition widened to `{0,127}` (`"a"*65` becomes agent-legal): `1 failed` — the two-direction
  evidence leg reds (*"… no longer differ in BOTH directions … CONVERGED"*). The evidence is computed live, both directions.

## 1. P7 — RED honesty, reproduced (lane `head` = unbuilt production at `e80a854`'s tree; measured 2026-09-25)
- Run set: my 24 files (`files4.txt`) — a superset of every file r4 touched. Two runs, `-n 8`, one at a time, same
  production: r4 tests (`e80a854`) vs r3 tests (`git checkout 39935f6 -- loremaster/tests`, restored after; 0 dirty tracked).
- Tails: r4 `177 failed, 2677 passed, 19 skipped, 51 errors` · r3 `170 failed, 2661 passed, 19 skipped, 51 errors`.
- `red_diff4.py` (§A.6): **r3-GREEN turned r4-RED: 0. NEW red ids: 7** — text pin (names EXACTLY
  `loremaster/loremaster/agents.py:161` and `loremaster/loremaster/store/surreal_schema.py:490`; `config.py` NOT named) ·
  SKIP-gate `[fixer-b]`/`[wave7]` (`AttributeError … is_legal_identifier`) · RE_REGISTER_door ×3 (`TypeError …
  'session_keep_id'`) · `R_Q5_1[perturbed-bound]` (`AttributeError … _REFUSAL_ID_SAMPLE_SIZE`). NEW green ids 17. r3 ids
  gone 1 (the deleted spelling pin, green at HEAD). red→green 0. **Every new red is the right reason. The author's §RED
  (0 turned, 7 new, the two named sites, 17 new-green, 1 gone) is CONFIRMED** on an independently derived run set (my
  absolute counts differ from theirs because my set is 24 files, theirs 22).

## 6. MISSING PINS — each: the test that should exist · the defect it catches · the wrong build that passes · receipt · CLASS
All receipts: lane `ref` (`adv4-ref` + the build), tests at `e80a854`, 24 files → **`2905 passed, 19 skipped`, 0 failed**
(= the reference's own tail); kill-pins in `test_adv_r4_killpins.py` (§A.4) GREEN on REF (`8 passed`) and RED on exactly
their build (§4.2). CLASS per the brief: SAME-CLASS (identity private-decision door) · NEW-CLASS · LIVE-PRODUCTION-DEFECT.
**No LIVE-PRODUCTION-DEFECT found** — the reference passes everything, and none of these doors is open at HEAD.

**MP-R4-1 — mint-once is pinned for rows, not for CALLERS: a stamped row re-registered with a DIFFERENT consistent pair
(RS1, real writer). CLASS: NEW-CLASS (ownership takeover; security-adjacent). Recommend GATING.**
- *Test that should exist:* a REAL-writer pin: register `(alice_pid, K)`, re-register `(bob_pid, K)` (a householded joiner:
  same session keep, different owner — reachable through `_comms_register`, which admits any principal householded in the
  session keep) → `("re-registered", "alice_pid", owner_agent=self, keep:K)` — KP-RS1. (Or: amendment-8 KB-5's r4a fourth
  parity row, PROVIDED it carries the ABSOLUTE real-side expectation the r4 rows carry; a `real == fake`-only row passes a
  build where both sides re-stamp — RS1 + FX2 together.)
- *Defect:* ruling §2.2 row 2 — re-register leaves all three columns **untouched** — is pinned only where re-stamping is
  invisible: the r2 pin `test_re_register_does_not_restamp_the_governed_triple_mint_once` re-registers with the SAME
  principal (both calls `principals={"alice": …}` — re-stamping writes identical bytes), and MP-F's rows are UNSTAMPED
  (α, legacy — a build that re-stamps only already-stamped rows never touches them). THE QUANTIFIER LAW again: mint-once
  ∀ rows was pinned; ∀ callers was not.
- *⚠ Amendment-8 KB-5's premise is false:* it says *"The real writer is pinned mint-once on it (r2's
  `test_re_register_does_not_restamp_the_governed_triple_mint_once`)"* — that pin cannot see a different pair (read above);
  RS1 is the receipt.
- *Wrong build that passes:* **RS1** (§4.2) → 2905/0. KP-RS1: REF green, RS1 red.

**~~MP-R4-2~~ — WITHDRAWN after the full-suite leg (kept visible, not deleted, because the correction is the lesson).**
R5b (an unswept emitter re-defining the swept `to` relation WITHOUT `ENFORCED`) survives the 24 contract files
(2905/0) and the r4 MP-4 premise pin (it keys "seen" on `(edge, endpoints)`; `relation_endpoints` drops `ENFORCED`) — but
the FULL suite kills it: `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically::
test_this_slice_contains_neither_a_relation_table_nor_a_sequence` + `…::test_every_table_definition_is_IF_NOT_EXISTS`
(packet 07, `147be46`), which sweep BOTH unswept slices (lease + floor_calibration). Measured: that file on REF `42 passed`;
on R5b `2 failed, 40 passed`; **on r3's R5 `2 failed, 40 passed` too** — see §8 R-1: adversary-r3's MP-4 (and so r4's
premise pin) was a SCOPED-FILE-SET artifact; the premise was already pinned, more strongly, since packet 07. A new third
unswept generator doing the same would red the FORK-A exact-set pin (its un-ENFORCED statement is not in the sweep's
union — construction). The live consequence (KP-R5b-live: ENFORCED dropped on the test store) stands as the reason the
packet-07 pin matters. **No missing pin.**

**MP-R4-3 — the SKIP-gate effect legs test agreement on LEGAL inputs at two short values: a private NARROWING conjunct
survives (G1). CLASS: SAME-CLASS (a private identity decision at the gate) — but it defeats the instrument amendment-6 §3
built for exactly this call site, and it is closable by FIXTURE GROWTH, not a new instrument (amendment-8's r4a shape).
Recommend: r4a row.**
- *Test that should exist:* `_LEGAL_NAME`/`_LEGAL_SESSION` baseline + a legal identity AT THE CAP (`"a" * 64`) — looked up
  exactly once (KP-G1); better, parametrize the mutation leg's baseline over it too.
- *Defect:* the class docstring claims *"any private decider at that call site, whatever it spells, is visible"*; that
  holds for deciders that WIDEN (the corpus) or REPLACE (the mutation), not for a conjunct that NARROWS — legal 33–64-char
  identities silently lose their footer. Parameter-value monoculture on the legal side (both witnesses ≤ 7 chars); the
  corpus carries cap+1 (`"z"*65`) but no legal cap.
- *Wrong build that passes:* **G1** → 2905/0. KP-G1: REF green, G1 red.

**MP-R4-4 — the MP-3 effect pin simulates "predicate absent" at ONE binding (FXg). CLASS: NEW-CLASS (the effect pin's
simulation reach — MP-3's guard-outlives-premise class, not the identity class). Recommend GATING-adjacent (it is the
builder's one granted edit, and amendment-6 ruled this pin subsumes "every silent-skip shape at once").**
- *Test that should exist:* the effect pin removes the predicate at EVERY `lorerunes*` module binding
  (`module_level_bindings_of(lorerunes.is_legal_identifier)`, anti-vacuity that ≥ 1 home was found) — KP-FXg; or keep
  the deleted presence pin beside it (next item).
- *Defect:* `monkeypatch.delattr(lorerunes, "is_legal_identifier")` removes the PACKAGE attribute; a guard whose `try`
  imports from the defining SUBMODULE (`lorerunes.identifiers`, where both reference builds put it) never raises, so the
  guard outlives its premise with the pin green. (Measured with my reference's module layout; a build that defines the
  predicate in `lorerunes/__init__.py` has no such submodule and the door closes by accident.)
- *Wrong build that passes:* **FXg** → 2905/0. KP-FXg and KP-E1c: REF green, FXg red on both.

**MP-R4-5 — DUAL: the deleted spelling pin's virtue (c) "the guard's mere PRESENCE reds" is lost (FXf). CLASS: two
readings, written down per scope law — (a) SAME-CLASS: FXf's fallback is a pasted COPY of the charset rule relocated into
the TEST tree, outside the text pin's `include_tests=False` reach; (b) NEW-CLASS: a DUAL virtue loss of the MP-3 rewrite.
I would pick (b) — the defect is the deletion, and its fix lives in MP-3's pin, not the identity instrument.**
- *Test that should exist:* keep the r3 AST presence pin (no `except` handler naming `ImportError` in `_comms_fakes.py`
  once the predicate exists) BESIDE the effect pin — amendment-6 deleted it as "a proxy … decoration", but the two observe
  DIFFERENT properties (silent-skip vs outlives-its-premise), and FXf is the build that separates them. KP-E1c (body
  verbatim from `39935f6`).
- *Defect:* a guard kept with a NON-silent fallback (`except ImportError: return lambda v: re.fullmatch(r"…", v) …`)
  refuses every hostile value, so the effect pin — which observes only silent registration — is green; the fallback is a
  second copy of the identity rule inside the fake, invisible to every r4 instrument (text pin: tests excluded; decision
  mutation: the fallback runs only when the predicate is absent).
- *Wrong build that passes:* **FXf** → 2905/0. KP-E1c: REF green, FXf red. The author's §DUAL E1 row lists virtues (a)+(b)
  only.

**MP-R4-6 — the fake's RE-register door with a different consistent pair (FX2). CLASS: NEW-CLASS, ALREADY RULED
(amendment-8 KB-5 → r4a).** Survives at `e80a854` (2905/0; KP-FX2 REF green, FX2 red). Listed so the r4a row is graded:
it must carry the absolute real-side expectation (MP-R4-1).

**MP-R4-7 — PROSE twin of the sample bound (PX2). CLASS: NEW-CLASS (the P8d served-prose class; MP-2's "two sources of one
policy" in the refusal TEXT). Recommend NON-GATING.**
- *Test that should exist:* in `R_Q5_1[perturbed-bound]`, after stripping the named ids, the reason carries no numeral equal
  to the BIRTH value (`\b10\b`) — or, positively, if the reason states the sample size at all, it states the PATCHED one.
- *Defect:* a builder writing *"(first 10 ids shown)"* beside a constant-read slice serves a false number the day the
  constant changes; the perturbation leg checks only `len(named)`.
- *Wrong build that passes:* **PX2** → 2905/0. Construction receipt only (no kill-pin run — the fixture lives inside the
  R-Q5-1 class).

**Bounds constructed, not missing pins (SAME-CLASS, already stated):** TWR (reworded class, 2905/0 — amendment-8 KB-2);
a `re.fullmatch(AGENT_NAME_PATTERN.pattern, v)` decider at a NEW call site (construction: the `.pattern` read is the r3
AST scan's blessed shape and no text constant exists; the mutation pin's reach is `_IDENTIFIER_DECISION_CONSUMERS` — the
amendment-6 §4 stated hand-list bound; my awk sweep at `e80a854` finds no such site today — every production reader of
`AGENT_NAME_PATTERN` / `_is_comms_charset_legal` / `_validate_comms_charset` is one of the listed entry points or prose).

## 5. P1b — QUANTIFIER TABLE (r4's invariants + the r3 invariants r4 re-shaped; each GUARDED row carries a receipt)
| # | invariant (ruling) | pinned as | class · receipt |
|---|---|---|---|
| Q1 | the identity decision is the shared `is_legal_identifier` at EVERY decision site (A4-bis, am-6 MP-1) | (i) mutation × 4 listed entry points; (ii) SKIP-gate effect legs; (iii) text ∀ over production constants | **(iii) ∀ over production members for PASTED text — SAFE** (X1, TWP, TWS, TWQ, MEM1 red; TWR/assembly = the stated KB-2 bound). **(i)+(ii) GUARDED by the listed sites** (am-6 §4 stated bound; awk: complete at `e80a854`). **At the gate: GUARDED by two short legal witnesses** — G1 (narrowing conjunct) SURVIVES → **MP-R4-3**; G2 (reworded widening) SURVIVES → closed by am-8 KB-1's r4a `"fixer.b"` (KP-G2 is that value; REF green, G2 red) |
| Q2 | R8's read budget: a value that cannot BE a name is never looked up (am-6 §3) | ∀ `_HOSTILE_IDENTIFIERS` → zero reads | ∀ over the corpus — SAFE for the corpus's shapes; GS KILLED (slug-legal `"z"*65`); dotted shape absent until r4a (G2) |
| Q3 | the refusal's id bound is ONE source (am-6 MP-2) | perturbed constant → exactly the patched count of ids | **∀ over the slice — SAFE** (X2 KILLED). **The served PROSE is a second source, unobserved** → PX2 SURVIVES → **MP-R4-7**. Over-strict leg: MP2DEF (one source, def-time capture) is RED — §8 R-4 |
| Q4 | mint-once: re-register never changes `owner_principal`/`owner_agent`/`scope` (ruling §2.2 row 2, am-4 MP-F) | α row + legacy row (unstamped) + same-principal re-register | **∀ over ROWS — SAFE** (r3: N10, X8 KILLED). **GUARDED by "the caller's pair equals the stamps, or the row is unstamped"** → RS1 SURVIVES → **MP-R4-1** |
| Q5 | the fake mirrors the writer ∀ inputs, incl. the RE-register door (am-6 MP-5) | 3 sequences, absolute expectations | FX1 KILLED. **GUARDED by the three ruled sequences** → FX2 SURVIVES (am-8 KB-5 → r4a) → MP-R4-6 |
| Q6 | the fake's guard does not outlive its premise (am-5 FORK-C, am-6 MP-3) | effect: predicate removed at the PACKAGE binding; ∀ corpus × {name, session} must not register | **∀ over silent-skip SPELLINGS — SAFE** (X3, X3b, X3c, X3d, X3e KILLED). **GUARDED by the ONE binding the simulation removes** → FXg SURVIVES → **MP-R4-4**; **GUARDED by "silent"** (a non-silent private fallback is invisible) → FXf SURVIVES → **MP-R4-5** |
| Q7 | FORK-A bound's premise: no generator emits a relation the ∀-ENFORCED sweep cannot see (am-6 MP-4) | `unseen = relations(derived) − relations(swept)`, keyed `(edge, (IN, OUT))`, pinned ∅ | ∀ over derived generators — SAFE for NEW edges (R5 KILLED). the r4 pin is GUARDED by the key's omission of `ENFORCED` (R5b survives it) — **but the premise is ∀-pinned by packet 07's `test_this_slice_contains_neither_a_relation_table_nor_a_sequence`, which kills R5 AND R5b in the full suite (§4.5) — SAFE at suite level** |
| Q8 | an exemption is evidence-backed, both directions, and reds on drift (am-7) | exact (file, binding, text) + live two-witness evidence + stale check | SAFE — SLUGDRIFT, CONVERGE red (§4.3/§4.4). Construction note: the stale check keys on PATH only (`site.split(":")[0]`), so a second exemption in the SAME file could mask a stale sibling — moot with one entry (§8 R-3) |

## 6a. P1c — REACH TABLE (every instrument r4 introduces or leans on)
Legs: **E** = empirical (a wrong build or reach edit in scratch + a control), **C** = construction-inspection.
| instrument | reach | coverage checked? | effect / proxy | one source by mutation | verdict · leg |
|---|---|---|---|---|---|
| text ∀ pin (`_classify_charset_constants` over `parse_production_trees(include_scripts=False)`) | **DERIVED** from `[tool.uv.workspace] members` + rglob of each `<m>/<m>` | **yes** — `assert_scan_reached_every_member` (equality, fails closed on empty); + non-vacuity: exactly ONE definition must be found | static PROXY by design (its effect twin is the mutation pin) | key asserted IN the live `AGENT_NAME_PATTERN.pattern` | **SAFE · E** — MEM1 (new member's paste named), MEM2 (src-layout member → declared-not-scanned), TWP/TWS (non-loremaster members), KEYDRIFT. Stated reach parameter `include_scripts=False` (am-8 KB-3; C: flipping it reds `scripts/c3_wrongbuild_driver.py`'s fixture string — seen in my awk sweep). Tests excluded → FXf's fallback copy invisible (MP-R4-5) |
| exemption evidence (`_assert_every_exemption_is_a_DIFFERENT_language`) | the one dict entry | stale check (path-keyed) | **effect** — computed live both directions | the exempt text is read LIVE from the module and compared to the adjudicated text | **SAFE · E** (SLUGDRIFT, CONVERGE) |
| SKIP-gate effect legs (`_traffic_line_lookups` + `_LookupCountingRegistry`) | ONE call site (the gate) — hand-picked, by ruling | the corpus leg has a positive control (a legal value IS looked up) | **effect** (registry reads; a proxy-after gate still reds — construction: the read IS the observation) | mutation of the shared predicate via `patch_shared_object_everywhere` (X1 KILLED) | **MISSING PIN on the legal-input axis · E** — G1 → 2905/0 (MP-R4-3) |
| `_IDENTIFIER_DECISION_CONSUMERS` (mutation pin) | **hand-list**, now STATED as such (am-6 §4) | no | effect | yes, per listed entry point | accepted bound · C (awk sweep: no unlisted production decider at `e80a854`) |
| MP-3 effect pin | the predicate removed at ONE binding (`lorerunes` package attr) | HEAD control (the guard visibly skips at HEAD) | effect — but of SILENT registration only | n/a | **MISSING PIN · E** — FXg (simulation reach) and FXf (non-silent fallback) → 2905/0 each (MP-R4-4/-5) |
| MP-2 perturbation (`R_Q5_1[perturbed-bound]`) | the slice | yes (count asserted independently) | effect on the served ids | **yes** (X2 KILLED) — for the slice; the prose is unobserved | SAFE for the slice · E; PX2 → MP-R4-7 |
| MP-4 premise pin | swept = `ALL_DDL_GENERATORS` (hand-list, the FORK-A bound); unseen over `schema_ddl_generators()` (DERIVED) | anti-vacuity (swept sees ≥ 1 relation) | **PROXY key** `(edge, endpoints)` for "the definition the sweep certified" | n/a | proxy key, but REDUNDANT with packet 07's stronger pin · E — R5b killed in the full suite (§4.5); residual §8 R-1 |
| MP-5 re-register parity rows | 3 ruled sequences | absolute expectations on each | effect (stamps read back) | n/a | FX1 KILLED · E; FX2 → r4a (KB-5); RS1 → MP-R4-1 |
| `pending_contracts.yaml` + currency (relied on) | derived from the live mypy transcript | self-destruct both ways | effect | n/a | §7 |

## 6b. KB-1…KB-5 (the r4 author's candidates; amendment-8 `2f16ac9` rules them — read after my builds were declared)
| KB | amendment-8 ruling | can I build a wrong build through it at `e80a854`? | class |
|---|---|---|---|
| KB-1 dotted corpus | CLOSE — `"fixer.b"` joins the corpus (r4a) | **yes — G2** (reworded dotted widening at the gate) → 2905/0. The r4a value is exactly my KP-G2 (REF green, G2 red), so r4a kills G2. ⚠ It does **not** kill G1 (a NARROWING conjunct) — that needs a legal cap witness (MP-R4-3) | SAME-CLASS |
| KB-2 reworded / assembled class | PINNED BOUND (negative control + message, r4a) | **yes — TWR** → 2905/0, exactly as the instrument's threat model states | SAME-CLASS, bound |
| KB-3 `include_scripts=False` | ACCEPTED reach parameter (docstring) | not built (a `scripts/` decider is outside production). C: the flag is self-revealing — `scripts/c3_wrongbuild_driver.py` carries the key text (my awk sweep), so flipping it reds | SAME-CLASS, accepted |
| KB-4 docstring quoting the rule reds | NOT a bound (the red is correct) | no wrong build — TWQ shows the red fires (`agents.py:405`). ⚠ The failure text at `e80a854` still teaches *"a docstring states the rule in words"*; am-8 amends it (r4a) | n/a |
| KB-5 different consistent pair | CLOSE — one parity row (r4a) | **yes — FX2** (fake) → 2905/0 **and RS1 (REAL writer)** → 2905/0. ⚠ **Am-8's premise "the real writer is pinned mint-once on it" is FALSE** (the r2 pin re-registers with the SAME principal). r4a's row closes both ONLY with an ABSOLUTE real-side expectation (owner stays the first principal), as the r4 rows carry; a `real == fake`-only row passes RS1+FX2 together (construction) | NEW-CLASS (MP-R4-1, MP-R4-6) |
| FORK-E | reading (i) confirmed | no build attempted — (i) is what the pin does (count asserted independently of the sample) | — |

### 4.5 FULL-SUITE leg for every contract survivor (alone, `-n 12`, `run_full.sh` §A.7 — memory watchdog, provenance printed)
Survivors of the 24 files were combined where their anchors are disjoint (a red in one cannot be masked by another —
reds from independent seams add):
- **COMBO1 = RS1 + G1 + FXg + FX2 + R5b + PX2** (launched 01:41:15, 29 GiB available; lowest 22 GiB): **`2 failed, 11426
  passed, 62 skipped, 3 xfailed`** — both reds are R5b's, in `test_floor_calibration_schema.py` (`…test_every_table_
  definition_is_IF_NOT_EXISTS`, `…test_this_slice_contains_neither_a_relation_table_nor_a_sequence`; messages name the
  lease slice's `DEFINE TABLE OVERWRITE to TYPE RELATION …`). **RS1, G1, FXg, FX2, PX2 survive the FULL suite.**
- **COMBO2 = G2 + FXf + TWR** (launched 01:50:06, 28 GiB; lowest 22 GiB): **`11428 passed, 62 skipped, 3 xfailed`, exit 0 —
  all three survive the FULL suite.**
- Attribution check, `test_floor_calibration_schema.py` alone: REF `42 passed` · R5b `2 failed, 40 passed` · **r3's R5
  `2 failed, 40 passed`** (same two pins).

## 2. SATISFIABILITY — my OWN reference (`my_ref_build_r4.py`, §A.1)
- **Instrument:** adversary-r3's `my_ref_build.py` VERBATIM (extracted from `REPORT-adversary-63c-i-a-r3.md` §A.1 at
  `c22419d` — it carries the builder's granted FORK-C guard deletion and the lint cleanups) + ONE r4 leg of mine: the
  amendment-6 swept-up one-liner `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern`, the `lorerunes` import placed
  where ruff's I001 sorts it. Written without reading the author's `r4_ref_build_extra.py`. Scratch `…/scratchpad/ref`,
  commit `3b6a12a` (branch `adv4-ref`). Provenance: `loremaster.__file__ =
  /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/ref/loremaster/loremaster/__init__.py`;
  `is_legal_identifier("fixer-b"), is_legal_identifier("fixer-b\n")` → `True False`; the brief ASSERT renders
  `ASSERT string::matches($value, '^[a-z0-9][a-z0-9_-]{0,63}$')` (byte-identical, as amendment-6 requires).
- **Lint AFTER the cleanups:** `uv run ruff check .` → `All checks passed!`.
- **24 contract files, `-n 8`, alone:** `2905 passed, 19 skipped, 4 warnings in 317.33s` — 0 failed, 0 errors.
- **FULL SUITE ALONE, `-n 12` (2026-09-25 01:32:04–01:41:04 EDT; 28 GiB available at launch, lowest 22 GiB; no other
  pytest on the box): `11428 passed, 62 skipped, 3 xfailed, 7 warnings in 536.45s` — 0 failed, 0 errors, exit 0.**
  **= the author's §SAT count exactly, on an independently written reference.**

## 7. `scripts/pending_contracts.yaml` (r4 edits: `test_agent_registry.py` attr-defined 3 → 4 + reason; the replaced pin's name repointed in the `_comms_fakes.py` comment)
- **HEAD** (lane `head`, unbuilt): `pending_contract_gate.py --currency --legs typecheck,ruff` → **`typecheck RED_ADJUDICATED
  — 20 residual(s)`, owned by `packet-63c-i-a-contract-r2` · `packet-63c-i-a-contract-r3`** · `ruff GREEN` · pytest NOT_RUN
  (by design — never a bare `--currency`, #466). Reproduces the author's 20.
- **Built world** (lane `ref` @ `adv4-ref`): **`typecheck RED_ORPHANED — 11 residual(s)`, ALL ELEVEN `SELF-DESTRUCT`** (10
  registered files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"); ruff GREEN; **0 real mypy
  errors**. Reproduces the author's 11.
- **#461 (would any entry self-destruct WRONGLY?):** no — every registered file is mypy-red at HEAD (20 residuals, all
  adjudicated), and the re-counted `attr-defined: 4` matches HEAD's transcript (else HEAD would show a count mismatch, not
  RED_ADJUDICATED). Process note (unchanged from r3): the builder deletes BOTH entries in the build commit.
- The repointed comment names `test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists` —
  resolves (collected).

## 11. P6 — corpse sweep (awk, BARE pattern `HEAD_RED_import_guard|import_guard_is_deleted`, every `git ls-files` path; measured 2026-09-25 at `2f16ac9`)
10 hits, each individually:
- `loremaster/tests/test_agent_registry.py:2145` — the DUAL comment naming the deleted pin · **OK (DUAL)**.
- `REPORT-adversary-63c-i-a-r3.md:145`, `:191`, `:583` — r3's measured history · **OK (dated history)**.
- `REPORT-contract-63c-i-a-r3.md:47`, `:62`, `:141` — r3 author's history · **OK**; `:942` — its r4 correction note marking
  the pin superseded · **OK**.
- `REPORT-contract-63c-i-a-r4.md:92`, `:121` — the author's DUAL/RED rows · **OK**.
- **No corpse: no live test asserts the retired pin; `pending_contracts.yaml` and `_comms_fakes.py` were repointed.**

### 3.1 DIFF of my E1–E5 against the author's §DUAL (read AFTER §3 was written)
- **Author rows ungrounded in the diff:** none. Their E1 ↔ my E1; their E2 (a never-committed r4 draft pin folded into the
  text pin) has no hunk in `39935f6..e80a854` — correct, nothing to ground; their "ADDITIVE" list matches mine.
- **Mine, absent from theirs:** **E1(c) — the deleted pin's "PRESENCE reds" virtue.** Their E1 lists (a) no silent skip and
  (b) HEAD anti-vacuity, and claims the effect pin reds "every silent-skip spelling". True for SILENT spellings; the
  deleted pin ALSO red two non-silent / other-binding guards that the effect pin cannot see — FXf and FXg, both full-suite
  survivors (§4.5), both RED under the restored pin KP-E1c. **A virtue lost by the replacement, not recorded** → MP-R4-4/-5.
  (Amendment-6 ruled the deletion — "two pins for one property, one of them a proxy" — on the premise that the two pins
  observe ONE property; FXf is the build that shows they observe two.) E2–E5: lint/prose, no virtue (theirs omit them —
  harmless).

## 8. Residuals (each with an individual verdict)
- **R-1 · adversary-r3's MP-4 (R5) was a SCOPED-FILE-SET artifact — the premise was already pinned.** r3 measured R5 on 24
  files only; `test_floor_calibration_schema.py::TestTheDdlDecisionRuleIsEnforcedMechanically::test_this_slice_contains_
  neither_a_relation_table_nor_a_sequence` (packet 07, `147be46`) kills R5 (and R5b) — measured §4.5. So r4's premise pin
  duplicates a stronger pre-existing pin, and its `(edge, endpoints)` key is weaker than that pin (R5b passes it). ·
  **Sidecar's call: cite the packet-07 pin in the FORK-A bound's docstring (it IS the premise's observation), and either
  delete r4's premise pin as redundant or key it on the full statement text. Lesson for every adversary in this chain,
  mine included: a survivor is a CONTRACT survivor until the full suite is run on it** (hence §4.5).
- **R-2 · prose over-claim in the instrument:** `TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA`'s section header
  says the legs make *"any private decider at that call site, whatever it spells, … visible"* — false for a NARROWING
  conjunct (G1, full-suite survivor). · **Fix with MP-R4-3's witness, or narrow the sentence.**
- **R-3 · stale-exemption check keys on PATH only** (`{site.split(":", 1)[0] …}`): a second exemption in the same file
  could mask a stale sibling. · **Moot with one entry (construction); note for the next entry.**
- **R-4 · MP-2's perturbation reds a ONE-source build that captures the constant at DEF time** (MP2DEF: `sample_size: int =
  _REFUSAL_ID_SAMPLE_SIZE`), and its failure text then says *"a restated literal: two sources"* — wrong diagnosis for that
  build. · **Low (a builder writes a module-global read); the failure text could say "does not read … at CALL time".**
- **R-5 · FXg's survival depends on module layout** (the predicate defined in a `lorerunes.identifiers` submodule — both
  reference builds do this). · **Recorded; MP-R4-4's pin (remove at EVERY binding) is layout-independent.**
- **R-6 · amendment-8 KB-5's premise is false** (the real writer is NOT pinned on a different consistent pair) — RS1. ·
  **Escalated as MP-R4-1; the r4a row must carry the absolute real-side expectation.**
- **R-7 · my mispredictions:** GS (declared `[fixer-b]` only; also `[wave7]` + corpus — slug-legal `"z"*65`, safe
  direction). R5b declared SURVIVE — held for the contract files, killed by the full suite (R-1). Not re-declared.
- **R-8 · author claims re-derived:** SAT `11428/62/3` ✓ (§2); 8 of the author's 10 builds re-run and killed exactly
  (X1 X2 X3 X3b X3c X3d R5 FX1) + SLUGDRIFT ✓; TW (rebind forgotten) not re-run as a build — its effect is §1's HEAD red
  naming `surreal_schema.py:490`, construction-equivalent; RED@HEAD ✓ (§1); text pin names exactly `agents.py` +
  `surreal_schema.py` ✓; built world 11 SELF-DESTRUCTs ✓ (§7); DRY "17 new symbols" re-counted from their §DRY: 17 ✓.
- **R-9 · deviations of mine:** (1) wrong builds via my declare-then-diff driver, not `mutation_proof.py` (multi-edit,
  declared-to-survive, non-production files) — the tool's discipline kept (collect-only declaration before any run, both-way
  diff); (2) the full-suite runs launched at **28–29 GiB available, 1–2 GiB under the brief's ~30 GB guideline**, after ~25
  min of polling found it flat at 29; mitigated by a watchdog that would kill my pytest by PID below 12 GiB — lowest observed
  22 GiB in all three runs; no other pytest on the box; (3) one turn lost to an API-server error mid-run (lead resume ping);
  the only partial artifact (a lint-failing reference commit) was rebuilt and re-committed before any run used it; (4) my
  first full-suite launch refused itself: its "another pytest -n running" guard matched the LEAD's watcher shell (command
  text contains both words) — the #228 self-matching class, on a neighbour; fixed to match python/pytest/uv processes only;
  the guard then saw my own run (positive control).
- **R-10 · lore:** register/heartbeat worked throughout; no lore friction hit. grep/rg hook-blocked (#473) — awk used.

## A. Instruments (pasted VERBATIM — scratch-only; my writable set is this report)
Scratch root: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad`. Lanes `ref`, `head` made by `./scripts/scratch_copy.sh` (provenance asserted by the tool; every driver re-asserts `loremaster.__file__`). `files4.txt` = `git diff --name-only 0b8ce37 e80a854 -- 'loremaster/tests/test_*.py'` ∪ {`test_comms_wiring.py`, `test_enforced_relations.py`, `test_derivation_source_unification.py`} (24 files); `files_ctl.txt` = `test_agent_registry.py` + `test_agent_governance_63c_i_a.py`.

### A.1 `my_ref_build_r4.py`
Lines 1–265 are adversary-r3's `my_ref_build.py` byte-for-byte except its first docstring line (md5 of r3's file as extracted from `REPORT-adversary-63c-i-a-r3.md` §A.1 @ `c22419d`: `7c06739b9f03…`; full r4 file md5 `3e419c754445…`) — cite that paste for the base. The ENTIRE file is pasted below anyway, so it can be re-run verbatim:
```python
"""adversary-63c-i-a-r4 (base: adversary-r3 §A.1 verbatim, itself adversary-r2's) — an INDEPENDENT reference (believed-correct) 63c-i-a build.

Written from the production source + amendment-2 §A1–A4, NOT from the r2 author's ref_build_r2.py.
Base legs (Q3 drop, W1-1 routing, Q5 scope-keyed migrate + row precondition) re-use the PRIOR
adversary's §A.1 anchors (b46d3f2 — a different author than the contract under grade); the A2/A3/A4
legs are my own.

Usage: uv run --no-project python my_ref_build.py <scratch-root>
Each edit asserts its anchor occurs exactly once (a silent no-op edit is a failed setup — #194).
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


def create(rel: str, body: str) -> None:
    path = ROOT / rel
    assert not path.exists(), f"{rel} already exists"
    path.write_text(body)


SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
RUNES_INIT = "lorerunes/lorerunes/__init__.py"

# ---- Q3: drop name/session/role ASSERTs (KEEP status) -------------------------------------------
edit(
    SCHEMA,
    '    ("name", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("session", _CHUNK_STRING_TYPE, _IDENTIFIER_CHARSET_ASSERT),\n'
    '    ("role", _CHUNK_STRING_TYPE, _NON_EMPTY_STRING_ASSERT),\n    ("model"',
    '    ("name", _CHUNK_STRING_TYPE, ""),\n'
    '    ("session", _CHUNK_STRING_TYPE, ""),\n'
    '    ("role", _CHUNK_STRING_TYPE, ""),\n    ("model"',
)
# ---- W1-1: the governed triple comes only from the ONE emitter ----------------------------------
edit(SCHEMA, '    ("owner_principal", "option<record<principal>>", ""),\n    # packet 62, Fork 1', "    # packet 62, Fork 1")
edit(
    SCHEMA,
    "    statements.append(\n"
    "        _plain_index(\n"
    "            AGENT_TABLE,\n"
    '            f"{AGENT_TABLE}_owner_principal",\n'
    "            _AGENT_OWNER_PRINCIPAL_INDEX_FIELDS,\n"
    "        )\n"
    "    )\n",
    "    statements += [\n"
    "        _define_field(AGENT_TABLE, name, type_expr, constraint=constraint)\n"
    "        for name, type_expr, constraint in _governed_field_specs()\n"
    "    ]\n"
    "    statements += _governed_index_statements(AGENT_TABLE)\n",
)
edit(SCHEMA, '_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS = ("owner_principal",)\n', "")

# ---- A4: the identifier DECISION + the pattern MOVE to lorerunes ---------------------------------
create(
    "lorerunes/lorerunes/identifiers.py",
    '"""The comms identity charset — ONE pattern, ONE decision (63c-i-a amendment-2 A4)."""\n\n'
    "from __future__ import annotations\n\n"
    "import re\n\n"
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n\n\n'
    "def is_legal_identifier(value: str) -> bool:\n"
    '    """Whether ``value`` matches ``AGENT_NAME_PATTERN`` IN FULL (``fullmatch``, finding #210)."""\n'
    "    return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
)
edit(
    RUNES_INIT,
    "from lorerunes.engine_rejection import reclassify\n",
    "from lorerunes.engine_rejection import reclassify\n"
    "from lorerunes.identifiers import AGENT_NAME_PATTERN, is_legal_identifier\n",
)
edit(RUNES_INIT, "__all__ = [\n", '__all__ = [\n    "AGENT_NAME_PATTERN",\n    "is_legal_identifier",\n')
edit(
    AGENTS,
    'AGENT_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n',
    "AGENT_NAME_PATTERN = _RUNES_AGENT_NAME_PATTERN  # re-export (A4: the pattern lives in lorerunes)\n",
)
edit(
    AGENTS,
    "from lorerunes import parse_credential\n",
    "from lorerunes import AGENT_NAME_PATTERN as _RUNES_AGENT_NAME_PATTERN\n"
    "from lorerunes import is_blank, is_legal_identifier, keep_scope, parse_credential\n",
)
edit(AGENTS, "from loremaster.render import render_attributed\n", "from loremaster.render import render_attributed, render_fenced\n")
edit(
    SERVER,
    "        return AGENT_NAME_PATTERN.fullmatch(value) is not None\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - house lazy-import idiom\n\n"
    "        return is_legal_identifier(value)\n",
)

# ---- A4 register MOVE (teaching) + A3 XOR + A2 stamp --------------------------------------------
edit(
    AGENTS,
    "class AgentIdentityConflictError(AgentRegistryError):",
    "class InvalidAgentIdentityError(AgentRegistryError):\n"
    '    """A register argument violates the agent identity rules (63c-i-a §4.2 MOVE)."""\n\n\n'
    "class AgentIdentityConflictError(AgentRegistryError):",
)
edit(
    AGENTS,
    "        owner_principal_id: str | None = None,\n    ) -> AgentRegisterResult:",
    "        owner_principal_id: str | None = None,\n        session_keep_id: str | None = None,\n    ) -> AgentRegisterResult:",
)
edit(
    AGENTS,
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
    "        if (owner_principal_id is None) != (session_keep_id is None):\n"
    "            raise AgentRegistryError(\n"
    '                "register called with an owner but no session keep (or the reverse) — a "\n'
    '                "server-side caller bug; nothing was written"\n'
    "            )\n"
    '        for field_name, value in (("name", name), ("session", session)):\n'
    "            if not is_legal_identifier(value):\n"
    "                raise InvalidAgentIdentityError(\n"
    '                    f"agent {field_name} must match {AGENT_NAME_PATTERN.pattern} (lowercase letters, "\n'
    "                    f\"digits, '_' or '-', 1-64 chars, starting with a letter or digit); nothing was \"\n"
    '                    f"written — register again with a legal {field_name}. The rejected value was:\\n"\n'
    '                    f"{render_fenced(value)}"\n'
    "                )\n"
    "        if is_blank(role):\n"
    "            raise InvalidAgentIdentityError(\n"
    '                "agent role must not be blank — nothing was written; register again with a role "\n'
    "                \"(e.g. 'builder')\"\n"
    "            )\n"
    "        agent_id = self._agent_id(session, name)\n        existing_row = await self._select_row(agent_id)\n        now = datetime.now(UTC)\n",
)
edit(
    AGENTS,
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n",
    "                _COL_CAPABILITY_HASH: sha512_hex(capability),\n"
    '                "owner_agent": RecordID(AGENT_TABLE, agent_id),\n'
    '                "scope": keep_scope(session_keep_id) if session_keep_id is not None else None,\n',
)
edit(
    SERVER,
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n        )\n        now = datetime.now(UTC)\n        registered_age_s",
    "            cadence=cadence,\n            owner_principal_id=principal_bare,\n"
    "            session_keep_id=(\n"
    '                str(session_keep.id).split(":", 1)[-1] if session_keep is not None else None\n'
    "            ),\n"
    "        )\n        now = datetime.now(UTC)\n        registered_age_s",
)

# ---- Q5: scope-keyed 3-column migrate + §2.1 row precondition (prior adversary §A.1 anchors) ------
edit(
    PRINCIPALS,
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, principal_store)\n",
    "    if table == AGENT_TABLE:\n        return await _migrate_agent_owner(store, keep_store, principal_store)\n",
)
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
    "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
)
edit(
    PRINCIPALS,
    "    from loremaster.governed import MigrateGovernedResult, governed_exempt\n\n    operator = await resolve_operator_principal(principal_store)\n",
    "    from lorerunes.pdp import keep_scope\n\n"
    "    from loremaster.governed import PROJECT_KEEP_KEY, MigrateGovernedResult, governed_exempt\n\n"
    "    operator = await resolve_operator_principal(principal_store)\n",
)
edit(
    PRINCIPALS,
    "    unmigrated = await _owner_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _owner_count(store, AGENT_TABLE, none=False)\n",
    "    unmigrated = await _scope_count(store, AGENT_TABLE, none=True)\n"
    "    already = await _scope_count(store, AGENT_TABLE, none=False)\n",
)
edit(
    PRINCIPALS,
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner) \"\n"
    "        \"WHERE owner_principal IS NONE\"\n"
    "    )\n",
    "    owned_unscoped = await run_query(\n"
    "        acquire=store.acquire,\n"
    "        drop=store.drop,\n"
    "        url=store.url,\n"
    "        noun=\"governed agent row precondition\",\n"
    "        label=\"governed.agent_precondition.rejected\",\n"
    "        statement=(\n"
    "            f\"SELECT VALUE id FROM {AGENT_TABLE} WHERE scope IS NONE AND owner_principal IS NOT NONE\"\n"
    "        ),\n"
    "        params={},\n"
    "        logger=logger,\n"
    "    )\n"
    "    owned_unscoped_ids = [str(row) for row in (owned_unscoped or [])]\n"
    "    if owned_unscoped_ids:\n"
    "        return MigrateGovernedResult(\n"
    "            table=AGENT_TABLE,\n"
    "            scanned=unmigrated + already,\n"
    "            backfilled=0,\n"
    "            already_migrated=already,\n"
    "            refused=True,\n"
    "            reason=(\n"
    "                f\"{len(owned_unscoped_ids)} agent row(s) carry an owner but no scope \"\n"
    "                f\"({', '.join(owned_unscoped_ids[:10])}) — a multi-principal or half-applied store; \"\n"
    "                \"adjudicate these rows by hand before migrating (§2.1)\"\n"
    "            ),\n"
    "        )\n"
    "    project_keep = await keep_store.get_or_create_keyed(\n"
    "        key=PROJECT_KEEP_KEY, type=\"project\", keeper_email=operator.email, name=\"lore\"\n"
    "    )\n"
    "    project_scope = keep_scope(project_keep.id.partition(\":\")[2] or project_keep.id)\n"
    "    operator_id = operator.id.partition(\":\")[2] or operator.id\n"
    "    backfill_statement = (\n"
    "        f\"UPDATE {AGENT_TABLE} SET owner_principal = type::record('{PRINCIPAL_TABLE}', $owner), \"\n"
    "        \"owner_agent = id, scope = $scope WHERE scope IS NONE\"\n"
    "    )\n",
)
edit(
    PRINCIPALS,
    "            statement=backfill_statement,\n            params={\"owner\": operator_id},\n",
    "            statement=backfill_statement,\n            params={\"owner\": operator_id, \"scope\": project_scope},\n",
)

# ---- r3 (amendment-4 MP-C): the refusal's id bound is a NAMED module constant, USED by the slice ----
edit(
    PRINCIPALS,
    "async def _migrate_agent_owner(\n",
    "#: The refusal names at most this many offending row ids (ruling §6 'ids, bounded'; amendment-4 MP-C).\n"
    "_REFUSAL_ID_SAMPLE_SIZE = 10\n\n\n"
    "async def _migrate_agent_owner(\n",
)
edit(
    PRINCIPALS,
    "owned_unscoped_ids[:10]",
    "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]",
)
# ---- r3 (amendment-5 FORK-C rider 3): the builder's ONE granted test-tree edit — delete the guard --
FAKES = "loremaster/tests/_comms_fakes.py"
edit(
    FAKES,
    "        try:\n"
    "            from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n"
    "        except ImportError:  # HEAD-RED accommodation — delete once the build lands the predicate\n"
    "            return None\n"
    "        return is_legal_identifier\n",
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n",
)
print("adversary-r3 reference build applied (r2 legs + MP-C constant + FORK-C guard deletion)")
# ---- lint-demanded cleanups (the SAT receipt must hold AFTER them) ---------------------------------
edit(AGENTS, "import logging\nimport re\nimport secrets\n", "import logging\nimport secrets\n")
edit(
    PRINCIPALS,
    "                f\"({', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])}) — a multi-principal or half-applied store; \"\n",
    "                f\"({', '.join(owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE])}) — a multi-principal or \"\n"
    "                \"half-applied store; \"\n",
)
print("lint cleanups applied")
# ---- r4 (adversary-63c-i-a-r4): amendment-6 swept-up builder one-liner — the schema's raw-string TWIN of the
# charset text becomes a READ of the ONE lorerunes definition (brief's ASSERT stays byte-identical).
edit(
    SCHEMA,
    '_IDENTIFIER_CHARSET_PATTERN = r"^[a-z0-9][a-z0-9_-]{0,63}$"\n',
    "_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern\n",
)
# (import placed exactly where `ruff check --fix` I001 sorts it — the lint-demanded shape)
edit(SCHEMA, "from lorerunes import PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLES\n", "")
edit(
    SCHEMA,
    "from __future__ import annotations\n\n# The shared authorization vocabulary",
    "from __future__ import annotations\n\n"
    "from lorerunes import AGENT_NAME_PATTERN, PRINCIPAL_ROLE_MEMBER, PRINCIPAL_ROLES\n\n"
    "# The shared authorization vocabulary",
)
print("r4 legs applied (_IDENTIFIER_CHARSET_PATTERN rebind)")
```

### A.2 `my_wbs4.py` (wrong builds + DECLARED expected-RED sets, written before any run)
```python
"""adversary-63c-i-a-r4 — wrong builds applied ON TOP of my independent reference (adv4-ref, my_ref_build_r4.py).

Usage: uv run --no-project python my_wbs4.py <scratch-root> <WB-id> [--declared]
  --declared   print the DECLARED expected-RED node ids (resolved against collected4.txt — the
               `pytest --collect-only -q` output of the 24 contract files (files4.txt), taken on adv4-ref
               BEFORE any wrong-build run) and exit.
Each edit asserts its anchor occurs exactly once (a no-op mutation is a failed setup — #194).
A DECLARED set of [] is my prediction that the build SURVIVES the contract.
Floor builds X1/X2/X3/X3b/R5/FX1 are adversary-r3's (§A.2/§A.3) bodies, re-anchored where r4 moved nothing.
"""

import sys
from pathlib import Path

INST = Path("/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/inst")
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

SCHEMA = "loremaster/loremaster/store/surreal_schema.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
SERVER = "loremaster/loremaster/server.py"
AGENTS = "loremaster/loremaster/agents.py"
FAKES = "loremaster/tests/_comms_fakes.py"
CONFIG = "loremaster/loremaster/config.py"
RUNES_IDS = "lorerunes/lorerunes/identifiers.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
ENF = "test_message_enforcement_63b_ii_a.py"

TEXT_PIN = "test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition"
SKIP_MUT = "test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier"
SKIP_CORPUS = "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus"
FAKE_EFFECT = "test_the_fake_never_silently_skips_the_identity_decision_once_the_predicate_exists"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
REREG_PARITY = "test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door"
PREMISE = "test_KNOWN_BOUND_premise_no_generator_emits_a_relation_the_ENFORCED_sweep_cannot_see"

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # --- the r3 floor (must now be KILLED, each on its r4 pin) ---
    "X1": [(REG, [SKIP_MUT]), (REG, [TEXT_PIN])],  # private drifted regex at the SKIP gate
    "X2": [(GOV, [RQ51, "perturbed-bound"])],  # literal [:10] beside the constant
    "X3": [(REG, [FAKE_EFFECT])],  # guard kept as `except Exception`
    "X3b": [(REG, [FAKE_EFFECT])],  # guard kept as ruled (`except ImportError`)
    "X3c": [(REG, [FAKE_EFFECT])],  # bare `except:`
    "X3d": [(REG, [FAKE_EFFECT])],  # getattr(lorerunes, ..., None)
    "X3e": [(REG, [FAKE_EFFECT])],  # except builtins.ImportError
    "R5": [(ENF, [PREMISE])],  # un-ENFORCED holds(lease→task) inside an unswept emitter
    "FX1": [(REG, [REREG_PARITY, "alpha-then-credentialed"])],  # the fake heals on re-register
    # --- new wrong builds against r4's instruments ---
    "G1": [],  # SKIP gate NARROWED by a private conjunct: legal names > 32 chars are never looked up
    "G2": [],  # SKIP gate WIDENED by a reworded private disjunct (dotted service names), witnesses excluded
    "GS": [(REG, [SKIP_MUT, "fixer-b"])],  # CONTROL: gate decides with config.SLUG_PATTERN (no hyphen)
    "FXg": [],  # fake guard KEPT, but imports the predicate from the SUBMODULE (delattr on the package misses it)
    "FXf": [],  # fake guard KEPT with a PRIVATE-regex fallback (the charset text inside the TEST tree)
    "RS1": [],  # REAL writer: re-register re-stamps an ALREADY-stamped row from the caller's pair (takeover)
    "FX2": [],  # FAKE: same as RS1, fake side only (KB-5's door) — at e80a854
    "R5b": [],  # lease emitter re-defines the ENFORCED `to` relation WITHOUT ENFORCED (same name + endpoints)
    "PX2": [],  # the refusal's PROSE restates the bound: "(first 10 shown)" beside the constant-read slice
    "TWR": [],  # KB-2: a REWORDED charset twin at a new production site (bound by the threat model)
    "TWP": [(REG, [TEXT_PIN])],  # CONTROL: a VERBATIM paste into loresigil (reach: a non-loremaster member)
    "TWS": [(REG, [TEXT_PIN])],  # CONTROL: a verbatim paste into lorescribe
    "TWQ": [(REG, [TEXT_PIN])],  # CONTROL: a production docstring QUOTING the rule (KB-4: red is correct)
    "SLUGDRIFT": [(REG, [TEXT_PIN])],  # exemption text drifts → private
    "MP2DEF": [(GOV, [RQ51, "perturbed-bound"])],  # SAT hazard: ONE source, captured at def time (default arg)
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (INST / "collected4.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

GUARD_DELETED = (
    "        from lorerunes import is_legal_identifier  # noqa: PLC0415 - call-time read (mutation-visible)\n\n"
    "        return is_legal_identifier\n"
)
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"


def guard(except_line: str, import_line: str = "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n",
          fallback: str = "            return None\n") -> None:
    edit(FAKES, GUARD_DELETED, "        try:\n" + import_line + except_line + fallback + "        return is_legal_identifier\n")


if WB == "X1":
    edit(SERVER, GATE,
         "        if attribution is None or re.fullmatch(r\"[a-z0-9][a-z0-9_.-]{0,63}\", attribution) is None:\n")
elif WB == "X2":
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:10]")
elif WB == "X3":
    guard("        except Exception:  # noqa: BLE001\n")
elif WB == "X3b":
    guard("        except ImportError:\n")
elif WB == "X3c":
    guard("        except:  # noqa: E722\n")
elif WB == "X3d":
    edit(FAKES, GUARD_DELETED,
         "        import lorerunes  # noqa: PLC0415\n\n"
         "        return getattr(lorerunes, \"is_legal_identifier\", None)\n")
elif WB == "X3e":
    edit(FAKES, GUARD_DELETED,
         "        import builtins  # noqa: PLC0415\n\n"
         "        try:\n"
         "            from lorerunes import is_legal_identifier  # noqa: PLC0415\n"
         "        except builtins.ImportError:\n"
         "            return None\n"
         "        return is_legal_identifier\n")
elif WB == "R5":
    edit(SCHEMA,
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         "    statements.append(_define_relation_table(\"holds\", LEASE_TABLE, TASK_TABLE))\n"
         "    return statements\n")
elif WB == "R5b":
    edit(SCHEMA,
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n    return statements\n",
         "        _define_field(LEASE_TABLE, LEASE_FENCE_EPOCH_COLUMN, \"int\", constraint=\"DEFAULT 0\"),\n"
         "    ]\n"
         "    statements.append(_define_relation_table(TO_RELATION, MESSAGE_TABLE, AGENT_TABLE))\n"
         "    return statements\n")
elif WB == "FX1":
    edit(FAKES,
         "        # status resets to active unconditionally (retired already excluded above).\n",
         "        if self.db.scopes.get(agent_id) is None and session_keep_id is not None:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n"
         "        # status resets to active unconditionally (retired already excluded above).\n")
elif WB == "FX2":
    edit(FAKES,
         "        # status resets to active unconditionally (retired already excluded above).\n",
         "        if self.db.scopes.get(agent_id) is not None and session_keep_id is not None:\n"
         "            self.db.scopes[agent_id] = keep_scope(session_keep_id)\n"
         "            self.db.owners[agent_id] = owner_principal_id\n"
         "        # status resets to active unconditionally (retired already excluded above).\n")
elif WB == "RS1":
    # re-register: when the row ALREADY carries a scope and the caller supplies a consistent pair, the
    # caller's pair is re-stamped (an ownership TAKEOVER of a stamped row; unstamped rows stay untouched).
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
elif WB == "GS":
    edit(SERVER, GATE,
         "        from loremaster.config import SLUG_PATTERN  # noqa: PLC0415\n\n"
         "        if attribution is None or re.fullmatch(SLUG_PATTERN, attribution) is None:\n")
elif WB == "FXg":
    guard("        except ImportError:\n",
          import_line="            from lorerunes.identifiers import is_legal_identifier  # noqa: PLC0415\n")
elif WB == "FXf":
    guard("        except ImportError:  # robustness: fall back to the rule's text\n",
          fallback=("            import re  # noqa: PLC0415\n\n"
                    "            return lambda value: re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"))
elif WB == "PX2":
    edit(PRINCIPALS,
         "                \"half-applied store; \"\n",
         "                \"half-applied store (first 10 ids shown); \"\n")
elif WB == "TWR":
    edit(AGENTS, "class InvalidAgentIdentityError(AgentRegistryError):",
         "_LEGACY_NAME_RE = re.compile(r\"^[0-9a-z][0-9a-z_-]{0,63}$\")  # reworded class (KB-2)\n\n\n"
         "class InvalidAgentIdentityError(AgentRegistryError):")
    edit(AGENTS, "import logging\nimport secrets\n", "import logging\nimport re\nimport secrets\n")
elif WB == "TWP":
    path = ROOT / "loresigil/loresigil/__init__.py"
    path.write_text(path.read_text() + "\nimport re as _re\n_NAME = _re.compile(r\"^[a-z0-9][a-z0-9_-]{0,63}$\")\n")
elif WB == "TWS":
    path = ROOT / "lorescribe/lorescribe/__init__.py"
    path.write_text(path.read_text() + "\n_NAME_TEXT = r\"^[a-z0-9][a-z0-9_-]{0,63}$\"\n")
elif WB == "TWQ":
    edit(AGENTS, "class InvalidAgentIdentityError(AgentRegistryError):\n    \"\"\"A register argument violates the agent identity rules (63c-i-a §4.2 MOVE).\"\"\"",
         "class InvalidAgentIdentityError(AgentRegistryError):\n    \"\"\"A register argument violates ^[a-z0-9][a-z0-9_-]{0,63}$ (63c-i-a §4.2 MOVE).\"\"\"")
elif WB == "SLUGDRIFT":
    edit(CONFIG, 'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]*$"', 'SLUG_PATTERN: str = r"^[a-z0-9][a-z0-9_]{0,127}$"')
elif WB == "MP2DEF":
    edit(PRINCIPALS,
         "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n"
         "    principal_store: PrincipalStore,\n) -> MigrateGovernedResult:",
         "async def _migrate_agent_owner(\n    store: StoreHandle,\n    keep_store: KeepStore,\n"
         "    principal_store: PrincipalStore,\n    sample_size: int = _REFUSAL_ID_SAMPLE_SIZE,\n"
         ") -> MigrateGovernedResult:")
    edit(PRINCIPALS, "owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]", "owned_unscoped_ids[:sample_size]")
else:
    raise SystemExit(f"unknown {WB}")
print(f"{WB} applied")
```

### A.3 `run_lane4.sh` (declare-then-diff lane driver; `run_lane4_ctl.sh` = the same file with `files4.txt`→`files_ctl.txt` and `wb_`→`ctl_` via sed)
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4 lane driver: for each WB, reset LANE to adv4-ref, resolve the DECLARED expected-RED set
# from collected4.txt (collect-only on adv4-ref, taken BEFORE any wrong-build run), apply the build, run the 24
# contract files (-n 8, ONE pytest session at a time), diff observed vs declared BOTH ways from junit, restore.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f adv4-ref && git clean -fdq
  [ -z "$(git status --porcelain)" ] || { echo "$WB: LANE DIRTY after reset — abort"; exit 2; }
  uv run --no-project python "$INST/my_wbs4.py" "$LANE" "$WB" --declared | sort > "$INST/wb_${WB}.declared" \
    || { echo "$WB: declaration failed"; exit 2; }
  uv run --no-project python "$INST/my_wbs4.py" "$LANE" "$WB" || { echo "$WB: APPLY FAILED (no-op edit?)"; exit 2; }
  [ -n "$(git status --porcelain)" ] || { echo "$WB: build left the lane CLEAN — mutation did not land"; exit 2; }
  uv run python -c "import loremaster,pathlib; assert pathlib.Path(loremaster.__file__).resolve().is_relative_to('$LANE'), loremaster.__file__" \
    || { echo "$WB: PROVENANCE FAILED"; exit 2; }
  timeout 1800 uv run pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/wb_${WB}.xml" $(cat "$INST/files4.txt") \
    > "$INST/wb_${WB}.log" 2>&1
  uv run --no-project python - "$INST/wb_${WB}.xml" > "$INST/wb_${WB}.observed" <<'PY'
import sys, xml.etree.ElementTree as ET
for case in ET.parse(sys.argv[1]).iter("testcase"):
    if case.find("failure") is not None or case.find("error") is not None:
        cls = case.get("classname", "")
        path = cls.replace(".", "/")
        # junit classname = loremaster.tests.test_x.TestY → map to the collect-only id shape by suffix match
        print(f"{cls}::{case.get('name')}")
PY
  sort -o "$INST/wb_${WB}.observed" "$INST/wb_${WB}.observed"
  tail_line=$(tail -1 "$INST/wb_${WB}.log")
  # both-ways diff on the TEST NAME (node id tail after the last '::'), class-qualified where junit gives it
  uv run --no-project python - "$INST/wb_${WB}.declared" "$INST/wb_${WB}.observed" <<'PY' > "$INST/wb_${WB}.diff"
import sys
declared = {l.strip() for l in open(sys.argv[1]) if l.strip()}
observed = {l.strip() for l in open(sys.argv[2]) if l.strip()}
def key(node):  # collect "path.py::Class::test[p]" / junit "pkg.mod.Class::test[p]" -> "Class::test[p]"; module-level -> "::test"
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
  echo "== $WB :: $tail_line :: $(head -1 "$INST/wb_${WB}.diff")"
done
git checkout -q -f adv4-ref && git clean -fdq
```

### A.4 `test_adv_r4_killpins.py` + `kp_pairs4.sh`
```python
"""adversary-63c-i-a-r4 kill-pins — each should be GREEN on my reference (adv4-ref) and RED on exactly its wrong build.

Copied into loremaster/tests/ of the lane for a run, then removed (scratch only). Imports the contract module as a
MODULE (never its Test* classes by name) so pytest collects nothing extra (adversary-r3 R-8 quirk avoided).
"""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest
import test_agent_registry as contract
from _comms_fakes import FakeAgentRegistry
from _enforced_relations_scaffold import (
    ALL_DDL_GENERATORS,
    apply_ddl,
    emit_schema_ddl,
    migration_db,  # noqa: F401 - re-exported pytest fixture
    relation_table_statements,
    schema_ddl_generators,
)
from _logging_fixtures import module_level_bindings_of
from _surreal_harness import run
from lorerunes.pdp import keep_scope

from loremaster.store.surreal_schema import (
    TO_RELATION,
    generate_agent_ddl,
    generate_lease_ddl,
    generate_message_ddl,
)

_MAX_LEGAL = "a" * 64  # the LONGEST legal identity (the cap itself; the corpus holds only cap+1)


# --- KP-G1: the SKIP gate looks up a legal identity AT THE CAP (parameter-value monoculture breaker) --------------
async def test_KP_G1_a_legal_attribution_at_the_64_char_cap_is_looked_up_once() -> None:
    assert await contract._traffic_line_lookups(_MAX_LEGAL) == [_MAX_LEGAL]


# --- KP-G2 (= amendment-8 KB-1's r4a corpus entry, run here as its own pin): the dotted twin is never looked up ----
async def test_KP_G2_a_dotted_attribution_is_never_looked_up() -> None:
    assert await contract._traffic_line_lookups("fixer.b") == []


# --- KP-E1c: the DELETED r3 spelling pin, restored VERBATIM in body (from 39935f6) — the guard's PRESENCE reds -----
def test_KP_E1c_the_deleted_spelling_pin_restored() -> None:
    import _comms_fakes
    import lorerunes

    source = Path(_comms_fakes.__file__).read_text(encoding="utf-8")
    import_error_handlers = [
        handler.lineno
        for handler in ast.walk(ast.parse(source))
        if isinstance(handler, ast.ExceptHandler)
        and any(
            isinstance(name, ast.Name) and name.id == "ImportError"
            for name in ([handler.type] if not isinstance(handler.type, ast.Tuple) else handler.type.elts)
        )
    ]
    if getattr(lorerunes, "is_legal_identifier", None) is None:
        assert import_error_handlers
        return
    assert not import_error_handlers, import_error_handlers


# --- KP-FXg: the EFFECT pin with "predicate absent" simulated at EVERY module binding, not only the package attr ---
async def test_KP_FXg_predicate_unavailable_at_every_binding_never_silently_registers(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import lorerunes

    bindings = module_level_bindings_of(lorerunes.is_legal_identifier)
    homes = [name for name, _module, _attr in bindings if name.startswith("lorerunes")]
    assert homes, "anti-vacuity: the predicate's lorerunes home(s) were not found"
    for module_name, module, attribute in bindings:
        if module_name.startswith("lorerunes"):
            monkeypatch.delattr(module, attribute)
    fake = FakeAgentRegistry()
    try:
        await fake.register("fixer-b\n", session="wave7", role="builder")
    except Exception:  # noqa: BLE001 - any refusal is non-silent
        assert fake.db.agents == {}
        return
    pytest.fail("the fake REGISTERED a hostile name while the predicate was unavailable at every lorerunes binding")


# --- KP-RS1 / KP-FX2: a STAMPED row re-registered with a DIFFERENT consistent pair keeps its stamps (mint-once ∀
# callers), real AND fake, ABSOLUTE expectation (so two builds that both re-stamp cannot agree their way past it) ---
_FIRST = ("alice_pid", contract._PARITY_KEEP)
_SECOND = ("bob_pid", contract._PARITY_KEEP)  # a householded joiner: same session keep, different owner
_EXPECTED = ("re-registered", "alice_pid", True, keep_scope(contract._PARITY_KEEP))


async def test_KP_RS1_the_REAL_writer_never_re_stamps_a_stamped_row() -> None:
    harness = contract.TestTheFakeRegistryMirrorsTheWriter63cIA
    assert await harness._real_re_register_outcome(_FIRST, _SECOND) == _EXPECTED  # noqa: SLF001


async def test_KP_FX2_the_FAKE_never_re_stamps_a_stamped_row() -> None:
    harness = contract.TestTheFakeRegistryMirrorsTheWriter63cIA
    assert await harness._fake_re_register_outcome(_FIRST, _SECOND) == _EXPECTED  # noqa: SLF001


# --- KP-R5b (static): every relation statement ANY generator emits is BYTE-identical to the swept statement of the
# same edge — the MP-4 premise keyed on (edge, endpoints) cannot see an ENFORCED clause dropped by a re-definition -
def test_KP_R5b_no_generator_re_defines_a_swept_relation_differently() -> None:
    swept: dict[str, str] = {}
    for generator in ALL_DDL_GENERATORS.values():
        swept.update(relation_table_statements(generator()))
    assert swept
    divergent = {
        (name, edge): statement
        for name, generator in schema_ddl_generators().items()
        for edge, statement in relation_table_statements(emit_schema_ddl(generator)).items()
        if edge in swept and statement != swept[edge]
    }
    assert divergent == {}, divergent


# --- KP-R5b-live (the consequence, on the TEST store): production applies the lease slice AFTER the schema; does
# the `to` edge keep ENFORCED? ------------------------------------------------------------------------------------
async def test_KP_R5b_live_the_lease_slice_leaves_to_ENFORCED(migration_db: Any) -> None:  # noqa: F811
    connection, env = migration_db

    async def to_definition() -> str:
        info = await run(connection, "INFO FOR DB", {})
        row = info[0] if isinstance(info, list) else info
        return str(row["tables"][TO_RELATION])

    for ddl in (emit_schema_ddl(generate_agent_ddl), emit_schema_ddl(generate_message_ddl)):
        await apply_ddl(connection, ddl, url=env.url)
    before = await to_definition()
    assert "ENFORCED" in before, f"CONTROL: the probe cannot see ENFORCED even before the lease slice: {before}"
    await apply_ddl(connection, generate_lease_ddl(), url=env.url)
    after = await to_definition()
    assert "ENFORCED" in after, f"the lease slice (applied after the schema, as production does) dropped it: {after}"
```
```bash
#!/usr/bin/env bash
# Kill-pin pairs (P0 controls): for each build (REF = the reference itself), reset the lane to adv4-ref, apply the
# build (my_wbs4.py), copy the kill-pins in, run ONLY the kill-pin file (-n 4), print the tail + the red ids.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/ref
cd "$LANE" || exit 2
for WB in "$@"; do
  git checkout -q -f adv4-ref && git clean -fdq
  if [ "$WB" != REF ]; then uv run --no-project python "$INST/my_wbs4.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }; fi
  cp "$INST/test_adv_r4_killpins.py" loremaster/tests/
  uv run pytest -n 4 -q -p no:cacheprovider -rf loremaster/tests/test_adv_r4_killpins.py > "$INST/kp_${WB}.log" 2>&1
  echo "== $WB :: $(tail -1 "$INST/kp_${WB}.log")"
  awk '/^FAILED/ {print "   " $2}' "$INST/kp_${WB}.log"
done
git checkout -q -f adv4-ref && git clean -fdq
```

### A.5 `mem_reach.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4 P1c empirical REACH legs for the charset-text pin (run ALONE, on adv4-ref, after the lane).
# MEM0 = control (reference as built → GREEN); MEM1 = a NEW declared member `loreglyph` whose package carries a
# VERBATIM paste → the pin must RED naming loreglyph (reach DERIVED from pyproject, not a hand-list);
# MEM2 = the new member is declared but ships a src-layout package (`loreglyph/src/loreglyph`) → the coverage
# assertion must RED (declared-not-scanned). Runs the venv's pytest directly (`uv run` would try to sync a
# member that has no pyproject). ONE test id; no xdist.
set -uo pipefail
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/ref
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/inst
PIN="loremaster/tests/test_agent_registry.py::TestTheIdentifierCharsetTextHasOneSpelling63cIA::test_the_charset_text_occurs_ONLY_in_the_lorerunes_definition"
cd "$LANE" || exit 2
run() {  # $1 = label
  git status --porcelain | head -5
  .venv/bin/python -c "import loremaster,pathlib; assert pathlib.Path(loremaster.__file__).resolve().is_relative_to('$LANE')" || { echo "$1 PROVENANCE FAILED"; return; }
  .venv/bin/python -m pytest -q -p no:cacheprovider -p no:xdist "$PIN" > "$INST/mem_$1.log" 2>&1
  echo "== $1 :: $(tail -1 "$INST/mem_$1.log")"
  awk '/loreglyph|declared-not-scanned|PRIVATE copy/' "$INST/mem_$1.log" | head -4
}
reset() { git checkout -q -f adv4-ref && git clean -fdq; }
reset; run MEM0
reset
sed -i 's/members = \["lorerunes", "lorescribe", "loresigil", "loremaster"\]/members = ["lorerunes", "lorescribe", "loresigil", "loremaster", "loreglyph"]/' pyproject.toml
mkdir -p loreglyph/loreglyph && printf 'import re\n_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n' > loreglyph/loreglyph/__init__.py
run MEM1
reset
sed -i 's/members = \["lorerunes", "lorescribe", "loresigil", "loremaster"\]/members = ["lorerunes", "lorescribe", "loresigil", "loremaster", "loreglyph"]/' pyproject.toml
mkdir -p loreglyph/src/loreglyph && printf 'import re\n_NAME = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")\n' > loreglyph/src/loreglyph/__init__.py
run MEM2
reset
```

### A.6 `red_diff4.py`
```python
"""adversary-63c-i-a-r4 RED@HEAD diff: junit(r4 tests) vs junit(r3 tests), same unbuilt production.
Prints: r3-GREEN turned r4-RED, NEW red ids (absent from r3's collection), r3 ids gone, and each new red's message head."""
import sys
import xml.etree.ElementTree as ET


def outcomes(path):
    result = {}
    for case in ET.parse(path).iter("testcase"):
        key = f"{case.get('classname')}::{case.get('name')}"
        bad = case.find("failure") if case.find("failure") is not None else case.find("error")
        skipped = case.find("skipped") is not None
        result[key] = ("red", (bad.get("message") or "")[:230]) if bad is not None else (("skip", "") if skipped else ("green", ""))
    return result


r4, r3 = outcomes(sys.argv[1]), outcomes(sys.argv[2])
turned = [k for k in r4 if k in r3 and r3[k][0] == "green" and r4[k][0] == "red"]
new_red = [k for k in r4 if k not in r3 and r4[k][0] == "red"]
new_green = [k for k in r4 if k not in r3 and r4[k][0] == "green"]
gone = [k for k in r3 if k not in r4]
red_to_green = [k for k in r4 if k in r3 and r3[k][0] == "red" and r4[k][0] == "green"]
print(f"r4 ids={len(r4)} r3 ids={len(r3)}")
print(f"r3-GREEN turned r4-RED: {len(turned)}")
for k in turned: print("  TURNED", k)
print(f"NEW red ids: {len(new_red)}")
for k in new_red: print("  NEW-RED", k, "::", r4[k][1])
print(f"NEW green ids: {len(new_green)}")
print(f"r3 ids gone: {len(gone)}")
for k in gone: print("  GONE", k, r3[k][0])
print(f"red->green: {len(red_to_green)}")
```

### A.7 `run_full.sh`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4: full suite ALONE at -n 12 on the ref lane at a given state, with a memory watchdog.
# Usage: run_full.sh <label> [WB ...]   (no WB = the reference itself; several WBs = applied in order, combined)
# Refuses to start if another `pytest -n` runs on the box; kills ITS OWN pytest by PID if MemAvailable < 12 GiB.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bd8e690b-53f2-431b-8f5c-edcbd023690c/scratchpad/ref
LABEL=$1; shift
cd "$LANE" || exit 2
if ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/ && / -n /{f=1} END{exit !f}'; then echo "another pytest -n is running — not starting"; exit 3; fi
git checkout -q -f adv4-ref && git clean -fdq
for WB in "$@"; do uv run --no-project python "$INST/my_wbs4.py" "$LANE" "$WB" || { echo "$WB apply failed"; exit 2; }; done
echo "state: $(git status --porcelain | wc -l) dirty paths; available at launch: $(free -g | awk 'NR==2{print $7}') GiB; $(date '+%F %T')"
uv run python -c "import loremaster; print('loremaster.__file__ =', loremaster.__file__)"
uv run pytest -n 12 -q -p no:cacheprovider --junitxml="$INST/full_${LABEL}.xml" > "$INST/full_${LABEL}.log" 2>&1 &
PID=$!
low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 12 ]; then echo "WATCHDOG: MemAvailable ${avail} GiB < 12 — killing pytest PID $PID"; kill "$PID"; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc lowest MemAvailable during run: ${low} GiB; $(date '+%F %T')"
tail -1 "$INST/full_${LABEL}.log"
git checkout -q -f adv4-ref && git clean -fdq
```

### A.8 one-off commands (verbatim)
```bash
# declaration universe (lane ref @ adv4-ref, BEFORE any wrong-build run):
uv run pytest --collect-only -q -p no:cacheprovider $(cat files4.txt) | awk '/::/' > collected4.txt   # 2924 ids
# reference contract run: uv run pytest -n 8 -q -p no:cacheprovider --junitxml=ref_contract.xml $(cat files4.txt)
# lanes: run_lane4.sh X1 X2 X3 X3b X3c X3d X3e R5 FX1 G1 G2 FXg FXf RS1 FX2 R5b PX2 TWR ; run_lane4_ctl.sh TWP TWS TWQ SLUGDRIFT MP2DEF GS
# kill-pin pairs: kp_pairs4.sh REF G1 G2 FXg FXf RS1 FX2 R5b   (then REF R5b again after the live-probe fix)
# KEYDRIFT / CONVERGE: sed on lorerunes/lorerunes/identifiers.py's re.compile text, then .venv/bin/python -m pytest -q -p no:xdist <text-pin id>
# RED@HEAD (lane head): pytest -n 8 --junitxml=red_r4.xml $(cat files4.txt); git checkout 39935f6 -- loremaster/tests; same -> red_r3.xml; git checkout HEAD -- loremaster/tests; red_diff4.py red_r4.xml red_r3.xml
# currency: uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff   (lane head; lane ref @ adv4-ref)
# full suite: run_full.sh REF ; run_full.sh COMBO1 RS1 G1 FXg FX2 R5b PX2 ; run_full.sh COMBO2 G2 FXf TWR
# attribution: uv run pytest -q -p no:xdist loremaster/tests/test_floor_calibration_schema.py  on REF / R5 / R5b
# corpse sweep: git ls-files | while read f; do awk -v F="$f" '/HEAD_RED_import_guard|import_guard_is_deleted/ {print F":"FNR}' "$f"; done
# charset sweep (P1c construction): git ls-files 'loremaster/loremaster/*.py' 'lorerunes/*.py' 'lorescribe/*.py' 'loresigil/*.py' 'scripts/*.py' 'skills/*.py' | xargs awk 'index($0,"[a-z0-9][a-z0-9_") || /AGENT_NAME_PATTERN|_is_comms_charset_legal|_validate_comms_charset|_IDENTIFIER_CHARSET|SLUG_PATTERN/'
```

## VERDICT: CONTRACT INSUFFICIENT — with NEW-CLASS survivors; no LIVE-PRODUCTION-DEFECT

Class breakdown of the 8 full-suite survivors: **NEW-CLASS 5** — RS1 (MP-R4-1, the one I would gate: a takeover door on
a security-adjacent invariant, and amendment-8's KB-5 ruling rests on a false premise about it), FXg (MP-R4-4), FXf
(MP-R4-5, SAME-CLASS reading also written), FX2 (MP-R4-6, already ruled KB-5 → r4a), PX2 (MP-R4-7, prose). **SAME-CLASS
3** — G1 (MP-R4-3, closable by one fixture value), G2 (closed by amendment-8 KB-1's r4a entry — KP-G2 is that exact
value), TWR (the stated KB-2 bound). **LIVE-PRODUCTION-DEFECT 0** — the reference is satisfiable (full suite 11428/0,
= the author), and none of these doors is open at HEAD.

The pins the author can go write, each with the defect it catches and a kill-pin already proven GREEN on a correct build
and RED on its wrong one (§A.4): **KP-RS1** (a stamped row re-registered with a different consistent pair keeps its
stamps — REAL writer, absolute expectation) · **KP-FXg** (the MP-3 effect pin removes the predicate at every `lorerunes*`
binding) · **KP-E1c** (restore the presence pin beside the effect pin) · **KP-G1** (a legal identity at the 64-char cap
is looked up once) · KP-FX2 · the PX2 prose leg (§6). All five r3 survivors are killed, exactly, on their r4 pins.
