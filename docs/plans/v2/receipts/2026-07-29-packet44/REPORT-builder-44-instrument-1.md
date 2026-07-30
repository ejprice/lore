brief-base v9 read
brief project v7 read
brief pkt44 v1 read

# REPORT-builder-44-instrument-1 — `scripts/gated_ground.py`, the per-axis gated-ground invariant

*All measurements 2026-07-29 in the worktree `.claude/worktrees/pkt44`, branch
`pkt44/ungated-ground`. My commits are **`7708a74`** (the implementation) and **`737ee6b`** (four
defects I found in my own work); the parent was `96816cc`, NOT the `a7cf955` my brief named — the
peer's loresigil R7 commit had already landed. The shipping bytes then landed in the lead's
**`ee1d753`**, which also tracked the contract. Every claim below is dated and SHA-scoped where it
matters; nothing here is a present-tense claim about a later tree state.*

---

## SUMMARY BLOCK

- `brief-base v9 read` · `brief project v7 read` · `brief pkt44 v1 read` — the comms tools DO
  exist for me; I registered, drained at every turn boundary, and drained empty each time (this is
  the counter-case to #287's two prior instances, both `tdd-contract` agents).
- **state: done-with-deviations.** `scripts/gated_ground.py` written. **171 passed on six runs**
  across four byte-states and two input sets · `./scripts/typecheck.sh` **EXIT=0** (its `scripts`
  leg type-checks this very file) · `ruff check .` clean · **full suite `8564 passed, 36 skipped,
  3 xfailed`, EXIT=0, reconciling exactly to 8603 collected** · and the RIDER: the guard's own
  verdict on this tree is **`GATED GROUND` … exit 0, 292/292 files classified, zero findings**
  (§2.2 verbatim). **The recursion is closed and MEASURED, not predicted**: at `ee1d753` the guard
  classifies its own instrument `TYPES=COVERED` and its own contract `TYPES=COVERED,
  EXECUTION=COVERED` (§2.3).
- deviation 1: **the contract's md5 is NOT the one my brief froze** — brief said
  `89cea408…`/2405 lines; disk is **`af4cdab58c9c24f72557d5cfb9ae38f3` / 2404 lines / 171
  collected**. The r5 report's own SUMMARY now agrees with the disk while its §7 still states the
  old value (§1). I built against the disk and edited no pin.
- deviation 2: **the contract author's throwaway reference build was still on disk when I started,
  and its author deleted it mid-flight during my first measurement run** — which is what produced
  a spurious `10 failed`. I did NOT read its body, so this build is an independent production
  (§1.2).
- deviation 3: **I did NOT cache the collector.** Cost measured: **129 s** for the 171 pins versus
  r5's ~46 s with a per-`repo_root` cache. Reasoning and the fork for you in §5.1.
- **⚠ deviation 4, the one to read first: MY CHANGE BROKE TWO REPO-WIDE ∀ INVARIANTS, and one was
  a REAL DEFECT the 171-pin contract could not see** — a `$`-anchored pattern validated with
  `.match`, so a finding number could carry a trailing newline into every rendered message. Both
  fixed, both re-measured, filed as **finding #289** (§3b).
- **⚠ decisions-needed (5), the first two load-bearing:**
  1. ~~`scripts/test_gated_ground.py` is UNTRACKED~~ — **RESOLVED WHILE I WAS WRITING**: you
     committed both files as `ee1d753`. Re-measured on the new input set, not predicted (§2.3).
     §5.2 is kept for its derivation, marked resolved.
  2. Collector caching: honesty vs 129 s in the standard gate (§5.1).
  3. The environment-read seam: I removed my read and pinned a bound instead of taking the design
     decision to allowlist it. Reverse that if you prefer the allowlist entry (§3b.2).
  4. The contract-md5 discrepancy — re-derive before anyone else inherits it (§1).
  5. Whether you want the reference build I preserved before its author deleted it (§1.2 — it is
     at an ephemeral path, so this expires with my session).
- `Packages considered:` §6 — six mechanisms, five `replace` with stdlib, one
  `keep_with_trigger`. No dependency added; the instrument imports the standard library only, as
  ruled.
- **lore's index is blind in this worktree (#125), so every structure question went to
  `git grep` / `git ls-files`.** Said out loud per the dogfood protocol; the LEDGER tools worked.
- receipt pointers: gates + rider §2 · what the build actually does §3 · **defects I found in my
  own work §4** · forks §5 · packages §6 · instruments pasted verbatim §7 · what I did NOT prove
  §8.

---

## 1. The two things that were not as briefed

### 1.1 The contract is not at the md5 my brief froze — and the r5 report contradicts itself

| source | md5 | lines | collected |
|---|---|---|---|
| my spawn brief | `89cea4086f8ae54ee36dcd986e0d1dd6` | 2405 | 171 |
| `REPORT-contract-44-gatedground-1-r5.md` §7 bound 1 | `89cea4086f8ae54ee36dcd986e0d1dd6` | — | — |
| `REPORT-contract-44-gatedground-1-r5.md` SUMMARY BLOCK | `af4cdab58c9c24f72557d5cfb9ae38f3` | 2404 | 171 |
| **the file on disk, re-derived by me twice** | **`af4cdab58c9c24f72557d5cfb9ae38f3`** | **2404** | **171** |

Mechanism, from mtimes: the r5 report was written at `20:24:25`, the contract was modified at
`20:25:39` — *after* the report — and the report's SUMMARY was then edited (my own `grep` at
`20:26` still read `89cea408…` on that line; it read `af4cdab…` minutes later). So the contract
author was still working when the brief quoting it was written, and **§7's "frozen at" line was
never updated to match its own SUMMARY.** The brief inherited the stale half.

**What I did: nothing to the contract.** I built against the bytes on disk, re-derived the md5
before and after my definitive runs (unchanged), and report the discrepancy rather than picking a
reading. The collected count — 171 — is identical either way, which is why this cost nothing but
is still worth your re-derivation before a cold audit inherits it.

### 1.2 The throwaway reference build was live, and it vanished mid-measurement

`scripts/gated_ground.py` **already existed** when I started (23 685 bytes). Its own docstring
says it is a *"THROWAWAY REFERENCE BUILD … DELETED at the end of that run … must never be
committed"* and *"⚠ NOT A DESIGN TO CLONE"*, and r5 §7 bound 1 claims it was already deleted. It
was not, yet.

My first measurement run against it reported `10 failed, 161 passed` with a
`FileNotFoundError` on the instrument's own path — **not a contract defect: its author deleted the
file while my run was in flight** (a following single-class run failed at import with
`ModuleNotFoundError: gated_ground`, and `find` then showed the file gone). I record this because
a `10 failed` line in a transcript is exactly the kind of number that gets inherited as evidence
of something.

**I did not read its body** — only the docstring header I saw while checking what the file was.
That was deliberate: the packet's value here is a second, independent production graded by the
contract, and cloning an ungraded reference build would have thrown that away while looking
identical at the gate. So this implementation is derived from the contract, the r5 report's §1–§5,
the sidecar's §Q3, and adversary-2's §3.

I preserved a byte copy before it disappeared. **It is at an ephemeral path, so it is
unrecoverable once my session ends** — brief-base forbids citing such a path as durable, and I am
not committing another agent's throwaway. If you want it, say so now (decision 4).

---

## 2. Gates — every claim with its command, and the RIDER

⚠ **READ §2.2 FIRST FOR THE SHIPPING RECEIPTS.** The runs in §2 and §2.1 graded
`4f244bbfec532049efd2ceaaa36bb7ce` — the bytes BEFORE the two §3b fixes. They are kept because
they are what establishes that *the 171-pin contract was green with the §3b.1 defect open*, which
is the whole point of that section. **The shipping bytes are `f6245142291bd97edc56602f8dcaf212`
(1065 lines), and §2.2 carries their receipts.**

Bytes under test in this subsection: `scripts/gated_ground.py` md5
`4f244bbfec532049efd2ceaaa36bb7ce`, 1049 lines, re-derived unchanged after the runs. Contract md5
`af4cdab58c9c24f72557d5cfb9ae38f3`.

```
uv run pytest -q scripts/test_gated_ground.py -p no:randomly     171 passed in 129.09s   (pre-commit)
uv run pytest -q scripts/test_gated_ground.py -p no:randomly     171 passed in 129.41s   (post-commit, RUN1_EXIT=0)
```
Both definitive runs against the final bytes, plus the full suite, are in §2.1. **171 collected,
171 passed, 0 failed, 0 skipped — the counts reconcile with no residue.**

```
./scripts/typecheck.sh
  Success: no issues found in 3 source files      typecheck: lorerunes OK
  Success: no issues found in 27 source files     typecheck: lorescribe OK
  Success: no issues found in 35 source files     typecheck: loresigil OK
  Success: no issues found in 171 source files    typecheck: loremaster OK
  Success: no issues found in 12 source files     typecheck: skills OK
  Success: no issues found in 2 source files      typecheck: docs/eval OK
  Success: no issues found in 21 source files     typecheck: scripts OK
  typecheck: shellcheck OK (7 tracked .sh)
  TYPECHECK_EXIT=0      (captured via ${PIPESTATUS[0]})
```
**The packet's thesis applied to itself, mechanically:** that `scripts` leg's *21 source files* are
the 19 tracked ones plus my instrument and its contract. My file is inside the canonical gate, and
it is green — it is not gated by anyone remembering to run it.

```
uv run ruff check .        All checks passed!    RUFF_EXIT=0
```

### The RIDER — the guard's verdict on THIS repository, verbatim

```
=== VERDICT (verbatim render) ===
GATED GROUND — every tracked module is registered with the type gate, and every tracked test-shaped file is one the collector reaches.
=== exit_code === 0
=== is_clean === True
=== blind_sources === ()
=== findings === 0
=== classified files === 290 of tracked 290        (291 after my commit)
    TYPES:     {'COVERED': 269, 'EXEMPT_ARCHIVED_RECEIPTS': 21}
    EXECUTION: {'COVERED': 151, 'NOT_APPLICABLE': 139}
=== typecheck_roots === ['lorerunes', 'lorescribe', 'loresigil', 'loremaster', 'skills', 'docs/eval', 'scripts']
=== testpaths === ['lorerunes/tests', 'lorescribe/tests', 'loresigil/tests', 'loremaster/tests', 'scripts', 'docs/eval', 'skills/lore-deploy/scripts', 'skills/lore-deploy/tests']
=== member_mypypath === {'docs/eval': 'docs/eval', 'scripts': 'scripts'}
=== unmodelled mypy === []
=== patterns === ['test_*.py', '*_test.py']
=== collected files === 149
```

**It flags nothing, and I checked that this is a result rather than an artifact** — the instrument
that proves it is pasted in §7.1. Post-commit, the guard classifies its own file
`scripts/gated_ground.py` as `TYPES=COVERED, EXECUTION=NOT_APPLICABLE`, by the `scripts` root and
by nothing about its name (the contract pins that no literal of its own path appears anywhere in
its source, and that pin is green).

### 2.1 Definitive chain against the FINAL bytes — verbatim

The first pair of runs graded bytes I then edited (§4), so a second pair was run after the last
edit, with the md5 taken **before and after** so the receipt is bound to the bytes it graded:

```
=== BYTES UNDER TEST ===
4f244bbfec532049efd2ceaaa36bb7ce  scripts/gated_ground.py
af4cdab58c9c24f72557d5cfb9ae38f3  scripts/test_gated_ground.py
1049 scripts/gated_ground.py
=== DEFINITIVE RUN A ===
171 passed in 129.30s (0:02:09)
A_EXIT=0
=== DEFINITIVE RUN B (determinism) ===
171 passed in 131.30s (0:02:11)
B_EXIT=0
=== POST-RUN BYTES (unchanged?) ===
4f244bbfec532049efd2ceaaa36bb7ce  scripts/gated_ground.py
```

**Four runs of 171/0 in total** on these bytes (two pre-edit, two post-edit), and the two
definitive ones are byte-bound. `findings are ordered deterministically` is itself one of the pins,
so the equality of the two runs is asserted inside the suite as well as observed across it.

### 2.2 THE SHIPPING RECEIPTS — post-§3b-fix bytes `f6245142291bd97edc56602f8dcaf212`

One chain, md5 taken before and after so the receipt is bound to the bytes it graded, pasted
verbatim:

```
=== BYTES BEFORE ===
f6245142291bd97edc56602f8dcaf212  scripts/gated_ground.py
af4cdab58c9c24f72557d5cfb9ae38f3  scripts/test_gated_ground.py
1065 scripts/gated_ground.py
=== CONTRACT RUN 1 ===        171 passed in 128.32s (0:02:08)      R1_EXIT=0
=== CONTRACT RUN 2 ===        171 passed in 127.93s (0:02:07)      R2_EXIT=0
=== TYPECHECK ===             Success: no issues found in 21 source files
                              typecheck: scripts OK
                              typecheck: shellcheck OK (7 tracked .sh)
                              TYPECHECK_EXIT=0
=== RUFF ===                  All checks passed!                   RUFF_EXIT=0
=== FULL SUITE ===            8564 passed, 36 skipped, 3 xfailed, 1 warning in 220.81s (0:03:40)
                              SUITE_EXIT=0
=== BYTES AFTER ===
f6245142291bd97edc56602f8dcaf212  scripts/gated_ground.py
=== GUARD VERDICT ===
GATED GROUND — every tracked module is registered with the type gate, and every tracked test-shaped file is one the collector reaches.
exit 0 | clean True | blind ()
bounds declared: 9
```

**The full suite reconciles EXACTLY, with no residue: 8564 + 36 + 3 = 8603 collected** — and 8603
is `8432 + 171`, the pre-existing collected count plus this contract's pins, both measured
separately. Zero failures: the two invariants my file broke (§3b) are closed.

Independently observed on these same bytes before the chain:

```
uv run ruff check scripts/gated_ground.py                     All checks passed!    (RUFF=0)
MYPYPATH=scripts uv run mypy scripts                          Success: no issues found in 21 source files
uv run pytest -q -p no:randomly \
  loremaster/tests/test_anchored_pattern_seam.py \
  loremaster/tests/test_secret_resolution_seam.py             89 passed in 8.28s   (the two pins that caught me)
python -c "…"  bounds NOT verbatim in docstring: []  ·  THREAT_MODEL in __doc__: True  ·  9 bounds, triggers unique
python -c "…"  Exemption(finding='#188\n')  ->  REJECTED   ·  control Exemption(finding='#188') -> constructs
```

### 2.3 ⚠ THE RECURSION IS NOW FULLY CLOSED — measured, not derived

While I was finalising, the lead committed **`ee1d753` "the derived gated-ground invariant —
contract + implementation"**, which carries my final bytes (`git show HEAD:scripts/gated_ground.py`
md5 `f6245142…`, identical to the working tree) **and tracks the contract.** That discharges the
§5.2 escalation and, more importantly, **changes the invariant's INPUT SET** — so it earns its own
measurement rather than my prediction:

```
scripts/gated_ground.py       tracked -> TYPES=COVERED, EXECUTION=NOT_APPLICABLE
scripts/test_gated_ground.py  tracked -> TYPES=COVERED, EXECUTION=COVERED
GATED GROUND … | exit 0 | clean True | tracked 292
```

Both fates are exactly what §5.2 derived before the commit existed. The guard now judges **its own
instrument and its own contract**, by the `scripts` root and the `scripts` testpath — not by any
literal of its own name, which remains pinned absent from its source.

⚠ **Consequence for my own receipts, stated rather than buried:** every run in §2, §2.1 and §2.2
was taken while the contract was UNTRACKED, i.e. against a 290/291-file input set rather than
today's 292.

**What IS measured on the 292-file set** is the block above: the guard's own verdict, the two
files' fates, `clean True`, `exit 0`. That is the assertion
`TestTheRealRepositoryIsFullyGated::test_no_committed_python_is_ungated_on_either_axis` evaluates,
computed directly.

**And the full 171-pin re-run on the new input set is now measured too**, observed to completion:

```
=== contract run with BOTH files as tracked ground (HEAD=ee1d753) ===
171 passed in 128.95s (0:02:08)
EXIT=0
```

So the 171/0 result holds on the input set that includes the instrument AND its contract as
committed ground. **Six runs of 171/0 across four byte-states and two input sets**; no run in this
report is a prediction.

---

## 3. What the build does, and the six places a wrong build would have differed

- **PER-AXIS, not binary.** `LEG A` is membership of a typecheck root parsed live from the single
  line-anchored `MEMBERS=(…)` declaration; `LEG B` is *measured collection*. Nothing computes a
  union.
- **LEG B is collector-derived**, via a `sys.executable -m pytest --collect-only -q` **subprocess**
  over `repo_root`, never the live session's items. It tolerates exit `{0, 5}` (`5` is
  `NO_TESTS_COLLECTED`, a result about a tree, not a broken instrument — r5 §3.2) and refuses
  anything else. It carries **its own anti-vacuity leg that the contract does not require**: exit
  `0` with no parsed node id is `GuardIsBlind`, because that combination means the output is not
  the shape this guard reads — the one way a silent parse change could return "nothing was
  collected" and read as a clean tree.
- **Blindness is monotone to the SERVED surface.** `classify` raises; `ungated_ground` is the ONE
  place `GuardIsBlind` is caught, and it catches it only to carry it outward as
  `Verdict.blind_sources`. A non-empty set is never `is_clean`, never exits zero, and renders a
  distinct opening line. This kills adversary-2's four survivors by construction rather than by a
  reader-level pin.
- **Membership is `PurePosixPath.is_relative_to`, at every call site** — the typecheck-root site,
  the testpath site, the receipts site (both axes) and the exemption site. `str.startswith`
  appears nowhere in the file.
- **No exemption table, no roster, no frozen sha** (F1). `EXEMPTIONS` ships `()`; the *validation
  rules* survive so a future proposed row meets a specification instead of a blank page. The one
  law-backed exemption is `ARCHIVED_RECEIPTS_ROOT`, and it is **doubly anchored**: absent from
  ruff's `extend-exclude`, or matching no tracked file, the whole verdict refuses.
- **Failure messages interpolate the PARSED scope**, never a hardcoded list, and carry the
  registration/execution disclaimer as one contiguous sentence plus the two sanctioned outs
  (gate-cover it, or escalate — *"there is no exemption mechanism, deliberately"*). Paths are
  rendered unambiguously, so a committed path carrying a newline and a forged header line cannot
  parse as a second finding.

---

## 3b. ⚠ MY CHANGE BROKE TWO REPO-WIDE INVARIANTS, AND ONE OF THEM WAS A REAL DEFECT

**Read this section before anything else in the report.** The full suite came back
`2 failed, 8562 passed` — and **both failures were mine, named by file and line**. Disclosed as a
deviation per brief-base §2 (a regression my own in-scope change directly causes may be fixed
minimally and must be disclosed prominently).

```
FAILED loremaster/tests/test_anchored_pattern_seam.py::TestNoAnchoredPatternValidatedWithMatch::test_every_anchored_match_use_is_allowlisted
  scripts/gated_ground.py:219 — _FINDING_NUMBER = '^#\\d+$'

FAILED loremaster/tests/test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::test_every_environment_read_is_the_entry_point_or_allowlisted
  scripts/gated_ground.py::collected_test_files
```

Neither is a pre-existing failure: the offender lists name **only** my file, so the tree was clean
on both before it landed. **My file is the first new module to land in `scripts/` since F1 brought
that tree under these ∀ scans, and both scans caught it within one suite run** — which is the
packet's own thesis arriving from the other direction.

### 3b.1 The anchored-pattern seam caught a REAL defect the 171-pin contract cannot see

`_FINDING_NUMBER = re.compile(r"^#\d+$")` was validated with `.match`. Python's `$` also matches
immediately **before a trailing newline**, so `.match` accepts `"#188\n"` — finding #210's exact
shape. Constructed, before the fix:

```
  .match("#188\n")     -> True   <- accepts it
  .fullmatch("#188\n") -> False  <- rejects it
  CONSTRUCTED a row whose finding is '#188\n' - the hole is real
```

**Why this matters beyond a lint:** a `finding` is interpolated into failure messages, so a row
carrying a line break injects a line into every render of it — the forgery class the contract
pins for PATHS, reappearing through the one field the contract's malformed-row matrix does not
have a newline case for. The 171 pins were green with the hole open. **A different invariant, in
another member's test tree, found what this packet's own contract structurally could not.**

Fixed: `.fullmatch`, with the reason in a comment beside it. Re-measured after the fix — rejected,
and the positive control (a well-formed `#188`) still constructs.

**Filed as finding #289**, because the *provenance* is the lesson and outlives the fix. Two
generalisations in it that are yours to rule on:

1. **A contract's malformed-input matrix should carry a trailing-newline case for every field it
   interpolates into served text, not just for paths.** Here the path case WAS pinned — a path was
   known to be hostile stored text — while a finding number was assumed safe because it *looks*
   like a closed charset. Same class, one field over.
2. **Bringing a tree under an existing repo-wide ∀ scan pays out immediately and invisibly.**
   Nobody planned for #210's seam to grade packet 44's instrument; F1 making `scripts` a typecheck
   root did it for free, on the first new file to arrive.

### 3b.2 The environment-read seam: I removed the read rather than take a design decision

`collected_test_files` built its child environment as `{**os.environ, "PYTEST_ADDOPTS": ""}`, to
stop an inherited option changing the invocation it measures. That is an environment read outside
this repository's ONE secret-resolution entry point, and **the pin says in its own message that a
new allowlist entry is a DESIGN decision, not a lint fix** — and that file is outside my writable
set either way.

So I did the opposite of allowlisting: **deleted the environment read** (and the now-unused `os`
import), and **pinned the residual as a ninth stated bound**,
`inherited-pytest-environment`, with its own re-open trigger — per the *when you cannot close a
hole, pin it* law. The consequence is not silent: if an inherited `PYTEST_ADDOPTS` changes the
collector's output shape, the anti-vacuity leg (exit zero + no parsed node id) refuses as blind
rather than serving a wrong verdict.

**Both seam suites after the fix: `89 passed`.** If you would rather have the allowlist entry than
the bound, that is your call and it is a one-line change in a file I may not touch.

---

## 4. Defects I found in my OWN work, and fixed before shipping

I record these because a build that goes 171/0 on its first run is exactly the situation where the
builder should be least trusted, and because three of the four are natural-language surfaces — the
class this repository has the most receipts against.

1. **Two stated-bound summaries were sentence FRAGMENTS that satisfied their pin.** To fit the
   line-length gate I had trimmed `registration-not-execution` to *"…does not prove mypy or pytest
   ran, or"* and `collection-convention` to *"…is invisible to pytest"*. Both are substrings of the
   module docstring, so `bound.summary in gg.__doc__` passed — while the thing a reader "meets" was
   a fragment. That is a false gate in the instrument's own mouth, self-inflicted. Fixed: every
   summary is now one complete sentence on one docstring line.
2. **A free numeric in taught prose (R8).** The docstring said *"three of the four historical
   instances of this defect class were HALF-gaps"* — a count I did not derive, inherited from the
   sidecar. Replaced with the citation that IS durable: *"(#188, #233 and #261 each in a different
   direction)"*.
3. **A blindness message that was false in a narrow case.** An absolute `MEMBERS` or `testpaths`
   entry (`/home` is in the contract's own matrix) was reported as *"widens to the whole tree"* —
   it does not; it *escapes the repository*. The pin only asserts the entry is named, so this would
   have shipped. Now both cases are stated.
4. **`ungated_ground` derived its inputs TWICE** — once directly and once via `classify` — which
   silently doubled the collector cost per served verdict. Restructured so each entry point derives
   once.
5. **A characterization I could not support.** The docstring said the half-gap instances were
   *"#188, #233 and #261 each in a different direction"*. The *half-gap* claim is the sidecar's and
   the contract's; *"each in a different direction"* was mine, derived from nothing. Cut to the bare
   citation.

**And the honest scoreboard on this section: I found four of these myself, and the two in §3b I did
NOT** — a repo-wide invariant in another member's test tree found those, one of them a live defect.
That is the split this repository's verification law predicts, arriving on schedule.

---

## 5. Forks for you — I did not settle these

### 5.1 The collector costs 129 s per contract run, and I chose honesty over the cache

Measured: the 171 pins take **129 s** (r5's reference build, caching per `repo_root`, reported
~46 s). The cost is ~12 whole-checkout collects at ~5.8 s plus ~60 fixture collects.

**I did not cache, deliberately.** A cache keyed on `repo_root` returns a stale answer after any
mutation of that tree, and this instrument's entire property is that it never certifies what it
cannot see (#136's shape). The honest cache key would have to include every file that can affect
collection — which is the whole tree, i.e. not closable. Under `-n auto` the 171 pins distribute
across workers, so the wall-clock hit to the standard gate is far below 129 s.

**Your call**, and r5 §3.3 already routed the same question to you: if the cost is unacceptable,
the lever is *fewer fixture repositories that call `classify`* (a contract change, not mine) or an
explicitly-scoped cache with its staleness stated on the served surface — never a silent one.

### 5.2 ✅ RESOLVED at `ee1d753` — kept because the DERIVATION is the receipt

*Written while the contract was untracked; you committed it before I finished, and §2.3 carries the
measurement that confirms every fate predicted below. Preserved verbatim rather than deleted,
because a prediction that was later measured true is worth more on the record than a tidy report.*

`scripts/test_gated_ground.py` is `??` in `git status`. `tracked_python_files` walks git's index,
so **the file is invisible to the invariant.** The recursion packet 44 exists to close is
currently closed for the half I committed and open for the half I may not touch.

This is not a guess about what happens when it lands — it is derived: `is_under` puts it under both
the `scripts` typecheck root and the `scripts` testpaths entry, and the collector already reports
it (`collected files === 149` includes it; the contract's own
`test_the_collector_sees_this_very_contract` asserts exactly that and is green). So on commit its
fates are `TYPES=COVERED, EXECUTION=COVERED` and the tree stays clean.

**I could not do it: the file is in my DO-NOT-TOUCH set, and `git add` is touching it.** Recommend
`git add scripts/test_gated_ground.py` in the wave close-out, then re-run the contract once —
committing it changes the invariant's INPUT SET, which is exactly the kind of change that deserves
its own green run rather than an assumption.

### 5.3 Unpinned freedoms I had to resolve — aim the adversary here first

Each is a choice the contract does not pin, so each is mine and ungraded:

| choice | what I did | the alternative |
|---|---|---|
| `COVERED` vs `EXEMPT_ARCHIVED_RECEIPTS` on TYPES | COVERED wins | receipts win, hiding a receipts tree that a root now covers |
| non-test file under the receipts root, on EXECUTION | `NOT_APPLICABLE` (it is not collectible) | `EXEMPT_ARCHIVED_RECEIPTS` |
| how many blind sources a `Verdict` carries | the FIRST refusal only | all of them, gathered per reader |
| a repo with zero tracked `.py` | `GuardIsBlind` | an empty list, which is the vacuity that reads clean |
| the collector's environment | clears `PYTEST_ADDOPTS`, so it models the COMMITTED configuration | inherits it, so one shell's env can change the verdict |

### 5.4 Noticed, outside my scope, raised as questions

- The contract's `TestTheInstrumentIsSelfContained` docstring cites
  `TestThisInstrumentRidesTheTypeGateItself.test_a_file_entry_importing_a_sibling_declares_the_mypypath_its_leg_needs`
  — a class r5 §2 records as **DELETED**. A dangling citation inside the frozen contract; harmless
  to behaviour, and exactly the natural-language-consistency class no gate checks. Do you want it
  filed?
- `scripts/__pycache__/` exists in the worktree and is untracked; `git status` does not show it, so
  it is ignored. Noting it only because a stale `__pycache__` is #140's third poison mode and I saw
  one beside a file that had just been deleted under me.
- **Eight `REPORT-*.md` at the worktree root are UNTRACKED** — derived from `git status --short`
  against `git ls-files 'REPORT-*.md'`: seven from prior packet-44 agents (`adversary-1`,
  `adversary-2`, and the contract's base + `r2`/`r3`/`r4`/`r5`) plus mine.
  `REPORT-builder-44-scripts-debt-1.md` and `REPORT-builder-forgery-sites.md` are already tracked.
  Per the archive law the untracked ones need `git mv` into
  `docs/plans/v2/receipts/2026-07-29-packet44/` before any image build — and until then the working
  tree is the ONLY copy of five contract revisions' reasoning, which is the state the
  commit-at-natural-boundaries rule exists to prevent.

---

## 6. Packages considered

| mechanism | library evaluated | what I READ | verdict |
|---|---|---|---|
| does pytest reach this file? | `pytest --collect-only` via `sys.executable -m pytest` subprocess | ran it against this checkout and against fixture repos; measured exit `0` (items), `5` (`NO_TESTS_COLLECTED`), non-zero on a conftest that cannot import; measured the node-id output shape and the 5.8 s cost | **replace** — supersedes a parse of `[tool.pytest.ini_options]`, which cannot close an open set (ruled directive D1) |
| manifest parsing | `tomllib` (stdlib) | signature + the same parser production reads with | **replace** a hand parser |
| the bash `MEMBERS` array | `shlex.split` (stdlib) | measured against `str.split` on a quoted entry containing a space: 2 tokens vs 3 — the case the contract pins | **replace** `str.split` |
| path membership | `PurePosixPath.is_relative_to` (stdlib) | behaviour on the contract's 12-row matrix, incl. sibling-prefix and root-level paths | **replace** `str.startswith` (which adversary-1 measured passing the whole contract at three sites) |
| `python_files` glob matching | `fnmatch.fnmatch` (stdlib) | matches pytest's own convention for these patterns | **replace** hand globbing |
| tracked-file enumeration | `git ls-files -z` subprocess **vs** GitPython / pygit2 | not adopted, and not on preference: the instrument is **stdlib-only BY RULING** (it must typecheck as its own `MEMBERS` iteration with no `MYPYPATH`, and a gate that imports what it grades goes down with it, reporting nothing — which reads clean) | **keep_with_trigger** — trigger: the stdlib-only ruling is lifted; then a real git binding beats parsing `-z` records |

No dependency was added. The instrument's imports are `fnmatch os re shlex subprocess sys tomllib
collections.abc dataclasses enum pathlib types` — all in `sys.stdlib_module_names`, which the
contract derives rather than allowlists.

---

## 7. Instruments — pasted verbatim, because they establish load-bearing claims

Neither is committed: `scripts/` additions are outside my writable set. Per brief-base §1 they
survive here rather than dying with my session.

### 7.1 The discrimination probe — "is the CLEAN verdict a result, or an artifact?"

The contract proves discrimination in `tmp_path` fixtures. This asks the sharper question about
*this checkout*: derive the real scopes once, narrow exactly one, and require the affected files to
turn UNGATED. A build that ignored its inputs stays clean in every leg.

```python
"""DISCRIMINATION PROBE (builder self-check, real tree, in-process)."""
import dataclasses, sys
from pathlib import Path
sys.path.insert(0, "scripts")
import gated_ground as gg

root = Path(".").resolve()
scopes = gg._derive(root)

def ungated(s):
    return {(v.path, a.name) for v in gg._classify(s, ()) for a in gg.GateAxis
            if v.fates[a] is gg.Fate.UNGATED}

print("CONTROL (real scopes, unperturbed) ungated pairs:", len(ungated(scopes)))

narrowed = dataclasses.replace(scopes, typecheck_roots=tuple(r for r in scopes.typecheck_roots if r != "scripts"))
hits = ungated(narrowed)
print("LEG A  drop 'scripts' from MEMBERS      ->", len(hits), "ungated; all under scripts/:",
      all(p.startswith("scripts/") and a == "TYPES" for p, a in hits))

narrowed = dataclasses.replace(scopes, typecheck_roots=tuple(r for r in scopes.typecheck_roots if r != "docs/eval"))
hits = ungated(narrowed)
print("LEG A  drop 'docs/eval' from MEMBERS    ->", len(hits), "ungated; all under docs/eval/:",
      all(p.startswith("docs/eval/") for p, a in hits))

narrowed = dataclasses.replace(scopes, collected=frozenset())
hits = ungated(narrowed)
print("LEG B  collector reaches nothing        ->", len(hits), "ungated; all EXECUTION:",
      all(a == "EXECUTION" for p, a in hits))

victim = sorted(scopes.collected)[0]
narrowed = dataclasses.replace(scopes, collected=scopes.collected - {victim})
print(f"LEG B  silence one real file           -> {sorted(ungated(narrowed))}   (victim {victim})")

narrowed = dataclasses.replace(scopes, testpaths=tuple(t for t in scopes.testpaths if t != "loremaster/tests"))
print("LEG B  drop 'loremaster/tests' testpath ->", sorted(ungated(narrowed)))
```

Output, at `7708a74`:

```
CONTROL (real scopes, unperturbed) ungated pairs: 0
LEG A  drop 'scripts' from MEMBERS      -> 19 ungated; all under scripts/: True
LEG A  drop 'docs/eval' from MEMBERS    -> 2 ungated; all under docs/eval/: True
LEG B  collector reaches nothing        -> 148 ungated; all EXECUTION: True
LEG B  silence one real file           -> [('docs/eval/test_smoke_p8b.py', 'EXECUTION')]   (victim docs/eval/test_smoke_p8b.py)
LEG B  drop 'loremaster/tests' testpath -> [('loremaster/tests/conftest.py', 'EXECUTION')]
```

**Read the last two rows carefully, because one of them is a bound and not a result.** Dropping the
`loremaster/tests` testpath flags only that tree's `conftest.py`, NOT its test modules — because
`collected` is still the set the REAL configuration produced, and for test modules collection (not
registration) is the check. That is a limit of perturbing a derived structure rather than the
config file, and it is precisely the `conftest-collection-hooks` bound made visible: a conftest is
registration-bounded, everything else is measured. The faithful version — rewrite `pyproject.toml`
and re-run the collector — is what the contract's own fixtures do, and they are green.

### 7.2 The exemption-validation probe — "rejected for the RIGHT reason?"

The contract asserts only that `InvalidExemption` is raised, so a validator that rejected
*everything*, or rejected all seventeen rows by one over-broad rule, would pass every case for the
wrong reason.

```python
"""PROBE: is each malformed exemption row rejected for its OWN reason?"""
import sys
from pathlib import Path
sys.path.insert(0, "scripts")
import gated_ground as gg

base = dict(root="docs/consult", axis=gg.GateAxis.TYPES, finding="#188",
            reason="standing disposition: its own work item, config half first",
            reopen_trigger="the #188 cleanup lands; delete this row and the leg goes live")
cases = [{"finding": ""}, {"finding": "188"}, {"finding": "see the ledger"},
         {"reopen_trigger": ""}, {"reopen_trigger": "   "}, {"reason": ""},
         {"reason": "45 measured errors, its own work item"},
         {"reason": "standing disposition since 2026-07-26"},
         {"root": ""}, {"root": "/absolute/tree"}, {"root": "../outside"}, {"root": "."},
         {"root": "./"}, {"root": " "}, {"reopen_trigger": "TBD"},
         {"reopen_trigger": "when we get to it"}, {"reason": "x"}]
for case in cases:
    try:
        gg.Exemption(**{**base, **case})
        print(f"  ACCEPTED (BAD!) {case}")
    except gg.InvalidExemption as error:
        field = next(iter(case))
        print(f"  {field:15} {case[field]!r:42} -> {str(error)[:96]}")
print("POSITIVE CONTROL (well-formed row):", gg.Exemption(**base).root, gg.Exemption(**base).axis.name)
```

Result: **seventeen rejections across five distinct rules, each naming the field that is actually
wrong** — finding-not-a-finding-number (×3), trigger-names-no-condition (×3, incl. `"TBD"`),
trigger-does-not-cite-its-finding (×1), reason-not-a-phrase (×2), reason-carries-a-numeral (×2),
root-is-blank (×2), root-widens-or-escapes (×4) — and the positive control constructs. No blanket
rejection.

---

## 8. What I did NOT prove — the honest limit of this report

- **I ran no `scripts/mutation_proof.py` wave.** §7.1 is a discrimination probe on a derived
  structure, not a source mutation with declared expected-RED node ids. The reason is the tree, not
  the clock: mutating source here requires either a scratch copy — **forbidden for this worktree by
  #284, since a copy's `.git` file makes `git add` mutate the real worktree** — or mutating the
  real tree with a content backup, which I judged the lead's to authorise while a peer session
  commits nearby. **Say the word and I will do the real-tree-with-backup form.**
- **r5 §5's list of unproven pins is not discharged by my green run.** A build satisfying the
  contract is satisfiability, not discrimination, and that list is the third adversary's target,
  unchanged by anything here.
- ~~I did not verify the guard's verdict after the contract is committed~~ — **now measured** at
  `ee1d753` (§2.3): both fates match the derivation exactly, and the 171 pins are green on that
  input set.
- Every fate precedence in §5.3 is my judgement, graded by nobody yet.
- The `129 s` and `5.8 s` figures are single measurements on this host under concurrent load from a
  peer session; treat them as an order of magnitude, not a benchmark.
