# REPORT-contract-04b1-253 — #253's contract addendum

brief-base v7 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **⚠ THE BRIEF'S PREMISE WAS FALSE.** The mid-flight ping DID land: `test_blocks_edge.py`
  **SECTION I** (14 pins for #253) was committed at **`98d5084`**, after the `f2bebfc` the
  brief names as HEAD. I did not re-pin it. **This contract is strictly ADDITIVE.**
- **deviation:** wrote a *different* file than a from-scratch #253 contract — an addendum of
  the pins SECTION I lacks. Writing the commissioned file would have been contract copy #2.
- **deviation:** built wrong `query_tasks` implementations (scratch copy ONLY, never the repo
  tree) to grade fixtures. Reading fork on the brief's "do not implement" — see §ESCALATIONS E-G.
- **Packages considered:** none — no mechanism specified; this deliverable is tests only. The
  one instrument question (rows-read counter) was resolved by REUSING the in-tree
  `test_blocks_edge::_rows_read` via import, not by adding a dependency or a copy. Verdict on
  the two existing in-tree query-COUNT instruments: `keep_with_trigger` — see §INSTRUMENT.
- **decisions-needed:**
  1. **BLOCKER — `test_blocks_edge.py::TestTheReadIsBOUNDEDByTheCallersFilter::test_rows_read_does_NOT_grow_with_the_size_of_the_LEDGER[owner-filter]` is UNSATISFIABLE.** It fails in fixture setup on every build, including two correct bounded ones. One-line fix, not my writable set. §ESCALATIONS E-A.
  2. Merge decision: this file + SECTION I, or fold one into the other. §ESCALATIONS E-B.
  3. `_rows_read`'s home — a test module importing a sibling test module. §ESCALATIONS E-C.
- **pins:** 23 collected · **declared-RED: 2** (taken from `--collect-only` before any run) ·
  observed RED: exactly those 2, both ways, no unexpected reds, no declared-green.
- **gates:** `./scripts/typecheck.sh` **EXIT=0** (all 5 members, loremaster 171 files) ·
  `uv run ruff check .` **EXIT=0, unpiped** · `pytest -n auto` this file **2 failed, 21 passed** ·
  `test_task_ledger.py` **234 passed** (unharmed by the cross-module import).
- **satisfiability receipt:** a correct bounded build takes this contract to **23 passed, 0 failed**.
- **scratch provenance (#140):** `loremaster.__file__` → `/tmp/wb253/loremaster/loremaster/__init__.py`
  (via `./scripts/scratch_copy.sh`); scratch `tasks.py` restored byte-exact, asserted in-harness.
- **receipt pointers:** §WRONG BUILDS (the 7 measured builds + what each contract saw) ·
  §GAP MAP (SECTION I vs this file, per requirement) · §ESCALATIONS · §RESIDUALS.

---

## 0. Ground truth, established first

The brief states HEAD = `f2bebfc` and that the #253 correction did not land. Both were stale
by the time I read them:

| sha | what |
|---|---|
| `0f4656c` | docs — #253 folded into 04b-1 scope by operator ruling |
| `688621b` | the 80-pin contract — **no #253 content** (`grep -c 253` → 0) |
| `f2bebfc` | docs — the five escalation rulings (brief's stated HEAD) |
| **`98d5084`** | **`test_blocks_edge.py` SECTION I — #253, 14 pins.** Actual HEAD. |

`98d5084`'s own commit message says it duplicates work in flight from this agent and that
"both will be diffed rather than both shipped; two contracts pinning one behaviour is how
two 04a-era suites came to contradict each other." **So I wrote the diff, not the twin.**

Deliverable: `loremaster/tests/test_query_tasks_bounded.py`, 23 pins, re-pinning nothing.

## 1. GAP MAP — the brief's three required properties against what already existed

| brief requirement | SECTION I (`98d5084`) | this addendum |
|---|---|---|
| **1** — no unbounded read; filters push down | ✅ pinned, `status`/`owner` legs | — |
| **1** — *"blocker resolution bounded by the candidate set's `blocked_by`/`blocks` edges"* | ❌ **not pinned** — neither growth leg supplies `blocked=` | ✅ `TestTheBLOCKEDPathIsBoundedToo` (the 2 RED pins) |
| **2(a)** — out-of-filter blocker still counts | ⚠️ pinned only where the blocker is **NON-terminal**, where the naive build is right by accident | ✅ `TestATerminalBlockerOUTSIDEtheCandidateSetStillRESOLVES` |
| **2(b)** — never-minted blocker fail-closed | ✅ pinned | — |
| **2(c)** — terminal = `done`/`wontfix` | ✅ pinned, ∀ six statuses | — |
| **2(d)** — partition never disagrees with the CAS | ✅ pinned over ONE-HOP shapes | ✅ extended to a 4-deep branching DAG (the packet's "≥3 deep AND branching" floor, which SECTION I does not meet) |
| **3** — fixture discriminates, N ≫ K | ✅ 60 vs 5 growth comparison | ✅ same instrument, reused by import |
| *(unstated, found by measurement)* | — | ✅ one-hop vs transitive · field identity vs narrowed projection · filter values not interpolated · filters AND-ed not OR-ed |

## 2. WRONG BUILDS — measured, not asserted

Seven `query_tasks` bodies built in the scratch copy; each run against SECTION I's four
classes and against this file. **Two of these findings contradicted my own prediction and
changed the contract** — the value was in running them, not in reasoning about them.

| build | what it does wrong | SECTION I sees | this addendum sees |
|---|---|---|---|
| **BASE** | nothing — correct + bounded | 2 failed *(see E-A, E-B)* | **23 passed** ✅ satisfiability |
| **W-1** | naive push-down; `status_by_id` from the `WHERE` rows only | **passes all 11 regression pins** ⚠️ | 4 RED (2 terminal-blocker + 2 boundedness) |
| **W-2** | filters down, but full-table re-read whenever `blocked` is asked | **passes everything** ⚠️ | 2 RED (boundedness) |
| **W-3** | correct, bounded, but blockers resolved by `+collect` **closure** (over-blocks) | passes everything ⚠️ | 2 RED (one-hop) |
| **W-3b** | correct, bounded, bare `@.{1..n}` **terminal-depth only** (under-blocks) | passes everything ⚠️ | 3 RED (one-hop) |
| **W-4** | correct, bounded, **narrowed projection** | passes everything ⚠️ | 7 RED (field identity) |
| **W-5** | correct, bounded, **values interpolated** into the statement | passes everything ⚠️ | 5 RED (hostile values) |
| **W-6** | correct, bounded, predicates **OR-joined** | passes everything ⚠️ | 2 RED (conjunction) |

### 2.1 The finding that matters most: W-1 defeats the pins written for it

**This answers `98d5084`'s own open question** (*"each of the 11 must be shown to go RED on a
NAIVE bounded rewrite"*). Measured answer: **none of them does.**

SECTION I's `test_a_blocker_EXCLUDED_by_the_STATUS_filter_still_counts` uses an `in_progress`
blocker; its owner twin uses a `claimed` blocker. Both are **non-terminal**, so both expect
BLOCKED — and W-1's fail-closed default answers BLOCKED for every blocker it cannot see. It
passes **for the wrong reason**. The third out-of-filter pin uses a phantom (fail-closed is
genuinely correct there), and the ∀ agreement pin queries `blocked=False` with no
`status`/`owner`, so its candidate set is the whole table and W-1 is indistinguishable from
correct. This is fixture *value monoculture* on the terminal/non-terminal axis, inside the
class written to guard the property.

The uncaught direction is a blocker that is **TERMINAL and outside the candidate set**: truth
says it resolves and the dependent is claimable; W-1 calls it unresolved and **drops claimable
work from the served answer**, silently, while the claim CAS grants it to anyone asking by id.
That is the finding's own damage pattern, from the other side. Now pinned, both filters.

### 2.2 Two pins my own measurements proved were decoration, and I fixed

- `test_status_AND_owner_AND_blocked_together_are_a_CONJUNCTION` passed W-6. An OR-join served
  `{wanted, blocked_decoy}` and the `blocked` conjunct then removed the decoy — the pin passed
  the build it existed to kill, for a **fixture-arithmetic** reason (the alignment trap,
  CLAUDE.md axis 3). Fixed by adding a decoy excluded by `owner` **alone** that stays unblocked.
- `test_a_task_whose_DIRECT_blocker_is_OPEN_is_BLOCKED` was unproven until I built **W-3b**;
  W-3 alone only exercises the over-blocking direction. The class ships as a complementary
  pair because the two error directions need two different wrong builds.

`agent-"quoted"` stayed GREEN under W-5 while the other three hostile values reddened — a
double quote does not break a single-quoted SurrealQL literal. A single-shape fixture here
would have been a coin flip; that is what the four-mechanism parametrisation buys.

### 2.3 Reproducing it

No `/tmp` path is a durable address (repo law), so the harness is described rather than cited.
It is ~90 lines: read `tasks.py`, slice the `query_tasks` body between
`rows = self._as_rows(await self._query(f"SELECT * FROM {TASK_TABLE}"))` and `return selected`,
substitute each variant body, run `pytest -q -n auto` over the two node sets, restore, assert
byte-exactness. The variant bodies are ordinary rewrites of that block; §2's column 2 is a
complete description of each. Recommend the builder's wave keeps this as a committed
`scripts/`-level helper if the lead wants it re-runnable — that is a scope question, not mine.

## 3. THE PINS, per property, with the wrong build each kills

**Property 1 — bounded read** (`TestTheBLOCKEDPathIsBoundedToo`, **the 2 RED pins**)
- `test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked[status-filter|owner-filter]` — kills
  W-2. Growth comparison (5 vs 60 unrelated tasks), never a threshold: a threshold is a value a
  builder tunes until it passes. **Measured RED at `98d5084`: 7 rows vs 62.**
  *Wrong build that would still pass:* one that returns `[]` — killed by the answer-cardinality
  leg asserted at both sizes.
- `test_the_UNFILTERED_blocked_read_is_ALLOWED_to_grow` — positive control (the same instrument
  on the same call must be seen GROWING) **and** a deliberate non-requirement: `query_tasks(blocked=…)`
  with no `status`/`owner` asks about every task, so its cost is the answer's cost. A builder who
  "fixes" that number has truncated a served answer.

**Property 2(a), the uncovered direction** (`TestATerminalBlockerOUTSIDEtheCandidateSetStillRESOLVES`)
- `test_a_DONE_blocker_outside_the_{STATUS,OWNER}_candidate_set_still_RESOLVES` — kills W-1.
  *Wrong build that would still pass:* any build using a non-terminal blocker in its fixture —
  which is precisely SECTION I's, hence this class.

**Property 2(c)/2(d), depth** (`TestTheBlockedPartitionIsONEHOPNeverTransitive`)
- `..._DIRECT_blocker_is_TERMINAL_is_UNBLOCKED` (kills W-3, over-block) ·
  `..._DIRECT_blocker_is_OPEN_is_BLOCKED` (kills W-3b, under-block) ·
  `test_the_partition_AGREES_with_the_CLAIM_over_a_DEEP_BRANCHING_dag` (4 levels + diamond).
  *Wrong build that would still pass:* one graded only on a 1-hop or 2-node fixture — the
  packet's stated floor and the reason for the depth.
  ⚠ The agreement sweep covers **open, unowned** tasks only, and the guard asserting that is
  load-bearing: "unblocked" ≠ "claimable" (the CAS also guards status/owner/superseded). My
  first draft swept a `done` root and reported a divergence **that was not one**. Non-open
  nodes stay in the DAG as structure with their own partition assertions.

**Property 3 + hazards named by the mandated store-reference read**
- `TestTheServedTaskIsFieldIDENTICALToGetTask` (kills W-4) — oracle is `get_task`, a
  single-record read #253 verdicted a non-defect, so equality against it is a ∀ over the model's
  fields rather than a hand-list. `test_the_FIXTURE_itself_populates_every_optional_column`
  derives the optional set from `Task.model_fields` and fails if any is at its default
  everywhere — the answer to "what wrong build would still pass this?" made mechanical.
- `TestAFilterVALUEIsNeverInterpolatedIntoQueryText` (kills W-5) — discriminating pair: a
  hostile value that IS an owner must match exactly its task; one that is nobody's must match
  nothing against a demonstrably non-empty ledger.
- `TestTheFiltersAreANDedNotORed` (kills W-6) — re-derived over the whole test tree: nothing
  anywhere supplies `status` **and** `owner` together.

## 4. INSTRUMENT — what I found, and what I reused

The brief asked me to look before hand-rolling. Found (by **grep** — an exhaustiveness question
over a non-symbol seam, so grep is the honest instrument under the dogfood protocol, and I am
saying so):

- `test_brief_ledger.py::TestCoverageQueryCountIsBounded::_coverage_query_count`
- `test_brief_ledger.py::TestFleetQueryCountIsBounded::_query_count`

Both count **queries**, not rows. **They are structurally blind to #253**: the defect is ONE
query that reads the whole table, so the query count is 1 before and after the fix. Verdict
`keep_with_trigger` — they remain right for their own N+1 question; the trigger for revisiting
is any future need to bound *volume* rather than *round trips*.

SECTION I already cloned their capture-then-wrap idiom into a rows-read instrument,
`test_blocks_edge::_rows_read`. **I wrote no instrument: I imported that one**, along with
`_seed_unrelated_tasks`, `_seed_legacy_task`, `_drive_to`, the `task_ledger` fixture and the
ledger vocabulary. Copy #2 of a measurement instrument is the #102 shape.

## 5. ESCALATIONS

**E-A — BLOCKER, and it is not mine to fix.**
`test_blocks_edge.py::TestTheReadIsBOUNDEDByTheCallersFilter::test_rows_read_does_NOT_grow_with_the_size_of_the_LEDGER[owner-filter]`
**is unsatisfiable.** Its `_measure(by_owner=True)` creates `blocker` (open), creates `target`
blocked_by=[blocker], then `assert claim.claimed` — the CAS refuses, because the blocker is
open and non-terminal. It dies in fixture setup *before `query_tasks` is called*, so no
implementation can make it pass. **Measured RED on all seven builds including BASE-correct**;
observed failure `AssertionError: assert False / ClaimResult(claimed=False, ...)`.
This is the **C-DEF class** the repo's law names ("a contract ships with a satisfiability
receipt"): it would trap the 04b-1 builder between a red test it may not edit and a fix that
cannot make it green. **Exact edit** (one line, in `_measure`, before the claim), mirroring
what my own `_measure` does:
```python
            await _drive_to(ledger, blocker, STATUS_DONE)   # ADD: the CAS cannot claim a
            if by_owner:                                    #      task whose blocker is open
                claim = await ledger.claim_task(target, ACTOR)
```
Not applied — `test_blocks_edge.py` is do-not-touch.

**E-B — the merge decision is the lead's.** Two files now cover #253. Mine re-pins nothing and
imports rather than clones, so shipping both is coherent; folding this file's classes into
SECTION I is equally coherent. **What must NOT happen is choosing one and discarding the
other**: SECTION I owns the four semantics pins this file does not restate, and this file owns
the six holes measured above. I recommend shipping both and citing this report from SECTION I's
header.

**E-C — `_rows_read`'s home.** A test module importing a sibling test module works (pytest and
mypy both resolve it; `test_task_ledger.py` 234 passed alongside) but is the wrong long-term
address. Proposed edit, outside my writable set: move `_rows_read` to `_surreal_harness.py`
beside `run`, exactly as `_enforced_relations_scaffold` houses the migration idiom, and have
both files import it there. One import line changes in each.

**E-D — the tool-level `limit`.** `server.py`'s dispatcher (`AppContext`, ~`:3520`) slices
AFTER materialisation, so a fully bounded `query_tasks` still hands the whole answer up before
the cap applies. Outside 04b-1's writable set. SECTION I flags it; I flag it again rather than
folding it in. **Fix now vs defer — the operator's call.**

**E-E — result ORDER, and store reference §7.** `query_tasks` promises no order (`_task_fakes`
deliberately reorders to keep consumers honest), so I did **not** invent an ordering pin. But
§7's *ORDER BY under an explicit projection* hazard becomes live the moment a builder adds an
`ORDER BY` to the new `WHERE`. Two readings: (i) no order is contracted, so nothing to pin —
what I did; (ii) the absence of a contract is itself worth pinning, so that a builder adding
`ORDER BY` must declare it. I recommend (i) and flag it for the builder's brief.

**E-F — concurrency.** Any bounded rewrite becomes a **two-read** operation (candidates, then
blockers). A writer committing between them can make the partition disagree with the CAS
without either read being wrong. Today's single full read has no such window. A contract pin is
the wrong instrument (≥8-way × 20 consecutive green runs); this belongs in the builder's brief
and the cold audit, and it is a genuinely NEW hazard this fix introduces.

**E-G — a reading fork in my own brief.** "Do NOT implement, stub, or 'helpfully' fix
`query_tasks`" admits two readings: (i) never write such code anywhere; (ii) never ship it in
the repo tree. I took (ii) — wrong builds exist only in `/tmp/wb253`, the repo tree contains
exactly one new untracked test file (`git status` verified), and without them §2's findings
would have been opinions. Under reading (i) my grading of SECTION I would have been impossible.
Flagged rather than silently chosen.

**E-H — SECTION I's own regression pins.** Measured: all 11 survive W-1, the naive rewrite.
That is not a defect I can fix from here (they are correct pins with under-discriminating
fixtures), and my addendum closes the gap behaviourally. But if the lead prefers the fix at
source, the edit is one parametrisation: run the two out-of-filter pins over a
`(non-terminal, terminal)` blocker axis instead of a single non-terminal blocker.

## 6. RESIDUALS — one line, one verdict each

| # | item | verdict |
|---|---|---|
| R-1 | `test_blocks_edge` `[owner-filter]` leg unsatisfiable | **BLOCKER — fix before the builder starts** (E-A) |
| R-2 | Two contracts cover #253 | **lead ruling needed** (E-B); both are coherent, discard neither |
| R-3 | `_rows_read` lives in a test module | **accepted for now**, promotion proposed (E-C) |
| R-4 | `server.py` tool-level `limit` slices post-materialisation | **operator ruling** — fix now or defer (E-D) |
| R-5 | No ordering contract on `query_tasks` | **deliberately not pinned**; builder-brief risk (E-E) |
| R-6 | Two-read TOCTOU introduced by any bounded rewrite | **not contract-pinnable**; route to builder brief + cold audit (E-F) |
| R-7 | Wrong builds written in scratch | **disclosed deviation** (E-G); repo tree clean, verified |
| R-8 | SECTION I's 11 regression pins all survive W-1 | **reported, closed behaviourally here**; source fix optional (E-H) |
| R-9 | `TestTheDuplicateBlockerDivergence` RED on every build incl. BASE | **pre-existing, its author's E-6** — I confirm it independently; NOT caused by #253 and not fixed by it |
| R-10 | `agent-"quoted"` survives W-5 | **not a gap** — a double quote cannot break a single-quoted literal; the other three shapes carry that pin |
| R-11 | My W-3/W-3b closures are plausible, not exhaustive | **honest bound** — other transitive shapes exist; the pins assert the ONE-HOP property, not these two builds |
| R-12 | `test_the_FIXTURE_itself_populates_every_optional_column` also reddens under W-4 | **intended** — it detects a fixture that cannot discriminate, and a narrowed projection makes it so; not a false positive |
| R-13 | Harness lives at a `/tmp` path | **not citable** by repo law; §2.3 describes it reproducibly instead |
| R-14 | `mid_wontfix` / `root_done` excluded from the agreement sweep | **deliberate** — "unblocked" ≠ "claimable"; both keep their own partition assertions |
| R-15 | Scratch copy `/tmp/wb253` still on disk | **lead's call** — delete it or keep it for the builder's own mutation proofs |

## 7. Gate tails

```
./scripts/typecheck.sh    → typecheck: {lorerunes,lorescribe,loresigil,loremaster,skills} OK   EXIT=0
uv run ruff check .       → All checks passed!                                                 EXIT=0  (unpiped)
pytest -n auto loremaster/tests/test_query_tasks_bounded.py  → 2 failed, 21 passed in 4.79s
pytest -n auto loremaster/tests/test_task_ledger.py          → 234 passed in 6.31s
BASE-correct build, scratch → ADDENDUM: 23 passed in 4.62s      (satisfiability)
scratch provenance          → loremaster → /tmp/wb253/loremaster/loremaster/__init__.py
scratch restore             → "scratch tasks.py restored byte-exact" (asserted in-harness)
```

**Declared-RED node ids** (from `--collect-only`, fixed before any run; diffed both ways, no
unexpected reds and no declared-green):

```
loremaster/tests/test_query_tasks_bounded.py::TestTheBLOCKEDPathIsBoundedToo::test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked[status-filter]
loremaster/tests/test_query_tasks_bounded.py::TestTheBLOCKEDPathIsBoundedToo::test_rows_read_does_NOT_grow_when_BLOCKED_is_also_asked[owner-filter]
```
