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
