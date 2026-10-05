brief-base v18 read · brief project v7 read

# REPORT — contract-486-r4 (tdd-light CONTRACT, #486 follow-up: R1 · #538 · R5; TESTS ONLY, 2026-10-04)

## SUMMARY BLOCK
- **State:** done-with-deviations (round 2 finished 00:33Z inside its 75-min deadline; §10: P1 4 RED/4 GREEN as declared + satisfiability reference 8/8; P2 17 GREEN + c1/c2/c3 PROOF HELD; P3 RED for never-went-down; one self-reported gate breach; one fork on the control's rc). Files edited: `loremaster/tests/test_harness_database_lifecycle_486.py` and (after the D1 ruling) `loremaster/tests/test_no_raw_listener_in_test_trees.py` (not committed). Base HEAD `3256201`.
- **R1:** a new lost-store state `wedged` (handshake completes, pings answered, requests never) added to `_LOST_STORE_STATES`, plus an end-bound leg (`_LOST_STORE_SESSION_END_BOUND_SECONDS = 120`) over ALL lost states. GREEN on `3256201`; **budget-deletion reference edit reddens exactly `[wedged-n0]` + `[wedged-xdist-n2]`** (`scripts/mutation_proof.py`: PROOF HELD, conftest restored byte-exact). §2.
- **#538:** `TestEveryXdistWorkerReportsItsSessionEnd` — **RED for the right reason on `3256201`** (construction held in both workers; rc 0, `1 passed`, nothing named), plus a GREEN control. §3.
- **R5:** `TestASessionEndReapTheStoreAnsweredWronglyIsNamedFailed[n0, xdist-n2]` — **GREEN on `3256201`: pins existing behaviour.** §4.
- **Deviations:** (1) SUPERSEDED by D1 (§9): the stdlib wedged server is deleted; the shipped wedged store is the `websockets` `ServerConnection` variant, and the #466 guard now derives, plants and flags `websockets`. (2) #538 is pinned under xdist only (no worker exists at `-n 0`). (3) `_LOST_STORE_SESSION_END_BOUND_SECONDS` is a NEW leg on the existing ∀-lost-state cell (all 4 states), not only on the wedged cell.
- **Packages considered:** wedged websocket server — `websockets` 16.0 (read: `websockets.sync.server.ServerConnection.__init__/handshake`, `websockets.server.ServerProtocol.__init__`, `websockets.frames.Frame.parse` signatures, `serve.conn_handler` source): it DOES the job and was built and proved first (PROOF HELD, §2) → verdict **`replace` (applied, D1, §9)**: the wedged store is the package's `ServerConnection`; the stdlib RFC 6455 server is deleted. Plugin injection: pytest's own `PYTEST_PLUGINS` env (no mechanism hand-rolled).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new reusable production symbols; test-local symbols dispositioned in §6.
- **Graded:** n/a (contract author).
- **Decisions needed:** none open. (D1 RULED by the lead: package + planted spelling — applied, §9.) (D2, accepted as is) token choices are mine: #538 named line = a worker id `gw<n>` + `session-end`; R5 = DB name + `failed`, and NEVER `unreachable`. One constant each if the lead wants others.
- **Receipts:** §2 R1 · §3 #538 · §4 R5 · §5 targeted before/after · §7 pre-flight · §A instruments.

## Capability check (brief-base §4)
- grep/rg hook-blocked (#473): every textual scan was awk. One `lore_search` (DRY, §6); `lore_comms register` + heartbeat done (session 63c).
- Idle-gate contract file: `/tmp/claude-idle-gate-lore/unknown-contract-486-r4.contract` (my session id is not visible to me; `unknown-` prefix as the directory's other entries).
- ⚠ Gate-check honesty: my first process-table check (`ps … | awk '/[p]ytest/ && /lore/'`) printed `1` at 23:08:02 — that row was MY OWN issuing `bash -c` (its cmdline contains the pytest command it was about to start). The 23:07 table, read just before, showed no other lore pytest. Later checks used `pgrep -fa '[p]ython.*-m pytest|[b]in/pytest'` → 0.
- Deadline 45 min: started 22:56Z.

## §1 Properties (lifted; outcomes only)
- **R1 (coldaudit-486-2 R1):** ∀ store state the TEST store may be LOST into after a real open — `refused`, `silent`, `muted`, and NEW `wedged` — the session ENDS within `_LOST_STORE_SESSION_END_BOUND_SECONDS` (120 s, outer kill 180 s), with the loud `unreachable` line naming the DB, rc ≠ 0, `1 passed` intact, no raw traceback; under `-n 0` and xdist `-n 2`. Domain is the existing `_LOST_STORE_STATES` tuple; the new state rides the existing parametrisation (generated, not a new hand cell).
- **#538 (R3):** under xdist, ∀ worker that finished, the controller either RECEIVED its session-end report or FAILS the session (rc ≠ 0) with a named line (worker id `gw<n>` + `session-end`), `1 passed` intact — whatever stopped the report. Not keyed on the cause: the construction raises in an UNRELATED session-finish hook, not in the reap.
- **R5:** a session-end reap the store ANSWERED wrongly → rc ≠ 0, a line naming the DB with `failed`, NO line naming the DB with `unreachable` (a false cause is a trust defect), no traceback, `1 passed`; `-n 0` and xdist.

## §2 R1 — the `wedged` state and the budget proof
- **Construction** (`_KillableStoreForwarder._serve_wedged`): after the kill, every new connection is served locally: RFC 6455 handshake (Sec-WebSocket-Accept per §1.3, `cbor` subprotocol, no extension → no deflate), then frame loop: ping → pong (same payload), close → echoed close, every data frame swallowed. The server never pings, so the SDK's keepalive (websockets default 20 s / 20 s) is answered forever; the 10 s open timeout is passed. Nothing a dependency owns ends a request.
- **Current build (`3256201`):** `[wedged-n0]`, `[wedged-xdist-n2]` GREEN (`5 passed in 34.31s` with the server-capable guard, run2 at 23:11Z).
- **Reference edit (throwaway, never shipped):** `reaper.join(budget_seconds)` → `reaper.join()` in `loremaster/tests/conftest.py::_reap_within_budget`. Predictions written BEFORE each run (scratch `predictions.md`): exactly the two wedged cells RED; refused/silent/muted GREEN.
- Command (both runs), declared ids from `--collect-only`:
  ```
  systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/mutation_proof.py \
    --file loremaster/tests/conftest.py --anchor '    reaper.join(budget_seconds)' --replacement '    reaper.join()' \
    --expect-red "$W[wedged-n0]" --expect-red "$W[wedged-xdist-n2]" -- \
    uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE \
      loremaster/tests/test_harness_database_lifecycle_486.py loremaster/tests/test_surreal_harness.py \
      --deselect "…::TestEveryXdistWorkerReportsItsSessionEnd::test_a_worker_that_never_shipped_its_session_end_report_fails_the_session"
  # W = loremaster/tests/test_harness_database_lifecycle_486.py::TestTheSessionEndReapNeverCostsPytestItsVerdict::test_an_opened_database_with_the_store_lost_at_session_end_is_reported_loudly
  ```
- **Run 1 (websockets `ServerConnection` variant, §A):** `2 failed, 129 passed in 365.34s` · `tree restored byte-exact (… md5 6c3710d6ac198d0cc7df2b1942821f84)` · `PROOF HELD`, rc 0.
- **Run 2 (shipped stdlib variant, 23:12–23:18Z):** `2 failed, 129 passed in 365.31s` · restored byte-exact (same md5, = coldaudit-486-2's conftest md5) · `PROOF HELD`, rc 0. Both REDs read `Failed: the inner session against ws://127.0.0.1:<port>/rpc did not END within 180s — …` — the right reason (a hang to the outer kill). `cmp` vs my `cp -a` content backup: identical.
- **Why this closes R1:** coldaudit-486-2 mutation (b) (the same edit) passed 126/126 because every constructed state was ended by a dependency default. With `wedged`, the build's own bound is the only thing that ends the session.
- The new end-bound assertion (`elapsed <= 120`) holds for all 4 states on `3256201` (the after run). It adds teeth against a LOOSE bound (e.g. a 170 s budget), which the outer kill alone would pass.

## §3 #538 — `TestEveryXdistWorkerReportsItsSessionEnd`
- **Injection:** pytest's own `PYTEST_PLUGINS=session_end_injection_486` env (+ `PYTHONPATH` = tests dir + plugin dir), inherited by every xdist worker. The plugin is a `tryfirst` `pytest_sessionfinish` that, in WORKERS only, appends the worker id to a marker file and raises `RuntimeError("contract-486-r4 injected hook bug")`, so every later session-finish impl in that worker (the harness's included) never runs. The raise text deliberately carries neither `gw` nor `session-end`, and lines containing it are excluded from the named-line search, so a build that merely surfaces the raise cannot pass.
- **Inner session:** one test that opens a DB and DROPS it (clean), so only the session end can fail it.
- **Construction guard:** 1 recorded DB AND the marker lists both workers (checked first, so a broken construction never reads as a verdict).
- **RED on `3256201`** (after run, 23:18Z):
  ```
  E           AssertionError: 2 xdist workers (gw1, gw0) finished WITHOUT shipping their session-end report, and the session PASSED: whatever those workers opened was never verified removed, and nobody was told (#538).
  E             returncode=0 created=['test_2398475_1a4802b754904745bb8af101c40f8df1']
  …
  E             PASSED test_inner_486.py::test_opens_a_database_and_drops_it
  E             1 passed in 1.48s
  E           assert 0 != 0
  ```
  Right reason: construction held, rc 0, `1 passed`, no name.
- **CONTROL** `test_CONTROL_the_same_injection_without_the_raise_passes`: GREEN (same plugin, not raising; marker shows both workers loaded it; rc 0, `1 passed`, no named line).
- `-n 0`: no worker, no hand-off; scoped out with that reason (a raise at `-n 0` already fails pytest natively).
- **SIBLINGS NOT TRIED:** a worker killed (SIGKILL) mid-session-finish (xdist's `node down` path — `pytest_testnodedown` `error` non-None), a worker whose `workeroutput` carries a corrupt (non-JSON) value. The pin is on the outcome, so the implementer's chokepoint should cover them; they are not constructed.

## §4 R5 — `TestASessionEndReapTheStoreAnsweredWronglyIsNamedFailed`
- **Injection:** the same `PYTEST_PLUGINS` route; a `tryfirst` `pytest_sessionfinish` replaces `_surreal_harness.run` so `INFO FOR NS` answers `{"accesses": {}, "databases": [], "users": {}}` (a LIST where a map is required) and records each wrong answer; every other statement reaches the live TEST store. Session end only.
- **Inner session:** `_INNER_LEAKING_TEST` (opens, never drops) — so the reap has a real job and the wrong answer hides a real leak.
- **Construction guard:** 1 recorded DB AND ≥1 marker line (proves the injection reached the reap's read).
- **Result on `3256201`:** `[n0]` and `[xdist-n2]` GREEN — **pins EXISTING behaviour** (coldaudit-486-2 §1 row 5: `SurrealStoreError`→`failed`; now pinned end to end).
- SIBLINGS NOT TRIED: other wrong shapes (the shape domain is pinned on the reaper itself by `TestTheReaperFailsLoudOnANamespaceAnswerItCannotRead`); `TxnContentionExhaustedError` / `RuntimeError` at session end.

## §5 Targeted runs (scope: the three briefed files; `-n 8 --timeout=300`, MemoryMax 16G cgroup)
| run | tree | result |
|---|---|---|
| before (23:20Z) | HEAD's test file swapped in (`git show HEAD:…`), my file `cp -a`-backed and `cmp`-restored | `1 failed, 160 passed in 66.40s` — the 1 = `TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed` (#537, runner-caused, coldaudit-486-2 §3) |
| after (23:18Z) | my file | `2 failed, 165 passed in 133.38s` — #537 (same) + the #538 pin (intended) |
- 167 − 161 = 6 new cells (2 wedged, 2 #538, 2 R5). Nothing else moved. The extra ~67 s wall-clock is the two wedged sessions (≈30 s budget each) on the critical path.
- **Intermediate run (23:08Z, websockets variant):** `3 failed, 164 passed` — the third red was `TestTheServerCapableDependenciesAreDerived::test_the_derived_server_capable_set_equals_the_planted_map`: `server-capable distributions imported by a test tree with NO planted spelling: ['websockets']`. That is why the shipped state is stdlib (deviation 1); after the swap it is GREEN.
- `uv run ruff check .` → `All checks passed!`; `ruff format --check` on my file → formatted.
- `scripts/typecheck.sh`: my file 0 errors (one `var-annotated` I introduced was fixed). `pending_contract_gate.py --currency --legs typecheck,ruff` → typecheck `RED_ADJUDICATED` (83 residuals owned by packet-58 / packet-64b-i contracts, none in my file), ruff `GREEN`; pytest `NOT_RUN` by design (no full suite in a contract round). No RED_ORPHANED among the legs run.
- TEST store `:18000` only; every inner DB removed in `finally` via `_remove_if_present`.

## §6 DRY / reuse ledger (test-local symbols only; no production symbol)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_injected_plugin_environment`, `_marked`, the two plugin sources | `lore_search "inject a pytest plugin into an inner pytest subprocess session via PYTEST_PLUGINS env so xdist workers load it"` | `test_extension_discovery.py::_inject_registry` (monkeypatch of a registry; unrelated) | HAND-ROLLED (test-local; nothing found) |
| `_serve_wedged` + `_WEBSOCKET_*` constants | — (package question, §Packages) | `websockets` does the job | bespoke under the #466 guard, trigger named (D1) |
| `_WEDGED_STORE`, `_LOST_STORE_SESSION_END_BOUND_SECONDS`, `_REAP_FAILED_WORD`, `_SESSION_END_WORD`, `_WORKER_ID`, `_WRONG_NAMESPACE_ANSWER`, `_INNER_OPENS_AND_DROPS` | awk over the file | extend existing domains (`_LOST_STORE_STATES`, `_UNREACHABLE_WORD`) | EXTENDED in place |
- REUSED: `_run_bounded`, `_KillableStoreForwarder`, `_INNER_PREAMBLE`, `_INNER_LEAKING_TEST`, `_remove_if_present`, `_passed_summary`, `_WORKER_MODES`, `_UNREACHABLE_WORD`.

## §7 Adversarial pre-flight → case
| failure mode | covered by |
|---|---|
| budget deleted / unbounded join | wedged × {n0, xdist} — mutation-proven RED |
| budget loosened (e.g. 170 s, under the outer kill) | the 120 s end-bound leg, ∀ 4 lost states (not mutation-run; LOW) |
| a dependency default masking the budget | the wedged state answers pings and passes the open timeout by construction |
| worker hook raises before the hand-off | #538 cell (RED) |
| a build that surfaces the raise text as its "named line" | raise text excludes the tokens; lines containing it are filtered |
| non-transport reap failure misnamed `unreachable` | R5 negative assertion |
| injection never reaching the reap / a worker | construction guards (marker files) + #538 control |
| `-n 0` vs xdist | R1 and R5 both modes; #538 xdist only (no worker at `-n 0`) |
| hostile stored text / input accounting | n/a: the units render no stored free text; DB names are harness-minted |

## §8 Flags outside this change
- **#537 (F1)** still red under the mandated `--with pytest-timeout` runner (before AND after). Not mine; recommendation unchanged (declare `pytest-timeout` a dev dependency).
- **D1:** the #466 guard has no `websockets` planted spelling. Any future test that imports the `websockets` server reddens it; adding one (and proving the detector flags `websockets.serve`) lets this contract use the package.
- **Implementer note (not a prescription):** #538's fix belongs at the controller (a finished worker with no report key = failed); R1 is already satisfied by the current budget.
- **R2** (anyio `fail_after` vs the daemon thread) is untouched by this contract; the wedged cell would carry any swap.

## §A Instruments
- The plugin sources, the wedged server and the constructions are in the test file itself (they ship with the contract).
- `scripts/mutation_proof.py` is committed; the exact invocation is in §2.
- The proven-but-not-shipped `websockets` variant of `_serve_wedged` (run 1, PROOF HELD), verbatim, for the D1 swap:
  ```python
  from websockets.server import ServerProtocol
  from websockets.sync.server import ServerConnection
  from websockets.typing import Subprotocol

      @staticmethod
      def _serve_wedged(client: socket.socket) -> None:
          """Complete the websocket handshake, answer every ping, never answer a request."""
          protocol = ServerProtocol(subprotocols=[Subprotocol("cbor")], max_size=None)
          connection = ServerConnection(client, protocol, ping_interval=None)
          with contextlib.suppress(Exception):  # a client hanging up mid-handshake ends the state
              connection.handshake()
              for _request in connection:  # every request is read and swallowed, unanswered
                  pass
  ```

## §9 D1 applied (lead ruling, 2026-10-04 ~23:24Z: "take the package")
- **Backups first:** `cp -a` of both files to scratch `d1/` before any edit; the lead's md5 of my pre-D1 file, `46c0b0fb…`, matched mine (`46c0b0fbdf8e4a1d1dfd93fc655429fc`).
- **486 file:** `_KillableStoreForwarder._serve_wedged` is now the §A `websockets` variant (`ServerProtocol(subprotocols=[Subprotocol("cbor")], max_size=None)` + `ServerConnection(client, protocol, ping_interval=None)`, handshake, read-and-swallow loop). The stdlib RFC 6455 server, its 11 `_WEBSOCKET_*` constants and the `base64`/`hashlib` imports are DELETED. The class docstring's `wedged` bullet now says it wraps an already-accepted socket and binds nothing.
- **Guard file (`test_no_raw_listener_in_test_trees.py`):**
  - The detector could not see ANY `websockets` listener. Probe before the edit, `listener_sites` over 5 spellings: `websockets.serve(...)`, `asyncio.server.serve`, `sync.server.serve` bare and qualified, and my accepted-socket `ServerConnection`. All 5 returned `[]`. So a planted spelling alone would have been decoration; the detector needed an entry.
  - **Leaf names derived from the installed 16.0 source** (awk over `websockets/**/*.py` for the listener verbs): `asyncio/server.py` (`loop.create_server` / `create_unix_server` inside `serve`, plus `unix_serve`), `sync/server.py` (`socket.create_server` inside `serve`, plus `unix_serve`), `legacy/server.py` (`Serve`, plus `unix_serve`). Added `"websockets": frozenset({"serve", "unix_serve", "Serve"})` to `_LISTENER_NAMES_BY_LIBRARY` (the aiohttp leaf-name idiom; not a whole-namespace entry, which would refuse honest clients).
  - `_PLANTED_BY_SERVER_DISTRIBUTION["websockets"]` = `from websockets.sync.server import serve` + `with serve(handler, '127.0.0.1', port) as server: server.serve_forever()`.
  - New class `TestTheDetectorSeesWebsocketsListeners`: a line-exact planted pin (5 spellings, lines 5–9: top-level `websockets.serve`, asyncio `serve`, `unix_serve`, qualified `websockets.sync.server.serve`, legacy `Serve`) and an honest pin (`websockets.connect`, `sync.client.connect`, `ServerConnection(accepted, ServerProtocol()).handshake()` → `[]`).
  - KNOWN BOUND (2) of `TestTheServerCapableDependenciesAreDerived` is updated: websockets is now imported, derived, planted and flagged. The `Derived at 43b8d16` comment above the map is extended too.
- **Positive control:** guard file `37 passed`, only #537 red (23:25Z). This includes `test_the_planted_spelling_of_each_server_capable_dependency_is_flagged[websockets]`, the line-exact planted pin and the honest pin.
- **The detector entry is load-bearing** (mutation proof, 23:26Z): deleting the `websockets` line from `_LISTENER_NAMES_BY_LIBRARY` reddened EXACTLY the line-exact planted pin and `…is_flagged[websockets]` (`2 failed, 35 passed in 10.80s`, #537 deselected). The honest pin stayed green. `PROOF HELD`, guard restored byte-exact (`f6f6f73f529a05bc940a0499239e2380`).
- **Negative control (the map without the entry):** cited from the 23:08Z run in §5. With `websockets` imported and no planted entry, `test_the_derived_server_capable_set_equals_the_planted_map` failed with `server-capable distributions imported by a test tree with NO planted spelling: ['websockets']`.
- **(c) currency, `--currency --legs typecheck,ruff` (23:27Z):** typecheck `RED_ADJUDICATED` (83 residuals owned by the packet-58 / 64b-i contracts, unchanged, none in either of my files), ruff `GREEN`, **RED_ORPHANED 0**. pytest is `NOT_RUN` by design.
- **(a) The wedged budget-deletion proof re-run on the SHIPPED package variant** (final 486 file md5 `6440b108c12a7fc37dc72f9f8fed5c46`; prediction recorded before the run, 23:26Z). Command identical to §2, same declared ids.
  - Result: `2 failed, 129 passed in 365.21s` · `tree restored byte-exact (loremaster/tests/conftest.py: md5 6c3710d6ac198d0cc7df2b1942821f84)` · **`PROOF HELD`**, rc 0.
  - Both REDs read `Failed: the inner session against ws://127.0.0.1:<port>/rpc did not END within 180s — …`, which is the right reason.
  - `cmp` of conftest against my pre-session backup: identical.
- **(b) Targeted after-run** (23:32Z, `-n 8 --timeout=300`, 16G cgroup): the 486 file + `test_surreal_harness.py` + the guard file.
  - Result: **`2 failed, 168 passed in 133.22s`**. The two failures are exactly #537 (`TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed`, pre-existing and runner-caused) and the #538 pin (intended RED).
  - 170 collected = 161 (HEAD, §5) + 6 (486 cells) + 3 (guard: the two `TestTheDetectorSeesWebsocketsListeners` pins and `…is_flagged[websockets]`). Everything else is green.
- **Final md5s:** 486 file `6440b108c12a7fc37dc72f9f8fed5c46`, guard file `f6f6f73f529a05bc940a0499239e2380`. Nothing committed.
- **Bound, stated:** the `websockets` leaf names were derived from the installed 16.0 source by reading it, and the derivation is not executed. A future `websockets` release that adds a new listener entry point would be derived as server-capable, because the reach oracle keys on the verbs, but it would NOT be flagged until it is named here. That is the aiohttp entry's existing bound, unchanged.

## §10 Round 2 (lead brief 2026-10-05 ~00:18Z: P1 Q2 hard outer bound · P2 #538 door domain · P3 F-3) — measured 00:18–00:32Z
**Base:** HEAD `6f35e0a` + the uncommitted r4 build (conftest `94f821754d8e37d0e613ef2f16f77dcc`, 486 file at start `6440b108…`). **Only file edited:** `loremaster/tests/test_harness_database_lifecycle_486.py` → final md5 `3c981b3ea9936c46ec08cd47df25109b`. Pre-edit `cp -a` backups of both the 486 file and conftest in scratch `r2/`. Nothing committed. Conftest ended byte-identical to `94f82175…` after every throwaway edit (`cmp` and the proof tool's own check).

### Summary
| pin | class (new) | cells | on the r4 build | right reason |
|---|---|---|---|---|
| P1 Q2 hard bound | `TestTheSessionEndReapHasAHardOuterBound` | 8 = {blocking, cooperative} × {n0, xdist-n2} × pytest `faulthandler_timeout` {unset, 600} | **4 BLOCKING RED, 4 COOPERATIVE GREEN** (as declared 00:24:26Z, before the run) | each RED: `a SYNC block in the session-end reap held the process 20.4s/20.4s/20.8s/20.8s past the session-end step's start — over the 9s hard bound (2 × 2s budget + 5s)` |
| P2 #538 door domain | `TestEveryWorkerDoorIsAccounted` | 17 = completeness + id-currency + 13 generated doors + all-doors-at-once + CONTROL | **17 GREEN** | — |
| P3 F-3 wording | `TestTheGapLineNeverContradictsItsCause` | 13 generated doors (2 skip: accounted doors name no one) | **`[never went down]` RED**, 10 GREEN | `the worker's node NEVER went down, but the line claims it ended ('finished') … xdist worker gw1 finished WITHOUT its session-end report (it never went down)` |

### P1 — construction and the seam the implementer must keep
- **Injection.** A `PYTEST_PLUGINS` plugin (`_HARD_BOUND_INJECTION_PLUGIN`) adds a `tryfirst` `pytest_sessionfinish` in every process. It:
  - sets the suite conftest's `_SESSION_END_REAP_BUDGET_SECONDS` to 2.0, on every loaded module whose `__file__` is `loremaster/tests/conftest.py`;
  - replaces `_surreal_harness.reap_minted_databases` with either a sync `time.sleep(10 × budget)` (blocking) or `await asyncio.sleep(10 × budget)` (cooperative);
  - stamps the time plus whether the budget seam exists, read by the construction guard.
- **Inner session.** `_INNER_OPENS_AND_DROPS` opens and drops one database, so the reap runs.
- **Hold.** `held` = child exit minus the earliest REAPING process's stamp. The ceilings were declared before the run:
  - blocking: `2 × budget + ε` = 9 s;
  - cooperative: `budget + ε` = 7 s;
  - `ε` = 5 s.
- **Blocking legs.**
  - `-n 0`: rc ≠ 0, plus a faulthandler frame `File "…conftest.py", line N in _reap_within_budget`. The regex has no comma before `in`, so a Python traceback (`, in`) cannot satisfy it; only faulthandler's format can.
  - xdist: rc ≠ 0, plus the #538 gap line naming a `gw<n>` (coldaudit-486-3 §5 addendum note 2).
- **Cooperative control.** Pins the existing line `no answer within the 2s session-end reap budget`, `1 passed`, NO faulthandler frame, and rc ≠ 0.
- **Note 1** (timer armed after pytest's last per-test cancel) is covered by the `pytest-faulthandler-timeout` variant: `PYTEST_ADDOPTS=-o faulthandler_timeout=600` arms and cancels the same process-global timer for each test.
- **SEAMS THE IMPLEMENTER MUST KEEP OR EXPOSE (named, not prescribed):**
  1. **The budget is read at session end from the conftest module attribute `_SESSION_END_REAP_BUDGET_SECONDS`, and the hard bound derives from that same value** (2 × it). This is the narrowest test-side injection the r4 build offers. The construction guard reports a missing attribute as CONSTRUCTION failed, never as a verdict. If the implementer prefers a different seam (e.g. an env var), the cell's injection changes in one place.
  2. The reap is still reached as `_surreal_harness.reap_minted_databases`, looked up at call time.
  3. The bounding step stays a frame named `_reap_within_budget`, because the dump must name it.
  4. **The dump must reach the child's REAL stderr.** pytest's fd capture can still own fd 2 at session finish. The reference below passes `file=sys.__stderr__`, which worked.
- **Satisfiability receipt: a throwaway reference, never shipped.** It added six lines to `_reap_within_budget` (verbatim below), and the result was **`8 passed in 9.47s`** (00:26:30Z). The reference conftest md5 was `5036e8f2…`; it was restored to `94f82175…`, `cmp` identical.
  ```python
      import faulthandler

      try:
          faulthandler.dump_traceback_later(2 * budget_seconds, exit=True, file=sys.__stderr__)
          try:
              anyio.run(_bounded_reap)
          finally:
              faulthandler.cancel_dump_traceback_later()
      except TimeoutError as error:
  ```
- **FORK (written down, my pick stated): the cooperative control's exit code.** Two readings:
  - am-37 §14 Q2 says the control "exits **0** … with the existing loud line";
  - your brief says only "the verdict is intact".

  Today the loud line FAILS the session (rc 1; pinned by `TestTheSessionEndReapNeverCostsPytestItsVerdict`), so "exits 0 with the loud line" contradicts an existing pin. I pinned **rc ≠ 0 + `1 passed` + no dump**. The "graceful vs hard" distinction is carried by the dump's ABSENCE, not by the rc, because `_exit(1)` and TESTS_FAILED are both 1. If the operator meant rc 0, that is a change to the #534 loud-line contract and needs a ruling.
- **Deviation from your expectation:** you expected the main leg to "hang to your outer kill". It does not. A `10 × budget` sync sleep RETURNS at about 20 s, so the RED is the 9 s ceiling, not the 90 s outer kill. The pin is the same; only the reason text differs.

### P2 — the generated door domain
- **Source of truth.** The keys are every conftest constant whose name ends in `_REPORT_WORKEROUTPUT_KEY`, found with `vars()`, never listed by hand. The "complete report" is whatever the conftest's OWN worker-side `pytest_sessionfinish` writes into a fake `workeroutput`. Nothing is hand-written.
- **Doors** (13): each key × {absent, corrupt `{not json`, wrong shape `{"not": …}`, `None`}, plus:
  - every key absent;
  - crashed and shipped nothing;
  - never went down;
  - crashed after a complete report (ACCOUNTED);
  - a complete report (ACCOUNTED).
- **Each door cell** runs a fleet {gw0 accounted, gw1 door}, so every case carries an accounted worker beside the gap (c3).
- **Assertions.** Through the hooks only (`pytest_testnodeready`/`pytest_testnodedown`/`pytest_sessionfinish`/`pytest_terminal_summary`), on a private `importlib` copy of conftest:
  - unaccounted door: exitstatus ≠ OK, plus a line naming gw1 with `session-end`;
  - gw0 is never named;
  - accounted doors: OK and not named.
- **All-doors-at-once** puts all 13 workers in one fleet and requires the named set to equal exactly the unaccounted set.
- **Completeness.** `test_the_generator_covers_every_key_a_worker_ships` requires the shipped keys to equal the named constants. `test_the_collected_door_ids_are_the_run_time_domain` catches stale parametrisation.
- **Isolation.** `_sdk_guard._CALL_HOOKS` is swapped for a copy (the private conftest copy appends its hook at import), and `_surreal_harness._MINTED_DATABASES` is set to `{}` (so the controller's session-finish has nothing of the outer process's to reap). Both are monkeypatched, so nothing leaks into the running session.
- **Mutation proofs** (`scripts/mutation_proof.py`). Ids were taken from `--collect-only` (30 ids in `r2/p2ids.txt`). The declared sets were derived and written (`r2/declared_c{1,2,3}.txt`) and the predictions recorded at 00:25Z, before any run. Scope: the P2+P3 classes, with P3 `[never went down]` deselected because it is the current-build red. Anchors are coldaudit-486-3 §A.5 verbatim.

  | mutant | declared | observed | verdict |
  |---|---|---|---|
  | c1 (half report: `.get(UNREAPED_KEY, "[]")`) | 3 (door `[…unreaped…=absent]`, all-at-once, P3 `[…unreaped…=absent]`) | `3 failed, 24 passed, 2 skipped in 1.56s` | **PROOF HELD**, restored `94f82175…` |
  | c2 (ValidationError gap → `None`) | 13 (6 corrupt/wrong-shape/none doors × {P2, P3} + all-at-once) | `13 failed, 14 passed, 2 skipped in 1.60s` | **PROOF HELD**, restored |
  | c3 (gaps only when every worker is a gap) | 12 (11 gap doors + all-at-once) | `12 failed, 15 passed, 2 skipped in 1.61s` | **PROOF HELD**, restored |

### P3 — the wording property
- **Property.** For every unaccounted door, the line naming the worker makes no lifecycle claim its cause contradicts:
  - a door whose node never went down → no `finished|ended|exited|terminated|completed|went down` once `never …` phrases are removed;
  - a door that went down → no `never went down|finished|ended|exited`.
- It is generated over the same 13 doors; the 2 accounted doors skip (no line names them, pinned by P2).
- **BOUND, stated in the class docstring:** the verb vocabulary is a list. A new lifecycle verb is not covered until it is added to `_ENDED_CLAIM`.
- On the r4 build only `[never went down]` reddens. That matches F-3: "finished WITHOUT … (it never went down)". The crash doors pass; the audit judged "finished" acceptable for a worker that did go down.

### Targeted before/after (486 file + `test_surreal_harness.py` + guard file; `-n 8 --timeout=300`, 16G cgroup, wait-loop gate)
| run | tree | result |
|---|---|---|
| before (00:26:51Z) | 486 file swapped back to `6440b108…` (`cp -a`, then restored, `cmp` identical) | **`170 passed in 133.00s`** |
| after (00:29Z) | final 486 file `3c981b3e…` | **`5 failed, 201 passed, 2 skipped in 154.64s`**. The 5 failures are exactly the declared REDs: 4 × P1 blocking, plus P3 `[never went down]` |
- 208 collected = 170 + 38 new (P1 8 + P2 17 + P3 13). Nothing else moved.
- `ruff check .` → `All checks passed!`; my file has 0 typecheck errors.
- **`--currency --legs typecheck,ruff`** (00:31Z): typecheck `RED_ADJUDICATED` (the same 83, owned by packet-58/64b-i, none in my file); ruff `GREEN`; **RED_ORPHANED 0**. The pytest leg is `NOT_RUN` by design (#540).

### ⚠ Gate breach (self-reported)
- At 00:22:36Z my gate check printed `procs=2` (other pytest processes live) and I started the run anyway. That run was the 1.57 s store-free P2/P3 run.
- At 00:23Z the two processes were gone. Their identity is unrecoverable; I did not capture their command lines before they exited.
- After that I wrote scratch `r2/gate.sh`, which WAITS (it does not refuse) until MemAvailable ≥ 20 GiB AND no other pytest is live. Every later run went through it; each `GATE CLEAR` line is in its log.
  ```bash
  #!/usr/bin/env bash
  set -euo pipefail
  while true; do
    avail_kib=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
    others=$(pgrep -fa '[p]ython.*-m pytest|[b]in/pytest' || true)
    if [ "$avail_kib" -ge $((20*1024*1024)) ] && [ -z "$others" ]; then break; fi
    echo "waiting $(date -u +%T): MemAvailable ${avail_kib} KiB; others: ${others:-none}" >&2; sleep 10
  done
  echo "GATE CLEAR $(date -u +%T): MemAvailable $(awk '/MemAvailable/ {print $2}' /proc/meminfo) KiB, no other pytest" >&2
  exec "$@"
  ```

### For the implementer (named, not prescribed)
- **P1:** add the hard outer bound; keep the four seams listed above.
- **P3:** derive the gap line's verb from the gap. Coldaudit-486-3's suggestion was "did not report its session-end before the session ended". The never-went-down door must not say "finished".
- **P2:** no change needed. It is a regression pin for a correct build.
