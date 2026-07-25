# REPORT-coldaudit-03b-2 — cold REFUTE audit of packet 03b's two remediation waves

brief-base v6 read

## SUMMARY BLOCK

- **VERDICT: NO-GO for deploy.** Six confirmed items. **Nothing contradicts a builder gate
  number** — every one reproduced. The defects are in the layer the gates cannot see: a
  served instruction that loops, an acceptance gate that never ran, a ruling whose safety
  argument is false, an undisclosed commit scope, four stale-prose sites, and three
  unimplemented rider clauses. No data loss, and zero production exposure today.
- **state:** done. All six claimed gate numbers INDEPENDENTLY re-run and REPRODUCED exactly.
- **gates (re-run by me 2026-07-25, baseline `0a0b38d`, 12-file MD5 fingerprint IDENTICAL
  before and after every run — §0):** full suite **6581 passed / 0 failed / 17 skipped /
  3 xfailed**, exit 0, 294.51s · `./scripts/typecheck.sh` **0 errors, all three members,
  loremaster 149 source files** · `uv run ruff check .` **All checks passed** · skill suite
  **117 passed** · 20-consecutive concurrency **20/20, TOTAL_RUNS_WITH_FAILURES=0**
  (my selector collected **11**, builder reported 14 — different `-k`, same outcome; §0.3) ·
  EXPLAIN receipt reproduced WITH its control (§3.2).
- **confirmed defects, ranked:**
  **C1** the PEEK re-ask does not CONVERGE above `_MAX_DRAIN_LIMIT` — advertised sequence
  `[50,50,50,50,50,50,50]`, 50 of 100 rows unreachable, control converges. **SPEC-PRESCRIBED**
  (round-1 handed over the line AND its two fixtures on separate axes, never crossed); degrades
  the peek mitigation DD-4.e rules on (§1).
  **C2** the packet's OWN ACCEPTANCE GATE NEVER RAN — DD-3.d says schema-description changes
  trip C3's consumer-battery re-run trigger; these waves rewrote four descriptions, the
  instructions block and two renders. **Zero mentions across all four reports; no transcript
  committed** (§2).
  **C3** DD-3.c's migration SAFETY ARGUMENT is FALSE — *"cannot write-poison (message rows are
  never UPDATEd)"* is true of `message` and **false of `to`**, where `ack_note` lives and which
  `drain` UPDATEs in ONE statement per call. I reproduced total inbox denial with controls (§3).
  **C4** `1a6010f` ("the trace_ts index — DEPLOY-GATED") carries the ENTIRE DD-3 store-schema
  change — 51 of 59 inserted lines, UNDISCLOSED (§4).
  **C5** FOUR stale-prose sites, two in the functions the fixes edited, two certifying the OLD
  world in the test tree (§5).
  **C6** THREE more rider clauses implemented-without-their-rider, incl. the one that would
  have caught C3 (§6).
- **ORACLE VERDICT (the lead's question): ACCEPT.** In scope, necessary, and it cannot
  introduce divergence — proved by MUTATION, not inspection (§7). Caveat stated honestly:
  it is satisfiable for BOTH consumer suites but only ONE discriminates on it.
- **decisions needed:** (a) C1 — the honest peek-over-cap re-ask is not expressible as a
  `limit=`; a DESIGN fork, recommendation in §1.4, the ruling is not mine. (b) C2 — run the
  battery before deploy, or rule the trigger waived, in writing. (c) C4 — does the
  deploy-gated commit need isolating?
- **receipt pointers:** §0 fingerprints + gate tails · §1 C1 · §2 C2 · §3 C3 + live store
  probes · §4 C4 · §5 C5 · §6 C6 + the rider audit · §7 the oracle · §8 mutation-proof table
  (13 mutations) · §9 what SURVIVED attack · §10 RESIDUALS

---

## 0 — Gate re-runs, with tree fingerprints (finding #192)

### 0.1 Fingerprint

Baseline HEAD `0a0b38d8620fba52c359caa7dcd6ae12f9d007e1`, `git status --short` clean apart
from a sibling's untracked `REPORT-blindreader-03b-2.md`. MD5s of all twelve changed files
captured BEFORE the first run and AFTER the last:

```
95dc8598b0a8271f6880083e7336c77f  loremaster/loremaster/config.py
097a33312a497f9fc2a7e78f24358d80  loremaster/loremaster/messages.py
de57fe6b3abe145a762ceeb21f6f88aa  loremaster/loremaster/server.py
2bfd445fe6c00b920d57c34652e85a5f  loremaster/loremaster/store/surreal.py
71a94f71cd0f6275a0d1d3b3777ddfdd  loremaster/loremaster/store/surreal_schema.py
6e5f7434c81407d6158666828c52e296  loremaster/pyproject.toml
083a55c56be5b626f70663dfae919e0e  loremaster/tests/_message_fakes.py
dc563f0a702892427b51cb462f5adb81  loremaster/tests/test_comms_promise_registry.py
0f9aa8e751b9cda802a4013327147d62  loremaster/tests/test_comms_schema.py
d7766ad21e3a293f64ea746963d1bc82  loremaster/tests/test_comms_tool.py
0dc2fab846cf7f8ca91f70bf34ab4539  loremaster/tests/test_message_ledger.py
8153dec93837b2e2bea2e5127ee3ff2a  loremaster/tests/test_trace_telemetry.py
```

`diff` of the pre- and post-run captures is EMPTY. **FINGERPRINT IDENTICAL.**

⚠ **HEAD MOVED MID-AUDIT, and it does not invalidate anything.** After my last run, HEAD
advanced `0a0b38d` → `09f8d3b` ("docs(03b): re-run the design-wave gates under #192").
`git diff --stat 0a0b38d..09f8d3b -- loremaster/` is **EMPTY** — the commit touches only
`REPORT-builder-03b-1-designwave.md`. Every number below therefore still describes the code
at HEAD. Disclosed rather than silently absorbed, per #192.

### 0.2 Tails

```
full suite   : 6581 passed, 17 skipped, 3 xfailed, 1 warning in 294.51s (0:04:54)   EXIT=0
typecheck    : Success: no issues found in 27 source files    → lorescribe OK
               Success: no issues found in 32 source files    → loresigil  OK
               Success: no issues found in 149 source files   → loremaster OK
ruff         : All checks passed!
skill suite  : 117 passed in 15.42s
```

Every count carries a passed-COUNT in the tail; none of these is a piped "no tests ran".
**All four match the builder's claims exactly.**

### 0.3 The 20-consecutive concurrency run

```
run 1: 11 passed …  run 20: 11 passed, 337 deselected in 5.34s
TOTAL_RUNS_WITH_FAILURES=0
FINGERPRINT IDENTICAL
```

Selector: `-k "oncurrent or Concurrent"` over `test_message_ledger.py` +
`test_trace_telemetry.py` → **11** collected. The builder reported **14**, so we ran
DIFFERENT sets, not the same one twice. Both read zero failures across 20 runs. I did not
reverse-engineer the builder's exact `-k`; I state my own set and its count rather than
report a number I did not produce.

---

## 1 — C1 (BLOCKING): the PEEK re-ask does not CONVERGE above `_MAX_DRAIN_LIMIT`

### 1.1 The claim under attack

`AppContext._render_comms_drain` now emits
`next_limit=min(result.total_pending if result.peeked else remainder, _MAX_DRAIN_LIMIT)`,
under a comment headed **"THE RE-ASK MUST BE OBEYABLE."** The fix's own contract class
`TestTheAdvertisedReAskIsACTUALLYReachable` states the property it pins: *"a drain's
advertised `next_limit`, fed back through the REAL dispatcher, must serve every row the
elision line counted."*

### 1.2 The uncovered cell — and it was PRESCRIBED, not invented by the builder

⚠ **This is a SPEC-PRESCRIBED defect, and that framing matters for who owns it.** The
round-1 cold audit (`REPORT-coldaudit-03b-1.md` §3, "Recommended fix (4 lines, one
function)") handed the builder the line VERBATIM:

> ```python
> next_limit=min(result.total_pending if result.peeked else remainder, _MAX_DRAIN_LIMIT),
> ```
> plus the two fixtures that were never written: **(i)** `total_pending > _MAX_DRAIN_LIMIT`,
> **(ii)** a `peeked=True` result WITH a remainder …

**Two axes, enumerated separately, never CROSSED.** The builder implemented the prescription
faithfully and wrote exactly those two fixtures — one per axis. The conjunction (peek AND
over-cap) is the third cell, and it is where the prescription's own stated property fails.
That property, quoted from the same paragraph, is *"a drain's advertised `next_limit`, fed
back through `_comms_drain`, must serve every row the elision line counted"* — **false in
that cell, measured below.**

This repo already names this exact shape: *"ONE was a SPEC that prescribed the bug"*
(PKT-28 C1) — and it is precisely why contracts get cold-audited, not just code. The builder
did not misimplement anything here; the fix's own prescription carried the gap, and the
round-1 audit that wrote it was its own only grader.

The two shipped legs are:

| leg | `total_pending` | `peek` | remainder vs cap (`_MAX_DRAIN_LIMIT` = 50) |
|---|---|---|---|
| `test_a_PEEK_re_ask_reaches_every_row_it_counted` | 30 | **True** | 20 — **under** the cap |
| `test_the_re_ask_NEVER_advertises_a_limit_the_dispatcher_overrides` | 70 | **False** | 60 — over the cap |

**No fixture combines `peek=True` with a remainder ABOVE the cap.** That is the same
fixture-monoculture the class's own docstring says it was written to end ("the largest
`total_pending` fixture ANYWHERE in the test tree was 10 … and no fixture combined
`peek=True` with a remainder").

### 1.3 The receipt (measured 2026-07-25 at `0a0b38d`, real dispatcher, with a control)

Probe driven through `AppContext.comms(action="drain", …)` exactly as the committed pins do,
100 pending against `_MAX_DRAIN_LIMIT` = 50, obeying the advertised instruction seven times:

```
ADVERTISED LIMIT SEQUENCE: [50, 50, 50, 50, 50, 50, 50]
SEEN 50 of 100; UNREACHABLE 50
FAILED  a consumer OBEYING the advertised peek re-ask [50, …] saw only 50 of 100 rows;
        50 are UNREACHABLE and the advertised limit never changes — the instruction LOOPS.

POSITIVE CONTROL (identical shape, peek=False): converges — 100 of 100 seen.  PASSED
```

The control is what makes this a receipt about the PEEK branch rather than about the cap:
the stamping drain, same pending count, same cap, reaches every row.

**Mechanism:** a peek stamps nothing, so every re-run re-reads from the OLDEST row. With
`total_pending` (100) clamped to 50, the advertised value is a fixed point: `limit=50`
serves rows 1–50, the elision recomputes `min(100, 50) = 50`, and the caller is instructed
to do the identical thing again, forever. Rows 51–100 are unreachable through the served
instruction at any limit. The served line reads `+50 more unread — re-run with limit=50`
immediately after a drain that WAS limit=50.

This is the property the code comment names: *"A re-ask naming a limit the dispatcher
silently overrides is a served instruction the system does not honour."* Here the
dispatcher honours the limit and the INSTRUCTION still cannot be completed.

**And the surface it degrades is one the design explicitly leans on.** DD-4.e rules that
*"peek stays the manual mitigation"* for the drain loss window — the ruled recovery for
DD-4's at-most-once exposure IS peek-then-act-then-stamp. A peek whose advertised re-ask
is a fixed point above 50 pending means that mitigation cannot inspect the tail of a large
inbox at all, which is exactly when an agent would reach for it.

### 1.4 Recommendation (a fork, not a ruling — the ruling is the lead's/operator's)

The clamp is right (DESIGN-LAW §1.2) and `total_pending` is right for a peek; the two are
simply not jointly expressible as a `limit=` once `total_pending > _MAX_DRAIN_LIMIT`.
So the honest surface is a DIFFERENT SENTENCE for that cell, e.g.:

> `+{more} more unread — a peek cannot reach past limit={cap}; re-run without peek=true to
> consume this window, then peek again`

with a third pin: `peek=True` × `total_pending > _MAX_DRAIN_LIMIT` × *"obeying the served
instruction reaches every counted row within K rounds"*. Reading two — leave the arithmetic
and pin the bound as a KNOWN BOUND per CLAUDE.md's "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" —
is defensible, but it is a served-instruction loop, so I would not choose it. **Written down
per brief-base §2 rather than picked silently.**

---

## 2 — C2: the packet's OWN ACCEPTANCE GATE never ran against the changed surface

This repo's CLAUDE.md names the acceptance instrument for served surfaces explicitly: *"consumer-agent
batteries with keyed honesty probes ending in the routing test — CALL_AGAIN vs ROUTE_AROUND, where a
ROUTE_AROUND on an honestly-rendered surface is a FAILED acceptance to fix, never a waived answer.
First instance: packet 03b rulings §C5."* The instrument exists in-tree as
`scripts/comms_consumer_eval.py`, and the LEAD ruled on its gating semantics DURING this packet
(`e165141` — *"a drifted run is not a GATING run — refuse to count it"*), so it is live and expected.

**DD-3.d names the trigger in its own text:** *"Note the cost: schema-description changes trip C3's
battery re-run trigger (one floor-model gate run — cheap, budgeted by FK-5)."*

**The trigger fired, comprehensively.** These two waves changed, all of them battery-graded surfaces:

| surface | change |
|---|---|
| `refs` tool description | REWRITTEN (the old one taught the bypass verbatim) |
| `thread` / `task_id` / `note` / `to` descriptions | four more edits, all with new bounds prose |
| `_INSTRUCTIONS` clauses 6 and 7 | REWRITTEN (D7 — the mechanism-with-no-consumers correction) |
| the drain elision render | new arithmetic AND a new served number |
| the ack receipt render | a NEW mutually-exclusive template variant |
| the solo-broadcast reject | an entirely NEW served error |
| `TraceSummary`'s served schema description | rewritten, plus two new served fields |

**Measured:** `grep -niE "consumer.?(battery|eval)|FK-5|comms_consumer_eval|CALL_AGAIN"` across
`REPORT-builder-03b-1-designwave.md`, `REPORT-builder-03b-1-fixwave.md`, `REPORT-coldaudit-03b-1.md`
and `REPORT-blindreader-03b-1.md` returns **ZERO hits** — the battery is not mentioned by the builder,
by either round-1 auditor, or by me until now. No transcript exists under
`docs/plans/v2/receipts/2026-07-24-packet03b/` (20 files, none a battery run;
`grep -rl "CALL_AGAIN\|ROUTE_AROUND"` over the whole receipts tree returns two DESIGN documents and
no run).

**Why this outranks everything except C1.** The gates that ARE green — pytest, mypy, ruff — cannot
see any of the seven surfaces above; that is precisely why C5 exists as a defect class and why the
battery was built. Every defect round one found lived in this layer. Shipping a wave whose entire
content is served-English changes, without running the one instrument that grades served English,
is the packet's exit gate left unmet — not a missing nice-to-have.

**Ask for the lead:** run it before deploy, or rule the trigger waived IN WRITING with a reason.
It is cheap by the ruling's own words ("one floor-model gate run"). I did not run it myself: it is
an acceptance gate, and an auditor running the gate it is auditing is the builder-grades-own-work
shape this role exists to avoid — plus my writable set is one file.

---

## 3 — C3: DD-3.c's migration SAFETY ARGUMENT is false, and the live store probes (spike-surreal `ws://127.0.0.1:18000` ONLY; `:18500` never touched)

### 3.0 The false safety claim, and the total-inbox-denial it permits

DD-3.c's migration bullet justifies landing the narrowing later if need be:

> **Migration:** … landed in THIS deploy the narrowing meets an empty table (§0.F7). **Landed later
> it still cannot write-poison (message rows are never UPDATEd)** …

**True of `message`. FALSE of `to`** — and `to` is where DD-3.f puts `ack_note`. `MessageLedger.drain`
UPDATEs `to` on EVERY call, and it does so in ONE guarded statement over the whole window:

```
UPDATE to SET seen_at = $seen_at WHERE out = $agent AND in IN $message_ids AND seen_at IS NONE
```

SurrealDB re-validates the WHOLE record on write (store reference §1.4), so a single legacy edge
carrying an over-cap `ack_note` fails that statement — and because it is one statement over the
window, **the agent cannot drain ANY of its inbox.** Not a per-row rejection: total denial.

**Reproduced independently, 2026-07-25, with a discriminating control set** (I re-derived this rather
than inherit it from the parallel sweep that first raised it):

```
D0 OLD world: two `to` edges written, one carrying a 2500-char ack_note   : OK
D1 NEW DDL (ack_note ASSERT <= 2000) applied over the dirty store         : OK
D2 drain's ACTUAL whole-window stamp, verbatim                            : REJECTED  <-- total denial
D3 CONTROL — the SAME statement over the CLEAN edge only                  : ACCEPTED (1 row)
D4 the POISONED edge alone, to name the cause                             : REJECTED, naming the ack_note value
```

D3 is what makes D2 a real negative rather than a broken instrument; D4 attributes the failure to
the ASSERT rather than to the statement shape.

**Production exposure TODAY is ZERO** — the `message`/`to` tables have never been deployed (the same
free-window fact verified in §3.3), which is exactly why the free window was used and why this is not
an outage. What is wrong is the RULING'S REASONING, which a future narrowing on either table will
lean on. And note what would have caught it: **the dirty-store rider DD-3.c itself specifies and
that was skipped** (§6). The rider was not bureaucracy; it was the instrument that finds this.

Provenance receipt printed by all three probes:
`loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py`
(the real tree, deliberately — these are READ/DDL probes against throwaway databases, not
mutation proofs; the mutation proofs used `scratch_copy.sh`, §8).

### 3.1 The #107 shape — does the schema delta actually MIGRATE a DIRTY store?

**Every test mints a virgin DB**, which is structurally why #107 survived 1040 tests. I built
the dirty path by hand: apply the PRE-change message DDL (no pointer ASSERTs, no `refs[*]`
row), write a row that is legal under it, then apply the shipped DDL over the top.

```
A0 OLD-DDL over-length row (300-char thread/ref/task_id) : ACCEPTED    (fixture is valid)
A1 NEW DDL applied over a DIRTY store                    : OK
A2 pre-existing row survives                             : [(seq=1, len(thread)=300)]
A3 [thread]     REJECTED, and the error NAMES `thread`
A3 [refs[*]]    REJECTED, and the error NAMES `refs`
A3 [task_id]    REJECTED, and the error NAMES `task_id`
A3 [refs count] REJECTED, and the error NAMES `refs`
A4 POSITIVE CONTROL — a legal row after migration        : ACCEPTED
B1 re-apply of the SAME DDL (the every-boot path)        : OK  (no boot crash)
B2 refs[*] ASSERT still fires after the re-apply         : REJECTED  (not wiped)
B3 INFO FOR TABLE echo:
   refs    → DEFINE FIELD refs ON message TYPE array<string> DEFAULT [] ASSERT array::len($value) <= 20
   refs.*  → DEFINE FIELD refs.* ON message TYPE string ASSERT string::len($value) <= 256
   thread  → DEFINE FIELD thread ON message TYPE string ASSERT string::len($value) <= 256
   task_id → DEFINE FIELD task_id ON message TYPE none | string ASSERT string::len($value) <= 256
total failures: 0
```

Probe discipline satisfied on all three legs: a positive control (A4), four
differently-broken inputs each rejected for a DIFFERENT reason naming its OWN field (A3),
and an explicit fixture-validity check (A0) proving the old world really was unguarded.

Three things this settles that the committed suite does not:

1. **The `OVERWRITE`-for-fields rule lands.** The ASSERTs migrate onto a store that already
   holds the old definitions AND rows. Not #107's shape.
2. **The `refs` / `refs[*]` ORDER is safe.** `_MESSAGE_FIELD_SPECS` emits the array row
   before the element row; re-applying the array row does NOT wipe `refs.*` (B2 + B3).
   Store reference §7's per-entry-ASSERT gotcha is obeyed, and `_define_field`'s `OVERWRITE`
   is what makes the always-a-re-definition element row legal.
3. **`task_id` echoes as `none | string`** — §7's `INFO FOR TABLE` normalisation note is
   real, and the committed pins correctly assert the EMITTED statement rather than the echo.

⚠ Consequence worth stating: the surviving pre-change row is now **write-poisoned**
(§1.4) — readable, but any future UPDATE re-validates the whole record and RAISES. Not
reachable in production (the `message` table has never been deployed — see §3.3), so this is
a note for whoever migrates a store that HAS shipped these tables, not a defect.

### 3.2 The EXPLAIN receipt, reproduced with its control

Real `generate_ddl(dim=4)` schema, 60 trace rows one per day, 14-day cutoff:

```
WINDOWED    -> Aggregate{by: tool} / IndexScan{index: trace_ts, access: ">d'2026-07-11T…'", direction: Forward}
UNWINDOWED  -> Aggregate{by: tool} / TableScan{table: trace, direction: Forward}
windowed   total calls = 14   (correct: strict `>` over 60 daily rows)
unwindowed total calls = 60
```

**The builder's claim reproduces exactly, control included.** The index is present and named
`trace_ts` on `FIELDS ts`, and the window is a real range IndexScan, not a filtered scan.

### 3.3 The `trace_ts` free-window argument — corroborated independently

The pin's docstring asserts *"production holds zero rows today (independently read on the
live store before this deploy)"*. I did not read `:18500` (brief prohibition). I corroborated
it from code history instead, which is the stronger instrument here: `SurrealStore.record_trace`
has exactly ONE caller in the whole tree (`TracingFastMCP._record_tool_trace`), and
`TracingFastMCP` was introduced in **`74863a7`**, which is INSIDE packet 03b and therefore
not in any deployed image. The trace table has never been written to in production, so the
free-window argument holds and `IF NOT EXISTS` will CREATE (not rebuild) at the next boot.

---

## 4 — C4: `1a6010f`'s contents are UNDISCLOSED

Builder deviation G2 discloses that `git commit --only` scopes PATHS not HUNKS, and that the
DD-3.d descriptions + cold-R4 therefore rode inside `ad8153b`. **I verified that disclosure
and it is accurate** — `ad8153b`'s server.py hunks are exactly the telemetry work plus the
four ruled description edits, nothing more.

**The undisclosed one is `1a6010f`.** Its message is *"feat(03b): the trace_ts index —
DEPLOY-GATED, the free window closes at this deploy"*, and `git show 1a6010f --stat` reads
`surreal_schema.py | 63 +++++--` (59 insertions). Only **8** of those lines are the index.
The other 51 are the ENTIRE DD-3 store-schema change:

- `MESSAGE_POINTER_MAX_CHARS = 256`, `MESSAGE_REFS_MAX_COUNT = 20`
- the `thread` ASSERT · the `refs` count ASSERT · the whole `refs[*]` element row ·
  the `task_id` ASSERT · the `ack_note` BODY-cap ASSERT

Its named partner commit `d4e4778` ("bound the POINTER fields") carries `messages.py`,
`_message_fakes.py` and the two test files — but **not** the schema it is named for.

**Why this matters more than G2:** `1a6010f` is the ONE commit the design wave labelled
DEPLOY-GATED. As landed it is not isolatable and not revertable without also reverting a
store-schema migration; and at `1a6010f` the tree carried the new ASSERTs with their pins
still one commit in the future. `git log --oneline` now teaches a false map of where the
schema change lives — which is the CLAUDE.md citation-durability concern one level up.

**Ask for the lead:** rule whether the deploy-gated line needs isolating before deploy, and
whether G2's disclosure should be amended to name this commit (the one it omits) as well as
the one it names. History rewriting is not mine to propose in a four-agent tree.

---

## 5 — C5: FOUR stale-prose sites

Every defect round one found lived in the served-English layer. These are the same class one
level in — prose that DESCRIBES behaviour and was falsified by the change beside it. None is
MCP-served, so none is deploy-blocking on its own; all four are lore-indexed and semantically
retrievable, which under THE CONSUMER LAW is a real reader. **Two of the four are TEST prose
certifying the OLD world** — the failure mode CLAUDE.md names as *"a suite can be green BECAUSE
it still asserts the corpse."*

**C5a — `AppContext._render_comms_drain`, its own docstring, falsified by `7574edc`.**
Two sentences, both now FALSE, sixty lines above the fix that falsified them:

> "The elision's re-ask is the REMAINDER **in both slots**, because a non-peek drain stamps
> exactly the served window …"

The peek slot is now `total_pending`, not the remainder. And in `Args:`:

> "`limit`: The served window's cap; unused by the arithmetic (**the honest re-ask is the
> remainder, never the cap**) …"

The re-ask IS clamped to the cap whenever `reachable > _MAX_DRAIN_LIMIT`. `limit` is still
genuinely unused — that half is true; the parenthetical is wrong twice.

**C5b — `AppContext._render_comms_drain_row`, falsified by `d4e4778`.**

> "``refs`` are capped at the SHARED ``_COVERAGE_NAMES_CAP`` with a counted remainder:
> **refs are uncapped at the ledger**, so an uncapped render is an unbounded dump …"

The design wave bounded refs at the ledger (`MESSAGE_REFS_MAX_COUNT = 20`) and at the store.
The render cap's stated JUSTIFICATION was retired by the same wave. (The render cap itself is
still correct and `_COVERAGE_NAMES_CAP = 5`, so the new `surreal_schema.py` comment's "the
drain render already caps the DISPLAY at five" is TRUE — I checked, it is not a second wrong
number.)

**C5c — the test tree still certifies the OLD world at the seam the fix wave corrected.**
Fix-wave item 3 rewrote `_trace_params_hash`'s docstring specifically to retire an over-claim,
and now reads *"It is NOT the whole argument boundary: the three keys in
`_TRACE_DECLARED_KEYS` are stored VERBATIM."* The test class that certifies that seam —
`test_trace_telemetry.py::TestParamsHashIsTheRuledRecipeAndLeaksNothing` — still says,
verbatim, the sentence that was retired:

> "The digest is the ONLY thing that crosses from arguments into the row, so it is also the
> **whole privacy boundary**: bodies, briefs, and queries pass through the hash and
> **nowhere else**."

`agent`, `session` and `action` are stored plaintext. The class is named `…LeaksNothing`.
This is CLAUDE.md's rename-sweep law exactly — *"tests written before a semantic change
certify the OLD world"* — and the sweep that should have caught it is the fix wave's own.
An agent asking lore "does the trace row leak arguments?" can retrieve this chunk and get
the false answer, with a class name that reinforces it.

**And the instrument that would have caught it is the one CLAUDE.md already mandates.** The
law says sweep with BARE, ANCHOR-FREE patterns. Measured:

```
$ grep -rn "nowhere else" --include=*.py loremaster/
loremaster/tests/test_trace_telemetry.py:2361:    the hash and nowhere else.          <-- the survivor
loremaster/loremaster/server.py:7648:  … reaches the row ONLY as this digest and nowhere else.   <-- the corrected copy
```

Two hits, one grep, no anchor. `"privacy boundary"` is tighter still and returns exactly the
one survivor. The round-1 audit report itself QUOTES the offending sentence verbatim in its
§4, so the search string was already written down. The fix corrected the copy the audit
POINTED AT and never swept for a second — a hand-list sweep instead of a grep sweep, which
is the failure mode CLAUDE.md records as *"sweep from the GREP, never from a report's
hand-list."*

**C5d — the elision contract class still asserts the RETIRED rule in its own name.**
`test_comms_tool.py::TestTheDrainElisionArithmeticIsTheREMAINDER` — the class the fix wave
superseded — still opens:

> "A non-peek drain stamps EXACTLY the served window … so the honest re-ask is the REMAINDER:
> `more == next_limit == total_pending - shown`."

Stated unconditionally, as settled law, with the retired rule in the CLASS NAME. It stays green
only because its assertions exercise the non-peek, under-cap branch where it is still true. The
governing design doc `03b-design-rulings-r2.md` §B15 likewise still teaches the retired
arithmetic as ruled. Two more copies of the corpse, at the exact seam C1 lives in.

---

## 6 — C6: rider clauses implemented WITHOUT their rider — the third instance, and three more

**The third instance the brief asked me to sweep for is not an inference — it is a sentence in
the ruling**, and it is the one that would have caught C3. DD-3.c's third bullet, verbatim:

> **Migration:** `DEFINE FIELD OVERWRITE` lands the changed definitions (§1.1) … **The
> message-slice dirty-store pin (§1.6 pattern) gains the narrowed-assert leg.**

**No dirty-store leg was added.** `test_comms_schema.py` already carries a complete
§1.6-pattern migration class — written for the `ENFORCED` flip
(`test_BASELINE_the_old_world_really_is_unguarded` /
`test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store` /
`test_the_row_written_under_the_OLD_definition_SURVIVES` /
`test_the_migration_is_idempotent_on_an_already_migrated_store`) — and it gained nothing.
The two classes the design wave added (`TestThePointerBoundsHaveTheirSTOREBackstop`,
`TestThreadIsREQUIREDAndNonOptional`) are both OFFLINE: they read generated DDL text and
never touch an engine. The ruling named the instrument and the template; neither was used.

This is the same shape as the two riders the builder self-reported, and it is the one it
did not catch. **It is also the highest-value of them all — because it is the leg that would
have found C3.** The very first thing a dirty-store leg does on `to` is write an old-world
`ack_note` and re-apply; §3.0's D2 is the assertion that leg would have made. The rider was
not bureaucracy. It was the instrument, and skipping it is why a false safety claim in the
ruling survived a full design wave, a builder self-audit, and two rounds of review.

### 6.0 THREE further unimplemented rider clauses (each verified by me)

| ruling | rider, verbatim | measured |
|---|---|---|
| **Q5 (folded)** | *"Fix-wave-eligible one-liner: the bound + its re-open trigger goes in `drain`'s docstring"* — the concurrent-same-agent double-serve KNOWN BOUND | **NOT IMPLEMENTED.** `MessageLedger.drain`'s docstring: **0** hits for re-open trigger / concurrent / races-itself / multiplex. An accepted KNOWN BOUND with no pin and no docstring is exactly what CLAUDE.md's "WHEN YOU CANNOT CLOSE A HOLE, PIN IT" forbids — *"an unpinned known limitation is indistinguishable from an unknown one."* |
| **DD-6 · cold R1(2)** | *"the >5%-p50 re-open trigger gets its INSTRUMENT: the deploy smoke TIMES a read-tool batch and commits the number… **A trigger nobody measures is a hope**"* | **NOT IMPLEMENTED.** `grep -cE "p50\|perf_counter\|latency\|elapsed" docs/eval/smoke_p8b.py` → **0**. The trace emission is now awaited inline on every dispatch with a 5 s ceiling; the trigger that was supposed to watch that has no measurement behind it. |
| **DD-6 · Q7 / cold R3** | a read-only `SELECT count() FROM trace` **and** `SELECT count() FROM message` on the live store **BEFORE** the DDL applies | **NO INSTRUMENT.** Nothing in `smoke_p8b.py` counts either table, and its `ProductionTraceReader` runs AFTER deploy. ⚠ **This one gates C4's own justification**: the free-window argument for shipping `trace_ts` now rests on "the table is empty today", and there is no committed instrument that establishes it at deploy time. I corroborated it from code history instead (§3.3) — sound, but it is my derivation, not the deploy's. |

None of these three is a code defect. All three are the same shape: a ruling's *"and measure/pin
it like this"* clause dropped, leaving a claim with no instrument under it.

### 6.1 What "mirroring `body` exactly" actually requires

DD-3.c's instruction is to enforce the pointer bounds at BOTH layers *"mirroring `body`
exactly"*. `body`'s instrumentation is the comparand, and it has **two** parts:

| | offline DDL pin | LIVE behavioural pin | dirty-store migration pin |
|---|---|---|---|
| `body` | yes | **`TestMessageSchemaLive::test_an_oversize_body_is_rejected_by_the_store_backstop`** | — |
| `refs` / `refs[*]` / `thread` / `task_id` / `ack_note` | `TestThePointerBoundsHaveTheirSTOREBackstop` (4 tests) | **NONE** | **NONE** |

`grep MESSAGE_POINTER_MAX_CHARS\|MESSAGE_REFS_MAX_COUNT loremaster/tests/*.py` returns hits in
exactly two files, and every `test_comms_schema.py` hit is inside the OFFLINE class.
`TestMessageSchemaLive` gained nothing. `test_comms_schema.py` also already carries a
dirty-store migration class as a ready template (`test_BASELINE_the_old_world_really_is_unguarded`
/ `test_the_guard_is_LIVE_after_applying_the_new_ddl_to_a_dirty_store` /
`test_the_row_written_under_the_OLD_definition_SURVIVES` /
`test_the_migration_is_idempotent_on_an_already_migrated_store`, written for the `ENFORCED`
flip) — and the pointer ASSERTs did not use it.

**This is not a live defect** — §3.1 proves the behaviour is correct TODAY, on a dirty store,
with a control. It is a missing INSTRUMENT, and it is the #107 lesson stated in this repo's
own words: **pinning the emitted statement proves the RECIPE; only a live pin proves the
CAKE.** An emission pin cannot see a definition that emits and never lands — which is
precisely the failure mode `OVERWRITE` exists to prevent.

Recommendation: port §3.1's probe into `TestMessageSchemaLive` (one over-length write per
field, with A4's legal-row control) and into the existing migration class. `_create_message`
needs `refs`/`thread`/`task_id` parameters to do it, which is plausibly why it was skipped.

### 6.4 The two SELF-REPORTED riders — both verified GENUINELY closed

The builder reports two rulings it initially implemented without their riders, and says both
are now pinned and re-proved RED. I re-derived both independently rather than taking the claim:

| rider | claim | my verdict |
|---|---|---|
| **the `trace_ts` line was silently deletable** | now pinned | **CLOSED.** M2 (delete the line) → `test_the_ts_index_ships_in_the_SAME_free_window` RED, 1 failed / 16 passed. |
| *and its own sub-rider:* "parse the FIELDS clause, never substring the statement" | obeyed | **OBEYED, genuinely.** `_index_fields` parses the FIELDS clause and its docstring states the reason (an index NAMED `trace_ts` contains `ts` as a substring, so a substring assertion passes over ANY fields list). The pin asserts `_index_fields(ddl, "trace_ts") == (TRACE_TS_FIELD,)` — a parsed tuple comparison, not a substring. It additionally pins `IF NOT EXISTS` and the absence of `UNIQUE`. |
| **the `refs` store ASSERT was invisible behind the ledger's teaching reject firing first** | now pinned | **CLOSED at the layer it pins.** M5b (drop the count ASSERT) → `test_refs_carries_its_COUNT_assert` RED, and the ledger reject cannot mask it because the pin reads the EMITTED DDL, never a round-trip write. ⚠ But see C4: this closes *emission*, not *behaviour*. |

---

## 7 — The ORACLE change: ACCEPT (the lead's question, answered by mutation)

`loremaster/tests/_message_fakes.py` gained two calls into production policy —
`MessageLedger._reject_oversize_pointers` in `send` and `MessageLedger._reject_oversize_note`
in `ack`. Repo law says an oracle change is contract-author + adversary work. My verdict is
**ACCEPT**, on four legs, three of them measured.

**(a) It is NECESSARY, and the mutation sets are DISJOINT AND MIRRORED.** Over both consumer
suites at once (`test_message_ledger.py` + `test_comms_tool.py`, 1072 tests):

| mutation | RED | which |
|---|---|---|
| revert the FAKE's `_reject_oversize_pointers` call | **4** | every `[fake-*]` parametrisation |
| remove PRODUCTION's `_reject_oversize_pointers` call | **4** | every `[real-*]` parametrisation |
| revert the FAKE's `_reject_oversize_note` call | **1** | `…ack_NOTE_is_REJECTED_at_the_BODY_cap[fake]` |

The contract is parametrised real/fake, so without the oracle change the `[fake-*]` half of
DD-3 is simply unpinned. That is the definition of in-scope.

**(b) It CANNOT introduce divergence — proved, not inspected.** The rules are ONE
implementation, so the only remaining divergence surface is call-site POSITION and ARGUMENTS.
I diffed both `send` bodies: the call sits in the IDENTICAL position in each (immediately
after the body cap check, immediately before the empty-recipient check) with the IDENTICAL
argument expression `thread=thread, task_id=task_id, refs=list(refs) if refs is not None
else []`. Same for `ack` (first statement, before the empty-`seqs` early return in both).
There is no input the fake now accepts that production rejects, or vice versa.

**(c) It attacks #190's CLASS correctly.** #190 exists because the fake's
`EmptyRecipientSetError` prose was a CLONE that drifted. Routing the NEW policy through the
real staticmethod is the one-implementation rule applied where the drift came from, not a
second copy. (The #190 divergence itself is untouched and still real: production's
`EmptyRecipientSetError` still says *"is a caller error, not a broadcast"* while the fake's
does not. It is now unreachable from the surface — the dispatcher intercepts the solo-broadcast
path first — but it is still there. Correctly ledgered to packet 05.)

**(d) THE HONEST CAVEAT the brief asked for.** The satisfiability receipt holds for BOTH
consumer suites — `test_comms_tool.py` is fully green with the change, and stayed green under
all three mutations above. But **`test_comms_tool.py` moved ZERO tests in all three**: it
exercises none of the new policy. So the change is *satisfiable* for both suites and
*discriminating* in only one. That is a scope fact, not a defect — but "it holds for both
suites" should be read as "it breaks neither", not "both check it".

---

## 8 — Mutation proofs (13 mutations)

All run in an isolated scratch tree built by the blessed tool:

```
./scripts/scratch_copy.sh /home/ejprice/scratch/ca2/tree
PROVENANCE  loremaster.__file__ = /home/ejprice/scratch/ca2/tree/loremaster/loremaster/__init__.py
```

(#140's three poison modes closed by the tool; provenance asserted and printed. The real
repo tree was NEVER mutated — `git status --short` clean throughout, no `stash`, no
`checkout --`, no `reset`, no bare `commit`.) Control run of the key pins in the copy, before
any mutation: **7 passed**.

| # | mutation | expected | measured |
|---|---|---|---|
| M1 | remove `anyio.CancelScope(shield=True)` | new anyio pin RED | **RED** — `test_a_scope_cancelled_dispatch_STILL_writes_its_row` |
| M1′ | *same mutation*, old asyncio pin | GREEN (the KNOWN BOUND's claim) | **GREEN — 1 passed** |
| M2 | delete the `trace_ts` index line | ts-index pin RED | **RED**, 1 failed / 16 passed |
| M3a | revert `next_limit` to the bare remainder | PEEK leg RED | **RED**, cap + control legs green |
| M3b | drop the `min(…, _MAX_DRAIN_LIMIT)` clamp | CAP leg RED | **RED**, peek + control legs green |
| M4 | `thread` → `option<string>` | DD-2.b RED | **RED, both legs** (spec + emitted DDL) |
| M5a | delete the `refs[*]` element row | element pin RED | **RED**, 1 of 5 |
| M5b | drop the `refs` count ASSERT | count pin RED | **RED**, 1 of 5 |
| M5c | drop the `task_id` ASSERT | label pin RED | **RED**, `[task_id]` only |
| M5d | give `ack_note` the POINTER cap | note pin RED | **RED**, 1 of 5 |
| M6 | insert an `await` after `ledger.drain()` | DD-4.b RED | **RED**, 1 of 2 |
| M7 | remove the `_TRACE_BY_TOOL_CAP` slice | cap pin RED | **RED**, control green |
| M8/M8b/M9 | the oracle legs | see §6 | see §6 |

**M1/M1′ is the headline and it reproduces the builder's own asymmetry exactly.** With the
shield removed, the new pin goes RED and the committed asyncio pin stays GREEN — which
independently confirms BOTH that the new pin discriminates AND that every factual claim in
the KNOWN BOUND docstring is true. Every schema mutation killed exactly its OWN pin and
nothing else, so none of the five is riding a sibling.

**One thing the committed suite does NOT execute, which I did.** `test_the_shielded_write_is_BOUNDED`
compares two CONSTANTS (`_TRACE_EMIT_TIMEOUT_SECONDS` vs `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS`)
and never runs the timeout path. I drove it:

```
emit=5.0  txn_deadline=2.0                          (the ordering claim is TRUE)
hanging emission CUT OFF after 0.40s (patched constant); logged=['trace.emit.failed']
the dispatch's own result survived; POSITIVE CONTROL: a fast emission is not cut off
3 passed
```

So `anyio.fail_after` nested INSIDE the shield fires correctly, its `TimeoutError` IS caught
by the seam's `except Exception`, and the failure is LOUD in the server log. The mechanism
works — it is just unpinned (R4).

---

## 9 — What SURVIVED attack (stated, because a NO-GO that lists only defects is a bad map)

- **All six gate numbers.** Re-run independently; every one reproduced (§0).
- **The cancellation shield**, including the discrimination asymmetry and every factual claim
  in its KNOWN BOUND docstring (§7 M1/M1′), plus the deadline mechanism end-to-end.
- **The drain elision fix's two shipped legs** — each dies to its OWN half (§7 M3a/M3b).
  The defect in §1 is a THIRD cell, not a failure of these two.
- **The whole schema delta on a DIRTY store**, with a positive control and per-field
  discrimination (§3.1). This was the #107-shaped risk and it is clean.
- **The EXPLAIN receipt**, control included (§3.2).
- **The `trace_ts` free-window argument**, corroborated from code history (§3.3).
- **The corrected instructions clause.** *"lore does not report that state back to you yet,
  so track it yourself"* is TRUE: `MessageLedger.awaiting_answer` and `WaitingOnAnswer` have
  ZERO production consumers outside `messages.py` itself. Verified by grep over
  `loremaster/loremaster/`.
- **`TraceSummary`'s served surface.** I confirmed the docstring is genuinely SERVED —
  it lands in the pydantic JSON-schema `description`, both standalone and nested under
  `IndexStatusSummary.$defs`, and `window_days` is a served property. The "WINDOWED" pin is a
  real served-surface pin, not a pin on dead prose.
- **The rewritten `refs` description.** The old one said *"the content lives in what you name
  here"* — the bypass, verbatim. The new one says *"the content lives in the report or
  finding you point AT, never inline here"*, and every number in it is f-string-interpolated
  from the constant. Correct.
- **The pointer-bound bypass I went looking for and did NOT find (§9's last bullet).** The ledger validates the
  SUPPLIED `thread`, but the store validates the EFFECTIVE one, which defaults to `session` —
  so a >256-char session would produce a raw engine ASSERT instead of the teaching reject.
  It is NOT reachable: `agent.session` carries `_IDENTIFIER_CHARSET_ASSERT`
  (`^[a-z0-9][a-z0-9_-]{0,63}$`, ≤64 chars) and a sender must be registered. Closed.
- **`ad8153b`'s disclosed scope**, which I verified matches deviation G2 exactly.
- **`_comms_resolve_recipients`' correctness**: duplicate `to` entries still fan out to the
  ledger's own deduper as before; the roster→probe fallback classifies retired vs unknown
  correctly; a name registered inside the race window is accepted, not spuriously rejected.

---

## 10 — RESIDUALS (individual verdict per row; "all remaining are X" is banned)

| # | residual | verdict |
|---|---|---|
| R1 | `config.py`, the `DEFAULT_TELEMETRY_WINDOW_DAYS` comment: **"the read is windowed rather thana full-table scan"** | **TYPO, real, cosmetic.** Code comment, not served. One-character fix; worth doing in the same touch as C5. |
| R2 | The SERVED `TraceSummary` schema description literally contains ``:data:`_TRACE_BY_TOOL_CAP` `` where the number 20 was available. Verified served (§9). Every sibling description in this same wave interpolates its constant (`{_MESSAGE_REFS_MAX_COUNT}` etc.). It is the only `:data:` on a private name inside a served MODEL docstring in `server.py`. | **REAL, LOW.** Does not lie; fails to inform an LLM that cannot resolve the symbol. Fix: f-string the docstring or restate as "the busiest 20". |
| R3 | `IndexStatusSummary.traces` uses `default_factory=TraceSummary`, so the published JSON schema advertises `window_days` `default: 14` — a hardcoded config value in a served schema. | **REAL, LOW, NOT reachable in serving.** `_build_index_status` always populates it. Only bare constructions (unit tests) hit the default. Flagged because it is a served number that a non-default `telemetry.aggregate_window_days` would contradict. |
| R4 | `test_the_shielded_write_is_BOUNDED` compares two CONSTANTS; nothing committed EXECUTES the timeout path. | **MISSING PIN, not a defect.** I proved the mechanism works (§8). Recommend adopting my probe: hang the recorder, patch the constant down, assert cut-off + `trace.emit.failed` logged + the dispatch's own result preserved, with the fast-emission control. |
| R5 | `TestMessageSchemaLive` applies DDL via `run(connection, generate_message_ddl())` — a MULTI-STATEMENT string through the SDK's `query()`, which validates **statement[0] ONLY** (store reference §3). A later DDL statement could fail silently and the pin would run against a partially-applied schema. | **PRE-EXISTING, not this wave's; REAL.** Surfaced per scope law. Every live pin in that class inherits it. `execute_transaction` is the prescribed seam. |
| R6 | `_comms_resolve_recipients`' docstring: *"The happy path costs ONE store read, not N."* For a SINGLE-recipient send the old code cost one keyed `get_agent`; the new code costs one session-wide `roster()`. | **OVER-CLAIM BY OMISSION, LOW.** Query COUNT is equal at N=1, cost is not. True and valuable for N>1. |
| R7 | My concurrency selector collected **11**; the builder reported **14**. | **NOT a discrepancy in outcome** — both 0 failures over 20 runs. Different `-k`. Disclosed so nobody reads 11 and 14 as the same measurement. |
| R8 | The `note` tool param bounds only its **'ack'** clause at `_MESSAGE_BODY_MAX_CHARS`. The same param also serves `heartbeat` (`last_note`) and `brief_publish`, which remain unbounded at the ledger. | **DESCRIPTION IS ACCURATE AS SCOPED.** The unbounded siblings are a PRE-EXISTING question this wave did not create and did not claim to close. Surfaced, not fixed; the operator owns whether they get the same treatment. |
| R9 | `message.session` and `to.session` carry no store ASSERT (unlike `agent.session`). | **NOT A GAP — verified closed** (§9, last bullet). Recorded so the next reader does not re-derive it. |
| R10 | HEAD moved `0a0b38d` → `09f8d3b` mid-audit. | **BENIGN, disclosed.** Docs-only; `git diff --stat 0a0b38d..HEAD -- loremaster/` is empty; the 12-file MD5 fingerprint is unchanged. |
| R11 | The DD-1.c retention sweep is named in the `trace_ts` pin's rationale ("the retention sweep a later packet lands") but is not itself ledgered in this wave. The builder's report §6 R3 says filing it is the lead's. | **OPEN, NOT MINE.** Flagged because the free-window argument for `trace_ts` explicitly rests on that second consumer existing; an unfiled consumer weakens the justification retroactively. |
| R12 | I wrote probe scratch under `/home/ejprice/scratch/ca2/**` (new subdirectory only). | **DEVIATION, disclosed.** The brief marks `/home/ejprice/scratch/**` WITHHELD; I read nothing pre-existing there and created only `ca2/`. The scratch copy (`ca2/tree`) can be deleted; nothing in the repo depends on it. |
| R13 | The parallel sweep reported three further items I did NOT independently verify: DD-1.b's wrong-build-3 rider prescribed *"two reads across a monkeypatched clock"* and the shipped pin (`test_the_cutoff_is_computed_PER_CALL_never_cached`) uses a real clock plus `asyncio.sleep(0.01)` instead — a mildly timing-dependent substitution, undisclosed as a deviation. | **UNVERIFIED BY ME, plausible.** Reported so the lead can route it; I assert nothing about it. |
| R14 | Same source: DD-3.c requires the teaching reject to name *the fix*, and the `thread`/`task_id` branch of `MessageLedger._reject_oversize_pointers` ends *"is a LABEL, not content"* with no next move (the `refs` branches do carry one). | **UNVERIFIED BY ME as a rider breach**, but the text is checkable in one read and the asymmetry is real on its face. Lead's call. |
| R15 | Same source: cold R10's CORRECTED re-open trigger landed in neither the 06 packet file nor the findings ledger, so the retired (known-false) trigger is what survives in the record. | **UNVERIFIED BY ME.** If true it is the same shape as C6 — a correction with no home. Worth one grep by whoever owns R10. |
| R16 | I did NOT run the FK-5 consumer battery myself (C2). | **DELIBERATE.** An auditor running the acceptance gate it is auditing is the builder-grades-own-work shape; and my writable set is one file. Flagged as a gap in MY coverage, not resolved. |

---

## 11 — Method notes

- **lore tools:** the `mcp__lore_lore__*` set was ToolSearch-loaded per the brief. I fell
  back to `grep` for the sweeps in §4, §5 and §8 **and say so**: every one of them is a
  non-symbol textual seam (prose inside docstrings and string literals) or a
  rename-exhaustiveness question where one missed site is exactly the defect — CLAUDE.md's
  two sanctioned fallback cases. Symbol-level questions (consumer sets for `record_trace`,
  `awaiting_answer`, `_MESSAGE_FIELD_SPECS`) were answered by grep as well, over
  `loremaster/loremaster/` only, because they were exhaustiveness questions about a possibly
  deleted-and-recreated seam; a graph answer would have been the better first call and I did
  not make it. Filed as a friction signal here rather than left silent.
- **Probe discipline:** every negative result in this report is paired with a positive
  control (§1.3 stamping-converges, §3.1 A4 + A0, §3.2 unwindowed TableScan, §7 M1′ and the
  fast-emission control). Where a probe's own instrument could have lied, I said which leg
  proves it could see a success.
- **Git safety:** no `stash`, no `checkout --`, no `reset --hard`, no `clean`, no bare
  `commit`. Every git command named its paths. The repo working tree is byte-identical to
  how I found it.
- **Delegation, disclosed, and what it changed.** I ran a parallel read-only sweep agent over
  both ruling docs. **It returned AFTER my first draft and it independently reached C6's third
  instance (DD-3.c's dirty-store rider) and C4 (the `1a6010f` scope leak) — arrived at separately,
  which is why I record them as corroborated rather than merely claimed.** It also raised the
  `ack_note`/`drain` hazard (C3), Q5's docstring rider, cold R1(2)'s p50 instrument, Q7/R3's
  pre-DDL counts, and the FK-5 battery gap. **A subagent's finding is a claim, not a fact:** I
  re-derived every one of them myself before it entered this report — C3 by a fresh live probe
  with its own controls (§3.0), the rest by direct measurement over the tree (§2, §6.0). Nothing
  here rests on its numbers. Its remaining rows (a mildly timing-dependent substitution in
  DD-1.b's wrong-build-3 pin; DD-3.c's `thread`/`task_id` reject text carrying no next move;
  cold R10's corrected re-open trigger landing nowhere) I have NOT independently verified and
  therefore do not assert — they are worth the lead routing to a follow-up, flagged as unverified.
- **Dates:** every measurement in this report was taken **2026-07-25** against baseline
  `0a0b38d` (code identical at `09f8d3b`). Nothing here is a present-tense claim about a
  later tree.
