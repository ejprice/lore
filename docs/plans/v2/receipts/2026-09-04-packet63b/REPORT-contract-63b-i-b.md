# REPORT-contract-63b-i-b

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- receipt: brief-base v14 read · brief project v7 read
- state: DONE-with-deviations — RED contract for #441/#436+#453/#437 + F5-allowlist DATA written &
  RED-at-HEAD validated; satisfiability 70/0 under Reading A (provenance-asserted scratch); ONE design gap
  flagged (§2.2 marker mapping, finding #456) needing a lead ruling + `_txn` scope grant.
- deviations: (1) adding the #436 replay-close allowlist entry reds ONE i-a frozen pin at HEAD (the ghost
  containment pin) — the INTENDED contract-first coupling, resolves when the builder adds #436's literal.
  (2) probe revealed the §2.2 marker→GovernedConflict mechanism needs a `_txn` seam change (outside i-b's
  writable set) — STOP-and-FLAG below.
- Packages considered: none new — no NEW mechanism specified; the contract reuses the LANDED F5 instrument
  (`_governed_contract`), the store txn seam (`compose`/`execute_transaction`/`_assert_envelope_integrity`),
  the `store_handle(on_acquire)` injection idiom, and `FakeEmbedder`. The §2 in-store THROW guard is
  `replace` (SurrealQL `THROW`, READ from surrealql-tests + probed live — finding #456).
- Reuse ledger: contract-only; new test symbols reuse existing substrate — `_REPLAY_CLOSE_ENTRY` EXTENDED
  `MEMORY_TREE_ALLOWLIST`; `_effect_upsert` EXTENDED (widened in place); test poison lever REUSED the 63a
  `embedding='not-a-float'` coerce-reject idiom (as a `note_text` ASSERT); injection REUSED `store_handle`.
  No new production symbols (builder's job). DRY ledger n/a (no new reusable production symbol authored).
- Graded: b2f9b0e · HEAD-at-report: b2f9b0e · SAME
- decisions-needed: **§2.2 marker→GovernedConflict mapping** (finding #456) — the design says
  `execute_transaction`'s root cause surfaces the `governed_conflict:` marker, but it is STRIPPED by ledger-#31
  hygiene; a `_txn` classification (outside i-b's writable set) is needed. Both readings + a proven fix below.
- pointers: #441 → `loremaster/tests/test_memory_supersede_atomicity_63b_ib.py`; #436/#453 →
  `test_memory_replay_fidelity_63b_ib.py`; #437 → `test_memory_render_bound_63b_ib.py`; F5 DATA →
  `test_memory_enforcement_63b_ia.py` (`_effect_upsert` widened + `_REPLAY_CLOSE_ENTRY`) + registration pins in
  `test_memory_f5_registration_63b_ib.py`; probe → `scripts/probe_supersede_throw_rollback.py`; finding #456.

## STATUS LOG
- STARTED at HEAD b2f9b0e. Registered on lore_comms (session packet63b). Idle-gate contract written.
- Reading: design §2/§3/§5.1 + store-ref §1/§2/§3 + landed F5 instrument (b2f9b0e).

## GROUND TRUTH ABSORBED (at HEAD b2f9b0e)

### #441 supersede atomicity (§2)
- `governed.guarded_write` (governed.py:337): monolithic pre-read→authorize→GovernedAuditUnavailable→
  guarded UPDATE composed w/ audit→execute→`row_count==0`→GovernedConflict. Its own `write_guard("guarded_write")`.
- `LocalMemoryBackend.remember` (local.py:544): supersede-close via `guarded_write` in its OWN txn (audit)
  → ledger.record → new-row UPSERT in a SECOND txn under `write_guard("remember")`. TWO txns = the defect.
- `invalidate` (local.py:702) routes its close through `guarded_write` (audit=self.audit_store).
- store-ref §3: `.query()` validates only statement[0]; `execute_transaction` checks every stmt; THROW inside
  BEGIN…COMMIT aborts the WHOLE txn (COMMIT then errors "aborted due to a prior error"); `_txn._domain_root_cause`
  picks first non-cascade marker (`_CASCADE_NOT_EXECUTED_MARKER="was not executed due to"`). Retry marker `"can be retried"`.

### #436/#453 replay fidelity (§3.1/§3.2)
- `MemoryLedger` (ledger.py): only record/all_records/count/close. Metadata JSON. NO retire/delete. Design adds
  `retire(memory_id,*,valid_until,superseded_by)` + `delete(memory_id)`; metadata gains owner_principal/owner_agent/
  scope/created_at/valid_until/superseded_by.
- `_ledger_metadata` (local.py:1309) stamps kind/importance/labels/source/expires_at/supersedes ONLY.
- `_replay_record` (local.py:1262): stamps NOTHING governed, valid_from=created_at=now(); one UPSERT under
  `write_guard("_replay_record")`. Design: reconstruct faithfully + compose predecessor-close into replay txn
  (same-owner only). Legacy rows → NONE/NONE fail-closed.
- `_build_content` (local.py:1333) staticmethod, valid_from=created_at=now; option cols default NONE. Design: takes
  stamps as params.
- `rebuild_embeddings` (local.py:896) drops table (_recreate_memory_table) then restore_from_ledger. #453: at HEAD a
  rebuild REVIVES retired/superseded rows (ledger records no closes). Fix: replay re-applies closes.

### #437 render bound line (§3.3)
- `_render_recalled_memories(recalled)` (server.py:4215) staticmethod, `_NO_MEMORIES_RECALLED` on empty. Called ONLY by
  `AppContext.recall` (sole consumer, verified via lore_impact). Design: `_render_recalled_memories(recalled,*,subject)`
  prepends `render_subject_bound(subject)`; empty case names the bound.

### F5 instrument (i-a LANDED, my registration target — DATA only)
- `_governed_contract.py`: `TreeWriteAllowlistEntry(site,justification,pin,frames,exempt_name,runtime_observed,
  statement="",effect:Callable[[ObservedEffect],bool]|None,l1_site=True)`; `classify_tree_observed_write` LABEL leg
  (runs entry.effect) + EXEMPT 4-leg; `ObservedEffect(row_deltas,schema_delta,schema_after)`; `RowDelta(id,kind,
  changed_columns,before,after)`; `governed_populations(schema_source)` AST-derives from surreal_schema;
  `governed_table_raw_mutation_sites_in_tree` derives L1 sites whole-tree (growth detector).
- `test_memory_enforcement_63b_ia.py`: `MEMORY_TREE_ALLOWLIST` + effect predicates (`_effect_upsert` for
  `_UPSERT_ENTRY` frames=("remember","_replay_record"); `_effect_migrate/_reinforce/_guarded_write/_recreate/
  _ensure_ready`). `_UPSERT_ENTRY.site=(local,"_upsert_fragment","UPSERT")`. `L1_SITE_ENTRIES`/`L1_ALLOWLISTED_SITES`
  ghost-check subset. `_effect_upsert` docstring ALREADY says "i-b WIDENS it".

## F5-ALLOWLIST DATA REGISTRATION plan (§5.1, MINE — DATA only, NOT instrument)
- (1) WIDEN `_effect_upsert` for `remember`: created-row-owned-by-subject ∪ updated-predecessor(changed⊆{valid_until,
  superseded_by}). #441's composed close is BUILT by GuardedPlan.fragments (dynamic `type::record('{table}',…)`
  → NOT L1-derived; L2 sees effect under `remember` label).
- (2) #436's `_replay_record` predecessor-close `UPDATE type::record('{MEMORY_TABLE}',$p)…` IS a new DERIVED L1 site
  → add sibling entry `(local,"_replay_record","UPDATE")` frames=("_replay_record",) w/ close effect predicate.
  At HEAD this literal is ABSENT → the new entry is a GHOST (or, if I split the frames, the site missing) — RED
  until the builder adds the literal. This is the "unregistered replay-close reds coverage/classify" pin.

## WORK (grows per pin family)

### #441 — test_memory_supersede_atomicity_63b_ib.py  [WRITTEN · RED-at-HEAD validated]
Poison lever: a targeted `DEFINE FIELD OVERWRITE note_text … ASSERT $value != '<sentinel>'` makes the
SUCCESSOR create (UPSERT) fail inside the composed txn while the close's valid_until write is untouched
— the exact window discriminating OLD (close commits first, separate txn) vs NEW (atomic rollback +
ledger compensation). Fixture `supersede_world` = ledger-backed backend + admin `_ADMIN` + scope="server"
(no keep/audit needed for self-supersede; audit auto-wired via `backend.audit_store` property).
- Behavioural (RED via old-build bug, ASSERTION failure — receipts pasted): predecessor-left-open
  (valid_until SET + superseded_by → phantom successor id at HEAD), ledger-orphan (no compensation),
  rejected-bypass-audit-orphan (before=0 after=1). Positive controls GREEN at HEAD.
- NEW-API (RED via unbuilt `governed.authorize_guarded`/`GuardedPlan`): authorize_guarded-no-effect,
  fragment-carries-IF-THROW (rider ii), composed-rescope-conflict+rollback (rider i, on_acquire#2),
  composed-positive-control, deny-first-zero-effect (rider iv), one-implementation structural (rider vi:
  guarded_write == authorize_guarded+fragments+execute AND row_count==0 branch deleted).
- RED-at-HEAD run: 9 failed (all right reason) / 2 passed (positive controls). Receipts in body below.
- rider vii probe → scripts/probe_supersede_throw_rollback.py (pending).

### #436/#453 — test_memory_replay_fidelity_63b_ib.py  [WRITTEN · RED-at-HEAD validated]
QUANTIFIER LAW property (∀ lifecycle states, forced by fixture `_seed_dirty_lifecycle`: live-owned,
superseded-pair, invalidated, admin-bypass-closed-foreign; 2 distinct owners for discrimination).
Snapshot governance+lifecycle cols → rebuild_embeddings → re-snapshot → per-COLUMN diff. RED at HEAD:
owner_principal/owner_agent/scope→None, valid_from/created_at re-stamped to rebuild instant, valid_until
+superseded_by→None (REVIVED). Failure NAMES each row.column (mutation proof: drop any stamp reds its col).
- #453 explicit: invalidated + superseded-predecessor STAY retired after rebuild (RED: valid_until→None).
- #436 ledger: remember records owner/scope/created_at metadata (RED: absent); invalidate retires ledger
  row (RED: no retire); MemoryLedger.retire + .delete verbs exist (RED-until-built).
- Green-at-HEAD protection pins: owner-diversity discrimination guard; legacy-row fail-closed (NONE/NONE).
- RED-at-HEAD run: 6 failed (all right reason) / 2 passed (protection). Receipts in body.

### #437 — test_memory_render_bound_63b_ib.py  [WRITTEN · RED-at-HEAD validated]
`render_subject_bound(subject)` derivation pins (mutation: change visible_keep_ids → line changes; 0-keep
names the bound), coverage-as-checked-variable (recall → _render_recalled_memories takes subject + calls
render_subject_bound — structural), empty-case names the bound (Leg-1), hostile forged-id containment
(routes through render_attributed), no-withheld-count, recall-passes-subject wiring. RED-at-HEAD run: 9 failed
(all right reason: render_subject_bound unbuilt / _render_recalled_memories takes no subject / recall passes
only `recalled`). Comms-read coverage (drain/story/await/rollup) scoped to 63b-ii (RED_ADJUDICATED there).

### F5-allowlist DATA + registration — test_memory_f5_registration_63b_ib.py + i-a DATA edits  [DONE · RED validated]
DATA edits in test_memory_enforcement_63b_ia.py (§5.1, in i-b writable set):
- `_effect_upsert` WIDENED (stricter on updated rows: create OR close with changed⊆{valid_until,superseded_by};
  a seizure composed beside the create → UNCLASSIFIED). SAFE at HEAD: create/replay frames produce created
  rows only, so identical to the coarse predicate on i-a shapes (verified: full i-a file 31 passed post-edit).
- `_REPLAY_CLOSE_ENTRY` ADDED (site (local,"_replay_record","UPDATE"), frames=("_replay_record",),
  effect=_effect_upsert, l1_site=True). Registered in MEMORY_TREE_ALLOWLIST. ★COUPLING★: reds the i-a ghost
  containment pin at HEAD (site not L1-derived until #436's literal) — INTENDED contract-first RED, GREEN at build.
  Verified: `_label_leg_classifies` returns True on first matching-frame entry whose effect holds; an effect=None
  entry would re-widen the frame, so the entry carries a real effect (_effect_upsert).
Registration pins (test_memory_f5_registration_63b_ib.py): replay-close-site-registered-and-derived (RED at HEAD:
builder deliverable), widened-effect accepts create+close / rejects seizure / rejects delete (green — DATA guards),
unlabelled composed close unclassified (deny-by-default), labelled clean classifies + labelled seizing unclassified,
site-in-exactly-one-entry, and the INTEGRATION pin (a composed supersede is ONE `remember` write with created+close,
not a separate `guarded_write` — RED at HEAD: observed `remember:[created]` + `guarded_write:1`). Run: 2 failed
(right reason), 7 passed (guards). Full i-a file post-edit: 1 red (ghost coupling) + 32 pass; evidencing-pin GREEN.

## RED-AT-HEAD TOTALS (serial `-n0`, TEST store :18000, b2f9b0e)
- #441 (test_memory_supersede_atomicity_63b_ib.py): 9 failed / 2 passed (positive controls).
- #436/#453 (test_memory_replay_fidelity_63b_ib.py): 6 failed / 2 passed (protection: owner-diversity + legacy fail-closed).
- #437 (test_memory_render_bound_63b_ib.py): 9 failed / 0 passed.
- F5 registration (test_memory_f5_registration_63b_ib.py): 2 failed / 7 passed (DATA guards + positive controls).
- **COMBINED (4 i-b files, serial `-n0`, b2f9b0e): 26 failed / 11 passed** — every failure right-reason.
- i-a coupling: exactly 1 i-a frozen pin reds (the ghost containment pin) — resolves with the builder's #436 literal.
- Contract files ruff-clean (`uv run ruff check` on all 5 test files + the probe → All checks passed).
Every RED verified for-the-right-reason (assertion on an observable old-build bug, or an unbuilt builder-deliverable
seam named in the message — never a TypeError/parse error in the test). Receipt tails pasted per-file above/below.

## PROBE RECEIPT (§2.4 rider vii) — scripts/probe_supersede_throw_rollback.py, exit 0
```
DISCOVERIES (report-only — design-level findings for lead-63b):
  * marker in RAW engine result (kind='Thrown'): True (text: 'An error occurred: governed_conflict:probe_t:target')
  * marker in execute_transaction EXCEPTION: False (exception: 'SurrealDB transaction failed and was rolled back:
    statement 4 of 5 was rejected (unspecified rejection); see the server log for the full engine detail')
  * GAP (design §2.2): the engine surfaces governed_conflict: in the raw 'Thrown' statement, but
    execute_transaction's ledger-#31 hygiene strips it from the raised exception ... STOP-and-FLAG to lead-63b.
PROBE OK (§2.4 rider vii) — (a) the in-store LET/IF-THROW ROLLS BACK a preceding UPSERT, (b) a matching close
COMMITS (positive control), (c) _assert_envelope_integrity ACCEPTS the LET + IF-THROW fragment.
```
Raw engine per-statement result (diagnostic): the IF-THROW statement returns `{"kind":"Thrown","status":"ERR",
"result":"An error occurred: governed_conflict:probe_t:target"}`; the COMMIT returns "Cannot COMMIT: ... aborted
due to a prior error"; the preceding UPSERT's row does NOT exist after the raise (rolled back).

## ⚠ STOP-AND-FLAG (decision needed from lead-63b) — §2.2 marker → GovernedConflict mapping (finding #456)
The §2.2 mechanism ("the driver's SEMANTIC root-cause selector `_txn._domain_root_cause` surfaces the THROW text;
`governed` maps the `governed_conflict:` marker → GovernedConflict") has an UNSPECIFIED step. Measured (probe above):
- `_domain_root_cause` DOES internally select the Thrown statement, BUT `execute_transaction` deliberately strips
  the raw per-statement text from the raised exception (ledger #31 error-message hygiene — raw text can echo a bound
  value to MCP clients), rendering only a classified "unspecified rejection; see the server log". So `governed`
  cannot read the `governed_conflict:` marker from the exception.
Two code-differing readings:
- **Reading A (RECOMMENDED — the analogous fix):** classify the `governed_conflict:` marker in `_txn` as a TYPED
  signal (a `GovernedConflictSignal`/marker), exactly as `_RETRYABLE_CONFLICT_MARKER` ("can be retried") is already
  classified and surfaced typed. The marker is a FIXED server-derived prefix, NOT a bound value, so surfacing the
  CLASSIFIED type does not violate #31 hygiene. `governed`/`guarded_write` catches it → GovernedConflict. Requires a
  `_txn.py` edit — OUTSIDE i-b's writable set (§5.1) → a scope grant.
- **Reading B:** `governed`/`remember` runs the composed txn via a path that reads the raw per-statement results and
  classifies the marker itself. REJECTED here: it clones `execute_transaction`'s verification (ROUTING-IS-NOT-SHARING)
  and re-exposes raw text — the exact thing #31 hygiene closed.
Contract impact: rider i/ii pins (`test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back`,
`test_the_guarded_plan_fragment_carries_the_in_store_throw`) assert `governed.GovernedConflict` per §2.2's stated
intent. If the lead rules a DIFFERENT type, those two pins' `pytest.raises(...)` target updates. The ATOMICITY legs
(predecessor unchanged / ledger compensated / successor absent) are error-TYPE-INDEPENDENT and hold regardless.
The ROLLBACK itself (§2.4 vii (a)) is CONFIRMED working. RECOMMENDATION: rule Reading A + grant the `_txn` edit to i-b.

## SATISFIABILITY RECEIPT (C-DEF) — DONE · 0-failed
Reference build in a provenance-asserted scratch (`scripts/scratch_copy.sh /tmp/lore-scratch-63bib`),
implementing #441/#436/#437 + the F5 replay-close literal + Reading A (the `_txn` marker classification):
- PROVENANCE (#140): `loremaster.__file__ = /tmp/lore-scratch-63bib/loremaster/loremaster/__init__.py`
  (the copy runs its OWN production code, not the original tree).
- Reference changes (scratch only): `governed.py` (`GuardedPlan`+`authorize_guarded`+`guarded_write`=
  composition, in-store THROW fragment, `_is_governed_conflict`→GovernedConflict); `store/_txn.py`
  (Reading A: `_ERROR_CLASS_GOVERNED_CONFLICT` — classify the `governed_conflict:` marker, a fixed
  server-derived string, safe under #31 hygiene); `memory/local.py` (composed remember + ledger-first +
  `delete` compensation; `_ledger_metadata` governance keys; `_build_content` stamp params;
  `_replay_record` faithful reconstruct + the composed predecessor-close L1 literal; `invalidate` retire);
  `memory/ledger.py` (`retire`+`delete`); `server.py` (`render_subject_bound`+`_render_recalled_memories(subject)`+`recall`).
- RUN (serial `-n0`, TEST store :18000): `test_memory_supersede_atomicity_63b_ib.py` +
  `test_memory_replay_fidelity_63b_ib.py` + `test_memory_render_bound_63b_ib.py` +
  `test_memory_f5_registration_63b_ib.py` + `test_memory_enforcement_63b_ia.py` → **70 passed, 0 failed**.
  (The i-a ghost pin GREENS on the reference — the `_replay_record` close literal is now L1-derived.)
- ⚠ **#436 byte-identity fidelity IS satisfiable** (the highest-risk concern): 8/8 passed — the
  governance+lifecycle stamps round-trip byte-identical across `rebuild_embeddings` (datetime ISO
  round-trip via the ledger holds at µs precision; the retire-restored predecessor close is byte-exact,
  and the composed replay-close belt is a no-op in the normal path so it never overwrites).

### Two self-caught contract bugs (the C-DEF process working — both FIXED in the real tree)
1. `test_a_rescope_on_the_composed_transaction_conflicts_and_rolls_back` expected `execute_transaction`
   to raise `governed.GovernedConflict`. FALSE by LAYERING: `_txn` (store) cannot import `governed`, so
   it raises `SurrealStoreError` — the GovernedConflict mapping lives in `governed`. FIXED: the pin now
   asserts the type-INDEPENDENT rollback (successor absent + predecessor unchanged) + the classified
   `governed_conflict` marker reaching the caller (Reading A). This is EXACTLY the §2.2 gap surfaced from
   the contract side — the pin now documents that the type mapping is a `governed`-layer concern.
2. `test_both_close_paths_route_through_authorize_guarded` banned the substring `"row_count == 0"`, which
   matched the reference build's DOCSTRING explaining the branch was deleted. FIXED: it now bans the
   code-shaped conditional `"if row_count == 0"` (won't appear in prose).
Both fixes re-verified RED-at-HEAD for the right reason (9 failed / 2 passed for #441 at b2f9b0e).

### Scratch note
The reference build lives at `/tmp/lore-scratch-63bib` (disposable by `scratch_copy.sh` design — NOT the
real tree; the real tree carries ONLY the contract tests + the F5 DATA edits). It demonstrates Reading A
resolves finding #456; the lead rules the actual `_txn` approach. Operator may discard the scratch.

## CLOSE-OUT
- state: done-with-deviations. 4 RED contract files + F5 DATA + probe written & validated RED-at-HEAD;
  satisfiability 70/0 under Reading A; ONE design gap flagged (finding #456) needing a lead ruling +
  `_txn` scope grant. All work in the writable set (tests/test_memory_* + F5 DATA); production untouched
  in the real tree.
- Do NOT stage/commit — the lead commits. The probe (`scripts/probe_supersede_throw_rollback.py`) is the
  lead's to commit per the brief.
- N unrelated failing tests: I ran ONLY the scoped set the brief named (my 4 files + the i-a file + the
  probe); I did not run the full suite, so I cannot report an unrelated-failure count. Not run = not claimed.
