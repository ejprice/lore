brief-base v18 read
- **State:** done (not committed; the brief says not to).
- **Deviations:**
  - Both stale sites are in ONE file, `test_harness_database_lifecycle_486.py`, so the "two files' tests" run covered that one file. The sweep found no other stale site.
  - The failure message is an `assert` message, not a docstring. "AST with docstrings blanked" alone therefore cannot be equal, so the instrument also blanks `Assert.msg` (§AST receipt).
- **Packages considered:** none — no mechanism specified (stdlib `ast` instrument only, pasted in §AST receipt).
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** none
- **Graded:** n/a — prose edit, not a verdict. HEAD-at-report `ea0e836`. The edited file is untracked #486 work.
- **Decisions needed:** none
- **Receipts:** §Edits · §Sweep · §AST receipt · §Counts

## Edits (`loremaster/tests/test_harness_database_lifecycle_486.py`, measured 2026-10-04 at `ea0e836`)
- **Backup:** `cp -a` to the session scratchpad (`prose-486/`) before editing.
  - Pre-edit sha256: `b1a6b92b…7c23` (this matches implement-486-r2's recorded hash).
  - Post-edit sha256: `41763a29…b6b4`.
- **`TestTheReaperRemovesExactlyWhatThisProcessLeaked` class docstring:**
  - The value is now described as `(minted_by, reaped)`.
  - `minted_by` = the minting test's node id, read from `PYTEST_CURRENT_TEST`. `reaped` turns True once the reaper removes the database as a leak (lead ruling D-r2b-1).
  - The reaper "marks each one reaped" and still returns the names it removed.
- **`test_unique_database_records_the_name_and_the_minting_test` failure message:** `(dict: name -> minting test node id)` became `(dict: name -> (minting test node id, reaped))`. The string was re-split across implicit concatenation to fit the line length. The assertion is unchanged.

```diff
-    ``_surreal_harness._MINTED_DATABASES`` (a ``dict`` of name -> the minting test's node id, read
-    from ``PYTEST_CURRENT_TEST`` at mint time); ``await reap_minted_databases()`` removes every
-    recorded database still present in the test namespace and returns the names it removed.
+    ``_surreal_harness._MINTED_DATABASES`` (a ``dict`` of name -> ``(minted_by, reaped)``:
+    ``minted_by`` is the minting test's node id, read from ``PYTEST_CURRENT_TEST`` at mint time,
+    and ``reaped`` turns True once the reaper removes the database as a leak — lead ruling
+    D-r2b-1); ``await reap_minted_databases()`` removes every recorded database still present in
+    the test namespace, marks each one reaped, and returns the names it removed.
...
-            "`_surreal_harness._MINTED_DATABASES` (dict: name -> minting test node id) is missing — "
+            "`_surreal_harness._MINTED_DATABASES` (dict: name -> (minting test node id, reaped)) is "
+            "missing — "
```

## Sweep
- **Method:** a bare awk over every `*.py` under `loremaster/tests` for `node id|name -> |_MINTED_DATABASES`. The sweep ran before the edit, at `ea0e836`.
- **Citation form:** line numbers are pre-edit, and the symbol is given for durability.

| file:line (pre-edit) | text | verdict |
|---|---|---|
| `_governed_contract.py:852` | `principals` maps `name -> role` | unrelated (fixture principals) |
| `_governed_contract.py:1376` | AST node id → enclosing FunctionDef | unrelated (AST node) |
| `_governed_contract.py:1391` | node ids of docstring Constants | unrelated (AST node) |
| `test_tool_allowlist.py:31` | expected-RED node id | unrelated (pytest nodeid in mutation prose) |
| `test_enforced_relations.py:1916` | `--expect-red <…node ids>` | unrelated |
| `test_extension_discovery.py:38` | expected-RED node id | unrelated |
| `test_agent_capability.py:48` | node id from `--collect-only` | unrelated |
| `_surreal_harness.py:23` | module docstring: recorded "with the test that minted it" | accurate (true of the tuple's first element; no shape claim) |
| `_surreal_harness.py:167` | comment `(minting test node id, reaped)` | accurate (new shape) |
| `_surreal_harness.py:173` | `dict[str, tuple[str, bool]]` | accurate (code) |
| `_surreal_harness.py:183` | `unique_database` docstring: "recorded … against the test minting it" | accurate (no shape claim) |
| `_surreal_harness.py:191` | `(…PYTEST_CURRENT_TEST…, False)` | accurate (code) |
| `_surreal_harness.py:876` | reaper docstring: reads the registry | accurate |
| `_surreal_harness.py:882` | reaper docstring: marks `reaped` | accurate (new shape) |
| `_surreal_harness.py:902` | `set(_MINTED_DATABASES)` | accurate (code; keys only) |
| `_surreal_harness.py:922-923` | tuple unpack / re-mark | accurate (code) |
| `test_harness_database_lifecycle_486.py:808` | class docstring "name -> the minting test's node id" | **STALE → FIXED** |
| `test_harness_database_lifecycle_486.py:813` | test name | accurate (name only) |
| `test_harness_database_lifecycle_486.py:815` | `getattr(…"_MINTED_DATABASES"…)` | accurate (code) |
| `test_harness_database_lifecycle_486.py:817` | message "(dict: name -> minting test node id)" | **STALE → FIXED** |
| `test_harness_database_lifecycle_486.py:824` | `in minted_by` (`str(registry[db])`) | accurate (logic; the brief forbids touching it; it holds for the tuple) |
| `test_harness_database_lifecycle_486.py:914` | `databases` a dict of `name -> definition` (INFO FOR NS) | unrelated (engine answer shape) |
| `test_floor_calibration_store.py:303` | node ids do not COLLECT | unrelated |
| `test_floor_calibration_store.py:1218` | parametrised node id | unrelated |
| `test_surreal_fakes.py:1350` | node id set after re-upsert | unrelated (graph node) |
| `test_surreal_fakes.py:1353` | duplicate node ids | unrelated (graph node) |
| `test_store_lease.py:524` | node ids do not COLLECT | unrelated |
| `test_secret_typing.py:670` | declared-RED node ids | unrelated |
| `test_secret_resolution_seam.py:1247` | declared-RED node ids | unrelated |
| `test_blocks_edge.py:8597` | parametrisation id → node id | unrelated |
| `test_blocks_edge.py:8963` | node id from `--collect-only` | unrelated |
| `test_blocks_edge.py:9159` | only the node id moved | unrelated |
| `conftest.py:300` | import `_MINTED_DATABASES` | accurate (code) |
| `conftest.py:304` | membership over keys | accurate (code; keys only) |
| `conftest.py:323` | import | accurate (code) |
| `conftest.py:325` | truthiness | accurate (code) |
| `conftest.py:330` | `(database, minted_by) for database, (minted_by, reaped) …` | accurate (new shape) |
| `_surreal_fakes.py:1430` | deduplicated by node id | unrelated (graph node) |
| `_comms_fakes.py:233` | `name -> row` resolution | unrelated (comms) |
| `test_surreal_harness.py:1733` | allowlist entry; comment at 1729-1732 "per-process record of every database name" | accurate (no value-shape claim) |
| `test_retry_seam.py:1885` | inline lambda node ids | unrelated (AST) |
| `test_retry_seam.py:6120` | three node ids | unrelated |
| `test_retry_seam.py:7356` | `local name -> bound name` | unrelated (import bindings) |
| `test_link5_render_containment.py:1142` | node id skipped | unrelated (AST) |

## AST receipt
- **Instrument:** pasted verbatim below. It ran from the scratchpad, `prose-486/ast_prose_only.py`.
- **Real edit (backup vs edited):**
  - docstrings blanked: `False`. This is expected, because an `assert` message changed.
  - docstrings and `Assert.msg` blanked: **`True`**.
- **Positive control:** the edited file with `assert database in registry` changed to `assert database not in registry`. Both comparisons gave `False`, so the instrument sees a one-token logic change.
- **Identity control** (backup vs itself): `True` / `True`.

```python
"""Prove an edit is prose-only: AST equality after blanking docstrings and assert messages."""
import ast, sys

class _Blank(ast.NodeTransformer):
    def __init__(self, blank_msgs: bool) -> None:
        self.blank_msgs = blank_msgs
    def _strip_doc(self, node):
        self.generic_visit(node)
        body = getattr(node, "body", None)
        if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) and isinstance(body[0].value.value, str):
            body[0] = ast.Expr(ast.Constant(""))
        return node
    visit_Module = visit_ClassDef = visit_FunctionDef = visit_AsyncFunctionDef = _strip_doc
    def visit_Assert(self, node):
        self.generic_visit(node)
        if self.blank_msgs and node.msg is not None:
            node.msg = ast.Constant("")
        return node

def dump(path: str, blank_msgs: bool) -> str:
    tree = ast.parse(open(path, encoding="utf-8").read())
    return ast.dump(_Blank(blank_msgs).visit(tree))

before, after = sys.argv[1], sys.argv[2]
print("docstrings-blanked equal:", dump(before, False) == dump(after, False))
print("docstrings+assert-msgs-blanked equal:", dump(before, True) == dump(after, True))
```

## Counts (2026-10-04, post-edit, at `ea0e836` plus the uncommitted #486 tree)
- **Preconditions:** MemAvailable was 24.4 GiB before the run and 20.8 GiB after. No other pytest process was in `ps`.
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q loremaster/tests/test_harness_database_lifecycle_486.py`
- **Result:** `41 passed in 7.96s`, rc 0.
- **ruff:** `uv run ruff check .` gave `All checks passed!`, rc 0.
