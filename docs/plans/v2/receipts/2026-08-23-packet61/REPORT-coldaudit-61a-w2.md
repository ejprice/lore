# REPORT-coldaudit-61a-w2

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **state:** done
- **VERDICT: GO.** #400's two-layer engine-rejection seam (`lorerunes.reclassify` + `loremaster.store._txn.wrap_store_rejection`, 9 pure-translate wraps routed) is correct, behaviour-byte-preserving, property-guarded, and green on every gate I re-ran independently. Nothing I found blocks the commit.
- deviations (from a clean GO): **none in scope.** Two out-of-scope residuals flagged below (a full-suite uvicorn-boot flake; a broader #408 transport-consistency question) — neither touches this wave.
- Packages considered: none — the mechanism is an internal DRY extraction; Layer 1 IS stdlib `contextlib.contextmanager` (verified installed/used, not hand-rolled `__enter__/__exit__`). No external library evaluated (correct — error-translation POLICY is app-specific).
- Reuse ledger: none (auditor writes no reusable symbol).
- **Graded:** `fb68427` · HEAD-at-report: `fb68427` · **SAME**. Wave is uncommitted in the working tree; graded the working-tree diff over HEAD `fb68427`.
- decisions-needed: none.
- receipt POINTERS: gates §1 · mutation table §2 (with `__file__` receipts) · behaviour/removed-behaviour inventory §3 · untouched-sites §4 · purity+shape-guard §5 · every-`except-SurrealStoreError`-site classification §5.3 · residuals §6.

---

## 0. Scope & method
Independent REFUTE of the 61a-w2 build before commit. I did NOT write this code. Everything below was re-run/re-derived first-hand; the builder/contract/adversary reports were read for claims and then VERIFIED, never trusted. Store: TEST `ws://127.0.0.1:18000` only (never :18500). Mutations were performed in a provenance-asserted `scratch_copy.sh` tree and restored byte-exact (proven by md5).

Store reference cited (not re-transcribed): `docs/reference/surrealdb-31-capabilities.md` §3 for the error-class hierarchy — `SurrealStoreError(RuntimeError)` with `SurrealConnectionError` / `TxnContentionExhaustedError` as SUBCLASSES (`_txn.py:119/123/159`, verified from source), which is why passthrough-first ordering is load-bearing.

---

## 1. GATES — every one re-run by me (counts pasted)

| gate | command | result |
|---|---|---|
| Layer-1 contract | `pytest lorerunes/tests/test_engine_rejection.py` | **20 passed** in 0.03s |
| Layer-2 seam contract | `pytest loremaster/tests/test_engine_rejection_seam.py -p no:xdist` | **56 passed** in 15.44s |
| **contract total** | (20 + 56) | **76** — matches brief's expected 76 |
| full suite | `pytest loremaster/tests -n auto` | **8463 passed, 1 failed, 2 errors**, 50 skipped, 3 xfailed, 317s |
| full-suite failures re-run SOLO | `pytest loremaster/tests/test_migration_wire.py -p no:xdist` | **14 passed** in 26s |
| typecheck | `./scripts/typecheck.sh` | **0 errors** (10 lorerunes / 226 loremaster / … all OK), exit 0 |
| ruff | `uv run ruff check .` | **All checks passed!**, exit 0 |
| currency | `scripts/pending_contract_gate.py --currency` | **PASS** — typecheck/ruff/pytest each GREEN, exit 0 (no RED_ORPHANED) |
| lorerunes purity (repo-wide) | `test_secret_typing.py::…depends_on_nothing_but_the_stdlib` | **1 passed** (rglobs the new module) |

**The 1 failed + 2 errors are OUT OF SCOPE and a load flake, PROVEN:** all three are in `test_migration_wire.py` (HTTP-transport/uvicorn smoke — `test_a_wildcard_allows_an_arbitrary_spoofed_host` + two setup errors), every one caused by `RuntimeError: uvicorn did not report started within 15s` under 64-way `-n auto` load running concurrently with the currency gate + a scratch `uv sync`. Re-run SOLO they pass **14/14**. Zero `engine_rejection` occurrences in any failure/error (grep-confirmed). No wrap-seam test failed anywhere. (See §6 residual R1 — flagged per the unrelated-failures rule.)

---

## 2. MUTATION PROOFS — independently re-derived (NOT the builder's table)

Provenance (#140): performed in `scratch_copy.sh --force /tmp/coldaudit-61aw2-scratch`, which asserts every member imports from inside the copy. Confirmed live from the scratch interpreter:
```
lorerunes:  /tmp/coldaudit-61aw2-scratch/lorerunes/lorerunes/__init__.py
loremaster: /tmp/coldaudit-61aw2-scratch/loremaster/loremaster/__init__.py
```
Each mutation: baseline md5 backed up → mutate → run → observe → restore from backup → **md5 re-verified byte-identical** (`engine_rejection.py 2cec1da6…`, `_txn.py 57f49f90…`, `keeps.py fb692deb…` — all three matched after restore) → final `scratch_copy.sh --verify-only` VERIFIED.

| # | mutation | expected | OBSERVED | control (positive) |
|---|---|---|---|---|
| **(a)** | drop Layer-1 `except passthrough: raise` in `reclassify` | transport-propagation pins RED across all 9 sites | L1 contract **4 RED** (all `TestPassthroughIsReRaisedFirst`) / 16 GREEN; seam **18 RED** (`test_transport_faults_propagate_untouched`, 9 sites × {connection,contention}) | seam **9 GREEN** `test_a_raw_store_error_surfaces_as_the_domain_error` — store-error→domain path intact ⇒ mutation is specific, not a blanket break |
| **(b)** | drop `TxnContentionExhaustedError` from Layer-2 `passthrough` tuple | contention pins RED, connection pins GREEN | seam **9 RED** (all `…-contention`) | **18 GREEN** = 9 `…-connection` + 9 store-error control ⇒ taxonomy binding is the ONE source AND discriminates contention from connection |
| **(c)** | give `KeepStore.delete_keep` a PRIVATE full-idiom copy (revert `with wrap_store_rejection` → local `try/except`, re-add `SurrealStoreError` import) | routing-not-sharing + coverage + reach pins RED | seam **5 RED**: reach `test_no_full_idiom_wrap_appears_outside_the_seam`; coverage `…routed_set_equals_the_invocation_map[keep]` + `…known_wrapping_verbs[keep]`; routing `test_dropping_LAYER1…[keep-delete_keep]` + `test_dropping_LAYER2…[keep-delete_keep]` | **51 GREEN** — the other 8 methods' routing pins, principal/principal_key coverage, and delete_keep's OWN behaviour+transport pins ALL held ⇒ the catch is scoped precisely to the private copy, both seam layers |

All three mutations reproduce the design's two-layer DRY proof: Layer-1 (control-flow) and Layer-2 (taxonomy) are EACH independently shared, and a private copy is caught by reach + coverage + routing simultaneously. The build's own `TestTheMutationProofDiscriminates` control (router moves, private clone doesn't) also passed under (c)'s 51-green.

---

## 3. BEHAVIOUR PRESERVATION (contract-blind DIFF frame) + removed-behaviour inventory

Read all 9 routed diffs. Each replaces
`try: <body> except (SurrealConnectionError, TxnContentionExhaustedError): raise; except SurrealStoreError as e: raise <Domain>(ctx) from e`
with `with wrap_store_rejection(<Domain>, ctx): <body>`, which expands (`_txn.wrap_store_rejection` → `lorerunes.reclassify`) to the **byte-behaviour-identical** control flow: passthrough re-raised FIRST (untouched, same instance), a plain `SurrealStoreError` translated to `<Domain>(ctx)` chained `from` the original (`__cause__` preserved), same context string, everything else propagating unchanged.

Routed set = **9** (matches addendum-4): `PrincipalStore.{create, set_subject}` · `PrincipalKeyStore.mint` · `KeepStore.{create_keep, add_household_member, remove_household_member, set_rank, set_keeper, delete_keep}`. (`AuditStore.append` born-wrapped in w4 — correctly not here.)

**Deliberate refusals raised INSIDE the `with` still PROPAGATE untouched — verified structurally.** Exception hierarchy read from source:
- `KeepStoreError(RuntimeError)`, `KeepNotFoundError(KeepStoreError)`, `KeeperLockoutError(KeepStoreError)` — `keeps.py:154/158/162`
- `PrincipalStoreError(RuntimeError)`, `PrincipalNotFoundError(PrincipalStoreError)`, `PrincipalHasKeepsError(PrincipalStoreError)` — `principals.py:208/212/216`
- `PrincipalKeyStoreError(RuntimeError)`, `PrincipalKeyNotFoundError(PrincipalKeyStoreError)` — `principal_keys.py:173/177`

**None subclass `SurrealStoreError`** — every domain-error family roots at `RuntimeError` directly. Only `SurrealConnectionError`/`TxnContentionExhaustedError` subclass `SurrealStoreError`. Therefore `catch=(SurrealStoreError,)` never re-wraps a `KeepNotFoundError` / `KeeperLockoutError` / `PrincipalNotFoundError` / ghost-email `KeepStoreError` raised inside the block — identical to the old `except SurrealStoreError` clause, which also never matched them. Confirmed live by the (a)/(b) 9-green store-error controls (the domain error surfaces) and by `remove_household_member`/`set_keeper`/`delete_keep` keeping their in-block `raise KeepNotFoundError/KeeperLockoutError` as context lines in the diff.

**Removed-behaviour inventory — nothing lost:**
- The trailing `if <row> is None: raise …` guards stay OUTSIDE the `with` in all sites (as they were outside the old `try`) — verified in every diff hunk. Same failure surface.
- `add_household_member`'s early `return existing` now sits inside the `with`; a `return` exits the context manager with no exception → `reclassify` resumes past `yield`, no except fires — identical to returning inside the old `try`. No behaviour delta.
- No except arm removed, no message changed, no guard moved. `make_error` is lazy (built only on a catch) — matches the old code building the error only in the `except` branch.

---

## 4. UNTOUCHED / EXCLUDED SITES — confirmed byte-unchanged AND correctly excluded by shape

`git diff --name-only` = design doc + `keeps.py` + `principal_keys.py` + `principals.py` + `store/_txn.py` + `lorerunes/__init__.py`. **`tasks.py`, `findings.py`, `floor_calibration/store.py` are NOT in the diff — byte-unchanged**, so the #407 CAS sites, #408 `transitive_blockers`, and the fence are untouched (routing them would have regressed them).

Independently verified each is correctly EXCLUDED by the shape guard (`_try_has_full_idiom`), read from source:
- `tasks.transitive_blockers` (`tasks.py:2495-2513`): sole-body `raise TaskLedgerError(...) from error` BUT **no passthrough-first clause** → deliberately wraps transport too → excluded by shape (addendum-4, PRESERVED; ledgered #408). ✓
- CAS re-validation (`tasks.py:1678`, `tasks.py:2006`, `findings.py:1033`, `findings.py:1088`): two-clause passthrough-first PRESENT, but **multi-statement body** (`_select_row`/`_select_row_by_id` + `_validate_transition`) → not a sole-body translate → excluded. ✓
- fence-verdict (`floor_calibration/store.py:429/707`): multi-statement/branch body → excluded. ✓

---

## 5. PURITY & SHAPE-GUARD checks

### 5.1 lorerunes purity (Layer-1 is stdlib-only)
`engine_rejection.py` imports only `contextlib`, `collections.abc` (read from source). Two independent guards GREEN: the beside-the-helper `TestTheNewModuleImportsNoSibling` (part of the 20), and the repo-wide `test_secret_typing.py::test_the_shared_package_depends_on_nothing_but_the_stdlib` which `rglob`s every `lorerunes/*.py` (1 passed, covers the new file by construction). No `loremaster`/`loresigil`/`lorescribe` import — the leaf stays importable by its siblings.

### 5.2 The shape guard is genuinely property-derived
- `_full_idiom_sites()` `rglob`s EVERY `loremaster.loremaster` module (reach DERIVED from the package tree, NOT a store hand-list) and AST-matches the FULL #400 idiom — a bare-re-raise of BOTH transport classes (spelling-agnostic: one tuple clause OR two separate clauses, via `_bare_reraise_passthrough_classes` UNION) PRECEDING a sole-body `except SurrealStoreError as e: raise <Domain>(...) from e`.
- Allowlist `_ALLOWLISTED_FULL_IDIOM` is **empty** and pinned empty (`test_the_allowlist_is_empty`) — the SHAPE is the sole discriminator; no per-site exemption.
- Positive control on the detector (`test_the_detector_keys_on_the_policy_in_BOTH_house_spellings`) proves it flags both house spellings and NOT: translate-without-passthrough, wrong-order, multi-statement CAS, or a partial (one-class) passthrough in either spelling.
- Conditional-reraise-inside-one-handler evasion honestly pinned as an accepted KNOWN_BOUND (`test_the_conditional_reraise_shape_is_a_KNOWN_BOUND`, #137/#138) with threat model + re-open trigger; I confirmed its discrimination logic (the detector returns False for that shape today) and that it carries the delete-if-closed instruction. Accepting it is the reach STOP-rule applied correctly, not a gap.
- Finds EXACTLY the 9 at HEAD / **0 after extraction** — proven by the green `test_no_full_idiom_wrap_appears_outside_the_seam` and my independent grep (`except (SurrealConnectionError, TxnContentionExhaustedError)` in the 3 routed modules = **ZERO**, all converted to `with wrap_store_rejection`).

### 5.3 EVERY `except SurrealStoreError` site in the package, classified (independent completeness sweep)
Enumerated all 16 code sites (2 more are docstring/comment prose in `_txn.py:169/211`). None is a missed full-#400 pure-translate clone:
- CAS re-validation (has passthrough-first, multi-statement): `findings.py:1033/1088`, `tasks.py:1678/2006` — excluded ✓
- wrap-everything read (no passthrough-first): `tasks.py:2315` (`_reject_unknown_blockers`, multi-statement), `tasks.py:2501` (`transitive_blockers`, sole translate) — excluded ✓
- signal/log-and-continue (no `as`, non-translate): `briefs.py:667/759/1016`, `index/indexer.py:661/1363/1820` — excluded ✓
- fence-verdict (multi-statement/branch): `floor_calibration/store.py:429/707` — excluded ✓
- batch per-item collection (multi-statement, append+continue — NOT a translate): `server.py:3946` (with passthrough-first `3931/3937`) — excluded ✓

Zero missed clones ⇒ the reach guard's green is TRUE.

### 5.4 Registration
No new **workspace member** was added — `engine_rejection.py` is a new FILE inside the already-registered `lorerunes` member (re-exported in `lorerunes/__init__.py` + `__all__`). So `registration_sites.py` (which governs new members) requires no action here; the new file is covered by the existing member's typecheck (`lorerunes` counted 10 source files), Containerfile `COPY lorerunes/`, and testpaths. Verified — not a gap.

---

## 6. RESIDUALS (non-blocking; out of scope for w2)

- **R1 — full-suite uvicorn-boot flake.** `test_migration_wire.py` produced 1 failed + 2 errors under 64-way `-n auto` + concurrent gate/sync load (`uvicorn did not report started within 15s`); passes **14/14 solo**. Unrelated to the wrap seam. **There is 1 failing test (+2 errored) unrelated to our present scope in the loaded full-suite run; all pass in isolation.** Flagged per the unrelated-failures rule; the lead may want the harness's uvicorn boot timeout raised for heavily-parallel runs, but nothing here is a defect in this wave.
- **R2 — #408's transport-consistency question likely has MORE than one site.** The addendum-4 ledger item (#408) names only `tasks.transitive_blockers` as wrapping transport faults into a domain error without a passthrough-first. `tasks.py:2315` (`_reject_unknown_blockers`) does the SAME — `except SurrealStoreError` with no preceding transport passthrough, so a `SurrealConnectionError` is wrapped into `TaskLedgerError`. Recommend the lead's #408 sweep DERIVE the set by property (every no-passthrough-first `SurrealStoreError`-wrapping read-path) rather than the single named site — consistent with the derive-by-property lesson this fork itself kept teaching. Out of scope for w2; both sites correctly untouched and shape-excluded.

---

## 7. Housekeeping
- No file edited in the real tree; no git state mutated. All mutation work was in `/tmp/coldaudit-61aw2-scratch` (a `scratch_copy.sh` throwaway, not a git worktree), restored byte-exact and provenance re-verified; safe to `rm -rf` (I will remove it).
- The 4 untracked `REPORT-*.md` at repo root (builder/contract/adversary/design-sidecar) + this one are the wave's paper trail for the lead to archive per the repo's receipts convention.

**VERDICT: GO.** The extraction is correct, behaviour-preserving over all 9 sites, property-guarded with an empty allowlist and an honestly-pinned bound, and green on every independently-re-run gate. The two residuals are out-of-scope and do not block the commit.
