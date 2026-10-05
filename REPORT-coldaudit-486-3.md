brief-base v18 read · brief project v7 read

# REPORT — coldaudit-486-3 (cold REFUTE audit, #486 follow-up round r4: R1 · R2 · #538 · R5 · #537; 2026-10-04/05)

## SUMMARY BLOCK
- **State:** done. **Verdict: GO-with-residuals.** The build is correct on every requirement. R1, R2, #538 (the constructed door), R5 and #537 all hold, with no regression. One MEDIUM residual: #538's pin covers one point of its domain (F-1).
- **Mutations (mine, §2):** (a) `fail_after(None)`, (a2) loose 150 s budget, (b) a missing report swallowed at the chokepoint, (d) the `websockets` entry deleted, (e) a `shield=True` reap: **all PROOF HELD**, each reddening exactly its declared set. **(c1) half report, (c2) corrupt value, (c3) partial fleet: all SURVIVE the whole 486 file (59/59).** The build is right on all three (§A.2 probe), so this is a missing regression pin, not a live defect.
- **Construction (§1):** wedged answers pings and withholds replies (probe + `muted` control). The #538 injection blocks both workers' reports, and xdist prints nothing. The R5 injection reaches the reap's `INFO FOR NS`.
- **#537/F1 (§3):** GREEN under plain, `--with pytest-timeout -n 8` and `-n 0`. RED in the HEAD-pyproject negative control.
- **Census (§4):** 936 collected on both sides; before `2 failed, 932 passed, 2 skipped` (F1 + #538) → after `934 passed, 2 skipped`; 0 GREEN→RED.
- **Gates (§5b):** typecheck RED_ADJUDICATED (83, owned, 0 in the audited files), ruff GREEN, **RED_ORPHANED 0**. The FAIL render is friction #540.
- **Judgment (§5):** F-a: the wedged cells already pin the store-waiting non-cancellable doors ((e) measured). The operator's Q2 hard outer bound covers the rest. Row 4: accept.
- **Trust (§6):** no false cause and no false clear. Two LOW wording issues: F-2 (the raised-hook cause is invisible; the implementer's "xdist already prints that" is false there) and F-3 ("finished" vs the gap "it never went down").
- **Deviations:** none. (HEAD moved docs-only during the audit, see `Graded:`.)
- **Packages considered:** none — no mechanism specified (audit). I READ, to judge others' verdicts: anyio 4.13.0 `AsyncIOBackend.run` → `asyncio.Runner`; `asyncio.constants.THREAD_JOIN_TIMEOUT` = 300; surrealdb `AsyncWsSurrealConnection._recv_task` / `_send`.
- **Odoo-20 portability:** n/a — no Odoo seam touched. **Reuse ledger:** none (no symbols added to the repo; instruments in §A).
- **Graded:** working tree on `edf0d79` (patch md5 `7fd7e2ec…`, five files at the briefed md5s) · HEAD-at-report: `a34a7e4` · DIFFERENT (graded base 2 behind). `fb83c4a` + `a34a7e4` touch only `docs/design/…amendment-37.md`, `REPORT-lead-63c.md`, `REPORT-sidecar-63c-2.md`, so no symbol or assertion my verdict rests on moved.
- **Decisions needed:** (1) R-1/F-1: fold a generated door-domain unit pin into the Q2 contract follow-up? (recommended; §F F-1). (2) F-2/F-3/R-6 wording: lead's call.
- **Receipts:** §0/§0' md5 · §1 construction · §2 mutation table · §3 F1 · §4 census · §5 judgment · §5b gates · §6 trust · §F findings · Residuals · §A instruments (verbatim).

## Capability check (brief-base §4)
- Bash `grep` is hook-blocked on the main checkout (live-indexed); textual scans here are `awk`. Said per dogfood protocol.
- `lore_comms register` done (session 63c, cadence ≤20m). Idle-gate contract written:
  `/tmp/claude-idle-gate-lore/e07941b2-f68c-4b38-8d21-fa856ce4b18a-coldaudit-486-3.contract`.
- Deadline: 90 min from spawn (spawn ≈23:52Z 2026-10-04 → ≈01:22Z 2026-10-05).
- Everything the brief demands is within my tools. No capability gap.

## §0 md5 receipts — START (2026-10-04 23:53Z, HEAD `edf0d79`)
```
94f821754d8e37d0e613ef2f16f77dcc  loremaster/tests/conftest.py
6440b108c12a7fc37dc72f9f8fed5c46  loremaster/tests/test_harness_database_lifecycle_486.py
f6f6f73f529a05bc940a0499239e2380  loremaster/tests/test_no_raw_listener_in_test_trees.py
f8f43532ab3febc4a153c9798e40eca8  pyproject.toml
2d0892676d29f0af24586afbdb8bd307  uv.lock
7fd7e2ec78ddf38e52032ec9059b6e1b  486-r4-BUILD.patch (lead scratchpad)
```
All match the brief. Content backup (`cp -a`) of all five taken to my scratchpad `backup/` before any run.

## §1 Construction (step 1)
### 1a. `wedged` — answers pings, withholds replies: VERIFIED by probe, with a control
Instrument (verbatim in §A.1) drives the contract's own `_KillableStoreForwarder` with no pytest: after the
kill switch, it opens a websocket on the `cbor` subprotocol, pings three times, sends one request-shaped frame.
Measured 2026-10-04 ≈23:58Z in a `scratch_copy.sh` tree of the audited working tree:
```
wedged: handshake OK, subprotocol=cbor
wedged: ping 0..2 answered within 3s: True (x3)
wedged: request unanswered after 5s
muted:  handshake OK, subprotocol=cbor          <- CONTROL: same probe, the state that swallows post-handshake bytes
muted:  ping 0..2 answered within 3s: False (x3)
muted:  request unanswered after 5s
```
So `wedged` is exactly the state that passes the open timeout AND keeps the client's keepalive alive; the
control shows the probe can see an unanswered ping. Nothing a dependency owns ends a wedged request.

### 1b. `#538` — the injection prevents the report in BOTH workers: HOLDS, by construction + guard + mutation
- The plugin is a `tryfirst` `pytest_sessionfinish` loaded via `PYTEST_PLUGINS` (inherited by every xdist worker); it
  appends the worker id to a marker, then raises. The harness's `pytest_sessionfinish` is not `tryfirst`, so it never runs
  in either worker and neither report key is written. The guard checks `len(marker) == _XDIST_WORKERS` (2) before any
  verdict, so a broken wiring reads as CONSTRUCTION, never as a pass.
- Observed in my mutation (b) inner tail (2026-10-04 23:58Z): `returncode=0`, `1 passed`, and **no worker traceback in the
  output at all**: xdist swallows a raising worker session-finish hook silently. That is exactly #538's false clear, so
  the construction builds the state it claims.
- **What wrong build passes this pin?** The pin's only construction is **(every worker) × (both keys absent)**. A build that
  fails the session only when EVERY worker is a gap, or only when BOTH keys are absent, or that treats a corrupt value as
  accounted, satisfies it. Measured in §2 (c1–c3).

### 1c. R5 — the injection reaches the reap's read: HOLDS
- A `tryfirst` session-finish hook swaps `_surreal_harness.run` for a wrapper that answers `INFO FOR NS` with a LIST where
  a map is required and records each answer it served. `reap_minted_databases` calls the module-global `run(connection,
  "INFO FOR NS")` (read at `_surreal_harness.reap_minted_databases`), so the swap is on the reap's path. The guard requires
  ≥1 marker line, so a reap that never read through the injection is CONSTRUCTION, not a pass.
- Wrong builds: "name everything `failed`" passes R5 but is caught by the lost-store cells' `unreachable` assertion;
  "name everything `unreachable`" is caught by R5's negative assertion. The two pins together discriminate the classifier's
  two outcomes. Fine.

### 1d. R1 end-bound leg and the wedged cell
- The wedged cell can only end by the build's own bound (§1a probe; mutation (a) below). The `elapsed <= 120 s` leg
  guards a LOOSE bound (between 120 s and the 180 s outer kill). The contract's §7 marked it "not mutation-run; LOW". I ran
  it: mutation (a2) in §2 (budget 30 s → 150 s) reddens exactly the two wedged cells THROUGH THIS LEG
  (`the session ENDED, but only after 152s/153s … over the 120s ceiling`), not through the outer kill. The leg is load-bearing.

## §2 Mutations — my own, re-run independently (step 2)
All in a `./scripts/scratch_copy.sh` tree of the audited working tree (provenance receipt:
`loremaster.__file__ = …/scratchpad/tree/loremaster/loremaster/__init__.py`; md5s of the five files = the brief's).
Instrument `scripts/mutation_proof.py`; declared ids taken from `--collect-only` (486 file: 59 collected; guard: 38) BEFORE
each run; predictions written to my scratch `predictions.md` before the first run. Runner each time: the gate (MemAvailable
≥ 20 GiB loop + `pgrep` for another lore pytest → none) then `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0
… uv run --with pytest-timeout pytest -n 8 --timeout=300`. Each run restored conftest/guard byte-exact (the script's own
check), and the tree's md5s were re-read after the chain.

| id | mutation (anchor → replacement, `loremaster/tests/conftest.py` unless noted) | scope | predicted | observed | verdict |
|---|---|---|---|---|---|
| (a) | `anyio.fail_after(budget_seconds)` → `anyio.fail_after(None)` | 486 file | exactly `[wedged-n0]`+`[wedged-xdist-n2]` RED | `2 failed, 57 passed in 189.18s`; both REDs `did not END within 180s — a session-end step is waiting on a TEST store that will never answer…` | **PROOF HELD** (rc 0) |
| (b) | in `pytest_testnodedown`'s `except KeyError` branch, the gap → `None` (a missing report swallowed AT the chokepoint, a different edit from the implementer's mutation B) | `TestEveryXdistWorkerReportsItsSessionEnd` | the #538 pin RED, CONTROL green | `1 failed, 1 passed in 4.16s`; the RED is `assert 0 != 0` with `returncode=0 … 1 passed`, i.e. the right reason | **PROOF HELD** |
| (c1) | HALF report (§7 row 10): `workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY]` → `workeroutput.get(_UNREAPED_REPORT_WORKEROUTPUT_KEY, "[]")` (a missing unreaped key reads as "nothing unverified") | 486 file | SURVIVES | `59 passed in 69.19s`; `mutation LANDED`; declared #538 pin STAYED GREEN | **SURVIVES: no pin catches it** |
| (c2) | CORRUPT value (§7 row 9): the `except ValidationError` gap → `None` (an unreadable report counts as accounted) | 486 file | SURVIVES | `59 passed in 69.00s`; LANDED; pin stayed green | **SURVIVES** |
| (c3) | PARTIAL fleet: `_workers_without_session_end_report` returns its gaps only when EVERY worker is a gap | 486 file | SURVIVES | `59 passed in 70.09s`; LANDED; pin stayed green | **SURVIVES** |
| (d) | `test_no_raw_listener_in_test_trees.py`: delete the `"websockets": frozenset({"serve", "unix_serve", "Serve"}),` line | guard file | exactly the line-exact planted pin + `…is_flagged[websockets]` RED | `2 failed, 36 passed in 10.75s`; honest pin green | **PROOF HELD** |
| (e) | F-a door: `await reap_minted_databases()` → wrapped in `anyio.CancelScope(shield=True)` inside the `fail_after` scope | 486 file | exactly the two wedged cells RED | `2 failed, 57 passed in 228.83s`; both `did not END within 180s`; LANDED | **PROOF HELD**: the wedged cells already pin the shielded-scope door |
| (a2) | LOOSE budget: `anyio.fail_after(budget_seconds)` → `anyio.fail_after(150)` (between the 120 s end-bound and the 180 s kill) | the lost-state test (8 cells) | exactly the two wedged cells RED via the END-BOUND leg | `2 failed, 6 passed in 154.30s`; both `the session ENDED, but only after 152s/153s with the TEST store wedged — over the 120s ceiling` | **PROOF HELD**: closes contract §7's "not mutation-run" row |

**Positive control for the survivors (c1–c3): the mutants ARE behaviourally wrong, and the build under audit is right.**
I drove `pytest_testnodeready` / `pytest_testnodedown` / `_workers_without_session_end_report` directly with fake xdist
nodes (instrument §A.2 = the implementer's §A probe, parameterised on the conftest file and extended with a HALF-report door
`gw8`), against the audited conftest and against each mutant (measured 2026-10-05 ≈00:04Z):
```
conftest_audited.py: gaps=['gw1','gw2','gw3','gw4','gw5','gw6','gw8']   PROBE OK
conftest_c1.py:      gaps=[... no 'gw8']                                 MISMATCH wrong=['gw8']           (half report accounted)
conftest_c2.py:      gaps=['gw1','gw2','gw6','gw8']                      MISMATCH wrong=['gw3','gw4','gw5'] (corrupt accounted)
conftest_c3.py:      gaps=[]                                             MISMATCH wrong=[all seven]        (partial fleet passes)
```
Note: the implementer's own §A probe has no half-report door with the UNREAPED key missing (its `gw2` drops the LEAK key),
so it would NOT have caught c1 either. And the probe lives only in a report: it is in no `testpaths`. See finding F-1.

After the chain (2026-10-05 00:06Z) the scratch tree's md5s were the audited ones again (conftest `94f82175…`,
guard `f6f6f73f…`, 486 `6440b108…`).

## §5 Judgment reads (step 6)
### F-a: a non-cancellable block now hangs the main thread instead of being abandoned. Recommendation: **ACCEPT, as ALREADY PINNED for every door that waits on the store**
The question is not "can anything hang?" but "can an HONEST change add a hang that no pin sees?". Lifted: *∀ non-cancellable
construct the reap path could gain, does a constructed lost store turn it into a RED?* The doors:
| door | mechanism under the new build | pinned? |
|---|---|---|
| `CancelScope(shield=True)` around a store await | `fail_after` cannot cancel inside it; wedged never answers | **YES, measured**: mutation (e) PROOF HELD |
| a SYNC blocking call that talks to the store (a blocking socket/HTTP call) | blocks the loop, so `fail_after` never runs; wedged/silent/muted never answer | YES by construction (reasoned, NOT measured): the same 180 s outer kill as (a)/(e) |
| `to_thread` / `run_in_executor` that talks to the store | `fail_after` cancels the await at 30 s, then `anyio.run`'s `asyncio.Runner.close()` calls `loop.shutdown_default_executor(constants.THREAD_JOIN_TIMEOUT)`, which waits up to **300 s** (read live on this venv: `THREAD_JOIN_TIMEOUT 300`; anyio 4.13.0 `AsyncIOBackend.run` uses `Runner`) | YES by construction (reasoned): 300 s > the 180 s kill, so the wedged cells go RED |
| a block that does NOT wait on the store (a deadlock, `time.sleep` in a loop) | hangs EVERY session, healthy ones included | visible to every test run; no special pin needed |
| the SDK's own executor use: `getaddrinfo` for a HOSTNAME store URL with dead DNS | could hold `anyio.run` teardown ≤ 300 s where the daemon thread abandoned it at 30 s | NOT pinned. Not reachable today: the TEST store is `ws://127.0.0.1:18000` by law (no DNS). **Re-open trigger: the TEST-store URL becomes a hostname.** Residual R-4 |
So F-a's realistic doors are already covered by R1's wedged cells. No new pin recommended. Keep the implementer's trigger.

### §7 row 4: `SystemExit` / `KeyboardInterrupt` (any non-`Exception` `BaseException`) now propagate. Recommendation: **ACCEPT** (no pin)
- `KeyboardInterrupt`: equivalent to the old build, because Ctrl-C was delivered to the main thread's `join` there too (the
  implementer's reading; I agree).
- The realistic `BaseException` here is `asyncio.CancelledError` from the SDK: on a dropped socket, `AsyncWsSurrealConnection._recv_task`'s
  `finally` calls `fut.cancel()` on every pending request (read: `surrealdb/connections/async_ws.py`, `_recv_task` + `_send`).
  But `_send`'s own `finally: del self.qry[query_id]` then raises `KeyError` (the recv task already did `self.qry.clear()`),
  which REPLACES the `CancelledError`. That `KeyError` is an `Exception`, and it is the request-routing `KeyError`
  `_reap_failure_outcome` already classifies as `unreachable`. So the SDK's one `CancelledError` door surfaces as an
  `Exception` today. **Re-open trigger:** an SDK upgrade that changes `_send`'s cleanup (e.g. `self.qry.pop(query_id, None)`)
  would let a raw `CancelledError` escape `_reap_within_budget` → raw traceback / INTERNALERROR at `-n 0` (a worker would
  then be a #538 gap, which still fails the session). Residual R-5.
- `SystemExit` raised BY the reap: no such code exists; spec-silent; fine.

## §F Findings
### F-1 (MEDIUM): #538 is pinned at ONE point of its domain; three plausible wrong builds pass the whole contract
- **CLASS (lifted):** *∀ xdist worker w, ∀ way w's session-end report can fail to be complete-and-readable at the controller
  (never went down · crashed · a key missing · BOTH keys missing · a corrupt value · a wrong shape · a `None` value), and ∀
  subset of workers that fail, the session fails and names each such w.* Domain source of truth: the two
  `*_REPORT_WORKEROUTPUT_KEY` constants × the two `TypeAdapter` shapes × {node-ready-without-node-down} × the worker set.
  The contract constructs exactly one point: **all workers × both keys absent**. This is the QUANTIFIER LAW / FIXTURE
  MONOCULTURE class (CLAUDE.md "FIXTURES MUST DISCRIMINATE" axis 2): the pin is ∀-quantified in its docstring and
  single-valued in its fixture.
- **Measured (§2):** c1 (half report accounted), c2 (corrupt value accounted), c3 (gaps reported only when every worker is
  a gap) each pass `59/59` of the 486 file, mutation LANDED. The build under audit is CORRECT on all of them (§2 positive
  control; §A.2 probe `PROBE OK`), so this is a missing REGRESSION pin, not a live defect.
- **SIBLINGS TRIED:** half report with the UNREAPED key missing (c1); corrupt/unreadable value (c2); partial fleet (c3);
  missing report at the chokepoint (b, caught).
- **SIBLINGS NOT TRIED (as pytest constructions):** a worker killed mid-session-finish (`error` non-None, real xdist); a
  node-ready with no node-down (an interrupted session); half report with the LEAK key missing (the implementer's probe
  `gw2` covers it offline, as do `gw3`–`gw6`).
- **Recommendation (for a contract author, not me):** promote the door probe to a pinned, store-free unit test that drives
  `pytest_testnodeready` / `pytest_testnodedown` / `_workers_without_session_end_report` with fake nodes, GENERATED over
  the door domain above (both keys × {absent, corrupt, wrong shape, `None`}, plus crash, plus never-went-down), with at least
  one ACCOUNTED worker beside the gaps in every case. It costs ~0.1 s and kills c1–c3 (proved by §A.2 against each mutant).
  This is a test-tree change, so it is a contract round, not an implementer fix.

## §3 #537 / F1 under every runner form (step 3) — measured 2026-10-05 00:12:50–00:12:57Z, real working tree
Node: `loremaster/tests/test_no_raw_listener_in_test_trees.py::TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed`
| runner (each under the 16G cgroup, gate checked first) | tail |
|---|---|
| `uv run pytest` (plain) | `1 passed in 0.10s` |
| `uv run --with pytest-timeout pytest -n 8 --timeout=300` | `1 passed in 1.45s` |
| `uv run --with pytest-timeout pytest -n 0 --timeout=300` | `1 passed in 0.10s` |
| **NEGATIVE CONTROL**: same `-n 8` form in my `before` scratch tree (HEAD `pyproject.toml`/`uv.lock`, no `pytest-timeout` in the venv) | `1 failed in 1.50s` |
The control shows the dev dependency is what turned F1 green, not a runner accident. `uv lock --check` → `Resolved 149
packages` (lock consistent with `pyproject.toml`, so the Containerfile's `uv sync --locked` will not fail on it).

## §4 Census (step 4) — targeted before vs after, measured 2026-10-05 00:06–00:12Z
Set (7 files): the implementer's §Scope six (`test_harness_database_lifecycle_486.py`, `test_no_raw_listener_in_test_trees.py`,
`test_surreal_harness.py`, `test_retry_seam.py`, `test_caplog_isolation.py`, `test_store_seam_one_derivation.py`) **plus my own
derivation**: `test_loopback_serving.py` (it pins behaviour under a "pytest-timeout-shaped BaseException", and `pytest-timeout`
is the new package in the venv). Derivation method: `awk` over every tracked test file for
`pyproject|uv.lock|dependency.groups|pytest_timeout|pytest-timeout|_reap_within_budget|pytest_testnodedown|workeroutput`
(the Bash text-search tool is hook-blocked on this checkout; `lore_impact` cannot see pytest hook dispatch, as the
implementer's F-e says — fallback stated). Other hits were read and rejected: they read `[tool.uv.workspace] members` /
`testpaths` / `mypy_path` (unchanged), or write their own tmp `pyproject.toml`.
`skills/lore-deploy/tests/test_containerfile_locked.py` reads only `members` + the Containerfile; its real dependency (lock
currency) is covered by `uv lock --check` above.
| side | tree | tail |
|---|---|---|
| BEFORE | scratch `before/`: HEAD `edf0d79` conftest (`6c3710d6…`) + HEAD `pyproject.toml`/`uv.lock`, `uv sync --all-packages` (no `pytest-timeout`), the two CONTRACT test files at the audited md5s; provenance verified by `scratch_copy.sh --verify-only` | `2 failed, 932 passed, 2 skipped, 9 warnings in 187.84s`, the 2 = F1 (#537) and the #538 pin |
| AFTER | the real working tree (audited md5s) | `934 passed, 2 skipped, 11 warnings in 184.26s`, rc 0 |
- 936 collected on both sides. Every contract cell GREEN after. **0 GREEN→RED.** RED→GREEN: exactly F1 and the #538 pin.
- Warnings 9 → 11 is NOT attributable: the same three categories on both sides (`_empty_subscription` never awaited, the
  pre-existing F-d; `websockets.legacy` and uvicorn `WebSocketServerProtocol` DeprecationWarnings). The deprecation pair is
  emitted once per xdist worker process that first imports uvicorn, so its count follows scheduling (4 tests listed before,
  5 after, ×2 categories).

## §5b Gates (step 5) — 2026-10-05 ≈00:07Z, real working tree
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` (no `-n` forwarded):
  `typecheck RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract …` · `ruff GREEN` · pytest `NOT_RUN`.
  **RED_ORPHANED 0 among the legs run.** ⚠ The render still ends `CURRENCY: FAIL — claimed but never run: pytest`, rc 1, for
  the leg CLAUDE.md tells every agent to leave unrun. Noted as friction (F-4), not a red.
- `scripts/typecheck.sh`: 83 errors total, **0 in the three audited test files** (awk over its output). Single-file
  `mypy loremaster/tests/conftest.py` → `Success: no issues found`.
- `ruff check` on the three files → `All checks passed!`; `ruff format --check` → `3 files already formatted`.

## §6 Trust (step 7): does any failure line over-claim or name a false cause?
The served #538 output, captured from the contract's own construction against the audited build (instrument §A.3; 2026-10-05
00:13Z; marker `['gw1','gw0']`, rc 1, one DB created and removed):
```
.                                                                        [100%]
==================================== PASSES ====================================
xdist worker gw0 finished WITHOUT its session-end report (no 'lore_486_leaked_test_databases' value arrived) — whatever test databases it opened were neither reaped-and-named nor reported unverified. They may still be on the TEST store; the periodic test-namespace wipe removes them
xdist worker gw1 finished WITHOUT its session-end report (no 'lore_486_leaked_test_databases' value arrived) — …same…
=========================== short test summary info ============================
PASSED test_inner_486.py::test_opens_a_database_and_drops_it
1 passed in 1.47s
```
- **No false cause.** The line names what is missing and does not guess why. R5's line says `failed`, never `unreachable`
  (pinned). The lost-store lines say `unreachable` (pinned).
- **F-2 (LOW, trust/report accuracy): the worker's real cause is invisible, and the implementer's report says otherwise.**
  REPORT-implement-486-r4 §1 says the line omits the worker's error text because *"xdist already prints that"*. In the
  constructed case it does NOT: the output above has no traceback, no `node down`, nothing. xdist swallowed the raising
  worker hook, and `error` was `None` (the gap reads without the "(went down with an error)" suffix). So the gap line is the
  operator's ONLY signal, and it cannot tell "a session-finish hook raised before the harness's" from "the report was lost
  in transit". Not a false clear (the session fails, the worker is named), and not a false cause (none is named). CLASS:
  *a served line whose companion signal is assumed to exist elsewhere.* SIBLINGS TRIED: the `error=None` path (this
  capture). NOT TRIED: a real worker crash (`error` non-None), where xdist does print. Recommendation: optional. If wanted,
  when `error is None` say "the worker reported no error, so a session-finish hook in it may have raised before the
  harness's". Not blocking.
- **F-3 (LOW, trust): "finished" is false for the gap `it never went down`.** That gap is reachable only when the
  controller's session-finish runs with a node still up (an interrupt or an internal xdist error). The line then reads
  `xdist worker gwN finished WITHOUT its session-end report (it never went down)`, which contradicts itself. The session is
  already non-OK in that case, so no verdict is wrong; the sentence is. CLASS: *fixed prose wrapped around a variable
  cause, where one cause falsifies the prose.* SIBLINGS TRIED: every gap string in `pytest_testnodedown` /
  `pytest_testnodeready` read against the fixed prefix; only this one contradicts it. Recommendation: derive the verb from
  the gap ("did not report its session-end before the session ended"). Not blocking.
- **Inherited, not new: "the periodic test-namespace wipe removes them".** I found no automated wipe (no cron entry, no
  systemd user timer, no script hit for a test-namespace wipe). The D2 ruling is *periodic OPERATOR wipes*
  (docs/plans/v2/receipts/2026-10-04-486/REPORT-coldaudit-486.md R5 row; REPORT-implement-486.md). `_unreaped_line` already
  said this before this round; the new line repeats it. A reader may take "the periodic … wipe" for a scheduled mechanism.
  Wording nit for the lead: "the operator's periodic test-namespace wipe". Residual R-6.
- The budget-expiry text `no answer within the 30s session-end reap budget` is the pre-round string, unchanged.

### §5 addendum — F-a vs the operator's Q2 ruling (landed DURING this audit, `fb83c4a`/`a34a7e4`, docs only)
The lead's report records an operator ruling (am-37 §14 Q2): keep `anyio.fail_after` as the graceful inner bound and ADD a
hard stdlib outer bound (`faulthandler.dump_traceback_later(2×budget, exit=True)`), pinned by a subprocess cell (a sync
sleep). That supersedes my "accept" above for the one door my table leaves to "visible everywhere": a non-cooperative block
that does not wait on the store. My measurements do not contradict the ruling. They show the store-waiting doors were
already pinned by the wedged cells ((e) measured; sync-block and `to_thread` reasoned). Notes for the delta audit
(coldaudit-486-4), unmeasured here:
1. `faulthandler.dump_traceback_later` is ONE process-global timer. pytest's own `faulthandler_timeout` ini option arms and
   cancels the same timer per test. Arming it in `pytest_sessionfinish` is after the last test, so the two should not
   collide, but the cell should prove the timer is armed AFTER pytest's last cancel.
2. `exit=True` calls `_exit`: no terminal summary and no pytest verdict line. At `-n 0` the session ends non-zero with only
   the dump. Under xdist the worker dies without its report, so the #538 chokepoint names it. Expect that, and pin it.

## §F (continued)
### F-4 (LOW, friction, FILED as lore finding #540): the currency gate's correct per-round use always renders FAIL
`--currency --legs typecheck,ruff` ends `CURRENCY: FAIL — claimed but never run: pytest`, rc 1, although CLAUDE.md makes
exactly that invocation the per-round check and forbids the pytest leg mid-packet. Every agent has to explain the red away
(implement-486-r4 §8 did; so does §5b here). CLASS: *a gate whose compliant use renders FAIL trains its readers to ignore
FAIL.* Not this round's code; surfaced and ledgered.

## Residuals
| # | residual | severity | owner (proposed) | trigger / next decision |
|---|---|---|---|---|
| R-1 | F-1: #538 pinned at one point of its door × worker-subset domain; c1/c2/c3 survive the contract (build correct today, by probe) | MEDIUM | a contract author (test tree), e.g. folded into the Q2 contract-486-r4 follow-up (writable: the 486 file) | before #486 closes; the §A.2 probe is the ready-made instrument |
| R-2 | F-2: in the raised-hook case xdist prints nothing; the gap line is the only signal and cannot name the cause; the implementer report's "xdist already prints that" is false here | LOW | lead (wording call) | optional wording change, no pin needed |
| R-3 | F-3: "finished WITHOUT…" contradicts the gap "it never went down" | LOW | implementer (conftest wording) | only reachable on an already non-OK session |
| R-4 | F-a executor door: a HOSTNAME TEST-store URL with dead DNS could hold `anyio.run` teardown ≤ 300 s (the old thread abandoned it at 30 s); after Q2 lands, the faulthandler bound at 2×budget closes it | LOW | covered by the Q2 ruling | re-open if Q2 is dropped AND the TEST-store URL becomes a hostname |
| R-5 | §7 row 4: the SDK's `CancelledError` door is masked today by `_send`'s `del self.qry[query_id]` `KeyError` (read, not measured) | LOW | none now | re-open on a surrealdb SDK upgrade that changes `_send`'s cleanup |
| R-6 | "the periodic test-namespace wipe removes them": inherited wording; the D2 mechanism is operator wipes, and no scheduled wipe exists | LOW | lead (wording) | wording nit only |
| R-7 | F-4 / #540: the currency render FAILs on the legs-subset invocation the law mandates | LOW | gate owner | filed #540 |

## §0' md5 receipts — END (2026-10-05 00:16:26Z)
```
94f821754d8e37d0e613ef2f16f77dcc  loremaster/tests/conftest.py
6440b108c12a7fc37dc72f9f8fed5c46  loremaster/tests/test_harness_database_lifecycle_486.py
f6f6f73f529a05bc940a0499239e2380  loremaster/tests/test_no_raw_listener_in_test_trees.py
f8f43532ab3febc4a153c9798e40eca8  pyproject.toml
2d0892676d29f0af24586afbdb8bd307  uv.lock
7fd7e2ec78ddf38e52032ec9059b6e1b  486-r4-BUILD.patch
```
Byte-identical to the start, and `cmp` against my `cp -a` content backup is identical for all five. I made no edit to any
tracked file (every mutation ran in the scratch copy and was restored byte-exact by `mutation_proof.py`). `git status`
shows only the five audited files plus three untracked reports (two pre-existing, plus this one). No pytest of mine is
left running (`pgrep` → 0). The TEST store `:18000` was the only store touched. Every inner database the contract helpers
created was removed in their `finally` blocks, and §A.3's in its own.

### Mutant generation for §A.2 (verbatim): the audited conftest with each of the §2 c1/c2/c3 anchor→replacement pairs applied by `str.replace`, after asserting the anchor occurs exactly once.

## §A Instruments (pasted VERBATIM — brief-base §1; my scratch tree is disposable)
Mutation runner: committed `scripts/mutation_proof.py`; exact anchors/replacements are in the §2 table; the chained runner and the test-law preamble follow.

### §A.1 wedged_probe.py (§1a)
```
"""coldaudit-486-3: does the contract's `wedged` store answer pings and withhold replies? (control: `muted`).

Drives the contract's own _KillableStoreForwarder (no pytest). After the kill-switch, opens a websocket
on the SDK's `cbor` subprotocol, pings, then sends one frame and waits for any reply.
"""
import importlib
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, "loremaster/tests")
contract = importlib.import_module("test_harness_database_lifecycle_486")
from websockets.sync.client import connect  # noqa: E402

for state in ("wedged", "muted"):
    tmp = Path(tempfile.mkdtemp(prefix=f"probe-{state}-"))
    kill_switch, killed_ack = tmp / "kill", tmp / "ack"
    with contract._KillableStoreForwarder(kill_switch, killed_ack, lost_state=state) as forwarder:
        assert forwarder._upstream[1] == 18000, forwarder._upstream  # TEST store only
        kill_switch.touch()
        deadline = time.monotonic() + 5
        while not killed_ack.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        assert killed_ack.exists(), "forwarder never lost the store"
        websocket = connect(forwarder.url, subprotocols=["cbor"], open_timeout=5, ping_interval=None)
        print(f"{state}: handshake OK, subprotocol={websocket.subprotocol}")
        for attempt in range(3):
            pong = websocket.ping(f"p{attempt}".encode())
            print(f"{state}: ping {attempt} answered within 3s: {pong.wait(3)}")
        websocket.send(b"\xa0")  # a CBOR empty map — a request-shaped frame
        try:
            websocket.recv(timeout=5)
            print(f"{state}: REQUEST ANSWERED")
        except TimeoutError:
            print(f"{state}: request unanswered after 5s")
        websocket.close_timeout = 1
        websocket.close()
```

### §A.2 probe538/probe.py (§2 positive control)
```
"""coldaudit-486-3: the implementer's #538 door probe (REPORT-implement-486-r4 §A), extended with the HALF-report door
(unreaped key missing, leak key present) and parameterised on WHICH conftest file it loads, so the same doors can be
driven against the audited conftest and against a mutant. Run: uv run python probe.py <conftest-path> (cwd = a lore tree)."""
import importlib.util
import json
import sys
from pathlib import Path
from types import SimpleNamespace

conftest_path = Path(sys.argv[1]).resolve()
sys.path.insert(0, str(Path("loremaster/tests").resolve()))
spec = importlib.util.spec_from_file_location("lore_conftest_probe", conftest_path)
conftest = importlib.util.module_from_spec(spec)
spec.loader.exec_module(conftest)
LEAK, UNREAPED = conftest._LEAK_REPORT_WORKEROUTPUT_KEY, conftest._UNREAPED_REPORT_WORKEROUTPUT_KEY
GOOD = {LEAK: "[]", UNREAPED: "[]"}


def node(worker, workeroutput=None):
    fake = SimpleNamespace(gateway=SimpleNamespace(id=worker))
    if workeroutput is not None:
        fake.workeroutput = workeroutput
    return fake


doors = {
    "gw0": (GOOD, None),                                    # clean report -> ACCOUNTED
    "gw1": (None, "worker died"),                           # crashed, no workeroutput -> GAP
    "gw2": ({UNREAPED: "[]"}, None),                        # leak key missing -> GAP
    "gw3": ({**GOOD, LEAK: "{oops"}, None),                 # corrupt -> GAP
    "gw4": ({**GOOD, UNREAPED: json.dumps([["x"]])}, None), # wrong shape -> GAP
    "gw5": ({**GOOD, LEAK: None}, None),                    # None value -> GAP
    "gw7": (GOOD, "died after reporting"),                  # readable report -> ACCOUNTED
    "gw8": ({LEAK: "[]"}, None),                            # HALF report: unreaped key missing -> GAP (added by coldaudit-486-3)
}
for worker, (workeroutput, error) in doors.items():
    each = node(worker, workeroutput)
    conftest.pytest_testnodeready(each)
    conftest.pytest_testnodedown(each, error)
conftest.pytest_testnodeready(node("gw6"))  # came up, node-down never fired -> GAP
gaps = conftest._workers_without_session_end_report()
expected = {"gw1", "gw2", "gw3", "gw4", "gw5", "gw6", "gw8"}
print(f"{conftest_path.name}: gaps={sorted(gaps)}")
print("PROBE OK" if set(gaps) == expected else f"PROBE MISMATCH: wrong={sorted(set(gaps) ^ expected)}")
```

### §A.3 show_538_output.py (§6)
```
"""coldaudit-486-3: print the SERVED output of the contract's #538 construction against the build in cwd.

Reuses the contract's own helpers (no new construction): _run_bounded + _INNER_OPENS_AND_DROPS + the raising
session-end plugin, 2 xdist workers, TEST store only; removes the one database it opens in `finally`.
"""
import asyncio
import importlib
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, "loremaster/tests")
contract = importlib.import_module("test_harness_database_lifecycle_486")
from _surreal_harness import surreal_url  # noqa: E402

assert ":18000" in surreal_url(), surreal_url()
tmp_path = Path(tempfile.mkdtemp(prefix="show538-"))
marker = tmp_path / "injection.marker"
created: list[str] = []
try:
    session = contract._run_bounded(
        tmp_path,
        contract._INNER_OPENS_AND_DROPS,
        workers=contract._XDIST_WORKERS,
        store_url=surreal_url(),
        timeout_seconds=contract._LOST_STORE_SESSION_TIMEOUT_SECONDS,
        created_sink=created,
        **contract._injected_plugin_environment(
            tmp_path, contract._RAISING_SESSION_END_PLUGIN, marker, **{contract._INJECTION_RAISES_ENV: "1"}
        ),
    )
    print("marker:", contract._marked(marker), "rc:", session.returncode, "created:", session.created)
    print("----- served output -----")
    print(session.output)
finally:
    asyncio.run(contract._remove_if_present(*created))
```

### §A.4 gate.sh (test-law preamble)
```
#!/usr/bin/env bash
# Test-law preamble: wait for MemAvailable >= 20 GiB, refuse if another lore pytest is live.
set -euo pipefail
while true; do
  avail_kib=$(awk '/MemAvailable/ {print $2}' /proc/meminfo)
  if [ "$avail_kib" -ge $((20*1024*1024)) ]; then break; fi
  echo "waiting: MemAvailable ${avail_kib} KiB" >&2; sleep 15
done
others=$(pgrep -fa '[p]ython.*-m pytest|[b]in/pytest' || true)
if [ -n "$others" ]; then echo "ANOTHER PYTEST LIVE:" >&2; echo "$others" >&2; exit 3; fi
echo "gate ok: MemAvailable $(awk '/MemAvailable/ {print $2}' /proc/meminfo) KiB, no other lore pytest, $(date -u +%H:%M:%SZ)"
exec "$@"
```

### §A.5 run_mutations.sh (b, c1–c3, d, e)
```
#!/usr/bin/env bash
S=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/e07941b2-f68c-4b38-8d21-fa856ce4b18a/scratchpad
cd $S/tree
F=loremaster/tests/test_harness_database_lifecycle_486.py
G=loremaster/tests/test_no_raw_listener_in_test_trees.py
C=loremaster/tests/conftest.py
W="$F::TestTheSessionEndReapNeverCostsPytestItsVerdict::test_an_opened_database_with_the_store_lost_at_session_end_is_reported_loudly"
PIN="$F::TestEveryXdistWorkerReportsItsSessionEnd::test_a_worker_that_never_shipped_its_session_end_report_fails_the_session"
RUN="uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE"
cap() { $S/gate.sh systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python scripts/mutation_proof.py "$@"; echo "rc=$?"; }
echo "=== (b) $(date -u +%T)"; cap --file $C --anchor '        _SESSION_END_REPORT_GAP_BY_WORKER[_worker_id(node)] = f"no {missing} value arrived{crashed}"' --replacement '        _SESSION_END_REPORT_GAP_BY_WORKER[_worker_id(node)] = None' --expect-red "$PIN" -- $RUN "$F::TestEveryXdistWorkerReportsItsSessionEnd"
echo "=== (c1) $(date -u +%T)"; cap --file $C --anchor '        unreaped = _UNREAPED_REPORT_SHAPE.validate_json(workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY])' --replacement '        unreaped = _UNREAPED_REPORT_SHAPE.validate_json(workeroutput.get(_UNREAPED_REPORT_WORKEROUTPUT_KEY, "[]"))' --expect-red "$PIN" -- $RUN $F
echo "=== (c2) $(date -u +%T)"; cap --file $C --anchor '            f"its report could not be read ({corrupt.error_count()} shape error(s))"' --replacement '            None' --expect-red "$PIN" -- $RUN $F
echo "=== (c3) $(date -u +%T)"; cap --file $C --anchor '    return {worker: gap for worker, gap in _SESSION_END_REPORT_GAP_BY_WORKER.items() if gap is not None}' --replacement '    return (lambda gaps: gaps if len(gaps) == len(_SESSION_END_REPORT_GAP_BY_WORKER) else {})({worker: gap for worker, gap in _SESSION_END_REPORT_GAP_BY_WORKER.items() if gap is not None})' --expect-red "$PIN" -- $RUN $F
echo "=== (d) $(date -u +%T)"; cap --file $G --anchor '    "websockets": frozenset({"serve", "unix_serve", "Serve"}),' --replacement '' --expect-red "$G::TestTheDetectorSeesWebsocketsListeners::test_every_planted_websockets_listener_is_flagged_on_its_line" --expect-red "$G::TestTheServerCapableDependenciesAreDerived::test_the_planted_spelling_of_each_server_capable_dependency_is_flagged[websockets]" -- $RUN $G
echo "=== (e) $(date -u +%T)"; cap --file $C --anchor '            await reap_minted_databases()' --replacement-file $S/shield_replacement.txt --expect-red "$W[wedged-n0]" --expect-red "$W[wedged-xdist-n2]" -- $RUN $F
echo "=== done $(date -u +%T)"; md5sum $C $G $F
```
