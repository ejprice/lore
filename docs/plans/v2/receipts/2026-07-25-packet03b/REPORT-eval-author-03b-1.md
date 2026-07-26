# REPORT-eval-author-03b-1 — the packet-03b client-acceptance instrument

brief-base v6 read

## SUMMARY BLOCK

- **state:** DONE. All four forks ruled, both follow-ups closed, and the lead's drift
  ruling implemented (§F′.1).
- **deliverable:** `scripts/comms_consumer_eval.py` (the committed acceptance instrument,
  spec `docs/plans/v2/03b-design-rulings-r2.md` §C1–C5) + `scripts/test_comms_consumer_eval.py`
  (**156 tests, `156 passed in 0.72s`; 306 across `scripts/`**, ruff clean, `--dry-run`
  exit 0 with all 19 surfaces generated from production code). Commits `0f662c8`,
  `35ee643`, `a1795b9`, `e165141`.
- **gate semantics (RULED):** a run answered by a model other than the pin is **not a
  gating run** and does not count toward the three — exit **3** (gate never valid),
  distinct from exit **1** (the surface failed). §F′.1.
- **roster verdict (lead follow-up 2): HONEST — no trust defect, nothing to file.** The
  remainder derives from `total_non_retired` (pre-truncation, same session filter), never
  from the 200-row window or the 5-name cap, and `send` passes the caller's RESOLVED session
  into the enrichment. Fixture was cheap → added as a non-gating surface. Full trace: §F′.2.
- **model-pin drift (lead follow-up 1): shipped.** Every run records the model each response
  reports; a mismatch is loud on stderr + in the transcript. One judgement call stated for
  you in §F′.1 (drift reports beside the verdict rather than failing the gate).
- **wired vs awaiting:** everything is wired — the render helpers LANDED during this run, so
  the seam generates every fixture from real production code today. `--dry-run` exits 0 and
  prints the served surfaces + battery with provenance (measured 2026-07-25 at `35ee643`).
- **deviation 1:** §C3 asks for a "dated model id"; a live `GET /v1/models` on 2026-07-25
  shows NO dated snapshot exists for any named population member. Pinned the bare
  `claude-sonnet-5` with the measurement recorded at the constant. Body §D1.
- **deviation 2:** §C5(a)'s "unknown recipient with roster" reject fixture is ABSENT, not
  faked — it cannot be produced without a live agent registry, and transcribing it would
  break §C1.1. Three other real teaching rejects carry the key. Body §D2.
- **deviation 3:** `anthropic` is not a project dependency; the run command is
  `uv run --with anthropic python scripts/comms_consumer_eval.py …` (no pyproject change,
  no permanent install). Body §D3.
- **live-call cost:** ONE call, `claude-sonnet-5`, 33 in / 15 out → **$0.000324**. Body §E.
- **decisions needed:** (a) accept the bare model pin; (b) accept the missing
  unknown-recipient reject or authorize a live-registry fixture; (c) confirm the
  `uv run --with anthropic` invocation vs. a dedicated eval venv. Body §D.
- **receipt pointers:** §A (the 15 tasks + graders + controls) · §B (the render seam) · §C
  (fixture discrimination) · §D (deviations/forks, all four RULED by the lead) · §E (the
  live call) · §F′ (the two lead follow-ups) · §F (RESIDUALS, one verdict per row) · §G
  (how to run the gate).

---

## A. The battery — 15 tasks, their keys, and each grader's positive control

The consumer answers every turn with a reasoning line plus `ANSWER: {json}`; only the JSON
is graded. Grading never reads prose: it reads seq sets, parsed `lore_comms` calls, keyed
tokens from closed vocabularies, and yes/no state calls. An unparseable answer is a FAIL,
not a skip (`TestBatteryRunner::test_an_unreadable_answer_is_a_failure_not_a_skip`).

The whole battery is ONE conversation, so task 15 sees everything tasks 1–14 produced —
which §C2 requires and a per-task-call design could not give.

| # | keys graded | the machine key | positive control (the grader shown FIRING) |
|---|---|---|---|
| 1 | `seqs`, `call` | seq set == the trailer's `{71, 74}` AND a parseable `action=ack` whose own seqs match | answers the ALL-UNACKED set `{71,72,74}`; answers the right set with prose instead of a call; answers a call whose `seqs=[]` contradicts the stated set |
| 2 | `remaining`, `call` | `remaining == 5` AND `action=drain` carrying NO cursor-shaped param | answers `remaining=9` (the `shown+more` re-ask); passes `since=74` |
| 3 | `delivered_seqs` | exactly `{71,72,73,74}`; the in-fence forged `#88` absent | includes `88`; lists a short set |
| 4 | `ack_again` | `false` | `true` |
| 5 | `still_waiting` | `true` | `false` |
| 6 | `thread_discharged`, `next_move_call` | discharged AND a `action=send … set_status='input_required'` re-ask | a re-ask with no `set_status`; "the thread still holds the debt" |
| 7 | `call` | `action=send`, `grade='directive'`, `to` names `fixer-b` | graded `signal`; addressed to nobody |
| 8 | `meaning`, `retry_blindly` | `NEVER_DELIVERED_TO_ME` + no blind retry | answers task 11's token; answers `retry_blindly=true` |
| 9 | `still_unread`, `call` | `true` AND a drain that does NOT pass `peek=true` | "the peek stamped them"; a stamping call still carrying `peek=true` |
| 10 | `call` | `action=send` with `to` omitted or `[]`, grade in the closed set | enumerates recipients; `grade='urgent'` |
| 11 | `meaning`, `retry_blindly` | `NO_SUCH_MESSAGE_EXISTS` + no blind retry | answers task 8's token; an off-vocabulary token |
| 12 | `tool_failed`, `anything_lost`, `anything_sent`, `fix_for_oversize` | nothing lost, nothing sent, fix == `PUT_THE_CONTENT_IN_A_REPORT_AND_REFERENCE_IT_IN_REFS` | "something was lost"; "the rejected send went through"; `RETRY_THE_SAME_CALL_UNCHANGED` |
| 13 | `shown`, `more`, `total`, `next_limit` | `4 / 5 / 9 / 5`, and the reported arithmetic closes | `next_limit=9`; a `more` that breaks `shown+more==total` |
| 14 | `matched_teaching`, `peeked_rows_were_still_unread`, `stamping_drain_served_them` | all three true | any one false |
| 15 | `verdict`, `reason` | `CALL_AGAIN` with a non-empty reason | `ROUTE_AROUND` (verdict text says: a FAILED acceptance to adjudicate, never waived); an empty reason; an off-vocabulary verdict |

Two design decisions worth the lead's eye:

- **Tasks 8 and 11 share ONE closed token set.** `not_addressed` and `unknown_message` are
  different rejects, and a consumer that conflates them looks correct on either question
  asked alone. Sharing the vocabulary forces the discrimination: conflating them fails
  exactly one of the two.
- **The routing test's failure message is part of the instrument.** A `ROUTE_AROUND`
  verdict returns *"a FAILED acceptance: adjudicate the render/teaching defect the reason
  names (never waive it)"* — the §C5(d)/FK-5 rule stated where the reader of a transcript
  will actually meet it, not only in a doc.

Also pinned: all 15 tasks present and numbered 1–15, task 15 LAST, every task mandatory,
every grader name resolves, every rendered prompt names its own answer keys, and dropping
ANY single required key from ANY correct answer makes that task fail
(`TestGradersRejectMissingKeys`, parameterised over all 15).

## B. The render seam — one thin place, and it fails LOUD

`LiveSurfaceProvider` is the only code that reaches production. It uses three distinct
authoritative seams and no fourth:

1. **The renders** — `AppContext._render_comms_{send,drain,ack}`, driven with real
   `loremaster.messages` value objects (`Message`, `InboxEntry`, `MessageDrainResult`,
   `MessageAckEntry`, `MessageAckResult`).
2. **The teaching** — `loremaster.server._INSTRUCTIONS` verbatim, and the `lore_comms`
   description + input schema read from the REAL registration
   (`build_mcp_server(LoreServer(load_config('lore.yaml')))` → `list_tools()`), i.e. the
   bytes an MCP client receives. Not re-typed, not AST-scraped.
3. **The rejects** — real teaching text raised by the real validation prologue of
   `MessageLedger.send`. The ledger is constructed with throwaway wiring; all three cases
   reject before the first `await`, so there is zero store contact.

**Drift is loud in both directions.** `_render_helper` compares the helper's keyword-only
parameters against a declared `_EXPECTED_KWARGS` map: a kwarg the seam passes that the
helper no longer accepts, and a REQUIRED kwarg the helper grew that the seam does not pass,
both raise `RenderSeamUnavailable` naming the parameter. A newly-added kwarg **with a
default** is tolerated — it cannot silently change what the seam renders, so it is not
drift (pinned four ways in `TestRenderSeamFailsLoud`, including the tolerated case). A
missing helper raises with *"the packet-03b render build has not landed yet. This
instrument NEVER substitutes a transcribed render."*

There is no fallback path in the code. The only two outcomes are "generated from production
code" and "failed to build" — which is the property §C1.1 is actually asking for.

**Provenance is printed on every run** (transcript header and `--dry-run` stderr):
`loremaster.server`'s and `loremaster.messages`'s `__file__` plus the config path, so a
transcript names the tree it graded.

## C. Fixtures, and what wrong build each one kills

Every number lives in one frozen `FixtureSpec` that the graders read too — an expected
answer is never a second hand-written copy of a fixture value. `TestFixtureSpecDiscriminates`
pins the properties:

- **Elision 4 shown / 9 pending / 5 remaining, request limit 4.** Pairwise distinct, so a
  build filling `{next_limit}` with `shown`, `total`, `shown+more`, or the request limit is
  distinguishable from the correct remainder (§B15).
- **A TWO-member trailer set `{71, 74}`**, and it differs from both the all-unacked set
  `{71,72,74}` and the all-directive set `{71,73,74}` — one discriminating fixture per
  conjunct of the emit predicate (AC-10's shape). A one-element set could not tell "serves
  the trailer" from "serves the first unacked directive it finds".
- **The hostile body carries all three §B7.3 threats at once**: embedded newlines, a line
  shaped exactly like the drain's own entry header (`#88 [directive] lead -> you: …`), and
  a backtick run of five. Verified against the real render: every occurrence of the forged
  row is INSIDE a fence.
- **The forged seq (88) collides with nothing else the battery keys on** — sharing a number
  with the `unknown_message` (424) or `not_addressed` (99) seqs would make a failure
  ambiguous between two causes.
- **All three `{context}` cell variants are exercised in one render** — task cell, thread
  cell (`q:gate-color`), and bare (§B14).
- **No fixture factory defaults a branched-on value.** `_message` / `_inbox_entry` require
  `question`, `acked_at`, `thread`, `task_id`, `refs`, `grade` at every call site (AC-11 /
  the repo's fixture-default law).

**A correction the real renders forced, recorded because it was a live near-miss:** tasks 5
and 6 originally shared one thread, so a reply DID land on task 5's thread and *"are you
still waiting"* had two defensible answers. Split onto `q:budget-split` (question +
self-note, no reply ever) and `q:two-questions` (two questions + the reply drain). A failure
there would have been a fixture artefact billed as a finding.

## D. Deviations and forks — the operator/lead owns these

### D1. The model pin is BARE, not dated (§C3's letter is unsatisfiable)

§C3: *"pin the exact dated model id in the script"*. Measured 2026-07-25, live
`GET /v1/models` on this account: the named population is served as `claude-sonnet-5`,
`claude-opus-5`, `claude-fable-5` — **no dated snapshot exists for any of them**; only
4.x-era models still carry dates (which is why the p8a precedent could pin
`claude-sonnet-4-5-20250929`). Appending a date would 404.

Chosen reading: pin the bare id as a module literal with the measurement dated at the
constant, so a future dated snapshot is a deliberate reviewed edit. Alternative reading
(not chosen): pin a dated 4.x Sonnet to satisfy the letter — rejected, because the operator
named Sonnet 5 as the floor CLIENT and grading a model nobody uses measures nothing.
**Recommendation: accept the bare pin.** Lead/operator call.

### D2. The "unknown recipient with roster" reject is ABSENT, not faked

§C5(a) names it as a fixture source. Its text is half registry-owned
(`UnknownAgentError`, raised inside `AgentRegistry._resolve_row`, which queries the store)
and half server-owned (`AppContext._comms_enrich_unknown_agent`, which awaits
`agent_registry.fleet`). It cannot be produced without a live registry, and transcribing it
would be exactly the defect §C1.1 forbids — so it is absent, with the reason written into
the code at `_rejects`'s docstring.

Task 12 is still keyed and still discriminating: it rides three REAL teaching rejects
(oversize body → the refs pointer; a broadcast that resolved to nobody; a grade outside the
closed vocabulary), which together carry §C5(a)'s key (nothing lost, nothing sent, a named
fix). **Fork for the lead:** accept the three, or authorize a live-registry fixture (a
store-backed session in the eval, which makes the instrument depend on a running SurrealDB
— a real cost against a currently store-free instrument). **Recommendation: accept the
three now; revisit if a trust probe ever needs the roster prose specifically.**

### D3. `anthropic` is not a project dependency

The project venv has `loremaster` and no `anthropic`; the p8a eval venv has `anthropic` and
no `loremaster`. This instrument needs BOTH (it imports production code AND calls the API).
Chosen: `uv run --with anthropic python scripts/comms_consumer_eval.py …` — the project
environment plus an SDK overlay, no `pyproject.toml` change, no permanent install, nothing
in my writable set violated. Verified working (`anthropic 0.120.0`, `loremaster` resolving
to the real checkout). Alternative: add `anthropic` to a dev/eval dependency group — a
pyproject edit, outside my writable set, and per the packages rule it is an install
authorization only the operator can grant. **Recommendation: keep the overlay; it is
reproducible and touches nothing.**

### D4. `scripts/` is outside the mypy gate

`scripts/typecheck.sh` runs mypy over `lorescribe`/`loresigil`/`loremaster` only, so neither
new file is type-checked by the repo gate. Both are fully annotated anyway. Flagged, not
fixed — widening the canonical typecheck runner is not in my writable set.

## E. The one live API call (cost discipline)

Exactly one generative call was made, through the real `AnthropicConsumerClient.ask` path so
the wiring itself was what got proven — the pinned model id, the cached system-block shape,
`output_config={"effort": "high"}`, and the answer parser end to end:

```
model: claude-sonnet-5   stop_reason: end_turn   reply: ANSWER: {"ok": true}
usage: {input 33, output 15, cache_creation 0, cache_read 0}   cost_usd: 0.000324
```

Plus one non-generative `models.list()` call ($0.00) for the D1 measurement. **The 15-task
battery was NOT run against a live model** — that is the lead's gate step.

Cost model for the lead's gate: the served surfaces are a large stable system prefix cached
across all 15 turns, so a run pays the prefix ~once at write rates and 14× at read rates.
The script reports per-run and total estimated USD in the transcript and on the final line;
rates are the skill's standard table (Sonnet 5's introductory discount deliberately NOT
applied — an over-stated cost never surprises anyone).

## F′. LEAD FOLLOW-UPS (added after the ruling; commit `a1795b9`)

### F′.1 — D1 hardening: the pin is now a RECEIPT, not a hope

Implemented as asked. Every run records the `model` field each API **response**
reports (not just the requested id). Surfaces:

- `RunOutcome.served_models` — the distinct answering models, first-seen order.
- `model_drift_notice(requested=, served=)` — returns a loud
  `⚠ MODEL PIN DRIFT: requested 'claude-sonnet-5', but the API answered on [...] — the
  pinned alias has been repointed upstream. This run did NOT measure the pinned model;
  re-pin deliberately before treating it as a gate.`
- Printed to **stderr** during the run, carried in a dedicated **transcript section**, and
  the verdict table gained an **"answered by"** column so every row shows both ids.

Positive control pinned (`TestModelPinDrift`): a mocked response whose `model` differs
produces the notice; the pinned model produces none; a response reporting no model at all
produces none; and a run-level test proves the notice reaches both the `RunOutcome` and the
transcript.

**RULED by the lead (2026-07-25), and the answer was a third option neither of us had
stated.** Drift must NOT be a surface FAIL (my reasoning accepted: a red gate that blames
the render for an upstream alias repoint is a false gate, and false gates get switched
off) — **but "PASS with a notice" was also wrong**, because §C3 defines the gate as 100% of
the mandatory keys *on the pinned consumer model*, and a run some other model answered has
not met that definition. It is not a failed run; **it is not a gating run at all.**

Implemented (`e165141`). `gate_passed() -> bool` is replaced by
`evaluate_gate() -> GateVerdict`, which separates three outcomes that used to be one:

| exit | meaning |
|---|---|
| 0 | the gate was satisfied |
| 1 | the **SURFACE** failed — a VALID run missed a mandatory key (the real verdict, kept unpolluted) |
| 2 | no `ANTHROPIC_API_KEY` |
| 3 | the gate was **never valid** — too few runs answered by the pinned model |

- A drifted run **does not count** toward the required three; the tally, and a
  plain-language reason per refused run (*"run 2 was answered by X, not the pinned
  'claude-sonnet-5' — NOT counted toward the gate"*), appear in the transcript's own gate
  section, on stderr, and in the final line. The verdict table gained a
  **"counted toward gate"** cell.
- A drifted run does **not reset** the streak either — it says nothing about the surface in
  either direction, so it neither extends nor breaks it (pinned: four runs with one drifted
  still yield three valid ones).
- A drifted run that FAILED is **not blamed on the surface** — it is excluded, and the gate
  reads invalid (exit 3) rather than red (exit 1).

**The positive control the ruling demanded, plus its own control:** three GREEN runs with
one drifted must NOT satisfy the gate (`counted == 2`, `surface_failed` False, exit 3), and
the same three without drift MUST — otherwise the first assertion would be satisfied by a
gate that never passes anything.

The rationale, recorded in the code so the next reader inherits it: the hazard was never a
drifted run failing loudly, it was a drifted run **passing quietly** and being cited later
as *"the battery passed on the pinned floor model"* — a false sentence nothing downstream
could catch. The "answered by" column makes drift **visible**; refusing to count it makes
that citation **impossible**.

### F′.2 — THE ROSTER VERDICT: **honest. No trust defect. Nothing to file.**

Read: `AppContext._comms_enrich_unknown_agent`, `AgentRegistry.fleet`, and the new
`AppContext._comms_send` path that routes into them.

**The arithmetic, traced.** `fleet(session=…, limit=200)` issues `SELECT * FROM agent`
under the session filter (**no SQL LIMIT**), partitions retired from non-retired, sets
`total = len(non_retired)` — the **pre-truncation** count — and only then truncates
`rows = non_retired[:limit]`. The enrichment takes `shown = names[:5]`
(`_COVERAGE_NAMES_CAP`) and computes `remainder = window.total_non_retired - len(shown)`.
**The remainder derives from the TRUE total, never from the row window or the display
cap** — so with 300 non-retired agents the render reads `…5 names… (+295 more)`, not
`(+195 more)`. The 200-row window cannot leak into the count. The label
("non-retired agents") describes exactly the set the count covers, and retired rows are
partitioned out before the total is taken.

**Session scope is correct on the new path** — this was the specific thing worth checking,
since `send` is new. `_comms_send` resolves recipients against `agent_row.session` (the
caller's RESOLVED session, per B2.3) and passes **that same `session_scope`** into the
enrichment, so the roster describes exactly the addressable recipient set. It does not
inherit the dispatcher's raw (possibly `None`) `session` param, which would have taught a
fleet-wide roster of agents the caller cannot address.

**Edge cases checked, all closed:** an empty roster renders `none` with no remainder (the
`0 - 0` case); `shown` cannot be empty while the total is positive (the window is
`[:200]`); and the names are joined **unsanitised**, which is safe only because
`AGENT_NAME_PATTERN = ^[a-z0-9][a-z0-9_-]{0,63}$` admits no newline, space, or backtick at
register time. That last one was implicit — I pinned it explicitly
(`test_the_roster_cannot_carry_a_forged_row`), so a widened charset goes RED on the render
that CONSUMES names, not only on the registry that admits them.

**The fixture was cheap, so it is in** — as a non-gating served surface:

```
agent 'fixer-z' is not registered — every comms call requires a prior 'register';
non-retired agents: lead, idle-d, fixer-c, runner-g, prober-f (+2 more)
```

Both halves are production code and **nothing is transcribed**: the bare
`UnknownAgentError` comes from the REAL `AgentRegistry.get_agent` (its resolve finds no row
and raises), and the roster prose + remainder come from the REAL enrichment over a REAL
`AgentFleetWindow` built by the REAL `fleet()`. The only stand-in is the **store** — each
registry's `_query` is replaced with a canned result — which is the same posture the render
fixtures already take toward the ledger. **No connection is opened**, so the instrument
stays store-free and `--dry-run` keeps working with SurrealDB down.

Fixture discrimination: **7 non-retired + 1 retired** → 5 shown, `(+2 more)`. 7 / 5 / 2 are
pairwise distinct, so a build deriving the remainder from the row window rather than the
true total is discriminable; a `(+3 more)` would mean retirement leaked into a set whose
label says non-retired. *Which* five are shown is deliberately NOT pinned — that is
`fleet()`'s status-then-freshest-heartbeat ordering, a display choice, not the count claim
under test.

**Loud absence, as directed:** `ServedSurfaces.absent_surfaces` records any surface that
could not be generated; absences print to stderr (`⚠ ABSENT SURFACE — …`) and get their own
transcript section, and a complete run explicitly states *"every specified surface was
generated; none absent."* — so a reader never has to infer completeness from a missing
section.

Battery impact: none of the 15 tasks key on this surface (it is non-gating, as ruled). It
does strengthen task 12 slightly, since "the calls the tool REJECTED" now includes a
fourth, count-bearing reject.

**Instrument state after both follow-ups: 149 tests pass, ruff clean, `--dry-run` exits 0.**

## F. RESIDUALS — one verdict per row (no wholesale classification)

| # | observation | verdict |
|---|---|---|
| 1 | The self-note receipt renders `sent #204 [signal] → fixer-b` with NO thread cell (B3.2 struck), so a reader cannot tell from the RECEIPT which thread a self-note rode. | **Not a defect — by design.** Task 5's prompt states the thread; the clearing RULE comes from the question teach line, which is what §C2.5 tests. Recorded because it makes the teach line load-bearing rather than decorative. |
| 2 | `_render_comms_send` shipped an additive `recipients must ack: lore_comms action=ack seqs=[201]` line on directive sends (not in my read of B3). | **ANSWERED by the lead — no defect.** It is contract-required, registered and proven: `loremaster/tests/test_comms_promise_registry.py`'s `_PROOF_LIST` entry with its non-cross-satisfied marker. Row closed. |
| 3 | The acked re-serve shipped as a TRAILER line (`re-served after ack: #73 — informational; …`) rather than a row suffix. | **Fine.** §A-GRAFT left the shape to the contract author. Task 4's prompt names the seq, so it does not depend on the placement. |
| 4 | The ack render's header reads `acked 1 of 4: #71` while FIVE entries were requested (the duplicate pair). | **Consistent with §B5's consistency clause** (counts derive from DISPLAYED membership, not raw entry counts). Not graded by any task. Recorded so nobody later reads it as an arithmetic bug. |
| 5 | `send_broadcast`'s receipt says `3 agents in session wave7` — count-form, no names. | **Correct per B3.1.** Task 10 keys on the CALL, not on the receipt, so the count-form is not a grading dependency. |
| 6 | The peek pair renders `3 of 3 pending` on both legs, i.e. the stamping drain still shows 3 pending. | **Fixture artefact, not a render claim** — my `MessageDrainResult` sets `total_pending` per leg. Recorded so a future reader does not mistake it for a serving inconsistency. |
| 7 | `load_config('lore.yaml')` resolves `ANTHROPIC_API_KEY` eagerly, so even `--dry-run` needs the key exported. | **Accepted.** The gate needs the key regardless; the failure is a clear `ValueError` naming the field and the env var, not a silent one. |
| 8 | The instrument grades first-contact only. | **Scope, per §C4** — long-horizon adherence is packet 06's drill, decay is the T-series. Written into the module docstring so a transcript reader cannot over-read a PASS. |
| 9 | `TestLiveRendersAgreeWithTheSpec` SKIPS rather than fails when the renders are unavailable. | **Deliberate** — the brief forbids unit tests that require the build. They currently RUN (the build landed) and all nine pass. |

## G. How the lead runs the gate

```sh
export ANTHROPIC_API_KEY=$(grep '^ANTHROPIC_API_KEY=' /home/ejprice/docker/mcp/.env | cut -d= -f2-)
# free — proves the seam and prints exactly what the consumer will see:
uv run --with anthropic python scripts/comms_consumer_eval.py --dry-run
# the per-change gate (§C3): floor model, 3 consecutive runs, 100% of mandatory keys
uv run --with anthropic python scripts/comms_consumer_eval.py --mode gate \
  --out docs/plans/v2/receipts/<date>-packet03b/consumer-eval-floor.md
# packet exit (FK-5): one run each on Sonnet 5 / Opus 5 / Fable 5; ANY keyed failure
# by ANY member is an adjudicated finding, never a waived receipt
uv run --with anthropic python scripts/comms_consumer_eval.py --mode population \
  --out docs/plans/v2/receipts/<date>-packet03b/consumer-eval-population.md
```

**Exit codes are three-way on purpose** (§F′.1) — a caller must be able to tell WHY:
**0** the gate was satisfied · **1** the SURFACE failed (a valid run missed a mandatory
key — the verdict this instrument exists to produce) · **2** no `ANTHROPIC_API_KEY` ·
**3** the gate was never valid (too few runs answered by the pinned model). Treat 3 as
"re-run", not "the render is broken".

The transcript carries the gate verdict with its counted-vs-required tally and a reason per
refused run, the verdict table (requested model · answered by · keys · counted toward gate ·
failures · cost), per-task observed-vs-expected evidence, the raw replies, per-run usage and
estimated cost, the fixture provenance, any absent surfaces, and the full served surfaces
verbatim — committable under `docs/plans/v2/receipts/` as §C3 requires.
