# REPORT-contract-telemetry-03b-r2 — the T-series telemetry contract (packet 03b)

brief-base v6 read

> **WAVE 2 (lead rulings relayed 2026-07-24, same session): ESC-5 GRANTED · E-S6 assigned.**
> Both applied; see **§8** for the ESC-5 oracle edit, **§9** for the E-S6 message-index pins
> (including a **file-home correction** to the lead's instruction — the pins had to go in
> `test_comms_schema.py`, not `test_surreal_schema.py`, and the derivation is in §9.1), and
> **§10** for the wave-2 tails. Rulings recorded: ESC-3 and ESC-4 ACCEPTED as translated ·
> ESC-6 covered by the surface sibling · ESC-7 confirmed as a packet-exit obligation the lead
> owns · ESC-8 acknowledged.
>
> **⚠ ESC-1 and ESC-2 are NO LONGER PENDING — both were RULED in commit `d0f84d0` while this
> wave ran** (found by reading `git log`, not relayed). ESC-1 → Reading B via a SUCCESS LATCH
> (`ok` starts False, latches True only on return, NO `except` arm; cancelled rows carry
> `ok=False`; third state refused). ESC-2 → CONFIRM channel A. **The deferred pin group is
> un-deferred and pinned**, plus one new pin for the ruled schema-comment wording. §5's ESC-1
> and ESC-2 entries below are the ESCALATION AS FILED and are preserved as the reasoning
> record; **the RULING and what it changed are in the wave-2 addendum §10a.**

- **State:** done-with-deviations. Contract authored TESTS ONLY; no reference implementation
  was built, sketched, or run (process law). Satisfiability is the adversary's to certify.
- **Deviations:** (D1) `_surreal_harness.py` docstring counts bumped — BOTH derived counts moved
  (35→36 importers, 21→22 `connect_admin` callers), re-derived with the pin's own AST derivation ·
  (D2) two prose corpses in `test_surreal_schema.py` (a "six core columns" comment + class
  docstring) fixed as a mechanical FK-3 consequence · (D3) `_field_statement` is IMPORTED from
  `test_surreal_schema` rather than cloned · (D4) `test_surreal_store.py` needed NO amendment —
  verified, not assumed · (D5) three T7-unlisted pins added: production PROSE corpses (AC-19's
  sweep) turned into mechanical pins.
- **Decisions needed (8):** ESC-1 `ok` on a CANCELLED dispatch (pin group DEFERRED — the ruled
  mechanism contradicts T2's own column semantics) · ESC-2 the emission's store-access channel is
  unnamed by the spec; my contract forces the request-lifespan channel · ESC-3 the brief's
  served≡limit/`hit_count` requirement contradicts T2 (no writer exists) · ESC-4 the brief's
  "seq typed int not option" pin is STRUCK-design vocabulary; under T2 `ordinal` IS `option<int>` ·
  ESC-5 the ORACLE (`_surreal_fakes.py`) is outside my writable set though T7.8 owns it here ·
  ESC-6 T7.12/AC-15's `message_ledger` wiring pin is SURFACE-wave work, unowned · ESC-7 T7.9 deploy
  smoke is a packet-exit obligation, not a pin · ESC-8 the shared tree's mypy count moved 39→94
  under the parallel surface wave (not mine).
- **Receipts:** §1 counts · §2 pin inventory → T-rulings · §3 the 19 mutation-proof obligations ·
  §4 probe receipts (4 probes, each with a control) · §5 escalations · §6 deviations · §7 residuals.

---

## §1 Gate counts (measured 2026-07-24, working tree at HEAD `e7db965` + this wave's edits)

| file | BEFORE | AFTER | note |
|---|---|---|---|
| `loremaster/tests/test_trace_telemetry.py` | did not exist | **63 failed / 12 passed** (75 collected, **0 collection errors**) | the T-series contract |
| `test_surreal_schema.py` + `test_surreal_fakes.py` + `test_surreal_store.py` + `test_surreal_harness.py` | **386 passed / 0 failed** | **2 failed / 384 passed** | exactly the two FK-3 amendments; nothing else moved |
| `test_retry_seam.py` + `test_retired_symbols.py` + `test_render_seam_pins.py` + `test_text_hygiene.py` + `test_mcp_server.py` + `test_symbols.py` | — | **1296 passed / 0 failed** | the structural/AST-pin suites, WITH the new file present: no collateral |
| `uv run mypy loremaster` | 39 errors / 3 files | 94 errors / 2 files | **ZERO in any file I touched**; see ESC-8 |
| `uv run ruff check loremaster/tests` | clean | **clean** | |

**Every one of the 63 REDs was verified RED FOR THE RIGHT REASON** (full reason histogram taken from
the run): 9 × `TypeError: SurrealStore.record_trace() got an unexpected keyword argument 'agent'`
(the T8 signature) · 35 × `len([]) == 0` / `0 == 1` on the recorder (no seam exists) · 5 ×
`no DEFINE FIELD statement found for trace.{agent,action,transport_session,ordinal,ok}` · 2 ×
`assert 'TYPE option<int>' in 'DEFINE FIELD OVERWRITE hit_count ON trace TYPE int'` (and `session`) ·
`expected exactly one DEFINE SEQUENCE for trace_seq, got []` · `no DEFINE INDEX statement named
exactly 'trace_agent_ordinal'` · `TracingFastMCP does not exist` ×2 · 3 × prose corpses
(`'six core'`, `'fire-and-forget'`) · the migration legs (`the enrichment columns [...] are NOT
declared on a store that already carried the OLD trace table`). **No RED is an import error, a
collection error, a fixture failure, or a mypy error.**

**The 12 green-today pins, each accounted for** (a pin that passes today must be justified or it is
decoration): 5 × `test_the_committed_columns_keep_their_definitions` (the delta must stay ADDITIVE) ·
2 × the index-FIELDS parser's own controls (positive: `chunk_tier_file` → `('tier','file_path')`;
negative: a forged statement NAMED `trace_agent_ordinal` with `FIELDS tool` parses as `('tool',)`) ·
`test_the_minimal_args_registry_is_exactly_the_registered_surface` (**the checked coverage
variable** — green now, RED the day a tool is added without a fixture) ·
`test_the_synthetic_probe_is_registered_after_construction` ·
`test_the_real_app_context_accepts_the_store_the_emission_writes_through` (AC-15 analogue) · **2
GUARD pins that are VACUOUS until the seam exists** — `test_a_failing_store_on_a_failing_tool_still_
surfaces_the_tools_error` and `test_a_dispatch_with_no_reachable_app_context_still_serves_the_tool`
(disclosed; obligation M19 below is their mutation proof).

---

## §2 Pin-group inventory, mapped to the ruling each group exists to enforce

Spec: `docs/plans/v2/03b-design-rulings-r2.md` §B. All pins in
`loremaster/tests/test_trace_telemetry.py` unless named otherwise. Cited by CLASS name (symbols
survive edits; line numbers do not).

| # | class | ruling | what it kills |
|---|---|---|---|
| G1 | `TestTheSeamIsInstalledAtTheOneFunnel` | T1 · T7.2 | telemetry that exists and is never wired (`build_mcp_server` still constructing a plain `FastMCP`); a subclass that INHERITS `call_tool` |
| G2 | `TestTheEmissionsDependencyIsRealInProduction` | T7.12/AC-15 (telemetry half) | the double declaring `write_store` into existence while production cannot construct it |
| G3 | `TestCoverageIsACheckedVariable` (4 pins + 16 parametrisations) | T7.1 | per-wrapper emission; a tool added with no fixture going silently unmeasured; a second/duplicate emission; a dispatch that traces only when a test calls the METHOD (the wire-handler leg is the path production uses) |
| G4 | `TestTheToolsOutcomeAlwaysWins` (5 pins) | T5.1 · T5.4 · T2 (`ok`, `hit_count`) · T3 | an emission that alters a result, inverts `ok`, fabricates `hit_count=0`, reports a constant latency, or mints the ordinal client-side |
| G5 | `TestATraceWriteFailureNeverTouchesTheCall` (4 pins) | T5.1 (the DESIGN-LAW §14 carve-out, FK-7 CONFIRMED) · T7.4 | a store failure that takes the tool down; a silent swallow; the store's error DISPLACING the tool's; an unstructured log |
| G6 | `TestACancelledDispatchStillRecordsItsRow` | AC-06 / T5.3 | "simplifying" `finally` into except+return arms, silently un-tracing the timed-out population |
| G7 | `TestIdentityIsDeclaredNeverGuessed` (8 pins) | T4.1–T4.3 · AC-17 | **session-sticky attribution**; an all-or-nothing harvest; `str()` coercion of a non-str value; harvesting the refused ledger-actor keys (`owner`/`actor`/`created_by`); overloading `session` with the correlator; a hardcoded/interned correlator |
| G8 | `TestParamsHashIsTheRuledRecipeAndLeaksNothing` (4 pins) | T6 | a non-T6 recipe; a constant digest; `sort_keys` dropped; **raw parameter content reaching the row** (hostile body fixture) |
| G9 | `TestTheIndexFieldsParserItself` | AC-12 rider | the substring trap: an index NAMED for its columns satisfying a whole-statement match |
| G10 | `TestTheTraceSchemaDelta` (7 + 5 params + 3 pins) | T2 · T2.1 | `IF NOT EXISTS` on a changed field (#107); a required (non-`option<>`) enrichment column; `BATCH`/`START` on the sequence (#146); a UNIQUE/wrong-field/`OVERWRITE` index; an accidental `transport_session` index (a DELIBERATE non-shipment with a named decision point) |
| G11 | `TestTheTraceDeltaMigratesADirtyStore` (4 pins) | T2 migration · T8 | the whole class a VIRGIN fixture cannot see: OLD definition applied → row written → production `ensure_ready` → new-shape write lands, legacy row survives + still reads, the index and sequence land on an EXISTING table, `trace_aggregates` counts BOTH generations |
| G12 | `TestTheOrdinalIsMintedByTheStore` (4 pins) | T3 · T7.6 | an ordinal left NONE (the schema cannot forbid it — `option<int>`); a client-side or read-max-then-CREATE mint (**≥8-way, separate connections**); a count derived from `max−min` ordinal arithmetic (pinned with a REAL burned gap + its control) |
| G13 | `TestRecordTraceAtTheNewSignature` (3 pins) | T8 | new params not reaching the row; a fabricated 0/"" for an unknown value; `ok` stored as a string/int |
| G14 | `TestNoProductionProseStillTeachesTheRetiredPlan` (3 pins) | T5.2 · AC-19 | production prose teaching the REFUSED fire-and-forget plan and a stale "six core fields" count — the repo's own top defect class, given a mechanical guard instead of a memo |
| FK-3a | `test_surreal_schema.py::TestTraceTableFieldDefinitions::test_trace_core_scalar_fields_are_defined` | T2 / AC-16 | a revert of either widened spec |
| FK-3b | `test_surreal_fakes.py::TestRecordTraceFake::test_record_trace_signature_matches_real_store` | T8 / AC-16 | the four new params missing on real OR fake; **an `ordinal` parameter appearing** (the client-side mint) |

**Deliberately NOT pinned, and why:** the drain-verb `[real]` legs (AC-17 — the KEY rule lets
SYNTHETIC probe tools carry every identity leg, so this contract has **zero** dependency on the
comms verbs landing first: no cross-wave collateral RED); `trace_aggregates`/`TraceSummary` shape
(T8 rules them UNCHANGED — the committed pins own them, cited not duplicated); the five new columns
restated inside the committed schema pin (two copies of one column list is two copies to drift).

---

## §3 Named mutation-proof obligations for the contract-adversary

Each is "break X → exactly these pins go RED". M4 and M19 are the two that matter most: they prove
the batteries are load-bearing *in combination*.

| # | mutation | must go RED |
|---|---|---|
| M1 | revert `build_mcp_server`'s constructor to plain `FastMCP` | G1 both pins + **all 16 coverage parametrisations** + the wire-handler leg |
| M2 | subclass exists but does not override `call_tool` | `test_the_dispatch_entry_point_is_the_subclass_override` |
| M3 | move the trace write from `finally` into `except`+success arms | G6 ONLY (everything else stays green — that is the point) |
| M4 | emit ONLY in the `except` arm | `test_a_successful_dispatch_..._records_ok_true` RED while **coverage stays green** — proves neither battery is sufficient alone |
| M5 | supply `hit_count=0` | `test_the_seam_records_no_hit_count` |
| M6 | mint the ordinal in the seam (client-side) | `test_the_seam_never_mints_the_ordinal_itself` + `test_eight_concurrent_writes_...` + FK-3b |
| M7 | session-sticky attribution (remember the last declared agent per transport) | `test_a_silent_call_records_NONE_even_after_a_declaring_call_...` ONLY |
| M8 | harvest `owner`/`actor`/`created_by` into `agent` | `test_the_heterogeneous_ledger_actor_params_are_NOT_harvested` |
| M9 | `str()`-coerce a declared non-str value | `test_a_non_string_declared_value_is_recorded_as_NONE` |
| M10 | copy `transport_session` into `session` when no session is declared | `test_a_partial_declaration_records_only_what_was_declared` |
| M11 | `params_hash` without `sort_keys` / over a filtered dict / a constant | key-order pin / recipe pin / determinism control pin respectively |
| M12 | store the raw arguments alongside the hash | `test_no_raw_parameter_content_reaches_the_row` |
| M13 | revert `hit_count` or `session` in `_TRACE_FIELD_SPECS` | FK-3a, on that column alone |
| M14 | add an `ordinal=` parameter to `record_trace` | FK-3b |
| M15 | make the trace index UNIQUE, reorder its FIELDS, or use `OVERWRITE` | `test_the_06_read_index_ships_in_the_free_window` |
| M16 | add `BATCH`/`START` to the sequence | `test_the_trace_sequence_is_defined_once_with_no_batch_or_start_clause` |
| M17 | flip the trace fields' emitter to `DEFINE FIELD IF NOT EXISTS` | every G10 field parametrisation + **all four G11 migration legs** (the #107 pair) |
| M18 | report latency in seconds, or measure it after the emission | `test_the_recorded_latency_reflects_the_calls_real_duration` |
| M19 | **(the green-today guards)** make the emission re-raise from `finally` | `test_a_failing_store_on_a_failing_tool_still_surfaces_the_tools_error` + `test_a_dispatch_with_no_reachable_app_context_still_serves_the_tool` — both pass VACUOUSLY today and this is the only proof they discriminate |

Also owed by the adversary per standing law: a **satisfiability receipt** (0-failed against its own
reference build, including the harder leg — still satisfiable after the cleanups ruff/mypy will
demand), and P2 fixture perturbation. Three pins whose satisfiability I judge least certain, so
attack them first: **G6** (does the awaited write in `finally` complete against a REAL store rather
than the in-memory double?), the **wire-handler leg** (SDK-internal handler registry), and
**G11**'s `INFO FOR …` introspection legs.

---

## §4 Probe receipts — all fresh 2026-07-24, TEST store `ws://127.0.0.1:18000` only

`:18500` (production) was never contacted. Each probe carries a positive control.

1. **The two `7f23223` store-reference facts, RE-PROBED ON CONTACT** (per the packet ruling), 3.2.1:
   - `sequence::nextval` under the default `START 0` returned **0** then **1** → ordinals are
     **0-based**; no pin assumes 1 (AC-05).
   - `SELECT *` **OMITS** an unset `option<>` column (row keys `['a','ord']`), while
     `SELECT a, b, ord` returned `{'b': None}`. **CONTROL:** a sibling row WITH `b` set came back
     carrying `b` under `SELECT *`, so the probe demonstrably sees presence. → `_TRACE_PROJECTION`:
     every read leg projects explicitly, so an unset column reads `None` instead of raising
     `KeyError` as a harness failure masquerading as a finding.
   - `CREATE t CONTENT object::extend($c, {ord: sequence::nextval('s')})` works; **CONTROLS:**
     `CONTENT $c SET …` and `CONTENT $c MERGE {…}` both PARSE-ERROR (`Unexpected token 'SET'` /
     `'MERGE'`). Recorded for the builder; this contract pins the ordinal's OBSERVABLE properties,
     never statement text.
2. **Harness mechanics at `mcp==1.27.2`:** a test-set `request_ctx` reaches a dispatched tool's
   `lifespan_context`; `request.headers.get('mcp-session-id')` is reachable in-handler; a raising
   tool surfaces `mcp.server.fastmcp.exceptions.ToolError` carrying the original message; cancelling
   the dispatching task raises `CancelledError` out of `call_tool`. **CONTROL:** with NO request
   context the tool errors ("Context is not available outside of a request") — which is why G5's
   no-app-context pin exists.
3. **The wire path:** `mcp._mcp_server.request_handlers[CallToolRequest]` invoked with a
   `CallToolRequest` returns a `ServerResult` with `isError=False` — a test CAN drive the handler
   FastMCP registers at `__init__`, so the coverage battery has a real wire leg.
4. **`INFO FOR …` introspection** (G11's instrument): `INFO FOR TABLE t` → `fields`/`indexes` dicts;
   `INFO FOR DB` → `sequences`. **The engine RENDERS `option<int>` back as `none | int`**, so the
   live legs assert NAMES only and the type expressions are pinned against the generator's output.
   **CONTROL, verified end-to-end:** a control sequence defined on the raw connection was still
   visible after the production `ensure_ready` (`['telemetry_control_seq']`), and `trace_seq` was
   genuinely absent — so "trace_seq is missing" is a real absence, not a blind read. (First draft
   used `message_seq` as that control; the message DDL rides its OWN generator, not `generate_ddl`,
   so `ensure_ready` never defines it and the control would have failed for its own reason. Caught
   and fixed before landing.)
5. **The derived-count re-derivation (AC-18):** run with the pin's OWN AST derivation and its OWN
   file set (`rglob('*.py')` minus the harness): **importers 35→36**, **`connect_admin` callers
   21→22**. AC-18 warned the second count hides behind the first assert — it does, and it moved:
   the new file both imports the harness and calls `connect_admin`. Strict-subset invariant
   re-checked (`callers ⊂ importers` → True). `test_surreal_harness.py` is green after the bump.

---

## §5 Escalations — forks I did NOT settle (spec ambiguity is a STOP)

**ESC-1 — `ok` on a CANCELLED dispatch. PIN GROUP DEFERRED.** T5's ruled shape sets `ok = False`
inside `except Exception`, which `CancelledError` (a `BaseException`) never enters — so the ruled
mechanism records a cancelled call as `ok = True`, contradicting T2's own definition of the column
("whether the tool call succeeded"). **Reading A:** literal T5 — a cancelled row carries `ok=True`
(cheapest, but the column then means "did not raise a non-cancellation exception" and packet 06's
`ok = true` filter silently includes timed-out calls). **Reading B:** a cancelled dispatch is not a
success — the emission records `ok=False` (or a third state) on `BaseException`. **My
recommendation: B**, because the entire purpose of `ok` is to keep errored calls out of the
numerator, and a timed-out drain is not a drain the agent performed. I pinned the row's EXISTENCE
(AC-06) and deliberately left `ok` unasserted on that leg, with the fork stated in the test's own
docstring so the builder cannot mistake silence for licence.

**ESC-2 — the spec never names the emission's STORE-ACCESS CHANNEL.** T5 gives the shape
(`try/except/finally` around `super().call_tool`) but not where `record_trace` comes from. **Reading
A (mine):** the request's lifespan context — the same channel every tool wrapper uses
(`context.request_context.lifespan_context`). Derived, not preferred: `build_mcp_server` constructs
the `FastMCP` instance BEFORE any `AppContext` exists (`_ProcessLifespanGuard` builds it lazily on
the first session), so a store cannot be injected at construction. **Reading B:** reach through the
guard/eager-lease attribute for the process-shared context. My contract's harness delivers the store
through channel A, so it FORCES A. If the operator/lead prefers B, the harness changes (one
fixture), not the pins' semantics — flagged rather than left implicit.

**ESC-3 — the brief's `hit_count`/served≡limit hard requirement contradicts the settled design.**
The brief requires "a drain fixture where limit exceeds pending MUST exist — `hit_count` records the
SERVED count". T2 **REFUSES** any generic hit-count writer ("supplying 0 would make the served
aggregate lie"), and the packet's Scope OUT forbids pre-empting 06 — so under r2 there is no
served-count writer for a `limit > pending` fixture to discriminate, and staging one would need the
drain verb (the exact cross-wave dependency AC-17 kills). **My translation:** the honesty pin (the
seam records NO hit count; `hit_count` is `option<int>`; an explicitly-unknown count stores NONE)
plus AC-12's own note-for-future as a **named re-open trigger**: *the wave that first adds a
served-count writer to `trace` owes the `limit > pending` twin fixture at that moment.* Recorded
here so it is met deliberately rather than rediscovered.

**ESC-4 — the brief's "seq-typed-int-not-option pin" is STRUCK-design vocabulary.** That pin
belonged to the struck architecture, whose ordinal column was named `seq` and typed REQUIRED `int`
(its measured incentive: `seq option<int>` greened 5 tests). Under the settled r2 design there is no
`trace.seq`; T2 rules `ordinal` **`option<int>`** deliberately (the §1.4 humble shape — and AC-16
adjudicated the all-`option<>` choice as CHEAPER precisely because no required column's removal can
green a committed pin). A pin asserting `TYPE int` for the ordinal would now CONTRADICT the design
authority. **My translation of the same door — three pins, not one:** the schema pin asserts
`TYPE option<int>` (so a required-int build is also RED); `test_every_written_row_carries_an_int_
ordinal_never_NONE` closes the cheapest green path the loosened type opens (the CONTRACT is the only
thing that can force presence once the schema cannot); and `test_the_seam_never_mints_the_ordinal_
itself` + FK-3b's absent-`ordinal`-parameter clause close the client-side mint. Flagging rather than
silently reinterpreting a hard requirement.

**ESC-5 — the ORACLE is outside my writable set although T7.8 assigns it to me.** T7.8 makes
`FakeSurrealStore.record_trace` parity "an ORACLE change, contract-author-owned"; my writable set
lists `test_surreal_fakes.py` (the PIN) but not `_surreal_fakes.py` (the FAKE). I amended the pin
only, so it is RED until both sides move. **The exact edit I would make** to
`loremaster/tests/_surreal_fakes.py::FakeSurrealStore.record_trace`: append four keyword-only
parameters `agent: str | None = None, action: str | None = None, transport_session: str | None =
None, ok: bool | None = None` after `model`, default `hit_count`/`session` to `None`, store all of
them on the recorded row, and **mint a fake ordinal from a per-instance counter** so
`recorded_traces()` mirrors the real row shape (T7.8's "row shape", not just the signature). Needs
either a scope grant to me or a builder-brief line; per 03a-2 row 4 its satisfiability receipt must
cover BOTH consumer suites.

**ESC-6 — T7.12 / AC-15's `message_ledger` wiring pin is unowned.** It sits in T7's list (the
telemetry contract's), but it tests the COMMS surface's production wiring (`AppContext.__init__`
accepts `message_ledger`; `build_app_context` constructs one; positive control over `brief_ledger`)
and belongs in a file outside my writable set. I did NOT write it — duplicating the surface sibling's
pin would create two divergeable copies of one invariant. **Lead must assign it**, or it falls
between the two waves. I wrote the telemetry ANALOGUE
(`TestTheEmissionsDependencyIsRealInProduction`: the real `AppContext` accepts `write_store`, with
positive and negative controls) so my own wave's harness-double hole is closed.

**ESC-7 — T7.9's deploy smoke is a packet-EXIT obligation, not a pytest pin.** A before/after trace
count on the LIVE production store around the smoke's own tool calls, plus one drain row carrying
`agent`+`action`+`ordinal`. It closes #147 with a production receipt and makes `lore_index`'s served
traces claim TRUE. Not simulated here: only the running artifact proves the cake.

**ESC-8 — the shared tree moved under me (observation, not mine to fix).** Baseline mypy at my start
was 39 errors / 3 files; at my finish 94 / 2 files — `test_comms_tool.py` 31→88 and
`test_comms_promise_registry.py` 3→6 (the parallel SURFACE wave, mid-flight), while
`test_message_ledger.py`'s 2 FK-4 errors disappeared (the casts appear to have landed). **Zero of
those errors are in any file I touched**, and the packet's global mypy-zero exit criterion is
unaffected by my wave. Flagged so the lead's arithmetic isn't surprised.

---

## §6 Deviations (each disclosed, none silent)

**D1 — `_surreal_harness.py` docstring counts (authorized by my brief; AC-18).** 35→36 and 21→22,
re-derived (§4.5), not hardcoded from the pin's failure text. This is the second count moving too —
exactly what AC-18 predicted.

**D2 — two prose corpses in `test_surreal_schema.py`.** The fixture comment block and
`TestTraceTableFieldDefinitions`'s docstring both claimed "six core columns"; the FK-3 amendment
makes that false. Fixed under the STANDING AUTHORIZATION (a mechanical consequence of a design
ruling that changes no assertion and preserves every rendered value), and rewritten so the count is
no longer restated in prose at all — the generator's `_TRACE_FIELD_SPECS` is the list. Leaving a
known corpse in a file I was amending would violate the rename-sweep law.

**D3 — cross-module import of a private test helper.** `from test_surreal_schema import
_field_statement`, rather than cloning it. It carries the `DEFINE FIELD OVERWRITE` guard-kind
assertion and its #107-shaped failure message; a second copy is a second thing to drift (DRY law).
Repo precedent: `test_comms_tool.py` imports from `test_render_seam_pins`, `test_text_hygiene.py`
imports `test_mcp_server`. Where a helper's reuse WOULD have meant importing a private DDL-apply
policy, I avoided the duplication instead: G11 applies its OLD-world DDL one statement per `query()`
call (the SDK inspects only the FIRST statement's status of a multi-statement query) and lets the
REAL production `ensure_ready` be the NEW world — a stronger pin than a hand-applied delta.

**D4 — `test_surreal_store.py`: no amendment was required.** VERIFIED rather than assumed: its trace
pins are per-key, every new column is `option<>`, and the suite runs 384 passed with only the two
intended FK-3 REDs. So FK-3 is TWO amendments, not three, and no `TestTraceRoundTrip` pin needed
touching (unlike the struck architecture's required-`seq` design, which needed four).

**D5 — three pins beyond T7's list** (`TestNoProductionProseStillTeachesTheRetiredPlan`). AC-19
assigns the production prose-corpse sweep to the BUILDER BRIEF as a remembered obligation. Given
this repo's own audited finding — that the same defect class shipped ten more instances *after* the
law was written, because served English had no mechanical guard — I converted three of those sites
into pins (`record_trace`'s fire-and-forget + "six core" claims, `_trace_statements`' "six core"
claim). A law people must remember is not a guard.

---

## §7 Residuals noticed (surfaced per standing law; none silently dropped)

1. **`trace.token_cost` / `trace.model` remain writer-less** after 03b (design §F.1). My pins assert
   both columns keep their committed `option<>` definitions; nothing writes them. Deliberate.
2. **Rows with `agent` set but `session` AND `transport_session` both NONE pool same-named agents
   across sessions** in a per-agent curve read (design §F.6) — visible in the data, bounded, owned by
   packet 06's analysis notes. My identity legs make that state REACHABLE and honest (the
   partial-declaration pin), which is the design's intent.
3. **`hit_count`/`session` widening leaves existing rows UPDATE-poisoned** on a dirty store (store
   reference §1.4). Harmless here because traces are append-only and never UPDATEd — pinned
   indirectly: G11 proves the legacy row still READS. If any wave ever adds a trace UPDATE path, that
   is the re-open trigger.
4. **`_MINIMAL_ARGS` is a ~16-line maintenance surface** (design D13, accepted). Its failure message
   teaches exactly what to add. If a future reader is tempted to delete it, the alternative is #131.
5. **The coverage battery's built-in dispatches nearly all FAIL** against the minimal app-context
   double (by design — the funnel traces outcome-blind). That is disclosed in the file's own
   "fixture discrimination" docstring section and is why M4 exists. A future author who "fixes" the
   double to make the built-ins succeed must keep a SUCCEEDING and a FAILING leg, or the pair stops
   discriminating.
6. **The `lore_index` served description's traces claim** (scout §6.2) becomes true only once the
   emission ships; T7.9's deploy smoke is what makes it honest. Not pinned here — it is a served-text
   claim about a live store, and asserting it pre-build would pin a lie.
