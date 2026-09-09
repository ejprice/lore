# REPORT-builder-63b-ib-rendercov-A

STARTED 2026-09-08 — builder-63b-ib-rendercov-A (Opus 4.8)

## SUMMARY BLOCK
- brief-base v14 read · brief project v7 read
- state: **done-with-deviations** — the 10 Class-A cascades are GREEN (both modules 176 passed,
  0 failed); coverage GREW + is mutation-proven; ONE sub-point of decision (b) is a genuine
  structural FORK, flagged (not silently resolved).
- deviations:
  1. comms identity registered as `builder-63b-ib-rendercov-a` (lowercased — comms charset
     rejects the uppercase `A`); report/idle-gate keep the exact spawn name `...-A.md`.
  2. TWO drivers needed the `subject` kwarg, not one: the shared probe registry
     (`_probes()` line ~2290) AND the per-door driver `_drive_recalled_memory` (line ~478).
     Both fixed; both in the writable set. Scanned both files — no third call site.
- Packages considered: none — no mechanism specified (reused the existing `member` Subject-forge
  + the existing `_tok`/`_field_token`/`_served` harness seams; wrote no new mechanism).
- Reuse ledger: 1 new symbol (`recalled_subject`, a local forge-aware helper in `_probes()`),
  dispositioned REUSED `_governed_contract.member`. See §DRY-LEDGER.
- Graded: n/a (authored build, not a verdict) · built on HEAD 46288b6 · HEAD-at-report 46288b6 · SAME
- decisions-needed:
  1. **FORK (b) — render_subject_bound as a SEPARATE P-U driven probe is NOT cleanly achievable
     in scope** (reddens the reverse-leg / needs an 11-method universe widening = design change)
     AND is redundant (its §3.3 ii/iii coverage is already GREEN in the dedicated module; and I
     drive+guard it TRANSITIVELY, mutation-proven). Recommend Reading A. See §FORK-B.
- pointers: §RED→GREEN · §COVERAGE-GREW (mutation proof) · §OTHER-MODULES · §FORK-B · §DRY-LEDGER · KEY ANALYSIS (above)

## LOG
- STARTED: wrote idle-gate contract + this skeleton.
- brief-base v14 read; standing brief project v7 read.
- comms: registered as `builder-63b-ib-rendercov-a` (LOWERCASED — comms charset
  `^[a-z0-9...]` rejects the uppercase `A` in my spawn name). Report + idle-gate keep the
  exact spawn name `...-A.md`. Deviation, disclosed.
- RED baseline at HEAD 46288b6 (`-n0 -p no:cacheprovider`, :18000):
  **10 failed, 166 passed** — all `TypeError: AppContext._render_recalled_memories()
  missing 1 required keyword-only argument: 'subject'`. Failure list matches the brief.
- signatures read (lore_get_symbol): `AppContext.render_subject_bound(subject)` staticmethod
  (server.py:4215); `AppContext._render_recalled_memories(recalled, *, subject)` (server.py:4231);
  `render_attributed(value: object) -> Rendered` in loremaster/render.py:249.

## KEY ANALYSIS (measured, before editing)
- The `_render_probes()` registry in `test_link5_render_containment.py` is the SINGLE shared
  inventory; `test_render_slot_inventory.py` imports/derives from it (`_driven_methods()` =
  `{probe.method for probe in _render_probes()}`), which is why one broken probe lambda
  cascaded into BOTH files. So the `subject=` fix in one place clears all 10.
- The P-U candidate universe is DERIVED name-blind by `_method_interpolates_a_nonconstant`
  (f-string / `.format` / sanitise-seam). **Measured:** `render_subject_bound` is NOT a
  candidate (62 candidates, 43 driven; `stale_driven=[]`, `unclassified=[]` at HEAD) because
  it routes purely through `render_line`/`render_attributed` — the CONTAINMENT seams, which
  the universe deliberately excludes (it targets LEAK-CAPABLE methods). It is one of **11**
  AppContext methods that use a render seam but are not candidates (the other 10:
  `_comms_drain/_comms_heartbeat/_comms_register/_render_comms_await/_render_comms_await_empty/`
  `_render_comms_story/_render_comms_waiting_line/_render_fleet_status_cell/_render_story_message/`
  `_rollup_extra_sections`).
- CONSEQUENCE: adding `render_subject_bound` to `_render_probes()` as a SEPARATE probe reddens
  the reverse-leg `test_no_probe_or_out_entry_is_a_stale_non_candidate` (it would be
  `stale_driven`) UNLESS the universe derivation is widened to admit containment-seam methods
  — which pulls in all 11 (0 currently driven/OUT) = a large coverage EXPANSION (design
  decision), out of a 2-file reconciliation's scope. → this is the (b) FORK below.
- render_subject_bound's design coverage pins (§3.3 ii AST-derivation, iii hostile-fixture)
  are ALREADY implemented GREEN in the dedicated `test_memory_render_bound_63b_ib.py`
  (`TestEveryGovernedReadRenderCarriesTheBoundLine`, `TestTheBoundLineContainsForgedIds`) —
  confirmed via lore_impact (1 consumer: `_render_recalled_memories`; 19 covering tests).
- shared Subject-forge = `member(principal_id, agent_id, keeps)` in
  `loremaster/tests/_governed_contract.py` (uses `pdp.Subject`); idiom `from _governed_contract
  import member`. REUSING it (DRY §6).

## §WHAT-I-CHANGED (writable set only; server.py UNTOUCHED)
Two edits, both in `loremaster/tests/test_link5_render_containment.py`; `test_render_slot_inventory.py`
needed NO direct edit (it derives from the shared `_render_probes()` registry — one fix cleared its 4).
1. `_probes()` — added `from _governed_contract import member  # noqa: PLC0415` and a local
   `recalled_subject(forge)` helper (forge-aware forged-id `Subject` via the shared `member`;
   non-empty keep set for a non-vacuous `visible via N keep(s)` count).
2. The `_render_recalled_memories` probe (the shared registry) — each of its 3 shapes now passes
   `subject=recalled_subject(g)` (forgery token in `principal_id`/`agent_id` when `g=True`, benign
   control when `g=False`).
3. `_drive_recalled_memory` (the per-door driver behind `TestEveryRenderLayerDoorNeutralisesAForgery`)
   — now builds a fixed benign valid `Subject` via `member` and passes `subject=`; it tests the
   `recalled_memory[text]` door, so the subject is incidental and benign (control stays marker-free).

## §RED→GREEN (test store :18000, `-n0 -p no:cacheprovider`)
- RED at HEAD 46288b6 (before edits): `test_link5_render_containment.py test_render_slot_inventory.py`
  → **10 failed, 166 passed** — every failure `TypeError: AppContext._render_recalled_memories()
  missing 1 required keyword-only argument: 'subject'` (6 in link5 + 4 in slot_inventory; list matches brief).
- After edit 1+2 (probe only): 2 failed, 174 passed — surfaced the SECOND driver
  (`_drive_recalled_memory` line 478) which also called positionally.
- After edit 3: **176 passed, 0 failed** (both modules). The 10 previously-red tests are GREEN.
- Universe invariants re-checked post-fix: `stale_driven == []`, `unclassified == []`
  (the P-U forward+reverse completeness legs stay clean; render_subject_bound remains
  correctly outside the leak-capable universe).

## §COVERAGE-GREW (mutation-proven — the brief's "prove the coverage grew" ask)
render_subject_bound is now DRIVEN + GUARDED transitively via the `_render_recalled_memories`
probe (its bound line is prepended to that render's output, so the P-N net
`test_no_shape_leaks_the_forgery[_render_recalled_memories]` byte-checks the forged
`principal_id`/`agent_id`). Mutation proof (in-process monkeypatch — server.py NOT modified on disk;
restored, verified `is orig`):
- POSITIVE control (real, contained render): leaked shapes = **0**; FORGERY_MARKER **present** in the
  real forge output = **True** (the forged id was genuinely DRIVEN — non-vacuous); benign shapes
  carrying the marker outside delimiters = **0** (probe-needs-a-control holds).
- NEGATIVE (MUTATION — `render_subject_bound` rewritten to leak the ids as BARE text, no
  `render_attributed`): leaked shapes = **3** → the probe DISCRIMINATES; a containment regression in
  render_subject_bound reddens the `_render_recalled_memories` P-N pin.
So coverage GREW (the probe now exercises + guards the #437 bound line) and nothing shrank; the
`_render_recalled_memories` probe is not skipped/exempted and render_subject_bound is not excluded.

## §OTHER-MODULES (no regression shifted elsewhere)
- All other render-named modules (`test_memory_render_bound_63b_ib`, `test_comms_render_architecture`,
  `test_render`, `test_render_seam_pins`, `test_render_mypy_layer`, `test_render_mypy_layer_optout`)
  → **207 passed, 3 xfailed** (`-n auto`).
- Modules importing from my file: `test_render_slot_inventory` (shared registry — GREEN in the
  main run); `test_comms_await` + `test_comms_waiting_line` (import only `FORGERY_MARKER`/`_leaks`,
  which I did not touch) → **49 passed**. `test_ast_reach_helpers.py` keys test_link5 only by
  FILENAME in a prose allowlist (no line/content pin) — unaffected.
- ruff on the two changed files → **All checks passed!**

## §FORK-B (decision needed — flagged per the brief's escape hatch, not silently resolved)
The brief's move (b) says "REGISTER render_subject_bound as a NEW driven render in the coverage
inventory … do NOT exclude it … coverage must GROW." Implementing that as a SEPARATE probe key in
`_render_probes()` has a structural conflict I could not resolve within the 2-file reconciliation:

- **Why (measured):** the P-U candidate universe is DERIVED name-blind by
  `_method_interpolates_a_nonconstant` (raw f-string / `.format` / sanitise-seam — the LEAK-CAPABLE
  property). render_subject_bound routes purely through the CONTAINMENT seams
  (`render_line`/`render_attributed`), so it is safe-by-construction and correctly NOT a candidate
  (62 candidates, 43 driven). It is **1 of 11** AppContext methods in that class. Adding it (alone)
  to `_render_probes()` reddens the reverse-leg `test_no_probe_or_out_entry_is_a_stale_non_candidate`
  (it becomes `stale_driven`). Making it a legitimate candidate requires widening the universe to
  admit containment-seam methods → pulls in all 11 (0 currently driven/OUT) → 11 new probes/OUT
  entries = a coverage EXPANSION + a change to the P-U universe's SEMANTICS (a design decision on
  the shared substrate for the whole containment test), which is beyond "reconcile to a landed
  render change" and is not licenced to weaken/reshape coverage.
- **Reading A (what I implemented — RECOMMENDED):** render_subject_bound is DRIVEN + GUARDED
  TRANSITIVELY via the `_render_recalled_memories` probe with a forged-id Subject (mutation-proven,
  §COVERAGE-GREW), and its design coverage pins (§3.3 (ii) AST-derivation, (iii) hostile-fixture)
  are ALREADY GREEN in the dedicated `test_memory_render_bound_63b_ib.py`
  (`TestEveryGovernedReadRenderCarriesTheBoundLine`, `TestTheBoundLineContainsForgedIds` — confirmed
  via lore_impact: 1 consumer, 19 covering tests). Coverage grows; nothing is excluded/shrunk; both
  universe legs stay clean; no scope explosion.
- **Reading B (NOT recommended):** widen `_method_interpolates_a_nonconstant` to treat the
  containment render seams as interpolation and add all 11 methods as probes. This is a universe
  redesign → escalate to the design-sidecar/operator; do NOT do it as a silent builder edit.
- **My pick: A.** It satisfies the brief's INTENT (render_subject_bound driven with a hostile
  fixture, coverage grows, nothing excluded, mutation-proven) without a scope-exploding,
  design-level change to the shared P-U substrate, and its dedicated design pins are independently
  green. If the lead requires a literal separate P-U probe key, that is Reading B = a design fork.

## §DRY-LEDGER (§6)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `recalled_subject` (local helper in `_probes()`) | lore_search "forge a Subject with a forged principal_id agent_id for the bound-line hostile fixture" (path=test_memory_render_bound_63b_ib.py) | `_subject(...)`→`member(...)` in `_governed_contract.py` (the shared `pdp.Subject` forge, SEC-F3 empty-id-refused) | **REUSED `_governed_contract.member`** — `recalled_subject` is a thin forge-aware wrapper (adds the `_tok`-token vs benign choice), not a fork of the forge |

## §DISCIPLINE
- No git mutation (the lead commits). No production file touched (server.py untouched on disk;
  the mutation proof monkeypatched in-process and restored — verified `is orig`).
- lore-first: used lore_get_symbol/lore_search/lore_impact for all structure lookups. Fallbacks
  SAID OUT LOUD: (a) grep is hook-blocked in this checkout — used Read + python file-scans for
  call-site enumeration and import-graph checks; (b) empirical membership checks run via a scratch
  python import of the test module (not lore) because the candidate/driven sets are runtime values,
  not indexed symbols.
- Tests ran against TEST store :18000 only (never :18500).
