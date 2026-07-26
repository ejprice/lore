# REPORT-coldaudit-03b-1 — COLD REFUTE AUDIT of packet 03b's build

brief-base v6 read

## SUMMARY BLOCK

- **VERDICT: NO-GO for deploy — GO after ONE fix wave.** Three confirmed defects, all in the
  SERVED-ENGLISH layer (the class this repo's own law names as where green-at-gate defects live).
  The store slice, the schema delta, the ordinal mint and the telemetry seam all SURVIVED attack.
- **state:** done. Audited `git diff f3971bd..84756b6 -- loremaster/loremaster/`; verified the
  production diff `84756b6..HEAD` is **EMPTY**, so the code audited IS the code at HEAD `fc3bb7b`.
- **gates, independently re-run by me 2026-07-25 (not inherited):** full suite `uv run pytest -n
  auto -q` → **6532 passed, 17 skipped, 3 xfailed in 200.20s** · `./scripts/typecheck.sh` → **0
  errors, all three members** · `uv run ruff check .` → **All checks passed** · skill suite →
  **117 passed** · concurrency block, **5 consecutive** → **14 passed × 5, zero failures**. Every
  builder gate claim reproduces at the claimed number.
- **confirmed defects, ranked:**
  1. **C1 (HIGH)** — `_render_comms_drain`'s elision re-ask is WRONG on the `peek` path: obeying
     the served instruction re-serves rows already read and leaves rows UNREACHABLE. Measured.
  2. **C2 (MEDIUM)** — that same re-ask is UNCLAMPED, so it names a `limit` the action silently
     overrides — diverging from the `fleet` precedent in the same file and from DESIGN-LAW §1.2 as
     quoted in this file's own `_MAX_FLEET_LIMIT` comment. Measured.
  3. **C3 (LOW-MED)** — `_trace_params_hash`'s docstring claims the digest is *"the ONLY thing that
     crosses from arguments into the row"*. FALSE: `agent`/`session`/`action` argument VALUES are
     written verbatim. The file contradicts itself 100 lines apart; no gate can see it.
- **decisions needed:** (a) approve the C1/C2 fix + its two missing fixtures (proven drop-in safe:
  **1211 passed, 0 failed** with the full fix applied); (b) rule on the trace write being AWAITED
  on the wire path (latency coupling, §R3); (c) confirm `SELECT count() FROM trace` is 0 on
  production before the deploy builds the new `(agent, ordinal)` index (I am forbidden `:18500`).
- **receipt pointers:** §2 gate tails · §3 C1/C2 measured probe + positive control · §4 C3 ·
  §5 the four mutation proofs (incl. sharing PROVEN by mutation) · §6 attacks that FAILED ·
  §7 the four disclosed deviations adjudicated · §8 RESIDUALS, one verdict per row.

---

## 1 — Method, posture, provenance

Read in order: `~/.claude/orchestration/brief-base.md` (v6), then
`docs/reference/surrealdb-31-capabilities.md` (§0, §1.1–§1.7, §2, §5, §6 — cited below, never
re-transcribed). I formed my view of the diff BEFORE opening `REPORT-builder-03b-1.md`.

**Tooling honesty (base §4).** The lore MCP tools were loaded via `ToolSearch` but I fell back to
`grep`/`Read`/`git diff` for essentially all navigation. The reason is the documented-legitimate
one: an audit of a specific 5-file diff is a *cross-cutting map* question plus *non-symbol textual
seam* work (served prose in string literals, DDL statement text, fixture values) — two of the three
cases this repo's dogfood protocol keeps for grep. Saying so out loud. **No friction row filed** —
this is the protocol working, not a lore weakness.

**Tree discipline.** I made ZERO edits to the repo (my only repo write is this file). Mutation
proofs ran in an isolated `./scripts/scratch_copy.sh` copy, whose provenance the tool asserted:

```
imports resolve INSIDE the copy:
loremaster  -> /home/ejprice/coldaudit03b-scratch/loremaster/loremaster/__init__.py
```

The live probe (§3) imported the REAL tree deliberately (it is a read-only measurement of shipped
behaviour, not a mutation), and printed its provenance receipt:

```
PROVENANCE loremaster.__file__ = /home/ejprice/PycharmProjects/lore/loremaster/loremaster/__init__.py
```

No `git stash` / `checkout --` / `reset --hard` / `clean` was used (finding #189). All store work hit
spike-surreal **`ws://127.0.0.1:18000`** on throwaway `unique_database()` DBs; **`:18500` was never
opened**.

⚠ **I could not delete the scratch copy** — `rm -rf /home/ejprice/coldaudit03b-scratch` was denied by
the permission layer. **It is restored byte-exact** (md5 of both mutated files matches the real tree:
`server.py 2dfcf7de0daca4e06fa1170c1214883d`, `surreal_schema.py 3cd43ecf3a47d38f399cd453145fa720`)
and is inert, but the lead should reap it.

---

## 2 — Gate tails, re-run by me (ground truth, not inherited)

Measured 2026-07-25. A green claim needs a passed-COUNT, so here they are.

```
$ uv run pytest -n auto -q
6532 passed, 17 skipped, 3 xfailed, 1 warning in 200.20s (0:03:20)

$ ./scripts/typecheck.sh
Success: no issues found in 27 source files   / typecheck: lorescribe OK
Success: no issues found in 32 source files   / typecheck: loresigil OK
Success: no issues found in 149 source files  / typecheck: loremaster OK

$ uv run ruff check .
All checks passed!

$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
117 passed in 14.90s

$ 5× (TestConcurrentSendsMintDistinctSeqs + TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner
      + TestTheOrdinalIsMintedByTheStore)
14 passed in 6.71s / 7.26s / 6.15s / 7.54s / 8.28s     -> 0 runs with failures
```

**Every builder gate claim reproduces.** (I ran 5 concurrency rounds, not 20; the builder's 20 are
corroborated, not replaced.)

---

## 3 — C1 + C2: the drain elision's re-ask (CONFIRMED, measured)

`AppContext._render_comms_drain` emits, on elision:

```python
remainder = result.total_pending - shown
if remainder > 0:
    lines.append(render_line(
        "+{more} more unread — re-run with limit={next_limit}",
        more=remainder, next_limit=remainder))
```

Its own docstring justifies `next_limit=remainder` thus: *"a non-peek drain stamps exactly the served
window and stamped rows never re-serve — a `shown + more` re-ask would name rows that CANNOT come
back."* **That justification is conditioned on the non-peek path only.** `MessageLedger.drain` with
`peek=True` stamps NOTHING and always windows `pending[:limit]` from the OLDEST seq — so on the peek
path the re-ask names the same head again.

### The probe, with a POSITIVE CONTROL on the same instrument

Live `MessageLedger` + `AgentRegistry` on spike-surreal, driving the REAL `AppContext._comms_drain`
handler (not just the render), 60 pending messages:

```
--- CONTROL (stamping drain — the probe CAN see a correct re-ask) ---
drained 20 of 60 pending
+40 more unread — re-run with limit=40
  -> obeying it served seqs [20 … 59], count 40, overlap with the first window: 0    ✅ CORRECT

--- C1 (peek drain — same render, same arithmetic) ---
peeked 20 of 60 pending — nothing stamped; re-run without peek=true to mark them seen
+40 more unread — re-run with limit=40
  -> obeying it served seqs [60 … 99], count 40
  -> overlap with the already-peeked window: 20
  -> pending set size: 60 ; rows UNREACHABLE at the advertised limit: 20             ❌ WRONG

--- C2 (elision re-ask vs the action's own cap; _MAX_DRAIN_LIMIT = 50) ---
260 pending, drain 20:
+240 more unread — re-run with limit=240
  -> obeying limit=240 actually served 50 rows                                       ❌ WRONG
```

**C1.** Half of what the served instruction returns is what the caller just read; a fifth of the
pending set cannot be reached at the advertised limit at all. The correct peek re-ask is
`shown + more` (= `total_pending`), which is exactly the value the docstring rules OUT — correctly,
for the other branch. The peek branch was reasoned about carefully for the header line and for the
`ACK REQUIRED` trailer (*"renders on STAMPING drains only"*) and then **missed for the elision**.

**C2.** `_render_comms_fleet`, in the same class, does `next_limit = min(total, _MAX_FLEET_LIMIT)`.
`_render_comms_drain` does `next_limit=remainder`, unclamped. The `_MAX_FLEET_LIMIT` comment states
the governing rule verbatim: *"a counted elision's re-ask value is always honest AND clamped to this
ceiling (DESIGN-LAW §1.2), never an unbounded 'ask for everything'."* Drain breaks it. Under the
CONSUMER LAW's trust doctrine a served instruction the system silently overrides is a trust defect,
not a cosmetic one.

### Why both were green at every gate — the fixture receipt

The maximum `total_pending` fixture value **anywhere in the test tree is 10**, against a cap of 50:

```
$ grep -rno "total_pending=[0-9]*" loremaster/tests/*.py | sed 's/.*=//' | sort -n | uniq -c
   16 1   5 2   1 3   1 4   3 7   1 9   1 10
```

That is the small-N monoculture this repo has now been bitten by four times: **no fixture can
distinguish the shipped build from a clamped one**, and none combines `peek=True` with a remainder.
Proven, not asserted — see MP-B/MP-C in §5.

### Recommended fix (4 lines, one function) — and it MUST ship with pins

```python
next_limit=min(result.total_pending if result.peeked else remainder, _MAX_DRAIN_LIMIT),
```

plus the two fixtures that were never written: (i) `total_pending > _MAX_DRAIN_LIMIT`, (ii) a
`peeked=True` result WITH a remainder, asserting the re-ask is reachable. Per repo law an
audit-caught defect CLASS becomes an invariant, so the honest pin is the property, not the literal:
*a drain's advertised `next_limit`, fed back through `_comms_drain`, must serve every row the elision
line counted.* A round-trip pin, not a string compare.

---

## 4 — C3: a FALSE privacy claim in `_trace_params_hash`'s docstring

`_trace_params_hash` (server.py) states:

> "The digest is the ONLY thing that crosses from arguments into the row, so it is also the whole
> privacy boundary: bodies, briefs and queries pass through it and nowhere else."

**The first clause is false.** `TracingFastMCP._record_tool_trace` harvests three argument VALUES and
writes them verbatim into `trace.agent` / `trace.session` / `trace.action`:

```python
declared = {key: value for key, value in ((key, arguments.get(key)) for key in _TRACE_DECLARED_KEYS)
            if isinstance(value, str)}
```

`_TRACE_DECLARED_KEYS` = `("agent", "session", "action")`. The comment above that constant describes
the harvest correctly, so **the same file contradicts itself ~100 lines apart**. The second clause
(*bodies/briefs/queries*) IS true, and the covering pin
(`TestParamsHashIsTheRuledRecipeAndLeaksNothing::test_no_raw_parameter_content_reaches_the_row`) is
honest — it asserts only that hostile BODY fragments are absent, with a genuine present-in-input
control. **So no gate can see the over-claim**: it is precisely the "prose restated beside the
mechanism rather than derived from it" class, in the packet that added the mechanism.

**Why it matters beyond pedantry:** a future engineer reading "the whole privacy boundary" concludes
no argument value is ever stored plaintext, and adds a fourth `_TRACE_DECLARED_KEYS` entry (or a
render of `trace.agent`) believing it costs nothing. Fix: delete the "ONLY"/"whole privacy boundary"
framing and say what is true — *bodies, briefs and queries reach the row only as this digest; the
three DECLARED identity keys are stored verbatim by design.*

---

## 5 — Mutation proofs (mine, in the provenance-asserted scratch copy)

| # | mutation | result | what it proves |
|---|---|---|---|
| **MP-A** | `_define_sequence` (the SHARED DDL emitter) → emit `{name}_MUTATED` | **8 failed / 4 passed**: 4 × `test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs[real]` **AND** 4 × `test_trace_telemetry.py::TestTheOrdinalIsMintedByTheStore` | **SHARING, PROVEN BY MUTATION.** The trace ordinal genuinely rides the SAME sequence mechanism as `message.seq` — one edit moves both callers. Not routing-wearing-the-shared-name. The 4 that stayed green are the `[fake]` legs, which do not execute DDL. |
| **MP-B** | add the missing C2 clamp (`next_limit=min(remainder, _MAX_DRAIN_LIMIT)`) | **1015 passed, 0 failed** (`test_comms_tool` + `test_comms_promise_registry` + `test_comms_render_architecture` + `test_comms_wiring`) | No pin discriminates the clamp **in either direction**. The C2 fix is drop-in safe against the certified contract. |
| **MP-C** | the FULL proposed fix (peek → `total_pending`, non-peek → `remainder`, both clamped) | **1211 passed, 14 skipped, 0 failed** (adds `test_message_ledger`) | Same, for C1. The fix wave is a one-hunk change that breaks nothing. |
| **MP-D** | (read-only control) hostile body through `render_fenced` | a 5-backtick run inside the body produced a **6-backtick** wrapper fence; embedded `#99 [directive] evil→you` and `ACK REQUIRED:` lines stayed INSIDE the fence | The hostile-render leg holds. |

Restored byte-exact from `cp -a` CONTENT backups; md5 verified against the real tree (§1).

---

## 6 — Attacks that FAILED (the build held — stated because a cold audit that only lists hits is not an audit)

- **Telemetry seam REACH.** I verified in the INSTALLED `mcp` package that
  `FastMCP._setup_handlers` registers the **bound** `self.call_tool`
  (`self._mcp_server.call_tool(validate_input=False)(self.call_tool)`), so the subclass override IS
  the wire path by construction. And coverage is a genuinely **CHECKED variable**, not a hardcoded
  name: `TestCoverageIsACheckedVariable` asserts `set(_MINIMAL_ARGS) == {t.name for t in await
  mcp.list_tools()}` **with a non-vacuity guard**, parametrises every registered tool through the
  funnel for both the success and failure cells, and registers a **synthetic post-construction
  extension tool** so the "tools the wrappers never met" leg is real. `build_mcp_server` is pinned to
  construct the subclass. This was the attack I expected to land and it did not.
- **Schema delta (the #107 shape).** Every clause matches store reference §1.1: `_define_field` →
  `OVERWRITE`; `_plain_index`/`_unique_index`/`_define_sequence`/`_define_table` → `IF NOT EXISTS`;
  the `to` RELATION table → `OVERWRITE`. All five new `trace` columns are `option<>` and the two
  widened ones (`hit_count`, `session`) went `int`/`string` → `option<>` — §1.4's rule for a new
  field on a possibly-populated table, obeyed. **And the dirty-store path is genuinely pinned**:
  `TestTheTraceDeltaMigratesADirtyStore` applies the OLD field specs one statement per `query()`,
  writes a legacy-shaped row, then runs the REAL `ensure_ready` and asserts both the new write lands
  and the legacy row survives — the §1.6 blind spot, closed for this slice.
- **B-OBL-1.** Verified by execution, not by reading: `_INSTRUCTIONS` splits into **8** paragraphs;
  the ruled comms paragraph is at **index 6**; the MEMORY paragraph at index 5 is byte-unchanged in
  the diff and still carries `action=register`, `action=heartbeat`,
  `action=brief_get/brief_publish/brief_ack`, `action=fleet` (plus `action=rollup`). Held.
- **Hostile input.** `safe_str` is `sanitise_line(str(value))` — a sanitising mint — so `refs`
  (my initial suspicion, since it is the one render field not visibly wrapped in `sanitise_line`) IS
  laundered. Bodies are ALWAYS fenced, with the fence sized past embedded runs (MP-D). Refuted.
- **The R3 bound on `awaiting_answer` is a true semantics-identical superset.** SQL admits
  `in.thread IN {question threads} AND in.seq > min(question seq)`; the unchanged Python filter needs
  `answer_thread == question.thread AND answer_seq > question_seq`, and `question_seq ≥ min` so
  `answer_seq > question_seq ⇒ answer_seq > min`. No row the loop would accept is excluded.
  `thread` is a REQUIRED `string` in `_MESSAGE_FIELD_SPECS`, so the `or ""` fallback is unreachable
  and cannot open a NONE-vs-`""` gap. The builder's EXPLAIN receipt is **honest** — it states in its
  own words that the traversal conjuncts sit in the post-index Filter in BOTH plans and that the bound
  does not change index ACCESS. No over-claim.
- **Broadcast never reaches a retired agent.** `AgentRegistry.roster` filters
  `agent.status != STATUS_RETIRED`, so `_comms_send`'s docstring claim is true and the
  undrainable-forever hazard the explicit path rejects cannot re-enter via broadcast.
- **Shape rejects fire before any store touch.** The disallowed-param loop, the `limit` range reject
  and the new `set_status` closed-vocabulary reject all run BEFORE `agent_registry.touch`. The
  `set_status` reject NAMES the one legal value, and `set_status` genuinely does not mutate the agent
  status row (`messages.py` uses it only as `question = set_status == 'input_required'`), so that
  served sentence is true.
- **Illegal `grade`** is rejected by the ledger with a teaching `IllegalMessageGradeError` naming the
  legal set — not by a raw schema ASSERT.

---

## 7 — The four disclosed deviations, adjudicated independently

**D1 — `_render_comms_drain` takes `agent_name`/`limit` and `del`s both. → PARTLY WRONG. The dead
`limit` is the fingerprint of C2.** The builder's reading ("the elision's honest arithmetic is the
REMAINDER, so `limit` is not a comparand") is right about `limit` and wrong about the conclusion: the
comparand the render is missing is not `limit` but `_MAX_DRAIN_LIMIT`, and the sibling render
(`_render_comms_fleet`) consumes exactly that ceiling at exactly this line. So the contract's fixed
signature is not pure over-specification — **a parameter went unused because a clamp went unwritten**,
and the builder adjudicated it as harmless without testing the branch. `agent_name` genuinely is
unused and harmless. **Recommendation: keep the signature, land the clamp; do not amend the contract
to delete `limit` until the fix wave has settled what the render must consume.**

**D2 — the retired-recipient reject is a `ValueError`. → ACCEPTED.** §B2.3 says "teaching reject",
not which class; the pin is `pytest.raises(Exception)` + text. `ValueError` matches every other comms
teaching reject in the dispatcher, so this is the CONSISTENT choice, not a shortcut. The message names
the recipient, says "retired", says retirement is terminal, and teaches the recovery (send to the
respawned name). No change needed.

**D3 — the skew block is read BEFORE the ledger drain. → CORRECT, and I could not break it.** I looked
for an ordering that loses or double-serves. There is none reachable: a skew-read failure aborts before
`drain` is called, so nothing is stamped and nothing is lost; a drain failure leaves the skew read as a
pure read with no side effect. The reverse order carries a REAL loss shape (stamp, then raise in the
skew read → messages consumed that nobody read), and `peek` does not change this because `peek` stamps
nothing either way. **The builder's reason is sound and the order it chose is the safe one.** It is
unpinned — worth a one-line ordering pin in the fix wave, since nothing currently stops a future
refactor from swapping it.

**D4 — `git stash` in a shared tree. → NO LOSS, independently confirmed by me.** `git diff
84756b6..HEAD -- loremaster/loremaster/` is **EMPTY** (the production code is exactly what I audited);
the sibling eval-author commits `0f662c8`, `35ee643`, `3dcd182` are all present in the log; the tree
was clean at `00a36d1` when I started. Nothing was swept. **The habit remains the hazard the builder
says it is** and should not be copied.

---

## 8 — RESIDUALS (one verdict per row — "all remaining are X" is banned here)

| id | file / symbol | observation | verdict |
|---|---|---|---|
| R1 | `server.py::TracingFastMCP.call_tool` | the trace write is **awaited** in `finally` on the wire path, so every served tool call pays a store round-trip before returning; a degraded store adds the retry budget (`_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS = 2.0` plus the attempt FLOOR) to EVERY call. The ruled failure posture covers the OUTCOME ("the tool call's outcome always wins") but is silent on LATENCY, and no docstring discloses it. | **DECISION FOR THE LEAD.** Not a defect against any ruling I can find — the `finally`-await is load-bearing for the cancellation leg and is pinned. But it is an undisclosed coupling of the whole tool surface to store latency. Rule it, then say it in the docstring. |
| R2 | `messages.py::MessageDrainResult.directive_pending` | computed over the WHOLE pending set by `MessageLedger.drain`, and rendered **nowhere** — the `ACK REQUIRED` trailer is deliberately window-scoped. | **DEAD AT THE SERVED LAYER, not a defect.** The typed field is pinned by the ledger contract; a drain that elides directives currently says only "+N more unread". Worth a ruling in packet 04/05 on whether the whole-set directive count should surface. |
| R3 | `surreal_schema.py` `_trace_statements` comment: *"this table is empty exactly once — now"* | I could not verify it — the brief forbids `:18500`. Supporting evidence: a repo-wide grep finds **no** `record_trace` caller outside this packet's own seam and the test tree, and the pre-packet `TraceSummary` docstring itself said the counts are 0 on "EVERY boot today". | **ALMOST CERTAINLY TRUE, UNVERIFIED BY ME.** Ask the deploy step to run one `SELECT count() FROM trace` on production before applying the DDL: if it is non-zero the new `(agent, ordinal)` index BUILDS, blocking, at boot (store reference §1.5). |
| R4 | `server.py` `to` Field description: *"a rejected send writes nothing at all"* | the caller's heartbeat row IS written by `agent_registry.touch` before the handler runs, so a recipient-resolution reject is not literally write-free. | **PRECISION ONLY, not a defect.** The intended reading (no message, no edge, no delivery) is true and is what an LLM consumer acts on. Tighten to "writes no message" if the fix wave is touching this file anyway. |
| R5 | `docs/eval/smoke_p8b.py` | shows as ` M` in the working tree at the time of this audit (a docstring/law rewrite). **Not mine** — I made zero repo edits — and not part of the audited diff. | **SIBLING WORK IN FLIGHT.** Informational; the lead should know an agent is mid-edit in the shared tree. |
| R6 | `/home/ejprice/coldaudit03b-scratch` | my scratch copy; restored byte-exact, inert. `rm -rf` was denied by the permission layer. | **REAP IT.** Nothing depends on it. |
| R7 | builder report R8 (`MessageLedger.drain` fetches ALL unstamped edges before windowing) | I re-derived it from the source and it is exactly as described. | **AGREE WITH THE BUILDER: file the findings row.** It is 03a's ledger internals and out of 03b's scope, but "an agent that never drains accumulates an unbounded read" is a real growth curve and the builder was right not to file it unilaterally. |
| R8 | builder report R10 (the two adversary reference builds live only under `/home/ejprice/scratch/**`) | unchanged; I honoured the WITHHELD set and never read them. | **STILL OPEN, and it is the citation law's own failure mode.** Two SUFFICIENT certifications rest on addresses that are unrecoverable by construction. Land the diffs or accept the loss, before the trees are reaped. |
| R9 | builder report R1 (`RuntimeWarning: coroutine '_empty_subscription' was never awaited`) | reproduces in MY full-suite run too (the "1 warning" in the tail). | **PRE-EXISTING, unrelated to 03b.** Confirmed independently, not inherited. |
| R10 | `_MAX_DRAIN_LIMIT` comment: *"50 entries with the 2000-char body cap bounds the worst-case render at a size a consumer can still use"* | arithmetic checks out (`MESSAGE_BODY_MAX_CHARS = 2000`), but 50 × 2000 ≈ 100 KB ≈ ~25k tokens in ONE response. | **A RULED VALUE, flagged not disputed.** The constant is the tunable and the clamp mechanism is not — but "a size a consumer can still use" is a claim nothing measures. If packet 06's telemetry ever shows drains at the cap, re-open it. |

---

## 9 — What I did NOT do

- **No production/test/doc edits.** This report is my only repo write.
- **No container was deployed, rebuilt, recreated, restarted or stopped.**
- **`:18500` was never opened**; `/home/ejprice/scratch/**` was never read, listed or grepped; the
  `pkt03b-tainted-corpus` tag was never checked out.
- **I ran 5 concurrency rounds, not 20** — a corroboration of the builder's 20, not a replacement.
- **I did not verify the production `trace` row count** (R3) — forbidden, and flagged as a deploy step.
