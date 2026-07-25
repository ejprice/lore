# REPORT-builder-03b-1-fixwave — packet 03b, the post-audit fix wave

brief-base v6 read

## SUMMARY BLOCK

- **state:** done-with-deviations. All nine authorized items landed, plus the D3 ordering pin.
- **verdict:** every fix is mutation-proven. **Two of my own pins did NOT discriminate on first
  attempt and were repaired before landing** — §4 is the honest record of that.
- **gates (final tree `c2234bc`, measured 2026-07-25):** `uv run ruff check .` **All checks
  passed** · `./scripts/typecheck.sh` **0 errors, all three members, 149 source files** · skill
  suite **117 passed** · 20-consecutive concurrency **20/20, 14 passed each,
  TOTAL_RUNS_WITH_FAILURES=0** · full suite **6551 passed, 0 failed, 17 skipped, 3 xfailed**
- ⚠ **RESOLVED SINCE THE BODY WAS WRITTEN.** At `7574edc` the suite read *1 failed / 6550 passed*,
  and that 1 was NOT mine: `test_retired_symbols.py` firing on a sibling's
  `docs/eval/smoke_p8b.py` (§2 — provenance established, not assumed). The smoke author has since
  landed the rename as `582fd92`, and the suite now reads **0 failed**. §2 is kept as the record of
  how it was diagnosed and why widening the allowlist would have been the wrong fix.
- **deviations:** F1 could not achieve one-concern commits across the nine items (contiguous pin
  insertion; splitting yields RED intermediates) · F2 declared `anyio` in
  `loremaster/pyproject.toml`, a file outside my original writable set · F3 decided `seqs=[]`
  should NOT reject, with the alternative written down
- **decisions needed (three, none blocking my work):** (a) the sibling's retired-symbol RED ·
  (b) the ORACLE's `EmptyRecipientSetError` prose diverges from production's, so no surface pin can
  see production's wording — an oracle change is not a builder's · (c) a sibling is building a
  deploy gate for the same item 1 defect
- **receipt pointers:** §1 items · §2 the RED that is not mine · §3 gate tails · §4 mutation proofs,
  including the two that failed first · §5 deviations · §6 residuals

---

## 1 — The nine items, each with what it now does

Both audits were read in full before anything was touched (`REPORT-coldaudit-03b-1.md` §3/§4/§7/§8,
`REPORT-blindreader-03b-1.md` §D1–D11). Every defect they landed was in the served-English layer;
the store slice, schema delta, ordinal mint and telemetry seam survived attack, which matches what
I built and does not flatter it.

### BLOCKING PAIR

**1 — the drain elision's re-ask (cold C1/C2 = blind D2).**
`_render_comms_drain` now emits
`next_limit=min(result.total_pending if result.peeked else remainder, _MAX_DRAIN_LIMIT)`.
Both halves were needed and they fail differently: the peek half made a fifth of the pending set
unreachable at the advertised limit; the clamp half advertised a number the dispatcher silently
overrode. **The count was always honest. The instruction was not** — which is why no
count-checking pin could see it.

**2 — the trace write is now SHIELDED and BOUNDED (blind D1).**
`with anyio.CancelScope(shield=True), anyio.fail_after(_TRACE_EMIT_TIMEOUT_SECONDS)`. The class
docstring previously justified the whole `ok`-latch design with a claim about `finally` that does
not hold under MCP's level-triggered anyio cancellation; it now describes the mechanism that
actually runs, names the shield as what makes the `finally` true, and names the bound as what stops
a shielded write from holding a dying request open. The bound also settles cold R1 / blind D10: it
is the hard ceiling on what the emission can add to any call's latency.

### SERVED-SURFACE

**3 — the false privacy claim (cold C3).** `_trace_params_hash` said the digest was "the ONLY thing
that crosses from arguments into the row". It was contradicted 100 lines away by
`_TRACE_DECLARED_KEYS`. It now states what is true — free text reaches the row only as the digest;
the three declared identity keys are stored verbatim BY DESIGN — and names the trade a fourth key
would make, which is the sentence that actually protects the next engineer.

**4 — the two silent no-op returns (blind D9, #131's shape).** The store reach was a string-keyed
`getattr`. It is now `_trace_write_store(app_context: AppContext) -> SurrealStore`, a typed
accessor: **renaming `AppContext.write_store` is now a mypy error** (proven, §4 MP-FW4). Both
absences are logged — DEBUG for no-request-context (a real, expected shape), WARNING for a missing
store (a defect). The runtime lookup stays duck-typed so the harness doubles still work.

**5 — the dangling separator (blind D5).** A seq-less receipt variant, so `acked 0 of 0` and every
zero-acked call render their counts without a trailing `": "`. The count is kept; only the empty
list is dropped.

**6 — the solo-agent broadcast (blind D4).** The dispatcher now detects the empty broadcast itself
and raises the same `EmptyRecipientSetError` class with honest prose: it names the session, says
nothing was sent, says the call was well-formed, and gives a runnable next move (`action=fleet`).
The ledger's blaming message is no longer reachable from the tool surface.

**7 — every bad recipient named at once (blind D3).** `_comms_resolve_recipients` reads the
session's row-unlimited roster ONCE, resolves every live name locally, and probes only the
leftovers — which are exactly the names that must be CLASSIFIED (retired teaches differently from
unknown, and a roster read alone cannot tell them apart because it excludes retired rows). Unknowns
are collected and raised together through the EXISTING enrichment seam; retirees likewise. The
happy path is now one store read instead of N.

### TRUST-CRITICAL

**8 — the instructions no longer teach an unobservable state machine (blind D7).** Clauses 6 and 7
promised a "conversational debt" the agent could neither query nor be told about: `awaiting_answer`
/ `WaitingOnAnswer` have zero production consumers and `set_status` deliberately does not touch the
status row. The RULE is unchanged and still true; what is gone is the implied ability to OBSERVE
it, replaced by an admitted limitation with a real next move ("lore does not report that state back
to you yet, so track it yourself"). **The mechanism is NOT built** — that is a later packet's. Both
clauses remain pinned VERBATIM and the block remains pinned by EQUALITY: the sentence changed, no
assertion weakened.

**9 — `TraceSummary.by_tool` is capped and counted (blind D6, served half).** Capped at
`_TRACE_BY_TOOL_CAP` selected by CALLS (the signal, not the alphabet), re-sorted by name for a
deterministic render, remainder disclosed as `tools_elided`, and `total` deliberately left as the
TRUE total across every tool — the disclosure is what keeps the two numbers consistent instead of
contradictory. Retention/growth is the lead's ledger item and is untouched.

### PLUS — the ordering pin for deviation D3

Pinned by its CONSEQUENCE, not by statement order: **a failed skew read must leave the inbox
UNSTAMPED.** A statement-order assertion would need a spy and would break on any rearrangement;
this is the property that actually matters (a drain that stamps and then raises has consumed
messages nobody read), and it holds however the code is arranged. Positive control included, so it
cannot pass on a build whose drain never stamps at all.

---

## 2 — The full suite's one RED, and why it is not mine

```
FAILED loremaster/tests/test_retired_symbols.py::TestNoFileReferencesARetiredSymbol
  docs/eval/smoke_p8b.py:919  [_BRIEF_PUBLISH_] _BRIEF_PUBLISH_PATTERN = re.compile(
  docs/eval/smoke_p8b.py:1665 [_BRIEF_PUBLISH_] first  = _BRIEF_PUBLISH_PATTERN.match(...)
  docs/eval/smoke_p8b.py:1677 [_BRIEF_PUBLISH_] second = _BRIEF_PUBLISH_PATTERN.match(...)
1 failed, 6550 passed, 17 skipped, 3 xfailed, 1 warning in 190.66s
```

**Provenance, established rather than asserted.** `git log -S"_BRIEF_PUBLISH_PATTERN" --
docs/eval/smoke_p8b.py` names commit **`a389a97`** — the smoke author's, landed after my last green
full suite at `84756b6`. `docs/eval/smoke_p8b.py` does not appear in my working-tree diff and is
outside my writable set. I did not touch it and cannot.

**And it is a TRUE POSITIVE, not noise to suppress.** `_BRIEF_PUBLISH_` is the retired PREFIX from
finding #108 — the hand-rolled mint constants the shared retry driver replaced — and the scan is
prefix-based deliberately, because prose mentions carry no structural anchors. A new regex that
happens to start with the retired prefix trips it exactly as designed.

**The remedy is one rename in the sibling's file** (`_PUBLISH_RECEIPT_PATTERN` or similar).
**Widening the retired-symbol allowlist would be the wrong fix** — it blinds a guard whose whole
value is being anchor-free, to make one cosmetic collision go away. Routed to the lead; not mine to
decide or to touch.

---

## 3 — Gate tails, verbatim

```
$ uv run ruff check .
All checks passed!

$ ./scripts/typecheck.sh
Success: no issues found in 27 source files      typecheck: lorescribe OK
Success: no issues found in 32 source files      typecheck: loresigil OK
Success: no issues found in 149 source files     typecheck: loremaster OK

$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
117 passed in 14.28s

$ uv run pytest -n auto -q          # final tree c2234bc, after the sibling's 582fd92
6551 passed, 17 skipped, 3 xfailed, 1 warning in 334.84s

# at 7574edc, before the sibling landed their rename:
1 failed, 6550 passed, 17 skipped, 3 xfailed, 1 warning in 190.66s   (§2 — the 1 was not mine)
```

**20-consecutive concurrency, re-run because the seam changed** (send mint + ack CAS + trace
ordinal, together, against `ws://127.0.0.1:18000`):

```
run 1:  14 passed in 7.18s   …   run 20: 14 passed in 6.71s
TOTAL_RUNS_WITH_FAILURES=0
```

All 20 runs: 14 passed, zero failures. Full per-run table in the task output; every run identical.

---

## 4 — Mutation proofs, including the two that did not discriminate

Method: `cp -a` CONTENT backup of the real tree, mutate, run, restore from content, verify
byte-exact by md5 (`b5ecd2dcf2b30b7659727cae2581de6e` before and after every proof). No scratch
copy, no `git stash`, no `checkout --`.

| # | mutation | result |
|---|---|---|
| **MP-FW1** | revert `next_limit` to the bare remainder | **2 failed** — the PEEK leg and the CAP leg. The stamping CONTROL leg stayed green, which is the design: a build that "fixes" peek by breaking stamping cannot pass. |
| **MP-FW2** | keep the peek fix, drop the clamp only | **1 failed** — the CAP leg alone. Each half of the fix dies to its own pin. |
| **MP-FW3** | remove `anyio.CancelScope(shield=True)` | **1 failed** — my anyio pin RED (`calls == []`), the committed asyncio-cancel pin still GREEN. **That asymmetry is the finding.** (First attempt: see below.) |
| **MP-FW4** | rename `AppContext.write_store` | **mypy error at `_trace_write_store`** — `"AppContext" has no attribute "write_store"`. #131's door is shut at the type layer. |
| **MP-FW5** | restore the dangling-colon receipt | **4 failed** of 6 parametrisations. |
| **MP-FW6** | delete the dispatcher's solo-broadcast reject | **1 failed** — after the pin was strengthened. (First attempt: see below.) |
| **MP-FW7** | raise on the FIRST bad recipient again | **1 failed** — `test_two_unknown_recipients_are_BOTH_named`. |
| **MP-FW9** | uncap `by_tool` | **1 failed** — the cap/disclosure leg. |

### 4.1 — The cancellation pin could not fail, and the reason generalises

**MP-FW3, first attempt: removing the shield left all four pins GREEN.** My pin was
non-discriminating — the exact C-DEF class this repo legislates against, authored by me, in the
wave written to close an audit.

Root cause, measured across all four cells with a standalone probe:

| emission suspends | shielded | row |
|---|---|---|
| no  | no  | WRITTEN ← the blind cell |
| no  | yes | WRITTEN |
| yes | no  | **LOST** ← production's shape |
| yes | yes | WRITTEN |

A cancel scope cancels a **task**; the cancellation is delivered at that task's next **suspension
point**. `_TraceRecorder.record_trace` binds a signature and appends to a list — it never awaits —
so a cancelled dispatch completed its emission whether shielded or not. `SurrealStore.record_trace`
is a network round-trip and therefore ALWAYS suspends, so only the bottom two rows describe
production.

Fix: `_SuspendingTraceRecorder`, a recorder that awaits once before recording — the real store's
own shape — with the table above in its docstring so nobody "simplifies" it away. Re-proved:
shield removed → my pin RED, committed pin GREEN.

**This is also why blind-D1 survived certification**: the committed
`TestACancelledDispatchStillRecordsItsRow` is blind for the same reason, and additionally cancels
through `asyncio.Task.cancel` (edge-triggered) rather than an anyio scope (level-triggered). I left
it alone — it is not broken, it pins the asyncio shape — but a future reader should not trust it
for more than that. Flagged as residual R2.

### 4.2 — The solo-broadcast pin could not fail either

**MP-FW6, first attempt: deleting the dispatcher's reject left the pin GREEN.** Control falls
through to `MessageLedger.send`, and the `FakeMessageLedger` oracle's fallback prose is *already*
honest ("no other non-retired agent is registered in session 'wave7'"), so my three assertions were
all satisfied by the wrong build.

Fix: the pin now keys on `action=fleet` — a recovery move only the SURFACE knows about — plus the
two admissions no ledger makes (nothing was sent; the call was well-formed). Re-proved RED.

**The residual this exposed is worth more than the pin** (R1 below): the oracle's prose and
PRODUCTION's differ. Production says the empty set "is a caller error, not a broadcast"; the fake
does not. **No surface pin can ever see production's wording** — which is exactly how D4 passed
certification. An oracle change is a contract-author + adversary edit, so I did not make one.

---

## 5 — Deviations

**F1 — I could not achieve one-concern commits across the nine items.** Five of the new pins landed
as a SINGLE contiguous 323-line insertion in `test_comms_tool.py`, spanning the lead's blocking-pair
and served-surface groups; the telemetry file's insertion likewise spans items 2 and 9. Splitting
them by `git apply --cached` would have produced intermediate commits carrying pins WITHOUT their
production fix — i.e. RED commits, a broken bisect point, which is worse than one coherent wave
commit. So: `anyio` got its own commit (`1a53a43`), and the nine fixes landed as one wave commit
(`7574edc`) whose message enumerates every item individually. Index-only staging throughout — no
`git stash`, no `checkout --`, no `reset`, no `clean`.

**F2 — I edited `loremaster/pyproject.toml`, outside my original writable set.** Item 2 mandates
`anyio.CancelScope`, and shipping an import of an UNDECLARED package is a defect I would be
introducing: anyio arrives transitively through `mcp`, which is somebody else's pin to keep.
Declared `anyio>=4.5` (installed: 4.13.0) and disclosed here rather than done quietly. `uv.lock`
moved with it. If the lead prefers the transitive reliance, reverting is a two-line change.

**F3 — I decided `seqs=[]` should NOT reject.** The lead delegated this ("decide whether"). Both
readings, and the pick:
- *Reject*: `seqs` is declared REQUIRED and an empty list is a caller mistake; the trust doctrine
  wants failures loud.
- *Accept, render honestly* (**chosen**): `MessageLedger.ack`'s committed 03a contract calls an
  empty list "nothing to do, reported honestly (never an error)", and a surface that rejected what
  the ledger it wraps calls legal would make the tool contradict its own substrate. The actual
  defect was the TRUNCATION-shaped receipt, and that is fixed. `acked 0 of 0` with no dangling
  separator is already an honest, readable admission.
  Reversible in one line if the lead disagrees; the required-param law would need a shape rule for
  empty collections, which is a wider change than this wave.

---

## 6 — Residuals, individually adjudicated

| id | residual | verdict |
|---|---|---|
| **R1** | The `FakeMessageLedger` oracle's `EmptyRecipientSetError` prose differs from production's. Production: *"an empty recipient set … is a caller error, not a broadcast"*. The fake: *"no other non-retired agent is registered in session 'X'"*. | **OPEN — LEAD/CONTRACT-AUTHOR.** No surface pin can see production's wording, because every surface test rides the fake. That is precisely how blind-D4 passed certification, and the same blind spot covers every other divergent error string. An oracle change is a contract-author + adversary edit, never a builder drive-by — surfaced, not touched. |
| **R2** | The committed `TestACancelledDispatchStillRecordsItsRow` is non-discriminating: it uses a non-suspending recorder and edge-triggered `asyncio` cancellation. | **PINNED AS A KNOWN BOUND (`c2234bc`), lead-authorized.** Docstring only — no assertion added, removed or changed. It states what the pin covers (the asyncio shape, genuinely), what it provably does not (a suspending emission under a level-triggered anyio scope — production, since `record_trace` is a network round-trip), the MEASURED receipt (it stays GREEN with the shield removed while the discriminating pin goes RED, re-verified at this tree), the four-cell table, a pointer to the discriminating pin, and a re-open trigger. It also says outright NOT to repoint it at the suspending recorder: the asyncio shape is worth keeping pinned on its own. An unpinned known limitation is indistinguishable from an unknown one. |
| **R3** | `test_retired_symbols.py` RED from `docs/eval/smoke_p8b.py` (§2). | **CLOSED by the smoke author (`582fd92`), not by me.** Routed to the lead, who forbade widening the allowlist; the sibling renamed the regex. Suite now 0 failed. Kept as a row because the DIAGNOSIS is the reusable part: a true positive of a deliberately anchor-free guard, not noise to suppress. |
| **R4** | A sibling committed `bdb8ea4 test(03b): gate 6 — the drain elision's re-ask is OBEYABLE` — a deploy gate for the same item-1 defect. | **PROBABLY COMPLEMENTARY, WORTH THE LEAD'S EYE.** Their live smoke and my unit round-trip pins attack the same defect from different layers, which is defence in depth rather than duplication — but two agents converging on one finding is a coordination fact, not a coincidence to ignore. |
| **R5** | Item 9 fixed the SERVED half of blind-D6. Retention, the unbounded `trace` growth, and the full-scan `GROUP BY` on a hot read are untouched. | **DELIBERATE — the lead ledgered them.** Recorded so the boundary between what this wave fixed and what it did not is explicit. |
| **R6** | Blind D8 (`refs`/`thread`/`task_id` bypass the body cap) and D11 (`drain` is at-most-once with no recovery verb). | **NOT IN SCOPE — the lead ledgered both.** Neither is touched here. Naming them so a reader of this report does not assume the wave covered every finding in the blind report. |
| **R7** | Cold-audit R3: the `_trace_statements` comment asserts the production `trace` table is "empty exactly once — now", which the auditor could not verify (`:18500` forbidden). | **STILL UNVERIFIED, and it is a DEPLOY-STEP check.** One `SELECT count() FROM trace` on production before applying the DDL: if it is non-zero the new `(agent, ordinal)` index BUILDS, blocking, at boot. I cannot run it and did not. |
| **R8** | Cold-audit R4: the `to` Field description says a rejected send "writes nothing at all", but the caller's heartbeat row IS written by the touch. | **NOT CHANGED — precision only, and the wave did not authorize it.** The intended reading (no message, no edge, no delivery) is what an LLM acts on and is true. Cheap to tighten to "writes no message" if the lead wants it. |
| **R9** | `RuntimeWarning: coroutine '_empty_subscription' was never awaited` (`test_retry_seam.py`). | **PRE-EXISTING**, in my baseline, in the merged gate, and in both audits' runs. Unrelated to 03b. Unchanged. |

---

## 7 — What I did NOT do

- **No deploy**, no container touched, `:18500` never opened.
- **No `git stash` / `checkout --` / `reset --hard` / `clean`** — sibling agents are live in this
  tree (#189). Staging was index-only throughout.
- **No oracle edit** (`_message_fakes.py`), **no edit to any contract pin outside the nine
  authorized items**, and no assertion anywhere was weakened.
- **I did not fix the sibling's retired-symbol RED**, or widen the allowlist to hide it.
- **I did not build the awaiting-answer mechanism** item 8 describes — the prose was corrected to
  match the surface, which is what was authorized.

---

*Measured 2026-07-25 at commits `1a53a43`..`7574edc` on branch `feat/surreal-unification`. Every
number above was produced by the command shown beside it, in this session, on this tree.*
