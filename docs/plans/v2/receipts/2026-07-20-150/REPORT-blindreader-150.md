# REPORT-blindreader-150 — contract-blind diff read of `8c96451..HEAD`

brief-base v5 read

## SUMMARY BLOCK

- state: **done-with-deviations**
- deviation 1: **I was exposed to 5 lines of a withheld file.** A bare sweep grep for the
  retired constant names matched `REPORT-harness-retry-builder.md` and printed 5 of its
  lines to my terminal (including its row "B1" adjudicating the budget widening). I did
  not open the file and did not read the #150 finding or the builder's brief. **Every
  finding below was derived before that grep ran**; nothing in the leaked text produced,
  confirmed, or suppressed a finding. Disclosed per the brief.
- deviation 2: I ran gates (pytest on the changed file, ruff, `scripts/typecheck.sh`) and
  four read-only probe processes. No repo file was modified; no live store was touched
  (all probes drive in-process fakes).
- decisions-needed: **F1** (exhaustion drops the engine's message — I recommend fixing in
  this diff); **F2** (teardown runs two uncomposed 2.0s budgets — measured 3.812s);
  **F9** (a dated receipt doc now describes deleted code — historical or stale?).
- verdict on the core change: **the routing is correct and the sharing is real.** All 5
  retried operations reach the seam; order is preserved; non-retryable errors still
  propagate unretried on the first attempt. The mutation pins are genuinely strong. The
  findings are about *information loss on the exhaustion path*, *budget composition*, and
  *three instruments whose prose claims more than their assertions check*.
- receipts: deleted-behaviour table §1 · error-path trace §2 · prose §3 · wrong-build §4 ·
  untouched §5 · gate output §6

---

## 0. What I read

`git show 8c96451:loremaster/tests/_surreal_harness.py` (full, before reading the diff),
then `git diff 8c96451..HEAD` over the three files, then `loremaster/store/_txn.py`,
`test_retry_seam.py`'s bootstrap/floor gates, and the 21 importers of the harness.

Tool honesty (§4): I used **grep/AST scans, not lore**, for every question here. Three of
the five frames are exhaustiveness-or-textual questions the project CLAUDE.md explicitly
routes to grep (retired-name sweep; "does any assertion touch this counter"; "what does
this AST gate's scan actually cover"). Saying so out loud as required. I did not file a
friction row — no lore weakness was routed around; the questions were outside its remit.

---

## 1. Independent enumeration of the DELETED behaviour, per-item verdict

I enumerated this from `8c96451` **before** reading the new file, per the frame.

| # | Old behaviour (at `8c96451`) | Verdict |
|---|---|---|
| B1 | `_RETRYABLE_CONFLICT_MARKER = "can be retried"`, a **declared local literal** | **dropped, plainly deliberate.** Detection is now `_txn.is_retryable_conflict_error`. Mutation-proven at both paths (`test_surreal_harness.py:487,520`). |
| B2 | `_MAX_DROP_DATABASE_ATTEMPTS = 5` — teardown bounded at 5 attempts | **dropped, deliberate, WIDENED.** Now floor 5 / ceiling 64 / 2.0s deadline. The floor equals the old budget, so the ≥5-attempt guarantee is preserved by construction (`_txn.py:895-897`). |
| B3 | Linear backoff `0.01 * (attempt+1)`, **explicitly non-jittered**, justified by a comment: *"Teardown has ONE waiter, so it needs no jitter."* | **dropped, deliberate, and the deletion is an improvement.** That comment's premise was **false under the standing `-n auto` runner** — teardown has one waiter *per worker*, and 64 workers reap databases concurrently against one server. Full jitter is now correct. Worth noting the old comment was a live wrong-reasoning artifact, not merely stale. |
| B4 | `except SurrealError` around the REMOVE | **still done, widened.** Now `except _CONNECTION_ERRORS` = `(OSError, SurrealError, WebSocketException)`. `SurrealError` ⊆ the new set, so nothing that was caught stopped being caught. |
| B5 | On a **non-retryable** error: bare `raise` on attempt 1 | **still done.** Verified by trace §2c and pinned at `test_surreal_harness.py:298,367`. |
| B6 | On a conflict **at the final attempt**: bare `raise` re-raising the **original `QueryError`, engine text intact** | **dropped — and SUSPICIOUS. See F1.** The new code raises a *generic* `TxnContentionExhaustedError` with **no `__cause__`, no `__context__`, and no `engine_error` in the log**. Measured. |
| B7 | `connect_admin` statement ORDER: `DEFINE NAMESPACE` → `use()` → `DEFINE DATABASE` | **still done.** `bootstrap_session` (`_txn.py:1021-1023`) issues the identical order, and the order is now *pinned* (`test_surreal_harness.py:258-263`) where it never was before. Improvement. |
| B8 | `connect_admin`'s three statements were **bare and unretried** | **deliberately REVERSED** — that is the diff's purpose. |
| B9 | `drop_database`'s `use()` was **bare and unretried** | **deliberately reversed.** |
| B10 | `signin()` bare and unretried, in both functions | **still done (unchanged).** Consistent with production `_ensure_connection`; sign-in cannot produce a write-write conflict. Not a gap. |
| B11 | `_RemovableDatabaseConnection` Protocol — `query` only | **still done, still accurate.** The new `_remove()` closure calls only `connection.query`. |
| B12 | `drop_database` closes the connection **only on the success path** | **still done — i.e. the leak is preserved.** See F10: not a regression, but the new code holds the socket ~40× longer before leaking it. |
| B13 | `call_until_recovered` (attempts=4 recovery probe) | **untouched.** But the new module docstring's absolute claim collides with it — F5. |
| B14 | Module docstring's import-cleanliness invariant (SDK + `records` only) | **still done at module level**, now enforced by an AST pin — whose reach is short (F3). |

**No deleted behaviour fell through a crack unnoticed except B6.**

---

## 2. Error-path trace — every failure kind, both functions

| input / failure | old | new | verdict |
|---|---|---|---|
| a. `signin()` fails | raw propagate | raw propagate | unchanged |
| b. conflict on `DEFINE NAMESPACE`/`use()`/`DEFINE DATABASE` | **raised immediately, fixture failed** | retried under one composed 2.0s budget | fixed (the point of the diff) |
| c. non-retryable domain rejection (`Specified database does not exist`) | raise, 1 attempt | raise, 1 attempt, **type unchanged (`QueryError`)** | preserved + pinned |
| d. transport fault (`OSError` / `WebSocketException`) | REMOVE path: `OSError` was **not** caught (`except SurrealError`) → propagate | caught by `_CONNECTION_ERRORS`, classified not-a-conflict, `raise` → propagate | net identical; **untested** (every fixture scripts `QueryError` only) |
| e. exception outside `_CONNECTION_ERRORS` (`RuntimeError`, `CancelledError`) | propagate | propagate (`retry_on_conflict` catches only its own signal) | correct; `CancelledError` is `BaseException` so no accidental swallow |
| f. **conflict that outlives the budget** | `QueryError` **with the engine's text** | `TxnContentionExhaustedError`, **generic text, engine message destroyed** | **F1 — information loss** |
| g. sustained conflict, wall clock | ≤ ~0.1s | up to **3.812s measured** for `drop_database` | **F2 — uncomposed budgets** |

**Nothing is swallowed. Nothing is retried that must not be.** The one thing that changed
for the worse is what a human sees when it finally gives up.

---

### F1 — HIGH · exhaustion destroys the engine's message, and the raise points at a log that does not have it
`loremaster/tests/_surreal_harness.py:265` · `loremaster/store/_txn.py:909-925`

`_run_under_store_retry_seam` calls `retry_on_conflict(_attempt)` with **no `label` and no
`url`**. In the driver, `engine_error` is gated on `label is not None` (`_txn.py:909-918`),
and the `raise TxnContentionExhaustedError` at `_txn.py:920` sits **outside** the `except
RetryableConflictSignal` block, so implicit chaining never fires. Measured, not reasoned:

```
=== WHAT THE HUMAN SEES (message) ===
SurrealDB operation gave up after 64 attempts over 0.000s (retryable conflict);
see the server log for the full engine detail
=== __cause__: None   __context__: None
=== engine text anywhere in the traceback? === False
=== LOG RECORD extras ===
store.retry.exhausted {'attempts': 64, 'elapsed_seconds': 0.00031}
```

The raised message **promises a receipt that does not exist on this path**. `_txn.py:876-880`
documents `last_conflict_cause` as existing precisely so exhaustion can quote the engine
"instead of leaving the operator with only an attempt count and a hint pointing at a server
log that holds nothing" — and the harness, by omitting `label`, lands in exactly that state.

**Failure scenario.** CI starts failing on teardown. Old world: pytest printed
`QueryError: Transaction conflict: Resource busy. This transaction can be retried` — the
engineer knows instantly it is contention, not a bug. New world: 64 attempts over 2.0s,
generic label, and the pointed-at log record carries `{attempts, elapsed_seconds}`. If the
engine has *reworded* its message (the exact drift the diff's own marker pin exists to
catch), the operator cannot see the new wording anywhere — the one artifact that would
diagnose it has been discarded.

**Recommended fix (one line each, no design question):** give
`_run_under_store_retry_seam` a `label: str` parameter and pass `url`, so the two call
sites become `label="harness.teardown.remove_database"` /
`"harness.teardown.select_database"` and `label="harness.connect_admin.bootstrap"`.
I suspect this was simply not considered rather than decided against — nothing in the
diff's prose mentions attribution.

*Adjacent, outside the diff, flagged per scope law:* `_txn.bootstrap_session` also passes
no `label`, and `retry_on_conflict`'s docstring (`_txn.py:857-859`) justifies that as
`bootstrap_session` and `execute_transaction` "hav[ing] their own attribution."
`execute_transaction` does (`_log_rollback`). **`bootstrap_session` logs nothing at all**
(`_txn.py:991-1023`) — so that docstring clause is false for one of the two functions it
names. Pre-existing; the diff newly routes the harness into it.

### F2 — MEDIUM · `drop_database` runs TWO independent 2.0s budgets where the sibling deliberately composes ONE
`loremaster/tests/_surreal_harness.py:348,349` · measured **3.812s**

`_run_under_store_retry_seam` passes no `deadline_seconds`, so each call resolves a **fresh**
`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`. `drop_database` calls it twice.

```
TOTAL teardown wall clock: 3.812s
  use() attempts=41 (then succeeded)   REMOVE attempts=49
```

This is the shape `_txn` itself condemns one function over (`_txn.py:965-970`,
blindreader-dry-2 F2 / audit-fix-1 B2): *"three equal deadlines would be three independent
budgets wearing a parameter."* `bootstrap_session` therefore composes. And the diff's own
docstring (`_surreal_harness.py:224-226`) **name-checks that property** — "`bootstrap_session`
already IS the shared, **budget-composing** form" — so the author knew it and did not apply
it to the two-operation path. I could not determine whether that was deliberate; nothing
in the diff says.

**Failure scenario.** A shared-server contention storm under `-n auto`: every worker's
teardown can now block ~4s instead of the seam's designed ~2s ceiling, and a suite that
mints one throwaway DB per test multiplies that across workers. Not a correctness bug —
a wall-clock bound that is silently double its stated design. Fix is one closure:
compute a `_remaining_budget()` in `drop_database` exactly as `bootstrap_session` does and
thread it through.

### F3 — MEDIUM · the import-isolation pin walks only `tree.body`, so a `try:`-wrapped module-level store import goes green
`loremaster/tests/test_surreal_harness.py:598-608`

The scan iterates `for node in tree.body` — i.e. imports that are *direct children of
Module*, not imports that *execute at module-import time*. Demonstrated:

```
source:  try:
             from loremaster.store._txn import retry_on_conflict
         except ImportError:
             retry_on_conflict = None

pin's offenders (tree.body only): []  -> GREEN (misses it)
walk-based:                       ['loremaster.store._txn']
```

Also missed: imports inside module-level `if`, `with`, `for`, `while`. All execute at
import. **And the `try/except ImportError` wrapper does not even save you** — a store
module that is mid-TDD-broken usually raises `SyntaxError`, `NameError`, or an
`AttributeError` from its own module body, none of which is an `ImportError` — so the
collection error still hits all 21 importers, which is precisely the failure the pin's own
message says it prevents.

This is a name/shape-keyed gate where the repo's law calls for a property
(`CLAUDE.md`: *"a runtime gate is an invariant only over code it actually RUNS"*, and the
six-defeats table). **Fix:** `ast.walk(tree)`, skipping nodes inside
`FunctionDef`/`AsyncFunctionDef`/`ClassDef` scopes — that *is* the property the docstring
describes. (Note `not name.startswith("loremaster.index.records")` also admits a
hypothetical `loremaster.index.records_anything`; trivial, mention only for completeness.)

### F4 — MEDIUM · `test_the_private_policy_constants_are_gone` is a 3-name deny-list whose message promises a check it does not perform
`loremaster/tests/test_surreal_harness.py:558,571-582`

The class docstring says *"a future edit that reintroduces a private budget/backoff/marker
goes RED **here**"*, and the failure message says *"The harness owns NO retry policy"*. The
assertion is `not hasattr(_surreal_harness, name)` for exactly three literal names. A
reintroduced `_TEARDOWN_MAX_ATTEMPTS = 5` or `_HARNESS_BACKOFF` passes it silently.

This is `CLAUDE.md`'s "enumerating what is FORBIDDEN" anti-pattern verbatim (the forbidden
set is unbounded; the safe set is enumerable) and its "failure message that promises a
check the assertion does not perform" clause.

**Severity is bounded, and I want to be fair about that:** the *behavioural* half of the
class IS caught — a differently-named private budget that actually took effect would make
`test_the_teardown_path_follows_the_seams_attempt_ceiling`'s positive-control leg observe
5 instead of 64 and go RED. So the wrong build does not escape the suite; it escapes *this
pin*, whose prose claims to be the one that catches it. Fix is either to soften the prose
to name the mutation pins as the real guard, or to make this an allowlist ("the harness's
module-level constants are exactly this set").

### F5 — MEDIUM · prose contradicted by code 60 lines above it
`loremaster/tests/_surreal_harness.py:31-32` (and repeated at `test_surreal_harness.py:577-579`)

> "The harness owns NO retry policy of its own: **no attempt budget**, no backoff, no copy
> of the engine's conflict marker."

`call_until_recovered` (`_surreal_harness.py:170-214`) takes `attempts: int = 4` and runs a
loop that swallows caller-supplied errors and gives up on a bound. That is an attempt
budget, in this module, untouched by the diff.

The *code* is fine — it is a recovery **probe** for lifecycle tests, a different concern
from conflict retry, and it should not route through `_txn`. The **claim** is what is
wrong: stated absolutely, in the module docstring, in the file that contains the
counter-example. This repo's largest confirmed defect class is exactly "natural-language
surfaces whose consistency with code no gate checks" (3 of 4 in one audited phase), so I am
flagging it rather than calling it a nit. **Fix:** scope the sentence — "owns no
*conflict-retry* policy: no conflict budget, no backoff, no marker."

### F6 — LOW-MED · the sharing pin's REACH is 2 of the 5 retried operations, and the two `use()` sites are not among them
`loremaster/tests/test_surreal_harness.py:389-403,252,319`

The diff puts five operations under the seam: three in the bootstrap (`DEFINE NAMESPACE`,
`use()`, `DEFINE DATABASE`) and two in teardown (`use()`, `REMOVE DATABASE`). The mutation
helpers return `statement_calls[_DEFINE_NAMESPACE]` and `query_calls`. Grepping every
`use_calls` assertion in the new file:

```
252:        assert fake.use_calls == 2
319:        assert fake.use_calls == 2
```

**No assertion ties either `use()` site to a seam constant** — both are constant-independent
"it retried once" checks that a private 2-attempt loop satisfies. The class docstring says
the proof holds "at BOTH its paths", which is true at *path* granularity and not at
*operation* granularity — and the un-mutated operation is `use()`, the call this repo's own
probe identified as *"the call that actually loses the bootstrap race"*
(`test_retry_seam.py:3066-3069`).

Live exposure today is nil: teardown's `use()` shares the *same helper object* as REMOVE, so
it cannot diverge, and the bootstrap's `use()` lives inside `_txn` and is covered by
`test_retry_seam.py:3065`. So this is a **discrimination gap, not a live defect** — but it
is the repo's "check coverage as a variable" law: the guard's reach should be enumerated and
asserted, not assumed.

### F7 — LOW · the diff fixed the instance; the instrument that missed it still cannot see the test tree
`loremaster/tests/test_retry_seam.py:222` (`_PACKAGE_ROOT = parents[1] / "loremaster"`), `:4700-4730`

`test_no_production_module_outside_the_seam_bootstraps_a_session` scans **production
modules only**. That is *why* the harness's bare bootstrap survived the #102/#108 wave
untouched — the harness is a test-tree module. The diff removes the offending code but does
not extend the gate's reach, so the next test helper that hand-rolls a bootstrap is
invisible again.

I ran that gate's own `_bootstrap_sites_in` algorithm over `loremaster/tests/`: the only
`connection.use()` outside a fixture is `_surreal_harness.py:346`, which is the
seam-wrapped one. **No live instances today** — this is about the missing invariant, per
`CLAUDE.md`'s "a fix without an invariant is half a fix". Either extend the scan with the
harness's one legitimate site allowlisted, or pin the bound explicitly per the
"WHEN YOU CANNOT CLOSE A HOLE, PIN IT" section.

### F8 — LOW · teardown's operation ORDER is unpinned, while the bootstrap's is
`loremaster/tests/test_surreal_harness.py:324-343`

`test_a_conflict_on_teardowns_use_call_is_retried_then_succeeds` asserts `use_calls == 2`
and `statement_calls[_REMOVE_DATABASE] == 1` but **not** `fake.operations`. A build that
issued `REMOVE DATABASE` *before* `use()` passes this fake (unkeyed statements succeed by
design) and fails against the real engine, which has no namespace/database selected. The
`connect_admin` sibling at `:258-263` does pin `operations` and calls the ordering
"load-bearing against the real engine" — the same reasoning applies one function over.

### F9 — LOW · a receipt doc now describes deleted code (operator ruling wanted)
`docs/plans/v2/receipts/2026-07-19-packet03/REPORT-recon-pkt03.md:414`

> "The REMOVE itself retries up to `_MAX_DROP_DATABASE_ATTEMPTS = 5` … linear backoff
> `0.01s * attempt`, unjittered (one waiter)."

All three facts are now false. **It is a dated receipt**, so it arguably correctly records
the world of 2026-07-19 and should not be rewritten. But a future reader grepping for
harness teardown behaviour lands here and gets the corpse. Your call: leave as historical,
or add a one-line superseded-by-#150 stamp. I did not touch it.

### F10 — INFORMATIONAL · the admin socket leaks on every failure path (pre-existing, now held ~40× longer)
`loremaster/tests/_surreal_harness.py:341-350`, `:284-291`

`await connection.close()` is only reached on the success path; a raise from `use()`, from
`REMOVE`, or from the bootstrap leaks the connection. **Identical in the old code — not a
regression.** The change is duration: the old code gave up in ~0.1s, the new one after up
to ~3.8s (F2), so a contention storm holds more sockets, longer, against the shared server.
A `try/finally` around both would close it. Raising it because the frame asks what the
change quietly makes worse, not because the diff introduced it.

---

## 4. Wrong-build analysis of the new tests — what I could NOT break

Stating the strong half honestly, since the frame asks for adversarial reading and the
answer is mostly "this holds":

- **`_MUTATED_ATTEMPT_CEILING = 7`** is well chosen — not 64 (real ceiling), not 5 (floor
  *and* the deleted copy's budget). An observed 7 can only come from reading the live seam
  constant. This defeats the obvious wrong builds.
- **Two independent axes** (ceiling → 7; deadline → 0.0 landing on floor 5) mean a build
  that coincidentally agreed on one number cannot agree on both.
- **Every mutation leg carries a positive control** at the unmutated value, and
  `test_both_paths_follow_the_seams_wall_clock_deadline:466` even asserts `ceiling != floor`
  so the pin cannot silently stop discriminating. This is the repo's probe-needs-a-control
  law applied properly.
- **The marker mutation is strictly stronger than the equality pin it replaces** — the
  retired test compared two literals, which a private copy satisfies by definition; the new
  one proves there is no second copy.
- **`_SUSTAINED_CONFLICTS = 500` > ceiling 64**, so no fixture "succeeds" by running off
  the end of its script; running off the end is a loud `IndexError`.
- A build hand-rolling `"can be retried" in str(error)` → caught (marker mutation, both
  paths). A build with a private differently-named budget that *takes effect* → caught
  (ceiling control leg). A build routing `use()` through the driver without classifying →
  caught at the bootstrap by `test_retry_seam.py:3065`.

Gaps found are F4 (deny-list prose), F6 (reach), F8 (teardown order), plus: **no fixture
exercises a non-`SurrealError` member of `_CONNECTION_ERRORS`** (`OSError` /
`WebSocketException`). Behaviour is correct by construction there (shared classifier), so I
rank it below the others, but every scripted outcome in the file is a `QueryError`.

---

## 5. Gate output (§6 receipts)

```
tests/test_surreal_harness.py:  17 passed in 0.17s
ruff check <the 3 changed files>:  All checks passed!
scripts/typecheck.sh:  Found 55 errors in 5 files (checked 146 source files)  -> FAILED
```

**Zero of the 55 mypy errors are in this diff's files** (grep for all three filenames over
the typecheck output returns nothing). They land in
`test_comms_tool.py` (44), `_message_fakes.py` (13), `test_comms_promise_registry.py` (7),
`test_message_ledger.py` (4), `test_surreal_schema.py` (1) — the packet-03 comms suites,
consistent with the INDEX's recorded "180 EXPECTED RED (ModuleNotFoundError
loremaster.messages)" state. I did **not** run the full suite (brief scope + base protocol
§3).

One process note, since it nearly bit me: my first gate attempt printed
`no tests ran in 0.00s` behind a pipe because a persisted `cd` left me in the wrong
directory. Caught by checking for a passed-COUNT, per repo law. The counts above are from
the corrected run.

---

There are **55 mypy errors across 5 files unrelated to our present scope** (and, per the
INDEX, ~180 expected-RED tests from the packet-03 contract that I did not run). Do you want
to examine them more closely?
