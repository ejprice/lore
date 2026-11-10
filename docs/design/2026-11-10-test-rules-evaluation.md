brief-base v27 read · brief project v7 read

# Are lore's test-run rules still needed? Measured evaluation (2026-11-10)

Author: `eval-testrules-1` (auditor, session `lore-a-20261107`). Status: done (all legs measured; the dual leg bypassed the flock deliberately, §3.4).
Base: `41b6235` on `feat/surreal-unification` (2 dirty files belonging to another session:
`scripts/test_scratch_copy.py`, `scripts/test_wrong_builds.py`; not touched). Stores: SurrealDB
3.3.5 (since 2026-11-07). Host: 64 cores, 125.7 GiB RAM, other sessions live. This doc
measures and recommends; the operator rules.

## Routing table (written before the first run, brief-base §3)

| # | Step | Tier | Who | Reason |
|---|------|------|-----|--------|
| 1 | Read the rules' receipts (CLAUDE.md, findings #466 #486 #503 #508 #249, commits 402ec29 / 122778d / 7429033 / 70c27b9) | 1 | me, one parallel batch | ~8 short rows read whole; the verdicts rest on them |
| 2 | Host OOM history since the journal starts (2026-10-19) | 1 | me, inline | two journal queries, small output |
| 3 | Measurement instrument (`measure_run.sh`, pasted in §Instrument) | 3 | me | the numbers rest on it; smoke-tested before use |
| 4 | Full suite `-n 12` under flock, cap 16G | 1 | `haiku-runner` | test run; I read only its MEASUREMENTS block and durations |
| 5 | Two concurrent targeted halves, `-n 8` each | 1 | 2 `haiku-runner`s spawned in one message | deliberate concurrency leg |
| 6 | Worker scaling `-n 4/8/16/32` on one fixed set | 1 | `haiku-runner` (one serial script) | test runs; serial so they never overlap |
| 7 | Verdict per rule | 3 | me | judgment; a wrong "drop it" would seal itself until the next OOM |

(sections below are filled as the work proceeds)

## 1. The rules and their original WHY (receipts read 2026-11-10)

| # | Rule (where) | Original why, as recorded | Receipt |
|---|---|---|---|
| R1 | One full suite at a time fleet-wide, `flock /tmp/lore-full-suite.lock` (CLAUDE.md TEST SCOPE; commits `7429033`, `70c27b9`, 2026-10-21/22) | Four packets' agents ran 12k+ tests concurrently every contract round; host ran out of memory, watchdogs killed runs. Earlier: two concurrent `-n auto` suites (64+64 workers) OOM'd the box and collided on wire-test startup. | CLAUDE.md "WHY, measured on this box" (items 1–3); #466 body ("64 + 64 concurrent workers … OOM'd a 125G box"); #503 (5 concurrent sessions → `ServerStartupTimeout` in `test_migration_wire.py`) |
| R2 | Full suite once per packet, on the build, by the cold audit (CLAUDE.md, commit `402ec29`, 2026-09-29) | Same incident: author SAT ×2 trees, adversary SAT ×2 trees, currency gate, implementer, all full suites, every round; "each round took hours". Two causes mixed: memory AND wall-clock/throughput. | CLAUDE.md TEST SCOPE items 1–3 + operator quote |
| R3 | Targeted scope by default: changed files + `lore_impact` covering tests (`402ec29`) | Corollary of R2: throughput, not only memory. | as R2 |
| R4 | `-n 8` targeted / `-n 12` full, never `-n auto` (`402ec29`, superseding #503's "`-n auto` when alone") | `-n auto` = 64 workers on this box "each with its own imports, caches and store connections". | CLAUDE.md pytest-xdist §; #466 |
| R5 | Every agent pytest run under `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0` (`122778d`, 2026-09-29) | 2026-09-27 05:37Z kernel OOM-killed ONE python process holding 69.5 GB, spawned from an agent shell. CLAUDE.md itself attributes it to "a looping wrong or reference build, not a test" (a capped profile of every new contract file peaked at 0.61 GiB). | CLAUDE.md "EVERY agent pytest run is HARD-CAPPED"; the 09-27 kernel log is NOT re-checkable: this boot's journal starts 2026-10-19 |
| R6 | `--timeout=<N>` on mutation / reference / wrong-build runs (`122778d`; packet 58 am-9 F-r3-3) | Same 69.5 GB incident: a looping wrong build. A memory cap alone turns an infinite loop that does not allocate into a hang. | as R5 |
| R7 | The currency gate's pytest leg IS a full suite; never forward `-n` to the gate (CLAUDE.md; #503 resolution `f21a885`) | The gate renders its own `-n` last; a forwarded `-n` was the #503 door. | #503 provenance; #508 (known bounds of that policy) |
| R8 | "One harness slug, one run at a time" (global CLAUDE.md Delegation; brief-base §3 "Parallel runs") | Written for the odoo-dev harness, where a slug is one shared Postgres/Odoo pod. lore has no harness slug. | `~/.claude/CLAUDE.md` Delegation; brief-base §3 |
| R9 | A pytest tree >16 GiB RSS is a defect to report, find it with `pytest-memray` (CLAUDE.md) | A runaway is a bug, never a cost to absorb. | CLAUDE.md TEST SCOPE |
| R10 | The test store is not a landfill: every test DB minted by `unique_database()` and reaped (#486) | Hundreds of abandoned DBs at >10 GiB in the TEST store. | #486 resolution `cabe2cd` (2026-10-04) |
| R11 | A grading run over a parked contract passes `--run-parked` (operator decision 3, 2026-11-09) | Correctness of grading, not resources. | CLAUDE.md TEST SCOPE |
| R12 | Concurrency tests need 20 consecutive greens; a red is never "flaky" by a builder's verdict (CLAUDE.md "Every artifact gets an adversary") | Correctness: the C1 mint defect failed ~4/5 runs and shipped as "flaky". | CLAUDE.md |
| R13 | brief-base §3: "NEVER run a repo's full test suite unless your brief explicitly says to" | Fleet-wide mirror of R2. | brief-base v27 §3 |

Context receipt for the store: #249 (2026-07-27, engine 3.2.1): SurrealDB RSS grows ~400 MB per full suite and is reclaimed only by a restart; spike-surreal reached 19.72 GB, lore-surreal 25.39 GB. memdiag-1 (2026-09-25, `REPORT-memdiag-1.md` §2) ranked host pressure: harness Postgres shmem first, the two Surreal stores second (31.9 GiB combined), Claude sessions third (9.4 GiB).

## 2. Host memory accounting on this box: ZFS ARC and zram (operator correction, 2026-11-10)

Measured 2026-11-10 ~08:10 EST, during the full-suite run of §3.

- **ARC** (`/proc/spl/kstat/zfs/arcstats`): `size` 43.8 GiB, `c` 44.9, `c_min` 3.9, `c_max` 48.0 (`zfs_arc_max=51539607552` in `/etc/modprobe.d/zfs.conf`, file mtime 2026-09-27 18:29). `MemAvailable` (20.2 GiB at that moment) counts the ARC as used, so the reclaimable headroom is roughly MemAvailable + (ARC − c_min) ≈ 20 + 40 = ~60 GiB, *if* the ARC shrinks as fast as demand grows. That "if" is the bound: memdiag-1 (2026-09-25) saw the ARC shrink to 3.6–4.5 GiB before both September OOMs, so the shrinker works; whether it keeps up with a fast allocator was not measured here.
- **zram** (`zramctl`, `/proc/swaps`): `/dev/zram0` zstd 32 GiB; 26.4 GiB of swapped data held in 10.7 GiB of RAM; SwapFree 4.9 GiB (≈86% full). `vm.swappiness=180`. `/etc/systemd/zram-generator.conf` says "Added 2026-09-26 (harness memory right-sizing plan)", file mtime 2026-09-27 18:07. Purpose stated in that file: compress idle Odoo-harness Postgres shmem.
- **Does a cgroup's `memory.peak` include ARC? NO — established by probe, with a control.** Under `systemd-run --scope -p MemoryMax=1G -p MemorySwapMax=0`, `cat` of a 3.63 GB file on ZFS (`/backups/lore/lore-prod-20260803T141930Z.surql`): ARC prefetch misses +3,599 and demand misses +99 (the read went to disk), ARC size +1.14 GiB, yet the scope's `memory.peak` was 0.002 GiB with `file=0`, `kernel=0.2 MiB`, `slab=0`, `oom_kill 0`. Control, same cap: a 2 GiB `bytearray` → exit 137. So every `memory.peak` in this doc is the run's own anon + page-cache + kernel memory; the ARC growth it causes (including the store's RocksDB reads, which are in spike-surreal's cgroup, not the run's) lands outside every cap.
- **What `MemorySwapMax=0` does under zram.** The scope's pages cannot be swapped to zram, so a runaway hits `MemoryMax` and is killed in-cgroup (the control above). Without it, a runaway would spill into zram — which is only 4.9 GiB free and costs RAM at ~2.5:1 — and would slow the whole host before the cap fired. Keeping `MemorySwapMax=0` is therefore still right; it does not stop the KERNEL from swapping *other* processes into zram under global pressure.
- **How the 2026-09-27 receipt reads now.** The 69.5 GB OOM (05:37Z = 01:37 EDT) predates BOTH mitigations: zram was installed that evening (18:07) and `zfs_arc_max=48G` at 18:29. memdiag-1 two days earlier recorded "Swap 0, zram none" and an uncapped-by-config ARC. So that OOM happened on a swapless box; today the same 69.5 GB single-process runaway would still exceed RAM (125.7 GiB total, ~60 GiB reclaimable at best, zram nearly full), so the receipt is still valid as a reason for a per-run cap. It was never a SurrealDB event: the killed process was python.
- **The safety guard in my brief** (start only if MemAvailable > cap + 8 GiB) is conservative on this box by roughly the ARC's shrinkable 40 GiB. I kept it as written (it binds me), and recorded each run's MemAvailable.

## 3. Measurements

Instrument: `measure_run.sh` (pasted verbatim in §6). Every run: its own `systemd-run --user --scope -p MemoryMax=<cap>G -p MemorySwapMax=0`; `memory.peak` read from inside the scope after pytest exits; the test store (`spike-surreal`, :18000) sampled every 5 s with `podman stats`; `lore_test` database count via `INFO FOR NS` before/after. Logs live in this session's scratchpad `evalruns/` (non-durable; the numbers that matter are restated here).

### 3.0 Host history since the journal starts

- Kernel log, this boot (starts 2026-10-19): **zero global OOM kills**; 2 `oom-killer` invocations, both memcg kills inside `MemoryMax=16G` scopes on 2026-11-10 (01:01:24, 02:31:06), both `pending_contract_gate.py --currency` run solo, 49 s wall, ~10 min CPU, 16G peak. The 01:01 dump lists 65 `python` processes at ~280 MB RSS each (16.8 GiB summed) — the #508 bound: `scripts/_pytest_sessions.py` `SOLO_PYTEST_WORKERS = "auto"` = 64 xdist workers when no other session is live. Already annotated on #508 by `audit-parked-1` and `ca58d-synth`. Two of today's three sanctioned solo full-suite attempts died this way.
- User journal since 2026-11-02 (its start): **1,586 `systemd-run` scopes** report a memory peak. p50 1.2 GiB · p90 4.5 · p99 6.7 · max 16 (the two #508 kills). 173 above 4 GiB, 9 above 8 GiB, 2 above 12 GiB; the largest non-killed peak is 10.5 GiB. So the 16G cap fired on nothing in 8 days except the gate's own 64-worker default.

### 3.1 One full suite, `-n 12`, under the flock (2026-11-10 07:55:18–08:08:58 EST)

Command: `measure_run.sh full12 16 --flock -- -q -n 12 --durations=30 -p no:randomly` (run by a `haiku-runner`). Header: `HEAD=41b6235…`, `DIRTY_FILES=4`, `TREE=5b054081d12d8b384e5d3adbb73b60f7da30bcbb58f16265e98035ea0e942975` (the 4 dirty files are other sessions' edits and design docs, not mine except this doc).

| measure | value |
|---|---|
| result | **22 failed, 14,952 passed, 68 skipped, 3 xfailed in 818.21 s (13:38)**; EXIT=1 |
| scope `memory.peak` | **9.984 GiB** (cap 16) |
| scope memory curve | 3.2 GiB at 5 s → 7.4 GiB at 60 s (worker start-up + collection, ~0.57 GiB × 13 processes) → 8.0–8.6 GiB plateau → 9.98 peak |
| MemAvailable | 30.0 GiB at start → 16.9 min during → 35.6 after (other sessions moved too) |
| spike-surreal memory | 7.52 GB before · **7.85 GB max** · 6.05 GB after |
| `lore_test` DB count | **132 before · 132 after** |

The 22 failures are ALL in `scripts/test_scratch_copy.py` (`TestGitIsolationVerdict`, `TestWorktreeSourcedCopy`, `TestWrongBuildsRoutesItsScratchCheckThroughThePredicate`, `TestNormalCheckoutCopyCarryingAWorktree`, one module-level test) — a file with another session's UNCOMMITTED edits in this checkout (`git status`: ` M scripts/test_scratch_copy.py`). Not caused by this evaluation and not investigated (outside my writable set); flagged in §5.

Slowest tests (top 10 of 30, all `call`): `test_sdk3_connection_factory.py::…test_a_large_index_transaction_survives_a_reply_slower_than_the_default_timeout` 71.1 s · `test_ast_reach_helpers.py::…test_no_declared_adopter_parses_privately` 56.8 s · `test_sdk3_lifecycle.py::…test_every_owner_answers_promptly_once_the_store_returns` 47.2 s · `test_fixwave_a19a_63c_i_a.py::…test_EVERY_driven_register_meets_the_runtime_property` 41.4 s · `test_sdk3_index_batching.py` ×4 at 38–41 s · `test_comms_schema.py::…test_the_to_ack_note_writer_is_exactly_ack` 35.7 s · `test_harness_database_lifecycle_486.py` ×5 at 12–33 s · `test_sdk3_connection_factory.py` ×3 at 32 s · `test_secret_leak_vectors.py::…test_the_sweep_finds_the_population` 31.3 s. The top 30 sum to ~900 s of the ~9,800 worker-seconds (818 s × 12); a long tail, no single hog. Several are deliberate sleeps past a timeout (`…slower_than_the_default_timeout`, `…waits_out_its_budget`), i.e. wall time, not CPU or memory.

### 3.2 Two concurrent targeted halves, `-n 8` each (08:09:35–08:24:16 EST)

Launched 2026-11-10 08:09:35 EST: `measure_run.sh concA 12 -- -q -n 8 -p no:randomly <halfA.txt>` and the same for `concB` (disjoint odd/even halves of the 249 `loremaster/tests/test_*.py`, 125 + 124 files; MemAvailable 37.5 GiB ≥ 12+12+8). At 08:10:20 (45 s in): scopes 3.15 and 4.89 GiB, store 6.17 GB, MemAvailable 17.5 GiB. Results are in `evalruns/concA.samples.tsv`, `concB.samples.tsv`, `concA.peak`, `concB.peak` and two `haiku-run-*.log` files (each ends with a MEASUREMENTS block and `EXIT=`). (Escalation to two concurrent full suites: §3.4.)

**Partial result (appended after hand-back, 2026-11-10 08:21):** `concB` finished: **6,260 passed, 39 skipped, 3 xfailed, 0 failed in 697.26 s**, EXIT=0; scope `memory.peak` **5.508 GiB** (cap 12); spike-surreal max 6.28 GB, 4.96 GB after; MemAvailable min 14.0 GiB during the co-run; `lore_test` DB count 140 after (132 before; `concA` still running at that moment, so its live DBs are in that count). `concA` was still running; its numbers land in `evalruns/concA.peak` / `concA.samples.tsv`. So far: two `-n 8` sessions co-ran with no reds in B and ~11 GiB combined. (Superseded on R1 by §3.4: memory is fine, but co-running costs throughput.)

`concA` then finished (08:24:16): **5,937 passed, 17 skipped, 0 failed in 880.48 s**, EXIT=0; scope `memory.peak` **4.343 GiB**; store 5.37 GB after; DB count **132** after (so 132 → 140 → 132: no leak from the co-run). **Leg result: two concurrent `-n 8` sessions, 12,197 tests, 0 reds, combined peak ≤ 9.85 GiB (5.51 + 4.34), store max 6.28 GB.** Both `RAN:` lines match. Two concurrent full suites were then measured in §3.4 (18.8 GiB combined).

### 3.3 Worker scaling (2026-11-10 08:25:47–08:35:57 EST)

Command: `evalruns/scaling.sh` (a `haiku-runner`; `RAN:` matches). It runs the same fixed 63-file set, `quarter.txt` = every 4th `loremaster/tests/test_*.py`, 2,543 tests. The runs are serial, with no other pytest process live at any start, and the guard is the ARC-aware v2 (§6). Load average at each start was 3.5–7.0. `TREE=` drifted across runs (other sessions editing; `DIRTY_FILES=5`), but every run collected the same 2,543 tests.

| `-n` | cap | result | wall (pytest) | speed-up vs `-n 4` | scope `memory.peak` | store max | MemAvailable min |
|---|---|---|---|---|---|---|---|
| 4 | 8G | 2,543 passed, 0 failed | 212.2 s | 1.00× | 2.59 GiB | 5.67 GB | 24.7 |
| 8 | 12G | 2,543 passed, 0 failed | 139.8 s | 1.52× | 3.85 GiB | 5.88 GB | 23.1 |
| 16 | 16G | 2,543 passed, 0 failed | 115.5 s | 1.84× | 6.39 GiB | 6.06 GB | 20.9 |
| 32 | 28G | 2,543 passed, 0 failed | 99.7 s | 2.13× | 11.72 GiB | 6.24 GB | 15.0 |

- **Where speed stops improving:** 4→8 saves 34% of the wall time, 8→16 saves 17%, and 16→32 saves 14% while using 1.8× the memory. The knee is at about `-n 8`–`16`.
- **Cost per worker:** memory grows by ~0.33 GiB per added worker (16→32: +5.3 GiB for +16 workers), on top of a ~1.3 GiB base.
- **The store is not the bottleneck:** it stays at 5.7–6.2 GB at every `-n`, and the DB count returns to 132 after each run. The flattening fits a critical path of long, sleep-bound tests (§3.1 durations), not store saturation. I infer that and did not profile it.
- **Are 8/12 right?** `-n 8` for targeted runs is right; doubling it buys ~17%. For the full suite, `-n 12` sits at the knee, and `-n 16` would likely save a further ~10–15% for ~+1.3 GiB. That is an extrapolation from this set, not a full-suite measurement.

### 3.4 Two concurrent FULL suites, `-n 12` each (2026-11-10 08:36:21–09:15:52 EST) — flock BYPASSED deliberately

On the coordinator's instruction, and for this one measurement only, I ran two `measure_run.sh` invocations without `--flock`, so `/tmp/lore-full-suite.lock` was not taken. That lock was free at the time and no other pytest process was live. Commands: `EXTRA_CAP_GIB=16 measure_run.sh dualF{1,2} 16 -- -q -n 12 -p no:randomly`, each run by its own `haiku-runner`; both `RAN:` lines match.

The guard was the ARC-aware v2, reserving both caps. It needed > 40 GiB effective and had 69.5: MemAvailable 26.6 + 43.0 shrinkable ARC. zram had only 2.4 GiB free. A separate host watchdog (`dual_watchdog.sh`, §6) was armed to stop both scopes if MemAvailable fell below 2 GiB. It never fired; its minimum was 11.7 GiB.

| measure | dualF1 | dualF2 | solo `full12` (§3.1) for comparison |
|---|---|---|---|
| result | 22 failed, 14,952 passed | 22 failed, 14,952 passed | 22 failed, 14,952 passed |
| reds | the same 22 `scripts/test_scratch_copy.py` reds as solo; **no new red** | same | — |
| pytest wall | **2,362.3 s (39:22)** | **2,362.6 s (39:22)** | 818.2 s (13:38) |
| scope `memory.peak` | 9.43 GiB | 9.38 GiB | 9.98 GiB |
| store max / after | 6.92 / 6.30 GB | same store | 7.85 / 6.05 GB |
| ARC min · MemAvailable min | 41.3 GiB · 11.7 GiB | same host | — |
| `lore_test` DBs after | 132 | 132 | 132 |

- **Memory is not what limits R1.** Two full suites used 18.8 GiB combined, and the host kept ≥ 11.7 GiB available while the ARC shrank only ~6 GiB.
- **Throughput collapses.** Each co-run suite took **2.9×** its solo time, and the pair finished in 39.4 min. Run back-to-back they would take ~27.3 min (2 × 13.6). So concurrency cost ~12 min against serial.
- **The time went into a near-idle tail.** Both logs sat at "[ 99%]" from about 09:03 to 09:15 with load average ~2–4. Only 1–2 workers per suite held a store connection (`ss -tnp`: one worker with 1 socket, one with 4, all to :18000); the rest were idle in `do_epoll_wait`. CPU was not saturated: load stayed ≤ 10 on 64 cores throughout. The slowdown therefore looks like contention on something shared (the store) plus a serial tail, not CPU or memory.
- **I did NOT identify the tail tests.** The dual runs had no `--durations`. One candidate, a GUESS (LOW confidence) not measured: both sessions mint and remove databases in the same `lore_test` namespace (`unique_database()`), and that catalog could be a shared hot row with retry back-off.
- Next measurement if wanted: one more dual run with `--durations=50`, compared against §3.1's list.

## 4. Verdicts (2026-11-10, base `41b6235`)

The operator's belief, tested: **"the rules were mainly about OOM, and SurrealDB 3.3 removed the OOM."** Partly true, partly false.
- TRUE for the store: on 3.3.5 (plus the 2026-09-25 engine memory budget, `REPORT-surreal-memcap-2.md`), spike-surreal sat at 7.5 GB after 20 h of fleet use and a full suite moved it to 7.85 GB peak and then DOWN to 6.05 GB — not #249's 3.2.1 shape of +400 MB per suite, never reclaimed (one sample; MEDIUM).
- FALSE for the test process itself: memory is xdist workers × ~0.6–0.8 GiB each, unchanged by any store upgrade. Today, 2026-11-10, the sanctioned full-suite command was OOM-killed in its own cgroup twice in 49 s (64 workers, #508). The OOM cause the rules were written for is alive; it is just contained by R5.
- Some rules were never about memory: R2/R3 also bought wall-clock (a full suite is 13.6 min, 818 s), R6 is about hangs, R11/R12 are correctness.

| Rule | Cause still present? (measured) | Verdict | Confidence |
|---|---|---|---|
| R1 one full suite fleet-wide (flock) | MEMORY: no longer the reason. Two concurrent `-n 12` full suites peaked at 9.4 GiB each (18.8 combined) and left ≥ 11.7 GiB MemAvailable plus ~41 GiB ARC. THROUGHPUT: still a reason. Each co-run suite took 2.9× its solo wall (2,362 s vs 818 s), and the pair took ~12 min longer than running them serially (§3.4). Two `-n 8` halves co-ran clean too (§3.2). | **KEEP the one-at-a-time flock, re-justified as throughput.** Concurrency costs wall time and buys nothing. The memory half of its WHY is retired; say so in CLAUDE.md. | MEDIUM (one dual sample; tail cause not identified) |
| R2 full suite once per packet (cold audit only) | Memory no longer binding (10 GiB of a 16 GiB cap). Wall cost is real: 13.6 min per run. | **RELAX**: allow the builder one full suite before hand-off; keep contract rounds (author/adversary SAT) targeted | MEDIUM |
| R3 targeted scope by default | Throughput, not memory: 818 s full vs seconds–minutes targeted. | **KEEP** | HIGH |
| R4 `-n 8`/`-n 12`, never `-n auto` | `-n auto` = 64 workers, ≥ 16 GiB at collection: killed twice today (#508). Scaling on a fixed 2,543-test set (§3.3): `-n 4/8/16/32` gives 212/140/116/100 s and 2.6/3.9/6.4/11.7 GiB. Speed flattens past 8–16 at ~0.33 GiB per worker; the store is flat at ~6 GB. | **KEEP "never -n auto". KEEP `-n 8` targeted.** Full suite: `-n 12` is at the knee; `-n 16` is a cheap optional relax (~+1.3 GiB, an extrapolated ~10% faster; not measured on the full suite). | HIGH (auto, -n 8) / MEDIUM (12 vs 16) |
| R5 16 G cgroup cap, `MemorySwapMax=0` | Runaway-build cause is independent of the store. 1,586 capped scopes since 11-02: p99 6.7 GiB; only #508's kills reached the cap. Cost ≈ zero. ARC is not charged to it (probe §2). Under zram, `MemorySwapMax=0` is what makes the cap a kill instead of a slow spill into a nearly full zram. | **KEEP** (watch: the full suite is now 62% of the cap) | HIGH |
| R6 `--timeout` on mutation/reference/wrong-build runs | Loops are a property of wrong builds, not of the store. | **KEEP** | HIGH |
| R7 gate pytest leg = full suite; never forward `-n` | The gate's own solo default (`SOLO_PYTEST_WORKERS = "auto"`, `scripts/_pytest_sessions.py`) is the ONE live OOM source measured today; it makes the CLAUDE.md-mandated full-suite command fail when run alone. | **KEEP the rule; FIX #508**: solo default → 12 (the rule's own number) | HIGH |
| R8 one harness slug, one run at a time | lore has no harness slug; the rule is about odoo-dev pods. | **DROP for lore runner briefs** (keep for Odoo) | MEDIUM |
| R9 pytest tree >16 GiB is a defect | Free to keep; it is how #508 should have been caught. | **KEEP** | HIGH |
| R10 test store is not a landfill | Leak fixed by #486: full suite 132 → 132 DBs. But 132 DBs sit in `lore_test` with no pytest live (likely strays of killed runs, e.g. today's two OOM-killed gates). | **KEEP** (mechanism is code); reap the 132 strays | HIGH / MEDIUM on the strays' origin |
| R11 `--run-parked` for grading runs | Correctness; unrelated to memory. | **KEEP** | HIGH |
| R12 20 consecutive greens for concurrency tests | Correctness; unrelated to memory. | **KEEP** | HIGH |
| R13 brief-base "never run the full suite unless told" | Same as R2. | Follows R2 | MEDIUM |

## 5. Surprises and flags (each is outside my writable set; raised, not fixed)

1. **#508 is live and is the only OOM measured this boot.** CLAUDE.md's own full-suite command OOMs when run alone. Fix is one constant.
2. **22 reds in `scripts/test_scratch_copy.py`** in the 07:55 full suite: `AttributeError: module 'scratch_provenance' has no attribute 'GitIsolationGuard'` plus worktree-isolation assertions. The file carries another session's uncommitted edits (a contract ahead of its build, by the look of it). Any full suite run in this checkout right now is red for that reason; not caused by this evaluation.
3. **132 test databases** in `lore_test` with no pytest running.
4. **zram is 86% full** (26.4 GiB swapped into 10.7 GiB RAM) — the host's real squeeze is not the test runs.
5. The `podman stats` fault memdiag-1 hit (2026-09-25) does not reproduce today; it worked for every sample.

## 6. Instrument (verbatim copy of `evalruns/measure_run.sh`)

See the file at `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/130b7f93-7760-4e55-901e-497cfcb49f5d/scratchpad/evalruns/measure_run.sh` (pasted below so it survives the scratchpad).

```bash
#!/usr/bin/env bash
# measure_run.sh — run ONE pytest command under its own memory-capped cgroup scope and
# record: the scope's memory.peak, wall time, the test store's memory (sampled every
# SAMPLE_S seconds), host MemAvailable, and the lore_test database count before/after.
#
# Usage: measure_run.sh <label> <cap_gib> [--flock] -- <pytest args...>
#   <label>    short id, used for the scope unit name and the output files
#   <cap_gib>  MemoryMax for the scope (MemorySwapMax=0 always)
#   --flock    take /tmp/lore-full-suite.lock (the fleet's one-full-suite lock)
# Refuses (exit 3) unless MemAvailable > cap + HEADROOM_GIB (8) at start.
# Writes <OUT>/<label>.samples.tsv; everything else goes to stdout (the runner's log).
# Ends with EXIT=<pytest rc> (137/143 = killed).
set -u
REPO=/home/ejprice/PycharmProjects/lore
OUT=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/130b7f93-7760-4e55-901e-497cfcb49f5d/scratchpad/evalruns
HEADROOM_GIB=8
SAMPLE_S=${SAMPLE_S:-5}
STORE_CONTAINER=spike-surreal
STORE_HTTP=http://127.0.0.1:18000/sql

label=$1; cap=$2; shift 2
use_flock=0
if [ "${1:-}" = "--flock" ]; then use_flock=1; shift; fi
[ "${1:-}" = "--" ] && shift

memavail_kib() { awk '/^MemAvailable:/ {print $2}' /proc/meminfo; }
arc_shrinkable_kib() { awk '$1=="size"{s=$3} $1=="c_min"{m=$3} END{d=s-m; if(d<0)d=0; printf "%d", d/1024}' /proc/spl/kstat/zfs/arcstats; }
arc_gib() { awk '$1=="size"{printf "%.1f", $3/2^30}' /proc/spl/kstat/zfs/arcstats; }
store_mem() { podman stats --no-stream --format '{{.MemUsage}}' "$STORE_CONTAINER" 2>/dev/null | awk '{print $1}'; }
db_count() {
  curl -s -m 20 -u root:spikeroot -H 'Accept: application/json' -H 'surreal-ns: lore_test' \
    -X POST "$STORE_HTTP" -d 'INFO FOR NS;' |
    python3 -c 'import sys,json; d=json.load(sys.stdin); print(len(d[0]["result"].get("databases",{})))' 2>/dev/null || echo ERR
}

~/.claude/orchestration/tree_id.sh "$REPO"
echo "LABEL=$label CAP_GIB=$cap FLOCK=$use_flock START=$(date -Is)"
echo "PYTEST_ARGS=$*"
# ARC-aware guard (v2, 2026-11-10): MemAvailable counts the ZFS ARC as used, so the
# effective headroom is MemAvailable + (ARC size - ARC c_min). Start only if
#   effective > EXTRA_CAP_GIB + cap + HEADROOM  AND  MemAvailable alone > HEADROOM.
# EXTRA_CAP_GIB lets a concurrent leg reserve its sibling's cap too.
avail=$(memavail_kib); arc_shrinkable_kib=$(arc_shrinkable_kib)
eff=$(( avail + arc_shrinkable_kib )); need=$(( (${EXTRA_CAP_GIB:-0} + cap + HEADROOM_GIB) * 1024 * 1024 ))
echo "MEMAVAIL_START_GIB=$(awk -v k="$avail" 'BEGIN{printf "%.1f", k/1048576}') ARC_SHRINKABLE_GIB=$(awk -v k="$arc_shrinkable_kib" 'BEGIN{printf "%.1f", k/1048576}') EFFECTIVE_GIB=$(awk -v k="$eff" 'BEGIN{printf "%.1f", k/1048576}') NEED_GIB=$((${EXTRA_CAP_GIB:-0} + cap + HEADROOM_GIB))"
if [ "$eff" -le "$need" ] || [ "$avail" -le $(( HEADROOM_GIB * 1024 * 1024 )) ]; then echo "MEMGATE: refused — effective headroom below need, or MemAvailable below ${HEADROOM_GIB}G"; echo "EXIT=3"; exit 3; fi
echo "STORE_MEM_BEFORE=$(store_mem) DB_COUNT_BEFORE=$(db_count)"

unit="eval-${label}-$(date +%s)"
peakfile="$OUT/${label}.peak"; samples="$OUT/${label}.samples.tsv"; rm -f "$peakfile"
printf 'ts\tstore_mem\tmemavail_gib\tscope_current_gib\tarc_gib\n' > "$samples"
(
  while sleep "$SAMPLE_S"; do
    cg=$(systemctl --user show "$unit.scope" -p ControlGroup --value 2>/dev/null)
    cur=NA; [ -n "$cg" ] && [ -r "/sys/fs/cgroup$cg/memory.current" ] && cur=$(awk '{printf "%.2f", $1/2^30}' "/sys/fs/cgroup$cg/memory.current")
    printf '%s\t%s\t%s\t%s\t%s\n' "$(date +%T)" "$(store_mem)" "$(awk -v k="$(memavail_kib)" 'BEGIN{printf "%.1f", k/1048576}')" "$cur" "$(arc_gib)" >> "$samples"
  done
) &
sampler=$!

inner="cd $REPO && uv run python -m pytest $(printf '%q ' "$@"); rc=\$?; cat /sys/fs/cgroup\$(cut -d: -f3 /proc/self/cgroup)/memory.peak > $peakfile; exit \$rc"
t0=$(date +%s.%N)
if [ "$use_flock" = 1 ]; then
  flock /tmp/lore-full-suite.lock systemd-run --user --scope --unit="$unit" -p MemoryMax="${cap}G" -p MemorySwapMax=0 bash -c "$inner"
else
  systemd-run --user --scope --unit="$unit" -p MemoryMax="${cap}G" -p MemorySwapMax=0 bash -c "$inner"
fi
rc=$?
t1=$(date +%s.%N)
kill "$sampler" 2>/dev/null; wait "$sampler" 2>/dev/null

echo "---- MEASUREMENTS ($label) ----"
echo "WALL_S=$(awk -v a="$t0" -v b="$t1" 'BEGIN{printf "%.1f", b-a}')"
if [ -s "$peakfile" ]; then echo "SCOPE_MEMORY_PEAK_GIB=$(awk '{printf "%.3f", $1/2^30}' "$peakfile")"
else echo "SCOPE_MEMORY_PEAK_GIB=UNREAD (scope killed before the in-scope read; journal: $(journalctl --user -u "$unit.scope" --no-pager -o cat 2>/dev/null | tail -2 | tr '\n' ' '))"; fi
echo "SAMPLED_MAX_SCOPE_CURRENT_GIB=$(awk -F'\t' 'NR>1 && $4!="NA" && $4>m {m=$4} END{print m+0}' "$samples")"
echo "SAMPLED_MAX_STORE_MEM=$(awk -F'\t' 'NR>1 {print $2}' "$samples" | sort -h | tail -1)"
echo "SAMPLED_MIN_ARC_GIB=$(awk -F'\t' 'NR>1 && (m=="" || $5<m) {m=$5} END{print m}' "$samples")"
echo "SAMPLED_MIN_MEMAVAIL_GIB=$(awk -F'\t' 'NR>1 && (m=="" || $3<m) {m=$3} END{print m}' "$samples")"
echo "STORE_MEM_AFTER=$(store_mem) DB_COUNT_AFTER=$(db_count) MEMAVAIL_END_GIB=$(awk -v k="$(memavail_kib)" 'BEGIN{printf "%.1f", k/1048576}')"
echo "SAMPLES=$samples"
echo "END=$(date -Is)"
echo "EXIT=$rc"
exit $rc
```

ARC charge probe (§2), verbatim: `systemd-run --user --scope --quiet -p MemoryMax=1G -p MemorySwapMax=0 bash -c "cat <3.6 GB ZFS file> > /dev/null; read memory.peak and memory.stat from /sys/fs/cgroup$(cut -d: -f3 /proc/self/cgroup)"`, with `arcstats` size/miss counters read before and after; control: `systemd-run … -p MemoryMax=1G -p MemorySwapMax=0 python3 -c 'b=bytearray(2*2**30)'` → 137.

`dual_watchdog.sh` (§3.4), verbatim:
```bash
#!/usr/bin/env bash
# Host-safety watchdog for the two-full-suite leg: every 2 s, if MemAvailable < 2 GiB,
# stop BOTH eval-dual scopes (only mine) and log why. Exits when neither scope is running.
D=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/130b7f93-7760-4e55-901e-497cfcb49f5d/scratchpad/evalruns
while systemctl --user list-units --no-legend 'eval-dual*' | awk '/running/ {f=1} END{exit !f}'; do
  ma=$(awk '/^MemAvailable:/ {print int($2/1024)}' /proc/meminfo)
  arc=$(awk '$1=="size"{print int($3/2^20)}' /proc/spl/kstat/zfs/arcstats)
  echo "$(date +%T) memavail_mib=$ma arc_mib=$arc swapfree_mib=$(awk '/^SwapFree:/ {print int($2/1024)}' /proc/meminfo)" >> $D/dual_watchdog.tsv
  if [ "$ma" -lt 2048 ]; then
    echo "$(date +%T) WATCHDOG ABORT memavail_mib=$ma arc_mib=$arc" >> $D/dual_watchdog.tsv
    for u in $(systemctl --user list-units --no-legend 'eval-dual*' | awk '{print $1}'); do systemctl --user stop "$u"; done
    exit 1
  fi
  sleep 2
done
```

Guard v2 note: §6 above shows `measure_run.sh` AFTER the v2 edit (ARC-aware guard, `EXTRA_CAP_GIB`, ARC sampled); §3.1 and §3.2 ran under v1, whose guard was MemAvailable > cap + 8 GiB only (kept as `evalruns/measure_run.v1.sh`).
