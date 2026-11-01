<!-- Extracted 2026-10-31 by lead lore-fix from agent source-trace-165's hand-back message; the harness refused the subagent's own report write. -->

brief-base v21 read

## SUMMARY
- State: done. Read-only. Deviations: none. Capability check: every tool the brief asked for worked; the awk sweep command was not DENIED.
- Packages considered: none (no mechanism specified). Odoo-20 portability: n/a (no Odoo seam touched). Reuse ledger: none (no new symbols). Haiku: 0 spawned (no test runs; execution probes ran inline as read-only `podman run --rm --network=none`).
- Graded: acbce73 · HEAD-at-report: acbce73 · SAME. The image `localhost/lore:latest` (id 4312207128bb…, the one lore-lore runs) was built at LORE_VERSION=0f5f2dc, 699 commits behind HEAD. Between 0f5f2dc and acbce73 the snapshot-relevant files changed only in `index/cli.py` and `scout.py`, and only in how the store is built (`build_store`). Nothing about the snapshot root changed.
- Q1: 79 hits for the literal `/source` across all 1620 tracked files (1618 opened; the other 2 are empty). Zero READERs. The only producer is `skills/lore-deploy/scripts/lore_deploy.py::_launch_container`, which adds the bind. The rest is comments, docstrings, prose, or unrelated text (`signature/source`, `loremaster/source/…`, tokenizer tokens). The baked image's 102 lore member files contain only stale docstrings and tokenizer tokens.
- Q2: every runtime snapshot reader roots at `Path.home()/docker/mcp/lore-snapshot`, which is `/home/lore/docker/mcp/lore-snapshot` in the image (probed). That root comes from `server._DEFAULT_SNAPSHOT_ROOT`, `index/cli.py::_DEFAULT_SNAPSHOT_ROOT` and `scout.py::_DEFAULT_SNAPSHOT_ROOT`, and reaches disk through `Indexer` and `graph_roots`. No served tool reads the snapshot from disk: `lore_read` is store-backed (`StoreReadTool`), and `ReadFileTool` is never constructed in production.
- Q3: the only redirects are `--snapshot-root` on `loremaster.index` and on `loremaster.scout`, plus `$HOME`, because `Path.home()` follows it. `loremaster.server` has no flag, no env var and no lore.yaml key for it. Nothing anywhere points any of these at `/source`.
- Q4: the Containerfile has no mkdir, VOLUME, ENV or chown for `/source`; it appears only in comments. The image's `Config.Volumes` is empty and `/source` does not exist in it (probed).
- Q5: no test asserts the `/source` mount. The deploy tests stub the static-root count to "0", so the static-mount branch is never run. Dropping `/source` needs no test change, but the replacement bind would also be untested (gap, §5).
- Discriminating probe, real `Indexer._snapshot_materialized` run in the image, with lore.yaml's 3 static tiers:
  - `/source`-only bind (the current lore_deploy shape): False ×3;
  - bind at the server path only, no `/source`: True ×3;
  - no bind: False ×3.
- Flags the operator should see (§6):
  - (a) Every re-acquire path crashes inside the container whatever the binds: the corpus `source:` dirs are not mounted, so you get FileNotFoundError; even when they are, the snapshot is `:ro`, so you get EROFS (probed). Triggers: a lore.yaml `version:` bump, a lost snapshot, or a fingerprint rebuild (`rebuild_all` / `is_rebuild`).
  - (b) `_launch_container` silently skips the bind when the host `SNAPSHOT_ROOT` is missing.
  - (c) Stale docstrings claim the snapshot is served from `/source`.
- Lore friction: the `/source` sweep was a textual fallback (non-symbol seam, a legitimate case (b)). It was not filed to `lore_findings` because the writable set is the report only, so the lead may want to file it.
- **VERDICT: SAFE-TO-DROP. Confidence HIGH.** Nothing in the repo or the shipped image reads `/source`, and the guard that #165 trips is satisfied by the server-path bind alone (probe C). The skill should replace `-v SNAPSHOT_ROOT:/source:ro` with `-v SNAPSHOT_ROOT:/home/lore/docker/mcp/lore-snapshot:ro` (CONTAINER_HOME-derived), not add a second bind. Bound: that is HIGH for the current static-tier set and the image at 0f5f2dc. It does not cover an extension SourceProvider; none exists in the repo.

Receipt pointers: §1 per-hit table · §2 data-flow map · §3 probes (instruments pasted verbatim) · §4 redirection · §5 tests · §6 flags.

---

## 0. Method and instruments
- The literal sweep used the brief's command exactly, from the repo root:
  `git ls-files -z | xargs -0 awk 'index($0,"/source"){print FILENAME":"FNR": "substr($0,1,200)}' 2>/dev/null`
  It was a textual fallback because `/source` is a non-symbol seam; the lore index cannot see literals in comments, YAML or Containerfile prose.
- I checked that the sweep could not have silently no-opped (awk aborts its batch on an unopenable file, and stderr was suppressed):
  `git ls-files -z | xargs -0 awk 'FNR==1{n++} index($0,"/source"){h++} END{print "files_opened="n" hits="h}'`
  It printed one END line, `files_opened=1618 hits=79`. `git ls-files | wc -l` gives 1620; the 2 missing files are empty, so FNR==1 never fires for them; `test -s` counted 2 EMPTY. So the sweep was one awk invocation over every non-empty tracked file.
- Alternate spellings checked: `source:ro`, `Path("/source`, `/ "source"`, a `"source"` joined to `"/"`. No new hits; every hit was already among the 79.
- Lore was used first: `lore_index()` showed root `/workspace` at git_ref acbce73, the same as HEAD, with the last sweep 74 s before the query. `lore_impact(loremaster.source.snapshot.SnapshotLayout)` listed its consumers as `index.indexer`, `Indexer.__init__`, `graph_roots`, `read_file`, `local_directory`, `LocalDirectorySourceProvider.acquire`. `lore_impact(loremaster.read_file)` gave one production consumer, `store_read`. A non-test textual sweep for construction sites (`SnapshotLayout(`, `ReadFileTool(`, `_DEFAULT_SNAPSHOT_ROOT`, `snapshot_root=`, `--snapshot-root`) agreed with lore.

## 1. Per-hit table: all 79 literal `/source` hits (acbce73)
Verdict key:
- DOCSTRING: a code comment, docstring or doc prose that mentions the mount; it runs nothing.
- UNRELATED: a different "…/source" string.
- WRITER: the site that produces the bind.
- READER: code that reads the path. There are 0 READER and 0 TEST-ASSERT hits.

| # | file:line | verdict | note |
|---|---|---|---|
| 1 | .claude/agents/package-scout.md:146 | UNRELATED | "signature/source" |
| 2 | Containerfile:8 | DOCSTRING | header comment; stale claim that the snapshot is at /source |
| 3 | Containerfile:102 | DOCSTRING | comment, not a `VOLUME` or mkdir |
| 4 | Containerfile:167 | DOCSTRING | example run invocation (comment) |
| 5 | Containerfile:186 | DOCSTRING | example run invocation (comment) |
| 6 | EXTENDING.md:372 | UNRELATED | module path `loremaster/source/snapshot.py` |
| 7 | LORE_EXTERNAL_REVIEW.md:125 | UNRELATED | "fact/source confidence" |
| 8 | docs/design/2026-07-31-packet39-google-oauth.md:330 | DOCSTRING | #165 prose |
| 9 | docs/design/2026-08-01-google-auth-restart-runbook.md:87 | DOCSTRING | #165 prose |
| 10 | docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629 | UNRELATED | `[source_book` |
| 11 | docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED | "labels/source" |
| 12 | docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151 | UNRELATED | "served/source" |
| 13 | docs/plans/v2/03b-comms-message-surface.md:69 | DOCSTRING | hand-rolled mount prose |
| 14 | docs/plans/v2/10-d-weak-match-disarm.md:82 | DOCSTRING | landmine prose |
| 15 | docs/plans/v2/10-d-weak-match-disarm.md:83 | DOCSTRING | landmine prose |
| 16 | docs/plans/v2/11c-index-boot-reconcile-honesty.md:80 | DOCSTRING | #165/#166 prose |
| 17 | docs/plans/v2/19-lore-deploy-rework.md:15 | DOCSTRING | "DISSOLVES #165" |
| 18 | docs/plans/v2/19-lore-deploy-rework.md:22 | DOCSTRING | mismatch prose |
| 19 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | DOCSTRING | landmine prose |
| 20 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | DOCSTRING | landmine prose |
| 21 | docs/plans/v2/65-hosted-write-joint-cutover.md:33 | DOCSTRING | landmine prose |
| 22 | docs/plans/v2/65-hosted-write-joint-cutover.md:130 | DOCSTRING | `/source:ro ×2` recreate recipe (prose) |
| 23 | docs/plans/v2/INDEX.md:269 | DOCSTRING | log prose |
| 24 | docs/plans/v2/INDEX.md:581 | DOCSTRING | log prose |
| 25 | docs/plans/v2/INDEX.md:1055 | DOCSTRING | log prose |
| 26 | docs/plans/v2/INDEX.md:1058 | DOCSTRING | log prose |
| 27 | docs/plans/v2/INDEX.md:1748 | DOCSTRING | recreate recipe prose (`/source:ro ×2`) |
| 28 | docs/plans/v2/INDEX.md:1752 | DOCSTRING | log prose |
| 29 | docs/plans/v2/INDEX.md:1785 | DOCSTRING | log prose |
| 30 | docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED | "ident/source/llm_summary" |
| 31 | docs/plans/v2/receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52 | UNRELATED | "tiers/sources" |
| 32 | docs/plans/v2/receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117 | DOCSTRING | says "mounted at the path the server READS, never `/source`", consistent with this verdict |
| 33 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92 | UNRELATED | dndbeyond URL `/sources/` |
| 34 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564 | UNRELATED | URL `/sources/` |
| 35 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169 | UNRELATED | module path `loremaster/source/local_directory.py` |
| 36 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448 | DOCSTRING | landmine prose |
| 37 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609 | DOCSTRING | landmine prose |
| 38 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283 | DOCSTRING | landmine prose |
| 39 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304 | DOCSTRING | "no `/source`/git break" |
| 40 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733 | DOCSTRING | landmine prose |
| 41 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734 | DOCSTRING | landmine prose |
| 42 | docs/plans/v2/receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201 | UNRELATED | "read-only/source leg" |
| 43 | docs/plans/v2/receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70 | UNRELATED | "AST/source pin" |
| 44 | docs/plans/v2/receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432 | UNRELATED | "AST/source guard" |
| 45 | docs/plans/v2/receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17 | DOCSTRING | landmine prose |
| 46 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-lead-59.md:146 | DOCSTRING | landmine prose |
| 47 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-sweep-59.md:319 | UNRELATED | "signature/source" |
| 48 | docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115 | UNRELATED | "signature/source" |
| 49 | docs/plans/v2/receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68 | UNRELATED | "scheme/source" |
| 50 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-build-48b.md:11 | UNRELATED | "signature/source" |
| 51 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-builder-48b.md:11 | UNRELATED | "signature/source" |
| 52 | docs/plans/v2/receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293 | UNRELATED | "package/source" |
| 53 | docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52 | UNRELATED | "labels/source" |
| 54 | docs/plans/v2/receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58 | DOCSTRING | landmine prose |
| 55 | docs/plans/v2/receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98 | UNRELATED | "AST/source pin" |
| 56 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110 | UNRELATED | log line, path `loremaster/loremaster/source/__init__.py` |
| 57 | …/lore-lore-podman.log:111 | UNRELATED | log line, path `…/source/local_directory.py` |
| 58 | …/lore-lore-podman.log:112 | UNRELATED | log line, path `…/source/snapshot.py` |
| 59 | docs/plans/v2/receipts/2026-10-04-531-536/REPORT-fix531.md:190 | UNRELATED | module path `…/source/local_directory.py` |
| 60 | loremaster/loremaster/index/indexer.py:395 | DOCSTRING | `Indexer.__init__` docstring, stale ("bind-mounted `:ro` at `/source` in the live server") |
| 61 | loremaster/loremaster/source/snapshot.py:6 | DOCSTRING | module docstring, stale |
| 62 | loremaster/loremaster/source/snapshot.py:70 | DOCSTRING | `SnapshotLayout` class docstring, stale |
| 63 | loremaster/tests/test_config.py:96 | UNRELATED | fixture value `installed_modules_file: "/source/installed.txt"` for the odoo extension config; never a mount |
| 64 | loremaster/tests/test_config.py:305 | UNRELATED | asserts that same string round-trips through config; it does not assert the mount, and dropping `/source` does not affect it |
| 65 | loremaster/tests/test_mcp_server.py:1719 | UNRELATED | "auto/summary/source" |
| 66 | loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9 | UNRELATED | "labels/source" |
| 67 | loremaster/tests/test_render_slot_inventory.py:168 | UNRELATED | "store/source-minted" |
| 68 | loremaster/tests/test_search.py:2870 | UNRELATED | "summary/source/auto" |
| 69 | loremaster/tests/test_source.py:6 | DOCSTRING | module docstring, stale |
| 70 | lorescribe/tests/test_astroid_parse.py:828 | UNRELATED | "chunk_type/source's" |
| 71 | loresigil/loresigil/data/voyage4_tokenizer.json:54621 | UNRELATED | BPE vocab token `"/source"` |
| 72 | loresigil/loresigil/data/voyage4_tokenizer.json:96938 | UNRELATED | BPE vocab token `"/sources"` |
| 73 | skills/lore-deploy/references/lifecycle.md:18 | DOCSTRING | skill reference prose, stale |
| 74 | skills/lore-deploy/references/lifecycle.md:19 | DOCSTRING | skill reference prose, stale |
| 75 | skills/lore-deploy/references/lifecycle.md:146 | DOCSTRING | example run invocation |
| 76 | skills/lore-deploy/scripts/lore_deploy.py:662 | DOCSTRING | `_launch_container` docstring |
| 77 | skills/lore-deploy/scripts/lore_deploy.py:684 | WRITER | `_launch_container` appends `-v {SNAPSHOT_ROOT}:/source:ro`; the only executable `/source` site, and a producer with no reader |
| 78 | skills/lore-deploy/scripts/test_lore_deploy.py:39 | DOCSTRING | test comment ("no /source mount"); the stub returns "0" |
| 79 | skills/lore-deploy/scripts/test_lore_deploy.py:219 | DOCSTRING | `_stub_read_config_field` comment; it returns "0" for static |

Image-side sweep (probe P1, §3): 102 baked files under the four members' `__path__` (`.py/.yaml/.toml/.sh/.txt/.md/.json/.cfg`). Hits:
- `snapshot.py:6`, `snapshot.py:70` and `indexer.py:395`: DOCSTRING;
- `voyage4_tokenizer.json` ×2: UNRELATED.

There is no reader in the artifact. The image COPYs only `pyproject.toml`, `uv.lock` and the four members (Containerfile `COPY` lines 72–77). The skill and `scripts/` are not in the image.

## 2. Data-flow map: runtime readers of the static-tier snapshot root

**Root constants.** All three are probed in the image as `/home/lore/docker/mcp/lore-snapshot` with `HOME=/home/lore`:
- `loremaster.server._DEFAULT_SNAPSHOT_ROOT` (`Path.home()/"docker"/"mcp"/"lore-snapshot"`);
- `loremaster.index.cli._DEFAULT_SNAPSHOT_ROOT`;
- `loremaster.scout._DEFAULT_SNAPSHOT_ROOT`.

**Served server path.** The chain starts at `server.main` → `LoreServer.run`. Inside the lifespan, `_build_context` calls `build_app_context(snapshot_root=_DEFAULT_SNAPSHOT_ROOT)`. `snapshot_root` then flows to exactly two places (non-test sweep plus `lore_impact`):

1. `index.indexer.graph_roots(config, snapshot_root)` builds a `SnapshotLayout`. For every static tier, `tier_roots[tier]` is `materialization_dir(tier)`, and those directories become astroid `project_roots` in `CodeGraph`.
   - Missing or empty root: **silent miss**. Astroid cannot resolve modules there. In lore.yaml today that is moot, because the 3 static tiers hold 0 `.py` files (find count, host snapshot).
2. `Indexer(snapshot_root=…)` sets `self._snapshot_layout = SnapshotLayout(snapshot_root)` (`Indexer.__init__`). Its disk-touching users:
   - **`Indexer._snapshot_materialized(tier)`**: `is_dir()` plus `any(iterdir())` on `materialization_dir(tier)`. It is called by `_index_static_tier` (realtime) and by `_prepare_static_tier_for_collect` (boot / bulk sweep pass 1).
     - Version stamp matches, snapshot present: SKIP. This is the healthy boot.
     - Stamp matches, snapshot missing or empty, tier HAS manifest rows: re-acquire, which **crashes**. This is the #165 path. `provider.acquire` raises FileNotFoundError because `source:` is not mounted (probe P2A/B). Even with the source mounted, `shutil.copytree` into the `:ro` bind fails with `[Errno 30] Read-only file system` (probe P3).
     - Stamp matches, snapshot missing, zero rows: **silent skip** (never built, so nothing is served for that tier).
   - **`LocalDirectorySourceProvider.acquire(tier, snapshot_root)`** (`local_directory.py`) calls `SnapshotLayout(snapshot_root).materialization_dir(tier)` and does a `copytree` there; it is a WRITER. Providers come from `server._build_source_providers`, one per static root carrying `source:`, unless an extension contributes a provider. No extension in the repo defines `acquire`; the only other `def acquire` is the `extension.py` Protocol.
     - Reached from `_index_static_tier`, `_prepare_static_tier_for_collect`, `_acquire_static_snapshot`, `_purge_tier_for_rebuild` and `rebuild_all` / `_rebuild_all_realtime`.
     - The last three acquire **unconditionally**, with no materialised check. So a fingerprint-mismatch rebuild (`server` → `indexer.rebuild_all(fingerprint)`) or an `is_rebuild` sweep **crashes inside the container whatever the binds**: FileNotFoundError, or EROFS if the source is mounted. See flag (a).
   - **`Indexer._tier_base(tier)`** returns `materialization_dir` for static tiers. Its users:
     - `_importable_module_name` / `CodeGraph.importable_module_name` (index time). Missing root: graph path-join fallback, **silent**.
     - `count_files_to_rebuild` → `_count_tier_files`: `not base.exists()` gives 0, **silent** (documented "conservative denominator").
     - `rebuild_graph_only(tier)`, called by the server's store-divergence heal (`server.py` PASS 2, `indexer.rebuild_graph_only`). It runs `(base / row.file_path).read_text()` on indexed `.py` rows. Missing root plus a static tier with `.py` rows would **crash** with FileNotFoundError. For lore.yaml today there are 0 `.py` files in static tiers, so it is moot.
     - The `_walk_and_index` base after a successful acquire.

**Served read tools.** None touches the snapshot on disk.
- `lore_read` is `StoreReadTool(store=write_store, manifest=manifest)` (in `build_app_context`). It serves stored bytes and touches no disk path. It uses `ReadFileTool._resolve_span` (a static method) and imports `ReadFileError`.
- `ReadFileTool`, the filesystem reader that would call `SnapshotLayout.resolve` / `tier_locations`, is **never constructed in production**. The non-test sweep for `ReadFileTool(` returned 0 hits.
- `lore_search`, `lore_get_symbol`, `lore_verify`, `lore_impact`, `lore_dead_code` and `lore_diff` are all store-backed.
- The watcher watches `WATCH_LIVE` roots only (`index/watcher.py`).
- The `build_app_context` docstring's "also the read-file static base" is stale; see flag (c).

**Other in-container entry points.**
- `python -m loremaster.index` (`index/cli.py`) and `python -m loremaster.scout` use the same root via their default or `--snapshot-root`, and reach the same `graph_roots` / `Indexer` paths.
- The skill runs the cold index on the HOST, not in the container (`lore_deploy.py`: `[_loremaster_python(), "-m", "loremaster.index", "--config", …]`, with no `--snapshot-root`). On the host, `Path.home()` is `/home/ejprice`, so it writes `~/docker/mcp/lore-snapshot`, which is the `SNAPSHOT_ROOT` the skill binds.
- The conformance harness (`conformance_run.sh`) mounts only `/workspace:ro`.
- `scripts/snapshot_gc.py` has no on-disk snapshot path; it deals with index snapshots in the store.

## 3. Execution probes (image `localhost/lore:latest` = 4312207128bb…, the image lore-lore runs; all `--network=none --rm`)

Mount shapes and results:
- P1 (no extra mount) found no `/source` READER in the image (see §1). It also printed:
  - `/source exists False`;
  - `home() /home/lore`;
  - all three `_DEFAULT_SNAPSHOT_ROOT` values are `/home/lore/docker/mcp/lore-snapshot`;
  - `__file__` is `/app/loremaster/loremaster/server.py`, i.e. the baked artifact, not a mount.
- P2 runs the real `Indexer._snapshot_materialized`, `graph_roots` and `LocalDirectorySourceProvider.acquire` against the real `/workspace/lore.yaml`, under the production `--userns=keep-id --user 1000:1000 -e HOME=/home/lore`:
  - A, no snapshot bind: materialized False ×3; acquire raises FileNotFoundError (`source directory for tier 'surrealdb-docs' does not exist: /home/ejprice/docker/mcp/lore-corpora/surrealdb-docs`).
  - **B, `/source:ro` only (the current lore_deploy shape): `/source exists: True`, yet materialized False ×3, and acquire raises the same FileNotFoundError.** The `/source` bind is invisible to the guard. This is #165, reproduced.
  - **C, a bind at `/home/lore/docker/mcp/lore-snapshot:ro` only, with no `/source`: materialized True ×3**, which takes the SKIP path and never reaches acquire. This is the positive control: the probe can see a satisfied guard.
  - `graph_roots` tier_roots are identical in A, B and C (`/home/lore/docker/mcp/lore-snapshot/<tier>`), so `/source` never enters the graph either.
- P3 binds the corpus source `:ro` plus the snapshot `:ro` at the server path. Acquire then raises `shutil.Error … [Errno 30] Read-only file system`. The host snapshot mtime was unchanged afterwards (2026-07-23 10:20:45), so the probe wrote nothing.

Instruments, verbatim (they also live in the scratchpad, which is not a durable address, so they are pasted here):

```python
# P1 probe_source165.py
"""Probe (source-trace-165): which snapshot root the BAKED image resolves, and whether
any baked lore member file contains the literal '/source'."""
import os, pathlib, importlib
print("HOME", os.environ.get("HOME"), "home()", pathlib.Path.home())
print("/source exists", os.path.exists("/source"))
print("snapshot dir exists", os.path.exists(pathlib.Path.home() / "docker/mcp/lore-snapshot"))
for mod in ("loremaster.server", "loremaster.index.cli", "loremaster.scout"):
    m = importlib.import_module(mod)
    print(mod, m.__file__, getattr(m, "_DEFAULT_SNAPSHOT_ROOT", None))
hits, scanned = [], 0
for pkg in ("lorerunes", "lorescribe", "loresigil", "loremaster"):
    p = importlib.import_module(pkg)
    roots = list(getattr(p, "__path__", []))
    for root in roots:
        for f in pathlib.Path(root).rglob("*"):
            if f.is_file() and f.suffix in (".py", ".yaml", ".yml", ".toml", ".sh", ".txt", ".md", ".json", ".cfg"):
                scanned += 1
                for n, line in enumerate(f.read_text(errors="replace").splitlines(), 1):
                    if "/source" in line:
                        hits.append(f"{f}:{n}: {line.strip()[:120]}")
print("scanned", scanned)
print("\n".join(hits))
# run: podman run --rm --network=none -e HOME=/home/lore -v <probe>:/probe.py:ro,Z --entrypoint python localhost/lore:latest /probe.py
```

```python
# P2 probe_guard165.py
"""Probe (source-trace-165): drive the REAL Indexer._snapshot_materialized,
graph_roots and LocalDirectorySourceProvider.acquire inside the baked image,
using the server's own default snapshot root and the lore.yaml static roots."""
import os, pathlib
from loremaster import server
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.source.snapshot import SnapshotLayout
from loremaster.source.local_directory import LocalDirectorySourceProvider
root = server._DEFAULT_SNAPSHOT_ROOT
print("server snapshot root:", root, "| /source exists:", os.path.exists("/source"))
from loremaster.config import load_config
cfg = load_config("/workspace/lore.yaml")
statics = [r for r in cfg.roots if r.watch == "static"]
ix = Indexer.__new__(Indexer)
ix._snapshot_layout = SnapshotLayout(root)
for r in statics:
    print(f"tier={r.tier} materialization_dir={ix._snapshot_layout.materialization_dir(r.tier)} "
          f"_snapshot_materialized={ix._snapshot_materialized(r.tier)} source={r.source} source_exists={os.path.exists(r.source)}")
tier_roots, _ = graph_roots(cfg, root)
print("graph tier_roots:", tier_roots)
r = statics[0]
try:
    LocalDirectorySourceProvider(r.tier, pathlib.Path(r.source)).acquire(r.tier, root)
    print("acquire: OK")
except Exception as exc:
    print("acquire raised:", type(exc).__name__, exc)
# run (base): podman run --rm --network=none --userns=keep-id --user $(id -u):$(id -g) -e HOME=/home/lore \
#   -e ANTHROPIC_API_KEY=probe-dummy -v /home/ejprice/PycharmProjects/lore:/workspace:ro -v <probe>:/probe.py:ro \
#   --entrypoint python  [A: nothing | B: -v ~/docker/mcp/lore-snapshot:/source:ro |
#   C: -v ~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro]  localhost/lore:latest /probe.py
```

```python
# P3 probe_roacquire165.py
"""Probe (source-trace-165): with the corpus SOURCE present and the snapshot bound :ro at
the server path, does the real LocalDirectorySourceProvider.acquire succeed?"""
import pathlib
from loremaster import server
from loremaster.source.local_directory import LocalDirectorySourceProvider
src = pathlib.Path("/home/ejprice/docker/mcp/lore-corpora/spectron-docs")
print("source exists:", src.exists())
try:
    LocalDirectorySourceProvider("spectron-docs", src).acquire("spectron-docs", server._DEFAULT_SNAPSHOT_ROOT)
    print("acquire: OK")
except Exception as exc:
    print("acquire raised:", type(exc).__name__, str(exc)[:300])
# run: … -v ~/docker/mcp/lore-corpora/spectron-docs:/home/ejprice/docker/mcp/lore-corpora/spectron-docs:ro \
#        -v ~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro … /probe.py
```

The first P2 attempt failed in `load_config` because `ANTHROPIC_API_KEY` was unset; re-run with a dummy value under `--network=none`. That failure did not count as a result.

## 4. Redirection (Q3)
- `loremaster.server.main` has a single argument, `--config` / `LORE_CONFIG`. **There is no snapshot-root flag, env var or config key**:
  - `config.py` mentions "snapshot" only in prose;
  - a sweep for `environ` together with `SNAPSHOT` gave 0 hits, as did `LORE_SNAPSHOT`.
- `loremaster.index` takes `--snapshot-root` (`index/cli.py`, default `_DEFAULT_SNAPSHOT_ROOT`).
- `loremaster.scout` takes `--snapshot-root` (`scout.py::build_parser`, used in `main`).
- **The implicit redirect is `$HOME`**: all three defaults are `Path.home()`-derived. The skill's `-e HOME=/home/lore` (`CONTAINER_HOME`) is what makes the in-container root `/home/lore/docker/mcp/lore-snapshot`.
- Nothing points any of these at `/source`. The tracked-file sweep for `--snapshot-root` / `snapshot-root` hits only `cli.py`, `scout.py` and the tests (`test_cli.py` 218/257 and `test_scout.py` 457, all using tmp paths or `/data/snap`). The image ENTRYPOINT/CMD is `tini -- python -m loremaster.server`, with no flags (probed via `podman image inspect`).

## 5. Tests (Q5)
- **No test asserts the `/source` mount.**
  - The `test_lore_deploy.py` launch tests (`_launch_container` user/home/manifest test, line ~39) and `_stub_read_config_field` (line ~219) stub the static-root count to "0". The `SNAPSHOT_ROOT` bind branch in `_launch_container` is therefore **never run by any test**.
  - Dropping `/source` needs no test change.
  - **Gap:** the replacement bind would also be unpinned. The branch is exactly where #165 lives, so a test that stubs a static count > 0 and asserts the bind target equals `f"{CONTAINER_HOME}/docker/mcp/lore-snapshot"` (derived, not literal) is the missing pin. Report only; my role writes no tests.
- Snapshot-path tests that stay valid with `/source` dropped:
  - `loremaster/tests/test_source.py` (`SnapshotLayout`; only its module docstring says `/source`);
  - `loremaster/tests/test_indexer.py` (FP-05 `_snapshot_materialized` legs, tmp roots);
  - `test_migration_wire.py:361`, which monkeypatches `server._DEFAULT_SNAPSHOT_ROOT` to a tmp path;
  - `test_cli.py` / `test_scout.py` `--snapshot-root` tmp paths.
- `test_config.py:96/305` `"/source/installed.txt"` is an unrelated odoo-extension fixture string.

## 6. Flags (raised, not fixed; writable set is this report only)
- **(a) In-container re-acquire can never succeed, so every path that reaches `provider.acquire` crashes inside the container.** This is independent of `/source`, and of whether the server-path bind is present.
  - Corpus `source:` dirs (`/home/ejprice/docker/mcp/lore-corpora/*`) are not mounted, which gives FileNotFoundError (P2). Mounting them would still fail, because the snapshot bind is `:ro` (EROFS, P3).
  - Triggers: a `version:` bump in lore.yaml; a lost or empty snapshot on a tier with rows; any fingerprint-mismatch `rebuild_all`; an `is_rebuild` sweep. The rebuild paths acquire unconditionally (`_acquire_static_snapshot`, `_purge_tier_for_rebuild`, `rebuild_all` loop).
  - The design (snapshot.py module docstring) assumes the HOST batch indexer materialises and the server only serves. The server-side acquire is therefore a latent crash, not a fallback.
  - This is outside "drop /source". Do you want it addressed? Packet 19 (lore-deploy rework) seems the natural owner. Options: skip-with-loud-notice in the server when the provider cannot acquire, or a server built without static providers. That is an operator design fork.
- **(b) Silent no-bind.** `_launch_container` appends the snapshot bind only when `SNAPSHOT_ROOT.exists()`. With static roots declared and the host snapshot missing, the container launches without it, and boot then hits flag (a). That is a silent condition feeding a loud crash with an unhelpful message. Suggested shape: fail loud at launch, naming the missing host snapshot and the `loremaster.index` cold-index remedy.
- **(c) Stale prose, a natural-language-surface class.** It claims the snapshot is served from `/source`, or that `snapshot_root` is "the read-file static base":
  - `snapshot.py` module docstring (line 6) and the `SnapshotLayout` docstring (line 70);
  - the `Indexer.__init__` docstring (`indexer.py:395`);
  - `local_directory.py` docstring ("for the live server to bind-mount `:ro`"), which is true but location-agnostic;
  - the `server.build_app_context` docstring ("also the read-file static base"; `ReadFileTool` is not constructed in production);
  - Containerfile comments at 8, 102, 167, 186;
  - `skills/lore-deploy/references/lifecycle.md` 18, 19, 146;
  - the `_launch_container` docstring (`lore_deploy.py:662`);
  - `test_source.py:6`;
  - the deploy-test comments.

  These should change in the same commit that changes the bind. Exact edit: replace "bind-mounted `:ro` at `/source`" with "bind-mounted `:ro` at `$HOME/docker/mcp/lore-snapshot` (`/home/lore/docker/mcp/lore-snapshot` in the container)".
- **(d) Hand-rolled recreate recipes in docs.** `INDEX.md:1748` and `65-hosted-write-joint-cutover.md:130` say `/source:ro ×2`. Once the skill is fixed, their "known-good shape" is two binds where one suffices. Those docs should be updated or annotated.
- **(e) Image currency.** `localhost/lore:latest` was built at 0f5f2dc, 699 commits behind HEAD acbce73. The verdict holds for both: no snapshot-related diff exists between them, and the image-side sweep was clean. Any code shipped after 0f5f2dc is unverified in the artifact until a rebuild; P1 can be re-run then.
- **(f) Lore friction (not filed, writable set).** The `/source` sweep needed the textual fallback, case (b) non-symbol seam: comments, Containerfile and markdown. Lead: file it via `lore_findings` if wanted.
