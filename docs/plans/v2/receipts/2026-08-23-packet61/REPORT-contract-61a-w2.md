# REPORT-contract-61a-w2

brief-base v14 read
brief project v7 read

_Revised four times (2026-08-23): addendum-2 (shape-keyed guard + route principal_keys) → addendum-3 (route tasks.transitive_blockers) → addendum-4 (PRESERVE tasks.transitive_blockers — NOT a full #400 clone — key the guard on the FULL idiom) → **addendum-5 (FINAL): recognize the passthrough-first POLICY in BOTH house spellings (one tuple clause OR two separate clauses) and pin the conditional-reraise evasion as an accepted bound.** My ground-truth finding (the transport-delta) was CONFIRMED by the sidecar. Pre-revision receipts superseded by §Satisfiability._

## SUMMARY BLOCK
- state: **done** — final RED contract authored, satisfiability proven on a provenance-asserting reference build
- deviations:
  - **Routed set = 9** (record-substrate family): `PrincipalStore.{create, set_subject}` + `PrincipalKeyStore.{mint}` + `KeepStore.{6}`. `tasks.transitive_blockers` is PRESERVED (not routed) — it lacks the passthrough-first clause (it deliberately wraps transport faults too, a DIFFERENT policy #400 must not change), so it is NOT a faithful clone. Its transport-wrap consistency is ledgered separately (#408 — the lead files it; not #400's concern).
  - **The guard keys on the FULL #400 idiom, spelling-agnostically** (`_try_has_full_idiom`: the handlers before a sole-body `except SurrealStoreError as e: raise <Domain>(...) from e` bare-re-raise BOTH transport classes — their UNION ⊇ `{SurrealConnectionError, TxnContentionExhaustedError}` — whether as one tuple clause OR two separate clauses, the two house spellings). This excludes `transitive_blockers` BY SHAPE (no passthrough) and catches a clone in EITHER spelling (addendum-5 closed the two-clause evasion). The instrument-lesson: key on the full POLICY, not a fragment and not a spelling. Allowlist EMPTY.
  - **One accepted BOUND, pinned** (`test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`, #137/#138): a full-equivalent clone written as a CONDITIONAL re-raise inside a single `except SurrealStoreError` handler is a non-house structure that evades the AST detector by design. Pinned as an accepted bound with a named re-open trigger (threat model = honest copy-paster of a house spelling, not an obfuscator; chasing exotic spellings is the reach spiral the STOP-rule forbids).
  - **Layer-1 `reclassify(*, passthrough, catch, make_error)`** (was `wrap_engine_rejection`); Layer-2 `_txn.wrap_store_rejection(domain_error, context)` delegates.
- Packages considered: none — stdlib `contextlib.contextmanager`; the extraction IS finding #400's resolution.
- Reuse ledger: 2 new symbols.

  | new symbol | lore query run | what it returned | disposition |
  |---|---|---|---|
  | `lorerunes.reclassify` (Layer 1) | `lore_search("wrap raw SurrealStoreError as domain error, re-raise connection/contention first — shared classification helper")` | only cloned per-method idioms; no shared control-flow primitive | **HAND-ROLLED** — the shared home #400 mandates |
  | `loremaster.store._txn.wrap_store_rejection` (Layer 2) | same search + repo-wide AST idiom scan | the surreal taxonomy cloned per-method (9 faithful sites) | **HAND-ROLLED** — the ONE taxonomy binding |

  Test idioms REUSED: `_patch_everywhere` mutation sweep (`test_secret_typing.py`), AST reach-derivation (`test_store_seam_one_derivation.py`), `keep_env` fixture shape.
- Graded: n/a (contract author).
- decisions-needed: none (the transport-delta fork — my prior decision-needed #1 — is RULED: addendum-4 preserves `transitive_blockers`, ledgers #408). This should be the last revision.
- receipt POINTERS:
  - contract files: `lorerunes/tests/test_engine_rejection.py` (20 pins) · `loremaster/tests/test_engine_rejection_seam.py` (56 pins)
  - the full-idiom guard + the instrument-lesson: §The-guard
  - satisfiability (`loremaster.__file__`, gate tails): §Satisfiability
  - declared RED/GREEN node sets: §Node-sets

---

## The two-layer seam (D2) — what the contract pins

- **Layer 1 — `lorerunes.reclassify(*, passthrough, catch, make_error)`** (stdlib-only control-flow POLICY). Pinned in `lorerunes/tests/test_engine_rejection.py` (20 pins) with SYNTHETIC classes mirroring the real hierarchy: existence + keyword-only signature + is-a-CM; happy path (+ `make_error` NOT invoked); catch→`make_error()`'s result (identity, context, `__cause__` chain, invoked exactly once, a catch-subclass translated); **the load-bearing ordering** (`passthrough` re-raised FIRST — propagates as itself, `make_error` not invoked); over-catch guard; `passthrough`/`catch` parameterised; module purity; `__init__` re-export + `__all__`.
- **Layer 2 — `_txn.wrap_store_rejection(domain_error, context)`** binds the surreal taxonomy ONCE and delegates to `reclassify`; a call-time function (not a partial). Rejecting option (b) (per-store taxonomy clone) is enforced by the Layer-2 mutation pin.
- **Routed set = the 9 FULL-#400 clones:** `PrincipalStore.{create, set_subject}` + `PrincipalKeyStore.{mint}` + `KeepStore.{create_keep, add_household_member, remove_household_member, set_rank, set_keeper, delete_keep}`. (`AuditStore.append` born-wrapped in w4.)

### The full-idiom shape guard (§The-guard — addendum-4/5, the instrument-lesson)
`TestNoFullIdiomCloneOutsideTheSeam` AST-walks EVERY loremaster module (derived from the package tree, no store hand-list) for the FULL #400 idiom via `_try_has_full_idiom` — a `try` whose handler LIST has a passthrough-first handler (`except (SurrealConnectionError, TxnContentionExhaustedError): raise`, a bare re-raise of BOTH classes) PRECEDING a sole-body `except SurrealStoreError as e: raise <Domain>(...) from e`. Asserts none appears outside the seam, **allowlist EMPTY** (`test_the_allowlist_is_empty`).

**Why the full idiom, and spelling-agnostic (the lesson, twice):** the addendum-2 revision keyed on the translate line alone and matched a 10th site — `tasks.transitive_blockers` — which shares the translate substring but has NO passthrough clause (a DIFFERENT whole policy). Keying on a FRAGMENT matched the wrong site → key on the FULL idiom (addendum-4). Then the adversary caught that keying on the SINGLE-TUPLE passthrough spelling let a TWO-CLAUSE clone (`except Conn: raise` / `except Contention: raise` — a real tasks/findings house idiom) evade → key on the passthrough POLICY (the UNION of bare-re-raised transport classes ⊇ both), in EITHER spelling (addendum-5). The detector's positive control (`test_the_detector_keys_on_the_policy_in_BOTH_house_spellings`) proves — with synthetic AST fixtures — that it flags BOTH house spellings and NOT: a translate-without-passthrough (transitive_blockers's shape), a wrong-order group, a multi-statement (CAS) translate, or a partial (one-transport-class) passthrough in EITHER spelling. Threat model in the guard: the honest copy-paster of a house spelling, NOT a deliberate obfuscator. The one non-house evasion (a conditional re-raise inside a single `except SurrealStoreError` handler) is pinned as an accepted BOUND (`test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`, #137/#138) with a re-open trigger — not chased (the reach spiral the STOP-rule forbids).

### Mutation + behavior pins (across the 3 routed stores)
- **Two-layer mutation proof** (`TestSharingProvenByMutation`): ∀ over all 9 routed paths, TWICE — patch `reclassify` → marker (Layer-1 control-flow sharing) AND patch `wrap_store_rejection` → marker (Layer-2 taxonomy-binding sharing; catches option (b)). Plus `TestTheMutationProofDiscriminates` (probe control).
- **Coverage** (`TestTheRoutedSetIsDerivedAndComplete`): the AST-derived routed set (methods referencing `wrap_store_rejection`) == the invocation map == the known wrapping verbs, per store.
- **Behavior-preservation** (`TestEngineRejectionWrappingBehaviourIsPreserved`): ∀ across the 3 stores — raw `SurrealStoreError` → domain error; transport → propagate. GREEN at HEAD AND after (the DUAL — the old world's virtues survive).

**Removed-behavior inventory (the DUAL, all adjudicated PRESERVED-WITH-PIN):** the passthrough re-raise → helper `reraise` (transport-fault pins + lorerunes ordering pins); the `SurrealStoreError`→domain wrap → helper `catch` (domain-error pins); the per-method context message → passed verbatim to the binding (byte-identical); the deliberate `KeepNotFoundError`/`KeeperLockoutError` refusals inside the try → still raised inside the `with`, still non-`SurrealStoreError`, pass through untouched (existing pins stay green). **`transitive_blockers`'s wrap-everything behavior is PRESERVED (not routed)** — addendum-4, ledgered #408.

---

## Satisfiability (final reference build in a provenance-asserting scratch)

Scratch: `/tmp/pkt61a-w2-ref` via `scripts/scratch_copy.sh`.
**`loremaster.__file__` = `/tmp/pkt61a-w2-ref/loremaster/loremaster/__init__.py`** (verified `scratch_copy.sh --verify-only`).

Reference extraction:
- `lorerunes/lorerunes/reclassify.py` — `reclassify(*, passthrough, catch, make_error)` (stdlib-only); `__init__` re-exports it + `__all__`.
- `_txn.py` — `wrap_store_rejection(domain_error, context)` delegating to `reclassify` (call-time function).
- `keeps.py` (6) + `principals.py` (2) + `principal_keys.py` (1) route through the seam; orphaned `SurrealStoreError` imports dropped from `keeps.py` + `principal_keys.py`.
- **`tasks.py` UNTOUCHED** (`transitive_blockers` preserved with its local wrap-everything handler).

Receipts (scratch, `fb68427` + extraction):
- **The full-idiom scan on the reference build (9 routed, `transitive_blockers` preserved) = `[]`** — the guard finds NO full-idiom clone outside the seam (transitive_blockers correctly not matched).
- **Contract 0-failed on the correct build:** `76 passed` (20 lorerunes + 56 seam).
- **Behavior preserved:** `231 passed` across `test_keeps_store.py`, `test_principals_store.py`, `test_principal_keys_store.py`, `test_secret_typing.py`, `lorerunes/tests/test_smoke.py`, `test_store_seam_one_derivation.py`, and `test_task_read_surface.py` (transitive_blockers coverage — untouched).
- **ruff:** clean (`All checks passed!`) — orphaned-import removals + import-sort are the cleanup leg; `tasks.py` reverted byte-identical to HEAD.
- **mypy:** `./scripts/typecheck.sh` → `typecheck: lorerunes OK` / `typecheck: loremaster OK`, MYPY_EXIT=0.
- **registration:** no new workspace member. Registration = the `lorerunes.__init__` re-export of `reclassify` (pinned by `TestPackageReExport`); `wrap_store_rejection` is an internal `_txn` symbol.

**The guard at HEAD finds exactly the 9 faithful clones, `transitive_blockers` EXCLUDED:**
```
keeps.py::{create_keep, add_household_member, remove_household_member, set_rank, set_keeper, delete_keep}
principal_keys.py::mint · principals.py::{create, set_subject}   (transitive_blockers present? False)
```

---

## Node-sets (declared from `--collect-only` at `fb68427`)

**RED at HEAD → GREEN on the reference build (45 nodes):**
- `lorerunes/tests/test_engine_rejection.py` — ALL 20.
- `loremaster/tests/test_engine_rejection_seam.py` — 25:
  - `TestNoFullIdiomCloneOutsideTheSeam::test_no_full_idiom_wrap_appears_outside_the_seam` (1)
  - `TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_invocation_map[keep|principal|principal_key]` (3)
  - `TestTheRoutedSetIsDerivedAndComplete::test_the_routed_set_equals_the_known_wrapping_verbs[keep|principal|principal_key]` (3)
  - `TestSharingProvenByMutation::test_dropping_LAYER1_reclassify_moves_every_routed_path[9]` (9)
  - `TestSharingProvenByMutation::test_dropping_LAYER2_wrap_store_rejection_moves_every_routed_path[9]` (9)

**GREEN throughout (behavior-preservation + positive controls + the pinned bound, 31 nodes):**
- `test_the_detector_keys_on_the_policy_in_BOTH_house_spellings` (1) · `test_the_conditional_reraise_shape_is_a_KNOWN_BOUND` (1) · `test_the_allowlist_is_empty` (1) · `test_the_technique_moves_a_router_and_not_a_private_clone` (1)
- `test_a_raw_store_error_surfaces_as_the_domain_error[9]` (9)
- `test_transport_faults_propagate_untouched[9×2]` (18)

RED count re-confirmed with final files: lorerunes `20 failed`; seam `25 failed, 31 passed`.

---

## Flags for the lead / adversary
1. **`tasks.transitive_blockers` preserved + ledgered #408** — the reach law surfaced it (a translate WITHOUT passthrough = a different policy); addendum-4 rules it preserved. The full-idiom guard excludes it by SHAPE (no allowlist entry). If #408 later routes it (with a deliberate transport-behavior decision), the guard will require it once it grows the passthrough clause.
2. **The guard is spelling-agnostic** (addendum-5) — a full clone in EITHER house spelling (one tuple clause or two separate clauses) reds; a partial passthrough in either spelling does not. One non-house structure (conditional re-raise in a single handler) is a pinned accepted BOUND (`test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`, #137/#138) with a re-open trigger — deliberately not chased (STOP-rule).
3. **The empty allowlist is pinned empty** (`test_the_allowlist_is_empty`) — a future entry reds it; the full idiom is the sole discriminator.
4. **Binding is a call-time delegator** — the Layer-1 mutation pin enforces it.
