# REPORT-contract-151c

brief-base v5 read

state: **done**

deviations:
- The MP7 pin adopted from adversary-151b §4 was refactored in ONE way, disclosed here and
  NOT a silent semantic change: its candidate universe is an explicit audit set
  (`_DOCUMENTED_SELF_ATTRIBUTING = {bootstrap_session, execute_transaction}`), not "every
  driver caller." A universe of all callers false-reds the day the docstring neutrally
  mentions a *labelled* caller (e.g. `run_query`) — a gate that fires on correct code. The
  load-bearing derivation (`named ∩ docstring − unlabelled`, behaviour side from the AST
  scan) is unchanged and matches the adversary's own `_DOCUMENTED_SELF_ATTRIBUTING` shape.
  A fourth positive-control leg now pins that door shut. §MP7.

decisions-needed: none. (R1 was lead-ruled in the brief; I implemented it as stated.)

receipt pointers:
- MP7 three-leg proof (RED/GREEN/GREEN) with real output — §MP7
- R1 pin, RED at HEAD + GREEN on reference build + leg-A RED — §R1
- I16 + residual-4 — §I16 / §R4
- provenance receipt (`loremaster.__file__`) — §PROV
- full-contract satisfiability (523/0) — §SAT
- gate tails with counts — §GATES
- forks surfaced — §FORKS

---

## WHAT CHANGED

One file, additive only: `loremaster/tests/test_retry_seam.py` (+529 lines).
`loremaster/tests/test_surreal_harness.py` was **not touched** (its :51–60 prose block the
lead is fixing separately is untouched; `git diff --stat` shows only test_retry_seam.py).

Four additions:

| # | where | what | today |
|---|---|---|---|
| **MP7** | new §10e class `TestTheDriversProseAboutItsCallersIsDerivedFromItsCallers` | the driver docstring's self-attribution claim, DERIVED-checked against the AST caller scan | 3 pins GREEN (leg B) |
| **R1** | new §10e-2 class `TestTheSignalsChainingUniversalHoldsOverThePopulationItIsTrueOf` | the `from error` universal, pinned over the population it is true of + the driver's own comment must NAME the un-chainable caller | 3 GREEN + **1 RED** |
| **I16** | `TestEveryProductionOwnerThreadsITSOWNUrl.test_the_per_owner_urls_this_class_drives_are_PAIRWISE_DISTINCT` | the eleven owner fixture urls are pairwise distinct | GREEN (fixture property) |
| **R4** | one clause added to `test_the_scan_does_NOT_see_an_ALIASED_call_a_KNOWN_BOUND`'s docstring | records the `**kwargs`-unpacking false-positive (fail-safe: too strict, not too loose) | docstring only |

**Contract delta at HEAD `72a0bc5`: 34 failed / 481 passed → 35 failed / 488 passed.**
+8 tests = my 8 new pins: **+1 RED** (R1's naming pin, correctly red at HEAD) **+7 GREEN**
(MP7 ×3, R1 reach/control/∀ ×3, I16 ×1). No previously-red pin flipped green and no
previously-green pin flipped red — the arithmetic is exact.

---

## §MP7 — the prose half of #151, DERIVED from behaviour (the blocker)

`_prose_liars(prose, audited, unlabelled)` returns the audited callers the docstring names
as label-less that in fact pass a label — `named = {c for c in audited if c in prose}`,
verdict `named − unlabelled`. `unlabelled` comes from `_all_retry_driver_call_sites()`, the
SAME scan §10 gates on, so the prose is graded against measured behaviour, never against its
own wording. **Not a substring assertion on prose** — it asserts no sentence; reword the
clause however you like and it objects only when a caller the English still names as
label-less has grown a label.

The three legs the brief required, all reproduced on a provenance-asserted reference build:

| leg | tree | result |
|---|---|---|
| **A** | behaviour fixed, docstring UNTOUCHED (the 523/0 build with only the two prose edits reverted) | **RED** — `liars = ['bootstrap_session']` |
| **B** | the UNFIXED tree at HEAD (prose is TRUE today) | **GREEN** — not an always-red trap |
| **C** | behaviour fixed AND the clause retired (the full reference build) | **GREEN** — satisfiable |

Leg A real output (behaviour-fixed / prose-untouched build):
```
docstring names as label-less : ['bootstrap_session', 'execute_transaction']
callers that ACTUALLY pass no label : ['_consume_live', '_safe_kill', 'execute_transaction']
=> liars = ['bootstrap_session']   (RED)
```
Leg B is the valuable one: **GREEN at HEAD, RED the instant HALF 1 lands** — it can be
neither satisfied by doing nothing nor inherited silently.

**Positive + negative controls** (`test_the_liar_detector_FIRES_on_a_known_lie`): four legs
on synthetic input — a real lie is reported, an agreeing pair is not, an unmentioned name is
not, and a *labelled caller the prose merely mentions but is outside the audit set* is not.
That fourth leg is the false-positive door the audit-set scoping shuts, and it is why I did
not universe over "every caller" (the deviation above). Reach control
(`test_the_reach_the_liar_check_depends_on_is_ALL_LIVE`) pins the docstring non-empty, the
audit set non-empty, and every audit-set member a LIVE driver caller — so a renamed caller
cannot leave a dead entry checking nothing.

---

## §R1 — the driver's `from error` universal (lead-ruled)

Measured at HEAD: five `raise RetryableConflictSignal` sites — `:1002`, `:1010`, `:1018`,
`:1103` raise `from error` inside an `except ... as error:` handler; **`:1242`, inside
`execute_transaction._attempt`, raises BARE with no exception in scope** (it detects the
conflict by inspecting a returned response's `failed_statements`, exactly as the driver's own
docstring describes). The comment at `_txn.py:876–880` asserts the unqualified universal
*"every caller that raises the signal does so ``from error``"*, and the `engine_error` extra
rests on it.

Implemented as the brief ruled — the code cannot conform, so the comment must change, and it
must change by **naming the exception**, not by deleting the claim:

- `test_every_signal_raised_FROM_AN_EXCEPT_HANDLER_chains_that_exception` — **∀ over the
  population where the premise is true** (raises lexically inside `except ... as NAME:`,
  derived structurally). GREEN today; a new single-statement seam that forgets `from error`
  goes red here. The handler stack resets at every function boundary, so a closure defined
  inside an `except` block is not miscredited its handler's name (that would report a bare
  raise as chainable — the unsafe direction).
- `test_the_drivers_explanation_NAMES_every_caller_that_raises_UNCHAINABLY` — **RED at HEAD**.
  Grades the comment block the tokenizer finds above `last_conflict_cause`: every bare-raise
  site's enclosing function must be named. It fails on a **deleted** comment as well as a
  **false** one, so the builder must make the comment true rather than delete it. Naming
  `execute_transaction` here also documents WHY §10's allowlist exempts that same body from
  `label=` — the pin strengthens the exemption's evidence rather than merely correcting prose.

RED reason at HEAD (checked against the failure message, not just redness):
```
these sites raise it with NO exception in scope … while the comment names neither them
nor any function enclosing them:
    store/_txn.py:1242 in execute_transaction._attempt()
```
On the reference build (comment corrected to name `execute_transaction`): GREEN, inside the
523/0. On the behaviour-fixed / comment-untouched build: RED (same `:1242`).

Positive control `test_the_walker_TELLS_APART_a_chained_raise_from_a_bare_one` proves the
classifier reports both shapes distinctly; reach control pins ≥5 raise sites so neither pin
goes vacuous. Every assertion's message was read against what the assertion actually checks
(the C-DEF false-gate class): the ∀ pin's message says "chains that exception" and the
assertion checks `chained_from == handler_name`; the naming pin's message says "names …
enclosing them" and the assertion checks `any(function in prose for function in enclosing)`.

---

## §I16 / §R4 — the two minors

**I16** — `test_the_per_owner_urls_this_class_drives_are_PAIRWISE_DISTINCT`. The eleven owner
urls (`_owner_url(name)` for the ten discovered seams + scout) must be a set of size 11.
GREEN today by design (a property of this file's own fixture, `_OWNER_URL_TEMPLATE`); it goes
red only if someone collapses the `{owner}` slot, which the adversary measured makes the
correct build and the hardcoded-url blocker indistinguishable across all ten per-owner pins.
Names the collapse directly instead of leaving it to be inferred from the two-owner pin.

**R4** — one clause added to the existing aliased-bound docstring recording the
`retry_on_conflict(_attempt, **attribution)` shape: SEEN as a site but scored
`has_label=False` (`keyword.arg` is `None` for `**`). Documented as a FALSE POSITIVE (the
gate is too strict, not too loose — fail-safe), no new test, per the brief.

---

## §PROV — which tree the reference build tested

Blessed tool, never `cp -a`:
```
$ ./scripts/scratch_copy.sh /tmp/ref151c-scratch2
  loremaster -> /tmp/ref151c-scratch2/loremaster/loremaster/__init__.py
$ cd /tmp/ref151c-scratch2 && uv run python -c "import loremaster; print(loremaster.__file__)"
PROVENANCE loremaster.__file__ = /tmp/ref151c-scratch2/loremaster/loremaster/__init__.py
```
The scratch carries my refactored pins (verified present before the run). The reference fix
was built independently from `_txn.py`/`scout.py`/the eleven owners — three label constants,
`*, url: str` keyword-only on `bootstrap_session`, label+url threaded into all three driver
calls, `url=self._url` at the ten seams, `url=url` at scout's bootstrap, a label at
`scout.py`'s `_scout_query` (R4), `url=env.url` at the harness — plus the two prose
corrections MP7 and R1 require.

## §SAT — satisfiability

```
$ cd /tmp/ref151c-scratch2/loremaster && uv run pytest \
      tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
523 passed, 1 warning in 19.13s
```
The adversary's number to meet was 515/0; 515 + my 8 additions = **523/0**. Exact. The
harder leg (a contract that traps the builder between the lint and a test it may not edit):
the fix ADDS parameters/constants and removes nothing, so ruff demands no orphaned-import
deletion — confirmed by running ruff on the reference build, not reasoning about it.

## §GATES — HEAD, read-only (no `--fix` run anywhere; scope-incident warning heeded)

```
$ cd loremaster && uv run pytest tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
35 failed, 488 passed, 1 warning in 20.13s        (was 34/481 committed — +1 RED, +7 GREEN)

$ uv run ruff check .            -> All checks passed!   (exit 0)
$ uv run ruff check loremaster/tests/test_retry_seam.py loremaster/tests/test_surreal_harness.py
                                 -> All checks passed!
$ ./scripts/typecheck.sh         -> Found 55 errors in 5 files   (baseline, packet-03 comms)
                                    grep for my two files in that output: 0 hits
```
Typecheck baseline did not grow; the 55 errors are all in packet-03 comms files
(`test_comms_*`, `test_message_ledger.py`), none in the files I touched.

## §FORKS — surfaced, not silently resolved

1. **The MP7 universe choice (settled, disclosed as a deviation).** All-callers vs a curated
   audit set: I picked the audit set because all-callers has a real false-positive door and
   the adversary's proven implementation used the audit set. Flagged here in case the lead
   prefers the fully-derived universe despite the false-positive risk — I do not recommend it.
2. **Scout's `_scout_query` label value in the reference build** was my own choice
   (`"command_subscriber.query.rejected"`) — it satisfies the R4 pins (non-empty, not a
   bootstrap label, not `run_query`'s) but is NOT prescribed by the contract; the builder
   picks the real name. This is a reference-build detail, not a pin.
3. **`REPORT-*.md` at the repo root now numbers twelve** including this one. Repo law requires
   deletion before any image build. Flagging, not acting.
4. **Scratch artifacts** left at `/tmp/ref151c-scratch` and `/tmp/ref151c-scratch2` (a `rm`
   was permission-denied). Both are outside the repo; delete at will.

---

## VERDICT

The one narrow ground round 2 was graded INSUFFICIENT on is closed. The prose half of #151 is
now pinned — DERIVED from the caller scan, GREEN today and RED the moment the behaviour lands
unaccompanied — and R1's false universal is pinned over the population it is true of while the
driver's own comment is forced to name the architectural exception. The behavioural contract
was not touched. Full contract satisfiable at 523/0 on an independently-built reference fix
with the prose retired.
