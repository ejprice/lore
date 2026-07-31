brief-base v9 read
brief project v7 read
brief pkt44 v2 read

# REPORT-coldaudit-44-1 — COLD REFUTE AUDIT of packet 44 ("UNGATED GROUND")

Measured 2026-07-30 in worktree `/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44`,
branch `pkt44/ungated-ground`, from **HEAD `2c741ee`** — which advanced to **`9377af5`** mid-audit
in a commit touching **only `REPORT-author-44-monotonic-1.md`**. Every artifact audited here is
byte-identical across that range (§1), so **every finding holds at both shas**. Every claim below
is dated and sha-scoped at the point it is made; nothing here is present-tense about a future tree.

---

## SUMMARY BLOCK

- `brief-base v9 read` · `brief project v7 read` · `brief pkt44 v2 read`
- **state: done** — read-only throughout; I fixed nothing and mutated no tracked content.
- **VERDICT: NO-GO**, on two blockers, both inside the class this packet exists to close:
  **D1** a CONSTRUCTED, byte-identical **false clear** from R10's memo + a **STATED BOUND that is
  false as written**; **D2** the headline invariant `test_no_committed_python_is_ungated_on_either_axis`
  **passes on a BLIND verdict**. Both are one-wave fixes. Everything else is fix-wave or routing.
- deviations: (1) lore's index is blind to this worktree (#125) — **every structure query fell back
  to `git grep`/`git ls-files`, said out loud here**; (2) my first path-forgery probe used a
  substring predicate and produced a FALSE POSITIVE — self-caught and corrected in §5.4; (3) I
  delegated two read-only fan-outs (residual extraction, prose sweep) and **re-derived every
  headline number they returned myself** — §4 receipts are mine, not theirs.
- `Packages considered:` **targeted semantic wrong-build harness** — evaluated `mutmut` /
  `cosmic-ray` / `mutpy`; READ: `importlib.util.find_spec` for all three → **not installed**, and
  absent from `uv.lock` + `pyproject.toml`; READ the in-repo `scripts/wrong_builds.py` source
  (`apply` / `run_contract` / `main`), which already implements this capability **plus two guards
  a generic operator-mutation tool does not have** (anchor-matches-exactly-once; collected-total
  comparability). Verdict **`keep_with_trigger`** — I imported and extended its registry rather
  than forking or installing. Trigger: the day an audit needs random operator-level mutation
  across a whole module rather than named semantic edits, evaluate `mutmut` and request install
  authorization.
- decisions-needed: **6 for the operator** — §8 (D1's fix scope · the exemption-mechanism prose
  ruling · whether the history rewrite is ledgered as well as reported · S2's in-image landing
  hazard · the two tracked root reports · the peer-owned falsified docstring frozen by R8).
  **D10 closed itself at `9377af5` while I measured** and does not count toward the NO-GO.
- receipt POINTERS: gates §2 · claim-by-claim refutation §3 · confirmed defects §4 ·
  attacks that FAILED §5 · wrong-build census §6 · residuals §7 · instruments verbatim §9.

---

## 0. CAPABILITY CHECK (brief-base §4 — first thing in the report)

| demanded by the brief | what I actually had | what I did |
|---|---|---|
| `lore_comms` register / `brief_get` / `drain` | **PRESENT** (via `ToolSearch`) | registered `coldaudit-44-1`, read `project` v7 + `pkt44` v2, drained (**no unread messages**). Finding **#287** (three agents found these ABSENT) **did NOT reproduce for me** — report that as a data point, not a closure. |
| lore index for code-structure questions | **BLIND to this worktree (#125)** | `git grep` / `git ls-files` throughout, declared per project law §3(a)/(c). I filed no friction row: #125 is already ledgered and I routed nowhere silently. |
| re-run the gates myself | full toolchain present | §2 — all re-run, none inherited. |
| never `cp -a` this worktree (#284) | — | both scratch repos built from `git archive HEAD` + fresh `git init`; **`.git` asserted to be a DIRECTORY** in each; provenance asserted in-process (§6). |

Nothing in the brief was unmeetable.

---

## 1. THE FROZEN TARGET — verified; HEAD moved mid-audit, every audited artifact did not

At the START of my run:

```
$ git rev-parse HEAD                            2c741ee3029bdb1a84cbeeba5e35a167467415bf   ✓
$ md5sum scripts/gated_ground.py                ce80544260f45ece25b939437581ca2e            ✓
$ md5sum scripts/test_gated_ground.py           7fb8f86f68dad8005f6734278a379001            ✓
$ git status --porcelain
 M REPORT-author-44-monotonic-1.md      <-- UNCOMMITTED, 66 lines. See D10.
```

⚠ **HEAD MOVED DURING MY RUN — declared, and bounded by measurement rather than by assurance.**
At the end of my run:

```
$ git rev-parse HEAD                            9377af51f8da239ac7a5ccdbdbed3d9a57865956
$ git log --oneline 2c741ee..HEAD
  9377af5 docs(44): ground-truth the re-sent grant, disclose every history rewrite, freeze
$ git diff --stat 2c741ee..HEAD
  REPORT-author-44-monotonic-1.md | 131 ++++++++++++++++++++++  (1 file changed)
$ md5sum scripts/gated_ground.py                ce80544260f45ece25b939437581ca2e            ✓ unchanged
$ md5sum scripts/test_gated_ground.py           7fb8f86f68dad8005f6734278a379001            ✓ unchanged
```

I re-checked **every** artifact this audit touches — `scripts/gated_ground.py`,
`scripts/test_gated_ground.py`, `scripts/typecheck.sh`, `pyproject.toml`, `scripts/wrong_builds.py`,
`scripts/test_forgery_door_sweep.py`, `docs/plans/v2/INDEX.md`,
`docs/design/2026-07-25-floor-calibration-addendum-F.md` — **all byte-identical across
`2c741ee..9377af5`.** The single new commit adds only the author's report addendum. **Every finding
below therefore holds at BOTH shas**, and D10 is the one it resolves (see D10).

`.git` here is a **FILE** (`ASCII text`, 64 bytes) — the #284 landmine, respected: neither scratch
repository was a copy of this worktree.

---

## 2. THE GATES — RE-RUN BY ME, NOT INHERITED

| gate | my command | result |
|---|---|---|
| types | `./scripts/typecheck.sh` (exit captured) | **`TYPECHECK_EXIT=0`** — 7 legs OK + `shellcheck OK (7 tracked .sh)` |
| lint | `uv run ruff check .` | **`RUFF_EXIT=0`** — `All checks passed!` |
| full suite | `uv run pytest -q -n auto` | **`8708 passed, 36 skipped, 3 xfailed, 1 warning in 386.00s`**, exit 0 |
| reconciliation | `uv run pytest --collect-only -q` | **8747 collected** = 8708 + 36 + 3 ✓ |
| instrument ×2 | `uv run pytest -q scripts/test_gated_ground.py -p no:randomly` | run 1 **315 passed in 80.80s** (`RUN1_EXIT=0`) · run 2 **315 passed in 80.95s** (`RUN2_EXIT=0`) — deterministic |
| the guard, live | `ungated_ground(Path('.'))` | `state=GATED_GROUND · is_clean=True · exit=0 · findings=0 · blind_sources=0` |

**There are 0 failing tests unrelated to the present scope.**

Fate census over **293** tracked `.py` (derived, not quoted):
`types`: 272 COVERED + 21 EXEMPT_ARCHIVED_RECEIPTS · `execution`: 152 COVERED + 141 NOT_APPLICABLE.

---

## 3. THE WAVE'S SEVEN CLAIMS — each attacked, each re-derived

| # | claim | my independent derivation | verdict |
|---|---|---|---|
| 1 | `docs/eval` type-gated; six p8a relics archived; two `.json` STAY because the smoke reads them via `Path(__file__).with_name()` | `git ls-files docs/eval` → exactly 4 (2 `.json` + smoke + suite). Archive holds 6 relics + README. **`smoke_p8b.py` `PRE_DDL_RECEIPT_PATH` and `LATENCY_BASELINE_PATH` both use `Path(__file__).with_name(...)`** — the stated reason is TRUE, at two call sites. `MYPYPATH=docs/eval mypy docs/eval` → 0 errors, 2 files. | **CONFIRMED** |
| 2 | `skills/lore-deploy/{scripts,tests}` joined `testpaths` (+117) | `pytest --collect-only -q skills/lore-deploy/{scripts,tests}` → **117 tests collected** | **CONFIRMED (exact)** |
| 3 | shellcheck leg DERIVED from `git ls-files '*.sh'`, 4 findings → 0 | `git ls-files '*.sh'` → **7**; `uv run shellcheck <those 7>` → **exit 0, no output**. Leg is derived (`while read -d '' … < <(git ls-files -z '*.sh')`) with an anti-vacuity abort. I re-measured the comment's own self-correction: bare `shellcheck` **prints usage and exits 3** — the comment is right and correctly flags itself as a dependency-behaviour claim. | **CONFIRMED** |
| 4 | #188 closed: `scripts/` 24 → 0, plain typecheck root under `MYPYPATH=scripts` | `MYPYPATH=scripts uv run mypy scripts` → **`Success: no issues found in 22 source files`**. `MEMBERS` at `typecheck.sh` contains `scripts`. | **CONFIRMED** |
| 5 | `loresigil` discriminators → `Final[Literal[...]]`, cast deleted | three `Final[Literal[...]]` constants in `loresigil/loresigil/factory.py`; **no `cast(` remains in that file** | **CONFIRMED** |
| 6 | the instrument: per-axis, LEG B empirical, monotonicity **structural**, memo keyed with `PYTEST_ADDOPTS` | Structural claim **SURVIVED my attack (§5.1)**. LEG B is empirical (subprocess `--collect-only`) ✓. **The memo claim is where the wave breaks — see D1.** | **PARTLY REFUTED** |
| 7 | prose sweeps for #282 and for claims this wave falsified | **REFUTED — the sweep is incomplete.** #282 itself is discharged, but **six served-or-taught sites falsified by this wave survive at HEAD** — D3 (a collected test's docstring *and* its failure message), D4 + D5 (two free numerics in `typecheck.sh`'s own teaching comments), D6 (a note this packet WROTE, falsified by this packet), D7 (the one dangling citation the archive move created), D8 (a served failure message denying a shipped mechanism). **Four of the six were written or last touched inside `7bd9b4e..HEAD`.** | **REFUTED** |

---

## 4. CONFIRMED DEFECTS

Numbered by severity. Every one carries a receipt I produced.

**Read the NO-GO correctly.** This wave is substantially sound: five of its seven claims verified
exactly, every gate is green under my own hands, R9's central structural claim survived a
deliberate attack (§5.1), **11 of the 12 wrong builds I invented to defeat it were killed** (§6.1),
and the author's own 21 re-run **20 killed / 1 equivalent-survivor** — including WB1 and WB2, the
two that survived revision 5 at 171/171 and caused ruling R9 to be written (§6.2). The NO-GO is not
a rejection of the instrument — it is a refusal to let two members of the class the instrument
EXISTS to close ship inside it. **What a GO requires is small and specific:**

1. **D1** — add the `repo_root`→testpath `conftest.py` chain to `_collector_input_paths`, and
   rewrite the `collector-memoisation` bound to state what is genuinely uncovered rather than
   enumerating three environment variables. (One function, one bound, one new pin.)
2. **D2** — assert on `ungated_ground(...).is_clean` rather than on `.findings`, at both real-tree
   call sites. (One line each; also closes R-8.)
3. **D4 / D5 / D6 / D7** — four falsified prose/numeric sites, three of them written by this packet.
   Mechanical edits.
4. **D13** — one character in `scripts/wrong_builds.py` (a build that has never parsed, therefore
   never measured), plus a summary line that stops counting NOT-COMPARABLE runs as kills. I already
   obtained the missing measurement and it is **GREEN for the wave** — the fix is to make the
   committed instrument able to obtain it too.

D3, D8, D9, D11 and D12 need operator routing (§8) rather than a builder. D10 closed itself.
**A contract revision goes to the adversary before a builder** — including this one, which is a fix
wave, and this repo's receipts say a fix wave is exactly where an adversary is cheapest.

### D1 — BLOCKER. R10's memo serves a **byte-identical healthy render** on a silenced tree, and the `collector-memoisation` STATED BOUND is FALSE as written

**The bound** (`scripts/gated_ground.py::STATED_BOUNDS`, identifier `collector-memoisation`):

> *"The memo's fingerprint covers **the collector's file inputs** and PYTEST_ADDOPTS, and no other
> variable."* … *"MEASURED over the installed pytest's own source, the residual is **three further
> variables** it reads … PYTEST_PLUGINS, PYTEST_DISABLE_PLUGIN_AUTOLOAD and PY_IGNORE_IMPORTMISMATCH"*

**The measurement.** `_collector_input_paths` hashes exactly three populations: `repo_root`'s
manifest / `conftest.py` / shadow candidates; every **tracked** `.py`; every `.py` **under a
testpath**. An **untracked `conftest.py` in a directory that is an ANCESTOR of a testpath** is in
none of the three — and pytest loads it, because conftest loading walks rootdir → target dir,
which is a *different mechanism* from `locate_config`, the only one the docstring reasons about.

Instrument: §9.1 (`probe_memo_stale.py`), run against a `tmp_path` repo, `.git` asserted to be a
DIRECTORY. Output:

```
gg.__file__ = /home/ejprice/.../worktrees/pkt44/scripts/gated_ground.py
A. healthy, cold memo (warms it)                       state=GATED_GROUND   exit=0 findings=0 blind=0
B. NEG CTRL: unkeyed silencer + KEYED manifest change  state=UNGATED_GROUND exit=1 findings=1 blind=0
C. healthy again, cold memo (warms it)                 state=GATED_GROUND   exit=0 findings=0 blind=0
D. unkeyed silencer ONLY, warm memo                    state=GATED_GROUND   exit=0 findings=0 blind=0
E. POS CTRL: same tree, memo cleared                   state=UNGATED_GROUND exit=1 findings=1 blind=0

bytes identical C vs D: True  <-- True == FALSE CLEAR
NEG CTRL passes (keyed change forced a re-run): True
POS CTRL passes (the guard can see the mutation): True
```

Separately measured on the same fixture: after adding the untracked ancestor conftest, the
fingerprint **does not move** (`_collector_input_fingerprint` before == after) — which is the
mechanism behind row D.

⚠ **These are the bytes of §9.1 as pasted, re-extracted FROM THIS REPORT and re-run** — not a
transcription of an earlier session's output.

The positive control proves the mutation is real and the guard **can** see it. The negative
control proves the memo is not merely always-stale — the key works for what it covers. Between
them, the only explanation is the one stated: a collector file input outside the key.

**Why this is a STOP and not a nit.** `_COLLECTOR_MEMO`'s own docstring says *"a stale HEALTHY
answer is a false clear — **the one failure this instrument may not have**."* Repo law: *"LOST:
one false clear — a wrong state that renders identically to the correct one. That is a **STOP
naming a gap in the derived failure set**, never a quiet fix."*

**And the guard for this bound cannot see it.** `test_the_memoisation_bound_never_names_a_variable_the_key_already_covers`
derives **environment variable names** from the instrument's AST and checks none appear in the
re-open trigger. It is keyed on a **name-list of env vars** and is therefore structurally blind to
a **file**-shaped hole. That is this repo's own instrument-lesson shape, one level up: the bound
enumerates its forbidden set (three env vars) instead of deriving its safe set.

**Live shapes in THIS tree** (ancestors of a testpath that are not themselves testpaths):
`lorerunes/`, `lorescribe/`, `loresigil/`, `loremaster/`, `docs/`, `skills/`, `skills/lore-deploy/`.
An untracked `loremaster/conftest.py` is an entirely ordinary thing for an honest engineer to add
— which is the declared threat model.

**Exploitability, stated precisely so nobody over- or under-reads this:** the memo lives for ONE
process, so the stale serve needs the unkeyed file to appear **during** a run. On a cold memo the
guard reports the finding correctly. So the *false clear* is constructible and measured; the
*current gate exposure* is narrow. **The false BOUND is unconditional** — it is served to every
future reader as fact and it is not true.

**Closing edit (one function):** add the conftest chain — for each testpath, every `conftest.py`
from `repo_root` down to it — to `_collector_input_paths`, and rewrite the bound to name what is
genuinely uncovered rather than enumerating three env vars.

### D2 — BLOCKER. The headline invariant passes on a **BLIND** verdict

`TestTheRealRepositoryIsFullyGated` — docstring: *"Everything above proves this assertion can
discriminate; **this is the assertion**."* Its body:

```python
findings = findings_of(REPO_ROOT, exemptions=())
assert not findings, ...
```

and `findings_of` returns `list(gg.ungated_ground(...).findings)` — **discarding `blind_sources`**.
A BLIND verdict has `findings == ()`:

```
blind verdict -> findings = [] | state = BLIND | exit = 2
the headline assertion `assert not findings` -> PASSES on a blind verdict
```

`findings_of`'s own docstring is the sharpest evidence: *"`ungated_ground` returns a `Verdict`,
not a list, **precisely so a blind state cannot be served as a clean one** … This helper keeps
that design change from obscuring the pins that are about findings."* The helper is exactly what
re-introduces the obscuring, at the one pin the class calls *the* assertion. That is a docstring
promising a property its use site defeats — this repo's false-gate shape.

**And it is not one pin — it is BOTH of them.** I enumerated every real-tree call site:

```
$ grep -n 'ungated_ground(REPO_ROOT' scripts/test_gated_ground.py
1459:        with_none = gg.ungated_ground(REPO_ROOT, exemptions=())      -> assert not with_none.findings
     (+ TestTheRealRepositoryIsFullyGated)                               -> assert not findings
$ grep -n 'REPO_ROOT' scripts/test_gated_ground.py | grep -i 'blind\|is_clean'
     (no matches)
```

**No pin anywhere asserts that this repository's verdict is not BLIND, or that it `is_clean`.**
Both `ungated_ground(REPO_ROOT)` sites read `.findings` and discard `.blind_sources`, and both are
satisfied by BLIND.

**Mitigation, measured so severity is not guessed — and it is INCIDENTAL, not designed.** The
*suite* is loud: with `git` made unusable (a `PATH` shim exiting 127 — the in-image shape) I
measured **`186 failed, 82 passed, 47 errors in 24.15s`**. But the reason is that `gg.classify(REPO_ROOT, …)`
at two other pins **raises** rather than returning — and those two pins are about the fate census,
not about blindness. Blindness on the real tree is caught **as a side effect of an exception nobody
catches**, by pins written for a different purpose. Remove or refactor either of them and the
headline invariant goes green on a guard that saw nothing.

So blindness does not ship green today, but the property is unowned. The fix is one line: assert on
`ungated_ground(...).is_clean` (or `not verdict.blind_sources`) instead of on findings — which also
closes R-8, since the same edit can pass the shipped `EXEMPTIONS` default.

### D3 — a **collected** test's docstring **and its served assertion message** teach a scope this packet retired and a count it calls fabricated

`scripts/test_forgery_door_sweep.py`, `TestThisInstrumentIsTYPECHECKED`:

> `"""⛔ ``scripts/`` is OUTSIDE ``scripts/typecheck.sh`` (#188 measured 41 mypy errors there), so
> nothing in the canonical gate reads these two files.`
> `Rather than add ``scripts`` to the gate (which would import 41 unrelated errors and turn it red) …`

and the failure message it serves: `"(scripts/ is outside scripts/typecheck.sh MEMBERS)"`.

**True at HEAD:** `MEMBERS=(… scripts)` since `bd6fb73` — *in this packet* — and
`MYPYPATH=scripts uv run mypy scripts` → **0 errors, 22 files**. Adding it did not turn the gate
red. And "41" is a number **this packet's own `scripts/typecheck.sh` comment calls a phantom**:
*"#188's own inherited '41' was a THIRD number, measured under neither shape."*

⚠ **Ownership:** ruling **R8** forbade this wave from touching that file (peer session). So this is
a *known, ruled-untouched* residual — but it is in the tree at HEAD, it is collected, and it is
the exact defect class the packet exists to close. It needs a routing decision, not silence (§8).

### D4 — `scripts/typecheck.sh` — "**two** of the entries are not members at all"; derived **THREE**

```
workspace members : ['loremaster', 'lorerunes', 'lorescribe', 'loresigil']
MEMBERS roots     : lorerunes lorescribe loresigil loremaster skills docs/eval scripts
roots NOT members : ['skills', 'docs/eval', 'scripts']  -> 3
```
The bullet list **directly beneath that sentence enumerates all three**. True at `2bc7e97`;
falsified by the **same packet's** `bd6fb73`, which added `scripts` and updated the list but not
the count. A free numeric in taught prose, restated rather than derived.

### D5 — `scripts/typecheck.sh` — "the house `sys.path.insert(...)` idiom — **eleven sites** use it"

Derived at HEAD: **9** files carry the verbatim idiom; **12** files carry any `sys.path.insert`.
Neither is 11. Falsified by this packet's own additions (`test_gated_ground.py`,
`test_forgery_door_sweep.py`).

### D6 — a note **this packet wrote** is falsified **by this packet**

`docs/design/2026-07-25-floor-calibration-addendum-F.md` (added at `8015d22`, dated 2026-07-29):

> *"⚠ The raise's OTHER half is still open …: **`scripts/` remains outside `scripts/typecheck.sh`
> MEMBERS** (#188 …). The **execution** axis is closed; the **type** axis is not."*
> *"Whoever picks up #188 should re-measure in the LEG shape before sizing it; 24 is a different
> job from 45."*
> *"re-measured in packet 44, a bare gated run collects **352** nodes from that tree"*

At HEAD, `bd6fb73` + `4bf4399` (same packet, same day, later) closed **both** axes and took #188
to **zero**; nobody needs to "pick up #188"; and `pytest --collect-only -q scripts` → **667**
(352 + 315 = 667 exactly — the instrument's own pins are the delta).

### D7 — `docs/plans/v2/INDEX.md` carries the **one dangling citation** the archive move created

`INDEX.md:283` cites `docs/eval/2026-07-04-p8a-baseline.md:123`. That file is now at
`docs/plans/v2/receipts/2026-07-04-p8a/`. Commit `038db75`'s **subject** reads *"repoint **every**
LIVE citation of the six archived relics — bare sweep, per-hit verdict"*; its **body** admits the
miss (*"FLAGGED, NOT EDITED … INDEX.md is the lead's file"*). Six commits later it still dangles.
Honest in the body, over-claiming in the subject — and `INDEX.md` is the plan of record.

I swept all six relic names bare and anchor-free and gave **every** hit an individual verdict
(§7.2). One live dangling; two archived-file lines carry old paths and are protected by
byte-faithful law; every other live citation was correctly repointed.

### D8 — the served failure message **denies a mechanism the module ships, exports and pins**

`gated_ground.py::_types_message` / `::_execution_message`, the only prose a consumer of a failing
gate reads:

> *"or ESCALATE — **there is no exemption mechanism, deliberately**."*

pinned as a required substring by `MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM`. Probed at HEAD, the
same module ships:

```
Exemption class      : True            Fate.EXEMPT_TABLE : 'exempt by a pinned row'
EXEMPTIONS           : ()              bound             : 'exemption-scope'
classify signature   : (repo_root, *, exemptions: Sequence[Exemption] = ())
ungated_ground sig   : (repo_root, *, exemptions: Sequence[Exemption] = ())
```

plus `InvalidExemption`, `_exempting_row`, seven validation branches, and the module's own line
*"A row here is a design decision requiring a ruling"* — which asserts the mechanism EXISTS. What
F1 did was **empty the table**, which the contract itself says (*"F1 emptied…"*). The operational
advice is right; the sentence about the code is false, and a pin holds it in place.

Under THE CONSUMER LAW this matters more than usual: an agent reading that message learns the
contract from it, and would conclude the public `exemptions=` parameter does not exist.

### D9 — LEG A: an inline `# mypy: ignore-errors` silences a **registered** file, unmodelled and **unstated**

`unmodelled_mypy_configuration` states the exact property it defends — *"any setting that makes a
REGISTERED file unchecked IN FACT would leave this guard certifying a tree it cannot see"* — and
closes the `pyproject.toml` form with five pins (including `ignore_errors` globally and per
override). The **per-file inline** form is neither closed nor named in any STATED BOUND.

Measured, with a positive control:

```
plain.py    (def f(x: int) -> str: return x)      -> error: Incompatible return value type  [return-value]
silenced.py (same defect + '# mypy: ignore-errors') -> Success: no issues found in 1 source file
LEG A: is_under('scripts/plain.py','scripts') == is_under('scripts/silenced.py','scripts') == True
```

Identical fate, identical bytes. **Zero such directives exist in the tree today** (`git grep -n
"^# mypy:" -- '*.py'` → empty), so this is not a live false clear — it is an open door with no
bound on it, in the same silencing class the guard decided was its business.

### D10 — ✅ **RESOLVED DURING THIS AUDIT** (at `9377af5`). Recorded because the verification is independent evidence, not because the defect stands

`REPORT-author-44-monotonic-1.md` is `M` at HEAD — **+66 lines**, containing:

1. `## ⚠ E1 AND E4 WERE ALREADY DONE WHEN THE GRANT WAS RE-SENT` — a lead artifact-verification
   that was **stale**.
2. `## PROCESS STOP — I REWROTE SHARED HISTORY, AND HERE IS THE COMPLETE LIST` — **four** history
   mutations, of which the lead's own account reached one.

I verified the disclosure's substance independently:

```
$ git merge-base --is-ancestor 00cf487 HEAD      -> NO — dropped from history
$ git log --oneline -1 00cf487
  00cf487 feat(gates): monotonicity by CONSTRUCTION (R9) + a pinned collector cache (R10)   [the LEAD's commit]
$ git show --stat 00cf487   -> touches exactly scripts/gated_ground.py + scripts/test_gated_ground.py
$ git diff --stat 00cf487 7ad1b0a -- scripts/gated_ground.py scripts/test_gated_ground.py
  (empty)   <-- CONTENT PRESERVED; the no-loss claim RE-DERIVES TRUE, and over every file 00cf487 touched
```

Also NOT ancestors of HEAD: `71fdebf`, `fd19f2e`, `09b1873`, `4120ccb`, `9c0f2da`.

So: **no content was lost** — a commit MESSAGE and a SHA were destroyed, not code — and my
re-derivation independently reproduces the author's own no-loss claim, including the harder leg
(over **every** file `00cf487` touched, not merely the two named).

**Resolution, mid-audit.** While I was measuring, `9377af5` committed that addendum (131 lines,
additive, no amend, no reset) carrying both `## ⚠ E1 AND E4 WERE ALREADY DONE…` and
`## PROCESS STOP — I REWROTE SHARED HISTORY…`. The disclosure now has a durable address, so the
CLAUDE.md violation (*"the working tree is never the ONLY copy of finished work"*) **no longer
holds**. **D10 is CLOSED and does not count toward the NO-GO.**

What survives D10 is the *verification*, which is worth keeping: the four rewrites are real, one of
them dropped the lead's commit object, and the no-loss claim **re-derives TRUE** under an
independent instrument. §8.3 keeps only the ledger question.

### D11 — the in-image conformance run will now collect `scripts/`, where the guard goes blind (S2, unclosed and unstated)

`Containerfile` copies `pyproject.toml`, `uv.lock` and the four workspace members — **neither
`scripts/` nor `.git`**. `conformance_run.sh` mounts the whole repo `:ro` and runs
`pytest -o cache_dir=/tmp/ptc -n auto -q --no-header` **with no path arguments**, so it collects
`testpaths` from the mounted manifest — which packet 44 extended to include `scripts`. Its own
header names the condition: *"git-not-in-image"*.

Measured shape under an unusable git: **`186 failed, 82 passed, 47 errors`**. Loud, not silent —
but this is a new, unstated consequence of adding `scripts` to `testpaths`, raised by
adversary-2 (S1/S2) with **no closure claim anywhere**.

### D12 — two **tracked** `REPORT-*.md` at the repo root

`git ls-files 'REPORT-*.md'` → `REPORT-author-44-monotonic-1.md`, `REPORT-builder-forgery-sites.md`.
CLAUDE.md requires the root to be clear of these before an image build, cleared by `git mv` into
`docs/plans/v2/receipts/<date>-<packet>/`. The second additionally teaches the falsified
`MEMBERS=(lorerunes lorescribe loresigil loremaster skills)` array and *"#188 measured 41 mypy
errors"* — and it is the report that **ordered its own successor's deletion**: *"clear #188's 41
errors, then append `scripts` to `MEMBERS` … **and delete `TestThisInstrumentIsTYPECHECKED` in the
same commit rather than keeping both**."* `bd6fb73` did the first half. D3 is the second half,
undone.

### D13 — the committed attack harness has a build that **has never measured anything**, and the summary counts it as killed

`scripts/wrong_builds.py::WB19_clean_render_over_claims` — committed at `1430aa5` under ruling E4
/ finding #278 — carries an escaping bug. Its replacement is written with a backslash-escaped
quote inside a triple-quoted literal, so the text it actually installs ends with **two** quotes:

```
replacement repr: '                return "GATED GROUND: every committed .py is registered on both axes.""'
patched source is INVALID PYTHON -> unterminated string literal (detected at line 1201)
   offending line: return "GATED GROUND: every committed .py is registered on both axes.""
```
(Contrast: `WB1` and `WB2` both `ast.parse` cleanly.)

The patched module never parses, so the run collects **1 error in 0.20s** and measures nothing.
The harness's guard #2 **fires correctly** on the per-build line (`⚠ NOT COMPARABLE (1 != 315)`) —
but its summary arithmetic is `len(names) - len(survivors)`, which folds the unmeasured run into
the kill count and prints **`21 built · 20 killed · 1 survived`**. A reader who takes the summary
line at its word over-counts coverage by one — in the instrument whose own docstring exists to stop
exactly that over-reading (*"A mutation that breaks the syntax collects nothing, exits 1, and prints
`1 error` — which a count of failures reads as 'killed' when in truth nothing was measured"*). The
harness diagnosed this failure mode in prose and then shipped an instance of it.

**Why this one matters more than an average build:** WB19 is the DUAL that ruling R9 was written
to close — the pkt44 brief names it verbatim (*"a build serving findings=1 with is_clean=True,
exit_code=0 and `render()=="GATED GROUND: every committed .py is registered on both axes."` passes
171/171"*). Its kill was the headline evidence for R9's over-claim leg, and it was never obtained.

**I obtained it.** Repairing the one character (§9.4) and re-running:

```
REF => 315 passed in 80.72s   [collected total: 315]
WB19fixed_clean_render_over_claims    1 failed, 314 passed in 80.58s   killed
1 built · 1 killed · 0 survived
```

**Comparable (315 == 315), and killed.** So the property holds and the contract does catch an
over-claiming clean render — **the wave's claim is true; only its evidence was missing.** Fix: one
character in `wrong_builds.py`, and a summary line that reports NOT-COMPARABLE runs as their own
category rather than as kills.

---

## 5. ATTACKS THAT FAILED TO REFUTE — the wave's real wins

A refute audit that reports only defects hides which claims are now *load-bearing*. These held.

### 5.1 R9's structural claim — **SOUND** within its stated threat model

I tried to build an inconsistent verdict four ways:

```
findings + blind (the named incoherent cell)  -> REFUSED at construction (IncoherentVerdict)
findings only  -> state=UNGATED_GROUND clean=False exit=1  consistent=True
blind only     -> state=BLIND          clean=False exit=2  consistent=True
neither        -> state=GATED_GROUND   clean=True  exit=0  consistent=True

ESCAPE 1  dataclasses.replace(v, blind_sources=('b',))  -> REFUSED (__post_init__ re-runs)
ESCAPE 2  a falsy-but-non-empty findings container      -> ESCAPES (see below)
ESCAPE 3  object.__setattr__ on the frozen dataclass    -> still CONSISTENT (derivation is live)
```

`is_clean` reads only `('state','VerdictState','GATED_GROUND')`; `exit_code` reads only
`('state','exit_code')`. The three answers cannot disagree.

**ESCAPE 2 is not a defect.** It needs a deliberately-crafted `tuple` subclass overriding
`__bool__` — the hostile-author case the module explicitly puts out of scope, and
`ungated_ground` only ever builds a real tuple. Named here so the bound is met deliberately
rather than discovered later.

### 5.2 The precedence constant — **verified against both installed tools**

```
mypy   defaults.CONFIG_NAMES        = ['mypy.ini', '.mypy.ini']
       defaults.SHARED_CONFIG_NAMES = ['pyproject.toml', 'setup.cfg']
pytest 9.0.3 locate_config config_names = ['pytest.toml','.pytest.toml','pytest.ini','.pytest.ini',
                                           'pyproject.toml','tox.ini','setup.cfg']
gg.SHADOWING_CONFIGURATION_FILENAMES   = ('mypy.ini','.mypy.ini','pytest.toml','.pytest.toml',
                                          'pytest.ini','.pytest.ini')
```
Exactly the names that outrank the manifest in each tool's own order, no more. And none of them
exist in this checkout. The "check `repo_root` alone is sufficient" argument holds: pytest tries
`base=repo_root` first and stops because the manifest carries `[tool.pytest.ini_options]`; mypy
searches the invocation directory, and `typecheck.sh` anchors it with `cd … || exit 1`.

### 5.3 The `collection-convention` bound has **zero real exposure** — measured, not assumed

I enumerated every tracked `.py` that defines `test_`/`async def test_` functions and contributes
**no** collected item: **0 files**. The bound is honest and currently costs nothing.

### 5.4 The hostile-path forgery pin — sound, **and my first probe was wrong**

My first attempt counted `_MESSAGE_HEADER` **substring occurrences** and reported "FORGERY
POSSIBLE". That was the wrong instrument. The sound predicate is header **lines**:

```
SOUND PREDICATE (header LINES): 1 for 1 finding -> no forgery
my earlier predicate (substring): 2  <- WRONG INSTRUMENT, false positive
POSITIVE CONTROL — a RAW-interpolating wrong build: 2 header LINES -> the pin WOULD fire
```
`{path!r}` escapes the newline; the contract's own fixture (a path carrying a newline *and* a
forged header line) discriminates against the raw-render build. **Recorded because a probe that
lies the same way the author's did is this repo's documented audit failure mode, and mine did.**

### 5.5 Deletion dual — the removals I could adjudicate

| removed | adjudication |
|---|---|
| the frozen-roster / `FROZEN_SHA` design | **never existed in any committed `gated_ground.py`** — `git log --all -S'frozen_roster'` reaches only `310658e`, the commit that *archived* the adversary reports. Not a corpse; nothing stranded. |
| `TestThisInstrumentRidesTheTypeGateItself` (adversary-3 D-4) | **obligation preserved-with-pin**: `scripts/gated_ground.py` is `TYPES=COVERED` and falls inside the ∀ real-tree pin. Verified by classification, not by argument. |
| non-empty `EXEMPTIONS` (D-7) | **disclosed, not hidden** — the contract carries `# ⚠ THIS LOOP IS VACUOUS TODAY` at the loop and *"A literal `()` is indistinguishable from `EXEMPTIONS` today (F1 emptied…)"* at the signature pin. Honest. |
| `test_every_parsed_typecheck_root_is_a_directory` (adversary-3 C7 "FALSE GATE, INVERTED") | **CLOSED at HEAD** — renamed `…_exists_in_this_checkout`, assertion relaxed to `.exists()`, the contradicting comment rewritten, and a separate guard-level pin added. |
| the `Exemption` machinery | **NOT removed** — see D8. |

---

## 6. WRONG-BUILD CENSUS

Two isolated scratch repositories, each built from `git archive HEAD` + a fresh `git init`
(**never `cp -a` of this worktree — #284**), `.git` asserted to be a DIRECTORY, provenance
asserted in-process:

```
/tmp/ca44/refrepo/.git   -> drwxr-xr-x (DIRECTORY)   gg.__file__ = /tmp/ca44/refrepo/scripts/gated_ground.py
/tmp/ca44/refrepo2/.git  -> drwxr-xr-x (DIRECTORY)   gg.__file__ = /tmp/ca44/refrepo2/scripts/gated_ground.py
md5 of both instrument files in the archive == the frozen target
```

### 6.1 My **twelve invented** wrong builds — 11 killed, 1 survived

The author's harness bounds itself honestly (*"the build set is an ENUMERATION … Six of these 21
survived their first outing — evidence the enumeration was doing work, never evidence that a 22nd
would not survive"*). So I wrote the 22nd through the 33rd, aimed at surfaces its 21 do not touch:
the LEG A call site, the conftest branch, the **vanished-input** direction, the collector parser,
LEG B vacuity, the R9 classifier itself, the mypy allowlist, R10's own new `PYTEST_ADDOPTS` read,
the receipts anchor, exemption validation, and the whole-tree widening test.

```
=== baseline (correct build) ===
REF => 315 passed in 97.15s   [collected total: 315]
CA10_receipts_class_widened_to_docs              95 failed, 220 passed    killed
CA11_exemption_reason_validation_off              2 failed, 313 passed    killed
CA12_whole_tree_test_never_fires                 30 failed, 285 passed    killed
CA1_types_fate_uses_startswith_at_the_call_site   1 failed, 314 passed    killed
CA2_conftest_is_covered_wherever_it_sits          4 failed, 311 passed    killed
CA3_tracked_enumeration_silently_narrowed         8 failed, 307 passed    killed
CA4_collector_parse_accepts_every_line              315 passed           ❗SURVIVED
CA5_collected_is_every_tracked_file              31 failed, 284 passed    killed
CA6_state_classifier_always_says_gated           72 failed, 243 passed    killed
CA7_nothing_is_test_shaped                       25 failed, 290 passed    killed
CA8_mypy_allowlist_never_fires                    9 failed, 306 passed    killed
CA9_fingerprint_drops_pytest_addopts              2 failed, 313 passed    killed

12 built · 11 killed · 1 survived
```

Every run's collected total matched the baseline's 315, so none is "NOT COMPARABLE" — nothing was
killed by a syntax error masquerading as a failure.

**The results that matter most, because they are the ones that could have gone the other way:**

- **CA6 killed (72 failed).** R9's single classifier is not decorative — a build that always says
  `GATED_GROUND` reddens 72 pins. Combined with §5.1, the structural claim is real.
- **CA3 killed (8 failed).** The **vanished-input** direction — the shape that reports nothing at
  all rather than reporting something wrong — is pinned. This is the hardest one to catch and it
  was caught.
- **CA1 killed (1 failed).** `is_under` is pinned **at the call site**, not merely as a helper.
  Exactly one pin does it, so it is load-bearing and singular.
- **CA9 killed (2 failed).** R10's new `PYTEST_ADDOPTS` read is genuinely pinned; deleting the
  ruling E1 change is caught. The rider was implemented, not dropped.
- **CA10 killed (95 failed).** The archived-receipts class really is anchored in the committed
  `[tool.ruff] extend-exclude` line — widening it one component reddens a third of the contract.

**SURVIVOR — `CA4_collector_parse_accepts_every_line`, adjudicated with a measurement, not an
argument** (*"an equivalent build is not a pass"*, and *"all remaining survivors are equivalent" is
banned output* — so here is the single one, individually):

```
collector exit: 0
shipped parser (`if "::" in line`) -> 149 paths
CA4 parser     (`if line.strip()`) -> 150 entries
EXTRA admitted by CA4: ['8747 tests collected in 4.09s']
do any EXTRA entries collide with a tracked path? NO -> equivalent ON THIS TREE
```

(149 collected-from files + the 3 tracked `conftest.py`, which are COVERED by registration rather
than by collection, = the 152 `execution: COVERED` in §2's census. The numbers close.)

**Verdict: NOT a defect in the shipped build — a MISSING PIN in the contract.** The shipped parser
is correct; the contract simply cannot tell the two apart, because on every tolerated exit code
(0 and 5) the only non-`::` line pytest emits is a summary that collides with no path. The `::`
filter is what makes the parser read *item* lines rather than *any* line, and its removal is the
false-clear direction should pytest's `-q` output shape ever change — which is precisely the class
of assumption the guard elsewhere refuses to make (it has an explicit anti-vacuity refusal for
*"its output is not the shape this guard reads"*). One fixture whose collector output contains a
bare non-`::` line equal to a tracked path would kill it.

### 6.2 The author's **21**, re-run by me against the frozen build

```
=== baseline (correct build) ===
REF => 315 passed in 97.52s   [collected total: 315]
WB10_memo_ignores_the_root                         315 passed              ❗SURVIVED
WB11_fingerprint_swallows_unreadable_inputs         3 failed, 312 passed    killed
WB12_fingerprint_covers_config_only                 1 failed, 314 passed    killed
WB13_shadow_refusal_names_nothing                   6 failed, 309 passed    killed
WB14_absent_mypy_table_accepted                     3 failed, 312 passed    killed
WB15_mypypath_reader_not_consulted                  3 failed, 312 passed    killed
WB16_whole_tree_test_is_a_spelling_denylist        12 failed, 303 passed    killed
WB17_door_identity_computed_not_literal             2 failed, 313 passed    killed
WB18_refusal_bypasses_the_door_helper               3 failed, 312 passed    killed
WB19_clean_render_over_claims                       1 error in 0.20s        killed  ⚠ NOT COMPARABLE (1 != 315)
WB1_blindness_only_for_five_named_doors            59 failed, 256 passed    killed
WB20_test_shapedness_uses_the_process_cwd           1 failed, 314 passed    killed
WB21_memo_written_before_the_anti_vacuity_check     1 failed, 314 passed    killed
WB2_served_surface_ignores_findings                 2 failed, 313 passed    killed
WB3_state_prefers_findings_over_blindness           1 failed, 314 passed    killed
WB4_exit_code_is_a_second_mapping                   1 failed, 314 passed    killed
WB5_incoherent_verdict_permitted                    1 failed, 314 passed    killed
WB6_shadow_check_covers_mypy_only                  12 failed, 303 passed    killed
WB7_shadow_reader_never_consulted                  18 failed, 297 passed    killed
WB8_basename_only_pattern_match                     4 failed, 311 passed    killed
WB9_memo_keyed_on_identity_alone                    9 failed, 306 passed    killed

21 built · 20 killed · 1 survived
```

**WB1 and WB2 — the two builds that survived revision 5 at 171/171, and the reason revision 6
exists — are now killed at 59 and 2 failures.** R9's ruling did what it was written to do.

**`WB10_memo_ignores_the_root` reproduces as a survivor**, exactly as the author reported and
adjudicated (BEHAVIOURALLY EQUIVALENT: the fingerprint hashes ABSOLUTE paths, so it already
distinguishes two identical trees at different roots, and the key's `repo_root` component is
defence in depth). The instrument carries that disposition and its re-open trigger in a ⚠ comment
at `_collector_input_fingerprint`. **I confirm the adjudication.**

**But one row is not a result — see D13.**

---

## 7. RESIDUALS

### 7.1 Things I could not close

| # | residual | what would close it |
|---|---|---|
| R-1 | **adversary-3 E1 — the reference build's provenance.** The contract author's throwaway reference build sat in-tree at `scripts/gated_ground.py` while the builder worked; deletion was *claimed*, never receipted. It was **untracked**, so no artifact survives: `git log --follow` reaches only `7708a74` onward. **UNVERIFIABLE by construction.** | Nothing, retroactively. Forward: a "delete the reference build" step that is a verified receipt. Mitigating: the shipped build has since survived 3 adversary passes, the author's 21 wrong builds and my 12. |
| R-2 | **adversary-3 E3 — the frozen contract moved after freezing** (`89cea408…`/2405 lines claimed vs `af4cdab5…`/2404 on disk), untracked, unattributed. | Nothing. Forward: freeze by `git add`, never by md5 of an untracked file. |
| R-3 | **r5's mutation count contradicts itself** — §4 heading *"2 runs"* over a 4-row table; line 27 *"4 mutation proofs total this wave, not 2"*; §157 *"I ran two."* Archived receipt; byte-faithful law forbids editing the body. | A one-line archived-report header saying so (CLAUDE.md permits exactly this). |
| R-4 | **r5 §5's unproven-pin list** — *"Treat every one of them as unproven"* — is discharged only in part by adversary-3. I did not re-derive it pin-by-pin. | A targeted mutation-proof wave over the named pins using `scripts/mutation_proof.py`. |
| R-5 | **E6 — three pytest env doors still open** (`PYTEST_PLUGINS`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD`, `PY_IGNORE_IMPORTMISMATCH`). The author holds the patch and declined to apply it without a ruling. **My D1 shows the residual is larger than these three.** | One operator ruling; then close them with D1's fix in the same wave. |
| R-6 | **164 dangling `REPORT-*.md` citation sites in live files** (pre-existing #152/#153 debt). **Packet 44 introduced ZERO** — every `REPORT-*.md` name on an added line in `7bd9b4e..HEAD` resolves. | Its own packet; out of scope here. Surfaced per scope law. |
| R-7 | A fixtures-only `test_*.py` (test-shaped, zero collected items) would be reported as UNGATED GROUND, and the message offers only "add its tree to testpaths" or "ESCALATE" — neither is the fix (renaming is). **Zero such files exist today** (§5.3), so this is a latent false-positive class, and a gate that refuses honest code gets switched off. | A third sentence in `_execution_message`. |
| R-8 | The real-tree pins call `classify(REPO_ROOT, exemptions=())`, not the shipped `EXEMPTIONS` default. Identical today (`EXEMPTIONS == ()`), and `()` is the stricter direction, so safe — but the invariant does not exercise the shipped default. | Fix D2 and pass the default in the same edit. |

### 7.2 Retired-name sweep — every hit, an individual verdict

Bare and anchor-free over the whole tracked tree. **"All remaining hits are X" is banned; each
line below is its own verdict.**

`FROZEN_SHA` / `frozen_roster` / `ls-tree` — **zero corpses**: no committed `gated_ground.py` at
any of `7708a74 737ee6b ee1d753 310658e 7ad1b0a 13bbe84 HEAD` ever contained them.

The six archived relics, per hit:

| file:line | verdict |
|---|---|
| `docs/design/2026-07-06-p8dprime-fix-specs.md:7,8,440,442` | **clean** — repointed to the new archive path |
| `docs/design/2026-07-06-p8dprime-fix-specs.md:509` | **clean** — bare filename, no path to dangle |
| `docs/plans/v2/DESIGN-LAW.md:127,128` | **clean** — new path |
| `docs/plans/v2/DESIGN-LAW.md:129` | **clean** — "its required sibling, same directory", relative to :128 |
| `docs/plans/v2/03b-design-rulings-r2.md:1046` | **clean** — new path |
| `docs/eval/smoke_p8b.py:16,26,249` | **clean** — new path |
| `docs/eval/smoke_p8b.py:30,43` | **clean** — bare names / symbol reference |
| `scripts/comms_consumer_eval.py:27` | **clean** — new path, in a gated source file |
| `loremaster/tests/test_mcp_server.py:4583` | **clean** — new path |
| **`docs/plans/v2/INDEX.md:283`** | **STALE CORPSE — DANGLING. → D7** |
| `docs/plans/v2/receipts/2026-07-10-design-docs-extraction.md:190,191,192,193,196,197` | **clean** — archived receipt, bare filenames, no path |
| `docs/plans/v2/receipts/2026-07-10-resume-chain-extraction.md:61` | **dangling-but-ARCHIVED** — carries the old `docs/eval/` path; byte-faithful law forbids the edit. Pre-existing class. |
| `docs/plans/v2/receipts/2026-07-26-packet11i-fixwave/REPORT-pkgscout-scripts.md:298` | **dangling-but-ARCHIVED** — same; law forbids the edit |
| `docs/design/2026-07-06-client-needs-consult.md:81` | **clean** — a historical negative (*"did not read…"*); `038db75` correctly ruled LEAVE, since repointing would falsify what that agent stated |

`roster` / `exempt` / `exemption` elsewhere in the tree resolve to live, unrelated senses —
`AgentRegistry.roster()` / `FleetRoster` (production API), the model-roster ruling in `CLAUDE.md`
and `INDEX.md`, the comms-fleet roster in the smoke, and the shellout / retry / promise-registry
allowlists in `loremaster`. The only `exemption` hits that are a defect are the five in
`gated_ground.py` / `test_gated_ground.py` that **assert the mechanism does not exist** → **D8**.

### 7.3 Numbers I re-derived, and where they landed

| claimed | where | derived at `2c741ee` | verdict |
|---|---|---|---|
| `scripts/` type errors | #188 | **0** (22 files) | ✓ discharged |
| shellcheck findings | R5 | **0** over **7** tracked `.sh` | ✓ |
| testpaths gain | R4 | **117** | ✓ exact |
| instrument pins | claim 6 | **315** collected, 315 passed ×2 | ✓ |
| full suite | — | **8708 p / 36 s / 3 xf = 8747 collected** | ✓ reconciles |
| "two entries are not members" | `typecheck.sh` | **3** | ✗ **D4** |
| "eleven sites" | `typecheck.sh` | **9** verbatim / **12** loose | ✗ **D5** |
| "352 nodes from that tree" | addendum-F | **667** | ✗ **D6** |
| "314 collected / 292 of 292 tracked `.py`" | author report SUMMARY BLOCK | **315** / **293** | flag — the report *is* date-scoped (`md5 197f6868…`, 4024 lines) and corrected ~700 lines down in the r2 addendum, but repo law says the lead reads the SUMMARY BLOCK first |
| "190 tests" in `docs/eval` | `44-ungated-ground.md:25` | **198** | stale-but-harmless, minted pre-range |
| "the 5021-line deploy smoke" | `44-ungated-ground.md:20` | **3254** | never true at any point; pre-existing, outside the packet range |

---

## 8. SURFACED TO LEAD — questions, not verdicts. Scope is the operator's.

1. **D1's fix scope.** Close the file-shaped memo hole (the conftest chain from `repo_root` to
   each testpath) **and** rewrite the `collector-memoisation` bound to state what is genuinely
   uncovered — or ship the bound as-is with the hole named? Recommendation: **close it**; the edit
   is one function and E6's three env doors can ride the same wave.
2. **D8 — the exemption-mechanism prose.** Two coherent resolutions: (a) delete the `Exemption`
   machinery and the ~30 pins exercising it, making the message true; (b) reword to *"the
   exemption table is EMPTY; a row requires an operator ruling"* and re-pin. This is a DESIGN
   decision, so I am not choosing. Recommendation: **(b)** — the machinery is the mechanism a
   future ruling would need, and deleting it to make a sentence true is the wrong direction.
3. **D10 — closed mid-audit at `9377af5`; only the ledger question remains.** The four history
   rewrites are real and one dropped the lead's commit object; the no-loss claim re-derives TRUE
   under my own instrument. Do you want the rewrite disclosed on the ledger as well as in the
   report, given the lead's own account reached one of four?
4. **D11 / S2 — the in-image landing hazard.** Adding `scripts` to `testpaths` means the packet-01a
   conformance run now collects `scripts/test_gated_ground.py` in an image with no git and no
   `scripts/` baked in. Options: bake `scripts/` + git into the image; exclude `scripts` from the
   in-image invocation; or state it as a bound. **No closure claim exists anywhere for this.**
5. **D12 — the two tracked root reports.** `git mv` both into
   `docs/plans/v2/receipts/2026-07-29-packet44/` as the wave close-out? `REPORT-builder-forgery-sites.md`
   is peer-authored, so I did not assume.
6. **D3 under R8.** The peer-owned `scripts/test_forgery_door_sweep.py` teaches a retired scope and
   a count this packet calls a phantom, in a **collected** test's docstring and its served failure
   message — and the report that shipped it ordered its deletion once `scripts` joined `MEMBERS`,
   which happened in-packet. R8 froze it. Does the trigger now fire, or does it stay ledgered?

Additionally, for information: **finding #287 did NOT reproduce for me** — `lore_comms` and
`lore_findings` loaded and worked. Three agents in this packet reported them ABSENT. That is a
data point about intermittency, not a closure.

---

## 9. INSTRUMENTS (brief-base §1 — an instrument that established a load-bearing claim is a deliverable)

None of these could be committed (I am read-only on tracked content), so they are pasted verbatim.
`/tmp` paths are given only to describe where they RAN; the bytes below are the durable form.

### 9.1 `probe_memo_stale.py` — established D1

```python
#!/usr/bin/env python3
"""coldaudit-44-1 — can the R10 memo serve a STALE HEALTHY verdict after PYTEST_ADDOPTS
was added to its key?

The `collector-memoisation` STATED BOUND (scripts/gated_ground.py::STATED_BOUNDS) reads:
    "The memo's fingerprint covers the collector's file inputs and PYTEST_ADDOPTS, and no
     other variable."
and names a residual of exactly THREE further pytest-read env vars.

This probe asks whether "the collector's file inputs" is TRUE — i.e. whether a file that
pytest genuinely reads during collection can sit OUTSIDE the fingerprint. Candidate: an
UNTRACKED conftest.py in a directory that is an ANCESTOR of a testpath but is neither
repo_root nor itself under a testpath. `_collector_input_paths` hashes (a) repo_root's
manifest/conftest/shadow-candidates, (b) every TRACKED .py, (c) every .py UNDER a testpath.
An untracked ancestor conftest is in none of the three — and pytest loads it.

CONTROLS (a negative result is worthless without them):
  * POSITIVE CONTROL — after clearing the memo, the same tree must report the findings,
    proving the mutation was real and the guard CAN see it.
  * NEGATIVE CONTROL — a mutation that IS in the key (the manifest) must invalidate,
    proving the memo is not simply always-stale.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path("/tmp/ca44/memoprobe")
GUARD_SOURCE = Path(
    "/home/ejprice/PycharmProjects/lore/.claude/worktrees/pkt44/scripts/gated_ground.py"
)

MANIFEST = """\
[tool.uv.workspace]
members = ["pkg"]

[tool.pytest.ini_options]
testpaths = ["pkg/tests"]

[tool.ruff]
extend-exclude = ["docs/plans/v2/receipts"]

[tool.mypy]
python_version = "3.13"
strict = true
"""

RUNNER = "#!/usr/bin/env bash\nMEMBERS=(pkg)\n"

SILENCER = """\
def pytest_ignore_collect(collection_path, config):
    return True
"""


def build() -> None:
    if ROOT.exists():
        shutil.rmtree(ROOT)
    (ROOT / "pkg" / "tests").mkdir(parents=True)
    (ROOT / "scripts").mkdir()
    (ROOT / "docs" / "plans" / "v2" / "receipts").mkdir(parents=True)
    (ROOT / "pyproject.toml").write_text(MANIFEST)
    (ROOT / "scripts" / "typecheck.sh").write_text(RUNNER)
    (ROOT / "pkg" / "__init__.py").write_text("")
    (ROOT / "pkg" / "tests" / "test_a.py").write_text("def test_a():\n    assert True\n")
    (ROOT / "docs" / "plans" / "v2" / "receipts" / "old.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(ROOT), "init", "-q", "-b", "main"], check=True)
    subprocess.run(["git", "-C", str(ROOT), "add", "-A"], check=True)
    subprocess.run(
        ["git", "-C", str(ROOT), "-c", "user.name=p", "-c", "user.email=p@e.invalid",
         "commit", "-q", "-m", "base"],
        check=True,
    )
    assert (ROOT / ".git").is_dir(), "PROVENANCE: .git must be a DIRECTORY, not a worktree file"


def show(label, verdict) -> None:
    print(f"{label:<58} state={verdict.state.name:<14} exit={verdict.exit_code} "
          f"findings={len(verdict.findings)} blind={len(verdict.blind_sources)}")


def main() -> int:
    sys.path.insert(0, str(GUARD_SOURCE.parent))
    import gated_ground as gg

    print(f"gg.__file__ = {gg.__file__}")
    build()

    gg._COLLECTOR_MEMO.clear()
    a = gg.ungated_ground(ROOT); show("A. healthy, cold memo (warms it)", a)

    # NEGATIVE CONTROL: silence the tree with the UNKEYED file AND move a KEYED input in the
    # same step. If the key works at all, the memo must re-run and SEE the silencer.
    (ROOT / "pkg" / "conftest.py").write_text(SILENCER)
    (ROOT / "pyproject.toml").write_text(MANIFEST + "\n# keyed input moved\n")
    b = gg.ungated_ground(ROOT); show("B. NEG CTRL: unkeyed silencer + KEYED manifest change", b)

    # THE MEASUREMENT: the unkeyed file ALONE, against a warm memo.
    gg._COLLECTOR_MEMO.clear()
    (ROOT / "pkg" / "conftest.py").unlink()
    (ROOT / "pyproject.toml").write_text(MANIFEST)
    c = gg.ungated_ground(ROOT); show("C. healthy again, cold memo (warms it)", c)
    (ROOT / "pkg" / "conftest.py").write_text(SILENCER)
    d = gg.ungated_ground(ROOT); show("D. unkeyed silencer ONLY, warm memo", d)

    # POSITIVE CONTROL: the same tree, memo cleared — the guard must SEE it.
    gg._COLLECTOR_MEMO.clear()
    e = gg.ungated_ground(ROOT); show("E. POS CTRL: same tree, memo cleared", e)

    print()
    print("bytes identical C vs D:", c.render() == d.render(), " <-- True == FALSE CLEAR")
    print("NEG CTRL passes (keyed change forced a re-run):", b.state.name == "UNGATED_GROUND")
    print("POS CTRL passes (the guard can see the mutation):", e.state.name == "UNGATED_GROUND")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 9.2 `ca44_wrong_builds.py` — twelve wrong builds the author's 21 do not contain

Extends `scripts/wrong_builds.py`'s registry rather than forking it — ONE IMPLEMENTATION: the
anchor-matches-exactly-once guard, the collected-total comparability guard, the byte-exact restore
and the `.git`-is-a-DIRECTORY provenance check all come from there.

```python
#!/usr/bin/env python3
"""coldaudit-44-1's OWN wrong builds — twelve the author's 21 do not contain.

Run:  .venv/bin/python /tmp/ca44/ca44_wrong_builds.py --scratch /tmp/ca44/refrepo2
"""

from __future__ import annotations

import sys

sys.path.insert(0, "/tmp/ca44/refrepo2/scripts")

import wrong_builds as wb  # noqa: E402

W = wb.WRONG_BUILDS

# CA1 — LEG A membership reverts to str.startswith at the CALL SITE. The helper stays
# correct; the site stops calling it. `scriptsfoo/x.py` then reads as covered by `scripts`.
W["CA1_types_fate_uses_startswith_at_the_call_site"] = [(
    """    if any(is_under(path, root) for root in scopes.typecheck_roots):
        return Fate.COVERED""",
    """    if any(path.startswith(root) for root in scopes.typecheck_roots):
        return Fate.COVERED""")]

# CA2 — a conftest is COVERED wherever it sits, so a conftest outside every testpath
# (which pytest never loads) reads as registered.
W["CA2_conftest_is_covered_wherever_it_sits"] = [(
    """    if PurePosixPath(path).name == CONFTEST_FILENAME:
        if any(is_under(path, testpath) for testpath in scopes.testpaths):
            return Fate.COVERED""",
    """    if PurePosixPath(path).name == CONFTEST_FILENAME:
        return Fate.COVERED""")]

# CA3 — THE VANISHED-INPUT DIRECTION, which reports nothing at all: a whole tree drops
# out of the enumeration, so no fate is ever computed for it and no finding can exist.
W["CA3_tracked_enumeration_silently_narrowed"] = [(
    """    tracked = sorted(record for record in records if record.endswith(".py"))""",
    """    tracked = sorted(
        record
        for record in records
        if record.endswith(".py") and not record.startswith("skills/")
    )""")]

# CA4 — the collector output parser accepts every non-blank line, so the "covered" set is
# a superset of what pytest actually collected.
W["CA4_collector_parse_accepts_every_line"] = [(
    """    contributing = frozenset(
        line.split("::", 1)[0].strip() for line in completed.stdout.splitlines() if "::" in line
    )""",
    """    contributing = frozenset(
        line.split("::", 1)[0].strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    )""")]

# CA5 — LEG B is never measured: everything tracked is declared collected. The collector
# subprocess is never run at all.
W["CA5_collected_is_every_tracked_file"] = [(
    """        collected=collected_test_files(repo_root),""",
    """        collected=frozenset(tracked),""")]

# CA6 — THE DIRECT ATTACK ON R9: the single classifier every served answer derives from
# always says GATED_GROUND. If this survives, deriving the three answers from one
# classifier bought nothing.
W["CA6_state_classifier_always_says_gated"] = [(
    """        if self.blind_sources:
            return VerdictState.BLIND
        if self.findings:
            return VerdictState.UNGATED_GROUND
        return VerdictState.GATED_GROUND""",
    """        return VerdictState.GATED_GROUND""")]

# CA7 — nothing is test-shaped, so LEG B quantifies over the empty set and is vacuously
# clean (the anti-vacuity direction for LEG B's INPUT rather than its output).
W["CA7_nothing_is_test_shaped"] = [(
    """    if PurePosixPath(path).name == CONFTEST_FILENAME:
        return True
    absolute = PurePosixPath(str(repo_root.resolve())) / path
    return any(_matches_collection_pattern(pattern, absolute) for pattern in patterns)""",
    """    return False""")]

# CA8 — the mypy allowlist never fires: an unmodelled setting no longer refuses, so LEG A
# certifies a scope it cannot see.
W["CA8_mypy_allowlist_never_fires"] = [(
    """    refusals = [
        f"[tool.mypy] {key} = {table[key]!r} is a mypy setting this guard does not model, so a "
        f"registered file could be unchecked in fact; extend it or remove the {key}"
        for key in sorted(table)
        if key not in _MODELLED_MYPY_TABLE_KEYS and key != _MYPY_OVERRIDES_KEY
    ]""",
    """    refusals: list[str] = []""")]

# CA9 — R10's OWN new claim, deleted: PYTEST_ADDOPTS leaves the memo key while the child
# still inherits it.
W["CA9_fingerprint_drops_pytest_addopts"] = [(
    """    digest.update(os.environ.get("PYTEST_ADDOPTS", "").encode("utf-8", errors="surrogateescape"))
    digest.update(b"\\0")""",
    """    digest.update(b"\\0")""")]

# CA10 — the archived-receipts exemption is widened one component. Caught by the ruff-
# declaration anchor; this is the POSITIVE CONTROL proving that anchor is live.
W["CA10_receipts_class_widened_to_docs"] = [(
    """ARCHIVED_RECEIPTS_ROOT = "docs/plans/v2/receipts\"""",
    """ARCHIVED_RECEIPTS_ROOT = "docs\"""")]

# CA11 — the exemption row's reason validation is switched off, so a placeholder row is
# admissible again.
W["CA11_exemption_reason_validation_off"] = [(
    """    def _validate_reason(self) -> None:
        if len(self.reason.split()) < _MINIMUM_PHRASE_WORDS:""",
    """    def _validate_reason(self) -> None:
        if False and len(self.reason.split()) < _MINIMUM_PHRASE_WORDS:""")]

# CA12 — the whole-tree widening test never fires, so a MEMBERS entry of "/" or ".."
# marks the tree covered and reports zero gaps.
W["CA12_whole_tree_test_never_fires"] = [(
    """    if not entry.strip():
        return True
    candidate = PurePosixPath(entry)
    return candidate.is_absolute() or candidate.parts == () or ".." in candidate.parts""",
    """    return False""")]

if __name__ == "__main__":
    only_mine = [name for name in sorted(W) if name.startswith("CA")]
    argv = sys.argv[1:]
    if not any(not a.startswith("-") and not a.startswith("/") for a in argv):
        argv = argv + only_mine
    raise SystemExit(wb.main(argv))
```

### 9.4 `wb19_fixed.py` — established D13's missing measurement

```python
#!/usr/bin/env python3
# coldaudit-44-1 — WB19 with its escaping bug repaired, so it MEASURES for the first time.
#
# scripts/wrong_builds.py::WB19_clean_render_over_claims's replacement ends  axes.""  — a stray
# quote produced by a backslash-escaped quote inside a triple-quoted literal — so the patched
# module is invalid Python, the run collects 1 error, and the harness reports it NOT COMPARABLE
# (nothing measured). This is the build for the DUAL false clear that ruling R9 exists to close,
# so its result matters. One character repaired; nothing else changed.
from __future__ import annotations

import sys

sys.path.insert(0, "/tmp/ca44/refrepo2/scripts")

import wrong_builds as wb  # noqa: E402

ANCHOR = (
    "                return (\n"
    '                    "GATED GROUND — every tracked module is registered with the type gate, and "\n'
    '                    "every tracked test-shaped file is one the collector reaches."\n'
    "                )"
)
REPLACEMENT = (
    '                return "GATED GROUND: every committed .py is registered on both axes."'
)

wb.WRONG_BUILDS["WB19fixed_clean_render_over_claims"] = [(ANCHOR, REPLACEMENT)]

if __name__ == "__main__":
    raise SystemExit(wb.main(sys.argv[1:] + ["WB19fixed_clean_render_over_claims"]))
```

⚠ My **first** draft of this file was itself invalid Python — its comment-turned-docstring contained
a literal `"""`, which terminated the docstring early. Recorded because it is the same class of
defect as the one it repairs, and because a probe that fails to run looks exactly like a probe that
found nothing.

### 9.5 The one-liners

```bash
# D2 — the headline invariant on a blind verdict (by construction)
python - <<'PY'
import sys; sys.path.insert(0,'scripts')
import gated_ground as gg
blind = gg.Verdict(findings=(), blind_sources=('the GUARD is blind, not the tree clean',))
print('findings =', list(blind.findings), '| state =', blind.state.name, '| exit =', blind.exit_code)
PY

# D2 — the in-image shape, empirically
mkdir -p /tmp/ca44/shim && printf '#!/bin/sh\nexit 127\n' > /tmp/ca44/shim/git && chmod +x /tmp/ca44/shim/git
PATH=/tmp/ca44/shim:$PATH uv run pytest -q scripts/test_gated_ground.py -p no:randomly | tail -3

# D9 — the inline mypy silencer, with a positive control
printf 'def f(x: int) -> str:\n    return x\n' > /tmp/plain.py
printf '# mypy: ignore-errors\ndef f(x: int) -> str:\n    return x\n' > /tmp/silenced.py
uv run mypy /tmp/plain.py; uv run mypy /tmp/silenced.py

# D4/D5/D6 — the numerics
python -c "import tomllib,pathlib;m=tomllib.loads(pathlib.Path('pyproject.toml').read_text());print(set(m['tool']['uv']['workspace']['members']))"
git grep -l 'sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))' -- 'scripts/*.py' | wc -l
uv run pytest --collect-only -q scripts | tail -2

# D10 — the history-rewrite verification
git merge-base --is-ancestor 00cf487 HEAD; git show --stat 00cf487
git diff --stat 00cf487 7ad1b0a -- scripts/gated_ground.py scripts/test_gated_ground.py   # empty == no loss

# §5.3 — the collection-convention bound's real exposure (0 files)
# §7.2 — the relic sweep
for n in 2026-07-04-p8a-baseline-raw 2026-07-04-p8a-baseline connections_p8a \
         evaluation_harness_p8a p8d-flip-eval-raw p8dprime-rerun-raw; do
  git grep -n -- "$n" -- . ':!docs/plans/v2/receipts/2026-07-04-p8a/'
done
```

---

*Cold audit by `coldaudit-44-1`, 2026-07-30, at `2c741ee`. I fixed nothing and committed nothing.
Both scratch repositories were built from `git archive` + a fresh `git init`; neither was a copy of
this worktree (#284), and provenance was asserted in-process before any measurement.*
