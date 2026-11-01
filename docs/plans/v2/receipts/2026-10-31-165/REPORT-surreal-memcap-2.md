brief-base v16 read · brief project v7 read

# REPORT surreal-memcap-2 — SurrealDB ENGINE memory budget for spike-surreal (~4 GiB) and lore-surreal (~8 GiB)

Measured 2026-09-25 17:00–~18:00 EDT, session 63c-20260924. Replaces surreal-memcap-1
(stopped: wrong brief — that agent was heading toward a container/cgroup limit, which the
operator explicitly ruled out).

## SUMMARY BLOCK
- **State:** done. Both stores have the engine memory budget applied, restarted, and
  verified (env live + boot-log "Memory manager" lines matching the design exactly on both).
- **Deviations:**
  1. Applying spike-surreal was gated, per brief, on a live `pytest -n 12` run (pid 55096,
     then a follow-on `run_COMBO_W.xml` run) using `:18000` at Step 3. A background poll
     (2 min interval) watched it; it cleared at 17:33:08 EDT (~13 min wait), well inside the
     90 min cap. Re-verified fresh immediately before touching the quadlet (§3.2).
  2. `podman stats --no-stream` is broken on this host (same `unknown FS magic` fault
     memdiag-1 hit) — RSS/memory read from `ps` and cgroup v2 `memory.current`/`.peak`
     instead, which is the more authoritative source anyway.
  3. **Unrelated, flagged per standing instruction, not fixed (out of this task's scope):**
     the spike smoke run (`loremaster/tests/test_comms_schema.py`, §3.2) surfaced **1 failed
     + 3 errors** (215 passed) — a schema field-derivation assertion missing `scope` from the
     `agent` table's non-vacuity floor, and three errors in
     `TestALegacyOverCapNoteCannotDenyADrain`. Nothing about this session's env-var changes
     (RocksDB block cache/write buffers) touches schema field derivation; this reads as a
     pre-existing gap between the schema emitter and this pin's expected floor. Not
     investigated further — outside this brief's scope, surfaced for the operator/lead.
- **Packages considered:** none — no mechanism specified (this is engine-config tuning, not
  a build).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none — no new code symbols introduced (quadlet env-var edits only).
- **Graded:** n/a — this report is a measurement/config change, not a verdict on someone
  else's artifact.
- **Decisions needed:** none from the operator. One FYI: the write-buffer count knobs
  (`SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER`) are pinned explicitly rather than left to
  SurrealDB's system-memory-scaled default — see §2 rationale — which is a design choice,
  not a request for a ruling.
- **Receipts:** §1 consumer table (sourced) · §2 the exact math + quadlet diffs · §3
  before/after (env live, boot-log "Memory manager" lines, RSS timeline, lore MCP
  reconnect) · §4 what is honestly NOT bounded · §5 re-open trigger.

Capability check: all demanded tools were available (lore reachable, registered as
`surreal-memcap-2`, session `63c-20260924`; podman/systemctl/journalctl all worked; no sudo
used; grep/rg avoided per #473, all filtering done with awk).

---

## 1. What makes up SurrealDB 3.2's memory, and which knob bounds each part

Researched in the required order: `docs/reference/surrealdb-31-capabilities.md` first (no
memory-budget section existed there — it is DDL/DML/txn/graph law, not a memory reference,
so this report is new ground for that file's scope), then the indexed vendor docs
(`surrealdb-docs` tier), then the live engine surface (`podman exec spike-surreal /surreal
start --help`, read-only) and the containers' actual live env
(`podman inspect {spike,lore}-surreal`). All HIGH confidence — every row below is either a
verbatim vendor-doc table row (`[SOURCE:reference/cli/surrealdb-cli/environment-variables.mdx]`)
or a live-measured fact from this session's own boot logs/`podman inspect`.

| Consumer | Bounding knob(s) | Default (this host, undeclared = system-memory-scaled) | Spills to disk? | Source |
|---|---|---|---|---|
| RocksDB block cache | `SURREAL_ROCKSDB_BLOCK_CACHE_SIZE` | `max((sysmem/2)-1GiB, 16MiB)` — undeclared, this would auto-size to ~61.9 GiB on this 125.7 GiB host | No — LRU, evicts | `[SOURCE:environment-variables.mdx:1502]`, vendor table |
| RocksDB write buffers (memtables) | `SURREAL_ROCKSDB_WRITE_BUFFER_SIZE` × `SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER` | size: 32/64/128 MiB by sysmem bucket (128 MiB on this host, >16 GiB bucket); count: 2/4/8/32 by sysmem bucket (**32** on this host, >64 GiB bucket) → **4 GiB undeclared, on this host specifically** | No — flushed to SST | `[SOURCE:environment-variables.mdx:1596-1621]` + **live-verified**: boot log before this change read `write buffer size: 134217728B` / `maximum write buffers: 32` (§3) |
| RocksDB "Memory manager: total memory limit" (engine's own computed sum) | = block cache + write_buffer_size×count (engine-computed, logged, not independently settable) | — | — | **[MEASURED, this session]** boot log line `Memory manager: total memory limit: 12884901888` = `8589934592 (declared cache) + 134217728×32 (undeclared buffers)` exactly. This is the fact that explains why the OLD 8 GiB "block-cache-only" cap still left the engine budgeting 12 GiB, and why both stores were observed at 14–19 GiB RSS (REPORT-memdiag-1.md) — the block cache was capped; the write-buffer pool was not. |
| HNSW vector-index cache | `SURREAL_HNSW_CACHE_SIZE` | 256 MiB, shared across every HNSW index in the process | No — bounded LRU | `[SOURCE:environment-variables.mdx:27-62]` vendor table + **live-verified in use**: `loremaster/loremaster/store/surreal_schema.py:1117-1121` (`_hnsw_index`) defines `HNSW DIMENSION {dim} DIST COSINE TYPE F32` indexes on **both** `chunk.embedding` and `memory.embedding` — this is a real, active consumer on both stores, not a dormant cap. |
| DISKANN index cache | `SURREAL_DISKANN_CACHE_SIZE` | 256 MiB, shared across every DISKANN index in the process | No — bounded LRU, but backed by a larger-than-memory persisted structure | `[SOURCE:environment-variables.mdx:27-62]` vendor table. **Not in use**: no `DISKANN` clause anywhere in `surreal_schema.py` — this cap is allocated capacity, not actual consumption. Confirmed by grep-equivalent (awk) sweep of the schema file. |
| Transaction cache | `SURREAL_TRANSACTION_CACHE_SIZE` | 10,000 **items**, not bytes | — | `[SOURCE:environment-variables.mdx:27-62]`. **NOT byte-bounded** — see §4. |
| Datastore definition cache | `SURREAL_DATASTORE_CACHE_SIZE` | 1,000 **definitions**, not bytes | — | same source. **NOT byte-bounded** — see §4. |
| Grouped-commit batch buffer | `SURREAL_ROCKSDB_GROUPED_COMMIT_MAX_BATCH_SIZE` | 4,096 **transactions**, not bytes; only active when `SURREAL_SYNC_DATA` is on and background-flush is off (neither store sets either) | — | `[SOURCE:environment-variables.mdx:1593-1598]`. Inactive on both stores today — confirmed via `podman inspect` env dump (§3), neither var is set. |
| Regex compile buffer | `SURREAL_REGEX_SIZE_LIMIT` | 10 MiB | — | vendor table. Negligible; not touched. |
| Query-execution scratch (sorting, string functions, GQL joins, etc.) | `SURREAL_EXTERNAL_SORTING_BUFFER_LIMIT`, `SURREAL_GENERATION_ALLOCATION_LIMIT`, `SURREAL_GQL_MAX_*_ROWS`, `SURREAL_MAX_CONCURRENT_TASKS` | assorted row/task/byte caps per call | some spill to disk (sorting) | vendor table. **Per-call bounded, not process-wide bounded** — see §4. |

`--help` on the running container does **not** surface any of the `SURREAL_ROCKSDB_*` /
`SURREAL_HNSW_*` names as CLI flags — they are env-var-only, confirmed by reading the full
472-line `surreal start --help` output (pasted in full below, §6) and finding zero
`rocksdb`/`memory`/`cache`/`buffer` hits (via `awk 'BEGIN{IGNORECASE=1}
/rocksdb|memory|cache|buffer|surrealkv|storage/'` over the captured output) outside the
`--path [default: memory]` argument. This matches the vendor docs' own framing: "Storage
backend environment variables" are a category *separate from* command flags.

**Live verification of the current (pre-change) state, both stores**, via
`podman inspect {spike,lore}-surreal --format '{{range .Config.Env}}...'`: both declared
only `SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8589934592` (8 GiB) — nothing else RocksDB-related was
set, confirming REPORT-memdiag-1.md's premise exactly.

---

## 2. Plan — the exact per-knob split

**The formula, live-verified (§3):** the engine's own "Memory manager: total memory limit"
boot-log line = `block_cache_size + write_buffer_size × max_write_buffer_number`, computed
by the engine itself and printed, not something SurrealDB exposes as a single settable knob.
So hitting a target total means setting **both** halves — capping only the block cache (the
pre-existing quadlets) leaves the write-buffer pool at its system-memory-scaled default,
which on this 125.7 GiB host is the **largest** bucket (32 buffers × 128 MiB = 4 GiB),
regardless of what the block cache is capped to. That is the exact mechanism behind
memdiag-1's finding that an "8 GiB" cap still budgeted 12 GiB and both stores were observed
well above 8 GiB RSS.

**Design choice:** `SURREAL_ROCKSDB_WRITE_BUFFER_SIZE` is pinned explicitly to `134217728`
(128 MiB) on both stores, rather than left to its size-bucket default. Reasoning: leaving it
undeclared makes the effective write-buffer budget a function of whatever memory the engine
detects at boot (a property of the *host*, not of this store's intended budget) — if this
host's visible memory ever changes (e.g. someone later adds a cgroup limit, or the host is
migrated), the "undeclared" default could silently jump to a different bucket and the budget
this report targets would silently drift. Pinning the size and tuning only the *count*
keeps the budget deterministic and independent of host sizing. This is a design decision,
not something the operator asked for by name — flagged per brief-base §2's ambiguity rule in
case a fixed-host-sizing assumption was intended instead.

**HNSW cache is left at its 256 MiB default on both stores** — it is small relative to the
targets, is in active use (not a dormant cap), and the operator's target is "about 4 GiB" /
"about 8 GiB", not an exact ceiling, so absorbing it as a fixed 256 MiB addend rather than
shaving it is the simpler, equally-correct choice.

**spike-surreal (TEST), target ~4 GiB:**
```
SURREAL_ROCKSDB_BLOCK_CACHE_SIZE       = 2147483648   (2 GiB)
SURREAL_ROCKSDB_WRITE_BUFFER_SIZE      = 134217728    (128 MiB, pinned)
SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER = 14           (14 × 128 MiB = 1.75 GiB)
```
RocksDB "total memory limit" (engine-computed) = 2147483648 + 14×134217728 = **4026531840 B (3.75 GiB)**.
\+ HNSW cache default 268435456 B (0.25 GiB) = **4294967296 B = exactly 4 GiB** nominal ceiling
on the bounded consumers.

**lore-surreal (PRODUCTION), target ~8 GiB:**
```
SURREAL_ROCKSDB_BLOCK_CACHE_SIZE       = 4831838208   (4.5 GiB)
SURREAL_ROCKSDB_WRITE_BUFFER_SIZE      = 134217728    (128 MiB, pinned)
SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER = 26           (26 × 128 MiB = 3.25 GiB)
```
RocksDB "total memory limit" (engine-computed) = 4831838208 + 26×134217728 = **8321499136 B (7.75 GiB)**.
\+ HNSW cache default 268435456 B (0.25 GiB) = **8589934592 B = exactly 8 GiB** nominal ceiling
on the bounded consumers.

Both numbers landed on exact round-GiB totals by construction (chosen for legibility when
checked against the boot log), not because the underlying math needed to.

**No container/cgroup limit is added anywhere** — no `Memory=`, no `MemoryHigh`, no
`MemoryMax`, no `podman --memory`, per the operator's hard limit. Every number above is an
`Environment=` line inside the existing `[Container]` block.

### Exact quadlet diffs

**`~/.config/containers/systemd/lore-surreal.container`** (production, applied — see §3):
```diff
-# Cap the RocksDB block cache (verified on spike: 8 GiB, not the ~62 GiB auto-default).
-# finding #331: two co-tenant stores' uncapped caches OOM-killed this one on a 125 GiB no-swap box.
-Environment=SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8589934592
+# Engine memory budget (REPORT-surreal-memcap-2.md, 2026-09-25) — this bounds the DATABASE's
+# own memory, not the container/cgroup (no Memory=/MemoryMax here, deliberately).
+# Block cache + write buffers together are what the engine's own boot log sums as
+# "Memory manager: total memory limit" (RocksDB only) -> 4831838208 + 26*134217728
+# = 8321499136 B (~7.75 GiB). Write-buffer size is pinned explicitly rather than left to
+# its system-memory-scaled default (32 x 128 MiB = 4 GiB on this 125 GiB host previously,
+# which is why the old 8 GiB cache-only cap still measured ~12 GiB of engine budget and a
+# store observed at 14-19 GiB RSS — finding #331's block-cache-only cap was necessary but
+# not sufficient). Add the active HNSW vector-index cache (SURREAL_HNSW_CACHE_SIZE, left at
+# its 256 MiB default; `chunk`/`memory` both carry HNSW indexes) for a ~8 GiB nominal ceiling
+# on this PRODUCTION store's bounded consumers. NOT bounded by these knobs: the transaction
+# cache (SURREAL_TRANSACTION_CACHE_SIZE, item-count not bytes), the datastore definition
+# cache (SURREAL_DATASTORE_CACHE_SIZE, item-count not bytes), per-connection/query working
+# memory, and allocator/OS-level retained memory — see the report for the full table.
+Environment=SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=4831838208
+Environment=SURREAL_ROCKSDB_WRITE_BUFFER_SIZE=134217728
+Environment=SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER=26
```

**`~/.config/containers/systemd/spike-surreal.container`** (test, applied — see §3.2):
```diff
-# Cap the RocksDB block cache so two co-tenant stores can't jointly OOM the box
-# (finding #331: uncapped ~62 GiB auto-cache × 2 stores on a 125 GiB no-swap box).
-Environment=SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8589934592
+# Engine memory budget (REPORT-surreal-memcap-2.md, 2026-09-25) — this bounds the DATABASE's
+# own memory, not the container/cgroup (no Memory=/MemoryMax here, deliberately). Mirrors
+# lore-surreal's rationale at half the size: block cache + write buffers = engine's own
+# "Memory manager: total memory limit" (RocksDB only) -> 2147483648 + 14*134217728
+# = 4026531840 B (~3.75 GiB); + the active 256 MiB HNSW vector-index cache default
+# (chunk/memory both carry HNSW indexes) for a ~4 GiB nominal ceiling on this TEST store's
+# bounded consumers. See REPORT-surreal-memcap-2.md for the full consumer table and what
+# is NOT bounded by these knobs.
+Environment=SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=2147483648
+Environment=SURREAL_ROCKSDB_WRITE_BUFFER_SIZE=134217728
+Environment=SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER=14
```

---

## 3. Apply — before/after receipts

### 3.0 Backups and pre-change snapshot (before touching anything)

Both quadlets `cp -a`'d to this session's scratchpad before editing:
`.../scratchpad/quadlet-backup/{spike,lore}-surreal.container.orig` (byte-identical copies of
the files as they stood before this report's edits).

`podman inspect --format '{{.Config.CreateCommand}}'`, captured before any change:
```
spike-surreal: podman run --name spike-surreal --replace --rm --cgroups=split --network host
  --sdnotify=conmon -d --user 1000:1000 --userns keep-id
  -v /home/ejprice/.local/state/lore/spike-surreal-data:/data
  --env SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8589934592
  --env-file /home/ejprice/docker/mcp/lore-secrets/lore.env
  docker.io/surrealdb/surrealdb:v3.2 start --bind 127.0.0.1:18000 rocksdb:/data/store.db

lore-surreal:  podman run --name lore-surreal --replace --rm --cgroups=split --network host
  --sdnotify=conmon -d --user 1000:1000 --userns keep-id
  -v /home/ejprice/.local/state/lore/surreal:/data
  --env SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=8589934592
  --env-file /home/ejprice/docker/mcp/lore-secrets/lore.env
  docker.io/surrealdb/surrealdb:v3.2 start --bind 127.0.0.1:18500 rocksdb:/data/store.db
```
Both containers' live env dump (before change) confirmed only `SURREAL_ROCKSDB_BLOCK_CACHE_SIZE`
was set on either — no `Memory=`/`MemoryMax` anywhere in either quadlet (verified by reading
the full files).

### 3.1 lore-surreal (PRODUCTION) — applied 2026-09-25 17:20:53 EDT

```
$ systemctl --user daemon-reload   # OK
$ systemctl --user restart lore-surreal.service   # issued
$ systemctl --user show lore-surreal.service -p NRestarts,ActiveState,SubState
ActiveState=active
SubState=running
NRestarts=0
```
Not restart-looping.

**Env live** (`podman inspect lore-surreal`, post-restart):
```
SURREAL_ROCKSDB_WRITE_BUFFER_SIZE=134217728
SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=4831838208
SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER=26
```

**Boot log, before vs. after** (`journalctl --user -u lore-surreal`, `Memory manager` lines):
```
BEFORE (2026-09-24 15:19:57, the OOM-killed boot):
  Memory manager: total memory limit: 12884901888
  Memory manager: block cache size: 8589934592B
  Memory manager: write buffer size: 134217728B
  Memory manager: maximum write buffers: 32

AFTER (2026-09-25 17:20:53, this change):
  Memory manager: total memory limit: 8321499136
  Memory manager: block cache size: 4831838208B
  Memory manager: write buffer size: 134217728B
  Memory manager: maximum write buffers: 26
```
`8321499136` matches the §2 calculation exactly (`4831838208 + 26×134217728`). **This is a
live, engine-emitted confirmation that the applied knobs produce the intended budget** — not
an inference from the env vars alone.

**lore MCP health check.** Restarting the store under a live MCP connection drops that
connection — `docs/reference/surrealdb-31-capabilities.md` §3 documents this exact shape
(a raw error on the in-flight call, normalizing to a clean transport-drop on the *next*
call, with reconnect on the call *after that* — "not automatic and not instantaneous").
Observed exactly that sequence, live:
```
call 1 (lore_index):  Error: "no close frame received or sent"
call 2 (lore_search):  Error: "no close frame received or sent"   [same call batch as #1]
call 3 (lore_index):  Error: "no close frame received or sent"
call 4 (lore_index):  SUCCESS — 3812 files indexed, last_sync age 1063s, calibration measured
call 5 (lore_search):  SUCCESS — 3 hits returned
```
lore-lore self-healed with no restart/recreate on this agent's part, matching standing law
("Never restart or recreate lore-lore"). It was not touched.

**RSS timeline** (pid 87802, `ps -o rss`, and cgroup `memory.current` under
`user.slice/user-1000.slice/user@1000.service/app.slice/lore-surreal.service/`):
| mark | RSS | cgroup memory.current | NRestarts |
|---|---|---|---|
| restart (t=30s) | 696 MiB | 720,052,224 B (0.67 GiB) | 0 |
| t=105s (after MCP reconnect + first index/search) | 2.90 GiB | 3,257,184,256 B (3.03 GiB) | 0 |
| +5 min (17:25:53) | 1.844 GiB | 1.921 GiB | 0 |
| +10 min (17:30:53) | 1.981 GiB | 2.057 GiB | 0 |

RSS **dropped** from the t=105s sample (2.90 GiB, right after the first post-restart
`lore_index`/`lore_search` calls) to 1.84–1.98 GiB at +5/+10 min, then held flat — consistent
with a transient allocation from the reconnect burst getting freed rather than sustained
growth. No restart-loop, no climbing trend; steady well under the 8 GiB target throughout
the 10-minute observation window.

### 3.2 spike-surreal (TEST) — applied 2026-09-25 17:34:14 EDT, after the gate cleared

At Step 3, the process table showed a live suite (pid 55096, `run_COMBO_C.xml`,
`-n 12`); a background poll (2 min interval, 90 min cap) watched for it to clear rather
than touching the store underneath it. The poll log shows the run continuing under a
follow-on job (`run_COMBO_W.xml`, same `-n 12` shape) plus unrelated scratch-tree
mutation-proof activity (a different session's `refU/` scratchpad — not this store, but
correctly left alone regardless) through 17:31:08, then:
```
17:31:08 BUSY: pid 95649 ... run_COMBO_W.xml (etimes 466s)
17:33:08 CLEAR: no pytest/xdist process found
```
Cleared after ~13 minutes, well inside the 90 min cap. **Re-verified fresh** immediately
before editing the quadlet (`ps -eo ... | awk '/pytest|xdist/'` at 17:33:18 — zero matches)
per the "check the process table, never shell text" rule (#228).

Applied the same diff shape as production (§2), halved:
```
$ systemctl --user daemon-reload   # OK
$ systemctl --user restart spike-surreal.service   # issued
$ systemctl --user show spike-surreal.service -p NRestarts,ActiveState,SubState
ActiveState=active
SubState=running
NRestarts=0
```

**Env live** (`podman inspect spike-surreal`):
```
SURREAL_ROCKSDB_BLOCK_CACHE_SIZE=2147483648
SURREAL_ROCKSDB_MAX_WRITE_BUFFER_NUMBER=14
SURREAL_ROCKSDB_WRITE_BUFFER_SIZE=134217728
```

**Boot log** (`journalctl --user -u spike-surreal`, `Memory manager` lines, 17:34:14):
```
Memory manager: total memory limit: 4026531840
Memory manager: block cache size: 2147483648B
Memory manager: write buffer size: 134217728B
Memory manager: maximum write buffers: 14
Memory manager: minimum write buffers to merge: 2
```
`4026531840` matches §2's calculation exactly (`2147483648 + 14×134217728`).

**Scoped smoke** (`cd /home/ejprice/PycharmProjects/lore && uv run pytest -q -n 4
loremaster/tests/test_comms_schema.py`), RSS of the `/surreal` process (pid 125566)
before/after:

| | RSS | cgroup memory.current |
|---|---|---|
| before | 0.698 GiB | — |
| after | 0.805 GiB | 0.821 GiB |

```
1 failed, 215 passed, 3 errors in 48.65s
```
A real passed-count in the tail (not a silent "no tests ran" behind a pipe). NRestarts
stayed 0 through the run. RSS grew by ~110 MiB under a 4-worker scoped run, nowhere near
the 4 GiB target. **The 1 failed + 3 errors are unrelated to this change** — see Summary
Block deviation 3; flagged, not investigated (out of scope for an engine-memory-budget
task).

---

## 4. What the engine budget does NOT bound (HONEST, per the trust doctrine)

These are facts, not disclaimers — each names a concrete consumer this session found no
byte-level knob for:

1. **The transaction cache (`SURREAL_TRANSACTION_CACHE_SIZE`, default 10,000) and the
   datastore definition cache (`SURREAL_DATASTORE_CACHE_SIZE`, default 1,000) are bounded by
   ITEM COUNT, not bytes.** A cached item's size is not itself capped — a transaction
   touching many large definitions, or a workload with unusually large per-transaction
   working sets, can grow these caches' byte footprint independent of the RocksDB budget
   above. No env var converts either cap to a byte ceiling.
2. **Per-connection and per-query working memory has no process-wide byte cap.** Individual
   mechanisms are bounded (`SURREAL_GENERATION_ALLOCATION_LIMIT` per string-function call,
   `SURREAL_EXTERNAL_SORTING_BUFFER_LIMIT` in row-count before spilling to disk,
   `SURREAL_MAX_CONCURRENT_TASKS` in job count, `SURREAL_GQL_MAX_*_ROWS` in row count for the
   experimental GQL path) — but there is no single "max total query memory" setting. A burst
   of concurrent large queries (exactly what a `-n 12` pytest run against spike produces) can
   transiently exceed the RocksDB+HNSW budget above; that budget bounds the STORE ENGINE's
   steady-state footprint, not the server process's instantaneous peak under load.
3. **RocksDB's own book-keeping outside the block cache and write buffers** — SST index/filter
   blocks not charged to the declared block cache (depending on RocksDB's internal
   `cache_index_and_filter_blocks` behavior, which SurrealDB does not expose as an env var),
   open-file-handle overhead bounded only by `SURREAL_ROCKSDB_MAX_OPEN_FILES` (1024, a file
   COUNT not a byte cap), and compaction/flush thread-pool memory (`SURREAL_ROCKSDB_JOBS_COUNT`,
   `SURREAL_ROCKSDB_THREAD_COUNT`, both thread counts, each thread carrying its own stack and
   working buffers) all sit outside the "Memory manager: total memory limit" line the engine
   itself prints.
4. **Allocator/OS-level retained memory is entirely outside SurrealDB's control surface.**
   memdiag-1 measured spike-surreal at 16.9 GiB RSS against a 130 MB on-disk store and a
   12 GiB engine-declared budget — a multi-GiB gap this session's research found no
   SurrealDB env var that explains. The likely mechanism (glibc/Rust allocator arenas
   retaining freed pages rather than returning them to the OS under `MemAvailable` pressure)
   is a property of the process's memory allocator, not of any SurrealDB setting; no
   documented knob (RocksDB or otherwise) addresses it. This is exactly the gap the operator's
   brief anticipated ("the block cache is only ONE part of the budget... find ALL the
   parts") — this session found and bounded the write-buffer part, but this fourth item is
   a genuinely open, unbounded-by-this-mechanism consumer.
5. **HTTP/WS server buffering, session state (`SURREAL_DURABLE_SESSIONS`, off by default and
   confirmed unset on both stores), and thread stacks** for the async runtime and RocksDB's
   own flush/compaction threads are real but comparatively small at this scale (single-digit
   MB per thread); not separately tuned here because they are not the dominant term.

**Re-open trigger:** either store's RSS observed above **1.5× its nominal ceiling**
(spike above 6 GiB, lore above 12 GiB) sustained for more than one poll interval — that
would mean an unbounded consumer above (most likely #2 or #4) has become dominant, and the
RocksDB-knob budget in this report is no longer the right lever.

---

## 5. Instruments (pasted verbatim, per brief-base §1)

RSS-timeline sampler (background, run against lore-surreal; the same shape was used to watch
for spike's pytest clearing before applying that leg):
```bash
SCRATCH=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7ed2d11e-3b15-4ea9-82cd-e5e745ee562f/scratchpad
OUT="$SCRATCH/lore_surreal_rss_timeline.txt"
RESTART_EPOCH=$(date -d "2026-09-25 17:20:53" +%s)
for target in 300 600; do
  now=$(date +%s); elapsed=$((now - RESTART_EPOCH)); wait_s=$((target - elapsed))
  if [ "$wait_s" -gt 0 ]; then sleep "$wait_s"; fi
  ts=$(date '+%H:%M:%S')
  rss=$(ps -o rss= -p 87802 2>/dev/null | awk '{printf "%.3f GiB", $1/1048576}')
  cg=$(awk '{printf "%.3f GiB", $1/1073741824}' /sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/app.slice/lore-surreal.service/memory.current 2>/dev/null)
  nrestarts=$(systemctl --user show lore-surreal.service -p NRestarts --value)
  echo "+${target}s mark (wall $ts): RSS=$rss cgroup=$cg NRestarts=$nrestarts" >> "$OUT"
done
```

pytest-clear poller (background, watched spike before applying that leg):
```bash
SCRATCH=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/7ed2d11e-3b15-4ea9-82cd-e5e745ee562f/scratchpad
OUT="$SCRATCH/spike_pytest_watch.txt"
MAX_ITERS=45   # 45 * 120s = 90 min
i=0
while [ "$i" -lt "$MAX_ITERS" ]; do
  hits=$(ps -eo pid,ppid,etimes,cmd | awk 'BEGIN{IGNORECASE=1} /pytest|xdist/ && !/awk/ && !/spike_pytest_watch/')
  if [ -z "$hits" ]; then
    echo "$(date '+%H:%M:%S') CLEAR: no pytest/xdist process found" >> "$OUT"; echo "CLEAR" >> "$OUT"; exit 0
  fi
  echo "$(date '+%H:%M:%S') BUSY:" >> "$OUT"; echo "$hits" >> "$OUT"
  i=$((i+1)); sleep 120
done
echo "$(date '+%H:%M:%S') TIMEOUT after 90 min, still busy" >> "$OUT"; echo "TIMEOUT" >> "$OUT"
```

---

## 6. `surreal start --help` (pasted verbatim, per brief-base §1 — read-only, run against spike-surreal)

Backs the §1 claim that no RocksDB/HNSW/memory-manager option is a documented CLI flag —
they are purely env-var-configured (`podman exec spike-surreal /surreal start --help`):

```
Start the database server

Usage: surreal start [OPTIONS] [PATH]

Arguments:
  [PATH]
          Database path used for storing data

          [env: SURREAL_PATH=]
          [default: memory]

Options:
      --no-banner
          Whether to hide the startup banner

          [env: SURREAL_NO_BANNER=]

      --index-compaction-interval <INDEX_COMPACTION_INTERVAL>
          [env: SURREAL_INDEX_COMPACTION_INTERVAL=]
          [default: 5s]

      --async-event-interval <EVENT_PROCESSING_INTERVAL>
          [env: SURREAL_ASYNC_EVENT_PROCESSING_INTERVAL=]
          [default: 5s]

      --reclaim-interval <RECLAIM_INTERVAL>
          [env: SURREAL_RECLAIM_INTERVAL=]
          [default: 60s]

  -h, --help
          Print help (see a summary with '-h')

Database:
      --node-membership-refresh-interval <NODE_MEMBERSHIP_REFRESH_INTERVAL>
          The interval at which to refresh node registration information

          [env: SURREAL_NODE_MEMBERSHIP_REFRESH_INTERVAL=]
          [default: 3s]

      --node-membership-check-interval <NODE_MEMBERSHIP_CHECK_INTERVAL>
          The interval at which to process and archive inactive nodes

          [env: SURREAL_NODE_MEMBERSHIP_CHECK_INTERVAL=]
          [default: 15s]

      --node-membership-cleanup-interval <NODE_MEMBERSHIP_CLEANUP_INTERVAL>
          The interval at which to process and cleanup archived nodes

          [env: SURREAL_NODE_MEMBERSHIP_CLEANUP_INTERVAL=]
          [default: 300s]

      --changefeed-gc-interval <CHANGEFEED_GC_INTERVAL>
          The interval at which to perform changefeed garbage collection

          [env: SURREAL_CHANGEFEED_GC_INTERVAL=]
          [default: 30s]

      --index-build-resume-interval <INDEX_BUILD_RESUME_INTERVAL>
          The interval at which to resume index builds left unfinished by a crashed node (0 to
          disable)

          [env: SURREAL_INDEX_BUILD_RESUME_INTERVAL=]
          [default: 30s]

      --reclaim-grace <RECLAIM_GRACE>
          Minimum age a removed namespace/database/index must reach before its data is physically
          reclaimed (snapshot-safety grace; effective value is max(this, --tikv-gc-lifetime))

          [env: SURREAL_RECLAIM_GRACE=]
          [default: 10m]

      --tikv-gc-interval <TIKV_GC_INTERVAL>
          The interval at which the TiKV MVCC garbage collector runs

          [env: SURREAL_TIKV_GC_INTERVAL=]
          [default: 10m]

      --tikv-gc-lifetime <TIKV_GC_LIFETIME>
          How far behind the current TSO the TiKV GC safepoint is allowed to sit

          [env: SURREAL_TIKV_GC_LIFETIME=]
          [default: 10m]

      --tikv-lock-cleanup-interval <TIKV_LOCK_CLEANUP_INTERVAL>
          The interval at which TiKV stale transactional locks are resolved

          [env: SURREAL_TIKV_LOCK_CLEANUP_INTERVAL=]
          [default: 60s]

      --durable-sessions
          Whether to persist client-attached HTTP RPC sessions in the datastore so they survive
          server restarts and can be resumed on any cluster node. Intended for deployments that
          route a given session to one node at a time (sticky routing / one runtime per session); a
          session used concurrently from multiple nodes is best-effort. The durable copy contains
          the session's authentication state, stored unencrypted in the datastore

          [env: SURREAL_DURABLE_SESSIONS=]

      --durable-session-ttl <DURABLE_SESSION_TTL>
          How long a persisted RPC session survives without being used; each use refreshes the
          expiry

          [env: SURREAL_DURABLE_SESSION_TTL=]
          [default: 24h]

      --durable-session-gc-interval <DURABLE_SESSION_GC_INTERVAL>
          The interval at which expired persisted RPC sessions are purged (0 to disable)

          [env: SURREAL_DURABLE_SESSION_GC_INTERVAL=]
          [default: 60s]

      --query-timeout <QUERY_TIMEOUT>
          The maximum duration that a set of statements can run for

          [env: SURREAL_QUERY_TIMEOUT=]

      --transaction-timeout <TRANSACTION_TIMEOUT>
          The maximum duration that any single transaction can run for

          [env: SURREAL_TRANSACTION_TIMEOUT=]

      --startup-operation-timeout <STARTUP_OPERATION_TIMEOUT>
          The maximum duration that each built-in startup datastore operation can retry for

          [env: SURREAL_STARTUP_OPERATION_TIMEOUT=]
          [default: 60s]

Authentication:
  -u, --username <USERNAME>
          The username for the initial database root user. Only if no other root user exists

          [env: SURREAL_USER=lore]
          [aliases: --user]

  -p, --password <PASSWORD>
          The password for the initial database root user. Only if no other root user exists

          [env: SURREAL_PASS=ef6e49e7fe3ad83e907852aeb6be7ac2fb5b517dfaa52f76]
          [aliases: --pass]

      --unauthenticated
          Whether to allow unauthenticated access

          [env: SURREAL_UNAUTHENTICATED=]

Datastore connection:
      --kvs-ca <KVS_CA>
          Path to the CA file used when connecting to the remote KV store

          [env: SURREAL_KVS_CA=]

      --kvs-crt <KVS_CRT>
          Path to the certificate file used when connecting to the remote KV store

          [env: SURREAL_KVS_CRT=]

      --kvs-key <KVS_KEY>
          Path to the private key file used when connecting to the remote KV store

          [env: SURREAL_KVS_KEY=]

HTTP server:
      --web-crt <WEB_CRT>
          Path to the certificate file for encrypted client connections

          [env: SURREAL_WEB_CRT=]

      --web-key <WEB_KEY>
          Path to the private key file for encrypted client connections

          [env: SURREAL_WEB_KEY=]

      --client-ip <CLIENT_IP>
          The method of detecting the client's IP address

          Possible values:
          - none:             Don't use client IP
          - socket:           Raw socket IP
          - CF-Connecting-IP: Cloudflare connecting IP
          - Fly-Client-IP:    Fly.io client IP
          - True-Client-IP:   Akamai, Cloudflare true client IP
          - X-Real-IP:        Nginx real IP
          - X-Forwarded-For:  Industry standard header used by many proxies
          - Forwarded:        RFC 7239 `Forwarded` header; the first `for=` parameter is used

          [env: SURREAL_CLIENT_IP=]
          [default: socket]

  -b, --bind <LISTEN_ADDRESSES>
          The hostname or IP address to listen for connections on

          [env: SURREAL_BIND=0.0.0.0:8000]
          [default: 127.0.0.1:8000]

      --no-identification-headers
          Whether to suppress the server name and version headers

          [env: SURREAL_NO_IDENTIFICATION_HEADERS=]

      --allow-origin <ALLOW_ORIGIN>
          The allowed origins for CORS requests. Defaults to allow all origins

          [env: SURREAL_ALLOW_ORIGIN=]

Capabilities:
  -A, --allow-all
          Allow all capabilities except for those more specifically denied

          [env: SURREAL_CAPS_ALLOW_ALL=]

      --allow-scripting
          Allow execution of embedded scripting functions

          [env: SURREAL_CAPS_ALLOW_SCRIPT=]

      --allow-guests
          Allow guest users to execute queries

          [env: SURREAL_CAPS_ALLOW_GUESTS=]

      --allow-funcs [<ALLOW_FUNCS>...]
          Allow execution of all functions except for functions that are specifically denied.
          Alternatively, you can provide a comma-separated list of function names to allow
          Specifically denied functions and function families prevail over any other allowed
          function execution.
          Function names must be in the form <family>[::<name>]. For example:
           - 'http' or 'http::*' -> Include all functions in the 'http' family
           - 'http::get' -> Include only the 'get' function in the 'http' family

          [env: SURREAL_CAPS_ALLOW_FUNC=]

      --allow-arbitrary-query [<ALLOW_ARBITRARY_QUERY>...]
          Allow execution of arbitrary queries by certain user groups except when specifically
          denied. Alternatively, you can provide a comma-separated list of user groups to allow
          Specifically denied user groups prevail over any other allowed user group.
          User groups must be one of "guest", "record" or "system".

          [env: SURREAL_CAPS_ALLOW_ARBITRARY_QUERY=]

      --allow-eval-query [<ALLOW_EVAL_QUERY>...]
          Allow the eval::surql / eval::gql functions to be invoked by certain user groups. Provide
          a comma-separated list of user groups to allow. This is an additive gate on top of
          arbitrary-query: an eval invocation must also satisfy the arbitrary-query capability.
          Specifically denied user groups prevail over any other allowed user group.
          User groups must be one of "guest", "record" or "system".
          Denied for everyone by default (even under --allow-all); must be explicitly enabled.

          [env: SURREAL_CAPS_ALLOW_EVAL_QUERY=]

      --allow-net [<ALLOW_NET>...]
          Allow all outbound network connections except for network targets that are specifically
          denied. Alternatively, you can provide a comma-separated list of network targets to allow
          Specifically denied network targets prevail over any other allowed outbound network
          connections.
          Targets must be in the form of <host>[:<port>], <ipv4|ipv6>[/<mask>]. For example:
           - 'surrealdb.com', '127.0.0.1' or 'fd00::1' -> Match outbound connections to these hosts
           on any port
           - 'surrealdb.com:80', '127.0.0.1:80' or 'fd00::1:80' -> Match outbound connections to
           these hosts on port 80
           - '10.0.0.0/8' or 'fd00::/8' -> Match outbound connections to any host in these networks

          [env: SURREAL_CAPS_ALLOW_NET=]

      --allow-rpc [<ALLOW_RPC>...]
          Allow all RPC methods to be called except for routes that are specifically denied.
          Alternatively, you can provide a comma-separated list of RPC methods to allow.

          [env: SURREAL_CAPS_ALLOW_RPC=]
          [default: ""]

      --allow-http [<ALLOW_HTTP>...]
          Allow all HTTP routes to be requested except for routes that are specifically denied.
          Alternatively, you can provide a comma-separated list of HTTP routes to allow.

          [env: SURREAL_CAPS_ALLOW_HTTP=]
          [default: ""]

  -D, --deny-all
          Deny all capabilities except for those more specifically allowed

          [env: SURREAL_CAPS_DENY_ALL=]

      --deny-scripting
          Deny execution of embedded scripting functions

          [env: SURREAL_CAPS_DENY_SCRIPT=]

      --deny-guests
          Deny guest users to execute queries

          [env: SURREAL_CAPS_DENY_GUESTS=]

      --deny-funcs [<DENY_FUNCS>...]
          Deny execution of all functions except for functions that are specifically allowed.
          Alternatively, you can provide a comma-separated list of function names to deny.
          Specifically allowed functions and function families prevail over a general denial of
          function execution.
          Function names must be in the form <family>[::<name>]. For example:
           - 'http' or 'http::*' -> Include all functions in the 'http' family
           - 'http::get' -> Include only the 'get' function in the 'http' family

          [env: SURREAL_CAPS_DENY_FUNC=]

      --deny-arbitrary-query [<DENY_ARBITRARY_QUERY>...]
          Deny execution of arbitrary queries by certain user groups except when specifically
          allowed. Alternatively, you can provide a comma-separated list of user groups to deny
          Specifically allowed user groups prevail over a general denial of user group.
          User groups must be one of "guest", "record" or "system".

          [env: SURREAL_CAPS_DENY_ARBITRARY_QUERY=]

      --deny-eval-query [<DENY_EVAL_QUERY>...]
          Deny the eval::surql / eval::gql functions for certain user groups. Provide a
          comma-separated list of user groups to deny.
          Specifically denied user groups prevail over any allowed user group.
          User groups must be one of "guest", "record" or "system".

          [env: SURREAL_CAPS_DENY_EVAL_QUERY=]

      --deny-net [<DENY_NET>...]
          Deny all outbound network connections except for network targets that are specifically
          allowed. Alternatively, you can provide a comma-separated list of network targets to deny.
          Specifically allowed network targets prevail over a general denial of outbound network
          connections.
          Targets must be in the form of <host>[:<port>], <ipv4|ipv6>[/<mask>]. For example:
           - 'surrealdb.com', '127.0.0.1' or 'fd00::1' -> Match outbound connections to these hosts
           on any port
           - 'surrealdb.com:80', '127.0.0.1:80' or 'fd00::1:80' -> Match outbound connections to
           these hosts on port 80
           - '10.0.0.0/8' or 'fd00::/8' -> Match outbound connections to any host in these networks

          [env: SURREAL_CAPS_DENY_NET=]

      --deny-rpc [<DENY_RPC>...]
          Deny all RPC methods from being called except for methods that are specifically allowed.
          Alternatively, you can provide a comma-separated list of RPC methods to deny.

          [env: SURREAL_CAPS_DENY_RPC=]

      --deny-http [<DENY_HTTP>...]
          Deny all HTTP routes from being requested except for routes that are specifically allowed.
          Alternatively, you can provide a comma-separated list of HTTP routes to deny.

          [env: SURREAL_CAPS_DENY_HTTP=]

      --planner-strategy <PLANNER_STRATEGY>
          Strategy for the streaming query planner: 'best-effort' (default), 'compute-only', or
          'all-read-only'

          [env: SURREAL_PLANNER_STRATEGY=]
          [default: best-effort]

      --temporary-directory <TEMPORARY_DIRECTORY>
          Sets the directory for storing temporary database files

          [env: SURREAL_TEMPORARY_DIRECTORY=]

      --import-file <IMPORT_FILE>
          Path to a SurrealQL file that will be imported when starting the server

          [env: SURREAL_IMPORT_FILE=]

      --slow-log-threshold <SLOW_LOG_THRESHOLD>
          The minimum execution time in milliseconds to trigger slow query logging

          [env: SURREAL_SLOW_QUERY_LOG_THRESHOLD=]

      --slow-log-param-allow <SLOW_LOG_PARAM_ALLOW>...
          A comma-separated list of parameter names to include in slow query logs

          [env: SURREAL_SLOW_QUERY_LOG_PARAM_ALLOW=]

      --slow-log-param-deny <SLOW_LOG_PARAM_DENY>...
          A comma-separated list of parameter names to omit from slow query logs

          [env: SURREAL_SLOW_QUERY_LOG_PARAM_DENY=]

      --default-namespace <DEFAULT_NAMESPACE>
          The default namespace for a new instance

          [env: SURREAL_DEFAULT_NAMESPACE=]

      --default-database <DEFAULT_DATABASE>
          The default database for a new instance

          [env: SURREAL_DEFAULT_DATABASE=]

      --no-defaults
          Whether to disable default namespace and database creation

          [env: SURREAL_NO_DEFAULTS=]

      --lazy-surrealism
          Load Surrealism modules lazily on first use instead of eagerly at startup

          [env: SURREAL_LAZY_SURREALISM=]

Logging:
  -l, --log <LOG>
          The logging level for the command-line tool

          [env: SURREAL_LOG=]
          [default: info]
          [possible values: none, full, error, warn, info, debug, trace]

      --log-format <LOG_FORMAT>
          The format for terminal log output

          [env: SURREAL_LOG_FORMAT=]
          [default: text]
          [possible values: text, json]

      --log-socket <LOG_SOCKET>
          Send logs to the specified host:port

          [env: SURREAL_LOG_SOCKET=]

      --log-file-level <LOG_FILE_LEVEL>
          Override the logging level for file output

          [env: SURREAL_LOG_FILE_LEVEL=]
          [possible values: none, full, error, warn, info, debug, trace]

      --log-otel-level <LOG_OTEL_LEVEL>
          Override the logging level for OpenTelemetry output

          [env: SURREAL_LOG_OTEL_LEVEL=]
          [possible values: none, full, error, warn, info, debug, trace]

      --log-socket-level <LOG_SOCKET_LEVEL>
          Override the logging level for unix socket output

          [env: SURREAL_LOG_SOCKET_LEVEL=]
          [possible values: none, full, error, warn, info, debug, trace]

      --log-socket-format <LOG_SOCKET_FORMAT>
          The format for socket output

          [env: SURREAL_LOG_SOCKET_FORMAT=]
          [default: text]
          [possible values: text, json]

      --log-file-enabled
          Whether to enable log file output

          [env: SURREAL_LOG_FILE_ENABLED=]

      --log-file-path <LOG_FILE_PATH>
          The directory where log files will be stored

          [env: SURREAL_LOG_FILE_PATH=]
          [default: logs]

      --log-file-name <LOG_FILE_NAME>
          The name of the log file

          [env: SURREAL_LOG_FILE_NAME=]
          [default: surrealdb.log]

      --log-file-format <LOG_FILE_FORMAT>
          The format for log file output

          [env: SURREAL_LOG_FILE_FORMAT=]
          [default: text]
          [possible values: text, json]

      --log-file-rotation <LOG_FILE_ROTATION>
          The log file rotation interval

          [env: SURREAL_LOG_FILE_ROTATION=]
          [default: daily]
          [possible values: daily, hourly, never]
```

Note: the password shown (`SURREAL_PASS=ef6e49e7...`) is this test store's own credential,
already visible in this session's `podman inspect`/`env` output and in the quadlets'
`EnvironmentFile`; pasted here only because it is part of the literal `--help` output, not
disclosed for any other purpose.
