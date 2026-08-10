# REPORT — contract-eh (INSTRUMENT E #289 + INSTRUMENT H #290)

brief-base v10 read
brief project v7 read

## SUMMARY
- **state:** done — two NEW contract files written, RED confirmed, gates clean on both.
- **Files (writable set, both NEW, nothing else touched):**
  - `scripts/test_trailing_newline_matrix.py` — INSTRUMENT E (#289)
  - `scripts/test_harness_guards.py` — INSTRUMENT H (#290)
- **RED/GREEN (measured at HEAD `e1dfa14`, `-p no:randomly`):** `12 failed, 5 passed`.
  - 5 GREEN = the instance/trap pins that must be green at HEAD (fix already landed).
  - 12 RED = every pin that references the two NOT-YET-BUILT helpers
    (`_newline_matrix.newline_forgery_variants`, `_harness_guards.refuse_vacuous_baseline`);
    all fail with `ModuleNotFoundError` — the RED the brief asks me to confirm.
- **Gates on the two new files:** ruff `All checks passed!`; mypy (canonical `scripts` leg,
  `MYPYPATH=scripts uv run mypy scripts`) — **0 errors in either new file**.
- **deviations:** (1) helper for E is imported via `importlib.import_module` (not a static
  `from _newline_matrix import …`) so the typecheck gate stays GREEN while pytest is RED — the
  concurrent sibling `scripts/test_wave_gate.py` did it the static way and REDDENS the scripts
  typecheck leg (see Flags). (2) E's malformed-input CLASS rule is realised as a reusable matrix
  GENERATOR + the residual field-classification left as judgement — a reconciliation of the brief
  vs design-doc §INSTRUMENT E, not a silent override (see Body §E-2).
- **Packages considered:** none — the two specced helpers are trivial stdlib predicates (a
  dict→variants generator; a zero-count refusal). No library replaces a two-line predicate; the
  point is ONE implementation + a covering test (design doc §INSTRUMENT H concurs).
- **Graded:** `e1dfa14` · HEAD-at-report: `e1dfa14` · SAME. (I render one verdict about a
  sibling artifact — `test_wave_gate.py` breaking the typecheck leg — measured at this sha.)
- **decisions-needed (3, details in Body §Forks):**
  1. `refuse_vacuous_baseline` raises `SystemExit` (I pinned this — preserves `wrong_builds.main`
     exit-1) vs. a dedicated exception. Builder/operator call.
  2. E helper module name/home `scripts/_newline_matrix.py` is MY choice (co-located + gated);
     builder may rename but must move the contract's `import_module("_newline_matrix")` with it.
  3. E helper's refusal type for empty/unknown-field pinned as `ValueError` (diagnostic refusal).
- **receipt pointers:** RED/GREEN tail → Body §Receipts; per-pin wrong-build table → Body §E-1/§E-2/§H;
  sibling typecheck breakage → Body §Flags.

---

## Body

### Lore usage / fallbacks
lore-first: `lore_findings action=get 289/290` (read in full), `lore_comms register`. One grep
fallback — `bash grep` over `pyproject.toml` / `test_gated_ground.py` for **non-symbol textual
seams** (testpaths list, the `Exemption` malformed-matrix parametrize block, ruff select) and for a
`.py`-existence check. Said out loud per dogfood protocol; not filed as friction (grep is the
honest instrument for these three, per CLAUDE.md §3).

### The gap each contract closes (verified live, not assumed)
- **#289:** `test_gated_ground.py::TestTheExemptionTableIsAnAllowlistOfTheSafe.`
  `test_a_malformed_row_is_rejected_by_the_tables_own_validation` parametrizes `finding` over
  `""`, `"188"`, `"see the ledger"` — **none carries `\n`**. `.match` and `.fullmatch` agree on all
  three, so a build reverting the #289 fix (`.fullmatch`→`.match`) passes the ENTIRE existing
  contract. Confirmed by reading the block live.
- **#290:** `wrong_builds.main` now has an inline zero-baseline `SystemExit` (the fix), but
  `test_wrong_builds.py` tests anchor-landing only — **nothing drives the zero-baseline path**, and
  the guard is not a reusable helper. Confirmed by reading both files.

### §E-1 — PART 1: the #289 instance, mutation-proven (GREEN at `e1dfa14`)
`TestTheFindingNumberValidatorRejectsATrailingNewline` — 3 pins, all GREEN today, all discriminating:

| pin | what WRONG build fails it |
|---|---|
| `test_match_and_fullmatch_disagree_on_a_trailing_newline` | regex-level control: proves `"#188\n"` actually separates `.match` (accepts) from `.fullmatch` (rejects) at `gg._FINDING_NUMBER`. Not a build-killer; it is the guard that the killer pin below is not vacuous. |
| `test_a_finding_number_with_a_trailing_newline_is_rejected` | **WB22** (`.fullmatch`→`.match`). Fixture is built so on the `.match` build the row CONSTRUCTS: `reopen_trigger` literally embeds `"#188\n"` so the `finding in reopen_trigger` cite check passes, leaving the fullmatch-vs-match decision as the ONLY thing between construct and reject. A `pytest.raises` that passed for the WRONG reason (cite failure) is the trap avoided; the `"not a finding number"` message assert is the positive control on the reason. |
| `test_the_same_finding_number_without_the_newline_is_accepted` | negative control — a validator that rejected EVERY finding. |

**Named killed wrong build (builder to add to `scripts/wrong_builds.py`, outside my writable set):**
`WB22_finding_number_validated_with_match` — anchor
`if not _FINDING_NUMBER.fullmatch(self.finding):` → `if not _FINDING_NUMBER.match(self.finding):`.

### §E-2 — PART 2: the reusable trailing-newline matrix (RED — helper absent)
`TestTheReusableTrailingNewlineMatrix` — 6 pins, all RED (`ModuleNotFoundError: _newline_matrix`).
Intended helper: `newline_forgery_variants(base: Mapping[str, object],
interpolated_fields: Sequence[str]) -> list[tuple[str, dict[str, object]]]`.

| pin | property / what WRONG helper fails it |
|---|---|
| `…yields_exactly_one_variant_per_declared_field` | one case per field; a helper that dedups or drops a field fails. |
| `…appends_a_trailing_newline_to_exactly_that_field` | only the named field gains `\n`; the rest copy through. Kills a helper that newlines every field, or the wrong one. |
| `…does_not_mutate_the_base_mapping` | returns fresh dicts; kills an in-place mutator that corrupts the caller's base. |
| `…empty_field_list_is_refused_as_vacuous` | **anti-vacuity on the matrix itself** (#290 lesson applied to E): `[]` must raise `ValueError`, not return `[]` (a `for … in variants` over `[]` passes silently). |
| `…field_absent_from_the_base_is_refused` | a field with no base value → loud `ValueError`, not a silent skip (a skipped field ends up with no `\n` case anyway). |
| `…matrix_drives_the_real_exemption_door_field` | INTEGRATION — the reusable form of PART 1: feed `["finding"]` + valid base (reopen_trigger embeds `"#188\n"` so it discriminates WB22), the produced `finding="#188\n"` row is REJECTED by the real `Exemption`. |

**Brief-vs-design reconciliation (surfaced, not silently resolved).** Design doc §INSTRUMENT E says
the class rule "cannot be AST-derived generically … rides a checklist, NOT a repo pin." The brief
asks me to "express this as a reusable/parametrised matrix over the interpolated fields." These are
compatible and I built to that seam: the helper is a **mechanical matrix GENERATOR** (enumerates the
`\n` case for whatever fields the author declares — so a forgotten case is impossible), while the
**field-classification** (which fields are bare DOORs vs `!r`-SAFE) stays the residual JUDGEMENT the
design doc calls non-derivable. This mirrors INSTRUMENT B's stance one surface over: derive the
inventory so a wrong judgement SURFACES; do not pretend to remove it. The completeness question
("did the author declare all door fields?") remains INSTRUMENT-0 reach-attack / tdd-checklist
territory — not this pin.

### §H — INSTRUMENT H: anti-vacuity on a comparison's baseline
`scripts/test_harness_guards.py`. Intended helper:
`refuse_vacuous_baseline(measured_count: int, *, cause_hint: str, interpreter: str) -> None`.

- `TestTheZeroBaselineTrapIsReal` (2 pins, GREEN, pure arithmetic — the DISEASE and its negative
  control): the per-run comparison `total == baseline` is SATISFIED by `0 == 0`, so it can never be
  the guard that sees a vacuous reference; with a real baseline the broken run IS caught. This is the
  brief's "distinguish anti-vacuity on the COMPARISON's reference value from the compared runs",
  made concrete and independently green.
- `TestRefuseVacuousBaseline` (6 pins, RED — `ModuleNotFoundError: _harness_guards`):

| pin | property / what WRONG guard fails it |
|---|---|
| `…zero_baseline_raises` | positive control — kills a build that returns None on 0 (no guard). |
| `…nonzero_baseline_passes_and_returns_none` | negative control — kills a build that always raises. |
| `…baseline_of_one_is_a_real_measurement_and_passes` | boundary — kills a `< 2` / `<= 1` threshold; only 0 is vacuous. |
| `…refusal_names_the_interpreter` | **#290 core** — kills a build that raises but drops the interpreter (the silent-ish, cause-less failure). |
| `…refusal_carries_the_cause_hint` | kills a build that ignores `cause_hint` and hardcodes `wrong_builds`' own cause (fatal for a REUSABLE guard). |
| `…guard_is_about_the_reference_not_the_per_run_comparison` | the distinction pinned end-to-end: the same 0 the per-run comparison waves through is REFUSED here. |

**Wiring/mutation proof is the BUILDER's (out of my writable set):** extract the inline guard from
`wrong_builds.main` into `_harness_guards.refuse_vacuous_baseline`, have `main` CALL it, and add the
mutation proof "delete the call in `main` → a covering pin in `test_wrong_builds.py` reddens." My
contract pins the helper's behaviour directly; I cannot land the caller-side proof without editing
`wrong_builds.py`/`test_wrong_builds.py`.

### §Receipts
```
uv run pytest scripts/test_trailing_newline_matrix.py scripts/test_harness_guards.py -p no:randomly -q
  → 12 failed, 5 passed in 0.13s
    5 passed  = E PART 1 (3) + H TestTheZeroBaselineTrapIsReal (2)   ← GREEN at e1dfa14 (fix landed)
    12 failed = E PART 2 (6, ModuleNotFoundError _newline_matrix) + H TestRefuseVacuousBaseline (6, _harness_guards)
uv run ruff check <both files>                       → All checks passed!
MYPYPATH=scripts uv run mypy scripts                 → 0 errors in either new file
                                                       (2 errors are in the SIBLING test_wave_gate.py — see Flags)
```

### §Forks (decisions-needed, detail)
1. **`SystemExit` vs custom exception (H).** I pinned `pytest.raises(SystemExit)` because the current
   `wrong_builds.main` does `raise SystemExit(...)`; a helper that raises `SystemExit` preserves the
   exit-1 behaviour with `main` unchanged (removed-behaviour inventory: preserve-with-pin). A
   dedicated `VacuousBaseline` exception is cleaner as a library surface but forces `main` to
   catch+convert. **Recommend SystemExit** (behaviour-preserving); operator/builder may override — if
   so, one line in my contract changes.
2. **E helper home (`scripts/_newline_matrix.py`).** The brief named H's helper path explicitly
   (`scripts/_harness_guards.refuse_vacuous_baseline`) but not E's. I chose `scripts/_newline_matrix.py`
   — co-located with the contract, and `scripts` is gated on both axes so the helper is covered from
   birth. Alternative: a shared test-support home (`loremaster/tests/_logging_fixtures.py`, per
   INSTRUMENT A-SUB) — rejected because it is not importable from a `scripts/` test without extra
   path juggling. **Recommend `scripts/_newline_matrix.py`.**
3. **E refusal type = `ValueError`** for both empty-list and unknown-field. Chosen as the "loud
   diagnostic refusal" idiom (over a raw `KeyError`). Minor; builder may widen.

### §Flags (noticed, per scope law — not fixed, out of writable set)
- **SIBLING `scripts/test_wave_gate.py` REDDENS THE SCRIPTS TYPECHECK LEG.** `MYPYPATH=scripts uv run
  mypy scripts` reports exactly 2 errors, both in `test_wave_gate.py` (a concurrent sibling's file,
  INSTRUMENT G / #344): `line 115: Cannot find implementation or library stub for module named
  "wave_gate" [import-not-found]` and `line 304: Unused "type: ignore" [unused-ignore]`. That file
  uses a STATIC `from wave_gate import …` against a not-yet-built module — the exact trap my
  `importlib.import_module` idiom avoids. **Consequence:** until `wave_gate.py` lands, the `scripts`
  typecheck leg is RED (would show RED_ORPHANED in a currency check). **Recommend** the wave_gate
  contract adopt the dynamic-import idiom (or its builder land the helper in the same wave). My two
  files are clean; this is not mine to edit.
- **Latent #289-adjacent risk in `Exemption` (noticed, not in scope).** `root`/`reason`/
  `reopen_trigger` are newline-SAFE TODAY only because their error messages use `!r` (repr escapes
  `\n`). If any of those messages is ever changed from `{field!r}` to bare `{field}`, that field
  becomes a DOOR and needs a trailing-newline pin. The E helper makes adding that case trivial, but
  nothing FORCES it — that is the INSTRUMENT-0 reach-attack's job. Raising it so the operator/adversary
  can decide whether to pin the repr-dependency.

### §Standing by
Registered `contract-eh` (session `2026-08-09-fix-344-345`). Will drain lore_comms at turn
boundaries and answer follow-ups. No git state touched (lead commits).
