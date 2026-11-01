brief-base v22 read

## SUMMARY
- **State:** done. Read-only. The only file written is this report, plus a probe script in my session scratchpad that is pasted verbatim in §6.
- **Deviations:** (1) I did not register on `lore_comms`: the brief named no session and it is a one-shot run. (2) I did not file a `lore_findings` row for the textual-sweep fallback, because the brief's writable set is this file only. The lead may file it. (3) No fan-out: everything ran inline (routing table in §7).
- **Packages considered:** none. No mechanism was specified.
- **Odoo-20 portability:** n/a. No Odoo seam was touched.
- **Reuse ledger:** none. No new symbols.
- **Graded:** acbce73 · HEAD-at-report: acbce73 · SAME. The image probed was `localhost/lore:latest`, built 2026-08-18 from `0f5f2dc`, which is 699 commits behind HEAD. Between the two, the snapshot-relevant code drifted only in `index/cli.py`, where the store was moved onto the `build_store` factory. Nothing touching the snapshot changed (§5).
- **Q1:** a bare `/source` sweep over all 1620 tracked files found 79 hits. Exactly ONE is functional: the **WRITER** in `lore_deploy.py::_launch_container` (`-v {SNAPSHOT_ROOT}:/source:ro`). There are **zero READERS**. The other 78 are comments, docstrings, docs, test comments or fixtures, or unrelated `x/source` substrings (§2).
- **Q2:** every runtime snapshot reader goes through `SnapshotLayout(<root>)`, and every root comes from `Path.home()/"docker"/"mcp"/"lore-snapshot"`. With `HOME=/home/lore` that is `/home/lore/docker/mcp/lore-snapshot`. The served `lore_read` tool reads from the store, not from disk under the snapshot (§3).
- **Q3:** the root can be redirected only by `--snapshot-root`, a flag on the `loremaster.index` and `loremaster.scout` CLIs. The served server takes no flag, env var or `lore.yaml` key; only `HOME` moves it. Nothing anywhere points at `/source` (§4).
- **Q4:** the Containerfile has no `mkdir`, `VOLUME`, `ENV` or `chown` for `/source`. It appears only in 4 comment lines. Probed: `/source` does not exist in the image (§5).
- **Q5:** no test asserts that a `/source` mount is present, or that a snapshot bind exists when static roots are configured. Dropping `/source` turns no test red. Two test comments and one docstring would go stale (§2).
- **Execution proof (§6):** the real `Indexer._snapshot_materialized` was run in the image under three binds.
  - Leg A, bind only at `/source`: False for all 3 tiers.
  - Leg C, no bind at all: identical to Leg A.
  - Leg B, bind only at the HOME path: True for all 3 tiers.
  - So `/source` has no effect on the code path.
- **Not caused by `/source`, but needs a decision:** inside the container, a static tier can NEVER be re-acquired. The `lore.yaml` `source:` paths are host paths that are not mounted, and the snapshot is mounted `:ro`. Any version bump, `rebuild_all`, or lost-snapshot case therefore raises `FileNotFoundError`, which no per-tier handler catches (§3, row R5).
- **Decisions needed:**
  - D1: drop `/source` and bind the snapshot at `CONTAINER_HOME/docker/mcp/lore-snapshot` (I recommend yes).
  - D2: the snapshot path is hardcoded in 4 places (`server`, `index/cli`, `scout`, `lore_deploy`), which is a ONE-IMPLEMENTATION violation. Should one owner hold it?
  - D3: add a pin for the static-root branch of `_launch_container`.
  - D4: the in-container re-acquire hazard above.
- **VERDICT: SAFE-TO-DROP — HIGH.** Nothing reads `/source`. The bind must move to `/home/lore/docker/mcp/lore-snapshot:ro` with `-e HOME=/home/lore` kept: the code reads that path and nothing else. This rests on the source read in §3 and the execution probe in §6.

---

## 1. Method and coverage
- **Sweep (textual fallback).** `/source` is a non-symbol textual seam (container paths, comments, docs), so lore's symbol graph cannot enumerate it; the brief also mandated an exhaustive sweep. I used the brief's exact non-grep command (no DENIED):
  `git ls-files -z | xargs -0 awk 'index($0,"/source"){print FILENAME":"FNR": "substr($0,1,200)}'`
  - Coverage: `files_opened=1620` against `git ls-files | wc -l` = 1620, one xargs batch, 79 hits.
  - The untracked `docs/plans/v2/receipts/2026-10-31-165/` is not in `git ls-files`, so it was never read, as the brief required.
- **Supplementary sweeps** over all 517–522 `*.py *.sh *.yaml *.yml *.toml Containerfile` files (files_opened equals the ls-files count):
  - `snapshot_root|SNAPSHOT_ROOT|lore-snapshot|SnapshotLayout(|LORE_SNAPSHOT`, used to find every root constructor.
  - A constructed `"source"` joined to `"/"` / `os.sep`: 0 hits.
  - `environ` combined with `SNAPSHOT|SOURCE`: 0 hits.
- **lore (index fresh):** `lore_index` reported git_ref `acbce73` = HEAD and a sweep 43 s old.
  - `lore_impact(SnapshotLayout)`: 6 production consumers, all in `index/indexer.py`, `read_file.py` and `source/local_directory.py`.
  - `lore_impact(ReadFileTool)`: 1 production consumer, `store_read`, and only through a static helper (§3).
- **In-image scan.** I walked 9669 `.py/.sh/.yaml/.toml/.cfg/.pth` files under `/app/.venv/lib` and the four members, looking for quoted `"/source"`, `'/source'`, `/source:`, `"/source/`, `'/source/` and ``` ``/source`` ```.
  - Hits were found only in our own members: 3 docstrings and 3 test lines.
  - Third-party site-packages had none.
  - This pattern is narrower than the repo sweep; it is a complement to it, not a replacement.

## 2. Per-hit table (Q1 + Q5) — all 79 hits from the bare sweep at acbce73
Verdict key:
- **WRITER**: creates the mount.
- **READER**: reads the path.
- **DOCSTRING**: a code comment or docstring that names the mount.
- **DOC**: prose in a doc or plan that names the mount.
- **TEST-ASSERT / TEST-FIXTURE / TEST-COMMENT**: test-tree hits, by role.
- **UNRELATED**: the substring belongs to something else (`x/source`, a module path, a URL, a vocab token).

| # | file:line | verdict | note |
|---|---|---|---|
| 1 | .claude/agents/package-scout.md:146 | UNRELATED | "signature/source" |
| 2 | Containerfile:8 | DOCSTRING | header comment: "optional read-only snapshot … at /source" (stale claim) |
| 3 | Containerfile:102 | DOCSTRING | comment: keep-id keeps `/source` readable |
| 4 | Containerfile:167 | DOCSTRING | run-recipe comment `[ -v <snapshot>:/source:ro ]` |
| 5 | Containerfile:186 | DOCSTRING | run-recipe comment `-v <snapshot>:/source:ro` |
| 6 | EXTENDING.md:372 | UNRELATED | module path `loremaster/source/snapshot.py` |
| 7 | LORE_EXTERNAL_REVIEW.md:125 | UNRELATED | "fact/source confidence" |
| 8 | docs/design/2026-07-31-packet39-google-oauth.md:330 | DOC | #165 recreate re-mounts `/source` |
| 9 | docs/design/2026-08-01-google-auth-restart-runbook.md:87 | DOC | #165 open |
| 10 | docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629 | UNRELATED | "file_path/source_book" |
| 11 | docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED | "labels/source/importance" |
| 12 | docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151 | UNRELATED | "served/source prose" |
| 13 | docs/plans/v2/03b-comms-message-surface.md:69 | DOC | hand-rolled `/source` mount |
| 14 | docs/plans/v2/10-d-weak-match-disarm.md:82 | DOC | hand-rolled mount landmine |
| 15 | docs/plans/v2/10-d-weak-match-disarm.md:83 | DOC | same |
| 16 | docs/plans/v2/11c-index-boot-reconcile-honesty.md:80 | DOC | #165/#166 |
| 17 | docs/plans/v2/19-lore-deploy-rework.md:15 | DOC | "DISSOLVES #165" |
| 18 | docs/plans/v2/19-lore-deploy-rework.md:22 | DOC | `/source` mismatch |
| 19 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | DOC | landmine |
| 20 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | DOC | landmine |
| 21 | docs/plans/v2/65-hosted-write-joint-cutover.md:33 | DOC | landmine |
| 22 | docs/plans/v2/65-hosted-write-joint-cutover.md:130 | DOC | "`/source:ro` ×2" CreateCommand shape |
| 23 | docs/plans/v2/INDEX.md:269 | DOC | log |
| 24 | docs/plans/v2/INDEX.md:581 | DOC | landmine |
| 25 | docs/plans/v2/INDEX.md:1055 | DOC | log |
| 26 | docs/plans/v2/INDEX.md:1058 | DOC | log |
| 27 | docs/plans/v2/INDEX.md:1748 | DOC | log, ×2 shape |
| 28 | docs/plans/v2/INDEX.md:1752 | DOC | log |
| 29 | docs/plans/v2/INDEX.md:1785 | DOC | log |
| 30 | docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED | "ident/source/llm_summary" |
| 31 | receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52 | UNRELATED | "tiers/sources" |
| 32 | receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117 | DOC | already says "mounted at the path the server READS, never `/source`" |
| 33 | receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92 | UNRELATED | dndbeyond URL `/sources/` |
| 34 | receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564 | UNRELATED | URL `/sources/` |
| 35 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169 | UNRELATED | module path |
| 36 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448 | DOC | landmine |
| 37 | receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609 | DOC | landmine |
| 38 | receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283 | DOC | landmine |
| 39 | receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304 | DOC | "no `/source`/git break" |
| 40 | receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733 | DOC | landmine |
| 41 | receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734 | DOC | landmine |
| 42 | receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201 | UNRELATED | "read-only/source leg" |
| 43 | receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70 | UNRELATED | "AST/source pin" (past the 200-char truncation; checked) |
| 44 | receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432 | UNRELATED | "AST/source guard" |
| 45 | receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17 | DOC | landmine (past truncation; checked) |
| 46 | receipts/2026-08-16-packet59/REPORT-lead-59.md:146 | DOC | landmine |
| 47 | receipts/2026-08-16-packet59/REPORT-sweep-59.md:319 | UNRELATED | "signature/source/probe" |
| 48 | receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115 | UNRELATED | "signature/source" |
| 49 | receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68 | UNRELATED | "scheme/source" (past truncation; checked) |
| 50 | receipts/2026-08-20-packet48/REPORT-build-48b.md:11 | UNRELATED | "signature/source" (past truncation; checked) |
| 51 | receipts/2026-08-20-packet48/REPORT-builder-48b.md:11 | UNRELATED | "signature/source" (past truncation; checked) |
| 52 | receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293 | UNRELATED | "package/source" |
| 53 | receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52 | UNRELATED | "labels/source/expires_at" |
| 54 | receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58 | DOC | landmine |
| 55 | receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98 | UNRELATED | "AST/source pin" |
| 56 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110 | UNRELATED | log `file_path` `loremaster/loremaster/source/__init__.py` |
| 57 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:111 | UNRELATED | log `…/source/local_directory.py` |
| 58 | receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:112 | UNRELATED | log `…/source/snapshot.py` |
| 59 | receipts/2026-10-04-531-536/REPORT-fix531.md:190 | UNRELATED | module path |
| 60 | loremaster/loremaster/index/indexer.py:395 | DOCSTRING | `Indexer.__init__` arg doc: "bind-mounted `:ro` at `/source` in the live server" (FALSE at acbce73) |
| 61 | loremaster/loremaster/source/snapshot.py:6 | DOCSTRING | module docstring: "server bind-mounts that dir `:ro` at `/source`" (FALSE) |
| 62 | loremaster/loremaster/source/snapshot.py:70 | DOCSTRING | `SnapshotLayout` arg doc, same false claim |
| 63 | loremaster/tests/test_config.py:96 | TEST-FIXTURE | opaque odoo-extension config value `installed_modules_file: "/source/installed.txt"`; no production code reads `installed_modules_file` (0 hits outside this file) |
| 64 | loremaster/tests/test_config.py:305 | TEST-ASSERT | asserts that config round-trip of the opaque string; NOT a mount assertion; unaffected by dropping `/source` |
| 65 | loremaster/tests/test_mcp_server.py:1719 | UNRELATED | "auto/summary/source" |
| 66 | loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9 | UNRELATED | "labels/source/expires_at" |
| 67 | loremaster/tests/test_render_slot_inventory.py:168 | UNRELATED | "store/source-minted" |
| 68 | loremaster/tests/test_search.py:2870 | UNRELATED | "summary/source/auto" |
| 69 | loremaster/tests/test_source.py:6 | DOCSTRING | test-module docstring repeating the mount claim |
| 70 | lorescribe/tests/test_astroid_parse.py:828 | UNRELATED | "chunk_type/source's" |
| 71 | loresigil/loresigil/data/voyage4_tokenizer.json:54621 | UNRELATED | vocab token `"/source"` |
| 72 | loresigil/loresigil/data/voyage4_tokenizer.json:96938 | UNRELATED | vocab token `"/sources"` |
| 73 | skills/lore-deploy/references/lifecycle.md:18 | DOC | teaches the `/source` bind (skill reference) |
| 74 | skills/lore-deploy/references/lifecycle.md:19 | DOC | same |
| 75 | skills/lore-deploy/references/lifecycle.md:146 | DOC | run recipe with `/source:ro` |
| 76 | skills/lore-deploy/scripts/lore_deploy.py:662 | DOCSTRING | `_launch_container` docstring |
| 77 | skills/lore-deploy/scripts/lore_deploy.py:684 | **WRITER** | `cmd += ["-v", f"{SNAPSHOT_ROOT}:/source:ro"]` in `_launch_container`; the ONLY functional `/source` site |
| 78 | skills/lore-deploy/scripts/test_lore_deploy.py:39 | TEST-COMMENT | "No static roots → no /source mount" (stubs `_read_config_field` → "0") |
| 79 | skills/lore-deploy/scripts/test_lore_deploy.py:219 | TEST-COMMENT | `_stub_read_config_field` returns "0" for static count |

Tallies (counted row by row): WRITER 1 · READER 0 · DOCSTRING 9 · DOC 32 · TEST-ASSERT 1 · TEST-FIXTURE 1 · TEST-COMMENT 2 · UNRELATED 33 = 79.

**Q5, measured from the table and the test file.** The static-roots branch of `_launch_container` has no test: both deploy tests stub the static count to "0", and no test asserts the `/source` bind or any snapshot bind. Dropping `/source` turns zero tests red.
- The wrong-path bind is the #165 defect, and it is unpinned today.
- A fix should add a pin asserting that the snapshot bind's container target equals `CONTAINER_HOME/docker/mcp/lore-snapshot`. The strongest form derives the target from the server's own default rather than restating it (decision D3).

Stale prose to update when `/source` is dropped:
- rows 2–5, 60–62, 69 and 76 (code and test docstrings and comments);
- rows 73–75, the skill reference that teaches the mount;
- `MEMORY.md`'s landmine line.

## 3. Runtime data-flow map (Q2): who reads the snapshot on disk, with what root
Root provenance: all four defaults are `Path.home() / "docker" / "mcp" / "lore-snapshot"`. Each one was probed in the image with `HOME=/home/lore`, and each resolves to `/home/lore/docker/mcp/lore-snapshot` (§5).
- `server._DEFAULT_SNAPSHOT_ROOT` (server.py, module level) is passed by the production lifespan `_build_context` as `build_app_context(snapshot_root=_DEFAULT_SNAPSHOT_ROOT)`.
- `index.cli._DEFAULT_SNAPSHOT_ROOT`
- `scout._DEFAULT_SNAPSHOT_ROOT`
- `lore_deploy.SNAPSHOT_ROOT`: host side, used only for the bind source and the `-v` decision.

| # | reader (symbol) | constructed by / root | touches disk how | missing/empty snapshot root → |
|---|---|---|---|---|
| R1 | `Indexer._snapshot_materialized` | `Indexer.__init__` → `SnapshotLayout(snapshot_root)`; server via `build_app_context`, CLI via `index.cli._run` | `materialization_dir(tier).is_dir()` + `iterdir()` | returns False → `_index_static_tier` / `_prepare_static_tier_for_collect` fall through to **re-acquire** (R5) when the manifest has rows for the tier. This is #165's boot break. Silent miss if the tier has 0 rows (skip). |
| R2 | `Indexer._index_static_tier` / `_prepare_static_tier_for_collect` | same | walks `materialization_dir(tier)` after acquire | only reached after R5; see R5 |
| R3 | `Indexer._tier_base` → `_importable_module_name` (`CodeGraph.importable_module_name(base, path)`), `_count_included_files`, the graph-only heal loop (`base / row.file_path).read_text`) | same | heal reads `.py` rows only (non-`.py` skipped by `_PYTHON_SUFFIX` check); count returns 0 if base missing | count: silent 0 (documented as conservative). Heal: a static tier holding `.py` would hit a `FileNotFoundError` on `read_text`. Current lore.yaml static tiers are `.mdx`/`.surql` only, so this is unreachable today (MEDIUM: from reading, not probed). |
| R4 | `graph_roots(config, snapshot_root)` → `SurrealCodeGraph(tier_roots=…, project_roots=…)` | server `build_app_context`, `index.cli._run`, `Scout.from_config` | astroid resolution base for static tiers' Python (graph.py `_tier_roots.get(tier)`) | silent: astroid finds nothing under a missing base, so references drop as external. Inert for today's non-Python static tiers. |
| R5 | `LocalDirectorySourceProvider.acquire(tier, snapshot_root)` (writer into `SnapshotLayout(snapshot_root).materialization_dir`) | providers from `server._build_source_providers` / `index.cli._source_providers` over `lore.yaml` `source:` | **reads** `source:` (host path `/home/ejprice/docker/mcp/lore-corpora/<tier>`), **writes** the snapshot | **crash:** `FileNotFoundError` naming the source dir, probed in all 3 legs (§6). It propagates: `_index_all_realtime` and the `ReconcileEngine` per-root loop have no per-tier catch, so it surfaces from the boot sweep and from every periodic reconcile. Reached from R1 (lost snapshot + rows), a version bump, `rebuild_all` (unconditional `_acquire_static_snapshot`) and `_purge_tier_for_rebuild`. Even with the source mounted, the copy would fail into a `:ro` snapshot bind. **Independent of `/source`.** |
| R6 | `ReadFileTool._snapshot_layout.resolve` / `tier_locations` | **never instantiated in production.** `lore_impact`: its one prod consumer `store_read` uses only the static `ReadFileTool._resolve_span` | — | none. The served `lore_read` is `StoreReadTool(store=…, manifest=…)` (server `build_app_context`), which serves stored bytes, gets staleness from manifest state/sha, and does no disk read. |
| R7 | `lore_search`, `lore_get_symbol`, `lore_impact`, `lore_verify`, `lore_diff`, `lore_dead_code` | store-backed | no snapshot disk access found (no `SnapshotLayout` consumer outside R1–R6 per `lore_impact` + sweep) | none |
| R8 | in-container conformance harness (`conformance_run.sh`, `conformance_provenance.py`) | — | 0 `/source` and 0 `snapshot_root` hits in `skills/` scripts other than `lore_deploy.py` | none |
| R9 | `lore_deploy` `setup`/`start` indexing | runs `python -m loremaster.index --config …` on the **host** via `_loremaster_python()` (lore_deploy.py `[…, "-m", "loremaster.index", "--config", …]`), no `--snapshot-root` | host default `~/docker/mcp/lore-snapshot` is the WRITER of the snapshot the container reads | n/a inside the container |

Bottom line for Q2: every in-container snapshot reader resolves under `/home/lore/docker/mcp/lore-snapshot`. None resolves under `/source`.

## 4. Redirection (Q3)
- `loremaster.index` (`index/cli.py` `--snapshot-root`, default `_DEFAULT_SNAPSHOT_ROOT`) honours the flag.
- `loremaster.scout` (`scout.py` `--snapshot-root`) honours the flag.
- **The served server has no override.** `_build_context` passes the module constant. There is no `lore.yaml` key (`config.py` mentions "snapshot" only in a `source` docstring and `snapshot_gc` prose) and no env var (environ×SNAPSHOT/SOURCE sweep: 0 hits). Only `HOME` moves it, through `Path.home()`.
- **No invocation anywhere passes `--snapshot-root /source`.**
  - The Containerfile CMD is `python -m loremaster.server` and its ENTRYPOINT is `tini --`.
  - `lore_deploy` runs the index CLI on the host with no flag.
  - The `--snapshot-root` sweep in scripts/ and skills/ found 0 call-site hits.

## 5. Containerfile and image (Q4), probed
- `Containerfile` at acbce73 has no `mkdir`, `VOLUME`, `ENV` or `chown` for `/source`. Its only occurrences are comments (rows 2–5). The only `ENV` lines are `PATH`, `LORE_CONFIG` and `LORE_VERSION`, and `useradd -r … lore` creates `/home/lore`.
- `podman image inspect localhost/lore:latest` showed: Created 2026-08-18, `LORE_VERSION=0f5f2dc`, `vols=map[]`, WorkingDir `/app`, Entrypoint `[/usr/bin/tini --]`, Cmd `[/app/.venv/bin/python -m loremaster.server]`.
- In-image probe (`HOME=/home/lore`, keep-id): all three `_DEFAULT_SNAPSHOT_ROOT` = `/home/lore/docker/mcp/lore-snapshot`; `/source exists: False`; `loremaster.__file__=/app/loremaster/loremaster/__init__.py`.
- Drift between `0f5f2dc` and HEAD on the snapshot path:
  - `git diff --stat` over Containerfile, `source/`, `read_file.py`, `store_read.py`, `index/cli.py` and `lore_deploy.py` touched only `index/cli.py`: the `SurrealStore(...)` → `build_store(config)` swap, which does not involve the snapshot.
  - In `server.py`, `indexer.py` and `scout.py`, the +/- lines mentioning snapshot are comment-only and unrelated ("snapshot-first WAIT", "snapshot_stamper").
- lore-lore's recorded CreateCommand (from the brief's pointer) carries both `-v …/lore-snapshot:/source:ro` and `-v …/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro`. The second bind is the one the code reads.

## 6. Execution probe (instrument — pasted verbatim; it lives in my session scratchpad, which the lead cannot see, so this copy is the durable one)
```python
"""Probe: which container path does the static-tier freshness guard actually read?

Runs INSIDE localhost/lore:latest. Derives the static tiers from the mounted
lore.yaml, then calls the REAL Indexer._snapshot_materialized (bound to a stub
carrying only the layout it reads) over the server's own _DEFAULT_SNAPSHOT_ROOT,
and the REAL LocalDirectorySourceProvider.acquire (the re-acquire fallback).
"""
import os
import sys
import types
from pathlib import Path

import yaml

import loremaster
import loremaster.server as server
from loremaster.index.indexer import Indexer
from loremaster.source.local_directory import LocalDirectorySourceProvider
from loremaster.source.snapshot import SnapshotLayout

config = yaml.safe_load(Path("/workspace/lore.yaml").read_text())
static_roots = [r for r in config["roots"] if r.get("watch") == "static"]
print(f"loremaster.__file__={loremaster.__file__}")
print(f"HOME={os.environ.get('HOME')} server_root={server._DEFAULT_SNAPSHOT_ROOT}")
print(f"/source exists={os.path.exists('/source')} static_tiers={len(static_roots)}")
stub = types.SimpleNamespace(_snapshot_layout=SnapshotLayout(server._DEFAULT_SNAPSHOT_ROOT))
for root in static_roots:
    tier = root["tier"]
    materialized = Indexer._snapshot_materialized(stub, tier)
    try:
        LocalDirectorySourceProvider(tier, Path(root["source"])).acquire(tier, Path("/tmp/probe-snap"))
        acquire = "OK"
    except FileNotFoundError as error:
        acquire = f"FileNotFoundError({error})"
    print(f"tier={tier} materialized={materialized} reacquire={acquire}")
sys.exit(0)
```
Runner, with the common prefix `podman run --rm --network=none --userns=keep-id --user $(id -u):$(id -g) -e HOME=/home/lore -v <repo>:/workspace:ro -v <probe>:/probe.py:ro <EXTRA> --entrypoint python localhost/lore:latest /probe.py`:

| leg | EXTRA | `/source` exists | materialized (surrealdb-docs / surrealql-tests / spectron-docs) | re-acquire |
|---|---|---|---|---|
| A (current skill shape) | `-v ~/docker/mcp/lore-snapshot:/source:ro` | True | False / False / False | FileNotFoundError ×3 |
| B (proposed: no `/source`) | `-v ~/docker/mcp/lore-snapshot:/home/lore/docker/mcp/lore-snapshot:ro` | False | **True / True / True** | FileNotFoundError ×3 |
| C (control: no bind) | none | False | False / False / False | FileNotFoundError ×3 |

What the legs show:
- **A ≡ C.** The `/source` bind changes nothing in the guard's output.
- **B differs.** The probe can see a bind when it is at the right path, which is the positive control.
- All legs exited 0.
- Host snapshot at probe time: `~/docker/mcp/lore-snapshot/{spectron-docs,surrealdb-docs,surrealql-tests}`, all non-empty.

Bound on this probe: it exercises the guard and the provider, not a full server boot. That `FileNotFoundError` propagates out of boot is from reading `_index_all_realtime` and the `ReconcileEngine` loop, which have no per-tier `try`. I did not trace whether the lifespan catches it. #165's recorded boot break is consistent with it propagating. MEDIUM on the exact boot-level outcome; HIGH on the guard result.

## 7. Routing table and fan-out
| step | tier | who | reason |
|---|---|---|---|
| bare `/source` sweep (brief's exact cmd) | 1 | me, inline | on the critical path; 79 lines that I had to read whole to give per-hit verdicts; one command |
| per-hit verdicts (79) | 2 candidate | me, inline | a Sonnet draft would have worked for the ~64 doc/UNRELATED rows. I kept them because the 15 code/test rows needed state from elsewhere (installed_modules_file consumers, docstring truth vs server default), and drafting plus sampling would have cost about as much as doing it. I name this as a deviation from §3 fan-out. |
| data-flow trace, image probes, verdict | 3 | me | the final verdict, plus a probe whose design needs a positive control |

Fan-out: haiku 0 · sonnet 0 · peak 0. No test runs: the brief is read-only and the work needed no test execution.

## 8. Flags for the lead and operator (raised, not acted on)
- **D2, ONE IMPLEMENTATION.** The snapshot-root path policy is hardcoded in four places: `server._DEFAULT_SNAPSHOT_ROOT`, `index.cli._DEFAULT_SNAPSHOT_ROOT`, `scout._DEFAULT_SNAPSHOT_ROOT` and `lore_deploy.SNAPSHOT_ROOT`.
  - The deploy skill's bind target must be the server's root re-based on `CONTAINER_HOME`. Today nothing ties the two together, and that gap is #165's root cause.
  - Also seen, not verified for divergence: `server._build_source_providers` and `index.cli._source_providers` both compose "extension providers + LocalDirectorySourceProvider per static root". These look like two copies of one policy.
- **D4, the in-container re-acquire hazard (R5).** The `lore.yaml` `source:` paths are host-absolute and not mounted, and the snapshot bind is `:ro`, so any re-acquire inside the container crashes. Once `/source` is fixed, the next version bump on a static tier will break boot again, and so will a schema `rebuild_all`, or a deploy where the snapshot bind is missing while rows exist. Should the container ever acquire, or should static tiers always be materialised on the host and only ever skipped in the container?
- **Stale docstrings that make false claims** (rows 60–62, 69, 2–5): these are served-adjacent prose about the mount, and they are false at acbce73.
