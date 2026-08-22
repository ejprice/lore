# REPORT-builder-60-w1 — packet 60 wave 1 BUILDER (the Keep substrate)

brief-base v14 read
brief project v7 read

## SUMMARY BLOCK
- **State: done-with-deviations** — the PRODUCTION build (my whole deliverable) is
  COMPLETE and CORRECT: both owned contract files fully GREEN (58 + 28), typecheck GREEN,
  ruff clean. ONE deviation: a required gate (`test_retry_seam.py`) is RED for a reason
  entirely OUTSIDE my writable set — it never registers the new `KeepStore` seam in its
  two HAND-WRITTEN canonical maps (`_SEAM_REJECTION_EVENTS` / `_SEAM_REJECTION_NOUNS`),
  a CONTRACT/test-file gap (the same registration packets 48/49 did for their stores).
  My `_query` emits the CORRECT canonical values; only the maps lack the entry. **This
  blocks the WAVE COMMIT** until a 2-line test-map edit lands — exact edit in §FORK. I did
  NOT make it (builder≠grader; test edits forbidden). Finding filed on `lore_findings`.
- **Capability check: full** — lore tools loaded (keyword form), spike TEST store
  `ws://127.0.0.1:18000` up (HARNESS_SLUG=general), all named files/paths present.
- **Touched ONLY the 2 production files:** `loremaster/loremaster/store/surreal_schema.py`
  (filled the 3 keep stubs) + `loremaster/loremaster/keeps.py` (filled the 7 CRUD verbs +
  mappers). NO test file, NO scaffold, NO other slice touched by me. ⚠ `git diff --stat`
  also lists `tests/_enforced_relations_scaffold.py` + `tests/test_enforced_relations.py`
  as modified — those are the CONTRACT AUTHOR's pre-existing edits (the `member_of`
  declaration + five→six re-count), already `M` in the session-start `git status` BEFORE
  I began; I never opened them. My edits: `surreal_schema.py` (tracked, +171) + `keeps.py`
  (new/untracked).
- **Deviations:** none in the build. One escalation (§FORK) — a required gate cannot go
  green without a TEST-map edit forbidden to me (builder≠grader). Did NOT edit it.
- **Packages considered:** ULID id mint → reused installed `ulid` (`str(ULID())`, the
  `messages.py:763` precedent) — `keep_with_trigger` (trigger: a new bare-id scheme). No
  new dependency; nothing package-replaceable hand-rolled.
- **Reuse ledger:** 3 genuinely-new reusable symbols, all dispositioned (§DRY ledger).
- **Graded:** N/A — this is a build, not a verdict on someone's artifact. Work at
  `b9e6335` (`git rev-parse HEAD` = `b9e6335`, SAME).
- **Decisions needed:** ONE — §FORK (register `KeepStore` in `test_retry_seam.py`'s two
  canonical maps, or route to the contract author). Recommendation: register it (the
  packet-48/49 sanctioned resolution), 2 lines, values given.
- **Pointers:** §Gate receipts · §What I built · §DRY ledger · §FORK (retry-seam) · §Store-law citations.

---

## §Gate receipts (real repo @ `b9e6335`, live spike `:18000`, HARNESS_SLUG=general)

| gate | command | result |
|---|---|---|
| keep schema contract | `pytest -n auto tests/test_keeps_schema.py` | **58 passed** |
| keep store contract | `pytest -n auto tests/test_keeps_store.py` | **28 passed** |
| enforced+blocks+surreal_schema+surreal_store | `pytest -n auto tests/test_enforced_relations.py tests/test_blocks_edge.py tests/test_surreal_schema.py tests/test_surreal_store.py` | **552 passed** |
| retry seam | `pytest -n auto tests/test_retry_seam.py` | **2 failed / 661 passed** — the 2 failures are the KeepStore canonical-map gap (§FORK), NOT a production defect |
| typecheck (all members) | `scripts/typecheck.sh` | **GREEN** — lorerunes/lorescribe/loresigil OK, `loremaster OK` (221 src files), skills/docs-eval/scripts/shellcheck OK |
| ruff | `uv run ruff check .` | **All checks passed!** |

The full combined `pytest -n auto` over the whole brief gate set = **2 failed, 1299
passed** (the same 2 retry-seam failures; everything else green). Passed-COUNT present in
every tail (no silent "no tests ran").

The 2 RED retry-seam tests, verbatim:
- `TestTheExhaustionRecordIsATTRIBUTABLE::test_the_exhaustion_record_names_the_seam_the_server_and_the_engine_text[KeepStore]`
- `TestTheSeamsRejectionLogSurvivesTheCollapse::test_every_seam_still_logs_its_OWN_canonical_rejection_event`

---

## §What I built (file:line by symbol, not line number)

### `surreal_schema.py` — the 3 keep stubs, filled (the fold into `generate_ddl` was already real)
- **`_keep_statements()`** — `[_define_table(KEEP_TABLE)]` + one `_define_field` per
  `_KEEP_FIELD_SPECS` (`keeper`/`name`/`created_at`) + the CALL-TIME-derived `type`
  field-def (`f"ASSERT $value IN [{type_allowed}]"` from `_KEEP_TYPES`, **NO DEFAULT**,
  the `_principal_statements` idiom) + `_plain_index(keep, keep_keeper, ("keeper",))`
  (NON-unique, `IF NOT EXISTS`). Store §1.1.
- **`_member_of_statements()`** — `[_define_relation_table(member_of, principal, keep,
  enforced=True)]` (→ `DEFINE TABLE OVERWRITE member_of TYPE RELATION IN principal OUT
  keep ENFORCED SCHEMAFULL`) + `_define_field` per `_MEMBER_OF_FIELD_SPECS` (`since`) +
  the CALL-TIME-derived `rank` field-def (`f"DEFAULT '{contributor}' ASSERT $value IN
  [{ranks_allowed}]"` from `_KEEP_RANKS`) + `_unique_index(member_of, member_of_in_out,
  ("in","out"))`.
- **`generate_keep_ddl()`** — `";\n".join(_keep_statements() + _member_of_statements()) +
  ";\n"`. The `generate_ddl` fold (`surreal_schema.py` @1727-1728) already called both
  assemblers AFTER `_principal_statements`, so the edge is emitted IDENTICALLY by both
  paths (a contract pin checks it — GREEN).

### `keeps.py` — the 7 CRUD verbs + private mappers
- **`create_keep`** — resolves keeper via `self._resolve_principal_id` (the Q-1 seam →
  composed `PrincipalStore.get_by_email`); mints `str(ULID())`; in ONE
  `execute_transaction` (via `compose(TxnFragment(...))`, the `tasks.py::_apply` idiom)
  CREATEs the keep (CONTENT object literal, `keeper: type::record('principal',$kid)`, the
  `mint` precedent) AND RELATEs `$keeper->member_of->$keep` at default rank=contributor
  (Fork D auto-add). Atomic: both or neither. Reads back through `get_keep`.
- **`get_keep` / `list_keeps_for_keeper`** — EXPLICIT projection `_KEEP_READ_PROJECTION`
  (`id, keeper, type, name, created_at`) + `_row_to_keep` mapping `name` via
  `PrincipalStore._optional_str(row.get("name"))` — **never `SELECT *`+bracket** (store §2;
  the exact attack-9 / w1b instrument). `list_keeps_for_keeper` filters `WHERE keeper =
  type::record('principal', $pid)` — the keeper IndexScan (Fork A rider).
- **`add_household_member`** — check-first idempotent (`_read_membership` → return the
  existing edge, a benign no-op, never a raise / second edge); else RELATE at default rank.
- **`remove_household_member`** — keeper-lockout guard (raise `KeeperLockoutError` BEFORE
  any delete when `keep.keeper_id == member_id`); else `DELETE member_of WHERE in=$m AND out=$k`.
- **`set_rank`** — `UPDATE member_of SET rank=$rank WHERE in=$m AND out=$k`; reads back.
- **`list_household`** — reads `member_of` as a PLAIN table (`WHERE out=$keep`, store §4),
  mapping each row via `_row_to_membership`.
- **`_query`** — UNCHANGED from the stub (named exactly `_query`, routed through
  `run_query`, `noun="keep query"`, `label="keep.query.rejected"`). I did NOT rename or
  hand-roll retry.

---

## §DRY ledger (new reusable symbols — proved by pointing, not cloning)

Shared seams REUSED (proved by pointing): `run_query` via `self._query` · `execute_transaction`
+ `compose` + `TxnFragment` (`loremaster.store._txn`, the `tasks.py::_apply` write-path idiom)
· `PrincipalStore.get_by_email` via `_resolve_principal_id` · `PrincipalStore._to_aware_utc`
via `self._to_aware_utc` · `PrincipalStore._as_rows` · `PrincipalStore._optional_str` ·
`_define_field`/`_define_relation_table`/`_define_table`/`_plain_index`/`_unique_index` (shared
DDL emitters, mutation-proven by the contract's ROUTES-THROUGH pins) · installed `ulid`.

| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `KeepStore._record_id_part` (static) | `lore_search "helper extracting the id portion of a str(RecordID) … record_id_part"` | `PrincipalKeyStore._record_id_part` (identical logic, on a SIBLING store) | **HAND-ROLLED** — id-string partition is TRIVIA (not policy: no retry/backoff/classification/validation). Reusing the sibling's static would import `PrincipalKeyStore` into `keeps.py` solely for a 2-line parse; the same partition is already inlined in the stub's `_resolve_principal_id` (same module). Named the candidate; kept a local static for module-locality. ⚠ Minor — flag for the lead if a shared `lorerunes` id-part predicate is wanted later. |
| `_KEEP_READ_PROJECTION` / `_MEMBER_OF_READ_PROJECTION` (module consts) | `lore_search "read projection constant explicit SELECT columns for a store row mapper"` | per-table projections only (trace test, `principals._READ_PROJECTION`) — NO shared projection helper exists | **HAND-ROLLED** — projections are per-table BY DESIGN (each table names its own columns); mirrors `principals._READ_PROJECTION`. |
| `KeepStore._row_to_keep` / `_row_to_membership` / `_read_membership` | (structural — the `_row_to_principal` mapper idiom) | `PrincipalStore._row_to_principal` (per-model mapper) | **HAND-ROLLED** — a per-model row mapper is model-specific, never shared policy (each value object has its own). They REUSE the shared `_to_aware_utc`/`_as_rows`/`_optional_str` inside. |

No shared-policy symbol was cloned. `create_keep`'s atomicity rides the shared
`execute_transaction`; nothing re-classifies conflicts or hand-rolls retry.

---

## §FORK (ESCALATION — retry-seam canonical-map registration; a TEST-FILE gap I may not edit)

**What:** `test_retry_seam.py` auto-discovers every class owning an `async def _query`
(`_discover_query_seams()`, AST-based). It found `KeepStore` (present since the STUB —
its `_query` shipped with `noun="keep query"` / `label="keep.query.rejected"`). But the
two CANONICAL maps in that file are **HAND-WRITTEN and were never given a `KeepStore`
entry**, so two pins that compare discovered-vs-canonical fail:

- `_SEAM_REJECTION_EVENTS` (`test_retry_seam.py`, ~line 6030) — missing `KeepStore`.
- `_SEAM_REJECTION_NOUNS` (~line 6075) — missing `KeepStore`.

**This was RED at the STUB too** (the seam existed with these values before I wrote a line
of CRUD), so it is a **CONTRACT GAP**, not a build defect — the identical registration
packets **48/49 performed** for `PrincipalStore`/`PrincipalKeyStore` (see the in-file
comments at those entries: *"registering its canonical event is the sanctioned resolution
… never a bespoke seam that dodges the AST enumeration (#120), never 'pre-existing,
ship'"*). My production `_query` emits the CORRECT values; only the maps lack the row.

**Why I did not fix it:** it is a TEST file, outside my writable set, and builder≠grader
is absolute repo law (my brief: *"test edits are forbidden; if a test seems wrong, STOP
and message the lead"*). This is out-of-authority deferral, surfaced NOW with the exact edit.

**The exact edit (2 lines), for the lead or a contract fixer:**
```python
# in _SEAM_REJECTION_EVENTS (alongside "PrincipalStore": "principal.query.rejected"):
    "KeepStore": "keep.query.rejected",
# in _SEAM_REJECTION_NOUNS (alongside "PrincipalStore": "principal query"):
    "KeepStore": "keep query",
```
Both values are exactly what `KeepStore._query` raises/logs today (mirror the `principal`
naming convention). `keep query` is a DOMAIN-naming noun, so it keeps the two-population
monoculture guard non-trivial (no risk to `test_the_canonical_noun_map_is_not_a_MONOCULTURE`).
The seam-count FLOOR (`_MIN_KNOWN_SEAMS = 13`) is already satisfied (16 seams discovered),
so no count pin needs touching. After that edit I expect all 663 retry-seam tests GREEN.

**Recommendation:** register it (the sanctioned packet-48/49 resolution). It is contract
territory; do NOT resolve it by changing my production `_query` (that would be the
#120 "bespoke seam that dodges the enumeration" anti-pattern the maps' own comments forbid).

---

## §Store-law citations (docs/reference/surrealdb-31-capabilities.md — cited, not re-transcribed)
- §1.1 — FIELD `OVERWRITE` (via shared `_define_field`); TABLE/INDEX `IF NOT EXISTS`;
  RELATION table `OVERWRITE … ENFORCED` (via `_define_relation_table(enforced=True)`).
- §2 — CONTENT writes; `keeper` bound as `type::record('principal',$id)`; EXPLICIT
  projection + `.get("name")` (never `SELECT *`+bracket — the `dm`-keep NONE trap).
- §3 — `create_keep` writes CREATE+RELATE in ONE `execute_transaction` (every statement
  verified), never a lax multi-statement `query()`.
- §4 — RELATE bound-RecordID endpoints (`$keeper->member_of->$keep`); ENFORCED validates
  both endpoints (the atomicity/ghost-keeper pin); reads of the edge use it as a PLAIN
  table (`WHERE out=$keep` / `WHERE keeper=$p`), never an arrow traversal.

## §Provenance
- Live probe used to settle the `in`/`out` read spelling: both bare `SELECT in, out, rank,
  since` and `record::id(in)` work on 3.2.4; chose bare `in, out` + `_record_id_part`
  partition (the `_resolve_principal_id` idiom). Probe was throwaway (a `/tmp` script,
  not a committed instrument — the claim is re-established by the GREEN live store tests
  in `tests/test_keeps_store.py`, which exercise `list_household` / `_read_membership`).
