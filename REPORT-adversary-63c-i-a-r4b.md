# REPORT-adversary-63c-i-a-r4b — contract-adversary NARROW delta pass on the r4b addendum (`bf77fb9..8b9eb6d`)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done · **VERDICT: CONTRACT INSUFFICIENT.** The only defect is one **SAT DEFECT**, which the pre-ruling FIXES. The fix is 2 lines and proven in scratch (§F-2). Class breakdown: **SAME-FAMILY 2** (RS1srvT ownership, FXt fake-guard → KNOWN BOUND, lead records) · **SAT 1** (F-2) · **NEW-CLASS 2** (F-1 served-prose count, G4 witness axis → sidecar) · **LIVE 0**.
- **Graded:** `8b9eb6d` · HEAD-at-report: `8900094` · DIFFERENT (1 ahead: `8900094` lead report, docs only — `git diff --stat 8b9eb6d 8900094 -- loremaster lorerunes lorescribe loresigil scripts` EMPTY).
- **deviations:** none of substance. The declared sets for G3/G3d/FXs were narrower than observed (+1/+1/+2 right-reason reds, not re-declared). I re-ran none of the author's pinned-bound survivors (FXo/PX2w/TWR); their receipt is the author's COMBO (§4c).
- **Packages considered:** stdlib `ast` (`iter_fields`, `Name.ctx`) / `re` / pytest. No mechanism a package does better; agrees with the author's "bespoke, justified" (§9). **Odoo-20 portability:** n/a — no Odoo seam touched (0 = author's 0). **Reuse ledger:** none — no repo symbols added; scratch instruments pasted §A.
- **SAT (§1):** my own reference with ALL seven builder edits, **BOTH helper shapes, FULL SUITE ALONE `-n 12`:** uncollapsed `11486 passed, 62 skipped, 3 xfailed` / collapsed `11486 passed, 62 skipped, 3 xfailed`, **0 failed each**. Both trees were ruff-clean and passed `typecheck.sh` on every leg. = author's count. Amendment 12's "both shapes green" is now full-suite-measured.
- **P1 (§4):** 15 builds. **Killed as the rows rule:** PX2 (r1), RS1srv (r2, killed ONLY by the new pin), FXh (r3), G3 + G3d (r4), C2 / C2real / C2fake (r5). FXs was killed by the r3/r4 sharing pins, not by the allowlist. **4 builds SURVIVE THE FULL SUITE** (COMBO `11486 passed, 62 skipped, 3 xfailed`, 0 failed): **PXlie, RS1srvT, FXt, G4**.
- **F-2 SAT DEFECT (row 1):** a CORRECT build is RED. Birth value 15 with fully derived prose `(first 3 of 18 ids shown, 15 more)` gives `1 failed` on `R_Q5_1[perturbed-bound]`. The remainder 18−3 = 15 equals the birth value. The same prose at birth 10 is green (P0 control). Fix: add `birth_bound + id_bound` to the trap avoid-set + the remainder to the self-check (`fix_F2_test.py` §A.7). Proven in scratch: ref+fix `4 passed`, PXrem15+fix `4 passed`, PX2+fix `1 failed` [perturbed-bound].
- **F-1 NEW-CLASS (row 1):** N = the constant serves `(first 10 of 2 ids shown)` below the cap and passes everything. This is the r4b author's own reference form, and the test's own failure message teaches it. Builder edit 6 has TWO readings (§F-1).
- **G4 NEW-CLASS (row 4):** a SKIP gate narrowing on `--`/`__` survives the full suite. It is a new legal-side axis; by my count it is the 4th, so amendment-11's re-open trigger ("a FOURTH witness axis → derive the corpus") FIRES. The count is contestable (§G4).
- **RED@HEAD (§7):** 0 turned red · 0 turned green · 27 new = 5 red (right reason) + 22 green · 0 gone. The author's claim is CONFIRMED; row 2's pin is GREEN at HEAD. **Currency (§6):** unbuilt 20 RED_ADJUDICATED; built 11/11 SELF-DESTRUCT with 0 real mypy errors; built + entries deleted → typecheck GREEN; yaml delta is comment-only and honest.
- **decisions-needed:** lead — apply F-2's fix (the pre-ruling FIXES SAT; re-run my SAT leg or the author's) and record the 2 KNOWN BOUNDs (text §8). Sidecar — F-1 (brief sentence vs pin) and G4 (the trigger fired → derive the corpus, or re-count).
- **Receipt pointers:** §0 capability · §1 SAT · §2 lanes · §3 DUAL (+§3b diff) · §4 wrong builds · §4b COMBO · §5 row-3 scanner probe · §6 yaml/currency · §7 RED@HEAD · §8 findings + bounds · §8b P1b · §8c P1c · §9 P-PKG / P-PORT · §10 residuals · §A instruments · VERDICT.

## 0. Capability check (brief-base §4) — measured 2026-09-25
- Idle-gate contract written without denial: `/tmp/claude-idle-gate-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84-adversary-63c-i-a-r4b.contract` = `{"artifact": "REPORT-adversary-63c-i-a-r4b.md"}`. The session id is taken from my scratchpad path.
- lore MCP reachable: `lore_comms register` OK (session `63c-20260924`, cadence `≤20m`, heartbeats per milestone). `lore_get_symbol` was used for the seed helpers (§3b).
- grep/rg are hook-blocked (#473). A command containing the WORD tripped the hook once, as #473 predicts. Every textual sweep here is `awk`: the corpus consumer sweep (§8b Q4) is a non-symbol textual seam, so it is an honest fallback, and this line says so.
- Store reference `docs/reference/surrealdb-31-capabilities.md`: I read the §0 banner and the six READ-THIS facts. r4b touches no DDL. Builder edit 3 rebinds an identical pattern string in Python.
- Amendments 11 and 12 read in full before grading. No worktrees. No `git stash`. All mutation happened in `scratch_copy.sh` lanes. Main checkout: this report is the only write.

## 1. SATISFIABILITY — my independent reference, BOTH helper shapes, full suite ALONE (measured 2026-09-25, lane `ref`)
Launch gate each run: ≥23 GiB available and no other python/pytest/uv pytest in the process table. A PID watchdog kills at <12 GiB; it never fired.
| reference | full suite `-n 12` (tail, verbatim) | RED | window · memory |
|---|---|---|---|
| **U** `adv4b-refU` `c3a4092` — uncollapsed (`return is_legal_identifier`) | `11486 passed, 62 skipped, 3 xfailed, 7 warnings in 537.77s (0:08:57)` exit 0 | 0 | 11:50:58–12:00:04 EDT · 31 GiB at launch, lowest 22 |
| **C** `adv4b-refC` `5c91e55` — collapsed (helper deleted, direct call) | `11486 passed, 62 skipped, 3 xfailed, 7 warnings in 558.07s (0:09:18)` exit 0 | 0 | 12:00:19–12:09:40 EDT · 30 GiB at launch, lowest 23 |
- Both runs used the trees AFTER lint cleanup. On U and C, `uv run ruff check .` gives `All checks passed!` and `./scripts/typecheck.sh` gives `OK` on every leg (lorerunes, lorescribe, loresigil, loremaster, skills, docs/eval, scripts, shellcheck). In the collapsed shape `Callable` stays imported (used at the fake's formatter), so there is no F401 fallout.
- This equals the author's `11486 passed, 62 skipped, 3 xfailed / 0 failed`, **CONFIRMED independently on both shapes**. The author full-suited only the uncollapsed shape.
- Collect-only over the 25 contract files on U: **3024 ids** (= author's).
- ⚠ U's prose is MY reading of builder edit 6: N = ids actually shown. The author's reading (N = the constant) is also full-suite green (the author's §3, and my COMBO with PXlie, §4b). That green-under-both is exactly F-1.

## 2. Lanes (all scratch; every instrument pasted VERBATIM in §A)
- Scratch root: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad`. This is my own session scratchpad because the brief names no location, so every instrument is pasted in §A.
- Lane `ref`: `./scripts/scratch_copy.sh` rc=0 (the tool asserts provenance), a copy of `8900094`. Every pytest run re-asserts `loremaster.__file__` inside the lane before launching. Receipts:
  - `loremaster.__file__ = …/scratchpad/ref/loremaster/loremaster/__init__.py`
  - `lorerunes.__file__ = …/scratchpad/ref/lorerunes/lorerunes/__init__.py`
  - `_comms_fakes.__file__ = …/scratchpad/ref/loremaster/tests/_comms_fakes.py`
  - `_comms_fakes.is_legal_identifier is lorerunes.is_legal_identifier` → `True`
- Lane `head`: a second `scratch_copy.sh` copy (rc=0) at `8900094`, used for currency and RED@HEAD. `loremaster.__file__ = …/scratchpad/head/loremaster/loremaster/__init__.py`.
- Reference U = `my_ref_build_r4.py` (adversary-r4's, verbatim, md5 `3e419c75…`) + `my_ref_leg_r4a.py` (adversary-r4a's, verbatim, md5 `0058ae3c…`) + MY `my_ref_leg_r4b.py` (§A.1, md5 `7bf387f2…`). I wrote my leg without reading the author's. Reference C = the same three with `--collapse`.
- Builder edits (brief FOCUS 1), and which leg carries each:

  | # | builder edit | carried by |
  |---|---|---|
  | 1 | guard deleted + module-top import | r4a leg |
  | 2 | both yaml entries deleted → `bounds: []` | my leg |
  | 3 | `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` | r4 build |
  | 4 | `_REFUSAL_ID_SAMPLE_SIZE` WHY comment | r4a leg |
  | 5 | "from ANY caller, including a different householded principal" | r4a leg |
  | 6 | derived prose `(first {min(bound, M)} of {M} ids shown)` | my leg |
  | 7 | both helper shapes | U and C |

## 3. DUAL — my independent enumeration of r4b's deletions / re-keys
Written from `git diff bf77fb9 8b9eb6d -- loremaster lorerunes scripts` BEFORE I opened the author's §4.
| # | site (symbol) | kind | old behaviour / virtue | new |
|---|---|---|---|---|
| D1 | `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_…[perturbed-bound]` — sample-size PHRASE leg | DELETED | refused ANY stated sample size ≠ the PATCHED bound, incl. a third number | gone; DUAL comment at the old site |
| D2 | same — residue strip of `trap_ids` (hand-list) | RE-KEYED | stripped trap ids only | strips every str value + every `RecordID` (`str(v)`, `str(v.id)`) of every `before` row, longest-first, skipping pure-digit strings (derived) |
| D3 | same — full-count strip `\b{trap}\s+(?:agent\s+)?rows?\b` | RE-KEYED | count stripped only beside `row(s)` | `\b{trap_count}\b` everywhere (a birth value equal to `trap_count` becomes invisible — guarded by D4) |
| D4 | same — fixture counts | RE-KEYED (guard) | legacy 3, trap = bound+15 | bumped off `birth` and `birth − other`; self-check `birth ∉ {id_bound, trap, legacy, trap+legacy}` |
| D5 | same — assertion message teaching prose | RE-KEYED | `first {sample_size} ids shown` | `first {sample_size} of {count} ids shown` |
| D6 | same — docstring "the birth-value leg is the ∀ half" | RE-KEYED | claimed ∀ | "∀ over DIGIT spellings"; PX2w named as KNOWN BOUND + trigger |
| D7 | `_fake_predicate_import_violations` docstring "the `try` is the tell … FXf (any fallback)" | RE-KEYED (erratum) | over-claimed | narrowed; clause (iii) added (strictly more violations) |
| D8 | shape pin docstring "cannot outlive its premise in ANY spelling" + message | RE-KEYED (erratum) | over-claimed | "every guard that SPELLS the name"; obfuscation bound |
| D9 | `_comms_fakes.py::FakeAgentRegistry._shared_identifier_predicate` docstring | RE-KEYED (prose) | — | + allowlist sentence; code unchanged |
| D10 | `scripts/pending_contracts.yaml` 63c-i-a entry | comment-only (+3) | — | no key/value moved |
| A1–A5 | tool-seam pin · 2 keep-axis sequences + `_PARITY_OTHER_KEEP` · clause (iii) + 14 positive / 2 negative / 2 bound params · `a-`,`a_`,`00` · `RecordID` import | ADDED | — | — |
No test function deleted; no param removed.

### 3b. DUAL diff — mine vs the author's §4
| mine | author | agreement |
|---|---|---|
| D1 | D1 | AGREE. Dropped deliberately per amendment-11 MP-A2 (third-number virtue lost; ruled not a two-sources defect). |
| D2 | D2 (first half) | AGREE: preserved-with-pin. I verified the premise myself via `lore_get_symbol` on `_agent_content` / `seed_agent_governed`. Every seeded string carries letters, so no strip can erase a restated digit birth value, and PX2 still dies (§4). The seeded strings are `legacy-N`, `owned-legacy-N`, `dead-session`, `builder`, `active`, ids `legacy_N` / `owned_trap_NNN`, and owners `other_principal_N`. |
| D3 | D2 (second half) | AGREE. D3 and D4 are one change: the widened strip is only safe because D4 moves `trap_count` off birth. |
| D4 | D3 | AGREE on fixture counts. I EXECUTED the loops for birth 1..200 (`arith_r4b.py` §A.6): 0 self-check violations. **But the loops guard FIXTURE counts, not counts DERIVED from them. The remainder `trap − shown` equals birth at exactly one value, 15 → F-2.** |
| D5 | — | AUTHOR OMITS. It is prose-only, but it matters: the message TEACHES N = the constant, which is F-1. |
| D6 · D7/D8 · D10 | folded into D1/PX2w · D4 · their §6 | AGREE (errata / comment-only) |
| D9 | — | AUTHOR OMITS. Prose-only, and accurate (§5). |
No inventory item is ungrounded in the diff.

## 4. Wrong builds — declare-then-diff
Method:
- Declared sets were fixed from `--collect-only` over the 25 files on U (`collected_r4b.txt`, 3024 ids) BEFORE any wrong-build run, then diffed against observed reds BOTH ways.
- Scope: the 25 contract files (`files5.txt`, = adversary-r4a's), `-n 8`, on reference U. A declared `[]` predicts SURVIVAL.
- Instruments: driver `my_wbs_r4b.py` (§A.2), runner `run_full_r4b.sh` (§A.4), batch `batch_r4b.sh` (§A.5).
- Waits: the foreign-pytest gate held RS1srvT ~18 min because another project's (`mobile-pricepaper-smoke`) pytest was on the process table. No run overlapped a foreign pytest. The watchdog never fired.

| WB | what it does | declared RED | observed (tail) | diff | verdict |
|---|---|---|---|---|---|
| PX2 | prose restates the birth value: `(first 10 ids shown)` | `RQ51[perturbed-bound]` | `1 failed, 3004 passed, 19 skipped` | exact | **KILLED** — row 1 |
| FXh | fake: call-time `getattr(lorerunes,"is_legal_identifier",None)` + NON-silent private fallback, no `try` | shape pin | `1 failed, 3004 passed` | exact | **KILLED** — row 3 clause (iii) |
| RS1srv | TOOL re-stamps `owner_principal` to the caller after a correct registry re-register | tool-seam pin | `1 failed, 3004 passed` | exact | **KILLED** — row 2, and ONLY by row 2's pin (load-bearing) |
| C2 | real + fake re-stamp owner+scope when the caller's KEEP differs | `RE_REGISTER_door[consistent-then-different-keep]`, `[…-different-owner-and-keep]` | 2 red | exact | **KILLED** — row 5 |
| C2real | real writer only | same 2 | 2 red | exact | **KILLED** — absolute leg on `real` |
| C2fake | fake only | same 2 | 2 red | exact | **KILLED** — parity `fake == real`, with `real` absolute ⇒ the fake is bound absolutely, never `real == fake` alone |
| G3 | SKIP gate `or attribution.endswith(("-","_"))` | `SKIP_gate_moves…[a-]`, `[a_]` | 3 red | +1 UNEXPECTED: `…::test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus` (right reason: its legal-value loop reads the corpus) | **KILLED** — row 4 |
| G3d | SKIP gate `or attribution.isdigit()` | `…[00]` | 2 red | +1 UNEXPECTED, the same corpus control | **KILLED** — row 4 |
| FXs | fake: `from _adv_private_rules import *` AFTER the honest top import (shadows without spelling) | `[]` (prediction declared UNKNOWN) | 2 red | +2 UNEXPECTED: `TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[name-fake]`, `[session-fake]` | **KILLED — by the r3/r4 SHARING pins, NOT the allowlist** (blind to it, §5). Belt-and-braces working. |
| PXlie | prose N = the CONSTANT: `(first {_REFUSAL_ID_SAMPLE_SIZE} of {M} ids shown)` → `(first 10 of 2 ids shown)` below cap | `[]` | `3005 passed` | exact | **SURVIVES** → §4b · **F-1** |
| PXrem15 | a **CORRECT** build: birth 15, prose `(first {min(bound,M)} of {M} ids shown, {M − shown} more)` | `RQ51[perturbed-bound]` (predicted false RED) | `1 failed, 3004 passed` | exact | **SAT DEFECT CONFIRMED — F-2** (served text quoted in §8) |
| PXrem10 | P0 control: PXrem15's prose at birth 10 | `[]` | `3005 passed` | exact | GREEN — the red is the collision, not the phrase |
| RS1srvT | RS1srv's takeover conditioned `and task_id is not None` (an argument row 2's pin never passes) | `[]` | `3005 passed` | exact | **SURVIVES** → §4b · ownership family |
| FXt | fake: `try: legal = identifier_decision(value)` / `except Exception:` → PRIVATE regex decides | `[]` | `3005 passed` | exact | **SURVIVES** → §4b · fake-guard family |
| G4 | SKIP gate `or "--" in attribution or "__" in attribution` | `[]` | `3005 passed` | exact | **SURVIVES** → §4b · witness-axis (G) class |

### 4b. Full-suite leg for EVERY survivor (brief: a survivor is a survivor only on the FULL suite)
`run_full_r4b.sh COMBO adv4b-refU 12 full PXlie RS1srvT FXt G4`. The four anchors are pairwise disjoint: principals prose · server register seam · fake `_refuse` call · server SKIP gate. The lane had 3 dirty paths. Run 14:02:22–14:11:08 EDT, 36 GiB at launch, lowest 30 GiB.
**`11486 passed, 62 skipped, 3 xfailed, 7 warnings in 520.41s (0:08:40)` — exit 0, RED count 0. All four SURVIVE the full suite.**

### 4c. The author's survivor claims
The author's pinned-bound survivors FXo / PX2w / TWR were NOT re-run by me. Their receipt is the author's COMBO (`11486/0`, REPORT-contract-63c-i-a-r4b §3). I checked their bounds' presence in the tree:
- FXo: `test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named` (green at HEAD, §7).
- PX2w: the `R_Q5_1` docstring bound + trigger.
- TWR: r4a KB-2, unchanged.

The author's other claims I re-derived independently: PX2 killed (the author's own mutation run found the same) · RS1srv / FXh / C2 / C2fake / G3 / G3d killed · SAT `11486/0` · RED@HEAD 0/5/22 · 11 SELF-DESTRUCTs. All reproduced.

## 5. Row 3 — the allowlist scanner probed DIRECTLY (`scanner_probe_r4b.py` §A.3; import only, no pytest session)
Run on lane U, 2026-09-25 ~11:55 EDT. rc=0: no MISMATCH among the 12 labelled shapes.
| shape | expected | observed | note |
|---|---|---|---|
| honest bare-`Name` return (U) · collapsed direct call (C) | quiet | quiet · quiet | CTRL+ (both honest shapes) |
| `getattr(lorerunes,'is_legal_identifier',None)` | flag | `Constant.value` | CTRL−: fires on clause (iii)'s own text, not a parse error |
| `del` / `for`-target / `with … as` / `match` capture | flag | `Name.id` / `MatchAs.name` | the grammar complement holds |
| `__import__(…).__dict__['…']` · `globals()['…'] = …` | flag | `Constant.value` | |
| `from lorerunes import *` alone · import under `if TYPE_CHECKING` | flag | clause (i) | |
| honest import + second top import from the submodule | flag | `alias.name` | |
| **star-import shadow after the honest import (FXs)** | — | **quiet** | never spelled; the suite killed it via sharing pins (§4) |
| **`try` AROUND THE CALL, private fallback (FXt)** | — | **quiet** | survives the full suite (§4b) |
| REAL: ref-U fake · ref-C fake | quiet | 0 · 0 | SAT at the scanner |
| REAL: HEAD fake (anti-vacuity) | flag | 3 violations | clause (i) + call-time `alias.name` |
| dry FXh fake | flag | 1 (`Constant.value`) | |

Amendment 12's soundness claim ("a Load `Name` can reach only THE object") is TRUE, and nothing here falsifies it. What FXt shows is that the pin's PROPERTY is narrower than "the fake has no second identity decision". The pin's own docstring states that narrower scope honestly: "every guard that SPELLS the predicate's name".

## 6. `scripts/pending_contracts.yaml` — honesty + self-destruct on the built world (#461) — lane `head`, `--legs typecheck,ruff` only
| world | typecheck leg | ruff | verdict |
|---|---|---|---|
| UNBUILT `8900094` | `RED_ADJUDICATED — 20 residual(s)` owned by `packet-63c-i-a-contract-r2` · `-r3` | GREEN | = author's 20 (= r4a's). The yaml comment "no count changes" is TRUE. |
| BUILT (r4 + r4a legs), HEAD yaml kept | `RED_ORPHANED — 11 residual(s)`: ALL 11 are `SELF-DESTRUCT` (10 files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"); 0 real errors | GREEN | = author's 11. The entries FAIL the gate until deleted, so they cannot linger; no wrong discharge. |
| BUILT + both entries deleted (`bounds: []`) | **GREEN** | GREEN | builder edit 2 leaves typecheck green |
In all three, pytest shows `NOT_RUN` by design (→ currency rc=1 for that reason only). The r4b yaml delta is 3 comment lines, and their text matches the measured scanner behaviour (§5): **HONEST**. The head lane was restored to `8900094` afterwards (scratch lane only).

## 7. RED@HEAD — r4b tests on UNBUILT production (lane `head` @ `8900094`), 25 files, `-n 8`
`r4b tests @HEAD: 195 failed, 2759 passed, 19 skipped, 4 warnings, 51 errors in 367.69s`. I diffed this (`red_diff_r4b.py` §A.9) against adversary-r4a's `red_r4a.xml`: r4a tests on production @`1705ea3`, where `190 failed … 51 errors` = 241 reds. `git diff 1705ea3 8900094 -- loremaster/loremaster lorerunes lorescribe loresigil` is EMPTY, so production is byte-identical.
- r4a 2997 ids / 241 reds → r4b 3024 ids / 246 reds. **TURNED RED 0 · TURNED GREEN 0 · NEW 27 = 5 red + 22 green · GONE 0** — the author's claim is **CONFIRMED**.
- The 5 new reds, all for the right reason (the unbuilt `session_keep_id` kwarg / the missing `lorerunes.is_legal_identifier`):
  - `RE_REGISTER_door[consistent-then-different-keep]`
  - `RE_REGISTER_door[consistent-then-different-owner-and-keep]`
  - `SKIP_gate_moves…[a-]`, `[a_]`, `[00]`
- 22 new greens:
  - row 2's tool-seam pin (**GREEN at HEAD**, as amendment 11 requires)
  - `register_accepts_a_valid_identifier_positive_control[a-|a_|00]`
  - the 14 allowlist positives, the 2 new negatives and the 2 KNOWN-BOUND controls

## 8. Findings, classified (pre-ruling: amendment 11 §1)
### F-2 — **SAT DEFECT** (row 1; correct build RED) — FIX under the pre-ruling
- **Failing node:** `loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[perturbed-bound]`
- **Correct build:** `_REFUSAL_ID_SAMPLE_SIZE = 15` (R-3: the value is NOT normative; adversary-r3 floated "≤ 20") with fully derived prose. The refusal it served, verbatim: `'18 agent row(s) carry an owner but no scope (agent:owned_trap_000, agent:owned_trap_001, agent:owned_trap_002) — a multi-principal or half-applied store (first 3 of 18 ids shown, 15 more); adjudicate these rows by hand before migrating (§2.1)'`. It was refused with *"restates the BIRTH sample size 15"*. That is false: 15 is the remainder 18 − 3.
- **Root cause:** the fixture-count guard (D4) covers counts the fixture INTRODUCES, not counts DERIVED from them. Executed over birth 1..200, the only collision is birth 15.
- **Minimal fix (2 lines, `fix_F2_test.py` §A.7):**

  ```python
  while trap_count in (birth_bound, birth_bound - legacy_count, birth_bound + id_bound):
  fixture_counts = {id_bound, trap_count, legacy_count, trap_count + legacy_count, trap_count - id_bound}
  ```

  Executed for birth 1..500: 0 collisions over `{shown, M, legacy, M+legacy, M−shown}`.
- **Proof (scratch only, `fixproof_F2.sh` §A.8):**

  | leg | result | meaning |
  |---|---|---|
  | ref U + fix | `4 passed` | still SAT |
  | PXrem15 + fix | `4 passed` | false RED removed |
  | PX2 + fix | `1 failed` = `[perturbed-bound]` | the birth leg is NOT blinded |

- **Honest reach:** a builder that follows the brief's exact prose `(first N of M ids shown)` never states a remainder. The defect bites only a correct build that ALSO states the remainder at birth 15. Narrow, but it is a correct build going RED, which is the class the pre-ruling fixes. The alternative, a builder-brief ban on remainder prose, would constrain the builder instead of the contract, so I don't recommend it.

### F-1 — **NEW-CLASS** (row 1: served-prose ACCURACY, not a fake-guard or ownership door) → sidecar
- **What survives:** PXlie. With N = the constant, the refusal serves **`(first 10 of 2 ids shown)`** in the below-cap population: a false served count (CONSUMER LAW: a served count must describe the set it names). It survives the full suite (§4b).
- **Why it is plausible, not contrived:**
  - It is the **r4b author's own reference** (`(first {_REFUSAL_ID_SAMPLE_SIZE} of {len(owned_unscoped_ids)} ids shown)`, their §3).
  - It is what the pin's failure message teaches (D5: `first {sample_size} of {count} ids shown`).
  - Builder edit 6, "the derived `(first N of M ids shown)` prose", admits TWO readings: **(a)** N = ids actually shown = `min(bound, M)`, which I pick and which my reference U builds; **(b)** N = the constant. Per brief-base §2, both readings are written here.
- **Why NEW-CLASS:** it is neither the fake-guard nor the ownership family. The birth-value leg only asks "is the number the BIRTH value", never "is the number TRUE".
- **Cheapest fixes (sidecar picks):**
  - (i) Builder brief, one sentence: "N = the number of ids actually named, `min(_REFUSAL_ID_SAMPLE_SIZE, count)`". Plus reword D5's message to `first {shown} of {count}`.
  - (ii) A pin: run the digit leg in `below-cap` too, where a correct build never needs the bound's value. This needs D4's count guard mirrored there.
- **Re-open trigger if ruled a bound:** "a served refusal found stating a sample size larger than its count".

### G4 — **NEW-CLASS** (row 4: the legal-witness axis class, which amendment 11 gave its own trigger) → sidecar
- **What survives:** a SKIP gate narrowing `or "--" in attribution or "__" in attribution` ("doubled separators are a typo", a plausible honest rule). It survives the full suite (§4b), because no legal witness carries consecutive separators.
- **Why NEW-CLASS:** it is not in either pre-ruled family.
- **Amendment 11's own trigger:** "a FOURTH witness axis found by an adversary → derive the corpus".
  - By my count the adversary-found legal axes are cap (G1, r4) · trailing separator (G3, r4a) · all-digit (G3d, closed alongside G3 in r4b), so G4 is the **fourth** and the trigger **FIRES**.
  - If the sidecar counts all-digit as sidecar-found rather than adversary-found, G4 is the third and the bound stands.
  - Either way, the ruled alternative to deriving is growing the hand-list (`"a--b"`, `"a__b"`), which is one more level of the recession amendment 11's STOP-rule warns about.
- **Recommendation:** derive per the ruling, OR record the bound with the ruling's rigor-to-importance note ("footer gate"). This is the sidecar's call.

### RS1srvT — **SAME-FAMILY (ownership) → KNOWN BOUND** (lead records)
- **What survives:** a takeover at the tool seam conditioned on an optional register argument. Row 2's pin calls `comms(action="register")` with only `agent/session/role` (parameter monoculture on the optional arguments). It survives the full suite (§4b).
- **Proposed KNOWN BOUND line:**
  > *KNOWN BOUND (amendment-11 pre-ruling, ownership family): the end-to-end invariance pin drives ONE argument shape (agent/session/role); a takeover conditioned on an optional register argument (model / spawned_by / task_id / cadence) survives it (adversary-r4b RS1srvT, full suite 11486/0). Threat model: the honest builder — no honest ownership rule keys on an optional descriptive argument.*
- **RE-OPEN TRIGGER:** any branch in `_comms_register` / `AgentRegistry.register` that reads model / spawned_by / task_id / cadence on the re-register path.
- **Closure if reopened:** one extra joiner call with every optional argument set, which is one param.

### FXt — **SAME-FAMILY (fake-guard) → KNOWN BOUND** (lead records)
- **What survives:** a `try` around the CALL whose `except Exception:` decides with a PRIVATE regex. It survives the full suite (§4b). The allowlist constrains how the NAME occurs, not whether the fake holds a second decision that never names it. The effect pin sees only silent skips.
- **Current impact:** inert today. The fallback fires only if `is_legal_identifier` raises, and it does not raise on the `str` inputs the fake receives.
- **Proposed KNOWN BOUND line:**
  > *KNOWN BOUND (amendment-11 pre-ruling, fake-guard family): the allowlist certifies every occurrence of the predicate's NAME in `_comms_fakes.py`; a second identity decision that never names it — an `except` handler around the CALL deciding with a private rule — survives (adversary-r4b FXt, full suite 11486/0), inert while the shared predicate cannot raise on `str`. Threat model: the honest builder.*
- **RE-OPEN TRIGGER:** an `except` handler around an identity decision in any test double, or i-b's new test doubles (amendment-10 C-5 branch 2).

### LIVE-PRODUCTION-DEFECT — none
Production is unchanged since `1705ea3`. At HEAD it fails exactly the contract's declared RED set (§7) and nothing beyond it. `:18500` was never touched and the TEI embedder never called, so this is a statement about the tree, not the deployed image. MEDIUM, the same basis as amendment 11 §MP-A3.

## 8b. P1b — quantifier table (the invariants r4b's rows pin)
| # | invariant | ∀ or guarded | receipt |
|---|---|---|---|
| Q1 | refusal prose never restates the constant's birth value | ∀ over DIGIT spellings, in `perturbed-bound` only (the only population where birth ≠ current) | PX2 killed; PX2w = pinned bound. **Over-broad:** refuses a correct derived remainder → F-2 (SAT) |
| Q1′ | the stated sample count is TRUE | **not pinned** | PXlie survives the full suite → F-1 |
| Q2 | re-register never changes the governed triple, ∀ callers, at the tool seam | guarded by ARGUMENT SHAPE (agent/session/role) | RS1srv killed; RS1srvT survives → bound |
| Q3 | the fake's identity decision IS the shared object | ∀ over name occurrences (receiver-blind); guarded by "reached via the name" | FXh killed (allowlist); FXs killed (sharing pins); FXo pinned bound; FXt survives → bound |
| Q4 | the SKIP gate accepts every legal identity | ∀ over a HAND-LIST corpus (stated bound) | G3/G3d killed; G4 survives → trigger. Consumers (awk sweep of the corpus name, a non-symbol textual seam): 3 — `test_agent_registry.py` register accept-control, SKIP-mutation param, legal-value loop — all read the tuple dynamically, so every new witness reaches all three |
| Q5 | re-register keeps the FIRST keep's scope, real and fake | ∀ over the 2×2 {same,different} owner × keep grid at the registry seam (tool seam unreachable, am-10 C-2) | C2 / C2real / C2fake killed |

## 8c. P1c — reach table (instruments r4b introduces or relies on)
| instrument | reach DERIVED? | coverage checked? | effect vs proxy | one source by mutation? | legs |
|---|---|---|---|---|---|
| I-1 clause (iii) scanner | file: ONE (`_comms_fakes.py`, ruled am-11 C-5, trigger named); within the file DERIVED (every AST node via `ast.iter_fields`) | anti-vacuity: HEAD fake flagged (3 violations, measured §5) | SHAPE by design; the effect pin covers silent skip; FXt sits in the gap → bound | `_PREDICATE_NAME` constant (inspection) | empirical (§5, FXh/FXt/FXs) |
| I-2 tool-seam pin | outermost seam — DERIVED by construction (row read after the whole call) | controls: foreign DENIED, joiner's own row joiner-stamped, keeper owns beforehand (inspection); RS1srv kill proves it can FAIL | EFFECT (row bytes) | n/a | empirical (RS1srv, RS1srvT) |
| I-3 seeded-identifier strip | DERIVED from `before` | PX2 still killed | effect | n/a | empirical |
| I-4 fixture-count guard | DERIVED from birth over FIXTURE counts; **misses DERIVED counts** | self-check assert | — | n/a | empirical (PXrem15 / PXrem10 / fix proof) → F-2 |
| I-5 legal witness corpus | HAND-LIST (stated bound + trigger) | — | — | shared tuple, read dynamically by 3 consumers | empirical (G3, G3d, G4) |

## 9. P-PKG / P-PORT
- **P-PKG:** I built my table first. The mechanisms are an AST name-occurrence scan (stdlib `ast.iter_fields` is the stdlib's own generic field walker, and `Name.ctx` is the only way to separate Load / Store / Del), a regex residue scan (`re`), and pytest parametrisation. No third-party package does an allowlist-over-AST-names job better, and none would replace these ~40 lines. This agrees with the author's "bespoke, justified". Nothing is hand-rolled one level down.
- **P-PORT:** no Odoo seam touched (0 = author's 0).

## 10. Residuals (each individually)
1. Author's R-2 (a purely-digit seeded identifier equal to birth would false-RED): **unreachable at `8b9eb6d`**. Every seeded string carries letters (§3b). Stated, not a finding.
2. The author's SAT reference serves PXlie's false prose below the cap. Their SAT is still valid (0 failed); it is just the F-1 reading.
3. FXs is killed by the r3/r4 SHARING pins, not by the allowlist. **Nobody may delete those pins believing the allowlist covers star-import shadowing.** Worth one line in the allowlist docstring's bound (lead's call).
4. Author's R-1 (the collapse is a post-build simplification): both shapes are now full-suite green (§1). The builder may collapse at no cost.
5. D5: the pin's failure message teaches N = the constant. It goes with F-1's resolution.
6. Ops: another project's pytest (`mobile-pricepaper-smoke`) held one run ~18 min. The author reports the same (their R-8).
7. No lore friction filed. The grep-word hook (#473) is already ledgered. One `lore_search` with `detail_level="summary"` returned a DETAIL MISS that correctly taught the retry, which is honest behaviour and not a defect.
8. No worktree created. The scratch lanes (`ref`, `head`, `dry/`) sit in my session scratchpad and can be discarded; nothing in them is the only copy of anything, since §A carries every instrument.

## A. Instruments (pasted VERBATIM — md5 at report time)

### A.1 `my_ref_leg_r4b.py` — md5 `7bf387f20cee6a798d78ad127e0b522c`
```python
"""adversary-63c-i-a-r4b — my r4b leg, applied AFTER adversary-r4's my_ref_build_r4.py (md5 3e419c75…) and
adversary-r4a's my_ref_leg_r4a.py (md5 0058ae3c…), both run VERBATIM.

Builder edits the r4b brief lists that the two prior legs do NOT already carry:
  (2) delete BOTH 63c-i-a entries in scripts/pending_contracts.yaml  (-> `bounds: []`)
  (6) the DERIVED "(first N of M ids shown)" prose in the migrate refusal.
      N = the number of ids ACTUALLY shown (min(bound, count)) — my reading; the author's reading
      (N = the constant itself) is a separate variant, `--prose=constant`.
  (7) optional `--collapse`: amendment-12's second honest shape — delete `_shared_identifier_predicate`
      and call `is_legal_identifier(value)` directly in `_refuse_what_the_writer_refuses`.
Already carried: (1) module-top import + guard deleted (r4a leg), (3) `_IDENTIFIER_CHARSET_PATTERN`
rebind (r4 build), (4) `_REFUSAL_ID_SAMPLE_SIZE` WHY comment (r4a leg), (5) "from ANY caller" (r4a leg).
Written WITHOUT reading the r4b author's my_ref_leg_r4b.py. Each edit asserts its anchor occurs exactly once (#194).
Usage: uv run --no-project python my_ref_leg_r4b.py <scratch-root> [--prose=shown|constant] [--collapse]
"""

import sys
from pathlib import Path

ROOT = Path(sys.argv[1])
PROSE = next((arg.split("=", 1)[1] for arg in sys.argv if arg.startswith("--prose=")), "shown")
COLLAPSE = "--collapse" in sys.argv


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    count = text.count(old)
    assert count == 1, f"{rel}: anchor occurs {count} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


YAML = "scripts/pending_contracts.yaml"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"

# (2) both 63c-i-a entries are the ONLY entries under `bounds:` — delete them; `bounds:` is empty again.
yaml_path = ROOT / YAML
yaml_text = yaml_path.read_text()
anchor = "bounds:\n  - id: packet-63c-i-a-contract-r2\n"
assert yaml_text.count(anchor) == 1, "yaml anchor"
assert yaml_text.count("  - id: ") == 2, "expected exactly the two 63c-i-a entries"
yaml_path.write_text(yaml_text[: yaml_text.index(anchor)] + "bounds: []\n")

# (6) derived sample prose. The refusal text after my_ref_build_r4.py's lint cleanup:
if PROSE == "shown":
    shown = "min(_REFUSAL_ID_SAMPLE_SIZE, len(owned_unscoped_ids))"
elif PROSE == "constant":
    shown = "_REFUSAL_ID_SAMPLE_SIZE"
else:
    raise SystemExit(f"unknown --prose {PROSE}")
edit(
    PRINCIPALS,
    '                "half-applied store; "\n',
    f'                f"half-applied store (first {{{shown}}} of "\n'
    '                f"{len(owned_unscoped_ids)} ids shown); "\n',
)

# (7) optional collapse (amendment 12: the builder MAY)
if COLLAPSE:
    fakes_path = ROOT / FAKES
    text = fakes_path.read_text()
    start = text.index("    @staticmethod\n    def _shared_identifier_predicate()")
    end_marker = "        return is_legal_identifier\n\n"
    end = text.index(end_marker, start) + len(end_marker)
    assert text.count("def _shared_identifier_predicate") == 1
    fakes_path.write_text(text[:start] + text[end:])
    edit(
        FAKES,
        "        identifier_decision = FakeAgentRegistry._shared_identifier_predicate()\n"
        "        if identifier_decision is not None:  # None at HEAD only — see the helper's removal trigger\n"
        "            for field_name, value in ((\"name\", name), (\"session\", session)):\n"
        "                if not identifier_decision(value):\n"
        "                    raise AgentRegistryError(f\"fake register: illegal {field_name}; nothing was written\")\n",
        "        for field_name, value in ((\"name\", name), (\"session\", session)):\n"
        "            if not is_legal_identifier(value):\n"
        "                raise AgentRegistryError(f\"fake register: illegal {field_name}; nothing was written\")\n",
    )
print(f"adversary-r4b leg applied (yaml bounds emptied; prose={PROSE}; collapse={COLLAPSE})")
```

### A.2 `my_wbs_r4b.py` — md5 `2de4368cae455e2f39ebe3a39f9243f1`
```python
"""adversary-63c-i-a-r4b — wrong builds (and two CORRECT-build SAT probes) ON TOP of my reference U
(lane branch adv4b-refU = my_ref_build_r4.py + my_ref_leg_r4a.py + my_ref_leg_r4b.py, uncollapsed fake).
Floor bodies (PX2, FXh, RS1srv, C2, G3) re-use adversary-r4a's my_wbs_r4a.py bodies (REPORT-adversary-63c-i-a-r4a.md
§A.3), re-anchored where my r4b leg changed the refusal prose. New builds are mine.

Usage: uv run --no-project python my_wbs_r4b.py <scratch-root> <WB-id> [--declared]
  --declared  print the DECLARED expected-RED node ids, resolved against collected_r4b.txt (collect-only over
              files5.txt on adv4b-refU, taken BEFORE any wrong-build run) and exit.
Each edit asserts its anchor occurs exactly once (#194). A DECLARED set of [] predicts the build SURVIVES.
"""

import sys
from pathlib import Path

INST = Path(__file__).resolve().parent
ROOT = Path(sys.argv[1])
WB = sys.argv[2]

AGENTS = "loremaster/loremaster/agents.py"
SERVER = "loremaster/loremaster/server.py"
PRINCIPALS = "loremaster/loremaster/principals.py"
FAKES = "loremaster/tests/_comms_fakes.py"

GOV = "test_agent_governance_63c_i_a.py"
REG = "test_agent_registry.py"
SHAPE = "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"
RQ51 = "test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
REREG_PARITY = "test_the_fake_and_the_real_writer_agree_on_the_RE_REGISTER_door"
TOOL_PIN = "test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched"
SKIP_MUT = "test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier"

# DECLARED expected-RED sets — (file fragment, [node fragments ALL required]). Written BEFORE any run.
DECLARED: dict[str, list[tuple[str, list[str]]]] = {
    # --- the author's claimed kills, re-derived ---
    "PX2": [(GOV, [RQ51, "perturbed-bound"])],
    "FXh": [(REG, [SHAPE])],
    "RS1srv": [(GOV, [TOOL_PIN])],
    "C2": [(REG, [REREG_PARITY, "consistent-then-different-keep"]),
           (REG, [REREG_PARITY, "consistent-then-different-owner-and-keep"])],
    "C2real": [(REG, [REREG_PARITY, "consistent-then-different-keep"]),
               (REG, [REREG_PARITY, "consistent-then-different-owner-and-keep"])],
    "C2fake": [(REG, [REREG_PARITY, "consistent-then-different-keep"]),
               (REG, [REREG_PARITY, "consistent-then-different-owner-and-keep"])],
    "G3": [(REG, [SKIP_MUT, "[a-]"]), (REG, [SKIP_MUT, "[a_]"])],
    "G3d": [(REG, [SKIP_MUT, "[00]"])],
    # --- my new builds ---
    "PXlie": [],  # prose N = the CONSTANT (the r4b author's own reference form): "first 10 of 2 ids shown" below cap
    "PXrem15": [(GOV, [RQ51, "perturbed-bound"])],  # CORRECT build (birth 15, derived remainder prose) — SAT probe
    "PXrem10": [],  # P0 control for PXrem15: same prose at birth 10 -> must be green
    "RS1srvT": [],  # tool-seam takeover conditioned on an argument the pin never passes (task_id)
    "FXt": [],  # fake: try AROUND THE CALL with a non-silent private-regex fallback (no import in the try, name Load-only)
    "FXs": [],  # fake: star-import shadow AFTER the honest module-top import (name never spelled) — prediction unknown
    "G4": [],  # SKIP gate narrows on CONSECUTIVE separators ('--' / '__') — an axis no legal witness carries
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
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"
FAKE_REREG = "        # status resets to active unconditionally (retired already excluded above).\n"
PRIVATE_RULE = 'lambda value: re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is not None'
PROSE_SHOWN = "{min(_REFUSAL_ID_SAMPLE_SIZE, len(owned_unscoped_ids))}"
PROSE_TAIL = '                f"{len(owned_unscoped_ids)} ids shown); "\n'
BIRTH = "_REFUSAL_ID_SAMPLE_SIZE = 10\n"


def gate(extra: str) -> None:
    edit(SERVER, GATE,
         "        if (\n"
         "            attribution is None\n"
         "            or not AppContext._is_comms_charset_legal(attribution)\n"
         f"            or {extra}\n"
         "        ):\n")


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


def tool_takeover(extra_condition: str) -> None:
    edit(SERVER,
         "        registered_age_s = int((now - result.agent.registered_at).total_seconds())\n",
         "        registered_age_s = int((now - result.agent.registered_at).total_seconds())\n"
         "        if result.re_registered and principal_bare is not None and hasattr(self.agent_registry, \"_query\")"
         f"{extra_condition}:\n"
         "            # 'the owner follows the most recent registrant' — a TAKEOVER at the tool seam\n"
         "            await self.agent_registry._query(  # noqa: SLF001\n"
         "                \"UPDATE type::record('agent', $rid) SET owner_principal = type::record('principal', $owner)\",\n"
         "                {\"rid\": self.agent_registry._agent_id(session, agent), \"owner\": principal_bare},  # noqa: SLF001\n"
         "            )\n")


if WB == "PX2":
    edit(PRINCIPALS, f'                f"half-applied store (first {PROSE_SHOWN} of "\n' + PROSE_TAIL,
         '                "half-applied store (first 10 ids shown); "\n')
elif WB == "PXlie":
    edit(PRINCIPALS, PROSE_SHOWN, "{_REFUSAL_ID_SAMPLE_SIZE}")
elif WB in ("PXrem15", "PXrem10"):
    if WB == "PXrem15":
        edit(PRINCIPALS, BIRTH, "_REFUSAL_ID_SAMPLE_SIZE = 15\n")
    edit(PRINCIPALS, PROSE_TAIL,
         '                f"{len(owned_unscoped_ids)} ids shown, "\n'
         f'                f"{{len(owned_unscoped_ids) - {PROSE_SHOWN[1:-1]}}} more); "\n')
elif WB == "FXh":
    edit(FAKES, HELPER_BODY,
         "        import re  # noqa: PLC0415\n\n"
         "        import lorerunes  # noqa: PLC0415 - call-time read: 'robust' if the predicate is ever absent\n\n"
         "        if getattr(lorerunes, \"is_legal_identifier\", None) is not None:\n"
         "            return is_legal_identifier\n"
         f"        return {PRIVATE_RULE}\n")
elif WB == "FXt":
    edit(FAKES, "                if not identifier_decision(value):\n",
         "                try:\n"
         "                    legal = identifier_decision(value)\n"
         "                except Exception:  # noqa: BLE001 - 'robust': a predicate hiccup never crashes a fake\n"
         "                    import re  # noqa: PLC0415\n\n"
         "                    legal = re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n"
         "                if not legal:\n")
elif WB == "FXs":
    rules = ROOT / "loremaster/tests/_adv_private_rules.py"
    assert not rules.exists()
    rules.write_text(
        '"""a private identity rule (FXs wrong build)."""\n\nimport re\n\n'
        "__all__ = [\"is_legal_identifier\"]\n\n\n"
        "def is_legal_identifier(value: str) -> bool:\n"
        "    return re.fullmatch(r\"[a-z0-9][a-z0-9_-]{0,63}\", value) is not None\n")
    edit(FAKES, "from lorerunes import is_blank, is_legal_identifier\n",
         "from lorerunes import is_blank, is_legal_identifier\n"
         "from _adv_private_rules import *  # noqa: F403, E402\n")
elif WB == "RS1srv":
    tool_takeover("")
elif WB == "RS1srvT":
    tool_takeover(" and task_id is not None")
elif WB == "C2":
    real_restamp(C2_REAL)
    fake_restamp(C2_FAKE)
elif WB == "C2real":
    real_restamp(C2_REAL)
elif WB == "C2fake":
    fake_restamp(C2_FAKE)
elif WB == "G3":
    gate("attribution.endswith((\"-\", \"_\"))  # 'a dangling separator is never a real name'")
elif WB == "G3d":
    gate("attribution.isdigit()  # 'an all-digit attribution is a counter, not a name'")
elif WB == "G4":
    gate("\"--\" in attribution or \"__\" in attribution  # 'doubled separators are a typo'")
else:
    raise SystemExit(f"unknown WB {WB}")
print(f"{WB} applied")
```

### A.3 `scanner_probe_r4b.py` — md5 `f8f7d409f192bba6931c14b10ba75b24`
```python
"""adversary-63c-i-a-r4b: probe the r4b clause-(iii) scanner DIRECTLY (import, no pytest session).
Usage (from the lane root): .venv/bin/python scanner_probe_r4b.py <lane-root> [<real fakes file> ...]"""
import ast, sys
from pathlib import Path
lane = Path(sys.argv[1]); sys.path[:0] = [str(lane / "loremaster/tests")]
import test_agent_registry as reg  # noqa: E402
scan = reg._fake_predicate_import_violations
TOP = "import lorerunes\nfrom lorerunes import is_blank, is_legal_identifier\n"
CASES = {
    # (expect_flagged, source)
    "CTRL+ honest bare-Name return": (False, TOP + "def p():\n    return is_legal_identifier\n"),
    "CTRL+ collapsed direct call": (False, TOP + "def p(v):\n    return is_legal_identifier(v)\n"),
    "CTRL- getattr (FXh core)": (True, TOP + "def p():\n    return getattr(lorerunes, 'is_legal_identifier', None)\n"),
    "star-import shadow AFTER the honest import (FXs)": (None, TOP + "from _adv_private_rules import *\n"),
    "try AROUND THE CALL, private fallback (FXt)": (None, TOP + "import re\ndef p(v):\n    try:\n        return is_legal_identifier(v)\n    except Exception:\n        return re.fullmatch('[a-z0-9]+', v) is not None\n"),
    "del rebind": (True, TOP + "del is_legal_identifier\n"),
    "match capture": (True, TOP + "def p(x):\n    match x:\n        case is_legal_identifier:\n            return is_legal_identifier\n"),
    "for-target rebind": (True, TOP + "for is_legal_identifier in [None]:\n    pass\n"),
    "with-as rebind": (True, TOP + "import contextlib\nwith contextlib.nullcontext(None) as is_legal_identifier:\n    pass\n"),
    "__import__ dict read": (True, TOP + "def p():\n    return __import__('lorerunes').__dict__['is_legal_identifier']\n"),
    "globals() write spelled": (True, TOP + "globals()['is_legal_identifier'] = None\n"),
    "star-import ONLY (no named import)": (True, "from lorerunes import *\n"),
    "module-top import inside if TYPE_CHECKING else": (True, "import typing\nif typing.TYPE_CHECKING:\n    from lorerunes import is_legal_identifier\n"),
    "honest import + second top import of same name from a submodule": (True, TOP + "from lorerunes.identifiers import is_legal_identifier\n"),
}
bad = 0
for label, (expect, src) in CASES.items():
    v = scan(ast.parse(src)); flagged = bool(v)
    verdict = "n/a" if expect is None else ("OK" if flagged == expect else "MISMATCH")
    bad += verdict == "MISMATCH"
    print(f"{verdict:8} flagged={flagged!s:5} {label}" + (f"  :: {v[0][:110]}" if v else ""))
for real in sys.argv[2:]:
    v = scan(ast.parse(Path(real).read_text())); print(f"REAL {real.split('/scratchpad/')[-1]}: {len(v)} violation(s) {v[:2]}")
sys.exit(1 if bad else 0)
```

### A.4 `run_full_r4b.sh` — md5 `8a606f1ea1b317b2c15e1fd449763178`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b: pytest ALONE on the ref lane at <base-branch> (+ optional WBs from my_wbs_r4b.py, in order).
# Launch gate: MemAvailable >= $MINMEM GiB (default 23 for -n 12) AND no other python/pytest/uv pytest process; polls up
# to 30 min, else exits 4 ("blocked"). Watchdog kills OUR pytest by PID when MemAvailable < 12 GiB (then STOP).
# Usage: run_full_r4b.sh <label> <base-branch> <nproc> <scope: full | files5> [WB ...]
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/ref
LABEL=$1; BASE=$2; NPROC=$3; SCOPE=$4; shift 4
MINMEM=${MINMEM:-23}
cd "$LANE" || exit 2
git checkout -q -f "$BASE" && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-adversary-63c-i-a-r4b.md
for WB in "$@"; do uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$WB" >/dev/null || { echo "$WB apply failed"; exit 2; }; done
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
if [ "$SCOPE" = full ]; then TARGETS=(); else mapfile -t TARGETS < "$INST/files5.txt"; fi
deadline=$(( $(date +%s) + 1800 ))
while :; do
  avail=$(awk '/MemAvailable/{print int($2/1048576)}' /proc/meminfo)
  busy=$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{n++} END{print n+0}')
  [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
  sleep 20
done
echo "base=$BASE WBs=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | awk '!/REPORT-/' | wc -l); avail at launch ${avail} GiB; $(date '+%F %T')"
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
git checkout -q -f "$BASE" && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-adversary-63c-i-a-r4b.md
```

### A.5 `batch_r4b.sh` — md5 `daea1406a4f68882c8e532cbedb65e30`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b batch: (1) collect-only over files5 on adv4b-refU -> collected_r4b.txt (BEFORE any WB run);
# (2) DECLARE every WB's expected-RED set from it; (3) SAT_C full suite; (4) each WB on files5 (-n 8), observed vs declared diffed BOTH ways.
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/ref
WBS="PX2 FXh RS1srv C2 C2real C2fake G3 G3d PXlie PXrem15 PXrem10 RS1srvT FXt FXs G4"
cd "$LANE" && git checkout -q -f adv4b-refU || exit 2
mapfile -t TARGETS < "$INST/files5.txt"
.venv/bin/python -m pytest --collect-only -q -p no:cacheprovider "${TARGETS[@]}" 2>/dev/null | awk '/::/' | sort > "$INST/collected_r4b.txt"
echo "collected: $(wc -l < "$INST/collected_r4b.txt") ids"
for WB in $WBS; do
  uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$WB" --declared | sort > "$INST/wb_${WB}.declared" || { echo "declare $WB failed"; exit 3; }
  echo "declared $WB: $(wc -l < "$INST/wb_${WB}.declared")"
done
"$INST/run_full_r4b.sh" SAT_C adv4b-refC 12 full
for WB in $WBS; do
  MINMEM=20 "$INST/run_full_r4b.sh" "wb_${WB}" adv4b-refU 8 files5 "$WB" > "$INST/driver_wb_${WB}.log" 2>&1
  # junit classname::name -> collected nodeid form is different; normalise both to "<file-stem>::<...>::<name>"
  .venv/bin/python - "$INST/wb_${WB}.declared" "$INST/run_wb_${WB}.observed" "$WB" <<'PY'
import sys
def norm_decl(n):  # loremaster/tests/test_x.py::Cls::test[p]  ->  test_x.Cls::test[p]
    path, _, rest = n.partition("::"); stem = path.rsplit("/", 1)[-1].removesuffix(".py")
    parts = rest.split("::"); return f"{stem}." + ".".join(parts[:-1]) + "::" + parts[-1] if len(parts) > 1 else f"{stem}::{parts[0]}"
def norm_obs(n):  # classname "tests.test_x.Cls" :: name  -> test_x.Cls::name
    cls, _, name = n.partition("::"); tail = cls.split(".")
    idx = max(i for i, t in enumerate(tail) if t.startswith("test_"))  if any(t.startswith("test_") for t in tail) else 0
    return ".".join(tail[idx:]) + "::" + name
declared = {norm_decl(l) for l in open(sys.argv[1]).read().split("\n") if l.strip()}
observed = {norm_obs(l) for l in open(sys.argv[2]).read().split("\n") if l.strip()}
print(f"{sys.argv[3]}: declared={len(declared)} observed={len(observed)} "
      f"UNEXPECTED-RED={sorted(observed - declared)} DECLARED-BUT-GREEN={sorted(declared - observed)}")
PY
  tail -3 "$INST/driver_wb_${WB}.log" | head -2
done
echo BATCH DONE
```

### A.6 `arith_r4b.py` — md5 `6415fb5db235cda1ba64a62a3cba3684`
```python
"""adversary-63c-i-a-r4b: replicate test_R_Q5_1[perturbed-bound]'s fixture-count loops (r4b, at 8b9eb6d) and the proposed F-2 fix.
Usage: python3 arith_r4b.py"""
def run(fixed: bool, top: int):
    bad, remainder_hits = [], []
    for birth in range(1, top + 1):
        id_bound = 3 if birth != 3 else 4
        trap = id_bound + 15; legacy = 3
        avoid = (lambda: (birth, birth - legacy, birth + id_bound)) if fixed else (lambda: (birth, birth - legacy))
        while trap in avoid(): trap += 1
        while legacy in (birth, birth - trap): legacy += 1
        counts = {id_bound, trap, legacy, trap + legacy} | ({trap - id_bound} if fixed else set())
        if birth in counts: bad.append(birth)
        if trap - id_bound == birth: remainder_hits.append((birth, id_bound, trap))
    return bad, remainder_hits
print("r4b loops, birth 1..200: self-check violations", run(False, 200)[0], "| remainder==birth at", run(False, 200)[1])
print("F-2 fixed loops, birth 1..500: violations over {shown, M, legacy, M+legacy, M-shown}", run(True, 500)[0],
      "| remainder==birth at", run(True, 500)[1])
```

### A.7 `fix_F2_test.py` — md5 `ff8211b7cf45fdab0407bf4f9ba46bbe`
```python
"""adversary-63c-i-a-r4b: the MINIMAL F-2 fix, applied to a SCRATCH copy of the contract test (never the repo).
Adds the derived REMAINDER (trap_count − id_bound) to the perturbed-bound fixture's avoid-set and self-check.
Usage: uv run --no-project python fix_F2_test.py <scratch-root>"""
import sys
from pathlib import Path
path = Path(sys.argv[1]) / "loremaster/tests/test_agent_governance_63c_i_a.py"
text = path.read_text()
for old, new in (
    ("            while trap_count in (birth_bound, birth_bound - legacy_count):\n",
     "            while trap_count in (birth_bound, birth_bound - legacy_count, birth_bound + id_bound):\n"),
    ("            fixture_counts = {id_bound, trap_count, legacy_count, trap_count + legacy_count}\n",
     "            fixture_counts = {id_bound, trap_count, legacy_count, trap_count + legacy_count, trap_count - id_bound}\n"),
):
    assert text.count(old) == 1, old
    text = text.replace(old, new)
path.write_text(text)
print("F-2 fix applied (scratch)")
```

### A.8 `fixproof_F2.sh` — md5 `7968c6a3250f96003343628275a823a7`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b: prove the minimal F-2 fixture fix (fix_F2_test.py, scratch-only) — 3 legs on the R_Q5_1 node (4 params):
#   ref U + fix     -> DECLARED 0 red   (the fix keeps a correct build green)
#   PXrem15 + fix   -> DECLARED 0 red   (the fix removes the false RED)
#   PX2 + fix       -> DECLARED 1 red: [perturbed-bound]   (the fix does NOT blind the birth leg)
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/ref
NODE="loremaster/tests/test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent"
cd "$LANE" || exit 2
while [ "$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{n++} END{print n+0}')" -ne 0 ]; do sleep 15; done
for LEG in REF PXrem15 PX2; do
  git checkout -q -f adv4b-refU && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-adversary-63c-i-a-r4b.md
  [ "$LEG" = REF ] || uv run --no-project python "$INST/my_wbs_r4b.py" "$LANE" "$LEG" >/dev/null || exit 2
  uv run --no-project python "$INST/fix_F2_test.py" "$LANE" >/dev/null || exit 2
  echo "== $LEG + F-2 fix: $(.venv/bin/python -m pytest -p no:xdist -p no:cacheprovider -q "$NODE" 2>&1 | tail -1)"
  .venv/bin/python -m pytest -p no:xdist -p no:cacheprovider -q -rf "$NODE" 2>&1 | awk '/^FAILED/{print "   " $2}'
done
git checkout -q -f adv4b-refU && git clean -fdq -e REPORT-sidecar-63c.md -e REPORT-adversary-63c-i-a-r4b.md
```

### A.9 `red_diff_r4b.py` — md5 `22401fe500e586ba37459be792e0849c`
```python
"""adversary-63c-i-a-r4b: RED@HEAD diff — r4a tests' junit (adversary-r4a red_r4a.xml, production @1705ea3) vs r4b tests' junit
(my run, production @8900094; `git diff 1705ea3 8900094 -- loremaster/loremaster lorerunes lorescribe loresigil` is EMPTY).
Usage: python red_diff_r4b.py <r4a.xml> <r4b.xml>"""
import sys, xml.etree.ElementTree as ET
def load(p):
    out = {}
    for c in ET.parse(p).iter("testcase"):
        key = f"{c.get('classname','')}::{c.get('name')}"
        out[key] = "red" if (c.find("failure") is not None or c.find("error") is not None) else ("skip" if c.find("skipped") is not None else "green")
    return out
old, new = load(sys.argv[1]), load(sys.argv[2])
turned_red = sorted(k for k in old if k in new and old[k] == "green" and new[k] == "red")
turned_green = sorted(k for k in old if k in new and old[k] == "red" and new[k] == "green")
added = sorted(k for k in new if k not in old); gone = sorted(k for k in old if k not in new)
print(f"r4a ids={len(old)} r4b ids={len(new)} | r4a reds={sum(v=='red' for v in old.values())} r4b reds={sum(v=='red' for v in new.values())}")
print(f"TURNED RED (r4a green -> r4b red): {len(turned_red)}"); [print('  ', k) for k in turned_red]
print(f"TURNED GREEN (r4a red -> r4b green): {len(turned_green)}"); [print('  ', k) for k in turned_green]
print(f"NEW ids: {len(added)} — red {sum(new[k]=='red' for k in added)}, green {sum(new[k]=='green' for k in added)}, skip {sum(new[k]=='skip' for k in added)}")
for k in added: print(f"   {new[k]:5} {k}")
print(f"GONE ids: {len(gone)}"); [print('  ', k) for k in gone]
```

### A.10 `red_at_head_r4b.sh` — md5 `5c7287a2640076372e55e36777ac5d4b`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b: RED@HEAD — r4b tests on UNBUILT production (lane head @ 8900094), 25 files, -n 8; diffed against
# adversary-r4a's red_r4a.xml (r4a tests on production @1705ea3 — byte-identical production, see §7).
set -uo pipefail
INST=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/inst
LANE=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bb3623e3-d20e-4d93-b019-24e05a5dbf84/scratchpad/head
R4A=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/bab26354-cc66-4f18-b92e-6d27fa6ff922/scratchpad/inst/red_r4a.xml
cd "$LANE" || exit 2
.venv/bin/python -c "import loremaster,pathlib; p=pathlib.Path(loremaster.__file__).resolve(); assert p.is_relative_to('$LANE'), p; print('loremaster.__file__ =', p)" || exit 2
echo "head lane at $(git rev-parse --short HEAD); dirty tracked: $(git status --porcelain | awk '!/^\?\?/' | wc -l)"
while [ "$(ps -eo comm=,args= | awk '$1 ~ /^(python|python3|pytest|uv)/ && /pytest/{n++} END{print n+0}')" -ne 0 ]; do sleep 15; done
mapfile -t TARGETS < "$INST/files5.txt"
.venv/bin/python -m pytest -n 8 -q -p no:cacheprovider --junitxml="$INST/red_r4b.xml" "${TARGETS[@]}" > "$INST/red_r4b.log" 2>&1
echo "r4b tests @HEAD: $(tail -1 "$INST/red_r4b.log")"
.venv/bin/python "$INST/red_diff_r4b.py" "$R4A" "$INST/red_r4b.xml"
```

Adversary-r4's `my_ref_build_r4.py` (md5 `3e419c7544454d632b8bbd0c460111e2`) and adversary-r4a's `my_ref_leg_r4a.py` (md5
`0058ae3c8e8e2a50e0a796459ce29ab4`) were run VERBATIM. Their text lives in `REPORT-adversary-63c-i-a-r4.md` §A.1 @ `86379a4` and
`REPORT-adversary-63c-i-a-r4a.md` §A.2 @ `94c31f8` (both md5s re-verified on my copies). Numbering note: §A.1 = my r4b leg, §A.2 = the
wrong-build driver, §A.3 = the scanner probe, §A.4 = the runner, §A.5 = the batch, §A.6 = the arithmetic, §A.7 = the F-2 fix,
§A.8 = its proof driver, §A.9 = the RED@HEAD diff, §A.10 = the RED@HEAD driver.

## VERDICT
**CONTRACT INSUFFICIENT** — on exactly ONE satisfiability defect, which the amendment-11 pre-ruling FIXES and which opens no r4c:
- **F-2 (SAT):** the pin that should exist is `test_R_Q5_1_…[perturbed-bound]` with the derived REMAINDER kept off the birth value (`fix_F2_test.py`, 2 lines, proven: ref+fix 4 passed · PXrem15+fix 4 passed · PX2+fix 1 failed). The defect it removes is a correct build (birth 15, `…15 more`) refused as restating the birth value. Verify with the SAT leg re-run (§1 runner) after the fix lands.
- **For the lead to record (SAME-FAMILY → KNOWN BOUND, text §8):** RS1srvT (ownership), FXt (fake-guard).
- **For the sidecar (NEW-CLASS):** F-1 (served sample count can be false below the cap; builder edit 6 is two-readings) · G4 (a 4th legal-witness axis by my count → amendment-11's derive-the-corpus trigger).
- Everything else r4b rules holds, measured: all five §W rows kill their named builds, both helper shapes are full-suite SAT (11486/0 ×2), RED@HEAD 0/5/22 exact, currency 20 → 11 SELF-DESTRUCT → GREEN.
