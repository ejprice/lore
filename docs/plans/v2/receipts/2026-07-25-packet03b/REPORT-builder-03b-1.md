# REPORT-builder-03b-1 — packet 03b BUILD (surface + telemetry)

brief-base v6 read

## SUMMARY BLOCK

- **state:** done-with-deviations (all deviations are DISCLOSURES, not unapproved changes)
- **verdict:** the certified 03b contract is GREEN at the exact target. Four commits, one tree.
- **gates (measured 2026-07-25 on the FINAL tree `84756b6`; the 20-run concurrency block at `74863a7`, whose only later delta is a deleted no-op noqa):** full suite **6532 passed / 0 failed / 17 skipped
  / 3 xfailed** (194s) · `./scripts/typecheck.sh` **0 errors, all three members, 149 loremaster
  source files** · `uv run ruff check .` **All checks passed** · skill suite **117 passed** ·
  20-consecutive concurrency **20/20, 14 passed each, TOTAL_RUNS_WITH_FAILURES=0**
- **deviations (each detailed in §7):** D1 the `limit`/`agent_name` kwargs on
  `_render_comms_drain` are contract-fixed and UNUSED by any served template — `del`'d, disclosed
  rather than quietly kept · D2 the retired-recipient reject is a `ValueError` (class not pinned) ·
  D3 the drain reads the skew block BEFORE the ledger drain (ordering not pinned; reason given) ·
  D4 I used `git stash` once in a SHARED working tree while sibling agents were committing — no
  loss, but a real hazard the lead should know about
- **decisions needed:** none blocking. Three items are OUTSIDE my writable set and are FLAGGED,
  not fixed: C6.9 (`test_surreal_harness.py` escalation, still unverified by anyone), the
  `comms-subsystem.md` pre-split drain row (rulings §F.4), and residual R4's pre-existing
  `RuntimeWarning` in `test_retry_seam.py`.
- **receipt pointers:** §2 what was built per ruling · §3 gate tails verbatim · §4 the EXPLAIN
  receipt (inherited row 2) · §5 the 20-run concurrency table · §6 obligations discharged ·
  §7 deviations · §8 residuals, each with an individual verdict

---

## 1 — Method and provenance

Read in the mandated order: `~/.claude/orchestration/brief-base.md` (v6), then
`docs/reference/surrealdb-31-capabilities.md` IN FULL (both pages), then
`docs/plans/v2/03b-design-rulings-r2.md` (all 1407 lines), the packet file, and
`receipts/2026-07-24-packet03b/REPORT-merged-gate-03b.md` §6/§7. The certified contract suites
were read as the specification.

**WITHHELD SET HONOURED.** Nothing under `/home/ejprice/scratch/**` was read, listed, diffed or
grepped; the `pkt03b-tainted-corpus` tag was never checked out or read; the gate's §8 reproduction
recipe was not followed. Every line of production code below was derived from the contract + the
rulings.

**Tooling honesty.** I fell back to `grep`/`Read` for essentially all structural navigation rather
than the lore MCP. The reason is mechanical, not preference: this session's tool surface exposed
the `mcp__lore_lore__*` tools only through `ToolSearch`, and the questions I needed answered were
of exactly the three kinds the repo's own dogfood protocol keeps for grep — (a) **exhaustiveness**
where one missed site breaks the build (which template literals exist, which classified strings
must be emitted byte-exact), (b) **non-symbol textual seams** (registry keys, ruled teaching
sentences, DDL statement text), and (c) **cross-cutting maps** (the whole 03b contract read as one
spec). Saying so out loud per §4 of the base protocol. No friction row filed: this is the
documented-legitimate fallback, not a lore weakness.

**Baseline re-derived, not inherited** (repo law): at `f3971bd`, `uv run pytest -n auto -q` →
`394 failed, 6138 passed, 17 skipped, 3 xfailed in 170.40s`. That corroborates the brief's entry
state exactly, and 6138 + 394 = 6532 = the target.

⚠ **A number worth stating so nobody re-derives it in a panic:** the suite COLLECTS **6552** and
PASSES **6532**. The 20-item gap is the 17 skips + 3 xfails, every one of them condition-declared
and enumerated in the merged gate's §4.5. It is not a coverage hole and not a drift.

---

## 2 — What was built, per ruling

### 2.1 The served surface (§A, B1–B15)

| ruling | where (symbol, never a line number) | note |
|---|---|---|
| B1 order + wiring | `AppContext.comms`, `AppContext._validate_comms_identities` | the shipped two-tier ladder extended with steps 2 (`to[]` charset) and 6 (`set_status`); SHAPE before the touch, DOMAIN after |
| B2.1 recipient charset | `_validate_comms_identities` | names ONLY the offender — an "one of these five is wrong" denial is not actionable for an LLM caller |
| B2.2 broadcast scope | `AppContext._comms_send` | resolves through `roster(session=agent_row.session)` — the caller's RESOLVED session, and the row-UNLIMITED membership |
| B2.3 explicit resolution | `_comms_send` | `get_agent(name, session=<caller's session>)`, always scoped; unknown → the EXISTING `_comms_enrich_unknown_agent`; retired → teaching reject |
| B2.4 closed `set_status` | `AppContext.comms` + `_COMMS_LEGAL_SET_STATUS_VALUES` | the legal set is a CONSTANT the message derives from, so a second value cannot be added without the prose following |
| B2.5 no status write | `_comms_send` (a plain touch) | the touch forwards `status`/`note` for `heartbeat` only, unchanged |
| B3 send receipt | `AppContext._render_comms_send` | committed templates; cap = the SHARED `_COVERAGE_NAMES_CAP`; remainder from the TRUE `recipient_count`; no body echo; **no thread cell** (B3.2 struck) |
| B4 drain render | `AppContext._render_comms_drain`, `_render_comms_drain_row` | whole-set counts, remainder elision, `acked_at`-keyed trailer, fenced bodies |
| B4.1/FK-6 skew at drain | `AppContext._comms_brief_skew_lines` + `AppContext._render_comms_skew_lines` | ONE assembly — READS and RENDER both — that heartbeat and drain call. Mutation-proven, §6 |
| B5 ack render | `AppContext._render_comms_ack` + `_ACK_OUTCOME_ORDER` | MEMBERSHIP, distinct+ascending, counts from DISPLAYED membership |
| B6 drain window | `config.DEFAULT_COMMS_DRAIN_LIMIT`, `CommsConfig.drain_limit`, `_MAX_DRAIN_LIMIT`, `CommsActionSpec.limit_cap` | the below-one message derives its range from the ACTION's cap |
| B7 hostile posture | `_render_comms_drain` (bodies via `render_fenced` only) | uniform; no inline-if-single-line variant |
| B8 promise instruments | the three new registry literals are emitted from the new helpers | registry GROWTH was already authored in the contract; production supplies the literals |
| B9 teaching | `_INSTRUCTIONS` comms paragraph at index 6; `lore_comms` schema descriptions | see §6, B-OBL-1 |
| B11 parked state | nothing added | no un-park anywhere in the new code |
| B12 dispatcher serves render | each handler calls its `_render_comms_*` | mutation-proven, §6 |
| B13 peek → no trailer | `_render_comms_drain` | the demand is gated on `not result.peeked` |
| B14 `{context}` cell | `_render_comms_drain_row` | REPLACE, not order-both: `task` wins, else `thread != session`, else bare |
| B15 elision arithmetic | `_render_comms_drain` | `more == next_limit == total_pending − shown` |

### 2.2 The telemetry (§B, T1–T8)

`TracingFastMCP` (`server.py`) overrides `call_tool`, delegates to `super()`, and is what
`build_mcp_server`'s single construction site now builds. `_trace_params_hash` is the ONE digest
recipe. `_TRACE_DECLARED_KEYS` is a generic PARAM-KEY rule (never a tool-name list). The schema
delta, the `trace_seq` sequence and the `(agent, ordinal)` index ride `_trace_statements`;
`SurrealStore.record_trace` gained the four keyword-only optional columns and mints the ordinal
server-side via `object::extend($content, {ordinal: sequence::nextval("trace_seq")})`.

**Store-reference citations that decided a shape** (cited, never re-transcribed):
§1.1 — fields `OVERWRITE`, sequence + index `IF NOT EXISTS`, and `ALTER` refused; §1.4 — a NEW
field on a possibly-populated table must be `option<>`, and a `DEFAULT` does not rescue it;
§1.5 — an INDEX `OVERWRITE` rebuilds and can hard-fail `ensure_ready` at boot; §2 — `CONTENT`
composes with neither `SET` nor `MERGE`, so `object::extend` is the only shape that mixes a bound
payload with a store-side mint, and `sequence::nextval` starts at **0**; §5 — gaps are REAL, so
the ordinal is an ordering key and never a count.

**#175 honoured:** this build adds NO message-scoped edge write. The only edge writes remain the
ledger's shipped `RELATE` (send) and its `UPDATE … WHERE … out = $me AND in IN $ids` (ack), which
already carries the `out` conjunct that makes it match.

---

## 3 — Gate tails, verbatim

### 3.1 Full repo suite — `uv run pytest -n auto -q`, at the FINAL tree `84756b6`

```
6532 passed, 17 skipped, 3 xfailed, 1 warning in 192.07s (0:03:12)
```

(Re-run at `74863a7` before the noqa deletion: `6532 passed, 17 skipped, 3 xfailed, 1 warning in
191.11s` — identical set, so the deletion changed nothing but the comment.)

**0 failed. Passed-COUNT present** (the "no tests ran behind a pipe" failure mode is excluded).
The single warning is residual R4 below — pre-existing, present identically in my `f3971bd`
baseline run, and not introduced by this build.

### 3.2 `./scripts/typecheck.sh`

```
Success: no issues found in 27 source files
typecheck: lorescribe OK
Success: no issues found in 32 source files
typecheck: loresigil OK
Success: no issues found in 149 source files
typecheck: loremaster OK
```

**Global mypy-zero, which packet 03b OWNS, is discharged in full.** The `149 source files` is the
whole tree including tests (`loremaster/loremaster` 56 + `loremaster/tests` 93), so this is not a
zero that quietly excluded the test tree — the same check the merged gate ran.

### 3.3 `uv run ruff check .`

```
All checks passed!
```

### 3.4 Skill suite

```
$ cd skills/lore-deploy/scripts && uv run python -m pytest -q . ../tests
117 passed in 14.86s
```

---

## 4 — The EXPLAIN receipt (03a-2 delta row 2)

**Question, as the delta poses it:** does the existing `(out, seen_at)` index serve the `out`
prefix — and therefore does the decision rule *"not served ⇒ a `to_out` plain index in the SAME
commit"* fire?

**Answer: it IS served. The rule does NOT fire. No extra index shipped.**

Probed on **spike-surreal `ws://127.0.0.1:18000`** (the TEST store; `:18500` was never touched),
engine **3.2.1**, on a throwaway database carrying the real `generate_agent_ddl()` +
`generate_message_ddl()`. Both the pre-R3 statement and the shipped bounded one plan identically
at the access layer:

```
--- UNBOUNDED (pre-R3) ---            --- BOUNDED (R3, shipped) ---
IndexScan                              IndexScan
  index:     to_out_seen_at              index:     to_out_seen_at
  access:    [agent:aaaa…]               access:    [agent:aaaa…]
  direction: Forward                     direction: Forward
Filter                                 Filter
  in.sender != agent:aaaa…               in.sender != agent:aaaa… AND
                                         in.thread INSIDE ['wave7'] AND in.seq > 0
```

Two CONTROLS, so the reading is discrimination and not a blind instrument:

```
out-only control:               IndexScan to_out_seen_at, access [agent:aaaa…]
drain shape (out + seen_at):    IndexScan to_out_seen_at, access [agent:aaaa…, NONE]
```

The control pair shows the SAME index taking a one-column prefix access and a two-column full
access, which is exactly the prefix-serving property in question.

**What the bound does and does not buy, stated honestly:** the traversal conjuncts
(`in.sender`, `in.thread`, `in.seq`) sit in the post-index `Filter` in BOTH plans — no `to`-local
index can serve a predicate that dereferences through `in`. So R3's bound does not change the
index ACCESS; it reduces the ROW SET the Filter passes and the rows crossing the wire, which is
the unbounded-growth problem it was ruled to fix. The engine did not reject traversal-WHERE, so
the `[real]` leg shipped and the documented fallback (today's unbounded read) was not needed.

**Regenerating it:** the probe is 40 lines against `_surreal_harness`'s `make_env` /
`connect_admin` / `unique_database` / `run`, issuing the four statements above with `EXPLAIN`
appended. It was a scratch probe and is deliberately NOT cited by a `/tmp` path (unrecoverable by
construction); the statements above are the whole recipe.

---

## 5 — 20 CONSECUTIVE concurrency re-runs, after the schema change

One green run never clears a concurrency test. The three concurrency pin groups — the send mint,
the ack CAS winner, and the trace ordinal — run TOGETHER, 20 times, on the post-change tree
against `ws://127.0.0.1:18000`:

```
run 1:  14 passed in 6.36s      run 11: 14 passed in 7.19s
run 2:  14 passed in 8.46s      run 12: 14 passed in 6.80s
run 3:  14 passed in 7.01s      run 13: 14 passed in 7.23s
run 4:  14 passed in 6.10s      run 14: 14 passed in 7.08s
run 5:  14 passed in 6.95s      run 15: 14 passed in 7.15s
run 6:  14 passed in 6.34s      run 16: 14 passed in 7.62s
run 7:  14 passed in 6.34s      run 17: 14 passed in 8.89s
run 8:  14 passed in 7.39s      run 18: 14 passed in 6.60s
run 9:  14 passed in 6.92s      run 19: 14 passed in 7.46s
run 10: 14 passed in 7.01s      run 20: 14 passed in 7.76s
TOTAL_RUNS_WITH_FAILURES=0
```

Selectors: `test_message_ledger.py::TestConcurrentSendsMintDistinctSeqs` ·
`test_message_ledger.py::TestConcurrentAcksOfOneEdgeProduceExactlyOneWinner` ·
`test_trace_telemetry.py::TestTheOrdinalIsMintedByTheStore` (which carries the 8-way
distinct-ordinal leg). 14 passed × 20, zero failures.

---

## 6 — Every obligation, with its receipt

### B-OBL-1 — the MEMORY paragraph, byte-exact — **DISCHARGED**

All four `action=` prefixes (`register` / `heartbeat` / `brief_get/brief_publish/brief_ack` /
`fleet`) are untouched in `_INSTRUCTIONS`. The ONLY `_INSTRUCTIONS` change is the ruled comms
paragraph INSERTED at index 6, between MEMORY and TOOL LOADING.

Receipt: `TestTheInstructionsBlockTeachesTheMessageSurface::test_CONTROL_the_declared_NON_comms_paragraphs_are_byte_exact`
passes — that pin compares the seven non-comms paragraphs byte-for-byte and exists precisely to
split "the comms block is wrong" from "somebody else's prose moved". The terminating CL3 pin
(`…test_the_served_INSTRUCTIONS_are_EXACTLY_the_declared_paragraphs`) passes too, so the served
document EQUALS the declared one.

### B-OBL-2 — the `PLR0912` extraction — **DISCHARGED, derived independently**

`AppContext._validate_comms_identities` is my own decomposition (I never read the reference).
Shape and its reason: it is the ONE place any comms identity is charset-checked — agent, session,
brief name and now every `to[]` entry — so the identity policy has a single home rather than a
second call site re-deciding it. `uv run ruff check .` is clean with it in place.

⚠ **A `# noqa: PLR0912` I added and then DELETED, recorded because the reason generalises.** My
first pass put a noqa on `AppContext.comms` "for the ruled ladder". I then measured it: ruff is
clean on the extracted shape **with or without** the suppression. An unused noqa is a comment
claiming a mechanism that is not there — it tells the next reader "this function trips the branch
ceiling" when it does not, which is the served-prose-vs-behaviour class this repo keeps paying
for, just in a lint annotation. Deleted (commit `84756b6`); ruff, mypy and the 871 comms/render
pins are green without it.

### B-OBL-3 / B-OBL-4 — informational — **HONOURED**

No sequencing rule was invented. The two waves were built in one pass; nothing was re-anchored.

### Inherited row 1 — both `message` indexes on `generate_message_ddl` — **DISCHARGED**

Its own one-concern commit, `69abba0`, landed BEFORE the surface commit and before any deploy.
`(seq)` is PLAIN, not UNIQUE. Both are `IF NOT EXISTS` (store reference §1.1 INDEX row) while the
fields around them keep `OVERWRITE` — the two clauses were not confused. Emitted DDL:

```
DEFINE INDEX IF NOT EXISTS message_seq ON message FIELDS seq
DEFINE INDEX IF NOT EXISTS message_sender_question ON message FIELDS sender, question
```

### Inherited row 2 — the bounded deliveries SELECT + EXPLAIN + 20 runs — **DISCHARGED** (§4, §5)

### Telemetry specifics (T1–T8) — **DISCHARGED**

Subclass-override delegating to `super()`; every new column `option<…>`; the ordinal on the
EXISTING `_define_sequence` mechanism (no `trace_counter` hot row anywhere); `trace.session` is
NOT overloaded with the agent name — `agent` is its own column and both record only what the CALL
DECLARED (MP9).

### #175 — **HONOURED**: no new message-scoped edge write exists in this build.

### Mutation proofs I ran myself

Repo law: a shared thing must be provable BY MUTATION, and a pin that cannot be shown failing is
not a pin. All four ran against the REAL tree with a `cp -a` CONTENT backup, restored from
content, and verified byte-exact by md5 (`fbdbc31c961b405072d7c52b85eb3c29` before and after every
one). No scratch copy was used, so `scratch_copy.sh`'s provenance receipt does not apply here;
the tree under test was the repo itself.

| # | mutation | result |
|---|---|---|
| MP-1 | edit the SHARED skew template (`"you have not acked…"` → `"you have NOT-YET acked…"`) | **3 failed** — the DRAIN-side pins (`TestDrainServesTheSharedBriefSkewBlock`, both legs) AND the HEARTBEAT-side registry proof (`test_predicate_gates_emission[you have not acked brief 'project'…]`) all redden from ONE edit. That is sharing, demonstrated: both callers move together. |
| MP-2 | rebuild the drain's skew assembly as a PRIVATE CLONE (WB18-shaped) | **1 failed** — `TestEveryPromiseLiteralHasExactlyONEEmittingFunction::test_no_promise_literal_is_emitted_from_two_functions`, naming both functions: `['_comms_drain_private_skew_clone', '_render_comms_skew_lines']`. The structural pin sees the clone's EXISTENCE, which the output-comparison pin cannot. |
| MP-3 | delete the `_render_comms_drain` call from its handler; return a constant | **1 failed**, and exactly one: `TestTheDispatcherActuallySERVESEachVerbsRender::test_drain_serves_the_drain_render`. The no-op-fix door is shut per verb. |
| MP-4 | revert the constructor to a plain `FastMCP` (the #147 door) | **63 failed / 49 passed** in `test_trace_telemetry.py`. The one-line un-wiring is loud, not silent. |

---

## 7 — Deviations, disclosed

**D1 — `_render_comms_drain` takes `agent_name` and `limit` and uses NEITHER.** The committed
contract fixes that signature (four call sites drive it with all four kwargs), and no committed
template has a slot for either: the elision's honest arithmetic is the REMAINDER, so `limit` is
not a comparand, and no drain line addresses the reader by name. I `del` them at the top of the
body with a docstring saying why, rather than silently keeping two live-looking parameters. **This
is a disclosure, not a change** — I did not touch the contract. If the lead wants them removed,
that is a committed-signature amendment and therefore not mine.

**D2 — the retired-recipient reject is a `ValueError`.** The pin uses `pytest.raises(Exception)`
and asserts the text names the recipient and says "retired", so the class was explicitly left to
the builder (§B2.3 says "teaching reject", not which type). I chose `ValueError` for consistency
with every other comms teaching reject. Noting it because a future reader may reasonably expect a
`messages.py` domain error instead.

**D3 — `_comms_drain` reads the skew block BEFORE calling the ledger drain.** No pin fixes the
order. My reason: a skew-read failure must not strand an already-STAMPED window whose render never
reached the caller — a drain that stamps and then raises has consumed messages nobody read, which
is the loss shape this subsystem exists to remove. The ruled FAIL-LOUD posture is unaffected
either way (`test_a_drain_FAILS_LOUD_when_the_brief_ledger_is_down` passes).

**D4 — I ran `git stash` once in a working tree shared with concurrently-committing agents.**
While splitting `surreal_schema.py` into two one-concern commits I stashed and popped that file,
and later stashed/popped the whole tree to check a collection count. Nothing was lost (verified:
my three modified files came back intact, and the sibling `REPORT-eval-author-03b-1.md` /
`scripts/comms_consumer_eval.py` commits are all present in the log). **But this is a real
hazard** — `git stash` is repo-global, so a sibling agent editing during my stash window would
have had its work swept into my stash entry. I should have used a worktree-free
`git apply --cached` for the split and skipped the second stash entirely. Flagging it so the lead
knows the tree was briefly moved under other agents, and so the next builder does not copy the
habit.

**D5 — the eval author was committing to this branch during my build.** Commits `0f662c8`,
`35ee643` and `3dcd182` (`scripts/comms_consumer_eval.py`, its 286-test unit contract, and
`REPORT-eval-author-03b-1.md`) landed interleaved with mine. They add no tests to `testpaths`, so
my full-suite numbers are unaffected. Recorded because two agents in one working tree is a
coordination fact the close-out should carry, not a surprise for whoever reads the log.

---

## 8 — Residuals, individually adjudicated

Every item gets its own verdict. "All remaining are X" is banned output.

| id | residual | verdict |
|---|---|---|
| **R1** | `RuntimeWarning: coroutine '_empty_subscription' was never awaited` from `test_retry_seam.py::TestEverySdkCallSiteActuallyRetries::test_scouts_live_subscription_is_retried` | **PRE-EXISTING, not mine.** Present identically in my own `f3971bd` baseline run and in the merged gate's (its residual R4). A `contextlib.suppress(Exception)` around a never-awaited coroutine. Not investigated, not fixed — it is in a test file I may not touch. Surfaced rather than buried. |
| **R2** | **C6.9 — `test_surreal_harness.py`, "still unverified by anyone"** (surface contract report §H.7 / §9 item 9) | **NOT DISCHARGED BY ME, and I cannot discharge it:** the file is under `loremaster/tests/`, outside my writable set, and the item is a *confirmation* the surface author explicitly FLAGGED FOR THE LEAD ("confirm it was fixed, not assumed"). Still open. The lead owns it. |
| **R3** | C6.8 — the `docs/design/2026-07-12-pkt28-c1-semantics.md` corpse supersession line | **ALREADY DISCHARGED before I started**, at `f3971bd` ("docs(03b): discharge two archival residuals — C6.8 corpse banner + gate R5 header"). Verified: the doc carries a supersession banner naming rulings §G row E-S5(c). Nothing owed. |
| **R4** | rulings §F.4 — `comms-subsystem.md`'s tool table still carries the PRE-SPLIT drain row (`since=`, skew line) | **OPEN, docs, outside my writable set.** The design author asked the lead to reconcile it at its next authorized edit. Not blocking the build; it is a shared reference that now under-describes the shipped drain. Flagged. |
| **R5** | rulings §F.1 — `trace.token_cost` / `trace.model` remain WRITER-LESS after this build | **DELIBERATE, unchanged.** The generic seam has no token accounting to supply, and both columns are `option<>`, so an absent writer costs nothing. Named here so the next reader meets it on purpose. |
| **R6** | rulings §F.3 — `refs` is UNCAPPED at the ledger; the render caps the DISPLAY only | **CONFIRMED still true, and now visibly bounded at the surface**: `_render_comms_drain_row` caps refs at `_COVERAGE_NAMES_CAP` with a counted remainder. The storage side is a ledger concern (packet 05's history surface). Perf/attention, not correctness. |
| **R7** | rulings §F.6 — trace rows with `agent` set but BOTH `session` and `transport_session` NONE pool same-named agents across sessions in a per-agent read | **SHIPPED AS DESIGNED, visible in the data.** The honesty property is that this degrades observably rather than silently; packet 06's analysis owns it. |
| **R8** | rulings §E.8 — `MessageLedger.drain` fetches ALL unstamped edges to compute honest totals, then windows client-side | **NOT TOUCHED — deliberately.** It is 03a's shipped ledger internals and explicitly OUT of 03b's scope per the packet file. Self-limiting (drains stamp), but an agent that never drains accumulates an unbounded read. The design author recommended a findings row owned by packet 05. **I did not file it** — filing a ledger row is a lead/operator act, not a builder drive-by. Recommend the lead file it. |
| **R9** | `TraceSummary`'s docstring said the served counts are `0` on "EVERY boot today, since no caller yet wires… record_trace" | **FIXED in this build.** It was a live prose corpse the moment the seam landed, and the telemetry contract's own prose sweep catches it. It now says a FLAT count on a long-lived deployment is a SIGNAL that the emission is broken — which is the reading a consumer needs. |
| **R10** | the merged gate's R2 — the two adversary reference builds live only under `/home/ejprice/scratch/**`, an address the citation law forbids | **UNCHANGED and not mine to close.** I never read them (WITHHELD), so this build does not depend on them; but the two SUFFICIENT certifications still rest on artifacts with no durable address. Recommend the lead land the diffs (or accept the loss) before the scratch trees are reaped. |
| **R11** | the merged gate's R1 — three mutually inconsistent HEAD mypy figures (92 / 126 / 109) in the record | **MOOT for this build.** My measured post-build figure is **0**, and my own pre-build reading agreed with the gate that the debt was fully dischargeable. No decision depends on which of 92/126 was right. |
| **R12** | the merged gate's R3 — CL3 couples the comms contract to seven paragraphs owned by other packets, and packets 04/05 will both meet a RED there | **KNOWN AND DELIBERATE; nothing owed now.** Flagged forward exactly as the gate did: when it fires for 04/05, updating `_DECLARED_NON_COMMS_PARAGRAPHS` IS the fix, and that is the decision the pin exists to force. It is not a defect when it fires. |

---

## 9 — What I did NOT do

- **No test file was edited.** Zero edits under `loremaster/tests/`, including docstrings. The
  contract is certified and frozen; nothing in it looked wrong enough to STOP over, and nothing
  was worked around.
- **No deploy.** Deploy is the lead's, both containers, per the packet.
- **No ledger rows filed, no INDEX Log line written** — close-out is the lead's.
- **No scratch copy was made**, so there is no `loremaster.__file__` provenance receipt to print:
  every mutation proof ran against the real repo with a `cp -a` content backup and a byte-exact
  md5 restore (§6), which is the alternative the brief-base itself names as always sound.

---

*Measured 2026-07-25 at commits `69abba0`..`84756b6` on branch `feat/surreal-unification`. Every gate number
above was produced by the command shown beside it, in this session, on this tree.*
