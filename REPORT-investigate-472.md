brief-base v16 read · brief project v7 read

# REPORT — investigate-472 (lore finding #472, read-only)

## SUMMARY BLOCK
- **State:** done-with-deviations
- **Deviations:** (1) Run 1 of the fidelity check wrote its script to the lore-lore container's `/tmp`, and it was removed afterwards. That is a container-filesystem write, not a store write; Run 2 used stdin. (2) **Run 1 (a full re-embed at concurrency 2 × 32) put production TEI into a 429 storm from 17:27:55 to 17:36:26Z. The server's embeds 429'd and one file took 76.7 s instead of 7 s. I killed it, and the server logged zero 429s in the 2 min after. No file failed because of it** (§5.1). Run 2 was a low-load sample: one text per request, sequential.
- **Verdict: (a) BENIGN**, measured 2026-09-24 at `f89a1ae`. The retry was **ResilientEmbedder's own per-input fallback** (`loresigil.resilient.ResilientEmbedder.embed_texts` → `_resolve_individually` → `_embed_single`). The event named `embed.permanent_failure` is a *batch-level* exhaustion and the step before that fallback. It is not the per-text outcome. A success leaves no log line. On the production store, `loremaster/tests/test_mcp_server.py` holds 471/471 chunks, each with a finite, unit-norm, distinct dim-2048 vector, and the id set equals the manifest's `chunk_ids`.
- **Packages considered:** none — no mechanism specified
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** none (no production symbols; four scratch instruments, pasted verbatim in §6, not committed because this investigation was read-only)
- **Graded:** n/a (not grading an artifact; investigation at HEAD `f89a1ae`)
- **Also:** 30 of 471 re-embedded, with ≥2 samples in every 32-text batch. All sampled bindings are correct: cos ≥ 0.999935, against a max cross-chunk cos of 0.994081. Tier-wide: the only row where the manifest and the store disagree is the #383 file, correctly marked `failed`. **No false clear in the `lore` tier.**
- **Decisions needed:** (D1) Rename `embed.permanent_failure` for batch exhaustion, and log the fallback's outcome? It is the whole source of #472 (§2). (D2) The #355 hypothesis in the 2026-09-24 annotation does **not** hold on its chunk-count leg (§5.3). Should that be recorded on #355? (D3) Should the #383 file's re-embed of all 505 chunks on every sweep be recorded as a cost amplifier on #383 (§5.2)? (D4) Should the TEI capacity fact (two full-rate clients 429 each other) be ledgered (§5.1)?
- **Receipts:** code path §2 · log interleaving §3 · store probe + positive control §4.1–4.2 · tier-wide diff §4.3 · re-embed fidelity + negative control §4.4 · instruments verbatim §6

## 0. Capability check (brief-base §4)
- **Demanded:** lore tools, read-only prod-store SELECTs via the app's client inside `lore-lore`, and code reads. **I had all of these.**
- **Fallbacks, stated out loud:** the PreToolUse hook blocks `grep` in the main checkout, so code *location* went through `lore_get_symbol` / `lore_search` / `lore_impact`, and `awk` + `Read` were used for line-level reads of files already located (`indexer.py`, `resilient.py`, `tei.py`, `surreal_manifest.py`, `logging_setup.py`) and for the non-symbol log seam (JSON event names in the podman log). This is case (b) of CLAUDE.md's grep allowance: non-symbol textual seams. Nothing was filed as friction, because lore answered every structure question asked of it.
- **Store client:** I did **not** use the app's `SurrealStore`/`bootstrap_session`, because `bootstrap_session` issues `DEFINE NAMESPACE/DATABASE`, which is a write. The probe uses the same SDK from the container's venv (`/app/.venv`, `surrealdb` 2.x): root `signin` from the container env, then `use()` only, then SELECT only. Credentials are read from env and passed straight to `signin`. They were never printed or written.

## 1. Verdict — (a) BENIGN, with an observability defect
Confidence: **HIGH** for the store state, which was measured directly with a positive control. **HIGH** that the retry path is `_resolve_individually`: the code is read, and the log timing matches it to the second. **MEDIUM-HIGH** that the failed batch belonged to `test_mcp_server.py` and not to another caller: this rests on timing and sequencing inference (§3), because the log carries no file id on embed events.

## 2. Code path — what happens after `embed.permanent_failure` (read at `f89a1ae`)
1. `Indexer._index_chunks` (`loremaster/loremaster/index/indexer.py`) → `Indexer._embed_records` → `TEIEmbedder.embed_documents` → `_embed_with` → `_embed_pieces`. The last of these splits the file's texts into ≤32-text batches (`build_batches`, `_MAX_BATCH_TEXTS = 32`) and runs them `concurrency` at a time (lore.yaml `embedding.concurrency: 2`) via `run_in_windows`. Each batch calls `ResilientEmbedder.embed_texts`.
2. `ResilientEmbedder.embed_texts` → `_request_with_retry(texts)`: up to `max_retries = 5` attempts. A `TimeoutException` (TEI `_REQUEST_TIMEOUT_S = 120.0`) logs `embed.retry.backoff` with `status: null`. When the budget is exhausted it logs **`embed.permanent_failure` (ERROR)** and returns `None`.
3. **The step the finding could not see:** when `raw_vectors is None`, `embed_texts` does **not** return Nones. It calls **`_resolve_individually(texts)`**, which re-sends **each of the 32 texts as its own request** (`_embed_single` → `_request_with_retry([text])`, a fresh 5-attempt budget per text). **A successful single-text request logs nothing.** A text ends up `None` only if its own single-text request also exhausts, and that would log a *second* `embed.permanent_failure` with `n_texts: 1`.
4. Only then does `_all_vectors_usable` run in the indexer. Any `None` sends the file to `_mark_file_failed` (`index.file.failed`, `embed_failed_or_non_finite`), which stores nothing new. So the finding's reading of `_mark_file_failed` was correct. It simply never received a `None`.
- **The log therefore rules out a dropped vector on its own:** after 13:20:31 there is **no** `n_texts: 1` backoff or failure event. All 32 single-text requests succeeded on their first attempt.
- **Why the name misleads (the real defect, D1):** `embed.permanent_failure` is *batch-scope*. Whether the batch's texts eventually fail is decided afterwards, and a success is never logged. An operator or agent reading ERROR `embed.permanent_failure` n_texts=32 is entitled to conclude that 32 texts failed, which is exactly what #472 concluded. In trust-doctrine terms the false alarm runs in the safe direction: it claims a failure that did not happen, and it does not hide one. Fix direction: rename to something like `embed.batch_exhausted`, and log the fallback's outcome (`embed.fallback.resolved n_texts=32 n_failed=k`). Keep `embed.permanent_failure` only for a per-input `None`. This is a naming and observability change, not a correctness one.

## 3. Log interleaving — whose batch was it? (receipt: `docs/plans/v2/receipts/2026-09-24-lore-cold-boot/lore-lore-podman.log`)
- **Indexing was sequential at boot.** Each `index.file.done` `duration_ms` fits the gap from the previous `done`. Examples: `test_memory_backend.py` done 13:28:48.187, duration 42.107 s → start 13:28:06.08, which matches `test_mcp_server.py` done at 13:28:06.007. `test_map.py` done 13:08:25.607, duration 27.538 s → start 13:07:58.07, which matches `test_logging_setup.py` done at 13:07:58.007.
- **Start of `test_mcp_server.py`'s embed/commit timer:** 13:28:06.007 − 1074.788 s = **13:10:11.2**. (`duration_ms` starts at the top of `_index_chunks`, after chunking. The 106 s gap after `test_map.py` is therefore chunking a 471-chunk file. That is INFERRED, but the scale is plausible: `test_link5_render_containment.py`, with 138 chunks, shows a 30.5 s pre-timer gap.)
- **Two** `embed.retry.backoff attempt 0 status null n_texts 32` events at 13:12:11.866 and .880. That is the 120 s request timeout after 13:10:11, twice, i.e. **both batches of this file's first concurrency-2 window** timed out. Only **one** chain continues through attempts 1–4, roughly 2 min apart (timeout plus jitter). The other batch's attempt-1 retry succeeded, and that success is unlogged (§2).
- 13:20:31 `embed.permanent_failure` → `_resolve_individually` (no further embed events) → remaining windows → 13:25:48 `store.apply.large_transaction statement_count 4913`, the file's single composed commit. The stored manifest `updated_at` is **13:25:48.254**, which is this commit (§4). → 13:28:06 `index.file.done state=indexed n_chunks=471`.
- **No other caller was embedding in the window.** Uvicorn did not bind until 16:00:18, so no MCP query or memory embeds could arrive. No other file logged `done` or `failed` between 13:08:25 and 13:28:06. The only embed events are the six backoffs and the one failure above. → **(c) rejected.** Bound: the embed events carry no file identity, so attribution is by timing (the two attempt-0 events land exactly one request-timeout after the file's timer start) and by sequencing. It is not by an id.

## 4. Store measurement — production `lore-surreal` :18500, ns `lore` / db `lore`, READ-ONLY (measured 2026-09-24 ~17:1xZ)
Instrument: `probe_472.py` (verbatim in §6.1), run inside `lore-lore` with `podman exec -i lore-lore /app/.venv/bin/python - < probe_472.py`. The exact statements, all SELECT, with bound params:
```sql
SELECT id, embedding, content_hash FROM chunk WHERE tier = $tier AND file_path = $fp
SELECT * FROM type::record('file', [$tier, $fp])
SELECT file_path, count() AS stored, count(array::len(embedding) = $dim) AS with_dim FROM chunk WHERE tier = $tier GROUP BY file_path
SELECT id, n_chunks, chunk_ids, state FROM file WHERE id[0] = $tier
SELECT count() AS n FROM chunk WHERE tier = $tier GROUP ALL
```
Per-vector classification is done client-side (NONE/missing · wrong dim · non-finite · zero norm · min/max norm · distinct 16-component prefixes). Point ids are compared with the manifest's `chunk_ids` in both directions.

### 4.1 Target + controls (raw output, `probe_472.out`)
| file | stored | dim 2048 | NONE | wrong dim | non-finite | all-zero | distinct vecs | norm min/max | content_hash values | manifest state / n_chunks / len(chunk_ids) | manifest `updated_at` | ids manifest∖store / store∖manifest |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **`loremaster/tests/test_mcp_server.py`** (target) | **471** | **471** | 0 | 0 | 0 | **0** | 471 | 1.0 / 1.0 | 1 | indexed / 471 / 471 | 13:25:48.254Z | 0 / 0 |
| `loremaster/tests/test_map.py` (control, indexed 13:08, before the stall) | 87 | 87 | 0 | 0 | 0 | 0 | 87 | 1.0 / 1.0 | 1 | indexed / 87 / 87 | 13:08:21.249Z | 0 / 0 |
| `loremaster/tests/test_memory_backend.py` (control, indexed right after) | 135 | 135 | 0 | 0 | 0 | 0 | 135 | 1.0 / 1.0 | 1 | indexed / 135 / 135 | 13:28:39.140Z | 0 / 0 |

The target's manifest `updated_at` (13:25:48.254Z) is the file's composed commit (`store.apply.large_transaction statement_count 4913` at 13:25:48.72Z). So this row is **the row written by the stalled run**, not a later re-index: the tier has not been rebuilt since, and the 17:16/17:36 sweeps skipped it (`files_skipped 1222/1221`).

### 4.2 Positive control for the instrument (does the probe SEE a broken state?)
`control_472.py` (§6.2) feeds `probe_472.measure_file` a fake connection whose rows carry one of each defect: a NONE vector, an all-zero vector, a wrong-dim vector, a NaN vector, a duplicated vector with a stale content_hash, and a manifest id with no stored row. Output:
`stored_chunks 6 · dim_2048 4 · none_or_missing 1 · wrong_dim 1 · non_finite 1 · all_zero 1 · distinct_vector_prefixes 2 · distinct_content_hash 2 · ids_in_manifest_not_store 1`. **Every injected defect is detected, each in its own column.** The clean 0s in §4.1 are therefore measurements, not blind spots. (Structural note: `chunk.embedding` is a non-`option` `array<float>` on a SCHEMAFULL table (`surreal_schema._CHUNK_FIELD_SPECS`), so a NONE vector cannot be stored at all. The all-zero and wrong-dim columns are the ones doing real work.)

### 4.3 Tier-wide derived check (blast radius, all `lore`-tier manifest rows)
`manifest_rows 1223 (indexed 1222, failed 1) · Σ n_chunks over ALL rows 28613 · store chunks 28108 · store chunks with dim 2048: 28108 · files with ≥1 stored chunk 1216 · store paths with no manifest row: 0`.
**The only row where `n_chunks == len(chunk_ids) == stored == with_dim` fails is `loremaster/tests/test_comms_tool.py` (state `failed`, n_chunks 505 retained from last-good, 0 stored). That is the #383 file, correctly marked failed.** 28613 − 505 = **28108**, exactly the store count. The other 1222 manifest rows agree on all four numbers. That includes 6 zero-chunk `indexed` rows (1222 − 1216), which pass as 0 = 0 = 0 = 0. **No false clear anywhere in the tier.**

### 4.4 Re-embed fidelity (are the stored vectors the RIGHT embeddings of their chunk texts?)
The §4.1 numbers rule out empty, zero, duplicate and wrong-shape vectors. They do **not** rule out a real vector bound to the wrong chunk, such as a positional shift inside the fallback. The broken state that would serve exactly the §4.1 bytes is "valid unit vectors, mis-assigned". The instrument for that state is a re-embed: re-chunk the on-disk file with the app's own `LoreServer.registry`, check that its `sha512` equals the stored `content_hash`, embed through the app's own `make_embedder_from_config`, and cosine-compare each fresh vector against the stored vector with the same deterministic `point_id`.

**Run 1 (full re-embed, concurrency 2): ABORTED by me at 17:36:26Z. See the deviation in §5.1.** It had logged 10 `embed.retry.backoff` (429) and 1 `embed.permanent_failure` in its own process and produced no result.

**Run 2 (the one that counts), 17:39:31–17:42:01Z:** `reembed_sample_472.py` (§6.3). It embeds **one text per request, sequentially, every 16th chunk** (ordinals 0, 16, …, 464). `build_batches` is an in-order contiguous partition (`loresigil.batching.build_batches` docstring + body), and a batch holds ≤32 texts. So stride 16 puts **≥2 samples in every 32-text batch, including the one that exhausted at 13:20:31**, whichever batch that was. Input on stdin, so nothing was written to the container filesystem. Output (`reembed_sample_472.out`):
| file | disk sha512 == stored content_hash | re-chunked / stored | sampled / ids matched | fresh None | cos min (ordinal) | cos median |
|---|---|---|---|---|---|---|
| `test_mcp_server.py` | **True** | 471 / 471 | 30 / 30 | 0 | **0.999935** (0) | 1.0 |
| `test_map.py` (control) | True | 87 / 87 | 6 / 6 | 0 | 1.0 | 1.0 |

**Negative control for this instrument, store-only with no TEI load** (`offdiag_472.py`, §6.4). This is the largest cosine between two *different* chunks' stored vectors in the same file:
`test_mcp_server.py: max off-diagonal 0.994081 · p99 0.840153 · pairs ≥0.999: 0` and `test_map.py: max 0.961208`.
A vector bound to the wrong chunk would therefore score **≤ ~0.9941** against the fresh embedding of that chunk's text. Every sample scored **≥ 0.999935**. **All 30 sampled bindings are correct, and at least 2 samples fall in every batch.** ⚠ Honest note on my own instrument: its printed `n_below_0.99` threshold was too loose to catch a swap with the single most-similar pair (0.994 > 0.99). The discriminating comparison is `cos_min` against `max_offdiag`, not that column.
**Bound:** 30 of 471 vectors were re-embedded. The other 441 rest on the §4.1 structural checks (all present, dim 2048, finite, non-zero, unit, distinct), on the batch-coverage argument above, and on the positional-alignment code (`_resolve_individually` appends in input order; `_embed_pieces` stitches by index).

## 5. Side observations (surfaced, not acted on)
### 5.1 DEVIATION — my Run 1 put production TEI into a 429 storm (no data harm, measured)
Run 1 sent concurrency-2 × 32-text batches. That is the same shape the server uses. From 17:27:55Z the **production server's** batches started receiving HTTP 429 (`embed.retry.backoff status 429`, one `embed.permanent_failure status 429 n_texts 32` at 17:28:10Z, more at 17:33–17:35Z). `REPORT-lead-63c.md` took **76.7 s** to index at 17:27:54Z, against **6.8–7.0 s** before and **6.6 s** after. I killed Run 1 at 17:36:26Z, and the server logged **zero** 429s in the following 2 min. Harm check: `index.file.failed` fired for no file except the #383 file (17:36:09Z, `store_op_failed_after_retries`, which is its standing failure, not an embed failure). INFERRED: TEI's guard admits about 64 concurrent texts (the `ResilientEmbedder` docstring calls it *"the TEI 64-concurrency DOS guard"*), and one client at concurrency 2 × 32 is already 64. **So any two concurrent full-rate embed clients will 429 each other.** That is a capacity fact the lead may want ledgered: two lore instances indexing at once would do the same.

### 5.2 The #383 file is re-EMBEDDED in full on every periodic sweep, then dropped
`test_comms_tool.py` (505 chunks) logged `index.file.store_failed` → `index.file.failed` at 12:55:05, 17:16:36 and 17:36:09Z. Each time the sweep embeds all 505 chunks (about 16 TEI batches) and then fails at the store cap. The server's 429 batch at 17:28:10Z most likely belonged to this re-embed: it is the only ≥32-chunk file processed in the 17:36:31 sweep, which indexed 2 files + 1 failed. That makes it a **second live instance of the §2 mechanism**. A batch exhausted at 429, and the file still reached the store step. Reaching the store step requires `_all_vectors_usable` to pass, so the fallback produced all 505 vectors under active contention. **Cost:** permanent unindexability (#383) also costs a full-file TEI re-embed on every sweep, forever. This belongs on #383 as a cost amplifier. Fix direction: skip re-embed when the content hash is unchanged and the prior failure reason is `store_op_failed_after_retries`.

### 5.3 #355's 2026-09-24 hypothesis — count leg measured, and it does NOT hold at the count leg
The annotation hypothesised that the permanently-failed #383 file guarantees a store-vs-manifest count delta, so the boot-only whole-tier purge fires every boot. `SurrealManifest.expected_chunks` sums `n_chunks` over **`indexed` rows only** (read at `f89a1ae`). Measured here: Σ over indexed rows = 28613 − 505 = **28108 = store count**. So **the failed file creates no delta on the chunk-count leg.** Unmeasured by me: the graph leg of `reconcile_store_divergence` (`code_graph.indexed_file_count()` vs manifest), and why the 17:16:37 and 17:36:31 `reconcile.summary` both still print `tiers_rebuilt ["lore"]` with 0 and 2 files indexed and 1221–1222 skipped. Either that label does not mean "purged", or another leg fires. **This is a lead for #355, not a conclusion.** (D2)

## 6. Instruments (verbatim — brief-base §1: a measurement's instrument ships with the claim)

### 6.1 `probe_472.py` — store probe (SELECT-only)
```python
"""READ-ONLY probe for lore finding #472 — per-file chunk/vector integrity vs manifest.

Runs INSIDE the lore-lore container (`podman exec -i lore-lore /app/.venv/bin/python - < probe_472.py`)
so it uses the app's own SDK and credentials from the container env. Credentials are read
from env and passed straight to signin; they are never printed. Every statement is a
SELECT; no DEFINE/bootstrap (connection.use() only), no write of any kind.
"""

from __future__ import annotations

import asyncio
import math
import os
import sys

from surrealdb import AsyncSurreal

URL = "ws://127.0.0.1:18500/rpc"
NAMESPACE = "lore"
DATABASE = "lore"
TIER = "lore"
EXPECTED_DIM = 2048
TARGET = "loremaster/tests/test_mcp_server.py"
CONTROLS = ("loremaster/tests/test_map.py", "loremaster/tests/test_memory_backend.py")
# Statements are FIXED strings with bound params — pasted verbatim into the report.
Q_FILE_VECTORS = (
    "SELECT id, embedding, content_hash FROM chunk WHERE tier = $tier AND file_path = $fp"
)
Q_MANIFEST_ROW = "SELECT * FROM type::record('file', [$tier, $fp])"
Q_TIER_COUNTS = (
    "SELECT file_path, count() AS stored, "
    "count(array::len(embedding) = $dim) AS with_dim "
    "FROM chunk WHERE tier = $tier GROUP BY file_path"
)
Q_TIER_MANIFEST = "SELECT id, n_chunks, chunk_ids, state FROM file WHERE id[0] = $tier"
Q_TIER_TOTAL = "SELECT count() AS n FROM chunk WHERE tier = $tier GROUP ALL"


def rows(result):
    """Narrow an SDK SELECT result to a list of dict rows."""
    return [row for row in result if isinstance(row, dict)] if isinstance(result, list) else []


def record_key(record_id) -> str:
    """The chunk point id as the manifest's chunk_ids spells it (the record key)."""
    return str(record_id.id) if hasattr(record_id, "id") else str(record_id)


async def measure_file(connection, file_path: str) -> dict:
    """Stored-vs-manifest integrity for one file: counts, dims, zero/non-finite, id-set diff."""
    chunk_rows = rows(await connection.query(Q_FILE_VECTORS, {"tier": TIER, "fp": file_path}))
    manifest = rows(await connection.query(Q_MANIFEST_ROW, {"tier": TIER, "fp": file_path}))
    stored = len(chunk_rows)
    dim_ok = none_or_missing = wrong_dim = all_zero = non_finite = 0
    norms = []
    fingerprints = set()
    for row in chunk_rows:
        vector = row.get("embedding")
        if vector is None:
            none_or_missing += 1
            continue
        if len(vector) != EXPECTED_DIM:
            wrong_dim += 1
            continue
        dim_ok += 1
        if not all(math.isfinite(component) for component in vector):
            non_finite += 1
            continue
        norm = math.sqrt(sum(component * component for component in vector))
        if norm == 0.0:
            all_zero += 1
        norms.append(norm)
        fingerprints.add(tuple(round(component, 6) for component in vector[:16]))
    stored_ids = {record_key(row["id"]) for row in chunk_rows}
    manifest_row = manifest[0] if manifest else None
    manifest_ids = set(manifest_row["chunk_ids"]) if manifest_row else set()
    hashes = {row.get("content_hash") for row in chunk_rows}
    return {
        "file_path": file_path,
        "stored_chunks": stored,
        "dim_2048": dim_ok,
        "none_or_missing": none_or_missing,
        "wrong_dim": wrong_dim,
        "non_finite": non_finite,
        "all_zero": all_zero,
        "distinct_vector_prefixes": len(fingerprints),
        "norm_min": round(min(norms), 6) if norms else None,
        "norm_max": round(max(norms), 6) if norms else None,
        "distinct_content_hash": len(hashes),
        "manifest_state": manifest_row["state"] if manifest_row else None,
        "manifest_n_chunks": manifest_row["n_chunks"] if manifest_row else None,
        "manifest_chunk_ids_len": len(manifest_row["chunk_ids"]) if manifest_row else None,
        "manifest_updated_at": str(manifest_row["updated_at"]) if manifest_row else None,
        "ids_in_manifest_not_store": len(manifest_ids - stored_ids),
        "ids_in_store_not_manifest": len(stored_ids - manifest_ids),
    }


async def tier_diff(connection) -> dict:
    """Tier-wide derived check: every manifest row vs its stored chunk + vector count."""
    counts = {
        row["file_path"]: row
        for row in rows(await connection.query(Q_TIER_COUNTS, {"tier": TIER, "dim": EXPECTED_DIM}))
    }
    manifest_rows = rows(await connection.query(Q_TIER_MANIFEST, {"tier": TIER}))
    total = rows(await connection.query(Q_TIER_TOTAL, {"tier": TIER}))
    states: dict[str, int] = {}
    mismatches = []
    expected_sum = 0
    for row in manifest_rows:
        _tier, file_path = row["id"].id
        states[row["state"]] = states.get(row["state"], 0) + 1
        expected_sum += row["n_chunks"]
        stored = counts.get(file_path, {}).get("stored", 0)
        with_dim = counts.get(file_path, {}).get("with_dim", 0)
        if not (row["n_chunks"] == len(row["chunk_ids"]) == stored == with_dim):
            mismatches.append(
                (file_path, row["state"], row["n_chunks"], len(row["chunk_ids"]), stored, with_dim)
            )
    manifest_paths = {row["id"].id[1] for row in manifest_rows}
    store_only = sorted(set(counts) - manifest_paths)
    return {
        "manifest_rows": len(manifest_rows),
        "manifest_states": states,
        "manifest_expected_chunks_sum": expected_sum,
        "store_total_chunks": total[0]["n"] if total else 0,
        "store_files": len(counts),
        "store_total_with_dim": sum(row["with_dim"] for row in counts.values()),
        "mismatch_rows": mismatches,
        "store_paths_without_manifest_row": store_only,
    }


async def main() -> int:
    """Sign in (root creds from env, never printed), select the db, run the SELECTs."""
    connection = AsyncSurreal(URL)
    await connection.connect()
    await connection.signin(
        {"username": os.environ["SURREAL_USER"], "password": os.environ["SURREAL_PASS"]}
    )
    await connection.use(NAMESPACE, DATABASE)
    for file_path in (TARGET, *CONTROLS):
        print(await measure_file(connection, file_path))
    print(await tier_diff(connection))
    await connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

### 6.2 `control_472.py` — positive control (offline, synthetic rows)
```python
"""Positive control: feed probe_472.measure_file synthetic broken rows and show it SEES each defect."""
import asyncio, sys, types
sys.path.insert(0, sys.argv[1])
import probe_472

class Rid:
    def __init__(self, key): self.id = key

good = [1.0] + [0.0] * 2047
rows = [
    {"id": Rid("a"), "embedding": good, "content_hash": "h"},
    {"id": Rid("b"), "embedding": None, "content_hash": "h"},                    # NONE vector
    {"id": Rid("c"), "embedding": [0.0] * 2048, "content_hash": "h"},            # all-zero
    {"id": Rid("d"), "embedding": [0.5] * 1024, "content_hash": "h"},            # wrong dim
    {"id": Rid("e"), "embedding": [float("nan")] * 2048, "content_hash": "h"},   # non-finite
    {"id": Rid("f"), "embedding": good, "content_hash": "h2"},                   # duplicate vector, stale hash
]
manifest = [{"state": "indexed", "n_chunks": 7, "chunk_ids": ["a", "b", "c", "d", "e", "f", "g"], "updated_at": "t"}]

class FakeConnection:
    async def query(self, statement, params):
        return manifest if statement == probe_472.Q_MANIFEST_ROW else rows

print(asyncio.run(probe_472.measure_file(FakeConnection(), "x.py")))
```

### 6.3 `reembed_sample_472.py` — sampled re-embed fidelity (Run 2; derived from Run 1's `reembed_472.py` by making the embed loop sequential, single-text, stride 16)
```python
"""READ-ONLY re-embed fidelity check for lore finding #472.

Runs INSIDE lore-lore. Re-chunks the on-disk file with the app's own registry (LoreServer),
asserts its sha512 equals the stored chunks' content_hash (so the text we embed IS the text
that was indexed), re-embeds every chunk through the app's own embedder (TEI), and compares
each fresh vector with the stored one by cosine, keyed by the deterministic point id.
A vector bound to the wrong chunk, a stale vector, or a placeholder would score far below 1.
Store access is SELECT-only; no store write, no DEFINE. Credentials never printed.
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
from pathlib import Path

from lorescribe.models import ChunkContext
from surrealdb import AsyncSurreal

from loremaster.config import load_config
from loremaster.embedding import make_embedder_from_config
from loremaster.index.records import chunk_to_record, sha512_hex
from loremaster.server import LoreServer

CONFIG_PATH = "/workspace/lore.yaml"
WORKSPACE = Path("/workspace")
URL = "ws://127.0.0.1:18500/rpc"
NAMESPACE = DATABASE = TIER = "lore"
Q_FILE = (
    "SELECT id, embedding, content_hash, mtime_ns FROM chunk "
    "WHERE tier = $tier AND file_path = $fp"
)
FILES = sys.argv[1:] or ["loremaster/tests/test_mcp_server.py"]
SAMPLE_STRIDE = 16  # every 16th chunk => >=2 samples inside every 32-text batch


def cosine(left: list[float], right: list[float]) -> float:
    """Cosine similarity of two equal-length vectors."""
    dot = sum(a * b for a, b in zip(left, right, strict=True))
    return dot / (math.sqrt(sum(a * a for a in left)) * math.sqrt(sum(b * b for b in right)))


async def check_file(connection, server, embedder, slug: str, file_path: str) -> None:
    """Re-chunk + re-embed one file and cosine-compare with its stored vectors."""
    rows = await connection.query(Q_FILE, {"tier": TIER, "fp": file_path})
    stored = {str(row["id"].id): row for row in rows}
    stored_hashes = {row["content_hash"] for row in rows}
    source = (WORKSPACE / file_path).read_text(encoding="utf-8")
    disk_hash = sha512_hex(source)
    mtime_ns = next(iter(rows))["mtime_ns"]

    def count_one(text: str) -> int:
        return embedder.count_tokens([text])[0]

    context = ChunkContext(
        slug=slug, file_path=file_path, count_tokens=count_one,
        max_input_tokens=embedder.max_input_tokens,
    )
    chunks = server.registry.dispatch_file(file_path, source, context)
    records = [
        chunk_to_record(chunk, slug=slug, tier=TIER, file_path=file_path,
                        content_hash=disk_hash, mtime_ns=mtime_ns)
        for chunk in chunks
    ]
    # LOW-LOAD: one text per request, sequential, every SAMPLE_STRIDE-th chunk only.
    sampled = list(range(0, len(records), SAMPLE_STRIDE))
    fresh = {}
    for ordinal in sampled:
        fresh[ordinal] = (await embedder.embed_documents([records[ordinal].embedding_text])).vectors[0]
    records_vectors = [(ordinal, records[ordinal], fresh[ordinal]) for ordinal in sampled]
    fresh_none = sum(1 for vector in fresh.values() if vector is None)
    matched = 0
    sims: list[tuple[float, int]] = []
    for ordinal, record, vector in records_vectors:
        row = stored.get(record.point_id)
        if row is None or vector is None:
            continue
        matched += 1
        sims.append((cosine(vector, row["embedding"]), ordinal))
    sims.sort()
    below = [(round(sim, 4), ordinal) for sim, ordinal in sims if sim < 0.99]
    print({
        "file_path": file_path,
        "disk_hash_equals_stored": stored_hashes == {disk_hash},
        "rechunked": len(records),
        "stored": len(stored),
        "ids_matched": matched, "sampled": len(sampled),
        "fresh_none": fresh_none,
        "cos_min": round(sims[0][0], 6) if sims else None,
        "cos_min_ordinal": sims[0][1] if sims else None,
        "cos_median": round(sims[len(sims) // 2][0], 6) if sims else None,
        "n_below_0.99": len(below),
        "below_0.99": below[:40],
    })


async def main() -> int:
    """Load the app's config/registry/embedder, sign in read-only, check each file."""
    config = load_config(CONFIG_PATH)
    server = LoreServer(config)
    embedder = make_embedder_from_config(config.embedding)
    connection = AsyncSurreal(URL)
    await connection.connect()
    await connection.signin(
        {"username": os.environ["SURREAL_USER"], "password": os.environ["SURREAL_PASS"]}
    )
    await connection.use(NAMESPACE, DATABASE)
    for file_path in FILES:
        await check_file(connection, server, embedder, config.project.slug, file_path)
    await connection.close()
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
```

### 6.4 `offdiag_472.py` — negative control for 6.3 (store-only)
```python
"""Negative control for the re-embed fidelity check (READ-ONLY, store-only, no TEI).

If the maximum cosine between two DISTINCT chunks' stored vectors in a file is well below the
fidelity threshold, then a vector bound to the wrong chunk would score visibly lower than the
~1.0 a correct binding scores, so the fidelity check discriminates. SELECT only; creds never printed.
"""
import asyncio, os
import numpy as np
from surrealdb import AsyncSurreal

Q = "SELECT id, embedding FROM chunk WHERE tier = $tier AND file_path = $fp"

async def main():
    connection = AsyncSurreal("ws://127.0.0.1:18500/rpc")
    await connection.connect()
    await connection.signin({"username": os.environ["SURREAL_USER"], "password": os.environ["SURREAL_PASS"]})
    await connection.use("lore", "lore")
    for file_path in ("loremaster/tests/test_mcp_server.py", "loremaster/tests/test_map.py"):
        rows = await connection.query(Q, {"tier": "lore", "fp": file_path})
        matrix = np.array([row["embedding"] for row in rows], dtype=np.float64)
        matrix /= np.linalg.norm(matrix, axis=1, keepdims=True)
        gram = matrix @ matrix.T
        np.fill_diagonal(gram, -2.0)
        off = gram[gram > -2.0]
        print({"file_path": file_path, "n": len(rows), "max_offdiag_cos": round(float(off.max()), 6),
               "p99_offdiag_cos": round(float(np.percentile(off, 99)), 6),
               "n_pairs_ge_0.999": int((off >= 0.999).sum() // 2)})
    await connection.close()

asyncio.run(main())
```
