# REPORT-adj-152-retryseam

brief-base v5 read

- **state:** done-with-deviations
- **deviations:**
  - Scope was "57 citation sites"; I also enumerated **two further dangling populations** the brief's pattern cannot see (§3) — 11 extension sites + 7 missing probe receipts. Reported, not fixed.
  - I ran the target test file (read-only, no mutation) to ground-truth ~25 "RED today" claims. Not explicitly authorised; it was the only instrument that could settle them. Receipt in §4.
- **decisions-needed:**
  - **DEFECT A (§4): ~25 false "RED today / expected RED" claims in this file.** Bigger than the citation problem. Needs an owner. Two of them sit *on* citation lines, so I could not repoint those without laundering a false claim.
  - **DEFECT B (§5): all 7 cited `scratchpad/` probe receipts are gone from disk AND untracked** — including the receipt for a served measured constant. Worse class than the report citations.
  - Ruling wanted on whether the 4 LOAD-BEARING repoints (§6) should be executed by a follow-up wave.
- **receipt pointers:** verification §1 · population §2 · extensions §3 · defects §4–5 · **57-row verdict table §7**
- **result:** 53 PROVENANCE · 4 LOAD-BEARING. No bulk rewrite proposed.

---

## 1. Verification — I did not inherit the lead's claim

```
git ls-files | grep -i <pattern>
  blindreader   exit=1  (empty — genuine no-match)
  audit-102     exit=1  (empty — genuine no-match)
  audit-fix     exit=1  (empty — genuine no-match)
  adversary     exit=0  → docs/plans/v2/receipts/2026-07-19-packet03/REPORT-adversary-pkt03.md
```

**Confirmed with one correction to the brief.** The brief's combined pattern would have returned a
non-empty result and could have been misread as "some reports survive". Per-pattern, three of four are
genuinely untracked. The single `adversary` hit is a **packet-03** report committed under
`docs/plans/v2/receipts/` — unrelated to this file's retry-seam contract adversary, and it does **not**
rescue any citation here.

Worth noting as a positive: `docs/plans/v2/receipts/` is proof the repo **already has a durable home
for reports**. The citations in this file predate that convention. That is the fix direction, and it
costs nothing to adopt.

## 2. Population — derived from the grep, not from a hand-list

```
git grep -nE "blindreader|audit-102|audit-fix-1|adversary" -- 'loremaster/tests/test_retry_seam.py'
  → 57 sites   (file is 7074 lines)
```

Matches the brief's 57 exactly. Full per-site table in §7.

## 3. Extension population — sites the brief's pattern MISSES

Widening to other report-shaped citation forms found **11 real additional sites**. Method: a bare
alternation over `audit-`, `REPORT-`, `W\d+-[A-Z]`, `dry-\d`, `fixwave`, `SCOUTKILL`, diffed against
the 57 by line number.

| line | citation | why the brief's pattern missed it |
|---|---|---|
| 3225 | `audit-dry-2 §3.3-3.4` | `audit-dry-2` ≠ `audit-102`/`audit-fix-1` |
| 3255 | `audit-dry-2 §2.2` | same |
| 3786 | `REPORT-audit-dry-2.md` | same — **and this is half of the §7 anchor block** |
| 7042 | `audit-polish-1 §P2` | agent name not in the pattern |
| 6592 | `` `W4-ACKSWALLOW` build`` | bare wrong-build label, no "adversary" nearby |
| 6642 | `` `W4-ACKSWALLOW`: name the type… `` | same |
| 6661 | `` `W4-ACKSWALLOW`'s shape `` | same |
| 6884 | `` `W1-SCOUTKILL` `` | same |
| 6964 | `**That is W1-SCOUTKILL.**` | same |
| 4492 | `a build that "fixes" F4` | bare finding-label back-reference |
| 3785 | `found F1,` / 3786 `F2, F3, F4` | bare finding labels |

**Verdict on the extension set: all PROVENANCE except 3786** (LOAD-BEARING — it is the second report
named in the §7 anchor block; see §6). The `W4-ACKSWALLOW` / `W1-SCOUTKILL` labels are all
accompanied by a full inline description of the wrong build they name, so they resolve without the
report.

⚠ **Excluded as noise, deliberately, with reasons** (they matched the wide pattern but are not
citations): 1555 and 1603 — `ruff's F401` / `64 × F401` are **lint codes**, not report sections. A
sweep that reported these as citations would be padding its own count.

## 4. ⚠ DEFECT A — ~25 FALSE "RED today" CLAIMS. THIS IS THE #151 CLASS, AT SCALE.

**This is the loudest thing I found, and it is larger than the problem I was sent to adjudicate.**

The file is a contract written *before* the retry-substrate wave landed. The wave **has** landed
(`9d29111` — "ONE retry seam — the eleven hand-rolled copies become one driver (#108 #120)";
`bootstrap_session` at `_txn.py:929` and `run_query` at `_txn.py:1026` both **exist**). The prose still
speaks in the pre-wave present tense throughout.

Ground truth:

```
uv run pytest loremaster/tests/test_retry_seam.py -n auto -q
425 passed, 1 warning in 7.90s
```

**425 passed, 0 failed.** Every one of the ~25 `RED today` / `expected RED` claims is now FALSE.
Enumerated at lines: 1014, 1038, 1321, 1372, 2050, 2293, 2824, 3591, 3658, 3711, 3721, 3789, 3933,
4085, 4123, 4432, 4715, 5489, 5560, 6586, 6620, 6766, 6813, 6869, 6975, 7004.

**The worst instance, and it is checkable to the line number** — `test_retry_seam.py:3591`:

> `"""RED today: briefs.py imports `_ERROR_CLASS_RETRYABLE_CONFLICT` (line 107), teaches it in a
> docstring (line 634) and branches on it (line 677)."""`

```
git grep -n "_ERROR_CLASS_RETRYABLE_CONFLICT" -- loremaster/loremaster/briefs.py
  → NO HITS
git grep -ln "_ERROR_CLASS_RETRYABLE_CONFLICT" -- loremaster/loremaster/
  → loremaster/loremaster/store/_txn.py     (only)
```

The symbol is **absent from `briefs.py` entirely**. The pin is GREEN and its docstring asserts RED
with three specific line numbers, none of which are true. This is exactly #151's shape — a docstring
clause that is outright false, which repo law rates strictly worse than one that dangles.

**Why this intersects my scope and why I did not quietly repoint around it:** three of my 57 sites
(6766, 6869, 6975) carry `— expected RED` *in the same parenthetical as the citation*. Repointing
those addresses while leaving the false claim beside them would have laundered the falsity behind a
durable-looking address. Per the brief, I flagged instead.

**Recommendation:** a separate sweep converts the pre-wave present tense to past
(`RED today` → `RED before 9d29111`), because the *historical* claim is true and valuable — it records
what the pin caught. Deleting the claims would lose that. This is a bigger job than #152 and wants its
own ledger row.

## 5. ⚠ DEFECT B — EVERY CITED PROBE RECEIPT IS GONE, INCLUDING ONE FOR A SERVED CONSTANT

A third dangling population, distinct from agent reports and worse in kind: `scratchpad/` receipt paths
cited as the evidence for **measured numbers**.

```
git ls-files scratchpad/ | wc -l   →  0     (nothing under scratchpad/ is tracked)
```

| cited path | on disk? |
|---|---|
| `scratchpad/contract-dry/probe_single_statement_conflict.py` (:90, :111) | **MISSING** |
| `scratchpad/contract-dry/probe_domain.py` (:111) | **MISSING** |
| `scratchpad/blindreader2/probe_bootstrap.py` (:404) | **MISSING** |
| `scratchpad/contract-dry/probe_bootstrap_ddl_race.py` (:1711) | **MISSING** |
| `scratchpad/contract-fix/hunt2-red-56.log` (:3261) | **MISSING** |
| `scratchpad/contract-fix/` (:3297) | **MISSING** |
| `scratchpad/contract-fix/probe_unique.py` (:3830) | **MISSING** |

**7 of 7 gone.** These are worse than the report citations because repo law is emphatic that inherited
numbers are re-measured and that a figure you did not measure is a rumour. The receipt is the
instrument that makes re-measurement possible, and it no longer exists.

**The mitigating fact, and it is real:** line 404's block states its protocol *inline*
("16 racers × 10 rounds = 160 virgin first-connects… three runs: 55/160, 43/160, 10/160"), and the
constant `_UNRETRIED_BOOTSTRAP_LOSS = "6.2%-34.4%"` is interpolated into the served assertion rather
than re-typed. Whoever wrote that block did the right thing: the number is **reproducible from the
prose without the script**. That is why I rate 404 LOAD-BEARING but not urgent.

## 6. The four LOAD-BEARING sites, with exact proposed replacements

Minimal edits — address swapped, surrounding prose untouched. Anchored by quoted text so they remain
locatable if the concurrent #151 contract work moves lines.

### L1 — `:6337` · **the strongest site in the file, and a perfect durable match exists**

Anchor: `` (Scout's own bare check-then-set is surfaced as a residual — see the report — because ``

A **bare, unnamed** pointer (`see the report`) that is the *only* address for a **known, deliberately
unclosed hole**: scout's `_ensure_connection` check-then-set, explicitly excluded from the P-2 pin.
Repo law: *"an unpinned known limitation is indistinguishable from an unknown one."*

**#127 is that residual, verbatim** — including the same sentence, independently written:
`"only one caller exists" is an argument, not a probe`. #127 also carries the **named re-open
trigger** ("any change that adds a second caller of `scout._ensure_connection` or makes scout
construct its own socket"), which the code comment lacks entirely.

```
- surfaced as a residual — see the report — because
+ surfaced as a residual (#127, with its re-open trigger) — because
```

### L2 — `:3783` · the §7 provenance anchor (report 1 of 2)

Anchor: `` Provenance, so nobody has to trust me: REPORT-blindreader-dry-1.md (a CONTRACT-BLIND ``

This is the file's **definition site** for "blindreader": every downstream `blindreader F1/F2/F3/F4`
label (20+ sites) resolves through it. Repointing this one line gives all of them a durable home —
the highest-leverage single edit available, and precisely the "anchor once per file" shape finding
#152 sanctions.

```
- Provenance, so nobody has to trust me: REPORT-blindreader-dry-1.md (a CONTRACT-BLIND
+ Provenance, so nobody has to trust me: the contract-blind diff read of the DRY
+ consolidation, landed 9d29111 (#108 #120) (a CONTRACT-BLIND
```

### L3 — `:3786` (extension site) · the §7 provenance anchor (report 2 of 2)

Anchor: `` F2, F3, F4; REPORT-audit-dry-2.md (the cold REFUTE audit) found the broken instrument ``

```
- F2, F3, F4; REPORT-audit-dry-2.md (the cold REFUTE audit) found the broken instrument
+ F2, F3, F4; the cold REFUTE audit of that same wave (9d29111) found the broken instrument
```

### L4 — `:404` · the receipt for a served measured constant

Anchor: `` # Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``. ``

The file is gone (§5). The protocol is inline, so the number survives; the *instrument* does not.

```
- # Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``.
+ # Receipt: the protocol above reproduces it; the range is standing law in CLAUDE.md
+ # (#126 carries the wave's latency acceptance).
```

**Two readings, and I say which I took:** L4 admits "PROVENANCE — the protocol is inline, so following
the receipt adds nothing." I went LOAD-BEARING because the citation is labelled **`Receipt:`** — it
makes a promise of checkable evidence that it cannot keep, and a dangling *receipt* for a served number
is a different failure from a dangling *provenance note*. **If the operator prefers the sparing
reading, L4 is the one to drop** — L1–L3 I would defend without qualification.

### Considered and REJECTED as load-bearing (stating these so the choice is visible)

- **`:6975`** (`blindreader-dry-2 F2 / audit-fix-1 B2`) — **#126 is its exact durable home** and I was
  tempted. Rejected: the mechanism (3 × 2.0s → one composed budget) is fully inline and **verified
  true** (`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS = 2.0`). #126 adds only the *acceptance decision*,
  which this pin does not depend on. Marking it LOAD-BEARING would have been repointing for tidiness.
- **`:6122`** (the §8 adversary anchor) — I initially had this as load-bearing by symmetry with L2.
  Rejected on re-read: unlike L2 it names **no report**, and each of P-1/P-2/P-3/R-3 is fully described
  at its own section head. There is nothing to repoint.

## 7. THE 57-SITE VERDICT TABLE

Every site individually. No collapsing, no ditto, no ranges.

| # | line | citation | verdict |
|---|---|---|---|
| 1 | 231 | `(Cold adversary, blocker 1.)` | PROVENANCE — WB-PROSE mechanism + 839/0 score stated in the next 6 lines |
| 2 | 235 | `The adversary built **WB-PROSE**` | PROVENANCE — build fully described inline |
| 3 | 334 | `P-5 (contract adversary, W8-NOKEYERROR)` | PROVENANCE — bare-`KeyError` door described in full, probe-verified inline |
| 4 | 393 | `**NEITHER WAS REPRODUCIBLE AS STATED** (audit-fix-1 A4)` | PROVENANCE — the three re-measured runs are quoted inline; CLAUDE.md carries the range |
| 5 | **404** | `Receipt: ``scratchpad/blindreader2/probe_bootstrap.py``` | **LOAD-BEARING → L4** (file MISSING, §5) |
| 6 | 912 | `audit-102 B1, now owned by the driver` | PROVENANCE — `#102` already durable in same sentence; floor verified `= 5` |
| 7 | 1027 | `named because a cold adversary will build it` | PROVENANCE — generic role, no address to follow |
| 8 | 1174 | `THE WRONG BUILD (the adversary built it; 839 passed / 0 failed…)` | PROVENANCE — score + mechanism inline |
| 9 | 1563 | `C-DEF-2 (contract adversary)` | PROVENANCE — both spy-binding failure modes spelled out |
| 10 | 1588 | `(and a cold adversary WILL build it)` | PROVENANCE — generic role |
| 11 | 1600 | `**RESHAPED … (C-DEF-2, contract adversary).**` | PROVENANCE — reshape rationale fully inline |
| 12 | 1739 | `The adversary broke it in one line` | PROVENANCE — 31/64 measurement + control stated inline |
| 13 | 2019 | `The adversary measured ``upsert`` at 31 … in 64 live attempts` | PROVENANCE — the number IS the substance, and it is here |
| 14 | 2937 | `The adversary defeated it with a **comment**` | PROVENANCE — defeat mechanism inline |
| 15 | 3585 | `a cold adversary walked through each one` | PROVENANCE — generic |
| 16 | 3641 | `attempt FLOOR (audit-102 B1)` | PROVENANCE — **verified**: `_MAX_TXN_CONFLICT_ATTEMPTS = 5` |
| 17 | **3783** | `REPORT-blindreader-dry-1.md` | **LOAD-BEARING → L2** (§7 anchor for all F1–F4) |
| 18 | 3798 | `(blindreader F1 — HIGH. "The single worst thing" in that report.)` | PROVENANCE — resolves via L2 anchor |
| 19 | 3913 | `**blindreader F1.**` | PROVENANCE — resolves via L2; mechanism inline |
| 20 | 4017 | `(blindreader F2 — HIGH.)` | PROVENANCE — resolves via L2 |
| 21 | 4068 | `**blindreader F2.**` | PROVENANCE — the promised-log-line defect stated in full |
| 22 | 4152 | `The blindreader's own fix shape observes…` | PROVENANCE — the observation is **quoted inline**; `ledger #31` already durable |
| 23 | 4195 | `P-4 (contract adversary, `WB-LOGSTORM`)` | PROVENANCE — level-not-name rationale fully inline |
| 24 | 4253 | `(blindreader F4 — MEDIUM. Behaviour ruling made by the lead.)` | PROVENANCE — resolves via L2 |
| 25 | 4416 | `**blindreader F4, and the lead's ruling.**` | PROVENANCE — the ruling itself is stated, not just cited |
| 26 | 4516 | `(blindreader F3 — HIGH, a design finding.)` | PROVENANCE — resolves via L2 |
| 27 | 4572 | `THE CONTRACT (blindreader's fix shape, adopted)` | PROVENANCE — sketch inline; **verified**: `bootstrap_session`/`run_query` exist |
| 28 | 4580 | `THIS SKETCH ONCE OMITTED IT (audit-fix-1 A2)` | PROVENANCE — regression + its named guarding test stated inline |
| 29 | 4691 | `**blindreader F3, structurally.**` | PROVENANCE — 30→1 collapse described inline |
| 30 | 5476 | `the exact build a cold adversary writes` | PROVENANCE — generic |
| 31 | 5537 | `(C-DEF-1, caught by the contract adversary)` | PROVENANCE — the `TypeError`-on-every-correct-build story is fully inline |
| 32 | 5873 | `(audit-fix-1 A2 · blindreader-dry-2 F6)` | PROVENANCE — the three served surfaces enumerated immediately below |
| 33 | 5911 | `the exact regression audit-fix-1 A2 predicts` | PROVENANCE — monoculture trap explained inline |
| 34 | 6019 | `The NOUN, read out of the message the seam actually RAISED (audit-fix-1 A2)` | PROVENANCE — derivation is in the code on the next line |
| 35 | 6037 | `R-1 (contract adversary)` | PROVENANCE — record-shape rationale inline; `ledger #31` durable |
| 36 | 6052 | `the NOUN, as an exact MAPPING (audit-fix-1 A2)` | PROVENANCE — the mapping is the adjacent literal |
| 37 | 6069 | `the emitting LOGGER (blindreader-dry-2 F6)` | PROVENANCE — assertion + message state it |
| 38 | 6122 | `A cold contract-adversary built the fix (W0)…` | PROVENANCE — names no report; all three survivors described below it (rejection reasoned in §6) |
| 39 | 6145 | `(adversary P-1, BLOCKER)` | PROVENANCE — full type-mismatch analysis follows |
| 40 | 6234 | `**adversary P-1 — the BLOCKER that survives everything else.**` | PROVENANCE — oracle stated inline |
| 41 | 6307 | `(adversary P-2, BLOCKER)` | PROVENANCE — double-checked-lock shape shown inline |
| 42 | **6337** | `the adversary just caught me shipping … see the report` | **LOAD-BEARING → L1** (bare pointer; only address for a known residual) |
| 43 | 6414 | `**adversary P-2 — the BLOCKER hiding behind a hand-list…**` | PROVENANCE — hand-list problem stated at 6122 |
| 44 | 6434 | `The wrong build (the adversary's `W7b`)` | PROVENANCE — consequence + score inline |
| 45 | 6472 | `(adversary P-3, BLOCKER)` | PROVENANCE — four-doors analysis follows immediately |
| 46 | 6563 | `**adversary P-3 — the BLOCKER item B left standing in three other doors.**` | PROVENANCE — doors enumerated in the adjacent parametrize |
| 47 | 6613 | `The adversary's `W4-ACKSWALLOW` build names the typed error…` | PROVENANCE — build described in full |
| 48 | 6665 | `` `tasks.supersede_task` is the one the adversary stripped `` | PROVENANCE — score + resulting false message quoted inline |
| 49 | 6709 | `(adversary R-3, latent)` | PROVENANCE — latency/latency-trigger reasoning inline, incl. re-open condition |
| 50 | 6725 | `R-3 (contract adversary)` | PROVENANCE — one-line restatement of 6709 |
| 51 | 6766 | `(blindreader-dry-2 F1 / audit-fix-1 B3 — expected RED)` | PROVENANCE **— but `expected RED` is FALSE, see DEFECT A** |
| 52 | 6801 | `**blindreader-dry-2 F1 / audit-fix-1 B3.**` | PROVENANCE — the three required keys are the adjacent constant |
| 53 | 6869 | `(blindreader-dry-2 F7 / audit-fix-1 B1 — expected RED)` | PROVENANCE **— but `expected RED` is FALSE, see DEFECT A** |
| 54 | 6931 | `**blindreader-dry-2 F7 / audit-fix-1 B1** — and the trap that comes with the fix.` | PROVENANCE — leak + type-change both described |
| 55 | 6975 | `(blindreader-dry-2 F2 / audit-fix-1 B2 — expected RED)` | PROVENANCE (#126 is its home; rejection reasoned in §6) **— `expected RED` is FALSE** |
| 56 | 6993 | `regardless of wall time — audit-102 B1` | PROVENANCE — **verified**: floor `= 5` |
| 57 | 6999 | `**blindreader-dry-2 F2 / audit-fix-1 B2** — three statements, ONE budget.` | PROVENANCE — the composition property is the assertion itself |

**Tally: 53 PROVENANCE · 4 LOAD-BEARING** (L1 `:6337`, L2 `:3783`, L3 `:3786` ext, L4 `:404`).

## 8. Why so few LOAD-BEARING — the judgement axis the brief asked me to reason about

The brief was right that the test tree's bar differs, and the direction surprised me: **it makes
*fewer* sites load-bearing here, not more.**

In production code a citation often *is* the whole rationale — the code shows the "what" and the
comment carries the "why". In this file the opposite holds. This contract was written to a repo law
that demands every pin carry its wrong-build, its measurement, and its re-open trigger **inline**, and
its author complied unusually thoroughly: nearly every citation sits beside a full statement of the
build it catches and the score that build achieved. The citation is a *byline*, not the authority.

So the three sites I pulled out are exactly the ones where that discipline **lapsed**:

- **`:6337`** — the only site that says "see the report" and states no substance at all. It is also
  the only one guarding an **unclosed** hole rather than a closed one, which is precisely the case
  repo law says must never be silently inherited.
- **`:3783` / `:3786`** — the anchor block, whose *stated purpose* is to be followable
  ("so nobody has to trust me"). A provenance note that exists to be checked and cannot be is
  self-defeating in a way the F1/F2/F3/F4 labels beneath it are not.

Everything else would have been churn a reviewer must diff for no gain — the outcome finding #152
explicitly warns against.

**Honest note on my own instrument:** the "resolves via the L2 anchor" reasoning in rows 18–29 is load-
bearing for those 12 verdicts. **If L2 is not executed, those rows do not become defects, but they do
lose their last durable footing** — every `blindreader F#` label in the file then names something with
no definition anywhere in the tree. L2 is the edit that makes the sparing verdict elsewhere honest.

## 9. Tool honesty

`lore_findings` (get/query) was first choice and did the decisive work: it resolved **#126/#127/#128**
and produced the verbatim #127 ↔ `:6337` match that made L1 provable rather than plausible.

**Fell back to `git grep` for the sweep itself, and saying so per repo law** — correctly, and for the
sanctioned reason: this is a **non-symbol textual seam** (prose inside comments and docstrings), one of
the three cases repo law names as grep's own. No lore index can answer "which comments cite an agent
report". No friction filed: the tool was not weak here, it was the wrong instrument by design.

`lore_findings action=query area=store` returned no matches — the store findings are filed under
`store._txn` / `scout` / `server`, not `store`. Minor discoverability wrinkle, not worth a row; I
resolved it by direct `get` on the numbers the brief supplied.

## 10. Everything else I noticed (operator owns scope)

1. **DEFECT A (§4)** — ~25 false "RED today" claims. **My top recommendation for a follow-up row.**
2. **DEFECT B (§5)** — 7/7 cited probe receipts gone; one backs a served constant.
3. **`docs/plans/v2/receipts/` already exists** and is tracked. Future waves should land reports there
   instead of deleting them — that closes #152 as a *class* rather than repointing it site by site.
   This is the one structural fix available and it costs nothing.
4. **#126 and #128's own bodies cite dangling reports** (`REPORT-blindreader-dry-2.md F2/F3`,
   `REPORT-audit-fix-1.md §B2/§12`). The ledger rows carry the substance, so they are sound — but
   **finding #152's population is larger than the code tree**. Worth knowing before anyone calls #152
   closed.
5. **I did not touch git state, and edited no file** other than this report.
