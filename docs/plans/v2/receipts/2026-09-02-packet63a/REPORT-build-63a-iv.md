# REPORT-build-63a-iv — packet 63 wave 63a-iv BUILD (Opus 4.8)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations**
- deviations:
  - **Findings numbered #444/#445, not #442/#443** — the brief's #442/#443 were anticipated numbers; the two bound findings were filed this session and minted #444 (F-2 L1 dynamic-table blind spot) / #445 (F-3 L2b member-verb reach). Bound notes + the report cite the ACTUAL numbers.
  - **2 PRE-EXISTING unrelated failures** in `test_schema_rebuild.py::TestRebuildingNoticeSeam` (search_code rebuilding-notice MCP-serialization) — PROVEN pre-existing by a reversible stash of my 11 edited files, identical failure at HEAD `7c9dc6a`. NOT caused by this wave; NOT in this wave's scope (the search/notice seam). See §GATES.
  - **`test_mcp_server.py` corpse fix exposes the resolved owner** — the 6 `derive_memory_id` callers there compare to a WIRED governed-tool mint whose owner is the DYNAMICALLY-resolved subject; the `governed_ctx` fixture now resolves that subject via the real `_resolve_subject` seam and exposes `_owner_principal`/`_owner_agent` so the oracle folds ground truth (not a guess). See §CORPSE.
- Packages considered: `contextvars` (stdlib) for the F5 guard-context — READ the installed `contextvars.ContextVar` + `contextlib.contextmanager` signatures (task-local, async-safe across `await`, auto-reset via `.reset(token)`); verdict **REUSED stdlib** (the exact primitive — no package). No other mechanism specified.
- Reuse ledger: see §REUSE (2 new reusable symbols; both dispositioned).
- Graded: n/a (build, not a verdict).
- decisions-needed: none (the audit-DDL fork was ruled #440 wontfix before this wave; item-5 stays a GREEN regression guard, untouched).
- receipt POINTERS: owner-fold → §OWNER-FOLD; F5 wiring → §F5; stale-prose → §STALE-PROSE; bound notes/findings → §BOUNDS; 7-file corpse → §CORPSE; mutation proofs → §MUTATION; gates → §GATES; DRY → §REUSE.

---

## §OWNER-FOLD — item 1 (10.9-B #439 owner fold)

**Production change (`memory/backend.py::derive_memory_id`):** signature gains two REQUIRED keyword-only args `owner_principal` / `owner_agent`; the uuid5 name is now
`memory:{owner_principal}:{owner_agent}:{text}:{refs_stamp}` (field order MY choice — the design left it to the builder; PINNED once chosen). NO WHERE-guard on the create UPSERT (store-ref §2: `UPSERT <id> … WHERE` on an existing id whose WHERE fails is a silent no-op — the unrepresentability comes from the DERIVATION, not a guard).

**Caller (`memory/local.py::remember`):** passes `owner_principal=subject.principal_id, owner_agent=subject.agent_id` (subject is non-None here — an identity-less write already denied above).

Pins → GREEN (all 5 owner-fold contract pins in `test_memory_ownerfold_63a_iv.py`):
- `TestDeriveMemoryIdFoldsTheOwnerPair::test_the_owner_pair_and_the_content_all_fold_into_the_id` (SHAPE, ∀-owner-pairs, order-agnostic) — was RED (TypeError).
- 3 seizure pins (cross-principal, sibling-agent, revive-retired) — were RED (ids collided → row seized).
- `TestSameAgentDedupIsPreserved` (POSITIVE CONTROL / anti-over-fix) — STAYS GREEN (no nonce/timestamp folded; same-agent dedup preserved).

## §F5 — item 2 (10.9-A enforcement completeness wiring)

**Mechanism (`governed.py`):** added `write_guard(label)` (stdlib `contextlib.contextmanager` over a `contextvars.ContextVar[str | None]`) and `active_write_guard() -> str | None`. Task-local + async-safe: the label stays set across the `await` inside the `with` block and auto-resets on exit (even on raise).

**Wired into 5 sites** (each wraps its store mutation in `with governed.write_guard("<frame>"):`):
- `governed.py::guarded_write` → wraps the `execute_read_transaction` guarded mutation (label `"guarded_write"`).
- `local.py::remember` → wraps the create-path `self._apply(...)` UPSERT (label `"remember"`).
- `local.py::_reinforce` → wraps the importance-bump loop (label `"_reinforce"`).
- `local.py::_replay_record` → wraps the ledger-replay `self._apply(...)` UPSERT (label `"_replay_record"`).
- `local.py::_recreate_memory_table` → wraps the `REMOVE TABLE` (label `"_recreate_memory_table"`).

Pins → GREEN (`test_memory_enforcement_63a_iv.py`):
- L2a `test_every_allowlisted_local_frame_calls_write_guard` (all 4 frames) + `test_guarded_write_sets_a_write_guard_context` — were RED (unwired).
- L2b `test_the_guard_context_mechanism_is_built` (attrs exist) + `test_every_observed_memory_mutation_is_attributed_to_a_frame` (all 3 seam paths carry a non-None label) — were RED (mechanism unbuilt / label=None).
- L1 (6 GREEN) unchanged — the derived raw-mutation set is still {`_upsert_fragment`/UPSERT, `_reinforce`/UPDATE, `_recreate_memory_table`/REMOVE}; wiring adds no raw mutation string.

## §F-B — item 3 (10.9-C `_reinforce`) — untouched, STAYS GREEN

Both `_reinforce` pins (bump-set≡served-set, statement-touches-only-importance) were GREEN at HEAD and STAY GREEN: wrapping the loop in `write_guard` changes no statement, and `_reinforce` still emits its ` SET importance = math::min(...)`-only UPDATE via `self._query` (the `_capture_reinforce_statements` pin wraps `backend._query`, still hit inside the `with`).

## §STALE-PROSE — item 4a (P8d prose currency)

- `backend.py` module prose (2 sites) + `derive_memory_id` docstring: rewritten to the owner-inclusive scheme; the retired literal `memory:{text}:{refs_stamp}` and the `scheme is UNCHANGED` claim REMOVED; the docstring now MENTIONS the owner.
- `server.py` `lore_remember` served description: `"Re-saving the same text dedups (same id)"` → `"Re-saving the same text as the same agent dedups in place (same id); a different agent's identical text is a distinct note"` (per-agent qualifier; trust Leg 1).

Pins → GREEN (`test_memory_prose_currency_63a_iv.py`, all 4): served-description-per-agent, docstring-mentions-owner, no-owner-less-literal, no-scheme-unchanged-claim. (Sweep scans production `_MEMORY_MODULES = backend/ledger/local` only.)

## §BOUNDS — item 4b (F-2/F-3 named bounds — WHEN YOU CANNOT CLOSE A HOLE, PIN IT)

- **F-2 (finding #444):** L1 AST scan is blind to a DYNAMICALLY-named governed write (runtime-variable table name renders `{tbl}`, matches neither the literal `memory` nor `{MEMORY_TABLE}`). Bound note added to `_governed_contract.governed_table_raw_mutation_sites`' docstring + a **pin-the-miss** in `test_memory_enforcement_bounds_63a_iv.py` (asserts the hole exists, with a positive control that the constant-named form IS derived → RED the day L1 is widened). RE-OPEN TRIGGER: any production write constructing a governed table name dynamically.
- **F-3 (finding #445):** L2b runtime reach covers only the 3 member-verb seam paths; `_replay_record`/`_recreate_memory_table` carry L2a structural coverage only. Bound note added to `_governed_contract.observe_governed_table_writes`' docstring (a coverage-shape note, not a discriminable hole). RE-OPEN TRIGGER: either frame becoming member-reachable.

## §AUDIT-DDL / item 5 — untouched (GREEN regression guard)

Per finding #440 / §10.8 supersession, item-5 (`test_audit_ddl_composition_root_63a_iv.py`) is a GREEN-at-HEAD composition-root regression guard on the existing `generate_ddl` audit-DDL fold. NOT touched; STAYS GREEN. No AuditStore wiring added (the wontfix ruling).

## §CORPSE — the 7-file removed-behaviour worklist (adversary §F-1)

The owner-fold signature breaks every 2-arg `derive_memory_id` caller + every oracle reconstructing the retired scheme. All updated to the new signature, **assertions preserved** (removed-behaviour dual — the old world's virtue: deterministic, reproducible, ref-order-insensitive, distinct-inputs-distinct-id; the owner is now part of the basis). Golden literals RECOMPUTED for the new scheme by an INDEPENDENT convention reimplementation (`scripts/compute_ownerfold_golden_ids_63a_iv.py` — raw uuid5, NOT `derive_memory_id`), cross-checked against production (§MUTATION).

| file | sites | how updated | assertions |
|---|---|---|---|
| `test_memory_backend.py` | oracle `expected_memory_id` (def) + 3 `_LITERAL_ID_*` + 6 inline golden + ~7 direct callers + module docstring | oracle folds owner (default = shared `_GOV_SUBJECT` pair `corpse_a_admin`/`corpse_a_agent`, matching every backend mint via `_GovernedTestBackend`); literals recomputed; direct callers pass `_OWNER_PRINCIPAL`/`_OWNER_AGENT` | preserved (determinism + independent-oracle cross-check + backend-parity) |
| `test_memory_ledger.py` | oracle `expected_memory_id` (def) + 2 docstrings | oracle folds a FIXED owner pair (ledger is owner-agnostic — keys on the id it is handed; no backend comparison) | preserved (dedup/retrieval by id) |
| `test_mcp_server.py` | 6 `derive_memory_id` callers + `_GovernedAppContext` proxy + `governed_ctx` fixture | fixture resolves the subject via the REAL `_resolve_subject` seam and exposes `_owner_principal`/`_owner_agent`; the 6 callers fold that GROUND-TRUTH owner | preserved (served-tool mint parity) |
| `test_schema_rebuild.py` | 1 caller (`ledger_only_id`) | folds `_GOV_SUBJECT` owner (a concurrent remember mid-rebuild) | preserved (replay-in-place by stored id) |
| `test_memory_cutover.py` | 1 caller (`_seed_ledger`) | folds `_GOV_SUBJECT` owner | preserved (restore keys + re-mints in place) |
| `test_search.py` | 1 inline uuid5 (fixture `_backend_recalled`) | inline literal → owner-inclusive shape (placeholder owner; the id is a realistic well-formed value NEVER asserted — pipeline reads only `.text`/`.score`/`.refs`) | preserved (unused id) |
| `_memory_fakes.py` | `FakeMemoryBackend.remember` | folds the owner from its `subject` EXACTLY as the real backend (calls the SAME `derive_memory_id` — ONE derivation policy; empty owner for a legacy None subject) — closes the P5 divergence | preserved + fake↔real parity |

## §MUTATION — mutation proofs (real tree, `cp -a` backup + byte-exact restore, #140)

Both mutated the REAL tree with a content backup and restored byte-exact (md5 verified); `loremaster.__file__` printed each time = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` (in-tree, not a poisoned copy).

- **Owner fold** — reverted the derivation to drop the owner (`(_ID_PREFIX, owner_principal, owner_agent, text, refs_stamp)` → `(_ID_PREFIX, text, refs_stamp)`, signature kept so callers don't TypeError). Result: **4 failed, 1 passed** — the 3 seizure pins (`test_a_non_owner_reremember_mints…`, `test_a_sibling_agent_reremember…`, `test_a_non_owner_reremember_does_not_revive…`) + the shape pin (`test_the_owner_pair_and_the_content_all_fold_into_the_id`, `AssertionError: owner_principal not folded`) went RED; the same-agent-dedup CONTROL stayed GREEN. md5 BYTE-EXACT-RESTORED.
- **F5 wiring** — unwired the `remember` frame (removed its `with governed.write_guard("remember"):` wrapper). Result: **2 failed, 2 passed** — L2a `test_every_allowlisted_local_frame_calls_write_guard` (remember no longer calls write_guard) + L2b `test_every_observed_memory_mutation_is_attributed_to_a_frame` (`UNCLASSIFIED … [('execute_transaction', 'UPSERT')]`) went RED; the guarded_write-L2a + L2b-mechanism pins stayed GREEN (only remember was unwired). md5 BYTE-EXACT-RESTORED.

The RED-at-HEAD contract pins are self-mutation-proven by the HEAD↔build delta (the wave IS the mutation); these two additionally prove the load-bearing pins discriminate away from a plausible wrong build.

## §GATES — RED→GREEN + gate output

- **5 contract modules** (`test_memory_{ownerfold,enforcement,reinforce,prose_currency}_63a_iv.py` + `test_audit_ddl_composition_root_63a_iv.py`), `-n auto`, TEST store ws://127.0.0.1:18000: **`24 passed`** — the 12 RED-at-HEAD (owner-fold 4 · stale-prose 4 · F5-L2 4) are GREEN; the 12 GREEN-at-HEAD (owner-fold control 1 · F-B 3 · F5-L1 6 · audit-DDL 2) stay GREEN.
- **All `test_*_63a*.py` (15 files, incl. the new bounds file) + `test_mcp_server.py`**: **`794 passed`** in 140s (exit 0, 0 skipped that matter — the run is 0-failed).
- **`test_memory_backend.py` + `test_memory_ledger.py` + `test_memory_cutover.py` + `test_schema_rebuild.py` + `test_search.py`**: **`344 passed, 2 failed`** — the 2 failures are `test_schema_rebuild.py::TestRebuildingNoticeSeam::{test_a8a_search_code_empty_in_progress_raises_rebuilding_error, test_a8a_search_code_rebuilding_error_survives_mcp_serialization}`, **PROVEN PRE-EXISTING**: with all 11 of my edited files stashed, the identical assertion fails at HEAD `7c9dc6a` (`2 failed, 5 passed`); files restored byte-clean. They concern the `search_code` rebuilding-notice MCP serialization seam — untouched by this wave.
- **61-family sweep** (`test_pdp_oracle_61b` · `test_tool_population_61b` · `test_visible_keeps_61b` · `test_keep_remediation_{store,cli}_61` · `test_principal_delete_cascade_61`) **+ the re-pointed `test_mcp_server` classes** (`TestSaveMemoryCutover` + `TestSaveMemoryReservedMetadataGuard`): **`79 passed`**. (No `test_*_60*.py`/`test_*_62*.py` files exist — 60/62 fold into the 61/63a suites.)
- **CORPSE-B/C** (`test_agent_capability_seams.py` + `test_keeps_store.py`): **`83 passed`** (neither references `derive_memory_id` — confirmed 0 hits).
- **`uv run ruff check`** on all 14 touched files: **All checks passed!**
- **`bash scripts/typecheck.sh`**: **EXIT=0** (loremaster leg `no issues found in 257 source files`; all legs OK). Note: the initial run flagged 12 `attr-defined` on `cutover_ctx._owner_principal` (typed `AppContext`); fixed by the file's own `getattr(ctx, "…")` idiom (ruff selects no `B`, so B009 does not apply; mypy returns `Any`).

## §REUSE — DRY ledger (brief-base §6)

| new symbol | lore query / search | returned | disposition |
|---|---|---|---|
| `governed.write_guard` / `governed.active_write_guard` | stdlib `contextvars` + `contextlib.contextmanager` | `ContextVar.set/get/reset` + `@contextmanager` is the exact task-local, async-safe, auto-reset primitive | **REUSED stdlib** `contextvars` (no package; no hand-rolled stack). The F5 substrate (`observe_governed_table_writes`) was already built getattr-tolerant against these two names — I only supplied the production mechanism the contract named. |
| `scripts/compute_ownerfold_golden_ids_63a_iv.py` (`convention_id`) | independent id oracle for the corpse golden literals | reimplements the uuid5 convention directly (not `derive_memory_id`) so the frozen literals stay a genuine cross-check | **HAND-ROLLED** (deliberately independent of the code under test — a helper that CALLED `derive_memory_id` would make the parity pins tautological). Committed under `scripts/` (instrument-as-deliverable). |

The owner fold is ONE function (`derive_memory_id`); `remember` and `FakeMemoryBackend.remember` both CALL it with owner-from-subject (never a second derivation policy). The F5 guard is ONE pair of functions (`write_guard`/`active_write_guard`) every frame CALLS (never a cloned contextvar).
