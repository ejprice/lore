# REPORT-adversary-telemetry-03b-r2 — contract adversary, packet 03b T-series telemetry

brief-base v6 read

> **All measurements in this report were taken 2026-07-24 against lore HEAD `03b93d3`**
> (branch `feat/surreal-unification`), engine spike-surreal **3.2.1** on `ws://127.0.0.1:18000`
> (`:18500` production was never contacted), `mcp` **1.27.2**, Python 3.14, 64-core host.
> Every "survives" / "dies" claim is a run of the REAL graded contract at that SHA against a
> wrong build in scratch — not a claim about any later state of those files.
> **Provenance receipt:** `loremaster.__file__ = /home/ejprice/scratch/adv-telemetry-03b-r2/loremaster/loremaster/__init__.py`
> (via `./scripts/scratch_copy.sh`). **The repo was never edited by me** — this report is the only
> file I wrote inside it. (`git status` at close also shows `docs/plans/v2/03b-design-rulings-r2.md`
> modified by a PARALLEL actor mid-run; telemetry-neutral — residual **R13**.)

---

## SUMMARY BLOCK

- **VERDICT: CONTRACT INSUFFICIENT.**
- **P1 headline — FOUR wrong builds survive the contract at the reference build's own score
  (1 failed / 451 passed), plus one surviving ORACLE mutation.** The worst: **W30** — the
  emission passes ONE keyword the real `record_trace` does not accept; the seam double takes
  `**fields` so every pin stays green, the T5.1 swallow hides the `TypeError`, and **every
  production trace write fails forever → `traces.total` stays 0. That is #147 reproduced by
  the packet that exists to close #147.**
- **QUANTIFIER TABLE (P1b): §2** — 17 invariants classified; 6 are guarded-not-∀; every
  guarded row carries a surviving door-build or the pin that killed the door.
- **MISSING PINS** (each with a written prototype + BOTH control legs): **MP-A** seam→REAL-store
  end-to-end leg (kills W30) · **MP-B** ∀-tools **success** coverage leg (kills W11) ·
  **MP-C** the ordinal-monotonicity pin is **UNSATISFIABLE** (`zip(..., strict=True)` always
  raises) so that property is pinned by nothing and the builder is trapped · **MP-D**
  fixture-independent latency pin (a constant 50.0 ms survives today) · **MP-E** zero-argument
  `params_hash` pin · **MP-F** the oracle's four new columns + its ordinal are unpinned ·
  **MP-G** three unguarded production prose corpses (incl. `TraceSummary`, served by `lore_index`).
- **Fixture discrimination: §5.** The latency fixture is value-aligned (perturbation pair proven,
  both legs). `_MINIMAL_ARGS` is NOT a monoculture (verified). The coverage battery is
  outcome-monocultured (error leg only) — that is MP-B.
- **RED reproduced (§6):** 69 failed / 618 passed over the six graded files, **0 collection
  errors**, distribution 64 / 3 / 1 / 1. Every RED is a missing production symbol or behaviour.
- **Satisfiability receipt (§1):** my blind reference goes **451 passed / 1 failed** (four files)
  and **686 passed / 1 failed** (six files); the single failure is MP-C, unsatisfiable by
  construction. ruff clean; mypy: zero errors in any telemetry file (§7 residual R8).
- **Author-claim verification (§4):** 19 named obligations re-run — 15 exact, **4 mis-stated**
  (M6, M4, M13, M19); M19's second guard needed a NEW mutation (M20), supplied and proven.
- **Blast radius (§8):** the oracle change is consumer-safe — **1457 passed / 0 failed** over the
  20 suites I re-derived (author said 21; derivation in §8). Concurrency: **20/20 consecutive**.

---

## §0 What I did, in order (and the boundary I kept)

1. Read the design authority FIRST: `docs/plans/v2/03b-design-rulings-r2.md` §B (T1–T8, T2.1) +
   §G (ESC-1 success latch, ESC-2 channel A) · `03b-comms-message-surface.md` (lines 1–204 only —
   I deliberately did **not** read its §ADVERSARY WAVE block, which summarises the struck
   adversary, until my own P1 battery was complete) · `docs/reference/surrealdb-31-capabilities.md`
   §1.1/§1.4/§2 + the `7f23223` additions · `03a-2-consume-path-design-rulings.md` R3 (the two
   message indexes) · production at HEAD · installed `mcp==1.27.2` source.
2. Built a REFERENCE implementation in scratch from the rulings ONLY.
3. **FROZE it** (md5s below) before opening a single test file.
4. Read the graded set; ran satisfiability; four-way-adjudicated every RED.
5. P1/P1b/P2/P3/P4/P5/P6/P6b/P7 batteries.
6. Only then read `REPORT-adversary-telemetry-03b.md` (struck) for the blind-diff completeness
   check — both directions, §9.

**Freeze receipt (2026-07-24T09:26:25-04:00, before any test file was read):**

```
76e88d00c18d45643efc6742523b56a0  loremaster/loremaster/server.py
3f7fde591a29f0cbb5065bbaecc2ff28  loremaster/loremaster/store/surreal.py
b2ce664a507c0d781e8ffd4b950296c2  loremaster/loremaster/store/surreal_schema.py
```

The reference after the four contract-demanded fixes of §1.2 (the build every wrong build below
was patched from and restored to; re-verified byte-identical at close):

```
5fee869affa6941941de9266af0d4f37  loremaster/loremaster/server.py
fce52db0748b399119e35ec9cd23aa1b  loremaster/loremaster/store/surreal.py
57711905f16423108aa1098d53967f11  loremaster/loremaster/store/surreal_schema.py
7389d74c1e006cfeca42f1be5d018be2  loremaster/tests/_surreal_fakes.py   (untouched HEAD oracle)
```

### The reference seam (reproduced here so this report is self-contained)

```python
class TracingFastMCP(FastMCP):
    _DECLARED_IDENTITY_KEYS = ("agent", "session", "action")
    _TRANSPORT_SESSION_HEADER = "mcp-session-id"

    async def call_tool(self, name, arguments):
        started = time.perf_counter()
        ok = False                                  # the latch
        try:
            result = await super().call_tool(name, arguments)
            ok = True                               # set ONLY on return; no except arm
            return result
        finally:
            latency_ms = (time.perf_counter() - started) * 1000.0
            try:
                await self._emit_trace(tool=name, arguments=arguments,
                                       latency_ms=latency_ms, ok=ok)
            except Exception:
                logger.exception("trace.emit.failed", extra={"tool": name})
```

plus `_emit_trace` (channel A: `self._mcp_server.request_context.lifespan_context.write_store`,
declared-only identity, header correlator, `sha256(json.dumps(args, sort_keys=True, default=str))`),
the T2/T2.1 schema delta (`hit_count`/`session` → `option<>`, five new `option<>` columns,
`_define_sequence("trace_seq")`, `_plain_index(trace, "trace_agent_ordinal", ("agent","ordinal"))`),
`record_trace`'s T8 signature with the store-side mint
(`CREATE trace CONTENT object::extend($content, { ordinal: sequence::nextval("trace_seq") })`),
and the two E-S6 message indexes in `_message_statements`.

---

## §1 Satisfiability receipt + four-way adjudication of every RED

### §1.1 The run

```
$ uv run pytest -n auto -q test_trace_telemetry.py test_comms_schema.py \
      test_surreal_schema.py test_surreal_fakes.py
1 failed, 451 passed in 17.95s
$ uv run pytest -n auto -q <the six graded files + test_surreal_store.py + test_surreal_harness.py>
1 failed, 686 passed in 25.71s
$ uv run ruff check .
All checks passed!
```

The ONE failure is MP-C (below) — a pin no correct build can pass. **This is the C-DEF class the
repo legislates for: a contract that cannot go 0-failed against a known-correct build.**

### §1.2 Four-way adjudication of the 7 REDs my frozen reference hit

| # | pin | verdict | evidence |
|---|---|---|---|
| 1 | `TestTheOrdinalIsMintedByTheStore::test_sequential_writes_carry_strictly_increasing_distinct_ordinals` | **PIN DEFECT (blocker)** | `zip(ordinals, ordinals[1:], strict=True)` over a 3-element list ALWAYS raises `ValueError: zip() argument 2 is shorter than argument 1`. Control: `all(l>e for e,l in zip(o,o[1:]))` → `True` for `[0,1,2]`, `False` for a non-increasing list; with `strict=True` → `ValueError` in both cases. **Unsatisfiable for every build** (the earlier `assert len(ordinals)==3` guarantees the mismatch). See MP-C. |
| 2 | `TestTheTraceSchemaDelta::test_the_ok_columns_ruled_semantics_are_documented_where_it_is_DEFINED` | **REFERENCE DEFECT** (+ residual R1) | My comment carried the ruled sentence VERBATIM but (a) wrapped across two `#` lines and (b) placed inline beside the `ok` tuple entry. The pin's window is `source_lines[specs-60 : specs+1]` — i.e. ABOVE the assignment only — and its `" ".join(window.split())` normalisation keeps the `#`, so a wrapped clause fails. Fixed by moving the sentence, unwrapped, above the assignment. Pin is legitimate; its brittleness is R1. |
| 3–5 | `TestNoProductionProseStillTeachesTheRetiredPlan` ×3 | **REFERENCE DEFECT** | I left "six core fields" / "fire-and-forget" in the two docstrings. The packet names them a known prose corpse; AC-19 demands the sweep. Pins correct. |
| 6 | `TestATraceWriteFailureNeverTouchesTheCall::test_a_failing_store_leaves_a_successful_result_intact` | **REFERENCE DEFECT** | My log call was `logger.exception("trace emission failed for tool %s", name)` — an interpolated sentence. The pin demands a dotted structured event. Verified the house idiom is REAL, not invented: `scout.periodic_reconcile.sweep_failed`, `store.transaction.malformed_response`, `startup.probe_gate.refuse`. Fixed to `logger.exception("trace.emit.failed", extra={"tool": name})`. |
| 7 | `test_surreal_fakes.py::TestRecordTraceFake::test_record_trace_signature_matches_real_store` | **REFERENCE DEVIATION** (+ residual R2) | I ordered the signature `tool, params_hash, latency_ms, hit_count=…` (required-before-defaulted habit). The pin asserts the exact committed ORDER `…, hit_count, latency_ms, …`. Every parameter is keyword-only, so the order carries NO semantics — a legal, natural signature is RED for a cosmetic reason. Pin defensible (parity), over-specified. |

No RED was a ruling ambiguity or a ruling defect.

---

## §2 P1b — THE QUANTIFIER TABLE (∀-over-inputs vs guarded-by-known-failure-mode)

Baseline for every row: the correct reference scores **1 failed / 451 passed**. A door-build that
also scores **1 failed / 451** SURVIVES.

| # | invariant | ∀ or GUARDED | receipt |
|---|---|---|---|
| I1 | every dispatch of every registered tool writes exactly one row carrying the dispatched name | **GUARDED by OUTCOME** — the coverage battery dispatches all 16 tools against a minimal double, so all 15 real tools take the ERROR leg; the only SUCCESS ever traced is a synthetic probe | **DOOR BUILD SURVIVES: W11** (`if ok and not tool.startswith("probe_"): return`) → **1 failed / 451 passed**. Every successful real-tool call untraced. Failed door attempts recorded: W11b/W11c (result-shape-keyed) died 21F — the synthetic probes also return `(content, structured)` tuples, so only a NAME-keyed skip reaches the cell. → **MP-B** |
| I2 | the row actually LANDS in the real store | **GUARDED by the DOUBLE** — `_TraceRecorder.record_trace(**fields)` accepts any keyword; no pin drives the seam into a real `SurrealStore` | **DOOR BUILD SURVIVES: W30** (one extra kwarg) → **1 failed / 451 passed**, while a real store raises `TypeError: record_trace() got an unexpected keyword argument 'request_id'` and the T5.1 swallow hides it. → **MP-A (BLOCKER)** |
| I3 | `ok` True iff the dispatch RETURNED (False on any raise, cancellation included) | **∀ over {return, raise, cancel}** | W7 (latch regression `ok=True`-initial + `except Exception`) → RED on the cancelled leg. W6 (`except`+success arms) → RED on the same leg. M4 (except-only) → RED. |
| I4 | the tool's result/error is never altered by telemetry | **∀ over {success, raise, store-broken, no-context}** | M19 (re-raise from `finally`) → 2 pins RED; M20 (context resolved outside the swallow) → the no-app-context pin RED. |
| I5 | a trace-write failure is LOUD (structured dotted event, `exc_info`, names the tool) | **∀ over failure modes** | My own reference's first pass went RED for an interpolated message; positive control in the same class asserts the healthy store DOES write. |
| I6 | identity is DECLARED, never guessed | **∀ over {all three, partial, silent-after-declaring, non-str, ledger-actor aliases}** | M7 sticky (instance) → exactly the sticky pin. W2a sticky (class-level) → sticky + non-str pins. M8 alias harvest → RED. M9 `str()` coercion → RED. M10 correlator→`session` → 3 identity pins RED. W17 correlator→`agent` → 3 RED. |
| I7 | `transport_session` = the `mcp-session-id` header, else NONE | **∀ over {header, no header, no transport}** | W27 (`str(id(session))` correlator) → 5 identity pins RED. Also moot-by-construction: the SDK mints `uuid4().hex` (`streamable_http_manager.py`), and my 400-session probe (§3.3) shows `id()` collapses 400 non-overlapping sessions to 1 key. |
| I8 | `params_hash` is the T6 recipe and no raw content reaches the row | **GUARDED by NON-EMPTY ARGUMENTS** — every recipe pin passes a non-empty dict | **DOOR BUILD SURVIVES: W31** (`if not arguments: return ""`) → **1 failed / 451 passed**. Four registered tools take no arguments (`lore_map`/`lore_index`/`lore_diff`/`lore_dead_code`). → **MP-E** |
| I9 | recorded latency reflects the call's real duration | **GUARDED by ONE FIXTURE BRACKET** — one dispatch, `45ms ≤ latency ≤ elapsed+5ms` | **DOOR BUILD SURVIVES: constant `latency_ms = 50.0`** → **1 failed / 451 passed**, though the pin's own comment claims it "kills a build passing 0, a constant, …". 0 dies (W16); seconds dies (M18); a constant inside the bracket lives. Perturbation pair in §5.1. → **MP-D** |
| I10 | the seam never fabricates a `hit_count` | **∀ over values** | W5 (`hit_count=0`) RED; W32 (`hit_count=7`) RED — the honesty pin discriminates away from the zero value, which is the brief's `hit_count = limit` question answered. |
| I11 | the ordinal is engine-minted, present, int, ≥0, distinct, strictly increasing; counts come from ROWS | **PARTLY ∀, one leg DEAD** | W4 (omit the mint) → 6 RED. M6 (seam mints) → seam pin RED. M14 (`ordinal=` param) → FK-3b RED. 8-way distinctness: 20/20 consecutive passes on the reference. ⚠ **W20 (per-PROCESS client-side mint) PASSES the 8-way pin** — measured, 2 passed in that class — and is caught only by the gap/count pin; the 8-way pin's docstring claim is wrong (R3). And **the strictly-increasing leg is dead** (MP-C). |
| I12 | schema delta: 5 added `option<>` + OVERWRITE, 2 widened, others unchanged, sequence exact, index fields/kind, no transport index | **∀ over columns (parametrised)** | W3a (required columns) 11F · W3b (un-widened) 12F · W22 (`IF NOT EXISTS`) 19F · W23 (`BATCH/START`) 1 pin · W13 (fields reversed) 1 pin · M15b (`OVERWRITE` index) 2 pins. |
| I13 | the delta migrates a DIRTY store | **∀ (old DDL → row → new DDL → 4 legs)** | W22 reddens all four migration legs. |
| I14 | `record_trace` signature + fake parity, no `ordinal` parameter | **∀ over the parameter list** | M14 → FK-3b RED, naming the client-side mint. |
| I15 | no production prose still teaches the retired plan | **GUARDED to THREE named docstrings** | **Unguarded corpses found (§6.2): `server.py::TraceSummary` ("no caller yet wires the per-invocation record_trace emission"), `surreal_schema.py` module header ("trace in P8a (six core + two accounting columns…)"), `surreal.py::trace_aggregates` (cites the sentence the builder must delete).** → **MP-G** |
| I16 | the two `message` hot-path indexes ship, PLAIN, sender-first | **∀ over {missing, UNIQUE, reversed, superset}** | W14b missing → 3 RED (incl. the live leg) · W14 UNIQUE → 2 RED · W28 reversed → 1 RED · W29 superset → 1 RED. |
| I17 | the ORACLE mirrors the real row shape | **UNPINNED** | **ORACLE MUTATION SURVIVES:** drop `agent`/`action`/`transport_session`/`ok` from the fake's row AND freeze its ordinal at 0 → `test_surreal_fakes.py` + `test_mcp_server.py` + `test_trace_telemetry.py` = **1 failed / 783 passed** (the 1 is MP-C). → **MP-F** |

---

## §3 P1 — the wrong-build battery (44 builds; 4 survivors + 1 surviving oracle mutation)

Every build was applied to the frozen reference in scratch by a patch script, run against the REAL
graded contract, then restored from a byte-identical snapshot. Command shape:

```
$ wrongbuild.sh <label> <patch.py>      # restore → patch → pytest -n auto -q <4 graded files> → restore
```

### §3.1 The four SURVIVORS (score identical to the correct build)

| id | the build | score | what ships to production |
|---|---|---|---|
| **W30** | the emission passes one extra keyword (`request_id=…`) to `record_trace` | **1 failed / 451 passed** | **EVERY trace write raises `TypeError`, is swallowed by the T5.1 log-and-serve, and `traces.total` stays 0 forever. #147, verbatim, shipped by the packet that closes #147.** |
| **W11** | `if ok and not tool.startswith("probe_"): return` in `_emit_trace` | **1 failed / 451 passed** | every SUCCESSFUL real-tool call is untraced; the denominator becomes "calls that failed", and the decay curve packet 06 decides on is garbage. |
| **P2-const** | `latency_ms = 50.0` (a constant) | **1 failed / 451 passed** | every row reports the same latency; the pin whose comment says it kills constants passes because 50 ms sits inside the fixture's own bracket. |
| **W31** | `params_hash = ""` when `arguments` is empty | **1 failed / 451 passed** | `lore_map` / `lore_index` / `lore_diff` / `lore_dead_code` rows all carry an empty digest and collapse into one bucket. |

Receipt for W30's production effect (the positive control that the build is genuinely broken):

```
$ uv run pytest -q loremaster/tests/test_adv_probe_end_to_end.py     # MP-A prototype, W30 applied
TypeError: SurrealStore.record_trace() got an unexpected keyword argument 'request_id'
1 failed in 1.33s
$ ... same probe, correct reference build
1 passed in 1.31s
```

### §3.2 The 40 builds the contract KILLS (each with its measured RED set)

| id | build | failures (excl. the always-red MP-C pin) |
|---|---|---|
| W1 | **the no-op fix** — `TracingFastMCP` exists, `build_mcp_server` constructs plain `FastMCP` | **39** — both G1 pins, all 16 coverage parametrisations, the wire-handler leg, every behaviour battery |
| M2 | subclass exists, `call_tool` NOT overridden | **38** |
| W8 | **partial fix** — success path only, no `finally` | **17** |
| M4 | except-arm only (failures only) | **20** (incl. coverage[probe_trace_ok] — see R5) |
| W6 | write moved from `finally` into except+success arms | **1** — the cancelled-dispatch pin ONLY (exactly as designed) |
| W7 | latch regression: `ok=True` initial + `except Exception` | **1** — the cancelled-dispatch pin's `ok is False` leg |
| W10 | name-list build (`if not tool.startswith("lore_"): return`) | **22** |
| W15 | fire-and-forget (`create_task`) | **36** |
| W16 | `latency_ms = 0.0` | **1** |
| M18 | latency in seconds | **1** |
| W5 | `hit_count=0` | **1** |
| W32 | `hit_count=7` | **1** |
| W9 | hash without `sort_keys` | **1** |
| M11/M12 | raw arguments stored beside the hash | **3** |
| W2a | session-sticky (class-level map) | **2** |
| M7 | session-sticky (instance map — the author's shape) | **1** |
| M8 | harvest `owner`/`actor`/`created_by` into `agent` | **1** |
| M9 | `str()`-coerce a non-str declared value | **1** |
| M10 | copy the correlator into `session` | **3** |
| W17 | correlator → `agent` fallback | **3** |
| W27 | `str(id(session))` correlator (brief-named) | **5** |
| W18 | harvest only `agent`+`session`, drop `action` | **1** |
| W19 | write `""` instead of omitting an unset column | **1** |
| W4 | omit the ordinal mint | **5** |
| W20 | per-process client-side ordinal | **1** (the gap/count pin — **NOT** the 8-way pin; see R3) |
| M6 | the SEAM mints and passes `ordinal=` | **1** |
| M14 | `record_trace` gains an `ordinal=` parameter | **1** (FK-3b) |
| W3a | five enrichment columns REQUIRED | **10** |
| W3b | `hit_count`/`session` left un-widened | **11** |
| W22 | trace fields emitted `IF NOT EXISTS` (#107's shape) | **18** incl. all four migration legs |
| W23 | sequence with `BATCH 1000 START 0` | **1** |
| W13 | index FIELDS reversed | **1** |
| M15b | index with `OVERWRITE` | **2** |
| W14 | message indexes UNIQUE | **2** |
| W14b | message indexes missing | **3** |
| W28 | `(question, sender)` instead of `(sender, question)` | **1** |
| W29 | `message_seq` as a `(seq, session)` superset | **1** |
| M19 | emission re-raises from `finally` | **2** |
| M20 | context resolved OUTSIDE the swallow | **1** |
| W11b/W11c | result-shape-keyed success skip | **20** — the door attempt that FAILED (probes return tuples too) |

### §3.3 The brief-named `caller = str(id(session))` question, settled both ways

```
non-overlapping sessions: 400 · distinct id() keys: 1 · COLLISIONS: 399
first collision (session #a reused by #b): (0, 1)
POSITIVE CONTROL — simultaneously-live sessions: 400 · distinct id() keys: 400
uuid4().hex over 400 mints: distinct = 400
```

- **Moot by construction**: the r2 design records the SDK's `mcp-session-id`, and the SDK mints it
  as `uuid4().hex` (`mcp/server/streamable_http_manager.py`) — read, not assumed.
- **AND a pin catches it anyway**: W27 (an `id()`-derived correlator) reddens 5 identity pins.
  Both legs answered; the hazard that headlined the struck adversary is closed twice over.

---

## §4 P4 — the author's 19 named obligations, re-run (never relayed)

15 exact. **Four mis-stated**, all reported here rather than repaired:

| # | claim | measured | verdict |
|---|---|---|---|
| M6 | RED: seam-mint pin **+ `test_eight_concurrent_writes…` + FK-3b** | ONLY the seam-mint pin (the store's signature and mint are untouched by a seam-side mint, so neither other pin can see it) | **over-claim** — the other two belong to M14/W20 |
| M4 | "`…records_ok_true` RED while **coverage stays green**" | coverage stays green for **15 of 16** — `coverage[probe_trace_ok]` also reddens (that entry is a SUCCEEDING tool) | **over-claim, harmless** |
| M13 | "FK-3a, **on that column alone**" | 11 pins RED (the un-widened types also break live writes and the migration legs) | **under-claim** |
| M19 | proves **both** vacuous guards | proves ONE (`…_on_a_failing_tool_…`). `…_no_reachable_app_context_…` stays green under M19 because with no context the reference returns before any write | **half-wrong — substitute supplied: M20** (resolve the context OUTSIDE the swallow) reddens exactly that pin, so it IS discriminating. Record M20 as the correct obligation. |

The wave-2 §10a latch obligation (restore `ok=True`-initial + `except Exception`) → **W7**:
the cancelled leg reddens, alone. ✔ Exactly as claimed.
The §9.2 four E-S6 receipts → **W14b/W14/W28/W29** + the live leg. ✔ All four discriminate.

**The author's §4 probe receipts, independently re-probed by me (each with its own control):**

```
FACT1 nextval first=0 second=1                                  (0-based ✔)
FACT2 CONTENT+SET   : REJECTED -> Parse error: Unexpected token `SET`
FACT2 CONTENT+MERGE : REJECTED -> Parse error: Unexpected token `MERGE`   (different token ⇒ not one blanket rejection)
FACT2 object::extend: ACCEPTED
FACT3 SELECT * (b unset)  keys = ['a', 'id']
FACT3 CONTROL SELECT * (b set) keys = ['a', 'b', 'id']          (the probe CAN see presence)
FACT3 explicit projection (b unset) = {'b': None}
```

All three `7f23223` facts hold on 3.2.1 at my own hand. ✔

---

## §5 P2 — fixture discrimination, with perturbation and correct-build controls

### §5.1 The latency fixture is VALUE-ALIGNED (the finding)

`_SLOW_TOOL_SECONDS = 0.05`, `_LATENCY_TOLERANCE_MS = 5.0`; the pin asserts
`45 ≤ latency ≤ elapsed+5`. Any constant in that window passes.

| leg | build | fixture | result |
|---|---|---|---|
| blindness | constant `50.0` | **original 0.05 s** | **PASSES** (whole contract: 1 failed / 451 passed) |
| perturbation | constant `50.0` | scratch copy with `0.30 s` | **FAILS** — `assert 50.0 >= ((0.3 * 1000) - 5.0)` |
| **control** | correct reference | scratch copy with `0.30 s` | **PASSES** (1 passed) — the perturbation is well-formed, not a botched expectation |

⇒ the pin discriminates only at its own fixture value. MP-D replaces the bracket with a
comparison of two dispatches of different real durations, which no constant can satisfy.

### §5.2 Fixtures that DO discriminate (individual verdicts, nothing waved through)

- `_MINIMAL_ARGS` vs the identity fixtures — **NOT a monoculture**: `lore_comms` uses
  `agent="coverage-probe", action="fleet"`; the identity legs use `auditor-q` / `wave9` / `drain`.
  A build keying on one value fails the other. ✔
- Two transport-session constants, plus a no-header leg and a no-transport leg. ✔
- The int-agent probe (`agent: int`) and the ledger-actor probe (`owner/actor/created_by`) — both
  kill real builds (M9, M8). ✔
- The dirty-store fixture freezes `_OLD_TRACE_FIELD_SPECS` as a literal rather than deriving it —
  correct; deriving would make the pin vacuous the moment the delta lands. ✔
- `TestTheIndexFieldsParserItself` — the instrument has its own positive AND negative control
  (a forged index NAMED `trace_agent_ordinal` with `FIELDS tool` parses as `('tool',)`). ✔
- The 8-way concurrency fixture — 8 stores on 8 connections, one database. Distinctness held
  **20/20 consecutive runs** on the reference. ✔ (but see R3 for its docstring's over-claim)
- ⚠ `test_no_raw_parameter_content_reaches_the_row` searches four fragments, one of which
  (`"row-shaped"`) does **not appear in `_HOSTILE_BODY` at all** — a vacuous element inside the
  ∀-loop (R4). The other three are real and W-M12 dies on them.

---

## §6 P3 branch reachability · P6 corpse sweep · P6b independent enumeration

### §6.1 P3 — every branch of the reference, and the pin that kills it

| branch | killed by |
|---|---|
| `ok=False` initial / latch on return | cancelled pin (`ok is False`), raising pin, success pin |
| the `finally` arm itself | cancelled pin (W6/W7) |
| inner `try/except` around the write (log-and-serve) | M19, the loud-log pin, the failing-store pins |
| `_request_context()` → `None` (no request) | `…_no_reachable_app_context_still_serves_the_tool` — **proven discriminating by M20**, not by M19 |
| `isinstance(value, str)` in the identity harvest | non-str pin (M9) |
| `_transport_session`: no request → NONE | `…_no_transport_request_at_all` |
| `_transport_session`: request without the header → NONE | `…_carries_no_session_header` |
| `_transport_session`: header value not a `str` | **UNREACHABLE through the real entry point** (HTTP headers are strings) — declared, not pinned |
| `record_trace` optional-omission loop, None branch | `…_an_anonymous_row_stores_NONE_in_every_declared_column` |
| `record_trace` optional-omission loop, value branch | `…_the_declared_fields_round_trip` |
| the store-side ordinal mint | the ordinal battery (W4, M6) |
| every schema statement | the schema battery (W3a/W3b/W22/W23/W13) |
| the two message indexes | the E-S6 battery (W14/W14b/W28/W29) |

No branch of the reference is unreached except the declared-unreachable one.

### §6.2 P6 — bare, anchor-free corpse sweep (every hit gets an individual verdict)

`grep -rn "fire-and-forget|six core|no caller yet|later phase|later serving-layer|never wired|not yet wired" loremaster/loremaster/`

| site (symbol-cited) | verdict |
|---|---|
| `surreal_schema.py` module header — *"``trace`` in P8a (six core + two accounting columns…)"* | **CORPSE, UNGUARDED.** The prose pin uses `inspect.getdoc(_trace_statements)`; a module-level COMMENT is invisible to it. After 03b the table has 13 columns. → MP-G |
| `surreal_schema.py::_trace_statements` docstring, summary line | **CORPSE, GUARDED** (`…_no_longer_claims_six_core_fields`) |
| `surreal_schema.py::_trace_statements` docstring, body | **CORPSE, GUARDED** (same pin) |
| `surreal.py::record_trace` docstring — "six core fields" | **CORPSE, GUARDED** |
| `surreal.py::record_trace` docstring — "fire-and-forget EMISSION … later serving-layer phase (P8d)" | **CORPSE, GUARDED** on "fire-and-forget"; the trailing "later serving-layer phase" is guarded only by adjacency |
| `surreal.py::trace_aggregates` docstring — *"the 'later serving-layer phase' the `record_trace` docstring flagged"* | **CORPSE BY REFERENCE, UNGUARDED.** It quotes a sentence the builder must delete; afterwards it cites nothing. → MP-G |
| `server.py::TraceSummary` docstring — *"``0``/``[]``/``None`` … which is EVERY boot today, since no caller yet wires the per-invocation `record_trace` emission (that wiring is a later phase per its own docstring)"* | **CORPSE, UNGUARDED, and the most consequential.** It is the docstring of the model `lore_index` SERVES; it will be false the moment 03b deploys, and it is exactly the "served prose no gate checks" class. → MP-G |
| `index/watcher.py` `_launch_overflow_reconcile` comment — "fire-and-forget from the watcher's own…" | **NOT A CORPSE** — different subsystem, still true |
| `surreal.py` module docstring — "app-level retry/backoff … left for a later phase" | **NOT A CORPSE** — unrelated to telemetry, untouched by this packet |
| `server.py` `_COMMS_ACTIONS` forward-compat comment — "in a later phase" | **NOT A CORPSE** — comms surface, unrelated |
| `server.py` extension-hooks comment — "extension-hooks-and-later phase" | **NOT A CORPSE** — unrelated |
| `server.py::index_status` docstring — *"``traces`` is the store's `trace` table aggregate … 'none recorded' on a fresh/never-traced table"* | **NOT A CORPSE** — remains true after 03b |
| `_surreal_fakes.py::FakeSurrealStore.record_trace` docstring — *"``ok`` (whether the tool call succeeded)"* | **CORPSE IN THE ORACLE (R9).** That is the exact wording ESC-1 corrected ("leaves the next reader to guess about cancellation"); the `ok`-semantics pin scans only `surreal_schema`, so the oracle teaches the retired reading. |

Test-tree corpse sweep (old-world assertions): `test_surreal_schema.py` asserts `TYPE option<int>`
/ `TYPE option<string>` (amended, correct); no test anywhere still asserts the old scalar types or
a required `hit_count`/`session` parameter. **No test corpses found.** ✔

### §6.3 P6b — independent enumeration of the REPLACED code, then the diff

**No Phase-0 removed-behaviour inventory was named in my brief and none exists in the packet
receipts for the telemetry slice** — so stage 2 has nothing to diff against. I record my stage-1
enumeration (from source alone) with an adjudication for each, and flag the missing inventory.

Replaced/deleted behaviour in `FakeSurrealStore.record_trace` and `SurrealStore.record_trace`:

| # | old observable behaviour | status | adjudication |
|---|---|---|---|
| O1 | `hit_count`/`session` REQUIRED → omitting either raised `TypeError` (loud) | replaced by silent NONE | **preserved-with-pin** (T8 rules it; the parity pin asserts real/fake defaults MATCH, so the loosening cannot diverge between them) |
| O2 | optional `token_cost`/`model` stored only when given | preserved (now a loop) | pinned (`…_omitted_optionals_read_back_none`, `…_stores_optional_columns_when_given`) ✔ |
| O3 | fake stamps `ts` itself | preserved | pinned ✔ |
| O4 | `_maybe_trip_connection_failure()` BEFORE any append | preserved | pinned (arm/recover + shared-counter tests) ✔ |
| O5 | append-only, never deduped | preserved | pinned ✔ |
| O6 | every fake row carried keys `{tool, params_hash, hit_count, latency_ms, session, ts}` unconditionally | **CHANGED** — `hit_count`/`session` now omitted when None, so `row["session"]` can `KeyError` | **checked, safe**: every consumer of `recorded_traces()` in the tree passes both explicitly (grep + the 1457-passed blast radius). No consumer indexes an omitted key. |
| O7 | (new) the fake mints an ordinal | **UNPINNED** → MP-F |
| O8 | (new) four columns stored when given | **UNPINNED** → MP-F |
| O9 | store: `hit_count int` / `session string` REJECTED a wrong-typed value at the engine | preserved by `option<int>`/`option<string>` | **spec-silent, unpinned in BOTH worlds** — no pin ever asserted a type rejection for these columns, so nothing was lost; recorded as R7 rather than a defect |

---

## §7 Missing pins — each is a test the author can go write, with both control legs proven

Prototypes were written and RUN in scratch (never in the repo). Each shows PASS on the correct
reference and FAIL on the named wrong build.

### MP-A (BLOCKER) — `test_a_dispatch_lands_a_real_row_in_the_real_trace_table`

**Defect it catches:** any emission whose call the REAL store rejects — an extra keyword, a
renamed keyword, a value the engine refuses. Today the seam is only ever pointed at a
`**fields`-swallowing double, so W30 (`traces.total` = 0 forever, #147 reproduced) is invisible.

Shape: build the server, install a request context whose `lifespan_context.write_store` is a REAL
`SurrealStore` on a throwaway DB, dispatch the synthetic probe through `mcp.call_tool`, then
`SELECT <explicit projection> FROM trace` and assert exactly one row with `tool`, `ok is True`,
`isinstance(ordinal, int)`.

```
correct reference : 1 passed in 1.31s
W30               : 1 failed — TypeError: record_trace() got an unexpected keyword argument 'request_id'
```

### MP-B (HIGH) — `test_every_registered_tool_traces_when_it_SUCCEEDS`

**Defect it catches:** any build whose success path is broken for real tools (W11). Shape:
parametrise over `_MINIMAL_ARGS`, monkeypatch `mcp._tool_manager.call_tool` to return a canned
`[TextContent(...)]` so EVERY registered tool succeeds through the production override, assert
one row with `ok is True` and the dispatched name.

```
correct reference : 16 passed in 1.32s
W11               : 15 failed, 1 passed   (the 1 = the synthetic probe, exactly as predicted)
```

### MP-C (HIGH — a pin that cannot pass) — fix `test_sequential_writes_carry_strictly_increasing_distinct_ordinals`

`zip(ordinals, ordinals[1:], strict=True)` raises `ValueError` for every non-empty list, so the
ordinal-monotonicity property is currently pinned by **nothing**, and a builder who implements
correctly is trapped against a contract it may not edit. It is RED today for the RIGHT reason
(`TypeError: record_trace() got an unexpected keyword argument 'agent'` — receipt in the RED run),
which is precisely why its author could not see it. Fix: drop `strict=True` (or compare
`ordinals == sorted(set(ordinals))`).

```
$ python -c "o=[0,1,2]; all(l>e for e,l in zip(o,o[1:],strict=True))"
ValueError: zip() argument 2 is shorter than argument 1
$ python -c "o=[0,1,2]; print(all(l>e for e,l in zip(o,o[1:])))"      → True
$ python -c "o=[0,0,1]; print(all(l>e for e,l in zip(o,o[1:])))"      → False   (still discriminates)
```

### MP-D (MEDIUM) — `test_two_dispatches_of_different_durations_record_different_latencies`

**Defect it catches:** a constant latency (survives today). Shape: dispatch the fast probe and the
slow probe in one request context; assert `slow_ms - fast_ms >= _SLOW_TOOL_SECONDS*1000*0.5`.

```
correct reference : 1 passed in 0.70s
constant-50 build : 1 failed — assert (50.0 - 50.0) >= ((0.05 * 1000) * 0.5)
```

### MP-E (MEDIUM) — `test_a_zero_argument_call_still_records_the_full_digest`

**Defect it catches:** W31 — an empty digest for the four zero-argument tools. Shape: dispatch a
no-argument probe; assert `re.fullmatch(r"[0-9a-f]{64}", served)` and `served == _expected_params_hash({})`.

```
correct reference : 1 passed in 0.65s
W31               : 1 failed
```

### MP-F (MEDIUM) — behavioural pins for the ORACLE (`_surreal_fakes.py`)

**Defect it catches:** the fake silently ceasing to mirror the real row shape. Measured: dropping
`agent`/`action`/`transport_session`/`ok` from the fake's row and freezing its ordinal at 0 leaves
`test_surreal_fakes.py + test_mcp_server.py + test_trace_telemetry.py` at **1 failed / 783 passed**.
Positive control that the mutation is real:

```
correct oracle : keys of row0 = ['action','agent','latency_ms','ok','ordinal','params_hash','tool','transport_session','ts'] · ordinals [0,1,2]
mutated oracle : keys of row0 = ['latency_ms','ordinal','params_hash','tool','ts']                                            · ordinals [0,0,0]
```

Shape (three cheap tests beside the existing `TestRecordTraceFake` pins): the four new columns
round-trip when given · they are ABSENT (`.get(...) is None`) when omitted · successive
`record_trace` calls carry distinct, increasing, 0-based ordinals.

### MP-G (MEDIUM) — widen the prose battery to the three unguarded corpses

`server.py::TraceSummary` (served by `lore_index`), the `surreal_schema.py` module header, and
`surreal.py::trace_aggregates`' cross-reference. Cheapest instrument that generalises: sweep the
`trace`-related docstrings/comments of both modules for the retired vocabulary (`six core`,
`fire-and-forget`, `no caller yet`, `later serving-layer phase`) rather than naming three
docstrings by hand — a name-list is the instrument this repo has watched lose six times.

---

## §8 P5 (oracle), blast radius, RED honesty, concurrency

- **P5 — can the fake FAIL?** For its NEW behaviour: **no** (MP-F receipts above). For its
  pre-existing behaviour: **yes** — parity, arm/recover, omitted-optionals and ordering pins all
  exist and the FK-3b parity pin reddens under M14.
- **Blast radius, re-derived (not inherited).** The author's §10 names 21 suites. My own
  derivation: **18 test files import `_surreal_fakes`**, **7 name `FakeSurrealStore` directly**,
  **6 touch `record_trace`/`recorded_traces`**. I ran every importer plus `test_mcp_server.py` and
  `test_surreal_store.py` — 20 suites — against the reference:
  `1457 passed in 127.61s (0:02:07)`. **Zero collateral from the oracle change.** The
  21-vs-20 difference is bookkeeping (the author counted `test_trace_telemetry` and
  `test_comms_schema` inside the same run); no suite is missing from either list.
- **P7 — RED honesty, reproduced on pristine production:**
  ```
  69 failed, 618 passed in 24.59s      # zero collection errors
  FAILED  test_trace_telemetry.py   × 64
  FAILED  test_comms_schema.py      ×  3      (E-S6)
  FAILED  test_surreal_schema.py    ×  1      (FK-3a)
  FAILED  test_surreal_fakes.py     ×  1      (FK-3b)
  ```
  Reason histogram: 36 × `len([]) == 0` / 33 × `assert 0 == 1` on the recorder (no seam) ·
  9 × `TypeError: record_trace() got an unexpected keyword argument 'agent'` · 5 × missing
  `DEFINE FIELD` · 2 × `'six core' is contained here` · 2 × `TracingFastMCP does not exist` ·
  the sequence/index/migration legs. **No import error, no collection error, no fixture error.**
  ⚠ One trap I hit and report as a method note: adding my own probe files to the tests directory
  reddened `test_surreal_harness.py::…test_the_harnesss_docstring_counts_are_the_DERIVED_counts`
  (the AST-derived importer count moved 36→39). That pin is working exactly as designed; the
  70th failure in my first run was MY contamination, and the clean run above excludes it.
- **Concurrency, 20 consecutive runs** of `test_eight_concurrent_writes_mint_eight_distinct_ordinals`
  on the reference: **20 passed, 0 failed** (1.56 s – 6.07 s).

---

## §9 Blind-diff against the struck adversary (read only AFTER my P1 battery), both directions

| struck finding | disposition under the r2 contract | evidence |
|---|---|---|
| MP1 `seq int` + omit-the-mint rejected | **moot + covered** — r2 rules `ordinal option<int>`; omission is pinned | W4 dies (5 pins) |
| MP2 cancellation via `finally` | **covered** | W6/W7 die |
| MP3 caller key unique across session lifetimes | **moot by architecture + covered anyway** | §3.3 + W27 |
| MP4 a non-drain comms action records identity | **covered by the generic KEY rule** (synthetic declaring + partial probes); residual R6 notes the one thing still untied | M7/M8/M9/M10 |
| MP5 `hit_count == served` under limit>pending | **translated correctly** — T2 refuses a generic hit count and the honesty pin discriminates at 0 AND at 7 | W5, W32 |
| MP6 a failed trace write is logged loudly | **covered, and strengthened** (structured dotted event + `exc_info` + names the tool) | my reference failed it on first pass |
| MP7 `token_cost`/`model` declared; index names both fields | **covered** | `_TRACE_UNCHANGED_COLUMNS`, W13 |
| **MP8 non-empty `params_hash` on a zero-arg call** | **NOT CARRIED — still open** | **W31 survives → MP-E** |
| MP9 `trace.session` semantics | **ruled** (declared-only) | M10 dies |
| MP10 collateral RED in other suites | **closed** — the FK-3 amendments landed; my satisfiability run shows no collateral | 686 passed / 1 failed |
| MP11 the S7 rung pin compares `id()` ints | **moot** (architecture gone) | — |

**Direction 2 — findings the struck adversary did NOT have** (its contract was a different
architecture, so these are genuinely new): **W30** (no seam→real-store leg), **W11** (the
success cell), **MP-C** (the unsatisfiable ordinal pin), **MP-D** (constant latency), **MP-F**
(the oracle's new behaviour), **MP-G** (three unguarded prose corpses).

---

## §10 Residuals — every one with an individual verdict (nothing dropped)

| id | residual | verdict |
|---|---|---|
| R1 | the `ok`-semantics pin's window is `[specs-60 : specs+1]` (ABOVE the assignment only) and its normalisation keeps `#`, so the ruled sentence **wrapped across two comment lines**, or placed inline beside the column entry, goes RED — while its own docstring promises "a reflow … does not go RED for a cosmetic reason" | **real fragility, low severity** (it cannot pass a wrong build; it can red a correct one). Receipt: my verbatim-but-wrapped reference. Cheap fix: strip `#` before normalising, and widen the window to the `_TRACE_FIELD_SPECS` tuple body. |
| R2 | `test_record_trace_signature_matches_real_store` pins the ORDER of keyword-only parameters, which carries no semantics | **over-specification.** A natural signature (required first) is RED for a cosmetic reason. Keep if the parity intent is exact-shape; say so in the message. |
| R3 | `test_eight_concurrent_writes…`'s comment claims it kills "an ordinal minted client-side" | **FALSE, measured**: W20 (per-process client counter) **passes that pin** (2 passed in the class); the gap/count pin catches it instead. Message-vs-assertion gap — fix the comment or the pin, and note that the gap pin's control is what makes it discriminate. |
| R4 | `test_no_raw_parameter_content_reaches_the_row` checks the fragment `"row-shaped"`, which does not occur in `_HOSTILE_BODY` | **vacuous element in a ∀-loop.** Add a control asserting each fragment IS present in the hostile input before asserting its absence from the row. |
| R5 | four author obligations mis-stated (M6, M4, M13, M19) | **corrected in §4**, with M20 supplied as the missing proof for the second vacuous guard. |
| R6 | nothing ties the harvested keys (`agent`/`session`/`action`) to the params the REAL tools declare — only synthetic probes exercise the rule | **low.** Cheap strengthening: the coverage dispatch of `lore_comms` already passes `agent="coverage-probe", action="fleet"` — assert the row carries them. |
| R7 | no pin asserts a wrong-TYPED `hit_count`/`session` is still rejected after the widening | **not a regression** (unpinned in the old world too), recorded so the next widening meets it deliberately. |
| R8 | mypy at HEAD `03b93d3` = **126 errors in 2 files** (`test_comms_tool.py` 120, `test_comms_promise_registry.py` 6) — the author reported 92 | **not telemetry.** Zero errors in any telemetry file and zero from my reference. The growth arrived with the surface wave (`7a8e44f`) + the E-S5 wording commit (`91ea5be`). Flagged for the lead, not fixed. |
| R9 | the ORACLE's docstring teaches `ok` as *"whether the tool call succeeded"* — the exact wording ESC-1 corrected | **prose corpse in the oracle**, unguarded (the `ok`-semantics pin scans only `surreal_schema`). One-line fix; fold into MP-G. |
| R10 | `record_trace`'s docstring still says the write is "a single awaitable insert" while the statement is now a `CREATE … object::extend(…)` with a store-side mint | **accurate enough**, no action; noted so the builder's docstring rewrite covers it. |
| R11 | the T7.9 deploy smoke (live before/after trace count on `:18500`) is a packet-EXIT obligation with no pytest home | **agreed and confirmed** — MP-A is its unit-level analogue and does NOT replace it. |
| R12 | `test_trace_telemetry.py` imports `_field_statement` from `test_surreal_schema` (test-module→test-module) | **fine** — it is the DRY choice over cloning, and the author disclosed it (D3). |
| R13 | **the design authority moved UNDER me, mid-run**: `git status` showed `docs/plans/v2/03b-design-rulings-r2.md` MODIFIED at close (one hunk at B3.2 — the send thread cell STRUCK, citing a "§G row / Reading A" ruling). I never wrote to it (my writable set is this report alone), so a parallel actor edited it while I graded | **not mine, and telemetry-neutral** — the single hunk is in §A/B3 (surface renders); §B T1–T8/T2.1 and §G's ESC-1/ESC-2 rows are byte-unchanged, so every ruling my reference was built from still reads as I read it. Flagged because grading against a moving authority is a real hazard for the NEXT reader of this report: my §B/§G reads are pinned to `03b93d3` + that uncommitted B3 hunk. |

---

## §11 Grading every CONTROL in the contract (P0 discipline applied to the author's instruments)

| control | can it SEE what it certifies? |
|---|---|
| `TestTheIndexFieldsParserItself` positive (`chunk_tier_file` → `('tier','file_path')`) | **YES** — a real multi-field committed index. ✔ |
| `TestTheIndexFieldsParserItself` negative (forged index NAMED for its columns) | **YES** — returns `('tool',)`, so the parser demonstrably reads FIELDS, not the name. ✔ |
| `TestTheEmissionsDependencyIsRealInProduction` positive (`embedder` in the signature) + negative (`trace_store_that_does_not_exist`) | **YES**, both directions. ✔ |
| `…_the_positive_control_the_same_call_writes_when_the_store_is_healthy` | **YES** — pairs with the failing-store leg. ✔ |
| `test_the_same_arguments_hash_identically_and_different_ones_do_not` (constant-killer leg) | **YES** — W9-class builds die. ✔ |
| `test_a_count_is_derived_from_ROWS…` burn control (`ordinals[-1] > ordinals[0]+1`) | **YES**, and it is doing double duty: it is what actually kills the client-side mint (W20). ✔ |
| `TestTheTraceDeltaMigratesADirtyStore` `INFO FOR DB` sequence control | **YES** — W22 reddens all four legs. ✔ |
| `test_no_raw_parameter_content_reaches_the_row` fragment loop | **PARTLY** — 3 of 4 fragments are real; `"row-shaped"` is absent from the fixture (R4). |
| the latency pin's implicit "constant" control | **NO** — it does not exist; the pin's comment claims it (R3-adjacent; MP-D). |
| `_TraceRecorder` as the emission's oracle | **NO for the store contract** — it accepts any keyword, which is the W30 hole (MP-A). |

---

## VERDICT: **CONTRACT INSUFFICIENT**

Four wrong builds and one oracle mutation survive the frozen contract at the correct build's own
score, and one pin cannot be satisfied by any build. The seven items in §7 are the pins that close
them; each has a written prototype and both control legs. Everything else in this contract is
strong — 40 of 44 wrong builds die, several on exactly one pin, and the identity, schema,
migration and E-S6 batteries are as discriminating as their docstrings claim.
