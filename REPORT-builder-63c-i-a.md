# REPORT-builder-63c-i-a — the 63c-i-a BUILD (agent roster governed)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **state:** done — 63c-i-a BUILT, NOT committed, NOT deployed (base `4d6d53e`; HEAD-at-report `5ce89cd`, which adds only `REPORT-lead-63c.md`). All 10 brief items dispositioned (item 10 declined, as permitted).
- **deviations:** none unruled. FORK-B1 (item 5 D3 needed a test file outside the writable set) escalated BEFORE editing and ruled (A) by the lead (#17008); the fold stayed inside that narrow grant (§D3).
- **Packages considered:** none — no mechanism specified beyond the ruled build; the charset predicate is `re` (stdlib, `fullmatch`), homed in `lorerunes` as ruled (A4).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 8 new symbols, all dispositioned (§DRY): 2 EXTENDED-by-move into `lorerunes`, 2 REUSED idiom (`_COL_*`), 4 HAND-ROLLED with reasons.
- **Graded:** n/a (builder report — no verdict rendered on another's artifact).
- **Gates (final bytes):** full suite ALONE `-n 12` **`11498 passed, 62 skipped, 3 xfailed`, 0 failed** · ruff clean · typecheck rc 0 every leg · currency `typecheck GREEN · ruff GREEN` with both yaml entries deleted (11/11 SELF-DESTRUCT before deletion).
- **RED@HEAD → GREEN:** 250 declared reds (25 contract files, 3036 ids) → 250 green; 0 of 2767 HEAD-greens turned; identical 19 skips (packet-43). Two real-tree mutation proofs HELD (routing-not-sharing on the server home: 15/15 exact; the served sample size: 1/1 exact).
- **decisions-needed:** none blocking. FLAGS for the lead (§FLAGS): F-1 stale fake docstring/comment (outside grant), F-2 a third raw-CREATE agent helper in `test_comms_schema.py`, F-3 `scripts/probe_governed_63c.py`'s C-agent control now fails by design (outside writable set), F-4 an ownerless-but-scoped raw row blocks the message migrate loudly (spec-consistent). Friction filed: lore #483 (`lore_index(reconcile=True)` aborted client-side at 300 s though the sweep completed; one `:18500` connection drop on the first filing attempt).
- **receipt pointers:** §0 capability · §FORK-B1 · §ITEMS · §D3 · §RED · §MUTATION · §DUAL · §DRY · §FLAGS · §GATES · §BACKUP (patch md5 `113d0143…`) · §A instruments.

## 0. Capability check (brief-base §4) — 2026-09-25
- Idle-gate contract written, no denial: `/tmp/claude-idle-gate-lore/a3c3f778-deba-476f-81cc-e0ff2b54daec-builder-63c-i-a.contract` = `{"artifact": "REPORT-builder-63c-i-a.md"}` (session id = this agent's scratchpad id).
- lore reachable: `lore_comms register` OK (session `63c-20260924`, role `builder`, cadence `≤20m`); `lore_index()` at start: watched root `/workspace` branch `feat/surreal-unification` ref `4d6d53e` = HEAD, last_sync 98 s.
- Store reference read FIRST (§1.1 OVERWRITE-for-fields / IF NOT EXISTS for indexes, §1.2 full-replace drops a stored ASSERT, §1.4 new field on a populated table is `option<>`, §6 vendor lies, §7 `string::matches` function form).
- grep/rg hook-blocked (#473): every textual sweep in this build is `awk`, a non-symbol textual seam (brief-base §4 fallback, said here).

## FORK-B1 — item 5 (D3 fold) vs the writable set (raised 2026-09-25 ~19:45 EDT, BEFORE any edit; build of every other item proceeds)
- **The two readings.** Brief item 5: *"D3 (REFACTOR phase): fold `_create_agent` onto `seed_agent_legacy`"* — `_create_agent` lives in `loremaster/tests/test_agent_owns_principal_schema.py` (11 call sites; the test module docstring of `test_agent_governance_63c_i_a.py` calls the fold "a builder action"). Brief item 1 + WRITABLE SET: *"The ONE granted test edit … No other test file may be edited"*; the writable set lists `_comms_fakes.py` (item 1 only) and no other test file.
  - (A) item 5 is itself a grant: edit `test_agent_owns_principal_schema.py` — delete `_create_agent`, route its 11 call sites through `_governed_contract.seed_agent_legacy(connection, row_id=…, name=…, session=…, role=…, owner_principal=RecordID(PRINCIPAL_TABLE, owner_bare_id))` (feasible: `seed_agent_legacy` pops `owner_principal` from `**overrides` verbatim; its default role is `"builder"` vs `_create_agent`'s `"worker"`, so each site passes `role="worker"` to keep the pkt-62 pins byte-equivalent).
  - (B) the writable set wins: D3 is not buildable under this brief; it is the lead's to re-grant or re-route.
- **Recommendation:** (A) — the operator ruled D3 and the brief names it as a builder item; the edit is mechanical and behaviour-preserving. **I have NOT made it**; awaiting the lead's ruling. Everything else is built independently of it.
- FORK-B1 RULED (A) by the lead (`lead-63c-2`, lore_comms #17008, acked 2026-09-25): `test_agent_owns_principal_schema.py` granted for the D3 fold ONLY. Receipts in §ITEMS row 5 / §D3.
- `lorerunes` needed no other workspace member change; no new workspace member (so `registration_sites.py` does not apply — `identifiers.py` is a module inside the existing `lorerunes` member).

## ITEMS — brief items 1–10 (all measured at the working tree over HEAD `4d6d53e`, 2026-09-25)
| # | what | where (symbols) | receipt |
|---|---|---|---|
| 1 | fake's `try`/`except ImportError` deleted; `is_legal_identifier` imported at MODULE TOP | `_comms_fakes.py`: `from lorerunes import is_blank, is_legal_identifier`; `FakeAgentRegistry._shared_identifier_predicate` body → `return is_legal_identifier` | the r4a SHAPE + allowlist pins and the r3 EFFECT pin green in the 25-file run (§RED) |
| 2 | both 63c-i-a entries deleted → `bounds: []` (the now-false "⚠ ADDED 2026-09-24" comment line deleted with them; nothing added) | `scripts/pending_contracts.yaml` | BEFORE deletion the gate itself reported **11/11 SELF-DESTRUCT** (10 files "produced NO mypy errors" + `lorerunes.is_legal_identifier` "now RESOLVES"); AFTER: `typecheck GREEN · ruff GREEN` (§GATES) |
| 3a | MP-F: re-register never stamps `owner_agent`/`scope` either, ∀ rows | `AgentRegistry.register` docstring, `owner_principal_id` arg | prose; pinned behaviour: `test_a_credentialed_re_register_never_stamps_an_UNSTAMPED_row_mint_once_for_every_row` green |
| 3b | MP-C: the bound is the NAMED constant, read in exactly one line | `principals._REFUSAL_ID_SAMPLE_SIZE = 10`; `shown_ids = owned_unscoped_ids[:_REFUSAL_ID_SAMPLE_SIZE]` in `_migrate_agent_owner` | `R_Q5_1[perturbed-bound]` green (the slice follows a patched constant) |
| 3c | A4-bis: the server's decision home calls the shared decision | `AppContext._is_comms_charset_legal` → `return is_legal_identifier(value)` (house lazy import) | §MUTATION proof 1 |
| 3d | `LegacyMapping` docstring gains agent = OWNED-BY-THE-OPERATOR | `governed.LegacyMapping` | prose (unpinnable by construction, per the contract docstring) |
| 4 | the 2 production prose lines adversary-r2 §11 names | (a) `agents.py` comment above the pattern: "enforced here … AND by the store's own ASSERT (defense-in-depth)" → rewritten (store ASSERT dropped; writer validates via the shared decision; the name is a re-export); (b) `_is_comms_charset_legal` docstring: "Both now move with ONE edit, which `test_perturbing_the_SHARED_predicate…` proves" → now names the DECISION-mutation pins (`test_the_identifier_decision_is_the_SHARED_is_legal_identifier`, `TestTheTrafficLineSkipGateMovesWithTheSharedDecision63cIA`) and says the pattern-perturbation pin proves only "no private pattern" | both pin names verified to exist (awk over the test file) |
| 5 | D3 fold (REFACTOR; granted by FORK-B1 (A)) | `test_agent_owns_principal_schema.py`: `_create_agent` deleted; 11 sites → `seed_agent_legacy(conn, row_id=…, name=…, session=…, role="worker"[, owner_principal=RecordID(PRINCIPAL_TABLE, …)])`; `+from _governed_contract import seed_agent_legacy`; 3 imports orphaned by the deletion removed (`datetime`/`UTC`/`_AGENT_STATUS_ACTIVE` — ruff F401, forced) | §D3 |
| 6 | refusal's served sample size = ids ACTUALLY named | `"First {len(shown_ids)} of {offending_count} ids shown: …"` | all four `R_Q5_1` populations green; §MUTATION proof 2 (serving the constant reds exactly `[below-cap]`) |
| 7 | `_IDENTIFIER_CHARSET_PATTERN = AGENT_NAME_PATTERN.pattern` | `surreal_schema.py` (+ `AGENT_NAME_PATTERN` added to its `lorerunes` import; ruff I001 placed the import line) | the charset TEXT pin green; `brief.name`'s ASSERT byte-identical (DDL unchanged for `brief`) |
| 8 | `_REFUSAL_ID_SAMPLE_SIZE` states WHY (a `#:` constant docstring) | `principals.py` | prose: bound exists for legibility at cutover; full count always served beside it; value not normative |
| 9 | re-register docstring: "does NOT re-stamp — from ANY caller, including a different householded principal" | `AgentRegistry.register` docstring (and the CREATE-content comment) | C-3's refusal NOT built (i-b's) |
| 10 | MAY collapse `_shared_identifier_predicate` | **declined** — helper kept (its dead `None` return type stays for i-b); minimal test edit | — |

**The build itself (the contract's spec, beyond the 10 items):**
- `lorerunes/lorerunes/identifiers.py` (NEW): `AGENT_NAME_PATTERN` (the ONE compile of the charset) + `is_legal_identifier` (`fullmatch`, #210); re-exported from `lorerunes/__init__.py` (`__all__` += 2).
- `agents.py`: `AGENT_NAME_PATTERN` becomes an explicit re-export (`from lorerunes import AGENT_NAME_PATTERN as AGENT_NAME_PATTERN  # noqa: PLC0414` — the repo's `no_implicit_reexport` idiom, same object; `import re` dropped, forced); `register(..., session_keep_id=None)`; `_refuse_an_inconsistent_provenance_pair` (A3 XOR) and `_refuse_an_invalid_identity` (§4.2 MOVE: `is_legal_identifier` per field, `is_blank` role; teaching; value via `render_fenced`) both BEFORE `_select_row` on every path; NEW `InvalidAgentIdentityError(AgentRegistryError)`; CREATE content stamps `owner_agent = RecordID(agent, id)` (every create) and `scope = keep_scope(session_keep_id)` (or NONE); new `_COL_OWNER_AGENT` / `_COL_SCOPE`.
- `server._comms_register`: `session_keep_bare: str | None = None` initialised, set in the principal branch (the SAME value the SF-63-1 gate checks), passed UNCONDITIONALLY as `session_keep_id=`.
- `surreal_schema.py`: `name`/`session`/`role` constraints → `""` (rows KEPT, so `DEFINE FIELD OVERWRITE` — store-ref §1.1/§1.2 — drops the stored ASSERT on a long-lived store); `status` ASSERT KEPT; the hand-rolled `owner_principal` spec row + `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` + its index line DELETED; `_agent_statements` appends `_governed_field_specs()` + `_governed_index_statements("agent")`. Emitted agent DDL = ruling §2.1's net DDL exactly (`owner_principal`/`owner_agent`/`scope` `OVERWRITE option<…>`, `agent_scope` + `agent_owner_principal` `IF NOT EXISTS`).
- `principals._migrate_agent_owner(store, keep_store, principal_store)`: scope-keyed counts (`_scope_count`); §2.1 row precondition = ONE `SELECT VALUE id … WHERE scope IS NONE AND owner_principal IS NOT NONE` BEFORE any write (count and sample from the same read, so they cannot describe different sets; sorted for a deterministic sample); refusal names the full count beside "agent row(s)", "first N of M ids shown", the ids, "by hand", "no row was stamped"; else project keep via `get_or_create_keyed(PROJECT_KEEP_KEY, …)` and ONE statement `UPDATE agent SET owner_principal = type::record('principal', $owner), owner_agent = id, scope = $scope WHERE scope IS NONE` under `governed_exempt("migrate-governed", statement=…)`.
- Prose kept true: the `brief.name` spec comment ("shares the SAME identifier charset ASSERT as agent.name" — falsified) rewritten; `_agent_statements` docstring and the `_AGENT_FIELD_SPECS` comment rewritten; `agents.py` module API docstring gains `session_keep_id` + `InvalidAgentIdentityError`.

## D3 — the fold's receipts (FORK-B1 (A), lead #17008)
1. Diff: `git diff loremaster/tests/test_agent_owns_principal_schema.py` → `1 file changed, 78 insertions(+), 66 deletions(-)` (copy: `<scratchpad>/d3_fold.diff`, pre-fold content backup `<scratchpad>/test_agent_owns_principal_schema.pre-fold.py`). The file's only changes: helper deleted, 11 call sites, `+import seed_agent_legacy`, 3 forced import removals. No assertion, fixture value, test name or docstring touched.
2. `--collect-only` ids: 27 before, 27 after, `diff` EMPTY (`owns_ids_before.txt` / `owns_ids_after.txt`).
3. `uv run pytest -q -n 4 loremaster/tests/test_agent_owns_principal_schema.py` → `27 passed in 2.70s`.
4. DUAL row — `_create_agent` DELETED: (a) default `role="worker"` → **preserved** by the explicit `role="worker"` at every site (seed's default is `"builder"`); (b) content columns (name/session/role/`status="active"`/registered_at/heartbeat_at, + `owner_principal` RecordID only when an owner was given) → **preserved** (`_governed_contract._agent_content` writes the same six; `seed_agent_legacy` pops `owner_principal` from `**overrides` verbatim, and omits it when not passed — the ownerless `option<>` path is still exercised); (c) return value (the CREATE's rows) → **dropped-deliberately**: no call site consumed it (all 11 were bare `await`s; seed returns the bare id); (d) its docstring's re-dated history (the D3 note) → **dropped-deliberately**: it described the helper being deleted; the same history lives in `seed_agent_legacy`'s docstring.

## RED — RED@HEAD → GREEN accounting (declared BEFORE the build)
- **HEAD run** (unbuilt production, tests at `4d6d53e`; the 25 files of the contract set `files5.txt` — md5 `2e6cc82c…`, identical set to the contract/adversary lanes' copy; `loremaster.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`), `-n 8`, 19:31–19:36 EDT: **`199 failed, 2767 passed, 19 skipped, 51 errors in 304.13s`** over 3036 collected ids → the declared RED set = 250 ids (`<scratchpad>/redhead_reds.txt`). Every one right-reason on inspection: `TypeError: AgentRegistry.register() got an unexpected keyword argument 'session_keep_id'` (incl. all 51 setup ERRORs in `test_mcp_server.py` — fixtures that register), missing `lorerunes.is_legal_identifier` / `AGENT_NAME_PATTERN`, the register-surface pins, the unbuilt migrate/DDL legs.
- **Built run** (same 25 files, same ids, `-n 8`, 19:43–19:48 EDT, same provenance): **`3017 passed, 19 skipped, 4 warnings in 306.42s`** — 0 failed, 0 errors.
- **Diff by id** (`red_green_diff.py`, §A): `ids: head=3036 built=3036 | gone=0 new=0` · `RED@HEAD: 250 -> now passed: 250 still red: 0` · `HEAD greens: 2767 -> turned non-passed: 0` · `skipped built=19 head=19 same_set=True`.
- The 19 skips are ALL `test_derivation_source_unification.py` packet-43 legs (edge ENFORCED flip "BLOCKED until _derive_edges") — identical at HEAD, not i-a's. **Every 63c dirty-store / legacy-row leg RAN and PASSED** (75 ids matching Dirty/Legacy; the 10 skipped matches are the packet-43 `…MigratesADirtyStore` legs).
- Note: this 25-file run preceded the D3 fold and three comment/docstring-only production edits (brief.name comment, agents module API docstring); the full suite (§GATES) covers the final bytes.

## MUTATION — the shared home is SHARED, and the served count is DERIVED (real tree, `scripts/mutation_proof.py`, content-restored byte-exact)
Declared RED sets were taken from `pytest --collect-only` BEFORE each run.
1. **Routing-is-not-sharing on MY build** (the N1 wrong build): `server.py` `_is_comms_charset_legal` body `from lorerunes import is_legal_identifier … return is_legal_identifier(value)` → `return AGENT_NAME_PATTERN.fullmatch(value) is not None`. Declared 15: `test_the_identifier_decision_is_the_SHARED_is_legal_identifier[{name,session}-{refuse,skip}-policy]` (4) + `test_the_SKIP_gate_moves_with_the_SHARED_is_legal_identifier[*]` (10) + `test_no_production_module_outside_lorerunes_DECIDES_with_the_pattern` (1). Run `test_agent_registry.py test_comms_footer.py -n 8` → `15 failed, 567 passed in 16.25s` · `tree restored byte-exact (… server.py: md5 d1dbdd7a…)` · **`PROOF HELD — the declared RED set fired EXACTLY`**, exit 0. (The `[register]` and `[fake]` legs stayed green — correct: those consumers do not read the server home.)
2. **Item 6 — the served sample size** (the PXlie wrong build): `principals.py` `First {len(shown_ids)} of` → `First {_REFUSAL_ID_SAMPLE_SIZE} of`. Declared 1: `test_R_Q5_1_…[below-cap]` (at/above-cap shown == the constant; under perturbation the patched constant == shown, so only below-cap can see it). Run `test_agent_governance_63c_i_a.py -n 8` → `1 failed, 85 passed` · restored byte-exact (`principals.py` md5 `bcef1d2f…`) · **`PROOF HELD`**, exit 0.
- The in-suite identity sweeps (`patch_shared_object_everywhere`, identity-keyed) are themselves mutation proofs of every consumer of `lorerunes.is_legal_identifier` / `AGENT_NAME_PATTERN` / `is_blank` / `keep_scope`; they are green on this build (§RED), and proof 1 shows they bite on it.

## DUAL — removed-behaviour inventory (every deleted/replaced production branch; adjudicated)
| # | removed / replaced | adjudication |
|---|---|---|
| R1 | `agent.name` / `agent.session` store charset ASSERT (`_IDENTIFIER_CHARSET_ASSERT` in `_AGENT_FIELD_SPECS`) | **dropped-deliberately, MOVED** — ruling §4.2 DROP+MOVE; preserved app-side in `AgentRegistry.register` → pinned by `TestQ3RegisterValidatesIdentityBeforeStoreIO63cIA` (13-shape hostile corpus × both fields, zero rows written) + the dirty-store drop legs (`TestTheAgentAssertsDropFromADirtyStore63cIA`) |
| R2 | `agent.role` store non-empty ASSERT | **dropped-deliberately, MOVED** — ruling §4.2; `is_blank` in `register`, pinned by `test_register_refuses_a_blank_role_before_any_store_write` + `test_the_blank_role_rule_is_the_SHARED_is_blank` |
| R3 | hand-rolled `owner_principal` spec row + `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` + its `_plain_index` line | **preserved-with-pin** — ruling §2.1: re-landed byte-identical via the shared emitter (same field def, same index NAME → `IF NOT EXISTS` no-op on a live store, §1.5); pinned by `test_agent_owns_principal_schema.py`'s exactly-once/route/no-ASSERT/no-DEFAULT pins. `_AGENT_OWNER_PRINCIPAL_INDEX_FIELDS` had no other consumer (awk over every tracked `.py`: 0 hits after deletion) |
| R4 | `agents.AGENT_NAME_PATTERN` as its OWN compiled object (+ `import re`) | **replaced** — ruling A4 (amendment-2): the name now binds THE `lorerunes` object; `.pattern` text identical (pinned `== r"^[a-z0-9][a-z0-9_-]{0,63}$"` in `test_agent_registry.py`); existing importers (`server.py`, tests) bind the same object |
| R5 | `_is_comms_charset_legal`: `AGENT_NAME_PATTERN.fullmatch(value) is not None` | **replaced** — amendment-4 A4-bis: `is_legal_identifier(value)` (same `fullmatch` semantics); pinned by the `[skip-policy]` / `[refuse-policy]` legs + §MUTATION 1 |
| R6 | `_migrate_agent_owner` OWNER-keyed: counts via `_owner_count(agent)`, `UPDATE … SET owner_principal … WHERE owner_principal IS NONE` | **replaced** — ruling §6: scope-keyed counts, ONE 3-column statement `WHERE scope IS NONE`; pinned R-Q5-1..3 + exempt-token golden + idempotence. Consequences, each stated: (a) `already_migrated` now counts scope-set rows, not owner-set rows (§6: `scope IS NONE` is THE unmigrated predicate); (b) an owned-but-unscoped row was silently SKIPPED before, is now a LOUD refusal of the whole table (§2.1 precondition, #470); (c) an OWNERLESS-but-SCOPED agent row (unreachable through the writer after A3 + mint-once; reachable only by a raw write) was stamped before and is now skipped — **spec-consistent** (MP-F names exactly this row as escaping `WHERE scope IS NONE`), but see FLAG F-4 |
| R7 | migrate noun/label `"governed agent-owner backfill"` | **replaced** → `"governed agent backfill"` (the statement is no longer owner-only; the old noun would falsify the served error prose). No pin read it (awk: 0 hits in tests/docs) |
| R8 | old migrate did not mint the project keep | **replaced** — ruling §6: the agent leg now mints/gets the canonical project keep via the SAME `get_or_create_keyed(PROJECT_KEEP_KEY, …)` the memory/message legs use; minted only AFTER the precondition passes (a refusal writes nothing) |
| R9 | `_comms_fakes` `try`/`except ImportError: return None` guard | **dropped-deliberately** — its removal trigger (the predicate exists) fired; brief item 1 |
| R10 | `test_agent_owns_principal_schema._create_agent` | §D3 row 4 |
| R11 | `pending_contracts.yaml` bounds `packet-63c-i-a-contract-r2` / `-r3` | **dropped-deliberately** — self-destructed on their own triggers (§GATES) |

## DRY ledger (brief-base §6) — every new reusable symbol
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `lorerunes.identifiers.AGENT_NAME_PATTERN` | `lore_search("is_legal_identifier AGENT_NAME_PATTERN fullmatch decision home", tier=lore)` + `lore_search("predicate deciding whether a string is a legal agent identifier…")` | only reports/amendments describing the move; production home = `loremaster.agents.AGENT_NAME_PATTERN` (awk-confirmed the sole compile) | **EXTENDED (moved)** `loremaster.agents.AGENT_NAME_PATTERN` — the same pattern, now homed in `lorerunes` and re-exported from `agents` (A4) |
| `lorerunes.identifiers.is_legal_identifier` | same two queries | production decision = `AppContext._is_comms_charset_legal` (server-private) | **EXTENDED (moved)** `_is_comms_charset_legal`'s decision into `lorerunes`; the server home now calls it |
| `AgentRegistry._refuse_an_inconsistent_provenance_pair` / `_refuse_an_invalid_identity` | (register-private seams) | the fake's `_refuse_what_the_writer_refuses` mirrors them in the TEST tree | **HAND-ROLLED** as private methods: they ROUTE to the shared predicates (`is_legal_identifier`, `is_blank`); the only policy in them is the A3 XOR, which has exactly one production caller |
| `InvalidAgentIdentityError` | `lore_get_symbol` on `agents` exceptions (read the class list) | `AgentRegistryError` family; no identity-violation class existed | **HAND-ROLLED** subclass of `AgentRegistryError` (the tests catch the base) |
| `principals._REFUSAL_ID_SAMPLE_SIZE` | named by the contract (MP-C) | — | **HAND-ROLLED** as ruled |
| `agents._COL_OWNER_AGENT` / `_COL_SCOPE` | the module's own `_COL_*` idiom | `_COL_OWNER_PRINCIPAL` etc. | **REUSED idiom** (column-name constants) |

## FLAGS — surfaced, not acted on (outside the writable set / grant, or observations)
- **F-1 (stale TEST prose, outside grant).** `_comms_fakes.FakeAgentRegistry._shared_identifier_predicate`'s docstring still says the predicate is "imported at CALL time … or `None` while it does not exist yet" and describes the `try`/`except ImportError` it no longer has; `_refuse_what_the_writer_refuses`'s comment still says "HEAD-RED accommodation: `is_legal_identifier` does not exist until the i-a build … so it is read at CALL time". Item 1 granted only the guard deletion + module-top import, so I left both. Exact edit I would make: docstring → "THE shared `lorerunes.is_legal_identifier` (module-top import). The `| None` return and the caller's `is not None` branch are dead since 63c-i-a — collapse at i-b (amendment 12)"; comment → drop the HEAD-RED sentence. (Or take item 10's collapse, which deletes both.)
- **F-2 (a THIRD raw-CREATE agent helper).** `test_comms_schema.py::_create_agent` (9 call sites) is another raw `CREATE agent … CONTENT` clone beside `_governed_contract.seed_agent_legacy`; D3 named only the `test_agent_owns_principal_schema.py` copy. Same fold applies; the lead's call.
- **F-3 (a committed probe the build falsifies).** `scripts/probe_governed_63c.py::_agent_dd3c` applies the CURRENT `generate_agent_ddl()` and its C-CONTROL asserts "the role non-empty ASSERT is REAL" — after this build it will print `PART C-agent C-CONTROL FAILED … the role non-empty ASSERT is not live` (its own comment also says "agent deliberately has NO scope column"). It is the pre-ruling measurement instrument whose finding this build implements; outside my writable set (`scripts/` = yaml only). Recommend: mark it historical (a header line "measured the pre-63c-i-a world; C-agent is expected to fail on ≥ 63c-i-a") or pin it to a frozen DDL.
- **F-4 (observation, spec-consistent, loud).** An agent row with `scope` SET but `owner_principal` NONE is unreachable through the writer (A3 refuses the half-pair; re-register never stamps) but reachable by a raw write. The agent migrate skips it (`WHERE scope IS NONE`), and the message migrate's §2.6 precondition (`_owner_count(agent, none=True)`) would then REFUSE forever, naming the NONE-owner count. Loud, not silent — MP-F already names this row. No action taken.
- **F-5 (observation).** `agents.py`'s module docstring API block was already stale before this build (`register` lacked `cadence`/`owner_principal_id`); I updated it to the full current signature while adding `session_keep_id`.

## GATES — on the final bytes (working tree over HEAD `5ce89cd`, which differs from my base `4d6d53e` only by `REPORT-lead-63c.md`; measured 2026-09-25)
- **Full suite ALONE, `-n 12`** (`run_guarded.sh full1 12 FULL`, launched 19:51:41 EDT, 59 GiB available, no other pytest on the process table, `spike-surreal.service` active; PID watchdog <15 GiB @5 s never fired, lowest 51 GiB; `loremaster.__file__` = the main checkout):
  ```
  11498 passed, 62 skipped, 3 xfailed, 9 warnings in 522.45s (0:08:42)
  exit=0 watchdog_fired=0 lowest=51GiB end=2026-09-25 20:00:26
  ```
  **0 failed, 0 errors.** 11498 = the contract's SAT count on the adversary reference build (REPORT-contract-63c-i-a-r4b-fix2 §SAT). The 9 warnings (contract SAT showed 7) are all outside i-a: never-awaited-coroutine `RuntimeWarning`s in `test_mcp_server.py` / `test_memory_enforcement_63b_ia.py` / `test_retry_seam.py`, uvicorn/websockets `DeprecationWarning`s, resource warnings in `test_migration_wire.py` — no i-a module named. The only edits after the launch were to this report (the `principals.py`/`server.py` md5s equal the mutation-proof restore receipts; §BACKUP).
- `uv run ruff check .` → `All checks passed!`
- `./scripts/typecheck.sh` → rc 0; every leg OK (`lorerunes`, `lorescribe`, `loresigil`, `loremaster`, `skills`, `docs/eval`, `scripts`, `shellcheck OK (7 tracked .sh)`).
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` → `typecheck GREEN` · `ruff GREEN` · `pytest NOT_RUN` (by design — never a bare `--currency`, #466; the suite ran separately above). Before the yaml deletion the same command reported `typecheck RED_ORPHANED — 11 residual(s)`, all 11 `SELF-DESTRUCT` (item 2).
- **Dirty-store (#107):** every field change is `DEFINE FIELD OVERWRITE` via `_define_field` (store-ref §1.1); the drops keep their rows with `""` so OVERWRITE's full replace removes the stored ASSERT (§1.2); new fields `option<>`, no DEFAULT (§1.4); indexes `IF NOT EXISTS` (§1.5). The contract's dirty-store / legacy-row legs RAN and PASSED (§RED), none skipped.
- ⚠ NOT DEPLOYED. No container rebuild/recreate, no `lore-deploy`.

## BACKUP — the working tree is not the only copy (NOT committed; the lead commits after the cold audit)
- Patch: `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/a3c3f778-deba-476f-81cc-e0ff2b54daec/scratchpad/builder-63c-i-a.patch` — md5 **`113d0143d175bcbf777170435eaa7d18`** = `git diff --binary` (9 tracked files) + `git diff --binary --no-index /dev/null lorerunes/lorerunes/identifiers.py` (the untracked new file; nothing was staged). `git apply --check --binary` against a `git archive HEAD` extract → applies cleanly.
- File copies (`cp -a`): `…/scratchpad/builder-63c-i-a-files/` — md5s: `agents.py 0139440c…` · `governed.py 4a3fa3dc…` · `principals.py bcef1d2f…` · `server.py d1dbdd7a…` · `store/surreal_schema.py 8da6e419…` · `_comms_fakes.py 82015012…` · `test_agent_owns_principal_schema.py f5961f2a…` · `lorerunes/identifiers.py 1e91a40d…` · `lorerunes/__init__.py 78c6ccb6…` · `scripts/pending_contracts.yaml 90688973…`.
- Other content backups taken before mutating: `surreal_schema.pre-fix.py` (before `ruff --fix`), `pending_contracts.pre.yaml`, `test_agent_owns_principal_schema.pre-fold.py`.

## A. Instruments (pasted VERBATIM — brief-base §1; the claims in §RED/§GATES rest on them)
### A.1 `run_guarded.sh` (launch gate + PID watchdog + junit)
```bash
#!/usr/bin/env bash
# run_guarded.sh LABEL WORKERS FILESET|FULL
# One guarded pytest session in the MAIN checkout (builder-63c-i-a):
#  - launch gate: MemAvailable >= 23 GiB for -n 12 (>= 20 GiB for -n 8 or less), no other pytest
#    on the process table (comm/args-anchored awk, never a shell-text pattern — #228),
#    spike-surreal.service active;
#  - PID watchdog: kills THIS pytest (by PID) when MemAvailable < 15 GiB, polled every 5 s;
#  - junit xml + log in the scratchpad; prints loremaster.__file__ as provenance.
set -u
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/a3c3f778-deba-476f-81cc-e0ff2b54daec/scratchpad
REPO=/home/ejprice/PycharmProjects/lore
LABEL=$1; WORKERS=$2; SET=$3
cd "$REPO" || exit 2
avail_gib() { awk '/^MemAvailable:/{printf "%d", $2/1048576}' /proc/meminfo; }
need=20; [ "$WORKERS" -ge 12 ] && need=23
others() { ps -eo pid=,comm=,args= | awk -v me=$$ '$1!=me && ($2 ~ /^(python|python3|pytest|uv)$/ || $2 ~ /^python3\.[0-9]+$/) && $0 ~ /py[t]est/ {print}'; }
waited=0
while :; do
  o=$(others); a=$(avail_gib)
  if [ -z "$o" ] && [ "$a" -ge "$need" ]; then break; fi
  if [ $waited -ge 1800 ]; then echo "BLOCKED: waited 30 min (avail=${a}GiB; others: $o)"; exit 3; fi
  echo "waiting: avail=${a}GiB need=${need}; others=[$o]"; sleep 30; waited=$((waited+30))
done
st=$(systemctl --user is-active spike-surreal.service); echo "spike-surreal: $st"
[ "$st" = active ] || { echo "spike-surreal not active"; exit 4; }
echo "provenance: $(uv run python -c 'import loremaster; print(loremaster.__file__)')"
if [ "$SET" = FULL ]; then TARGETS=(); else mapfile -t TARGETS < "$SET"; fi
echo "launch $(date '+%F %T') avail=$(avail_gib)GiB workers=$WORKERS label=$LABEL"
uv run pytest -q -p no:cacheprovider -n "$WORKERS" --junitxml="$S/$LABEL.xml" "${TARGETS[@]}" > "$S/$LABEL.log" 2>&1 &
PID=$!
low=$(avail_gib); fired=0
while kill -0 "$PID" 2>/dev/null; do
  a=$(avail_gib); [ "$a" -lt "$low" ] && low=$a
  if [ "$a" -lt 15 ]; then echo "WATCHDOG FIRED avail=${a}GiB — killing $PID"; kill "$PID"; pkill -P "$PID"; fired=1; fi
  sleep 5
done
wait "$PID"; rc=$?
echo "exit=$rc watchdog_fired=$fired lowest=${low}GiB end=$(date '+%F %T')"
tail -3 "$S/$LABEL.log"
```
### A.2 `junit_ids.py` (junit → outcome/id/message TSV)
```python
"""junit_ids.py XML — print '<outcome>\t<file::class::name>\t<first line of message>' per testcase."""
import sys
import xml.etree.ElementTree as ET

for case in ET.parse(sys.argv[1]).iter("testcase"):
    classname = case.get("classname", "")
    parts = classname.split(".")
    # loremaster.tests.test_x.Class -> loremaster/tests/test_x.py::Class
    mod_idx = next(i for i, p in enumerate(parts) if p.startswith("test_"))
    node = "/".join(parts[: mod_idx + 1]) + ".py" + "".join(f"::{p}" for p in parts[mod_idx + 1 :]) + "::" + case.get("name", "")
    outcome, msg = "passed", ""
    for tag in ("failure", "error", "skipped"):
        el = case.find(tag)
        if el is not None:
            outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
            msg = (el.get("message") or "").splitlines()[0][:160] if el.get("message") else ""
            break
    print(f"{outcome}\t{node}\t{msg}")
```
### A.3 `red_green_diff.py` (RED@HEAD → GREEN, both directions)
```python
"""red_green_diff.py HEAD.tsv BUILT.tsv — RED@HEAD -> GREEN accounting by test id, both directions."""
import sys

def load(path):
    rows = {}
    for line in open(path):
        outcome, node, _msg = (line.rstrip("\n").split("\t") + ["", ""])[:3]
        rows[node] = outcome
    return rows

head, built = load(sys.argv[1]), load(sys.argv[2])
red = {"failed", "error"}
head_reds = {n for n, o in head.items() if o in red}
head_greens = {n for n, o in head.items() if o == "passed"}
print(f"ids: head={len(head)} built={len(built)} | gone={len(set(head)-set(built))} new={len(set(built)-set(head))}")
print(f"RED@HEAD: {len(head_reds)} -> now passed: {sum(built.get(n)=='passed' for n in head_reds)} "
      f"still red: {sum(built.get(n) in red for n in head_reds)} other: {sum(built.get(n) not in red|{'passed'} for n in head_reds)}")
turned_red = sorted(n for n in head_greens if built.get(n) != "passed")
print(f"HEAD greens: {len(head_greens)} -> turned non-passed: {len(turned_red)}")
for n in turned_red:
    print("  TURNED", built.get(n), n)
for n in sorted(head_reds):
    if built.get(n) != "passed":
        print("  STILL", built.get(n), n)
skips = sorted(n for n, o in built.items() if o == "skipped")
print(f"skipped built={len(skips)} head={sum(o=='skipped' for o in head.values())} same_set={set(skips)=={n for n,o in head.items() if o=='skipped'}}")
```
### A.4 one-off commands
```bash
# declared universe + HEAD run (BEFORE any production edit):
uv run pytest --collect-only -q -p no:cacheprovider $(cat files5.txt) | awk '/::/' > collected_head.txt   # 3036
run_guarded.sh redhead 8 files5.txt ; python3 junit_ids.py redhead.xml > redhead.tsv
# built run + diff:
run_guarded.sh built1 8 files5.txt ; python3 junit_ids.py built1.xml > built1.tsv ; python3 red_green_diff.py redhead.tsv built1.tsv
# mutation proofs: see §MUTATION (anchor/replacement files mp1_anchor.txt / mp1_repl.txt; declared_mp1.txt, declared_mp2.txt from --collect-only)
# full suite: run_guarded.sh full1 12 FULL
```
