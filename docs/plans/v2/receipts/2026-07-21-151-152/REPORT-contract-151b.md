# REPORT-contract-151b

brief-base v5 read

state: **done-with-deviations — MP1–MP6 all closed; the blocker build is dead**

deviations:
- **SCOPE INCIDENT, self-caught and reverted:** my `uv run ruff check . --fix` ran repo-wide and modified **4 tracked files under `docs/plans/v2/receipts/2026-07-20-probes/`** — outside my writable set. Backed up, diffed, reverted; `git status -- docs/` is now empty. Detail §8.1.
- Fixed the adversary's residual #1 (an un-derived count claim) in `test_retry_seam.py` — prose only, no assertion touched. §8.2.
- Built a reference fix in `/tmp/contract151b-ref` (provenance asserted) for the satisfiability receipt and 8 mutation proofs. No production file in the repo was modified; no git state touched.

decisions-needed:
- **F4 — MP3's label-vocabulary table constrains the builder's label naming.** Two readings written out; I picked the stricter and said why. §7.1.
- **HEAD moved during my run** (`d2d7b2c` → `ee0bec2`, 3 commits). Verified: neither of my two files was touched; diff base intact; all gates re-measured at the new HEAD. §8.6.
- F3 (ruff dirty at HEAD) was real mid-run and was **fixed under me** by `81f79d2`; recorded because it caused my §8.1 incident. §8.3.
- Adversary residuals #2 (`scout.py:171`) and #3 (`_surreal_harness.py` writable) are COVERED by R4/R5 and pinned. §6.

receipt pointers: RED §1 · MP coverage table §2 · MP1 mutation proof §3 · provenance §4 · satisfiability §5 · all mutations §3 · forks §7 · residuals §8

---

## 1. RED receipts (the UNFIXED tree)

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster
$ uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
34 failed, 481 passed, 1 warning in 19.94s
```

Inherited baseline `17 failed, 472 passed` → **+17 new RED, +9 new green-by-design, 26 new tests.**
The inherited 17 are untouched: not one was weakened, rewritten, or simplified.

| n | new pin | MP | file |
|---|---|---|---|
| 10 | `test_each_production_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion[×10 seams]` | MP1 | test_retry_seam.py |
| 1 | `test_scouts_command_connection_logs_ITS_OWN_url_on_bootstrap_exhaustion` | MP1 | test_retry_seam.py |
| 1 | `test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls` | MP1 | test_retry_seam.py |
| 1 | `test_every_bootstrap_session_call_passes_a_url` | MP2 | test_retry_seam.py |
| 3 | `test_each_bootstrap_label_NAMES_its_own_statement[×3]` | MP3 | test_surreal_harness.py |
| 1 | `test_scouts_query_exhaustion_carries_a_label_OF_ITS_OWN` | R4 | test_retry_seam.py |

**Every one checked against its FAILURE REASON, not merely its redness** (the C-DEF class). No
`TypeError`, no collection error, no arity accident. Verbatim samples:

```
E  AssertionError: AgentRegistry and BriefLedger were connecting to two DIFFERENT servers
   and both exhaustion records name None.
E  assert None != None

E  AssertionError: the statement this fixture drove to exhaustion logged label='', which
   does not name what it is: it carries none of ['database', 'select', 'use'].

E  AssertionError: these calls to the shared session bootstrap pass no `url=`:
E  assert not [('agents.py', 413, '_ensure_connection'), ('briefs.py', 442, …), …]

E  AssertionError: scout's query seam exhausted and logged label=None.
```

### Nine new pins that are GREEN by design — stated, never counted as receipts

Repo law: a pin red for the wrong reason is a defect, and so is a green one silently
counted as proof. These prove themselves by MUTATION (§3), not by today's redness.

| pin | why green today | proof |
|---|---|---|
| `test_the_scan_does_NOT_see_an_ALIASED_call_a_KNOWN_BOUND` (MP5) | it ASSERTS the hole exists | mutation E |
| `test_scouts_query_exhaustion_carries_NO_url_a_KNOWN_BOUND` (R4) | ⚠ **green for the WRONG reason today** — no url because no label either | mutation G |
| `test_the_TWO_gates_SHARE_one_scanner` | the scanners are already shared | mutation H |
| `test_every_owner_the_scan_finds_is_DRIVEN_here` | coverage is complete today | mutation E |
| `test_the_two_independent_owner_counts_AGREE` · `…scan_is_not_silently_finding_nothing` · `…exemption_is_EVIDENCE_BACKED_and_REAL` · `…scan_SEES_a_url_less_call` · `…scan_SPARES_a_url_carrying_call` | reach + evidence + ± controls | controls are their own proof |

MP6's `attempts` assertion is likewise **green today** (it is a non-regression pin restoring
an orphaned virtue, not a defect pin) — mutation F.

### Gates

- `uv run ruff check loremaster/tests/test_retry_seam.py loremaster/tests/test_surreal_harness.py` → **All checks passed!** (exit 0)
- `./scripts/typecheck.sh` → **Found 55 errors in 5 files** — baseline exactly, **zero** in either file I touched (grepped: `NONE`).

---

## 2. MP1–MP6 coverage

| MP | closed by | wrong build it kills | proof |
|---|---|---|---|
| **MP1 (BLOCKER)** | `TestEveryProductionOwnerThreadsITSOWNUrl` — **all 11 owners at 11 DIFFERENT urls**, + a two-owner observed-vs-observed pin, + a coverage-as-a-checked-variable pin | all 11 owners hardcode one url (was 489/0, zero delta over 6079) | **mutation A: 12 failed** §3 |
| **MP2** | `TestEveryBootstrapCallThreadsItsOwnUrl` — deny-by-default AST gate on `bootstrap_session`, EMPTY evidence-backed allowlist, reach floor 11, ± controls | any owner omits `url=` | mutation B |
| **MP3** | `test_each_bootstrap_label_NAMES_its_own_statement` — expectation derived from the **statement's SurrealQL vocabulary**, never from the constant | labels rotated: present, distinct, each naming its neighbour (was 489/0) | **mutation C: 2 failed, and ONLY MP3's params** |
| **MP4** | allowlist reshaped to `(evidence, COUNT)` — the exemption is a BUDGET, not a blanket; + an "overdrawn exemption" leg | unlabelled call added inside an exempt body (was 489/0) | mutation D3 |
| **MP5** | `test_the_scan_does_NOT_see_an_ALIASED_call_a_KNOWN_BOUND` — bound pinned, positive control first, named re-open trigger | silent inheritance / silent closure of the alias hole | mutation E |
| **MP6** | `attempts == _seam_attempt_ceiling()` restored into the new class, adjudicated **preserved-with-pin** against #151 R1 (not "the old code did it") | record's attempt count diverging from the exception's | mutation F |
| **R4 (bonus, brief-required)** | `TestScoutsQuerySeamIsAttributedByLabelOnly` — label pinned RED, url-gap pinned as a KNOWN BOUND with a re-open trigger | scout's seam left unattributed, or the bound closed silently | mutation G |

**MP1 and MP2 are NOT redundant, and the mutations prove it.** Mutation A (all owners
hardcode) **passes** the MP2 AST gate — the callers do pass `url=`, just a literal — and is
killed only by MP1's behavioural pins. Mutation B (one owner omits `url=`) is caught by the
AST gate and names the site by `file:line`. Structural proves every caller DOES; behavioural
proves each one passes **its own**.

---

## 3. Mutation proofs (reference build, restore-verified before each)

Harness: restore from tar → purge `__pycache__` → mutate in place → run the contract.
**Restore control: `515 passed`** (re-run after the sweep).

| # | wrong build | result | verdict |
|---|---|---|---|
| **A** | **all 11 production owners hardcode `url="ws://127.0.0.1:8000/rpc"`** | **12 failed, 503 passed** | **THE BLOCKER IS DEAD.** All ten seams + scout + the two-owner pin |
| B | `SurrealStore` drops `url=` at the bootstrap call | 16 failed | MP2's gate fires and names the site |
| C | NS/DB label VALUES rotated | **2 failed — MP3's two params, nothing else** | MP3 is the *only* thing that sees it |
| D3 | unlabelled `retry_on_conflict` inside the exempt `execute_transaction` | **1 failed** — the label gate | MP4 closed |
| E | scanner reach widened to see an aliased call | 4 failed, incl. the KNOWN-BOUND pin | MP5: the bound cannot close silently |
| F | record's `attempts` disagrees with the exception's | 14 failed, incl. all 3 MP6 params | MP6 discriminates |
| G | scout's query seam threads a url | **1 failed — the R4 KNOWN-BOUND pin only** | R4 bound cannot close silently |
| H | `_bootstrap_call_sites_in` hand-rolled instead of calling the shared scanner | **1 failed — the DRY pin only** | **sharing proven BY MUTATION**, not by inspection |

### Mutation A, in full — the blocker the previous contract could not see

```
MUTATION A applied: 11 owners hardcode the url
FAILED …TestEveryProductionOwnerThreadsITSOWNUrl::test_each_production_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion[AgentRegistry]
FAILED …[BriefLedger]  …[DiffEngine]  …[FindingLedger]  …[SurrealCodeGraph]
FAILED …[SnapshotStamper]  …[SurrealManifest]  …[LocalMemoryBackend]
FAILED …[SurrealStore]  …[TaskLedger]
FAILED …test_scouts_command_connection_logs_ITS_OWN_url_on_bootstrap_exhaustion
FAILED …test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls
12 failed, 503 passed, 1 warning in 26.98s
```

This is the build the adversary measured at **489 passed / 0 failed with a ZERO failure delta
across all 6079 tests in the repository.**

---

## 4. Provenance receipt (#140 — prove which tree you are testing)

Scratch copy via the blessed tool, never `cp -a`:

```
$ ./scripts/scratch_copy.sh /tmp/contract151b-ref
scratch copy READY: /tmp/contract151b-ref
  loremaster  -> /tmp/contract151b-ref/loremaster/loremaster/__init__.py

$ cd /tmp/contract151b-ref && uv run python -c "import loremaster; print(loremaster.__file__)"
PROVENANCE loremaster.__file__ = /tmp/contract151b-ref/loremaster/loremaster/__init__.py
```

Heeding the adversary's own §0 control failure — *asserting `loremaster.__file__` is necessary
and NOT sufficient, because the TEST TREE has its own provenance* — I never made a
copy-of-a-copy. The mutation harness restores from a tar of the provenance-asserted tree and
mutates it **in place**, and every mutation is bracketed by a restore leg that reproduces
`515 passed`. A poisoned harness cannot produce that alternation.

---

## 5. Satisfiability receipt — 515 passed / 0 failed

Reference fix built independently in the scratch tree: three label constants + `*, url: str`
on `bootstrap_session` threaded into all three driver calls, all 11 production owners passing
`url=`, `_surreal_harness.py:339` passing `url=env.url` (R5), and `scout.py:171` labelled
(R4, `url=None`).

```
$ cd /tmp/contract151b-ref/loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
515 passed, 1 warning in 25.72s
```

**The harder leg** (a contract that traps the builder between the lint and a test it may not
edit is a C-DEF defect):

- `uv run ruff check loremaster/` on the fixed build → **All checks passed!**
- `./scripts/typecheck.sh` on the fixed build → **Found 55 errors in 5 files** — baseline
  unchanged; zero in `store/_txn.py`, `scout.py`, or either test file.

**No orphaned-import cleanup is demanded by this contract** — the reference fix adds
arguments and constants, removes nothing, so the lint has nothing to demand that a pin
forbids.

---

## 6. Owner enumeration — derived, not inherited

The brief warned its own hand-list may under-match. Swept bare:

```
$ git grep -n "bootstrap_session" -- .
```

**11 production call sites**, all confirmed against the AST scan and all *driven* by MP1:
`agents.py:413` · `briefs.py:442` · `diff.py:544` · `findings.py:453` · `graph_surreal.py:416`
· `index/snapshots.py:275` · `index/surreal_manifest.py:201` · `memory/local.py:364` ·
`scout.py:223` · `store/surreal.py:454` · `tasks.py:466` — plus the 12th, test-tree
`tests/_surreal_harness.py:339` (R5, the builder's).

Two independent enumerations agree and are pinned to agree
(`test_the_two_independent_owner_counts_AGREE`): the `_ensure_connection` side
(`_MIN_KNOWN_BOOTSTRAP_OWNERS = 11`) and the call-site side
(`_MIN_KNOWN_BOOTSTRAP_CALL_SITES = 11`).

**Scout is the tenth-plus-one and is driven by its own pin**, because it is a module-level
function rather than a class with `_ensure_connection` — the exact reason it was the eleventh
invisible hand-rolled copy (#120). A pin parametrized over `_QUERY_SEAMS` alone would have
left it precisely as unpinned as before, which is why
`test_every_owner_the_scan_finds_is_DRIVEN_here` compares the DRIVEN set to the SCANNED set
rather than trusting either list.

---

## 7. Forks — surfaced, not silently settled

### 7.1 F4 — MP3's vocabulary table constrains the builder's label naming

MP3 must derive its expectation independently of the constant under test, which means
asserting something about the label's *content*. Two readings:

- **Reading A (MY PICK, shipped).** Require each label to carry its statement's own SurrealQL
  vocabulary and to *exclude* the vocabulary distinguishing the other two
  (`namespace`/not-`database`; `database|select|use`/not-`namespace`,not-`define`;
  `database`/not-`namespace`). Case-insensitive substrings, any-of alternatives. Exactly one
  assignment of three values satisfies all three rows, so **every permutation fails** —
  including the NS↔DB swap that passed the previous contract 489/0. Cost: it tells the
  builder its labels must NAME their statements. That *is* the property #151 asks for
  ("an operator must land on WHICH of the three died"), so I judge the constraint legitimate
  rather than incidental.
- **Reading B.** Assert only that the three labels are pairwise distinct *and* that permuting
  them changes the outcome — i.e. drive all three and require a specific stable ORDER.
  Constrains no vocabulary, but pins nothing an operator can read: three labels named `a`,
  `b`, `c` would pass, and #151's complaint is precisely that a label must be greppable.

I deliberately made the middle row admit **three** alternatives (`database`/`select`/`use`)
because the SDK call is `use()` and the operation is "select the database": a contract
dictating one spelling would be a C-DEF trap for a builder doing the right thing.

### 7.2 A knowing, disclosed duplication

`_exhaustion_record` (test_retry_seam.py) and `_the_one_exhaustion_record`
(test_surreal_harness.py) are the same four lines in two files. They are **trivia, not
policy** — "take the one record or fail loudly", with no retry budget, classification, or
threshold to drift. The two files do not import each other (the tree's idiom is that helper
sharing goes through `_surreal_harness.py`, a production-adjacent module I may not touch).
Raising it rather than pretending: if the lead wants it shared, the seam is
`_surreal_harness.py` and that is the builder's file.

---

## 8. Residuals — individually, with verdicts

### 8.1 ⚠ MY OWN SCOPE INCIDENT, self-caught

`uv run ruff check . --fix` — run to clean my own two files — modified **4 tracked files**
outside my writable set:
`102-recovery/probe_conflict_kind.py`, `102-recovery/probe_sequence.py`, `probe_budget.py`,
`probe_long_query_69.py` (5 insertions / 7 deletions: an `else:`→`elif` collapse, two unused
imports, one import reorder).

Handling, in order: `cp -a` the whole directory to `/tmp/ruff-collateral-151b/` **first**
(repo law — an agent mutating an uncommitted tree backs up content before restoring), read
the full diff, confirm the files were unmodified at session start (my brief's own opening
`git status` shows them clean, so mine were the only edits and no other agent's work could be
lost), then `git checkout -- docs/plans/v2/receipts/2026-07-20-probes/`.
`git status --short -- docs/` is now **empty**. **Lesson for the next brief: `ruff check .`
is a repo-wide command and `--fix` makes it a repo-wide WRITE.** Scoped invocations only.

### 8.2 Adversary residual #1 — un-derived count claim — FIXED

`test_retry_seam.py:6779` (comment) and `:6841` (failure message) both read *"the **eleven**
possible emitters (ten `_query` seams, scout, the bootstrap)"* — a parenthesis enumerating
**twelve**, and conflating the two populations CLAUDE.md's own §ONE IMPLEMENTATION section
warns are different counts. The adversary graded it *"real, fix in this wave"*; the file is
in my writable set and repo law forbids kicking the can. **Fix: dropped the un-derived
number, kept the enumeration** (`"the possible emitters (the ten `_query` seams, scout's query
seam, the session bootstrap)"`). Prose only — no assertion touched, suite unchanged at
`34 failed, 481 passed` before and after. Revert is one line if the lead disagrees.

### 8.3 F3 — ruff was dirty mid-run, and was FIXED UNDER ME by another agent

Mid-run, `uv run ruff check .` returned **`Found 9 errors.`** — all in
`docs/plans/v2/receipts/2026-07-20-probes/` (`probe_cosine_projection_s4b.py`: `PLR0915`,
`F841`, import ordering, and siblings), tracked files shipped by commit `1666856`
*"docs(receipts): #152 archive the #102 design record and the surviving probe instruments"*.
Outside my writable set, so I flagged rather than acted.

**By the end of my run it was resolved by someone else**: `81f79d2 build(ruff): exclude the
archived receipts tree from lint`. Final state, re-measured at the new HEAD:
`uv run ruff check .` → **All checks passed!**

**Recorded anyway, because the sequence is the finding:** a wave shipped a ruff-dirty commit,
and for a window every agent in this repo inherited a false "ruff is clean" baseline. I hit
that window, and my §8.1 scope incident is its direct consequence — I ran `--fix` because
ruff was failing on files I had not touched.

### 8.6 ⚠ HEAD MOVED DURING MY RUN — my diff base verified intact

The brief pinned the contract at `d2d7b2c`. By the time I finished, HEAD was `ee0bec2`, three
commits ahead (`1666856` → `81f79d2` → `ee0bec2`), including `ee0bec2 docs(test): #152
adjudicate the test tree's dangling citations — 25 edits, prose only`, which committed the 13
concurrent-agent test-file modifications flagged as adversary residual #10.

**Verified, not assumed:**
- `git merge-base --is-ancestor d2d7b2c HEAD` → **true**; the contract commit is still in the
  ancestry.
- `git log -- <my two files>` → their most recent commit is still **`d2d7b2c`**. None of the
  three new commits touched either file I am editing, so my diff base is intact and my
  receipts are not stale.
- Full re-verification at the new HEAD: contract **`34 failed, 481 passed`** (unchanged),
  typecheck **`Found 55 errors in 5 files`** (baseline), ruff **`All checks passed!`**.

Residual #10 is therefore now **CLOSED** — that work is committed and no longer lives only in
the working tree.

### 8.4 Adversary residuals, re-checked

| # | item | status |
|---|---|---|
| 2 | `scout.py:171` (F1) | **COVERED by R4.** Label pinned RED; the url gap pinned as a KNOWN BOUND with a named re-open trigger (mutation G) |
| 3 | `_surreal_harness.py` writable (F2) | **CONFIRMED still blocking.** My reference build required exactly `url=env.url` at `:339`; R5 grants it |
| 4 | `_seam_attempt_ceiling()` orphan risk | **NOT an orphan** — MP6 now uses it again in the new class |
| 5 | the R3 gate never checked `url=` | **CLOSED by MP2** |
| 6 | `_ATTRIBUTED_BY_ANOTHER_MECHANISM` evidence quality | evidence still holds; now **mechanically floored** (`_MIN_EVIDENCE_CHARACTERS`) so `""`/`"TODO"` cannot punch a hole |
| 7 | composition pin's clock dependency | untouched, still 20/20 stable in every run above |
| 8 | scratch builds in `/tmp` | mine is `/tmp/contract151b-ref` (+ tar `/tmp/ref151b.tgz`, harness `/tmp/mut151b.sh`, backup `/tmp/ruff-collateral-151b`). All outside the repo; delete at will |
| 10 | **concurrent agent editing `loremaster/tests/`** | **CLOSED during my run.** 13 files were uncommitted when I started (and `REPORT-apply-152-tests.md` appeared mid-run); commit `ee0bec2` landed them. I touched none of them, and none touched my two files (§8.6) |

### 8.5 New observation

`REPORT-*.md` at the repo root now numbers **ten** untracked files including this one. Repo
law requires deletion before any image build. Flagging, not acting.

---

## 9. What I changed

| file | change |
|---|---|
| `loremaster/tests/test_retry_seam.py` | `_call_sites_in` extracted as the ONE shared scanner (both gates call it; sharing proven by mutation H). `_ATTRIBUTED_BY_ANOTHER_MECHANISM` reshaped to `(evidence, count)` + an overdrawn-exemption leg (MP4). Added the aliased-call KNOWN BOUND (MP5). New §10b `TestEveryBootstrapCallThreadsItsOwnUrl` (MP2, 6 pins). New §10c `TestEveryProductionOwnerThreadsITSOWNUrl` (MP1, 13 pins). New §10d `TestScoutsQuerySeamIsAttributedByLabelOnly` (R4, 2 pins). Un-derived count claim fixed at `:6779`/`:6841`. |
| `loremaster/tests/test_surreal_harness.py` | `_BOOTSTRAP_LABEL_NAMING` table + `test_each_bootstrap_label_NAMES_its_own_statement` ×3 (MP3). MP6's `attempts` assertion restored into `TestTheBootstrapPathsExhaustionIsAttributable`, adjudicated preserved-with-pin against #151 R1. |

No production file in the repo was modified. No git state was staged, committed, or reverted
**except** the scope-incident restore in §8.1, which is disclosed as a deviation.
