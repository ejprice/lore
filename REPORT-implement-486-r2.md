brief-base v18 read · brief project v7 read

# REPORT — implement-486-r2 (tdd-light GREEN, lore #486 round 2/2b)

## SUMMARY BLOCK
- **State:** done. Measured 2026-10-04 on the uncommitted #486 working tree over HEAD `8bd7835` (HEAD moved to `2c35dd8` mid-run; that commit touches only `REPORT-contract-486-r2.md`).
- **Result:** the 8 round-2/2b reds are GREEN; 0 GREEN→RED; the outer run prints 0 `LEAKED` lines. BEFORE `8 failed, 824 passed` → AFTER `832 passed`, rc 0.
- **Deviations:** none from the brief. One interface note: the VALUE type of `_MINTED_DATABASES` changes from `str` to `(minted_by, reaped)` (§D-r2b-1). The contract's docstring prose describes the value as "the minting test's node id"; its assertion (`str(registry[db])` contains the test name) still holds.
- **Packages considered:** F3 `replace` → reused `loremaster.governed.map_of` (read its installed source via lore_get_symbol: `required=` raises on missing key, and a required key whose value is not a dict raises). F2: none, no package mechanism.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 0 new reusable symbols (no new module-level name anywhere; one local `databases_key` inside the reaper).
- **Graded:** n/a — implementation, not a verdict. HEAD-at-report `2c35dd8`.
- **Decisions needed:** none. A flag for the contract owner: the `TestTheReaperRemovesExactlyWhatThisProcessLeaked` docstring and the `test_unique_database_records…` failure message still say "dict: name -> minting test node id" (§D-r2b-1).
- **Receipts:** §Changes · §D-r2b-1 · §Counts · §Gates · diff in §Diff

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473): every text search used awk. lore_get_symbol was used for `map_of`.
- Backups taken before editing: `cp -a` of `_surreal_harness.py` (sha256 `e3561445…2fbe`) and `conftest.py` (`e9941c5e…89ba`) into the session scratchpad. These match contract-486-r2's recorded pre-reference hashes.
- Post-edit sha256: `_surreal_harness.py` `cd078f09…b00c`, `conftest.py` `83588ced…0e47`.
- No test file edited: `test_harness_database_lifecycle_486.py` `b1a6b92b…7c23` and `test_surreal_harness.py` `f884dc9c…70b7` are identical before and after.
- No git mutation and no commit. TEST store `:18000` only.

## Changes (by symbol)
### `_surreal_harness._MINTED_DATABASES`
- Type is now `dict[str, tuple[str, bool]]`: name → `(minting test node id, reaped)`.
- A reaped entry is KEPT. The comment says why: the session-end report names every leak, including one that a mid-session reaper call removed.

### `_surreal_harness.unique_database`
- Records `(PYTEST_CURRENT_TEST or "", False)`.

### `_surreal_harness.reap_minted_databases`
- **F3:** the namespace read goes through `map_of(info, noun="test-namespace reaper", required=("databases",))`, which is production's ONE fail-closed INFO reader.
  - Non-dict answers raise `SurrealStoreError`.
  - A missing `databases` key raises.
  - A non-map `databases` (list, string, None) raises.
  - The old `info.get("databases", {}) if isinstance(info, dict) else set()` coercion is gone.
  - `map_of` is imported in-function, per RULING 1. The import pin scans only import-time imports.
- **F2:** after each successful removal, the entry is re-marked `(minted_by, True)`. It is marked only AFTER the removal succeeds, so a removal that raises leaves the database present for the session-end reap.
- The return value is unchanged: the names THIS call removed. The re-keyed reaper test still reads it.
- The docstring is updated: the marking, and a new `Raises: SurrealStoreError` entry.

### `conftest.pytest_sessionfinish`
- Still runs the reaper when anything was minted.
- It now builds the report from the REGISTRY (every entry with `reaped=True`, sorted, as `(database, minted_by)`) instead of from the last reap's return.
- Attribution is therefore by minter, never by whichever test ran the reaper.
- xdist `workeroutput` / controller merge / terminal summary are unchanged.

## D-r2b-1 — where the reaped-leak record lives, and why
- **Chosen:** the state lives in the existing `_MINTED_DATABASES` values. This is the lead's first suggested option. The allowlist pin `test_the_harnesss_module_level_names_are_exactly_the_allowed_set` PASSES (confirmed by node id, §Counts).
- **Alternatives rejected:**
  - A conftest-side ledger cannot see a mid-session reaper call without either wrapping or monkeypatching `_surreal_harness.reap_minted_databases` from conftest (routing-is-not-sharing; import-binding-order fragile), or classifying `REMOVE DATABASE` SDK calls through `_sdk_guard._CALL_HOOKS`. That last option cannot tell the reaper's REMOVE from `drop_database`'s, because both go through `_remove_database_with_retry`.
  - Popping dropped names from the registry (to make "minted and never dropped" the leak set) would break `_every_database_a_test_opens_was_minted_by_the_harness`, which checks opened names against the registry at test teardown, AFTER the test's own drop.
- **Why a plain tuple and not a record type:** a NamedTuple/dataclass, or key-name constants for a dict value, would each add a module-level name, which the ruling forbids. Callers unpack the tuple, so no index literals appear.
- **Interface note (two readings, written down per brief-base §2):**
  - (i) the contract pins the value as EXACTLY a node-id string;
  - (ii) the contract pins that the value identifies the minting test.
  - Only (ii) is asserted (`str(registry[database])` contains the test name), and the lead's ruling explicitly suggested state on these entries, so I took (ii). The contract's prose ("dict: name -> minting test node id") is now stale in two places: the `TestTheReaperRemovesExactlyWhatThisProcessLeaked` class docstring and the `test_unique_database_records_the_name_and_the_minting_test` failure message. It is the contract owner's file; I did not touch it.

## Counts (targeted; same tree, same command)
- **Scope:** `test_surreal_harness.py`, `test_harness_database_lifecycle_486.py`, `test_retry_seam.py`, `test_memory_replay_fidelity_63b_ib.py`, `test_comms_wiring.py`.
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -rf …`.
- **Conditions:** MemAvailable was 22.0 GiB (BEFORE) and 21.4 GiB (AFTER). No other lore pytest was alive: the only `ps` match was this agent's own shell.

| run | result | red set |
|---|---|---|
| BEFORE | `8 failed, 824 passed, 1 warning in 34.06s`, rc 1 | F2 `[n0]`, `[xdist-n1]` + F3 `[not-a-dict-none]`, `[not-a-dict-list]`, `[not-a-dict-string]`, `[databases-key-missing]`, `[databases-a-list]`, `[databases-a-string]` |
| AFTER | `832 passed, 1 warning in 31.96s`, rc 0 | none |

- **Arithmetic:** 824 + 8 = 832, so 0 GREEN→RED.
- **Outer `LEAKED` lines:** 0 BEFORE, 0 AFTER (`awk '/LEAKED/' after.log | wc -l` → 0).
- **By-node-id confirmation:** `-rA` run, `-k "MidSessionReap or FailsLoud or ReaperRemovesExactly or module_level_names_are_exactly"` → `14 passed in 4.72s`, rc 0. All 8 BEFORE-red ids appear as PASSED (scripted check: `8 GREEN`). The run also covers:
  - both F2/F3 controls;
  - `[databases-none]`;
  - the re-keyed `test_the_reaper_removes_a_leaked_database_and_spares_a_dropped_one`;
  - `test_unique_database_records_the_name_and_the_minting_test`;
  - the allowlist pin.
- **The warning:** pre-existing (`_empty_subscription` never awaited, `test_retry_seam.py`; refactor-486 §Counts).

## Gates (2026-10-04)
- `uv run ruff check .` → `All checks passed!`.
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED`: 83 residuals, owned by packet-58-contract and packet-64b-i-contract. That is the same count contract-486-r2 recorded.
  - `ruff GREEN`.
  - `pytest NOT_RUN`: the known #533 scoped-legs line.
  - **RED_ORPHANED 0** for typecheck and ruff.
- `scripts/typecheck.sh` → 83 `error:` lines; **0 lines name `_surreal_harness.py` or `tests/conftest.py`**.

## Noticed / flags
- The contract prose is stale on the registry's value type (§D-r2b-1). This is a contract-owner edit.
- `_surreal_harness` module docstring ("Lifetime (#486)") is still accurate. It says that the session names each leak; it does not claim that only the session-end reap counts. I left it unchanged.
- The previously flagged sibling, the census oracle `_databases_in_the_test_namespace`, was hardened by contract round 2c (`2c35dd8`) via the same `map_of`. Both reads of `INFO FOR NS` now share one shape policy.

## Diff (my edits only, vs the `cp -a` backups)
```diff
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/8e68029f-068e-4f14-bdf7-66d286972de1/scratchpad/_surreal_harness.py.orig	2026-09-27 00:05:09.446511514 -0400
+++ _surreal_harness.py	2026-10-04 13:33:25.856914741 -0400
@@ -163,10 +163,14 @@
     return SecretStr(os.environ.get(_ENV_PASS, DEFAULT_PASS))
 
 
-# #486: every database name :func:`unique_database` minted in THIS process, mapped to the
-# node id of the test that minted it (``PYTEST_CURRENT_TEST`` at mint time). Mutated IN
-# PLACE, never rebound — a holder of this dict must see every later mint.
-_MINTED_DATABASES: dict[str, str] = {}
+# #486: every database name :func:`unique_database` minted in THIS process, mapped to
+# ``(minting test node id, reaped)``: the node id is ``PYTEST_CURRENT_TEST`` at mint time, and
+# ``reaped`` turns True once :func:`reap_minted_databases` removes the database as a leak. A
+# reaped entry is KEPT, never dropped, so the session-end report names every leak — including
+# one a mid-session reaper call removed (contract-486-r2 F2; lead ruling D-r2b-1 keeps that
+# state here rather than in a new module-level name). Mutated IN PLACE, never rebound — a
+# holder of this dict must see every later mint.
+_MINTED_DATABASES: dict[str, tuple[str, bool]] = {}
 
 
 def unique_database() -> str:
@@ -184,7 +188,7 @@
     name = f"test_{os.getpid()}_{uuid.uuid4().hex}"
     # ``PYTEST_CURRENT_TEST`` is pytest's own "<nodeid> (<phase>)" marker; absent outside a
     # test (a session hook, a plain import), where the empty string attributes to nobody.
-    _MINTED_DATABASES[name] = os.environ.get("PYTEST_CURRENT_TEST", "")
+    _MINTED_DATABASES[name] = (os.environ.get("PYTEST_CURRENT_TEST", ""), False)
     return name
 
 
@@ -875,14 +879,25 @@
     left alone. Every engine call rides :func:`_run_under_store_retry_seam`, exactly as
     :func:`drop_database`'s teardown does.
 
+    Every database it removes is also marked ``reaped`` in :data:`_MINTED_DATABASES`, so the
+    session-end report names it and its minting test whoever called this, and whenever: a
+    mid-session call can never swallow a leak (contract-486-r2 F2).
+
     Returns:
-        The names of the databases it removed. Each one is a leak: its test minted it and
-        never dropped it. A database its test already dropped is never returned.
+        The names of the databases THIS call removed. Each one is a leak: its test minted it
+        and never dropped it. A database its test already dropped is never returned.
 
     Raises:
+        SurrealStoreError: If the ``INFO FOR NS`` answer is not a map with a ``databases``
+            map — the present set cannot be read, so the reaper fails closed rather than
+            answering "nothing leaked" (contract-486-r2 F3).
         TxnContentionExhaustedError: If the engine keeps reporting a retryable conflict on
             one of the removals past the seam's budget.
     """
+    # In-function, per RULING 1 (operator, 2026-07-20): no module-level loremaster import
+    # beyond ``loremaster.index.records`` — see test_surreal_harness.py's import pin.
+    from loremaster.governed import map_of
+
     # A snapshot: minting the reader below records into the live registry mid-iteration.
     candidates = set(_MINTED_DATABASES)
     if not candidates:
@@ -894,10 +909,18 @@
     connection = await connect_admin(reader_env)
     try:
         info = await run(connection, "INFO FOR NS")
-        present = set(info.get("databases", {})) if isinstance(info, dict) else set()
+        # Production's ONE fail-closed INFO reader: a wrong-shaped answer raises instead of
+        # reading as an empty namespace, which would be a false "nothing leaked".
+        databases_key = "databases"
+        namespace = map_of(info, noun="test-namespace reaper", required=(databases_key,))
+        present = set(namespace[databases_key])
         leaked = tuple(sorted(candidates & present))
         for database in leaked:
             await _remove_database_with_retry(connection, database, url=reader_env.url)
+            # Marked only once removed: a removal that raised leaves the database present,
+            # for the session-end reap to find again.
+            minted_by, _already_reaped = _MINTED_DATABASES[database]
+            _MINTED_DATABASES[database] = (minted_by, True)
     finally:
         await connection.close()
         await drop_database(reader_env)
--- /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/8e68029f-068e-4f14-bdf7-66d286972de1/scratchpad/conftest.py.orig	2026-10-04 13:10:57.354713038 -0400
+++ conftest.py	2026-10-04 13:33:25.856914741 -0400
@@ -322,9 +322,13 @@
     """
     from _surreal_harness import _MINTED_DATABASES, reap_minted_databases
 
-    minted_by = dict(_MINTED_DATABASES)
-    leaked = tuple(asyncio.run(reap_minted_databases())) if minted_by else ()
-    report = [(database, minted_by.get(database, "")) for database in leaked]
+    if _MINTED_DATABASES:
+        asyncio.run(reap_minted_databases())
+    # Report from the registry, not from this last reap's return: a leak a mid-session reaper
+    # call already removed is marked reaped there and must still be named (contract-486-r2 F2).
+    report = sorted(
+        (database, minted_by) for database, (minted_by, reaped) in _MINTED_DATABASES.items() if reaped
+    )
     workeroutput = getattr(session.config, "workeroutput", None)
     if workeroutput is not None:
         workeroutput[_LEAK_REPORT_WORKEROUTPUT_KEY] = json.dumps(report)
```
