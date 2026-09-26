brief-base v16 read · brief project v7 read

# REPORT — refactor-466 (tdd-light Phase 5 REFACTOR + AUDIT, finding #466)

## SUMMARY BLOCK
- **State:** done-with-deviations. Refactor applied (R1–R5, behaviour-preserving, no test edited). **Acceptance ACCEPTED: 20/20 concurrent-pair rounds green, 14/14 ×2 each; 0 ServerStartupTimeout in 480 starts; startup p50 3.06 s, max 4.24 s against a 15 s budget.**
- **Deviations:**
  - (1) The acceptance run used `--allow-other-sessions` and ran alongside a28 (lead-directed).
  - (2) A timing-only pytest plugin was injected via `PYTEST_ADDOPTS` to measure startups.
  - (3) My first lane checker was blind to scratch-copy lore sessions. It was fixed, and the §4 receipt carries a correction.
- **Packages considered:** none new. I read uvicorn 0.48.0 `Server.shutdown` (it closes the passed `sockets`) and `Config.configure_logging` (`log_config=None` still sets levels) to verify F3 and the implementer's D1. Verdict: keep (in use).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 2 new symbols, both private extractions:
  - `_root_manifest`: FILE-LOCAL private extraction. `lore_search` for a manifest reader failed twice with an opaque store error (filed as **#496**). The Python text-scan fallback, said out loud, found root-`pyproject.toml` `tomllib` readers in ~10 other files: `test_secret_typing`, `test_ast_reach_helpers`, `_governed_contract`, `registration_sites.py`, `test_containerfile_locked`, the guard, and others. Several are DELIBERATELY independent oracles, so a repo-wide consolidation is a design question, not a refactor. HAND-ROLLED (local to `_logging_fixtures`).
  - `_http_server_on`: statements moved verbatim out of `serve_http` (no new policy). The contract's DRY ledger already established the helper as copy #1. My `lore_search("run uvicorn server in a background thread …")` returned only the helper's own `_UvicornServerThread._run`, and the guard proves no other test-tree listener exists.
- **Graded:** `6566ba6` · HEAD-at-report: `b434cfe` · DIFFERENT (10 ahead; none touch a #466 file, verified by `git diff --stat`).
- **Decisions needed:**
  - F1: start-wait cleanup on an unexpected `BaseException`.
  - F2: silent overrun of the shutdown join.
  - C1: `_CONTRACT_FILES` dead-entry pin.
  - C2: pin uvloop's absence, or force `loop="asyncio"`.
  - C3: `aiohttp` is installed but not a guarded namespace.
  - F12: xdist orphans on a driver timeout.
  - F7: guard cost of ~19 s single-process, deferred with its reason.
- **Foreign red to route:** the whole-tree-clone pin names `test_reanchor_58_r2_rulings.py::test_the_claim_lost_marker_is_ONE_literal_per_side` (58-r2) in addition to the two known 64b files.
- **Receipts:** §1 findings · §2 contract smells · §3 changes and equivalence proofs · §4 verify (146 passed / 1 foreign red, twice; skill idiom 120 passed; typecheck 0 in my files) · §5 acceptance · §Instruments (pasted verbatim).

## Capability check (brief-base §4)
| demanded | have | did instead | lead must change |
|---|---|---|---|
| lore-first DRY search | lore loaded; `lore_search` k=10 served 1 hit under budget 1100 | used the hit plus `lore_get_symbol`; for textual seams, Python scans | nothing |
| grep/rg | hook-blocked, even as a word (#473) | Python `pathlib` text scans (non-symbol seams) | — |
| quiet LORE lane detection by comm plus lore path | built `lore_lane.py` (pasted in §Instruments); positive control detected a planted `python3` whose cwd is the repo | — | — |

## 1. Findings — cold review of the GREEN diff (`git show 6566ba6`, #466 files only)

Severity: **D** = defect (needs a contract phase, because fixing it changes behaviour) · **C** = contract-test smell (REPORTED, not patched) · **N** = nit (fixed in place if it preserves behaviour).

### Contract coverage: MET
Every contract clause maps to an implementation path I read:
- held socket: `LoopbackPort.__init__` binds `:0` and keeps the socket.
- `sockets=[held.socket]`: `_UvicornServerThread._run`.
- `bind_and_activate=False` plus socket swap: `serve_http`.
- three cause leaves: bind in `LoopbackPort.__init__`; timeout and crash in `_UvicornServerThread.start`.
- crash named within one poll: `join(timeout=min(poll, remaining))` returns on thread death.
- lifespan forced on: `_UVICORN_LIFESPAN`.
- real shutdown on exit: `stop()` sets `should_exit` and joins.

**Race-freedom:** no bind→close→rebind anywhere in the helper or the four migrated sites. The only `bind` calls are `LoopbackPort.__init__` (port 0) and the contract's exempt squatter. uvicorn with `sockets=` calls `create_server(sock=)`. HTTPServer is built with `bind_and_activate=False` and its unbound socket is closed before the swap.

### F1 (D, low): the startup-wait path has no cleanup for an unexpected `BaseException`
`_UvicornServerThread.start()` cleans up (`_abandon`) only on its two named raises. Any other exception raised inside the wait loop leaves the process-global `uvicorn.error` handler attached and the server thread running on the held socket. Examples: `KeyboardInterrupt`, or pytest-timeout's signal-method exception raised in the main thread. `serve_asgi` calls `start()` outside its `try`, so `stop()` never runs. For an owned port, `LoopbackPort.__exit__` then closes the fd underneath a live uvicorn thread.
- **Fix:** wrap the wait in `except BaseException: self._abandon(); raise`.
- **Pin:** inject an exception into the wait, for example by monkeypatching `threading.Thread.join` to raise once. Then assert the handler is detached and `_is_released`.
- **Not applied:** it is a behaviour change on an uncontracted path, which my rules forbid in REFACTOR. **Decision needed:** fix now under a one-pin contract delta, or ledger it.

### F2 (D, low; trust doctrine "failures are LOUD"): a shutdown that overruns its join is silent
`stop()` joins for `_SHUTDOWN_JOIN_TIMEOUT_S` (5 s) and then returns, whether or not the thread finished. A lifespan teardown that hangs, such as a store or watcher close in the wire harness, passes unnoticed. The old `_serve` (join 20) had the same silence, so this is **old-bug-preserved**, not a regression. The replaced-code inventory did not list it (row 8 covers only the failed-start join).
- **Fix:** raise or warn naming the address when `thread.is_alive()` after the join.
- **Not applied:** behaviour change. **Decision needed.**

### F3 (N, docs): passed-port ownership differs between the two helpers, and neither docstring says so
- `serve_asgi(port=held)`: uvicorn's `Server.shutdown(sockets=…)` calls `sock.close()` on the passed socket. I read the installed uvicorn 0.48.0 `Server.shutdown` source. So on exit the caller's socket is already closed.
- `serve_http(port=held)`: calls neither `server_close()` nor `held.close()`. On exit the caller's socket is still bound **and listening**, so a connect is queued, not refused, until the caller closes it.

Both behaviours are safe for every current caller, which all nest inside the owner's `with`. **Fixed in place:** docstrings only.

### F4 (N): `_crash_detail` is convoluted and uses exception truthiness
It builds a one-line comprehension over a conditional tuple and tests `if self._crash`. **Fixed in place:** a plain two-step build with `is not None`. Same output.

### F5 (N, DRY): `_logging_fixtures.py` has three copies of "read the root `pyproject.toml`", and parses twice
- `workspace_roots` (pre-existing), `_declared_workspace_members` (pre-existing) and #466's new `_declared_testpaths` each call `tomllib.loads((root / "pyproject.toml").read_text())`.
- `parse_production_trees` now has two identical `ast.parse(path.read_text())` loops.

**Fixed in place:** the two `_declared_*` readers route through one `_root_manifest()`, and the parse loops are unified (the key sets are unchanged; the roots are disjoint, and the overlap rule is `setdefault`-shaped).
- **Not touched:** `workspace_roots` (pre-existing and heavily shared; routing it changes nothing observable). It is a follow-up candidate.
- **Deliberately NOT consolidated:** the guard's own `_declared_testpaths` in `test_no_raw_listener_in_test_trees.py`. Its docstring declares it the INDEPENDENT oracle for reach. Routing it through the fixture's reader would make reach `derived == derived`.

### F6 (N): `serve_http`'s socket swap is five inline statements with no name
**Fixed in place:** extracted as `_http_server_on(held, handler_class)` with a docstring. Behaviour is identical.

### F7 (N, efficiency): the guard re-parses the whole tree five times
~330 files per parse. Measured: `11 passed in 19.46s` single-process; each scan test takes 2.5–4.7 s.
- **NOT fixed:** a `functools.cache` on `_test_tree_scan` would freeze the parse. Under `test_ast_reach_helpers.TestSharingProvenByMutation`'s parser-drop, a cached consumer stays green: a private copy wearing the shared name (ONE IMPLEMENTATION / prove-sharing-by-mutation).
- The sanctioned caching idiom is a nullary module-scoped fixture the proof drives through `__wrapped__` (anchored-seam's `production_trees`). Adopting it adds the guard to the proof's adopter set and changes consumer signatures, which is contract-phase work.
- Under `-n auto` the five run in parallel, so wall cost is ~5 s. **Recommendation:** ledger it and do not change it now.

### F8 (N, DRY for the driver): `_NODE_ID_LINE` keeps `^…$` while matched with `.fullmatch`
The anchors are redundant but harmless, and the anchored-pattern seam is satisfied (`.fullmatch`). Left as is: the anchors document intent.

### F9 (N): the driver's public methods lack docstrings
Affected: `is_green`, `describe`, `green_rounds`, `accepted`, `summary`, `run_round`, `parse_arguments`, `main`. **Fixed in place:** docstrings only.

### F10 (N): the spike's `item2` builds `LoopbackPort()` outside a `with`
If the FastMCP app build raises, the held socket leaks until GC. The spike is a one-shot measurement script and the leak is bounded to its process. Left as is to avoid churn in a cited receipt instrument; noted.

### F11 (verified, not a finding): the spike docstring's "the command above provides the workspace venv"
Verified: `uv run --with httpx python -c "import loremaster.testing.loopback as m; print(m.__file__)"` → `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/testing/loopback.py`.

### F12 (N, driver): a session timeout may orphan xdist workers
`subprocess.run(timeout=)` kills only the direct `python -m pytest` child. `-n 4` workers may outlive a timed-out round. Not fixed (behaviour); surfaced.

### F13 (verified): lifecycle on the normal and named-failure exit paths is correct
- **serve_asgi normal exit:** `stop()` in `finally` → `should_exit` → uvicorn shutdown closes the socket → join → handler detached. An owned port is also closed by `LoopbackPort.__exit__`, which is idempotent.
- **Timeout / crash:** `_abandon` closes the socket and detaches the handler, and never joins (daemon thread).
- **serve_http:** `shutdown()` in `finally` then join. An owned port is closed by `LoopbackPort.__exit__`.
- **Exception in the `with` body:** `finally` covers it on both helpers.
- **The gap is F1 only.**

## 2. Test-smell rejection list over the Phase-1 tests (CONTRACT defects: REPORTED, not patched)

### C1 (drift-prone hardcoded convention → false green): `_CONTRACT_FILES` has no dead-entry pin
In `test_no_raw_listener_in_test_trees.py`, `test_both_trees_adopt_the_helper` excludes `_CONTRACT_FILES` so the contract's own files cannot vouch for a tree. If `test_loopback_serving.py` is ever renamed, the stale entry excludes nothing, and the renamed contract file counts as the `loremaster/tests` adopter. The adoption pin then stays GREEN even if `test_migration_wire.py` regresses to a private listener. That regression is still caught by the invariant test itself, so this is defence-in-depth, not a hole.
- **Fix:** a dead-entry pin (`every _CONTRACT_FILES path exists`), matching `_EXEMPT_SITES`' existing one.

### C2 (unpinned environment premise): `_spy_on_every_bind` assumes uvloop is absent
`test_loopback_serving.py::_spy_on_every_bind`'s docstring says uvloop is NOT installed (still true: measured 2026-09-26, `find_spec("uvloop") is None`), but nothing pins it. uvicorn's default `loop="auto"` would pick uvloop if it ever arrived. Whether uvloop's `create_server(host, port)` then binds through the Python `socket.socket.bind` the spy replaces is **LOW confidence / unverified** (uvloop is not installed, so I cannot read it). If it does not, `test_no_bind_to_a_specific_port_happens_during_the_whole_serve` goes blind to a rebinding build. Its non-vacuity check (`assert addresses`) would still pass on `LoopbackPort`'s own `:0` bind, so that message ("the spy certifies nothing") would not fire.
- **Mitigation already present:** wrong build w1 is also caught by the `fileno != -1` leg.
- **Fix:** pin `find_spec("uvloop") is None` with a re-open message, or have the helper force `loop="asyncio"`. The second is a helper behaviour change and needs a ruling.

### C3 (deny-list residual in the guard): `aiohttp` is INSTALLED but absent from `_LISTENER_NAMESPACES`
Measured 2026-09-26: `find_spec("aiohttp")` is truthy. An honest developer's `aiohttp.web.run_app(app, port=…)` or `TCPSite` opens a listener with no `.bind` and no asyncio verb in our source, so the guard cannot see it. The guard's own threat model ("an honest listener goes unnoticed IS a defect") classifies this as in-model. The fix is one namespace entry plus one `_PLANTED` line.
- **Re-open trigger if ledgered:** any new server-capable dependency (a deny-list is the enumeration antipattern; the RUNTIME rung named in the guard's known bound is the durable answer).

### Checked, no hit
- **Tautology:** none. `test_the_default_budget_is_a_positive_finite_number` is deliberately existence-and-sanity (measure-then-tune, §E), not a tautology. `test_the_three_causes_are_distinct_leaves…` is structural, with a stated reason.
- **Unrepresentative fixture:** the heavy real lifespan is scoped out of the unit contract and covered by the acceptance driver on the real `test_migration_wire.py`. The production door is Starlette `lifespan.startup.failed`, and it is pinned.
- **No magnitude guard:** the port is bounded by the kernel range read from `/proc`. Elapsed windows are bounded on both sides.
- **Forward-run-as-validation:** not data-driven; the acceptance driver IS the concurrency validation, not a smoke run of a derived output.

## 3. Changes applied (behaviour-preserving; no test file edited; no assertion touched)
All edits were made against `b434cfe`. The three files were content-backed-up first (md5 `f60e7619…` loopback.py, `3df81793…` _logging_fixtures.py, `1bc10ad8…` driver).

| # | file · symbol | change | proof it preserves behaviour |
|---|---|---|---|
| R1 (F4) | `loopback.py` · `_UvicornServerThread._crash_detail` | two-step build with `is not None` in place of a conditional-tuple comprehension over exception truthiness | same strings for all four (text?, crash?) cases; the crash pins in `test_loopback_serving.py` (§4) |
| R2 (F6) | `loopback.py` · new `_http_server_on(held, handler_class)` | the `bind_and_activate=False` socket-swap statements moved verbatim into a named, documented function; `serve_http` calls it | identical statement sequence; `TestServeHttp` (incl. the bind spy) + skill idiom (§4) |
| R3 (F3) | `loopback.py` · `serve_asgi` / `serve_http` docstrings | state passed-port ownership: serve_asgi's server CLOSES a passed socket; serve_http leaves it bound AND listening until the owner closes it | **constructed, not reasoned**: `ownership_probe.py` (§Instruments) printed `serve_asgi … fileno -1 REFUSED` · `serve_http … fileno 3 ACCEPTED/QUEUED` · after owner exit `fileno -1` |
| R4 (F5) | `_logging_fixtures.py` · new `_root_manifest()`; `_declared_workspace_members` / `_declared_testpaths` route through it; `parse_production_trees` one root loop instead of two parse loops | DRY: 2 of 3 manifest reads → 1; 2 parse bodies → 1 | `equiv_f5.py` (§Instruments): OLD (backup) vs NEW over all 16 flag combos — **same keys, same ORDER, identical `ast.dump` per file** (`F5 EQUIVALENT over 16 combos`; two transient mismatches were concurrent edits by other agents on the live tree, each vanished on immediate re-check). Parse-guard sanctioning is keyed on the `parse_production_trees` FRAME (`_stack_has_frame(caller, sanctioned_code)`), not a line, so one parse site is still sanctioned |
| R5 (F9) | `concurrent_wire_acceptance.py` · 10 methods/functions | docstrings only (each replacement count-asserted `== 1` before applying) | driver contract `scripts/test_concurrent_wire_acceptance.py` (§4) |

**Not applied (need a ruling — behaviour changes):** F1, F2, F12; contract defects C1–C3. **Not applied (cost > value / risk):** F7 (the cache would defeat the sharing-by-mutation proof), F8, F10. `workspace_roots`' own manifest read (the 3rd copy) is left: it is pre-existing, heavily shared, and outside #466.

## Instruments (pasted VERBATIM — the scratchpad is disposable)

### `lore_lane.py`
```python
#!/usr/bin/env python3
"""List live LORE test-lane processes: comm is uv|python*|pytest AND cwd or exe is in a lore tree.

Never reads argv text (a watcher whose own argv names 'pytest' would self-match). Excludes the
caller's own ancestry (pass --exclude-pid for extra PIDs). Exit 0 = quiet lane, 1 = busy (listed).
"""
import os, sys
from pathlib import Path

REPO = Path("/home/ejprice/PycharmProjects/lore").resolve()
COMMS = ("uv", "pytest")

def is_lore_tree(path: Path) -> bool:
    """True iff ``path`` is inside the lore repo OR any lore checkout/scratch copy (a directory
    holding both ``lore.yaml`` and ``loremaster/``) — scratch-copy runs share the test store."""
    if path == REPO or REPO in path.parents:
        return True
    return any((d / "lore.yaml").is_file() and (d / "loremaster").is_dir() for d in (path, *path.parents))


def ancestry(pid: int) -> set[int]:
    seen = set()
    while pid > 1 and pid not in seen:
        seen.add(pid)
        try:
            stat = Path(f"/proc/{pid}/stat").read_text()
        except OSError:
            break
        pid = int(stat.rsplit(")", 1)[1].split()[1])
    return seen

def main() -> int:
    excluded = ancestry(os.getpid())
    excluded |= {int(a) for a in sys.argv[1:] if a.isdigit()}
    busy = []
    for entry in Path("/proc").iterdir():
        if not entry.name.isdigit() or int(entry.name) in excluded:
            continue
        try:
            comm = (entry / "comm").read_text().strip()
            cwd = Path(os.readlink(entry / "cwd"))
        except OSError:
            continue
        if not (comm in COMMS or comm.startswith("python")):
            continue
        try:
            exe = Path(os.readlink(entry / "exe"))
        except OSError:
            exe = Path("/")
        if is_lore_tree(cwd) or is_lore_tree(exe):
            busy.append((int(entry.name), comm, str(cwd)))
    for pid, comm, cwd in sorted(busy):
        print(f"{pid} {comm} {cwd}")
    return 1 if busy else 0

if __name__ == "__main__":
    raise SystemExit(main())
```

### `run_gated.sh`
```bash
#!/usr/bin/env bash
# Usage: run_gated.sh <logfile> <cwd> -- <command...>
# Runs the command in its own process group; a watchdog kills the WHOLE group (by PGID, never by
# pattern) if MemAvailable drops below 15 GiB. Exit status = the command's, or 137 if killed.
log=$1; cwd=$2; shift 3
cd "$cwd" || exit 2
setsid "$@" >"$log" 2>&1 &
pid=$!
while kill -0 "$pid" 2>/dev/null; do
  avail_kb=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  if [ "$avail_kb" -lt $((15*1024*1024)) ]; then
    echo "WATCHDOG: MemAvailable ${avail_kb}kB < 15GiB — killing process group $pid" >>"$log"
    kill -TERM -- "-$pid"; sleep 5; kill -KILL -- "-$pid" 2>/dev/null
    wait "$pid"; exit 137
  fi
  sleep 2
done
wait "$pid"
```

### `ownership_probe.py`
```python
"""Probe F3: what a PASSED LoopbackPort looks like after serve_asgi / serve_http exit."""
import http.server, socket
from loremaster.testing.loopback import LoopbackPort, serve_asgi, serve_http

async def app(scope, receive, send):
    if scope["type"] == "lifespan":
        while True:
            m = await receive()
            if m["type"] == "lifespan.startup":
                await send({"type": "lifespan.startup.complete"})
            else:
                await send({"type": "lifespan.shutdown.complete"}); return

class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass

def connect_state(host, port):
    try:
        socket.create_connection((host, port), timeout=1).close(); return "ACCEPTED/QUEUED"
    except ConnectionRefusedError:
        return "REFUSED"

with LoopbackPort() as held:
    with serve_asgi(app, port=held):
        pass
    print("serve_asgi passed port after exit: fileno", held.socket.fileno(), connect_state(held.host, held.port))
with LoopbackPort() as held:
    with serve_http(H, port=held):
        pass
    print("serve_http passed port after exit: fileno", held.socket.fileno(), connect_state(held.host, held.port))
    held_fd_open = held.socket.fileno() != -1
print("serve_http passed port after OWNER exit: fileno", held.socket.fileno())
```

### `equiv_f5.py`
```python
"""F5 equivalence: old (backup) vs new parse_production_trees + _declared_* over all 16 flag combos."""
import ast, hashlib, importlib.util, itertools, sys
sys.path.insert(0, ".")
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path); mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod; spec.loader.exec_module(mod); return mod
old = load("old_fixtures", sys.argv[1]); new = load("new_fixtures", "_logging_fixtures.py")
assert old._declared_workspace_members() == new._declared_workspace_members()
assert old._declared_testpaths() == new._declared_testpaths()
def digest(trees):
    return {k: hashlib.sha1(ast.dump(v).encode()).hexdigest() for k, v in trees.items()}
for flags in itertools.product([False, True], repeat=4):
    kw = dict(zip(("include_scripts", "include_skills", "include_tests", "include_testpaths"), flags))
    a, b = digest(old.parse_production_trees(**kw)), digest(new.parse_production_trees(**kw))
    assert list(a) == list(b), (kw, set(a) ^ set(b))  # same keys, same ORDER
    assert a == b, kw
    print(flags, len(a), "identical")
print("F5 EQUIVALENT over 16 combos")
```

### `startup_probe_466.py`
```python
"""pytest plugin (timing-only): record every loopback server start's duration and outcome.

Loaded via PYTEST_ADDOPTS="-p startup_probe_466" with this dir on PYTHONPATH; appends one JSON line
per _UvicornServerThread.start call to $STARTUP_PROBE_LOG. Re-raises everything unchanged.
"""
import json, os, time
from loremaster.testing import loopback

_original_start = loopback._UvicornServerThread.start

def _timed_start(self, startup_timeout_s):
    began = time.monotonic()
    outcome = "started"
    try:
        _original_start(self, startup_timeout_s)
    except BaseException as error:
        outcome = type(error).__name__
        raise
    finally:
        with open(os.environ["STARTUP_PROBE_LOG"], "a", encoding="utf-8") as log:
            log.write(json.dumps({"pid": os.getpid(), "seconds": round(time.monotonic() - began, 4),
                                  "budget": startup_timeout_s, "outcome": outcome}) + "\n")

loopback._UvicornServerThread.start = _timed_start
```

### `lane_watch.sh`
```bash
#!/usr/bin/env bash
# Every 10s, emit any LORE-lane process NOT in process group $1 (the acceptance run's group).
# Exits when group $1 is gone.
pgid=$1
while kill -0 -- "-$pgid" 2>/dev/null; do
  python3 /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/5a869a31-f116-48e6-b719-7cc7498715f4/scratchpad/lore_lane.py 2>/dev/null | while read -r p comm cwd; do
    g=$(awk '{print $5}' /proc/$p/stat 2>/dev/null)   # field 5 = pgrp (comm has no spaces for these)
    [ -n "$g" ] && [ "$g" != "$pgid" ] && echo "$(date +%T) FOREIGN lore-lane pid=$p comm=$comm pgid=$g"
  done
  sleep 10
done
echo "$(date +%T) acceptance group $pgid ended"
```

(`equiv_f5.py` is run from `loremaster/tests` with the backup path as argv[1]; the live-tree re-check wrapper added one `if a != b:` re-parse before the assert.)

## 4. Receipts (after R1–R5, measured 2026-09-26 at HEAD `b434cfe` + my working-tree edits)
⚠ **CORRECTION: the lane was NOT proven quiet for these runs.** The first version of `lore_lane.py` keyed on "cwd under the repo" and was **blind to lore sessions running from SCRATCH COPIES** (for example a 58-r2 `pytest -n 16` with cwd `…/051e3520…/scratchpad/ref`, which holds `lore.yaml` + `loremaster/`). The acceptance driver's argv-based preflight exposed the false clear. The checker now treats any lore checkout as a lore path (`is_lore_tree`; the §Instruments copy is the FIXED one). The counts below stand as measured; only the quiet-lane precondition is unproven, and a concurrent lane can only have ADDED stress.
**Brief verify set** (`-p no:xdist`, under the 15 GiB watchdog):
```
FAILED loremaster/tests/test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
1 failed, 146 passed, 4 skipped, 2 warnings in 154.08s (0:02:34)
```
- **The one red is not mine.** Its offenders (re-run `--tb=short`) are `test_findings_identity_64b.py::_routing_markers`, `test_governed_substrate_64b.py::_resource_construction_sites` (both named in the brief) **and `test_reanchor_58_r2_rulings.py::test_the_claim_lost_marker_is_ONE_literal_per_side`**. That third one is NEW (untracked, contract-58-r2's), and the brief did not list it. **Its owner needs telling.**
- The brief's other two known reds, the anchored-pattern seam on `restore_prod_dump.py` and the sharing-proof knock-on, are **GREEN** in this run (cleared upstream by `441f3b0`/`8ec8c6a`).

**Skill idiom** (`cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests`): `120 passed in 16.37s`.

**ruff check** on the 3 changed files: `All checks passed!`. `ruff format --check` flags `_logging_fixtures.py`, but that file was already unformatted at HEAD (checked by `git show HEAD:… | ruff format --check --stdin-filename`). Format is not a manifested gate, so I did not mass-reformat a shared file.

**typecheck.sh**: 0 errors in the 3 changed files. The loremaster leg fails with 41 errors and the scripts leg with 1. Per file:

| errors | file | git state | verdict |
|---|---|---|---|
| 7 | `test_supersede_reanchor_58.py` | tracked | packet-58 contract (known) |
| 7 | `test_reanchor_58_r2_rulings.py` | untracked | 58-r2 contract |
| 3 | `test_reanchor_58_r2_probes.py` | untracked | 58-r2 contract |
| 2 | `test_reanchor_58_r2_am2.py` | untracked | 58-r2 contract |
| 1 | `test_reanchor_58_r2_scale.py` | untracked | 58-r2 contract |
| 2 | `_reanchor_58_support.py` | modified | 58-r2 in flight |
| 1 | `test_task_claimable_partition_58.py` | modified | 58-r2 in flight |
| 1 | `test_task_guarded_shell_58.py` | modified | 58-r2 in flight |
| 1 | `test_task_read_surface.py` | modified | 58-r2 in flight |
| 1 | `test_blocks_edge.py` | modified | 58-r2 in flight |
| 6 | `test_governed_substrate_64b.py` | untracked | 64b contract |
| 4 | `test_findings_identity_64b.py` | untracked | 64b contract |
| 2 | `test_findings_governance_64b.py` | untracked | 64b contract |
| 1 | `test_findings_enforcement_64b.py` | untracked | 64b contract |
| 1 | `test_findings_migrate_64b.py` | untracked | 64b contract |
| 1 | `test_findings_schema_64b.py` | untracked | 64b contract |
| 1 | `scripts/test_forgery_door_sweep.py` | modified | `SupersedeResult` missing (58 in flight) |

None are #466 files.

**Verify re-run** (2026-09-26 13:51–13:54, with `lane_watch.sh` observing the lane throughout):
```
FAILED loremaster/tests/test_ast_reach_helpers.py::TestNoTestFileHandRollsAWholeTreeParserOutsideTheAllowlist::test_no_unallowlisted_whole_tree_parser_clone_survives
1 failed, 146 passed, 4 skipped, 2 warnings in 126.45s (0:02:06)
```
- Same verdict as the first run, and the same foreign red.
- **The lane was NOT quiet** despite a 2×15 s quiet reading at 13:51:55. A foreign `-n 12` lore pytest (pgid 2919752, from a scratch copy) appeared at 13:52:03 and ran about 1 min, and two short runs followed (13:53:34, 13:53:54). The source is **contract-63c-i-a-a28's `mutation_proof.py` sequence** (session `e8143e2c`, scratch `…/scratchpad/ref`): back-to-back pytest runs whose gaps can fool a short quiet window. So the acceptance run waits for a 60 s continuously quiet lane.

## 5. Acceptance: `scripts/concurrent_wire_acceptance.py`, 20 consecutive concurrent-pair rounds (2026-09-26 13:55:25–14:02:12)
**Verdict: `#466 concurrent-pair acceptance: ACCEPTED — 20/20 rounds green in both sessions (20 run; expected 14 passed per session)`.** RUNNER EXIT 0; the watchdog never fired.

**Run conditions:**
- Lead-directed (it overrides the quiet-lane wait): run ALONGSIDE contract-63c-i-a-a28's mutation-proof pytests.
- Default `-n 4` per session; the expected count of 14 was derived by the driver's `--collect-only`.
- Code under test: HEAD `b434cfe` plus my R1–R5 working-tree edits.
- `--allow-other-sessions` was passed. **Deviation:** the driver's argv-text preflight refuses on ANY process naming pytest; the lead ruled the concurrent run.
- MemAvailable at launch: 37 GiB. A 15 GiB watchdog (whole process-group kill) was armed.
- Startup timings came from `startup_probe_466.py`, a timing-only plugin injected via `PYTEST_ADDOPTS` (§Instruments). It re-raises everything and changes no repo code.

**Per round.** Pass counts are `session1 · session2`. The third column names each foreign lore pytest observed live during the round (the fixed `lore_lane.py`, sampled every 5 s; a foreign run shorter than 5 s could be missed).

| round | s1 · s2 | exit | foreign lore pytest during the round |
|---|---|---|---|
| 01 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377: `pytest -n 8 … -k "not RS5" test_fixwave_a28_63c_i_a.py test_fixwave_a19a_63c_i_a.py …` (scratch copy `e8143e2c…/ref`) |
| 02 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (same) |
| 03 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (same) |
| 04 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (same) |
| 05 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (now without `-k "not RS5"`) |
| 06 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (same) |
| 07 | 14/14 · 14/14 | 0 · 0 | a28 pgid 2925377 (same) |
| 08–20 | 14/14 · 14/14 each | 0 · 0 each | none observed |

Every round shows `0 failed/errored` in both sessions. Round wall time was 16–27 s.

**ServerStartupTimeout count: 0.** Of 480 server starts (40 sessions × 12, across 160 distinct xdist worker pids), 480 reported `started`: 0 timeouts, 0 `ServerThreadCrashed`, 0 `ServerBindError`.

**Startup spread** (time from `start()` to uvicorn `started`, i.e. the real heavy lifespan: probe gate + store + watcher; budget 15.0 s):
- min 1.869 s · p50 3.059 s · p90 3.547 s · p99 4.178 s · max 4.237 s · mean 3.101 s.
- **Headroom:** the worst observed start used 28% of the budget, a 3.5× margin at max.

**§E measure-then-tune recommendation:** keep `DEFAULT_STARTUP_TIMEOUT_S = 15.0`. Nothing timed out, and max/budget is 0.28. Re-open trigger: any `ServerStartupTimeout` in a gate run, or a p99 above 7.5 s (half the budget).

**Bound on what this proves:** rounds 1–7 ran three concurrent lore pytest sessions (the pair plus a28's `-n 8`); rounds 8–20 ran only the pair. The pre-#466 failure shape (2 failed + 4 errors under a concurrent pair) did not appear in any round.
