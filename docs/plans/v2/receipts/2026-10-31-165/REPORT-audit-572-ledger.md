brief-base v25 read
brief project v7 read

# REPORT — audit-572-ledger (tdd-light Phase 5 REFACTOR+AUDIT, #572 + #568 audit C1–C6, wave #165, 2026-11-01)

## Summary
- **STATE:** done. **Verdict on 7d79115: GO.** The marker-after-success rule holds on every `verb_setup` path and is mutation-proven. No defect in the graded diff blocks. Three contract gaps let a wrong build through (P-2, P-3, D-1). They are routed as PROPERTIES, not blockers.
- **Deviations:** (1) I fixed retired names `search_code`/`reindex` in SKILL.md, the same class as task 6 but outside the named lines. (2) My brief's expected count for the Sonnet sweep (110) was wrong; the real count is 106, the sweep is complete, and the same 106 appear in my own grep.
- **Packages considered:** none — no mechanism specified (docs + docstrings only; reviewed stdlib `sqlite3`/`datetime` use in the graded diff, no change).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — 0 new symbols (`lore_search` DRY check on the graded diff's new symbols: §Findings "DRY check").
- **Graded:** 7d79115 · HEAD-at-report: 7d79115 · SAME (my edits are uncommitted, on top of it).
- **Fixes made (in place, operator grant 2026-09-27 "Keep it"):** lore_deploy.py comments and docstrings only. The AST is equal to 7d79115 modulo docstrings (checked), and no runtime string changed. Also the stale-doc rewrite of SKILL.md, references/lifecycle.md and references/server-interface.md (§Task 6).
- **Routed to the contract as PROPERTIES:** P-STATUS-RUNNING (P-3 survivor) · P-SETUP-NO-CONFIG (P-2 survivor) · P-OWNER-RENDER (D-1) · P-STATE-DIR-UNCREATABLE (D-3) · P-OWNER-VALUE (tautology). §Items routed.
- **Mutation (marker-after-success):** KILLED, PROOF HELD exit 0, 4 declared reds exact, 415 passed, restored byte-exact (`gate-audit-572-mutation-marker-after-success-r2.log`). #560 recurred on r1 (annotated).
- **Gates (final, lore_deploy.py sha256 `cbbfcdf0…387a`):** skill suite 419 passed EXIT=0 · typecheck `skills OK`, 0 lore_deploy lines (EXIT=1 = the 83 adjudicated packet-58/64b-i residuals) · ruff EXIT=0 · currency RED_ORPHANED 0 (EXIT=1 = pytest NOT_RUN, #565). §Gate receipts.
- **Builder receipts:** all 4 valid by EXIT/count line; code identity checked by sha256 `ad23a318…` = `git show 7d79115:…lore_deploy.py` (the TREE mismatch is the builder's stated instrument bound); none re-run.
- **Decisions needed:** D-5. Rename `ManifestOwner`/`MANIFEST_DIR`/`_manifest_path`/`self.manifest` + the 3 unpinned served "manifest" strings (lore_deploy.py `_slug_collision` refusals, `verb_stop`) to "ledger" in a follow-up that edits the tests too? Also: whether `ManifestOwner.record` is deleted once the contract stops calling it (§Task 5).
- **Flags (not mine to edit):** 3 STALE test docstrings (§Residual sweep); lifecycle.md "Collections" Qdrant-era bullet and the SKILL.md "ten tools" count, both unverified (§Task 6).

## Gate receipts (my final runs; haiku-runner, RAN: line checked = my commands; logs read by me)
| gate | command | log | EXIT | count line | TREE | lore_deploy.py sha256 |
|---|---|---|---|---|---|---|
| skill suite | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE` | `docs/plans/v2/receipts/2026-10-31-165/gate-audit-572-final-skill-suite.log` | 0 | `419 passed in 35.31s`, no FAILED/ERROR | fe5a3b47… | cbbfcdf0… |
| typecheck | `bash scripts/typecheck.sh` | `…/gate-audit-572-final-typecheck.log` | 1 (adjudicated) | `typecheck: skills OK`; loremaster 82 + scripts 1 = 83, 0 lines naming lore_deploy | 807d2f98… | cbbfcdf0… |
| ruff | `uv run ruff check .` | `…/gate-audit-572-final-ruff.log` | 0 | `All checks passed!` | 58e0be65… | cbbfcdf0… |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `…/gate-audit-572-final-currency.log` | 1 (#565) | typecheck RED_ADJUDICATED 83 · ruff GREEN · pytest NOT_RUN · no RED_ORPHANED | c5f70208… | cbbfcdf0… |
| (interim, VOID: superseded by later docstring edits) | same four | `…/gate-audit-572-{skill-suite,typecheck,ruff,currency}.log` | 0/1/0/1 | 419 passed | — | ec1240a0… |
TREE differs per log for the builder's stated reason: untracked receipt logs land between runs. Code identity is the sha256 column, identical across the four final logs and equal to the working-tree file at report time.

Fan-out: haiku 2 (gate runners) · sonnet 1 (test-hit verdict draft, 14/106 sampled) · peak 1.


## Routing table (written before first sweep)
| step | tier | who | reason |
|---|---|---|---|
| cold diff review (task 1) | 3 | self | audit verdict; errors self-seal |
| contract smell list (task 2) | 3 | self | judging another agent's tests |
| receipt verification (sha256, log EXIT/count/TREE) | 1 | self, one parallel batch | ≤6 small logs, read whole anyway |
| mutation proof (task 3) | 3 verdict / 1 run | self builds mutant; haiku-runner not used: mutation_proof.py is one command whose verdict I must judge, and scratch provenance must be checked in the same shell | |
| fixes (task 4, 6) | 3 | self | doc wording is never Haiku |
| post-fix skill suite + gates | 1 | haiku-runner | test runs |
| bare-pattern residual sweep (index_status / manifest) | 1 | self, one batch | small skill tree, output read whole for per-hit verdicts |

## Findings — written before 2026-11-01T00:38Z (the #560 annotate stamp), BEFORE any edit (graded 7d79115, lore_deploy.py sha256 ad23a318…ea31d9)

### Cold diff review (task 1)
Every path through `verb_setup` at 7d79115, checked for "only a successful cold index writes the marker":
- slug unresolvable → `_EXIT_ERROR`, nothing written. ✔
- container mounts another path / ledger records another owner / ownerless ledger + no lore.yaml → refusal, nothing written. ✔ (C2/C3)
- corrupt ledger → `meta()` raises `LedgerError` inside `_slug_collision` → one `setup: refused:` line. ✔ (C1)
- marker present + lore.yaml present → no-op + `.mcp.json` re-merge; nothing written. ✔
- marker present + lore.yaml ABSENT → `provisioned_at` forced `None` → scaffold + full re-provision. Safe direction; see D-2 (no pin forces it).
- scaffold / env-file / probe / image failures → return before step 7; nothing written. ✔
- cold index rc≠0 → return before `mark_provisioned`. ✔
- cold index rc=0 → `mark_provisioned` writes owner + marker in ONE transaction; a write failure → `LedgerError` → one line. ✔
- `mark_provisioned` has exactly one caller (after the rc check); `record` has none in production. The claim holds on every path.

| id | sev | finding | disposition |
|---|---|---|---|
| D-1 | low (defect class, pre-existing at 99c2b8e) | `_slug_collision`'s refusals render the ledger's stored `recorded` path and podman's `mounted` path RAW (`is held by {recorded}`); `status` repr-quotes the same stored owner path. A hostile/newline owner path forges a line on setup's stderr. The contract's hostile fixture covers `status` only — sibling NOT TRIED. | ROUTED to contract as a PROPERTY (below). Not fixed: it changes refusal text, a behaviour change outside a nit grant. |
| D-2 | low (door) | Nothing pins "marker present but lore.yaml deleted → setup does not no-op". A build dropping `if config_path.exists()` from the provisioned read no-ops and calls `_merge_mcp_from_config` on a missing config. | PROBED (§Probes P-2); routed as PROPERTY if it survives. |
| D-3 | low (C1 sibling) | `MANIFEST_DIR.mkdir` at step 7 is outside the `LedgerError` treatment: an uncreatable state dir (absent dir, unwritable parent) is an uncaught `PermissionError` traceback before the cold index. C1's write pin covers only "dir exists, read-only". | ROUTED as PROPERTY. Not fixed (traceback→refusal is a behaviour change). |
| D-4 | low (quality) | `ManifestOwner.record` has no production caller since 7d79115; its docstring does not say so. | FIX: docstring (task 5 verdict below). |
| D-5 | low (naming drift) | `ManifestOwner`, `_manifest_path`, `MANIFEST_DIR`, `_MANIFEST_META_DDL` and `exists()`'s `self.manifest` still say "manifest" while every new docstring and message says "ledger". The user rule calls cross-file naming inconsistency a bug. | NOT fixed: the contract calls `lore_deploy.ManifestOwner` / `MANIFEST_DIR` by name; a rename needs a test edit. Decision for the lead: a follow-up rename with the tests. |
| D-6 | info | setup reads the ledger twice (`_slug_collision` → `recorded_path()`, then `provisioned_at()`); two read-only sqlite opens. | Not fixed: negligible cost; folding needs a `_slug_collision` signature change for no measurable gain. |
| D-7 | info | `meta()` returns `str(value)`; DDL is `v TEXT NOT NULL`, so only a hand-edited row can hold `""`, which reads as provisioned. | Note only (hand-edit). |
| D-8 | info | `mark_provisioned` uses `datetime.UTC` (3.11+). The repo floor is 3.14 (`pyproject.toml` requires-python, ruff `py314` with UP), and the script runs as host `python3`. On a <3.11 host this is the one failure that lands AFTER the expensive index. | Note only: within the declared floor; `timezone.utc` would trip ruff UP017. |
| D-9 | info (wording) | The post-index write-failure line (`setup: cannot write ledger …`) does not say the index succeeded and that the next setup re-indexes. | Note only; C1 pins it to ONE line, so any wording change must stay on that line. |

DRY check: `lore_search` "read sqlite meta table key value rows from host manifest file" and "child python -c snippet exits with TypeName: message instead of traceback" (index current at 7d79115, `lore_index()` 2026-11-01T00:33Z) → the only ledger reader is `ManifestOwner.meta`; the child-error idiom has one sibling, `_DERIVE_SLUG_SNIPPET` (catches `ValueError`, exits `str(error)`; the two differ on purpose: the normaliser's message is already operator prose). No duplicate.

### Contract smell list (task 2) — REPORTED, never patched
| smell | where | what wrong build survives |
|---|---|---|
| tautology (expected value from the production reader) | `TestStatusShowsTheLedgerAsWhatItIs::test_status_shows_the_recorded_owner_path` takes its expected owner from `ManifestOwner.recorded_path()` | a `mark_provisioned` that records an unresolved or wrong path, echoed faithfully by status. The expectation should be `str(scene.project.resolve())`. |
| drift-prone hardcoded convention | `UNREADABLE_TOKEN = "unreadable"` (`test_status_over_a_meta_only_ledger_reports_nothing_unreadable`) keys on the retired renderer's word | a build saying "cannot read files table" passes this pin (the byte-identical `files`-variant pin still catches it, so the narrower pin is near-subsumed). |
| unrepresentative fixture | `DeployShim` always answers "no container" | the RUNNING branch of status is never rendered by this contract; a count printed only when running is unpinned here (probed, §Probes P-3). |
| no magnitude guard / forward-run-as-validation | — | none found; the count pin uses two unrelated populations and scrubs tmp paths. |
| fixture monoculture | hostile fixture applied to `status` only | D-1. |

Data-driven-scoring section: n/a — pure deploy logic with a fixed spec; green tests suffice.

## Probes (my own runs, scratch copy; none of these the builder ran)
Scratch: `scripts/scratch_copy.sh` → `…/scratchpad/mut572` (provenance asserted by the tool, EXIT=0). Receipt, printed inside the proof log:
`loremaster.__file__ = …/scratchpad/mut572/loremaster/loremaster/__init__.py` · `lore_deploy.__file__ = …/scratchpad/mut572/skills/lore-deploy/scripts/lore_deploy.py` · `LORE_PYTHON = …/scratchpad/mut572/.venv/bin/python`. Pre-mutation sha256 of the copy's lore_deploy.py = ad23a318…ea31d9 (= 7d79115).

| probe | mutation | command | result | verdict |
|---|---|---|---|---|
| **M-1 (task 3, mutation proof)** | marker write moved ABOVE the cold-index rc check (written whatever the index returns) | `scripts/mutation_proof.py --file lore_deploy.py --anchor-file … --replacement-file … --expect-red ×4 -- systemd-run … pytest -q . ../tests -n 8 --timeout=300 -rfE` from `skills/lore-deploy/scripts` | r1: `4 failed, 415 passed`, tool EXIT=4 (id-form false alarm, #560); r2: `4 failed, 415 passed`, **PROOF HELD, EXIT=0**, restored byte-exact (sha256 after = ad23a318…) | **KILLED.** The marker-after-success rule is pinned by exactly `TestSetupMarksProvisionedOnlyAfterASuccessfulColdIndex::{test_a_failed_cold_index_leaves_the_project_unprovisioned, test_a_failed_cold_index_over_an_owner_only_ledger_leaves_it_unprovisioned}` × {demand_intelligence, odoo-custom}. Logs: `docs/plans/v2/receipts/2026-10-31-165/gate-audit-572-mutation-marker-after-success.log` (r1) and `…-r2.log` (r2). |
| P-2 | `provisioned_at = ledger.provisioned_at()` (drop the `if config_path.exists()` guard) | `systemd-run … pytest -q . ../tests -n 8 --timeout=300 -rfE` | `419 passed` | **SURVIVES** — D-2 door open. |
| P-3 | status prints `SELECT COUNT(*) FROM files` from the ledger ONLY when the container is running | same | `419 passed` | **SURVIVES** — the ruling's central status property ("never shows file or chunk counts from the ledger") is pinned over the absent-container branch only. |

M-1's declared set was fixed from the test source BEFORE r1 (the only suite driving a failing cold index is `test_ledger_572.py`; verified by grepping `loremaster.index` / failure fakes in the other skill suites). r2 re-spelled the SAME 4 tests: taken from `--collect-only -q . ../tests` and stripped of the rootdir→cwd prefix `skills/lore-deploy/scripts/`, mechanically, never copied from r1's output.
**#560 recurred despite "run from the same cwd":** `--collect-only -q` prints rootdir-relative ids; the `-rfE` summary prints cwd-relative ids, from the identical cwd and args. Annotated on #560 (2026-11-01T00:38Z). The brief line is insufficient; the tool must normalise.

## Items routed back to the contract as PROPERTIES (each with the wrong build that survives today)
1. **P-STATUS-RUNNING (from P-3, highest):** "status prints no file or chunk count from the ledger in EVERY container state (absent, stopped, running)." Survivor: P-3. The fixture monoculture is `DeployShim` answering only "no container".
2. **P-SETUP-NO-CONFIG (from P-2):** "a ledger carrying the provisioned marker, with the project's lore.yaml deleted, does not make setup a no-op: setup re-scaffolds and re-provisions (or refuses), and never returns `_EXIT_OK` having merged `.mcp.json` from a missing config." Survivor: P-2.
3. **P-OWNER-RENDER (D-1):** "every render of a ledger-stored or podman-reported path is ONE value — the hostile newline owner path cannot forge a line on `setup`'s refusal stderr either." The hostile fixture exists (`HOSTILE_PROJECT_NAME`); apply it to the C2/F4 refusal (`is held by {recorded}`). Production fix belongs to the implementer once pinned.
4. **P-STATE-DIR-UNCREATABLE (D-3):** "setup over a state dir that cannot be CREATED (absent, parent unwritable) refuses in one line naming it, no traceback" — the write-path sibling of C1's read-only-dir pin.
5. **P-OWNER-VALUE (smell, tautology):** `test_status_shows_the_recorded_owner_path` should expect `str(scene.project.resolve())`, not the production reader's output.

## Task 5 — `ManifestOwner.record` verdict
**KEEP, for now.** Grep (fallback, case (a), exhaustiveness): zero production callers at 7d79115. `lore_impact("ManifestOwner.record")`, bare and module-qualified, both rode the bare-name fallback and unioned with `MemoryLedger.record` ("1 prod" = `LocalMemoryBackend.remember`, NOT this symbol). It disclosed this itself, so it is not a false clear. The skills/ scripts are not module-qualifiable in the graph (the known #507 seam); one test caller, `test_ledger_572.py::LedgerScene.record_owner_only`, which uses it to build the owner-only shape the #568 backfill left on disk. Deleting it would break a test the brief forbids touching. It is test-only production code, so I updated its docstring to say exactly that and when to delete it (with that arrangement). Recommended follow-up (contract-side): build the owner-only shape with raw `sqlite3`, as `write_legacy_ledger` already does for the pre-P5 shape, then delete `record`.

## Task 6 — stale docs: what changed (2026-11-01, on top of 7d79115)
Backups before the first edit: `cp -a` of all four writable files to `…/scratchpad/backup-7d79115/`.
- `SKILL.md`: the persistence paragraph (the store holds the index; the state dir holds the ledger and `<slug>.memory.db`); the `setup` row (it no-ops on the provisioned marker, which only a cold index exiting 0 writes; a ledger without the marker re-indexes); the `stop` row; the `status` row (it shows the owner and the marker, never an index count, and names `lore_index()`); "manifest/state layout" → "state-dir layout"; the persistence bullet; the freshness note (`index_status()` → `lore_index()`). **Also, the same class but outside the named lines:** the retired `search_code(..., wait_for_fresh=True)` → `lore_search(...)` and `reindex(tier=...)` → `lore_index(reconcile=True, tier=...)` in "How the tools work". These are CLAUDE.md's retired names, in served prose inside my writable set; I'm disclosing it here as a scope extension.
- `references/lifecycle.md`: the Manifest bullet → **Ledger** (no index state; counts come from `lore_index()`); setup step 1 (the marker decides; a corrupt ledger or a held slug refuses, exit 2, one line); setup step 7 (only exit 0 writes owner + marker in one transaction); the state-dir wording in the `--user`/`HOME`/`-v` bullets (index lives in the store; the dir holds `<slug>.memory.db` + the calibration cache, verified in `loremaster/loremaster/server.py` at the `MemoryLedger(...manifest_path.with_name(...memory.db))` and `CalibrationEngine(state_dir=manifest_path.parent)` sites); stop step 2; status steps 4–5 (the ledger line; a corrupt ledger goes to stderr with exit 0, per F-C; `lore_index()` named).
- `references/server-interface.md`: the healthcheck rule; §2 retitled "State-dir location", with the index declared store-resident; §3 rewritten as "Index counts come from `lore_index()`, never from `status`".
- `scripts/lore_deploy.py` (comments/docstrings ONLY, no runtime string changed): the module docstring, the `CONTAINER_HOME` comment, the `_launch_container` docstring, the `PROJECT_PATH_META_KEY` / `_MANIFEST_META_DDL` comments, the `_manifest_path` docstring, the `_slug_collision` docstring, and the `ManifestOwner.record` docstring (D-4).

**Flagged, NOT fixed (no verified replacement or not in the named set):** `references/lifecycle.md` "Collections: `lore_<slug>` + `lore_<slug>_memory` … `size=dim`, `distance=cosine`" is Qdrant-era prose, and the store is SurrealDB. A correct rewrite needs the store's per-slug database naming, which I did not verify. `SKILL.md` "when to use which of the ten tools" is a count claim I did not re-derive (the lore MCP served 15 tools in this session).

### Residual sweep — bare `index_status|manifest` (case-insensitive), skills/lore-deploy/, AFTER the edits
Coverage: `find` over `*.md *.py *.sh *.yaml *.json` (no `__pycache__`) = **23 files scanned**. Before the edits: **152 hits in 10 files**. After: 32 in production files/docs + 106 in tests = **138**. Retired-name sweep (`search_code|reindex(|what_imports|blast_radius|tests_for|read_file(|save_memory|recall_memory`, *.md) after the edits: 0 hits.

Production + docs (32 hits; my own verdicts):
| file:line | verdict | reason |
|---|---|---|
| references/server-interface.md:32 | OK-TRUE | the store-resident index manifest, named as such |
| SKILL.md:32 | OK-TRUE | same |
| references/lifecycle.md:17 | OK-TRUE | same |
| references/lifecycle.md:209 | OK-TRUE | same ("the index itself (manifest + code graph) lives in the store") |
| scripts/lore_deploy.py:77 | OK-IDENTIFIER | `MANIFEST_DIR`; the contract patches it by name (D-5) |
| scripts/lore_deploy.py:126 | OK-HISTORY | recounts the original incident, when status read the manifest file |
| scripts/lore_deploy.py:545 | OK-HISTORY | "the historical SQLite manifest", the DDL's documented origin |
| scripts/lore_deploy.py:548 | OK-IDENTIFIER | `_MANIFEST_META_DDL` (D-5) |
| scripts/lore_deploy.py:622 | OK-IDENTIFIER | `_manifest_path` (D-5) |
| scripts/lore_deploy.py:623 | OK-HISTORY | docstring now says ledger, "named for its pre-P5 role" |
| scripts/lore_deploy.py:624 | OK-IDENTIFIER | `MANIFEST_DIR` |
| scripts/lore_deploy.py:635 | OK-IDENTIFIER | `ManifestOwner`; the contract calls it by name (D-5) |
| scripts/lore_deploy.py:640 | OK-OTHER-SENSE | `SurrealManifest`, the store class |
| scripts/lore_deploy.py:646 | OK-IDENTIFIER | `<MANIFEST_DIR>` in a docstring |
| scripts/lore_deploy.py:647 | OK-IDENTIFIER | attribute `self.manifest` (D-5) |
| scripts/lore_deploy.py:651 | OK-IDENTIFIER | `self.manifest` |
| scripts/lore_deploy.py:661 | OK-IDENTIFIER | `self.manifest` |
| scripts/lore_deploy.py:664 | OK-IDENTIFIER | `self.manifest` |
| scripts/lore_deploy.py:672 | OK-IDENTIFIER | `self.manifest`; the rendered word is "ledger" |
| scripts/lore_deploy.py:711 | OK-IDENTIFIER | `self.manifest` |
| scripts/lore_deploy.py:712 | OK-IDENTIFIER | `self.manifest` |
| scripts/lore_deploy.py:715 | OK-IDENTIFIER | `_MANIFEST_META_DDL` |
| scripts/lore_deploy.py:722 | OK-IDENTIFIER | `self.manifest`; the rendered word is "ledger" |
| scripts/lore_deploy.py:754 | OK-IDENTIFIER | `ManifestOwner` |
| scripts/lore_deploy.py:762 | **TERM-DRIFT (served stderr)** | refusal renders "(manifest <path> records no project_path)". Unpinned: the contract pins only "unknown owner" (`test_scaffold_slug.py::UNKNOWN_OWNER_TEXT`). Proposed: "ledger". Left for the D-5 rename. |
| scripts/lore_deploy.py:766 | **TERM-DRIFT (served stderr)** | "(manifest <path>)" in the held-by refusal; same proposal; also D-1's raw `{recorded}` |
| scripts/lore_deploy.py:1106 | OK-IDENTIFIER | `MANIFEST_DIR` in the `-v` mount |
| scripts/lore_deploy.py:1189 | OK-IDENTIFIER | `ManifestOwner` |
| scripts/lore_deploy.py:1203 | OK-IDENTIFIER | `ledger.manifest`; rendered as "ledger <path>" |
| scripts/lore_deploy.py:1242 | OK-IDENTIFIER | `MANIFEST_DIR.mkdir` (D-3) |
| scripts/lore_deploy.py:1497 | **TERM-DRIFT (served stdout)** | `stop` prints "(store data + manifest preserved)". This is true of the store's manifest, but ambiguous now that the host file is the ledger. Unpinned. Proposed: "(store data + state dir preserved)". Left for D-5. |
| scripts/lore_deploy.py:1501 | OK-IDENTIFIER | `ManifestOwner` type hint |
| scripts/lore_deploy.py:1512 | OK-IDENTIFIER | `ledger.manifest` inside "no ledger at <path>" |
| scripts/lore_deploy.py:1522 | OK-IDENTIFIER | `ledger.manifest` inside "ledger <path>: owner …" |
| scripts/lore_deploy.py:1556 | OK-IDENTIFIER | `ManifestOwner(slug)` constructor |

Test files (106 hits): per-hit verdicts were drafted by a Sonnet agent against the key in §Routing (tier 2), and I sampled 14 of 106, all acceptable. Totals: OK-IDENTIFIER 65 · TERM-DRIFT 21 · OK-HISTORY 14 · OK-OTHER-SENSE 3 · **STALE 3** · ASSERTION-ON-RETIRED 0. The 3 STALE rows are present-tense test docstrings/comments, outside my writable set (NO test edits), so they are FLAGGED with proposed edits:
- `scripts/test_launch_snapshot_bind.py:1126` "live manifest/graph state dir" → "live host state dir";
- `scripts/test_lore_deploy.py:40` "manifest + `<slug>.graph.db` are mounted" → "`<slug>.memory.db` and the calibration cache are mounted";
- `scripts/test_lore_deploy.py:42` "reads the exact manifest + graph the host cold-index wrote" → "finds its `<slug>.memory.db` and cache in the state dir".
No assertion pins a retired name. The full per-hit table follows verbatim.


(Expected 110; the command returned 106.)

| file:line | verdict | reason |
|---|---|---|
| scripts/test_launch_snapshot_bind.py:522 | OK-OTHER-SENSE | placeholder for SurrealManifest/store collaborators |
| scripts/test_launch_snapshot_bind.py:529 | OK-IDENTIFIER | constructor keyword argument name |
| scripts/test_launch_snapshot_bind.py:1126 | STALE: rewrite "off the live host state dir" | comment says state dir holds manifest/graph |
| scripts/test_launch_snapshot_bind.py:1129 | OK-IDENTIFIER | MANIFEST_DIR module attribute |
| tests/test_containerfile_locked.py:96 | OK-OTHER-SENSE | workspace package manifest |
| scripts/test_lore_deploy.py:4 | OK-HISTORY | recounts old UID-999 regression incident |
| scripts/test_lore_deploy.py:5 | OK-HISTORY | recounts old UID-999 regression incident |
| scripts/test_lore_deploy.py:6 | OK-HISTORY | recounts old UID-999 regression incident |
| scripts/test_lore_deploy.py:7 | OK-HISTORY | recounts old UID-999 regression incident |
| scripts/test_lore_deploy.py:32 | OK-IDENTIFIER | test function name |
| scripts/test_lore_deploy.py:35 | TERM-DRIFT | state dir called manifest dir |
| scripts/test_lore_deploy.py:38 | TERM-DRIFT | state dir called manifest dir |
| scripts/test_lore_deploy.py:40 | STALE: rewrite "<slug>.memory.db and calibration cache are mounted" | claims index graph lives in mounted dir |
| scripts/test_lore_deploy.py:41 | TERM-DRIFT | state dir called manifest dir |
| scripts/test_lore_deploy.py:42 | STALE: rewrite "server finds its <slug>.memory.db and cache in the state dir" | claims server reads index manifest/graph from host |
| scripts/test_lore_deploy.py:48 | TERM-DRIFT | state dir called manifest dir |
| scripts/test_lore_deploy.py:60 | OK-IDENTIFIER | test-local variable name |
| scripts/test_lore_deploy.py:61 | TERM-DRIFT | assert message calls state dir manifest |
| scripts/test_lore_deploy.py:675 | TERM-DRIFT | comment says manifest read; reads ledger now |
| scripts/test_lore_deploy.py:676 | OK-IDENTIFIER | MANIFEST_DIR attribute and path comment |
| scripts/test_lore_deploy.py:678 | OK-IDENTIFIER | MANIFEST_DIR attribute and path comment |
| scripts/test_lore_deploy.py:1570 | OK-IDENTIFIER | MANIFEST_DIR attribute and path comment |
| scripts/test_lore_deploy.py:1572 | OK-IDENTIFIER | MANIFEST_DIR attribute and path comment |
| scripts/test_scaffold_slug.py:27 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:31 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:32 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:33 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:127 | OK-HISTORY | pre-P5 legacy manifest fixture shape |
| scripts/test_scaffold_slug.py:128 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:129 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:131 | OK-HISTORY | pre-P5 legacy manifest fixture shape |
| scripts/test_scaffold_slug.py:133 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:151 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:152 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:158 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:178 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:179 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:183 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:288 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:401 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:404 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:405 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:407 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:408 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:409 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:410 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:412 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:419 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:424 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:427 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:428 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:429 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:452 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:453 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:454 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:455 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:457 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:772 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:788 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:789 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:799 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:907 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:922 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:944 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:951 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:953 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:954 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:962 | TERM-DRIFT | assert message calls ledger a manifest |
| scripts/test_scaffold_slug.py:968 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:983 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:991 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:996 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:1001 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1002 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1010 | TERM-DRIFT | assert message calls ledger a manifest |
| scripts/test_scaffold_slug.py:1013 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1022 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:1029 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1040 | OK-HISTORY | describes legacy ownerless manifest |
| scripts/test_scaffold_slug.py:1042 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1096 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1218 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1219 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1249 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1250 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1251 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1257 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1269 | TERM-DRIFT | docstring calls ledger a manifest |
| scripts/test_scaffold_slug.py:1272 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1281 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1282 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1290 | TERM-DRIFT | assert message calls ledger a manifest |
| scripts/test_scaffold_slug.py:1292 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1297 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1298 | OK-IDENTIFIER | MANIFEST_* constants and helper names |
| scripts/test_scaffold_slug.py:1306 | TERM-DRIFT | assert message calls ledger a manifest |
| scripts/test_ledger_572.py:5 | OK-OTHER-SENSE | SurrealManifest class name |
| scripts/test_ledger_572.py:110 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:214 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:219 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:223 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:224 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:228 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:605 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| scripts/test_ledger_572.py:667 | OK-IDENTIFIER | MANIFEST_DIR / ManifestOwner identifiers |
| tests/test_port_probe.py:7 | OK-HISTORY | recounts original incident, old status checks |

OK-OTHER-SENSE: 3
OK-IDENTIFIER: 65
STALE: 3
OK-HISTORY: 14
TERM-DRIFT: 21
ASSERTION-ON-RETIRED: 0

