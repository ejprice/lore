# REPORT-recon-pkt03 — structural map for packet 03 (comms message graph)

brief-base v4 read

- **state**: done
- **deviations**: none — read-only run, no file outside this report touched.
- **decisions-needed** (four; §G carries all eight flags):
  1. **Edge-guard sequencing.** The dangling-edge hazard (#105) is unguarded and its guard is scheduled for **packet 04** — one packet *after* packet 03's `to` fan-out creates the exposure. §C.4.
  2. **Where the new renders live.** A render in `messages.py` rather than `server.py` silently escapes **three of the five** render scanners; no registration path exists (the path is a bare string constant). §D.3.
  3. **Two unprecedented mechanisms.** `DEFINE SEQUENCE`/`sequence::nextval` and `ulid()` ids exist nowhere in this tree. Per the repo's routing rule these are *properties to invent*, not specs to implement — design work, not builder work. §C.6, §A.1.
  4. **Spec sufficiency.** `docs/plans/v2/03-comms-message-graph.md` is 38 lines and defers semantics to `comms-subsystem.md:64-79` + `~/.claude/plans/one-of-claude-codes-nifty-garden.md` §"Data model". A contract author working from the packet file alone cannot write pins — confirm the design source is in their brief.
- **receipt pointers**:
  - §A ledger blueprint — `briefs.py:374-545` · §A.2 the `briefed` edge, direct model for `to` — `briefs.py:897-968`
  - §B retry seam + guard coverage — `store/_txn.py:804,1026`; `tests/test_retry_seam.py:651-677,1891-1941,2536-2567`
  - §C schema slices · §D render seam · §E tool surface · §F harness · §G flags — below
- **three answers the lead should read before briefing anyone**:
  - **§B.3** — SDK-guard coverage of a new module is **AUTOMATIC** (`rglob`, no registration list; that was a deliberate design choice, `test_retry_seam.py:600-612`). But it creates a **mandatory, non-obvious edit**: every new SDK call site is auto-enumerated and goes **RED as "unobserved"** until the builder drives it in `test_retry_seam.py:2510-2534`. Fails closed, not open.
  - **§C.2** — a new schema slice **CAN silently fail to land in the DDL**. The aggregation point is a hand-maintained list and the pins are `<=` subset checks, not `==`. Two tables (`finding_counter`, `brief_counter`) are already outside them today.
  - **§F.4** — **correction to a premise in my brief**: `test_txn_contention.py` has *zero* live races. The real ≥8-way pins are in `test_findings.py:477-539` and `test_brief_ledger.py:285-317`, and they race **separate ledger instances on separate connections** — not coroutines on one socket.

**Tool honesty**: lore's MCP tools were loaded but this run is overwhelmingly grep/AST-shaped work — enumerating call sites, finding textual seams (log event names, action literals, DDL strings), and answering exhaustiveness questions ("is there a list a new file must appear in?"). Per the repo dogfood protocol those are exactly cases (a) and (b) where grep is honest. **I fell back to grep for most of this map and am saying so.** `lore_get_symbol`/`lore_read` were used for definition lookups where the name was already known.

---

## A) THE LEDGER-MODULE BLUEPRINT

Three siblings share ONE idiom, byte-for-byte in the scaffolding. `tasks.py` (1546 lines) is the named blueprint; `briefs.py` (1292) is the most recent and the closest analogue for packet 03 (it owns BOTH a node table and a relation edge — exactly the `message` + `to` shape).

`briefs.py:1-95` is itself the best available blueprint: its module docstring pins the ENTIRE public API surface as a typed block before any code. A new `messages.py` should open the same way.

### A.1 The class scaffolding — clone this verbatim

All of `__init__` / `_ensure_connection` / `ensure_ready` / `close` / `_drop_connection` / `_safe_close` / `_query` / `_apply` are the SAME in all three modules, differing only in the `noun`/`label`/log-event strings and the DDL generator called.

| member | briefs.py | agents.py | tasks.py |
|---|---|---|---|
| `__init__(*, url, namespace, database, user, password)` | `:392` | `:356` | `:400` |
| `_ensure_connection` | `:412` | `:380` | `:432` |
| `ensure_ready` | `:463` | `:434` | `:489` |
| `close` | `:485` | `:457` | `:517` |
| `_drop_connection` | `:491` | `:463` | `:523` |
| `_safe_close` (staticmethod) | `:498` | `:470` | `:536` |
| `_query` | `:505` | `:477` | `:544` |
| `_apply` (txn) | `:526` | — (no txn path) | `:563` |
| `_as_rows` (staticmethod) | `:1236` | `:900` | `:1440` |
| `_row_to_X` | `:1242` | `:906` | `:1398` |
| `_require_aware_utc` | `:1254` | `:928` | `:1459` |
| `_to_aware_utc` (staticmethod) | `:1269` | `:943` | `:1478` |
| `_bare_id` (staticmethod) | `:1285` | `:964` | `:1534` |

**Constructor / DI pattern** (`briefs.py:392-408`): keyword-only `url, namespace, database, user, password`. Stores them plus `self._connection: _SurrealConnection | None = None` and `self._connect_lock = asyncio.Lock()`. **Opens no connection.** There is no store/pool object injected — each ledger owns its OWN lazily-opened WS connection.

**Connection acquisition** (`briefs.py:412-461`): double-checked lock; `AsyncSurreal(self._url)`; `await connection.signin({username, password})`; then `await bootstrap_session(connection, ns, db)` — the ONE shared bootstrap. Disposition is the seam's own job: `TxnContentionExhaustedError` AND `_CONNECTION_ERRORS` both close the half-open socket and re-raise as `SurrealConnectionError`. Note `briefs.py:423` — `bootstrap_session` deliberately does NOT wrap, because scout's reconnect ladder needs the raw exhaustion type.

**Single-statement queries** (`briefs.py:505-524`) — THE seam. Delegates wholly to `run_query`, passing:
- `acquire=self._ensure_connection`, `drop=self._drop_connection`, `url=self._url`
- `noun="brief query"` (message wording only)
- `label="brief.query.rejected"` — **this module's OWN canonical log event**
- `logger=logger` — **this module's OWN `logging.getLogger(__name__)`** (`briefs.py:125`). `run_query`'s docstring at `_txn.py:1063-1068` explains why: `JsonFormatter` serves `logger: record.name`, and Mezmo alerts key on `logger:loremaster.tasks`. A new module MUST pass its own logger, not `_txn`'s.

A new `messages.py` therefore owns a `message.query.rejected` label and `loremaster.messages` logger.

**Transactions** (`briefs.py:526-538`): `_apply(fragments: list[TxnFragment])` → `compose(*fragments)` → `execute_transaction(statement_text, merged_params, acquire=, drop=, url=)`. `compose` (`_txn.py:313`) merges fragments and raises `TxnParamCollisionError` on duplicate param names — hence the exhaustive per-fragment param-name constants (`briefs.py:202-221`, `tasks.py:185-249`). Note `tasks.py:248-249` uses **format-string param names** (`_CREATE_MANY_ID_PARAM_FMT = "cm{index}_id"`) for the fan-out case — that is the existing idiom for a variable-arity write, directly relevant to packet 03's `to`-edge fan-out.

`execute_transaction` verifies EVERY statement's status — the counter to the SDK's first-statement-only validation (`_txn.py:1132-1135`).

**Error-classification / laundering posture**: the ledger raises NOTHING raw. Three typed outcomes, all from `_txn`: `SurrealConnectionError` (transport, self-healed), `SurrealStoreError` (domain rejection, connection kept healthy), `TxnContentionExhaustedError`. The raw engine text is **logged server-side only**; the raised message carries a classified label + "see the server log" hint (ledger #31 — `_txn.py:1104-1118`). Each module then defines its own domain exception tree over `RuntimeError`: `BriefLedgerError`/`UnknownBriefError`/`UnknownBriefVersionError` (`briefs.py:362-371`), `AgentRegistryError` + 5 subclasses (`agents.py:315-337`), `TaskLedgerError`/`TaskNotFoundError`/`IllegalTransitionError` (`tasks.py:370-379`).

**Value objects**: pydantic `BaseModel` (`briefs.py:263,290,304,326,341`; `agents.py:201,242,258,277,295`; `tasks.py:256,303,319,355`). Rows → models via a `_row_to_X` method that runs every datetime through `_require_aware_utc` (a missing/naive stamp is an error, not a default) and every RecordID through `_bare_id`. Protocols (`AgentRefLike` `briefs.py:224`, `TaskSpecLike` `tasks.py:340`) are the idiom for accepting an externally-resolved identity.

**Decoupling ruling worth inheriting** (`briefs.py:79-89`): `BriefLedger` NEVER imports `loremaster.agents`. It accepts `agent_id`/`agent_name`/an `AgentRefLike` roster; the dispatcher resolves the roster via `AgentRegistry.fleet()`. Packet 03's `to=[]` ⇒ "broadcast active registry" will face exactly this fork — the existing law says the ledger stays key-agnostic and the CALLER resolves the roster.

**Id scheme**: deterministic `uuid5` hex. `briefs.py:542-545` — `uuid5(NAMESPACE_URL, f"lore://brief/{name}/{version}").hex`. `agents.py:499` `_agent_id(session, name)`. (Packet 03 spec instead calls for `ulid()` on `message` — a deviation from the sibling idiom that the contract author should note as deliberate.)

### A.2 The edge blueprint — `briefed`, the direct model for the `to` edge

`briefs.py:897-952` `_relate_briefed` is the closest existing analogue to packet 03's `to` delivery edge.

**The bound-RecordID RELATE form** (`briefs.py:919-931`), with the gotcha pinned in the docstring at `:900-906`: `RELATE type::record(...)->edge->type::record(...)` is a **PARSE ERROR on 3.1.5**. The working shape is:

```
RELATE $from->{RELATION}->$to SET via = $via, at = $at
```
with `$from`/`$to` bound as SDK `RecordID(TABLE, id)` objects — never a `type::record()` call at a RELATE endpoint position. Cloned from `graph_surreal._edge_statement`.

**UNIQUE(in,out) as the idempotency signal** (`briefs.py:908-913, 946-952`): a UNIQUE rejection is caught as `SurrealStoreError`, then `_select_briefed_edge` reads back the existing edge's payload and reports `already_acked=True`. If the read-back finds NOTHING, the original rejection re-raises (it was a genuine failure, e.g. an out-of-domain value hitting a schema ASSERT).

**The guarded-CAS door — do not omit** (`briefs.py:933-945`): `TxnContentionExhaustedError` is re-raised UNTOUCHED and must NEVER fall through to the read-back. If it did, a DROPPED write would be reported to the caller as an idempotent no-op. The comment states this is one of **FOUR** such doors in the package, that a hand-list once named only two and dropped a third, and that **the contract quantifies over all four structurally so a fifth is pinned the day it is written**. Packet 03's `ack` (write-once CAS) will be that fifth door — it will be structurally pinned automatically, and it must carry the identical guard.

**Edge read-back** (`briefs.py:954-968`): `SELECT * FROM {RELATION} WHERE in = $edge_in AND out = $edge_out LIMIT 1`, endpoints again bound as `RecordID`.

---

## B) THE RETRY SEAM

### B.1 Public signatures — `loremaster/loremaster/store/_txn.py`

```python
async def retry_on_conflict[T](                      # :804
    attempt: Callable[[], Awaitable[T]], *,
    deadline_seconds: float | None = None,
    label: str | None = None,
    url: str | None = None,
) -> T

async def bootstrap_session(                          # :929
    connection: _SurrealConnection, namespace: str, database: str
) -> None

async def run_query(*,                                # :1026
    acquire: AcquireConnection, drop: DropConnection,
    url: str, noun: str, label: str,
    statement: str, params: dict[str, Any] | None = None,
    logger: logging.Logger,
) -> Any

async def execute_transaction(                        # :1123
    statement: str, params: dict[str, Any], *,
    acquire: AcquireConnection, drop: DropConnection,
    url: str, deadline_seconds: float | None = None,
) -> None

def compose(*fragments: TxnFragment) -> tuple[str, dict[str, Any]]   # :313
```

**Division of labour** (`_txn.py:822-836`): it is a HELPER, NOT A DECORATOR — by design ruling. `retry_on_conflict` owns attempt counting, the give-up predicate, per-attempt fresh full jitter, and the exhaustion raise. **Detection stays with the caller**: `attempt` is responsible for classifying whatever it catches into `RetryableConflictSignal`. Anything else propagates untouched with ZERO retries (at-most-once: a transport fault may already have committed).

This is precisely the "ROUTING IS NOT SHARING" trap from CLAUDE.md — a new module that calls the driver but hand-rolls its own `"Resource busy"` string match is a private copy wearing the shared name. The shared classifiers are `is_retryable_conflict_error` (`:633`), `is_connection_error` (`:592`), `_classify_engine_error` (`:527`), keyed on `_RETRYABLE_CONFLICT_MARKER` (`:409`).

**Budget constants** (`:437,471,472,480,484`): `_MAX_TXN_CONFLICT_ATTEMPTS = 5` (floor), `_TXN_CONFLICT_ATTEMPT_CEILING = 64`, default deadline `2.0s`, backoff base `0.005`/cap `0.1`. The deadline is read at CALL time, never frozen into a default argument (`:848-853`) — freezing it at import is what left #102's retry branch unreachable by every test ever written.

### B.2 How a ledger module calls it

**A ledger module never calls `retry_on_conflict` directly.** It calls `run_query` (single statements) or `execute_transaction` (multi-statement), both of which call the driver internally (`_txn.py:1120`). The only ledger-level obligation is to pass its OWN `label` + `logger` (§A.1).

### B.3 THE RUNTIME SDK-ESCAPE GUARD — *the decisive answer*

Guard implementation: `loremaster/tests/_sdk_guard.py`. Consumers: `loremaster/tests/test_retry_seam.py`.

The guard wraps every public async method on the three real SDK connection classes (`_sdk_guard.py:103` `SDK_CONNECTION_CLASSES`, `:333` the install loop) and classifies each call by whether a driver frame sits above it. Design per CLAUDE.md's "allowlist the safe": **deny by default**, with a two-name safe set `SAFE_CONNECTION_METHODS = frozenset({"signin", "close"})` (`_sdk_guard.py:131`). `_GUARDED_SDK_METHODS` (`test_retry_seam.py:1881-1888`) is DERIVED from the SDK classes by reflection, never hand-listed — so a method the SDK adds in 2027 is covered with no edit. `_UNGATED_SDK_WRITES` (`:2008-2020`) pins exactly that, including a param literally named `some_method_the_sdk_adds_in_2027`.

**IS COVERAGE AUTOMATIC FOR A NEW MODULE? — YES. There is no registration list.** All three enumerators walk the package from disk:

- `_discover_query_seams()` — `test_retry_seam.py:651-677`: `_PACKAGE_ROOT.rglob("*.py")`, AST-finds every class owning an `async def _query`, imports it, and parametrises it into every seam pin as `_QUERY_SEAMS` (`:674`).
- `_all_sdk_call_sites()` — `:1891-1941`: `rglob("*.py")` → every call on a connection receiver.
- `_unseamed_sdk_call_sites()` — `:1944-1976`: the offenders subset.

The design intent is stated at `:600-612`: *"A pin over a hand-listed set can only ever be as complete as the list, and the list is exactly what nobody can be trusted to keep… An ELEVENTH clone — a new ledger that hand-rolls the same seam without the retry — is discovered the day it is written and goes RED without anyone remembering to add it."* **A new `messages.py` cannot silently escape the guard.**

**BUT — three obligations a new module MUST meet, or it breaks the gate rather than escaping it:**

1. **`_CTOR_VALUES` (`test_retry_seam.py:633-648`) is a real, hand-maintained list — and it is the one place a new module touches the test file.** `_construct` (`:680-695`) asserts that every REQUIRED constructor parameter has an entry, and fails LOUDLY with: *"Add them to _CTOR_VALUES — do NOT drop the seam from the suite."* If `MessageLedger.__init__` takes only the standard five (`url, namespace, database, user, password`), all are already present and nothing needs adding. Any NEW required param must be added here.

2. **THE COVERAGE PIN IS THE HARD OBLIGATION** — `test_retry_seam.py:2536-2567` (inside `TestNoSdkCallEscapesTheDriverAtRuntime`, class at `:2263`). It computes `unobserved = all_sites - observed` and asserts it is EMPTY:
   > *"the runtime guard never EXECUTED N of M production SDK call sites, so it certifies NOTHING about them… A runtime gate is an invariant only over code it RUNS. An unwatched call site is how `_drain_pending` shipped finding #120 alive through a suite that scored 932/0. Drive it here — or it is watched by nothing but a name-keyed lint."*

   The `observed` set comes from a **hand-written driving body** (`:2510-2534`) that explicitly exercises each seam against a live engine. **So: every SDK call site the new `messages.py` adds is enumerated AUTOMATICALLY and will go RED as "unobserved" until the builder adds code to that driving body to execute it.** This is the single most consequential fact in this report for packet 03 planning — it is a mandatory, non-obvious edit to `test_retry_seam.py`, and it fails closed (red), not open.

3. **The scan gate `_talks_to_surrealdb`** (`test_retry_seam.py:1862-1876`): a module is scanned iff it imports `surrealdb` OR `loremaster.store._txn`. A `messages.py` following the sibling idiom imports BOTH (`briefs.py:105-118`), so it is in scope. **Stated limit at `:1865-1867`**: a module that only RECEIVES a connection and imports neither would be skipped.

**Stated honest limits of the seam enumerator** (`:614-622`) — the builder should know these, since packet 03 could trip them:
- It finds a class OWNING `async def _query`. A module spelling its seam differently (`_run`, a bare inline `connection.query`) is NOT found — this is the documented `scout.py` defeat.
- `_MIN_KNOWN_SEAMS = 10` (`:625`) guards against the scan silently finding nothing (a parametrised suite over an empty list is vacuously green). **A new ledger raises the true count to 11; if this constant is a floor it still passes, but the builder should verify it is not an equality pin.**

**`artifact_root()` / `require_observations()` — the #136 anti-vacuity layer** (`_sdk_guard.py:134-244`):
- `artifact_root()` (`:202-221`) asks the IMPORTED `loremaster` module where it executes from — never derived from the test file's path. Raises `GuardCannotSubstantiate` if `__file__` is None (a namespace package).
- `_require_a_root_the_code_runs_from()` (`:230-244`) is an ARM-TIME precondition: if the code the guard must judge does not live under the watched root, no frame can ever match, so it raises rather than certifying nothing.
- `GuardReport.require_observations(flow)` (`:176-192`) — a caller asserting cleanliness on a flow that PROVABLY calls the SDK must first call this; zero observations raises rather than passing vacuously. Existing call sites: `test_retry_seam.py:2309, 2345, 2392, 2435`.
- The coverage pin also emits a divergent-trees warning (`:2546-2556`) when the scanned tree ≠ the executed tree.

**Other named lists in `test_retry_seam.py` a builder may meet**: `_SHARED_SEAM_NAMES = ("retry_on_conflict", "run_query")` (`:1554`), `_SEAM_MODULE = "store/_txn.py"` (`:1788`), `_CONNECTION_NAMES = frozenset({"connection", "conn"})` (`:1787` — the receiver-name heuristic), `_LABEL_HOME`/`_LABEL_PREFIX` (`:3542-3544`), `_MARKER_NAME`/`_MARKER_TEXT` (`:3549-3550`), and a DESIGN-LAW cross-check at `:3677-3678`. Note `TestEverySdkCallSiteActuallyRetries` at `:3055`.

---
## C) SCHEMA SLICES — `loremaster/loremaster/store/surreal_schema.py` (1371 lines)

### C.1 The house pattern

FieldSpecs are **plain tuples — there is no dataclass anywhere in the file.** Two variants:
- 2-tuple `(name, type_expr)` — only for constraint-free tables: `_CHUNK_FIELD_SPECS:150-166`, `_CODE_NODE_FIELD_SPECS:577-584`, `_REFERS_FIELD_SPECS:588-593`, `_ANSWERS_TO_FIELD_SPECS:597-600`, `_NAME_FIELD_SPECS:607`.
- 3-tuple `(name, type_expr, constraint)` — **the canonical form to clone**: `_MEMORY_FIELD_SPECS:218-240`, `_TASK_FIELD_SPECS:305-318`, `_FINDING_FIELD_SPECS:367-383`, `_AGENT_FIELD_SPECS:439-451`, `_BRIEF_FIELD_SPECS:485-492`, `_BRIEFED_FIELD_SPECS:514-517`, `_TRACE_FIELD_SPECS:557-566`.

**The OVERWRITE-vs-IF-NOT-EXISTS decision is encoded ONCE, in the generator helpers — never per-spec.** This is the #107 fix, and a new slice inherits it for free by using the helpers:
- `_define_field():636-671` → `DEFINE FIELD OVERWRITE … TYPE …` — **always OVERWRITE**, because `IF NOT EXISTS` is a silent no-op against an existing field, so a changed definition never migrates a live store.
- `_define_table():610-612`, `_define_relation_table():615-622` → `DEFINE TABLE IF NOT EXISTS … SCHEMAFULL`.
- `_hnsw_index():674-679`, `_fulltext_index():682-687`, `_plain_index():690-692`, `_unique_index():695-701`, `_analyzer_statement():704-709` → all `IF NOT EXISTS` (rationale in the docstring at `:654-660`).

Representative slice to clone — `task` (closed-domain ASSERT, `option<>` columns, `DEFAULT []`, `FLEXIBLE`, one plain index):
specs `:305-318`, statements `_task_statements():932-952`, generator `generate_task_ddl():1257-1276`. The generator body is uniformly `";\n".join(statements) + ";\n"`.

### C.2 REGISTRATION — ⚠ THE GAP IS REAL AND OPEN (finding #124)

`generate_ddl()` at `:1170-1204`. Its composition list at `:1188-1203` is **a plain hand-maintained Python list.** Nothing derives it.

**Plain answer to the lead's question: YES — a new slice can be written and silently NOT land in the DDL.** Nothing forces the append into `:1188-1203`, nothing forces a `generate_x_ddl()` to exist, and nothing forces the owning class to call whichever generator does exist.

The only guards are **subset checks, not exact-set pins**:
- `EXPECTED_TABLES` frozenset, `tests/test_surreal_schema.py:77-91`, asserted `EXPECTED_TABLES <= tables` at `:505-513`.
- Comms mirror: `assert {AGENT_TABLE, BRIEF_TABLE, BRIEFED_RELATION} <= tables`, `tests/test_comms_schema.py:632`.

Both use `<=`, never `==`. So the pin only fires if a developer independently remembered to add the new table name to the frozenset — i.e. it catches nothing that the same forgetfulness would not also skip. **Corroborating evidence that this gap bites in practice: `generate_ddl()` DOES emit `finding_counter`, and `EXPECTED_TABLES` does NOT list it; `test_comms_schema.py:632` likewise omits `brief_counter`.** Two tables are already outside the pins today.

**Architecture note the contract author needs**: the comms tables are **not aggregated into `generate_ddl()` at all.** `agent`/`brief`/`briefed`/`brief_counter` have their own generators (`generate_agent_ddl():1302-1320`, `generate_brief_ddl():1323-1345`), as does the graph slice (`generate_graph_ddl():1348-1371`). Each is applied by its OWNING class at its own `ensure_ready()`: `agents.py:437-447`, `briefs.py:466-475`, `tasks.py:492-507`, `findings.py:479-496`, `graph_surreal.py:443-460`, `memory/local.py:390-403`, `index/surreal_manifest.py:228-245`. `SurrealStore.ensure_ready()` (`store/surreal.py:513`) is the only caller of `generate_ddl()` itself. **So a `messages.py` slice follows the comms precedent: its own `generate_message_ddl()`, applied by `MessageLedger.ensure_ready()` — and it will NOT appear in `generate_ddl()`.**

### C.3 The edge slices — three `TYPE RELATION` tables

Constants: `BRIEFED_RELATION = "briefed"` `:87`, `REFERS_RELATION = "refers"` `:108`, `ANSWERS_TO_RELATION = "answers_to"` `:109`.

All three declare via `_define_relation_table():615-622` → `DEFINE TABLE IF NOT EXISTS {name} TYPE RELATION SCHEMAFULL`. **`in`/`out` are NEVER hand-declared** — auto-defined by `TYPE RELATION` (comment `:505-508`). **No `PERMISSIONS` clause anywhere in the file** (grep: zero occurrences).

| edge | statements | fields | UNIQUE(in,out)? |
|---|---|---|---|
| `briefed` | `_briefed_statements():1053-1075` | `:514-517` — `via` string ASSERT IN [register,explicit,publish]; `at` datetime DEFAULT time::now() | **YES** — `_unique_index(BRIEFED_RELATION, f"{BRIEFED_RELATION}_in_out", ("in","out"))` at `:1072-1074`, fields tuple `:526` |
| `refers` | `:1144-1154` | `:588-593` — kind, resolved bool, src_tier, src_file_path | no — plain index on `src_file_path` `:1151-1153` |
| `answers_to` | `:1157-1167` | `:597-600` — tier, file_path | no — plain index on `(tier, file_path)` `:1164-1166` |

`briefed` is explicitly the **first and only** relation table carrying a UNIQUE(in,out) index (comments `:519-526`, `:1062-1065`), legal on SurrealDB ≥3.1.0 per the #7061 fix. **It is therefore the sole precedent for packet 03's `to` edge.**

### C.4 RELATE in calling code — the bound-RecordID form

Two production call sites, identical idiom, both citing the 3.1.5 gotcha that `type::record(...)` in RELATE endpoint position is a **parse error**:
- `briefs.py:919-931` — `RELATE $from->briefed->$to SET via = $via, at = $at`, endpoints bound as `RecordID(TABLE, id)`.
- `graph_surreal.py:947-951` and `:973-975` — same shape, endpoints from `_code_node_id():550-552` / `_name_id():554-557`.

**⚠ DANGLING-EDGE HAZARD (#105) IS OPEN AND UNHANDLED.** `docs/reference/surrealdb-31-capabilities.md:274-283`: RELATE does **not** validate that `in`/`out` exist — a bogus id silently writes a dangling edge with no error. Neither existing RELATE call site validates endpoint existence. The guard ("guard every edge-writing verb") is scheduled for **packet 04** (`docs/plans/v2/04-comms-blocks-footer.md:17`), i.e. NOT this packet. Packet 03's `to` fan-out writes edges to caller-supplied recipient names — **this is the exact hazard shape, and the mitigation is one packet later than the code that creates the exposure.** Flagging for an operator ruling, not deciding it.

### C.5 The `agent` table

`AGENT_TABLE = "agent"` `:85`; specs `_AGENT_FIELD_SPECS:439-451`; `_agent_statements():1001-1027` (fields + non-unique `(session,status)` index + non-unique standalone `name` index).

**ID scheme — deterministic uuid5, NOT a sequence** (`agents.py:499-501`):
`uuid5(NAMESPACE_URL, f"lore://agent/{session}/{name}").hex`
Consumed as a bound string into `type::record('agent', $id)` for SELECT (`agents.py:507-509`), and as `RecordID(AGENT_TABLE, agent_id)` for RELATE (`briefs.py:919`).

**Active/retired marker** — a single `status` field over a closed 4-value domain: `active` / `idle` / `input_required` / `retired` (`surreal_schema.py:412-421`, ASSERT built `:422`, applied `:444`). App-side mirrors `agents.py:106,109`. **`orphaned` (`agents.py:141`) is NOT a stored value** — it is derived at render time from `heartbeat_at` age (comment `surreal_schema.py:409-411`) and is deliberately excluded from the ASSERT domain. **There is no hard delete — agents are retired, never removed.** This matters for packet 03's `to=[]` broadcast: "active registry" must be defined against this domain, and a retired agent still has rows and edges.

### C.6 `sequence::nextval` — DOES NOT EXIST YET

**Not present anywhere in the production tree.** Grep for `sequence` / `nextval` / `DEFINE SEQUENCE` over `loremaster/loremaster/` returns zero DDL hits (the only two "sequence" matches, `surreal_schema.py:90` and `:1083`, are English prose unrelated to the SQL feature). `git log` on `surreal_schema.py` confirms its recent commits are the #107/#102 fixes only.

It is planned-but-unbuilt, and packet 03 is where it lands: `docs/plans/v2/03-comms-message-graph.md:15-16` — `message.seq` via native `DEFINE SEQUENCE` + `sequence::nextval("<name>")`, probe-settled and operator-confirmed under ledger task **f86af162**, explicitly **not gapless, accepted**. **Packet 03 therefore introduces BOTH a new DDL verb (`DEFINE SEQUENCE`) and a new id scheme (`ulid()`) that no existing slice uses — neither has an existing pattern to clone.**

---
## D) THE RENDER SEAM (packets 02 + 02a)

### D.1 `loremaster/loremaster/sanitise.py` (100 lines) + `render.py`

- **`SafeLine`** — `sanitise.py:43-65`, a **`str` subclass** (not NewType, not dataclass). The docstring is explicit that the type alone enforces nothing (an f-string coerces anything via `str()`); the guarantee comes from four paired instruments in `render.py`. Mintable ONLY by `sanitise_line`, `safe_str`, `render.render_join` — enforced by AST scan.
- **`Rendered`** — `render.py:95-105`, also a `str` subclass. Minted only by `render_line`, `render_fenced`, `render_compose`.
- **`safe_str(value: object) -> SafeLine`** — `sanitise.py:68-74`; `return sanitise_line(str(value))`.
- **`sanitise_line(text: str) -> SafeLine`** — `sanitise.py:77-94`; `SafeLine(CONTROL_CHAR_PATTERN.sub(" ", text).strip())`. `CONTROL_CHAR_PATTERN` (`:36-38`) covers C0/C1+DEL, ANSI/OSC ESC+BEL, bidi override U+202A-202E / isolate U+2066-2069 / marks U+200E-200F, zero-width U+200B-200D/U+2060/U+FEFF, and separators U+2028/2029. **It does NOT touch fenced bodies** — fencing is a separate guarantee.
- **`max_backtick_run(text) -> int`** — `sanitise.py:97-99`; sizes a fence strictly longer than any embedded backtick run (`render_fenced`, `render.py:229-243`) so a body cannot smuggle a fence-closer.

Note the naming detail for a builder: the public function is **`sanitise_line`**, not `_sanitise_line` (the leading-underscore form named in the brief was its pre-promotion name under finding #34).

Golden-oracle pin: `tests/test_sanitise.py` — `_GOLDEN_BATTERY:52-59`, row-forgery fixture `_ROW_FORGE_INPUT`/`_ROW_FORGE_EXPECTED:31-32`, every documented threat codepoint `:73-93`. **This file proves the sanitiser only, never call-site discipline.**

### D.2 The deny-by-default safe set (packet 02a)

The canonicaliser lives in **`tests/test_comms_promise_registry.py`**: `_canonicalise:1252-1375`, with `_canonicalise_call:1188-1218`, `_canonicalise_string_method:1221-1249`, `_canonicalise_binop:1378-1415`. Its docstring (`:1259-1262`): *"an explicit ALLOWLIST in two halves… it ends in `raise`, so any shape outside both halves fails loud."*

**Half (a) — text-building shapes (must canonicalise or deny)**: `ast.Constant` str `:1264-1266`; `ast.JoinedStr` `:1270-1277`; `ast.FormattedValue` `:1278-1280`; `ast.BinOp` — **only `+` and `%`**, all else denies (`:1378-1415`); `ast.IfExp` `:1283-1286`; `ast.BoolOp` `:1287-1295`; `ast.Call` `:1296-1297` (render wrappers, `.format`/`.join`, or `_TRANSPARENT_ARG_POSITIONS`/`_TRANSPARENT_ARG_KEYWORDS` for `dict.get`/`getattr`/`next`/`str`); `ast.Name` `:1298-1313` (resolved via same-function `Assign`/`AnnAssign` or parameter defaults; opaque if unbound).

**Half (b) — opaque runtime values (each exemption evidence-commented)**: `ast.Attribute` `:1315-1316`; `ast.Subscript` of a non-string base `:1317-1322` (**denies if indexing a literal**); `ast.List|Tuple|Set` incl. `Starred` `:1323-1331`; `ast.Dict` `:1332-1339`; `ast.ListComp|SetComp|GeneratorExp` `:1340-1350`; `ast.DictComp` `:1351-1361`; `ast.Starred` `:1362-1364`; `ast.Compare|UnaryOp` `:1365-1372`; `ast.Await` `:1373-1374`.

**Everything else hits `raise _UnclassifiableShape(node)` at `:1375`**, carrying `ast.dump(node)`. The two scanners calling it (`_scan_render_literals_over_tree:232-289`, `_scan_safe_str_over_tree:1435-1464`) route the site into an `unclassifiable` list; `TestTheCanonicaliserDeniesByDefault.test_no_unclassifiable_shape_in_the_shipped_comms_surface:1641-1652` asserts that list is EMPTY. So an unrecognised shape is a **hard failure naming `file:line` + the dump**, never a silent pass. The retired canonicaliser it replaced ended `else: [_PLACEHOLDER]` and shipped three live holes (`%`-format, `.format`, `.join`) invisibly (`:992-1003`).

### D.3 AST scanners — ⚠ COVERAGE SPLITS IN TWO, AND THIS IS DECISION-CRITICAL

| Scanner | file:line | Scans | Auto-covers a NEW module? |
|---|---|---|---|
| `TestSafeLineRenderedMintPin` | `test_render_seam_pins.py:264-329` (scan `:117-181`) | `_PACKAGE_ROOT.rglob("*.py")`, root `:39` | **YES** |
| `TestRenderLineTemplateLiteralPin` | `test_render_seam_pins.py:413-460` (scan `:230-261`) | same `rglob` | **YES** |
| Promise-literal scan `_comms_render_literals` | `test_comms_promise_registry.py:292-295` → `TestEveryCommsRenderLiteralIsClassified:309-340`, `TestTheScanReachedEveryCommsRenderHelper:343-370` | `_SERVER_PY` — **ONE hardcoded file** (`:78`) | **NO** |
| `safe_str`-literal scan | `test_comms_promise_registry.py:1467-1469, 1519-1554` | same hardcoded `_SERVER_PY` `:1468` | **NO** |
| `TestRendersNeverNameTheStandingBriefConstant` | `test_comms_render_architecture.py:610-654` | `_PACKAGE_ROOT / "server.py"` `:613,645` | **NO** |

**The answer the lead asked for: coverage is SPLIT.** The two seam-level pins auto-scan the whole package via `rglob`, so a new `loremaster/messages.py` inherits mint discipline and template-literal discipline for free. **But the three comms-specific scanners are hardcoded to `server.py` by path.** A render helper defined in a new module would be **invisible to the promise-classification guard, the safe_str-literal guard, and the STANDING_BRIEF name-constant guard.** There is no file list to register into — the path is a bare string constant.

This gap is **latent, not currently exercised**: all 17 `_render_comms_*`/`_comms_*` functions live in `server.py` today (zero in `agents.py`/`briefs.py`). Packet 03 is the first packet that could trip it, if it puts renders in `messages.py`.

**Naming is load-bearing independently of file**: all three scanners walk only `FunctionDef|AsyncFunctionDef` whose `.name` starts with `_render_comms` or `_comms_` (`test_comms_promise_registry.py:265,1447`; `test_comms_render_architecture.py:619`). **A correctly-shaped helper with the wrong prefix is not scanned at all.**

### D.4 The promise registry (`test_comms_promise_registry.py`, 2115 lines)

A default-FAIL completeness + behavioural instrument over every served comms line, in two parallel halves per literal:

**Static classification** — `_PROMISE_REGISTRY: dict[str,str]` (`:89-164`, promise text → predicate description) and `_PROMISE_FREE: dict[str,str]` (`:171-207`, text → reason). Every scanned `render_line`/`render_join` template literal must appear in one or the other, else `test_every_comms_render_literal_is_classified:312-324` fails naming `fn:line: text`. The parallel safe_str channel classifies against `_SAFE_STR_PROMISE_FREE:1498-1512` via `:1519-1554` — and a **real promise** found there must **STOP and escalate to packet 02 scope**, never be quietly classified promise-free (`:1533-1535`).

**Executable proof** — `PromiseProof` dataclass `:635-645`: `literal`, a byte-exact `marker` substring, and two callables `render_emit`/`render_no_emit` that drive the **real** `AppContext._render_comms_*` method with the predicate TRUE and FALSE. `_assert_predicate_gates:648-664` asserts the marker is present in the EMIT leg (positive control) and **absent** in the NO-EMIT leg (discrimination — proving the predicate actually gates emission). `_PROOF_LIST`/`_PROMISE_PROOFS:667-879`.

**registered ⟺ proven** — `test_registered_iff_proven:890-901` asserts `frozenset(_PROMISE_PROOFS) == frozenset(_PROMISE_REGISTRY)`, reporting `registered but UNPROVEN` and `proven but UNREGISTERED` separately by name. Plus `test_predicate_gates_emission:886-888` (parametrized over every proof) and `test_no_duplicate_proof_literals:903-909`.

**What a NEW render must do here** — registration is MANDATORY, default is FAIL:
1. Every new `render_line`/`render_join` template literal in a `_render_comms*`/`_comms_*` function **in `server.py`** → add to `_PROMISE_REGISTRY` (with a §9.7-litmus predicate description) or `_PROMISE_FREE` (with a reason).
2. Any literal registered as a promise → add a `PromiseProof` to `_PROOF_LIST` driving the real render TRUE/FALSE with a byte-exact marker, or `test_registered_iff_proven` fails.
3. The marker must not be satisfied by any OTHER proof's emit render (`TestNoMarkerIsCrossSatisfiedByAnotherProof:1955-1965`, `_cross_satisfied_markers:1936-1949`) unless exempted with a reason in `_MARKER_CO_EMISSION_EXEMPTIONS:1925-1933`.

**An `ACK REQUIRED` trailer reads as a mechanism promise on its face** — it will need registry entry + proof + non-cross-satisfied marker.

**Two PINNED KNOWN BOUNDS (#143 territory — "pin the miss" law), both directly relevant to packet 03**:
- `test_KNOWN_BOUND_cross_function_flow_is_not_reached:2075-2086` — a promise assembled in a helper WITHOUT the `_render_comms`/`_comms_` prefix and passed by call into a comms `safe_str` is invisible. Re-open trigger (`:2070-2073`): any such helper must itself carry the prefix.
- `test_KNOWN_BOUND_a_promise_carried_in_a_render_VALUE_is_not_inspected:2088-2115` — neither scanner inspects `render_line`'s **value kwargs**, only the template. Caught today only because a placeholder-only template `"{msg}"` is itself unclassified. Re-open trigger: the day anyone classifies a bare `"{...}"` template as promise-free, this bound must close FIRST. **A numbered drain list is a plausible candidate for exactly such a template — the contract author should check this bound before designing the drain render.**

### D.5 STANDING_BRIEF role accessor + typed applicability (#104)

- **The accessor**: `STANDING_BRIEF = BRIEF_NAME_PROJECT` at `briefs.py:147` (`BRIEF_NAME_PROJECT = "project"` at `:137`). Docstring `:140-146`: *"the ONE named standing-brief ROLE… a ROLE bound to a name, not the literal name — the four standing surfaces in `server.py` read THIS symbol (never a private `== BRIEF_NAME_PROJECT` copy)."* Consumed at `server.py:4569,4577,4600,4603,4609,4674,4704,4720`.
- **Typed applicability**: `_render_comms_brief_publish` (`server.py:5001-5010`) takes keyword-only `auto_ack_at_register: bool` and branches on it directly (`:5023,5055`) — never `result.brief.name == BRIEF_NAME_PROJECT`. Rule stated at `:5013-5020`.
- **Mutation proof it is ONE shared role**: `TestStandingBriefIsOneSharedRole` (`test_comms_render_architecture.py:319-391`) monkeypatches `server_module.STANDING_BRIEF` to a novel `"governance"` (`_ROLE:310`, `_install_role:313-316`, `raising=False`) and asserts all four surfaces follow — a surface still hardcoded to `BRIEF_NAME_PROJECT` fails for the right reason.
- **Anti-name-comparison discriminators**: `TestFirstVersionTailIsTypedNotNameDerived:133-206` and `TestSkewTailIsNameConditioned:239-293` each carry a `test_DISCRIMINATOR_*` case where the brief IS literally named `'project'` but the flag is `False` (and the converse) — a build re-deriving applicability from the name fails both directions. **This is the fixture-monoculture lesson made mechanical; a new render's fixtures must do the same.**
- **Structural AST ban**: `TestRendersNeverNameTheStandingBriefConstant:629-654` scans every `_render_comms*` body for an `ast.Name`/`ast.Attribute` load of `BRIEF_NAME_PROJECT` or `STANDING_BRIEF` (`_BANNED_NAME_CONSTANTS:607`, scanner `:610-626`) and fails if found.

**Rule for a new render**: receive applicability as a **typed parameter it branches on**; never re-derive a role by comparing a name string inside the render; never load the name constants inside a `_render_comms*` function.

### D.6 The files that will police a new render

- `tests/test_sanitise.py` — byte-exact golden oracle for the sanitiser itself.
- `tests/test_render_seam_pins.py` — package-wide AST pins (mint discipline; `render_line`/`render_join` template+separator must be `ast.Constant`). **Auto-covers a new file.** Also hosts `assert_actions_covered:535-560`.
- `tests/test_render_mypy_layer.py` (+ `_optout.py`) — subprocess-mypy meta-test pinning the exact error codes for the value/return legs (`render.py:29-32`).
- `tests/test_render.py` — unit behaviour/errors of the four render primitives.
- `tests/test_comms_promise_registry.py` — classification + canonicaliser + emit/no-emit proofs + cross-satisfaction. **`server.py` only.**
- `tests/test_comms_render_architecture.py` — #104 typed applicability, role mutation proof, banned-name AST scan, skew pins. **`server.py` only.**
- `tests/test_comms_tool.py` — `C1_RENDER_CASES:3583-3602` hostile-injection registry + per-action-family completeness `:3611-3631`.
- `tests/test_mcp_server.py` — `TestRenderInjectionRegistry:7824+`, the older sibling registry; documented at `:7845-7851` as NOT auto-detecting a new comms render (defers to `assert_actions_covered`).
- `tests/render_injection_scaffold.py` — not a test file (uncollected); shared `RenderCase` / `_INJECTION_THREAT_CHARS` / `assert_render_injection_safe` (3-assertion oracle: no added `\n`, no surviving Cc/Cf/Zl/Zp, no forged row line).

---

## E) THE COMMS TOOL SURFACE

### E.1 Dispatcher shape

**MCP wrapper**: `server.py:7353-7512` — `@mcp.tool(name="lore_comms", description=…, annotations=_COMMS_TOOL_ANNOTATIONS)` over `async def comms(context, action, agent, session=None, role=None, model=None, spawned_by=None, task_id=None, note=None, status=None, name=None, body=None, version=None, limit=None) -> str`. Every optional param is `Annotated[X | None, Field(description=…)] = None`. The body (`:7498-7512`) forwards every kwarg to `_app_context(context).comms(...)`.

**Domain dispatcher**: `AppContext.comms` — `server.py:4369-4484`, returns `Rendered`. The algorithm is written as a numbered comment at `server.py:4357-4367`:
1. `spec = _COMMS_ACTIONS.get(action)`; `None` → `ValueError` listing `list(_COMMS_ACTIONS)` (`:4408-4412`).
2. Charset-validate `agent`/`session`/`name` via `_validate_comms_charset` (`:4486-4502`) **before any store touch** (`:4414-4418`).
3. Strict-param law: any non-`None` param outside `spec.params | spec.required` → `_comms_foreign_param_error` (`:4504-4525`); `session` is universal (`:4433-4438`); then every `spec.required` must be non-`None` (`:4439-4443`).
4. `limit` range pre-check (`:4452-4456`) — deliberately BEFORE the heartbeat touch so a rejected call has **zero side effects** (rationale `:4444-4451`).
5. Uniform heartbeat touch for every action with `spec.requires_registration` (`:4458-4467`).
6. `return await spec.handler(self, agent=…, …)` (`:4469-4484`) — handlers receive the FULL kwarg set plus `agent_row`.

**Mechanism**: a **dict of frozen dataclass specs**, not an if/elif chain, not a Literal/enum. `_COMMS_ACTIONS: dict[str, CommsActionSpec]` at `server.py:5428-5457`; `CommsActionSpec` at `:5404-5420` — `handler: Callable[..., Awaitable[Rendered]]`, `params: frozenset[str]`, `required: frozenset[str] = frozenset()`, `requires_registration: bool = True`. Its docstring (`:5406-5415`) calls this a **sanctioned deviation** from the `tasks()`/`findings()` if/elif house idiom, motivated by the completeness pin needing a real iterable table.

**End-to-end, `register`** (the one action with `requires_registration=False`): spec `:5429-5434` (`params={role,model,spawned_by,task_id}`, `required={session,role}`) → dispatcher SKIPS `touch` (`:4459` guard), `agent_row` stays `None` → handler `_comms_register:4549-4587` calls `agent_registry.register(...)`, then unconditionally `brief_ledger.get_head(STANDING_BRIEF)` + `ack(...)` (`:4568-4580`, the #98 self-ack) → render `_render_comms_register:4752+` (a `@staticmethod -> Rendered`, built only from `render_line`/`render_compose`/`sanitise_line`/`safe_str`) → back up to the `-> str` wrapper.

### E.2 Adding an action — every site

**There is no `Literal` and no enum; `action` is typed `str` end to end** (`server.py:4372`, `:7373`). The single source of truth is `_COMMS_ACTIONS`. Name constants at `server.py:1100-1105`, and the comment directly above them (`:1097-1099`) is explicit: *"exactly six in C1; send/drain/ack/await/story are C2/C3 growth points (design doc §FORWARD-COMPAT) that widen `_COMMS_ACTIONS` deliberately in a later phase."* **Packet 03's additions were designed for.**

Sites a new action must touch:
1. `server.py:1100-1105` — the `_COMMS_ACTION_*` string constant.
2. `server.py:5428-5457` — the `CommsActionSpec` entry.
3. `server.py:4547+` — the `_comms_<action>` handler (`-> Rendered`).
4. `server.py:4734+` — the `_render_comms_<action>` helper.
5. `server.py:4369-4385` — any genuinely NEW param added to `AppContext.comms`'s keyword signature **AND** to the `values: dict[str, Any]` block at `:4420-4432` that the strict-param and required-param checks iterate.
6. `server.py:7370-7497` — the same new params on the MCP wrapper as `Annotated[…] = None`, **and** forwarded in the call at `:7498-7512`.
7. `server.py:7355-7367` — the tool `description=` must NAME the new action (pin-enforced, see E.4).
8. `tests/test_comms_tool.py:300` — `_EXPECTED_ACTIONS`, asserted `== set(_COMMS_ACTIONS)` at `:302-303`.

The `action` parameter's own `Field(description=…)` (`server.py:7372-7383`) should list it too — not independently pinned, but the strict-param teaching error and discoverability make it de facto required.

### E.3 `agent=` resolution + the heartbeat touch

- Helper: `AgentRegistry._resolve_row(name, session) -> dict[str, Any]` — `agents.py:522-559`. With `session`: deterministic-id lookup `self._select_row(self._agent_id(session, name))` (`:539`) — **this deliberately DOES find a retired row**, so downstream raises a teaching `RetiredAgentError` rather than a confusing unknown-agent (`:526-527`). Without `session`: bare-name search over non-retired rows only (`:546-547`); 0 → `UnknownAgentError` (`:549-552`); >1 → `AmbiguousAgentError` naming candidate sessions (`:553-558`). Call sites: `agents.py:743` (`touch`) and `:701`.
- Unknown agent: `UnknownAgentError` (`agents.py:319-320`) propagates from `touch`, is caught at `server.py:4466-4467` and re-raised **enriched** via `_comms_enrich_unknown_agent` (`:4527-4545`), appending a capped/counted active roster (`_COVERAGE_NAMES_CAP = 5`, `:1112`) scoped to the SAME session. Packet 03's "unregistered recipient = teaching error" should route through this existing helper rather than minting a second one.
- **Heartbeat touch — ONE site, unconditional except `register`**: `server.py:4463-4465`, gated by `spec.requires_registration` (`:5420`; only `register` sets it `False` at `:5433`). `touch_status`/`touch_note` are populated ONLY when `action == _COMMS_ACTION_HEARTBEAT` (`:4460-4461`); every other action still touches, passing `status=None, note=None`. The comment at `:4364-4366` states the design: *"one site (not a decorator, not per-handler; a per-handler touch is the forgotten-wrap defect class P8d catalogued)."* `touch` (`agents.py:706-778`) always stamps `heartbeat_at`; status changes only on explicit `status=` or an idle→active auto-flip (`:753-759`).
- **For `send`/`drain`/`ack`: the touch is inherited automatically** unless the spec sets `requires_registration=False`. No extra wiring, and no other opt-out.

### E.4 The four structural pins — all TOOL-level, all in `tests/test_mcp_server.py`

Named as a set in `docs/design/2026-07-12-pkt28-c1-semantics.md:755-758`.

| # | pin | file:line | asserts | tripped by a new ACTION? |
|---|---|---|---|---|
| a | exact-set registration | `test_mcp_server.py:1048-1064` (`_ALL_BUILTIN_TOOL_NAMES:1034`) | `names == _ALL_BUILTIN_TOOL_NAMES` | **NO** — set is over tool NAMES; `lore_comms` already a member |
| b | dead-name hygiene | `:1092-1149` (`_TOOL_NAME_TOKEN = re.compile(r"\blore_[a-z_]+\b"):1120`) | every `lore_`-prefixed token in instructions, every tool `description`, AND every per-param `inputSchema` description names a LIVE tool | **NO**, unless prose accidentally writes e.g. `lore_send` |
| c | instructions-names-every-tool | `:1223-1236` | every name in `_ALL_BUILTIN_TOOL_NAMES` appears in `mcp.instructions` | **NO** — `lore_comms` already named |
| d | `_MUTATING_TOOLS` membership | constant `:1185`, checked `:1707-1714` | mutating tools not marked read-only (tool-level `ToolAnnotations`, `_COMMS_TOOL_ANNOTATIONS` at `server.py:6738-6740`) | **NO** |

**Net: adding an action does NOT trip the tool-count pin. The surface stays 15 tools.** The "14→15" in CLAUDE.md was the addition of the `lore_comms` TOOL itself (comment at `test_mcp_server.py:1032`), already landed.

### E.5 The ACTION-level pins that DO need touching — the ones that matter for packet 03

These are a distinct set from the four above, and they are where a new action actually gets policed:
- **Exact-action-set**: `test_comms_tool.py:300-303` — `_EXPECTED_ACTIONS` asserted equal to `set(_COMMS_ACTIONS)`.
- **Tool-description names every action**: `test_comms_tool.py:387-391`, against `tools["lore_comms"].description`.
- **Param honesty**: `test_comms_tool.py:393-408` — every spec's `params | required` must appear in the live tool's `inputSchema.properties`.
- **Render completeness, default-FAIL**: `assert_actions_covered` (`test_render_seam_pins.py:535-560`) invoked at `test_comms_tool.py:3623-3627` with `exemptions={}`, plus `test_every_action_has_at_least_one_registered_case:3629-3631`. Every action needs ≥1 `RenderCase("<action>.<field>", …)` in `C1_RENDER_CASES` (`:3583-3602`) or a non-blank exemption. **Coverage is per action FAMILY (`label.split(".",1)[0]`), not per field — so a new agent-controlled field on an EXISTING action is NOT force-registered. A wholly new action IS, and fails loudly by name.**
- `test_mcp_server.py:7839-7853` is documented at `:7845-7851` as explicitly NOT auto-detecting a new comms render — it defers to `assert_actions_covered`.

### E.6 Return-value shape

Every handler and render helper is typed `-> Rendered` (`server.py:4385`, `:4559`, `:4589`, `:4759`). `Rendered` is `class Rendered(str)` (`render.py:95-105`). Enforcement is the four-instrument story at `render.py:10-72`: (1) mypy strict on value/return legs — a raw f-string returned from a `-> Rendered` function is rejected, pinned by the subprocess-mypy meta-test; (2) the AST template-literal pin; (3) a runtime control-char assert inside `render_line`/`render_join` raising `RenderSafetyError` (`render.py:108-122`); (4) the AST mint pin forbidding `Rendered(...)`/`cast(Rendered, ...)` outside `render.py`/`sanitise.py`.

The outer MCP wrapper is typed `-> str` (`server.py:7497`) — satisfied because `Rendered` IS a `str`. **`lore_comms` returns plain text, not a pydantic model** — it is absent from `_TOOL_OUTPUT_FIELDS` (`test_mcp_server.py:1731-1753`), unlike `lore_search`/`lore_verify`.

---

## F) TEST HARNESS

### F.1 `unique_database()` — `tests/_surreal_harness.py:130-137`

```python
def unique_database() -> str:
    """A per-test database name unique to this process (``test_<pid>_<uuid4>``)."""
    return f"test_{os.getpid()}_{uuid.uuid4().hex}"
```
A **plain sync name-minter** — not a fixture, not a context manager. Callers build a `SurrealEnv` via `make_env(database=unique_database(), dim=…)` (`:161-170`).

Two `pytest_asyncio` fixtures own the lifecycle: `surreal_env()` `:379-396` (production dim 2048; creates via `connect_admin`, reaps via `drop_database` in a `finally`) and `admin_db()` `:399-413` (yields `(raw_connection, env)` at `NONDEFAULT_DIM` 512, for DDL-generator tests).

**Ledger contract tests do NOT use `surreal_env`** — they hand-roll a `*_ledger_factory` fixture, because pytest-asyncio 1.4's Runner reentrancy forbids resolving one async fixture from inside another's body (documented at `test_task_ledger.py:252-264`). A builder cloning the pattern must know this or will fight the framework.

A test receives the **ledger object**, not a bare connection, in the common case. Teardown is always `REMOVE DATABASE IF EXISTS` via a **fresh** admin connection (`drop_database:290-305`) — deliberately independent of the test's own connection, since a resilience test may have killed it. The REMOVE itself retries up to `_MAX_DROP_DATABASE_ATTEMPTS = 5` (`:106`) on the `"can be retried"` marker (`_remove_database_with_retry:260-287`), linear backoff `0.01s * attempt` (`:112`), unjittered (one waiter).

> ⚠ **SUPERSEDED BY #150 (2026-07-20) — the paragraph above is left as written, because it
> correctly records the world of 2026-07-19; it is no longer true of the code.** All four of
> its teardown claims are dead. Three names were **deleted outright** —
> `_MAX_DROP_DATABASE_ATTEMPTS`, `_DROP_DATABASE_BACKOFF_SECONDS`, and the private
> `"can be retried"` marker copy. **`_remove_database_with_retry` still EXISTS**
> (`_surreal_harness.py:363`, called from `drop_database`): what was deleted is its private
> retry LOOP — it now delegates budget, backoff and conflict classification to the shared
> seam. The harness now owns no conflict-retry policy of its own: teardown and
> `connect_admin` both route through the ONE shared seam
> (`loremaster/loremaster/store/_txn.py` — `bootstrap_session` / `retry_on_conflict` /
> `is_retryable_conflict_error`), so budget, backoff and marker are the seam's, and the
> backoff is now **jittered** — the old "one waiter" premise was false under the standing
> `-n auto` runner, where teardown has one waiter *per worker*. Do not cite this paragraph
> for current behaviour; read `_surreal_harness.py` and finding #150.

### F.2 The `[real]` tier — NOT a pytest marker

**There is no `markers =` list anywhere in the repo** (`pyproject.toml:107-118` is the full `[tool.pytest.ini_options]`). `[real]` is the **auto-generated parametrize id**: every ledger contract file declares

```python
@pytest_asyncio.fixture(params=["real", "fake"])
```
(`test_task_ledger.py:240`, `test_brief_ledger.py:188`, `test_findings.py:224`), and with no explicit `ids=` pytest uses the param strings verbatim — hence `test_x[real]` / `test_x[fake]`. **`test_agent_registry.py` has no such fixture — it is real-only, with no fake parity leg.**

**There is NO skip-when-unavailable mechanism, by design.** `_surreal_harness.py:12-14`: *"An unreachable server is a LOUD failure (the fixture raises), never a silent skip."* The only `pytest.skip(` calls in the tree are `test_server.py:119,206` (missing XML fixture) and `test_schema_rebuild.py:1832` (MCP SDK import shape) — none store-related.

Env-driven topology (`_surreal_harness.py:56-63`), resolved by `surreal_url()`/`surreal_user()`/`surreal_password()` (`:115-127`):
`LORE_TEST_SURREAL_URL` / `_USER` / `_PASS`, defaulting to `ws://127.0.0.1:18000/rpc`, `root`, `spikeroot` — i.e. **spike-surreal, never production :18500.**

### F.3 The worked example to clone

`test_brief_ledger.py:188-234` is the canonical factory-fixture form: `params=["real","fake"]`; on `real`, `make_env(database=unique_database(), dim=PRODUCTION_DIM)` → `connect_admin(env)` → close → an inner `async def make()` that constructs the ledger with the five kwargs, `await ledger.ensure_ready()`, appends to `created`; on `fake`, a shared `FakeBriefDatabase` + `FakeBriefLedger` cast to the real type. `finally`: close every created ledger, then `drop_database(env)` if real. A thin `brief_ledger` fixture (`:230-234`) just calls the factory.

The act/assert form is `test_brief_ledger.py:237-248` (`TestPublishFirstVersion`), with `_assert_recent_utc(result.brief.created_at, not_before=before, not_after=after)` bracketing the timestamp between two locally-taken `datetime.now(UTC)` reads.

**A `messages.py` test file clones this skeleton**, adding a `FakeMessageDatabase`/`FakeMessageLedger` pair (the comms fakes live in `tests/_comms_fakes.py`).

### F.4 Concurrency pins — ⚠ CORRECTION TO THE BRIEF'S ASSUMPTION

**`test_txn_contention.py` (774 lines) contains ZERO `asyncio.gather` calls and ZERO live N-way races.** It pins the *typed* `TxnContentionExhaustedError` seam using a scripted fake (`_SustainedConflictConnection:177-224`) answering every `query_raw` with a canned conflict shape — it tests error classification and propagation, not concurrency degree. **It is not the model for packet 03's ≥8-way pins.**

The real ≥8-way live pins are:
- **`test_findings.py`** — `_CONCURRENT_REPORTS = 8` (`:148`), `_CONCURRENT_REPORTS_AT_SCALE = (16, 32)` (`:155`). `TestConcurrentNumbering.test_concurrent_reports_get_distinct_consecutive_numbers:477-500` races **8 separate ledger instances (separate live connections, not coroutines on one socket)** via `asyncio.gather`; `…_at_scale:502-539` is `@pytest.mark.parametrize("reporters_count", _CONCURRENT_REPORTS_AT_SCALE)` → 16 and 32.
- **`test_brief_ledger.py`** — `_CONCURRENT_PUBLISHERS = 8` (`:142`), `TestConcurrentPublishesLandDistinctVersions:285-317`, 8 separate `BriefLedger`s gather'd, asserting gapless consecutive versions.

**The separate-instance detail is load-bearing**: N coroutines on ONE connection do not contend the way N connections do.

**The "20 consecutive" rule has TWO distinct meanings — do not conflate them.** (a) In-test iteration: `_RACE_ITERATIONS = 20` (`test_findings.py:159`, `test_task_ledger.py:127`), consumed as `for iteration in range(_RACE_ITERATIONS): … await asyncio.gather(…)` at `test_findings.py:971` and `test_task_ledger.py:570,1006,1102,1247,1327` — each iteration builds a fresh race and re-asserts, all in one test function. (b) The CLAUDE.md rule *"a lone green run never clears a concurrency test"* is a **separate manual practice** — the whole suite run 20× (`scratchpad/102-recovery/DESIGN-102-final.md:182`: *"20 consecutive greens under `-n auto`"*). **No pytest-repeat/rerun/flaky plugin is installed** (dev deps `pyproject.toml:15-27` are only `pytest`, `pytest-asyncio`, `pytest-xdist`). So (b) is a lead/builder discipline with no mechanical enforcement — worth the lead knowing before it is assumed automatic.

`test_agent_registry.py` has no race/concurrency classes at all.

### F.5 The parallel runner

`pytest-xdist` is a dev dep; the safety argument is the comment at `pyproject.toml:19-23` — `unique_database()`'s `test_<pid>_<uuid4>` naming means no cross-worker collision. **No `@pytest.mark.xdist_group` usage anywhere** (zero hits). Order-sensitive tests spawn a **fresh serial subprocess** instead of grouping — `test_caplog_isolation.py:110-140` launches `sys.executable -m pytest <this file>::TestTheLeak -p no:randomly -q` precisely because *"the outer `-n auto` shard lottery cannot split it"*.

**Four autouse fixtures in `conftest.py` every new test inherits automatically**: `_dummy_anthropic_api_key:37-48`, `_reset_cosine_floor_drift_state:51-79`, `_restore_lore_logger_propagation:82-117`, and critically **`_no_sdk_call_escapes_the_retry_driver:197-211` — the runtime SDK guard from §B**. It is suite-wide, unconditional, with no opt-out and no xdist interaction. **A new `MessageLedger`'s raw `.query()` calls must route through the `_txn` seam or this autouse gate fails them.**

### F.6 Existing comms test files

| file | lines | covers | new message-graph tests belong…? |
|---|---|---|---|
| `test_comms_schema.py` | 1534 | S1: pure DDL generators (`generate_agent_ddl`/`generate_brief_ddl`) — offline DDL-string pins + live `INFO FOR DB`/`INFO FOR TABLE`. Explicitly NOT ledgers or dispatcher. | **yes** — the `message`/`to` DDL slice pins |
| `test_comms_tool.py` | 3696 | S3: the `lore_comms` surface — `_COMMS_ACTIONS` dispatch, `AppContext.comms` algorithm, six `_render_comms_*` helpers, hostile-render battery. Uses injected fakes (`_comms_fakes.py`), deliberately bypasses a full `AppContext`. | **yes** — `send`/`drain`/`ack` dispatch + renders + `C1_RENDER_CASES` |
| `test_brief_ledger.py` | 1816 | S2: `BriefLedger` — publish/version/get_head/ack/coverage/self-ack; `[real]`+`[fake]`; 8-way concurrent-publish pin | the shape to clone |
| `test_agent_registry.py` | 971 | S2: `AgentRegistry` — register/re-register/touch/fleet/status machine. Real-only. | — |
| `test_task_ledger.py` | 2109 | pre-C1 seam: `TaskLedger` create/claim/transition/supersede; `[real]`+`[fake]`; 20-iteration race pins | the race-pin shape to clone |

**No message-graph test file exists** (`find -iname "*message*"` under `loremaster/` → zero hits), and `surreal_schema.py` has no `MESSAGE_TABLE`/`generate_message_ddl`. Confirms packet 03 is genuinely unbuilt.

### F.7 DDL application in tests — two patterns

1. **Schema-generator tests** apply DDL directly via `admin_db` + the `run()` helper — `test_comms_schema.py:627-630`: `connection, _env = admin_db` → `await run(connection, generate_agent_ddl())` → `await run(connection, "INFO FOR DB")`.
2. **Ledger contract tests never call `generate_*_ddl` themselves** — the production class applies its own slice inside `ensure_ready()` (`briefs.py:463-483`), invoked by the factory's `make()` (`test_brief_ledger.py:209`). That is where DDL lands on the throwaway DB, idempotent per the `IF NOT EXISTS`/`OVERWRITE` rules.

A `MessageLedger` follows pattern 2; a `message`-slice DDL test follows pattern 1.

---

## G) FLAGS — things I noticed that are not in my brief (operator/lead decides, not me)

1. **The `generate_ddl()` registration gap (§C.2) is real and already has two live instances** — `finding_counter` and `brief_counter` are emitted/created but absent from the subset pins. Finding #124 treats this as load-bearing against silent data loss. A `message`-slice landing outside both `generate_ddl()` and the pins would make three.
2. **The dangling-edge hazard (#105) is unguarded, and its guard is scheduled for packet 04 — one packet AFTER the code that creates the exposure** (§C.4). Packet 03's `to` fan-out writes edges from caller-supplied recipient identities. Sequencing question for the operator.
3. **Renders placed in `messages.py` rather than `server.py` silently escape three of the five render scanners** (§D.3). No registration path exists; the path is a bare string constant in two test files.
4. **The `_render_comms`/`_comms_` NAME PREFIX is load-bearing** (§D.3) — a correctly-shaped helper named otherwise is scanned by nothing. This is exactly the "keyed on a name" defeat class CLAUDE.md catalogues six times.
5. **Pinned bound `test_KNOWN_BOUND_a_promise_carried_in_a_render_VALUE_is_not_inspected` (§D.4)** has a re-open trigger that a numbered drain list could plausibly pull. Worth checking BEFORE the drain render is designed, not after.
6. **`_MIN_KNOWN_SEAMS = 10` (§B.3)** — a new ledger makes 11. It reads as a floor, but the builder should confirm it is not an equality assertion.
7. **The "20 consecutive greens" law has no mechanical enforcement** (§F.4) — no repeat plugin is installed. If the lead expects it automatically, it will not happen.
8. **Packet 03 introduces two mechanisms with NO existing pattern to clone**: `DEFINE SEQUENCE`/`sequence::nextval` and `ulid()` ids (§C.6, §A.1). Both are spec'd, neither is precedented in this tree — per the repo's routing rule, "a property to invent" is design work, not builder work.
