brief-base v16 read · brief project v7 read

# REPORT — investigate-486 (read-only investigator, lore finding #486)

## SUMMARY BLOCK
- **State:** done-with-deviations
- **Deviation (1):** a store-free `--tb=line` control pytest (§A.3) ran while another project's pytest (`mobile-pricepaper-smoke`) was live. It touched no store, no DB and no port, but it breaks the brief's "only when NO other pytest is live" rule. The single-test repro loop (§A.4) ran on a clear process table.
- **Packages considered:** none. No mechanism specified or built; a fix shape is recommended only (§5).
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** none (0 new symbols in the repo; the one scratch instrument is pasted verbatim in §A.1).
- **Graded:** n/a
- **Headline:** #486 is a **TEST-HARNESS ESCAPE, not a production defect** (HIGH on the escape, MEDIUM on the contender). The raw `QueryError` came from the test's own unretried `_surreal_harness.run()` writes in `_orphan_the_successor_in_the_store` (`DELETE` S / `UPDATE` P on `memory`). The most likely contender is the engine's own background FULLTEXT/HNSW index compaction (`--index-compaction-interval`, default 5s on 3.2.4). Test concurrency is not the cause. **Blast radius: 24 unwrapped test-side WRITE sites on HNSW/FULLTEXT tables across 8 files**, plus 168 on other tables.
- **Decisions needed:** (1) accept the fix home: `_surreal_harness.run` routes through the harness's existing `_run_under_store_retry_seam`, with an explicit raw opt-out (§5). (2) Rule on the opt-out set: 4 files mention conflict markers and must be adjudicated (§5).
- **Receipts:** §1 call chain · §2 seam/guard analysis · §3 contender · §4 blast radius · §A instruments + outputs.
- All measurements taken 2026-09-26 at HEAD `6a099549` (branch `feat/surreal-unification`; lore index watched root at the same ref, `lore_index()` last_sync 35s at start).

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473), so textual scans used `awk`/`sed` and one Python AST scan (§A.1). This fallback was for a non-symbol textual seam (statement verbs in string literals), which is one of the dogfood protocol's sanctioned grep cases. Structure reads went to lore first: `lore_findings get 486`, `lore_get_symbol LocalMemoryBackend.restore_from_ledger`, `lore_index`, `lore_search` (surrealdb-docs tier + code).
- `pytest-repeat` is **not installed** (`find_spec("pytest_repeat") is None`), so there was no `--count`. The repro was a sequential loop of single runs, which is load-free and cannot recreate `-n 12` pressure. See §A.4 for what that bounds.
- No scratch copy was needed. No production or test file was mutated.

## 1. Which store call raised it?
**Answer (HIGH that it was a test-side `run()` call; MEDIUM that it was one of the two WRITES rather than a SELECT):**
the raise came from `loremaster/tests/test_memory_replay_fidelity_63b_ib.py::_orphan_the_successor_in_the_store`, one of its two raw statements:
`DELETE type::record('memory', $sid)` or `UPDATE type::record('memory', $pid) SET valid_until = NONE, superseded_by = NONE`.

**Call chain:**
`test_a_cross_owner_replay_close_is_skipped_with_a_warning` → `_orphan_the_successor_in_the_store(connection, …)` → `_surreal_harness.run(connection, statement, params)` → `connection.query(...)` (SDK `AsyncWsSurrealConnection.query`, which delegates to `query_raw` and then calls `_check_query_result`) → `surrealdb/connections/utils_mixin.py:24` `raise parse_query_error(stmt)` → a raw `surrealdb.errors.QueryError`. The `connection` is the fixture's `connect_admin(env)` raw SDK connection.

**Why this is decisive and not a guess** (elimination over every `.query` caller on the test's execution path):
1. `utils_mixin.py:24` is `UtilsMixin._check_query_result`. Among the SDK doors, only `.query()` calls it (`"_check_query_result" in getsource(AsyncWsSurrealConnection.query)` is True, and False for `query_raw`). So the raise came from a `.query()` call, never from `execute_transaction` / `_txn_query_raw` (`query_raw`).
2. Every production `.query()` on this path goes through `_txn.run_query` (via `LocalMemoryBackend._query`: `_existing_ids`, the `_replay_record` predecessor pre-read) or `_txn.bootstrap_session` (via `_ensure_connection`). `QueryError` → `ServerError` → `SurrealError` sits inside `_CONNECTION_ERRORS`, so `run_query._attempt` catches it and does one of three things. A `can be retried` text raises `RetryableConflictSignal` and is retried. Any other text is re-raised **wrapped** as `SurrealStoreError`/`TxnDomainRejectionError` `from error`. Exhaustion raises `TxnContentionExhaustedError`. `bootstrap_session` retries conflicts, and `_ensure_connection` wraps exhaustion as `SurrealConnectionError`. **No production path lets a raw `QueryError` be the outermost exception.**
3. Under `--tb=line`, pytest prints the crash site of the **outermost** exception. The control in §A.3 (store-free) shows this: an unwrapped raise prints `utils_mixin.py:24: surrealdb.errors.QueryError: …can be retried`, and the same raise wrapped `from error` prints the wrapper's own file:line and `SurrealStoreError`. #486's line has the first shape, so nothing wrapped it.
4. The remaining `.query()` callers on this test's path are all test-side. Fixture setup/teardown is already retried (`connect_admin` → `bootstrap_session`; `drop_database` → `_run_under_store_retry_seam`; `backend.ensure_ready` / `audit_store.ensure_ready` → `execute_transaction`). The `_governed_contract` F5 observer is excluded twice over: it reads only through the unwrapped `query_raw` door (`_f5_unwrapped_query_raw`, never `utils_mixin:24`), and it only runs inside `observe_governed_table_writes`, which this test does not open. **That leaves the test body's six `run()` calls:** `DELETE` and `UPDATE` (in `_orphan_the_successor_in_the_store`) plus four `SELECT`s (`_governed_row`).
5. Between those six, "Resource busy" is RocksDB's optimistic-transaction **write-write** conflict status (the spike store is `rocksdb:/data/store.db`, per `~/.config/containers/systemd/spike-surreal.container`). A read-only `SELECT` has no write set to validate, so the two writes are the candidates. ⚠ **Bound:** that SELECTs cannot conflict is **believed, not probed** (MEDIUM). The original `--tb=line` hid the frame, and I could not recreate the failure (§A.4), so I cannot say which of the two writes fired. The DELETE is the stronger candidate because it must remove S's FULLTEXT postings and HNSW node, which are the keys a compaction pass rewrites (§3).

## 2. Does it route through the shared retry seam?
**Answer (HIGH):** **it escapes.** The escaping site is `loremaster/tests/_surreal_harness.py::run` (the harness's raw statement funnel: `return await connection.query(statement, params)`, with no classify-and-signal). The retry never fired because it was never in the loop. The brief's other candidates are all refuted: budget exhaustion would surface as `TxnContentionExhaustedError`; a reworded message would surface as a *wrapped* `SurrealStoreError`; commit/compose and nested statements do not apply to a single-statement raw `query()`.

**Should the #136-fixed runtime guard (`loremaster/tests/_sdk_guard.py`) have seen it? No, by its declared design (HIGH).** Its docstring states the invariant as "No call on a live SurrealDB connection may escape the retry driver". It then scopes this to **production** callers: attribution is "by the IMMEDIATE caller, never 'the nearest production frame'", and `install(production_root=artifact_root())` watches the imported package root. The immediate caller here is test code, so the guard is correctly silent. This is not a guard defect. It is a **reach bound that nothing states**: the guard covers production, and nothing covers the harness's own statement funnel.

**The sharper finding is in the harness's own claim.** `_surreal_harness._run_under_store_retry_seam`'s docstring calls itself "This module's SINGLE classify-and-signal site" and says that "Both teardown operations that can hit the engine's retryable write-write conflict — selecting the database (`use()`) and removing it — call THIS". In other words, it states "the harness operations that can conflict" over **teardown only**. `run()` is a third harness operation that can hit the same conflict and does not call it. This is **THE QUANTIFIER LAW** (CLAUDE.md): a safety property derived over the members of a set that someone analysed (finding #150's teardown), then read as holding for the whole set (every harness call on a live connection).

## 3. Production defect or test-harness artefact?
**Answer: TEST-HARNESS ARTEFACT on the escape side (HIGH). The contention source is ENGINE-INTRINSIC and NOT the test's own setup concurrency (MEDIUM).**
- **Not the test's concurrency.** Every await in the test is sequential on one DB (`unique_database()` → `test_<pid>_<uuid4>`), and no production code on the path spawns background work. A scan of `memory/*.py`, `governed.py` and `audit.py` for `create_task|ensure_future|TaskGroup|gather(|run_in_executor|to_thread` found no hits (awk fallback). xdist peers write to *other* databases.
- **The best-supported contender is the engine's own background work on this DB's index keys** (MEDIUM, not probed). `surreal start --help` on the pinned image (`docker.io/surrealdb/surrealdb:v3.2` → `3.2.4+20260803.93ab219`) lists `--index-compaction-interval` (**default 5s**), `--async-event-interval` (5s) and `--reclaim-interval` (60s). The schema defines no `EVENT`/`ASYNC`/`DEFER`/`CONCURRENTLY` (awk over `store/surreal_schema.py`), so async events do not apply. That leaves index compaction over `memory`'s FULLTEXT (`memory_note_text_ft`) and HNSW (`memory_embedding_hnsw`) indexes, which the preceding `remember()` calls just populated. The raw `DELETE` of S must rewrite exactly those index structures.
- **Corroboration from this repo's own measurements:** (a) `docs/reference/surrealdb-31-capabilities.md` §1.7, `[MEASURED, P8c]`: "can hit a retryable conflict with an async HNSW index build". (b) `_surreal_harness._remove_database_with_retry`'s docstring (finding #150): teardown `REMOVE DATABASE` "races background RocksDB/index maintenance work … rolls the REMOVE back with … This transaction can be retried", measured at "~30-50% of standalone store-suite runs". The same engine-background-vs-foreground-write class was measured once already and fixed at teardown only.
- **Why only under load:** isolation passed 40/40 here (§A.4) and 12/12 ×3 in the finding. Under the full `-n 12` run the engine is saturated, so each compaction pass takes longer and is more likely to overlap a sub-millisecond foreground write. ⚠ This part is **inference**. Nothing here measured it (bound: the brief forbids restarting the spike store with a different compaction interval or running the full suite).
- **Production exposure for this mechanism: none found.** The same statement shapes in production (`remember`/`invalidate`/`_replay_record` → `_apply` → `execute_transaction`, and every `_query` → `run_query`) ride the driver, and the production reach is policed by `_sdk_guard` plus the AST lint. I did not re-audit that reach; I cite it.

## 4. Blast radius (derived from a property, not a hand-list)
**Property:** a test-side call that issues a SurrealQL statement on a live SDK connection outside the retry driver. There are two doors: (a) the harness `run()` funnel; (b) a direct `.query`/`.query_raw` whose enclosing function is not an attempt body handed to a driver. Test roots are derived from `[tool.uv.workspace] members`. The "compacted-index tables" set is derived by rendering every `generate_*_ddl` and keeping tables with `HNSW`/`FULLTEXT` indexes, which yields **{`memory`, `chunk`}**. Instrument: §A.1 (verbatim). Output: §A.2.

| class | sites |
|---|---|
| **WRITE on a HNSW/FULLTEXT table (the #486 shape)** | **24** (8 files) |
| WRITE on another table (door a / b) | 168 / 11 |
| READ on a HNSW/FULLTEXT table (believed non-conflicting, §1.5 bound) | 37 |
| READ elsewhere (door a / b) | 288 / 7 |
| statement not a literal, unclassified (door a / b) | 222 / 5 |
| **total unwrapped** | **762 sites in 66 files** |

The 24 #486-shape sites (file:line and enclosing function) are listed in §A.2. They include both #486 sites and `test_memory_enforcement_63b_ia.py` (10), `test_memory_supersede_atomicity_63b_ib.py` (3), the `_governed_contract` seeders (`seed_memory_legacy`, `seed_memory_governed`, used by many tests) and `test_governed_substrate_63a.py` (2).
- **Bounds (stated so this table does not over-claim):** a statement built in a variable classifies as `?` (227 sites: unknown verb, unknown table). "Other table" writes are exposed only to engine background work on *their* keys, which is lower but not zero: teardown's #150 conflict hit `REMOVE DATABASE`, which spans every key. Conftest-local raw helpers are caught only by door (b). The alias-follow covers `from _surreal_harness import run as X` only.
- Line numbers in §A.2 are as measured at `6a09954`. Cite the enclosing functions; the lines go stale.

## 5. Recommended fix shape (NOT implemented)
**ONE-IMPLEMENTATION home: `loremaster/tests/_surreal_harness.py::run` routes its `connection.query` through the harness's existing `_run_under_store_retry_seam`** (which already delegates classification, budget and backoff to `_txn` in-function, per RULING 1). Do not add a per-test retry, and do not add a second harness helper. Fixing `run` fixes all 24 + 168 literal-write sites and the 222 unclassified ones in one place, and it makes the docstring's "SINGLE classify-and-signal site" claim true over the whole module.
- **Opt-out, not opt-in:** some tests may *deliberately* observe a raw conflict through `run`. Add an explicit raw door (e.g. `run(..., retry=False)` or a separately named `run_unretried`) and have **the operator/contract author rule each use**. Candidate set derived by awk: files that import `run` and mention a conflict marker are `test_retry_seam.py` (31), `test_surreal_store.py` (11), `test_store_lease.py` (3), `test_txn_contention.py` (1). This is a worklist, not a verdict.
- **Pins (the rider):**
  - (i) a fake-connection pin in `test_surreal_harness.py` (the existing `_remove_database_with_retry` pin idiom): `run` retries a once-conflicting `can be retried` error and returns the success, and does not retry a domain error.
  - (ii) **prove sharing by MUTATION**: move `_txn._RETRYABLE_CONFLICT_MARKER` and `run`'s pin must go red (the same mutation the teardown pins already carry).
  - (iii) close the reach gap by making the harness's coverage a checked variable: an AST pin asserting that `_surreal_harness` contains no `connection.query`/`query_raw`/`use` call outside an attempt body handed to `_run_under_store_retry_seam`, with an allowlist for the explicit raw door. This allowlists the safe set per THE INSTRUMENT LESSON, rather than listing the forbidden.
- **Satisfiability watch:** retrying inside `run` changes timing for tests that measure store traffic (`measure_store_traffic`/`StoreTraffic`). A contract author should check that those pins count *statements issued*, not *calls to run*.
- **Not recommended:** marking the test `flaky`/rerun (it has a mechanism), or wrapping the two #486 statements locally (copy #2 of the harness seam, which is exactly the #102 shape).

## Confidence labels
- §1 "raised by a test-side raw `run()`": **HIGH** (elimination plus the §A.3 control). "One of the two writes, not a SELECT": **MEDIUM** (RocksDB read-only semantics believed, not probed). Which of the two writes: **UNKNOWN** (frame hidden, no recreation).
- §2 escape + guard-silent-by-design: **HIGH** (read `run`, `run_query`, `_sdk_guard` docstring/`install`).
- §3 harness artefact: **HIGH**. The contender being background index compaction: **MEDIUM** (flag default read live, prior measurements corroborate, no controlled probe). The load-dependence explanation: **LOW/inference**.
- §4 counts: **HIGH** for the derivation as stated, with bounds in §4. Hand-checked for false positives: the first pass matched `chunks_total` as `chunk`, and the regex was tightened before the figures above.

## Follow-ups surfaced (operator/lead owns scope)
- **Controlled contender probe (not run; out of this brief's authority):** on a throwaway engine (never :18500, and not the shared spike), set `--index-compaction-interval` to 1s vs a very large value and hammer raw `DELETE`s on freshly-`remember`ed `memory` rows. A conflict rate that tracks the interval would confirm §3. Named decision point: whoever builds the §5 fix decides whether that receipt is needed (the fix is correct either way, because any `can be retried` must be retried).
- **`SAFE_CONNECTION_METHODS` receipt gap** (seen in passing in `_sdk_guard.py`, already self-declared there): the `signin` exemption's 256-connect probe is untracked and "UNVERIFIED". Not new; noted per scope law.

## A. Instruments and raw outputs
### A.1 Blast-radius instrument (scratch, pasted VERBATIM per brief-base §1; run as `uv run python raw_store_calls.py <repo-root>`)
```python
"""Blast-radius derivation for lore #486 (investigate-486, 2026-09-26).

PROPERTY: a test-side call that issues a SurrealQL statement on a live SDK connection
WITHOUT the store retry driver. Two doors, both derived from the tree, not hand-listed:
  (a) a call to `run(...)` where `run` is imported from `_surreal_harness` (the harness's
      raw `connection.query` funnel — no retry, by construction);
  (b) a direct `<expr>.query(...)` / `<expr>.query_raw(...)` in test code whose ENCLOSING
      function is not an attempt body handed to a retry driver (`retry_on_conflict`,
      `_run_under_store_retry_seam`, `_driver()`), i.e. not wrapped.
Each hit is classified by the statement's leading SurrealQL verb (WRITE vs READ) and by
whether it targets a table whose DDL carries an engine-background-compacted index
(HNSW / FULLTEXT: derived separately from the DDL generators = {memory, chunk}).
Test roots = every `[tool.uv.workspace] members` entry's tests dir that exists.
BOUNDS: a statement assembled in a variable elsewhere classifies as '?'; `run` imported
under an alias is followed; other raw helpers (e.g. conftest-local ones) are caught only via
door (b).
"""
from __future__ import annotations

import ast
import sys
import tomllib
from collections import Counter
from pathlib import Path

ROOT = Path(sys.argv[1])
WRITE = {"CREATE", "UPDATE", "UPSERT", "DELETE", "INSERT", "RELATE", "DEFINE", "REMOVE", "BEGIN", "ALTER", "REBUILD"}
READ = {"SELECT", "INFO", "RETURN", "LET", "SHOW"}
import re
COMPACTED_RE = re.compile(r"(\{MEMORY_TABLE\}|\{CHUNK_TABLE\}|'memory'|'chunk'|\bmemory:|\bchunk:|\b(FROM|INTO|UPDATE|DELETE|CREATE|UPSERT|INSERT)\s+(ONLY\s+)?(memory|chunk)\b)", re.IGNORECASE)
DRIVERS = {"retry_on_conflict", "_run_under_store_retry_seam", "_driver", "run_query", "execute_transaction"}

members = tomllib.loads((ROOT / "pyproject.toml").read_text())["tool"]["uv"]["workspace"]["members"]
test_roots = [ROOT / m / "tests" for m in members if (ROOT / m / "tests").is_dir()]


def statement_text(node: ast.AST | None) -> str:
    if node is None:
        return ""
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            else:
                parts.append("{" + ast.unparse(value.value) + "}")
        return "".join(parts)
    if isinstance(node, ast.BinOp):
        return statement_text(node.left) + statement_text(node.right)
    return ""


def verb_of(text: str) -> str:
    stripped = text.lstrip().lstrip("(").upper()
    word = stripped.split(None, 1)[0].rstrip(";") if stripped else ""
    return "WRITE" if word in WRITE else "READ" if word in READ else "?"


hits: list[tuple[str, int, str, str, str, bool, str]] = []
for test_root in test_roots:
    for path in sorted(test_root.rglob("*.py")):
        tree = ast.parse(path.read_text(), filename=str(path))
        run_names = {
            alias.asname or alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module == "_surreal_harness"
            for alias in node.names
            if alias.name == "run"
        }
        if path.name == "_surreal_harness.py":
            run_names.add("run")
        # functions handed to a driver by name: driver(fn, ...) / driver(fn)
        wrapped = {
            arg.id
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and (getattr(node.func, "id", None) in DRIVERS or getattr(node.func, "attr", None) in DRIVERS
                 or (isinstance(node.func, ast.Call) and getattr(node.func.func, "id", None) in DRIVERS))
            for arg in node.args[:1]
            if isinstance(arg, ast.Name)
        }
        parents: dict[ast.AST, ast.AST] = {}
        for node in ast.walk(tree):
            for child in ast.iter_child_nodes(node):
                parents[child] = node

        def enclosing(node: ast.AST) -> str:
            cursor = parents.get(node)
            while cursor is not None and not isinstance(cursor, (ast.FunctionDef, ast.AsyncFunctionDef)):
                cursor = parents.get(cursor)
            return cursor.name if cursor is not None else "<module>"

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            door = None
            statement_node = None
            if isinstance(node.func, ast.Name) and node.func.id in run_names and len(node.args) >= 2:
                door, statement_node = "a:run", node.args[1]
            elif isinstance(node.func, ast.Attribute) and node.func.attr in {"query", "query_raw"} and node.args:
                if path.name == "_surreal_harness.py" and enclosing(node) == "run":
                    continue  # the funnel itself; its callers are door (a)
                door, statement_node = f"b:.{node.func.attr}", node.args[0]
            if door is None:
                continue
            function = enclosing(node)
            if function in wrapped:
                continue  # an attempt body a retry driver runs
            text = statement_text(statement_node)
            compacted = bool(COMPACTED_RE.search(text))
            hits.append((str(path.relative_to(ROOT)), node.lineno, function, door, verb_of(text), compacted, text[:70].replace("\n", " ")))

by_class = Counter((h[3][0], h[4], h[5]) for h in hits)
print(f"test roots: {[str(r.relative_to(ROOT)) for r in test_roots]}")
print(f"TOTAL unwrapped statement call sites: {len(hits)}  files: {len({h[0] for h in hits})}")
for key in sorted(by_class):
    print(f"  door={key[0]} verb={key[1]:5} on_compacted_table={key[2]!s:5} -> {by_class[key]}")
print("--- WRITE on a compacted-index table (the #486 shape) ---")
for h in hits:
    if h[4] == "WRITE" and h[5]:
        print(f"{h[0]}:{h[1]} [{h[2]}] {h[3]} :: {h[6]}")
```
### A.2 Its output at `6a09954`
```
test roots: ['lorerunes/tests', 'lorescribe/tests', 'loresigil/tests', 'loremaster/tests']
TOTAL unwrapped statement call sites: 762  files: 66
  door=a verb=?     on_compacted_table=False -> 222
  door=a verb=READ  on_compacted_table=False -> 288
  door=a verb=READ  on_compacted_table=True  -> 37
  door=a verb=WRITE on_compacted_table=False -> 168
  door=a verb=WRITE on_compacted_table=True  -> 24
  door=b verb=?     on_compacted_table=False -> 5
  door=b verb=READ  on_compacted_table=False -> 7
  door=b verb=WRITE on_compacted_table=False -> 11
--- WRITE on a compacted-index table (the #486 shape) ---
loremaster/tests/_governed_contract.py:322 [seed_memory_legacy] a:run :: CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content
loremaster/tests/_governed_contract.py:349 [seed_memory_governed] a:run :: CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content
loremaster/tests/test_governed_migration_63a.py:123 [test_the_legacy_row_is_still_writable_after_the_field_add] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET importance = $i
loremaster/tests/test_governed_schema_63a.py:422 [run_governed_create] a:run :: CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content
loremaster/tests/test_governed_schema_63a.py:441 [_create_memory_legacy] a:run :: CREATE type::record('{MEMORY_TABLE}', $id) CONTENT $content
loremaster/tests/test_governed_substrate_63a.py:341 [test_a_guarded_write_on_a_vanished_row_raises_conflict] a:run :: DELETE type::record('memory', 'vanishing_row')
loremaster/tests/test_governed_substrate_63a.py:372 [_rescope_on_second_acquire] a:run :: UPDATE type::record('memory', 'toctou_row') SET owner_agent = type::re
loremaster/tests/test_memory_enforcement_63b_ia.py:548 [test_a_no_effect_write_is_not_a_governance_event] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'ke
loremaster/tests/test_memory_enforcement_63b_ia.py:575 [test_a_write_inside_a_rolled_back_txn_is_not_observed] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'ke
loremaster/tests/test_memory_enforcement_63b_ia.py:624 [test_a_write_then_revert_in_one_txn_is_unobserved_named_bound] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'ke
loremaster/tests/test_memory_enforcement_63b_ia.py:1596 [test_ii_shape_agnostic_a_concatenated_seizure_is_observed] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = 'ke
loremaster/tests/test_memory_enforcement_63b_ia.py:1626 [test_iv_two_gathered_writes_each_get_their_own_effect] a:run :: CREATE type::record('{MEMORY_TABLE}', 'g1') CONTENT { note_text: 'a', 
loremaster/tests/test_memory_enforcement_63b_ia.py:1632 [test_iv_two_gathered_writes_each_get_their_own_effect] a:run :: CREATE type::record('{MEMORY_TABLE}', 'g2') CONTENT { note_text: 'b', 
loremaster/tests/test_memory_enforcement_63b_ia.py:553 [test_a_no_effect_write_is_not_a_governance_event] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'legacy') SET {_COL_SCOPE} = {_C
loremaster/tests/test_memory_enforcement_63b_ia.py:1434 [test_the_ensure_ready_effect_predicate_discriminates] a:run :: DEFINE FIELD __oracle_probe ON {MEMORY_TABLE} TYPE option<string>
loremaster/tests/test_memory_enforcement_63b_ia.py:1640 [test_iv_two_gathered_writes_each_get_their_own_effect] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'g1') SET {_COL_SCOPE} = 'k1'
loremaster/tests/test_memory_enforcement_63b_ia.py:1641 [test_iv_two_gathered_writes_each_get_their_own_effect] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'g2') SET {_COL_SCOPE} = 'k2'
loremaster/tests/test_memory_replay_fidelity_63b_ib.py:457 [_orphan_the_successor_in_the_store] a:run :: DELETE type::record('{MEMORY_TABLE}', $sid)
loremaster/tests/test_memory_replay_fidelity_63b_ib.py:458 [_orphan_the_successor_in_the_store] a:run :: UPDATE type::record('{MEMORY_TABLE}', $pid) SET valid_until = NONE, su
loremaster/tests/test_memory_supersede_atomicity_63b_ib.py:110 [_poison_note_text] a:run :: DEFINE FIELD OVERWRITE note_text ON TABLE {MEMORY_TABLE} TYPE string A
loremaster/tests/test_memory_supersede_atomicity_63b_ib.py:459 [_rescope_on_second_acquire] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'race_pred') SET owner_agent = t
loremaster/tests/test_memory_supersede_atomicity_63b_ib.py:567 [_rescope_on_second_acquire] a:run :: UPDATE type::record('{MEMORY_TABLE}', 'gw_pred') SET owner_agent = typ
loremaster/tests/test_surreal_schema.py:302 [_create_chunk] a:run :: CREATE type::record('chunk', $id) SET tier=$tier, file_path=$file_path
loremaster/tests/test_surreal_schema.py:771 [test_memory_probe_round_trips] a:run :: CREATE type::record('memory', $id) SET note_text=$note_text, labels=$l
```
### A.3 `--tb=line` control (store-free; see Deviation)
```python
"""Control for #486's inference: what does --tb=line print for a wrapped vs a raw SDK error?"""
import pytest
from surrealdb.connections.utils_mixin import UtilsMixin
from loremaster.store._txn import SurrealStoreError

CONFLICT = {"status": "ERR", "kind": "Query",
            "result": "Transaction conflict: Resource busy: . This transaction can be retried"}

def _raw():
    UtilsMixin._check_query_result(CONFLICT)          # the utils_mixin.py:24 raise

def test_raw_escape():
    _raw()

def test_wrapped_like_run_query():
    try:
        _raw()
    except Exception as error:
        raise SurrealStoreError("SurrealDB memory query rejected (retryable conflict)") from error
```
Output (`uv run pytest -p no:cacheprovider -q --tb=line …`), both crash lines:
```
…/site-packages/surrealdb/connections/utils_mixin.py:24: surrealdb.errors.QueryError: Transaction conflict: Resource busy: . This transaction can be retried
…/tbline/test_tbline_control.py:19: loremaster.store._txn.SurrealStoreError: SurrealDB memory query rejected (retryable conflict)
2 failed in 1.69s   (both fail by design; the point is the printed crash site)
```
### A.4 Repro loop (the one test, sequential, process table clear at start)
`for i in 1..40: uv run pytest -p no:cacheprovider -q --tb=long <nodeid>` → **40/40 rc=0** (`1 passed in 0.64s` each).
This **bounds** the search: a load-free loop cannot recreate `-n 12` pressure, so a green loop neither refutes §3 nor clears the test. Per standing law, a green run never clears a concurrency failure.
### A.5 Engine flags (read live from the pinned image)
`podman run --rm docker.io/surrealdb/surrealdb:v3.2 start --help` → `--index-compaction-interval [default: 5s]`, `--async-event-interval [default: 5s]`, `--reclaim-interval [default: 60s]`; `version` → `3.2.4+20260803.93ab219`.
