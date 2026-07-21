# REPORT-builder-151b

brief-base v5 read
state: done
deviations: none (writable set respected; no assertion, fixture or constant edited)
decisions-needed:
- FLAG-1 — four `scout.py:NNN` citations in `test_retry_seam.py` prose went stale when my
  labels shifted scout's lines (571→576, 599→608); the fix is outside my authorization. §F1
- FLAG-2 — those same four sentences say "RED today … passes no `label`", now doubly false;
  §10d carries the identical PRE-EXISTING instance at `scout.py:171`. §F2
- FLAG-3 — `_txn.py:819-820` holds a SECOND caller enumeration in the same docstring, not in
  the clause the brief scoped. Not false today; same drift shape. §F3
receipts:
- RED→GREEN counts: §1 · scout labels: §2 · F1 before/after: §3 · F2 before/after: §4
- derived-prose pin GREEN: §5 · broader suites: §6 · ruff/mypy tails: §7 · flags: §F1–F4

---

## 1. RED → GREEN (the scoped gate)

```
cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
    tests/test_surreal_harness.py tests/test_retry_seam.py -q -p no:randomly
```

BEFORE (my own baseline, not inherited — 855c266, clean tree):

```
FAILED tests/test_retry_seam.py::TestEveryCallIntoTheRetryDriverIsAttributable::test_every_call_into_the_driver_passes_a_label
FAILED tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_live_subscription_exhaustion_carries_a_label_OF_ITS_OWN
FAILED tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_live_subscription_exhaustion_carries_the_ENGINES_OWN_TEXT
FAILED tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_kill_exhaustion_carries_a_label_OF_ITS_OWN
FAILED tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_kill_exhaustion_carries_the_ENGINES_OWN_TEXT
FAILED tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly::test_scouts_three_seams_label_their_exhaustion_THREE_DIFFERENT_WAYS
6 failed, 525 passed, 1 warning in 19.23s
```

AFTER (re-run once more following the §3 rewording, so this tail is the final tree):

```
531 passed, 1 warning in 18.55s
```

Target met exactly: **6 failed / 525 passed → 0 failed / 531 passed.** The single warning is
pre-existing (`coroutine '_empty_subscription' was never awaited`, test_retry_seam.py:3156) and
present in the baseline tail above.

## 2. TASK 1 — scout's two best-effort seams (`loremaster/loremaster/scout.py`)

`_consume_live` (now :576) and `_safe_kill` (now :608):

```python
subscription = await retry_on_conflict(_attempt, label="command_subscriber.live.rejected")
await retry_on_conflict(_attempt, label="command_subscriber.kill.rejected")
```

No `url` on either — the contract PINS that gap as an inherited known bound
(`test_scouts_{live_subscription,kill}_exhaustion_carries_NO_url_a_KNOWN_BOUND`, both GREEN).

**Why these two strings.** Derived from each seam's own vocabulary, in the house shape
`<owner>.<statement>.rejected` that every other caller already uses — `command_subscriber.query.rejected`
(scout.py:178, ruling R4), `brief.query.rejected`, `store.bootstrap.define_namespace.rejected`. The
seam nouns come from the seams' own existing log events: `command_subscriber.live_unavailable`
(:582) → `live`, and `command_subscriber.kill.already_closed` (:610) → `kill`. Pairwise distinct
from each other and from `command_subscriber.query.rejected`; neither is one of the three
`store.bootstrap.*` labels the borrowed-label assertions refuse.

Both `_attempt` bodies already raised `RetryableConflictSignal() from error`, so the driver's
`last_conflict_cause` was always populated on these paths — the label is the only thing that was
missing, and the two `ENGINES_OWN_TEXT` pins confirm the engine's words now reach the record.

**The explanatory comments** mirror `_scout_query`'s (scout.py:171-175) as instructed, with one
deliberate difference: they cite `_scout_query` **by name, never by line**, so the pointer cannot
rot. (`_scout_query`'s own comment carries no line cite either.)

## 3. TASK 2 / F1 — `loremaster/loremaster/store/_txn.py` (docstring, `label:` arg)

BEFORE (:857-861):

```
            ``None`` (the default — :func:`execute_transaction`, which keeps its
            own attribution via ``_log_rollback``) omits the seam-identity extras
            entirely rather than logging a hole. Every other caller — the ten
            single-statement seams, the three session-bootstrap statements, and
            scout's query seam — passes its own ``label``.
```

AFTER (:857-861):

```
            ``None`` (the default) omits the seam-identity extras entirely rather
            than logging a hole. EVERY caller passes its own ``label`` except one:
            :func:`execute_transaction`, which keeps its own attribution via
            ``_log_rollback``. The EXEMPT caller is what is named — enumerating the
            attributed ones instead goes stale at the next caller (finding #151).
```

Inverted to the exemption form as specified: the rule is stated ∀ callers, and only the exempt
one is named — the same set `_DOCUMENTED_SELF_ATTRIBUTING` / `_ATTRIBUTED_BY_ANOTHER_MECHANISM`
now hold (both down to `execute_transaction` alone). Nothing outside the clause was reflowed.

**Deliberate: FIVE lines replaced by FIVE lines.** My first draft was six and shifted every line
below it by one, breaking five live citations into this file (`_txn.py:876`, `:950`, `:1021`,
`:1092`, `:1242`). Verified line-stable:

```
git diff --numstat → 5  5  loremaster/loremaster/store/_txn.py
old/new line counts: 1386 1386
LINE-STABLE BELOW THE CLAUSE: True      # old[861:] == new[861:], byte-for-byte
```

## 4. TASK 2 / F2 — `loremaster/tests/test_retry_seam.py` (:6843-6845, failure message only)

BEFORE:

```python
            f"server, no engine text. It cannot be attributed to ANY of the possible "
            f"emitters (the ten `_query` seams, scout's query seam, the session bootstrap), "
            f"so the hint points at a log "
```

AFTER:

```python
            f"server, no engine text. It cannot be attributed to ANY of the possible "
            f"emitters — every caller into the driver labels its own exhaustion, save "
            f"`execute_transaction`, which is attributed by `_log_rollback` instead — "
            f"so the hint points at a log "
```

**Proof I changed no assertion** (the AST check the brief warned would be run — I ran it on
myself first):

```
$ git show 855c266:loremaster/tests/test_retry_seam.py > /tmp/tsr_855c266.py
$ python: compare [ast.unparse(n.test) for every ast.Assert] old vs new
assert count old/new: 308 308
ALL ASSERTION TESTS BYTE-IDENTICAL: True
```

`git diff` on the file is a single 3-line hunk inside that one message. No fixture, constant,
`_Exemption` entry or other message was touched.

## 5. The derived-prose pin stayed GREEN

```
uv run pytest tests/test_retry_seam.py::TestTheDriversProseAboutItsCallersIsDerivedFromItsCallers \
              tests/test_retry_seam.py::TestEveryCallIntoTheRetryDriverIsAttributable \
              tests/test_retry_seam.py::TestScoutsBestEffortSeamsAreAttributedByLabelOnly \
              tests/test_retry_seam.py::TestScoutsQuerySeamIsAttributedByLabelOnly -q -p no:randomly
→ 20 passed in 1.99s
```

Why the rewording is safe rather than lucky: `_prose_liars` reports any member of
`_DOCUMENTED_SELF_ATTRIBUTING = {"bootstrap_session", "execute_transaction"}` that appears as a
SUBSTRING of the docstring while no longer being an unlabelled caller. `bootstrap_session` passes
labels since 352db0e, so the literal `bootstrap_session` must not appear — the retired clause
avoided it by writing "session-bootstrap", and my replacement drops the mention entirely.
`execute_transaction` is named and genuinely still unlabelled, so it is not a liar. The reach
control (`prose.strip()`, non-empty audit set, every audited name a live caller) also still holds:
`execute_transaction` remains named, so the pin is non-vacuous rather than merely quiet.

## 6. Broader suites (collateral check)

```
cd /home/ejprice/PycharmProjects/lore/loremaster && uv run pytest \
  tests/test_scout.py tests/test_txn_contention.py tests/test_surreal_store.py \
  tests/test_surreal_apply.py tests/test_store_read.py tests/test_surreal_schema.py \
  tests/test_surreal_manifest.py tests/test_graph_surreal.py -q -p no:randomly -n auto
→ 1 failed, 618 passed in 31.87s
```

The one failure is `test_surreal_schema.py::TestFieldDdlConvergesOnAnExistingStore::
test_every_define_statement_carries_the_guard_its_kind_requires` —
`ImportError: cannot import name 'generate_message_ddl' from loremaster.store.surreal_schema`.
**Proven pre-existing, not assumed:** the symbol does not exist at 855c266 either
(`git show 855c266:…/surreal_schema.py | grep -c generate_message_ddl` → `0`) and neither that
test file nor `surreal_schema.py` appears in my `git status` (0 modified). It is the packet-03
committed-RED contract the brief predicted.

## 7. Gates

```
cd /home/ejprice/PycharmProjects/lore && uv run ruff check .
All checks passed!
RUFF_EXIT=0
```

```
cd /home/ejprice/PycharmProjects/lore && ./scripts/typecheck.sh
Found 55 errors in 5 files (checked 146 source files)
typecheck: loremaster FAILED
TYPECHECK_EXIT=1
```

The 55 did not grow and none is in a file I touched:

```
  12 loremaster/tests/_message_fakes.py
   7 loremaster/tests/test_comms_promise_registry.py
  32 loremaster/tests/test_comms_tool.py
   3 loremaster/tests/test_message_ledger.py
   1 loremaster/tests/test_surreal_schema.py
```

`scout.py`, `store/_txn.py` and `test_retry_seam.py` contribute **zero**.

## 8. Whole diff — 3 files, `git diff --numstat` (added / deleted):

```
11  2  loremaster/loremaster/scout.py        # two labels + their two comments
 5  5  loremaster/loremaster/store/_txn.py   # F1, line-stable by construction
 2  1  loremaster/tests/test_retry_seam.py   # F2, one failure-message clause
```

---

# FLAGS

## F1 — my change made four line-number citations in `test_retry_seam.py` stale (NOT fixed: outside my writable authorization)

Adding the labels shifted scout's call sites. The pins' own prose still cites the old numbers:

| file:line | cites | now actually |
|---|---|---|
| `loremaster/tests/test_retry_seam.py:8854` (docstring) | `scout.py:571` | `scout.py:576` |
| `loremaster/tests/test_retry_seam.py:8888` (failure msg) | `scout.py:571` | `scout.py:576` |
| `loremaster/tests/test_retry_seam.py:8935` (docstring) | `scout.py:599` | `scout.py:608` |
| `loremaster/tests/test_retry_seam.py:8961` (failure msg) | `scout.py:599` | `scout.py:608` |

Citations at or above scout.py:568 are unaffected (`scout.py:171`, `:328`, `:138-145` — my two
hunks start at 568 and 601). I did not touch these because my F2 authorization is exactly one
clause; renumbering them is a second, different edit.

**RECOMMENDED EDIT — do not re-number them; DE-number them.** The number is the part that rots
(this is #152's class, and it just rotted inside the wave that exists to close #151's version of
it). Concretely, at :8888 `at `scout.py:571`.` → ``in `_consume_live`.``; at :8961
`` `scout.py:599`.`` → ``in `_safe_kill`.``; same substitution in the two docstrings.

## F2 — the same four sentences are now doubly false, and §10d has the identical PRE-EXISTING instance

Each opens `"""RED today: `scout.py:571` passes no `label`…`. After this wave the call DOES pass a
label, so the sentence is false about behaviour as well as about the address — a green pin whose
docstring describes a retired world, i.e. #156's shape one level down.

This is not new with me: `TestScoutsQuerySeamIsAttributedByLabelOnly` at :8151 still reads
`"""RED today: `scout.py:171` passes no `label`` — stale since ruling R4 landed the query-seam
label in a previous wave. So there are **six** such sentences after this wave, four mine and two
inherited. Suggest one sweep, phrased as history rather than state ("RED at contract time:
`_consume_live` passed no `label`…"), which is true forever and cites nothing that can move.

## F3 — a SECOND caller enumeration lives in the same docstring, outside the clause the brief scoped

`_txn.py:818-820`: *"Every single-statement seam in this package, and :func:`execute_transaction`,
call this — there is nothing left to hand-roll."* Not false today, and not the clause F1 named, so
I left it byte-for-byte. But it is the same enumerate-the-attributed shape F1 was just inverted to
escape, sitting four paragraphs above it. Operator's call whether it wants the same treatment.

## F4 — tool honesty

`lore_findings` served #151 and #156 (both read in full). Everything else here was grep + AST over
the tree: the label-vocabulary sweep, the `scout.py:NNN` / `_txn.py:NNN` citation sweep, and the
assertion byte-identity check. Those are the sanctioned grep cases in CLAUDE.md's dogfood protocol
— non-symbol textual seams (string literals, prose, line-number citations) and rename-style
exhaustiveness where one missed site matters — so this is a declared fallback, not a routing-around;
no friction filed. `lore_search`/`lore_get_symbol`/`lore_impact` were not needed: the brief named
every file and symbol, and the RED pins were the spec.

## F5 — unrelated failures

In the suites I ran (scoped gate + eight scout/store suites), exactly **one** test fails and it is
the pre-existing packet-03 contract proven above. I did not run the repo-wide suite (brief-base §3
forbids it unless briefed); the brief states repo-wide currently shows ~309 failed + 166 errors from
that same committed-RED packet.

There is 1 failing test unrelated to our present scope. Do you want to examine it more closely?
