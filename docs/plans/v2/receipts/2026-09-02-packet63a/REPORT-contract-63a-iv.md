# REPORT-contract-63a-iv — packet 63 wave 63a-iv CONTRACT (Opus 4.8, tests-only)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- state: **done-with-deviations** (one escalated fork: §10.8 audit-DDL gap is ALREADY CLOSED at HEAD — item (5) is a GREEN regression guard, not RED-until-built; recommend against redundant wiring).
- deviations:
  - **FORK-AUDIT-DDL (escalated, finding #440):** the §10.8 production audit-DDL gap the ruling+cold-audit assert is OPEN is DEMONSTRABLY CLOSED at HEAD (probed). Item (5) written as a GREEN-at-HEAD composition-root regression guard; recommend NOT adding redundant explicit AuditStore wiring. See §AUDIT-DDL-FORK.
  - **STUB added:** `governed.write_guard(label)` + `governed.active_write_guard()` (contextvar plumbing, no business logic) — the F5 runtime guard-context symbol the pins need; the builder WIRES it into `guarded_write` + the allowlisted frames. See §F5.
  - `derive_memory_id` gains an owner-folding signature — pinned as the contract; a STUB signature widening may be needed for collection (see §OWNER-FOLD).
- Packages considered: none — no mechanism specified (contract/tests only; the guard-context uses stdlib `contextvars`, not a package).
- Reuse ledger: see §REUSE (F5 substrate in `_governed_contract.py`; write_guard = stdlib contextvars).
- Graded: f77ac24 (production base the pins were measured against) · HEAD-at-report: 0ea337b (this RED-contract commit) · DIFFERENT (1 ahead — 0ea337b adds ONLY this contract's tests; no production code, so f77ac24 remains the correct grading base)
- RED/GREEN @ HEAD f77ac24: **12 RED-for-the-right-reason / 12 GREEN / 24 total** (owner-fold 4R+1G · stale-prose 4R · F-B 3G · F5 6G(L1)+4R(L2) · audit-DDL 2G). Satisfiability: **24/24 GREEN** against the provenance-asserted reference build (`/tmp/contract63aiv-ref`), incl. after ruff cleanups.
- decisions-needed:
  - **FORK-AUDIT-DDL** — item (5): ship as GREEN regression guard + DROP the redundant AuditStore wiring? (my recommendation) OR add belt-and-braces explicit wiring anyway? lead-63/operator ruling. (RED-until-built premise refuted.)
- receipt POINTERS: owner-fold pins → §OWNER-FOLD; F5 enforcement → §F5; F-B → §F-B; stale-prose → §STALE-PROSE; audit-DDL fork+probes → §AUDIT-DDL-FORK; RED/GREEN delta → §GATES; satisfiability receipt → §SAT; mutation-proof plan → §MUTATION; DRY → §REUSE.

---

## §AUDIT-DDL-FORK — the §10.8 gap is already closed at HEAD (escalated; finding #440)

**Claim (design §10.8 + cold-audit-63a-iii §FORK-1 / RES-2-DDL):** production has no `audit`
table DDL, so a memory `guarded_write` admin-bypass audit CREATE auto-creates it SCHEMALESS
(#107 shape), permanently un-repairable by a later `IF NOT EXISTS`. Grounds cited: `grep -c
"AuditStore|generate_audit_ddl" server.py = 0`.

**Refuted at HEAD `f77ac24` (empirically, test store ws://127.0.0.1:18000):**
- `SurrealStore.ensure_ready()` (`store/surreal.py:551`) applies `generate_ddl(...)`.
- `generate_ddl` (`store/surreal_schema.py:1889`) unconditionally `statements += _audit_statements()`
  → `DEFINE TABLE audit ... SCHEMAFULL` + `action` field `ASSERT $value INSIDE ['WRITE','DELETE','SET_SCOPE','SET_OWNER']`.
- `build_app_context` calls `write_store.ensure_ready()` (`server.py:9198`) FIRST — before the
  memory backend is constructed (`server.py:9311`) — and `build_store` uses
  `config.effective_surreal_database` (`store/surreal.py:1880`), the SAME database
  `surreal_database` the memory backend + its `audit_store` write to.
- **So the audit table is SCHEMAFULL + action-ASSERT-enforcing on that database BEFORE any
  write can land.** The schemaless-auto-create hazard cannot trigger.

The cold-audit grep was keyed on `AuditStore|generate_audit_ddl` and MISSED that the audit DDL
reaches production through `generate_ddl` (the global write-store schema) — the "keyed-on-a-name"
instrument defeat (lore CLAUDE.md instrument lesson). A `grep generate_ddl`/`_audit_statements`
or a live `INFO FOR TABLE audit` probe catches it.

### Probe transcripts (verbatim per brief-base §1 — instrument is a deliverable)

`/tmp/probe_audit_ddl.py` → after `write_store.ensure_ready()` ONLY, `INFO FOR TABLE audit`
shows `action: "... ASSERT $value INSIDE ['WRITE','DELETE','SET_SCOPE','SET_OWNER']"` plus every
field defined.

`/tmp/probe_audit_ddl2.py` output:
```
TABLE DEF: DEFINE TABLE audit TYPE NORMAL SCHEMAFULL PERMISSIONS NONE
SCHEMAFULL? True
OUT-OF-DOMAIN action -> REJECTED by ASSERT: InternalError Found 'EXFILTRATE' for field `action` ...
```
(Probe scripts pasted in §PROBES below.)

### Recommendation (contract author → lead-63)
1. Item (5) ships as a **GREEN-at-HEAD composition-root regression guard**: after the REAL
   `build_app_context` on a fresh DB (no test-side audit ensure), assert `INFO FOR TABLE audit`
   SCHEMAFULL + the call-time `action` ASSERT present; discriminating leg: a valid audit row
   lands (+1) and an out-of-domain `action` fragment is REJECTED. It reds if anyone removes
   `_audit_statements()` from `generate_ddl`, or reorders so a write precedes the ready.
2. **Do NOT add redundant explicit `AuditStore.ensure_ready(generate_audit_ddl())` at
   `build_app_context`** — it is a second, idempotent readying of a table the write-store schema
   already owns (ONE-IMPLEMENTATION: `generate_audit_ddl` and the `generate_ddl` fold share
   `_audit_statements()`). Harmless but a duplicate.
3. This is a **spec/reality contradiction = a defect** (not a contract decision) → escalated.
   If lead/operator still wants belt-and-braces wiring, it is harmless; I recommend against.

---

## §RES-ATOM — §10.9-D (NOT pinned here; documented bound owned by 63b)

Per design §10.9-D the RES-ATOM close-first crash-before-ledger window stays a DOCUMENTED LOW
bound — contract-63a-iv did NOT pin a fix (the ruling forbids it here). The 63b ledger row the
rider requires is **filed as finding #441** (owner: 63b; the ruled fix shape = authorize-first,
compose the guarded close WITH the new-row UPSERT as one execute_transaction).

## §OWNER-FOLD — item (1), 10.9-B #439 owner fold

File `loremaster/tests/test_memory_ownerfold_63a_iv.py` (PROMOTES cold-audit §REPRO
`TestCandidateA_*`, FLIPPED). Item → pins:
- **Construction 1 (cross-principal seizure + re-scope)** → `test_a_non_owner_reremember_mints_a_distinct_id_and_does_not_seize_or_rescope` — bob re-remembers alice's exact text (+`scope=principal-private`) → asserts `bob_id != alice_id` AND alice's row owner/scope/valid_until UNCHANGED; CONTROL: bob's guarded invalidate DENIES. **RED at HEAD** (ids collide: `bob_id == alice_id == f142dc42-…`).
- **Construction 2 (intra-principal sibling seizure, LIVE today)** → `test_a_sibling_agent_reremember_mints_a_distinct_id_and_does_not_seize` — worker_2 (same principal, 2nd agent) re-remembers → distinct id, worker_1's owner_agent unchanged; CONTROL: sibling's invalidate DENIES. **RED at HEAD**.
- **Construction 3 (revive a retired foreign note)** → `test_a_non_owner_reremember_does_not_revive_a_retired_foreign_note` — bob re-remembers alice's retired text → distinct id, alice's row STILL retired. **RED at HEAD**.
- **POSITIVE CONTROL / anti-over-fix** → `TestSameAgentDedupIsPreserved::test_the_same_agent_reremembering_its_own_text_dedups_in_place` — same (principal, agent) re-save → SAME id, count()==1. **GREEN at HEAD** (the taught contract preserved; discriminates against an over-fix that folds a nonce and breaks dedup).
- **`derive_memory_id` SHAPE pin (∀ owner-pairs, quantifier law)** → `TestDeriveMemoryIdFoldsTheOwnerPair::test_the_owner_pair_and_the_content_all_fold_into_the_id` — order-agnostic: with ≥2 distinct principals AND ≥2 distinct agents, asserts same(owner,text,refs)⇒same id, differing principal⇒distinct, differing agent⇒distinct, and text/refs still vary the id. **RED at HEAD** (`TypeError: derive_memory_id() got an unexpected keyword argument 'owner_principal'`).

DERIVATION-not-WHERE-guard: the pin comment cites store-ref §2 (UPSERT+WHERE on an existing id
whose WHERE fails is a silent no-op) — unrepresentability comes from folding the owner into the id.
PARAM NAMES `owner_principal`/`owner_agent` are the contract (descriptive-naming law); the uuid5
STRING field order stays the builder's choice.

## §F5 — item (2), 10.9-A enforcement completeness (REUSABLE substrate — DRY)

Substrate in `loremaster/tests/_governed_contract.py` (the ONE implementation; 63b/64 parametrise,
never clone): `MutationSite` · `GovernedWriteAllowlistEntry` (site, justification, pin, frames) ·
`governed_table_raw_mutation_sites` (AST, statement-shape derived — the `_SCANNED_MEMBERS` idiom,
docstrings excluded, SurrealQL-syntax required) · `governed_table_guarded_write_frames` ·
`function_calls_write_guard` · `observe_governed_table_writes` (seam instrument) · `call_name`
(shared func-name helper). Memory parametrisation + pins in
`loremaster/tests/test_memory_enforcement_63a_iv.py` (MEMORY_WRITE_ALLOWLIST = 3 triples).

- **L1 STRUCTURAL (deny-by-default)** — `TestEveryRawMemoryMutationIsAllowlisted`: derived raw set == {`_upsert_fragment`/UPSERT, `_reinforce`/UPDATE, `_recreate_memory_table`/REMOVE}; every derived site ∈ allowlist (no orphan/ghost); **synthetic-source discriminator** proves a NEW raw site grows-and-reds; pin-existence (each entry's `pin` resolves in the test tree); guarded frames {invalidate, remember} derived. + `TestRecreateMemoryTableIsBootAdminOnly` (RES-1 evidence). **6 GREEN at HEAD** (completeness instrument, self-proven by the synthetic discriminator).
- **L2a STRUCTURAL guard-context coverage** — `TestEveryAllowlistedFrameSetsAWriteGuardContext`: every allowlisted FRAME (derived from the allowlist — grows-and-covers) + `guarded_write` calls `governed.write_guard`. **2 RED at HEAD** (unwired).
- **L2b RUNTIME (deny-by-default, live)** — `TestEveryObservedMemoryMutationCarriesAGuardContext`: `active_write_guard` exists; a battery (remember-create → execute_transaction, recall→reinforce → run_query, invalidate→guarded → execute_read_transaction) is seam-instrumented; every OBSERVED memory mutation carries a non-None context, across all 3 seam paths. **2 RED at HEAD** — the instrument is LIVE at HEAD (observed all 3 seam mutations `[execute_transaction/UPSERT, run_query/UPDATE, execute_read_transaction/UPDATE]`), the RED is the None context. Reference build wires `write_guard` in 5 sites → GREEN.

## §F-B — item (3), 10.9-C _reinforce two pins

File `loremaster/tests/test_memory_reinforce_63a_iv.py`. Both GREEN at HEAD (invariant/allowlist-
justification guards — §10.9-C ACCEPTS `_reinforce` as-is), each a discriminator:
- **(i) bump set ≡ served set** → `TestReinforceBumpsOnlyTheServedSet` — a foreign principal-private note the caller cannot READ is never bumped (`after == before`); POSITIVE CONTROL: the owner's own readable note IS bumped (`after > before`, C1 law — reinforcement proven live). REDDENS a refactor to reinforce the PRE-filter candidate set.
- **(ii) statement touches ONLY `importance`** → `TestReinforceStatementTouchesOnlyImportance` — captures the RESOLVED runtime statement (wraps `_query`; NON-VACUOUS — a source regex misses the `{_COL_IMPORTANCE}` interpolation, verified `assigned == {importance}`), asserts the SET assigns only `importance`, no isolation/validity column. Mutation-proven (see §MUTATION).

## §STALE-PROSE — item (4), P8d prose currency

File `loremaster/tests/test_memory_prose_currency_63a_iv.py`. All 4 **RED at HEAD**:
- SERVED (trust Leg 1) → `test_lore_remember_description_scopes_dedup_to_the_owning_agent` — the `lore_remember` tool description must qualify dedup per-agent (design §10.9-B "for the same agent"). Tolerant matcher.
- `test_derive_memory_id_docstring_mentions_the_owner` — the folding function's docstring mentions the owner (non-trapping: any owner mention passes).
- Bare-grep P8d sweeps (each residual hit reported file:line): `test_no_module_prints_the_owner_less_uuid5_name_literal` (`memory:{text}:{refs_stamp}` — NON-TRAPPING: not a substring of the owner-inclusive rewrite `memory:{owner_principal}:…`) + `test_no_module_claims_the_id_scheme_is_unchanged` (`scheme is UNCHANGED` — false under the fold). Hits at HEAD: `backend.py:14`, `backend.py:97`, `backend.py` derive_memory_id docstring.

## §AUDIT-DDL — item (5), §10.8 composition-root pin (GREEN regression guard — see §AUDIT-DDL-FORK)

File `loremaster/tests/test_audit_ddl_composition_root_63a_iv.py`. Boots the REAL `build_app_context`
(no test-side audit ensure — the #131 fixture-fiction rider (i) forbids), inspects the audit table on
the SAME DB. Both **GREEN at HEAD** (per finding #440 — the gap is already closed):
- rider (i) → `test_the_audit_table_is_schemafull_with_the_action_assert` — `INFO FOR DB` SCHEMAFULL + `INFO FOR TABLE audit` action ASSERT present.
- rider (ii) discriminating pair → `test_a_valid_action_lands_and_an_out_of_domain_action_is_rejected` — a valid audit row lands (+1), an out-of-domain `action` is REJECTED (a schemaless auto-create would accept both).
These are REGRESSION guards: red if `_audit_statements()` leaves `generate_ddl`, or the ready order
changes. **Recommendation to lead: DROP the redundant explicit AuditStore wiring** (§AUDIT-DDL-FORK).

## §GATES — RED/GREEN delta + gate output

- 5 modules @ HEAD f77ac24 (test store ws://127.0.0.1:18000): **`12 failed, 12 passed in 11.04s`** — 12 RED-for-the-right-reason (owner-fold 4 · stale-prose 4 · F5-L2 4), 12 GREEN (owner-fold control 1 · F-B 3 · F5-L1 6 · audit-DDL 2). Every RED traced to the unbuilt deliverable (owner fold / write_guard wiring / stale prose); no RED for a wrong reason.
- `uv run ruff check .` → **All checks passed!**
- `bash scripts/typecheck.sh` → **EXIT=0** (loremaster leg: `no issues found in 256 source files`; all legs OK).
- Regression (my additions are backward-compatible — additive test files + additive `_governed_contract` symbols/fields): `test_governed_substrate_63a.py` (F1–F4 consumer) + `test_memory_retrofit_63a.py` (fixture source) + `test_pdp_oracle_61b.py` → **`64 passed in 26.89s`**.

## §SAT — satisfiability receipt

Reference build in a provenance-asserted scratch copy (`./scripts/scratch_copy.sh /tmp/contract63aiv-ref`):
`PROVENANCE loremaster.__file__ = /tmp/contract63aiv-ref/loremaster/loremaster/__init__.py` (imports
resolve INSIDE the copy — #140-safe). Reference implements: owner-fold in `derive_memory_id`
(+`remember` call-site passing `subject.principal_id`/`agent_id`); `governed.write_guard`/
`active_write_guard` + wiring into `guarded_write` and the 4 allowlisted frames; stale-prose
corrections (derive_memory_id docstring, backend.py:14/97, the `lore_remember` description).
- **All 5 modules against the reference: `24 passed in 12.16s` (0 failed).**
- After the ruff cleanup the reference lint demanded (reflow a long docstring line): re-ran stale-prose + owner-fold → **`9 passed`** (contract still 0-failed after cleanup).
- NOTE (for the builder): the owner-fold changes `derive_memory_id`'s signature; the old-signature callers (`test_memory_backend` parity suite) must be updated by the builder — out of THIS contract's writable set, flagged.

## §MUTATION — mutation-proof plan per load-bearing pin

The RED-at-HEAD pins are self-mutation-proven by the HEAD↔reference delta (HEAD IS the "mutation":
owner fold removed / write_guard unwired / stale prose present → RED; reference → GREEN). For the
GREEN-at-HEAD invariant pins:
- **F-B statement-shape (ii)** — DEMONSTRATED: added `{_COL_SCOPE} = 'x'` to the reinforce SET in the reference → the statement-shape pin REDS (`assigned == {importance, scope} != {importance}`) + L2b collateral-reds. Restored.
- **F5 L1 containment** — self-proven by `test_a_synthetic_new_raw_mutation_site_grows_the_derived_set_and_reds` (a synthetic new raw site reds the containment).
- **F-B isolation (i)** — plan: move `_reinforce(memories)` to run on the pre-`read_filter` candidate list → a foreign unreadable row is bumped → the pin reds (not run — needs a source reshuffle; the POSITIVE CONTROL guards vacuity).
- **audit-DDL** — plan: delete `_audit_statements()` from `generate_ddl` → the composition-root SCHEMAFULL pin reds (probed equivalent: a schemaless table accepts the out-of-domain action).
- **owner-fold shape** — plan: revert `derive_memory_id` to `(text, refs_stamp)` → the shape pin TypeErrors + the 3 seizure pins red (this IS the HEAD state).

## §REUSE — DRY ledger (brief-base §6)

| new symbol | lore query / search | returned | disposition |
|---|---|---|---|
| `MutationSite`, `GovernedWriteAllowlistEntry`, `governed_table_raw_mutation_sites`, `governed_table_guarded_write_frames`, `function_calls_write_guard`, `observe_governed_table_writes` | new F5 substrate; modelled on `test_governed_routing_63a.py`'s `@observes_routing` AST-coverage idiom | that idiom is per-VERB routing, not per-MUTATION-SITE enforcement | HAND-ROLLED in the SHARED `_governed_contract.py` (design §3.2 mandates F5 land reusable there; 63b/64 parametrise) |
| `call_name(ast.Call)` | the `func.attr if isinstance … else func.id …` idiom, repeated 3× (2 in _governed_contract, 1 in enforcement) | no shared helper existed | HAND-ROLLED once in `_governed_contract`, reused at all 3 sites (kills the 3 E501s too) |
| `governed.write_guard`/`active_write_guard` (reference only) | stdlib `contextvars` | `contextvars.ContextVar` + `@contextmanager` is the exact primitive | REUSED `contextvars` (stdlib) — no package needed; the pins reach it getattr-tolerant so NO production stub in the main tree |
| test-local `_bare_s`, `_read_governed`, `_importance` | cold-audit §REPRO helpers | §REPRO defined them in scratch (discarded with its tree) | HAND-ROLLED (per-module test helpers; §REPRO's copies were scratch — a shared home (`_governed_contract`) is a cheap follow-up, flagged) |

Packages considered: none — no production mechanism specified (contract/tests only). The reference
guard-context uses stdlib `contextvars` (not a package).

## §PROBES — instruments verbatim (brief-base §1)

**Audit-DDL probe** (`/tmp/probe_audit_ddl2.py`, run at HEAD, output in §AUDIT-DDL-FORK):
```python
import asyncio, sys
sys.path.insert(0, "loremaster/tests")
from _surreal_harness import make_env, connect_admin, run, drop_database, unique_database
async def main():
    env = make_env(database=unique_database(), dim=8)
    from loremaster.store.surreal import SurrealStore
    store = SurrealStore(url=env.url, namespace=env.namespace, database=env.database,
                         user=env.user, password=env.password, dim=env.dim)
    try:
        await store.ensure_ready()  # applies generate_ddl (folds in _audit_statements)
        admin = await connect_admin(env)
        dbinfo = await run(admin, "INFO FOR DB", {})
        print("TABLE DEF:", dbinfo.get("tables", {}).get("audit"))  # -> DEFINE TABLE audit TYPE NORMAL SCHEMAFULL
        good = {"actor_principal": None, "actor_agent": None, "actor_email":"a@x",
                "actor_agent_name":"ag", "action":"WRITE", "target_table":"memory", "target_row":"memory:1"}
        bad = dict(good); bad["action"] = "EXFILTRATE"
        try: await run(admin, "CREATE audit CONTENT $c", {"c": bad})
        except Exception as e: print("OUT-OF-DOMAIN -> REJECTED by ASSERT:", type(e).__name__)
        await admin.close()
    finally:
        await store.close(); await drop_database(env)
asyncio.run(main())
```
(The AST-scanner prototype `/tmp/probe_ast_scan2.py` is superseded by the committed
`_governed_contract.governed_table_raw_mutation_sites` — the instrument IS the deliverable, tracked.)
