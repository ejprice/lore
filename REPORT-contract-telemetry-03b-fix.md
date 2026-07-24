# REPORT-contract-telemetry-03b-fix — telemetry contract FIX WAVE (packet 03b, delta rows F/G/H)

brief-base v6 read

> All measurements taken 2026-07-24 against lore HEAD `0921157` (branch
> `feat/surreal-unification`), engine spike-surreal **3.2.1** on `ws://127.0.0.1:18000`.
> Satisfiability + every mutation was run in a provenance-verified scratch copy against a
> CORRECT reference build I authored there (production untouched in the real repo). Claims are
> dated where made; "RED"/"survives" are runs at this SHA, not later states.

---

## SUMMARY BLOCK

- **State: DONE-WITH-DECISIONS.** Contract INSUFFICIENT → closed. Telemetry pins **41 → 53**
  (12 new methods + 2 in-place strengthenings: MP11 S7-rung pin, the #107 pin gains §1.4 legs).
- **MP1–MP11 all closed.** MP1 `test_seq_is_typed_int_not_option` (+#107 live legs). MP2
  cancel-writes-row + cancel-leak companion. MP3 lifetime-uniqueness + map-retention (interlock).
  MP4 heartbeat + register identity. MP5 limit>pending served-count. MP6 failed-write-logged. MP7
  new-col types + index-names-both. MP8 zero-arg params_hash. MP9 session-declared-only. MP11 `is`.
- **7 amendments (Part B), each MUTATION-PROVEN, STRENGTHEN-ONLY:** #1 schema field-def → asserts
  loosened `option<>` + the 5 new col types + seq-not-option. #2 fakes signature → new 11-name list
  (⚠ REQUIRES builder R8, below). #3–6 four `TestTraceRoundTrip` pins → `_create_trace` supplies
  `seq`. #7 flagship #107 whole-schema pin → seq in trace seed (keeps survival) + new-writes-must-
  mint assertion (SHARPENED, NOT weakened; goes RED under `option<int>`).
- **WB9 mutation** (`caller = str(id(session))`, 400 non-overlapping sessions) → MP3a uniqueness
  **RED**. **`option<int>` flip** → MP1 + #107 + MP7 (contract) AND amended field-def + flagship
  migration pins all **RED**. Every listed WB (WB1/2/4/5/6/22/30/32 + MP9-resolved) proven RED.
- **Satisfiability: 1022 passed / 0 failed across ALL FIVE files** against the correct reference
  (telemetry alone 53/53). Receipts §Satisfiability, §Mutations.
- **Provenance:** `loremaster.__file__ = /home/ejprice/scratch/ct-telemetry-fix/loremaster/loremaster/__init__.py`
  (via `scripts/scratch_copy.sh`, provenance-asserted). Real-repo production + `_surreal_fakes.py`
  UNTOUCHED; footprint = the 4 authorized test files only.
- **3 REQUIRED builder obligations** (the correct build does what the adversary's minimal reference
  did NOT — a pin goes RED for each until the builder does it): §Escalations E1 register-annotate
  (§S7 item 2), E2 declared-session-not-resolved (§S8 MP9), E3 fake R8 update.
- **1 flagged residual (8th-edit, not authorized): `test_trace_rejects_undeclared_field`** now
  lacks `seq`; still green but for a masked reason. Fix named in §Residuals.
- **No worktree** (scratch copy, discardable). No production/doc/sibling-file edits.

---

## Provenance & method

`./scripts/scratch_copy.sh /home/ejprice/scratch/ct-telemetry-fix` → provenance asserted inside the
copy. I installed the adversary's reference build there, then authored the CORRECT reference (three
corrections the adversary's minimal 41/41 build lacked — E1/E2/E3 below), copied my edited test
files in, and ran satisfiability + every mutation against it. Every mutation restored from a
byte backup (`/tmp/refbackup/`); the contract returned to its pass count after each.

The reference production diff (scratch only) = the adversary's delta rows F/G (schema 5 cols +
`session`/`hit_count`→`option<>` + `seq int` + `DEFINE SEQUENCE` + `(caller,seq)` index; the
`TracingFastMCP` seam; `object::extend($content,{seq: sequence::nextval})` mint) **plus** my three
corrections and the R8 fake-signature update.

---

## Part A — the missing pins (adversary §8), all closed

Map MP → pin(s) in `test_trace_telemetry.py`:

| MP | pin(s) | catches |
|---|---|---|
| **MP1** | `TestTheTraceSchemaDelta::test_seq_is_typed_int_not_option` (offline) + `test_the_new_columns_land_on_an_ALREADY_EXISTING_trace_table` legs (c)/(d) (live) | WB3 `option<int>` flip; a seq-less write; an UPDATE-poisoned pre-03b row |
| **MP2** | `TestTelemetrySurvivesCancellation::test_a_cancelled_dispatch_still_writes_its_row` + `…::test_annotations_do_not_leak_after_a_cancelled_call` | WB30 (`except Exception`, not `finally`); a non-request-local channel cleaned only off the `finally` |
| **MP3** | `TestTheCallerKeyAcrossLifetimes::test_the_caller_key_is_unique_across_session_lifetimes` (400 freed sessions) + `…::test_the_caller_key_map_does_not_retain_finished_sessions` (weakref, no internal-symbol naming) | WB9 `str(id())`; WB32 plain dict — the INTERLOCK (neither pin alone) |
| **MP4** | `TestCommsActionsAnnotateIdentity::test_a_heartbeat_records_the_resolved_agent_and_declared_session` + `…::test_a_register_records_the_resolved_agent_and_declared_session` | WB1 drain-only annotator; the register-path gap (§S7 item 2) |
| **MP5** | `TestARealDrainWritesAnEnrichedRow::test_a_drain_whose_limit_exceeds_pending_records_the_served_count` | WB2 `hit_count = limit` (the arithmetic-alignment escape) |
| **MP6** | `TestTelemetryNeverBreaksTheCall::test_a_failing_trace_write_is_logged_loudly` | WB4 `except Exception: pass` (#147 silent-zero inside its own fix) |
| **MP7** | `TestTheTraceSchemaDelta::test_the_new_columns_and_index_are_typed_and_named` | WB5 (token_cost/model deleted); WB6 (index on wrong field / wrong order) |
| **MP8** | `TestTheSeamRecordsItsOwnFieldsHonestly::test_a_zero_argument_call_records_a_non_empty_params_hash` | WB22 blank digest on empty args |
| **MP9** | `TestCommsActionsAnnotateIdentity::test_trace_session_records_only_what_the_call_declared` | a build annotating `agent_row.session` (inferred) instead of the declared arg |
| **MP10** | Part B (the 7 collateral pins adjudicated + amended) | — |
| **MP11** | in-place amend `TestTheS7RungSelectionFact::test_the_server_session_object_is_per_mcp_session` — holds the `ServerSession` objects alive, compares with `is` (not `id()` ints) | a future per-request session missed by address reuse |

### MP3 — how the retention half avoids naming the internal map

`test_the_caller_key_map_does_not_retain_finished_sessions` holds a `weakref.ref` to a session,
drives one seam dispatch (which mints against it), drops the strong ref, `gc.collect()`s, and
asserts the weakref is dead. A plain `dict` (WB32) keeps a STRONG ref → the object stays reachable →
weakref alive → RED. A `WeakKeyDictionary` → collected → weakref dead → GREEN. This observes
retention WITHOUT binding any production symbol name (the design names a `WeakKeyDictionary` but not
a symbol). A non-vacuity guard (the seam must have minted a caller) runs first.

### MP2 — the cancellation subtlety, resolved empirically

A single `task.cancel()` delivers ONE `CancelledError`, consumed inside the handler; the seam's
plain `finally` write then completes (measured: the reference writes 1 row on cancellation). So
`asyncio.shield` is **not required** for the write to survive — the requirement is satisfiable by a
plain `finally`, and the pin demands exactly that. The cancel-leak companion needed care: it uses a
locally-registered **annotate-then-sleep** probe so the cancel lands AFTER the annotation is
contributed but BEFORE cleanup (a probe that annotates-then-returns has no window and the pin cannot
discriminate — I hit this and fixed it; see §Mutations).

---

## Part B — the 7 authorized amendments (each strengthen-only, mutation-proven)

| # | file::pin | change | what it now catches |
|---|---|---|---|
| 1 | `test_surreal_schema.py::TestTraceTableFieldDefinitions::test_trace_core_scalar_fields_are_defined` | `hit_count`→`option<int>`, `session`→`option<string>`; + assert caller/seq/agent/pending/peeked types; + `seq` is `int` NOT `option` | the loosening landed; seq-not-option; new-col type drift |
| 2 | `test_surreal_fakes.py::TestRecordTraceFake::test_record_trace_signature_matches_real_store` | expected list → the new 11-name signature | real↔fake signature parity ⚠ **requires builder R8 (E3)** |
| 3–6 | `test_surreal_schema.py::TestTraceRoundTrip::{test_trace_probe_round_trips_core_fields, test_trace_ts_is_auto_populated_when_omitted, test_trace_optional_columns_absent_when_omitted, test_trace_optional_columns_round_trip_when_given}` | one edit to the shared `_create_trace` helper (supply `seq`) fixes all four | the seq mint is now required — a seq-less raw CREATE is rejected |
| 7 | `test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore::test_the_whole_schema_migrates_an_existing_populated_store` | `seq` added to the trace seed (row still survives, hit_count/session still round-trip) **+ a new "a seq-less trace write is REJECTED" assertion** in the constraints-still-bite section | KEEPS all prior assertions; GAINS new-writes-must-mint; goes RED under `option<int>` (cannot be greened by making the schema silent) |

**#7 is SHARPENED, not weakened** — measured: under `option<int>` the added assertion goes RED (a
seq-less CREATE would succeed). The "old row is UPDATE-poisoned" half of the §1.4 truth lives in the
telemetry contract's dedicated #107 pin (which owns a genuine pre-seq legacy row); the flagship
whole-schema pin applies the current schema throughout, so its trace row is legitimately new-shaped
(minted). I judged this the non-weakening split; **if the lead wants the flagship pin itself to also
host a pre-seq legacy trace row, say so** — it would mean interleaving old-trace DDL into a
monolithic whole-schema pin, which I did not do unilaterally.

The 4 round-trip helper edit and the `_TRACE_SEQ` constant beside it are the minimal way to amend
pins #3–6 (they share `_create_trace`); I count them as part of those four amendments, not an 8th
edit.

---

## Before → after counts per file

| file | test methods before → after | lines |
|---|---|---|
| `test_trace_telemetry.py` | 41 → **53** (+12 new; 2 in-place strengthenings) | +641 |
| `test_surreal_schema.py` | unchanged count (1 pin amended + `_create_trace` helper + `_TRACE_SEQ`) | +26/−3 |
| `test_surreal_store.py` | unchanged count (flagship pin sharpened) | +24 |
| `test_surreal_fakes.py` | unchanged count (signature list amended) | +11/−2 |

Timing-sensitive pins (cancellation + MP3 400-session lifetime) verified stable **3/3 under
`-n auto`**.

## Satisfiability

```
$ uv run pytest -n auto -q test_trace_telemetry.py test_surreal_store.py \
      test_surreal_schema.py test_surreal_fakes.py test_mcp_server.py     # vs CORRECT reference
1022 passed, 5 warnings in 109.81s
$ uv run pytest -n auto -q test_trace_telemetry.py                        # telemetry alone
53 passed in 6.66s
```
Provenance printed each run: `…/scratch/ct-telemetry-fix/loremaster/loremaster/__init__.py`.

Gates on the real-repo edited files: `ruff check` **All checks passed!**; `typecheck.sh` — my
changes add **ZERO** new mypy errors (verified by `git stash`: the 6 `record_trace(caller=)` errors
in the FROZEN Section H pre-exist at HEAD; the residual errors are all the RED-by-design forward-ref
class, design residual #8, which vanish when the builder lands rows F/G). The contract COLLECTS
cleanly in the real repo (53 tests) and is RED-for-the-right-reason (runtime `AttributeError`/
`AssertionError` naming the missing seam, never a collection error).

---

## Mutations (break → RED → restore; run `-n0` against the correct reference)

| mutation | target pin | result |
|---|---|---|
| **WB9** `caller = str(id(session))` | MP3a uniqueness (400 sessions) | **RED** ✓ |
| **WB32** plain `dict` caller map | MP3b retention | **RED** ✓ (and uniqueness GREEN — interlock) |
| **`option<int>`** flip (`seq` spec) | MP1 seq-int, #107 pin, MP7 | **all RED** ✓ (contract); also amended field-def + flagship migration RED |
| **WB30** emit in `except Exception`, not `finally` | MP2 cancel-writes-row | **RED** ✓ |
| module-dict channel cleaned only at end (not `finally`) | MP2 cancel-leak companion | **RED** ✓ (existing sequential leak pins GREEN on same build — unique BaseException-path coverage) |
| **WB1** drain-only annotator | MP4 heartbeat | **RED** ✓ |
| register-path annotate removed only | MP4 register | **RED** ✓ (heartbeat GREEN — control) |
| MP9-resolved: annotate `agent_row.session` (inferred) | MP9 declared-only | **RED** ✓ |
| **WB2** `hit_count = limit` | MP5 | **RED** ✓ |
| **WB4** `except Exception: pass` on failed write | MP6 | **RED** ✓ (never-fails-call control GREEN) |
| **WB22** blank digest on empty args | MP8 | **RED** ✓ |
| **WB5** delete token_cost/model specs | MP7 | **RED** ✓ |
| **WB6** index on `(tool)`; **WB6b** `(seq, caller)` reversed | MP7 | **both RED** ✓ |

⚠ **I found and fixed a FALSE GATE in my own MP7 index check during mutation.** The first draft did
`index_statement.find("caller")` / `.find("seq")` over the WHOLE statement — but the index NAME
`trace_caller_seq` itself contains both substrings, so WB6 (index on `tool`) SURVIVED (passed for
the name, not the fields). Fixed to split on `" FIELDS "` and read the fields clause only; WB6 and
the reversed-order variant both go RED now. (This is exactly the P2 false-gate / name-substring
class — caught because I mutation-proved every pin instead of trusting it.)

---

## Escalations — 3 REQUIRED builder obligations (the correct build ≠ the adversary's minimal one)

The adversary's reference build reached 41/41 but did NOT satisfy the design rulings on three
points. My CORRECT reference (in scratch) fixes all three, and the corresponding pins ENFORCE them.
Each is a thing the builder MUST do or the named pin stays RED. The lead should carry these into the
builder brief:

- **E1 — annotate the REGISTER path (§S7 item 2: "every comms row carries … agent").** `register`
  has `requires_registration=False`, so it does NOT ride the dispatcher's touch→annotate branch;
  the agent is minted inside `_comms_register`. The builder must add
  `_annotate_trace(agent=str(result.agent.id), session=session)` there. Otherwise an agent that
  registers and then only makes generic calls never binds its caller key to its identity ("the
  FIRST lore call binds its key" is false). Pin: `test_a_register_records_the_resolved_agent_and_declared_session`.
  *If the operator rules register-annotation out-of-scope for 03b, drop that one pin — but the join
  design (§S7 item 2) reads it as required, so I pinned it.*
- **E2 — annotate the DECLARED session, NEVER the resolved `agent_row.session` (§S8 MP9).** The
  comms annotation must use the call's own `session=` argument (→ `NONE` when omitted), not the
  agent row's stored session. The adversary's reference wrote `agent_row.session` (the reading MP9
  OVERRULED). Pin: `test_trace_session_records_only_what_the_call_declared` (a heartbeat that omits
  `session=` must record `NONE`, even though the server can resolve one).
- **E3 — update `FakeSurrealStore.record_trace` (adversary R8).** `_surreal_fakes.py` (the fake
  DEFINITION) is **NOT in my writable set**, so I could not land this in the real repo. Amendment #2
  asserts real↔fake signature parity; it stays RED until the builder updates the fake to the new
  11-name signature. My satisfiability includes that update in the scratch reference. This is the
  one-implementation smell the adversary flagged (three `record_trace` shapes for one seam) — the
  builder must be told the fake is in scope.

## Residuals & flags

- **`test_surreal_schema.py::TestTraceRoundTrip::test_trace_rejects_undeclared_field`** (NOT one of
  my 7 authorized amendments, so I did not touch it): its inline CREATE now omits `seq` too, so
  under the new schema it raises on EITHER the missing seq OR the rogue field — it stays green but
  for a **masked/compound reason** (the rogue-field rejection it exists to prove may never be
  reached). **Fix (an 8th edit I am not authorized to make): add `"seq": <n>` to its content** so
  only the undeclared field can trigger the rejection. Flagged for the lead to authorize.
- **MP11 is hygiene, not a live-defect fix.** The adversary tried and could not induce a false green
  from the `id()`-int comparison (3/3). My amendment (hold the `ServerSession` objects alive, compare
  with `is`) removes the address-reuse exposure structurally; there is no live mutation to prove it
  RED because the SDK mints one session per MCP session today.
- **Production `:18500` trace count = 0 (S8-E3 ground 1) — NOT re-derived by me.** I do not write to
  prod and did not run a read against `:18500`. E3's stronger ground is code-derived and holds
  regardless: `record_trace` has had ZERO production callers in any shipped image (so no store can
  hold organic trace rows). I relied on that, not on a live prod count.
- **`_LIFETIME_SESSIONS = 400`** matches the regime the adversary measured (400 sessions → 17
  `str(id)` keys). RED already fires at 200; 400 is margin, and the seam call is ~0.05 ms so the pin
  is not a wall-clock burden.
- **Sibling-wave files** `test_comms_tool.py` / `test_comms_promise_registry.py` show as modified in
  the working tree — **that is the live sibling wave, not me.** My footprint is exactly the 4
  authorized test files; production, docs, `_message_fakes.py`, and the real `_surreal_fakes.py`
  DEFINITION are untouched.
- **Scratch copy** `/home/ejprice/scratch/ct-telemetry-fix` is a discardable `scratch_copy.sh` tree
  (not a git worktree). Discard when the wave closes.
