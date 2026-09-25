brief-base v16 read · brief project v7 read

# REPORT memdiag-1 — host memory-pressure diagnosis (measured 2026-09-25 15:31–15:49 EDT, HEAD 4dca89e)

## SUMMARY BLOCK
- **State:** done. Diagnosis only; nothing was killed, stopped, edited or dropped. Standing by.
- **Deviations:** (1) `podman stats --no-stream` fails on this host (`unknown FS magic on /run/user/1000/netns/...`), so container memory was read from cgroup v2 `memory.current`/`memory.stat` instead. That source is more authoritative, not less. (2) `/proc/slabinfo` is root-only, so the per-cache slab split is unmeasured; it is not needed for the conclusions. (3) The kernel journal only reaches back to 2026-09-19. Earlier OOM history comes from atop raw logs.
- **Top 3 causes, ranked (GiB, measured 2026-09-25 15:32):**
  1. **pp-odoo harness Postgres pods: 23.7 GiB shmem now; 55.6 GiB at the 09-24 OOM; ~97 GiB at the 09-14 mass-OOM.** Each pod runs `shared_buffers=8GB`. A pg_restore touches the whole pool, and on a no-swap host that is pinned, unreclaimable shmem (~8.3 GiB per pod) until the pod dies. Three pods are alive now (ctx250, costperf, 0ly8). This is the pressure driver in **every** OOM cluster on record. HIGH.
  2. **The two SurrealDB stores: 31.9 GiB combined** (spike-surreal :18000 at 16.9 GiB, lore-surreal :18500 PROD at 14.9 GiB). Neither quadlet sets `Memory=`. The 8 GiB block-cache cap does NOT bound RSS: the memory manager budgets 12 GiB, prod was OOM-killed at 18.6 GiB anon on 09-24, and its predecessor peaked at 24.6 G (systemd receipt). Both stores jumped from 1–2 GiB to 15–19 GiB on 2026-09-24 between 06:00 and 16:00. HIGH on the numbers; cause of the surge undetermined (LOW).
  3. **Claude Code sessions plus their MCP children: 9.4 GiB** (22 tmux scopes; 6 top-level sessions and 15 agents, ~0.3–0.4 GiB each). No single straggler. HIGH.
  - ARC is **not** a cause, confirmed by atop: it shrank to 3.6–4.5 GiB before both recent OOMs. The operator made the same ruling mid-run.
- **Packages considered:** none (no mechanism specified).
- **Odoo-20 portability:** n/a (no Odoo seam touched).
- **Reuse ledger:** none.
- **Graded:** n/a (measurement of the host, not of an artifact) · HEAD-at-report 4dca89e.
- **Decisions needed:** 3, all operator-owned. R1: Postgres harness `shared_buffers`, which belongs to the odoo-dev harness owner. R2: `Memory=`/OOM-priority on the Surreal quadlets. R6: the failing DIMM (EDAC). See §6.
- **Receipts:** §2 table · §4 OOM history · instruments pasted verbatim in §8 · raw captures in this session's scratchpad `memdiag/` (scan1.tsv, timeline.txt, oom_0923.txt, oom_0924.txt, oom_hist_atop.txt, surreal_trend.txt). Those are non-durable; the load-bearing numbers are restated in this report.

Capability check: all demanded tools were available. lore was reachable (registered as `memdiag-1`, session `63c-20260924`). No sudo was used. grep/rg were avoided per #473; all filtering was done with awk.

---

## 1. Snapshot (2026-09-25 15:31:26 EDT; `/proc/meminfo`)
MemTotal 125.7 GiB · MemAvailable 30.6 GiB · MemFree 17.3 GiB · **Shmem 23.7 GiB** · AnonPages 50.0 GiB · Cached 33.5 GiB (includes the shmem, so only ~10 GiB is reclaimable file cache) · SUnreclaim 9.7 GiB · SReclaimable 4.6 GiB · PageTables 0.46 GiB · **Swap 0, zram none** · Committed_AS 182 GiB against CommitLimit 63 GiB (`overcommit_memory=0`, heuristic). PSI memory avg10/60/300 = 0.00 at snapshot time.

⚠ `free`'s "buff/cache ~39 GiB" **overstates headroom**: ~24 GiB of it is Postgres shmem that cannot be reclaimed on a swapless box. MemAvailable already accounts for this; buff/cache does not. HIGH.

## 2. Where every GiB goes (cgroup v2, 2026-09-25 ~15:33)
| owner | GiB | of which | receipt |
|---|---|---|---|
| **user@1000.service total** | **84.8** | anon 49.7 · file 32.4 (**shmem 23.6**) | `memory.stat` |
| ├ spike-surreal.service (:18000 test) | 17.6 | anon 16.9 · peak 17.9 | pid 1753451, up 261.6 h |
| ├ lore-surreal.service (:18500 PROD) | 14.7 | anon 14.5 · **peak 21.57** since 09-24 15:19 restart | pid 4058159, up 24.2 h |
| ├ pod pp-odoo-test-ctx250 (4dd609…) | 15.9 | shmem 8.26 (pg) + one odoo proc 7.0 GiB anon (pid 3923652, `-d ppt-apps15-test-ctx250`, 0.5 h old, backend "idle in transaction") | owner: pp-odoo session, agent gh250-green (cwd `odoo-custom-wt-ctx250`) MEDIUM |
| ├ pod pp-odoo-test-costperf (0d0304…) | 9.2 | shmem 8.26 | pod 7 h old; agent adversary-pb/contract-pb (`odoo-custom-wt-costperf`) MEDIUM |
| ├ pod pp-odoo-test-0ly8 (139b09…) | 6.8 | shmem 6.08 | pod 12 days old, postmaster up 4 d |
| ├ 22 tmux-spawn scopes (Claude sessions + MCP children) | 9.4 | 0.26–0.69 each | §5 |
| ├ mcp-qdrant.service | 2.1 | peak 5.7 | killed in the 09-23 OOM |
| ├ lore-lore (libpod-efbf…) | 0.55 | | healthy |
| └ other app.slice services and 11 github-mcp-server containers | ~0.6 | negligible | |
| system.slice | 1.2 | | |
| **Kernel, uncharged** (MemTotal − cgroups − MemFree) | ~20 | ARC 13.3–14.2 (**shrinks under pressure; not a cause**) + SUnreclaim 9.7 (overlaps ARC metadata) + vmalloc 3.4 | arcstats, meminfo |
| MemFree | 17.3 | | |

Postgres `shared_buffers=8GB` is identical on all three pods (postmaster cmdlines, pids 3909942 / 2748492 / 2081621), with `effective_cache_size=32GB`, `maintenance_work_mem=2GB`, `work_mem=128MB`. HIGH.

## 3. Orphan / straggler candidates
**None are proven orphans.** I found no reparented pytest/xdist workers, no bound uvicorn servers, and no `dart` fleet (the only processes parented to PID 1 or the user systemd are daemons: journald, atop, fwupd, rclone). Every candidate below belongs to another session and is `needs-other-session`:

| pid / object | owner | RSS | age | evidence |
|---|---|---|---|---|
| pod pp-odoo-test-0ly8 (pg 2081621 + odoo) | pp-odoo session (not attributed) | 6.8 GiB | pod 12 d | oldest harness pod; its last activity was a test (`festive_fermat` ephemeral container, 3 min old at scan) — **ALIVE, in use** |
| pod pp-odoo-test-ctx250 | gh250 team (session-7250b102) | 15.9 GiB | 2 d | active (ephemeral `ecstatic_yalow` 32 min old). The 7 GiB odoo process 3923652 is a live run. |
| pod pp-odoo-test-costperf | pb team (session-4bafeb07) | 9.2 GiB | 7 h | active (`admiring_saha` 14 min old) |
| team session-818bede7 (packetdoc-65, packetdoc-57-58-11c, packetdoc-64) | lore plan-review (Fable lead pid 3795065, MEDIUM) | 0.83 GiB | 25 h | the plan review closed 09-24; these three are likely finished-but-resident |
| tdd-contract-fixa (session-5d5e7f41), gh250-contract (session-7250b102), design-sidecar-a36 (session-d2a6ab05) | odoo / mobile sessions | ~0.3 GiB each | 53 h / 38 h / 31 h | old, but sidecars are legitimately long-lived |
| 11 `github-mcp-server` containers (thirsty_hopper … exciting_tesla) | per-session stdio MCPs | ~0.05 GiB total | 4 h – 2 wk | some date from sessions that look ended; negligible memory |
| pod `pp-odoo-test` (Exited), `pod_nsa`/`pod__odoo12` (Created) | — | 0 | | no memory cost |

**Per-test Surreal DBs:** spike-surreal's data dir is **130 MB on disk (2 SST files)** against **17 GiB RSS**. The RSS is NOT leftover per-test data; it is in-process memory (cache/memtables plus retained heap). HIGH on the sizes, MEDIUM on the interpretation. I made no DB listing query (it would need credentials and was not necessary).

## 4. OOM history (kernel journal from 09-19; atop raw logs from 08-27 boot)
Since boot, cgroup counters show **429 oom_kills under `/sys/fs/cgroup/user.slice`**: 357 in user-1000.slice (354 of them in since-dead scopes), 64 in user-49004 (`podmanuser`, `/srv/podman`), 1 each in 49002 and 49005, and 2 in system.slice. All events were `global_oom` (CONSTRAINT_NONE); no cgroup limit was ever hit. HIGH.

| when (EDT) | kills | shmem at the time | victims / what was resident | source |
|---|---|---|---|---|
| 09-03 10:00–20:50 | 5 | 32–50 GiB | (pre-journal) | atop |
| 09-09 09:00–09:20 | 4 | 42 GiB | (pre-journal) | atop |
| 09-11 12:10 | 3 | 45 GiB | (pre-journal) | atop |
| 09-13 13:10–21:30 | 6 | 57–84 GiB | (pre-journal) | atop |
| 09-14 00:10–08:20 | 6 | 84.5 GiB, avail 1.5 GiB | (pre-journal) | atop |
| **09-14 15:20–15:50** | **404** | **97 GiB** | mass OOM storm; shmem dropped to 47 GiB after it (≈6 harness pods died) | atop |
| 09-23 22:09:34 | 2 | 38.6 GiB after | victims: a **postgres** backend (8.4 GiB shmem-rss) and **mcp-qdrant** (2.1 GiB). Trigger: **96 `dart` processes holding ~51 GiB anon** (`dart:scan_call_` 40.8 G + `dart` 5.8 G + `dart:collect_co` 4.5 G), attributable to `mobile_pricepaper_smoke` (it has a `dart/` tree; MEDIUM) | kernel + dump |
| **09-24 15:19:54** | 1 | **55.6 GiB (kernel: shmem 58.3 GB)**, avail 5.7 GiB at 15:00 | victim **lore-surreal PROD** (anon-rss 18.6 GiB, oom_score_adj 200). Resident: spike-surreal ~8.8 GiB, ~6 Postgres harness instances, 52 python procs 13 GiB (pytest workers among them), 17 odoo 4.4 GiB, Claude ~5 GiB. Store auto-restarted in 3 s (quadlet). | kernel + dump |

The pattern is HIGH confidence: every OOM cluster sits on a shmem plateau of ≥40 GiB built by harness Postgres pods. The "last straw" varies (a dart fleet, a Surreal surge, pytest workers). ARC was already shrunk to 3.6–5.5 GiB at each event (atop `zfarc`).

## 5. Surreal growth (atop PRM samples; GiB)
| time | spike-surreal | lore-surreal PROD |
|---|---|---|
| 09-15 → 09-24 06:00 | 0.8 → 1.8 | 0.7 → 1.2 |
| 09-24 12:00 | 1.7 | **14.2** |
| 09-24 15:00 | 8.8 | **19.0** → OOM-killed 15:19 |
| 09-24 20:00 | 13.7 | 8.1 (new pid) |
| 09-25 06:00 | 16.0 | 13.0 |
| 09-25 15:00 | 16.9 | 15.0 |
| 09-25 15:45 | 16.9 | 16.8 **transient** → 14.9 by 15:46 |

Both are decelerating toward a plateau (MEDIUM): spike at ~17 GiB, prod at ~15 GiB steady with bursts to 21.6 GiB (cgroup `memory.peak`). The engine's own budget is 12 GiB (`total memory limit: 12884901888`; cache 8 GiB + 32 × 128 MiB write buffers, boot log 09-24 15:19:57), so ≥3–9 GiB lives outside RocksDB accounting (query heap / allocator retention; LOW on mechanism). What drove the 09-24 06:00–15:00 surge on BOTH stores is **undetermined** (LOW). Candidates: the fleet's full suites against spike; unknown heavy traffic against prod.

## 6. Headroom model (estimate; no suite was running during this pass, so cost is NOT re-measured)
- **Suite cost:** I did not measure it. The lead's figure of 6–7 GiB for `-n 12` is inherited and unverified. At the 09-24 OOM, 52 python processes held 13 GiB anon, but that mixes suites with MCP/odoo processes, so it does not isolate a suite. `-n 8` ≈ 4.5–5 GiB by linear scaling (LOW).
- **Steps that arrive without the lead's control:** +8.3 GiB per new harness pod (one pg_restore, minutes). +6.6 GiB prod Surreal burst (peak 21.6 vs steady 15.0), and plausibly a similar surge on spike. +~50 GiB for a dart fleet (09-23 precedent). The kernel floor/reserve is ~4 GiB.
- **How many suites fit now (avail ≈ 30 GiB):** reserve one pod step (8.3) + one Surreal burst (6.6) + floor (4) → ~11 GiB spendable → **ONE `-n 12` suite, not two.** MEDIUM.
- **The lead's thresholds:** `-n 12` at ≥23 and `-n 8` at ≥20 are **about right as launch gates** (23 − 7 = 16 left, which absorbs one step of either kind). The **12 GiB watchdog is too low** (MEDIUM): a single harness restore (8.3 GiB) or Surreal burst (6.6 GiB) takes 12 → ≤5 GiB inside one poll interval, which is below where the kernel starts killing (09-24 ran out at avail ≈ 2–5 GiB). Recommend a **15 GiB kill-line with ≤10 s polling**. The thresholds only guard what the lead launches; they cannot see other sessions' pods, which are the dominant variable.

## 7. RECOMMENDATIONS
| # | action | who | GiB recovered | risk |
|---|---|---|---|---|
| R1 | Cut harness Postgres `shared_buffers` from 8GB to **2GB** (and `effective_cache_size` to 8GB) in the pp-odoo harness pod template. A throwaway `fsync=off` harness does not need an 8 GB pool; ZFS/page cache serves reads. | **needs-operator-approval** (harness owner: odoo-dev tooling), executed by **needs-other-session** | **~6 GiB per pod** (~18 now; ~40+ at the 09-14/09-24 peaks) | slower cold queries in harness tests (LOW risk, throwaway DBs) |
| R2 | Put a `Memory=`/`MemoryMax` on **spike-surreal** (e.g. 20G) so it hits a *local* cgroup OOM instead of joining a global one, and raise its OOM priority above prod (`PodmanArgs=--oom-score-adj=1000`; rootless can raise but not lower). Leave prod unlimited or set a generous `MemoryHigh` (≥24G) so it throttles rather than dies. | **needs-operator-approval** (quadlet edits) | 0 steady; **removes prod as a preferred global victim** (today both sit at adj 200 and prod was the 09-24 victim) | a spike cap too tight kills test runs mid-suite; size it from memory.peak |
| R3 | Cap concurrent harness pods (e.g. ≤2 live at once) or reap idle ones on a TTL. 0ly8 is 12 days old. | **needs-other-session** (pp-odoo sessions) / operator policy | 6.8–9.2 per pod reaped | loses a warm harness |
| R4 | Recycle **spike-surreal** (test store) at a quiet moment to drop its retained ~15 GiB. **Not while `adversary-63c-i-a-r4b-fix` or any suite is running.** | **lead-can-do** only if the lead's grant covers restarting the test store; otherwise needs-operator-approval | ~15 (it regrows under suite load, per §5) | interrupts any in-flight test run using :18000 |
| R5 | Raise the lead's watchdog kill-line from 12 → **15 GiB, ≤10 s poll**. Keep the launch gates at 23/20 and never run 2 suites concurrently. | **lead-can-do** | 0 (it prevents OOM) | more false aborts of the lead's own runs |
| R6 | **Hardware:** 154 identical EDAC corrected errors on `mc#0 csrow#3 channel#2 page 0xf2da61`, 3 pages hwpoisoned (`HardwareCorrupted: 4 kB`); MCE lines daily 56–321 since 09-19. Schedule a DIMM check/replacement. | **needs-operator-approval** | 0 | a correctable error on one page can become uncorrectable (host crash) — unrelated to the OOMs, but real (HIGH that errors are logged; MEDIUM on DIMM degradation) |
| R7 | The `mobile_pricepaper_smoke` dart fleet (96 procs / ~51 GiB on 09-23) needs a concurrency cap on its dart/Flutter worker count. | **needs-other-session** | up to ~50 at burst | none |
| R8 | Reap the three finished `packetdoc-*` agents (session-818bede7) and stale github-mcp-server containers. | **needs-other-session** (their lead) | ~0.9 | low |

**No immediate-threat message was sent** (§ brief): during 15:42–15:48, MemAvailable held flat at 29.4–32.0 GiB, with no downward trend and PSI at 0.00. The standing risk is structural: one new harness restore + one Surreal burst + one suite ≈ 22 GiB of steps against 30 GiB available.

## 8. Instruments (pasted verbatim, per brief-base §1)
Per-process scan, `procscan.py` (read-only):
```python
#!/usr/bin/env python3
"""Read-only per-process memory attribution scan (memdiag-1, 2026-09-25)."""
import os, pwd, sys, time
CLK_TCK = os.sysconf("SC_CLK_TCK")
with open("/proc/uptime") as uptime_file:
    UPTIME_S = float(uptime_file.read().split()[0])
def read_text(path):
    try:
        with open(path, "rb") as handle:
            return handle.read().decode(errors="replace")
    except OSError:
        return None
def kv_kb(text, keys):
    out = {}
    if not text:
        return out
    for line in text.splitlines():
        name, _, rest = line.partition(":")
        if name in keys:
            out[name] = int(rest.split()[0])
    return out
rows = []
for entry in os.listdir("/proc"):
    if not entry.isdigit():
        continue
    base = f"/proc/{entry}"
    status = read_text(f"{base}/status")
    if status is None:
        continue
    fields = kv_kb(status, ("VmRSS", "RssAnon", "RssFile", "RssShmem", "VmSwap"))
    if not fields.get("VmRSS"):
        continue
    uid = int([l for l in status.splitlines() if l.startswith("Uid:")][0].split()[1])
    ppid = int([l for l in status.splitlines() if l.startswith("PPid:")][0].split()[1])
    try:
        user = pwd.getpwuid(uid).pw_name
    except KeyError:
        user = str(uid)
    rollup = kv_kb(read_text(f"{base}/smaps_rollup"), ("Pss",))
    stat = read_text(f"{base}/stat") or ""
    try:
        start_ticks = int(stat.rsplit(")", 1)[1].split()[19])
        age_h = (UPTIME_S - start_ticks / CLK_TCK) / 3600
    except (IndexError, ValueError):
        age_h = -1
    cmd = (read_text(f"{base}/cmdline") or "").replace("\0", " ").strip()[:220]
    try:
        cwd = os.readlink(f"{base}/cwd")
    except OSError:
        cwd = "?"
    cgroup = (read_text(f"{base}/cgroup") or "").strip().split("::")[-1][:120]
    rows.append((int(entry), ppid, user, age_h,
        fields.get("VmRSS", 0) / 1024, fields.get("RssAnon", 0) / 1024,
        fields.get("RssFile", 0) / 1024, fields.get("RssShmem", 0) / 1024,
        rollup.get("Pss", -1024) / 1024, fields.get("VmSwap", 0) / 1024,
        cgroup, cwd, cmd))
rows.sort(key=lambda row: row[4], reverse=True)
sys.stdout.write("pid\tppid\tuser\tage_h\trss_mb\tanon_mb\tfile_mb\tshmem_mb\tpss_mb\tswap_mb\tcgroup\tcwd\tcmd\n")
for row in rows:
    sys.stdout.write("\t".join(f"{v:.1f}" if isinstance(v, float) else str(v) for v in row) + "\n")
```
atop timeline, `atop_timeline.sh YYYYMMDD…`:
```bash
for day in "$@"; do
  atop -r "/var/log/atop/atop_${day}" -m 2>/dev/null | awk -v day="$day" '
    /^ATOP/ { t=$5; keep = (substr(t,4,2)=="00" || substr(t,4,2)=="01" || substr(t,4,2)=="02") ; next }
    /^MEM/ && /avail/ { for(i=1;i<=NF;i++){ if($i=="avail") av=$(i+1); if($i=="cache") ca=$(i+1); if($i=="slab") sl=$(i+1) } next }
    /^MEM/ && /shmem/ { for(i=1;i<=NF;i++){ if($i=="shmem") sh=$(i+1); if($i=="zfarc") za=$(i+1) } next }
    /^PAG/ { for(i=1;i<=NF;i++) if($i=="oomkill") ok=$(i+1);
             if (keep || ok+0>0) printf "%s %s avail=%-7s shmem=%-7s cache=%-7s zfarc=%-7s slab=%-7s oomkill=%s\n", day, t, av, sh, ca, za, sl, ok }'
done
```
(The first sample of each day carries the since-boot oomkill total, e.g. 428; per-interval counts are the rest.) Surreal trend: `atop -r /var/log/atop/atop_<day> -b HH:00 -e HH:09 -P PRM | awk '$1=="PRM" && $8=="(surreal)" && !seen[$5 $7]++ {print $5,$7,$12/1048576}'`. Field $12 is RSS in KiB; the y/n process flag column shifts, so dedupe on (time, pid). cgroup readings: `memory.current`, `memory.stat` (anon/file/shmem), `memory.peak`, and `memory.events` oom_kill under `/sys/fs/cgroup/user.slice/user-1000.slice/user@1000.service/`.
