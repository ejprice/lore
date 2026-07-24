brief-base v6 read

# REPORT-audit-10d-cold — independent cold audit, packet 10-d (weak-match DISARM)

> ⚠ **ARCHIVE-CORRECTION HEADER (added by the lead at close-out, 2026-07-24).** This audit's
> verdict (**GO**) and its findings were verified and acted on. **One MECHANISM description in it
> is wrong**, corrected here because it would send the next reader to the wrong place:
> - **§9.9 says the `TeammateIdle` hook resolves `${CLAUDE_PROJECT_DIR:-.}`. It does not** — the
>   script derives its root from `BASH_SOURCE` (its own file location), which always lands in the
>   MAIN checkout. **The diagnosed symptom was exactly right** (a worktree-assigned agent's
>   committed report reads as missing) and the recommended fix shape was right; only the named
>   cause was wrong. Verified at source before fixing. **FIXED in `14a987b`** — the gate now also
>   walks `git worktree list`, pipe-tested on all branches with a before/after control.
>
> Also note §9.9/§9.10 were both numbered 9.9 in the original (an amend added the second); the
> scratch copy item is the one describing `/home/ejprice/scratch-audit-10d`.
>
> Everything else stands, including the load-bearing residual **R-11ii** (the disarm MASKS #176,
> it does not fix it) — carried into `docs/plans/v2/11-ii-floor-calibration-cutover.md`'s entry
> check so it cannot be silently inherited.

## SUMMARY BLOCK
- `brief-base v6 read` · agent `audit-10d-cold` · worktree `/home/ejprice/PycharmProjects/lore-pkt10`, branch `pkt10-floor-calibration-design`, HEAD `3b19f77` · audited 2026-07-24
- **VERDICT: GO** — the disarm does what E1 ruled, on the artifact, traced at runtime with positive controls. No wrong build I could invent survives the pins. Gates re-run independently, all green with counts.
- **DEVIATION 1 (server.py docstring): VERIFIED TRUE, with one precision correction — recommend KEEP.** The docstring IS served inside `lore_index`'s `outputSchema` (measured, §Deviation 1). But only the CLASS-level paragraph is served; the `Attributes:` block is NOT — and the one sentence the disarm actually falsified lives in that unserved half. The builder's "made two of its sentences false" is an overstatement: I count **one**.
- **FINDING A (must rule before close-out):** the spec's Exit clause *"Record in each row [#176/#179/#180] that the surface was disarmed here and by which commit"* was **not done and not disclosed**. Verified on #176: `status=open`, `provenance.events` EMPTY. §Finding A.
- **FINDING B (low, 11-ii-relevant):** the builder's production review verdicts `search.py` 791–853 **"accurate"** — that span contains the exact sentence finding #176 names verbatim as a false promise, untouched by this packet. A span-level "accurate" over a line an open finding disputes. §Finding B.
- **RESIDUAL R3 (unadjudicated served-information loss):** `lore_index` can no longer surface the stamp's `measured_file_count` / `measured_embedding_schema_fingerprint`, nor any drift warning at all — the `measured`/`stale` states are unreachable in production. Not a spec violation; never adjudicated either. §Contract-blind.
- **RESIDUAL R-11ii (the trap):** the disarm **masks** #176, it does not fix it. `_format_result`'s gate still carries no `disarmed_by_drift` term. 11-ii arming the floor by setting a value re-opens #176 the same instant.
- decisions-needed: (1) DEVIATION 1 keep-vs-revert (I recommend keep); (2) who executes the findings-row bookkeeping (Finding A); (3) whether smoke check 8's expected pre-deploy RED is acceptable (§Smoke).
- receipt POINTERS: provenance §Provenance · runtime trace §1 · note served §3 · mutation battery §4 · wrong-builds §4b · my sweep §5 · gates+counts §6 · deviation 1 §7 · contract-blind inventory §8 · residuals §9

---

## Provenance (#24 / #139 / #140 — a run whose tree you cannot name is not a run)

Worktree under audit:
```
$ cd /home/ejprice/PycharmProjects/lore-pkt10 && uv run python -c "import loremaster, loremaster.search as s; print(loremaster.__file__); print(s.__file__); print(repr(s._COSINE_WEAK_MATCH_FLOOR))"
/home/ejprice/PycharmProjects/lore-pkt10/loremaster/loremaster/__init__.py
/home/ejprice/PycharmProjects/lore-pkt10/loremaster/loremaster/search.py
None
```
Scratch copy for experiments, minted by the blessed tool (`./scripts/scratch_copy.sh`), provenance asserted by the tool itself and re-printed inside every run:
```
scratch copy READY: /home/ejprice/scratch-audit-10d
  loremaster  -> /home/ejprice/scratch-audit-10d/loremaster/loremaster/__init__.py
  loresigil   -> /home/ejprice/scratch-audit-10d/loresigil/loresigil/__init__.py
  lorescribe  -> /home/ejprice/scratch-audit-10d/lorescribe/lorescribe/__init__.py
```
Every mutation ran in the SCRATCH copy. The worktree under audit was **never mutated** — I did not edit one production file or test in it. `git status` in the worktree is clean apart from this report.

**Tool honesty (brief-base §4):** lore's index watches the MAIN checkout, not this worktree (#125), so **the entire sweep is grep** — a sanctioned fallback and the correct instrument regardless, since the corpse class here is prose and string literals with no symbol anchors. One lore call was made (`lore_findings action=get 176`, §Finding A) and it **failed on first attempt** — `SurrealDB finding query failed against 'ws://127.0.0.1:18500/rpc': no close frame received or sent` — then succeeded verbatim on retry. Transient; flagged, not chased (residual §9.6).

---

## 1. Does the disarm actually darken BOTH surfaces? — traced at RUNTIME, not read off the gate

Instrument: a probe driving the **real `SearchPipeline.search_code`** end to end (not `_format_result` in isolation), at the SHIPPED constants with **no monkeypatch anywhere**, against three candidates whose cosines (0.01 / 0.02 / 0.11) are all far below the retired 0.50649. Rendered output, verbatim:

```
--- SHIPPED (no patch) ---
[hit] '...```\ndef some_function():\n    pass\n\n```\nsim 0.01'
[hit] '...```\ndef some_function():\n    pass\n\n```\nsim 0.02'
[hit] '...```\ndef some_function():\n    pass\n\n```\nsim 0.11'
```
No `weak match`. No `no confident match`. No notice entry at all.

**POSITIVE CONTROL — same fixture, floor restored to 0.50649** (without this, the negative above is worthless):
```
--- CONTROL (floor=0.50649) ---
[hit]    '... sim 0.01\n⚠ weak match — semantic similarity 0.01 is below the 0.51 floor measured on real-query hits'
[hit]    '... sim 0.02\n⚠ weak match — semantic similarity 0.02 is below the 0.51 floor measured on real-query hits'
[hit]    '... sim 0.11\n⚠ weak match — semantic similarity 0.11 is below the 0.51 floor measured on real-query hits'
[notice] "no confident match: best hit similarity 0.11 is below the range real answers measure on this corpus (≥0.51) ..."
```
The harness demonstrably renders **both** claims. At the shipped constants it renders **neither**.

**The one mutable input, forced both ways.** `_cosine_floor_runtime_state.disarmed_by_drift` is the only runtime state either gate consults. Set to `False` and to `True`, at the shipped constants, over the same fixture: no weak claim, no verdict, in either case. So no cached/warmed state can resurrect a surface.

**Every producer of a weak-match claim, enumerated (bare grep, production tree only):**

| producer | call sites | gated by |
|---|---|---|
| `_cosine_weak_match_warning` | `search.py::SearchPipeline._format_result` — the ONLY caller | `_COSINE_WEAK_MATCH_FLOOR is not None and …` |
| `_COSINE_WEAK_MATCH_WARNING_TEMPLATE` | `search.py::_cosine_weak_match_warning` only | (as above) |
| `_COSINE_ABSENCE_VERDICT_TEMPLATE` | `search.py::_cosine_absence_verdict`, after its gate | `_COSINE_WEAK_MATCH_FLOOR is None or …disarmed_by_drift → return None` |
| `_ABSENCE_VERDICT_MARKER` | `server.py::_enforce_search_budget` — **detection**, never production of a claim | n/a |

No other path exists. Checked and cleared, each with a receipt:
- **No rendered-result cache.** Grep for cache classes/`lru_cache`/`cached_` across `loremaster/loremaster/*.py` returns only the graph resolution cache and calibration ratio cache — nothing that stores a rendered `SearchResult`.
- **No config/env override of the floor.** Zero references to `_COSINE_WEAK_MATCH_FLOOR` outside `search.py`, its tests, and docs; `LoreConfig` has no floor field.
- **The served `_INSTRUCTIONS` blob never promised the weak-match flag.** Bare grep for `weak|similarity|confiden` across `server.py`'s instructions range: no hits. So there is no teaching-prose surface left over-claiming a flag that no longer serves (this repo's #1 green-at-gate defect class — checked explicitly).

## 2. Does the SUBSTRATE stay on? (over-correction check)

Same run, same fixture: `sim 0.01` / `sim 0.02` / `sim 0.11` render on every hit. Control: mutation M2 (§4) turns it off and exactly one pin goes RED, so the substrate assertion is not passing for a fixture reason.

## 3. Is the disarm note SERVED, or merely DEFINED?

Followed to the output, twice, at two layers.

**Layer 1 — the function** (`apply_cosine_floor_drift_check`, shipped constants, no patch):
```
CosineFloorDriftStatus(state='disabled', floor=None, ..., note='weak-match confidence surfaces
disarmed pending per-instance calibration (findings #83/#176/#179/#180; packets 11-i/11-ii)
— per-hit similarity substrate remains served.')
```
**CONTROL** (float floor + matching stamp → `measured`): `note=None`. The probe can therefore see a null; the non-null above is a real observation.

**Layer 2 — the served payload.** `lore_index()` on a real `AppContext` renders `cosine_floor.state='disabled'` with that exact string in `.note` (pinned patch-free by `test_production_default_serves_the_disarm_note_through_lore_index`; independently re-run green in §6, and mutation M4 below proves the pin fires if the server drops the note).

The note's text matches E1's ruled shape at source (`docs/design/2026-07-24-floor-calibration.md` Addendum E1) word for word.

## 4. ARE THE PINS REAL? — mutation battery, re-run by me

Method: scratch copy only, `cp -a` content backup, restore + md5 verify after every mutation. Pin set = `test_search.py::TestWeakMatchDisarmedAtTheProductionDefault` (8) + `test_mcp_server.py::TestCosineFloorStatusWiring` (6) = **14**.

```
BASELINE md5 search=9e5a389939da6abcd5f6ec099586742b server=eb8253cde7763b290dc4e1b3c075268d
FINAL    md5 search=9e5a389939da6abcd5f6ec099586742b server=eb8253cde7763b290dc4e1b3c075268d
```
(byte-exact restore after all seven mutations; `RESTORE OK` printed after each)

| # | mutation | result | caught by |
|---|---|---|---|
| M0 | none (control) | **14 passed** | — |
| M1 | `_COSINE_WEAK_MATCH_FLOOR = 0.50649` (undo the disarm) | **5 failed, 9 passed** | `test_the_shipped_floor_is_none`, `test_no_per_hit_weak_flag_however_low_the_cosine`, `test_no_aggregate_absence_verdict_even_when_every_condition_holds`, `test_the_disabled_state_serves_the_disarm_note_not_a_null`, `test_production_default_serves_the_disarm_note_through_lore_index` |
| M2 | `_COSINE_SUBSTRATE_ENABLED = False` (over-correct) | **1 failed, 13 passed** | `test_the_substrate_line_still_renders` — alone |
| M3 | `_COSINE_WEAK_MATCH_FLOOR_STAMP = None` (retire the stamp early) | **1 failed, 13 passed** | `test_the_measurement_stamp_survives_the_disarm` — alone |

**All three of the builder's mutation proofs reproduce exactly** — same failure counts, same test names. The claim is verified, not relayed.

### 4b. What WRONG build would still pass? — four I invented, all die

| # | wrong build | result | caught by |
|---|---|---|---|
| M4 | **the note is defined and returned, but the SERVER drops it** (`note=None` at `_build_index_status`'s `CosineFloorStatus(...)`) — "a constant that exists but never reaches a render" | **4 failed, 10 passed** | `test_production_default_serves_the_disarm_note_through_lore_index` + the three stale-state pins |
| M5 | **half-disarm: per-hit flag dark, AGGREGATE still live** (constant stays `None`, `_cosine_absence_verdict` falls back to a hardcoded 0.50649) — the exact asymmetry the frontier asked about | **1 failed, 13 passed** | `test_no_aggregate_absence_verdict_even_when_every_condition_holds` — alone |
| M6 | **vacuous note** (`_COSINE_FLOOR_DISARMED_NOTE = "disabled"`) — passes every other pin | **1 failed, 13 passed** | `test_the_disarm_note_admits_the_condition_and_names_the_next_move` — alone |
| M7 | **disarm note served on EVERY branch**, stale included | **4 failed, 10 passed** | `test_the_disarm_note_is_not_the_drift_note` + three `TestCosineFloorStatusWiring` state pins |

Every one of the frontier's named wrong builds is caught, and M2/M3/M5/M6 are each caught by **exactly one** pin — the discrimination receipt. I could not construct a wrong build that survives from inside the suite. The one that does survive is the builder's own disclosed bound (source says `None`, deployed image patched at runtime — #139's class); smoke check 8 is its instrument, and it interrogates the artifact.

## 5. THE SWEEP — re-derived from my own greps, never from the builder's table

Patterns, bare and anchor-free: `weak match` · `weak-match` · `weak_match` · `COSINE_WEAK` · `0.50649` · `0\.506` · `absence verdict` · `absence_verdict` · `no confident match` · `cosine floor` · `cosine_floor` · `sim 0\.` · `confidence surface` · `real-query hits` · `_COSINE_FLOOR_DISARMED_NOTE`.

I did not re-derive the builder's 391-row count. My sweep is **keyed on the axis that can actually express the corpse**, which is stronger for this packet: an AST pass over every test in the repo that touches the cosine machinery, classified by whether it patches the floor — because *the corpse here is a pin that relies on the module constant being a float*.

### 5a. Tests that ASSERT a weak/absence/substrate marker and do NOT patch the floor (the corpse-capable set)

| file:line | test | verdict |
|---|---|---|
| `test_search.py:1720` | `TestCosineSubstrateLit::test_renders_the_compact_magnitude_when_cosine_is_present` — asserts `"sim 0.87" in …` | **VALID.** Asserts the substrate PRESENT; the substrate is deliberately still on. Independent of the floor. |
| `test_search.py:2555` | `TestWeakMatchDisarmedAtTheProductionDefault::test_no_per_hit_weak_flag_however_low_the_cosine` | **VALID — intended patch-free pin.** Mutation-proven (M1). |
| `test_search.py:2566` | `…::test_the_substrate_line_still_renders` | **VALID — intended patch-free pin.** Mutation-proven (M2). |
| `test_search.py:2582` | `…::test_no_aggregate_absence_verdict_even_when_every_condition_holds` | **VALID — intended patch-free pin.** Mutation-proven (M1, M5). |
| `test_mcp_server.py:5275` | `TestSearchParamsCutBudgetAndTeachingMiss::test_absence_verdict_and_elision_notice_…` — asserts `"no confident match" in kept[1].formatted` | **VALID, now dormant.** Builds the notice BY HAND and feeds `_enforce_search_budget`; never calls the verdict machinery, never reads the floor. Tests finding #71's reservation, which production can no longer trigger until 11-ii (builder disclosed this as Surfaced item 3 — confirmed). |
| `test_mcp_server.py:5334` | `…::test_absence_verdict_survives_the_at_cap_recursive_recompute` | **VALID, now dormant** — same shape, same reason. |

**No vacuous pass exists.** The dangerous shape — a test asserting the ABSENCE of a weak claim over a fixture that would have produced one pre-disarm, without patching the floor — returns **zero** hits outside the new pin class. (Such a test could not have been green at `cbf61ac` anyway; I checked the inverse case, a high-cosine fixture asserting no-flag, and it does not exist either.)

### 5b. Remaining NO-FLOOR-PATCH cosine-touching tests — per-file:line verdict, individually

| file:line | verdict |
|---|---|
| `test_search.py:758` `test_respects_k_ceiling` · `:898` `test_query_equal_to_chunk_text_ranks_it_first_at_rrf_scale` · `:997` `test_no_memory_store_is_inert` | **COSINE-AS-DATA.** Reference `vector_cosine` as a candidate field; assert nothing about any claim. |
| `test_search.py:1668` `test_no_substrate_line_regardless_of_cosine` | **VALID.** Patches `_COSINE_SUBSTRATE_ENABLED=False`, not the floor. Forced-dark substrate path. |
| `test_search.py:1732` `test_renders_nothing_extra_when_cosine_is_absent` | **VALID.** `vector_cosine=None` short-circuits before any gate. |
| `test_search.py:2246`, `:2249`, `:2253` (`TestCosineAbsencePredicate`) | **VALID/pure-fn.** `_cosine_absence_predicate` takes `floor` as an ARGUMENT; module-constant-independent. |
| `test_search.py:2276`, `:2279`, `:2284`, `:2291`, `:2301`, `:2309` (`TestCosineFloorDriftCheck`) | **VALID/pure-fn.** `_cosine_floor_drift_note` takes the stamp as an ARGUMENT. |
| `test_search.py:2546` `test_the_measurement_stamp_survives_the_disarm` | **VALID — new pin.** Mutation-proven (M3). |
| `test_search.py:2603`, `:2616` (disarm-note pins) | **VALID — new pins.** Mutation-proven (M4/M6/M7). |
| `test_search.py:2661` `test_the_retired_constants_no_longer_exist` · `:2669` `test_the_retired_functions_no_longer_exist` | **VALID.** Assert `_SEARCH_SCORE_FLOOR` / `_WEAK_MATCH_WARNING_TEMPLATE` / `_ALL_HITS_WEAK_TEMPLATE` / `_weak_match_warning` / `_all_hits_weak_notice` are **absent** — the pre-S4b retired generation, unrelated to the 10-d constants (note `_WEAK_MATCH_WARNING_TEMPLATE` ≠ `_COSINE_WEAK_MATCH_WARNING_TEMPLATE`; the latter still exists, correctly). Re-run green. |
| `test_mcp_server.py:2873` `test_production_default_serves_the_disarm_note_through_lore_index` | **VALID — the served-surface pin.** Mutation-proven (M1, M4). |
| `test_mcp_server.py:2894` `test_cosine_floor_defaults_disabled_on_a_bare_index_status_summary` | **VALID.** Pins the model's own default. See §9.5 for the one served-claim tension it exposes (unreachable in production — receipt there). |
| `test_mcp_server.py:5068`, `:5200`, `:5788`, `:5953` (budget/elision composition) | **VALID, now dormant.** Hand-built notice fixtures; gate-independent. Same class as 5a's last two rows. |
| `test_indexer_contextualized.py:399` · `test_memory_backend.py:632`, `:917` · `test_memory_cutover.py:338` · `test_surreal_fakes.py:256`, `:285`, `:351` · `test_surreal_store.py:235`, `:241`, `:430` · `loresigil/tests/test_response_validation.py:95` · `loresigil/tests/test_voyage_batch.py:1421` | **COSINE-PLUMBING, each individually read.** They carry/derive/project `vector_cosine` (or a raw embedding similarity) as DATA. None reads `_COSINE_WEAK_MATCH_FLOOR`; none asserts a claim string. |
| `scripts/test_search_score_survey.py` — all 23 cosine-touching tests | **SURVEY-TOOL.** Independently verified: `grep -rn "_COSINE_WEAK_MATCH_FLOOR" scripts/` returns **zero** hits; the survey imports `_cosine_absence_predicate` (which takes `floor` as an argument) and chooses a floor offline. Re-run: **50 passed**. |

### 5c. Targeted literal sweeps (the strings that could express the corpse)

- **`0.50649`** — 8 hits total outside `docs/` and `REPORT-*.md`. Six are `search.py`'s measurement-provenance comment block and the stamp itself (`:256`, `:271`, `:272`, `:362`, `:365`, `:368`) — kept by Scope IN, verdict **KEEP**. Two are `test_search.py:2547` (comment) and `:2552` (`assert stamp.floor == 0.50649`) — verdict **VALID**, that is the stamp-survival pin. **No test anywhere asserts the SERVING floor is a float.**
- **`real-query hits`** (the weak-match template's tail) — 3 hits: `search.py:573` (the template, **byte-identical**, Scope OUT honoured) and two dated `docs/design/` files. Verdict **KEEP** / **DOC-RULED**.
- **Templates untouched, verified from the diff, not from intent:** `git diff cbf61ac..HEAD -- search.py` filtered for any line touching `_COSINE_WEAK_MATCH_WARNING_TEMPLATE`, `_COSINE_ABSENCE_VERDICT_TEMPLATE`, `_COSINE_SUBSTRATE_TEMPLATE`, or their literal bodies → **NONE**. The ruled wording law is honoured.

## 6. Gates — re-run independently, with COUNTS

| gate | my result |
|---|---|
| `uv run pytest -n auto -q` — `test_search.py test_mcp_server.py test_retired_symbols.py test_render_seam_pins.py test_text_hygiene.py test_render.py` | **`949 passed, 3 xfailed in 113.06s`**, `EXIT=0` |
| `cd scripts && uv run pytest -q test_search_score_survey.py` | **`50 passed in 0.18s`** |
| `uv run ruff check .` | `All checks passed!` · `RUFF_EXIT=0` |
| `./scripts/typecheck.sh` @ HEAD | `Found 51 errors in 3 files (checked 149 source files)` |
| `./scripts/typecheck.sh` @ `cbf61ac` (scratch copy, 5 changed files restored to pre-packet content, `git diff --stat cbf61ac` empty for all five) | `Found 51 errors in 3 files (checked 149 source files)` |

**ZERO MYPY DELTA — verified stronger than a count match.** `diff <(grep error: BASE | sort) <(grep error: HEAD | sort)` → **empty**. The two error sets are identical **line for line**, not merely equal in cardinality.

⚠ **Correction to the lead's brief:** the 51 pre-existing errors are in `test_comms_tool.py` (42), `test_trace_telemetry.py` (6), `test_comms_promise_registry.py` (3). The brief named two comms files and said "3 comms test files" — the third is `test_trace_telemetry.py`, not a comms file. Count is right; the file list was not. Not the builder's, not 10-d's.

## 7. DEVIATION 1 — `server.py`'s `CosineFloorStatus` docstring: ground truth

**Is it genuinely served?** YES — measured, not reasoned. Built the real MCP server (`build_mcp_server`), listed tools, read `lore_index`'s `outputSchema`:
```
$defs.CosineFloorStatus.description  →  contains "packet 10-d": True
```
The full edited paragraph is present verbatim in the served schema. The builder's claim is **TRUE**.

**Three precision corrections the operator should have before deciding:**
1. **Only HALF the edit is served.** The `Attributes:` block is NOT in the schema — the served `note` property is bare (`{'anyOf': [{'type':'string'},{'type':'null'}], 'default': None, 'title': 'Note'}`), **no `description` key**. Pydantic lifts the class docstring, not the Google-style Attributes section. So hunk 2 of Deviation 1 is an ordinary internal docstring, not a served surface.
2. **"Made two of its sentences false" is an overstatement — I count ONE.** Reading `cbf61ac`'s docstring at source: the only sentence the disarm falsified is `note: A human-readable explanation, present iff ``state == "stale"``.` — and it lives in the **unserved** Attributes block. The class-level served paragraph contained nothing false; it described `stale` correctly and said nothing about `disabled`. The served hunk is therefore an *improvement* (it explains a state that is now the shipped one), not a *repair of a falsehood*.
3. **The edit is confined to docstrings — verified from the diff.** `git diff cbf61ac..HEAD -- server.py` is 17 lines, entirely inside two docstrings. No logic, no field, no default, no `model_config`, no validator. `state: str = "disabled"` and `note: … = None` are untouched.

**Is the new wording TRUE?** Yes, on every clause, each checked against measured behaviour: `state == "disabled"` IS the shipped state on every instance (§1); the per-hit flag AND the aggregate verdict ARE both dark (§1); the substrate DOES keep serving (§2); `note` DOES carry the explanation rather than a null (§3). The one tension — a *bare* `CosineFloorStatus()` renders `state="disabled"` with `note=None`, the very "never turned on" reading the sentence says can never happen — is **unreachable in production**: `grep -rn "IndexStatusSummary(" loremaster/loremaster/` returns exactly one construction (`server.py::_build_index_status`) and it always passes `cosine_floor=`. The builder's own parenthetical discloses the model default anyway.

**My recommendation: KEEP.** It is docstring-only, it is true, and it improves a genuinely served surface under the trust doctrine. But the *necessity* argument is weaker than the report states — nothing was false on the served side; the builder could equally have edited only the unserved Attributes line and stayed in scope. The operator is deciding between "correct and useful" and "strictly in scope", not between "correct" and "broken".

## 8. CONTRACT-BLIND DIFF PASS — done last, frame = *"what did the old code DO that this no longer does?"*

Enumerated from `git diff cbf61ac..HEAD` alone, then adjudicated against the SPEC (never against "the old code did it").

| # | removed / lost behaviour | adjudication |
|---|---|---|
| R1 | The per-hit weak-match flag renders on any hit below the floor | **DROPPED-DELIBERATELY-AND-CORRECTLY.** E1, verbatim. Preserved-with-pin in the inverse: `test_no_per_hit_weak_flag_however_low_the_cosine` (M1-proven). |
| R2 | The aggregate absence verdict renders | **DROPPED-DELIBERATELY-AND-CORRECTLY.** E1. Pin: `test_no_aggregate_absence_verdict_…` (M1/M5-proven). |
| R3 | `lore_index` could surface a **drift warning** (`state="stale"`, "re-measure needed: …"), and could surface the stamp's `measured_file_count` / `measured_embedding_schema_fingerprint`. Post-disarm the `measured` and `stale` states are **unreachable in production** and those two fields are always `null` on the served surface, even though the stamp still holds `214` / `b4dd657beb…`. | **DROPPED — correct, but NEVER ADJUDICATED by the packet.** Not a spec violation: the disabled branch's `measured_*=None` contract predates 10-d (the packet only made that branch reachable), and 11-i reads the stamp from CODE, not from the served status. But it is real served-information loss and the packet never named it. → **residual for 11-i/11-ii**. |
| R4 | `_cosine_floor_runtime_state.disarmed_by_drift` could become `True` | **INERT, not broken.** The disabled branch sets it `False` on every call. Finding #74 part 3's mechanism is exercised by no production path until 11-ii. Builder disclosed (Surfaced 5) — confirmed correct. |
| R5 | The finding-#71 budget reservation could fire | **INERT, not broken.** Conditional on the notice's presence; the notice can no longer be produced. Builder disclosed (Surfaced 3) — confirmed. |
| R6 | `_cosine_weak_match_warning` + `_COSINE_WEAK_MATCH_WARNING_TEMPLATE` reachable in production | **PRESERVED DELIBERATELY, now unreachable.** Scope OUT: templates go dark unchanged. Builder disclosed (Surfaced 4) — confirmed. Per the repo's *"WHEN YOU CANNOT CLOSE A HOLE, PIN IT"*, a bound pin would stop a `lore_dead_code` sweep re-litigating it; that is a scope call for the operator, and 11-ii's natural home. |
| R7 | Docstring/comment sentences deleted (5 sites) | **REPLACED WITH TRUE STATEMENTS.** Each read at source and checked against behaviour. One was falsified by this change (`present iff stale`); three were falsified by it (`the floor is measured and set by default`; `Dark while … the disabled/rollback state`); and one — see below — **was already false before the packet**. |
| — | No guard, no branch, no validation, no side effect, no error path was removed. Verified by reading all 1223 diff lines. | — |

**Positive finding — a pre-existing prose defect this packet incidentally repaired.** At `cbf61ac`, `_format_result` carried: *"the cosine substrate/weak-flag machinery — both dark (no-op) until their own gate constant is measured on"* — while `_COSINE_SUBSTRATE_ENABLED = True` **and** `_COSINE_WEAK_MATCH_FLOOR = 0.50649`, i.e. **both were LIT**. That comment was already a lie before 10-d touched it. The builder replaced it with an accurate description of the two gates deliberately disagreeing. Credit where due; also a data point for the repo's own "served/rendered English has no mechanical guard" thesis.

---

## 9. RESIDUALS

**9.1 — FINDING A (needs a ruling before close-out): the spec's findings-row bookkeeping was not done and not disclosed.**
`docs/plans/v2/10-d-weak-match-disarm.md`, final paragraph: *"Findings #176 / #179 / #180 stay OPEN … **Record in each row that the surface was disarmed here and by which commit.**"* Ground truth, `lore_findings action=get 176`:
```
[#176 open] … provenance: {'created_at': '2026-07-24T02:32:56…', 'created_by': 'lead-pkt10', 'events': []}
```
`events` is EMPTY — no disarm annotation, no commit reference. `REPORT-builder-10d.md` contains no `lore_findings` call and does not list this among its deviations or its "What I did NOT do". **Scope note:** this may legitimately be the lead's step (it sits in the same Exit block as DEPLOY, which is), but the spec assigns no owner, and a silently-unexecuted Exit clause is exactly what the scope law forbids. **I verified #176 only; I did not individually re-read #179 and #180 — the lead should confirm all three before close-out.**

**9.2 — FINDING B (low, but it becomes live at 11-ii): a span-level "accurate" verdict over a line an open finding disputes.**
The builder's §Production review states *"`search.py` … 791–853 (the absence predicate and verdict) … **accurate**"*. That span contains, at `_cosine_absence_verdict`'s docstring, the sentence:
> *"the per-hit weak-match flag/substrate line are unaffected — see their own gates below"*

which finding **#176 names verbatim** as *"a message promising a check the code does not perform (CLAUDE.md, P2 2026-07-14)"*. It is **untouched by this packet** (`git diff cbf61ac..HEAD -- search.py | grep -c unaffected` → 0), inside a docstring the builder rewrote two paragraphs above. Behaviourally harmless today — both surfaces are dark, so the promise is moot. But (a) declaring the span "accurate" is the banned wholesale-classification pattern in span form, and (b) the sentence goes live and wrong again the moment 11-ii arms the floor. **Not a blocker for this packet; it is 11-ii's inheritance.**

**9.3 — R-11ii, the trap worth writing down: the disarm MASKS #176, it does not fix it.** `_format_result`'s per-hit gate still reads `_COSINE_WEAK_MATCH_FLOOR is not None and … cosine < floor` with **no `disarmed_by_drift` term**. If 11-ii arms the surfaces by giving that constant a value, #176 returns intact and instantly. Recommend 11-ii carry an explicit pin for the per-hit drift gate rather than treating the disarm as having addressed it.

**9.4 — Report arithmetic (minor, but this repo treats it as a class).** `REPORT-builder-10d.md` §Tests says *"**4** corpse/stale sites repaired — §Sweep, Table A"*; Table A lists **5** rows. I derived the true number from the diff: **5** assertion/patch repairs (3 stamp-only patches armed in `test_mcp_server.py`, plus the two `note is None` corpse pins in `test_mcp_server.py` and `test_search.py`) **plus 2 prose corrections**. The table is right; the sentence is not.

**9.5 — Checked and cleared, recorded so it is not re-litigated:** the served sentence *"`note` carries that explanation rather than a null, so this state can never be misread as 'never turned on'"* is contradicted by a **bare** `CosineFloorStatus()` (`state="disabled"`, `note=None`). Receipt that it cannot happen in production: exactly one construction of `IndexStatusSummary` exists in `loremaster/loremaster/` (`server.py::_build_index_status`, line ~3915) and it always passes `cosine_floor=`. The other three constructions are in test files. **Not a defect — but if a second production construction is ever added, that served sentence becomes false.**

**9.6 — `lore_findings` transient failure.** First call: `SurrealDB finding query failed against 'ws://127.0.0.1:18500/rpc': no close frame received or sent`. Immediate retry succeeded. Not investigated (production store; out of my writable set). Flagging per the dogfood protocol — the lead may want a friction row if it recurs.

**9.7 — Smoke check 8 will be RED against the currently-deployed image.** It asserts `cosine_floor.state == "disabled"`, and the running container still bakes `0.50649`. That is correct by design — it *is* the deploy gate, and it is the only instrument covering the builder's disclosed residual bound (source says `None`, image could differ, #139's class). But anyone running `smoke_p8b` **before** the deploy sees a failure that is not a defect. Worth a line in the deploy note. Also: check 8 rides the `--mechanics` path, so the cheap pre-flight now carries it too.

**9.8 — Two dated `docs/design/` files describe the weak-match surface in the present tense** (`2026-07-06-weak-match-discrimination.md`, `2026-07-06-client-needs-consult.md`). The builder flagged this (Surfaced 7); I confirm it and add the sharper form: these are **indexed**, so a future agent retrieving a chunk from them gets present-tense prose about a dark surface, with no header travelling alongside the chunk to date it (brief-base §1's own warning). A one-line dated banner at the top of each would not survive chunk retrieval either — the honest fix is a dated clause *in the paragraph that makes the claim*. Operator's call; out of my writable set.

**9.9 — The `TeammateIdle` gate cannot see a worktree-assigned agent (orchestration friction, not a 10-d defect).** At my idle boundary the hook fired:
> *"idle-gate: REPORT-audit-10d-cold.md is not at the repo root."*

It is — at the root of the worktree my brief assigned me. The hook resolves `${CLAUDE_PROJECT_DIR:-.}` to the **session's main checkout** (`/home/ejprice/PycharmProjects/lore`), while every packet agent in this phase works in `/home/ejprice/PycharmProjects/lore-pkt10`. Receipt:
```
$ ls -l /home/ejprice/PycharmProjects/lore-pkt10/REPORT-audit-10d-cold.md   # 32799 bytes
$ git -C …/lore-pkt10 log --oneline -1 -- REPORT-audit-10d-cold.md          # d5345ad
$ git -C …/lore-pkt10 ls-files --error-unmatch REPORT-audit-10d-cold.md     # tracked
$ ls /home/ejprice/PycharmProjects/lore/REPORT-audit-10d-cold.md            # No such file
```
**I did not satisfy the gate**, deliberately: writing the report into the main checkout would violate this brief's explicit *"DO NOT TOUCH `/home/ejprice/PycharmProjects/lore` (main) — another agent works there."* The brief outranks the hook (brief-base precedence), and a gate that can only be satisfied by breaking the brief must be reported, not obeyed. **This will fire for every worktree-assigned agent in this phase**, and its one-shot semantics mean each one burns a nudge on a false positive — which is exactly how an instrument gets ignored (`CLAUDE.md`: *"a gate that refuses honest code is a gate that gets SWITCHED OFF"*). Fix shape, for the lead to rule: have the hook resolve the agent's actual repo root (`git rev-parse --show-toplevel` from the agent's cwd) rather than the session's project dir. Not filed as a lore friction row — it is a hooks defect, not a lore-tool weakness, and the board carries no row of mine.
**Ledger note:** my brief named no ledger task id, so per brief-base §5 I touched the board not at all — the nudge's "transition your ledger item" clause has no referent for this agent.

**9.10 — Scratch copy left on disk:** `/home/ejprice/scratch-audit-10d` (a plain directory copy, **not** a git worktree, so #134 does not apply). Its 5 changed files currently hold `cbf61ac` content from the mypy-baseline run, and my probe file is parked at `/tmp/audit10d_probe.py.keep`. Safe to delete outright; I left it in case the lead wants to re-run anything. **The worktree under audit was never mutated.**

---

## What I did NOT do
- Did not edit any production file or test in `/home/ejprice/PycharmProjects/lore-pkt10`. Did not deploy. Did not merge. Did not touch `/home/ejprice/PycharmProjects/lore`.
- Did not re-derive the builder's 391-hit sweep row-for-row; I ran my own, keyed on the corpse-capable axis (§5), and gave every hit in that axis an individual verdict.
- Did not individually re-read findings #179 and #180 (§9.1 states the scope of what I verified).
- Did not run the full suite — brief scoped me to the changed suites plus the structural/AST pins (§6).
