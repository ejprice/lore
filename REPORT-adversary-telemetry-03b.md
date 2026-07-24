# REPORT-adversary-telemetry-03b — contract adversary, packet 03b all-tools telemetry

brief-base v6 read

> All measurements in this report were taken **2026-07-23/24 against lore HEAD `45cc161`**
> (branch `feat/surreal-unification`), engine spike-surreal **3.2.1** on `ws://127.0.0.1:18000`,
> `mcp` **1.27.2**, Python 3.14. Every "passes" / "survives" claim below is a run against the
> FROZEN contract `loremaster/tests/test_trace_telemetry.py` at that SHA — not a claim about
> any later state of that file.

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — ELEVEN wrong builds survive the contract at 41 passed / 0 failed.** The most
  dangerous: **`caller = str(id(session))`** — 400 non-overlapping MCP sessions collapse to
  **17 distinct caller keys (383 collisions)**, silently pooling agents into one denominator,
  while every S7 same-key/different-key pin stays green.
- **Second headline, a defect PATH the contract creates:** the correct build (`seq int`, per
  ruling S8-E3) turns **7 committed pins RED** in four other suites; flipping `seq` to
  `option<int>` — which the contract does **not** pin — turns 5 of them green AND keeps the
  contract at 41/41. The cheapest path to a green tree destroys E3's whole rationale.
- **MISSING PINS (blocker):** MP1 `seq int` + omit-the-mint-is-REJECTED · MP2 emission survives
  cancellation (`finally`, not `except Exception`) · MP3 caller key unique ACROSS session
  lifetimes + the map does not retain finished sessions · MP4 a NON-drain comms action records
  `agent`/`session`.
- **MISSING PINS (high):** MP5 a drain whose limit EXCEEDS pending records `hit_count == served`
  · MP6 a failed trace write is LOGGED loudly.
- **MISSING PINS (medium):** MP7 `token_cost`/`model` declared + the `(caller, seq)` index names
  both fields · MP8 non-empty `params_hash` on a zero-arg call · MP9 `trace.session` semantics
  (ESCALATION — spec admits two readings) · MP10 adjudicate the 7 collateral-RED pins · MP11 the
  S7 rung pin compares `id()` ints, not object identity.
- **Fixture discrimination:** the drain fixture (`seeded 5 / limit 2`) is **arithmetic-aligned** —
  served ≡ limit, so `hit_count = limit` is indistinguishable from `hit_count = served`.
  Perturbation proven BOTH legs (limit 20 > pending 5: RED on the wrong build, GREEN on the
  reference).
- **RED reproduced:** 36 failed / 5 passed, for the right reason (missing production symbols, no
  collection error). **Reference build: 41 passed / 0 failed** — the satisfiability receipt holds
  *in isolation* only; see MP10.
- **S7 fact independently RE-DERIVED** with a stronger instrument (`is`-comparison, objects held
  alive): `mcp` 1.27.2 mints ONE `ServerSession` per MCP session. **Rung 1 selection is CORRECT.**
- **Provenance receipt:** `loremaster.__file__ = /home/ejprice/scratch/adv-telemetry-03b/loremaster/loremaster/__init__.py`
  (via `./scripts/scratch_copy.sh`). **The repo was never edited** — `git status --porcelain` empty
  at close.

---

## 0. Instrument setup, and why it can be trusted

```
$ ./scripts/scratch_copy.sh /home/ejprice/scratch/adv-telemetry-03b
scratch copy READY: /home/ejprice/scratch/adv-telemetry-03b
  imports resolve INSIDE the copy:
  loremaster  -> /home/ejprice/scratch/adv-telemetry-03b/loremaster/loremaster/__init__.py
$ .venv/bin/python -c "import importlib.metadata as md; print('mcp', md.version('mcp'))"
mcp 1.27.2
```

Every probe in this report printed `loremaster.__file__` as its first line; every one resolved
inside the scratch tree. All wrong builds were applied to that copy and reverted from a
byte-identical reference snapshot (`md5sum` re-verified at close: `f359898e…` / `13199ffe…` /
`f015c106…`, contract back to 41 passed).

### P7 — the claimed RED, reproduced

```
$ uv run pytest -n auto -q loremaster/tests/test_trace_telemetry.py
36 failed, 5 passed, 2 warnings in 6.59s
```

Matches the brief's claim exactly. The 5 green are `TestTheS7RungSelectionFact` (a standing
measurement, correctly green today) plus the four `TestTheDeploySmokeAssertionDiscriminates`
controls (pure functions over synthetic payloads). Failures are RUN-time `AttributeError` naming
the missing seam, never a collection error — the `_server_attr` call-time-accessor discipline
(finding #133) works. **VERDICT: RED is honest.**

### P0 — the reference build (the control without which no wrong-build result means anything)

I built the full row-F/row-G production change in scratch: the schema delta (5 new columns,
`session`/`hit_count` loosened, `DEFINE SEQUENCE IF NOT EXISTS trace_seq`, the `(caller, seq)`
index), `record_trace`'s new signature with a store-side
`object::extend($content, {seq: sequence::nextval("trace_seq")})` mint, and
`TracingFastMCP(FastMCP)` + the ContextVar annotation channel + the `WeakKeyDictionary` caller
ladder + the one-line instantiation swap.

```
$ uv run pytest -q loremaster/tests/test_trace_telemetry.py
41 passed, 5 warnings in 10.23s
```

⚠ **With rows F/G ONLY it is 39/41.** The two `TestARealDrainWritesAnEnrichedRow` pins need the
comms `drain` action and its `peek` parameter, which do not exist at `45cc161` and belong to
delta rows **C/D** — a different contract's production work. I added a minimal `_comms_drain` to
reach 41/41. **This is a sequencing fact the lead needs: the telemetry contract cannot go
0-failed on a builder brief scoped to rows F/G/H.** (Flagged, not adjudicated — scope is the
operator's.)

---

## 1. P1 — the wrong builds. ELEVEN survive.

Each row was applied to the reference tree, run against the **frozen** contract, and — where it
survived — followed by a consequence probe **paired with a positive control on the reference
build**. Commands: `/home/ejprice/scratch/adv-probes/{wrong.py,run.sh,consequences.py}` (scratch;
the recipes are reproduced inline below so the finding does not depend on an unrecoverable path).

### 1.1 Survivors (contract: 41 passed, 0 failed)

| id | the wrong build | measured consequence | control (reference build) |
|---|---|---|---|
| **WB9** | `caller` key = `str(id(session))` instead of a minted uuid | 400 sequential non-overlapping sessions → **17 distinct keys, 383 collisions** | 400 distinct, 0 collisions |
| **WB30** | emission in `except Exception` + success path, not `finally` | a CANCELLED dispatch writes **0** rows | writes **1** row |
| **WB32** | caller map is a plain `dict`, not `WeakKeyDictionary` | 500 finished sessions retain **500** entries | retains **0** |
| **WB3** | `seq option<int>` instead of `int` | a writer that OMITS the mint is **ACCEPTED** | **REJECTED** (`InternalError: Expected int but found NONE`) |
| **WB1** | comms annotates `agent`/`session` only inside the drain branch | `register` and `heartbeat` rows carry `agent=None session=None` | heartbeat row carries `agent='c7c6b231…' session='wave7'` |
| **WB2** | `hit_count = limit` instead of `len(result.entries)` | seeded 1, default limit 20 → **`hit_count=20`**, truth 1 | `hit_count=1` |
| **WB4** | `except Exception: pass` on a failed trace write | **0** log records ≥WARNING naming the failure | **1** (`ERROR: trace write FAILED for tool=lore_index …`) |
| **WB5** | `token_cost`/`model` deleted from `_TRACE_FIELD_SPECS` | `token_cost declared: False  model declared: False` | both `True` |
| **WB6** | `trace_caller_seq` index on `(tool)` | `DEFINE INDEX … trace_caller_seq ON trace FIELDS tool` | `… FIELDS caller, seq` |
| **WB19** | `session` annotation from the caller-supplied argument | heartbeat with no `session=` records `session=None` | records `'wave7'` |
| **WB22** | `params_hash = ""` when `arguments` is empty | every zero-argument call shares one empty digest | a 16-hex digest |

### 1.2 Builds the contract CAUGHT — its real strengths, stated plainly

| id | the wrong build | result |
|---|---|---|
| WB7 | fire-and-forget (`asyncio.ensure_future`), explicitly REFUSED by §S6v2 item 6 | **25 failed / 16 passed** |
| WB33 | the comms handler is a SECOND writer (calls `record_trace` itself) | **2 failed** (`len(rows) == 1` fires) |
| WB21 | `caller` written only when a dispatch produced comms annotations | **2 failed** |
| WB20 | `latency_ms` = a constant 42.0 | **1 failed** — the fast/slow fixture PAIR works |
| — | `build_mcp_server` never swapped to `TracingFastMCP` | caught by construction: `traced_server` uses the real factory |

Four of the coverage pins are genuinely strong: `test_the_traced_order_is_the_dispatch_order`
kills batching/replay builds; `test_the_coverage_derivation_is_live_not_a_snapshot` proves the
registered set is read live; the success/error pin pair covers both fates for `Exception`; and
`test_the_same_session_yields_the_same_caller_key` uses **two different tools**, so a
per-(session, tool) key is caught too. I could not break any of them.

### 1.3 The single most dangerous survivor, in detail — WB9

§S7's own self-attack table says of "key collides across sessions": *"uuid-minted per object /
server-minted header — **no collision path**"*. That row is unenforced. `str(id(session))` is
alnum (passes the charset pin), stable within a session (passes), distinct while two sessions
**coexist** (passes both the seam leg and the real-transport leg) — and catastrophically
non-unique across a session's death, which is the only regime a long-lived server ever runs in.

```
[WB9] 400 sequential, NON-OVERLAPPING sessions -> 17 distinct caller keys (383 COLLISIONS)
[REF] 400 sequential, NON-OVERLAPPING sessions -> 400 distinct caller keys (0 COLLISIONS)
```

The contract's quantifier is *"distinct across sessions that overlap in time"*. The property S7
needs is *"distinct across sessions, ∀ time"*. That gap is the whole finding.

---

## 2. P1b — THE QUANTIFIER TABLE

Every invariant the contract asserts, classified ∀-over-inputs vs guarded-by-a-known-failure-mode.
Every guarded row carries a receipt: a surviving door-build, or the door-build that died.

| # | invariant | ∀ / guarded | receipt |
|---|---|---|---|
| 1 | every REGISTERED tool writes ≥1 row | **∀ over registered tools** — derived from `FastMCP.list_tools`, never listed; and ∀ over dispatch DOORS: grep proves production has **exactly one** `FastMCP(` construction and **zero** other `call_tool`/`_tool_manager` dispatch sites | door-build attempted and DIED: WB21 (2 failed), WB7 (25 failed) |
| 2 | exactly ONE row per dispatch, in dispatch order | **∀** (list equality, not set) | batching/replay build killed by `observed == dispatched` |
| 3 | ONE writer — handlers never `record_trace` | **∀ for lore_comms** via `len(rows) == 1` | WB33 died (2 failed) |
| 4 | a row is written on BOTH fates | **GUARDED — by exception TYPE (`Exception`)** | **WB30 SURVIVES**: same bad outcome (a dropped row) through the `BaseException`/cancel door. 0 rows vs 1 on the control. |
| 5 | every row carries a caller key | **∀ over swept rows** | WB21 died |
| 6 | the caller key is stable within a session | **∀ over the 2 seam legs + 2 transport legs** | fresh-key-per-call build cannot pass; WB21 died |
| 7 | the caller key is distinct across sessions | **GUARDED — by the sessions COEXISTING in the pin** | **WB9 SURVIVES**: 383/400 collisions once sessions are sequential |
| 8 | the caller key map does not grow without bound | **NOT ASSERTED AT ALL** (spec names `WeakKeyDictionary`; no pin) | **WB32 SURVIVES**: 500 retained entries vs 0 |
| 9 | annotations are request-scoped, reset in a `finally` | **GUARDED — by exception TYPE** (success leg + `Exception` leg) | shares WB30's door: on cancellation neither reset path runs |
| 10 | domain enrichment reaches the trace row | **GUARDED — by `action == "drain"`**; zero pins on any other comms action | **WB1 SURVIVES**: `register`/`heartbeat` rows carry `agent=None`, so §S7 item 2's "the FIRST lore call binds its key" is false |
| 11 | `hit_count` is the SERVED count | **GUARDED — by the fixture's `limit ≤ pending` arithmetic**; served ≡ limit | **WB2 SURVIVES**; perturbation pair proves it (§3) |
| 12 | `pending` is `total_pending` | **∀** — 5 vs 2 vs 1 are pairwise distinct | a served-count or directive-count build is caught |
| 13 | `peeked` discriminates | **∀** — both values fixtured | constant-False build caught |
| 14 | a telemetry failure never fails/modifies the call | **∀** for the drive path; **the "never fail SILENTLY" half is UNASSERTED** | **WB4 SURVIVES**: 0 log records vs 1 |
| 15 | field DDL is `OVERWRITE`, table/index/sequence `IF NOT EXISTS` | **∀ over the emitted statements**, but by an `if/elif` **blacklist** of three known prefixes — anything else is unchecked | see R6 |
| 16 | the schema delta itself (types, columns, index fields) | **GUARDED — by substring presence only** | **WB3 / WB5 / WB6 all SURVIVE** |
| 17 | the loosening lands on an ALREADY-EXISTING table (#107) | **∀** — old DDL → dirty row → new DDL → both halves asserted | a genuine, strong pin; `IF NOT EXISTS` for fields is caught |
| 18 | `seq` is store-minted, global, distinct at 8-way | **∀ over the live store** | strong; but see R1 — the *sweep-level* seq pin is decoration |
| 19 | `params_hash` is stable and discriminating | **GUARDED — by `arguments` being non-empty**, and by ONE tool with ONE key | **WB22 SURVIVES** |
| 20 | argument VALUES never enter the row | **GUARDED — one tool, one key, one secret** | no door-build built; low risk (§4 R12) — verdict recorded, not a demanded pin |
| 21 | the ARTIFACT records (deploy smoke) | **NOT AN INVARIANT — a function nobody runs** | §5 |

---

## 3. P2 — fixture discrimination, with perturbation receipts

### 3.1 The drain fixture is arithmetic-aligned — PROVEN, both legs

`_DRAIN_SEEDED = 5`, `_DRAIN_LIMIT = 2` ⇒ served = min(5, 2) = **2 = the limit**. Because drain
semantics force `served = min(pending, limit)`, served is ALWAYS either `pending` or `limit`, so
**one drain fixture can never separate all three**. The contract has only the `limit < pending`
case, so `hit_count = limit` is invisible.

Perturbation, in a scratch COPY of the contract (`_DRAIN_LIMIT = 20`, assert
`hit_count == _DRAIN_SEEDED`):

```
LEG 1  perturbed fixture + CORRECT build   -> 3 passed, 38 deselected     (control: my expectation is right)
LEG 2  perturbed fixture + WB2             -> 1 failed:  assert 20 == 5
       ORIGINAL fixture  + WB2             -> 41 passed                    (the blindness)
```

Real-world consequence, measured through the production dispatch path with the default
`comms.drain_limit = 20` and ONE seeded message:

```
[WB2] SEEDED=1 LIMIT=20(default) -> hit_count=20 pending=1   (truth: served=1)
[REF] SEEDED=1 LIMIT=20(default) -> hit_count=1  pending=1
```

`hit_count` is *the* number packet 06's decay curve reads. A build that writes the limit reports
20 served on every ordinary drain.

### 3.2 Assertion-vs-message gap in that same pin (a FALSE GATE)

```python
assert row[TRACE_HIT_COUNT] == _DRAIN_LIMIT, (
    f"hit_count must be the SERVED count ({_DRAIN_LIMIT}), got …"
```

The message *names the property* (SERVED count); the assertion *checks the limit*. Under the
perturbation the message renders as `"hit_count must be the SERVED count (20), got 20"` while
asserting `20 == 5` — the conflation is written into the instrument. This is the P2 false-gate
class (CLAUDE.md, 2026-07-14) live in the frozen contract.

### 3.3 Parameter-value monocultures found

| axis | monoculture | verdict |
|---|---|---|
| comms `action` | every enrichment pin uses `drain` | **FINDING** → WB1 (MP4) |
| comms `session=` | every comms call passes `session="wave7"`, equal to the agent's registered session | **FINDING + ESCALATION** → WB19 (MP9) |
| `arguments` | only `PROBE_ECHO` is called with a non-empty dict; the whole sweep uses `{}` | **FINDING** → WB22 (MP8) |
| `peek` | both `True` and `False` fixtured | **CLEAN** |
| `limit` vs `pending` | see 3.1 | **FINDING** |
| annotation values | `hit_count=2 / pending=5 / peeked=True` pairwise distinct | **CLEAN — well done** |
| latency | two true durations, 384× / 1.50× margins (measured, §4 R11) | **CLEAN** |

### 3.4 P5 — can the doubles FAIL?

`_RecordingStore` can fail: WB20/WB21/WB33 all went RED through it, and its `**fields` shape
catches a renamed column. **But its `seq` mint is its own**, and production never supplies `seq`
(by design — `test_record_trace_takes_no_seq_parameter` forbids it). Proven by mutating the
double in a scratch contract copy (`self.next_seq = 999`):

```
E  AssertionError: seq must be DISTINCT per row — 23 duplicates
E  assert 1 == 24  where 1 = len({999})
```

The pin reads the FAKE's counter, not the build's. **Verdict: the three ordering assertions in
`test_seqs_are_distinct_and_increasing_across_a_sweep` are decoration** — only its non-vacuity
guard carries information, and that duplicates the order pin. Harmless (real `seq` behaviour is
pinned against the live store in `TestSeqIsMintedByTheStore`), but it should not be counted as
coverage.

---

## 4. P4 — the author's claims, verified

| claim | verdict |
|---|---|
| "41 pins, 36 failed / 5 passed" | **TRUE**, reproduced verbatim |
| "RED for the right reason, never at COLLECTION time" | **TRUE** — run-time `AttributeError` naming row G |
| §S7: `mcp` 1.27.2 mints ONE `ServerSession` per MCP session → rung 1 | **TRUE — independently RE-DERIVED** with a stronger instrument (see below) |
| `record_trace` has ZERO production callers | **TRUE** — grep over `loremaster/loremaster/`: the only production reference is `trace_aggregates` in `AppContext._trace_summary` |
| "`:18500` prod trace table holds count() = 0" (load-bearing for S8-E3 ground 1 and the free-window index argument) | **NOT RE-DERIVED.** My read-only `SELECT count()` against `:18500` was refused by the environment's command classifier. I did not work around it. **The lead must re-derive this read-only before the E3 ruling is relied on.** |

### 4.1 The S7 re-derivation (my instrument, not the contract's)

The contract compares `id()` **integers**. I compared **object identity** with the objects held
alive in a list, plus request ids and headers:

```
observations: 5
  [0] request_id=1 id=140647423257840 header=50d80d266750...
  [1] request_id=3 id=140647423257840 header=50d80d266750...
  [2] request_id=4 id=140647423257840 header=50d80d266750...
  [3] request_id=1 id=140647421843472 header=d8a56854f496...
  [4] request_id=3 id=140647421843472 header=d8a56854f496...
IDENTITY (is-comparison, objects held alive):
  session A: all 3 calls share ONE ServerSession object -> True
  session B: all 2 calls share ONE ServerSession object -> True
  A is B (must be False)                                -> False
  distinct request_ids within A                          -> 3
  header stable within A / differs across               -> True / True
```

**Rung 1 is correctly selected. The design ruling stands.**

### 4.2 …but the pin that GUARDS that fact uses a weaker instrument (MP11)

`id()` is aggressively reused: 200 sequentially-created-and-freed objects yielded **2 distinct
`id()` values (198 reuses)**. The S7 rung pin captures `id()` from session objects it does not
hold alive; its cross-session control (`first != other_session`) is therefore exposed to a
spurious RED, and — in the dangerous direction — a future per-REQUEST `ServerSession` could be
missed by address reuse on the very assertion that exists to detect it.

**I attempted to induce that false green and FAILED, 3/3.** In a scratch contract copy I replaced
`id(request_context.session)` with `id(<a freshly-minted, immediately-freed object>)` — the exact
SDK change the pin guards:

```
1 failed, 40 deselected  (×3 consecutive runs)
```

The intervening allocations of a real MCP request cycle keep the addresses apart. **Verdict: the
pin holds today; the instrument is nevertheless weaker than it needs to be, and the fix is one
line (hold the objects, compare with `is`).** Recorded as MP11 (LOW), not a blocker.

---

## 5. The deploy-smoke leg — does it prove the ARTIFACT records?

**Partly, and only if a human remembers.** `assert_deploy_smoke_traces` is a well-built *function*
with real controls (good payload accepted; two differently-broken payloads rejected for
*different* reasons; empty payload rejected). But **nothing in the repo runs it against the
artifact.** Its docstring says "THE LEAD RUNS THIS" — a "remember to" obligation, which this
repo's own CLAUDE.md classifies as a hope rather than a guard. The repo already owns the stronger
instrument (**#139 / packet 01a**: run the suite inside the deployed image, asserting
`loremaster.__file__` is in site-packages). **Recommendation: bind the smoke to a committed
deploy script or to the 01a in-image conformance run, so it cannot be skipped.**

Shape checks against the real served model (`IndexStatusSummary.traces: TraceSummary`):

```
TraceSummary.model_dump() -> {"total": 2, "by_tool": [{"tool": "lore_comms", "calls": 1}, …]}
(a) model_dump() mapping            -> ACCEPTED          <- what an MCP client sees. GOOD.
(b) the TraceSummary object itself  -> AttributeError: 'TraceSummary' object has no attribute 'get'
(c) by_tool as pydantic objects     -> AssertionError: "…missing ['lore_comms','lore_search'] (saw [])"
```

Verdicts: **(a) sound.** **(b)** contradicts the function's own `Raises: AssertionError` docstring
— a lead calling it in-process gets a TypeError-shaped surprise. **(c)** `isinstance(entry, Mapping)`
**silently discards** non-mapping entries, so a shape mismatch is reported as *"the artifact
recorded nothing"* — it fails SAFE (no false green) but for the WRONG REASON, and would send a
lead hunting a telemetry outage that does not exist.

---

## 6. P6 — corpse sweep. Every hit gets an individual verdict.

### 6.1 The collateral RED: 7 committed pins the correct build breaks (C-DEF class)

```
$ uv run pytest -n auto -q test_surreal_store.py test_surreal_schema.py test_surreal_fakes.py test_mcp_server.py
7 failed, 962 passed in 125.80s      # against the REFERENCE (correct) build
```

| # | pin | why it breaks | verdict |
|---|---|---|---|
| 1 | `test_surreal_schema.py::TestTraceTableFieldDefinitions::test_trace_core_scalar_fields_are_defined` | asserts `"TYPE int" in … hit_count`; row F loosens it to `option<int>` | **CORPSE — must be amended by the wave.** Unmentioned by the contract or the spec. |
| 2 | `test_surreal_fakes.py::TestRecordTraceFake::test_record_trace_signature_matches_real_store` | asserts the EXACT 7-name old parameter list | **CORPSE — must be amended**, AND it exposes R8 below. |
| 3 | `test_surreal_schema.py::TestTraceRoundTrip::test_trace_probe_round_trips_core_fields` | raw `CREATE trace` without a mint → `Expected int but found NONE` | **STRUCTURAL CONTRADICTION** with `seq int`. Needs an operator/lead ruling. |
| 4 | `…::TestTraceRoundTrip::test_trace_ts_is_auto_populated_when_omitted` | same | same |
| 5 | `…::TestTraceRoundTrip::test_trace_optional_columns_absent_when_omitted` | same | same |
| 6 | `…::TestTraceRoundTrip::test_trace_optional_columns_round_trip_when_given` | same | same |
| 7 | `test_surreal_store.py::TestSchemaMigrationAgainstAnExistingStore::test_the_whole_schema_migrates_an_existing_populated_store` | the repo's **own #107 dirty-store pin** seeds `trace:probe` by raw DDL → `Expected int but found NONE` | **STRUCTURAL CONTRADICTION with the repo's flagship migration invariant.** Highest-priority adjudication. |

**And this is the defect PATH, measured.** Flipping `seq` to `option<int>` (WB3 — which the
contract does not pin):

```
seq int          (correct, S8-E3):  contract 41/41  +  7 committed pins RED
seq option<int>  (WB3, violates E3): contract 41/41  +  2 committed pins RED   (1008 passed)
```

A builder chasing a green tree has a five-test incentive to undo E3's ruling, and **no gate
anywhere stops it.** That is why MP1 is a blocker rather than a nicety: E3's ground 3 —
*"`int` buys a STANDING mechanical guard `option<>` cannot … Instrument over hope"* — is currently
pure hope.

### 6.2 Prose corpses — served/teaching text the change retires, no gate

| file:symbol | the retired claim | verdict |
|---|---|---|
| `store/surreal.py::SurrealStore.record_trace` docstring | *"The async **fire-and-forget** EMISSION that schedules these writes … are a later serving-layer phase (P8d)"* | **CORPSE — actively harmful.** §S6v2 item 6 **REFUSES** fire-and-forget. Production prose teaching the exact posture the spec bans. |
| `store/surreal.py::SurrealStore.record_trace` docstring | *"the **six core fields** describe one served request"*; `hit_count: How many results the call returned`; `session: The fleet/session identity` | **CORPSE** — 13 columns; `hit_count` is now drain-served-only and `session` is now optional. |
| `server.py::TraceSummary` docstring | *"which is EVERY boot today, **since no caller yet wires** the per-invocation `record_trace` emission (that wiring is a later phase)"* | **CORPSE** — false the moment 03b lands, in the same file the builder edits. |
| `store/surreal_schema.py` `_TRACE_FIELD_SPECS` header comment | *"six core columns"*, *"Aggregates … surface in a LATER phase (P8d); P8a defines only the table + its write path"* | **CORPSE** |
| `store/surreal_schema.py::_trace_statements` docstring | *"the six core fields + two optional columns"*; will not mention the sequence or the index | **CORPSE** |
| `store/surreal_schema.py` module header (`trace` in P8a, "six core + two accounting columns") | same | **CORPSE** |
| `server.py` `lore_index` description: *"per-tool trace-call aggregates"* | **NOT a corpse** — §S6v2 item 7 says the widening makes it TRUE for the first time | **CLEAN** (pinned only indirectly, by `test_workspace_status.py::TestLoreIndexDescription`, which checks other clauses) |

⚠ **Delta row F additionally REQUIRES prose that no pin demands:** the `token_cost`/`model`
*zero-writers-by-design* spec comment + `record_trace` docstring line with its re-open trigger,
and the "comms/drain-only" comments on `agent`/`pending`/`peeked`. Unpinned, and WB5 shows the
columns can be deleted outright without a single test noticing.

### 6.3 P6b — independent enumeration of the replaced code's behaviours

**⚠ There is no Phase-0 removed-behavior inventory to diff against.**
`docs/plans/v2/receipts/2026-07-24-packet03b/` holds only `REPORT-design-comms-03b.md` and
`REPORT-scout-147-traces.md`. So the instrument (two INDEPENDENT enumerations, diffed) is
half-missing. My enumeration, made from `surreal.py::record_trace` alone before reading either
report:

| old observable behaviour | preserved? | pinned by 03b? |
|---|---|---|
| writes via `CONTENT` (never `SET`) because `session` is a PROTECTED variable | must be preserved | **no direct pin** — a `SET session = $session` build dies at runtime, so the live legs catch it *incidentally*. Verdict: adequate, by luck rather than design. |
| optional columns OMITTED when `None` so they store NONE cleanly | must be preserved | **yes**, via `test_a_generic_row_may_omit_session_and_hit_count` + `test_a_generic_tool_leaves_the_comms_columns_empty` |
| `ts` stamped SERVER-SIDE by `DEFAULT time::now()`; the method never sends it | must be preserved | **NO PIN.** A seam that stamps `ts` client-side passes. Low severity (`seq` is now the ordering key) — verdict: note only. |
| append-only, never keyed/deduped | preserved | implicitly (`len(rows) == 1` per dispatch) |
| errors classified by the `_query` seam (`SurrealConnectionError` / `SurrealStoreError`) | preserved | not pinned here; owned by `test_surreal_store.py` |
| `hit_count` / `session` REQUIRED | **deliberately dropped** (row F) | the drop is pinned; the *consequences for the 6 committed fake-store tests* are not adjudicated (see 6.1) |

---

## 7. P3 — branch reachability of the seam the builder will write

| branch | reached by | verdict |
|---|---|---|
| request context present → write | the whole suite | reached |
| request context ABSENT → skip, still serve | `test_a_dispatch_without_a_request_context_still_serves` | reached |
| `write_store` absent from a PRESENT context | **no pin** | unreached; harmless (any error is swallowed) — note only |
| tool returns normally | `test_a_succeeding_call_writes_its_row` | reached |
| tool raises `Exception` | `test_a_raising_call_still_writes_its_row` | reached |
| **tool raises `BaseException` / is cancelled** | **no pin** | **UNREACHED → MP2 (WB30)** |
| annotations empty / non-empty | both pinned | reached |
| caller key first-sight / already-minted | both pinned | reached |
| **caller key after the session object dies** | **no pin** | **UNREACHED → MP3 (WB9, WB32)** |
| `record_trace` raises → catch, log, serve | the catch is pinned; **the log is not** | **HALF-UNREACHED → MP6 (WB4)** |
| comms annotation: drain | pinned | reached |
| **comms annotation: register / heartbeat / brief_* / fleet** | **no pin** | **UNREACHED → MP4 (WB1)** |

Dispatch-door reachability is honest: `grep -rn "FastMCP("` finds **exactly one** construction in
production and there is **no other** `call_tool` / `_tool_manager` dispatch site, so the
seam-level pins genuinely reach the production entry point.

---

## 8. MISSING PINS — the deliverable

Each is *the test that should exist* + *the defect it catches*.

**BLOCKER**

- **MP1 — `test_the_schema_rejects_a_writer_that_omits_the_seq_mint`.** Against a live store on
  the production DDL, `CREATE trace CONTENT {tool, params_hash, latency_ms}` (no `seq`) must
  RAISE; and the emitted `seq` field statement must read `TYPE int`, not `option<int>`.
  *Catches:* WB3 — the flip that silently discards ruling S8-E3's standing guard, and which
  5 collateral-RED committed pins actively push the builder toward.
- **MP2 — `test_a_cancelled_dispatch_still_writes_its_row`.** Create the dispatch as a task,
  `task.cancel()`, and assert one row landed.
  *Catches:* WB30 — emission in `except Exception` instead of `finally`. Client disconnects and
  timeouts go untraced, which is exactly the struggling-session population the decay curve is
  about. (Add the companion leak leg: after a cancelled dispatch, the next call's row must carry
  no inherited annotations.)
- **MP3 — `test_the_caller_key_is_unique_across_session_lifetimes`** + a map-hygiene leg. Mint
  keys for N (≥100) sequentially created and *freed* session objects, assert N distinct; and
  assert the caller map retains 0 entries after the sessions are collected.
  *Catches:* WB9 (383/400 collisions) and WB32 (unbounded growth). This is the pin that turns
  §S7's *"no collision path"* claim into an instrument.
- **MP4 — `test_a_non_drain_comms_action_records_agent_and_session`.** Drive
  `lore_comms action='register'` (and `heartbeat`) through the seam and assert the row carries
  the resolved agent RecordID and the fleet session.
  *Catches:* WB1 — the drain-only annotator, which makes §S7 item 2's "the register-first spawn
  protocol means a fleet agent's FIRST lore call binds its key" false, and leaves every
  non-draining agent permanently unattributable.

**HIGH**

- **MP5 — `test_a_drain_whose_limit_exceeds_pending_records_the_served_count`.** Seed 5, drain
  with `limit=20`; assert `hit_count == 5` and `pending == 5`. Keep the existing `limit < pending`
  pin; the PAIR is what discriminates (served is always either `pending` or `limit`).
  *Catches:* WB2 — `hit_count = limit`, which lies on every drain whose inbox is smaller than the
  cap, i.e. the ordinary case. Also fixes the false-gate message in §3.2.
- **MP6 — `test_a_failing_trace_write_is_logged_loudly`.** With a raising store, `caplog` must
  contain ≥1 record at ≥WARNING naming the tool.
  *Catches:* WB4 — `except Exception: pass`, which re-creates #147's silent zero **inside its own
  fix**. §S6v2 item 6 says "never fail silently"; nothing currently checks it.

**MEDIUM**

- **MP7 — extend `test_the_trace_ddl_uses_the_ruled_guards`** to assert (a) `token_cost` and
  `model` are still declared, (b) the `(caller, seq)` index statement names **both** fields in
  order, (c) the emitted type of every new column. *Catches:* WB5, WB6 — both currently pass a
  substring check.
- **MP8 — `test_a_zero_argument_call_records_a_non_empty_params_hash`.** *Catches:* WB22.
- **MP9 — ESCALATION + pin: `trace.session` semantics.** §S6v2 item 5 admits two readings —
  *"the explicit fleet session"* (the resolved agent's `session`) vs *"ONLY an explicitly-known
  comms session"* (the caller-supplied `session=` argument). Every fixture passes
  `session="wave7"` equal to the agent's registered session, so the contract cannot tell them
  apart (WB19). **I would pick the resolved agent's session** — it is always known, it is the
  documented fleet identity, and the argument is optional off-`register`. Whichever the operator
  rules, pin it with a comms call that OMITS `session=`.
- **MP10 — adjudicate the 7 collateral-RED committed pins (§6.1)** before the builder starts, per
  the C-DEF law. Four of them (`TestTraceRoundTrip`) and the flagship
  `TestSchemaMigrationAgainstAnExistingStore` write raw trace rows without the mint; they are
  *structurally* contradicted by `seq int`. The builder must be told which assertion to amend and
  why, or it will "fix" the schema instead.

**LOW**

- **MP11 — the S7 rung pin should hold the `ServerSession` objects alive and compare with `is`,
  not compare `id()` ints.** *Catches:* a future address-reuse false green on the one fact the
  pin exists to guard. (Attempted and could not induce it today — 3/3 RED — so this is hygiene,
  not a live defect.)

---

## 9. RESIDUALS — every one with an individual verdict

| # | residual | verdict |
|---|---|---|
| R1 | `test_seqs_are_distinct_and_increasing_across_a_sweep`'s three ordering assertions read the **double's** seq mint, not production's (proven: freezing the fake to 999 turns it RED) | **DECORATION.** Harmless; real coverage is `TestSeqIsMintedByTheStore`. Re-point at the live store or delete the three asserts and keep the non-vacuity guard. |
| R2 | the drain `hit_count` message names "the SERVED count" while asserting the LIMIT | **FALSE GATE** — closed by MP5. |
| R3 | `assert_deploy_smoke_traces` is a function nobody runs | **UNGUARDED PROCEDURE.** Bind it to a committed deploy script or the packet-01a in-image run (#139). |
| R4 | the smoke silently drops non-`Mapping` `by_tool` entries and then reports "saw []" | **FAILS SAFE, WRONG REASON.** Raise a shape error instead. |
| R5 | the smoke raises `AttributeError` (not `AssertionError`) when handed the pydantic model | **DOCSTRING/BEHAVIOUR MISMATCH.** One-line fix. |
| R6 | the DDL-guard pin's `if/elif` checks three known prefixes; anything else is unchecked | **BLACKLIST SHAPE** (the repo's named defeat class). Invert: assert every statement matches one of the ALLOWED forms, else fail. |
| R7 | 6 prose corpses in the two files the builder edits (§6.2) | **EACH NAMED ABOVE**; the `fire-and-forget` line is the dangerous one — it teaches the posture §S6v2 item 6 refuses. |
| R8 | `_surreal_fakes.FakeSurrealStore.record_trace` is a **second** `record_trace` implementation with a signature-parity pin, and the contract's `_RecordingStore` is a **third** shape | **ESCALATE (ONE-IMPLEMENTATION).** After 03b the tree carries three shapes for one seam and six committed tests against the fake. The builder must be told the fake is in scope; nothing in rows F/G/H mentions it. |
| R9 | production trace count on `:18500` (S8-E3 ground 1, the free-window index argument) | **NOT RE-DERIVED** — my read-only `SELECT count()` was refused by the environment classifier and I did not work around it. **Lead must re-derive read-only.** |
| R10 | the contract needs the comms `drain` action + `peek` (delta rows **C/D**) to reach 41/41; on a rows-F/G-only build it is 39/41 | **SEQUENCING FLAG** — brief the builder for C/D+F/G/H together, or expect a 2-RED tail. |
| R11 | latency fixtures: fast max 0.104 ms vs a 40 ms ceiling (**384×** headroom); slow min 60.14 ms vs a 40 ms floor (**1.50×**) | **SOUND.** No flake risk measured under `-n auto`; the two-fixture pair genuinely discriminates (WB20 died). |
| R12 | the argument-value privacy pin uses one tool, one key, one secret | **ACCEPTED.** The seam is receiver-blind, so a per-tool privacy leak is implausible; no pin demanded. |
| R13 | no Phase-0 removed-behavior inventory exists for this packet | **INSTRUMENT MISSING** — my P6b enumeration (§6.3) had nothing to diff against; it is recorded unilaterally, which is strictly weaker. |
| R14 | a build tracing only names matching a prefix (`lore_`/`probe_`) passes the sweep, since every registered tool matches | **ACCEPTED under the stated threat model** (the honest engineer adding a `lore_*` tool in packet 04 is still caught). Noted, not demanded. |
| R15 | nothing pins that `ts` stays SERVER-stamped | **NOTE ONLY** — `seq` is now the ordering key, so client-side `ts` skew is cosmetic. |
| R16 | nothing structurally asserts `build_mcp_server` returns a `TracingFastMCP` | **ADEQUATE** — behavioural coverage through the real factory is stronger than an `isinstance`. |
| R17 | `hit_count` for a generic call is honest NONE, and the honest-NONE leg exists | **CLEAN — a good pin.** |
| R18 | the #107 dirty-store migration pin (`test_the_new_columns_land_on_an_ALREADY_EXISTING_trace_table`) | **CLEAN AND STRONG.** It genuinely catches `DEFINE FIELD IF NOT EXISTS` for the loosened fields, and it applies the PRODUCTION emitter rather than hand-rolled DDL. Best pin in the file. |

---

## 10. What I could not break (stated, so the strengths are not lost)

- The coverage derivation is genuinely **live**, not a snapshot — `test_the_coverage_derivation_is_live_not_a_snapshot`
  registers a tool the fixture never mentions and demands it on both sides. I could not construct
  a build that counts a tool on both sides without dispatching it: `dispatched` is *what the pin
  tried to call*, and `observed` is *what wrote a row*, so set equality is a real implication.
- Batching / replay / one-row-per-registered-tool builds are killed by the ORDERED comparison.
- A second writer is killed by `len(rows) == 1`.
- Fire-and-forget is killed hard (25 failed).
- A constant `latency_ms` is killed by the fast/slow fixture pair.
- A per-(session, tool) caller key is killed because the same-session pin uses two DIFFERENT tools.
- The S7 rung pin resisted a deliberate per-request-session simulation, 3/3.

---

## VERDICT: **CONTRACT INSUFFICIENT**

Eleven wrong builds pass 41/41. Four of them (WB9, WB30, WB1, WB3) defeat properties the design
rulings state as guarantees — §S7's *"no collision path"*, §S6v2 item 2's *"an errored pull is
still a pull"*, §S7 item 2's *"the FIRST lore call binds its key"*, and §S8-E3's *"instrument over
hope"*. MP1–MP4 close them; MP5–MP11 close the rest. MP10 is not a pin but a ruling the builder
cannot proceed safely without.
