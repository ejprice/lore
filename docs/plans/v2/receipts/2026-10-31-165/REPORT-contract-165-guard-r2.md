# REPORT-contract-165-guard-r2

brief-base v24 read · brief project v7 read
- **State:** done-with-deviations. Contract extended with 10 pins for the ruling's ∀ phase property: 8 phase doors, one ∀-neighbour pin, one control.
- **Deviations:** (1) 4 contract runs, not 2: one door (import + module-level skip) was added after legs 1–2 launched and declared before its run. (2) Original declaration had the xfail pin GREEN on the reference; it went RED (pytest's xfail absorbs a teardown failure too) — §Declared-vs-observed.
- **Pins → wrong guard:** §Pins table. In short: fixture-window recorders (the reference) miss module/class setup and module/session teardown; next-setup checkers mis-charge (∀-neighbour pin); a passed-only flipper misses skip, import-skip and xfail; no collection charging misses both import doors.
- **Reference guard (declared → observed):** 7 declared RED → 7 RED; plus `[attempt in an xfail-marked test]` declared GREEN → observed RED (declaration wrong, RED genuine). 0 declared reds stayed green. Old 31 + ∀-neighbour + control pass. Final: 8 failed / 33 passed.
- **Build leg (committed `8d8b2fa` conftest, real tree):** 41 passed, 0 failed (31 old + 10 new). No build defect found.
- **Provenance:** scratch `loremaster.__file__` = `/var/tmp/claude-1000/guard-r2-scratch/loremaster/loremaster/__init__.py`; `scratch_copy.sh --verify-only` exit 0; reference conftest `cmp`-identical.
- **Gates:** ruff clean; currency `--legs typecheck,ruff`: typecheck RED_ADJUDICATED (owned), ruff GREEN, no RED_ORPHANED — but EXIT 1 because the deselected pytest leg reads ORPHAN → **finding #565**.
- Packages considered: none — no mechanism specified · Odoo-20 portability: n/a — no Odoo seam touched · Reuse ledger: no rule-deciding symbol; `_run_inner`/`_mirror_repo` EXTENDED · Graded: n/a (author).
- **Decisions needed:** F1 session-teardown = node report (picked) vs "charged anywhere"; F2 xfail judged via junit (picked); Q1 function-scope door? Q2 xdist phase doors? Q3 `--continue-on-collection-errors` OK? — §Forks.
- **Pointers:** §Contract · §Pins · §Runs · §Declared-vs-observed · §Forks · file `skills/lore-deploy/tests/test_prod_store_guard.py` (`PHASE_MODULES`, `TestEveryAttemptFailsTheNodeWhosePhaseMadeIt`, `TestPhaseControlWithoutAnyGuard`).

## Routing table (written before the first sweep, 2026-10-31)
| step | tier | who | reason |
|---|---|---|---|
| read brief-base, ruling addendum, contract file, impl D1–D3 | 3 | self | inputs to the contract design |
| design inner doors + outer pins | 3 | self | contract design (never Haiku) |
| scratch copy via `scratch_copy.sh` | 1 | self | one command on my critical path; nothing overlaps it |
| contract run, real tree (build leg) | 1 | haiku-runner | test run |
| contract run, scratch + reference guard (discrimination leg) | 1 | haiku-runner | test run |
| `--collect-only` declaration of expected reds | 1 | self | must be fixed by me BEFORE the run; the node list is short |
| ruff + currency `--legs typecheck,ruff` | 1 | haiku-runner | gate runs |
| declared-vs-observed diff verdict | 3 | self | judgment over a grader-shaped result |

## Declaration — written BEFORE any run against the reference guard (2026-10-31)
Node ids from `--collect-only` (real tree, contract file as edited). Prefix
`skills/lore-deploy/tests/test_prod_store_guard.py::TestEveryAttemptFailsTheNodeWhosePhaseMadeIt::test_attempt_fails_the_node_whose_phase_made_it`:

**Declared RED under the reference guard** (`/var/tmp/claude-1000/guard-ref/conftest.py`, clear-at-function-setup / fail-at-function-teardown):
1. `[module-scoped fixture setup]` — attempt made before the reference's `clear()`; discarded.
2. `[class-scoped fixture setup]` — same.
3. `[module-scoped fixture teardown]` — attempt made after the reference's teardown check; cleared at the next setup.
4. `[session-scoped fixture teardown]` — after the last check; dropped.
5. `[module import (collection)]` — no collection charging; discarded by the first `clear()`.
6. `[attempt followed by pytest.skip]` — the module fixture skips before the reference's function fixture is set up, so no check runs.

**Declared GREEN under the reference guard:**
- `[attempt in an xfail-marked test]` — the reference fails at the TEARDOWN phase, which xfail does not cover. This pin catches a different wrong guard (one that flips only a `passed` report); the reference is not it. The ruling-addendum sentence "the reference guard goes RED on each new pin" does not hold for this pin; see §Forks.
- `TestEveryAttemptFailsTheNodeWhosePhaseMadeIt::test_no_node_whose_phases_made_no_attempt_is_charged` — the reference drops attempts rather than mis-charging them.
- `TestPhaseControlWithoutAnyGuard::test_every_phase_inner_test_passes_without_a_guard` — no conftest in play.
- all 31 pre-existing pins.

### Declaration amendment — written BEFORE the run that includes it (2026-10-31)
Added after runs 1 (build leg) and 1 (reference leg) were LAUNCHED on the earlier text, before either returned:
`...::test_attempt_fails_the_node_whose_phase_made_it[module import followed by a module-level skip]`
— **declared RED under the reference guard** (import-time attempt discarded by the first `clear()`; the module
skips at collection, so no check runs). Reason it is a separate pin from `[module import (collection)]`: the
idiom "probe the store at import, `pytest.skip(allow_module_level=True)` when unreachable" yields a SKIPPED
collect report, not a passed one; a guard that fails only a passed or errored collect report waves it through.

## Contract (plain English) — `skills/lore-deploy/tests/test_prod_store_guard.py`, base `8d8b2fa`, measured 2026-10-31
The guard's earlier pins drive attempts only from inside a test's CALL. These pins drive them from every other
phase. Seven inner modules run as ONE isolated session, in a fixed order, inside the existing netns/stub
machinery (`_mirror_repo`, `_run_inner`, `_parse_junit`). Every attempt is swallowed, so only a recorder that
charges the right report can fail the right node:

| inner door (module, in run order) | node that MUST fail (and name 18500) | innocent node that MUST NOT |
|---|---|---|
| `test_inner_phase_import.py`: swallowed attempt at import | its COLLECTION case (`skills.lore-deploy.tests.test_inner_phase_import`) | `test_phase_innocent_first`, the first test the session runs |
| `test_inner_phase_import_skip.py`: probe at import, `pytest.skip(allow_module_level=True)` when unreachable | its collection case (a SKIPPED collect report otherwise) | same |
| `test_inner_phase_module_setup.py`: module fixture dials at setup | `test_module_fixture_first_user` (NOT the module's first test) | `test_phase_innocent_first`, `test_module_fixture_second_user` |
| `test_inner_phase_class_setup.py`: class fixture dials at setup | `test_class_fixture_first_user` | `test_class_fixture_second_user` |
| `test_inner_phase_module_teardown.py`: module fixture dials at teardown | `test_module_teardown_fixture_user` (its last test) | `test_innocent_after_module_teardown` (next module's first test) |
| `test_inner_phase_skip_xfail.py`: module fixture probes and SKIPS when unreachable | `test_skip_fixture_first_user` | `test_skip_fixture_second_user` (stays `skipped`: cached skip, no attempt) |
| same module: `@pytest.mark.xfail` test whose raw `connect` is refused | `test_xfail_marked_attempt` | — |
| `test_inner_phase_session_teardown.py`: session fixture dials at teardown | `test_session_teardown_fixture_user` (the session's last test) | — |

Outer pins (10 new, all in the real tree's file):
- `TestEveryAttemptFailsTheNodeWhosePhaseMadeIt::test_attempt_fails_the_node_whose_phase_made_it[<door>]` × 8 — the charged node is `failed`/`error` AND its text names `18500` (reuses `_assert_blocked_and_named`).
- `TestEveryAttemptFailsTheNodeWhosePhaseMadeIt::test_no_node_whose_phases_made_no_attempt_is_charged` — ∀ reported nodes not charged: exact expected outcome (`PHASE_UNCHARGED_OUTCOME`). Quantified over nodes, not over doors.
- `TestPhaseControlWithoutAnyGuard::test_every_phase_inner_test_passes_without_a_guard` — the same seven modules with conftests and plugins disabled: every inner test passes. The import-time probes, the probe fixture and the xfail test all succeed against the stub, so no door "fails for a fixture reason".

Mechanical changes to the existing machinery (no old assertion weakened): `_run_inner` gained `modules`,
`must_report`, `may_report` (old runs pass the old values, so their exact-set check is unchanged); `_mirror_repo`
writes the phase modules into both trees; the phase run passes `--continue-on-collection-errors`, because pytest
otherwise interrupts the session at the first collection error and the later modules never run.

## Pins → the wrong guard each catches
| pin | wrong guard it catches (none built by me — role boundary) |
|---|---|
| `[module-scoped fixture setup]`, `[class-scoped fixture setup]` | clear-the-record when the test's own function fixture sets up (the reference guard) — discards a shared fixture's attempt |
| `[module-scoped fixture teardown]` | check-at-function-teardown (reference): the module fixture tears down after the check. Plus "check pending at the NEXT setup": charges the innocent next test (∀-neighbour pin) |
| `[session-scoped fixture teardown]` | any guard whose last check runs before session teardown — the attempt is dropped |
| `[module import (collection)]` | any guard without collection charging — discarded, or charged to the first test run (∀-neighbour pin) |
| `[module import followed by a module-level skip]` | a guard that fails only a passed/errored collect report; the skip idiom yields a SKIPPED one |
| `[attempt followed by pytest.skip]` | "flip a passed report to failed" (a skipped report is waved through); also the reference (no check runs after a higher-scope fixture skips) |
| `[attempt in an xfail-marked test]` | "flip passed only"; also ANY guard that fails via an exception in ANY phase — pytest 9.0.3 `_pytest/skipping.py::pytest_runtest_makereport` converts an exception from setup/call/teardown of an xfail-marked test to `xfailed` (the reference) |
| `test_no_node_whose_phases_made_no_attempt_is_charged` | "charge whoever runs next", or never draining the record |
| phase control | a broken door: every RED above must be the guard's doing |

## Adversarial pre-flight (each → case or note)
- Attempt in a shared fixture, module/class scope → setup pins. Function-scope fixture setup/teardown: NOT given its own door. Every plausible wrong guard I could name that misses a function fixture also misses a module fixture, so the module/class doors subsume it. This is a consolidation call; the lead may want the door.
- Attempt in a fixture TEARDOWN, module/session → teardown pins.
- Attempt at import → import pin; import + module-level skip → import-skip pin.
- Attempt then skip, the realistic "probe, skip if unreachable" → skip pin. The guard's own refusal causes the skip.
- xfail mark absorbing the refusal → xfail pin.
- Mis-attribution to the next innocent node / never draining → ∀-neighbour pin, with an innocent node placed after every door.
- xdist for the phase doors → NOT TRIED. The recorder-in-every-worker is pinned by the existing xdist pins. Session teardown under xdist lands on each worker's last item, which nobody controls. See §Forks Q3.
- Production-realistic values: port read from env (inner-port-from-env rule kept); `18500` in a failure text can only come from the guard.

## Realism clauses
- ☑ Production-realistic inputs: the doors are the shapes real lore fixtures take (shared probe fixture, skip-if-unreachable, import-time probe). The port comes from the same source as the old pins (`PROD_STORE_PORT`, cited to `_scaffold_lore_yaml`).
- ☑ Independent expected values: the charged node of each door is derived from pytest's documented phase model (a fixture runs in the setup/teardown phase of the item that first/last needs it). The control run confirms each door passes unguarded. Nothing is read from the build.
- ☑ Seam coverage: the inner session loads the real conftest chain through the mirror. junit is the seam read; the collect-case name comes from `_pytest.junitxml.mangle_test_address`, read in pytest 9.0.3.
- ☐ Magnitude bound: not applicable because the pins assert outcomes and texts, not derived numbers.
- ☑ Shared conventions: same constants and env names as the existing pins; no new literal port.
- Hostile fixtures for rendered stored text: not applicable, no stored text is rendered.
- Input accounting: applies in spirit. Every inner node has exactly one fate: charged (`PHASE_CHARGED`) or uncharged with an exact outcome (`PHASE_UNCHARGED_OUTCOME`). `_run_inner`'s `must_report`/`may_report` rejects unknown or missing nodes. Each fate is forced by a fixture; the control proves each door's attempt actually runs.

## Packages
Packages considered: none — no mechanism specified (the contract pins a property; the mechanism is the build's, `REPORT-impl-165-guard.md` §Decisions).
Odoo-20 portability: n/a — no Odoo seam touched.
Reuse ledger: new symbols are test-module constants and inner-source strings plus `_INNER_PHASE_PRELUDE._swallowed_attempt` (inner, mirrors the existing `test_swallow_any_exception_around_create_connection` body). All REUSED existing helpers (`_run_inner` EXTENDED with three keyword params, `_assert_blocked_and_named`, `_parse_junit`, `_mirror_repo` EXTENDED). No rule-deciding function introduced.

## Runs (each a haiku-runner; I read every count line in the log myself)
| # | label | file text | result | log |
|---|---|---|---|---|
| 1 | build leg, real tree, committed `conftest.py` (`8d8b2fa`) | before the import-skip amendment (40 pins) | **40 passed**, EXIT 0 | `scratchpad/build-leg-1.log` |
| 2 | reference leg, scratch + reference guard | same | **7 failed, 33 passed**, EXIT 1 | `scratchpad/ref-leg-1.log` |
| 3 | build leg (re-run after adding the import-skip door) | final (41 pins) | **41 passed**, EXIT 0, no ImportError | `scratchpad/build-leg-2.log` |
| 4 | reference leg (re-run, same reason) | final | **8 failed, 33 passed**, EXIT 1 | `scratchpad/ref-leg-2.log` |
More than 2 runs, because I added one door after legs 1–2 launched. Its declaration was written before the run that included it. (Scratchpad = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/81673450-8699-4e0e-98f1-bd89dc33af88/scratchpad/`; session-local, not durable. The counts above are the record.)

## Declared-vs-observed (reference guard), both directions
- Declared RED (7 = 6 + the amendment) → all 7 observed RED. The failure messages show the right reasons: `outcome=passed` for module setup, class setup, module teardown and session teardown; `outcome=skipped` for the skip fixture and the import-skip collect case; the import collect case was `never reported`, because the reference collected the module cleanly.
- **Declared GREEN, observed RED: `[attempt in an xfail-marked test]`. My declaration was WRONG.** I believed xfail covers only the call phase. pytest 9.0.3 `_pytest/skipping.py::pytest_runtest_makereport` (`elif not rep.skipped and xfailed: if call.excinfo: …`) converts an exception from ANY phase of an xfail-marked test to `xfailed`. So the reference's teardown `pytest.fail` was absorbed (observed `outcome=skipped`). I read that source AFTER the run. The RED is genuine: the reference violates the property. The pin catches strictly more than I declared.
- Declared GREEN, observed GREEN: the ∀-neighbour pin, the phase control, all 31 old pins.
- Unexpected reds: none besides the xfail one above. Declared reds that stayed green: none.

Provenance (scratch): `/var/tmp/claude-1000/guard-r2-scratch/.venv/bin/python -c "import loremaster; print(loremaster.__file__)"` → `/var/tmp/claude-1000/guard-r2-scratch/loremaster/loremaster/__init__.py`. `scratch_copy.sh --verify-only` exit 0. The scratch root `conftest.py` is byte-identical (`cmp`) to `/var/tmp/claude-1000/guard-ref/conftest.py`, checked before both reference legs. No `skills/lore-deploy/**/conftest.py` exists in scratch. The scratch contract file is byte-identical to the real tree's, checked before each leg. The mirror resolves `REPO_ROOT` from the contract file's own path, so scratch runs mirror scratch's conftest.

## Gates
- ruff `skills/lore-deploy/tests/test_prod_store_guard.py`: All checks passed (final text).
- `pending_contract_gate.py --currency --legs typecheck,ruff` (final text, run 2): typecheck RED_ADJUDICATED (83 residuals, owned by packet-58-contract / packet-64b-i-contract; `test_prod_store_guard` appears 0 times in the log), ruff GREEN, **no RED_ORPHANED**. The command still EXITS 1 with `CURRENCY: FAIL — claimed but never run: pytest`: the deselected pytest leg renders as ORPHAN. That contradicts CLAUDE.md's per-round use of this exact command → filed **finding #565**. Not mine to fix.

## Forks (both readings written; my pick named)
- **F1 — session-teardown attribution.** (a) The ruling's text: the attempt fails the report of the node whose phase it ran in, i.e. the session's LAST item, at teardown. (b) The brief's gloss: "charged somewhere, never dropped" — e.g. a session-level failure (exit status / `sessionfinish` message) with no node report. I pinned (a). A guard doing only (b) fails `[session-scoped fixture teardown]`. The build does (a).
- **F2 — xfail is read through junit.** A guard that sets `outcome="failed"` but leaves `wasxfail` makes pytest's exit status fail, yet junit files it as `skipped` ("xfail-marked test passes unexpectedly", no port text). The pin rejects that guard. My pick: keep it. junit is a consumer surface, and a junit "skipped" is the silent green this wave exists to prevent. Alternative: judge by the inner exit status plus terminal text.
- **F3 — the ruling addendum's discrimination sentence.** It holds for all 8 phase-door pins, measured above, but for the xfail pin it holds for a different reason than the addendum implies (see the declared-vs-observed section).
- **Q1 (scope, the lead's call):** a separate function-scoped fixture setup/teardown door was consolidated away (§Adversarial pre-flight). Add it?
- **Q2 (scope):** the phase doors run in ONE tree (`tests`), serial. Tree liveness and per-worker recording are already pinned by the old pins. Phase doors under xdist were NOT TRIED. Want them?
- **Q3:** `--continue-on-collection-errors` on the phase run (needed so one session reaches every door). It changes only session continuation, not reporting. Flagging it in case the lead wants the import doors in their own session instead.

## Noticed outside this change
- The haiku-runner for run 2 misreported four failure outcomes as `skipped` (the log says `passed`). I caught it by reading the log. Brief-base already says a runner's output is a claim; this one would have mis-stated why the reference failed.
- Finding #565 (above).

## Fan-out
Routing table at top. haiku-runner × 6 (4 contract runs, 2 currency runs) · sonnet 0 · peak 3. Kept inline: scratch copy, collect-only, ruff (each one command on the critical path), and every judgment step.
