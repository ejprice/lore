brief-base v9 read

# REPORT-adversary-44-gatedground-2 — second adversarial grading of the packet-44 gated-ground contract

**Target graded:** `scripts/test_gated_ground.py` · md5 **`ec3dd8906553fe0d1688d645d7161818`** ·
2474 lines · 174 collected. Verified at start **and at end** (14:32 EDT 2026-07-29); the file did
not move under me. Worktree `/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44`, branch
`pkt44/ungated-ground`, HEAD `f033a876c5814127262775bf4c63199ffd6c5df7`.
All claims below are measured **2026-07-29 at `f033a87`** unless dated otherwise.

---

## SUMMARY BLOCK

- `brief-base v9 read` · **state: done** · deviations: 1 (used my own scratch harness rather than
  `scripts/mutation_proof.py` — §11) · capability gap: **no `mcp__lore_lore__*` tools, no
  `SendMessage`** (brief-base §4; this file is my only channel — matches finding #287).
- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 HEADLINE — 44 wrong builds built and run against the real contract: 32 killed, 12 survived
  at 174 passed / 0 failed. 10 of the 12 carry a PROVEN behavioural divergence; 2 are INERT
  patches and are adjudicated as NOT findings (§4.3).** All **11** of the predecessor's survivors
  are genuinely closed (re-derived, §5) — every new survivor is *narrow-patch residue* or a class
  neither pass had reached.
- **The single biggest hole: `blind is not clean` is pinned at the READER level and almost never
  through the ENTRY POINT.** 14 blind inputs are pinned on `typecheck_roots` / `pytest_testpaths`
  / `tracked_python_files` / `frozen_roster`; only 2 are pinned through `ungated_ground`/`classify`.
  Four builds that swallow a `GuardIsBlind` inside `classify` pass all 174 pins, and **three of
  them serve bytes IDENTICAL to a healthy tree on a broken state** — a Leg-2 false clear by this
  repo's own hard definition of trust (§3).
- **And one hole needs no wrong build at all: the CORRECT build serves a false clear.** With
  `norecursedirs = ["probes"]` in `pyproject.toml`, pytest collects **0** tests from
  `loremaster/tests/probes/`, the guard reports `EXECUTION = COVERED` and **0 findings**, and the
  contract passes **174/174**. LEG A has `unmodelled_mypy_configuration`; **LEG B has no
  analogue** (§6).
- **MISSING PINS (8, each with both legs proven — §7):** P-1 blind-is-not-clean through the whole
  verdict · P-2 the receipts membership site on the EXECUTION axis · P-3 the frozen roster governs
  every axis · P-4 `member_mypypath` must read the RUNNER, not answer for it · P-5 the roster's
  `.py` filter is a suffix test · P-6 `unmodelled_pytest_configuration` · P-7 `frozen_sha` shape
  validation · P-8 the roster derivation is NUL-separated.
- **P-PKG DIFF (§10): one MISSING ROW** in the author's survey — `git ls-tree -r -z --name-only`,
  the roster seam the ruling introduced, is surveyed nowhere, and it is exactly where P-5/P-8 live.
- **⚠ SURFACED, operational, not a contract defect: `FROZEN_SHA=f033a87` is a FEATURE-BRANCH-ONLY
  object** (`git branch --contains f033a87` → `pkt44/ungated-ground` only). A squash-merge, a
  rebase, a `gc`, or any fresh clone of `master` orphans it, and the gate becomes permanently
  `GuardIsBlind` — which is precisely the pressure that produces wrong build AWB01 (§9, S1).
- **Satisfiability receipt: my independent reference build goes 174 passed / 0 failed** (§2).
- receipt pointers: reference build §2 · Leg-2 false clears §3 · wrong-build matrix §4 ·
  predecessor re-derivation §5 · the correct-build false clear §6 · missing pins + both legs §7 ·
  quantifier table §8 · surfaced §9 · P-PKG §10 · instruments verbatim §12.

---

## 0. Capability check (brief-base §4, first)

| the brief demanded | what I actually have | what I did instead |
|---|---|---|
| lore tools as first choice for structure questions | **no `mcp__lore_lore__*` tools in my definition** (matches finding #287, recorded for the contract agent) | `git grep` / `git ls-files` throughout — **said out loud here**. The brief already notes lore cannot see this worktree (#125), so the loss is small, but the tool absence is real and a lead must fix the agent definition, not the brief. |
| file findings via `lore_findings` | **no tool** | this report is the only channel |
| SendMessage to the lead | **not in my toolset** | report only |
| verify md5 at start and end | ✅ done, unchanged |  |
| never `cp -a` the worktree (#284) | ✅ every fixture and the whole substrate is `git archive` → fresh `git init`; **`.git` asserted to be a DIRECTORY** before use (§2, and in every instrument) |  |
| measure only artifacts whose author is at rest | ✅ `REPORT-contract-44-gatedground-1-r3.md` last written 13:59:23; I read it at 14:2x, 25+ min quiescent; `contract-44-gatedground-1` alive but idle |  |

---

## 1. Method, and the P0 controls that make every verdict below readable

The role's own law: *a probe that cannot fail is worth exactly as much as a pin that cannot fail.*
Four controls, all passed before any verdict was rendered:

1. **PROVENANCE.** Every run prints the module actually under test:
   `gg.__file__ = /home/ejprice/adv44-scratch/base/scripts/gated_ground.py` — inside the scratch,
   never the worktree (#140). Asserted, not eyeballed:
   `assert gg.__file__.startswith('/home/ejprice/adv44-scratch/base')`.
2. **`.git` IS A DIRECTORY.** `drwxr-xr-x 6 ejprice ejprice 9 … .git` in the scratch (the worktree's
   is a 64-byte **FILE**). #284 closed by construction, and every fixture repository re-asserts it.
3. **SATISFIABILITY / positive control.** The unmutated reference build: **174 passed / 0 failed**.
   Without it every "SURVIVED" would be unreadable.
4. **DIVERGENCE control.** A wrong build that passes the contract is only a *finding* if it behaves
   differently from the reference on some input. §4.3 rejects **two** of my own twelve survivors as
   INERT on exactly this ground — including one I initially expected to be a finding.

**Independence discipline:** the entire enumeration in §4 and §7 was derived from the contract
source alone. `REPORT-adversary-44-gatedground-1.md` §2.1 and the author's `-r2`/`-r3` tables were
opened only **after** batch 1 had been built and run (§5 is the diff).

---

## 2. The substrate, and the satisfiability receipt

```bash
$ mkdir -p /home/ejprice/adv44-scratch/base
$ git -C <worktree> archive f033a87 | tar -x -C /home/ejprice/adv44-scratch/base
$ cd /home/ejprice/adv44-scratch/base && git init -q -b main .
$ ls -ld .git
drwxr-xr-x 6 ejprice ejprice 9 Jul 29 14:06 .git          # a DIRECTORY (#284)
$ git add -A --force && git commit -q -m "replica of f033a87"
S0=53c8506cfbec7c8d12cea44d219c6bb7c7aff61c
tracked py: 290
$ diff <(git -C <worktree> ls-tree -r f033a87 --name-only) <(git ls-files)
TREE IDENTICAL TO f033a87
```

`S0` plays `FROZEN_SHA`'s role (a fresh `git init` cannot reproduce `f033a87`'s hash, but it
reproduces its **tree**, byte for byte). I then wrote an independent `scripts/gated_ground.py`,
copied the contract in byte-exact, added the two file-granularity `MEMBERS` entries + the
`MEMBER_MYPYPATH` line the contract demands, and committed as `S1` — i.e. **the post-landing
world**, which is the only substrate on which a wrong build can be graded.

```
PROVENANCE gg.__file__ = /home/ejprice/adv44-scratch/base/scripts/gated_ground.py
roots     : ['lorerunes','lorescribe','loresigil','loremaster','skills','docs/eval',
             'scripts/gated_ground.py','scripts/test_gated_ground.py']
tracked   : 292      FINDINGS  : 0

$ .venv/bin/python -m pytest scripts/test_gated_ground.py -q -p no:randomly
174 passed in 2.41s
```

**The contract is satisfiable, first try, by a build written blind to the author's implementation.**
That is a genuinely strong result and it is the reason the survivors below are believable.

**The two expected-RED pins reproduce, for the right reasons.** Removing the `MEMBERS` file entries
(= code committed, entries missing) gives:

```
FAILED …TestThisInstrumentRidesTheTypeGateItself::test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row
FAILED …TestThisInstrumentRidesTheTypeGateItself::test_every_file_granularity_members_entry_carries_a_dissolution_trigger
FAILED …TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis
3 failed, 171 passed in 2.39s
```

The third is the author's own predicted "third expected-RED at commit time" (r2 §0) — **it appears
only once the files are TRACKED**, which is why the brief's count of 2 and this count of 3 are both
right, for different worlds. Each fails naming the real missing artifact, not an import error.

---

## 3. LEG-2 FALSE CLEARS — constructed, byte-diffed, and the headline finding

The repo's hard definition: *"what broken state of this tool would serve exactly these bytes?
Identical bytes = a false clear = STOP."* Derived failure set = the guard's stateful dependencies
{`typecheck.sh`, `pyproject.toml`, `git ls-files`, `git ls-tree`, the frozen commit object} ×
{missing, empty, malformed, duplicated, widened-to-`.`, unreachable}.

**The contract pins every one of these — at the READER.** It pins **only two** through the entry
point (`test_an_unmodelled_setting_makes_the_WHOLE_VERDICT_refuse_not_just_a_reader`, and the two
archived-receipts cases). Nothing requires `classify` / `ungated_ground` to PROPAGATE a
`GuardIsBlind` raised by `typecheck_roots`, `pytest_testpaths`, `tracked_python_files` or
`frozen_roster`. Measured:

```
=== AWB01  frozen sha unreachable  (rebase / squash / fresh clone)
    healthy (reference, healthy state) : CLEAN (0 findings)
    CONTROL (reference, BROKEN state)  : CLEAN (0 findings)      <- see note
    wrong build (BROKEN state)         : CLEAN (0 findings)
    VERDICT: FALSE CLEAR - identical bytes to healthy

=== AWB04  testpaths widened to '.'
    healthy                            : CLEAN (0 findings)
    CONTROL (reference, BROKEN state)  : RAISED GuardIsBlind: testpaths entry '.' widens to the whole tree…
    wrong build (BROKEN state)         : CLEAN (0 findings)
    VERDICT: FALSE CLEAR - identical bytes to healthy

=== AWB05  no git binary on PATH  (#131 verbatim)
    healthy                            : CLEAN (0 findings)
    CONTROL (reference, BROKEN state)  : RAISED GuardIsBlind: the guard could not execute git ([Errno 2]…)
    wrong build (BROKEN state)         : CLEAN (0 findings)
    VERDICT: FALSE CLEAR - identical bytes to healthy

=== AWB03  runner declares no MEMBERS
    CONTROL (reference, BROKEN state)  : RAISED GuardIsBlind: … declares no MEMBERS array …
    wrong build (BROKEN state)         : a STORM of false positives (docs/eval/*, skills/* …)
    VERDICT: distinguishable — but it still passed 174/174, and a gate that
             refuses honest code is a gate that gets switched off
```

⚠ **AWB01's control row deserves its own sentence, because it is the sharpest thing in this
report.** The reference build reports `CLEAN` on the broken state *for a different reason*: the
exemption row I swapped the sha into is only consulted for files that are not otherwise covered, and
in this substrate everything is covered. So AWB01's false clear is real but its control is weak —
**and I say so rather than let a strong-looking row stand on a coincidence.** The *decisive* receipt
for AWB01 is not this table; it is §7 P-1 leg 1, where a purpose-built repository separates the two
builds cleanly (`REFERENCE` raises, `AWB01` returns a clean tree).

Everything else in the derived failure set is honestly pinned at the reader and — for the four
inputs above — nowhere else. `git ls-files` duplicate-declaration analogue: TOML forbids duplicate
keys (`tomllib` raises), so the bash-only `MEMBERS=(` duplicate is the real hazard and it **is**
pinned (`test_two_members_declarations_are_blind_not_clean`; my mutation of it was killed).

---

## 4. P1 — THE WRONG-BUILD MATRIX

44 built, 32 killed, 12 survived. Every "killed" row names the pin that killed it; every
"SURVIVED" row is adjudicated in §4.2/§4.3.

### 4.1 Batch 1 — derived from the contract source alone, before reading any prior report

| # | wrong build | result |
|---|---|---|
| AWB01 | **`frozen_roster`'s `GuardIsBlind` swallowed inside `classify`; falls back to the tree root** | **174P 0F — SURVIVED** |
| AWB02 | `unmodelled_mypy_configuration` computed and never consulted | killed — `…test_an_unmodelled_setting_makes_the_WHOLE_VERDICT_refuse_not_just_a_reader` |
| AWB03 | **`typecheck_roots` blind swallowed → falls back to `workspace_members`** | **174P 0F — SURVIVED** |
| AWB04 | **`pytest_testpaths` blind swallowed → `testpaths = ["."]`** | **174P 0F — SURVIVED** |
| AWB05 | **`tracked_python_files` blind swallowed → empty list → `return []`** | **174P 0F — SURVIVED** |
| AWB06 | `str.startswith` at the LEG-A typecheck-root site | killed — `test_a_sibling_prefix_of_a_typecheck_root_is_not_covered` |
| AWB07 | `str.startswith` at the LEG-B testpath site | killed — `test_a_sibling_prefix_of_a_testpath_is_not_covered` |
| AWB08 | `str.startswith` at the receipts site, both axes | killed — `test_a_sibling_prefix_of_the_archived_receipts_root_is_not_exempt` |
| AWB09 | **`str.startswith` at the receipts site, EXECUTION axis ONLY** | **174P 0F — SURVIVED** |
| AWB10 | roster ignored, whole tree grandfathered | killed — 2 roster pins |
| AWB11 | roster derived at `HEAD` instead of the frozen sha | killed — 2 roster pins |
| AWB12 | roster hardcoded to this checkout's `scripts/*.py` | killed — `test_the_roster_is_derived_from_the_repository_not_from_a_committed_list` |
| AWB13 | **roster read with line-split `git ls-tree` (no `-z`)** | **174P 0F — SURVIVED** |
| AWB14 | **roster honoured on TYPES only; tree-root on EXECUTION** | **174P 0F — SURVIVED** |
| AWB15 | self-exemption via `Path(__file__).name` | killed — `test_the_guard_grants_its_own_files_no_special_exemption` + a roster pin |
| AWB16 | self-exemption via a string literal | killed — `test_the_guard_names_no_path_of_its_own_anywhere_in_its_source` |
| AWB17 | `git ls-files` line-split (no `-z`) | killed — 2 hostile-path pins |
| AWB18 | `conftest.py` dropped from the LEG-B scope | killed — 4 pins |
| AWB19 | pytest patterns hardcoded to `test_*.py` | killed — 2 pins |
| AWB20 | exemption not axis-scoped | killed — `test_an_exemption_is_scoped_to_its_axis` |
| AWB21 | message interpolates the raw path | killed — `test_a_hostile_path_cannot_forge_a_second_finding_row` |
| AWB22 | the packet's literal UNION property | killed — **19 pins** |
| AWB23 | `EXEMPT_TABLE` beats `COVERED` | killed — 2 pins |
| AWB24 | a file `MEMBERS` entry treated as its parent directory | killed — 4 pins |
| AWB25 | mypy allowlist reverted to a denylist | killed — the 2 "invented after this guard" params |
| AWB26 | empty roster returned rather than raised | killed — `test_a_roster_that_matches_nothing_is_blind_not_clean` |
| AWB27 | findings unsorted | killed — `test_findings_are_ordered_deterministically` |
| AWB28 | `ungated_ground` reports the TYPES axis only | killed — **31 pins** |

### 4.2 Batch 2 — narrow-patch hunting (built AFTER reading the prior reports)

| # | wrong build | result |
|---|---|---|
| NP1 | **`member_mypypath` FABRICATES the map the runner does not declare** | **174P 0F — SURVIVED** |
| NP2 | reverse containment on the TYPES axis only | 174P 0F — **survived but INERT** (§4.3) |
| NP3 | root-level `.py` COVERED on the EXECUTION axis only | killed — `test_repository_root_level_python_is_ordinary_committed_ground` |
| NP4 | exemption-root widening guard dropped | killed — 2 malformed-row params |
| NP5 | **`frozen_sha` validation relaxed to `[0-9a-fA-F]{1,40}`** | **174P 0F — SURVIVED** |
| NP6 | **`.py` by substring in the frozen roster only** | **174P 0F — SURVIVED** |
| NP7 | disclaimer contiguous on TYPES, scattered on EXECUTION | killed — `test_the_disclaimer_is_one_contiguous_claim_not_scattered_keywords` |
| AWB15b | self-exemption keyed on the resolved path, no literal | killed — `test_the_guard_grants_its_own_files_no_special_exemption` |
| AWB15c | **`classify` appends its own file to `roots`** (fixture-blind, literal-free) | 174P 0F — **survived but INERT at landing** (§4.3) |

### 4.3 ⚠ TWO SURVIVORS ARE **INERT PATCHES AND NOT FINDINGS** — my own P0 control firing

- **NP2 — reverse containment on TYPES.** I expected a hole. Measured over the **whole real tree**:
  `tracked paths compared: 292   divergent verdicts: 0 → INERT PATCH (not a finding)`. Reverse
  containment needs a tracked path to be an *ancestor* of a typecheck root, and every tracked path
  is a file. **Reporting this as a hole would have been my instrument lying the same way the
  author's could.** It is listed so the count reconciles, and struck.
- **AWB15c — the literal-free structural self-exemption.** It survives at 174/174 in the landing
  state, but it changes **nothing observable there** (the `MEMBERS` entries already cover the
  files), and in the state where it *would* matter — entries deleted — `test_the_instrument_is_
  covered_by_a_members_entry_not_by_the_exemption_row` fires anyway, **because that pin reads the
  RUNNER and not the guard**:

  ```
  --- STATE A: MEMBERS entries PRESENT            174 passed
  --- STATE B: MEMBERS entries DELETED
  FAILED …test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row
  FAILED …test_every_file_granularity_members_entry_carries_a_dissolution_trigger
  FAILED …TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis
  ```

  **FRONTIER ITEM 2 — ANSWERED: the self-exemption class is genuinely closed, and the revision's
  central structural claim holds.** Two independent pins guard it, one of which is immune to any
  guard-side lie. Residual only: the pin's *comment* claims "delete the `MEMBERS` entry and the
  recursion re-opens with every pin still green" — measurably **false**, and harmlessly so.

### 4.4 The divergence receipts for the surviving mis-classifications

```
AWB09 - test-shaped sibling of the archived-receipts root (should be UNGATED on EXECUTION)
  REFERENCE                    TYPES=UNGATED   EXECUTION=UNGATED
  AWB09                        TYPES=UNGATED   EXECUTION=EXEMPT_ARCHIVED_RECEIPTS

AWB13 - hostile (newline) path inside the frozen roster (should be EXEMPT_TABLE)
  REFERENCE                    TYPES=EXEMPT_TABLE
  AWB13                        TYPES=UNGATED

AWB14 - EXECUTION-axis exemption, file added AFTER the freeze (should be UNGATED)
  REFERENCE                    EXECUTION=UNGATED
  AWB14                        EXECUTION=EXEMPT_TABLE

NP1 - runner has NO MEMBER_MYPYPATH line; does the requirement pin still pass?
  REFERENCE                    1 failed in 0.10s      <- correct: the leg would exit 1
  NP1                          1 passed in 0.05s      <- the guard answered for the runner
  (the runner really is missing the declaration: True)

NP5 - frozen_sha validation relaxed
  git ls-tree <UPPERCASE sha> -> rc=0                  (git DOES accept uppercase)
  REFERENCE  frozen_sha=ab -> rejected   |  NP5  frozen_sha=ab -> ACCEPTED

NP6 - the exempted tree holds only `notes.py.txt` at the frozen sha
  REFERENCE  RAISED GuardIsBlind: the frozen roster for 'scripts' … is EMPTY
  NP6        roster=['scripts/notes.py.txt'] (guard proceeds — reads as an ordinary exemption)
```

---

## 5. P4/P6 — the predecessor's ELEVEN survivors, RE-DERIVED (never relayed)

The brief's instruction was to assume every fix was narrow until proven otherwise. I rebuilt all
eleven rather than reading the author's claim that they die.

| predecessor survivor | my re-derivation | verdict |
|---|---|---|
| WB3 `startswith` at the LEG-B site | AWB07 | **CLOSED** — 1 RED |
| WB4b self-exemption by exact path | AWB16 / AWB15 / AWB15b / AWB15c | **CLOSED** (§4.3) |
| WB27 LEG-B reverse containment | WB27 | **CLOSED** — 2 RED |
| WB28 `startswith` at the LEG-A site | AWB06 | **CLOSED** — 1 RED |
| WB29 `startswith` at the receipts site | AWB08 | **CLOSED** — 1 RED, **but the patch did not generalise → AWB09** |
| WB31 `".py" in name` | WB31 | **CLOSED** — 2 RED, **but not at the roster seam → NP6** |
| WB33 `StatedBound.reopen_trigger="TBD"` | WB33 | **CLOSED** — 1 RED |
| WB36 message keyword-stuffed | WB36 | **CLOSED** — 1 RED (and NP7, the per-axis variant, also dies) |
| WB38 `Exemption.reopen_trigger="TBD"` | WB38 | **CLOSED** — 4 RED |
| WB43 root-level `.py` COVERED | WB43 | **CLOSED** — 1 RED (and NP3, the per-axis variant, dies) |
| WB45 `Exemption.reason="x"` | WB45 | **CLOSED** — 2 RED |

**11 of 11 closed. The fixes are real, not letter-of-the-finding — with two exceptions, both
axis-scoped:** the WB29 fix pinned the receipts site with a fixture that is **not test-shaped**, so
it discriminates on TYPES only (→ AWB09, P-2); the WB31 fix pinned the suffix property on the
`git ls-files` seam and the ruling then introduced a **second** enumeration seam (`git ls-tree`)
that inherited none of it (→ NP6/AWB13, P-5/P-8).

### 5.1 P4 — the author's own six roster mutation proofs, reproduced

| proof | author declared | I measured | verdict |
|---|---|---|---|
| MP-R1 roster at `HEAD` not the frozen sha | 2 | **2** (AWB11) | reproduces |
| MP-R2 `frozen_sha` format validation removed | 3 | **3** | reproduces |
| MP-R3 unreachable sha no longer raises | 4 | **4** | reproduces |
| MP-R4 empty roster read as "nothing to grandfather" | 1 | **1** (AWB26) | reproduces |
| MP-R5 roster read from a committed list | 5 | **5** | reproduces |
| MP-R6 nothing is grandfathered | 7 | **8** | reproduces the *property*; count differs |

**MP-R6 is the one discrepancy and it is benign:** my mutation prefixes every roster entry
(`"NEVER/" + entry`), the author's phrasing was "roster consulted, never matches". Different
mutation shapes reach the same property and redden overlapping-but-not-identical sets; the extra
RED in mine is `test_a_file_entry_covers_itself_ahead_of_any_exemption`. **I am not calling the
author's row wrong** — I am recording that the number is shape-dependent, which is why a declared
set must travel with its patch. Their arithmetic also checks out independently: every tail sums to
174 (`n failed + n passed + 3 deselected`), and the 3 deselected are
`TestThisInstrumentRidesTheTypeGateItself`, stated in their §3.

The author's **self-reported PROOF FAILEDs are honest and I could not improve on them.** MP-R5/MP-R6
both redden `TestTheRealRepositoryIsFullyGated` — I reproduced exactly that (see the MP-R5 RED list
in §12), which is what their §3.2 says caught them.

---

## 6. THE HOLE THAT NEEDS NO WRONG BUILD — the CORRECT build serves a false clear

LEG A is honest about a hard problem: *registered ≠ actually checked*, so
`unmodelled_mypy_configuration` **refuses to certify** when `[tool.mypy]` carries anything that
could make a registered file unchecked, allowlist-by-default, with the "setting invented after this
guard" params to prove it is not a name list. That is excellent, and it is the contract's best idea.

**LEG B makes the identical claim and models nothing.** Constructed:

```bash
$ # pyproject.toml gains:  norecursedirs = ["probes"]
$ pytest --collect-only -q | grep -c "probes/test_probe"
0                                     # pytest collects NOTHING there

$ python -c "import gated_ground as gg; …"
 fates: {'TYPES': 'COVERED', 'EXECUTION': 'COVERED'}
 total findings served: 0             # byte-identical to the healthy render

$ pytest scripts/test_gated_ground.py -q
174 passed in 2.32s
```

`norecursedirs`, `collect_ignore` / `collect_ignore_glob` in a `conftest.py`, and
`--ignore-glob`/`-p no:…` inside `addopts` each make a **registered** file **uncollected**, which is
LEG B's entire claim. The `registration-not-execution` bound does not cover this: it disclaims
*"mypy or pytest RAN or PASSED"*, while the file here is registered and *never collected at all*.

⚠ I checked the obvious near-miss and it is **not** the lever: `--ignore=scripts` in `addopts` does
**not** suppress collection when `scripts` is an explicit `testpaths` entry (`526` node ids collected
from `scripts/` with and without it). Reported because a probe that fires for the wrong reason is
worth nothing — `norecursedirs` is the one that actually works, and only for paths *below* a
testpath.

---

## 7. MISSING PINS — numbered, actionable, BOTH LEGS PROVEN

The full pin bodies are in §12.2 (`scripts/test_proposed_pins.py`, run in the scratch). Leg 2
(control): **9 of 10 pass on the known-correct reference build** — the tenth, P-6, is red because
the capability genuinely does not exist yet, which is the point of asking for it.

| # | the test that should exist | the defect it catches | severity |
|---|---|---|---|
| **P-1** | `TestBlindIsNotCleanThroughTheWholeVerdict` — four cases routing an unreachable sha, a blind `MEMBERS`, a `"."` testpath and a missing `git` binary through **`ungated_ground`/`classify`**, not through the reader | a build that swallows `GuardIsBlind` inside the verdict and serves a CLEAN tree. **Kills AWB01, AWB03, AWB04, AWB05** | **BLOCKER** |
| **P-2** | `test_a_TEST_SHAPED_sibling_of_the_receipts_root_is_not_exempt_on_execution` (a `docs/plans/v2/receipts_live/test_promoted_tool.py` fixture) | the receipts membership site discriminating on TYPES only. **Kills AWB09** | **BLOCKER** |
| **P-3** | `test_a_file_added_after_the_freeze_is_flagged_on_the_EXECUTION_axis_too` (an `axis=EXECUTION` exemption row + a file added after the freeze) | the frozen roster governing one axis; an EXECUTION-axis row stays an OPEN-set exemption — the exact staleness the ruling exists to close. **Kills AWB14** | **BLOCKER** |
| **P-4** | `test_member_mypypath_returns_only_what_the_runner_declares` + `test_every_declared_mypypath_entry_is_a_line_of_the_real_runner` | a `member_mypypath` that fabricates the map, so the pin closing the lead's §7.4 red-gate gap asks the GUARD for its opinion about the RUNNER — **the identical false-gate shape the author fixed one pin over**. **Kills NP1** | **BLOCKER** |
| **P-5** | `test_a_tree_holding_only_a_py_substring_file_is_blind_not_clean` | the roster's `.py` filter as a substring test, defeating the anti-vacuity guard. **Kills NP6** | MEDIUM |
| **P-6** | `TestPytestConfigurationThisGuardDoesNotModel` + a `gg.unmodelled_pytest_configuration` allowlist over `[tool.pytest.ini_options]` | LEG B certifying COVERED for a file pytest cannot collect (§6). **No wrong build needed — the CORRECT build serves it** | **BLOCKER** |
| **P-7** | extend the malformed-row matrix: `frozen_sha` of `"ab"`, `"F033A87"`, `"deadbeefG"` | validation admitting a sha shape that only fails later, at the roster. **Kills NP5**. (Bounded: the *shipped* row is separately pinned) | LOW |
| **P-8** | a hostile-path fixture on the ROSTER seam (a `scripts/forged\nrow.py` present at the frozen sha) | `git ls-tree` read line-wise: a grandfathered file falls out of the roster and is flagged — a false POSITIVE, which is how a gate gets switched off. **Kills AWB13** | MEDIUM |

**Leg-1 receipts (each pin kills exactly its target and nothing else):**

```
AWB01  → FAILED …test_an_unreachable_frozen_sha_makes_the_WHOLE_VERDICT_refuse
AWB03  → FAILED …test_a_blind_members_declaration_makes_the_WHOLE_VERDICT_refuse
AWB04  → FAILED …test_a_whole_tree_testpath_makes_the_WHOLE_VERDICT_refuse
AWB05  → FAILED …test_a_missing_git_binary_makes_the_WHOLE_VERDICT_refuse
AWB09  → FAILED …test_a_TEST_SHAPED_sibling_of_the_receipts_root_is_not_exempt_on_execution
AWB14  → FAILED …test_a_file_added_after_the_freeze_is_flagged_on_the_EXECUTION_axis_too
NP1    → FAILED …test_member_mypypath_returns_only_what_the_runner_declares
         FAILED …test_every_declared_mypypath_entry_is_a_line_of_the_real_runner
NP6    → FAILED …test_a_tree_holding_only_a_py_substring_file_is_blind_not_clean
(every row additionally shows the always-red P-6, the missing capability)
```

---

## 8. P1b — THE QUANTIFIER TABLE (∀-over-inputs vs guarded-by-known-failure-mode)

Every guarded row carries a receipt: either a surviving wrong build walking the same bad outcome
through an unguarded door, or the attempted door-build naming the pin that killed it.

| # | invariant | ∀ or GUARDED | receipt |
|---|---|---|---|
| I1 | every tracked `.py` has exactly one fate per axis; every UNGATED fate is reported | **∀-over-inputs** — the helper runs on every fixture, conditioned on no cause | AWB28 (report one axis) killed by **31**; AWB22 (union) killed by **19** |
| I2 | LEG A coverage ⟺ under a parsed typecheck root, component-wise | **∀ over call sites** (the r2 fix) | AWB06 killed; AWB24 (file-root→parent) killed by 4 |
| I3 | LEG B coverage ⟺ under a parsed testpath, component-wise | **∀ over call sites** | AWB07 killed; WB27 (reverse containment) killed by 2 |
| I4 | archived-receipts exemption membership | **GUARDED by AXIS** — the only fixture is not test-shaped | ❗**AWB09 SURVIVED 174/174**; divergence `EXECUTION: UNGATED → EXEMPT_ARCHIVED_RECEIPTS`. → **P-2** |
| I5 | an exemption applies ⟺ path ∈ the frozen roster, on the row's axis | **GUARDED by AXIS** — all roster fixtures use `axis=TYPES` | ❗**AWB14 SURVIVED**; divergence `EXECUTION: UNGATED → EXEMPT_TABLE`. → **P-3** |
| I6 | a file added after the frozen sha is not grandfathered | **∀ over files** (on TYPES) | AWB10, AWB11 each killed by 2 — and the `FROZEN_SHA == HEAD` coincidence is **NOT** a monoculture trap: fixtures mint their own two-commit topology |
| I7 | **blind is not clean** | **GUARDED by ENTRY POINT** — 14 blind inputs pinned on readers, 2 through the verdict | ❗**AWB01, AWB03, AWB04, AWB05 SURVIVED**; 2 of 4 serve bytes identical to healthy (§3). → **P-1** |
| I8 | the roster is DERIVED, never a committed list | **∀** (disjointness against this checkout) | AWB12 killed |
| I9 | the table refuses malformed rows | **∀ over 21 shapes**, except `frozen_sha`, guarded by 3 named shapes | ❗**NP5 SURVIVED** (`"ab"`, uppercase). Bounded by a separate shipped-row pin. → **P-7** |
| I10 | the file enumeration is NUL-separated and suffix-filtered | **GUARDED by SEAM** — pinned on `git ls-files`, not on `git ls-tree` | ❗**AWB13 and NP6 SURVIVED**; divergences in §4.4. → **P-5**, **P-8** |
| I11 | the guard grants itself no special exemption | **∀ — two independent pins, one runner-based and immune to the guard** | AWB15, AWB15b, AWB16 killed; AWB15c survives but is **INERT** and dies in the state that matters (§4.3) |
| I12 | the instrument rides the type gate via a `MEMBERS` entry | **∀** — reads the RUNNER | AWB16 killed; the entries-deleted state reddens it (§2) |
| I13 | the file-entry leg declares the `MYPYPATH` it needs | **GUARDED — it asks the GUARD, not the runner** | ❗**NP1 SURVIVED**; reference RED / NP1 GREEN on a runner with no declaration. → **P-4** |
| I14 | the message carries a contiguous disclaimer and both ways out | **∀ over findings** | WB36 killed; NP7 (per-axis variant) killed |
| I15 | threat model + every bound stated, each with a distinct trigger | **∀ over `STATED_BOUNDS`** | WB33 killed |
| I16 | **registration ⟹ the gate's scope really contains the file** | **GUARDED to LEG A ONLY** (`unmodelled_mypy_configuration`) | ❗the **CORRECT** build serves a false clear under `norecursedirs` (§6). → **P-6** |
| I17 | the instrument imports stdlib only / never the project | **∀** (AST walk incl. lazy imports) | author's MP7; re-checked by inspection of my build |
| I18 | findings are deterministic and path-ordered | **∀** | AWB27 killed |
| I19 | untracked ground is out of scope | **∀ by construction** | pinned as behaviour — **but see §9 S4: it is not a STATED BOUND, so no reader of the guard meets it** |

---

## 9. SURFACED TO LEAD — questions, not decisions (scope is yours)

**S1 — ⚠ `FROZEN_SHA = f033a87` IS A FEATURE-BRANCH-ONLY OBJECT, and the gate dies with it.**
```
$ git branch -a --contains f033a87
* pkt44/ungated-ground
$ cd <a repo without that object> && git ls-tree -r --name-only f033a87 -- scripts
fatal: Not a valid object name f033a87
```
A squash-merge to `master`, a rebase, a `gc` after the branch is deleted, or any fresh/shallow clone
orphans the commit — and the roster derivation then raises `GuardIsBlind` **for everyone,
permanently**. That is "loud", which is correct by design, but it is loud in the most confusing
possible way *and it is exactly the pressure that produces wrong build AWB01* ("the sha didn't
survive the rebase; fall back to the tree root"). **Recommendation (yours to rule):** a pin asserting
the frozen sha is an ANCESTOR of `HEAD` (`git merge-base --is-ancestor`), whose failure message says
*"the frozen commit was orphaned by a rebase/squash — re-pin `FROZEN_SHA` to the merge commit's
first parent and re-derive; do NOT widen the row"*. Cheaper than the outage, and it converts a
mysterious future red into an instruction. The author's r3 §3.1 raises the adjacent landing-order
question but not this one.

**S2 — the guard cannot run in the deployed image.** `Containerfile` COPYs `pyproject.toml`,
`uv.lock` and the four members; it copies **neither `scripts/` nor `.git`**. If packet 01a's in-image
conformance run (#139) ever collects `testpaths`, this contract errors in-image (`git` may also be
absent — #131's own shape). Not a defect of this contract; a landing-sequence fact worth knowing.

**S3 — `REPORT-contract-44-gatedground-1-r2.md` §7.1 states md5 `6887b7a140b4799f68d39bbe98595a69`.**
The file's md5 is `ec3dd8906553fe0d1688d645d7161818` (r2's own SUMMARY BLOCK, r3 §4.1, and my two
measurements agree). **Verdict: a stale receipt in r2, silently corrected by r3.** Harmless here
because r3 exists; worth naming because "the number in the report about numbers" is this repo's
signature failure.

**S4 — `untracked-ground` is pinned as BEHAVIOUR but is not a STATED BOUND.** `REQUIRED_BOUND_
IDENTIFIERS` has five entries and none says *"the quantifier is `git ls-files`; untracked ground is
out of scope"*. Under Leg 1 (scope diff) the render should name the SET it answered about. One
`StatedBound` entry closes it.

**S5 — the author's r3 §3.3 bound (the roster is PATH-keyed) lives only in a report.** Per *WHEN YOU
CANNOT CLOSE A HOLE, PIN IT*, that is a `StatedBound` with a named re-open trigger, not a paragraph
in an archived receipt. The author explicitly offered to add it if ruled — I agree it should be.

**S6 — the three stale-prose sites (author r2 §5.3), each with an INDIVIDUAL verdict** (no wholesale
classification):
- `scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED` docstring — *"`scripts/` is
  OUTSIDE `scripts/typecheck.sh` (#188 measured 41 mypy errors there)"*. **Becomes FALSE at landing**
  for the two instrument files, and carries an undated count (`41`) of exactly the kind
  `test_no_exemption_reason_carries_a_measured_count` bans. **Nothing asserts it → silent.** Owed by
  the builder or a sweep.
- `loremaster/tests/test_secret_typing.py:139-141` — *"`scripts/` is scanned even though it is NOT
  one of `scripts/typecheck.sh`'s `MEMBERS`, so mypy never sees it"*. **Becomes partially false at
  landing** (two files will be MEMBERS). It already, commendably, refuses to quote the list.
  **Nothing asserts it → silent.**
- `scripts/test_search_score_survey.py:572` — *"`scripts/` is not a `typecheck.sh` member (#221)"*.
  **Same class, same verdict: becomes partially false, unasserted, silent.**
- **And one the author did not name, found by my own grep:** `docs/eval/test_smoke_p8b.py:29-35`
  quotes the `testpaths` list in prose. **Verdict: still TRUE after this packet** (packet 44 adds no
  testpaths entry) — listed because "the rest look fine" is banned output.
- **Sweep completeness:** `git grep -n -I "MEMBERS"` over `loremaster lorerunes lorescribe loresigil
  docs scripts skills`, minus `_SCANNED_MEMBERS` / `LEGACY_DISJOINT` / `MEMBERSHIP` / the contract
  itself, returns **only** the above plus archived `docs/plans/v2/receipts/**` reports (which are
  dated artifacts and correctly stale). **No live ASSERTION anywhere in the tree pins the `MEMBERS`
  content**, so adding the two entries breaks nothing.

**S7 — `test_a_file_entry_importing_a_sibling_declares_the_mypypath_its_leg_needs` is doubly weak.**
The author disclosed leg one (it is **vacuously green** until a file entry exists). P-4 is leg two
(it can be answered by the guard). Both should be closed together, or the lead should know that the
"the builder can no longer ship a `typecheck.sh` that exits 1" claim in r2 §4.2 is currently
**unsupported**.

**S8 — nothing pins that `scripts/typecheck.sh` EXITS ZERO with the new entries.** Only the
MYPYPATH *cause* is modelled. A `MEMBERS` entry that fails mypy for any other reason ships with all
174 green. This is arguably the commit gate's job, not the contract's — but the contract is what
*adds* the entries, so I flag rather than assume.

**S9 — `scripts/registration_sites.py` derives registration sites from "three or more member names
co-occur".** File-granularity `MEMBERS` entries are a new registration shape; whether the derivation
still finds `typecheck.sh` is out of my grading scope and worth one run before landing.

**S10 — a P2 fixture note, no action implied.** `_minimal_repository`'s
`if not any(path.startswith("scripts/") for path in extra_files)` uses `str.startswith` — inside a
contract whose central lesson is that `startswith` loses. It is fixture bookkeeping and cannot
affect a verdict (an `extra_files` entry of `scripts_extra/x.py` would merely skip the auto-added
`scripts/` file and trip the roster's own anti-vacuity raise, loudly). Named, not charged.

---

## 10. P-PKG — my table, built first, then DIFFED against the author's r2 §6

| mechanism the contract specifies | library evaluated | what I **READ** (an installed signature or source, never an expectation) | my verdict | vs author |
|---|---|---|---|---|
| path-component membership (`is_under`) | `PurePosixPath.is_relative_to` | ran the contract's own 12-row matrix through it — 12/12; **and probed the identity case: `PurePosixPath('scripts').is_relative_to('scripts')` → `True`**, so the `==` disjunct is redundant. Also probed `PurePosixPath('release_probe.py').is_relative_to('.')` → **`True`**, which is *why* the `"."` guards are load-bearing (NP4 confirms) | **replace** | agrees |
| `MEMBERS=(…)` token split | `shlex.split` / `shlex.quote` | measured: `shlex.split('a "docs/my eval" b')` → `['a','docs/my eval','b']`; `str.split` → 4 tokens. `shlex.quote('docs/eval')` → unquoted, so the real-runner seam pin still matches byte-for-byte | **replace** | agrees (author retracted a measurably false r1 row — correctly) |
| locating the `MEMBERS` declaration line | `bashlex` (not installed) vs anchored `re` | `bashlex` would be an install; `re.match(r"^MEMBERS=\(")` + a duplicate-count check is the whole mechanism | **bespoke** (anchored regex) | agrees |
| TOML parsing | `tomllib` | stdlib; `tomllib.loads`; note it **raises on duplicate keys**, which is why the `testpaths` duplicate-declaration attack is not a hazard | **replace** | agrees |
| filename glob | `fnmatch` | **read the source:** `fnmatch()` calls `os.path.normcase()` on BOTH arguments then delegates to `fnmatchcase()`. On linux/macOS `normcase` is identity, so they agree; on Windows they do not | **replace with `fnmatchcase`** | ⚠ **DIFF — the author's row names `fnmatch.fnmatch`.** Right name, platform-dependent semantics ("check the CLASS, not just the name"). **Immaterial for this project** (linux + macOS only) — recorded, not charged |
| committed-file enumeration | `git ls-files -z` | measured NUL-raw vs quoted-line output on a `docs/consult/forged\nrow.py` path | **replace** | agrees |
| **frozen-set enumeration at a commit** | `git ls-tree -r -z --name-only` | measured: identical quoting hazard to `ls-files`; `-z` required. Also measured `git ls-tree` on `""`, `"deadbee"`, `"0"*40`, `"not-a-sha"` → all `fatal`, and on an UPPERCASE sha → **rc=0** | **replace** | ⚠ **DIFF — THE AUTHOR'S SURVEY HAS NO ROW FOR THIS SEAM AT ALL.** It is a *new* mechanism introduced by the frozen-roster ruling, and it is exactly where AWB13/NP6/P-5/P-8 live. **A correction is a specification too — survey it.** |
| stdlib membership of an import | `sys.stdlib_module_names` + `ast` | present in 3.14; walked the whole AST incl. lazy imports | **replace** a maintained allowlist | agrees |
| pytest `python_files` default | `_pytest.config.get_config()._parser._inidict` | private API, read live; the contract's `_pytest_declared_default_patterns` derives rather than restates | **replace_with_adapter** | agrees |
| **what pytest would actually COLLECT** | `pytest --collect-only` / `_pytest.main` | the instrument is stdlib-only **by ruling**, so it cannot call pytest — the `keep_with_trigger` is legitimate and its trigger is real | **keep_with_trigger** | ⚠ **partial DIFF:** the verdict is right, but the **cheap in-scope substitute was never surveyed** — an allowlist over `[tool.pytest.ini_options]` keys, mirroring `unmodelled_mypy_configuration`, needs no library at all. That gap is finding **P-6** |
| what mypy would actually CHECK | `mypy.find_sources` | same reasoning; the allowlist substitute IS built here | **keep_with_trigger** | agrees |
| mutation proving | `scripts/mutation_proof.py` | read `--help` semantics: exactly-once anchor, expected-RED node ids as an ARGUMENT, both-ways diff, content restore | **keep_with_trigger** for repo work | ⚠ my deviation — §11 |

---

## 11. Deviation

I used my own harness (`probe.py`, §12.1) rather than `scripts/mutation_proof.py`. Reason: I needed
to mutate a *scratch reference implementation* and run the contract against it 44 times, which is
not the shape `mutation_proof.py` takes (it mutates the real tree and diffs a declared node set).
**The cost is real and I state it:** `mutation_proof.py`'s both-ways diff of a *pre-declared* RED set
is stronger discipline than my "did anything fail" check. I compensated with (a) an
anchor-landed-exactly-once assertion that hard-exits, (b) a no-op-mutation guard, (c) the
unmutated-reference 174/0 control before every batch, and (d) the divergence prover in §4.3/§4.4
that rejects inert patches. Where I *declare* an expected set — the eight proposed pins in §7 — I
declared it before running and every row matched.

---

## 12. INSTRUMENTS (brief-base §1: an instrument that established a load-bearing claim is a
deliverable, not scratch — pasted verbatim because the scratch tree is disposable by design)

All four live at `/home/ejprice/adv44-scratch/` (an unrecoverable address, hence the paste).

### 12.1 `probe.py` — the wrong-build harness core

```python
#!/usr/bin/env python3
"""Applies a named mutation to the ADVERSARY REFERENCE BUILD of scripts/gated_ground.py inside
an isolated scratch replica, runs the REAL contract against it, and reports passed/failed plus
the failing node ids.  A wrong build that survives at 174 passed / 0 failed is a BLOCKER."""
SCRATCH   = Path("/home/ejprice/adv44-scratch")
BASE      = SCRATCH / "base"
TARGET    = BASE / "scripts" / "gated_ground.py"
REFERENCE = SCRATCH / "reference_gated_ground.py"

def _apply(name: str) -> str:
    source = REFERENCE.read_text(encoding="utf-8")
    for old, new in MUTATIONS[name]:
        if old not in source:                       # #194: evidence the mutation LANDED
            raise SystemExit(f"MUTATION DID NOT LAND for {name!r}: anchor absent")
        if source.count(old) != 1:
            raise SystemExit(f"MUTATION AMBIGUOUS for {name!r}: {source.count(old)} matches")
        source = source.replace(old, new)
    if source == REFERENCE.read_text(encoding="utf-8"):
        raise SystemExit(f"MUTATION IS A NO-OP for {name!r}")
    TARGET.write_text(source, encoding="utf-8")
    return source

def _run() -> tuple[int, int, list[str]]:
    completed = subprocess.run([str(PYTHON), "-m", "pytest", "scripts/test_gated_ground.py",
                                "-q", "-p", "no:randomly", "--no-header", "-rf"],
                               cwd=BASE, capture_output=True, text=True)
    output = completed.stdout + completed.stderr
    failed_ids = sorted({line.split(" ")[1].split("::", 1)[-1] for line in output.splitlines()
                         if line.startswith(("FAILED ", "ERROR "))})
    failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", output)) else 0
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", output)) else 0
    return passed, failed, failed_ids
# main(): for each name -> _apply, _run, print "SURVIVED (BLOCKER)" iff failed == 0;
#         finally shutil.copyfile(REFERENCE, TARGET)
```

**The seven batch-1 survivor patches, verbatim** (each a single `(old, new)` pair against the
reference build; the reference build itself is a straightforward implementation of the contract and
is reproducible from the contract in about 500 lines):

```python
"AWB01-roster-blind-swallowed-by-classify": [
  ("        if key not in cache:\n"
   "            cache[key] = frozenset(frozen_roster(repo_root, sha=row.frozen_sha, root=row.root))",
   "        if key not in cache:\n"
   "            try:\n"
   "                cache[key] = frozenset(frozen_roster(repo_root, sha=row.frozen_sha, root=row.root))\n"
   "            except GuardIsBlind:\n"
   "                cache[key] = None  # 'the frozen sha did not survive the rebase'"),
  ("        if row.axis is axis and path in rosters[(row.root, row.frozen_sha)]:",
   "        roster = rosters[(row.root, row.frozen_sha)]\n"
   "        if row.axis is axis and (is_under(path, row.root) if roster is None else path in roster):")],

"AWB03-typecheck-roots-blind-swallowed-fallback-to-members": [   # applied at BOTH call sites
  ("    roots = typecheck_roots(repo_root)",
   "    try:\n        roots = typecheck_roots(repo_root)\n"
   "    except GuardIsBlind:\n        roots = workspace_members(repo_root)")],

"AWB04-testpaths-blind-swallowed-everything-covered": [          # applied at BOTH call sites
  ("    testpaths = pytest_testpaths(repo_root)",
   "    try:\n        testpaths = pytest_testpaths(repo_root)\n"
   "    except GuardIsBlind:\n        testpaths = ['.']")],

"AWB05-git-blind-swallowed-empty-file-list": [
  ("    tracked = tracked_python_files(repo_root)",
   "    try:\n        tracked = tracked_python_files(repo_root)\n"
   "    except GuardIsBlind:\n        tracked = []\n    if not tracked:\n        return []")],

"AWB09-startswith-at-receipts-site-EXECUTION-axis-only": [
  ("    if is_under(path, ARCHIVED_RECEIPTS_ROOT):",
   "    if is_under(path, ARCHIVED_RECEIPTS_ROOT) or (\n"
   "        axis is GateAxis.EXECUTION and path.startswith(ARCHIVED_RECEIPTS_ROOT)\n    ):")],

"AWB13-roster-line-split-not-NUL": [
  ('raw = _git(Path(repo_root), "ls-tree", "-r", "-z", "--name-only", sha, "--", root)',
   'raw = _git(Path(repo_root), "ls-tree", "-r", "--name-only", sha, "--", root).replace("\\n", "\\0")')],

"AWB14-roster-honoured-on-TYPES-only-tree-root-on-EXECUTION": [
  ("        if row.axis is axis and path in rosters[(row.root, row.frozen_sha)]:",
   "        in_scope = (path in rosters[(row.root, row.frozen_sha)]\n"
   "                    if axis is GateAxis.TYPES else is_under(path, row.root))\n"
   "        if row.axis is axis and in_scope:")],

"NP1-member-mypypath-reader-fabricates-what-the-runner-lacks": [ # appended to member_mypypath
  ("    return declared",
   "    for root in typecheck_roots(repo_root):          # 'a file root resolves against its dir'\n"
   "        if (Path(repo_root) / root).is_file():\n"
   "            declared.setdefault(root, str(PurePosixPath(root).parent))\n    return declared")],

"NP5-frozen-sha-validation-accepts-a-short-or-upper-hex": [
  ('if not re.fullmatch(r"[0-9a-f]{7,40}", self.frozen_sha):',
   'if not re.fullmatch(r"[0-9a-fA-F]{1,40}", self.frozen_sha):')],

"NP6-py-substring-only-in-the-frozen-roster": [
  ('roster = sorted(entry for entry in raw.split("\\0") if entry.endswith(".py"))',
   'roster = sorted(entry for entry in raw.split("\\0") if ".py" in entry)')],
```

### 12.2 `test_proposed_pins.py` — THE EIGHT MISSING PINS, both legs proven

Run against the reference build → **9 passed, 1 failed** (the failure is P-6, the capability that
does not exist). Run against each named wrong build → that build's pin goes RED and no other.

```python
"""THE PROPOSED MISSING PINS, validated both legs.  Leg 2 = green on a known-correct build;
leg 1 = red on the wrong build that survived the shipped contract at 174/174."""

def _repository(root, *, members=("loremaster",), testpaths=("loremaster/tests",), files=(),
                ruff=("scratchpad", "docs/plans/v2/receipts"), write_runner=True) -> str:
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=root, check=True)
    assert (root / ".git").is_dir(), "#284: .git must be a DIRECTORY, never an inherited file"
    ...  # writes scripts/typecheck.sh, pyproject.toml, the files; git add -A; commit; returns HEAD


class TestBlindIsNotCleanThroughTheWholeVerdict:                          # P-1  (AWB01/03/04/05)
    def test_an_unreachable_frozen_sha_makes_the_WHOLE_VERDICT_refuse(self, tmp_path):
        _repository(tmp_path)
        rows = _rows(sha="dead000000000000000000000000000000000bee")
        with pytest.raises(gg.GuardIsBlind):
            gg.ungated_ground(tmp_path, exemptions=rows)
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(tmp_path, exemptions=rows)

    def test_a_blind_members_declaration_makes_the_WHOLE_VERDICT_refuse(self, tmp_path):
        sha = _repository(tmp_path, write_runner=False)
        with pytest.raises(gg.GuardIsBlind):
            gg.ungated_ground(tmp_path, exemptions=_rows(sha=sha))
        with pytest.raises(gg.GuardIsBlind):
            gg.classify(tmp_path, exemptions=_rows(sha=sha))

    def test_a_whole_tree_testpath_makes_the_WHOLE_VERDICT_refuse(self, tmp_path):
        sha = _repository(tmp_path, testpaths=("loremaster/tests", "."))
        with pytest.raises(gg.GuardIsBlind):
            gg.ungated_ground(tmp_path, exemptions=_rows(sha=sha))

    def test_a_missing_git_binary_makes_the_WHOLE_VERDICT_refuse(self, tmp_path, monkeypatch):
        rows = _rows(sha=_repository(tmp_path))
        monkeypatch.setenv("PATH", str(tmp_path / "no_binaries_here"))
        with pytest.raises(gg.GuardIsBlind):
            gg.ungated_ground(tmp_path, exemptions=rows)


class TestTheReceiptsSiteDiscriminatesOnBothAxes:                                    # P-2 (AWB09)
    def test_a_TEST_SHAPED_sibling_of_the_receipts_root_is_not_exempt_on_execution(self, tmp_path):
        sha = _repository(tmp_path, files=("docs/plans/v2/receipts_live/test_promoted_tool.py",))
        fate = _fate(tmp_path, _rows(sha=sha),
                     "docs/plans/v2/receipts_live/test_promoted_tool.py", gg.GateAxis.EXECUTION)
        assert fate is gg.Fate.UNGATED, (
            f"a TEST-SHAPED sibling of the archived-receipts root inherited the archive's "
            f"exemption on the EXECUTION axis; got {fate}")


class TestTheFrozenRosterGovernsEveryAxis:                                           # P-3 (AWB14)
    def test_a_file_added_after_the_freeze_is_flagged_on_the_EXECUTION_axis_too(self, tmp_path):
        frozen = _repository(tmp_path, members=("loremaster", "skills"),
                             files=("skills/lore-deploy/tests/test_port_probe.py",))
        # ... add skills/newskill/tests/test_added_later.py, git add -A, commit ...
        rows = _rows(root="skills", axis=gg.GateAxis.EXECUTION, sha=frozen)
        fate = _fate(tmp_path, rows, "skills/newskill/tests/test_added_later.py",
                     gg.GateAxis.EXECUTION)
        assert fate is gg.Fate.UNGATED, (
            f"a file added AFTER the frozen sha was grandfathered on the EXECUTION axis; the "
            f"roster governs the types axis only, so an execution-axis row is still an "
            f"open-set exemption. Got {fate}")


class TestTheMypypathReaderReadsTheRunner:                                            # P-4 (NP1)
    def test_member_mypypath_returns_only_what_the_runner_declares(self, tmp_path):
        _repository(tmp_path, members=("loremaster", "scripts/registration_sites.py"))
        declared = gg.member_mypypath(tmp_path)
        assert declared == {}, (
            f"the runner declares no MEMBER_MYPYPATH map, but the reader returned {declared!r}. "
            f"A reader that fabricates the map makes the MYPYPATH requirement pin answer a "
            f"question about the runner with the guard's own opinion -- the false-gate shape.")

    def test_every_declared_mypypath_entry_is_a_line_of_the_real_runner(self):
        runner = (REPO_ROOT / "scripts" / "typecheck.sh").read_text(encoding="utf-8")
        for entry, value in gg.member_mypypath(REPO_ROOT).items():
            assert f'[{entry}]="{value}"' in runner, (
                f'member_mypypath reports [{entry}]="{value}", which reconstructs no line of '
                f"scripts/typecheck.sh -- the reader is not reading the file the gate executes")


class TestTheRosterFiltersPythonBySuffix:                                             # P-5 (NP6)
    def test_a_tree_holding_only_a_py_substring_file_is_blind_not_clean(self, tmp_path):
        sha = _repository(tmp_path, files=("docs/consult/notes.py.txt",))
        with pytest.raises(gg.GuardIsBlind):
            gg.frozen_roster(tmp_path, sha=sha, root="docs/consult")


class TestPytestConfigurationThisGuardDoesNotModel:            # P-6 (the CORRECT build's false clear)
    def test_a_norecursedirs_setting_makes_the_guard_refuse_rather_than_mis_model(self, tmp_path):
        _repository(tmp_path)
        manifest = tmp_path / "pyproject.toml"
        manifest.write_text(manifest.read_text(encoding="utf-8") + 'norecursedirs = ["probes"]\n')
        unmodelled = getattr(gg, "unmodelled_pytest_configuration", None)
        assert unmodelled is not None, (
            "the guard models [tool.mypy] settings that can make a REGISTERED file unchecked "
            "(unmodelled_mypy_configuration) and models NOTHING equivalent for "
            "[tool.pytest.ini_options]. norecursedirs / collect_ignore_glob / an --ignore-glob "
            "in addopts each make a REGISTERED file UNCOLLECTED, which is LEG B's whole claim.")
        assert unmodelled(tmp_path), "a declared norecursedirs was accepted silently"

# P-7: add to the malformed-row matrix -> ({"frozen_sha": "ab"}, "a sha too short to be a git
#      object name"), ({"frozen_sha": "F033A87"}, "an uppercase object name the row does not
#      normalise"), ({"frozen_sha": "deadbeefG"}, "a non-hex character").
# P-8: the AWB13 fixture -- commit `scripts/forged\nrow.py` BEFORE the freeze and assert its
#      TYPES fate is EXEMPT_TABLE (line-split ls-tree makes it UNGATED, a false positive).
```

### 12.3 `legtwo.py` — the Leg-2 false-clear constructor (structure)

```python
def _render(build_source, *, env_path=None) -> str:
    """The bytes this build SERVES for BASE, or the exception it raises."""
    TARGET.write_text(build_source); gg = _reimport()
    try:
        findings = gg.ungated_ground(BASE)
        return f"CLEAN ({len(findings)} findings)" if not findings else "\n\n".join(
            f.message for f in findings)
    except Exception as error:
        return f"RAISED {type(error).__name__}: {str(error)[:150]}"

def _case(title, mutation, degrade, restore, *, env_path=None):
    healthy = _render(REFERENCE.read_text())          # the healthy render
    degrade()
    control = _render(REFERENCE.read_text(), env_path=env_path)   # correct build, BROKEN state
    served  = _render(_mutate(mutation),    env_path=env_path)    # wrong build,   BROKEN state
    restore()
    print("FALSE CLEAR - identical bytes to healthy" if served == healthy else "distinguishable")

# cases: frozen sha -> unreachable | runner -> MEMBERS renamed away | pyproject -> testpaths += "."
#        | PATH -> an empty directory (no git binary)
```

### 12.4 `divergence.py` — the P0 control that rejected two of my own survivors

```python
def np2():  # "is there ANY input that separates the builds?"
    a = {v.path: v.fates[TYPES].name for v in reference.classify(BASE)}
    b = {v.path: v.fates[TYPES].name for v in wrong.classify(BASE)}
    differing = {p: (a[p], b[p]) for p in a if a[p] != b.get(p)}
    print(f"tracked paths compared: {len(a)}   divergent verdicts: {len(differing)}")
    # -> 292 compared, 0 divergent  =>  INERT PATCH (not a finding)
```

---

## 13. What this contract does exceptionally well (so a fix wave does not damage it)

Stated because a fix wave that guts a strength to close a gap is a worse outcome than the gap.

1. **The per-axis framing is right and the `half_gapped_repository` fixture is lethal** — the union
   build died on 19 pins, the TYPES-only reporter on 31. Nothing here should be softened.
2. **`unmodelled_mypy_configuration` is the best idea in the packet** — allowlist-by-default with
   *"a setting invented after this guard"* params is the instrument-lesson applied correctly, and
   its false-gate control (`…relaxations_this_repository_actually_uses…`) is why it will not get
   switched off. **P-6 asks for exactly this, one axis over.**
3. **The runner-reading requirement pin is the structural fix that holds.** Every self-exemption I
   could invent — literal, basename, resolved path, fixture-blind — is either killed or inert,
   because one pin asks the *runner* and not the guard. That is a genuine improvement on revision 2.
4. **The accounting helper is a real ∀-over-inputs quantifier**, not a conditional: it asks *where
   did each of the N tracked files GO*, and it caught every drop/invent/double-classify I tried.
5. **Fixtures are `git init` from empty and the parameter-monoculture discipline is visible**
   (`FixtureRepository` defaults nothing the guard branches on). The `FROZEN_SHA == HEAD` coincidence
   the brief flagged as a possible trap is **not** one — the roster fixtures mint their own
   two-commit topology, so AWB11 dies.
6. **The author's PROOF-FAILED disclosures are honest and reproduce.** I re-ran MP-R2/R3/R5/R6 and
   found the same properties; MP-R5's undeclared `TestTheRealRepositoryIsFullyGated` red is exactly
   what their §3.2 describes.

---

## 14. VERDICT

# CONTRACT INSUFFICIENT

Not because it is weak — it is the strongest contract I have graded in this repository, and a
blind reference implementation satisfied it 174/0 on the first attempt. It is insufficient because
**twelve wrong builds pass all 174 pins, ten of them with a proven behavioural divergence, three of
them serving bytes identical to a healthy tree on a broken state — and one false clear needs no
wrong build at all, because the CORRECT build serves it.**

The eight missing pins in §7 are written, run, and proven on both legs. Six are a one-class fix
(quantify an existing invariant over the *entry point*, over the *other axis*, or over the *second
enumeration seam* instead of only where the failure was first found) — the quantifier law, three
more times. P-4 is the false-gate law recurring in the sibling of the pin where the author had just
fixed it. P-6 is a mechanism the survey verdicted `keep_with_trigger` without surveying the cheap
substitute that needs no library at all.

**Recommended routing:** back to CONTRACT for P-1…P-8, then **an adversary pass on the revision** —
this grading found four blockers in a revision that had already been graded once, which is the
receipt for that rule, not an argument against it.

---

*Graded 2026-07-29 by `adversary-44-gatedground-2` against md5 `ec3dd8906553fe0d1688d645d7161818`
at `f033a87`. Scratch tree `/home/ejprice/adv44-scratch/` is disposable; every load-bearing
instrument is pasted in §12. The repository was not modified: `scripts/gated_ground.py` was never
created in the worktree, and the contract's md5 is unchanged from the value in my brief.*
