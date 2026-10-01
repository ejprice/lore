# REPORT-contract-63c-i-a-r4b-fix — contract r4b-fix addendum (amendment 13 §W items 1–5, as amended by 14 and 15)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done. All five §W items are pinned and mutation-proven. Two forks were raised and RULED (amendments 14 `e6441aa` and 15 `7f01787`). There is one commit on `feat/surreal-unification`.
- **deviations:** (1) `loremaster/tests/conftest.py` redirects hypothesis's cache home out of the tree. `database=None` measurably did NOT stop `.hypothesis/`; this is within the writable set and the brief's "or otherwise ensure" (§DEPENDENCY RIDER). (2) Committing: brief-base §2 says never commit, but the spawn brief orders ONE commit and wins by precedence. That is not a deviation, only stated.
- **Packages considered:** `hypothesis` 6.168.1 → **replace** (the hand-listed witness axis; `from_regex` over THE pattern object).
  - Group: `[dependency-groups] dev` (= pytest's), via `uv add --dev`; `uv.lock` +73.
  - In-image: `Containerfile` `RUN uv sync --locked --all-packages` installs `dev`. Measured: `uv export --no-dev` drops pytest AND hypothesis together.
  - Fallback not used.
  - The effect leg REUSES `patch_shared_object_everywhere`; the cache redirect REUSES `hypothesis.configuration.set_hypothesis_home_dir`.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 6 new symbols, all dispositioned (§DRY LEDGER).
- **Graded:** n/a (author, not grader). Base HEAD at report: `0242a19`; production byte-identical to `8b9eb6d`.
- **SAT:** both helper shapes, FULL SUITE ALONE `-n 12`, `11496 passed, 62 skipped, 3 xfailed` / 0 failed each (U 529.52 s, C 533.54 s). Both trees are lint-clean (no cleanup needed). The birth-15 remainder variant is GREEN on the touched files. An OWN SAT defect (the "§2.1" strip order) was caught by the SAT leg and fixed.
- **Kills:** 8 declared-vs-observed diffs, all EMPTY both ways: PXlie, PX2, PX2iso (birth leg not blinded), PXrem15 GREEN, RS1srvT, G4 (shrunk `'0__'`), FXt-on-U, FXt-on-C. **No survivors.**
- **RED@HEAD:** 0 turned red · 0 turned green · 13 new (2 red, right reason; 11 green) · 3 gone (= DUAL re-keys). **Currency** `--legs typecheck,ruff`: typecheck `RED_ADJUDICATED 23` · ruff GREEN. On the built world: 11/11 SELF-DESTRUCT → GREEN.
- **decisions-needed:** none blocking. 3 candidate doors are listed for the narrow delta's consideration (§CANDIDATE DOORS). The lead carries builder brief item 6 (amendment 13 F-1 (i)); my reference builds it as `--prose=shown`.
- **Receipt pointers:** §0 capability · §FORK F1-ADMIT · §FORK F5-REACH · §RULINGS · §DEPENDENCY RIDER · §DUAL · §ITEMS · §SAT · §RED · §GATE RECEIPTS · §DRY LEDGER · §CANDIDATE DOORS · §A instruments.

## 0. Capability check (brief-base §4) — measured 2026-09-25
- Idle-gate contract written without denial: `/tmp/claude-idle-gate-lore/7d832f61-e9e0-49da-a635-c43f7ed9206c-contract-63c-i-a-r4b-fix.contract` = `{"artifact": "REPORT-contract-63c-i-a-r4b-fix.md"}`. The session id comes from my scratchpad path.
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `contract`, cadence `≤20m`).
- grep/rg are hook-blocked (#473), so every textual sweep here uses awk. That is a fallback for non-symbol textual seams, stated here.
- Store reference `docs/reference/surrealdb-31-capabilities.md`: I read the §0 banner, the six READ-THIS facts and the section map. This work touches no DDL.
- `rm -rf` of the stray `.hypothesis/` was denied by the auto-mode classifier, so I MOVED it to my scratchpad instead (no retry by another deleting route).
- One `lore_search` took >120 s and was backgrounded by the harness; its result arrived and is used in §DRY LEDGER. Not filed as friction: the lore server was mid-load, as noted by other agents today, and it answered.
- Adversary instruments were copied from the adversary's scratch root after an md5 check: `my_ref_build_r4.py` `3e419c75…`, `my_ref_leg_r4a.py` `0058ae3c…`, `my_ref_leg_r4b.py` `7bf387f2…`, `my_wbs_r4b.py` `2de4368c…`. All four match the adversary's §A.

## FORK F1-ADMIT — item 2 (F-1): the ruling's literal leg contradicts the brief's required SAT variant (raised 2026-09-25, BEFORE any F-1 code) — RULED: amendment 14 (`e6441aa`), reading (B)
**The ruling (amendment 13 §F-1 "Pin"):** "after stripping the named ids and the full count, every integer literal left in the reason is an element of `{len(shown)}`."
**The brief (SAT receipt):** "Also build the remainder-prose variant at `_REFUSAL_ID_SAMPLE_SIZE = 15` (`…, 15 more`) — the F-2 case — and show it GREEN on the touched files."
**The contradiction:** under the literal leg, the remainder variant is RED in every population:
- `below-cap`: `(first 2 of 2 ids shown, 0 more)` leaves `0` after the strip, and `0 ∉ {2}`.
- `at-cap`: `0 more`, same.
- `perturbed-bound`: after F-2, `16 more` at birth 15, and `16 ∉ {3}`.

The r4b docstring (amendment-11 MP-A2) also names `"3 legacy rows"` as something a correct refusal may state. The literal leg REDs that too.

**Reading (A), literal:** admitted = `{len(shown)}`.
- This is unsatisfiable by the brief's required variant.
- It would be a new SAT defect of F-2's exact class: a count derived from the fixture that the pin never admits.

**Reading (B), recommended — admitted = the fixture's TRUE counts, derived per population:**
- The set is `{len(shown), count, count − len(shown), legacy_count, count + legacy_count}`. This is F-2's `fixture_counts`, extended with `len(shown)` per population as the ruling directs.
- The per-population guard ensures `birth ∉ admitted` wherever `birth ≠ len(shown)`, i.e. wherever N = the constant would be a lie. In `below-cap` that means moving `legacy_count` off `birth` and `birth − count`.
- Property pinned: **every integer the refusal serves is a TRUE count of the fixture's sets**. This is the CONSUMER-LAW form of "a served count describes the set it names".
- It kills PXlie in `below-cap` for any birth > 2 (the only births at which PXlie is a lie there).
- It admits the remainder and legacy prose, so the F-2 variant and the r4b-anticipated legacy statement stay SAT.
- What it gives up against (A): a lie that happens to equal a different TRUE fixture count other than birth, e.g. `(first 3 of 2 ids shown)` when legacy = 3. That is not a plausible build. The only plausible wrong N is the constant, and the guard keeps the constant out of the admitted set.

**Second, smaller reading, on scope:** the ruling says "all three populations" and the brief names `below-cap`, `at-cap` and `perturbed-bound`. I read this as "not only `perturbed-bound`", and I would ALSO run the leg in `above-cap`.
- In `above-cap`, `shown = bound = birth`, so the leg cannot false-RED a correct build.
- Excluding one population would be an unexplained guard (the QUANTIFIER LAW: ∀ inputs).
- If the lead or sidecar want exactly three populations, it is a one-line exclusion.

**What I am doing while waiting:** items 1, 3, 4 and 5 and the dependency rider are independent of this fork, and I am proceeding with them. Item 2 is being built to reading (B) in the working tree, so the delta is ready. It will be switched to (A) if ruled otherwise, before any mutation proof or SAT receipt depends on it.

## FORK F5-REACH — item 5 (FXt): the ruled structural clause kills FXt on the COLLAPSED shape only (raised 2026-09-25, measured) — RULED: amendment 15 (`7f01787`), option (b)
**The ruling (amendment 13 §KB-FXt):** "the predicate's `Name` may not occur inside any `ast.Try` (body or handlers) in `_comms_fakes.py` … Positive control: FXt". The brief says "Must kill FXt" and requires mutation proof.
**The measurement:** instrument `fxt_probe.py` is pasted in §A. It scans the adversary's two reference fakes (`fakes_U.py` / `fakes_C.py`, copied from the adversary-r4b scratch root) with clause (iv) implemented as ruled:
```
honest U: 0 violation(s)
FXt-on-U: 0 violation(s) []
honest C: 0 violation(s)
FXt-on-C: 1 violation(s) ['line 289: `is_legal_identifier` occurs INSIDE a `try` (line 288) — …']
```
**Why:** adversary-r4b's FXt was built on reference U, the UNCOLLAPSED helper that amendment 12 lets the builder keep:
- On U, the `try` wraps `identifier_decision(value)`, a LOCAL ALIAS bound from `FakeAgentRegistry._shared_identifier_predicate()`.
- The predicate's `Name` occurs only in the helper's `return is_legal_identifier`, which sits outside any `try`.
- So the ruled clause cannot see the survivor it was ruled to close.

A clause that followed the alias would be a binding tracker. That is the packet-01 v2 design, which regressed. It is a design problem, not a builder or contract edit.

**Options:**
- **(a) As ruled, plus a pinned KNOWN BOUND** for FXt on the uncollapsed shape. This keeps KB-FXt half-open. The bound would be a control asserting the scanner stays quiet on FXt-on-U, going RED the day it is closed. Its RE-OPEN TRIGGER would be the adversary's existing one.
- **(b) RECOMMENDED — an EFFECT leg, alias-blind and receiver-blind.** `patch_shared_object_everywhere` replaces THE shared predicate with a stub that RAISES a sentinel exception. A fake `register` of a LEGAL identity must then propagate the sentinel: no `except` may swallow the shared decision.
  - It kills FXt on BOTH shapes.
  - It also kills every FXt variant that names nothing, because it observes the effect, not the spelling.
  - Both honest shapes stay green, since the exception propagates.
  - At HEAD (predicate absent) it takes the same early-return control as the effect pin above it.
  - It is one test function, using the r3/r4 sharing pins' existing seam `patch_shared_object_everywhere` (reused, not hand-rolled).
  - This is an instrument beyond the ruled clause, so it needs a ruling.
- **(c) Force the collapse** (R-3b). Amendment 12 already rejected it as a scope change. Not recommended.

**What I am doing while waiting:** clause (iv) is implemented EXACTLY as ruled, with its controls, because it is correct and kills FXt-on-C. Its mutation proof will be taken on the collapsed shape. The uncollapsed-shape survival is measured above. I am NOT adding (a)'s bound control or (b)'s effect leg until ruled.

## RULINGS RECEIVED (both forks closed before any proof depended on them)
- **F1-ADMIT → amendment 14 (`e6441aa`)**, directive #16016 (acked): reading (B), with above-cap IN. The bound "a lie equal to a DIFFERENT true count" is stated in the `R_Q5_1` docstring with its re-open trigger. Item 2 is built to it.
- **F5-REACH → amendment 15 (`7f01787`)**, directive #16018 (acked): option (b).
  - The EFFECT leg is the ∀.
  - Clause (iv) and the allowlist stay as static twins, with "static reach — the effect leg is the ∀" docstrings.
  - The amendment-11 obfuscation KNOWN BOUND is CLOSED. Its control is re-labelled, and its KNOWN-BOUND message is removed (DUAL).

## DEPENDENCY RIDER (amendment 13 §G4 + §E) — receipts, measured 2026-09-25
| leg | receipt |
|---|---|
| group | `[dependency-groups] dev` in `pyproject.toml`, the SAME list that holds `pytest`, `pytest-asyncio` and `pytest-xdist`. Added via `uv add --dev hypothesis`, which appended `"hypothesis>=6.168.1",` (+1 line). |
| resolved | `hypothesis==6.168.1` plus its one dependency `sortedcontainers==2.4.0` |
| lock diff | `uv.lock` +73 / −0 (two `[[package]]` blocks + the dev-group entry). `uv sync --locked --all-packages --dry-run` gives "Would make no changes", so the lock is current. |
| in-image proof | `Containerfile`: `RUN uv sync --locked --all-packages`, with no `--no-dev` and no `--only-group`. uv's default groups include `dev`. MEASURED: `uv export --locked --all-packages` lists `hypothesis==6.168.1` and `sortedcontainers==2.4.0`, while `uv export --locked --all-packages --no-dev` lists NEITHER them NOR `pytest`. They are one group, installed together or not at all. The in-image conformance runner (`skills/lore-deploy/scripts/conformance_run.sh`) then runs the BAKED `$PY -m pytest … -n auto` against the `:ro` mount. **`hypothesis` WILL be present in-image.** No fork. |
| scratch copy | `./scripts/scratch_copy.sh <scratch>/ref` gave rc=0 with provenance asserted (every member resolves inside the copy). In the copy: `import hypothesis` gives `6.168.1` from `<scratch>/ref/.venv/lib/python3.14/site-packages/hypothesis/__init__.py`. `loremaster.__file__ = <scratch>/ref/loremaster/loremaster/__init__.py`. |
| fallback | NOT used. There was no measured conflict: venv resolution clean, lock current. |
| `.hypothesis/` | ⚠ `database=None` is NOT sufficient. Measured on the first HEAD run: hypothesis 6.168.1 wrote `<repo>/.hypothesis/{unicode_data,constants}` (caches, not the example database) with its own `.gitignore` (`*`), so `git status` stayed clean.<br>From the installed source: `configuration.py` has `__hypothesis_home_directory_default = Path.cwd() / ".hypothesis"`, and the cache writes in `internal/charmap.py` / `internal/constants_ast.py` are wrapped in `except Exception: pass`. So a `:ro` mount in-image silently skips them and cannot fail the conformance run.<br>**Fix (tree hygiene, stated):** `loremaster/tests/conftest.py` calls the package's own `hypothesis.configuration.set_hypothesis_home_dir(<tempdir>/lore-hypothesis-<uid>)`. Re-measured: no `.hypothesis` in the repo or the lane after runs, and the caches land in `/var/tmp/lore-hypothesis-1000/{constants,unicode_data}`.<br>`.gitignore` NOT edited. The stray directory from the first run was moved (not deleted, since `rm -rf` was classifier-denied) to `<scratch>/hypothesis-stray-from-first-run`. ⚠ The conftest edit is a file outside the brief's item list but inside the writable set (`loremaster/tests/**`). The brief's "or otherwise ensure no `.hypothesis/` directory is written" authorises it; flagged here for visibility. |

## DUAL — every pin deleted, inverted or re-keyed (each carries an in-place DUAL comment or explaining comment)
Each row is a site, what changed, the old virtue, and its adjudication.

**1. `test_agent_governance_63c_i_a.py::…::test_R_Q5_1_…` — residue computation (RE-KEYED)**
- Change: extracted to `_integers_stated_beside_the_seeded_identifiers`, now run in EVERY population (it was `perturbed-bound` only). Strip ORDER swapped: section citations now go before the full count.
- Old virtue: the seeded-identifier strip, the full-count strip and the section strip all preserved.
- Adjudication: preserved-with-pin (amendment 14). The order swap fixes a SAT defect my extension exposed: at count 2, `\b2\b` split "§2.1" and left a phantom "1". It was measured RED on BOTH reference shapes (§SAT) before the fix, and the swap is commented in place.

**2. same test — D5 message and docstring (RE-KEYED prose)**
- Change: `first {sample_size} of {count}` → `first {shown} of {count}`.
- Old virtue: none lost; it taught N = the constant.
- Adjudication: DUAL comment in place (amendment 13 §F-1 (i)).

**3. same test — F-2 guard (WIDENED)**
- Change: `while` avoid-set `+ birth_bound + id_bound`; `fixture_counts` `+ trap_count − id_bound`.
- Old virtue: kept, since the guard is strictly wider.
- Adjudication: amendment 13 §W-1, verbatim from the adversary's `fix_F2_test.py`.

**4. same test — birth-value leg (KEPT, now second)**
- Change: the new F-1 ∀ leg runs before it in every population.
- Old virtue: its PX2 kill. Leg-isolated proof in §ITEMS: PX2iso.
- Adjudication: preserved-with-pin.

**5. `…::test_a_householded_joiners_re_register_…_untouched` (node ids RE-KEYED)**
- Change: parametrised `[required-only]` / `[every-optional]`. `required-only` is byte-for-byte the r4b call. Control 2 passes the same extras.
- Old virtue: all preserved, and `required-only` = the old test.
- Adjudication: additive (comment in place); the node id gains a param suffix.

**6. `test_agent_registry.py::test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named` → `test_the_STATIC_allowlist_cannot_see_an_OBFUSCATED_predicate_name_the_effect_leg_does` (RE-KEYED)**
- Change: renamed; the KNOWN-BOUND message and re-open trigger were removed.
- Old virtue: it documented the obfuscation door.
- Adjudication: DUAL comment in place (amendment 15). The bound is CLOSED by the effect leg; the control's assertion (the scanner stays quiet) is unchanged.

**7. `_fake_predicate_import_violations` docstring + shape-pin docstring (RE-KEYED prose)**
- Change: the KNOWN-BOUND obfuscation sentence is replaced with "STATIC REACH — THE EFFECT LEG IS THE ∀". The FXs star-import line is added. "Two pins" becomes "Three pins".
- Old virtue: none lost.
- Adjudication: amendments 13 (residual 3) and 15.

**8. `test_comms_schema.py::_LEGAL_IDENTIFIER_WITNESSES` comment (RE-KEYED)**
- Change: the KNOWN BOUND and "a FOURTH witness axis → derive" trigger are replaced by "hand-list = NAMED controls; the generated leg is the ∀".
- Old virtue: the tuple is unchanged (all 8 witnesses kept).
- Adjudication: amendment 13 §G4 ("drops the trigger sentence").

**9. `scripts/pending_contracts.yaml` — `packet-63c-i-a-contract-r2` / `test_agent_registry.py` `attr-defined` (RE-PINNED count)**
- Change: count 4 → 7, with the reason naming the 3 new direct reads of the not-yet-moved `lorerunes.AGENT_NAME_PATTERN` / `is_legal_identifier`.
- Adjudication: the allowance is a PIN (currency said so). It still self-destructs with the build (§SAT currency legs).

No test function was deleted and no param removed.

## ITEMS — pin · wrong build killed · mutation receipt (declare-then-diff)
**Method.**
- Lane `<scratch>/ref` was built with `scratch_copy.sh` (rc=0; `loremaster.__file__ = <scratch>/ref/loremaster/loremaster/__init__.py`, asserted inside every run by `run_lane.sh`).
- `fixbase` `fd1f0c8` is main's 7 files byte-identical (`cmp`).
- `refU` `7f9b9a2` / `refC` `e1cfeaa` = `fixbase` + adversary-r4 `my_ref_build_r4.py` + adversary-r4a `my_ref_leg_r4a.py` + adversary-r4b `my_ref_leg_r4b.py --prose=shown [--collapse]`. All three were run VERBATIM (md5 `3e419c75…` / `0058ae3c…` / `7bf387f2…`, checked against the adversary's §A).
- `--prose=shown` is builder item 6 as amendment 13 F-1 (i) now reads it: N = the ids actually named, `min(_REFUSAL_ID_SAMPLE_SIZE, count)`.
- Declared expected-RED sets were fixed in `my_wbs_fix.py` §A from `--collect-only` over the 3 touched test files on `refU` (`collected_fix.txt`, **637 ids**), BEFORE any wrong-build run. They were re-collected after the lane re-sync: IDENTICAL.
- Observed reds (junit) were diffed against declared BOTH ways (`batch_fix.sh` §A). Scope: the 3 touched test files, `-n 8`, 2026-09-25 14:5x–15:0x EDT.
- Wrong-build bodies PX2 / PXlie / PXrem15 / RS1srvT / FXt / G4 are adversary-r4b's `my_wbs_r4b.py` (md5 `2de4368c…`), REUSED by subprocess. PX2iso and FXtC are mine.

**Results (all declared-vs-observed diffs EMPTY both ways):**

**Item 1 — F-2**
- Pin: `test_R_Q5_1_…[perturbed-bound]` guard.
- **PXrem15**, a CORRECT build (birth 15, derived remainder prose): declared GREEN; `637 passed` → **now GREEN** (it was a false RED at r4b).
- **PX2**: declared `[below-cap]` + `[perturbed-bound]`; `2 failed, 635 passed` → **KILLED**.
- **PX2iso** (PX2 with the F-1 leg disabled in scratch — LEG ISOLATION): declared `[perturbed-bound]`; `1 failed, 636 passed`. The message is the BIRTH leg's own ("restates the BIRTH sample size 10 while the slice follows the PATCHED constant 3"), so **the F-2 guard did not blind the birth leg**.

**Item 2 — F-1 (amendment 14 (B))**
- Pin: `test_R_Q5_1_…` — the ∀-population true-count leg.
- **PXlie** `(first 10 of 2 ids shown)`: declared `[below-cap]`; `1 failed, 636 passed` → **KILLED** (a survivor of the r4b full suite).

**Item 3 — G4**
- Pins: `TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language`, plus the hostile companion `…never_looks_up_GENERATED_text_the_SHARED_predicate_rejects`.
- **G4** (`or "--" in attribution or "__" in attribution`): declared `[GENERATED_identity_language]`; `1 failed, 636 passed` → **KILLED**. Hypothesis's shrunk falsifying example: `attribution='0__'`.

**Item 4 — RS1srvT**
- Pin: `test_a_householded_joiners_re_register_…_untouched[every-optional]`.
- **RS1srvT** (takeover `and task_id is not None`): declared `[every-optional]`; `1 failed, 636 passed` → **KILLED**. `[required-only]` stayed green, as declared, which proves the new param is what sees it.

**Item 5 — FXt (amendment 15)**
- Pin: `test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists[name|session]`.
- **FXt on U** (the adversary's build: `try` around the ALIAS): declared `[name]` + `[session]`; `2 failed, 635 passed` → **KILLED**. Clause (iv) is blind here, as measured in §FORK F5-REACH.
- **FXtC on C** (`try` around the direct call): declared `[name]` + `[session]` + shape pin; `3 failed, 634 passed` → **KILLED**. Here the static twin (clause iv) ALSO fires.

**Survivors:** none. Every wrong build in scope is killed, so no survivor claim needs a full-suite leg. The full suites below are SAT legs.

**Scanner-level controls** (pytest, main, HEAD):
- clause (iv) positives: FXt direct-call, predicate-only-in-handler, `except*`.
- negatives: both honest shapes beside an unrelated `try`, plus R-A (ii)'s submodule import beside an unrelated `try` (the pre-existing `submodule-top-import-and-an-unrelated-try` param).
- Result: 49 passed (§RED).

**Wall-clock of the new legs** (junit, touched-scope run, `-n 8`, per shape):
| leg | U | C |
|---|---|---|
| the 2 hypothesis legs (200 examples each; pure, in-memory spy, no store) | 0.589 s | 0.589 s |
| effect leg ×2 | 0.022 s | 0.025 s |
| clause-(iv) controls | ≈0.01 s | ≈0.01 s |
| `[every-optional]` (one more store-backed world) | 3.778 s | 3.518 s |

## SAT — satisfiability receipt (measured 2026-09-25, lane `<scratch>/ref`, pytest ALONE)
Launch gate on every run: ≥23 GiB available for `-n 12` (≥20 GiB for `-n 8`), and no other python/pytest/uv pytest in the process table (PID/argv scan; the pattern is bracketed so it cannot match itself). A PID watchdog kills below 12 GiB; **it never fired.**

**Full suite, `-n 12`, ALONE:**
| reference | tree | tail (verbatim) | RED | window · memory |
|---|---|---|---|---|
| **U** — uncollapsed (`return is_legal_identifier`) | `refU` `7f9b9a2` | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 529.52s (0:08:49)` exit 0 | 0 | 15:02:47–15:11:42 EDT · 37 GiB at launch, lowest 30 |
| **C** — collapsed (direct call) | `refC` `e1cfeaa` | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 533.54s (0:08:53)` exit 0 | 0 | 15:11:42–15:20:43 EDT · 36 GiB at launch, lowest 28 |

- 11496 = r4b's 11486 (adversary-r4b §1) + exactly the 10 ids this addendum adds (RED receipt: 13 new − 3 re-keyed).
- **Lint cleanups:** on both built trees, run BEFORE the full suites, `uv run ruff check .` gives `All checks passed!` and `./scripts/typecheck.sh` gives OK on every leg (lorerunes, lorescribe, loresigil, loremaster, skills, docs/eval, scripts, shellcheck).
  - The reference legs already carry their own lint cleanup (adversary-r4 `my_ref_build_r4.py`).
  - **No further cleanup was needed**, so "before" and "after lint cleanups" are the SAME tree. One full-suite run per shape covers both.
- **Final trees** `refU` `32ae680` / `refC` `6939322` (= main's final 7 files, `cmp`-identical):
  - They differ from the full-suited trees by ONE line: `_FXT_PRIVATE_FALLBACK` now reuses `_PRIVATE_RULE` (`git diff 7f9b9a2 32ae680`, 1+/1−, a fixture string in `test_agent_registry.py`).
  - Touched-scope re-run, `-n 8`: U `637 passed in 59.37s`, C `637 passed in 57.81s`, RED 0 each.
- **Birth-15 remainder variant** (`_REFUSAL_ID_SAMPLE_SIZE = 15`, prose `(first {shown} of {M} ids shown, {M − shown} more)`, adversary-r4b PXrem15 body): touched files `637 passed in 59.43s`, **GREEN** (it was a false RED at r4b).
- **Own SAT defect, caught by this SAT leg and fixed before any proof depended on it.** My first reference run was `1 failed, 636 passed` on `R_Q5_1[below-cap]`, on BOTH shapes. The cause was the F-1 leg's residue strip order: `\b2\b` split "§2.1" and left a phantom "1". Fixed by stripping sections first (DUAL row 1). All proofs above are on the fixed tree; the first batch was killed by PID.
- **Currency on the built world** (lane `refU`, `--legs typecheck,ruff`):
  - with my yaml KEPT: `RED_ORPHANED — 11 residual(s)`, ALL `SELF-DESTRUCT` (10 files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"), 0 real errors. `test_agent_registry.py`'s 7-count allowance discharges.
  - with `bounds: []` (builder edit 2): typecheck **GREEN**, ruff **GREEN**.
  - This equals adversary-r4b §6's shape. The entries are honest, owned by `63c-i-a`, with a real trigger; nothing is carried as a bound.

## RED receipt — MAIN checkout @ `0242a19` + my edits, the 3 touched test files, `-n 8`
`157 failed, 477 passed, 3 errors in 59.10s` (160 reds). I diffed it (`red_diff_fix.py` §A) against adversary-r4b's `red_r4b.xml`: r4b tests on production @`8900094`, with production/tests/scripts diff EMPTY from `8b9eb6d` to `0242a19`, restricted to the same 3 files.
- r4b 627 ids / 158 reds → fix 637 ids / 160 reds.
- **TURNED RED 0 · TURNED GREEN 0 · NEW 13 = 2 red + 11 green · GONE 3.**
- The 2 new reds, both for the RIGHT reason (unbuilt world):
  - `…GENERATED_identity_language`: `AttributeError: module 'lorerunes' has no attribute 'AGENT_NAME_PATTERN'`
  - `…GENERATED_text_the_SHARED_predicate_rejects`: `AttributeError: … 'is_legal_identifier'`, "while generating 'value'"
- The 11 new greens:
  - the tool-seam pin's two params (**GREEN at HEAD**, as amendment 11 requires of row 2)
  - the effect leg ×2 (HEAD early-return control)
  - clause-(iv) positives ×3 and negatives ×2
  - the re-labelled static-reach control ×2
- GONE 3 = re-keyed ids, not deletions: the tool-seam pin's un-suffixed id (now `[required-only]`) and `test_KNOWN_BOUND_an_OBFUSCATED_…[concatenated-name|joined-name]` (renamed). See DUAL rows 5 and 6.
- **0 r4b-greens turned red**, as the brief expected. No red is RED for the wrong reason.

## GATE RECEIPTS — main checkout, final tree
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → lorerunes / lorescribe / loresigil / skills / docs/eval / scripts OK; shellcheck OK (7 tracked .sh); **loremaster FAILED: `Found 23 errors in 10 files`**. These are the RED contract's adjudicated residuals: 20 at r4b + my 3 direct reads (DUAL row 9).
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED — 23 residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3`
  - `ruff GREEN`
  - `pytest NOT_RUN` (by design under `--legs`, per the brief; a bare `--currency` was never run)
- The r4b-fix contract is RED at HEAD by design (it is a RED contract for the i-a build). Its SAT is §SAT.

## DRY LEDGER (brief-base §6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_integers_stated_beside_the_seeded_identifiers` (staticmethod, `TestAgentMigrateScopeKeyed63cIA`) | none needed — the body is r4b's in-test residue code, moved | — | **EXTENDED** r4b's inline residue computation (moved verbatim into a helper for PLR0912/0915; strip order fixed) |
| `_the_identity_language`, `_text_the_shared_predicate_rejects` (strategy builders) | none needed — `hypothesis` enters the tree in this commit | no prior strategy exists (`hypothesis` was absent from the venv, probed) | **REUSED** the package: `hypothesis.strategies.from_regex` / `text().filter` |
| `_SharedDecisionReached` (sentinel exception) | `lore_search("sentinel exception class raised by a test stub to prove a shared function was called")` | only `test_watcher.py`'s private no-op store sentinels, which raise `AssertionError` (indistinguishable from an assertion failure) | **HAND-ROLLED** (one line; needs a dedicated type the leg can `except`) |
| `_FXT_PRIVATE_FALLBACK` (fixture string) | read the file's constants | `_PRIVATE_RULE` already holds the regex | **REUSED** `_PRIVATE_RULE` (`f"({_PRIVATE_RULE})(value)"`) |
| `_HYPOTHESIS_HOME` (conftest) | read the installed `hypothesis/configuration.py` | `set_hypothesis_home_dir` / `HYPOTHESIS_STORAGE_DIRECTORY` | **REUSED** `hypothesis.configuration.set_hypothesis_home_dir` |
| effect-leg patching | — | `_governed_contract.patch_shared_object_everywhere` | **REUSED** (default `expect_in=("lorerunes",)`) |

## CANDIDATE DOORS — noticed, NOT pinned (scope closed; each needs a ruling)
1. **The hostile companion's sample space is far from legal.** `st.text()` rarely draws a NEAR-MISS identity (uppercase twin, dotted `a.b`, a single illegal char inside a legal body). A gate that WIDENS by one character class is caught by the hand-listed `_HOSTILE_IDENTIFIERS`, which carries those shapes, not by the generated leg. The ruling specifies `st.text()`, and I built exactly that. A near-miss generator (legal language × one mutated position) would make the hostile side a ∀ too. Candidate for the narrow delta.
2. **The hypothesis cache home is shared per user** (`/var/tmp/lore-hypothesis-<uid>`) across concurrent sessions. charmap writes are atomic (`mkstemp` + `os.renames`). The constants cache uses `write_text` keyed on the source hash, so a concurrent writer writes identical content. I judge this low risk; stated, not measured under contention.
3. **Failure-message ordering in `perturbed-bound`:** the F-1 leg now runs before the birth-value leg, so a PX2-shaped build reports the F-1 message (which teaches `min(bound, count)`), not the birth message. PX2iso proves the birth leg is live; a reader of a red sees the F-1 text first. Not a defect; stated for whoever reads a red.

## Unrelated failures
None observed: both full suites were 0 failed. **There are 0 failing tests unrelated to our present scope.**

## A. Instruments (pasted VERBATIM — md5 at report time; scratch root `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7d832f61-e9e0-49da-a635-c43f7ed9206c/scratchpad`)
Reused verbatim, not re-pasted: adversary-r4 `my_ref_build_r4.py` (md5 `3e419c75…`, REPORT-adversary-63c-i-a-r4.md §A.1 @ `86379a4`), adversary-r4a `my_ref_leg_r4a.py` (`0058ae3c…`, REPORT-adversary-63c-i-a-r4a.md §A.2 @ `94c31f8`), adversary-r4b `my_ref_leg_r4b.py` (`7bf387f2…`) and `my_wbs_r4b.py` (`2de4368c…`), both in REPORT-adversary-63c-i-a-r4b.md §A.1/§A.2 @ `60899bf`. The edit scripts that WROTE the contract (`apply_item2.py`, `apply_item3.py`, `apply_item5.py`, `apply_item5b.py`, `apply_lint.py`, `rewrap5b.py`) are not measurement instruments; their output IS the commit.

### A.1 `fxt_probe.py` — md5 `facb3128a2b2e1ccd7728d26bc31a72c`
```python
"""contract-63c-i-a-r4b-fix: does scanner clause (iv) see adversary-r4b's FXt on BOTH honest helper shapes?
Usage: .venv/bin/python fxt_probe.py <repo-root> <fakes_U.py> <fakes_C.py>"""
import ast, sys
from pathlib import Path
sys.path[:0] = [str(Path(sys.argv[1]) / "loremaster/tests")]
import test_agent_registry as reg  # noqa: E402
scan = reg._fake_predicate_import_violations
FXT_U = ("                if not identifier_decision(value):\n",
         "                try:\n                    legal = identifier_decision(value)\n"
         "                except Exception:  # noqa: BLE001\n                    import re  # noqa: PLC0415\n\n"
         "                    legal = re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"
         "                if not legal:\n")
FXT_C = ("            if not is_legal_identifier(value):\n",
         "            try:\n                legal = is_legal_identifier(value)\n"
         "            except Exception:  # noqa: BLE001\n                import re  # noqa: PLC0415\n\n"
         "                legal = re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"
         "            if not legal:\n")
for label, fname, (old, new) in (("U", sys.argv[2], FXT_U), ("C", sys.argv[3], FXT_C)):
    src = Path(fname).read_text()
    print(f"honest {label}: {len(scan(ast.parse(src)))} violation(s)")
    assert src.count(old) == 1, (label, src.count(old))
    mutated = src.replace(old, new)
    v = scan(ast.parse(mutated))
    print(f"FXt-on-{label}: {len(v)} violation(s) {v[:1]}")
```

### A.2 `my_wbs_fix.py` — md5 `531c4b1b584d401367c4a497c7bc8911`
```python
"""contract-63c-i-a-r4b-fix — wrong builds (and CORRECT-build SAT probes) against the r4b-fix contract, ON TOP of
reference U (lane branch refU) or C (refC). Adversary-r4b's bodies (my_wbs_r4b.py, md5 2de4368c…, §A.2 of
REPORT-adversary-63c-i-a-r4b.md) are REUSED by subprocess for PX2 / PXlie / PXrem15 / RS1srvT / FXt / G4; the
builds below are mine.

Usage: .venv/bin/python my_wbs_fix.py <scratch-root> <WB-id> [--declared]
  --declared  print the DECLARED expected-RED node ids, resolved against collected_fix.txt (collect-only over
              touched.txt on refU, taken BEFORE any wrong-build run) and exit.
A DECLARED set of [] predicts the build SURVIVES (or, for a CORRECT build, stays GREEN). Each edit asserts its
anchor occurs exactly once (#194).
"""

import subprocess
import sys
from pathlib import Path

INST = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
TOOL_PIN = "test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched"
GEN_LEGAL = "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language"
EFFECT_LEG = "test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists"
SHAPE = "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # F-1: prose N = the CONSTANT -> '(first 10 of 2 ids shown)' below the cap; true everywhere else.
    "PXlie": [(GOV, [RQ51, "[below-cap]"])],
    # F-2 re-proof: PX2 '(first 10 ids shown)' — the F-1 leg reds below-cap (10 ∉ {2,0,3,5}) and perturbed-bound.
    "PX2": [(GOV, [RQ51, "[below-cap]"]), (GOV, [RQ51, "[perturbed-bound]"])],
    # PX2 with the F-1 leg DISABLED in the test (leg isolation): the BIRTH-VALUE leg alone must still red
    # perturbed-bound — the F-2 guard did not blind it.
    "PX2iso": [(GOV, [RQ51, "[perturbed-bound]"])],
    # a CORRECT build: birth 15 + derived remainder prose '(first 3 of 19 ids shown, 16 more)' — must stay GREEN.
    "PXrem15": [],
    # RS1srvT: tool takeover conditioned on task_id -> only the every-optional param sees it.
    "RS1srvT": [(GOV, [TOOL_PIN, "[every-optional]"])],
    # G4: SKIP gate narrows on doubled separators -> the GENERATED legal leg (hand-list carries no '--'/'__').
    "G4": [(REG, [GEN_LEGAL])],
    # FXt on U (adversary's anchor, try around the ALIAS): the effect leg on both fields; clause (iv) blind.
    "FXt": [(REG, [EFFECT_LEG, "[name]"]), (REG, [EFFECT_LEG, "[session]"])],
    # FXt on C (try around the direct call): the effect leg on both fields AND clause (iv) (the shape pin).
    "FXtC": [(REG, [EFFECT_LEG, "[name]"]), (REG, [EFFECT_LEG, "[session]"]), (REG, [SHAPE])],
}


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


if "--declared" in sys.argv:
    collected = (INST / "collected_fix.txt").read_text().splitlines()
    for file_fragment, node_fragments in DECLARED[WB]:
        hits = [n for n in collected if file_fragment in n and all(f in n for f in node_fragments)]
        assert hits, f"declared rule ({file_fragment}, {node_fragments}) matched NO collected node"
        for node in hits:
            print(node)
    raise SystemExit(0)

ADVERSARY = INST / "my_wbs_r4b.py"
if WB in ("PXlie", "PX2", "PXrem15", "RS1srvT", "FXt", "G4"):
    subprocess.run([sys.executable, str(ADVERSARY), str(ROOT), WB], check=True)
elif WB == "PX2iso":
    subprocess.run([sys.executable, str(ADVERSARY), str(ROOT), "PX2"], check=True)
    edit("loremaster/tests/" + GOV,
         "        untrue_counts = sorted(set(stated_integers) - admitted_counts)\n",
         "        untrue_counts: list[int] = []  # LEG ISOLATION (scratch only): the F-1 leg disabled\n")
elif WB == "FXtC":
    edit("loremaster/tests/_comms_fakes.py",
         "            if not is_legal_identifier(value):\n",
         "            try:\n"
         "                legal = is_legal_identifier(value)\n"
         "            except Exception:  # noqa: BLE001 - 'robust': a predicate hiccup never crashes a fake\n"
         "                import re  # noqa: PLC0415\n\n"
         "                legal = re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"
         "            if not legal:\n")
else:
    raise SystemExit(f"unknown WB {WB}")
print(f"{WB} applied")
```

### A.3 `run_lane.sh` — md5 `b07e1885fc070a64e2f84821f8e88403`
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4b-fix: pytest ALONE on the scratch lane at <branch> (+ optional WBs from my_wbs_fix.py, in order).
# Adapted from adversary-r4b run_full_r4b.sh (§A.4). Launch gate: MemAvailable >= $MINMEM GiB (default 23 for -n 12;
# pass MINMEM=20 for -n 8) AND no other python/pytest/uv pytest process (a PID/argv scan that cannot match itself:
# the awk pattern is bracketed); polls up to 30 min, else exits 4 ("blocked"). Watchdog kills OUR pytest by PID when
# MemAvailable < 12 GiB, writes WATCHDOG_FIRED, and the caller STOPS.
# Usage: run_lane.sh <label> <branch> <nproc> <scope: full | touched> [WB ...]
set -uo pipefail
MY=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7d832f61-e9e0-49da-a635-c43f7ed9206c/scratchpad
INST=$MY/inst
LANE=$MY/ref
LABEL=$1; BRANCH=$2; NPROC=$3; SCOPE=$4; shift 4
MINMEM=${MINMEM:-23}
cd "$LANE" || exit 2
git checkout -q -f "$BRANCH" && git clean -fdq
for WB in "$@"; do .venv/bin/python "$INST/my_wbs_fix.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }; done
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
if [ "$SCOPE" = full ]; then TARGETS=(); else mapfile -t TARGETS < "$INST/touched.txt"; fi
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /[p]ytest/{n++} END{print n+0}')
  [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
  sleep 20
done
echo "branch=$BRANCH WBs=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | wc -l); avail at launch ${avail} GiB; $(date '+%F %T')"
.venv/bin/python -m pytest -n "$NPROC" -q -p no:cacheprovider --junitxml="$INST/run_${LABEL}.xml" "${TARGETS[@]}" > "$INST/run_${LABEL}.log" 2>&1 &
PID=$!; low=999
while kill -0 "$PID" 2>/dev/null; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo); [ "$avail" -lt "$low" ] && low=$avail
  if [ "$avail" -lt 12 ]; then echo "WATCHDOG FIRED: ${avail} GiB — killing pytest PID $PID"; kill "$PID"; echo WATCHDOG > "$INST/WATCHDOG_FIRED"; fi
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
echo "tree .hypothesis present: $([ -e "$LANE/.hypothesis" ] && echo YES || echo no)"
git checkout -q -f "$BRANCH" && git clean -fdq
```

### A.4 `batch_fix.sh` — md5 `b332e3d0ddba48baaaafa4cf55c123a5`
```bash
#!/usr/bin/env bash
# contract-63c-i-a-r4b-fix batch: (1) touched-scope SAT on refU/refC; (2) every WB on its lane, observed vs DECLARED
# (declared from collected_fix.txt BEFORE any run) diffed BOTH ways; (3) lint gates on refU/refC; (4) full-suite SAT
# ALONE at -n 12 on refU and refC. Stops on a WATCHDOG_FIRED or BLOCKED run.
set -uo pipefail
MY=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7d832f61-e9e0-49da-a635-c43f7ed9206c/scratchpad
INST=$MY/inst; LANE=$MY/ref
stop_if_bad() { [ -e "$INST/WATCHDOG_FIRED" ] && { echo "STOP: watchdog fired"; exit 5; }; [ "$1" -eq 4 ] && { echo "STOP: blocked"; exit 4; }; return 0; }
diff_both_ways() {  # <WB>
  "$LANE/.venv/bin/python" - "$INST/wb_$1.declared" "$INST/run_wb_$1.observed" "$1" <<'PY'
import sys
def norm_decl(n):
    path, _, rest = n.partition("::"); stem = path.rsplit("/", 1)[-1].removesuffix(".py")
    parts = rest.split("::"); return f"{stem}." + ".".join(parts[:-1]) + "::" + parts[-1] if len(parts) > 1 else f"{stem}::{parts[0]}"
def norm_obs(n):
    cls, _, name = n.partition("::"); tail = cls.split(".")
    idx = max(i for i, t in enumerate(tail) if t.startswith("test_")) if any(t.startswith("test_") for t in tail) else 0
    return ".".join(tail[idx:]) + "::" + name
declared = {norm_decl(l) for l in open(sys.argv[1]).read().split("\n") if l.strip()}
observed = {norm_obs(l) for l in open(sys.argv[2]).read().split("\n") if l.strip()}
print(f"DIFF {sys.argv[3]}: declared={len(declared)} observed={len(observed)} "
      f"UNEXPECTED-RED={sorted(observed - declared)} DECLARED-BUT-GREEN={sorted(declared - observed)}")
PY
}
rm -f "$INST/WATCHDOG_FIRED"
for SHAPE in U C; do
  MINMEM=20 "$INST/run_lane.sh" "SATt_$SHAPE" "ref$SHAPE" 8 touched; stop_if_bad $?
done
for WB in PXlie PX2 PX2iso PXrem15 RS1srvT G4 FXt; do
  MINMEM=20 "$INST/run_lane.sh" "wb_$WB" refU 8 touched "$WB" > "$INST/driver_wb_$WB.log" 2>&1; rc=$?
  tail -4 "$INST/driver_wb_$WB.log" | head -2; stop_if_bad $rc; diff_both_ways "$WB"
done
MINMEM=20 "$INST/run_lane.sh" "wb_FXtC" refC 8 touched FXtC > "$INST/driver_wb_FXtC.log" 2>&1; rc=$?
tail -4 "$INST/driver_wb_FXtC.log" | head -2; stop_if_bad $rc; diff_both_ways FXtC
for SHAPE in U C; do
  (cd "$LANE" && git checkout -q -f "ref$SHAPE" && git clean -fdq && echo "LINT ref$SHAPE: ruff: $(uv run ruff check . 2>&1 | tail -1)" \
    && echo "LINT ref$SHAPE: typecheck: $(./scripts/typecheck.sh 2>&1 | awk '/^typecheck:/' | tr '\n' ' ')")
done
for SHAPE in U C; do
  "$INST/run_lane.sh" "SATfull_$SHAPE" "ref$SHAPE" 12 full; stop_if_bad $?
done
echo BATCH DONE
```

### A.5 `red_diff_fix.py` — md5 `116393dedddfee9b231b0f38ce374e56`
```python
"""contract-63c-i-a-r4b-fix: RED receipt — r4b tests (adversary-r4b red_r4b.xml: r4b tests on production @8900094)
vs r4b-fix tests (my junit, MAIN checkout @0242a19 + my edits). Production is byte-identical between the two
(`git diff --stat 8b9eb6d HEAD -- loremaster/loremaster lorerunes/lorerunes lorescribe/lorescribe loresigil/loresigil
loremaster/tests lorerunes/tests scripts` EMPTY at 0242a19). Restricted to the files the fix touched.
Usage: python red_diff_fix.py <r4b.xml> <fix.xml> <file-stem> [<file-stem> ...]"""
import sys
import xml.etree.ElementTree as ET


def load(path: str, stems: list[str]) -> dict[str, str]:
    out = {}
    for case in ET.parse(path).iter("testcase"):
        classname = case.get("classname", "")
        if not any(f".{stem}." in f".{classname}." or classname.endswith(stem) for stem in stems):
            continue
        key = f"{classname}::{case.get('name')}"
        red = case.find("failure") is not None or case.find("error") is not None
        out[key] = "red" if red else ("skip" if case.find("skipped") is not None else "green")
    return out


stems = sys.argv[3:]
old, new = load(sys.argv[1], stems), load(sys.argv[2], stems)
turned_red = sorted(k for k in old if k in new and old[k] == "green" and new[k] == "red")
turned_green = sorted(k for k in old if k in new and old[k] == "red" and new[k] == "green")
added = sorted(k for k in new if k not in old)
gone = sorted(k for k in old if k not in new)
print(f"r4b ids={len(old)} fix ids={len(new)} | r4b reds={sum(v == 'red' for v in old.values())} "
      f"fix reds={sum(v == 'red' for v in new.values())}")
print(f"TURNED RED (r4b green -> fix red): {len(turned_red)}")
for key in turned_red:
    print("  ", key)
print(f"TURNED GREEN (r4b red -> fix green): {len(turned_green)}")
for key in turned_green:
    print("  ", key)
print(f"NEW ids: {len(added)} — red {sum(new[k] == 'red' for k in added)}, green "
      f"{sum(new[k] == 'green' for k in added)}, skip {sum(new[k] == 'skip' for k in added)}")
for key in added:
    print(f"   {new[key]:5} {key}")
print(f"GONE ids: {len(gone)}")
for key in gone:
    print("  ", key)
```
