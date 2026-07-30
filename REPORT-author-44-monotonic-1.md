brief-base v9 read
brief project v7 read
brief pkt44 v2 read

# REPORT-author-44-monotonic-1 — revision 6 of the gated-ground invariant: the QUANTIFIER, not the instances

*All measurements taken **2026-07-29** in the worktree `.claude/worktrees/pkt44`, branch
`pkt44/ungated-ground`, from parent `310658e`; my commits are **`7ad1b0a`** (both scripts) and
**`4120ccb`** (this report). Shipping bytes: `scripts/gated_ground.py` md5
**`ed6840d2fcf27fd169e5d082237e0e86`** (1461 lines) · `scripts/test_gated_ground.py` md5
**`197f6868e6cf3b9a620b0f91657c2f15`** (4024 lines, **314 collected**). Every claim below is dated
and scoped to those bytes; nothing here is a present-tense claim about a later tree.*

---

## SUMMARY BLOCK

- `brief-base v9 read` · `brief project v7 read` · `brief pkt44 v2 read` — the `lore_comms` /
  `lore_findings` tools DO exist for me: registered, `brief_get pkt44` read, drained at every turn
  boundary (empty each time). **Counter-case to #287**, like `builder-44-instrument-1`.
- **state: done-with-deviations.** R9 and R10 implemented as a DESIGN change, then attacked by me:
  **21 wrong builds built · 15 killed · 6 SURVIVED · 5 of those 6 fixed and re-killed · 1 proven
  BEHAVIOURALLY EQUIVALENT** (§4). Four of the six survivors were REAL missing pins **in my own
  contract**, found only because I built the wrong implementations rather than reasoning about them.
- **Gates.** `pytest -q scripts/test_gated_ground.py` → **314 passed in 79.80s** and **314 passed
  in 87.67s** (two runs, determinism) · `./scripts/typecheck.sh` **EXIT=0** (`${PIPESTATUS[0]}`) ·
  `uv run ruff check .` **All checks passed, EXIT=0** · full suite `-n auto` →
  **8707 passed, 36 skipped, 3 xfailed**, reconciling **exactly** to **8746 collected** (§6).
- **RIDER — the guard's verdict on THIS repository, verbatim:** `GATED_GROUND` · `exit_code 0` ·
  `is_clean True` · 0 findings · `blind_sources ()` · **292 of 292 tracked `.py` classified**.
  Render: *"GATED GROUND — every tracked module is registered with the type gate, and every tracked
  test-shaped file is one the collector reaches."* Nothing was flagged, so nothing was suppressed.
- **R10 cost, re-derived (§5).** Same 314 tests: **146.26 s uncached → 79.80 s cached**, measured by
  disabling the memo lookup in an isolated scratch copy. Direct component costs on this checkout:
  **~6.0 s** per collector subprocess vs **~29 ms** per fingerprint. ⚠ The brief's "129 s → ~46 s"
  was measured over **171** pins; I did not inherit it.
- **deviation 1:** the contract grew from 171 to **314** pins and I rewrote parts of it — the
  operator ruled this a design change and the brief granted both files. **deviation 2:** MP-3 needed
  three attempts; the first two FAILED for instrument reasons `mutation_proof.py` caught (§5.3) —
  reported rather than tidied. **deviation 3:** I found and fixed **four defects in my own contract
  by running it** (§3.4) before any wrong build existed. **deviation 4:** my first `git commit -F -`
  landed a message I did not write, carrying **another session's `Claude-Session` trailer**; I
  detected it by reading `git log`, re-committed both with the authored messages (`git reset --soft`,
  nothing pushed), and verified the committed bytes are byte-identical to the tested md5s. **E5.**
- **decisions-needed (5):** §7 — E1 the `PYTEST_ADDOPTS` env-read fork (needs a file outside my
  writable set) · E2 a file-vs-directory `MEMBERS` ruling I resolved one way · E3 what to do with
  adversary-3's E1/E2/E5 residuals · E4 whether the wrong-build harness should be committed ·
  **E5 a commit whose message and `Claude-Session` trailer were not mine** (detected and corrected).
- `Packages considered:` **§8** — 6 mechanisms surveyed by READING installed source:
  `_pytest.pathlib.fnmatch_ex` → **replace_with_adapter + oracle pin** (the row three prior surveys
  got wrong) · `mypy.defaults.CONFIG_NAMES` + `_pytest.config.findpaths.locate_config` → **replace**
  the hand-list · `hashlib.blake2b` → **replace** · `scripts/tree_fingerprint.sh` → **bespoke, does
  not do the job** (it fingerprints the TRACKED tree; pytest collects untracked files) ·
  `functools.lru_cache` → **bespoke** (the key must be a content fingerprint, not the argument) ·
  `configparser` → **not needed**, presence beats parsing.
- **lore's index is blind in this worktree (#125)**, so every structure question went to `git grep`
  / `git ls-files` / AST. Said out loud per the dogfood protocol; the ledger tools worked.
- receipt pointers: what changed §2 · the design and why §3 · **my own wrong builds §4** · mutation
  proofs + cost §5 · gates §6 · **escalations §7** · packages §8 · instruments verbatim §9 · what I
  did NOT prove §10.

---

## 1. Capability check (brief-base §4)

| demanded | what I have | what I did |
|---|---|---|
| `ToolSearch` the `lore_comms` / `lore_findings` tools; register; `brief_get name=pkt44`; drain each turn | both present | all done; drain empty every time. R9/R10 read from the pkt44 brief itself, not only from the spawn message |
| worktree, `git grep` (lore index blind — #125) | yes | used throughout; every structural answer is a `git grep`/AST derivation, said out loud |
| never `cp -a`/`scratch_copy.sh` this worktree (#284) | — | scratch built by `git archive HEAD` + `tar` + a fresh `git init`; **`.git` asserted to be a DIRECTORY** and the gitdir printed (§4.1) |
| `scripts/mutation_proof.py` with declared RED node ids | present | 5 proofs, §5 |

No demand in my brief was unmeetable.

---

## 2. What changed

### 2.1 `scripts/gated_ground.py` — the served surface is ONE derivation (R9)

| symbol | change |
|---|---|
| `VerdictState` | **NEW.** Three states, and **the member's VALUE IS the exit code** — there is no second table for the mapping to drift in |
| `IncoherentVerdict` | **NEW.** `Verdict.__post_init__` refuses findings-AND-blind-sources: the incoherent cell is **unrepresentable**, not forbidden |
| `Verdict.state` | **NEW.** THE classifier. `is_clean` is an identity test on it, `exit_code` is its value, `render()` is a `match` over it — so a fourth state is a mypy error, not a silent fall-through to the clean sentence |
| `GuardIsBlind.door` | **NEW.** Every refusal carries a stable identity, which is what makes the failure set DERIVABLE instead of written down |
| `_blind(door, what)` | 26 call sites now pass a literal door identity; 2 more added → **28 doors, 28 unique**, cross-checked by two independent derivations (AST and textual) |
| `SHADOWING_CONFIGURATION_FILENAMES` + `shadowing_configuration_files()` | **NEW.** LEG A's `mypy.ini` hole (#107's shape) closed by REFUSING when a higher-precedence config file exists |
| `unmodelled_mypy_configuration` | now refuses an **ABSENT** `[tool.mypy]` table too — without it mypy's search falls through to `setup.cfg`, an ancestor, then `~/.config/mypy/config` |
| `_matches_collection_pattern` | **NEW.** A port of `_pytest.pathlib.fnmatch_ex`, pinned against installed pytest as an ORACLE |
| `_is_test_shaped(..., repo_root=)` | now reconstructs the ABSOLUTE path pytest is handed, because the matcher branches on it |
| `_COLLECTOR_MEMO` + `_collector_input_fingerprint` | **NEW (R10).** Memo keyed on a content fingerprint of the collector's inputs; an unreadable input REFUSES rather than yielding a partial key |
| `_derive` | consults `shadowing_configuration_files` **before any configuration file is read**, and calls `member_mypypath` **for its refusal alone** — see §3.3 |
| `STATED_BOUNDS` | 9 → **12**: `gate-configuration-precedence`, `collector-memoisation`, `collection-pattern-platform` |

### 2.2 `scripts/test_gated_ground.py` — 171 → 314 pins

New classes: `TestTheServedSurfaceIsOneDerivation` · `TestTheDerivedFailureSetIsFullyProbed`
(**34 constructed broken states** over 28 doors) · `TestLegBTestShapednessEqualsPytests` ·
`TestTheCollectorIsMemoisedAndTheMemoInvalidates` · `TestEveryStatedBoundIsTrueOfItsMechanism`.

Deleted: the four-value `test_every_blind_state_serves_bytes_distinct_from_healthy`
parametrization — **two lists that must agree are one list**, and that list WAS the defect.

Repaired vacuous/false pins (adversary-3 §3.4, §6): the exemption default pin now checks
**identity of the default ∀ entry points that take `exemptions`**; the precedence pin now passes a
real row; the load-bearing predicate got a fixture table with a live row and a dead one;
`test_every_parsed_typecheck_root_is_a_directory` → `…_exists_in_this_checkout` (its assertion
forbade what its own comment permitted) plus a new GUARD-level pin that a single-file root is legal
and covers only itself.

Corpse sweep — every hit from adversary-3 §6, with a verdict:

| ref | disposition |
|---|---|
| C1 FROZEN-ROSTER paragraph citing a deleted class | **deleted**, replaced by a past-tense retirement note |
| C2 two dangling `:class:`/`:meth:` citations | **re-pointed** at pins that exist; the TYPES-axis obligation they claimed is now actually pinned (P-11) |
| C3 file-vs-directory comment citing a deleted class | **re-pointed** at the new guard-level pin |
| C4 `# the frozen roster is only as sound as the sha it names` | **deleted** |
| C5 "the pinned exemption root" rationale | **rewritten** — the property is unchanged, the reason is now the two GATES that tree carries |
| C6 `#188 exemption` in a served failure message | **deleted** |
| C7 false gate, inverted | **fixed** (renamed + split, above) |
| C8 fixture comments asserting the opposite of the asserted fate | **rewritten** |
| C9 `if scripts were ever added to MEMBERS` | **rewritten** (it already is) |
| C10 docstring offering a third way out that a pinned string denies | **deleted**, with the contradiction named |
| C11–C15 | LEGITIMATE, unchanged (agreed with adversary-3) |

**Residual sweep, bare and anchor-free** (`roster|frozen|ls-tree|exemption row|#188|EXPECTED_EXEMPTION|SCRIPTS_EXEMPTION`),
every hit individually verdicted: lines 13 (historical provenance) · 44–45 (my retirement note,
past tense) · 117 (ditto) · 179 (explains an R4 fix) · 347 (C12, legitimate) · 1104 (my
correction note) · 1319–1332 (the empty-table pin's own reasoning) · 1348–1508 + 1386–1402
(`finding="#188"` inside FIXTURE rows — real finding number, never shipped) · 2274 (explains the R4
fix) · 2369 (contrasts a bound with an exemption) · 2572 (my C10 correction). **A dangling-citation
checker over every `:class:`/`:meth:`/`:data:` reference reports none** (§9.3).

---

## 3. The design, and why each piece is the shape it is

### 3.1 R9 — what "unrepresentable" can and cannot mean, stated honestly

**It is achieved for one thing and approximated for the other, and the difference matters:**

- **UNREPRESENTABLE, literally.** A verdict holding findings AND naming unreadable inputs cannot be
  constructed: `IncoherentVerdict` raises. `Verdict(findings=(f,), blind_sources=("x",))` →
  `IncoherentVerdict: a verdict cannot hold 1 finding(s) AND name 1 unreadable input(s)…`. The
  four-cell product of the two fields therefore has **three** legal cells, not a convention. And
  the exit code cannot disagree with the state because **it is the state's own enum value**.
- **NOT literally unrepresentable, and I will not claim it is: the SOURCE.** Anyone editing
  `gated_ground.py` can write anything; no structure in Python prevents `is_clean` from being
  rewritten to read a field. The strongest available form is what I built: **ONE classifier, and a
  MUTATION proof that every served answer follows it** — `test_every_served_answer_moves_when_the_
  one_classifier_moves` replaces `Verdict.state` and requires every public non-field member to
  change, quantified over the members the dataclass ACTUALLY has rather than over three someone
  listed. WB2 (adversary-3's survivor) dies on it, and MP-2 proves it fires (§5).
  *Routing is not sharing; this is the pin that tells them apart.*

### 3.2 The failure set is DERIVED, and coverage is a CHECKED VARIABLE

The previous wave's hole was a **list**: four strings plus three named entry points, 6 of 26 states
covered, 17 false clears at 171/171. Revision 6 reads the door set **out of the instrument's own
AST** (`blind_doors_declared_by_the_instrument`) and diffs it BOTH ways against 34 constructed
states:

- a door with **no** constructed state → RED (*"a new door was added without a state"*);
- a state naming **no** declared door → RED (*"a probe aimed at nothing, or a renamed door"*);
- a refusal constructed **without** the door helper → RED (`test_no_refusal_bypasses_the_one_door_helper`),
  which is the clause that stops the derivation degenerating into a name list;
- the derivation has a **second-derivation control**: the AST count must equal a textual count of
  `_blind(` calls (28 == 28). *An AST walk that silently matched a subset would make every ∀ here
  quantify over less than it claims, and nothing else could see it.*

And because a door set can only ever describe refusals the guard HAS, a second derivation covers
the other direction: `test_every_dependency_the_guard_names_is_probed` derives the input addresses
from the instrument's own constants (`*_RELATIVE_PATH` + the shadowing filenames) and demands a
probe for each — **that is where a dependency with NO door shows up**, which is exactly how
`mypy.ini` had been invisible.

### 3.3 LEG A's `mypy.ini` hole — closed by refusing, and the argument for checking only `repo_root`

READ, in the installed dependency, not from docs or memory:
`mypy/defaults.py` → `CONFIG_NAMES = ['mypy.ini', '.mypy.ini']`, `SHARED_CONFIG_NAMES =
['pyproject.toml', 'setup.cfg']`; `mypy/config_parser.py::_find_config_file` iterates
`CONFIG_NAMES + SHARED_CONFIG_NAMES` and returns the FIRST that parses, and for a CONFIG_NAMES
entry it does **not** require a `[mypy]` section — so **an empty `mypy.ini` wins and `[tool.mypy]`
is ignored entirely**. pytest's `locate_config` declares
`["pytest.toml", ".pytest.toml", "pytest.ini", ".pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg"]`
— **four** names beat the manifest, not one.

The guard refuses on the PRESENCE of any of those six. Three reasons, in order of weight:
1. **Allowlist the safe.** The safe set is one file. Modelling six sidecars' CONTENT is a second
   place to be wrong about another tool's precedence rules.
2. **Checking `repo_root` alone is sufficient, and this is an argument rather than an assumption:**
   both tools walk upward and stop at the first ACCEPTED candidate, and the runner invokes mypy
   from the repository root while the collector runs with `cwd=repo_root`. So once the manifest at
   the root is accepted — which the guard now guarantees by refusing when the modelled tables are
   absent — no ancestor and no user-level file is consulted at all.
3. **`setup.cfg` / `tox.ini` are deliberately NOT refused**: they come AFTER the manifest in both
   orders, so refusing them would be a false positive, and *a gate that refuses honest code is a
   gate that gets switched off.*

The instrument carries the order as a stdlib-only constant; the contract **re-derives it from both
installed tools on every gate run** (`test_the_instruments_precedence_constant_matches_what_the_
tools_declare`), pytest's list by AST-reading the literal out of `locate_config`'s source because
it is a function-local with no constant to import.

### 3.4 Four defects in my own contract, found by RUNNING it

Reported because they are the counter-example to reasoning: none of these was visible from reading.

1. **A false positive on the CORRECT build.** My new message-scopes pin (P-5) flagged `scripts` as a
   leaked scope — because the message legitimately names `scripts/typecheck.sh` and this checkout
   also declares `scripts` as a scope. A pin that reddens on honest output is how a gate gets
   switched off; fixed by removing the guard's own ADDRESSES from the haystack, which leaves every
   other occurrence intact.
2. **Three pins failed because a directory did not exist.** `FixtureRepository` runs `git init` with
   `cwd` set to the root it is handed, so `_minimal_repository(tmp_path / "control")` raises
   `FileNotFoundError` — and one of the three was the **healthy CONTROL every byte-diff is measured
   against**, so a fixture defect read as 26 broken states. Fixed with ONE `_repository_beside`
   helper, so the mkdir cannot be forgotten at a fourth call site.
3. **A "control" that was arithmetic, not a property.** My door-derivation control compared the door
   count to the number of constructed STATES (`>=`) — but several states legitimately share a door,
   so the comparison held for a reason unrelated to what it claimed. Replaced by a genuine SECOND
   derivation (AST vs textual), diffed for equality.
4. **A perturbation that did not perturb.** My memo-invalidation row wrote `norecursedirs=["tests"]`
   and the tree collected exactly as before — `norecursedirs` prunes RECURSION, not an explicitly
   named `testpaths` entry. A row whose perturbation is inert proves the memo let go when nothing
   had changed. Fixed by nesting the pruned directory, which is also why the pre-existing §6-hole
   pin uses `probes`.

### 3.5 A defect the new instrument found in the SHIPPED build

`member_mypypath`'s duplicate-declaration refusal was **unreachable from any verdict**: nothing in
`_derive` called that reader, so the door existed and no consumer of the served surface could ever
meet it. The door-coverage pin is what surfaced it (a declared door with no reachable state), and
`_derive` now consults the reader **for its refusal alone**. *A reader nobody consults is the same
shape as a guard nobody runs* — the instrument's own words, now enforced rather than written.

---

## 4. MY OWN WRONG BUILDS — 21 built, and 6 of them survived

### 4.1 Provenance (#284 / #140), asserted not assumed

```
worktree .git file contents: gitdir: /home/ejprice/PycharmProjects/lore/.git/worktrees/pkt44
scratch gitdir: /tmp/author44/refrepo/.git
PROVENANCE OK: .git is a DIRECTORY (not a worktree file)
gg.__file__ = /tmp/author44/refrepo/scripts/gated_ground.py
PROVENANCE ASSERTED: the instrument under test is the scratch copy
tracked .py: 292        scratch verdict: GATED_GROUND exit 0
```

Built by `git archive HEAD | tar -x` + a fresh `git init` — **never `cp -a`, never
`scratch_copy.sh`**, because this worktree's `.git` is a FILE naming the real gitdir and a copy's
`git add` would mutate the real index. `.venv` is a symlink to the worktree's; disclosed
consequence: `import loremaster` inside the scratch resolves to the original checkout, which is
irrelevant here because the module under test is `gated_ground`, imported from the scratch
`scripts/` and asserted above. Every patch anchor must match **exactly once** or the harness aborts,
and every run's collected total is compared to the baseline's 314 — a run that does not collect 314
is reported NOT COMPARABLE rather than as a survivor.

### 4.2 Round 1 — against the contract as I first wrote it

`REF => 314 passed in 76.96s [collected total: 307]` (baseline at that revision), then:

| # | wrong build | result | verdict |
|---|---|---|---|
| WB1 | blindness reported only for 5 named doors (adversary-3's survivor) | 57 failed | killed |
| WB2 | served surface ignores findings (adversary-3's survivor) | 2 failed | killed |
| WB3 | the classifier prefers findings over blindness | **307 passed** | ❗SURVIVED |
| WB4 | exit code becomes a SECOND mapping that agrees today | 1 failed | killed |
| WB5 | the incoherent cell is permitted again | 1 failed | killed |
| WB6 | the shadow check covers mypy's sidecars only | 12 failed | killed |
| WB7 | the precedence reader is computed and never consulted | 18 failed | killed |
| WB8 | the matcher reverts to basename-only `fnmatch` | 3 failed | killed |
| WB9 | the memo is keyed on the root alone | 7 failed | killed |
| WB10 | the memo ignores the root | **307 passed** | ❗SURVIVED |
| WB11 | the fingerprint swallows an unreadable input | 3 failed | killed |
| WB12 | the fingerprint covers config files only | **307 passed** | ❗SURVIVED |
| WB13 | the shadow refusal names no file | 6 failed | killed |
| WB14 | an absent `[tool.mypy]` table is accepted | **307 passed** | ❗SURVIVED |
| WB15 | `member_mypypath` is no longer consulted | 3 failed | killed |
| WB16 | the whole-tree test reverts to a spelling denylist | 12 failed | killed |
| WB17 | a door identity becomes a computed value | 2 failed | killed |
| WB18 | a refusal bypasses the door helper | 3 failed | killed |
| WB19 | the clean render over-claims one axis | 1 error | killed (NOT COMPARABLE — a syntax break, reported as such) |
| WB20 | test-shapedness uses the process cwd | **307 passed** | ❗SURVIVED |
| WB21 | the memo is written BEFORE the anti-vacuity check | **307 passed** | ❗SURVIVED |

**21 built · 15 killed · 6 survived.**

### 4.3 The six survivors, adjudicated — and four were real

| survivor | verdict | what it cost me |
|---|---|---|
| **WB12** fingerprint covers config only | **REAL MISSING PIN.** Every invalidation row perturbed a file INSIDE a collection root, which the directory walk covers alone. The tracked-`.py` population exists for a module OUTSIDE every testpath whose content decides whether collection SUCCEEDS | new pin: a conftest imports a module outside every testpath; break it and the guard must refuse instead of serving the memoised healthy answer |
| **WB14** absent `[tool.mypy]` accepted | **REAL MISSING PIN.** My own new refusal had no state constructing it — every fixture writes that table, and the refusal SHARES a door with the unmodelled-setting one, so door coverage was satisfied without it | new broken state, with an assertion that the removal actually landed |
| **WB20** test-shapedness uses the cwd | **REAL MISSING PIN.** The EIGHTH call site of the repo_root property, arriving with the matcher. Separator-free patterns answer from the basename, and my one separator-bearing fixture matched under BOTH roots — arithmetic alignment again | new pin discriminating on the fixture root's own basename, with a CONTROL showing the pattern must not match under the real cwd |
| **WB21** memo written before the anti-vacuity check | **REAL MISSING PIN, and the nastiest.** The first ask refuses correctly AND caches the empty answer; every later ask reads the cached emptiness and returns a clean "nothing collected". The memo converts a refusal into a false clear, and only a pin that asks TWICE can see it | new pin: two asks on the same still-broken tree must both refuse |
| **WB3** classifier prefers findings over blindness | **INERT — dead code, which an auditor is entitled to call a defect.** The only input distinguishing the two orders is the incoherent cell, which cannot be constructed | made REACHABLE and pinned as deliberate defence-in-depth (via `object.__setattr__`, the only route past the refusal), so if the construction refusal is ever relaxed blindness still dominates |
| **WB10** memo ignores the root | **BEHAVIOURALLY EQUIVALENT — not a wrong build.** The fingerprint hashes ABSOLUTE paths, so it already distinguishes two byte-identical trees at different roots; the key's root component is redundant defence in depth | strengthened the pin to assert the property WHERE IT LIVES (two twin trees must have different fingerprints) and documented which half of the key is load-bearing, with the re-pin trigger |

### 4.4 Round 2 — the same six against the strengthened contract

```
REF => 314 passed in 79.37s   [collected total: 314]
WB3_state_prefers_findings_over_blindness            1 failed, 313 passed  killed
WB10_memo_ignores_the_root                           314 passed            ❗SURVIVED
WB12_fingerprint_covers_config_only                  1 failed, 313 passed  killed
WB14_absent_mypy_table_accepted                      3 failed, 311 passed  killed
WB20_test_shapedness_uses_the_process_cwd            1 failed, 313 passed  killed
WB21_memo_written_before_the_anti_vacuity_check      1 failed, 313 passed  killed

6 built · 5 killed · 1 survived
```

**WB10 is reported as a survivor and NOT as a kill, deliberately.** I could have contorted a pin to
detect a difference with no observable consequence; that would be a pin fitted to a mutation rather
than to a property. The honest disposition is in the table above and in the code, with the trigger
that would make it load-bearing.

### 4.5 adversary-3's two headline holes, re-measured

| hole | before | after |
|---|---|---|
| **WB1** — 5 named doors honoured, the rest swallowed into a clean verdict (17 false clears at 171/171) | survived | **57 failed** — every door has a constructed state and the ∀ is over the AST-derived set |
| **WB2** — `findings=1` served with `is_clean=True`, `exit_code=0` and the clean sentence | survived | **2 failed**; and its incoherent half is now **unrepresentable** (`IncoherentVerdict` raises) |
| **F-A** — `MEMBERS=(loremaster ./)` accepted, every file COVERED, bytes identical to healthy | live in the reference build | closed in the shipped build and now pinned over ONE shared spelling constant used by **three** call sites (both axes' scope pins and the exemption-row matrix) |
| **F-B** — a committed `mypy.ini` switches LEG A off, guard serves healthy bytes | live in the reference build | closed: 6 shadowing filenames × 3 pins, derived from the vendors' own orders |

---

## 5. Mutation proofs and the R10 measurement

### 5.1 Five declared-RED proofs, observed column non-blank

Every declared set was derived by **grep over `pytest --collect-only`**, never transcribed from a
result. `scripts/mutation_proof.py` diffs BOTH ways (unexpected reds AND declared reds that stayed
green) and restores byte-exact.

| # | mutation | declared RED | observed | verdict |
|---|---|---|---|---|
| MP-1 | a door identity is renamed (`git-command-failed` → `…-renamed`) | 2 | 2, exactly | **HELD** |
| MP-2 | `is_clean` re-derives the verdict privately (`return not self.blind_sources`) | 2 | 2, exactly | **HELD** |
| MP-3 | the memo is keyed on the root alone | 8 | 8, exactly | **HELD** (3rd attempt — §5.3) |
| MP-4 | the matcher reverts to basename-only `fnmatch` | 3 | 3, exactly | **HELD** |
| MP-5 | the precedence reader is computed and never consulted | 18 | 18, exactly | **HELD** |

### 5.2 R10 — the cost, and the price paid for it

| measurement | value |
|---|---|
| one collector subprocess, this checkout | **~6.0 s** |
| one input fingerprint, this checkout (182 `.py`, 9.06 MB) | **~29 ms** |
| `scripts/test_gated_ground.py`, 314 tests, **memo disabled** | **146.26 s** (1 failed — the memo pin itself, correctly) |
| the same 314 tests, memo live | **79.80 s** |

⚠ The brief's *"129 s → ~46 s"* was measured over **171** pins and I did not inherit it; the numbers
above are for 314. Measured by disabling the memo LOOKUP in the isolated scratch copy, never in the
worktree.

**The price, paid:** 6 invalidation pins (4 input classes + a change outside every collection root +
a refusal that must never be cached) and a wrong-instance pin at the fingerprint. An unreadable
input REFUSES rather than yielding a partial key, because a partial key collides with the healthy
one — a stale answer wearing a fresh receipt. Non-`.py` files under a collection root are excluded
deliberately and the reason is read from pytest's source, not guessed: only `.py` files become
collected modules, and `__pycache__` mtimes move DURING a run, so hashing them would thrash the memo
it exists to key.

### 5.3 MP-3 failed twice before it held, and both failures are receipts

1. **Attempt 1 — the mutation landed BROKEN.** My `--replacement` had no trailing newline, so it
   joined with the following line: `SyntaxError`, `1 error in 0.20s`, **NOT COMPARABLE**. The
   instrument refused it (exit 4) instead of reporting `1 error` as a proof.
2. **Attempt 2 — my declared set was STALE.** 7 declared, 8 observed: the extra was a pin I had
   added *after* declaring. Exit 4, both-ways diff naming it.
3. **Attempt 3 — HELD**, with the set re-derived by a stated RULE over `--collect-only` (*every
   invalidation pin in the memo class, plus every state reaching the fingerprint's own door*).
   ⚠ **Bound, stated because it cannot be closed mechanically:** the re-declaration happened after
   I had seen attempt 2's output. The rule is written down so a reader can check the set against it
   rather than against my word.

*This is finding #194's shape twice in one session, in the session using the instrument built for
it — and the instrument caught both. A guard nobody runs is a hope with a filename; this one ran.*

---

## 6. Gates

```
$ uv run pytest -q scripts/test_gated_ground.py -p no:randomly        # run 1 of 2
314 passed in 79.80s (0:01:19)

$ uv run pytest -q scripts/test_gated_ground.py -p no:randomly        # run 2 of 2 (determinism)
314 passed in 87.67s (0:01:27)

$ ./scripts/typecheck.sh
typecheck: lorerunes OK … lorescribe OK … loresigil OK … loremaster OK … skills OK …
typecheck: docs/eval OK
typecheck: scripts OK
typecheck: shellcheck OK (7 tracked .sh)
TYPECHECK EXIT=0                      # ${PIPESTATUS[0]}

$ uv run ruff check .
All checks passed!
RUFF EXIT=0

$ uv run pytest -n auto -q ; echo "FULL_SUITE_EXIT=$?"
8707 passed, 36 skipped, 3 xfailed, 1 warning in 222.43s (0:03:42)
FULL_SUITE_EXIT=0
$ uv run pytest -q --collect-only
8746 tests collected
# 8707 + 36 + 3 = 8746 == collected. EXACT reconciliation, no failures, no errors.
# (Run twice: 225.68s without an exit capture, then 222.43s with one. Same counts both times.)
```

**There are 0 failing tests unrelated to our present scope.**

RIDER — the guard on this repository, verbatim (§SUMMARY): `GATED_GROUND`, exit 0, 292/292
classified, zero findings, `blind_sources ()`. It flagged nothing, so nothing was suppressed.

---

## 7. SURFACED TO LEAD — questions, not decisions

**E1 — the `PYTEST_ADDOPTS` fork, and it needs a file I may not touch.**
The memo's key is filesystem state. An inherited `PYTEST_ADDOPTS` **changed inside one process**
would alter what the collector answers without moving the key. Closing it means one line —
`os.environ.get("PYTEST_ADDOPTS", "")` in the fingerprint — which would break
`loremaster/tests/test_secret_resolution_seam.py::TestSecretResolutionHasExactlyOneEntryPoint::
test_every_environment_read_is_the_entry_point_or_allowlisted`, **outside my writable set**
(`builder-44-instrument-1` hit the same wall and removed its env read for the same reason). I
therefore PINNED the miss instead: the `collector-memoisation` bound states it with a named re-open
trigger. *The exact edit a lead would make:* an `ENV_READ_ALLOWLIST` entry keyed
`scripts/gated_ground.py::_collector_input_fingerprint` with the reason *"an operational knob read
as a CACHE KEY, never as configuration — the inherited value still decides what is measured"*.
**Your call: allowlist entry, or keep the pinned bound?**

**E2 — I resolved adversary-3's E4 one way; say if you want the other.**
`test_every_parsed_typecheck_root_is_a_directory` asserted `is_dir()` while its own comment
permitted a single FILE root — a false gate, inverted, that would go RED the day anyone followed the
prose. I **relaxed the tree assertion to `exists()`** (renaming it for what it actually checks) and
**added a guard-level pin that a file root is legal and covers only itself**, because the instrument
permits it and an unpinned permitted behaviour is untested code. The alternative adversary-3
recommended was deleting the prose and forbidding file roots. Both are defensible; mine keeps a
mechanism that closed this instrument's own recursion before F1 made it unnecessary.

**E3 — adversary-3's E1/E2/E5 are unaddressed by me and are yours to route.** E1 (should the
reference build's deletion become a verified receipt?), E2 (r5's mutation-proof count contradicting
itself), E5 (nothing pins that `typecheck.sh`'s shell leg stays live — **I closed the mechanical
half**: `test_the_file_types_bound_agrees_with_the_runners_shell_leg` derives the bound's claim from
the runner, so if the shellcheck leg is deleted the bound must change with it).

**E4 — the wrong-build harness and the memo cost prober are the instruments this report rests on.**
Both are pasted verbatim in §9 per brief-base §1. They are not committed, because `scripts/` is my
writable set only for the two named files. **Do you want `wrong_builds.py` committed to `scripts/`?**
It is the only artifact that can re-run §4 — and adversary-3's seven probes evaporated with its
scratch tree for exactly this reason (#278).

**E5 — a commit message I did not write, carrying another session's provenance trailer.**
Measured 2026-07-29: `git -c … commit -q -F -` with a heredoc produced a commit whose message was
NOT the one on stdin. The message that landed was factually accurate about this work (my numbers, my
survivor counts) but its subject differed from mine and its trailer read
`Claude-Session: …/session_01H5xrNX8kEVso8NEjahzsTV` — **a different session id from mine**
(`…/session_01K9LrKALqEHarYKEw4ZdDqM`). I caught it by reading `git log -1 --format=%B` rather than
trusting the commit, re-committed both (`git reset --soft HEAD~2`, then `-F <file>` instead of
`-F -`; nothing had been pushed) and verified the committed bytes are byte-identical to the tested
md5s. **Why this is worth your attention rather than a shrug:** this repo's citation law makes a
provenance line load-bearing, and a trailer naming the wrong session is a false citation that no
gate checks — the same class as the natural-language surfaces `CLAUDE.md` has the most receipts
against. *Question: do you want this filed as a finding (my `lore_findings` tools work), and should
briefs stop recommending `-F -`?*

**Noticed, outside my items:** `scripts/test_forgery_door_sweep.py` (R8, peer-owned) is untouched.
`docs/plans/v2/INDEX.md` and `CLAUDE.md` untouched.

---

## 8. `Packages considered:` — six mechanisms, each with what I READ

| mechanism | library | what I READ | verdict |
|---|---|---|---|
| `python_files` glob → "is this test-shaped?" | `_pytest.pathlib.fnmatch_ex` via `_pytest.python.path_matches_patterns` | **installed source, pytest 9.0.3**: the `if sep not in pattern: name = path.name else: name = str(path)` branch, plus `if path.is_absolute() and not os.path.isabs(pattern): pattern = f"*{os.sep}{pattern}"` | **`replace_with_adapter`** — the instrument is stdlib-only by ruling and cannot import pytest, so it ports the POSIX branch and the contract pins it against the installed pytest as an ORACLE. ⚠ Three prior surveys recorded plain `fnmatch` as an exact replacement **without opening pytest's matcher** |
| mypy config discovery | `mypy.defaults`, `mypy.config_parser` | **installed source, mypy 2.1.0**: `CONFIG_NAMES`, `SHARED_CONFIG_NAMES`, `_find_config_file`'s loop and `_parse_individual_file`'s *"basename in SHARED_CONFIG_NAMES and 'mypy' not in parser"* asymmetry (so an EMPTY `mypy.ini` still wins) | **`replace`** the pyproject-only read; the candidate order is a constant re-derived from these on every gate run |
| pytest config discovery | `_pytest.config.findpaths.locate_config` | **installed source**: the `config_names` local — four names beat `pyproject.toml` — and `load_config_dict_from_file`'s per-suffix acceptance rules | **`replace`** any hand-list; the contract AST-reads the literal, since it is a function-local with no constant to import |
| content digest for the memo key | `hashlib.blake2b` | stdlib; measured 29 ms over 9.06 MB | **`replace`** — no hand-rolled hash |
| tree fingerprint for the memo key | `scripts/tree_fingerprint.sh` (in-repo) | **its source and its own stated BOUNDS**: it hashes `git ls-files -s` + `git diff`, i.e. the TRACKED tree, and states *"a brand-new untracked file does not move the tree hash"* | **`bespoke` — it does not do the job.** pytest COLLECTS untracked files, so reusing it would under-invalidate, which is the one direction that serves a false clear. Minimal surface: the bespoke part is a path walk plus a digest, and it is pinned by 6 invalidation pins |
| memoisation | `functools.lru_cache` | stdlib signature | **`bespoke`** — `lru_cache` keys on the ARGUMENTS, and the argument (`repo_root`) is precisely the key that goes stale. The cache must be keyed on a fingerprint the argument does not carry |
| INI section detection for the sidecars | `configparser` | stdlib | **not needed** — the guard refuses on PRESENCE, so no sidecar is parsed. Deliberately cruder than modelling: a model of another tool's precedence is a second place to be wrong |

No dependency added; the instrument still imports the standard library only, which
`test_the_instrument_imports_nothing_outside_the_standard_library` derives from
`sys.stdlib_module_names`.

---

## 9. Instruments — verbatim (brief-base §1: not committable by me, so pasted)

### 9.1 `wrong_builds.py` — the wrong-build harness (§4)

Exact-string patcher + runner. **A patch whose anchor is missing or non-unique is a hard error**,
and every run's collected total is compared to the baseline's — a run that does not collect the same
number of tests is reported NOT COMPARABLE rather than as a survivor (it fired for real: WB19).

```python
#!/usr/bin/env python3
"""Wrong-build harness: derive wrong implementations of gated_ground.py by exact-string patching,
run the REAL contract against each, and report which SURVIVE."""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

SCRATCH = Path("<scratch>/refrepo")
INSTRUMENT = SCRATCH / "scripts" / "gated_ground.py"
PYTHON = "<worktree>/.venv/bin/python"

WRONG_BUILDS: dict[str, list[tuple[str, str]]] = {}    # name -> [(anchor, replacement), ...]

# ... 21 entries; each one's anchor/replacement pair is quoted in §4.2's table by description,
# and the two adversary-3 survivors are reproduced here because they are the load-bearing pair:

WRONG_BUILDS["WB1_blindness_only_for_five_named_doors"] = [(
    """    try:
        scopes = _derive(repo_root)
    except GuardIsBlind as blindness:
        return Verdict(findings=(), blind_sources=(str(blindness),))""",
    """    try:
        scopes = _derive(repo_root)
    except GuardIsBlind as blindness:
        pinned = {
            "members-declaration-absent",
            "members-entry-widens-to-the-whole-tree",
            "git-is-unexecutable",
            "manifest-unreadable",
            "receipts-root-is-not-lint-excluded",
        }
        if blindness.door in pinned:
            return Verdict(findings=(), blind_sources=(str(blindness),))
        return Verdict(findings=(), blind_sources=())""")]

WRONG_BUILDS["WB2_served_surface_ignores_findings"] = [
    ("""        return self.state is VerdictState.GATED_GROUND""",
     """        return not self.blind_sources"""),
    ("""            case VerdictState.UNGATED_GROUND:
                return "\\n\\n".join(finding.message for finding in self.findings)""",
     """            case VerdictState.UNGATED_GROUND:
                return (
                    "GATED GROUND — every tracked module is registered with the type gate, and "
                    "every tracked test-shaped file is one the collector reaches."
                )"""),
]


def apply(name: str, pristine: str) -> str:
    patched = pristine
    for anchor, replacement in WRONG_BUILDS[name]:
        found = patched.count(anchor)
        if found != 1:
            raise SystemExit(
                f"{name}: anchor matched {found} times, so the patch would not land as written:\n"
                f"{anchor[:160]}"
            )
        patched = patched.replace(anchor, replacement)
    if patched == pristine:
        raise SystemExit(f"{name}: the patch changed nothing")
    return patched


def run_contract() -> tuple[int, int, int, str]:
    completed = subprocess.run(
        [PYTHON, "-m", "pytest", "-q", "scripts/test_gated_ground.py", "-p", "no:randomly"],
        cwd=SCRATCH, capture_output=True, text=True, check=False,
    )
    tail = completed.stdout.strip().splitlines()[-1] if completed.stdout.strip() else "<no output>"
    passed = int(match.group(1)) if (match := re.search(r"(\d+) passed", tail)) else 0
    failed = int(match.group(1)) if (match := re.search(r"(\d+) failed", tail)) else 0
    errors = int(match.group(1)) if (match := re.search(r"(\d+) error", tail)) else 0
    return passed, failed, errors, tail


def main() -> int:
    pristine = INSTRUMENT.read_text(encoding="utf-8")
    Path("<scratch>/pristine_gated_ground.py").write_text(pristine, encoding="utf-8")  # CONTENT
    names = sys.argv[1:] or sorted(WRONG_BUILDS)
    print("=== baseline (correct build) ===")
    passed, failed, errors, tail = run_contract()
    baseline = passed + failed + errors
    print(f"REF => {tail}   [collected total: {baseline}]")
    if failed or errors:
        raise SystemExit("the correct build is not green in the scratch — nothing below is comparable")
    survivors: list[str] = []
    for name in names:
        INSTRUMENT.write_text(apply(name, pristine), encoding="utf-8")
        passed, failed, errors, tail = run_contract()
        total = passed + failed + errors
        comparable = "" if total == baseline else f"  ⚠ NOT COMPARABLE ({total} != {baseline})"
        verdict = "❗SURVIVED" if failed == 0 and errors == 0 else "killed"
        if verdict == "❗SURVIVED":
            survivors.append(name)
        print(f"{name:52s} {tail:34s} {verdict}{comparable}")
        INSTRUMENT.write_text(pristine, encoding="utf-8")
        assert INSTRUMENT.read_text(encoding="utf-8") == pristine, "restore is not byte-exact"
    print(f"\n{len(names)} built · {len(names) - len(survivors)} killed · {len(survivors)} survived")
    for name in survivors:
        print(f"  SURVIVOR: {name}")
    return 1 if survivors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

### 9.2 The scratch builder (#284-safe) and the R10 cost prober

```bash
# NEVER `cp -a` / scratch_copy.sh THIS WORKTREE: its .git is a FILE naming the real gitdir.
mkdir -p <scratch>/refrepo
git archive HEAD -o <scratch>/head.tar
tar -xf <scratch>/head.tar -C <scratch>/refrepo
cp scripts/gated_ground.py scripts/test_gated_ground.py <scratch>/refrepo/scripts/
git -C <scratch>/refrepo init -q -b main .
git -C <scratch>/refrepo add -A
git -C <scratch>/refrepo -c user.name=scratch -c user.email=scratch@example.invalid commit -q -m base
ln -s "$PWD/.venv" <scratch>/refrepo/.venv
test -d <scratch>/refrepo/.git && echo "PROVENANCE OK: .git is a DIRECTORY" || exit 1
```

```python
# R10 cost prober: disable ONLY the memo lookup, in the SCRATCH, then time the same 314 tests.
import pathlib
p = pathlib.Path("<scratch>/refrepo/scripts/gated_ground.py")
s = p.read_text()
anchor = "    memoised = _COLLECTOR_MEMO.get(memo_key)"
assert s.count(anchor) == 1, s.count(anchor)
p.write_text(s.replace(anchor, "    memoised = None  # MEMO DISABLED for the cost measurement"))
# -> 1 failed, 313 passed in 146.26s   (the one failure IS the memo pin, correctly)
```

### 9.3 The dangling-citation checker (used for the §2.2 corpse sweep)

```python
import ast, re, pathlib
src = pathlib.Path("scripts/test_gated_ground.py").read_text()
tree = ast.parse(src)
local = {n.name for n in ast.walk(tree) if isinstance(n, (ast.ClassDef, ast.FunctionDef))}
cited = set(re.findall(r":(?:class|meth|data|func|attr):`+([A-Za-z0-9_.]+)`+", src))
bad = [c for c in cited
       if c.split(".")[0] not in {"gg"} and not all(p in local for p in c.split("."))]
print("DANGLING:", sorted(bad) if bad else "none")     # -> none
```

⚠ **Known bound of this checker, named because adversary-3 named the same one in its own:** it only
knows LOCAL classes, so a cross-module citation (`:class:`gg.Verdict``) must be excluded by hand or
it reads as dangling. It is a lead-generator, not an oracle.

---

## 10. What I did NOT prove

- **Source-level "unrepresentable" for anything but the incoherent cell.** §3.1 states exactly which
  claim is structural and which is quantified. A build that edits the classifier is caught by a
  mutation pin, not by the type system.
- **That the derived failure set is complete over the WORLD.** It is complete over the doors the
  instrument declares (checked both ways) and the configuration files the two vendors declare
  (checked against their constants). A world-state with neither is not in it — the byte-diff legs
  are what would catch one, and any false clear found later is a re-open trigger for the table
  rather than a retroactive pass for it. The table says so in its own docstring.
- **The memo under a mid-process environment change** (E1) — pinned as a bound, not closed.
- **That my 21 wrong builds are the right 21.** They are my own enumeration, written before I
  re-read adversary-3's list, plus its two named survivors. Six of them surviving is evidence the
  enumeration was doing work; it is not evidence that a 22nd would not survive.
- **Windows.** The matcher ports pytest's POSIX branch only, stated as a bound with a trigger.
- **Nothing about a FUTURE tree.** Every number here is dated 2026-07-29 and scoped to the two md5s
  in the header. The full suite was run twice — the first without an exit capture (a gap I noticed
  and closed rather than reported around), the second with `FULL_SUITE_EXIT=0` — same counts both
  times.

---

# ADDENDUM r2 — the lead's rulings on §7, executed (2026-07-30)

**Appended here rather than written as a separate `-r2` file, deliberately:** the citation law
prefers ONE durable address over two, and every pointer already written at
`REPORT-author-44-monotonic-1.md` keeps resolving. Everything above this line is the state at
`7ad1b0a`; everything below is what changed after it, in commits **`13bbe84`** (E1), **`1430aa5`**
(E4) and **`9c0f2da`** (this addendum).

⚠ **One more deviation, disclosed because a receipt about commits should not be the one thing left
unreceipted:** my first attempt landed E1 and E4 as ONE commit — `scripts/wrong_builds.py` had been
`git add`-ed earlier so the guard would see it as TRACKED (that is how §E4's fates were measured),
and it was still staged when E1 was committed. Caught by reading `git show --stat`, split into the
three commits above with `git reset --soft` (nothing pushed), and the four frozen md5s re-verified
against `git show HEAD:<path>` afterwards — they match the working tree exactly.

## FROZEN FOR THE AUDITOR

| artifact | md5 | lines |
|---|---|---|
| `scripts/gated_ground.py` | **`ce80544260f45ece25b939437581ca2e`** | 1481 |
| `scripts/test_gated_ground.py` | **`7fb8f86f68dad8005f6734278a379001`** | 4122 (**315 collected**) |
| `scripts/wrong_builds.py` *(new, E4)* | **`00d9adf8244175c19e1d617b514071bc`** | 402 |
| `loremaster/tests/test_secret_resolution_seam.py` *(one allowlist entry, E1)* | **`aa5366a53a1a0ac872be9974f811ce9a`** | — |

Full suite **8747 collected**. The guard's own verdict on this tree: `GATED_GROUND`, exit 0,
**293 of 293** tracked `.py` classified (292 + `wrong_builds.py`), zero findings.

## E1 — GRANTED and executed, with ONE deviation I am escalating rather than deciding

**Done as ruled:** the allowlist entry is added at exactly the granted key
`scripts/gated_ground.py::_collector_input_fingerprint` with the reason verbatim from §7 plus the
grant's provenance; `_collector_input_fingerprint` now hashes
`os.environ.get("PYTEST_ADDOPTS", "")`; and the invalidation it buys is pinned by
`test_an_inherited_pytest_addopts_moves_the_memo_key` — **two legs**, because either alone passes
for the wrong reason:

- **Leg 1 (the answer):** with `PYTEST_ADDOPTS=--ignore=loremaster/tests/probes` the collector stops
  seeing a registered test file, the memo lets go, and **a second subprocess runs** (asserted, not
  inferred) — so the pin is measuring collection rather than a hash.
- **Leg 2 (the key):** two DIFFERENT but behaviourally INERT values (`-p no:randomly` vs
  `-p no:cacheprovider`) must still produce different fingerprints — so the key is covering the
  VARIABLE, not a consequence of it that it could already see in the files.

**Not touched:** anything else in `loremaster/`. The seam's own suite passes —
`pytest -q loremaster/tests/test_secret_resolution_seam.py` → **64 passed in 6.75s** — which
matters because that file holds the pins that would reject a bad entry
(`test_every_environment_read_is_the_entry_point_or_allowlisted`,
`test_no_allowlist_entry_is_stale`, `test_every_allowlist_entry_carries_a_reason`).

### ⚠ THE ONE THING I DID NOT DO, AND WHY — the bound is RESTATED, not retired

The ruling's premise was **one door**. I measured **four**. Derived from the installed pytest's own
source (`grep -rhoE 'environ(\.get)?\(?\[?"[A-Z_]+"' .venv/…/_pytest/`), the variables it reads that
can change what a collection produces are **`PYTEST_ADDOPTS`** (closed today), **`PYTEST_PLUGINS`**,
**`PYTEST_DISABLE_PLUGIN_AUTOLOAD`** and **`PY_IGNORE_IMPORTMISMATCH`**.

**Retiring `collector-memoisation` would therefore state a closed hole as closed while three doors
stand open — the exact defect class this packet exists to close, in the direction that is FALSE IN
THE DANGEROUS SENSE.** (A bound describing an already-closed hole is false in the safe direction;
deleting a bound whose hole is open is false in the other.) So the bound is **restated to name the
measured residual**, its re-open trigger now enumerates the three variables, and the retirement of
its old PYTEST_ADDOPTS clause is recorded here as the ruled decision — closed, not forgotten.

And the restatement is itself **mechanically guarded**, because prose about a mechanism is exactly
what no gate checks: `test_the_memoisation_bound_never_names_a_variable_the_key_already_covers`
AST-derives the environment variables the instrument reads and asserts **none of them appears in
the re-open trigger**, plus that the trigger names at least one variable it does not read. A future
agent that closes `PYTEST_PLUGINS` and forgets the prose goes RED.

**E6 — the fork, with the patch ready and a recommendation.** Covering all four costs **zero extra
allowlist entries**: the seam's scan keys per `path::function`, and this function already holds the
granted key — so reading three more variables inside it produces the same single entry. The change
is three lines in `_collector_input_fingerprint` plus widening the existing pin's parametrization.
**My recommendation: do it** — the three are strictly more dangerous than the one that was closed
(`PYTEST_DISABLE_PLUGIN_AUTOLOAD` can silence an entire plugin's collection hooks), and the residual
would then be only *"the installed package set, which cannot change inside one process"*, which is
an argument rather than a hope. **It is a scope decision and therefore yours, not mine** — and I
have deliberately NOT widened it, because making the ruling moot by pre-empting it is the same error
as ignoring it.

## E4 — GRANTED and executed: `scripts/wrong_builds.py`

Committed with a docstring that states what it is (an ATTACK harness), that it is **hand-run and
wired into no gate**, how to build the #284-safe scratch repository, how to re-run the 21-build
attack, and its own three BOUNDS — including the one that matters most: *a SURVIVOR is not
automatically a defect, and "all remaining survivors are equivalent" is banned output.*

Rewritten for a committed home rather than pasted: `argparse` (`--scratch`, `--instrument`,
`--contract`, optional build names) instead of hardcoded paths, `sys.executable` instead of an
absolute venv path, and **a refusal to run at all if `<scratch>/.git` is not a DIRECTORY** — the
#284 landmine, enforced by the tool rather than remembered by its user. The 21 build definitions
are carried over **verbatim** from the run that produced §4's census; a re-typed table would be a
different instrument reporting the same numbers.

**The lead's question — did my own guard flag it?** No, and the reason is the mechanism working
rather than luck:

```
tracked .py: 293 (was 292)      wrong_builds tracked? True
its fates: {'TYPES': 'COVERED', 'EXECUTION': 'NOT_APPLICABLE'}
state: GATED_GROUND | exit: 0 | findings: 0
```

`scripts` is a `MEMBERS` typecheck root, so LEG A covers the new file **because the tree is
registered, not because anything knows its name**; and it is not test-shaped, so LEG B correctly
declines to judge it. It type-checks under that root: `MYPYPATH=scripts uv run mypy
scripts/wrong_builds.py` → *Success: no issues found in 1 source file*, and the `scripts` leg of
`typecheck.sh` is green.

**Smoke-tested from its committed home**, against the live scratch:

```
$ .venv/bin/python scripts/wrong_builds.py --scratch <scratch>/refrepo WB1_… WB2_… WB21_…
=== baseline (correct build) ===
REF => 315 passed in 89.54s (0:01:29)   [collected total: 315]
WB1_blindness_only_for_five_named_doors              59 failed, 256 passed   killed
WB2_served_surface_ignores_findings                  2 failed, 313 passed    killed
WB21_memo_written_before_the_anti_vacuity_check      1 failed, 314 passed    killed
3 built · 3 killed · 0 survived
HARNESS EXIT=0
```

(WB1 now dies on **59** pins rather than 57 — the two new memo pins added since §4's census. The
number is re-derived here rather than carried forward.)

## E2 / E3 — noted

E2 accepted as I resolved it; no change made. E3 routed to the cold audit; I add nothing.

## A defect this addendum's own pins caught, in this addendum's own work

Restating the `collector-memoisation` bound broke
`test_every_stated_bound_carries_a_named_re_open_trigger_and_appears_in_the_docstring`: my new
summary was **111 characters**, so it wrapped in the module docstring and stopped being a
contiguous substring of it — a bound declared in `STATED_BOUNDS` that a reader of the file would
never meet. One failed / 314 passed, fixed by shortening the summary. *The pin exists because a
bound nobody meets is a bound nobody has, and it fired on its author within an hour of the author
writing the law about it.*

## GATES, re-run fresh after both grants landed

```
$ uv run pytest -q scripts/test_gated_ground.py -p no:randomly      # run 1 of 2
315 passed in 80.33s (0:01:20)

$ uv run pytest -q scripts/test_gated_ground.py -p no:randomly      # run 2 of 2 (determinism)
315 passed in 80.42s (0:01:20)

$ ./scripts/typecheck.sh ; echo "TYPECHECK EXIT=$?"
… typecheck: scripts OK
typecheck: shellcheck OK (7 tracked .sh)
TYPECHECK EXIT=0

$ uv run ruff check . ; echo "RUFF EXIT=$?"
All checks passed!
RUFF EXIT=0

$ uv run pytest -n auto -q ; echo "FULL_SUITE_EXIT=$?"
8708 passed, 36 skipped, 3 xfailed, 1 warning in 220.82s (0:03:40)
FULL_SUITE_EXIT=0
$ uv run pytest -q --collect-only
8747 tests collected
# 8708 + 36 + 3 = 8747 == collected. EXACT reconciliation, no failures, no errors.

$ uv run pytest -q loremaster/tests/test_secret_resolution_seam.py -p no:randomly
64 passed in 6.75s
```

**There are 0 failing tests unrelated to our present scope.**

RIDER, re-run: the guard on this repository → `GATED_GROUND`, exit 0, **293/293** classified, zero
findings, `blind_sources ()`.

## FOR THE COLD AUDIT

The four md5s above are frozen. The two claims I would attack first if I were the auditor:

1. **The derived door set is only as complete as the derivation.** `test_no_refusal_bypasses_the_
   one_door_helper` is what stops it degenerating into a name list — break it and check it fires.
2. **E6's three uncovered environment variables.** I measured them by grepping the installed
   `_pytest`; re-derive rather than inherit, and check whether any gate path in this repo sets one.
