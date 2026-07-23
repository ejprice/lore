# REPORT — packet-03-builder-store

brief-base v6 read

## SUMMARY BLOCK
- state: **done** — the packet-03 STORE pins are GREEN; only `surreal_schema.py` changed.
- Scoped gate (`test_comms_schema.py` + `test_surreal_schema.py`, `-n auto`): **304 passed, 0 failed** (2026-07-23, working tree at parent branch `feat/surreal-unification`).
- Blast radius (graph/brief/agent/comms-render/comms-fleet): **432 passed, 0 failed**.
- Invariant: `test_message_ledger.py` **STAYS RED, 14 failed / 166 errors — IDENTICAL to HEAD**, all `ModuleNotFoundError: No module named 'loremaster.messages'` (packet 03a).
- mypy: `surreal_schema.py` is CLEAN; my change took the tree 55→54 errors (resolved the missing-`generate_message_ddl` one). All 54 remaining are in the immutable committed RED 03a/03b contract test files — NOT my writable set.
- ruff: clean.
- Mutation matrix: 3 mutations each proven RED + a 14-pin correct-build control green; byte-exact restore verified.
- #349/#308 re-probed on 3.2.1 — both CONFIRM the contract's assumptions (verbatim below).
- deviations: (1) `asked_at` is NOT a stored `message` column — it is DERIVED from the question's `created_at` (contract says so); the packet-doc prose listing it as a node field is imprecise. (2) `MESSAGE_BODY_MAX_CHARS=2000` exposed in `surreal_schema` as the single source 03a must import (DRY).
- decisions-needed: **the global `scripts/typecheck.sh` gate cannot be zero until 03a/03b build their modules** — is the packet-03 exit's typecheck gate scoped to "no NEW errors / clean writable file", or is a red 03a/03b contract acceptable at this checkpoint? (see §Gates.)
- receipt pointers: change-list §Changes · gate tails §Gates · mutation matrix §Mutation proofs · probes §Entry-check probes.
- provenance (real-tree mutation runs): `loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`.
- Do NOT commit — lead commits. Report graded by an independent cold audit.

## Store-reference citations relied on
`docs/reference/surrealdb-31-capabilities.md` (all CITED, never re-transcribed):
- §1.1 (DDL decision-rule table) — RELATION TABLE row (`OVERWRITE`, the only clause that lands a changed `IN`/`OUT`/`ENFORCED`; `IF NOT EXISTS` = silent no-op, #107's shape); SEQUENCE row (`IF NOT EXISTS`, a bare `DEFINE SEQUENCE` raises on re-apply → boot crash; BATCH/START residual = #146); NODE TABLE / INDEX stay `IF NOT EXISTS`.
- §1.5 — `DEFINE TABLE OVERWRITE` is SAFE on a populated table (preserves fields/indexes/rows, does NOT rebuild), with its positive control; this is what makes the relation-table flip affordable.
- §4 ("Shape to ship") — `DEFINE TABLE OVERWRITE <edge> TYPE RELATION IN <a> OUT <b> ENFORCED SCHEMAFULL`; `ENFORCED` validates BOTH endpoints and is the only thing that closes the `INSERT RELATION` door; `UNIQUE(in,out)` on a relation edge is legal on our floor (#7061 settled ABSENT) and makes a duplicate a LOUD err → dedupe before the RELATE loop.
- §5 — `sequence::nextval("<name>")`; gaps are REAL, so `seq` is an ORDERING key, never a count/handle.
- §2 — `seen_at`/`acked_at` as `option<datetime>` so `IS NONE` is a real write-once CAS guard; `session` is a protected variable name (CONTENT writes, not `SET session`).
- §0 — the 3.2.1 migration receipts (engine IS 3.2.1; un-re-probed 3.1.5 facts keep their labels).

## Entry-check probes (spike-surreal `ws://127.0.0.1:18000`, 3.2.1, 2026-07-23)
Throwaway DB under `lore_test`; production `:18500` never touched. Ran BEFORE writing code, applying the EXACT statements I planned to emit. Verbatim observed behaviour:

**#349 — duplicate edge record ID fix / `UNIQUE(in,out)` dedupe on the `to` edge.**
Created a `to`-shaped `TYPE RELATION` edge with `UNIQUE(in,out)`, RELATEd a pair, RELATEd the SAME pair again:
```
[#349] second RELATE of same pair RAISED: InternalError: Database index `to_in_out`
       already contains [message:baf35d566b554d3f9ec5d4d4139882ac,
       agent:f8aa45fdd4864369b48a8ec0ee95afa9], with record `to:ng08n8swtd3gjejn06g1`
[#349] edge count after dup attempt = [{'count': 1}]
```
→ On 3.2.1 a duplicate pair is still a **LOUD error**, edge count stays 1. The #349 fix did NOT turn this into a silent dedupe. This CONFIRMS `test_a_duplicate_recipient_edge_is_a_LOUD_error` and the "dedupe before the RELATE loop" requirement (03a). No contract pin contradicted.

**#308 — cold-start `Session not found` router-race fix.**
Assessed, not probed (per brief: do not manufacture a probe). NO packet-03 pin leans on it: every `[real]`/`admin_db` pin runs against a WARM connection — `connect_admin` (`_surreal_harness.py`) runs the synchronous `bootstrap_session` before any test body, and each test uses an already-established connection on its own unique DB. There is no cold-start router race in this packet's surface, so #308's fix is irrelevant to the pins. Reasoned, no probe.

**Supporting probes (all CONFIRM the contract on 3.2.1):**
```
[DDL] tables=['agent','message','to']  sequences=['message_seq']
[DDL] to-def='DEFINE TABLE to TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL PERMISSIONS NONE'
[ENFORCED] ghost OUT RAISED: NotFoundError: The record 'agent:`a-ghost-that-never-was`' does not exist
[SEQ] first=0 second=1 advanced=True                         (re-apply did NOT reset the counter)
[DIRTY-FLIP] before='DEFINE TABLE to2 TYPE RELATION SCHEMAFULL PERMISSIONS NONE'
[DIRTY-FLIP] after ='DEFINE TABLE to2 TYPE RELATION IN message OUT agent ENFORCED SCHEMAFULL PERMISSIONS NONE'
[DIRTY-FLIP] ENFORCED landed = True
```
The dirty-store `OVERWRITE` flip lands `ENFORCED`+endpoint typing on an EXISTING untyped relation table on 3.2.1 — the load-bearing production-touching behaviour. No re-probe contradicted any contract pin.

## Changes (`loremaster/loremaster/store/surreal_schema.py` ONLY)
New constants (comms section, after `_BRIEFED_IN_OUT_INDEX_FIELDS`):
- `MESSAGE_TABLE = "message"`, `TO_RELATION = "to"`, `MESSAGE_SEQUENCE_NAME = "message_seq"`, `MESSAGE_BODY_MAX_CHARS = 2000` (public — 03a imports it; DRY).
- `_MESSAGE_GRADE_{SIGNAL,DIRECTIVE}` / `_MESSAGE_GRADES` / `_MESSAGE_GRADE_ALLOWED`.
- `_MESSAGE_FIELD_SPECS`: `seq int` · `session string` · `thread string` · `sender record<agent>` · `grade string ASSERT $value IN ['signal','directive']` · `body string ASSERT string::len($value) <= 2000` · `refs array<string> DEFAULT []` · `task_id option<string>` · `question bool DEFAULT false` · `created_at datetime`. (all via `_define_field` → `OVERWRITE`.)
- `_TO_FIELD_SPECS`: `session string` · `created_at datetime` · `seen_at option<datetime>` · `acked_at option<datetime>` · `ack_note option<string>`. `in`/`out` NEVER hand-declared (auto by TYPE RELATION).
- `_TO_IN_OUT_INDEX_FIELDS = ("in","out")` (UNIQUE), `_TO_DRAIN_INDEX_FIELDS = ("out","seen_at")` (plain drain index).

`_define_relation_table` — NEW SIGNATURE (one helper, not a fork — DRY/ONE-IMPLEMENTATION):
`_define_relation_table(name, in_table, out_table, *, enforced=False)` now emits
`DEFINE TABLE OVERWRITE {name} TYPE RELATION IN {in} OUT {out}[ ENFORCED] SCHEMAFULL`.
The signature change makes every caller a type error until updated — the intended mechanism. All three existing callers updated with real endpoints:
- `_briefed_statements` → `(BRIEFED_RELATION, AGENT_TABLE, BRIEF_TABLE)` (agent→brief)
- `_refers_statements` → `(REFERS_RELATION, CODE_NODE_TABLE, NAME_TABLE)` (code_node→name)
- `_answers_to_statements` → `(ANSWERS_TO_RELATION, CODE_NODE_TABLE, NAME_TABLE)` (code_node→name)
(edge directions verified against `graph_surreal.py` RELATEs and `briefs.py:757`; the blast-radius suites re-prove them.)

New `_define_sequence(name)` helper → `DEFINE SEQUENCE IF NOT EXISTS {name}` (no BATCH/START).

New `_message_statements()` (message node + fields + `_define_sequence(message_seq)` + `to` edge via `_define_relation_table(..., enforced=True)` + `_TO_FIELD_SPECS` + UNIQUE(in,out) + drain index) and public `generate_message_ddl()` (mirrors `generate_agent_ddl`).

## Gates (passed-COUNTs)
| gate | command | result |
|---|---|---|
| scoped | `pytest test_comms_schema.py test_surreal_schema.py -n auto` | **304 passed, 0 failed** |
| blast radius | `pytest test_graph_surreal.py test_brief_ledger.py test_agent_registry.py test_comms_render_architecture.py test_comms_fleet_grouping.py -n auto` | **432 passed, 0 failed** |
| invariant (03a RED) | `pytest test_message_ledger.py` | **14 failed / 166 errors** (== HEAD; all `ModuleNotFoundError: loremaster.messages`) |
| mypy | `scripts/typecheck.sh` | `surreal_schema.py` CLEAN; **55→54** errors (my change removed 1). Remaining 54 all in the RED 03a/03b contract files — see below. |
| ruff | `uv run ruff check .` | **All checks passed!** |

**⚠ typecheck flag (decision-needed).** `scripts/typecheck.sh` is NOT globally zero, and was not zero at HEAD either (55 errors). All 54 remaining `error:` lines are in the immutable committed RED contract for 03a/03b (derived from `error:` lines only): `test_comms_tool.py` (32), `_message_fakes.py` (12), `test_comms_promise_registry.py` (7), `test_message_ledger.py` (3) — every one from a reference to a not-yet-built module (`loremaster.messages`, `_render_comms_*`). These are OUT of my writable set (the contract is immutable) and belong to packets 03a/03b. My change introduced ZERO new mypy errors and resolved one (`generate_message_ddl` now exists → the 55th, in a 5th file, is gone). The global gate cannot reach zero until 03a/03b land their modules — flagging rather than narrowing scope.

## Mutation proofs (real tree; `cp -a` content backup, restored + md5-verified byte-exact each time)
| # | mutation | pin(s) | result |
|---|---|---|---|
| a | `to` edge → `IF NOT EXISTS` | `TestRelationFlipAgainstAnExistingStore::test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store` | **RED** — stored def stayed `DEFINE TABLE to TYPE RELATION SCHEMAFULL` (silent no-op, ENFORCED never landed) |
| b | drop `ENFORCED` (`enforced=False`) | `TestEnforcedIsLiveOnTheDeliveryEdge` | **4 RED** (ghost OUT/IN, no-dangling-edge, INSERT-RELATION-door: "DID NOT RAISE") + **2 controls stayed GREEN** (real-endpoint accepted, INSERT RELATION legal-with-real) |
| c | `refers` → bare untyped `IF NOT EXISTS` | guard-kind pin + `test_every_relation_table_in_every_comms_generator_is_typed` + `test_the_flip_LANDS_on_an_existing_untyped_relation_table[refers]` | **3 RED** + **2 controls GREEN** (`[briefed]`/`[answers_to]` flip-lands unaffected — mutation isolated) |
| control | restore byte-exact | all 14 mutated pins | **14 passed** on the restored tree |

Backup (`surreal_schema.py.GOOD`) and the probe script were removed; `git status` shows only `surreal_schema.py` modified.

## Decisions I made (with the alternative written down)
1. **`asked_at` is NOT a `message` column.** The packet-doc Scope-IN prose lists `asked_at` as a node field, but the 03a contract (`test_message_ledger.py`) defines `asked_at` ONLY on `WaitingOnAnswer` and pins `waiting.asked_at == sent.message.created_at` (`test_asked_at_IS_the_questions_own_created_at`); the `Message` value object has no `asked_at`, and no raw query references `message.asked_at`. Reading A (stored column): adding a REQUIRED `asked_at datetime` would break the store contract's own `_create_message` (which omits it) with "Expected datetime found NONE"; an `option<datetime>` version would be a dead unused column. Reading B (derived from `created_at`): matches every pin. **I chose B — no `asked_at` column.**
2. **`question` = `bool DEFAULT false`.** 03a's `Message.question: bool` is non-optional; the store contract's `_create_message` omits `question`. `DEFAULT false` satisfies both (omitted → false = "ordinary send is not a question"), whereas `option<bool>` would decode to `None` and contradict the value object. `bool` (no default) would break `_create_message`.
3. **`MESSAGE_BODY_MAX_CHARS` lives in `surreal_schema`** as the one source of the 2000 bound; 03a's `_msg().MESSAGE_BODY_MAX_CHARS` should import it, not re-declare — the store ASSERT and the app teaching-reject must never drift (DRY law).

## Tool honesty
The lore MCP server was listed as **still-connecting at session start**, so I performed all code-structure lookups (definitions, the `_define_relation_table` caller set, edge directions) via **direct Read/Grep over the real tree** rather than waiting on it — SAID here per repo law. A `lore_index()` at report time confirms lore is now reachable (watching `/workspace @ feat/surreal-unification`, `last_sync` age 10 s — it has already indexed my `surreal_schema.py` save), but no index-backed answer was relied upon for any decision above; every fact is from a live read of the tree or a live probe against spike-surreal 3.2.1. The `_define_relation_table` caller set (3 sites, all in-module) was cross-checked with grep because it is a rename/signature-change exhaustiveness question (one missed caller compiles-but-mypy-errors) — mypy then confirmed zero missed sites.
