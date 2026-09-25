# REPORT-adversary-63c-i-a-r4b-fix — contract-adversary NARROW delta pass on the r4b-fix addendum (`8b9eb6d..10a33ef`)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done · **VERDICT: CONTRACT INSUFFICIENT — one SAT defect (F-A1), which the pre-ruling FIXES (12-line test-side fix, proven in scratch).** Class breakdown: **SAME-FAMILY 4** (fake-guard: FXtVE, FXand, FXname · ownership: RS1combo → KNOWN BOUND, lead records; texts in §8) · **SAT 1** (F-A1) · **NEW-CLASS 2** (G5 length axis, G6 punctuation axis — the witness-axis class, sampled not closed → sidecar; each has a MEASURED one-function closure, §4f) · **LIVE 0**.
- **Graded:** `10a33ef` · HEAD-at-report: `1977ca6` · DIFFERENT (2 ahead: `4dca89e`, `1977ca6` — both docs-only; `git diff --stat 10a33ef 1977ca6 -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock` EMPTY). `1977ca6` raises the lead's watchdog kill-line 12→15 GiB; my runs used the brief's 12 GiB line and never went below 28 GiB available, so no run is affected.
- **deviations:** none of substance. Declaration misses stated in §4 (all benign: extra reds on a positive-control pin; the hostile companion killed MORE than I predicted). One self-inflicted instrument no-op (an unasserted `str.replace` on my own variant catalogue) caught before any run depended on it and re-applied with an asserted anchor.
- **Packages considered:** `hypothesis` 6.168.1 (read: installed `hypothesis.target(observation, *, label="")`, `strategies.from_regex`, `configuration.set_hypothesis_home_dir`, `internal/charmap.py` + `internal/constants_ast.py` cache paths) → **replace** confirmed for the author's use; `hypothesis.target` → **replace** for G5's proposed closure (measured, §4b/§4f); G6's exhaustive single-char leg → **bespoke** (sampling measured insufficient: near-miss strategies scored 0 on `@`, §4b — an exhaustive loop over a stated alphabet is not a sampling package's job). **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none — no repo symbols added; scratch instruments pasted §A.
- **SAT (§1):** my own reference, BOTH shapes, FULL SUITE ALONE `-n 12`: U `11496 passed, 62 skipped, 3 xfailed` / C same — **0 failed each** = author. Lint: ruff + typecheck clean on both built trees (no cleanup needed). Required-green enumeration R1–R10 ALL GREEN (incl. remainder, birth-15 remainder, "legacy rows", no-N prose, births 1/2/3); R11 (a true count the admitted list omits) RED → F-A1.
- **Author's claims re-derived:** kills PXlie/PX2/G4 (`'0__'`)/RS1srvT/FXt-on-U/FXt-on-C and PXrem15 GREEN — **all CONFIRMED**, diffs empty both ways (§4a, §4d). RED@HEAD `0 turned red · 0 turned green · 13 new (2 red, 11 green) · 3 gone` — **CONFIRMED to the id** (§7). Typecheck 23 = 20 + 3 direct `lorerunes` reads, owned + honest; **11/11 SELF-DESTRUCT** on the built world (§6). Dependency rider: `hypothesis` in `[dependency-groups] dev` with pytest; `Containerfile` `uv sync --locked --all-packages` installs it; `import hypothesis` 6.168.1 in fresh `scratch_copy.sh` lanes (§6). Shared cache home: 8-way cold + 4-way warm concurrent processes, identical 400-example digests (§6, MEASURED).
- **Survivors (FULL SUITE, §4e — 4 COMBO runs, each `11496 passed`, 0 red):** Nmid (G5) · Wat/Wplus/Wtab (G6) · FXtVE · FXand · FXname · RS1combo.
- **decisions-needed:** LEAD — apply F-A1's fix (§8, verbatim block) and re-run the SAT leg; record 4 KNOWN BOUNDs (texts §8) and delete two docstring over-claims ("whatever the handler spells", "REACHED and TRUSTED"). SIDECAR — G5 (`target(len)`, one line, proven) and G6 (exhaustive single-char leg, proven; read-budget-only consequence — right-size it).
- **Receipt pointers:** §0 capability · §1 SAT + required-green table · §3 DUAL · §4 wrong builds (4a author kills · 4b generated-leg reach · 4c families · 4d fix proofs · 4e full-suite legs · 4f closure proofs) · §5 per-item conformance · §6 typecheck/yaml/rider/cache · §7 RED@HEAD · §8 findings · §A instruments · VERDICT.

## 0. Capability check (brief-base §4) — measured 2026-09-25
- Idle-gate contract written without denial: `/tmp/claude-idle-gate-lore/297217bd-cb03-409c-ac95-0eb7ca9bf74b-adversary-63c-i-a-r4b-fix.contract` = `{"artifact": "REPORT-adversary-63c-i-a-r4b-fix.md"}`. Session id = the lead's (the spawn brief lives in that session's scratchpad; the sibling contracts in that directory carry the same prefix).
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `adversary`, cadence `≤20m`).
- grep/rg hook-blocked (#473): every textual sweep here is `awk` — non-symbol textual seams (test prose, yaml, Containerfile), an honest fallback, said here.
- Store reference `docs/reference/surrealdb-31-capabilities.md`: read the banner, the six READ-THIS facts, §0–§1.8 and the section map. r4b-fix touches no DDL, no store code.
- One `rm -rf` inside a compound command was classifier-denied; I did not retry it by another deleting route (used a fresh uniquely-named directory instead).
- Standalone hypothesis probes (§A.7/§A.8/§A.9) run OUTSIDE pytest, so they bypass the conftest cache redirect: `gen_sample_probe.py` created `refC/.hypothesis/` at 16:13:06 EDT (first file mtime; the probe was written 16:12:55). Scratch only; noted so it is not mistaken for a contract leak.
- Scratch root (my session scratchpad; the brief names no location, so every instrument is pasted in §A): `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/54ee5b75-304f-4da7-94a9-0d383933e627/scratchpad`.

## 1. SATISFIABILITY — my independent reference, BOTH helper shapes, full suite ALONE (measured 2026-09-25)
**Reference (built independently of the author's lanes):** two fresh `scratch_copy.sh` lanes of `4dca89e` (production byte-identical to `10a33ef`: `git diff --stat 10a33ef 4dca89e -- loremaster lorerunes lorescribe loresigil scripts pyproject.toml uv.lock skills Containerfile` EMPTY), each + adversary-r4 `my_ref_build_r4.py` (md5 `3e419c75…`) + adversary-r4a `my_ref_leg_r4a.py` (`0058ae3c…`) + adversary-r4b `my_ref_leg_r4b.py` (`7bf387f2…`) `--prose=shown` — copied from adversary-r4b's scratch root, md5-checked against its §A, run verbatim. `--prose=shown` IS builder item 6 as amendment 13 F-1 (i) now reads (`(first {min(_REFUSAL_ID_SAMPLE_SIZE, len(ids))} of {len(ids)} ids shown)`). Lane `refU` @ `ae32b40` (uncollapsed helper) · lane `refC` @ `084d80b` (`--collapse`, direct call). `loremaster.__file__` asserted inside the lane by every run (§A.1).
**Lint cleanups:** on both built trees `uv run ruff check .` → `All checks passed!`; `./scripts/typecheck.sh` → OK on every leg (lorerunes, lorescribe, loresigil, loremaster, skills, docs/eval, scripts, shellcheck 7 .sh). No cleanup was needed beyond what the reference legs already carry, so "before" = "after" lint cleanup — one full suite per shape covers both (same as adversary-r4b and the author).
| shape | full suite `-n 12`, ALONE (tail verbatim) | RED | window · memory |
|---|---|---|---|
| **U** `refU` `ae32b40` | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 496.02s (0:08:16)` exit 0 | 0 | 15:41:21–15:49:41 EDT · 33 GiB at launch, lowest 28 |
| **C** `refC` `084d80b` | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 489.93s (0:08:09)` exit 0 | 0 | 15:49:54–15:58:10 EDT · 37 GiB at launch, lowest 30 |
= the author's `11496 passed, 62 skipped, 3 xfailed / 0 failed` on both shapes — **CONFIRMED independently.** Launch gate each run: MemAvailable ≥ 23 GiB and no other pytest in the process table (comm-anchored awk, cannot self-match); PID watchdog at < 12 GiB never fired.

**The REQUIRED-GREEN enumeration (listed BEFORE judging the admitted shape, per amendment 14's lesson), each measured on the touched files:**
| # | correct build the rulings require | where required | scope | result |
|---|---|---|---|---|
| R1 | uncollapsed helper, N = `len(shown)` prose | amendment 12 + 13 F-1 (i) | FULL suite | **GREEN** 11496/0 |
| R2 | collapsed helper, same prose | amendment 12 | FULL suite | **GREEN** 11496/0 |
| R3 | N = `len(shown)` + remainder `, {M − shown} more` (birth 10) | amendment 14 (the fix author's (B) case) | touched 3 files | **GREEN** `637 passed` |
| R4 | birth 15 + remainder (F-2's scenario) | brief / amendment 13 §W-1 | touched | **GREEN** `637 passed` |
| R5 | birth 15, no remainder | F-2 control | gov file | **GREEN** `86 passed` |
| R6 | a legacy statement: `"{L} clean legacy rows also await the migrate ({count+L} unscoped in total)"` | r4b docstring's `"3 legacy rows"` (amendment 11 MP-A2), amendment 14 admitted set | gov file | **GREEN** `86 passed` |
| R7 | R6 + remainder at birth 15 | combination of R4 + R6 | gov | **GREEN** `86 passed` |
| R8 | NO sample-size prose at all | r4b docstring "derived … **or absent**" | gov | **GREEN** `86 passed` |
| R9 | birth 1 + remainder · birth 2 + remainder · birth 3 + legacy + remainder | R-3: the builder picks the birth value | gov | **GREEN** `86 passed` each |
| R10 | arithmetic of every population, birth 1..1000 | R-3 | `arith_fix.py` (§A.2) | **0 self-check violations**; PXlie admitted where birth ≠ shown: **0** |
| R11 | a TRUE count the admitted list omits: the ALREADY-MIGRATED count (`{already} already migrated`, = 0 here) | amendment 14's stated property: *"a served number that IS a true count of something the reader can see is honest prose, whether or not I anticipated its phrasing"* | gov | **RED `2 failed, 84 passed`** — `[above-cap]` + `[perturbed-bound]` → **F-A1 (§8)** |

## 3. DUAL — my independent enumeration, then the diff
(Enumerated from `git diff 8b9eb6d 10a33ef` in my working notes BEFORE I opened the author's report; written up here after. Honest bound: the write-up post-dates my read of the author's §DUAL — m6 and m10 were in the pre-read notes; the table's wording is post-read.)
Mine, in diff order:
| # | site | change | old virtue | my adjudication |
|---|---|---|---|---|
| m1 | `test_comms_schema.py` `_LEGAL_IDENTIFIER_WITNESSES` comment | KNOWN BOUND + "FOURTH witness axis → derive" trigger DELETED; replaced by "hand-list = named controls; the generated leg is the ∀" | named the hand-list's reach | dropped-deliberately (amendment 13 §G4: the trigger fired). Tuple byte-identical (8 witnesses). |
| m2 | `test_agent_governance…::test_a_householded_joiners_re_register…` | parametrised `required-only` / `every-optional`; Control 2 now passes the SAME extras | the r4b single shape | preserved: `required-only` == the r4b call byte-for-byte; node id gains a suffix (a RE-KEY, one "gone" id). |
| m3 | `TestAgentMigrateScopeKeyed63cIA` residue code | inline block MOVED into `_integers_stated_beside_the_seeded_identifiers`; **strip order SWAPPED** (§-citations now before the full count) | the birth-value leg's residue | behaviour change inside a moved block — preserved for the birth leg (both orders strip a `§N` citation; only a count that splits a `§2.1` differs), and the swap fixes a below-cap phantom `1`. Leg-isolated proof of the birth leg: §4 PX2 (`perturbed-bound` RED). |
| m4 | same test, D5 failure message | `first {sample_size} of {count}` → `first {shown} of {count}` | none (it taught N = the constant) | re-keyed prose; assertion unchanged. |
| m5 | same test, F-2 `while` avoid-set + `fixture_counts` | widened (`+ birth + id_bound`; `+ trap − id_bound`) | the r4b guard | strictly wider; arithmetic sweep birth 1..1000 clean (§A.2). |
| m6 | same test, NEW F-1 ∀-population leg + second `legacy` guard loop | additive | — | new pin (graded §5). The new loop MUTATES `legacy_count` in `below-cap` (3 → off birth / birth−2): the `below-cap` fixture VALUE changes for births ≥ 3 — e.g. birth 5 ⇒ legacy 4. No other leg in this test keys on legacy = 3 (read). |
| m7 | `_fake_predicate_import_violations` | clause (iv) ADDED; docstring's obfuscation KNOWN BOUND replaced by "STATIC REACH — THE EFFECT LEG IS THE ∀" | the bound's text + trigger (#138) | scanner behaviour WIDENED for every consumer (the HEAD-control shape pin, both control tests) — additive-red only; HEAD control still sees the guard (RED@HEAD diff §7: 0 turned red). |
| m8 | `test_KNOWN_BOUND_an_OBFUSCATED_predicate_name_is_NOT_named` → `test_the_STATIC_allowlist_cannot_see_an_OBFUSCATED_predicate_name_the_effect_leg_does` | renamed; KNOWN-BOUND message + re-open trigger removed; assertion unchanged | the bound's red-on-close message | re-keyed (amendment 15); 2 "gone" ids (its 2 params). |
| m9 | shape-pin docstring | "Two pins" → "Three pins"; bound sentence replaced | prose | re-keyed prose. |
| m10 | `loremaster/tests/conftest.py` | NEW module-level `from hypothesis.configuration import …` + `set_hypothesis_home_dir(<tempdir>/lore-hypothesis-<uid>)` | — | NOT a deletion, but a blast-radius item the author's DUAL does not list as one: **every** `loremaster/tests` session now hard-imports `hypothesis` at conftest load (an absent package = the whole tree fails to collect, not one module). Mitigated by the rider (§6: it ships in the same group as pytest). |
| m11 | `scripts/pending_contracts.yaml` attr-defined count 4 → 7 | re-pinned | — | §6 accounting. |
| m12 | `pyproject.toml` / `uv.lock` | `hypothesis>=6.168.1` in `[dependency-groups] dev` (+`sortedcontainers`) | — | §6 rider. |

**Diff vs the author's §DUAL (rows 1–9):** AGREE on m1↔8, m2↔5, m3↔1, m4↔2, m5↔3, m8↔6, m7/m9↔7, m11↔9. The author's row 4 (birth leg KEPT, now second) is my m3/m6 read. **Mine only:** m6's `below-cap` legacy-VALUE mutation (harmless, stated) and m10 (the conftest hard import is a whole-tree dependency, not a leaf one — the author lists it as a deviation, not as a blast radius). No disagreement on any adjudication.

## 4. Wrong builds — declare-then-diff (touched 3 files, lane `refU` @ `ae32b40` unless noted, `-n 8`, 2026-09-25 15:59–16:45 EDT)
**Method.** Expected-RED ids DECLARED in `declared.py` (§A.4) BEFORE any wrong-build run, each asserted to exist in `collected_touched.txt` (`--collect-only` over the 3 touched files on `refU`: **637 ids** = author's). Observed = junit reds; diffed BOTH ways by `batch_wb.sh` (§A.5). Bodies: adversary-r4b `my_wbs_r4b.py` (md5 `2de4368c…`, verbatim) for the `r4b:` builds; `my_variants.py` (§A.3) for mine — every edit asserts its anchor occurs exactly once (#194). *(Reading note: a declared `[]` prints one empty line, so `declared=1 … declared-but-green=1` on a `[]` row is that blank line, not a miss.)*
**Declaration misses, stated (all benign, all in the conservative direction):** for every SKIP-gate NARROWING I did not declare `…never_looks_up_any_value_of_the_hostile_corpus` — it reds too because its POSITIVE CONTROL loops the legal witnesses first (read after the run: `test_agent_registry.py` `test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus`); for Wupper/Wdot/Wlead I predicted the generated hostile leg GREEN and it went RED (the companion is better than I and the author predicted — hypothesis mines string constants from the source, e.g. it drew `'SURREAL_USER'`); Wlen128/Wany red 11/10 more pins than declared (the charset-text pins and every witness).

### 4a. The author's kills — RE-DERIVED on my reference (diff EMPTY both ways)
| build | declared | observed tail | verdict |
|---|---|---|---|
| r4b:PXlie `(first 10 of 2 ids shown)` | `R_Q5_1[below-cap]` | `1 failed, 636 passed` | **KILLED** (= author) |
| r4b:PX2 (birth restated as literal 10) | `[below-cap]`,`[perturbed-bound]` | `2 failed, 635 passed` | **KILLED** |
| r4b:PXrem15 (CORRECT: birth 15 + remainder) | — | `637 passed` | **GREEN** (F-2 fixed) |
| r4b:G4 (`--`/`__` narrowing) | generated legal leg | `1 failed, 636 passed` — shrunk `'0__'` | **KILLED** (= author's `'0__'`) |
| r4b:RS1srvT (`and task_id is not None`) | `[every-optional]` | `1 failed, 636 passed` | **KILLED** |
| r4b:FXt on U (try around the alias) | effect leg `[name]`,`[session]` | `2 failed, 635 passed` | **KILLED** (clause (iv) blind, as the author measured) |

### 4b. Item 3 — the generated legs' REACH (my builds)
Legal side (SKIP gate NARROWS: skips a value the predicate accepts). "GEN" = the generated legal leg.
| build | GEN | hand-list | verdict |
|---|---|---|---|
| Ncap48 `len > 48` | **GREEN** | `[aaaa…64]` + hostile-corpus control | killed by the HAND-LIST only |
| Ncap64 `len == 64` | GREEN | same | hand-list only |
| Nlen20 `len > 20` | RED | same | GEN + hand-list |
| Ndigit / Ntrail / Nsingle | RED | `[00]` / `[a-]`,`[a_]` / `[a]` | both |
| N3sep `---`/`___` · Nmixed `-` and `_` | RED | none | **GEN only** (the ∀ working) |
| **Nmid `27 < len < 64`** | see §4d | none (the only long witness is 64) | see §4d |
**Why Ncap48 escapes GEN — MEASURED, not inferred** (`gen_sample_probe.py`, §A.7, calls the hypothesis-wrapped test methods directly with the lookup replaced by a correct-gate recorder, so it draws the exact derandomized set pytest runs): **200 distinct legal draws, max length 27; 5 draws ≥ 21, 0 ≥ 41, 0 at the 64 cap.** Axis hits: doubled sep 4 · tripled 2 · trailing 10 · all-digit 15 · single-char 32 · mixed 12. So the doubled/trailing/digit axes ARE sampled (G3/G3d/G4 closed as ruled); the LENGTH axis above 27 is in the language but not in the sample.
**Closure measured (proposal, not built into the contract):** one line in the leg — `hypothesis.target(float(len(attribution)), label="length")` (hypothesis's own targeted-PBT API) — re-drawn with the same probe: **max length 64; 92 draws ≥ 21, 65 ≥ 41, 30 at the cap; every length 21..64 present.** (Trade: tripled-sep hits 2 → 0, mixed 12 → 3; doubled/trailing/digit kept.) Package API read: `hypothesis.target(observation, *, label="")`, installed 6.168.1.

Hostile side (SKIP gate WIDENS: looks up a value the predicate rejects). "GENh" = the generated hostile companion (`st.text()` filtered).
| build | GENh | hand-list `_HOSTILE_IDENTIFIERS` | verdict |
|---|---|---|---|
| Wupper `.lower()` | RED — `'A'` | `Fixer-B` | both |
| Wdot `.→-` | RED — `'0.'` | `fixer.b` | both |
| Wlead `lstrip("-_")` | RED — `'_0'` | `-fixer`,`_fixer` | both |
| Wstrip `.strip()` | RED — `'0\x85'` | `fixer-b\n` | both |
| Wascii NFKD→ASCII | RED — `'à'` | none | **GENh only** |
| Wany `len > 0` | RED | all | both |
| Wlen128 `{0,127}` | GREEN | `'z'*65` (+ the charset-text ONE-spelling pin) | hand-list only |
| Wspace ` →-` | GREEN | `fixer b` | **hand-list only** |
| Wnl `rstrip("\n")` | GREEN | `fixer-b\n` | **hand-list only** |
| **Wat `@→-`** | GREEN | none | **touched-scope SURVIVOR** → §4d |
| **Wplus `+→-`** | GREEN | none | **touched-scope SURVIVOR** → §4d |
| **Wtab `\t→-`** | GREEN | none | **touched-scope SURVIVOR** → §4d |
**The author's candidate door 1, MEASURED:** the companion does draw near-misses (`near`: of its 200 draws, 29 ASCII-only, 35 one substitution away from legal, 83 with an uppercase ASCII letter — `gen_sample_probe.py`), so it kills uppercase/dot/leading-separator/Unicode-fold widenings on its own. It does NOT kill a widening keyed on ONE specific ASCII punctuation character that no hand-list witness carries (`@`, `+`, tab). A near-miss strategy (THE pattern's language × one substituted/inserted character, `near_miss_probe.py` §A.8) does not reliably close it either: with `st.characters()` it scores Wat 0 / Wplus 0 / Wtab 0 / Wspace 0; with an ASCII alphabet Wat 0 / Wplus 2 / Wtab 0 / Wspace 7 — sampling cannot promise one specific character in 200 draws. The deterministic closure is exhaustive, not sampled: ∀ single character `c` of a stated alphabet (e.g. ASCII 0–127, 128 values), `f"a{c}b"` / `f"{c}a"` / `f"a{c}"` that the predicate rejects is never looked up — ≤ 384 pure in-memory spy calls, derived from the predicate, no hand-list.

### 4c. Items 4 and 5 — ownership and fake-guard families (my builds)
| build (U unless noted) | what it does | declared | observed | verdict |
|---|---|---|---|---|
| RS1model | takeover `and model is not None` | `[every-optional]` | `1 failed, 636 passed` | KILLED |
| **RS1combo** | takeover `and task_id is not None and model is None` — a point of the 2⁴ argument lattice neither param visits | `[]` | `637 passed` | **touched-scope SURVIVOR** → §4d |
| FXsupp | `contextlib.suppress(Exception)` around the call (no `ast.Try` anywhere) | effect `[name]`,`[session]` | `2 failed, 635 passed` | KILLED by the effect leg (static twins blind) |
| FXconv | `except Exception: raise AgentRegistryError(...) from error` (fail-CLOSED) | effect ×2 | `2 failed, 635 passed` | KILLED (a fail-closed conversion reds too — see F-5 note) |
| FXdisc | calls the shared predicate, DISCARDS the result, a private regex decides | sharing `[name-fake]`,`[session-fake]` | `2 failed, 635 passed` | KILLED by the r3/r4 SHARING pins, **not** by the effect leg (the stub is reached) |
| FXor | `shared(v) or private(v)` | sharing ×2 | `2 failed, 635 passed` | KILLED by the SHARING pins |
| **FXtVE** | `try: legal = identifier_decision(v)` / `except ValueError: legal = private(v)` — the handler catches a type the stub never raises | `[]` | `637 passed` | **touched-scope SURVIVOR** → §4d |
| **FXand** | `private(v) and shared(v)` — private conjunct FIRST; the stub is still reached on a legal value; the SHARING pins only ever NARROW the predicate | `[]` | `637 passed` | **touched-scope SURVIVOR** → §4d |
| **FXname** | `except Exception as e: if 'Shared' in type(e).__name__: raise; legal = private(v)` — adversarial-only | `[]` | `637 passed` | **touched-scope SURVIVOR** → §4d |

### 4d. Proofs of the proposed F-A1 fix, the collapsed shape, and the stamped-count probe (declared before running; diffs EMPTY both ways)
| build | lane | observed | reading |
|---|---|---|---|
| Vstamped — refusal adds `"no row was stamped (0 rows)"` (ruling §6's own "ZERO stamped", in digits) | refU | `2 failed, 635 passed` — `[above-cap]`,`[perturbed-bound]` | **a CORRECT build RED** — F-A1's second witness |
| Tfix2 + Vstamped · Tfix2 + Valready · Tfix2 + V0 · Tfix2 + Vb15legacy · Tfix2 + r4b:PXrem15 | refU | `637 passed` each | the fix admits every true count built |
| Tfix2 + r4b:PXlie · Tfix2 + r4b:PX2 | refU | `1 failed` `[below-cap]` · `2 failed` `[below-cap]`,`[perturbed-bound]` | the fix keeps BOTH kills |
| Tfix2 + V0 | **refC** `084d80b` | `637 passed` | fix SAT on the collapsed shape |
| FXtC (try around the DIRECT call) | refC | `3 failed` — effect `[name]`,`[session]` + the shape pin | KILLED (effect leg AND static clause (iv)) = author's FXtC |
| FXtVEC (`except ValueError`, direct call) | refC | `1 failed` — the shape pin only | KILLED on C by the STATIC twin (clause (iv)); the effect leg is blind to it (the stub's type is not caught) |
| FXandC (`private and shared`, direct call) | refC | `637 passed` | touched-scope survivor on C too |
| Nmid `27 < len < 64` | refU | `637 passed` | touched-scope survivor (full-suite leg §4e) |

## 5. Per-item conformance (amendment 13 §W 1–5 as amended by 14 and 15 — later wins)
| item | ruled requirement | what the contract does (read at `10a33ef`) | verdict |
|---|---|---|---|
| 1 F-2 | `while` guard + `trap_count − id_bound` | verbatim (`+ birth_bound + id_bound` in the avoid-set; `trap_count - id_bound` in `fixture_counts`) | **CONFORMS** — PXrem15 (birth 15 + remainder) GREEN on touched (`637 passed`, §4); arithmetic birth 1..1000 clean (§A.2). |
| 2 F-1 (am. 14 (B)) | admitted = per-population TRUE counts `{len(shown), count, count−len(shown), legacy, count+legacy}` with the birth guard; ALL FOUR populations; PXlie RED below-cap ∀ birth > 2; bound in docstring with trigger | admitted set exactly those five, computed per population; the assertion sits OUTSIDE the `perturbed-bound` branch → runs in all four; below-cap legacy guard loop; docstring carries "⚠ KNOWN BOUND (amendment 14, accepted) … RE-OPEN TRIGGER: a served refusal found stating a sample size that equals another fixture count and not `len(shown)`" | **CONFORMS to the letter; the letter under-delivers the ruled PROPERTY → F-A1 (SAT, §8)**: the ruling's property is *"every integer the refusal serves is a TRUE count of one of the fixture's sets … whether or not I anticipated its phrasing"*, but the admitted set is a HAND-LIST of five; the result's own `already_migrated` (0) and `backfilled` (0 — the ruling's "ZERO stamped") are true counts it omits. PXlie: killed at birth 10 (§4) and ∀ birth 3..1000 by arithmetic (R10). |
| 3 G4 | `from_regex(lorerunes.AGENT_NAME_PATTERN, fullmatch=True)` THE object; oracle-equality gate == predicate; `derandomize=True, max_examples=200`; hostile `st.text()` companion; dev dep in pytest's group | `_the_identity_language()` binds `identity_pattern = lorerunes.AGENT_NAME_PATTERN` and passes THE object (not `.pattern` text, not a copy); resolved at draw time via `st.deferred`; the leg asserts `lookups in ([], [attribution])` then `looked_up_once == lorerunes.is_legal_identifier(attribution)` — gate vs PREDICATE; settings exactly `derandomize=True, max_examples=200, database=None, deadline=None` | **CONFORMS to the letter; the ∀ claim over-reaches (MEASURED, §4/§8 G5):** the 200 derandomized legal draws have **max length 27** (0 ≥ 41, 0 at the 64 cap) — "cap … in its sample space by construction" is true of the SPACE, not the SAMPLE. A narrowing on 28..63-char names survives both the generated leg and the hand-list. Hostile companion: author's candidate 1 measured (§4). |
| 4 RS1srvT | a second joiner call with EVERY optional register argument set, through `AppContext.comms(action="register")` | `every-optional` = `model`, `spawned_by`, `task_id`, `cadence` — exactly the optional keyword set of `AppContext._comms_register(*, agent, session, role, model, spawned_by, task_id, cadence=None, **_ignored)` (read in the built lane); driven through `ctx.comms(action="register", …)`; Control 2 proves the shape is ACCEPTED end to end | **CONFORMS.** RS1srvT killed (§4). Two parameter points of a 2⁴ argument lattice — see RS1combo (§4). |
| 5 FXt (am. 15) | effect leg: THE shared predicate → raising stub via `patch_shared_object_everywhere` (`expect_in` lorerunes); a LEGAL register must PROPAGATE; HEAD early-return control; static twins say "static reach — the effect leg is the ∀"; obfuscation control re-labelled, bound message gone | `patch_shared_object_everywhere(monkeypatch, "is_legal_identifier", shared_predicate, _raising_stub)` — default `expect_in=("lorerunes",)` (read via `lore_get_symbol`: identity-keyed sweep, raises if the home binding is not patched — #194 evidence built in); `∀ field ∈ {name, session}`; HEAD branch registers `"fixer-b\n"` and asserts it lands; "STATIC REACH — THE EFFECT LEG IS THE ∀" present in `_fake_predicate_import_violations`, the shape pin and the clause-(iv) positive control; obfuscation control renamed, assertion unchanged, KNOWN-BOUND message removed | **CONFORMS.** FXt killed on BOTH shapes (§4). Docstring over-claims ("whatever the handler spells"; "REACHED and TRUSTED") — survivors FXtVE / FXand (§4, SAME-FAMILY). |

## 6. Typecheck 20 → 23 accounting · `pending_contracts.yaml` self-destruct · dependency rider (all measured 2026-09-25 @ `4dca89e`, production byte-identical to `10a33ef`)
**Currency, main checkout (unbuilt), `--legs typecheck,ruff`:** `typecheck RED_ADJUDICATED — 23 residual(s), owned by: packet-63c-i-a-contract-r2 · packet-63c-i-a-contract-r3` · `ruff GREEN` · pytest NOT_RUN (by design; never a bare `--currency`, #466). = author.
**The +3, derived from `./scripts/typecheck.sh` error lines (not from the yaml):** 23 errors = `test_agent_registry.py` 10 · `test_message_migrate_63b_ii_a.py` 4 · `_comms_fakes.py` 2 · one each in 7 other files. The `test_agent_registry.py` `attr-defined` set is now **7** = `is_legal_identifier` ×4 (the decision mutation pin, the MP-1 SKIP-gate leg, **NEW** `_text_the_shared_predicate_rejects`'s filter, **NEW** the generated-leg oracle) + `AGENT_NAME_PATTERN` ×3 (the two A4 MOVE pins, **NEW** `_the_identity_language`'s `from_regex`). The 3 NEW sites are exactly the three direct `lorerunes.<attr>` reads r4b-fix added (the effect leg reads via `getattr(…, None)` and adds none). **Owned** (entry `packet-63c-i-a-contract-r2`, owner = the i-a build), **honest** (the reason text's 4/3 split matches the error lines 1:1), **self-destructing** (below). Not a finding.
**On the BUILT world** (lane `refC` = my reference, collapsed shape, with the main checkout's yaml restored — `cmp` identical): `RED_ORPHANED — 11 residual(s)`, **all 11 `SELF-DESTRUCT`** (10 files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"), 0 real errors; with builder edit 2 (`bounds: []`): `typecheck GREEN` · `ruff GREEN`. **11/11 SELF-DESTRUCT confirmed** (#461).
**Dependency rider — re-derived:**
- `pyproject.toml` `[dependency-groups] dev` holds `pytest`, `pytest-asyncio`, `pytest-xdist` … and `"hypothesis>=6.168.1"` — ONE list. `[tool.uv]` sets no `default-groups` (read: only `package = false`), so uv's default (`dev`) applies.
- `Containerfile`: `RUN uv sync --locked --all-packages` — no `--no-dev`, no `--only-group`/`--no-group`. Its own comment names "the dev group (pytest, pytest-asyncio, pytest-xdist, mypy, ruff, type stubs)" as baked.
- `uv export --locked --all-packages` → `hypothesis==6.168.1`, `pytest==9.0.3`, `sortedcontainers==2.4.0`; with `--no-dev` → **none of the three**. hypothesis and pytest travel together or not at all. ✔
- Fresh `scratch_copy.sh` lanes (`refU`, `refC`, rc=0, provenance asserted by the tool): `import hypothesis` → `6.168.1` from `<scratch>/refC/.venv/lib/python3.14/site-packages/hypothesis/__init__.py`; `loremaster.__file__` = `<scratch>/refU/loremaster/loremaster/__init__.py` / `<scratch>/refC/…` (printed by every run, §A.1).
- ⚠ Observation (not a finding): `uv.lock` pins hypothesis 6.168.1 as **`cp310-abi3` native wheels** (uploaded 2026-09-23), incl. `manylinux_2_17_x86_64` — fine for `python:3.14-slim` (glibc, abi3), but the dep is no longer pure-Python, so it joins the Containerfile's "wheel-fragile members of the stack" audit list the file's own header asks to re-audit "whenever a dependency lands". Not measured in-image (no image build in my brief).
**`.hypothesis/` redirect (conftest):** after all 81 pytest sessions of this pass (incl. 6 full suites) no `.hypothesis` exists in the main checkout, `refU` or `head`; the ONE in `refC` was created 16:13:06 EDT by my standalone `gen_sample_probe.py` (it calls the test methods OUTSIDE pytest, so the conftest redirect never ran — timestamps §0), not by any pytest run. Note hypothesis writes a `.gitignore` of `*` into it, so a stray one is invisible to `git status` AND survives `git clean -fd` (`ls`: No such file). The home resolves via `tempfile.gettempdir()` — `TMPDIR=/var/tmp` on this box, hence `/var/tmp/lore-hypothesis-1000`; in-image it would be `/tmp/…` (writable), and hypothesis swallows cache-write failures anyway (author's source read, re-read by me: `internal/charmap.py` writes via `mkstemp` + `os.renames` under `except Exception`; `internal/constants_ast.py` caches by source-SHA1 filename, read failures fall back to recomputation). **Leak into other tests:** the redirect is process-global but only `loremaster/tests/conftest.py` sets it and no other test uses hypothesis; both hypothesis legs pass `database=None`. **Two concurrent sessions sharing the per-user home — MEASURED** (the author's candidate 2 was stated, not measured): `hyp_contention.py` (§A.9) — 8 processes COLD on one fresh shared home, then 4 WARM: every process succeeded and all 12 printed the SAME 400-example digest `1f1822365a19`, equal to an isolated-home control. Safe for this use. (Bound: one box, one hypothesis version; a torn-read would degrade to recomputation, never to a different example set, per the source.)

## 7. RED@HEAD — r4b-fix tests on UNBUILT production (lane `head` @ `d383bed` = `4dca89e` + untracked reports), the 3 touched files, `-n 8`
`157 failed, 477 passed, 3 errors in 62.82s` (160 reds) — = author's tail. Diffed (`red_diff_fix.py`, §A.10) against adversary-r4b's `red_r4b.xml` (r4b tests on unbuilt production @ `8900094`; `git diff --stat 8900094 4dca89e -- loremaster/loremaster lorerunes lorescribe loresigil` EMPTY), restricted to the 3 modules: r4b 627 ids / 158 reds → r4b-fix 637 ids / 160 reds. **TURNED RED 0 · TURNED GREEN 0 · NEW 13 = 2 red + 11 green · GONE 3.** The 2 new reds are the two generated legs (`AttributeError: module 'lorerunes' has no attribute 'AGENT_NAME_PATTERN'` / `'is_legal_identifier'` — right reason). The 11 new greens: tool-seam pin ×2 (GREEN at HEAD, as amendment 11 requires of row 2), effect leg ×2 (HEAD early return), clause-(iv) positives ×3, negatives ×2, static-reach control ×2. GONE 3 = the un-suffixed tool-seam id + `test_KNOWN_BOUND_an_OBFUSCATED_…[concatenated-name|joined-name]` — re-keys, matching my DUAL m2/m8. **The author's claim is CONFIRMED to the id.**

## 8. Findings, classified under the amendment-11 pre-ruling (SAT → FIXED · fake-guard / ownership family → KNOWN BOUND the lead records · NEW-CLASS → sidecar · LIVE → loud)

### F-A1 — **SAT DEFECT** (item 2): the F-1 leg refuses a correct refusal that states a TRUE count its admitted hand-list omits — F-2's exact class
- **Failing ids (on a correct build):** `test_agent_governance_63c_i_a.py::TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[above-cap]` and `[perturbed-bound]`.
- **Witnesses (two, both correct by amendment 14's own stated property):** Valready — the refusal adds `"{already} already migrated"` (the result's own `already_migrated` field; 0 in this fixture) → `2 failed, 635 passed`, message *"the refusal states [0] — not a TRUE count of any set this fixture seeds"* (a FALSE statement: 0 is the true count of scoped rows). Vstamped — the refusal adds `"no row was stamped (0 rows)"`, the ruling §6's own "ZERO rows stamped" in digits (`backfilled`, which this very test asserts `== 0`) → `2 failed, 635 passed`, same ids. Green in `below-cap`/`at-cap` only because there `count − len(shown) = 0` happens to be admitted — arithmetic alignment (CLAUDE.md FIXTURES MUST DISCRIMINATE, axis 3) doing the hiding.
- **Why SAT and not a scope quibble:** amendment 14 rules the property as *"every integer the refusal serves is a TRUE count of one of the fixture's sets … a served number that IS a true count of something the reader can see is honest prose, whether or not I anticipated its phrasing."* The pin implements a HAND-LIST of five true counts. Amendment 14's own §E names the habit this violates: *"enumerate the correct builds the brief and the prior rulings already REQUIRE to be green"* — the required list (R1–R10) is all GREEN; R11 is the ruled property's next member. The codebase's OTHER migrate refusal already states counts in exactly this idiom (`"({len(principals)} principals, {len(admins)} admins)"` in `_migrate_agent_owner`), so a builder writing counts beside the refusal is the house style, not an exotic build.
- **Minimal fix (test-side, 12 lines incl. comment — `my_variants.py` `fix_true_zero`, §A.3), inserted just before `stated_integers = …`:**
  ```python
          # adversary-r4b-fix F-A1 (SAT, F-2's class): the result's own counts are TRUE counts a correct refusal
          # may state — rows ALREADY migrated (scope set; derived from ``before``, where ``SELECT *`` omits a NONE
          # column), rows STAMPED (``result.backfilled``, asserted 0 above: the ruling's own "ZERO stamped"), and
          # the scanned total. None can be the birth value (birth >= 1; the total is count + legacy + already).
          already_migrated_count = sum(1 for row in before if row.get("scope") is not None)
          admitted_counts |= {
              already_migrated_count,
              result.backfilled,
              trap_count + legacy_count + already_migrated_count,
          }
          assert birth_bound == shown_count or birth_bound not in admitted_counts, (
              f"fixture self-check: the birth value {birth_bound} is an admitted TRUE count {sorted(admitted_counts)}"
          )
  ```
- **Proven in scratch (§4d, declared before running):** fix + Vstamped / Valready / V0 / Vb15legacy / PXrem15 → `637 passed` each (U); fix + V0 on C → `637 passed`; fix + PXlie → `1 failed [below-cap]`; fix + PX2 → `2 failed [below-cap, perturbed-bound]` — both kills kept, no birth value can enter (0 < birth; the total ≥ count).
- **Named residual the fix does NOT close (proposed as the bound line in the same docstring):** a count of a set OUTSIDE the agent table — e.g. `"(1 principal)"` — is still refused, and cannot simply be admitted: at birth 1 in `perturbed-bound` it would collide with the birth guard. Proposed docstring line: *"⚠ KNOWN BOUND (adversary-r4b-fix F-A1): the admitted set is the agent-table counts and the result's own counts; a true count of another table (principals, keeps) is refused. RE-OPEN TRIGGER: a correct refusal stating a non-agent count."*

### G5 — **NEW-CLASS → sidecar** (item 3): the generated legal leg does not SAMPLE lengths 28..64; a SKIP-gate narrowing on 28–63-char names survives the FULL suite
- **Build (Nmid):** `… or (27 < len(attribution) < 64)` at the SKIP gate. **FULL SUITE, alone, `-n 12` (in COMBO_A, §4e): `11496 passed, 62 skipped, 3 xfailed` — 0 red.** Touched alone: `637 passed`.
- **Measured cause** (`gen_sample_probe.py`): the 200 derandomized legal draws have max length **27** (0 ≥ 41, 0 at the cap). The hand-list's only long witness is exactly 64 chars, so a narrowing that spares 64 escapes both. Ncap48 is caught by the hand-list only.
- **Why neither pre-ruled family:** it is not a fake-guard (it is production code, the SKIP gate) and not ownership; it is the WITNESS-AXIS class (G1/G3/G3d/G4) that amendment 13 ruled CLOSED by derivation — its survivor lives in the derivation's SAMPLING, which the amendment's *"G1's cap … in the sample space by construction"* does not address (space ≠ sample). The pre-ruling routes it to the sidecar.
- **Measured closure (one line, the package's own API):** `hypothesis.target(float(len(attribution)), label="length")` inside the leg → max length 64, 65 draws ≥ 41, 30 at the cap (probe). Contract-level proof: §4f.
- **Prose that over-claims today** (a builder reads it as a ∀): the `_LEGAL_IDENTIFIER_WITNESSES` comment in `test_comms_schema.py` (*"every axis of the language (cap, …) is in its sample space by construction; it checks 200 derandomized examples"*) and the generated leg's docstring (*"every narrowing conjunct on an axis of the language, named or not"*).

### G6 — **NEW-CLASS → sidecar** (item 3, the author's candidate door 1, now MEASURED): widenings keyed on one ASCII punctuation character survive
- **Builds:** Wat (`@→-`), Wplus (`+→-`), Wtab (`\t→-`): each `637 passed` on touched; together in COMBO_A the FULL suite is green (and widening-only in COMBO_W, §4e, which removes Nmid's possible masking).
- **Consequence, sized honestly:** one extra registry READ per such attribution (R8's read budget) — the served traffic line cannot change (no such identity can be registered). Low importance.
- **Why not a family:** production SKIP gate, hostile side of the same witness-axis class.
- **Measured closure options:** sampling does NOT reliably close it (near-miss strategies: Wat 0 hits in 200 draws with either alphabet, §4b). Exhaustive does: ∀ ASCII `c`, the rejected one-edit neighbours `a{c}b`/`{c}a`/`a{c}` are never looked up (≤ 384 in-memory spy calls, derived from the predicate). Contract-level proof: §4f. Rigor-to-importance note for the sidecar: a one-function leg vs a read-budget-only consequence — "ship it simply or ledger it" is the operator's call.

### FXtVE / FXand / FXname — **SAME-FAMILY (fake-guard) → KNOWN BOUND** (item 5)
- **FXtVE** (`except ValueError` around the alias, private fallback): FULL SUITE green in COMBO_A. The effect leg's stub raises `_SharedDecisionReached(Exception)`, which a narrower handler does not catch; on C the static clause (iv) catches the same build (FXtVEC `1 failed`), on U nothing does.
- **FXand** (`private(v) and shared(v)`): §4e COMBO_B. The stub IS reached on a legal value (the private conjunct passes first), and the r3/r4 SHARING pins only ever NARROW the predicate (`lambda value: value != target and shared_predicate(value)`), so a private conjunct that is stricter-or-equal is invisible. Sharing is proven by mutation in ONE direction only.
- **FXname** (swallow all except a type whose name contains `Shared`): §4e COMBO_C. Adversarial-only (keys on the test's sentinel name).
- **Proposed bound line** (carrier: the effect leg's docstring, per amendment 13's carrier rule): *"⚠ KNOWN BOUND (adversary-r4b-fix, fake-guard family): this leg observes that the shared decision is REACHED and that ITS exception propagates; it does not observe a handler for a type the stub does not raise (FXtVE: `except ValueError`), a private conjunct evaluated before a reached predicate (FXand), or a handler keyed on this sentinel's name (FXname). The SHARING pins mutate the predicate in the NARROWING direction only. RE-OPEN TRIGGER: a fake found consulting any rule besides `is_legal_identifier`."* **And the docstring's two over-claims go:** *"whatever the handler spells"* (FXtVE falsifies it) and amendment 15's *"REACHED and TRUSTED"* (FXdisc is reached, not trusted — killed only by the SHARING pins, §4c).
- **Cheaper-than-the-bound closure, for the lead's judgement (amendment 13's precedent):** a WIDENING leg in the SHARING pin (patch the predicate to ACCEPT one hostile value; the fake must admit it) would kill FXand on both shapes; a stub sentinel subclassing `ValueError, TypeError, LookupError` would kill FXtVE and its common siblings. **Both UNMEASURED** (reasoned from the builds' code, not run) — not built here (brief: survivors of this family are recorded, not closed).

### RS1combo — **SAME-FAMILY (ownership) → KNOWN BOUND** (item 4)
- **Build:** takeover `and task_id is not None and model is None` — a point of the 2⁴ optional-argument lattice that neither `required-only` (all None) nor `every-optional` (all set) visits. FULL SUITE green (COMBO_A).
- **Proposed bound line** (carrier: the tool-seam pin's docstring): *"⚠ KNOWN BOUND (adversary-r4b-fix RS1combo): two points of the joiner's 2⁴ optional-argument lattice; a takeover conditioned on a MIXED argument shape survives. RE-OPEN TRIGGER: a register path found branching on an optional argument."* Cheap closure alternative: four more params, each setting exactly ONE optional argument (kills every single-argument and every `X set ∧ Y unset` condition with X's param).

### LIVE-PRODUCTION-DEFECT — none
r4b-fix is tests + a dev dependency; production is byte-identical to `8b9eb6d`. The in-image dependency path is verified by reading and `uv export` (§6), not by an image build.

### 4e. FULL-SUITE legs for every touched-scope survivor (brief: "a survivor is a survivor only if it survives the FULL suite") — lane `refU`, `-n 12`, ALONE
| run | builds applied together (independent anchors) | tail (verbatim) | RED |
|---|---|---|---|
| COMBO_A | GATEcombo (= Nmid ∨-skip + Wat + Wplus + Wtab widenings in ONE gate edit) + FXtVE + RS1combo | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 521.51s (0:08:41)` exit 0 · 16:53:50–17:02:36 EDT | **0** |
| COMBO_B | FXand | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 482.33s (0:08:02)` exit 0 · –17:10:41 | **0** |
| COMBO_C | FXname | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 536.83s (0:08:56)` exit 0 · –17:19:42 | **0** |
| COMBO_W | GATEwiden (Wat + Wplus + Wtab ONLY — removes the one possible masking in COMBO_A: Nmid's skip could hide a hostile 28–63-char witness) | `11496 passed, 62 skipped, 3 xfailed, 7 warnings in 481.33s (0:08:01)` exit 0 · 17:23:21–17:31:26 | **0** |
Interaction reasoning for COMBO_A (stated, since combining is a claim): FXtVE edits the fake, RS1combo the register path, GATEcombo the SKIP gate — three disjoint anchors; Nmid's skip cannot un-red a test of a legal 28–63-char name (it is what WOULD red it), so Nmid's survival is unmasked; the widenings' survival is the one masking risk, closed by COMBO_W.

### 4f. The two NEW-CLASS closures, PROVEN at contract level in scratch (declared in `closure_declared.txt` BEFORE running; `test_agent_registry.py`, refU, `-n 8`)
| contract edit + build | declared | observed |
|---|---|---|
| `target(len)` + correct build | none | `332 passed` |
| `target(len)` + Nmid | GL | `1 failed` — GL ✔ |
| `target(len)` + Ncap48 · + Ncap64 | GL, MW[a×64], HC | `3 failed` each — exactly those ✔ |
| single-char leg + correct build | none | `333 passed` |
| single-char leg + Wat · Wplus · Wtab | SC | `1 failed` each — SC ✔ |
| single-char leg + Wspace · Wnl | SC, HC | `2 failed` each — exactly those ✔ |
Both closures are satisfiable on the correct build and kill every build in their class that survived; all ten diffs EMPTY both ways. They are PROPOSALS for the sidecar, not contract edits (I commit nothing).

## 9. Residuals — each individually (observations that are not findings)
| # | residual | verdict |
|---|---|---|
| 1 | FXconv (a fail-CLOSED `except Exception: raise AgentRegistryError(...) from error`) is RED on the effect leg | intended by amendment 15 ("no `except` may swallow the shared decision"); no ruling REQUIRES a try in the fake, so not SAT. Stated so a future builder who writes a defensive conversion knows it is refused on purpose. |
| 2 | FXdisc (reached, result discarded) is killed only by the r3/r4 SHARING pins, not by the effect leg | the effect leg's docstring + amendment 15 say "REACHED and TRUSTED"; it observes REACHED only. Covered elsewhere today — the over-claim is §8's docstring edit. |
| 3 | The conftest's module-level `from hypothesis…` import makes hypothesis a hard dependency of the WHOLE `loremaster/tests` tree (collection fails without it), not of one module | mitigated by the rider (same group as pytest, §6). Re-open trigger: any install path that selects test deps by a narrower group than `dev`. |
| 4 | hypothesis 6.168.1 ships `cp310-abi3` NATIVE wheels | joins the Containerfile header's "wheel-fragile … re-audit whenever a dependency lands" list; not measured in-image (no image build in this brief). |
| 5 | The cache home follows `tempfile.gettempdir()` (`TMPDIR=/var/tmp` here → `/var/tmp/lore-hypothesis-1000`; `/tmp/…` in-image) | fine; the brief's `/var/tmp/lore-hypothesis-<uid>` is this host's instance of that rule, not a constant. |
| 6 | The author's candidate door 3 (F-1 message now precedes the birth-value message in `perturbed-bound`) | confirmed benign: my r4b:PX2 run reds `[perturbed-bound]` with the F-1 text first; the author's PX2iso proves the birth leg live. |
| 7 | `below-cap`'s `legacy_count` now varies with the birth value (my DUAL m6) | harmless (no leg keys on 3); stated. |

## Unrelated failures
None observed: every correct-build run in this pass (SAT full suites ×2, touched/gov variants, fix proofs, closure controls) ended 0 failed. **There are 0 failing tests unrelated to our present scope.**

## A. Instruments (pasted VERBATIM — md5 at report time; scratch root `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/54ee5b75-304f-4da7-94a9-0d383933e627/scratchpad`)
Reused verbatim, NOT re-pasted (md5-checked against their authors' §A): adversary-r4 `my_ref_build_r4.py` `3e419c7544454d632b8bbd0c460111e2` (REPORT-adversary-63c-i-a-r4.md §A.1), adversary-r4a `my_ref_leg_r4a.py` `0058ae3c8e8e2a50e0a796459ce29ab4` (REPORT-adversary-63c-i-a-r4a.md §A.2), adversary-r4b `my_ref_leg_r4b.py` `7bf387f20cee6a798d78ad127e0b522c` + `my_wbs_r4b.py` `2de4368cae455e2f39ebe3a39f9243f1` (REPORT-adversary-63c-i-a-r4b.md §A.1/§A.2 @ `60899bf`). `near_miss_probe_ascii.py` = `near_miss_probe.py` with `st.characters()` → `st.characters(codec="ascii")` (one `sed`).

### A.1 `run_lane.sh` — md5 `78e3a7f3e8d23fae29c974d4b4223cdd`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b-fix: pytest ALONE on <lane> at <base> (+ edits: my_variants.py names V*/W*, my_wbs_r4b.py names
# prefixed r4b:). Launch gate: MemAvailable >= $MINMEM GiB (23 for -n 12, 20 for -n 8) AND no other pytest process
# (python/pytest/uv comm, bracket-free awk on comm so it cannot self-match); polls 30 min, else exit 4 (blocked).
# Watchdog kills OUR pytest by PID below 12 GiB. Asserts loremaster.__file__ inside the lane.
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
  [ "$avail" -ge "$MINMEM" ] && [ "$busy" -eq 0 ] && break
  [ "$(date +%s)" -ge "$deadline" ] && { echo "BLOCKED: avail=${avail} GiB busy_pytest=${busy} after 30 min"; exit 4; }
  sleep 20
done
echo "label=$LABEL base=$BASE edits=${*:-none} scope=$SCOPE -n $NPROC; dirty=$(git status --porcelain | wc -l); avail ${avail} GiB; $(date '+%F %T')"
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
git checkout -q -f "$BASE" && git clean -fdq
```

### A.2 `arith_fix.py` — md5 `31ed2fb88776160c492acf185782936e`
```python
"""adversary-63c-i-a-r4b-fix: replicate test_R_Q5_1's fixture arithmetic at 10a33ef for birth 1..N, every population.
Checks: (a) the fixture self-checks never fire; (b) every stated count of the REQUIRED correct prose shapes is admitted;
(c) the birth-value leg (perturbed-bound only) never sees a TRUE count equal to birth; (d) PXlie ('first {birth}')
is RED (birth not admitted) exactly where birth != shown.  Usage: python3 arith_fix.py [N]"""
import sys
N = int(sys.argv[1]) if len(sys.argv) > 1 else 500
problems, pxlie_survives = [], []
for birth in range(1, N + 1):
    for pop in ("below-cap", "at-cap", "above-cap", "perturbed-bound"):
        id_bound = birth
        if pop == "perturbed-bound":
            id_bound = 3 if birth != 3 else 4
        trap = {"below-cap": 2, "at-cap": id_bound, "above-cap": id_bound + 15, "perturbed-bound": id_bound + 15}[pop]
        legacy = 3
        if pop == "perturbed-bound":
            while trap in (birth, birth - legacy, birth + id_bound): trap += 1
            while legacy in (birth, birth - trap): legacy += 1
            fc = {id_bound, trap, legacy, trap + legacy, trap - id_bound}
            if birth in fc: problems.append((birth, pop, "F2 self-check", fc))
        shown = min(id_bound, trap)
        if birth != shown:
            while legacy in (birth, birth - trap): legacy += 1
        admitted = {shown, trap, trap - shown, legacy, trap + legacy}
        if not (birth == shown or birth not in admitted):
            problems.append((birth, pop, "F1 self-check", admitted))
        # required correct prose: shown, count, remainder, legacy, count+legacy — all admitted by construction;
        # the birth leg (perturbed-bound) must not see birth among them.
        if pop == "perturbed-bound" and birth in {shown, trap, trap - shown, legacy, trap + legacy}:
            problems.append((birth, pop, "birth leg false-RED on correct prose", admitted))
        if birth != shown and birth in admitted:
            pxlie_survives.append((birth, pop))
        # the count strip `\b{trap}\b` also erases any OTHER admitted count that equals trap — harmless; but a
        # correct count equal to birth only matters in perturbed-bound (checked above).
print(f"birth 1..{N}: problems={problems[:10]} (n={len(problems)}) | PXlie admitted where birth!=shown: {pxlie_survives[:10]} (n={len(pxlie_survives)})")
```

### A.3 `my_variants.py` — md5 `5bb7ef4ad7d1da3645606ad20bc3488a`
```python
"""adversary-63c-i-a-r4b-fix: correct-build VARIANTS (and wrong builds) applied on top of a reference lane.
Each edit asserts its anchor occurs exactly once (#194). Usage: python my_variants.py <lane> <VARIANT>"""
import sys
from pathlib import Path

ROOT, NAME = Path(sys.argv[1]), sys.argv[2]
PRINCIPALS = "loremaster/loremaster/principals.py"
REGISTRY = "loremaster/tests/_comms_fakes.py"
AGENTS = "loremaster/loremaster/agents.py"
SHOWN_ANCHOR = '                f"{len(owned_unscoped_ids)} ids shown); "\n'


def edit(rel: str, old: str, new: str) -> None:
    path = ROOT / rel
    text = path.read_text()
    assert text.count(old) == 1, f"{rel}: anchor occurs {text.count(old)} times: {old[:80]!r}"
    path.write_text(text.replace(old, new))


def birth(value: int) -> None:
    edit(PRINCIPALS, "_REFUSAL_ID_SAMPLE_SIZE = 10\n", f"_REFUSAL_ID_SAMPLE_SIZE = {value}\n")


def remainder() -> None:
    edit(PRINCIPALS, SHOWN_ANCHOR,
         '                f"{len(owned_unscoped_ids)} ids shown, '
         '{len(owned_unscoped_ids) - min(_REFUSAL_ID_SAMPLE_SIZE, len(owned_unscoped_ids))} more); "\n')


def legacy() -> None:  # "N clean legacy rows" + the unscoped total — both TRUE counts
    edit(PRINCIPALS, SHOWN_ANCHOR, SHOWN_ANCHOR +
         '                f"{unmigrated - len(owned_unscoped_ids)} clean legacy rows also await the migrate '
         '({unmigrated} unscoped in total); "\n')


def already() -> None:  # the already-migrated count — a TRUE count (0 in this fixture), not in the admitted list
    edit(PRINCIPALS, SHOWN_ANCHOR, SHOWN_ANCHOR + '                f"{already} already migrated; "\n')


def no_n() -> None:  # prose without any sample size (the r4b docstring: "derived … or absent")
    edit(PRINCIPALS,
         '                f"half-applied store (first {min(_REFUSAL_ID_SAMPLE_SIZE, len(owned_unscoped_ids))} of "\n'
         + SHOWN_ANCHOR,
         '                "half-applied store; "\n')


GOVTEST = "loremaster/tests/test_agent_governance_63c_i_a.py"


def fix_already() -> None:  # PROPOSED test fix (F-A1): the already-migrated count is a TRUE count too — admit it
    edit(GOVTEST,
         "        stated_integers = self._integers_stated_beside_the_seeded_identifiers(\n",
         "        # adversary-r4b-fix F-A1 (SAT, F-2's class): the ALREADY-MIGRATED count (rows whose scope is set —\n"
         "        # derived from ``before``; ``SELECT *`` omits a NONE column) is a TRUE count the result itself carries\n"
         "        # (``already_migrated``), and so is the scanned total. Neither can equal the birth value here (the\n"
         "        # fixture seeds no scoped row, and the total is count + legacy), so the F-1 guard is unchanged.\n"
         "        already_migrated_count = sum(1 for row in before if row.get(\"scope\") is not None)\n"
         "        admitted_counts |= {already_migrated_count, trap_count + legacy_count + already_migrated_count}\n"
         "        assert birth_bound == shown_count or birth_bound not in admitted_counts, (\n"
         "            f\"fixture self-check: the birth value {birth_bound} is an admitted TRUE count {sorted(admitted_counts)}\"\n"
         "        )\n"
         "        stated_integers = self._integers_stated_beside_the_seeded_identifiers(\n")


SERVER = "loremaster/loremaster/server.py"
GATE = "        if attribution is None or not AppContext._is_comms_charset_legal(attribution):\n"


def widen(alternative: str) -> None:  # WRONG BUILD: the SKIP gate looks up MORE than the shared predicate accepts
    edit(SERVER, GATE,
         "        if attribution is None or not (\n"
         "            AppContext._is_comms_charset_legal(attribution)\n"
         f"            or {alternative}\n"
         "        ):\n")


FAKES = "loremaster/tests/_comms_fakes.py"
FAKE_DECISION = "                if not identifier_decision(value):\n"
PRIVATE = '__import__("re").fullmatch(r"[a-z0-9][a-z0-9_-]{0,63}", value) is not None'


def fake(block: str) -> None:  # WRONG BUILD in the uncollapsed fake: replace the one decision line by ``block``
    edit(FAKES, FAKE_DECISION, block + "                if not legal:\n")


def narrow(extra: str) -> None:  # WRONG BUILD: the SKIP gate skips a value the shared predicate ACCEPTS
    edit(SERVER, GATE,
         "        if attribution is None or not AppContext._is_comms_charset_legal(attribution) or (\n"
         f"            {extra}\n"
         "        ):\n")


def tool_takeover(extra_condition: str) -> None:  # adversary-r4b my_wbs_r4b.py's body, verbatim, condition varied
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


def fix_true_zero() -> None:  # PROPOSED test fix v2 (F-A1): admit the already-migrated AND the stamped counts
    edit(GOVTEST,
         "        stated_integers = self._integers_stated_beside_the_seeded_identifiers(\n",
         "        # adversary-r4b-fix F-A1 (SAT, F-2's class): the result's own counts are TRUE counts a correct refusal\n"
         "        # may state — rows ALREADY migrated (scope set; derived from ``before``, where ``SELECT *`` omits a NONE\n"
         "        # column), rows STAMPED (``result.backfilled``, asserted 0 above: the ruling's own \"ZERO stamped\"), and\n"
         "        # the scanned total. None can be the birth value (birth >= 1; the total is count + legacy + already).\n"
         "        already_migrated_count = sum(1 for row in before if row.get(\"scope\") is not None)\n"
         "        admitted_counts |= {\n"
         "            already_migrated_count,\n"
         "            result.backfilled,\n"
         "            trap_count + legacy_count + already_migrated_count,\n"
         "        }\n"
         "        assert birth_bound == shown_count or birth_bound not in admitted_counts, (\n"
         "            f\"fixture self-check: the birth value {birth_bound} is an admitted TRUE count {sorted(admitted_counts)}\"\n"
         "        )\n"
         "        stated_integers = self._integers_stated_beside_the_seeded_identifiers(\n")


def stamped() -> None:  # the ruling's own phrase ("ZERO rows stamped", §6) in digits — a TRUE count (backfilled = 0)
    edit(PRINCIPALS, SHOWN_ANCHOR, SHOWN_ANCHOR + '                "no row was stamped (0 rows); "\n')


FAKE_DECISION_C = "            if not is_legal_identifier(value):\n"


def fake_c(block: str) -> None:  # WRONG BUILD in the COLLAPSED fake (direct call)
    edit(FAKES, FAKE_DECISION_C, block + "            if not legal:\n")


REGTEST = "loremaster/tests/test_agent_registry.py"


def target_length() -> None:  # PROPOSED closure (G5): hypothesis targeted PBT drives the legal draws toward the cap
    edit(REGTEST,
         "        import lorerunes\n\n        lookups = asyncio.run(_traffic_line_lookups(attribution))\n",
         "        import lorerunes\n        from hypothesis import target\n\n"
         "        target(float(len(attribution)), label=\"length\")\n"
         "        lookups = asyncio.run(_traffic_line_lookups(attribution))\n")


def single_char_leg() -> None:  # PROPOSED closure (W-punct): EXHAUSTIVE one-character neighbourhood over ASCII
    path = ROOT / REGTEST
    text = path.read_text()
    assert "test_ADV_single_char_neighbourhood" not in text
    path.write_text(text + """

async def test_ADV_single_char_neighbourhood_the_predicate_rejects_is_never_looked_up() -> None:
    \"\"\"adversary-r4b-fix proposal: ∀ ASCII character c, every one-edit neighbour of a legal witness the SHARED
    predicate rejects (a{c}b, {c}a, a{c}) is never looked up — exhaustive over a STATED alphabet, derived from the
    predicate, no hand-list. POSITIVE CONTROL: the legal neighbours ARE looked up once.\"\"\"
    import lorerunes

    looked_up: dict[str, list[str]] = {}
    legal_seen = 0
    for code in range(128):
        character = chr(code)
        for value in (f"a{character}b", f"{character}a", f"a{character}"):
            lookups = await _traffic_line_lookups(value)
            if lorerunes.is_legal_identifier(value):
                legal_seen += 1
                assert lookups == [value], f"CONTROL: legal {value!r} not looked up once: {lookups!r}"
            elif lookups:
                looked_up[value] = lookups
    assert legal_seen > 0, "CONTROL: no legal neighbour was generated"
    assert not looked_up, f"the SKIP gate looked up one-edit neighbours the predicate rejects: {looked_up!r}"
""")


VARIANTS = {
    # widening-only COMBO (no narrowing, so a hostile 28..63-char witness cannot be masked by Nmid's skip)
    "GATEwiden": lambda: edit(SERVER, GATE,
        "        if attribution is None or not (\n"
        "            AppContext._is_comms_charset_legal(attribution)\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"@\", \"-\"))\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"+\", \"-\"))\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"\\t\", \"-\"))\n"
        "        ):\n"),
    "Tgen_target": target_length,
    "Tsinglechar": single_char_leg,
    # COMBO gate: every touched-scope-surviving GATE build at once (one anchor, so they cannot be stacked separately)
    "GATEcombo": lambda: edit(SERVER, GATE,
        "        if attribution is None or not (\n"
        "            AppContext._is_comms_charset_legal(attribution)\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"@\", \"-\"))\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"+\", \"-\"))\n"
        "            or AppContext._is_comms_charset_legal(attribution.replace(\"\\t\", \"-\"))\n"
        "        ) or (27 < len(attribution) < 64):\n"),
    "Nmid": lambda: narrow("27 < len(attribution) < 64"),  # the lengths the generated sample never draws (max 27)
    "Tfix2": fix_true_zero,
    "Vstamped": stamped,
    "FXtC": lambda: fake_c(
        "            try:\n"
        "                legal = is_legal_identifier(value)\n"
        "            except Exception:  # noqa: BLE001\n"
        f"                legal = {PRIVATE}\n"),
    "FXtVEC": lambda: fake_c(
        "            try:\n"
        "                legal = is_legal_identifier(value)\n"
        "            except ValueError:\n"
        f"                legal = {PRIVATE}\n"),
    "FXandC": lambda: fake_c(f"            legal = ({PRIVATE}) and is_legal_identifier(value)\n"),
    "RS1combo": lambda: tool_takeover(" and task_id is not None and model is None"),
    "RS1model": lambda: tool_takeover(" and model is not None"),
    "Ncap48": lambda: narrow("len(attribution) > 48"),
    "Ncap64": lambda: narrow("len(attribution) == 64"),
    "Ndd": lambda: narrow('"--" in attribution or "__" in attribution'),
    "Ndigit": lambda: narrow("attribution.isdigit()"),
    "Ntrail": lambda: narrow('attribution.endswith(("-", "_"))'),
    "Nsingle": lambda: narrow("len(attribution) == 1"),
    "N3sep": lambda: narrow('"---" in attribution or "___" in attribution'),
    "Nmixed": lambda: narrow('"-" in attribution and "_" in attribution'),
    "Nlen20": lambda: narrow("len(attribution) > 20"),
    "FXtVE": lambda: fake(  # try around the ALIAS, handler catches ValueError only (a type the stub never raises)
        "                try:\n"
        "                    legal = identifier_decision(value)\n"
        "                except ValueError:\n"
        f"                    legal = {PRIVATE}\n"),
    "FXdisc": lambda: fake(  # consults the shared predicate, then DISCARDS its result; a private rule decides
        "                identifier_decision(value)\n"
        f"                legal = {PRIVATE}\n"),
    "FXand": lambda: fake(f"                legal = ({PRIVATE}) and identifier_decision(value)\n"),
    "FXor": lambda: fake(f"                legal = identifier_decision(value) or ({PRIVATE})\n"),
    "FXsupp": lambda: fake(  # contextlib.suppress — no ast.Try anywhere
        f"                legal = {PRIVATE}\n"
        "                with __import__(\"contextlib\").suppress(Exception):\n"
        "                    legal = identifier_decision(value)\n"),
    "FXname": lambda: fake(  # adversarial: swallow everything EXCEPT a type whose NAME looks like the test sentinel
        "                try:\n"
        "                    legal = identifier_decision(value)\n"
        "                except Exception as error:  # noqa: BLE001\n"
        "                    if 'Shared' in type(error).__name__:\n"
        "                        raise\n"
        f"                    legal = {PRIVATE}\n"),
    "FXconv": lambda: fake(  # fail-CLOSED conversion: a predicate error becomes a refusal (no private accept)
        "                try:\n"
        "                    legal = identifier_decision(value)\n"
        "                except Exception as error:  # noqa: BLE001\n"
        "                    raise AgentRegistryError('fake register: predicate failed') from error\n"),
    "Wupper": lambda: widen("AppContext._is_comms_charset_legal(attribution.lower())"),
    "Wdot": lambda: widen('AppContext._is_comms_charset_legal(attribution.replace(".", "-"))'),
    "Wspace": lambda: widen('AppContext._is_comms_charset_legal(attribution.replace(" ", "-"))'),
    "Wlen128": lambda: widen('__import__("re").fullmatch(r"[a-z0-9][a-z0-9_-]{0,127}", attribution) is not None'),
    "Wlead": lambda: widen('AppContext._is_comms_charset_legal(attribution.lstrip("-_"))'),
    "Wnl": lambda: widen('AppContext._is_comms_charset_legal(attribution.rstrip("\\n"))'),
    "Wstrip": lambda: widen("AppContext._is_comms_charset_legal(attribution.strip())"),
    "Wat": lambda: widen('AppContext._is_comms_charset_legal(attribution.replace("@", "-"))'),
    "Wplus": lambda: widen('AppContext._is_comms_charset_legal(attribution.replace("+", "-"))'),
    "Wascii": lambda: widen(
        'AppContext._is_comms_charset_legal(__import__("unicodedata").normalize("NFKD", attribution)'
        '.encode("ascii", "ignore").decode())'),
    "Wtab": lambda: widen('AppContext._is_comms_charset_legal(attribution.replace("\\t", "-"))'),
    "Wany": lambda: widen("len(attribution) > 0"),
    "Tfix_already": fix_already,
    "V0": lambda: None,
    "Vrem": remainder,
    "Vb15rem": lambda: (birth(15), remainder()),
    "Vb15": lambda: birth(15),
    "Vlegacy": legacy,
    "Vb15legacy": lambda: (birth(15), legacy(), remainder()),
    "Vnon": no_n,
    "Vb1rem": lambda: (birth(1), remainder()),
    "Vb2rem": lambda: (birth(2), remainder()),
    "Vb3legacyrem": lambda: (birth(3), legacy(), remainder()),
    "Valready": already,
}
VARIANTS[NAME]()
print(f"variant {NAME} applied")
```

### A.4 `declared.py` — md5 `73af36b725828fd675dba494ea6d4cf3`
```python
"""adversary-63c-i-a-r4b-fix: DECLARED expected-RED node ids per wrong build, written BEFORE any wrong-build run
(2026-09-25 ~16:00 EDT), resolved against collected_touched.txt (collect-only, refU @ ae32b40, 637 ids).
Usage: python declared.py <WB> -> prints the declared ids (asserts each is collected). Guesses marked (G)."""
import sys
from pathlib import Path
INST = Path(__file__).resolve().parent
COLLECTED = set(INST.joinpath("collected_touched.txt").read_text().split())
P = "loremaster/tests/test_agent_registry.py::TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA::"
GL = P + "test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language"
GH = P + "test_the_SKIP_gate_never_looks_up_GENERATED_text_the_SHARED_predicate_rejects"
HC = P + "test_the_SKIP_gate_never_looks_up_any_value_of_the_hostile_corpus"
MW = lambda w: P + f"test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[{w}]"
R = "loremaster/tests/test_agent_registry.py::"
SH = lambda f: R + f"TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA::test_the_identifier_decision_is_the_SHARED_is_legal_identifier[{f}]"
EF = lambda f: R + f"test_the_fake_PROPAGATES_the_shared_decision_on_a_LEGAL_identity_once_the_predicate_exists[{f}]"
G = "loremaster/tests/test_agent_governance_63c_i_a.py::"
TOOL = lambda p: G + f"TestRegisterStampsTheGovernedTriple63cIA::test_a_householded_joiners_re_register_of_the_keepers_agent_leaves_its_ownership_untouched[{p}]"
RQ = lambda p: G + f"TestAgentMigrateScopeKeyed63cIA::test_R_Q5_1_the_row_precondition_refuses_an_owned_but_unscoped_agent[{p}]"
A64 = "a" * 64
DECLARED = {
    # --- re-derivations of the author's kills (adversary-r4b bodies) ---
    "r4b:PXlie": [RQ("below-cap")], "r4b:PX2": [RQ("below-cap"), RQ("perturbed-bound")], "r4b:PXrem15": [],
    "r4b:G4": [GL], "r4b:RS1srvT": [TOOL("every-optional")], "r4b:FXt": [EF("name"), EF("session")],
    # --- item 3: narrowings (legal side) — generated-leg reach ---
    "Ncap48": [MW(A64), GL],  # GL (G)
    "Ncap64": [MW(A64)],  # predict GL GREEN (a 64-char draw in 200 is unlikely) (G)
    "Ndigit": [MW("00"), GL], "Ntrail": [MW("a-"), MW("a_"), GL], "Nsingle": [MW("a"), GL],
    "N3sep": [GL],  # (G)
    "Nmixed": [GL],  # (G)
    "Nlen20": [MW(A64), GL],
    # --- item 3: widenings (hostile side) — does the GENERATED companion or only the hand-list kill? ---
    "Wupper": [HC], "Wdot": [HC], "Wspace": [HC], "Wlen128": [HC], "Wlead": [HC], "Wnl": [HC],
    "Wstrip": [HC, GH],  # GH (G)
    "Wat": [], "Wplus": [], "Wtab": [],  # predicted touched-scope SURVIVORS (no hand-list witness; st.text far from legal)
    "Wascii": [GH],  # (G) single non-ASCII chars that NFKD-fold to [a-z0-9]
    "Wany": [HC, GH],
    # --- item 5: fake-guard family vs the effect leg ---
    "FXtVE": [],  # predicted SURVIVOR: handler catches a type the stub never raises; clause (iv) blind on U
    "FXdisc": [SH("name-fake"), SH("session-fake")],  # effect leg GREEN (reached), sharing pins kill
    "FXand": [],  # predicted SURVIVOR: private-first conjunct; sharing pins only NARROW the predicate
    "FXor": [SH("name-fake"), SH("session-fake")],
    "FXsupp": [EF("name"), EF("session")],
    "FXname": [],  # predicted SURVIVOR (adversarial-only: swallows all but a sentinel-NAMED type)
    "FXconv": [EF("name"), EF("session")],
    # --- item 4: ownership family ---
    "RS1combo": [],  # predicted SURVIVOR: takeover only when task_id set AND model unset (neither param)
    "RS1model": [TOOL("every-optional")],
    # --- SAT probe (correct build) + the proposed fix ---
    "Valready": [RQ("above-cap"), RQ("perturbed-bound")],
    # --- added 16:3x EDT, AFTER gen_sample_probe.py measured the legal sample's max length (27), BEFORE any run of these ---
    "Nmid": [],  # predicted touched-scope SURVIVOR: 28..63-char legal names skipped; hand-list has only 64 (HC's control too)
    "Vstamped": [RQ("above-cap"), RQ("perturbed-bound")],  # SAT probe: the ruling's own "ZERO stamped" as '0 rows'
    "FXtC": [EF("name"), EF("session"), R + "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"],
    "FXtVEC": [R + "test_the_fakes_predicate_import_is_at_module_top_and_UNGUARDED_once_the_predicate_exists"],  # clause (iv) sees it on C
    "FXandC": [],  # predicted SURVIVOR on C too
    # --- the PROPOSED F-A1 fix (Tfix2), declared before its runs: correct builds GREEN, the lies still RED ---
    "Tfix2 Vstamped": [], "Tfix2 Valready": [], "Tfix2 V0": [], "Tfix2 Vb15legacy": [], "Tfix2 r4b:PXrem15": [],
    "Tfix2 r4b:PXlie": [RQ("below-cap")], "Tfix2 r4b:PX2": [RQ("below-cap"), RQ("perturbed-bound")],
}
if __name__ == "__main__":
    ids = DECLARED[sys.argv[1]]
    missing = [i for i in ids if i not in COLLECTED]
    assert not missing, f"declared ids not collected: {missing}"
    print("\n".join(sorted(ids)))
```

### A.5 `batch_wb.sh` — md5 `ce9a2d40c7b07b1e55411483250177ae`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b-fix: for each WB, run the touched files on refU (base ae32b40) with the WB applied, then diff
export LC_ALL=C
# OBSERVED reds against DECLARED (declared.py, written before any run) BOTH ways. Usage: batch_wb.sh WB...
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
for WB in "$@"; do
  L=$(echo "$WB" | tr ': ' '__')
  "$INST/run_lane.sh" "wb_$L" "$S/${LANE:-refU}" "${BASE:-ae32b40}" 8 touched $WB > "$INST/driver_wb_$L.log" 2>&1
  python3 "$INST/declared.py" "$WB" > "$INST/wb_$L.declared"
  tailline=$(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_wb_$L.log" | tail -1)
  unexpected=$(comm -13 "$INST/wb_$L.declared" <(python3 "$INST/norm.py" < "$INST/run_wb_$L.observed" | sort) | wc -l)
  stayed=$(comm -23 "$INST/wb_$L.declared" <(python3 "$INST/norm.py" < "$INST/run_wb_$L.observed" | sort) | wc -l)
  echo "$WB | $tailline | declared=$(wc -l < "$INST/wb_$L.declared") observed=$(wc -l < "$INST/run_wb_$L.observed") | unexpected-red=$unexpected declared-but-green=$stayed"
done
```

### A.6 `norm.py` — md5 `47ec629815281a898f1aec7ca20ad981`
```python
"""junit 'classname::name' -> pytest node id (loremaster.tests.mod[.Class]::name -> loremaster/tests/mod.py[::Class]::name)."""
import sys
for line in sys.stdin:
    classname, _, name = line.strip().partition("::")
    parts = classname.split(".")
    if parts[-1][:1].isupper():
        print(f"{'/'.join(parts[:-1])}.py::{parts[-1]}::{name}")
    else:
        print(f"{'/'.join(parts)}.py::{name}")
```

### A.7 `gen_sample_probe.py` — md5 `ce215fab989240a0e1ad231ead412f44`
```python
"""adversary-63c-i-a-r4b-fix: record the EXACT example set the two generated SKIP-gate legs draw (derandomized — the
seed derives from the test function, so the set is the one pytest runs), by calling the hypothesis-wrapped test
methods directly with ``_traffic_line_lookups`` replaced by a recorder that answers as the CORRECT gate would.
Run inside a BUILT lane: <lane>/.venv/bin/python gen_sample_probe.py <lane>. Prints length / axis coverage."""

import sys
from collections import Counter
from pathlib import Path

LANE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(LANE / "loremaster" / "tests"))

import loremaster  # noqa: E402

assert Path(loremaster.__file__).resolve().is_relative_to(LANE), loremaster.__file__
import lorerunes  # noqa: E402
import test_agent_registry as module  # noqa: E402

drawn: dict[str, list[str]] = {"legal": [], "hostile": []}
bucket = "legal"


async def _recorder(attribution: str) -> list[str]:
    drawn[bucket].append(attribution)
    return [attribution] if lorerunes.is_legal_identifier(attribution) else []


module._traffic_line_lookups = _recorder
suite = module.TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA()
suite.test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language()
bucket = "hostile"
suite.test_the_SKIP_gate_never_looks_up_GENERATED_text_the_SHARED_predicate_rejects()

legal = drawn["legal"]
lengths = Counter(len(value) for value in legal)
print(f"legal draws: {len(legal)} (distinct {len(set(legal))}); max len {max(lengths)}; "
      f"len>=21: {sum(1 for v in legal if len(v) >= 21)}; len>=41: {sum(1 for v in legal if len(v) >= 41)}; "
      f"len==64: {sum(1 for v in legal if len(v) == 64)}")
print("length histogram:", sorted(lengths.items()))
axes = {
    "doubled sep": lambda v: "--" in v or "__" in v, "tripled sep": lambda v: "---" in v or "___" in v,
    "trailing sep": lambda v: v.endswith(("-", "_")), "all digit": str.isdigit, "single char": lambda v: len(v) == 1,
    "mixed - and _": lambda v: "-" in v and "_" in v,
}
print("legal axis hits:", {name: sum(1 for v in legal if test(v)) for name, test in axes.items()})
hostile = drawn["hostile"]
near = {
    "ascii-only": lambda v: v.isascii(), "len<=64": lambda v: len(v) <= 64,
    "one char off legal (a single substitution makes it legal)": lambda v: any(
        lorerunes.is_legal_identifier(v[:i] + "a" + v[i + 1:]) for i in range(len(v))),
    "contains '@'": lambda v: "@" in v, "contains '+'": lambda v: "+" in v, "contains tab": lambda v: "\t" in v,
    "has uppercase ASCII": lambda v: any("A" <= c <= "Z" for c in v),
}
print(f"hostile draws: {len(hostile)} (distinct {len(set(hostile))})",
      {name: sum(1 for v in hostile if test(v)) for name, test in near.items()})
print("hostile sample (first 25):", [v for v in hostile[:25]])
```

### A.8 `near_miss_probe.py` — md5 `42a98907d2b8ec213d1b8fdd427539d2`
```python
"""adversary-63c-i-a-r4b-fix: would a NEAR-MISS hostile strategy — THE pattern's language with ONE position replaced
(or one character inserted / appended) by an arbitrary character, filtered to what the shared predicate REJECTS —
reach the widening gates the plain ``st.text()`` companion misses? Draws 200 derandomized examples and reports, for
each widening rule W, how many draws satisfy ``W(v) and not legal(v)`` (a draw on which the widened gate would LOOK UP a
value the predicate rejects = a kill). Run in a BUILT lane: <lane>/.venv/bin/python near_miss_probe.py <lane>"""

import sys
import unicodedata
from pathlib import Path

LANE = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(LANE / "lorerunes"))
import lorerunes  # noqa: E402

assert Path(lorerunes.__file__).resolve().is_relative_to(LANE), lorerunes.__file__
from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402

legal = lorerunes.is_legal_identifier


@st.composite
def near_miss(draw: st.DrawFn) -> str:
    base = draw(st.from_regex(lorerunes.AGENT_NAME_PATTERN, fullmatch=True))
    position = draw(st.integers(min_value=0, max_value=len(base)))
    character = draw(st.characters())
    mode = draw(st.sampled_from(("replace", "insert")))
    if mode == "replace" and position < len(base):
        return base[:position] + character + base[position + 1:]
    return base[:position] + character + base[position:]


WIDENINGS = {
    "Wat": lambda v: legal(v.replace("@", "-")), "Wplus": lambda v: legal(v.replace("+", "-")),
    "Wtab": lambda v: legal(v.replace("\t", "-")), "Wspace": lambda v: legal(v.replace(" ", "-")),
    "Wnl": lambda v: legal(v.rstrip("\n")), "Wupper": lambda v: legal(v.lower()),
    "Wdot": lambda v: legal(v.replace(".", "-")),
    "Wascii": lambda v: legal(unicodedata.normalize("NFKD", v).encode("ascii", "ignore").decode()),
}
drawn: list[str] = []


@settings(derandomize=True, max_examples=200, database=None, deadline=None)
@given(near_miss().filter(lambda v: not legal(v)))
def collect(value: str) -> None:
    drawn.append(value)


collect()
print(f"near-miss draws: {len(drawn)}; kills per widening:",
      {name: sum(1 for v in drawn if rule(v)) for name, rule in WIDENINGS.items()})
```

### A.9 `hyp_contention.py` — md5 `aa0e977218656fc569dbf70a33341768`
```python
"""adversary-63c-i-a-r4b-fix: N processes share ONE fresh hypothesis home (the conftest redirect's shape) and each
draws the SAME derandomized examples from from_regex(AGENT_NAME_PATTERN) and st.text(); prints a digest per process.
Every process must succeed and print the SAME digest. Usage: python hyp_contention.py <home> <tag>"""

import hashlib
import sys
from pathlib import Path

from hypothesis.configuration import set_hypothesis_home_dir

set_hypothesis_home_dir(Path(sys.argv[1]))

from hypothesis import given, settings  # noqa: E402
from hypothesis import strategies as st  # noqa: E402
from loremaster.agents import AGENT_NAME_PATTERN  # noqa: E402

seen: list[str] = []


@settings(derandomize=True, max_examples=200, database=None, deadline=None)
@given(st.from_regex(AGENT_NAME_PATTERN, fullmatch=True))
def legal(value: str) -> None:
    seen.append(value)


@settings(derandomize=True, max_examples=200, database=None, deadline=None)
@given(st.text())
def hostile(value: str) -> None:
    seen.append(value)


legal()
hostile()
digest = hashlib.sha1("\x00".join(seen).encode("utf-8", "surrogatepass")).hexdigest()[:12]
print(sys.argv[2], len(seen), digest)
```

### A.10 `red_diff_fix.py` — md5 `0746b4fa2233595153a20850701e537e`
```python
"""adversary-63c-i-a-r4b-fix: RED@HEAD diff — adversary-r4b's red_r4b.xml (r4b tests on UNBUILT production @8900094)
vs my run of the r4b-fix tests on UNBUILT production @4dca89e (lane `head`), RESTRICTED to the 3 touched test modules.
`git diff --stat 8900094 4dca89e -- loremaster/loremaster lorerunes lorescribe loresigil` is EMPTY (production unchanged).
Usage: python red_diff_fix.py <r4b.xml> <fix.xml>"""
import sys, xml.etree.ElementTree as ET
MODULES = ("loremaster.tests.test_agent_governance_63c_i_a", "loremaster.tests.test_agent_registry", "loremaster.tests.test_comms_schema")
def load(p):
    out = {}
    for c in ET.parse(p).iter("testcase"):
        cls = c.get("classname", "")
        if not any(cls == m or cls.startswith(m + ".") for m in MODULES):
            continue
        out[f"{cls}::{c.get('name')}"] = "red" if (c.find("failure") is not None or c.find("error") is not None) else ("skip" if c.find("skipped") is not None else "green")
    return out
old, new = load(sys.argv[1]), load(sys.argv[2])
turned_red = sorted(k for k in old if k in new and old[k] == "green" and new[k] == "red")
turned_green = sorted(k for k in old if k in new and old[k] == "red" and new[k] == "green")
added = sorted(k for k in new if k not in old); gone = sorted(k for k in old if k not in new)
print(f"r4b ids={len(old)} fix ids={len(new)} | r4b reds={sum(v=='red' for v in old.values())} fix reds={sum(v=='red' for v in new.values())}")
print(f"TURNED RED: {len(turned_red)}"); [print('  ', k) for k in turned_red]
print(f"TURNED GREEN: {len(turned_green)}"); [print('  ', k) for k in turned_green]
print(f"NEW ids: {len(added)} — red {sum(new[k]=='red' for k in added)}, green {sum(new[k]=='green' for k in added)}")
for k in added: print(f"   {new[k]:5} {k}")
print(f"GONE ids: {len(gone)}"); [print('  ', k) for k in gone]
```

### A.11 `tail_runs.sh` — md5 `9bf15cb21966e760afdb20d9175dab00`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b-fix: after batch3 — RED@HEAD (unbuilt lane `head`, touched, -n 8) then the FULL-SUITE survivor
# legs on refU (-n 12, ALONE): COMBO_A = GATEcombo + FXtVE + RS1combo · COMBO_B = FXand · COMBO_C = FXname.
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
until [ -s "$INST/batch3.log" ] && [ "$(awk '/ \| /' "$INST/batch3.log" | wc -l)" -ge 4 ]; do sleep 15; done
"$INST/run_lane.sh" redhead "$S/head" d383bed 8 touched > "$INST/driver_redhead.log" 2>&1
"$INST/run_lane.sh" COMBO_A "$S/refU" ae32b40 12 full GATEcombo FXtVE RS1combo > "$INST/driver_COMBO_A.log" 2>&1
"$INST/run_lane.sh" COMBO_B "$S/refU" ae32b40 12 full FXand > "$INST/driver_COMBO_B.log" 2>&1
"$INST/run_lane.sh" COMBO_C "$S/refU" ae32b40 12 full FXname > "$INST/driver_COMBO_C.log" 2>&1
echo TAIL_DONE > "$INST/tail_runs.done"
```

### A.12 `closure_declared.txt` — md5 `b56905f77d009b4613760580026998c1`
```text
# adversary-63c-i-a-r4b-fix: DECLARED before running (2026-09-25 ~17:00 EDT), scope = test_agent_registry.py on refU.
# GL = ...::test_the_SKIP_gate_agrees_with_the_SHARED_predicate_over_the_GENERATED_identity_language
# MW64 = ...::test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[a*64] ; HC = ...hostile_corpus ; SC = test_ADV_single_char_neighbourhood...
Tgen_target V0        -> (none)
Tgen_target Nmid      -> GL
Tgen_target Ncap48    -> GL MW64 HC
Tgen_target Ncap64    -> GL MW64 HC
Tsinglechar V0        -> (none)
Tsinglechar Wat       -> SC
Tsinglechar Wplus     -> SC
Tsinglechar Wtab      -> SC
Tsinglechar Wspace    -> SC HC
Tsinglechar Wnl       -> SC HC
```

### A.13 `closure_runs.sh` — md5 `7ae87e3dacb31dbecaabe3acd93f8253`
```bash
#!/usr/bin/env bash
# adversary-63c-i-a-r4b-fix: closure proofs (declared in closure_declared.txt BEFORE this runs), reg scope, refU, -n 8.
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
until [ -f "$INST/tail_runs.done" ]; do sleep 15; done
for SET in "Tgen_target V0" "Tgen_target Nmid" "Tgen_target Ncap48" "Tgen_target Ncap64" "Tsinglechar V0" "Tsinglechar Wat" "Tsinglechar Wplus" "Tsinglechar Wtab" "Tsinglechar Wspace" "Tsinglechar Wnl"; do
  L=$(echo "$SET" | tr ' ' '_')
  "$INST/run_lane.sh" "cl_$L" "$S/refU" ae32b40 8 reg $SET > "$INST/driver_cl_$L.log" 2>&1
  echo "$SET | $(awk '/passed|failed/ && /in [0-9.]+s/' "$INST/run_cl_$L.log" | tail -1) | RED: $(python3 "$INST/norm.py" < "$INST/run_cl_$L.observed" | sed 's#.*::##' | tr '\n' ' ')"
done > "$INST/closure_runs.log"
echo CLOSURE_DONE >> "$INST/closure_runs.log"
```

### A.14 `last_run.sh` — md5 `d5d1d64429660dfbfdd69733736577fa`
```bash
#!/usr/bin/env bash
S=$(dirname "$(dirname "$(readlink -f "$0")")"); INST=$S/inst
until awk '/CLOSURE_DONE/{f=1} END{exit !f}' "$INST/closure_runs.log" 2>/dev/null; do sleep 15; done
"$INST/run_lane.sh" COMBO_W "$S/refU" ae32b40 12 full GATEwiden > "$INST/driver_COMBO_W.log" 2>&1
echo LAST_DONE > "$INST/last_run.done"
```

## VERDICT
**CONTRACT INSUFFICIENT** — on exactly one ground, the one class the amendment-11 pre-ruling FIXES: **F-A1 (SAT)**, a correct refusal stating a TRUE count the admitted hand-list omits (`already_migrated`, `backfilled` = 0 — the ruling's own "ZERO stamped") is RED in `[above-cap]`/`[perturbed-bound]`. The fix is the 12-line block in §8, proven: every correct variant GREEN on both shapes, PXlie and PX2 still killed. Apply it and the contract is SUFFICIENT under the pre-ruling.
Everything else routes as ruled, with no new round: **SAME-FAMILY 4** (FXtVE, FXand, FXname — fake-guard; RS1combo — ownership), each a FULL-SUITE survivor, bound texts + re-open triggers in §8 for the lead to record in the carrier docstrings, plus two docstring over-claims to delete. **NEW-CLASS 2 → sidecar**: G5 (the generated legal leg never samples lengths 28–64; Nmid survives the full suite) and G6 (single-punctuation widenings survive the full suite) — the witness-axis class amendment 13 closed by derivation, surviving in the derivation's SAMPLING; each has a one-function closure MEASURED at contract level (§4f), and G6 is read-budget-only in consequence. **LIVE 0.**
Independently confirmed: SAT on both helper shapes (full suite `11496 passed, 62 skipped, 3 xfailed`, 0 failed each), all eight author kill claims, RED@HEAD to the id, the typecheck 20→23 accounting (owned, honest, 11/11 self-destruct), the dependency rider, and shared-cache safety under concurrency.
