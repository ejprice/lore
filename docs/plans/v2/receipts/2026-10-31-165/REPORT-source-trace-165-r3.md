brief-base v23 read

## SUMMARY (measured 2026-10-31 at `acbce73`; image `4312207128bb`, LORE_VERSION `0f5f2dc`)
- state: done
- deviations: none. The summary block runs past brief-base's 15 lines, within the brief's 25-line limit.
- Packages considered: none (no mechanism specified)
- Odoo-20 portability: n/a (no Odoo seam touched)
- Reuse ledger: none (no new production symbols; the probe is a read-only instrument, pasted in §Execution probe)
- Graded: acbce73 · HEAD-at-report: acbce73 · SAME
- Q1: 79 literal `/source` hits (coverage 1618/1620; the 2 unopened files are empty). **0 READERS**, 1 WRITER (`lore_deploy.py` `_launch_container`, the bind), 1 TEST-ASSERT on an Odoo extension-config string (not a mount); the rest are DOCSTRING or UNRELATED.
- Q2: the server's only snapshot root is `server._DEFAULT_SNAPSHOT_ROOT` (`Path.home()/docker/mcp/lore-snapshot` = `/home/lore/…`), used by `graph_roots` (silent miss) and `Indexer` (boot guard → re-acquire → FileNotFoundError crash when rows exist; `rebuild_graph_only` crash on `.py` rows). `lore_read` serves from the store, so disk plays no part.
- Q3: no flag, env var or config key redirects the server root. `HOME` is the only selector. Nothing passes `/source` (`LORE_SNAPSHOT` sweep: 0 hits).
- Q4: the Containerfile mentions `/source` only in comments. The image has no VOLUME, no mkdir and no chown, and has neither `/source` nor `/home/lore` in its fs.
- Q5: no test at HEAD asserts the `/source` bind; the static branch is stubbed to "0". #165's claim of a test asserting the mount does not hold at HEAD. A boot invariant is still owed.
- Probe (real `Indexer._snapshot_materialized` + `graph_roots`, inside the image, with a `/source` positive control): the guard over the default root is False×3 with only `/source` bound, True×3 with only the home path bound, False×3 with neither. The control is True×3 on `/source`. Source-only ≡ neither on every server-facing fact.
- decisions-needed: (1) operator: a `:ro` bind means no in-container re-acquire can succeed in any mount shape (§Verdict flag 3). Do you want that raised? (2) The stale-prose list (§Verdict flag 1) goes to whoever ships the change.
- pointers: §Q1 tables · §Q2 map · §Execution probe · W=`scratchpad/r3/trace/` (sweep.txt, sites-*.txt, image.txt, probe-*.txt, verdicts-draft.md)
- **VERDICT: SAFE-TO-DROP** the `/source` bind, provided the host snapshot is bound at `/home/lore/docker/mcp/lore-snapshot` with `HOME=/home/lore` kept. **Confidence HIGH:** static sweep, code trace and in-image execution agree. Residual: the probe did not run a full server boot (no store), so the crash consequence comes from the code plus #165's tracebacks.

## Routing table (written before first sweep; all steps routed by the brief)
| step | tier | who | reason |
|---|---|---|---|
| 1 literal `/source` sweep | 1 | haiku-worker | brief-routed |
| 2 construction-site sweeps (8 patterns) | 1 | haiku-worker | brief-routed |
| 3 Containerfile + image facts | 1 | haiku-worker | brief-routed |
| 4 non-code hit verdicts draft | 2 | Sonnet general-purpose | brief-routed; code/test hits kept by me (verdict depends on state elsewhere) |
| 5 Q2 data-flow trace, Q3/Q5 reading, probe design | 3 | me | brief-routed |
| 6 probe run, 3 mount legs | 1 | haiku-worker | brief-routed |
| 7 verdict | 3 | me | brief-routed |

`Fan-out: haiku 4 · sonnet 1 · peak 3` (steps 1–3 concurrent; step 4 and step 6 each alone with my tier-3 work).
Test runs: none (no pytest; the probe is an execution probe, run by a haiku-worker per brief step 6).

## Capability check
Demanded vs had: everything the brief names was available (Agent, Bash, podman, lore MCP). Lore index fresh: `lore_index()` at
2026-10-31T15:38Z, last_sweep 218 s old, watched root `/workspace` @ `acbce73` (= my HEAD). No session edits to source → no reconcile needed.
Grep fallback: none — all literal sweeps used `awk index()` over `git ls-files` (brief-specified), which is the
"non-symbol textual seam" case (§dogfood 3b) — said out loud here; not lore friction (lore cannot search a literal substring by design).
Independence: no file under `docs/plans/v2/receipts/2026-10-31-165/` or `REPORT-source-*-165-r2.md` was opened. Both are UNTRACKED
(`git status` at start), so the `git ls-files` sweeps never touched them; no lore_search was issued, so no hit from them surfaced.

## Q1 — every literal `/source` (79 hits; coverage `files_opened=1618 hits=79` vs `git ls-files | wc -l` = 1620)
The 2 unopened files are empty: `loremaster/loremaster/index/__init__.py`, `lorescribe/tests/__init__.py` (awk FNR==1 never fires) → coverage complete.
Gitignored-but-live config checked separately: `lore.yaml` opened=1 hits=0; `.mcp.json` opened=1 hits=0. Env-file
`~/docker/mcp/lore-secrets/lore.env` KEY NAMES only (values not read): LORE_TEI_KEY, QDRANT__SERVICE__API_KEY, SURREAL_USER, SURREAL_PASS, ANTHROPIC_API_KEY — no HOME, no snapshot key.
Raw sweep: `scratchpad/r3/trace/sweep.txt` (brief-named W).

### Code/test/Containerfile hits (19) — my verdicts (measured at `acbce73`)
| # | file:line | verdict | why |
|---|---|---|---|
| C1 | Containerfile:8 | DOCSTRING | header comment: "optional read-only snapshot of static tiers at /source" — aspirational, nothing in the image consumes it |
| C2 | Containerfile:102 | DOCSTRING | comment "/workspace and /source remain readable" above `USER lore` |
| C3 | Containerfile:167 | DOCSTRING | commented run recipe `[ -v <snapshot>:/source:ro ]` |
| C4 | Containerfile:186 | DOCSTRING | commented run recipe `-v <snapshot>:/source:ro` |
| C5 | loremaster/loremaster/index/indexer.py:395 | DOCSTRING | `Indexer.__init__` Args docstring "bind-mounted :ro at /source in the live server" — FALSE vs the code: the server passes `_DEFAULT_SNAPSHOT_ROOT` |
| C6 | loremaster/loremaster/source/snapshot.py:6 | DOCSTRING | module docstring "the server bind-mounts that dir :ro at /source" — same false claim |
| C7 | loremaster/loremaster/source/snapshot.py:70 | DOCSTRING | `SnapshotLayout` docstring, same claim |
| C8 | loremaster/tests/test_config.py:96 | UNRELATED (TEST fixture value) | `extensions.odoo.installed_modules_file: "/source/installed.txt"` — an opaque extension-config string in a schema round-trip fixture; no production `.py`/`.yaml` reads `installed_modules_file` (awk over all tracked `*.py *.yaml *.yml`: only these 2 test lines) |
| C9 | loremaster/tests/test_config.py:305 | TEST-ASSERT (of the fixture string, not of a mount) | asserts the round-tripped string equals "/source/installed.txt"; pins config passthrough, not any reader of `/source` |
| C10 | loremaster/tests/test_mcp_server.py:1719 | UNRELATED | "(auto/summary/source)" detail_level enum |
| C11 | loremaster/tests/test_memory_replay_fidelity_63b_ib.py:9 | UNRELATED | "labels/source/expires_at" field list |
| C12 | loremaster/tests/test_render_slot_inventory.py:168 | UNRELATED | "store/source-minted pointer" prose |
| C13 | loremaster/tests/test_search.py:2870 | UNRELATED | "summary/source/auto" enum |
| C14 | loremaster/tests/test_source.py:6 | DOCSTRING | test-module docstring repeating the /source bind claim; no assertion on it |
| C15 | lorescribe/tests/test_astroid_parse.py:828 | UNRELATED | "chunk_type/source's business" comment |
| C16 | skills/lore-deploy/scripts/lore_deploy.py:662 | DOCSTRING | `_launch_container` docstring |
| C17 | skills/lore-deploy/scripts/lore_deploy.py:684 | **WRITER** (the bind) | `cmd += ["-v", f"{SNAPSHOT_ROOT}:/source:ro"]`, only when static_root_count ∉ {"", "0"} and host `SNAPSHOT_ROOT` exists |
| C18 | skills/lore-deploy/scripts/test_lore_deploy.py:39 | DOCSTRING (comment) | "No static roots → no /source mount" — the test STUBS static count to "0", so the bind branch is not exercised |
| C19 | skills/lore-deploy/scripts/test_lore_deploy.py:219 | DOCSTRING (comment) | `_stub_read_config_field` returns "0" for the static expr → no test reaches line 684 |
**READER count across all 79: 0.** WRITER: 1 (C17). TEST-ASSERT: 1 (C9, a fixture string, not a mount).

### Non-code hits (60) — Sonnet draft, sampled by me
Draft: `scratchpad/r3/trace/verdicts-draft.md` (60 rows: 32 DOCSTRING, 28 UNRELATED, 0 AMBIGUOUS; counts line `in_scope_rows=60 skipped_code_rows=19 total_input_lines=79` reconciles with 79).
Sample: 16 rows re-checked against the matched span (rows 1, 3, 13, 18, 23, 28, 29, 35, 38, 44, 52, 53, 54, 56, 58, 60; the log rows 52–54 against
the full line, where `/source` is `loremaster/loremaster/source/…py`). **16/16 agree.** No non-code hit is a READER by construction (docs, receipts, a log, a tokenizer vocab).
The full per-row table is reproduced in the appendix at the end of this report so it survives the scratchpad.

## Q2 — data-flow map: every runtime path to the static snapshot (traced at `acbce73`; lore_impact + reads)
**One root, one source.** `loremaster.server._DEFAULT_SNAPSHOT_ROOT = Path.home() / "docker" / "mcp" / "lore-snapshot"` (module-level, evaluated
at IMPORT, so `HOME` is load-bearing; deploy sets `-e HOME=/home/lore` → `/home/lore/docker/mcp/lore-snapshot`).
`build_mcp_server._build_context` → `build_app_context(snapshot_root=_DEFAULT_SNAPSHOT_ROOT, …)` is the ONLY production call that supplies it.
`lore_impact(SnapshotLayout)`: 6 prod consumers — `indexer`, `Indexer.__init__`, `graph_roots`, `read_file`, `local_directory`, `LocalDirectorySourceProvider.acquire`.

| # | runtime path (in container) | constructs `SnapshotLayout` with | missing / empty root does |
|---|---|---|---|
| P1 | `build_app_context` → `graph_roots(config, snapshot_root)` → `SurrealCodeGraph(tier_roots=…)` | `SnapshotLayout(_DEFAULT_SNAPSHOT_ROOT)` (`indexer.graph_roots`) | **silent**: static tiers' astroid search roots point at absent dirs; references resolve as external (no error) |
| P2 | `build_app_context` → `Indexer(snapshot_root=…)` | `Indexer.__init__`: `self._snapshot_layout = SnapshotLayout(snapshot_root)` | see P3–P6 |
| P3 | boot/reconcile `_index_static_tier` and `_prepare_static_tier_for_collect` fast-skip guard | `_snapshot_materialized(tier)` over P2's layout | absent/empty + tier has manifest rows → **re-acquire** → `LocalDirectorySourceProvider.acquire` raises `FileNotFoundError` (provider `source` is a HOST path, absent in-container; probe shows `exists=False` all 3 tiers) → **crash** (eager startup fails, #165 mechanism). Absent + zero rows → silent skip |
| P4 | full rebuild `_acquire_static_snapshot` / rebuild walk | P2's layout | same `acquire` → **crash**; and even with source present, the bind is `:ro`, so `copytree` into the snapshot root would fail in EITHER mount shape (inference from `shutil.copytree` into a read-only bind — not probed) |
| P5 | `rebuild_graph_only(tier)` → `_tier_base` → `(base / row.file_path).read_text()` for `.py` rows | P2's layout | **crash** (`FileNotFoundError`) for a static tier with indexed `.py` rows; no-op for non-`.py` tiers |
| P6 | `count_files_to_rebuild` / `_importable_name` via `_tier_base` | P2's layout | silent: 0 / path-join fallback |
| P7 | serve: `lore_read` = `StoreReadTool(store, manifest)` (server.py, the only prod construction) | **none** — reads `file_text` from the store; imports `ReadFileTool` only for the static `_resolve_span` | none (disk-independent) |
| P8 | `ReadFileTool(snapshot_layout=…)` | constructed **only in tests** (sites sweep: 3 hits, all `tests/`) | n/a in production |

Other in-container entry points: `loremaster.index.cli` and `loremaster.scout` each define their own `_DEFAULT_SNAPSHOT_ROOT` (same `Path.home()` expression)
with a `--snapshot-root` override. The deploy runs the batch index on the HOST (`lore_deploy.py` `[_loremaster_python(), "-m", "loremaster.index", …]`),
writing host `~/docker/mcp/lore-snapshot` — the WRITER of the snapshot is host-side and unaffected by the container bind.

## Q3 — can anything redirect the root, and does anything point at `/source`?
- Server: **no** flag, env var or config key. `snapshot_root=` production hits (sites sweep, 5): `index/cli.py:164`, `scout.py:775`, `scout.py:1023`, `server.py:9878`, `server.py:11010` — the server's two both trace to `_DEFAULT_SNAPSHOT_ROOT`. `LORE_SNAPSHOT` sweep: **0 hits** (coverage files_opened=509 of 511; the 2 are the empty `__init__.py`s). `LoreConfig` has no snapshot field (awk over `config.py`: only docstring mentions).
- The only redirect is `HOME` (via `Path.home()` at import). The image bakes NO `HOME` (`Config.Env`: PYTHON_*, PATH, LORE_CONFIG, LORE_VERSION); the deploy sets `HOME=/home/lore`; the env-file has no HOME key (names checked above).
- CLIs: `--snapshot-root` (index/cli, scout). Every caller passing it is a test with a tmp/`/data/snap` path (flag sweep, 8 hits). **Nothing passes `/source`.**

## Q4 — Containerfile and image
Containerfile (1 tracked file, 207 lines): `/source` appears only in comments (C1–C4). No `VOLUME`, no `mkdir`/`chown` of `/source`, no ENV naming it.
Image `localhost/lore:latest` = `4312207128bb…` (the image lore-lore runs, per #165's 2026-10-31 annotation), created 2026-08-18, `LORE_VERSION=0f5f2dc`:
`Volumes=null`, `Entrypoint=["/usr/bin/tini","--"]`, `Cmd=["/app/.venv/bin/python","-m","loremaster.server"]`, `User=lore`, `WorkingDir=/app`.
In-image fs: `/source` absent; `/home/lore` absent too (podman creates it for the bind targets). Receipts: `scratchpad/r3/trace/image.txt`.
Image is 699 commits behind HEAD (`0f5f2dc` is an ancestor of `acbce73`), but `git log -S` over `0f5f2dc..HEAD` finds NO commit touching
`_DEFAULT_SNAPSHOT_ROOT`, `_snapshot_materialized`, `SnapshotLayout(`, `snapshot_root` in server.py/indexer.py, or `/source` in lore_deploy.py/Containerfile,
and `git diff --stat` over `loremaster/loremaster/source/`, `read_file.py`, `store_read.py` is empty — so the probed image and HEAD agree on every symbol the verdict rests on.

## Q5 — tests on the mount / snapshot path
- **No test asserts the `/source` bind at HEAD.** `test_lore_deploy.py` stubs `_read_config_field` to "0" for the static expr (C18, C19), so `lore_deploy.py:684` is reached by no test. ⚠ #165's body says "the test in test_lore_deploy.py that asserts the /source mount" — that does not hold at `acbce73` (not investigated when it disappeared or whether it existed).
- The deploy test that does exist pins `HOME=/home/lore` and the manifest mount `…:/home/lore/.local/state/lore` (`test_lore_deploy.py`, the `_launch_container` user/home test).
- `test_config.py:305` pins the extension string "/source/installed.txt" round-trip — not a mount (C9).
- Snapshot-path tests: `test_migration_wire.py` monkeypatches `server._DEFAULT_SNAPSHOT_ROOT` to `tmp_path/"snap"`; `test_source.py`, `test_read_file.py`, `test_store_read.py`, `test_static_snapshot_reacquire.py`, `test_indexer.py` build `SnapshotLayout(tmp_path…)`; `test_cli.py`/`test_scout.py` pass `--snapshot-root` tmp paths. All exercise the layout with injected roots; none pins the container path.
- Gap (= #165's "INVARIANT OWED", still owed): no test proves a static-tier container BOOTS in the deploy's mount shape.

## Execution probe (step 5 design, step 6 haiku-worker run, judged by me)
Instrument (pasted verbatim per brief-base §1; source file `scratchpad/r3/trace/probe_snapshot_root.py`):
```python
"""Probe: which snapshot root does the SHIPPED server's boot guard actually read?

Runs INSIDE the deployed image (localhost/lore:latest). Imports the ARTIFACT's
loremaster (asserted under /app, never the /workspace mount), resolves the
server's real default snapshot root, and calls the real, unpatched
``Indexer._snapshot_materialized`` and ``graph_roots`` over every static tier the
live lore.yaml declares.

Positive control: the same real method evaluated over a layout rooted at
``/source``. When /source is bound it must return True for tiers that exist on
the host, proving the method CAN return True (a guard that only ever prints
False proves nothing).

Usage (in container): python /probe/probe_snapshot_root.py
Output: one ``key=value`` line per fact; exit 0 unless the provenance assert fails.
"""

from __future__ import annotations

import os
from pathlib import Path

import yaml

import loremaster
from loremaster import server
from loremaster.config import LoreConfig
from loremaster.index.indexer import Indexer, graph_roots
from loremaster.source.snapshot import SnapshotLayout

CONFIG_PATH = Path("/workspace/lore.yaml")
CONTROL_ROOT = Path("/source")


def materialized(root: Path, tier: str) -> bool:
    """Evaluate the REAL ``Indexer._snapshot_materialized`` over a layout rooted at ``root``.

    The Indexer is built without ``__init__`` (which needs a live store, manifest and
    embedder); only ``_snapshot_layout`` is set — the one attribute the method reads,
    assigned exactly as ``Indexer.__init__`` assigns it (``SnapshotLayout(snapshot_root)``).
    """
    indexer = Indexer.__new__(Indexer)
    indexer._snapshot_layout = SnapshotLayout(root)
    return Indexer._snapshot_materialized(indexer, tier)


def main() -> None:
    """Print the provenance, the resolved roots, and the guard verdict per static tier."""
    artifact_file = Path(loremaster.__file__).resolve()
    print(f"loremaster.__file__={artifact_file}")
    assert not str(artifact_file).startswith("/workspace"), "probe is grading the mount, not the image"
    print(f"HOME={os.environ.get('HOME')} uid={os.getuid()}")
    default_root = server._DEFAULT_SNAPSHOT_ROOT
    print(f"server._DEFAULT_SNAPSHOT_ROOT={default_root} exists={default_root.exists()}")
    print(f"/source exists={CONTROL_ROOT.exists()} is_dir={CONTROL_ROOT.is_dir()}")
    config = LoreConfig.model_validate(yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")))
    static_tiers = [root.tier for root in config.effective_roots if root.watch == "static"]
    print(f"static_tiers={static_tiers}")
    tier_roots, _project_roots = graph_roots(config, default_root)
    for tier in static_tiers:
        print(
            f"tier={tier} "
            f"guard_default_root={materialized(default_root, tier)} "
            f"guard_control_source={materialized(CONTROL_ROOT, tier)} "
            f"graph_tier_root={tier_roots[tier]} "
            f"graph_root_exists={Path(tier_roots[tier]).exists()}"
        )
        provider_source = next(r.source for r in config.effective_roots if r.tier == tier)
        print(f"tier={tier} provider_source={provider_source} exists={Path(str(provider_source)).exists()}")


if __name__ == "__main__":
    main()
```
Run shape: `podman run --rm --network=none --userns=keep-id --user 1000:1000 -e HOME=/home/lore -v /home/ejprice/PycharmProjects/lore:/workspace:ro -v <W>:/probe:ro [LEG BIND] localhost/lore:latest /app/.venv/bin/python /probe/probe_snapshot_root.py`.
Provenance receipt (all legs): `loremaster.__file__=/app/loremaster/loremaster/__init__.py` — the image's copy, not the `/workspace` mount (asserted in-script).
Haiku `RAN:` lines checked: match my three commands. Output files re-read by me.

| leg | bind | `_DEFAULT_SNAPSHOT_ROOT` exists | real guard over default root (3 tiers) | positive control: guard over `/source` | graph roots exist | host provider sources |
|---|---|---|---|---|---|---|
| source-only (today's `lore-deploy start`) | `/source` | False | **False ×3** | **True ×3** | False ×3 | absent ×3 |
| home-only (proposed) | `/home/lore/docker/mcp/lore-snapshot` | True | **True ×3** | False ×3 | True ×3 | absent ×3 |
| neither | — | False | **False ×3** | False ×3 | False ×3 | absent ×3 |
Tiers: surrealdb-docs, surrealql-tests, spectron-docs (from live lore.yaml). exit=0 all legs.
Reading: the control proves the real method returns True when its root holds the data, so the default-root False in source-only is a real miss, not a dead probe.
**Source-only and neither are byte-identical on every server-facing fact** (default root, guard, graph roots) — the `/source` bind contributes nothing the server reads.
Bound: the probe evaluates the guard and graph_roots, not a full server boot (no store/manifest); the boot consequence (P3 re-acquire → crash when rows exist) is from the code trace + #165's tracebacks, not re-run here.

## Verdict
Dropping `-v ~/docker/mcp/lore-snapshot:/source:ro` is **SAFE** provided the same host dir is bound at `/home/lore/docker/mcp/lore-snapshot`
(with `HOME=/home/lore` kept). 0 READERS of `/source` across 79 literal hits; the one root the server uses has no redirect; and in the image, `/source`-bound ≡ unbound for everything the server reads.
Flags for whoever makes the change (not edited — read-only brief):
1. Stale prose that will then be false (already false about the server): Containerfile:8,102,167,186; `indexer.py` `Indexer.__init__` docstring; `source/snapshot.py` module + `SnapshotLayout` docstrings; `tests/test_source.py` module docstring; `lore_deploy.py` `_launch_container` docstring; `skills/lore-deploy/references/lifecycle.md:18,19,146`.
2. The bind branch has no test (Q5) — the change should ship #165's owed boot invariant, not a mount-string assert.
3. P4: with a `:ro` bind, an in-container re-acquire can never succeed in any mount shape (source is a host path, target read-only) — so a stamp bump on a static tier while the container is down-path still crashes boot. Outside this question; raise as a question to the operator.
4. `Path.home()` at import makes `HOME` the hidden selector; the image bakes no HOME and has no `/home/lore`. A deploy that drops `-e HOME` moves the root to whatever the passwd lookup gives the run uid (not measured).

## Appendix — non-code hit verdicts (Sonnet draft, 16/16 sampled agree)
| # | path:line | verdict | 8-word reason |
|---|---|---|---|
| 1 | .claude/agents/package-scout.md:146 | UNRELATED | signature/source phrase, not a mount |
| 2 | EXTENDING.md:372 | UNRELATED | loremaster/source/snapshot.py package path |
| 3 | LORE_EXTERNAL_REVIEW.md:125 | UNRELATED | fact/source calibration prose |
| 4 | docs/design/2026-07-31-packet39-google-oauth.md:330 | DOCSTRING | recreate re-mounts /source breaks boot |
| 5 | docs/design/2026-08-01-google-auth-restart-runbook.md:87 | DOCSTRING | container recreate re-mounts /source note |
| 6 | docs/design/2026-08-14-packet47-ingest-entity-seam-design.md:629 | UNRELATED | tier/file_path/source_book field list |
| 7 | docs/design/2026-08-28-packet63-retrofit-rulings.md:52 | UNRELATED | labels/source/importance field list |
| 8 | docs/design/2026-09-11-packet63b-ii-b-drain-update-ruling.md:151 | UNRELATED | served/source prose, not mount |
| 9 | docs/plans/v2/03b-comms-message-surface.md:69 | DOCSTRING | hand-rolled /source mount reapply note |
| 10 | docs/plans/v2/10-d-weak-match-disarm.md:82 | DOCSTRING | hand-rolled /source mount not restart-durable |
| 11 | docs/plans/v2/10-d-weak-match-disarm.md:83 | DOCSTRING | normal start re-mounts /source note |
| 12 | docs/plans/v2/11c-index-boot-reconcile-honesty.md:80 | DOCSTRING | hand-rolled /source mount landmine |
| 13 | docs/plans/v2/19-lore-deploy-rework.md:15 | DOCSTRING | /source-vs-snapshot mount design note |
| 14 | docs/plans/v2/19-lore-deploy-rework.md:22 | DOCSTRING | /source snapshot-mount mismatch note |
| 15 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:23 | DOCSTRING | lore-lore hand-rolled /source mount |
| 16 | docs/plans/v2/2026-08-01-dnd-rag-RESUME.md:25 | DOCSTRING | start re-mounts /source note |
| 17 | docs/plans/v2/65-hosted-write-joint-cutover.md:33 | DOCSTRING | hand-rolled /source mount landmine |
| 18 | docs/plans/v2/65-hosted-write-joint-cutover.md:130 | DOCSTRING | podman args binding /source:ro |
| 19 | docs/plans/v2/INDEX.md:269 | DOCSTRING | cutover hand-rolled /source mount subject |
| 20 | docs/plans/v2/INDEX.md:581 | DOCSTRING | hand-rolled /source mount not restart-durable |
| 21 | docs/plans/v2/INDEX.md:1055 | DOCSTRING | /source-mount issue #165 reference |
| 22 | docs/plans/v2/INDEX.md:1058 | DOCSTRING | hand-rolled /source mount landmine |
| 23 | docs/plans/v2/INDEX.md:1748 | DOCSTRING | podman args binding /source:ro |
| 24 | docs/plans/v2/INDEX.md:1752 | DOCSTRING | known-good /source mount shape |
| 25 | docs/plans/v2/INDEX.md:1785 | DOCSTRING | known-good /source shape, not deploy start |
| 26 | docs/plans/v2/MASTER-PLAN.md:283 | UNRELATED | ident/source/llm_summary column list |
| 27 | docs/plans/v2/receipts/2026-07-28-packet11ib/REPORT-informant-fable-11ib.md:52 | UNRELATED | tiers/sources composition prose |
| 28 | docs/plans/v2/receipts/2026-08-01-agent-comms-fix/REPORT-design-sidecar-04b2-1.md:117 | DOCSTRING | mounted at server path, never /source |
| 29 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:92 | UNRELATED | dndbeyond URL /sources/ path |
| 30 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-corpus-scout-1.md:564 | UNRELATED | URL path /sources/dnd |
| 31 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:169 | UNRELATED | loremaster/source/local_directory.py module path |
| 32 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:448 | DOCSTRING | hand-rolled /source mount not restart-durable |
| 33 | docs/plans/v2/receipts/2026-08-01-dnd-rag-scoping/REPORT-lorearch-scout-1.md:609 | DOCSTRING | hand-rolled /source mount not restart-durable |
| 34 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:283 | DOCSTRING | hand-rolled /source mount fragility |
| 35 | docs/plans/v2/receipts/2026-08-01-packet04b2-wavec/REPORT-lead-04b2-wavec-r2.md:304 | DOCSTRING | log check: no /source break |
| 36 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:733 | DOCSTRING | hand-rolled /source mount not durable |
| 37 | docs/plans/v2/receipts/2026-08-04-packet04b3/REPORT-design-sidecar-04b3-1.md:734 | DOCSTRING | normal start re-mounts /source |
| 38 | docs/plans/v2/receipts/2026-08-08-packet05aiii/REPORT-contract-fix-05aiii.md:201 | UNRELATED | counts/read-only/source CLI leg prose |
| 39 | docs/plans/v2/receipts/2026-08-09-defect-class/REPORT-adversary-g.md:70 | UNRELATED | AST/source pin phrase |
| 40 | docs/plans/v2/receipts/2026-08-10-packet05aii/REPORT-adversary-05a-ii.md:432 | UNRELATED | AST/source guard phrase |
| 41 | docs/plans/v2/receipts/2026-08-12-packet06a/REPORT-coldaudit-honesty-06a.md:17 | DOCSTRING | MEMORY landmine: hand-rolled /source mount |
| 42 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-lead-59.md:146 | DOCSTRING | hand-rolled /source mount deploy landmine |
| 43 | docs/plans/v2/receipts/2026-08-16-packet59/REPORT-sweep-59.md:319 | UNRELATED | signature/source/probe phrase |
| 44 | docs/plans/v2/receipts/2026-08-17-packet07/DESIGN-sidecar-144-posture.md:115 | UNRELATED | signature/source, not docs phrase |
| 45 | docs/plans/v2/receipts/2026-08-17-regression-fix/REPORT-regr-fixer.md:68 | UNRELATED | header name/scheme/source phrase |
| 46 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-build-48b.md:11 | UNRELATED | signature/source phrase |
| 47 | docs/plans/v2/receipts/2026-08-20-packet48/REPORT-builder-48b.md:11 | UNRELATED | signature/source phrase |
| 48 | docs/plans/v2/receipts/2026-08-24-packet62/REPORT-adversary-62w2.md:293 | UNRELATED | package/source table header |
| 49 | docs/plans/v2/receipts/2026-09-04-packet63b/REPORT-contract-63b-i-b.md:52 | UNRELATED | labels/source/expires_at field list |
| 50 | docs/plans/v2/receipts/2026-09-09-packet63b-ib/REPORT-lead-63b-s2.md:58 | DOCSTRING | hand-rolled /source mount, do not start |
| 51 | docs/plans/v2/receipts/2026-09-12-packet63b-ii-b/REPORT-contract-63b-ii-b.md:98 | UNRELATED | AST/source pin phrase |
| 52 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:110 | UNRELATED | loremaster/source/__init__.py log file_path |
| 53 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:111 | UNRELATED | loremaster/source/local_directory.py log file_path |
| 54 | docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log:112 | UNRELATED | loremaster/source/snapshot.py log file_path |
| 55 | docs/plans/v2/receipts/2026-10-04-531-536/REPORT-fix531.md:190 | UNRELATED | loremaster/source/local_directory.py path citation |
| 56 | loresigil/loresigil/data/voyage4_tokenizer.json:54621 | UNRELATED | tokenizer vocab token "/source" |
| 57 | loresigil/loresigil/data/voyage4_tokenizer.json:96938 | UNRELATED | tokenizer vocab token "/sources" |
| 58 | skills/lore-deploy/references/lifecycle.md:18 | DOCSTRING | snapshot bind-mounted :ro at /source |
| 59 | skills/lore-deploy/references/lifecycle.md:19 | DOCSTRING | no static roots needs no /source mount |
| 60 | skills/lore-deploy/references/lifecycle.md:146 | DOCSTRING | podman -v snapshot:/source:ro line |

in_scope_rows=60 skipped_code_rows=19 total_input_lines=79
