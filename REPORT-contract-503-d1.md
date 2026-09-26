BRIEF CONFLICT: I refused to re-run the refactor's constructed survivor ("the refactor's constructed survivor must go RED", "the declared wrong builds killed"). Doing so is a contract-author → grader transfer, which brief-base v17 §2 ROLE BOUNDARY marks non-overridable. The survivor is DECLARED below, together with the exact assertion that should kill it. The kill proof belongs to the grader: an adversary re-grade, or refactor-503 re-running its own §6 build.

brief-base v17 read · brief project v7 read (lore_comms register, session `297217bd`, agent `contract-503-d1`)

# REPORT-contract-503-d1: tdd-light Phase 1 DELTA for lore #503 (the currency gate's worker count)

## SUMMARY BLOCK
- **State:** done-with-deviations. Tests only; nothing committed. Measured 2026-09-26 at HEAD `f66a190` plus the Phase 4 build in the working tree.
- **Deviations:**
  - (1) BRIEF CONFLICT above: the survivor was declared, not run.
  - (2) The brief asked for ONE F8 test that is GREEN and also asserts "the last worker flag is the policy's". On the current tree those two conditions contradict each other, so I split it into two tests. The pin-the-miss is GREEN. The harmlessness legs are ruling-1 pins and are RED (§Forks D1-F4).
  - (3) The ruling-4 pins are **GREEN** on the current tree, not RED, because the Phase 4 build already excludes its own pid on every path. They guard against the declared survivor (§RED).
- **Packages considered:** worker-count oracle → pytest's own `Parser` plus `xdist.plugin` option registration, `replace` for the test oracle. I read `_pytest/config/argparsing.py` (`allow_abbrev=False`) and probed live: `-n 2 -n 3`→3, `-qn3`→3, `--numproc 5`→None. These agree with the subprocess measurements in REPORT-refactor-503.md §6. Refusal parser: `_hardcoded_worker_counts`, REUSED per ruling 2. ⚠ The same oracle shows that the impl report's reason for hand-rolling that helper does not hold (§Noticed 1).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 7 new test-side symbols, all dispositioned (§DRY).
- **Graded:** n/a — this is an authored contract delta. Base: `f66a190` + working tree.
- **Decisions needed:**
  - D1-F1: the F8 loader-door reading. I pinned B.
  - D1-F2: refuse before ANY gate spawns. Pinned.
  - D1-F3: the refusal's exception type is spec-silent. The CLI exit 2 is pinned.
  - Noticed 1: the helper could be replaced by pytest's parser, which would close F8.
- **RED (current tree):** 33 failed / 109 passed across the 3 touched files. All 33 are new pins failing for behavioral reasons. All prior pins are green (§RED).
- **SAT (reference build, scratch):** **276 passed / 0 failed** over the 8-file gate, i.e. 226 prior + 50 new (§SAT).
- **Receipts:** §Tests · §RED · §SAT · §Pre-flight · §DUAL · §Forks · §Builder notes.

## Capability check (brief-base §4)
- lore tools: loaded and used (`lore_comms` register/heartbeat, `lore_search` for the DRY ledger).
- Fallback, said out loud: `scripts/` is not in lore's graph (#507, already filed by refactor-503, so I did not file a duplicate). I used **awk** over `scripts/*.py` and `skills/lore-deploy/scripts/*.py` to find the render-path call sites and the stale prose. grep/rg are hook-blocked (#473).
- Everything else the brief demanded was satisfiable. I ran no full suite, never touched :18500, and killed nothing. Every run used `-n 12`.

## Tests (what changed)
**`scripts/test_pytest_workers_503.py`**
- The module docstring now carries the d1 delta paragraph and the F9 fix: the detector "lives in `_pytest_sessions.py`, moved there by the #503 build".
- The `LORE_GATE_SESSION_ARGV` comment (F9) now describes the ALONE-branch render.
- One DUAL edit (§DUAL).
- New section 5:

| class | tests (count) | ruling |
|---|---|---|
| `TestThePolicyFlagIsTheLastWorkerFlag` | render-path completeness (1) · `test_the_policy_count_is_the_last_worker_flag` over 9 path×forwarded cases × 2 branches (18) · `…clustered_worker_flag_in_the_manifest_still_loses_to_the_policy` × 2 branches (2) | 1 (+ F8 harmlessness) |
| `TestForwardedWorkerFlagsAreRefused` | rows-are-the-helper's-spellings (6) · leg-runner refuses before any spawn (6) · gate CLI exit 2 (6) · wave CLI exit 2 (2) · control pass-through (3) · routes-through-the-shared-helper, mutation-by-stub (1) | 2 |
| `TestKnownBoundClusteredWorkerFlag` | pin-the-miss (1) | 3 |
| `TestTheGateNeverCountsItself` | own-pid over 4 render paths (4) | 4 |

**`loremaster/tests/test_loopback_serving.py`** (prose only, F4-tail): the three comments that called the startup default "measure-then-tune" now say it is operator-ruled (lore #503, 2026-09-26). The shutdown comment keeps "measure-then-tune", which is still true, but drops the stale "like the startup budget".
**`loremaster/tests/test_migration_wire_budget_503.py`** (prose only, F6): "6x the measured max" now reads "~6x the measured max (60 / 10.04 = 5.98x; exactly 4x the 15 s default)".

## The delta in plain English
1. **Ruling 1.** On every way the pytest gate's argv is built, the fleet policy's `-n <count>` is the LAST worker flag, and it comes after every forwarded arg or `--wave` selector. The four paths are `GateRunner.run` direct, `_run_selected_gates`, `pending_contract_gate.main --legs … -- <args>`, and `wave_gate.main --wave …`. Each is checked with another session live and with the gate alone.
   - Two instruments check it: pytest-xdist's own option parser must resolve exactly the policy's count from the captured argv (behavioral), and the policy's `-n` must sit after the forwarded run (state).
   - A clustered `-qn3` forwarded, or placed in the manifest after `-n {workers}`, must still lose.
   - The path set is hand-listed, so it carries a completeness pin: an AST sweep of the non-test scripts for callers of `_run_selected_gates` / `GateRunner(` must equal the driven set.
2. **Ruling 2.** Forwarded args carrying any spelling `_hardcoded_worker_counts` recognises are REFUSED before any gate spawns (typecheck included), with a message naming `pytest_worker_count`. The spellings are `-n auto`, `-n 3`, `-n12`, `--numprocesses 4`, `--numprocesses=auto`, and a trailing bare `-n`.
   - Both CLIs exit 2 and name the policy on stderr.
   - Forwarded args without a worker flag pass through unchanged.
   - A mutation-by-stub proves the refusal routes through the ONE helper: swap the helper and the refusal follows it both ways.
3. **Ruling 3 (KNOWN BOUND F8).** Three facts are pinned: the helper misses `-qn3`, the loader accepts it, and the forwarded path spawns with it. xdist really does honour it (3 workers). The failure message is the ruled one, and the re-open trigger is in the comment.
4. **Ruling 4.** The REAL detector runs over a fake `/proc` whose only pytest process is the gate itself. The result must be "auto" (not "12") on all four paths, and every detector call's `own_pids` must contain `os.getpid()`.

## RED receipt (HEAD `f66a190` + working tree, 2026-09-26)
```
$ uv run pytest -q -p no:cacheprovider --tb=line -n 12 scripts/test_pytest_workers_503.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_loopback_serving.py
33 failed, 109 passed, 20 warnings in 28.31s
$ uv run pytest -q -p no:cacheprovider --tb=no -n 12 scripts/test_pytest_workers_503.py   (after the mypy fix)
33 failed, 43 passed in 1.82s
```
All 33 failures are new section-5 tests. I grouped them by failure message:
- **16 ruling-1 matrix rows.**
  - 10 fail the state check: "the policy's -n N sits BEFORE the forwarded args in [...]". This happens on the selected, gate-cli and wave paths, both branches.
  - 6 fail behaviorally: "xdist would run '3' workers … says 'auto'/'12'". These are the clustered-F8 rows on the three forwarding paths.
- **2** manifest-clustered rows: "a manifest -qn3 after -n {workers} overrode the policy".
- **6** leg-runner refusal rows: "was NOT refused — a gate was spawned: [['./scripts/typecheck.sh']]".
- **8** CLI refusal rows (6 gate-cli + 2 wave-cli): "a gate was SPAWNED with a forwarded worker flag, not refused".
- **1** routing pin: "the shared helper flagged the forwarded args and the leg-runner spawned anyway".

**GREEN by design (17 new):**
- the 2 direct-path ruling-1 rows (a single `-n`, already last)
- the completeness pin
- the 6 rows-are-the-helper's-spellings
- the 3 pass-through controls
- the F8 pin-the-miss
- the **4 ruling-4 own-pid rows**. The current build resolves via `GateRunner.run` with `{getpid, getppid}` on every path, so it is correct and these pass.

Every prior pin stays green.

**Declared wrong build for ruling 4 (NOT run by me, see BRIEF CONFLICT):** REPORT-refactor-503.md §6 "D2 wrong build". There, `_run_selected_gates` pre-resolves `{workers}` via `pytest_worker_count(own_pids=set())`. Expected kill:
- `TestTheGateNeverCountsItself` rows `selected-forwarded`, `gate-cli-forwarded` and `wave-forwarded` should fail on both assertions.
  - First assertion: the real detector over the fake `/proc` counts the gate's own pid, giving xdist-resolved `12` ≠ `auto`.
  - Second assertion: the detector call carries `own_pids=set()`, which does not contain `getpid()`.
- The `direct` row should stay green.

That is a prediction from reading the build, not a measurement.

## SAT receipt (reference build in `./scripts/scratch_copy.sh` copy)
- Copy: `…/scratchpad/ref503d1`. scratch_copy asserted provenance. **`loremaster.__file__` = `/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/32523bd5-77af-473f-b123-6b1674f72e32/scratchpad/ref503d1/loremaster/loremaster/__init__.py`**, and `pending_contract_gate.__file__` is `…/ref503d1/scripts/pending_contract_gate.py`.
- The reference build is about 30 lines in `scripts/pending_contract_gate.py`, on top of the Phase 4 tree:
  - `GateRunner.run` renders `spec.resolved_command(junit_xml)` with the placeholder left in place. A new `_with_policy_workers_last` then drops the `-n {workers}` pair wherever it sits and appends `-n <policy count>` last.
  - `_run_selected_gates` calls `_hardcoded_worker_counts(pytest_args)` at entry, before the loop. If that returns anything, it raises `ManifestError("forwarded pytest args … carry an xdist worker count … the fleet policy (_pytest_sessions.pytest_worker_count) decides …")`.
  - `resolved_command` and the manifest are unchanged.
```
$ uv run pytest -q -p no:cacheprovider --tb=line -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py scripts/test_pytest_workers_503.py scripts/test_concurrent_wire_acceptance.py scripts/test_gate_currency.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py
276 passed, 22 warnings in 30.70s
$ uv run pytest -q -p no:cacheprovider --tb=no -n 12 scripts/test_pytest_workers_503.py   (after the mypy fix, re-synced)
76 passed in 2.00s
$ uv run ruff check scripts/pending_contract_gate.py scripts/test_pytest_workers_503.py   (scratch)
All checks passed!
```
Lint legs on the real tree for the three touched files: `ruff check` clean · `ruff format --check` "3 files already formatted" · `MYPYPATH=scripts mypy scripts/test_pytest_workers_503.py` "Success: no issues found".

## Adversarial pre-flight (each item → covering case, or scoped-out)
| # | Realistic failure | Covered by |
|---|---|---|
| 1 | Forwarded `-n auto` (the CLAUDE.md habit) silently overrides the policy | refusal rows `short-separate-auto` on leg-runner and gate CLI |
| 2 | Each spelling the helper knows gets through a hand-picked subset refusal | 6 rows × 2 surfaces, plus rows-are-the-helper's-spellings |
| 3 | Refusal done by a SECOND parser (copy #2) | `test_the_refusal_routes_through_the_shared_helper` (mutation-by-stub, both directions) |
| 4 | Refusal fires only when the pytest leg is reached, after minutes of typecheck | leg-runner rows pass ALL manifest ids and assert `spawned == []` (fork D1-F2) |
| 5 | Refusal raises an exception the CLIs don't catch (traceback, not exit 2) | gate-CLI and wave-CLI exit-2 pins |
| 6 | Over-refusal: legitimate forwarded args (`-x`, `-k`, `-p no:…`, `-rfE`, selectors) rejected or mangled | 3 pass-through controls (contiguous, in order, unchanged) |
| 7 | Policy flag rendered BEFORE the forwarded args, so a clustered flag wins | ruling-1 state check + clustered-F8 behavioral rows |
| 8 | Fixed on `_run_selected_gates` but not on a CLI path, or the reverse | 4 render paths, generated completeness over AST callers |
| 9 | Manifest carries a clustered flag after the placeholder | manifest-clustered rows (fork D1-F1) |
| 10 | Two `-n` rendered (placeholder substituted in place AND appended) | the pre-existing `_workers_in` "exactly one -n" on every forwarded/direct render; the reference build proved that satisfiable |
| 11 | Forwarded args lost or reordered when the policy flag moves | DUAL-edited contiguity assertion + ruling-1 `forwarded_start is not None` |
| 12 | Own pid counted on a forwarding path (the survivor) | `TestTheGateNeverCountsItself` × 4 paths, real detector over a fake `/proc` |
| 13 | Wrong unit/scale: `auto` vs integer, or the placeholder leaking into argv | xdist-resolved string compare; no-placeholder assertion on every matrix row |
| 14 | Zero/degenerate: bare `-n` with no value | `flag-without-value` row |
| 15 | Abbreviated long flag (`--numproc 5`) | scoped out, **measured**: pytest's parser sets `allow_abbrev=False`, so `--numproc 5` resolves to None. It is not a door |
| 16 | `--maxprocesses`, `-p no:xdist`, `-o addopts=…`, `PYTEST_ADDOPTS` | **SIBLINGS NOT TRIED**, surfaced in §Noticed 3. None is a spelling the helper recognises, so ruling 2 does not cover them |
| 17 | Hostile rendered text | scoped out: nothing renders stored free text |

## Realism & independence
- ☑ **Production-realistic inputs.** The forwarded args are real selectors from this repo plus flags agents actually pass. `-n auto` is CLAUDE.md's own habit. The `/proc` argv is the gate-leg shape observed live (contract-503).
- ☑ **Independent expected values.** The expected counts are the ruled constants `RULED_WORKERS_*`. The "which count runs" oracle is xdist's own parser, not the implementation's placement logic. Its agreement with REPORT-refactor-503.md §6's spawned-worker measurement is cited.
- ☑ **Seam coverage.** The real handoff is exercised: CLI argv → argparse → `_run_selected_gates` → `GateRunner.run` → `subprocess.run` → the `Popen` argv, on both CLIs. The wave leg narrows only the manifest (to the shipped junit gate, verbatim), so the typecheck leg is not spawned first.
- ☐ **Magnitude bound on derived outputs.** Not applicable: the worker count is a two-valued ruled enum, not a derived magnitude.
- ☑ **Shared conventions.** `WORKERS_PLACEHOLDER` and the policy name (`pytest_worker_count.__name__`) are read from production. The flag spellings are xdist's external CLI, copied independently on purpose (the same stance as F10).
- ☐ **Hostile fixtures.** Not applicable: no stored free text is rendered.
- ☑ **Input accounting.** Every forwarded token has one fate, and each fate is forced by a fixture:
  - refused (6 spellings)
  - passed through unchanged (3 controls, plus the matrix rows)
  - passed through but overridden (the clustered F8 case)

## DUAL rows (pins whose assertion changed)
| pin | was | now | why |
|---|---|---|---|
| `TestTheGateRendersTheResolvedCount::test_forwarded_pytest_args_keep_the_policy_count` | `argv[-len(forwarded):] == forwarded`, i.e. the forwarded args at the argv TAIL | `_contiguous_run_start(argv, forwarded) is not None`, i.e. they arrive unchanged, contiguous and in order. Their position relative to the policy flag is pinned more strongly by the ruling-1 matrix | Ruling 1 places the policy's `-n` AFTER the forwarded args, which the tail pin contradicts. The comment is in place |

No other assertion changed. The prose edits (F4-tail/F6/F9) touch only comments and docstrings.

## Forks (two readings; my pick written down; the lead or operator rules)
- **D1-F1: "the rendered argv's LAST worker flag is still the policy's" at the LOADER door.**
  - Reading A: forwarded path only. A manifest may place `-qn3` after the placeholder and win.
  - Reading B (pinned): a property of every rendered argv, so the policy flag also follows manifest tokens. This forces "append last" over "insert forwarded before the pair".
  - I pinned B because ruling 1 says "ENFORCE AT THE STATE". The shipped-manifest pin (`_workers_in` = one `-n` carrying the placeholder) does not stop a shipped `-qn3` beside it, so under A F8 would NOT be harmless for the shipped gate.
  - If A is ruled, delete `test_a_clustered_worker_flag_in_the_manifest_still_loses_to_the_policy`.
- **D1-F2: when the refusal fires.**
  - Pinned: before ANY gate spawns.
  - Alternative: when the pytest leg is reached, after typecheck and ruff have already run.
  - I recommend the pin: a usage error found after minutes of typecheck wastes that time and reads like a half-run. Relax it by passing `[spec.id]` instead of `manifest.ids` in the leg-runner rows.
- **D1-F3: the refusal's exception type is spec-silent.**
  - The leg-runner pin is type-agnostic (it must not be the spawn sentinel, and it must name the policy). The CLI pins require exit 2 plus the policy on stderr.
  - The reference build used `ManifestError`. pcg then prints **"MANIFEST ERROR:"** for a refused *CLI argument*, which is a mislabel an LLM reader would see. Alternative: a typed error that both mains catch.
  - Builder's or lead's call. The pins accept either.
- **D1-F4: a brief-internal contradiction.** The brief wanted one F8 test asserting both "the refusal misses it" AND "the last flag is the policy's", and also wanted the F8 pin GREEN. On the current tree the second half is false (`-qn3` lands after `-n auto`). So the miss is the GREEN `TestKnownBoundClusteredWorkerFlag`, and harmlessness is carried by the RED ruling-1 rows `*-clustered-F8` and by the manifest-clustered rows.

## Builder notes (prose surfaces no gate checks)
- `pytest_args` argparse help (`"extra arguments forwarded to the pytest gate"`), the `_run_selected_gates` docstring, the `wave_gate` forwarding comment ("the leg-runner appends them to the junit-reader gate's command alone") and the gates.yaml FIELDS header: each must now say that worker flags are refused, and that the policy flag is rendered last.
- `GateSpec.resolved_command`'s docstring says it substitutes `{workers}`. If the builder moves worker rendering out of it (as the reference did), update both that docstring and the `GateRunner.run` docstring that refactor-503 just edited (F12).
- CLAUDE.md "Run pytest with `-n auto`" is correct for a lone *manual* run, but forwarding it to the gate is now refused. contract-503 §Noticed 4 already recommends a commentary line. Extend it to say "don't forward `-n` to the gate".

## Noticed (surfaced, not dropped)
1. **The hand-roll verdict on `_hardcoded_worker_counts` looks wrong, measured.** REPORT-impl-503.md's DRY ledger says argparse "does not fit: it would need xdist's full option table to parse a foreign argv". pytest's own parser plus `xdist.plugin` IS that table. My oracle (`_xdist_option_parser`, three lines) resolves every spelling, including `-qn3`, and last-wins. Using it in the gate would close F8 outright.
   - Caveat: it relies on private pytest API (`_pytest.config.get_config`, `config._parser`), which is why I only use it as a TEST oracle.
   - Operator call: `replace_with_adapter` (and close F8) vs `keep_with_trigger` (F8's trigger). This is the packages-over-hand-rolling rule's "asserted a limitation without reading" shape.
2. A forwarded `-n {workers}` (the placeholder itself) is not refused, because the helper excludes the placeholder. It is harmless: it is resolved or stripped. I did not pin it.
3. **Siblings not tried** (CLASS = "every forwarded arg that changes xdist's worker count"): `--maxprocesses=<n>`, `-p no:xdist` (turns `-n` into a usage error, which is loud), `-o addopts=…` and `PYTEST_ADDOPTS` (addopts are prepended, so argv last-wins should still hold, but this is unmeasured). Ruling 2 limits itself to the helper's spellings, so these are open.
4. The wave CLI can only carry a dash-led worker token through `--wave=<token>`. argparse rejects `--wave x.py -n 3` before any policy runs, which is a loud usage error. So only the joined spellings are wave-refusal rows.

## DRY ledger (new test-side symbols)
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_xdist_option_parser` / `_xdist_resolved_workers` | `lore_search("parse pytest command line argv numprocesses xdist worker count helper in tests")` | only report prose (REPORT-refactor-503 §6 subprocess probe, REPORT-impl-503 ledger); no in-tree helper | HAND-ROLLED as a thin adapter over pytest's own parser (the package does the parsing) |
| `_contiguous_run_start` | same search; awk over `scripts/test_*.py` for sub-sequence helpers | none | HAND-ROLLED (6 lines) |
| `_one_gate_manifest` | same search | none. `_manifest_with` (this file) builds a TEMPLATE gate, not a verbatim shipped spec | HAND-ROLLED; it complements `_manifest_with` |
| `_wave_cli_argv`, `_render_on`, `_cli_outcome` | awk over `scripts/test_wave_gate.py` / `test_pending_contract_gate.py` for main-driving helpers | test_wave_gate drives `main` with its own fixtures, which do not capture the `Popen` argv | HAND-ROLLED (render-path dispatcher local to this contract) |
| (reused) `_fake_proc`, `_record_popen`, `_stub_detector`, `_manifest_with`, `_workers_in`, `_shipped_worker_sized_gates` | — | this file | REUSED |

## Unrelated failures
None in the scoped runs. The 8-file gate ran 0-failed in scratch. I did not run typecheck.sh. refactor-503 recorded 60 pre-existing mypy errors in other packets' files.
