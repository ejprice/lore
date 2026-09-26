brief-base v17 read · brief project v7 read (lore_comms register, session `297217bd`, agent `refactor-503`)

# REPORT-refactor-503 — tdd-light Phase 5 (REFACTOR + AUDIT): #503 heavy wire budget · R4 · currency-gate workers

## SUMMARY BLOCK
- **State:** done-with-deviations. Measured 2026-09-26 on HEAD `f66a190` + the uncommitted tree. Nothing committed.
- **Deviations:** (1) No de-bloat was applied (§3). (2) My first `ruff check` invocation included `gates.yaml`, and ruff parsed it as Python ("153 errors"). That was my invocation error, not a defect; the Python-only run is clean (§4). (3) I found the lore graph does not contain `scripts/` (filed as **#507**), so the consumer sweep used awk.
- **Packages considered:** none — no mechanism specified. This pass only edits docstrings and comments. On the builder's side, psutil `keep_with_trigger` stands as they recorded it.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new symbols (§5 carries the index checks run against the builder's 6).
- **Graded:** `f66a190` + working tree · HEAD-at-report: `f66a190` · SAME.
- **Decisions needed:**
  - **(a)** Forwarded `-n` overrides the policy, and I measured that the last `-n` wins. Choose between refusing it at `_run_selected_gates` (recommended, reusing `_hardcoded_worker_counts`) and documenting it as an override (§1a).
  - **(b)** Missing pin: `own_pids` on the forwarded path. A constructed survivor passes 26/26 (§1b).
  - **F8:** `-qn3` escapes the loader refusal (measured). Choose between extending the refusal and pinning it as a bound.
  - **F4-tail / F6 / F9:** stale contract prose (routed).
- **Headline:** R4 / #503 / workers implementation matches the contract. There are 0 behaviour defects in the implementation. 4 prose fixes were applied (F4, F5, F6, F12). 4 items are routed to contract: (a), (b), F8, and the prose nits.
- **Gates:** 226 passed / 0 failed · skills 120 passed · ruff clean · format clean on formatter-clean files. On the 2 files that are format-red at HEAD, the hunk count is unchanged (28/28 and 10/10). typecheck: 60 errors, **0 in touched or contract files** (§4).
- **Receipts:** §1 findings · §2 smell list · §3 refactors · §4 gate tails · §5 DRY · §6 instruments (pasted) · §7 deletions.

## 1. Cold review findings (written BEFORE any edit; graded tree = HEAD `f66a190` + the uncommitted working tree)

Classes: **fixed** (in place, prose or quality, no behaviour change) · **routed-to-contract** (needs a pin or a behaviour change, so it is a CONTRACT decision, not a refactor) · **not-a-defect** (with the reason).

### Adjudications the brief asked for

**(a) Forwarded `pytest_args` can carry a second `-n` → ROUTED-TO-CONTRACT (a hole in the lifted class, documented nowhere).**
- *Measured, 2026-09-26* (scratch probe, instrument pasted in §6): with `pytest -n 2 -n 3`, xdist started **3** workers (`PYTEST_XDIST_WORKER_COUNT=3`). The control, `-n 2` alone, started 2. **The last `-n` wins**, so a forwarded `-n X` silently overrides the fleet policy.
- *Documented as an override?* **No.** The places that could say so are the `pytest_args` argparse help (`"extra arguments forwarded to the pytest gate"`), the `_run_selected_gates` docstring, the gates.yaml FIELDS header, and `wave_gate`'s forwarding comment. None of them mentions it.
- *Hole or intent?* The ruling's letter ("the manifest must express it WITHOUT hardcoding a count") is met, because the refusal sits at manifest load. The contract's own lifted CLASS is broader: "the worker count of EVERY manifested pytest-reader gate is decided by ONE policy at the moment the gate runs". A forwarded `-n` violates that class.
- *Threat model (honest developer):* this door is plausible, because CLAUDE.md's Quality-gates bullet literally teaches "Run pytest with `-n auto`". An agent that forwards `-n auto` out of habit while another session is live gets 64 workers, which is exactly the #503 side-answer failure.
- **Recommendation:** refuse a worker flag in forwarded args at the one chokepoint, `_run_selected_gates`, by REUSING `_hardcoded_worker_counts`. The error should teach that the fleet policy decides. The alternative is to document it as a deliberate operator override in the `pytest_args` help. Either choice changes served behaviour or text, so it needs a contract pin. I did not patch it.

**(b) D2 — is the `[alone]` / `[another-lore-session-live]` pair of `test_forwarded_pytest_args_keep_the_policy_count` sufficient? → For the VALUE, yes. One survivor exists → ROUTED-TO-CONTRACT (low severity).**
- *Value:* the stub report's unfixed build is the construction receipt. `[another-lore-session-live]` went RED (`'auto' == '12'`) while `[alone]` stayed green. Both render paths go through `GateRunner.run`, so any build that resolves in `run` is covered on both.
- *Survivor I constructed* (real tree, content backup, restored byte-exact with `cmp`, §6): I made `_run_selected_gates` pre-resolve `{workers}` itself via `pytest_worker_count(own_pids=set())`, which is a second resolution site that ignores the gate's own pids. **Result: `scripts/test_pytest_workers_503.py` 26 passed / 0 failed.** The forwarded test never checks `own_pids`, and the direct-path test that does check it never goes through `_run_selected_gates`.
- *Consequence of that wrong build:* the gate counts itself when its own argv contains "pytest". For example, `wave_gate` forwarding the selector `scripts/test_pytest_workers_503.py` would then cap at 12 while alone. That is the safe direction, so severity is low.
- *Missing pin:* in the forwarded test, assert the stubbed detector's calls carry `own_pids ∋ os.getpid()`. The stub's suggested `len(calls) == 1` does NOT kill this build, because the pre-substituted spec no longer `wants_worker_count`, so `run` never calls the detector a second time.
- *CLASS:* "every resolution of `{workers}` excludes the gate's own process". *SIBLINGS TRIED:* forwarded path. *SIBLINGS NOT TRIED:* `wave_gate` (it calls `_run_selected_gates`, same seam).

**(c) D1 — nothing pins the literal `"{workers}"`. Does anything observable depend on it? → NOT-A-DEFECT.**
- The one observable dependence is that the shipped manifest's argv must equal the constant. `test_every_shipped_pytest_gate_takes_its_count_from_the_placeholder` pins that, and it reads the constant.
- The literal spelling was the contract's choice, following the `{junit_xml}` idiom (§Stub item 3). The operator did not rule it, so a value pin would pin a convention, not a ruling.
- Prose sites that spell the literal (awk sweep, §6): `gates.yaml` FIELDS header and command, and the `GateSpec.wants_worker_count` / `resolved_command` docstrings. They would drift only if someone renamed BOTH the constant and the manifest, which is the same exposure `{junit_xml}` has had since it shipped.

### Other findings

| # | Finding | Class |
|---|---|---|
| F4 | `loopback.DEFAULT_STARTUP_TIMEOUT_S` docstring still says "The value is measure-then-tune (#466 contract report §E)". Since 2026-09-26 it is an operator-RULED exact value (#503 ruling 1; the contract's removed-behaviour table says so) and it is pinned by `test_the_default_startup_budget_stays_at_the_ruled_value`. This is served teaching prose that contradicts the pinned state. | **fixed** (docstring only) |
| F5 | `_loud_teardown` Args: `endpoint: … named in any overrun report` — after R4 it is also named in the teardown-raise note. | **fixed** (docstring only) |
| F6 | `test_migration_wire.py` comment: "6 x the measured heavy max 10.04 s … = 60 s". 6 × 10.04 = 60.24; 60 / 10.04 = 5.98. The same "6x the measured max" claim is in the contract docstring of `test_migration_wire_budget_503.py`. | impl comment **fixed** · contract docstring **routed-to-contract** (nit) |
| F7 | `_pytest_sessions.other_pytest_sessions` docstring claims "execnet's bootstrap argv never names pytest". | **not-a-defect** — verified live: the worker argv is `['…/.venv/bin/python', '-u', '-c', 'import sys;exec(eval(sys.stdin.readline()))']` (§6) |
| F8 | `_hardcoded_worker_counts` misses a clustered short-option form. I measured that `pytest -qn3` starts **3** workers, while `_hardcoded_worker_counts(["-qn3"])` returns `[]` because the part starts with `-q`, so the loader would accept a manifest spelling `-qn3`. An honest author could plausibly write `-qn auto`. | **routed-to-contract**: either extend the detector (behaviour change plus a refusal row) or pin it as a KNOWN BOUND |
| F9 | Stale contract prose after the build. In `test_pytest_workers_503.py`, the module docstring says the detector is "today in `concurrent_wire_acceptance.py`", and the `LORE_GATE_SESSION_ARGV` comment says "as the manifest spells it today" while the argv carries `-n auto`. The manifest now spells `{workers}`. The fixture is still a realistic live-session shape (the `alone` branch renders `-n auto`); only the words are stale. The RED-dating line partly covers it. | **routed-to-contract** (prose nit) |
| F10 | The contract report's realism line says "The xdist flag … read from production modules", but the test defines its own `XDIST_WORKERS_FLAG = "-n"`. | **not-a-defect** in the tests: `-n` is xdist's external CLI spelling, and an independent copy is the stronger oracle. The report's line is inaccurate (a report nit; no edit) |
| F11 | A forwarded selector or shell whose argv text contains "pytest" counts as "another session". Own pid and parent are excluded, but a grandparent shell is not. | **not-a-defect for this cycle**: this is #506 (ruled F2 = reuse unchanged), and it errs toward the cap, which is the safe direction |
| F12 | `GateRunner.run` docstring does not mention that it resolves `{workers}`. The only statement is an inline comment. | **fixed** (docstring sentence) |
| F13 | Citations `REPORT-measure-503.md` (388c604) and `REPORT-refactor-466-d1.md` are tracked at the repo root today, so they will MOVE when the lead archives them. The commit SHA keeps the measure citation resolvable. | **not-a-defect**; flagged for the lead's archive step (re-point to the `docs/plans/v2/receipts/…` path then) |
| F14 | `pytest.raises(ManifestError)` in the refusal rows has no `match=`. | **not-a-defect**: the placeholder control uses the identical template, so a build that refused for another reason would redden the control |

### Quality / DRY / reuse / efficiency (index-checked; see §5 DRY ledger)
- The detector has one definition, which I confirmed three ways: the contract's AST pin, an awk sweep over `scripts/*.py` and `skills/lore-deploy/scripts/*.py` for `/proc` readers (the only other hit is `test_concurrent_wire_acceptance.py`'s tree-member check, a different predicate), and `lore_search` for a `/proc` pytest scanner. That search found only report-embedded scripts (`REPORT-refactor-466.md`, `REPORT-contract-58-r2.md`), none in-tree.
- Each gate run does one `/proc` scan, and only for placeholder-carrying gates. That is negligible.
- `resolved_command`'s substitution map plus `_substitute` is one routine for both placeholders. No duplication.
- The R4 change is minimal and correct by construction: `except Exception` inside the failing branch, a bare `raise`, and a clean path left untouched.
- **F4 tail (routed-to-contract, prose nit):** the pre-existing test comments `test_loopback_serving.py` in `TestServerStartupTimeout`-area (awk hits at the lines that say "the value is measure-then-tune — §E" and "the VALUE is measure-then-tune (#466 contract report, §E)") still describe the STARTUP default as measure-then-tune. The contract owns those files, so I did not edit them. The third hit, which calls the SHUTDOWN budget measure-then-tune, is still true.

## Capability check (brief-base §4)
- **lore tools:** loaded. `lore_index` returned `last_sync` 292 s at review start, with the watched root at `feat/surreal-unification`@`f66a190`. `lore_search` ran for the detector, the worker policy and the note pattern (§5).
- **Graph gap:** `lore_impact` / `lore_get_symbol` cannot resolve any `scripts/` module (`pending_contract_gate`, `scripts.pending_contract_gate` and `GateRunner.run` all miss). I filed this as **#507** (capability_gap, area lore_impact). The fallback was **awk** over `scripts/*.py`, `skills/lore-deploy/{scripts,tests}/*.py` and `loremaster/tests/*.py` (grep/rg are hook-blocked, #473). This is the textual seam in dogfood case (b).
- **Hook note:** the PreToolUse hook also blocked a `find … | xargs awk` form ("lore main checkout is live-indexed"). Plain `awk` over globs was allowed.
- **Everything else the brief demanded was satisfiable.** No full suite was run, :18500 was never touched, and the TEI embedder was never called (the wire suites use the fake embedder). No process was killed.

## 2. Test-smell rejection list (contract tests)

| Smell | Result |
|---|---|
| Tautology | **None.** The expected values are written independently as operator-ruled constants (`OPERATOR_RULED_*`, `RULED_WORKERS_*`) and never read back from the module under test. The re-export pin is an identity check against a separately imported module. |
| Unrepresentative fixture | **None load-bearing.** The `/proc` argvs, pids and cwds are shapes observed live. I re-verified the worker shape myself (§6 probe). The comment on `LORE_GATE_SESSION_ARGV` is stale (F9), but the argv is still a real `alone`-branch render. The R4 overrun note fragment `"shutdown"` is weak on its own, but the same assertion also requires `host:port`. |
| No magnitude guard on a derived output | **None missing.** The budgets carry ≥3× measured-max headroom guards. The slow-start pin checks `start_took_s >= SLOW > DEFAULT`, and the R4 exit windows are bounded on both sides. The worker count is a two-valued enum, not a magnitude. |
| Forward-run-as-validation | **Not applicable, and I say so explicitly.** This work is pure logic with a fixed spec: an operator-ruled constant, an exception-routing rule, and a yes/no → enum policy. Nothing's output is DERIVED from data, so green tests are sufficient (standing "data-driven behaviour" clause). The 60 s value comes from a measurement (388c604), but the implementation only carries a ruled constant. Validating the measurement belongs to the measure-503 wave, not this refactor. |
| Drift-prone hardcoded convention | **None defective.** The literals the tests hardcode (`60.0`, `15.0`, `"12"`, `"auto"`, the name `MIGRATION_WIRE_STARTUP_TIMEOUT_S`, `"-n auto"` as the retired literal) are each the ruled thing being pinned, which is the permitted case. `XDIST_WORKERS_FLAG = "-n"` is xdist's external spelling, and an independent copy is the stronger oracle (F10). The placeholder is read from production (D1, not-a-defect). |
| Probe without a control | Refusal rows have no `match=`. A same-template control exists (F14), so this is not a defect. |

## 3. Refactors applied (all prose; zero behaviour change; each re-gated)
1. `loopback.DEFAULT_STARTUP_TIMEOUT_S` docstring (F4): "measure-then-tune (#466 §E)" became "operator-ruled (2026-09-26, lore #503), sized for the LIGHT callers (measured in commit 388c604); a heavier caller passes its own `startup_timeout_s` (e.g. `test_migration_wire.MIGRATION_WIRE_STARTUP_TIMEOUT_S`) rather than moving this default". I deliberately did NOT restate the inherited 0.50 s figure, because a number restated beside a claim is the drift class.
2. `loopback._loud_teardown` Args (F5): `endpoint` is now "named in any teardown-failure report or note".
3. `test_migration_wire.py` constant comment (F6): the text now reads "60 s is ~6 x (5.98 x) the measured heavy max 10.04 s … and exactly 4 x the 15 s censoring bound", replacing the false equality "6 x 10.04 = 60".
4. `pending_contract_gate.GateRunner.run` docstring (F12): it now states that `{workers}` is resolved there, once per run, by `_pytest_sessions.pytest_worker_count`, never at manifest load.
- **Structural refactors: none warranted.** There is one detector definition, one substitution routine for both placeholders, and a minimal R4 branch. No duplication was found (§5).
- **De-bloat: none applied.**
  - `test_the_policy_constants_carry_the_ruled_values` is arguably subsumed by the `…over_the_real_detector` rows, since both compare against the ruled values. It gives the only failure message that names the constant, so the cost of keeping it is about 4 lines, and I did not run the demonstrate-then-delete step.
  - `_fake_proc` (new) vs `TestTheOtherSessionPreflight._fake_proc` (existing): consolidating would change the existing tests' fixture content (cwd symlinks and non-pid entries), which is a fixture retarget, so I kept both. The contract report already offers it as an EXTEND candidate for the lead.

## 4. Final gate tails (2026-09-26, HEAD `f66a190` + tree, after the last edit)
```
$ uv run pytest -q -p no:cacheprovider --tb=short -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py scripts/test_pytest_workers_503.py scripts/test_concurrent_wire_acceptance.py scripts/test_gate_currency.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py
226 passed, 22 warnings in 29.47s
$ cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests
120 passed in 17.49s
$ uv run ruff check <5 impl .py + 3 contract .py>
All checks passed!
$ uv run ruff format --check loopback.py _pytest_sessions.py concurrent_wire_acceptance.py test_loopback_serving.py test_migration_wire_budget_503.py test_pytest_workers_503.py
6 files already formatted
$ ruff format --diff hunk count, builder-tree backup → after my edits
scripts/pending_contract_gate.py        28 → 28   (also red at HEAD f66a190 — pre-existing)
loremaster/tests/test_migration_wire.py 10 → 10   (also red at HEAD f66a190 — pre-existing)
$ ./scripts/typecheck.sh    → exit 1, 60 error lines; 0 in loopback.py / pending_contract_gate.py / test_migration_wire*.py / _pytest_sessions.py / concurrent_wire_acceptance.py / test_pytest_workers_503.py / test_loopback_serving.py
  (tail: "scripts/test_forgery_door_sweep.py:42: error: Module "loremaster.tasks" has no attribute "SupersedeResult" … typecheck: scripts FAILED"; skills, docs/eval and shellcheck legs OK)
$ uv run python scripts/pending_contract_gate.py --verify-registry   → exit 0 (script-mode import of _pytest_sessions resolves)
```
The 60 typecheck errors match the builder's own count. They sit in other packets' files (the 58 / 63c / 64b families, `test_forgery_door_sweep.py`, and others), which I did not judge per the brief.

## 5. DRY ledger (index checks against the builder's new symbols; I introduced none)
| symbol | lore query run | returned | verdict |
|---|---|---|---|
| `_pytest_sessions.other_pytest_sessions` / `PROC_ROOT` | `lore_search("scan /proc for pytest sessions cmdline")`, `("function that lists running pytest processes excluding own pid")`, plus awk for `/proc` over `scripts/`, `skills/` | only report-embedded scripts (`REPORT-contract-58-r2.md` bash, `REPORT-refactor-466.md` python), no in-tree definition. The only other in-tree `/proc` read is `test_concurrent_wire_acceptance.py`'s tree-member check, which is a different predicate | one implementation, confirmed |
| `pytest_worker_count` + constants | `lore_search("choose xdist -n worker count … cap workers when another session is live")` | report prose only | no prior policy; HAND-ROLLED is justified |
| R4 note (`add_note`) | `lore_search("add PEP 678 note … teardown")` + awk `add_note(` over the production trees | only `loopback.py`'s two calls, in the one policy function | one policy site |
| `WORKERS_PLACEHOLDER` / `_substitute` / `_hardcoded_worker_counts` | awk importers of `pending_contract_gate` / `_pytest_sessions` (graph gap #507) | all importers are in `scripts/`, and each inserts `scripts/` on `sys.path` (or runs as a script), so the new `import _pytest_sessions` comment's claim holds | EXTENDED the `{junit_xml}` seam; no clone |

## 6. Instruments (pasted verbatim, per brief-base §1)
**xdist probe** (answers (a) and verifies F7 and F8): scratch `…/scratchpad/probe/test_probe_workers.py`
```python
import os
from pathlib import Path

def test_argv_of_self():
    me = [p.decode() for p in Path(f"/proc/{os.getpid()}/cmdline").read_bytes().split(b"\0") if p]
    out = Path(os.environ["PROBE_OUT"])
    out.write_text(f"{me!r}\n{os.environ.get('PYTEST_XDIST_WORKER_COUNT')}\n")
```
```
$ PROBE_OUT=out.txt  uv run pytest -q -p no:cacheprovider --rootdir=$S -c /dev/null -n 2 -n 3 test_probe_workers.py  → worker count 3
$ PROBE_OUT=out2.txt uv run pytest … -n 2 test_probe_workers.py                                                  → 2   (control)
$ PROBE_OUT=out3.txt uv run pytest … -qn3 test_probe_workers.py                                                   → 3   (F8: clustered form honoured by xdist)
worker argv (all three): ['/home/ejprice/PycharmProjects/lore/.venv/bin/python', '-u', '-c', 'import sys;exec(eval(sys.stdin.readline()))']
```
**D2 wrong build**: real tree, `cp -a` content backup, restored and `cmp`-verified byte-exact. The mutation LANDED: the `git diff --stat` line count for the file went from 82 to 84 changed lines.
```python
old = '''            spec = spec.model_copy(
                update={"command": (*spec.command, *pytest_args)}
            )'''
new = old + '''
            _wb = _pytest_sessions.pytest_worker_count(own_pids=set())
            spec = spec.model_copy(update={"command": tuple(p.replace(WORKERS_PLACEHOLDER, _wb) for p in spec.command)})'''
# applied to scripts/pending_contract_gate.py::_run_selected_gates
```
```
$ uv run pytest -q -p no:cacheprovider --tb=line scripts/test_pytest_workers_503.py
26 passed in 0.40s        ← survivor: the forwarded path's own-pid exclusion is unpinned
RESTORED-BYTE-EXACT
```
Declared expectation before the run: "if a pin covers the forwarded path's own_pids, a `…forwarded…` row goes RED". None did.

## 7. Symbols / behaviours DELETED by the final diff (vs HEAD `f66a190`, files in this cycle)
| deleted | where | disposition |
|---|---|---|
| `concurrent_wire_acceptance.other_pytest_sessions` (local def) | driver | MOVED to `_pytest_sessions`. The driver name still resolves, as a re-export of the same object (pinned) |
| `concurrent_wire_acceptance.PROC_ROOT` | driver | MOVED to `_pytest_sessions.PROC_ROOT`. It is **NOT re-exported** by the driver. An awk sweep of `scripts/`, `skills/` and `loremaster/tests/` finds no consumer of the old name |
| the literal `"pytest"` in the detector body | driver → shared | now the constant `_pytest_sessions.PYTEST_ARGV_MARKER` (same value) |
| gates.yaml pytest argv `"-n", "auto"` | `scripts/gates.yaml` | replaced by `"-n", "{workers}"` (ruling 3) |
| gates.yaml description sentence "run with -n auto per CLAUDE.md's measured 9.6x" | `scripts/gates.yaml` | replaced with policy-by-pointer prose (retired-literal pin) |
| `GateSpec.resolved_command` inline comprehension (junit-only substitution) | `pending_contract_gate` | replaced by the substitution map + `GateSpec._substitute`. Signature widened (`workers=None`), so existing one-arg callers are unchanged |
| **behaviour:** `_loud_teardown` failing-body branch where a raising `stop` REPLACED the body's exception | `loopback.py` | dropped (R4, operator "fix now"). The raise now rides as a note, and interrupts still propagate (F1 = Reading A) |
| **behaviour:** `_serve_migration_wire` inheriting the 15 s default | `test_migration_wire.py` | dropped (ruling 1); it now passes `MIGRATION_WIRE_STARTUP_TIMEOUT_S` |
| docstring claim "the value is measure-then-tune (#466 §E)" on `DEFAULT_STARTUP_TIMEOUT_S` | `loopback.py` | removed by me (F4); the value is now ruled |
| the multi-line `overrun = (...)` expression | `loopback.py` | reshaped into `address` + `overrun` (same text) |
| (never in HEAD, so not a HEAD deletion) the stub-era `_pytest_sessions._STUB_WORKERS_PLACEHOLDER` and the stub's `DEFAULT_STARTUP_TIMEOUT_S` import in `test_migration_wire.py` | — | removed by the builder before this pass |

## Unrelated failures
`./scripts/typecheck.sh` reports 60 mypy errors, all outside this cycle's files (§4). No test failed in the scoped runs.
