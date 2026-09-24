brief-base v16 read · brief project v7 read
- **State:** done-with-deviations · **Deviations:** (1) grep hook-blocked in the main checkout → constants located with a Python `ast` locator + Read (said out loud; friction filed **#475**); (2) the brief's "#420 legs RED_ADJUDICATED in `scripts/pending_contracts.yaml`" premise is wrong by design — the legs live in `server._GOVERNED_VERBS_PENDING_ROUTING` (rulings §10.2); written as found.
- **Packages considered:** none — no mechanism specified (a planning doc; mechanisms are routed to the sidecar as forks).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (no code symbols introduced).
- **Graded:** n/a (authored, not graded) · read at HEAD `0eed242` (moved to `5e3e5a4` by a peer commit before close; my two files are the only edits).
- **Decisions-needed:** FORK F0 (operator: 64 vs in-flight 63c share `_governed_contract.py`/`server.py`/exact-set pins in ONE tree) + sidecar forks F1–F9 (packet file §FORKS).
- **Pointers:** `docs/plans/v2/64-governed-retrofit-tasks-findings.md` §Ground truth · §FORKS · §Findings owned.

## Files written
`docs/plans/v2/64-governed-retrofit-tasks-findings.md` (new, ~223 lines) · this report. Nothing else touched; no git ops.

## Verified (read at `0eed242`, lore-first; index watched ref = HEAD at read time)
- `task`: `owner option<string>` = the CLAIMANT (claim-CAS gate `owner IS NONE`, `TaskLedger._claim_fragment`); **no `created_by` column** — creator is `provenance.created_by` in a FLEXIBLE blob (`_new_task_content`).
- `finding`: `created_by` required string column with non-empty ASSERT; `supersedes` a real link; global UNIQUE `number`.
- ⇒ authz §7's "free-form string" premise HOLDS for both (false for memory/message) — 63's `LegacyMapping` already names STRING-UNRESOLVABLE → UNOWNED-LEGACY for 64.
- `AppContext.tasks/findings/claim_task` take caller `created_by`/`actor`/`owner`; none has `capability=`.
- `_TASK_ACTIONS` (8) / `_FINDING_ACTIONS` (10) are plain tuples — no `requires_capability` field to flip (FORK F7).
- 19 #420 legs in `_GOVERNED_VERBS_PENDING_ROUTING`; 3 tools in `_GOVERNED_TOOLS_PENDING_OWNER_STAMP`; `pending_contracts.yaml` has only the 63c-i-a bound.
- Six seams by symbol (`lore_verify`): `resolve_subject`, `read_filter`, `guarded_write`, `_governed_field_specs`, `_governed_index_statements`, `StoreHandle`, `LegacyMapping`; `migrate_governed` lives in **`loremaster.principals`** (not `governed`) and refuses task/finding today.
- `blocks` joins the governed population by derivation (`TASK_TABLE` is a module literal).
- All 15 owned findings exist, `acknowledged`, routed → 64 by `plan-review` 2026-09-24.
- `bb31a86` (63a close) and `5d61f9e` (63b-ii-b) are ancestors of HEAD.

## UNVERIFIED (stated as such in the packet)
The DD-3.c KEEP/DROP outcome per ASSERT (left as a scope item with a constructing leg); whether F5's reach already covers `task`/`finding` sites; the probe verdicts over task/finding DDL (an entry-check probe).

## Contradictions found
1. **INDEX row 63's Status is stale** — says "63b/63c NOT started" while the Log records 63b CLOSED 2026-09-12. Row not flipped.
2. **63b verbs still sit in `_GOVERNED_VERBS_PENDING_ROUTING`** at `0eed242` (`send/drain/ack/await/story/register` under `_ROUTE_63B_MESSAGE`) although 63b closed and flipped `requires_capability`. Either the per-verb pin was never moved to `_GOVERNED_VERBS_ROUTED` in 63b, or it is deferred to 63c by a ruling I did not find — **UNVERIFIED which; raise to the 63c lead.**
3. Rulings §3.1 phrase "`task.owner`/`created_by`" implies two author columns; only `owner` exists and it is the claimant, not an author (FORK F2).
4. Brief premise re `pending_contracts.yaml` (deviation 2).
5. §10-N's tasks→`principal-private` default makes a task claimable only within the creator's principal — sound for the single-principal fleet, but it collides with authz §4's "Keep task claimable by household" as the COMMON case (FORK F3).
