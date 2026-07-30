brief-base v9 read

# REPORT-adversary-44-gatedground-1 — contract adversary, packet 44 (`scripts/test_gated_ground.py`)

*Every measurement below was taken **2026-07-29** in the worktree `.claude/worktrees/pkt44`,
branch `pkt44/ungated-ground`, HEAD **`f033a87`** (HEAD did not move during my run). **The
graded artifact is `scripts/test_gated_ground.py` at md5 `77a0cde8bdc6a7f2a12bcb7a8cda5682`,
1864 lines, 130 collected** — re-verified unchanged at the end of the run. ⚠ The file was
**revised twice under me** (see §0); a claim here about "the contract" means that md5 and no
other.*

---

## SUMMARY BLOCK

- `brief-base v9 read` · state: **done**
- **VERDICT: CONTRACT INSUFFICIENT** — 8 numbered missing pins, each with the test to write and
  the defect it catches (§4). This is a *strong* contract; the survivors are concentrated in one
  shape (see next line), not scattered.
- **P1 HEADLINE: 42 wrong builds built and run against the real contract; 31 killed, **11 SURVIVED
  (130 passed / 0 failed)**.** Seven have a proven divergence receipt on a constructed input (§2.2).
  The sharpest: **a guard that hardcodes `if path in {"scripts/gated_ground.py",
  "scripts/test_gated_ground.py"}: COVERED` — the lead's named WRONG BUILD #2 — passes ALL 130**;
  and the pin written to forbid it, `test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row`, **passes on that build even with no `MEMBERS` entry at all** (§2.3).
- **THE ONE SHAPE:** `is_under` is pinned by a 12-row matrix, but only **1 of its 4 call sites** has
  a fixture that discriminates it. `str.startswith` at the typecheck-root site (WB28), the testpath
  site (WB3) and the receipts site (WB29) each survive the whole contract. Classic no-op-fix class.
- **LEG-2 FORGERY: 6 false clears against a build that passes 130/130** (§3) — a 2nd `MEMBERS=(`
  declaration (bash's last assignment wins → LEG A canary vanishes), `testpaths=["."]` / `[""]`
  (LEG B vanishes), an exemption row rooted at `"."` (whole axis silenced). Plus **5 mypy
  relaxations accepted silently**, including a *global* `[tool.mypy] ignore_errors = true` (§3.2).
- **P0 controls held:** my reference build passes **130/130** (satisfiability, independently
  reproduced); every patch asserts its anchor landed; every survivor carries a divergence receipt;
  my own Leg-2 probe **under-reported on its first run and I fixed it** (§3.1); my own P_A pin was
  RED for the wrong reason and I caught it (§4.9).
- `Packages considered:` `PurePath.is_relative_to` (READ: live 12-row replay of the contract's own
  `test_prefix_membership` matrix, 0 mismatches, stdlib ≥3.9) → **replace** the hand-rolled
  `parts[:n]` comparison — *a row the author's survey does not have* · `shlex.split` (READ:
  `shlex.split('a "docs/my eval" b')` → 3 tokens vs `str.split`'s 4) → **replace** `.split()` inside
  the `MEMBERS` parse; the author's `bespoke` row asserts *"the only stdlib-shaped alternative is
  `source`-ing the runner"*, which is **measurably false** · `tomllib` → replace (agree) · `fnmatch`
  → replace (agree) · `git ls-files -z` → replace (agree) · pytest defaults → the author's
  revision-2 constant + contract-side drift guard is **better than my build's private-API import**;
  I adopted it. Full diff §5.
- decisions-needed: 4, all in §7 SURFACED TO LEAD (the `.sh` bound · the duplicate self-typing
  mechanism vs `test_forgery_door_sweep.py` · 3 blank mutation-proof receipts in the contract
  report · two prose claims that go stale at landing).
- receipt pointers: wrong-build matrix §2.1 · divergence proofs §2.2 · Leg-2 sweep §3 · missing
  pins with both legs §4 · P-PKG diff §5 · quantifier table §6 · corpse sweep §8 · instruments
  pasted verbatim §A.

---

## 0. Capability check (brief-base §4, first thing) — and a material hazard

| demanded | what I actually have | what I did instead | what a lead must change |
|---|---|---|---|
| project law: lore-first for code-structure; ledger facts | **no `mcp__lore_lore__*` tools.** `ToolSearch` surfaces the server but no tool was available to me at any point in this run | `git grep` / `git ls-files` throughout — **said out loud, per the dogfood protocol**. I could not file the friction row that fallback normally requires, and I could not read the findings ledger (#188/#233/#260/#261/#280 reach me only through the sidecar and sweep reports, i.e. **inherited, un-re-derived**) | this is the **seventh** instance of the crippled-agent-definition class (the contract author reported the sixth). Either grant `contract-adversary` the lore tools or state in the definition that ledger facts arrive via artifacts |
| `SendMessage` to the lead | **absent** — my final chat message and this file are my only channels | wrote the report first, per brief-base §1 | grant the tool or drop the instruction |
| **forbidden:** `cp -a` / `scratch_copy.sh` of this worktree (#284) | honoured — **zero copies** | `git archive HEAD \| tar -x` into a fresh `git init`, **asserted `.git` is a DIRECTORY**; all fixtures `git init` from empty in `tempfile` dirs | — |
| git / uv / pytest / mypy | present | — | — |

**Provenance receipt (#140 law):** every probe ran against
`gated_ground.__file__ = /tmp/adv44/ref/scripts/gated_ground.py` — asserted in-process before any
verdict. The scratch tree's `.git` was verified to be a **directory**, not the worktree's `.git`
**file**. No production file and no test in this repository was modified at any point.

### 0.1 ⚠ THE CONTRACT MOVED UNDER ME — TWICE — AND THIS AFFECTS HOW YOU READ THIS REPORT

| when | md5 | lines | collected |
|---|---|---|---|
| my first read (≈12:55) | *(not captured — my error; see below)* | 1613 | — |
| my first `cp` (13:00) | `3c0c80cd9b598f1d0089aebc524de356` | 1852 | 130 |
| **graded (13:08 → end of run)** | **`77a0cde8bdc6a7f2a12bcb7a8cda5682`** | **1864** | **130** |

The lead's brief describes *"123 pins, 1612 lines"* — that is **revision 1**, which no longer
exists on disk. Two of my independently-derived pre-flight findings were **already fixed in
revision 2 before I could report them**:

- *"`test_every_parsed_typecheck_root_exists_as_a_directory` asserts `is_dir()`, which the F1
  file-entry ruling makes unsatisfiable"* → revision 2 renamed it
  `test_every_parsed_typecheck_root_names_something_that_exists` and relaxed to `.exists()`.
- *"nothing pins the F1/FU2-B mechanism"* → revision 2 added `TestATypecheckRootMayBeASingleFile`
  and `TestThisInstrumentRidesTheTypeGateItself`.

**Two consequences the lead must act on.** (a) I did not snapshot revision 1, so I cannot show
those two findings failing — I report them as *corroborated-and-already-closed*, not as receipts.
(b) **An adversary grading a live-edited artifact is grading a moving target**; the only reason
this run is sound is that the file stopped changing at 13:05 and I re-verified the md5 at the end.
If the author revises again, **this verdict applies to `77a0cde8` and must be re-run.**

---

## 1. Method, and the P0 controls that make the verdicts readable

1. **Independent enumeration first.** I derived my own wrong-build list from the contract source +
   the ruled spec (`REPORT-design-sidecar-44-1.md` §Q3, `FU1 ANSWERS` A/C/D, `FU2 ANSWERS` B)
   **before** opening the author's §4 wrong-build table. ⚠ **Honesty deviation:** I *did* read the
   author's §2 (package survey) and §3 (adversarial pre-flight) earlier in the same command output,
   before writing my package table. I therefore claim independence for my **build** and my
   **wrong-build list**, but only *partial* independence for the P-PKG table — and I say so rather
   than claim a purity I did not have. The two P-PKG rows I contribute (§5) are rows the author's
   table does **not** contain, which is the diff that matters.
2. **A reference build, written blind to the author's §9.** ~390 lines, stdlib-only, pasted in §A.1.
3. **SATISFIABILITY CONTROL (the leg without which every "SURVIVED" is meaningless):**

```
$ cd /tmp/adv44/ref && .venv/bin/python -m pytest scripts/test_gated_ground.py -q
130 passed in 0.82s
```

   …after applying the ruled `typecheck.sh` edit. **Before** it, exactly the two builder-requirement
   pins are red — matching the author's §6.1 independently:

```
2 failed, 128 passed in 0.95s
FAILED …::TestThisInstrumentRidesTheTypeGateItself::test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row
FAILED …::TestThisInstrumentRidesTheTypeGateItself::test_every_file_granularity_members_entry_carries_a_dissolution_trigger
```

4. **P7 — RED honesty, reproduced.** The contract as delivered is RED for the *right* reason, not
   an import typo or a bad path:

```
$ .venv/bin/python -m pytest scripts/test_gated_ground.py -q --no-header
E   ModuleNotFoundError: No module named 'gated_ground'
ERROR scripts/test_gated_ground.py
1 error in 0.12s
```

5. **Every patch asserts its anchor landed** (`apply_patch` raises `SystemExit` if the anchor is
   absent). This fired for real once — batch 1 aborted on `WB13`'s stale anchor — which is the
   #194 control working: *a wrong build that was never built would "survive" for free.*
6. **Every survivor carries a divergence receipt** (§2.2): a constructed input on which the wrong
   build and the reference build give **different fates**. Without it, an inert patch reads as a
   finding.

---

## 2. P1 — WRONG BUILDS

### 2.1 The matrix — 42 built, 31 killed, 11 survived

`P`/`F` are against the full 130-pin contract. Anything with `0F` is a **defect the contract
cannot catch**.

| # | wrong build | result |
|---|---|---|
| WB1 | the packet's literal **BINARY / UNION** property (frontier item 1) | 113P **17F** killed |
| WB2 | `is_under` → `str.startswith` (everywhere) | 124P 6F killed |
| **WB3** | **`str.startswith` ONLY at the LEG-B testpath site** (`is_under` left correct) | **130P 0F — SURVIVED** |
| WB4 | self-exemption by exact path, **no** runner edit | 129P 1F killed — *by the wrong pin*, §2.3 |
| **WB4b** | **self-exemption by exact path + the ruled runner edit** | **130P 0F — SURVIVED** |
| WB5 | `unmodelled_mypy_configuration` computed, never consulted (the no-op reader) | 129P 1F killed |
| WB6 | **frozen count** in the exemption reason (frontier item 2) | 127P 3F killed |
| WB7 | `skills` blanket-covered on LEG B (frontier item 3) | 123P 7F killed |
| WB8 | `git ls-files` failure swallowed → `[]` (frontier item 4) | 129P 1F killed |
| WB9 | `git ls-files` without `-z`, line-split | 128P 2F killed |
| WB10 | message interpolates the path unquoted (forgery) | 129P 1F killed |
| WB11 | report drops the EXECUTION axis | 105P 25F killed |
| WB12 | `conftest.py` ignored on LEG B | 127P 3F killed |
| WB13 | exemption row not axis-scoped | 129P 1F killed |
| WB16 | whole-tree `MEMBERS` entry accepted | 126P 4F killed |
| WB17 | hardcoded `["test_*.py"]` pattern list | 128P 2F killed |
| WB18 | a file root covers its **siblings** | 127P 3F killed |
| WB19 | over-refusing `unmodelled_mypy_configuration` (**false-gate control**) | 104P 26F killed |
| WB20 | `classify` drops hostile (newline) paths | 129P 1F killed |
| WB22 | per-file exemption rows instead of root-scoped | 126P 4F killed |
| WB23 | exemption consulted **before** a file root (papers over the recursion) | 128P 2F killed |
| WB24 | exemption membership by `startswith` | 129P 1F killed |
| WB25 | findings unsorted | 129P 1F killed |
| WB26 | `THREAT_MODEL` is a disclaimer, not a fact | 129P 1F killed |
| **WB27** | **LEG B reverse containment** (a testpath *under* the file's dir counts) | **130P 0F — SURVIVED** |
| **WB28** | **`str.startswith` at the LEG-A typecheck-root site** | **130P 0F — SURVIVED** |
| **WB29** | **`str.startswith` at the archived-receipts site** | **130P 0F — SURVIVED** |
| WB30 | receipts class becomes a growing list of roots | 127P 3F killed |
| **WB31** | **`".py" in record`** instead of `endswith(".py")` | **130P 0F — SURVIVED** |
| WB32 | untracked files included via a directory walk | 128P 2F killed |
| **WB33** | **`StatedBound.reopen_trigger = "TBD"`** | **130P 0F — SURVIVED** |
| WB34 | `NOT_APPLICABLE` used to hide UNGATED on LEG A | 128P 2F killed |
| WB35 | report computed independently of `classify` (drops conftests) | 113P 17F killed |
| **WB36** | **message keyword-stuffs the five required substrings**, disclaimer gone | **130P 0F — SURVIVED** |
| WB37 | LEG B skips everything under `docs` | 124P 6F killed |
| **WB38** | **`Exemption.reopen_trigger = "TBD"`** | **130P 0F — SURVIVED** |
| **WB43** | **repository-root-level `.py` treated as COVERED on both axes** | **130P 0F — SURVIVED** |
| WB44 | UNGATED only for the historically-found trees (`docs`/`tools`/`scripts_extra`) | 129P 1F killed |
| **WB45** | **`Exemption.reason = "x"`** | **130P 0F — SURVIVED** |
| WB46 | a second, undeclared exemption hidden inside the classifier | 129P 1F killed |
| WB47 | LEG B ignores testpaths deeper than 2 components | 128P 2F killed |
| WB48 | blind-check special-cases one entry name | 129P 1F killed |

**Frontier items 1, 2, 3, 6, 7 are all correctly killed.** Frontier items 4 and 5 are where the
holes are.

### 2.2 Divergence receipts — every survivor is genuinely wrong, not an inert patch

Each row is a `git init`-from-empty repository with the named file committed; both modules
classify the same tree.

```
WB3-startswith-only-in-leg-B      loremaster/tests_extra/test_probe.py  [EXECUTION]  reference=UNGATED  wrong=COVERED  -> DIVERGES
WB28-typecheck-root-startswith    docs/evaluation/harness.py            [TYPES]      reference=UNGATED  wrong=COVERED  -> DIVERGES
WB29-receipts-startswith          docs/plans/v2/receipts_live/promoted_tool.py [TYPES] reference=UNGATED wrong=EXEMPT_ARCHIVED_RECEIPTS -> DIVERGES
WB31-py-substring                 docs/consult/notes.py.txt             [TYPES]      reference=ABSENT   wrong=UNGATED   -> DIVERGES
WB43-root-level-py                release_probe.py                      [TYPES]      reference=UNGATED  wrong=COVERED  -> DIVERGES
WB27-legB-reverse-containment     skills/test_workspace_probe.py        [EXECUTION]  reference=UNGATED  wrong=COVERED  -> DIVERGES
WB4b-self-exemption               scripts/gated_ground.py               [TYPES]      reference=EXEMPT_TABLE wrong=COVERED -> DIVERGES
```

Five of the seven wave through **real committed ungated ground**. WB31 is the opposite failure —
it *invents* a finding for `notes.py.txt`, and a false positive is how a gate gets switched off
(this repo's own false-gate law). WB4b is the guard lying about **itself**: it reports COVERED for
a file whose coverage is decided entirely by `typecheck.sh`, so deleting the `MEMBERS` entry
re-opens the recursion invisibly.

### 2.3 ⚠ THE SHARPEST RESULT — the pin named for WRONG BUILD #2 cannot see WRONG BUILD #2

The lead's F1 ruling states: *"A build that hardcodes 'except me' anywhere is a WRONG BUILD —
verify the contract kills it."* The contract's module docstring makes the same claim in prose:
*"The guard therefore contains no mention of its own path anywhere."*

Measured, both ways:

- **WB4b** (hardcode + the ruled runner edit) → **130 passed, 0 failed.** Nothing sees it.
- **WB4** (hardcode, runner *not* edited) → 129P **1F**, and the single red is
  `test_every_file_granularity_members_entry_carries_a_dissolution_trigger` — the **RIDER**, which
  fails only because `typecheck.sh` has no file entry. The pin actually named for this,
  `test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row`, **PASSED** — because
  it asks the guard for its own verdict, and the guard is the thing lying.

The existing guard against this, `test_the_guard_grants_its_own_files_no_special_exemption`, uses
`tools/gated_ground.py` and `tools/test_gated_ground.py`. It therefore detects self-exemption **by
basename only**; a full-path hardcode is invisible to it. That is a **parameter-value monoculture**
of exactly the class this repo has four prior receipts on.

→ **MISSING PIN M1** (§4.1), validated both legs.

---

## 3. P1b/Leg-2 — FORGERY PINS: dependencies × verbs, CONSTRUCTED not reasoned

Run against the reference build — i.e. **a build that passes the contract 130/130**. The fixture
tree always carries a canary, `docs/consult/test_orphan.py`, which is ungated on **both** axes; the
comparison is per-axis against the healthy baseline.

```
HEALTHY BASELINE -> docs/consult/test_orphan.py:EXECUTION
                    docs/consult/test_orphan.py:TYPES

git: index EMPTY (nothing staged)             -> GuardIsBlind: no tracked .py at all …
git: NOT A REPOSITORY                         -> GuardIsBlind: `git ls-files` failed (exit 128) …
git: BINARY ABSENT on PATH (#131 shape)       -> FileNotFoundError: … 'git'
typecheck.sh: MISSING                         -> GuardIsBlind: scripts/typecheck.sh is missing …
typecheck.sh: no MEMBERS declaration          -> GuardIsBlind: no line-anchored MEMBERS=(…) …
typecheck.sh: MEMBERS=()                      -> GuardIsBlind: the MEMBERS=() declaration is empty …
typecheck.sh: MEMBERS=(.)  whole tree         -> GuardIsBlind: MEMBERS entry '.' widens to the whole tree …
typecheck.sh: TWO declarations, 2nd narrower  -> docs/consult/test_orphan.py:EXECUTION   <<< FALSE CLEAR: canary VANISHED on TYPES
pyproject: MISSING                            -> GuardIsBlind: no pyproject.toml …
pyproject: MALFORMED TOML                     -> TOMLDecodeError: Expected ']' …
pyproject: testpaths = []                     -> GuardIsBlind: testpaths is empty …
pyproject: testpaths = ['.']  WHOLE TREE      -> docs/consult/test_orphan.py:TYPES        <<< FALSE CLEAR: canary VANISHED on EXECUTION
pyproject: testpaths = ['', 'loremaster/tests'] -> docs/consult/test_orphan.py:TYPES      <<< FALSE CLEAR: canary VANISHED on EXECUTION
ruff: receipts root removed from extend-exclude -> GuardIsBlind: 'docs/plans/v2/receipts' is not in extend-exclude …
exemption table: a row rooted at '.'          -> docs/consult/test_orphan.py:EXECUTION    <<< FALSE CLEAR: canary VANISHED on TYPES
exemption table: a row rooted at './'         -> docs/consult/test_orphan.py:EXECUTION    <<< FALSE CLEAR: canary VANISHED on TYPES
exemption table: a row rooted at 'docs'       -> docs/consult/test_orphan.py:EXECUTION    <<< FALSE CLEAR: canary VANISHED on TYPES

FALSE CLEARS: 6
```

**Verdicts, one per row:**

| state | verdict |
|---|---|
| git index empty | **guarded** — anti-vacuity raise |
| git not a repository | **guarded** — pinned by `test_a_directory_that_is_not_a_git_repository_is_blind_not_clean` |
| **git binary absent (#131 verbatim)** | **loud but UNPINNED** — `FileNotFoundError`, not `GuardIsBlind`, and no fixture constructs this state. A build with `except OSError: return []` is inert with git present, so the contract can never see it. **Residual, not a blocker** (downstream anti-vacuity still raises). Named in §7. |
| typecheck.sh missing / no decl / empty / wildcard / phantom / decoy-comment | **guarded** — six pins, all fire |
| **typecheck.sh: two `MEMBERS=(` declarations** | **FALSE CLEAR.** bash's *last* assignment wins; the guard reads the *first*. It certifies a wider gate than the one that runs. → **M3** |
| pyproject missing / no table / no key / empty | **guarded** |
| pyproject malformed TOML | **loud but unpinned** — `TOMLDecodeError` escapes as itself. Residual. |
| **testpaths `["."]` / `[""]` / `["/"]`** | **FALSE CLEAR.** The contract pins the whole-tree wildcard for `MEMBERS` (4 params) and has **no analogue for `testpaths`**. LEG B silently covers the whole tree. → **M2** |
| ruff exclusion removed | **guarded** |
| **exemption root `"."` / `"./"`** | **FALSE CLEAR.** `PurePosixPath(".").parts == ()`, so the row matches every path and silences the whole axis. The 11-row malformed-row matrix covers `""`, `"/absolute"`, `"../outside"` — not `"."`. → **M4** |
| exemption root `"docs"` | **BY DESIGN** — a broad but declared, finding-backed exemption. Not a defect; listed so no row is left unverdicted. |

### 3.1 ⚠ MY OWN PROBE FAILED FIRST, AND I CAUGHT IT

The first version of this probe compared the served string to the healthy string and printed
**"FALSE CLEARS: 0"**. It could not see a case that lost **one** axis's canary and kept the other —
which is every one of the six. That is the auditor's instrument failing the same way the author's
might. Fixed to a **per-axis** canary comparison; the code in §A.3 is the fixed version, and the
comment recording the failure is in it.

### 3.2 The `unmodelled_mypy_configuration` refusal is a FORBIDDEN-NAME LIST, and it loses

The contract pins exactly two shapes: `[tool.mypy] exclude` and `[[tool.mypy.overrides]]
ignore_errors`. Measured against the reference build (controls at the bottom — my probe demonstrably
fires):

```
follow_imports = "skip"   (global)          -> ACCEPTED SILENTLY  <<<
ignore_errors = true      (global)          -> ACCEPTED SILENTLY  <<<
disable_error_code = [...] (global)         -> ACCEPTED SILENTLY  <<<
override follow_imports = "skip"            -> ACCEPTED SILENTLY  <<<
override disable_error_code = [...]         -> ACCEPTED SILENTLY  <<<
CONTROL: exclude (modelled)                 -> REFUSES
CONTROL: override ignore_errors (modelled)  -> REFUSES
```

**A global `[tool.mypy] ignore_errors = true` turns the entire type gate off while this guard
certifies a fully-gated tree.** It is the *same setting* the contract already pins one level down.
This is `CLAUDE.md`'s instrument lesson verbatim — *"when you catch yourself enumerating what is
FORBIDDEN, you have already lost… allowlist the safe"* — and the safe set here is small and already
written down: the contract's own positive control names the three harmless keys the repo uses. →
**M5**.

---

## 4. MISSING PINS — numbered, actionable, both legs proven

Each is validated **RED on the shipped-shape reference build** (the pin discriminates) and
**GREEN on a `reference+` build** (the pin is satisfiable and does not over-reach). Control that
`reference+` does not over-reach:

```
CONTROL — does reference+ still satisfy the SHIPPED contract?
  130 passed in 0.82s
```

```
PROPOSED PINS, both legs:
  reference build (shipped shape)      2P 3F  [P_A, P_B, P_C]        <- discriminates
  reference+ build (pins honoured)     5P 0F  []                     <- satisfiable
  reference+ WITH the self-exemption   4P 1F  [P_D]                  <- P_D discriminates
```

### M1 — `test_the_guard_names_no_path_of_its_own_anywhere_in_its_source`
**Catches:** WRONG BUILD #2, the lead's own named wrong build — a guard that hardcodes
`if path in {"scripts/gated_ground.py", "scripts/test_gated_ground.py"}: COVERED`. **Currently
passes all 130 pins** (§2.3).
**Shape:** AST-walk `gg.__file__` (the machinery already exists in
`TestTheInstrumentIsSelfContained._imported_roots`), collect every `ast.Constant` string, assert
none equals the instrument's own file name / stem / repo-relative path. This is the assertion
behind the docstring claim *"the guard contains no mention of its own path anywhere"*, which today
has none. Full body in §A.4.
**Why the existing pin misses it:** `test_the_guard_grants_its_own_files_no_special_exemption` uses
`tools/…` paths, so it detects basename self-exemption only.

### M2 — `test_a_whole_tree_testpath_is_blind_not_clean`
**Catches:** `testpaths = ["."]`, `[""]`, `["/"]`, `[".."]` — LEG B silently covers the entire
tree and reports zero execution findings. The contract already pins this **for `MEMBERS`** with
four parameters; LEG B has no analogue. Parametrise the same four values.
**Receipt:** §3, row `pyproject: testpaths = ['.']` — canary vanished on EXECUTION against a
130/130 build.

### M3 — `test_two_MEMBERS_declarations_are_blind_not_clean`
**Catches:** a guard that parses a `MEMBERS=(…)` line **bash never executes**. Last assignment
wins; a narrowed second declaration reads as the wider first, so a *shrunken* type gate certifies
as unshrunken. The author's report §7 notes *"`grep -nE '^[A-Z_]+=\(' ` finds exactly one array"* —
that is a **fact about today**, not a pin.
**Receipt:** §3, row `typecheck.sh: TWO declarations` — canary vanished on TYPES.

### M4 — `test_an_exemption_root_that_widens_to_the_whole_repository_is_rejected`
**Catches:** `Exemption(root=".")` / `root="./"` — one row silences an entire axis. The
deny-by-default allowlist becomes an off switch. Add to the existing malformed-row `parametrize`
(which already covers `""`, `"/absolute/tree"`, `"../outside"`); the positive control
`test_a_well_formed_row_constructs` already exists and must stay.
**Receipt:** §3, exemption-root rows.

### M5 — `test_an_unmodelled_mypy_setting_is_refused_by_ALLOWLIST_not_by_name`
**Catches:** a *global* `[tool.mypy] ignore_errors = true` (the whole gate off), plus
`follow_imports = "skip"` and `disable_error_code` at either level — five relaxations accepted
silently today (§3.2).
**Shape:** invert the predicate. Enumerate the `[tool.mypy]` and override keys the guard *knows*
are harmless (the contract's own positive control names three: `follow_untyped_imports`,
`ignore_missing_imports`, `disallow_any_unimported`) and **refuse anything else**. Keep
`test_the_relaxations_this_repository_actually_uses_do_not_trip_the_refusal` as the false-gate
control — the allowlist must not turn the gate into one that gets switched off.

### M6 — the `is_under` CALL-SITE pins (three, one per unguarded membership site)
**Catches:** WB28 / WB3 / WB29 — `str.startswith` at the typecheck-root, testpath and
archived-receipts sites. `test_prefix_membership` pins the **helper**; nothing requires `classify`
to use it, and only the *exemption-root* site has a fixture that discriminates
(`scripts_extra/` vs `scripts`).
**Shape (proven, §4.9):** add four files to `workspace_shaped_repository` —
`docs/evaluation/harness.py` (sibling prefix of the `docs/eval` **typecheck root**),
`loremaster/tests_extra/test_probe.py` (sibling prefix of a **testpath**),
`skills/test_workspace_probe.py` (an **ancestor** of a testpath, kills WB27),
`release_probe.py` + `conftest.py` (**repository-root level**, kills WB43) — and one assertion each.
A `receipts_live/` sibling of `docs/plans/v2/receipts` closes WB29.

### M7 — `test_repository_root_level_python_is_ordinary_committed_ground`
**Catches:** WB43 — a build treating top-level `.py` as covered. **No fixture in the contract has a
single repository-root-level `.py`**, and the design sidecar's own draft mutation m3 was exactly
*"`git add` a stray tracked `.py` at the scratch repo ROOT → LEG A red"*. A stray root-level
`conftest.py` / `probe.py` is the single most likely way real ungated ground appears.
(Folded into M6's fixture; listed separately because it is the sidecar's own dropped rider.)

### M8 — the placeholder-trigger / placeholder-reason gap (**a FORK, not a prescription**)
**Catches:** WB33, WB38, WB45 — `reopen_trigger = "TBD"` on a `StatedBound` **or** on an exemption
row, and `reason = "x"`, all pass. The assertions test `.strip()` truthiness while their own
failure messages promise *"a bound with no condition for revisiting it is a hope"* and *"nothing
says when the trade changes"*. That is this repo's **false-gate law**: the message is the spec the
author believed; the assertion admits `"TBD"`.
**I am not prescribing the fix, because both options have a real cost and the choice is a ruling:**
(a) require the trigger to cite a `#\d+` finding number (allowlist-the-safe, mechanical, but a
legitimate bound may have no ledger row); (b) accept it as un-mechanisable and **soften the failure
messages** so they promise only what they check. Doing neither leaves a false gate. → §7.

### M9 — `test_the_message_teaches_and_does_not_merely_contain_the_keywords` (**weakest, listed for completeness**)
**Catches:** WB36 — a message that keyword-stuffs the five required substrings
(`registration; does not prove; finding number; re-open trigger`) and carries no disclaimer,
passes. Under the CONSUMER LAW the message is a served surface read by an agent that will act on
it. A defensible strengthening: require the disclaimer as a **contiguous phrase** rather than two
separate substrings. I rank this lowest: substring pins on prose are inherently weak, and
over-tightening is itself a false-gate risk.

### 4.9 The P2 PERTURBATION PAIR — receipts for M6/M7

Perturbed the contract's most load-bearing fixture in a **scratch copy** (the repo's copy was never
touched), then proved both legs:

```
PAIR LEG 2 — the perturbed contract on the CORRECT reference build (must be GREEN):
    reference build / new pins only                  4P   0F  []
    reference build / WHOLE perturbed contract     134P   0F  []

PAIR LEG 1 — the same perturbed pins against each surviving wrong build (must be RED):
    WB28-typecheck-root-startswith    3P 1F  [test_a_sibling_prefix_of_a_TYPECHECK_ROOT_is_not_covered]
    WB3-startswith-only-in-leg-B      3P 1F  [test_a_sibling_prefix_of_a_TESTPATH_is_not_covered]
    WB27-legB-reverse-containment     2P 2F  [test_an_ancestor_of_a_testpath_is_not_covered_by_it,
                                              test_repository_root_level_python_is_ordinary_committed_ground]
    WB43-root-level-py                3P 1F  [test_repository_root_level_python_is_ordinary_committed_ground]
    WB2-startswith-everywhere         2P 2F  [both sibling-prefix pins]
```

**Leg 2 is the leg that makes leg 1 mean something** — without it a red is just a botched
expectation. The whole perturbed contract is 134/134 on a correct build, so the four new pins add
no false positives.

### 4.10 My own P_A pin was RED FOR THE WRONG REASON, and I caught it

First run: `test_P_A_a_whole_tree_testpath_is_blind_not_clean` was RED on **both** legs — including
`reference+`, which implements the guard. Cause: my fixture called `_minimal_repository(tmp_path /
f"case{...}")` on a directory that did not exist, so `git init` raised `FileNotFoundError` and
`pytest.raises(GuardIsBlind)` failed. **A pin that is red for a fixture reason is indistinguishable
from a pin that is doing its job.** Fixed (`case.mkdir()`); the pair then held cleanly. Reported
rather than quietly corrected, because it is the exact class I am here to find in others.

---

## 5. P-PKG — my table, and the DIFF against the author's §2

I built my own implementation and chose mechanisms for it before writing this table; the read-order
caveat is stated in §1. The diff is what matters, and it has **two rows the author's survey does
not contain**.

| mechanism | my verdict | author's verdict | DIFF |
|---|---|---|---|
| TOML parsing | `tomllib` → **replace** (READ: `registration_sites.py::declared_members`, and I used it) | same | agree |
| glob match of a filename | `fnmatch` → **replace** (READ: `fnmatch.fnmatch` signature; used in my build) | same | agree |
| committed-file enumeration | `git ls-files -z` → **replace** (READ: measured NUL vs quoted line output on a newline path — my WB9 reproduces the divergence) | same | agree |
| pytest's `python_files` default | my build imported `_pytest.config.get_config([])._parser._inidict`; **revision 2's constant + contract-side drift guard is BETTER** and I adopted it — it removes a private-API runtime dependency while keeping the value derived on every gate run | constant + drift guard | **author ahead of me.** Credit where due |
| mypy's real discovery / pytest's real collection | **keep_with_trigger** — this is a registration guard, and shelling to pytest from inside pytest is the wrapper seam §Q3.1 forbids | same, triggers named | agree |
| mutation proving | `scripts/mutation_proof.py` → **replace** hand-run blocks. ⚠ **I did not use it** — I wrote my own 42-variant driver because I needed *survivor* detection (zero-red), which is the inverse of `mutation_proof.py`'s declared-RED diff. Instrument pasted §A.2 | replace; used for MP1–MP8 | **divergence, disclosed** |
| **path-component membership (`is_under`)** | **`PurePosixPath.is_relative_to` → replace.** READ: replayed the contract's own 12-row `test_prefix_membership` matrix through the stdlib method — **0 mismatches**, stdlib since 3.9. The spec (§Q3.3) says *"`Path.parts` prefix"*, prescribing a hand-roll where a stdlib primitive is exact | **no row** | **⚠ MISSING FROM THE AUTHOR'S SURVEY.** Not a blocker (the wrapper name `is_under` is right to keep and its 12-row matrix already pins the behaviour) — but the contract should not prescribe hand-rolled component arithmetic when one stdlib call is byte-equivalent. **Recommend: keep `is_under` as the seam, implement it as `PurePosixPath(path).is_relative_to(tree)`** |
| **`MEMBERS` array token split** | **`shlex.split` → replace `str.split()`.** READ: `shlex.split('lorerunes "docs/my eval" loremaster')` → `['lorerunes', 'docs/my eval', 'loremaster']`; `str.split` → `['lorerunes', '"docs/my', 'eval"', 'loremaster']` | `bespoke`, with the claim *"the only stdlib-shaped alternative is `source`-ing the runner, which EXECUTES the gate as a side effect of reading it"* | **⚠ THE CLAIM IS MEASURABLY FALSE.** The read-column cites the real runner and a grep — not `shlex`'s API. This is precisely the "asserting a package limitation without reading the API" class. The *anchored regex* half of the bespoke verdict stands; the *token split* half should be `shlex.split`, and `FixtureRepository.render_members_line` should gain a quoted-entry case |
| the property itself | **domain logic** — no package models "is this tree registered with this repo's gates" | same | agree |

**Net:** the author's survey is strong and its `keep_with_trigger` verdicts are legitimate and
well-triggered. Two rows are missing/wrong, both in the *"one level down"* position the role spec
warns about — a correctly-surveyed mechanism (`bespoke` MEMBERS parse) whose sub-step (`str.split`)
was never surveyed, and a mechanism (path membership) that never got a row at all.

---

## 6. P1b — THE QUANTIFIER TABLE (∀-over-inputs vs guarded-by-known-failure-mode)

Every invariant, classified. **Every `guarded` row carries a receipt**: either a surviving wrong
build that walks the same bad outcome through an unguarded door, or the attempted door-build naming
the pin that killed it.

| # | invariant | ∀ / guarded | receipt |
|---|---|---|---|
| I1 | every tracked `.py` has **exactly one fate per axis**, none vanished, none invented | **∀ over inputs** | `assert_every_tracked_file_is_accounted_for` runs on every fixture *and* on `REPO_ROOT`. Door-builds killed: WB35 (report ≠ classify, 17F), WB20 (drops hostile paths, 1F), WB32 (invents untracked, 2F) |
| I2 | every UNGATED fate is **reported** | **∀ over inputs** | same helper; WB11 (drops an axis) 25F |
| I3 | LEG A covered ⟺ under a parsed typecheck root | **GUARDED** — membership discriminated at the *exemption* site only | ❗**WB28 SURVIVED 130/130**; divergence `docs/evaluation/harness.py` UNGATED→COVERED. → M6 |
| I4 | LEG B covered ⟺ under a parsed testpath | **GUARDED** — same | ❗**WB3 SURVIVED**, ❗**WB27 SURVIVED**; divergences in §2.2. → M6 |
| I5 | archived-receipts exemption membership | **GUARDED** — same | ❗**WB29 SURVIVED**; `receipts_live/` UNGATED→EXEMPT. → M6 |
| I6 | exemption-table membership is component-wise | **∀** (a fixture forces it) | WB24 killed by `test_a_sibling_prefix_directory_is_neither_gated_nor_exempt` |
| I7 | COVERED beats every EXEMPT fate | **∀** | WB14 (2F), WB23 (2F) killed |
| I8 | an exemption is scoped to its axis | **∀** | WB13 killed by `test_an_exemption_is_scoped_to_its_axis` |
| I9 | the table refuses malformed rows | **GUARDED** — an 11-shape forbidden list | WB6 killed; ❗**WB38 / WB45 SURVIVED** (`"TBD"`, `"x"`); ❗exemption root `"."` accepted (§3). → M4, M8 |
| I10 | blind ≠ clean on unparseable inputs | **GUARDED** — per named input | 12 pins fire; ❗**3 unguarded doors** found by construction (§3). → M2, M3 |
| I11 | the enumeration is tracked-only and `.py`-only | **GUARDED** | WB32 killed; ❗**WB31 SURVIVED** (`".py" in record`) |
| I12 | a hostile path survives intact and cannot forge a row | **∀ over the render** | WB9 (2F), WB10 (1F), WB20 (1F) all killed. **Strongest cluster in the contract** |
| I13 | the guard grants itself no special exemption | **GUARDED** — by basename, in a *different* tree | ❗**WB4b SURVIVED 130/130** — the lead's named wrong build. → M1 |
| I14 | the message carries the disclaimer and both ways out | **GUARDED** — five substrings | ❗**WB36 SURVIVED** (keyword stuffing). → M9 |
| I15 | threat model + bounds stated, each with a re-open trigger | **GUARDED** — non-blankness | WB26 killed (disclaimer-as-threat-model); ❗**WB33 SURVIVED** (`"TBD"`). → M8 |
| I16 | the instrument imports **only** the stdlib | **∀ over the AST** — derived from `sys.stdlib_module_names`, never an allowlist | **fired on me for real**: my first reference build imported `_pytest` and this pin caught it (`the instrument imports ['_pytest']`). Best pin in the file |
| I17 | the instrument is inside a `testpaths` entry | **∀-trivial** (one assertion, one fact) | green on the real tree; would redden if `scripts` left `testpaths` |
| I18 | the real repository is fully gated | **∀ over the real tree** | 0 findings at `f033a87` (my measurement); the author's `5a850c3` replay shows 12 findings, so the pin **can** fire |
| I19 | findings are deterministic and path-ordered | **∀** | WB25 killed |
| I20 | every reader answers for `repo_root`, not the process cwd | **∀ over all 6 readers** | parametrised; `distinctly_configured_repository` differs on **every** parsed value, so it is not a coincidence pass |
| I21 | mypy configuration the guard cannot model ⇒ refuse | **GUARDED** — a 2-name forbidden list | ❗**5 relaxations accepted silently**, incl. global `ignore_errors = true` (§3.2). → M5 |
| I22 | LEG A never returns `NOT_APPLICABLE` | **∀** (helper) | WB34 killed |
| I23 | the receipts class is ONE law-backed address, non-vacuous, ruff-backed | **∀ + anti-vacuity** | WB30 (growing list) 3F killed; the ruff-exclusion and empty-class raises both fire (§3) |
| I24 | LEG B's patterns come from pytest, not a constant | **∀ + drift guard** | WB17 killed (2F); the drift guard re-derives from installed pytest each run |
| I25 | a file-granularity `MEMBERS` entry covers itself and not its siblings | **∀** | WB18 (3F), WB23 (2F) killed |

**Guarded rows: 9. Rows whose guard a surviving wrong build walks around: 7** (I3, I4, I5, I9, I11,
I13, I14, I15, I21 — with I11/I14 lower-severity). Per the role spec that alone forces
INSUFFICIENT.

---

## 7. SURFACED TO LEAD — questions, not decisions (scope is yours)

1. **The `.sh` axis is NOT stated anywhere in the contract.** `git grep -n 'shellcheck\|\.sh axis'`
   over the contract → **zero hits**; `REQUIRED_BOUND_IDENTIFIERS` names four bounds, none about
   file types. F3.9 ruled `.sh` out of the model, and a shell gate has since landed (`2bc7e97`,
   derived `git ls-files '*.sh'` + `shellcheck-py`). The instrument's headline claim is *"every
   committed `.py`"*, so a reader meets an unstated scope limit. Per *WHEN YOU CANNOT CLOSE A HOLE,
   PIN IT*: **should `REQUIRED_BOUND_IDENTIFIERS` gain a `file-types-modelled` bound** ("this
   quantifies over tracked `.py`; `.sh` is covered by `typecheck.sh`'s own derived shellcheck leg
   and by nothing on the execution axis; `.pyi` and every other extension are unmodelled"), with
   the re-open trigger being a second file type acquiring a gate? One identifier + one docstring
   sentence.
2. **TWO MECHANISMS FOR "THIS INSTRUMENT TYPES ITSELF", in the same directory.**
   `scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED` already solves this
   problem *inside a test*, running `mypy` with `MYPYPATH=scripts:{declared_path}` — **and its
   docstring explicitly rejects the approach packet 44 is about to take**: *"Rather than add
   `scripts` to the gate … or **hand-list files inside it (the enumeration this repo has the most
   receipts against)**, the check is scoped to exactly the two files this contract owns."* Packet 44
   hand-lists two files inside `scripts/` in the gate. Per ONE IMPLEMENTATION, duplication is a
   **design decision to escalate**: do the two instruments converge (both use `MEMBERS` file
   entries, and `test_forgery_door_sweep`'s in-test mypy leg is deleted), or is the divergence
   deliberate? Either way one of the two docstrings is about to become false.
3. **THREE MUTATION-PROOF VERDICTS IN THE CONTRACT REPORT HAVE A BLANK OBSERVED COLUMN.** §6.2's
   table: MP6 `2 ids | — | PROOF HELD — fired EXACTLY`, MP7 `2 ids | — | …`, MP8 `3 ids | — | …`.
   A verdict of *"fired EXACTLY"* with no observed counts is the #194 shape — *a mutation proof
   needs evidence the mutation LANDED* — inside a report that cites #194. Also **the counts do not
   agree with themselves**: §5 says *"8 mutation proofs, 8 declared RED sets, 8 exact matches"*,
   §6.2's heading says *"5 run through `scripts/mutation_proof.py`"*, and the package-survey row
   says *"All five proofs in §6.2"*. **Ask the author to paste MP6–MP8's tails or downgrade the
   verdicts.** (I did not reproduce MP1–MP8; my own 42-variant matrix is independent evidence of
   the same properties, and it agrees with the author wherever they overlap.)
4. **The MYPYPATH consequence of the F1 ruling — independently reproduced, and it MATCHES the
   author's §R.3 exactly**, so this is corroboration, not a new finding:

   ```
   $ mypy scripts/gated_ground.py                       -> resolves standalone, no MYPYPATH ✓
   $ mypy scripts/test_gated_ground.py                  -> Cannot find implementation or library
                                                           stub for module named "gated_ground"
                                                           + 13 no-any-unimported cascade errors
   $ MYPYPATH=scripts mypy scripts/test_gated_ground.py -> those 14 vanish
   ```

   **What is still open:** `TestTheInstrumentIsSelfContained`'s docstring gives the rationale *"It
   must typecheck as its own `MEMBERS` iteration without a `MYPYPATH`"* — **true for the
   instrument, false for the contract file**, and nothing in the contract asserts the new legs
   actually typecheck. The builder can add both `MEMBERS` entries, watch every pin go green, and
   ship a `typecheck.sh` that exits 1. **Cheapest pin: assert `MEMBER_MYPYPATH` carries an entry
   for any file-granularity `MEMBERS` entry that imports a sibling module in its own directory**
   (derived, matching the `docs/eval` precedent), or run `mypy` over the file entries in one test.
5. **Two prose claims go stale the moment this lands** (P8d natural-language class; neither is
   asserted, so nothing reddens):
   `loremaster/tests/test_secret_typing.py` — *"`scripts/` is scanned even though it is NOT one of
   `scripts/typecheck.sh`'s `MEMBERS`, so mypy never sees it"* → false for two files after landing.
   `scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED` docstring — *"`scripts/` is
   OUTSIDE `scripts/typecheck.sh` (#188 measured **41** mypy errors there), so nothing in the
   canonical gate reads these two files"* → the exclusion becomes partial, **and the `41` is the
   drifted count** (45 at `5a850c3` per the lead; 24 under `MYPYPATH=scripts`) that the contract's
   own `test_no_exemption_reason_carries_a_measured_count` exists to ban. Same undated count at
   `scripts/test_search_score_survey.py` (*"`scripts/` is not a `typecheck.sh` member (#221)"*).
6. **`git` binary absent is unpinned** (§3). Not a false clear today, but it is #131 verbatim and no
   fixture constructs the state. A `except OSError: return []` build is inert with git present, so
   the contract structurally cannot see it. Worth a `monkeypatch.setenv("PATH", …)` pin, or an
   explicit bound.
7. **M8 is a genuine fork** (placeholder triggers/reasons): mechanise via a required `#\d+` in the
   trigger, or soften the failure messages so they promise only what they check. Doing neither
   leaves a false gate in a contract whose own §Q3.7 exists to prevent exactly that.

---

## 8. P6 / P6b — corpse sweep and orphaned virtues

**P6b (orphaned virtues) is NOT APPLICABLE in the usual sense: packet 44 deletes and replaces no
code.** The change is additive — one new instrument, one new contract, two new `MEMBERS` entries.
There is no Phase-0 removed-behavior inventory to diff against, and I state that rather than
manufacture one. The nearest thing to a replacement is `typecheck.sh`'s `MEMBERS` array gaining
file-granularity entries, whose only prior behaviour (directory-only roots) is preserved and pinned
by `TestATypecheckRootMayBeASingleFile`.

**P6 corpse sweep** — `git grep -nI --fixed-strings -e MEMBERS -e testpaths -e typecheck.sh --
'*.py'`, bare and anchor-free. **Every hit gets an individual verdict; "the rest look fine" is not
used.**

| file:symbol | verdict |
|---|---|
| `docs/eval/test_smoke_p8b.py` (module docstring, testpaths/typecheck.sh prose) | **CURRENT** — updated by the config wave; names packet 44 explicitly |
| `loremaster/tests/test_backoff_seam.py` (`scripts` used to be outside testpaths) | **CURRENT** — carries *"⚠ DISCHARGED 2026-07-25 by #199"* |
| `loremaster/tests/test_secret_resolution_seam.py` (R6 skills commentary, two sites) | **CURRENT** — already says *"packet 44 added the testpaths entries on 2026-07-29"* |
| `loremaster/tests/test_secret_typing.py::_SCANNED_MEMBERS` | **CURRENT and load-bearing** — includes `("scripts","scripts")`, so the new instrument **will** be scanned by packet 42's ∀ secret-typing pins. The builder must satisfy them; not a corpse |
| `loremaster/tests/test_secret_typing.py` (comment: *"mypy never sees it"*) | **GOES STALE AT LANDING** — prose only, nothing reddens. §7.5 |
| `loremaster/tests/test_secret_typing.py` (comment: *"`skills/` … was ungated ground when that ruling was written"*) | **CURRENT** — past tense, historically accurate |
| `scripts/test_forgery_door_sweep.py::TestThisInstrumentIsTYPECHECKED` (docstring) | **GOES STALE AT LANDING + carries the drifted `41`** — and its stated policy contradicts packet 44's. §7.2, §7.5 |
| `scripts/test_search_score_survey.py` (docstring: *"not a `typecheck.sh` member (#221)"*) | **GOES STALE AT LANDING** — prose only |
| `loremaster/tests/test_render_mypy_layer.py` (mirrors typecheck.sh's command shape) | **UNAFFECTED** — runs `mypy loremaster`; new entries do not touch it |
| `docs/plans/v2/receipts/2026-07-28-packet11ib/consult-11ib/tools/*.py` (5 files, *"in neither testpaths nor …"*) | **CORRECT AND MUST STAY** — archived receipts, preserved byte-faithful by repo law; they are the archived-receipts exemption class |
| `loremaster/{memory/local.py,server.py,store/lease.py}`, `_memory_fakes.py`, `test_blocks_edge.py`, `test_comms_tool.py`, `test_retry_seam.py`, `test_anchored_pattern_seam.py`, `_logging_fixtures.py` | **UNRELATED** — the word "MEMBERSHIP"/"MEMBERS" in a different domain (set membership, cycle members, the lock interface). No gate semantics. Verdicted individually, not wholesale |

**No test in the tree asserts the OLD ungated state**, so nothing is green *because* it asserts the
corpse. The stale material is all prose, which is precisely the P8d class this repo has receipts
against — hence §7.5 rather than silence.

---

## 9. P3 — branch reachability

Every fate is forced by a named fixture (`test_each_named_fate_is_forced_by_a_fixture`, 9 params,
plus `test_the_execution_axis_exempt_table_fate_is_reachable` for the one fate the shipped table
cannot reach). I found **no unreached fate**. The unreached *branches* are the ones §3 names: the
whole-tree-testpath guard, the second-declaration guard, the whole-tree-exemption-root guard, and
the non-`exclude`/non-`ignore_errors` mypy relaxations — all of which are unreachable because the
branch **does not exist**, not because no test reaches it. That is the difference between a dead
branch and a missing one, and here it is the latter.

`ungated_ground(repo_root)` is called **without** `exemptions=` at one site
(`test_an_untracked_file_is_out_of_scope_by_construction`), so the parameter must carry a default.
A build defaulting to `()` rather than `EXEMPTIONS` passes that assertion either way — a **residual**
ambiguity, not a defect: no pin distinguishes the two defaults. One line would
(`assert gg.ungated_ground(repo) == gg.ungated_ground(repo, exemptions=gg.EXEMPTIONS)`).

---

## 10. What the contract does EXCEPTIONALLY well (so the fix wave does not damage it)

Stated because a fix wave that guts these to close §4 would be a net loss:

- `TestTheInstrumentIsSelfContained` **caught my own reference build** on its first run
  (`the instrument imports ['_pytest']`). Derived from `sys.stdlib_module_names`, walking the whole
  AST including lazy imports — allowlist-the-safe done right.
- `test_readers_answer_for_repo_root_not_for_the_process_cwd` × 6 readers against a fixture where
  **every** parsed value differs. Coincidence is explicitly designed out.
- The hostile-path cluster (newline survival + header-count forgery) killed three separate wrong
  builds and is mechanism-agnostic about the fix.
- `assert_every_tracked_file_is_accounted_for` is a genuine ∀-over-inputs helper conditioned on no
  cause, applied everywhere — it killed WB35 with 17 reds and WB11 with 25.
- The positive controls are real: `test_the_healthy_control_repository_raises_nothing`,
  `test_a_well_formed_row_constructs`, `test_the_relaxations_this_repository_actually_uses_do_not_trip_the_refusal`
  (WB19 proves that last one fires: an over-refusing build lost 26 pins).
- `test_every_shipped_row_is_load_bearing` proves the exemption row by **mutation**, not inspection.

---

# VERDICT: **CONTRACT INSUFFICIENT**

Eleven wrong builds pass all 130 pins, seven with proven divergence on constructed inputs; six
Leg-2 false clears and five silently-accepted mypy relaxations sit against a build that passes the
contract. The blocking items are **M1** (the lead's own named WRONG BUILD #2 is invisible),
**M6/M7** (three of four `is_under` call sites undiscriminated + no root-level fixture), **M2/M3/M4**
(three unguarded blind-not-clean doors) and **M5** (a forbidden-name list where an allowlist is
available). M8 is a fork for the lead; M9 is advisory.

Re-run this grading after the fix wave — and note §0.1: **this verdict binds md5
`77a0cde8bdc6a7f2a12bcb7a8cda5682` only.**

---

# APPENDIX A — INSTRUMENTS (pasted verbatim; brief-base §1)

I am read-only on this repository, so none of these could be committed to `scripts/`. They lived in
`/tmp/adv44/` (unrecoverable by construction) and are therefore reproduced here in full. Each runs
against a tree built by `git archive HEAD | tar -x` into a fresh `git init` — **never** a copy of
this worktree.

## A.0 Building the isolated tree (the #284-safe recipe)

```bash
mkdir -p /tmp/adv44/ref
git archive HEAD | tar -x -C /tmp/adv44/ref
cp scripts/test_gated_ground.py /tmp/adv44/ref/scripts/test_gated_ground.py   # untracked here
cd /tmp/adv44/ref && git init -q -b main . && git add -A
[ -d /tmp/adv44/ref/.git ] || { echo "FAIL: .git is a FILE — #284 poison"; exit 1; }
# -> OK: .git is a DIRECTORY ; 291 tracked .py
```

Then the ruled `typecheck.sh` edit, applied only in the scratch tree:

```
MEMBERS=(lorerunes lorescribe loresigil loremaster skills docs/eval scripts/gated_ground.py scripts/test_gated_ground.py)
```
preceded by a contiguous comment block naming both entries and citing `#188` as the dissolution
trigger (required by `test_every_file_granularity_members_entry_carries_a_dissolution_trigger`).

## A.1 `reference_gated_ground.py` — the known-correct control (130/130)

> ⚠ **This is an ADVERSARY CONTROL, not a specification.** It exists to prove the contract is
> satisfiable and to be the "correct build" leg of every perturbation. The builder should build
> from the contract, not from this.

```python
"""ADVERSARY REFERENCE BUILD of the packet-44 gated-ground guard.

THREAT MODEL:
This gate is for the HONEST ENGINEER who commits a load-bearing .py into a tree no gate covers, or only half the gates cover, believing the repo's gates see it. It is NOT a security boundary: anyone who can commit here can delete this test.

BOUNDS, each with a named re-open trigger:

registration-not-execution:
This proves REGISTRATION in the gates' configuration; it does not prove mypy or pytest ran, or passed.

execution-axis-covers-test-shaped-files-only:
LEG B quantifies over test-shaped files and conftest.py only; execution coverage of ordinary library modules is a coverage-measurement problem this instrument does not claim.

collection-convention:
A file full of asserts named outside pytest's collection convention is invisible to pytest everywhere, which is a different defect class.

lore-index-axis:
lore's index is a third gate direction this instrument does not model.
"""

from __future__ import annotations

import fnmatch
import re
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath


class GuardIsBlind(RuntimeError):
    """The guard cannot see. A blind guard is never a clean tree."""


class InvalidExemption(ValueError):
    """An exemption row the table's own validation refuses."""


class GateAxis(Enum):
    TYPES = "LEG A — types"
    EXECUTION = "LEG B — execution"

    @property
    def label(self) -> str:
        return self.value


class Fate(Enum):
    COVERED = "covered"
    EXEMPT_TABLE = "exempt (pinned table)"
    EXEMPT_ARCHIVED_RECEIPTS = "exempt (archived receipts)"
    UNGATED = "ungated"
    NOT_APPLICABLE = "not applicable"


_FINDING_PATTERN = re.compile(r"#\d+")


@dataclass(frozen=True)
class Exemption:
    root: str
    axis: GateAxis
    finding: str
    reason: str
    reopen_trigger: str

    def __post_init__(self) -> None:
        if not self.root.strip():
            raise InvalidExemption("an exemption row needs a root")
        if self.root.startswith("/"):
            raise InvalidExemption(f"exemption root {self.root!r} is absolute")
        if ".." in PurePosixPath(self.root).parts:
            raise InvalidExemption(f"exemption root {self.root!r} escapes the repository")
        if not _FINDING_PATTERN.fullmatch(self.finding):
            raise InvalidExemption(
                f"exemption {self.root!r} cites {self.finding!r}, not a finding number"
            )
        if not self.reason.strip():
            raise InvalidExemption(f"exemption {self.root!r} gives no reason")
        if re.search(r"\d", self.reason):
            raise InvalidExemption(
                f"exemption {self.root!r} carries a number in its reason: {self.reason!r}"
            )
        if not self.reopen_trigger.strip():
            raise InvalidExemption(f"exemption {self.root!r} names no re-open trigger")


@dataclass(frozen=True)
class StatedBound:
    identifier: str
    summary: str
    reopen_trigger: str
    finding: str = ""


@dataclass(frozen=True)
class UngatedFile:
    path: str
    axis: GateAxis
    message: str


@dataclass(frozen=True)
class FileVerdict:
    path: str
    fates: Mapping[GateAxis, Fate]


ARCHIVED_RECEIPTS_ROOT = "docs/plans/v2/receipts"

THREAT_MODEL = (
    "This gate is for the HONEST ENGINEER who commits a load-bearing .py into a tree no "
    "gate covers, or only half the gates cover, believing the repo's gates see it. It is "
    "NOT a security boundary: anyone who can commit here can delete this test."
)

STATED_BOUNDS: tuple[StatedBound, ...] = (
    StatedBound(
        identifier="registration-not-execution",
        summary=(
            "This proves REGISTRATION in the gates' configuration; it does not prove mypy "
            "or pytest ran, or passed."
        ),
        reopen_trigger="a demand to prove COLLECTION or EXECUTION rather than registration",
    ),
    StatedBound(
        identifier="execution-axis-covers-test-shaped-files-only",
        summary=(
            "LEG B quantifies over test-shaped files and conftest.py only; execution "
            "coverage of ordinary library modules is a coverage-measurement problem this "
            "instrument does not claim."
        ),
        reopen_trigger="a coverage-measurement gate lands in this repository",
    ),
    StatedBound(
        identifier="collection-convention",
        summary=(
            "A file full of asserts named outside pytest's collection convention is "
            "invisible to pytest everywhere, which is a different defect class."
        ),
        reopen_trigger="a naming-convention gate lands",
    ),
    StatedBound(
        identifier="lore-index-axis",
        summary="lore's index is a third gate direction this instrument does not model.",
        reopen_trigger="#260 lands; then the index becomes a modelled axis",
        finding="#260",
    ),
)

EXEMPTIONS: tuple[Exemption, ...] = (
    Exemption(
        root="scripts",
        axis=GateAxis.TYPES,
        finding="#188",
        reason="standing disposition: its own work item, config half first",
        reopen_trigger="the #188 cleanup lands; delete this row and the leg goes live",
    ),
)

_MEMBERS_DECLARATION = re.compile(r"^MEMBERS=\(([^)]*)\)", re.MULTILINE)
_WHOLE_TREE = {".", "..", "/"}

#: pytest's own declared default, cited: ``_pytest.python.pytest_addoption`` declares
#: ``default=["test_*.py", "*_test.py"]``. Carried as a constant because the instrument is
#: stdlib-only by ruling; the contract re-derives it from the installed pytest every run.
PYTEST_DEFAULT_TEST_FILE_PATTERNS: tuple[str, ...] = ("test_*.py", "*_test.py")


def is_under(path: str, tree: str) -> bool:
    """Path-component-wise prefix membership. Never ``str.startswith``."""
    path_parts = PurePosixPath(path).parts
    tree_parts = PurePosixPath(tree).parts
    return path_parts[: len(tree_parts)] == tree_parts


def _manifest(repo_root: Path) -> Mapping[str, object]:
    manifest = repo_root / "pyproject.toml"
    if not manifest.is_file():
        raise GuardIsBlind(
            f"no pyproject.toml at {repo_root} — the GUARD IS BLIND, not the tree clean"
        )
    with manifest.open("rb") as handle:
        return tomllib.load(handle)


def _table(data: Mapping[str, object], *path: str) -> Mapping[str, object] | None:
    node: object = data
    for key in path:
        if not isinstance(node, Mapping) or key not in node:
            return None
        node = node[key]
    return node if isinstance(node, Mapping) else None


def typecheck_roots(repo_root: Path) -> list[str]:
    runner = repo_root / "scripts" / "typecheck.sh"
    if not runner.is_file():
        raise GuardIsBlind(
            "scripts/typecheck.sh is missing, so no MEMBERS declaration can be read — the "
            "GUARD IS BLIND, not the tree clean"
        )
    text = runner.read_text(encoding="utf-8")
    match = _MEMBERS_DECLARATION.search(text)
    if match is None:
        raise GuardIsBlind(
            "no line-anchored MEMBERS=(…) declaration in scripts/typecheck.sh — the GUARD "
            "IS BLIND, not the tree clean"
        )
    roots = match.group(1).split()
    if not roots:
        raise GuardIsBlind(
            "the MEMBERS=() declaration in scripts/typecheck.sh is empty — the GUARD IS "
            "BLIND, not the tree clean"
        )
    for root in roots:
        if root in _WHOLE_TREE or root.startswith("/") or ".." in PurePosixPath(root).parts:
            raise GuardIsBlind(
                f"MEMBERS entry {root!r} widens to the whole tree; every file would read as "
                f"gated. The GUARD IS BLIND, not the tree clean"
            )
        if not (repo_root / root).exists():
            raise GuardIsBlind(
                f"MEMBERS entry {root!r} names nothing in this checkout — the gate iterates "
                f"it and checks nothing. The GUARD IS BLIND, not the tree clean"
            )
    return roots


def pytest_testpaths(repo_root: Path) -> list[str]:
    table = _table(_manifest(repo_root), "tool", "pytest", "ini_options")
    if table is None:
        raise GuardIsBlind(
            "pyproject.toml declares no [tool.pytest.ini_options] table, so testpaths "
            "cannot be read — the GUARD IS BLIND, not the tree clean"
        )
    if "testpaths" not in table:
        raise GuardIsBlind(
            "[tool.pytest.ini_options] declares no testpaths — the GUARD IS BLIND, not the "
            "tree clean"
        )
    raw = table["testpaths"]
    testpaths = [str(entry) for entry in raw]
    if not testpaths:
        raise GuardIsBlind("testpaths is empty — the GUARD IS BLIND, not the tree clean")
    for testpath in testpaths:
        if not (repo_root / testpath).is_dir():
            raise GuardIsBlind(
                f"testpaths entry {testpath!r} is not a directory in this checkout; pytest "
                f"collects nothing there. The GUARD IS BLIND, not the tree clean"
            )
    return testpaths


def workspace_members(repo_root: Path) -> list[str]:
    table = _table(_manifest(repo_root), "tool", "uv", "workspace")
    if table is None or "members" not in table:
        raise GuardIsBlind("pyproject.toml declares no [tool.uv.workspace] members")
    return [str(member) for member in table["members"]]


def ruff_excluded_trees(repo_root: Path) -> list[str]:
    table = _table(_manifest(repo_root), "tool", "ruff")
    if table is None or "extend-exclude" not in table:
        raise GuardIsBlind("pyproject.toml declares no [tool.ruff] extend-exclude")
    return [str(tree) for tree in table["extend-exclude"]]


def pytest_test_file_patterns(repo_root: Path) -> list[str]:
    table = _table(_manifest(repo_root), "tool", "pytest", "ini_options")
    if table is not None and "python_files" in table:
        return [str(pattern) for pattern in table["python_files"]]
    return list(PYTEST_DEFAULT_TEST_FILE_PATTERNS)


def tracked_python_files(repo_root: Path) -> list[str]:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "ls-files", "-z"],
        capture_output=True,
        check=False,
    )
    if completed.returncode != 0:
        raise GuardIsBlind(
            f"`git ls-files` failed at {repo_root} (exit {completed.returncode}) — the "
            f"GUARD IS BLIND, not the tree clean: "
            f"{completed.stderr.decode('utf-8', 'replace').strip()}"
        )
    records = [
        record.decode("utf-8", "surrogateescape")
        for record in completed.stdout.split(b"\0")
        if record
    ]
    return sorted(record for record in records if record.endswith(".py"))


def unmodelled_mypy_configuration(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[str]:
    del exemptions
    mypy = _table(_manifest(repo_root), "tool", "mypy")
    unmodelled: list[str] = []
    if mypy is None:
        return unmodelled
    if "exclude" in mypy:
        unmodelled.append(
            f"[tool.mypy] declares exclude = {mypy['exclude']!r}, which this guard does not "
            f"model: a file inside a typecheck root can be skipped by mypy while passing a "
            f"path-membership test. Extend it or remove the exclude."
        )
    overrides = mypy.get("overrides", [])
    if isinstance(overrides, list):
        for override in overrides:
            if isinstance(override, Mapping) and override.get("ignore_errors"):
                modules = override.get("module", [])
                named = modules if isinstance(modules, list) else [modules]
                unmodelled.append(
                    f"[[tool.mypy.overrides]] sets ignore_errors for "
                    f"{', '.join(str(module) for module in named)}, which this guard does "
                    f"not model. Extend it or remove the exclude."
                )
    return unmodelled


def _preflight(repo_root: Path) -> None:
    unmodelled = unmodelled_mypy_configuration(repo_root)
    if unmodelled:
        raise GuardIsBlind(
            "this guard does not model the mypy configuration in this checkout, so its LEG "
            "A verdict is not sound: " + " | ".join(unmodelled)
        )
    excluded = ruff_excluded_trees(repo_root)
    if ARCHIVED_RECEIPTS_ROOT not in excluded:
        raise GuardIsBlind(
            f"{ARCHIVED_RECEIPTS_ROOT!r} is not in [tool.ruff] extend-exclude {excluded!r}; "
            f"the archived-receipts class has lost its law backing. The GUARD IS BLIND"
        )


def _is_test_shaped(path: str, patterns: Sequence[str]) -> bool:
    name = PurePosixPath(path).name
    if name == "conftest.py":
        return True
    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def classify(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[FileVerdict]:
    _preflight(repo_root)
    tracked = tracked_python_files(repo_root)
    if not tracked:
        raise GuardIsBlind(
            "no tracked .py at all — the GUARD IS BLIND (wrong root? wrong cwd?), not "
            "looking at a repository without Python in it"
        )
    if not any(is_under(path, ARCHIVED_RECEIPTS_ROOT) for path in tracked):
        raise GuardIsBlind(
            f"no committed .py sits under {ARCHIVED_RECEIPTS_ROOT!r}; the archived-receipts "
            f"class is vacuous. The GUARD IS BLIND, not the tree clean"
        )
    roots = typecheck_roots(repo_root)
    testpaths = pytest_testpaths(repo_root)
    patterns = pytest_test_file_patterns(repo_root)

    verdicts: list[FileVerdict] = []
    for path in tracked:
        fates: dict[GateAxis, Fate] = {}
        if any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED
        elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
            fates[GateAxis.TYPES] = Fate.EXEMPT_ARCHIVED_RECEIPTS
        elif any(row.axis is GateAxis.TYPES and is_under(path, row.root) for row in exemptions):
            fates[GateAxis.TYPES] = Fate.EXEMPT_TABLE
        else:
            fates[GateAxis.TYPES] = Fate.UNGATED

        if not _is_test_shaped(path, patterns):
            fates[GateAxis.EXECUTION] = Fate.NOT_APPLICABLE
        elif any(is_under(path, testpath) for testpath in testpaths):
            fates[GateAxis.EXECUTION] = Fate.COVERED
        elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
            fates[GateAxis.EXECUTION] = Fate.EXEMPT_ARCHIVED_RECEIPTS
        elif any(
            row.axis is GateAxis.EXECUTION and is_under(path, row.root) for row in exemptions
        ):
            fates[GateAxis.EXECUTION] = Fate.EXEMPT_TABLE
        else:
            fates[GateAxis.EXECUTION] = Fate.UNGATED
        verdicts.append(FileVerdict(path=path, fates=fates))
    return verdicts


def _message(path: str, axis: GateAxis, roots: Sequence[str], testpaths: Sequence[str]) -> str:
    if axis is GateAxis.TYPES:
        scope = f"outside every typecheck root ({', '.join(roots)})"
        fix = (
            "Fix: add its tree to scripts/typecheck.sh MEMBERS as its own iteration, or add "
            "a pinned exemption row carrying a finding number and a named re-open trigger."
        )
    else:
        scope = f"outside every testpaths entry ({', '.join(testpaths)})"
        fix = (
            "Fix: add its tree to testpaths in pyproject.toml, or add a pinned exemption "
            "row carrying a finding number and a named re-open trigger."
        )
    return (
        f"UNGATED GROUND ({axis.label}): {path!r} is a committed .py {scope} and not exempt.\n"
        f"    This test proves REGISTRATION in the gates' configuration — it does not prove "
        f"mypy or pytest ran, or passed; the gate's own exit code proves that.\n"
        f"    {fix}\n"
        f"    Do not widen the receipts class to admit it."
    )


def ungated_ground(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[UngatedFile]:
    verdicts = classify(repo_root, exemptions=exemptions)
    roots = typecheck_roots(repo_root)
    testpaths = pytest_testpaths(repo_root)
    findings: list[UngatedFile] = []
    for verdict in sorted(verdicts, key=lambda verdict: verdict.path):
        for axis in GateAxis:
            if verdict.fates[axis] is Fate.UNGATED:
                findings.append(
                    UngatedFile(
                        path=verdict.path,
                        axis=axis,
                        message=_message(verdict.path, axis, roots, testpaths),
                    )
                )
    return findings
```

## A.2 `drive.py` — the wrong-build driver (harness core)

The 42 patch specifications are the §2.1 table; the six that produced survivors are pasted in full
below the harness. The harness is what makes the "SURVIVED" verdict trustworthy: it asserts the
anchor landed, restores the reference between runs, and re-stages the git index each time.

```python
#!/usr/bin/env python3
"""WRONG-BUILD DRIVER — adversary-44-gatedground-1.

For each named wrong build: patch the adversary's own reference implementation of
``scripts/gated_ground.py``, stage it, run the REAL contract against it, and record whether
the contract SURVIVED it (a survivor = a defect the contract cannot catch).

Every variant is a textual patch against the reference source, applied with an assertion
that the anchor was found — a patch that silently no-ops would be a wrong build that never
existed, and its "SURVIVED" verdict would be a false clear (the #194 shape).
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TREE = Path("/tmp/adv44/ref")
BUILD = TREE / "scripts" / "gated_ground.py"
RUNNER = TREE / "scripts" / "typecheck.sh"
REFERENCE = Path("/tmp/adv44/reference_gated_ground.py").read_text(encoding="utf-8")
RUNNER_WITH_FILE_ENTRIES = Path("/tmp/adv44/typecheck_with_file_entries.sh").read_text(encoding="utf-8")
RUNNER_ORIGINAL = Path("/tmp/adv44/typecheck_original.sh").read_text(encoding="utf-8")
PYTHON = "…/.claude/worktrees/pkt44/.venv/bin/python"

# (name, [(anchor, replacement), ...], edits_runner)
VARIANTS: list[tuple[str, list[tuple[str, str]], bool]] = [...]  # see §2.1 + the six below


def apply_patch(source: str, patches: list[tuple[str, str]], name: str) -> str:
    for anchor, replacement in patches:
        if anchor not in source:
            raise SystemExit(f"[{name}] PATCH ANCHOR NOT FOUND — the wrong build was never built:\n{anchor}")
        source = source.replace(anchor, replacement, 1)
    return source


def run(name: str, patches: list[tuple[str, str]], edits_runner: bool) -> tuple[str, int, int, list[str]]:
    BUILD.write_text(apply_patch(REFERENCE, patches, name), encoding="utf-8")
    RUNNER.write_text(RUNNER_WITH_FILE_ENTRIES if edits_runner else RUNNER_ORIGINAL, encoding="utf-8")
    subprocess.run(["git", "-C", str(TREE), "add", "-A"], check=True, capture_output=True)
    completed = subprocess.run(
        [PYTHON, "-m", "pytest", "scripts/test_gated_ground.py", "-q", "--no-header", "-p", "no:cacheprovider"],
        cwd=TREE, capture_output=True, text=True,
    )
    failed = re.findall(r"^FAILED (\S+)", completed.stdout, re.MULTILINE)
    passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", completed.stdout)) else 0
    n_failed = int(m.group(1)) if (m := re.search(r"(\d+) failed", completed.stdout)) else 0
    if (m := re.search(r"(\d+) error", completed.stdout)):
        n_failed += int(m.group(1))
    return completed.stdout.strip().splitlines()[-1], passed, n_failed, failed


def main() -> None:
    survivors: list[str] = []
    for name, patches, edits_runner in VARIANTS:
        tail, passed, n_failed, failed = run(name, patches, edits_runner)
        verdict = "SURVIVED (contract blind)" if n_failed == 0 else f"KILLED by {len(failed)}"
        print(f"{name:52s} {passed:4d}P {n_failed:3d}F  {verdict}")
        for node in failed[:6]:
            print(f"      RED: {node.split('::', 1)[-1]}")
        if n_failed == 0:
            survivors.append(name)
    print(f"\nSURVIVORS ({len(survivors)}): {survivors}")
    BUILD.write_text(REFERENCE, encoding="utf-8")
    RUNNER.write_text(RUNNER_WITH_FILE_ENTRIES, encoding="utf-8")
    subprocess.run(["git", "-C", str(TREE), "add", "-A"], check=True, capture_output=True)


if __name__ == "__main__":
    main()
```

### The six survivor patches, verbatim

```python
# WB3 — str.startswith ONLY at the LEG-B testpath site (is_under left correct)
("""        elif any(is_under(path, testpath) for testpath in testpaths):
            fates[GateAxis.EXECUTION] = Fate.COVERED""",
 """        elif any(path.startswith(testpath) for testpath in testpaths):
            fates[GateAxis.EXECUTION] = Fate.COVERED"""),

# WB4b — WRONG BUILD #2: self-exemption by exact path (run WITH the ruled runner edit)
("""        if any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED""",
 """        if path in {"scripts/gated_ground.py", "scripts/test_gated_ground.py"}:
            fates[GateAxis.TYPES] = Fate.COVERED
        elif any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED"""),

# WB27 — LEG B reverse containment
("""        if not _is_test_shaped(path, patterns):
            fates[GateAxis.EXECUTION] = Fate.NOT_APPLICABLE
        elif any(is_under(path, testpath) for testpath in testpaths):
            fates[GateAxis.EXECUTION] = Fate.COVERED""",
 """        if not _is_test_shaped(path, patterns):
            fates[GateAxis.EXECUTION] = Fate.NOT_APPLICABLE
        elif any(
            is_under(path, testpath) or is_under(testpath, str(PurePosixPath(path).parent))
            for testpath in testpaths
        ):
            fates[GateAxis.EXECUTION] = Fate.COVERED"""),

# WB28 — str.startswith at the LEG-A typecheck-root site
("""        if any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED""",
 """        if any(path.startswith(root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED"""),

# WB29 — str.startswith at the archived-receipts site
("""        elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
            fates[GateAxis.TYPES] = Fate.EXEMPT_ARCHIVED_RECEIPTS""",
 """        elif path.startswith(ARCHIVED_RECEIPTS_ROOT):
            fates[GateAxis.TYPES] = Fate.EXEMPT_ARCHIVED_RECEIPTS"""),

# WB43 — repository-root-level .py treated as covered on both axes
("""        if any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED""",
 """        if "/" not in path:
            fates[GateAxis.TYPES] = Fate.COVERED
        elif any(is_under(path, root) for root in roots):
            fates[GateAxis.TYPES] = Fate.COVERED"""),
("""        if not _is_test_shaped(path, patterns):
            fates[GateAxis.EXECUTION] = Fate.NOT_APPLICABLE""",
 """        if "/" not in path:
            fates[GateAxis.EXECUTION] = Fate.COVERED
        elif not _is_test_shaped(path, patterns):
            fates[GateAxis.EXECUTION] = Fate.NOT_APPLICABLE"""),

# WB31 / WB33 / WB36 / WB38 / WB45 — one-liners
('    return sorted(record for record in records if record.endswith(".py"))',
 '    return sorted(record for record in records if ".py" in record)'),
('        reopen_trigger="a demand to prove COLLECTION or EXECUTION rather than registration",',
 '        reopen_trigger="TBD",'),
("""        f"    This test proves REGISTRATION in the gates' configuration — it does not prove "
        f"mypy or pytest ran, or passed; the gate's own exit code proves that.\\n\"""",
 '        f"    registration; does not prove; finding number; re-open trigger\\n"'),
('        reopen_trigger="the #188 cleanup lands; delete this row and the leg goes live",',
 '        reopen_trigger="TBD",'),
('        reason="standing disposition: its own work item, config half first",',
 '        reason="x",'),
```

## A.3 `leg2_forgery.py` — the dependency × verb false-clear sweep

```python
#!/usr/bin/env python3
"""LEG-2 FORGERY PROBE — adversary-44-gatedground-1.

Dependencies {git index, scripts/typecheck.sh, pyproject.toml, the exemption table} ×
{empty, missing, malformed, whole-tree-wildcard, duplicated}. For each CONSTRUCTED state,
compare the guard's served answer against the HEALTHY one. Identical bytes on a broken
state = a FALSE CLEAR.

Run against the ADVERSARY REFERENCE BUILD — i.e. a build that passes the whole contract
130/130. Anything this finds is a hole the contract licenses.
"""

from __future__ import annotations

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REFERENCE = Path("/tmp/adv44/reference_gated_ground.py")


def load():
    spec = importlib.util.spec_from_file_location("ref_gg", REFERENCE)
    module = importlib.util.module_from_spec(spec)
    sys.modules["ref_gg"] = module          # dataclasses resolve annotations via sys.modules
    spec.loader.exec_module(module)
    return module


gg = load()

MODULE_BODY = '"""m."""\n\n\ndef answer() -> int:\n    return 42\n'
TEST_BODY = '"""t."""\n\n\ndef test_it() -> None:\n    assert True\n'


def build(root, *, members_line="MEMBERS=(loremaster)", testpaths=None, ruff_exclude=None,
          manifest_text=None, files=None, init_git=True):
    if init_git:
        subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=root, check=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "typecheck.sh").write_text(
        f"#!/usr/bin/env bash\nset -uo pipefail\n{members_line}\n", encoding="utf-8")
    if manifest_text is None:
        manifest_text = (
            '[project]\nname = "fixture"\nversion = "0.0.0"\n\n'
            '[tool.uv.workspace]\nmembers = ["loremaster"]\n\n'
            f"[tool.ruff]\nextend-exclude = "
            f"{json.dumps(ruff_exclude or ['scratchpad', 'docs/plans/v2/receipts'])}\n\n"
            '[tool.mypy]\npython_version = "3.14"\nstrict = true\n\n'
            '[tool.pytest.ini_options]\nasyncio_mode = "auto"\n'
            f"testpaths = {json.dumps(testpaths if testpaths is not None else ['loremaster/tests'])}\n")
    (root / "pyproject.toml").write_text(manifest_text, encoding="utf-8")
    everything = {
        "loremaster/tests/test_store_lease.py": TEST_BODY,
        "docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py": MODULE_BODY,
        # THE CANARY: committed ungated ground on BOTH axes. A healthy guard reports it.
        "docs/consult/test_orphan.py": TEST_BODY,
        **(files or {}),
    }
    for relative, body in everything.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    if init_git:
        subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)


def served(root, *, exemptions=None, env=None) -> str:
    """The bytes a consumer sees: the finding set, or the loud failure."""
    saved = dict(os.environ)
    if env is not None:
        os.environ.clear(); os.environ.update(env)
    try:
        kwargs = {} if exemptions is None else {"exemptions": exemptions}
        findings = gg.ungated_ground(root, **kwargs)
        return "\n".join(sorted(f"{f.path}:{f.axis.name}" for f in findings)) or "(ZERO FINDINGS)"
    except Exception as error:                       # the served answer IS the failure
        return f"{type(error).__name__}: {str(error)[:110]}"
    finally:
        if env is not None:
            os.environ.clear(); os.environ.update(saved)


# … per-case construction: index-empty, non-repo, PATH without git, runner missing / no
# declaration / MEMBERS=() / MEMBERS=(.) / TWO declarations, manifest missing / malformed /
# testpaths []/['.']/[''], ruff exclusion removed, exemption roots '.', './', 'docs' …

# ⚠ PER-AXIS, not whole-output identity. The first version of this probe compared the
# served string to the healthy string and reported "FALSE CLEARS: 0" — it could not
# see a case that lost ONE axis's canary and kept the other. That is the probe
# passing for the wrong reason, and it is the failure this comparison exists to stop.
healthy_axes = {line.rsplit(":", 1)[1] for line in healthy.splitlines()}
answer_axes = {line.rsplit(":", 1)[1] for line in answer.splitlines()
               if line.startswith("docs/consult/test_orphan.py")}
lost = sorted(healthy_axes - answer_axes)
loud = answer.startswith(("GuardIsBlind", "FileNotFoundError", "TOMLDecodeError"))
if lost and not loud:
    false_clears.append(f"{label} (lost {', '.join(lost)})")
```

## A.4 The four proposed pins (M1–M4), validated both legs

Drop into the contract (or a sibling file) as-is; `reference+` proves them satisfiable.

```python
class TestProposedPins:
    def test_P_A_a_whole_tree_testpath_is_blind_not_clean(self, tmp_path: Path) -> None:
        # M2. WRONG BUILD IT CATCHES: LEG B silently covered by `testpaths = ["."]` — the exact
        # analogue of the MEMBERS wildcard the contract already pins, on the other axis.
        for index, wildcard in enumerate((".", "./", "..", "/", "")):
            case = tmp_path / f"case{index}"
            case.mkdir()
            repository = _minimal_repository(case, testpaths=["loremaster/tests", wildcard])
            with pytest.raises(gg.GuardIsBlind) as raised:
                gg.pytest_testpaths(repository.root)
            assert repr(wildcard) in str(raised.value) or wildcard in str(raised.value)

    def test_P_B_an_exemption_root_that_widens_to_the_whole_repository_is_rejected(self) -> None:
        # M4. WRONG BUILD IT CATCHES: one exemption row silences an entire axis. The table is a
        # deny-by-default allowlist; `.` turns it into an off switch.
        for root in (".", "./"):
            with pytest.raises(gg.InvalidExemption):
                gg.Exemption(root=root, axis=gg.GateAxis.TYPES, finding="#188",
                             reason="standing disposition, its own work item",
                             reopen_trigger="the cleanup lands")

    def test_P_B_control_a_legitimate_narrow_root_still_constructs(self) -> None:
        # POSITIVE CONTROL: without it, a validator that rejected EVERYTHING would pass above.
        row = gg.Exemption(root="scripts", axis=gg.GateAxis.TYPES, finding="#188",
                           reason="standing disposition, its own work item",
                           reopen_trigger="the cleanup lands")
        assert row.root == "scripts"

    def test_P_C_two_MEMBERS_declarations_are_blind_not_clean(self, tmp_path: Path) -> None:
        # M3. WRONG BUILD IT CATCHES: the guard parses a declaration bash never executes (last
        # assignment wins), so a NARROWED gate reads as the wider one — LEG A false clear.
        repository = _minimal_repository(tmp_path, members=["loremaster", "docs"])
        runner = repository.root / "scripts" / "typecheck.sh"
        runner.write_text(runner.read_text(encoding="utf-8") + "\nMEMBERS=(loremaster)\n",
                          encoding="utf-8")
        with pytest.raises(gg.GuardIsBlind) as raised:
            gg.typecheck_roots(repository.root)
        assert "MEMBERS" in str(raised.value)

    def test_P_D_the_guard_names_no_path_of_its_own_anywhere_in_its_source(self) -> None:
        # M1. WRONG BUILD IT CATCHES: a build that hardcodes `if path in {"scripts/gated_ground.py",
        # "scripts/test_gated_ground.py"}: COVERED`. With the ruled MEMBERS entries also in
        # place, EVERY pin in the shipped contract passes — measured. The contract's docstring
        # already CLAIMS "the guard contains no mention of its own path anywhere"; this is the
        # assertion behind the claim.
        instrument = Path(gg.__file__)
        forbidden = {instrument.name, instrument.stem, f"scripts/{instrument.name}",
                     "test_gated_ground.py", "scripts/test_gated_ground.py"}
        literals = {node.value for node in ast.walk(ast.parse(instrument.read_text(encoding="utf-8")))
                    if isinstance(node, ast.Constant) and isinstance(node.value, str)}
        named = sorted(literal for literal in literals if literal in forbidden)
        assert not named, (
            f"the guard's source names its own files {named}. A guard that special-cases itself "
            f"stops tracking the runner: delete the MEMBERS entry and it still reports COVERED. "
            f"RULED FIX: a MEMBERS entry is a typecheck root and a file is the finest grain of "
            f"one — cover the instrument through the runner, never through a literal."
        )
```

The `reference+` guards that make P_A/P_B/P_C green (i.e. the *implementation* the pins demand):

```python
# P-A — in pytest_testpaths, before the is_dir() check
if (testpath.strip() in {"", ".", "./", "..", "/"} or testpath.startswith("/")
        or ".." in PurePosixPath(testpath).parts):
    raise GuardIsBlind(
        f"testpaths entry {testpath!r} widens to the whole tree; every test-shaped "
        f"file would read as gated. The GUARD IS BLIND, not the tree clean")

# P-B — in Exemption.__post_init__
if not PurePosixPath(self.root).parts or self.root.strip() in {".", "./"}:
    raise InvalidExemption(
        f"exemption root {self.root!r} widens to the whole repository, which silences "
        f"the whole axis — an exemption is an allowlist of the safe, not an off switch")

# P-C — in typecheck_roots, before the single-match search
declarations = _MEMBERS_DECLARATION.findall(text)
if len(declarations) > 1:
    raise GuardIsBlind(
        f"scripts/typecheck.sh carries {len(declarations)} MEMBERS=(…) declarations; bash's "
        f"last assignment wins, so this guard cannot know which one the gate executes. The "
        f"GUARD IS BLIND, not the tree clean")
```

## A.5 `perturb.py` — the P2 fixture perturbation (M6/M7)

Applied to a **scratch copy** of the contract only. The addition goes immediately after the
`scripts_extra/promotion_helper.py` line in `workspace_shaped_repository`:

```python
    # ADVERSARY PERTURBATION — one file per blind spot the shipped fixture cannot see.
    # sibling prefix of the `docs/eval` TYPECHECK ROOT (the shipped fixture only has a
    # sibling prefix of the EXEMPTION root, so only that membership site is discriminated)
    repository.add_python_file("docs/evaluation/harness.py")
    # sibling prefix of the `loremaster/tests` TESTPATH
    repository.add_python_file("loremaster/tests_extra/test_probe.py", body=_TEST_BODY)
    # an ANCESTOR of the `skills/lore-deploy/tests` testpath
    repository.add_python_file("skills/test_workspace_probe.py", body=_TEST_BODY)
    # REPOSITORY-ROOT-LEVEL committed Python — no fixture in the shipped contract has any
    repository.add_python_file("release_probe.py")
    repository.add_python_file("conftest.py", body=_TEST_BODY)
```

```python
class TestAdversaryPerturbations:
    """The four pins the shipped fixture cannot support, each named for the wrong build it
    kills. Written by adversary-44-gatedground-1; each is GREEN on a correct build."""

    def test_a_sibling_prefix_of_a_TYPECHECK_ROOT_is_not_covered(self, workspace_shaped_repository):
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=gg.EXEMPTIONS)
        assert fates_of(verdicts, "docs/evaluation/harness.py")[gg.GateAxis.TYPES] is gg.Fate.UNGATED

    def test_a_sibling_prefix_of_a_TESTPATH_is_not_covered(self, workspace_shaped_repository):
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=gg.EXEMPTIONS)
        assert fates_of(verdicts, "loremaster/tests_extra/test_probe.py")[
            gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_an_ancestor_of_a_testpath_is_not_covered_by_it(self, workspace_shaped_repository):
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=gg.EXEMPTIONS)
        assert fates_of(verdicts, "skills/test_workspace_probe.py")[
            gg.GateAxis.EXECUTION] is gg.Fate.UNGATED

    def test_repository_root_level_python_is_ordinary_committed_ground(self, workspace_shaped_repository):
        verdicts = assert_every_tracked_file_is_accounted_for(
            workspace_shaped_repository.root, exemptions=gg.EXEMPTIONS)
        assert fates_of(verdicts, "release_probe.py")[gg.GateAxis.TYPES] is gg.Fate.UNGATED
        assert fates_of(verdicts, "conftest.py")[gg.GateAxis.EXECUTION] is gg.Fate.UNGATED
```

## A.6 `divergence.py` — the inert-patch control

```python
"""DIVERGENCE PROVER — P0 CONTROL for every "SURVIVED" verdict.

A patch that changed nothing would also survive the contract, and reporting it as a finding
would be a false clear. For each survivor this builds a tiny ``git init``-from-empty
repository exhibiting a concrete input on which the WRONG build and the REFERENCE build give
DIFFERENT answers, and prints both.
"""
# … build_repo() as in A.3, then, per survivor:
wrong_source = drive.apply_patch(REFERENCE, PATCHES[name], name)
assert wrong_source != REFERENCE, f"{name}: patch was inert"
ref_verdicts   = {v.path: v.fates for v in reference.classify(root)}
wrong_verdicts = {v.path: v.fates for v in wrong.classify(root)}
diverged = "DIVERGES" if ref_name != wrong_name else "identical — INERT PATCH"
```

Interrogated inputs, one per survivor: `loremaster/tests_extra/test_probe.py` ·
`docs/evaluation/harness.py` · `docs/plans/v2/receipts_live/promoted_tool.py` ·
`docs/consult/notes.py.txt` · `release_probe.py` + `conftest.py` ·
`skills/test_workspace_probe.py` · `scripts/gated_ground.py`.

## A.7 The mypy-relaxation sweep (§3.2)

```python
CASES = {
 'follow_imports = "skip"  (global)':  '[tool.mypy]\nfollow_imports = "skip"\n',
 'ignore_errors = true      (global)': '[tool.mypy]\nignore_errors = true\n',
 'disable_error_code (global)':        '[tool.mypy]\ndisable_error_code = ["attr-defined"]\n',
 'override follow_imports=skip':       '[[tool.mypy.overrides]]\nmodule=["x"]\nfollow_imports="skip"\n',
 'override disable_error_code':        '[[tool.mypy.overrides]]\nmodule=["x"]\ndisable_error_code=["a"]\n',
 'CONTROL: exclude (modelled)':        '[tool.mypy]\nexclude = ["loremaster/store/.*"]\n',
 'CONTROL: override ignore_errors':    '[[tool.mypy.overrides]]\nmodule=["x"]\nignore_errors=true\n',
}
for label, mypy_block in CASES.items():
    # build a git-init fixture repo with that [tool.mypy] block, then:
    print(label, "->", "REFUSES" if gg.unmodelled_mypy_configuration(root) else "ACCEPTED SILENTLY")
```

## A.8 The P-PKG measurements (§5)

```python
from pathlib import PurePosixPath
import shlex
# the contract's own 12-row test_prefix_membership matrix, replayed through the stdlib method
bad = [r for r in rows if PurePosixPath(r[0]).is_relative_to(r[1]) is not r[2]]
# -> mismatches: []                                       (stdlib is byte-equivalent to is_under)
shlex.split('lorerunes "docs/my eval" loremaster')
# -> ['lorerunes', 'docs/my eval', 'loremaster']
'lorerunes "docs/my eval" loremaster'.split()
# -> ['lorerunes', '"docs/my', 'eval"', 'loremaster']      (the bespoke parse mis-splits)
```
