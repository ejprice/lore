# REPORT-adversary-151

brief-base v5 read

state: **done — VERDICT: CONTRACT INSUFFICIENT (1 blocker + 5 missing pins)**

deviations:
- My FIRST mutation harness was poisoned (`cp -a` of a scratch copy → `tests` resolved to
  the original tree). Caught by my own positive control; harness rebuilt to mutate in
  place. All results below are from the rebuilt harness. §0.
- Built my own independent reference fix in `/tmp/adv151-scratch` (provenance asserted).
  No file in the repo was modified; no git state touched.

decisions-needed:
- **B1 (BLOCKER) — the url invariant is quantified over ONE caller, and it is a TEST file.**
  All 11 production owners can hardcode the url; contract passes 489/0 AND the full
  6079-test suite shows a ZERO failure delta. Needs a pin before a builder starts.
- F1/F2 from the author's report (scout.py:171; `_surreal_harness.py` writable) are REAL —
  I reproduce both. Still operator-owned.

receipt pointers: provenance §0 · quantifier table §2 · wrong builds §3 · missing pins §4 ·
author-claim verification §5 · fixture discrimination §6 · P6b §7 · residuals §8

---

## SUMMARY

**P1 headline — FIVE wrong builds survive the contract.** One is a blocker: eleven
production connection owners hardcoding the RPC url instead of threading their own passes
the contract 489/0 *and* adds zero failures across the entire 6079-test suite.

**The author's own claims are honest.** Satisfiability (489/0), every mutation proof
(M1/M2/M4/M5/M6), both gate baselines, the 20/20 composition stability, and the 17-failure
RED all reproduce independently. The disclosed weaknesses (§1's "red for the wrong reason"
pins, §6's un-pinnable docstring, F1/F2) are accurate and were disclosed unprompted. This
is a strong contract with one structural hole its author could not see, because the hole is
in the *frame*: the contract quantifies beautifully over the three statements and not at all
over the eleven callers.

---

## 0. Provenance (P0)

```
scratch tree : /tmp/adv151-scratch          (via ./scripts/scratch_copy.sh)
FINAL PROVENANCE: loremaster.__file__ = /tmp/adv151-scratch/loremaster/loremaster/__init__.py
reference build restored + re-verified: 489 passed, 1 warning in 16.63s
```

### ⚠ My own P0 control failure, caught and reported

My first harness did `cp -a /tmp/adv151-scratch /tmp/adv151-work`. `loremaster.__file__`
resolved *correctly* to the work tree — so the obvious provenance check PASSED — but the
**test packages** did not:

```
E   ImportError: cannot import name 'test_surreal_harness' from 'tests'
    (/tmp/adv151-scratch/lorescribe/tests/__init__.py)
```

Under that harness, mutation A "passed 489/0" and **so did a control I knew to be broken**.
Only the control exposed it. Two lessons worth recording: (1) `#140`'s poison applies to a
copy-of-a-scratch-copy, not just a copy of the repo; (2) **asserting `loremaster.__file__`
is necessary and NOT sufficient — the test tree has its own provenance.** Harness rebuilt to
restore-from-tar and mutate the provenance-asserted tree in place. Every result below was
re-run on the rebuilt harness, and the restore leg reproduces 489/0 before each mutation.

---

## 1. The P1 headline

| # | Wrong build | Contract result | Verdict |
|---|---|---|---|
| **A** | **All 11 production owners hardcode `url="ws://127.0.0.1:8000/rpc"`** | **489 passed / 0 failed** | **BLOCKER** |
| **C** | Label values rotated — each statement reports as a *different* statement | **489 / 0** | missing pin |
| **D3** | New unlabelled driver call inside an *exempt* function | **489 / 0** | missing pin |
| **E** | New unlabelled caller via `retry_on_conflict as _retry` | **489 / 0** | missing pin (bound not pinned) |
| control | Same url defect one level down (inside `bootstrap_session`) | 3 failed | probe SEES url defects |
| control | Same unlabelled call in a NON-exempt function | 1 failed | gate SEES unlabelled calls |

---

## 2. QUANTIFIER TABLE (P1b) — every invariant, ∀-over-inputs vs guarded

| # | Invariant | ∀ or GUARDED | Receipt |
|---|---|---|---|
| I1 | Each bootstrap statement's exhaustion record carries a label | **∀ over 3 statements** | M5: dropping the `use` label fails *exactly* the three `[use]` params (§6) |
| I2 | The three labels are pairwise distinct | **∀** (derived from observation) | M1: 1 failed — the distinctness pin only |
| I3 | **The label NAMES the statement it attributes** | **NOT PINNED** | **Wrong build C: 489/0.** Assertion compares the record to the constant under test — self-referential |
| I4 | **The record carries the CALLER's url** | **GUARDED — by CALLER, quantified over exactly ONE, and it is a test file** | **Wrong build A: 489/0 contract, 0 delta over 6079 tests.** Control: 3 failed |
| I5 | The record carries the engine's own text | **∀ over 3 statements** | M2: 13 failed (3 new + 10 pre-existing seam pins) |
| I6 | `url` is required and keyword-only | **∀** (signature-level) | RED today; M6: 1 failed |
| I7 | Every `retry_on_conflict` call passes `label=` | **GUARDED twice**: (a) by the driver's NAME; (b) allowlist keys on the FUNCTION, not the call | **E: 489/0** (alias) · **D3: 489/0** (exempt fn). Controls: 1 failed each |
| I8 | **Every `retry_on_conflict` call passes `url=`** | **NOT PINNED AT ALL** — the gate checks only `label=` | R1 demands the full triple; nothing enforces the url leg |
| I9 | `bootstrap_session` propagates every failure UNWRAPPED | **∀ over 4 fates**, exact type | M4 (SCOUTKILL): 31 failed, incl. the e2e scout ladder pin |
| I10 | The three statements share ONE composed budget | **∀**, strictly decreasing | W5: 2 failed (two independent pins); 20/20 stable |
| I11 | The scan's reach is non-vacuous | **∀** (floor ≥ 8) | 8 sites confirmed; sibling packages clean |
| I12 | Exemptions are non-stale | **∀** | pinned by `test_every_exemption_matches_a_REAL_call_site` |
| I13 | The docstring no longer claims false attribution | **not mechanical** — author discloses (W8) | honest; §5 |

**Six of thirteen are clean ∀-over-inputs with door-build receipts. I4 is the blocker; I3,
I7, I8 are the missing pins.**

---

## 3. Wrong-build record (commands + real output)

Harness: restore reference from tar → mutate in place → `uv run pytest
tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly`.
Sanity leg before each: `489 passed`.

### A — the BLOCKER: production owners hardcode the url

Mutation: in all ten class owners `url=self._url` → `url="ws://127.0.0.1:8000/rpc"`, plus
`scout.py`'s `_open_command_connection`. `bootstrap_session`'s own threading left INTACT.

```
MUTATION A applied: 11 owners hardcode the url
=== A: all 11 PRODUCTION owners HARDCODE the url ===
489 passed, 1 warning in 17.44s
```

**Positive control** (the same defect one level down, so I know the probe can see it):

```
CONTROL applied: bootstrap_session ignores its url parameter
      3 FAILED …TestTheBootstrapPathsExhaustionIsAttributable::test_each_bootstrap_statement_carries_the_CALLERS_url
3 failed, 486 passed
```

**Full-suite decisive leg** — failure sets diffed, reference vs mutation A:

```
MUTA failures: 309
REF  failures: 309
=== CAUSED BY MUTATION A (in MUTA, not in REF) ===
=== end ===          <-- EMPTY
```

(309 is the known packet-03 comms RED baseline, identical on both sides, so the comparison
is valid.) **Nothing anywhere in this repository can tell the two builds apart.**

**Why the contract cannot see it:** the only url-discriminating pin drives
`_surreal_harness.connect_admin` — the ONE test-tree call site, and it is in the builder's
writable set under R5. The eleven production owners are the real population and carry zero
pins. `test_every_connection_owner_holds_the_ONE_shared_bootstrap` (`:5486`) checks helper
**identity** only. The R3 gate keys on `retry_on_conflict` and never looks at a
`bootstrap_session` call site.

This is **caller-population monoculture** — the `name="project"` class one level up. The
author correctly broke *value* monoculture at the driver (`_DISTINCT_BOOTSTRAP_URL`, a
TEST-NET-2 address appearing nowhere else — genuinely good) and then quantified the
invariant over a caller set of size one.

**Operational harm:** production connects to `:18500`. A hardcoded `:8000` in the exhaustion
record is a *plausible-looking wrong server name* — worse than the absent url #151 set out
to fix, because it looks complete.

### C — the label names the WRONG statement

`_BOOTSTRAP_DEFINE_NAMESPACE_LABEL` holds `"…define_database.rejected"` and vice-versa.
Labels stay pairwise distinct; every per-statement pin passes.

```
=== C: label values name the WRONG statement ===
489 passed, 1 warning in 17.03s
```

The pin's own failure message says *"An operator who greps the exhaustion record must land on
WHICH of the three statements died."* The assertion performs
`record.label == getattr(txn_module, <constant name>)` — comparing the observation to the
constant that is itself under test. **A message promising more than the assertion performs:
the exact false-gate class CLAUDE.md records.**

### D3 — the allowlist exempts a FUNCTION, not a call site

An unreachable `await retry_on_conflict(lambda: None)` added inside `execute_transaction`
(zero runtime effect, so only the gate could object):

```
=== D3: UNLABELLED call inside exempt fn, zero runtime effect ===
489 passed, 1 warning in 17.00s
```

**Control** — the identical call inside `bootstrap_session` (not exempt):

```
=== D3-CONTROL: same call in a NON-exempt function ===
      1 FAILED …TestEveryCallIntoTheRetryDriverIsAttributable::test_every_call_into_the_driver_passes_a_label
1 failed, 488 passed
```

`_ATTRIBUTED_BY_ANOTHER_MECHANISM` keys on `(module, enclosing_function)`. Its evidence
(`_log_rollback` runs on the way out) is true of the *original* call and says nothing about
a new one. One evidence-backed exemption silently pre-approves every call later written in
that body.

### E — an ordinary import alias evades the gate

```
MUTATION E: new unlabelled driver call via `retry_on_conflict as _retry`
=== E: new UNLABELLED caller via an ALIASED IMPORT ===
489 passed, 1 warning in 17.01s
```

Measured reach of `_retry_driver_call_sites_in` across twelve call shapes:

| shape | seen? |
|---|---|
| bare call · attribute call · inside a lambda · inside a comprehension · class method · module level | **YES** (6/6) |
| aliased import · variable holding the fn · `getattr` · `functools.partial` · dict dispatch · decorator | **NO** (6/6) |

The author documented four of the six misses. Two are undocumented (dict dispatch,
decorator) — both exotic, low concern. **My disagreement is with the threat-model
justification, not the bound:** the scanner's docstring says an aliased call "would have to
be written deliberately, by an author who knew this gate existed." `from ._txn import
retry_on_conflict as _retry` is ordinary Python — routinely written to dodge a name clash,
by exactly the honest engineer the gate is declared to be for. The bound is real and
acceptable; the *reason given for accepting it* is too generous, and per CLAUDE.md's
"WHEN YOU CANNOT CLOSE A HOLE, PIN IT" the bound belongs in a test with a re-open trigger,
not in a docstring.

---

## 4. MISSING PINS — what the author must go write

**MP1 (BLOCKER) — `test_each_production_owner_logs_ITS_OWN_url_on_bootstrap_exhaustion`.**
Drive at least **two** real production owners (e.g. `SurrealStore` and `BriefLedger`)
constructed at **two DIFFERENT urls** to bootstrap exhaustion, and assert each record's
`url` equals *that owner's* url. Two owners at two urls is the load-bearing part: one owner
cannot distinguish "threaded" from "hardcoded to the value this fixture happens to use", and
a shared module global passes any single-url pin. *Catches:* wrong build A — and, more
generally, the entire production caller population, which the contract currently does not
reach at all.

**MP2 — `test_every_bootstrap_session_call_passes_a_url`.** Extend the deny-by-default AST
gate (or add a sibling keyed on `bootstrap_session`) requiring `url=` at every
`bootstrap_session` call site, with the same evidence-backed allowlist discipline. *Catches:*
R1's url leg, which invariant I8 shows is enforced by nothing today. The gate currently
proves the *label* half of the triple ∀ callers and the *url* half for zero.

**MP3 — `test_each_bootstrap_label_NAMES_its_own_statement`.** Assert each observed label
against an expectation derived independently of the constant — e.g. that the
DEFINE-NAMESPACE record's label contains `"namespace"` and not `"database"`. *Catches:*
wrong build C, and closes the gap between the existing pin's message and its assertion.

**MP4 — make the allowlist key on the CALL, not the function.** Either record the exempt
call's own signature/lineno, or assert a per-function *count* of exempt calls. *Catches:*
wrong build D3.

**MP5 — pin the scanner's bound.** A test asserting `_retry_driver_call_sites_in` does NOT
see an aliased/indirect call, carrying the message *"this is a KNOWN BOUND (#151) — the gate
is name-keyed; if you closed this deliberately, delete this pin and say so"*, with the named
re-open trigger (repo law: an unpinned known limitation is indistinguishable from an unknown
one). *Catches:* silent inheritance of wrong build E's hole.

**MP6 (minor, P6b) — restore the deleted pin's `attempts` assertion.** See §7.

---

## 5. Verification of the author's claims (P4) — every one reproduced

| Claim | Author | My independent measurement | Verdict |
|---|---|---|---|
| RED on the unfixed tree | 17 failed / 472 passed | **17 failed, 472 passed** — same 17 tests | **TRUE** |
| Satisfiability | 489 passed / 0 failed | **489 passed** on *my own* reference build | **TRUE** |
| ruff on the fixed build | clean | `All checks passed!` | **TRUE** |
| typecheck on the fixed build | 55 errors / 5 files (= baseline) | `Found 55 errors in 5 files` — identical to the real repo's baseline | **TRUE** |
| M1 one shared label | 1 failed | **1 failed** — distinctness pin only | **TRUE** |
| M2 cause lost | 13 failed | **13 failed** (3 new + 10 pre-existing) | **TRUE** |
| M3 hardcoded url | 3 failed | **3 failed** (as my A-control) | **TRUE** |
| M4 SCOUTKILL | 20 failed | **31 failed** incl. the e2e scout ladder pin — my wrap covered all three statements, theirs one. Disposition identical | **TRUE, under-claimed** |
| M5 one call loses its label | 4 failed | **4 failed** — gate + the 3 pins for *that* statement | **TRUE** |
| M6 url made positional | 1 failed | **1 failed** | **TRUE** |
| W5 composition gap "already repaired" | verified not assumed | **confirmed** — strict `<` and strict pairwise decrease; regression → 2 failed; **20/20 consecutive green** | **TRUE** |
| §1 "5 pins red on plumbing, not on their property" | disclosed | **confirmed**: `TypeError: bootstrap_session() got an unexpected keyword argument 'url'` | **TRUE — honest disclosure** |
| F1 `scout.py:171` unlabelled | blocking fork | **confirmed** — one of 8 sites, no self-attribution | **REAL** |
| F2 `_surreal_harness.py` must be writable | blocking fork | **confirmed** — required `url` breaks every `[real]` fixture | **REAL** |

**No over-claim found. One under-claim (M4).** The author's §1 disclosure of pins that are
"red today for the wrong reason" is the single most valuable thing in its report and is
accurate.

---

## 6. Fixture-discrimination verdicts (P2), individually

- `_bootstrap_conflicting_on_define_namespace` / `_on_use` / `_on_define_database` —
  **DISCRIMINATE.** Receipt: dropping only the `use` label fails **exactly** the three
  `[use]` params and nothing else. No cross-talk, no small-N collapse; each fate is genuinely
  FORCED. This is the contract's strongest work.
- `_DISTINCT_BOOTSTRAP_URL` (TEST-NET-2, unique in tree) — **DISCRIMINATES at the driver**
  (control: 3 failed) — **and is blind at the caller** (wrong build A). Correct instrument,
  wrong quantifier. See MP1.
- `_BOOTSTRAP_LABEL_CONSTANTS` read off `_txn` — **PARTIALLY discriminates.** Catches
  absence and non-distinctness; cannot catch wrong-statement (build C). See MP3.
- `_BOOTSTRAP_FAILURE_FATES` (4 fates, exact type) — **DISCRIMINATES** (M4: 31 failed).
- Composition-pin fixture (µs margins) — **DISCRIMINATES and is STABLE**: regression → 2
  failed; 20/20 consecutive green. Perturbation note: it depends on `_silence_sleep` patching
  `asyncio.sleep` but not `time.monotonic`. That dependency is documented at the pin and
  holds, but it is the pin's load-bearing fixture assumption — worth a comment if anyone ever
  patches the clock.
- `_MIN_KNOWN_RETRY_DRIVER_CALL_SITES = 8` — **DISCRIMINATES** against a silently-blinded
  scanner (a `>=` floor, 8 sites confirmed today, sibling `loresigil`/`lorescribe` clean).
- `_the_one_exhaustion_record` (exactly-one assertion) — **DISCRIMINATES**; correctly refuses
  to silently take the first of several.

**P5 — can the fake FAIL?** Yes. `_FakeConnection` is script-driven, and M5's per-statement
result is the proof: the `use` fixture demonstrably reaches the `use` statement and nothing
else. Not a mirror of the implementation.

---

## 7. P6b — independent enumeration of the DELETED pin, then the diff

Enumerated from the source at `d2d7b2c^` **before** reading the author's §8. The deleted
`test_the_bootstrap_paths_exhaustion_is_UNATTRIBUTED_a_known_bound` asserted three things:

1. `not hasattr(record, "label")` — the bound itself.
2. **`getattr(record, "attempts", None) == _seam_attempt_ceiling()`** — the attempt count on
   the LOG RECORD.
3. `not hasattr(record, "engine_error")` — the bound's cost.

**Diff against the author's §8** (which describes the deletion but does not enumerate what
the pin asserted): (1) and (3) are the bound, correctly *inverted* by the replacement class —
deletion rather than weakening is the right call and matches the pin's own stated re-open
trigger. **(2) is an ORPHANED VIRTUE.** `TestTheBootstrapPathsExhaustionIsAttributable`
asserts label, url, engine_error and distinctness — never `attempts`.

**Verdict: MINOR.** The bootstrap path's attempt count survives at the *exception* level
(`test_sustained_conflict_raises_the_seams_own_exhaustion_type`, `:391-396`, asserts
`exc_info.value.attempts == ceiling`), and the driver computes `attempts` once for both the
extra and the exception, so the two artifacts cannot diverge without a deliberate edit. Not a
blocker — but it is a behaviour the old world pinned and the new world does not, and repo law
says it gets an adjudication rather than a silent drop. **Recommended: preserved-with-pin** —
one line (`assert getattr(record, "attempts", None) == _seam_attempt_ceiling()`) in the new
class (MP6).

**Corpse sweep (P6):** grepped the test tree for assertions still pinning the retired
"unattributed" behaviour. `test_surreal_harness.py:590` and `:699` and `:715` are *docstring
prose* describing the pre-fix record (`{attempts, elapsed_seconds}` and nothing else) — all
three are in the NEW class's own explanatory text describing the defect being closed, which
is correct and stays true as history. **No live assertion pins the corpse.** Individual
verdicts: `:590` prose/keep · `:699` prose/keep · `:715` prose/keep.

---

## 8. Residuals — every item, individually

1. **The author's §7.1 count claim — CONFIRMED REAL.** `test_retry_seam.py:6841` and the
   comment at `:6779` say *"eleven possible emitters (ten `_query` seams, scout, the
   bootstrap)"* — the parenthesis enumerates **twelve**. Verified by reading both sites. It is
   the un-derived-count class, inside a failure message, and it becomes semantically stale the
   day #151 lands (the bootstrap *becomes* attributable). **Verdict: real, fix in this wave —
   derive the count or drop the number and keep the enumeration.**
2. **`scout.py:171` (F1) — REAL, still unruled.** One of 8 driver call sites, no
   self-attribution, #151's exact shape. I concur with the author's Reading A (label it); note
   its caveat is right — a *full* fix wants a url and `_scout_query` has none in scope, so the
   url half is a genuine design change. **Recommend: label now (partial attribution), and PIN
   the url gap as a known bound with a re-open trigger** rather than leaving it unrecorded.
3. **`_surreal_harness.py` writable (F2) — REAL and BLOCKING.** Verified: without
   `url=env.url` at `:339` the contract is unsatisfiable. My reference build required exactly
   this edit.
4. **`_seam_attempt_ceiling()` orphan risk** — checked: still used at `:394`, `:473`, `:940`,
   `:1202`, `:1238`. **Not an orphan;** ruff is clean. The author's note stands.
5. **The R3 gate checks `label=` but never `url=`** — see I8/MP2. Escalating because R1
   explicitly demands the full triple and the structural half currently delivers two-thirds.
6. **`_ATTRIBUTED_BY_ANOTHER_MECHANISM` evidence quality** — I read all three entries against
   the cited source. `execute_transaction`→`_log_rollback` (`:789-801`): **evidence holds.**
   `scout._consume_live` (`:568-569`, `exc_info=True`): **evidence holds.** `scout._safe_kill`
   (`:593-594`): **evidence holds** (best-effort, swallowed). All three are genuinely
   evidence-backed, not "out of scope" placeholders. Good.
7. **Composition pin's clock dependency** — depends on `_silence_sleep` not patching
   `time.monotonic`. Documented at the pin, 20/20 stable. **Verdict: accepted, noted.**
8. **`/tmp/contract151-ref`** — the author left its reference build in place. Mine is at
   `/tmp/adv151-scratch`. Both outside the repo; delete at will.
9. **`REPORT-*.md` at repo root** — 8 untracked report files present including this one. Repo
   law requires deletion before any image build. **Flagging, not acting.**
10. **⚠ A CONCURRENT AGENT EDITED 13 REPO TEST FILES WHILE I WAS GRADING — ESCALATING.**
    The tree was clean of modifications at session start (per my opening `git status`). At
    **15:16–15:21** thirteen files under `loremaster/tests/` acquired uncommitted
    modifications (148 insertions / 72 deletions), including **`_sdk_guard.py`, which
    `test_retry_seam.py` imports** — one of the two files I was grading. Content indicates
    another agent's editorial work (receipt/UNVERIFIED annotations), consistent with the
    untracked `REPORT-adj-152-*.md` files at the repo root. **I did not make these edits and
    did not touch them.**
    **Impact on my verdict: NONE, and I verified rather than assumed it:**
    - Both contract files are **byte-identical** across HEAD `d2d7b2c`, the worktree, and my
      scratch copy (md5 `f7cd1f58…` and `7514e003…` all three ways). I graded exactly the
      committed contract.
    - The `_sdk_guard.py` edit is **comments only** — `git diff` filtered to non-comment
      lines returns zero output.
    - RED **re-verified after the edits**: `17 failed, 472 passed`, unchanged.
    **Why it still gets escalated:** (a) my reference build was copied at 14:58 and therefore
    predates these edits, so any *future* re-run of my receipts against a moved tree needs
    this timeline; (b) repo law is explicit that finished work must not sit uncommitted, and
    148 lines of another agent's edits are currently the only copy of that work; (c) two
    agents mutating one uncommitted tree is the exact hazard behind the MD5-list near-miss
    already in CLAUDE.md. **Operator's call — but somebody should commit or checkpoint that
    work.**

---

## VERDICT

# CONTRACT INSUFFICIENT

Not because it is weak — it is one of the stronger contracts I have graded, and every claim
its author made is true. It is insufficient because of **one structural hole with a
full-strength receipt**: invariant I4 (the caller's url reaches the record) is quantified over
a single caller, and that caller is a test file the builder may edit. A build in which all
eleven production connection owners hardcode the RPC url passes the contract 489/0 and
produces a **zero failure delta across all 6079 tests in the repository**.

Route back to CONTRACT with **MP1** (blocking) and **MP2–MP6**. MP1 alone closes the blocker;
MP2 closes the structural half of R1's triple; MP3/MP4/MP5 close the three surviving
non-blocking wrong builds; MP6 restores the one orphaned virtue.

**The generalisable lesson, for the ledger:** the contract broke parameter-value monoculture
correctly and then reintroduced it one level up as **caller-population monoculture**. The
repo's law currently reads *"if the code can branch on a value, at least one pin must use a
DIFFERENT value."* This wave argues for its dual: **if a value must be THREADED from N call
sites, at least two pins must drive DIFFERENT call sites with DIFFERENT values.** One caller
is a monoculture, and a test-tree caller is a monoculture the builder is allowed to edit.
