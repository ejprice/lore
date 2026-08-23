# REPORT — coldaudit-61a-w3

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done**
- **VERDICT: GO** — the #398/#399 recurrence invariant is real, non-vacuous, discriminates, and
  faithfully executes §Fork J + its rider. All gates green; all 5 mutation legs + both KNOWN-BOUND
  PIN-THE-MISS pins independently re-derived and HELD; the docstring cleanup is a faithful reframe.
- deviations: none (audit-only; edited no file; the guard was mutated in-place with a content backup
  and restored byte-exact — md5 `31d548eaec69938ef22542071fc2d29a` unchanged).
- Packages considered: none — no mechanism specified (audit of a stdlib `ast`/`re` source guard).
- Reuse ledger: none — I introduced no production symbols (audit; scratch/in-place probes only).
- Graded: f87e774 · HEAD-at-report: f87e774 · SAME (wave uncommitted; the three REPORT-*, the guard,
  the contract, and the `test_principal_keys_schema.py` docstring edit are the untracked/modified set).
- decisions-needed: none blocking. One RESIDUAL for the lead + a 61a-w4 brief note (§Residuals R1).
- receipt pointers:
  - independent slice enumeration → §"Not vacuously green"
  - re-derived mutation table → §"Mutation proofs (independently re-derived)"
  - both-derivations + INSTRUMENT-0 + prose-bound + docstring checks → §"Derivations & bounds"
  - RESIDUALS → §Residuals
  - guard content backup: `/tmp/guard-backup-61aw3.py` (md5 matches HEAD guard)

Provenance receipt (#140): mutations were applied to the TEST-tree file
`loremaster/tests/_schema_fold_guard.py` **in place in the real repo** (no scratch copy), so
`import loremaster` is unambiguously the real package — `loremaster.__file__ =
/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`. Each mutation was
content-backed and restored byte-exact (verified by md5 after every leg).

---

## Gates (re-run, counts pasted)
- **Contract file** `test_schema_fold_coverage.py -n auto` → **29 passed in 4.37s** (matches expected 29).
- **typecheck.sh** → all members OK (`loremaster` OK · `skills` OK · `docs/eval` 49 files OK · `scripts`
  OK · shellcheck OK 7 .sh). 0 errors.
- **ruff check .** → `All checks passed!`
- **Full suite** `loremaster/tests -n auto` (SOLO) → **8495 passed, 50 skipped, 3 xfailed, 0 failed** in 273.14s (exit 0). Zero failures ⇒ the #405 SOLO caveat did not trigger.
- **pending_contract_gate.py --currency** (SOLO) → **PASS** — `typecheck GREEN · ruff GREEN · pytest GREEN`, manifest `('typecheck','ruff','pytest')`, no RED_ORPHANED (exit 0).

## Not vacuously green (the load-bearing check for a scan-guard)
Independent enumeration (bare `grep -nE '^def _[a-z0-9_]+_statements\('` over `surreal_schema.py`, then
cross-checked through the guard's own AST functions):

- **28** `_*_statements` slice fns (by-NAME) — I counted them by grep AND via `derive_slice_fns`; equal.
- **28** private top-level `-> list[str]` defs (by-SHAPE, `derive_statement_emitters`) — the SAME 28, so
  `by_name == by_shape` (the INSTRUMENT-0 positive control; contract's "= 28 at f87e774" reproduced).
- `derive_folded_slices` = **16** (independently confirmed by reading `generate_ddl`'s body, lines
  1708–1731).
- The **12** unfolded slices are EACH consumed by a standalone `generate_*_ddl` — I verified every one
  by reading the generator bodies:
  `_agent`→`generate_agent_ddl`; `_brief`/`_briefed`/`_brief_counter`→`generate_brief_ddl`;
  `_message`→`generate_message_ddl`;
  `_code_node`/`_name`/`_refers`/`_answers_to`→`generate_graph_ddl`;
  `_floor_measurement`/`_floor_head`→`generate_floor_calibration_ddl`; `_lease`→`generate_lease_ddl`.
- `covered = folded | standalone` = **28**; `slices - covered = []`; `scan_schema_fold_coverage(real)` =
  **[]**; `scan_stale_emptiness_prose(real)` = **[]**.

So the guard returns `[]` on the real schema because every slice is **genuinely folded-or-standalone**,
NOT because it saw nothing. Non-vacuity is additionally proven two ways: (a) the fail-closed reach pins
(M3 below) show a blind/renamed scan RAISES rather than returning a clean `[]`; (b) the literal-only
`_emits` wrong build (M2) leaves the real-schema scan green — a false clear caught ONLY by the
variable-returner pins, which is exactly the adversary blocker the contract closed.

## Mutation proofs (independently re-derived — NOT trusting the builder table)
Each leg: declare expected-RED pins → mutate the production guard (content-backed) → assert the pins
fail → assert a positive control STAYS GREEN where applicable → restore → verify md5. Guard md5 back to
`31d548eaec69938ef22542071fc2d29a` after every leg.

| # | leg | mutation (on `_schema_fold_guard.py`) | declared RED — result | positive control |
|---|---|---|---|---|
| M1 | structural fold-coverage | `derive_folded_slices` → `return slices` (all "folded") | 6 pins RED (unfolded-nonempty, unfolded-variable, both real-source fold-drops, rederived-per-call, finding-names-slice) — **HELD** | (unmutated = 29 passed) |
| M2 | `_emits` literal-only (adversary blocker) | `_is_provably_empty`: `if len(body)!=1: return False` → `return True` (variable-returners treated empty) | 3 variable-returner pins RED (`…_variable_returning_slice_is_flagged`, `test_removing_a_real_variable_returning_fold_call_reds_the_scan`, `test_reintroducing_stale_prose…`) — **HELD** | literal pin + `test_the_real_schema_has_zero_fold_coverage_findings` STAYED GREEN (proves targeted **and** the false-clear the blocker guards) |
| M3 | INSTRUMENT-0 fail-closed | drop the `_assert_reach_or_raise(by_name, by_shape)` call | 2 reach pins RED (`test_a_misnamed_emitter_fails_the_scan_closed`, `test_a_wholesale_convention_rename_fails_the_scan_closed`) — **HELD** | — |
| M4 | prose leading-comment | `_leading_comment_block` → `return ""` | leading-comment prose pin RED (`test_reintroducing_stale_prose…`) — **HELD** | docstring prose pin STAYED GREEN (paths independent) |
| M5 | prose docstring | `docstring = ast.get_docstring(node) or ""` → `docstring = ""` | docstring prose pin RED (`…_stale_emptiness_docstring_is_flagged`) — **HELD** | leading-comment prose pin STAYED GREEN (paths independent) |

The five legs map to the brief's five (drop-a-real-fold ⇒ M1's mechanism + the real-source mutation
pins it reddens; literal-only `_emits` ⇒ M2; rename-convention/self-coverage ⇒ M3; emits-nothing-comment
⇒ M4; +5th = M5 docstring half). M2 is the load-bearing one: it independently reproduces the adversary
blocker — a literal-only `_emits` false-clears the real schema and is caught ONLY by the
variable-returner pins.

## Derivations & bounds
- **(a) Slice-fn set is AST-DERIVED, not a hand-list.** `derive_slice_fns` = `{def.name matches
  ^_[a-z0-9_]+_statements$}` over `ast.parse`; re-derived per call (pinned:
  `test_the_scan_is_rederived_per_call_not_cached`, mutation-proven under M1). No literal slice list
  anywhere in the guard.
- **(b) Standalone set is DERIVED** (called-by-some-`generate_*_ddl`), not a literal
  `_STANDALONE_SLICES`. This is a REASONED refinement of §Fork J's "explicit allowlist" wording,
  demanded by the same ruling's rider ("derived-not-hand-list") + INSTRUMENT-0 / registration_sites
  law; the adversary concurred (a literal set = the 7th reach-defeat). GOOD.
- **Dead-generate over-exemption is honestly PINNED as a KNOWN BOUND** with a whole-tree-reachability
  re-open trigger (`TestStandaloneExemptionIsAKnownBound`). I confirmed it is a real PIN-THE-MISS:
  closing the exemption in the guard (`covered = derive_folded_slices(source)` only) REDS the pin
  (M6, restored byte-exact). Verified false at HEAD: every `generate_*_ddl` is wired to a store
  `ensure_ready` (contract-61a-w3 §"Standalone allowlist" traces each; not re-run — a static wiring
  claim, accepted).
- **Prose bound honesty.** The prose leg is enumerate-the-forbidden over a CLOSED
  `KNOWN_EMPTINESS_PHRASES` set, pinned as a KNOWN BOUND (`TestStaleEmptinessProseIsAKnownBound`). I
  confirmed it is a real PIN-THE-MISS: widening the set to catch the "novel" phrase REDS the
  bound pin (M7, restored byte-exact). Within-set discrimination is proven by M4/M5 + the contract's
  honest-prose / truthful-empty-stub / novel-phrasing negative controls. "emits nothing" and "emit []"
  are both in the set; it covers the shipped #398/#399 wordings (`red stub`, `not folded`, `emit`).
- **INSTRUMENT-0 residual bound** (rename that ALSO drops `-> list[str]` evades both derivations) is
  pinned with its re-open trigger (`test_a_rename_dropping_the_annotation_evades_both_is_a_known_bound`).

## Docstring cleanup (`test_principal_keys_schema.py`) — faithful reframe, ground-truthed
The diff reframes the module docstring's stale present-tense STUB claim into a dated historical-origin
note. Ground-truthed against the real greened slice:
- `_principal_key_statements` (surreal_schema.py:1891) emits a real `DEFINE TABLE` + 6 fields + 2 UNIQUE
  indexes — NOT `[]`.
- folded into `generate_ddl` (line 1722).
- consumed by standalone `generate_principal_key_ddl` (line 1947: `return ";\n".join(
  _principal_key_statements()) + ";\n"`).
All three claims in the new note are TRUE; the old present-tense claims were all FALSE at HEAD. This is
a faithful reframe (past-tense for the authoring stub state, present-tense for the greened reality,
tagged `retired 2026-08-23, packet 61a-w3, #398/#399`) — NOT a blind deletion and NOT a new inaccuracy.
Only that sentence changed.

## Residuals
- **R1 (fragility, low severity — does NOT block GO): the prose backstop has an undocumented
  FALSE-POSITIVE mode.** A *truthful historical* note ("Introduced as RED STUBS … the slice is NOW
  BUILT and emits real DDL") placed **directly above** an emitting folded slice is flagged by
  `scan_stale_emptiness_prose` as a stale #398/#399 lie (probed: it returns
  `ProseFinding(slice_fn='_hist_statements', phrase='red stub')`). The real schema is clean ONLY
  because the `_KEEP_FIELD_SPECS` / `_PRINCIPAL_KEY_FIELD_SPECS` constants sit BETWEEN each historical
  comment block and its def (probed: the same note *separated* by one constant → `[]`). Two reasons
  this is worth surfacing:
  1. It is undocumented — only the false-NEGATIVE direction (novel phrasing) is a pinned bound; this
     false-POSITIVE direction is not, and its finding MESSAGE would be inaccurate ("contradicting the
     running code" for a truthful note).
  2. It could bite **61a-w4** (the `audit` slice, which §Fork J says "WILL write RED-STUB comments a
     builder greens"): if that builder retires the RED-STUB comment by **reframing it in place directly
     above the def** — the very pattern the builder just used for `test_principal_keys_schema.py` — the
     guard false-positives. The safe remediation is to DELETE the RED-STUB comment on green, or keep any
     historical note NON-adjacent to the def. Recommend the lead either (a) note this in the 61a-w4
     brief, or (b) have a follow-up pin the false-positive as a second KNOWN BOUND. No fix asked of this
     wave.
- **R2 (housekeeping, at commit): resolve #398 AND #399 on the invariant's commit** (§Fork J rider) —
  the fix-without-the-invariant was half a fix. Lead action, not a build defect.
- **R3 (informational): finding #409** (contract author's transient `lore_index` failure) is filed;
  the contract's exhaustive def enumeration fell back to grep (sanctioned — rename-exhaustiveness). No
  bearing on this build.

## What I verified vs accepted
- VERIFIED first-hand: slice enumeration (grep + AST), fold/standalone derivation (read every generator
  body), all 5 mutation legs + M6/M7 bound-discrimination, the docstring reframe (read the real slice),
  typecheck, ruff, contract-file 29, prose false-positive probe.
- ACCEPTED (static claim, not re-run): the standalone→store-`ensure_ready` wiring table in
  contract-61a-w3 §"Standalone allowlist" (12 rows). It is the dead-generate bound's "false-at-HEAD"
  evidence; the bound is pinned regardless, so a stale row degrades to the pinned bound, not a false
  clear.
