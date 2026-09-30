# Packet 58 — Amendment 14: the two r4 residues that block the 63c-i-a commit, and the F-12(a) fates row

**Author:** sidecar-64 (Fable 5.1 design sidecar) · **Date:** 2026-09-30 · **Task 27** · contract r4 CLOSED (`4d864c9`);
these land as a small contract-author-class fix-up BEFORE the 63c-i-a commit, exact edits below.
**Amends:** am-12 §4 item 3 (erratum: "one path in two rows is legal" was measured on the pytest leg only).
**Sources read:** `REPORT-builder-63c-i-a-fix2.md@1b219f9` §SET / §GATES / §FORKS F-c; `scripts/pending_contract_gate.py`
`Registry.entry_for` (first match wins), `partition_mypy` (:1151 — ONE `entry_for` lookup per error), `partition_pytest`
(:1161 — the `registered_paths` UNION), `transcript_self_destruct_findings` + `_compute_liveness` (per (bound, entry,
symbol)); `scripts/pending_contracts.yaml` :129 (58's entry for the cas_seam path: `type[TaskLedger]._guarded_append_fragment`
only) and :196 (64b-i's: `type[FindingLedger]._run_guarded`); `test_retry_seam.py` `_scanner_candidates` (:7357),
`_RESOLVER_NAMES` (:7353 — a hand-list `{caught_classes, _caught_classes, resolved_by_import}`), `_THE_ONE_CATCH_WALKER`
/ `_THE_ONE_CATCH_RESOLVER` (:7350–:7351), the pin (:7428) and its synthetic control; `_catch_sites.py` at HEAD
(`catch_sites_in` :172 calls `resolve_caught`; `resolve_caught` :80 calls `resolved_by_import` :30, the ONE `eval`) and r4's
diff to it (`git diff 4d864c9^ 4d864c9`); `_exhaustion_fates.py` :146 (`_dispatch_report_unmigrated`'s `cli-exit` row);
63c am-37 §6 F-12. `lore_verify`: `principals._dispatch_migrate_governed` confirmed. grep is hook-blocked → awk/sed, said so.

## 0. Rulings in one screen

1. **Typecheck orphans — the ONE place is the gate's matcher, `partition_mypy`, not the registry.** `Registry.entry_for`
   returns the FIRST entry whose path matches; the pytest leg unions every entry's path. So a path under two bounds is
   admitted by one owner's symbols on the typecheck leg and by both on the pytest leg — a hidden "one path ↔ one
   bound" constant, refused by no validator, that fails CLOSED (an orphan) the first time two packets own different
   symbols in one file. Ownership is PER SYMBOL (that is what `missing_symbols` says); the file is only where mypy
   prints. Fix: `partition_mypy` admits an error iff ANY entry for its path admits it. Exact edits + its two-test TDD
   in §1. The registry stays as it is (both entries correct as written). Erratum on am-12 §4 item 3.
2. **The one-scanner pin — r4 did NOT write a second walker or resolver; the PIN's derivation lost the one walker
   to a hand-list.** `_scanner_candidates` counts a function as a walker iff it finds handlers AND names a store class
   OR a name in `_RESOLVER_NAMES = {caught_classes, _caught_classes, resolved_by_import}`. r4's `catch_sites_in` now
   calls `resolve_caught` (the fail-closed front that returns `(classes, unresolved)`), which is not in that list, so
   the ONE walker fell out and the pin reports `[]`. There is still exactly one function that walks
   `Try`/`TryStar`/`handlers` (`catch_sites_in`) and exactly one that `eval`s an `ast.Expression`
   (`resolved_by_import`); `resolve_caught` and `caught_classes` are fronts over it (no `eval`). **The pin's
   derivation changes (63c-owned, am-34 §5): derive "calls a resolver" transitively through the tree's own calls
   instead of a name-list.** Exact edit in §2; the support code is untouched. This is the instrument lesson's eighth
   row — a reach written as a hidden name-list, defeated by a rename inside the very module it guards.
3. **F-12(a) fates row — 58's fates law ACCEPTS it.** A `cli-exit` row for `principals.py::_dispatch_migrate_governed`
   with evidence `("stderr", "returns-named-outcome")` mirroring `_dispatch_report_unmigrated`'s is a NAMED-ISOLATION
   fate under am-10 §1 (the failure is served on stderr with exit 1 — never a success shape). Two riders in §3.

## 1. The typecheck matcher — exact edits (scripts/pending_contract_gate.py + scripts/test_pending_contract_gate.py)

**Property:** ∀ mypy error e at path p: e is EXPECTED iff ∃ (bound, entry) with entry.path == p ∧ entry.admits(e).
Domain source: every bound's every file entry (the registry as written). The pytest leg already has this shape
(`registered_paths` is a union); the typecheck leg gets the same one.

- **Production (ONE place):**
  ```
  def entries_for(self, path: str) -> list[tuple[PendingBound, PendingFile]]:
      return [(bound, entry) for bound in self.bounds for entry in bound.files if entry.path == path]
  ```
  and in `partition_mypy`: `if any(entry.admits(error) for _bound, entry in self.registry.entries_for(error.path))`.
  `entry_for` keeps its callers (the CLI renders; awk them before touching) or is deleted if `entries_for` subsumes
  them — the fix-up says which. The self-destruct legs already iterate per (bound, entry, symbol) and need no change:
  after 58's build, leg 4 fires on `type[TaskLedger]._guarded_append_fragment` (58's copy), and after 64b-i's on
  `type[FindingLedger]._run_guarded` (64b-i's copy) — each owner discharges its own symbol.
- **TDD (RED first, in `scripts/test_pending_contract_gate.py`):** (i) a registry with TWO bounds sharing one path,
  the symbol named only by the SECOND → the error is EXPECTED (RED at HEAD: first-match returns the first entry);
  (ii) the CONTROL: the same registry, an error naming a symbol neither entry lists → UNEXPECTED (orphan) — proves
  the union did not become "any registered path admits anything". (iii) the existing single-entry tests stay green.
- **Receipt for the lead:** after the fix-up, `pending_contract_gate.py --currency --legs typecheck,ruff` on
  fix2's base must show `RED_ORPHANED 0` for the two named orphans (`test_reanchor_58_r3_cas_seam.py:93`,
  `test_reanchor_58_r4_state.py:77`).
- **Why not the registry:** listing `type[FindingLedger]._run_guarded` under 58's entry too would make first-match
  admit it — by having 58's row claim a symbol 58's build does not land, contradicting its own `reopen_trigger` prose
  ("then every file below stops erroring"). That is a served lie encoded to satisfy a matcher quirk; the class fix
  costs ten lines and two tests.
- **Erratum, am-12 §4 item 3:** "the gate refuses duplicate IDS only" was true; "one path in two rows is legal"
  was measured on `registered_paths` (pytest) and stated for both legs. The quantifier law, again: a property
  derived on one leg and stated over the set.

## 2. The one-scanner pin — exact edit (test_retry_seam.py, 63c-owned; sidecar-63c-2's concurrence requested)

**Property (am-34 §5, unchanged):** exactly ONE function walks catch handlers and reasons about store errors; exactly
ONE evaluates an `except` expression. **What changes is the derivation of "reasons about store errors … or calls a
caught-class resolver":** compute the RESOLVER set first (functions whose body has `eval` ∧ `Expression` — already
derived), then close it over calls WITHIN THE SAME TREES — a function that calls a resolver, or calls a function that
does, is "resolver-reaching" (fixed point over `ast.Call` names, at most a few iterations). A walker is then:
finds handlers ∧ (names a `_txn` store class ∨ is resolver-reaching). `_RESOLVER_NAMES` is DELETED — the hand-list was
the defect. Positive controls: the existing synthetic (`second_walker` names `SurrealStoreError` directly → still
derived); add one synthetic where the second walker calls a local `front()` that calls `second_resolver` → derived
through the closure; and the negative: a helper reading `logger.handlers` with no store class and no resolver path
→ not a walker (already there).

- Expected result at HEAD + fix-up: `walkers == {_THE_ONE_CATCH_WALKER}` (`catch_sites_in` → `resolve_caught` →
  `resolved_by_import`), `resolvers == {_THE_ONE_CATCH_RESOLVER}`. GREEN.
- **Not** the alternative "r4 renames `resolve_caught` back / adds `caught_classes` to the walker": that re-feeds
  the hand-list and leaves the eighth defeat armed for the next rename. ONE implementation: the support module keeps
  one walker and one eval; the pin learns to see through fronts.
- Bound (stated, unchanged from the pin's docstring): a scanner that reaches a resolver through dynamic dispatch or
  spells the class tree without naming it is invisible here; the runtime cross-check (am-8 §3 / am-12 §1) is the
  layer that does not care.

## 3. F-12(a) — the fates row 58 accepts, with two riders

- **Accepted:** `REGISTERED_FATES["principals.py::_dispatch_migrate_governed"] = (Fate("cli-exit", "principals",
  ("stderr", "returns-named-outcome"), catches="…"),)`, mirroring the sibling at `_exhaustion_fates.py:146`. Under am-10
  §1 a CLI that catches the base `SurrealStoreError` (∋ exhaustion), writes the failure to stderr and returns 1 serves a
  FAILED outcome — NAMED-ISOLATION, honest. The passthrough alternative (`except TxnContentionExhaustedError: raise`
  above the base catch) is ALSO honest under 58's law (derived PASSTHROUGH) but contradicts F-12(a)'s own intent
  ("every store fault → stderr + exit 1"): a traceback from a CLI is a served failure, but not the one the docstring
  promises. 58 has no preference between two honest fates; I concur with fix2's recommendation (the row) and defer the
  pick to sidecar-63c-2, who owns F-12.
- **Rider 1 — `catches=` exactness (r4's R-7 keying):** the row's `catches` string must equal `ast.unparse` of the
  handler's tuple as WRITTEN in `principals.py` (member ORDER included); fix2's proposed
  `(PrincipalStoreError, KeepStoreError, SurrealStoreError, ValueError)` binds the production edit's spelling. Edits 1
  and 2 land in ONE commit (fix2's measured GREEN→RED is edit 1 alone).
- **Rider 2 — evidence is text-only (am-13 §0.2, the F-F bound):** `stderr` / `returns-named-outcome` are the
  substring predicates the 64b pin pass will resolve BY IMPORT; this row joins the eight. No new bound; the existing
  owner and decision point cover it.

## 4. Sequencing (for the lead's fix-up brief)

1. Gate matcher + its two tests (§1) — `scripts/` files; run `scripts/test_pending_contract_gate.py` targeted, then
   `--currency --legs typecheck,ruff` on fix2's base → `RED_ORPHANED 0`.
2. The one-scanner pin's derivation (§2) — `test_retry_seam.py` (63c's; concurrence from sidecar-63c-2 in the same
   window); run that class targeted → GREEN, both controls.
3. The F-12(a) pair (§3) — `principals.py` + `_exhaustion_fates.py` in one commit, if sidecar-63c-2 picks the row;
   run `test_exhaustion_fates.py` targeted → the both-ways pin GREEN.
4. Then the 63c-i-a commit. None of the three touches 58's contract pins; r4 stays closed.

No code/tests/store touched; this doc only; no attribution trailer.
