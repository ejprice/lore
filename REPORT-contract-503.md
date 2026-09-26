# REPORT-contract-503 — tdd-light CONTRACT: #503 heavy wire start budget · R4 teardown never masks the body · currency gate pytest workers

## SUMMARY BLOCK
- `brief-base v16 read` · `brief project v7 read` (lore_comms register, session `297217bd`)
- **State:** done-with-deviations. Tests only; nothing committed. Written and measured 2026-09-26 at HEAD `884ca63`.
- **Deviations:** (1) I appended R4's pins to the existing `loremaster/tests/test_loopback_serving.py`, which already holds the rig helpers, instead of starting a new file, and I added 4 import lines there. No existing assertion changed. (2) I ran a reference build inside a `scratch_copy.sh` copy to prove the contract is satisfiable. That code never touched the real tree (§Satisfiability).
- **Packages considered:** process detection → psutil `keep_with_trigger`. psutil is not a scripts dependency. The stdlib `/proc` reader `concurrent_wire_acceptance.other_pytest_sessions` already exists; I read its source, and the contract MOVES it rather than replacing it. Trigger: the day the detector needs more than argv (cwd, children, exe). Budgets and the teardown note: no mechanism beyond the stdlib (PEP 678 `add_note`). Worker-count substitution: follows the existing `{junit_xml}` placeholder idiom in `pending_contract_gate` (I read `GateSpec.resolved_command`).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 4 new test-side symbols, all dispositioned (§DRY ledger). The contract DEFINES 7 production symbols (§Stub expectations).
- **Graded:** n/a — this report is an authored contract, not a verdict on someone else's artifact.
- **Decisions needed:** **F1** (R4: does an interrupt that lands in the teardown of a failing body propagate? My pin says yes, Reading A). **F2** (what counts as "another LORE pytest session"? My pins are neutral between the readings). **F3** (should the manifest loader REFUSE a hardcoded worker count? That goes beyond the ruling's letter, and I pinned it). Details: §Forks.
- **RED receipt (HEAD `884ca63`):** 46 new tests (15 + 5 + 26, from the three run tails). **14 fail for a behavioral reason**, **18 fail only because a symbol does not exist yet** (ModuleNotFoundError or AttributeError, listed in §Stub), and **14 are green on purpose** (controls and regression guards). Per file: R4 4F/11P · budget 4F/1P (1 of the 4 needs a stub) · workers 24F/2P (17 of the 24 need a stub). Details: §RED receipt.
- **Satisfiability:** a reference build in a provenance-asserted scratch copy runs the new files plus 6 neighbouring suites at **226 passed / 0 failed**. 3 wrong builds are each caught (§Satisfiability).
- **Receipts:** §RED receipt · §Satisfiability · §Adversarial pre-flight · §Forks.

## Capability check (brief-base §4)
- **Demanded:** lore tools first-choice. **Have:** yes. I used `lore_impact(serve_asgi)`, which found 22 test refs and 0 prod refs, consistent with a test-only helper.
- **Demanded:** grep/rg hook-blocked. **Did:** fell back to **awk** for three text searches: `-n auto` pin hunting (a non-symbol textual seam), `serve_asgi(` call sites, and a `/proc` cmdline sample. These are the grep-honest cases (b) and (c) in CLAUDE.md. No lore friction was filed, because lore does not index `/proc` or YAML argv, so this was not a lore weakness.
- **Demanded:** `-n 12` when another lore session is live. **Did:** a live lore session was observed (pid 3874001, a scratch copy of lore), so every run used `-n ≤12`. No full suite was run, :18500 was never touched, and the TEI embedder was never called (the wire fixture uses a `FakeEmbedder`).

## Test paths
1. `loremaster/tests/test_loopback_serving.py` → new class `TestAFailingBodyIsNeverReplacedByItsTeardown` plus its rig section, appended at the end. It also adds imports: `typing`, `dataclass`, `ServedEndpoint`, and `loremaster.testing.loopback as loopback_module`.
2. `loremaster/tests/test_migration_wire_budget_503.py` (new).
3. `scripts/test_pytest_workers_503.py` (new).

## The contract in plain English
- **R4.** When a test body inside `serve_asgi` or `serve_http` fails, the test's own exception is what surfaces. This holds whatever the teardown did: overran its budget, or raised. The teardown problem is attached to that exception as a PEP 678 note. The note names `host:port`, and for a raise it also names the error's type and text.
  - If the body was clean and the teardown raises, that teardown error surfaces unchanged (control).
  - An interrupt (Ctrl-C, or pytest-timeout's BaseException) that lands in the teardown still propagates unchanged, with the body's failure on its `__context__` (Reading A, F1).
  - Nothing is left behind on the R4 path: no logging handler attached, no live thread, and the owned port released.
  - The domain is generated: every serving helper that `loopback.__all__` exports (derived from type hints) × {Exception body, BaseException body} × {teardown raises, teardown overruns}.
- **#503.** The heavy wire fixture `_serve_migration_wire` starts its server with a budget of 60 s. The budget is a named module constant, `MIGRATION_WIRE_STARTUP_TIMEOUT_S`, passed by that name at every `serve_asgi` call in `test_migration_wire.py` (AST-derived). The value actually reaches `serve_asgi` (runtime spy). A real heavy start of more than 20 s is served rather than timed out (behavioral pin). `loopback.DEFAULT_STARTUP_TIMEOUT_S` stays at 15 s.
- **Workers.**
  - One policy, `_pytest_sessions.pytest_worker_count`, returns `"12"` if the one shared detector `other_pytest_sessions` reports another session, and `"auto"` otherwise. There is no division by session count and no refusal (ruling 4).
  - The detector lives once, in `scripts/_pytest_sessions.py`, and `concurrent_wire_acceptance` re-exports that same object.
  - The shipped manifest's pytest gate spells `-n {workers}`. `GateRunner.run` substitutes the count at run time, not at load time. This works through both render paths (direct, and `_run_selected_gates` with forwarded args), and the gate excludes its own pid.
  - The manifest loader refuses a junit gate that hardcodes a worker count (F3).
  - No manifest description still teaches `-n auto`.

## Adversarial pre-flight (each item → the case that covers it, or a scoped-out note)
| # | Realistic failure | Covered by |
|---|---|---|
| 1 | Wrong scale: the heavy budget is typed too small (e.g. 16 s) or left at the default | `test_the_heavy_budget_constant_has_the_ruled_value` (== 60, ≥3× measured max), plus the behavioral slow-start pin |
| 2 | The constant is defined but never passed (the name exists, the value does not reach the start) | the AST pin (generated over call sites) + the runtime spy + the behavioral pin |
| 3 | A second heavy serve site is added later without the budget | AST pin generated over every `serve_asgi` call in the file |
| 4 | The default moves to 60 s (the "fix" is applied globally) | `test_the_default_startup_budget_stays_at_the_ruled_value` |
| 5 | A delay that is injected but not inside the awaited start (vacuous slow pin) | the non-vacuity check `start_took_s >= SLOW > DEFAULT`, plus the delayed gate running exactly once |
| 6 | R4 fixed for Exception bodies only (pytest's `Failed` is a BaseException) | body-kind parametrization `body-raises-BaseException` |
| 7 | R4 fixed for one helper only | helper domain derived from `__all__` type hints + a completeness pin |
| 8 | R4 over-fix: `except BaseException` around stop swallows Ctrl-C/timeout | `test_an_interrupt_in_the_teardown_of_a_failing_body_still_propagates` (W1 was caught) |
| 9 | R4 note is silent about WHICH teardown error, or about the address | note must carry the address + type name + sentinel text |
| 10 | R4 fix drops the error on a clean body | clean-body control |
| 11 | Injection lands after the teardown (a vacuous pass) | `still_blocked()` read at exit + an exit-time window per failure kind |
| 12 | Policy counts its own process | `only-own-pid` row + the gate's `own_pids ∋ getpid()` check (W3 was caught) |
| 13 | Policy counts xdist workers or non-test processes | `worker-and-non-test-process` row (worker argv observed live: `python -u -c import sys;exec(...)`) |
| 14 | Policy divides by session count, or caps sessions (ruling 4) | `three-sessions-still-12` |
| 15 | Detector cloned into the gate (copy #2) | AST one-definition pin + mutation-by-stub pins (W6 was caught) |
| 16 | Count frozen at import or manifest load; a session that starts during the typecheck leg is missed | `test_the_count_is_resolved_when_the_gate_runs_not_when_it_loads` |
| 17 | Forwarded pytest args drop the resolved count, or the count drops them | `test_forwarded_pytest_args_keep_the_policy_count` |
| 18 | Manifest re-hardcodes a count later (`-n auto`, `-n12`, `--numprocesses=…`) | loader-refusal pins + the shipped-manifest placeholder pin |
| 19 | Stale prose: the gate description still says "-n auto" | `test_no_shipped_gate_description_teaches_the_retired_count` |
| 20 | A test accidentally spawns a real full suite | `subprocess.Popen` is replaced by a raising recorder, so no spawn API gets through. **Bound:** a builder using `os.posix_spawn` or asyncio subprocesses would bypass it (scoped out: no such use in scripts/) |
| 21 | Wrong anchor (a lore session in a scratch copy has cwd OUTSIDE the repo) | `one-scratch-session` row, whose shape was observed live, and F2 |
| 22 | Sign, null, zero on the budgets | scoped out: the constants are positive literals ruled by the operator. The existing `test_the_default_budget_is_a_positive_finite_number` still guards the default |
| 23 | Empty or degenerate `/proc` | `empty-proc` row, plus non-pid entries (`self`, `sys`, `meminfo`) present in every fake `/proc` |
| 24 | Hostile rendered text | scoped out: the R4 note renders an exception's own text into a PEP 678 note, not into a machine-parsed or row-shaped output. No stored free text is rendered |

## Realism & independence
- ☑ **Production-realistic inputs.** The `/proc` argvs, cwds and pid magnitudes were copied from the live box on 2026-09-26: a scratch-copy lore session, an execnet worker, and the gate's own leg. The budgets come from REPORT-measure-503 (n=551). The R4 sentinel mirrors the measured `RuntimeError: can't start new thread`.
- ☑ **Independent expected values.** The expected values are the operator ruling (60 / 15 / "12" / "auto"), written as the test's own constants and never read back from the module under test. The measured maxima 10.04 s and 0.50 s are cited to 388c604.
- ☑ **Seam coverage.** The real handoffs are exercised: fixture → `serve_asgi` (spy bound on the real signature, plus a behavioral start through the real lifespan), manifest → `GateRunner` → `Popen` argv, and policy → shared detector (mutation-by-stub with an opposite fake `/proc`).
- ☑ **Magnitude/sanity bounds.** Heavy budget ≥ 3× measured heavy max; default ≥ 3× measured light max; the injected delay plus the measured max fit inside the ruled budget; exit-time windows are bounded on both sides.
- ☑ **Shared conventions.** The xdist flag, the placeholder (`pending_contract_gate.WORKERS_PLACEHOLDER`), `DEFAULT_STARTUP_TIMEOUT_S`, `ServedEndpoint` and the helper set are all read from production modules. The one hardcoded convention is `RETIRED_WORKERS_LITERAL` ("-n auto"), which is deliberate: it is the retired spelling.
- ☐ **Hostile fixtures for rendered stored text.** Not applicable: no stored free text is rendered (pre-flight #24).
- ☑ **Input accounting for collection transforms.** Applies only in the weak sense that the policy consumes a process collection and emits a yes/no. The per-input fates are covered: own pid is excluded, a worker is not a session, a non-test process is not a session, a lore session counts. Each fate is forced by a row.

## Forks (spec-silent or two readings: my pick is written down, and the operator rules)
- **F1: an interrupt that lands in the teardown of a FAILING body.**
  - Reading A (pinned): the interrupt propagates unchanged. The ruling calls "an overrun OR a raise" teardown failures, and R1 says interrupts propagate; the body stays reachable on `__context__`.
  - Reading B: the body's exception wins, with the interrupt as a note. That swallows Ctrl-C or a pytest-timeout. HEAD already behaves as A, so the pin is green at HEAD and guards against the over-broad fix (W1).
  - **Recommend A.** If B is ruled, delete `test_an_interrupt_in_the_teardown_of_a_failing_body_still_propagates` and say so.
- **F2: "another LORE pytest session".** The Phase 0 doc describes the detector as keying on "executable plus lore path, never args text, per #228". **That is FALSE at HEAD `884ca63`:** `other_pytest_sessions` matches `any("pytest" in part for part in argv)` on every process on the box. Observed 2026-09-26:
  - It counts non-lore sessions (mobile-pricepaper-smoke pytest pids 3891491 and 3895372).
  - It counts an agent shell whose command TEXT mentions pytest: my own awk loop, pid 3895470. That is #228's self-match class, one level over.
  - A lore identity by `exe` fails, because the venv python resolves to `/usr/bin/python3.14`.
  - A lore identity by cwd-under-repo misses scratch-copy lore sessions (pid 3874001, cwd `…/scratchpad/ref`), and those DO hit the same test store.
  - Reading A: reuse as-is. False positives only ever cap the gate at 12, which is the safe direction. Cost: `concurrent_wire_acceptance` falsely refuses when an unrelated pytest or a shell mentioning pytest is live.
  - Reading B: narrow the detector, for example to cwd under a lore checkout or scratch copy. That needs a lore-identity definition, which is a design question.
  - My pins are **neutral**: live fixtures are lore-shaped under both readings, and no row asserts that a non-lore session is ignored. **Recommend A for this cycle**, with the #228 shell-self-match surfaced to the lead (a false refusal in the acceptance driver, not a gate risk).
- **F3: loader refusal of a hardcoded count** (`test_the_loader_refuses_a_hardcoded_worker_count`, 5 rows).
  - The ruling says only "the manifest must express it WITHOUT hardcoding a count". I enforced that at the STATE (manifest load) rather than only pinning the shipped file ("enforce at the state, not the path").
  - It rejects `-n <x>` unless x is `{workers}`, `-n<x>`, and `--numprocesses[=…]`, all in junit gates only. A junit gate with no worker flag still loads, as serial (control). The existing fixtures in test_gate_currency / test_wave_gate have no `-n`, so they are unaffected (they ran green against the reference build).
  - The lead may downgrade this to the shipped-manifest pin alone: delete the 5 refusal rows, and the placeholder control stays.

## Removed-behavior adjudication (what the build deletes or replaces)
| Removed / replaced behavior | Verdict | Pin / reason |
|---|---|---|
| `gates.yaml` pytest gate always runs `-n auto` | dropped-deliberately | Operator ruling 3 replaces it with the fleet policy (`auto` is still the alone branch) |
| `gates.yaml` pytest description "run with -n auto per CLAUDE.md's measured 9.6x" | dropped-deliberately | It becomes false. Pinned by the retired-literal description pin |
| `concurrent_wire_acceptance.other_pytest_sessions` defined locally | preserved-with-pin (moved) | ONE IMPLEMENTATION (Phase 0 item 3): identity re-export pin + one-definition AST pin. The existing `TestTheOtherSessionPreflight` still imports it from the driver and passed against the reference build |
| `_loud_teardown` failing branch: a stop raise REPLACES the body error | old-bug (R4), not re-pinned | Operator: fix now |
| `_loud_teardown` clean branch: a stop raise propagates | preserved-with-pin | Phase 0 item 2 ruling (clean-body control) |
| `_serve_migration_wire` inherits the 15 s default | dropped-deliberately | Operator ruling 1 |
| `DEFAULT_STARTUP_TIMEOUT_S = 15.0` | preserved-with-pin | Operator ruling 1. It was "measure-then-tune" and is now an exact ruled value |

**No existing pin was changed.** None asserts `-n auto` literally: I searched every `scripts/test_*.py`, `loremaster/tests/*.py` and `skills/lore-deploy/tests/*.py` with awk for `"auto"` / `-n auto` / `gates.yaml` / `resolved_command`. The hits are docstrings and unrelated `mode="auto"` values.

## RED receipt (HEAD `884ca63`, run 2026-09-26, `-n 4…12`)
```
R4   loremaster/tests/test_loopback_serving.py::TestAFailingBodyIsNeverReplacedByItsTeardown
     4 failed, 11 passed in 2.54s
     RED (behavioral, AssertionError "…teardown REPLACED the body's own _BodyFailure with _TeardownFailure(…)"):
       the 4 `raise` rows = {serve_asgi, serve_http} × {Exception, BaseException body}
     GREEN by design: completeness · 4 overrun rows · 2 clean-body controls · 4 interrupt (Reading A) rows

#503 loremaster/tests/test_migration_wire_budget_503.py
     4 failed, 1 passed in 18.28s
     RED behavioral: AST pin ("test_migration_wire.py:381 starts the heavy composition with NO startup_timeout_s")
                     spy pin ("handed serve_asgi startup_timeout_s=15.0; … must start under 60.0s")
                     slow-start pin (Failed: "a heavy start of >20.0s was reported as a startup timeout (15.0s budget)")
     RED needs-stub: test_the_heavy_budget_constant_has_the_ruled_value (AttributeError MIGRATION_WIRE_STARTUP_TIMEOUT_S)
     GREEN by design: default-stays-15 control

WORK scripts/test_pytest_workers_503.py
     24 failed, 2 passed in 1.28s
     RED behavioral (7): 5 × loader refusal (Failed: DID NOT RAISE ManifestError)
                          one-definition AST ("defined at ['concurrent_wire_acceptance.py:227']")
                          retired-literal description ("gate 'pytest''s description still says '-n auto'")
     RED needs-stub (17): 15 × ModuleNotFoundError _pytest_sessions · 2 × AttributeError WORKERS_PLACEHOLDER
     GREEN by design: shipped-manifest non-vacuity · serial-gate loader control
```
Totals: 46 tests (15 + 5 + 26), 32 red (14 behavioral + 18 needs-stub) and 14 green by design (11 + 1 + 2). mypy on the new files shows exactly the 4 pending-symbol `attr-defined` errors (1 in the budget file, 3 in the workers file, run with `MYPYPATH=scripts`), and ruff is clean.

⚠ **Gate currency:** if the lead commits this contract before the build, `typecheck` goes red on those 4 lines and `pytest` goes red on 32 tests. They need `scripts/pending_contracts.yaml` entries, or they are RED_ORPHANED. That file is outside my writable set, and it is already modified in the working tree by someone else.

## Satisfiability (reference build, scratch only)
- Copy: `./scripts/scratch_copy.sh …/scratchpad/ref503` (exit 0, provenance asserted). `loremaster.testing.loopback.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/c48cf6ae-617d-4986-9104-2c96fa8a4c45/scratchpad/ref503/loremaster/loremaster/testing/loopback.py`.
- Reference build (about 40 lines):
  - `_loud_teardown`'s failing branch wraps `stop` in `try/except Exception` → `add_note(f"server at {host}:{port} teardown raised {type}: {error}")`, with `else` keeping the overrun note, then a bare `raise`.
  - The constant plus `startup_timeout_s=MIGRATION_WIRE_STARTUP_TIMEOUT_S`.
  - The detector moved to `scripts/_pytest_sessions.py`, plus `pytest_worker_count`.
  - `WORKERS_PLACEHOLDER` substituted in `resolved_command` (at run time; own pids = {getpid, getppid}).
  - Loader refusal in `_must_be_neither_empty_nor_ambiguous`.
  - `gates.yaml` → `"-n", "{workers}"` and a new description.
- **226 passed / 0 failed** (34.2 s), over: test_loopback_serving, test_migration_wire_budget_503, test_migration_wire, test_pytest_workers_503, test_concurrent_wire_acceptance, test_gate_currency, test_pending_contract_gate, test_wave_gate.
- **Wrong builds** (scratch only, restored byte-exact with `cmp`):

| id | wrong build | result |
|---|---|---|
| W1 | R4 with `except BaseException` (notes interrupts too) | 4 failed / 11 passed (the 4 interrupt rows) |
| W3 | policy passes `own_pids=set()` | 3 failed (`only-own-pid`, both gate own-pid checks) |
| W6 | gate hand-rolls its own `/proc` scan (copy #2) | 4 failed (both gate branches' detector-call count, forwarded-alone, resolved-at-run) |

- **"What wrong build would still pass?"**, per pin family:
  - **R4:** a build that notes a raise but WRAPS the body exception (re-raises a new one with `from`) fails the identity check. A build that also swallows interrupts fails W1. **Survivor:** a build that leaks a thread only on the raise path until the rig releases (the release precedes the thread check). That is bounded, and it is the documented abandon semantics of R1.
  - **#503:** a build that passes 60 via a differently named constant fails the AST name check, which is deliberate: the ruling demands the named constant with its comment. **Survivor:** the constant's COMMENT (the derivation and the re-open trigger) is not pinned, because a regex over prose is the antipattern. It is a review item for the audit.
  - **Workers:** a policy returning "12" for ANY process (not just pytest) fails the `worker-and-non-test-process` row. **Survivor:** a detector narrowed to lore-only (F2 Reading B) passes every row. That is intended, since the pins are neutral pending F2.

## Stub expectations (symbols the contract imports that do not exist at `884ca63`)
1. `loremaster/tests/test_migration_wire.py::MIGRATION_WIRE_STARTUP_TIMEOUT_S` (module-level float). Once stubbed with a placeholder value ≠ 60.0, the value pin goes behaviorally RED.
2. `scripts/_pytest_sessions.py` (new module) exporting `PROC_ROOT`, `other_pytest_sessions(*, proc_root=PROC_ROOT, own_pids) -> list[tuple[int, str]]` (MOVED from `concurrent_wire_acceptance`, which re-exports it), `FLEET_CAPPED_PYTEST_WORKERS: str`, `SOLO_PYTEST_WORKERS: str`, and `pytest_worker_count(*, proc_root=PROC_ROOT, own_pids) -> str`. The policy must call `other_pytest_sessions` through the module global (the mutation-by-stub pins rely on it).
3. `scripts/pending_contract_gate.py::WORKERS_PLACEHOLDER = "{workers}"`.
- **Builder notes** (prose surfaces no gate checks — the P8d class):
  - `_loud_teardown`'s docstring and the `serve_asgi` / `serve_http` "Raises:" paragraphs describe only the overrun note. They must say a raising teardown is noted too.
  - `ServerShutdownTimeout`'s docstring says "When the served body is already raising, this is never raised". That stays true, but it names only the overrun.

## DRY ledger (new test-side symbols)
| new symbol | lore query run | what it returned | disposition |
|---|---|---|---|
| `_TeardownRig` / `_serve_asgi_rig` / `_serve_http_rig` | `lore_impact(serve_asgi)` → covering tests; read test_loopback_serving | existing `_RecordingApp(shutdown_gate)`, `_stuck_handler_class`, `_stick_a_request`, `_main_thread_interrupt` | REUSED all four (the rigs compose them; there is no second fixture) |
| `_fake_proc` (scripts test) | read `scripts/test_concurrent_wire_acceptance.py::TestTheOtherSessionPreflight._fake_proc` | a staticmethod on a test class writing cmdline only | HAND-ROLLED: the existing one is a private staticmethod of another test class, and it lacks the `cwd` symlink and non-pid entries F2-neutral fixtures need. Candidate to EXTEND if the lead prefers one helper |
| `_record_popen` | lore_search not run; `scripts/test_*` read via awk for `Popen` / `subprocess.run` recorders | `test_concurrent_wire_acceptance` has a process-group runner AST scan, not a recorder | HAND-ROLLED (a 10-line spy) |
| `_serve_asgi_calls_in_the_wire_fixture_home` | read `test_no_raw_listener_in_test_trees.py` (the AST scanner over test trees) | a raw-listener scanner keyed on bind/listen calls | HAND-ROLLED: a different predicate; 12 lines |

## Anything noticed outside this change
1. **F2's false description.** The Phase 0 doc says the detector keys on "executable plus lore path, never args text, per #228"; the code at `884ca63` matches args text. Consequence: `concurrent_wire_acceptance` refuses to start whenever ANY process's argv mentions "pytest" — an unrelated project's pytest, or an agent shell whose command text says pytest. That is the #228 self-match shape one level over. Raise to the operator: fix now, or ledger it?
2. **R4 at HEAD also affects `serve_http`.** `_stop_http_server` starts a helper thread on every stop. Under thread exhaustion (the measured door) the stop raises before any join, so both helpers are exposed. Both are covered by the generated pins.
3. **My scratch copy picked up other agents' in-flight working-tree edits** (`test_comms_footer.py`, `test_mcp_server.py`, `pending_contracts.yaml`, and `test_fixwave_a28_63c_i_a.py`, which differs from HEAD). The reference run passed over the suites listed, which do not include those files. I have no opinion on them. Noted only so the provenance of the 226 is exact.
4. **CLAUDE.md commentary.** The "Quality gates" bullet "Run pytest with `-n auto` (pytest-xdist)" stays correct for a lone session. **Recommend the lead add one line:** "the currency gate resolves `-n {workers}` via `scripts/_pytest_sessions.py::pytest_worker_count` — 12 when another lore pytest session is live, else auto (operator 2026-09-26)". Place it beside it, and keep the MEMORY.md landmine consistent. `test_the_shipped_manifest_names_every_gate_claude_md_still_spells_out` checks ids only, so nothing reddens either way.
5. **Cost:** the behavioral slow-start pin spends about 26 s of wall time per run: 20 s injected plus about 6 s for the heavy build. It is the only receiver-blind proof that the budget is effective. The lead may mark it `wire` or drop it if suite time matters more than that proof.
