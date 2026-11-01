brief-base v25 read
brief project v7 read

## SUMMARY (impl-568-slug · finding #568 GREEN · 2026-10-31 · HEAD `0c7477c`, uncommitted tree)
- **State:** done-with-deviations (one escalation, nothing silently chosen: F-A below).
- **Deviations:** (1) TREE= receipts cannot be equal across gates, because `tree_id.sh` hashes the untracked REPORT files and gate logs (§Gate receipts). Per-file sha256 of every changed file is given instead. (2) One Bash call was DENIED (an `rm -rf` in the scratchpad); retried without the delete.
- **Gates:** skill suite **348 passed / 0 failed** EXIT=0 · loremaster config scope **557 passed / 2 skipped / 0 failed** EXIT=0 · typecheck: skills leg OK; 83 errors, all in packet-58/64b test files, all RED_ADJUDICATED (0 in my files) · ruff clean · currency `--legs typecheck,ruff` **RED_ORPHANED 0** · dry scaffold `odoo-custom` → `slug: "odoo_custom"`.
- **ONE normaliser:** `loremaster.config.derive_project_slug` (beside `SLUG_PATTERN`). **ONE resolver:** `lore_deploy._project_slug`. Its config branch `_configured_slug` is used directly only where a config is already required (§Call sites).
- **Packages considered:** slug normalisation → python-slugify 9.1.3 · read the installed signature + `py.typed` + live outputs for the contract's names · `replace` (ruled F1). Manifest owner row → stdlib `sqlite3` · no loremaster SQLite writer exists to reuse (§Reuse) · `bespoke` (5 statements, flagged).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 6 new rule-deciding symbols, all dispositioned (§DRY ledger).
- **Dependency / image:** `uv add --package loremaster python-slugify` (adds python-slugify 9.1.3 + text-unidecode 1.3 to `uv.lock`). Image: `Containerfile` `RUN uv sync --locked --all-packages` installs it from the lock, so no Containerfile change. ⚠ `config.py` imports slugify at MODULE level, so the image NEEDS it at server boot, not only on the host.
- **Decisions needed:** F-A (finding **#572**): the SQLite `<slug>.db` that setup/status and the new owner row key on has had no writer in loremaster since P5. Move ownership to `SurrealManifest` meta, or formally keep the SQLite file as a deploy-side ledger? Plus two unpinned readings (§Readings).
- **Receipts:** §Gate receipts · `docs/plans/v2/receipts/2026-10-31-165/gate-568-impl-*.log` · instrument `dry_scaffold.py` pasted in §Gate 5.
- **Graded:** n/a (builder report; renders no verdict on another's artifact).

## Capability check
All demanded tools were available, except one Bash call: DENIED 2026-10-31, the gate-5 command that began with `rm -rf <scratchpad>/dry`. Retried with `mktemp -d` and no delete. Nothing else was blocked.

## Routing table (written before the first sweep; first draft at report creation)
| step | tier | who | reason |
|---|---|---|---|
| read ruling / contract report / tests / lore_deploy.py | 3 | self | the implementer must read the spec and the code it changes |
| reuse search (normaliser, meta writer, resolver, rebuild paths) | 1/3 | self, as parallel batches | small (<6 queries each, output read in full), on the critical path; coverage lines below |
| implementation edits | 3 | self | builder role (project roster: Opus) |
| uv add python-slugify | 1 | self inline | one command on the critical path |
| gate 1 skill suite | 1 | haiku-runner | test run |
| gate 2 loremaster config scope | 1 | haiku-runner | test run |
| gates 3+4 typecheck, ruff, currency (serial: one shared mypy cache) | 1 | haiku-runner | gate runs |
| gate 5 live scaffold dry check | 1 | self inline | one script; I must read its whole output |

Fan-out: haiku 3 · sonnet 0 · peak 2. Every runner's `RAN:` line matched my command; I read each count/EXIT line in the log myself.

## Call sites (all 8 #568 sites + main)
| site | slug source |
|---|---|
| `_resolve_env_file` | `_project_slug(project)` |
| `_scaffold_lore_yaml` | `_derive_slug(project)`: only runs when lore.yaml is absent, which is the resolver's own else-branch |
| `_launch_container` | `_configured_slug(config_path)`: launch requires a config, and tests pass a `config_path` with a faked reader (`test_lore_deploy.py` `ConfigReaderFake`), so it must read THAT config |
| `_launch_or_exit_loudly` | `_configured_slug(config_path)`; if the read fails, the label falls back to "the lore container for <project>" and the launch reports the real failure |
| `verb_setup` · `verb_start` · `verb_stop` · `verb_status` | `_project_slug(project)` |
| `main` | the `is_dir()` guard now runs BEFORE `_resolve_env_file`; a `RuntimeError` (incl. `SlugRefusal`) → `_EXIT_ERROR` + a stderr line |
Bare `project.name` remains in exactly one place: the argument to the normaliser, inside `_derive_slug`.

## What changed
- `loremaster/loremaster/config.py`: `SLUG_SEPARATOR = "_"` and `derive_project_slug(directory_name)` beside `SLUG_PATTERN`. The function calls `slugify(name, separator="_")`, checks `re.fullmatch(SLUG_PATTERN, …)`, and otherwise raises `ValueError` naming the directory, `project.slug` and `lore.yaml`. New imports: `re`, `slugify`.
- `skills/lore-deploy/scripts/lore_deploy.py`, new section "Project slug (#568)":
  - constants `CONFIG_FILENAME`, `CONTAINER_WORKSPACE`, `PROJECT_PATH_META_KEY`, `_MANIFEST_META_DDL`, `_DERIVE_SLUG_SNIPPET`, `_WORKSPACE_SOURCE_FORMAT` and `_SLUG_REMEDY`;
  - `SlugRefusal(RuntimeError)`, `_derive_slug`, `_configured_slug`, `_project_slug`, `_manifest_path`;
  - `ManifestOwner` (`exists` / `recorded_path` / `record`), `_container_workspace_source` and `_slug_collision`.
  - The normaliser is reached as `[_loremaster_python(), "-c", snippet, project.name]`. The name travels as argv, never as code. A refusal is `sys.exit(str(error))`: a stderr line, no traceback.
- Scaffold:
  - the slug is emitted as `json.dumps(slug)`, a YAML double-quoted scalar, so `2026` stays a string;
  - the file is written to a staged temp file beside the target, schema-validated, then `os.replace`d into place, and the staged file is always unlinked. Neither an invalid template nor a crash can leave an invalid lore.yaml.
- `verb_setup` runs, in order: resolve the slug → `_slug_collision` → backfill `project_path` on an own legacy manifest (provisioned path) → after the cold index, `owner.record(project)`. A scaffold failure → `_EXIT_ERROR`.
- `pyproject.toml` / `uv.lock`: python-slugify.

## Reuse receipts / DRY ledger
| new symbol | where I looked | why nothing fit |
|---|---|---|
| `derive_project_slug` | contract report Phase 0 (480 .py, no normaliser); my own grep `slugify\|def .*slug` over loremaster/lorerunes/skills/scripts (prod only, 3 hits, all unrelated `slug` params) | none exists; `lorerunes` is stdlib-only (ruling F2) |
| `_project_slug` / `_configured_slug` / `_derive_slug` | `lore_deploy.py` def sweep (60 defs); `_read_config_field` is REUSED as the config read | thin routing over existing seams; no prior resolver |
| `ManifestOwner` | `lore_search` "manifest sqlite meta table writer"; grep `INTO meta\|FROM meta\|meta (k` over prod trees (0 prod hits) | the only live meta writer is async `SurrealManifest.meta_set` (Surreal store). The SQLite `Manifest` class was DELETED post-P5 (`loremaster/index/manifest.py` docstring), so there is no SQLite writer to reuse. `lore_deploy._manifest_counts` is the file's only other reader. The `meta` DDL is copied from `loremaster.index.manifest._SCHEMA` (private, documented as "Not executed by anything today"): a duplicated 1-line DDL, cited in its comment. **Not reused:** `open_resilient_sqlite`, because it DELETES a malformed DB, which is wrong for an ownership ledger. |
| `_container_workspace_source` | `_container_state` / `_container_image_id` (same `podman container inspect --format` idiom) | they read other fields; one more `--format` query in the same idiom |
| `_slug_collision` | none | a new rule (F4) |
lore was the first tool. grep fallbacks were used for `scripts/`/`skills/` (a seam `lore_impact` cannot see, #507) and for the textual DDL/meta-key seam.

## F-A — ESCALATION: the manifest the contract keys on is a dead file (finding #572)
Measured 2026-10-31 at `0c7477c`:
- `loremaster/index/cli.py` cold-indexes into `SurrealManifest` only;
- `server.py` uses `manifest_path` only as the anchor for `<slug>.memory.db`;
- host `lore.db` was last written 2026-07-03 and `demand_intelligence.db` 2026-07-04.

So:
- **(1)** On a real host, `ManifestOwner.record` CREATES `<slug>.db` with only `meta`. That is what makes the next setup see "already provisioned". Before this change, every setup of a post-P5 project re-ran the cold index.
- **(2)** For such a project, `verb_status` now prints `(unreadable: no such table: files)` where it used to print `no manifest (not yet set up)`. Both are false. The real counts are in Surreal, and no test pins status on a meta-only file.
- **(3)** The contract fixture `PodmanShim._index_like_the_real_indexer` models an indexer that creates `<slug>.db`; the real indexer does not. That is the TEST-ENVIRONMENT-IS-A-FICTION class.

Implemented per the ruled contract regardless, because the row works as a deploy-side ownership ledger. **Decision for the operator:** move ownership + the provisioned check + status counts to `SurrealManifest` meta, or rule the SQLite file a deploy-side ledger (and fix status's counts).

## project_path durability (directive #18017)
Sweep: `git ls-files '*.py'` excluding tests, 180 files, grep for `meta_delete|DELETE FROM meta|REMOVE TABLE|DROP TABLE|.unlink(|os.remove(|shutil.rmtree|_DEFAULT_MANIFEST_DIR|MANIFEST_DIR|open_resilient_sqlite(|schema_rebuild_status|fingerprint_mismatch|store_divergence_heal`. Every hit was read:
- `indexer.py` schema rebuild / `fingerprint_mismatch` / `server.py` `store_divergence_heal` all act on `SurrealManifest` meta (Surreal), never on the SQLite file. `indexer.py` `meta_delete` deletes only `BULK_SWEEP_BATCH_JOB_META_KEY`, in Surreal.
- `sqlite_resilient.py`'s unlink is reached only via `MemoryLedger` (`<slug>.memory.db`, `server.py` `manifest_path.with_name(...)`), never `<slug>.db`.
- `memory/local.py` `REMOVE TABLE` is the Surreal memory table.
- `lore_deploy.py`'s only unlink is the staged scaffold temp file.
- The remaining hits (`build_variants.py`, `mutation_proof.py`) are receipt and tool scratch.

**Verdict (HIGH, from the sweep):** no loremaster path rebuilds, recreates or deletes the SQLite `<slug>.db`, so none can drop the row. That holds only because loremaster no longer owns the file (F-A). If F-A moves ownership into Surreal meta, the rebuild paths above become the ones to re-check. Residual: an operator deleting the state dir loses the row, and the next fresh setup then just re-records it.

## Readings (two readings each; my pick stated; neither is pinned)
1. **Container shows this path + legacy manifest + no lore.yaml.** Reading (a), literal to the Addendum ("only a FRESH setup … meeting an ownerless manifest is refused"): refuse as unknown owner. Reading (b), from "names the holder's path … from the container when that shows it": the container proves ownership, so backfill. **Implemented (a)** (no added untested behaviour). (b) is one condition in `_slug_collision`.
2. **Container mounts THIS path but the manifest records ANOTHER.** The reference short-circuits on the container (accept). **Implemented the ruling's "manifest OR container" literally**, so either one naming another path refuses. No test distinguishes the two.

## Noticed
- **`tree_id.sh` cannot give equal TREE= across one builder's gates.** It hashes untracked, non-ignored files, which includes every root `REPORT-*.md` and every gate log under `docs/plans/v2/receipts/`. Writing a receipt changes TREE. A clean checkout of the graded commit will also differ by the 30+ untracked REPORTs now at the root. Suggested fix (outside my set): hash only tracked paths plus explicitly named ones, or exclude `REPORT-*.md` and `receipts/**/*.log`.
- `stop`/`status` now need a readable lore.yaml when one exists (F3). A malformed lore.yaml makes `stop` refuse (`_EXIT_ERROR` + the read error) where it used to stop `lore-<dirname>`. Accepted as a consequence of F3; flagged.
- `main` resolves the env-file for `stop`/`status` too, which never use it: one extra config read each. Unchanged behaviour shape.
- The `PLR0911` noqa on `verb_setup` now covers more returns. The P8e rework is already noted there.

## Gate receipts
Changed-file fingerprints, **unchanged since before gate 1 started** (last edit 19:45:01; gate 1 launched after): `lore_deploy.py` `b130e134…e9e2` · `config.py` `fdb3f039…9698` · `loremaster/pyproject.toml` `ccd63401…0b` · `uv.lock` `55dc360e…ef60d` (full hashes: `sha256sum` of each; re-derivable).
| gate | command | log | EXIT | count | TREE= |
|---|---|---|---|---|---|
| 1 skill suite | `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests -n 8 --timeout=300 -p no:cacheprovider -rfE` | `docs/plans/v2/receipts/2026-10-31-165/gate-568-impl-skill-suite.log` | 0 | 348 passed in 26.69s (0 collection/import errors) | `6f9f8781…7fa657` |
| 2 loremaster config scope | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q loremaster/tests/test_config.py loremaster/tests/test_auth_config_recut.py loremaster/tests/test_harness_database_lifecycle_486.py loremaster/tests/test_build_store.py loremaster/tests/test_agent_registry.py loremaster/tests/test_comms_cli.py -n 8 --timeout=300 -p no:cacheprovider -rfE` | `…/gate-568-impl-loremaster-config.log` | 0 | 557 passed, 2 skipped in 164.57s (0 collection/import errors) | `4db7a2af…e8da44eb` |
| 3a typecheck | `bash scripts/typecheck.sh` | `…/gate-568-impl-typecheck.log` | 1 | skills OK; 83 `error:` = 82 loremaster (packet-58/64b test files) + 1 scripts (`test_forgery_door_sweep.py`), 0 in my files | `be473e94…5f3005` |
| 3b ruff | `uv run ruff check skills/lore-deploy/scripts/lore_deploy.py loremaster/loremaster/config.py` | `…/gate-568-impl-ruff.log` | 0 | All checks passed! | `384ef21d…76138f` |
| 4 currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `…/gate-568-impl-currency.log` | 1 (pytest NOT_RUN by `--legs` design) | typecheck RED_ADJUDICATED (83 residuals, packet-58 + 64b-i), ruff GREEN, **RED_ORPHANED 0** | `4a595759…68a56` |
| 5 dry scaffold | `python3 <scratchpad>/dry_scaffold.py skills/lore-deploy/scripts <mktemp dir>` (bare python3; real `_loremaster_python()`) | `…/gate-568-impl-dry-scaffold.log` | 0 | `slug: "odoo_custom"`; resolver `odoo_custom`; `---` refused (SlugRefusal), no leftovers | `7518ca95…e46e61` |

TREE values differ only by REPORT/log files (deviation 1). The code fingerprints above are the binding identity.
Typecheck vs HEAD: no separate HEAD run. The baseline is the adjudication registry, whose owned residual set (83) equals the observed set (83). The contract report recorded the same RED_ADJUDICATED state at `eba0a46`.
Gate 2 scope derivation: `lore_impact(loremaster.config.SLUG_PATTERN)` → covering tests only in `test_scaffold_slug.py` (63 tests; 48 elided, #563). `derive_project_slug` is new and not yet indexed. I added the config behaviour suites (`test_config.py`, `test_auth_config_recut.py`) plus a grep fallback (`SLUG_PATTERN|SlugStr|derive_project_slug|from slugify|invalid slug|slug.*hyphen` over the loremaster/lorerunes/loresigil/lorescribe test trees: 5 files), and SAY SO.

### Gate 5 instrument (pasted verbatim, brief-base §1)
```python
"""Gate 5 instrument (#568): scaffold-only dry check on a throwaway `odoo-custom` git repo.

Runs the REAL `_scaffold_lore_yaml` and `_project_slug` with the real `_loremaster_python()`;
no container, no cold index, no network. Usage: python3 dry_scaffold.py <skill-scripts-dir> <base-dir>
"""

import subprocess
import sys
from pathlib import Path

scripts_dir, base = Path(sys.argv[1]), Path(sys.argv[2])
sys.path.insert(0, str(scripts_dir))
import lore_deploy as d  # noqa: E402

print("loremaster python:", d._loremaster_python())
project = base / "odoo-custom"
project.mkdir()
subprocess.run(["git", "init", "-q", str(project)], check=True)
d._scaffold_lore_yaml(project, project / "lore.yaml")
text = (project / "lore.yaml").read_text(encoding="utf-8")
print("slug line:", [line for line in text.splitlines() if line.strip().startswith("slug:")])
print("resolver _project_slug:", d._project_slug(project))
print("leftovers:", sorted(p.name for p in project.iterdir()))

refused_dir = base / "---"
refused_dir.mkdir()
try:
    d._scaffold_lore_yaml(refused_dir, refused_dir / "lore.yaml")
    print("NOT REFUSED (defect)")
except RuntimeError as error:
    print("refused:", type(error).__name__, error)
print("--- leftovers:", sorted(p.name for p in refused_dir.iterdir()))
```
Output (from the log): `slug line: ['  slug: "odoo_custom"']` · `resolver _project_slug: odoo_custom` · `leftovers: ['.git', 'lore.yaml']` · `refused: SlugRefusal project directory '---' has no valid lore slug (derived '', …); set project.slug by hand in the project's lore.yaml, or rename the directory (project …/---)` · `--- leftovers: []`.

## Anything in the reference not demanded by a test or the brief
- I did not copy the reference's `return` after validation, which left dead code below it. My scaffold is staged and atomic instead.
- Where the reference used a raw sqlite writer, mine is a `ManifestOwner` class (same storage; see F-A).
- Its container-first short-circuit was replaced by the ruling's literal OR (Reading 2).
