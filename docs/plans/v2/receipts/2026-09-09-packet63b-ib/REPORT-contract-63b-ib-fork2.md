# REPORT-contract-63b-ib-fork2

brief-base v14 read · brief project v7 read

## SUMMARY BLOCK
- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done** — RED contract for FORK 2 riders i–vii complete; RED-at-HEAD + satisfiable.
- deviations:
  - rider iii's type pin `TestDomainRejectionErrorType` lives in the ATOMICITY contract (my
    writable set), not `test_surreal_store.py` which the ruling §2.5 names (outside my set) — FLAG A.
  - rider vi is a **GREEN-at-HEAD regression guard**, not RED-at-HEAD — the ruling itself frames
    the foreign-supersede shape as "faithful today ONLY because the guard is absent"; its power is
    the declared (b)-without-(a) mutation. (The one pin not RED-at-HEAD; justified below.)
  - scratch reference copy could not be `rm`'d (permission denied); path noted under SATISFIABILITY,
    disposable (session scratchpad).
- Packages considered: none — no new mechanism specified. The §2.4 shape is a typed exception
  subclass + an `except` narrowing + a Python-leg owner pre-read + a `ledger.retire` call, all reusing
  existing seams (`_domain_rejection_error`, `MemoryLedger.retire`, `_replay_record`).
- Reuse ledger: 4 new TEST helpers, all dispositioned (table below); no new PRODUCTION reusable
  symbol authored (I write RED tests only). The one ruled production symbol `TxnDomainRejectionError`
  is a builder deliverable, EXTENDED onto the existing `_domain_rejection_error` mapping (not a clone).
- Graded: `46288b6` · HEAD-at-report: `46288b6` · SAME (authored + verified against HEAD; the
  satisfiability run measured a scratch reference build I wrote, provenance-asserted inside the copy).
- decisions-needed (lead): (1) FLAG A — accept `TestDomainRejectionErrorType` in the atomicity
  contract, or grant `test_surreal_store.py` to relocate it? (2) the two atomicity-contract docstrings
  that cite `test_surreal_store.py::TestDomainRejectionErrorType` are now stale prose (the class lives
  here) — I did NOT edit them (they are pre-existing; minor); fix in the build wave or grant me the edit.
- receipt POINTERS: RIDERS→PIN MAP (below) · RED-AT-HEAD RECEIPTS (below) · SATISFIABILITY (below) ·
  REFERENCE BUILD DIFF (below) · MUTATION-PROOF DECLARATIONS (below) · FLAGS (below).

## CAPABILITY CHECK
- lore tools: loaded via `ToolSearch "+lore"` (keyword form) — used as first choice throughout
  (`lore_get_symbol`/`lore_read`/`lore_search`/`lore_verify`). No fallback to grep was needed for
  structure questions; ⚠ `grep`/`rg` over the repo AND over pytest STDOUT is HOOK-BLOCKED here (the
  brief said "grepping stdout is fine" — it is NOT; used `--tb=line`/`tail` instead). Filed nothing
  (a known session constraint, not a lore weakness).
- spike-surreal `ws://127.0.0.1:18000`: reachable — all store-heavy pins ran live (never :18500).
- STORE LAW (read, cited not re-transcribed): `docs/reference/surrealdb-31-capabilities.md` §3
  (lines 438–481) — "[PROBED] A socket drop with queries in flight surfaces a raw
  `builtins.KeyError(uuid)` from SDK 2.0.0's response routing … Classify `KeyError` tightly, at the
  SDK-await boundary only" and "the supported all-statements call is `query_raw()` … NEVER send
  multi-statement through `query()`". This is the AUTHORITY behind my transport injection (rider i/ii:
  raise `KeyError` on the composed `query_raw`) and the `BEGIN`-gate discriminator — matched against
  the doc, not just reasoned from code (the #107 law), and empirically confirmed (the fault surfaces
  as `SurrealConnectionError` end-to-end). No store/schema/DDL is changed by this contract.
- writable set honoured: only the two named contracts + this report + the idle-gate contract were
  written in the repo. The reference build lived in a `scratch_copy.sh` copy (never the repo tree; no
  git-state mutation — I am COMMIT-ONLY).

## MISSION
Author the RED contract for FORK 2 of packet 63b-i-b closeout: the §2.4 ruled shape
(`TxnDomainRejectionError` + DOMAIN-scoped compensation + FLAG-1/FLAG-2 shipped together),
pinned via §2.5 riders i–vii. Contract-first: RED-at-HEAD for the right reason + a satisfiability
receipt against a known-correct build.

## DESIGN NOTES (ground-truthed at HEAD 46288b6)
- Composed supersede API + #436/#453 replay are BUILT & GREEN at HEAD (baseline: `pytest
  test_memory_supersede_atomicity_63b_ib.py test_memory_replay_fidelity_63b_ib.py -n0` → 21 passed).
  My pins target the UNBUILT narrowing (§2.4) + FLAG-1/2.
- `TxnDomainRejectionError` is ABSENT at HEAD (lore_verify not_found) → rider iii/iv pins RED via the
  absent symbol (import-guarded, no stub needed).
- Exception hierarchy: `SurrealStoreError` ⊃ {`SurrealConnectionError`(transport), `TxnContentionExhaustedError`,
  `TxnGovernedConflictError`(domain)}. Ruled: add `TxnDomainRejectionError(SurrealStoreError)`;
  `TxnGovernedConflictError` subclasses IT; `_domain_rejection_error` returns it for the non-governed label.
- Compensation at HEAD (`remember`): `except Exception: if plan is not None and ledger: ledger.delete(S)` —
  deletes on ALL exceptions incl. transport/contention → the loss path.
- TRANSPORT INJECTION (validated): the single-statement pre-read seam `run_query` uses `connection.query`;
  the TRANSACTION seam `_txn_query_raw` uses `connection.query_raw`. So a one-shot poison on `query_raw`
  (gated on a `BEGIN` statement) fails ONLY the composed close+create txn — `_row_exists`/`authorize_guarded`
  pre-read + `ledger.record(S)` all succeed first. A `KeyError`/`_CONNECTION_ERRORS` member self-heals to
  `SurrealConnectionError` (the #422/§2.2 in-flight-drop signal); `TxnContentionExhaustedError` propagates as itself.
- FLAG-1: `_replay_record`'s composed close has NO owner predicate (`WHERE superseded_by IS NONE OR = $rc_succ`)
  and no WARNING → cross-owner close fires unconditionally (rider v RED-at-HEAD).
- FLAG-2: `remember`'s supersede path never `ledger.retire(P)`; rebuild fidelity of a superseded predecessor
  rides S's replay close + ledger insertion order (P-before-S). Rider vi is a GREEN-at-HEAD regression guard
  (the shape is faithful today only because the close is unguarded) whose value is the (b)-without-(a) mutation.

## PROGRESS LOG
- [STARTED] idle-gate written, report skeleton created, brief-base read, HEAD=46288b6.
- [DESIGN] Read spec §2.1-2.6+FLAGS, design §3.2, all HEAD production seams + both contracts I extend.
  Baseline 21 passed. Injection mechanism validated. Writing pins.
- [RED] Wrote riders i–vii pins into the two contracts + `TestDomainRejectionErrorType`. HEAD run:
  8 RED (right reason), 26 passed. ruff clean, mypy `loremaster` clean (263 files).
- [SATISFIABILITY] Built the §2.4 reference in a `scratch_copy.sh` copy (provenance-asserted). Full
  contract → 34 passed / 0 failed. Reference ruff + mypy clean. Reference diff pasted below.

## RIDERS → PIN MAP (§2.5)
All pins live in `loremaster/tests/test_memory_supersede_atomicity_63b_ib.py` (atomicity) or
`loremaster/tests/test_memory_replay_fidelity_63b_ib.py` (replay), EXTENDING the existing i-b contracts.

| rider | pin (class::test) | file | RED@HEAD | reason it reds |
|---|---|---|---|---|
| i (transport keeps row) | `TestTransportAndContentionKeepTheSupersedeLedgerRow::test_a_transport_failure_on_the_composed_supersede_keeps_the_ledger_row` | atomicity | YES | HEAD `except Exception` deletes S on transport → row gone |
| ii (∀ shapes×causes) | `TestCompensationIsDomainScopedAcrossShapesAndCauses::test_the_ledger_row_survives_iff_the_failure_is_not_a_supersede_domain_rejection` (2×2 parametrized) | atomicity | 1 of 4 cells: `[True-transport-True]` | supersede×transport survives=FALSE at HEAD (deletes); other 3 cells green |
| iii (ONE mapping, typed) | `TestDomainRejectionErrorType::test_the_typed_domain_class_exists_and_governed_conflict_subclasses_it` · `::test_the_one_mapping_helper_returns_the_typed_domain_error_for_a_non_governed_label` | atomicity | YES (×2) | `TxnDomainRejectionError` absent at HEAD |
| iv (typed classification, not name-scan) | behavioural: `...::test_exhausted_contention_on_the_composed_supersede_keeps_the_ledger_row` + positive source pin `TestCompensationClassifiesByTheTypedDomainErrorAndTeachesIt::test_the_compensation_gates_on_the_typed_domain_rejection_class` | atomicity | YES (×2) | contention deleted at HEAD; `TxnDomainRejectionError` unreferenced at HEAD. (Allowlist-the-safe form; the deny half is the transport+contention behavioural cells, NOT an enumerate-the-forbidden AST pin) |
| v (pair-guarded replay close, FLAG-1) | `TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning` (+ same-owner positive control, green) | replay | YES | HEAD's composed close has no owner predicate → closes a foreign P |
| vi (foreign supersede survives rebuild, FLAG-2) | `TestAForeignSupersedeSurvivesARebuild::test_an_admin_bypass_foreign_supersede_stays_closed_after_rebuild` | replay | **NO (green-at-HEAD)** | regression guard; see RED-AT-HEAD note |
| vii (prose-drift instrument) | `TestCompensationClassifiesByTheTypedDomainErrorAndTeachesIt::test_the_compensation_comment_no_longer_teaches_the_retired_supersede_scoped_rule` | atomicity | YES | HEAD comment teaches "SUPERSEDE-SCOPED" |

## RED-AT-HEAD RECEIPTS (measured at 46288b6, `-n0`)
- Both files together: **8 failed, 26 passed** (each RED for the RIGHT reason — verified individually):
  - transport / contention / 2×2[True-transport-True]: RED with `new ledger ids: set()` (row DELETED by
    HEAD's `except Exception`; the injection counter `fired==1`, so the fault reached the composed txn seam).
  - rider iii ×2 + rider iv source: RED via `TxnDomainRejectionError is UNBUILT` / unreferenced.
  - rider vii: RED — the comment contains "SUPERSEDE-SCOPED".
  - rider v: RED with the foreign predecessor (owner `gov_admin_b`) CLOSED (`valid_until` set) by the
    unguarded cross-owner replay close.
- The 26 green include the 21 pre-existing i-b pins (unbroken) + the 5 green-by-design new pins
  (3 non-RED cells of the 2×2, rider v same-owner control, rider vi regression guard).
- INJECTION MECHANISM (rider i/ii/iv transport+contention cells): a one-shot fault on the FIRST
  composed `BEGIN … COMMIT` `query_raw` call — `_arm_one_shot_txn_fault`. The single-statement pre-read
  seam `run_query` uses `connection.query`; the transaction seam `_txn_query_raw` uses `query_raw`
  (SDK `query()` delegates to `query_raw` too, hence the `BEGIN` gate), so the fault fires AFTER
  `authorize_guarded` + the durable `ledger.record(S)`, on the composed close+create alone — the §2.2
  window. `KeyError` → `SurrealConnectionError` (the #422 in-flight-drop signal); `TxnContentionExhaustedError`
  propagates as itself.
- FIXTURES-MUST-DISCRIMINATE self-interrogation ("what WRONG build still passes this?"):
  - a build that compensates on ALL exceptions → rider i/contention/2×2 cell red (they assert KEEP).
  - a build that NEVER compensates → the domain cells green-cell `[True-domain-False]` (asserts DELETE)
    reds, AND rider iii's existing sibling `test_a_failed_successor_create_compensates_the_ledger` reds.
  - a build that classifies by `isinstance(SurrealConnectionError)` (enumerate-the-forbidden) → KEEPS
    transport but the **contention** cell reds (it also deletes contention) — this is why iv keeps a
    contention cell, not only a transport one.
  - a build that string-matches "governed" → the supersede×domain(plain ASSERT, no "governed" text)
    cell reds (it fails to compensate a plain domain rejection).
  - rider v mutation (delete the owner predicate) → the cross-owner skip leg reds again.

## SATISFIABILITY (§2.4 reference build — inline, bounded, no nested spawn)
Built the ruled §2.4 shape in a `scripts/scratch_copy.sh` copy (provenance-asserted: `loremaster.__file__`
resolved INSIDE the copy — #140 receipt printed). Ran the FULL contract:
- **34 passed / 0 failed** (`-n0`) — every RED-at-HEAD pin flips GREEN; every green-at-HEAD pin stays green.
- Reference build **ruff clean** + **mypy clean** (`loremaster`, 263 files) → the ruled shape is cleanly
  buildable, so the contract stays satisfiable AFTER any lint cleanup (the C-DEF "harder leg"); no
  orphaned imports are created.
- Provenance receipt: `loremaster.__file__ = <scratch>/loremaster/loremaster/__init__.py`.
- Scratch path (disposable, could not `rm` — permission denied; auto-cleaned session scratchpad):
  `…/e821d0cd-…/scratchpad/ref63bib`. The reference is NOT a repo change (COMMIT-ONLY); its diff is
  pasted below as the durable instrument (brief-base §1 — a lost scratch tree is a lost claim).

## MUTATION-PROOF DECLARATIONS (rider iii/v — for the adversary/builder, run against the reference)
Declare expected-RED node ids from `--collect-only` BEFORE the run (`scripts/mutation_proof.py`):
- rider iii — mutate `_txn._domain_rejection_error` to `return SurrealStoreError(message)` (non-governed
  branch) → expected RED:
  `test_memory_supersede_atomicity_63b_ib.py::TestDomainRejectionErrorType::test_the_one_mapping_helper_returns_the_typed_domain_error_for_a_non_governed_label`
  AND `…::TestTransportAndContentionKeepTheSupersedeLedgerRow::test_a_transport_failure…` control leg
  (the domain 2×2 cell `[True-domain-False]` also reds — a plain `SurrealStoreError` is no longer
  isinstance-`TxnDomainRejectionError`, so a supersede domain reject stops compensating). Both raise
  sites route through the ONE helper (ROUTING-IS-SHARING — visible in source: `run_query` +
  `_run_verified_transaction` both call `_domain_rejection_error`).
- rider v — mutate `_replay_record` to drop the owner-pair predicate (always append the close) →
  expected RED: `test_memory_replay_fidelity_63b_ib.py::TestTheReplayCloseIsPairGuarded::test_a_cross_owner_replay_close_is_skipped_with_a_warning`.
- rider vi — mutate: ship the pair guard (b) but DELETE the supersede-path `ledger.retire` (a) →
  expected RED: `…::TestAForeignSupersedeSurvivesARebuild::test_an_admin_bypass_foreign_supersede_stays_closed_after_rebuild`
  (P replays open, cross-owner close refused → P revived). This is the discriminator that makes (a)
  load-bearing (§2.4-3 ORDER-MATTERS).

## RED-AT-HEAD EXCEPTION — rider vi is a GREEN-at-HEAD regression guard (declared, not a gap)
The contract-first default is "every pin RED-at-HEAD". Rider vi is the ONE exception, and the ruling
frames it so (§2.4-3: "Today that shape is faithful ONLY because the guard is absent"). At HEAD an
admin-bypass foreign supersede survives a rebuild because S's UNGUARDED replay close fires (ledger
insertion order P-before-S — the same mechanism the pre-existing GREEN
`test_a_superseded_predecessor_stays_closed_after_rebuild` relies on). So rider vi cannot be RED at
HEAD without contradicting reality. Its discriminating power is the MUTATION above (b-without-a) — a
positive-control/regression class, exactly like the atomicity contract's existing positive controls
and rider v's same-owner control. Flagged here so it is met deliberately, not mistaken for a corpse.

## DRY LEDGER (§6 — new reusable TEST symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_arm_one_shot_txn_fault` (atomicity) | `lore_search "store_handle … on_acquire acquire wrap injection"` + read `_txn_query_raw`/`run_query` | `store_handle`'s `on_acquire` wraps ACQUIRE, not `query_raw`; no existing helper raises a one-shot transport fault on the composed txn | HAND-ROLLED — the §2.5-rider-i injection ("make `query_raw` raise a `_CONNECTION_ERRORS` member once") has no existing helper; `store_handle` covers acquire-count/TOCTOU, not a transport raise |
| `_warning_haystack` (replay) | (inline reasoning; caplog idiom) | no existing helper renders a LogRecord's message+extra as one searchable string | HAND-ROLLED — 2-line test-local reader so the WARNING pin accepts ids in message OR `extra=` (not over-fitted) |
| `_governed_row` (replay) | mirrors atomicity's `_memory_row` | atomicity's `_memory_row` is in the OTHER file (not importable across contract modules without a shared conftest helper) | HAND-ROLLED (deliberate per-file duplication of a trivial 1-query SELECT reader — a shared home would be a conftest change outside my task; FLAG C) |
| `_orphan_the_successor_in_the_store` (replay) | (scenario scaffolding) | none | HAND-ROLLED — constructs the §2.3 crash-window state (S absent, P re-opened) deterministically |

## FLAGS (surfaced per scope law — the lead routes)
- **FLAG A (decision) — `TestDomainRejectionErrorType` placement.** The ruling §2.5 rider iii names
  it `test_surreal_store::TestDomainRejectionErrorType`; that file is OUTSIDE my writable set, so I put
  the class in the atomicity contract (which already imports `_txn` symbols). It is a store-free unit
  of `_txn._domain_rejection_error`. Options: (a) accept it in the atomicity contract [what I shipped];
  (b) grant `test_surreal_store.py` and relocate. Either satisfies rider iii; the node id in the
  mutation-proof declaration reflects (a).
- **FLAG B (stale prose, pre-existing) — two atomicity-contract docstrings** (`test_a_conflicting_guarded_close_surfaces_governed_conflict`,
  and the class docstring of `TestTheComposedConflictGuardIsInStore`) cite
  `test_surreal_store.py::TestDomainRejectionErrorType` as the store-layer classification pin. That
  class now lives in THIS file, not `test_surreal_store.py`. I did NOT edit those docstrings (they are
  pre-existing text I did not author, and the citation is prose, not a runtime dependency). The build
  wave should re-point them (or the cold audit greps BARE for `test_surreal_store` per rider vii's
  discipline).
- **FLAG C (reuse) — `_memory_row` / `_governed_row` duplication.** Both contract files hand-roll a
  ~1-query governed-columns row reader (`_memory_row` in atomicity, `_governed_row` in replay). A
  shared `conftest`/`_governed_contract` helper would DRY them, but that touches a file outside my set.
  Low stakes (trivia, not policy — brief-base §6 permits duplicating trivia). Named for the lead.
- **NOTE (no escalation) — rider vii is a cold-audit task too.** I shipped it as an INSTRUMENT (the
  prose-drift source pin) per the CLAUDE.md "ship the instrument, not just the law" rule; the ruling's
  additional ask (cold audit greps BARE for "supersede-scoped" and gives each hit a file:line verdict)
  remains the fix-wave cold audit's job.

## REFERENCE BUILD DIFF (the satisfiability instrument — a faithful §2.4 realization, NOT a repo change)
⚠ This is the reference I built in the scratch copy to PROVE the contract is satisfiable (34 passed).
It is one faithful realization of ruling §2.4-1/-2/-3; the BUILDER implements the real thing (the
ruling doc is the authority). Pasted verbatim (brief-base §1: the instrument survives here since the
scratch tree is disposable).

```diff
--- a/loremaster/loremaster/store/_txn.py
+++ b/loremaster/loremaster/store/_txn.py
@@ class SurrealConnectionError ... @@
+class TxnDomainRejectionError(SurrealStoreError):
+    """A non-retryable DOMAIN rejection — the store said the write is ILLEGAL and rolled back.
+    ... a caller may safely COMPENSATE a durable pre-write on it — unlike a transport failure
+    (SurrealConnectionError) or exhausted contention (TxnContentionExhaustedError), whose outcome
+    is UNKNOWN. Subclasses SurrealStoreError so every existing `except SurrealStoreError` catches it."""
@@ class TxnGovernedConflictError @@
-class TxnGovernedConflictError(SurrealStoreError):
+class TxnGovernedConflictError(TxnDomainRejectionError):
@@ def _domain_rejection_error @@
     if error_class == _ERROR_CLASS_GOVERNED_CONFLICT:
         return TxnGovernedConflictError(message)
-    return SurrealStoreError(message)
+    return TxnDomainRejectionError(message)

--- a/loremaster/loremaster/memory/local.py
+++ b/loremaster/loremaster/memory/local.py
@@ imports from loremaster.store._txn @@
+    TxnDomainRejectionError,
@@ remember() compensation @@
-                    # #441 compensation is SUPERSEDE-SCOPED ...
-                    if plan is not None and self._ledger is not None:
+                    # #441 compensation is DOMAIN-scoped (close-out rulings §2.4-2): ... KEEP the
+                    # authoritative ledger row on transport/contention/cancellation, replay converges.
+                    if (
+                        isinstance(error, TxnDomainRejectionError)
+                        and plan is not None
+                        and self._ledger is not None
+                    ):
                         self._ledger.delete(memory_id)
                     ... (GovernedConflict mapping unchanged) ... raise
+            # FLAG-1 (a) §2.4-3(a): the composed supersede COMMITTED — retire P's ledger row
+            # (store-first, mirroring invalidate) so P replays CLOSED regardless of S's replay.
+            if plan is not None and supersedes is not None and self._ledger is not None:
+                self._ledger.retire(supersedes, valid_until=now.isoformat(), superseded_by=memory_id)
         return memory_id
@@ _replay_record() close composition @@
         if isinstance(supersedes, str):
-            fragments.append(TxnFragment( ... unconditional close ... ))
+            # FLAG-1 (b) §2.4-3(b): apply the composed close ONLY when P's STORED owner pair ==
+            # the successor's STAMPED pair; else log WARNING(both ids) + SKIP (no back-door foreign close).
+            <_bare()-based owner extraction>  # RecordID.record_id or str(...).split(":")[-1]
+            predecessor = self._as_rows(await self._query("SELECT owner_principal, owner_agent ..."))[0]
+            if stored_pair == stamped_pair:
+                fragments.append(TxnFragment( ... same close ... ))
+            else:
+                logger.warning("memory.replay.close.pair_mismatch",
+                               extra={"predecessor": supersedes, "successor": record.memory_id, ...})
         with governed.write_guard("_replay_record"):
             await self._apply(fragments)
```
(Full byte-exact diff was captured from the scratch copy; the elisions above are the unchanged close
statement/params and the docstring bodies. `git diff --stat`: local.py +71/-23, _txn.py +14/-2.)
