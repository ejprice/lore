brief-base v9 read

# REPORT-adversary-44-gatedground-3 — third adversarial grading of the packet-44 gated-ground contract

**Target graded:** `scripts/test_gated_ground.py` · md5 **`af4cdab58c9c24f72557d5cfb9ae38f3`** ·
**2404 lines** · **171 collected**. Verified at start (20:25 EDT) **and at end** (20:56 EDT) —
the file did not move under me. Worktree `.claude/worktrees/pkt44`, branch `pkt44/ungated-ground`,
HEAD `96816cc` at the start of my run. **All measurements below were taken 2026-07-29 against md5
`af4cdab5…` and no other version.**

⚠ **HEAD ADVANCED UNDER ME AND THE GRADED ARTIFACT DID NOT.** By the time I finished writing,
`builder-44-instrument-1` had landed `7708a74` (*"the derived, per-axis gated-ground invariant"*) and
`737ee6b` (*"four defects I found in my own instrument"*), so `scripts/gated_ground.py` is now a
COMMITTED build I have not graded and make no claim about. `git log -- scripts/test_gated_ground.py`
is still empty (the contract remains untracked and byte-identical at both ends of my run), so every
finding below stands as a statement about the CONTRACT. My scratch was fully isolated —
`git -C <scratch> rev-parse --absolute-git-dir` → `<scratch>/.git` (a DIRECTORY), never the
worktree's `/home/ejprice/PycharmProjects/lore/.git/worktrees/pkt44` — so #284 was avoided and no
staging of mine reached the real index.

⚠ **THE BRIEF NAMED A DIFFERENT ARTIFACT.** My brief and `REPORT-contract-44-gatedground-1-r5.md`
both fix the target at md5 **`89cea4086f8ae54ee36dcd986e0d1dd6` · 2405 lines**. The file on disk
when I started was already `af4cdab5…` · 2404 lines. I graded what exists; both versions collect
171 tests. See §0.

---

## SUMMARY BLOCK

- `brief-base v9 read` · **state: done** · deviations: 2 (§0.3 — mutation baseline was the contract
  author's own reference build found in-tree, not one I authored; scratch repo built by `git archive`
  + fresh `git init`, never `cp -a`) · **capability gap: no `mcp__lore_lore__*` tools of any kind** —
  **third measured instance of #287** (§0.4).
- **VERDICT: CONTRACT INSUFFICIENT** — 11 numbered missing pins (§4), each with the test to write and
  the defect it catches.
- **P1 HEADLINE — 21 wrong builds run against the real contract: 15 killed, 6 SURVIVED at
  171 passed / 0 failed.** And **two holes need no wrong build at all: the reference build that
  proves this contract's satisfiability serves FALSE CLEARS** — byte-identical-to-healthy output on
  a broken tree (§2).
- **THE SHAPE OF THIS WAVE'S FAILURE: r5 fixed the INSTANCES the last adversary named, not the
  QUANTIFIERS.** D2 pins blindness-monotonicity at the served surface for **5 named doors**;
  quantified over the derived failure set it is **6/26**, and a build honouring exactly those 5
  doors (WB1) passes 171/171 while serving **17 false clears** (§3.1).
- **AND THE DUAL NOBODY PINNED: findings-monotonicity.** `is_clean` / `exit_code` / `render()` are
  pinned for blind states and for clean trees, and **never for a tree with findings**. WB2 serves
  `findings=1`, `is_clean=True`, `exit_code=0`, `render()=="GATED GROUND: every committed .py is
  registered on both axes."` — and passes 171/171 (§3.2).
- **LEG A reads a file mypy may IGNORE.** A committed `mypy.ini` beats `pyproject.toml`
  (verified in installed mypy 2.1.0 source, `defaults.CONFIG_NAMES` before `SHARED_CONFIG_NAMES`).
  The gate goes off; the guard serves healthy bytes. **#107 verbatim.** LEG B is immune — because D1
  made it empirical (§2.2).
- **P-PKG DIFF: one row, three surveys, all wrong the same way.** `fnmatch` is surveyed `replace`
  by the author, adversary-1 and adversary-2; **nobody read pytest's matcher.** pytest uses
  `fnmatch_ex`, which matches the WHOLE PATH when the pattern contains `/`. **6 measured
  divergences, all in the silent-drop direction** (§5).
- **F1's deletion stranded 3 pins that can no longer fail** — proven, one with `assert False` in a
  loop body that still passes (§3.4, §6).
- **A stated bound is FALSE TODAY:** `conftest-collection-hooks` claims `collect_ignore_glob` is
  unmodelled; the contract's own passing `test_a_conftest_level_collection_hook_is_caught_too`
  proves D1 catches it. r5 applied this exact correction to `.sh` and not to its sibling (§7).
- `Packages considered:` **`_pytest.pathlib.fnmatch_ex`** (READ: installed source, the
  `if sep not in pattern: name = path.name else: name = str(path)` branch) → **`replace_with_adapter`
  + oracle pin** — ⚠ **DIFF, and the sharpest finding in §5** · `mypy.defaults.CONFIG_NAMES` (READ:
  installed `mypy/defaults.py` + `config_parser.py:277`) → **`replace`** the pyproject-only read ·
  `PurePosixPath.is_relative_to` (READ: 6-spelling normalisation probe — `.`/`./`/`./.` all give
  `parts == ()`) → **`replace`** the spelling denylist · `shlex.split` (READ: signature + measured
  3-vs-4 token split) → **replace**, agree · `tomllib` → replace, agree · `git ls-files -z` →
  keep (subprocess; `pygit2`/`dulwich`/`GitPython` **not installed** — verified via
  `importlib.util.find_spec`; escalate rather than vendor) · `bashlex` for the `MEMBERS` parse →
  **not installed → `keep_with_trigger`** (trigger: the runner's array ever becomes multi-line;
  the regex `[^)]*` cannot see it) · full table §5.
- receipt pointers: target/version §0 · REF false clears §2 · wrong-build matrix §3 · missing pins
  §4 · P-PKG §5 · corpse sweep + P6b §6 · bounds §7 · quantifier table §8 · escalations §9 ·
  instruments verbatim §10.

---

## 0. Preconditions, provenance, deviations, capability

### 0.1 The version discrepancy

| source | md5 | lines | collected |
|---|---|---|---|
| my brief | `89cea4086f8ae54ee36dcd986e0d1dd6` | 2405 | 171 |
| `REPORT-contract-44-gatedground-1-r5.md` §"FIXED TARGET" | `89cea408…` | 2405 | 171 |
| **on disk, 20:25 and 20:56 EDT 2026-07-29** | **`af4cdab58c9c24f72557d5cfb9ae38f3`** | **2404** | **171** |

The file is UNTRACKED (`git status` → `?? scripts/test_gated_ground.py`), so there is no committed
object to diff against and I cannot recover `89cea408…`. I graded `af4cdab5…`. Every claim in this
report is about that md5. **Whoever edited the frozen contract after r5 froze it did so without a
receipt — this is escalation E3 (§9).**

### 0.2 Scratch provenance (#284 / #140)

I never copied this worktree. `.git` here is a FILE naming the original gitdir, so a copy's
`git add` would mutate the real worktree. Instead:

```
$ git -C <worktree> archive HEAD -o /home/ejprice/scratch/adv44-3/head.tar   # 29,644,800 bytes
$ tar -xf head.tar -C /home/ejprice/scratch/adv44-3/refrepo
$ cp <the two untracked files> refrepo/scripts/
$ git -C refrepo init -q -b main .
PROVENANCE OK: .git is a DIRECTORY (not a worktree file)
$ git -C refrepo ls-files '*.py' | wc -l
292
```

Instrument provenance receipt, asserted not assumed:

```
gg.__file__ = /home/ejprice/scratch/adv44-3/refrepo/scripts/gated_ground.py
PROVENANCE ASSERTED: instrument under test is the scratch copy
```

`.venv` is a symlink to the worktree's venv. **Disclosed consequence:** `import loremaster` inside
the scratch resolves to the original checkout via the editable `.pth`. That is irrelevant here —
the module under test is `gated_ground`, which is imported from the scratch `scripts/` directory by
the contract's own `sys.path.insert`, and I assert its path above. No production file was touched.

### 0.3 Deviations

1. **My mutation baseline is not a build I authored.** When I started, `scripts/gated_ground.py`
   contained the **contract author's own throwaway reference build** (docstring: *"THROWAWAY
   REFERENCE BUILD — satisfiability receipt for scripts/test_gated_ground.py … Written by
   contract-44-gatedground-1 … It is DELETED at the end of that run and must never be committed"*).
   I snapshotted it, restored one mid-mutation literal (`identifier="file-types-XX"` →
   `"file-types-modelled"`) and used it as **REF**. Rationale: it is the artifact whose 171/0 IS the
   contract's satisfiability receipt, and mutating it grades the CONTRACT rather than the builder.
   **My wrong-build enumeration is entirely my own and was derived and written down before I opened
   either predecessor report** (§3 order of work). This is escalation **E1** (§9).
2. **Satisfiability reproduced independently:**
   `REF.py => 171 passed in 11.70s   [collected total: 171]`. I re-derived the count; I did not
   relay r5's.

### 0.4 Capability check (brief-base §4) — third measured instance of #287

| demanded by my brief | what I actually have | what I did instead |
|---|---|---|
| `ToolSearch "select:mcp__lore_lore__lore_comms"`; `lore_comms action=register`; `action=brief_get name=pkt44` | **no `mcp__lore_lore__*` tools of any kind.** `select:`-form search → *"No matching deferred tools found"*; keyword search → same, after the server finished connecting and its instructions loaded into my context | **zero of the three calls was possible.** I never read the pkt44 brief and cannot echo a `brief pkt44 v<N> read` receipt. This report is my only channel |

This is the **third** consecutive measurement of the same gap (r2, r5, and now me) on **three
different agent definitions**. The `contract-adversary` definition grants no MCP surface at all, and
I also have **no `SendMessage`** — so brief-base §5's "write the fork, then send one message" is
half-unavailable to me. **What a lead must change:** either grant these definitions an MCP surface,
or stop briefing a pull channel they provably cannot reach. Filing via `lore_findings` was likewise
impossible.

### 0.5 Peer-safety

`builder-44-instrument-1` was writing `scripts/gated_ground.py` throughout. I checked the process
table before every read of it, took a snapshot at 20:25, and did all work in scratch. At 20:31 the
file vanished mid-run (`cp: cannot stat …`) and by 20:55 it was a **different, larger build**
(45,339 bytes, its own docstring). I graded neither. Repo files: read-only except this report.

---

## 1. Method, and the order it was done in

1. Read the contract end to end (2404 lines) and the live `scripts/typecheck.sh` + `pyproject.toml`
   it parses.
2. **Derived my own wrong-build enumeration and wrote it down** — categories: no-op fix · plausible
   -wrong branch/order · partial fix · cosmetic/served-surface · deletion-wave corpses · fixture
   monoculture · hardcoded-list. 21 builds came out of it.
3. Built REF, proved 171/0.
4. Ran every wrong build against the real contract with a **collected-count check** in the runner
   (a run that does not total 171 is reported as not comparable — `no tests ran` behind a pipe is
   the failure mode).
5. Derived the Leg-2 failure set as {dependency} × {verb} and byte-diffed 26 constructed states.
6. P2 perturbations on scratch copies of the contract, each with a correct-build control leg.
7. **Only then** read `REPORT-adversary-44-gatedground-1.md` and `-2.md`, and diffed.

---

## 2. THE HEADLINE: the reference build itself serves false clears

Two holes need no wrong build. REF passes 171/171 and is the contract's satisfiability receipt.

### 2.1 F-A — `MEMBERS=(loremaster ./)` is a whole-tree wildcard the contract does not pin

`test_a_whole_tree_member_is_blind_not_clean` parametrizes `[".", "..", "/", "/home"]`.
`test_a_whole_tree_testpath_is_blind_not_clean` parametrizes `[".", "./", "..", "/", ""]`.
**`"./"` is pinned on ONE axis.** And:

```
'.'   -> PurePosixPath '.'  parts ()      covers-everything True
'./'  -> PurePosixPath '.'  parts ()      covers-everything True
'./.' -> PurePosixPath '.'  parts ()      covers-everything True
'..'  -> PurePosixPath '..' parts ('..',) covers-everything False
```

REF rejects roots by the SPELLING `root in {".", ".."}`, so `./` walks through. Probe
(`probe_wildcard_asymmetry.py`, §10.3), all three controls green:

```
[control A] healthy tree: is_clean=True exit=0 blind=()
[control B] ungated ground present: findings=1 is_clean=False exit=1     <- probe can see findings
[control C] '.' correctly raises GuardIsBlind: typecheck root '.' is a whole-tree wildcard...

[probe] MEMBERS=(loremaster ./)
    typecheck_roots ACCEPTED it -> ['loremaster', './']
    served: is_clean=True exit=0 blind=() TYPES-findings=0
    BYTES IDENTICAL TO HEALTHY: True
    *** FALSE CLEAR: 'docs/consult/coherence_check.py' is under no real typecheck root,
        yet LEG A reports nothing. ***
[probe] MEMBERS=(loremaster ./.)      -> same
[probe] MEMBERS=(loremaster docs/../.) -> blind (SAFE)
```

→ **MISSING PIN P-1** (§4).

### 2.2 F-B — a committed `mypy.ini` switches LEG A's gate off and the guard serves healthy bytes

`unmodelled_mypy_configuration` exists precisely to refuse a mypy configuration the guard cannot
model. **It reads `pyproject.toml` — the file mypy IGNORES when a `mypy.ini` exists.** Verified in
the *installed* dependency, not from docs or memory:

```
$ .venv/bin/python -c "import mypy.defaults as d; print(d.CONFIG_NAMES, d.SHARED_CONFIG_NAMES)"
CONFIG_NAMES = ['mypy.ini', '.mypy.ini']
SHARED_CONFIG_NAMES = ['pyproject.toml', 'setup.cfg']
$ grep -n CONFIG_NAMES .venv/.../mypy/config_parser.py
277:        for name in defaults.CONFIG_NAMES + defaults.SHARED_CONFIG_NAMES:   # first hit wins
```

`probe_config_shadowing.py` (§10.5) on trees that are **otherwise fully gated**:

```
[control A] fully-gated tree, no sidecar -> is_clean=True exit=0
[control B] one ungated file, no sidecar -> 1 finding(s), bytes != healthy: True

sidecar case                                  blind?  findings  bytes
mypy.ini excludes the ONLY typecheck root     False   0         IDENTICAL-TO-HEALTHY
mypy.ini turns errors off globally            False   0         IDENTICAL-TO-HEALTHY
.mypy.ini excludes the only root              False   0         IDENTICAL-TO-HEALTHY
setup.cfg mypy section excludes the only root False   0         IDENTICAL-TO-HEALTHY  (lower precedence — harmless)
pytest.ini redirects testpaths                False   1         distinct              <- D1 CATCHES IT
tox.ini [pytest] section                      False   0         IDENTICAL-TO-HEALTHY  (lower precedence — harmless)
```

Two things worth stating together. This is **#107 verbatim** — reading a declaration the tool does
not execute. And **LEG B is immune to the same attack**, because D1 made LEG B *empirical*: a
`pytest.ini` that redirects collection is caught by the collector without anyone modelling
`pytest.ini` at all. That asymmetry is the argument for P-2's shape.

→ **MISSING PIN P-2** (§4).

---

## 3. P1 — the wrong-build matrix

Runner: `run_contract_against.sh` (§10.2). Every patch anchor is asserted present and unique;
an unfound anchor is a hard error, because a silently-unapplied patch reads as a surviving build.
`REF.py => 171 passed`.

| # | wrong build | result | verdict |
|---|---|---|---|
| WB1 | `ungated_ground` reports blindness only for the 5 doors pinned at the served surface, swallows the rest into a CLEAN verdict | **171 passed** | ❗**SURVIVED — 17 false clears** |
| WB2 | `is_clean`/`exit_code`/`render()` ignore `findings` entirely | **171 passed** | ❗**SURVIVED — served false clear** |
| WB3 | the failure message's scopes come from `Path.cwd()`, not `repo_root` | **171 passed** | ❗**SURVIVED** |
| WB4 | `exemptions` defaults to a literal `()` instead of `EXEMPTIONS` | **171 passed** | ❗**SURVIVED — pin is vacuous post-F1** |
| WB5 | the `file-types-modelled` bound's CONTENT reverts to teaching a closed hole as open | **171 passed** | ❗**SURVIVED** |
| WB9 | precedence reversed: an exemption row BEATS gate coverage | **171 passed** | ❗**SURVIVED — the pin named for this passes `exemptions=()`** |
| WB6 | the collector is never consulted (pre-D1 registration-only LEG B) | 2 failed | killed — D1 holds |
| WB7 | pytest exit 5 treated as BLIND | 2 failed | killed |
| WB8 | any collector exit code accepted as an honest zero | 1 failed | killed |
| WB10 | LEG B reads the LIVE session's items instead of a subprocess | 11 failed | killed — D1's subprocess property holds |
| WB11 | the blind render names nothing about what went blind | 4 failed | killed — D2's `expected_token` leg holds |
| WB12 | `typecheck_roots` accepts a root that does not exist | 1 failed | killed (but see §6 C7) |
| WB13 | `member_mypypath` always returns `{}` | 1 failed | killed |
| WB14 | `str.startswith` at the typecheck-root site (adversary-1's WB28) | 1 failed | killed — closed |
| WB15 | `conftest.py` is not test-shaped | 4 failed | killed |
| WB16 | findings emitted for the TYPES axis only | 32 failed | killed |
| WB17 | receipts exemption granted by substring (adversary-1's WB29) | 2 failed | killed — closed |
| WB18 | the mypy refusal fires only on trees with >4 tracked files | 1 failed | killed |
| WB19 | the bound IDENTIFIER broken, content intact | 1 failed | killed — see §3.5 |
| WB20 | `conftest.py`'s by-design zero contribution becomes a finding | 2 failed | killed (tree-dependent — §6 C9) |
| WB21 | `_is_test_shaped` matches the WHOLE PATH for every pattern | 17 failed | killed — but only this half (§5) |

**21 built · 15 killed · 6 survived.**

### 3.1 WB1 — D2's monotone property is GUARDED BY FIVE DOORS, not ∀ over blind sources

r5's D2 work added `blind_sources`, three entry-point pins and a 4-value byte-diff parametrization.
Quantified over the derived failure set that is **5 doors of 26**. WB1 honours exactly those five
and serves a clean verdict for everything else. Same probe, same controls, different build:

```
REF: blind states correctly reported 21/26 · false clears 2
WB1: blind states correctly reported  6/26 · false clears 17     (and 171 passed / 0 failed)

FALSE CLEARS (17) — broken state served BYTES IDENTICAL TO HEALTHY:
  typecheck.sh / missing / runner absent
  typecheck.sh / empty / empty MEMBERS array
  typecheck.sh / duplicate / two MEMBERS declarations
  typecheck.sh / whole-tree / MEMBERS wildcard '.'      <- the pinned one, at the READER only
  typecheck.sh / whole-tree / MEMBERS wildcard './'
  typecheck.sh / whole-tree / MEMBERS wildcard './.'
  typecheck.sh / whole-tree / MEMBERS wildcard '/'
  typecheck.sh / phantom / MEMBERS phantom root
  pyproject.toml / malformed / pyproject malformed
  pyproject.toml / empty / no [tool.pytest] table
  pyproject.toml / empty / empty testpaths
  pyproject.toml / phantom / testpaths phantom
  pyproject.toml / unmodelled / mypy exclude
  pyproject.toml / unmodelled / mypy global ignore_errors
  pyproject.toml / vacuous / no receipts file at all
  collector / non-zero-exit / collector conftest raises
  git index / missing / not a git repository
```

Note the first wildcard row: `MEMBERS=(loremaster .)` is pinned **at the reader** and **through
`classify`** — but the byte-diff parametrization's `members` case is *no declaration at all*, so the
wildcard's SERVED behaviour is unpinned. This is adversary-2's I7 recurring one level up: the fix
enumerated the doors it had been shown instead of quantifying over the door set.
→ **MISSING PIN P-3**.

### 3.2 WB2 — the served surface is pinned for blind and for clean, never for FINDINGS

Nothing in 171 tests asserts that a tree WITH findings serves a non-clean verdict.
`_healthy_render` asserts `is_clean` on a clean control; `test_a_clean_tree_serves_a_clean_verdict`
pins `blind_sources==()`, `exit_code==0`, `is_clean`; `test_every_blind_state_serves_bytes_distinct
_from_healthy` pins the blind side. The findings side is open, and every findings-based pin reads
`.findings` directly through the `findings_of` helper, so it never touches the served surface.

```
===== REF =====
  findings  = 1  (paths: ['docs/consult/coherence_check.py'])
  is_clean  = False   exit_code = 1
  render()  = UNGATED GROUND (LEG A — types): 'docs/consult/coherence_check.py' is a committed .py …

===== WB2 (171 passed / 0 failed) =====
  findings  = 1  (paths: ['docs/consult/coherence_check.py'])
  is_clean  = True    exit_code = 0
  render()  = GATED GROUND: every committed .py is registered on both axes.
```

By this repo's hard definition of trust, that is a false clear: a consumer acting on `render()` or
`exit_code` without checking is wrong in a way the response did not name. → **MISSING PIN P-4**.

### 3.3 WB3 — the message may name the WRONG repository's scopes

`test_the_types_message_names_the_file_the_axis_and_every_parsed_root` iterates
`typecheck_roots(half_gapped_repository.root)` and asserts each appears in the message. The fixture's
roots are `['loremaster', 'skills']` and its testpaths `['loremaster/tests', 'docs/eval']` — **both
strict SUBSETS of this checkout's** (`MEMBERS=(lorerunes lorescribe loresigil loremaster skills
docs/eval scripts)`; `testpaths=[… 'loremaster/tests', 'scripts', 'docs/eval', …]`). So a message
built from the wrong root satisfies the assertion by coincidence. Reproduced with `cwd` set to the
repository root, exactly as pytest runs:

```
===== REF =====
  fixture's OWN typecheck roots : ['loremaster']
  message scope line: … outside every typecheck root declared in scripts/typecheck.sh MEMBERS (loremaster) …
===== WB3 (171 passed / 0 failed) =====
  fixture's OWN typecheck roots : ['loremaster']
  message scope line: … MEMBERS (lorerunes, lorescribe, loresigil, …
```

This is the *arithmetic-alignment* fixture class: `test_readers_answer_for_repo_root_not_for_the
_process_cwd` quantifies the repo-root property over 6 READERS and the message builder is a seventh
call site nothing covers. → **MISSING PIN P-5**.

### 3.4 WB4 + WB9 — two pins stranded by F1's deletion

- **WB4**: `test_the_default_exemption_table_is_the_shipped_one` asserts
  `findings_of(REPO_ROOT) == findings_of(REPO_ROOT, exemptions=())`. Its own comment says *"a build
  defaulting to `()` rather than `EXEMPTIONS` satisfies that assertion either way. This is the line
  that distinguishes them."* Post-F1 `EXEMPTIONS == ()`, so the two calls are **identical** and the
  line distinguishes nothing. WB4 survives. The pin is now mutually exclusive with
  `test_the_table_lands_EMPTY…`: one cannot fail while the other passes.
- **WB9**: `test_covered_ground_beats_an_exemption_so_a_stale_row_becomes_visible` — named and
  commented for the precedence property — **passes `exemptions=()`**, so there is no exemption for
  coverage to beat. It asserts only that a file under a MEMBERS root is `COVERED`, which a dozen
  other pins already do. WB9 reverses precedence and survives. → **MISSING PINS P-6, P-7**.

### 3.5 WB5 / WB19 — which mutation did r5's MP-R6 actually measure?

r5 §4 declares `MP-R6 | the .sh bound reverts to teaching an open hole | 1 | 1 failed, 170 passed |
HELD`. Two distinguishable mutations exist:

| mutation | result |
|---|---|
| **WB5** — bound CONTENT rewritten to *"Committed .sh is gated by NOTHING in this repository"* (identifier intact) | **171 passed — SURVIVED** |
| **WB19** — bound IDENTIFIER changed to `file-types-XX`, content intact | **1 failed, 170 passed** |

WB19's count matches r5's declared `1 failed, 170 passed` exactly; WB5's does not. Independently:
the snapshot of the reference build I took at 20:25 carried `identifier="file-types-XX"` and failed
exactly `test_every_required_bound_is_stated`. I therefore **cannot confirm** that MP-R6 measured
the teaching content it names; the reproducible reading is that it measured the identifier. **What I
measured, and it stands on its own: no pin constrains the CONTENT of any bound's summary beyond
being non-empty, unique-triggered and present in the docstring.** The R6 correction r5 wrote into
the contract's own comment — *"A bound describing a hole already closed is the natural-language
defect inverted — false in the safe direction is still false"* — is unenforced.
→ **MISSING PIN P-8**. (And §7 shows the defect is already live in a *different* bound.)

### 3.6 Negative results, reported because the brief asked

- **exit 5 in either direction IS pinned.** WB7 (5 treated as blind) → 2 failed; WB8 (any exit
  accepted) → 1 failed. The killing pins are `test_a_conftest_is_in_scope_even_when_python_files
  _would_exclude_it` / `test_the_execution_axis_follows_the_configured_patterns` (whose
  `python_files=["check_*.py"]` fixtures collect zero items, producing a legitimate exit 5) and
  `test_a_collector_subprocess_that_fails_is_blind_not_clean`. **It is incidental, not designed** —
  no pin names exit 5 — but it discriminates today. Residual: if either fixture's `python_files`
  value ever changes, the exit-5 property loses its only guard silently.
- **A collector using the live session is caught** (WB10, 11 failed), including under xdist
  reasoning — `test_the_collector_answers_for_repo_root_not_for_the_live_session` fires.
- **`conftest.py`'s by-design zero is not treated as a finding** (WB20, 2 failed) — but only by the
  two REAL-TREE pins, because this checkout happens to contain conftests inside testpaths. No
  fixture forces it. §6 C9.
- **adversary-1's WB28/WB29 and adversary-2's I4/P-2 are genuinely closed** (WB14 → 1 failed,
  WB17 → 2 failed).

---

## 4. MISSING PINS — the test to write, and the defect it catches

**P-1 · the whole-tree wildcard value set must be IDENTICAL on both axes.**
*Test:* parametrize `test_a_whole_tree_member_is_blind_not_clean` over the same set the testpath
pin already uses — `[".", "./", "./.", "..", "/", "/home", ""]` — and, better, share ONE
parametrization constant between the two pins so they cannot drift.
*Defect caught:* `MEMBERS=(loremaster ./)` accepted as a typecheck root, every file marked COVERED,
LEG A reports nothing, served bytes identical to healthy. **Live in the reference build.**
*Both legs proven* (`probe_p2_perturbations.py`, §10.7):
```
[baseline] pristine contract  + REF          -> 4 passed
[leg 1]    PERTURBED contract + REF          -> 2 failed, 4 passed
[leg 2]    PERTURBED contract + CORRECTED    -> 6 passed
PAIR PROVEN: True   (red on the hole, green on the fix)
```
The corrected build replaces the spelling denylist with `if not PurePosixPath(root).parts:` — the
derived property, not a longer list of forbidden spellings.

**P-2 · a higher-precedence config file must make the guard BLIND, not clean.**
*Test:* a fixture repository carrying `mypy.ini` (and `.mypy.ini`) alongside `pyproject.toml`;
`classify` must raise and `ungated_ground(...).blind_sources` must be non-empty, with the render
naming `mypy.ini`. Derive the file list from `mypy.defaults.CONFIG_NAMES + SHARED_CONFIG_NAMES` and
pytest's `_pytest.config.findpaths.locate_config`'s `config_names` rather than hand-listing it —
both are importable by the contract, which already imports `_pytest` for its drift guard.
*Defect caught:* the type gate is off (`exclude` / global `ignore_errors` in `mypy.ini`) and the
guard certifies a fully-gated tree with byte-identical-to-healthy output. **#107's exact shape, live
in the reference build.**
*Note the asymmetry that makes this cheap to argue:* pytest's equivalent shadowing is already caught
by D1's collector, with nobody modelling `pytest.ini`. LEG A has no empirical leg; until it does, the
honest move is to refuse.

**P-3 · blindness-monotonicity must be quantified over the DERIVED failure set, not 4 named doors.**
*Test:* replace the `["members", "testpath", "git", "manifest"]` parametrization with a
constructor-per-state list covering every door that can raise `GuardIsBlind` — runner absent · empty
`MEMBERS` · duplicate `MEMBERS` · each wildcard spelling · phantom root · malformed manifest · no
pytest table · empty testpaths · phantom testpath · unmodelled mypy setting · receipts root not
ruff-excluded · receipts class vacuous · collector non-zero exit · not-a-git-repository · git
missing. For each: `blind_sources` non-empty, `exit_code != 0`, `not is_clean`, and
`render() != healthy`. A helper that enumerates the states once and is used by both the reader-level
and entry-point pins keeps them from drifting apart again.
*Defect caught:* WB1 — 17 false clears at 171/171.

**P-4 · findings-monotonicity at the served surface (the dual of D2).**
*Test:* on a tree with exactly one ungated file: `verdict.findings` non-empty ⟹ `is_clean is False`
**and** `exit_code != 0` **and** `render() != healthy_render` **and** the finding's path appears in
`render()`.
*Defect caught:* WB2 — `findings=1`, `is_clean=True`, `exit_code=0`, `render()` == the clean
sentence, at 171/171.

**P-5 · the MESSAGE's scopes must come from `repo_root`.**
*Test:* build the message on a fixture whose roots/testpaths are **NOT subsets** of this checkout's
(e.g. `members=["alpha_only"]`, `testpaths=["alpha_only/probes"]`) and assert the message contains
those and **contains none of** `typecheck_roots(REPO_ROOT) - fixture_roots`. Equivalently: add the
message builder as a 7th case to `test_readers_answer_for_repo_root_not_for_the_process_cwd`.
*Defect caught:* WB3 — a message that teaches an agent the wrong scopes, at 171/171.
*Fixture note:* `half_gapped_repository`'s scopes must stop being a subset of the real ones, or this
pin inherits the same coincidence.

**P-6 · precedence: COVERED beats EXEMPT_TABLE — with an exemption actually present.**
*Test:* `test_covered_ground_beats_an_exemption_so_a_stale_row_becomes_visible` must pass a real row
rooted at the tree it also adds to `MEMBERS`, and assert `Fate.COVERED`.
*Defect caught:* WB9 — reversed precedence hides a stale row behind its own exemption, so nobody can
tell the row is dead. At 171/171 today because the test passes `exemptions=()`.

**P-7 · the exemption machinery must be exercised even though the table is empty — or the pins must
be deleted.**
*Test:* either (a) parametrize the exemption-behaviour pins over a FIXTURE table and delete
`test_the_default_exemption_table_is_the_shipped_one` (which cannot fail while `EXEMPTIONS == ()`),
or (b) keep it and pin the default by identity: `inspect.signature(gg.classify).parameters
["exemptions"].default is gg.EXEMPTIONS`.
*Defect caught:* WB4. Also makes `test_every_shipped_row_is_load_bearing` honest — today its loop
body never executes:
```
[P2-b] PERTURBED contract (assert False as the FIRST statement of the loop body) + REF -> 1 passed
VACUOUS PIN CONFIRMED: True
```

**P-8 · a stated bound's CONTENT must be checked against the mechanism it describes.**
*Test:* for the bounds whose subject is mechanically checkable, assert the claim: e.g. the
`file-types-modelled` bound must state that `.sh` IS gated on the type axis — derive it, don't
match prose (`"shellcheck" in (REPO_ROOT/"scripts/typecheck.sh").read_text()` ⟹ the bound must not
claim `.sh` is ungated on that axis). Same for `conftest-collection-hooks` (see P-9).
*Defect caught:* WB5 — a bound teaching a closed hole as open, at 171/171; the natural-language
defect class this repo has the most receipts against.

**P-9 · the `conftest-collection-hooks` bound is FALSE and must be re-stated and pinned.**
*Test:* assert the bound's summary does NOT claim `collect_ignore`/`collect_ignore_glob` are
unmodelled, because `test_a_conftest_level_collection_hook_is_caught_too` proves D1 catches them;
the true residual bound is the one `TestLegBIsDerivedFromTheCollector`'s docstring states —
*conftest.py contributes no items by design, so its own reach is bounded by registration.*
*Defect caught:* a served bound that teaches an agent the guard is blind where it is not. r5 applied
exactly this correction to the `.sh` bound (its R6 comment) and not to its sibling. §7.

**P-10 · LEG B's test-shapedness must equal pytest's, including separator-bearing patterns.**
*Test:* an oracle-equality pin in the shape of the existing drift guard — for a matrix of
`python_files` patterns **including at least one containing `/`**, assert
`gg._is_test_shaped(path, patterns) == (_pytest.python.path_matches_patterns(Path(path), patterns)
or Path(path).name == "conftest.py")`. Plus one fixture repository whose `python_files` contains a
separator.
*Defect caught:* 6 measured divergences, every one `guard=False / pytest=True` — a committed
test-shaped file judged `NOT_APPLICABLE` and dropped from LEG B entirely (the PR93 vanished-input
shape, not a false positive). §5.

**P-11 · the instrument's own LEG A coverage must be pinned, as LEG B's already is.**
*Test:* the counterpart to `test_this_contract_is_inside_a_testpaths_entry` —
`any(is_under(relative, root) for root in typecheck_roots(REPO_ROOT))` for both the contract and the
instrument.
*Defect caught:* the module docstring says two obligations are *"pinned in
`TestThisInstrumentRidesTheTypeGateItself`"*. **That class does not exist** (§6 C2). So the class
named `TestThisGuardIsItselfGated` pins the instrument's EXECUTION axis and not its TYPES axis —
**the contract's own self-check is a half-gap, which is the exact class the contract exists to
close** (its docstring: *"Three of the four historical instances of this class were HALF-gaps"*).
Satisfied in fact today only because `scripts` is in `MEMBERS` and only once the files are tracked.

---

## 5. P-PKG — my table, built first, then diffed

Mechanisms specified by this contract, my independent verdicts, then the diff.

| mechanism | library | what I **READ** | my verdict |
|---|---|---|---|
| `python_files` glob → "is this test-shaped?" | `_pytest.pathlib.fnmatch_ex` via `_pytest.python.path_matches_patterns` | **installed source, pytest 9.0.3**: `if sep not in pattern: name = path.name else: name = str(path)`; then `fnmatch.fnmatch(name, pattern)`. `python.py:211` is the only caller | **`replace_with_adapter`** — the instrument is stdlib-only by ruling so it cannot import pytest; it must reproduce the *branch* and the contract must pin it against pytest as an ORACLE (the drift-guard idiom already in the file) |
| mypy config discovery | `mypy.defaults` + `mypy.config_parser` | `CONFIG_NAMES = ['mypy.ini', '.mypy.ini']`, `SHARED_CONFIG_NAMES = ['pyproject.toml', 'setup.cfg']`, `config_parser.py:277` iterates `CONFIG_NAMES + SHARED_CONFIG_NAMES` and stops at the first hit | **`replace`** the pyproject-only read: derive the candidate list from these constants |
| pytest config discovery | `_pytest.config.findpaths.locate_config` | source: `config_names = ["pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"]` — **four** names beat pyproject, not one | **`replace`** any hand-list of shadowing files |
| path containment | `PurePosixPath.is_relative_to` | 6-spelling probe: `.`, `./`, `./.` all → `parts == ()`; `..`, `a/..`, `docs/../.` → non-empty | **`replace`** the spelling denylist `root in {".", ".."}` with `not PurePosixPath(root).parts` |
| shell token split of `MEMBERS=(…)` | `shlex.split` | signature + measured `shlex.split('a "docs/my eval" b')` → 3 tokens vs `str.split`'s 4 | **replace** — the reference build already does |
| bash array PARSE (not split) | `bashlex` | `importlib.util.find_spec('bashlex')` → **not installed** | **`keep_with_trigger`** — regex `^MEMBERS=\(([^)]*)\)` cannot see a multi-line array. **Trigger: the runner's array ever wraps a line.** Escalate for install rather than hand-roll a parser |
| TOML parse | `tomllib` | stdlib; `tomllib.loads` signature | replace — agree |
| tracked-file enumeration | `git ls-files -z` subprocess | `find_spec` → `pygit2`, `dulwich`, `git` (GitPython) **all absent** | **keep** (subprocess, with the `OSError` → blind guard that #131 demands). Escalate if a library is ever wanted; do not vendor |
| structured collection | a JSON-reporting pytest plugin | `find_spec('pytest_jsonreport')` → **not installed** | **keep** stdout parsing of `--collect-only -q`; **trigger:** if the plugin is ever added, the `"::" in line` heuristic should be replaced |
| import-surface scan | `ast` + `sys.stdlib_module_names` | stdlib; derived, not an allowlist | replace — agree |
| shellcheck for the `.sh` leg | `shellcheck` binary | present at `.venv/bin/shellcheck` | n/a — already live in `typecheck.sh` |

### The diff — one row, three surveys, all wrong the same way

| row | author (r1 `:99`, unchanged through r5) | adversary-1 (`:462`) | adversary-2 (`:544`) | me |
|---|---|---|---|---|
| filename glob | `fnmatch` → replace. READ: *"`fnmatch.fnmatch` signature; **it is what pytest's own matcher is built on**"* | agree. READ: *"`fnmatch.fnmatch` signature; used in my build"* | **replace with `fnmatchcase`** — READ the `fnmatch` source, caught `normcase` (Windows only), adjudicated *"immaterial for this project"* | ❗**`replace_with_adapter` — pytest's matcher is `fnmatch_ex`, which is `fnmatch.fnmatch` wrapped in a basename-vs-whole-path DECISION. The wrapper IS the semantics.** 6 measured divergences |

The author's read-column asserts a relationship to pytest's matcher **without opening pytest's
matcher**. That is the P-PKG failure mode named in my own role spec — *"a library can carry the
right function under the wrong semantics; read the source, a name match is not a fit"* — and
adversary-2 went one level deeper into the *right file* and still never reached pytest's. Receipt
(`probe_python_files_oracle.py`, §10.6):

```
[oracle] pytest 9.0.3 _pytest.python.path_matches_patterns
[control] separator-free agreements: 16 (must be > 0)

DIVERGENCES (6) — the guard's LEG B scope != pytest's:
  ['tests/check_*.py']          / loremaster/tests/check_store_lease.py:   guard=False pytest=True
  ['tests/check_*.py']          / docs/consult/tests/check_coherence.py:   guard=False pytest=True
  ['loremaster/tests/test_*.py']/ loremaster/tests/test_store_lease.py:    guard=False pytest=True
  ['**/tests/test_*.py']        / loremaster/tests/test_store_lease.py:    guard=False pytest=True
  ['**/tests/test_*.py']        / skills/lore-deploy/tests/test_port_probe.py: guard=False pytest=True
  ['docs/consult/tests/*.py']   / docs/consult/tests/check_coherence.py:   guard=False pytest=True
```

Every divergence is `guard=False / pytest=True`: a real test file judged not-a-test and dropped from
LEG B. WB21 proves the contract pins the *other* half of the branch (whole-path-always → 17 failed)
and leaves open the half the reference build takes. → **P-10**.

**Rows where I agree with the author and say so:** `tomllib`, `shlex.split`, `git ls-files -z`,
`ast`+`sys.stdlib_module_names`, `PurePosixPath` (adversary-1's row, adopted), the collector
subprocess (r5's row — and my probe independently vindicates it: it is what makes LEG B immune to
`pytest.ini` shadowing, §2.2).

---

## 6. P6 corpse sweep + P6b independent enumeration of what F1 deleted

### 6.1 P6b — enumerated from the contract FIRST, then diffed against r5 §2

I enumerated what a reader of `af4cdab5…` can tell was removed, before reading r5 §2:

| # | behaviour/pin the deletion removed | in r5 §2? | verdict |
|---|---|---|---|
| D-1 | `EXPECTED_EXEMPTION_ROW_COUNT` / `SCRIPTS_EXEMPTION_ROOT` / `SCRIPTS_EXEMPTION_FINDING` anchors | yes | clean removal, no residue |
| D-2 | `TestTheScriptsExemptionIsAFrozenRoster` (whole class) | yes | **residue: cited at line 49 as live ruled design** (C1) |
| D-3 | `frozen_roster` / `frozen_sha` readers, `git ls-tree` seam | yes | clean — zero `frozen_*` / `ls-tree` symbol hits; r5's claim REPRODUCED |
| D-4 | `TestThisInstrumentRidesTheTypeGateItself` (whole class) | **NO** | ❗**not in r5 §2's list, and it takes the instrument's LEG A self-coverage pin with it** (C2 → **P-11**) |
| D-5 | `TestATypecheckRootMayBeASingleFile` (whole class) | **NO** | ❗**not in r5 §2, and `test_every_parsed_typecheck_root_is_a_directory` now asserts the OPPOSITE of the comment that survived it** (C7) |
| D-6 | the real exemption row previously passed to the precedence pin | **NO** | ❗**pin survives, subject deleted → WB9 (P-6)** |
| D-7 | the non-empty `EXEMPTIONS` that made `test_the_default_exemption_table_is_the_shipped_one` and `test_every_shipped_row_is_load_bearing` discriminate | **NO** | ❗**two vacuous pins → WB4 (P-7)** |
| D-8 | adversary-1's pin `test_the_instrument_is_covered_by_a_members_entry_not_by_the_exemption_row` | **NO** | ❗**a missing pin was closed by DELETING the pin** — the obligation is now unpinned (P-11) |

**Four of eight enumerated removals are absent from r5 §2, and all four leave a pin or an obligation
stranded.** This is the P6b instrument doing exactly its job: two independent enumerations, diffed.

### 6.2 P6 — every residual hit, individual verdict

Bare, anchor-free grep (`roster|frozen|ls-tree|exemption row|#188|EXPECTED_EXEMPTION|SCRIPTS_EXEMPTION`),
plus an AST check of every `:class:`/`:meth:` citation.

| # | file:symbol | text | verdict |
|---|---|---|---|
| C1 | module docstring, ¶ after "read it as ruled" (line 48–49) | *"The `scripts` exemption is therefore a **FROZEN ROSTER** derived live from one commit (`:class:`TestTheScriptsExemptionIsAFrozenRoster`)"* | **CORPSE — the worst one.** Teaches a mechanism F1 DELETED as the ruled design, and cites a class that does not exist. It is the FIRST thing a builder reads, and it contradicts line 95 fifty lines below (*"the roster mechanism is retired"*). **Delete the paragraph.** |
| C2 | module docstring line 55 + `TestTheInstrumentIsSelfContained` docstring line 2247 | `:class:`TestThisInstrumentRidesTheTypeGateItself`` and `:meth:`…test_a_file_entry_importing_a_sibling_declares_the_mypypath_its_leg_needs`` | **CORPSE with consequences.** Both citations DANGLE. The docstring says *"Two consequences the builder owes, pinned in \<this class\>"* — neither is pinned. → **P-11** |
| C3 | line 791 comment | *"A MEMBERS entry may be a DIRECTORY or a single FILE (see `TestATypecheckRootMayBeASingleFile`)"* | **CORPSE.** Class deleted; and see C7 — the surviving assertion forbids what this sentence permits |
| C4 | line 1280, inside `test_a_malformed_row_is_rejected…`'s parametrize list | `# the frozen roster is only as sound as the sha it names` | **CORPSE.** A trailing comment annotating a parametrize row that was deleted. Harmless but delete it |
| C5 | `TestMembershipIsPathComponentWise` docstring (line 1007–1008) | *"`scripts` is simultaneously a `testpaths` entry and **the pinned exemption root**, so a substring test would hand a hypothetical `scripts_extra/` BOTH a gate and an exemption"* | **CORPSE.** There is no exemption root. The *test* is still valid (sibling-prefix), its stated rationale is not |
| C6 | line 1038–1039, failure message of `test_a_sibling_prefix_directory_is_neither_gated_nor_exempt` | *"a substring test gave a sibling directory both the gate and **the #188 exemption**"* | **CORPSE in a served failure message** — it teaches a reader that a #188 exemption exists, which `MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM` exists to deny |
| C7 | `test_every_parsed_typecheck_root_is_a_directory` | comment: *"A root may be a directory OR a single file … What it may never be is a phantom"*; assertion: `assert (REPO_ROOT / root).is_dir()` | ❗**FALSE GATE, INVERTED — the message admits what the assertion forbids.** And the module docstring (C2) instructs the builder to add a **FILE** entry, which would turn this pin RED. **WB12 receipt: with `is_dir` removed from the reader, this pin still PASSED** (only `test_a_member_naming_no_directory…` fired) — so it cannot see a guard defect at all; it is a TREE assertion wearing a guard pin's name |
| C8 | line 480–482, `workspace_shaped_repository` comments | *"# exempt by the pinned table on types"* / *"# exempt on types, covered on execution"* for `scripts/registration_sites.py` and `scripts/test_registration_sites.py` | **CORPSE.** Every call site passes `exemptions=()`, and `test_each_named_fate_is_forced_by_a_fixture` pins these very files as **`TYPES-UNGATED`**. The comments describe the opposite of the asserted fate |
| C9 | line 1358 comment | *"If `scripts` were ever added to MEMBERS, the #188 row would be stale"* | **CORPSE.** `scripts` IS in `MEMBERS` as of `bd6fb73`. The conditional is already true and the row is already gone |
| C10 | `TestTheRealRepositoryIsFullyGated` docstring (line 2394–2396) | *"Do not widen the archived-receipts class, and **do not add an exemption row without a finding number and a named re-open trigger**"* | ❗**CORPSE, and a direct contradiction of a PINNED string.** `MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM = "there is no exemption mechanism"` is asserted into every failure message, while the docstring a reader meets on failure offers the deleted route. This is the R4 fix applied to the message and not to the prose beside it |
| C11 | `TestTheExemptionTableIsAnAllowlistOfTheSafe` docstring | *"every exemption is evidence-backed, axis-scoped, and carries a named re-open trigger"* | **LEGITIMATE** — describes the validation RULES, which are still live and still exercised by the malformed-row matrix. No change needed |
| C12 | line 310, `FixtureRepository.stage` docstring | *"The commit is kept after the frozen roster's retirement because…"* | **LEGITIMATE** — a deliberate note explaining why a now-unnecessary commit was retained. Correct form for a retirement note |
| C13 | line 13, module docstring | *"(#188, #233, #261) were HALF-gaps"* | **LEGITIMATE** — historical provenance, not a live mechanism |
| C14 | lines 1250/1252/1289/1291/1303/1305/1323/1325/1334 | `finding="#188"` etc. inside FIXTURE rows | **LEGITIMATE** — fixture data for the validation-rule tests; `#188` is a real finding number and the rows are never shipped |
| C15 | line 104 `frozenset(` · line 2197 *"unlike an exemption row"* · line 142/2102 *"'add a pinned exemption row' names a route F1 DELETED"* | — | **LEGITIMATE** — `frozenset` is a grep artifact; the other three deliberately reference the retired mechanism in the past tense to explain a fix |

Also verified: **zero** `frozen_roster` / `frozen_sha` / `git ls-tree` *symbol* references remain
(r5's claim reproduced), and `:class:`gg.Verdict`` at line 425 is a **valid** cross-module citation
— my own checker flagged it as dangling because it only knows local classes. **That was a false
positive in MY instrument and I am naming it.**

---

## 7. The stated bounds — is each stated where a reader meets it, and TRUE today?

| bound | stated in the docstring? | true today? |
|---|---|---|
| `registration-not-execution` | yes (mechanically pinned: `summary in gg.__doc__`) | **true** |
| `execution-axis-covers-test-shaped-files-only` | yes | **true** — pinned by `test_an_ordinary_module_is_not_judged_on_the_execution_axis` |
| `collection-convention` | yes | **true** |
| `lore-index-axis` | yes, cites `#260` | **true** |
| `untracked-ground` | yes | **true** — pinned by `test_an_untracked_file_is_out_of_scope_by_construction` |
| `file-types-modelled` | yes | **true in the reference build** (`shellcheck` leg verified live in `typecheck.sh`) — but its CONTENT is unpinned (WB5 → P-8) |
| **`conftest-collection-hooks`** | yes | ❗**FALSE.** It states *"collection hooks written in a conftest.py (`collect_ignore`, `collect_ignore_glob`) are **not modelled** and can still make a registered file uncollected."* D1's collector **catches exactly that**, and the contract's own **passing** `test_a_conftest_level_collection_hook_is_caught_too` is the proof. The true residual bound is the one `TestLegBIsDerivedFromTheCollector`'s docstring states: *conftest.py contributes no items by design, so its own reach stays bounded by registration.* → **P-9** |
| *(absent)* LEG A trusts `pyproject.toml` although `mypy.ini` outranks it | — | ❗**MISSING BOUND** — and it should be a closed hole, not a bound → **P-2** |
| *(absent)* LEG B's test-shapedness diverges from pytest for separator-bearing `python_files` | — | ❗**MISSING BOUND** → **P-10** |

The `conftest-collection-hooks` row is the sharpest process point in this report: **r5 identified
this exact defect class, wrote the correction into the contract in a ⚠ comment beside the `.sh`
bound — *"A bound describing a hole already closed is the natural-language defect inverted — false
in the safe direction is still false"* — and did not apply it to the bound one entry below.** The
rider was implemented for the clause it was written next to.

**"No free numerics / interpolate the parsed root set" (brief item 6): CLEAN.** `_render`
interpolates `roots` and `testpaths` from its parameters; no hardcoded root list, no frozen count
survived the retirement (`EXPECTED_EXEMPTION_ROW_COUNT` is gone with no residue).
`PYTEST_DEFAULT_TEST_FILE_PATTERNS` is a constant but is re-derived from pytest's own parser on
every run. One free numeric remains — `len(bound.reopen_trigger.split()) > 1` — and it is
self-documenting; not charged.

---

## 8. P1b — THE QUANTIFIER TABLE (∀-over-inputs vs guarded-by-known-failure-mode)

Every **GUARDED** row carries a receipt: a surviving wrong build walking the same bad outcome through
an unguarded door, or the door-build that died naming the pin that killed it.

| # | invariant | ∀ or GUARDED | receipt |
|---|---|---|---|
| I1 | every tracked `.py` has exactly one fate per axis; every UNGATED fate is reported | **∀-over-inputs** — `assert_every_tracked_file_is_accounted_for` runs on every fixture, conditioned on no cause | WB16 (one axis only) killed by **32**; WB6 (union LEG B) killed by 2 |
| I2 | LEG A coverage ⟺ component-wise under a parsed typecheck root | **∀ over call sites** | WB14 (`startswith` at the LEG A site) killed by 1 — adversary-1's WB28 CLOSED |
| I3 | LEG B coverage ⟺ component-wise under a parsed testpath | **∀ over call sites** | WB15 killed by 4; adversary-1's WB3 shape closed |
| I4 | archived-receipts membership, both axes | **∀ over axes** (r2/r5 fix) | WB17 (substring) killed by 2 — adversary-2's I4/P-2 CLOSED |
| I5 | a scope that widens to the whole tree ⟹ BLIND | ❗**GUARDED BY SPELLING, and the two axes are guarded by DIFFERENT spelling sets** | ❗**REF itself false-clears on `./` and `./.`** (§2.1). Perturbation pair proven (§4 P-1). → **P-1** |
| I6 | LEG A's model of mypy configuration is sound, or the guard refuses | ❗**GUARDED TO ONE FILE** — `pyproject.toml`, which mypy ignores when `mypy.ini` exists | ❗**REF itself false-clears on `mypy.ini` / `.mypy.ini`** (§2.2), verified against installed mypy source. → **P-2** |
| I7 | LEG B's model of pytest configuration is sound | **∀ BY CONSTRUCTION** — D1 asks the collector, so unmodelled mechanisms are caught without being modelled | door-build attempted and it **died**: `pytest.ini redirects testpaths` → 1 finding, bytes distinct (§2.2). WB6 killed by 2, WB10 by 11. **D1 is the strongest thing in this contract** |
| I8 | **blind is not clean, through the SERVED SURFACE** | ❗**GUARDED BY FIVE NAMED DOORS** (3 entry-point pins + a 4-value byte-diff) | ❗**WB1 SURVIVED 171/171 with 17 false clears**; blind coverage 6/26 vs REF's 21/26. → **P-3** |
| I9 | blind is not clean, at the READER | **∀ over 16 reader-level inputs** | WB12 killed by 1; WB11 killed by 4 (the `expected_token` leg — one of r5's unproven items, now PROVEN) |
| I10 | **findings ⟹ the served verdict is not clean** | ❗**NOT PINNED AT ALL** — pinned for blind states and for clean trees only | ❗**WB2 SURVIVED**: `findings=1`, `is_clean=True`, `exit_code=0`, render == the clean sentence. → **P-4** |
| I11 | the failure message names the scopes of the repository it JUDGED | ❗**GUARDED BY A FIXTURE-SUBSET COINCIDENCE** — `half_gapped`'s scopes ⊂ this checkout's | ❗**WB3 SURVIVED**, message names `lorerunes, lorescribe, loresigil…` for a fixture whose only root is `loremaster`. → **P-5** |
| I12 | readers answer for `repo_root`, not the cwd | **∀ over 6 readers** (and `member_mypypath`, `collected_test_files`, `unmodelled_mypy_configuration` are covered incidentally by their own fixtures — WB13 killed by 1, WB10 by 11, WB18 by 1) | the 7th call site — the message builder — is **not** covered: I11 |
| I13 | COVERED beats EXEMPT_TABLE, so a stale row is visible | ❗**NOT PINNED** — the pin named for it passes `exemptions=()` | ❗**WB9 SURVIVED**. → **P-6** |
| I14 | every shipped exemption row is load-bearing | ❗**VACUOUS** — loop over `()` | `assert False` as the loop body's first statement still passes (§4 P-7). → **P-7** |
| I15 | the default `exemptions` is the SHIPPED table | ❗**VACUOUS** — `EXEMPTIONS == ()` makes the two calls identical | ❗**WB4 SURVIVED**. → **P-7** |
| I16 | the table refuses malformed rows | **∀ over 19 shapes**, incl. the `"."`/`"./"` widening roots | rules still exercised though the table is empty; no survivor |
| I17 | LEG B's scope == the set pytest would collect | ❗**GUARDED BY A PARAMETER MONOCULTURE** — every `python_files` fixture is separator-free | ❗**6 oracle divergences on REF** (§5); WB21 proves only the opposite half is pinned. → **P-10** |
| I18 | the collector is a SUBPROCESS over `repo_root`, never the live session | **∀** | WB10 killed by 11, incl. `test_the_collector_answers_for_repo_root_not_for_the_live_session` |
| I19 | a failed collector is blind, an honest empty collect is not | **∀ in both directions** — though **incidentally** | WB7 killed by 2, WB8 killed by 1. Residual: the guard is two fixtures' `python_files` values (§3.6) |
| I20 | file enumeration is NUL-separated and suffix-filtered | **∀** | hostile newline path + `notes.py.txt` both pinned; no survivor |
| I21 | the guard grants its own files no special exemption | **∀** — AST literal scan over the instrument's source | no survivor; adversary-1's WRONG BUILD #2 closed |
| I22 | the instrument imports stdlib only, never the project | **∀** — AST walk incl. lazy imports, derived from `sys.stdlib_module_names` | no survivor |
| I23 | **the instrument is itself gated on BOTH axes** | ❗**GUARDED TO ONE AXIS** — EXECUTION pinned, TYPES not | ❗the docstring cites a DELETED class for the TYPES half (§6 C2/D-4/D-8). → **P-11** |
| I24 | every stated bound is stated, uniquely triggered, and in the docstring | **∀ over `STATED_BOUNDS`** for SHAPE | ❗content unquantified: **WB5 SURVIVED**, and `conftest-collection-hooks` is FALSE today (§7). → **P-8, P-9** |
| I25 | the message carries a contiguous disclaimer and the two ways out | **∀ over findings** | no survivor; R4's five required substrings hold |
| I26 | findings are deterministic and path-ordered | **∀** | no survivor. Residual: the secondary key (two axes, one path) is unordered — cosmetic, not charged |

---

## 9. ESCALATIONS — questions for the lead, not decisions

**E1 — the contract author's THROWAWAY REFERENCE BUILD was sitting in the tree at
`scripts/gated_ground.py` while the builder was working, and r5 reported it deleted.**
r5 §"1." states *"Frozen at md5 `89cea408…`; throwaway reference build deleted."* At 20:25–20:31 EDT
2026-07-29 that path held a file whose own docstring reads:

> *"THROWAWAY REFERENCE BUILD — satisfiability receipt for scripts/test_gated_ground.py … Written by
> contract-44-gatedground-1 … It is DELETED at the end of that run and must never be committed.
> ⚠ NOT A DESIGN TO CLONE. Nothing here has been graded by an adversary or an audit. A builder that
> reproduces this file inherits every ungraded choice in it."*

`builder-44-instrument-1` was concurrently running `scripts/mutation_proof.py --file
scripts/gated_ground.py` against it (observed on the process table, anchors matching that file's
`_render`). By 20:55 the path held a different, larger build. **I graded neither, and I make no claim
about what the builder did or did not inherit.** But the artifact's own warning is that reading it is
the hazard, and the report that promised its deletion is the reason nobody would look for it.
*Question:* does the builder's output need a provenance check against that file, and should the
"delete the reference build" step become a verified receipt rather than a claim?

**E2 — r5's mutation-proof count contradicts itself inside one report.** §4's heading reads
*"Mutation proofs — **2 runs**, both observed columns filled"* above a table of **4 rows**, and §5
opens *"You required a mutation proof per new/changed pin. **I ran two.**"* Both cannot be right.
Related: §3.5 shows MP-R6's declared `1 failed, 170 passed` reproduces for an **identifier** mutation
and not for the **content** mutation it is named for. *Question:* can r5's exact mutation texts be
recovered, or should the four proofs be re-run with declared node ids via `scripts/mutation_proof.py`?

**E3 — the frozen contract moved after it was frozen, untracked, with no receipt.** §0.1. The file
is untracked, so `89cea408…` is unrecoverable. *Question:* who edited it, and can the contract be
committed so the next adversary grades a git object instead of a working-tree file?

**E4 — `test_every_parsed_typecheck_root_is_a_directory` will go RED the day a builder follows the
module docstring.** The docstring instructs a per-FILE `MEMBERS` entry; the assertion demands
`is_dir()`. Today it is moot (`MEMBERS` is all directories, and `scripts` covers the instrument), so
this is a latent trap rather than a live one. *Question:* delete the file-entry prose, or relax the
assertion to "exists"? (§6 C7 — my recommendation is to delete the prose, since F1 made the file
entry unnecessary.)

**E5 — noticed, outside my target, escalated per scope law.** `scripts/typecheck.sh`'s shell leg
runs `git ls-files -z '*.sh'` and aborts if it matches nothing. The gated-ground instrument's own
`.sh` bound depends on that leg staying live, and **nothing in packet 44 pins it**. A one-line pin
(`"shellcheck" in typecheck.sh` ⟹ the `file-types-modelled` bound must claim closure) would tie the
bound to the mechanism — this is the mechanical half of **P-8**.

---

## 10. Instruments — VERBATIM (brief-base §1: not committable by me, so pasted)

All seven live at `/home/ejprice/scratch/adv44-3/`, which is **not a durable address**, so they are
reproduced here in full. Recommend committing them to `scripts/` if the lead wants them re-runnable;
`probe_python_files_oracle.py` and `probe_leg2_forgery.py` are the two worth keeping as permanent
guards.

### 10.1 `make_wrong_builds.py` (+ `add_builds_b.py`, `add_builds_c.py`)

Exact-string patcher. **A patch whose anchor is missing or non-unique is a hard error** — that is
the "if step N silently no-opped, would step N+1 read as success?" guard, and it fired for real
during my run (a heredoc double-escaped `\n`, the anchor legitimately failed, and I fixed the anchor
rather than the report).

```python
#!/usr/bin/env python3
"""Derives wrong builds of gated_ground.py from a reference build by exact-string patching."""
from __future__ import annotations
import sys
from pathlib import Path

WRONG_BUILDS: dict[str, list[tuple[str, str]]] = {}

WRONG_BUILDS["WB1_blindness_guarded_by_the_five_pinned_doors"] = [(
    """    except GuardIsBlind as exc:
        return Verdict(findings=(), blind_sources=(str(exc),))""",
    """    except GuardIsBlind as exc:
        message = str(exc)
        pinned = (
            "cannot find a MEMBERS=(...) declaration" in message
            or "widens to the whole tree" in message
            or "cannot run `git`" in message
            or ("cannot read" in message and "pyproject.toml" in message)
            or "extend-exclude" in message
        )
        if pinned:
            return Verdict(findings=(), blind_sources=(message,))
        return Verdict(findings=(), blind_sources=())""")]

WRONG_BUILDS["WB2_served_surface_ignores_findings"] = [
    ("""    @property
    def is_clean(self) -> bool:
        return not self.findings and not self.blind_sources""",
     """    @property
    def is_clean(self) -> bool:
        return not self.blind_sources"""),
    ("""        if not self.findings:
            return "GATED GROUND: every committed .py is registered on both axes."
        return "\\n\\n".join(finding.message for finding in self.findings)""",
     """        return "GATED GROUND: every committed .py is registered on both axes."""" + '"'),
]

WRONG_BUILDS["WB3_message_scopes_come_from_the_cwd"] = [(
    """        verdicts = classify(repo_root, exemptions=exemptions)
        roots = typecheck_roots(repo_root)
        testpaths = pytest_testpaths(repo_root)""",
    """        verdicts = classify(repo_root, exemptions=exemptions)
        roots = typecheck_roots(Path.cwd())
        testpaths = pytest_testpaths(Path.cwd())""")]

WRONG_BUILDS["WB4_default_is_a_literal_empty_tuple"] = [
    ("def classify(repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS)",
     "def classify(repo_root: Path, *, exemptions: Sequence[Exemption] = ())"),
    ("def ungated_ground(repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS)",
     "def ungated_ground(repo_root: Path, *, exemptions: Sequence[Exemption] = ())"),
    ("""def unmodelled_mypy_configuration(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
)""",
     """def unmodelled_mypy_configuration(
    repo_root: Path, *, exemptions: Sequence[Exemption] = ()
)"""),
]

WRONG_BUILDS["WB5_file_types_bound_teaches_a_closed_hole_as_open"] = [(
    '''            "This quantifies over tracked .py. Committed .sh IS gated on the type axis — the "
            "derived shellcheck leg in typecheck.sh is live — and is gated by nothing on the "
            "execution axis; .pyi and every other extension are unmodelled here."''',
    '''            "This quantifies over tracked .py. Committed .sh is gated by NOTHING in this "
            "repository - no shell gate of any kind exists - and .pyi and every other extension "
            "are unmodelled here."''')]

WRONG_BUILDS["WB6_control_collector_never_consulted"] = [(
    """            elif any(is_under(path, scope) for scope in scopes) and (
                axis is GateAxis.TYPES
                or Path(path).name == "conftest.py"
                or path in collected
            ):""",
    """            elif any(is_under(path, scope) for scope in scopes):""")]

WRONG_BUILDS["WB7_exit_five_is_blind"] = [
    ("    if completed.returncode not in {0, 5}:", "    if completed.returncode != 0:")]
WRONG_BUILDS["WB8_any_collector_exit_is_an_honest_zero"] = [
    ("    if completed.returncode not in {0, 5}:",
     "    if completed.returncode not in {0, 5, 3, 4, 1, 2}:")]

# WB9: precedence reversed — the EXEMPT_TABLE branch is moved ABOVE the COVERED branch.
WRONG_BUILDS["WB9_exemption_beats_coverage"] = [(
    """            elif any(is_under(path, scope) for scope in scopes) and (
                axis is GateAxis.TYPES
                or Path(path).name == "conftest.py"
                or path in collected
            ):
                fates[axis] = Fate.COVERED
            elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
                fates[axis] = Fate.EXEMPT_ARCHIVED_RECEIPTS
            elif any(
                row.axis is axis
                and is_under(path, row.root)
                for row in exemptions
            ):
                fates[axis] = Fate.EXEMPT_TABLE""",
    """            elif any(
                row.axis is axis
                and is_under(path, row.root)
                for row in exemptions
            ):
                fates[axis] = Fate.EXEMPT_TABLE
            elif any(is_under(path, scope) for scope in scopes) and (
                axis is GateAxis.TYPES
                or Path(path).name == "conftest.py"
                or path in collected
            ):
                fates[axis] = Fate.COVERED
            elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
                fates[axis] = Fate.EXEMPT_ARCHIVED_RECEIPTS""")]

# WB10: LEG B reads the LIVE session's items (found via gc) before falling back to the subprocess.
WRONG_BUILDS["WB10_collector_reads_the_live_session"] = [(
    """    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )""",
    """    live = sys.modules.get("_pytest.config")
    if live is not None:
        import gc
        for obj in gc.get_objects():
            if type(obj).__name__ == "Session" and hasattr(obj, "items"):
                contributing = frozenset(
                    str(item.location[0]) for item in getattr(obj, "items", []) or []
                )
                if contributing:
                    _COLLECTED_CACHE[key] = contributing
                    return contributing
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            cwd=repo_root, capture_output=True, text=True, check=False,
        )""")]

# --- second batch: escape-free anchors (add_builds_b.py) ---
WRONG_BUILDS["WB11_blind_render_names_nothing"] = [
    ('+ "; ".join(self.blind_sources)', '+ ""')]
WRONG_BUILDS["WB12_roots_need_not_exist"] = [(
    '        if not (repo_root / root).is_dir():\n'
    '            raise GuardIsBlind(f"typecheck root {root!r} is not a directory in {repo_root} '
    '— {_BLIND}")',
    '        pass  # WB12: a phantom root is accepted')]
WRONG_BUILDS["WB13_member_mypypath_always_empty"] = [
    ('    if "MEMBER_MYPYPATH=(" not in text:\n        return {}',
     '    if True:  # WB13\n        return {}')]
WRONG_BUILDS["WB14_control_startswith_at_the_types_site"] = [(
    '            elif any(is_under(path, scope) for scope in scopes) and (',
    '            elif any(\n'
    '                (path.startswith(scope) if axis is GateAxis.TYPES else is_under(path, scope))\n'
    '                for scope in scopes\n'
    '            ) and (')]
WRONG_BUILDS["WB15_control_conftest_not_test_shaped"] = [
    ('    return name == "conftest.py" or any(fnmatch.fnmatch(name, pattern) for pattern in patterns)',
     '    return any(fnmatch.fnmatch(name, pattern) for pattern in patterns)')]
WRONG_BUILDS["WB16_control_only_types_findings_are_emitted"] = [
    ('            if verdict.fates[axis] is Fate.UNGATED:',
     '            if verdict.fates[axis] is Fate.UNGATED and axis is GateAxis.TYPES:')]
WRONG_BUILDS["WB17_control_receipts_by_substring"] = [
    ('            elif is_under(path, ARCHIVED_RECEIPTS_ROOT):',
     '            elif path.startswith(ARCHIVED_RECEIPTS_ROOT):')]
WRONG_BUILDS["WB18_mypy_refusal_only_when_already_dirty"] = [(
    '    unmodelled = unmodelled_mypy_configuration(repo_root, exemptions=exemptions)\n'
    '    if unmodelled:',
    '    unmodelled = unmodelled_mypy_configuration(repo_root, exemptions=exemptions)\n'
    '    if unmodelled and len(tracked_python_files(repo_root)) > 4:')]

# --- third batch (add_builds_c.py) ---
WRONG_BUILDS["WB19_bound_identifier_broken_content_intact"] = [
    ('identifier="file-types-modelled"', 'identifier="file-types-XX"')]
WRONG_BUILDS["WB20_conftest_by_design_zero_becomes_a_finding"] = [(
    '                axis is GateAxis.TYPES\n'
    '                or Path(path).name == "conftest.py"\n'
    '                or path in collected',
    '                axis is GateAxis.TYPES\n'
    '                or path in collected')]
WRONG_BUILDS["WB21_test_shaped_matches_the_whole_path"] = [(
    '    name = Path(path).name\n'
    '    return name == "conftest.py" or any(fnmatch.fnmatch(name, pattern) for pattern in patterns)',
    '    name = Path(path).name\n'
    '    return name == "conftest.py" or any(fnmatch.fnmatch(path, pattern) for pattern in patterns)')]


def main() -> int:
    reference = Path(sys.argv[1]).read_text(encoding="utf-8")
    out_dir = Path(sys.argv[2]); out_dir.mkdir(parents=True, exist_ok=True)
    for name in (sys.argv[3:] or list(WRONG_BUILDS)):
        source = reference
        for anchor, replacement in WRONG_BUILDS[name]:
            if anchor not in source:
                raise SystemExit(
                    f"FATAL: patch anchor for {name!r} not found in the reference build. "
                    f"An unapplied patch would look like a surviving wrong build.\nanchor:\n{anchor}")
            if source.count(anchor) != 1:
                raise SystemExit(f"FATAL: anchor for {name!r} appears {source.count(anchor)} times")
            source = source.replace(anchor, replacement)
        assert source != reference, f"{name} produced an unchanged file"
        (out_dir / f"{name}.py").write_text(source, encoding="utf-8")
        print(f"built {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 10.2 `run_contract_against.sh`

```bash
#!/usr/bin/env bash
# Runs the REAL contract against a candidate gated_ground.py inside an isolated scratch repo
# (git archive + fresh `git init` — never a cp -a of a worktree, per lore #284/#140).
set -uo pipefail
SCRATCH=/home/ejprice/scratch/adv44-3/refrepo
CANDIDATE="$1"; shift
cp "${CANDIDATE}" "${SCRATCH}/scripts/gated_ground.py" || exit 1
OUT=$(cd "${SCRATCH}" && ./.venv/bin/python -m pytest scripts/test_gated_ground.py \
        -q -p no:cacheprovider -n 16 "$@" 2>&1)
echo "${OUT}" | grep -E "^(FAILED|ERROR)" | sed 's/^/    /'
TAIL=$(echo "${OUT}" | tail -3 | grep -E "passed|failed|error|no tests ran")
# The COUNT is the receipt: a run that collected the wrong number of tests is not a result.
TOTAL=$(echo "${TAIL}" | grep -oE "[0-9]+ (passed|failed)" | grep -oE "[0-9]+" | paste -sd+ | bc)
echo "  $(basename "${CANDIDATE}") => ${TAIL}   [collected total: ${TOTAL:-NONE}]"
if [ "${TOTAL:-0}" != "171" ]; then echo "    !! WARNING: total != 171 — this run is not comparable"; fi
```

### 10.3 `probe_wildcard_asymmetry.py`

Establishes §2.1. Controls: healthy→clean · dirty→findings · the PINNED spelling `.` must raise.
Full source omitted only where it duplicates 10.5's fixture builder; the discriminating body is:

```python
for spelling in ("./", "./.", "docs/../."):
    case = build_repo(..., members=["loremaster", spelling],
                      ungated_file="docs/consult/coherence_check.py")
    try:
        roots = gg.typecheck_roots(case)
        print(f"    typecheck_roots ACCEPTED it -> {roots}")
    except gg.GuardIsBlind as exc:
        print(f"    blind (SAFE): {str(exc)[:80]}"); continue
    verdict = gg.ungated_ground(case, exemptions=())
    types_findings = [f for f in verdict.findings if f.axis is gg.GateAxis.TYPES]
    print(f"    BYTES IDENTICAL TO HEALTHY: {verdict.render() == healthy_bytes}")
    if not types_findings:
        print("    *** FALSE CLEAR ***"); failures += 1
```

`load_instrument` note, worth keeping: `importlib.util.module_from_spec` must be registered in
`sys.modules` **before** `exec_module`, or `dataclasses` raises
`AttributeError: 'NoneType' object has no attribute '__dict__'` on the first `@dataclass`.

### 10.4 `probe_leg2_forgery.py` — the derived {dependency} × {verb} matrix

The failure set is DERIVED, not curated: dependencies = `scripts/typecheck.sh` · `pyproject.toml` ·
the git index · the collector subprocess; verbs = missing · empty · malformed · whole-tree-wildcard ·
duplicate-declaration · phantom-target · non-zero-exit · shadowed-by-a-higher-precedence-file.
26 constructed states, each byte-diffed against the healthy render. Controls: healthy→clean,
dirty→findings, and `assert blind_seen > 0` so a "no false clears" result cannot be a probe artifact.
Case table (the part worth re-typing; the builder is 10.5's, plus `no_members_line`,
`second_members`, `malformed_pyproject`, `omit_pytest_table`, `no_git` switches):

```python
CASES = [
    ("runner absent",              "typecheck.sh", "missing",     {"omit_runner": True}),
    ("no MEMBERS declaration",     "typecheck.sh", "empty",       {"no_members_line": True,
                                    "decoy": "# The MEMBERS=(decoy) mention is prose.\n"}),
    ("empty MEMBERS array",        "typecheck.sh", "empty",       {"members": ""}),
    ("two MEMBERS declarations",   "typecheck.sh", "duplicate",   {"members": "loremaster docs",
                                    "second_members": "MEMBERS=(loremaster)\n"}),
    ("MEMBERS wildcard '.'",       "typecheck.sh", "whole-tree",  {"members": "loremaster ."}),
    ("MEMBERS wildcard './'",      "typecheck.sh", "whole-tree",  {"members": "loremaster ./"}),
    ("MEMBERS wildcard './.'",     "typecheck.sh", "whole-tree",  {"members": "loremaster ./."}),
    ("MEMBERS wildcard '/'",       "typecheck.sh", "whole-tree",  {"members": "loremaster /"}),
    ("MEMBERS phantom root",       "typecheck.sh", "phantom",     {"members": "loremaster deleted_member"}),
    ("pyproject absent",           "pyproject.toml", "missing",   {"omit_pyproject": True}),
    ("pyproject malformed",        "pyproject.toml", "malformed", {"malformed_pyproject": True}),
    ("no [tool.pytest] table",     "pyproject.toml", "empty",     {"omit_pytest_table": True}),
    ("empty testpaths",            "pyproject.toml", "empty",     {"testpaths": ""}),
    ("testpaths wildcard '.'",     "pyproject.toml", "whole-tree",{"testpaths": '"loremaster/tests", "."'}),
    ("testpaths wildcard './'",    "pyproject.toml", "whole-tree",{"testpaths": '"loremaster/tests", "./"'}),
    ("testpaths phantom",          "pyproject.toml", "phantom",   {"testpaths": '"loremaster/tests", "docs/eval"'}),
    ("mypy exclude",               "pyproject.toml", "unmodelled",{"mypy_extra": 'exclude = ["loremaster/store/.*"]'}),
    ("mypy global ignore_errors",  "pyproject.toml", "unmodelled",{"mypy_extra": "ignore_errors = true"}),
    ("receipts not ruff-excluded", "pyproject.toml", "unbacked",  {}),   # ruff extend-exclude trimmed
    ("no receipts file at all",    "pyproject.toml", "vacuous",   {}),   # git rm --cached the receipt
    ("collector conftest raises",  "collector",    "non-zero-exit",
        {"extra_files": (("loremaster/tests/conftest.py", "raise RuntimeError('boom')\n"),)}),
    ("git binary missing",         "git index",    "missing",     {}),   # PATH -> empty dir
    ("not a git repository",       "git index",    "missing",     {"no_git": True}),
    ("mypy.ini SHADOWS pyproject", "pyproject.toml", "shadowed",  {}),
    ("pytest.ini SHADOWS pyproject","pyproject.toml","shadowed",  {}),
    ("setup.cfg SHADOWS pyproject","pyproject.toml", "shadowed",  {}),
]
```

### 10.5 `probe_config_shadowing.py` — establishes §2.2

```python
def build(root: Path, *, sidecar: tuple[str, str] | None, ungated: bool) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=root, check=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "scripts" / "typecheck.sh").write_text(
        '#!/usr/bin/env bash\nset -uo pipefail\nMEMBERS=(loremaster)\n'
        'for member in "${MEMBERS[@]}"; do uv run mypy "${member}"; done\n', encoding="utf-8")
    (root / "pyproject.toml").write_text(
        '[project]\nname = "fixture"\nversion = "0.0.0"\n\n'
        '[tool.uv.workspace]\nmembers = ["loremaster"]\n\n'
        '[tool.ruff]\nextend-exclude = ["scratchpad", "docs/plans/v2/receipts"]\n\n'
        '[tool.mypy]\npython_version = "3.14"\nstrict = true\n\n'
        '[tool.pytest.ini_options]\nasyncio_mode = "auto"\ntestpaths = ["loremaster/tests"]\n',
        encoding="utf-8")
    files = [("loremaster/tests/test_store_lease.py", TEST_BODY),
             ("loremaster/store/lease.py", MODULE_BODY),
             ("docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py", MODULE_BODY)]
    if ungated:
        files.append(("docs/consult/coherence_check.py", MODULE_BODY))
    if sidecar is not None:
        files.append(sidecar)
    for relative, body in files:
        target = root / relative; target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
    subprocess.run(["git", "add", "-A"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "-c", "user.name=p", "-c", "user.email=p@example.invalid",
                    "commit", "-q", "-m", "f"], cwd=root, check=True, capture_output=True)
    return root

SIDECARS = [
    ("mypy.ini excludes the ONLY typecheck root",
     ("mypy.ini", "[mypy]\nexclude = (?x)(^loremaster/)\n"), "mypy.ini BEATS pyproject.toml"),
    ("mypy.ini turns errors off globally",
     ("mypy.ini", "[mypy]\nignore_errors = True\n"), "the type gate is a no-op"),
    (".mypy.ini excludes the only root",
     (".mypy.ini", "[mypy]\nexclude = (?x)(^loremaster/)\n"), "same precedence"),
    ("setup.cfg mypy section excludes the only root",
     ("setup.cfg", "[mypy]\nexclude = (?x)(^loremaster/)\n"), "LOWER precedence — harmless"),
    ("pytest.ini redirects testpaths",
     ("pytest.ini", "[pytest]\ntestpaths = loremaster/store\n"), "pytest.ini BEATS ini_options"),
    ("tox.ini [pytest] section",
     ("tox.ini", "[pytest]\ntestpaths = loremaster/store\n"), "lower precedence — harmless"),
]
# every case runs on an OTHERWISE FULLY GATED tree, so `served == healthy_bytes` means the guard
# certified a tree whose gate had been switched off.
```

### 10.6 `probe_python_files_oracle.py` — oracle equality against pytest itself

```python
from _pytest.python import path_matches_patterns   # THE ORACLE

PATHS = ["loremaster/tests/test_store_lease.py", "loremaster/tests/check_store_lease.py",
         "docs/consult/tests/check_coherence.py", "tools/promotion_test.py", "conftest.py",
         "loremaster/tests/conftest.py", "scripts/registration_sites.py",
         "skills/lore-deploy/tests/test_port_probe.py"]
PATTERN_SETS = [["test_*.py", "*_test.py"], ["check_*.py"],          # control: separator-free
                ["tests/check_*.py"], ["loremaster/tests/test_*.py"],  # separator-bearing
                ["**/tests/test_*.py"], ["docs/consult/tests/*.py"]]

root = Path("/repo_root_stand_in")
for patterns in PATTERN_SETS:
    has_sep = any("/" in p for p in patterns)
    for relative in PATHS:
        oracle = (path_matches_patterns(root / relative, patterns)
                  or Path(relative).name == "conftest.py")
        guard = gg._is_test_shaped(relative, patterns)
        if guard != oracle:
            divergences.append(f"{patterns!r} / {relative}: guard={guard} pytest={oracle}")
        elif not has_sep:
            control_agreements += 1
assert control_agreements > 0, "PROBE ARTIFACT — the control set never agreed"
```

### 10.7 `probe_p2_perturbations.py` — perturbations with the correct-build control leg

```python
CORRECTION_A = (   # the corrected build for P2-a: a derived property, not a longer denylist
    '        if root in {".", ".."} or Path(root).is_absolute() or ".." in parts:',
    '        if not PurePosixPath(root).parts or Path(root).is_absolute() or ".." in parts:')

PERTURBATIONS = {
    "P2-a_members_wildcard_value_set": (
        '@pytest.mark.parametrize("wildcard", [".", "..", "/", "/home"])\n'
        '    def test_a_whole_tree_member_is_blind_not_clean',
        '@pytest.mark.parametrize("wildcard", [".", "./", "./.", "..", "/", "/home"])\n'
        '    def test_a_whole_tree_member_is_blind_not_clean',
        "TestTheGuardFailsLoudRatherThanBlind::test_a_whole_tree_member_is_blind_not_clean"),
    "P2-b_load_bearing_row_loop_is_empty": (
        '        for row in gg.EXEMPTIONS:\n'
        '            without = tuple(other for other in gg.EXEMPTIONS if other is not row)',
        '        for row in gg.EXEMPTIONS:\n'
        '            assert False, "PERTURBATION: this line proves the loop body executes"\n'
        '            without = tuple(other for other in gg.EXEMPTIONS if other is not row)',
        "TestTheExemptionTableIsAnAllowlistOfTheSafe::test_every_shipped_row_is_load_bearing"),
}
# Each perturbation edits a SCRATCH COPY of the contract, runs the named node against REF, then
# against the CORRECTED build, and restores the pristine contract in a `finally`.
```

Output reproduced in §4 (P-1, P-7). The contract in the repo was never touched; the perturbations
were applied to the scratch copy only, and restored.

---

## 11. VERDICT

# CONTRACT INSUFFICIENT

**21 wrong builds · 15 killed · 6 survived at 171 passed / 0 failed** — plus **two false clears in
the reference build itself**, which no wrong build was needed to find, and **6 oracle divergences**
against pytest's own matcher.

This is a strong contract, and it got stronger in r5: D1 is the best thing in it — the collector
makes LEG B immune to config shadowing *without modelling the config*, which is the only place in
this instrument where an open set is closed by construction rather than by enumeration. The
membership call-site pins, the hostile-path forgery leg, the anti-vacuity family and the
allowlist-the-safe mypy refusal all held against everything I threw at them.

The failure is a single, nameable shape, and it is the one this repo has the most receipts against:
**r5 fixed the instances the previous adversary named, not the quantifiers behind them.** D2 answered
"four builds swallowed blindness" with four byte-diff cases and three entry-point pins — so WB1,
which honours exactly those five doors, walks 17 false clears through the other twenty-one. The
findings side of the same served surface was never quantified at all (WB2). And F1's deletion left
three pins whose subjects are gone: one whose loop body cannot execute, one whose two calls are now
identical, and one that passes `exemptions=()` to a test named for exemption precedence.

The 11 missing pins in §4 are each one function to write. **P-1** (share one wildcard value set
between the axes), **P-2** (`mypy.ini` outranks `pyproject.toml` — #107's shape, live), **P-3**
(quantify blindness over the derived failure set), **P-4** (findings-monotonicity), and **P-10**
(oracle-equality against `fnmatch_ex`) are the five I would not ship without.

---

*Measured 2026-07-29 in worktree `.claude/worktrees/pkt44` at HEAD `96816cc`, against
`scripts/test_gated_ground.py` md5 `af4cdab58c9c24f72557d5cfb9ae38f3` (2404 lines, 171 collected),
verified unchanged at the start and the end of this run. All claims are dated and scoped to that
artifact; a later revision of the contract may have closed any of them.*
