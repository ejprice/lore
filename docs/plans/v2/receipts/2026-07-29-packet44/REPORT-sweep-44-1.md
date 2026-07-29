brief-base v9 read

# REPORT-sweep-44-1 — packet 44 UNGATED GROUND, entry derivation sweep

**Capability check (brief-base §4).** The brief demanded: read files, run the repo's gates,
run `registration_sites.py`, parse config, file lore findings, write one report. I had every
tool required — Read, Bash, Write, ToolSearch, and the `lore_findings` MCP tool. **Nothing in
the brief was unmeetable.** One deviation from the brief's tool guidance, disclosed up front:
the brief said lore is first choice but that this task is a non-symbol textual/path seam plus
an exhaustiveness question, sanctioning `git ls-files` + path arithmetic. **I took that
fallback, and I say so here as the dogfood protocol requires** — every structural answer below
comes from `git ls-files`, `mypy`'s own discovery API, `pytest --collect-only` and `ruff
--show-files`, not from the lore graph. That was the correct instrument: the question is
*"which committed files does each gate's discovery reach"*, which is a set-membership question
over paths, and a graph keyed on symbols cannot answer it. I used `lore_findings` for the five
required finding reads and for filing. No lore friction to report — lore was not routed around,
it was not the right tool for this question.

---

## SUMMARY BLOCK

- `brief-base v9 read`
- **state: done** — sweep run, property interrogated, 4 findings filed, nothing fixed (read-only as briefed)
- deviation: HEAD moved under me mid-sweep, `7bd9b4e` → `fe576ba` (a sibling committed `scripts/forgery_door_sweep.py`). **All headline numbers below are re-measured at `fe576ba`**; §7 records the delta.
- deviation: I ran the 117 `skills/` tests (out-of-brief measurement) to size finding #280 rather than widen blind — #188's own law. Result in §5.
- `Packages considered:` **sweep instrument** — `mypy.find_sources.create_source_list` + `mypy.config_parser.parse_config_file` (READ: live signature probe, returns `BuildSource(path=…)`) → **replace** a hand-rolled directory walk; `pytest --collect-only` (READ: its node-id output shape) → **replace** a hand-rolled `python_files` matcher; `tomllib` (stdlib) → **replace** hand-parsing TOML; the `MEMBERS=(…)` bash-array reader → **bespoke**, minimal surface (one anchored regex), because the only package-shaped alternative is `source`-ing `typecheck.sh`, which EXECUTES the gate as a side effect of reading it. Details §9.
- **decisions-needed (4):** ① packet 44 has **ballooned — a split is MANDATED** (§6); ② is the shell tree in scope? 7 committed `.sh`, **zero** shell gate (§4c); ③ #270 is moot at HEAD — close it? (#283); ④ the fired-and-undischarged re-open trigger (#282) — fix here or route out?
- **derived count:** coarse property (as packet 44 words it) = **19** files, **all 19 exempt**, evidence in §4a. The real answer is the refined one: **23 live committed files no type gate touches** (§4b) + **8 test files / 117 tests no pytest gate collects** (§5).
- **2×2 over 290 tracked `.py`:** typed+collected **130** · typed only **118** · collected only **10** · **neither 32**
- **type debt blocking the packet: 87 mypy errors across 10 committed files** (`scripts` 45/7, `docs/eval` 42/3) — re-derived, §7
- findings filed: **#280** (skills/ — 117 uncollected tests, NEW tree) · **#281** (#261 is 6× understated) · **#282** (stale prose + fired trigger) · **#283** (#270's premise is dead)
- receipt pointers: instrument verbatim §10 · anti-vacuity + mutation proof §3 · full row tables §4 · self-interrogation §2 · escalations §8

---

## 1. What I derived, and from what

The property, as packet 44 words it: *a committed `.py` outside every `scripts/typecheck.sh`
member AND outside every `pyproject.toml` `testpaths` entry.*

**Both input sets are parsed from the real config files at runtime.** Nothing is mirrored into
the script — a hand-mirrored config list is the stale-mirror hazard CLAUDE.md records against
`scratch_provenance.py::WORKSPACE_MEMBERS`, and this sweep exists to catch that class, not to
join it. Derived at `fe576ba`:

```
typecheck.sh MEMBERS (5) : lorerunes lorescribe loresigil loremaster skills
pytest testpaths (6)     : lorerunes/tests lorescribe/tests loresigil/tests loremaster/tests scripts docs/eval
[tool.mypy] exclude      : NONE DECLARED
[tool.ruff] extend-exclude: ['scratchpad', 'docs/plans/v2/receipts']
tracked files            : 689
tracked .py              : 290
mypy discovers           : 248 files across the members
pytest collects from     : 140 files
```

**The brief asked whether `[tool.mypy]` has an `exclude` that makes a file ungated in fact
while passing the property. It does not** — `exclude` is absent, verified by asking mypy's own
config parser rather than by reading the TOML with my eyes (`opts.exclude == []`). So no
tracked file is hidden that way. I checked the *general* form of that hazard anyway, in §4d.

**I ran the model instrument first**, as briefed — `./scripts/registration_sites.py` at
`7bd9b4e`: `declared workspace members (4)` · `co-occurrence sites found: 42 · incomplete: 20`,
exit 1. It is the shape this sweep copies: derive from a property, ship the bounds in the
docstring, emit a worklist and not a verdict, and refuse to report a clean tree when the
detector itself is broken.

---

## 2. The two self-interrogations the brief demanded, in writing

### *"If step N silently no-opped, would step N+1 still print something that reads as success?"*

**Yes, in five places, and every one of them is now closed by an abort rather than a comment.**
This is the whole reason the instrument has an `_prove_the_instrument_works` gate:

| silent no-op | what it would have printed | guard |
|---|---|---|
| `MEMBERS=(…)` regex misses → `members == []` | every file "ungated" — loud, safe direction | abort on empty |
| `MEMBERS` parse widens to `.` or an absolute path | **"0 gaps" — reads as a clean bill of health** | abort on wildcard/absolute/non-dir member |
| `git ls-files '*.py'` glob matches nothing | **"0 gaps"** | abort on empty tracked / empty `.py` set |
| mypy discovery returns `[]` | every file "untyped" — loud, safe direction | abort on empty |
| `pytest --collect-only` errors or collects nothing | **every file "UNCOLLECTED" — reads as a huge FINDING, i.e. a broken instrument wearing a result** | abort on non-zero exit and on empty set |
| classifier stuck at `True` | **"0 gaps"** | NEGATIVE CONTROL: a synthetic path in no tree must classify ungated |
| classifier stuck at `False` | every file "ungated" | POSITIVE CONTROL: some tracked file must classify typed, and some collected |

The failure direction that matters is always toward false confidence, so the guards are
weighted there: **three of the seven rows above end in a printed number a reader would file as
reassurance.** Proven live, not asserted (§3).

### *"What WRONG build would still pass this sweep?"*

Honest answers, because each is a real bound rather than a rhetorical flourish:

1. **A gate that reaches a file and checks nothing.** The sweep asks *"does discovery REACH
   this file"*, never *"is it adequately typed/tested"*. A `testpaths` tree of empty test
   functions passes. A module of `# type: ignore` passes. **This is why finding #280 quotes a
   passed-COUNT and not a collected-count**, and why §7 reports error counts separately.
2. **A tree gated by an instrument I did not model.** I modelled mypy, pytest and (separately)
   ruff. The AST scans' `_SCANNED_MEMBERS`, the in-image conformance run, and
   `registration_sites.py` itself are gates too. A file this report calls "ungated" may be
   covered by one of them; a file it calls gated is gated *only by the gates named*.
3. **A build that adds a tree to `testpaths` where nothing is collectable.** `testpaths` entries
   are only checked for EXISTENCE, so pointing one at an empty directory would satisfy the
   coarse property and change nothing. This is not hypothetical — it is exactly the shape of
   the real defect in §4b, where `docs/eval` sits in `testpaths` while its 3246-line subject
   module is read by neither gate.
4. **A file added to `.gitignore`.** The property is scoped to `git ls-files`, so a
   load-bearing module that is untracked is invisible to this sweep by construction. That is
   deliberate ("committed ground"), and it bit during this very run — see §7.

---

## 3. Proving the instrument works before believing its output

Four controls, all executed. **CONTROL C is the interesting one, because I got it wrong.**

**CONTROL A — the discovery API agrees with how `typecheck.sh` actually invokes mypy.** The
runner passes RELATIVE member names; my sweep passed absolute paths. Different arguments can
mean different module-name resolution, so this was not assumed:

```
CONTROL A — relative-arg discovery == absolute-arg discovery: True (248 vs 248)
```

**CONTROL B — an independent path-arithmetic count reaches the same set.**

```
CONTROL B — independent path-arithmetic count of tracked .py under members: 248
           set equality with mypy discovery: True
           tracked .py total: 288 | outside member dirs: 40   [measured at 7bd9b4e]
```
Two instruments agreeing is not redundancy: it says that *at this commit* path arithmetic and
mypy's real discovery coincide. The API leg is what would catch a divergence tomorrow, and
§4d shows divergence is a real mode, not a theoretical one.

**CONTROL C — can the discovery leg OMIT an on-disk `.py` at all?** My first version of this
control asserted mypy skips a file whose stem contains a dot. **Execution said otherwise — mypy
discovered `dotted.name.py`, and my control returned `False`.** The belief was wrong, not the
tool. This is CLAUDE.md's own sentence operating on me in real time: *a false belief about your
own semantics is SELF-SEALING, and the only instrument that breaks it is execution.* Had I
written that belief into the report instead of into a control, it would have shipped as a fact.
Corrected, the leg does discriminate:

```
on disk       : ['__pycache__/cached.py', 'dotted.name.py', 'good.py', 'pkg.py', 'pkg/__init__.py']
mypy discovers: ['dotted.name.py', 'good.py', 'pkg/__init__.py']
omitted       : ['__pycache__/cached.py', 'pkg.py']          <- stem collides with the pkg/ dir
CONTROL C — discovery leg CAN omit an on-disk .py: True
```

**CONTROL D — mutation proof of the anti-vacuity gate.** A guard nobody has watched fail is a
hope with a filename. I removed the `MEMBERS=` line from a copy of `typecheck.sh` and pointed
the parser at it:

```
MUTATION PROOF HELD — aborts loudly: INSTRUMENT BROKEN: no `MEMBERS=(
```

---

## 4. The rows — every file individually, no wholesale classification

CLAUDE.md bans *"all remaining hits are X"*. Every file below carries its own verdict.

### 4a. COARSE gap set — the packet-44 property as worded: **19 files, all exempt**

All 19 sit under `docs/plans/v2/receipts/`. **The exemption is evidence-backed by three
independent committed declarations that this tree is archived ground, and by a measurement of
ruff's actual behaviour** — not by "it's obviously fine":

- `pyproject.toml` `[tool.ruff] extend-exclude = ["scratchpad", "docs/plans/v2/receipts"]`, whose
  committed comment states the reason: receipts are *"preserved BYTE-FAITHFUL… a receipt that has
  been reformatted is no longer evidence of the run it documents. Linting them would mean editing
  them."*
- `scripts/registration_sites.py::_EXCLUDED` names `:!docs/plans/v2/receipts` for the same reason.
- CLAUDE.md's ARCHIVE-REPORTS-NEVER-DELETE law (#152/#153).
- **Measured, not assumed** — my first attempt at this evidence was wrong-shaped (I passed the
  path explicitly, and ruff overrides excludes for explicit paths, "finding" 12 errors). The
  correct question is what ruff's own discovery does under the canonical invocation:
  ```
  $ uv run ruff check .                                   -> All checks passed!
  $ uv run ruff check . --show-files | grep -c 'docs/plans/v2/receipts'   -> 0
  ```
  And the convergence is exact: **the set of tracked `.py` ruff does not lint IS the coarse gap
  set, all 19, no more and no less.**

| # | file | lines | misses | verdict |
|---|---|---|---|---|
| 1 | `docs/plans/v2/receipts/2026-07-20-probes/102-recovery/probe_conflict_kind.py` | 274 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 2 | `…/102-recovery/probe_sequence.py` | 176 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 3 | `…/102-recovery/probe_sequence_concurrency.py` | 130 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 4 | `…/102-recovery/probe_sequence_concurrency_scale.py` | 130 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 5 | `…/102-recovery/probe_sequence_txn_concurrency.py` | 153 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 6 | `…/102-recovery/probe_sequence_txn_concurrency_v2.py` | 175 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 7 | `…/102-recovery/probe_txn_control_no_sequence.py` | 140 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 8 | `…/102-recovery/probe_txn_control_predefined_table.py` | 141 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 9 | `…/102-recovery/probe_txn_control_warmup.py` | 141 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 10 | `…/2026-07-20-probes/probe_budget.py` | 62 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 11 | `…/2026-07-20-probes/probe_cosine_projection_s4b.py` | 149 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 12 | `…/2026-07-20-probes/probe_long_query_66b.py` | 91 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 13 | `…/2026-07-20-probes/probe_long_query_69.py` | 134 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 14 | `…/2026-07-24-packet11i/probe_bootstrap_degeneracy.py` | 1342 | mypy, pytest, ruff | `exempt-archived-receipt` |
| 15 | `…/2026-07-28-packet11ib/consult-11ib/tools/build_variants.py` | 389 | mypy, pytest, ruff | `exempt-archived-receipt` + ARCHIVED marker in-file (verified per-file) |
| 16 | `…/consult-11ib/tools/check_coherence.py` | 636 | mypy, pytest, ruff | `exempt-archived-receipt` + ARCHIVED marker · **carries #270's parsing defect, now frozen** |
| 17 | `…/consult-11ib/tools/grade.py` | 452 | mypy, pytest, ruff | `exempt-archived-receipt` + ARCHIVED marker · **carries #270's parsing defect, now frozen** |
| 18 | `…/consult-11ib/tools/keyed_surface.py` | 119 | mypy, pytest, ruff | `exempt-archived-receipt` + ARCHIVED marker |
| 19 | `…/consult-11ib/tools/make_exhibit_jsonl.py` | 212 | mypy, pytest, ruff | `exempt-archived-receipt` + ARCHIVED marker |

Rows 15–19 are #270's five tools. **They are no longer at the repo root** — archived at
`d74e1da` (*"archive the consult tools out of the repo root — nothing calls them"*) and marked
at `499003f`. Filed as **#283**; see §8.

### 4b. THE REAL ANSWER — 13 LIVE committed modules neither gate reads

The coarse property calls these **gated**, because they sit inside a `testpaths` directory.
They are not. `testpaths` runs pytest over a tree; it does not make every `.py` in that tree a
test, and none of these is typed. **This is why the brief's instruction to interrogate the
property rather than just count it was the load-bearing instruction.**

| # | file | lines | typed? | collected? | verdict |
|---|---|---|---|---|---|
| 1 | `docs/eval/smoke_p8b.py` | 3246 | **no** | no | `gap` — THE DEPLOY SMOKE, caught #107 and #131. mypy on it alone: **0 errors** |
| 2 | `docs/eval/evaluation_harness_p8a.py` | 556 | **no** | no | `gap` — DESIGN-LAW names it *"the A/B instrument"*; **12 errors** |
| 3 | `docs/eval/connections_p8a.py` | 151 | **no** | no | `gap` — its required sibling; **23 errors**, the worst file in the tree |
| 4 | `scripts/comms_consumer_eval.py` | 2430 | **no** | no | `gap` — packet 03b's ACCEPTANCE AUTHORITY (#188); **5 errors** |
| 5 | `scripts/token_survey.py` | 1628 | **no** | no | `gap`; 0 errors today, named by 12 test files |
| 6 | `scripts/search_score_survey.py` | 999 | **no** | no | `gap` — holds the #233 consumer that a rename would have broken; **4 errors** |
| 7 | `scripts/forgery_door_sweep.py` | 824 | **no** | no | `gap` — **committed during this sweep** (`fe576ba`), the #278 instrument |
| 8 | `scripts/snapshot_gc.py` | 448 | **no** | no | `gap`; 0 errors today |
| 9 | `scripts/mutation_proof.py` | 307 | **no** | no | `gap` — the #196 guard; 0 errors today |
| 10 | `scripts/registration_sites.py` | 247 | **no** | no | `gap` — **the packet's own model instrument, and CLAUDE.md orders it RUN. Named by ZERO test files** (derived below) |
| 11 | `scripts/survey_txn_contention_102.py` | 210 | **no** | no | `gap` — **8 errors**, third-worst file in the repo |
| 12 | `scripts/calibration_baseline.py` | 194 | **no** | no | `gap`; 0 errors today |
| 13 | `scripts/scratch_provenance.py` | 173 | **no** | no | `gap` — the #140 guard `scratch_copy.sh` runs; 0 errors today |

Coverage heuristic for row 10, derived rather than eyeballed (`git grep -l <name> -- '*/test_*.py'`
— a NAME-MENTION count, **not** a coverage measurement, so treat it as a lead):

```
calibration_baseline  3 | comms_consumer_eval 2 | forgery_door_sweep 1 | mutation_proof   5
registration_sites    0 | scratch_provenance  2 | search_score_survey 5 | snapshot_gc      6
survey_txn_contention_102 2 | token_survey    12
```

### 4c. Tested but UNTYPED — 10 files (the other half of the 2×2)

Collected by pytest, invisible to `typecheck.sh`. These are the files behind #188's number.

| # | file | lines | mypy errors today | verdict |
|---|---|---|---|---|
| 1 | `docs/eval/test_smoke_p8b.py` | 2168 | **7** (#261's entire measurement) | `gap` — pytest-gated, type-ungated |
| 2 | `scripts/test_comms_consumer_eval.py` | 1170 | **10** | `gap` |
| 3 | `scripts/test_search_score_survey.py` | 636 | **5** | `gap` |
| 4 | `scripts/test_token_survey.py` | 578 | **10** | `gap` |
| 5 | `scripts/test_forgery_door_sweep.py` | 519 | **3** | `gap` — committed during this sweep |
| 6 | `scripts/test_mutation_proof.py` | 375 | 0 | `gap` |
| 7 | `scripts/test_scratch_copy.py` | 306 | 0 | `gap` |
| 8 | `scripts/test_snapshot_gc.py` | 251 | 0 | `gap` |
| 9 | `scripts/test_tree_fingerprint.py` | 165 | 0 | `gap` |
| 10 | `scripts/test_calibration_baseline.py` | 122 | 0 | `gap` |

### 4d. The hazard the brief named — a file inside a gate's directory the gate skips

```
=== inside a typecheck MEMBER directory, yet NOT discovered by mypy ===
  (none — every tracked .py under a member directory is in mypy's source list)
=== discovered by mypy but NOT committed (untracked files inside a gate) ===
  (none)
```

**A negative result, and it is only worth anything because CONTROL C proved the leg can return
a positive one.** Two real omission modes exist in this mypy version — a `__pycache__` tree, and
a `.py` whose stem collides with a sibling directory (`pkg.py` beside `pkg/`) — and neither
occurs in this tree today. This is the leg that would catch a future member gaining a
`foo.py` beside a `foo/`, which no path-arithmetic sweep can see.

### 4e. Committed shell — REPORTED, NOT CLASSIFIED (a widening, surfaced not adopted)

The brief told me to surface this rather than silently adopt or drop it. **There is no shell
gate in this repo at all** — `git grep -l shellcheck` returns nothing, and there is no CI
config of any kind (`.github`, `.gitlab`, `.circleci`, `.drone` — all absent). So these 7 files
are covered by no linter, no type checker, and no test-of-themselves:

| file | lines | note |
|---|---|---|
| `scripts/scratch_copy.sh` | 189 | the #140 provenance tool CLAUDE.md orders agents to USE; `scripts/test_scratch_copy.py` tests it (pytest-gated) |
| `scripts/zero_test_store.sh` | 161 | no test file names it |
| `scripts/contention_hunt.sh` | 92 | no test file names it |
| `scripts/tree_fingerprint.sh` | 90 | the #192 guard; `scripts/test_tree_fingerprint.py` tests it |
| `.claude/hooks/teammate-idle-gate.sh` | 78 | the idle-gate hook CLAUDE.md cites as the reference implementation |
| `skills/lore-deploy/scripts/conformance_run.sh` | 59 | the in-image conformance runner (#139) |
| `scripts/typecheck.sh` | 56 | **the canonical gate itself is ungated** |

**Question for the operator, not a verdict:** is the shell tree in packet 44's scope? Adopting
it means a new dependency (`shellcheck` is not installed and is not a Python package), which is
an install authorization, not a code change. I did not decide.

---

## 5. The sibling the derivation found — `skills/`, filed as #280

The packet's third Scope IN item asked for siblings **by derivation**. The 2×2 produced one
immediately, and it is the exact MIRROR of #261: `skills` is a `typecheck.sh` MEMBER (ruling
R9) and is in **no** `testpaths` entry. Derived generally — every committed file *shaped* like a
test (patterns read from config; `python_files` is unset, so pytest's documented defaults are in
force) that the standard gate never collects:

```
python_files patterns in force: ['test_*.py', '*_test.py'] (default — not set in pyproject)
committed test-SHAPED files: 147   collected by the standard gate: 139
TEST-SHAPED BUT NEVER COLLECTED: 8      <- all under skills/, nothing else in the tree
```

| file | tests | lines |
|---|---|---|
| `skills/lore-deploy/tests/test_workspace_probe.py` | 45 | 1438 |
| `skills/lore-deploy/scripts/test_lore_deploy.py` | 37 | 1984 |
| `skills/lore-deploy/scripts/test_conformance_provenance.py` | **16** | 475 |
| `skills/lore-deploy/tests/test_port_probe.py` | 5 | 149 |
| `skills/lore-deploy/tests/test_containerfile_locked.py` | 4 | 122 |
| `skills/lore-deploy/scripts/test_scaffold_config.py` | 4 | 92 |
| `skills/lore-deploy/scripts/test_merge_mcp_json.py` | 3 | 51 |
| `skills/lore-deploy/scripts/test_read_config_field.py` | 3 | 71 |

**117 tests that run only when someone remembers CLAUDE.md's idiom.** The sharpest row is
`test_conformance_provenance.py`: it guards `conformance_provenance.py::EXPECTED_MEMBERS`,
registration site #6, the guard that proves a workspace member ARRIVED in the deployed image —
CLAUDE.md's own words: *"A `COPY` with no guard entry is a deployment nobody checks"*, and a
missing member is *"an ImportError at boot, in production only, invisible to every test on this
host"* — #131/#139 verbatim.

**This one is cheap, and that is measured, because #188's law is "do not widen blind":**

```
$ uv run --no-sync pytest -q skills/lore-deploy/tests skills/lore-deploy/scripts | tail -1
117 passed in 14.60s
```
Isolated green is not evidence of a clean MERGE — the `tests.*` namespace collision that forces
`typecheck.sh` to iterate per-member lives exactly here — so I measured the merge too:
```
current testpaths alone                    : 8315 tests collected
current testpaths + skills/lore-deploy     : 8432 tests collected
8315 + 117 = 8432 exactly — no collision, no test lost.
```

---

## 6. Sizing — the packet has BALLOONED, and the law says that MANDATES a split

Packet 44 is a **0.15 wu** row. What it actually carries at `fe576ba`:

| item | measured cost |
|---|---|
| #261 — give `docs/eval` a type gate | **42 mypy errors in 3 files**, incl. DESIGN-LAW's A/B instrument, **plus a strategy design ruling** |
| #188 — `scripts/` under the type gate (a rider #238 explicitly left open) | **45 mypy errors in 7 files** |
| #280 — `skills/` into `testpaths` (NEW) | one line; measured green |
| #270 — markdown-it-py adoption | **moot at HEAD** (#283) — the tools are archived |
| #282 — stale prose + fired re-open trigger | a design call on consolidation, not an edit |

**87 mypy errors across 10 committed files, spanning two trees, gated behind a design ruling
that has never been made.** The decisive precedent is #188's own disposition (2026-07-26),
which sized **41** errors — one of the two trees, and the number has not improved — as *"its own
work item, sized ~half a session, NOT folded into any packet's exit"*, adding: **"Widening the
canonical runner is the LAST step, not the first — do it only once the number is zero, or the
gate lands red on day one and gets switched off, which is how an instrument dies."**

Packet 44 currently proposes to do that work for TWO trees inside 0.15 wu. **Recommended split
(the operator rules; I am recommending, not deciding):**

- **44a — `skills/lore-deploy` → `testpaths`** (#280). Zero design content, one line, measured
  green both isolated and merged. Ship it alone; it is the one piece that is genuinely 0.15 wu.
- **44b — the STRATEGY RULING for #261**, decided once: own typecheck leg with a scoped config ·
  move the smoke under a member · a pinned, loud exclusion. Design only, no error-fixing. **Note
  from #281: whichever wins must handle BOTH failure modes** — 3 `import-not-found` that are a
  resolution artifact, and ~32 ordinary un-annotated-code errors a config change cannot touch.
- **44c — `docs/eval` type debt to zero** (42/3), then join the runner.
- **44d — `scripts/` type debt to zero** (45/7). This is #188, already sized at ~half a session
  by its own disposition.
- **44e — close-outs**: #270 as superseded-by-relocation (#283), and route #282.

---

## 7. Numbers I re-derived rather than inherited, and a tree that moved under me

CLAUDE.md: *re-derive every number you inherit, INCLUDING from this file.* Every inherited
figure in packet 44's inputs was re-measured; **three of four had drifted.**

| source | inherited | re-derived at `fe576ba` |
|---|---|---|
| #188 | `41 errors in 6 files (14 source files)` | **45 errors in 7 files (19 source files)** |
| #261 | `7 errors` from a 2-file invocation | **42 errors in 3 files (4 source files)** in the runner's DIRECTORY shape — #281 |
| #261 | *"the 5021-line deploy smoke"* | the two files it names now total **5414**; the tree totals **6121** across **4** modules |
| #238 | `scripts/test_survey_stats.py::TestSmokeP8bPercentileUnits` | **that path does not exist** — the class moved to `loremaster/tests/test_stats.py`; the pin survived and improved, the citation dangles — #282 |

**#261's 7 reproduces exactly** (`docs/eval/test_smoke_p8b.py` contributes exactly 7), so its
author measured correctly — they measured the wrong SHAPE. `smoke_p8b.py` itself is **clean**;
the 42 come from `connections_p8a.py` (23), `evaluation_harness_p8a.py` (12), `test_smoke_p8b.py`
(7). ⚠ **My first per-file histogram over-counted** (50 and 63 against totals of 45 and 42),
because `grep '^[^:]*\.py'` catches mypy's `note:` lines as well as `error:` lines. Corrected
with `grep ': error:'`; the corrected per-file sums reconcile exactly with mypy's own totals.

**THE TREE MOVED UNDER ME, TWICE, AND I ONLY NOTICED BECAUSE THE ARITHMETIC DID NOT CLOSE.** A
sibling agent was writing `scripts/forgery_door_sweep.py` while I swept. First a 20-test
discrepancy appeared between two of my own collection counts (117 vs an implied 137); chasing it
showed the baseline had moved `8295 → 8315` from an untracked file. Then, between my detailed
run and my final run, HEAD moved `7bd9b4e → fe576ba` and both files became committed ground.

- **All headline numbers in this report are at `fe576ba`.** Where a `7bd9b4e` figure is quoted
  it is labelled (CONTROL B's 288/40).
- **Committed-ground `scripts/` was 42 errors in 6 files at `7bd9b4e`, and is 45 in 7 at
  `fe576ba`** — the +3 is `test_forgery_door_sweep.py`.
- ⚠ **Finding #281's body was written at `7bd9b4e`** and describes those two files as untracked
  in-flight work. **That is now stale by one commit** — they are committed, and the
  committed-ground number it reports as 42/6/17 is now 45/7/19. Whoever resolves #281 should add
  that note. I did not edit the filed body.
- The lesson is not the drift, it is that **the drift was invisible until a count refused to
  reconcile.** Scoping the property to `git ls-files` is what kept the *committed-ground* answer
  stable while the working tree moved.

---

## 8. SURFACED TO OPERATOR — questions, not verdicts

1. **Is the committed shell tree in scope for packet 44?** 7 `.sh` files, ~725 lines, covered by
   no gate whatsoever — including `scripts/typecheck.sh`, the canonical gate itself, and
   `scratch_copy.sh`, which CLAUDE.md orders every mutating agent to use. Adopting `shellcheck`
   is an install authorization, not a code change. **Should I have widened the property to
   `.sh`, or is "ungated ground" Python-only?** I reported and did not adopt.
2. **#270 is moot at HEAD — close it?** Its tools were archived at `d74e1da` and marked at
   `499003f`; option (1) of its own recommended sequence was already taken by someone who did not
   know they were discharging it. **But the parsing defect it measured is now FROZEN INTO A
   RECEIPT** — `grade.py` and `check_coherence.py` produced packet 11-i-b's published scoreboard,
   and nobody has checked whether any graded cell contained a pipe. Worth one command? (#283)
3. **A fired, undischarged re-open trigger.** `TestSmokeP8bPercentileUnits`'s docstring still
   teaches *"docs/eval is outside testpaths… so no gate watches its imports"* — false since
   `44e2e65` (2026-07-26) — and its own trigger says the trade changes *"the day docs/eval gains
   a testpaths entry."* That day was three days ago. **Fix in packet 44 (same tree) or route
   out?** The consolidation half is a design call, not a docstring edit. (#282)
4. **The instrument's home is a design ruling in flight.** The brief told me not to commit
   `ungated_sweep.py` to `scripts/`. Noting the recursion honestly: **if it lands in `scripts/`
   it becomes row 14 of §4b — a committed instrument that is itself untyped and uncollected.**
   Whatever #261 strategy wins should be applied to it in the same breath, or packet 44 ships a
   fifth instance of the class it exists to close.
5. **`registration_sites.py` is named by zero test files** and is untyped — the derivation
   CLAUDE.md orders every agent to RUN rather than read a list. Its own exit code is load-bearing.
   In scope, or its own row?
6. **There is no CI in this repo.** Packet 44's Exit says *"typecheck legs run in CI-shape, not
   just locally"*, and no `.github` / `.gitlab` / `.circleci` / `.drone` config exists. **What does
   "CI-shape" mean here** — a clean-shell run of the runner from the repo root, or does packet 44
   include standing up CI? Those are very different sizes.
7. **An instrument-preservation observation, offered because brief-base v9 §1 makes it topical:**
   `scripts/forgery_door_sweep.py` was committed mid-sweep with the message *"the instrument two
   agents built and both times lost"* (#278). This sweep's instrument is in §10 verbatim for
   exactly that reason.

---

## 9. `Packages considered:` — the detail

| mechanism | package evaluated | what I READ | verdict |
|---|---|---|---|
| mypy's file discovery | `mypy.find_sources.create_source_list` + `mypy.config_parser.parse_config_file` | live probe of both signatures; confirmed `BuildSource(path=…)` return and that `parse_config_file`'s 2nd arg is a **zero-arg** callable (my first call passed `lambda x:` and raised) | **replace** — asking mypy beats modelling its recursion, stem-collision and exclude rules by hand; a wrong model reads as coverage |
| pytest's collection | `pytest --collect-only -q` | its node-id output shape (`path::test`) | **replace** — re-implementing `python_files` matching + "does it hold tests" is a second implementation of pytest's discovery, and §5's whole point is that shape-matching and collection differ |
| TOML parsing | `tomllib` (stdlib) | — | **replace** — no hand-parsing |
| tracked-file enumeration | `git ls-files -z` | — | **replace** |
| ruff's file discovery | `ruff check . --show-files` | its output shape | **replace** — and it corrected my wrong-shaped first attempt (§4a) |
| `MEMBERS=(…)` bash-array read | none adopted | — | **bespoke**, one anchored regex. The only package-shaped alternative is `source`-ing `typecheck.sh`, which **EXECUTES the gate as a side effect of reading it**. Minimal surface, and it aborts loudly rather than returning an empty list (§3 CONTROL D). ⚠ If the runner ever computes `MEMBERS` dynamically this regex silently sees the literal — a named bound, not a covered case. |

No install authorization is needed for anything above; all are already present.

---

## 10. The instrument, verbatim

Per brief-base §1: an instrument built to establish a load-bearing claim is a deliverable. It is
**not committed** (the brief forbade it — its home is a design ruling in flight with the Fable
sidecar), so it survives here. It lived at
`<scratchpad>/ungated_sweep.py` during the run; that address is unrecoverable by construction,
which is why the bytes are below. Invoke from anywhere inside the repo:
`uv run --no-sync python ungated_sweep.py`.

```python
#!/usr/bin/env python3
"""ungated_sweep.py — DERIVE every committed file that no repo gate covers.

**WHY THIS SHAPE** (packet 44, finding-class #188 / #233 / #238 / #261 / #270).

Four times this repo has discovered a tree holding load-bearing committed code that no
gate covers, and every one of the four was found by an agent tripping over it — never by
an instrument. ``CLAUDE.md``'s standing lesson is that *an enumeration of places to look
is the artifact this repo has the most receipts against*, so this script holds no list of
ungated trees. It derives them, exactly as ``scripts/registration_sites.py`` derives
registration sites, from a property:

    A COMMITTED FILE IS UNGATED WHEN NO GATE'S OWN DISCOVERY MECHANISM REACHES IT.

Both gate memberships are read FROM THE REAL CONFIG FILES at runtime — ``MEMBERS=(...)``
out of ``scripts/typecheck.sh``, ``testpaths`` out of ``pyproject.toml``. Nothing here
mirrors them. A hand-mirrored copy of a config list is the stale-mirror hazard
``CLAUDE.md`` records against ``scratch_provenance.py::WORKSPACE_MEMBERS``, and this
script exists to catch that class, not to add to it.

**IT ASKS THE GATES, IT DOES NOT MODEL THEM.** Two levels of answer are produced, because
they differ and the difference is the interesting part:

* **COARSE (path arithmetic)** — is the file under a typecheck member directory / under a
  ``testpaths`` entry? This is the property as packet 44 words it, and it is what scopes
  the packet.
* **ACTUAL (each gate's own discovery)** — mypy's real source discovery
  (``mypy.find_sources.create_source_list`` under the config parsed from
  ``pyproject.toml``) and pytest's real collection (``pytest --collect-only``). A file can
  sit inside a gate's directory and still be invisible to that gate: ``testpaths`` runs
  pytest over a tree, it does not make every ``.py`` in that tree a test, and
  ``docs/eval/smoke_p8b.py`` is 3111 lines of deploy-gating code that neither gate reads.

The two gates are ORTHOGONAL — a file may be typed-but-uncollected or collected-but-
untyped — so the output is a 2x2, never a flat "ungated" list.

**ANTI-VACUITY.** Every input is asserted non-empty and every classifier is proven able
to emit BOTH verdicts before any result is printed (``_prove_the_instrument_works``). The
failure this guards is the one that reads as success: if the ``git ls-files`` glob matched
nothing, or the ``MEMBERS=`` regex silently produced ``.``, this script would print
"0 gaps" and a reader would file it as a clean bill of health. It now aborts loudly
instead.

**BOUNDS, stated so the next reader meets them deliberately:**

* It answers *"does a gate's discovery REACH this file"*, never *"is this file
  adequately tested/typed"*. A collected test file that asserts nothing passes this
  sweep.
* ``mypy.find_sources`` is an internal mypy API. It is the same discovery the binary
  uses, but a mypy upgrade may move it; the script fails loudly rather than falling back
  silently.
* Gates other than mypy and pytest are NOT modelled (ruff, the AST scans, the deploy
  conformance guard). A file this script calls "ungated" may still be linted.
* Non-Python committed executables (``.sh``) are REPORTED, never classified — this repo
  has no shell gate at all, which is a scope question for the operator, not a verdict
  this script may render.

USAGE

    ./ungated_sweep.py                 # the 2x2 + every row, individually
    ./ungated_sweep.py --exit-nonzero  # also exit 1 if any true gap exists
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path

#: ``MEMBERS=(a b c)`` in ``scripts/typecheck.sh``. Anchored to the start of a line so a
#: mention inside a comment cannot be mistaken for the declaration.
_MEMBERS_ASSIGNMENT = re.compile(r"^MEMBERS=\(([^)]*)\)", re.MULTILINE)

#: A path that exists in no tree, used as the NEGATIVE CONTROL. If the classifier cannot
#: call this ungated, it cannot call anything ungated, and a "0 gaps" result is a lie.
_IMPOSSIBLE_PATH = "__no_such_tree_44__/probe.py"

_EXIT_OK = 0
_EXIT_GAPS = 1
_EXIT_INSTRUMENT_BROKEN = 2


@dataclass(frozen=True)
class GateVerdict:
    """How each gate's own discovery answers for one committed file."""

    path: str
    under_typecheck_member: bool
    under_testpath: bool
    checked_by_mypy: bool
    collected_by_pytest: bool

    @property
    def is_coarse_gap(self) -> bool:
        """The packet-44 property as worded: outside every member AND every testpath."""
        return not self.under_typecheck_member and not self.under_testpath

    @property
    def is_actual_gap(self) -> bool:
        """Neither gate's discovery reaches this file, whatever directory it sits in."""
        return not self.checked_by_mypy and not self.collected_by_pytest

    @property
    def quadrant(self) -> str:
        """Which cell of the typed x tested 2x2 this file lands in."""
        typed = "typed" if self.checked_by_mypy else "UNTYPED"
        tested = "collected" if self.collected_by_pytest else "UNCOLLECTED"
        return f"{typed} / {tested}"


def typecheck_members(repo_root: Path) -> list[str]:
    """The mypy gate's scope, parsed from the canonical runner itself."""
    runner = repo_root / "scripts" / "typecheck.sh"
    match = _MEMBERS_ASSIGNMENT.search(runner.read_text(encoding="utf-8"))
    if match is None:
        raise SystemExit(
            f"INSTRUMENT BROKEN: no `MEMBERS=(...)` assignment found in {runner}. "
            "The mypy gate's scope could not be derived — do NOT read any result below "
            "as a clean tree."
        )
    return [word for word in match.group(1).split() if word]


def pytest_testpaths(repo_root: Path) -> list[str]:
    """The pytest gate's scope, parsed from the root manifest."""
    manifest = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    paths: list[str] = manifest["tool"]["pytest"]["ini_options"]["testpaths"]
    return list(paths)


def ruff_excluded_trees(repo_root: Path) -> list[str]:
    """Trees ruff is configured to skip — the repo's own declaration of "archived, not source".

    Read rather than listed, so an exemption in this sweep's output is always backed by a
    line someone actually committed in ``pyproject.toml`` rather than by this script's
    opinion.
    """
    manifest = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    excluded: list[str] = manifest["tool"]["ruff"].get("extend-exclude", [])
    return list(excluded)


def mypy_exclude_patterns(repo_root: Path) -> list[str]:
    """``[tool.mypy] exclude`` — a file inside a member that mypy skips is ungated IN FACT."""
    manifest = tomllib.loads((repo_root / "pyproject.toml").read_text(encoding="utf-8"))
    patterns = manifest["tool"]["mypy"].get("exclude", [])
    return [patterns] if isinstance(patterns, str) else list(patterns)


def tracked_files(repo_root: Path) -> list[str]:
    """Every committed file, from git. Untracked scratch is not committed ground."""
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["git", "ls-files", "-z"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    return [name for name in completed.stdout.split("\0") if name]


def mypy_checked_files(repo_root: Path, members: list[str]) -> set[str]:
    """Ask MYPY which files it would check, under the repo's real config.

    This is mypy's own discovery, not a re-implementation of it: the same
    ``create_source_list`` the binary calls, with options parsed from ``pyproject.toml``
    so ``exclude`` / ``explicit_package_bases`` / ``namespace_packages`` are honoured.
    Modelling directory recursion by hand would reproduce mypy's stem-collision and
    dotted-name rules by guesswork, and a wrong model here reads as coverage.
    """
    try:
        from mypy.config_parser import parse_config_file
        from mypy.find_sources import create_source_list
        from mypy.options import Options
    except ImportError as exc:  # pragma: no cover - environment problem, reported loudly
        raise SystemExit(
            f"INSTRUMENT BROKEN: mypy's discovery API is unavailable ({exc}). This script "
            "refuses to fall back to path-prefix guessing, because a guessed mypy scope "
            "reads as coverage. Run it inside the workspace venv (`uv run`)."
        ) from exc

    options = Options()
    parse_config_file(options, lambda: None, str(repo_root / "pyproject.toml"), sys.stdout, sys.stderr)
    checked: set[str] = set()
    for member in members:
        for source in create_source_list([str(repo_root / member)], options):
            checked.add(str(Path(source.path).resolve().relative_to(repo_root)))
    return checked


def pytest_collected_files(repo_root: Path) -> set[str]:
    """Ask PYTEST which files it actually collects tests from, under the repo's real config.

    ``testpaths`` names directories; it does not make every ``.py`` inside one a test.
    The only honest answer to "does the pytest gate read this file" is pytest's own
    collection, so this shells out rather than re-implementing ``python_files`` matching
    and test discovery.
    """
    completed = subprocess.run(  # noqa: S603 - fixed argv, no shell
        ["uv", "run", "--no-sync", "pytest", "--collect-only", "-q"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(
            f"INSTRUMENT BROKEN: `pytest --collect-only` exited {completed.returncode}. "
            "An errored or empty collection would make every file look UNCOLLECTED, which "
            "reads as a finding rather than as a broken instrument.\n"
            f"{completed.stdout[-2000:]}\n{completed.stderr[-2000:]}"
        )
    collected: set[str] = set()
    for line in completed.stdout.splitlines():
        node, separator, _ = line.partition("::")
        if separator and node.endswith(".py"):
            collected.add(node.strip())
    return collected


def _under_any(path: str, trees: list[str]) -> bool:
    """Is ``path`` the tree itself, or inside it? Path-component aware, never a substring."""
    parts = Path(path).parts
    return any(parts[: len(Path(tree).parts)] == Path(tree).parts for tree in trees)


def classify(
    paths: list[str],
    members: list[str],
    testpaths: list[str],
    mypy_files: set[str],
    pytest_files: set[str],
) -> list[GateVerdict]:
    """One verdict per file — both the coarse path property and each gate's real reach."""
    return [
        GateVerdict(
            path=path,
            under_typecheck_member=_under_any(path, members),
            under_testpath=_under_any(path, testpaths),
            checked_by_mypy=path in mypy_files,
            collected_by_pytest=path in pytest_files,
        )
        for path in paths
    ]


def _prove_the_instrument_works(
    members: list[str],
    testpaths: list[str],
    tracked: list[str],
    python_files: list[str],
    mypy_files: set[str],
    pytest_files: set[str],
    repo_root: Path,
) -> None:
    """Abort unless every input is non-empty AND both verdicts are demonstrably reachable.

    THE FAILURE THIS EXISTS FOR: every silent no-op upstream of the report produces the
    SAME output as a clean tree. An empty ``MEMBERS`` parse, a ``git ls-files`` glob that
    matched nothing, a ``members`` entry that widened to ``.`` — each ends in a printed
    number that a reader files as reassurance. So the question asked here is *"if step N
    silently no-opped, would step N+1 still print something that reads as success?"*, and
    every path where the answer was yes is closed below.
    """
    if not members:
        raise SystemExit("INSTRUMENT BROKEN: zero typecheck members parsed.")
    for member in members:
        if member in {".", "..", "/", ""} or Path(member).is_absolute():
            raise SystemExit(
                f"INSTRUMENT BROKEN: typecheck member {member!r} is a whole-tree wildcard. "
                "It would mark every file gated and print zero gaps."
            )
        if not (repo_root / member).is_dir():
            raise SystemExit(f"INSTRUMENT BROKEN: typecheck member {member!r} is not a directory.")
    if not testpaths:
        raise SystemExit("INSTRUMENT BROKEN: zero pytest testpaths parsed.")
    for testpath in testpaths:
        if not (repo_root / testpath).exists():
            raise SystemExit(f"INSTRUMENT BROKEN: testpath {testpath!r} does not exist.")
    if not tracked:
        raise SystemExit("INSTRUMENT BROKEN: `git ls-files` returned nothing.")
    if not python_files:
        raise SystemExit("INSTRUMENT BROKEN: zero tracked .py files — the glob matched nothing.")
    if not mypy_files:
        raise SystemExit("INSTRUMENT BROKEN: mypy discovered zero files across all members.")
    if not pytest_files:
        raise SystemExit("INSTRUMENT BROKEN: pytest collected zero files.")

    # POSITIVE CONTROL — the classifier can say "gated" on both axes.
    verdicts = classify(python_files, members, testpaths, mypy_files, pytest_files)
    if not any(verdict.checked_by_mypy for verdict in verdicts):
        raise SystemExit("INSTRUMENT BROKEN: no tracked file classified as mypy-checked.")
    if not any(verdict.collected_by_pytest for verdict in verdicts):
        raise SystemExit("INSTRUMENT BROKEN: no tracked file classified as pytest-collected.")

    # NEGATIVE CONTROL — and it can say "ungated". Without this leg a classifier stuck at
    # True prints a clean tree, which is the false-clear direction.
    impossible = classify([_IMPOSSIBLE_PATH], members, testpaths, mypy_files, pytest_files)[0]
    if not impossible.is_actual_gap or not impossible.is_coarse_gap:
        raise SystemExit(
            f"INSTRUMENT BROKEN: the control path {_IMPOSSIBLE_PATH!r} classified as GATED. "
            "The classifier cannot produce an ungated verdict, so a zero count below would "
            "be an artifact, not a result."
        )


def main(argv: list[str] | None = None) -> int:
    """Report the ungated set; return an exit code."""
    parser = argparse.ArgumentParser(
        prog="ungated_sweep.py",
        description="Derive every committed file no repo gate covers (packet 44).",
    )
    parser.add_argument(
        "--exit-nonzero", action="store_true", help="exit 1 when any true gap exists"
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent
    if not (repo_root / ".git").exists():
        repo_root = Path(
            subprocess.run(  # noqa: S603 - fixed argv, no shell
                ["git", "rev-parse", "--show-toplevel"],
                capture_output=True,
                text=True,
                check=True,
            ).stdout.strip()
        )

    members = typecheck_members(repo_root)
    testpaths = pytest_testpaths(repo_root)
    archived_trees = ruff_excluded_trees(repo_root)
    mypy_excludes = mypy_exclude_patterns(repo_root)
    tracked = tracked_files(repo_root)
    python_files = sorted(name for name in tracked if name.endswith(".py"))
    shell_files = sorted(name for name in tracked if name.endswith((".sh", ".bash")))
    mypy_files = mypy_checked_files(repo_root, members)
    pytest_files = pytest_collected_files(repo_root)

    _prove_the_instrument_works(
        members, testpaths, tracked, python_files, mypy_files, pytest_files, repo_root
    )

    verdicts = classify(python_files, members, testpaths, mypy_files, pytest_files)

    print(f"repo root                : {repo_root}")
    print(f"typecheck.sh MEMBERS ({len(members)}) : {' '.join(members)}")
    print(f"pytest testpaths ({len(testpaths)})    : {' '.join(testpaths)}")
    print(f"[tool.mypy] exclude       : {mypy_excludes or 'NONE DECLARED'}")
    print(f"[tool.ruff] extend-exclude: {archived_trees or 'NONE DECLARED'}")
    print(f"tracked files             : {len(tracked)}")
    print(f"tracked .py               : {len(python_files)}")
    print(f"mypy discovers            : {len(mypy_files)} files across the members")
    print(f"pytest collects from      : {len(pytest_files)} files")
    print()

    quadrants: dict[str, list[GateVerdict]] = {}
    for verdict in verdicts:
        quadrants.setdefault(verdict.quadrant, []).append(verdict)
    print("2x2 — mypy discovery x pytest collection, over all tracked .py:")
    for quadrant in sorted(quadrants):
        print(f"  {quadrant:26s} {len(quadrants[quadrant]):4d}")
    print()

    coarse = [verdict for verdict in verdicts if verdict.is_coarse_gap]
    actual = [verdict for verdict in verdicts if verdict.is_actual_gap]
    print(f"COARSE gaps (packet-44 property: outside every member AND every testpath): {len(coarse)}")
    print(f"ACTUAL gaps (neither gate's discovery reaches the file):                   {len(actual)}")
    print()

    print("=== COARSE gap rows ===")
    for verdict in coarse:
        lines = len((repo_root / verdict.path).read_text(encoding="utf-8", errors="replace").splitlines())
        archived = "archived-tree" if _under_any(verdict.path, archived_trees) else "LIVE-TREE"
        print(f"  {verdict.path}  [{lines} lines] [{archived}] [{verdict.quadrant}]")
    print()

    print("=== ACTUAL gap rows (untyped AND uncollected) ===")
    for verdict in actual:
        lines = len((repo_root / verdict.path).read_text(encoding="utf-8", errors="replace").splitlines())
        archived = "archived-tree" if _under_any(verdict.path, archived_trees) else "LIVE-TREE"
        inside = []
        if verdict.under_typecheck_member:
            inside.append("in-member-dir")
        if verdict.under_testpath:
            inside.append("in-testpath-dir")
        print(f"  {verdict.path}  [{lines} lines] [{archived}] [{','.join(inside) or 'outside-both-dirs'}]")
    print()

    # THE SUBTLETY THAT MAKES THE COARSE PROPERTY UNSOUND IN BOTH DIRECTIONS. Sitting in a
    # gate's directory is not the same as being reached by that gate's discovery: mypy skips
    # a file whose stem collides with a sibling directory or contains a dot, and pytest
    # collects only what matches ``python_files`` AND holds tests. A file in this section
    # passes the coarse property while being ungated in fact — which is exactly how #261's
    # 3246-line deploy smoke sat inside ``testpaths`` and inside no gate.
    print("=== inside a typecheck MEMBER directory, yet NOT discovered by mypy ===")
    invisible_to_mypy = [
        verdict
        for verdict in verdicts
        if verdict.under_typecheck_member and not verdict.checked_by_mypy
    ]
    for verdict in invisible_to_mypy:
        print(f"  {verdict.path}  [{verdict.quadrant}]")
    if not invisible_to_mypy:
        print("  (none — every tracked .py under a member directory is in mypy's source list)")
    print()

    print("=== collected by pytest, yet NOT discovered by mypy (tested but untyped) ===")
    tested_untyped = [
        verdict for verdict in verdicts if verdict.collected_by_pytest and not verdict.checked_by_mypy
    ]
    for verdict in tested_untyped:
        lines = len((repo_root / verdict.path).read_text(encoding="utf-8", errors="replace").splitlines())
        print(f"  {verdict.path}  [{lines} lines]")
    if not tested_untyped:
        print("  (none)")
    print()

    print("=== discovered by mypy but NOT committed (untracked files inside a gate) ===")
    untracked_in_gate = sorted(mypy_files - set(tracked))
    for name in untracked_in_gate:
        print(f"  {name}")
    if not untracked_in_gate:
        print("  (none)")
    print()

    print("=== committed shell executables — REPORTED, NOT CLASSIFIED ===")
    print("    (this repo declares no shell gate; whether one is in scope is the operator's call)")
    for name in shell_files:
        lines = len((repo_root / name).read_text(encoding="utf-8", errors="replace").splitlines())
        print(f"  {name}  [{lines} lines]")

    if args.exit_nonzero and actual:
        return _EXIT_GAPS
    return _EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
```

**Known nits in the pasted bytes, disclosed rather than silently fixed** (it is a scratch
instrument the lead may promote): `_EXIT_INSTRUMENT_BROKEN` is declared and unused (the abort
path uses `SystemExit(str)`, which exits 1); the docstring says "3111 lines" quoting #261 where
the file is now 3246; `repo_root` falls back to `git rev-parse` and therefore requires the cwd
to be inside the repo when the script lives outside it. **If promoted to `scripts/` it must also
be brought under whichever gate strategy #261 settles** — see §8 item 4.

---

## 11. Findings filed

| # | subject | area | category |
|---|---|---|---|
| **#280** | `skills/` holds 117 committed tests the standard pytest gate NEVER collects — third instance of the #199/#238 class, incl. the #131/#139 image-conformance guard | `pyproject/testpaths` | `test_gap` |
| **#281** | #261 understates its own scope 6× — `mypy docs/eval` in the RUNNER SHAPE is 42 errors in 3 files, two of them modules #261 never named | `scripts/typecheck.sh / docs/eval` | `coverage_gap` |
| **#282** | `TestSmokeP8bPercentileUnits` teaches a retired fact and its own named RE-OPEN TRIGGER fired 3 days ago, undischarged | `loremaster/tests/test_stats.py` | `stale_prose` |
| **#283** | #270's premise no longer holds — the consult tools were archived (`d74e1da`) and marked (`499003f`); option (1) of its own sequence was already taken | `consult-11ib/tools` | `stale_premise` |

Nothing was fixed. The repo tree is unmodified by me: my only write is this file.

---

## 12. Bounds on this whole report

1. **Two gates modelled, one measured separately.** mypy and pytest are the sweep's axes; ruff
   was measured but is not a column. The AST scans' `_SCANNED_MEMBERS`, the in-image conformance
   guard, and `registration_sites.py` are gates this sweep does not model. **A file called
   "ungated" here is ungated BY MYPY AND PYTEST**, which is the property packet 44 names — not
   by everything.
2. **Reach, not adequacy.** Every verdict answers *"does discovery reach this file"*. It says
   nothing about whether the tests assert anything or the annotations are honest.
3. **Committed ground only.** Untracked files are invisible by construction — deliberate, and it
   is what kept the answer stable while the tree moved twice under me (§7).
4. **`mypy.find_sources` is an internal API.** It is the same discovery the binary uses today; a
   mypy upgrade may move it. The script fails loudly rather than degrading to a path-prefix
   guess.
5. **Findings, not verdicts.** Following #282's dangling citation found one stale-prose instance.
   **No systematic sweep for other prose asserting gate membership was run**, and the derived
   instrument for that class — a scan asserting no committed string claims a tree is outside
   `testpaths`/`typecheck.sh` when the config says otherwise — does not exist. That is the
   PKT-28 C1 lesson ("a diagnosis is not an instrument") still outstanding for this class.
6. **All measurements are at `fe576ba`** on branch `feat/surreal-unification`, 2026-07-29,
   except CONTROL B (labelled `7bd9b4e`). Every number in this report has a command beside it or
   in §3/§5/§7; **no count is stated that I did not run.**
