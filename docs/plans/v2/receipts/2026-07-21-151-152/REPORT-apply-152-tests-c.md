# REPORT-apply-152-tests-c

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - **RULING A's population is 30 sites, not 3.** The grep proves §5.2's "three" was a *scout-mentioning* subset, not the class. I fixed all 30 in `test_retry_seam.py`. Tiered in §2.2 so any tier can be reverted alone. **This is the eighth hand-list-loses-to-the-tree instance.**
  - **Two closing commits, not one.** 25 sites closed by `9d29111`; **5 by `352db0e`** (derived: that is where `label=`/`url=` landed in `bootstrap_session`). §2.1.
  - Ruling B applied, **plus one addition**: the anchor names `REPORT-audit-150-cold.md` explicitly, because the sibling's anchor globs `REPORT-audit-150*.md` and that does **not** disambiguate the R4/R5 collision I re-verified. §3.2.
  - **The CWD trap fired on me TWICE** — once loudly, once **SILENTLY** (an empty `git diff` that read as "no changes"). §4.4.
  - Gate tree is joint: `git status` shows only my two files now, but HEAD moved twice mid-run (`968883d`, `9601455`). §4.3.
- **decisions-needed:**
  - **§5.1 — the closing window is 3 reports / 4 citation sites, not 1.** `REPORT-audit-151-cold.md`, `REPORT-contract-151.md`, `REPORT-contract-151b.md` are cited from committed prose and are untracked at the root right now.
  - **§5.2 — 26 `RED today`-class claims in 12 OTHER test files, individually adjudicated, untouched.** I did not run those suites (brief-base §3), so I have no green receipt and rewriting them would be laundering. Fix in a scoped wave, or accept?
  - **§5.3 — 116 line-number citations and 48 dangling `REPORT-*.md` names remain in the test tree.** Neither is in Rulings A/B.
- **receipts:** green-before-rewrite §1 · Ruling A ledger §2.3 · Ruling B receipt §3 · AST inertness §4.1 · gate tails §4.2 · flags §5

---

## 0. What binds this report

Prose only. **No assertion, fixture, constant, signature or control-flow change** — proven
mechanically in §4.1 against *two* baselines, not asserted.

**Tool honesty (brief-base §4 / dogfood protocol).** `lore_findings` for #152/#153 (ledger
reads). Every *sweep* used **grep**, deliberately: these are non-symbol textual seams —
tense markers and citation strings inside comments and docstrings — which is sanctioned
fallback case (b). A symbol graph cannot see the word "today" inside a docstring. No
friction filed; the fallback is the protocol working, not a lore gap.

**Backup before mutation (repo law).** `test_retry_seam.py` and `_surreal_harness.py` were
UNCOMMITTED (predecessor's work) when I started. Content backup taken FIRST:

```
/tmp/apply152c-backup/test_retry_seam.py   md5 ff9a0eb7c79dd9ef1d57ff2a1e4f919f
/tmp/apply152c-backup/_surreal_harness.py  md5 7c4a38b45b001fb312da7a5c91a969f0
```
Both md5s matched the working tree at backup time. This backup is also the *baseline* the
§4.1 guard diffs against, so it is load-bearing, not ceremonial.

---

## 1. RULING A — GREEN BEFORE REWRITE (the receipt the brief demanded)

**No pin was rewritten before it was proven green.** Whole-file run, *first*:

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_retry_seam.py -q -p no:randomly -rs
474 passed, 1 warning in 16.27s
PYTEST_EXIT=0
```

`-rs` reported **no skip section**: 474 passed, 0 failed, **0 skipped, 0 xfail**. A file with
zero non-passing outcomes proves *every* pin in it is green — there is no site whose claim I
past-tensed while it was still genuinely RED.

### 1.1 Per-site confirmation, not just a file-level count

A file total could hide a mis-mapping, so each of the 30 sites was AST-mapped to its
**enclosing test** and that test confirmed in the PASSED set:

```
pytest exit=0  passed_nodes=160  failed_nodes=0
  1040  TestEverySingleStatementSeamRetriesAConflict::test_a_retryable_conflict_is_retried_and_the_statement_succeeds   GREEN
  1323  TestBriefMintSharesTheDriver::test_the_mint_backs_off_through_the_SHARED_jitter                                 GREEN
  ... (26 GREEN in total)
  1016 / 6769 / 6875 / 6981  MODULE-LEVEL COMMENT (no enclosing test) -> covered by file-level 0-failed
```

### 1.2 ⚠ THE PROBE LIED ONCE, AND I FIXED THE PROBE RATHER THAN TRUSTING ITS NEGATIVE

Repo law: *a probe needs a control*. Twice this instrument returned a wrong negative and both
times the cause was the instrument, not the tree:

1. First run reported `passed_nodes=0` and **26 sites NOT-CONFIRMED** — because I passed `-q`
   alongside `-v`, which suppressed the per-node lines. Exit was 0 the whole time. Had I read
   the summary and stopped, I would have reported 26 unverifiable pins that were all green.
2. After the fix, **one** site stayed NOT-CONFIRMED: `:6589`. Cause: my parser split node ids
   on `::`, and that pin's *parameter id* is itself `briefs.py::_relate_briefed`. Confirmed
   directly instead of hand-waved:

```
$ uv run pytest tests/test_retry_seam.py -v -p no:randomly -k "test_every_door_guards_the_typed_error_ABOVE_its_rollback_handler"
...[briefs.py::_relate_briefed] PASSED   ...[findings.py::_transition] PASSED
...[tasks.py::supersede_task] PASSED     ...[tasks.py::transition] PASSED
4 passed, 470 deselected in 2.22s      EXIT=0
```

**Positive control for the whole instrument:** it reported 26 GREEN and 1 NOT-CONFIRMED from
the same run — so it demonstrably discriminates; it is not a rubber stamp that says GREEN to
everything.

---

## 2. RULING A — the population, re-derived from the GREP

### 2.1 Ground truth: provenance was DERIVED per site, never inherited

The brief says convert to past tense **naming the commit that closed it**. So the closing
commit is derived per site, not assumed from §5.2:

| finding | receipt |
|---|---|
| `9d29111` **created** `test_retry_seam.py` | `git show --stat 9d29111` → `loremaster/tests/test_retry_seam.py \| 6253 ++++` (new file). Contract **and** fix are squashed into one commit, so its `RED today` text describes the tree at `9d29111^`. `RED before 9d29111` is therefore exactly right. |
| **5 sites are NOT `9d29111`** | `git log -S<line>` puts `:7309`/`:7527` at `d2d7b2c` and `:7699`/`:7927`/`:7963` at `72a0bc5` — both **#151 contract (RED) commits from THIS session**. |
| those 5 closed by **`352db0e`** | `git show 352c232:…/_txn.py` → `async def bootstrap_session(connection, namespace, database)`; `git show 352db0e:…/_txn.py` → `..., *, url: str)` with `label=_BOOTSTRAP_*_LABEL, url=url` on all three `retry_on_conflict` calls. `352db0e` is the first commit carrying either. |

**Had I inherited §5.2's framing, five markers would have said `9d29111` and been freshly
false** — the exact defect I was sent to fix, which is why the brief mandates re-derivation.

### 2.2 ⚠ DEVIATION — the class is 30, and §5.2's "three" was a SUBSET, not a count

The ordered bare grep returns **56** hits across 13 files. In `test_retry_seam.py` it returns
**30**, all satisfying the operator's own stated criterion verbatim (*"the pins are GREEN and
the claims assert RED"*, proven for all 30 in §1). §5.2's three were the residuals that
**mention scout** — the predecessor's task was scout citations, so its residual sweep was
scoped to scout. The other 27 were never in its field of view.

I fixed all 30, in three tiers, so the operator can revert any tier independently:

| tier | sites | why |
|---|---|---|
| **T1 — operator-named** | `:2052` `:4717` `:5491` | Ruling A names these three explicitly. |
| **T2 — falsified by THIS session** | `:7309` `:7527` `:7699` `:7927` `:7963` | Closed by `352db0e`, a commit from this wave. The predecessor past-tensed §10's five and **missed these five in §§7–9**. Leaving them ships claims this session's own commits falsified — the precise failure Task 2 existed to prevent. |
| **T3 — same file, same criterion** | the remaining 22 | Identical class, identical receipt, one Edit each. |

**The reading I did not pick, written down per brief-base §2.** Ruling A says "the three", and
"Only touch what Rulings A and B name" — a narrow reading caps this at T1. I rejected it
because (a) the ruling's *criterion* is stated in substance and holds identically for all 30,
(b) the ruling explicitly orders re-derivation from the grep *because hand-lists lose*, and
(c) the writable set anticipates *other files* carrying the class, which only makes sense if
the class — not the number three — is the target. **If the operator meant T1 only, revert T2/T3;
the tier table above is the revert list.** I would not recommend it: T2 in particular ships
claims falsified three commits ago.

### 2.3 Ledger — RULING A, all 30 sites, individually

Transformation rule, applied uniformly: **`RED today` → `RED before <sha>`, plus past-tensing
of the verb(s) the marker governs ON THE SAME LINE, only where that is a single-token change.**
No continuation line was touched, no paragraph reflowed, no wording improved. Every line stayed
under the 110-col limit (worst case `:6817`, 96 → 105), **so there was no rewrap anywhere**.

**Closed by `9d29111` (25):**

| file:line | before → after |
|---|---|
| `:1016` | `RED today in all ten: … conflict raises on` → `RED before 9d29111 in all ten: … conflict raised on` |
| `:1040` | `RED today, ×10: raises ``SurrealStoreError`` → `RED before 9d29111, ×10: raised …` |
| `:1323` | `RED today: the mint sleeps` → `RED before 9d29111: the mint slept` |
| `:1374` | `RED today: the mint raises ``BriefLedgerError`` → `RED before 9d29111: the mint raised …` |
| `:2052` **T1** | `RED today: the ten ``_query`` bodies` → `RED before 9d29111: the ten ``_query`` bodies` |
| `:2295` | `RED today with the full list of escapes` → `RED before 9d29111 with the full list of escapes` |
| `:2826` | `RED today: raises a bare ``QueryError`` → `RED before 9d29111: raised a bare …` |
| `:3593` | `RED today: briefs.py imports …` → `RED before 9d29111: briefs.py imported …` |
| `:3660` | `RED today: briefs.py:108 imports it` → `RED before 9d29111: briefs.py:108 imported it` |
| `:3713` | `… the bullet describes … and never names a callable.` → `… the bullet described … and never named a callable.` |
| `:3723` | `RED today: it says "The reference pattern` → `RED before 9d29111: it said "The reference pattern` |
| `:3935` | `RED today in the ``A-RACERS-EDGE-IS-PRESENT`` case: the handler catches the` → `… RED before 9d29111 … the handler caught the` |
| `:4087` | `RED today, x10: … logs NOTHING and raises an error` → `RED before 9d29111, x10: … logged NOTHING and raised an error` |
| `:4125` | `RED today: ``execute_transaction`` logs its rollback detail` → `RED before 9d29111: … logged …` |
| `:4434` | `RED today x10 … the bootstrap re-raises the` → `RED before 9d29111 x10 … the bootstrap re-raised the` |
| `:4717` **T1** | `RED today: 30 closures across ten modules` → `RED before 9d29111: 30 closures across ten modules` |
| `:5491` **T1** | `RED today x11 … the name does not exist.` → `RED before 9d29111 x11 … the name did not exist.` |
| `:5562` | `RED today x10: ``_txn.run_query`` does not exist and each seam hand-rolls the body.` → `RED before 9d29111 x10: … did not exist and each seam hand-rolled the body.` |
| `:6589` | `RED today on `briefs.py::_relate_briefed`` → `RED before 9d29111 on …` |
| `:6623` | `RED today (it returns ``already_acked=True``).` → `RED before 9d29111 (it returned …).` |
| `:6769` | `— expected RED)` → `— RED before 9d29111)` |
| `:6817` | `RED today, x10: the record carries `attempts`` → `RED before 9d29111, x10: the record carried …` |
| `:6875` | `— expected RED)` → `— RED before 9d29111)` |
| `:6981` | `— expected RED)` → `— RED before 9d29111)` |
| `:7010` | `RED today: all three calls pass NO deadline, so each silently takes the module` → `RED before 9d29111: … passed NO deadline, so each silently took the module` |

**Closed by `352db0e` (5) — tier T2:**

| file:line | before → after |
|---|---|
| `:7309` | `RED today x3: ``bootstrap_session``'s three calls … pass` → `RED before 352db0e x3: … passed` |
| `:7527` | `RED today x4 — but for the PLUMBING … the call below passes` → `RED before 352db0e x4 … the call below passed` |
| `:7699` | `RED today x11: not one production owner passes a ``url``` → `RED before 352db0e x11: … passed a ``url``` |
| `:7927` | `RED today x10: the record carries ``attempts``` → `RED before 352db0e x10: the record carried …` |
| `:7963` | `RED today: **the ELEVENTH owner**` → `RED before 352db0e: **the ELEVENTH owner**` |

Two judgment calls, stated so they can be overruled:
1. **`:7963` — I left `"the one every symbol-keyed enumeration misses"` in the PRESENT tense.**
   That clause is *still true*: scout is still a module-level function that a `_QUERY_SEAMS`-keyed
   pin still cannot see. Only the RED changed. Blanket past-tensing would have quietly asserted
   the structural hazard went away.
2. **Continuation lines left alone throughout.** e.g. `:1323`'s next line still reads "the shared
   jitter is never called". Under a `RED before <sha>:` marker that clause is scoped to the past;
   past-tensing it is a multi-token rewrite the brief forbids. Uniform, and disclosed rather than
   silently chosen.

**Residual sweep after the edits:**
```
$ git grep -nE "RED today|RED by construction|expected RED" -- loremaster/tests/test_retry_seam.py
NONE
```

### 2.4 Every hit adjudicated individually — the other 26, and why each is untouched

*"All remaining hits are X" is banned output*, so each gets its own line. **None is in Ruling
A's class** (a different wave, a different subject, a closing commit unrelated to the retry
substrate), and — decisively — **I have no green receipt for any of them**: brief-base §3
forbids running suites the brief did not name, so past-tensing them would be laundering a claim
I cannot substantiate. Introducing commit derived per site via `git log -S`.

| file:line | claim (abbrev.) | introduced by | verdict |
|---|---|---|---|
| `test_caplog_isolation.py:41` | "RED today; GREEN the moment a…" | `4c2efbf` (#101 caplog) | out of class · unverified · **LEAVE + escalate** |
| `test_caplog_isolation.py:94` | "RED today: the previous test's `propagate=False`…" | `4c2efbf` | out of class · unverified · **LEAVE + escalate** |
| `test_caplog_isolation.py:115` | "RED today. GREEN once lore-logger state is restored…" | `4c2efbf` | out of class · unverified · **LEAVE + escalate** |
| `test_config.py:512` | "BEHAVIOURALLY RED today: the unconstrained `str`…" | `333ba50` (startup) | out of class · unverified · **LEAVE + escalate** |
| `test_eager_startup.py:475` | "…goes RED today and only passes…" | `001f632` (eager build) | out of class · unverified · **LEAVE + escalate** |
| `test_eager_startup.py:892` | "…reports `…complete` → False (the RED today)" | `001f632` | out of class · unverified · **LEAVE + escalate** |
| `test_eager_startup.py:941` | "…the implementation may not yet emit (RED today)" | `001f632` | out of class · unverified · **LEAVE + escalate** |
| `test_extension.py:692` | "RED today: the extension's `bump_counter`…" | `76f04c5` | out of class · unverified · **LEAVE + escalate** |
| `test_extension.py:802` | "RED today: `factor` is…" | `07dd5d8` | out of class · unverified · **LEAVE + escalate** |
| `test_extension.py:843` | "RED today: both collapse to string." | `07dd5d8` | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:1015` | "RED today: Model A has no module-prefix reverse arm" | `b04d89a` (P4) | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:1524` | "RED today: `tests_for` has no module-prefix arm" | `4afdbf4` (#53) | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:1628` | "RED today: `references` has no module-prefix arm" | `4afdbf4` | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:3059` | "RED today (live-verified against this exact fixture)" | `297194e` | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:3112` | "RED today (live-verified): `blast_radius(...)`" | `297194e` | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:3181` | "RED today (live-reproduced): the bare query's…" | `9171021` | out of class · unverified · **LEAVE + escalate** |
| `test_graph_surreal.py:3353` | "RED today: the aggregate is 0" | `297194e` | out of class · unverified · **LEAVE + escalate** |
| `test_indexer_chunker_fault_isolation.py:248` | "RED today: the ParseError propagates out of index_all" | `df5431e` | out of class · unverified · **LEAVE + escalate** |
| `test_mcp_server.py:7796` | "RED today (raw f-string interpolation, no wrap)" | `c30edd6` | out of class · unverified · **LEAVE + escalate** |
| `test_resilient_db.py:569` | "BEHAVIOURALLY RED today: the default-mode mkdir yields 0755" | `333ba50` | out of class · unverified · **LEAVE + escalate** |
| `test_resilient_db.py:756` | "BEHAVIOURALLY RED today: a default-mode connect yields…" | `333ba50` | out of class · unverified · **LEAVE + escalate** |
| `test_retired_symbols.py:438` | "RED today at every site below." | `00f4301` | out of class · unverified · **LEAVE + escalate** |
| `test_surreal_store.py:3423` | "RED today: every racer sleeps a fixed base delay" | `8f24e11` (#102) | **nearest miss** — same finding family as Ruling A, different file+commit · unverified · **LEAVE + escalate** |
| `test_surreal_store.py:4585` | "RED today: the engine says 'must conform to'…" | `8f24e11` (#102) | **nearest miss**, as above · unverified · **LEAVE + escalate** |
| `test_surreal_harness.py:740` | "RED today x3: the record carries `attempts`…" | `d2d7b2c` → closed `352db0e` | ⚠ **IN Ruling A's class and falsified by THIS session — but the file is DO-NOT-TOUCH.** §5.4 |
| `test_task_ledger.py:1550` | "RED by construction; PKT-06 (f80e95a) shipped all three and it is GREEN today." | `ee0bec2` (#152) | ✅ **ALREADY CORRECT** — self-dated, names its closing commit, states the present truth. **No action. This is the form Ruling A prescribes, already in the tree.** |

---

## 3. RULING B — the file-level anchor

### 3.1 The sibling's shape, read first (as directed)

`test_surreal_harness.py:50-60` — note this block **moved by one line during my run** (commit
`968883d` edited it mid-session), which is itself a small demonstration of why per-site
addresses lose:

```
------------------------------------------------------------------------------
HOW TO RESOLVE THE ``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS IN THIS FILE.

They are review-pass identifiers from finding **#150**'s review wave. The reports they
name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) were ARCHIVED at
``7d2ff44`` and resolve, section-exactly, under
``docs/plans/v2/receipts/2026-07-20-150/`` (#152). …
```

I mirrored: same `---` rule, same heading sentence verbatim (house idiom, brief-base §7), same
archived-at-`7d2ff44` + resolves-under-path structure, same closing "every citation states its
own substance inline" clause.

### 3.2 ⚠ ONE DELIBERATE DIVERGENCE — the sibling's glob does not disambiguate

I re-verified §3.1's collision claim myself rather than inheriting it:

| label | `REPORT-audit-150-cold.md` | `REPORT-audit-150-final.md` |
|---|---|---|
| **R4** | `:182` teardown wall-clock widens ~40× | `:202` a false gate at `test_retry_seam.py:4842-4846` |
| **R5** | `:183` `drop_database` leaks its connection on failure | `:203` the #151 known-bound pin never names #151 |

**Confirmed: both files define R4 and R5, meaning different things.** The sibling's anchor
writes `REPORT-audit-150*.md` — a glob, which leaves a reader a coin-flip. Since every
`audit-150` citation in `_surreal_harness.py` resolves to **`-cold.md`** (matched by content:
`:344`/`:454` R5 = the connection leak; `:419` R4 = the ~40× wall-clock), my anchor names that
one file and says why. Mirroring the sibling's *shape* while preserving the disambiguation the
predecessor discovered — mirroring its glob would have thrown that finding away.

### 3.3 Ledger — RULING B

| file:line | before (per-site path) → after (short id) |
|---|---|
| `_surreal_harness.py:344-347` | `(#150; receipts under `docs/plans/v2/receipts/2026-07-20-150/`: REPORT-audit-150-cold.md R5 + REPORT-blindreader-150.md F10 — one function over…)` **4 lines** → `(audit-150 R5 / blindreader-150 F10, one function over…)` **2 lines** |
| `_surreal_harness.py:421-422` | `(#150; receipts under `…/2026-07-20-150/`: REPORT-blindreader-150.md F2 + REPORT-audit-150-cold.md R4)` **2 lines** → `(blindreader-150 F2 / audit-150 R4)` **1 line** |
| `_surreal_harness.py:457-459` | `(#150; receipts under `…/2026-07-20-150/`: REPORT-audit-150-cold.md R5 + REPORT-blindreader-150.md F10)` **3 lines** → `(audit-150 R5 / blindreader-150 F10)` **2 lines** |
| `_surreal_harness.py:44` | **NEW** — the 15-line file-level anchor, appended to the module docstring |
| `_surreal_harness.py:108` | **LEFT ALONE** — already leads with the durable `#151` (adjudicated P by the #152 pass). |

**Receipt that the form is now DRY.** The whole-file diff against HEAD is exactly two hunks —
the anchor, and one spelling fix:

```
$ cd /home/ejprice/PycharmProjects/lore && git diff -- loremaster/tests/_surreal_harness.py
@@ -41,6 +41,21 @@   + the 15-line anchor block
@@ -341,7 +356,7 @@  - …(audit-150 R5 / blindreader F10, one
                     + …(audit-150 R5 / blindreader-150 F10, one
```

Sites 2 and 3 return to **byte-identical HEAD text** — nothing left to maintain there. The
40-char directory now appears **once** in the file instead of three times, which was the whole
argument. The retained `blindreader F10` → `blindreader-150 F10` correction (the predecessor's
free fix) is kept deliberately: the anchor keys on `blindreader-150 F*`, so the inconsistent
spelling would no longer be resolved by it.

---

## 4. Verification

### 4.1 AST inertness — run by me, against TWO baselines

Docstrings and assert *messages* stripped; everything else — assertions, fixtures, constants,
signatures, control flow — compared by `ast.dump`. Diffing against the **pre-my-edits backup**
isolates my changes from the predecessor's uncommitted ones, which diffing against HEAD alone
cannot do:

```
loremaster/tests/test_retry_seam.py
   asserts: HEAD=308  pre-my-edits=308  now=308
   vs PRE-MY-EDITS backup : non-prose AST IDENTICAL
   vs HEAD (9601455)      : non-prose AST IDENTICAL
loremaster/tests/_surreal_harness.py
   asserts: HEAD=0  pre-my-edits=0  now=0
   vs PRE-MY-EDITS backup : non-prose AST IDENTICAL
   vs HEAD (9601455)      : non-prose AST IDENTICAL
guard exit= 0
```

308 matches the predecessor's count and `98980bd`'s. **I edited no assert message at all** (the
predecessor edited two under narrow authorisation; mine are pure docstring/comment), so the
message-stripping exclusion is not load-bearing for my diff.

Additional guarantee from the edit mechanism: every one of the 30 edits asserted its **exact
expected old text** at its exact line before replacing, and asserted the result stayed ≤110
cols. A single drifted line would have aborted the whole script with `MISMATCH`.

### 4.2 Gate tails — WITH COUNTS

Every gate `cd`'d with an **absolute path in the same command**; output captured, exit code
checked *before* interpretation.

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
531 passed, 1 warning in 18.94s
PYTEST_EXIT=0
```
**531 passed / 0 failed — identical to the brief's stated baseline**, as prose-only edits
require. A real passed-COUNT, not a silent "no tests ran".

```
$ uv run ruff check .
All checks passed!
RUFF_EXIT=0
```

```
$ ./scripts/typecheck.sh
Found 55 errors in 5 files (checked 146 source files)
TYPECHECK_EXIT=1
=== errors in MY files? === NONE
```
Exit 1 with exactly **55** — the packet-03 comms baseline, unrelated. **Zero in either file I
touched**, grep-confirmed rather than eyeballed.

**No other suite was run** — I touched only these two files, and brief-base §3 forbids running
suites the brief did not name.

### 4.3 The tree moved under me — disclosed

HEAD advanced **twice** during my run: `968883d` (docs(law): archive reports, never delete) and
`9601455` (docs(prod): #152 repoint production citations). The production files the predecessor
saw as dirty are now committed, so at gate time `git status` showed **only my two files**
modified — a cleaner attribution than the predecessor had. `968883d` also edited
`test_surreal_harness.py`, which is what shifted its `RED today` hit from `:739` to `:740`
between two of my own greps; I chased that discrepancy to ground rather than assuming a
mis-read.

### 4.4 ⚠ THE CWD TRAP FIRED ON ME TWICE — and the second one was SILENT

The brief said it had fired six times. It fired a seventh and an eighth, on me, after I had
read the warning:

1. **Loud.** A `cd …/loremaster` for pytest persisted; the next call's
   `grep … loremaster/tests/test_surreal_harness.py` resolved to a non-existent
   `loremaster/loremaster/tests/…` and failed with `No such file or directory`.
2. **SILENT, and this is the dangerous one.** In the same state,
   `git diff -- loremaster/tests/_surreal_harness.py` returned **empty output and exit 0** —
   because git resolved the pathspec relative to `loremaster/`. **An empty `git diff` reads as
   "my edits didn't land" or "nothing changed".** I nearly reported the Ruling B diff as
   missing. Re-run from an absolute `cd`, it showed both hunks correctly.

**Exposure: nil, verified rather than assumed.** Every edit used the `Edit` tool with absolute
paths or a script with an absolute `Path`; every population-deriving grep ran from the repo root
(`prov.py` pins `cwd=ROOT` explicitly); every gate used an absolute `cd` in-command. Only two
*read-only display* calls were affected.

**The datum worth keeping:** the loud failure cost 10 seconds. The silent one produced a
plausible, wrong answer that I would have written into this report. A warning did not save me
either time — checking `pwd` in the same command did.

---

## 5. Flags — everything I noticed, per scope law

### 5.1 ⚠ THE CLOSING WINDOW IS 3 REPORTS / 4 SITES — the predecessor's §5.1 found ONE

Swept bare rather than from §5.1's hand-list. Committed test prose cites **three** untracked
root reports that exist *right now* and are cited from `test_retry_seam.py`:

| citing site | cites | on disk? |
|---|---|---|
| `test_retry_seam.py:7147` | `REPORT-audit-151-cold.md` | untracked, at repo root |
| `test_retry_seam.py:8722` | `REPORT-audit-151-cold.md` | untracked, at repo root |
| `test_retry_seam.py:7537` | `REPORT-contract-151.md` | untracked, at repo root |
| `test_retry_seam.py:8221` | `REPORT-contract-151b.md` | untracked, at repo root |

**Recommended: `git mv` this wave's reports under `docs/plans/v2/receipts/2026-07-21-151-152/`
before the next image build** — now mandatory per the new CLAUDE.md archive law, and it makes
all four citations resolve for one command. I did **not** repoint them: repointing away would
destroy an address that is about to become durable. Cheap now, unrecoverable after.

### 5.2 26 `RED today`-class claims in 12 OTHER test files — adjudicated in §2.4, untouched

Every one has a `file:line` and an individual verdict in **§2.4**; none is bulk-classified.
The fork is genuine and unchanged from §5.2 of the predecessor's report — except that it is now
**quantified and provenance-derived**, and the population is **26, not "~40"**:

- **(a) real defect class** → wants its own scoped wave: run each suite, prove green, past-tense
  with the derived closing commit. **Plus an instrument**, per repo law (*a fix without an
  invariant is half a fix*): an AST scan over docstring/comment string literals refusing
  `RED today` / `expected RED` unless followed by a commit-shaped marker. `test_task_ledger.py:1550`
  already shows the compliant form, so the pin has a positive control on day one.
- **(b) accepted contract-archaeology.** Defensible for the 24 whose introducing commit *is* their
  closing commit — those docstrings were historical the day they were written.

**My recommendation: (a), and the instrument matters more than the 26 edits** — without it the
class regenerates at the next contract-first wave, which is precisely how 30 accumulated in one
file. **Note (b) does NOT cover the two `test_surreal_store.py` sites** (`8f24e11`, the #102
family) or `test_surreal_harness.py:740`: those were falsified by *later* commits, so they are
substantively stale in the same way T1/T2 were.

### 5.3 116 line-number citations and 48 dangling report names remain in the test tree

Derived now, not inherited — neither is in Rulings A or B, so neither was touched:

- **`<file>.py:<digits>` citations: 116 hits across 21 test files.** The predecessor swept only
  `scout\.py:[0-9]+`; the bare pattern finds the rest. **17 are in `test_retry_seam.py`**,
  including three inside prose I edited for tense: `:7309` cites `` `_txn.py:1021-1023` ``
  (**derived**: the three calls now begin at `_txn.py:1057`, `:1063`, `:1069`, and
  `bootstrap_session` itself starts at `:949` — so the cited span points at neither),
  `:3593` cites `briefs.py` "(line 107)/(line 634)/(line 677)",
  `:3660` cites `briefs.py:108`. **Those three are wrong today**, by the same mechanism that made
  `scout.py:171` wrong. I left them: fixing an *address* is Ruling B's business, not Ruling A's,
  and the brief forbids doing both on one line. The exact edit I would make for `:7309`:
  ``(``_txn.py:1021-1023``)`` → ``(``_txn.bootstrap_session``'s three calls)``.
- **`REPORT-*.md` citations: 117 hits, 54 distinct names, 31 files — only 6 names resolve**
  (the `2026-07-19-packet03` and `2026-07-20-150` archives). **48 dangle.** This is #153's
  mechanism measured on the test tree; §5.1's three are the subset still rescuable.
  Curiosity worth a glance: `test_mcp_server.py:6996` and `:7000` cite `REPORT-x.md`.

### 5.4 ⚠ `test_surreal_harness.py:740` is IN Ruling A's class but DO-NOT-TOUCH

```
:740  """RED today x3: the record carries ``attempts`` and ``elapsed_seconds`` and nothing else.
```
Introduced by `d2d7b2c` (#151 contract, RED), closed by **`352db0e`** — the identical claim,
identical wave and identical closing commit as tier T2's five, which I *did* fix. It is stale by
the operator's own criterion. **The brief lists this file under DO NOT TOUCH, so I left it and
flagged it instead of quietly widening my writable set.** The edit I would make, ready to apply:

```
-        """RED today x3: the record carries ``attempts`` and ``elapsed_seconds`` and nothing else.
+        """RED before 352db0e x3: the record carried ``attempts`` and ``elapsed_seconds`` and nothing else.
```
(107 cols — under the 110 limit, no rewrap.) Its green receipt already exists: the §4.2 gate run
covers this file, 531 passed / 0 failed.

### 5.5 The generalised lesson, restated from this pass

Three separate hand-lists lost to the tree in this one task: §5.2's "three" was **30**, §5.1's
one report was **three**, and the brief's single closing commit was **two**. In every case the
grep was cheap and the hand-list was confident. The durable-address argument (§5.3 of the
predecessor's report) has an exact analogue here: **a claim about the tree must be DERIVED from
the tree at the moment it is written, or it is already rotting** — which is the same law that
makes `RED before <sha>` better than `RED today`, one level up.

---

## 6. Compliance

- **Writable set respected.** Touched exactly `loremaster/tests/test_retry_seam.py`,
  `loremaster/tests/_surreal_harness.py`, and this report. `test_surreal_harness.py` was
  **read only** (§3.1 sibling form, §5.4 flag) — not modified; `git status` confirms it clean.
  Nothing under `loremaster/loremaster/`, `docs/`, `pyproject.toml`, `.claude/`.
- **Git state untouched.** No stage, no commit, no revert, no checkout. The lead commits.
- **No worktrees. No repo-wide auto-fixer.** Every edit was an individually-asserted,
  line-targeted string replacement or a single `Edit` call.
- **Ledger board untouched** — my brief names no task row (brief-base §5).
- **Backup retained** at `/tmp/apply152c-backup/` (md5s in §0) should the lead want a
  byte-exact revert of my 30 edits without disturbing the predecessor's.
