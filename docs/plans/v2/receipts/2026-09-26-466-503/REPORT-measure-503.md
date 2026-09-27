# REPORT-measure-503 — test_migration_wire server-start budget under concurrent load (#503)

brief-base v16 read · brief project v7 read

## SUMMARY BLOCK
- **State:** done-with-deviations. Measured 2026-09-26 16:49–17:30 (host time) on this 64-core box, against code at `4ddb913`.
- **Deviations:** (1) I added a launch gate to the leg runner, because ambient MemAvailable sat at 10–16.6 GB against the briefed 15 GB kill floor. The floor itself was kept. (2) The plugin gained env-gated probes mid-run (async-stack sampler, round-trip and store-CPU accounting). Rounds r1–r3 ran without them, r4–r6 with them. Timing code was identical in both. (3) I discarded a cProfile attempt: on 3.14 it profiles every thread (§Breakdown). (4) Four sessions were cut short by the watchdog. Their partial starts are kept (§Legs). (5) The raw data stays in my scratchpad, because my writable set is this file only (§Receipts).
- **Packages considered:** `numpy.percentile(method="inverted_cdf")` gives nearest-rank percentiles (used). cProfile was **rejected**: I read its output and it attributes the main thread's 20 ms poll to `join`. pyinstrument's async mode is the replace candidate for the sampler, verdict `keep_with_trigger` (trigger: this instrument gets committed). It is not installed, and adding it would edit `pyproject.toml`, which is outside my writable set.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none. I wrote no repo code; the instruments are scratch-only and pasted below.
- **Graded:** 4ddb913 · HEAD-at-report: 19f8f80 · DIFFERENT (HEAD is 1 commit ahead: a docs-only lead report). `git diff --stat 4ddb913 19f8f80` is EMPTY over loopback.py, test_migration_wire.py, server.py, store/, conftest.py, _surreal_harness.py, gates.yaml and pending_contract_gate.py.
- **HEADLINE:** n=551 heavy starts across L1/L2/L5 ×6 reps: **p50 5.9 s, p99 9.85 s, max 10.04 s**. A start is 99.4 % `build_app_context`, and 97 % of that is **waiting on SurrealDB replies from the shared test store** (80 round-trips per start; one DDL request alone takes p50 2.3 s, max 4.3 s). Start time does NOT track my own concurrency (r = −0.09) or load average (r = +0.08, over the 8.6–21 load range I could reach). It tracks the **other fleet sessions' xdist workers** (r = +0.74, +0.12 s per worker). Light `serve_asgi` callers: p50 0.02 s, max 0.50 s.
- **Recommendation (§Recommendation):** (a) set a per-caller `startup_timeout_s=60` in `_serve_migration_wire`, which is the narrow fix. Keep the default at 15 s, since light callers are about 30× under it. Separately, raise the currency gate's `-n auto` (see below).
- **Decisions needed:** (1) the operator rules on the a / b / c / d budget options. (2) The operator rules on whether `scripts/gates.yaml`'s `-n auto` pytest gate should respect the fleet cap in MEMORY.md (§Side answer).
- **Receipts:** §Legs (table) · §Envelope · §Breakdown · §Light callers · §Instrument (verbatim) · §Fires-control.

## Side answer — does `pending_contract_gate.py --currency` spawn its suite at `-n auto`?
**YES. HIGH confidence: I read the code at `4ddb913`.**
- `--currency` with no `--legs` runs every gate in the manifest. `scripts/pending_contract_gate.py::main` sets `legs = arguments.legs if arguments.legs is not None else manifest.ids`, then calls `_run_selected_gates`, which executes each manifest `command` verbatim (plus any forwarded `pytest_args`).
- The manifest entry `id: pytest` in `scripts/gates.yaml` is `["uv", "run", "pytest", "-q", "-n", "auto", "-o", "junit_family=xunit1", "--junit-xml={junit_xml}"]`. Its description reads "run with -n auto per CLAUDE.md's measured 9.6x".
- So every currency close-out runs a full suite at **64 workers**, which is outside the envelope measured below (≤36 other workers). It also ignores MEMORY.md's rule of "-n 12 when another lore suite is live". Surfaced for the operator; I have not changed anything.

## Capability check (brief-base §4)
- **Demanded:** a 15 GB MemAvailable watchdog with a process-tree kill by PID.
- **Have:** yes (`run_leg.sh` below; it walks `/proc/*/status` PPid; no `pkill -f`).
- **Conflict found 2026-09-26 16:43:**
  - Ambient MemAvailable was **10.1–16.6 GB before I launched anything**. SwapFree was **84 kB of 16 GB**. RSS by command: postgres 55.3 GB (non-lore), surreal 15.6 GB, python 12.8 GB (the lore test fleet). ZFS ARC was 26.8 GB.
  - One copy of my leg peaks at **~230 MB RSS** (measured), so five copies are about 1.2 GB.
  - The floor killed both validation copies before any start was recorded.
- **Resolution, within the brief:**
  - I kept the 15 GB kill floor.
  - I added a launch gate: a leg starts only when MemAvailable ≥ 15 GB + N×0.3 GB + 1 GB.
  - I raised the fork on lore_comms (`q:503-memfloor`, #17077). Ambient recovered by about 17:00, so I withdrew it (#17078). No ruling was needed.
- **Named bound:** samples are censored toward moments with ≥16 GB free memory. Five watchdog kills happened in total (listed below).

## Legs — per-leg start-time table (measured 2026-09-26 16:49–17:26, code at `4ddb913`)
- **What was run:** each copy is `.venv/bin/python -m pytest -p no:xdist -p no:cacheprovider -p measure503_plugin -q loremaster/tests/test_migration_wire.py`. Six reps per leg, interleaved as L1, L2, L5, L1, … so that ambient drift is spread across the legs.
- **Budget:** overridden to 120 s, so no start was cut off. Every start completed (`non-started` over the heavy legs is empty).
- **What is timed:** the wall time from `_UvicornServerThread.start` entry to "uvicorn reported started". This is exactly the wait `DEFAULT_STARTUP_TIMEOUT_S` bounds.
- **Percentiles** are nearest-rank.
- **Column meanings:**
  - "othSess" = other lore pytest sessions live at the start (mine excluded).
  - "othFull" = how many of those were full-suite runs.
  - "othWrk" = their xdist workers.
  - "build%" = the minimum share of the start spent inside `build_app_context`.

```
leg     n     p50     p90     p99     max    min    load1 range  othSess  othFull  othWrk  build%
L1     61    6.98    8.84    9.34    9.34   4.87    8.8-  21.1   2-5     1-3     8-36   99.3%
L2    130    6.00    9.06    9.76    9.97   5.16    8.6-  17.8   2-6     1-3     9-36   99.4%
L5    360    5.83    8.98    9.88   10.04   5.02    9.2-  16.3   1-5     1-3     8-36   99.4%
ALL   551  p50=5.88  p90=8.98  p99=9.85  max=10.04
```
- **Reading:** L5 is not slower than L1. My own concurrency, one to five sessions without xdist, has no measurable effect.
- **What does each start track?** Pearson r and OLS slope over n=551 (`regress.py`):
```
my_concurrency(N)            r=-0.09  slope=-0.081s/unit  intercept=6.86  range=1-5
loadavg1                     r=+0.08  slope=+0.060s/unit  intercept=5.85  range=8.6-21.13
other_sessions               r=+0.74  slope=+0.862s/unit  intercept=3.79  range=1-6
other_full_suite_sessions    r=+0.69  slope=+1.210s/unit  intercept=4.50  range=1-3
other_workers                r=+0.74  slope=+0.121s/unit  intercept=3.76  range=8-36
other_workers+my_copies      r=+0.75  slope=+0.124s/unit  intercept=3.22  range=9-41
store_cores (during start)   r=+0.38  slope=+0.344s/core  intercept=5.33  range=0.20-3.88  n=270
```
- ⚠ **These correlations are observational.** Fleet load drifted over the 40 minutes, and I did not control it. The covariate that matters is the rest of the fleet, which I cannot set. I could only add at most 5 sessions without xdist (brief cap).
- **Watchdog-censored sessions:** 4 sessions were cut short. They are kept as partial samples: L1-r1-c1 5/12, L1-r5-c1 8/12, L2-r4-c1 5/12, L2-r4-c2 5/12. There were also 2 pre-run validation kills that recorded nothing. Full log: `logs/watchdog.log`, 5 lines.

## Envelope — start time by ambient fleet load (`envelope.py`)
```
 other_workers    n    p50    p99    max       load1  N_mine
     0-15       199   5.54   6.53   6.54   9.5- 13.6 [1, 2, 5]
    16-23        58   5.93   6.83   6.83  10.2- 13.5 [1, 2, 5]
    24-29       159   6.02   9.28   9.33   9.5- 21.1 [1, 2, 5]
    30-36       135   8.56   9.97  10.04   8.6- 17.8 [1, 2, 5]
```
- **The measured envelope:** at most 36 other lore xdist workers, plus at most 5 of my sessions, with load1 ≤ 21 on 64 cores (the CPU was never oversubscribed).
- **The #503 failure was outside it on LOAD, not on worker count.** The lead's episode had 3×8 + 6 = **30** workers, which is inside my worker range. But it also had typecheck.sh running and **load 77 > 64 cores**. The largest start I saw at 30–36 workers was 10.04 s; the lead saw >15 s.
- **So the failure regime is CPU oversubscription on top of store load.** I could not reproduce it inside the brief's caps (≤5 copies, no full suite).

## Breakdown of one start — where the seconds go
**Phase timestamps** (plugin, every start). This example is a representative record, `L5-r6-c3`, the `test_a_legit_proxied_host_is_accepted` setup. Seconds are measured from start() entry:
```
run_begin 0.0002 · ls_begin (uvicorn lifespan startup) 0.0007 · bac_begin (build_app_context) 0.0010 ·
gate_begin/end (run_probe_gate, FakeEmbedder) 0.0010→0.0011 · bac_end 5.6957 · ls_end 5.6966 · started 5.7042
rtt: n=80 requests, sum 5.562 s, largest single request 2.336 s; by process: signing in 13 / 0.416 s, use 13 / 0.214 s, query 54 / 4.932 s
store_cores (spike-surreal CPU during the start) 1.527
```
- **Where the time goes:** uvicorn boot and the lifespan plumbing take under 1 ms, and the probe gate takes about 0.1 ms. **99.3–99.4 % of every start is `loremaster.server.build_app_context`** (the minimum across all 551 starts).
- **Inside the build**, from the async-stack sampler: 12 starts, 7803 samples at 10 ms (`attribute.py` over `samples.jsonl`). **97.6 % of samples were parked on `surrealdb/connections/async_ws.py:_send`**, awaiting a reply from the shared test store `ws://127.0.0.1:18000`.
- **Share by `build_app_context` step:**
```
 44.9%  server.py:build_app_context → store/surreal.py  SurrealStore.ensure_ready
 13.3%  → graph_surreal.py ensure_ready      12.8% → messages.py ensure_ready
 10.3%  → agents.py ensure_ready              5.7% → briefs.py ensure_ready
 ≤1.4% each: watcher.run_sweep, tasks, surreal_manifest, findings, keeps, memory/local, principals, snapshots, diff
```
- **Round-trip accounting** (`MEASURE503_RTT`, 282 starts):
  - Every start makes exactly **80 requests**: 13 connections × (sign-in + `use`), plus **54 queries**.
  - Σ request latency / wall has a p50 of **0.971**. The start is the store's latency, serialized.
  - **The largest single request has a p50 of 2.32 s and a max of 4.31 s**, which is a p50 of 42 % of the whole start.
  - That request is in the `SurrealStore.ensure_ready` schema DDL. **MEDIUM confidence:** it is inferred from the two instruments agreeing (45 % of samples ≈ 2.6 s of a ~5.8 s start ≈ the largest request), not from logging the query text.
- **Store CPU during starts:** p50 1.54, max 3.88 cores. The store is not CPU-saturated at these loads, and store CPU correlates only weakly with start time (r = +0.38).
- **Dominant phase, named:** the per-start **fresh-database schema DDL against the shared SurrealDB test store**, above all SurrealStore.ensure_ready. Its latency grows with the number of concurrent fleet workers hitting the same store. That matches every test's `unique_database()` + DDL.
- **`TestTheHeavyBuildRunsOncePerProcess`** is about the *app* process: one build per server. Each test in this file starts a NEW server on a NEW database, so every one of the 12 starts in a session pays the full build.
- **The discarded cProfile instrument, for the record.** Python 3.14's cProfile recorded ALL threads. Its top self-time, 7.0 s in `_thread._ThreadHandle.join` over 398 calls, is the MAIN thread's `_await_started` poll (`join(timeout=0.02)` ×398 ≈ the start wait itself), not a cause. The sampler replaced it.

## Light callers — are the other `serve_asgi` / `serve_http` callers near 15 s?
**No. They are about 30× under 15 s.**
- **Who calls these helpers:** an awk scan of tracked `*.py` (a grep fallback for an importer set). lore_impact returned covering tests but no consumer modules for these test-only helpers.
  - `serve_asgi` is called from `loremaster/tests/test_migration_wire.py` (the heavy one), `loremaster/tests/test_loopback_serving.py` (light apps), and `scripts/fastmcp_migration_spike.py` (a script that passes its own `_STARTUP_TIMEOUT_S`).
  - `serve_http` is called from `skills/lore-deploy/tests/{test_loopback_home,test_port_probe,test_workspace_probe}.py`. **`serve_http` has no startup wait and no startup budget** (it activates synchronously), so the question does not apply to it.
- **Measured:** `test_loopback_serving.py` ×3 runs, with the plugin at `MEASURE503_BUDGET_S=0` so each caller's own budget is honoured. All 46 tests passed each time. There were 93 starts:
  - **69 started: p50 0.020 s, p99 = max 0.502 s.**
  - The other 24 are the file's deliberate failure cases: ServerThreadCrashed ×9, injected interrupts ×12, ServerStartupTimeout ×3 on a 1 s budget.
  - Caller budgets seen: 15.0 (default) ×66, **60.0 ×21**, 10.0 ×3, 1.0 ×3.
  - Ambient during these runs: load 10–12, 6–14 other workers.
- **Conclusion:** the default of 15 s is used heavily only by light callers, and they sit about 30× under it. **A per-caller budget is the narrow fix.**

## Recommendation — budget options, each derived from the numbers above
**Facts every option rests on:**
- The in-envelope maximum is **M = 10.04 s** (n=551).
- The current default of 15 s = **1.49 × M**. It had about 1.5× headroom over a benign fleet, and it broke in the lead's out-of-envelope episode.
- The true start time in that regime is **censored at >15 s and unknown**.
- A large budget costs little. `_UvicornServerThread._await_started` checks `self._thread.is_alive()` before the deadline on every ≤20 ms poll, so **a crash is named within one poll whatever the budget**. The budget only bounds how long a genuine HANG (thread alive, never started) takes to be named.

**(a) Per-caller heavy budget: `_serve_migration_wire` passes `startup_timeout_s=60`. [RECOMMENDED]**
- **Derivation:** 60 s = **6 × M**, and **4 × the censoring bound** (15 s) of the only observed failing regime. In-tree precedent: `test_loopback_serving.py` already passes 60.0 on 21 of its starts.
- **Certifies:** the measured envelope (≤36 other workers + ≤5 sessions, load1 ≤ 21) with a 6× margin. Beyond that, it certifies starts up to 60 s.
- ⚠ **Not measured:** whether the oversubscribed regime (load > 64, the #503 episode) stays under 60 s. The brief's caps forbid reproducing it.
- **Re-open trigger:** the first `ServerStartupTimeout` at 60 s, or the first recorded heavy start ≥ 30 s (half the budget).
- **Cost:** a real hang in this fixture is named after 60 s instead of 15 s. Light callers are untouched.

**(b) Raise `DEFAULT_STARTUP_TIMEOUT_S` to 60.**
- **Certifies** the same for the heavy caller.
- **For light callers** (max 0.50 s) it only delays naming a hang from 15 s to 60 s.
- **Not recommended.** It is broader than the evidence requires. The default would then no longer be derived from the callers that use it (light, about 30× headroom already).

**(c) A fleet cap at which the current 15 s holds with margin.**
- **Margin by fleet size, from the §Envelope table:**
  - Other lore xdist workers ≤ **23**: max 6.83 s, so 15 s has **2.2×** margin.
  - ≤ **36**: max 10.04 s, so **1.49×** margin.
- **Load must be capped as well:** load1 ≤ 21 is the only CPU state measured.
- ⚠ **Worker count alone does NOT certify it.** The failing episode had 30 workers but load 77.
- ⚠ **The cap is unenforceable as things stand.** Nothing counts sessions. `scripts/gates.yaml`'s own pytest gate runs `-n auto` (**64 workers**), which alone exceeds the certified envelope, so every currency close-out would break the cap.
- **Certifies:** ≤23 workers at load ≤ 21 with 2×, if someone enforces it.

**(d) Both (a) and (c).**
- (a) fixes the test.
- (c) is fleet hygiene that also helps every other store-bound test. It needs an instrument to be more than a hope (a "diagnosis is not an instrument" item).

**Structural option, surfaced for the operator, not a budget:**
- Each session pays 12 full builds (12 × 80 store round-trips, 12 × a ~2.3 s DDL), about 70 s of an 81–129 s session wall.
- A server scoped to the class or module would cut the exposure count, not the per-start tail.
- Per-test database isolation may be deliberate. **Operator's call.**

## Fires-control (the instrument demonstrably fires)
- **Expected starts per complete session:** 12, which is 10 `migration_wire` fixture setups + 2 `TestTheAllowedHostsWildcardAndDefault` bodies. The 2 remaining tests of the 14 (`test_build_asgi_app_passes_stateless_http_false_explicitly`, `TestTraceEmitGuardsANoneRequestContext`) start no server.
- **Observed:** every one of the **44 complete heavy sessions recorded exactly 12**, and the 4 prof sessions also recorded 12 each. The only short sessions are the 4 watchdog-killed ones listed above. Validation run 1 recorded 9 starts before its kill (`starts-validation.jsonl`).
- **Instrument health:** zero sessions ran without records.
- **Provenance:** every session line records `loremaster_file = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`. That is the real tree, whose measured files are byte-identical to `4ddb913`.
- **No repo edit was made.** The budget override is applied by wrapping `_UvicornServerThread.start` at runtime, so no scratch copy was needed.

## Receipts (data location — needs archiving by the lead)
- **Scratch dir (not durable):** `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3dc70960-5c40-45ae-b446-e5a1605ac922/scratchpad/m503/`.
- **Contents:**
  - `starts.jsonl`: 692 start records + 55 session records.
  - `samples.jsonl`: the async-stack samples.
  - `starts-validation.jsonl`.
  - `logs/`: per-copy pytest tails, `drive.out`, `watchdog.log`.
  - `final-*.txt`: the tables above.
- **Suggested archive:** `docs/plans/v2/receipts/2026-09-26-measure-503/`. My writable set was this report only.

## Instrument (verbatim — all scratch; nothing committed)

### `measure503_plugin.py`
```python
"""measure-503 timing shim — a pytest plugin loaded with ``-p measure503_plugin`` (PYTHONPATH).

Wraps ``loremaster.testing.loopback._UvicornServerThread.start`` (the start wait inside
``serve_asgi``) WITHOUT editing the repo:
  * overrides the startup budget to max(caller budget, MEASURE503_BUDGET_S) so no start is cut
    off (we measure the tail, not the pass rate);
  * records per start: wall seconds from start() entry to started, phase timestamps, the caller's
    original budget, the test nodeid, the 1-min loadavg, MemAvailable, and a fleet sample.

Phases (all relative to start() entry, seconds):
  run_begin      uvicorn thread body entered
  ls_begin/end   uvicorn LifespanOn.startup (the ASGI lifespan startup, incl. the heavy build)
  bac_begin/end  loremaster.server.build_app_context (the heavy build)
  gate_begin/end loremaster.server.run_probe_gate (first heavy primitive)
  started        start() returned (uvicorn reported started)

Fleet sample (#228-safe: NO pattern match over args text): a process is a "lore python" iff its
/proc/<pid>/exe basename starts with "python" AND its /proc/<pid>/maps maps a file under a lore
tree's ``.venv`` (path contains "PycharmProjects/lore" or "PycharmProjects-lore" AND "/.venv/").
A SESSION is a lore python whose parent is not a lore python. Processes carrying
MEASURE503_TAG in their environ are mine (the concurrent legs) and counted separately; this
process's own session is excluded from both.

Env: MEASURE503_OUT (JSONL path, required), MEASURE503_TAG (leg label), MEASURE503_BUDGET_S
(default 120), MEASURE503_PROFILE (a path: cProfile the FIRST start's server thread into it).
"""

from __future__ import annotations

import cProfile
import json
import os
import threading
import time
from pathlib import Path

_OUT = os.environ.get("MEASURE503_OUT")
_TAG = os.environ.get("MEASURE503_TAG", "untagged")
_BUDGET_S = float(os.environ.get("MEASURE503_BUDGET_S", "120"))
_PROFILE_PATH = os.environ.get("MEASURE503_PROFILE")
_LORE_MARKERS = ("PycharmProjects/lore", "PycharmProjects-lore")

_by_thread: dict[int, dict] = {}  # server-thread ident -> record
_current: dict | None = None  # the record of the start in flight (starts are sequential per process)
_profiled = False


_STORE_PID = os.environ.get("MEASURE503_STORE_PID")  # spike-surreal (:18000) host PID — READ-ONLY /proc
_CLK_TCK = os.sysconf("SC_CLK_TCK")


def _store_cpu_s() -> float | None:
    """Cumulative user+system CPU seconds of the test store process (None if unset/unreadable)."""
    if not _STORE_PID:
        return None
    try:
        fields = Path(f"/proc/{_STORE_PID}/stat").read_text().rsplit(")", 1)[1].split()
        return (int(fields[11]) + int(fields[12])) / _CLK_TCK
    except OSError:
        return None


def _loadavg() -> list[float]:
    return [float(x) for x in Path("/proc/loadavg").read_text().split()[:3]]


def _mem_available_kb() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemAvailable:"):
            return int(line.split()[1])
    return -1


def _is_lore_python(pid: int) -> bool:
    try:
        if not os.path.basename(os.readlink(f"/proc/{pid}/exe")).startswith("python"):
            return False
        with open(f"/proc/{pid}/maps", encoding="utf-8", errors="replace") as maps:
            for line in maps:
                if "/.venv/" in line and any(marker in line for marker in _LORE_MARKERS):
                    return True
    except OSError:
        return False
    return False


def _ppid(pid: int) -> int:
    try:
        for line in Path(f"/proc/{pid}/status").read_text().splitlines():
            if line.startswith("PPid:"):
                return int(line.split()[1])
    except OSError:
        pass
    return -1


def _is_mine(pid: int) -> bool:
    try:
        return b"MEASURE503_TAG=" in Path(f"/proc/{pid}/environ").read_bytes()
    except OSError:
        return False


def _fleet_sample() -> dict:
    my_pid = os.getpid()
    lore_pids = {int(p) for p in os.listdir("/proc") if p.isdigit() and _is_lore_python(int(p))}
    lore_pids.discard(my_pid)
    parents = {pid: _ppid(pid) for pid in lore_pids}
    sessions = [pid for pid, parent in parents.items() if parent not in lore_pids and parent != my_pid]
    mine = {pid for pid in lore_pids if _is_mine(pid)}
    other_sessions = [pid for pid in sessions if pid not in mine]
    # worker count per other session (children that are lore pythons)
    other_workers = sum(1 for pid, parent in parents.items() if parent in other_sessions)
    # CLASSIFICATION ONLY (detection above never reads args): a session whose argv names no
    # ``*.py`` / ``::`` target is running a full (testpaths) suite.
    full_suite_sessions = 0
    for pid in other_sessions:
        try:
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
        except OSError:
            continue
        if not any(arg.endswith(b".py") or b"::" in arg for arg in argv[1:] if not arg.startswith(b"-")):
            full_suite_sessions += 1
    return {
        "other_sessions": len(other_sessions),
        "other_session_pids": sorted(other_sessions),
        "other_workers": other_workers,
        "other_full_suite_sessions": full_suite_sessions,
        "my_other_copies": len([pid for pid in sessions if pid in mine]),
    }


_SAMPLE_PATH = os.environ.get("MEASURE503_SAMPLE")  # JSONL: async-stack samples of the build task
_SAMPLE_INTERVAL_S = 0.01


def _coro_chain(coro) -> list[str]:
    """The await chain of a coroutine, outermost first, as ``file:function:line`` strings."""
    chain = []
    while coro is not None:
        frame = getattr(coro, "cr_frame", None) or getattr(coro, "gi_frame", None) or getattr(coro, "ag_frame", None)
        if frame is None:
            chain.append(f"<{type(coro).__name__}>")
        else:
            chain.append(f"{frame.f_code.co_filename.split('site-packages/')[-1].split('PycharmProjects/lore/')[-1]}"
                         f":{frame.f_code.co_name}:{frame.f_lineno}")
        awaited = getattr(coro, "cr_await", None) or getattr(coro, "gi_yieldfrom", None) or getattr(coro, "ag_await", None)
        has_frame_attrs = any(hasattr(awaited, a) for a in ("cr_frame", "gi_frame", "ag_frame"))
        if awaited is not None and not has_frame_attrs and frame is not None \
                and frame.f_code.co_name in ("__aenter__", "__aexit__"):
            # an ``anext()`` awaitable (async_generator_asend) exposes no frame: step into the
            # @asynccontextmanager's own async generator instead.
            awaited = getattr(frame.f_locals.get("self"), "gen", None)
        coro = awaited
    return chain


def _sample_task_stack(task, stop: threading.Event, record: dict | None) -> None:
    """Sample the build task's await chain every _SAMPLE_INTERVAL_S from a side thread (read-only)."""
    samples = []
    t0 = time.monotonic()
    while not stop.wait(_SAMPLE_INTERVAL_S):
        try:
            samples.append((round(time.monotonic() - t0, 3), _coro_chain(task.get_coro())))
        except Exception as error:  # noqa: BLE001 — a racy read is a dropped sample, never a crash
            samples.append((round(time.monotonic() - t0, 3), [f"<sample error {type(error).__name__}>"]))
    with open(_SAMPLE_PATH, "a", encoding="utf-8") as out:
        out.write(json.dumps({"test": (record or {}).get("test"), "interval_s": _SAMPLE_INTERVAL_S,
                              "samples": samples}) + "\n")


def _phase(record: dict | None, name: str) -> None:
    if record is not None and name not in record["phases"]:
        record["phases"][name] = round(time.monotonic() - record["_t0"], 4)


def pytest_configure(config) -> None:  # noqa: ARG001 — pytest hook signature
    global _current
    if not _OUT:
        raise RuntimeError("MEASURE503_OUT must be set")
    import loremaster
    import loremaster.server as server_module
    from loremaster.testing import loopback
    from uvicorn.lifespan.on import LifespanOn

    Path(_OUT).parent.mkdir(parents=True, exist_ok=True)
    with open(_OUT, "a", encoding="utf-8") as out:
        out.write(json.dumps({"kind": "session", "tag": _TAG, "pid": os.getpid(),
                              "loremaster_file": loremaster.__file__,
                              "loopback_file": loopback.__file__}) + "\n")

    original_start = loopback._UvicornServerThread.start
    original_run = loopback._UvicornServerThread._run
    original_ls_startup = LifespanOn.startup
    original_bac = server_module.build_app_context
    original_gate = server_module.run_probe_gate

    def timed_start(self, startup_timeout_s: float) -> None:
        global _current
        fleet = _fleet_sample()
        record = {
            "kind": "start", "tag": _TAG, "pid": os.getpid(),
            "test": os.environ.get("PYTEST_CURRENT_TEST", "?"),
            "caller_budget_s": startup_timeout_s, "applied_budget_s": max(startup_timeout_s, _BUDGET_S),
            "loadavg": _loadavg(), "mem_available_kb": _mem_available_kb(), **fleet,
            "phases": {}, "wall_s": None, "outcome": None,
            "_store_cpu0": _store_cpu_s(),
            "_t0": time.monotonic(),
        }
        _current = record
        try:
            original_start(self, max(startup_timeout_s, _BUDGET_S))
            record["outcome"] = "started"
        except BaseException as error:
            record["outcome"] = f"{type(error).__name__}: {str(error)[:200]}"
            raise
        finally:
            record["wall_s"] = round(time.monotonic() - record["_t0"], 4)
            store_cpu0, store_cpu1 = record.pop("_store_cpu0"), _store_cpu_s()
            record["store_cores"] = (
                round((store_cpu1 - store_cpu0) / record["wall_s"], 3)
                if store_cpu0 is not None and store_cpu1 is not None else None
            )
            record["loadavg_end"] = _loadavg()
            _phase(record, "started")
            record.pop("_t0")
            _current = None
            with open(_OUT, "a", encoding="utf-8") as out:
                out.write(json.dumps(record) + "\n")

    def timed_run(self) -> None:
        global _profiled
        record = _current
        if record is not None:
            _by_thread[threading.get_ident()] = record
        _phase(record, "run_begin")
        if _PROFILE_PATH and not _profiled:
            _profiled = True
            profiler = cProfile.Profile()
            profiler.enable()
            try:
                original_run(self)
            finally:
                profiler.disable()
                profiler.dump_stats(_PROFILE_PATH)
        else:
            original_run(self)

    async def timed_ls_startup(self) -> None:
        record = _by_thread.get(threading.get_ident())
        _phase(record, "ls_begin")
        try:
            await original_ls_startup(self)
        finally:
            _phase(record, "ls_end")

    async def timed_bac(*args, **kwargs):
        record = _by_thread.get(threading.get_ident())
        _phase(record, "bac_begin")
        sampler_stop = threading.Event()
        sampler = None
        if _SAMPLE_PATH:
            import asyncio
            build_task = asyncio.current_task()
            sampler = threading.Thread(
                target=_sample_task_stack, args=(build_task, sampler_stop, record), daemon=True
            )
            sampler.start()
        try:
            return await original_bac(*args, **kwargs)
        finally:
            _phase(record, "bac_end")
            if sampler is not None:
                sampler_stop.set()
                sampler.join()

    async def timed_gate(*args, **kwargs):
        record = _by_thread.get(threading.get_ident())
        _phase(record, "gate_begin")
        try:
            return await original_gate(*args, **kwargs)
        finally:
            _phase(record, "gate_end")

    if os.environ.get("MEASURE503_RTT"):
        # Round-trip accounting (separate runs only): every SurrealDB ws request the SERVER thread
        # makes between bac_begin and bac_end — count, summed and max per-request latency.
        import surrealdb.connections.async_ws as async_ws_module

        original_send = async_ws_module.AsyncWsSurrealConnection._send

        async def timed_send(self, message, process, bypass=False):
            record = _by_thread.get(threading.get_ident())
            in_build = record is not None and "bac_begin" in record["phases"] and "bac_end" not in record["phases"]
            sent_at = time.monotonic()
            try:
                return await original_send(self, message, process, bypass)
            finally:
                if in_build:
                    latency = time.monotonic() - sent_at
                    rtt = record.setdefault("rtt", {"n": 0, "sum_s": 0.0, "max_s": 0.0, "by_process": {}})
                    rtt["n"] += 1
                    rtt["sum_s"] = round(rtt["sum_s"] + latency, 4)
                    rtt["max_s"] = round(max(rtt["max_s"], latency), 4)
                    per = rtt["by_process"].setdefault(str(process), [0, 0.0])
                    per[0] += 1
                    per[1] = round(per[1] + latency, 4)

        async_ws_module.AsyncWsSurrealConnection._send = timed_send

    loopback._UvicornServerThread.start = timed_start
    loopback._UvicornServerThread._run = timed_run
    LifespanOn.startup = timed_ls_startup
    server_module.build_app_context = timed_bac
    server_module.run_probe_gate = timed_gate
```

### `run_leg.sh`
```bash
#!/usr/bin/env bash
# measure-503 leg runner: run N concurrent copies of test_migration_wire.py (-p no:xdist), each
# with the timing plugin, under a MemAvailable watchdog that kills ONLY this leg's process trees,
# BY PID (never pkill -f — #228). Usage: run_leg.sh <N> <rep-label>
set -u
N="$1"; REP="$2"
REPO=/home/ejprice/PycharmProjects/lore
M=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3dc70960-5c40-45ae-b446-e5a1605ac922/scratchpad/m503
WATCHDOG_KB=$((15 * 1024 * 1024))
mkdir -p "$M/logs"
# LAUNCH GATE: start only with headroom for this leg (N x 0.3 GB) + 1 GB above the kill floor,
# so the watchdog trips on genuine pressure, not on the leg's own planned footprint.
need_kb=$((WATCHDOG_KB + N * 300 * 1024 + 1024 * 1024))
waited=0
until [ "$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)" -ge "$need_kb" ]; do
  sleep 5; waited=$((waited + 5))
  [ "$waited" -ge 1800 ] && { echo "GATE: gave up after ${waited}s waiting for ${need_kb} kB" | tee -a "$M/logs/watchdog.log"; exit 3; }
done
echo "gate waited ${waited}s"
pids=()
for i in $(seq 1 "$N"); do
  tag="L${N}-${REP}-c${i}"
  ( cd "$REPO" && exec env PYTHONPATH="$M" MEASURE503_OUT="$M/starts.jsonl" MEASURE503_TAG="$tag" \
      .venv/bin/python -m pytest -p no:xdist -p no:cacheprovider -p measure503_plugin -q \
      --tb=line -rfE ${MEASURE503_TARGET:-loremaster/tests/test_migration_wire.py} ) > "$M/logs/$tag.log" 2>&1 &
  pids+=("$!")
done
echo "leg L${N}-${REP} pids: ${pids[*]}"

descendants() {  # all descendant PIDs of $1, via /proc PPid (no pattern matching)
  local root="$1" p kids
  kids=$(awk -v r="$root" '/^PPid:/{if($2==r) print FILENAME}' /proc/[0-9]*/status 2>/dev/null | awk -F/ '{print $3}')
  for p in $kids; do echo "$p"; descendants "$p"; done
}

alive=1
while [ $alive -eq 1 ]; do
  alive=0
  for p in "${pids[@]}"; do kill -0 "$p" 2>/dev/null && alive=1; done
  avail=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  if [ "$alive" -eq 1 ] && [ "$avail" -lt "$WATCHDOG_KB" ]; then
    echo "WATCHDOG: MemAvailable ${avail} kB < ${WATCHDOG_KB} kB — killing leg trees ${pids[*]}" | tee -a "$M/logs/watchdog.log"
    for p in "${pids[@]}"; do
      for d in $(descendants "$p") "$p"; do kill -9 "$d" 2>/dev/null; done
    done
  fi
  sleep 2
done
for i in $(seq 1 "$N"); do
  tag="L${N}-${REP}-c${i}"
  echo "$tag: $(tail -n 1 "$M/logs/$tag.log")"
done
```

### `drive.sh`
```bash
#!/usr/bin/env bash
# Interleave legs so ambient drift is spread across all three: (L1, L2, L5) x reps.
M=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3dc70960-5c40-45ae-b446-e5a1605ac922/scratchpad/m503
for rep in r1 r2 r3; do
  for n in 1 2 5; do
    echo "=== $(date +%T) L$n $rep"; "$M/run_leg.sh" "$n" "$rep"
  done
done
echo "=== DONE $(date +%T)"
touch "$M/drive.done"
```

### `drive2.sh`
```bash
#!/usr/bin/env bash
# Extension rounds: same interleave, plus store-CPU and round-trip accounting on every start.
M=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/3dc70960-5c40-45ae-b446-e5a1605ac922/scratchpad/m503
export MEASURE503_STORE_PID=$(podman inspect spike-surreal --format '{{.State.Pid}}') MEASURE503_RTT=1
for rep in r4 r5 r6; do
  for n in 1 2 5; do
    echo "=== $(date +%T) L$n $rep"; "$M/run_leg.sh" "$n" "$rep"
  done
done
echo "=== DONE2 $(date +%T)"
```

### `summarize.py`
```python
"""measure-503 summarizer: per-leg start-time distribution from starts.jsonl (nearest-rank percentiles)."""
import json, sys, collections
import numpy as np
path = sys.argv[1]
rows = [json.loads(l) for l in open(path)]
sessions = [r for r in rows if r["kind"] == "session"]
starts = [r for r in rows if r["kind"] == "start"]
by_leg = collections.defaultdict(list)
for r in starts:
    if "-prof" in r["tag"] or "-light" in r["tag"]: continue
    by_leg[r["tag"].split("-")[0]].append(r)
per_tag = collections.Counter(r["tag"] for r in starts)
print("sessions:", len(sessions), "starts:", len(starts))
print("starts per tag:", dict(sorted(per_tag.items())))
print("loremaster files:", {s["loremaster_file"] for s in sessions})
def pct(values, q):
    return float(np.percentile(values, q, method="inverted_cdf"))  # nearest-rank
print(f"{'leg':4} {'n':>4} {'p50':>7} {'p90':>7} {'p99':>7} {'max':>7} {'min':>6} {'load1 range':>14} {'othSess':>8} {'othFull':>8} {'othWrk':>7} {'build%':>7}")
for leg in sorted(by_leg, key=lambda l: int(l[1:])):
    rs = [r for r in by_leg[leg] if r["outcome"] == "started"]
    w = [r["wall_s"] for r in rs]
    if not w: continue
    loads = [r["loadavg"][0] for r in rs]
    osess = [r["other_sessions"] for r in rs]; ofull = [r.get("other_full_suite_sessions", -1) for r in rs]
    owrk = [r["other_workers"] for r in rs]
    build = [(r["phases"]["bac_end"] - r["phases"]["bac_begin"]) / r["wall_s"] for r in rs if "bac_end" in r["phases"]]
    print(f"{leg:4} {len(w):4} {pct(w,50):7.2f} {pct(w,90):7.2f} {pct(w,99):7.2f} {max(w):7.2f} {min(w):6.2f} {min(loads):6.1f}-{max(loads):6.1f} {min(osess):>3}-{max(osess):<3} {min(ofull):>3}-{max(ofull):<3} {min(owrk):>3}-{max(owrk):<3} {100*min(build):5.1f}%")
bad = [r for r in starts if r["outcome"] != "started"]
print("non-started:", [(r["tag"], r["outcome"][:60]) for r in bad])
```

### `regress.py`
```python
"""measure-503: what does start time track? Pearson r + OLS slope of wall_s vs each ambient covariate."""
import json, sys
import numpy as np
rows = [json.loads(l) for l in open(sys.argv[1])]
s = [r for r in rows if r["kind"] == "start" and r["outcome"] == "started"
     and "-prof" not in r["tag"] and "-light" not in r["tag"]]
w = np.array([r["wall_s"] for r in s])
cov = {
    "my_concurrency(N)": [int(r["tag"].split("-")[0][1:]) for r in s],
    "loadavg1": [r["loadavg"][0] for r in s],
    "other_sessions": [r["other_sessions"] for r in s],
    "other_full_suite_sessions": [r.get("other_full_suite_sessions", 0) for r in s],
    "other_workers": [r["other_workers"] for r in s],
    "other_workers+my_copies": [r["other_workers"] + int(r["tag"].split("-")[0][1:]) for r in s],
}
if all(r.get("store_cores") is not None for r in s[-10:]):
    ss = [r for r in s if r.get("store_cores") is not None]
    print(f"store_cores subset n={len(ss)}")
print(f"n={len(s)}  wall mean={w.mean():.2f} sd={w.std():.2f}")
for name, x in cov.items():
    x = np.array(x, dtype=float)
    if x.std() == 0: print(f"{name:28} constant"); continue
    r = np.corrcoef(x, w)[0, 1]; slope, icpt = np.polyfit(x, w, 1)
    print(f"{name:28} r={r:+.2f}  slope={slope:+.3f}s/unit  intercept={icpt:.2f}  range={x.min():g}-{x.max():g}")
sc = [(r["store_cores"], r["wall_s"]) for r in s if r.get("store_cores") is not None]
if len(sc) > 3:
    x, y = np.array(sc).T; r = np.corrcoef(x, y)[0, 1]; slope, icpt = np.polyfit(x, y, 1)
    print(f"{'store_cores (during start)':28} r={r:+.2f}  slope={slope:+.3f}s/core  intercept={icpt:.2f}  range={x.min():.2f}-{x.max():.2f}  n={len(sc)}")
rt = [r for r in s if "rtt" in r]
if rt:
    q = np.array([r["rtt"]["by_process"]["query"][1] for r in rt]); mx = np.array([r["rtt"]["max_s"] for r in rt])
    print(f"rtt subset n={len(rt)}: query-sum p50={np.median(q):.2f}s  max-single-request p50={np.median(mx):.2f}s max={mx.max():.2f}s  n_requests={sorted({r['rtt']['n'] for r in rt})}")
```

### `envelope.py`
```python
"""measure-503: start-time envelope by ambient fleet workers (other lore xdist workers live at start)."""
import json, sys
import numpy as np
rows = [json.loads(l) for l in open(sys.argv[1])]
s = [r for r in rows if r["kind"] == "start" and r["outcome"] == "started"
     and "-prof" not in r["tag"] and "-light" not in r["tag"]]
bins = [(0, 15), (16, 23), (24, 29), (30, 36)]
print(f"{'other_workers':>14} {'n':>4} {'p50':>6} {'p99':>6} {'max':>6} {'load1':>11} {'N_mine':>7}")
for lo, hi in bins:
    b = [r for r in s if lo <= r["other_workers"] <= hi]
    if not b: continue
    w = np.array([r["wall_s"] for r in b]); L = [r["loadavg"][0] for r in b]
    mine = sorted({int(r["tag"].split("-")[0][1:]) for r in b})
    print(f"{lo:>6}-{hi:<7} {len(b):4} {np.percentile(w,50,method='inverted_cdf'):6.2f} {np.percentile(w,99,method='inverted_cdf'):6.2f} {w.max():6.2f} {min(L):5.1f}-{max(L):5.1f} {mine}")
w = np.array([r["wall_s"] for r in s])
print(f"ALL n={len(s)} p50={np.percentile(w,50,method='inverted_cdf'):.2f} p90={np.percentile(w,90,method='inverted_cdf'):.2f} p99={np.percentile(w,99,method='inverted_cdf'):.2f} max={w.max():.2f}")
tags = sorted({r['tag'] for r in s}); print("sessions:", len(tags))
killed = [t for t in tags if sum(1 for r in s if r['tag'] == t) != 12]
print("incomplete (watchdog-censored) sessions:", {t: sum(1 for r in s if r['tag'] == t) for t in killed})
```

### `attribute.py`
```python
"""Attribute build_app_context wall time to its steps from async-stack samples (measure-503)."""
import json, sys, collections
BUILD = "build_app_context"
step = collections.Counter(); leaf = collections.Counter(); runs = 0; total = 0
for line in open(sys.argv[1]):
    run = json.loads(line); runs += 1; interval = run["interval_s"]
    for _t, chain in run["samples"]:
        total += 1
        names = [c for c in chain]
        idx = next((i for i, c in enumerate(names) if f":{BUILD}:" in c), None)
        if idx is None:
            step["<outside build_app_context>"] += 1; continue
        below = names[idx + 1:]
        step[(names[idx], below[0].rsplit(":", 1)[0] if below else "<build frame itself>")] += 1
        leaf[names[-1].rsplit(":",1)[0] + " <- " + (names[-2].rsplit(":",1)[0] if len(names) > 1 else "")] += 1
print(f"runs={runs} samples={total} (~{total*interval/runs:.2f}s/run at {interval}s)")
print("-- by build_app_context line / awaited step (share of samples)")
for k, v in step.most_common(15): print(f"{100*v/total:5.1f}%  {k}")
print("-- by innermost frame")
for k, v in leaf.most_common(12): print(f"{100*v/total:5.1f}%  {k}")
```
