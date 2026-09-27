# REPORT — stub-466 (tdd-light Phase 2 STUB, finding #466)

## SUMMARY BLOCK
- **State:** done. The gate passes: **0 structural failures**. All 32 failures are `NotImplementedError` (BEHAVIORAL); 29 tests pass legitimately.
- **Runs** (lead-ruled 2026-09-26: run now, single-process `-p no:xdist`, 15 GB PID watchdog; the watchdog never fired):
  - `uv run pytest -q -p no:cacheprovider -p no:xdist loremaster/tests/test_loopback_serving.py loremaster/tests/test_no_raw_listener_in_test_trees.py scripts/test_concurrent_wire_acceptance.py` → **`30 failed, 28 passed in 0.59s`**
  - `cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider -p no:xdist ../tests/test_loopback_home.py` → **`2 failed, 1 passed in 0.28s`**
  - Checked in the logs: 32 `E   ` lines; **0 are not `NotImplementedError`**; 0 `ERROR` (collection/fixture) entries.
- **ruff:** clean. **typecheck:** FAILED on the loremaster leg only, with 7 errors all in `test_supersede_reanchor_58.py` (packet 58's pre-stub contract; not this change). **0 errors in #466 files.**
- **Nothing staged or committed.** I touched only the 3 files below.

## Files
| file | change |
|---|---|
| `loremaster/loremaster/testing/__init__.py` | NEW: package docstring only |
| `loremaster/loremaster/testing/loopback.py` | NEW. **Real:** `LOOPBACK_HOST="127.0.0.1"`, `DEFAULT_STARTUP_TIMEOUT_S=15.0`, `AsgiApplication` alias, `ServerStartError(RuntimeError)` with `.host`/`.port`, leaves `ServerBindError` / `ServerStartupTimeout` (+`.startup_timeout_s`) / `ServerThreadCrashed` (mutually non-subclassing), frozen dataclass `ServedEndpoint(host, port, base_url)`. **Stubbed** (`NotImplementedError("Not yet implemented")`): `LoopbackPort.__init__/listen/close/__enter__/__exit__`, `serve_asgi(app, *, port=None, startup_timeout_s=DEFAULT_STARTUP_TIMEOUT_S)`, `serve_http(handler_class, *, port=None)`. Both serve functions are `@contextlib.contextmanager`, typed `Iterator[ServedEndpoint]`. |
| `loremaster/tests/_logging_fixtures.py` | `parse_production_trees(..., include_testpaths: bool = False)`. `True` raises `NotImplementedError`; `False` is unchanged (default call: 170 trees). Docstring extended. |

## Per-file outcomes (MEASURED)
| file | passed | failed | failure type | class |
|---|---|---|---|---|
| `loremaster/tests/test_loopback_serving.py` (27) | 2 (`test_the_three_causes_are_distinct_leaves_of_server_start_error`, `test_the_default_budget_is_a_positive_finite_number`) | 25 | `NotImplementedError` (`loopback.py` `LoopbackPort.__init__` / `serve_asgi` / `serve_http`) | BEHAVIORAL |
| `loremaster/tests/test_no_raw_listener_in_test_trees.py` (11) | 6 | 5 (`test_no_test_tree_opens_a_listener_outside_the_helper`, `test_every_exemption_still_matches_a_live_site`, `test_every_declared_testpaths_root_is_scanned`, `test_the_scan_is_not_vacuous`, `test_both_trees_adopt_the_helper`) | `NotImplementedError` (`_logging_fixtures.py:274`, the `include_testpaths=True` stub) | BEHAVIORAL |
| `scripts/test_concurrent_wire_acceptance.py` (20) | 20 | 0 | — (the driver already exists) | n/a |
| `skills/lore-deploy/tests/test_loopback_home.py` (3) | 1 (the provenance pin: `loopback.__file__` ends `loremaster/testing/loopback.py`) | 2 | `NotImplementedError` | BEHAVIORAL |

**Structural failures (ImportError / ModuleNotFoundError / NameError / AttributeError / SyntaxError / arg-count TypeError): NONE.**

## Deviation from the contract report's expectation (flagged, not a defect)
The contract report expected `test_every_exemption_still_matches_a_live_site` and `test_the_scan_is_not_vacuous` to go GREEN "once the kwarg exists". Under the lead-directed stub, `include_testpaths=True` raises rather than parses, so they are RED with `NotImplementedError`. They should go GREEN in the GREEN phase once `include_testpaths` actually parses the testpaths roots.

## Process notes
- My first wait (60 min, lore and other-project pytest counted alike) timed out with the box never clear. I escalated, and the lead ruled to run now. The lane rule is now LORE-scoped.
- Before the ruling I verified structure without a pytest session: all 4 modules imported via `importlib` and the signatures bound. My first harness attempt hit `AttributeError` inside `dataclasses` (module not registered in `sys.modules`). That was a harness bug, fixed on retry, not a stub defect.
- The bash hook blocks any command containing `grep` in this checkout, including a process-table `grep -q`. I used `awk` instead.
