# REPORT-adversary-63b-i-b-2

brief-base v14 read

STATE: STARTED — 2026-09-04, re-grading REVISED i-b memory-fidelity contract (packet 63b)

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: done
- **VERDICT: CONTRACT INSUFFICIENT** — exactly ONE BLOCKER missing pin (below); everything else holds.
- **P1 headline:** the 3 fixes (F1 split · cand-2 _txn unit · cand-3 render REACH) ALL DISCRIMINATE
  (7 F1/cand-2 wrong builds each caught; cand-3 coverage pin reds on a new bound-less render). The
  #441 matrix + §2.5 C-DEF are robustly pinned. **The ONE hole is in #436 §3.2:** the fidelity
  fixture seeds `scope="server"` on ALL 5 rows (monoculture), and — unlike OWNER, which has
  `test_the_dirty_store_carries_owner_diversity` — SCOPE has no diversity guard. A replay build that
  corrupts every non-`server` scope to `"server"` PASSES the whole contract (FID + LEGACY + ledger-
  write all green), with a correct-build control (the reference passes 80/0). A scope-widening on
  rebuild (`keep:`/`agent-private` → `server`) is a governance-visibility regression #436 exists to
  prevent, invisible to every pin.
- **MISSING PIN:** `test_the_dirty_store_carries_scope_diversity` (mirror the owner-diversity guard)
  AND `_seed_dirty_lifecycle` seeds ≥1 row with a distinct non-`server` scope (probed grantable:
  `principal-private` / `agent-private` both work through `remember`). Defect it catches: a replay
  that hardcodes/collapses scope to a constant.
- Packages considered: none — no mechanism specified (adversary graded a contract + built a throwaway
  reference; hand-rolled nothing new for the grade).
- Graded: 61dc97f · HEAD-at-report: 61dc97f · SAME.
- decisions-needed: none (the missing pin is a contract-author fix within their authority).
- pointers: this report §FIX-DISCRIMINATION · §441-436-437-MATRIX · §436-QUANTIFIER · §P1B · §P1C ·
  §SATISFIABILITY-RECEIPT · §RESIDUALS. Reference build receipts inline (scratch `/tmp/lore-adv-63bib2`,
  `loremaster.__file__` asserted inside).

## Mandate (from lead)
Re-grade the REVISED i-b contract. 1st adversary found F1 (BLOCKER C-DEF) + candidates 2/3,
then STALLED before the wrong-build matrix + #436 QUANTIFIER attack. Verify the 3 fixes
discriminate AND complete the grading the 1st adversary never reached.

Targets (committed 61dc97f):
- test_memory_supersede_atomicity_63b_ib.py (#441, F1 split)
- test_memory_replay_fidelity_63b_ib.py (#436/#453)
- test_memory_render_bound_63b_ib.py (#437 render-coverage derivation)
- test_memory_f5_registration_63b_ib.py
- F5-DATA edit in test_memory_enforcement_63b_ia.py
- test_surreal_store.py::TestDomainRejectionErrorType
- test_retry_seam.py (§2.5 _txn classification unit pins)

Spec (AUTHORITATIVE): design §2 + §3.1-3.2 + §3.3 + §5.1 + §2.5 ADDENDUM.

## Progress log
- [started] report + idle-gate contract written; lore_comms registering; now reading.
- [read] role spec + full design (§1–§5.1 + §1.9 + §2.5 ADDENDUM) + both continuity reports + all 7 target modules.
- [reference] Built a FULL §2/§3/§2.5 reference in provenance-asserted scratch `/tmp/lore-adv-63bib2`
  (`loremaster.__file__ = /tmp/lore-adv-63bib2/loremaster/loremaster/__init__.py`).

## SATISFIABILITY RECEIPT (independent, FULL — closes the reviser's scoped gap)
Reference build (throwaway; builder ships the real thing) touched, per §2/§3/§2.5:
- `store/_txn.py`: `TxnGovernedConflictError(SurrealStoreError)` · `_ERROR_CLASS_GOVERNED_CONFLICT`
  (fixed label) · `_GOVERNED_CONFLICT_MARKER = "governed_conflict:"` · `_classify_engine_error`
  marker branch → the fixed label · `_domain_rejection_error(error_class, message)` (label→type, ONE
  helper) · BOTH raise sites (`run_query`, `_run_verified_transaction`) route through it.
  `_rollback_verdict` UNCHANGED.
- `governed.py`: `authorize_guarded`→`GuardedPlan` split; `GuardedPlan.fragments` emits
  `LET $gw_hit=(UPDATE … RETURN AFTER); IF array::len($gw_hit)=0 { THROW "governed_conflict:<t>:<id>" }`;
  `guarded_write` = authorize_guarded + fragments + execute + `except TxnGovernedConflictError → raise
  GovernedConflict from error`; the Python `row_count==0` branch DELETED.
- `memory/ledger.py`: `retire(id, *, valid_until, superseded_by)` + `delete(id)`.
- `memory/local.py`: `remember` = authorize_guarded (deny-first) → ledger record (governance +
  lifecycle stamps) → ONE `execute_transaction([*plan.fragments(close), upsert])` under
  `write_guard("remember")` → compensate `ledger.delete` on ANY exception; `invalidate` → guarded_write
  close → `ledger.retire`; `_replay_record` reconstructs FROM the ledger (owner/scope/created_at/
  valid_from/valid_until/superseded_by) + composes the predecessor-close UPDATE literal (the #436 L1
  site); `_build_content` takes the stamps; `_ledger_metadata` carries them.
- `server.py`: `render_subject_bound(subject)` (via `render_line`+`render_attributed`);
  `_render_recalled_memories(recalled, *, subject)` prepends it (incl. empty); `recall` passes `subject=`.

Command (serial, bounded, provenance-asserted): `timeout 600 ./.venv/bin/python -m pytest <7 target
modules> -n0 -p no:cacheprovider` → **80 passed, 0 failed, 1 warning in 18.12s (no hang; real 0m19s)**.
Covers ALL 4 i-b modules + the i-a F5 module (ghost pin GREEN on the reference) + `TestDomainRejection
ErrorType` + `TestTheGovernedConflictClassIsRegisteredInTheSeam`. Incremental green receipts:
§2.5 unit 9/0 · store-layer NEW-API 7/0 · #437 render 9/0 · behavioral atomicity + replay fidelity
13/0 · f5 registration 9/0.

All wrong builds below were applied to the reference (backup → patch → run pin → restore; every
restore diff-verified byte-identical). Every RED is paired with the reference's GREEN (P0 control).

## §FIX-DISCRIMINATION (mandate 1 — the 3 fixes discriminate)
| # | wrong build (mutation) | pin that MUST red | result |
|---|---|---|---|
| F1(a) | raise message = `f"…{root_cause.raw_result}"` (leak raw marker/suffix) | `TestDomainRejectionErrorType::…transaction_seam…` [both params] + the store-layer rescope pin (`…no race_pred in msg`) | **RED** (2 + 1) |
| F1(b) | `_domain_rejection_error` always returns plain `SurrealStoreError` (never typed) | rescope pin (`isinstance TxnGovernedConflictError`) + live seam pin + helper unit | **RED** (1 + 2 + 1) |
| F1(c) | `guarded_write` does NOT `except TxnGovernedConflictError` | `test_a_conflicting_guarded_close_surfaces_governed_conflict` (expects `GovernedConflict`) | **RED** |
| cand-2(a) | `run_query` raises `SurrealStoreError(...)` inline (bypass the ONE helper) | `test_both_domain_raise_sites_build_their_rejection_via_the_one_mapping_helper` | **RED** |
| cand-2(b) | drop the marker branch in `_classify_engine_error` | `test_the_classifier_maps_the_governed_conflict_marker_to_the_fixed_label` + live seam | **RED** (1 + 2) |
| cand-2(b') | `_ERROR_CLASS_GOVERNED_CONFLICT = "governed_conflict: rejected"` (C-DEF from the label side) | `test_the_governed_conflict_label_carries_no_raw_marker_or_suffix` | **RED** |
| cand-3 | add a governed-read render `_render_adv_probe(subject)` that OMITS the bound line | `test_every_governed_read_render_calls_render_subject_bound` | **RED** (derivation GREW to include it) |

**C-DEF closed both sides — swept ALL 6 target modules:** every `"governed_conflict:"` occurrence is
either a HYGIENE assert (marker ABSENT from message/label), a FRAGMENT-text assert (the THROW our
code authors — §2.5 point 1, correct), a classifier INPUT fixture, or a comment/docstring. **NO pin
positively asserts the raw underscore marker in an EXCEPTION MESSAGE** — the F1 C-DEF the 1st
adversary found is gone from both the store-layer AND governed-layer sides.

⚠ **cand-3 self-caught P0 control failure (disclosed):** my FIRST cand-3 probe passed the coverage
pin (false clear) — its comment string contained `render_subject_bound`, and the pin's check is a
NAIVE `"render_subject_bound" in inspect.getsource(render_fn)` SUBSTRING (includes comments/
docstrings). A CLEAN probe (no mention anywhere) correctly reds it. So the derivation IS a checked
variable — but see §RESIDUALS R1 for the substring weakness that clean pass exposed.

## §441-436-437-MATRIX (mandate 2 — the wrong-build matrix the 1st adversary never reached)
| # | wrong build (mutation) | pin that MUST red | result |
|---|---|---|---|
| #441 THROW-is-mechanism | `GuardedPlan.fragments` drops the `IF array::len($gw_hit)=0 { THROW }` statement | rescope pin (successor lands beside un-closed pred) | **RED** |
| #441 ledger compensation | `remember` except drops `ledger.delete(memory_id)` | `test_a_failed_successor_create_compensates_the_ledger` | **RED** |
| #441 atomicity (two-txn) | `remember` runs the close in a SEPARATE `_apply` before the create (the OLD shape) | `test_a_failed_successor_create_leaves_the_predecessor_open` | **RED** |
| #441 deny-first | `authorize_guarded` never raises `GovernedDenied` | `test_a_member_superseding_a_foreign_row_denies_with_zero_effect` | **RED** |
| §2.5 rider iv ONE-SOURCE | mutate `_GOVERNED_CONFLICT_MARKER` constant | BOTH the composed rescope pin AND the standalone governed-layer pin | **RED** (both) |
| #436 drop-one-stamp | `_replay_record` passes `scope=None` / `owner_principal=None` / `created_at=now` | fidelity pin, diff NAMES the column (`⟨id⟩.scope: 'server' -> None`, …) | **RED** (each, column-named) |
| #453 revive (supersede) | `_replay_record` drops the composed predecessor-close | `test_a_superseded_predecessor_stays_closed_after_rebuild` | **RED** |
| #453 revive (invalidate) | `invalidate` skips `ledger.retire` | `test_an_invalidated_memory_stays_retired_after_rebuild` | **RED** |
| #437 + F5 DATA | (satisfiability) `_REPLAY_CLOSE_ENTRY` registered + L1-derived once `_replay_record` has the UPDATE literal; widened `_effect_upsert` classifies create+close, rejects a seizure | f5_registration module 9/0 on the reference (ghost pin GREEN) | **GREEN on ref** |

## §436-QUANTIFIER (highest-risk per design §5.1 — the ∀ over lifecycle states)
- **Drop-one-stamp is a REAL ∀ for 6 of 7 columns:** owner_principal, owner_agent, created_at,
  valid_from, valid_until, superseded_by — each dropped/mis-stamped in `_replay_record` reds the
  fidelity diff NAMING the column. Owner is additionally guarded by the diversity pin (2 principals /
  2 agents), so a hardcode reds.
- **VACUOUS for `scope` → THE BLOCKER.** `_seed_dirty_lifecycle` seeds `scope="server"` for ALL 5
  rows. Reproduction (correct-build control = reference passes 80/0):
  - naive `scope="server"` unconditional → LEGACY pin reds (a legacy NONE row would wrongly get
    "server"), so a NAIVE hardcode is caught;
  - **the precise surviving wrong build** `scope = "server" if scope is not None else None` (corrupt
    every non-None scope to "server", None→None) → **FID + LEGACY + ledger-write ALL PASS** (3/0).
    A `keep:`/`agent-private`/`principal-private` memory would rebuild as `server` (a visibility
    WIDENING) and NO pin sees it.
- **Each fate IS exercised** (owned-live, superseded-pair, invalidated, admin-bypass-closed-foreign
  in the fidelity fixture; legacy-NONE in `TestLegacyLedgerRowsReplayFailClosed`) — so the ∀ is not
  fate-vacuous. It is COLUMN-vacuous on `scope` alone, because that column is a value monoculture
  across every exercised fate (the P2 monoculture axis).
- Fix (actionable — probed): seed ≥1 row with a distinct grantable scope + add the scope-diversity
  guard (see SUMMARY MISSING PIN).

## §P1B — QUANTIFIER TABLE (per-invariant ∀-over-inputs vs guarded)
| invariant | ∀ or guarded | receipt |
|---|---|---|
| §2.5 typed conflict at BOTH raise sites | ∀ (parametrized `execute_transaction`/`execute_read_transaction` + `run_query` structural) | F1(b)/cand-2(a) reds |
| §2.5 message hygiene (no raw marker/suffix) | ∀ over message + label + log | F1(a)/cand-2(b') reds; forensics-survive positive control present |
| §2.5 never-retried | guarded-by-verdict, with positive control (retryable DOES retry) | `_rollback_verdict` pin GREEN + control |
| #441 atomicity (close+create) | ∀ over {success, successor-reject} — both fates forced (poison ASSERT + clean control) | atomicity 13/0; two-txn mutation reds |
| #441 ledger compensation | ∀ over {fail→no orphan, success→row present} | compensation drop reds |
| #441 deny-first | ∀ (foreign supersede denies, zero effect) | deny mutation reds |
| #436 fidelity byte-diff | ∀ over rows×columns EXCEPT **scope is a value-monoculture** | drop-one-stamp reds (6/7); **scope corruption survives — BLOCKER** |
| #453 no-revive | ∀ over {invalidated, superseded} — both fates forced | both revive mutations red |
| #437 bound line derived | ∀ (mutation on visible_keep_ids changes the line) | render 9/0; count 2 vs 5 discriminates |

## §P1C — REACH TABLE (every guard/derivation the contract introduces or relies on)
| instrument | reach DERIVED? | coverage a checked var? | effect vs proxy | one-source-by-mutation | verdict |
|---|---|---|---|---|---|
| render-coverage `_governed_read_render_methods()` | DERIVED from `_resolve_subject`-calling AppContext methods → their `_render_*` calls (AST) | YES — a new governed-read render GROWS the set and reds the pin (empirical: clean probe reds) | source-substring PROXY (`"render_subject_bound" in getsource`) — see R1 | n/a | **checked, w/ R1 caveat** |
| L1 site derivation `governed_table_raw_mutation_sites_in_tree` (relied on) | DERIVED (AST grammar; `_REPLAY_CLOSE_ENTRY` site becomes derived only once `_replay_record` has the UPDATE literal — the intended contract-first ghost coupling) | YES — ghost pin RED at HEAD, GREEN on ref | effect (AST literal) | i-a instrument, not mutated here | checked (empirical: ghost pin flips) |
| §2.5 classifier ONE-source (`_GOVERNED_CONFLICT_MARKER`) | single constant both paths consume | n/a | effect | **mutate constant → BOTH paths red** (empirical) | one-source proven |
| §2.5 `_domain_rejection_error` ONE-helper (relied on) | structural (both raise sites' source references it) | source-substring proxy | proxy (`"_domain_rejection_error" in getsource`) | cand-2(a) reds | checked (source-substring — same class as R1) |
| #436 fidelity per-column diff | rows × `_STAMP_COLUMNS` (7) | column-named diff | effect (store re-SELECT) | drop-one reds | checked EXCEPT scope monoculture (BLOCKER) |
| owner-diversity guard | asserts ≥2 principals in the fixture | YES for owner | effect | n/a | checked — **no scope twin (the gap)** |

## §RESIDUALS (individual verdicts — none block, all disclosed)
- **R1 (render-coverage substring proxy):** `test_every_governed_read_render_calls_render_subject_bound`
  and `test_both_domain_raise_sites…one_mapping_helper` both use `"<name>" in inspect.getsource(fn)` —
  a SUBSTRING over source that includes COMMENTS/DOCSTRINGS. A render whose docstring/comment merely
  MENTIONS `render_subject_bound` (or a raise site whose comment mentions `_domain_rejection_error`)
  passes without a real call. Low severity (implausible for an honest builder), but it is a proxy, not
  the effect. Verdict: RESIDUAL, not a blocker; a stronger form would AST-check for an actual Call node.
- **R2 (replay ORDER dependency):** the reference's `_replay_record` composed close relies on the
  predecessor replaying BEFORE the successor (SQLite `all_records()` insertion order). The fixture
  satisfies it (pred remembered before succ). A build/ledger that reordered records would revive a
  pred whose successor replayed first. NOT pinned by the contract; the contract's #453 pins pass on
  insertion order. Verdict: RESIDUAL — a latent bound the contract does not force; flag to the author
  (a pin seeding an out-of-order ledger, or a build that retires pred at supersede time, would close it).
- **R3 (invalidate byte-identity via SDK datetime round-trip):** the reference's `invalidate`
  reads back the server `time::now()` valid_until and stores its ISO; replay re-stamps it. Byte-identity
  HELD empirically (fidelity 13/0), but it rests on the SDK delivering a stamped datetime identically
  to a `time::now()` one. Verdict: RESIDUAL — held in this environment; a builder should be aware
  (a client-computed close ts, as the supersede path uses, is more robust).
- **R4 (i-a ghost pin RED at HEAD is INTENDED):** confirmed — `test_the_replay_close_site_is_registered_
  and_derived` and the i-a ghost pin are RED at HEAD (the #436 close literal is a builder deliverable)
  and GREEN on the reference. This is the contract-first coupling, not a defect. Verdict: correct.

## §SATISFIABILITY-RECEIPT (mandate 3) — see the receipt above (80 passed / 0 failed / no hang;
`loremaster.__file__ = /tmp/lore-adv-63bib2/loremaster/loremaster/__init__.py`; serial `-n0`;
`timeout 600`; :18000). Includes the #436 byte-identity fidelity (GREEN on the correct reference).

## §DISCIPLINE / SCRATCH
- INLINE only — NO nested subagents spawned (the prior stall/wake-chain hazard avoided).
- The committed contract + production were NOT modified. ALL wrong+right builds lived in the scratch
  copy `/tmp/lore-adv-63bib2` (`scratch_copy.sh`, provenance asserted INSIDE the copy). Every mutation
  was backup→patch→run→restore; each restore diff-verified byte-identical to the reference.
- Scratch `/tmp/lore-adv-63bib2` is a disposable `cp` copy (NOT a git worktree); it holds only the
  throwaway reference build. Safe for the lead/operator to `rm -rf` (sandbox may deny it to me).
- pytest ran against the TEST store `:18000` only (never :18500).

## §DISPOSITION
INSUFFICIENT on ONE precise, cheap missing pin (scope diversity in the #436 fidelity fixture). This
is the 2nd i-b contract failure — per the lead's brief the lead escalates the DESIGN at 3, not now.
The fix is a fixture edit + one guard pin, fully within the contract author's authority (the same
shape as the owner-diversity guard already present). Everything else — F1 split, §2.5 typed
classification + hygiene + ONE-source, #441 composed atomicity + compensation + deny-first, #453
no-revive, #437 derived bound + REACH — is satisfiable and robustly pinned (proven by 15 wrong builds
that each red the right pin, plus an 80/0 correct-build reference).
