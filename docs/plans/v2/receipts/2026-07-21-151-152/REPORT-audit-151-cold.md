# REPORT-audit-151-cold — cold refute audit of finding #151's fix (`352db0e`)

brief-base v5 read

## SUMMARY BLOCK
- **state:** done-with-deviations — verdict is **NO-GO**, narrowly, on ONE served-English defect.
- **The bootstrap_session fix itself is GO-quality and MUST NOT be reverted.** All 7 refutation
  targets against the fix FAILED to refute (the fix holds): receipt exists end-to-end, all 11
  owners thread their own url, scout bound is a real post-fix tripwire, the prose half is
  behaviour-derived, no wrapping regression, no un-suite-visible caller, DRY proven by mutation.
- **The blocking defect is ADJACENT, not in the fix:** the §10 exemption evidence for
  `scout._consume_live` claims *"the engine's text rides the traceback"* — **MEASURED FALSE**
  (`/tmp/probe_consume_live.py`). It is green at every builder gate, it is the repo's largest
  confirmed defect class (served English no gate checks), and it was authored by the #151
  contract and blessed "evidence holds" by BOTH adversary passes **on inspection, never measured.**
- **decisions-needed:** (1) Fix now vs defer the `_consume_live` evidence clause — operator's call
  (recommend fix now; one-string edit, no behaviour change). (2) Should the two best-effort scout
  paths pass a `label=` so the driver record actually carries `engine_error` (making the aspiration
  true), or stay exempt-and-pinned? Design question — operator ruling.
- **deviations:** I ran three mutation proofs on the REAL tree with a `cp -a` content backup
  (`/tmp/_txn_151.py.bak`), each restored byte-exact (md5 `3cfbf06b…`, `git diff` empty). No git
  state touched. Scratch lives outside the repo.
- **receipt pointers:** end-to-end receipt → §T1 + `/tmp/probe_151.py`; own-url mutation → §T2;
  scout bound → §T3; derived-prose mutation → §T4; no-wrap mutation → §T5; type-env sweep → §T6;
  DRY → §T7; **the NO-GO defect → §FINDING + `/tmp/probe_consume_live.py`**; gates → §GATES;
  overlap with withheld reports → §OVERLAP.

## Method / order (per brief)
I formed every finding from the DIFF (`git show 352db0e`) + the finding (`lore_findings get 151`) +
the store reference, and I ran my own probes/mutations, BEFORE reading any withheld report. Only at
the end (§OVERLAP) did I skim `REPORT-builder-151.md` / `REPORT-contract-151*.md` /
`REPORT-adversary-151*.md`, solely to mark overlaps. `loremaster.__file__` in both probes resolved
to `/home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py` — I tested the real tree.

---

## §T1 — Refutation target #1: the receipt exists end-to-end. **COULD NOT REFUTE.**
`/tmp/probe_151.py` drove `bootstrap_session(..., url=X)` to exhaustion against a faked conflict
storm (a real `surrealdb.errors.SurrealError` carrying the live `"…can be retried"` marker) and
inspected the emitted `store.retry.exhausted` log record:

```
label        = 'store.bootstrap.define_namespace.rejected'
url          = 'ws://probe-151-host:18000/rpc'
engine_error = 'Failed to commit transaction due to a read or write conflict. This transaction can be retried'
attempts     = 64
raised msg   = '…gave up after 64 attempts…(retryable conflict); see the server log for the full engine detail'
```
The record now carries the full triple (statement label, server url, the engine's own text), and
the raised message's "see the server log" promise points at a record that now holds it — including
the reworded-message case the finding worried about (`engine_error` is `str(last_conflict_cause)`,
the raw engine text). **Positive control (same probe):** the pre-fix shape — an UNLABELLED
`retry_on_conflict` call, which is byte-for-byte what bootstrap did before the fix — logs a record
with NO `label`/`url`/`engine_error`. The probe distinguishes attributed from unattributed; it is
not blind. **Control 2:** a labelled-but-BARE-signal call logs `label`+`url` but `engine_error=""`,
confirming the engine text requires `raise … from error` — which bootstrap's three inner attempts
do (`_txn.py:1036/1044/1052`).

## §T2 — Refutation target #2: all 11 owners thread their OWN url. **COULD NOT REFUTE.**
Source spot-check: all ten ledger/store/manifest owners set `self._url = url` from an injected
constructor arg (`agents.py:366`, `briefs.py:402`, `diff.py:495`, `findings.py:406`,
`graph_surreal.py:325`, `snapshots.py:222`, `surreal_manifest.py:145`, `memory/local.py:293`,
`store/surreal.py:381`, `tasks.py:418`) — a per-instance own url, not a module global; the two the
commit message names (SurrealStore, TaskLedger) do so too. Scout's `_open_command_connection` passes
its own `url` parameter (`scout.py:231`).
**Independent mutation (A):** in a `cp -a`-backed real tree I hardcoded the three bootstrap calls to
`url="ws://mutant-hardcoded:9999/rpc"`. `TestEveryProductionOwnerThreadsITSOWNUrl` → **12 failed / 2
passed** — every one of the ten seams, scout, AND `test_two_owners_at_two_urls_log_TWO_DIFFERENT_urls`
(`assert 'ws://mutant…' != 'ws://mutant…'`) went red; the 2 that passed assert the fixture's own
discrimination, not the tree. The own-url pins genuinely discriminate a shared/hardcoded url from
per-owner threading. Restored byte-exact.

## §T3 — Refutation target #3: scout's known bound is real and pinned. **COULD NOT REFUTE.**
`_scout_query(connection, …)` takes a bare connection and `CommandSubscriber` holds a `connect`
callable, not a url (`scout.py`) — url attribution there is a genuine design change, correctly
deferred. Post-fix scout passes `label="command_subscriber.query.rejected"` but no url, so the driver
writes `extra["url"] = None`. `retry_on_conflict`'s signature confirms `url: str | None = None`
(keyword-only), so the label-only call is valid. `test_scouts_query_exhaustion_carries_NO_url_a_
KNOWN_BOUND` (`:8203`) is therefore now a **real tripwire** (not "true for the wrong reason" as it
was on the unfixed tree — that is disclosed in its own docstring): the day someone threads a url into
`scout.py:171`, `extra["url"]` becomes non-None and the pin goes RED, carrying the "delete this pin
and say so" message and a named re-open trigger. Companion pin
`test_scouts_query_exhaustion_carries_a_label_OF_ITS_OWN` (`:8156`) asserts the label as a PROPERTY
(non-empty, not a borrowed bootstrap/run_query label), not against a declared constant.

## §T4 — Refutation target #4: the prose half is DERIVED, not restated. **COULD NOT REFUTE.**
`TestTheDriversProseAboutItsCallersIsDerivedFromItsCallers` (`:8335`) computes `{callers the
docstring names as self-attributing} ∩ {audited} − {callers the AST scan measured as unlabelled}`;
neither set is written down in the assertion. It ships a reach control (all three inputs live) and a
four-leg positive control (the liar detector fires on a known lie, stays quiet when prose+behaviour
agree, reports every audited liar, and does NOT flag a labelled caller merely mentioned).
R7 is guarded by `TestTheSignalsChainingUniversalHoldsOverThePopulationItIsTrueOf` (`:8575`), an AST
walk that pins ∀ handler-borne raises chain `from error` and that the `last_conflict_cause` comment
NAMES `execute_transaction._attempt` (the one un-chainable raiser) — membership in the tokenizer-found
comment block, any wording accepted.
**Independent mutation (B):** I reintroduced the exact #151 lie into the driver docstring
(`:func:`bootstrap_session` and :func:`execute_transaction`, which have their own attribution`).
`test_every_caller_the_docstring_names_as_UNLABELLED_really_passes_no_label` → **RED**
(`assert not ['bootstrap_session']`). Reword-proof and non-tautological. Restored byte-exact.

## §T5 — Refutation target #5: no wrapping regression (R5). **COULD NOT REFUTE.**
The diff adds no `except`/wrap to `bootstrap_session` or its inner attempts; every failure still
propagates unwrapped. `TestAttributingTheBootstrapDoesNotChangeItsDisposition` (`:7524`) asserts the
EXACT type (not isinstance) across all four failure fates.
**Independent mutation (C):** I wrapped bootstrap's first retry call to raise
`SurrealConnectionError` on exhaustion (the W1-SCOUTKILL shape). Both the direct pin AND
`TestScoutsConnectFailureReachesTheReconnectLadder[SUSTAINED-CONTENTION…]` went **RED** — the ladder
pin proved a wrap flies past scout's reconnect ladder and drops `command:gap`. Restored byte-exact.

## §T6 — Refutation target #6: the type environment is a fiction. **COULD NOT REFUTE.**
Repo-wide sweep (bare grep — a required-kwarg signature change is a rename-exhaustiveness question):
every `bootstrap_session(...)` call is a **static, direct** call — 11 production owners
+ 1 test-harness (`_surreal_harness.py:339`, threaded `url=env.url`). **Zero** callers in the sibling
packages `loresigil` / `lorescribe`; **zero** dynamic dispatch (`getattr`/`partial`/aliasing). So
mypy sees every caller; `url` being REQUIRED+keyword-only TypeErrors any missed static caller at
compile — which is exactly how the commit says SurrealStore and TaskLedger (absent from the fix
brief's hand-list) were caught. No production-only or runtime-only caller exists that a green suite
would miss.

## §T7 — Refutation target #7: DRY / routing-is-not-sharing. **COULD NOT REFUTE.**
All owners feed the ONE `bootstrap_session` → the ONE `retry_on_conflict` driver, which owns the
attribution policy (the `if label is not None:` extras block, `_txn.py:919-928`). Mutation A (§T2) is
the mutation proof: changing the shared driver's url source moved 15+ pins across all owners at once —
a per-owner private copy would not have moved. The two attribution gates share ONE scanner
(`_call_sites_in`, `:7168`, "one implementation, two keys"), not a clone.

---

## §FINDING — the NO-GO defect (real, green-at-every-gate, repo's largest class)

**`scout._consume_live`'s §10 exemption evidence contains a factually FALSE clause.**
`_ATTRIBUTED_BY_ANOTHER_MECHANISM[("scout.py","_consume_live")]` (`test_retry_seam.py:7143`) reads:

> "swallows `TxnContentionExhaustedError` and logs its own `command_subscriber.live_unavailable`
> record with `exc_info=True` (scout.py:568-569). The exception never escapes, **and the engine's
> text rides the traceback**."

**MEASURED FALSE** (`/tmp/probe_consume_live.py`, driving the real `_consume_live` to exhaustion):
```
(a) driver record on this path : label=<ABSENT> url=<ABSENT> engine_error=<ABSENT>  (unattributed)
(b) swallowed exception         : TxnContentionExhaustedError, __cause__=None, __context__=None
    formatted traceback         : …TxnContentionExhaustedError: SurrealDB operation gave up after 64
                                   attempts…; see the server log for the full engine detail
    'can be retried' in traceback? False        'see the server log' in traceback? True
```
The driver raises the exhaustion error **bare** (`_txn.py:930`, outside the `except`), so
`__cause__`/`__context__` are `None` and the engine's conflict text does **not** ride the traceback;
`exc_info=True` captures only the "see the server log" message, and the record it points at holds
nothing (unlabelled caller). This is #151's *exact* false-promise shape — and its exact **cognitive**
error (believing an attribution exists where it does not) — reproduced inside #151's own contract.

**Why it is a NO-GO, precisely:** it is real, it is the served-English class CLAUDE.md treats as
first-order ("A DIAGNOSIS IS NOT AN INSTRUMENT"), and it is **green at every builder gate** — the
§10 gate checks an exemption's evidence only for presence and a 60-char floor, never truthfulness
("no assertion can read English", `:7609`), so a false clause sails through. That "no gate can read
it" property is exactly why #151 exists and why this audit exists.

**Why it does NOT condemn the fix:** the exemption is still LEGITIMATE on its *other*, true ground —
"the exception never escapes" (best-effort swallow; the poll backstop serves; no operator-facing
false promise), identical to `_safe_kill`'s correctly-framed evidence. The FIX BEHAVIOUR is right;
only the justifying prose over-claims.

**Recommended remediation (one string, no behaviour change):** delete/replace the "the engine's text
rides the traceback" clause so the evidence rests only on the true "swallowed, best-effort, never
reaches a caller" ground (align it with `_safe_kill`'s wording); and correct the stale line cite
(the `command_subscriber.live_unavailable` log is `scout.py:577`, not `:568-569` — that is the
`raise` site). **Optional design fork for the operator:** if we want the aspiration to be TRUE, give
`_consume_live`/`_safe_kill` a `label=` so the driver's `store.retry.exhausted` record actually
carries `engine_error` server-side for these best-effort paths — a design change the contract
deliberately did not make, so it is the operator's call, not a builder's.

---

## §GATES (re-run independently; counts asserted)
- `tests/test_surreal_harness.py tests/test_retry_seam.py` → **523 passed, 0 failed** (18.7s). Matches
  the brief's claimed 523/0. (One benign `RuntimeWarning: coroutine '_empty_subscription' was never
  awaited` at `test_retry_seam.py:3156` — a test-fixture wart, not a failure. Flagging, not fixing.)
- `uv run ruff check .` → **All checks passed, exit 0.**
- `./scripts/typecheck.sh` → **exit 1, 55 errors in 5 files** — all in packet-03 comms
  (`test_comms_*`, `test_message_ledger`, `_message_fakes`, `test_surreal_schema`); **verified NONE
  touch any #151 file.** Matches the brief's baseline.
- Green restoration after all three mutations: 523/0 re-confirmed; `git diff` empty on `_txn.py`.

## §OVERLAP (read only after forming the verdict)
- **The §FINDING is NEW to this audit and CONTRADICTS both adversary passes.** `REPORT-adversary-151.md`
  residual #6 read the three exemption evidences "against the cited source" and declared
  `scout._consume_live (:568-569, exc_info=True): **evidence holds.**` `REPORT-adversary-151b.md` I12
  re-read them and recorded `_consume_live, _safe_kill: hold` — and pointedly *did* drive-verify the
  `execute_transaction` entry ("I verified this rather than relaying it") but only re-READ the two
  scout entries. Neither pass drove `_consume_live` to exhaustion and inspected the traceback; my
  cold audit did, and the "rides the traceback" clause is false. This is the cold-audit-catches-what-
  inspection-blessed pattern the phase exists for (P8d: 3 of 4 waves).
- `REPORT-contract-151.md` §residual notes `scout.py:171` was "#151's exact shape in a different
  function … outside the brief's stated scope" — a related awareness, but about the LABEL gap it then
  fixed, not the `_consume_live` evidence falsehood.
- Everything else in the withheld reports (515/0 prose door, MP1 own-url door, I16 fixture vacuity,
  R7 bare-raise) matches what I independently reproduced above; no disagreement.

## §HOUSEKEEPING
- Tree byte-exact and clean of production/test edits (`git status --porcelain` shows no
  `loremaster/loremaster` or `loremaster/tests` changes). No git state touched. No worktree created.
- Scratch (all outside the repo, deletable): `/tmp/probe_151.py`, `/tmp/probe_consume_live.py`,
  `/tmp/_txn_151.py.bak`.
- I did NOT file a lore finding for §FINDING (would mutate a shared ledger I was not told to own) —
  recommend the lead file it, kind=friction, area `loremaster.store._txn` / `scout._consume_live`,
  linking #151.

## VERDICT: **NO-GO** — one narrow served-English defect (§FINDING), green at every builder gate,
of the repo's largest confirmed class, authored inside #151's own contract and blessed by two
adversary passes on inspection. **The `bootstrap_session` attribution fix itself is sound and must
NOT be reverted** — remediation is a one-string evidence correction (plus the optional design fork).

### RESIDUALS (read these, not just the verdict — repo law)
1. **[the NO-GO] `_consume_live` exemption evidence is false** — §FINDING. One-string fix.
2. **Stale line cite in the same evidence:** `scout.py:568-569` → the actual log is `scout.py:577`
   (`:568-569` is the `raise RetryableConflictSignal` site). Low-harm, but it is the same served-text
   class; fix in the same edit.
3. **Design fork (operator):** `_consume_live` and `_safe_kill` lose the engine's conflict text on
   exhaustion entirely (record unattributed AND traceback bare). Harmless today (DEBUG, swallowed,
   poll backstop) but it is genuine attribution loss on two more driver callers. Pass a `label=` (and
   accept the engine text lands server-side) OR keep them exempt-and-pinned — a deliberate choice,
   currently made implicitly.
4. **Benign test wart:** `RuntimeWarning: coroutine '_empty_subscription' was never awaited`
   (`test_retry_seam.py:3156`). Not a failure; worth a one-line `contextlib.suppress`→proper-await
   cleanup someday.
5. **Disclosed completeness bound (not a defect):** the derived-prose pin only audits the enumerated
   set `{bootstrap_session, execute_transaction}`. A future FALSE self-attribution claim about a
   *different* caller would not be caught until that caller is added to `_DOCUMENTED_SELF_ATTRIBUTING`.
   Honestly disclosed at `:8297-8310`; acceptable, but named so it is inherited deliberately.
