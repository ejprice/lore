# lore-lore cold boot — 3h48m MCP outage (2026-09-24)

Captured by `lead-63c-2` (packet 63c session `63c-20260924`) at 2026-09-24 ~16:11Z, while the
container was still running, so the log survives a later recreate.

- **Artifact:** `lore-lore-podman.log` — the COMPLETE `podman logs --timestamps lore-lore` output for
  the container started 2026-09-24 08:12:07 EDT (12:12Z), 0 restarts, image at HEAD-era
  `f04916d` tree. 1314 lines. Secret-scanned before commit: 0 credential-shaped hits outside
  `file_path` values.
- **Findings:** recurrence annotated on **#355** (boot-only whole-tier purge). Related: **#383/#338**
  (`test_comms_tool.py` > 5000 stmts/txn, permanently unindexable), **#339** (lore-lore not
  restart-managed), **#434** (full reconcile > 300s MCP timeout).

## Timeline (all from the log; UTC)

| time | event |
|---|---|
| 12:12:12 | `Started server process`; `embed.probe.ok` (dim 2048); `watcher.start` |
| 12:13:53 | first `index.file.done` — a WHOLE-TIER re-embed of `lore` begins (no log line says why — the #355 "unlogged decision" defect, still present) |
| 12:55:05 | `index.file.store_failed` → `index.file.failed` `loremaster/tests/test_comms_tool.py` (`store_op_failed_after_retries`; `_txn.compose` cap — #383) |
| 13:12:11 → 13:20:20 | TEI embedder stalls: `embed.retry.backoff` attempts 0–4 on a 32-text batch, ~2 min per attempt (`status: null` = timeout, no HTTP status) |
| 13:20:31 | **`embed.permanent_failure` (ERROR), n_texts 32** |
| 13:28:06 | `index.file.done` `loremaster/tests/test_mcp_server.py` — **state `indexed`, n_chunks 471, duration 1,074,788 ms** (the file in flight during the stall) |
| 16:00:18 | `reconcile.summary`: `files_indexed 1218, files_failed 1, tiers_rebuilt ["lore"]`, 3 doc tiers skipped, `duration_ms 13,586,943` (3h46m) |
| 16:00:18 | `Application startup complete`; `Uvicorn running on http://127.0.0.1:9202` — MCP first reachable |

The documented eager boot is ~150 s (repo `CLAUDE.md` §Deploy). Uvicorn does not bind until
the boot reconcile finishes, so every consumer's MCP client gets ECONNREFUSED for the whole
rebuild, and Claude Code does not reconnect by itself (`/mcp` needed).

## Open questions (not yet measured)

1. **Why a whole-tier rebuild?** The log has no divergence line. HYPOTHESIS (unproven): the
   permanently-unindexable #383 file means the store count and the manifest can never agree, so the
   #355 exact-inequality check fires a full purge on EVERY boot. Test: boot with #383 fixed or
   excluded, and see whether `tiers_rebuilt` is empty.
2. **Possible false clear — `test_mcp_server.py`.** `Indexer._mark_file_failed`'s docstring says an
   unusable embed marks the file `failed`. Here a 32-text batch failed permanently mid-file, and
   the file still reported `indexed` with 471 chunks, with no `index.file.failed` logged. Either an
   upstream retry re-embedded the batch (benign, but not logged), or up to 32 chunks were
   dropped or stored without vectors while the manifest says `indexed`. Only the second is a
   trust-doctrine false clear. Measure: stored chunk count and vector presence for that file vs 471.

## Resolutions (2026-09-24, investigate-472 — `REPORT-investigate-472.md`, archived with packet 63c)

1. **Q1 (why a whole-tier rebuild) is still OPEN.** The #383 count-delta hypothesis is **refuted** on the
   chunk-count leg: `SurrealManifest.expected_chunks` sums only `indexed` rows, and Σ indexed = 28108 = store count.
   The unmeasured leads are recorded on #355.
2. **Q2 (possible false clear) is BENIGN, and #472 is resolved.** `embed.permanent_failure` is batch-scope.
   `ResilientEmbedder` then re-embeds each text individually and logs nothing when that succeeds. All 471 chunks
   were stored with correct vectors, and no file in the tier is affected. The misleading event name is filed as #474.
