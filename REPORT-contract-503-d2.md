brief-base v17 read

# REPORT-contract-503-d2 — tdd-light Phase 1 FINAL DELTA for lore #503: three pins on a green build

## SUMMARY BLOCK
- **State:** done-with-deviations. Tests only. Nothing committed. Measured 2026-09-26 at HEAD `f66a190` plus the d1 build in the working tree. The build files are unchanged: `pending_contract_gate.py` md5 `4651686a…` before and after.
- **Deviations:**
  - (1) I also mutation-proved the D-2 `not isinstance` leg (survivor C) and both pin-the-miss pins (closing each bound). That goes beyond the one §2b survivor the brief named. The role reading is in §Capability.
  - (2) I added one thin oracle adapter, `_xdist_worker_processes`, on top of the reused `_xdist_option_parser`. Two readings of "not a new one" are in §Forks F1.
  - (3) I did not register on `lore_comms`, because the brief named no ledger row.
- **Packages considered:** worker-count cap oracle → xdist 3.8.0's own `xdist.plugin.pytest_cmdline_main` plus `pytest_xdist_auto_num_workers`, verdict `replace` (test oracle; `min()` is not hand-written). I read the installed `.venv/…/xdist/plugin.py` hook body (`numprocesses = min(numprocesses, config.option.maxprocesses)`), and probed that the parsed namespace carries `usepdb/collectonly/distload/dist/tx`. Parser: the existing `_xdist_option_parser`, REUSED.
- **Odoo-20 portability:** n/a — no Odoo seam touched.
- **Reuse ledger:** 5 new test-side symbols plus constants, all dispositioned (§DRY).
- **Graded:** n/a — this is an authored contract delta. Base: `f66a190` + working tree.
- **Decisions needed:** F1 (the adapter reading) · F2 (whether to promote the `REFUSED ARGUMENT` label to a production constant) · F3 (the D-1 generated sweep's `--currency` row overlaps ruling 2).
- **Headline:** 29 new pins, all GREEN on the current build (105 passed in the file). Four mutation proofs held, each an EXACT match against a set declared from `--collect-only` before the run:
  - §2b survivor B: **15/15**
  - subclass door C: **6/6**
  - D-1 closed: **4/4**
  - maxprocesses closed: **8/8**
- **Gates:** 8-file **305 passed / 0 failed** · ruff check clean · ruff format clean · `mypy` on the file clean · `typecheck.sh` 54 errors, all in other packets' files (same count as refactor-503-d1), **0 in the touched file**.
- **Receipts:** §1 tests · §2 kill proofs + instrument verbatim · §3 gate tails · §4 pre-flight · §5 realism · §Forks · §DRY · §Noticed.

## Capability check (brief-base §4) and role note
- **Demanded vs had:** everything was satisfiable.
  - `scripts/` is outside lore's graph (#507), and grep/rg are hook-blocked (#473), so the source reads used awk and sed. I am saying that fallback out loud; no new friction to file.
  - The lore DRY queries both completed: neither found an existing helper (§DRY).
- **Role boundary (§2), two readings, written down:**
  - The brief asked me to re-run refactor-503-d1 §2b's survivor against my own new pin, and framed that as contract-side mutation-proving.
  - Reading 1 (taken): refactor-503-d1 is a refactorer, not a grader. tdd-light has no adversary, and CLAUDE.md requires every load-bearing pin to be mutation-proven by its author ("a pin that cannot be demonstrated failing is not a pin"). That is the contract's own duty, not a grader's re-grade. Surviving-build replays by an author are banned when they re-grade a grader's findings. These are my pins, first proven here.
  - Reading 2: re-running any externally constructed wrong build needs an operator grant.
  - Under Reading 2, survivor C and the two bound-closings are still my own mutations of my own pins. Only B is at issue, and its result (15/15) is reproducible from §2's driver. **Lead's call.**
- No full suite was run. :18500 was never touched. Nothing was killed. All mutations ran in a `scratch_copy.sh` copy, and the real tree was never mutated.

## 1. Tests added (`scripts/test_pytest_workers_503.py`, new section 6; the docstring gains a d2 paragraph; the only other change is two imports: `inspect`, `SimpleNamespace`)
I diffed the pre-d2 content backup against the file: every pre-existing line is byte-identical except for the offset. No existing pin was edited.

| class | tests | ruling / bound |
|---|---|---|
| `TestTheRefusalIsLabelledAsARefusedArgument` | derived-families non-vacuity (1) · leg-runner raises `ForwardedWorkerCountError` and is NOT any other exit-2 family (6) · gate CLI stderr carries `REFUSED ARGUMENT:` and no other exit-2 label (6) · wave CLI, same (2) | D1-F3 rider (D-2) |
| `TestKnownBoundNonRunningModesIgnoreForwardedArgs` | mode-flag completeness (1) · per derived mode flag: refused iff `--currency` (3) · `--derive` spawns exactly the typecheck gate (1) · `--verify-registry` spawns nothing, exit ≠ 2 (1) | KNOWN BOUND #503 D-1 |
| `TestKnownBoundMaxprocessesOnlyLowersTheCount` | 4 cases × {joined, separate}: not refused, reaches the spawn, xdist starts min(X, Y) and never more than X (8) | KNOWN BOUND #503 maxprocesses |

Design, in brief:
- **D-2 is generated, not listed.**
  - `_exit_two_handlers(cli)` AST-derives `{caught exception: stderr label}` from each CLI's `main`. The source is the `except` handlers that `print(f"LABEL: …")`.
  - The forbidden families are every other handler across BOTH CLIs. Today that is `MANIFEST ERROR`, `REGISTRY ERROR`, `BROKEN INSTRUMENT`, `CONFIG ERROR`, and the types `ManifestError`, `RegistryError`, `BrokenInstrumentError`.
  - A non-vacuity pin requires the derived set ⊇ the two ruled labels plus `ManifestError`, and requires each CLI to have a `REFUSED ARGUMENT` handler for the typed error.
  - Positive leg: `REFUSED ARGUMENT:` ∈ stderr. Production does not expose the label; both mains spell it inline. **So the contract carries the literal** `REFUSED_ARGUMENT_LABEL = "REFUSED ARGUMENT"` (F2).
- **D-1 is generated over the gate CLI's store_true mode flags**, derived from `_build_parser()._actions`. A completeness pin forces a new mode to be classified as refusing or as a pinned miss.
  - Failure message: `this is a KNOWN BOUND (#503 D-1) — if you closed it deliberately, delete this pin and say so`.
  - The re-open trigger is in the comment: *either mode starts running the pytest gate*. A mode that starts APPLYING the args also reddens, through the "not applied" assertion.
- **maxprocesses**, both halves:
  - Half 1: the helper does not flag it, `_run_selected_gates` spawns, and the tokens arrive contiguous.
  - Half 2: the xdist worker count from the captured argv equals the hand-computed `min(X, Y)` and is ≤ X.
  - The live branch is X = 12. The alone branch is `auto`, pinned hermetically to 64 through xdist's own `PYTEST_XDIST_AUTO_NUM_WORKERS` env var (64 is this box's core count, CLAUDE.md).
  - Y values: 2 and 8 lower the count; 64 and 128 are above the policy and must not raise it.
  - Failure-message shape is `(#503 maxprocesses)`. Re-open trigger in the comment: *xdist makes --maxprocesses able to RAISE the worker count*.

## 2. Kill proofs (`scripts/mutation_proof.py`, in a `./scripts/scratch_copy.sh` copy)
- **Provenance receipt:**
  - `loremaster.__file__ = /var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f2573939-49db-41c6-9c9f-064ec53acfa0/scratchpad/sc503d2/loremaster/loremaster/__init__.py`
  - `pending_contract_gate.__file__ = …/scratchpad/sc503d2/scripts/pending_contract_gate.py`
  - scratch_copy exit 0.
  - `cmp` against the real tree: the test file, `pending_contract_gate.py` and `wave_gate.py` were byte-identical before the runs.
  - Unmutated baseline in the copy: `105 passed`.
- **Declared sets:** awk over `pytest --collect-only` (105 ids), written and hashed BEFORE each run.

| mutation (in `scripts/pending_contract_gate.py`) | declared (sha256, time) | observed | verdict |
|---|---|---|---|
| **B** = refactor-503-d1 §2b: `raise ForwardedWorkerCountError(` → `raise ManifestError(` | 15 = 6 leg-runner + 6 gate-CLI + 2 wave-CLI label rows + D-1 `[--currency]` (`374a2ad0…`, 19:40:47) | `15 failed, 90 passed` | **PROOF HELD, EXACT** |
| **C** subclass door: `class ForwardedWorkerCountError(ValueError)` → `(ManifestError)`. Both CLIs catch the typed error first, so stderr stays correct and only the isinstance leg can see it | 6 leg-runner rows (`107292e9…`, 19:41:21) | `6 failed, 99 passed` | **PROOF HELD, EXACT** |
| **D1-closed**: `_refuse_forwarded_worker_counts(arguments.pytest_args)` inserted before `if arguments.derive:` in `_dispatch` | 4 = `[--derive]`, `[--verify-registry]`, derive-spawns, verify-registry (`f09800d6…`, 19:42:20) | `4 failed, 101 passed` | **PROOF HELD, EXACT** |
| **MP-closed**: the refusal also raises on any `--maxprocesses…` token | all 8 maxprocesses rows (`87b25458…`, 19:42:20) | `8 failed, 97 passed` | **PROOF HELD, EXACT** |

- Every run was restored byte-exact (md5 `4651686a…`) and `cmp`'d equal to the real tree afterwards.
- Under B, the served text was `MANIFEST ERROR: the forwarded pytest args ['-n', 'auto'] car…` and `CONFIG ERROR: the forwarded pytest args ['-n12'] carry an xd…`. Those are exactly the mislabels the new rows reject.
- ⚠ **Self-caught hazard:** I re-ran the B driver once more with `| head -4` to capture its provenance lines. A SIGPIPE could have killed `mutation_proof` between the mutation and the restore. I checked afterwards: no `mutation_proof` process was alive, and the scratch `pending_contract_gate.py` `cmp`'d equal to the real tree. The real tree was never at risk, because every mutation was scratch-only.
- **Why the oracle discriminates in both directions (maxprocesses):** the lowering rows (2, 8) show it does not just return the policy count. The no-raise rows (12, 64) show it does not just return the cap.

Driver, verbatim (`…/scratchpad/drive_d2.sh`). C, D1 and MP used the same `mutation_proof.py` call with `--anchor[-file]`/`--replacement[-file]` as tabled above.
```bash
#!/usr/bin/env bash
# REPORT-contract-503-d2 §Kill proof: the REPORT-refactor-503-d1.md §2b survivor B (the typed refusal raised as
# ManifestError), run with scripts/mutation_proof.py in a scratch_copy.sh copy against a declared RED set.
set -u
SP=/var/tmp/claude-1000/-home-ejprice-PycharmProjects-lore/f2573939-49db-41c6-9c9f-064ec53acfa0/scratchpad
SC=$SP/sc503d2
cd "$SC" || exit 99
uv run python -c 'import loremaster; print("loremaster.__file__ =", loremaster.__file__)'
(cd scripts && uv run python -c 'import pending_contract_gate as p; print("pending_contract_gate.__file__ =", p.__file__)')
TEST=(uv run pytest -q -p no:cacheprovider --tb=line -rfE -n 12 scripts/test_pytest_workers_503.py)
echo "--- baseline (unmutated copy):"; "${TEST[@]}" | tail -1
EXPECT=(); while read -r id; do EXPECT+=(--expect-red "$id"); done < "$SP/declared_B_d2.txt"
uv run python scripts/mutation_proof.py --file scripts/pending_contract_gate.py \
  --anchor '        raise ForwardedWorkerCountError(' --replacement '        raise ManifestError(' \
  "${EXPECT[@]}" -- bash -c "${TEST[*]}; echo '--- served labels under B:'; uv run python scripts/pending_contract_gate.py -- -n auto 2>&1 | cut -c1-60; uv run python scripts/wave_gate.py --wave=-n12 2>&1 | cut -c1-60"
rc=$?
cmp scripts/pending_contract_gate.py /home/ejprice/PycharmProjects/lore/scripts/pending_contract_gate.py && echo "scratch pcg == real tree (byte-exact, restored)"
echo "mutation_proof exit=$rc"
```
Mutation replacement for D1-closed: `    _refuse_forwarded_worker_counts(arguments.pytest_args)\n    if arguments.derive:\n`. For MP-closed, after `    hardcoded = _hardcoded_worker_counts(pytest_args)\n`: `    if any(str(a).startswith("--maxprocesses") for a in pytest_args):\n        raise ForwardedWorkerCountError("maxprocesses refused")\n`.

## 3. Gate tails (2026-09-26, real tree, after the last edit)
```
$ uv run pytest -q -p no:cacheprovider --tb=line -n 12 scripts/test_pytest_workers_503.py
105 passed in 3.53s                                   (exit=0)
$ uv run pytest -q -p no:cacheprovider --tb=line -n 12 <the 8 files>
305 passed, 24 warnings in 37.23s                     (exit=0)   = 276 prior + 29 new
$ uv run ruff check scripts/test_pytest_workers_503.py        → All checks passed!
$ uv run ruff format --check scripts/test_pytest_workers_503.py → 1 file already formatted
$ MYPYPATH=scripts uv run mypy scripts/test_pytest_workers_503.py → Success: no issues found in 1 source file
$ ./scripts/typecheck.sh → loremaster 53 + scripts 1 (test_forgery_door_sweep.py, pre-existing) = 54; 0 in the touched file
```
My first mypy run showed 3 errors, all mine: xdist has no stubs, which made one `type: ignore` unused. I fixed them with `# type: ignore[import-untyped]` on the local `import xdist.plugin` and removed the unused ignore. All the gates above ran after that fix.

## 4. Adversarial pre-flight → covering case
| # | Failure | Covered by |
|---|---|---|
| 1 | Refusal raised as `ManifestError` (§2b) | leg-runner type rows + CLI label rows (proof B) |
| 2 | Typed error subclasses a manifest/config family (stderr correct, type wrong) | `not isinstance(other exit-2 families)` (proof C) |
| 3 | Label right on one CLI, wrong on the other | both CLIs driven; forbidden labels are the union across both |
| 4 | A new exit-2 family added later (e.g. a new `FOO ERROR`) and used for the refusal | derived handler sweep, no hand-list |
| 5 | Derivation goes vacuous (the handler shape changes) | non-vacuity pin: ⊇ the ruled labels + ManifestError, and a REFUSED ARGUMENT handler per CLI |
| 6 | A new gate-CLI mode added that silently drops args | mode-flag completeness pin |
| 7 | D-1 closed by refusing, or "fixed" by applying the args | refused ⇒ red; forwarded run found in a spawn ⇒ red (proof D1) |
| 8 | `--maxprocesses` spellings: joined and separate | both parametrized |
| 9 | maxprocesses raising above the policy (xdist semantics change) | `workers <= policy` + exact min, via xdist's own hook |
| 10 | `auto` resolution being host-dependent | pinned via xdist's env var, so hermetic |
| 11 | maxprocesses refused (the bound closed) | pytest.fail with the bound message (proof MP) |
| 12 | Hostile rendered text | scoped out: nothing renders stored free text |
| 13 | `-p no:xdist`, `-o addopts`, `PYTEST_ADDOPTS` siblings | **not tried**; still open from contract-503-d1 §Noticed 3 |

## 5. Realism & independence
- ☑ **Inputs:** the real forwarded spellings and selectors (the existing rows are reused), real X (12 / auto), and Y on both sides of X.
- ☑ **Independent expected values:** the min(X, Y) table is hand-computed from the lead's rule and matches refactor-503-d1 §2d's subprocess probe. The count is produced by xdist's own code, not by the gate's.
- ☑ **Seam:** CLI argv → argparse → `_dispatch` / `_run_selected_gates` → Popen argv → xdist's parser and hook.
- ☐ **Magnitude bound:** partly applicable. The maxprocesses count carries `≤ policy` as its sanity bound. Everything else is a label or type, i.e. pure logic.
- ☑ **Shared conventions:** policy values come from the `RULED_*` constants, and the mode set is derived from the production parser. The refusal label is a literal, because production exposes no constant (F2).
- ☐ **Hostile fixtures:** not applicable; no stored text is rendered.
- ☐ **Input accounting:** not applicable to the new pins. Token fates were already covered by d1.

## Forks
- **F1 — "reuse the existing xdist-parser oracle helper, not a new one".**
  - Reading A (taken): reuse `_xdist_option_parser` as the parser, and add a thin adapter that hands the parsed namespace to xdist's own `pytest_cmdline_main`. The `--maxprocesses` cap lives in that hook, not in the parser, so the parser alone cannot observe the cap. Writing `min()` in the test would make the oracle re-implement the rule being pinned.
  - Reading B: no new function at all. Parse with `_xdist_resolved_workers` and apply `min()` in the test.
  - B is weaker: it pins the lead's rule against itself and never checks xdist. I picked A. If B is ruled, delete `_xdist_worker_processes` and compute `min` inline.
- **F2 — the refusal label is a literal in both CLIs.** refactor-503-d1 R2 said to promote it to a constant if a pin wants it read from production. I did not touch production, per the writable set. If it is promoted, swap `REFUSED_ARGUMENT_LABEL` to read that constant.
- **F3 — overlap.** The D-1 sweep's `[--currency]` row also checks the refusal label, so it fired under B, alongside the 14 dedicated rows. This is harmless, and I declared it in B's set. It is a second witness, not a duplicate pin.

## DRY ledger
| new symbol | lore query run | returned | disposition |
|---|---|---|---|
| `_exit_two_handlers`, `_other_exit_two_families` | `lore_search("test helper that derives stderr labels or caught exception types from a CLI main's except handlers via AST")` | completed after the draft: top hit is `lorerunes/tests/test_engine_rejection.py` `test_an_error_outside_the_catch_set_propagates_unchanged`, an unrelated catch-set pin with no handler-derivation helper. `scripts/` is not in the graph (#507). awk over `scripts/test_*.py` for `ExceptHandler`: no helper found | HAND-ROLLED |
| `_gate_cli_mode_flags` | same awk; `test_pending_contract_gate.py` drives modes by literal argv | none | HAND-ROLLED (4 lines) |
| `_xdist_worker_processes` | `lore_search("compute pytest-xdist worker process count including --maxprocesses cap from an argv in tests")` | only REPORT-refactor-503.md prose (subprocess probe) | EXTENDED over REUSED `_xdist_option_parser`; the cap itself is xdist's `pytest_cmdline_main` (F1) |
| `REFUSED_ARGUMENT_LABEL`, `RULED_OUT_LABELS`, `KNOWN_BOUND_*_MESSAGE`, `*_MODE_FLAGS`, `_MAXPROCESSES_CASES`, … | — | contract constants | new named constants (no magic literals in assertions) |
| (reused) `_record_popen`, `_stub_detector`, `_cli_outcome`, `_contiguous_run_start`, `_shipped_worker_sized_gates`, `_REFUSED_FORWARDED_SPELLINGS`, `_REFUSED_SINGLE_TOKEN_SPELLINGS`, `_LIVE/_ALONE` | — | this file | REUSED |

## Noticed (surfaced, not dropped)
1. **Bound on the D-2 derivation.** It recognises a handler only in the shape `print(f"LABEL: …", …)`. A handler that reports some other way (logging, a helper call) would not join the forbidden set. The non-vacuity pin catches the derivation going empty for the ruled labels, but not for a future third family written in another shape. That is LOW, and it is stated here so the next reader meets it deliberately.
2. `_xdist_worker_processes` repeats the two-line "find the pytest token" lookup from `_xdist_resolved_workers`. That is trivia, not policy. I left the existing helper unedited, per "never edit existing pins/helpers".
3. `-p no:xdist`, `-o addopts=…` and `PYTEST_ADDOPTS` remain untried siblings of the worker-count class (from contract-503-d1 §Noticed 3). They are not pinned either way.
4. The refactor-503-d1 open items T2 (the completeness pin's reach is name-keyed) and P6 (the F8 trigger #2 is unmeasured) are untouched by this delta and still open.

## Unrelated failures
`./scripts/typecheck.sh`: 54 mypy errors, all outside this cycle's files (§3). No test failed in any scoped run.
