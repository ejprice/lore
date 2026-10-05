# REPORT-fix531 — #531: the landed shape-fault text no longer claims "a re-run is idempotent"

brief-base v18 read
- **State:** done. Fix commit `f47724ae1932db53358d97bb1b8bc6684a2fb9fe` (2 files, +2/−2). #531 resolved by `fix531`.
- **Deviations:** none. One caveat: the "HEAD" baseline ran on HEAD `64805e5` *plus* the tree's uncommitted #486 WIP (not mine, not touched). The fix run used the same tree, so the only delta is my two files.
- **Packages considered:** none. No mechanism was specified; this is a one-clause string change.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. No new symbols.
- **Graded:** n/a. No verdict on anyone else's artifact.
- **Capability check:** every demand in the brief was satisfiable. grep/rg are hook-blocked, so the sweep used an AST classifier plus awk (§4 below; no lore tool does a bare textual sweep, CLAUDE.md dogfood case b).
- **Decisions-needed:** none. One residual for the operator is in §5: the orphaned-key case on a landed `mint`.
- **Receipts:** §1 RED/GREEN · §2 targeted counts · §3 gates · §4 sweep table + instrument · §5 residuals.

## 0. The change
`loremaster/loremaster/governed.py::_LANDED_SHAPE_FAULT` and its byte-exact pin
`loremaster/tests/test_am37_13_3_63c_i_a.py::_LANDED_TEMPLATE` now read:
`"the {noun} LANDED (committed) but answered a {type} instead of its rows — nothing was decided from the answer; verify the stored state before re-running"`.
The old clause `a re-run is idempotent` was false for the `PrincipalStore.create` and `PrincipalKeyStore.mint` landed sinks, where a re-run collides with the landed row. The new clause holds for every `landed=True` sink.

## 1. TDD — pin first, then RED, then GREEN (measured 2026-10-04, pre-commit tree on `64805e5`)
Order: pin edited → RED → `governed.py` edited → GREEN.
RED (`-k landed_template`), failing because the text differs and for no other reason:
```
E         - e answer; verify the stored state before re-running
E         + e answer; a re-run is idempotent
FAILED ...::TestEveryPostWriteShapeReadSaysItLanded::test_the_one_landed_template[str]
FAILED ...::TestEveryPostWriteShapeReadSaysItLanded::test_the_one_landed_template[None]
FAILED ...::TestEveryPostWriteShapeReadSaysItLanded::test_the_one_landed_template[dict]
3 failed, 88 deselected in 1.93s
```
GREEN, after the `governed.py` edit:
```
3 passed, 88 deselected in 1.84s
```

## 2. Targeted set, before vs after
Files: `test_am37_13_3_63c_i_a.py`, `test_fail_closed_shapes_63c_13b.py`, `test_principals_cli.py`, `test_engine_rejection_seam.py`.
Each run was gated on MemAvailable ≥ 20 GiB with no other lore pytest live. Both ran under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300`.
Before the edit (recorded before any change):
```
.........                                                                [100%]
513 passed in 18.29s
EXIT=0
```
After the fix:
```
.........                                                                [100%]
513 passed in 18.28s
EXIT=0
```
The counts are identical (513 / 0 failed), so no owned-residual failures appear in this set.

## 3. Gates (post-fix, pre-commit)
- `uv run ruff check .` → `All checks passed!`
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff`:
  - `typecheck RED_ADJUDICATED — 83 residual(s)`, owned by `packet-58-contract` · `packet-64b-i-contract`
  - `ruff GREEN`
  - **RED_ORPHANED: 0**
  - It also prints `pytest NOT_RUN` / `CURRENCY: FAIL — claimed but never run: pytest`. That is the pytest leg, which `--legs typecheck,ruff` excludes by design (CLAUDE.md TEST SCOPE). It is not an orphaned red.
  - I did not measure HEAD's residual count of 83 separately. The change is a single str constant, so it cannot introduce a type error.

## 4. Bare sweep for `idempotent` over `loremaster/`, `scripts/`, `docs/reference/` (post-fix)
- **Result:** 346 hits, case-insensitive, no anchors.
  - By kind: DOCSTRING 183 · COMMENT 133 · STRLIT 28 · DOC 2.
  - 30 hits also mention a re-run.
  - `docs/reference/` has 0 hits. `governed.py` has 0, since the fixed constant is gone.
- **Verdict:** no OTHER served text makes the #531 claim, so nothing else was edited.
- **Served strings in production code:** three, each read and judged TRUE.
- **Test-tree string literals:** 25. These are test text, not served.
- **Instrument:** pasted verbatim below (§4.1). It has a bound: it decides "served" syntactically (a non-docstring str literal). A docstring that a framework serves would be missed.
  - MEDIUM: `server.py` passes tool and argument descriptions as explicit `description=` strings (seen at the `lore_comms` registration), so the docstrings there are not what is served. I did not verify this for every tool.

| hit | kind | verdict |
|---|---|---|
| `loremaster/loremaster/agents.py:4` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/agents.py:346` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/agents.py:349` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/agents.py:456` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/agents.py:548` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/agents.py:818` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/agents.py:822` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/audit.py:177` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/briefs.py:7` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:44` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:305` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:485` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:903` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:934` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:967` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:977` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:986` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/briefs.py:1007` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/calibration/corpus/dense_python.py.txt:205` | DOC | calibration corpus fixture text — not served; not a landed-write claim |
| `loremaster/loremaster/calibration/corpus/markdown_prose.md.txt:92` | DOC | calibration corpus fixture text — not served; not a landed-write claim |
| `loremaster/loremaster/calibration/engine.py:270` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/calibration/engine.py:281` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/diff.py:564` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/extension.py:229` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/extension.py:239` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/findings.py:482` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/floor_calibration/store.py:293` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/graph_surreal.py:23` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/graph_surreal.py:27` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/graph_surreal.py:441` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/graph_surreal.py:445` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/inbox_awaiter.py:19` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/index/records.py:20` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/index/snapshots.py:296` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/index/snapshots.py:520` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/index/snapshots.py:530` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/index/snapshots.py:540` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/index/sqlite_resilient.py:210` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/index/sqlite_resilient.py:287` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/index/surreal_manifest.py:225` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/index/surreal_manifest.py:684` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/keeps.py:266` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/keeps.py:527` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/keeps.py:654` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/keeps.py:681` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/keeps.py:706` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/logging_setup.py:52` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/logging_setup.py:450` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/logging_setup.py:637` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/logging_setup.py:656` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/backend.py:327` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/backend.py:426` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/ledger.py:12` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/ledger.py:29` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/ledger.py:133` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/memory/local.py:410` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/memory/local.py:978` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/memory/local.py:1392` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/messages.py:147` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/messages.py:352` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/messages.py:586` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/messages.py:1445` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principal_keys.py:287` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/principals.py:381` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/principals.py:640` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:1132` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/principals.py:1140` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/principals.py:1350` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:1491` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/principals.py:1523` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:2245` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:2254` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:2493` | STRLIT | SERVED (lore-adm CLI help) — TRUE: add_household_member is check-first, re-add returns the existing edge (keeps.KeepStore.add_household_member). Not this class. |
| `loremaster/loremaster/principals.py:2528` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:2675` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/principals.py:2858` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/scout.py:409` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/scout.py:581` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/scout.py:629` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/scout.py:951` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:1023` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:2217` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:6693` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:6705` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:6767` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:6814` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:6830` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:8202` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:9074` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:9083` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:9094` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:9106` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:9397` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/server.py:9411` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/server.py:9474` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:10028` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:10106` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:10123` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11024` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11085` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11090` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11093` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11096` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11099` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11104` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11109` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11113` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11115` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11120` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11123` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11127` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11128` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:11132` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/server.py:12160` | STRLIT | SERVED (lore_comms tool description) — TRUE: register is a designed idempotent re-register (agents.py register). Not a landed-write re-run claim. |
| `loremaster/loremaster/server.py:12186` | STRLIT | SERVED (lore_comms action Field description) — TRUE, same as above. |
| `loremaster/loremaster/source/local_directory.py:52` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/lease.py:383` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/store/surreal.py:534` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/store/surreal.py:1045` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal.py:1210` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:12` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:623` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:675` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1012` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1052` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1066` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1070` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1077` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1136` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1239` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1260` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1688` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1880` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1884` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1938` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1961` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:1989` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2013` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2035` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2104` | DOCSTRING+RERUN | not served (docstring). True as stated (IF NOT EXISTS re-apply is a no-op) but #107-adjacent: no-op also means it never migrates. OBSERVATION only, not edited. |
| `loremaster/loremaster/store/surreal_schema.py:2134` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2431` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2456` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2481` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2498` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/store/surreal_schema.py:2508` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/tasks.py:865` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `loremaster/loremaster/tasks.py:928` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |
| `loremaster/loremaster/token_verifier.py:485` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `loremaster/tests/_comms_fakes.py:898` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_comms_fakes.py:910` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_comms_fakes.py:1100` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_governed_contract.py:15` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_governed_contract.py:612` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_governed_contract.py:1833` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_governed_contract_64.py:404` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_governed_contract_64.py:691` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/_ingest_entity_fixtures.py:227` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/conftest.py:285` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_capability.py:472` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_governance_63c_i_a.py:1423` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_governance_63c_i_a.py:1424` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_governance_63c_i_a.py:1425` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_governance_63c_i_a.py:1433` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_governance_63c_i_a.py:1750` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_registry.py:268` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_agent_registry.py:537` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:84` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:1140` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:5885` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:6592` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:8831` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_blocks_edge.py:9010` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_brief_ledger.py:37` | DOCSTRING+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_brief_ledger.py:483` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_brief_ledger.py:533` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_brief_ledger.py:1009` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_calibration_engine.py:925` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_await.py:8` | DOCSTRING+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_await.py:591` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_await.py:629` | STRLIT+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_promise_registry.py:377` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_promise_registry.py:482` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_read_governance_63b_ii_b.py:433` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_read_governance_63b_ii_b.py:469` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_read_governance_63b_ii_b.py:522` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_read_governance_63b_ii_b.py:554` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_read_governance_63b_ii_b.py:597` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_register_notice.py:9` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_register_notice.py:361` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_render_architecture.py:746` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:501` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:798` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:799` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:811` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:1093` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:1122` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:1132` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:1605` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:2540` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:2570` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:3169` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_schema.py:3586` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_send_scope_63b_ii_a.py:304` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_send_scope_63b_ii_a.py:317` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:352` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:691` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:707` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:1585` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:2163` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:2223` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:2245` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:2319` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:2406` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_tool.py:3488` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_wiring.py:757` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_wiring.py:852` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_wiring.py:976` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_comms_wiring.py:978` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_derivation_source_unification.py:381` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_eager_startup_survives_unparseable_file.py:186` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:534` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1185` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1278` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1316` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1320` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1350` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1780` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_enforced_relations.py:1787` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_engine_rejection_seam.py:323` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_extension.py:665` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_findings_migrate_64b.py:10` | DOCSTRING+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_findings_migrate_64b.py:375` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a19_63c_i_a.py:125` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a19b_63c_i_a.py:552` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a28_63c_i_a.py:403` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a28_63c_i_a.py:410` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a28_63c_i_a.py:837` | DOCSTRING+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_fixwave_a28_63c_i_a.py:865` | STRLIT+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:7` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:10` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:68` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:160` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:164` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:166` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:189` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_migration_63a.py:197` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_substrate_63a.py:73` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_substrate_63a.py:369` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_governed_substrate_64b.py:167` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:31` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:675` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:698` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:700` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:2464` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_graph_surreal.py:2466` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keep_remediation_store_61.py:261` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_cli.py:25` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_cli.py:502` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_schema.py:1178` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:14` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:374` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:391` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:520` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:521` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:523` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_keeps_store.py:536` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_logging_setup.py:35` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_logging_setup.py:783` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_logging_setup.py:818` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_logging_setup.py:825` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_mcp_server.py:568` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_mcp_server.py:1821` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_mcp_server.py:1854` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_mcp_server.py:1856` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_backend.py:625` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_backend.py:1370` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_backend.py:1992` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_enforcement_63b_ia.py:296` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_enforcement_63b_ia.py:371` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_ledger.py:206` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_memory_supersede_atomicity_63b_ib.py:142` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_enforcement_63b_ii_a.py:237` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_ledger.py:1416` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_ledger.py:1685` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_ledger.py:1881` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_ledger.py:1955` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:115` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:353` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:372` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:435` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:490` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_63b_ii_a.py:546` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_dirty_store_63b_ii_b.py:239` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_dirty_store_63b_ii_b.py:243` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_message_migrate_dirty_store_63b_ii_b.py:258` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_mutating_set_derivation.py:259` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_preboot_schema_precondition_63c_13d.py:10` | DOCSTRING+RERUN | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_principals_store.py:331` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_principals_store.py:335` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_reanchor_58_r3_cas_seam.py:555` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_resilient_db.py:5` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:1770` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:1843` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:2842` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:3942` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:3958` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:4090` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:4143` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:4169` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:4176` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:4194` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:6804` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_retry_seam.py:7028` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_scout.py:868` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_secret_leak_vectors.py:27` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_secret_leak_vectors.py:698` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_snapshots.py:51` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_snapshots.py:825` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_source.py:303` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:1` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:390` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:1106` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:1108` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:1125` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_startup_divergence_reconcile.py:1187` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_supersede_reanchor_58.py:752` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_supersede_reanchor_58.py:816` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_fakes.py:1299` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_fakes.py:1301` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_manifest.py:55` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_manifest.py:290` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:14` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:538` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:550` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:570` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:573` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_schema.py:595` | STRLIT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_store.py:264` | DOCSTRING | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_store.py:273` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_store.py:296` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_surreal_store.py:5199` | COMMENT | test text/comment — not served; not a landed-write claim |
| `loremaster/tests/test_wire_isolation_63a.py:118` | COMMENT | test text/comment — not served; not a landed-write claim |
| `scripts/probe_member_of_cascade.py:173` | COMMENT | not served (comment) — not a landed-write re-run claim |
| `scripts/probe_read_filter_63.py:52` | DOCSTRING+RERUN | not served (docstring) — schema/backfill/poll re-run claim, unrelated to the landed-write template |
| `scripts/probe_read_filter_63.py:352` | DOCSTRING | not served (docstring) — not a landed-write re-run claim |

### 4.1 The instrument (verbatim; run from the repo root as `uv run python sweep.py`)
```python
"""Bare sweep for 'idempotent' (case-insensitive) over loremaster/, scripts/, docs/reference/.
Every hit line is classified: STRLIT (inside a non-docstring str literal — the servable population),
DOCSTRING, COMMENT, or DOC (non-.py file). STRLIT/DOCSTRING hits also flag RERUN if the same literal
mentions re-run/rerun/run again."""
import ast, pathlib, re, sys
ROOTS = ["loremaster", "scripts", "docs/reference"]
WORD = re.compile(r"idempotent", re.I)
RERUN = re.compile(r"re-?run|run again|retry", re.I)
rows = []
for root in ROOTS:
    for p in sorted(pathlib.Path(root).rglob("*")):
        if not p.is_file() or ".venv" in p.parts or "__pycache__" in p.parts:
            continue
        try:
            text = p.read_text()
        except (UnicodeDecodeError, OSError):
            continue
        lines = text.splitlines()
        hits = [i + 1 for i, l in enumerate(lines) if WORD.search(l)]
        if not hits:
            continue
        if p.suffix != ".py":
            rows += [(str(p), h, "DOC", "") for h in hits]
            continue
        doc_spans, str_spans = [], []
        tree = ast.parse(text)
        docnodes = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
                first = node.body[0]
                if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str):
                    docnodes.add(id(first.value))
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and WORD.search(node.value):
                span = (node.lineno, node.end_lineno, node.value)
                (doc_spans if id(node) in docnodes else str_spans).append(span)
        for h in hits:
            kind, flag = "COMMENT", ""
            for a, b, v in str_spans:
                if a <= h <= b:
                    kind, flag = "STRLIT", ("RERUN" if RERUN.search(v) else ""); break
            else:
                for a, b, v in doc_spans:
                    if a <= h <= b:
                        kind, flag = "DOCSTRING", ("RERUN" if RERUN.search(v) else ""); break
            rows.append((str(p), h, kind, flag))
for r in rows:
    print(f"{r[0]}:{r[1]}\t{r[2]}\t{r[3]}")
from collections import Counter
print("TOTAL", len(rows), dict(Counter(r[2] for r in rows)), "RERUN", sum(1 for r in rows if r[3]), file=sys.stderr)
```

## 5. Residuals and observations (surfaced, not acted on — the operator decides)
1. **Orphaned key after a landed `mint`.** #531's body notes that a `mint` which lands and then faults on shape leaves a key whose secret was never printed. The new text tells the operator to verify the stored state, but it does not say "revoke the unprinted key".
   - The finding proposed two other fix shapes: per-sink wording (an `idempotent: bool` on the call, or two templates). The brief ruled the single truthful clause instead.
   - If the operator wants mint-specific guidance, that is a follow-up.
   - Reachability per #531: near-impossible, since the engine would have to answer a committed CREATE with a non-row-list.
2. **`store/surreal_schema.py:2104`** (docstring, not served): "Every statement is idempotent (`IF NOT EXISTS` …)". This is true as written, but it is the #107 neighbourhood: an idempotent no-op also never migrates. It is an observation only, outside my writable set.
3. **Class lift (per the global "fix the CLASS" rule):**
   - *Property:* a fault text's safety claim holds for every write sink it is rendered for.
   - *Domain:* every `rows_of(..., landed=True)` call site, which `test_am37_13_3_63c_i_a.py`'s `_landed_population` already derives.
   - *How it is met:* the one shared template now makes a claim true over the whole domain ("verify the stored state"). No per-sink list is needed.
   - *No new pin:* the text is a fixed string pinned byte-exact.
