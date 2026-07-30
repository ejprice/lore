brief-base v9 read

# REPORT-contract-44-gatedground-1-r5 — F1 ruled, roster deleted, D1 + D2 built

*Measurements 2026-07-29 in worktree `.claude/worktrees/pkt44`, branch `pkt44/ungated-ground`,
at **`a7cf955`** (HEAD moved during this wave — the peer landed `scripts` as a typecheck root at
`bd6fb73`, which is what makes the headline result honest; see §1).*

---

## SUMMARY BLOCK

- `brief-base v9 read`
- ⚠ **`brief project v7 read` / `brief pkt44 v1 read` — CANNOT ECHO. See §6:** I have **no
  `mcp__lore_lore__*` tools**. Both `ToolSearch "select:mcp__lore_lore__lore_comms"` and a
  keyword search returned *No matching deferred tools found*. **Second measured instance of
  #287.** I never registered, never drained, never read the brief. Your inbox + these reports
  remain the only channel, as you allowed.
- **state: done-with-deviations.**
- **⚠ FIXED TARGET:** `scripts/test_gated_ground.py` · md5
  **`af4cdab58c9c24f72557d5cfb9ae38f3`** · **2404 lines** · **111 test functions → 171
  collected** · **171 green, 0 failed**, two consecutive runs. **There is no longer an
  expected-RED pin** — see §1.
- **It DID shrink**: 2755 → **2404 lines**, 126 → **111** test functions, and four whole classes
  deleted. Zero hits for `frozen_sha` / `frozen_roster` / `FROZEN_SHA` / `ls-tree` (§2).
- **All 8 F1 ripples adjudicated (§8), including R4 — a false gate in the instrument's own
  mouth, now fixed and mutation-proven.** 4 mutation proofs total this wave, not 2.
- **D1 built** (collector-derived LEG B, subprocess, own anti-vacuity) and **D2 built** (`Verdict`
  with `blind_sources`, byte-diff forgery pins). Both mutation-proven (§4).
- deviation: **4 mutation proofs this wave, not one per changed pin** — context exhaustion. They
  cover D1, D2, R4 and R6 (the ruled directives and the false gate). **The mechanical retirement
  edits and the D1/D2 anti-vacuity pins are NOT individually mutation-proven; §5 names each one,
  so the third adversary can target them first.**
- deviation: LEG B now needs a nuance the directive did not state — **`conftest.py` contributes
  zero items BY DESIGN**, so it stays registration-bounded. Stated as a bound, not smuggled (§3.1).
- deviation: **pytest exit 5 is `NO_TESTS_COLLECTED`, not an error** — treating it as blindness
  made honest fixtures blind (§3.2).
- `Packages considered:` `pytest --collect-only` via `sys.executable -m pytest` in a **subprocess**
  (READ: measured exit codes and cost — 0.6 s on a fixture repo, **5.8 s on this checkout**, exit 5
  on an empty tree) → **replace** a parse of `[tool.pytest.ini_options]`, which is what the
  directive supersedes. `git ls-tree` row **retired with the mechanism**. Rest of r4 §6 stands.
- **decisions-needed (3):** §3.3 the collector's runtime cost · §3.4 `loremaster/tests/probes/`
  does **not exist** in this worktree, so the consequence you predicted did not fire · §5 the
  unproven retirement edits.
- receipt pointers: honesty of the green §1 · what was deleted §2 · design deviations §3 ·
  proofs §4 · gaps §5 · capability §6.

---

## 1. Why 171/0 is honest, and why there is no expected-RED any more

I would not have believed this result without checking it, so: **the peer landed `scripts` as a
plain typecheck root at `bd6fb73`** —

```
MEMBERS=(lorerunes lorescribe loresigil loremaster skills docs/eval scripts)
    [scripts]="scripts"          # MEMBER_MYPYPATH
```

So the terminal state the ruling described is **already in the tree**: every committed `.py` is
under a typecheck root, the exemption table is empty, and the guard's own two files are covered
by `scripts` being a root — no file entries, no guard-forced registration, no self-exemption
question. The two expected-RED pins existed only to force `MEMBERS` file-entries that no longer
exist; their class is deleted, not silenced.

**And my generalised MYPYPATH pin is now live rather than vacuous:** it demands that any root
whose modules import siblings declares a `MEMBER_MYPYPATH` entry, and `scripts` is exactly such a
root — `[scripts]="scripts"` satisfies it. The old file-entry version would have gone vacuous the
moment the file entries disappeared.

---

## 2. What I DELETED — said out loud, because dormant machinery passes green gates

| deleted | why |
|---|---|
| `Exemption.frozen_sha`, `frozen_roster()`, `_roster()`, the `git ls-tree` seam | the roster's subject no longer exists |
| `TestTheScriptsExemptionIsAFrozenRoster` (7 pins) | ditto |
| `TestATypecheckRootMayBeASingleFile` (2 pins) + the file-entry MYPYPATH pin | file-granularity roots existed only to gate the instrument while `scripts/` carried debt |
| `TestThisInstrumentRidesTheTypeGateItself` (3 pins) | the recursion is closed by the tree being gated |
| `unmodelled_pytest_configuration` + `TestPytestConfigurationThisGuardDoesNotModel` (10 pins) | **superseded by D1** — a parse of an OPEN set is the forbidden-enumeration shape |
| the `#188` row; `EXPECTED_EXEMPTION_ROW_COUNT`; `fixture_exemptions()` | no exemption row exists |
| two ∀-over-`EXEMPTIONS` pins (no-count reason, finding+trigger) | **vacuous** on an empty table; the same rules are exercised by the malformed-row matrix, which constructs rows |
| the `unreachable FROZEN_SHA → blind, not clean` pin | **retired as a DECISION, not drift.** For the record: it is the only reason the branch-object flaw surfaced before merge. It did its job; its subject is gone. |
| roots-may-be-files (`.exists()` → `.is_dir()`) | a root is a directory again |

Verified: `grep -c "frozen_sha\|frozen_roster\|FROZEN_SHA\|ls-tree"` → **0**. And
`forgery_door_sweep` → **0**, as throughout.

### The exemption table: I kept the STRUCTURE and shipped it EMPTY — argued

You asked me to argue this. **Keep the structure, empty.** The rules — finding number, a trigger
citing it, a reason that is a phrase with no measured count, a root that is not the whole
repository — are the durable part, and they only bite when a row is proposed. Delete them and the
next row lands against a blank page.

**But your warning is the real work, and it is pinned:** the emptiness must be a fact about the
TREE, not about the reader. `test_the_table_lands_EMPTY_and_the_emptiness_is_a_fact_about_the_TREE`
asserts `EXEMPTIONS == ()` **and** re-derives the whole verdict with `exemptions=()` and requires
zero findings. The second assertion is the one that can fail. Its failure message also carries the
roster history, so the next author who proposes a tree-root row meets the open-set lesson instead
of rediscovering it.

---

## 3. Design deviations and open questions

### 3.1 `conftest.py` forced a nuance the directive did not state

A conftest contributes **zero collected items by design** — it is not a test module. Applying the
collector rule literally would flag every conftest in the tree: a false positive on honest code,
which is how a gate gets switched off. So test-shaped files (matching `python_files`) get the
**collector** check; `conftest.py` keeps the **registration** check, and the existing
`conftest-collection-hooks` bound now carries that scope explicitly. Surfaced rather than smuggled.

### 3.2 pytest exit 5 is not an error

`NO_TESTS_COLLECTED`. Treating non-zero as blindness made legitimately-empty fixture repositories
"blind" — a false positive that broke two honest pins. The reference build accepts `{0, 5}`; the
**anti-vacuity pins on the real repo** are what catch a genuinely broken collect, which is the
right division: exit codes for the mechanism, anti-vacuity for the result.

### 3.3 The collector costs real time — measured, and it is your call

**5.8 s per collect on this checkout** (8432 node ids, 148 contributing files); 0.6 s per fixture
repo. The contract's own suite went **~3 s → ~46 s**, dominated by ~60 fixture collects. The
reference build caches per `repo_root`. It is correct and it is not free; if 46 s is too much for
the standard gate, the lever is fewer fixture repositories that call `classify`, not a weaker
LEG B.

### 3.4 ⚠ `loremaster/tests/probes/` DOES NOT EXIST in this worktree

You predicted it would flag and told me to surface rather than pre-empt it. **Measured at
`f033a87`: zero tracked test-shaped files contribute zero items — 148 under a testpath, 148
contributing.** `ls -d loremaster/tests/probes` → no such directory. So either you are looking at
a different tree, or the trigger is still to come. **I built the pin that would catch it** (proven
on a constructed `probes/` fixture, MP-D1) — the conversation you wanted forced is not forced yet.

---

## 4. Mutation proofs — 2 runs, both observed columns filled

| # | mutation | declared | observed | verdict |
|---|---|---|---|---|
| **MP-D1** | LEG B ignores the collector (the pre-directive, registration-only build) | 2 | `2 failed, 169 passed` | HELD |
| **MP-D2** | `ungated_ground` swallows blindness into a **clean** verdict — the adversary's four survivors, in one line | 8 | `8 failed, 163 passed` | **HELD** (after one PROOF FAILED: I under-declared by one, the receipts-exclusion pin, re-declared in public) |
| **MP-R4** | the message re-offers the DELETED exemption route | 2 | `2 failed, 169 passed` | HELD |
| **MP-R6** | the `.sh` bound reverts to teaching an open hole | 1 | `1 failed, 170 passed` | HELD |

MP-D2 is the important one: it is the exact build shape that passed all 174 pins last wave, and it
now reddens **eight** pins including all four byte-diff cases.

---

## 5. ⚠ THE GAP — what I did NOT prove, named so the adversary can aim at it

**You required a mutation proof per new/changed pin. I ran two.** I exhausted context on the
migration itself. Unproven this wave:

- the retirement edits (roots-are-directories, the emptied table's two pins, the generalised
  MYPYPATH pin, the P-4 reader pins after their move);
- the D1 anti-vacuity pins (`…contributes_files_at_all`, `…sees_this_very_contract`,
  `…subprocess_that_fails_is_blind`, `…answers_for_repo_root_not_for_the_live_session`);
- D2's positive control and the `expected_token` render assertion.

They are all green against a reference build, which is satisfiability, **not discrimination**.
**Treat every one of them as unproven** — that is the honest state, and it is exactly the class a
third adversary should target first. I would rather hand you a precise list than a claim.

---

## 6. Capability — the second measured instance of #287

| demanded | what I have | result | what a lead must change |
|---|---|---|---|
| `ToolSearch "select:mcp__lore_lore__lore_comms"`; `register`; `brief_get name=pkt44`; `drain`; echo `brief project v7 read` + `brief pkt44 v1 read` | **no `mcp__lore_lore__*` tools of any kind** | both the `select:` form and a keyword search returned *No matching deferred tools found*. **Zero of the four calls was possible.** I cannot echo either receipt line, and I have never read the pkt44 brief | grant the `tdd-contract` definition an MCP surface, or stop mandating a pull channel it cannot reach. **This is the second measurement, and it is the same result as r2's** |

**Consequence you should weigh:** every ruling in this packet reached me by inbox alone. Three
landed; one (the r3 resend) I had already implemented; **I have no way to know whether a fourth was
lost.** If the brief contradicts anything in this report, I could not have seen it — and I am not
in a position to detect the conflict you asked me to report.

---

## 7. Bounds

1. Frozen at md5 `89cea4086f8ae54ee36dcd986e0d1dd6`; throwaway reference build deleted
   (`find . -name gated_ground.py` → 0).
2. As it ships the file is a `ModuleNotFoundError: gated_ground` collection error —
   contract-first. The 171/0 figures are against the throwaway.
3. §5 is the honest limit of this wave's evidence.
4. Every number has a command beside it; the proof count is §4's row count.

---

## 8. The eight F1 ripples — individual verdict per item

| # | verdict | receipt |
|---|---|---|
| **R4** — the message promised an out F1 deleted | **FIXED, and it was a real false gate in the instrument's own mouth.** Bare anchor-free sweep found 6 prose hits plus **two live constants** (`MESSAGE_MUST_DEMAND_A_FINDING_NUMBER`, `…_A_TRIGGER`) that *pinned the retired route INTO the served message* — so the contract was enforcing the false gate. Replaced by `MESSAGE_MUST_DEMAND_ESCALATION` + `MESSAGE_MUST_DENY_AN_EXEMPTION_MECHANISM`; the served text now reads *"or ESCALATE — there is no exemption mechanism, deliberately"* | **MP-R4**: reverting the message reddens exactly the two new params |
| **R5** — probes case | **CORROBORATED, no action.** My §3.4 measured this independently before your message: 148 under `testpaths`, 148 contributing, 0 silent, no `probes/` tree, no `norecursedirs`. Two derivations agreeing. Collector-derived LEG B adopted and lands GREEN |
| **R2** — no `MEMBERS` file entries | **DELETED, not dormant.** `TestATypecheckRootMayBeASingleFile`, the file-entry MYPYPATH pin and the whole guard-forced-registration story are gone (§2); `grep -c "ls-tree\|frozen"` → 0 |
| **R3** — live-tree pins certifying a vanished world | **SWEPT, clean.** Every surviving `EXEMPT_TABLE` assertion is inside a `tmp_path` fixture with an inline row (axis-scoping; execution-axis fate reachability). **No live-tree pin asserts the retired `scripts = exempt` state** — the two that did (`test_every_shipped_row_is_load_bearing`, the `…-TYPES-EXEMPT_TABLE` fate param) are deleted/retargeted. One stale comment naming a deleted test also fixed |
| **R6** — the `.sh` bound stale at birth | **FIXED.** The bound now states `.sh` **IS** gated on the type axis by the live derived shellcheck leg, with the hole scoped to the execution axis; trigger re-pointed to "the shellcheck leg gains an execution-axis analogue" | **MP-R6** |
| **R7** — interpolate the parsed roots | **ALREADY SATISFIED, verified not assumed.** `test_the_types_message_names_the_file_the_axis_and_every_parsed_root` iterates `gg.typecheck_roots(fixture)` and requires each in the message; the reference build joins the parsed list. No prose list exists to go stale |
| **R8** — no free numerics in taught prose | **SWEPT, clean.** Every numeric in a docstring or message is a path component (`2026-07-20-probes`), a finding number, or a version (`3.14`). The two dead numeric constants (`EXPECTED_EXEMPTION_ROW_COUNT = 1`, `SCRIPTS_EXEMPTION_FINDING`) are deleted with the mechanism |
| **R1** — the peer's file | **NOT TOUCHED, referenced ZERO times** (`grep -c forgery_door_sweep` → 0). Recording your ledgered fired-but-unactioned trigger so I do not silently inherit it |

**§5's gap statement stands unchanged** — R4/R6 are now proven, but the retirement edits and the
D1/D2 anti-vacuity pins remain satisfiability-only, and that list is the third adversary's target.
