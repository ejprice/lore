# Packet SDK3 — Python SDK `surrealdb` 2.0.0 → 3.0.0 (on the 3.3.5 stores)

Status: DISCOVERY + CONTRACT (tdd Phase 0 + Phase 1), written 2026-11-07 by the SDK3 contract author
against HEAD `4624daf` (branch `feat/surreal-unification`; the brief named `c05bf3f`, HEAD moved
under another builder's commit while this ran), SDK 2.0.0 in lore's venv, SDK 3.0.0 in the
research40 scratch venv. Operator approved the packet 2026-11-07. **This contract STOPS for operator
review** (§5 forks); then `contract-adversary` grades it, then a builder implements.

Inputs: `docs/research/2026-11-07-surrealdb-3.3-4.0-for-lore.md` (SUMMARY, §B4–B6/B18, §C, §D-4/D-10,
§E 7/11/12), finding #576, `docs/reference/surrealdb-31-capabilities.md` §0a/§2/§3/§6.5.

## SUMMARY

- **Round 2 (operator ruling R1, `docs/plans/v2/sdk3-rulings.md`):** the inventory is now a workaround
  re-evaluation (§3), 31 rows, each re-probed live on SDK 3.0.0 + 3.3.5 (Appendix A/B). **Retire:** the
  `KeyError` transport arm (W1) and the bare `"TransactionConflict"` literal (W6), each with a
  retirement pin that is RED at HEAD, GREEN on SDK 3.0, and RED again under a mutation re-introducing the
  old symptom (§3.2). **Simplify:** #576's per-owner self-heal (W7), the statement[0] rule's rationale
  (W4). **Keep:** NotAllowed-as-transport (changed: still reached after reconnect give-up, W3), cascade
  root-cause selection, the unique-index text marker, every §2/§6.6 engine workaround (all
  still-present on 3.3.5) and the bootstrap retry (conflicts fell to ~0.6%, not zero). **Forks:**
  F9 (`starts_with` is index-served now), F10 (the `websockets` arm). Known-bound pins on SDK 3.0: none
  went red.

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

## 3. Workaround re-evaluation inventory (operator ruling R1, round 2)

Round 1 wrote this as a preservation list. Operator ruling R1 (`docs/plans/v2/sdk3-rulings.md`) recast
it: each row says whether lore's code exists because something was BROKEN, and whether that defect
still exists on **SDK 3.0.0 + engine 3.3.5**, MEASURED by `probe_r1_workarounds.py` (pasted verbatim in
Appendix A, run 2026-11-07 against the TEST store, throwaway `lore_test/sdk3r1_*` databases, all
removed — every run printed `sdk3r1* databases left: []`). Outputs: Appendix B. Scope widened to the
engine workarounds store reference §2/§3/§6.5/§6.6 document.

Fates: `retire` = defect gone, delete the workaround, ships a retirement pin + mutation proof (§3.2) ·
`keep` = defect still present · `simplify` = defect changed · design rows keep the round-1 fates.

| # | lore workaround (where) | origin | defect | re-probed on SDK 3.0.0 + 3.3.5 | fate |
|---|---|---|---|---|---|
| W1 | `KeyError` caught as transport: `_SDK_AWAIT_BOUNDARY_ERRORS`, both drivers' `except (*_CONNECTION_ERRORS, KeyError)`, `_raise_attempt_failure`'s `isinstance(error, KeyError)` | sdk-bug | store ref §3 [PROBED] "raw `builtins.KeyError(uuid)`" (3.1.5, 3.2.4; lore memory `bef131a1`) | **gone** — P1: 4/4 in-flight calls raise `surrealdb.errors.ConnectionUnavailableError` (SDK 2.0 same probe: 4/4 `builtins.KeyError`) | **retire** — pin RP1, mutation M1 |
| W2 | raw `websockets` errors caught as transport: `WebSocketException` in `_CONNECTION_ERRORS` (and so in every `_safe_close`) | sdk-bug | store ref §3 "next call heals via `ConnectionClosedError`"; #576 text | **gone on every measured path** — P1: next call on the same connection OK, `close()` after the drop OK; P2: three calls after an idle bounce OK (SDK 2.0: `websockets…ConnectionClosedError: no close frame received or sent` on every call). Unmeasured paths: a LIVE subscription's iterator, `kill()` on a dead socket | **retire proposed → fork F10** (ambiguous: proven on 3 paths, not all) — pin RP1 covers the in-flight path |
| W3 | `NotAllowed` caught as transport (`_CONNECTION_ERROR_KINDS`): "the socket silently reconnected unauthenticated" | sdk-bug | `_txn._CONNECTION_ERROR_KINDS` comment / `_txn_query_raw` docstring; undocumented as a finding | **changed** — a default SDK 3.0 reconnect replays auth + ns/db (P2: `INFO FOR DB` authed, `session::ns/db` intact). But once the SDK's reconnect GIVES UP (P3, `attempts=1`), every call answers `-32002 … actor: anonymous` and never heals by itself; with `reconnect=False` (mutation M2) the first call after a bounce is "Anonymous access not allowed" | **keep** (trigger is now reconnect give-up, not every drop; comment to be updated) |
| W4 | the statement[0]-only gap: multi-statement SurrealQL must ride `execute_transaction` / `query_raw`; `tests/_sdk_guard.py`'s multi-statement refusal on bare `.query()`; store ref §3 rule | sdk-bug | store ref §3, §6.5, §6.6 #10; #124 / #144 | **changed** — P4: a plain multi-statement `query()` now RAISES the later failure (`ThrownError`; SDK 2.0 returned success); inside `BEGIN…COMMIT` it raises the CASCADE notice (`QueryError details.kind NotExecuted`), not the root cause (SDK 2.0 returned `None`) | **simplify** — keep the rule and the drivers; its reason changes from "swallowed" to "raises the cascade, so the cause and a conflict's retry are lost". No code retires; store ref §3/§6.5 prose must change (outside writable set) |
| W5 | root-cause selection `_is_domain_cascade_notice` / `_domain_root_cause` | engine-bug | #93; store ref §3 "Classify SEMANTICALLY" | **still-present** — P5: `[OK, NotExecuted, NotExecuted, Thrown, Cancelled, NotExecuted]` (statements before the offender, the offender, after it, COMMIT) | **keep** — pins T3 ×3 positions |
| W6 | the bare `_RETRYABLE_CONFLICT_KIND = "TransactionConflict"` literal, read via `_detail_kind` | sdk-bug | #111 ("the SDK ships no predicate"); store ref §3 #111 bullet | **gone** — P6: `QueryError.is_transaction_conflict` is True on 5/5 raised single-statement conflicts and 29/29 parsed per-statement entries, agreeing with `details.kind` (SDK 2.0: 0/53 and 0/52 — no such attribute) | **retire** (route `_is_retryable_conflict_kind` through the SDK predicate) — pin RP3, mutation M3; behaviour stays pinned by T1/T2/T4 |
| W7 | per-owner `_ensure_connection` self-heal: drop the handle on a transport error, reconnect on the NEXT call (#576) | sdk-bug | #576; store ref §3 | **changed** — P2: an idle connection reconnects and replays its session on its own (SDK 2.0: dead until dropped); P1: a call racing the drop still fails once; P3: after reconnect give-up only a fresh connection (lore's drop) heals | **simplify** — #576's idle failure retires (pins L1 ∀18 owners, RP2, mutation M2); the drop stays as the racing/give-up backstop (pins L3, L4) |
| W8 | bootstrap DDL retried (`bootstrap_session` under `retry_on_conflict`) | engine-bug | `bootstrap_session` docstring: 6.2%–34.4% of 16-way virgin first-connects lost (3.2.x) | **changed** — P16, 4 × (10 fresh databases × 16 concurrent connects), no retry: 0 + 3 + 0 (SDK 3.0) and 1 (SDK 2.0) failures in 640 — all `use()` → `TransactionConflict`; ~0.6%, still non-zero | **keep** (the retry is the shared driver; rarer, not gone) |
| W9 | client-side conflict retry `retry_on_conflict` for single statements and transactions | engine-bug (no server retry before 4.0) | store ref §3 "Client-side conflict retry is MANDATORY"; #102 | **still-present** — P6: 5 raised + 29 per-statement conflicts at 16-way; T1/T2 premise (attempts > writes) holds on 3.3.5 | **keep** |
| W10 | unique-index collision text-classified (no typed kind) | engine-bug | amendment 33 §(a); KNOWN-BOUND pin `test_am33_KNOWN_BOUND_a_unique_index_collision_is_an_untyped_InternalError` | **still-present** — P7: `InternalError(kind='Internal', details=None)` on both paths; the known-bound pin stays GREEN on SDK 3.0 (§6) | **keep** |
| W11 | readers never assume a `SELECT *` column is present (explicit projections / `.get`) | engine-bug | store ref §2, §6.6 #12 | **still-present** — P8: `SELECT *` keys `['a','id']` (NONE column omitted); projection reads `{'a':'x','o':None}` | **keep** |
| W12 | `object::extend($bound, {computed})` instead of `CONTENT … SET/MERGE` | engine-bug | §2, §6.6 #11 | **still-present** — P9: `CONTENT+SET` and `CONTENT+MERGE` parse errors; `object::extend` works | **keep** |
| W13 | every relation table DECLARED before first RELATE | engine-bug | §4, §6.6 #1 | **still-present** — P10: `RELATE` onto an undeclared table auto-creates `DEFINE TABLE … TYPE ANY SCHEMALESS` | **keep** |
| W14 | tables declared before concurrent first writes | engine-bug | §5, §6.6 #2, #144 | **still-present** — P15: 4 of 16 concurrent first writes to an undeclared table → `TransactionConflict` | **keep** |
| W15 | re-point an edge by DELETE + re-RELATE, never `UPDATE in/out` | engine-bug | §2, §6.6 #8 | **still-present** — P11: `UPDATE … SET out` returns a row, the edge is unchanged | **keep** |
| W16 | `compose` refuses a top-level `RETURN` in a transaction | engine-bug | §3, #497 / #501 | **still-present** — P12: `BEGIN; CREATE a; RETURN NONE; CREATE b; COMMIT` → all `OK`, only `a` committed | **keep** |
| W17 | fields `DEFINE FIELD OVERWRITE`, never `IF NOT EXISTS` | engine-bug | §1.1, §6.1, #107 | **still-present** — P13: `IF NOT EXISTS` on an existing field → `OK`, definition unchanged | **keep** |
| W18 | an `IN` inside an `OR` expanded to per-value equalities | engine-bug | §2, #413 | **still-present** — P14: `c IN $set OR d = …` TableScan; `IN` alone and the expanded `OR` index-served | **keep** |
| W19 | prefix match as a `>= / <` range, never `string::starts_with` | engine-bug | §2 [PROBED] "`string::starts_with` = TableScan" | **gone** — P14: `string::starts_with(s,'pre00')` plans an index range (`access: ">="`, no TableScan) on 3.3.5 | **retire is possible → fork F9** (the range is equally correct; retiring it is churn on a served query shape) |
| W20 | `CONTAINSANY` clause omitted when the set is empty | engine-bug | §2 (2026-08-24 probe) | **still-present** — P14: `CONTAINSANY []` TableScan; `CONTAINSANY ['t1']` index-served | **keep** |
| W21 | array columns indexed by element path (`.*`) | engine-bug | §2, §6.6 #14, re-probed §0a | **still-present** — P14: plain index, `tags = 'x'` → `[]`, whole-array → `[]`, `CONTAINS` → rows | **keep** |
| W22 | node-side traversal filter, never a traversal subquery in `FROM` | engine-bug | §6.6 #13 | **still-present** — P17: subquery-`FROM` + field `WHERE` → `[]`; node-side filter → the row | **keep** |
| D1 | `run_query` returns the FIRST statement's result | design | lore's driver contract | changed by SDK 3.0 (list per statement) | **preserved-with-pin** R1–R4 (F1) |
| D2 | `query_raw` per-statement shape read by `_failed_statements` / `execute_read_transaction` | design | — | SDK 3.0 streams on ≥3.3 and rebuilds it identically (T1/T2/R5 green on SDK 3.0) | **preserved-with-pin** T1, T2, R5 |
| D3 | served id = `str(RecordID)`, split on `:` (keeps, principals, principal_keys, scopes, `audit.target_row`) | design | #248 | changed: SDK 3.0 brackets every digit-led key (§2.2) | **preserved-with-pin** R7–R9 (F8) |
| D4 | `LIVE SELECT` id from `query()` handed to `subscribe_live` | design | store ref §10 | changed shape (list) | **preserved-with-pin** R10 + control |
| D5 | poll fallback under every LIVE | design | store ref §10 | SDK 3.0 does not replay a `query()`-made LIVE on reconnect (source read) | **preserved** (existing `test_comms_await`) |
| D6 | datetimes truncated to µs on read | sdk-bug (decoder) — no lore workaround exists | R6b | **gone** (`PreciseDatetime` keeps nanoseconds; R6b green on SDK 3.0) | **spec-silent → F3** |
| D7 | `RecordID.parse` raises `InvalidRecordIdError` for malformed ids (`diff`, `snapshots`) | design | — | changed (3.0 parses `x:y`-in-key, dict shapes) | **spec-silent → F7** |
| D8 | no client request timeout | design | — | SDK 3.0 defaults to 30 s | **spec-silent → F4** |
| D9 | `AsyncEmbeddedSurrealConnection` imported from `surrealdb` | design | — | moved (needs `surrealdb-embedded`) | **dropped** |

### 3.1 Known-bound pins run against SDK 3.0 (R1's instrument)
The engine/SDK KNOWN-BOUND pins found by `grep -rnE "KNOWN[ -]BOUND|goes RED the day|delete this pin"`
over `loremaster/tests`, filtered to engine/SDK facts (grep fallback: lore MCP down): 
`test_fixwave_a28b_63c_i_a.py::TestTheSdkDoesNotTypeAUniqueIndexCollision63cIAa28b` (W10) and
`test_fixwave_a28c_63c_i_a.py::TestTheEngineFactsTheClassifierRestsOn63cIAa28c` (the engine nouns the
classifier anchors on). Both run on SDK 3.0 (shadow #2) in §6: none went red, so no `gone` signal —
consistent with P7. The other KNOWN-BOUND hits are product bounds (single issuer, label attribution,
legacy grades, …), not SDK/engine facts.

### 3.2 Retirement pins and mutation proofs (R1 rider)
File `loremaster/tests/test_sdk3_workaround_retirement.py`; each pin is RED at HEAD (defect present),
GREEN on SDK 3.0, and RED again under the mutation that re-introduces its defect's symptom
(`scratchpad/sdk3/sdk3shadow_mutation/sitecustomize.py`, `$SDK3_MUTATION`, pasted in Appendix C):

| pin | row | asserts | HEAD | SDK 3.0 | mutation → result |
|---|---|---|---|---|---|
| RP1 `TestAnInFlightDropIsATypedSdkTransportError` | W1, W2 | 8 calls in flight at an RST: each raises `SurrealConnectionError` whose cause is a `surrealdb.errors.SurrealError` | R (8/8 `builtins.KeyError`) | G | M1 `keyerror` → **R** (only this pin) |
| RP2 `TestAnIdleConnectionComesBackOnItsOwn` | W2, W7 | after an idle bounce the SAME plain connection serves `session::ns/db` (unchanged) and an authed `INFO FOR DB` | R (`ConnectionClosedError: no close frame…`) | G | M2 `noreconnect` → **R** ("Anonymous access not allowed") |
| RP3 `TestTheSdkTypesALiveTransactionConflict` | W6 | 16 racers: every live conflict, raised and per-statement, has `is_transaction_conflict is True` | R (195/195 untyped) | G | M3 `nopredicate` → **R** |

Bound, stated: RP3's single-statement leg can observe zero conflicts in a run (the premise asserts
only the transactional leg, which saw 29–74 per run); its "all observed agree" holds vacuously then.

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
| RP1 | `TestAnInFlightDropIsATypedSdkTransportError` (round 2, W1/W2 retirement) | in-flight drop: driver raises `SurrealConnectionError` caused by a typed `SurrealError` | **R** (`KeyError`) | — | G (M1 → R) |
| RP2 | `TestAnIdleConnectionComesBackOnItsOwn` (W2/W7) | the same plain connection serves an authed call in its session after an idle bounce | **R** (`ConnectionClosedError`) | — | G (M2 → R) |
| RP3 | `TestTheSdkTypesALiveTransactionConflict` (W6) | every live conflict typed by `is_transaction_conflict` on both paths | **R** (195/195 untyped) | — | G (M3 → R) |

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
  leave the 8 RED-at-HEAD pins (5 round-1 + RP1–RP3) orphaned until the build lands. Until ruled, they
  are RED_ORPHANED in a full-suite currency run.
- **F7 — `RecordID.parse` acceptance widened** (I-9): enumerate what snapshot ids lore accepts, or rule
  it unreachable (snapshot ids are lore-minted).
- **F8 — record-id rendering policy (the §2.2 finding).** Recommend a single lore-owned "served id"
  function (table + bare key, SDK-2.0 shape) in `lorerunes`/`_txn`, replacing the four `partition(":")`
  re-parsers; and a production check that no persisted `keep:`/`principal:` scope or `target_row` was
  ever written bracketed (a read-only count on `:18500`, by the lead).

- **F9 — retire the `string::starts_with` avoidance (W19)?** P14: 3.3.5 serves it by index range, so the
  defect is gone. The `>= / <` range lore uses is equally correct and index-served; retiring it changes
  served query text for no measured gain. Recommend KEEP (re-classify as design); a retire needs a pin
  + mutation like RP1–RP3.
- **F10 — retire the raw-`websockets` transport arm (W2)?** Proven gone on the in-flight, next-call,
  close and idle-bounce paths (P1, P2, RP1, RP2), not on a LIVE iterator or `kill()` over a dead socket.
  Removing `WebSocketException` from `_CONNECTION_ERRORS` turns any unmeasured leak into an uncaught
  crash instead of a `SurrealConnectionError`. Recommend: retire the `KeyError` arm (W1, unambiguous)
  now; keep the `WebSocketException` arm until the builder measures the two remaining paths, or keep
  it as a harmless superset.
- **Flag (not a fork): store reference prose** — §3's statement[0] bullet, §6.5, §6.6 #3/#10 and the
  #111 bullet describe SDK 2.0; W3/W4/W6 change them. Outside this packet's writable set.

## 6. Gate receipts

Logs in the session scratchpad, `scratchpad/sdk3/receipts/` (lead-named session dir). Final receipts
(TREE taken after the last test edit; the only later edit is this §6 table and one §4 cell, so a re-derived TREE will differ by this doc alone — rerun if that matters):

| gate | command | log | EXIT | count | TREE |
|---|---|---|---|---|---|
| contract @HEAD (SDK 2.0) | `systemd-run --user --scope -p MemoryMax=16G -p MemorySwapMax=0 uv run pytest -q -rfE -p no:cacheprovider --timeout=300 -n 8 <3 files>` | `head_contract_final.log` | 1 | 5 failed, 23 passed (the 5 designed REDs: L1×2, L2, L6, R6b) | TREE=810bd097…9da8 |
| contract @SDK3 (shim) | same, `--setenv=PYTHONPATH=scratchpad/sdk3/sdk3shadow` (SDK_UNDER_TEST printed in log) | `sdk3_plain_contract_final.log` | 1 | 16 failed, 12 passed | TREE=810bd097…9da8 |
| contract @SDK3+U | same, `--setenv=PYTHONPATH=scratchpad/sdk3/sdk3shadow_unwrap` | `sdk3_unwrap_contract_final.log` | 1 | 4 failed, 24 passed (R7, R8, R9, L6) | TREE=810bd097…9da8 |
| currency | `uv run python scripts/pending_contract_gate.py --currency --legs typecheck,ruff` | `gate_currency_final.log` | 1 | typecheck RED_ADJUDICATED (83, packet-58-contract) · ruff GREEN · no RED_ORPHANED · `CURRENCY: FAIL — claimed but never run: pytest` (the `--legs` subset still reports the unrun pytest leg as a failure: a gate quirk, flagged) | TREE=810bd097…9da8 |


Round 2 receipts (operator ruling R1), same log directory; the contract set is the 4 `test_sdk3_*` files
plus the two engine/SDK KNOWN-BOUND classes (§3.1). Only this paragraph and table were edited after them.

| gate | log | EXIT | count | TREE |
|---|---|---|---|---|
| contract @HEAD (SDK 2.0) | `r2_head_contract.log` | 1 | 8 failed, 38 passed — the designed REDs: L1×2, L2, L6, R6b, RP1, RP2, RP3; both known-bound classes GREEN | TREE=4c700181…c0a1 (HEAD 2697974) |
| contract @SDK3+U | `r2_sdk3_unwrap_contract.log` | 1 | 4 failed, 42 passed — R7, R8, R9, L6; RP1–RP3 and both known-bound classes GREEN | TREE=4c700181…c0a1 (HEAD 2697974) |
| mutation proofs M1/M2/M3 on the retirement file | `r2_mutation_proofs.log` | 1 each | 1 failed, 2 passed each — keyerror→RP1, noreconnect→RP2, nopredicate→RP3 | TREE=4c700181…c0a1 (HEAD 2697974) |
| currency `--legs typecheck,ruff` | `r2_gate_currency.log` | 1 | typecheck RED_ADJUDICATED (83, packet-58) · ruff GREEN · no RED_ORPHANED · pytest NOT_RUN quirk | TREE=4c700181…c0a1 (HEAD 2697974) |
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


## Appendix A — `probe_r1_workarounds.py` (verbatim; run with the SDK under test, `-I`)

```python
"""Packet SDK3 round 2 (operator ruling R1): re-probe every SDK/engine workaround's DEFECT on the
installed SDK against the TEST store (3.3.5).

    <python with the SDK under test> probe_r1_workarounds.py [probe-id ...]

Runs against ws://127.0.0.1:18000/rpc in a throwaway database lore_test/sdk3r1_<hex>, removed at the
end (and printed). Store bounces go through loremaster/tests/_sdk3_proxy.py (an in-process TCP proxy),
never a store restart. Every probe prints `P<n> <id>: <observation>` lines; verdicts are the reader's.
Uses query_raw (identical shape on SDK 2.0 and 3.0) for engine probes so the SDK cannot colour them.
"""

import asyncio
import importlib.metadata
import sys
import uuid

sys.path.insert(0, "/home/ejprice/PycharmProjects/lore/loremaster/tests")
from _sdk3_proxy import StoreBounceProxy  # noqa: E402
from surrealdb import AsyncSurreal  # noqa: E402

URL = "ws://127.0.0.1:18000/rpc"
AUTH = {"username": "root", "password": "spikeroot"}
NS = "lore_test"
DB = f"sdk3r1_{uuid.uuid4().hex[:12]}"
SDK = importlib.metadata.version("surrealdb")
SDK3 = SDK.startswith("3.")


def ename(exc: BaseException) -> str:
    kind = getattr(exc, "kind", None)
    details = getattr(exc, "details", None)
    return f"{type(exc).__module__}.{type(exc).__name__}(kind={kind!r}, details={details!r}): {str(exc)[:110]}"


async def connect(url: str = URL, **kwargs):
    connection = AsyncSurreal(url, **kwargs) if kwargs else AsyncSurreal(url)
    await connection.signin(AUTH)
    await connection.use(NS, DB)
    return connection


async def raw(connection, sql: str, params=None):
    """Per-statement (status, result, kind, details) via query_raw — SDK-shape-neutral."""
    response = await connection.query_raw(sql, params or {})
    if response.get("error") is not None:
        return [("RPC-ERR", response["error"], None, None)]
    return [(s.get("status"), s.get("result"), s.get("kind"), s.get("details")) for s in response["result"]]


async def first(connection, sql, params=None):
    entries = await raw(connection, sql, params)
    status, result, kind, details = entries[0]
    if status != "OK":
        return f"ERR kind={kind} details={details} {str(result)[:120]}"
    return result


async def p1_in_flight_drop():
    proxy = StoreBounceProxy(upstream_url=URL)
    await proxy.start()
    connection = await connect(proxy.url)
    tasks = [asyncio.create_task(connection.query_raw("RETURN sleep(2s)")) for _ in range(4)]
    await asyncio.sleep(0.4)
    await proxy.go_down()
    await proxy.come_up()
    outcomes = await asyncio.gather(*tasks, return_exceptions=True)
    print(f"P1 in-flight-drop: {sorted({ename(o) if isinstance(o, BaseException) else 'VALUE' for o in outcomes})}")
    await asyncio.sleep(4)
    try:
        print(f"P1 next-call-after-in-flight-drop: OK {await first(connection, 'RETURN 1')}")
    except Exception as exc:  # noqa: BLE001
        print(f"P1 next-call-after-in-flight-drop: {ename(exc)}")
    try:
        await connection.close()
        print("P1 close-after-drop: OK")
    except Exception as exc:  # noqa: BLE001
        print(f"P1 close-after-drop: {ename(exc)}")
    await proxy.close()


async def p2_idle_bounce():
    proxy = StoreBounceProxy(upstream_url=URL)
    await proxy.start()
    connection = await connect(proxy.url)
    await first(connection, "RETURN 1")
    await proxy.bounce(down_seconds=0.5)
    await asyncio.sleep(5)
    for attempt in (1, 2, 3):
        try:
            info = await first(connection, "RETURN [session::ns(), session::db()]")
            authed = await first(connection, "INFO FOR DB")
            print(f"P2 idle-bounce call {attempt}: OK ns/db={info} authed_info_for_db={str(authed)[:40]}")
        except Exception as exc:  # noqa: BLE001
            print(f"P2 idle-bounce call {attempt}: {ename(exc)}")
    try:
        await connection.close()
    except Exception as exc:  # noqa: BLE001
        print(f"P2 close: {ename(exc)}")
    await proxy.close()


async def p3_reconnect_give_up():
    """What the next call sees once the SDK's reconnect has GIVEN UP (the NotAllowed-after-reconnect row)."""
    if not SDK3:
        print("P3 give-up: n/a on SDK 2.0 (no reconnect)")
        return
    from surrealdb import ReconnectOptions

    proxy = StoreBounceProxy(upstream_url=URL)
    await proxy.start()
    connection = await connect(proxy.url, reconnect=ReconnectOptions(attempts=1, retry_delay=0.2, retry_delay_max=0.2))
    await first(connection, "RETURN 1")
    await proxy.go_down()
    await asyncio.sleep(3)
    await proxy.come_up()
    await asyncio.sleep(1)
    for attempt in (1, 2, 3):
        try:
            print(f"P3 after-give-up call {attempt}: OK {await first(connection, 'RETURN [session::ns(), session::db(), $auth]')}")
        except Exception as exc:  # noqa: BLE001
            print(f"P3 after-give-up call {attempt}: {ename(exc)}")
        try:
            print(f"P3 after-give-up table read {attempt}: {await first(connection, 'INFO FOR DB')!s:.80}")
        except Exception as exc:  # noqa: BLE001
            print(f"P3 after-give-up table read {attempt}: {ename(exc)}")
    try:
        await connection.close()
    except Exception as exc:  # noqa: BLE001
        print(f"P3 close: {ename(exc)}")
    await proxy.close()


async def p4_later_statement_failure(connection):
    for label, sql in [
        ("plain", "CREATE p4a:1; THROW 'p4-second-fails'; CREATE p4a:2;"),
        ("txn", "BEGIN; CREATE p4b:1; THROW 'p4-second-fails'; CREATE p4b:2; COMMIT;"),
    ]:
        try:
            out = await connection.query(sql)
            print(f"P4 query() {label}: RETURNED {out!r:.100}")
        except Exception as exc:  # noqa: BLE001
            print(f"P4 query() {label}: RAISED {ename(exc)}")


async def p5_cascade_kinds(connection):
    entries = await raw(connection, "BEGIN; CREATE p5:1; CREATE p5:2; THROW 'p5-root'; CREATE p5:3; COMMIT;")
    print(f"P5 txn per-statement kinds: {[(status, kind, (details or {}).get('kind') if isinstance(details, dict) else details) for status, _r, kind, details in entries]}")


async def p6_conflict_typing():
    racers = [await connect() for _ in range(16)]
    await first(racers[0], "UPSERT p6:hot SET n = 0")
    errors = []

    async def bump(connection):
        for _ in range(10):
            try:
                await connection.query("UPDATE p6:hot SET n += 1")
            except Exception as exc:  # noqa: BLE001
                errors.append(exc)

    await asyncio.gather(*(bump(c) for c in racers))
    typed = [e for e in errors if getattr(e, "is_transaction_conflict", None) is True]
    detail = [e for e in errors if isinstance(getattr(e, "details", None), dict) and e.details.get("kind") == "TransactionConflict"]
    print(f"P6 single-statement conflicts: errors={len(errors)} sdk_predicate_true={len(typed)} details_kind_TransactionConflict={len(detail)} types={sorted({type(e).__name__ for e in errors})}")
    if errors:
        print(f"P6 sample: {ename(errors[0])}")
    txn_conflicts = 0
    txn_typed = 0

    async def txn(connection):
        nonlocal txn_conflicts, txn_typed
        from surrealdb.errors import parse_query_error

        for _ in range(5):
            response = await connection.query_raw(
                "BEGIN; LET $c = (SELECT VALUE n FROM ONLY p6:hot); UPDATE p6:hot SET n = $c + 1; COMMIT;"
            )
            for entry in response["result"]:
                if entry.get("status") == "ERR" and (entry.get("details") or {}).get("kind") == "TransactionConflict":
                    txn_conflicts += 1
                    parsed = parse_query_error(entry)
                    if getattr(parsed, "is_transaction_conflict", None) is True:
                        txn_typed += 1

    await asyncio.gather(*(txn(c) for c in racers))
    print(f"P6 txn conflict entries: {txn_conflicts} parsed_with_sdk_predicate_true={txn_typed}")
    for c in racers:
        await c.close()


async def p7_unique_index_collision(connection):
    await raw(connection, "DEFINE TABLE p7 SCHEMALESS; DEFINE INDEX p7_u ON p7 FIELDS k UNIQUE; CREATE p7:1 SET k = 'x';")
    try:
        await connection.query("CREATE p7:2 SET k = 'x'")
        print("P7 unique collision: no error")
    except Exception as exc:  # noqa: BLE001
        print(f"P7 unique collision (query): {ename(exc)}")
    print(f"P7 unique collision (query_raw entry): {(await raw(connection, 'CREATE p7:3 SET k = $k', {'k': 'x'}))[0][2:]}")


async def p8_select_star_none(connection):
    await raw(connection, "DEFINE TABLE p8 SCHEMAFULL; DEFINE FIELD a ON p8 TYPE string; DEFINE FIELD o ON p8 TYPE option<string>; CREATE p8:1 SET a = 'x';")
    star = await first(connection, "SELECT * FROM p8:1")
    proj = await first(connection, "SELECT a, o FROM p8:1")
    print(f"P8 SELECT * keys={sorted(star[0])} | explicit projection={proj}")


async def p9_content_set(connection):
    for label, sql in [
        ("CONTENT+SET", "CREATE p9 CONTENT { a: 1 } SET b = 2"),
        ("CONTENT+MERGE", "CREATE p9 CONTENT { a: 1 } MERGE { b: 2 }"),
        ("object::extend", "CREATE p9 CONTENT object::extend({ a: 1 }, { b: 2 })"),
    ]:
        print(f"P9 {label}: {str(await first(connection, sql))[:140]}")


async def p10_relate_undeclared(connection):
    await raw(connection, "DEFINE TABLE p10a SCHEMALESS; DEFINE TABLE p10b SCHEMALESS; CREATE p10a:1; CREATE p10b:1;")
    print(f"P10 RELATE onto undeclared table: {str(await first(connection, 'RELATE p10a:1->p10undeclared->p10b:1'))[:80]}")
    info = await first(connection, "INFO FOR TABLE p10undeclared")
    print(f"P10 auto-created table definition: {str((info or {}).get('tables', info))[:160] if isinstance(info, dict) else info}")
    db_info = await first(connection, "INFO FOR DB")
    print(f"P10 INFO FOR DB tables.p10undeclared: {db_info['tables'].get('p10undeclared')}")


async def p11_relation_endpoint_update(connection):
    await raw(connection, "DEFINE TABLE p11n SCHEMALESS; DEFINE TABLE p11e TYPE RELATION; CREATE p11n:a; CREATE p11n:b; CREATE p11n:c; RELATE p11n:a->p11e:1->p11n:b;")
    print(f"P11 UPDATE edge out: {str(await first(connection, 'UPDATE p11e:1 SET out = p11n:c'))[:120]}")
    print(f"P11 edge after: {await first(connection, 'SELECT in, out FROM p11e:1')}")


async def p12_return_in_txn(connection):
    entries = await raw(connection, "BEGIN; CREATE p12:a; RETURN NONE; CREATE p12:b; COMMIT;")
    rows = await first(connection, "SELECT VALUE id FROM p12")
    print(f"P12 RETURN in txn: statuses={[e[0] for e in entries]} rows_committed={rows}")


async def p13_if_not_exists(connection):
    await raw(connection, "DEFINE TABLE p13 SCHEMALESS; DEFINE FIELD f ON p13 TYPE string;")
    entries = await raw(connection, "DEFINE FIELD IF NOT EXISTS f ON p13 TYPE int;")
    info = await first(connection, "INFO FOR TABLE p13")
    print(f"P13 IF NOT EXISTS on existing field: status={entries[0][0]} definition_now={info['fields']['f']}")


async def p14_plans(connection):
    await raw(
        connection,
        "DEFINE TABLE p14 SCHEMALESS; DEFINE INDEX p14_c ON p14 FIELDS c; DEFINE INDEX p14_d ON p14 FIELDS d; "
        "DEFINE INDEX p14_s ON p14 FIELDS s; DEFINE INDEX p14_tags ON p14 FIELDS tags; DEFINE INDEX p14_el ON p14 FIELDS el.*;",
    )
    for n in range(200):
        await raw(connection, "CREATE p14 CONTENT $r", {"r": {"c": f"c{n % 20}", "d": f"d{n % 7}", "s": f"pre{n:04d}", "tags": ["x", f"t{n % 5}"], "el": ["x", f"t{n % 5}"]}})
    probes = {
        "IN-inside-OR": ("SELECT * FROM p14 WHERE c IN $set OR d = 'd1' EXPLAIN", {"set": ["c1", "c2"]}),
        "IN alone": ("SELECT * FROM p14 WHERE c IN $set EXPLAIN", {"set": ["c1", "c2"]}),
        "expanded-OR": ("SELECT * FROM p14 WHERE c = $a OR c = $b OR d = 'd1' EXPLAIN", {"a": "c1", "b": "c2"}),
        "starts_with": ("SELECT * FROM p14 WHERE string::starts_with(s, 'pre00') EXPLAIN", {}),
        "range-prefix": ("SELECT * FROM p14 WHERE s >= 'pre00' AND s < 'pre01' EXPLAIN", {}),
        "CONTAINSANY []": ("SELECT * FROM p14 WHERE el CONTAINSANY [] EXPLAIN", {}),
        "CONTAINSANY [x]": ("SELECT * FROM p14 WHERE el CONTAINSANY ['t1'] EXPLAIN", {}),
    }
    for label, (sql, params) in probes.items():
        plan = str(await first(connection, sql, params))
        print(f"P14 {label}: TableScan={'TableScan' in plan} plan={plan[:150]}")
    eq = await first(connection, "SELECT VALUE s FROM p14 WHERE tags = 'x' LIMIT 3")
    whole = await first(connection, "SELECT VALUE s FROM p14 WHERE tags = ['x', 't1'] LIMIT 3")
    contains = await first(connection, "SELECT VALUE s FROM p14 WHERE tags CONTAINS 'x' LIMIT 3")
    print(f"P14 plain-array index: tags='x'->{eq} whole-array->{whole} CONTAINS->{contains}")


async def p15_undeclared_first_write_storm():
    racers = [await connect() for _ in range(16)]
    table = f"p15_{uuid.uuid4().hex[:6]}"
    errors = []

    async def write(connection, index):
        entries = await raw(connection, f"CREATE {table} SET i = $i", {"i": index})
        if entries[0][0] != "OK":
            errors.append(entries[0][2:])

    await asyncio.gather(*(write(c, i) for i, c in enumerate(racers)))
    print(f"P15 16-way first write to an undeclared table: errors={len(errors)} kinds={sorted({str(e[1]) for e in errors})}")
    for c in racers:
        await c.close()


async def p16_virgin_bootstrap_ddl():
    """Rounds of 16-way concurrent bootstrap of a FRESH (virgin) database each, no retry — the reason
    bootstrap_session retries (6.2%-34.4% of virgin first-connects lost, 3.2.x)."""
    failures = []
    databases = []

    async def boot(database):
        connection = AsyncSurreal(URL)
        await connection.signin(AUTH)
        try:
            for step, call in (
                ("define-ns", lambda: connection.query_raw(f"DEFINE NAMESPACE IF NOT EXISTS {NS}")),
                ("use", lambda: connection.use(NS, database)),
                ("define-db", lambda: connection.query_raw(f"DEFINE DATABASE IF NOT EXISTS {database}")),
            ):
                try:
                    response = await call()
                    if isinstance(response, dict):
                        for entry in response.get("result") or []:
                            if entry.get("status") == "ERR":
                                failures.append((step, entry.get("kind"), (entry.get("details") or {}).get("kind")))
                        if response.get("error"):
                            failures.append((step, "RPC", str(response["error"])[:60]))
                except Exception as exc:  # noqa: BLE001
                    failures.append((step, type(exc).__name__, getattr(exc, "details", None)))
        finally:
            await connection.close()

    rounds = int(__import__("os").environ.get("P16_ROUNDS", "3"))
    for _round in range(rounds):
        database = f"sdk3r1b_{uuid.uuid4().hex[:10]}"
        databases.append(database)
        await asyncio.gather(*(boot(database) for _ in range(16)))
    cleanup = await connect()
    for database in databases:
        await cleanup.query_raw(f"REMOVE DATABASE IF EXISTS {database}")
    await cleanup.close()
    print(f"P16 virgin bootstrap {rounds} fresh dbs x16 connects: failures={len(failures)} sample={failures[:3]}")


async def p17_subquery_from_array(connection):
    await raw(
        connection,
        "DEFINE TABLE p17n SCHEMALESS; DEFINE TABLE p17e TYPE RELATION; CREATE p17n:root; "
        "CREATE p17n:l1 SET lvl = 1; CREATE p17n:l4 SET lvl = 4; "
        "RELATE p17n:root->p17e->p17n:l1; RELATE p17n:root->p17e->p17n:l4;",
    )
    field_filter = await first(connection, "SELECT * FROM (SELECT VALUE ->p17e->p17n FROM ONLY p17n:root) WHERE lvl = 4")
    node_side = await first(connection, "SELECT VALUE ->p17e->(p17n WHERE lvl = 4) FROM ONLY p17n:root")
    print(f"P17 subquery-FROM array + field WHERE: {field_filter} | node-side filter: {node_side}")


async def main(selected):
    print(f"sdk={SDK} url={URL} db={NS}/{DB}")
    admin = await connect()
    version = await first(admin, "RETURN 1")
    del version
    try:
        probes = {
            "p1": p1_in_flight_drop, "p2": p2_idle_bounce, "p3": p3_reconnect_give_up,
            "p6": p6_conflict_typing, "p15": p15_undeclared_first_write_storm, "p16": p16_virgin_bootstrap_ddl,
        }
        with_connection = {
            "p4": p4_later_statement_failure, "p5": p5_cascade_kinds, "p7": p7_unique_index_collision,
            "p8": p8_select_star_none, "p9": p9_content_set, "p10": p10_relate_undeclared,
            "p11": p11_relation_endpoint_update, "p12": p12_return_in_txn, "p13": p13_if_not_exists,
            "p14": p14_plans, "p17": p17_subquery_from_array,
        }
        order = ["p1", "p2", "p3", "p4", "p5", "p6", "p7", "p8", "p9", "p10", "p11", "p12", "p13", "p14", "p15", "p16", "p17"]
        for name in order:
            if selected and name not in selected:
                continue
            try:
                if name in probes:
                    await probes[name]()
                else:
                    await with_connection[name](admin)
            except Exception as exc:  # noqa: BLE001 - a probe crash is itself an observation
                print(f"{name.upper()} PROBE-CRASH: {ename(exc)}")
    finally:
        await admin.query_raw(f"REMOVE DATABASE IF EXISTS {DB}")
        info = await admin.query_raw("INFO FOR NS")
        left = [n for n in (info["result"][0]["result"] or {}).get("databases", {}) if n.startswith("sdk3r1")]
        print(f"cleanup: removed {DB}; sdk3r1* databases left: {left}")
        await admin.close()


asyncio.run(main(set(sys.argv[1:])))
```

## Appendix B — probe outputs (2026-11-07, TEST store 3.3.5)

SDK 3.0.0, all probes (its P16 line is the FIRST, same-database version of P16 — superseded by the fresh-database runs below; Appendix A is the final script):
```
sdk=3.0.0 url=ws://127.0.0.1:18000/rpc db=lore_test/sdk3r1_c81f22024b06
P1 in-flight-drop: ['surrealdb.errors.ConnectionUnavailableError(kind=None, details=None): WebSocket connection closed before a response was received.']
P1 next-call-after-in-flight-drop: OK 1
P1 close-after-drop: OK
P2 idle-bounce call 1: OK ns/db=['lore_test', 'sdk3r1_c81f22024b06'] authed_info_for_db={'accesses': {}, 'analyzers': {}, 'apis'
P2 idle-bounce call 2: OK ns/db=['lore_test', 'sdk3r1_c81f22024b06'] authed_info_for_db={'accesses': {}, 'analyzers': {}, 'apis'
P2 idle-bounce call 3: OK ns/db=['lore_test', 'sdk3r1_c81f22024b06'] authed_info_for_db={'accesses': {}, 'analyzers': {}, 'apis'
P3 after-give-up call 1: OK ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details': {'details': {'action': 'process', 'actor': 'anonymous', 'resource
P3 after-give-up table read 1: ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details'
P3 after-give-up call 2: OK ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details': {'details': {'action': 'process', 'actor': 'anonymous', 'resource
P3 after-give-up table read 2: ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details'
P3 after-give-up call 3: OK ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details': {'details': {'action': 'process', 'actor': 'anonymous', 'resource
P3 after-give-up table read 3: ERR kind=None details=None {'cause': None, 'code': -32002, 'details': {'details'
P4 query() plain: RAISED surrealdb.errors.ThrownError(kind='Thrown', details=None): An error occurred: p4-second-fails
P4 query() txn: RAISED surrealdb.errors.QueryError(kind='Query', details={'kind': 'NotExecuted'}): The query was not executed due to a failed transaction
P5 txn per-statement kinds: [('OK', None, None), ('ERR', 'Query', 'NotExecuted'), ('ERR', 'Query', 'NotExecuted'), ('ERR', 'Thrown', None), ('ERR', 'Query', 'Cancelled'), ('ERR', 'Query', 'NotExecuted')]
P6 single-statement conflicts: errors=5 sdk_predicate_true=5 details_kind_TransactionConflict=5 types=['QueryError']
P6 sample: surrealdb.errors.QueryError(kind='Query', details={'kind': 'TransactionConflict'}): There was a problem with the key-value store: Transaction conflict: Resource busy. This transaction can be ret
P6 txn conflict entries: 29 parsed_with_sdk_predicate_true=29
P7 unique collision (query): surrealdb.errors.InternalError(kind='Internal', details=None): Database index `p7_u` already contains 'x', with record `p7:1`
P7 unique collision (query_raw entry): ('Internal', None)
P8 SELECT * keys=['a', 'id'] | explicit projection=[{'a': 'x', 'o': None}]
P9 CONTENT+SET: ERR kind=None details=None {'cause': None, 'code': -32000, 'kind': 'Validation', 'message': 'Parse error: Unexpected token `SET`, expected E
P9 CONTENT+MERGE: ERR kind=None details=None {'cause': None, 'code': -32000, 'kind': 'Validation', 'message': 'Parse error: Unexpected token `MERGE`, expected
P9 object::extend: [{'a': 1, 'b': 2, 'id': RecordID(table_name=p9, record_id='8x9f16ip8wpf7iiw5rw8')}]
P10 RELATE onto undeclared table: [{'id': RecordID(table_name=p10undeclared, record_id='j4h4xbt0gi6wz3376s50'), 'i
P10 auto-created table definition: {}
P10 INFO FOR DB tables.p10undeclared: DEFINE TABLE p10undeclared TYPE ANY SCHEMALESS PERMISSIONS NONE
P11 UPDATE edge out: [{'id': RecordID(table_name=p11e, record_id=1), 'in': RecordID(table_name=p11n, record_id='a'), 'out': RecordID(table_na
P11 edge after: [{'in': RecordID(table_name=p11n, record_id='a'), 'out': RecordID(table_name=p11n, record_id='b')}]
P12 RETURN in txn: statuses=['OK', 'OK', 'OK', 'OK'] rows_committed=[RecordID(table_name=p12, record_id='a')]
P13 IF NOT EXISTS on existing field: status=OK definition_now=DEFINE FIELD f ON p13 TYPE string PERMISSIONS FULL
P14 IN-inside-OR: TableScan=True plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'direction': 'Forward', 'pre_decode_filter': 'yes', 'predicate': "c INSIDE ['c1', 'c
P14 IN alone: TableScan=False plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'predicate': "c INSIDE ['c1', 'c2']"}, 'children': [{'attributes': {'branches': '2',
P14 expanded-OR: TableScan=False plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'predicate': "c = 'c1' OR c = 'c2' OR d = 'd1'"}, 'children': [{'attributes': {'tabl
P14 starts_with: TableScan=False plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'predicate': 'string::starts_with(...)'}, 'children': [{'attributes': {'access': ">=
P14 range-prefix: TableScan=False plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'access': ">='pre00' <'pre01'", 'direction': 'Forward', 'index': 'p14_s', 'predicate
P14 CONTAINSANY []: TableScan=True plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'direction': 'Forward', 'pre_decode_filter': 'yes', 'predicate': 'el CONTAINSANY []'
P14 CONTAINSANY [x]: TableScan=False plan={'attributes': {'projections': '*'}, 'children': [{'attributes': {'branches': '1', 'table': 'p14'}, 'children': [{'attributes': {'access': "= 't1'", '
P14 plain-array index: tags='x'->[] whole-array->[] CONTAINS->['pre0110', 'pre0152', 'pre0051']
P15 16-way first write to an undeclared table: errors=4 kinds=["{'kind': 'TransactionConflict'}"]
P16 virgin bootstrap 3x16 connects: failures=0 sample=[]
P17 subquery-FROM array + field WHERE: [] | node-side filter: [RecordID(table_name=p17n, record_id='l4')]
cleanup: removed sdk3r1_c81f22024b06; sdk3r1* databases left: []
```
SDK 2.0.0 (lore's venv), the SDK-dependent probes (P16 here is likewise the first, same-database version):
```
sdk=2.0.0 url=ws://127.0.0.1:18000/rpc db=lore_test/sdk3r1_6f5eb63a0fb4
P1 in-flight-drop: ["builtins.KeyError(kind=None, details=None): '3d3cf913-e8f2-4d89-a111-1a946e037861'", "builtins.KeyError(kind=None, details=None): '44a2b8cc-6760-4d50-ba01-e651aadeacfc'", "builtins.KeyError(kind=None, details=None): '64000010-8c79-47b8-9e57-9c6566bc4b4f'", "builtins.KeyError(kind=None, details=None): 'f81be125-7bab-4166-8b6a-0e399fac9733'"]
P1 next-call-after-in-flight-drop: websockets.exceptions.ConnectionClosedError(kind=None, details=None): no close frame received or sent
P1 close-after-drop: OK
P2 idle-bounce call 1: websockets.exceptions.ConnectionClosedError(kind=None, details=None): no close frame received or sent
P2 idle-bounce call 2: websockets.exceptions.ConnectionClosedError(kind=None, details=None): no close frame received or sent
P2 idle-bounce call 3: websockets.exceptions.ConnectionClosedError(kind=None, details=None): no close frame received or sent
P4 query() plain: RETURNED [{'id': RecordID(table_name=p4a, record_id=1)}]
P4 query() txn: RETURNED None
P6 single-statement conflicts: errors=53 sdk_predicate_true=0 details_kind_TransactionConflict=53 types=['QueryError']
P6 sample: surrealdb.errors.QueryError(kind='Query', details={'kind': 'TransactionConflict'}): There was a problem with the key-value store: Transaction conflict: Resource busy. This transaction can be ret
P6 txn conflict entries: 52 parsed_with_sdk_predicate_true=0
P7 unique collision (query): surrealdb.errors.InternalError(kind='Internal', details=None): Database index `p7_u` already contains 'x', with record `p7:1`
P7 unique collision (query_raw entry): ('Internal', None)
P16 virgin bootstrap 3x16 connects: failures=0 sample=[]
cleanup: removed sdk3r1_6f5eb63a0fb4; sdk3r1* databases left: []
```
P16, fresh database per round, 10 rounds x 16 connects per run (three SDK 3.0 runs, one SDK 2.0 run):
```
P16 virgin bootstrap 10 fresh dbs x16 connects: failures=0 sample=[]
cleanup: removed sdk3r1_0413555bc528; sdk3r1* databases left: []
P16 virgin bootstrap 10 fresh dbs x16 connects: failures=3 sample=[('use', 'QueryError', {'kind': 'TransactionConflict'}), ('use', 'QueryError', {'kind': 'TransactionConflict'}), ('use', 'QueryError', {'kind': 'TransactionConflict'})]
cleanup: removed sdk3r1_cb1cce33b460; sdk3r1* databases left: []
P16 virgin bootstrap 10 fresh dbs x16 connects: failures=0 sample=[]
cleanup: removed sdk3r1_ea50aeeb6bf0; sdk3r1* databases left: []
P16 virgin bootstrap 10 fresh dbs x16 connects: failures=1 sample=[('use', 'QueryError', {'kind': 'TransactionConflict'})]
cleanup: removed sdk3r1_aed43ae2e71d; sdk3r1* databases left: []
```

## Appendix C — the mutation shadow (`scratchpad/sdk3/sdk3shadow_mutation/sitecustomize.py`, verbatim)

```python
"""SDK3 MUTATION shadow (packet SDK3 round 2, operator ruling R1 rider) — re-introduces ONE old SDK 2.0
defect's symptom on top of shadow #2 (SDK 3.0 + first-statement query()), chosen by $SDK3_MUTATION:

  keyerror     an in-flight drop raises builtins.KeyError (SDK 2.0's response-routing failure)
  noreconnect  connections are built with reconnect=False (SDK 2.0 never reconnected)
  nopredicate  QueryError.is_transaction_conflict answers False (SDK 2.0 shipped no predicate)

A retirement pin that stays GREEN under its mutation proves nothing."""
import functools
import os

import surrealdb
from surrealdb.connections.async_ws import AsyncWsSurrealConnection
from surrealdb.errors import ConnectionUnavailableError, QueryError


class AsyncEmbeddedSurrealConnection:
    """Placeholder: the embedded class needs the uninstalled ``surrealdb-embedded`` extra."""


surrealdb.AsyncEmbeddedSurrealConnection = AsyncEmbeddedSurrealConnection
_MUTATION = os.environ.get("SDK3_MUTATION", "")
_sdk3_query = AsyncWsSurrealConnection.query
_sdk3_query_raw = AsyncWsSurrealConnection.query_raw


async def _first_statement_query(self, query, vars=None, session_id=None, txn_id=None):
    try:
        return await _sdk3_query(self, query, vars, session_id, txn_id).first()
    except ConnectionUnavailableError as error:
        if _MUTATION == "keyerror":
            raise KeyError(str(id(self))) from None
        raise error


async def _query_raw(self, query, vars=None, session_id=None, txn_id=None):
    try:
        return await _sdk3_query_raw(self, query, vars, session_id, txn_id)
    except ConnectionUnavailableError as error:
        if _MUTATION == "keyerror":
            raise KeyError(str(id(self))) from None
        raise error


AsyncWsSurrealConnection.query = _first_statement_query
AsyncWsSurrealConnection.query_raw = _query_raw
if _MUTATION == "noreconnect":
    surrealdb.AsyncSurreal = functools.partial(surrealdb.AsyncSurreal, reconnect=False)
if _MUTATION == "nopredicate":
    QueryError.is_transaction_conflict = property(lambda self: False)
```
