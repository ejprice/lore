# REPORT-builder-03b-1-wave5 — two can-kicks discharged

brief-base v6 read

## SUMMARY BLOCK

- **state:** BOTH ITEMS DONE. `cad340f` (#196's instrument) · `a65ccca` (R4 rename) · this report.
- **gates (fingerprint diff EMPTY):** full suite **6611 passed / 0 failed** / 17 skipped / 3 xfailed —
  **identical either side of the rename**, so nothing was dropped from collection · `scripts/`
  **326 passed** (was 315; +11 new) · typecheck **0, all three members** · ruff clean · skill **117**
- **the instrument is dogfooded:** three self-mutations against its own suite, expected-RED declared
  first, all three **PROOF HELD**.
- **⚠ two NEW findings, both caught BY the tool, IN the tool, within minutes of it existing** — §1.3.
  One of them is #194's own mechanism at the shell level, and it bit me on the first live run.
- **deviations:** X1 sandbox is not a `git init` repo (reasoned, §1.4) · X2 six of eleven contract
  tests were VACUOUSLY green in the RED phase (§1.5)
- **decisions needed:** none. One observation for the close-out (§2.3: a rename breaks a symbol
  citation exactly as an edit breaks a line citation).

---

## 1 — ITEM 1: `scripts/mutation_proof.py`, the #196 instrument

### 1.1 What it enforces

| requirement | how |
|---|---|
| expected-RED set declared **BEFORE** the run | `--expect-red NODEID`, repeatable, **required** — argparse refuses a proof without one |
| diff **both ways** | `observed != declared` → a report naming *unexpected reds* AND *declared reds that stayed GREEN*, separately |
| one failing unit | every failure path returns a distinct non-zero exit (3 anchor · 4 mismatch · 5 restore · 6 unparseable) |
| anchor landed | `count != 1` aborts **before touching the file**; 0 is #194 verbatim, >1 is an ambiguous site |
| receipt | `mutation LANDED (anchor matched exactly once)` — printed only when it actually did |
| restore from **content** | `shutil.copy2` to a temp dir before mutating, restored in a `finally`, md5-verified after; a mismatch is its own loud exit code |

**The direction that matters is the second one.** `set -e` guards *setup*. A mutation that lands and
reddens the **wrong** test prints `1 failed` — byte-identical to a successful proof. Both times that
happened, what caught it was me knowing which test *should* redden and noticing the count did not
match. That is now mechanical, and it is the only reason this tool is worth more than the rule.

The third leg — **declared red stayed GREEN** — catches a mutation that applies cleanly into code no
test exercises. It lands, it is real, every gate passes, and a one-directional check calls it a proof
while the pin has never been shown to fail at all.

### 1.2 Dogfood: three self-mutations, expected-RED declared first

| # | mutation to `mutation_proof.py` | declared RED | result |
|---|---|---|---|
| **MP-1** | `if observed != declared:` → `if observed - declared:` (make the diff one-way) | `…::test_a_mutation_landing_in_UNREACHED_code_FAILS` | **PROOF HELD** — exactly that one |
| **MP-2** | `if matches != 1:` → `if matches > 1:` (accept a 0-match anchor) | `…::test_a_non_unity_anchor…[zero-matches]` | **PROOF HELD** (after §1.3a) |
| **MP-3** | `.split(" - ", 1)` → `.rsplit(" - ", 1)` | `…::test_a_failure_MESSAGE_containing_a_dash_separator…` | **PROOF HELD** |

Each printed `tree restored byte-exact`. MP-1 is the strongest: **it proves the two-way diff by
deleting one direction of it** and shows exactly one test notices.

### 1.3 ⚠ TWO FINDINGS THE DOGFOOD CAUGHT — IN THE TOOL, BY THE TOOL

**(a) pytest ASCII-ESCAPES non-ASCII in parametrised node ids.** MP-2's declared id was transcribed
from my own source, which had an em-dash in a parameter string. pytest emits `…[zero matches —
the #194 shape]`. The id could **never** match, so a perfectly correct mutation reported a two-way
mismatch. Fixed twice over: explicit ASCII `pytest.param(id=…)` in my fixture, and a `--help` BOUND
telling callers to take ids from `pytest --collect-only -q`. **Collecting is not peeking** — it names
tests without running them, so the declared set is still fixed before any result exists.

**(b) ⚠ PIPING THE HELPER INTO `tail` DISCARDS ITS EXIT STATUS — #194'S OWN MECHANISM, ONE LEVEL UP,
AND IT BIT ME ON THE FIRST LIVE RUN.** I ran MP-2 as `./mutation_proof.py … | tail -6` under `set -e`.
The pipe's status is `tail`'s, so the helper's exit-4 was thrown away and `set -e` did not fire. **I
noticed only because `PROOF HELD` was absent from the output** — i.e. by reading the words, which is
exactly the manual vigilance this tool exists to replace.

That is worth more than the code: **I built the instrument for #194 and was defeated by #194 while
testing it.** The forbidden set is unbounded — you cannot enumerate every shell construct that eats
an exit code. Now in `--help`: *pipe only where a human reads the words, never where a shell decides.*
All three proofs above were re-run unpiped, with `echo "helper exit=$?"` as the receipt.

### 1.4 Deviation X1 — the sandbox is not a `git init` repo

The brief said a throwaway `git init` repo. My fixtures use a plain `tmp_path` directory. **The
essential requirement — never this checkout — is met and stated in the module docstring.** The
helper never consults git: it backs up and restores by **content**, which is strictly stronger than
any git check and works on an uncommitted tree (where these proofs actually run). A git repo in
these fixtures would be **scenery**, and scenery in a fixture is how a reader concludes a check
exists that does not. Say the word if you want it anyway.

### 1.5 Deviation X2 — six of eleven were vacuously green at RED

Honest accounting of the TDD phase: with no `mutation_proof.py` on disk, the first run was
**5 failed / 6 passed**. The six "passing" tests were the ones asserting `returncode != 0` or *file
unchanged* — trivially true against a missing script. **They were not evidence of anything.** What
made the suite meaningful was that the *positive control* (`…reddening_EXACTLY_the_declared_set_
PASSES`) was among the five genuine reds. A suite of only negative assertions would have been green
at RED and green at GREEN, and would have measured nothing — the same defect the tool is built to
catch, in the tool's own contract.

---

## 2 — ITEM 2: R4, the class whose NAME asserted a boundary three columns cross

`TestParamsHashIsTheRuledRecipeAndLeaksNothing`
→ **`TestParamsHashIsTheRuledRecipeAndCarriesFreeTextOnlyAsADigest`**

The docstring has told the truth since wave 3; the name went on lying, **and the name is what a
reader greps**. An agent asking whether the trace row leaks its arguments found a class asserting it
does not. The new name states what the five pins actually assert — free text reaches the row only as
the digest — without claiming anything about `agent`/`session`/`action`, which are plaintext by
design so packet 06 can group by them.

**Receipts:** 5 tests collect under the new name (5 before). Full suite **6611 / 0 failed on both
sides of the rename** — a rename that silently drops a class from collection is the failure mode
here, and an unchanged total is what rules it out.

### 2.1 Residual sweep — bare, anchor-free grep, every hit adjudicated

`grep -rn "LeaksNothing\|leaks nothing"` across the whole tree, no path filter. **Nine hits, nine
verdicts** — no wholesale classification:

| # | file:line | verdict |
|---|---|---|
| 1 | `loremaster/tests/test_trace_telemetry.py:2470` | **KEEP — deliberate.** The provenance note naming the retired name. §2.3 is why. |
| 2 | `REPORT-coldaudit-03b-1.md:204` | **KEEP UNCHANGED** — an audit's own finding text. Editing it falsifies the receipt. |
| 3 | `REPORT-coldaudit-03b-2.md:440` | **KEEP UNCHANGED** — same. |
| 4 | `REPORT-coldaudit-03b-2.md:447` | **KEEP UNCHANGED** — same; this is the hit that raised R4. |
| 5 | `REPORT-builder-03b-1-wave3.md:87` | **KEEP** — my wave-3 C3c row, true as of that wave. |
| 6 | `REPORT-builder-03b-1-wave3.md:90` | **KEEP** — same. |
| 7 | `REPORT-builder-03b-1-wave3.md:269` | **KEEP, now DISCHARGED** — the R4 deferral row itself. Discharge recorded here. |
| 8 | `docs/plans/v2/receipts/2026-07-24-packet03b/REPORT-contract-telemetry-03b-r2.md:95` | **KEEP** — archived receipt, byte-faithful by law, ruff-excluded. |
| 9 | `…/REPORT-contract-telemetry-03b-r2-wave2.md:263` | **KEEP** — same. |

### 2.2 The test tree was checked for assertions pinning the old name

Per the rename law (*a suite can be green BECAUSE it still asserts the corpse*): grepped
`loremaster/` for `ParamsHashIsTheRuled` — the only hit is the class statement itself. No structural
pin enumerates test-class names, so nothing certified the retired name.

### 2.3 ⚠ ONE OBSERVATION FOR THE CLOSE-OUT — not a request

The archiving law prefers **symbol** citations over **line** citations because symbols survive edits.
**A rename breaks a symbol citation exactly as an edit breaks a line citation** — hits 8 and 9 are
archived receipts citing a symbol that, as of `a65ccca`, no longer exists.

That is why residual 1 is KEEP and not tidied away: the retired name survives **once**, in a
provenance note, so `grep LeaksNothing` still lands on the class. **That breadcrumb is the mitigation
the law does not currently name.** Cheap, and it makes a rename non-destructive to prior citations.
Your call whether it is worth a line in the close-out; I am not proposing an edit to CLAUDE.md.

---

## 3 — Gates

```
BEFORE / AFTER   HEAD=e6653d4  STATUS_LINES=4  TRACKED_TREE_MD5 identical
                 diff EMPTY — the tree held across every run

ruff        All checks passed!
typecheck   lorescribe OK (27) · loresigil OK (32) · loremaster OK (149) — 0 errors
suite       6611 passed, 17 skipped, 3 xfailed, 1 warning in 189.27s
scripts/    326 passed in 6.04s      (315 before; +11 for mutation_proof)
skill       117 passed
```

⚠ **`scripts/` IS NOT IN `testpaths`** (`lorescribe/tests`, `loresigil/tests`, `loremaster/tests`), so
`scripts/test_mutation_proof.py` and `scripts/test_tree_fingerprint.py` are **NOT in the 6611** and do
not run in the standard gate. Both helpers are lead/agent tooling rather than shipped code, so that
may be correct — but it means **these two instruments are only as green as someone remembering to run
`pytest scripts/`**, which is the same shape as the law we just instrumented. Flagging, not fixing:
adding a fourth testpath changes every agent's gate cost and is a decision, not a fix.

No concurrency re-run — I touched neither the seam nor the schema, as briefed.

---

## 4 — What I did not touch

- **`docs/eval/deploy-baseline-latency.json`** — untracked, not mine, present throughout. Left alone;
  both commits used `git commit --only` with explicit paths, never a bare `git commit`.
- **The archived receipts and the sibling reports** — §2.1 hits 2–9. Records of what was true when
  written.
- **The five pins inside the renamed class** — not one assertion changed. Strengthen-only, as briefed.
- **#195, #190, #183, DD-2.a, DD-4.c, #214, #193** — owned elsewhere with named decision points, per
  your list.

---

## 5 — ADDENDUM: `scripts` added to `testpaths` (lead-ruled after the report above)

The §3 flag was ruled ADD IT. One line in `pyproject.toml`, with the reasoning beside it so the
next reader does not have to reconstruct why a tooling directory is gated like shipped code.

```
full suite BEFORE   6611 passed, 17 skipped, 3 xfailed   in 189.27s
full suite AFTER    6937 passed, 17 skipped, 3 xfailed   in 197.77s
                    ^ 6611 + 326 exactly — collection independently confirms 6957 = 6631 + 326
ruff                All checks passed!
skill               117 passed — unaffected, as expected: it passes explicit path
                    arguments, and testpaths applies only when none are given
```

**Cost, measured rather than asserted: +8.5s on a 189s gate (+4.5%).** That does not change the
gate's character, so the ruling's assumption holds and there was nothing to stop for. Nothing in
`scripts/` failed.

⚠ **The fingerprint diff for this step is NOT empty, and that is correct.** `pyproject.toml` moved —
it is my own one-line edit, made between the BEFORE and AFTER captures. HEAD was stable at `e4ccb7e`
throughout and no sibling movement appeared. Claiming an empty diff here would require capturing
around the RUN rather than around the CHANGE, which would be a different (and weaker) receipt.

**Scope held:** this adds the **pytest** gate only. `scripts/` remains outside
`scripts/typecheck.sh`, where #188 measured 41 mypy errors — a separate work item, not conflated
here, and noted in the config comment so the omission reads as deliberate rather than forgotten.

---

*Measured 2026-07-25 on branch `feat/surreal-unification`; §1–4 at HEAD `e6653d4` with an empty
fingerprint diff, committed as `cad340f` and `a65ccca`; §5 at HEAD `e4ccb7e`.*
