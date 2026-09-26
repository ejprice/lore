brief-base v16 read · brief project v7 read

# REPORT-refactor-466-d1 — #466 delta d1, tdd-light Phase 5 (REFACTOR + AUDIT) + lead pins (c) and (d)

## SUMMARY BLOCK
- **state:** done-with-deviations
- **deviations:** (1) pins (c)/(d) authored AFTER the build (lead-directed; both rulings post-date the contract) — each proven able to fail by mutation, 9/9 PROOF HELD (§Pins-c, §Pins-d). (2) The DRY lore search ran post-write (it took >120 s — finding #500). (3) Pin (c) uses two private pytest APIs (`_pytest.fixtures.getfixturemarker`, `request._fixturemanager._arg2fixturedefs`); pytest has no public fixture registry; failure mode is loud.
- **Packages considered:** pin (c) — pytest's own plugin discovery (`importlib.metadata.entry_points(group="pytest11")`, the mechanism pytest uses) + pytest's fixture marker reader → `replace` of a hand-listed name set (read: installed pytest 9.0.3 `getfixturemarker` signature, pytest-asyncio 1.4.0 `_unused_port`, anyio 4.13.0 `FreePortFactory`). Pin (d) — stdlib `http.server`/`socket` test fixtures only. No production mechanism specified.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 14 new test-side symbols (8 guard + 6 serving; test classes excluded), all dispositioned (§DRY ledger); detector EXTENDED in place, not forked.
- **Graded:** `ef0fcda` · HEAD-at-report: `3861050` · DIFFERENT (2 ahead, docs-only: `REPORT-lead-63c.md`; the 5 in-scope files are byte-identical at both)
- **headline finding:** R1 (MEDIUM, probe-confirmed) — F1's leak on the TEARDOWN side: a `BaseException` during `_UvicornServerThread.stop`'s join leaves the `uvicorn.error` capture handler attached. One-line fix (`try: join finally: _detach_capture()`), not applied (behaviour change; needs a RED pin first).
- **decisions-needed:** (a) R1: fix now with a test-first pin (my rec: yes, same cycle), or ledger? · (b) give `serve_http` a `shutdown_timeout_s` (pin d currently spends the real 5 s default twice) — rec: yes · (c) pin (c) refuses ANY unclassified plugin fixture (allowlist-the-safe) — confirm that over a name-keyed deny-list · (d) contract smells T1–T4 go to a contract author.
- **receipts:** findings §Step 1 (R1–R10) · smells §Step 2 (T1–T4) · nits §Step 3 · pins+mutations §Pins-d/§Pins-c · verify §Step 5 (`110 passed`; ×5 `41 passed` each; skills `120 passed`; ruff clean; typecheck 0 in-scope, 44 in other packets' files) · instruments §Instruments A/B (verbatim).

---

## Capability check (brief-base §4)
- **Demanded:** lore-first. **Have:** lore tools loaded (`ToolSearch "+lore"`), registered on `lore_comms` (session `466-d1`).
- **Demanded:** grep/rg hook-blocked. **Did:** `awk` / `sed -n` for textual seams (said at each use below).
- **Demanded:** mutation in a `./scripts/scratch_copy.sh` copy with `loremaster.__file__` printed. **Have:** the script; receipts in §Pins.
- **Demanded:** kill by PID, never `:18500`. No store is touched by any file in scope.
- Idle-gate contract written: `/tmp/claude-idle-gate-lore/unknown-refactor-466-d1.contract` (the harness exposes no session id to Bash — `$CLAUDE_SESSION_ID` is empty — so the file is named with `unknown`, the fallback the directory already uses).

## Step 1 — cold review of `git diff a124c5a ef0fcda` (written BEFORE any edit)

Graded: `ef0fcda` · HEAD at review start: `8738503` (one docs-only commit, `REPORT-lead-63c.md`; no graded symbol moved).

| # | sev | finding | evidence |
|---|---|---|---|
| R1 | **MEDIUM — defect** | **F1's class, on the TEARDOWN side.** `_UvicornServerThread.stop` calls `_detach_capture()` only AFTER an uninterrupted `self._thread.join(...)`. A `BaseException` landing in that join (Ctrl-C, pytest-timeout's signal method — the exact door F1 was about) propagates out of `stop()` with the `uvicorn.error` capture handler still attached, for the life of the process. F1's fix wrapped only `start()`. | Probe (verbatim, §Instruments A), run 2026-09-26 at `8738503`: control `handlers before 0 after 0`; interrupt at 0.5 s into a 3 s teardown join → `raised Stuck`, `handlers before 0 after 1`. Fix is one line: `try: join finally: _detach_capture()`. **Not applied** — it changes behaviour on an exceptional path, so it needs a RED pin first and it is outside this brief's grant (refactor = behaviour-preserving). Decision (a). |
| R2 | LOW — API asymmetry | `serve_http` exits through the SAME `_loud_teardown`, but takes no `shutdown_timeout_s`: its budget is always `DEFAULT_SHUTDOWN_TIMEOUT_S` (5 s). Consequence: pin (d) must spend the real 5 s per overrun test, and a caller cannot tune it. The builder flagged it (impl report "d-follow-up"). | `serve_http` signature. Decision (b). |
| R3 | LOW — policy is genuinely ONE | `_loud_teardown` is the single overrun policy; both helpers call it and neither re-implements the decision (the `stop` callables only return a bool; the raise/note choice lives in one place). **Proven by mutation in §Pins-d**: mutating `_loud_teardown` reddens serve_asgi's F2 pins AND the new serve_http pins. | §Pins-d receipts. |
| R4 | LOW | In `_loud_teardown`'s failing-body branch, if `stop()` itself raises (e.g. `_stop_http_server`'s `Thread.start()` → `RuntimeError: can't start new thread`), the body's exception is replaced (it survives only as `__context__`). Same on the clean path by construction. Not worth a fix at this blast radius; surfaced. | code read. |
| R5 | LOW — prose currency (natural-language surface) | Two docstrings still describe the pre-ruling-(d) world: `DEFAULT_SHUTDOWN_TIMEOUT_S` says it is "How long `serve_asgi`'s exit waits" (serve_http now uses it too); `ServerShutdownTimeout` says "A STARTED server's **lifespan** shutdown overran" (serve_http has no lifespan — its overrun is the `serve_forever` thread). | Fixed as refactor nits (§Step 3). |
| R6 | LOW — guard reach | `_LISTENER_NAMES_BY_LIBRARY["aiohttp"]` is a DENY-list of five leaves — enumerate-the-forbidden. Left unflagged by design or omission: `SockSite`, `AppRunner` (contract explicitly unruled), `RawTestServer`, `NamedPipeSite`, `test_utils.TestClient` (it starts a `TestServer` internally when handed an app via the pytest plugin's `aiohttp_client`). The saving grace: the C3b derivation reddens the day a test first imports aiohttp — at which point a human is forced to look. Bound, surfaced. | builder's own design note + code read. |
| R7 | LOW — derivation honesty | C3b's reach derivation is honest (derived from what the test trees import × what those distributions' source does; non-empty asserted; equality with the planted map both ways). Two silent-shrink doors inside it — see test-smell T3. The verb oracle is a second byte-identical copy of the detector's verbs (T4). Sync `.bind`+`.listen` servers are a named bound (1). | code read. |
| R8 | LOW | `ConcurrentPairDriver.expected_passed()` still uses `subprocess.run(timeout=)` (the F12 orphan class; `--collect-only` spawns no workers so exposure is low). Carried forward from the contract report §Surfaced-5 / impl decisions — still open at `ef0fcda`. | code read. |
| R9 | INFO | F12 `_kill_process_group` fires on timeout and on `BaseException`; on NORMAL completion any group member that outlived the leader is not killed. xdist joins its workers before exit, so no live exposure. | code read. |
| R10 | INFO — lifecycle table (every exit path of the d1 code) | see below | code read + probes |

**R10 — lifecycle table (socket · thread · capture handler) per exit path, at `ef0fcda`:**

| path | held socket | server thread | capture handler |
|---|---|---|---|
| asgi start: named failure | closed (`_abandon`) | asked to exit, daemon | detached |
| asgi start: any other BaseException (F1) | closed | asked to exit | detached |
| asgi clean exit, in budget | closed by uvicorn / owned `LoopbackPort` | joined | detached |
| asgi clean exit, overrun | uvicorn closed listeners before the lifespan hang (impl §F2 note) | daemon, still in the hung lifespan | detached |
| asgi body raises | same as above two rows | same | detached |
| **asgi: BaseException DURING the teardown join** | owned: closed by `LoopbackPort.__exit__`; passed: still the caller's | `should_exit` set → ends when lifespan returns | **LEAKED (R1)** |
| http clean / overrun / body raises | owned: closed by `LoopbackPort.__exit__`; passed: stays bound+listening (documented) | overrun: daemon, ends after the stuck handler returns; a daemon "… shutdown" thread too | n/a |
| http: BaseException during the join | as above | shutdown already requested → ends after the handler returns | n/a |

## Step 2 — test-smell list over the d1 tests (CONTRACT defects: reported, NOT patched)

| # | smell class | where | what a wrong build gets past |
|---|---|---|---|
| T1 | **no magnitude guard** | `TestAShutdownOverrunIsLoud.test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note` | Only an UPPER elapsed bound. A build that, on the failing path only, skips the wait (checks `is_alive()` at once, adds the note, returns) passes. It also asserts NO lifecycle on the failing path (handler detached, port released) — W9 covers the clean path only. |
| T2 | **drift-prone hardcoded convention** | `test_positive_control_a_slow_in_budget_shutdown_does_not_raise` passes `shutdown_timeout_s=GENEROUS_STARTUP_BUDGET_S` | A STARTUP constant used as a SHUTDOWN budget: retuning the startup budget silently retunes this control. Wants its own `GENEROUS_SHUTDOWN_BUDGET_S`. |
| T3 | **unrepresentative / silent-shrink** | `_server_capable_imported_distributions` | `except OSError: continue` and `distribution.files or []` drop a distribution from the reach SILENTLY (no count, no name). A RECORD-less install (some editable/system installs) of a server library is exempt with nothing said — the reach shrinks exactly where it cannot be seen. Should collect and assert-empty (or render) the skipped set. |
| T4 | **drift-prone hardcoded convention** | `_DEPENDENCY_LISTENER_VERBS` vs the detector's `_LISTENER_METHODS` | Byte-identical six-verb sets, deliberately "independent" but with nothing relating them. Add a verb to the detector only → the oracle is narrower than the detector, silently. The independence argument (derived ≠ derived) holds for the DETECTOR reading the oracle, not for leaving the two unrelated; a pin `oracle ⊇ detector-methods` keeps independence and kills the drift. |
| T5 | none found | F1 (`TestAnInterruptedStartupLeavesNothingBehind`) | Identity, handler snapshot, thread survivors, port refusal, injection-count non-vacuity — discriminating. |
| T6 | none found | F12 (`TestATimedOutSessionTakesItsWholeTreeWithIt`) | depth-3 tree, 6-member non-vacuity, marker-checked liveness with its own positive control. |
| T7 | none found | C2, C1, C3a | C3a's honest-client control kills the whole-namespace build; C1 has a planted-stale control. |

No tautology and no forward-run-as-validation found in the d1 tests.

## Step 3 — refactor nits applied (behaviour-preserving; no assertion weakened or retargeted)

| file | change | why |
|---|---|---|
| `loremaster/loremaster/testing/loopback.py` `DEFAULT_SHUTDOWN_TIMEOUT_S` docstring | now names BOTH helpers (serve_asgi: lifespan shutdown; serve_http: the `serve_forever` thread) and says serve_http always uses the default | R5 — prose taught the pre-ruling-(d) world |
| `loremaster/loremaster/testing/loopback.py` `ServerShutdownTimeout` docstring | "lifespan shutdown" → "shutdown", with a sentence naming what overruns for each helper | R5 |

No code-path change in `loopback.py`: `git diff` over it is docstring-only (+10/−4 lines at `8738503`+working tree). R1 (the teardown-join handler leak) is a behaviour change and was NOT applied — decision (a).

## Step 4 — lead-directed pins (documented deviation from test-first: both rulings post-date the contract)

### §Pins-d — `serve_http` teardown with a stuck handler is bounded and loud, via the SAME `_loud_teardown`
New in `loremaster/tests/test_loopback_serving.py`: `TestServeHttpShutdownOverrunIsLoud` (3 tests) + `_stuck_handler_class`, `_stick_a_request`, `STUCK_HANDLER_BOUND_S`, `STUCK_HANDLER_REQUEST`, `_STUCK_EXIT_WINDOW_LOW_S/HIGH_S`.
- **clean exit** → `ServerShutdownTimeout`, exact type, `.host/.port` == served, message names `host:port` + "shutdown", `.shutdown_timeout_s == DEFAULT_SHUTDOWN_TIMEOUT_S`, elapsed in `[0.9×5 s, 5 s + 2 s]`, owned port refuses afterwards, and every thread the test started ends once the handler is released.
- **failing body** → the SAME exception object propagates, carrying a note naming `host:port` + "shutdown"; elapsed bounded on BOTH sides (this closes, for serve_http, the magnitude gap T1 names for serve_asgi's twin).
- **positive control** → a failing body with a PROMPT handler gets no note.
- Discrimination: `STUCK_HANDLER_BOUND_S` (30 s) > default + grace is asserted in-test; the handler's own wait is bounded so a wrong build that waits for it goes RED instead of hanging.
- Reading chosen (the two readings of "exactly like serve_asgi's"): **(A, applied)** pin serve_http at its only budget, the 5 s default — no API change; **(B)** add `shutdown_timeout_s` to serve_http (a public-API change; cuts ~9 s off the class). B is decision (b).

**Mutation receipts** — scratch copy `…/scratchpad/scr466d1` made by `./scripts/scratch_copy.sh` (provenance asserted by the script), driver prints:
`loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/dc1fb7c6-f219-4ef4-88ae-41ecce96bd71/scratchpad/scr466d1/loremaster/loremaster/__init__.py` and `loopback.__file__ = …/scr466d1/loremaster/loremaster/testing/loopback.py`. Each proof ran through `scripts/mutation_proof.py` (declared RED set written in the driver BEFORE the run, diffed both ways, file restored by content — restored md5s equal the real tree's: `loopback.py b90f6440…`, guard `083ebd1f…`, serving `7e685540…`).

| proof | mutation | declared RED (== observed) | tail |
|---|---|---|---|
| d1 | **shared** `_loud_teardown`: clean-exit raise disabled | asgi `test_a_clean_exit_whose_shutdown_hangs_…` + http `test_a_clean_exit_with_a_stuck_handler_…` | `2 failed, 6 passed` — PROOF HELD |
| d2 | **shared** `_loud_teardown`: `add_note` → `pass` | asgi + http `test_a_failing_body_keeps_its_own_exception_…` | `2 failed, 6 passed` — PROOF HELD |
| d3 | `_stop_http_server` back to the OLD synchronous `server.shutdown()` | both http overrun tests; asgi untouched | `2 failed, 6 passed … 63.48s` — PROOF HELD (bounded by the handler's 30 s, no hang) |
| d4 | serve_http BYPASSES the shared policy (private silent `try/finally: stop()`) | both http overrun tests; asgi untouched | `2 failed, 6 passed` — PROOF HELD |

d1+d2 are the ruling's "a mutation of the shared function must redden BOTH" — it does, both directions of the policy. d4 is the ROUTING direction: serve_http cannot drop the shared policy without its own pins reddening.

### §Pins-c — pytest-plugin port fixtures are forbidden in the test trees (derived, allowlist-the-safe)
New in `loremaster/tests/test_no_raw_listener_in_test_trees.py`: `_SAFE_PLUGIN_FIXTURES` (12 classified entries, reasons inline), `_RULED_PORT_FIXTURES`, `_installed_plugin_fixtures()` (derived from the `pytest11` entry points — independent of `-p no:…`), `_forbidden_plugin_fixtures()` (= derived − safe), `_FIXTURE_LOOKUP_VERBS`, `_plugin_fixture_primitive`, `_is_installed_third_party`; `_SiteCollector` gains the request leg (parameter · `getfixturevalue(…)` · `usefixtures(…)`) so the EXISTING invariant, exemption map and dead-entry pin cover it — one detector, not a second guard. Class `TestPluginPortFixturesAreForbidden` (13 tests incl. 8 parametrised).
- **The derivation found what the ruling did not name:** anyio 4.13.0's `free_tcp_port`, `free_tcp_port_factory`, `free_udp_port`, `free_udp_port_factory` — the same bind→close→"return an unbound port" race (source read: `anyio.pytest_plugin.FreePortFactory.__call__` docstring "Return an unbound port"). A hand-list of pytest-asyncio's names would have missed all four. Forbidden set at `8738503`: the 4 pytest-asyncio + 4 anyio names.
- **Live tree:** the invariant is GREEN — no test-tree file requests any of the 8 today.
- **Reach as a checked variable:** each derived forbidden name is shown flagged (parametrised at collection, so the set growing grows the pin); ruled names reached (non-vacuity); every safe entry still defined (dead-entry); the RUNNING session's third-party fixture registry ⊆ the static derivation (the register-at-configure and `-p`/`pytest_plugins` door).
- **Bounds (in the class docstring, each with a re-open trigger):** pytest core trusted wholesale; `pytest_plugins`/`-p`-only plugins (e.g. `aiohttp.pytest_plugin`'s `aiohttp_unused_port`) seen only by the live leg in a session that loads them — measured: no conftest declares `pytest_plugins`, `addopts` has no `-p`; indirect parametrisation unread; a non-fixture param spelled like a forbidden fixture is a false positive.
- **Private API used, said out loud:** `_pytest.fixtures.getfixturemarker` (static leg) and `request._fixturemanager._arg2fixturedefs` (live leg). pytest exposes no public fixture registry. A pytest release that moves either fails LOUD (ImportError at collection / AttributeError in the live leg), never silently.

| proof | mutation (guard = the build for pin c) | declared RED (== observed) | tail |
|---|---|---|---|
| c1 | parameter leg removed | planted pin + all 8 derived-name pins | `9 failed, 4 passed` — PROOF HELD |
| c2 | `getfixturevalue`/`usefixtures` leg removed | planted pin | `1 failed, 12 passed` — PROOF HELD |
| c3 | `unused_tcp_port` wrongly classified SAFE | planted pin + ruled-reach pin | `2 failed, 10 passed` — PROOF HELD |
| c4 | static derivation blind to one plugin (anyio) | planted pin + safe dead-entry pin + live-session leg | `3 failed, 6 passed` — PROOF HELD |
| c5 | honest-developer plant in a REAL test-tree file (`def test_uvloop_is_not_installed(self, unused_tcp_port: int)`) | the live-tree invariant `TestNoRawListenerInAnyTestTree::test_no_test_tree_opens_a_listener_outside_the_helper` | `1 failed, 1 passed` — PROOF HELD |

c4's declared set was corrected ONCE before the run (predicted from the planted source: anyio's names on lines 4/11 go unflagged when anyio is not derived) — the driver file shows the final declaration; no run had happened when it was amended.

## Step 5 — verification (real tree = HEAD `3861050` + this working tree; in-scope files at HEAD are byte-identical to `ef0fcda`, `git diff --stat ef0fcda HEAD` over them is empty)

Brief's command — `uv run pytest -p no:xdist -q -p no:cacheprovider loremaster/tests/test_loopback_serving.py loremaster/tests/test_no_raw_listener_in_test_trees.py scripts/test_concurrent_wire_acceptance.py loremaster/tests/test_migration_wire.py`:
```
110 passed, 2 warnings in 167.21s (0:02:47)
exit=0
```
(94 at `ef0fcda` per the impl report + 13 pin-c + 3 pin-d = 110. The 2 warnings are uvicorn's websockets deprecation, pre-existing.)

`test_loopback_serving.py` ×5 (sequential, while a second lore pytest session was live):
```
run 1 exit=0 :: 41 passed, 2 warnings in 19.64s
run 2 exit=0 :: 41 passed, 2 warnings in 19.62s
run 3 exit=0 :: 41 passed, 2 warnings in 19.38s
run 4 exit=0 :: 41 passed, 2 warnings in 19.07s
run 5 exit=0 :: 41 passed, 2 warnings in 19.44s
```
Skills — `cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests`:
```
120 passed in 18.50s
```
ruff — `uv run ruff check` over the five #466 files: `All checks passed!`; `ruff format --check` over the three edited files: clean (my new hunks were formatted; HEAD's copy of `test_loopback_serving.py` was already format-clean, checked before formatting).

typecheck — `./scripts/typecheck.sh`: exit 1, **0 errors in any #466 file**; `skills`, `docs/eval`, shellcheck OK. The red is 44 errors in 19 OTHER packets' files (43 in `loremaster`, 1 in `scripts`): `test_findings_{enforcement,governance,identity,migrate,schema}_64b.py`, `test_governed_substrate_64b.py`, `test_reanchor_58_r2_{am2,probes,rulings,scale}.py`, `test_supersede_reanchor_58.py` (7, committed), `test_fixwave_a19a/a19b/a28_63c_i_a.py`, `test_blocks_edge.py`, `test_task_claimable_partition_58.py`, `test_task_guarded_shell_58.py`, `test_task_read_surface.py`, `scripts/test_forgery_door_sweep.py` — almost all uncommitted work in progress of packets 58/63c/64b in this shared checkout. Not mine to touch; surfaced.

## DRY ledger (brief-base §6)
⚠ **Deviation:** the lore search ran AFTER the symbols were written (it took >120 s and was backgrounded — filed as **finding #500**), so it could not inform the write; it returned only my own `_installed_plugin_fixtures` (+10 elided). In-file reuse was deliberate and is listed.

| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_installed_plugin_fixtures`, `_forbidden_plugin_fixtures`, `_is_installed_third_party` (guard) | "derive installed pytest plugin fixtures from pytest11 entry points, or check whether a file is inside site-packages" | only the new symbol itself (post-write) | HAND-ROLLED — no existing derivation; pytest has no public registry (private `getfixturemarker` / `_arg2fixturedefs` used, stated) |
| `_SAFE_PLUGIN_FIXTURES`, `_RULED_PORT_FIXTURES`, `_FIXTURE_LOOKUP_VERBS`, `_plugin_fixture_primitive`, `_SiteCollector._add` (guard) | same | — | EXTENDED `_SiteCollector` / `listener_sites` / `ListenerSite` in place (one detector; the existing invariant + exemptions + dead-entry pin cover the new leg) rather than a second guard |
| `_stuck_handler_class`, `_stick_a_request`, `STUCK_HANDLER_BOUND_S`, `STUCK_HANDLER_REQUEST`, `_STUCK_EXIT_WINDOW_LOW_S/HIGH_S` (serving tests) | same query (no stuck-handler helper exists in the file — read) | — | HAND-ROLLED test fixtures; REUSED `_BodyFailure`, `_StubHandler`, `_threads_still_alive_after`, `_becomes_refused`, `_get`, `SHUTDOWN_GIVE_UP_GRACE_S`, `THREAD_END_BOUND_S`, `HTTP_TIMEOUT_S` |

## Instruments (verbatim — brief-base §1)

### A — the R1 probe (interrupt during the teardown join leaks the capture handler)
```python
"""Probe: a BaseException landing in serve_asgi's TEARDOWN join (not the startup wait) — does the
uvicorn.error capture handler leak? Control: same run without the interrupt."""
import asyncio, logging, signal, threading, time, sys
from loremaster.testing.loopback import serve_asgi
import loremaster.testing.loopback as lb
print("loopback file:", lb.__file__)

class Stuck(BaseException): pass

def app_factory(gate):
    async def app(scope, receive, send):
        if scope["type"] == "lifespan":
            while True:
                m = await receive()
                if m["type"] == "lifespan.startup":
                    await send({"type": "lifespan.startup.complete"})
                else:
                    while not gate.is_set():
                        await asyncio.sleep(0.05)
                    await send({"type": "lifespan.shutdown.complete"}); return
    return app

def handlers():
    return list(logging.getLogger("uvicorn.error").handlers)

for inject in (False, True):
    gate = threading.Event()
    before = handlers()
    def _raise(*_): raise Stuck()
    signal.signal(signal.SIGALRM, _raise)
    try:
        with serve_asgi(app_factory(gate), shutdown_timeout_s=3.0):
            if inject:
                signal.setitimer(signal.ITIMER_REAL, 0.5)  # lands inside the 3 s teardown join
    except BaseException as e:
        print("inject=", inject, "raised", type(e).__name__)
    signal.setitimer(signal.ITIMER_REAL, 0)
    gate.set(); time.sleep(0.3)
    print("inject=", inject, "handlers before", len(before), "after", len(handlers()))
```
Output at `8738503` (loopback resolved to the real tree, printed by the probe):
```
inject= False raised ServerShutdownTimeout
inject= False handlers before 0 after 0
inject= True raised Stuck
inject= True handlers before 0 after 1
```

### B — the mutation-proof driver (declared RED sets fixed before the run; wraps `scripts/mutation_proof.py`)
```bash
#!/usr/bin/env bash
# Mutation proofs for lead pins (c) and (d), #466 d1 Phase 5. Declared RED sets are written HERE, before
# any run. Runs inside a scratch_copy.sh copy (provenance asserted); each proof restores its file by content.
set -uo pipefail
SCR="$1"; cd "$SCR" || exit 2
uv run python -c 'import loremaster, loremaster.testing.loopback as l; print("loremaster.__file__ =", loremaster.__file__); print("loopback.__file__   =", l.__file__)'
PYT=(uv run pytest -p no:xdist -p no:cacheprovider -q)
SERV=loremaster/tests/test_loopback_serving.py
GUARD=loremaster/tests/test_no_raw_listener_in_test_trees.py
LB=loremaster/loremaster/testing/loopback.py
ASGI_CLEAN="$SERV::TestAShutdownOverrunIsLoud::test_a_clean_exit_whose_shutdown_hangs_raises_naming_the_address"
ASGI_NOTE="$SERV::TestAShutdownOverrunIsLoud::test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note"
HTTP_CLEAN="$SERV::TestServeHttpShutdownOverrunIsLoud::test_a_clean_exit_with_a_stuck_handler_raises_naming_the_address"
HTTP_NOTE="$SERV::TestServeHttpShutdownOverrunIsLoud::test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note"
PF="$GUARD::TestPluginPortFixturesAreForbidden"
proof() { local name="$1"; shift; echo "=== $name"; uv run python scripts/mutation_proof.py "$@"; echo "=== $name exit=$?"; }

# d1: the SHARED policy's clean-exit raise → silent. Must redden BOTH helpers' clean-exit pins.
proof d1-shared-clean --file "$LB" \
  --anchor $'    if not stop(shutdown_timeout_s):\n        raise ServerShutdownTimeout(' \
  --replacement $'    if not stop(shutdown_timeout_s) and False:\n        raise ServerShutdownTimeout(' \
  --expect-red "$ASGI_CLEAN" --expect-red "$HTTP_CLEAN" \
  -- "${PYT[@]}" "$SERV" -k "ShutdownOverrunIsLoud"
# d2: the SHARED policy's note → dropped. Must redden BOTH helpers' failing-body pins.
proof d2-shared-note --file "$LB" \
  --anchor '            body_error.add_note(overrun)' --replacement '            pass' \
  --expect-red "$ASGI_NOTE" --expect-red "$HTTP_NOTE" \
  -- "${PYT[@]}" "$SERV" -k "ShutdownOverrunIsLoud"
# d3: serve_http's stop back to the OLD unbounded synchronous shutdown. Only the http pins redden.
proof d3-http-unbounded --file "$LB" \
  --anchor '    threading.Thread(target=server.shutdown, name=f"{thread.name} shutdown", daemon=True).start()' \
  --replacement '    server.shutdown()' \
  --expect-red "$HTTP_CLEAN" --expect-red "$HTTP_NOTE" \
  -- "${PYT[@]}" "$SERV" -k "ShutdownOverrunIsLoud"
# d4: serve_http bypasses the shared policy (a private, silent teardown). Only the http pins redden.
proof d4-http-bypasses-policy --file "$LB" \
  --anchor $'        with _loud_teardown(held.served_endpoint(), DEFAULT_SHUTDOWN_TIMEOUT_S, stop) as served:\n            yield served' \
  --replacement $'        try:\n            yield held.served_endpoint()\n        finally:\n            stop(DEFAULT_SHUTDOWN_TIMEOUT_S)' \
  --expect-red "$HTTP_CLEAN" --expect-red "$HTTP_NOTE" \
  -- "${PYT[@]}" "$SERV" -k "ShutdownOverrunIsLoud"

# c1: the detector's PARAMETER leg removed. Planted pin + every derived-name pin redden.
C1_RED=(--expect-red "$PF::test_every_planted_plugin_fixture_request_is_flagged_on_its_line")
for n in free_tcp_port free_tcp_port_factory free_udp_port free_udp_port_factory unused_tcp_port unused_tcp_port_factory unused_udp_port unused_udp_port_factory; do
  C1_RED+=(--expect-red "$PF::test_each_derived_forbidden_fixture_is_flagged_when_requested[$n]")
done
proof c1-no-parameter-leg --file "$GUARD" \
  --anchor '                if parameter.arg in self.forbidden_fixtures:' --replacement '                if False:' \
  "${C1_RED[@]}" -- "${PYT[@]}" "$GUARD" -k "PluginPortFixtures"
# c2: the detector's getfixturevalue/usefixtures leg removed. Only the planted pin reddens.
proof c2-no-lookup-leg --file "$GUARD" \
  --anchor '_FIXTURE_LOOKUP_VERBS = frozenset({"getfixturevalue", "usefixtures"})' \
  --replacement '_FIXTURE_LOOKUP_VERBS: frozenset[str] = frozenset()' \
  --expect-red "$PF::test_every_planted_plugin_fixture_request_is_flagged_on_its_line" \
  -- "${PYT[@]}" "$GUARD" -k "PluginPortFixtures"
# c3: a ruled port fixture wrongly classified SAFE. Planted pin + ruled-reach pin redden.
proof c3-port-fixture-classified-safe --file "$GUARD" \
  --anchor '    "worker_id": "pytest-xdist: this worker' \
  --replacement '    "unused_tcp_port": "WRONG",
    "worker_id": "pytest-xdist: this worker' \
  --expect-red "$PF::test_every_planted_plugin_fixture_request_is_flagged_on_its_line" \
  --expect-red "$PF::test_the_derivation_reaches_the_ruled_port_fixtures" \
  -- "${PYT[@]}" "$GUARD" -k "PluginPortFixtures"
# c4: the static derivation goes blind to one plugin (anyio). The live leg + the safe dead-entry pin redden.
proof c4-derivation-blind-to-anyio --file "$GUARD" \
  --anchor $'    for entry_point in metadata.entry_points(group="pytest11"):\n' \
  --replacement $'    for entry_point in metadata.entry_points(group="pytest11"):\n        if entry_point.name == "anyio":\n            continue\n' \
  --expect-red "$PF::test_every_planted_plugin_fixture_request_is_flagged_on_its_line" \
  --expect-red "$PF::test_every_safe_entry_is_still_a_defined_plugin_fixture" \
  --expect-red "$PF::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed" \
  -- "${PYT[@]}" "$GUARD" -k "PluginPortFixtures"
# c5: an honest-developer plant in a REAL test-tree file. The live-tree invariant reddens.
proof c5-live-tree-plant --file "$SERV" \
  --anchor '    def test_uvloop_is_not_installed(self) -> None:' \
  --replacement '    def test_uvloop_is_not_installed(self, unused_tcp_port: int) -> None:' \
  --expect-red "$GUARD::TestNoRawListenerInAnyTestTree::test_no_test_tree_opens_a_listener_outside_the_helper" \
  -- "${PYT[@]}" "$GUARD" -k "TestNoRawListenerInAnyTestTree"
```
Invocation: `bash mutation_proofs_466d1.sh <scratch copy>`; `driver exit=0`, 9/9 `PROOF HELD`.
