# REPORT-gate-blind-fixwave — closing 5 residuals of the #150 cold audit

brief-base v5 read

## SUMMARY BLOCK

- **state:** done-with-deviations
- **Item 1 (R1, receiver-blind deny leg):** DONE — and shipped **method-blind as well as
  receiver-blind**. That is the one deviation, upward, measured, one-line reversible.
- **Item 2 (R1b, symmetric receiver predicate):** DONE — NOT moot; the `use()` leg still
  needs it. Reasoning in §4.
- **Item 3 (R2, false count):** DONE — numerals DERIVED at assert time, not re-measured.
- **Item 4 (R4, false gate):** DONE — all three shared names now mutation-proven; the claim
  is executed, not softened.
- **Item 5 (R5, #151):** DONE — pin docstring *and* failure message name #151; wave-wide
  citation sweep verdicted per-site in §8.
- **deviations:** (1) DDL leg is method-blind, not `{query,execute}`-keyed — the SDK ships
  `query_raw`, measured cost zero (§3). (2) Items 1–4 landed in ONE commit; they are not
  separable in that file (§9). (3) One `_surreal_harness.py` line is outside my writable
  set — flagged, not edited (§8).
- **decisions-needed:** ratify or revert the method-blind widening (§3); rule on the
  `use()`-leg residual bound (§4, ESC-1); `_surreal_harness.py:27` fix is yours to grant (§8).
- **Item-1 fallout: ZERO sites.** Every variant measured; full classification §2.
- receipts: fallout §2 · deviation §3 · items §4–§7 · sweep §8 · gates §10 · mutations §11

---

## 1. Fallout measurement — the STOP condition, checked first

Per the brief I measured **before** shipping. Four predicates, over every module in
`loremaster/tests/` (92 modules), with a positive control on the measuring instrument
itself.

| variant | DDL leg | `use()` leg | sites found |
|---|---|---|---|
| **A** — current (HEAD) | receiver-keyed | receiver-keyed | **1** |
| **B** — as ruled | receiver-blind, `{query,execute}` | receiver-keyed | **1** |
| **C** — shipped | receiver-blind, **method-blind** | receiver-keyed | **1** |
| **D** — also blind `use()` | receiver-blind, method-blind | receiver-blind | **1** |

**The honest-code fallout is ZERO.** Not "small" — zero. The auditor's prediction is
confirmed: this tree's `DEFINE NAMESPACE` literals are bare strings, expected-value
constants, and source fixtures passed to scanner functions — never call ARGUMENTS. The
allowlist did not have to absorb anything; there was nothing to absorb.

## 2. Every flagged site, classified individually

There is exactly one site tree-wide, under every variant. Per repo law it gets a
`file:line` and its own verdict rather than a wholesale classification:

| file:line | what | verdict |
|---|---|---|
| `_surreal_harness.py:436` | `connection.use()` | **CORRECT — already allowlisted.** `drop_database` selects namespace+database for teardown and runs that select *under* the store retry seam, on a deadline composed with the drop's. This is the existing one-row allowance, unchanged, and its site-count pin still fires (§11 M6). |

No other site exists, so there is no residual set to classify. The gate's own
`test_no_test_module_outside_the_allowlist_bootstraps_a_session` re-derives this every run
and prints `file:line` for anything new.

**Positive control on the measuring instrument** (so the zero is not a broken scanner):
against a hand-rolled `db = AsyncSurreal(...)` bootstrap, variant A returns `[]` — i.e. it
reproduces the audit's blindness — while B/C return both DDL sites and D also returns the
`use()`. The instrument can see; the tree is genuinely clean.

## 3. DEVIATION — the DDL leg is method-blind, not `{query, execute}`-keyed

**What the ruling said:** flag a `.query(...)`/`.execute(...)`-shaped call carrying the
DDL on **any** receiver. **What I shipped:** any *method* carrying the DDL on any receiver.

**Why, and it is a receipt, not an argument:**

```
>>> [m for m in dir(surrealdb.AsyncWsSurrealConnection) if not m.startswith('_')]
[... 'live', 'merge', 'patch', 'query', 'query_raw', 'select', 'signin', ...]
```

The installed SDK ships **`query_raw` beside `query`**. A deny keyed on `{query, execute}`
is defeated by a real method on the real dependency, on the day it lands — which is the
identical failure the ruling was correcting one column over (`CLAUDE.md`'s own table:
*"the SDK gate keyed on 3 METHOD NAMES → defeated by the other 30"*). Shipping B would have
fixed the receiver axis and left the method axis holding the same class of bug.

**Measured cost of going further: zero** (variant C in §1 — identical to B and to A).

I judged this a strengthening squarely inside the ruling's stated *principle*
("stop enumerating the forbidden") while exceeding its stated *shape*, so it is disclosed
here rather than assumed. **It is one line to revert** — reinstate a
`if node.func.attr not in _DDL_CARRYING_METHODS: continue` guard in
`_executed_bootstrap_sites_in`. Your call; I did not treat the choice as mine to make
silently.

**The residual risk I am buying, stated plainly:** method-blind means
`<anything>.<anymethod>("...DEFINE NAMESPACE...")` flags. Today zero sites, because this
tree is pytest-style (bare `assert`) and scanner fixtures are passed as bare-function calls
(`ast.Name` func), which the scan never matches. A unittest-style
`self.assertEqual(x, "DEFINE NAMESPACE ...")` WOULD flag. That is a one-row allowlist entry
in a diff a reviewer can see — the design's intended cost — and I measured it does not
happen today.

## 4. Item 2 (R1b) — NOT moot, and here is why

The brief asked me to say explicitly whether item 1 subsumes it. **It does not.**

- The DDL leg is now receiver-blind, so it never calls `_is_connection_receiver`.
- The **`use()` leg still does**, and must: `use` is a generic English verb. An unqualified
  receiver-blind deny on `.use(...)` would fire on `monkeypatch.use()`, `fixture.use()`,
  and any unrelated helper — the false-positive class that gets a gate switched off. (Note
  variant D measured zero *today*; I did not ship it, because zero-today on a token that
  generic is luck, not a property.)
- So the asymmetry was still live: `self._connection` (an `ast.Attribute`, suffix-matched)
  caught, plain local `_connection` (an `ast.Name`, frozenset-tested) missed.

Fixed symmetrically — both node types now resolve to a name and take the same rule
(`in _CONNECTION_NAMES or endswith("connection")`). Pinned by
`test_the_use_leg_still_reads_the_shared_receiver_predicate`, which carries a negative
control (`monkeypatch.use(thing)` must NOT fire) so the pin cannot pass by the leg simply
matching everything.

**Honest residual (ESC-1):** a bootstrap that runs *only* `use()` on an oddly-named handle
— no DDL — is still missed. In practice a hand-rolled bootstrap runs the DDL too, and the
receiver-blind DDL leg sees that regardless of naming, so the *bootstrap* is caught even
when that one leg is blind. I have not pinned this bound because closing vs. pinning it is
a design call, not mine. **Recommend: pin it** per "when you cannot close a hole, PIN IT",
with re-open trigger *"the day a reconnect path selects a session without re-running DDL."*

## 5. Item 3 (R2) — derived, not re-measured

Re-measuring and re-hardcoding would have reproduced the defect a third time, exactly as
the brief warns. So:

- **Every live numeral is gone** from the rationale block. The two remaining occurrences of
  "23 sites, 22 of them" are explicit *quotations of the retired claim, framed as history*
  (`"It used to say…"`), which is what makes the section teach the lesson.
- Two new pins DERIVE the claims the numerals used to carry:
  - `test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING` — re-implements the OLD
    receiver-keyed predicate alongside the new one and asserts they find the same count per
    file. This is the §1 fallout measurement, executable, every run.
  - `test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here` — re-derives both
    populations and asserts the *relationship* the design rests on (literal ≫ executed),
    never either count, plus that the executed total equals the allowlist's granted total.
- **I also caught two live numerals I had introduced myself** during the interrogation pass
  — a `"7 of 9"` in a docstring beside an 11-entry parameter list (already contradicting
  itself), and a surviving `"22 of the 23"`. Both replaced by pointers at the executable
  list. Flagging this because it is the same defect class inside its own fix, and I would
  rather report catching it than have it found later.

## 6. Item 4 (R4) — the claim is EXECUTED

The block named three shared constants and promised *"that mutation is not an argument
here; it is executed, below."* Only `_SESSION_SELECT_METHOD` was. Now all three are, each
with a positive control before the mutation and `monkeypatch.undo()` between legs:

| shared name | mutated to | both scans must go blind |
|---|---|---|
| `_SESSION_SELECT_METHOD` | `"not_the_select"` | production + test-tree `use()` legs |
| `_BOOTSTRAP_DDL_KEYWORDS` | `("DEFINE GALAXY",)` | production literal leg + test-tree DDL leg |
| `_is_connection_receiver` | `lambda node: False` | both `use()` legs |

The third leg carries an **extra assertion that the DDL leg does NOT go blind** when the
receiver predicate is blinded — because it is receiver-blind by design. Asserting that it
*could* be blinded there would have been a second false gate written into the fix for the
first; the docstring says so explicitly.

## 7. Item 5 (R5) — #151, and the message not just the docstring

`grep -rn "#151"` over the repo returned **zero** hits while #151 is open with the full
analysis. Fixed at `test_surreal_harness.py`:

- docstring now names **#151** as the durable address and states *why* the old citations
  fail (untracked scratch reports that repo law requires be deleted before any image build);
- **the failure message names #151 too** — that is the load-bearing half, since the message
  is what an engineer who trips the pin actually reads, and it now says they are looking at
  #151 being FIXED (the pin's own re-open trigger) rather than a regression.

## 8. Citation sweep — every site, individual verdict

`git grep -nE "audit-150|blindreader-150"` over tracked files, bare and anchor-free. No
wholesale classification.

**`loremaster/tests/test_surreal_harness.py` (writable — handled):**

| line | verdict |
|---|---|
| 39 `blindreader-150 F6` | **PROVENANCE, substance inline** — the sentence states the mechanism in full. Anchored by the new §51–66 block. Not rewritten. |
| 46 `blindreader-150 F1` | **PROVENANCE, substance inline.** Anchored. |
| 51–66 | **NEW — the durable anchor.** Records what these identifiers are, names #150/#151 and the wave's six commit SHAs, states none is a must-follow pointer. |
| 397 `F8` · 444–445 `audit-150 R5 / F10` · 536 `F1` · 652 `F2 / R4` · 659 `R1` · 724 `R1` · 752 `F2` · 838 `F6` · 1065 `F4 / R3` · 1123 `F3` · 1371 `R2` · 1406 `R2` | **PROVENANCE, substance inline — all twelve.** Each states its own finding in the surrounding prose; following the citation adds nothing. Anchored, not rewritten: 12 mechanical rewrites of non-load-bearing text is churn a reviewer must diff for no gain. |
| 612 | **LOAD-BEARING → FIXED.** The #151 known-bound pin. Now names #151 in docstring and message. |

**`loremaster/tests/test_retry_seam.py` (writable — handled):**

| line | verdict |
|---|---|
| 5632 (was) `audit-150 R2` | **LOAD-BEARING → FIXED.** It explains why a committed ruling rested on a false count; repointed at commit `fff1382`, which is durable and diffable. |

**`loremaster/tests/_surreal_harness.py` — OUTSIDE MY WRITABLE SET, FLAGGED NOT EDITED:**

| line | verdict |
|---|---|
| 27 `until audit-150` | **LOAD-BEARING, UNFIXED.** Cites a scratch report as the authority for a count correction. **Exact edit I would make:** `until audit-150` → `until fff1382`. |
| 108 `blindreader-150 F1` | **PROVENANCE, substance inline.** Would benefit from `(#151)` — this is the same defect #151 tracks. |
| 344 `audit-150 R5 / blindreader F10` | **PROVENANCE, substance inline.** No durable row exists. |
| 419 `blindreader-150 F2 / audit-150 R4` | **PROVENANCE, substance inline** (carries its own measurement, 3.812s vs designed 2.0s). |
| 454–455 `audit-150 R5 / blindreader-150 F10` | **PROVENANCE, substance inline.** |

**Also noticed, and raising rather than silently scoping out:** ~30 sites across
**production** files (`_txn.py`, `briefs.py`, `agents.py`, `scout.py`, `surreal.py`,
`findings.py`, `tasks.py`, `graph_surreal.py`, `snapshots.py`, `surreal_manifest.py`,
`memory/local.py`, `diff.py`) cite `blindreader F1/F2/F3` — the **earlier #102/#108 wave**,
not this one, but the identical non-durable-address pattern, and in production code. Out of
my writable set and out of this brief. **Your call whether that is worth a sweep of its
own** — it is 30 lines of provenance prose, all with substance stated inline, so I would
rate it LOW and not urgent.

## 9. DEVIATION — items 1–4 in one commit

The brief suggested three commits: (a) receiver-blind leg, (b) counts + mutation claims,
(c) citations. I shipped **two**, because (a) and (b) are not separable in
`test_retry_seam.py`:

- R2's numerals live *inside* the rationale block R1 rewrites;
- R4's mutation legs *assert R1's receiver-blind behaviour* (the third leg's extra assert).

Splitting would have produced an intermediate commit whose prose contradicts its own tests
— worse than one honest commit. **The commit message states its full scope explicitly**
rather than under-describing its diff, which is the same defect class this wave is closing.

## 10. Gates — every command with its passed-COUNT tail

```
cd loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -n auto
  -> 467 passed, 1 warning in 8.03s          (baseline 453; +14 accounted below)

cd <root> && ./scripts/typecheck.sh
  -> Found 55 errors in 5 files (checked 146 source files)
  -> grep for test_retry_seam|test_surreal_harness in the mypy output: NO HITS
     (floor unchanged; zero in the writable set)

cd <root> && uv run ruff check .
  -> All checks passed!

cd loremaster && uv run pytest tests/test_surreal_store.py tests/test_txn_contention.py -q -n auto
  -> 200 passed in 11.79s                    (live store, spike-surreal :18000 — never :18500)
```

**+14 tests, fully accounted:** 11 × `test_the_DDL_leg_is_RECEIVER_BLIND...` (parametrised
over 4 control + 7 measured-missed names) + `test_the_use_leg_still_reads_the_shared_receiver_predicate`
+ `test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING`
+ `test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here`.

**Zero production drift:**
```
git diff --stat 1837036..HEAD -- loremaster/loremaster/
  -> (empty)
```
`_txn.py` untouched; #151 left deliberately open per operator ruling.

⚠ **A near-miss worth recording:** one mutation run inherited a `cd loremaster` from a
prior command and exited **`no tests ran in 3.62s`** behind a `tail`. That is the exact
silent-green the brief names. Caught because I check for a passed-COUNT rather than an exit
code; every count above is from a tail I read.

## 11. Mutation proofs — wrong build → observed RED → restore → re-green

All applied to the **real tree** (committed + clean, so `git checkout --` restores
byte-exactly) with a `cp -a` **content** backup at `/tmp/gbf/BACKUP_test_retry_seam.py` and
an `md5sum -c` restore proof after every leg — never a naive `cp -a` repo copy (repo law
#140). No scratch copy was used, so no `.pth`/`__pycache__` provenance poisoning is
possible; nothing here ran outside the real checkout.

| # | wrong build | observed |
|---|---|---|
| **M1** | DDL leg reverted to **receiver-keyed** (i.e. HEAD) | **RED, and precisely.** 8 failed / 416 passed. The 7 measured names (`db`, `client`, `surreal`, `sdb`, `session`, `handle`, `store`) went RED; the **4 control names stayed GREEN** — so the pin discriminates rather than failing wholesale. The shared-predicate pin also fired. |
| **M2** | `_is_connection_receiver` reverted to the **asymmetric** predicate | **RED**, exactly 1 failed / 423 passed — `test_the_use_leg_still_reads_the_shared_receiver_predicate`. R1b's pin is real. |
| **M3** | test-tree DDL leg given a **private keyword tuple** | **RED** — `test_the_two_scans_SHARE_their_predicates_rather_than_cloning_them`. This leg **did not exist before** (item 4's false gate); it now catches real drift. |
| **M4** | test-tree `use()` leg given a **private receiver predicate** | **RED** — 2 failed: the sharing pin *and* the use()-leg pin. Also previously unmutated. |
| **M5** | *(end-to-end, below)* honest helper added to the tree | **RED** — 3 pins, named by `file:line`. |
| **M6** | *(auditor's, re-confirmed)* allowlist site-count | still fires — `test_every_allowance_still_holds_exactly_the_sites_it_was_granted` is in the 467. |

**Restore proof after every leg:** `md5sum -c /tmp/gbf/pre.md5 -> OK`.

### The before/after the brief asked for — the `db = AsyncSurreal(...)` construct

A real test module, `test_zzz_gbf_honest_helper.py`, holding a textbook #150-shaped helper
that opens a socket, signs in, hand-rolls the DDL and the select, and names its handle `db`.
Same file, same tree; only the gate's predicate varies.

```
===== BEFORE (receiver-keyed DDL leg, i.e. HEAD) =====
1 passed in 1.66s                      <-- the gate does not see it

===== AFTER (this wave's build) =====
E   test_zzz_gbf_honest_helper.py:12  .query(DEFINE NAMESPACE ...)
E   test_zzz_gbf_honest_helper.py:13  .query(DEFINE DATABASE ...)
FAILED ... test_no_test_module_outside_the_allowlist_bootstraps_a_session
FAILED ... test_the_receiver_blind_DDL_leg_costs_this_tree_NOTHING
FAILED ... test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here
3 failed in 3.32s                      <-- caught, named by file:line
```

Note the AFTER also demonstrates the two **new derived-count pins firing on a real new
site** — they are not decoration; they discriminate. Scratch file **deleted** (`ls` confirms
absent) and the tree restored byte-exact before committing.

## 12. Assertion-vs-message interrogation (the item-4 defect class, not reintroduced)

Every new assertion was read against its own failure message. All agree. One honest note:
the second assert in `test_the_literal_keyed_scan_would_be_MOSTLY_FALSE_POSITIVES_here`
(executed total == allowlist granted total) is **partially redundant** with the existing
gate + allowance pins. It is a cross-check, not a false gate — the message claims exactly
what the assertion performs — but I am flagging it rather than letting you discover a
redundancy I noticed and said nothing about.

## 13. Tool honesty

`lore_findings action=query` confirmed #150/#151 open and gave me #151's durable id. The
citation sweep and the fallout measurement used **grep and a hand-written AST script, not
lore** — declared per protocol: both are non-symbol textual-seam sweeps over prose in
string literals and comments, which is case (b) of the three grep-honest cases in
`CLAUDE.md`. The fallout measurement additionally had to run a *modified* predicate over
the tree, which no index can answer.

## 14. ESCALATIONS

1. **ESC-1 — ratify or revert the method-blind widening (§3).** Measured cost zero;
   rationale is `query_raw` in the installed SDK. One line to narrow back to
   `{query, execute}` if you want the ruling honoured literally.
2. **ESC-2 — the `use()`-leg residual bound (§4).** A DDL-less bootstrap on an
   oddly-named handle is still missed. Recommend pinning it with a named re-open trigger
   rather than closing it (closing means denying receiver-blind on a generic English verb).
   Not done — pin-vs-close is a design call.
3. **ESC-3 — `_surreal_harness.py:27` (§8).** Load-bearing citation of a scratch report,
   outside my writable set. Exact edit: `until audit-150` → `until fff1382`.
4. **ESC-4 — ~30 production-file `blindreader F*` citations (§8).** Same non-durable-address
   pattern from the earlier #102/#108 wave, in production code. LOW; your call.
5. **ESC-5 — commit granularity (§9).** Two commits, not three, with reasons. Disclosed in
   the commit message itself.

**Commits:** `2105c7e` (items 1–4) · `2a97a04` (item 5).

**There are 0 failing tests unrelated to our present scope.**
