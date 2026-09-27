brief-base v16 read · brief project v7 read

# REPORT-contract-466-d1 — #466 audit delta (F1 · F2 · C1 · C2 · C3 · F12), tdd-light Phase 1

## SUMMARY BLOCK
- **state:** done-with-deviations
- **deviations:** (1) C1 and C2 cannot be RED at `43b8d16` by nature (a dead-entry pin and an environment-premise pin hold today); both are mutation-proven instead (§C1, §C2). (2) C3 was extended from the audit's aiohttp item to a DERIVED reach pin (the brief invited it); it adds one RED (`[anyio]`) and ~4.5–8 s of guard time. The lead may drop it by deleting one class (§C3b). (3) The F2 names need a STUB phase: until then `test_loopback_serving.py` fails collection with `ImportError: DEFAULT_SHUTDOWN_TIMEOUT_S` (§Stub).
- **Packages considered:** F12 tree-kill: stdlib `subprocess.Popen(start_new_session=True)` + `os.killpg`, proven by the reference build; `psutil` is keep_with_trigger (not installed, not read; trigger: a descendant that leaves the process group). F1 injection: stdlib `signal.setitimer`; pytest-timeout is not installed and cannot target a mid-wait moment with a known exception identity. F2: PEP 678 `add_note` (stdlib, used by the reference build) · C3: `importlib.metadata.packages_distributions` + `Distribution.files` (stdlib, measured) + **`packaging.utils.canonicalize_name` REPLACES my hand-rolled PEP 503 regex** (read the installed 26.2 signature; packaging is a hard dependency of pytest) · C2: `importlib.util.find_spec`.
- **Odoo-20 portability:** n/a — no Odoo seam touched
- **Reuse ledger:** 18 new private symbols, all dispositioned (§DRY). The count was DERIVED from `git diff -U0` (an awk over added `def _` / `class _` / `_NAME =` lines): 14 helpers or types plus 4 contract-data constants. One is REUSED (`_import_aliases` backs `_imported_top_level_modules`), one hand-roll was package-REPLACED and deleted (`canonicalize_name`), and the rest are HAND-ROLLED with the query that found nothing fitting.
- **Graded:** none. This report authors a contract and grades no one else's artifact. Base `43b8d16` (in-scope files byte-identical to `e6e17d8`).
- **decisions-needed:**
  - **(a) F2 reading.** I picked raise-on-clean-exit plus note-on-failing-exit. The alternative, warn + ERROR log only, is written in §F2. Confirm.
  - **(b) C3b.** Keep the derived-reach class (costs ~4.5–8 s) or drop it?
  - **(c) Surfaced door.** pytest-asyncio's `unused_tcp_port` fixture is a door no call-keyed scan can see. Rule it in or out (§Surfaced-1).
  - **(d) serve_http teardown.** With a stuck handler it hangs unbounded (§Surfaced-2). Fix now, or ledger it?
  - **(e) F2 default budget.** The real wire-lifespan teardown time has never been measured against the 5 s default (§Surfaced-3).
- **receipts:** declared-vs-observed RED §R1–§R3 · satisfiability §R4 · 17 mutation proofs §R5 · stability §R6 · typecheck §R7 · instruments pasted verbatim in Appendix A–E.

---

## Capability check (brief-base §4)
- **Demanded:** lore-first. **Have:** it works. `lore_search` failed 3/3 when the calls ran in parallel, with a bare-UUID error, and worked singly afterwards. Filed as **finding #498**.
- **Demanded:** grep/rg are hook-blocked. **Did:** used `awk` for the textual seams, stated each time. No structure question needed a fallback.
- **Demanded:** kill by PID, never touch `:18500`. **Did:** every test process is reaped by PID after a marker check. No store was touched.
- **Demanded:** scoped runs only. **Did:** complied. Mutation and reference builds ran in a `scratch_copy.sh` copy with asserted provenance: `loremaster.testing.loopback.__file__` = `…/scratchpad/scr466/loremaster/loremaster/testing/loopback.py`.

## Files (writable set only; `git add` nothing)
| file | change (pure insertions — `git diff -U0` shows zero removed lines, so no existing pin changed and no DUAL-comment is owed) |
|---|---|
| `loremaster/tests/test_loopback_serving.py` | +337: F1, F2, C2 classes and probes. `_RecordingApp` gains `shutdown_gate`, `shutdown_delay_s` and `loop_classes`, all defaulting to absent, so every original fixture is unchanged. |
| `loremaster/tests/test_no_raw_listener_in_test_trees.py` | +246: C1, C3a and C3b classes, plus `_DEPENDENCY_LISTENER_VERBS` and `_PLANTED_BY_SERVER_DISTRIBUTION`. |
| `scripts/test_concurrent_wire_acceptance.py` | +152: F12 class and tree probes. |

---

## §F1 — an unexpected BaseException in the startup wait (`TestAnInterruptedStartupLeavesNothingBehind`)
**Contract.** Any exception that interrupts `serve_asgi`'s startup wait must:
- propagate **unchanged**: the same object, not wrapped, not replaced;
- leave **no logging handler attached anywhere** in the process;
- leave **no server thread alive** once the blocked lifespan is released;
- leave a **caller-passed port unserved**: no server comes up on the caller's socket.

**Injection is receiver-blind.** A `SIGALRM` handler raises in the main thread 0.3 s into a wait whose lifespan is gated shut. This is the real door (pytest-timeout's signal method, Ctrl-C). A join, an `Event.wait` and a `sleep` are all interruptible on POSIX, so the pin does not bind the helper to `Thread.join`.

**Parametrised types:**
- `_InjectedInterrupt(BaseException)`, the pytest-timeout shape. It discriminates an `except Exception` build (W1).
- `KeyboardInterrupt`.

**Two tests:**
- **Owned port.** RED today because the handler leaks.
- **Passed port** (the sharp form). The caller still holds the socket, so on `43b8d16` uvicorn comes up and serves it forever from an unstoppable thread.

## §F2 — shutdown overrun is LOUD (`TestAShutdownOverrunIsLoud`)
**Decision (the brief's fork).** On a **clean** exit, raise `ServerShutdownTimeout(RuntimeError)` with `.host`, `.port` and `.shutdown_timeout_s`; the message names `host:port` and says "shutdown". When the body is **already raising**, never mask: its own exception propagates (same object) and carries the overrun as a PEP 678 `add_note` naming `host:port`. The budget is `serve_asgi(shutdown_timeout_s=…)`, defaulting to the new public `DEFAULT_SHUTDOWN_TIMEOUT_S` (value measure-then-tune).

**Why this and not reading B (pytest-visible warning + ERROR log, always):**
- **Trust doctrine / hard definition.** A test whose teardown hung and which reads `N passed` is a response a consumer acts on without checking, wrong in a way it did not name. A warning lands in a summary block an agent reading the pass-count skips, so it is a false clear. A raise turns it red.
- **Masking.** Raising unconditionally from `finally` would replace the test's own failure as the headline, so the note path exists for exactly that case.
- **What B would change.** Reading B would flip W5 (a log-only build) from wrong to right; that is the only pin difference. I judged A sound on both axes the brief named. It remains an operator-visible decision, recorded here as decisions-needed (a).

**Interface pins:**
- `ServerShutdownTimeout` is **not** a `ServerStartError` subclass, so a start-retry `except` cannot swallow a teardown overrun.
- The fixture arithmetic is pinned: `SHORT (0.5) + GRACE (2.0) < DEFAULT_SHUTDOWN_TIMEOUT_S`. My first draft had grace 5.0, and a build ignoring the passed budget (joining the old fixed 5 s) passed the elapsed bound (5.0 ≤ 5.5). Found by asking "what wrong build still passes?" and proven by W10.

**Controls:**
- A slow in-budget shutdown does not raise.
- A failing body with a prompt shutdown gets **no** note (W6).

## §C1 — `_CONTRACT_FILES` is held live (`TestTheContractFileExclusionIsLive`)
- **Pin.** Every entry is a file the scan actually read (stronger than "exists": it also catches an entry outside testpaths), via `_stale_entries(entries, scanned_paths)`.
- **Positive control.** The same function, fed a planted renamed entry, reports it.
- **Green at birth by nature.** The defect was the pin's absence, not a stale entry. Proven by W13 (rename an entry → live pin RED) and W14 (checker returns `[]` → control RED).

## §C2 — the bind spy's premise (`TestTheBindSpyPremiseHolds`)
**Decision: pin the premise; do NOT force `loop="asyncio"` in the helper.**
- Production `LoreServer` runs `uvicorn.Config(app, host=…, port=…, log_level="info")` with no `loop`, so it runs on the default `"auto"` (read with `awk` at `server.py`, symbol `LoreServer.run`; not grep, #473).
- Forcing asyncio only in the test helper would, the day `uvicorn[standard]` brings uvloop, make the wire harness test a loop production no longer runs. That is THE TEST ENVIRONMENT IS A FICTION class (#131).
- The pin reddens with a re-open message telling the reader to decide deliberately: verify the spy under uvloop, or force the loop in BOTH places.

**Two legs:**
- `find_spec("uvloop") is None`.
- **Behavioural.** The served app runs on a loop whose class module is `asyncio.*`. This catches any door to a foreign loop (an extra, a policy, a plugin), not only the one `find_spec` sees.

**Proof.** Green at birth (premise holds at `43b8d16`). A fake `uvloop` on `PYTHONPATH` (Appendix E) reddens exactly the two declared pins (§R5).

## §C3 — aiohttp and the derived server-library reach
**C3a (`TestTheDetectorSeesAiohttpListeners`)**
- **Must be flagged:** planted `web.run_app`, `web.TCPSite`, `aiohttp.web.UnixSite`, `test_utils.TestServer`, and `test_utils.unused_port()`. The last is #466's own bind→read→close race shipped inside a dependency; I read the installed source.
- **Must NOT be flagged:** `aiohttp.ClientSession()`, `web.Application()`, `web.Response(…)`, `web.json_response(…)`. This kills the whole-namespace build (W11).
- **Deliberately unruled:** `AppRunner` and `SockSite` are in neither list, as stated in the test's comment.

**C3b (`TestTheServerCapableDependenciesAreDerived`) — reach as a checked variable (INSTRUMENT 0)**
- **The derivation.** Server-capable = an installed distribution that (i) provides a module some test-tree file imports (read through the detector's own `_import_aliases`) and (ii) calls a listener verb in its own source. The verb oracle is `_DEPENDENCY_LISTENER_VERBS`: asyncio's 4 plus anyio's 2, kept deliberately independent of the detector's constant.
- **Measured at `43b8d16`:** {anyio, uvicorn}.
- **The check.** Derived must equal the keys of `_PLANTED_BY_SERVER_DISTRIBUTION`, and each planted spelling must be flagged. anyio's `create_tcp_listener` is not flagged today, so that is the RED.
- **Honest anyio clients are not flagged:** `connect_tcp`, `create_task_group`.

Cost measurements that shaped C3b:
| derivation variant | cost | set it produced |
|---|---|---|
| whole site-packages, full AST parse | 32.7 s | — |
| bytes-prefiltered | 6.0 s | also drags in 5 internal-only packages (execnet, joblib, kubernetes, langsmith, mypy) |
| test-import-scoped | ~4.5 s | {anyio, uvicorn} |

In the suite, under `-n 8`, the derivation test measured 8.26 s.

**Named bounds (in the class docstring):**
1. Sync `.bind`+`.listen` servers (werkzeug-style) are not derived. A `.bind` oracle drowns in `Signature.bind` noise. Re-open trigger: the first such library imported by a test.
2. An un-imported library is not derived until it is imported. websockets is installed and verb-capable but not imported at `43b8d16`, so it is left to this pin.
3. A fixture-name door (see §Surfaced-1).

## §F12 — a timed-out session takes its whole tree (`TestATimedOutSessionTakesItsWholeTreeWithIt`)
**The fake tree.** `session_argv` is replaced on the instance by a 3-deep tree: session → worker → worker's child. That is one level deeper than xdist, so a build that kills one level below still fails. Every member records its pid atomically and sleeps 120 s, and a uuid marker in argv rules out a recycled pid.

**Asserted after `run_round(1)` with a 3 s timeout:**
- 6/6 members recorded (non-vacuity);
- both outcomes timed out and the round is not green;
- the round returned within timeout + 15 s (it did not wait on the tree);
- no member is alive 5 s later.

**Positive control.** The liveness probe sees a live tree and sees its death.

**Cleanup.** A `finally` SIGKILLs marker-checked survivors by pid. Verified: `ps` shows 0 leaked `tree466-` processes after every run.

---

## Adversarial pre-flight → coverage map
| realistic breaking input / wrong build | covered by |
|---|---|
| cleanup `except Exception` (misses KeyboardInterrupt / pytest-timeout `Failed`) | F1 `_InjectedInterrupt` param · W1 |
| cleanup detaches the handler but does not abandon (thread keeps the caller's socket) | F1 passed-port test · W2 |
| interrupt wrapped or replaced by a ServerStartError | F1 identity (`is raised[0]`) · W3 |
| interrupt lands outside the wait (probe mistimed) | startup gated shut + 60 s budget; injection count asserted == 1 |
| handler leaked on a DIFFERENT logger than today's | receiver-blind snapshot of every logger's handlers |
| thread found by name / structure | receiver-blind new-thread set |
| overrun silent on a clean exit (old behaviour) | F2 clean-exit test (stub RED) |
| overrun log-only | W5 |
| overrun raise MASKS the body's failure | F2 failing-body identity · W4 |
| overrun silent on the failing path | F2 note check (stub RED) |
| note on every failure (noise) | prompt-shutdown control · W6 |
| wrong unit: budget in ms (returns immediately) | lower elapsed bound 0.9 × budget |
| wrong scale: passed budget ignored, default used | pinned arithmetic + upper bound · W10 |
| message omits address | W8 |
| handler leaked on the overrun path | W9 |
| raise on every exit | slow-shutdown positive control. The pre-existing suite also reddens wholesale; not run as a proof because its declared set would be ~10 pins long (stated, not hidden) |
| zero / negative budget | **scoped out**: the original contract validates no budget value (neither startup); surfaced as a gap for both, not ruled here |
| C1 renamed contract file | W13 |
| C1 checker vacuous | W14 |
| C2 uvloop via `find_spec` / via another door | both legs · fake-uvloop proof |
| C3 aiohttp partial coverage | W12 |
| C3 over-broad namespace | W11 |
| C3 derived library without a planted spelling | W15 |
| C3 blind verb oracle | W16 (+ its own positive control) |
| C3 dead planted entry (no longer derived) | same equality assertion, `dead` leg |
| F12 kill only the direct child (today) | `43b8d16` RED |
| F12 no process group created | W17 |
| F12 kill one level below | depth-3 tree (stated; an extra wrong build was not run) |
| F12 descendant escapes via `setsid` | **bound, not pinned**: xdist does not setsid; psutil trigger in the Packages line |
| F12 pid reuse / zombie | marker-checked `/proc/<pid>/cmdline` (zombie reads empty) |
| F12 tree not built before the timeout (slow box) | non-vacuity `6 == 2 × 3` |

## Realism & independence
- ☑ **Production-realistic inputs.** Real uvicorn over real TCP. Real OS process trees. The real signal door. aiohttp spellings from the installed API: `unused_port` source read. Budgets are short but proven discriminating.
- ☑ **Independent expected values.** Every expectation comes from the audit's §1/§2 text, the trust doctrine, or kernel facts (pid alive / dead); none from a helper formula.
- ☑ **Seam coverage.** Main-thread signal → helper wait → uvicorn thread. Driver → subprocess tree (real processes, no mocks). Guard → installed package metadata and source (real site-packages).
- ☑ **Magnitude bounds.** Elapsed windows bounded on both sides for F2, one side for F12. Member count equality 6. A derived set that is non-empty.
- ☑ **Shared conventions.** `DEFAULT_SHUTDOWN_TIMEOUT_S` is imported, not restated. `CONCURRENT_SESSIONS` comes from the driver. Logger identity is not hardcoded (receiver-blind). testpaths and imports come from the shared parser. PEP 503 names come from `packaging`.
- ☐ **Hostile fixtures for rendered stored text.** Not applicable: no unit renders stored free text (the guard renders source `file:line`, which is not stored text).
- ☐ **Input-accounting helper.** Not applicable: no unit transforms a caller-supplied collection into emitted items. The C3b set equality is two-directional (`unshown` and `dead`), which is the accounting analogue for its keys.

## Replaced-behaviour adjudication (no Phase-0 inventory was supplied; enumerated from the audit)
| old behaviour | verdict |
|---|---|
| `stop()` returns silently when the join overruns | **Old-bug** (audit F2 "old-bug-preserved"). NOT re-pinned; replaced by §F2. |
| startup wait cleans up only on the 2 named raises | **Old-bug** (F1). Replaced. |
| `subprocess.run(timeout=)` kills only the direct child | **Old-bug** (F12). Replaced. |
| exit waits a fixed `_SHUTDOWN_JOIN_TIMEOUT_S` = 5 s | **Preserved-with-pin at the interface level only**: the default stays a positive finite number (measure-then-tune), now public as `DEFAULT_SHUTDOWN_TIMEOUT_S`. The value is **spec-silent** → decisions-needed (e). |

**Deliberately-dropped list:** none. **Spec-silent list:** the default shutdown budget value (e).

---

## Stub expectations (tdd-light STUB phase — behaviour-neutral)
The stub must make `test_loopback_serving.py` collect, and nothing more. Receipt: Appendix B, 77 lines.
- **Constant.** Add `DEFAULT_SHUTDOWN_TIMEOUT_S: float` (5.0 keeps today's behaviour).
- **Exception class.** Add `ServerShutdownTimeout(RuntimeError)` with `__init__(message, *, host, port, shutdown_timeout_s)`.
- **Parameter.** `serve_asgi(..., shutdown_timeout_s=DEFAULT_SHUTDOWN_TIMEOUT_S)` is accepted and used as the join timeout, **with no raise and no note**.
- **Exports.** Both names are added to `__all__`.

With that stub, the observed RED set is exactly the declared six (§R2).

**Builder scope flag.** C3 and C3b go GREEN only by extending the guard's **detector section** (`_LISTENER_FUNCTIONS` / `_LISTENER_METHODS` / `_listener_primitive`), which lives in `test_no_raw_listener_in_test_trees.py` itself.
- The builder's writable set must include that file, **restricted to the detector section above the d1 classes**.
- The planted strings, `_PLANTED_BY_SERVER_DISTRIBUTION` and every test body are contract, not to be edited.

The F12 fix is in `scripts/concurrent_wire_acceptance.py`; the F1 and F2 fixes are in `loremaster/loremaster/testing/loopback.py`.

---

## Receipts
**§R1 — guard, real tree `43b8d16`.**
- The declared set was written to a file from `--collect-only` ids before the run.
- Run: `2 failed, 18 passed in 12.08s`, diff vs declared IDENTICAL. Re-run after the DRY edits: `2 failed, 18 passed in 12.47s`, IDENTICAL.
- RED reasons:
  - `flagged lines [] != expected [5, 6, 7, 8, 9]`
  - `the detector does not see anyio's listener … assert []`

**§R2 — loopback, scratch copy + stub only.**
- Declared 6 (4 × F1, 2 × F2), checked collected.
- Run: `6 failed, 32 passed, 14 warnings in 8.23s`, IDENTICAL.
- RED reasons:
  - `DID NOT RAISE <class '…ServerShutdownTimeout'>`
  - `the interrupted start left a logging handler attached …` (×2)
  - `the overrun is SILENT on the failing path — no note naming the address: ''`
  - `the interrupted start left server thread(s) running on the caller's held port: ['serve_asgi 127.0.0.1:48781']` (×2)
- The 32 pre-existing plus control pins stayed green on the stub. The 14 warnings are pre-existing `websockets.legacy` / `WebSocketServerProtocol` DeprecationWarnings from uvicorn's import. They are unrelated and also present before d1.

**§R3 — driver, real tree `43b8d16`.**
- Run: `1 failed, 21 passed in 8.51s`, IDENTICAL to declared.
- RED reason: `4 of 6 members of the timed-out session trees are still alive 5.0s after the round: […] — orphaned xdist workers (F12)`. The two direct children died; all four descendants survived: the defect exactly.

**§R4 — satisfiability (reference builds in scratch, Appendix C).**
- Loopback: `38 passed` in 5/5 `-n 8` runs + 1 serial.
- Guard: `20 passed`.
- Driver: `22 passed`.
- **It caught one defect in my own contract:** the hang test read `app.events` at the instant of releasing the gate, racing the lifespan's 50 ms poll. Fixed with a bounded wait before these receipts.

**§R5 — mutation proofs (17/17), via `scripts/mutation_proof.py` (declared-before-run, diffed both ways, byte-exact restore).**
- Battery (Appendix D): W1–W6, W8–W17 all `PROVEN`.
- **W3 caveat.** W3 first FAILED: *my* mutation was malformed, since it also re-wrapped the named start errors. Three pre-existing pins reddened, and the 4 declared F1 pins did fire. Re-formed to wrap only non-`ServerStartError` interrupts → `PROVEN`.
- Guard mutations W11–W16 were re-proven after the DRY edits (6/6).
- C2 fake-uvloop: `2 failed, 36 passed`, IDENTICAL to the declared pair; message `RE-OPEN (#466 C2): uvloop is now importable …`.
- md5 of every reference file equals its backup after the battery.
- W7 (raise on every exit) was not run; the reason is in the pre-flight table.

**§R6 — stability (reference build).**
- The 11 d1 loopback pins (signal- and timing-based): **20/20 runs green** under `-n 8`, which shows xdist workers run tests on the main thread (the probe asserts it).
- F12 pins: 5/5 runs green, 0 leaked processes.

**§R7 — typecheck (`scripts/typecheck.sh` in scratch, where the reference names resolve).**
- **0 errors in the three d1 files.** The legs are red for 44 errors (43 across 18 loremaster files, plus 1 in scripts), **none mine**.
- Every error file is another packet's in-flight contract, listed individually (all are pre-existing tree state in the shared checkout, not caused by d1):
  - **Modified (` M`):**
    - `loremaster/tests/test_blocks_edge.py` (1)
    - `…/test_fixwave_a19a_63c_i_a.py` (2)
    - `…/test_fixwave_a19b_63c_i_a.py` (2)
    - `…/test_task_claimable_partition_58.py` (1)
    - `…/test_task_guarded_shell_58.py` (1)
    - `…/test_task_read_surface.py` (1)
    - `scripts/test_forgery_door_sweep.py` (1: `loremaster.tasks has no attribute SupersedeResult`)
  - **Untracked (`??`):**
    - `…/test_findings_enforcement_64b.py` (1)
    - `…/test_findings_governance_64b.py` (2)
    - `…/test_findings_identity_64b.py` (4)
    - `…/test_findings_migrate_64b.py` (1)
    - `…/test_findings_schema_64b.py` (1)
    - `…/test_fixwave_a28_63c_i_a.py` (2)
    - `…/test_governed_substrate_64b.py` (6)
    - `…/test_reanchor_58_r2_am2.py` (2)
    - `…/test_reanchor_58_r2_probes.py` (3)
    - `…/test_reanchor_58_r2_rulings.py` (5)
    - `…/test_reanchor_58_r2_scale.py` (1)
  - **Tracked and CLEAN** (committed with RED type errors — a committed contract awaiting its build?):
    - `…/test_supersede_reanchor_58.py` (7)
- ruff check + format: clean on all three files.

---

## DRY ledger (brief-base §6)
| new symbol | lore query | returned | disposition |
|---|---|---|---|
| `_interrupt_main_thread_after` | "signal.setitimer SIGALRM handler raise in main thread during a test" | test_scout's loop signal-registration spy | HAND-ROLLED — the spy observes registration and cannot raise mid-wait |
| `_attached_logging_handlers`, `_threads_still_alive_after` | (covered by the same probe-helper search; no logging- or thread-leak helper surfaced) | — | HAND-ROLLED, test-local; ⚠ no dedicated query was run for these two, so this is stated rather than claimed |
| `_InjectedInterrupt`, `_BodyFailure` | n/a (trivial test types) | — | HAND-ROLLED |
| `_stale_entries` | (inspected the guard's existing `_EXEMPT_SITES` dead-entry pin) | inline logic with a different predicate (live site, not scanned file) | HAND-ROLLED — different predicate; existing pin not refactored, so it stays unchanged |
| `_imported_top_level_modules` | read the guard's `_import_aliases` | same import resolution | **REUSED `_import_aliases`** (body is now one line over it; bound: two imports binding the SAME alias in one file keep only the last) |
| `_canonical` | Packages-over-hand-rolling | `packaging.utils.canonicalize_name` | **REPLACED by the package**; symbol deleted |
| `_calls_a_listener_verb`, `_server_capable_imported_distributions` | "kill process tree…" and site-packages probes (Appendix A) | nothing in-repo derives dependency capability | HAND-ROLLED |
| `_DEPENDENCY_LISTENER_VERBS`, `_PLANTED_BY_SERVER_DISTRIBUTION`, `_UNEXPECTED_INTERRUPTS` | n/a — contract DATA (an oracle set, a planted map, a param list), not policy | — | HAND-ROLLED as contract data. The verb oracle is deliberately NOT the detector's `_LISTENER_METHODS`: reusing it would make reach derived == derived. |
| `_is_live_tree_member`, `_tree_pids`, `_survivors_after`, `_reap_by_pid`, `_tree_session_argv`, `_TREE_MEMBER_SCRIPT` | "kill process tree on subprocess timeout" · "start_new_session os.killpg process group descendants orphan pytest xdist workers" | only fake `kill(query_uuid)` stubs; a memory about in-process agents | HAND-ROLLED — no process-tree helper exists (the "kill the process TREE" memory landmine has no function behind it; a candidate for `lorerunes` if the F12 fix wants it shared) |

---

## Surfaced (outside the six; not decided by me)
1. **pytest-asyncio's `unused_tcp_port` / `unused_tcp_port_factory` fixtures.** pytest-asyncio is installed, `asyncio_mode = "auto"`, and the plugin source contains `unused_tcp_port` (measured).
   - They are #466's bind→close→number race, requested as a fixture PARAMETER: no call exists, so no call-keyed scan sees it.
   - aiohttp's pytest plugin (`aiohttp_unused_port`, `aiohttp_server`) is the same shape if it is ever loaded.
   - **Proposed pin, ready to add:** a planted `def test_x(unused_tcp_port): ...` must be flagged (a FunctionDef-argument leg).
   - Operator scope ruling needed: decisions-needed (c).
2. **`serve_http` teardown can hang UNBOUNDED.** `server.shutdown()` waits, with no timeout, for `serve_forever` to exit, and a stuck `HTTPServer` request handler blocks it. The F2 class exists here in a worse form: a hang, not a silent pass. No pytest-timeout is installed, so the session hangs. decisions-needed (d).
3. **F2 will turn a slow REAL teardown red.** `test_migration_wire.py`'s real lifespan (store close, watchers) has never been timed against the 5 s default. That is correct by the trust doctrine, but unmeasured.
   - Measure-then-tune decision point: the builder's GREEN run of the acceptance driver (`scripts/concurrent_wire_acceptance.py`). Any `ServerShutdownTimeout` there is the data.
   - Owner: the lead. decisions-needed (e).
4. **Neither budget is validated.** `startup_timeout_s` and `shutdown_timeout_s` accept 0, negative or NaN unvalidated, a pre-existing gap in the original contract. Not pinned; surfaced.
5. **Driver edges.** `ConcurrentPairDriver.expected_passed()` also uses `subprocess.run(timeout=)`. `--collect-only` spawns no xdist workers, so the exposure is low, but it is the same orphan class. A Ctrl-C of the driver mid-round also leaves both sessions and their workers running. Neither is pinned.
6. **Finding #498** (filed): lore_search batch failure with a bare-UUID error.
7. **Typecheck red** in 19 other-packet files (§R7): their owners should know. `test_supersede_reanchor_58.py` is COMMITTED with 7 type errors.

---

## Appendix A — derivation probe (the measurement behind C3b's cost table; verbatim)
```python
"""Measure v3: server-capable distributions that some test-tree file IMPORTS (verb-keyed)."""
import ast, sys, time
from pathlib import Path
from importlib import metadata
sys.path.insert(0, "loremaster/tests")
t=time.monotonic()
from _logging_fixtures import parse_production_trees
import tomllib
trees = parse_production_trees(include_scripts=True, include_skills=True, include_tests=True, include_testpaths=True)
testpaths = tomllib.loads(Path("pyproject.toml").read_text())["tool"]["pytest"]["ini_options"]["testpaths"]
trees = {p:t_ for p,t_ in trees.items() if any(p==r or p.startswith(r.rstrip('/')+'/') for r in testpaths)}
t1=time.monotonic()
tops=set()
for tree in trees.values():
    for n in ast.walk(tree):
        if isinstance(n,ast.Import):
            tops.update(a.name.split('.')[0] for a in n.names)
        elif isinstance(n,ast.ImportFrom) and n.module and n.level==0:
            tops.add(n.module.split('.')[0])
pd=metadata.packages_distributions()
dists={d for top in tops for d in pd.get(top,[])}
VERBS={"create_server","create_unix_server","start_server","start_unix_server","create_tcp_listener","create_unix_listener"}
TOK=tuple(v.encode() for v in VERBS)
hits={}
for dn in sorted(dists):
    d=metadata.distribution(dn)
    for f in d.files or []:
        if f.suffix!=".py": continue
        raw=Path(d.locate_file(f)).read_bytes()
        if not any(x in raw for x in TOK): continue
        for n in ast.walk(ast.parse(raw)):
            if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr in VERBS:
                hits.setdefault(dn,set()).add(str(f))
print(f"{len(trees)} test files; parse {t1-t:.1f}s; derive {time.monotonic()-t1:.2f}s")
print("imported dists:", len(dists), sorted(dists))
print("server-capable imported:", {k:sorted(v) for k,v in hits.items()})
```
Output at `43b8d16`: `338 test files; parse 2.9s; derive 4.50s` · 24 imported dists · `server-capable imported: {'anyio': ['anyio/_core/_sockets.py'], 'uvicorn': ['uvicorn/server.py']}`.

## Appendix B — STUB (behaviour-neutral; diff vs `43b8d16`; verbatim)
```diff
diff --git a/loremaster/loremaster/testing/loopback.py b/loremaster/loremaster/testing/loopback.py
index 31bee13..54de10c 100644
--- a/loremaster/loremaster/testing/loopback.py
+++ b/loremaster/loremaster/testing/loopback.py
@@ -42,6 +42,9 @@ pass ``startup_timeout_s`` to override it without editing this module."""
 KERNEL_ASSIGNED_PORT: int = 0
 """The port number that asks the kernel for an ephemeral port — the ONLY port ever bound here."""
 
+DEFAULT_SHUTDOWN_TIMEOUT_S: float = 5.0
+"""STUB (d1): how long exit waits for the lifespan shutdown."""
+
 _STARTUP_POLL_S: float = 0.02
 """How often the startup wait re-checks ``started`` / thread death. Small, so a crash is named
 promptly rather than when the budget expires."""
@@ -125,6 +128,16 @@ class ServerThreadCrashed(ServerStartError):
     """
 
 
+class ServerShutdownTimeout(RuntimeError):
+    """STUB (d1): a started server's lifespan shutdown overran its budget."""
+
+    def __init__(self, message: str, *, host: str, port: int, shutdown_timeout_s: float) -> None:
+        super().__init__(message)
+        self.host = host
+        self.port = port
+        self.shutdown_timeout_s = shutdown_timeout_s
+
+
 @dataclass(frozen=True)
 class ServedEndpoint:
     """Where a started test server is answering.
@@ -318,10 +331,10 @@ class _UvicornServerThread:
             # A join returns the moment the thread dies, so a crash is named within one poll.
             self._thread.join(timeout=min(_STARTUP_POLL_S, remaining_s))
 
-    def stop(self) -> None:
+    def stop(self, shutdown_timeout_s: float = _SHUTDOWN_JOIN_TIMEOUT_S) -> None:
         """Drive a real lifespan shutdown and wait (bounded) for the thread to finish."""
         self._server.should_exit = True
-        self._thread.join(timeout=_SHUTDOWN_JOIN_TIMEOUT_S)
+        self._thread.join(timeout=shutdown_timeout_s)
         self._detach_capture()
 
     def _abandon(self) -> None:
@@ -351,6 +364,7 @@ def serve_asgi(
     *,
     port: LoopbackPort | None = None,
     startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S,
+    shutdown_timeout_s: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
 ) -> Iterator[ServedEndpoint]:
     """Serve ``app`` under a real uvicorn in a thread, FROM a pre-bound socket.
 
@@ -380,7 +394,7 @@ def serve_asgi(
         try:
             yield held.served_endpoint()
         finally:
-            server_thread.stop()
+            server_thread.stop(shutdown_timeout_s)
 
 
 def _http_server_on(
@@ -443,6 +457,7 @@ def serve_http(
 
 
 __all__ = [
+    "DEFAULT_SHUTDOWN_TIMEOUT_S",
     "DEFAULT_STARTUP_TIMEOUT_S",
     "KERNEL_ASSIGNED_PORT",
     "LOOPBACK_HOST",
@@ -450,6 +465,7 @@ __all__ = [
     "LoopbackPort",
     "ServedEndpoint",
     "ServerBindError",
+    "ServerShutdownTimeout",
     "ServerStartError",
     "ServerStartupTimeout",
     "ServerThreadCrashed",
```

## Appendix C — SATISFIABILITY reference builds (diff vs `43b8d16`; verbatim)
⚠ A receipt that the contract is satisfiable, **not a spec**. The contract prescribes outcomes, not these mechanisms. Recommend NOT handing this appendix to the builder (anchoring); the lead decides.

### C.1 `loremaster/loremaster/testing/loopback.py` (stub + F1 + F2)
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/loremaster/testing/loopback.py	2026-09-26 13:27:55.193567809 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/93b938dc-25e9-4935-bdaf-4dbd6a6f51cf/scratchpad/loopback.reference.py	2026-09-26 14:27:36.400773624 -0400
@@ -42,6 +42,9 @@
 KERNEL_ASSIGNED_PORT: int = 0
 """The port number that asks the kernel for an ephemeral port — the ONLY port ever bound here."""
 
+DEFAULT_SHUTDOWN_TIMEOUT_S: float = 5.0
+"""STUB (d1): how long exit waits for the lifespan shutdown."""
+
 _STARTUP_POLL_S: float = 0.02
 """How often the startup wait re-checks ``started`` / thread death. Small, so a crash is named
 promptly rather than when the budget expires."""
@@ -125,6 +128,16 @@
     """
 
 
+class ServerShutdownTimeout(RuntimeError):
+    """STUB (d1): a started server's lifespan shutdown overran its budget."""
+
+    def __init__(self, message: str, *, host: str, port: int, shutdown_timeout_s: float) -> None:
+        super().__init__(message)
+        self.host = host
+        self.port = port
+        self.shutdown_timeout_s = shutdown_timeout_s
+
+
 @dataclass(frozen=True)
 class ServedEndpoint:
     """Where a started test server is answering.
@@ -295,10 +308,16 @@
         """
         logging.getLogger(_UVICORN_ERROR_LOGGER).addHandler(self._capture)
         self._thread.start()
+        try:
+            self._wait_started(startup_timeout_s)
+        except BaseException:
+            self._abandon()
+            raise
+
+    def _wait_started(self, startup_timeout_s: float) -> None:
         deadline = time.monotonic() + startup_timeout_s
         while not self._server.started:
             if not self._thread.is_alive():
-                self._abandon()
                 raise ServerThreadCrashed(
                     f"server thread for {self._address} ended before it reported started:\n"
                     f"{self._crash_detail()}",
@@ -307,7 +326,6 @@
                 )
             remaining_s = deadline - time.monotonic()
             if remaining_s <= 0:
-                self._abandon()
                 raise ServerStartupTimeout(
                     f"server at {self._address} timed out: not started within {startup_timeout_s}s "
                     "(server thread still alive)",
@@ -315,14 +333,24 @@
                     port=self._held.port,
                     startup_timeout_s=startup_timeout_s,
                 )
-            # A join returns the moment the thread dies, so a crash is named within one poll.
             self._thread.join(timeout=min(_STARTUP_POLL_S, remaining_s))
 
-    def stop(self) -> None:
-        """Drive a real lifespan shutdown and wait (bounded) for the thread to finish."""
+    def stop(self, shutdown_timeout_s: float, in_flight: BaseException | None = None) -> None:
         self._server.should_exit = True
-        self._thread.join(timeout=_SHUTDOWN_JOIN_TIMEOUT_S)
+        self._thread.join(timeout=shutdown_timeout_s)
         self._detach_capture()
+        if not self._thread.is_alive():
+            return
+        message = (
+            f"server at {self._address}: lifespan shutdown did not finish within "
+            f"{shutdown_timeout_s}s (server thread still alive)"
+        )
+        if in_flight is not None:
+            in_flight.add_note(message)
+            return
+        raise ServerShutdownTimeout(
+            message, host=self._held.host, port=self._held.port, shutdown_timeout_s=shutdown_timeout_s
+        )
 
     def _abandon(self) -> None:
         """Give up on a failed start: ask the thread to exit and release the held port NOW.
@@ -351,6 +379,7 @@
     *,
     port: LoopbackPort | None = None,
     startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S,
+    shutdown_timeout_s: float = DEFAULT_SHUTDOWN_TIMEOUT_S,
 ) -> Iterator[ServedEndpoint]:
     """Serve ``app`` under a real uvicorn in a thread, FROM a pre-bound socket.
 
@@ -379,8 +408,10 @@
         server_thread.start(startup_timeout_s)
         try:
             yield held.served_endpoint()
-        finally:
-            server_thread.stop()
+        except BaseException as in_flight:
+            server_thread.stop(shutdown_timeout_s, in_flight)
+            raise
+        server_thread.stop(shutdown_timeout_s)
 
 
 def _http_server_on(
@@ -443,6 +474,7 @@
 
 
 __all__ = [
+    "DEFAULT_SHUTDOWN_TIMEOUT_S",
     "DEFAULT_STARTUP_TIMEOUT_S",
     "KERNEL_ASSIGNED_PORT",
     "LOOPBACK_HOST",
@@ -450,6 +482,7 @@
     "LoopbackPort",
     "ServedEndpoint",
     "ServerBindError",
+    "ServerShutdownTimeout",
     "ServerStartError",
     "ServerStartupTimeout",
     "ServerThreadCrashed",
```

### C.2 guard detector (C3a + C3b)
```diff
--- /home/ejprice/PycharmProjects/lore/loremaster/tests/test_no_raw_listener_in_test_trees.py	2026-09-26 14:38:41.569058680 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/93b938dc-25e9-4935-bdaf-4dbd6a6f51cf/scratchpad/guard.reference.py	2026-09-26 14:39:11.571838538 -0400
@@ -82,9 +82,25 @@
 # Every callable reached through these modules opens (or configures) a listener.
 _LISTENER_NAMESPACES = ("socketserver", "http.server", "uvicorn", "wsgiref.simple_server")
 # The one ``socket`` module function that binds (``socket.socket`` itself binds nothing until ``.bind``).
-_LISTENER_FUNCTIONS = ("socket.create_server",)
+_LISTENER_FUNCTIONS = (
+    "socket.create_server",
+    "aiohttp.web.run_app",
+    "aiohttp.web.TCPSite",
+    "aiohttp.web.UnixSite",
+    "aiohttp.test_utils.TestServer",
+    "aiohttp.test_utils.unused_port",
+)
 # asyncio's listener verbs — matched on ANY receiver (a loop, the asyncio module, an alias).
-_LISTENER_METHODS = frozenset({"create_server", "create_unix_server", "start_server", "start_unix_server"})
+_LISTENER_METHODS = frozenset(
+    {
+        "create_server",
+        "create_unix_server",
+        "start_server",
+        "start_unix_server",
+        "create_tcp_listener",
+        "create_unix_listener",
+    }
+)
 # The helper's public names — an adoption is a CALL to one of these.
 _HELPER_ENTRY_POINTS = frozenset({"LoopbackPort", "serve_asgi", "serve_http"})
 # Files this contract itself adds; adoption must be observed OUTSIDE them (they cannot vouch for a tree).
```

### C.3 `scripts/concurrent_wire_acceptance.py` (F12)
```diff
--- /home/ejprice/PycharmProjects/lore/scripts/concurrent_wire_acceptance.py	2026-09-26 13:32:26.802654625 -0400
+++ /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/93b938dc-25e9-4935-bdaf-4dbd6a6f51cf/scratchpad/driver.reference.py	2026-09-26 14:30:10.149777556 -0400
@@ -29,6 +29,7 @@
 import argparse
 import os
 import re
+import signal
 import subprocess
 import sys
 import tempfile
@@ -210,18 +211,21 @@
 
     def _run_session(self, junit_path: Path) -> ProcessOutcome:
         """Run one pytest session to completion (or timeout) and read its junit with the shared reader."""
+        process = subprocess.Popen(  # noqa: S603 — argv is ours, no shell
+            self.session_argv(junit_path),
+            cwd=REPO_ROOT,
+            stdout=subprocess.PIPE,
+            stderr=subprocess.PIPE,
+            text=True,
+            start_new_session=True,
+        )
         try:
-            completed = subprocess.run(  # noqa: S603 — argv is ours, no shell
-                self.session_argv(junit_path),
-                cwd=REPO_ROOT,
-                capture_output=True,
-                text=True,
-                timeout=self.timeout_s,
-                check=False,
-            )
-        except subprocess.TimeoutExpired as expired:
-            partial = expired.stdout if isinstance(expired.stdout, str) else ""
-            return ProcessOutcome.from_junit(None, returncode=-1, timed_out=True, tail=partial)
+            stdout, stderr = process.communicate(timeout=self.timeout_s)
+        except subprocess.TimeoutExpired:
+            os.killpg(process.pid, signal.SIGKILL)
+            stdout, _stderr = process.communicate()
+            return ProcessOutcome.from_junit(None, returncode=-1, timed_out=True, tail=stdout or "")
+        completed = subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
         output = f"{completed.stdout}\n{completed.stderr}"
         tail = "\n".join(output.splitlines()[-TAIL_LINES:])
         junit_text = junit_path.read_text(encoding="utf-8") if junit_path.exists() else None
```

## Appendix D — wrong-build battery (verbatim; run from the scratch-copy root over the Appendix C reference; each proof = `scripts/mutation_proof.py`)
```python
#!/usr/bin/env python3
"""contract-466-d1 wrong-build battery: each entry = one mutation of a REFERENCE build (anchor must match
exactly once) + the RED set declared BEFORE the run; scripts/mutation_proof.py applies, runs, diffs BOTH
ways and restores byte-exact. Run from the scratch copy root. Exit 0 iff every proof passes."""
import subprocess, sys, tempfile
from pathlib import Path

LOOP = "loremaster/loremaster/testing/loopback.py"
LOOP_T = "loremaster/tests/test_loopback_serving.py"
GUARD_T = "loremaster/tests/test_no_raw_listener_in_test_trees.py"
DRIVER = "scripts/concurrent_wire_acceptance.py"
DRIVER_T = "scripts/test_concurrent_wire_acceptance.py"
F1 = f"{LOOP_T}::TestAnInterruptedStartupLeavesNothingBehind::"
F2 = f"{LOOP_T}::TestAShutdownOverrunIsLoud::"
P = ["[pytest-timeout-shaped-BaseException]", "[KeyboardInterrupt]"]
OWNED = [f"{F1}test_the_interrupt_propagates_unchanged_and_no_logging_handler_is_left_attached{p}" for p in P]
PASSED = [f"{F1}test_a_passed_port_is_not_served_after_the_interrupted_start{p}" for p in P]
CLEAN = f"{F2}test_a_clean_exit_whose_shutdown_hangs_raises_naming_the_address"
BODY = f"{F2}test_a_failing_body_keeps_its_own_exception_and_carries_the_overrun_as_a_note"
PROMPT = f"{F2}test_positive_control_a_failing_body_with_a_prompt_shutdown_gets_no_note"
G = f"{GUARD_T}::"

MUTATIONS = [
    # (name, file, anchor, replacement, declared RED, test file)
    ("W1 F1 cleanup catches Exception only", LOOP,
     "        except BaseException:\n            self._abandon()\n            raise\n",
     "        except Exception:\n            self._abandon()\n            raise\n", OWNED + PASSED, LOOP_T),
    ("W2 F1 detaches the handler but never abandons the start", LOOP,
     "        except BaseException:\n            self._abandon()\n            raise\n",
     "        except BaseException:\n            self._detach_capture()\n            raise\n", PASSED, LOOP_T),
    ("W3 F1 wraps the interrupt in a ServerStartError", LOOP,
     "        except BaseException:\n            self._abandon()\n            raise\n",
     "        except ServerStartError:\n            self._abandon()\n            raise\n"
     "        except BaseException:\n            self._abandon()\n"
     "            raise ServerThreadCrashed('wrapped', host=self._held.host, port=self._held.port)\n",
     OWNED + PASSED, LOOP_T),
    ("W4 F2 raises even with a body exception in flight (MASKS it)", LOOP,
     "            in_flight.add_note(message)\n            return\n", "            pass\n", [BODY], LOOP_T),
    ("W5 F2 logs the overrun instead of raising (log-only reading)", LOOP,
     "        raise ServerShutdownTimeout(\n            message, host=self._held.host, port=self._held.port, "
     "shutdown_timeout_s=shutdown_timeout_s\n        )\n",
     "        logging.getLogger(__name__).error(message)\n", [CLEAN], LOOP_T),
    ("W6 F2 notes every failing body, overrun or not", LOOP,
     "        if not self._thread.is_alive():\n            return\n",
     "        if not self._thread.is_alive() and in_flight is None:\n            return\n", [PROMPT], LOOP_T),
    ("W8 F2 message does not name the address", LOOP,
     'f"server at {self._address}: lifespan shutdown did not finish within "',
     'f"server: lifespan shutdown did not finish within "', [CLEAN, BODY], LOOP_T),
    ("W9 F2 leaks the capture handler on overrun", LOOP,
     "        self._detach_capture()\n        if not self._thread.is_alive():\n            return\n",
     "        if not self._thread.is_alive():\n            self._detach_capture()\n            return\n",
     [CLEAN], LOOP_T),
    ("W10 F2 ignores the passed budget (joins the old fixed 5 s)", LOOP,
     "        self._thread.join(timeout=shutdown_timeout_s)\n",
     "        self._thread.join(timeout=_SHUTDOWN_JOIN_TIMEOUT_S)\n", [CLEAN, BODY], LOOP_T),
    ("W11 C3 whole-namespace aiohttp (over-broad)", GUARD_T,
     '    "aiohttp.web.run_app",\n    "aiohttp.web.TCPSite",\n    "aiohttp.web.UnixSite",\n'
     '    "aiohttp.test_utils.TestServer",\n    "aiohttp.test_utils.unused_port",\n)\n',
     ')\n_LISTENER_NAMESPACES = (*_LISTENER_NAMESPACES, "aiohttp")\n',
     [f"{G}TestTheDetectorSeesAiohttpListeners::test_honest_aiohttp_clients_and_handlers_are_not_flagged"],
     GUARD_T),
    ("W12 C3 only run_app + TCPSite covered", GUARD_T,
     '    "aiohttp.web.UnixSite",\n    "aiohttp.test_utils.TestServer",\n    "aiohttp.test_utils.unused_port",\n', "",
     [f"{G}TestTheDetectorSeesAiohttpListeners::test_every_planted_aiohttp_listener_is_flagged_on_its_line"], GUARD_T),
    ("W13 C1 a renamed contract file leaves a stale entry", GUARD_T,
     '        "loremaster/tests/test_loopback_serving.py",\n        "skills/lore-deploy/tests/test_loopback_home.py",\n'
     "    }\n)\n",
     '        "loremaster/tests/test_loopback_serving_old.py",\n'
     '        "skills/lore-deploy/tests/test_loopback_home.py",\n    }\n)\n',
     [f"{G}TestTheContractFileExclusionIsLive::test_every_contract_file_entry_is_a_scanned_test_tree_file"], GUARD_T),
    ("W14 C1 the stale-entry checker reports nothing", GUARD_T,
     "    return sorted(entry for entry in entries if entry not in scanned)\n", "    return []\n",
     [f"{G}TestTheContractFileExclusionIsLive::test_positive_control_a_planted_stale_entry_is_reported"], GUARD_T),
    ("W15 C3 reach: a derived server library with no planted spelling", GUARD_T,
     '    "anyio": (\n        "import anyio\\n"\n        "async def serve(port):\\n"\n'
     "        \"    await anyio.create_tcp_listener(local_host='127.0.0.1', local_port=port)\\n\"\n    ),\n", "",
     [f"{G}TestTheServerCapableDependenciesAreDerived::test_the_derived_server_capable_set_equals_the_planted_map"],
     GUARD_T),
    ("W16 C3 reach: the verb oracle is blind", GUARD_T,
     "    if not any(verb.encode(\"ascii\") in source for verb in _DEPENDENCY_LISTENER_VERBS):\n        return False\n",
     "    return False\n",
     [f"{G}TestTheServerCapableDependenciesAreDerived::test_the_derived_server_capable_set_equals_the_planted_map",
      f"{G}TestTheServerCapableDependenciesAreDerived::test_positive_control_the_verb_oracle_sees_a_verb_and_ignores_prose"],
     GUARD_T),
    ("W17 F12 kills the session's process group but not the pid (group never created)", DRIVER,
     "            start_new_session=True,\n", "",
     [f"{DRIVER_T}::TestATimedOutSessionTakesItsWholeTreeWithIt::test_no_member_of_a_timed_out_session_tree_survives_the_round"],
     DRIVER_T),
]


def main() -> int:
    failures = 0
    only = set(sys.argv[1:])
    for name, target, anchor, replacement, declared, test_file in MUTATIONS:
        if only and name.split()[0] not in only:
            continue
        with tempfile.TemporaryDirectory() as scratch:
            anchor_file = Path(scratch) / "anchor"
            anchor_file.write_text(anchor, encoding="utf-8")
            replacement_file = Path(scratch) / "replacement"
            replacement_file.write_text(replacement, encoding="utf-8")
            argv = [sys.executable, "scripts/mutation_proof.py", "--file", target,
                    "--anchor-file", str(anchor_file), "--replacement-file", str(replacement_file)]
            for node in declared:
                argv += ["--expect-red", node]
            argv += ["--", "uv", "run", "python", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-n", "8", test_file]
            completed = subprocess.run(argv, capture_output=True, text=True, check=False)
        verdict = "PROVEN" if completed.returncode == 0 else f"FAILED (exit {completed.returncode})"
        print(f"{name}: {verdict}", flush=True)
        if completed.returncode != 0:
            failures += 1
            print(completed.stdout[-3000:], completed.stderr[-3000:], sep="\n")
    ran = len([m for m in MUTATIONS if not only or m[0].split()[0] in only])
    print(f"{ran - failures}/{ran} proofs passed")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## Appendix E — fake uvloop (C2 proof; `PYTHONPATH=<dir containing uvloop/>`; verbatim)
```python
"""A stand-in uvloop for contract-466-d1's C2 proof: a stdlib SelectorEventLoop subclass whose class
lives in module ``uvloop`` — what uvicorn's loop='auto' would pick the day the real one is installed."""
import asyncio


class Loop(asyncio.SelectorEventLoop):
    """Behaves exactly like the stdlib loop; only its identity differs."""


def new_event_loop() -> Loop:
    return Loop()
```
