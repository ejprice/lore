# REPORT-fixer-44-audit-1 — closing `coldaudit-44-1`'s two blockers and its mechanical defects

*Everything in this report is measured at worktree `pkt44` (`/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44`),
branch `pkt44/ungated-ground`, HEAD `9377af5`, on 2026-07-30. Every number is derived here, not
inherited — including the ones I took from the audit.*

## SUMMARY BLOCK

```
brief-base v9 read
brief project v7 read
brief pkt44 v3 read
state: done-with-deviations
deviation 1: D7 (INDEX.md:283) NOT edited — the brief's writable set and its NOT-YOURS list
             contradict each other on that one file; exact edit given in §7, decision needed.
deviation 2: fixed TWO defects the audit did not list — D14 (a `collected_test_files` docstring
             falsified by R10's own grant) and D15 (`wrong_builds.py` reported 3 PHANTOM
             SURVIVORS against a baseline that collected NOTHING). Both in the writable set,
             both the same class as the items I was sent for. §5.
deviation 3: closed D2's class at the SEAM (`findings_of` now refuses a blind verdict) rather
             than at the two call sites named — one implementation, 13 call sites. §3.
Packages considered: none — no new mechanism specified; every fix is an edit to an existing
             stdlib-only instrument (`gated_ground.py` imports the stdlib by ruling), and the
             three instruments I ran (`mutation_proof.py`, `wrong_builds.py`, the audit's
             `probe_memo_stale.py`) are this repo's own.
decisions-needed: D7 routing (§7.1) · the `scripts/test_wrong_builds.py` home (§7.2) ·
             REPORT-author-44-monotonic-1.md still teaches the retired roster bound (§7.3)
receipts: gates §6 · D1 probe + both controls §2.3 · D2 before/after mutation proofs §3.2 ·
             four mutation proofs §4 · guard verdict verbatim §6.4 · md5 freeze §8
```

## 0. CAPABILITY CHECK (brief-base §4)

Everything the brief demanded was available. `lore_comms` and `lore_findings` **loaded and
worked** — `register`, `brief_get pkt44`, and four `drain` calls all returned. **Finding #287 did
NOT reproduce for me**, which matches `coldaudit-44-1`'s experience and not the three agents who
reported them absent; that is a second data point for intermittency, not a closure.

lore's **index** is blind in this worktree (#125), so every structural search in this report is
`git grep`. **Said out loud, as required.** I did not file a friction row for it: #125 already
exists and is the reason the brief told me to use `git grep`.

## 1. WHAT I CHANGED

| file | what |
|---|---|
| `scripts/gated_ground.py` | D1 (the conftest chain in `_collector_input_paths` + the rewritten `collector-memoisation` bound, in `STATED_BOUNDS` and the module docstring) · R13/D8 (`_types_message` / `_execution_message` + the `EXEMPTIONS` note) · D14 (`collected_test_files`'s falsified docstring) |
| `scripts/test_gated_ground.py` | D2 at both real-tree pins **and at the `findings_of` seam** · the D1 pin · the rewritten memoisation-bound pin (inverted) · the D13 applicability pin · R13's renamed constant and its prose |
| `scripts/wrong_builds.py` | D13 (WB19's escaping bug + a NOT-COMPARABLE summary category + exit code) · D15 (baseline anti-vacuity, stderr no longer discarded, corrected HOW TO RUN) |
| `scripts/typecheck.sh` | D4 ("two of the entries" → point at the list) · D5 ("eleven sites" → scoped, dated, with the derivation) |
| `docs/design/2026-07-25-floor-calibration-addendum-F.md` | D6 (a dated correction block; the original text left standing) |

Nothing else. `git status --porcelain` shows exactly those five files modified plus the untracked
`REPORT-coldaudit-44-1.md` I was handed.

## 2. D1 — BLOCKER, CLOSED

### 2.1 The fix

`_collector_input_paths` gained a **fourth population**: for each testpath, every `conftest.py`
from `repo_root` down to it. Four lines of code; the docstring now names conftest loading as a
*second mechanism* — pytest walks rootdir → the collection target — distinct from `locate_config`,
which was the only one the previous docstring reasoned about.

### 2.2 The bound, rewritten as a PROPERTY

The old bound said the key covers *"the collector's file inputs and PYTEST_ADDOPTS, and no other
variable"* and then enumerated three environment variables as the residual. **That enumeration was
the defect**, not merely beside it: a residual stated as a roster of variable names cannot contain
a file. It now reads:

> summary: *"The memo key covers a DERIVED address set plus PYTEST_ADDOPTS; every other collector
> input is outside it."*
>
> trigger: *"the collector's answer is ever made to depend, within ONE process, on state outside
> the address set `_collector_input_paths` derives — a second environment variable, an installed
> distribution, a non-.py file. The residual here is the COMPLEMENT of a derived set and not a
> roster of names…"*

The three measured environment instances survive in the module docstring, **explicitly labelled as
instances rather than as the extent** — deleting them would have lost a real measurement (E6 / the
audit's R-5 holds a patch for them).

**And the pin that guarded this bound was itself keyed on the roster.**
`test_the_memoisation_bound_never_names_a_variable_the_key_already_covers` *required* the trigger
to name an uppercase environment-variable token — so it was enforcing the shape that hid the hole.
I inverted it:

* kept: no variable the instrument demonstrably reads (AST-derived) may appear in the trigger;
* **new, inverted:** no environment-variable-shaped token may appear **at all** — the roster form
  growing back is now the failure;
* **new, anti-vacuity:** the trigger must name `_collector_input_paths` **as a symbol**, so a
  complement that names nothing is refused and renaming the derivation reddens the bound that
  describes it.

### 2.3 The audit's own probe, re-run — the receipt the brief asked for

I extracted §9.1 of `REPORT-coldaudit-44-1.md` **programmatically** (fence-to-fence, no
transcription) and ran it against the fixed guard:

```
gg.__file__ = /home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44/scripts/gated_ground.py
A. healthy, cold memo (warms it)                           state=GATED_GROUND   exit=0 findings=0 blind=0
B. NEG CTRL: unkeyed silencer + KEYED manifest change      state=UNGATED_GROUND exit=1 findings=1 blind=0
C. healthy again, cold memo (warms it)                     state=GATED_GROUND   exit=0 findings=0 blind=0
D. unkeyed silencer ONLY, warm memo                        state=UNGATED_GROUND exit=1 findings=1 blind=0
E. POS CTRL: same tree, memo cleared                       state=UNGATED_GROUND exit=1 findings=1 blind=0

bytes identical C vs D: False  <-- True == FALSE CLEAR
NEG CTRL passes (keyed change forced a re-run): True
POS CTRL passes (the guard can see the mutation): True
```

**Row D flipped from `GATED_GROUND` to `UNGATED_GROUND` and now equals row E**, `bytes identical C
vs D` is **False** (was True), and **both controls still fire**: the negative control proves the
memo is not merely always-stale, the positive control proves the mutation is real and visible. Run
twice, before and after the mypy-driven rename in §6.2; identical output.

### 2.4 The pin

`TestTheCollectorIsMemoisedAndTheMemoInvalidates::test_an_untracked_conftest_in_an_ANCESTOR_of_a_collection_root_moves_the_key`,
three legs, each killing a build the others wave through: the **address set** must contain the file
(a build that "fixed" this by never memoising passes the other two), the **key** must move, and the
**served bytes** must differ (the false clear itself — the only leg a consumer can see). Mutation
proof in §4.

## 3. D2 — BLOCKER, CLOSED, AND THE CLASS CLOSED WITH IT

### 3.1 The sweep the brief demanded — every `.findings` site, individually

`git grep -n 'findings_of\|\.findings\b' scripts/test_gated_ground.py` → 21 sites. **No wholesale
verdict; each one below is its own.** The question asked of each: *would a BLIND verdict (findings
== () by construction) satisfy this assertion?*

| site (symbol) | shape | verdict |
|---|---|---|
| `TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis` | `assert not findings` on **REPO_ROOT** | ❗**D2 — FIXED**, now `verdict.is_clean` |
| `TestTheExemptionTableIsAnAllowlistOfTheSafe::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE` | `assert not with_none.findings` on **REPO_ROOT** | ❗**D2 — FIXED**, now `with_none.is_clean` |
| `TestTheDerivationIsWholeTreeQuantified` (the `scratchpad/session_debris.py` absence pin) | `assert <path> not in reported` on a fixture | ⚠ **same shape, fixture-scoped — closed by the seam fix below** |
| `TestTheDerivationIsWholeTreeQuantified` (the `docs/consult/notes.py.txt` absence pin) | `assert <path> not in reported` on a fixture | ⚠ **same shape, fixture-scoped — closed by the seam fix below** |
| `_row_is_load_bearing` | returns `any(...)` over findings | **safe as used** — its call sites pair a live row (reddens on blind) with a dead one in one test |
| `assert_every_tracked_file_is_accounted_for` | compares findings to `gg.classify` | **safe by construction** — `classify` RAISES on blindness, so the comparison is unreachable blind |
| `TestBlindnessIsMonotoneToTheServedSurface::test_a_clean_tree_serves_a_clean_verdict` | `verdict.findings == ()` | **safe** — paired with `blind_sources == ()` and `is_clean` in the same test |
| the forgery-matrix pin (`assert not verdict.findings` under a broken dependency) | asserts a blind verdict carries no findings | **correct as-is** — it is *about* blindness, opposite direction |
| the remaining 13 (`half_gapped_*`, `workspace_shaped_*`, ordering, message, hostile-path) | assert findings **ARE** present | **safe** — a blind verdict reddens them |

### 3.2 The fix, and the proof it discriminates — BOTH directions

Both real-tree pins now assert `is_clean`. The headline pin additionally calls
`gg.ungated_ground(REPO_ROOT)` with the **shipped default**, which closes residual **R-8** in the
same edit; the empty-table pin deliberately keeps `exemptions=()` because its whole claim is
*empty-because-nothing-needs-exempting*.

**BEFORE** — the same forced-blindness mutation, against the *old* assertions, declared set written
to `/tmp/fixer44/declared_d2.txt` before the run and taken from `--collect-only`:

```
mutation LANDED (anchor matched exactly once) in scripts/gated_ground.py
..                                                                       [100%]
2 passed in 0.04s
PROOF FAILED — the observed RED set is not the declared one.
  DECLARED RED but STAYED GREEN (the pin never fired):
    - …::test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE
    - …::test_no_committed_python_is_ungated_on_either_axis
```

**`2 passed in 0.04s` over a guard that had read nothing.** That is D2, reproduced mechanically
rather than argued.

**AFTER** — same mutation, same declared set:

```
FF                                                                       [100%]
E   AssertionError: the repository's verdict is BLIND, not GATED_GROUND: 0 committed file/axis
E   pair(s) are ungated ground and 1 input(s) could not be read.
2 failed in 0.30s
PROOF HELD — the declared RED set fired EXACTLY
```

### 3.3 ONE IMPLEMENTATION — the class, not the two instances (deviation 3)

The brief said *"do not assume these two are the only ones; that assumption is exactly what
produced this defect."* It was right, and the answer is not four edits: **`findings_of` is the one
seam all 13 findings-only pins route through, and its own docstring already promised that a blind
state cannot be served as a clean one.** It now refuses:

```python
verdict = gg.ungated_ground(repo_root, exemptions=exemptions)
assert not verdict.blind_sources, (…)
return list(verdict.findings)
```

Thirteen call sites get the guarantee at once, including ones nobody has written yet; a pin that
genuinely wants a blind tree reads `blind_sources` off the verdict, as the blindness pins already
do. Pinned live by
`TestTheArchivedReceiptsClass::test_the_findings_helper_refuses_a_blind_verdict` (a guard nobody
exercises is a hope with a filename), and mutation-proven in §4.

## 4. MUTATION PROOFS — four, declared before the run, diffed both ways

Every declared set was taken from `pytest --collect-only -q`, written to a file **before** the run,
and diffed in both directions by `scripts/mutation_proof.py`. Commands and declared-set files:
`/tmp/fixer44/{anchor,replacement,declared}_*.txt` — reproduce them from the anchors below.

| # | mutation | scope run | declared RED | observed |
|---|---|---|---|---|
| MP-1 | `ungated_ground`'s `scopes = _derive(repo_root)` → forced `_blind(...)` | the two real-tree node ids | 2 | **2 failed** — `PROOF HELD` (and, before the fix, `2 passed` = D2) |
| MP-2 | the conftest chain deleted from `_collector_input_paths` (→ `pass`) | **whole contract file** | 1 | `1 failed, 315 passed in 81.32s` — `PROOF HELD` |
| MP-3 | WB19's escaped-quote bug re-introduced into `wrong_builds.py` | **whole contract file** | 1 | `1 failed, 316 passed in 82.05s` — `PROOF HELD` |
| MP-4 | `findings_of`'s refusal disabled (`assert True or …`) | **whole contract file** | 1 | `1 failed, 317 passed in 82.63s` — `PROOF HELD` |

Supplementary leg proof for MP-3's *other* half (an anchor that no longer matches, so the mutation
cannot land and the CORRECT build is graded): corrupting `WB20`'s anchor reddens the same pin with
`cannot LAND — anchor matched 0 times`. Scoped to the one class, and **said so**: it is a leg
proof, not the primary.

Every run restored the tree byte-exact (`mutation_proof.py` asserts it and prints the md5). I also
took a content backup of all five writable files to `/tmp/fixer44/backup/` **before** the first
mutation, because the tree is uncommitted — standing law, and `mutation_proof.py`'s in-memory
restore does not survive a crash.

## 5. THE TWO DEFECTS THE AUDIT DID NOT LIST (deviation 2)

Both are in files the brief made writable, both are the same class as the items I was sent for, and
both were found by doing the work rather than by looking for them.

### 5.1 D14 — `collected_test_files`'s docstring was falsified by R10's own grant

The last sentence read: *"an inherited value that CHANGES inside one process moves what the
collector would answer **without moving this key**."* That is **exactly what
`test_an_inherited_pytest_addopts_moves_the_memo_key` proves FALSE** —
`_collector_input_fingerprint` hashes `PYTEST_ADDOPTS`, so the key moves with it. The paragraph has
been false since the grant landed, in the same file, one function above the bound I was sent to
rewrite. *A docstring teaching a hole its own contract has closed is the natural-language defect
inverted.* Rewritten, with the correction dated and attributed in place.

### 5.2 D15 — the attack harness reported **three phantom survivors** against a baseline of nothing

I ran `wrong_builds.py` **exactly as its own HOW TO RUN said to** (`./scripts/wrong_builds.py
--scratch …`) and got:

```
=== baseline (correct build) ===
REF => <no output>   [collected total: 0]
WB19_clean_render_over_claims                        <no output>    ❗SURVIVED
WB1_blindness_only_for_five_named_doors              <no output>    ❗SURVIVED
WB2_served_surface_ignores_findings                  <no output>    ❗SURVIVED

3 built · 0 killed · 3 survived · 0 NOT COMPARABLE (nothing measured)
```

**Cause:** the shebang is `#!/usr/bin/env python3`, the child is `sys.executable -m pytest`, and
`/usr/bin/python3` on this host has no pytest. Every child printed nothing on stdout; `run_contract`
**discards stderr**; `passed = failed = errors = 0`; the `if failed or errors` guard did not fire;
the baseline of **0** then made every build *comparable to zero*, failure-free, and therefore
**SURVIVED**.

**Why this is worse than D13 and why I fixed it rather than filing it.** D13 over-counted kills by
one. This manufactures **survivors** — the alarming direction. Over the full set the summary line
would have read **`21 survived`**, i.e. *"this contract catches nothing"*, entirely as an artifact
of a missing pytest, in the instrument this repository committed under finding #278 precisely so a
measurement could be re-run. It is `wrong_builds.py`'s own diagnosed failure mode (*"if step N
silently no-opped, would step N+1 still print something that reads as success?"*) one level above
where it was looking: **guard #2 compares each build's total to the baseline's, and nothing asked
whether the baseline was a measurement.**

Three repairs, all in the writable set:

1. **Baseline anti-vacuity** — a baseline that collected nothing is a hard `SystemExit` naming the
   likely cause and the interpreter the child would use.
2. **stderr is no longer discarded** — when nothing countable comes back, the tail carries
   `exit=<code>: <last stderr line>`.
3. **HOW TO RUN corrected** to `.venv/bin/python scripts/wrong_builds.py …`, with the shebang trap
   stated.

**Positive control** (the invocation that produced the phantoms, re-run against the fix):

```
=== baseline (correct build) ===
REF => exit=1: /usr/bin/python3: No module named pytest   [collected total: 0]
the baseline collected NOTHING, so every build below would compare 0 to 0 and read as a
SURVIVOR — the contract never ran. …
CONTROL_EXIT=1
```

## 6. D13 — the measurement the committed instrument could not obtain, obtained by it

### 6.1 The repair

`WB19_clean_render_over_claims`'s replacement was a triple-quoted literal ending in `\"`, which
Python resolves — so the installed text ended in **two** quotes and the patched module never
parsed. Re-derived independently before touching it: **WB19 is the only one of the 21 that does not
parse; all 21 anchors match exactly once.** The replacement is now a plain single-quoted string
with **no escape at all** (an escaped quote inside a triple-quoted literal is a defect generator,
not a style choice).

The summary now counts **three** outcomes, and a NOT-COMPARABLE run exits non-zero — *an unmeasured
build is not a killed one*. The docstring's exit-code contract was updated with it.

### 6.2 The measurement, from the committed harness

Scratch built per the docstring's `git archive` recipe (**never** `cp -a` of this worktree, #284),
with provenance asserted both ways:

```
PROVENANCE: /tmp/fixer44/refrepo/.git is a DIRECTORY (not a worktree file)
scratch gg.__file__ = /tmp/fixer44/refrepo/scripts/gated_ground.py
PROVENANCE OK: the scratch imports its OWN instrument
```

```
=== baseline (correct build) ===
REF => 317 passed in 88.50s (0:01:28)   [collected total: 317]
WB19_clean_render_over_claims             2 failed, 315 passed in 82.35s (0:01:22) killed
WB1_blindness_only_for_five_named_doors  60 failed, 257 passed in 84.54s (0:01:24) killed
WB2_served_surface_ignores_findings        4 failed, 313 passed in 81.80s (0:01:21) killed

3 built · 3 killed · 0 survived · 0 NOT COMPARABLE (nothing measured)
```

**Comparable (317 == 317) and killed.** WB1 and WB2 are the two that survived revision 5 at 171/171
and caused ruling R9 to be written; they are here as controls, and both die loudly. WB19 reddens
**2** pins against the audit's repaired-copy measurement of 1 — my contract adds pins the
over-claiming render also violates; the verdict (killed, comparable) is unchanged.

⚠ **A note on the coupling this introduces.** The new applicability pin makes the contract read
`wrong_builds.py`, so a scratch must now carry the harness as well as the instrument and the
contract. The HOW TO RUN recipe says so explicitly; without it the baseline fails for a reason that
has nothing to do with the tree.

### 6.3 The invariant, not just the fix

`TestTheCommittedWrongBuildsCanActuallyRun::test_every_committed_wrong_build_lands_exactly_once_and_parses`
— every declared build must LAND (anchor matches exactly once) and PARSE. Two failure modes, one
pin, because they are the same defect at different times: a replacement that is not valid Python
(cannot be graded) and an anchor that has rotted (cannot land, so the CORRECT build is graded and
reads as a survivor). No subprocess: string substitution plus `ast.parse`.

⚠ **The trade, stated so it is met deliberately:** this couples the contract to the harness's
anchors, so a refactor of `gated_ground.py` that moves an anchored line reddens it. That is the
intended direction — an attack harness whose anchors have rotted measures nothing while still
printing a census — and the repair is to re-anchor the build, never to delete the pin.

### 6.4 Gates

All run by me, at the frozen state. **Exit codes captured unpiped or via `${PIPESTATUS[0]}`.**

```
uv run pytest -q scripts/test_gated_ground.py   (1 of 2)  ->  318 passed in 82.38s   EXIT=0
uv run pytest -q scripts/test_gated_ground.py   (2 of 2)  ->  318 passed in 82.23s   EXIT=0
./scripts/typecheck.sh                                     ->  TYPECHECK_EXIT=0
    … lorerunes/lorescribe/loresigil/loremaster/skills/docs/eval OK
    Success: no issues found in 22 source files
    typecheck: scripts OK
    typecheck: shellcheck OK (7 tracked .sh)
uv run ruff check .                                        ->  All checks passed!    RUFF_EXIT=0
uv run pytest -q -n auto                                   ->  FULLSUITE_EXIT=0
    8711 passed, 36 skipped, 3 xfailed, 1 warning in 221.06s (0:03:41)
uv run pytest --collect-only -q                            ->  8750 tests collected
RECONCILES: 8711 + 36 + 3 = 8750  ✓
```

`scripts/` tree: **670** collected (`scripts/test_gated_ground.py` contributes **318**). The audit
measured 667/315 at `9377af5`; the delta is exactly my three new pins.

**⚠ One typecheck failure occurred and is disclosed rather than buried:** my first draft of the
conftest chain named its loop variable `directory`, colliding with the `os.walk` loop below it —
`scripts/gated_ground.py:872: error: Incompatible types in assignment` — renamed to `ancestor`, and
every gate above was re-run afterwards from scratch.

**RIDER — the guard's verdict on this repository, verbatim:**

```
gg.__file__   = /home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44/scripts/gated_ground.py
state         = GATED_GROUND
exit_code     = 0
is_clean      = True
findings      = 0
blind_sources = 0
--- render() verbatim ---
GATED GROUND — every tracked module is registered with the type gate, and every tracked test-shaped file is one the collector reaches.
```

## 7. D4 / D5 / D6 / R13 — and the sweep

### D4 — `scripts/typecheck.sh`, *"two of the entries are not members at all"*

Re-derived by me, not inherited:

```
workspace members : ['loremaster', 'lorerunes', 'lorescribe', 'loresigil']
MEMBERS roots     : lorerunes lorescribe loresigil loremaster skills docs/eval scripts
roots NOT members : ['skills', 'docs/eval', 'scripts'] -> 3
```

**Fixed by removing the free numeric, not by writing "three".** The sentence now points AT the
bullet list immediately below it, which enumerates exactly those entries — so the next entry cannot
falsify it. The one-line derivation command is in the comment.

### D5 — *"the house `sys.path.insert(…)` idiom — eleven sites use it"*

Re-derived, and **the audit's own numbers were right but unscoped**, which matters here:

| reading | count |
|---|---|
| files under `scripts/` with the idiom **verbatim** | **9** |
| files under `scripts/` with **any** `sys.path.insert` | **12** |
| repository-wide, verbatim | **10** |
| repository-wide, any | **31** |

Four values for one sentence, none of them 11. The paragraph is about `scripts/`, so the
`scripts/`-scoped pair is the honest reading — and the prose now carries **no** count, states its
scope, and gives both `git grep` one-liners.

### D6 — the addendum-F note this packet falsified

Every forward-looking claim in it is false at HEAD: `scripts` **is** in MEMBERS (`bd6fb73`), #188 is
**zero** (`4bf4399`), nobody needs to "pick up #188", and *"352 nodes"* has since read **667**,
**669** and **670** — **four values in two days**, two of them inside this fix wave. The original
text is **left standing** (a design note records what was believed when written) with a dated,
attributed correction block appended. The correction block was itself written with `669` in it and
falsified by my next pin — which is now the point it makes.

### R13 / D8 — the exemption prose

Reworded, machinery and its pins **kept** (operator-ruled). The served messages now end:

> *"…or ESCALATE — the exemption table is EMPTY and a row requires an operator ruling. Do not widen
> the receipts class to admit it."*

`MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM = "there is no exemption mechanism"` →
`MESSAGE_MUST_STATE_THE_EXEMPTION_TABLE_IS_EMPTY = "the exemption table is empty"`, still asserted
into **every** message on both axes. The `EXEMPTIONS` note and the two docstrings that repeated the
false sentence were corrected with it; under THE CONSUMER LAW the message is where an agent learns
this contract, and it was teaching that a parameter it can see does not exist.

### The retired-name sweep — BARE, anchor-free, **every hit individually**

`git grep -F` over the whole tracked tree, `REPORT-coldaudit-44-1.md` excluded as the source
document. **No wholesale verdicts.**

| pattern | file:line | verdict |
|---|---|---|
| `no exemption mechanism` | `docs/plans/v2/receipts/2026-07-29-packet44/REPORT-adversary-44-gatedground-3.md:621` | **archived receipt — LEAVE**, byte-faithful law |
| | `docs/plans/v2/receipts/2026-07-29-packet44/REPORT-builder-44-instrument-1.md:311` | **archived receipt — LEAVE** |
| | `docs/plans/v2/receipts/2026-07-29-packet44/REPORT-contract-44-gatedground-1-r5.md:200` | **archived receipt — LEAVE** |
| | `docs/plans/v2/receipts/2026-07-29-packet44/REPORT-design-sidecar-44-1.md:416` | **archived receipt — LEAVE** |
| | `scripts/test_gated_ground.py:210` | **INTENTIONAL** — quotes the retired string inside the ⚠ note explaining why it was retired |
| | `scripts/test_gated_ground.py:4262` | **INTENTIONAL** — same, in `TestTheRealRepositoryIsFullyGated`'s docstring |
| `MESSAGE_MUST_DENY` | `…/REPORT-adversary-44-gatedground-3.md:617` | **archived receipt — LEAVE** |
| | `…/REPORT-adversary-44-gatedground-3.md:621` | **archived receipt — LEAVE** |
| | `…/REPORT-contract-44-gatedground-1-r5.md:200` | **archived receipt — LEAVE** |
| `eleven sites` | `scripts/typecheck.sh:124` | **INTENTIONAL** — quotes the retired number in the correction that retires it |
| `two of the entries` | — | **zero hits** |
| `collector's file inputs` | — | **zero hits** |
| `and no other variable` | — | **zero hits** |
| `PYTEST_PLUGINS` | `scripts/gated_ground.py:89` | **INTENTIONAL** — labelled an *instance*, not the extent |
| | `REPORT-author-44-monotonic-1.md:737, 751, 982` | ⚠ **STALE, tracked, NOT MINE — §7.3** |
| `PY_IGNORE_IMPORTMISMATCH` | `scripts/gated_ground.py:90` | **INTENTIONAL** — same |
| | `REPORT-author-44-monotonic-1.md:738, 983` | ⚠ **STALE, tracked, NOT MINE — §7.3** |

**Zero live served surfaces still carry a retired string.**

## 7. SURFACED TO LEAD — questions, not verdicts

### 7.1 D7 — the brief contradicts itself, so I did not edit `INDEX.md`

The writable set says *"the prose sites D4–D7 name"*; **D7's site is `docs/plans/v2/INDEX.md:283`**,
and the NOT-YOURS list names `docs/plans/v2/INDEX.md` explicitly. Two readings, different actions,
so per scope law I took neither silently: **the specific prohibition beats the generic grant**, and
`038db75`'s own body already ruled *"INDEX.md is the lead's file"*. **Unedited. The exact edit:**

```
docs/plans/v2/INDEX.md:283
- 15. **Upstream report** of the mcp-builder TextContent serialization bug (docs/eval/2026-07-04-p8a-baseline.md:123).
+ 15. **Upstream report** of the mcp-builder TextContent serialization bug (docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md:123).
```

I verified the target resolves: `docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md`
exists at HEAD. **One line, and it is the plan of record's only dangling citation.** Say the word
and I will apply it, or apply it yourself in the wave commit.

### 7.2 The applicability pin's home

`TestTheCommittedWrongBuildsCanActuallyRun` lives in `scripts/test_gated_ground.py` because a **new
file** (`scripts/test_wrong_builds.py`) is outside my writable set — and `scripts/test_mutation_proof.py`
shows the per-tool contract is this directory's idiom. The pin is about *this* contract's own attack
harness, so the home is defensible, but **the idiomatic home is a dedicated file** and moving it
needs a scope grant. Your call.

### 7.3 `REPORT-author-44-monotonic-1.md` still teaches the retired bound

It is **tracked** at the repo root (the audit's D12) and states the memoisation residual in the
roster form this wave just retired, in four places. Under CLAUDE.md it should be `git mv`'d into
`docs/plans/v2/receipts/2026-07-29-packet44/` **with a one-line header saying the bound it
describes was superseded on 2026-07-30** — archiving is not free of judgement, and a silently
preserved wrong claim is the failure mode that rule warns about. Peer-authored and outside my set;
I did not touch it.

### 7.4 Residuals I did NOT close, and did not silently drop

* **R-5 / E6** — the three pytest environment doors. My rewrite reframes them as *instances of a
  complement*; **it does not close them.** Closing needs the ruling the audit asked for.
* **R-1, R-2, R-3, R-4, R-6, R-7** — untouched, out of my items, still open exactly as the audit
  left them.
* **R-8** — closed as part of D2 (the headline invariant now exercises the shipped default).
* **D3 / D11 / D12** — ruled elsewhere (R14 / R12 / lead's), not mine, not touched.
* **D9** — the inline `# mypy: ignore-errors` door: still open, still zero instances in the tree,
  still no STATED BOUND naming it. Needs a ruling; I did not invent one.

## 8. FREEZE — for `coldaudit-44-2`

```
HEAD                                    9377af5   (unchanged; I created no commits)
branch                                  pkt44/ungated-ground
git status --porcelain                  M docs/design/2026-07-25-floor-calibration-addendum-F.md
                                        M scripts/gated_ground.py
                                        M scripts/test_gated_ground.py
                                        M scripts/typecheck.sh
                                        M scripts/wrong_builds.py
                                        ?? REPORT-coldaudit-44-1.md   (handed to me, untracked)

md5  scripts/gated_ground.py            2d2f91276278cf4d80d031ae37c54e52   (1525 lines)
md5  scripts/test_gated_ground.py       379f4336063e2c30e876372c23bc7f3e   (4290 lines)
md5  scripts/wrong_builds.py            c5bc9744e109471b473cfc823c885372   ( 480 lines)
md5  scripts/typecheck.sh               04a3bc8bbf2b54d2290ce57e44726ffa   ( 201 lines)
md5  docs/design/2026-07-25-floor-calibration-addendum-F.md
                                        02ed4e50800185c8f52c6f85d5e88d5e

collected: whole repo 8750 · scripts/ 670 · scripts/test_gated_ground.py 318
full suite 8711 passed / 36 skipped / 3 xfailed  ->  8750, reconciles
```

⚠ **The addendum-F md5 above is later than the one in §6.4's run**: I corrected its own numbers
(669 → 670, 317 → 318) after the last pin landed. The gates were re-run at the final state; the
markdown file is not executable and is in no gate's scope, which is exactly why its numbers rot.

## 9. INSTRUMENTS (brief-base §1)

Nothing I built is lost. Disposition of each:

* **`scripts/mutation_proof.py`** — this repo's, committed, used unmodified. The four proofs are
  reproducible from the anchors quoted in §4.
* **`scripts/wrong_builds.py`** — this repo's, committed, **improved in place** (§5.2, §6.1).
* **`probe_memo_stale.py`** — `coldaudit-44-1`'s, pasted verbatim in its §9.1. I did not
  re-transcribe it: I extracted it fence-to-fence from that report with the snippet below and ran
  the bytes. **It is not committed anywhere** — it lives only inside a report that is itself
  untracked at the repo root, which is the exact perversity brief-base §1 warns about. **Recommend
  the lead commit it as `scripts/probe_memo_stale.py` when archiving the audit**, or the receipt
  behind this packet's blocker becomes unreproducible the moment that file moves.

```python
# fixer-44-audit-1 — extract an instrument from a report by fence, never by transcription
from pathlib import Path
lines = Path('REPORT-coldaudit-44-1.md').read_text().splitlines(keepends=True)
start = next(i for i, l in enumerate(lines) if l.startswith('### 9.1 `probe_memo_stale.py`'))
opened = next(i for i in range(start, len(lines)) if lines[i].startswith('```python'))
closed = next(i for i in range(opened + 1, len(lines)) if lines[i].rstrip() == '```')
Path('/tmp/fixer44/probe_memo_stale.py').write_text(''.join(lines[opened + 1:closed]))
```

* **The scratch recipe** for `wrong_builds.py` (§6.2) is the harness's own committed docstring, now
  corrected in two ways it was wrong (the harness must be copied in; the venv interpreter must be
  used). Nothing bespoke was invented.

---

*Ordering note for the record: the D2 BEFORE proof (§3.2) was run against the unmodified
assertions, before any contract edit — a declared-RED set transcribed after watching the output is
the tautology in a new costume, and this one was written to a file first.*
