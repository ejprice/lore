# Packet 63b — i-b close-out rulings (design-sidecar-63b-s2, 2026-09-08)

`brief-base v14 read` · brief project v7 read

Status: FORKS 1, 2, B and FORK-2/B1 RULED (2026-09-08/09, graded at `c658781`; B1 measured against the adversary's reference at `98cf52c`). Standing by for 63b-ii/iii follow-ups. Authority per operator
delegation: this doc IS the ruling for 63b; the lead implements it.

## FORK 1 — Class D delete-vs-update

**VERDICT: DELETE the CLASS `TestEveryRawMemoryMutationIsAllowlisted` (5 tests) — NOT the module, NOT a
data UPDATE.** Every virtue it certifies is preserved by a strictly-stronger, already-GREEN pin elsewhere
(inventory below, one row per test). UPDATE-the-DATA is REJECTED on ONE-IMPLEMENTATION grounds: it would
keep a SECOND memory allowlist (`63a_iv::MEMORY_WRITE_ALLOWLIST`, 3 entries, local.py-scoped) beside the
canonical `63b_ia::MEMORY_TREE_ALLOWLIST` (7 entries, whole-tree) — and the two have ALREADY diverged
(the tree list carries `_REPLAY_CLOSE_ENTRY`; the twin does not), which is exactly the drift the law
predicts. A whole-MODULE delete is REJECTED for i-b close because the module carries two live
couplings (§1.3) that must be relocated first — ruled as the follow-up end state, not the D fix.

Measured 2026-09-08 at `c658781`: `uv run python -m pytest loremaster/tests/test_memory_enforcement_63a_iv.py -n0`
→ **3 failed, 6 passed** — the 3 reds are all in the ruled class; the 6 greens are the other three classes
plus the class's own V3/V4 (both superseded, see table).

### 1.1 Removed-behavior inventory (CLAUDE.md rename/reshape law — item-by-item adjudication)

Sources read in full: `loremaster/tests/test_memory_enforcement_63a_iv.py` (296 lines);
`test_memory_enforcement_63b_ia.py` (allowlist DATA + `TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries`,
`TestCoverageIsACheckedVariableOverTheRuntimeObservedFrames`, `TestGuardedWriteIsAnAllowlistedLabelFrame`,
`TestEveryAllowlistEntryHasARealEvidencingPin`, `TestL1IsACoverageFloorWithADerivedGrammar`);
`test_memory_enforcement_63a_v.py::TestTheWholeTreeReachIsAnOutput` (+ its pin-existence leg);
`test_memory_supersede_atomicity_63b_ib.py` (deny-first, in-store conflict, rider-vi structural);
`test_memory_f5_registration_63b_ib.py::TestTheReplayCloseSiteIsRegistered`;
`_governed_contract.governed_table_raw_mutation_sites` / `_in_tree` / `governed_table_guarded_write_frames`
(via `lore_get_symbol`).

| # | virtue certified by the OLD test | new-world pin that preserves it | adjudication |
|---|---|---|---|
| V1 | `test_the_derived_raw_mutation_set_is_non_empty_and_is_the_known_set` — (a) scan anti-vacuity, (b) EXACT-SET equality of local.py's raw-mutation set against a known set (an added OR removed site reds) | (a) `63b_ia::TestL1CoverageIsDenyByDefaultOverTheSiteBackedEntries::test_every_derived_site_is_in_a_site_backed_entry_and_no_ghost` asserts `derived` non-empty; (b) the same test's `orphans == ∅ ∧ ghosts == ∅` IS exact-set equality (A==B ⟺ A−B=∅ ∧ B−A=∅), over the WHOLE TREE (⊇ local.py) against `L1_ALLOWLISTED_SITES`; twin: `63a_v::TestTheWholeTreeReachIsAnOutput::test_the_whole_tree_derived_set_is_the_known_four_sites` asserts `derived == L1_ALLOWLISTED_SITES` literally | **PRESERVED-WITH-PIN** (strictly stronger scope; identical predicate). The old pin is RED today precisely because it certifies the pre-i-b set — the corpse case. |
| V2 | `test_every_derived_raw_mutation_site_is_in_the_allowlist` — deny-by-default containment (no orphan) + no ghost, local.py | same two tests as V1 (orphan/ghost legs), whole-tree | **PRESERVED-WITH-PIN** |
| V3 | `test_a_synthetic_new_raw_mutation_site_grows_the_derived_set_and_reds` — GROWS-AND-REDS discriminator for the statement-shape scanner (a synthetic new function with a raw `UPDATE type::record('{MEMORY_TABLE}'…)` is derived and is not allowlisted) | `63a_v::test_a_governed_write_in_any_member_grows_the_reach_and_the_scan_is_precise` (synthetic workspace: a new `_do_write` UPDATE in TWO members is derived; SELECT-only / concat / test-tree are not — grows-and-reds PLUS precision); positive control on the SAME per-file scanner: `test_memory_enforcement_bounds_63a_iv.py::TestL1IsBlindToADynamicallyNamedGovernedWrite::test_a_constant_named_raw_memory_write_is_derived`. `_in_tree` delegates per-file to `governed_table_raw_mutation_sites` (ONE implementation — its docstring says so), so the discriminator reaches the same code. | **PRESERVED-WITH-PIN** (GREEN today; superseded, not lost) |
| V4 | `test_every_allowlist_entry_has_a_real_evidencing_pin` — pin-existence over the (old) allowlist | `63b_ia::TestEveryAllowlistEntryHasARealEvidencingPin::test_every_entry_pin_is_a_defined_test` + `63a_v::TestMigrateGovernedIsAnEvidenceBackedTriple::test_every_tree_allowlist_entry_has_a_real_evidencing_pin`, both over `MEMORY_TREE_ALLOWLIST`, whose upsert/reinforce/recreate pins are the SAME three names the old list carries | **PRESERVED-WITH-PIN** (GREEN today) |
| V5a | `test_the_guarded_write_frames_are_derived_and_are_not_raw_sites` leg (a): `{invalidate, remember} ⊆` functions calling `guarded_write(table=MEMORY_TABLE)` — "the supersede-close in `remember` is GUARDED" | The predicate is FALSE BY DESIGN in the new world (design §2.2 step 3–4: `remember` composes `authorize_guarded` + `plan.fragments`, never `guarded_write`). Its INTENT — remember's close is authorized deny-first and conflict-guarded — is pinned BEHAVIOURALLY: `atomicity::TestAuthorizeGuardedIsDenyFirst::test_a_member_superseding_a_foreign_row_denies_with_zero_effect`, `TestTheComposedConflictGuardIsInStore::test_a_conflicting_guarded_close_surfaces_governed_conflict`, `TestSupersedeIsAtomicUnderSuccessorFailure::*`; at the F5 seam: `f5_registration::TestAComposedSupersedeIsOneObservedWriteUnderRemember::test_the_supersede_close_is_composed_under_the_remember_label`; structurally for the shared seam: `TestSupersedeAndInvalidateShareOneImplementation::test_both_close_paths_route_through_authorize_guarded`. A wrong build that closes the predecessor with a raw UPDATE in `remember` also reds V1/V2's twins (a new orphan site). | **DROPPED-DELIBERATELY** — the old assertion certifies the retired two-transaction shape; the behavioural pins above are stronger than a call-name scan (a call-name scan is the enumerate-by-NAME reach the instrument lesson warns against). ⚠ Optional cheap keep (NOT required for D-close): widen `_governed_contract.governed_table_guarded_write_frames` to recognise `authorize_guarded` beside `guarded_write` and assert `{invalidate, remember} ⊆` it from the tree allowlist's frames — only worth doing if the follow-up (§1.3) keeps a structural guarded-consumer leg at all. |
| V5b | same test, leg (b): `invalidate` carries NO raw memory mutation | Implicit-but-discriminating in V1/V2's twins: a raw site inside `invalidate` derives as `(local.py, invalidate, <verb>)`, which is in no site-backed entry → orphan → RED. | **PRESERVED-WITH-PIN** (via deny-by-default; no separate assertion needed) |

No row is `spec-silent`; no `old-bug`. Every virtue is either preserved by a GREEN pin or is a certificate of
the retired shape whose intent is pinned behaviourally. That satisfies the DELETE bar the brief set.

### 1.2 THE D FIX — exact mechanical edit (routes to a builder; test file, outside i-b's production set)

In `loremaster/tests/test_memory_enforcement_63a_iv.py`:
1. Delete `class TestEveryRawMemoryMutationIsAllowlisted` (the whole class, lines 116–195 at `c658781`).
2. Delete the now-unused module constant `_KNOWN_RAW_SITES` (used only by V1).
3. Delete `_defined_test_names()` (module tail; used only by V4) — and, because that helper is the
   subject of the module's parse-skip entry in `test_ast_reach_helpers.py` (`"test_memory_enforcement_63a_iv.py": (…"_defined_test_names"…)`),
   the builder MUST confirm `TestTheParseSkipSetIsACheckedVariable::test_the_parse_skip_allowlist_carries_no_dead_entries`
   stays GREEN after step 3; if that pin keys on the helper's presence, the entry is removed in the same
   edit (one concern: "63a_iv no longer enumerates the test tree"). Either way the outcome is pinned by
   running `test_ast_reach_helpers.py` in the fix wave's gate.
4. Update the module docstring's "THREE layers" preamble: L1 is no longer in this module — point at
   `test_memory_enforcement_63b_ia.py` / `63a_v` as the L1 home (a docstring teaching a deleted layer is
   the P8d prose-drift class).
5. Keep `MEMORY_WRITE_ALLOWLIST` / `MEMORY_F5_CASE` FOR NOW — they still feed the GREEN L2a class
   (`TestEveryAllowlistedFrameSetsAWriteGuardContext`). Their retirement is §1.3.
6. Gate for the fix: `pytest loremaster/tests/test_memory_enforcement_63a_iv.py loremaster/tests/test_memory_enforcement_63b_ia.py loremaster/tests/test_memory_enforcement_63a_v.py loremaster/tests/test_ast_reach_helpers.py -n0` → the 63a_iv module must report **6 passed, 0 failed** (a passed-COUNT, per the piped-run law) and the other three unchanged-green.

Rider (pin it like this): none new — the D fix REMOVES a corpse; the invariant it removed is already pinned
twice (V1/V2 twins). The mutation proof the fix wave owes is the EXISTING one: plant a synthetic raw
`UPDATE` in a new `local.py` function in a scratch copy → `63b_ia::test_every_derived_site_is_in_a_site_backed_entry_and_no_ghost` and `63a_v::test_the_whole_tree_derived_set_is_the_known_four_sites` both RED (proves the surviving instrument, not the deleted one, is the deny-by-default gate).

### 1.3 The couplings that FORBID a whole-module delete today — and the ruled END STATE (follow-up, not D)

Derived by a textual scan of `loremaster/**/*.py` + `docs/**/*.md` for the module name and its exported
names (fallback SAID OUT LOUD: `lore_impact` cannot resolve the test module by qualified name — filed as
friction below; a deletion gate is exhaustiveness, grep-class case (a) of the dogfood protocol):

- **C1 — the recreate pin lives here.** `TestRecreateMemoryTableIsBootAdminOnly::test_recreate_memory_table_is_reachable_only_from_rebuild_embeddings`
  (63a_iv line 203) is the `pin=` of the CANONICAL `63b_ia::_RECREATE_ENTRY` (line 356). Deleting the
  module reds `63b_ia::test_every_entry_pin_is_a_defined_test` AND `63a_v::test_every_tree_allowlist_entry_has_a_real_evidencing_pin`.
  END STATE: MOVE that test (verbatim) into `test_memory_enforcement_63b_ia.py` beside
  `TestEnsureReadyIsAnAllowlistedDdlFrame::test_recreate_entry_is_runtime_observed` (the entry's other leg).
- **C2 — the parse-skip entry** in `test_ast_reach_helpers.py` names `test_memory_enforcement_63a_iv.py`
  (its `_defined_test_names` enumeration). A module delete leaves a DEAD entry →
  `test_the_parse_skip_allowlist_carries_no_dead_entries` reds. END STATE: delete the entry in the same
  commit as the module.
- **C3 — L2a over the TWIN allowlist.** `TestEveryAllowlistedFrameSetsAWriteGuardContext::test_every_allowlisted_local_frame_calls_write_guard`
  derives its frame set from `MEMORY_WRITE_ALLOWLIST` (the 3-entry twin). Its reach is therefore a
  HIDDEN CONSTANT relative to the canonical list — a frame added only to `MEMORY_TREE_ALLOWLIST` is never
  checked here (INSTRUMENT 0's exact shape). Is L2a still needed at all? `TreeWriteAllowlistEntry.runtime_observed`
  defaults True and `63b_ia` flipped `_RECREATE_ENTRY` to True (§5.1 Q1); every memory entry is therefore
  runtime-observed, and `63b_ia::TestCoverageIsACheckedVariableOverTheRuntimeObservedFrames` proves every
  frame is OBSERVED WITH A LABEL under the battery — a label exists only if `write_guard` was entered,
  so the runtime leg SUBSUMES L2a for the memory table (the remaining structural leg for `guarded_write`
  is already `63b_ia::test_guarded_write_carries_its_label_and_one_row_effect` (a)). END STATE: delete
  `TestEveryAllowlistedFrameSetsAWriteGuardContext`, `MEMORY_WRITE_ALLOWLIST`, `MEMORY_F5_CASE`.
  ⚠ Named bound the END STATE inherits: `TreeWriteAllowlistEntry`'s docstring still teaches
  "`_recreate_memory_table` / `_replay_record` … `runtime_observed=False`" — stale prose since §5.1 Q1
  (the P8d class); fix it in the same sweep.
- **C4 — the L2b mechanism hasattr test** (`TestEveryObservedMemoryMutationCarriesAGuardContext::test_the_guard_context_mechanism_is_built`)
  is subsumed by every `63b_ia` runtime pin (they call `write_guard`/`active_write_guard` live). Delete with the module.
- **C5 — substrate leftovers** in `_governed_contract.py` once C3 lands: `GovernedWriteAllowlistEntry`,
  `MutationSite` (still returned by the per-file scanner — KEEP), `governed_table_guarded_write_frames`
  (`lore_impact`: 0 prod / 1 test ref → dead after the class delete), `function_calls_write_guard`
  (0 prod / 2 test refs, a one-line delegate to `function_calls_named` → dead after C3),
  `GovernedTableCase.mutation_source` / `.write_allowlist` fields. Retire in the same sweep or ledger them;
  the docstring "64 builds a TASK_F5_CASE … the SAME way" must be re-pointed at the TREE allowlist shape
  (`TreeWriteAllowlistEntry`) — otherwise 64 clones the retired shape.

**Recommended routing (lead's call — wave structure is not mine):** ship §1.2 (the class delete) in the
i-b close-out fix wave — it is the D fix and it is safe alone. Ship §1.3 C1–C5 as ONE small
"retire the 63a_iv twin" commit either in the same wave (same builder, +3 test files) or as the first
63b-ii prelude; it must not be left un-ledgered (deferral law: named owner + decision point). Either
way, **63a_iv's `MEMORY_WRITE_ALLOWLIST` must never be UPDATED again** — a new memory site is adjudicated
in `MEMORY_TREE_ALLOWLIST` only.

## FORK 2 — C-residual compensation scope

**VERDICT: NARROW the #441 ledger compensation to DOMAIN-REJECTION-ONLY — compensate iff the STORE
REJECTED the composed write (a typed domain rejection: ASSERT / coercion / `GovernedConflict` / any
engine `ERR` the rollback verdict classifies as non-retryable); KEEP the ledger row on every other
failure (transport, exhausted contention, cancellation, anything whose outcome is not a store
rejection).** The committed supersede-scoped-on-ALL-exceptions fix is SOUND against the FP-06 test and
is a legitimate stopgap for i-b, but it is not the design end state, because it carries a permanent-loss
path the LOW-window framing does not describe (§2.2 below). Timing (fix-wave vs 63b-ii prelude) is the
lead's; the design is ruled. If the lead closes i-b on the stopgap, the bound is PINNED + ledgered as
§2.5 specifies — never left as prose.

### 2.1 What the code does at `c658781` (read via `lore_get_symbol`, not the report)

`LocalMemoryBackend.remember` (`memory/local.py`): `authorize_guarded` → `ledger.record(S)` → embed →
`with write_guard("remember"): try: await self._apply([*plan.fragments(close), upsert(S)]) except
Exception as error: if plan is not None and ledger: ledger.delete(S); (map TxnGovernedConflictError →
GovernedConflict); raise`. `_apply` → `execute_transaction` → `_run_verified_transaction`, whose raise
surface is exactly three types (docstring + code): `SurrealConnectionError` (transport — `_txn_query_raw`,
after `drop` self-heal), `TxnContentionExhaustedError` (a retryable conflict that outlived the budget),
and the DOMAIN rejection built by `_domain_rejection_error(error_class, msg)` — `TxnGovernedConflictError`
for the governed-conflict label, else a PLAIN `SurrealStoreError`. All three subclass `SurrealStoreError`;
the domain case is the only one with NO type of its own. **That is the seam the narrowing needs and it is
already the §2.5 ONE-mapping helper — widening it is the whole classify-seam change.**

### 2.2 Why ALL-exceptions is wrong for a SUPERSEDE, precisely (not "recoverable, so keep")

The brief framed the residual as *"transport is recoverable, so deleting loses a recoverable write"*. That
is true but it is the weaker half. The load-bearing half is **OUTCOME KNOWLEDGE**:

- A DOMAIN rejection has a KNOWN outcome: the engine said `ERR`, the txn rolled back, nothing landed, and
  (per `execute_transaction`'s own contract) *"retrying it would never succeed"*. The ledger row is a
  promise the store will NEVER honour → compensate. Correct, keep it.
- A TRANSPORT failure has an UNKNOWN outcome. Store-ref §3 [PROBED, re-probed 2026-08-05 on 3.2.4]: a
  socket drop with a query in flight surfaces as `KeyError(uuid)` → `SurrealConnectionError` — **after the
  frame was sent**. The `COMMIT` may have been applied server-side with the response lost. Then the store
  HAS S and P-closed, and the compensation DELETES S's ledger row. The ledger is AUTHORITATIVE (design
  §2.3, verbatim: *"the ledger is written first and is AUTHORITATIVE; the store CONVERGES to it by
  replay"*), and `rebuild_embeddings` — reached from `server.py` on an embedding-schema mismatch at boot
  (design §3.1: *"AUTO-RUNS on any embedding-schema change at boot"*) — DROPS the table and replays the
  ledger: **S is gone for good, and P is REVIVED** (P's ledger row is never retired on supersede — see
  FLAG-2). The rebuild reports success. That is a Leg-2 false clear (dependency = store transport × verb
  = partial) with a silent, permanent consequence — the trust doctrine's one unacceptable shape.
- And the FP-06 law itself: "the ledger is the copy a Surreal failure cannot touch" is pinned ∀ remembers
  but constructed only for the PLAIN case; a supersede under the same #422-class WS reset that a plain
  remember survives silently gets the OPPOSITE behaviour. That is THE QUANTIFIER LAW's exact failure —
  an invariant conditioned on the one shape the fixture happened to force.

So the correct rule is not transport-vs-domain; it is **compensate ONLY when the store's own verdict says
the write is illegal; on unknown-or-legal-but-unlanded, keep the row and let replay converge.** Keep is
the DEFAULT (allowlist the safe set: the one typed domain class; never enumerate the transport shapes).

### 2.3 Does §3.2 replay actually handle the kept orphan faithfully? (the brief's central question)

Read `_replay_record` + `restore_from_ledger` at `c658781`:
- **Transport-aborted supersede, nothing landed:** store has P OPEN, S absent; ledger has S with
  `supersedes=P`, owner pair, created_at. Next `restore_from_ledger` (boot, `server.py`) replays ids
  ABSENT from the store → `_replay_record(S)` composes `UPSERT S` + `UPDATE type::record('memory',$rc_pred)
  SET valid_until=$rc_close_ts, superseded_by=$rc_succ WHERE superseded_by IS NONE OR superseded_by=$rc_succ`
  into ONE txn with `rc_close_ts = S.created_at` → S lands, P closed with byte-identical stamps. **Faithful.**
  An agent retry before the boot is also safe: `MemoryLedger.record` is `INSERT … ON CONFLICT DO UPDATE`
  (idempotent on the deterministic id), the txn lands, one ledger row.
- **Transport failure AFTER a server-side commit (lost response):** store has S and P closed → S is not
  absent → no replay → consistent. Faithful ONLY because the row was KEPT.
- **`GovernedConflict` ("row moved") orphan:** a DOMAIN rejection → still compensated immediately under
  this ruling; only the §2.3 crash window (~ms) can leave it — unchanged from today.
- **⚠ The pair-match guard the design relies on is NOT BUILT.** Design §3.2: *"applied ONLY when P's
  stored owner pair equals the record's stamped pair. A pair mismatch … is NOT re-applied — logged
  WARNING with both ids"*, and §2.3's crash-window safety claim rests on it (*"a conflict-because-the-
  row-moved orphan cannot close a now-foreign row by the back door"*). The composed close's WHERE
  carries ONLY the idempotency clause; no owner predicate; no WARNING; no pin in
  `test_memory_replay_fidelity_63b_ib.py` (its dirty world's `pred`/`succ` share one owner, and its
  "foreign" row is an `invalidate` bypass, which retires via P's OWN ledger row). **This is a DROPPED
  RIDER at HEAD regardless of this fork** — FLAG-1 below. Consequence for THIS fork: narrowing widens
  the kept-orphan lifetime from ~ms to until-next-restore, so the pair guard goes from belt to
  load-bearing IF an owner-mutating path exists. I know of none in production (owner columns are set at
  create; `migrate-governed` touches NONE-scope rows' scope only) — **LOW confidence, unverified**;
  therefore the ruling ships the guard WITH the narrowing rather than betting on that.

### 2.4 THE RULED SHAPE (design; the lead routes it — `_txn.py` §2.5-scoped + `local.py`, contract tests)

1. **`_txn.py` (§2.5 seam widened by ONE type):** add `class TxnDomainRejectionError(SurrealStoreError)`
   (generic message, no text-parsed attrs — the hygiene boundary is unchanged) and make
   `TxnGovernedConflictError` subclass IT. `_domain_rejection_error` returns `TxnGovernedConflictError`
   for the governed label and `TxnDomainRejectionError` otherwise — it remains the ONE mapping and both
   raise sites (`run_query`, `_run_verified_transaction`) inherit the change with zero edits
   (ROUTING-IS-SHARING, proven by mutation in rider iii). Every existing `except SurrealStoreError`
   keeps catching it (same argument the `TxnContentionExhaustedError` docstring makes).
2. **`local.py` compensation site:** replace `if plan is not None and self._ledger is not None:
   self._ledger.delete(memory_id)` with `if isinstance(error, TxnDomainRejectionError) and plan is not None
   and self._ledger is not None: self._ledger.delete(memory_id)` — i.e. compensate iff (composed supersede)
   ∧ (typed domain rejection). Rewrite the comment: it currently teaches "SUPERSEDE-SCOPED … FP-06"; it
   must teach "DOMAIN-scoped: a store rejection is a promise the store will never honour → compensate; an
   unknown/unlanded outcome keeps the authoritative row and replay converges (§2.3 of the close-out
   rulings)". The `plan is not None` guard STAYS (a plain remember has no orphan-successor semantics; keeping
   it also keeps FP-06's construction unchanged).
3. **The dropped §3.2 rider, shipped in the same change (FLAG-1 fix):** (a) the SUPERSEDE path calls
   `ledger.retire(P, valid_until=now.isoformat(), superseded_by=S)` AFTER the composed txn commits
   (store-first, mirroring `invalidate` — ONE mechanism for durable closes; P's own ledger row then replays
   CLOSED whatever happens to S's replay); (b) `_replay_record` applies the composed predecessor close ONLY
   when P's stored owner pair equals S's stamped pair — a Python-leg pre-read of P's `owner_principal`/
   `owner_agent` (replay is boot/admin, not hot; the read→close TOCTOU is the §2.3 ms class) — else it
   logs WARNING with both ids and skips the close. ⚠ ORDER MATTERS: (b) WITHOUT (a) would BREAK fidelity
   for an admin-bypass FOREIGN supersede (rebuild replays P open, then refuses S's cross-owner close →
   P revived — #453 re-opened for that shape). Today that shape is faithful ONLY because the guard is
   absent. Ship (a) and (b) together, never (b) alone.

### 2.5 Riders — and pin it like this (contract → adversary → build → cold audit; no skipping the adversary)

| # | rider | RED when |
|---|---|---|
| i | **transport keeps the row** | inject a transport failure on the COMPOSED txn only (after `authorize_guarded`'s pre-read — the §10.6-iii acquire wrap the atomicity contract already owns; make the returned connection's `query_raw` raise a `_CONNECTION_ERRORS` member once) → `remember(supersedes=P)` raises `SurrealConnectionError`, the ledger STILL has S, P is unchanged in the store; then `restore_from_ledger()` → S present, P closed with `superseded_by == S`, `valid_until == S.created_at`. POSITIVE CONTROL: the same fixture with the poison ASSERT (domain) → ledger has NO S (the existing rider-iii pin). A build that compensates on all exceptions reds the first leg; a build that never compensates reds the control. |
| ii | **∀ shapes, not ∀ causes (QUANTIFIER LAW)** | one parametrised pin over {plain, supersede} × {transport, domain}: ledger-row-survives is TRUE for both transport cells and for plain×domain(n/a — a plain remember has no domain-reject fixture today; construct one with the poison ASSERT on a plain remember and assert the row is KEPT — FP-06's own law, now forced for the reject cause too), FALSE only for supersede×domain. The 2×2 table is the fixture; no cell may be "not covered". |
| iii | **ONE mapping, proven by mutation** | in a `scratch_copy.sh` copy, make `_domain_rejection_error` return a plain `SurrealStoreError` for the non-governed label → rider i's control leg (compensation on ASSERT) reds AND `test_surreal_store::TestDomainRejectionErrorType` reds; both raise sites are reached through the one helper (a wrong build that types only one site reds one of them). Declare the expected-RED ids from `--collect-only` BEFORE the run (`scripts/mutation_proof.py`). |
| iv | **the typed class is the classification, not a name scan** | the compensation site's `except` must not string-match, must not test `isinstance(error, SurrealConnectionError)` (enumerating the forbidden), and must not catch `SurrealStoreError` broadly — pinned by rider ii's supersede×contention cell if the contract can construct exhausted contention cheaply (an 8-way racer on P's close with a tiny deadline), else by an AST pin that the `except` body names `TxnDomainRejectionError` and no transport type. Prefer the behavioural cell. |
| v | **pair-guarded replay close (FLAG-1)** | fixture: ledger row S (owner A, `supersedes=P`) with P owned by B in the store and S absent → `restore_from_ledger()` → S lands, P's `valid_until` is STILL NONE, a WARNING carrying both ids was logged (caplog); POSITIVE CONTROL: same-owner → P closed. Mutation: delete the pair predicate → the mismatch leg reds. |
| vi | **admin-bypass foreign supersede survives a rebuild** | dirty world gains `A supersedes B's row` (admin bypass, audited) → `rebuild_embeddings()` → P still closed, `superseded_by == S` (the §3.2 byte-diff pin extended by one lifecycle state — the state the current fixture does not force). This is the pin that makes 2.4-3(a) load-bearing and catches "(b) shipped without (a)". |
| vii | **removed-behaviour inventory for the C-fix's comment + docstring** | the `remember` docstring's "Order (per the FP-06 durability …)" paragraph and the compensation comment are served prose (a builder reads them); the fix wave's cold audit greps BARE for "SUPERSEDE-SCOPED" / "supersede-scoped" and every hit gets a file:line verdict. |

### 2.6 If the lead closes i-b on the stopgap instead (deferral shape 2 — the operator/lead owns timing)

Then the bound is PINNED, not described: a test in the atomicity module asserting the CURRENT behaviour
(transport on a supersede → ledger row DELETED) with the message *"KNOWN BOUND (63b close-out rulings
§2 / finding #458 for the companion FLAG-1/2 defects; mint a new finding for this bound): compensation is supersede-scoped on ALL exceptions; a lost-response commit followed
by a rebuild loses the successor. If you narrowed it deliberately, delete this pin and say so"* — plus a
`lore_findings` row (category `data_integrity`, area `memory.remember`) naming the owner and the
decision point. **Named re-open trigger:** the FIRST of (a) the 63b-ii wave opening `local.py` for any
reason, (b) any observed `SurrealConnectionError` on a supersede in the prod log, (c) the first off-fleet
consumer of lore. My recommendation remains: do not take this branch — the fix is two small edits at
seams already ruled, and the failure it closes is silent and permanent.

---

## FORK 2 — ADVERSARY BLOCKER B1 (lore_comms #10015, ruled 2026-09-09) — the `TxnDomainRejectionError` retype's exact-type blast radius

Sources: `REPORT-adversary-63b-ib-fork2.md` §B1 + REQUIRED REVISIONS (read); `test_surreal_store.py:827-930`
(the F2 class docstring + the §2.5 mapping pin at :912, read); my OWN textual derivation of every exact-type
check on `SurrealStoreError` across `loremaster/`, `lorerunes/`, `loresigil/`, `lorescribe/`, `scripts/`
(regex: `type(…) is|==|is not|!= SurrealStoreError`, `.__class__ is|== SurrealStoreError`, `.type is|==
SurrealStoreError`, and the reversed operand order; fallback said out loud — an assertion-spelling sweep is
grep-class case (b)); 8 of the sites the adversary's table omits, read in context.

### B1.1 RULING (1) — §2.4-1 STANDS. The subclass retype is the right mechanism; the corpses are reconciliation debt, not a design signal.

- **The alternatives are worse by law already in this doc.** *Compensate-unless-transport/contention* is
  the enumerate-the-forbidden shape rider iv rejects (the instrument lesson: the forbidden set is unbounded;
  a future `TxnSomethingElseError` silently lands on the compensate side). *An attribute flag on the base
  exception* (`error.is_domain_rejection`) is a weaker classification: not `except`-dispatchable, invisible
  to `pytest.raises`, and a default-`False` attribute on the base is a silent-safe that HIDES a missed
  classification instead of surfacing it. The repo's own precedent is the typed subclass — `TxnContentionExhaustedError`
  and `TxnGovernedConflictError` were both added exactly this way, with the same "every `except
  SurrealStoreError` keeps catching it" argument, and neither broke a production consumer.
- **Measured blast radius is bounded and behaviour-preserving.** My derivation: **21 exact-type sites, ALL in
  tests, 0 in production** (the adversary's R4 sweep confirmed by an independent scan — but the reviser
  RE-DERIVES this; a number inherited from this doc is a rumour). The adversary counted ~15–17; the six it
  missed are `test_surreal_store.py:754, :1036, :2124, :4498`, `test_surreal_apply.py:1157`,
  `test_surreal_manifest.py:588, :1104, :1342` — every one read, every one the SAME F2 shape: `assert
  type(x) is SurrealStoreError` immediately followed by `assert not isinstance(x, SurrealConnectionError)`
  and a connection-kept assertion. The `:754` comment states the reason exactness was chosen: *"the broad
  `pytest.raises(Exception)` pattern is exactly what let this drift … so the type is pinned EXACTLY, not
  just 'a subclass of'"* — i.e. exact-type was the ONLY way, at the time, to say "a store error that is NOT
  the connection subclass". `isinstance(x, TxnDomainRejectionError)` says that MORE precisely (it also
  excludes contention), so the F2 intent is not merely preserved by the retype — it is sharpened.
- **The one pin that asserts the inverted invariant (`:912`, plus the `:1036` live positive control and the
  parametrised transaction-seam pin's non-governed leg) is the §2.5 helper's OWN unit pin, written
  2026-09-04 as a DESCRIPTION of the then-mapping ("else the PLAIN `SurrealStoreError`"), not as a ruled
  property.** §2.4-1 of this doc SUPERSEDES that clause of design-2026-09-03 §2.5: `_domain_rejection_error`
  now mints a typed domain class for EVERY domain label (`TxnGovernedConflictError` for the governed
  label, `TxnDomainRejectionError` otherwise). Old-world virtue "a non-governed rejection is distinguishable
  from a governed one" → PRESERVED-WITH-PIN: `type(plain) is TxnDomainRejectionError and not
  isinstance(plain, TxnGovernedConflictError)`. ⚠ FLAG-6: the 2026-09-03 design doc's §2.5 text now
  teaches a retired mapping — the lead adds a one-line supersession note there (outside my writable set).

### B1.2 RULING (2) — corpse-adjudication POLICY: decided by EXECUTION, rewritten through ONE helper, never exact-type on the base again

**Derivation rule (construction, never reading):** run the full suite on the reference build. The RED set
IS the inventory. DIFF it against the textual scan (mine: 21; the adversary's: ~15). Every site in the UNION
gets a row with a file:line + a one-word class + the edit; "all remaining hits are X" is banned output.

| class | how you know | rewrite |
|---|---|---|
| **M — mapping pin** (the test's SUBJECT is the type the helper/raise-site MINTS: `:912`, `:1036`, the parametrised seam pin's non-governed leg) | RED on the reference build AND the assertion message names the mapping / "only the governed label maps to the typed subclass" | `type(plain) is TxnDomainRejectionError` — exact-type is CORRECT here because the helper's contract is the leaf it mints; `and not isinstance(plain, TxnGovernedConflictError)`; RED-until-built via the repo's `getattr(_txn, "TxnDomainRejectionError", None)` idiom with a legible message (the §2.5 pins' own idiom) |
| **I — intent pin** ("a store rejection, not a connection error; connection kept; message hygiene" — the F2 family, the `TestQueryClassifiedErrorPosture` twins, `TestSetState`, `TestRecordTraceErrorPosture`) | RED on the reference build; the next line is `not isinstance(x, SurrealConnectionError)` | replace the exact-type line with a call to ONE shared helper `assert_domain_rejection(error)` (new, in the test substrate — `_surreal_harness.py` or `_governed_contract.py`, wherever `SurrealStoreError` is already imported) that asserts `isinstance(error, TxnDomainRejectionError)` (RED-until-built, legible) and `not isinstance(error, SurrealConnectionError)`. 21 call sites need the SAME policy ⇒ a function they call, never 21 pasted `getattr` blocks (brief-base §6; prove by mutation — flip the helper's predicate → every caller reds). Keep each test's own connection-kept / hygiene lines untouched. **Do NOT rewrite to `type(x) is TxnDomainRejectionError`** — that relocates the corpse class one level down (the next refinement, e.g. a future `TxnAssertViolationError`, re-reds all 21) |
| **P — plain-base raise** (stays GREEN on the reference build ⇒ its fixture is NOT a domain rejection routed through `_domain_rejection_error`; a `SurrealStoreError` minted by OUR code — envelope integrity, a compose collision, an `is_connection_error` False-branch wrap) | GREEN on the reference build | still rewrite (the invariant pin bans the spelling): `isinstance(x, SurrealStoreError)` + the specific negatives the test cares about; record WHICH code minted it in the row. I expect this class to be EMPTY or near-empty (all 21 read shapes are domain fixtures) — the reviser measures, does not assume |

**Why the split matters:** M keeps exactness where the exact type IS the contract (the mint); I removes
exactness where it was only ever a stand-in for "not the connection subclass"; P is the honesty row that
proves the inventory was derived from execution and not from the regex.

### B1.3 RULING (3) — the revision completeness bar (all of the adversary's four, plus three it did not ask for)

1. **Whole-suite satisfiability receipt** — the reference build + the corpse rewrites → full suite, run
   ALONE (the #422 / uvicorn-timeout note in project memory), **0 failed with a passed-COUNT in the pasted
   tail**, plus `scripts/typecheck.sh` and `ruff` clean. The harder leg stands: satisfiable AFTER the lint
   cleanups (an orphaned `SurrealStoreError` import in a rewritten test is the obvious one).
2. **Removed-behaviour inventory enumerated from EXECUTION** (B1.2's RED set) and DIFFED against the textual
   scan; one row per site in the union; class M/I/P; the edit; the intent preserved. The `:754` comment
   ("pinned EXACTLY, not just a subclass of") is quoted in its row with the sharpening argument, so the
   next reader does not "restore" it.
3. **The repo-local invariant pin** — an AST scan over the WHOLE test tree (every workspace member's
   `tests/`, roots DERIVED from `[tool.uv.workspace] members` the way `derive_member_source_roots` does —
   reach as a checked variable, not `loremaster/tests` only) asserting NO `type(<expr>) is|== SurrealStoreError`,
   `<expr>.__class__ is|== SurrealStoreError`, or `<excinfo>.type is|== SurrealStoreError` (either operand
   order) survives. Required legs: a **discrimination control** (a planted synthetic source carrying the
   banned spelling is flagged, naming file:line), a **non-vacuity guard** (the scan SAW ≥ N test files and
   ≥ 1 `assert_domain_rejection(` call — else the scanner is blind), and a **home that `test_ast_reach_helpers.py`
   accepts** (its parse-skip / clone detectors flag test-dir enumerators: register the entry or place the
   scan in a module that already carries one — the reviser runs `test_ast_reach_helpers.py` green as part of
   the receipt).
4. **Production sweep** — re-derive the 0 (adversary R4 + my scan agree; a `match … case SurrealStoreError():`
   is isinstance-semantics and is fine; `except` is fine). Paste the regex and the count.
5. **NEW — the sibling-DISJOINTNESS hierarchy pin** (RED-until-built, in the FORK-2 contract): `issubclass(TxnDomainRejectionError,
   SurrealStoreError)`, `issubclass(TxnGovernedConflictError, TxnDomainRejectionError)`, **`not issubclass(SurrealConnectionError,
   TxnDomainRejectionError)`**, **`not issubclass(TxnContentionExhaustedError, TxnDomainRejectionError)`**.
   This is what makes BOTH the compensation site's `isinstance(error, TxnDomainRejectionError)` and every
   Class-I rewrite mean "domain, not transport, not contention". Without it a future "tidy-up" that
   re-parents `SurrealConnectionError` under the domain class silently flips the compensation rule to
   delete-on-transport — the exact false clear FORK 2 exists to close.
6. **NEW — corpse edits live in the CONTRACT revision, not the build wave.** They are TEST assertions; the
   contract author owns tests and the builder touches production only (builder ≠ grader, and a contract
   whose sibling tests are RED on the correct build is UNSATISFIABLE by definition — the C-DEF law). Class
   A/D were regressions a builder discovered AFTER building; B1 was found BEFORE the build, which is exactly
   where the adversary is cheapest. Between the contract commit and the build commit the RED-until-built
   siblings are RED_ADJUDICATED in `scripts/pending_contracts.yaml` (owner: the FORK-2 build; trigger: the
   build commit) — never RED_ORPHANED.
7. **NEW — re-adversary is MANDATORY after the revision** (CLAUDE.md: a fix wave is exactly where an
   adversary is cheapest and most needed; `r5` receipts). Its brief carries the P1c reach attack on the
   new invariant pin (item 3) and a mutation of `assert_domain_rejection`'s predicate (item B1.2-I).
8. (Optional, adversary R2) strengthen rider iv's source pin from name-presence to an AST check that the
   compensation `except` body names `TxnDomainRejectionError` and no transport type — or rely on the
   behavioural contention cell, which already discriminates. Reviser's choice; say which.

**Net:** the FORK-2 design is unchanged; the contract grows by one helper, one hierarchy pin, one
tree-wide invariant pin, ~21 mechanical rewrites, and a whole-suite receipt. That is the reconciliation
the retype always implied and the 2-file satisfiability scope hid — INSTRUMENT 0's reach class, caught
at CONTRACT time, which is the adversary doing its job.

---

## FORK-B — `render_subject_bound` and the render-coverage P-U universe (lore_comms #10011, 2026-09-08)

**RULING: Reading A. `render_subject_bound` is NOT a separate P-U universe member; Reading B (widen
`_method_interpolates_a_nonconstant` to admit the containment seams → 11 new probes) is REJECTED.**
Verified at `c658781` (+ the builder's test-only edits), not taken from the report:
- `AppContext.render_subject_bound` builds its line ONLY via `render_line(template, principal=render_attributed(…),
  agent=render_attributed(…), count=int)` — no f-string of a non-constant, no `.format` of a non-constant,
  no `_INTERP_NONCONTAIN` guard. By the universe's OWN property it is not leak-capable, so "not a
  candidate" is the property working, not a gap. Admitting it means changing the property — that
  relocates the universe boundary and admits 11 methods with nothing to leak, i.e. 11 probes no wrong
  build can fail (FIXTURES MUST DISCRIMINATE).
- **Its OUT-of-universe status is a CHECKED VARIABLE, not a hidden constant — which is the reach
  question INSTRUMENT 0 asks.** The universe is re-derived name-blind from `server.py`'s AST on every run
  and the forward leg `test_every_candidate_is_driven_or_out` reds any candidate that is neither driven
  nor OUT. So a leak-capable rewrite of `render_subject_bound` (an f-string of `subject.principal_id`)
  ENTERS the universe as `unclassified` → RED with no edit anywhere. Transitive drive is therefore not
  what guards it; the derivation is. The transitive `_render_recalled_memories` P-N pin (forged Subject →
  3 leaked shapes under the builder's mutation) is a SECOND, byte-level witness of the same thing.
- §3.3-ii's coverage intent is met where the design put it: `test_memory_render_bound_63b_ib.py::
  TestEveryGovernedReadRenderCarriesTheBoundLine::test_every_governed_read_render_calls_render_subject_bound`
  derives the governed-read render set from truth (`_governed_read_render_methods()`, `_resolve_subject`
  entry points → `_render_*` calls) with a non-vacuity guard — a checked variable, not a hand-list — and
  §3.3-iii's hostile fixture is `TestTheBoundLineContainsForgedIds`. The P-U universe was never the home
  of the bound-line coverage; it is the home of leak-capability, and the two must not be conflated.

**Rider — and pin it like this (one scratch receipt, lead or cold audit, declared-RED from `--collect-only`
BEFORE the run, `scripts/mutation_proof.py` / `scratch_copy.sh`):** rewrite `render_subject_bound` to
`return f"scope: principal {subject.principal_id} · agent {subject.agent_id} · …"` (bare f-string, no seam) →
expected RED = `test_link5_render_containment.py::…::test_every_candidate_is_driven_or_out` (naming
`render_subject_bound` as unclassified — proves OUT-by-property is re-derived) AND
`test_no_shape_leaks_the_forgery[_render_recalled_memories]` (the byte-level transitive witness) AND
`test_memory_render_bound_63b_ib.py::TestTheBoundLineContainsForgedIds::test_a_forged_principal_id_does_not_escape_the_render`;
restore, all green. If the first of the three does NOT red, the universe derivation has a blind spot and
this ruling re-opens (that would be the reach defect, not a reason for Reading B).

Named bound (unchanged from the P-U substrate's own): a method that leaks THROUGH a containment seam's
misuse is the seam's test's job (`render_line`/`render_attributed` pins), not the P-U universe's.

---

## FLAGS (outside my writable set — exact edits named; the lead routes)

- **FLAG-1 (filed: finding #458) — DROPPED RIDER at HEAD `c658781`: design §3.2's pair-guarded replay close is unbuilt and
  unpinned.** `_replay_record`'s composed close has no owner predicate and no WARNING; the §2.3
  compensation-window safety claim therefore does not hold today (a crash inside the window after a
  `GovernedConflict` leaves an orphan whose replay WOULD close the moved row). Fix + pins: §2.4-3 and
  riders v/vi. Must ship (a) retire-P-on-supersede together with (b) the guard — see the ORDER warning.
- **FLAG-2 (filed: finding #458, companion) — `remember`'s supersede path never retires P's ledger row.** Today fidelity of a superseded
  predecessor depends on S's replay close (ledger insertion order P-before-S under `rebuild_embeddings`,
  and S-absent under `restore_from_ledger`). Design §3.2 called this the "belt" and said `retire` is
  load-bearing only for `invalidate`; that is true ONLY while the replay close is unguarded (FLAG-1).
  Fix: §2.4-3(a). Pin: rider vi.
- **FLAG-3 — stale served prose:** `_governed_contract.TreeWriteAllowlistEntry` docstring teaches
  "`_recreate_memory_table` / `_replay_record` … `runtime_observed=False`" — false since 63b-i-a §5.1 Q1
  (both are observed by the battery). `63a_iv`'s module docstring will teach a deleted L1 layer after the
  D fix (§1.2 step 4). The `GovernedTableCase` docstring's "64 supplies its table's own pair" points 64
  at the RETIRED local-file allowlist shape (§1.3 C5).
- **FLAG-4 — friction (filed: finding #459):** `lore_impact` cannot resolve a TEST module by its dotted name
  (`loremaster.tests.test_memory_enforcement_63a_iv` → not-found), so the "who imports this test module"
  deletion gate fell back to a textual scan. Filed as finding #459.

- **FLAG-5 — idle-gate contract keyed on the WRONG session id (brief-template defect, fleet-wide).**
  The spawn brief dictated the contract path `…/63b-session2-20260908-design-sidecar-63b-s2.contract`
  (the LOGICAL session name), but `.claude/hooks/teammate-idle-gate.sh` resolves
  `contract_file="${marker_dir}/${session_id}-${teammate_name}.contract"` with `session_id` read from
  the hook input (`jq -r '.session_id'` — the HARNESS id, `session_01…`). So the declared contract was
  never consulted, the gate fell to the v1 default, and it nudged a compliant agent for a
  `REPORT-design-sidecar-63b-s2.md` that was never owed (measured 2026-09-08: the one-shot nudge fired
  with the deliverable present at its declared path). That is the switched-off-scanner class the
  brief-base warns about. Exact fix for the LEAD's brief template: either pass the harness `session_id`
  in the brief (the lead can read it from the hook input / the `.nudged` marker names already in
  `/tmp/claude-idle-gate-lore/`), or have the hook fall back to a `*-<teammate_name>.contract` glob when
  the exact-id file is absent (one line; keep exact-id first). I re-wrote my contract under the harness id
  derived from my own `.nudged` marker — the nudge is one-shot per session, so this is insurance, not a fix.

## Summary block (brief-base §1 — this doc is the report; no `REPORT-*.md` is owed per the spawn brief)

- receipt: `brief-base v14 read` · `brief project v7 read`
- state: **done** (both forks ruled; standing by for 63b-ii/iii)
- deviations: none. Writable set respected (this doc + the idle-gate contract file). No code, tests, or other docs touched.
- Packages considered: none — no new mechanism specified (a typed exception subclass + an `except` reorder + a Python-leg pre-read reuse existing seams: `_txn._domain_rejection_error`, `MemoryLedger.retire`, `_replay_record`).
- Reuse ledger: 1 new symbol ruled — `TxnDomainRejectionError` · lore query `lore_get_symbol(_domain_rejection_error / TxnContentionExhaustedError / SurrealConnectionError)` · returned: the three-type raise surface with NO typed domain class · disposition **EXTENDED** the §2.5 `_domain_rejection_error` mapping (not a new classifier; not a clone).
- Graded: `c658781` · HEAD-at-report: `c658781` · SAME.
- decisions-needed (lead): (1) FORK 1 §1.2 → route the class-delete to a builder now; §1.3 end state → same wave or 63b-ii prelude (must be ledgered either way). (2) FORK 2 → ship §2.4 (+ FLAG-1/2 fixes) in the i-b close-out fix wave [recommended] or close i-b on the stopgap with the §2.6 pin + finding. (3) None escalate to the operator as a spec gap — both forks were settleable from the sources; FLAG-1 is a dropped rider, not an ambiguity.
- pointers: FORK-2/B1 ruling (retype STANDS · M/I/P corpse policy via ONE `assert_domain_rejection` helper · 8-item completeness bar incl. the disjointness pin) · FORK-B ruling (Reading A + its mutation receipt) · §1.1 inventory · §1.2 D-fix edit · §1.3 couplings C1–C5 · §2.2 the loss path · §2.4 ruled shape · §2.5 riders i–vii · §2.6 stopgap pin · FLAGS 1–6 (FLAG-6 = supersession note owed in design-2026-09-03 §2.5).
