brief-base v17 read

# REPORT-refactor-503-d1 — tdd-light Phase 5 (REFACTOR + AUDIT) on the DELTA of lore #503 (the currency gate's worker count)

## SUMMARY BLOCK
- **State:** done-with-deviations. Measured 2026-09-26 on HEAD `f66a190` plus the working tree. Nothing committed.
- **Deviations:** (1) I found P9 while fixing P1, after §1 was written, and I say so in §4. (2) I did not register on `lore_comms` (no ledger row was named). (3) A role-boundary reading is written down in §Capability for the lead to rule.
- **Packages considered:** none — no mechanism specified. My edits are prose only. The builder's `keep_with_trigger` verdict on `_hardcoded_worker_counts` stands as ruled; I corrected one overstated claim in it (P3, read in the installed pytest 9.0.3 source).
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 0 new symbols. The builder's 5 were index-checked (§6).
- **Graded:** `f66a190` + working tree · HEAD-at-report: `f66a190` · SAME.
- **Decisions needed:**
  - **D-2 (MEDIUM, routed):** the D1-F3 ruling has NO pin. A `ManifestError` build passes 76/76 and serves `MANIFEST ERROR:` / `CONFIG ERROR:` (§2b).
  - **D-1 (LOW, routed):** `--derive` spawns typecheck with a forwarded `-n 3` unrefused, and `--verify-registry` drops it silently (§1a).
  - **T2 (LOW):** the completeness pin's reach is keyed on names.
  - **P6 (LOW):** the F8 trigger #2 is unmeasured.
  - `--maxprocesses` is an unrefused sibling that can only lower the count.
  - Role-boundary reading (§Capability).
- **Headline:** the delta is correct against D1-F1, D1-F2 and D1-F3 and ruling 4 on all four render paths. The own-pid survivor is KILLED on the delta: A = 19/19 declared, and the isolating A′ = 3/3, killed by the own-pid pin alone. The §1a forwarded second `-n` is now refused (exit 2, nothing spawned). The served prose over-claimed ("the policy is the only thing that sets it" is false: `--maxprocesses` measured) and is fixed, along with 4 other prose nits. One contract rider is missing (D-2).
- **Gates:** 8-file **276 passed / 0 failed** · skills **120 passed** · ruff clean · typecheck 54 errors, **0 in touched files** · `--verify-registry` exit 0.
- **Receipts:** §1 findings (written before any edit) · §2 grader runs + instruments verbatim · §3 smells · §4 refactors · §5 gate tails · §7 deletions.

## 1. Cold review findings (written BEFORE any edit)

Graded tree: HEAD `f66a190` plus the working tree. The delta is taken against the first-pass green copies in
`…/297217bd-…/scratchpad/backup-503-green/scripts/`. `wave_gate.py` is absent from that backup, so its delta is
`git diff HEAD -- scripts/wave_gate.py`: every hunk is refusal-related, so none of it came from the first pass.
`_pytest_sessions.py` shows no diff against the backup, so the delta leaves it UNCHANGED.

Classes: **fixed** (prose or quality only, no behaviour change) · **routed-to-contract** (needs a pin or a
behaviour change) · **not-a-defect** (with the reason).

### 1a. Correctness against the lead rulings, on all four render paths
The four paths are `GateRunner.run` direct, `_run_selected_gates`, `pending_contract_gate.main --legs … -- <args>` and `wave_gate.main --wave …`.

| # | Ruling | Verdict | Evidence |
|---|---|---|---|
| C1 | D1-F1 = Reading B: the policy `-n` is appended LAST, after everything, manifest tokens included | **not-a-defect.** Implemented at the STATE chokepoint `GateSpec.resolved_command`. That chokepoint has exactly one caller, `GateRunner.run` (awk over `scripts/*.py`). Every path goes through it, so no path can skip the move | `_with_policy_workers_last` drops every `{workers}`-valued flag span and appends `-n {workers}`. Forwarded args are appended to `spec.command` BEFORE `run` (`_run_selected_gates`), so the order is manifest-minus-pair, then forwarded, then the policy pair |
| C2 | D1-F2 = refuse before ANY gate spawns | **Correct on the three forwarding paths.** `_refuse_forwarded_worker_counts` is the first statement of `_run_selected_gates`, before the leg loop. **The ruling's class does not hold on two other modes → D-1, routed** | See D-1 |
| C3 | D1-F3 = a typed error of its own, never "MANIFEST ERROR" | **Correct in code.** `ForwardedWorkerCountError(ValueError)` is caught first in `pcg.main` and in `wave_gate.main`, and both print `REFUSED ARGUMENT:` and exit 2. `_dispatch` has no `except ValueError` that could swallow it. **No pin enforces the ruling → D-2, routed** | See D-2 |
| C4 | Ruling 4: own-pid exclusion on every path | **Correct.** The only resolution site is `GateRunner.run`, and it passes `own_pids={getpid(), getppid()}`. The delta did not touch it | §2 survivor run |
| C5 | F8 KNOWN BOUND, and the helper stays hand-rolled as keep_with_trigger | **Correct.** The recognition logic is byte-identical to the first pass: I compared the old and new `_hardcoded_worker_counts` bodies hunk by hunk. The `-qn3` miss is unchanged, and the docstring carries the verdict and the triggers | diff §7 |

**D-1 (routed-to-contract, LOW). `--derive` and `--verify-registry` accept `pytest_args` and never refuse them.**
- *Measured 2026-09-26* with the in-process probe in §6, which uses a recording `Popen`, so nothing is actually spawned:
  - `main(["--derive","--","-n","3"])` spawns `['./scripts/typecheck.sh']` with no refusal.
  - `main(["--verify-registry","--","-n","3"])` returns exit 0 with nothing spawned, and the argument is silently dropped.
  - Control: `main(["--","-n","3"])` returns exit 2 with nothing spawned.
- *Class (lifted):* "every CLI mode that ACCEPTS `pytest_args` either applies them or refuses them before any gate spawns". The domain's source of truth is the argparse `pytest_args` positional in `_build_parser`, together with every `_dispatch` branch.
  - *Siblings tried:* default mode (refuses), `--derive` (spawns, drops the args), `--verify-registry` (drops the args).
  - *Sibling not tried:* `--currency`. It goes through `_run_selected_gates`, so it refuses by construction.
- *Harm:* none to the worker count, because the args are never applied in those modes. The harm is served behaviour: a forwarded argument vanishes without a word, which is the silent-drop shape. This is pre-existing (the builder's §Noticed 1 raised it). The delta made the inconsistency visible, because the ruling now says "refuse".
- *Recommendation (lead or operator):* treat any non-empty `pytest_args` in `--derive` / `--verify-registry` as a usage error, raised at `_dispatch` entry through the same typed error. It is a behaviour change, so it needs a pin. I did not patch it.

**D-2 (routed-to-contract, MEDIUM). The D1-F3 ruling has no pin: the rider was dropped.**
- The contract pinned D1-F3 as spec-silent. Its words were "the pins accept either", and it wrote them before the lead ruled.
- After the ruling ("a typed error of its own, never MANIFEST ERROR for a CLI arg"), no test checks the exception type or the label printed on stderr.
- Survivor constructed and run in §2b: `_refuse_forwarded_worker_counts` raises `ManifestError` instead. Expected result: every contract test stays green, `pcg` prints `MANIFEST ERROR:`, and `wave_gate` prints `CONFIG ERROR:`.
- *Missing pin:*
  - the leg-runner rows assert `isinstance(excinfo.value, pcg.ForwardedWorkerCountError)` and `not isinstance(…, ManifestError)`;
  - the CLI rows assert that stderr does not contain `MANIFEST ERROR` or `CONFIG ERROR`, OR that it starts with the refusal label, read from a production constant if the lead wants the label pinned.
- *Class:* "a refused CLI argument is never labelled as a manifest or config fault, on every CLI that surfaces it". *Siblings:* `pcg.main` and `wave_gate.main`, the two catch sites (the same two the completeness pin enumerates).

### 1b. DRY: ONE refusal helper, ONE policy, no second parser
| # | Finding | Class |
|---|---|---|
| R1 | `_worker_flags` is the ONE recogniser. `_hardcoded_worker_counts` (used by the loader and the refusal) and `_with_policy_workers_last` (the render) both read it. `_refuse_forwarded_worker_counts` is the ONE refusal helper: its only caller is `_run_selected_gates`, and both CLIs reach it through that caller. The policy has one resolution site. The builder's mutation of `_worker_flags` reddened the loader, the refusal and the render together, and the contract's mutation-by-stub pin covers refusal → helper | not-a-defect |
| R2 | The label `REFUSED ARGUMENT:` is a literal in both `pcg.main` and `wave_gate.main` | **not-a-defect.** Each CLI already spells its own labels inline (`MANIFEST ERROR`, `CONFIG ERROR`, `BROKEN INSTRUMENT`). This is presentation, not policy, and a lone constant would break the local idiom. If D-2's pin reads the label from production, promote it to a constant then |

### 1c. The typed error's name and message, as served English
- **Name:** `ForwardedWorkerCountError`. It names what was refused (a forwarded worker count), and it subclasses `ValueError`, which is a bad argument value. **not-a-defect.**
- **Message** (from the builder's live receipt, re-read in the code): *"the forwarded pytest args [...] carry an xdist worker count ['auto'] — the gate's worker count is decided by the fleet policy (_pytest_sessions.pytest_worker_count), rendered as the LAST worker flag. Drop the -n / --numprocesses argument (lore #503)."*
  - The policy name is DERIVED from the function object (`__module__`/`__name__`), not a literal. It names the remedy.
  - For `wave_gate`, the "forwarded pytest args" are the `--wave` selectors. The `--wave` help says selectors are forwarded to pytest, so the vocabulary is taught. **not-a-defect.**

### 1d. Prose-vs-behaviour on every surface the delta touches
| # | Surface | Finding | Class |
|---|---|---|---|
| P1 | `gates.yaml` `pytest` description: "so the policy is the only thing that sets it". Also the FIELDS header, "so no other spelling can override it", and the `pytest_args` help, "Its xdist worker count is NOT forwardable" | **FALSE as served.** *Measured 2026-09-26* with the xdist probe in §6: a forwarded `--maxprocesses=2` sets the count to **2** against `-n 4` (in either order) and against `-n auto`. It is not refused, because ruling 2 limits the refusal to the helper's spellings. It only ever LOWERS the count (`-n 2 --maxprocesses=8` → 2; `--maxprocesses=64 -n 3` → 3), so it errs in the safe direction. The sentences still claim more than the mechanism enforces, which is a false clear on a surface agents read. *Class:* "every served sentence about who sets the gate's worker count is bounded to the worker-FLAG spellings the render and refusal govern". *Siblings checked:* `resolved_command` docstring ("every other spelling lose", scoped to `-n` spellings, true) · `_with_policy_workers_last` docstring ("no other spelling … can override the policy", read as the worker flag; I tightened it) · `wave_gate` `--wave` help (names `-n / --numprocesses`, true) · the refusal message (true) | prose **fixed** (§3). The unrefused `--maxprocesses` is **routed** as a sibling, still open: the contract's §Noticed 3 listed it untried. It is now measured, and it errs in the safe direction |
| P2 | `_hardcoded_worker_counts` docstring: "Two callers: the manifest loader … and `_run_selected_gates`" | Inaccurate. The caller is `_refuse_forwarded_worker_counts`, which `_run_selected_gates` calls | **fixed** |
| P3 | Same docstring: "`pytest.Parser` … its constructor demands `_ispytest=True`" | **Overstated.** I read the installed pytest 9.0.3 source: `Parser.__init__(…, *, _ispytest: bool = False)` calls `check_ispytest`, which only `warn(PRIVATE)`s when the flag is False. The constructor does not refuse. The conclusion (the API is private) still stands | **fixed** |
| P4 | `wave_gate.main` docstring: "2 = a BROKEN INSTRUMENT / bad config" | Omits the new exit-2 cause, a refused argument | **fixed** |
| P5 | `pcg.main` docstring, first line: "2 = a BROKEN INSTRUMENT". Its body now says the case includes "a refused forwarded worker count" | The line was already imprecise before the delta (MANIFEST and REGISTRY errors are not broken instruments either). The delta put a refused argument under a heading that calls it a broken instrument | **fixed** (the first line now names the four causes) |
| P6 | F8 re-open trigger #2, in the helper's docstring and the test comment: "a real gate invocation carries a worker spelling this helper does not refuse" | Nothing observes real gate invocations, so this trigger is never measured. Per CLAUDE.md, "a trigger nobody measures is a hope". Trigger #1 (pytest exposes its parser) is also unmeasured, but it is an upstream event. The pin-the-miss test is the real guard: it reddens the day the bound closes | **routed** (LOW; ruled bound, so no edit) |
| P7 | The `XDIST_WORKERS_*` constant comment names only the loader as a consumer | Still true, because it does not claim to be exhaustive | not-a-defect |
| P8 | `resolved_command`, `GateRunner.run`, `_run_selected_gates` docstrings, the `wave_gate` forwarding comment, and the gates.yaml FIELDS "LAST" sentence | Each matches the code as read (C1/C2) | not-a-defect |

### 1e. Contract-side findings seen during review (the §2/§3 instruments settle them)
- **T1 = D-2** (the D1-F3 rider is unpinned). Survivor in §2b.
- **T2 (routed, LOW). The completeness pin's REACH is keyed on NAMES.**
  - `test_the_render_path_domain_is_complete` derives callers of `{_run_selected_gates, GateRunner}`, which means the constructor NAME.
  - The real render chokepoint is `GateSpec.resolved_command`, reached through `GateRunner.run`, and neither `resolved_command` nor `.run` is in the entry-name set. A new function that takes an existing runner and calls `runner.run(pytest_spec)` (the shape `_dispatch --derive` already uses), or a new caller of `spec.resolved_command`, escapes the domain.
  - *Severity LOW:* the ruling-1 property is enforced AT the chokepoint, so any new path through `run` inherits it. A new path that bypasses `resolved_command` would leave `{workers}` literal, and pytest rejects that loudly.
  - *Class:* "the render-path domain is derived from the callers of the chokepoint (`resolved_command` / `GateRunner.run`), not from a constructor name". This is instrument-lesson row 1 in miniature.

## 2. Grader duty: the wrong builds, run against the delta build
All runs are in a `./scripts/scratch_copy.sh` copy, which asserted its own provenance (exit 0). Receipt:
**`loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/de5007bd-cad5-4d23-9d9c-466a0fd8c6d1/scratchpad/sc503d1/loremaster/loremaster/__init__.py`**,
and `pending_contract_gate.__file__` is inside the copy. Before any mutation I `cmp`'d the copy's `pending_contract_gate.py`, `wave_gate.py`, `gates.yaml`, `_pytest_sessions.py` and `test_pytest_workers_503.py` against the real tree: all byte-identical. Unmutated baseline in the copy: `76 passed in 1.65s`.

**Instrument:** `scripts/mutation_proof.py`, the repo's own tool. It matches the anchor exactly once, diffs the RED set against the declared set in both directions, and restores from a content backup. It is driven by the script below.
- Declared sets were taken from `pytest --collect-only` (76 ids) and written to files, hashed at `2026-09-26T19:29:11-04:00`, before the first run.
  - `declared_A.txt` sha256 `3c8d8da7…`: 19 ids.
  - `declared_Aprime.txt` sha256 `b1c49889…`: 3 ids.
  - `declared_B.txt`: the EMPTY set, sha256 `e3b0c442…`. B is predicted to survive.
- The awk predicates that produced the sets:
  - A = every `test_the_policy_count_is_the_last_worker_flag[...]` row except `[direct-*]` (16), plus every `TestTheGateNeverCountsItself` row except `[direct]` (3).
  - A′ = the 3 non-direct own-pid rows.

### 2a. The own-pid survivor (refactor-503 §1b / §6), transplanted onto the delta build
- **A (verbatim transplant).** `_run_selected_gates` pre-resolves `{workers}` through `pytest_worker_count(own_pids=set())` and substitutes the value in place.
  - Result: **`19 failed, 57 passed`**. `mutation_proof`: **PROOF HELD, the declared 19 fired EXACTLY**, with no unexpected reds and no declared rows left green.
  - The contract's declared kill was the 3 own-pid rows. The other 16 are ruling-1 rows, because on the delta build an in-place pre-resolution also leaves the policy flag BEFORE the forwarded args.
  - The contract's prediction (the own-pid rows `selected-forwarded`, `gate-cli-forwarded` and `wave-forwarded` go red, and `direct` stays green) holds. It is a subset of the observed set, and I had declared the full set independently.
- **A′ (isolating variant, mine).** This is the same own-pid bug, but the pre-resolution goes through `_with_policy_workers_last`, so the policy flag is still LAST. Only the own-pid pin can catch it.
  - Result: **`3 failed, 73 passed`**. **PROOF HELD, the declared 3 fired EXACTLY.**
  - ⇒ ruling 4's pin `TestTheGateNeverCountsItself` discriminates **on its own**. The first audit's §1b survivor is killed, and it is not killed by ruling 1 by accident.
- File restored byte-exact after every run (md5 `34f59c0b…`), and `cmp` against the real tree was clean after each run.

### 2b. D-2 survivor: the D1-F3 ruling is unpinned
- **B.** `raise ForwardedWorkerCountError(` becomes `raise ManifestError(` in `_refuse_forwarded_worker_counts`.
  - The would-be kills were passed to `--expect-red`. They are the 14 refusal rows (6 leg-runner, 6 gate-CLI, 2 wave-CLI), where D-2's missing pin would sit.
  - Result: **`76 passed`**. `mutation_proof` exit 4, **all 14 "DECLARED RED but STAYED GREEN"**, and **zero unexpected reds**. The observed RED set is ∅, which equals my declared prediction `declared_B.txt`.
- Served text under B, captured in the same run:
  ```
  MANIFEST ERROR: the forwarded pytest args ['-n', 'auto'] car…     (pending_contract_gate)
  CONFIG ERROR: the forwarded pytest args ['-n12'] carry an xd…      (wave_gate)
  ```
  That is exactly the mislabel the lead ruled out, and the contract waves it through. **D-2 is confirmed.**

### 2c. refactor-503 §1a re-run: a forwarded second `-n` is now REFUSED
The in-process probe (below) uses a recording `Popen`, so nothing can spawn. Run on the REAL tree, 2026-09-26:
```
gate-cli -n 2 -n 3:                 exit=2 spawned=[]   stderr: REFUSED ARGUMENT: … carry an xdist worker count ['2', '3'] — … (_pytest_sessions.pytest_worker_count) …
gate-cli -n auto (CLAUDE.md habit): exit=2 spawned=[]
wave --wave=-n3:                    exit=2 spawned=[]
CONTROL gate-cli plain selector:    SPAWNED ['uv','run','pytest','-q','-o','junit_family=xunit1','--junit-xml=/var/tmp/…/junit.xml','loremaster/tests/test_migration_wire.py','-n','12']
```
The control shows the positive leg: the probe CAN see a spawn, and the policy flag renders LAST. The count was `12` because the real detector saw another pytest session live on the box at that moment, which is the policy working. **§1a is closed by the delta.**

### 2d. Instruments, pasted verbatim (brief-base §1)
`drive.sh` (in `…/scratchpad/mut/`):
```bash
#!/usr/bin/env bash
# Driver for REPORT-refactor-503-d1 §2. Runs in the scratch_copy tree; one mutation per call of scripts/mutation_proof.py.
# Usage: drive.sh <A|Aprime|B>
set -u
P=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/de5007bd-cad5-4d23-9d9c-466a0fd8c6d1/scratchpad
SC=$P/sc503d1
cd "$SC" || exit 99
uv run python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)'
TEST=(uv run pytest -q -p no:cacheprovider --tb=line -rfE scripts/test_pytest_workers_503.py)
case "$1" in
  A)      ANCHOR=$P/mut/anchor_selected.txt; REPL=$P/mut/repl_A.txt;      DECL=$P/declared_A.txt ;;
  Aprime) ANCHOR=$P/mut/anchor_selected.txt; REPL=$P/mut/repl_Aprime.txt; DECL=$P/declared_Aprime.txt ;;
  B)      ANCHOR=""; DECL=$P/mut/would_kill_B.txt ;;
esac
EXPECT=(); while read -r id; do EXPECT+=(--expect-red "$id"); done < "$DECL"
if [ "$1" = B ]; then
  uv run python scripts/mutation_proof.py --file scripts/pending_contract_gate.py \
    --anchor '        raise ForwardedWorkerCountError(' --replacement '        raise ManifestError(' \
    "${EXPECT[@]}" -- bash -c "${TEST[*]}; echo '--- served labels under B:'; uv run python scripts/pending_contract_gate.py -- -n auto 2>&1 | cut -c1-60; uv run python scripts/wave_gate.py --wave=-n12 2>&1 | cut -c1-60"
else
  uv run python scripts/mutation_proof.py --file scripts/pending_contract_gate.py \
    --anchor-file "$ANCHOR" --replacement-file "$REPL" "${EXPECT[@]}" -- "${TEST[@]}"
fi
rc=$?
cmp scripts/pending_contract_gate.py /home/ejprice/PycharmProjects/lore/scripts/pending_contract_gate.py && echo "scratch file == real tree file (byte-exact)"
echo "mutation_proof exit=$rc"
```
The anchor, which is the same for A and A′, is the `_run_selected_gates` forwarded-args copy:
```python
            spec = spec.model_copy(
                update={"command": (*spec.command, *pytest_args)}
            )
```
Replacement A is the anchor, plus:
```python
            _wb = _pytest_sessions.pytest_worker_count(own_pids=set())
            spec = spec.model_copy(update={"command": tuple(p.replace(WORKERS_PLACEHOLDER, _wb) for p in spec.command)})
```
Replacement A′ is the anchor, plus:
```python
            _wb = _pytest_sessions.pytest_worker_count(own_pids=set())
            spec = spec.model_copy(update={"command": tuple(p.replace(WORKERS_PLACEHOLDER, _wb) for p in _with_policy_workers_last(spec.command))})
```
`derive_probe.py` (the D-1 measurement) and `second_n_probe.py` (§2c) are both in `…/scratchpad/probe/`:
```python
"""Probe: does `pending_contract_gate --derive -- -n 3` refuse, or spawn a gate and drop the args?"""
import subprocess
import sys

sys.path.insert(0, ".")
import pending_contract_gate as pcg  # noqa: E402

class Captured(Exception):
    pass

spawned: list[list[str]] = []

def recording_popen(args, *a, **k):
    spawned.append([str(p) for p in args])
    raise Captured

subprocess.Popen = recording_popen  # type: ignore[misc]
for argv in (["--derive", "--", "-n", "3"], ["--verify-registry", "--", "-n", "3"], ["--", "-n", "3"]):
    spawned.clear()
    try:
        code = pcg.main(argv)
        outcome = f"exit={code}"
    except Captured:
        outcome = "SPAWNED"
    print(f"{argv}: {outcome} spawned={spawned}")
```
Output (run from `scripts/`, 2026-09-26):
```
['--derive', '--', '-n', '3']: SPAWNED spawned=[['./scripts/typecheck.sh']]
['--verify-registry', '--', '-n', '3']: exit=0 spawned=[]
['--', '-n', '3']: exit=2 spawned=[]
```
```python
"""REPORT-refactor-503-d1 §2c: refactor-503 §1a's forwarded second `-n`, re-run against the delta build.

A recording Popen captures any argv and raises, so no suite can start. Control: forwarded args with no
worker flag must reach a spawn, with the policy's -n LAST.
"""
import subprocess
import sys

sys.path.insert(0, "scripts")
import pending_contract_gate as pcg  # noqa: E402
import wave_gate  # noqa: E402

class Captured(Exception):
    pass

spawned: list[list[str]] = []

def recording_popen(args, *a, **k):
    spawned.append([str(p) for p in args])
    raise Captured

subprocess.Popen = recording_popen  # type: ignore[misc]
pytest_gate = next(g.id for g in pcg.GateManifest.load(pcg.DEFAULT_MANIFEST_PATH).gates
                   if pcg.READERS[g.reader] is pcg.JUnitReportReader)
sel = "loremaster/tests/test_migration_wire.py"
cases = [
    ("gate-cli -n 2 -n 3", lambda: pcg.main(["--legs", pytest_gate, "--", "-n", "2", "-n", "3", sel])),
    ("gate-cli -n auto (CLAUDE.md habit)", lambda: pcg.main(["--legs", pytest_gate, "--", "-n", "auto", sel])),
    ("wave --wave=-n3", lambda: wave_gate.main(["--wave=-n3"])),
    ("CONTROL gate-cli plain selector", lambda: pcg.main(["--legs", pytest_gate, "--", sel])),
]
for label, call in cases:
    spawned.clear()
    try:
        outcome = f"exit={call()}"
    except Captured:
        outcome = "SPAWNED"
    print(f"{label}: {outcome} spawned={spawned}")
```
xdist `--maxprocesses` probe (P1): this is refactor-503 §6's probe file, reduced to write only `PYTEST_XDIST_WORKER_COUNT`. Each row ran `PROBE_OUT=o.txt uv run pytest -q -p no:cacheprovider --rootdir=$S -c /dev/null <args> test_probe_workers.py`:
```
[-n 4]                     exit=0 workers=4    (control)
[--maxprocesses=2 -n 4]    exit=0 workers=2
[-n 4 --maxprocesses=2]    exit=0 workers=2
[--maxprocesses 2 -n auto] exit=0 workers=2
[-n 2 --maxprocesses=8]    exit=0 workers=2    (a max, never raises)
[--maxprocesses=64 -n 3]   exit=0 workers=3
```

## 3. Test-smell rejection list: the NEW section-5 tests
A hit is a CONTRACT defect. It is reported here, not patched.

| Smell | Result |
|---|---|
| Tautology | **None.** The ruling-1 oracle is pytest's OWN parser with `xdist.plugin` registered (`_xdist_option_parser`), not the gate's placement logic. The expected counts are the ruled constants `RULED_WORKERS_*`, never read back from `_pytest_sessions`. The refusal rows are tied to the helper only by the row→helper direction (`test_every_refused_row_is_a_spelling_the_shared_helper_recognises`), and the refusal itself is checked by behaviour: no spawn, exit 2, the policy named. |
| Unrepresentative fixture | **None.** The forwarded args are real selectors and real agent flags (`-x`, `--tb=line`, `-k "budget and not slow"`, `-p no:randomly -rfE`). `-n auto` is the CLAUDE.md habit. The own-pid fixture is a fake `/proc` holding only the gate's own pid, with the live gate-leg argv. Both branches are driven on every matrix row, so there is no value monoculture in the count. **§2 proved that the own-pid fixture discriminates on its own (A′).** |
| No magnitude guard on a derived output | **N/A.** The worker count is a two-valued ruled enum, not a derived magnitude. |
| Forward-run-as-validation | **N/A, stated explicitly.** This is pure logic with a fixed spec: argv placement, a refusal predicate, and a routing rule. Nothing is derived from data, so green tests are sufficient. The scored-holdout clause does not apply. |
| Drift-prone hardcoded convention | **One LOW hit, T2 (§1e).** The completeness pin keys its reach on the names `{_run_selected_gates, GateRunner}`, not on callers of the render chokepoint (`GateSpec.resolved_command` / `GateRunner.run`). `KNOWN_RENDER_CALLERS` is a hand-list, and it has a completeness assertion, but that assertion's domain is itself name-keyed. Other literals are not defects: `XDIST_WORKERS_FLAG = "-n"` is an independent oracle copy (as ruled in the first audit, F10), `CLUSTERED_WORKER_FLAG`/`"3"` pin the measured bound, and `_REFUSED_*` rows are proven ⊆ the helper's spellings. |
| (brief extra) Rider dropped | **HIT, D-2 (§1a/§2b).** Lead ruling D1-F3 has no pin. The contract's leg-runner rows are type-agnostic (`pytest.raises(Exception)`), and the CLI rows check only `exit 2` plus the policy name. A `ManifestError` build passes 76/76. |
| (brief extra) Re-open trigger unmeasured | **LOW, P6.** F8 trigger #2 ("the first clustered worker flag seen in a real gate invocation") has no instrument. The pin-the-miss test is the real guard. |

## 4. Refactors applied (all prose; zero behaviour change; gated after the last edit, §5)
Content backup taken first (`cp -a` → `…/scratchpad/backup-pre-refactor/`). My changed lines: `pending_contract_gate.py` 21, `wave_gate.py` 3, `gates.yaml` 12 (diff line counts against that backup).

1. **P1: gates.yaml FIELDS `command` entry.** "so no other spelling can override it" became "so no other `-n` / `--numprocesses` spelling can override it (xdist: last wins)". I added: "Other xdist options are NOT policed: a forwarded `--maxprocesses` is passed through and can only LOWER the count." That is the measured bound (§2d probe), stated where the rule is stated.
2. **P1 + P9: gates.yaml `pytest` description.** I DELETED the delta's sentence "The policy's `-n` is the LAST worker flag of the run, and a worker count forwarded to this gate is refused, so the policy is the only thing that sets it."
   - **P9 was found during this fix, AFTER §1 was written, and I say so here.** The manifest's own FIELDS header rules `description` to be "what it is FOR. Prose here describes intent, never behaviour", and this sentence was behaviour. It was also P1's false claim, and it duplicated the FIELDS `command` entry.
   - The one home for the rule is now the FIELDS `command` entry.
   - The only test that reads descriptions (`test_no_shipped_gate_description_teaches_the_retired_count`) pins the ABSENCE of the retired literal, so it is unaffected.
3. **P1: `pytest_args` argparse help** (`pending_contract_gate._build_parser`). "Its xdist worker count is NOT forwardable" became "A worker count is not forwardable … renders its -n as the LAST worker flag … Other xdist options pass through unchecked (--maxprocesses can only lower the count)".
4. **P1 sibling: `_with_policy_workers_last` docstring.** "no other spelling" became "no other worker-flag spelling".
5. **P2: `_hardcoded_worker_counts` docstring.** The second caller is now named correctly: `_refuse_forwarded_worker_counts`, which `_run_selected_gates` runs first.
6. **P3: same docstring.** "its constructor demands `_ispytest=True`" became "its constructor warns `PytestDeprecationWarning("A private pytest class or function was used.")` unless passed `_ispytest=True`". I read the installed pytest 9.0.3 source: `Parser.__init__(…, *, _ispytest: bool = False)` calls `check_ispytest`, and `check_ispytest` does `warn(PRIVATE)`, where `PRIVATE = PytestDeprecationWarning("A private pytest class or function was used.")`.
7. **P5: `pending_contract_gate.main` docstring.** The first line is now "2 = no measurement happened", and a new line lists the four exit-2 causes: BROKEN INSTRUMENT, MANIFEST error, REGISTRY error, REFUSED ARGUMENT.
8. **P4: `wave_gate.main` docstring.** Exit 2 now names "a REFUSED ARGUMENT (a `--wave` selector carrying a worker count; no gate spawns)".
- **Structural refactors: none warranted.** The delta already has one recogniser (`_worker_flags`), one refusal helper, one policy resolution site, and one render chokepoint (§1b).
- **De-bloat: none.** No section-5 test is strictly subsumed.
  - The routing pin, the rows-are-the-helper's-spellings pin and the refusal rows each fail on a different wrong build.
  - A′ (§2a) shows the own-pid rows are not subsumed by the ruling-1 rows, because only they catch it.
  - The DUAL-edited section-3 forwarded test overlaps the ruling-1 `selected-plain` rows, but it additionally runs `_workers_in` (exactly one `-n` in argv). The ruling-1 rows do not assert that; they take the LAST `-n`. That test therefore catches a "substituted in place AND appended" build that the matrix alone would let through, so it is not strictly subsumed.

## 5. Final gate tails (2026-09-26, HEAD `f66a190` + working tree, after the last edit)
```
$ uv run pytest -q -p no:cacheprovider --tb=short -n 12 loremaster/tests/test_loopback_serving.py loremaster/tests/test_migration_wire_budget_503.py loremaster/tests/test_migration_wire.py scripts/test_pytest_workers_503.py scripts/test_concurrent_wire_acceptance.py scripts/test_gate_currency.py scripts/test_pending_contract_gate.py scripts/test_wave_gate.py
276 passed, 22 warnings in 27.55s          (pytest exit=0 via PIPESTATUS)
$ cd skills/lore-deploy/scripts && uv run python -m pytest -q -p no:cacheprovider . ../tests
120 passed in 17.33s                       (exit=0)
$ uv run ruff check scripts/pending_contract_gate.py scripts/wave_gate.py scripts/_pytest_sessions.py
All checks passed!
$ ./scripts/typecheck.sh                   (exit 1)
Found 53 errors in 23 files (checked 297 source files)   typecheck: loremaster FAILED
Found 1 error in 1 file (checked 63 source files)        typecheck: scripts FAILED   (scripts/test_forgery_door_sweep.py:42 — loremaster.tasks has no SupersedeResult)
lorerunes / lorescribe / loresigil / skills / docs/eval / shellcheck: OK
→ 54 error lines total; 0 in pending_contract_gate.py / wave_gate.py / _pytest_sessions.py / test_pytest_workers_503.py
$ uv run python scripts/pending_contract_gate.py --verify-registry   → exit 0
$ uv run python scripts/wave_gate.py --help                          → exit 0
$ ruff format drift (via --stdin-filename under the repo config), my edits' before → after:
  pending_contract_gate.py 197 → 197 diff lines · wave_gate.py 20 → 20   (pre-existing; ruff format is not a manifested gate)
```
The count of 54 typecheck errors matches the builder's (REPORT-impl-503-d1 §Gate tails). All of them are in other packets' files.

## 6. DRY ledger
**I introduced 0 new symbols.** The delta's new symbols were index-checked, not asserted:

| symbol (builder's) | query run | returned | verdict |
|---|---|---|---|
| `_worker_flags` / `_WorkerFlag` / `_with_policy_workers_last` | `lore_search("parse argv for xdist -n / --numprocesses worker flag spans and move or refuse them")`, plus awk over `scripts/*.py` | only `REPORT-contract-503-d1.md` prose. `scripts/` is not in the graph (#507) | awk confirms one recogniser; `_hardcoded_worker_counts` is EXTENDED over it, not forked |
| `ForwardedWorkerCountError` | `lore_search("exception raised when a CLI argument is refused, printed as REFUSED ARGUMENT with exit code 2")` | a test helper `_refuse` (`test_logging_setup.py`, unrelated) and review prose | no prior typed refusal; HAND-ROLLED per D1-F3 is justified |
| `_refuse_forwarded_worker_counts` | awk `def _refuse` over `scripts/`, `skills/` | `restore_prod_dump._refuse_foreign_endpoint` (httpx guard, different domain) | one refusal helper; it CALLS the shared recogniser |

## 7. Symbols and behaviours DELETED or REPLACED by the delta (vs the first-pass green copies; `wave_gate.py` vs HEAD)
| deleted / replaced | where | disposition |
|---|---|---|
| the inline recognition loop in `_hardcoded_worker_counts` | pcg | MOVED byte-for-byte into `_worker_flags` (I compared the old body with the new function). The helper keeps its name, signature and output |
| **behaviour:** `resolved_command` substitutes `{workers}` IN PLACE, where the manifest put the flag | pcg | replaced (ruling 1, Reading B): when `workers` is given, the flag moves LAST. With `workers=None` it is still left in place |
| **behaviour:** `_run_selected_gates` accepts forwarded worker flags (last one wins) | pcg | replaced (ruling 2): refused before any spawn with `ForwardedWorkerCountError`. **Not extended to `--derive` / `--verify-registry` (D-1)** |
| **pin:** forwarded args at the argv TAIL (`argv[-len(forwarded):] == forwarded`) | test_pytest_workers_503 | replaced by a contiguity check (the contract's DUAL row); the position is now pinned by the ruling-1 matrix |
| `pytest_args` help "extra arguments forwarded to the pytest gate" | pcg | replaced (builder); reworded again by me (P1) |
| the one-line `_run_selected_gates` docstring | pcg | replaced with the ordering-and-refusal docstring |
| gates.yaml FIELDS sentence "A junit gate that hardcodes a count instead is a PARSE FAILURE (lore #503)" | gates.yaml | content kept, reflowed into the longer entry (builder + P1) |
| `pcg.main` docstring first line "2 = a BROKEN INSTRUMENT" | pcg | replaced by me (P5) |
| the delta's gates.yaml description sentence (never at HEAD) | gates.yaml | deleted by me (P1/P9) |
| `_pytest_sessions.py` | — | nothing deleted: UNCHANGED against the first-pass copy |

## Capability check (brief-base §4) and role note
- **Demanded vs had:** everything was satisfiable. `scripts/` is not in lore's graph (#507, already filed), so the structural sweeps used **awk** (grep/rg are hook-blocked, #473). I am saying that fallback out loud; there is no new friction to file.
- **I did not register on `lore_comms`:** the brief named no ledger row, and the deliverable is this file. I declared the idle-gate contract file for `REPORT-refactor-503-d1.md`.
- No full suite, :18500 never touched, and no process killed. Every scratch mutation was restored byte-exact, and the real tree was never mutated by a probe.
- **Role boundary (brief-base §2), two readings, written down:**
  - The non-overridable clause forbids "grader/auditor → fixer: editing the code it judges".
  - Reading 1 (the one I took): tdd-light Phase 5 is operator-authored skill law defining ONE invocation that audits and then refactors. Findings were written BEFORE any edit (per the skill), and fixes were limited to prose, so this is the phase's own definition and not a brief-added transfer. The grader runs (§2) are audit work and within role.
  - Reading 2: any edit by the auditor needs a quoted operator grant.
  - Under Reading 2, my §4 edits are 36 prose lines. They can be reverted from `…/scratchpad/backup-pre-refactor/` with three `cp` commands, and every finding stays valid.
  - **Lead's call.**

## Unrelated failures
`./scripts/typecheck.sh`: 54 mypy errors, all outside this cycle's files (§5). No test failed in the scoped runs.
