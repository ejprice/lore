brief-base v16 read (read mid-run, before this report — the spawn brief did not name it; see deviations)

# REPORT-impl-466-d1 — #466 delta d1, tdd-light Phase 4 (GREEN)

## SUMMARY BLOCK
- **state:** done-with-deviations
- **deviations:** (1) `serve_http` got bounded+loud teardown (ruling d) with NO new `shutdown_timeout_s` parameter — it uses `DEFAULT_SHUTDOWN_TIMEOUT_S`; no contract pin exists for it, so it is proven by a scratch probe + mutation (§D), not a test. (2) `_SHUTDOWN_JOIN_TIMEOUT_S` deleted (its only reader was replaced; it duplicated `DEFAULT_SHUTDOWN_TIMEOUT_S`=5.0). (3) The F12 timeout tail now carries real output: before `a124c5a`'s successor it was ALWAYS `""` on POSIX (§F12). (4) Incidental exposure: a `lore_search` DRY query returned a span of the contract report's Appendix B containing a reference driver diff — AFTER my F12 was written and green (§Exposure). (5) brief-base read late (brief didn't instruct it).
- **Packages considered:** F12 — stdlib `subprocess.Popen(start_new_session=True)` + `os.killpg` (read: installed 3.14.7 `subprocess.run` behaviour, probed `TimeoutExpired.stdout` type) → `replace` of `subprocess.run(timeout=)`; psutil `keep_with_trigger` (not installed; trigger: a descendant that `setsid`s). F2 — PEP 678 `BaseException.add_note` (stdlib). Ruling d — stdlib `HTTPServer.shutdown()` has no timeout (read: `socketserver.BaseServer.shutdown` = set flag + unbounded `Event.wait`) → `replace_with_adapter` (shutdown on a daemon thread, bounded join). C3 — no package; detector data.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 7 new symbols, all dispositioned (§DRY).
- **Graded:** none (builder report). Built on HEAD `a124c5a`.
- **decisions-needed:**
  - (c) pytest-asyncio `unused_tcp_port*`: the contract has NO pin for it (only a named bound in `TestTheServerCapableDependenciesAreDerived`'s docstring, bound 3). Per brief I added no test. Needs a contract pin (the author's proposed FunctionDef-argument leg) if ruled IN.
  - (d-follow-up) give `serve_http` a `shutdown_timeout_s` parameter + a contract pin? Today its overrun path is unpinned (probe-proven only).
  - `ConcurrentPairDriver.expected_passed()` still uses `subprocess.run(timeout=)` (contract report §Surfaced-5, same orphan class; `--collect-only` spawns no workers). Route it through the same tree-kill? Not done — not in the F12 grant.
- **receipts:** §VERIFY tails · §E teardown measurement · §D ruling-d probe + mutation · §M mutation proofs · §Instruments (verbatim).

---

## Files changed (writable set only; nothing staged)
| file | change |
|---|---|
| `loremaster/loremaster/testing/loopback.py` | F1: `_UvicornServerThread.start` wraps `thread.start()` + the new `_await_started` in `except BaseException: self._abandon(); raise` (the named failures' inline `_abandon()` calls removed — the one handler covers all). F2: `stop()` returns `bool` (finished in budget); new `_loud_teardown` context manager = THE one overrun policy (clean exit → `ServerShutdownTimeout`; body raising → same exception + `add_note`). `serve_asgi` exits through it. Ruling d: `serve_http` exits through the SAME `_loud_teardown` with new `_stop_http_server` (shutdown on a daemon thread, bounded join). `_SHUTDOWN_JOIN_TIMEOUT_S` deleted. |
| `loremaster/tests/test_no_raw_listener_in_test_trees.py` (detector section only, above the d1 classes) | `_LISTENER_METHODS` += anyio's `create_tcp_listener`, `create_unix_listener`. New `_LISTENER_NAMES_BY_LIBRARY = {"aiohttp": {run_app, TCPSite, UnixSite, TestServer, unused_port}}` + `_is_library_listener`, matched at ANY depth under the library (aiohttp re-exports: `aiohttp.web.TCPSite` is defined in `aiohttp.web_runner` — measured 3.14.1). No test body / planted string / `_PLANTED_BY_SERVER_DISTRIBUTION` touched. |
| `scripts/concurrent_wire_acceptance.py` | F12: `_run_session` uses `Popen(start_new_session=True)`; on `TimeoutExpired` → `_kill_process_group` (SIGKILL the group) then drain `communicate()`; on ANY other `BaseException` (Ctrl-C) → kill the group and re-raise (preserves `subprocess.run`'s kill-on-any-exception, widened to the tree). New `_output_tail` shared by both return paths. |
| `REPORT-impl-466-d1.md` | this report |

### Design notes
- **C3 "derive rather than hand-list":** the contract forbids deriving the detector's verbs from `_DEPENDENCY_LISTENER_VERBS` (derived == derived, contract §C3b), so the detector keeps its own verb set; the derivation lives in the contract's reach pin, which now matches the derived set {anyio, uvicorn}. For aiohttp a whole-namespace entry is ruled out (W11, honest-client control), so it is a per-library leaf allowlist-of-listeners. `SockSite` / `AppRunner` / `RawTestServer` / `NamedPipeSite` are deliberately NOT added (contract leaves `SockSite`/`AppRunner` unruled; the others are untested) — flagging them is a one-word edit if the lead wants it.
- **F1 passed-port:** `_abandon` closes the held socket (pre-existing behaviour on the named failures, now on every interrupt). Once released, uvicorn's `create_server(sock=<closed>)` fails and the thread ends — the passed-port test observes: thread ended within 5 s, port refuses.
- **F2 port release on overrun:** uvicorn's `Server.shutdown` closes its listeners BEFORE awaiting the lifespan shutdown, so a hanging lifespan leaves the port refusing (pinned by `_becomes_refused` in the clean-exit test).

## Removed/changed-behaviour inventory
| old behaviour | now |
|---|---|
| `start()` abandons only on its 2 named raises | abandons on ANY `BaseException` (F1; contract old-bug) |
| `stop()` silent on join overrun | returns `False`; `_loud_teardown` raises / notes (F2; contract old-bug) |
| `serve_http` exit: `server.shutdown()` **unbounded**, then a silent 5 s join | bounded 5 s (`DEFAULT_SHUTDOWN_TIMEOUT_S`), loud (ruling d). Passed-port semantics unchanged (no `server_close`; stays bound+listening). On overrun a daemon `"… shutdown"` thread stays blocked until the stuck handler returns. |
| driver `subprocess.run` kills the direct child on timeout AND on any exception | kills the whole process group on both (F12) |
| driver timeout tail: `expired.stdout if isinstance(..., str) else ""` | real tail (stdout+stderr, last `TAIL_LINES`). Old one was ALWAYS `""` on POSIX: probed 2026-09-26, Python 3.14.7 — `TimeoutExpired.stdout` is `bytes` (`b'hello\n'`) even with `text=True`. Old-bug, not pinned. |

## §VERIFY (all after every edit; HEAD `a124c5a` + this working tree)
Brief's command:
```
uv run pytest -p no:xdist -q -p no:cacheprovider loremaster/tests/test_loopback_serving.py loremaster/tests/test_no_raw_listener_in_test_trees.py scripts/test_concurrent_wire_acceptance.py loremaster/tests/test_migration_wire.py
94 passed, 2 warnings in 158.52s (0:02:38)
```
RED before (same three d1 files, pre-edit): `9 failed, 71 passed` — exactly the 9 declared (4×F1, 2×F2, C3a aiohttp, C3b `[anyio]`, F12).

`test_loopback_serving.py` ×5 more:
```
38 passed, 2 warnings in 8.87s
38 passed, 2 warnings in 8.39s
38 passed, 2 warnings in 8.87s
38 passed, 2 warnings in 9.08s
38 passed, 2 warnings in 8.88s
```
Skills: `cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests` → `120 passed in 19.40s`.
Ruff: `ruff check` clean + `ruff format --check` clean on all three changed files.
`scripts/typecheck.sh`: **0 errors in the three changed files.** Legs loremaster (43 errors / 18 files) and scripts (1) are RED — identical to the pre-existing other-packet set in REPORT-contract-466-d1.md §R7 (e.g. `loremaster.tasks has no attribute SupersedeResult`, `MigratePreconditionCounts`); skills, docs/eval, shellcheck OK.
Leaks: `ps` shows 0 `tree466-` / probe / wire-test processes after all runs. `:18500` never touched.
The 2 warnings are the pre-existing uvicorn `websockets.legacy` DeprecationWarnings.

## §E — Ruling e: real wire-lifespan teardown measurement (2026-09-26, HEAD `a124c5a` + this tree)
Instrument: scratch pytest plugin wrapping `_UvicornServerThread.stop` (the exact span `shutdown_timeout_s` bounds), `test_migration_wire.py`'s real `migration_wire` fixtures via `serve_asgi`; no assertion touched (verbatim in §Instruments).
| load | n | finished in budget | p50 | p99 | max |
|---|---|---|---|---|---|
| serial (2 × `-p no:xdist` runs, 14 passed each) | 24 | 24/24 | 0.155 s | 0.197 s | 0.198 s |
| concurrent pair (2 × `-n 4` sessions at once, 14 passed each) | 24 | 24/24 | 0.144 s | 0.194 s | 0.194 s |

p99 with n=24 is effectively the max (stated, not hidden). **Recommendation: max(5 s, 3×p99 ≈ 0.6 s) = 5 s → `DEFAULT_SHUTDOWN_TIMEOUT_S` left at 5.0, unchanged.** Headroom ≈ 25× the observed max.

## §D — Ruling d: `serve_http` bounded + loud (probe; no contract pin exists)
Stuck handler (`release.wait(60)`), request in flight at exit:
```
module: /home/ejprice/PycharmProjects/lore/loremaster/loremaster/testing/loopback.py
CLEAN: raised after 5.00s: server at 127.0.0.1:55885 did not finish its shutdown within 5.0s | budget=5.0
FAILING: after 5.00s kept ValueError('body-sentinel'); notes=['server at 127.0.0.1:40001 did not finish its shutdown within 5.0s']
CONTROL: prompt handler exited clean
```
(Old code would have blocked in `server.shutdown()` until the handler returned — 60 s here, forever in general; stdlib `BaseServer.shutdown` waits with no timeout.)

## §M — mutation proofs (ONE implementation, proven by mutation)
Real tree mutated with a `cp -a` content backup (`scratch_copy` not needed: `loopback.__file__` = `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/testing/loopback.py`, the real tree). Declared ids taken from `--collect-only` before the runs. Tool: `scripts/mutation_proof.py`.
- **M1** `if not stop(shutdown_timeout_s):` (clean-exit branch of `_loud_teardown`) → `... and False:` — `PROOF HELD — the declared RED set fired EXACTLY: [...TestAShutdownOverrunIsLoud::test_a_clean_exit_whose_shutdown_hangs_raises_naming_the_address]`, restored byte-exact (md5 `06d4befb2b4a11211c4f7620fb1b4ea1`).
- **M2** `body_error.add_note(overrun)` → `pass` — `PROOF HELD — ... [...test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note]`, restored byte-exact.
- **Sharing by mutation:** the same M1 applied by `sed` (1 site matched) → the `serve_http` stuck-handler probe printed `serve_http CLEAN overrun: SILENT (no raise)`; restored from backup (md5 equal) → `RAISED server at 127.0.0.1:59221 did not finish its shutdown within 5.0s`. One site silences both helpers ⇒ shared, not cloned.
- Not re-run: the contract author's W1–W17 battery (its Appendix D) — out of my brief.

## DRY ledger
| new symbol | lore query | returned | disposition |
|---|---|---|---|
| `_loud_teardown` | "bounded thread join on teardown that raises or adds a PEP 678 note when the shutdown overruns its timeout" | ran >120 s (backgrounded; finding #499), then returned only REPORT-refactor-466.md:58 (the F2 audit text) and the contract's `TestAShutdownOverrunIsLoud` — no existing helper | HAND-ROLLED — the policy is new (F2); it is the ONE copy both helpers call (proven §M). |
| `_stop_http_server` | (same class; stdlib read: `socketserver.BaseServer.shutdown`) | no bounded stdlib stop | HAND-ROLLED adapter over stdlib `shutdown()` |
| `_UvicornServerThread._await_started` | n/a — the existing wait loop extracted verbatim so the `except BaseException` wraps it | — | EXTRACTED (not new logic) |
| `_kill_process_group` | "kill process tree os.killpg subprocess Popen start_new_session timeout" (×2, tier custom / unscoped) | only a surrealdb-docs `db.kill` chunk; `budget` notice "0 of 6" (finding #499). Contract author's identical query (their DRY ledger) found only fake `kill(query_uuid)` stubs | HAND-ROLLED over stdlib `os.killpg`; a `lorerunes` candidate if a second caller appears (e.g. `expected_passed`, decisions-needed) |
| `_output_tail` | "last N lines tail of subprocess stdout and stderr output" | only reports / SurrealQL docs | HAND-ROLLED — extracts the driver's existing inline tail so both return paths share it |
| `_is_library_listener`, `_LISTENER_NAMES_BY_LIBRARY` | read the detector's `_is_in_namespace` / `_LISTENER_FUNCTIONS` | namespace matcher (whole namespace — over-broad for aiohttp, W11) | EXTENDED the detector; REUSES `_is_in_namespace` |

## Exposure (honesty)
The `_output_tail` DRY query's hit #2 was `REPORT-contract-466-d1.md:344-388` — inside the heading range the report labels "Appendix B — STUB", but containing a `driver.reference.py` diff (Popen + killpg). I saw it AFTER my F12 was implemented and green (22 passed). My build differs (kills on any `BaseException`, tail includes stderr, `with Popen` context). Appendix C was not read. Note for the lead: a lore search can surface withheld appendices to builders (and the Appendix B heading appears to contain reference-build content).

## Instruments (verbatim — the measurement is not separable from them)
`teardown_probe.py` (loaded via `PYTHONPATH=<dir> uv run pytest -p teardown_probe …`, env `TEARDOWN_PROBE_OUT=<file>`):
```python
"""Scratch pytest plugin (ruling e): time every serve_asgi teardown — _UvicornServerThread.stop — to a file."""
import os, time
import loremaster.testing.loopback as loopback
_OUT = os.environ["TEARDOWN_PROBE_OUT"]
_real_stop = loopback._UvicornServerThread.stop
def _timed_stop(self, shutdown_timeout_s=loopback.DEFAULT_SHUTDOWN_TIMEOUT_S):
    started = time.monotonic()
    finished = _real_stop(self, shutdown_timeout_s)
    with open(_OUT, "a", encoding="utf-8") as out:
        out.write(f"{time.monotonic() - started:.4f} {int(finished)} {os.getpid()}\n")
    return finished
loopback._UvicornServerThread.stop = _timed_stop
print("teardown_probe armed on", loopback.__file__)
```
Runs: serial `for i in 1 2; do … -p no:xdist … loremaster/tests/test_migration_wire.py; done`; pair: two `… -n 4 …` sessions launched together, `wait`. Stats: `statistics.median` and `statistics.quantiles(d, n=100, method="inclusive")[98]` over column 1.

Ruling-d probe:
```python
import http.server, threading, time, urllib.request
import loremaster.testing.loopback as lb
print("module:", lb.__file__)
release = threading.Event()
class Stuck(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        release.wait(60)
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass
def poke(url):
    threading.Thread(target=lambda: urllib.request.urlopen(url, timeout=60), daemon=True).start()
    time.sleep(0.3)
t0 = time.monotonic()
try:
    with lb.serve_http(Stuck) as s:
        poke(s.base_url); t0 = time.monotonic()
except lb.ServerShutdownTimeout as e:
    print(f"CLEAN: raised after {time.monotonic()-t0:.2f}s: {e} | budget={e.shutdown_timeout_s}")
release.set(); time.sleep(0.6); release.clear()
try:
    with lb.serve_http(Stuck) as s:
        poke(s.base_url); t0 = time.monotonic()
        raise ValueError("body-sentinel")
except ValueError as e:
    print(f"FAILING: after {time.monotonic()-t0:.2f}s kept {e!r}; notes={getattr(e,'__notes__',None)}")
release.set(); time.sleep(0.6)
class Ok(http.server.BaseHTTPRequestHandler):
    def do_GET(self): self.send_response(200); self.end_headers()
    def log_message(self, *a): pass
with lb.serve_http(Ok) as s:
    urllib.request.urlopen(s.base_url, timeout=5).read()
print("CONTROL: prompt handler exited clean")
```

## Flags (surfaced, not decided)
- **Unrelated RED:** `scripts/typecheck.sh` legs loremaster + scripts are red with 44 pre-existing errors in other packets' in-flight files (listed in REPORT-contract-466-d1.md §R7) — none in #466 files.
- Contract report §Surfaced-4 (budgets unvalidated: 0/negative/NaN) — still open, untouched.
- Finding **#499** filed (lore_search budget notice "0 of 6", a >120 s query).
