# REPORT-scout-11i — packet 11-i discovery scout (floor calibration, dark machinery)

brief-base v6 read

- **state:** done
- **deviations:** none to the writable set (this file only; no code, no tests, no packet/design edits).
- **decisions-needed (lead/operator):**
  1. **SIZING: 11-i measures ~0.40–0.45 wu, not ~0.25–0.30 → SPLIT.** D7's named sub-split line
     ("pool+bootstrap+gate" vs "paired-decomposition+cost-capture") is LOPSIDED (~0.35 / ~0.05);
     a better seam is proposed in §6.
  2. **The R2 "in-container one-shot verb" SHAPE is unspecified and one obvious reading violates
     11-i's own Scope OUT** (an MCP tool is a served surface). Recommendation + the in-repo
     precedent in §RAISED-3.
  3. **Design D2 contains a factual error at the mechanism it just corrected** (§RAISED-1) —
     `slug` is NOT in the scrolled payload. Recoverable, but the fix changes what the builder writes.
- **receipt pointers:** §1 survey map · §2 store seam · §3 hot-row seam · §4 reuse inventory ·
  §5 query-embed seam · §6 sizing · §RAISED-1…9.

All findings below measured **2026-07-24** against worktree `/home/ejprice/PycharmProjects/lore-pkt11i`
at base commit **`d0ee2be`** (branch `pkt11i-floor-calibration-dark`). lore's index confirmed at the
SAME ref (`lore_index()` → `git_ref d0ee2be…`, `last_sync` age 178s), so lore's graph answers are
valid for unmodified files.

**Tool honesty (base §4):** lore-first was used for definitions/spans (`lore_get_symbol`,
`lore_read`). I fell back to **grep** for exactly three classes, all sanctioned: (a) the #170
rename-exhaustiveness sweep (bare, anchor-free, §4.4); (b) non-symbol textual seams —
`testpaths`, `Containerfile` COPY lines, `_REQUIRED_GUARDS`, `_CTOR_VALUES`, marker strings;
(c) cross-cutting maps (every `embed_query` call site, every `_*_FIELD_SPECS`). Two Explore
subagents fanned out on Q2/Q3; **every load-bearing claim of theirs is re-verified at source by me
below** — I did not relay an unverified subagent claim.

---

## 1 · Q1 — The survey instrument, mapped for portability

`scripts/search_score_survey.py` (988 LOC) + `scripts/test_search_score_survey.py` (561 LOC, 50 tests).

### 1.1 Full symbol map

**PURE CORE — portable into `loremaster` essentially as-is** (no store, no network, already unit-tested):

| symbol | role |
|---|---|
| `every_nth` | deterministic every-Nth sampler. **RETIRED by D2** (the sampler-discontinuity defect). |
| `HitCapture` (frozen dc) | `fused_score, vector_cosine: float\|None, file_path, ident_text, origin` |
| `_to_hit_capture` | `Candidate` → `HitCapture` |
| `QueryCapture` (frozen dc) | `query, query_kind, hits: tuple[HitCapture,...], pre_budget_pool_size, has_verbatim_anchor` |
| `top_hit_cosine` / `max_cosine_of_response` / `fused_top_margin` / `within_query_cosine_spread` / `source_concentration` | per-response aggregations |
| `GroupCosineSummary` (frozen dc) + `summarize_cosine_group` | percentile stats per group (mean/median/p5/p95 × top-hit and max-of-response) |
| `VerdictSample` (frozen dc) | `(max_cosine, has_verbatim_anchor)` — the EXACT pair the production predicate consumes |
| `query_capture_to_verdict_sample` | `QueryCapture` → `VerdictSample \| None` |
| `CosineFloorRecommendation` (frozen dc) + `.meets_adoption_bar` | the D2 output + adoption gate |
| **`choose_cosine_floor`** | the selection rule (dominance order: max catch → min false-fire → max floor) |
| `substrate_gate_passes` | the D1 gate |
| `parse_eval_questions` | mines `loremaster/evaluation.xml`. **Lore-specific labeled data.** |

**LORE-SPECIFIC LABELED DATA — becomes "that instance's standing regression control" per R1, NOT portable:**
`NONSENSE_QUERIES` (15), `IMPLEMENTATION_VOCABULARY_QUERIES` (6, each verbatim-sourced from a
documented informant probe), `DEFAULT_EVAL_XML` → `loremaster/evaluation.xml` (35 pairs).

**IDENTITY-PINNED SEAMS (the load-bearing part — these must survive the port):**

- Three production functions are **imported and re-exported, never re-derived**
  (`scripts/search_score_survey.py` module header, S4b audit finding #1):
  `loremaster.search._cosine_absence_predicate` (as `cosine_absence_verdict_fires`) ·
  `loremaster.search._has_verbatim_identifier_anchor` · `loremaster.search._query_tokens`.
- Pinned by **object identity (`is`)** in
  `scripts/test_search_score_survey.py::TestPredicateParityWithProduction` — three tests, one per seam.
- The **bars** are module constants, deliberately not CLI defaults:
  `D2_MAX_FALSE_FIRE_RATE = 0.05` · `D2_MIN_NONSENSE_CATCH_RATE = 0.6` · `D1_MIN_MEDIAN_SPREAD = 0.05`.
- `loremaster.search._cosine_absence_predicate(best_cosine, floor, has_verbatim_anchor)` is **pure and
  takes `floor` as a parameter** — verified at source. **Therefore packet 10-d's
  `_COSINE_WEAK_MATCH_FLOOR = None` does NOT break `choose_cosine_floor`.** (Confirmed at `d0ee2be`:
  `loremaster/loremaster/search.py` has `_COSINE_WEAK_MATCH_FLOOR: float | None = None`.)

**LIVE CLIENT — replaced wholesale by in-process handles (B1):** `_make_store` (hardcoded
`DEFAULT_SURREAL_URL`), `_make_embedder` (hardcoded TEI coordinates), `sample_identifier_queries`,
`capture_query`, `survey`.

**REPORTING:** `build_markdown_report`, `_write_jsonl`, `_default_output_dir`, `build_arg_parser`, `main`.

### 1.2 C6f VERIFIED AT SOURCE (the design's claim holds — I did not take its word)

The #180 rider rests on per-hit cosine being captured **and** persisted. Both confirmed:

- **Captured for every hit:** `search_score_survey.py::_to_hit_capture` sets
  `vector_cosine=candidate.vector_cosine` for each `Candidate`; `capture_query` builds
  `hits = tuple(_to_hit_capture(c) for c in candidates)` over the FULL `k=10` (`SURVEY_K`) response.
- **Persisted per hit:** `search_score_survey.py::_write_jsonl` writes, for every `h in c.hits`,
  `{"fused_score", "vector_cosine", "file_path", "origin"}`.
- Source of the value: `loremaster/loremaster/store/surreal.py::SurrealStore._extract_vector_cosine`
  — reads the projected `vector_cosine` key; its own docstring says the projection in
  `_hybrid_statement` "always emits a float in practice, since `embedding` is a required,
  non-`option` column", the `None` return being defensive only.

**⚠ One bound the design does NOT state (see RAISED-6): `ident_text` is NOT persisted per hit.**
The jsonl carries only the QUERY-level `has_verbatim_anchor`. C6(c) ("verbatim-anchor rates per
group") is computable from the query-level flag; a **per-hit** anchor decomposition is NOT
re-derivable from the jsonl alone.

---

## 2 · Q2 — The store seam

File: `loremaster/loremaster/store/surreal_schema.py` (1585 LOC). All emitter strings quoted verbatim
from source (I re-read them; the subagent's transcription is correct).

### 2.1 The DDL emitters and the exact clause each emits

| emitter | emitted clause |
|---|---|
| `surreal_schema._define_table(name)` | `DEFINE TABLE IF NOT EXISTS {name} SCHEMAFULL` |
| `surreal_schema._define_schemaless_table(name)` | `DEFINE TABLE IF NOT EXISTS {name} SCHEMALESS` |
| `surreal_schema._define_relation_table(...)` | `DEFINE TABLE OVERWRITE {name} TYPE RELATION IN … OUT …[ ENFORCED] SCHEMAFULL` |
| `surreal_schema._define_field(table, name, type_expr, *, constraint="")` | `DEFINE FIELD OVERWRITE {name} ON {table} TYPE {type_expr}[ {constraint}]` |
| `surreal_schema._plain_index` / `._unique_index` | `DEFINE INDEX IF NOT EXISTS {name} ON {table} FIELDS …[ UNIQUE]` |
| `surreal_schema._hnsw_index` / `._fulltext_index` | `DEFINE INDEX IF NOT EXISTS …` |
| `surreal_schema._define_sequence` / `._analyzer_statement` | `DEFINE SEQUENCE\|ANALYZER IF NOT EXISTS …` |

**There is no `_define_index`** — the index DDL is four kind-specific emitters. A brief that names
`_define_index` will send a builder looking for a symbol that does not exist.

This is exactly the store reference's **§1.1 decision rule**
(`docs/reference/surrealdb-31-capabilities.md` §1.1, with §1.2 the mechanism, §1.3 why `ALTER` is a
trap, §1.5 why indexes must never take `OVERWRITE`) — **already implemented in code**, and
additionally **mechanically enforced** by the pin in §2.4. 11-i's new plain table therefore takes
`IF NOT EXISTS`, its fields `OVERWRITE`, its indexes `IF NOT EXISTS` — and the builder does not have
to remember that, because the pin fails closed.

### 2.2 The `_*_FIELD_SPECS` pattern

A module-level tuple of tuples — **no dataclass**. Two shapes: `tuple[tuple[str, str], ...]`
(`name, type_expr`) and `tuple[tuple[str, str, str], ...]` (`name, type_expr, constraint`).
Exemplar — `surreal_schema._TASK_FIELD_SPECS` (I re-read `_CHUNK_FIELD_SPECS` in full myself):

```python
("status", _CHUNK_STRING_TYPE, f"ASSERT $value IN [{_TASK_STATUS_ALLOWED}]"),
("blocked_by", "array<string>", "DEFAULT []"),
("provenance", "object FLEXIBLE", ""),
("owner", "option<string>", ""),
```

- TYPE = the `type_expr` string; **optionality = `option<...>` wrapping** (no separate flag);
  ASSERT/DEFAULT = verbatim in `constraint` (a field may carry both).
- **FLEXIBLE has TWO spellings** and this is a live dialect constraint: inside `type_expr`
  (`"object FLEXIBLE"`) normally, but in the `constraint` slot when the type is `option<...>`
  (`_AGENT_FIELD_SPECS`: `("checkpoint", "option<object>", "FLEXIBLE")`) — `FLEXIBLE` must trail
  OUTSIDE the angle brackets. **11-i's results/bars/corpus-snapshot/cost blobs are `object`s — this
  bites immediately.**
- Full list (14): `_CHUNK_`, `_MEMORY_`, `_TRACE_`, `_TASK_`, `_FINDING_`, `_AGENT_`, `_BRIEF_`,
  `_BRIEFED_`, `_MESSAGE_`, `_TO_`, `_CODE_NODE_`, `_REFERS_`, `_ANSWERS_TO_`, `_NAME_FIELD_SPECS`.
- **Not universal:** `file`, `meta`, `file_text`, `snapshot`, `snapshot_entry`, `command`,
  `finding_counter`, `brief_counter` write their `_define_field(...)` calls out longhand inside
  their own `_*_statements()`. Both shapes are legitimate; the spec-tuple is convention, not a gate.
- The derivation idiom worth copying: `CHUNK_COLUMNS` and `CHUNK_FILTER_KEYS` are **derived** from
  `_CHUNK_FIELD_SPECS`, never hand-copied — its own comment: *"a hand-copied twin that could drift"*.

### 2.3 Adding a table: **there is NO production registry** (verified)

`generate_ddl(*, dim, analyzer_name)` concatenates `_chunk_statements` … `_finding_counter_statements`
and `_STRUCTURAL_TABLES` (empty today). **Eight further slices** are separately callable and are
applied by their OWN domain class's own `ensure_ready()` on its own connection:
`generate_manifest_ddl`, `generate_memory_ddl`, `generate_task_ddl`, `generate_finding_ddl`,
`generate_agent_ddl`, `generate_brief_ddl`, `generate_message_ddl`, `generate_graph_ddl`.

The real assembly point is procedural: `loremaster/loremaster/server.py::build_app_context` —
a hand-written `construct → await X.ensure_ready() → write_stack_readied.append(X)` sequence.

**MEASURED PROOF THAT A TABLE CAN BE SILENTLY UNWIRED:** `grep -c "MessageLedger\|message_ledger"`
over `loremaster/loremaster/server.py` returns **0**. `generate_message_ddl` / `_message_statements` /
`MessageLedger` exist and are tested; nothing in the live server constructs or readies one. Whether
that is deliberate staging or a gap is the lead's call — either way it is the empirical answer to
"can a new table be silently unwired": **yes.** (RAISED-2.)

**Mechanical edit sites for a new table `floor_calibration`:**
1. `surreal_schema.py`: `FLOOR_CALIBRATION_TABLE = "…"`; state/ASSERT constants;
   `_FLOOR_CALIBRATION_FIELD_SPECS`; `_floor_calibration_statements() -> list[str]`.
2. **Either** splice into `generate_ddl()` (shared write-store connection) **or** add
   `generate_floor_calibration_ddl()` (own ledger/connection, mirroring `generate_agent_ddl`).
3. If own ledger: a new class with `ensure_ready()` calling `execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", …)`.
4. `server.py::build_app_context`: construct, `await …ensure_ready()`, append to `write_stack_readied`.
5. **Test-side, REQUIRED if step 2 chose a new top-level generator:** add it to
   `loremaster/tests/test_surreal_schema.py::TestFieldDdlConvergesOnAnExistingStore._generated_ddl()`
   — its own docstring: *"a new generator outside this dict is the registration gap this whole class
   exists to close."* Miss this and the #107 guard pin never inspects the new table at all.
6. Convention (not enforced): `EXPECTED_TABLES` in the same file if it rides `generate_ddl()`.

### 2.4 `ensure_ready()` rides `execute_transaction` — CONFIRMED

`loremaster/loremaster/store/surreal.py::SurrealStore.ensure_ready`:
`await self._ensure_connection()` → `ddl = generate_ddl(...)` →
`await execute_transaction(f"BEGIN;\n{ddl}COMMIT;\n", {}, acquire=self._ensure_connection,
drop=self._drop_connection, url=self._url)`. The whole DDL is ONE batched call, and
`execute_transaction` walks `response["result"]` extracting every `ERR` entry (`_failed_statements`
→ `_rollback_verdict`), naming the offending 1-based statement index. **Never a bare `query()`** —
which is the `statement[0]`-only validation gotcha the store reference documents. Nine domain twins
follow the identical three-step shape.

### 2.5 The structural pin that already covers a new table

`loremaster/tests/test_surreal_schema.py::TestFieldDdlConvergesOnAnExistingStore.test_every_define_statement_carries_the_guard_its_kind_requires`
regex-parses **every `DEFINE`** out of **every generator in `_generated_ddl()`** and asserts
`_REQUIRED_GUARDS = {FIELD: OVERWRITE, TABLE: IF NOT EXISTS, TABLE (RELATION): OVERWRITE,
INDEX: IF NOT EXISTS, ANALYZER: IF NOT EXISTS, SEQUENCE: IF NOT EXISTS}`. It **fails closed** on any
unclassifiable `DEFINE` and carries its own positive control (`count > 0` per kind) — a good pin.
`EXPECTED_TABLES` (live-server) is a **subset** (`<=`) check over `generate_ddl()`'s 11 tables only.

---

## 3 · Q3 — The hot-row seam

File: `loremaster/loremaster/store/_txn.py`. Signature re-read by me at source:

```python
async def retry_on_conflict[T](
    attempt: Callable[[], Awaitable[T]],
    *, deadline_seconds: float | None = None, label: str | None = None, url: str | None = None,
) -> T:
```

- Retries **only** `RetryableConflictSignal`; anything else propagates untouched with ZERO retries
  (at-most-once: a transport fault may already have committed).
- Give-up: `attempts >= _TXN_CONFLICT_ATTEMPT_CEILING (64)` **OR** (`elapsed >= deadline` **AND**
  `attempts >= _MAX_TXN_CONFLICT_ATTEMPTS (5)`) — the deadline can never veto the attempt floor.
  `deadline_seconds=None` resolves `_TXN_CONFLICT_DEFAULT_DEADLINE_SECONDS (2.0)` **at call time**,
  never frozen into a default argument (that freeze is what made #102's retry branch untestable).
- Jitter: `_txn_conflict_backoff_seconds(attempts)` — **fresh full jitter every attempt**.
- Exhaustion: logs `store.retry.exhausted` and raises `TxnContentionExhaustedError` (⊂ `SurrealStoreError`).

**Classification is SHARED, not hand-rolled.** One authority: `_txn._RETRYABLE_CONFLICT_MARKER`,
consulted through exactly one function `_txn._is_retryable_conflict_text`, wrapped per path by
`_txn.is_retryable_conflict_error` (single-statement) and `_txn._rollback_verdict` (transactional).
`RetryableConflictSignal` deliberately does NOT subclass `SurrealStoreError`. A repo law pin —
`loremaster/tests/test_retry_seam.py::TestTheAttemptFloorOutlivesItsBriefsConsumer.test_no_production_module_holds_the_engines_conflict_marker`
— fails if any production module outside `_txn.py` names the marker.

**Sibling seams:** `_txn.execute_transaction` (transactional; the ONE documented caller that passes
no `label`, keeping its own attribution via `_log_rollback`) · `_txn.run_query` (the single-statement
attempt body every `_query` delegates to) · `_txn.bootstrap_session` (three `retry_on_conflict` calls
sharing one wall-clock budget).

### 3.1 The two counter-mint precedents — and they differ

| | `findings.py` | `briefs.py` |
|---|---|---|
| symbol | `FindingLedger._report_fragment` (bump) → `FindingLedger._apply` → `execute_transaction` | `BriefLedger._mint_version` → `self._query` → `run_query` → `retry_on_conflict` |
| statement | `LET $… = (UPSERT type::record('finding_counter','…') SET next += 1 RETURN AFTER)[0].next` | `UPSERT type::record('brief_counter', $name) SET next = (next ?? 0) + 1 RETURN AFTER` |
| placement | **inside the same txn as the row CREATE** | **its own statement/txn, before the CREATE** |
| why | finding id is `uuid4().hex` — independent of the number | brief id is `uuid5(name, version)` — Python must know the version first |
| compensation | none needed | `BriefLedger._release_version` (guarded `WHERE next = $version`) on a failed CREATE |

**Both matter for 11-i**, which has TWO hot rows: the head pointer per scope (findings shape works if
the row id doesn't depend on the number) and the single-flight lease. `_mint_version`'s own docstring
records that it USED to hand-roll "a private 4-attempt budget, a linear backoff, a 4-slot jitter
table" — the #102 defect. **Neither file contains the marker string** (grepped: zero hits).

### 3.2 The single-flight LEASE precedent is a THIRD shape, and it is the dangerous one

The in-repo conditional-claim (CAS) precedent is `loremaster/loremaster/scout.py::CommandSubscriber._mark`
— `UPDATE … WHERE status = 'pending' RETURN BEFORE`; an **empty** result is a LOST RACE with a
defined meaning and **must never be retried**, while a retryable conflict IS retried transparently.
That is exactly the semantics 11-i's lease needs. **But `scout.py` routes through the module-level
function `scout._scout_query`, not a `_query`-owning class** — the eleventh-copy shape CLAUDE.md
records. See RAISED-4 for what that costs.

### 3.3 The runtime guard (#136's fix) and what a NEW caller must do

- **Guard:** `loremaster/tests/_sdk_guard.py` — `install(monkeypatch, *, production_root=None,
  witness=None) -> GuardReport`; `GuardReport(escapes, observed, armed, watched_root, intercepted)`
  + `.require_observations(flow)`; `SdkEscape`; `GuardCannotSubstantiate`;
  `SAFE_CONNECTION_METHODS = frozenset({"signin","close"})`; `SDK_CONNECTION_CLASSES`; `artifact_root()`.
- **Armed by an AUTOUSE fixture** — `loremaster/tests/conftest.py::_no_sdk_call_escapes_the_retry_driver`
  (verified at source): every test in the suite is watched. It monkeypatches every public coroutine
  method on the three real SDK connection classes with a plain `def` wrapper (stack-walk must happen
  at CALL time, or `asyncio.gather(connection.query(...))` is invisible) and records an `SdkEscape`
  when a production frame calls the SDK with no `retry_on_conflict.__code__` frame above it.
- **"Refuses to certify what it cannot see" — two distinct refusals, both raising
  `GuardCannotSubstantiate`:** (1) at ARM time, if the `witness` does not actually execute from under
  `production_root` (the literal #136 bug: out-of-tree, the guard watched a directory nothing ran
  from and every "no escapes" assertion passed vacuously); (2) at VERDICT time,
  `GuardReport.require_observations(flow)` raises when `observed` is empty — zero observations is
  BLIND, not CLEAN.

**What a new hot-row caller must do to be covered:**

- **Nothing to register in the guard itself** (autouse + wraps every method), and nothing to add to
  `SAFE_CONNECTION_METHODS` (an `UPSERT` rides `query`, already watched).
- **Nothing to register in the AST lint** —
  `test_retry_seam.py::TestNoProductionCodeCallsTheSdkOutsideTheSeam.test_every_sdk_call_site_is_run_by_the_retry_seam`
  `rglob`s the whole package.
- **Auto-discovery, conditional on shape:** `test_retry_seam.py::_discover_query_seams()` (re-read by
  me) AST-walks every package file for a class owning `async def _query` and builds `_QUERY_SEAMS`.
  **Measured at `d0ee2be`: 11 seams are discovered** — `AgentRegistry, BriefLedger, DiffEngine,
  FindingLedger, SurrealCodeGraph, SnapshotStamper, SurrealManifest, LocalMemoryBackend,
  MessageLedger, SurrealStore, TaskLedger`. A new class in that idiom is picked up **for free** into
  the mutation proofs.
  **⚠ Hard constraint nobody has written down:** `_construct(seam)` builds each discovered class from
  `_CTOR_VALUES` — a fixed dict of `url, namespace, database, user, password, dim, store, manifest,
  ledger, embedder, existing_chunks, tier_roots, project_roots, project_root`. **A new ledger with a
  REQUIRED ctor parameter outside that dict breaks the auto-discovery pins the day it is written.**
  Keep new required params inside that vocabulary, or the builder must extend `_CTOR_VALUES`.
- **THE ONE REAL OBLIGATION:** `test_retry_seam.py::TestNoSdkCallEscapesTheDriverAtRuntime.test_every_production_sdk_call_site_was_OBSERVED_by_the_guard`
  cross-checks the AST's full call-site list against what the guard actually OBSERVED, and it drives
  its flows from a hand-written list (the `_discover_query_seams()` loop, `execute_transaction`, plus
  scout's bespoke bootstrap/drain/CAS/live-subscribe). **A bespoke shape — e.g. a module-level
  `_floor_query` mirroring `scout._scout_query` — must be added to that test's drive list by hand,
  or its call site lands in `unobserved` and the pin fails naming the site.** This is the
  coverage-as-a-checked-variable clause of CLAUDE.md's instrument lesson.

### 3.4 Mutation proof of sharing — EXISTS

`test_retry_seam.py::TestDetectionFollowsTheOneSharedMarker` monkeypatches
`_txn._RETRYABLE_CONFLICT_MARKER` and asserts **both directions**
(`test_the_new_marker_starts_being_a_conflict` / `test_the_old_text_stops_being_a_conflict`),
parametrized over all 11 `_QUERY_SEAMS`, plus
`test_the_transactional_caller_follows_the_marker_too` for `execute_transaction`. A private copy
passes at most one direction. A second proof targets the shared jitter for the brief mint —
`TestBriefMintSharesTheDriver.test_the_mint_backs_off_through_the_SHARED_jitter`, **with a positive
control** (`test_the_shared_jitter_recorder_can_actually_see_a_draw`). 11-i's head mint and lease
should land inside these same parametrized proofs by construction.

---

## 4 · Q4 — The reuse-vs-clone inventory

### 4.1 `calibration/engine.py` — B5's three reuse claims, graded individually

| B5 claim | verdict at source |
|---|---|
| (a) findings-seam Protocol | ✅ **REUSABLE AS-IS.** `calibration.engine.FindingsPort` (`@runtime_checkable Protocol`): `async has_open_drift_finding(area) -> bool` · `async report_drift_finding(*, subject, body, area, category, kind, created_by) -> None`. The concrete adapter `server._CalibrationFindingsAdapter` wraps `FindingLedger`, treating `open` OR `acknowledged` as live. 11-i needs only its own `AREA`/`CATEGORY`/`KIND`/`CREATED_BY` constants (cf. `CALIBRATION_AREA="token_calibration"`, `DRIFT_CATEGORY="api_drift"`, `DRIFT_KIND="drift"`, `DRIFT_CREATED_BY="calibration-engine"`). **The adapter itself is reusable as-is** — nothing in it is token-ratio-specific. |
| (b) `from_engine_status` construction seam | ✅ **REUSABLE AS A PATTERN, and it is a genuinely good one.** `server.CalibrationStatus.from_engine_status(payload)` (a `@classmethod` on an `extra="forbid"` pydantic model) selects only declared fields and **logs unknown engine keys loudly** rather than bricking the render — audit finding 4/F3. Note this is a *pattern*, not a shared function; ONE IMPLEMENTATION is satisfied because the POLICY (which fields) differs per model. Contrast `server.CosineFloorStatus`, which deliberately does NOT use it. |
| (c) "the closed-distinct-state discipline **with the exact-set pin**" | ❌ **THE EXACT-SET PIN DOES NOT EXIST. There is nothing to reuse.** See RAISED-5. |

**Engine state set at source** (`calibration/engine.py`): five module constants —
`STATE_CACHED="cached"`, `STATE_MEASURED="measured"`, `STATE_DRIFT_ADOPTED="drift_adopted"`,
`STATE_CACHED_RETRYING="cached_retrying"`, `STATE_INTEGRITY_FAILED="integrity_failed"`. **No tuple,
no frozenset, no enum.**

**Wholesale-reuse rejection CONFIRMED correct at source.** `CalibrationEngine._apply_measurement`
compares a token-weighted live total against a SHIPPED baseline corpus and scales a committed
constant; `_count_live_total`, `_load_cache`/`_write_cache`, `DRIFT_THRESHOLD=0.01`,
`BACKOFF_START_S/CAP_S` are all token-ratio mechanics. B5's "sibling engine, shared seams" is right.
**What IS structurally reusable is the LIFECYCLE**: `start()` (idempotent, `asyncio.create_task`,
boot never blocks) / `stop()` (cancel + suppress `CancelledError`) / `wait_until_settled()` /
`status()` under `self._lock`. That is B5's named "probe-task lifecycle" candidate — and per B5's own
instruction it is an **ESCALATION, not a copy**. My read: extract a small shared task-lifecycle
helper both engines call. (RAISED-8.)

### 4.2 `records.point_id` — signature and semantics

`loremaster/loremaster/index/records.py::point_id(slug, tier, file_path, chunk_type, identity,
sub_ordinal, key_version=KEY_VERSION) -> str`, returning
`str(uuid5(NAMESPACE_URL, "slug:tier:file_path:chunk_type:identity:sub_ordinal:key_version"))`.
`KEY_VERSION = 2`. Deterministic across processes and hosts; uuid5 output is uniform → **unbiased
hash-stable sampling, exactly as D2 argues.** Reusable as-is *if* the caller can supply `slug` — see
RAISED-1.

### 4.3 `records.sha512_hex` — signature and semantics

`loremaster/loremaster/index/records.py::sha512_hex(data: bytes | str) -> str` — 128-char lowercase
hex; a `str` is hashed as UTF-8 so the str and bytes paths agree. **Reusable as-is** for D4's
surviving-probe test and D5's cache key (both hash probe TEXT in hand).

### 4.4 `SurrealStore.scroll` — D2's claim, verified and PARTLY FALSIFIED

`loremaster/loremaster/store/surreal.py::SurrealStore.scroll(filters: dict[str,str], limit: int) ->
list[dict[str, Any]]`. Statement (read at source):

```
SELECT * OMIT embedding FROM chunk [WHERE …] ORDER BY id LIMIT $limit
```

- ✅ **`SELECT * OMIT embedding` — CONFIRMED**, exactly as D2 says. Deterministic ascending
  record-id order; `limit` is a REQUIRED bound; filter keys validated against `CHUNK_FILTER_KEYS`
  (SurrealQL-injection defense) → **a scroll can raise `SurrealStoreError` on a bad key.**
- ❌ **"every `point_id` input is present in the scrolled payload" — FALSE.** `_CHUNK_FIELD_SPECS`
  (read in full) is: `tier, file_path, chunk_type, identity, sub_ordinal, content_hash, mtime_ns,
  line_start, line_end, source_text, ident_text, llm_summary, metadata, embedding`. **`slug` is NOT a
  chunk column** (it is `LoreConfig.slug`, driving namespace/database naming). `key_version` is a
  code constant with a default. → RAISED-1.
- ✅ **But the point_id is already ON the row.** `SurrealStore.upsert` writes
  `UPSERT type::record('chunk', $id) CONTENT $content` with `{"id": record.point_id, …}`, and
  `SurrealStore._normalize_row` (which only spreads/removes `metadata`) leaves `id` intact. So the
  scrolled row carries its own `point_id` as a `RecordID`; the in-repo helper for the bare form is
  `SurrealStore._bare_id` (a private `@staticmethod` — reachability is the builder's problem).

### 4.5 #170 — the design's ⚠-marked self-correction is CORRECT

Bare, anchor-free grep for `embedding_text_sha512` across `*.py`/`*.md`/`*.yaml` (rename-exhaustiveness
fallback, said out loud). **The load-bearing, time-stable half: ZERO hits in any `.py` file** —
`grep -r "embedding_text_sha512" --include="*.py" . | wc -l` → `0`, re-derived 2026-07-24.
The doc half was **12 hits across 6 files at sweep time** — `docs/design/2026-07-24-floor-calibration.md`
(1), `docs/design/2026-07-22-embedding-schema-reconciliation.md` (6),
`docs/plans/v2/11a-…` (1), `docs/plans/v2/11b-…` (1), `docs/plans/v2/24-odoo-scale-certification.md` (1),
`docs/plans/v2/receipts/2026-07-24-packet10/REPORT-fable-design-pkt10.md` (2).
⚠ **The doc count is NOT stable and must be re-derived, never inherited** — a re-run minutes later
returned 15, because agent reports accrete at the repo root (this report added 1; a sibling
`REPORT-fable-design-11i.md` appeared with 2). Cite the `.py` count, not the doc count.
Per CLAUDE.md's "all remaining hits are X" ban: every hit is individually a DOC/DESIGN-PROSE mention
of an unbuilt field — none is a code reference, none is a test assertion.
`Chunk.embedding_text` (the unhashed text) does exist; no persisted hash of it does.
**#170 is open; the field does not exist; D2's dissolution of the 11b dependency stands.**

---

## 5 · Q5 — The query-embed seam

**The seam is `loresigil.base.Embedder.embed_query(text) -> list[float]`.**

- **Production search path:** `loremaster/loremaster/search.py::SearchPipeline.search` (the
  `hybrid_search` step) does `vector = await self._embedder.embed_query(query)` then
  `await self._store.hybrid_search(query_vector=vector, query_text=query, k=k, filters=…)`.
- **Survey script:** `search_score_survey.py::capture_query` does
  `vector = await embedder.embed_query(query)` then
  `store.hybrid_search(query_vector=vector, query_text=query, k=SURVEY_K)`.
  **→ SAME method, same call shape.** (`SURVEY_K=10` vs production default `k=8` — a difference in
  the parameter, not the seam.)
- **Reachable from an `AppContext`-owned task: YES, directly.**
  `server.AppContext.__init__` stores `self.embedder = embedder` (a **public** attribute), and
  `build_app_context` passes that same object into `SearchPipeline(store=write_store,
  embedder=embedder, …)`. So an AppContext-owned task has the **identical object** the search path
  uses, plus `write_store`. B1's claim — *"everything the runner needs is already in-process: the
  store handle, the query-embed seam the search path uses, the production predicate"* — is
  **VERIFIED at source on all three counts.**
- **⚠ But the survey's embedder is NOT constructed by the production seam.** Production builds it via
  `loremaster/loremaster/embedding.py::make_embedder_from_config` → `to_loresigil_config` →
  `loresigil.factory.make_embedder`, and `to_loresigil_config` does non-obvious work (routes
  `config.dim` onto BOTH `dim` and `output_dimension` so a non-TEI backend cannot silently inherit a
  factory default). The survey hand-rolls `_make_embedder()` from hardcoded constants
  (`DEFAULT_TEI_BASE_URL`, `DEFAULT_TEI_MODEL`, `DEFAULT_EMBEDDING_DIM=2048`,
  `DEFAULT_TEI_QUERY_PROMPT_NAME="query"`). → RAISED-7.
- **Implications for D5/E5:** an in-process runner sharing `AppContext.embedder` inherits whatever
  batching/caching that instance has, so D5's probe-embed cache and E4's "cache as determinism
  instrument" both key on **this one object** — which is also the reason a cache placed here is
  shared with live search traffic. Worth a deliberate decision (RAISED-9).

---

## 6 · MEASURED SIZING — 11-i is ~0.40–0.45 wu · **SPLIT**

Reference points measured at `d0ee2be`: `calibration/engine.py` = **660** prod LOC against
**910 + 346** test LOC — and that engine serves ONE scalar, runs ONE probe kind, and has 5 states.
11-i's engine has 8 states, an interval, a bootstrap over the whole selection procedure, a stratified
sampler, two probe legs, a paired decomposition, a store table with a head mint and a lease, a cost
capture, a CLI verb, AND a ~450-LOC core port. `store/_txn.py` = 1388, `surreal_schema.py` = 1585,
`findings.py` = `briefs.py` = 1273 each.

| # | work item | new / port | est. wu | rationale |
|---|---|---|---|---|
| 1 | Schema slice: table + ~20 fields (interval, N, B, method, bars, results, corpus snapshot, cost, trigger, scope, paired stats) + indexes + generator | new | 0.03 | mechanical; `_REQUIRED_GUARDS` covers it; `object FLEXIBLE` spelling trap (§2.2) |
| 2 | `FloorCalibration` ledger: `_query`, `ensure_ready`, append row, **head mint** + **single-flight lease** via `retry_on_conflict`, read-adopted; `build_app_context` wiring | new | 0.06 | TWO hot rows, TWO different precedents (§3.1/§3.2); lease is a CAS whose empty result must NOT retry |
| 3 | Port the pure core into `loremaster` + **re-home 50 tests into `loremaster/tests/`** + carry the 3 identity pins | port | 0.04 | the code is written and tested — but the tests are **not in the gate** (RAISED-3a) |
| 4 | Hash-stable pool sampling (D2), keyed on the row's own point_id | new | 0.02 | small once RAISED-1 is settled |
| 5 | **Self-supervised answered probes** — docstring/heading-derived, deterministic, per-tier stratified, skips counted | new | 0.06 | the genuinely NEW instrument; no prior art in tree; per-chunk-type derivation rules + skip accounting |
| 6 | Hold-out absent leg (source-file exclusion, k′ > k) | new | 0.02 | one filter over the same calls, but a new `hybrid_search` shape |
| 7 | Bootstrap interval machinery (D1) — B≥1000, resamples answered ∪ absent JOINTLY and re-runs the whole selection procedure per resample | new | 0.05 | arithmetic-heavy; needs its own determinism + a discriminating fixture (a 1-sample resample makes `len()≡sum()`) |
| 8 | N-noise curve + ≥98% decision-agreement stability gate (D2) | new | 0.04 | subsample ladder + the pre-registered gate as code |
| 9 | Paired decomposition (D4) — surviving-probe subset by point_id AND unchanged probe-text sha | new | 0.02 | reuses `sha512_hex` |
| 10 | Per-run cost capture (D5) | new | 0.01 | counters + wall clock into the row |
| 11 | **Determinism control + its mutation proof (E5, must-prove)** | new | 0.03 | two-leg outcome (bit-identical vs within-CI) must BOTH be expressible and the leg recorded |
| 12 | R2 one-shot verb + the C6 (a)–(f) evidence package | new | 0.06 | six sub-deliverables incl. per-group jsonl, anchor rates, side-by-side probe texts, typed provenance render, #180 decomposition; shape unsettled (RAISED-3) |
| 13 | 8-state closed set + **an exact-set pin that must be BUILT** + render model via `from_engine_status` | new | 0.03 | B5 assumed this existed to reuse; it does not (RAISED-5) |
| | **TOTAL** | | **≈ 0.42** | |

**Why higher than D7's 0.25–0.30:** three costs the design did not price — (a) the ported core's
tests are outside the gate and must be re-homed, not just moved (RAISED-3a); (b) the exact-set state
pin B5 names as reusable does not exist (RAISED-5); (c) C6's evidence package is six deliverables,
not one report. Items 5, 7, 8 are also the "arithmetic-heavy" ones D7 flagged, and I price them
higher than "plumbing-light" implies because each needs a *discriminating* fixture, not just code.

### Evaluating D7's named sub-split line

D7: *"the sub-split line is 'pool+bootstrap+gate' vs 'paired-decomposition+cost-capture'."*
Mapping my table: A = items 1,2,3,4,5,6,7,8,11,13 ≈ **0.36**; B = items 9,10 ≈ **0.03** (+12 if it
lands there). **That is not a split — it is 0.36 with a 0.03 offcut**, and it leaves R2/B7.5
unassigned, which is the half the packet's own Exit calls a HANDOFF that two downstream decisions
block on (the F3 consult and #180's fix choice).

### Recommendation to the lead (a recommendation, not a decision)

**Split at the STORE/RUNNER seam instead, i.e. B7.1 vs B7.2+B7.5:**

- **11-i-a "store + engine skeleton"** — items 1, 2, 13 (+11's harness) ≈ **0.13**. Independently
  landable and auditable with **zero measurement**: a table, a ledger, two hot rows inside the
  existing mutation proofs, the state set + its new exact-set pin, the render model. Nothing served
  changes. This is the half with all the CONCURRENCY risk and none of the arithmetic risk — exactly
  the shape a cold audit grades well.
- **11-i-b "runner + R2"** — items 3–12 ≈ **0.29**. All the arithmetic, the probes, the bootstrap,
  the gate, the determinism pin, and the R2 handoff. Lands against an already-audited store.

If the lead prefers to honour D7's literal line, my read is it needs re-drawing anyway to place
item 12 (R2) — and once R2 moves, the line is effectively the one proposed above.

---

## 7 · RAISED ITEMS (nothing here is declared out of scope — the lead/operator decides)

**RAISED-1 · Design D2 is factually wrong at the mechanism it just corrected (MEDIUM, changes what the builder writes).**
D2 says *"Every input is in the scrolled payload (`SurrealStore.scroll` is `SELECT * OMIT embedding` —
verified), so membership is computed at measurement time by calling the existing function."* The
`OMIT embedding` half is TRUE (§4.4). The "every input" half is **FALSE: `slug` is not a chunk
column** (`_CHUNK_FIELD_SPECS`, read in full). A builder taking D2 literally will look for a `slug`
key in the scrolled row and not find one. Two readings, both producing different code:
*(i)* supply `slug` from `LoreConfig.slug` in-process and call `point_id(...)` as D2 intends —
works, but re-derives a value the row already carries, and a future key-scheme change silently
desynchronises the sampler from the stored ids;
*(ii)* **read the point_id straight off the scrolled row's `id`** — `SurrealStore.upsert` writes
`UPSERT type::record('chunk', $id)` with `id = record.point_id`, and `_normalize_row` preserves `id`.
**I would pick (ii)**: it cannot drift from the stored key, needs no config, and honours ONE
IMPLEMENTATION better than re-deriving. Caveat for (ii): the row's `id` arrives as a `RecordID`, and
the bare-form helper `SurrealStore._bare_id` is a private staticmethod — the builder needs a
sanctioned way to reach it (promote it, or add a public accessor). Escalating rather than picking
silently, per base §2.

**RAISED-2 · `MessageLedger` has full DDL, a ledger class, and ZERO production wiring (MEDIUM, pre-existing, outside 11-i).**
`grep -c "MessageLedger\|message_ledger" loremaster/loremaster/server.py` → **0** at `d0ee2be`.
`generate_message_ddl` / `_message_statements` / `MessageLedger` exist and are tested (it is one of
the 11 discovered `_QUERY_SEAMS`). Either deliberate staging for a later packet or a wiring gap.
Not 11-i's to fix — but it is the measured proof that this repo has **no registry preventing a
silently-unwired table**, which is precisely the risk 11-i incurs. Flagging per scope law.

**RAISED-3 · The R2 "in-container one-shot verb" has no specified shape, and the obvious reading breaks 11-i's own Scope OUT (HIGH — needs a ruling before the contract).**
The packet says "an in-container one-shot verb" and Scope OUT says "**Any serving change
whatsoever**". Measured constraints:
- **An MCP tool is a served surface.** `loremaster/tests/test_mcp_server.py::TestToolRegistration`
  uses `_EXPECTED_TOOLS <= names` (a SUBSET pin, so a new tool does not trip it) — but
  `test_instructions_names_every_tool` iterates `_ALL_BUILTIN_TOOL_NAMES` and requires the
  **instructions** to name every builtin tool. So: add the tool to that set → the instructions
  change → **a served byte changes**, violating Scope OUT. Do NOT add it → the tool ships untaught,
  which the Trust Doctrine's "agents learn the contract FROM what is served" reads as a defect.
  Either branch is bad. **An MCP tool is the wrong shape for 11-i.**
- **The right shape exists in-repo:** `loremaster/loremaster/index/__main__.py` + `index/cli.py` —
  `python -m loremaster.index --config lore.yaml [--tier T]`, described in its own docstring as the
  module-invocation entry point "in CI/deploy". A `python -m loremaster.<floor_module>` one-shot is
  in-container, serves nothing, and needs no instructions change.
- **(3a) AND: `scripts/` IS NOT IN THE IMAGE.** `Containerfile` COPYs `pyproject.toml`, `uv.lock`,
  `lorescribe/`, `loresigil/`, `loremaster/` — **not `scripts/`**. So `search_score_survey.py`
  cannot run in-container at all. This corroborates B7.5/#177 ("dev harness only") and makes the
  port to `loremaster/` a hard requirement for R2, not a preference.

**RAISED-4 · `scripts/test_search_score_survey.py` — 50 tests, INCLUDING the three production-identity pins — DO NOT RUN in the standard gate (HIGH).**
Measured: `pyproject.toml [tool.pytest.ini_options] testpaths = ["lorescribe/tests",
"loresigil/tests", "loremaster/tests"]`. `uv run pytest --collect-only -q` → **6552 tests collected,
of which `grep -c test_search_score_survey` = 0**. Named explicitly, the file collects **50 tests**.
So `TestPredicateParityWithProduction` — the `is`-identity pins that are the ONLY thing stopping the
survey's predicate from drifting from production's — has never run in any routine gate, and neither
has the `choose_cosine_floor` dominance-rule suite that produced 0.50649. **The prior art's guard
suite is invisible to CI.** 11-i's port must land these tests under `loremaster/tests/` (priced as
item 3). Recommend the lead also decide whether the `scripts/` tests get a `testpaths` entry in the
meantime — that is a change outside my writable set, so it is a flag, not an edit.

**RAISED-5 · B5's reusable "exact-set pin" for the closed state set DOES NOT EXIST (MEDIUM, sizing + a real latent defect).**
B5 lists as shared: *"(c) the closed-distinct-state discipline (#4's lesson) **with the exact-set
pin**."* Measured: the calibration states are five bare module constants with **no tuple/frozenset/enum**.
The only tests are
`loremaster/tests/test_calibration_engine.py::TestModuleContract.test_state_string_constants`, which
asserts **four** string values individually — **`STATE_INTEGRITY_FAILED` is absent from it** (it is
exercised elsewhere, at `test_calibration_engine.py` line ~488, but not pinned in the contract test).
And `loremaster/tests/test_mcp_server.py::_CALIBRATION_STATES` is a **hand-copied 5-tuple used only
as a `@pytest.mark.parametrize` source** — nothing asserts it equals the engine's actual constant
set. That is exactly the "hand-copied twin that could drift" the `_CHUNK_FIELD_SPECS` comment warns
against, and exactly the shape of finding #4. **Consequences:** (a) 11-i must BUILD its 8-state
exact-set pin, not reuse one (priced in item 13); (b) the calibration engine's own state set is
currently unpinned as a SET — a sixth state could be added and nothing would notice. (b) is
pre-existing and outside 11-i; raising it per scope law, lead's call whether to fold a fix in.

**RAISED-6 · C6f is computable, but `ident_text` is NOT persisted per hit (LOW, bounds the #180 rider).**
`_write_jsonl` persists per hit only `fused_score, vector_cosine, file_path, origin`. The verbatim
anchor is persisted **per QUERY** (`has_verbatim_anchor`). Since the production predicate is
`max_cosine < floor AND not has_verbatim_anchor` (query-level), the over-flag decomposition C6f
promises **is** computable — my verification stands. But C6(c) "verbatim-anchor rates per group"
is only available at query granularity, and any future **per-hit** anchor analysis is not
re-derivable from a stored run. Cheap fix while porting: persist `ident_text` per hit. Flagging
rather than assuming the design intended query-granularity.

**RAISED-7 · The survey's embedder is NOT built by the production config seam (LOW-MEDIUM, a real drift risk being retired anyway).**
`search_score_survey.py::_make_embedder` constructs `loresigil.factory.EmbeddingConfig` directly from
hardcoded constants, bypassing `loremaster/loremaster/embedding.py::to_loresigil_config` — which
exists precisely so `config.dim` reaches BOTH `dim` and `output_dimension` and no factory default
leaks in. Two divergence vectors today: (a) hardcoded TEI coordinates vs `lore.yaml`; (b) the
`output_dimension` routing. The 11-i port to in-process handles **retires this by construction** —
worth saying in the contract so nobody "helpfully" ports `_make_embedder` along with the core.
(Same class as RAISED-8 below: hardcoded coordinates in that script are also finding #177's
production-URL landmine, `DEFAULT_SURREAL_URL = "ws://127.0.0.1:18500/rpc"` — confirmed at source,
and I did NOT run the script.)

**RAISED-8 · The probe-task lifecycle is a genuine shared-policy candidate → ESCALATION, per B5's own instruction (MEDIUM, design decision).**
`CalibrationEngine.start/stop/wait_until_settled/status` is a complete, correct
AppContext-owned-background-task lifecycle (idempotent start, clean cancel with `CancelledError`
suppression, lock-guarded status snapshot). 11-i needs the identical POLICY. Per ONE IMPLEMENTATION
and B5's explicit *"extract a helper both engines call — escalate, never copy"*, this should be a
decision made BEFORE the builder starts, not discovered mid-build. I recommend extracting it; the
operator/lead owns whether that extraction lands in 11-i or is deferred with a named decision point.

**RAISED-9 · Where D5's probe-embed cache lives is a shared-object decision nobody has made (LOW-MEDIUM, forward-looking).**
D5(i)/E4 promote a probe-embedding cache keyed on (probe-text sha, embedder fingerprint), and E4
records it as ALSO the determinism instrument for E5. Because `AppContext.embedder` is the **same
object** the live search path uses (§5), a cache installed on that object is shared with live query
traffic — which may be desirable (free query-cache) or undesirable (a calibration run warming/poisoning
serving behaviour, and a cross-surface staleness question the Trust Doctrine would want rendered).
The cache is deferred out of 11-i by D5's YAGNI clause, so this is not a blocker — but the
**placement** should be ruled before 11-ii builds it, and 11-i's determinism receipts (E5) may be
read as evidence about it.

---

## 8 · Things I checked that are FINE (recorded so the next agent need not re-derive)

- `_cosine_absence_predicate` takes `floor` as a parameter → 10-d's `None` disarm does not affect
  `choose_cosine_floor` or any measurement path.
- `SurrealStore.scroll` orders deterministically (`ORDER BY id`) and bounds mandatorily — safe for a
  reproducible pool walk; note it validates filter keys and can raise on a bad key.
- The `#107` DDL decision rule is not merely documented, it is **mechanically enforced**
  (`_REQUIRED_GUARDS`, fail-closed, with a positive control). 11-i's builder cannot get the clause
  wrong silently.
- The retry driver's mutation proofs are parametrized over auto-discovered seams, so a
  conventionally-shaped new ledger gets sharing-by-mutation **for free** — subject to the
  `_CTOR_VALUES` constraint in §3.3.
- `server._CalibrationFindingsAdapter` is domain-agnostic and reusable as-is.
</content>
