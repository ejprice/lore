# REPORT-builder-44-config-1 — packet 44 UNGATED GROUND, config wave

brief-base v9 read

## CAPABILITY CHECK (brief-base §4 — first thing in the report)

The brief demanded: worktree git ops, file edits, `uv`/`mypy`/`pytest`/`ruff`, a **shellcheck**
binary that does not exist on this host, and `lore_findings`. **Everything was meetable.** The one
real question was shellcheck: `which shellcheck` → not found, and there is no system package. It
resolved as a Python wheel (`shellcheck-py`, which vendors the binary), so no install
authorization was needed beyond the dev-group line the brief already authorized. Nothing in the
brief was impossible, and no work was silently skipped.

**Dogfood disclosure (project CLAUDE.md step 3):** every structural answer below comes from
`git grep` / `git ls-files` / config parsing, **not** from the lore graph. That is sanctioned and
correct here — lore's index cannot see this worktree (#125), and every question in this wave is a
non-symbol textual/path seam (config keys, prose citations, path membership) that a symbol graph
cannot answer. `lore_findings` was used for the ledger. **No lore friction to file:** lore was not
routed around, it was not the instrument for these questions.

---

## SUMMARY BLOCK

- `brief-base v9 read`
- **state: done-with-deviations** — 7 work items (A–G) complete, 6 commits, all gates green.
- **deviation 1 (material, read this one):** the brief's prescribed fix for `contention_hunt.sh`
  — *"SC2086, quote `$CONTRACT`"* — **would have installed a false clear.** Measured, not
  argued. Fixed as an array instead. §E2.
- **deviation 2:** the brief said add a `docs/eval` iteration and separately said update the
  `MEMBERS` comment; I put `docs/eval` **inside** `MEMBERS` with a per-root MYPYPATH map, so the
  sibling's `MEMBERS`-parsing guard sees it as a typecheck root. Both readings written out, §B1.
- **deviation 3:** one of my OWN comments asserted an unverified fact about shellcheck; a
  mutation proof falsified it. Corrected in the file, visibly. §E4.
- `Packages considered:` **shellcheck-py** (READ: ran `uv run --with shellcheck-py shellcheck
  --version` → 0.11.0 before adopting; it vendors the upstream binary as a wheel) → **replace** a
  system-package dependency, because a gate that resolves from `uv`'s lock cannot be present on
  one machine and absent on another — that absence is #131 verbatim. **markdown-it-py** (READ:
  #270's own probe receipts + the archived README's promotion clause) → **keep_with_trigger**,
  trigger = "a future packet promotes a battery grader to `scripts/`"; the swap must NOT touch the
  archived copies (byte-faithful law). **shell-array parsing / `git ls-files` enumeration /
  `tomllib`** → already-present tools, no new mechanism authored.
- **decisions-needed (5, all in §SURFACED):** ① the #198 consolidation fork re-opened by its own
  fired trigger — **filed as #286**, needs an operator ruling · ② `docs/plans/v2/INDEX.md:283`
  dangles, exact edit supplied, lead's file · ③ `REPORT-builder-forgery-sites.md` is a tracked
  report at the repo root awaiting its archive-law `git mv` · ④ the F12.2 row in the r2 amendment
  ledger carries the same now-discharged raise, exact edit supplied · ⑤ **#188 is
  invocation-shape-dependent and materially smaller than believed** — 45 vs **24**.
- **receipt pointers:** gate tails §GATES · mutation proofs §RIDER · the per-hit prose verdicts
  §A2 and §F · the CONTRACT false-clear measurement §E2 · ledger dispositions §G.
- **findings:** #261 #270 #280 #281 #282 #283 **resolved** (6); **#286 filed** (1 new).

---

## GATES — all measured in this worktree, 2026-07-29, at HEAD `8015d22` + this report

```
./scripts/typecheck.sh
  typecheck: lorerunes OK
  typecheck: lorescribe OK
  typecheck: loresigil OK
  typecheck: loremaster OK
  typecheck: skills OK
  typecheck: docs/eval OK          <- NEW leg (#261)
  typecheck: shellcheck OK (7 tracked .sh)   <- NEW leg
  TYPECHECK EXIT=0

uv run ruff check .        ->  All checks passed!     RUFF EXIT=0

uv run shellcheck $(git ls-files '*.sh')   ->  EXIT 0 over 7 tracked .sh
  (baseline at 5a850c3, re-derived by me: exactly 4 findings, 2 warning + 2 info — the
   lead's number reproduced. Now zero.)

uv run pytest -n auto
  8393 passed, 36 skipped, 3 xfailed, 1 warning in 214.60s   PYTEST_EXIT=0
  8393 + 36 + 3 = 8432 = the collected count, exactly.
```

⚠ **The passed-count above is an EXECUTED count, not a collected one** — the brief was right to
insist, and the reconciliation to 8432 is what makes it checkable. A final re-run at report time
is in §TREE-MOVED, along with why its total is larger and why that total is not mine.

Collection arithmetic for the `skills` addition, re-derived rather than inherited:

```
collected BEFORE : 8315
collected AFTER  : 8432        8315 + 117 = 8432 exactly — no collision, no test lost
```

**Provenance receipt (#140 law), printed because a claim is about a TREE:**

```
loremaster:  .../worktrees/pkt44/loremaster/loremaster/__init__.py
loresigil:   .../worktrees/pkt44/loresigil/loresigil/__init__.py
lorescribe:  .../worktrees/pkt44/lorescribe/lorescribe/__init__.py
lorerunes:   .../worktrees/pkt44/lorerunes/lorerunes/__init__.py
```

All four resolve **inside the worktree**, re-verified after my `uv sync --all-packages`.
**No `scratch_copy.sh` and no `cp -a` of this worktree was used anywhere** — the brief's landmine
is real (a worktree's `.git` is a FILE naming the original repo's gitdir, so a scratch `git add`
mutates the real worktree). Every mutation proof used the standing-law alternative: mutate the
real tree, restore from a `cp -a` **content** backup at `/tmp/pkt44-content-backup/`, verify
byte-exact by md5 **and** an empty `git diff`. Never `git checkout --`.

---

## A — the six p8a relics archived (`439b55d`)

`git mv` to `docs/plans/v2/receipts/2026-07-04-p8a/`, plus a README modelled on the
`2026-07-28-packet11ib` one (base-path note, what-is-here table, law-backed ungated statement,
re-open trigger).

**Byte-identity is proven by git, not asserted by me:** all six are 100%-similarity renames,
`6 files changed, 0 insertions(+), 0 deletions(-)`. That is what honours `DESIGN-LAW.md` §6's
**"REUSED VERBATIM — measurement pins are never upgraded"** pin: the pin is about the ARTIFACT,
and only the address moved.

**The two `.json` files stayed**, as the brief required — `deploy-receipt-pre-ddl.json` and
`deploy-baseline-latency.json` are LIVE inputs the smoke reads via `Path(__file__).with_name(...)`
at `PRE_DDL_RECEIPT_PATH` / `LATENCY_BASELINE_PATH`. A wholesale `docs/eval/*.json` sweep would
have broken the deploy smoke.

### A2 — the bare prose sweep, per-hit verdict (`038db75`)

Sweep as briefed — bare, anchor-free, all tracked files, **no file-type filter**:

```
git grep -nI --fixed-strings -e connections_p8a -e evaluation_harness_p8a \
  -e 2026-07-04-p8a-baseline -e p8d-flip-eval-raw -e p8dprime-rerun-raw \
  -- . ':!docs/plans/v2/receipts'
```

The bareness is load-bearing: the sidecar's own earlier grep was `--include`-anchored to
`.py/.sh/.toml/.yaml` and **structurally could not see `.md`** — and `DESIGN-LAW.md`, the file
carrying the pin on these very instruments, is `.md`. **I then ran a second, wider sweep on the
bare string `docs/eval`, which found a SEVENTH live site the six-name grep could not see either,
because it is written as a glob** (`docs/eval/p8d*-raw.md`). Anchors keep losing to prose.

| site (symbol/string, not line number) | verdict |
|---|---|
| `DESIGN-LAW.md` §6 `Sources:` + A/B-instrument bullet | **UPDATE** + dated note — the pin site |
| `03b-design-rulings-r2.md` §C1 A/B-instrument citation | **UPDATE** + dated note |
| `2026-07-06-p8dprime-fix-specs.md` **Evidence base:** block | **UPDATE** + a file-level address note |
| `2026-07-06-p8dprime-fix-specs.md` §3.1 `Baseline =` / `Flip =` | **UPDATE** |
| `smoke_p8b.py` module docstring (connection-layer ×2) | **UPDATE** + dated note |
| `smoke_p8b.py::connect` docstring | **UPDATE** |
| `comms_consumer_eval.py` `HOW TO RUN` | **UPDATE** |
| `test_mcp_server.py::test_unknown_tier_filter_renders_tier_appropriate_teaching_not_path_wording` docstring | **UPDATE** — checked: prose only; the assertions below it pin notice text, so no test was certifying the old address |
| `2026-07-06-p8dprime-fix-specs.md` §3.5 bare `connections_p8a.py` | **LEAVE** — a filename in a narrative sentence about a latent import bug, not an address to follow |
| `smoke_p8b.py` docstring lesson 2, `evaluation_harness_p8a.py._serialize_tool_result` | **LEAVE** — a `module.symbol` reference; the new dated note six lines above names its home |
| `DESIGN-LAW.md` §6 bare `connections_p8a.py` | **LEAVE** — qualified in place as *"(its required sibling, same directory)"* |
| `2026-07-06-client-needs-consult.md` deviations line, `docs/eval/p8d*-raw.md` | **LEAVE** — a HISTORICAL NEGATIVE ("did not read…") about files at their then-address. Repointing it would falsify what that agent actually stated. |
| every hit inside the six moved files themselves | **LEAVE** — archived receipts, byte-faithful law; the arrival README's PATH NOTE translates them (the `d74e1da` convention) |
| `docs/plans/v2/INDEX.md:283` | **FLAGGED, NOT EDITED** — lead's file. Exact edit in §SURFACED ②. |

No wholesale classification anywhere; every residual carries its own reason.

---

## B — `scripts/typecheck.sh`, the `docs/eval` leg (`2bc7e97`)

```
MYPYPATH=docs/eval uv run mypy docs/eval  ->  Success: no issues found in 2 source files
uv run mypy docs/eval  (control, same tree) ->  Found 7 errors in 1 file
```

The 7→0 pair reproduces in-worktree **after** the relic move, as the rider demanded.

**Why leg-scoped and not a global `[tool.mypy] mypy_path`** — preserved as the sidecar §Q1.2 ruled,
because it is the whole point: a global entry would make `import smoke_p8b` resolve inside EVERY
member, so a stray one in `loremaster` would type-check clean here and `ImportError` in the
deployed image. That is a mypy-**manufactured** false clear of the #131 shape — fixing 7 phantom
errors by installing a real one.

### B1 — deviation 2, both readings written out

The brief said *"add a leg-scoped `docs/eval` iteration"* **and** *"update the MEMBERS comment to
say the array is really typecheck roots"*. Those admit two builds:

- **(r1)** keep `MEMBERS` as-is and append a separate hard-coded leg after the loop. Then the
  array literally stays "the five roots", but **`docs/eval` is invisible to anything that parses
  `MEMBERS=(...)`** — and the sibling's `scripts/test_gated_ground.py` parses exactly that to
  derive typecheck roots (sidecar §Q3.3). Its LEG A would flag `docs/eval/smoke_p8b.py` as
  ungated, or demand an exemption row for a tree that IS gated.
- **(r2, chosen)** put `docs/eval` **in** `MEMBERS` and add a `declare -A MEMBER_MYPYPATH` map
  consulted per iteration. Still one iteration per root, still never merged, still leg-scoped
  (the env var exists only for that leg) — and the parsed array now tells the truth.

I chose r2 because it satisfies both of the brief's sentences at once and keeps the sibling's
derived guard honest. The distinction the sidecar actually ruled — **no global `mypy_path`
entry** — is preserved exactly. Flagging it because it is a sentence that admits two builds, not
because I felt uncertain.

**Stated bound:** `declare -A` needs bash ≥ 4.0 (2009). Fine on this Linux host; on a stock macOS
`/bin/bash` 3.2 it would fail. The shebang is `#!/usr/bin/env bash`, so a Homebrew bash wins if
present. Not closed, deliberately — saying so rather than discovering it later.

### B2 — SC2164, a real defect the new gate caught on its first run

`cd "$(dirname …)/.."` had no `|| exit`. It sits **directly beneath a nine-line comment** that
explains at length how a wrong cwd makes this script's output LIE — *3 errors reported vs 55 true,
"a false all-clear for two separate readers in one session"*. An unguarded `cd` that fails leaves
the shell in the caller's directory and the script runs on regardless, producing **that exact lying
output from the one direction the paragraph did not defend.** The prose knew; nothing enforced it.
Now `|| exit 1`. This is the packet's thesis in one line: a diagnosis is not an instrument.

---

## C — `scripts/registration_sites.py` (`0b8527f`)

`:!docs/eval` removed. Its stated reason ("archived records") was **false of half the tree** —
`docs/eval` holds the live deploy smoke.

**Measured with a POSITIVE CONTROL, because "no change" is also what a failed edit looks like:**

```
CONTROL 0 -- ':!docs/eval' absent from the live constant            : PASS
CONTROL 1 -- the grep now REACHES docs/eval                         : 3 mentions,
             ALL `loremaster`; lorerunes/lorescribe/loresigil 0 each
CONTROL 2 -- same grep, whole tree                                  : 1929 mentions
             (non-zero => a docs/eval zero is a RESULT, not a silence)
RESULT    -- docs/eval co-occurrence sites                          : 0
             whole-tree output byte-identical before and after (42 sites, 20
             incomplete, EMPTY diff)
```

The sidecar's zero reproduces. And the zero is **structural, not incidental**: a site needs ≥3
DISTINCT members within 4 lines, and only ONE distinct member's name occurs in that tree at all.
That reasoning is written into the constant's comment so it is re-derivable **from the script**
rather than from a report — the brief-base §1 citation preference, applied.

Also: the `_EXCLUDED` comment gave one shared reason for three unlike things; each now carries its
own. And a docstring paragraph now records that **hand-run status and non-zero exit on a healthy
tree are DELIBERATE** — it is a worklist, not a pass/fail gate; several sites are always
legitimately incomplete, so wiring its exit code into a gate would make that gate permanently red,
and a gate that is always red gets switched off. Previously inherited silently; now met
deliberately.

---

## D — `pyproject.toml` (`ed6f895`, and the dev-dep in `2bc7e97`)

`skills/lore-deploy/scripts` + `skills/lore-deploy/tests` → `testpaths` (117 tests, third instance
of the #199/#238 class). `shellcheck-py` → `[dependency-groups] dev`.

Two entries rather than one because the tests live in two sibling trees. Merge measured, not
assumed — the `tests.*` namespace collision that forces `typecheck.sh` to iterate per-root lives in
exactly this neighbourhood, and 8315 + 117 = 8432 closed exactly.

---

## E — the shell gate (`2bc7e97`)

### E1 — where it lives, and why

**Inside `scripts/typecheck.sh`**, not its own runner. Reasons, in order of weight:

1. **A separate `scripts/shellcheck.sh` would be an EIGHTH `.sh` that nothing runs** — a fresh
   instance of the class packet 44 exists to close. It would need the shell gate to check *it*,
   from outside itself.
2. There is exactly **one** command this repo's law names as a commit gate. A second runner is a
   second thing to remember, and *"a guard nobody runs is a hope with a filename"* has receipts
   here: both of packet 03b's instruments sat outside `testpaths`.
3. The file is **already** the static-analysis runner rather than a mypy-only script — ruling R9
   put a non-member (`skills`) in `MEMBERS` in packet 42. The header now says so.
4. **Self-gating**: `typecheck.sh` is itself tracked `.sh`, so the gate covers its own runner —
   which is how §B2's defect surfaced.

Counter-argument, acknowledged rather than hidden: mixing tools muddies the header's per-member
mypy rationale. Mitigated by a clearly separated section and a rewritten header.

The file set is **DERIVED** from `git ls-files -z '*.sh'`, never listed — a hand-list is the
artifact this repo has the most receipts against, and CLAUDE.md's own registration-site
enumeration was wrong four times *while the law about it was being written*. The derived set
covers the eighth script nobody has added yet.

### E2 — ⚠ DEVIATION 1: the brief's prescribed fix would have installed a false clear

The brief said: *"`contention_hunt.sh:54,71` (SC2086, quote `$CONTRACT`)"*. **`$CONTRACT` is a
newline-separated list of FOUR test files and its word splitting is DELIBERATE.** I measured
before deviating:

```
unquoted (as shipped): argc=4
quoted (brief's fix):  argc=1
array   (my fix):      argc=4
```

Then measured the downstream consequence end-to-end, because argc alone is not the harm:

```
uv run pytest --collect-only -q "<the collapsed single argument>" | grep -cE "^loremaster/tests/.*::"
  ->  0        (grep exit 1)
```

So under the brief's fix: `BASE_COLLECTED` becomes `0`; every iteration's `N` is `0`; the script's
own **"COLLECTED COUNT MOVED" abort never fires because 0 == 0**; and pytest's *"file or directory
not found"* does not match its `^[0-9]+ (failed|error)` detector — so **all thirty runs of a
concurrency hunt log as "green" over zero tests.**

That is a false clear installed by a linter fix, inside the instrument built to prevent a false
clear, defeating that instrument's own freeze detector. Fixed as a bash **array** with
`"${CONTRACT[@]}"`, which keeps four arguments and satisfies SC2086 for the right reason instead
of by accident. The reasoning is written into the file so the next person to "just quote it" reads
it first.

I am flagging this as a defect in the brief's prescription, not a complaint: the prescription was
reasonable on its face, and only execution distinguished it.

### E3 — the other fixes

`zero_test_store.sh` SC1090: the sourced path is a runtime variable **by design** (the caller may
point `SECRETS_ENV` anywhere), so a `# shellcheck source=/dev/null` directive, not a constant path
— making the path constant to satisfy a linter would trade a real capability for a clean report.
⚠ Non-obvious: the directive had to be split out of the one-liner `set -a; . "$X"; set +a`, because
on a compound line it binds to `set -a` and SC1090 still fires. Measured, then fixed.

### E4 — ⚠ DEVIATION 3: my own comment was falsified by my own mutation proof

My first draft of the anti-vacuity comment asserted that `shellcheck` with no file arguments
*"reads stdin and exits 0"*, making an empty set a silent green. **Measured: it prints its usage
summary and exits 3**, so the `elif` would have taken the FAILED branch and the gate would have
gone red regardless.

I had written a confident claim about a dependency's behaviour without running it — in a packet
about gates that lie, in the comment justifying an anti-vacuity guard. The guard **stays**, for two
reasons that survive the correction and are better than the one I invented: it **diagnoses** (else
the reader hunts for shell defects that do not exist when the real fault is a broken enumeration),
and it makes the invariant **ours** rather than a third-party tool's argument handling. The
correction is left visible in the file rather than tidied away.

---

## RIDER — mutation proofs, expected-RED declared BEFORE each run

Per the brief and CLAUDE.md's *"a mutation proof needs evidence the mutation LANDED"*. Every
expectation was written down before the command ran, and diffed both ways.

| # | mutation | declared expectation | observed |
|---|---|---|---|
| baseline | none | 6 mypy legs `OK` + `shellcheck OK (7)`, EXIT 0 | **exactly that** |
| **M1** | one type error appended to `docs/eval/smoke_p8b.py` | **only** `docs/eval FAILED`; other 5 `OK`; shellcheck `OK`; EXIT 1 | **exactly that** — `smoke_p8b.py:3256: error: Incompatible types…` |
| **M2** | SC2086 appended to `scripts/tree_fingerprint.sh` — **a file this wave never touches**, so the DERIVED reach is proven, not assumed | **only** `shellcheck FAILED`; 6 mypy legs `OK`; EXIT 1 | **exactly that** |
| **M3** | shell glob mutated to `'*.no-such-extension'` | `shellcheck ABORTED … BROKEN INSTRUMENT`; 6 mypy legs `OK`; EXIT 1 | **exactly that** — and it falsified my own comment (§E4) |

Restores: `cp -a` content backup → restore → **md5 match** (`423904ea…` for `smoke_p8b.py`) **and**
empty `git diff` for every mutated file. Never `git checkout --` (the tree carried uncommitted wave
work). Backup dir listed and hashed at capture time.

**"If step N silently no-opped, would step N+1 print something that reads as success?"** — asked of
the shell leg specifically. The enumeration step is the one whose empty output flows onward, and
it terminates in an explicit abort rather than in the `shellcheck` call. M3 is that path executed.

---

## F — the stale-prose sweep (`8015d22`)

Bare `git grep --fixed-strings testpaths` over all tracked files. **Every hit, individual verdict.**
The sweep runs AFTER item D deliberately: five of the sites are falsified by my own change.

| site (symbol/string) | verdict |
|---|---|
| `test_stats.py` `import smoke_p8b` comment | **FIX** — "docs/eval is not in testpaths (#238)"; #238 CLOSED that 2026-07-26 |
| `TestSmokeP8bPercentileUnits` docstring, premise | **FIX** — same retired fact, twice more |
| `TestSmokeP8bPercentileUnits` **RE-OPEN TRIGGER** | **DISCHARGED** — fired 2026-07-26, see below |
| `test_backoff_seam.py` `_BACKOFF_SITES` note, reason 1 | **FIX + RE-DERIVE** — claimed **150** collectable nodes never run in any gate vs **0** by a bare gated run. **Both false now: 352, and a bare gated run collects all 352.** Marked DISCHARGED in place, and explicitly noted the conclusion does NOT depend on it (reason 2 alone suffices) so nobody tidies away a still-valid warning |
| `docs/eval/test_smoke_p8b.py` module docstring | **FIX** — "covers the three workspace members only, so this file is NOT collected by a bare pytest run": false in **both** halves (four member trees + `scripts` + `docs/eval` + `skills/lore-deploy`; and it has been collected since #238) |
| `test_secret_typing.py` `_SCANNED_MEMBERS` note | **FIX** — "the residual is `testpaths` alone"; my item D closed it |
| `test_secret_resolution_seam.py` `_scanned_python_sources` docstring | **FIX** — same |
| `test_secret_resolution_seam.py::test_the_scan_reaches_the_skills_tree` comment | **FIX** — same |
| `scripts/typecheck.sh` MEMBERS comment (`skills` bullet) | **FIX** — my own new text, tightened to past tense |
| `addendum-F.md` §F12.2 | **RULED — DISCHARGED**, see below |
| `scripts/test_search_score_survey.py` | **LEAVE** — past tense, correct as history; and its *"#221 `scripts/` is not a `typecheck.sh` member"* is **still TRUE** (I did not add `scripts` to MEMBERS) |
| `lorerunes/tests/test_smoke.py` ×2 | **LEAVE** — still true |
| `pyproject.toml` "Until 2026-07-25…" | **LEAVE** — historical, true |
| `44-ungated-ground.md` ×3 | **LEAVE** — the packet's own premise; the lead closes it out |
| `CLAUDE.md` ×2, `INDEX.md` ×2 | **LEAVE** — historical and correct; also outside my writable set |
| `docs/design/…addendum-F-r2.md` F12.2 row | **FLAGGED, NOT EDITED** — §SURFACED ④ |
| `REPORT-builder-forgery-sites.md` ×2 | **FLAGGED, NOT EDITED** — §SURFACED ③ |

**No test was certifying the old world** — checked, not assumed: I grepped the test tree for
assertions on these strings and on the `150`. **Zero hits.** Every stale site was a comment or a
docstring; the `150` was a `#:` data-comment with no assertion behind it.

### F1 — #282's trigger: discharged, and the line I did NOT cross

The docstring's own trigger read: *"the day `docs/eval/` gains a `testpaths` entry, the trade
changes — the smoke's own suite would then be gated, an import break would be caught, and
consolidating could be reconsidered."* That day was 2026-07-26; it sat undischarged for three days.

I discharged the **stale premise**. I did **not** decide whether to consolidate the deliberate 4th
percentile copy, and that restraint is deliberate: the trigger says the trade *"could be
reconsidered"*, and the surviving half of #198's argument is untouched by gating — the smoke is a
**detachable** instrument pointed at a deployed image, and any new import is a new way for it to
fail to *start*. Gating watches the import from the repo; it does nothing for a detached run
against a container, which is the shape #238's own RULING-2 reversal was measured on. That is a
design decision about a settled trade and it belongs to the operator.

**Filed as #286** so it has a ledger address rather than living only in a docstring and this
report — a deferral without a named decision point is a can-kick.

---

## G — ledger (all via `lore_findings`, actor `builder-44-config-1`)

| # | action | substance |
|---|---|---|
| **#261** | **resolved** | `docs/eval` type gate landed; strategy arm 1; the 7→0 receipts; why arms 2 and 3 lost; the relic archive as part of the strategy, not tidying; M1 mutation proof |
| **#270** | **resolved** | **RATIFIES `d74e1da`**; "adopt the package" discharged as **`keep_with_trigger`, NOT a swap**; the byte-faithful reason the archived copies must not be edited; the trigger's address (arrival README); the residual door LEDGERED per the threat-model law. **Carries the lead's derived receipt verbatim: the corpus DOES contain escaped pipes in code spans at `consult-11ib/{honest,appendix}/07-determinism-and-run-receipt.md:52`, but `grade.py`'s `_DELTA_ROW` never matches that row and `check_coherence.py` keys on `cells[0]` while a mis-split corrupts only `cells[1:]` — so the published scoreboard is UNCORRUPTED, derived not assumed** |
| **#280** | **resolved** | testpaths entries; 8315→8432 collected; **8393 executed passed** reconciling to 8432; the R6-rider prose corrections |
| **#281** | **resolved** | it was RIGHT; **its body's staleness recorded as a note, body NOT edited** as instructed; both failure modes' fixes; **plus the #188 shape discovery** |
| **#282** | **resolved** | both halves; the broader sweep it prompted; **explicit statement of what is deliberately NOT decided** |
| **#283** | **resolved** | premise-dead ratified; **and its open question answered** — the scoreboard is uncorrupted; plus the sweep-protocol process note (`git log -- <area>` before minting scope from a body) |
| **#286** | **FILED (new)** | the #198 consolidation fork, with the two arms, my recommendation (arm 2: keep, and re-pin the bound on its *surviving* argument), and what is true regardless |

---

## SURFACED TO LEAD — questions, not verdicts

**① The #198 consolidation fork is live and needs an operator ruling.** Filed as **#286**. Arms:
consolidate the 4th percentile copy now that imports are watched, or keep it and **re-pin the bound
on its surviving argument** with a trigger that can actually fire. My recommendation is the latter
— an accepted bound whose stated reason has expired is indistinguishable from an unexamined one —
but this is a design call on a settled trade and it is yours, not mine. Do you want it ruled in
packet 44 or routed out?

**② `docs/plans/v2/INDEX.md:283` now dangles** (your file — I did not touch it). Exact edit:

```
-15. **Upstream report** of the mcp-builder TextContent serialization bug (docs/eval/2026-07-04-p8a-baseline.md:123).
+15. **Upstream report** of the mcp-builder TextContent serialization bug
+    (docs/plans/v2/receipts/2026-07-04-p8a/2026-07-04-p8a-baseline.md:123 — archived from
+    docs/eval/ 2026-07-29 at `439b55d`, bytes unchanged).
```

**③ `REPORT-builder-forgery-sites.md` is a TRACKED report at the repo root**, and it quotes the old
`MEMBERS=(lorerunes lorescribe loresigil loremaster skills)` array, which my change falsified. Per
the archive law it wants a `git mv` into `docs/plans/v2/receipts/<date>-<packet>/` rather than an
edit — but it is not mine and it is not in my writable set. It also blocks an image build while it
sits at the root. Do you want it archived in this packet's close-out?

**④ `docs/design/2026-07-25-floor-calibration-addendum-F-r2.md` F12.2 row** carries the identical
now-discharged raise (`| F12.2 (testpaths) | **SURVIVES UNCHANGED** | Null. Third report asking. |`).
It is not in my named writable set so I flagged rather than edited it. Exact edit: change the
verdict cell to `**DISCHARGED (execution axis) — see addendum-F §F12.2**` and leave the rest. Want
me to apply it?

**⑤ ⚠ #188 IS INVOCATION-SHAPE-DEPENDENT AND MATERIALLY SMALLER THAN BELIEVED.** Measured on
**committed ground** (via `git ls-files 'scripts/*.py'`, so a sibling's untracked in-flight file
cannot inflate it), 2026-07-29:

```
uv run mypy <tracked scripts/*.py>              ->  45 errors in 7 files   (reproduces the sweep exactly)
MYPYPATH=scripts uv run mypy <the same files>   ->  24 errors in 7 files
```

**21 of the 45 are import-resolution artifacts, not type defects** — the identical illusion that
made #261 look 6× its real size, with the identical fix (a leg-scoped `MYPYPATH`, which this packet
just gave `docs/eval`). #188 has been sized at "~half a session" against the 45. **24 is a different
job.** I wrote this into `addendum-F.md` §F12 and into #281's resolution so it survives at tracked
addresses, but I did not re-open #188 or file against it — that is your call. It may make #188
foldable rather than its own packet.

**⑥ The bash ≥ 4.0 dependency** in `typecheck.sh`'s `declare -A` (§B1). Not closed. Say the word and
I will convert it to a `case` if a stock-macOS run matters.

---

## TREE-MOVED — the sibling agent, and why my final suite total differs

⚠ **The worktree moved under me twice while I worked, both times from the parallel agent building
`scripts/test_gated_ground.py`.** Recorded because it contaminated two of my measurements and I
only caught it because a count refused to reconcile.

1. **A transient `ruff` red.** `uv run ruff check .` returned `Found 3 errors` at one point, then
   `All checks passed!` minutes later with no action by me — their file mid-write. **Not mine, and
   not a defect.**
2. **A transient collection ERROR.** `pytest --collect-only` reported `8432 tests collected, 1
   error` — `ModuleNotFoundError: No module named 'gated_ground'` from their untracked
   `scripts/test_gated_ground.py`. Timestamps: their file written **12:43:50**, my green full suite
   finished **12:41:43** — it did not exist during my 8393-passed run. It was a normal TDD RED
   state (contract before implementation); they have since landed `scripts/gated_ground.py` and
   collection is healthy. **I did not touch either file** (do-not-touch honoured).
3. **A contaminated mypy count.** My first `uv run mypy scripts` gave **58 errors in 8 files** —
   because mypy walks DIRECTORIES, not git, and swallowed their untracked file's 13 errors. Scoping
   to `git ls-files 'scripts/*.py'` gave **45 in 7**, reproducing the sweep exactly. §SURFACED ⑤'s
   numbers are the committed-ground ones. *This is why the committed-ground scoping matters and why
   I re-derived rather than inherited.*

**Consequence for the final receipt:** the headline `8393 passed / 8432 collected / EXIT 0` in
§GATES is the clean committed-ground measurement. A re-run at report time collects **8554** —
+122 from their now-landed untracked files — and that total is **not a claim I am making about my
own work**. Its outcome is in §FINAL-RERUN below.

---

## FINAL-RERUN

Re-run at report time, after every commit in this wave, with the sibling's now-landed
`scripts/{gated_ground,test_gated_ground}.py` present in the tree:

```
uv run pytest -n auto
====== 8515 passed, 36 skipped, 3 xfailed, 1 warning in 229.06s (0:03:49) ======
PYTEST_EXIT=0
```

**Reconciliation, both ways:**

- `8515 + 36 + 3 = 8554` = the collected count **exactly**. Nothing was collected-but-not-run.
- `8515 − 8393 = 122` = **exactly** the sibling's contribution (`8554 − 8432 = 122`). So the delta
  against my clean committed-ground run is fully accounted for by their files, and **zero** of it
  is movement in mine.
- **0 failed, 0 errors, exit 0** in both runs.

The sibling's 122 tests pass as well, so there is nothing outstanding for the lead to chase there.

**There are 0 failing tests, related or unrelated.** Both the committed-ground run
(8393 passed) and the whole-tree run (8515 passed) are clean.

---

## Commits

| sha | concern |
|---|---|
| `439b55d` | archive the six p8a relics + arrival README |
| `038db75` | repoint every live citation, per-hit verdict |
| `2bc7e97` | typecheck.sh: docs/eval leg + DERIVED shellcheck leg + the 4 shell fixes + shellcheck-py |
| `ed6f895` | skills/lore-deploy → testpaths |
| `0b8527f` | registration_sites.py: drop `:!docs/eval`, per-exclusion reasons, hand-run bound |
| `8015d22` | the testpaths stale-prose sweep, #282 discharged |

All staged with explicit paths (`git add <path>`), never `-a`. Standard trailers on each.
