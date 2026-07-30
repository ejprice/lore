brief-base v9 read

# REPORT-contract-44-gatedground-1 — CONTRACT for packet 44's derived gated-ground invariant

*All measurements in this report were taken 2026-07-29 in the worktree
`.claude/worktrees/pkt44` on branch `pkt44/ungated-ground`, at **`8015d22`** unless another
sha is named. HEAD moved four commits under me mid-run (`5a850c3 → … → 8015d22`, the peer
config wave) — §7 records the consequence, which is material.*

---

## SUMMARY BLOCK

- `brief-base v9 read`
- **state: done-with-deviations** — **revision 2**, incorporating the lead's consolidated recursion
  correction. **130 pins**; 128 green, **2 EXPECTED-RED by design** (§R); **8 mutation proofs held**.
- **the correction is APPLIED IN FULL** — file-granularity `MEMBERS` roots, coverage-before-exemptions,
  stdlib-only, the sharing ruling, and the rider. Item-by-item table in §R.
- deviation 1: **two files, not one** (§F1) — and the correction's ruling #3 **sharpens this fork with a
  new measurement**: the instrument module needs NO `MYPYPATH`, but the contract file's entry DOES.
  Measured both ways in §R.3. **This may change your F1 ruling; please read it.**
- deviation 2: **LEG B derives its patterns from pytest's `python_files`** (§F2). Ruling #3 forced this
  from a live pytest probe to a pinned CONSTANT + a drift guard that re-derives it every gate run —
  **strictly stronger than what I had**, §R.4.
- deviation 3: throwaway `scripts/gated_ground.py` existed in this worktree in two short windows to run
  the receipts; deleted, `find` confirms zero, bytes in §9.
- deviation 4: the brief's expected-RED pin went green mid-run (peer config wave, §7). **The correction
  restores two expected-RED pins**, which only the instrument's builder can discharge.
- **capability gaps (brief-base §4): NO `mcp__lore_lore__*` tools and NO `SendMessage`.** §Capability.
- **a false gate in MY OWN pin, caught by my own satisfiability probe and fixed** — §R.5. It demanded a
  finding number on the same line as the path, which honest multi-line commentary never does.
- `Packages considered:` `tomllib` → **replace** · pytest `python_files` default (READ:
  `_pytest.python.pytest_addoption` source + `get_config([])._parser._inidict` probe) →
  **replace_with_adapter** (constant in the stdlib-only instrument + a drift guard in the contract;
  the adapter is one tuple) · `git ls-files -z` → **replace** · `fnmatch` → **replace** ·
  `scripts/mutation_proof.py` → **replace** · `sys.stdlib_module_names` + `ast` → **replace** a
  maintained allowlist · `MEMBERS=(…)` read → **bespoke** · `mypy.find_sources` /
  `pytest --collect-only` → **keep_with_trigger**, triggers named. Full table §2.
- **decisions-needed (4 open forks: F1, F2, F3, F5)** — F4 is closed by events; every F3 item is
  disclosed and numbered.
- receipt pointers: correction adjudication §R · satisfiability §6.1 · 8 mutation proofs §6.2 ·
  pre-config-wave replay §6.3 · post-wave satisfiability of the expected-RED pins §6.4 ·
  wrong-build table §4 · adversarial pre-flight §3 · realism checklist §5 · instruments §9.

---

## Capability check (brief-base §4, first thing)

| demanded | what I actually have | what I did instead | what a lead must change |
|---|---|---|---|
| project law: lore-first for code-structure; brief read #4 implies the `lore_findings` ledger for #188/#233/#238/#260/#261 | **no `mcp__lore_lore__*` tools at all** — `ToolSearch "select:mcp__lore_lore__lore_findings,…"` and a keyword search both returned *No matching deferred tools found* | `git grep` over the tracked tree for every finding number; the design sidecar's and sweep's ledger quotes are my only ledger source, and I treat them as **inherited, un-re-derived** | either grant the `tdd-contract` agent definition the lore tools, or state in the brief that ledger facts arrive via the spec. This is the sixth instance of the crippled-agent-definition class flagged 2026-07-28 |
| file/bash/write | present | — | — |
| `scripts/mutation_proof.py`, `git`, `uv`, `pytest`, `ruff` | present | — | — |
| spawn brief / harness: *"you MUST use the SendMessage tool"* to reach the lead | **no `SendMessage` tool** — ToolSearch finds none | this report file is the only channel I have. Per brief-base §1 that is the durable one anyway, so nothing is lost — but the lead must PULL it, not wait for a ping | grant the tool, or drop the SendMessage instruction from `tdd-contract` briefs so the next author does not assume a channel exists |
| **forbidden**: `cp -a`/`scratch_copy.sh` of this worktree | honoured — **zero copies made** | every fixture is `tmp_path` + `git init` from EMPTY; the one replay (§6.3) uses `git archive` (read-only) into a fresh `git init`, and asserts `.git` is a DIRECTORY not a FILE | — |

Also honoured: I never staged, committed or reverted anything. `git status` shows my contract as
the only file I added.

---

## 1. Deliverables

| file | what it is |
|---|---|
| `scripts/test_gated_ground.py` | **THE CONTRACT**, revision 2. 1864 lines, 89 test functions → **130 collected**. md5 `77a0cde8bdc6a7f2a12bcb7a8cda5682` at delivery. Contains its own fixture builder (`FixtureRepository`) — **no sibling fixture helper module was needed**, so none was created. |

**The API surface the contract DEFINES** (the builder implements `scripts/gated_ground.py`):

```
GuardIsBlind(RuntimeError)          InvalidExemption(ValueError)
GateAxis{TYPES, EXECUTION} + .label   Fate{COVERED, EXEMPT_TABLE, EXEMPT_ARCHIVED_RECEIPTS,
                                            UNGATED, NOT_APPLICABLE}
Exemption(root, axis, finding, reason, reopen_trigger)   — validating, frozen
StatedBound(identifier, summary, reopen_trigger, finding)
UngatedFile(path, axis, message)    FileVerdict(path, fates: Mapping[GateAxis, Fate])
EXEMPTIONS: tuple[Exemption, ...]   STATED_BOUNDS: tuple[StatedBound, ...]
THREAT_MODEL: str                   ARCHIVED_RECEIPTS_ROOT: str
PYTEST_DEFAULT_TEST_FILE_PATTERNS: tuple[str, ...]   — stdlib-only; drift-guarded by the contract
typecheck_roots(repo_root)          pytest_testpaths(repo_root)
workspace_members(repo_root)        ruff_excluded_trees(repo_root)
pytest_test_file_patterns(repo_root)  unmodelled_mypy_configuration(repo_root, *, exemptions=…)
tracked_python_files(repo_root)     is_under(path, tree)
classify(repo_root, *, exemptions=EXEMPTIONS) -> list[FileVerdict]
ungated_ground(repo_root, *, exemptions=EXEMPTIONS) -> list[UngatedFile]
```

Every reader takes an explicit `repo_root` (§Q3.3 / FU1-C) — that is what makes `tmp_path` fixture
repositories possible without ever copying this worktree.

---

## 2. PACKAGE SURVEY — one row per mechanism the contract specifies

| mechanism | libraries evaluated (name + version) | what I READ | verdict |
|---|---|---|---|
| TOML parsing (`testpaths`, workspace members, ruff excludes, mypy table) | `tomllib` (stdlib, py3.14) | `scripts/registration_sites.py::declared_members` — the repo already uses exactly this for the same manifest; no second reader invented | **replace** — no hand-parsing. ⚠ ONE-IMPLEMENTATION note in §F3(h): `declared_members` and the contract's `workspace_members` are the same query; the builder should escalate whether to share rather than quietly write copy #2 |
| pytest's test-file patterns / defaults | `pytest` 8.x via `_pytest.python.pytest_addoption` and `_pytest.config.get_config` | **source read**: `pytest_addoption` declares `"python_files", default=["test_*.py", "*_test.py"]`. **Live probe**: `get_config([])._parser._inidict["python_files"][2]` → `['test_*.py', '*_test.py']`, obtained WITHOUT parsing any config file | **replace_with_adapter.** The instrument is stdlib-only by ruling, so it cannot import pytest: the adapter is **one tuple** (`PYTEST_DEFAULT_TEST_FILE_PATTERNS`) plus a **drift guard in the contract**, which pytest is already running and which re-derives the real declaration every gate run. Strictly better than importing pytest in the instrument — a stale constant is caught by the gate, and nothing depends on a private attribute at runtime. Kills a one-pattern hardcode AND a build that ignores a configured override. §R.4 |
| glob matching of a filename against those patterns | `fnmatch` (stdlib) | `fnmatch.fnmatch` signature; it is what pytest's own matcher is built on | **replace** hand-rolled `startswith`/`endswith` pattern logic |
| committed-file enumeration | `git ls-files -z` | **measured, not assumed** (probe in §3, adversarial item 7): on a path containing a newline, `git ls-files` emits `"pkg/we\nird.py"` — QUOTED and backslash-escaped — while `-z` emits the raw bytes. A line-splitting reader therefore returns a string that is not the path | **replace** a directory walk; and the NUL form specifically, pinned by `test_a_path_containing_a_newline_survives_enumeration_intact` |
| mypy's REAL file discovery (`mypy.find_sources.create_source_list`) | `mypy` ≥1.17 | `REPORT-sweep-44-1.md` §9 read in full: it probed both signatures live and adopted them for the SWEEP | **keep_with_trigger — deliberately NOT adopted here.** §Q3 rules this instrument a REGISTRATION guard (path membership in the gates' config), not a discovery guard; asking mypy would make the guard's answer depend on an internal API and on mypy being importable at gate time. The unmodelled-config REFUSAL (`unmodelled_mypy_configuration`) is the ruled substitute. **Trigger: the day `[tool.mypy]` gains `exclude`, or a `foo.py` lands beside a `foo/` inside a member** — at which point registration and discovery diverge and the refusal fires by design |
| pytest's REAL collection (`pytest --collect-only`) | `pytest` 8.x | same sweep §9 row (it read the node-id output shape) | **keep_with_trigger — deliberately NOT adopted.** Same reason, plus: shelling out to pytest from inside a pytest run is a re-entrancy seam, and it is exactly the script-with-wrapper shape §Q3.1 forbids. **Trigger: a demand to prove COLLECTION rather than REGISTRATION** — that is a different instrument and a different packet |
| bash-array read of `MEMBERS=(…)` | none adopted; `bashlex` considered | the real `scripts/typecheck.sh` (one `^MEMBERS=(` line, verified by `grep -nE '^[A-Z_]+=\('` → exactly one array at `8015d22`) | **bespoke**, minimal surface: one line-anchored regex. `bashlex` is not installed (an install authorization), and the only stdlib-shaped alternative is `source`-ing the runner, which **runs the gate as a side effect of reading it**. Pinned against a decoy `MEMBERS=(…)` mention inside a comment |
| mutation proving | `scripts/mutation_proof.py` (in-repo) | its `--help`: exactly-once anchor matching, **both-ways** diff of the declared RED set, content-restore with md5 verification, and the warning that a piped run under `set -e` throws away the helper's exit code | **replace** hand-run mutation shell blocks. All five proofs in §6.2 ran through it with ids declared from `--collect-only` BEFORE each run |
| the property itself (per-axis gate registration, exemption adjudication) | — | — | **domain logic.** This is packet 44's business rule; no package models "is this tree registered with this repo's gates" |

---

## 3. Adversarial pre-flight — every realistic input that could break the unit

| # | failure mode | covered by |
|---|---|---|
| 1 | **Wrong unit — path-string vs path-components.** `scripts_extra/` passing as `scripts` | `TestMembershipIsPathComponentWise` (12-row matrix + a fixture where `scripts` is BOTH a gate root and the exemption root). **Mutation-proved**: §6.2 MP4 |
| 2 | **Wrong scale — the union property.** Both gate sets collapsed into one, so a half-gap reads as covered | `TestThePropertyIsPerAxisNotBinary` (4 pins on a repo built to hold nothing but the two half-gaps). **Mutation-proved**: §6.2 MP1 |
| 3 | **Wrong anchor — `repo_root` ignored, the process cwd answered instead.** Every fixture would then silently grade the REAL repo | `test_readers_answer_for_repo_root_not_for_the_process_cwd`, parametrised over all six readers, against `distinctly_configured_repository` where **every** parsed value differs from this checkout's (coincidence is not discrimination) |
| 4 | **Null / empty — a silent no-op that prints as a clean tree.** Empty `MEMBERS`, absent declaration, missing runner, empty/absent `testpaths`, no pytest table, missing manifest, non-repo root | `TestTheGuardFailsLoudRatherThanBlind`, 12 pins, each a single-variable perturbation of a **healthy control repository** that is itself pinned (`test_the_healthy_control_repository_raises_nothing`) |
| 5 | **Degenerate driver table — a `MEMBERS` entry that widens to the whole tree** (`.`, `..`, `/`, an absolute path) or names a deleted directory. This is the nastiest: it marks EVERY file gated and prints zero findings | `test_a_whole_tree_member_is_blind_not_clean` (4 params) + `test_a_member_naming_no_directory_is_blind_not_clean` + the testpath analogue |
| 6 | **Zero / boundary — vacuous everything.** Zero tracked `.py`, an enumeration that reached only part of the tree, an exemption class matching nothing, a classifier stuck at one verdict | `TestAntiVacuity` (4) + `TestTheArchivedReceiptsClass` (6) + `test_every_shipped_row_is_load_bearing` |
| 7 | **Real-distribution tail — a committed path git cannot render on one line.** git permits newlines in paths; measured, `git ls-files` quotes them and `-z` does not | `test_a_path_containing_a_newline_survives_enumeration_intact` |
| 8 | **Rendered stored text forging structure.** A committed path carrying a newline plus a line shaped exactly like the guard's own header | `test_a_hostile_path_cannot_forge_a_second_finding_row` — header-line count must equal finding count. Mechanism-agnostic (quote, escape or fence — the contract does not pick) |
| 9 | **Producer↔consumer seam: the fixture stops modelling the real config.** A fixture repo whose `MEMBERS` line shape has drifted from the runner's | `test_fixture_members_line_matches_the_real_runner` — the fixture builder's renderer must reproduce a line of the LIVE `scripts/typecheck.sh` |
| 10 | **Producer↔consumer seam: `typecheck.sh` silently drops a workspace member** | `test_typecheck_roots_cover_every_declared_workspace_member` (§Q3.3's cross-derivation pin) |
| 11 | **A gate that reaches a tree and checks nothing** — a `testpaths` entry pointing at an empty or deleted directory | `test_every_parsed_testpath_exists_as_a_directory` + the blind-guard raise |
| 12 | **Config the guard does not model.** A future `[tool.mypy] exclude` or an `ignore_errors` override makes a file ungated IN FACT while passing path membership | `TestMypyConfigurationThisGuardDoesNotModel` (5), including a **positive control** proving the three relaxation shapes the repo actually uses do NOT trip the refusal (a false gate here would get the guard switched off), and a pin that the **whole verdict** refuses — not merely a reader nobody calls. **Mutation-proved**: §6.2 MP5 |
| 13 | **An exemption that is stale, unbounded, or carries a drifting count** | `TestTheExemptionTableIsAnAllowlistOfTheSafe` (10), including 11 malformed-row params, a well-formed positive control, axis-scoping, root-scoping, the no-digits-in-reason rule (FU1-A), and load-bearing-by-mutation |
| 14 | **The next skill, not the one that was found.** The config wave registers `skills/lore-deploy/*`; a NEW skill must still be caught | `test_a_new_skill_tree_is_reported_even_though_a_sibling_skill_is_registered` — the quantifier law, refusing to condition the invariant on the instance that prompted the work |
| 15 | **Input vanishes between classification and report** (PR93 D1's exact shape: supply fine, totals conserved, an input gone) | `assert_every_tracked_file_is_accounted_for`, applied in **every** case in the suite. **Mutation-proved both legs**: §6.2 MP2 (emission drop) and MP3 (classification drop) |
| 16 | **The guard exempts itself** — the recursion the sweep escalated (§8.4) | `test_the_guard_grants_its_own_files_no_special_exemption` |
| 17 | **Non-determinism** — findings reshuffle so two gate outputs cannot be diffed | `test_findings_are_ordered_deterministically` (two runs equal + path-ordered) |
| 18 | Untracked scratch counted as committed ground | `test_an_untracked_file_is_out_of_scope_by_construction`, `test_untracked_files_are_excluded` |
| 19 | **SCOPED OUT — committed `.sh` files.** The repo gained a shell gate at `2bc7e97`; this guard's property is Python-only and §Q3 does not extend it | not covered. The sweep already surfaced this to the operator (`REPORT-sweep-44-1.md` §8.1); I did not widen the spec. **Fork F3(i)** |
| 20 | **SCOPED OUT — `GIT_DIR`/`GIT_WORK_TREE` environment pollution** redirecting the enumeration | not covered. Out of the stated threat model (honest engineer, not a hostile environment); the cwd/anchor pin (#3) covers the realistic half |
| 21 | **SCOPED OUT — wall-clock budget.** The guard runs in the standard gate | not pinned; a timing assertion is flaky by nature. Measured at `8015d22`: the whole contract runs in **1.13 s**, so there is no budget question today |

---

## 4. Wrong-build table — every pin, and the wrong build it kills

| pin | wrong build it kills |
|---|---|
| `TestThePropertyIsPerAxisNotBinary` (4) | **#1, the headline:** the packet's literal UNION property. At `5a850c3` it reported **zero** findings over a tree with 4 untyped `docs/eval` modules and 8 uncollected `skills` test files (§6.3) |
| `test_a_new_skill_tree_is_reported…` | a guard whose LEG B is satisfied because the ONE skill that prompted the fix got registered |
| `test_prefix_membership` ×12 + `test_a_sibling_prefix_directory…` | `str.startswith` membership — a sibling directory inheriting both a gate and an exemption |
| `TestTheGuardFailsLoudRatherThanBlind` ×12 | a guard that returns `[]` when it cannot parse its inputs: **blind printed as clean** |
| `test_a_whole_tree_member_is_blind_not_clean` ×4 | a `MEMBERS` parse that widens to `.` — every file "gated", zero findings, a false clear wearing a clean bill of health |
| `test_a_members_mention_inside_a_comment_is_not_the_declaration` | an unanchored regex that parses a comment as the declaration |
| `test_readers_answer_for_repo_root_not_for_the_process_cwd` ×6 | readers that shell out or open relative paths with the process cwd — every fixture in this file would silently grade the real repo and pass |
| `test_typecheck_roots_cover_every_declared_workspace_member` | `typecheck.sh` silently dropping a workspace member |
| `test_fixture_members_line_matches_the_real_runner` | fixtures that have drifted from the file the guard parses — a suite green about a world that no longer exists |
| `TestMypyConfigurationThisGuardDoesNotModel` (5) | (a) honouring a future `[tool.mypy] exclude` silently; (b) a reader that reports unmodelled config which `classify` never consults; (c) — the positive control — a build that refuses `ignore_missing_imports` and gets switched off inside a week |
| `test_the_table_holds_exactly_one_row_at_landing` | an exemption table that grows by builder edit rather than by operator ruling |
| `test_no_exemption_reason_carries_a_measured_count` | FU1-A's own confessed defect: a drifting error count baked into a row's prose |
| 11 malformed-row params + the well-formed control | validation that accepts a row with no finding number or no trigger — **and** validation that rejects everything (the probe firing for the wrong reason) |
| `test_an_exemption_is_scoped_to_its_axis` | treating an exemption row as an exemption from the whole guard |
| `test_every_shipped_row_is_load_bearing` | a dead exemption row nobody can tell is dead |
| `test_covered_ground_beats_an_exemption…` | precedence that lets a stale row hide behind its own exemption |
| `TestTheArchivedReceiptsClass` (6) | a receipts class that is a growing list; one anchored in the guard's opinion rather than in ruff's committed declaration; one that matches nothing; one that exempts only the types axis |
| `assert_every_tracked_file_is_accounted_for` (every case) | an input that vanishes — classified-but-unreported, or never classified. Conditioned on NO cause |
| `test_each_named_fate_is_forced_by_a_fixture` ×9 + `test_the_execution_axis_exempt_table_fate_is_reachable` | a ∀-helper evaluated only where a branch cannot fire. Every fate on every axis has a fixture that FORCES it |
| `TestAntiVacuity` (4) | a zero that is an artifact: empty file list, an enumeration that missed a member, empty parsed roots, a classifier stuck at one verdict |
| `test_a_path_containing_a_newline…` | `git ls-files` + `splitlines()` — a path that is not the path |
| `test_a_hostile_path_cannot_forge_a_second_finding_row` | a render in which committed stored text can forge a finding row an agent will act on |
| `TestTheExecutionAxisScope` (7) | a hardcoded `test_*.py` list (misses `*_test.py`); a build that derives LEG B from `python_files` alone and loses every `conftest.py`; a build that reports library modules as execution-ungated (the false positive that gets a gate switched off) |
| `TestTheFailureMessage` (6) | a message that does not name the scope the file is outside of; one that promises mypy ran; one that invites an exemption with no finding number or trigger; one that tells the reader to widen the receipts class; one with no scannable header |
| `TestTheInstrumentStatesItsThreatModelAndBounds` (5) | an instrument whose threat model lives in a report instead of in the file — the absence that cost a previous gate two fix waves; and bounds with no named re-open trigger |
| `TestThisGuardIsItselfGated` (4) | a guard sitting outside `testpaths` (a hope with a filename); one that exempts itself by name; one that launders its verdict through a subprocess exit code |
| `TestTheRealRepositoryIsFullyGated` (1) | **the tree growing new ungated ground.** Proven able to fire: 12 findings at `5a850c3`, 0 at `8015d22` (§6.3) |

---

## 5. Realism & independence checklist

- ☑ **Production-realistic inputs.** Every fixture path is a real repository path or a plausible
  next one: `docs/eval/smoke_p8b.py`, `skills/lore-deploy/tests/test_port_probe.py`,
  `scripts/registration_sites.py`, `docs/plans/v2/receipts/2026-07-20-probes/probe_budget.py`,
  `loremaster/tests/test_store_lease.py`. The mypy-override fixtures reproduce the three relaxation
  shapes the real manifest actually carries (`follow_untyped_imports`, `ignore_missing_imports`,
  `disallow_any_unimported=False`). No `foo`/`bar`, no `x=1`; the module body is a real-looking
  module.
- ☑ **Independent expected values.** Expectations come from the ruled spec (§Q3.1–§Q3.8, FU1-A/C/D),
  from pytest's OWN source (`python_files` default), and from git's OWN measured behaviour (the
  quoting difference). The `str.startswith` vs `Path.parts` matrix is hand-computed from path
  semantics, not from any implementation. **Tautology check applied**: the pins that could have been
  tautological are the message pins — so they assert content the BUILDER writes (the instrument's
  docstring, `THREAT_MODEL`, each `StatedBound.summary`), never content this contract supplies.
  *Would these still hold if the implementation were subtly wrong?* Answered by measurement, not
  assertion: **8 mutation proofs, 8 declared RED sets, 8 exact matches** (§6.2).
- ☑ **Seam / boundary coverage.** Four real handoffs are exercised with real values:
  `scripts/typecheck.sh` → the parser (`test_fixture_members_line_matches_the_real_runner`, which
  reproduces a LIVE line of the runner); `pyproject.toml` → `tomllib` (fixtures are parsed by the
  same parser production uses); `git` → the enumeration (NUL vs line encoding, measured);
  `[tool.uv.workspace] members` → `MEMBERS` (the ⊇ cross-derivation pin). The cwd/`repo_root` pin
  covers the seam where a reader could answer about the wrong tree.
- ☑ **Magnitude / sanity bound on derived outputs.** Mostly *not applicable, pure logic* — the
  numeric outputs are `len()` over set-membership results. The two non-trivial guards that ARE the
  magnitude class: `test_every_declared_workspace_member_contributed_files_and_all_are_covered`
  (∀ over members, derived — catches an enumeration that reached only part of the tree, which is the
  order-of-magnitude failure here) and the conservation pin `len(verdicts) == len(tracked)`.
- ☑ **Shared domain conventions, never hardcoded literals.** Member names, testpaths, ruff
  exclusions and the receipts address are all READ from the live config at assertion time, never
  copied. The two literals I pin — `EXPECTED_EXEMPTION_ROW_COUNT = 1` (spec'd by FU1-A) and the pytest default set (re-derived from pytest on every run by the §R.4 drift guard, so it cannot go stale silently) — the first is spec'd by FU1-A and its
  failure message tells the reader to update it *and cite the ruling*. `ARCHIVED_RECEIPTS_ROOT` is
  pinned by derivation (∈ ruff's `extend-exclude`, matches ≥1 tracked file, is a single `str`), not
  by literal equality.
- ☑ **Hostile fixtures for rendered stored text.** A committed path is stored text this guard
  interpolates into output an agent parses. Two hostile pins: newline-survives-enumeration, and the
  forgery pin whose fixture path contains a newline **plus a line shaped exactly like the guard's own
  header**. Delimiter runs are not applicable — the render has no fence syntax to break out of; the
  header line is the only structure, and it is the thing the forgery attacks.
- ☑ **Input accounting (totality).** `assert_every_tracked_file_is_accounted_for` is a **shared
  helper applied across every case**, not a bespoke test: each tracked `.py` has exactly one fate per
  axis, no duplicates, no vanished inputs, no invented ones, and `ungated_ground`'s output equals
  exactly the UNGATED verdicts. **Fate coverage**: 9 parametrised pins force COVERED / EXEMPT_TABLE /
  EXEMPT_ARCHIVED_RECEIPTS / UNGATED on TYPES and COVERED / EXEMPT_ARCHIVED_RECEIPTS / UNGATED /
  NOT_APPLICABLE on EXECUTION, plus `test_the_execution_axis_exempt_table_fate_is_reachable` which
  forces the one fate the SHIPPED table cannot reach (it has no execution-axis row) using a fixture
  table rather than leaving the branch unexecuted. **Mutation proof**: MP2 and MP3, one for each leg.

---

## 6. Receipts

### 6.1 Satisfiability — 0 failed against a known-correct build

```
$ for i in 1 2 3; do uv run --no-sync pytest scripts/test_gated_ground.py -q; done
2 failed, 128 passed in 0.94s     <- the 2 are TestThisInstrumentRidesTheTypeGateItself,
2 failed, 128 passed in 0.87s        EXPECTED RED by design (§R item 1); satisfiable, §6.4
2 failed, 128 passed in 0.88s

$ uv run --no-sync pytest scripts/test_gated_ground.py -q \
    --deselect scripts/test_gated_ground.py::TestThisInstrumentRidesTheTypeGateItself
128 passed, 2 deselected in 0.80s

$ uv run --no-sync pytest scripts -q -n auto --deselect <the two above>
480 passed in 7.60s               <- the gate neighbourhood, contract included

$ uv run ruff check scripts/test_gated_ground.py
All checks passed!
```

**Every pin except the two builder-requirement pins is green against a known-correct build**, three
runs running. The two REDs are the contract doing its job: they demand a `typecheck.sh` edit that only
the instrument's builder can make, and §6.4 proves they turn green when it is made.

**Provenance receipt (#140 law):** `gated_ground.__file__ =
/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44/scripts/gated_ground.py` — the reference
build was a **throwaway written into this worktree and deleted**, never a copy of it. No
`scratch_copy.sh`, no `cp -a`, no second `.git`. Window: 2026-07-29 **16:45:59Z → 16:53:47Z**;
`git status` after deletion shows only `?? scripts/test_gated_ground.py` from me.

With the throwaway removed, the contract is **RED as delivered**, which is contract-first working:

```
E   ModuleNotFoundError: No module named 'gated_ground'
ERROR scripts/test_gated_ground.py
1 error in 0.14s
```

### 6.2 Mutation proofs — 5 run through `scripts/mutation_proof.py`, all declared BEFORE the run

Node ids taken from `--collect-only` (which names tests without running them, so the declared set is
fixed before any result exists), never transcribed from output. Every run restored the tree
byte-exact by content.

| # | mutation | declared RED | observed | verdict |
|---|---|---|---|---|
| MP1 | the UNION property, EXECUTION leg: a file under a typecheck root counts as execution-covered | 7 ids | 7 failed, 115 passed | **PROOF HELD — fired EXACTLY** |
| MP2 | `ungated_ground` silently drops one classified-UNGATED file (PR93 D1's emission-plumbing shape) | 1 id | 1 failed, 121 passed | **PROOF HELD — fired EXACTLY** |
| MP3 | `classify` never emits a verdict for one tracked file (input vanishes upstream) | 1 id | 1 failed, 121 passed | **PROOF HELD — fired EXACTLY** |
| MP4 | `is_under` → `path.startswith(tree)` | 6 ids | 6 failed, 117 passed | **PROOF HELD — fired EXACTLY** |
| MP5 | `classify` computes `unmodelled_mypy_configuration` and never consults it | 1 id | 1 failed, 122 passed | **PROOF HELD — fired EXACTLY** |
| MP6 | file-granularity `MEMBERS` entries silently dropped from the parsed roots (`.exists()` → `.is_dir()`) | 2 ids | — | **PROOF HELD — fired EXACTLY** |
| MP7 | the instrument acquires a project import (`import loremaster`) | 2 ids | — | **PROOF HELD — fired EXACTLY** |
| MP8 | the pinned pytest default drifts to one pattern | 3 ids | — | **PROOF HELD — fired EXACTLY** |

MP6–MP8 ran with `TestThisInstrumentRidesTheTypeGateItself` **deselected**, stated here rather than
buried: those two pins are red before the mutation, so leaving them in would have forced me to declare
already-red ids and blunted the both-ways diff.

MP2 and MP3 together are the input-accounting clause's required mutation proof — the helper is
demonstrated failing on *both* the classification leg and the emission leg.

### 6.3 The strongest receipt — replay against the pre-config-wave tree

The brief predicted the real-repo pin would be RED until the peer config wave landed. **It landed
mid-run**, so the pin is green at HEAD and a "122 passed" receipt alone would prove nothing about
whether it can ever fire. So I replayed the guard against `5a850c3` — the sha the brief was written
against — using `git archive` (read-only on this worktree) into a **fresh `git init`** repository,
asserting `.git` is a DIRECTORY not a FILE:

```
MEMBERS at 5a850c3   = ['lorerunes', 'lorescribe', 'loresigil', 'loremaster', 'skills']
testpaths at 5a850c3 = ['lorerunes/tests', 'lorescribe/tests', 'loresigil/tests',
                        'loremaster/tests', 'scripts', 'docs/eval']

FINDINGS AT 5a850c3: 12
  TYPES     docs/eval/connections_p8a.py
  TYPES     docs/eval/evaluation_harness_p8a.py
  TYPES     docs/eval/smoke_p8b.py
  TYPES     docs/eval/test_smoke_p8b.py
  EXECUTION skills/lore-deploy/scripts/test_conformance_provenance.py
  EXECUTION skills/lore-deploy/scripts/test_lore_deploy.py
  EXECUTION skills/lore-deploy/scripts/test_merge_mcp_json.py
  EXECUTION skills/lore-deploy/scripts/test_read_config_field.py
  EXECUTION skills/lore-deploy/scripts/test_scaffold_config.py
  EXECUTION skills/lore-deploy/tests/test_containerfile_locked.py
  EXECUTION skills/lore-deploy/tests/test_port_probe.py
  EXECUTION skills/lore-deploy/tests/test_workspace_probe.py

FINDINGS AT WORKTREE HEAD (8015d22): 0
```

**That is the packet's whole thesis, measured**: the guard, had it existed, would have named every
one of the four half-gaps this packet was minted to close — and reports nothing once they are closed.
The union property the packet's own sentence specifies would have reported **zero** on that tree.

The replay script is small enough to reproduce from this description, but per brief-base §1 it is a
load-bearing instrument, so its bytes are in §9.2.

### 6.4 The two EXPECTED-RED pins are satisfiable — a red pin nobody has seen turn green is a demand, not a contract

Same replay instrument (§9.2): `git archive HEAD` (read-only) into a **fresh `git init`**, then simulate
the builder's wave — copy both instrument files in, append the two file-granularity entries to `MEMBERS`
with a three-line comment block naming the `#188` dissolution trigger, `git add`. Then run **the real pin
bodies**, imported from the contract with `REPO_ROOT` repointed — never a paraphrase of them, because a
probe that re-implements what it checks proves nothing:

```
PROVENANCE contract.__file__   = /tmp/gatedground-requirement-satisfiable/scripts/test_gated_ground.py
PROVENANCE instrument.__file__ = /tmp/gatedground-requirement-satisfiable/scripts/gated_ground.py
instrument paths derived: ['scripts/gated_ground.py', 'scripts/test_gated_ground.py']
PIN 1 GREEN — instrument COVERED by a MEMBERS entry, not by the exemption row
PIN 2 GREEN — every file entry named in the comment block, which cites a finding
TOTAL ungated findings after the simulated wave: 0
```

And the ruled mechanism behaving exactly as designed, from the same run:

```
MEMBERS after the builder's wave: [... , 'docs/eval', 'scripts/gated_ground.py',
                                          'scripts/test_gated_ground.py']
  scripts/gated_ground.py                TYPES=covered        <- by its own entry
  scripts/test_gated_ground.py           TYPES=covered        <- by its own entry
  scripts/registration_sites.py          TYPES=exempt-table   <- the #188 row still load-bearing
```

**This run is also what caught the false gate in §R.5** — its first pass reported
`cites-finding=False` against an honest comment block, and the pin was wrong, not the block.

---

## 7. ⚠ THE TREE MOVED UNDER ME — and it changes the brief's central prediction

At spawn, HEAD was `5a850c3`. During my run the peer `builder-44-config-1` committed five times;
HEAD is now `8015d22`. Material consequences, each re-derived rather than inherited:

| brief said | measured at `8015d22` |
|---|---|
| "the ONE pin that asserts the REAL repo is clean will be RED until `builder-44-config-1` lands" | **it is GREEN.** `typecheck.sh` MEMBERS now carries `docs/eval`; `testpaths` now carries `skills/lore-deploy/scripts` and `skills/lore-deploy/tests`. There is **no expected-RED pin** in this contract |
| "docs/eval relics still present" | **archived** at `439b55d`; `docs/eval` holds 2 tracked `.py` |
| `scripts/` is not a typecheck root | still true — `MEMBERS=(lorerunes lorescribe loresigil loremaster skills docs/eval)`. The single `#188` exemption row is therefore **load-bearing**, and its pin proves it |
| — | **NEW, and the lead should know:** a shell gate landed (`shellcheck-py` + a shellcheck leg). `grep -nE '^[A-Z_]+=\('` finds exactly one array in `typecheck.sh`, so the `MEMBERS` parse is unaffected. But the `.sh` axis is now a *real* gate this guard does not model — fork F3(i) |

Also note the ordinary risk this creates: **if any later wave adds `scripts` to `MEMBERS` without
deleting the `#188` exemption row, `test_every_shipped_row_is_load_bearing` goes RED.** That is the
pin doing its job, not a defect — but a builder meeting it cold will need this sentence.

---

---

## R. The lead's consolidated recursion correction — adjudicated item by item

*Received after revision 1 was delivered; applied in full. Contract went 123 → **130 pins**.*

| ruled item | what I did | receipt |
|---|---|---|
| **1. The instrument's file becomes its own `MEMBERS` entry; the BUILDER adds it (a phantom entry makes mypy exit `Cannot read file`); contract it as a REQUIREMENT** | `TestThisInstrumentRidesTheTypeGateItself` — 2 pins, **EXPECTED RED until the builder lands**. The instrument's paths are **DERIVED** from `__file__` and `gg.__file__`, never listed, so the pin is right whether the instrument ships as one file or two | mypy's phantom-entry behaviour measured: `mypy: error: Cannot read file 'scripts/does_not_exist.py'`. Pins proven **satisfiable** (not merely red) in §6.4 |
| **2. LEG A computed against ALL parsed entries incl. FILE entries, component-wise, BEFORE exemptions. An entry covers ITSELF. No hardcoded self-mention** | `TestATypecheckRootMayBeASingleFile` — 2 pins: a file entry covers that file **and not its siblings**; a file entry inside the exempted tree is `COVERED`, while the tree's **residue stays `EXEMPT_TABLE`** (so the #188 row is not quietly retired). `is_under` already makes an entry its own prefix — **no code path names the instrument** | **MP6** held exactly. The blind-guard pin changed from *"is not a directory"* to *"names nothing that exists"*, so a file root is legal and a phantom still is not |
| **3. Instrument must be STDLIB-ONLY and self-contained** | `TestTheInstrumentIsSelfContained` — 2 pins, **DERIVED from `sys.stdlib_module_names`**, never a maintained allowlist; walks the whole AST (lazy imports are a house idiom and are exactly where a project import hides) and rejects relative imports | **MP7** held exactly. ⚠ **This forced a real design change** — see §R.3 and §R.4 |
| **4. Two `tomllib` readers of one registry are consumers, not policy clones; do NOT import `registration_sites.py`** | **Ruled, not re-litigated.** My revision-1 escalation F3(8) is **withdrawn**. The ruling is now *enforced*: `test_the_instrument_does_not_import_the_project` forbids the import, and its comment records the reasoning so the next reader does not re-open it | **MP7** covers it (`import loremaster` reddens both pins) |
| **5. RIDER: mutation-proof the file-leg; the `typecheck.sh` entry carries a comment naming its dissolution trigger** | `test_every_file_granularity_members_entry_carries_a_dissolution_trigger` — ∀ over file entries, **plus an anti-vacuity leg** so it cannot pass by there being no file entries. The **mutation proof of the leg itself is a BUILDER receipt** I could not run (I may not edit `typecheck.sh`): stated as an owed receipt in §R.6 | §R.5 records a **false gate in my first version of this pin**, caught and fixed |
| **6. Wrong build #2 (self-exemption by hardcoded path)** | `test_the_guard_grants_its_own_files_no_special_exemption` already existed; its comment now names wrong build #2 explicitly and explains why the mechanism is the fix | in the wrong-build table §4 |

### R.3 ⚠ Ruling #3 interacts with fork F1, and the measurement should reach you before you rule

Ruling #3's stated motivation is *"so the file-leg typechecks without a `MYPYPATH`"*. Under my
two-file deviation that is **half true**, measured at `8015d22`:

```
uv run mypy scripts/gated_ground.py                     -> resolves standalone, no MYPYPATH ✓
uv run mypy scripts/test_gated_ground.py                -> 14 errors, ALL no-any-unimported
                                                            (the unfollowed `import gated_ground`)
MYPYPATH=scripts uv run mypy scripts/test_gated_ground.py -> the 14 vanish; only the module's
                                                            own errors remain ✓
```

So: **the instrument module needs no `MYPYPATH`; the contract file's entry needs `MYPYPATH=scripts`.**
That cost is small and *precedented twice in this repo* — the new `docs/eval` leg uses
`MYPYPATH=docs/eval`, and `test_forgery_door_sweep.py`'s own self-check already runs
`MYPYPATH=scripts:{declared_path}`. But it is a cost that **the one-file design does not pay at all**,
and it is a fact you did not have when you ruled. **If you rule F1 → one file, the change is
mechanical** (fold the instrument into the contract file; the two `TestThisInstrumentRidesTheTypeGate
Itself` pins keep working unchanged, because they derive the instrument's paths rather than listing
them — that was designed for exactly this).

### R.4 Ruling #3 made the pytest-defaults question STRONGER, not weaker

Revision 1 had the instrument ask pytest for its `python_files` default
(`get_config([])._parser._inidict`). Stdlib-only forbids that. Rather than fall back to an
unverified constant, the resolution splits the concern:

- the **instrument** carries `PYTEST_DEFAULT_TEST_FILE_PATTERNS` as a constant (stdlib-only ✓);
- the **contract** — which pytest is already running, so it may import pytest — re-derives pytest's
  own declaration on **every gate run** and pins the constant against it
  (`test_the_declared_default_matches_what_pytest_itself_declares`).

That is better than revision 1: a constant that drifts is caught by the gate, and the instrument no
longer depends on a private pytest attribute at runtime. **MP8** proves it: dropping `*_test.py` from
the constant reddens exactly three pins.

### R.5 A false gate in my own pin — caught by my own satisfiability probe

My first `dissolution-trigger` pin required the finding number to appear **on the same line as the
entry path**. The satisfiability probe (§6.4) wrote a perfectly honest three-line comment block — paths
on one line, `#188` trigger on another — and **the pin refused it**. That is precisely the failure this
repo's own law names: *a gate that refuses honest code is a gate that gets switched off, and then the
outage happens again with nothing watching at all.*

Fixed: the unit is now the **contiguous comment block immediately above the declaration**, which must
mention each file entry and cite a finding number somewhere in the block. The pin's failure message
states its own bound explicitly — *it verifies the block exists, mentions each entry and cites a
finding; it CANNOT verify the prose is true* — so it does not promise a check it does not perform.

**Worth naming as process, not just as a fix:** the correction's rider is what produced this. Had I
implemented ruling #5's clause and skipped its "and pin it like this" half, the false gate would have
shipped inside the instrument built to prevent exactly this class.

### R.6 What the BUILDER owes that a test cannot assert

1. **The `MEMBERS` entries themselves**, in the same wave as the code, with the comment block naming
   the dissolution trigger. Both requirement pins go green the moment they land — **proven**, §6.4.
2. **The mutation proof of the file-leg** (ruling #5): introduce a type error into the instrument, run
   `scripts/typecheck.sh`, watch **that leg and only that leg** go red, restore. I cannot run it — I may
   not edit `typecheck.sh` — and a test cannot assert it without invoking the whole gate from inside
   the gate. Declared expected-RED legs before the run, per the `mutation_proof.py` discipline.
3. **`MYPYPATH=scripts` on the contract file's leg**, if F1 stands as two files (§R.3).

---

## 8. SURFACED TO LEAD — forks and questions. I picked; you rule.

### F1 — ONE FILE vs TWO. **This is the fork I most want ruled.**

§Q3.1 and the brief both say *one pytest file; the test IS the instrument*. **I shipped two**:
`scripts/gated_ground.py` (the builder's) + `scripts/test_gated_ground.py` (mine).

- **Reading A (one file):** the builder adds helper functions into the contract file above the tests.
  **Measured objection, and it is decisive:** a one-file contract must reference helper names that do
  not yet exist, which is `F821 Undefined name` — and the `F` family is selected in this repo. I
  measured it: a two-line probe file under `scripts/` produced `F821 Undefined name` and `ruff exit:
  1`. Repo law requires `uv run ruff check .` clean **at every commit**, so a one-file contract could
  not be committed ahead of its builder. An import of a not-yet-existing module is invisible to ruff
  (ruff does not resolve imports) — verified: the delivered contract is `All checks passed!`.
  Secondary objection: it hands the builder a file they must edit, which the repo's own
  satisfiability-receipt law warns about.
- **Reading B (two files), which I took.** The property §Q3.1 actually protects — no step-N/step-N+1
  seam where a script no-ops while a wrapper prints green — is **fully preserved and pinned**:
  `test_the_guard_returns_data_rather_than_an_exit_code` requires the assertion to consume typed
  values in-process; there is no subprocess and no exit code anywhere in the contracted surface. The
  import idiom is the established `scripts/` house one (`sys.path.insert` + `import … # noqa: E402`,
  as in `test_token_survey.py`, `test_snapshot_gc.py`, `test_forgery_door_sweep.py`).
- **Cost of B, stated honestly:** `scripts/gated_ground.py` is one more committed module that no type
  gate reads — the recursion `REPORT-sweep-44-1.md` §8.4 escalated. It falls under the root-scoped
  `#188` exemption on LEG A and is out of LEG B's scope (not test-shaped), so it creates **no new
  ungated ground**, and the exemption's re-open trigger retires it. But it is one file, not zero.

### F2 — what LEG B quantifies over

§Q3.2 says *"every tracked `test_*.py` and every `conftest.py`"*. I implemented **the patterns pytest
would actually collect under this repo's configuration** (`python_files`, defaulting to pytest's own
`["test_*.py", "*_test.py"]`) **plus `conftest.py`**. That is a strict superset of the spec's wording.
Rationale: a hardcoded `test_*.py` is a two-name list where the safe set has two members and the
config can change either — the instrument lesson's losing shape, and a `foo_test.py` walks straight
through it. Discriminating pins: `test_the_patterns_in_force_here_are_pytests_own_defaults`,
`test_a_configured_python_files_override_replaces_the_defaults`,
`test_the_second_default_pattern_is_covered`. **If you rule the literal reading, three pins change.**

### F3 — nine things I added beyond §Q3's literal text. Each is disclosed, none is silent.

1. **Whole-tree-wildcard and non-directory `MEMBERS`/`testpaths` entries raise.** §Q3.3 names only
   "parse failure or empty"; a root of `.` is the strictly worse failure (it prints zero findings).
   Taken from `REPORT-sweep-44-1.md` §10, which measured it.
2. **A FIFTH anti-vacuity pin: every shipped exemption row must be LOAD-BEARING**, proved by removing
   it and requiring findings to appear. The brief names four; this is the anti-stale-row one.
3. **Precedence: COVERED beats an exemption**, so a stale row becomes visible to (2) rather than
   hiding behind itself.
4. **Unmodelled `[tool.mypy]` config makes the WHOLE verdict refuse**, not just a reader return a
   list. Without this a builder could write the reader and never call it. (I caught this gap in my
   own contract during the write-up and added the pin — the count went 122 → 123.)
5. **Hostile-path pins** (NUL enumeration + header-count forgery) — the rendered-stored-text clause.
6. **Determinism pin** (two runs equal, path-ordered) so two gate outputs are diffable.
7. **`classify`/`ungated_ground` take an injectable `exemptions=`.** Required for fate coverage: the
   shipped table has no execution-axis row, so `EXEMPT_TABLE` on LEG B is otherwise an unreachable
   branch. The shipped table is pinned separately.
8. ~~ONE-IMPLEMENTATION escalation~~ — **WITHDRAWN, ruled by the lead** (correction item 4): two
   `tomllib` readers of one registry are consumers, not policy clones, and the import is forbidden by
   stdlib-only self-containment. Now *enforced* by `test_the_instrument_does_not_import_the_project`
   rather than escalated. See §R.
9. **The `.sh` axis is NOT modelled.** A shell gate landed at `2bc7e97`. §Q3 scopes the property to
   Python; the sweep already asked the operator whether shell is in scope
   (`REPORT-sweep-44-1.md` §8.1). **I did not widen it.** If you rule shell in, this is a third leg
   and a new fixture family, not an edit.

### F4 — the vanished expected-RED (see §7)

The brief's order-dependence warning is discharged by events, so **F4 is CLOSED**. The
`5a850c3` replay (§6.3) supplies the evidence the vanished RED would have: it shows the invariant pin
firing on the real tree, naming the real gaps. **The correction then restored two DIFFERENT
expected-RED pins** (`TestThisInstrumentRidesTheTypeGateItself`), which only the instrument's builder
can discharge — and those are proven satisfiable in §6.4, so they are a contract, not a demand.

### F5 — committing this contract turns `pytest scripts/` RED

Until the builder lands `scripts/gated_ground.py`, collection of `scripts/test_gated_ground.py`
errors, and pytest reports `Interrupted: 1 error during collection` for the whole `scripts` tree.
That is ordinary contract-first, but it means **the commit that lands this contract makes the
standard gate red**, which repo law otherwise forbids. Sequence deliberately, or land contract and
build in one wave.

### Questions I could not answer (no lore tools — see Capability check)

- I could not read the `lore_findings` bodies for #188, #260, #280. **The finding numbers I pin
  (`#188` in the exemption row, `#260` as the lore-index bound's re-open trigger) are inherited from
  the design sidecar and the sweep, not re-derived by me.** If either is wrong, two pins are wrong.
- I could not file a friction row for the lore fallback, which the dogfood protocol requires.

### Replaced-code inventory

**None was supplied, and none applies** — this feature deletes and replaces no code. The nearest
thing is `REPORT-sweep-44-1.md` §10's scratch instrument, which was never committed and whose home
§Q3 rules differently on purpose (registration guard, not discovery sweep); its two discovery
mechanisms are adjudicated in the package survey as `keep_with_trigger` with triggers named, not
silently dropped.

---

## 9. Instruments (brief-base §1 — an instrument that establishes a load-bearing claim is a deliverable)

### 9.1 The throwaway reference build

⚠ **THIS IS NOT A DESIGN TO CLONE.** It exists only so §6.1's "0 failed" is a measurement rather than
a hope. Nothing in it has been graded by an adversary or an audit; a builder that reproduces it
inherits every ungraded choice in it. **The deliverable is a build that satisfies the contract, not a
copy of this one.** In particular it uses a PRIVATE pytest attribute (`_parser._inidict`) which the
contract deliberately does not pin, and its `__doc__` composition is one of several legitimate ways
to satisfy the docstring pins. md5 `b584aa5b63bcd3392ba9b4e347e9b360` (revision 2 — stdlib-only, file-granularity roots).

<details>
<summary><code>scripts/gated_ground.py</code> — throwaway reference build, revision 2</summary>

```python
"""THROWAWAY REFERENCE BUILD — satisfiability receipt for scripts/test_gated_ground.py."""

from __future__ import annotations

import fnmatch
import re
import subprocess
import tomllib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class GuardIsBlind(RuntimeError):
    """Raised when an input could not be derived. Blind is not clean."""


class InvalidExemption(ValueError):
    """Raised when an exemption row lacks the evidence that makes it legitimate."""


class GateAxis(Enum):
    TYPES = "types"
    EXECUTION = "execution"

    @property
    def label(self) -> str:
        return "LEG A — types" if self is GateAxis.TYPES else "LEG B — execution"


class Fate(Enum):
    COVERED = "covered"
    EXEMPT_TABLE = "exempt-table"
    EXEMPT_ARCHIVED_RECEIPTS = "exempt-archived-receipts"
    UNGATED = "ungated"
    NOT_APPLICABLE = "not-applicable"


@dataclass(frozen=True)
class Exemption:
    root: str
    axis: GateAxis
    finding: str
    reason: str
    reopen_trigger: str

    def __post_init__(self) -> None:
        if not self.root or Path(self.root).is_absolute() or ".." in Path(self.root).parts:
            raise InvalidExemption(f"exemption root {self.root!r} is not a repo-relative tree")
        if not isinstance(self.axis, GateAxis):
            raise InvalidExemption(f"exemption axis {self.axis!r} is not a GateAxis")
        if not re.fullmatch(r"#\d+", self.finding):
            raise InvalidExemption(
                f"exemption {self.root!r} cites {self.finding!r}, which is not a finding number"
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
    finding: str | None = None


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

EXEMPTIONS: tuple[Exemption, ...] = (
    Exemption(
        root="scripts",
        axis=GateAxis.TYPES,
        finding="#188",
        reason=(
            "the tree carries a standing type-debt disposition of its own; widening the "
            "canonical runner before that debt is zero lands the gate red on day one, and a "
            "gate that lands red is a gate that gets switched off"
        ),
        reopen_trigger=(
            "the #188 cleanup lands and mypy is clean over scripts/ — delete this row and add "
            "scripts to typecheck.sh MEMBERS in the same commit"
        ),
    ),
)

THREAT_MODEL = (
    "This gate is for the HONEST ENGINEER who commits a load-bearing .py into a tree no gate, "
    "or only half the gates, cover — believing the repo's gates see it. It is NOT a security "
    "boundary: anyone who can commit here can delete this test."
)

STATED_BOUNDS: tuple[StatedBound, ...] = (
    StatedBound(
        identifier="registration-not-execution",
        summary=(
            "This proves REGISTRATION in the gates' configuration. It does not prove mypy or "
            "pytest ran, or passed; each gate's own exit code proves that."
        ),
        reopen_trigger="a gate result is ever inferred from this test rather than from that gate",
    ),
    StatedBound(
        identifier="execution-axis-covers-test-shaped-files-only",
        summary=(
            "LEG B quantifies over test-shaped files and conftest only; execution coverage of "
            "ordinary library modules is a coverage-measurement problem this does not claim."
        ),
        reopen_trigger="a coverage instrument lands that can answer the stronger question",
    ),
    StatedBound(
        identifier="collection-convention",
        summary=(
            "A file full of asserts named outside pytest's collection convention is invisible "
            "to pytest everywhere, which is a different defect class than ungated ground."
        ),
        reopen_trigger="a committed assert-carrying module is found outside the convention",
    ),
    StatedBound(
        identifier="lore-index-axis",
        summary=(
            "lore's index is a third gate direction this instrument does not model, so a tree "
            "outside lore.yaml's include list passes here while being ungraphed."
        ),
        reopen_trigger="#260 lands, at which point the index axis becomes derivable and this re-opens",
        finding="#260",
    ),
)

__doc__ = (
    "gated_ground.py — DERIVE every committed .py that no repo gate registers, PER AXIS.\n\n"
    "THREAT MODEL. " + THREAT_MODEL + "\n\nBOUNDS:\n"
    + "\n".join(f"  * {bound.summary} (re-open: {bound.reopen_trigger})" for bound in STATED_BOUNDS)
)

_MEMBERS_DECLARATION = re.compile(r"^MEMBERS=\(([^)]*)\)", re.MULTILINE)
_BLIND = "the guard is blind, not the tree clean"


def _manifest(repo_root: Path) -> dict[str, object]:
    path = repo_root / "pyproject.toml"
    try:
        return tomllib.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GuardIsBlind(f"cannot read {path} ({exc}) — {_BLIND}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise GuardIsBlind(f"cannot parse {path} ({exc}) — {_BLIND}") from exc


def _table(manifest: Mapping[str, object], *keys: str) -> Mapping[str, object]:
    node: object = manifest
    for key in keys:
        if not isinstance(node, Mapping) or key not in node:
            raise GuardIsBlind(f"pyproject.toml declares no [{'.'.join(keys)}] — {_BLIND}")
        node = node[key]
    if not isinstance(node, Mapping):
        raise GuardIsBlind(f"[{'.'.join(keys)}] is not a table — {_BLIND}")
    return node


def typecheck_roots(repo_root: Path) -> list[str]:
    runner = repo_root / "scripts" / "typecheck.sh"
    try:
        text = runner.read_text(encoding="utf-8")
    except OSError as exc:
        raise GuardIsBlind(f"cannot read {runner} for its MEMBERS declaration ({exc}) — {_BLIND}") from exc
    match = _MEMBERS_DECLARATION.search(text)
    if match is None:
        raise GuardIsBlind(f"cannot find a MEMBERS=(...) declaration in {runner} — {_BLIND}")
    roots = [word for word in match.group(1).split() if word]
    if not roots:
        raise GuardIsBlind(f"the MEMBERS declaration in {runner} is empty — {_BLIND}")
    for root in roots:
        parts = Path(root).parts
        if root in {".", ".."} or Path(root).is_absolute() or ".." in parts:
            raise GuardIsBlind(
                f"typecheck root {root!r} is a whole-tree wildcard: it would mark every file "
                f"gated and report zero findings — {_BLIND}"
            )
        if not (repo_root / root).exists():
            raise GuardIsBlind(f"typecheck root {root!r} names nothing in {repo_root} — {_BLIND}")
    return roots


def pytest_testpaths(repo_root: Path) -> list[str]:
    options = _table(_manifest(repo_root), "tool", "pytest", "ini_options")
    if "testpaths" not in options:
        raise GuardIsBlind(f"pyproject.toml declares no testpaths — {_BLIND}")
    paths = list(options["testpaths"])  # type: ignore[call-overload]
    if not paths:
        raise GuardIsBlind(f"the declared testpaths list is empty — {_BLIND}")
    for testpath in paths:
        if not (repo_root / testpath).is_dir():
            raise GuardIsBlind(f"testpaths entry {testpath!r} names no directory — {_BLIND}")
    return paths


def workspace_members(repo_root: Path) -> list[str]:
    workspace = _table(_manifest(repo_root), "tool", "uv", "workspace")
    members = list(workspace.get("members", []))  # type: ignore[call-overload]
    if not members:
        raise GuardIsBlind(f"pyproject.toml declares no workspace members — {_BLIND}")
    return members


def ruff_excluded_trees(repo_root: Path) -> list[str]:
    ruff = _table(_manifest(repo_root), "tool", "ruff")
    return list(ruff.get("extend-exclude", []))  # type: ignore[call-overload]


#: pytest's own declared default for ``python_files``. A CONSTANT because this module is
#: stdlib-only by ruling and may not import pytest; kept honest by the contract's drift guard,
#: which reads the value out of `_pytest.python.pytest_addoption`'s parser on every gate run.
PYTEST_DEFAULT_TEST_FILE_PATTERNS: tuple[str, ...] = ("test_*.py", "*_test.py")


def pytest_test_file_patterns(repo_root: Path) -> list[str]:
    manifest = _manifest(repo_root)
    try:
        options = _table(manifest, "tool", "pytest", "ini_options")
    except GuardIsBlind:
        options = {}
    configured = options.get("python_files")
    if configured:
        return list(configured)  # type: ignore[call-overload]
    return list(PYTEST_DEFAULT_TEST_FILE_PATTERNS)


def unmodelled_mypy_configuration(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[str]:
    manifest = _manifest(repo_root)
    try:
        mypy = _table(manifest, "tool", "mypy")
    except GuardIsBlind:
        return []
    reasons: list[str] = []
    excludes = mypy.get("exclude")
    if excludes:
        reasons.append(
            f"[tool.mypy] declares exclude={excludes!r}: this guard does not model mypy "
            f"excludes; extend it or remove the exclude."
        )
    overrides = mypy.get("overrides", [])
    if isinstance(overrides, list):
        for override in overrides:
            if not isinstance(override, Mapping) or not override.get("ignore_errors"):
                continue
            modules = override.get("module", [])
            if isinstance(modules, str):
                modules = [modules]
            for module in modules:
                as_path = str(module).replace(".", "/")
                if any(
                    row.axis is GateAxis.TYPES and is_under(as_path, row.root) for row in exemptions
                ):
                    continue
                reasons.append(
                    f"[[tool.mypy.overrides]] sets ignore_errors for {module!r}, which carries no "
                    f"pinned exemption: this guard does not model mypy excludes; extend it or "
                    f"remove the exclude."
                )
    return reasons


def tracked_python_files(repo_root: Path) -> list[str]:
    try:
        completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
            ["git", "ls-files", "-z"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError as exc:
        raise GuardIsBlind(f"cannot enumerate committed files under {repo_root} ({exc}) — {_BLIND}") from exc
    if completed.returncode != 0:
        raise GuardIsBlind(
            f"`git ls-files` exited {completed.returncode} in {repo_root} — {_BLIND}\n"
            f"{completed.stderr.strip()}"
        )
    return sorted(name for name in completed.stdout.split("\0") if name.endswith(".py"))


def is_under(path: str, tree: str) -> bool:
    path_parts = Path(path).parts
    tree_parts = Path(tree).parts
    return path_parts[: len(tree_parts)] == tree_parts


def _validate_receipts_class(repo_root: Path, tracked: Sequence[str]) -> None:
    excluded = ruff_excluded_trees(repo_root)
    if ARCHIVED_RECEIPTS_ROOT not in excluded:
        raise GuardIsBlind(
            f"{ARCHIVED_RECEIPTS_ROOT!r} is not in [tool.ruff] extend-exclude {excluded!r}: the "
            f"archived-receipts exemption is backed by that declaration and by nothing else — {_BLIND}"
        )
    if not any(is_under(path, ARCHIVED_RECEIPTS_ROOT) for path in tracked):
        raise GuardIsBlind(
            f"no committed .py sits under {ARCHIVED_RECEIPTS_ROOT!r}: the archived-receipts class "
            f"is vacuous — {_BLIND}"
        )


def _is_test_shaped(path: str, patterns: Sequence[str]) -> bool:
    name = Path(path).name
    return name == "conftest.py" or any(fnmatch.fnmatch(name, pattern) for pattern in patterns)


def classify(repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS) -> list[FileVerdict]:
    unmodelled = unmodelled_mypy_configuration(repo_root, exemptions=exemptions)
    if unmodelled:
        raise GuardIsBlind(" ".join(unmodelled) + f" — {_BLIND}")
    tracked = tracked_python_files(repo_root)
    _validate_receipts_class(repo_root, tracked)
    roots = typecheck_roots(repo_root)
    testpaths = pytest_testpaths(repo_root)
    patterns = pytest_test_file_patterns(repo_root)

    verdicts: list[FileVerdict] = []
    for path in tracked:
        fates: dict[GateAxis, Fate] = {}
        for axis, scopes in ((GateAxis.TYPES, roots), (GateAxis.EXECUTION, testpaths)):
            if axis is GateAxis.EXECUTION and not _is_test_shaped(path, patterns):
                fates[axis] = Fate.NOT_APPLICABLE
            elif any(is_under(path, scope) for scope in scopes):
                fates[axis] = Fate.COVERED
            elif is_under(path, ARCHIVED_RECEIPTS_ROOT):
                fates[axis] = Fate.EXEMPT_ARCHIVED_RECEIPTS
            elif any(row.axis is axis and is_under(path, row.root) for row in exemptions):
                fates[axis] = Fate.EXEMPT_TABLE
            else:
                fates[axis] = Fate.UNGATED
        verdicts.append(FileVerdict(path=path, fates=fates))
    return verdicts


def _render(path: str, axis: GateAxis, roots: Sequence[str], testpaths: Sequence[str]) -> str:
    if axis is GateAxis.TYPES:
        scope_label = "typecheck root declared in scripts/typecheck.sh MEMBERS"
        scope = ", ".join(roots)
        gate = "mypy"
        fix = "add its tree to scripts/typecheck.sh MEMBERS as its own iteration"
    else:
        scope_label = "testpaths entry declared in pyproject.toml"
        scope = ", ".join(testpaths)
        gate = "pytest"
        fix = "add its tree to the pyproject.toml testpaths list"
    return (
        f"UNGATED GROUND ({axis.label}): {path!r} is a committed .py outside every "
        f"{scope_label} ({scope}) and carries no pinned exemption.\n"
        f"This test proves REGISTRATION in the gates' config — it does not prove {gate} ran, or "
        f"passed; that gate's own exit code proves that.\n"
        f"Fix: {fix}, or add a pinned exemption row carrying a finding number and a named "
        f"re-open trigger. Do NOT widen the receipts class to admit it."
    )


def ungated_ground(
    repo_root: Path, *, exemptions: Sequence[Exemption] = EXEMPTIONS
) -> list[UngatedFile]:
    verdicts = classify(repo_root, exemptions=exemptions)
    roots = typecheck_roots(repo_root)
    testpaths = pytest_testpaths(repo_root)
    findings: list[UngatedFile] = []
    for verdict in verdicts:
        for axis in GateAxis:
            if verdict.fates[axis] is Fate.UNGATED:
                findings.append(
                    UngatedFile(
                        path=verdict.path,
                        axis=axis,
                        message=_render(verdict.path, axis, roots, testpaths),
                    )
                )
    return findings
```

</details>

### 9.2 The pre-config-wave replay (§6.3's instrument)

Read-only on this worktree; builds a **fresh** repository, never a copy of a worktree's `.git`.

```python
import subprocess, sys, shutil
from pathlib import Path

WORKTREE = Path("/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44")
SHA = "5a850c3"                      # the sha packet 44's brief was written against
dest = Path("/tmp/gatedground-replay-5a850c3")
shutil.rmtree(dest, ignore_errors=True)
dest.mkdir(parents=True)

# git archive WRITES A TARBALL — it never touches git state in the source repo.
archive = subprocess.run(["git", "archive", SHA], cwd=WORKTREE, capture_output=True, check=True)
subprocess.run(["tar", "-x", "-C", str(dest)], input=archive.stdout, check=True)

# A FRESH repository. NEVER a copy of a worktree's .git, which is a FILE naming the
# original gitdir — a copied one makes `git add` mutate the tree you meant to isolate.
subprocess.run(["git", "init", "-q", "-b", "main", "."], cwd=dest, check=True)
subprocess.run(["git", "add", "-A"], cwd=dest, check=True, capture_output=True)
assert not (dest / ".git").is_file(), "the replay repo must own a real .git DIRECTORY"

sys.path.insert(0, str(WORKTREE / "scripts"))
import gated_ground as gg
print("PROVENANCE gated_ground.__file__ =", gg.__file__)
print("MEMBERS at", SHA, "=", gg.typecheck_roots(dest))
print("testpaths at", SHA, "=", gg.pytest_testpaths(dest))
findings = gg.ungated_ground(dest)
print(f"\nFINDINGS AT {SHA}: {len(findings)}")
for f in findings:
    print(f"  {f.axis.name:9s} {f.path}")
print("\nFINDINGS AT WORKTREE HEAD:", len(gg.ungated_ground(WORKTREE)))
shutil.rmtree(dest)
```

Run it with `uv run --no-sync python …` — a bare `python3` cannot import `_pytest`, which the
patterns reader needs. (That was my own first attempt and it failed loudly, which is the behaviour
the contract's blind-not-clean pins demand of the guard itself.)

---

## 10. Bounds on this report

1. **Two derivations, not one.** My LEG A / LEG B numbers at `5a850c3` (4 + 8) and the sweep's
   (`REPORT-sweep-44-1.md` §4b/§5) agree on the sets; they were derived by different instruments
   (path arithmetic here, mypy/pytest discovery there). Where they would differ is precisely the
   registration-vs-discovery gap the `keep_with_trigger` rows in §2 name.
2. **Finding numbers are inherited, not re-derived** (no lore tools — see Capability check).
3. **Everything numeric here has a command beside it.** No count is stated that I did not run.
4. **The tree moved four commits under me.** Every headline number is at `8015d22` except the replay,
   which is labelled `5a850c3`.
