# REPORT-apply-152-tests-b

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - Task 1's population is **9 sites, not 7** — the grep found two the lead's hand-list missed (`:1684`, `:6161`). Both adjudicated + fixed. §1.
  - Task 2's population is **5 sites, not 3** — `:8900` and `:8972` carry the identical now-false `RED today` claim, falsified by the same commit. Both fixed. §2.
  - **The brief's causal attribution is wrong for §10d:** `:171→:176` was shifted by **352db0e**, NOT 98980bd. Past-tense markers name the correct commit per site. §1.1.
  - Task 3 applied as directed (archived path), but a **fork** exists: this file's sibling already solves the same problem with ONE file-level anchor. §3.1.
  - Local reflow of 2→3 lines at `:6161` and `:344` — unavoidable when a 16-char address becomes a path. No paragraph restructured.
  - **The fix shape was vindicated mid-session:** a concurrent agent's `scout.py` edit shifted the seams AGAIN (`571→576→578`, `599→608→610`). Renumbering would have shipped stale *within this session*. §1.2a.
  - Gate tree was **shared** with the concurrent agent (9 files modified, 7 not mine) — 531/0 is a joint result. §4.2a.
- **decisions-needed:**
  - **§5.1 — a CLOSING WINDOW, same shape as the one `7d2ff44` closed:** committed test prose cites `REPORT-contract-151b.md`, an untracked root scratch file. It exists *right now*; the next image build deletes it.
  - **§5.2** — 3 residual `RED today` claims (pre-existing, closed by `9d29111`), each with an individual verdict. Fix or leave?
  - **§3.1** — Task 3 form: per-site path (applied) vs file-level anchor (recommended).
- **receipts:** ledger §1–§3 · green-before-rewrite §2.1 · AST guard §4.1 · gate tails §4.2 · flags §5

---

## 0. What binds this report

Prose only. **No assertion, fixture, constant, or control-flow change** — proven mechanically in §4.1, not asserted.

**Tool honesty (brief-base §4 / repo dogfood protocol):** I used `lore_findings` for #152/#153 (a ledger read). Every *sweep* here used **grep**, and I say so deliberately: these are non-symbol textual seams — line-number citations inside comments and docstrings — which is sanctioned fallback case (b) in the repo's dogfood protocol. A symbol graph structurally cannot see `scout.py:171` sitting in a string literal. No friction filed: the fallback is the protocol working, not a lore gap.

---

## 1. TASK 1 — `scout.py:NNN` → symbol citations

### 1.1 Ground truth, derived — and a correction to the brief

The brief supplied a table and told me not to trust it. Correct call — **one row's causal attribution is wrong.**

| seam | prose said | actual now | **shifted by** |
|---|---|---|---|
| `_scout_query`'s `retry_on_conflict` | `:171` | **176** | **`352db0e`** ⟵ *not 98980bd* |
| `_consume_live`'s `retry_on_conflict` | `:571` | **576** | `98980bd` |
| `_safe_kill`'s `retry_on_conflict` | `:599` | **608** | `98980bd` |

Receipt — `98980bd`'s only two `scout.py` hunks are at `@@ -568` and `@@ -596`, **both below line 171**, so it cannot have moved `_scout_query`. Bisected directly:

```
352c232:loremaster/loremaster/scout.py:171:    return await retry_on_conflict(lambda: _scout_query_once(...))   # unlabelled
855c266:loremaster/loremaster/scout.py:176:    return await retry_on_conflict(                                    # labelled
```
`352db0e` sits between them, and its message says it: *"scout._scout_query gets a label only, no url (R4)"*.

This matters beyond pedantry: Task 2 requires past-tense markers to **name the commit that closed it**. Had I inherited the brief's table, all five markers would have said `98980bd` and two would have been freshly false — shipping a new instance of the defect class I was sent to fix.

### 1.2 The population: 9, not 7

```
$ git grep -nE "scout\.py:[0-9]+" -- loremaster/tests/
```
returned **9** hits. The two beyond the hand-list are real and independently wrong:

| file:line | cited | ground truth | verdict |
|---|---|---|---|
| `:1684` | `scout.py:328` for a *"compare-and-set WRITE on the command table"* | **328 is `_ensure_connection`.** The CAS (`UPDATE … WHERE status = $pending_status RETURN BEFORE`) is `_mark`, at 401–443 | **wrong in substance, not just number** |
| `:6161` | `scout.py:138-145` for the transport-fault law | block is **139–146** | off-by-one; **pre-existing** — it was 139 at `352c232`, `352db0e` *and* `98980bd`. Never correct. |

`:1684` is the more interesting catch: a reader following it lands on connection caching and finds no CAS at all. That is #152's exact failure mode — an address that resolves to the *wrong thing*, which is worse than one that dangles, because it looks like it worked.

I also swept **bare** `scout\.py` (anchor-free, per repo law) across both writable files: 11 further mentions, all file-level or symbol-level, none carrying a line number. No residue.

### 1.2a ⚠ THE FIX SHAPE WAS VINDICATED MID-SESSION — the numbers moved a THIRD time

While I worked, the concurrent agent editing `loremaster/loremaster/` touched `scout.py`. **Every line number shifted again**, measured after my edits landed:

| seam | brief's table | at `98980bd` | **NOW** |
|---|---|---|---|
| `_scout_query` | 171 | 176 | 176 |
| `_consume_live` | 571 | 576 | **578** |
| `_safe_kill` | 599 | 608 | **610** |

**Had I renumbered to the brief's verified-correct `576`/`608`, this fix would have shipped ALREADY STALE** — falsified inside the same session, by a sibling agent, before the lead could even commit it. The brief predicted this trap ("you would be the third agent to fall into it") and the tree proved it in real time.

Every symbol citation I wrote is still correct, verified against the current tree:

```
_mark              403:    async def _mark(
_scout_query       167:async def _scout_query(
_scout_query_once  150:async def _scout_query_once(
_consume_live      545:    async def _consume_live(...)
_safe_kill         587:    async def _safe_kill(...)
```

All five moved. None of my citations did. That is the whole argument for §5.3 in one table.

### 1.3 Fix shape — and the idiom I matched

Lead-specified: cite the symbol. I did **not** invent a form — `test_retry_seam.py:5598` already uses `` `scout.py::_open_command_connection` ``, so `::` is the house idiom (brief-base §7). Every repoint uses it.

### 1.4 Ledger — Task 1

| file:line | before → after |
|---|---|
| `test_retry_seam.py:1684` | `(scout.py:328)` → ``(``scout.py::_mark``)`` |
| `test_retry_seam.py:6161` | `scout.py:138-145 states this law` → `` `scout.py::_scout_query_once`'s banner states this law `` |
| `test_retry_seam.py:8113` | `` `scout.py:171` (`_scout_query`) `` → `` `scout.py::_scout_query` `` (+ tense, §2) |
| `test_retry_seam.py:8217` | ``thread a url into `scout.py:171` `` → ``thread a url into `scout.py::_scout_query` `` |
| `test_retry_seam.py:8888` | ``f"at `scout.py:571`."`` → ``f"at `scout.py::_consume_live`."`` |
| `test_retry_seam.py:8961` | ``f"`scout.py:599`."`` → ``f"`scout.py::_safe_kill`."`` |
| `test_retry_seam.py:8151` · `:8854` · `:8935` | address + tense together — §2.2 |

**Residual sweep after the edits: `git grep -nE "scout\.py:[0-9]+" -- loremaster/tests/` returns NOTHING.**

---

## 2. TASK 2 — `RED today` claims that are now false

### 2.1 ⚠ GREEN BEFORE REWRITE — the receipt the brief demanded

A pin still genuinely RED must never be past-tensed. Verified **first**, edited second:

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_retry_seam.py -q -p no:randomly \
    -k "TestScoutsQuerySeamIsAttributedByLabelOnly or TestScoutsBestEffortSeamsAreAttributedByLabelOnly"
..........                                                               [100%]
10 passed, 464 deselected in 0.97s
```

All 10, named (a count alone would not prove *which*):

```
test_scouts_query_exhaustion_carries_a_label_OF_ITS_OWN
test_scouts_query_exhaustion_carries_NO_url_a_KNOWN_BOUND
test_scouts_live_subscription_exhaustion_carries_a_label_OF_ITS_OWN
test_scouts_live_subscription_exhaustion_carries_the_ENGINES_OWN_TEXT
test_scouts_kill_exhaustion_carries_a_label_OF_ITS_OWN
test_scouts_kill_exhaustion_carries_the_ENGINES_OWN_TEXT
test_scouts_three_seams_label_their_exhaustion_THREE_DIFFERENT_WAYS
test_scouts_live_subscription_exhaustion_carries_NO_url_a_KNOWN_BOUND
test_scouts_kill_exhaustion_carries_NO_url_a_KNOWN_BOUND
test_a_LABELLED_call_that_raises_the_signal_BARE_logs_an_EMPTY_engine_error
```

Every pin whose claim I rewrote is in that set. **0 failed** — no genuinely-RED pin was touched.

### 2.2 The population: 5, not 3 — and the historical claim is PRESERVED

The brief named `:8151`, `:8854`, `:8935`. Sweeping `RED today` found **two more** in the same two classes, falsified by the same commit:

| file:line | before → after | closed by |
|---|---|---|
| `:8113` (§10d banner) | *"`scout.py:171` (`_scout_query`) **is** a FOURTH unlabelled call… its exhaustion **produces** the same unattributable record… It **is** NOT exempt"* → *"**Before 352db0e**, `scout.py::_scout_query` **was** a FOURTH unlabelled call… **produced**… It **was** NOT exempt"* | 352db0e |
| `:8151` | ``"""RED today: `scout.py:171` passes no `label`, so the driver suppresses…"`` → ``"""RED before 352db0e: `scout.py::_scout_query` passed no `label`, so the driver suppressed…"`` | 352db0e |
| `:8216` (⚠ DISCLOSED) | *"**today** the record carries no url because it carries no label either… it **becomes** a real tripwire the moment the label lands"* → *"⚠ DISCLOSED (**HISTORICAL — closed at 352db0e**)… the record **carried**… it **became** a real tripwire the moment the label **landed**"* | 352db0e |
| `:8854` | ``"""RED today: `scout.py:571` passes no `label`…"`` → ``"""RED before 98980bd: `scout.py::_consume_live` passed no `label`…"`` | 98980bd |
| **`:8900`** ⟵ *beyond hand-list* | `"""RED today, and it is the HALF THE FALSE CLAUSE PROMISED.` → `"""RED before 98980bd, and it is…` | 98980bd |
| `:8935` | ``"""RED today: `scout.py:599` passes no `label`.`` → ``"""RED before 98980bd: `scout.py::_safe_kill` passed no `label`.`` | 98980bd |
| **`:8972`** ⟵ *beyond hand-list* | `"""RED today. Same property as the live seam's…` → `"""RED before 98980bd. Same property…` | 98980bd |

**Nothing was deleted.** Every claim keeps its full substance — what the pin caught, why it mattered, the mechanism — and gains a date. That was the brief's explicit requirement and it is also the right call: these sentences are the only surviving record of what these pins were built to catch.

Two judgment calls I made rather than mechanically past-tensing, both stated so you can overrule:

1. **`:8113` — I left `"it propagates, it logs nothing of its own"` in the PRESENT tense.** Those two clauses are *still true*: `_scout_query`'s disposition did not change at 352db0e, only its attribution. Blanket past-tensing would have quietly asserted the seam stopped propagating.
2. **`:8113` — `"It was NOT exempt"`.** Still true today (after 98980bd the allowlist holds `execute_transaction` alone), but the sentence is arguing about the *pre-fix* decision, so past tense is the honest frame.

### 2.3 `:1684` — the one site where I fixed the address and left the tense

`:1684` says scout *"runs a compare-and-set WRITE … **with no retry** and a raw SDK `QueryError`"* — no longer true; `_mark` routes through `_scout_query` and retries.

**I fixed only the address.** Reason: the paragraph's frame is *already* explicitly historical — it opens **"BLOCKER 2, closed."** and narrates what the enumerator found at the time (*"It found ten. It structurally COULD NOT find `scout.py`"*). The verbs are inside that past frame, and the next sentence closes it: *"On the CORRECT build it still raised on the first conflict."*

**The alternative reading, since it produces a different edit:** treat the present-tense verbs as free-standing claims and past-tense them (`ran a CAS write … with no retry`). I would **not** pick it — it flattens a deliberate narrative voice for no gain in truth, and the brief forbids improving wording. Flagging it because it admits two readings.

---

## 3. TASK 3 — the three `_surreal_harness.py` repoints, re-adjudicated

### 3.0 The premise change is REAL — verified, not inherited

`REPORT-adj-152-tests.md` §8 rows 2–4 proposed collapsing to a bare `(#150)` **because the reports were unrecoverable.** That premise is now false. Verified tracked, not merely present on disk:

```
$ git ls-files docs/plans/v2/receipts/2026-07-20-150/
  … REPORT-audit-150-cold.md   REPORT-audit-150-final.md   REPORT-blindreader-150.md  (+5)
```

And every cited label resolves — checked individually, not assumed:

| label | resolves to |
|---|---|
| `audit-150 R5` | `REPORT-audit-150-cold.md:183` — *"`drop_database` leaks its connection on failure"* |
| `audit-150 R4` | `REPORT-audit-150-cold.md:182` — *"worst-case teardown wall-clock widens ~40×"* |
| `blindreader-150 F10` | `REPORT-blindreader-150.md:288` — *"the admin socket leaks on every failure path"* |
| `blindreader-150 F2` | `REPORT-blindreader-150.md:131` — *"`drop_database` runs TWO independent 2.0s budgets"* |

### 3.1 ⚠ THE FINDING THAT DECIDED THE FORM — `audit-150` is AMBIGUOUS

**The archive contains TWO `audit-150` reports, and their label namespaces COLLIDE.** Both `REPORT-audit-150-cold.md` and `REPORT-audit-150-final.md` define an **R4** *and* an **R5** — meaning entirely different things:

| label | `-cold.md` | `-final.md` |
|---|---|---|
| R4 | teardown wall-clock widens ~40× | a false gate in `test_retry_seam.py:4842` |
| R5 | `drop_database` leaks its connection | the #151 known-bound pin never names #151 |

So the adjudicator's proposed bare `(#150)` **and** a naive `(#150, audit-150 R5)` are *both* under-specified — a reader has a 50% chance of landing on an unrelated finding. **Only naming the file disambiguates.** This is what settled the form: I matched each citation to its report by content (§3.0 table), and every one resolved to **`-cold.md`**.

### 3.2 Ledger — Task 3, with the per-site choice and why

I used **`#150` + the archived path**, not one or the other. The reasoning is uniform, so I state it once rather than three times: **`#150` is the better address for the CLAIM** (durable forever, survives any archive reshuffle, carries the adjudicated *why*); **the archived path is the better address for the EVIDENCE** (section-exact, and per §3.1 the only form that disambiguates `-cold` from `-final`). Dropping either loses something real.

| file:line | before → after |
|---|---|
| `_surreal_harness.py:344` | `(audit-150 R5 / blindreader F10, one function over…)` → `(#150; receipts under `docs/plans/v2/receipts/2026-07-20-150/`: REPORT-audit-150-cold.md R5 + REPORT-blindreader-150.md F10 — one function over…)` |
| `_surreal_harness.py:419` | `(blindreader-150 F2 / audit-150 R4)` → `(#150; receipts under `docs/plans/v2/receipts/2026-07-20-150/`: REPORT-blindreader-150.md F2 + REPORT-audit-150-cold.md R4)` |
| `_surreal_harness.py:454-455` | `(audit-150 R5 / blindreader-150 F10)` → `(#150; receipts under `docs/plans/v2/receipts/2026-07-20-150/`: REPORT-audit-150-cold.md R5 + REPORT-blindreader-150.md F10)` |
| `_surreal_harness.py:108` | **LEFT ALONE** — adjudicated **P**; already leads with the durable `#151`. |

Site `:344` also silently fixes the inconsistent `blindreader F10` spelling (the sibling always writes `blindreader-150`) — a free correction inside an address I was already replacing, disclosed rather than slipped in.

The directory path is kept **whole on one line** at all three sites. A path split across a line break is not greppable and not clickable, which would defeat the point of repointing at it.

### 3.3 ⚠ FORK — per-site path (applied) vs file-level anchor (my recommendation)

The brief directed per-site paths and that is what shipped. But this admits two readings that produce different diffs, so per brief-base §2 both are written down.

- **(A) Per-site archived path — APPLIED.** Every site self-resolves with no reliance on the reader finding an anchor block. *Cost:* the same 40-char directory now appears **three times in one file** — precisely the duplication `ONE IMPLEMENTATION` warns about. If the archive is ever reorganised, three sites go stale together.
- **(B) One file-level anchor — WHAT I WOULD PICK.** **This is not a hypothetical: the sibling file already does it**, from this very wave — `test_surreal_harness.py:50-60` carries a block headed *"HOW TO RESOLVE THE `blindreader-150 F*` / `audit-150 R*` CITATIONS IN THIS FILE"*, naming the same archive directory. The adjudicator's own note that `_surreal_harness.py` *"has no anchor block (unlike its test sibling), so it inherits no resolution"* diagnoses exactly this. Under (B) the three sites keep their short readable ids and one block resolves them all.

**Recommendation: (B), or (A)+(B) together.** (B) is the established, already-shipped convention twenty lines away, it is DRY, and it gives the *file* one place to update. I did not apply it because it adds a block — beyond "change the address or the tense" — and that is a scope call that belongs to the operator, not to me.

---

## 4. Verification

### 4.1 AST guard — I ran it, I did not assume it

The brief warned the lead would AST-verify assertions against `98980bd`. I ran that check **myself** first, and made it strictly stronger: it compares not only assert *test expressions* but the **entire non-prose AST** — with docstrings and assert messages stripped — so a changed fixture value, constant, or control-flow branch cannot hide anywhere in the file, not just inside an `assert`.

```
loremaster/tests/test_retry_seam.py: 308 assertions @ 98980bd -> 308 now  BYTE-IDENTICAL  | full non-prose AST (fixtures, constants, control flow) also IDENTICAL
loremaster/tests/_surreal_harness.py: 0 assertions @ 98980bd -> 0 now  BYTE-IDENTICAL  | full non-prose AST (fixtures, constants, control flow) also IDENTICAL
guard exit=0
```

308 matches `98980bd`'s own stated count exactly. Script at `/tmp/assert_guard.py` (not written into the repo — outside my writable set).

Two failure **messages** were edited (`:8888`, `:8961`) — prose inside `assert … , (…)`, deliberately excluded from the expression comparison and explicitly sanctioned: `98980bd` did the same under narrow lead authorization. Named here so the lead can diff them precisely rather than hunt.

### 4.2 Gate tails — WITH COUNTS

Every gate `cd`'d with an **absolute path in the same command**, output captured to a variable, exit code checked before interpretation.

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
531 passed, 1 warning in 26.55s
PYTEST_EXIT=0
```
**531 passed / 0 failed — identical to the pre-edit baseline**, as prose-only edits require. A real passed-COUNT, not a silent "no tests ran".

```
$ cd /home/ejprice/PycharmProjects/lore && uv run ruff check .
All checks passed!
RUFF_EXIT=0
```

```
$ ./scripts/typecheck.sh
Found 55 errors in 5 files (checked 146 source files)
TYPECHECK_EXIT=1
=== errors in MY files? === NONE in touched files
```
Exit 1 with exactly **55** — the packet-03 comms baseline, unrelated. **Zero in either file I touched**, grep-confirmed rather than eyeballed.

### 4.2a ⚠ THE GATE TREE WAS SHARED — my 531/0 is a JOINT result, not an isolated one

Disclosed because a green count implies more than it should here. At gate time `git diff --name-only` showed **9** modified tracked files, not 2:

```
loremaster/loremaster/briefs.py      render.py    scout.py    search.py
loremaster/loremaster/server.py      store/_txn.py           store/surreal.py
loremaster/tests/_surreal_harness.py loremaster/tests/test_retry_seam.py     <- MINE
```

The seven production files are the **concurrent agent's** repoints (the brief assigned them to another agent; I touched none of them — all 14 of my `Edit` calls targeted the two test files, and §4.1's AST guard independently proves my two files' logic is byte-identical to `98980bd`).

**What this does and does not license:** 531/0 proves the *combined* tree is green — which is the useful fact, and it is unchanged from the pre-edit baseline. It does **not** isolate my edits from theirs. My edits are prose-only and AST-proven inert (§4.1), so my own contribution to that count is provably zero-risk; but if the lead needs a clean attribution for the production half, that is the other agent's gate to run, not a number I can claim.

### 4.3 ⚠ THE CWD TRAP FIRED ON ME — disclosed

The brief said it had fired six times. It fired a seventh — on me. A `cd` into `docs/plans/v2/receipts/2026-07-20-150/` persisted into the next call, which then failed to find `pyproject.toml`.

**Exposure: nil, and I verified that rather than assuming it.** The trap fired on a *read-only* lookup which **failed loudly** (exit 2, `cannot open file`) instead of silently returning wrong data. I re-checked call ordering: every `git grep` that derived a population ran from the repo root **before** the `cd`, and every `Read`/`Edit` used absolute paths. No edit, gate, or count is affected. Every command after it uses an absolute `cd` in the same invocation.

Worth the lead's attention as a datum: the warning was in my brief, I had read it, and I still did it. The instrument that saved this was not the warning — it was that the failure was **loud**. A relative path that happened to resolve in both directories would have been silent.

---

## 5. Flags — everything I noticed, per scope law

### 5.1 ⚠ A CLOSING WINDOW — committed prose cites an untracked scratch report *right now*

`test_retry_seam.py:8219` (inside the text I edited) cites **`REPORT-contract-151b.md`**. That file is an **untracked scratch file at the repo root** — the exact class repo law requires *deleted before any image build*.

**This is #153's mechanism live, mid-flight.** It is the same window `7d2ff44` closed for the #150 wave, and it is open again for the #151/#152 wave — `git status` shows **15 untracked `REPORT-*.md`** at the root, several cited from committed prose.

I did **not** repoint it. Repointing it away would *destroy* a currently-resolvable address; the correct fix is archival, which belongs to the lead and costs one `git add`. Per #153's own receipt, that single command made 15 in-tree citations resolve last time.

**Recommended: `git add` this wave's reports under `docs/plans/v2/receipts/2026-07-21-151-152/` before the next image build.** This is cheap now and unrecoverable after.

### 5.2 Residual `RED today` claims — individually adjudicated, NOT bulk-classified

Repo law bans *"all remaining hits are X"*. Three residual hits in my writable file mention scout; each gets its own verdict:

| file:line | claim | verdict |
|---|---|---|
| `test_retry_seam.py:2052` | *"RED today: the ten `_query` bodies, scout's bare calls (one a compare-and-set WRITE)…"* | **Stale — closed by `9d29111`** (the ONE-retry-seam commit), not by this session. Pre-existing. |
| `test_retry_seam.py:4717` | *"RED today: 30 closures across ten modules, plus scout's eleventh copy."* | **Stale — closed by `9d29111`.** Pre-existing. |
| `test_retry_seam.py:5491` | *"RED today x11 (the ten store seams + scout): the name does not exist."* | **Stale — closed by `9d29111`.** Pre-existing. |

**Left alone, deliberately.** None was falsified by this session's commits, none carries a line-number citation, and all three belong to a much larger pre-existing population — **~40 `RED today` claims across the test tree** (`test_graph_surreal.py`, `test_eager_startup.py`, `test_extension.py`, `test_config.py`, `test_resilient_db.py`, and more), most outside my writable set entirely.

**Operator's call**, and the fork is genuine: this is either (a) a real defect class — a suite whose prose systematically describes a world that no longer exists, which is #152's thesis exactly — or (b) accepted contract-archaeology, where `RED today` is understood to mean "RED when written". If (a), it wants its own scoped wave **and an instrument** (repo law: *a fix without an invariant is half a fix*) — plausibly an AST scan asserting no docstring says `RED today` without a commit marker. Bulk-rewriting 40 sites by hand is exactly the churn #152's adjudication warns against.

### 5.3 The durable-address lesson, generalised

Three of the nine Task-1 sites were stale, and **`:6161` was never correct at all** — it shipped off-by-one and no gate could tell. A line number is wrong the instant anyone inserts a line above it, and *nothing in this repo checks it*. That is #153's point restated from the test tree: **the fix for a citation class is making the address durable BY CONSTRUCTION, not renumbering.** Symbol citations (§1.3) are durable; `#150`-style ledger rows are durable; archived paths are durable. Line numbers never are.

Worth pairing with §5.2's instrument if that wave happens: an AST scan over string literals refusing `<file>.py:<digits>` in test prose would have caught all nine of these mechanically, including the one that was born wrong.

---

## 6. Compliance

- **Writable set respected.** Touched exactly `loremaster/tests/test_retry_seam.py`, `loremaster/tests/_surreal_harness.py`, and this report. `test_surreal_harness.py` was **read only** (for its anchor form, §3.3) — not modified. Nothing under `loremaster/loremaster/`, `docs/`, `pyproject.toml`, `.claude/`.
- **Git state untouched.** No stage, no commit, no revert. The lead commits.
- **No worktrees.** No repo-wide auto-fixer — every edit is an individually-targeted string replacement (`git diff --stat`: 2 files, +36/−29, all prose).
- **Ledger board untouched** — my brief names no task row (brief-base §5).
