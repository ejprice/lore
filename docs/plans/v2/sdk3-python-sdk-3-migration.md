# Packet SDK3 — Python SDK `surrealdb` 2.0.0 → 3.0.0 (on the 3.3.5 stores)

Status: DISCOVERY + CONTRACT (tdd Phase 0 + Phase 1), written 2026-11-07 by the SDK3 contract author
against HEAD `4624daf` (branch `feat/surreal-unification`; the brief named `c05bf3f`, HEAD moved
under another builder's commit while this ran), SDK 2.0.0 in lore's venv, SDK 3.0.0 in the
research40 scratch venv. Operator approved the packet 2026-11-07. **This contract STOPS for operator
review** (§5 forks); then `contract-adversary` grades it, then a builder implements.

Inputs: `docs/research/2026-11-07-surrealdb-3.3-4.0-for-lore.md` (SUMMARY, §B4–B6/B18, §C, §D-4/D-10,
§E 7/11/12), finding #576, `docs/reference/surrealdb-31-capabilities.md` §0a/§2/§3/§6.5.

## SUMMARY

- **Headline:** besides the expected `query()` list-per-statement break, SDK 3.0 **renders every
  digit-led record key in angle brackets** (`keep:01J…` → `keep:⟨01J…⟩`). lore splits that rendering
  on `:` to look records up again, to bind the PrincipalStore refuse-while-keeping guard, and to build
  the `keep:<id>` scopes it PERSISTS on governed rows. Every keep id (a ULID) and ~28% of
  engine-minted principal ids have that shape. A build that only fixes the result shape ships: keeps
  unfindable by their own id, a keeper principal deletable while keeping, and scopes that no longer
  match pre-bump rows (those rows go dark). Pinned (§4 R7–R9); measured RED on SDK 3.0 + shape fix.
- **#576 is fixed by SDK 3.0's background reconnect**, measured across all 18 connection owners
  through a bounce proxy: RED at HEAD with #576's own text, GREEN on SDK 3.0 with NO lore change (§4 L1).
- **Unmodified lore on SDK 3.0 is dangerous, not just broken:** a lost compare-and-set reads `[[]]`
  (truthy), so **8 of 8** racers "won" one claim (measured); the inbox LIVE wake never attaches
  (`subscribe_live([uuid])`), silently degrading `await` to its poll.
- Contract: 3 test files + 1 fixture module, **28 pins**. HEAD: 23 GREEN (preserved-with-pin),
  5 RED for the right reason (3 = #576 itself: L1×2, L2; 1 = fork F2: L6; 1 = fork F3: R6b) — §4.
- Gate: `--currency --legs typecheck,ruff` RED_ORPHANED 0 (typecheck RED_ADJUDICATED to packet-58,
  ruff GREEN). **The RED pins could NOT be registered** in `scripts/pending_contracts.yaml`: the
  registry has no shape for a pytest-only RED (fork F6).

## 0. Routing table (written before the first sweep)

| step | tier | who | reason |
|---|---|---|---|
| S1 literal call-site sweep (12 categories) | 1 | `haiku-worker` | brief-routed; exact `git grep` patterns, coverage line per category |
| S2 classify each production hit against SDK 3.0's breaks | 3 | me (inline) | brief-routed inline: a verdict depends on what SDK 3.0's source does at that call shape (state outside the hit's span) |
| S3 read SDK 3.0 source (reconnect, errors, query/query_raw, RecordID, PreciseDatetime) | 3 | me | critical path; must read installed source, not a digest |
| S4 read lore's classification seams (`_txn`) and connection owners | 3 | me | the removed-behavior inventory is judgement per branch |
| S5 test runs (HEAD satisfiability; SDK 3.0 shadow runs) | 1 | `haiku-runner` ×6 | receipts; my own debug iterations ran inline (deviation, below) |
| S6 gate `--currency --legs typecheck,ruff` | 1 | `haiku-runner` ×2 | gate run |

Fan-out: haiku 7 (1 worker, 6 runners) · sonnet 0 · peak 4. Deviation: debugging iterations of the
new pins (≈12 short targeted runs) ran inline on the critical path; every receipt in §6 is a runner's.
lore MCP was DOWN (corpus re-index): **grep fallback for every structure question**, per brief no
friction filed. One sweep-instrument defect caught: the worker's C4 pattern (`[…\]]` inside a bracket
class) matched 1 line where the corrected pattern matches 1090 — a no-op sweep reading as "1 hit";
re-run inline and the file replaced.

## 1. Discovery sweep (tdd Phase 0)

Instrument: `git grep -n -E` per category over `loremaster lorerunes lorescribe loresigil scripts
skills conftest.py`, `*.py` only. Coverage: `files_scanned=482` = `git ls-files` count (324+14+27+35+63+18+1).
Raw hits: session scratch `scratchpad/sdk3/sweep_C*.txt` (runner script `scratchpad/run_sdk3_sweep.sh`).

| cat | pattern (abridged) | files | hits | production hits (non-test, non-scripts) |
|---|---|---|---|---|
| C1 import | `(from\|import)\s+surrealdb` | 86 | 97 | 21 (17 owners import `AsyncSurreal`; `RecordID` ×14; `InvalidRecordIdError` ×2; `_txn` imports `AsyncEmbeddedSurrealConnection`, errors) |
| C2 `.query(` | `\.query\(` | 44 | 270 | 10 → **5 SDK sites**: `_txn.run_query`, `_txn.bootstrap_session` ×2, `scout._scout_query_once` ×2, `inbox_awaiter._live_query` (rest: `FindingLedger.query` / docstring) |
| C3 `.query_raw(` | `\.query_raw\(` | 17 | 36 | 1: `_txn._txn_query_raw` |
| C4 await SDK verb | `await <recv>.(select\|create\|…\|use\|signin\|close\|kill…)(` (corrected) | 163 | 1090 | SDK receivers: `signin` ×17 (one per owner), `use` ×1 (`bootstrap_session`), `kill` ×2 (scout, awaiter), `close` ×19; **no `select/create/update/upsert/merge/delete/insert/relate` on a connection anywhere in production** |
| C5 client ctor | `Surreal\|AsyncSurreal\|*SurrealConnection` | 68 | 256 | `AsyncSurreal(self._url)` in 17 owners + `scout._open_command_connection`; no blocking client in production |
| C6 RecordID/Table | `\bRecordID\|StringRecordId\|Table\b` | 87 | 495 | 182; the load-bearing ones: `str(RecordID)` served as ids and split on `:` (`keeps._record_id_part`/`_resolve_principal_id`, `principal_keys._record_id_part`, `principals.delete` / scope builders ×4), `audit` `target_row`, `RecordID.parse` (`diff`, `snapshots`) |
| C7 SDK error names | `ServerError\|QueryError\|…\|ConnectionClosed*` | 66 | 382 | all SDK-error decisions live in `store/_txn.py`; elsewhere only pydantic `ValidationError` (false hits) |
| C8 websockets | `websockets` | 5 | 33 | 1: `_txn` imports `WebSocketException` |
| C9 broad except | `except … (KeyError\|OSError\|…)` | 54 | 129 | 24; SDK-relevant: `_txn` `(*_CONNECTION_ERRORS, KeyError)` ×2; the rest are file/OS handling |
| C10 datetime | `isinstance(…datetime\|fromisoformat\|.isoformat(\|…` | 55 | 150 | 63; every type check is `isinstance(value, datetime)` (6 cloned coercers: agents, briefs, findings, messages, principals, tasks) — no `type(x) is datetime` |
| C11 result shape | `["result"]\|["status"]\|"ERR"` | 41 | 189 | 13: `_txn` (`execute_read_transaction`, `_failed_statements`) |
| C12 conn owner | `def _ensure_connection\|…` | 42 | 123 | **18** `_ensure_connection` owners (17 store/ledger classes + `scout.CommandSubscriber`) |

### 1.1 Classification against SDK 3.0's breaking changes (source read at v3.0.0)

| SDK 3.0 change | lore sites hit | effect if unaddressed (measured = shadow run §6) |
|---|---|---|
| `query()` returns one entry PER STATEMENT (a sync method returning an awaitable builder) | `run_query` (every owner's `_query`), `scout._scout_query_once`, `inbox_awaiter._live_query`, `bootstrap_session` (discards), test harness `run()` | **measured**: rows `[[…]]`, scalar `[42]`, lost CAS `[[]]` truthy → 8/8 racers win; `LIVE SELECT` id `[uuid]` → `subscribe_live` keys on `"[UUID(…)]"`, wake never fires; counter reads `[[32]]` |
| digit-led record keys render `⟨…⟩` (SDK 2.0: bare) | every `str(RecordID)` that is served or split: keeps, principals, principal_keys, audit `target_row`, agent_existence's render-match | **measured**: `keep:⟨01J…⟩`; `principal:⟨4558…⟩`; §2.3 |
| `RecordID` now hashable; `RecordID.parse("x:y")` no longer raises | `diff._parse_snapshot_id`, `snapshots.delete_snapshot` catch `InvalidRecordIdError` | spec-silent: which malformed ids still raise was not enumerated (inventory I-9) |
| datetimes decode as `PreciseDatetime` (a `datetime` subclass, `.nanosecond` kept; `__eq__`/`__hash__` NOT overridden) | 63 production datetime sites, all `isinstance` | **measured** GREEN: equality, ordering, ISO, pydantic JSON; and the nanoseconds now round-trip (fork F3) |
| error split `ServerError` / `TransportError` (`ConnectionUnavailableError`, `TransportTimeoutError`) | `_txn.is_connection_error`, `_CONNECTION_ERRORS`, `_SDK_AWAIT_BOUNDARY_ERRORS` | non-`ServerError` → transport already; `KeyError`/websockets branches go dead (inventory I-1/I-2) |
| request **timeout 30 s by default** (2.0: none) | every SDK call | a statement > 30 s becomes `TransportTimeoutError` → classified transport → `drop` → `SurrealConnectionError` while the statement may still commit server-side (fork F4) |
| auto-reconnect ON (5 attempts, 2/4/8/16/32 s backoff), replays auth/ns/db, NOT `query()`-made LIVE | all 18 owners (`AsyncSurreal(url)` defaults) | **measured** fixes #576 for idle owners; long outage parks a call on the backoff (fork F2) |
| `query_raw` STREAMS on a ≥3.3 server, rebuilt to the buffered shape | `_txn._txn_query_raw` | **measured** GREEN: per-statement `kind`/`details` intact (conflict retry, cascade selection, positional results) |
| `query()` raises on a LATER failed statement (cascade `NotExecuted` in a txn) | none in production (multi-statement rides `execute_transaction`) | statement[0]-only gap closes for any stray `query()` (inventory I-4) |
| top-level `AsyncEmbeddedSurrealConnection` moved (needs `surrealdb-embedded` extra) | `_txn` import + type alias; `test_retry_seam._SDK_CONNECTION_CLASSES` | **measured**: lore does not import (`ImportError`) |
| `query`, `select`, `create`, `update`, `upsert`, `delete`, `insert`, `relate` are no longer coroutine functions | `tests/_sdk_guard.py` wraps only `inspect.iscoroutinefunction` members | the runtime SDK-escape guard silently loses reach over `.query()` and its multi-statement check (fork F5) |
| plain `"t:id"` string is a TABLE | no production CRUD-method call takes a string target (C4) | none in production; scripts unchecked one by one (§7) |

### 1.2 Packages considered
`surrealdb` 3.0.0 (the migration target; read: `errors.py`, `connections/async_ws.py`
`_request`/`query`/`query_raw`/`_may_stream`/`subscribe_live`/`_run_reconnect`, `connections/reconnect.py`
`ReconnectOptions.delay`, `data/types/datetime.py`, `data/_decoder.py`) — verdict for the fixture
mechanism: `bespoke` for the bounce proxy (no SDK/test package simulates a server restart in-process;
`asyncio.start_server` is the package doing the work); reconnect itself `replace` (SDK 3.0's
`ReconnectOptions` replaces lore's one-failed-call self-heal for idle owners).

## 2. Findings beyond the research doc

### 2.1 Unmodified lore on SDK 3.0 (measured, `scratchpad/sdk3/receipts/sdk3_plain_contract.log`)
lore does not even import (`AsyncEmbeddedSurrealConnection`); with that one name shimmed, 16 of 28
pins go RED, each for the intended reason (list-per-statement shape, LIVE not attached, render).

### 2.2 The record-key rendering change (NEW — not in the research doc)
SDK 2.0 bracketed a key that was all digits or held a non-word character; SDK 3.0 also brackets
**any key starting with a digit**. lore mints keep ids as `str(ULID())` (today every ULID starts with
`0`/`1`), and the engine mints principal ids from `[a-z0-9]` (~10/36 digit-led). Consequences if a
build keeps rendering through the SDK:
1. `KeepStore.get_keep(keep.id)` misses (`type::record('keep', '⟨01J…⟩')` names another key) — and
   `create_keep` returns "read back through get_keep".
2. `PrincipalStore.delete`'s refuse-while-keeping read binds the wrong principal key, finds no kept
   keep, and deletes the keeper (a dangling `keep.keeper`) — **measured** the served id
   `principal:⟨4558tcyfmwp3lj775pwi⟩`.
3. `keep_scope(keep.id.partition(":")[2])` becomes `keep:⟨01J…⟩`; rows written before the bump carry
   `keep:01J…`, so governed reads filtered by the new scope stop seeing them (**inferred**, not probed:
   it follows from 1 and the scope builder; R8/R9 pin the root).
4. Any `str(RecordID)` persisted as a value (`audit.target_row`) compares unequal across the bump.

### 2.3 Instrument (verbatim, run under both venvs with `-I`)
```python
"""Offline: str(RecordID(table, key)) per SDK version for key shapes lore mints or admits."""
import importlib.metadata, uuid
from surrealdb import RecordID
keys = ["01JCXZ3Q9V8M2T5K7R4N6P1W0Y", "0abc", "9", "123", "abc", "abc123", "a0", "_x", "x_y", "ABC", "e1", "1e5", "0x1f", "café", "inf", "NaN", "true", "none", str(uuid.uuid4().hex), "z0ysb7r5es9"]
print("sdk", importlib.metadata.version("surrealdb"))
for k in keys:
    print(f"{k!r:34} {str(RecordID('t', k))}")
```
Differs (2.0 → 3.0), measured 2026-11-07: `01JCXZ…` → `⟨01JCXZ…⟩`, `0abc` → `⟨0abc⟩`, `1e5`, `0x1f`,
a digit-led hex digest, `café` → `⟨café⟩`. Same: `9`/`123` (bracketed by both), `abc`, `abc123`, `a0`,
`_x`, `x_y`, `ABC`, `e1`, `inf`, `NaN`, `true`, `none`, `z0ysb7r5es9`, uuid strings (bracketed by both).

### 2.4 Other observations (raised, not in this packet's scope unless ruled)
- `scout.CommandSubscriber._drop_connection` is an unconditional null (no compare-and-swap like the 17
  store owners), and takes no argument — the only owner whose drop does not fit `run_query`'s `drop`.
- Six modules carry a cloned datetime coercer (`isinstance(value, datetime)` … `fromisoformat`) —
  a ONE-IMPLEMENTATION question, pre-existing.
- Several owners' served ids are re-parsed by `partition(":")` in four modules — a policy (how a served
  id names its key) with no single owner; SDK 3.0 is the second time it bit (#248 was the first).

## 3. Removed-behavior inventory (SDK-2.0-shaped behaviours lore depends on)

| # | behaviour (where) | fate | pin / reason |
|---|---|---|---|
| I-1 | in-flight drop raises raw `builtins.KeyError(uuid)`; `_SDK_AWAIT_BOUNDARY_ERRORS` and both driver `except`s catch `KeyError` as transport | **dropped-deliberately** (SDK 3.0 raises `ConnectionUnavailableError`, a `SurrealError`); the property it served is **preserved-with-pin** | L3: every call in flight at a drop raises `SurrealConnectionError`. Whether the `KeyError` arm is deleted is the builder's call — its catch must stay narrow to the SDK await (it wraps nothing else today) |
| I-2 | `websockets.ConnectionClosed*` / `WebSocketException` classified transport (`_CONNECTION_ERRORS`) | same as I-1: SDK 3.0 wraps send failures as `ConnectionUnavailableError`; the property **preserved-with-pin** (L3, L1 both sever shapes) | — |
| I-3 | `ServerError.kind == NotAllowed` → transport (the "silently reconnected unauthenticated" socket, `_CONNECTION_ERROR_KINDS`) | **preserved** — SDK 3.0 replays auth on reconnect, but after the attempts run out `_give_up` clears session state and the next request runs on a fresh socket unauthenticated (source read, `async_ws._run_reconnect`); unprobed live (research §E-7). Existing pins: `test_retry_seam` bootstrap-fate rows. **spec-silent→operator** whether to probe a >62 s outage (fork F2 decides the attempt budget, which decides reachability) | — |
| I-4 | `query()` validates statement[0] only → multi-statement SQL must ride `execute_transaction` (store ref §3, §6.5; `_sdk_guard` multi-statement check) | **old-bug** (the SDK now raises on any failed statement) — not re-pinned; the house rule stays (it also buys root-cause selection) | T2 covers the transactional path |
| I-5 | `query()` returns the FIRST statement's result | **preserved-with-pin** at `run_query` (the ONE single-statement driver every `_query` calls) | R1–R4; T-pins read counters through it |
| I-6 | `query_raw` buffered per-statement dicts (`status`/`result`/`kind`/`details`) | **preserved-with-pin** (streamed on ≥3.3, must rebuild identically) | T1 (conflict typed in `details`), T2 (cascade vs root), R5 (positions) |
| I-7 | `details.kind == "TransactionConflict"` read by `_detail_kind` (2.0 had no predicate; 3.0 has `QueryError.is_transaction_conflict` and unwraps 3.0.0's double-wrapped details) | **preserved-with-pin** (T1 both paths at 16-way, T3 text never buys a retry); replacing the literal with the SDK predicate is spec-silent (research §C recommends it) | T1, T3, T4 |
| I-8 | cascade selection `_is_domain_cascade_notice` (SDK `is_not_executed`/`is_cancelled`) | **preserved-with-pin** | T2 ×3 positions |
| I-9 | `RecordID.parse` raises `InvalidRecordIdError` on malformed input (`diff._parse_snapshot_id`, `snapshots.delete_snapshot`) | **spec-silent→operator**: 2.0 raised on `x:y`-in-key / dict-literal shapes, 3.0 parses them; which snapshot ids now parse that did not was not enumerated | not pinned (fork F7) |
| I-10 | `str(RecordID)` renders digit-led keys bare | **preserved-with-pin** (served ids and persisted scopes depend on it) | R7, R8, R9 |
| I-11 | datetimes decode as plain `datetime`, truncated to µs | equality/ordering/ISO/JSON **preserved-with-pin** (R6); the truncation itself **spec-silent→operator** (fork F3) | R6, R6b |
| I-12 | no client request timeout (a statement may run as long as the engine takes) | **spec-silent→operator** (fork F4) | not pinned |
| I-13 | no reconnect: a dead socket stays dead until lore's `drop` | **dropped-deliberately** — this IS #576 | L1, L2 |
| I-14 | `subscribe_live(uuid)` yields `result` only; generator ends on close | consumers treat notifications as contentless wakes — **preserved-with-pin** at the behaviour (R10) | R10 + control |
| I-15 | a `query()`-made LIVE is lost on reconnect (2.0: everything is lost) | **preserved** (poll fallback mandatory; SDK 3.0 does not replay it either) | existing `test_comms_await` fakes |
| I-16 | `AsyncEmbeddedSurrealConnection` importable from `surrealdb` | **dropped** (builder: import from its new home or drop it from the alias) | import failure is loud |

## 4. Contract index

Files: `loremaster/tests/test_sdk3_lifecycle.py`, `test_sdk3_txn_classification.py`,
`test_sdk3_result_shapes.py`, fixture `loremaster/tests/_sdk3_proxy.py` (`StoreBounceProxy`: an
in-process TCP proxy in front of `:18000` that plays a restart — stop listening, sever every socket
by RST or by a status-less WS close frame, listen again on the same port; it COUNTS accepted/severed/
live sockets so every pin proves its own premise). Columns: HEAD = SDK 2.0 at `4624daf`; SDK3 =
unmodified lore + the moved-name shim; SDK3+U = additionally `query()` answering the first statement
(SDK 3.0's own `.first()`), the minimal correct shape adaptation.

| id | pin | behaviour | HEAD | SDK3 | SDK3+U |
|---|---|---|---|---|---|
| L0 | `TestTheOwnerSetIsNotSilentlySmall` | the derived owner set (`_discover_bootstrap_owners`) ≥ 14 | G | G | G |
| L1 | `…FirstCallAfterAStoreBounce::…after_a_bounce[abort]`, `[close_frame]` | all 18 idle owners answer their FIRST call after a bounce; premise checks: each owner held a proxied socket, the bounce severed ≥18, recovery opened ≥18 new sockets | **R** (#576 text "no close frame received or sent"; 1005) | G | G |
| L2 | `…two_bounces_in_a_row` | recovery is repeatable | **R** | G | G |
| L3 | `…RacingTheDrop…raises_SurrealConnectionError` (+ positive control `…succeed_when_nothing_is_cut`) | 8 calls in flight at an RST each raise `SurrealConnectionError` within 20 s — no value, no domain error, no hang | G | G | G |
| L4 | `…next_call_succeeds_and_no_stale_socket_survives` | after the racing failure the next call succeeds first time; 7 s later exactly ONE live socket (no zombie reconnect of the dropped connection) | G | G | G |
| L5 | `TestAClosedOwnerStaysClosed` | after `close()`, a bounce opens no socket within 7 s | G | G | G |
| L6 | `TestRecoveryLatencyAfterALongOutage` (**fork F2**) | 1 s after a 15 s outage ends, the first call answers within 6 s | **R** | R (parked on backoff) | R |
| T1 | `…read_modify_write_transactions_all_commit_once` | 16 racers × 2 rounds of BEGIN/LET/UPDATE/COMMIT: none fails, counter == 32, attempts > 32 (premise: conflicts happened) | G | R (shape) | G |
| T2 | `…single_statement_updates_all_commit_once` | the same at the single-statement path | G | R (shape) | G |
| T3 | `…a_throw_anywhere…[first\|middle\|last]` | a THROW at any position: `TxnDomainRejectionError`, `.kind == "Thrown"` (never a cascade kind), 1 attempt, nothing committed | G | R (rollback check reads `[[]]`) | G |
| T4 | `…quoting_the_conflict_text_is_still_not_retried` | text never buys a retry | G | G | G |
| T5 | `…single_statement_throw_is_not_retried` | single-statement THROW: kind `Thrown`, 1 attempt | G | G | G |
| R1 | `…a_select_returns_its_rows` | `run_query` returns the statement's rows | G | R | G |
| R2 | `…a_scalar_return_is_the_scalar` | `RETURN 42` → `42` | G | R | G |
| R3 | `…lost_compare_and_set_is_empty…` | lost CAS `== []` and falsy; won CAS one row | G | R (`[[]]`) | G |
| R4 | `…exactly_one_of_eight_racing_claims_wins` | 8 owners race one CAS: exactly one winner | G | **R (8 of 8 won)** | G |
| R5 | `…results_line_up_with_the_composed_statements` | `execute_read_transaction` results at composed positions | G | G | G |
| R6 | `…written_datetime_reads_back_equal_ordered_and_serialisable` | equality, engine order == Python order, UTC, ISO and pydantic JSON round trips | G | R (shape) | G |
| R6b | `…server_stamped_datetime_matches_its_own_row_when_bound_back` (**fork F3**) | a server stamp read back and re-bound matches its own row (5/5) | **R** (µs truncation) | R (shape) | G |
| R7 | `…every_minted_key_shape_round_trips` | ULID / engine-style digit-led / letter-led / uuid5 / path / int keys: type, table, key, symmetric render, and SDK-2.0 rendering | G | R | **R (render)** |
| R8 | `TestTheIdLoreServesNamesTheEnginesKey` | `Keep.id == "keep:<engine key>"`; `get_keep(keep.id)` finds it | G | R | **R (render)** |
| R9 | `TestAKeeperCannotBeDeletedWhileKeeping…` | a digit-led keeper principal (minted until the engine yields one, ≤40) is refused deletion while keeping | G | R | **R (render)** |
| R10 | `…relate_to_the_waiting_agent_wakes_it_within_seconds` | `InboxAwaiter` (production opener, poll 600 s, budget 10 s) wakes < 4 s after a RELATE | G | **R (8.5 s: LIVE never attached)** | G |
| R10c | `…control_without_a_notification…` | control: no RELATE → waits out its budget | G | G | G |

Shape of the remaining work, read off the SDK3+U column: a correct build must fix the record-id
rendering (R7–R9) and choose F2; everything else is green once the single-statement seams answer the
first statement. That column is evidence the pins are SATISFIABLE, not a reference build: the
adversary builds that (role boundary).

Adversarial pre-flight (what wrong build each family kills): L1 — an owner constructed with
`reconnect=False` or bypassing a shared factory (∀ 18 owners, derived); L2 — a reconnect state that is
spent after one use; L3 — classifying `ConnectionUnavailableError` as domain, or resending; L4 — a
`drop` that nulls without `close()` (SDK 3.0 would keep the orphan reconnecting); L5 — `close()` that
leaves the reconnect task alive; T1/T2 — conflict typing lost in the streamed rebuild or SDK 3.0's
`details` unwrap; T3 — positional root-cause selection (three positions); R3/R4 — any un-unwrapped
truthy wrapper; R6 — normalising `PreciseDatetime` to naive/str; R7–R9 — keeping `str(RecordID)` as
the served id; R10 — passing the list to `subscribe_live`.
Checklist: concurrency ≥ 8 everywhere it applies (8, 16, 18); every negative pin has a control (L3c,
R10c, premise asserts in L1/T1/T2/R9); fixtures vary the branch value (3 THROW positions, 7 key shapes,
2 sever shapes); nothing touches `:18000`'s container, `:18500`, lore-surreal or lore-lore.
Known residual: L6/L1 timing constants are tuned to SDK 3.0's default schedule (first reconnect
~2 s); a correct build with a slower first attempt would RED L1 — that is F2's decision.

## 5. Open forks for the operator

- **F1 — where the result-shape adaptation lives.** `query()` now returns a list per statement.
  Recommend: ONE adaptation inside `_txn.run_query` (+ the two seam-local `query()` callers in scout
  and the awaiter routed through it or through one shared helper), never per caller. The harness
  `run()` needs the same (test fixture, outside this packet's contract writable set).
- **F2 — reconnect policy (one shared connection factory).** 18 owners call `AsyncSurreal(url)` with
  defaults. Recommend a single factory in `store/_txn.py` with `ReconnectOptions(attempts=-1,
  retry_delay=0.5, retry_delay_max=2.0)` so a call after a long outage answers in ≤ ~2 s (L6 pins 6 s).
  Alternative: keep defaults and delete L6 (accepting a call parked up to ~30 s, then
  `TransportTimeoutError`).
- **F3 — keep the engine's nanoseconds.** SDK 3.0's `PreciseDatetime` round-trips them, so a stamp read
  back can be bound back (cursor/CAS on a timestamp). Recommend YES (R6b); NO deletes R6b.
- **F4 — request timeout.** SDK 3.0 defaults to 30 s per request; SDK 2.0 had none. A long DDL/index
  build/large write past 30 s becomes a transport error and a `drop` while the statement may still
  commit. Recommend `timeout=None` in the shared factory (keep 2.0's semantics) unless a measured
  bound is ruled; unpinned (a >30 s pin costs a minute per run).
- **F5 — the runtime SDK-escape guard (`tests/_sdk_guard.py`) loses reach.** It wraps coroutine
  functions only; SDK 3.0's `query` (and 7 CRUD verbs) are sync builder factories, so the guard and its
  multi-statement check silently stop observing the one method every seam uses. The builder must
  extend the guard's reach and prove it by its existing controls; recommend counting observed
  `query` calls as a checked variable (instrument-lesson row 8 otherwise).
- **F6 — the RED pins are unregistered.** `scripts/pending_contracts.yaml` can only adjudicate a file
  that has mypy errors naming unbuilt symbols; registering these files would make the typecheck leg
  SELF-DESTRUCT ("produced NO mypy errors"). Options: (a) extend `PendingFile` with a pytest-only
  `red_nodeids` adjudication that self-destructs when they go green (recommended; a gate change); (b)
  leave the 6 RED pins orphaned until the build lands (next step). Until ruled, they are RED_ORPHANED
  in a full-suite currency run.
- **F7 — `RecordID.parse` acceptance widened** (I-9): enumerate what snapshot ids lore accepts, or rule
  it unreachable (snapshot ids are lore-minted).
- **F8 — record-id rendering policy (the §2.2 finding).** Recommend a single lore-owned "served id"
  function (table + bare key, SDK-2.0 shape) in `lorerunes`/`_txn`, replacing the four `partition(":")`
  re-parsers; and a production check that no persisted `keep:`/`principal:` scope or `target_row` was
  ever written bracketed (a read-only count on `:18500`, by the lead).

## 6. Gate receipts

Logs in the session scratchpad, `scratchpad/sdk3/receipts/` (lead-named session dir). Final receipts
(TREE taken after the last test edit; the only later edit is this §6 table and one §4 cell, so a re-derived TREE will differ by this doc alone — rerun if that matters):

| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| contract @HEAD (SDK 2.0) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -rfE -p no:cacheprovider --timeout=300 -n 8 <3 files>` | `head_contract_final.log` | 1 | 5 failed, 23 passed (the 5 designed REDs: L1×2, L2, L6, R6b) | TREE=810bd097…9da8 |
| contract @SDK3 (shim) | same, `--setenv=PYTHONPATH=scratchpad/sdk3/sdk3shadow` (SDK_UNDER_TEST printed in log) | `sdk3_plain_contract_final.log` | 1 | 16 failed, 12 passed | TREE=810bd097…9da8 |
| contract @SDK3+U | same, `--setenv=PYTHONPATH=scratchpad/sdk3/sdk3shadow_unwrap` | `sdk3_unwrap_contract_final.log` | 1 | 4 failed, 24 passed (R7, R8, R9, L6) | TREE=810bd097…9da8 |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `gate_currency_final.log` | 1 | typecheck RED_ADJUDICATED (83, packet-58-contract) · ruff GREEN · no RED_ORPHANED · `CURRENCY: FAIL — claimed but never run: pytest` (the `--legs` subset still reports the unrun pytest leg as a failure: a gate quirk, flagged) | TREE=810bd097…9da8 |

Hygiene: SDK3-shadow runs cannot run the harness's session-end reaper (it reads SDK 2.0's shape), so
their test databases were removed by name afterwards (`scratchpad/sdk3/reap_leaked.py`; 2 + 25 + 26 + 27
databases, `still present: []`). One stray empty `lore_test` database created by that script's first
version (a bare `use()`) was removed.

## 7. For the builder (outside this contract's writable set — flags, not edits)

- `loremaster/tests/_surreal_harness.py` `run()` / reaper / `drop_database` and `conftest.py`'s
  session-end reap read SDK 2.0 shapes (`INFO` map) — they fail under SDK 3.0 (measured: "the
  test-namespace reaper read answered a list"), leaking test databases.
- `loremaster/tests/_sdk_guard.py` (F5); `test_retry_seam._SDK_CONNECTION_CLASSES` names the embedded
  class.
- `scripts/`: 21 scripts call the SDK (C1–C4); all index `query()` results SDK-2.0-style. By name
  (NOT verified against cron/docs) the recurring ones are `snapshot_gc.py`,
  `survey_txn_contention_102.py`, `forgery_door_sweep.py`, `search_score_survey.py`; the rest read as
  dated probes. Which to port is a builder/lead call.
- `pyproject.toml`/`uv.lock`: SDK 3.0 needs `aiohttp>=3.14.0`, `websockets>=15`, `pydantic-core>=2.10`
  (lore has 3.14.1 / 16.0 / 2.46.4 — compatible); `surrealdb-embedded` only if the embedded class stays.

## DRY ledger (new reusable symbols, all test-side)

| new symbol | where I looked | found | disposition |
|---|---|---|---|
| `_sdk3_proxy.StoreBounceProxy`, `SeverMode` | grep `proxy\|start_server\|bounce` in `loremaster/tests` | `test_retry_seam` drop fakes (scripted, no real socket); none proxies a live store | HAND-ROLLED: nothing severs a real socket |
| `test_sdk3_lifecycle._construct_live_owner` | `test_retry_seam._construct_live` | fits except scout's `connect`/`handler`/`poll_interval_s` | near-copy (8 lines) because `test_retry_seam.py` is outside the writable set — recommend EXTENDING `_construct_live` with those values and deleting this |
| `_drop_of` | `run_query`'s `DropConnection` alias | none adapts a no-arg drop | HAND-ROLLED (scout's drop shape, §2.4) |
| `_CountingOwner` | grep `attempts` counters in tests | per-file fakes only | HAND-ROLLED, test-local |
| reused | `_discover_bootstrap_owners`, `_MIN_KNOWN_BOOTSTRAP_OWNERS`, `_CTOR_VALUES` (test_retry_seam); `_peek_empty`/`_peek_traffic` (test_comms_await); harness `connect_admin`/`drop_database`/`run`/`make_env`/`unique_database`; `scout._open_command_connection` | | REUSED |
