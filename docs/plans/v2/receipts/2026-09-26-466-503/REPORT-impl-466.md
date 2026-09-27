# REPORT — impl-466 (tdd-light Phase 4 GREEN, finding #466)

## SUMMARY BLOCK
- **State:** done-with-deviations. Every #466 contract test is green. 3 reds remain in the verify set, all in files owned by other agents (see "Remaining reds"). Nothing is staged or committed.
- **Files changed (mine only):**
  - `loremaster/loremaster/testing/loopback.py`: the real implementation.
  - `loremaster/tests/_logging_fixtures.py`: `parse_production_trees(include_testpaths=)`, plus `_declared_testpaths()`.
  - `loremaster/tests/test_migration_wire.py`: `_free_port`/`_serve` → `serve_asgi`.
  - `skills/lore-deploy/tests/test_port_probe.py`: `_free_port`/`_start_stub_server` → `LoopbackPort`/`serve_http`.
  - `skills/lore-deploy/tests/test_workspace_probe.py`: `_dead_port` → a held-unlistened `dead_port` fixture; `_StubMCPServer` → `serve_http`.
  - `scripts/fastmcp_migration_spike.py`: ROUTE onto `serve_asgi`/`LoopbackPort`.
  - `scripts/concurrent_wire_acceptance.py`: `.match` → `.fullmatch`.
- **No assertion was edited.**

## Implementation notes
- **uvicorn 0.48.0** runs as `Server.run(sockets=[held.socket])`, with `lifespan="on"` and `log_level="error"` (adjudication #9: kept, not pinned).
- **Deviation D1: `log_config=None`.** Without it, uvicorn's default `dictConfig` resets the process-global `uvicorn.error` handlers on every `Config()`. That would strip a concurrent server's crash capture.
- **Crash text.** A failed lifespan startup ends uvicorn's thread NORMALLY: nothing is raised, and the cause exists only as `uvicorn.error` ERROR records. The helper captures those records per thread with a handler filtered by `record.thread`. The crash is named within one 20 ms poll of thread death (via `join(timeout=)`).
- **Timeout and crash paths** close the held socket at the raise and never join the stuck thread.
- **stdlib half.** `HTTPServer(..., bind_and_activate=False)`, then its own unbound socket is swapped for the held one, then `server_activate()`.
- **Ownership.** A passed port is not closed by `serve_http`; the caller closes it. uvicorn itself closes a served socket on shutdown.
- **D2.** `test_port_probe.py`'s module docstring said to run it with a bare system interpreter. That became false once the file imports `loremaster.testing`, so I corrected it to the skill idiom.
- **D3.** The spike's docstring claimed "Nothing under loremaster/ … is imported". Updated to name the helper import. Its 10 s budget is kept as `_STARTUP_TIMEOUT_S`.
- **D4.** The three `_dead_port()` tests gained a `dead_port: int` fixture parameter. The signatures changed; the assertions did not.

## Receipts
Lore verify set: `-p no:xdist`, run after confirming no other lore pytest was live.
```
FAILED loremaster/tests/test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted
FAILED loremaster/tests/test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
FAILED loremaster/tests/test_ast_reach_helpers.py::TestSharingProvenByMutation::test_each_real_fixture_consumer_reddens_when_the_shared_parser_is_dropped[test_anchored_pattern_seam.py]
3 failed, 144 passed, 4 skipped, 2 warnings in 121.69s (0:02:01)
```
Skill idiom:
- `120 passed in 17.27s`
- Migrated files alone (`test_loopback_home`, `test_port_probe`, `test_workspace_probe`): `53 passed in 13.25s`

Lint and types:
- ruff on the 7 changed files: `All checks passed!`
- `./scripts/typecheck.sh`: every leg OK except loremaster, which has 7 errors, all in `test_supersede_reanchor_58.py` (packet 58's contract, expected).

## Remaining reds — NOT mine, need an owner
1. `test_anchored_pattern_seam`: 5 offenders, all in `scripts/restore_prod_dump.py`. The brief says another agent owns that file, so I did not touch it. `concurrent_wire_acceptance.py` is no longer listed.
2. `test_ast_reach_helpers::…whole_tree_parser_clone…`: hand-rolled whole-tree parses in `test_findings_identity_64b.py::_routing_markers` and `test_governed_substrate_64b.py::_resource_construction_sites`. These are untracked packet-64b contract files from another agent.
3. `test_ast_reach_helpers::…SharingProvenByMutation[test_anchored_pattern_seam.py]`: a downstream effect of #1. Its positive control fails because the seam consumer is already red on the real tree.

## Not done
- The 20-round acceptance driver run (`scripts/concurrent_wire_acceptance.py`) was not run. It was not in the brief's verify list, and it needs an exclusive window for 2×`-n 4` sessions.
