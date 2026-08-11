brief-base v11 read

# REPORT-investigate-reembed — why the 65e36c8 recreate re-embedded the whole lore tier

## SUMMARY BLOCK
- state: **done** (read-only diagnosis; no fix applied, per brief)
- capability check: brief satisfiable in full — store reachable read-only via the uv-venv
  `surrealdb` SDK; lore MCP down as briefed (not used); creds read from `~/docker/mcp/lore-secrets/lore.env`.
- deviations: none. All store access was SELECT + session `.use()` only — **no writes, no DEFINE, prod store untouched.**
- Packages considered: none — no mechanism specified (read-only investigation).
- Graded: 57b959d · HEAD-at-report: 57b959d · SAME. (Prior image `a04a23ca` is not a local rev; the running boot image `65e36c8` was built between 5466b7b and the recreate.)
- **ROOT CAUSE**: boot-time `reconcile_store_divergence` (server.py:8144) fires a **whole-tier purge + re-embed on `live != expected`** (exact inequality, any delta), for the live `lore` tier, and **logs nothing when it fires**. It fired this boot because the store's live lore chunk-count and the manifest's expected n_chunks had drifted apart by boot time.
- **RECURS EVERY RECREATE? NO** (not structural) — a cleanly-swept tier has `live==expected` by construction; once this re-embed finishes, the next recreate's heal finds agreement. **BUT** the check runs *only at boot*, so any out-of-band store drift between recreates sits latent and detonates as a surprise full re-embed at the next recreate.
- **UNDERLYING DRIFT SOURCE**: not provable now — the pre-heal `live` count was destroyed by the heal's own `delete_by_tier`, the prior container's logs are gone, backups are too old (Aug 3 / Jul 28). Best-supported inference (atomic writes + internally-consistent manifest ⇒ store-side drift): #336-adjacent (lore-surreal on the floating `v3.2` tag). Stated as inference, not measurement.
- decisions-needed: none for this diagnosis. Follow-up-packet fix directions in §6.
- receipt pointers: divergence condition §1 (server.py:8236, 8276-8277); fired-this-boot §2; measured inputs §3 (probe scripts §7); ruled-out candidates §4; recurrence §5.

---

## 1. The exact divergence condition (quoted, file:line)

At boot, `build_app_context(start_tasks=True)` calls `reconcile_store_divergence` **before** the
initial sweep — the *only* call site (`server.py:8741`; grep confirmed one caller in the package).
For each `watch: live` root (only `lore` is live; the doc tiers are `static`):

```
# loremaster/loremaster/server.py  (reconcile_store_divergence, ~L8232-8238)
expected = await manifest.expected_chunks(tier)     # Σ n_chunks WHERE state='indexed' AND id[0]=tier
live     = await store.count(tier)                  # COUNT(chunk) WHERE tier=$tier
count_diverged = live != expected                   # ← ANY inequality trips it
if count_diverged:
    tiers_to_purge.append(tier)
...
# ~L8275-8277
for tier in tiers_to_purge:
    await store.delete_by_tier(tier)                # DELETE chunk WHERE tier=$tier  (whole tier)
    await manifest.reset_tier(tier)                 # UPDATE file SET state='dirty' WHERE id[0]=tier
```

- `store.count` = `SELECT count() FROM chunk WHERE tier = $tier GROUP ALL` (surreal.py:1153).
- `expected_chunks` = `SELECT math::sum(n_chunks) FROM file WHERE state='indexed' AND id[0]=$tier GROUP ALL` (surreal_manifest.py:702).
- `reset_tier` flips **every** row for the tier to `STATE_DIRTY`, preserving `n_chunks`/`chunk_ids`/`sha512`/`size` (surreal_manifest.py:767).

Then the initial sweep (`run_sweep` → `Indexer.index_tier`) re-embeds every reset row, because
`needs_reindex` is True for any non-`indexed` row — **bypassing the mtime+size fast-path**. That is
why 127/152 *unchanged* files re-embedded: the trigger is the count delta, not a file change.

**Two properties that shaped the incident:**
- **Whole-tier, not per-file.** `delete_by_tier` is the only purge primitive used here, so an
  off-by-one delta and an off-by-thousands delta produce the identical response: purge + re-embed
  all 833 lore files (~1.5 hr of embedder load).
- **Silent.** `reconcile_store_divergence` contains **no `logger.*` call on the heal path** (only
  the rebuilding-notice meta window is opened). Nothing at INFO/DEBUG records "tier X diverged
  live=A expected=B → purging". This is why `podman logs | grep divergence|reset|delete_by_tier`
  found nothing, and why the operator saw an unexplained re-embed.

## 2. It fired this boot (measured, not inferred)

Boot = 2026-08-11 00:23:50 UTC (container `Created`/`StartedAt`; log `watcher.start` 00:23:55).
Manifest read at 2026-08-11 ~01:53 UTC, mid-heal:

| lore `file` rows | state |
|---|---|
| 244→286 (rising) | `indexed` (already re-embedded this boot) |
| 588→531 (falling) | `dirty` (reset by the heal, pending) |
| 1 | `failed` |
| **833 total** | |

The **`dirty` state on unchanged files is the signature of `reset_tier`** — nothing else sets an
unchanged file to `dirty` at boot (a mtime-driven reindex would leave a pending file `indexed`
until the sweep processes it, then flip straight to `indexed`). So the heal fired for certain.

Static tiers were **untouched** (chunk counts intact: surrealdb-docs=4606, surrealql-tests=1984,
spectron-docs=1467), confirming a **tier-scoped `lore`-only heal**, not a global rebuild.

## 3. Measured inputs (read-only queries; scripts verbatim in §7)

Store `chunk` table, per tier (mid-heal, 01:53 UTC):
`{lore: 10412 (rebuilding), spectron-docs: 1467, surrealdb-docs: 4606, surrealql-tests: 1984}`

Manifest `file` table, lore tier:
- `expected_chunks(lore)` (indexed-only) = **10412** — exactly equal to the live lore chunk count
  right now (the re-done portion is self-consistent; see §5).
- Σ n_chunks over **all** lore rows (indexed+dirty+failed) = **21569** (mix of new re-done values +
  preserved pre-heal values).
- lore rows = **833**, **all present on disk (0 absent)**.
- Preserved (dirty/failed) rows = 531; rows where `n_chunks != len(chunk_ids)` = **0**.
- chunk rows with `tier = NONE` = **0**.

meta table: `last_sync_at=2026-08-10T23:43:55Z` (prior container's last live file-index),
`last_sweep_at=2026-08-11T00:20:54Z` (prior container's last periodic sweep, ~3 min before this
boot), `schema_rebuild_status=idle`, `embedding_schema_fingerprint=f6e2ee34…a885a8`.

**The pre-heal `live` count is unrecoverable**: `delete_by_tier('lore')` wiped it at heal start,
the prior container (`a04a23ca`) is gone with its logs, and the newest store backup is Aug 3
(`/backups/lore/lore-prod-20260803T141930Z.surql`) — 8 days stale. So the *magnitude and direction*
(over- vs under-count) of the pre-heal divergence cannot be measured. This is a stated bound, not a
gap I can close read-only.

## 4. Root-cause: candidates confirmed / ruled out (with evidence)

| candidate | verdict | evidence |
|---|---|---|
| (c) new image computes count/expected differently | **RULED OUT** | count/expected_chunks/schema/indexer/reconcile/manifest **unchanged** `a04a23ca..HEAD` (git diff --name-only); `embedding_schema_fingerprint` stored == `embedding_schema_fingerprint(HEAD)` **byte-identical** (f6e2ee34…). |
| schema-fingerprint full rebuild (`_maybe_spawn_schema_rebuild`) | **RULED OUT** | fingerprint identical (above) **and** static tiers untouched — a schema rebuild rebuilds every tier. |
| (d) watcher missed *deletions* → stale rows / orphan over-count | **RULED OUT** | **0 of 833** lore manifest rows point at a missing file; every row's file exists on disk. |
| manifest bookkeeping error (n_chunks wrong) | **RULED OUT** | `n_chunks == len(chunk_ids)` on **all 531** preserved rows; 0 null-tier chunks. Manifest internally consistent. |
| per-file live-index non-atomicity (store vs manifest drift under normal watcher op) | **RULED OUT** | `Indexer._build_index_fragments` composes chunk-replace + file_text + manifest(n_chunks, state=indexed) + graph into **ONE** `store.apply()` transaction (indexer.py ~L681-690). Normal operation cannot drift them. |
| (a)/(e) store-side out-of-band chunk drift (#336-adjacent) | **BEST-SUPPORTED, UNPROVEN** | By elimination: writes atomic + manifest internally consistent ⇒ the mismatch entered the **store's chunk set outside lore's transactional path**. lore-surreal runs the **floating `v3.2` tag** (Created 2026-08-08 03:15 UTC, `Image=docker.io/surrealdb/surrealdb:v3.2`); #336 is exactly the forward-only version-drift hazard. **But the triggering event and direction are not measurable now** (pre-heal `live` destroyed). |

**Net root cause:** the divergence heal is a boot-only, whole-tier, silent trip-wire on exact
count equality; it fired because the live lore chunk-count and the manifest's expected n_chunks had
drifted apart by boot. The drift entered store-side (outside lore's atomic writes); the most likely
source is a #336-adjacent store mutation on the floating `v3.2` tag, but that specific event cannot
be proven from surviving evidence.

## 5. Does it recur on every recreate? — **NO (not structural), with a real latent-drift caveat**

**Not structural.** By construction, a fully-swept live tier has `live == expected`: the write path
sets `n_chunks = len(records)` and atomically writes exactly that many chunks. Measured
corroboration: the re-done portion this boot is exactly self-consistent — live lore chunks = 10412
= indexed-row n_chunks = 10412. So once this re-embed completes cleanly, the **next** recreate's
heal will read `live == expected` and **not** re-embed.

Also measured: an *interrupted* re-embed does **not** cause a re-heal — mid-sweep, both `live` and
`expected` count only the already-`indexed` files (dirty rows contribute 0 to both), so they stay
equal; the next boot's heal passes and the sweep simply finishes the remaining dirty rows.

**The caveat (this is the real deploy-mechanism finding):** the divergence check runs **only at
boot** — `reconcile_store_divergence` has a single caller (`build_app_context`), and the periodic
reconcile (`run_sweep` → `index_tier`) does **not** call it. So any out-of-band store drift that
occurs *while a container is running* is invisible to that running server and sits latent **until
the next recreate**, where it detonates as a surprise full-tier re-embed. It will recur **iff** the
store drifts again. **Re-open / recurrence trigger:** a lore-surreal restart or `v3.2` floating-tag
version bump, an interrupted external rebuild, or any non-atomic mutation of the `chunk` table.

**Severity: MEDIUM.** Pre-production (only consumer is the dogfood fleet), container healthy,
uvicorn gated on readiness, no external risk. Cost per occurrence ≈ 1.5 hr embedder load + a
serving-stale/rebuilding window. The defect worth fixing is the **nuclear + silent** response to a
possibly-tiny drift, independent of this instance's (unknowable) trigger.

## 6. Recommended fix direction (for a follow-up packet — NOT implemented here)

1. **Log the heal (cheapest, highest value).** Emit INFO on fire and on completion with
   `{tier, live, expected, delta, action, duration}`. The operator flew blind on a 1.5 hr
   operation; a divergence self-heal that rewrites the whole index must be loud (trust doctrine:
   failures/heals are LOUD, never silent).
2. **De-nuke the heal.** On a *small* delta, diff the store chunk-set against each file's stored
   `chunk_ids` and re-embed only the drifted files, instead of `delete_by_tier` over the whole
   tier. An off-by-N should not cost a full-tier rebuild.
3. **Detect mid-life, not only at boot.** Run a lightweight count-only divergence probe inside the
   periodic reconcile (or alert on it) so drift is surfaced while the server runs, instead of being
   deferred to a surprise at the next recreate.
4. **Kill the drift source.** Pin lore-surreal to an image **digest** rather than the floating
   `v3.2` tag (#336), so a forward version drift cannot silently alter the store; and investigate
   whether the 3.2.x RocksDB reopen changes `count()` / drops points (the unproven trigger here).

Items 1–3 are lore-code changes (pre-authorized per PRE-PRODUCTION status); item 4 is a
deploy/quadlet change (`~/.config/containers/systemd/lore-surreal.container`).

## 7. Instruments (verbatim — read-only probes that established §3/§4 claims)

Run against `ws://127.0.0.1:18500/rpc`, ns/db `lore`, creds from `~/docker/mcp/lore-secrets/lore.env`,
via `uv run python` in `loremaster/`. **SELECT + `.use()` only — no writes.**

```python
# probe A — counts + states + meta  (established §3 aggregate numbers)
import asyncio, os
from surrealdb import AsyncSurreal
URL="ws://127.0.0.1:18500/rpc"; NS=DB="lore"
env={}
for line in open(os.path.expanduser("~/docker/mcp/lore-secrets/lore.env")):
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.strip().split("=",1); env[k]=v
async def main():
    db=AsyncSurreal(URL)
    await db.signin({"username":env["SURREAL_USER"],"password":env["SURREAL_PASS"]})
    await db.use(NS,DB)
    print(await db.query("SELECT tier, count() AS c FROM chunk GROUP BY tier"))
    print(await db.query("SELECT id[0] AS tier, state, count() AS c FROM file GROUP BY tier, state"))
    print(await db.query("SELECT math::sum(n_chunks) AS s FROM file WHERE state='indexed' AND id[0]='lore' GROUP ALL"))
    print(await db.query("SELECT math::sum(n_chunks) AS s FROM file WHERE id[0]='lore' GROUP ALL"))
    print(await db.query("SELECT * FROM meta"))
    await db.close()
asyncio.run(main())
```

```python
# probe B — every lore manifest path stat'd for on-disk existence  (established §4: 0 stale rows)
import asyncio, os
from pathlib import Path
from surrealdb import AsyncSurreal
URL="ws://127.0.0.1:18500/rpc"; NS=DB="lore"; REPO=Path("/home/ejprice/PycharmProjects/lore")
env={}
for line in open(os.path.expanduser("~/docker/mcp/lore-secrets/lore.env")):
    if "=" in line and not line.strip().startswith("#"):
        k,v=line.strip().split("=",1); env[k]=v
async def main():
    db=AsyncSurreal(URL)
    await db.signin({"username":env["SURREAL_USER"],"password":env["SURREAL_PASS"]}); await db.use(NS,DB)
    rows=await db.query("SELECT id, state, n_chunks FROM file WHERE id[0]='lore'")
    present=absent=0
    for r in rows:
        path=r["id"].id[1]
        (present:=present+1) if (REPO/path).is_file() else (absent:=absent+1)
    print("rows",len(rows),"present",present,"absent",absent)
    await db.close()
asyncio.run(main())
```

```python
# probe C — manifest internal consistency  (established §4: n_chunks == len(chunk_ids), 0 mismatch)
#   SELECT id, state, n_chunks, array::len(chunk_ids) AS n_ids
#   FROM file WHERE id[0]='lore' AND state IN ['dirty','failed']
#   → compare n_chunks vs n_ids per row (0 mismatches over 531 rows)
#   SELECT count() AS c FROM chunk WHERE tier = NONE GROUP ALL   → 0
```

Corroborating shell (git delta + fingerprint):
```
git diff --name-only a04a23ca..HEAD | grep -iE 'store/surreal|surreal_schema|surreal_manifest|index/(indexer|reconcile|manifest|records|watcher)'   # → empty
# embedding_schema_fingerprint(load_config(lore.yaml)) == stored meta f6e2ee34…a885a8   # → identical
podman inspect lore-surreal --format '{{.Created}} {{.Image}}'   # → 2026-08-08 03:15 UTC, docker.io/surrealdb/surrealdb:v3.2 (floating)
grep -c 'reconcile_store_divergence' (callers) → 1 real call site: server.py:8741 (boot only)
```
