brief-base v18 read · brief project v7 read

# REPORT — coldaudit-486-2 (fresh-context RE-AUDIT of #486 round 3, finding #534; patch FINAL2 `eb6a5dd8`)

## SUMMARY BLOCK
- **VERDICT: GO**, with three residuals the lead must route or rule (R1–R3 below). The #534 fix holds by construction and under mutation:
  - mutations (a), (c), (d) and (b′) **PROOF HELD**;
  - the (b″) control is green;
  - targeted run on the patched tree: **928 passed, 1 failed, 4 skipped**, and the one red is F1, which is runner-caused and red on plain HEAD (now **#537**, not #486's);
  - 0 loud/traceback lines in the outer run; census of `lore_test` **75 → 75** across every run;
  - ruff GREEN; currency typecheck/ruff **RED_ORPHANED 0**.
  - **The other reading, written down (brief-base §2):** R1 and R3 are the "rider half-pinned" and "fixed at the PATH, not the STATE" classes from CLAUDE.md. A grader who weights those laws above right-sizing would call this **NO-GO until R1+R3 land**. I do not, because neither is a regression against HEAD and R3 needs a harness bug to fire. That is a lead/operator call (D1).
- **State:** done.
- **Deviations:**
  - Mutation (b) was run against the brief's predicted RED set, and my own prediction was written down first (`predictions.md`, §2). It SURVIVED, which is finding R1.
  - Probe (e) is extra; it measures implementer flag 5.
- **Packages considered:**
  - **(i) Bounded reap.** Read the installed `/usr/lib/python3.14/concurrent/futures/thread.py` (`threading._register_atexit(_python_exit)`, line 37) and `asyncio.timeouts.Timeout.__aexit__`. Probed `anyio.fail_after` (anyio 4.13.0, a DIRECT dependency, `anyio>=4.5`). Verdict: **`replace` recommended** (R2). The bespoke daemon thread works, but its premise "an in-loop timeout is not a bound" is false for anyio.
  - **(ii) The contract's TCP forwarder.** Read `loremaster.testing.loopback` (ASGI/uvicorn only), `socketserver.TCPServer.__init__` and the installed set (no proxy package; toxiproxy absent; socat binds a numbered port, the #466 class). Verdict: **`keep_with_trigger`** (JUSTIFIED). Trigger: a second fault-injecting proxy is needed anywhere.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** none (0 new repo symbols; instruments pasted in §A).
- **Graded:** patch `eb6a5dd8` over `fc1ef7a` · HEAD-at-report: `fc1ef7a` · SAME.
- **Decisions needed:**
  - (D1) R1 (budget unpinned) + R3 (#538, worker-hook raise is swallowed): fix now in one small tdd-light wave (my recommendation), or rule them pinned bounds.
  - (D2) R2: replace the daemon-thread bound with `anyio.fail_after`, or keep it with a stated reason.
  - (D3) #537 (F1): add `pytest-timeout` as a dev dependency (recommended), or fix the classifier.
- **Receipts:** §0 trees · §1 construction · §2 mutations · §3 F1 · §4 packages · §5 targeted · §6 census · §7 gates · RESIDUAL TABLE · §A instruments.

## Capability check (brief-base §4)
- grep/rg are hook-blocked (#473). Every textual scan was awk or a Python AST instrument (grep case (b), textual seams in an uncommitted patch the lore index cannot see, #125).
- lore was used for `lore_comms register/heartbeat`, `lore_findings` (query, report #537 and #538, annotate #534).
- Nothing the brief demanded was out of reach.
- Deadline 75 min: started 19:13Z; report ~19:45Z.

## §0 Trees and provenance (measured 2026-10-04 19:13–19:15Z, HEAD `fc1ef7a`)
- **Three trees, each made with `./scripts/scratch_copy.sh`, then `git reset --hard HEAD && git clean -fd`:** `git status --short` printed nothing for each.
  - `S` = `…/scratchpad/reaudit486` (patched);
  - `M` = `…/scratchpad/mut486b` (patched, mutations);
  - `H` = `…/scratchpad/head486` (plain HEAD, the F1 control).
- **Patch check:** `md5sum 486-FINAL2.patch` = `eb6a5dd81df0b4b9d0518cc96639f653`. It has 28 files and 0 outside `loremaster/tests/`. It applied cleanly to S and M (28 entries in `git status`).
- **`loremaster.__file__`** for each tree:
  - S: `…/scratchpad/reaudit486/loremaster/loremaster/__init__.py`
  - M: `…/scratchpad/mut486b/loremaster/loremaster/__init__.py`
  - H: `…/scratchpad/head486/loremaster/loremaster/__init__.py`
- **The main tree's working copy is byte-identical to S** across all 28 files (`cmp`, 0 differing). The audited bytes are the bytes the lead will commit.
- After all mutations, M is byte-identical to S again (0 differing); the conftest md5 is `6c3710d6…` throughout.

## §1 By construction (read in S; cited by symbol in `loremaster/tests/conftest.py`)
| # | Check | Verdict | Evidence |
|---|---|---|---|
| 1 | The session-end reap dials the store ONLY if a minted DB was opened | **PASS** | `pytest_sessionfinish`: `if _DATABASES_OPENED_THIS_SESSION & _MINTED_DATABASES.keys(): failure = _reap_within_budget(...)`. `_DATABASES_OPENED_THIS_SESSION` is filled by the existing `_record_database_selection` `use()` observer. Mutation (a) proves the cells see it (§2). |
| 2 | Bounded reap, explicit budget | **PASS (behaviour); bound UNPINNED (R1)** | `_SESSION_END_REAP_BUDGET_SECONDS = 30.0` → `_reap_within_budget` (daemon `threading.Thread`, `join(budget)`, returns `TimeoutError("no answer within the 30s session-end reap budget")`). (b′)/(b″) prove the budget is what bounds a TRUE hang. Mutation (b) proves no contract cell sees its deletion (§2). |
| 3 | refused / silent / muted → ONE named "unreachable / could not verify" line + rc ≠ 0 + pytest summary intact + no traceback | **PASS** | `_unreaped_line` + `pytest_terminal_summary` print one line per outcome kind, merged across workers. All 12 LEG-4b cells are GREEN in §5. Mutation (d) proves the line and no-traceback legs bite. |
| 4 | Under xdist, a worker's reap failure reaches the controller's verdict | **PASS for reap failures; GAP for hook failures (R3, #538)** | The worker writes `workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY]`, `pytest_testnodedown` merges it, and the controller's `pytest_sessionfinish` sets `TESTS_FAILED`. Mutation (c) proves it. But probe (e) shows a raise anywhere in the hook BEFORE that write is swallowed: rc 0, `1 passed`, no trace (§2). |
| 5 | Non-transport reap failures named too | **PASS by construction, UNPINNED** | `_reap_failure_outcome` returned these (§A.4): `ConnectionRefusedError`→unreachable, `TimeoutError`→unreachable, `KeyError`→unreachable, `SurrealStoreError`→**failed**, `TxnContentionExhaustedError`→**failed**, `RuntimeError`→**failed**. The `failed` kind gets its own `session-end reap failed against …` line. No contract cell constructs a non-transport failure; the implementer's §Class says so too. |
| 6 | No new harness module-level name (D-r2b-1) | **PASS** | The round-3 harness delta (FINAL→FINAL2, harness hunk only) is 35 changed patch lines, all docstring text or hunk-offset headers (§A.3). The AST diff of `_surreal_harness.py` HEAD→S adds `Iterable, _MINTED_DATABASES, _RUN_STATEMENT_LABEL, reap_minted_databases`, all rounds 1–2, all in `_ALLOWED_MODULE_LEVEL_NAMES`. `test_the_harnesss_module_level_names_are_exactly_the_allowed_set` is inside §5's 928 passed. |
| 7 | Reuse of `_txn._SDK_AWAIT_BOUNDARY_ERRORS` / `is_connection_error` | **PASS (with the implementer's own DRY flag)** | Both are imported from `loremaster.store._txn` inside `_reap_failure_outcome` and referenced, not redefined. The composite `isinstance(KeyError) or is_connection_error` is composed locally; `_txn` has no named predicate for it. The implementer flagged the needed `is_transport_fault(error)` extraction (`_txn.py` was outside its writable set). I concur; it is LOW, a ROUTING-IS-NOT-SHARING-adjacent composition. |

**Other reads:**
- **Honest wording:** the unverified list = opened ∩ minted ∩ not-marked-reaped. It includes opened-and-properly-dropped DBs, so the line says "could not verify … were removed", not "leaked". That is correct for a store that cannot be asked.
- **Abandoned-thread snapshot:** `dict(_MINTED_DATABASES)` copies once. The interpreter is GIL-enabled (`sys._is_gil_enabled()` → True, Python 3.14.7), so a C-level dict copy is atomic against the abandoned thread's value writes.
- **Reader DB under `muted`:** the forwarder forwards client→upstream bytes, so the store DOES receive the reap's sign-in. The SDK blocks on the swallowed sign-in reply before any `use()`, so no reader DB is created. Census delta 0 over 14 muted inner sessions confirms it (§6). A store that wedges AFTER `use()` would leave the reader unnamed: the session-end `use()` runs outside any armed per-test guard. That is a LOW residual (R6).

## §2 Mutations (tree M; `scripts/mutation_proof.py`; declared sets fixed BEFORE any run from `pytest --collect-only -q`)
- **Scope of every run:** `test_harness_database_lifecycle_486.py` + `test_surreal_harness.py` (126 tests).
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE`.
- Each run was gated (`GATE CLEAR` printed).
- Predictions were written to `predictions.md` at 19:18Z, before the first run; they are verbatim in §A.2.

| Mutation (exact text §A.2) | Declared RED | Result | Tail |
|---|---|---|---|
| (a) `if True:` in place of the opened∩minted gate | 4 × `test_a_name_only_session…[{refused,silent}-{n0,xdist-n2}]` | **PROOF HELD** | `4 failed, 122 passed in 58.59s`, restored byte-exact |
| (b) `reaper.join()`: the budget deleted, nothing else | (brief's expectation) `…reported_loudly[muted-n0]`, `[muted-xdist-n2]`. **My prediction: 0 reds.** | **SURVIVED: 126 passed in 68.50s.** The tool exited 4: "DECLARED RED but STAYED GREEN". My prediction held. | **R1:** `muted` ends at websockets' ~40 s keepalive (→ SDK `KeyError` → "unreachable"), `silent` at the 10 s open timeout, `refused` at once. Every constructed state is bounded by a DEPENDENCY default, so the build's own budget is deletable with all gates green. |
| (b′) inner sessions' reap never answers (`asyncio.sleep(10**6)` when the URL is not `:18000`) AND `reaper.join()` | 6 × `…reported_loudly[{refused,silent,muted}-{n0,xdist-n2}]` | **PROOF HELD** | `6 failed, 120 passed in 542.74s`. Each red is the named `did not END within 180s` fail (right reason, §A.2). |
| (b″) CONTROL: the same never-answering reap, budget INTACT | none | **126 passed in 98.21s**, rc 0 | The 30 s budget alone ends a true hang, with the loud line. (b′) vs (b″) isolates the budget as load-bearing. |
| (c) worker ships `json.dumps([])` for the unreaped report | 3 × `…reported_loudly[*-xdist-n2]` | **PROOF HELD** | `3 failed, 123 passed in 58.40s` |
| (d) a traceback-shaped line in place of `_unreaped_line` | 6 × `…reported_loudly[*]` | **PROOF HELD** | `6 failed, 120 passed in 58.49s` |
| (e) PROBE (not a contract mutation): worker-only `raise RuntimeError` just before the `workeroutput` write | — | `-n 2` → **rc 0, `1 passed`, 0 mentions of the raise**; `-n 0` → rc 0 (the probe is worker-only by construction) | **R3 = #538:** a hook failure outside the reap is the xdist false clear contract-486-r3 found, re-opened by any bug in the hook |

Restore: the conftest md5 is `6c3710d6ac198d0cc7df2b1942821f84` after every run. The `cp -a` content backup was `cmp`-identical before (b″) and (e), which were restored by `cp -a`.

## §3 F1 — `TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed` (19:17Z)
| tree | runner | result |
|---|---|---|
| H (plain HEAD) | `uv run --with pytest-timeout pytest -n 8 --timeout=300` | **1 failed** |
| H | `uv run pytest -n 8` (no `--with`) | **1 passed** |
| H | `uv run --with pytest-timeout pytest -n 0 --timeout=300` | **1 failed** |
| S (patched) | the same three runs | fail / pass / fail, identical |

- **Verdict:** pre-existing on HEAD, runner-caused, **NOT #486's** (identical on HEAD and patched).
- **Mechanism (MEDIUM, from reading, not instrumented):** `_is_installed_third_party` takes its installed roots from the RUNNING interpreter's `sysconfig` purelib/platlib. Under `uv run --with`, that is uv's overlay env, while the project's plugins live in `.venv` site-packages. So the live set is empty and `assert live` fails.
- **Filed as #537** (no prior finding matched; I queried the open set).
- **Currency would NOT see it as an orphan.** `scripts/gates.yaml` runs plain `uv run pytest`, where the test passes. It is visible only in agents' targeted tails, where every brief mandates `--with pytest-timeout` (CLAUDE.md §TEST SCOPE). It recurs as an "unattributed red" in every one.
- **Recommended fix:** declare `pytest-timeout` as a dev dependency. It is a mandated tool, but absent from `pyproject.toml` (awk: only `pytest-xdist` matches). That removes the overlay everywhere.

## §4 Hand-rolled vs packages
- **Bounded reap (`_reap_within_budget`, ~15 lines): a FINDING (R2), not JUSTIFIED as reasoned.**
  - The implementer read stdlib only. Its premise is that an in-loop timeout is not a bound, because cancelling the reap runs a `finally` whose awaits hit the same silent store.
  - That holds for `asyncio.timeout`, whose installed `Timeout.__aexit__` only converts after the body exits.
  - It is false for `anyio.fail_after`: anyio's cancel scope is level-triggered and re-cancels each await inside the scope.
  - anyio is a declared DIRECT dependency (`anyio>=4.5`; 4.13.0 installed).
  - Measured (probe §A.1) on a coroutine whose body AND `finally` both await forever:
    - `asyncio.timeout(0.5)` → still running at the probe's 3 s cap;
    - `anyio.fail_after(0.5)` → `TimeoutError` at **0.52 s**;
    - control: `asyncio.timeout` on a body with no hanging `finally` → 0.50 s.
  - The ThreadPoolExecutor reading is correct (`threading._register_atexit(_python_exit)` at installed `thread.py:37`).
  - So the declared dependency does the job in-loop, with no abandoned daemon thread.
  - The current code is CORRECT ((b′)/(b″)); this is a packages-over-hand-rolling finding, not a defect.
  - If replaced, the R1 pin covers both. A unit pin can drive `_reap_within_budget` (or its anyio successor) with a never-answering reap and a small budget, and assert it ends within budget + ε.
- **TCP forwarder (`_KillableStoreForwarder`): JUSTIFIED** (`keep_with_trigger`).
  - What I read:
    - `LoopbackPort` (held bind, `listen()`, `close()`; the module serves ASGI via uvicorn only, no raw forward);
    - `socketserver.TCPServer(server_address, RequestHandlerClass, bind_and_activate=True)`. It could carry the accept loop, via `bind_and_activate=False` + a socket swap, but not the substance.
  - **The substance is bespoke:**
    - the kill switch + ack handshake with the inner process;
    - three lost states;
    - `muted`'s forwarding of the HTTP upgrade response up to `\r\n\r\n`, then swallowing.
  - No installed package offers it. toxiproxy is absent and binds its own numbered port (the #466 race); socat likewise.
  - anyio/aiohttp are installed, but the outer test blocks on a subprocess, so an in-loop forwarder would need its own loop thread anyway.
  - It is test-local scaffolding, not a production seam.
  - Prose nit: contract-486-r3 calls it "~45 lines". It is 108 lines (class through `_pump`, including the docstring). LOW, R7.
  - **It satisfies the raw-listener guard:** `test_no_raw_listener_in_test_trees.py` gives **35 passed** on S under the plain runner (19:35Z). Under `--with`, its only red is F1 (§3).

## §5 Targeted run on the patched tree S (gate `GATE CLEAR 19:15:01Z MemAvailable=22GiB other_lore_pytest=0`)
- **Files:** `test_harness_database_lifecycle_486.py`, `test_surreal_harness.py`, `test_no_raw_listener_in_test_trees.py`, `test_retry_seam.py`, `test_memory_replay_fidelity_63b_ib.py`, `test_comms_wiring.py`, `test_ast_reach_helpers.py`.
- **Command:** `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE <files>`
```
FAILED loremaster/tests/test_no_raw_listener_in_test_trees.py::TestPluginPortFixturesAreForbidden::test_the_running_session_registers_no_plugin_fixture_the_derivation_missed
1 failed, 928 passed, 4 skipped, 1 warning in 114.61s (0:01:54)
RC=1
```
- **Red attribution:** 1/1 is F1 = #537, not #486 (§3). **0 #486-caused reds.**
- The 4 skips are in `test_ast_reach_helpers.py`, the file added to the implementer's set (879 + `test_ast_reach_helpers` = 933 collected). The pre-existing warning is at `test_retry_seam.py:3263` (`_empty_subscription` never awaited), as the implementer reported.
- **Outer loud lines:** an awk count of `LEAKED|unreachable at session end|session-end reap failed|Traceback (most recent` over the whole log = **0**.

## §6 Leak census — TEST store `ws://127.0.0.1:18000`, namespace `lore_test` only
- **Instrument:** coldaudit-486's census, extracted verbatim from `REPORT-coldaudit-486.md` §A.1 (committed `beecc68`). It refuses any non-`:18000` URL.

| when | total | harness-shaped (live pid) | bare hex32 | other |
|---|---|---|---|---|
| before (19:14Z) | 75 | 13 (0) | 60 | 2 |
| after targeted (19:17Z) | 75 | 13 (0) | 60 | 2 |
| after all mutations + (b″) (19:34Z) | 75 | 13 (0) | 60 | 2 |

- **Name-set diff before→after: added [], removed [] — delta 0.**
- This covers every run in this audit: the targeted run, the 6 mutation/control runs (126 tests each, 14 `muted` inner sessions among them), the six 180 s hung-and-killed inner sessions of (b′), and the small F1, guard and probe-(e) runs. The contract's `created_sink` cleanup on the hung path works.
- The 75 strays are the accepted D2 bound (coldaudit-486 R5).

## §7 Gates (S)
- `uv run ruff check .` → `All checks passed!`
- `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` (rc 1, the known #533 shape):
  - `typecheck    RED_ADJUDICATED — 83 residual(s), owned by: packet-58-contract … · packet-64b-i-contract …`
  - `ruff         GREEN`
  - `pytest       NOT_RUN — claimed by the manifest, never executed` (#533: the leg was deliberately excluded)
  - ⇒ **RED_ORPHANED 0** for typecheck and ruff.
- `scripts/typecheck.sh`: 83 `error:` lines. **0 of them name any of the 28 patched files** (an awk join on basenames, §A.5).

## RESIDUAL TABLE
| # | Class (lifted) | Severity | Owner | Trigger / next decision |
|---|---|---|---|---|
| R1 | **The D2 rider is half-pinned:** ∀ lost store state, the session ends within the BUILD's budget — but every constructed state is bounded by a dependency default, so deleting the build's budget passes 126/126 (mutation b). The missing state is the realistic one: a store whose transport stays alive (pings answered) while requests go unanswered, e.g. a wedged engine. | MEDIUM-LOW (a future-regression door, not a current defect) | #486 contract (tdd-light, one cell) | **Recommend fix now:** a unit pin drives the budget function with a never-answering reap and a small budget, and asserts it ends within budget + ε. Or a `wedged` forwarder state that passes websocket control frames. Re-open trigger if ruled a bound: any edit to `_reap_within_budget` / `_SESSION_END_REAP_BUDGET_SECONDS`. |
| R2 | **Packages:** the bespoke daemon-thread bound was chosen on a false generalisation. `anyio.fail_after` (a direct dependency) bounds the hanging-`finally` case in-loop (§4, measured). | LOW (maintenance; the current code is correct) | #486 implementer | D2: `replace` (recommended; carries R1's pin) or keep with a stated reason |
| R3 | **#538:** under xdist, a worker-side session-end hook failure OUTSIDE the reap is swallowed. Measured: rc 0, `1 passed`, no trace. The r3 fix enforces "worker failure reaches the controller" at the reap PATH; the STATE-level form is "every finished worker shipped its report keys". | MEDIUM (a false-clear door; needs a harness bug to open) | #486 implementer + contract | D1. Fix: the controller treats a worker whose `workeroutput` lacks `_UNREAPED_REPORT_WORKEROUTPUT_KEY` as a failed hook, plus a pin. `error` in `pytest_testnodedown` is probably None here (verify). |
| R4 | **#537 (F1):** the plugin-fixture live leg is red under the mandated `--with pytest-timeout` runner. It is invisible to currency, which runs plain `uv run pytest`. | LOW, NOT #486's (red on plain HEAD) | lead / test-file owner | D3: declare `pytest-timeout` as a dev dependency (recommended) |
| R5 | Non-transport session-end failures (`failed` line) are built but unpinned (implementer §Class) | LOW | #486 contract | One fake-`INFO`-shape cell, `-n 0` + xdist, if R1/R3 open a wave |
| R6 | A store wedging AFTER the reap's own `use()` would leave the reader DB unnamed in the loud line: the session-end `use()` is outside any armed guard. Not reachable in the constructed states (§1). | LOW | — | Re-open if a reader DB is ever found among strays |
| R7 | Prose: contract-486-r3 calls the forwarder "~45 lines" (it is 108). The `_txn` composite predicate is composed in conftest (implementer DRY flag: extract `is_transport_fault`). | LOW | whoever touches the files | None blocking |
| R8 | D-r3-1 consequence (inherited, stated in the conftest block comment): a higher-scoped fixture's minted DB is neither observed nor, since #534, reaped when no test opened a mint | accepted bound | operator | The first non-function-scoped fixture that mints |

## §A Instruments (pasted verbatim per brief-base §1; none committed)

### §A.1 anyio vs asyncio deadline probe (`uv run python anyio_probe.py`, in S)
```python
"""Does an in-loop deadline bound a coroutine whose `finally` ALSO awaits forever?
asyncio.timeout (edge-triggered, one cancel) vs anyio.fail_after (level-triggered cancel scope),
both on the asyncio backend. Control: the body alone (no hanging finally) under asyncio.timeout."""
import asyncio, time, anyio

async def reap_like(hang_in_finally: bool):
    try:
        await asyncio.sleep(10**6)          # the silent request
    finally:
        if hang_in_finally:
            await asyncio.sleep(10**6)      # close()/drop on the same silent store

async def under_asyncio(hang):
    async with asyncio.timeout(0.5):
        await reap_like(hang)

async def under_anyio(hang):
    with anyio.fail_after(0.5):
        await reap_like(hang)

async def measure(label, factory, hang, cap=3.0):
    started = time.monotonic()
    try:
        await asyncio.wait_for(factory(hang), cap)   # outer cap only so the probe itself ends
        outcome = "returned"
    except TimeoutError as error:
        outcome = f"TimeoutError({'outer cap' if time.monotonic()-started >= cap-0.05 else 'deadline'})"
    print(f"{label:28s} hang_in_finally={hang!s:5s} -> {outcome:28s} {time.monotonic()-started:.2f}s")

async def main():
    await measure("asyncio.timeout (control)", under_asyncio, False)
    await measure("asyncio.timeout", under_asyncio, True)
    await measure("anyio.fail_after", under_anyio, True)
print("anyio", anyio.__version__ if hasattr(anyio, "__version__") else "")
asyncio.run(main())
```
Output (2026-10-04 ~19:33Z):
```
asyncio.timeout (control)    hang_in_finally=False -> TimeoutError(deadline)       0.50s
asyncio.timeout              hang_in_finally=True  -> TimeoutError(outer cap)      3.00s
anyio.fail_after             hang_in_finally=True  -> TimeoutError(deadline)       0.52s
```

### §A.2 Mutation texts, predictions, and runner
Predictions file, written 19:18Z before any run:
```
(a) dial unconditionally (if True:)            -> RED = 4 cells (a) name_only [refused,silent]x[n0,xdist-n2]; nothing else.
(b) drop the bound (join() unbounded)           -> MY PREDICTION: 0 reds (muted ends ~40s via websockets keepalive -> KeyError -> "unreachable"; silent ends at 10s open timeout). Brief's expectation: silent/muted cells red. Declared to the tool: muted-n0, muted-xdist-n2 (expect the tool to report "declared but GREEN" if my prediction holds).
(b') drop the bound AND make the reap hang forever -> RED = 6 cells (c) [refused,silent,muted]x[n0,xdist-n2] via _InnerSessionHung at 180s.
(b'') CONTROL: reap hangs forever, bound intact -> 0 reds (budget TimeoutError -> unreachable line).
(c) worker ships an empty unreaped report       -> RED = 3 cells (c) *-xdist-n2.
(d) traceback-shaped text instead of the line   -> RED = 6 cells (c).
```
Anchors → replacements (each matched exactly once in `loremaster/tests/conftest.py`):
```
(a)  "    if _DATABASES_OPENED_THIS_SESSION & _MINTED_DATABASES.keys():\n"
  -> "    if True:  # MUTATION (a)\n"
(b)  "    reaper.join(budget_seconds)\n"
  -> "    reaper.join()  # MUTATION (b)\n"
(c)  "        workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY] = json.dumps(unreaped)\n"
  -> "        workeroutput[_UNREAPED_REPORT_WORKEROUTPUT_KEY] = json.dumps([])  # MUTATION (c)\n"
(d)  "            terminalreporter.write_line(_unreaped_line(outcome, records))\n"
  -> "            terminalreporter.write_line(f\"Traceback (most recent call last):\\n  {records!r}\")  # MUTATION (d)\n"
(e)  "    workeroutput = getattr(session.config, \"workeroutput\", None)\n"
  -> "    if getattr(session.config, \"workeroutput\", None) is not None:\n        raise RuntimeError(\"PROBE e: a bug in the worker-side session-end hook\")\n" + the anchor
```
(b′) anchor (block) → replacement; (b″) is the same with `reaper.join(budget_seconds)` kept:
```python
            asyncio.run(reap_minted_databases())
        except BaseException as error:  # handed to the caller, which classifies and reports it
            failures.append(error)

    reaper = threading.Thread(target=_reap, name="lore-session-end-reap", daemon=True)
    reaper.start()
    reaper.join(budget_seconds)
# ->
            asyncio.run(asyncio.sleep(10**6) if ":18000" not in __import__("_surreal_harness").surreal_url() else reap_minted_databases())  # MUTATION (b'): inner sessions' reap never answers
        except BaseException as error:  # handed to the caller, which classifies and reports it
            failures.append(error)

    reaper = threading.Thread(target=_reap, name="lore-session-end-reap", daemon=True)
    reaper.start()
    reaper.join()  # MUTATION (b'): and no bound
```
(The `:18000` condition confines the hang to the INNER sessions, which point at a forwarder. The outer session's own reap against the live store stays real, so the outer run cannot hang on itself.)

(b′) red reason: 4 of 6 failure messages read in full, each `Failed: the inner session against ws://127.0.0.1:<port>/rpc did not END within 180s — a session-end step is waiting on a TEST store that will never answer…`; 66 hang-mention lines in total.

Runner:
```bash
#!/usr/bin/env bash
SP=<scratchpad>
cd $SP/mut486b
for m in "$@"; do
  $SP/gate.sh || exit 3
  args=(); while read -r id; do args+=(--expect-red "$id"); done < $SP/mut/$m.expect
  echo "######## MUTATION $m $(date -u +%T)"
  uv run python scripts/mutation_proof.py --file loremaster/tests/conftest.py --anchor-file $SP/mut/$m.anchor --replacement-file $SP/mut/$m.repl "${args[@]}" -- \
    systemd-run --user --scope -q -p MemoryMax=16G -p MemorySwapMax=0 uv run --with pytest-timeout pytest -n 8 --timeout=300 -q -p no:cacheprovider -rfE \
    loremaster/tests/test_harness_database_lifecycle_486.py loremaster/tests/test_surreal_harness.py > $SP/mut/$m.out 2>&1
  echo "MUTATION $m proof rc=$?"; tail -25 $SP/mut/$m.out | awk '/PROOF|MISMATCH|unexpected|declared|GREEN|passed|failed|restor/'
  md5sum loremaster/tests/conftest.py
done
```
Gate (comm-keyed, so it cannot self-match a shell; brief-base §5 item 5):
```bash
for i in $(seq 1 900); do
  avail_kib=$(awk '/^MemAvailable:/{print $2}' /proc/meminfo)
  others=$(ps -eo pid,comm,args | awk '$2 ~ /^(python|pytest)/ && $0 ~ /pytest/ && $0 ~ /lore/' | wc -l)
  if [ "$avail_kib" -ge $((20*1024*1024)) ] && [ "$others" -eq 0 ]; then
    echo "GATE CLEAR $(date -u +%H:%M:%SZ) MemAvailable=$((avail_kib/1024/1024))GiB other_lore_pytest=0"; exit 0
  fi
  sleep 2
done
echo "GATE TIMEOUT"; exit 1
```

### §A.3 Module-level name diff (AST) and the round-3 harness delta
```python
"""Module-level bound names of a file (AST), for a HEAD-vs-patched diff."""
import ast, sys
def names(path):
    out=set()
    for node in ast.parse(open(path).read()).body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)): out.add(node.name)
        elif isinstance(node,(ast.Assign,ast.AnnAssign)):
            for t in (node.targets if isinstance(node,ast.Assign) else [node.target]):
                for n in ast.walk(t):
                    if isinstance(n,ast.Name): out.add(n.id)
        elif isinstance(node,(ast.Import,ast.ImportFrom)):
            for a in node.names: out.add((a.asname or a.name).split(".")[0])
    return out
h,s=names(sys.argv[1]),names(sys.argv[2])
print("added:",sorted(s-h)); print("removed:",sorted(h-s))
```
- **`_surreal_harness.py`, HEAD→S:** added `['Iterable', '_MINTED_DATABASES', '_RUN_STATEMENT_LABEL', 'reap_minted_databases']`; removed `[]`.
- **Round-3 delta:** a `difflib` comparison of the harness hunk in `486-FINAL.patch` vs `486-FINAL2.patch` gives 35 changed patch lines:
  - the module docstring's "Lifetime (#486)" paragraph;
  - the `_run_under_store_retry_seam` docstring's `_REACH_EXEMPT_FUNCTIONS` sentence;
  - `@@` offset headers.

  None of them is a binding.

### §A.4 Classifier probe (in S)
```python
import sys; sys.path.insert(0,"loremaster/tests")
import conftest as c
from loremaster.store._txn import TxnContentionExhaustedError
from loremaster.store.surreal import SurrealStoreError
for err in [ConnectionRefusedError(111,"x"), TimeoutError("no answer"), KeyError("uuid"), SurrealStoreError("bad shape"),
            TxnContentionExhaustedError.__new__(TxnContentionExhaustedError), RuntimeError("bug")]:
    print(type(err).__name__, c._reap_failure_outcome(err))
# -> ConnectionRefusedError unreachable · TimeoutError unreachable · KeyError unreachable
#    SurrealStoreError failed · TxnContentionExhaustedError failed · RuntimeError failed
```

### §A.5 Typecheck attribution
```bash
git status --short | awk '{print $2}' | sed 's#.*/##' > patched_basenames.txt
awk 'NR==FNR{b[$1]=1; next} /error:/{split($1,a,":"); f=a[1]; sub(/.*\//,"",f); if (f in b) {print; m++}} END{print "errors in patched files:", m+0}' patched_basenames.txt typecheck.log
# -> errors in patched files: 0   (of 83 error lines)
```

## Time log
- 19:13Z start.
- 19:15Z targeted run.
- 19:17Z F1 matrix; filed #537.
- 19:18–19:32Z mutations a, b, c, d, b′.
- 19:32Z (b″).
- 19:35Z probe (e) and the plain guard run; filed #538; annotated #534.
- ~19:45Z report.
