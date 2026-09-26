brief-base v16 read · brief project v7 read

# REPORT — contract-466 (tdd-light CONTRACT for finding #466)

## SUMMARY BLOCK
- **State:** done-with-deviations. Contract = 3 test files plus the acceptance driver and its tests (5 files). Measured at HEAD `5d549a1` (2026-09-26): satisfiable (the scratch reference build passes 27/27); 11 wrong builds all RED; the guard's RED set at HEAD is exactly the 4 declared files (11 sites); 0 false positives over 325 test-tree files.
- **Deviations:** (D1) the idle-gate `.contract` write to `/tmp/claude-idle-gate-lore/` was denied by the auto-mode classifier (outside the writable set). No effect: the hook's default artifact is this report. (D2) I wrote the acceptance **driver itself** (the brief allowed it), not only its tests, so builder and grader are the same agent for that one file. It needs a cold audit. (D3) the driver's first draft hand-rolled a pytest-summary regex. The DRY search found `pending_contract_gate.JUnitReportReader`, so I rewrote the driver onto it: tests first, shown RED, then GREEN. Sharing is proven by mutation. (D4) `grep`/`rg` are hook-blocked (#473), so repo sweeps were AST scans in Python. `lore_get_symbol` does not resolve `scripts/` symbols, so those files were read directly.
- **Packages considered:** listener handoff → **uvicorn 0.48.0 `Server.run(sockets=[…])`**. I read the installed `uvicorn/server.py` `_serve`/`startup`: with `sockets=`, uvicorn calls `loop.create_server(sock=…)` and never binds, and lifespan runs before `create_server`. Verdict `replace` (use the package's feature). Stdlib half → **`http.server.HTTPServer(…, bind_and_activate=False)` + `server_activate()` on the held socket**. The reference build exercises it (27/27). Verdict `replace`. Pytest-result reading → **`scripts/pending_contract_gate.JUnitReportReader`** (in-house): `REUSED`. `portpicker`-style "give me a free port NUMBER" libraries: not installed, not read. Rejected on design grounds only: any API that returns a number rather than a held socket has the close→rebind window by construction. Called out so nobody mistakes this for a read.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 10 new symbols (contract-defined), all dispositioned (§DRY ledger). One EXTENDED: `_logging_fixtures.parse_production_trees` gains `include_testpaths`.
- **Graded:** n/a (I authored this; nothing of anyone else's was graded). Base of the measurements: `5d549a1`, which moved from `1206233` during the session via doc-only commits (`REPORT-sidecar-64.md`). Nothing my files touch changed.
- **Decisions needed:** (1) **spike adjudication:** I recommend ROUTE (§Spike). (2) **#492 (filed):** `lore_deploy._free_port(base)` has the same race in PRODUCTION. It is exempted in the guard with a trigger; operator ruling needed. (3) **§E:** the `gates.yaml` `-n auto` leg and the 15 s timeout. Surfaced only, with the decision point stated. (4) **runtime tripwire vs AST-only guard:** I recommend AST now, runtime at the re-open trigger (§Guard).
- **Receipts:** §RED/GREEN receipts · §Wrong builds · §Instruments (pasted verbatim) · finding #492 (lore_deploy prod race) · finding #493 (a lore_search filter-miss that contradicts itself).

## Capability check (brief-base §4)
| demanded | have | did instead | lead must change |
|---|---|---|---|
| write the idle-gate `.contract` file | Bash, but the classifier denied `/tmp/claude-idle-gate-lore/*` | relied on the hook default (`REPORT-contract-466.md`) | nothing, or add the path to the writable set in future briefs |
| lore-first for structure | lore loaded; `lore_get_symbol` misses `scripts/*` symbols (`pending_contract_gate.JUnitReportReader`, `mutation_proof._summary_section`: "no Python symbol … indexed") | read the files directly | none. The miss is noted here; filing it is optional |
| grep for sweeps | blocked (#473) | Python `ast` scans (instrument pasted in §Instruments) | — |

## Files (the writable set, all NEW; `git add` not run)
| file | what it is | md5 at report time |
|---|---|---|
| `loremaster/tests/test_loopback_serving.py` | the helper contract (A + B + lifecycle), 27 tests | `7fca1869…` |
| `loremaster/tests/test_no_raw_listener_in_test_trees.py` | the guard (C), 11 tests | `4c5979cd…` |
| `skills/lore-deploy/tests/test_loopback_home.py` | proves the ONE home works under the skill idiom, plus the `_probe_mcp_port` seam, 3 tests | `490c80d4…` |
| `scripts/concurrent_wire_acceptance.py` | the acceptance driver (D) | `d0eb9743…` |
| `scripts/test_concurrent_wire_acceptance.py` | driver contract, 20 tests | `55991325…` |

## Stub expectations (what the tdd-stub / implementer must create)
**Module `loremaster/loremaster/testing/loopback.py`**, with `loremaster/loremaster/testing/__init__.py`. Public names:
- `LOOPBACK_HOST: str = "127.0.0.1"`, `DEFAULT_STARTUP_TIMEOUT_S: float` (value not pinned; keep 15.0, §E).
- `class LoopbackPort` (context manager): `__init__(self, host: str = LOOPBACK_HOST)`, `.host`, `.port`, `.socket`, `.base_url`, `.listen()`. It binds `host:0` and does NOT listen by default. A bind failure raises `ServerBindError` no later than `__enter__`.
- `class ServerStartError(RuntimeError)`, plus the leaves `ServerBindError`, `ServerStartupTimeout` (`.host`, `.port`, `.startup_timeout_s`) and `ServerThreadCrashed` (`.host`, `.port`). The leaves are mutually non-subclassing.
- `serve_asgi(app, *, port: LoopbackPort | None = None, startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S)` → a context manager yielding an endpoint with `.host`, `.port`, `.base_url`.
- `serve_http(handler_class, *, port: LoopbackPort | None = None)` → the same endpoint shape.

**Extension (EXTENDED):** `loremaster/tests/_logging_fixtures.py::parse_production_trees(..., include_testpaths: bool = False)` must also parse every `[tool.pytest.ini_options] testpaths` root. Today `docs/eval` is unreached. The default stays False, so `test_ast_reach_helpers`' key-set pins are unaffected.

**RED-vs-collection:** until the stub lands, `test_loopback_serving.py` and `test_loopback_home.py` are COLLECTION errors (ImportError). The 5 scan tests in the guard raise `TypeError` on `include_testpaths`. Once the stub exists (module plus kwarg), every RED is behavioural.

## Plain-English contract
1. **A held port, never a number.** A test that needs a port gets a socket already bound to `127.0.0.1:0` and kept open for the test's lifetime. Nobody else can take the port meanwhile. By default the socket is not listening, so a connect is refused immediately. That is the race-free "dead port" the lore-deploy tests want. `.listen()` makes it accept. Exit closes it.
2. **Servers start from that socket.** `serve_asgi` runs real uvicorn with `sockets=[held]` and lifespan forced on. `serve_http` runs a stdlib handler on the held socket. At no point in the process does anything bind a specific (non-zero) port. That is pinned as an outcome over every bind in the process, via a receiver-blind spy on `socket.socket.bind`.
3. **Start failures name their cause:**
   - `ServerBindError`: the bind failed; the address is in the message and the `OSError` is chained.
   - `ServerStartupTimeout`: the thread is alive but not started within the budget. It is raised no earlier than the budget and no later than budget + 10 s (the helper must not sit on the old 20 s join), and it releases the held port.
   - `ServerThreadCrashed`: the server thread ended before it reported started. It must be named within 5 s even with a 60 s budget, carry the app's own error text, and release the port.
   - The crash doors pinned: a raising plain-ASGI lifespan, a real Starlette `lifespan.startup.failed` (the production door), and an app with no lifespan support (packet-59 FG1).
4. **Exit** drives a real lifespan shutdown and releases the port.
5. **Guard:** no file under any `testpaths` root opens a listener outside the helper. A listener means a `.bind(address)` call on any receiver, any call into `socketserver`/`http.server`/`uvicorn`/`wsgiref.simple_server` however aliased, `socket.create_server`, or an asyncio listener verb on any receiver. Exemptions are `(file, function)` pairs with evidence and a dead-entry pin. Reach is checked against `testpaths` (the scan must see every root), a non-vacuity floor, and adoption observed in both trees.
6. **Acceptance:** two concurrent pytest sessions of `test_migration_wire.py` (`-n 4` each), 20 consecutive rounds. Each round is green only if both sessions show total == passed == the count collected up front (14 at `5d549a1`), exit 0, and no timeout. Results are read by the shared junit reader. The driver refuses to start while another pytest session is live.

## Declared RED set (collected ids, fixed BEFORE any result; dated `5d549a1`)
- Guard, scan tests (TypeError now, behavioural after the stub):
  - `TestNoRawListenerInAnyTestTree::test_no_test_tree_opens_a_listener_outside_the_helper`. Offenders measured at HEAD (§Instruments scan): `test_migration_wire.py:107 (_free_port)`, `:122/:123 (_serve)`; `fastmcp_migration_spike.py:174 (_free_port)`, `:186/:188 (serve)`; `test_port_probe.py:43 (_free_port)`, `:75 (_start_stub_server)`; `test_workspace_probe.py:141 (_dead_port)`, `:292/:294 (_StubMCPServer.__init__)`.
  - `…::test_every_exemption_still_matches_a_live_site`. This goes GREEN as soon as the kwarg exists: both exemptions are live.
  - `TestTheScanReachesEveryTestTree::test_every_declared_testpaths_root_is_scanned`: `docs/eval` is unreached.
  - `…::test_the_scan_is_not_vacuous`: GREEN once the kwarg exists (325 files; 13 sites).
  - `…::test_both_trees_adopt_the_helper`: RED until the implementer migrates the 3 test files.
- `test_loopback_serving.py` (27) and `test_loopback_home.py` (3): all RED (module absent).
- Expected to stay RED after the stub and GREEN only after migration: the guard invariant plus the adoption pin. These are the implementer's migration of `test_migration_wire.py` / `test_port_probe.py` / `test_workspace_probe.py` and the spike ruling.

## RED/GREEN receipts (scoped runs only; no full suite)
- Guard discrimination and known-bound controls plus the first driver draft: `27 passed in 0.33s`.
- Guard at HEAD: `5 failed, 6 passed in 0.26s` (the 5 = TypeError on `include_testpaths`, as declared).
- Helper contract vs the **scratch reference build** (grafted as `loremaster.testing.loopback` by a pytest plugin; repo untouched): `27 passed, 2 warnings in 3.85s` (the final re-run after the w6 fix).
- `test_loopback_home.py` under the **skill idiom** (`cd skills/lore-deploy/scripts && uv run python -m pytest -q ../tests/test_loopback_home.py`): grafted `1 failed, 2 passed`. The failure is the provenance pin rejecting the scratch module path, which is its positive control. At HEAD: `1 error` (collection).
- Driver: rewritten tests vs the old driver: `1 error` (collection; `count_collected_node_ids` missing). After the rewrite: `20 passed in 0.25s`. Live `--collect-only` via `count_collected_node_ids`: `node ids: 14`. Live preflight: refused, naming a peer's `uv run pytest -n auto` (pid 2215810).
- ruff: all 5 files `All checks passed!`. mypy: `scripts` leg clean (`Success: no issues found in 2 source files`). The loremaster/skills files are clean except `import-untyped` on the not-yet-existing `loremaster.testing.loopback` (resolved by the stub). `lore_deploy` import-not-found appears only in single-file invocation; the sibling `test_port_probe.py` shows the same.
- **Not run (and why):** `test_ast_reach_helpers.py` against my new guard file. A peer full suite went live before I could, and one-session law applies. My reasoning that it stays green: the guard's only whole-tree parse goes through `parse_production_trees`, and the tmp-file control has `read_text` + `ast.parse` but no directory source, which is the Layer-2 clone signature's third leg. **A cold audit should run it.**

## Wrong builds (tdd-light has no adversary; this is the substitute, measured)
Each build is derived from the reference by exact-substring replacement, with `count == 1` asserted, so the mutation LANDED.
| build | defect | RED tests |
|---|---|---|
| w1_close_rebind | serve_asgi closes the held socket and hands `port=` to uvicorn (the #466 shape) | `test_a_passed_port_is_the_one_served_and_stays_open_while_serving`, `test_no_bind_to_a_specific_port_happens_during_the_whole_serve` |
| w2_lifespan_auto | `lifespan="auto"` | raising-lifespan crash, FG1 no-lifespan |
| w3_crash_only_on_timeout | never checks thread death (185 s run) | the 3 crash-promptness tests |
| w4_listen_by_default | LoopbackPort listens at bind | the unlistened-refuses test, the serve_http held-refuses test |
| w5_no_cause_text | crash message `"heavy build failed?"` | raising-lifespan and Starlette crash (sentinel missing) |
| w6_timeout_leaks_socket | removed the close in the timeout branch | **SURVIVED 27/27.** The mutation landed in redundant code (the owned-socket `finally` still closed it). Rebuilt as w6b ↓ |
| w6b_timeout_really_leaks | a real leak: no close on the timeout path | `test_a_lifespan_that_never_completes_raises_startup_timeout`. **This needed a contract fix:** the original check ("connect refused after the raise") could NOT see the leak, because a leaked but never-listened socket refuses too. It was replaced with `_is_released` (a rebind succeeds). |
| w7_free_port_close | LoopbackPort closes and rebinds the same number | the 3 bind-spy tests |
| w8_crash_named_as_timeout | a crash is raised as `ServerStartupTimeout` | the 3 crash tests |
| w9_bind_error_unwrapped | a raw `OSError` escapes | `test_an_unassignable_host_raises_server_bind_error_naming_the_host` |
| w10_http_rebinds_number | `HTTPServer((host, port))` after close | `TestServeHttp::test_no_bind_to_a_specific_port_happens` |
| w11_timeout_joins_stuck_thread | a 20 s join before raising the timeout | the timeout test (upper bound) |

## Adversarial pre-flight → case
| failure mode | covering case / note |
|---|---|
| **The #466 race itself** (bind:0 → close → rebind) | `test_the_port_stays_held_while_the_context_is_open` (EADDRINUSE squatter); the bind spies (∀ binds in the process have port 0); the passed-port `fileno` leg; wrong builds w1/w7/w10 |
| Wrong unit / scale: a config port (9233) or 0 returned as the port | `test_the_port_is_a_kernel_assigned_ephemeral_port` (in `/proc/sys/net/ipv4/ip_local_port_range`) |
| Wrong anchor: `base_url` built from a different host/port than the one served | `base_url ==` pins on the listener and on both serve paths |
| Null / zero / boundary: a startup exactly inside vs outside the budget | slow-in-budget control (0.5 s of 10 s) vs never-completes (1.0 s budget; elapsed ∈ [0.9, 11]) |
| Degenerate driver: a helper that binds nothing | every spy test asserts `addresses` is non-empty (non-vacuity) |
| Cause confusion (bind vs timeout vs crash) | three leaf classes, mutually non-subclassing; w8 |
| Crash only noticed at the timeout | the 5 s bound with a 60 s budget; w3 |
| Cause text lost ("heavy build failed?") | sentinel pins on the plain and Starlette doors; w5 |
| FG1: an app without lifespan served silently | `test_an_app_that_cannot_speak_lifespan_fails_loudly`; w2 |
| Lifecycle: resource leaks on each exit path (normal / timeout / crash) | exit-refuses (served paths), `_is_released` (timeout and crash paths, never listened), `fileno == -1` (LoopbackPort); w6b |
| Concurrency degree | 16-way distinct held ports; 8-way concurrent `serve_asgi`, each answering with its own identity |
| Producer↔consumer seam: helper → uvicorn 0.48 / → http.server / → `lore_deploy._probe_mcp_port` | real uvicorn over real TCP; real HTTPServer; `test_loopback_home.py` drives the real probe against a served port and a held-unlistened port |
| Real-distribution tail: the heavy real lifespan (store + watcher build) | **scoped out of the unit contract** (it needs the live store). It is covered by the acceptance driver running the real `test_migration_wire.py` 20× concurrently |
| Guard false negatives: aliasing, receiver renames, from-imports | `_PLANTED` covers 11 flagged spellings including aliased receivers and aliased from-imports |
| Guard false positives: `Signature.bind(None, **f)` (a REAL site in `test_fastmcp_migration.py`), structlog bind, clients, class references | the `_HONEST` negative control; the HEAD scan found 0 false positives over 325 files |
| Guard reach: a testpaths root not scanned | `test_every_declared_testpaths_root_is_scanned` (RED today: `docs/eval`) |
| Guard exemption rot | the dead-entry pin; exemptions keyed by function (`test_the_exemption_is_keyed_by_function_not_by_file`) |
| A library-internal listener (`LoreServer(config).run()` unpatched) | **KNOWN BOUND, pinned** (`TestKnownBoundLibraryInternalListeners`); re-open trigger: first occurrence → runtime tripwire |
| Driver: "no tests ran", a missing report, a count drift, one session red, a timeout, a short run | `TestTheRoundVerdict` (10 cases), the measured-#466 junit shape |
| Driver: a private parser drifting from the shared one | `test_the_verdict_follows_the_shared_reader` (mutation of the shared reader) |

## Realism clauses
- ☑ **Production-realistic inputs.** Real uvicorn 0.48.0 and a real Starlette lifespan (the fastmcp app type), over real TCP. The ports are kernel-assigned and checked against the kernel's own range file. Failure hosts and errnos were probed on this box before writing (EADDRNOTAVAIL 99, ECONNREFUSED 111, EADDRINUSE 98). The driver fixtures are pytest junit xunit1 documents in the shape the shared reader already accepts.
- ☑ **Independent expected values.** Expected values come from kernel semantics (a bound, unlistened socket refuses; a held port refuses a squatter), from the requirement (no specific-port bind; a named cause), and from the measured #466 shape (2 failed + 4 errors, 14 alone). None derive from an implementation formula. The satisfiability run used my own reference build, but each pin was also shown to fail on a wrong build.
- ☑ **Seam coverage.** helper→uvicorn (`sockets=`), helper→http.server, helper→`lore_deploy._probe_mcp_port`, and the skill idiom→the workspace member (the provenance pin).
- ☑ **Magnitude / sanity bounds.** Port in the ephemeral range; elapsed-time windows for the timeout ([0.9×, +10 s]) and the crash (< 5 s); non-empty spy lists.
- ☑ **Shared conventions, not literals.** The ephemeral range is read from `/proc` (the kernel's truth). `testpaths` is read from `pyproject.toml`. The expected wire count is derived by `--collect-only`, and the test constant 14 is only a fixture value dated to `5d549a1`. The junit family matches the shared reader's refusal rule.
- ☐ **Hostile fixtures for rendered stored text:** not applicable. No stored free text is rendered. The error messages carry only exception text from the app under test.
- ☑ **Input accounting for collection transforms**, applied to the guard (each input file × site → exactly one fate: offender, exempted, or clean). Every fate is forced: offenders (the HEAD scan), exempted (2 live exemptions plus the function-keyed exemption test), clean (the `_HONEST` control). The reach pins make sure no file silently has no fate.

## Replaced-code inventory adjudication
Spec = finding #466 (as annotated by lead-63c-2), packet-59 FG1 (the wire docstring's cited design guard), and this brief.
| # | old behavior (where) | verdict | pin / reason |
|---|---|---|---|
| 1 | bind `127.0.0.1:0`, read the port, CLOSE (`_free_port` ×3, `_StubMCPServer.__init__`) | **old-bug** | this IS #466. Not re-pinned; its absence is pinned (held port + bind spies) |
| 2 | `_dead_port`: an UNSERVED port (connect refused) | **preserved-with-pin**, strengthened | brief: "keep that semantics". An unlistened `LoopbackPort` refuses AND is held (`test_an_unlistened_port_refuses_connections_fast`; `test_the_probe_refuses_a_held_unlistened_port_fast`) |
| 3 | `lifespan="on"` forced (the FG1 loud failure) | **preserved-with-pin** | packet-59 FG1 → `test_an_app_that_cannot_speak_lifespan_fails_loudly` |
| 4 | exit drives a real shutdown so lifespan teardown runs | **preserved-with-pin** | the wire harness needs teardown (store and watchers) → `test_exit_drives_a_real_lifespan_shutdown` |
| 5 | uvicorn in a daemon thread; the caller gets a base URL | **preserved-with-pin** | `base_url` pins |
| 6 | 15 s startup budget (`_serve`), 10 s (spike) | **dropped-deliberately (as a pinned value)** | the value is measure-then-tune (§E). Only existence and sanity are pinned; the budget is a parameter |
| 7 | timeout raised as generic `RuntimeError("…heavy build failed?")` | **old-bug** | the guess conflated the causes (#466 annotation). Replaced by the three leaves |
| 8 | `thread.join(timeout=20)` in `finally` even after a failed start | **old-bug** | it hid the failure behind a 20 s wait; w11 pins "no". The successful-start join is not pinned (spec-silent → no ruling needed; ordinary cleanup) |
| 9 | `log_level="error"` on uvicorn | **spec-silent: operator ruling required** | my recommendation: keep it (it controls noise, not behavior) and leave it unpinned |
| 10 | `http.server.HTTPServer((host, port), …)` stubs; the caller owns `shutdown()`/`server_close()` | **preserved** in semantics (serve and release); the mechanism is replaced | `TestServeHttp` exit-releases |
| 11 | `_start_stub_server` delayed-listen (`test_port_probe`: a listener appears mid-wait) | **preserved-with-pin**, race-free | `test_a_held_port_refuses_until_served_then_accepts` (hold unlistened, then serve on the same socket) |
| 12 | `_StubMCPServer` records requests (`stub.tool_calls`, `structured`) | **preserved** (the handler's own state, untouched by the helper) | no helper pin needed; the implementer keeps the handler class |

**Dropped-deliberately list:** #6 (the budget value as a pin).
**Spec-silent list:** #9 (`log_level="error"`). I recommend keep-unpinned; say if you want a ruling.

## Spike adjudication (`scripts/fastmcp_migration_spike.py`)
It is a **cited receipt instrument**: 41 references in the packet-59 and regression-fix receipts; `REPORT-spike-59.md` names it the durable, re-runnable harness. It already carries an exemption in `test_secret_typing` (`_FASTMCP_SPIKE_EXEMPT`). It holds the 4th copy of the policy (`_free_port` + `serve`, with a 10 s budget).
- **Recommend ROUTE:** replace its `_free_port`/`serve` with `serve_asgi`. It already runs in the workspace venv (`uv run --with … python scripts/fastmcp_migration_spike.py`), so `loremaster.testing.loopback` imports. This keeps the receipt runnable and deletes copy #4.
- Alternatives: RETIRE (delete). That loses a cited, re-runnable instrument, against brief-base's "an instrument is a deliverable". Or LEAVE + PINNED BOUND: add `("scripts/fastmcp_migration_spike.py", "_free_port"|"serve")` to `_EXEMPT_SITES` with a re-open trigger.
- **The guard is RED on it either way until the ruling lands.** That forces the decision instead of letting it default.

## Guard: AST now, runtime later (decision 4)
The AST guard covers what an honest developer writes in our source. The threat model is written into the file. It cannot see a listener inside a dependency (the pinned known bound). A runtime tripwire (autouse wrapping `socket.socket.bind`, naming any non-helper frame that binds a non-zero port) would close that. But it touches every test, needs conftest edits in two trees, and has no measured occurrence to justify it.
- **Recommendation:** AST now; runtime at the stated trigger.
- The alternative reading of "allowlist the safe" is a runtime-only guard. I chose AST because the brief specified the AST idiom.

## §E — surfaced, not pinned
- `scripts/gates.yaml` pytest leg `-n auto` (~line 91). Fine under the 2026-09-26 memory relaxation. #466's second failure mode (64+64 workers OOM) returns only if two `-n auto` sessions overlap, which the new driver's preflight now refuses for itself. The gate itself does not check. **Decision point:** at the first OOM or watchdog kill in a currency run, or when the box's memory baseline changes. Owner: operator.
- The 15 s startup budget. **Measure-then-tune:** once the helper names causes, run the acceptance driver 20× and read the `ServerStartupTimeout` count and the observed startup spread. Tune only if timeouts appear. **Decision point:** the implementer's acceptance run, decided by the lead. Also note: `DEFAULT_STARTUP_TIMEOUT_S` exists, so the wire harness can pass a different budget without editing the helper.

## Also noticed (outside this change)
- **#492 (filed):** `lore_deploy._free_port(base)`: production close→podman-rebind race. It also checks 127.0.0.1 only, while podman may publish on another interface.
- **#493 (filed):** `lore_search` served `[FILTER MISS] … 'lore' is not a configured tier — configured tier(s): 'lore', …`. It contradicts itself and blames the tier for what the DETAIL MISS in the same response attributes to the detail filter. This is a trust-doctrine surface.
- `lore_get_symbol` cannot resolve `scripts/*.py` symbols (bare or module-qualified), e.g. `pending_contract_gate.JUnitReportReader`, so the DRY search for `scripts/` had to fall back to AST. Not filed. The lead may want it filed as a reach gap, since `scripts` is a typecheck and testpaths root.
- The driver's preflight is deliberately over-inclusive: any process whose argv mentions `pytest` counts, including bash wrappers and non-lore projects' sessions (the `mobile_pricepaper_smoke` lanes were live today). `--allow-other-sessions` exists for when the operator rules that only lore sessions matter.
- `test_mcp_server.TestRunAndMain` calls `LoreServer(config).run()` with `uvicorn.Server.serve` patched. That is safe today, but it is the exact door the known-bound pin names. If that patch is ever dropped, the test binds config port 9233.

## DRY ledger (brief-base §6)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `LoopbackPort` / `serve_asgi` / `serve_http` / the 4 error classes (contract-defined) | `lore_search("free ephemeral loopback port for a throwaway test server, bind socket to port 0")`; AST scan of every testpaths root and member | lore: only SurrealDB-docs noise. AST: the 4 hand-rolled copies (+ the prod `lore_deploy._free_port`) and nothing shared | **HAND-ROLLED (as a contract)**: no shared helper exists; this contract creates copy #1 and retires copies 1–4 |
| `parse_production_trees(include_testpaths=…)` | read `_logging_fixtures.py` | the ONE tree parser; it lacks `docs/eval` | **EXTENDED `_logging_fixtures.parse_production_trees`** |
| guard `listener_sites` / `_SiteCollector` / `_import_aliases` | read `test_no_exact_type_check_on_surreal_store_error.py`, `test_ast_reach_helpers.py` | the idiom is per-file offender functions over the shared parser (by design; each scan owns its predicate) | **HAND-ROLLED**: the predicate is guard-specific; the parse and reach are REUSED (`parse_production_trees`, `assert_scan_reached_every_member`, `_workspace_root`) |
| driver result reader | `lore_search("parse pytest summary line …")`, `lore_search("regex over pytest terminal output …")` (#493 surfaced here); AST scan of `scripts/` for tally/junit/summary | `pending_contract_gate.JUnitReportReader`, `mutation_proof._summary_section` | **REUSED `pending_contract_gate.JUnitReportReader`** (proven by mutation); my first-draft regex was deleted |
| `count_collected_node_ids`, `other_pytest_sessions` | `lore_search("detect other live pytest processes in /proc …")`; the same AST scan | nothing equivalent | **HAND-ROLLED**: nothing found (queries above) |

## Instruments (pasted verbatim — scratch dir is disposable)
**Graft plugin** (`-p ref466_plugin`, `PYTHONPATH=<dir>`, `REF466_MODULE=<build>`):
```python
import importlib, os, sys, types
import loremaster
target = os.environ.get("REF466_MODULE", "ref_loopback")
mod = importlib.import_module(target)
pkg = types.ModuleType("loremaster.testing"); pkg.__path__ = []
pkg.loopback = mod
sys.modules["loremaster.testing"] = pkg
sys.modules["loremaster.testing.loopback"] = mod
loremaster.testing = pkg
```
**Reference build** (`ref_loopback.py`, the satisfiability receipt; NOT a spec for the implementer, who builds blind to it):
```python
from __future__ import annotations
import contextlib, logging, socket, threading, time, traceback
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any
import uvicorn

LOOPBACK_HOST = "127.0.0.1"
DEFAULT_STARTUP_TIMEOUT_S = 15.0
_POLL_S = 0.02
_JOIN_S = 5.0

class ServerStartError(RuntimeError):
    def __init__(self, message: str, *, host: str, port: int) -> None:
        super().__init__(message); self.host = host; self.port = port
class ServerBindError(ServerStartError): pass
class ServerStartupTimeout(ServerStartError):
    def __init__(self, message: str, *, host: str, port: int, startup_timeout_s: float) -> None:
        super().__init__(message, host=host, port=port); self.startup_timeout_s = startup_timeout_s
class ServerThreadCrashed(ServerStartError): pass

class LoopbackPort:
    def __init__(self, host: str = LOOPBACK_HOST) -> None:
        self.host = host
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.bind((host, 0))
        except OSError as exc:
            self.socket.close()
            raise ServerBindError(f"bind of {host}:0 failed: {exc}", host=host, port=0) from exc
        self.port = int(self.socket.getsockname()[1])
        self.base_url = f"http://{host}:{self.port}"
    def listen(self) -> None: self.socket.listen()
    def close(self) -> None: self.socket.close()
    def __enter__(self) -> "LoopbackPort": return self
    def __exit__(self, *exc: object) -> None: self.close()

@dataclass(frozen=True)
class ServedEndpoint:
    host: str; port: int; base_url: str

class _Capture(logging.Handler):
    def __init__(self) -> None: super().__init__(); self.lines: list[str] = []
    def emit(self, record: logging.LogRecord) -> None:
        text = record.getMessage()
        if record.exc_info: text += "\n" + "".join(traceback.format_exception(*record.exc_info))
        self.lines.append(text)

@contextlib.contextmanager
def serve_asgi(app: Any, *, port: LoopbackPort | None = None,
               startup_timeout_s: float = DEFAULT_STARTUP_TIMEOUT_S) -> Iterator[ServedEndpoint]:
    owned = port is None
    held = LoopbackPort() if port is None else port
    config = uvicorn.Config(app, log_level="error", lifespan="on")
    server = uvicorn.Server(config)
    capture = _Capture(); error_logger = logging.getLogger("uvicorn.error"); error_logger.addHandler(capture)
    crash: list[BaseException] = []
    def _run() -> None:
        try: server.run(sockets=[held.socket])
        except BaseException as exc: crash.append(exc)
    thread = threading.Thread(target=_run, daemon=True); thread.start()
    address = f"{held.host}:{held.port}"
    try:
        deadline = time.monotonic() + startup_timeout_s
        while not server.started:
            if not thread.is_alive():
                detail = "\n".join(capture.lines) + "".join(repr(c) for c in crash)
                held.close()
                raise ServerThreadCrashed(f"server thread for {address} crashed before startup:\n{detail}",
                                          host=held.host, port=held.port)
            if time.monotonic() >= deadline:
                server.should_exit = True
                held.close()
                raise ServerStartupTimeout(f"startup timed out after {startup_timeout_s}s at {address} (thread alive)",
                                           host=held.host, port=held.port, startup_timeout_s=startup_timeout_s)
            time.sleep(_POLL_S)
        yield ServedEndpoint(held.host, held.port, held.base_url)
    finally:
        server.should_exit = True
        if server.started: thread.join(timeout=_JOIN_S)
        error_logger.removeHandler(capture)
        if owned: held.close()

@contextlib.contextmanager
def serve_http(handler_class: Any, *, port: LoopbackPort | None = None) -> Iterator[ServedEndpoint]:
    import http.server
    owned = port is None
    held = LoopbackPort() if port is None else port
    server = http.server.HTTPServer((held.host, held.port), handler_class, bind_and_activate=False)
    server.socket.close(); server.socket = held.socket; server.server_activate()
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    try:
        yield ServedEndpoint(held.host, held.port, held.base_url)
    finally:
        server.shutdown(); thread.join(timeout=_JOIN_S); held.close()
```
**Wrong-build generator** (each edit is asserted `count == 1` before replacing). The (old → new) pairs are exactly as tabulated in §Wrong builds. Representative entries:
```python
"w1_close_rebind": [("server.run(sockets=[held.socket])", "held.close(); config.port = held.port; config.host = held.host; server.run()")],
"w2_lifespan_auto": [('lifespan="on"', 'lifespan="auto"')],
"w3_crash_only_on_timeout": [("if not thread.is_alive():", "if False:")],
"w6b_timeout_really_leaks": [("server.should_exit = True\n                held.close()\n", "server.should_exit = True\n"),
                             ("        if owned:\n            held.close()\n\n\n@contextlib.contextmanager\ndef serve_http", "        if owned and server.started:\n            held.close()\n\n\n@contextlib.contextmanager\ndef serve_http")],
"w9_bind_error_unwrapped": [('raise ServerBindError(f"bind of {host}:0 failed: {exc}", host=host, port=0) from exc', 'raise')],
"w11_timeout_joins_stuck_thread": [("held.close()\n                raise ServerStartupTimeout(", "held.close()\n                thread.join(timeout=20)\n                raise ServerStartupTimeout(")],
```
**HEAD listener scan** (the guard's own detector over the shared parser minus `include_testpaths`; run from `loremaster/tests`):
```python
import sys; sys.path.insert(0, ".")
import test_no_raw_listener_in_test_trees as guard
from _logging_fixtures import parse_production_trees
trees = parse_production_trees(include_scripts=True, include_skills=True, include_tests=True)
tp = guard._declared_testpaths()
scoped = {p: t for p, t in trees.items() if any(guard._under(p, r) for r in tp)}
print(len(scoped), [r for r in tp if not any(guard._under(p, r) for p in scoped)])
for site in guard._all_sites(scoped):
    print("EXEMPT" if (site.path, site.function) in guard._EXEMPT_SITES else "OFFENDER", site.render())
```
Output at `5d549a1`: 325 files; unreached `['docs/eval']`; 2 EXEMPT + 11 OFFENDER. The offender lines are listed in §Declared RED set.
