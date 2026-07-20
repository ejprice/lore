# REPORT — harness-retry-fixwave (finding #150 residue)

brief-base v5 read

## SUMMARY BLOCK

- **state: done-with-deviations**
- **All 10 items done.** 11 wrong builds constructed, **11/11 caught**, each reddening a
  different non-overlapping set; every file restored byte-exact (§4).
- **deviation 1 (widened, disclosed):** item 10 named `drop_database` only. I also closed the
  IDENTICAL leak in `connect_admin`, where it is worse — the caller never receives the
  connection, so on a raise nothing in the program holds a reference that could close it. One
  hunk, revertable. §3.10.
- **deviation 2 (ordering):** I applied the behavioural fixes and measured them with probes
  BEFORE writing their pins. The mutation proofs in §4 are the RED receipts, run after the fact.
- **deviation 3 (commit split):** split by FILE (behavioural · instruments · prose-only), not the
  brief's suggested behavioural/instruments/prose, because those three concerns are textually
  interleaved inside single docstrings. §6.
- **decisions-needed: 3** — all in §7. (a) the two PRODUCTION `_txn.py` defects both graders
  found are still open and I did not touch them; I have PINNED the bound instead, with a named
  re-open trigger. (b) `REPORT-harness-retry-builder.md` §3.5 claims a consumer sweep over "21
  files" when there are 35 — its conclusion survives my re-measurement, its coverage did not.
  (c) the two doc/receipt residuals (cold R6/R7, blindreader F9) remain untouched, outside my
  writable set.
- **zero production drift:** `git diff 0734d78..HEAD -- loremaster/loremaster/` = **0 bytes** (§5).
- **gates:** 446 passed (baseline 420, +26, all accounted §2) · live store 200 passed · mypy
  **exactly 55 in 5 files**, zero in my three · ruff clean. Tails in §2.
- **commits:** `20e7635` · `4659056` · `fff1382`.
- **receipt pointers:** gates §2 · per-item disposition §3 · mutation proofs §4 · the two
  "old instrument was blind" demos §4.2 · count derivation §3.9 · drift + bare sweep §5 ·
  escalations §7.

---

## 1. Per-item disposition

| # | item | disposition | proof |
|---|---|---|---|
| 1 | restore exhaustion attribution | **DONE** — `label`+`url` are now REQUIRED params of the helper | §3.1, WB-C |
| 2 | compose ONE budget across `drop_database`'s two calls | **DONE** — measured 3.585s → 2.039s | §3.2, WB-B/WB-J |
| 3 | pin the COMPOSED budget at `connect_admin` | **DONE** — the auditor's 17/17 wrong build now RED | §3.3, WB-A |
| 4 | import-isolation pin walks only `tree.body` | **DONE** — `ast.walk`, scope-skipping, + 5 hostile controls + 1 negative control | §3.4, WB-E1/E2, demo 1 |
| 5 | 3-name deny-list → ALLOWLIST | **DONE** — allowlist chosen, not the prose-softening fallback | §3.5, WB-F, demo 2 |
| 6 | prose contradicted by `call_until_recovered` | **DONE** — scoped to "no CONFLICT-RETRY policy" at all 3 sites | §3.6 |
| 7 | sharing proof reaches 2 of 5 operations | **DONE** — 5 probes, reach is a CHECKED variable | §3.7, WB-G |
| 8 | pin teardown's operation ORDER | **DONE** | §3.8, WB-H |
| 9 | a FALSE COUNT at 4 sites | **DONE** — both counts re-derived by me; 4/4 sites fixed; now PINNED | §3.9, WB-I |
| 10 | `drop_database` leaks its connection | **DONE + widened to `connect_admin`** | §3.10, WB-D |

**I did not refuse any item.** Item 5 offered a fallback ("if you judge an allowlist infeasible,
soften the prose instead") — the allowlist is feasible and is what shipped; the prose was
corrected as well, so the message no longer overclaims either way.

## 2. Gates — every command, with its passed-COUNT tail

```
$ cd loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
446 passed, 1 warning in 13.50s

$ uv run pytest tests/test_txn_contention.py tests/test_surreal_store.py -q -n auto
200 passed in 12.86s

$ ./scripts/typecheck.sh
Found 55 errors in 5 files (checked 146 source files)
typecheck: loremaster FAILED

$ ./scripts/typecheck.sh 2>&1 | grep -E '_surreal_harness|test_retry_seam'
NONE

$ uv run ruff check .
All checks passed!
```

**+26 accounted, all in `test_surreal_harness.py` (17 → 43; `test_retry_seam.py` unchanged at 403):**

| class | Δ | what |
|---|---|---|
| `TestDropDatabaseRetriesRetryableConflict` | 0 | order assertion added to an existing test (item 8) |
| `TestTheAdminSocketIsClosedOnEveryFailurePath` | **+4** | 3 failure paths + 1 success control (item 10) |
| `TestTheSeamsExhaustionRecordIsAttributable` | **+3** | 2 parametrised teardown labels + 1 KNOWN-BOUND pin (item 1) |
| `TestSeveralOperationsUnderOneCallerShareONEBudget` | **+3** | connect_admin · teardown · read-not-copied (items 2, 3) |
| `TestTheHarnessRetryPolicyIsTheSeamsPolicy` | **+9** | −3 (2 per-path ceiling + 1 both-paths deadline) +12 (reach pin + 5 ceiling + 5 deadline, parametrised over `_OPERATION_PROBES`) (item 7) |
| `TestTheHarnessDeclaresNoRetryPolicyOfItsOwn` | **+7** | allowlist +1, import-scan controls +5 hostile +1 negative, docstring-count pin +1 (items 4, 5, 9) |

**Store targeting proven, not assumed:** `systemctl --user is-active spike-surreal.service` →
`active`; `LORE_TEST_SURREAL_URL` **unset** ⇒ `DEFAULT_URL = ws://127.0.0.1:18000/rpc`.
Production **:18500 was never contacted**.

### 2.1 Stability — a single green run clears nothing here

Two of the new pins are timing-shaped (they make an operation spend wall clock to prove budget
composition). Per repo law:

```
20 consecutive serial runs of tests/test_surreal_harness.py : 43 passed, 20/20, 2.47s–2.53s
 5 consecutive `-n auto` runs of the scoped pair            : 446 passed, 5/5
```

The composition pins are **deterministic by construction, not merely lucky**: the budget-burning
operation conflicts 4 times (asserted `< ` the seam's attempt floor of 5, so it can never give
up) at 0.06s each, spending 0.30s against a 0.20s budget. `asyncio.sleep` never returns EARLY,
so the overspend is guaranteed. Both premises are asserted inside the pin
(`_assert_the_two_bounds_differ`) rather than left implicit.

### 2.2 Consumer regression — A/B measured, not reasoned

The harness has 35 importers. I ran the **33 unchanged consumers** (excluding my two edited test
files) against HEAD and against the pre-wave harness swapped in from `0734d78`:

| tree | result |
|---|---|
| HEAD (`fff1382`) | `61 failed, 2698 passed, 166 errors in 151.47s` |
| baseline harness (`0734d78`) | `61 failed, 2698 passed, 166 errors in 153.14s` |

**Identical on all three counters**, and identical to the number the cold auditor recorded for
the previous wave. Zero consumer regressions; the packet-03 RED floor did not grow.

## 3. What changed, and why

### 3.1 Item 1 — attribution (`_surreal_harness.py:262-300`)

`label: str` and `url: str` are now **required** keyword parameters of
`_run_under_store_retry_seam` — not optional, because there is no call site here that should be
anonymous. The two labels are module constants following the store seams' own
`_SEAM_REJECTION_EVENTS` convention: `harness.teardown.select_database`,
`harness.teardown.remove_database`.

The brief's premise was correct and the previous builder's adjudication was wrong: `label` and
`url` are ARGUMENTS of `retry_on_conflict` (`_txn.py:804-810`), so this is entirely a call-site
change. **Measured, with a negative control** (`/tmp/fw150/probe_attribution.py`):

```
=== FIXED: label passed ===
  {'attempts': 64, 'label': 'harness.teardown.remove_database',
   'url': 'ws://127.0.0.1:18000/rpc',
   'engine_error': 'Transaction conflict: Resource busy. This transaction can be retried'}
  engine text in log?   True

=== CONTROL: label omitted (pre-fix shape), everything else identical ===
  {'attempts': 64, 'label': '<ABSENT>', 'url': '<ABSENT>', 'engine_error': '<ABSENT>'}
  engine text in log?   False
```

The raised exception still carries `__cause__: None` — that is the `_txn.py` side and is out of
scope (§7a). What the raised message PROMISES ("see the server log for the full engine detail")
is now true on this path.

### 3.2 Item 2 — one composed budget across teardown's two operations

`drop_database` now mirrors `bootstrap_session`'s `_remaining_budget()` closure. The budget is
**read from the seam at call time** via a new `_seam_default_deadline_seconds()` — never frozen
at import, never copied.

**A/B measured** (`/tmp/fw150/probe_budget.py`; both legs drive the identical fake, first
operation deliberately burning 1.5s of a 2.0s budget):

```
UNCOMPOSED  TOTAL 3.585s   use_calls=33  REMOVE_calls=44  (REMOVE got a FRESH 2.0s)
COMPOSED    TOTAL 2.039s   use_calls=32  REMOVE_calls=15  (REMOVE got what was LEFT)
delta = 1.547s;  composed within the designed 2.0s budget: True
```

That reproduces the blindreader's 3.812s in kind and shows the fix landing inside the seam's
designed bound.

### 3.3 Item 3 — the composed budget is now PINNED at `connect_admin`

`TestSeveralOperationsUnderOneCallerShareONEBudget::test_connect_admins_three_statements_share_one_budget`.
The discriminator is arithmetic and is stated in the fixture constants rather than left for a
reader to reconstruct.

I did **not** use the auditor's literal suggestion (zero the deadline, expect FLOOR on the third
statement) — **it does not discriminate.** Under a zeroed deadline an UNCOMPOSED build gives each
statement a fresh 0.0s, so each also lands on the floor; both builds produce the same number.
The property only becomes observable when an EARLIER operation actually consumes the budget. So:
statement 1 conflicts 4 times (below the floor, so it recovers) while overspending a shortened
0.20s budget; statement 3 then lands on the FLOOR under a composing caller and would run to the
CEILING under one handing out fresh budgets. **The auditor's exact wrong build is now RED**
(WB-A), where it previously passed 17/17.

The pin also asserts the three statements really ran, in order — otherwise a low count could be
low for a reason that has nothing to do with budgets.

### 3.4 Item 4 — the import scan

`_module_level_imported_modules(source)` now recurses everywhere except into
`FunctionDef`/`AsyncFunctionDef`/`ClassDef` bodies. Five hostile sources are **positive
controls** (`try/except ImportError`, module-level `if`, `with`, `for`, `try/finally`) and one
**negative control** proves the scan does not simply flag every import — without which a scan
that returned everything would pass all five. I also tightened
`not name.startswith("loremaster.index.records")` to exact equality (the blindreader's
`loremaster.index.records_anything` note).

### 3.5 Item 5 — allowlist, not deny-list

`_ALLOWED_MODULE_LEVEL_NAMES` is the exact set of 35 module-level bindings (assignments,
functions, classes) the harness may declare, AST-derived. The three named legs are kept as
defence in depth for the specific message they can give, and their docstring now says so
explicitly instead of claiming to be the general guard. **A reintroduced
`_TEARDOWN_MAX_ATTEMPTS` passed the old deny-list 3/3 and fails the allowlist** (§4.2 demo 2).

### 3.6 Item 6 — the `call_until_recovered` contradiction

Fixed at **three** sites, not the two named: `_surreal_harness.py:35-39` (module docstring),
`test_surreal_harness.py:17` (module docstring), and `_surreal_harness.py:263` (the helper's own
docstring, which carried the same absolute "no attempt budget"). The code is right and unchanged;
the claim now reads "no CONFLICT-RETRY policy … no conflict budget", with `call_until_recovered`
named as the legitimate counter-example and the reason it must not route through `_txn`.

### 3.7 Item 7 — reach as a CHECKED variable

`_OPERATION_PROBES` holds one constant-tied probe per operation the harness puts under the seam
(all 5, both `use()` calls included). `test_every_operation_under_the_seam_has_a_constant_tied_probe`
**discovers** the operations by driving both functions against the fake and normalising
`fake.operations` — deliberately not a lookup against known statements, so a NEW statement
produces a NEW key and reddens the pin rather than falling into a default bucket. The ceiling and
deadline pins are parametrised over that dict, each with its positive control.

WB-G confirms this closed a real hole: a private 2-attempt loop on teardown's `use()` — the
operation this repo's own probe called "the call that actually loses the bootstrap race" —
reddens the two `drop_database:use` probes. Under the previous 2-operation proof it would have
been invisible.

### 3.8 Item 8 — teardown order

`assert fake.operations == [use, use, REMOVE]`. WB-H (REMOVE issued before `use()`) is now RED.

### 3.9 Item 9 — the two counts, DERIVED BY ME

I did not copy the lead's numbers. AST derivation, run over `loremaster/tests/**/*.py` excluding
the harness itself — **importer** = any `import _surreal_harness` / `from _surreal_harness import`
anywhere in the file (`ast.walk`, so a conditional or in-function import counts, since either
still breaks on a bad module); **caller** = any `ast.Call` whose func is `connect_admin` by name
or attribute:

```
IMPORTERS: 35
CONNECT_ADMIN CALLERS: 21
callers that are not importers: []   (⇒ callers ⊂ importers, strictly)
```

Both of the lead's numbers reproduce exactly. **They are two real counts of two different
populations** and the fixed prose states them distinctly at all four sites
(`_surreal_harness.py:24-31`, `test_surreal_harness.py` docstring + failure message,
`test_retry_seam.py:5031`).

Two structural fixes so this cannot recur:
- The failure message in the import-isolation pin now **interpolates the live derived count**
  (`len(importers)`) instead of stating a literal — the site that previously told a reader the
  wrong number at the exact moment the gate fired can no longer carry a number at all.
- `test_the_harnesss_docstring_counts_are_the_DERIVED_counts` parses both numbers out of the
  harness docstring and asserts them against the AST derivation, plus asserts the two populations
  are genuinely different sets. WB-I proves it fires.

### 3.10 Item 10 — socket hygiene (**and the disclosed widening**)

`drop_database` wraps both operations in `try/finally`. **Pre-existing**: byte-identical in the
pre-#150 code, so not a regression from either wave — but the leak window widened from ~0.1s to
the seam's whole budget once these operations started retrying, on a path that runs for every
`[real]` test under `-n auto`. Fixed opportunistically inside a function I was already rewriting,
exactly as the brief framed it.

**Widened beyond the item, deliberately:** `connect_admin` carries the identical leak one
function over (blindreader F10 names `:284-291` alongside the teardown site), and there it is
strictly worse — the caller never receives the connection, so on a raise there is no other object
in the program that could close it. I judged leaving a known identical defect one function over
to be the can-kick the repo law names, and it is inside the writable set. It is **one hunk in
`connect_admin`, revertable on its own**. Guarded by a control pin
(`test_connect_admin_still_hands_back_an_OPEN_connection_on_success`) so a build that closed
unconditionally — handing every fixture a dead socket — cannot pass.

## 4. Mutation proofs

### 4.1 Eleven wrong builds, eleven caught

Driver: `/tmp/fw150/mutate.py`. Each leg applies ONE wrong build to the committed tree, runs only
the pins that should catch it, restores via `git checkout --`, and re-verifies md5.

```
POSITIVE CONTROL (correct build): 43 passed in 2.56s

RED ✅  WB-A  connect_admin inlines 3 independent budgets (audit R1)      -> 1 failed, 2 passed
RED ✅  WB-B  drop_database passes no deadline (uncomposed, F2)           -> 1 failed, 2 passed
RED ✅  WB-C  seam call site omits label/url (F1)                         -> 2 failed, 1 passed
RED ✅  WB-D  drop_database closes only on success (F10)                  -> 2 failed, 2 passed
RED ✅  WB-E1 import scan walks tree.body only (F3)                       -> 5 failed, 7 passed
RED ✅  WB-E2 harness gains a try-wrapped module-level _txn import (F3)   -> 1 failed, 11 passed
RED ✅  WB-F  harness declares _TEARDOWN_MAX_ATTEMPTS (F4)                -> 1 failed, 11 passed
RED ✅  WB-G  teardown use() runs a PRIVATE 2-attempt loop (F6)           -> 2 failed, 11 passed
RED ✅  WB-H  teardown issues REMOVE before use() (F8)                    -> 1 failed, 2 passed
RED ✅  WB-I  docstring says 21 importers again (audit R2)                -> 1 failed, 11 passed
RED ✅  WB-J  drop_database hardcodes its composed budget                 -> 2 failed, 1 passed

all files restored byte-exact: True
```

Each reddens a **different, non-overlapping** set — that is the "differently-broken build
rejected for a *different* reason" control, not one blunt instrument firing on everything. WB-J
is mine, not the brief's: it separates "composes" from "composes a number it hardcoded", which
is the routing-is-not-sharing failure one level down from the one #150 removed.

### 4.2 The other half — were the OLD instruments actually blind?

A pin going RED proves it fires. It does **not** prove it was needed. Driver
`/tmp/fw150/blind.py` re-applies two wrong builds with the PRE-FIX instrument in place:

```
DEMO 1  try-wrapped module-level `_txn` import
   judged by the OLD (tree.body) scan : 1 passed      <- the hole, live
   judged by the NEW (walk)      scan : 1 failed

DEMO 2  harness declares `_TEARDOWN_MAX_ATTEMPTS = 5`
   judged by the OLD 3-name deny-list : 3 passed      <- the hole, live
   judged by the NEW allowlist        : 1 failed

restored byte-exact: True
```

### 4.3 Tree provenance

No scratch copy was made (repo law #140). All mutations ran in the **real, committed** checkout
and were restored by `git checkout --` with md5 verification after every leg — the "always sound"
alternative the law names. Receipt:

```
loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
$ git status --short     # after all 13 mutation legs
?? REPORT-audit-150-cold.md
?? REPORT-blindreader-150.md
?? REPORT-harness-retry-builder.md
?? scratchpad/
```

### 4.4 Assertion-vs-message interrogation

I re-read every new and changed assertion against its own failure message (the brief's own item 5
generalised), by hand, one at a time. **Result: no gap found.** Specifically:

- the reach pin asserts set EQUALITY and its message enumerates both directions of the
  difference (a subset assertion would have admitted a probe naming a dead operation);
- the composition pins' floor-vs-ceiling reasoning is stated in the message and is exactly what
  the assertion checks;
- the allowlist pin's message reports `added` and `removed` separately, which is what it asserts;
- the retired-name legs' docstring now says they are defence in depth, so they no longer promise
  the general property the allowlist carries;
- the KNOWN-BOUND pin's message names the condition it actually tests (`hasattr(record, "label")`).

The one weakness I will name rather than hide: the composition pins' messages say "`{ceiling}`
means it was handed a FRESH budget", while the assertion is `observed == floor`. An observed
value that is neither floor nor ceiling would fail with a message that overstates what was
inferred. I judged this acceptable — the message's load-bearing claim (`observed != floor` ⇒ not
composing) is exactly what the assertion checks — but it is the closest thing to a gap in this
diff and you should know it is there.

## 5. Production drift and the bare sweep

```
$ git diff --stat 0734d78..HEAD -- loremaster/loremaster/
$ git diff 0734d78..HEAD -- loremaster/loremaster/ | wc -c
0

$ git diff --stat 0734d78..HEAD
 loremaster/tests/_surreal_harness.py     | 144 ++++-
 loremaster/tests/test_retry_seam.py      |   7 +-
 loremaster/tests/test_surreal_harness.py | 972 +++++++++++++++++++++++++++---
 3 files changed, 1006 insertions(+), 117 deletions(-)
```

**Zero production bytes.** No file outside the writable set was modified; `_txn.py` was never
touched, including during the mutation legs (every wrong build mutated the two test-tree files
only).

**Bare, anchor-free sweep** for the retired claim (`21 test files` / `21 importers` / `21 files`),
per-hit verdicts, no wholesale classification:

| hit | verdict |
|---|---|
| `_surreal_harness.py:26` | **CORRECT** — my new prose, 21 correctly labelled as the `connect_admin`-caller population |
| `test_surreal_harness.py:1338` | **CORRECT** — the count-pin docstring quoting the false claim as history |
| `REPORT-audit-150-cold.md:17, :180, :229` | **CORRECT** — the report that identified the count as false |
| `REPORT-blindreader-150.md:34, :177` | **STALE** — a grader's dated report; inherited the false count from the code it read. Untracked, outside my writable set. Informational. |
| `REPORT-harness-retry-builder.md:17, :79` | **STALE** — same shape, same disposition |
| `REPORT-harness-retry-builder.md:139-140` | **STALE AND LOAD-BEARING** → §7b. Its consumer sweep claims coverage of "the 21 files that import the harness"; there are 35. |

Zero live-code hits carry the false claim.

## 6. Commits

| sha | scope |
|---|---|
| `20e7635` | `_surreal_harness.py` — items 1, 2, 10 + the prose those changes carry (6, 9) |
| `4659056` | `test_surreal_harness.py` — items 3, 4, 5, 7, 8 + the count pins (9) |
| `fff1382` | `test_retry_seam.py` — prose only (items 6, 9 at the retired 7e block) |

**Deviation from the suggested split, stated plainly:** the brief suggested
behavioural / instruments / prose. Those three concerns are textually interleaved — the
behavioural change to `_run_under_store_retry_seam` and the prose correction to its docstring are
lines apart in the same hunk — so a clean three-way split by concern was not achievable without
rewriting history hunk by hunk. I split by FILE instead, which lands close to the same boundary:
commit 1 is behavioural, commit 2 is instruments, commit 3 is prose-only.

**Commit 1 is independently green, measured** — the fixed harness against the OLD (pre-wave)
test files, which is the tree an `HEAD~2` checkout produces:

```
$ git checkout 20e7635 -- loremaster/tests/test_surreal_harness.py loremaster/tests/test_retry_seam.py
$ uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q
420 passed, 1 warning in 11.22s          # the pre-wave baseline, exactly
```

## 7. ESCALATIONS

**(a) The two PRODUCTION `_txn.py` defects are still open — I pinned the bound instead of
closing it.** Per the brief I did not touch `_txn.py`. `bootstrap_session` passes no `label`, so
`connect_admin`'s exhaustion record still carries an attempt count and nothing else — and
`retry_on_conflict`'s docstring (`_txn.py:857-859`) justifies that omission by naming
`bootstrap_session` as having "its own attribution", which is FALSE: it logs nothing at all.
Rather than leave that inherited silently, I shipped
`test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound`, which ASSERTS the hole,
names it as a known bound with the finding, and carries an explicit **re-open trigger**: "the day
`bootstrap_session` passes a label, delete this pin and extend the attribution assertions".
It goes RED the moment someone closes the hole, which is the point. **If you would rather this
were fixed in `_txn.py` than pinned, say so and the pin comes out with the fix.**

**(b) The first builder's consumer sweep was undersized, and its own report says so once you know
the real count.** `REPORT-harness-retry-builder.md` §3.5 is titled "the 21 files that import the
harness" and B3's non-regression argument rests on having "grepped every `_surreal_harness`
importer (21 files)". There are **35**. So the caller-visible exception-type change
(`QueryError` → `TxnContentionExhaustedError`) was argued from a sweep covering 21 of 35 files.
**The conclusion survives** — the cold auditor re-ran 33 files and got identical counts, and I
independently re-ran the same 33 at HEAD and at the pre-wave harness and got identical counts
again (§2.2) — but the *coverage* claim in that committed report is wrong, and it is the second
time this one bad number has propagated into an argument. That report is untracked and outside my
writable set. **Your call whether it gets a correction stamp.**

**(c) Two doc residuals untouched, outside my writable set** — I agree with both graders'
recommendation of a superseded-by-#150 stamp rather than a rewrite:
- `docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:414` (cold R6 / blindreader
  F9) describes `_MAX_DROP_DATABASE_ATTEMPTS = 5` and the deleted linear backoff as LIVE. All
  four claims are now false.
- `docs/plans/v2/INDEX.md:413` (cold R7) reads "eleven hand-rolled copies deleted" for the #102
  chain; #150 deleted a twelfth.

**(d) Not a decision, but flagging per scope law — one thing I noticed and did NOT act on.**
`signin()` is still a bare unretried `await` in both `connect_admin` and `drop_database`
(cold R8). I agree with the auditor that this is CORRECT — auth cannot produce a write-write
conflict, so the seam's classifier would decline it and wrapping would be routing without
purpose. Raising it only because it is a bare await in the two functions this wave hardened, and
because it is now the ONLY engine call in either function not under the seam. It is consequently
also the one operation the new reach pin does not cover — `_FakeConnection.signin` records
nothing into `operations`, by the fake's pre-existing design.

---

There are **55 mypy errors across 5 files unrelated to our present scope** (the packet-03 comms
contract: `test_comms_tool.py` 44, `_message_fakes.py` 13, `test_comms_promise_registry.py` 7,
`test_message_ledger.py` 4, `test_surreal_schema.py` 1 — the count did not move), and per the
INDEX ~180 expected-RED tests from that contract which I did not run. Do you want to examine them
more closely?
