brief-base v24 read
brief project v7 read

## SUMMARY (audit-165, tdd-light Phase 5 REFACTOR + AUDIT, lore #165; written 2026-10-31 ~18:30Z)
- **State:** done-with-deviations. **VERDICT: GO** (attribution of the full-suite reds is in §R6).
- **Deviations:**
  1. The literal DRY sweeps were NOT RUN: the hook denied grep even in scratch copies (#561).
  2. The `mutation_proof.py` verdicts for M1–M4 were hand-diffed: the tool false-FAILs on the id form (#560). M5 PASSED in the tool.
  3. The M3 and M5 runners returned no final report; I read their logs directly.
- **Packages considered:** none. No mechanism specified (the refactor reshapes a string; stdlib `pathlib` predicate).
- **Odoo-20 portability:** n/a. No Odoo seam touched.
- **Reuse ledger:** 0 new symbols of mine; the builder's 8 are dispositioned in §DRY ledger. Sharing is proven by mutation (M1).
- **Graded:** 26c3a20 + uncommitted diff (lore_deploy.py f3859a7b…, snapshot.py 247bccfb…, indexer.py 379df279…) · HEAD-at-report: 26c3a20 · SAME.
- **Rulings:** F1 (c)(i)+(c)(ii), R1, R2, R3, S1, S2 are all MET. #166 stays out, as ruled.
- **Mutations** (§Mutation results, §M5): 5 of 5 killed EXACTLY their declared sets, both ways.
  - M1 sharing: both sides moved.
  - M2 clone: killed.
  - M3 outage guard: killed.
  - M4 target, incl. the real-image pin: killed.
  - M5 first-tier-only: killed.
  - Every leg's provenance is in-copy, including the spawned interpreter's `loremaster.__file__`.
- **Findings** (§Cold findings):
  - 2 ROUTED behavioural/contract items: A1, a RuntimeError escaping after teardown on the recreate path (LOW); A8, the remedy runs under bare `python` (LOW).
  - 2 ROUTED test smells: T1 (substring "healthy dir" check), T8 (expr-substring stub).
  - 1 kept with a trigger: A2, +~1s per start.
  - Fixed in place: A3 + A4.
- **Refactor:** A3 (readable expression, **byte-identical by oracle**) + A4 (WHY comment). Deletion inventory: 2 local names, 0 behaviours.
- **R5 targeted:** **234 passed**, EXIT=0, matching the builder's GREEN.
- **R7 gates:** ruff clean. Typecheck has 83 errors = the 83 RED_ADJUDICATED baseline, 0 in graded files.
- **R6 full suite** (`flock`, -n 12): **530 failed, 13442 passed, 67 skipped, 3 xfailed**, 12m59s, no cap kill.
  - 0 failures in the graded area.
  - All 32 failing files are named in `scripts/pending_contracts.yaml`.
  - **HEAD control: the identical 530 ids fail with the graded files at HEAD, so 0 are attributable** (§R6).
- **Decisions needed:**
  - A1: route it to an implementer (catch `RuntimeError` after teardown + a pin)?
  - A8: should the remedy name the venv interpreter? That is a contract text change.
- **Pointers:** §Routing table · §Mutation declarations/results · §Cold findings · §Refactor · §R5 · §R6 · §R7 · §DRY ledger · §Instruments · §Anything noticed.
- **Fan-out:** haiku 12 (worker 2, runner 10) · sonnet 0 · peak 4.


# REPORT-audit-165 — tdd-light Phase 5 REFACTOR + AUDIT, lore #165 (2026-10-31)

(summary block is written at the end; this file grows incrementally)

## Routing table (written before the first sweep, brief-base v24 §3)

| step | tier | who | reason |
|---|---|---|---|
| R1 cold diff read + rulings check | 3 | self (Opus) | brief: inline audit judgment |
| R2a `lore_index(reconcile=True)` | 1 | self | single call on the critical path before R2b |
| R2b reuse sweep: `lore_search` per new symbol job (`SnapshotLayout.is_materialized`, `_unmaterialised_static_tiers`, `_require_launchable_snapshot`, `_gate_snapshot_precondition`, `_SNAPSHOT_SUBPATH`/`CONTAINER_SNAPSHOT_ROOT`, `_STATIC_ROOT_COUNT_EXPR`, `_COLD_INDEX_MODULE`) | 1 | self, ONE parallel batch of 7 calls | small set (7), output read in full anyway; a Haiku spawn would add latency on the critical path |
| R3 scratch copies (one per mutation, 4) | 1 | haiku-worker | brief-routed |
| R4 mutation edits | 3 | self, in scratch only | brief: judgment |
| R4 mutation runs (M1–M4) | 1 | haiku-runner ×4, parallel (one scratch copy each) | brief-routed |
| R4 mutation verdicts | 3 | self | never Haiku |
| test-smell list over the contract (26 pins) | 3 | self | a sampled Sonnet draft would miss whether a pin can fail — that needs the mutation runs I own; 26 pins is small |
| R5 targeted re-run | 1 | haiku-runner | brief-routed |
| R6 full suite | 1 | haiku-runner | brief-routed |
| R7 gates | 1 | haiku-runner | brief-routed |

## Mutation declarations (written BEFORE any mutation run, 2026-10-31; ids from `--collect-only -q` in /var/tmp/claude-1000/a165-m1)

Scratch copies `/var/tmp/claude-1000/a165-m{1..4}` via `scripts/scratch_copy.sh` (exit 0 ×4, provenance `loremaster -> /var/tmp/claude-1000/a165-mN/loremaster/loremaster/__init__.py`).
Graded-file md5 in every copy == the working tree (lore_deploy.py f3859a7b…, snapshot.py 247bccfb…, indexer.py 379df279…).
Anchor/replacement files were generated from each copy's own bytes by an exact-once script (instrument pasted in §Instruments).

| id | mutation | run scope | declared RED |
|---|---|---|---|
| M1 | `SnapshotLayout.is_materialized`: `return any(materialization_dir.iterdir())` → `return True` (non-empty leg dropped) | test_launch_snapshot_bind.py + loremaster/tests/test_static_snapshot_reacquire.py | `…test_launch_snapshot_bind.py::TestOneLaunchPreconditionDecidesBothLevels::test_launch_and_verb_start_agree_on_refusal[3-tier_empty]` (deploy side) · `…::TestDeployPreconditionAgreesWithServerGuard::test_deploy_refuses_a_tier_iff_server_guard_reads_it_unmaterialised[empty]` (server-side fixture anchor) · `loremaster/tests/test_static_snapshot_reacquire.py::TestStaticSnapshotReacquire::test_matching_stamp_reacquires_when_snapshot_dir_empty` (server guard behaviour) |
| M2 | deploy precondition hand-rolls `<root>/<tier>` (is_dir + non-empty, layout bypassed) instead of `layout.is_materialized` | test_launch_snapshot_bind.py | `…::TestDeployPreconditionAgreesWithServerGuard::test_deploy_reads_the_server_layout_not_a_retyped_root_slash_tier` only (real static tiers are not in `TIER_SUBDIRS`, so their dir == name; only `pip` diverges) |
| M3 | recreate path: `_gate_snapshot_precondition` moved after `podman stop` + `podman rm` | test_launch_snapshot_bind.py + test_lore_deploy.py | `…::TestVerbStartRefusesMissingSnapshotBeforeTeardown::test_static_roots_with_absent_snapshot_return_error_with_no_destructive_podman[recreate]` · `…::TestMalformedConfigAbortsRecreateBeforeTeardown::test_malformed_config_on_recreate_path_leaves_container_and_reports` |
| M4 | bind target `CONTAINER_SNAPSHOT_ROOT` → `/source` | test_launch_snapshot_bind.py | `…::TestStaticRootsBindSnapshotAtServerDefaultRoot::test_static_roots_bind_host_snapshot_once_at_server_default_root[1]` · `…[3]` · `…::test_no_bind_targets_the_retired_source_path` · `…::TestLaunchCommandBootsTheGuardTrueInTheRealImage::test_launch_command_makes_guard_true_for_every_static_tier` |

(`…` = `skills/lore-deploy/scripts/test_launch_snapshot_bind.py`)

## Mutation results (M1–M4, measured 2026-10-31 ~17:45Z on scratch copies of the graded tree over 26c3a20)

`scripts/mutation_proof.py` printed `PROOF FAILED` (exit 4) on all four. **Every one is an id-FORM mismatch, not a set mismatch:** the declared ids come from `--collect-only -q` (rootdir-relative: `skills/lore-deploy/scripts/test_launch_snapshot_bind.py::…`, `loremaster/tests/…`); pytest's short summary prints CWD-relative ids (`test_launch_snapshot_bind.py::…`, `../../../loremaster/tests/…`) when cwd ≠ rootdir. The tool's own help tells you to take ids from `--collect-only`, and it never normalises them. I diffed by hand, test by test (normalised path-to-rootdir): **observed == declared in all four, both directions.** Tool defect filed (§Anything noticed).

| id | declared RED (n) | observed RED (pytest tail) | both-ways diff (normalised) | landed / restored | provenance (host loremaster · lore_deploy · spawned interpreter · spawned loremaster) |
|---|---|---|---|---|---|
| M1 is_materialized drops non-empty leg | 3 | `3 failed, 27 passed`: agreement[empty] · R1 [3-tier_empty] · reacquire `…_snapshot_dir_empty` | ∅ / ∅ | exactly once · md5 247bccfb… restored | all four under `/var/tmp/claude-1000/a165-m1/…` |
| M2 deploy hand-rolls `<root>/<tier>` | 1 | `1 failed, 25 passed`: `…_not_a_retyped_root_slash_tier` | ∅ / ∅ | exactly once · md5 f3859a7b… | all four under `a165-m2` |
| M3 recreate gate after stop+rm | 2 | `2 failed, 61 passed` (incl. test_lore_deploy.py, 0 reds there): absent-snapshot [recreate] · malformed-config R2 | ∅ / ∅ | exactly once · md5 f3859a7b… | all four under `a165-m3` (re-derived by me; the runner exited without a report, log read directly) |
| M4 bind target → `/source` | 4 | `4 failed, 22 passed`: pin1 [1] · [3] · no-/source · pin 2 artifact (in-image guard `False ×3`) | ∅ / ∅ | exactly once · md5 f3859a7b… | all four under `a165-m4` |

**Verdicts.**
- M1, the sharing proof (S1 pin 4 / R1), is KILLED on BOTH sides. Breaking the one predicate moved the deploy refusal (R1 tier_empty cell) AND the server guard: the agreement pin's server-side anchor, plus the FP-05 re-acquire behaviour in `test_static_snapshot_reacquire.py`. That proves sharing by mutation.
- M2 (clone) is KILLED by the layout pin alone. As declared, it is the only discriminator, because the 3 real static tiers fall back to `<root>/<tier>`. See test-smell T3.
- M3 (outage guard) is KILLED by both recreate legs.
- M4 (target) is KILLED by pins 1 and 2, including the real-image probe.
Logs: `/var/tmp/claude-1000/a165-mut/m{1..4}.log` (scratch, not durable; this table is the record).

## Cold findings (written 2026-10-31 ~17:50Z, BEFORE any edit to the graded files)

Graded diff md5: lore_deploy.py `f3859a7b9462c06cc3a4d2fa1d2e16ad` · snapshot.py `247bccfbf97ff45abd1fb0ff152d9699` · indexer.py `379df27999b257b19f2b417ea2b48b9c` · contract test_launch_snapshot_bind.py `ddb8ce063c1df6f351659f86b794f9f4`.

**Rulings coverage (R1 cold read):**
- F1(c)(i) is MET: `_launch_container` → `_require_launchable_snapshot` raises `RuntimeError` before any podman call.
- F1(c)(ii) is MET on both paths. On the recreate path the gate sits before `_probe_embed` and before stop/rm. On the fresh path it sits after the image/env checks and before the probes.
- R1 is MET: one function, `_require_launchable_snapshot`, and `_gate_snapshot_precondition` only wraps it.
- R2 is MET: the config-read RuntimeError is caught by the gate before teardown.
- R3 is MET: `{error}` reaches stderr.
- S1 is MET: the predicate moved to `SnapshotLayout.is_materialized`, the Indexer delegates, and deploy evaluates it over the host root through `_read_config_field`.
- S2 is MET, through `is_dir`.
- #166 is out, as ruled; the bound is in the Indexer docstring.
- Riders: pins 1–3 were the contract's. Pin 4 is proven by M1 above.

| # | sev | file:symbol | finding | disposition |
|---|---|---|---|---|
| A1 | LOW | lore_deploy.py:`verb_start` (recreate `except subprocess.CalledProcessError`) + `_launch_container` | **A RuntimeError can escape AFTER teardown.**<br>• Mechanism: `_launch_container` re-runs `_require_launchable_snapshot` after `podman stop` + `rm`. The recreate handler catches only `CalledProcessError`. If a tier becomes unmaterialised between the gate and the launch, or the second `_read_config_field` subprocess fails, a raw traceback reaches the dispatcher with the stale container already gone.<br>• The window: `_probe_embed` + `_probe_surreal` + `podman stop` (≤10s).<br>• The property it violates: the block's own comment, *"after teardown every launch failure degrades to loud `_EXIT_ERROR`, never a raw raise."*<br>• Same class at HEAD: HEAD's `_launch_container` also called `_read_config_field` after teardown. This diff adds a second raise site. | **ROUTED** (behaviour change + needs a pin; brief: behavioural → route). Candidate fix: `except (subprocess.CalledProcessError, RuntimeError)`, plus a pin where the second precondition evaluation raises after rm. |
| A2 | LOW | lore_deploy.py:`_require_launchable_snapshot` ×2 per start | **Cost.**<br>• A `start` now spawns up to 4 loremaster interpreters (gate: count + tiers; launch: count + tiers), against 1 at HEAD. Measured: 0.25s warm, 0.67s cold each, so ≈ +0.75–1s per start.<br>• **It cannot be merged without breaking existing test seams.** `test_lore_deploy._stub_read_config_field` dispatches on `expr` substrings (`"port"` → port, `"static"` → `"0"`). A single JSON-returning read would get `"0"` back and crash every recreate test. Passing the decision down changes `_launch_container`'s 3-arg signature, which tests replace positionally.<br>• The re-check also closes the gate→launch TOCTOU, so it is not pure waste. | **keep_with_trigger** (trigger: start latency becomes an operator complaint). Not fixed. |
| A3 | LOW | lore_deploy.py:`_unmaterialised_static_tiers` | Dense single-line `__import__` expression (builder F1). Option B, an imports kwarg on `_read_config_field`, is **ruled out by the same stub seam**: every `(config_path, expr)` stub would TypeError. So option A is forced; only readability is fixable. | **FIX IN PLACE** (refactor, byte-identical expression proven by an oracle) |
| A4 | INFO | lore_deploy.py:`_STATIC_ROOT_COUNT_EXPR` / tiers expr | **The `'static'` literal stays.**<br>• The owner constant `loremaster.config.WATCH_STATIC` exists.<br>• Using it inside the subprocess expression needs `__import__`, which contains the substring `"port"`. The test stub would then answer the port, and test_lore_deploy breaks.<br>• The value is also owned by `RootConfig.watch: Literal["live","static"]`, so a rename breaks every lore.yaml loudly first.<br>• Pre-existing at HEAD (moved, not new). | keep, with a WHY comment (fix in place: comment only) |
| A5 | INFO | lore_deploy.py:`_require_launchable_snapshot` `in ("", "0")` | **The `""` arm is unreachable both ways:** `print(sum(...))` always prints an int, and the test stub returns `"0"`. Pre-existing at HEAD (moved). Replacing it with `int(...) == 0` would add a `ValueError` raise type to a function documented to raise only `RuntimeError`. | keep (no gain, adds a raise type); recorded |
| A6 | INFO | builder F4 | **Closed.**<br>• Builder concern: the printed remedy path could be relative.<br>• `main` does `Path(args.project).resolve()`, so `config_path` is always absolute. | closed |
| A7 | INFO | builder F3 | **Pre-existing:** a refused fresh start still `rm -f`s an EXITED container. That is not an outage. Unchanged by this diff. | noted for lead |
| A8 | LOW | refusal text `python -m loremaster.index …` | **The remedy runs under bare `python`.**<br>• On the host, bare `python` is not the loremaster venv (lore_deploy itself resolves `_loremaster_python()`). Pasted verbatim outside the venv, the command fails with `ModuleNotFoundError`.<br>• The exact text is pinned by amendment r2 item 3. | **ROUTED** (contract/ruling decision; property: "a paste-ready remedy runs as pasted") |

**DRY / prior-art (R2: one parallel batch of 7 lore calls after `lore_index(reconcile=True)`; files_indexed 4031, `lore` @ 26c3a20):**
- `SnapshotLayout.is_materialized`: no other owner. `lore_search` ("materialisation dir is_dir … non-empty") returned only the ruling and the FP-05 suite; `lore_impact` shows 1 prod consumer, `Indexer._snapshot_materialized`. EXTENDED `SnapshotLayout`, correctly.
- `_SNAPSHOT_SUBPATH` / `CONTAINER_SNAPSHOT_ROOT`: the server owns `_DEFAULT_SNAPSHOT_ROOT`. The stdlib-only dispatcher cannot import it, and the contract pins the agreement. Acceptable.
- `_STATIC_ROOT_COUNT_EXPR`: same expression as HEAD, moved.
- `_COLD_INDEX_MODULE`: the module path appears in prose (`references/server-interface.md`); no code owner.
- ⚠ **The literal exhaustiveness sweeps were NOT RUN** (`any(…iterdir())`, `watch == 'static'`, `lore-snapshot`). The repo's PreToolUse hook denied grep even when targeted at a scratch copy under `/var/tmp`, for both me and a haiku-worker. The semantic searches above are the only reuse evidence, which is a coverage gap. Friction filed.

**Test-smell list over the contract (26 pins):**
| # | smell | pin | detail | disposition |
|---|---|---|---|---|
| T1 | drift-prone hardcoded convention | `_assert_teaches_every_failing_tier` | **The "healthy dir not named" check is a substring test** (builder's lead). With healthy `<root>/x` and failing `<root>/x-y`, a CORRECT refusal reads as naming the healthy dir: a false RED, not a wrong-build door. Latent: the 3 real tiers share no prefix. The `tier in text` leg is implied by the `tier_dir in text` leg whenever dir == name, so it adds no discrimination. | ROUTED (contract author), LOW |
| T2 | unrepresentative fixture (position monoculture) | agreement + R1 per-tier cells | **Every per-tier fixture breaks `tiers[0]`.**<br>• A build that checks only the FIRST static tier survives every per-tier cell.<br>• It may be caught by the absent-root message pins (`failing=None` requires ALL tiers named). | **M5 below proves it by construction** |
| T3 | single discriminator | `…_not_a_retyped_root_slash_tier` | **The one pin standing between a `<root>/<tier>` clone and green.**<br>• It is the only pin, because all real static tiers fall back to their own name (M2: 1 of 26).<br>• It discriminates correctly and fails loud if `TIER_SUBDIRS` loses every divergent entry. | OK, noted |
| T4 | forward-run-as-validation | — | n/a: pure logic with a fixed spec. **The data-driven validation clause does not apply.** | — |
| T5 | magnitude guard | — | n/a | — |
| T6 | tautology | agreement pin | **Not a tautology,** although both sides now call one predicate: the server side is anchored to the fixture (`server_unmaterialised == expected`), and M1 reddened that anchor. **A byte-identical deploy-side CLONE passes it by construction**; only mutation (M1) can see that, which is exactly why the ruling put pin 4 on the audit. | OK |
| T7 | artifact pin scope (bound) | pin 2 | It grades the image currently tagged `localhost/lore:latest`, whose `Indexer._snapshot_materialized` predates the delegation. **The server-side delegation reaches production only on rebuild**; host evidence is the FP-05 suite plus M1. | noted (deploy smoke owns it) |
| T8 | (noticed, outside the contract file) | `test_lore_deploy._stub_read_config_field` | **It dispatches on `expr` SUBSTRINGS.** Any future expression containing `__import__` contains `"port"` and is answered with the port. That is a spelling-keyed stub, and it is what forces A2/A3/A4. | ROUTED (test hygiene), LOW |

## M5 declaration (written BEFORE the run): position monoculture (T2)
- **Mutation:** in `_unmaterialised_static_tiers`, `for r in c.roots` → `for r in [next(x for x in c.roots if x.watch == 'static')]`, so only the FIRST static tier is checked.
- **Scope:** test_launch_snapshot_bind.py. Ids are in cwd-relative form, to sidestep the tool defect.
- **Declared RED:**
  - `test_launch_snapshot_bind.py::TestMissingHostSnapshotRefusesLaunch::test_static_roots_with_absent_host_snapshot_refuse_without_podman`
  - `test_launch_snapshot_bind.py::TestVerbStartRefusesMissingSnapshotBeforeTeardown::test_static_roots_with_absent_snapshot_return_error_with_no_destructive_podman[fresh]`
  - `…[recreate]`
- **Prediction:** each of the 3 requires every tier to be named, and everything else stays green. If observed == declared, T2's door is CLOSED by the message pins.

## Refactor (after the findings above; 2026-10-31 ~18:00Z)
Content backup first: `/var/tmp/claude-1000/a165-backup/` (md5 == graded md5 for all three files).

- **A3 (fixed in place), lore_deploy.py:`_unmaterialised_static_tiers`.**
  - The one dense expression is now built from named parts (`host_layout`, `failing_tier_dirs`), with a WHY comment: `_read_config_field` evaluates ONE expression, so the imports ride `__import__` and `for layout in [...]` binds the layout once.
  - **Byte-exact oracle:** both expressions `_require_launchable_snapshot` sends to `_read_config_field` were captured before and after, and `cmp` reports them identical. The oracle script is pasted below.
- **A4 (comment only), lore_deploy.py:`_STATIC_ROOT_COUNT_EXPR`.** The new comment records why the `'static'` literal stays, rather than `WATCH_STATIC`.
- **Not changed, with reasons:**
  - A2 (merging the subprocess reads) and builder F1 option B are both blocked by the test seams.
  - The A5 `""` arm stays: no gain, and removing it adds a raise type.
  - snapshot.py and indexer.py were already minimal: one predicate with a docstring, plus a delegation.

lore_deploy.py md5 after the refactor: `191f90d138afc1e4e3692bf2568ef7ac`. snapshot.py and indexer.py are untouched (they still equal the graded md5).

**Deletion inventory (this refactor):**
- Deleted: the local name `layout`, renamed `host_layout` (it is a Python name in lore_deploy, not a name inside the expression; the in-expression comprehension variable `layout` is unchanged) and the local name `expr`, inlined into the call.
- No symbol, branch, guard, side effect or output field was deleted.
- Behaviour deltas: none, per the oracle.

## Instruments (pasted verbatim, brief-base §1)
### expr_oracle.py: the byte-exact refactor oracle
```python
"""Capture the exact expression strings lore_deploy's snapshot precondition sends to _read_config_field."""
import sys
from pathlib import Path
sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/skills/lore-deploy/scripts")
import lore_deploy

captured = []
def _capture(config_path, expr):
    captured.append(expr)
    return "{}" if len(captured) > 1 else "3"
lore_deploy._read_config_field = _capture
lore_deploy._require_launchable_snapshot(Path("/x/lore.yaml"))
for expr in captured:
    print(repr(expr))
```
Run it before and after (`uv run python expr_oracle.py > before|after.txt`), then `cmp before.txt after.txt`.

### prep.py: exact-once mutation anchor builder (M1–M4; M5 is built the same way)
```python
from pathlib import Path
out = Path("/var/tmp/claude-1000/a165-mut")
def once(text, anchor, label):
    n = text.count(anchor)
    assert n == 1, f"{label}: anchor matched {n}x"
# M1: drop the non-empty leg of SnapshotLayout.is_materialized
s = Path("/var/tmp/claude-1000/a165-m1/loremaster/loremaster/source/snapshot.py").read_text()
a = "        return any(materialization_dir.iterdir())\n"
once(s, a, "M1"); (out/"m1.anchor").write_text(a); (out/"m1.repl").write_text("        return True\n")
# M2: deploy hand-rolls <root>/<tier> (non-empty leg kept, so only the layout differs)
d = Path("/var/tmp/claude-1000/a165-m2/skills/lore-deploy/scripts/lore_deploy.py").read_text()
a = "\"if r.watch == 'static' and not layout.is_materialized(r.tier)})\""
once(d, a, "M2"); (out/"m2.anchor").write_text(a)
(out/"m2.repl").write_text("\"if r.watch == 'static' and not ((layout._snapshot_root / r.tier).is_dir() and any((layout._snapshot_root / r.tier).iterdir()))})\"")
# M3: move the recreate-path gate after stop+rm
d = Path("/var/tmp/claude-1000/a165-m3/skills/lore-deploy/scripts/lore_deploy.py").read_text()
gate = ("            # The static snapshot (and the config read it needs, R2) is a launch\n"
        "            # precondition too: a relaunch over an unmaterialised tier crashes boot.\n"
        "            if (rc := _gate_snapshot_precondition(config_path, container_name)) != _EXIT_OK:\n"
        "                return rc\n")
start = d.index(gate); rm = '            _run(["podman", "rm", container_name], check=False)\n'
end = d.index(rm, start) + len(rm)
block = d[start:end]; once(d, block, "M3")
(out/"m3.anchor").write_text(block); (out/"m3.repl").write_text(block[len(gate):] + gate)
# M4: revert the bind target to /source
d = Path("/var/tmp/claude-1000/a165-m4/skills/lore-deploy/scripts/lore_deploy.py").read_text()
a = 'cmd += ["-v", f"{SNAPSHOT_ROOT}:{CONTAINER_SNAPSHOT_ROOT}:ro"]'
once(d, a, "M4"); (out/"m4.anchor").write_text(a); (out/"m4.repl").write_text('cmd += ["-v", f"{SNAPSHOT_ROOT}:/source:ro"]')
print("ok")
```

## M5 result (T2: position monoculture), measured 2026-10-31 ~18:05Z, scratch a165-m2
- Provenance: host loremaster, lore_deploy and spawned loremaster are all under `/var/tmp/claude-1000/a165-m2/…`.
- Result: `3 failed, 23 passed`. **`PROOF HELD`, exit 0**: the declared set fired exactly, the mutation landed exactly once, and the file was restored to md5 f3859a7b….
- **T2 is CLOSED:** a first-static-tier-only build is killed by the absent-root message pins (`failing=None` requires every tier named).
- With cwd-relative ids the tool passes, which confirms #560's diagnosis.

## R7 gates (measured 2026-10-31 ~18:05Z, working tree incl. my refactor, HEAD 26c3a20)
- `uv run ruff check .` gives **All checks passed!** (exit 0).
- `./scripts/typecheck.sh` exits 1, as the baseline does.
  - loremaster leg: **82 errors, all in `loremaster/tests/*.py`**. scripts leg: **1** (`scripts/test_forgery_door_sweep.py:42`, `SupersedeResult`).
  - Total **83 = the 83 RED_ADJUDICATED baseline**. **0 errors in lore_deploy.py, snapshot.py or indexer.py**.
  - The skills, lorerunes, lorescribe, loresigil and docs/eval legs are OK.
  - (I did not run the `--legs` currency verdict, since #555 makes its line falsely read FAIL.)

## R5: targeted re-run after the refactor (measured 2026-10-31 ~18:07Z, working tree on 26c3a20, lore_deploy.py md5 191f90d1…)
- **RAN** (haiku-runner; the `RAN:` line was checked and is my command): `cd skills/lore-deploy/scripts && systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q . ../tests ../../../loremaster/tests/{test_indexer,test_source,test_static_snapshot_reacquire,test_indexer_bulk_sweep,test_graph_wiring}.py --timeout=300 -p no:cacheprovider -n 8 -rf`
- **Tail, read by me** (`/var/tmp/claude-1000/a165-r5.log`): **`234 passed in 11.48s`**, EXIT=0, no collection errors. This equals the builder's GREEN of 234.
- Scope derivation: the brief's list, which is the builder's `lore_impact`-derived set (REPORT-impl-165 §Step C). It includes the real-image pin 2.

## DRY ledger (brief-base §6)
| new symbol | where I looked | returned | disposition |
|---|---|---|---|
| `SnapshotLayout.is_materialized` (builder) | `lore_search` "materialisation dir is_dir … non-empty" (budget 4000); `lore_impact` | only the ruling text + the FP-05 suite; 1 prod consumer (`Indexer._snapshot_materialized`) | EXTENDED `SnapshotLayout` (the ruled owner); the Indexer's inline copy was removed, so ONE copy remains, mutation-proven (M1) |
| `_unmaterialised_static_tiers` / `_require_launchable_snapshot` / `_gate_snapshot_precondition` (builder) | `lore_search` "launch precondition refuse before teardown…"; read `verb_start` | the pre-existing image/env-file guards are inline `if` blocks, with no shared precondition helper to extend | HAND-ROLLED (acceptable: a new precondition, one decision, R1-shared; M3 proves its placement) |
| `_SNAPSHOT_SUBPATH`, `CONTAINER_SNAPSHOT_ROOT` (builder) | `lore_search` "container path … lore-snapshot" | `loremaster.server._DEFAULT_SNAPSHOT_ROOT` is the owner, but the dispatcher is stdlib-only and cannot import it | HAND-ROLLED mirror, pinned by `CONTAINER_SNAPSHOT_TARGET` derivation in the contract (M4 proves) |
| `_STATIC_ROOT_COUNT_EXPR` (builder) | HEAD diff | the same expression as HEAD's inline literal | moved, not new |
| `_COLD_INDEX_MODULE` (builder) | `lore_search` "cold index command …" | prose only (`references/server-interface.md`); no code owner | HAND-ROLLED constant |
| (mine) none; the refactor introduced only local names `host_layout`, `failing_tier_dirs` | — | — | — |
⚠ The literal grep cross-check was NOT RUN (hook-denied, #561), so the "no other owner" rows rest on semantic search alone.

## Anything noticed
- **#560 (filed):** `mutation_proof.py` false-FAILs a correct proof when cwd ≠ rootdir, because of the id form. 4 of my 5 proofs hit it.
- **#561 (filed):** the grep hook blocks literal sweeps even in scratch copies, so exhaustiveness sweeps are impossible. That is why the DRY literal leg was NOT RUN.
- **#558 still open:** `_loremaster_python()` hardcodes `~/PycharmProjects/lore/.venv` as its fallback, so any proof without `LORE_PYTHON` grades the original tree. Every proof here exported `LORE_PYTHON` and printed the spawned interpreter's `loremaster.__file__`.
- **T8:** `test_lore_deploy._stub_read_config_field` dispatches on expr substrings. It now constrains production spelling (A2/A3/A4). That is a spelling-keyed stub, the "test behaviour, not spelling" class in reverse. Routed for test hygiene.
- **Builder F6 (docs):** `references/lifecycle.md` and `19-lore-deploy-rework.md` may need the new refusal text. They are outside my set, so not graded.
- Several haiku-runners returned only an interim "waiting on background work" hand-back, or none (M3, M5). I read their logs directly; every verdict above comes from a log I read, never from a runner summary alone.

## R6: the packet's ONE full suite (measured 2026-10-31 18:09–18:22Z, working tree incl. my refactor, HEAD 26c3a20)
- **RAN** (haiku-runner; the `RAN:` line was checked and is my command): `flock /tmp/lore-full-suite.lock systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run python -m pytest -q -n 12 -p no:cacheprovider -rf`, run from the repo root.
- **Tail, read by me:** **`530 failed, 13442 passed, 67 skipped, 3 xfailed, 6 warnings in 779.52s`**, EXIT=1. **No cap kill** (no 137 / Killed / INTERNALERROR / collection error). The 20 `ERROR loremaster.store._txn…` lines are captured log records, not summary entries.
- **Per-failure attribution (every one of the 530):**
  1. **0 failures in any graded or covering file:** lore_deploy, snapshot, indexer, launch_snapshot_bind, test_source, reacquire.
  2. The 530 span 32 files: packet-58 reanchor/supersede/task-shell ×~17, packet-64b findings ×~12, test_comms_footer (81), test_mcp_server `TestResolveManyAcknowledgeManyDispatch` (28), test_blocks_edge, test_exhaustion_fates, test_task_read_surface, scripts/test_forgery_door_sweep. **All 32 are named in `scripts/pending_contracts.yaml`** (filename match).
  3. **HEAD control (the decisive receipt).** In scratch `a165-m4`, the 3 graded files were reverted to `git show HEAD:` bytes (lore_deploy.py md5 d05b14eb… = HEAD); every other file is the same working tree. Running the same 32 files with `-n 8` there gives **`530 failed, 1310 passed`**. **The failing-id set is identical to the full suite's, 0 / 0 both ways** (provenance `PROV /var/tmp/claude-1000/a165-m4/loremaster/loremaster/__init__.py`).
  4. **⇒ 0 of 530 attributable to this diff.** They are the in-flight packet-58/64b/63c contract reds, red with or without #165.
- The diff script and id lists: `/var/tmp/claude-1000/a165-full-failed-ids.txt` (scratch). The method is set equality over `FAILED ` summary ids, full log against control log.

## VERDICT: GO
Every ruling and rider is met. Each of the 5 mutations killed exactly its declared set: sharing, clone, outage guard, target, and position. The refactor is byte-identical by oracle. Targeted: 234 passed. Gates are at the baseline. The full-suite reds are 0 attributable. The routed items (A1, A8, T1, T8) are LOW and none blocks the commit. A1 is the one I would route before the next start-path change.
