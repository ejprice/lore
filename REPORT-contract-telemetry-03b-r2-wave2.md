# WAVE-2 ADDENDUM — ESC-5 oracle grant + E-S6 message indexes

Companion to `REPORT-contract-telemetry-03b-r2.md` (same agent, same session, 2026-07-24).
Sections numbered to continue that report (§8–§11). The lead's wave-2 rulings are transcribed
in that file's header note.

---

## §8 ESC-5 applied — the ORACLE change (`loremaster/tests/_surreal_fakes.py`)

Granted verbatim as written in ESC-5, cited inline to **ESC-5 + T7.8/T8**. What landed on
`FakeSurrealStore`:

- `record_trace` gains four keyword-only params after `model` — `agent`, `action`,
  `transport_session`, `ok` (all `| None = None`); `hit_count` and `session` become
  `| None = None`.
- Every optional column is stored ONLY when given (the real `option<>` column's
  clean-NONE-on-omission), via one loop rather than eight `if` blocks.
- **The fake mints an ordinal from a new per-instance counter** (`_trace_ordinal`,
  `_next_trace_ordinal`) so `recorded_traces()` mirrors the real ROW SHAPE, not just the
  signature. **0-based**, matching the engine's `sequence::nextval` under the default
  `START 0` (probed — §4.1 of the main report), so no consumer can grow a dependency on
  1-based ids the real store would never produce.
- The docstring records WHY `ordinal` is not a parameter (T3: the real mint is server-side
  because a client-side mint races) and marks the concurrency property as deliberately
  provable only against the real engine — the fake counter is single-threaded by
  construction and must not be mistaken for evidence about contention.

**Effect on the FK-3b pin, which is the point:** it now fails pointing at PRODUCTION
(`Left contains 4 more items, first extra item: 'agent'` — the FAKE is ahead, the real store
owes the change), where before it failed ambiguously against both sides. The oracle's
satisfiability duty across BOTH consumer suites transfers to the adversary per the lead's
ruling; my own receipt is that the change broke nothing in the 15 suites that consume
`FakeSurrealStore` (§10).

---

## §9 E-S6 applied — the two `message` hot-path indexes

Design authority: `03a-2-consume-path-design-rulings.md` **R3 part (1)**, carried into
`03b-design-rulings-r2.md` **B10 row 3** as OPEN work. Three offline pins + one live pin.

### §9.1 ⚠ FILE-HOME CORRECTION — the pins are in `test_comms_schema.py`, not `test_surreal_schema.py`

The lead's instruction named `test_surreal_schema.py` ("your file"). **That premise is false and
I measured it before writing:**

- `test_surreal_schema.py`'s entire subject is `generate_ddl`, and **`generate_ddl` does not
  contain the `message` slice at all** — derived, not assumed: enumerating every
  `DEFINE INDEX` in `generate_ddl(dim=512)` yields 14 statements, none on `message`/`to`
  (that enumeration is also what caught my own first index-parser control, which had reached
  for `to_out_seen_at` and found nothing).
- The message DDL is a SEPARATE generator, `generate_message_ddl`, applied by
  `MessageLedger.ensure_ready` — and its pins already live in
  **`test_comms_schema.py::TestMessageDdlOffline`**, which carries the `to_in_out` UNIQUE
  index pin, the `to_out_seen_at` drain index pin, the sequence pin, and the per-object-kind
  guard-kind pin over the whole slice.
- **R3 itself points at that file**: *"Index-presence pins follow `test_comms_schema.py`'s
  existing `_index_statements` idiom."*

Writing them into `test_surreal_schema.py` would have created a SECOND home for one
invariant — message-index pins in two files, one of which cannot even see the DDL without
importing a generator alien to its subject. That is the duplication-of-policy failure this
repo legislates against, so I wrote them in the correct home and am flagging the deviation
rather than either silently obeying a false premise or silently skipping the task.

**Scope note, stated plainly:** `test_comms_schema.py` was in NEITHER my writable set nor my
do-not-touch list (which named `test_comms_tool.py`, `test_comms_promise_registry.py`,
`test_message_ledger.py`), and `git status` confirmed it unmodified by the parallel surface
wave before I touched it. My edits there are purely ADDITIVE (four new tests; no committed
assertion altered), which is the shape the design authority already anticipated — R3's own
"Costs" line budgets "two schema pins" in that file. **If the lead prefers a different home,
moving four tests is a mechanical edit; say so and I will move them.**

### §9.2 The pins

| pin | ruling | what it kills |
|---|---|---|
| `TestMessageDdlOffline::test_the_seq_index_is_defined_PLAIN_on_the_message_table` | R3(1) | a missing `(seq)` index (ack's `WHERE seq IN $seqs` table-scans every message ever sent); a UNIQUE one (a semantics change — it would REJECT a second row per seq, not merely fail to speed a read); a wrong name; a composite standing in for it |
| `TestMessageDdlOffline::test_the_sender_question_index_is_defined_SENDER_FIRST` | R3(1) · R4 | a missing `(sender, question)` index; **the reversed prefix** `(question, sender)` — a boolean leading column halves the table at best where `sender` selects one agent's rows; a UNIQUE one (many messages share the pair); a superset |
| `TestMessageDdlOffline::test_the_index_field_patterns_discriminate_single_from_composite` | the CONTROL | the two pins above passing for a fixture reason: it proves each `FIELDS` pattern means "these fields EXACTLY" in BOTH superset directions, on fixtures built in the test so the control never starts depending on the thing it certifies |
| `TestMessageSchemaLive::test_both_message_hot_path_indexes_actually_LAND_on_the_engine` | R3(1) + store ref §6.5 | **an index the engine REJECTS**: applying this slice is a MULTI-statement query and the SDK inspects only the FIRST statement's status, so a later `DEFINE INDEX` failure is swallowed and the sibling apply pin still passes (its subject was created earlier). Pinning the source proves the recipe; only the engine proves the cake. Carries a positive control (the introspection sees the committed edge indexes) so a missing name is a real absence |

The **deploy-window rationale** is in the section comment above the pins, as directed: an index
on a POPULATED table BUILDS, blocking, at the first `ensure_ready` carrying it (store reference
§1.5); production carries ZERO `message`/`to` rows until 03b deploys (03/03a-1/03a-2 are
test-only, and this DDL is applied only by `MessageLedger.ensure_ready`, which nothing deployed
instantiates yet) — so these two lines are free exactly once, and the window closes at 03b's
deploy permanently.

The `IF NOT EXISTS` guard kind is deliberately NOT re-asserted: R3 records that
`test_every_field_uses_the_overwrite_guard_and_every_object_uses_if_not_exists` already covers
every object in the slice automatically, and `_index_statements` only matches statements
carrying it. Cited, not duplicated.

### §9.3 New probe receipt — the shared name is SAFE on 3.2.1 (a risk R3 did not name)

R3 gives the SEQUENCE and the new INDEX the **same name**, `message_seq`. Nothing in the
trusted record says whether the engine tolerates that, and a rejection would be a **boot-time
crash on the every-boot re-apply** — so I probed it (TEST store `:18000` only, 3.2.1):

- **sequence-first**: both accepted · **index-first**: both accepted.
- Both objects coexist: `INFO FOR TABLE message → indexes ['message_sender_question',
  'message_seq']` alongside `INFO FOR DB → sequences ['message_seq']`.
- **Re-applying both statements is idempotent** in either order (the `ensure_ready` path).
- CONTROL: a differently-named index on the same fields is also accepted, so the acceptance is
  not an artefact of the engine ignoring the statements.

Recorded as a fact with a pin rather than a memory: the live leg (§9.2 row 4) asserts the
sequence SURVIVES alongside the index of the same name, so an engine upgrade that revokes this
fails a test instead of a deploy.

---

## §10 Wave-2 tails (measured 2026-07-24, after both wave-2 edits)

| suite / gate | result | reading |
|---|---|---|
| `test_comms_schema.py` | **3 failed / 222 passed** | the three E-S6 pins whose subject does not exist yet; the CONTROL passes (it must) |
| `test_surreal_fakes.py` + `test_surreal_store.py` + `test_surreal_schema.py` + `test_surreal_harness.py` | **2 failed / 384 passed** | UNCHANGED from wave 1 — the oracle change broke nothing, and FK-3b now fails pointing at production |
| `test_trace_telemetry.py` | **63 failed / 12 passed** (75 collected) | unchanged |
| **the ORACLE blast radius + the structural/AST suites, in ONE run** — 21 suites: `test_trace_telemetry` · `test_comms_schema` · every `FakeSurrealStore` consumer (`test_indexer`, `test_indexer_contextualized`, `test_indexer_bulk_sweep`, `test_indexer_chunker_fault_isolation`, `test_graph_wiring`, `test_impact`, `test_extension`, `test_reconcile`, `test_map`, `test_static_snapshot_reacquire`, `test_symbols`, `test_search`, `test_store_read`, `test_watcher`) · `test_retry_seam` · `test_retired_symbols` · `test_render_seam_pins` · `test_text_hygiene` · `test_mcp_server` | **66 failed / 1994 passed** | **the 66 are EXACTLY my two RED contracts** (63 telemetry + 3 E-S6) — enumerated from the FAILED lines, not inferred from the count. **ZERO collateral from the oracle change**: the blast radius was RUN, not reasoned about |
| `uv run mypy loremaster` | 92 errors / 2 files | **ZERO in any file I touched** (all in the parallel surface wave's `test_comms_tool.py` 86 + `test_comms_promise_registry.py` 6) |
| `uv run ruff check loremaster/` | clean | |

**RED reasons, verified individually (all three E-S6 pins):**
`expected a DEFINE INDEX on message.(seq) — R3(1) names it 'message_seq' …` · `expected a
DEFINE INDEX on message.(sender, question) for the questions read …` · `the message hot-path
indexes are missing from the LIVE table; declared: []` (reached only AFTER its positive control
passed, so the introspection demonstrably works). No collection error, no fixture failure, no
mypy error.

---

## §10a ESC-1 / ESC-2 ARE RULED — found in the tree, not in the inbox (`d0f84d0`)

The lead's wave-2 message said ESC-1 and ESC-2 were "PENDING the design owner". **They were
ruled while I worked**, in commit `d0f84d0`, which I found by reading `git log` before closing
out — not from any message. (Durable-pull-channel law, working exactly as advertised: the
ruling was in the repo the whole time. Worth noting because the interim state the lead
described — a deferred pin group — was already obsolete when it was described.)

**ESC-1 RULED: Reading B, via a SUCCESS LATCH.** `ok` initializes **False** and is latched
**True** only after `super().call_tool` RETURNS — **no `except` arm at all**. Semantics,
verbatim into the schema comment: *True iff the dispatch RETURNED a result; False on any raise,
cancellation included.* Third state REFUSED (NONE already means "writer did not supply it"; 06
filters cancelled and errored identically; time-to-cancel already lives in `latency_ms`).

The ruling's own framing of my escalation is worth preserving because it generalises: an
`ok=True`-initial flag cleared in `except Exception` **is a failure-class NAME-LIST, and
`CancelledError` is the door it misses** — this repo's instrument lesson reproduced in control
flow. The latch **allowlists the ONE success path** instead of enumerating failures, so there is
no except arm left to get wrong.

**Applied, un-deferring the pin group:**
- `TestACancelledDispatchStillRecordsItsRow` now asserts the row exists **AND `ok is False`**,
  with the latch mechanism and its failure mode in the message.
- The error-leg pin's message now states the ruled semantics rather than "whether the call
  succeeded".
- The module docstring's "deliberately not pinned" section became a **"RULED MID-WAVE"**
  section citing `d0f84d0`; nothing about `ok` is deferred any more.
- **NEW PIN** — `TestTheTraceSchemaDelta::test_the_ok_columns_ruled_semantics_are_documented_
  where_it_is_DEFINED`: the ruling requires the sentence verbatim in the column's comment, so it
  gets an INSTRUMENT rather than a memo (`ok` is a boolean whose meaning is not guessable from
  its name, and 06 filters on it). Keyed on the distinctive clause *"False on any raise,
  cancellation included"* within a 60-line window above the `_TRACE_FIELD_SPECS` assignment — so
  a reflow does not go RED, while the wording the latch exists to correct ("whether the tool
  succeeded") does. **RED now**, for the right reason: the comment does not exist yet.
  **Mutation obligation:** restore the `ok=True`-initial + `except Exception` shape → the
  cancelled leg goes RED (the ruling names this one itself).

**ESC-2 CONFIRM channel A** — the request's lifespan context, on the construction-order
derivation my harness already encoded; Reading B refused as routing-not-sharing. **No harness
change**: it was forcing A already. The module docstring now cites the ruling rather than
resting on my derivation.

**Post-ruling counts:** `test_trace_telemetry.py` **64 failed / 12 passed (76 collected)** — up
from 75/63F by the one new prose pin; the cancellation leg's added `ok` assertion rides an
existing test. Six-suite run (`test_trace_telemetry` + `test_comms_schema` + the four store
suites): **69 failed / 618 passed** = 64 + 3 (E-S6) + 2 (FK-3), i.e. exactly my three RED
groups and nothing else. ruff clean; mypy still **zero in every file I touched** (92 in the
now-COMMITTED surface wave's two files, `7a8e44f`).

---

## §11 Wave-2 self-caught defect, recorded because it is the more useful half

**My first version of the E-S6 control asserted a FALSE property of its own instrument** and
would have shipped a lie in a failure message. It claimed a "documented bound" of the shared
`_index_statements` idiom: that `FIELDS\s+seq$` would still match `FIELDS thread, seq`, and
that the two pins therefore needed the index NAME as a backstop. The assertion FAILED — because
`re.search` needs `FIELDS` + whitespace + `seq` + end-of-line **contiguously**, and `FIELDS`
occurs once, so the pattern is exact in both superset directions.

Two things follow, and both are in the code now:

1. The control was rewritten to assert the property that is TRUE (positive: each pattern sees
   its exact clause; negative: neither `seq, thread` nor `thread, seq` satisfies the
   single-column pattern, and no three-column superset satisfies the composite one), and the
   `(seq)` pin's docstring now states the measured behaviour and cites the control by name
   instead of hand-waving about anchors.
2. The name + exact-count assertions STAY — not because the anchor is insufficient (it is
   sufficient), but as defence in depth against a build that ships the right fields under a
   name nothing else keys on. The reason in the code is now the real one.

This is the same class the main report's §6 D5 pins mechanically for production prose: **a
failure message that promises a check the assertion does not perform is a false gate.** It
appeared inside a control written *by the author of those pins*, in the same session, and only
running it caught it. Worth the adversary's attention as a pattern, not just as a fixed line.

---

## §12 CLOSE-OUT STATUS (appended 2026-07-24, after the lead's ratification)

**Both waves of this contract are RATIFIED and COMMITTED at `bb64324`** ("test(03b): the
telemetry RED contract wave — T-series, oracle parity, message indexes"), which carries all
eight files: this addendum, the main report, `test_trace_telemetry.py` (new),
`test_comms_schema.py`, `test_surreal_schema.py`, `test_surreal_fakes.py`, `_surreal_fakes.py`,
`_surreal_harness.py`. Verified by the author against `git show --stat` with a clean working
tree afterwards, so nothing in either wave lived only in the tree at hand-off.

Lead rulings recorded at ratification:

- **§9.1's file-home deviation is RATIFIED as ruled** — the E-S6 message-index pins stay in
  `test_comms_schema.py`; the instruction naming `test_surreal_schema.py` rested on a premise
  that file cannot satisfy (it cannot see the message DDL), and R3 already pointed at the home
  chosen. **No move.** Recorded here so a future reader does not "correct" the home back.
- **§9.3's shared-name probe** (SEQUENCE and INDEX both named `message_seq`) — pinning it rather
  than remembering it is confirmed as the right call.
- **§10a** (self-serving the `d0f84d0` ESC-1/ESC-2 rulings out of the tree rather than waiting
  for a relay) goes into the packet close-out as the durable-pull-channel law working as
  designed.
- **§11's self-caught control defect** is flagged to the contract-adversary as a PATTERN, not
  just a fixed line, at the author's request.
- Lead independently re-ran and matched the six-suite tail (**69 failed / 618 passed**).

**State at ratification: the contract is RED by design and owes nothing further.** The next
instrument is the contract-adversary — its outstanding duties, as filed: the satisfiability
receipt (0-failed against its own reference build, including the after-lint-cleanups leg), the
19 named mutation-proof obligations (main report §3, M4 and M19 first — they are what prove the
batteries load-bearing in combination), the oracle-change satisfiability across BOTH consumer
suites (§8), and the three pins whose satisfiability the author judged least certain: the
cancellation leg, the wire-handler leg, and the `INFO FOR …` introspection legs.

---

# FIX WAVE (appended 2026-07-24, after the adversary's INSUFFICIENT re-grade)

Grading input: `REPORT-adversary-telemetry-03b-r2.md` (committed `a45f705`), read in full. Its
prototypes were treated as INPUT, not authority — each is marked ADOPTED / ADAPTED / IMPROVED
below with the reason. **The adversary's work found a blocker I could not have seen from inside
my own instrument, and its four-way adjudication of every RED is the reason this wave is small
and targeted rather than a rewrite.**

## §13 The seven missing pin groups

| MP | verdict | what landed | where |
|---|---|---|---|
| **MP-A** (blocker) | **IMPROVED — three legs, not one** | `TestADispatchLandsARealRowInTheRealTraceTable`: the seam dispatches through the production `FastMCP.call_tool` with a **REAL `SurrealStore`** behind the request's lifespan context, and the row is read back with an explicit projection. Legs: SUCCESS · **RAISING** · **declared-identity**. The prototype had the success leg only; the swallow hides a store rejection on the ERROR path identically (an `ok=False` row carrying a bad kwarg is invisible to a success-only leg), and the four enrichment kwargs are the NEW half of the store contract, so a rename/typo in any one of them must die here too. | `test_trace_telemetry.py` + `_app_context_double_over` |
| **MP-B** | **ADOPTED + a control added** | `test_every_registered_tool_traces_when_it_SUCCEEDS`, parametrised over all 16 registry entries, tool manager stubbed so every dispatch RETURNS through the real override. **Added:** an assertion that the stub's text reached the caller — without it the pin could pass while the dispatch had not actually succeeded, which is the "passes for a neighbouring reason" shape. | `TestCoverageIsACheckedVariable` |
| **MP-C** | **IMPROVED — the class, not the instance** | Dropping `strict=True` fixes the instance; it leaves the next inline predicate free to be wrong the same way. The predicate is now `_is_strictly_increasing()` with `TestTheMonotonicityPredicateItself` (5 discriminating cases + an "is it evaluable at all" regression guard). **An instrument with no control is exactly how this defect survived authorship.** | `test_trace_telemetry.py` |
| **MP-D** | **ADOPTED + hardened** | `test_two_dispatches_of_different_durations_record_different_latencies`. **Hardened:** the floor is a FRACTION of the slow probe's own sleep (`_LATENCY_DIFFERENCE_FRACTION`), not an absolute millisecond figure, so retuning the fixture cannot silently weaken it. | `TestTheToolsOutcomeAlwaysWins` |
| **MP-E** | **ADOPTED** | `test_a_zero_argument_call_still_records_the_full_digest` + a dedicated zero-argument probe. Asserts full 64-hex AND equality with the recipe's own value for `{}`. | `TestParamsHashIsTheRuledRecipeAndLeaksNothing` |
| **MP-F** | **ADOPTED — three pins** | The four enrichment columns round-trip when given · are ABSENT (`.get(...) is None`) when omitted · successive calls mint distinct, increasing, **0-based** ordinals. My own ESC-5 oracle edit had no behavioural pins; the adversary's measured mutation (drop four columns + freeze the ordinal → 783 passed) is their discrimination receipt. | `test_surreal_fakes.py::TestRecordTraceFake` |
| **MP-G** | **IMPROVED — a sweep, and it replaces the name-list** | `_telemetry_prose_offenders()` walks every COMMENT and STRING token of `surreal.py`, `surreal_schema.py`, `server.py`, keeps those mentioning a telemetry token, and flags any retired phrase — **so prose written LATER is covered without anyone extending a list.** The three hand-named docstring pins it subsumes are DELETED (net −3 +2, strictly stronger). Scoped by telemetry token on purpose: those modules legitimately say "left for a later phase" about other subsystems, and **a gate that reddens honest prose is a gate someone switches off** — the threat model is the honest author editing a trace docstring. Two-direction control: `test_the_sweep_itself_fires` proves it SEES a corpse and IGNORES both honest telemetry prose and retired phrasing about another subject. | `TestNoProductionProseStillTeachesTheRetiredPlan` |

## §14 The four surviving wrong builds + the oracle mutation — each now has a named killer

| survivor | what it shipped | the pin that kills it now |
|---|---|---|
| **W30** (extra kwarg → every production write raises, swallowed; `traces.total` 0 forever — **#147 reproduced by the packet closing #147**) | telemetry dead in production, green everywhere in test | **MP-A**, all three legs. The success leg dies on the `TypeError` the double used to absorb; the error and identity legs close the same hole on the failure path and on each enrichment kwarg individually |
| **W11** (`if ok and not tool.startswith("probe_"): return` — every SUCCESSFUL real-tool call untraced; denominator becomes "calls that failed") | a garbage decay curve | **MP-B** — 15 of the 16 parametrisations RED (the synthetic probe is the 16th, exactly as the adversary predicted) |
| **P2-const** (`latency_ms = 50.0`) | every row the same duration | **MP-D** — no constant can satisfy a DIFFERENCE |
| **W31** (`params_hash = ""` on empty arguments) | four registered tools collapse into one digest bucket | **MP-E** |
| **oracle mutation** (drop the four columns, freeze the ordinal) | every fake-backed consumer grading against a row the real store never writes | **MP-F — 2 of its 3 pins fire** (round-trip + 0-based ordinals). ⚠ CORRECTED (adversary RG-R2): "all three" was an over-claim — the third pin asserts the OPPOSITE direction (columns ABSENT when not given), which a mutation that DROPS them satisfies, so it cannot fire on this mutation. It is discriminating in its own direction and the adversary proved it separately as **M25b** (make the fake fabricate `""`/`0`/`False` for an unset column → that pin, and only that pin, reddens). Three pins, three directions, two of them relevant to this mutation |
| *(bonus)* **W20** (per-process client-side mint) — passes the 8-way pin | plausible-looking ordinals that are not the engine's | already died to the gap/count pin; its **false comment is corrected** (R3) so the next reader is not told the 8-way pin catches it |

## §15 §2's six guarded-not-∀ rows — each CLOSED

| row | invariant | closed by |
|---|---|---|
| I1 | every dispatch of every registered tool traces | **MP-B** — the SUCCESS cell is now ∀ over the registry; the error cell was already ∀ |
| I2 | the row actually LANDS in the real store | **MP-A** |
| I8 | `params_hash` is the recipe ∀ arguments | **MP-E** (the guard was NON-EMPTY ARGUMENTS) |
| I9 | latency reflects real duration | **MP-D** (the guard was ONE FIXTURE BRACKET) |
| I15 | no production prose teaches the retired plan | **MP-G** (the guard was THREE NAMED DOCSTRINGS) |
| I17 | the oracle mirrors the real row shape | **MP-F** (was UNPINNED) |

Nothing is left justified-but-open: all six were real holes and all six are closed by construction
rather than by argument.

## §16 Residuals R1–R13, each adjudicated individually

| id | verdict | action |
|---|---|---|
| **R1** | **VALID — fixed.** The `ok`-semantics pin could RED a correct build whose sentence was verbatim but wrapped across two `#` lines. A pin that reddens a correct build is a builder trap even when it cannot green a wrong one. | Window widened to span the comment block AND the tuple body; `#` stripped before normalising |
| **R2** | **VALID as over-specification — KEPT deliberately, and now says why.** Parameter ORDER carries no semantics (all keyword-only), so a natural signature is RED cosmetically. It stays because the pin's subject is EXACT-SHAPE parity between two implementations: a set comparison would let the two drift into different orders and then into different NAMES via a one-sided rename. The message now tells a builder to reorder or escalate — **never to weaken it to a set comparison** | message amended |
| **R3** | **VALID — FALSE COMMENT, fixed in both places.** The 8-way pin claimed it kills "an ordinal minted client-side"; measured, a per-process counter passes it. The latency pin claimed it kills "a constant"; measured, 50.0 passes it. Both are the false-gate class **inside my own comments** | both corrected, each naming the pin that DOES kill the build |
| **R4** | **VALID — fixed.** `"row-shaped"` never occurred in `_HOSTILE_BODY`: a vacuous iteration inside a ∀-loop, reading as coverage | fragments hoisted to `_HOSTILE_FRAGMENTS`; each is asserted PRESENT IN THE INPUT before its absence from the row is asserted |
| **R5** | **ACCEPTED — my four mis-stated obligations** (M6 over-claim · M4 over-claim, harmless · M13 under-claim · M19 half-wrong) | corrected in §17, with **M20** adopted as the missing proof |
| **R6** | **VALID — pinned.** Nothing tied the harvest to a REAL tool's declared params | `test_a_real_tools_declared_identity_is_harvested_too` (drives `lore_comms`, values deliberately different from every identity leg) |
| **R7** | **CLOSED rather than recorded.** "Not a regression" is how a silent loosening to `any` ships | `test_the_widened_columns_still_REJECT_a_wrong_typed_value` — `option<int>` widens the DOMAIN, not the TYPE; classified rejection + a legal-value positive control |
| **R8** | **CONFIRMED, not mine.** mypy at my close: **108 errors in 2 files** (`test_comms_tool.py` 102, `test_comms_promise_registry.py` 6) — it has moved three times during this packet (39 → 92 → 126 → 108) as the surface wave commits. **ZERO in any file I touch**, zero from the adversary's reference | flagged to the lead |
| **R9** | **VALID — fixed, and PINNED.** The oracle's docstring taught `ok` as "whether the tool call succeeded" — the exact reading ESC-1 corrected | oracle docstring rewritten with the ruled sentence verbatim; the `ok`-semantics pin now scans the ORACLE as well as the schema module, so the two cannot drift |
| **R10** | **NOTED for the builder.** `record_trace`'s "a single awaitable insert" is accurate enough; the statement is now a `CREATE … object::extend(…)` with a store-side mint | no pin (MP-G's sweep covers the retired-plan vocabulary; this is not a corpse) |
| **R11** | **AGREED.** MP-A is the unit-level analogue of the T7.9 deploy smoke and does **not** replace it: MP-A proves the seam+store agree on a throwaway DB; only the smoke proves it on the deployed artifact against `:18500` | remains a packet-exit obligation the lead owns |
| **R12** | **AGREED** (cross-test-module import of `_field_statement` is the DRY choice; disclosed as D3) | no action |
| **R13** | **NOTED — lead's, already handled.** The design authority moved mid-run under the adversary | no action |

## §17 The obligation list, corrected and extended

**Corrections to my wave-1 list** (adversary §4, all four accepted):

- **M6** — over-claim. A seam-side mint reddens the seam-mint pin ONLY; the store's signature and mint are untouched, so FK-3b and the 8-way pin cannot see it. Those belong to M14/W20.
- **M4** — over-claim, harmless. Coverage stays green for 15 of 16, not 16: `coverage[probe_trace_ok]` also reddens, because that entry is a SUCCEEDING tool.
- **M13** — under-claim. Reverting a widened spec reddens **11** pins, not one column's: un-widened types also break live writes and all four migration legs.
- **M19** — half-wrong. It proves ONE vacuous guard. **M20 (resolve the app context OUTSIDE the swallow) is the correct obligation for the second** (`…_no_reachable_app_context_still_serves_the_tool`), and it discriminates.

**New obligations from this wave** (each stated as the mutation and its exact expected RED set):

| # | mutation | must go RED |
|---|---|---|
| M21 | emission passes one extra keyword to `record_trace` (**W30**) | MP-A's three legs — and NOTHING else in the contract, which is precisely the point |
| M22 | `if ok and not tool.startswith("probe_"): return` (**W11**) | MP-B, 15 of 16 parametrisations |
| M23 | `latency_ms` = any constant inside the bracket | MP-D only (the bracket pin stays green — proving the two are not redundant) |
| M24 | `params_hash = ""` for empty arguments (**W31**) | MP-E only |
| M25 | drop any one of the fake's four enrichment columns / freeze its ordinal | the matching MP-F pin |
| M26 | reintroduce any retired phrase into any trace-related comment or docstring in the three swept modules | the MP-G module leg for that module — **including a NEW docstring nobody listed**, which is the property the name-list lacked |
| M27 | make `_is_strictly_increasing` return True unconditionally | `TestTheMonotonicityPredicateItself` (3 of 5 cases) — the control the original inline predicate never had |
| ~~M28~~ **M28b** | widen `hit_count` to **`option<int \| string>`** (⚠ CORRECTED, adversary RG-R4: the originally-stated `option<any>` is INVALID DDL on 3.2.1 — it crashes `ensure_ready` and reddens 65 unrelated tests, so it would have tested the DDL parser, not the pin. An obligation that cannot isolate its target is not an obligation) | R7's pin (rejection leg) + the two widened-type pins, and nothing else |
| M29 | teach `ok` as "whether the tool call succeeded" in the oracle docstring | the `ok`-semantics pin's ORACLE surface |

## §18 Fix-wave tails (measured 2026-07-24, after the adversary re-grade at `a45f705`)

| gate | before the fix wave | after | reading |
|---|---|---|---|
| `test_trace_telemetry.py` | 64F / 12P (76) | **87 failed / 19 passed (106 collected)**, 0 collection errors | +30 pins: MP-A ×3 · MP-B ×16 + R6 ×1 · MP-D ×1 · MP-E ×1 · R7 ×1 · MP-C predicate control ×6 · MP-G sweep ×3 + control ×1, minus the 3 name-listed prose pins the sweep replaces |
| the SIX graded files | 69F / 618P | **92 failed / 628 passed** | distribution 87 (telemetry) / 3 (E-S6) / 1 (FK-3a) / 1 (FK-3b) — exactly my four RED groups, nothing else |
| oracle blast radius, re-run | 1994P (21 suites) | **1714 passed / 0 failed** (16 suites: every `FakeSurrealStore` consumer + `test_mcp_server` + `test_retry_seam`) | the MP-F pins + the oracle docstring fix broke nothing |
| `uv run ruff check loremaster/` | clean | **clean** | |
| `./scripts/typecheck.sh` | 92 / 2 files | **108 errors / 2 files** (`test_comms_tool.py` 102 · `test_comms_promise_registry.py` 6) | **ZERO in any file I touch** (R8 — the surface wave's, moving as it commits) |

**The 19 green-today pins, each accounted for** (unchanged discipline: a pin that passes today is
justified or it is decoration): 5 delta-is-additive params · 2 index-parser controls · the checked
coverage variable · the synthetic-probe registration · the AC-15 wiring analogue · 2 vacuous-until-
the-seam guards (M19/M20 are their proofs) · **6 monotonicity-predicate control cases** ·
**the prose sweep's own two-direction control**. The last seven are new and are instrument
controls — they SHOULD be green now; that is what makes the instruments trustworthy.

**RED-reason histogram, re-verified after the fix** (no reason is an import, collection, fixture or
mypy error): 58 × empty-recorder / 54 × `assert 0 == 1` (no seam) · 9 × `TypeError: record_trace()
got an unexpected keyword argument 'agent'` · 5 × missing `DEFINE FIELD` · 3 × the MP-G sweep
naming its offenders · 2 × `TracingFastMCP does not exist` · 2 × `assert None is not None` ·
the sequence / index / migration / real-store legs.

**Two defects I caught in my own fix wave by RUNNING it, recorded because the pattern is the
finding:**
1. The R7 pin first asserted `"hit_count" in str(error)` — the store's classifier deliberately
   REDACTS the field detail into the server log, so that assertion was **unsatisfiable for every
   build**: the same cannot-pass class as MP-C, written by the author who had just spent the wave
   fixing MP-C. It now asserts the classified error CLASS (`field coercion`) with a legal-value
   positive control.
2. The MP-B stub needed its own "did the dispatch actually succeed" assertion, or the pin could
   have passed while the tool never returned — the neighbouring-reason shape.
   **Both were invisible to inspection and obvious on execution.** A pin is not a pin until it has
   been run against something.

## §19 What I did NOT change, and why

- **The `_TraceRecorder` double stays** for every seam pin except MP-A. It is the right instrument
  for WHAT the seam records (a real store cannot show you the kwargs it never received) and the
  wrong one for WHETHER the store accepts it. MP-A adds the second instrument rather than replacing
  the first; deleting the double would cost every identity/failure-posture leg its precision.
- **The bracket latency pin stays** beside MP-D. It kills 0 and seconds (M18/W16 die on it alone);
  MP-D kills constants. Neither subsumes the other, and M23 is the obligation that proves it.
- **FK-3b's parameter-ORDER assertion stays** (R2) — with the reason now written into the pin, and
  an explicit instruction not to weaken it to a set comparison.
- **No pin was weakened anywhere in this wave.** The three deleted prose pins were replaced by a
  strictly stronger ∀ sweep, which is the only deletion.

---

# FIX WAVE 2 (appended 2026-07-24, after the re-grade at `20fc9f7` — INSUFFICIENT narrowly on W33)

Four items, all landed. The re-grade confirmed every wave-1 fix (all seven MP groups landed, every
survivor dies to its named killer, MP-C genuinely fixed, reference 485/0 and 720/0) and found ONE
new hole.

## §20 MP-H — the uncovered cell (W33)

**The hole, stated as the matrix it is:** coverage of "the seam's call is one the store ACCEPTS"
had four cells and three instruments. MP-A drives SYNTHETIC probes into a REAL store; MP-B drives
REAL tools into the DOUBLE; nothing drove a REAL registered tool into a REAL store. **W33** —
`**({"request_id": "x"} if tool.startswith("lore_") else {})` — lives in that cell and scored
485 passed / 0 failed, identical to a correct build, while shipping the packet's worst outcome:
every real tool's trace write raises, the ruled swallow logs it, `traces.total` stays 0. #147, a
third time, by a different door.

**Landed: `test_every_REAL_registered_tool_lands_a_real_row` — ADAPTED, and stronger than the
prototype.** The prototype dispatched ONE real tool (`lore_comms`); a build keyed on a single
tool NAME rather than the `lore_` prefix walks straight through that, and the whole lesson of this
contract's own history is that a pin must cover the CELL, not out-guess the shapes. So the pin
sweeps the **ENTIRE registry against ONE real store**: 16 dispatches, one database, and the
recorded tool set asserted EQUAL to the registry — a checked variable again, with its
non-emptiness guard. That is cheaper than 16 parametrised database mints and closes the cell ∀
tools rather than for one.

Both mechanisms are reused unchanged rather than reinvented: the tool-manager stub is MP-B's (so
no tool body needs a full AppContext) and the real store behind the request's lifespan context is
MP-A's. RED now for the right reason: `0 of 16 dispatches landed a row in the REAL trace table`.

**On the shared miss:** the adversary noted this cell is one it missed too — its MP-A prototype
used a synthetic subject, and my improvement extended the LEGS while keeping that SUBJECT. Worth
recording as the pattern: *when you improve a prototype, check whether you improved along the axis
that was actually thin.* I added legs (success/error/identity) and left the subject axis
untouched, and the subject axis was where the hole was.

## §21 The three corrections

| item | verdict | action |
|---|---|---|
| **RG-R1** — the MP-G control's negative leg passed for a fixture reason: its sample contained NO retired phrase, so an UNSCOPED sweep returned `[]` for it too and the leg could not tell a correct instrument from a broken one | **VALID.** A control that cannot distinguish is the exact defect I spent wave 1 fixing in others' name — here in my own control, one level down | the negative sample now carries a retired phrase about a NON-telemetry subject (`"app-level retry/backoff is left for a later serving-layer phase"`), so an unscoped sweep FAILS this leg and scoping is what the control proves. Comment records the measurement |
| **RG-R2** — §14 claimed the oracle mutation dies to "MP-F, all three pins" | **OVER-CLAIM.** 2 of 3 fire; the third asserts the OPPOSITE direction (columns ABSENT when unset), which a mutation that DROPS them satisfies | §14 corrected in place; **M25b** (make the fake fabricate `""`/`0`/`False`) recorded as that pin's own proof. Three pins, three directions |
| **RG-R4** — M28's stated mutation `option<any>` | **INVALID DDL on 3.2.1** — crashes `ensure_ready` and reddens 65 unrelated tests, i.e. it would test the DDL parser rather than R7's pin. An obligation that cannot isolate its target is not an obligation | replaced by **M28b** (`option<int \| string>`), which reddens exactly R7 + the two widened-type pins |

**RG-R3 (the `test_message_ledger.py` FK-4 pair) — no action, per the lead:** measured STALE, a
transient mid-edit snapshot of the parallel surface wave; the live tree is clean there. My own
close-out measurement agrees (see §22: zero errors in `test_message_ledger.py`). **RG-R5/R6/R7**
need no action — R5 confirms my two self-caught defects, R6 agrees with keeping the parameter-order
parity assertion, R7 keeps the T7.9 deploy smoke open as a packet-exit obligation that MP-A/MP-H do
NOT replace (they prove seam+store agree on a throwaway DB; only the smoke proves it against the
deployed artifact on `:18500`).

## §22 Fix-wave-2 tails (measured 2026-07-24, at the fix-wave-2 tree)

| gate | fix wave 1 | fix wave 2 | reading |
|---|---|---|---|
| `test_trace_telemetry.py` | 87F / 19P (106) | **88 failed / 19 passed (107 collected)**, 0 collection errors | +1 pin: MP-H. Green count UNCHANGED — the MP-G control fix stays green (it must: the correct instrument passes it) and MP-H is RED |
| the SIX graded files | 92F / 628P | **93 failed / 628 passed** | 88 / 3 (E-S6) / 1 (FK-3a) / 1 (FK-3b) — exactly my four RED groups |
| `uv run ruff check loremaster/` | clean | **clean** | |
| `./scripts/typecheck.sh` | 108 / 2 files | **108 errors / 2 files** (`test_comms_tool.py` 102 · `test_comms_promise_registry.py` 6) | **ZERO in any file I touch**, and zero in `test_message_ledger.py` — corroborating the lead's stale-snapshot reading of RG-R3 |

MP-H's RED reason, verified individually: `0 of 16 dispatches landed a row in the REAL trace
table` (missing: all 16) — a missing production seam, not a fixture or harness fault. The MP-G
control leg passes (`1 passed`), as a correct instrument must.

## §23 The contract's own history, in one line, because it is the transferable part

Three grading rounds found three holes of ONE shape: **the instrument covered the property and
missed a CELL of the input space** — outcome (error vs success: W11), store (double vs real: W30),
subject (synthetic vs real tool: W33). Each was closed by crossing two mechanisms the contract
already had, never by inventing a third. **When a battery feels complete, enumerate its axes and
look for the cell nobody dispatched into** — that question would have found all three at
authorship, and it is cheaper to ask than any of the three fixes was to write.

---

# FIX WAVE 3 (appended 2026-07-24, after the closing re-grade — the STRUCTURAL fix)

The closing re-grade verified MP-H kills W33/D2/D3/D5 and found two more conditional survivors on
the OUTCOME axis: **D4** (bad kwarg only on a real tool's FAILURE path) and **D6** (only on a
CANCELLED dispatch). Rather than a fourth cell-pin, it recommended the structural form. Adopted.

## §24 The double now BINDS against the real signature

`_TraceRecorder.record_trace` binds every call through
`inspect.signature(SurrealStore.record_trace)` before recording anything, so **the double can
never accept what the real signature would reject.** A keyword the real store does not declare —
or a required one the seam forgot — raises exactly as it would in production, and nothing is
recorded, so the pin expecting a row fails on the row's ABSENCE (which is precisely how production
behaves: T5.1's ruled swallow logs the `TypeError` and serves the tool anyway).

**What that converts, at a stroke:** every double-backed pin in this file becomes an end-to-end
signature check — success, error, cancellation, all eight identity legs, the hostile body, the
whole params-hash battery, all 16 coverage parametrisations. Adversary-measured on the fixed form:
correct build **107 passed**; **D4 → 15 failed**; **D6 → 1 failed**; **W33 → 32 failed**;
**D2 → 3 failed**.

**Why this is the right shape and not just a bigger net.** Three grading rounds found ONE defect
five times, each time in a different cell of the same matrix (outcome × store × subject): W11
(success cell), W30 (real-store cell), W33 (real-tool cell), D4 (real-tool-failure cell), D6
(cancelled cell). Chasing cells one pin at a time IS the enumerate-the-forbidden shape this repo
has watched lose six times — the forbidden set is unbounded, and each new pin only proves the
previous enumeration was incomplete. Binding against the real signature holds the whole matrix by
construction, and **signature drift now reddens every consumer instantly** instead of silently
widening the double. The safe set (what the real store declares) is small, enumerable, and — the
part that matters — DERIVED rather than transcribed.

**Honest bound, stated on the recorder itself so nobody over-trusts it:** `Signature.bind` checks
NAMES and ARITY, never TYPES or values. A wrong-TYPED argument still passes the double and is
caught only against the real engine — which is what MP-A/MP-H and R7's rejection pin are for. The
binder replaces the cell-chasing, not the real-store legs.

## §25 The binder's own control — `TestTheDoubleBindsAgainstTheRealSignature` (4 pins, green)

Every double-backed pin now leans on the binder, so a binder that silently accepted everything
would return the contract to the state three rounds found holes in — **invisibly, because a
permissive double makes pins PASS.** That is the MP-C lesson (an instrument with no control) applied
to the harness itself, before an adversary has to apply it for me. Three directions plus a
derivation, because a one-directional control would also be satisfied by a binder that rejects
everything:

| leg | proves |
|---|---|
| an undeclared keyword is REJECTED, **naming it**, and NOTHING is recorded | the binder fires, actionably, and leaves no row |
| the legal call is ACCEPTED | it is not simply rejecting everything (the positive control) |
| a MISSING required argument is REJECTED, naming it | the other direction of arity — a build that forgets `params_hash` is as broken as one that invents a column |
| **every parameter the REAL signature declares is ACCEPTED**, derived via `inspect.signature` | the binder IS the signature, not a name list transcribed from it: a parameter added to production later is covered without editing this test |

⚠ One fixture correction made while landing it, worth recording as the same class it belongs to:
the legal-call fixture first carried only the three post-T8-required names, so both accept-legs
were RED **today** for T8's reason (`hit_count` is still REQUIRED at HEAD) — a control failing for
a neighbouring reason isolates nothing. The fixture now names the set that binds under BOTH the
committed and the T8 signature; T8's own change stays pinned by FK-3b, where it belongs.

## §26 Fix-wave-3 tails (measured 2026-07-24)

| gate | fix wave 2 | fix wave 3 | reading |
|---|---|---|---|
| `test_trace_telemetry.py` | 88F / 19P (107) | **88 failed / 23 passed (111 collected)** | +4 binder-control pins, all GREEN (a correct instrument must pass its own control); **RED count UNCHANGED at 88** — the binder cannot alter a RED reason today because no seam calls the double yet, which is exactly the "changes nothing until there is a build" property a harness fix should have |
| the SIX graded files | 93F / 628P | **93 failed / 632 passed** | 88 / 3 (E-S6) / 1 (FK-3a) / 1 (FK-3b) — my four RED groups, unchanged; +4 passes are the new controls |
| `uv run ruff check loremaster/` | clean | **clean** | |
| `./scripts/typecheck.sh` | 108 / 2 files | **108 errors / 2 files** | ZERO in any file I touch |

Green-today accounting, complete at 23: 5 delta-is-additive · 2 index-parser controls · the checked
coverage variable · synthetic-probe registration · the AC-15 wiring analogue · 2 vacuous-until-the-seam
guards (M19/M20) · 6 monotonicity-predicate cases · the prose sweep's control · **4 binder controls**.
Fourteen of the twenty-three are instrument controls — which is the shape a contract should have:
the pins that grade production are RED, and the pins that grade the INSTRUMENTS are green.

## §27 New obligations from this wave

| # | mutation | must go RED |
|---|---|---|
| M30 | remove the `bind()` call from `_TraceRecorder.record_trace` (a permissive double) | the binder's reject-unknown and reject-missing legs — and, on a build carrying any conditional bad kwarg (D4/D6/W33), the pins those defects live in stop reddening, which is the property M31 measures |
| M31 | `_TraceRecorder` binds against a HARDCODED name list instead of `inspect.signature` | `…_every_parameter_the_REAL_signature_declares_is_ACCEPTED` the moment production's signature and the list disagree — i.e. at the next signature change, which is when a copy always fails |
| M32 | bad kwarg only on the FAILURE path (**D4**) / only on a CANCELLED dispatch (**D6**) | 15 pins / 1 pin respectively, via the binder — no new cell-pin required, which is the point of §24 |

---

# FIX WAVE 4 (appended 2026-07-24, after the final confirmation pass — MP-I, the last cell)

The confirmation pass verified the binder in its committed form and swept six shapes of its own
invention. Five die. One survives: **D9b**.

## §28 MP-I — the cell `bind()` structurally cannot cover

**D9b, and why it is not an epsilon:** a LEGAL keyword carrying a WRONG-TYPED value, read out of
`arguments.get("depth", 7)`. Its static type is `Any`, so **mypy reports no issues**, and
`Signature.bind` checks names and arity and never types — so the binder, which closed the whole
NAME family at a stroke, is structurally blind to it. Measured surviving at **490 passed / 0
failed with the type gate clean**. Only the engine rejects it, and only on a path some pin actually
dispatches: MP-H covers real tools on the SUCCESS path; the real-tool × ERROR × real-store cell had
no dispatcher at all.

The lead ruled the fork **CLOSE** (over pin-the-bound), and it is the right call at this price: six
lines against a defect whose production outcome is the errored population vanishing from the
denominator — biasing packet 06's decay curve toward healthy sessions, which is exactly the
direction that would argue against forced drains.

**Landed: `test_every_REAL_registered_tool_that_FAILS_lands_a_real_row`** — MP-H's loop with a
RAISING stub. Same mechanism, same registry-equality assertion, `ok is False` on every row. It
closes the NAME family in this cell too (D4 dies here as well as at the binder).

**The stub raises `ToolError`, deliberately and with a receipt.** That is the shape the real tool
manager surfaces and the one `_dispatch_ignoring_tool_failure` suppresses; a `RuntimeError` stub
escapes the dispatch and the probe fails for its own reason. **The adversary hit exactly that on
its first run of this prototype and disclosed it** — so this wave has now paid the same "a pin is
not a pin until it has been run" lesson on both sides of the grading table, three times total (my
`zip(strict=True)`, my `"hit_count" in str(error)`, its `RuntimeError` stub). Verified here: the
pin's RED is the row-set assertion, reached AFTER the loop completes, which proves the suppression
works.

## §29 Fix-wave-4 tails (measured 2026-07-24)

| gate | fix wave 3 | fix wave 4 | reading |
|---|---|---|---|
| `test_trace_telemetry.py` | 88F / 23P (111) | **89 failed / 23 passed (112 collected)** | +1 pin (MP-I), RED for the right reason: `0 of 16 FAILING dispatches landed a row in the REAL trace table` |
| the SIX graded files | 93F / 632P | **94 failed / 632 passed** | 89 / 3 (E-S6) / 1 (FK-3a) / 1 (FK-3b) — my four RED groups, nothing else |
| `uv run ruff check loremaster/` | clean | **clean** | |
| `./scripts/typecheck.sh` | 108 / 2 files | **108 errors / 2 files** (`test_comms_tool.py` 102 · `test_comms_promise_registry.py` 6) | ZERO in any file I touch |

## §30 The real-store cell table, now complete

| | DOUBLE (binder-checked NAMES + arity) | REAL store (engine-checked TYPES + values) |
|---|---|---|
| **synthetic probe · success** | every seam pin | MP-A leg 1 |
| **synthetic probe · error** | the raising pin | MP-A leg 2 |
| **synthetic probe · cancel** | the cancellation pin | — (accepted: the cancelled write is proven against the double; the engine path is covered by the four other cells) |
| **real tool · success** | MP-B (16) + R6 | **MP-H** (16, one store) |
| **real tool · error** | the coverage battery (16) | **MP-I** (16, one store) ← was empty |

Six grading rounds' worth of survivors — W11, W30, W33, D2, D4, D6, D9b — were all one defect
wearing seven different cells of this table. It is complete now, and the two axes that made it
complete are cheap: **the binder** holds every name/arity case by construction, and **two registry
loops** (success + error) hold every type/value case against the real engine. Neither is a list
anyone has to remember to extend.

