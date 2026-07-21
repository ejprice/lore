# REPORT-adj-152-tests

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - The brief's premise "`git ls-files | grep -iE "blindreader|audit-102|audit-fix|adversary"` returns NOTHING TRACKED" is **FALSE as stated** — it returns one tracked hit. Per-pattern re-derivation below.
  - **A TRACKED RECEIPTS ARCHIVE ALREADY EXISTS** (13 `REPORT-*.md` under `docs/*/receipts/`). A large sub-population of my 82 sites is therefore **not dangling at all** — the reports are tracked, the citations merely omit the path. This is a third state the brief's two-verdict scheme does not anticipate; I mapped it onto LOAD-BEARING and say so per-site.
  - `test_surreal_harness.py` was edited by the concurrent agent DURING my run (+55 lines below old line 397). Population stable at 82, citation text unchanged. Both old and current line numbers given.
- **decisions-needed:**
  1. **TIME-LIMITED:** `REPORT-blindreader-150.md`, `REPORT-audit-150-cold.md`, `REPORT-audit-150-final.md` **still exist untracked at repo root right now**. Archiving them under `docs/plans/v2/receipts/` would resolve 17 sites at a stroke and cost one `git add`. They are deleted at the next image build and the knowledge is gone permanently. Operator call, and it expires.
  2. Two sites admit two readings (test_message_ledger.py W-labels; test_comms_tool.py §-labels) — both written out in §5, with my pick.
- **receipt pointers:** §1 verification · §2 population · §3 the DEFECT · §4 full 82-row table · §5 two-reading forks · §6 extension population

**Verdict tally: 73 PROVENANCE · 9 LOAD-BEARING (11%) · 1 flagged DEFECT (also load-bearing).**

---

## 1. Verification — I did not inherit the brief's claim

```
$ git ls-files | grep -iE "blindreader|audit-102|audit-fix|adversary"
docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md
EXIT=0
```

Per-pattern (exit code checked on each):

| pattern | tracked hits | rc |
|---|---|---|
| `blindreader` | none | 1 |
| `audit-102` | none | 1 |
| `audit-fix` | none | 1 |
| `adversary` | **1** — `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md` | 0 |

**So the brief's "returns NOTHING TRACKED" is false.** The three report *families* it names are indeed untracked; `adversary` is not. That single hit is load-bearing for this whole adjudication and is why the tally below is not a rubber stamp.

### 1a. The archive convention already exists — and says so in its own words

`docs/plans/v2/receipts/2026-07-19-packet03/README.md:3`:

> *"Preserved because repo law deletes root-level `REPORT-*.md` before an image build. … They are here so a claim can be audited back to its receipt."*

13 reports are tracked across two receipt dirs (`docs/plans/v2/receipts/2026-07-19-packet03/` ×8, `docs/orchestration/receipts/2026-07-19-comms/` ×5). **Finding #152's proposed fix direction is incomplete**: for the packet-02a/03-era citations the durable address is not a finding number — it is the tracked path, which preserves the *section labels* a finding number cannot.

### 1b. The cited section labels actually resolve — verified, not assumed

```
$ grep -oE "\bW[0-9]+\b" .../REPORT-adversary-pkt03.md | sort -u
W1 W2 W3 W4 W5 W6 W7 W8 W9 W10 W11
$ grep -nE "MAJOR-4|RESIDUAL 7\.4" .../REPORT-adversary-pkt03.md
18:- **MAJOR-4** the dirty-store migration pin covers `to` …
```

Every W-label cited in `test_message_ledger.py` and both labels cited in `test_comms_schema.py` resolve inside the tracked report. **These citations work today.** A bulk repoint at finding numbers would have *destroyed* working pointers.

### 1c. All six offered SHAs resolve

`6be78d6` · `0734d78` · `20e7635` · `fff1382` · `634da1c` · `9d29111` — all resolve to real commits with #150/#108/#120 subjects. The anchor block in `test_surreal_harness.py` that cites the first three is sound.

---

## 2. Population — derived from the grep, not the hand-list

```
$ git grep -nE "blindreader|audit-102|audit-fix-1|adversary" -- 'loremaster/tests/*.py' ':!loremaster/tests/test_retry_seam.py'
82 sites / 22 files
```

Matches the brief's per-file counts exactly. Bare, anchor-free patterns per repo law.

### 2a. ⚠ Concurrent-edit blast radius (brief-flagged, and it fired)

`test_surreal_harness.py` mtime moved from my first grep to my line extraction. Re-grep: **13 sites still, identical citation text, line numbers +55 below old 397.** `_surreal_harness.py` untouched (4 sites, lines unchanged).

| old line | current line | anchor text (quoted, re-locatable) |
|---|---|---|
| 39 | 39 | `(blindreader-150 F6). So the operations are now DISCOVERED` |
| 46 | 46 | `ENGINE SAID — blindreader-150 F1), budget COMPOSITION` |
| 51 | 51 | `HOW TO RESOLVE THE ``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS` |
| 54 | 54 | `they name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) are UNTRACKED` |
| 397 | **452** | `# call COUNTS cannot see that build (blindreader-150 F8).` |
| 445 | **500** | `blindreader-150 F10). That was pre-existing, and harmless-ish` |
| 536 | **591** | `` ``__cause__``/``__context__`` both ``None`` (blindreader-150 F1). `` |
| 612 | **663** | `to name ("blindreader-150 F1"), which are untracked scratch files` |
| 652 | **703** | `(measured 3.812s against a designed 2.0s: blindreader-150 F2 / audit-150 R4).` |
| 752 | **803** | `f"first fix (blindreader-150 F2)."` |
| 838 | **889** | `# identified as the one that actually loses the bootstrap race (blindreader-150 F6).` |
| 1065 | **1116** | `# that used to be the only structural guard here (blindreader-150 F4 / audit-150 R3).` |
| 1123 | **1174** | `` except ImportError:`` wrapper GREEN (blindreader-150 F3, demonstrated) `` |

All 17 blast-radius sites (13 + 4) are anchored by quoted text above and in §4.

---

## 3. ⚠ DEFECT — a "Receipt:" pointing at a file that does not exist

**`loremaster/tests/_sdk_guard.py:130`**

```python
# Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``.
SAFE_CONNECTION_METHODS = frozenset({"signin", "close"})
```

Verified:
```
$ git ls-files | grep -c "^scratchpad/"   → 0
$ ls scratchpad/blindreader2/             → No such file or directory
```

`scratchpad/` exists on disk with unrelated files; **`blindreader2/` was never there and nothing in it is tracked.**

**Why this is worse than the rest of the population.** The 21 lines above it retire two prior point-estimates as *"neither reproducible as stated"*, then assert a re-measured range — **6.2 %–34.4 %** across three named runs (55/160, 43/160, 10/160) — and that range is quoted as standing law in `CLAUDE.md` and sits directly above a `frozenset` that is a **deny-by-default security allowlist**. Repo law: *"Every exemption in a deny-by-default safe-set must be evidence-backed (a live probe proving it cannot conflict), never 'it writes no row'."* The word `Receipt:` is a promise that the evidence is retrievable. **It is not.** This is the repo's own "a failure message that promises a check the assertion does not perform" pattern, applied to provenance: the comment promises an artifact, and the artifact is absent.

I am **not** repointing this, because repointing a claim whose evidence is gone would launder it. Two honest options for the operator:

- **(a) Re-measure and re-cite.** The protocol is fully specified inline (16 racers × 10 rounds, bootstrap UNRETRIED). Re-run, archive the probe under `docs/plans/v2/receipts/`, cite the tracked path.
- **(b) Demote the claim honestly** — minimal edit, no new evidence claimed:
  ```python
  # Receipt: the protocol above is reproducible; the probe script was a scratch file and is gone (#152).
  ```

**My pick: (a).** The number gates a security allowlist and is quoted as standing law; (b) leaves standing law resting on an unreproducible measurement. But this is a scope call, not mine.

---

## 4. The 82-site verdict table

Every site gets its own line. No collapsing, no ditto, no ranges.

Verdict key — **P** = PROVENANCE (mechanism stated in full inline; following the citation adds nothing → LEAVE IT) · **LB** = LOAD-BEARING (citation is the authority → repoint) · **P\*** = sweep false positive: matched the pattern but is not a citation at all (the English word "adversary"), so there is nothing to repoint.

### `_message_fakes.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `_message_fakes.py:20` | `Neither the author's satisfiability run nor the contract-adversary's could see` | **P** | Role reference, no address. The next two lines name **finding #133** explicitly as the durable authority. Already anchored. |

### `_sdk_guard.py` (2)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `_sdk_guard.py:118` | `THAT IS A RANGE, AND IT IS A RANGE ON PURPOSE (audit-fix-1 A4).` | **P** | The 11 lines that follow state the entire mechanism — why a range, what was retired, the protocol, all three run results. Following `A4` adds nothing. Leave. |
| `_sdk_guard.py:130` | `` # Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``. `` | **LB — DEFECT** | See §3. File does not exist; `scratchpad/` untracked. Do **not** silently repoint. |

### `_surreal_harness.py` (4) — ⚠ blast radius

| file:line | citation text | verdict | proposed replacement |
|---|---|---|---|
| `_surreal_harness.py:108` | `…holds nothing (#151, blindreader-150 F1).` | **P** | Already carries the durable address `#151` first; the dead id is redundant tail. Leave. |
| `_surreal_harness.py:344` | `# failure against the shared dev server (audit-150 R5 / blindreader F10, one` | **LB** | → `# failure against the shared dev server (#150, one`. This file has **no anchor block** (unlike its test sibling), so it inherits no resolution. ⚠ Also note the id is spelled `blindreader F10`, not `blindreader-150 F10` — an inconsistent form the sibling file never uses. |
| `_surreal_harness.py:419` | `designed 2.0s (blindreader-150 F2 / audit-150 R4), on a path that runs for EVERY` | **LB** | → `designed 2.0s (#150), on a path that runs for EVERY`. The citation is the sole authority for the measured **3.812s vs 2.0s** figure. |
| `_surreal_harness.py:455` | `# / blindreader-150 F10).` | **LB** | Lines 454–455 → `# seam's full budget once these two operations started retrying (#150).` |

### `test_brief_ledger.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `test_brief_ledger.py:1308` | `"""adversary P2 finding #4 (REPORT-c1-audit-adversary.md): the` | **P** | Report untracked, but the docstring names **finding #94**, `_MAX_FLEET_LIMIT` (200) and the measured 407 round-trips inline. Fully self-contained. Leave. |

### `test_comms_render_architecture.py` (2)

| file:line | citation text | verdict | proposed replacement |
|---|---|---|---|
| `…:480` | `"""§9.2 v8 CAP + collapse + ORDER (the adversary-found gap): with MORE` | **P** | Cites the design doc §9.2 (durable) and describes the gap fully. Leave. |
| `…:495` | `contract 617/0 (REPORT-pkt02-adversary.md §"surviving wrong builds").` | **LB** | Report **untracked and not archived** (checked: pkt02 has no receipts dir). The specific number **617/0** and the two named wrong builds are attributed solely to it. → `contract 617/0 (packet 02: docs/plans/v2/02-comms-render-architecture.md; the adversary report was a root scratch file and is gone).` |

### `test_comms_schema.py` (3)

| file:line | citation text | verdict | proposed replacement |
|---|---|---|---|
| `…:1811` | `# ⚠ RESIDUAL 7.4 (adversary): this endpoint must be an EXISTING record of` | **LB — resolvable** | `RESIDUAL 7.4` is a section label into a **TRACKED** report. → `# ⚠ RESIDUAL 7.4 (docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md):` |
| `…:2269` | `"""⚠⚠ MAJOR-4 (adversary) — THE INSTRUMENT WAS AIMED AT THE WRONG TABLE.` | **LB — resolvable** | `MAJOR-4` verified present at that report's line 18. → `"""⚠⚠ MAJOR-4 (docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md) — THE INSTRUMENT WAS AIMED AT THE WRONG TABLE.` |
| `…:2393` | `field, an unrelated ASSERT, a typo in the statement. The adversary's own` | **P** | Names `§8.2` but states the whole story inline (control broken for a different reason → unsound attribution). Leave. |

### `test_comms_tool.py` (20)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:317` | `small-N blind spot the C1 adversary's finding #96 audit proved` | **P** | Names **finding #96**; the `len` vs `sum` mechanism is spelled out in the 6 preceding lines. |
| `…:318` | `(REPORT-c1c-contract-adversary-96.md §P1). Asserted as its own named` | **P** | Continuation of 317; untracked report, but #96 + inline mechanism carry it. |
| `…:758` | `"""adversary P2 finding #2 (REPORT-c1-audit-adversary.md): mutating` | **P** | States the mutation, the 643-green count and the leak precisely. |
| `…:783` | `"""adversary P2 finding #3: the empty-roster branch renders` | **P** | Names the exact rendered string and the real-world trigger. |
| `…:795` | `"""adversary P2 finding #5: the label/set agreement pin above is` | **P** | States N=4, the cap (200) and what the fixture adds. |
| `…:1117` | `"""BLOCKER pin (contract-adversary §1): the self-ack wiring must be` | **P** | Includes the *literal wrong-build line of code* and the 832/0 receipt. Strongest self-containment in the file. |
| `…:1124` | `fleet", and it passed the ENTIRE pre-adversary contract (832 passed, 0` | **P** | "pre-adversary" is a time reference, not an address. |
| `…:1536` | `pre-adversary contract. Finding #98 closed the monoculture for the SELF-ACK;` | **P** | Names **#98** durably. |
| `…:2053` | `"""finding #94, adversary BLOCKER (REPORT-c1-audit-adversary.md §P2): the` | **P** | Names **#94**; explains the isolated-pin-never-called defect fully. |
| `…:2056` | `it. The adversary shipped a perfect bulk method, left ``_comms_fleet``'s` | **P** | Role reference inside the same docstring. |
| `…:2125` | `"""adversary P2 finding #4: the defect was MEASURED at limit=200` | **P** | Gives the constant and the 407 figure inline. |
| `…:2386` | `"""Contract-adversary §2: the bound is a caller/SHAPE error, so it must` | **P** | Cites design §8 step 4 and §7 (durable) and states the 554/554 wrong build. |
| `…:2520` | `Parametrised over the brief NAME (contract-adversary §1): the value that` | **P** | Names the wrong-build guard expression inline. |
| `…:2870` | `"""BLOCKER (C1 adversary, finding #96 audit —` | **P** | Names **#96**; both cap-boundary fixtures named by test name. |
| `…:2871` | `REPORT-c1c-contract-adversary-96.md §P1/§MISSING PINS #1): the` | **P** | Continuation of 2870. |
| `…:2926` | `"""MEDIUM (C1 adversary, finding #96 audit — REPORT-c1c-contract-` | **P** | Names the mutant, the two conditions, the ugly served string. |
| `…:2927` | `adversary-96.md §MISSING PINS #2): the omission branch` | **P** | Continuation of 2926. |
| `…:2941` | `DEVIATION from the adversary's proposed framing: its report names` | **P** | ⚠ *Weakest P in the file* — a documented deviation from an unreadable proposal. But the docstring then states the full reason (design §0.3, `uuid5(session, name)`, §5.3), so the reader can re-derive the deviation without the report. Leave. |
| `…:3540` | `"""LOW (C1 adversary, finding #96 audit — REPORT-c1c-contract-` | **P** | Names **#96**; states the §10 inventory gap fully. |
| `…:3541` | `adversary-96.md §MISSING PINS #3): the skew line's ``{session}`` is` | **P** | Continuation of 3540. |

### `test_comms_wiring.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:480` | `"""Parametrised over the brief NAME (contract-adversary §1): the E2E` | **P** | Cites design **§5.1 step 2** (durable) and states the monoculture defect. Leave. |

### `test_diff.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:117` | `# A port with nothing listening — the "server is down" adversary (the SAME dead` | **P\*** | **Not a citation.** English word for a fault-injection fixture. Nothing to repoint. |

### `test_graph_surreal.py` (2)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:128` | `# A port with nothing listening — the "server is down" adversary (the same dead` | **P\*** | Not a citation — dead-port fixture prose. |
| `…:1151` | `# equivalence across a boundary-adversary corpus + an EXPLAIN-based pin that` | **P\*** | Not a citation — "boundary-adversary corpus" describes a test corpus. Cites **ledger #30** durably one line up. |

### `test_mcp_server.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:1305` | `# Finding #125 (the honesty line), adversary §A5 — the escalation the operator` | **P** | Leads with **#125** and dates the operator ruling (2026-07-14); §A5 is redundant tail. Leave. |

### `test_memory_backend.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:263` | `# A port with nothing listening — the "SurrealDB is down" adversary for the` | **P\*** | Not a citation — dead-port fixture prose. |

### `test_message_ledger.py` (9) — all resolvable against a TRACKED report

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:396` | `KILLS the adversary's W5.` | **P** | W5 = leaked `message:` prefix; stated in full in the 5 lines above. W5 verified present in the tracked report. |
| `…:561` | `none of them can tell the two keys apart. KILLS the adversary's W8.` | **P** | Name-vs-id dedupe fully explained inline. |
| `…:600` | `KILLS the adversary's W9 (drops the LAST recipient when >2) and W10` | **P** | **Self-decoding** — both W-labels carry their own gloss in parentheses. Best-shaped citation in the population. |
| `…:971` | `KILLS the adversary's W2.` | **P** | The 2/3/0 discrimination arithmetic is spelled out above. |
| `…:1240` | `⚠ The adversary wondered whether this is a spec GAP. It is not — both the` | **P** | Records an adjudication and gives the reason (both param and column are in the approved design). |
| `…:1655` | `KILLS the adversary's W3.` | **P** | Monoculture mechanism stated inline. |
| `…:1699` | `would correlate them in every fixture in this file (the adversary's W1).` | **P** | States the orthogonality reason inline. |
| `…:1755` | `waiting". KILLS the adversary's W1.` | **P** | States the grade-keyed wrong build inline. |
| `…:1889` | `KILLS the adversary's W4.` | **P** | `asked_at` fabrication mechanism stated inline. |

**Recommended addition (not a per-site repoint) — see fork §5.1:** one file-level anchor line naming the tracked report, so the W-set is resolvable as a *coverage index*.

### `test_retired_symbols.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:37` | `cold adversary walked through every one of them.)` | **P** | Role reference; the measured 83-candidate/4-real result and the "cries wolf 79 times" reasoning are inline. Leave. |

### `test_shellout_allowlist.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:3` | `The defect this closes is the one the contract-adversary found sitting UNDER the honesty` | **P** | Names **#125/#131** in the very first line; the whole no-git-in-image story follows. Leave. |

### `test_shellout_seam_perimeter.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:23` | `only adversary this gate has — an honest one who made a mistake.` | **P\*** | **Not a citation** — this is the *threat model* sentence repo law requires ("an honest developer, not a hostile author"). The word is doing rhetorical work. Repointing it would damage the file. |

### `test_snapshots.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:1002` | `# A port with nothing listening — the "server is down" adversary (the SAME` | **P\*** | Not a citation — dead-port fixture prose. |

### `test_surreal_harness.py` (13) — ⚠ blast radius; already anchored file-wide

This file **already carries the fix #152 asks for**, at lines 51–62: a `HOW TO RESOLVE` block that declares the ids unfollowable and maps them to `#150`, `#151`, and three commit SHAs (all verified to resolve, §1c). Every citation below therefore inherits a durable resolution **without individual edits** — the "anchor once per file" pattern finding #152 itself endorses.

| old→cur line | citation text | verdict | note |
|---|---|---|---|
| 39→39 | `(blindreader-150 F6). So the operations are now DISCOVERED by driving both functions` | **P** | Anchored by 51–62. Mechanism (use() = the call that loses the race) inline. |
| 46→46 | `ENGINE SAID — blindreader-150 F1), budget COMPOSITION (several operations driven by one` | **P** | Anchored. Three properties named inline. |
| 51→51 | `HOW TO RESOLVE THE ``blindreader-150 F*`` / ``audit-150 R*`` CITATIONS IN THIS FILE.` | **LB — already correct** | This line **is** the durable resolution. No edit unless the reports are archived (§5.2). |
| 54→54 | `they name (``REPORT-blindreader-150.md``, ``REPORT-audit-150*.md``) are UNTRACKED` | **LB — already correct** | States the dangling-by-design fact explicitly. Only edit if archived. |
| 397→**452** | `# call COUNTS cannot see that build (blindreader-150 F8).` | **P** | Anchored. The order-vs-count wrong build is stated in full. |
| 445→**500** | `blindreader-150 F10). That was pre-existing, and harmless-ish while a failure meant` | **P** | Anchored. Socket-leak mechanism inline. |
| 536→**591** | `` ``__cause__``/``__context__`` both ``None`` (blindreader-150 F1). `` | **P** | Anchored. Carries the measured dict verbatim. |
| 612→**663** | `to name ("blindreader-150 F1"), which are untracked scratch files at the repo root` | **P** | Anchored — and this line is itself #150's *worked example* of the repoint (it already names **#151** as the durable address two lines up). Model site. |
| 652→**703** | `(measured 3.812s against a designed 2.0s: blindreader-150 F2 / audit-150 R4).` | **P** | Anchored. Both numbers inline. |
| 752→**803** | `f"first fix (blindreader-150 F2)."` | **P** | Anchored. In an assertion message that states the whole composition argument. |
| 838→**889** | `# identified as the one that actually loses the bootstrap race (blindreader-150 F6).` | **P** | Anchored. Reach-of-the-mutation-proof reasoning inline. |
| 1065→**1116** | `# that used to be the only structural guard here (blindreader-150 F4 / audit-150 R3).` | **P** | Anchored. Cites CLAUDE.md's safe-set law directly. |
| 1123→**1174** | `` except ImportError:`` wrapper GREEN (blindreader-150 F3, demonstrated) `` | **P** | Anchored. States the AST property and why `tree.body` is insufficient. |

### `test_surreal_manifest.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:132` | `# A port with nothing listening — the "server is down" adversary (same dead` | **P\*** | Not a citation — dead-port fixture prose. |

### `test_surreal_store.py` (10)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:126` | `# A port with nothing listening — the "server is down" adversary. Connecting here` | **P\*** | Not a citation — dead-port fixture prose (the original of the five copies). |
| `…:3342` | `argued. The cold adversary built ``wb6-budget-only``: a **totally` | **P** | Names the wrong build by id and states exactly what it proved (passes 8/16/32-way). |
| `…:3397` | `# claim was wrong and a cold adversary measured it:` | **P** | A self-correction; the corrected content follows in full. Exemplary. |
| `…:3400` | `# every time — 300/300 idle and 200/200 under loadavg 32 (adversary-measured;` | **P** | Attribution tag on a number stated inline with its protocol. |
| `…:3428` | `**Catches (each proven by the adversary as a build the old pins could not` | **P** | Every catch named by wrong-build id (`wb5-row-seeded`, `wb16`, `wb17`, `wb3`, `wb6-budget-only`). |
| `…:3505` | `# on it is straddled by some table. A cold adversary measured exactly that — my` | **P** | Retracts a false claim and gives the replacing measurements (30-slot 26 %, 45-slot 52 %, 55-slot 70 %). |
| `…:3661` | `The cold adversary defeated that scan with **six of seven** evasions — the` | **P** | Shows the defeating refactor as a literal code block. |
| `…:3709` | `# except-body scan sees nothing. SIX of these were built by the cold adversary` | **P** | The seven evasions are enumerated in the code immediately below. |
| `…:3859` | `cold adversary defeated each with a one-line refactor; the last, most elaborate` | **P** | Gives the 13-of-15 + 3-false-positive result inline. |
| `…:4697` | `# past 1040 green comms tests, a cold code audit and a contract adversary, and` | **P** | This is the **#107** narrative; the virgin-DB blind spot is stated in full. Role reference, not an address. |

### `test_task_ledger.py` (1)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:2078` | `THE pin the cold adversary proved was missing. It built ``wb-string-gate``:` | **P** | Names **#102** one line up, the wrong build by id, and its 545/ruff/mypy-0 score. Leave. |

### `test_workspace_status.py` (5)

| file:line | citation text | verdict | note |
|---|---|---|---|
| `…:463` | `# NOTE (adversary A4): this fixture declares NO ``path``, so on its own it` | **P** | States precisely what this fixture can and cannot discriminate, and names the sibling pin that covers the gap. |
| `…:495` | `# THE POLICY-vs-PROXY PIN (adversary A4 — a wrong build passed 24/24 without it).` | **P** | The 24/24 receipt plus the full validator/mypy reasoning follow inline. |
| `…:640` | `"""The section describes the watched tree **NOW**, not at boot (adversary A1).` | **P** | Names **#125** and states the long-lived-process reasoning. |
| `…:767` | `The adversary built the build a well-informed builder actually writes once they` | **P** | Role reference; the ROUTING-IS-NOT-SHARING build and its 22-of-24 score are described in full. |
| `…:1032` | `# THE OTHER ALTITUDE (adversary A1). ``TestFreshOnEveryRead`` proves the pure` | **P** | Cites a **test class name that lives in the tree** — already a durable address by the brief's own definition. |

---

## 5. Forks — sites admitting two readings

### 5.1 `test_message_ledger.py`'s nine W-labels: per-site vs file-level

- **Reading A (per-site):** each `KILLS the adversary's W_n` states its mechanism fully → all nine are **PROVENANCE**, leave untouched.
- **Reading B (as a set):** the W-labels are not nine independent notes, they are a **coverage index**. Their collective claim — *"the contract kills the adversary's wrong builds"* — is checkable only against the enumeration `{W1…W11}`. The tests cite W1–W5 and W8–W10; **W6, W7 and W11 are cited nowhere in this file.** A reader asking "did we cover them all?" cannot answer from the tree, and under Reading A never learns the question exists.

**My pick: A for the nine sites (they stay PROVENANCE in §4), plus ONE file-level anchor** — cheapest edit that makes Reading B answerable, mirroring `test_surreal_harness.py:51`:

```
# The ``W<n>`` labels below are the packet-03 adversary's wrong-build enumeration
# (W1..W11), resolvable at
# docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md.
```

⚠ **And a real question falls out of it, which I am raising rather than answering:** W6, W7 and W11 are cited by no pin in this file. Either they were killed by pins elsewhere, ruled not-applicable, or **they are uncovered wrong builds**. I did not verify which — it is outside a citation adjudication, and it is exactly the kind of thing that should not be silently noticed. **Recommend a follow-up check.**

### 5.2 The #150 reports still exist — a closing window

`REPORT-blindreader-150.md`, `REPORT-audit-150-cold.md`, `REPORT-audit-150-final.md` are **on disk at repo root right now**, untracked.

- **Reading A:** dangling by design; anchor block at `test_surreal_harness.py:51` already handles it. Do nothing.
- **Reading B:** the archive convention exists (§1a) and was applied to packet 03 for exactly this reason. `git add` them under `docs/plans/v2/receipts/2026-07-20-finding-150/` and **all 17 blindreader/audit-150 sites become resolvable**, preserving the `F1…F10` / `R1…R5` section labels that `#150` alone cannot carry.

**My pick: B, and it is time-limited** — the next image build deletes them and the knowledge is gone permanently. Under B, the only edits needed are `test_surreal_harness.py:54` and `:56` (the two lines asserting the reports are UNTRACKED become false) plus optionally the three `_surreal_harness.py` repoints in §4. Cost: one `git add` + a two-line docstring correction. **This is the single highest-value action available and it expires.**

### 5.3 `test_comms_tool.py`'s §-labels into untracked reports

Eight sites cite `§P1`/`§P2`/`§MISSING PINS #n` in reports that are gone. I graded all **PROVENANCE** because each states its mechanism fully and names a durable finding (#94/#96/#98). The alternative reading — repoint all eight at their finding numbers — is a **12-line diff that adds no information a reader lacks**, i.e. the churn finding #152 explicitly warns against. I would not do it. Recorded so the operator can overrule.

---

## 6. Extension population — sites the brief's pattern misses

The brief asked me to report other report-shaped citations. Bare wide sweep:

```
$ git grep -nEi "REPORT-|blindreader|audit-[0-9]|audit-fix|adversary|scoutkill|dry-[0-9]|\baudit-[a-z]|per (the )?audit|W[0-9]-[A-Z]" \
    -- 'loremaster/tests/*.py' ':!loremaster/tests/test_retry_seam.py'
240 lines
```

**240 vs 82 — the brief's pattern sees roughly a third of the test tree's report-shaped citations.** The extension (~158 lines) breaks down as:

- **Genuine `REPORT-*.md` citations the narrow pattern misses** — ~60 across `test_impact.py`, `test_map.py`, `test_symbols.py`, `test_render*.py`, `test_agent_registry.py`, `test_search.py`, `_surreal_fakes.py`, `_comms_fakes.py`, `render_injection_scaffold.py`, `test_text_hygiene.py`, `test_sanitise.py`, `test_surreal_fakes.py`, `test_findings.py`, `test_store_read.py`, `test_schema_rebuild.py`, `test_server.py`, `test_source.py`, `test_txn_contention.py`, `test_comms_promise_registry.py`, `test_comms_fleet_grouping.py`. Notable: `REPORT-phase0-audit-1.md` ×7, `REPORT-slate-*.md` ×12, `REPORT-polish-*.md` ×6, `REPORT-c1-*.md` ×10 — **none tracked**.
- **Non-`REPORT` audit-pass ids:** `audit-findings #1/#2` (×5), `audit-read finding 3/4` (×4), `audit-waveb-1 finding #1/#3` (×3), `audit-w4a finding #1/#2` (×3), `audit-w1/w2` (×2), `audit-dimgate finding 1`, `audit-dry-2 F5`, `audit-150 R2/R5` (×3). These name review passes with **no report filename at all** — strictly harder to resolve than the 82.
- **False positives to exclude from any future count:** fixture *data* — `AGENT_AUDIT_C = "audit-c"`, `agent_name="audit-d"`, `report_path="REPORT-x.md"`, `refs=["REPORT-fixer-b.md"]`, `"audit-c2"` in a parametrize list. ~20 lines. These are test values, not citations.

**Recommendation:** the #152 ledger row should be corrected — its "the TEST tree carries **139** sites under the same patterns" is itself an under-count from a narrow pattern, and the row's own ⚠ CAUTION warns against exactly that. My bare sweep finds ~220 real citations (240 minus ~20 fixture-data false positives) in the test tree. **I did not adjudicate the extension** — it is outside my 82-site scope and I am not narrowing or widening scope unilaterally. Flagging it for the operator.

Also worth the operator's attention: **`test_retry_seam.py` (57 sites, another agent's scope) and the 61 production sites in #152 are a third and fourth population.** Four populations, four counts — conflating them is the #120/#102 defect class the ledger row explicitly warns about.

---

## 7. Tool honesty

`lore_findings action=get id_or_number=152` used for the durable finding text. **Everything else was grep**, which I say out loud per repo law and brief-base §4. This was correct rather than a fallback: the entire task is a *non-symbol textual seam* sweep over prose in comments and docstrings — case (b) of the three grep-honest cases in CLAUDE.md. `lore_search` ranks by meaning and cannot enumerate exhaustively, and exhaustiveness is the whole deliverable here. No friction to file: lore was not the wrong tool, it was the wrong *question* for lore.

---

## 8. Summary of proposed edits (9 LOAD-BEARING sites)

| # | file:line | action |
|---|---|---|
| 1 | `_sdk_guard.py:130` | **DEFECT — do not repoint.** Re-measure + archive probe (preferred), or demote the `Receipt:` claim honestly. §3. |
| 2 | `_surreal_harness.py:344` | `(audit-150 R5 / blindreader F10, one` → `(#150, one` |
| 3 | `_surreal_harness.py:419` | `(blindreader-150 F2 / audit-150 R4)` → `(#150)` |
| 4 | `_surreal_harness.py:455` | lines 454–455 → `# seam's full budget once these two operations started retrying (#150).` |
| 5 | `test_comms_render_architecture.py:495` | → `contract 617/0 (packet 02: docs/plans/v2/02-comms-render-architecture.md; the adversary report was a root scratch file and is gone).` |
| 6 | `test_comms_schema.py:1811` | `(adversary)` → `(docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md)` |
| 7 | `test_comms_schema.py:2269` | `(adversary)` → `(docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md)` |
| 8 | `test_surreal_harness.py:51` | already correct — edit **only** under fork §5.2 (archive) |
| 9 | `test_surreal_harness.py:54` | already correct — edit **only** under fork §5.2 (archive) |

Plus one non-site addition: the `test_message_ledger.py` file-level anchor (§5.1).

**I edited nothing.** This report is my only written file.
