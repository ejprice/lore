brief-base v25 read · brief project v7 read

# REPORT — impl-572-ledger (tdd-light GREEN, #572 + the #568 audit's C1–C6, wave #165, 2026-10-31)

## Summary
- **State:** done-with-deviations (one small deviation, below).
- **Result at HEAD 94d3a0d + this diff:** the skill suite passes, **419 passed, 0 failed** (the contract's RED was 57 failed / 362 passed at 94d3a0d). typecheck has 0 errors in `lore_deploy.py` (`skills OK`). ruff is clean. Currency `--legs typecheck,ruff` shows **RED_ORPHANED 0**.
- **Deviations:**
  1. I `repr`-quote the `provisioned_at` value in status and in setup's no-op line, the same as the owner path. No test demands this. It comes from the stored-text render rule: the ledger is hand-editable.
- **Packages considered:** stdlib `sqlite3` (the existing `ManifestOwner` reader/writer, read in full) and stdlib `datetime` for the marker's UTC timestamp. Verdict: no new package; this extends the existing mechanism in place.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 7 new symbols, all dispositioned (§DRY ledger). `ManifestOwner` was EXTENDED, not forked.
- **Graded:** n/a (builder report, not a verdict).
- **Decisions needed:** none blocking. Two forks have both readings written (§Forks F-A, F-B). Five flags concern files outside my writable set (§Flags).
- **Receipts:** §Gate receipts · `lore_deploy.py` sha256 `ad23a318f112b1e80f62d71d8fd88ed19df39c73134028facba6d830b3ea31d9` at report time (2026-10-31), the same bytes every final gate ran on.

## Capability check
Nothing was denied. The brief's `-rfE` shows no reasons because nothing failed.

## Routing table (written at start; final)
| step | tier | who | reason |
|---|---|---|---|
| read the rulings, the contract report, the tests and the `lore_deploy.py` seams | 3 | self | the implementation judgment rests on it |
| `lore_search` for owners of new rule-deciding code | 1 | self, inline | 2 queries, output read whole, on the critical path |
| edit `lore_deploy.py` | 3 | self | the GREEN build |
| ruff + import pre-flight on one file | 1 | self, inline | under 1 s, run before spending a runner |
| skill-suite gate (r1, then r2 after deviation 1) | 1 | haiku-runner ×2 | test runs |
| typecheck / ruff / currency gates | 1 | the same r2 haiku-runner, run sequentially | lint/type gates |

Fan-out: haiku 2 · sonnet 0 · peak 1. I read both runners' `RAN:` lines and re-read every log's count/`EXIT=`/`TREE=` line myself.

## Gate receipts
| gate | command | log | EXIT | count line | TREE |
|---|---|---|---|---|---|
| skill suite (FINAL) | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE` | `docs/plans/v2/receipts/2026-10-31-165/gate-impl-572-skill-suite-r2.log` | 0 | 419 passed in 34.02s; no ImportError, no collection error | abe4bfe18bbd310d74afb78596d3f13318e61e19ca645d6c601541627ccc9c2e |
| typecheck | `bash scripts/typecheck.sh` | `docs/plans/v2/receipts/2026-10-31-165/gate-impl-572-typecheck.log` | 1 (adjudicated) | `typecheck: skills OK`; 0 lines naming `lore_deploy`; loremaster 82 errors + scripts 1 = 83 | 49f574fc6097f78d782e3727ea32edc98530127711a9cc9e7d206c21c91d8d5a |
| ruff | `uv run ruff check .` | `docs/plans/v2/receipts/2026-10-31-165/gate-impl-572-ruff.log` | 0 | All checks passed! | 32a7fe7365763d10988fec317ae7b3d08a60561049e39d1376f78fdd927ab313 |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `docs/plans/v2/receipts/2026-10-31-165/gate-impl-572-currency.log` | 1 (#565) | typecheck RED_ADJUDICATED (83 residuals, packet-58 / 64b-i) · ruff GREEN · pytest NOT_RUN · no RED_ORPHANED line | dac3ada5cf91d775cab24020b399f98199a8c277ef1ff719693bdd4fd36939c5 |
| skill suite r1 (VOID, superseded by deviation 1's edit) | same as FINAL | `docs/plans/v2/receipts/2026-10-31-165/gate-impl-572-skill-suite.log` | 0 | 419 passed in 34.62s | af7c0563… |

⚠ **Why the four final TREE values differ (bound, measured 2026-10-31):**
- `tree_id.sh` hashes untracked files too, and `docs/plans/v2/receipts/2026-10-31-165/` is untracked at 94d3a0d.
- So each gate's own log, written before the next gate starts, changes the next gate's TREE.
- No production or test file changed between the four runs: the runner made no edits, and I made none during the batch.
- The code identity to check is the `lore_deploy.py` sha256 in the summary.
- An auditor's TREE on the graded commit can match only if the commit carries the same untracked set. That is a property of the instrument; the lead decides how to grade it.

## Files changed
- `skills/lore-deploy/scripts/lore_deploy.py` (the only file in my writable set): +190 / −82. Backup of the 94d3a0d bytes was taken before the first edit (scratchpad `lore_deploy.py.orig-94d3a0d`).
- `REPORT-impl-572-ledger.md` (this file).

## What changed (by symbol)
- **`ConfigUnreadable(RuntimeError)`**, new. `_read_config_field` now raises it.
  - The child program wraps the load + `print(expr)` in `try/except Exception` and exits `sys.exit(f"{TypeName}: {message}")`. That is the same idiom as `_DERIVE_SLUG_SNIPPET`, so no traceback reaches stderr (C6).
  - The message keeps the `failed to read {expr!r} from {config_path}:` prefix. The existing `match="failed to read"` pins in `test_lore_deploy.py` hold, and `config_reader_fake.py`'s `TypeName: message` shape now matches the real reader.
- **`LedgerError(RuntimeError)`**, new: one line naming the ledger file plus sqlite's own error (C1).
- **`ManifestOwner`**, extended in place:
  - `meta()` is the ONE reader.
    - It opens the file read-only and asks `sqlite_master` whether a `meta` table exists. Absent file or table → `{}`.
    - Any `sqlite3.Error` → `LedgerError`.
    - This classifies by STRUCTURE, not by matching the "no such table" message text the reference used.
  - `recorded_path()` / `provisioned_at()` are views over `meta()`.
  - `_write_meta(rows)` is the ONE writer: mkdir, DDL and every row in one transaction. `OSError` / `sqlite3.Error` → `LedgerError`.
  - `record(project)` writes the owner only. `mark_provisioned(project)` writes the owner AND the marker (`provisioned_at` = UTC ISO-8601) in one transaction. The reference used two transactions.
  - New constants: `PROVISIONED_META_KEY`, `_LEDGER_HAS_META_SQL`.
- **`verb_setup`:**
  - The collision check and the provisioned read are wrapped in `except LedgerError` → `setup: refused: <one line>`, `_EXIT_ERROR`, before anything is created.
  - "Already provisioned" is `config exists AND provisioned_at() is not None`.
  - After a successful cold index it calls `mark_provisioned`; a write failure gives `setup: <one line>` and `_EXIT_ERROR`.
- **`_refuse_unresolved_slug(verb, project, error)`**, new: the shared refusal for `stop` and `status`.
  - It prints the error.
  - For a `ConfigUnreadable` only, the LAST stderr line is the remedy: `fix <project>/lore.yaml, or stop the container by hand: podman stop lore-<slug> (the project.slug you meant)`.
  - It guesses no slug and runs no podman call.
- **`_ledger_status_line(ledger)`**, new.
  - No ledger → `no ledger at <path> (not yet set up).`
  - Otherwise: the ledger path, the owner (repr, or "none recorded (a pre-#568 ledger)") and the provisioned state (yes with the repr'd timestamp, or "no (the next setup cold-indexes)").
  - It derives no index fact.
- **`verb_status`:**
  - It prints the ledger line; a `LedgerError` goes to stderr naming the file, and the exit stays `_EXIT_OK`.
  - It then ALWAYS prints `the index counts live in the store, not in this ledger: read them with the lore_index() MCP tool (the server must be running).`

## Removed-behaviour inventory
| removed / changed | disposition |
|---|---|
| `_manifest_counts` (deleted): per-state `files` counts, "no files indexed yet", `(unreadable: …)` on `sqlite3.Error` | counts **dropped-deliberately** (RULING-572-ledger.md: status shows no ledger counts); its `sqlite3.Error` guard is **preserved-with-pin** via `LedgerError` in `_ledger_status_line` (`TestStatusOverACorruptLedger`) |
| status `manifest <path> → <counts>` / `no manifest at <path>` lines | replaced by the ledger line, **pinned**: `TestStatusShowsNoIndexFactFromTheLedger`, `TestStatusShowsTheLedgerAsWhatItIs` |
| status's running-only line `query the MCP index_status() tool for live freshness (see server-interface.md …)` | **dropped-deliberately / old-bug**: `index_status` is a retired tool name (`lore_index`'s own description says it merged the index-status tool), and the line contradicted the new pointer. Replaced by the always-printed `lore_index()` line, **pinned** by `test_status_names_where_the_index_counts_live` |
| setup's "already" = config exists AND ledger file exists | replaced by the marker, **pinned** by `TestProvisionedDecisionFollowsTheMarker` |
| setup's legacy backfill on the no-op path (`owner.record(project)` when no owner was recorded) | **dropped-deliberately** (F-2 (a): a legacy ledger is unprovisioned, so setup re-indexes and `mark_provisioned` claims it), **pinned** by `test_existing_deployment_with_a_legacy_manifest_is_reindexed_and_claimed` |
| `recorded_path` catching EVERY `OperationalError` as "ownerless" (a locked or permission-denied ledger read as ownerless, so setup with a lore.yaml proceeded) | **changed deliberately**: only an absent `meta` table is ownerless; every other sqlite error refuses (C1 class). Corrupt shapes are pinned (C1 ×4); **a permission-denied READ is not pinned** (the C1 write pin covers the write side only); flagged for the contract |
| setup no-op text `(config + manifest present)` | reworded to name the ledger and the marker's timestamp; nothing pins the old text |
| `_read_config_field` raising a plain `RuntimeError` carrying the child's traceback | `ConfigUnreadable` (a `RuntimeError` subclass, so every caller's `except RuntimeError` is unchanged), `TypeName: message`; **pinned** by C6 ×4 and the existing `failed to read` pins |
| stop/status on a `SlugRefusal` | unchanged (same line, no added remedy: the refusal already ends with `_SLUG_REMEDY`) |

## DRY ledger
| new symbol | where I looked | what it returned | disposition |
|---|---|---|---|
| `ManifestOwner.meta` / `_write_meta` / `mark_provisioned` / `provisioned_at` | the brief (named `ManifestOwner`); `lore_search "lore_deploy ledger sqlite error classification unreadable manifest provisioned marker"` | only the contract report's description of the reference | **EXTENDED `ManifestOwner`**: its one reader and one writer now serve both keys; no parallel sqlite reader |
| `LedgerError` | same query; read `lore_deploy.py` (`SlugRefusal` is the only error type) | none | HAND-ROLLED: a distinct type so setup/status catch the ledger failure without catching config or slug errors |
| `ConfigUnreadable` | `lore_search "child interpreter exits with one-line error message instead of traceback"`; in-file `_DERIVE_SLUG_SNIPPET` | the in-file `sys.exit(str(error))` idiom | the child error idiom is **REUSED** (`_DERIVE_SLUG_SNIPPET`'s); the type is HAND-ROLLED so stop/status can tell "slug unknowable" from `SlugRefusal` |
| `_refuse_unresolved_slug` | `verb_stop` / `verb_status` / `verb_setup` / `verb_start` error branches | four inline `print(...); return _EXIT_ERROR` copies | HAND-ROLLED as the ONE shared refusal for stop+status (the two C6 verbs); setup/start keep their own lines (see F-B) |
| `_ledger_status_line` | `verb_status`; the shared sanitiser law (`loremaster.search._sanitise_line`) | the sanitiser cannot be imported (bare python3, brief) | HAND-ROLLED; owner and marker are `repr`-quoted, the same idiom this file uses for rendered values (`{expr!r}`) |
| `PROVISIONED_META_KEY`, `_LEDGER_HAS_META_SQL` | beside `PROJECT_PATH_META_KEY` / `_MANIFEST_META_DDL` | the sibling constants | new constants in the same block |

## Forks (both readings written; my pick stated)
- **F-A, C6 "a refusal line":** the addendum says stderr "is a refusal line naming the file and the parse error". (a) ONE physical line: collapse the loader's multi-line pydantic/YAML text. (b) A refusal that opens with one line naming the file, followed by the loader's own text unchanged. **I picked (b)**: no test pins either, and the loader's text is the oracle the contract checks. Choosing (a) means one `" ".join(stderr.split())` in `_read_config_field`, which changes every caller's message.
- **F-B, the remedy's reach:** I added the C6 remedy to `stop` / `status` only, which are the verbs C6 names. `setup` / `start` on an unreadable lore.yaml still print `failed to read … : TypeName: message` without a traceback (the `_read_config_field` fix reaches them), but with no "podman stop" remedy. That seemed right because the remedy is stop-shaped. Do you want a verb-appropriate remedy on those two as well?
- **F-C, status exit over a corrupt ledger:** spec-silent. I kept `_EXIT_OK` and sent the `LedgerError` line to stderr, as status already does for an unreadable server block. The other reading is `_EXIT_ERROR`, since a corrupt ledger is an error.

## Flags (outside my writable set; nothing edited)
1. **`_validate_config_schema`** (same file, a sibling of C6) still runs `_schema_load_snippet` bare. A scaffolded config that fails validation still prints a child traceback. This is the same class as C6, and no test pins it. I left it alone rather than add untested behaviour. Do you want it routed through the same `TypeName: message` child?
2. **Docs still describe the pre-#572 world:**
   - `skills/lore-deploy/SKILL.md:51`: "detects the existing config + manifest and no-ops";
   - `SKILL.md:54` and `:280`: status reports `index_status()` freshness and "reads the manifest directly";
   - `skills/lore-deploy/references/lifecycle.md:52` and `:223`;
   - `skills/lore-deploy/references/server-interface.md:47` (§3 `index_status()`).

   Each now teaches a retired tool name and a ledger count status no longer prints. The fix is to say that status shows the ledger's owner and provisioned marker, and that the counts come from `lore_index()`.
3. **A permission-denied ledger READ is unpinned** (removed-behaviour row 6). It is a contract gap, not a builder gap.
4. **`ManifestOwner.record` has no production caller** after this change. Setup now uses `mark_provisioned`, and `record` is reached only from the contract (`LedgerScene.record_owner_only`, which arranges the #568 owner-only shape). I kept it because the contract calls it. `lore_dead_code` will list it as `only_referenced_by_tests`.
5. **F-2 re-index cost is unmeasured** (carried from the contract report). The next `setup` on `lore` and `demand_intelligence` cold-indexes and needs the secrets env-file. `stop` / `start` never read the ledger.

## Reference handling
I started from the SATISFIABILITY-ONLY reference and did not copy these defects:
- the unsorted `import datetime`;
- classifying "no table" by matching sqlite's message text;
- two transactions for owner + marker;
- the remedy duplicated inline in stop and status;
- the stale `index_status()` line left in place beside the new pointer;
- the unquoted marker value.

Nothing in the reference that no test or ruling demands was kept.
