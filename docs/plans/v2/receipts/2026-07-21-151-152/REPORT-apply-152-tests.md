# REPORT-apply-152-tests

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - Executed 2 sites the tests-adjudicator marked LOAD-BEARING as **PROVENANCE instead**
    (`test_comms_schema.py:1811`/`:2269`) — the comms-adjudicator read the full prose and
    graded them P; I verified and agree. Reconciliation in §3.
  - Added ONE non-site line (the `test_message_ledger.py` W-anchor) recommended by BOTH
    adjudicators. It is an addition, not a repoint; trivially revertible. §2 row 25.
  - Found and executed **one Ruling-2 instance neither adjudicator listed**
    (`test_task_ledger.py:1542`, "RED by construction" — PKT-06 shipped it at `f80e95a`).
  - 6 LOAD-BEARING sites are **outside my writable set** — flagged with exact edits, §5.
- **decisions-needed:**
  1. **`test_surreal_harness.py:54` IS NOW FALSE** — it asserts the #150 reports "are
     UNTRACKED"; commit `7d2ff44` tracked them. Out of my set. §5.1. **Highest-value flag.**
  2. **TIME-LIMITED:** `scratchpad/probe_budget.py` and 5 sibling probes are **still on disk,
     untracked**. Archiving them resolves measured claims I was otherwise required to strike.
     The window closes at the next cleanup. §6.1.
  3. Two known bounds still have **no ledger row** (`test_render_seam_pins.py:430`,
     `test_impact.py:812`), which repo law requires. §6.2.
- **receipt pointers:** §1 rulings applied · §2 the 25-row ledger · §3 reconciliations ·
  §4 gate tails WITH COUNTS · §5 out-of-set flags · §6 escalations · §7 declined sites

**25 edits across 13 files · 148 insertions / 72 deletions · ZERO test logic touched
(AST-proven, §4.3).**

⚠ **Reading the diff:** `git diff --stat` shows **14** files. The 14th is
`loremaster/tests/test_retry_seam.py` (+446 lines) — that is the **concurrent #151 agent's
work, not mine**. My wave is exactly the 13 files listed in §2, and `test_retry_seam.py`
was on my do-not-touch list. Nothing is staged (`git status --porcelain` staged count: 0).

---

## 1. What I executed, by ruling

| ruling | sites | note |
|---|---|---|
| **R1** — load-bearing repoint | 5 | every target VERIFIED to carry the claim before pointing at it (§3.1) |
| **R2** — stale RED → past tense | 4 | every one preceded by a GREEN receipt (§4.1) |
| **R3** — strike unreproducible numbers | 8 | 2 KEPT under the protocol-inline exception (§3.2) |
| **R4** — evidence-lost annotation | 7 | no durable address existed; claim kept, pointer marked unverified |
| addition | 1 | W-anchor, recommended by both adjudicators |

**I did not touch a single PROVENANCE site.** ~87% of the adjudicated population is
PROVENANCE and stays byte-identical, per Ruling 1's explicit ban on churn.

---

## 2. The per-site ledger

### Ruling 1 — LOAD-BEARING repoints (5)

| # | file:line | before → after |
|---|---|---|
| 1 | `test_brief_ledger.py:7` | `recorded in ``REPORT-c1-contract-ledgers.md``` → `recorded AT THEIR USE SITES, beside the pin each one governs` + the **verified** map (decision #4 → `test_comms_tool.py::test_unknown_agent_error_is_enriched_with_a_capped_non_retired_roster`; #5/#6 → `test_comms_wiring.py::TestSchemaIsActuallyAppliedNotJustConstructed`; d1d2-b → `TestUnknownBriefErrorCappedKnownNames`) |
| 2 | `test_comms_schema.py:57` | `see ``REPORT-probe-7061-c1.md`` at the repo root` → `see ``docs/reference/surrealdb-31-capabilities.md`` §4 (UNIQUE-on-relation is legal and the #7061 cascade hazard is settled ABSENT, with the probe transcript)` |
| 3 | `test_comms_promise_registry.py:2231` | `the instrument shape proposed in REPORT-pkt02a-finalwave.md §F, ledgered as its own item` → `the instrument shape ledgered as finding #143` |
| 4 | `test_task_ledger.py:1424` | `scratchpad/contract-v5/capture_engine.py` → `the capture script was a scratch file and is gone, but the same wording is transcribed from a live probe in docs/reference/surrealdb-31-capabilities.md §6.1` |
| 5 | `test_graph_surreal.py:1990` | `see REPORT-slate-builder-s1.md's #60 resolution note` → `see finding #60, since RESOLVED: the wire exposure landed as ``server.py::DeadCodeSweepResult{nodes, elided}``` |

**Row 1 note — I corrected my own error mid-flight.** I first wrote the class name as
`TestUnknownBriefErrorGrammar`; the real class at that line is
`TestUnknownBriefErrorCappedKnownNames`. Caught by grepping the name I had just written,
which is exactly the "verify the target carries the claim" step this ruling demands.
Had I not checked, I would have shipped a *new* dangling citation while fixing one.

### Ruling 2 — stale RED prose → past tense (4)

Each names the commit that closed it. The historical claim is PRESERVED, never deleted.

| # | file:line | before → after |
|---|---|---|
| 6 | `test_comms_render_architecture.py:17` | `RED EXPECTATION (this whole module is the RED half of a TDD cycle — the builder makes it green)` → `RED EXPECTATION AS AUTHORED — HISTORICAL, NOT CURRENT … packet 02 (17277d1) shipped the fix and these pins are GREEN today. What each pin caught, preserved because it records what the pin is FOR:` — plus the three bullets' verbs tensed (`does not accept`→`did not accept`, `are RED … today`→`were RED … before 17277d1`, `which has no such symbol`→`which had no such symbol`, `it is RED`→`it was RED`) |
| 7 | `test_comms_render_architecture.py:499` | `RED against clean production: … has no ``subscribed_skew`` parameter yet` → `RED before 17277d1: … had no ``subscribed_skew`` parameter` (+ `a clean tree — which has no`→`the pre-fix tree — which had no`) |
| 8 | `test_brief_ledger.py:1481` | `Against CLEAN production they are RED for the right reason — ``BriefLedger`` has no ``subscribed_name_skew`` yet` → `Before 17277d1 they were RED against the real store for the right reason — … had no ``subscribed_name_skew``; packet 02 shipped it at ``briefs.py::subscribed_name_skew`` and they are GREEN on both tiers today` |
| 9 | `test_task_ledger.py:1542` | **found by my own sweep, not listed in any adjudication.** ```TaskLedger.create_many`` / ``.updated_since`` / … do not exist on the REAL ledger yet — this is RED by construction` → `RED AS AUTHORED — HISTORICAL, NOT CURRENT. … did not exist … when these pins were written … PKT-06 (f80e95a) shipped all three and it is GREEN today` |

### Ruling 3 — measured numbers whose instrument is gone (8 struck, 2 kept)

| # | file:line | number | verdict |
|---|---|---|---|
| 10 | `test_task_ledger.py:1235` | `reproduced live 30/30` | **STRUCK** → `reproduced live and repeatably at authoring time; the reproduction COUNT is struck — it measured a build that no longer exists`. Qualitative claim kept; the pin below proves it. |
| 11 | `test_task_ledger.py:1308` | `reproduced live 40/40` | **STRUCK**, same shape, cross-referencing row 10's class. |
| 12 | `test_brief_ledger.py:1217` | `407 round-trips / 234 ms` | **SPLIT — 407 KEPT, `234 ms` STRUCK.** `_query_count` is in that same file, so the round-trip count is re-derivable in-tree; no in-tree instrument measures wall-clock. |
| 13 | `test_brief_ledger.py:1654` | `6.1× leaf-elapsed at 11× rows` | **STRUCK** → `the audit's leaf-elapsed ratio is struck: its instrument is gone … the PLAN assertion below is what makes the claim checkable`. |
| 14 | `test_comms_render_architecture.py:496` | `617/0` | **STRUCK** → `passed the FULL render contract with zero failures … the pass COUNT it reported is not restated here — the suite has since changed shape`. |
| 15 | `test_agent_registry.py:765` | `(715 passed)` | **STRUCK**; `left the WHOLE SUITE GREEN` kept — that is the load-bearing half. |
| 16 | `test_agent_registry.py:783` | *"see the report for the measured wall time"* | **CLAUSE STRUCK** — a dead pointer to a number that was never even stated. `205 sequential register() calls` kept (re-derivable: it is `_MAX_FLEET_LIMIT + 5`). |
| 17 | `test_mcp_server.py:4975` | `7 of 119 budgets dangled` | **STRUCK** → the count was fixture-shape-specific; `the sweep below is what makes the invariant checkable`. ⚠ its probe is still on disk — §6.1. |

**KEPT under the protocol-inline exception (2):**

- **`_sdk_guard.py:118`, the `6.2%–34.4%` range.** The brief names this exception and this
  is its exemplar: the prose states `16 racers × 10 rounds = 160 virgin first-connects,
  bootstrap UNRETRIED` and all three runs (`55/160 · 43/160 · 10/160`). Reproducible
  WITHOUT the script. **Kept in full.** (Its dead `Receipt:` line is row 23.)
- **`_comms_fakes.py:676`, `407 store round-trips at limit=200`.** rep-rest listed it as
  instrument-gone; I **kept** it, because it is the SAME measurement as row 12, whose
  instrument (`_query_count`) is in-tree. Striking it in one file while keeping it in the
  other would be the inconsistency, and `limit=200` is `_MAX_FLEET_LIMIT`, an in-tree
  constant. Flagged so the operator can overrule.

### Ruling 4 — evidence-lost annotations (7)

No durable address exists for any of these. The claim is KEPT; only the pointer is marked.

| # | file:line | what the annotation says |
|---|---|---|
| 18 | `_sdk_guard.py:130` | `Receipt: NONE THAT CAN BE FOLLOWED` — the probe was never tracked and is gone, so neither the three runs nor `signin`'s 256-connect clean bill can be re-checked. Names that this is a **deny-by-default safe set** where repo law requires evidence-backed exemptions, and points at re-measure-and-archive as the standing fix. |
| 19 | `test_task_ledger.py:1534` | the PKT-06 design doc `is gone from disk entirely, so the verbatim-transcription claim can no longer be re-checked against its source — treat the literals pinned below as the surviving contract`. |
| 20 | `test_agent_registry.py:8` | the open-decision list `is LOST` — and explicitly contrasts `test_brief_ledger.py`, whose decisions ARE restated at use sites, while this file's are not (I verified: `grep "contract decision"` returns only the docstring itself). |
| 21 | `test_agent_registry.py:777` | the mutation receipt `is therefore UNVERIFIED today, and by this docstring's own standard ("a pin that cannot be shown failing is not a pin") it is owed a re-run rather than trusted`. |
| 22 | `test_render.py:7` | **the `/tmp` binding spec.** `THE BINDING SPEC IS UNRECOVERABLE … never in the repo and is gone from disk entirely` — names both sibling modules whose §-refs die with it. |
| 23 | `test_render_seam_pins.py:6` + `:430` | the same `/tmp` note at module level; at `:430`, the accepted known bound gains `the AUTHORITY for accepting this bound is unverified. The mechanism below is self-contained; the ACCEPTANCE is not` + a note that repo law wants it ledgered and it never was. |
| 24 | `test_render_mypy_layer.py:3` | short local marker pointing at `test_render.py`'s note; states `This module's own substance below does not depend on it`. |

### Addition (1)

| # | file:line | what |
|---|---|---|
| 25 | `test_message_ledger.py:21` | Anchor naming `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md` §W1–W11, making all nine `KILLS the adversary's W<n>` docstrings resolvable at one line. **Recommended by both adjudicators**; target verified TRACKED with the table at lines 68–77. Uses the FULL PATH, not the bare basename (hardening rep-comms §E4 flagged). |

---

## 3. Reconciliations — where adjudicators disagreed

### 3.1 `test_comms_schema.py:1811` and `:2269` — I took PROVENANCE, against the tests-adjudicator

adj-152-tests marked both **LB — resolvable** and proposed expanding `(adversary)` into the
tracked archive path. adj-152-rep-comms marked both **PROVENANCE**. I read both sites in
full and **took PROVENANCE**:

- `:1811` — the residual's entire content is inline: *"a NONEXISTENT one is rejected by
  `ENFORCED` before endpoint TYPING is ever consulted — so the test would pass for a
  neighbouring reason."* Following the label adds nothing.
- `:2269` — the wrong-table analysis is inline, **and its durable half
  (`REPORT-audit-edge-preflight.md §Q5`) is already cited four lines down** and is TRACKED.

**Why the disagreement happened, which is worth recording:** the tests-adjudicator graded
these from the citation LINE; the comms-adjudicator graded them from the surrounding PROSE.
Ruling 1's test is *"does the surrounding prose already state the mechanism"* — that is a
prose question, so the prose reader wins. Both sites stay byte-identical.

### 3.2 `test_comms_render_architecture.py:495` — split verdict, split action

adj-152-tests: **LB**, repoint the address. adj-152-rep-comms: **PROVENANCE**, but flag the
number. I took **PROVENANCE for the address** (both wrong builds ARE named inline with their
exact mutations) and **struck the number** under Ruling 3. The address stays dangling and
that is the correct outcome — Ruling 1 does not repoint provenance.

### 3.3 `_comms_fakes.py` — the cluster-boundary overlap

rep-rest adjudicated it (2 sites, both P) and flagged possible overlap with the comms
adjudicator, who did not cover it. No conflict to resolve. I made **no edit** there except
the deliberate KEEP of `407` documented in §2.

---

## 4. Gates

### 4.1 Ruling-2 green receipts — taken BEFORE each conversion

Ruling 2 forbids re-tensing a pin that is genuinely still RED. Every converted site was
proven green first.

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_comms_render_architecture.py tests/test_brief_ledger.py -q -n auto
146 passed in 8.48s
```
```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_task_ledger.py -q -n auto
234 passed in 9.78s
```

And the symbols the prose claimed were missing, confirmed present in production:

| claimed missing | actually present |
|---|---|
| `BriefLedger.subscribed_name_skew` | `loremaster/loremaster/briefs.py:1093` |
| `auto_ack_at_register` | `server.py`, 5 occurrences |
| `_HEARTBEAT_SKEW_NAMES_CAP` | `server.py`, 4 occurrences |
| `STANDING_BRIEF` | `server.py`, 9 occurrences |
| `TaskLedger.create_many` / `.updated_since` | `tasks.py:1260` / `tasks.py:1219` |

Closing commits, derived with `git log -S`: **`17277d1`** (packet 02 render architecture)
for the first four; **`f80e95a`** (PKT-06 orchestration ledger verbs) for the last two.

### 4.2 pytest over every touched file

```
$ cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_comms_render_architecture.py tests/test_brief_ledger.py \
    tests/test_task_ledger.py tests/test_agent_registry.py \
    tests/test_comms_promise_registry.py tests/test_graph_surreal.py \
    tests/test_render.py tests/test_render_seam_pins.py \
    tests/test_render_mypy_layer.py tests/test_mcp_server.py \
    tests/test_comms_schema.py tests/test_message_ledger.py -q -n auto

71 failed, 1706 passed, 3 xfailed, 166 errors in 243.10s (0:04:03)
```

PASSED-COUNT present: **1706**. The 71 failed + 166 errors = **237, and every one of them
lives in 3 of the 12 files** — all packet-03, all committed-RED before I arrived:

| file | failed+errors | cause — VERIFIED, not assumed |
|---|---|---|
| `test_message_ledger.py` | **180** | `No module named 'loremaster.messages'` (matches the ledgered "180 EXPECTED RED" exactly) |
| `test_comms_schema.py` | **46** | `surreal_schema has no attribute 'generate_message_ddl'` (35) · `no attribute 'MESSAGE_TABLE'` (5) · the relation-table OVERWRITE flip not yet shipped (6) |
| `test_comms_promise_registry.py` | **11** | `No module named 'loremaster.messages'` |
| **the other 9 touched files** | **0** | — |

I did **not** take "packet 03, not mine" on faith — I ran each file and read the actual
error class, because a prose wave that broke a docstring-parsing test would hide behind
exactly that assumption. None of the 237 is at or near an edit of mine, and §4.3 proves
structurally that none *could* be.

### 4.3 The strongest instrument: AST-equivalence proof that NOTHING but prose changed

A passing count is weak evidence for a prose-only wave — the suite could pass with a
fixture value quietly altered. So I proved it directly: parse each touched file at `HEAD`
and in the working tree, **strip every docstring**, and compare `ast.dump`. Any change to a
test, an assertion, a fixture value, an import or a constant would differ.

```
IDENTICAL        loremaster/tests/test_comms_render_architecture.py
IDENTICAL        loremaster/tests/test_brief_ledger.py
IDENTICAL        loremaster/tests/test_comms_schema.py
IDENTICAL        loremaster/tests/test_comms_promise_registry.py
IDENTICAL        loremaster/tests/test_task_ledger.py
IDENTICAL        loremaster/tests/test_graph_surreal.py
IDENTICAL        loremaster/tests/test_agent_registry.py
IDENTICAL        loremaster/tests/test_render.py
IDENTICAL        loremaster/tests/test_render_seam_pins.py
IDENTICAL        loremaster/tests/test_render_mypy_layer.py
IDENTICAL        loremaster/tests/_sdk_guard.py
IDENTICAL        loremaster/tests/test_mcp_server.py
IDENTICAL        loremaster/tests/test_message_ledger.py

files=13 differing=0
AST_CHECK_EXIT=0
```

Script at `/tmp/ast_prose_check.py` (scratch — not committed; say the word and I will move
it in-tree, where it would generalise to any prose-only wave).

### 4.4 ruff + typecheck

```
$ cd /home/ejprice/PycharmProjects/lore && for i in 1 2; do uv run ruff check .; done
run1 RUFF_EXIT=0 -> All checks passed!
run2 RUFF_EXIT=0 -> All checks passed!
```

```
$ cd /home/ejprice/PycharmProjects/lore && for i in 1 2; do ./scripts/typecheck.sh; done
run1 TYPECHECK_EXIT=1 -> Found 55 errors in 5 files (checked 146 source files)
run2 TYPECHECK_EXIT=1 -> Found 55 errors in 5 files (checked 146 source files)
```

```
$ uv run pytest tests/test_agent_registry.py -q -n auto     # the last file I touched
150 passed in 7.49s
```

⚠ **ONE TRANSIENT NON-GREEN READING, REPORTED RATHER THAN BURIED.** Immediately after my
final edit, a single chained invocation returned `RUFF_EXIT=1 / Found 1 error` and
`Found 56 errors in 6 files`. **It did not reproduce** — ruff is exit 0 and typecheck is
exactly 55/5 across two clean runs each, above, and the AST proof is unchanged at
`differing=0`. I could not establish a cause (most likely a cache or a read racing the
just-written file); I am flagging it because an unexplained one-off on a gate is worth the
lead knowing about even when the stable state is clean. **If a reviewer sees 56/6, that is
the signal to look here, not a new defect from this wave.**

**Stable state: exactly the 55/5 baseline — not grown.** Distribution:

| file | errors |
|---|---|
| `test_comms_tool.py` | 32 |
| `_message_fakes.py` | 12 |
| `test_comms_promise_registry.py` | 7 |
| `test_message_ledger.py` | 3 |
| `test_surreal_schema.py` | 1 |

Two of those files are ones I touched. **Zero of their errors are at or near my edits:**
`test_comms_promise_registry.py`'s are at lines 718–796 (I edited 2231);
`test_message_ledger.py`'s at 156/1716/1736 (I edited ~21). All are the packet-03
`loremaster.messages` import class.

---

## 5. Sites needing edits that are OUTSIDE my writable set

All six are LOAD-BEARING per adj-152-tests §8 / adj-152-rep-rest §5.2. I made **no edit**.
Exact edits given so whoever owns these files can apply them without re-deriving.

### 5.1 ⚠ HIGHEST-VALUE: `test_surreal_harness.py:54` is now FALSE

The file's own anchor block asserts:

> *the reports they name (`REPORT-blindreader-150.md`, `REPORT-audit-150*.md`) are
> **UNTRACKED** scratch files at the repo root that repo law requires be deleted before any
> image build — so the citations are **not followable** and were never meant to be*

**Commit `7d2ff44` made that false.** Verified — all three are now tracked:

```
docs/plans/v2/receipts/2026-07-20-150/REPORT-audit-150-cold.md
docs/plans/v2/receipts/2026-07-20-150/REPORT-audit-150-final.md
docs/plans/v2/receipts/2026-07-20-150/REPORT-blindreader-150.md
(+ 5 more from the same wave)
```

This is precisely the class #152 exists to kill — **prose that contradicts the tree** — and
the archive that resolved 15 citations created it. Both adjudicators predicted this exact
consequence (adj-152-tests §5.2: *"the only edits needed are `:54` and `:56`"*).

**Proposed edit (`test_surreal_harness.py`, lines 51–60):** replace the "are UNTRACKED …
not followable" clause with:

```
they name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) were untracked
scratch files at the repo root, but were ARCHIVED at 7d2ff44 and now resolve under
``docs/plans/v2/receipts/2026-07-20-150/`` — so the ``F*``/``R*`` citations in this
file ARE followable, section-exactly. Their durable addresses remain the ledger rows
#150 / #151 and the wave's commits:
```

⚠ **And the same block's `:51` "HOW TO RESOLVE" heading is now under-selling itself** —
it declares the ids unfollowable when they are followable. Same edit covers both.

### 5.2 The three `_surreal_harness.py` repoints (adj-152-tests §8 rows 2–4)

⚠ **These need RE-ADJUDICATING, not applying as written.** The adjudicator proposed
collapsing them to `(#150)` *because* the reports were unrecoverable. After `7d2ff44` the
richer address is available and strictly better:

| line | current | I would now propose |
|---|---|---|
| 344 | `(audit-150 R5 / blindreader F10, one` | `(#150; receipts at docs/plans/v2/receipts/2026-07-20-150/, one` |
| 419 | `designed 2.0s (blindreader-150 F2 / audit-150 R4), on a path` | `designed 2.0s (#150, F2/R4 in docs/plans/v2/receipts/2026-07-20-150/), on a path` |
| 454–455 | `# / blindreader-150 F10).` | `# seam's full budget once these two operations started retrying (#150, F10 in docs/plans/v2/receipts/2026-07-20-150/).` |

Note also the adjudicator's observation that `:344` spells the id `blindreader F10` where
every sibling uses `blindreader-150 F10` — an inconsistency worth normalising in the same
touch.

### 5.3 `test_retry_seam.py:7353` (adj-152-rep-rest §5.2, and #151's agent owns this file)

| current | proposed |
|---|---|
| `and is recorded as such in REPORT-contract-151.md.` | `and is recorded as such against finding #151.` |

Pure address swap; `#151` is a live ledger row and is already the sentence's subject.
⚠ `REPORT-contract-151.md` is **untracked at the repo root right now** — same closing
window as §6.1.

---

## 6. Escalations

### 6.1 ⚠ TIME-LIMITED — six probe scripts are still on disk, untracked

The `#150` archive at `7d2ff44` proved the pattern works. **The same window is open right
now for the probes**, and I had to strike numbers *because* they are untracked:

```
scratchpad/probe_budget.py            ← the instrument for row 17's struck count
scratchpad/probe_long_query_69.py
scratchpad/probe_long_query_66.py  /  _66b.py  /  _66c.py
scratchpad/probe_cosine_projection_s4b.py
scratchpad/probe_surface.py  ·  reaudit_probe1.py  ·  reaudit_probe2_mutation.py
```

`git ls-files scratchpad/ | wc -l` → **0**. Nothing there survives.

**rep-rest §6.3 counted 33 `scratchpad/` citations across the test tree** and both it and
the retryseam adjudicator independently called this class *worse* than the report
citations — a report is prose you can live without; **a probe is the only thing that can
re-derive a number.** Archiving what still exists under `docs/plans/v2/receipts/` costs one
`git add` and would let row 17's count (and others outside my scope) be restored honestly
rather than struck. **This expires at the next cleanup.**

Confirmed permanently gone, by whole-filesystem `find` (so Ruling 4 was correct for these,
not a judgment call): `capture_engine.py` · `probe_bootstrap.py` ·
`phase0-render-safety-ruling.md` · `PKT-06-build-design.md` · `measure_distinct.py`.

### 6.2 Two known bounds with no ledger row — repo law requires one

Repo law: *"WHEN YOU CANNOT CLOSE A HOLE, PIN IT … Every bound carries a NAMED RE-OPEN
TRIGGER."* I annotated both (rows 21, 23) but **cannot file findings** — not in my brief.

1. **`test_render_seam_pins.py:430`** — the accepted re-assigned-name evasion gap. Its
   acceptance authority was the `/tmp` ruling; nothing survives. Never ledgered.
2. **`test_impact.py:812`** (rep-rest DEFECT 4) — *"flagged for the team-lead as a
   writable-set gap"*, a real behaviour gap in `graph_surreal.tests_for` handed forward in
   a docstring with no row, no number, no decision point. I searched the ledger and found
   nothing matching. **This one is a behaviour defect, not a citation problem.**

Contrast `test_comms_promise_registry.py:2232` (row 3), which DID have a row (#143) — that
is what a correctly-ledgered bound looks like, and it is why that repoint was one token.

### 6.3 ✅ An open adjudicator question — ANSWERED, no follow-up needed

adj-152-tests §5.1 flagged that `W6`, `W7` and `W11` are cited by no pin in
`test_message_ledger.py`, and recommended a follow-up: *"Either they were killed by pins
elsewhere, ruled not-applicable, or **they are uncovered wrong builds**."*

**They are the report's own CONTROLS.** From the tracked table (lines 76–78):

```
| W6  | drain stamps the WHOLE pending set (*control*)      | 2 failed, 55 passed  | correctly killed |
| W7  | awaiting_answer returns the NEWEST question (*control*) | 1 failed, 56 passed | correctly killed |
| W11 | fan-out writes NO edges at all (*control*)          | 26 failed, 31 passed | correctly killed |
```

No pin is owed for them. **This closes the escalation** — and the anchor I added (row 25)
records it inline so the question cannot be re-asked from the tree.

### 6.4 Carried forward, unactioned (raised by adjudicators, outside my brief)

- **rep-comms §E1** — `report_path="REPORT-comms-c0-contract.md"` fixtures at
  `test_task_ledger.py:1984/2057` teach the repo-root form that repo law deletes. Not
  citations, so no verdict; but the ledger's own field documents #152's defect by example.
  Changing it alters what agents write into a live production column — **operator call.**
- **rep-comms §E2 / rep-rest §6.2** — single-line greps miss **line-wrapped** citations
  (2 of 19 in the largest comms file). Any future sweep of this class needs a line-joined
  pass; the filed production count of 61 has this exposure.
- **rep-rest §6.4** — the reverse error is also live: many `adversary` hits are **not
  citations** (`the "server is down" adversary` describes a fixture in 6 files). The filed
  count is inflated in one direction and deflated in the other; neither cancels the other.

---

## 7. Sites I declined to touch, and why

- **Every PROVENANCE site (~87% of the population).** Ruling 1 bans it. Byte-identical.
- **`test_comms_schema.py:1811`, `:2269`** — reconciled to PROVENANCE, §3.1.
- **`test_comms_render_architecture.py:495`'s address** — PROVENANCE; only the number
  struck, §3.2.
- **`_comms_fakes.py:676`'s `407`** — KEPT deliberately, §2 Ruling-3 exception.
- **`_sdk_guard.py:118`'s `6.2%–34.4%` range** — KEPT; protocol stated inline, the brief's
  named exception.
- **`test_brief_ledger.py:1484` and `test_comms_render_architecture.py:40`'s citation
  addresses** — both adjudicators refused to repoint these *because* the surrounding RED
  claim was false ("repointing launders the false claim"). **I fixed the false claim
  instead (rows 6–8) and still left the addresses alone**, since neither is LOAD-BEARING.
  The laundering hazard is gone; the churn ban still applies.
- **All 6 out-of-set sites**, §5.

---

## 8. Tool honesty

`lore_findings action=get` for **#143** and **#60** — both repoints in §2 rows 3 and 5 are
backed by the ledger row's own text, not by my inference (#143 turned out to be a verbatim
match for the trigger's described instrument; #60 turned out to be **resolved**, which
changed the wording I applied).

**Everything else was `git grep` / `sed` / `find`, said out loud per brief-base §4.** This
is the sanctioned fallback, not a routing-around: the whole task is a *non-symbol textual
seam* sweep over prose in comments and docstrings — case (b) of the three grep-honest cases
in CLAUDE.md — plus case (a), exhaustiveness. lore's symbol graph does not model comment
prose. **No friction to file:** lore was not the wrong tool, it was the wrong question for
lore.

## 9. What I did not do

- **No git state touched** — nothing staged, committed, or reverted. The lead commits.
- **No production code** (`loremaster/loremaster/`), no `docs/`, no `.claude/`. My only
  writes are the 13 test files in §2 and this report.
- **No test logic, assertion, fixture value or import changed** — proven, §4.3.
- Did not touch `test_retry_seam.py`, `test_surreal_harness.py`, `_surreal_harness.py`
  (#151's agent owns them).
- Did not file the two findings §6.2 calls for — outside my brief; raising instead.
