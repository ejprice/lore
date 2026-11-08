# SDK3 — operator rulings

Packet: SDK3 (Python SDK `surrealdb` 2.0.0 → 3.0.0 on SurrealDB 3.3.5).
Packet doc: `docs/plans/v2/sdk3-python-sdk-3-migration.md` (contract author's).
Rulings here are binding on every SDK3 agent (contract author, adversary, builder, cold audit).

## R1 — the inventory is a WORKAROUND RE-EVALUATION, not a preservation list (operator, 2026-11-07)

Operator, verbatim: *"inventory of SDK 2.0 behaviours we rely on — much of which is likely
workarounds for driver or DB bugs that need to be re-evaluated."*

Much of what lore "relies on" exists BECAUSE of a defect in SDK 2.0 or in the engine (3.1.5–3.2.4).
Carrying such code forward with a fresh pin preserves the workaround after its reason is gone.
Ask of every inventory row: *"is this code here because something was broken, and is it still
broken on SDK 3.0 + 3.3.5?"*

Every removed-behaviour inventory row therefore carries:

| column | content |
|---|---|
| origin | `sdk-bug` / `engine-bug` / `design` (lore's own choice, no defect behind it) |
| defect | the finding #, store-ref section, or receipt that documents the bug; `undocumented` if none |
| re-probed | the defect's status on **SDK 3.0.0 + engine 3.3.5**, MEASURED by a probe you run (instrument + output in the packet doc), never inferred from release notes: `still-present` / `gone` / `changed` (describe) |
| fate | `retire` (bug gone → delete the workaround; pin the CORRECT behaviour that now holds natively) · `keep` (bug still present; keep the pinned known bound) · `simplify` (bug changed) · `design` rows use the original preserved / dropped / spec-silent fates |

Scope: not only SDK-2.0-shaped branches. Include the ENGINE workarounds in the store-seam code
that store reference §6.5 / §6.6 / §2 / §3 document, wherever the SDK swap or the 3.3.5 engine
could have changed the underlying behaviour. Examples to evaluate, not an exhaustive list:
- KeyError-as-transport and `websockets.ConnectionClosed*` classification;
- NotAllowed-after-silent-reconnect;
- statement[0]-only validation and later-statement error swallowing (§6.5, §6.6 #10);
- `_is_domain_cascade_notice` root-cause selection;
- the bare `"TransactionConflict"` literal (#111);
- the per-owner `_ensure_connection` self-heal (#576);
- `SELECT *` omitting NONE columns (§6.6 #12);
- `CONTENT` not composing with `SET` (§6.6 #11).

Existing KNOWN-BOUND pins ("this pin goes RED the day someone closes the hole") are the
instrument: run them against an SDK 3.0 scratch build. A known-bound pin going red is a `gone`
signal for that row, to confirm with a probe.

Rider (same sentence, per CLAUDE.md "THE RIDER IS PART OF THE RULING"): **every `retire` row
ships with a pin that FAILS if the workaround is still needed**, i.e. a test that drives the
formerly-broken case through the plain SDK 3.0 path and asserts the correct behaviour, AND a
mutation proof that re-introducing the old defect's symptom reddens it.

Decision rights: a `retire` whose re-probe is unambiguous is decided by the evidence. A row
whose re-probe is ambiguous, or whose retirement changes a served surface, is an operator fork:
list it in the packet doc's forks section.

## R2 — F1: `run_query` returns its ONE statement's result, and refuses anything else (operator, 2026-11-07)

Ruled option A. `_txn.run_query` is lore's single-statement seam (every production caller sends one
statement; multi-statement work rides `execute_transaction`). Under SDK 3.0 `query()` returns one entry
per statement, so `run_query` selects that one statement's result itself, and RAISES when the SDK
returns anything other than exactly one result — never a silent `[0]`. This is the seam's contract,
not a mimicry of SDK 2.0 (which validated only statement[0]).

Rider: `scout._scout_query_once` and `inbox_awaiter._live_query` are converted to the same seam, so
the selection rule lives in exactly one place. Pin it like this: a lost compare-and-swap must read
as lost (the measured SDK 3.0 failure was `[[]]` read truthy, 8/8 racers winning), a counter must
read its scalar, a `LIVE SELECT` must yield its bare id, and a two-statement call must raise; prove
the sharing by mutation (break the selection in the seam — scout and the inbox awaiter must redden
with it).

Rejected: B (per-caller `[0]`, 27 copies of the rule); C (`query_raw` for every statement; unmeasured
outside transactions). Not covered by this ruling: the test harness `run()` fixture.

## R3 — the per-file statement cap is IN SCOPE for SDK3 (operator, 2026-11-07)

Measured 2026-11-07 on production lore-lore boot: `loremaster/tests/test_comms_tool.py` (8,784 lines)
composes to 5,113 statements and `compose()` refuses it (`TXN_STATEMENT_HARD_CAP = 5000`,
`store/_txn.py`), so `index.file.store_failed` → `index.file.failed` and the file is absent from the
index (no chunks, no graph). This pre-dates the 3.3.5 migration. Ruled in scope for this packet;
the mechanism is an open fork (packet doc §5).

## R4 — R3's mechanism: BATCH ROWS (operator, 2026-11-07)

Ruled option A. A file's index write stays ONE atomic transaction, but rows are written as one
batched `INSERT` (or `INSERT RELATION`) per table carrying an array of rows, so the statement count
scales with the number of tables, not rows. The cap is re-expressed as a bound on what strains the
shared server (rows or bytes), not statement count. Rejected: B (raise the cap — moves the ceiling),
C (split a file across transactions — readers see a half-indexed file).

Rider: (1) read `docs/reference/surrealdb-31-capabilities.md` first, and confirm bulk `INSERT` /
`INSERT RELATION` semantics on 3.3.5 (protected keys, RELATE's unvalidated endpoints, CONTENT
datetimes) against the `surrealql-tests` corpus, then a probe; (2) measure test_comms_tool.py's
per-table row breakdown BEFORE choosing the new bound; (3) a file still refused must be NAMED on a
served surface, never silently absent; (4) pin: test_comms_tool.py-sized fixture indexes and is
searchable; a mutation restoring per-row statements reddens the bound pin.

## R5 — F2 + F4 ruled together: reconnect forever, finite timeouts (operator, 2026-11-07)

Grounds (SDK 3.0 source, `connections/reconnect.py` + `async_ws.py::_await_reconnect`): a request in
flight at a drop fails with `ConnectionUnavailableError` and is NOT re-sent; a request made during a
reconnect waits, bounded ONLY by the request timeout; the default policy gives up after 5 attempts
(~1 min) and leaves the connection `disconnected`; `connection.timeout(N)` scopes an override.

- **F2b:** ONE shared connection factory with `ReconnectOptions(attempts=-1, retry_delay=0.5,
  retry_delay_max=2.0)`. This retires the 18 per-owner `_ensure_connection` self-heals (drop list).
- **F4b:** a FINITE default request timeout (keep SDK 3.0's 30 s until measured) plus a NAMED constant
  override, with its rationale, for each known-long operation (startup DDL / `ensure_ready`,
  `REBUILD INDEX`, large index transactions), applied with `connection.timeout(N)`. F4a (`timeout=None`)
  is REJECTED: with F2b it hangs a call forever during a permanent outage.

Riders: (1) the builder MEASURES the longest legitimate operations before setting the overrides;
(2) a timed-out or in-flight-dropped WRITE is raised as "outcome unknown" (the commit may have
happened server-side), never as a plain failure; (3) pins: a call during an outage fails within its
bound; a call after the server returns answers within ~2 s (L6); a long DDL under its override
survives past 30 s. Unknown, stated: whether the engine keeps running a statement whose client
timed out (unmeasured) — which is why rider (2) says "unknown".

## R6 — PRINCIPLE: native SDK shapes over hand-rolled ones; F3, F5–F10, scheduling, S1, S2 accepted (operator, 2026-11-07)

Operator, verbatim: "I prefer to use the native SDK shapes over hand rolling. Otherwise,
recommendations accepted." Applied item by item:

- **F8 (CHANGED by the principle):** NO lore-owned SDK-2.0-shape "served id" function. lore adopts
  SDK 3.0's own `RecordID` rendering (`str(RecordID)`, bracketed digit-led keys) and parses with
  `RecordID.parse` — the four `partition(":")` re-parsers are deleted, not centralised. Consequence
  the contract must carry: values PERSISTED in the SDK-2.0 bare shape (keep scopes, principal refs,
  `audit.target_row`, anything storing a `str(RecordID)`) compare unequal after the bump → a
  migration of persisted id-strings (or storing `record<…>` values instead of strings), sized by a
  read-only count on :18500 run by the lead BEFORE the contract revision.
- **S2 (CHANGED):** the six cloned datetime coercers are DELETED in favour of the SDK's native
  `PreciseDatetime` (a `datetime` subclass), not merged into a seventh shared copy.
- **F7 (CHANGED):** `RecordID.parse` is THE parser; lore keeps no acceptance list of its own.
  Snapshot ids are lore-minted (unreachable widening), so no lore-side validation is added.
- **F3:** yes — keep the engine's nanoseconds (native `PreciseDatetime`).
- **F5:** widen `tests/_sdk_guard.py` to the SDK 3.0 sync builder methods; observed `query` calls are
  a checked variable.
- **F6:** extend `PendingFile` with a pytest-only expected-red node-id list that self-destructs when
  green (a gate change).
- **F9:** keep the `>=`/`<` range, re-classified as design (see the open question below).
- **F10:** retire the `KeyError` arm now; keep `WebSocketException` until the builder measures the LIVE
  iterator and `kill()`-over-dead-socket paths. Target state per the principle: classification by the
  SDK's own `TransportError` / `ConnectionUnavailableError`, with lore's hand-kept error lists retired.
- **Scheduling:** SDK3 before the dormant 58 / 63c / 64b.
- **S1:** in scope — scout's drop goes away with R5's shared factory.
- **R2 stands:** `run_query` consumes the SDK's native per-statement list and selects its one
  statement — that is the seam's contract, not a reshaped copy of SDK 2.0.

## R7 — after the 4.0 scout: F8/F7 re-ruled, R5 amended, db.batch conditional, SDK pinned, F9 native (operator, 2026-11-07)

Grounds: scout-40-sdk3 (throwaway v4.0.0 + v3.3.5 memory containers, SDK 3.0.0 and 3.0.1 @ 05d3192), receipts
`scratchpad/scout40/REPORT.md` + probe scripts beside it. R2, R4, the R5 API, F3, F9 and F10 hold on 4.0 unchanged.

- **F8/F7 (REPLACES R6's F8/F7 bullets).** SDK `str(RecordID)` changed between 3.0.0 (`keep:⟨01J…⟩`) and 3.0.1
  (``keep:`01J…` ``), and `RecordID.parse` is `split(":", 1)` — `parse(str(rid)) != rid` on both. The ENGINE renders
  the bare form (`keep:01J…`) lore already persists, so persisted bare strings need NO migration. Ruled, all
  SDK-native: (a) record ids travel as `RecordID` values end to end; prefer storing `record<…>` values over
  strings; (b) build ids with `RecordID(table, key)` from `.table_name` / `.id`, never by parsing text;
  (c) text → id via `StringRecordId(text)` (server-parsed; reads both bracket styles); (d) served/persisted text
  comes from the engine (`<string> id`) or `.table_name + ":" + .id`, NEVER `str(RecordID)`. The four
  `partition(":")` parsers are deleted. Lead's read-only :18500 check stays: no persisted id string was written
  BRACKETED by SDK 2.0 (which bracketed all-digit / non-word keys).
- **R5 amended.** "Unknown, stated" is replaced by the measurement (both engines, memory engine): SDK streaming
  default + timeout → the SDK sends a stream cancel, nothing commits; disconnect mid-flight → nothing commits;
  `streaming=False` + timeout → the ENGINE KEEPS RUNNING AND COMMITS; client transactions never stream. Rider (2)
  ("outcome unknown") is CONFIRMED. The shared factory sets streaming EXPLICITLY, pinned. Override wording:
  `with db.timeout(N):` (context manager). Bound: SurrealKV/RocksDB unprobed; a commit racing the cancel unconstructed.
- **`db.batch()` (native) — CONDITIONAL.** The contract pins the transaction behaviour lore needs (root-cause
  selection incl. domain-cascade notices, conflict typing, no writes on failure); the builder uses SDK `db.batch()`
  in place of `_txn.compose` + root-cause selection IF it passes those pins, else keeps `compose` and files the gap
  upstream. (Packages-over-hand-rolling: decided by measurement.)
- **W6 contract wording.** `query()` on a conflicted transaction raises the FIRST failure (`NotExecuted`,
  `is_transaction_conflict=False`); the retirement pin drives the transaction path through the root-cause selector.
- **SDK pinned `surrealdb==3.0.0`** (3.0.1 unpublished on PyPI as of 2026-11-07).
- **F9 — native (REPLACES R6's F9 bullet).** The native principle extends to the engine: retire the `>=`/`<`
  range for `string::starts_with` (index-served by range on 3.3.5 and 4.0, measured). Retire with a pin + mutation
  like RP1–RP3 (the pin proves the native form is index-served via the shared EXPLAIN walker).
- **4.0 flags (NOT this packet; for the 4.0 upgrade packet):** compatibility level 4 refuses narrowing
  `DEFINE FIELD OVERWRITE` on populated tables (MIGRATE EXISTING ROWS); `INFO FOR DB/TABLE` key sets change;
  `RETURN` inside a transaction commits the rest on 4.0; 3.x→4.0 in-place upgrade is experimental, one-way,
  RocksDB → SurrealKV.

## R8 — round-3 contract: drop list and forks F11–F17 (operator, 2026-11-07: "Approved.")

Contract `496d745` (packet doc "ROUND 3" §R3.0–R3.11). The DROP LIST (§R3.5, 31 rows) is APPROVED AS FATED: R rows
retire with their named pins; C rows retire only when their named measurement passes, and the builder reports each
C row's measurement and resulting fate; K rows stay. The removed-behaviour inventory X1–X17 (§R3.6) is the
adjudication record — X8, X12, X13 carry their stated consequences into the build. Lead measurement (read-only,
:18500, 2026-11-07): ZERO persisted id strings written bracketed across `lore/lore` and `lore/demand_intelligence`
(control fired on `⟨⟩` and backtick, not on bare or NONE; populated fields checked: memory.supersedes 26,
task.blocked_by 38, task.superseded_by 11, agent.task_id 15, message.refs 860, file.chunk_ids 5,885; the scope
columns and audit.target_row are empty in prod, so the zero is vacuous there) → no persisted-id migration (R7 holds).

- **F11 — streaming ON**, set explicitly by the shared factory and pinned (CF4), because `streaming=False` + timeout
  lets the engine commit after the client gave up.
- **F12 — the row bound REPLACES the statement cap everywhere**: `TXN_ROW_HARD_CAP` is the one bound; packet 58's
  packer and the entity seam re-size by rows; the statement-cap pins become row-cap pins (and pin it: a build that
  keeps the statement cap anywhere goes RED).
- **F13 — scout and the inbox awaiter call the shared one-statement selection function**, not `run_query` (keeps
  the W1-SCOUTKILL raw-error contract); sharing proven by mutation (M-R2).
- **F14 — every SDK `TransportError` on a request maps to `SurrealOutcomeUnknownError`** (the seam cannot tell a
  read from a write, nor sent from queued).
- **F15 — the engine form (`<string> id`) is the text form for anything persisted or compared with persisted
  text**; `.table_name + ":" + .id` only where no persisted comparison exists.
- **F16 — all ~31 parser sites (3 families) are deleted under R7**, not only the four R7 named.
- **F17 — bare text with no `:` maps to `RecordID(<that API's table>, text)`.**

## R9 — after adversary round 1: lead decisions under the autonomy grant (2026-11-07; operator MAY OVERTURN)
Grant (operator, verbatim): *"3 more contract and two more adversary rounds approved. Work autonomously and finish
the SDK migration."* Adversary round 1 graded `d84cd6c` **INSUFFICIENT**: MP1 (F12's rider dropped — the reference
keeps the statement cap live and passes), MP2 (F14 pinned only on CREATE/BEGIN — a verb-sniffing build survives),
MP3 (R5's named overrides pinned on one owner only — `PrincipalStore.ensure_ready` and an index `apply` time out at
30 s on the reference). These go to contract round 4. The adversary raised three decisions; the lead ruled them:
- **D1 — R5 rider 2 ("never as a plain failure") covers SERVED surfaces.** `server.py`'s finding batch-resolve
  renders any `SurrealConnectionError` — so every `SurrealOutcomeUnknownError` — as "ABORTED … retry these": a
  resolve whose commit may have landed is served as aborted and the agent is told to re-apply it (a Leg-2 false
  clear; F14 widens it to every transport failure). In scope; round 4 pins it ∀ served catch sites of
  `SurrealConnectionError` (prior art: `principal_keys._mint_fault_note`, `_txn.proven_no_key`).
- **D2 — `TXN_STATEMENT_WARN_THRESHOLD` (800) becomes a ROW warn.** F12 makes rows the one strain measure; a
  statement-count warn beside it is a second source of truth. Low stakes (a log line).
- **D3 — the ~40 pre-existing tests that encode retired rulings (statement cap, KeyError-as-transport,
  `_RETRYABLE_CONFLICT_KIND`) are CONTRACT SURFACE.** Round 4's author rewrites them, not the builder (§R3.10's
  hand-off to the builder crossed the implementer → test-author role boundary). Each verdict is confirmed by a run
  (the adversary's TRAP list was 2/4 wrong on `test_surreal_apply`).
Raised to the operator, NOT decided: RS9 — drop row #22 (`retry_on_conflict`, K) was kept without checking
`tenacity` (installed, the global default for retries); changing an approved K row is the operator's call.

## R10 — drop row #22 (`retry_on_conflict`) re-fated K → C: evaluate `tenacity` (operator, 2026-11-07)
Operator, verbatim: *"Evaluate it for replacement but keep it if it works better."* (answering R9's RS9.)
- **Fate C:** `tenacity` (installed, 9.1.4; the global default for retry/backoff) replaces the hand-rolled
  `retry_on_conflict` **iff** a tenacity build is at least as good, measured; otherwise the hand-rolled one stays,
  with the measurement as its keep-reason. Equal ⇒ replace (packages over hand-rolling).
- **Gate (and pin/measure it like this):** the tenacity build must (1) pass every existing conflict-retry pin
  unchanged — T1, T2 (16-way, both paths), RP3, `test_retry_seam.py`; (2) classify conflicts through the seam's own
  predicate (`_is_retryable_conflict_kind` / the root-cause selector) — a tenacity `retry=` that matches text locally
  is ROUTING-NOT-SHARING and fails the gate; (3) keep a full-jitter wait (`wait_random_exponential`, not
  `wait_exponential_jitter`) and the same attempt budget unless the measurement says otherwise; (4) measure both
  builds on T2's 16-way contention over 20 runs — attempts-to-success and wall time, mean and max. "Works better" =
  fewer lost/failed transactions first, then lower max wall time; ties go to tenacity.
- **Who:** contract round 4 reports whether tenacity's API can express (1)–(3); the builder runs (4) and reports the
  row's measurement and fate like every other C row (R8); the cold audit verifies that receipt.

## R11 — every hand-rolled retry goes onto tenacity; SUPERSEDES R10 (operator, 2026-11-07)
Operator, verbatim: *"If our retry is hand rolled use tenacity."* R10's measured keep-if-better conditional is
withdrawn, and so is #202's "deliberately NOT churned" fence on `_txn.retry_on_conflict`.
- **In this packet (66):** drop row #22 is fated **R**. `retry_on_conflict` becomes a tenacity `AsyncRetrying`
  (stop = the existing attempt budget / `deadline_seconds`; wait = `wait_random_exponential`, i.e. full jitter, via
  `loresigil.backoff`'s shared policy; `retry=` = the seam's own `is_retryable_conflict_error` / root-cause selector)
  and `_txn_conflict_backoff_seconds`'s private `uniform` draw is deleted. `scout._backoff`'s hand loop converts the
  same way. **And pin it like this:** T1, T2 (16-way, both paths), RP3 and `test_retry_seam.py` stay green UNCHANGED;
  a mutation of the seam's conflict classifier reddens the retry path (sharing by mutation, as M-W6); a `retry=`
  that matches error text locally is ROUTING-NOT-SHARING and fails audit. Removed-behaviour inventory covers the
  deadline, the rollback log per attempt, and the attempt-count/exhaustion fate.
- **Outside this packet:** the five loops that already use tenacity's wait but loop by hand go to packet **68**
  (INDEX row), after 66 and before 65-cut.

## R12 — round-4 forks (lead, under the autonomy grant, 2026-11-07; operator MAY OVERTURN)
Contract round 4 committed `b655971` (packet doc §ROUND 4 R4.0–R4.13, Appendix E). Its forks, ruled:
- **F18 — D1 reaches the `SurrealStoreError` family too (14 sites).** `briefs.BriefLedger.publish` hands back the
  version it minted when a publish that may have committed fails, so the version can be minted twice. The other ~39
  broad-catch sites each get a one-line verdict in the inventory; a pin only where the site renders a definite failure.
- **F19 — packet 58's re-size by rows is pinned at a SHRUNK cap** (monkeypatched, per F21), never a 50,000-row
  fixture. 58 is dormant: its own contract owner writes those pins; SDK3 states the bound.
- **F20 — F14 does NOT reach scout or the inbox awaiter.** F13 keeps their raw-error contract.
- **F21 — the row cap and the row-warn threshold are read live from `_txn`.**
- **F22 — R11 amended (its "test_retry_seam unchanged" clause contradicted deleting the draw):**
  `_txn_conflict_backoff_seconds` stays as the ONE conflict-jitter source (9 consumers via `_record_shared_jitter`)
  but DELEGATES to tenacity `wait_random_exponential` through `loresigil.backoff`; its private `uniform` draw goes.
  `test_backoff_seam`'s source-text clause (a spelling check) retires; its behaviour clauses stay.
- **F-a — fakes answer per SDK version for the interim** (so HEAD stays green until the build lands); the SDK-2.0
  branch is a drop-list row the builder deletes in the same commit that pins `surrealdb==3.0.0`.
- **F-b — a server-ANSWERED error (e.g. `NotAllowedError`) is a definite failure, never outcome-unknown.** Pinned:
  F14 covers transport only, and an "unknown" that should be "failed" teaches agents to ignore the label.
- **F-c — not pinned** (whether a propagating `KeyError` keeps the connection is not a served behaviour).
- **F-d — C7's KeyError-tuple reach check retires**: after the arm's removal it finds nothing (a vacuous guard).
- **C9 is an SDK3 REGRESSION, not noise.** `test_fixwave_a28_63c_i_a::TestTheMeasuredCountsAreTypedFields63cIAa28`
  passes 42/42 ×3 at HEAD on SDK 2.0 (lead, 2026-11-07) and fails nondeterministically on BOTH SDK3 references
  (`owner_classification 'foreign'`) — round 4's "0 attributable reds" is wrong for it. Contract round 5 pins it
  deterministically (a digit-led / non-word principal key) and the builder fixes the comparison.
- **Raised to the operator:** whether reusing the `_catch_sites` walker for D1's catch-site reach pin is a new
  source scanner (global law: a new scanner needs approval). Kept pending the answer.
- **RS7 — `SurrealStore.upsert` (0 production callers, outside batching and the row cap) is DELETED**, not routed
  through `compose`: a dead door with no consumer is removed (drop-list row; the builder re-confirms 0 callers).
- **X18/X19 (nested `PrincipalStore` close in `KeepStore`/`PrincipalKeyStore`; `LocalMemoryBackend._rebuild_lock`)
  are pinned by behaviour in round 5**, since the shared factory replaces the code that carries them.
- **C9's class is PINNED, not handed to the builder (lead, 2026-11-07).** Root cause: `principals._measured_counts`
  and `_owned_unscoped_part` compare `str(RecordID)` with a differently-rendered id. CLASS: *one record compared
  through two text forms*. The four at-risk siblings found by the round-5 sweep get pins in round 5:
  `governed.py` `_bare` (feeds `pdp.Resource` — an ACCESS decision, first priority), the served refusal text in
  `principals.py` (message ids are ULIDs, always digit-led, so always bracketed under SDK 3.0's `str()`), and
  `memory/local.py`'s two owner compares (verify the `record_id` guard by execution).

## R13 — round 5 (lead, under the autonomy grant, 2026-11-07; operator MAY OVERTURN)
Round 5 committed `0ac1434` (C9) + `082d2f2` (the rest; packet doc §ROUND 5 R5.0–R5.11, Appendix F). Lead re-ran
RED@HEAD (23 declared = 23 observed) and the typecheck/ruff currency (RED_ORPHANED 0). The a28 class now passes 42 ×3
on the round-5 reference (C9 fixed there).
- **Satisfiability is NOT yet shown for R11.** ~29 nodes are red on the round-5 reference, green at HEAD and green on
  the r4 baseline — nearly all from its tenacity/scout port (`test_retry_seam` 11, `test_scout` 13, the scout CAS
  pin, a19's sanitise-routing pin, two a19-householding pins). Adversary round 2 builds its OWN reference anyway; it
  must classify each as REFERENCE BUG (a correct port passes it) or CONTRACT CONTRADICTION (no correct port can — e.g.
  a scan of `_ensure_connection` callers, or a pin on one jitter draw per attempt where tenacity draws `wait` before
  `stop`). Contradictions go to round 6.
- **RS7 REVISED: `SurrealStore.upsert` is KEPT and routed through `compose`** (so it sits under the row cap), not
  deleted. It has 0 production callers but 90 test fixture call sites in 7 files; deleting it buys nothing a consumer
  notices and costs 90 edits. Supersedes the R12 addendum's deletion line.
- **C10 — `_surreal_harness.run` and `_sdk_guard` SDK-3 adaptations are BUILDER work** (test infrastructure, not
  pins encoding a ruling; R9 D3 does not reach them). The build lands SDK 3.0 in one commit, so no interim
  version-awareness is needed there.
- **F-r5-1 — `_POW_ALLOWLIST` drops `_txn.py` in the build commit** (after R11 `_txn` keeps no private power ladder).
- **F-r5-2 — an unknown-outcome publish PROPAGATES the error** (no verify-and-return).
- **F-r5-3 — gap, to round 6 if the adversary confirms it:** the indexer pin admits a build that raises out of
  `index_all` and aborts the sweep; an unknown commit on one file must not stop the others.
- Found by round 5, recorded: SDK 2.0 is already wrong at HEAD for NON-WORD principal/agent keys (governed gate
  denies the owner; memory replay revives a predecessor) — latent today (lore mints no non-word keys), live under
  SDK 3.0 for ~28% of principals (digit-led). The round-5 pins cover both.

## R14 — the catch-site reach pins (operator, 2026-11-07: "B")
Both walker-derived reach pins STAY — `test_sdk3_served_outcome::TestEveryCatchSiteThatNamesTheTransportErrorIsAdjudicated`
(round 4) and `::TestEveryStoreErrorFamilyCatchSiteIsAdjudicated` (round 5). They reuse the ONE catch-site walker
(`loremaster/tests/_catch_sites.py`, packet 58 amendment 9) and are approved as scanners. **Round 5's clause that
checks each "pinned" verdict row names an existing test is REMOVED** (a test about tests). Stated bound: the walker
sees only handlers that name the class (or its family); a bare `except Exception` site is adjudicated by hand
(§R5.1's 39-row table) and is not guarded — re-open trigger: a served false "failed" traced to such a site.
Owner of the removal: contract round 6 if the adversary sends one; otherwise a minimal contract touch before the builder.

## R15 — adversary round 2: INSUFFICIENT → contract round 6, the LAST (lead, under the grant, 2026-11-07)
Adversary round 2 graded `d90936d`. **R11 has NO contract contradiction:** a correct tenacity port passes all 26
attributable retry/scout nodes; every one was a reference bug. Root cause, a tenacity trap the builder must know:
`AsyncRetrying.__call__` never awaits the result of a NON-coroutine callable (`retry_on_conflict(lambda: …)` returns an
un-awaited coroutine), and tenacity computes `wait` BEFORE `stop` (an adapter must not draw on the exhausting attempt).
All five round-1 survivors are now killed. Missing, routed to round 6:
- **MP-A (F-r5-3 confirmed):** an unknown-outcome commit that did NOT land raised out of `index_all` aborts the sweep.
  Pin: one file's store fault never stops the sweep, whatever its outcome class (batch + realtime legs).
- **MP-B:** the driver can consult the shared jitter source and sleep something else (equal jitter) with 0 new reds.
  Pin: every slept backoff equals the drawn full-jitter value (extend the draw-count pin with `slept == drawn`); sibling:
  scout's connect wait.
- **MP-C — SATISFIABILITY, the property:** *every targeted node GREEN AT HEAD is GREEN on the SDK-3 reference*, measured
  against HEAD (never against an earlier reference), with a C10 harness in the reference. 117 nodes fail it today
  (F-a fakes not applied beyond the 3 C1 doubles; C2 `route_connections` not applied; the C9 class in the TEST tree —
  test-side `str(RecordID)` vs engine/bare text, ~30 cloned `_bare` helpers; the StoreTraffic instrument counting at
  `query_raw` while SDK-3 `query()` bypasses it; am-37 adjudication rows missing for `SurrealOutcomeUnknownError` and
  `TxnRowCapExceededError`; `test_ingest_entity_seam` ×8 `links=[]` UNTRACED; a19's `_renderings`).
- **Ownership rulings (R9 D3 extended):** the StoreTraffic instrument and the am-37 rows are CONTRACT surface (guard
  instruments and ruling tables, not plumbing). Pre-existing spelling scans that encode RETIRED rulings — the
  socket-owner AST scans ×2 (R5 F2b) and `test_derivation_source_unification`'s `RELATE` regex ×3 (R4) — are rewritten
  as behaviour pins or retired with a one-line reason. The governed SDK-name scan that now false-fires on contextvar
  `.set()/.reset()` (SDK 3 added `set`/`reset`) is narrowed to SDK receivers — it fires on correct code. The proxies
  that a correct port PASSES (the `_ensure_connection` caller scan #127, the `last_conflict_cause` scan) stay.
- **Also round 6:** RS7's rider (an `upsert` batch over the row cap is refused — R13 ruled routing, nothing pins it);
  R14's removal of the "pin row names a real test" clause; stale drop-list rows #21/#22 (row #22 is R since R11; #21
  overlaps R11); a named per-C-row receipt table for the cold audit.
- **Builder (not contract):** C10 `_surreal_harness.run`; the `store/surreal.py` `ensure_ready` timeout routed through
  `long_operation` like the other 16 owners.
Round 6 is the last contract round and adversary round 3 the last adversary round in the operator's budget; a
contract still unsatisfiable after them goes back to the operator, not to a seventh round.

## R16 — budget extended; build follows (operator, 2026-11-08)
Operator, verbatim: *"Add one more contract and adversary to the budget if need, then go to build."* Budget now: contract
round 7 and adversary round 4, each only if needed. After the last adversary round the packet goes to BUILD: Opus
builder → cold audit → ONE full suite (flock, -n 12) → in-image conformance against a COPY of :18500 → close-out.
Missing pins still open at that point travel to the builder brief and the cold audit as NAMED residuals; an
UNSATISFIABLE pin (red on every correct build) is the one thing that still stops a builder, since a builder may not
edit tests. Still NO prod deploy (65-cut owns it).

## R17 — the governing test (operator, 2026-11-08)
Operator, verbatim: *"And we must hold to consumer law and the trust doctrine. Agents are lores clients."* Every
remaining ruling, contract pin, build decision and audit verdict in packet 66 is judged against repo CLAUDE.md's
Consumer Law + Trust Doctrine: a served response is trustworthy iff an agent acting on it WITHOUT CHECKING cannot be
wrong in a way the response did not name (Leg 1 scope diff; Leg 2 forgery pins by construction). Sharpest here:
outcome-unknown vs failed (F14/D1/F18), served id text (F15/C9), refused-file naming (R4), retry teaching prose. The
builder and cold-audit briefs carry this as a numbered first criterion; the design sidecar rules under it.

## R18 — tenacity used NATIVELY, not as a jitter RNG behind hand-rolled loops (lead, 2026-11-08; amends R12-F22; sidecar MAY amend)
Operator, 2026-11-08: *"I got the sense that we're not fully using Tenacity and instead are plugging it in to satisfy
the no hand rolling bypassing the spirit of the rule. Is that true?"* — lead's answer: partly yes. `loresigil.backoff`
drives `wait_random_exponential` through a fake `RetryCallState` while every loop stays hand-written (#202's fence), and
R12-F22 kept `_txn_conflict_backoff_seconds` + 9 draw-COUNT pins, which forced a `_wait` that pre-checks `stop` and then
MP-B's "slept == drawn" pin — tests of the old implementation shaping production around tenacity. Under R11's spirit:
- **`retry_on_conflict` is a native `AsyncRetrying`:** `stop=` composed from `stop_after_attempt`/`stop_after_delay`
  (per-call deadline), `wait=wait_random_exponential(...)` DIRECTLY (full jitter), `retry=retry_if_exception_type(
  RetryableConflictSignal)` (classification stays in the seam — sharing, not routing), `retry_error_callback` raising
  `TxnContentionExhaustedError` with the attempt count and the last cause, `before_sleep`/`after` hooks for logging, an
  `async def` callable (tenacity never awaits a plain callable's coroutine). `_txn_conflict_backoff_seconds` and its
  private draw are DELETED; so is the `stop`-peeking `_wait` adapter.
- **Pins move from implementation to behaviour (and pin it like this):** attempts ≤ budget and deadline honoured; every
  slept delay lies in `[0, min(cap, base·2^(n-1)))`; ≥8-way racers do NOT sleep identical sequences (decorrelation —
  T2's 16-way contention stays green); exhaustion = the typed error + exactly one log record with the last cause; a
  non-conflict error propagates untouched after one attempt; a mutation of the seam's classifier reddens the retry
  path. The 9 draw-count pins (`_record_shared_jitter`) and MP-B's slept==drawn pin are RETIRED as implementation
  pins (R9 D3: pins encoding a retired design are contract surface).
- **Scout's connect loop:** `async for attempt in AsyncRetrying(...)` with native wait/stop — no detached RNG call.
- **Packet 68 firmed:** the five other loops become native `AsyncRetrying`/`Retrying`, and `loresigil.backoff`'s fake-
  `RetryCallState` shim is DELETED (not "if no caller needs it"); `additive_jitter` for Retry-After stays only if
  tenacity has no native form (check `wait_combine`/`wait_chain` against the installed source first).
Routing: contract round 7 (R16 budget) rewrites the retry pins; round 6 is in flight and is not steered mid-run.

## R19 — design sidecar ruling 1 (design-sidecar-66, Fable, under the operator's 2026-11-08 delegation; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-1.md` (archived from the sidecar's scratch at close-out).
- **CONFIRMED:** R9 D1/D2/D3; R12 F18, F19, F21, F22 (since amended by R18), F-a…F-d, C9, X18/X19; R13 F-r5-1/2/3; R15
  MP-A/MP-B/ownership. No operator ruling should be reversed.
- **R12 F20 bound re-worded:** scout has no claim-before-dispatch — the CAS is the terminal MARK after the handler ran
  (`scout._dispatch` → `_mark`), so the true bound is AT-LEAST-ONCE across a lost mark reply, as `_mark`'s docstring says.
- **R13 RS7 confirmed + rider:** the kept `upsert` is `apply([replace_file_fragment(...)])`-shaped with zero private
  row-building or SQL, proven by one fragment-builder mutation reddening the upsert pins.
- **R13 C10 OVERTURNED in part:** `_sdk_guard` and `_surreal_harness.run()` are CONTRACT surface (the guard that fails
  tests when a build escapes the seam; run()'s rule — first statement vs R2 raise vs list — feeds `drop_database` and
  the #486 reaper, so it is stated, not chosen by a builder). The builder keeps only the `store/surreal.py` `ensure_ready`
  timeout routing.
- **R15 MP-C sharpened:** a BOTH-WAYS node-id diff against HEAD on the same test tree — green@HEAD ∖ green@ref = ∅ AND
  red@HEAD ∖ red@ref = the DECLARED set. The narrowed governed scan must still fire on a positive control.
  `test_ingest_entity_seam` ×8: TRACE BY EXECUTION (index one fixture on HEAD and on the reference; both-ways diff of
  refers/answers_to/entity-edge row counts) and add an edge-COUNT pin to the B family (B4 proves no dangling edge;
  nothing proves no MISSING edge).
- **Open questions, adopted as recommended:**
  - **Q1 — the conformance image is NEVER tagged `latest`:** tag it `sdk3-conform-<sha>`, and the close-out carries a
    receipt that `latest`'s image id is unchanged — else the next `lore-deploy start` ships SDK 3 to :18500 by
    accident (packet 66 has no prod deploy).
  - **Q2:** the :18500-COPY conformance run greps for `TransportTimeoutError` / `SurrealOutcomeUnknownError` (expected 0)
    and names the slowest served tool; non-zero fires R5's "until measured" on the 30 s default.
  - **Q3:** at close-out the lead adds store reference §0b "SDK 3.0.0 receipts" (its §3/§6.5/§6.6 teach SDK 2.0 today).
  - **Q4:** drop rows #29/#30 (keepalive, version gate) accepted, recorded in §0b.
  - **Q5:** no cron/timer runs any `scripts/` SDK site; unported scripts get a header naming the bound; port only
    named re-runs.
  - **Q6:** D1's served advice splits by shape — "write: verify before retrying / read: safe to re-run".
  - **Q7:** the ~30 `_bare` clones collapse to `bare_record_key`, proven by mutation.
Routing: everything contract-side not already in round 6 (C10 split, RS7 rider, entity-edge count pin, Q6, MP-C
both-ways form, governed-scan control) goes to contract round 7 with R18.

## R20 — design sidecar ruling 2: R18 CONFIRMED in direction, four clauses AMENDED (design-sidecar-66; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-2.md` (also the R17 Leg-1/Leg-2 retrofit table for
ruling 1's served-surface verdicts). Verified against installed tenacity 9.1.4: `wait_random_exponential` is HEAD's
jitter law exactly, `stop_any`/`stop_all` is HEAD's predicate, `retry_error_callback` replaces the RetryError raise,
`sleep=` is injectable, and an unslept final draw is native and harmless once nothing counts draws.
- **A1 — no per-attempt logging hooks.** `before_sleep`/`after` logging would break X22 (exactly one exhaustion record,
  nothing on a resolved conflict; p50 ≈ 2 attempts per mint ⇒ a log storm). The one record lives in
  `retry_error_callback`; unused hooks are omitted. `before_sleep_log` is NOT used here.
- **A2 — CONVERT, don't delete, the recorder's CONTROL uses.** `_record_shared_jitter` has 8 call sites (sidecar's grep;
  R12/R18 said 9 — re-derive at round 7), several of which are premises ("an empty scout claim did NOT back off"; the
  16-way family's "the run actually RETRIED"). Deleting them lets T2 pass vacuously on a never-retrying build (a Leg-2
  false clear). They move to observing the SLEEP call through tenacity's `sleep=` seam (or the asyncio.sleep patch);
  only the draw-COUNT assertions retire. MP-B becomes native: only "slept", no "drawn".
- **A3 — add a distribution pin** (R18's window + decorrelation pins admit the adversary's `wb_r11_sleepdrift`, whose
  `w/2 + d/2` stays in-window and decorrelated): ≥256 recorded sleeps at a fixed attempt index ⇒ min < w/8 AND max > 7w/8
  (false-red ≈ 3e-15). Control: `wb_r11_sleepdrift` must go RED.
- **A4 — ONE native wait FACTORY stays in `loresigil.backoff`** as the policy chokepoint once the fake-`RetryCallState`
  shim dies: `full_jitter(base_s, cap_s) -> wait_random_exponential(...)` and `jittered_fixed(delay, width) ->
  wait_fixed(delay) + wait_random(0, width)`. Sharing proven by mutation: factory → `wait_fixed(SENTINEL)` ⇒ every
  site's slept value == SENTINEL. The AST perimeter scan stays; `_POW_ALLOWLIST` empties (F-r5-1).
- **Native mechanisms, verdicts:** `sleep=` USE (the test seam); a `wait_base` subclass `wait_retry_after` combined with
  `wait_random` for Retry-After USE in packet 68 (tenacity has no built-in Retry-After reader; `wait_chain` is not
  it); `wait_fixed + wait_random` for the lease boot pause USE in 68; `RetryableConflictSignal(TryAgain)` optional
  (keep the explicit `retry=`); `stop_before_delay` not HEAD's semantics; the exhaustion pin counts with the attempt
  body's own counter, not tenacity statistics.
- **R17 legs for R18:** Leg 1 — the exhaustion text answers "did NOT commit after N attempts", which is what the agent
  asks; a conflict is server-answered ⇒ definite (F-b), never unknown. Leg 2 — driver × {never-retries → T1/T2
  premise (A2); over-retries a transport-unknown → F14 zero-retry pins; correlated jitter → A3; UN-AWAITED coroutine →
  pin that `retry_on_conflict` RETURNS THE ATTEMPT'S VALUE for a lambda-shaped caller}.
Routing: contract round 7 implements R18 as amended here.

## R21 — SDK-2.0 tests may be updated, modernized or removed (operator, 2026-11-08)
Operator, verbatim: *"Updating, modernizing or removing tests for SDK 2.0 is authorized."* Consequences:
- **Contract authors (round 6/7)** may rewrite or delete any test that encodes SDK-2.0 behaviour or shapes (list-shaped
  results, KeyError-as-transport, per-module `AsyncSurreal` patching, `str(RecordID)` text oracles, the statement cap,
  `_RETRYABLE_CONFLICT_KIND`, draw-count implementation pins). **F-a simplifies:** fakes answer SDK-3 shapes only — no
  version-aware interim branch; the RED-at-HEAD set grows accordingly and is DECLARED from `--collect-only`.
- **The builder** may also update/modernize/remove a test whose failure on the SDK-3 build is caused by an SDK-2.0
  shape or behaviour. This relaxes the implementer→test-author boundary for THAT class only. And pin it like this:
  every such edit is listed in the build report (file::test, old SDK-2.0 behaviour → new form, or REMOVED + reason);
  no edit may weaken a pin of an SDK-3 ruling (R1–R20) or a consumer-facing behaviour (R17); the cold audit's
  contract-blind diff pass adjudicates each listed edit, and an unlisted test edit is a NO-GO.
- **MP-C's property amended:** every targeted node green at HEAD is green on the SDK-3 reference, OR it encodes SDK-2.0
  behaviour and is rewritten/removed with a named verdict. An SDK-2.0-only test that no correct SDK-3 build can pass
  therefore no longer stops a builder (R16's one remaining blocker narrows to pins of SDK-3 rulings).

## R22 — design sidecar ruling 3: R21's reading CONFIRMED with three riders (design-sidecar-66; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-3.md`. The riders make "listed" and "does not weaken"
checkable by construction:
- **Separate commit + both-ways diff.** The builder's SDK-2.0 test edits land in a commit SEPARATE from the production
  change. Run the targeted set on the pre-edit tree against the build (red set R1) and on the post-edit tree (R2):
  every node in R1∖R2 must be touched by a LISTED edit (else an unlisted edit hid a red → NO-GO); every listed edit's
  node must be in R1 (else it had no SDK-2.0 cause → adjudicate); R2∖R1 = ∅. The contract-blind pass reads only the
  exceptions.
- **"Encodes SDK 2.0" is a VERDICT with an inventory row, never a label.** Each removed/rewritten test names the
  behaviour it certified at HEAD and one fate — carried-by <new pin id> · retired-with drop-list row #N · old-bug #… —
  recorded in the am-37 adjudication table (contract surface per R15). MP-C's escape clause is bounded by that
  inventory.
- **Interim reds are owned.** SDK-3-only fakes (F-a) redden HEAD until the build: register those nodes under F6
  `red_nodeids` (owner: SDK3 builder; trigger: the build commit), so currency never reads RED_ORPHANED in the interim.

## R23 — the builder does NOT edit tests; a standing contract author services its requests (operator, 2026-11-08)
Operator, verbatim: *"Let's not have the builder editing tests. Have it send it back and keep a contract author alive
to service those requests."* **R21's builder clause is REVOKED** (contract authors keep R21's authority to update,
modernize or remove SDK-2.0 tests); R22's riders now bind the SERVICING AUTHOR's edits instead of the builder's.
- **Builder:** never edits a test file. A test that fails on its build for a reason it believes is SDK-2.0-encoded, a
  contradiction, or a defect goes back as a REQUEST (file::test, the failure line, the cause it believes, the edit it
  proposes), posted on lore_comms to the servicing author, plus a native wake while that author is at rest. The builder
  keeps building and drains its lore_comms inbox at its turn boundaries for the answer.
- **Servicing contract author (long-running, Opus, keeps the last contract round's context — the round-7 author if
  round 7 runs, else a fresh one briefed on rounds 1–6):** stands by at rest; per request it rules REWRITE / REMOVE
  (with an am-37 verdict row: carried-by pin · retired-with drop-list row · old-bug) / REFUSE (the build is wrong —
  the test stays), edits only tests, proves the edit (RED→GREEN on the build for the stated reason; no weakening of an
  R1–R22 pin or an R17 behaviour), and replies on the thread. The design sidecar rules any fork it raises.
- **Lead:** commits each servicing batch by explicit path in a commit SEPARATE from the builder's production commits
  (R22 rider 1's both-ways diff runs over those commits); the cold audit's contract-blind pass adjudicates every
  servicing edit, and any test edit authored by the builder is a NO-GO.

## R24 — design sidecar ruling 4: R23's channel CONFIRMED, six holes closed (design-sidecar-66; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-4.md`.
1. **The builder's request is a claim** → the servicer REPRODUCES (runs the node itself) before ruling. Request body =
   node id + one-line claim + log path in refs; a verdict without the servicer's own run is void.
2. **REMOVE needs a home** → its fate must be `carried-by <pin id>` or `retired-with drop-list row #N`; neither ⇒ a FORK
   to the sidecar BEFORE the edit. REFUSE = a product red, back to the builder; the servicer never touches production.
3. **Shared tree** → the servicer COMMITS ONLY TEST PATHS itself (explicit-path commits; amends R23's "lead commits"
   so the commit is the artifact the builder can watch). Its receipts carry TREE= and run only the targeted nodes; the
   builder holds commits while a servicing run it was told of is in flight. The AUTHORITATIVE both-ways diff (R22
   rider 1) is computed ONCE at the cold audit over the whole packet: pre-build test tree × final production → R1;
   final test tree × final production → R2. Per-request receipts are attribution, not the gate.
4. **A waiting builder reads as done/stalled** → never block on one request; continue other items and drain at
   boundaries. When blocked only on servicing, arm a `Bash(run_in_background)` watcher on the servicer's ARTIFACT (a
   commit touching the requested file) — never inbox polls or repeated await turns. Proof of service is the commit.
5. **The servicer's idle is benign** → spawned with the `{"artifact": null}` idle-gate contract, registered on lore_comms
   with a cadence, draining at EVERY turn boundary; its state lives in am-37 rows + commits, so a context-full respawn
   (suffixed name) loses nothing.
6. **Interim reds while a request is open** → accepting a request registers the node under F6 `red_nodeids` (owner:
   servicer; trigger: the ruling commit); self-destruct clears it on green.

## R25 — budget +1 more of each (operator, 2026-11-08)
Operator, verbatim: *"Because my changes missed the last round, add another round of each to the allowance."* Rulings
R17–R24 landed after contract round 6 was briefed. Budget now: contract rounds 7 AND 8, adversary rounds 4 AND 5, each
only if needed; then BUILD (R16) under R23/R24 (builder never edits tests; a standing contract author services them).

## R26 — design sidecar ruling 5: round-6 forks (design-sidecar-66 on ecae572; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-5.md`.
1. **FORK-R6-1 CONFIRMED (A): `TransactionConflict` is a fourth fate, RETRIED.** No served surface names it: a conflict
   resolves (value served) or exhausts into `TxnContentionExhaustedError` (proven-no-key). Filing it "unknown" (B)
   would be a false bound. The fate list is now **created / proven-no-key / unknown / retried** (derived from R11 and
   drop-list #2). Mirror it into am-37 §15 at the operator's next pass. Riders, all for contract round 7:
   (a) **FALSE PROSE.** q1b's comment ("SDK 3.0 adds ErrorKind.TRANSACTION_CONFLICT") and §R6.2 ("top level or as a
   Query detail") are both wrong. The lead verified on the installed 3.0.0: the value exists ONLY in `QueryDetailKind`
   (`surrealdb/errors.py`, `QueryDetailKind.TRANSACTION_CONFLICT`); `ErrorKind` lacks it. Fix both sentences.
   (b) **Disjointness pin in q1c:** `_SDK_TOP_KINDS & _SDK_DETAIL_KINDS` must be empty. Otherwise a future top-level
   kind would leave that door untested while the table reads as covering it.
   (c) q1b's proven/unknown failure text gains the third word, "retried".
2. **FORK-R6-2 CONFIRMED (A): no SDK-version branching.** The ruling-table and a19 refusal pins go RED at HEAD as
   declared pins. A version-branched pin asserts two worlds under one name. The a19 pins are served-surface pins, and
   branching them would bless `str(RecordID)` on SDK 2.0, which R7(d) forbids. Rider (R22-3/R24-6): register the
   declared RED@HEAD set under F6 `red_nodeids` and put the count in the round-7 receipt.
3. **Helper (b): SPLIT.** `digit_led_record_key` moves to `sdk3_shape_fakes`, which is pure and I/O-free;
   `rekey_principal` stays in `_governed_contract`, because it runs admin DML. **(c): YES.** In
   `credentialed_app_context(digit_led_principals=)`, change the default to True in ONE line, never a sweep:
   28% of production principals are digit-led and every ULID is. Discrimination rider: served-id pins keep their
   letter-led and non-word legs, and any digit-led-only pin gains one letter-led leg.
4. **B-1: no new pin.** `_RULED_PROVEN_NO_KEY` together with
   `test_a_fault_during_the_CREATE_call[TxnRowCapExceededError]` already turns a build that omits the class RED.
   **B-2: ONE store-free pin, in round 7.** Feed the `_id_sample` and `_owned_unscoped_part` renderers a digit-led
   RecordID and a non-word one. The served text is the bare key or the engine form, with no ⟨⟩ or backtick. a19's
   live leg stays as the witness. A bare key is acceptable only where the sentence names its table; a sentence that
   mixes tables serves `record_text`.
5. **Stale for round 7:** MP-B's slept==drawn pins and the §R6.8 draw-count note are superseded by R18/R20 (a sleep
   seam with no draws). The §R6.5 citation `final2_*` becomes `final3_*`.

## R27 — design sidecar ruling 6: round-7 forks (design-sidecar-66 on daccccf+150b85b; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-6.md`.
1. **R7-1 CONFIRMED.** Harness `run()` returns the first statement's result and fails closed on a non-list or an empty answer. That is honest only because SDK 3 `query()` RAISES when a later statement fails (measured). The staged patch is the SERVICING author's FIRST commit, made right after the builder's surrealdb==3.0.0 pin commit, so no gate runs on the red interval. The builder's brief names it as its first request.
2. **R7-2: take (a).** The upsert rule is "zero private row-building or SQL in `upsert`". ONE pure chunk-row builder serves both callers: `replace_file_fragment` composes it after its DELETE, and `upsert` composes it alone (one fragment, so no param collision, and the row cap binds). Sharing is proven by mutation: break the row builder ⇒ the upsert pins AND B1 redden. If the engine cannot overwrite in place (R4 rider 1's corpus read + probe), the fallback is (b), grouping per file. A private UPSERT loop is never acceptable. BUILDER work; no contract edits.
3. **R7-3 CONFIRMED.** The seam text carries both halves: the bound is stated as a FACT, because the seam cannot tell the shape. A renderer that knows the shape serves only its half (pinned).
4. **R7-4: F6 is BUILD STEP 0** (the owner was already ruled the builder, §R3.7(c)). Its tests are contract surface (R23), so contract round 8 carries the F6 gate contract:
   - §R3.7(c)'s five semantics, verbatim;
   - `--verify-registry` admits files with red_nodeids only and still refuses an entry with neither symbols nor ids.
   The servicer then registers the DRAFT (sdk3r7 item5), filled from round 7's `declare/` and rounds 3–6. Interim bound: the INDEX Log line of 2026-11-08 together with `receipts/2026-11-08-sdk3/red_at_head_unregistered_29c56751.txt`.
5. **R7-5:** R22's removed-test inventory lives in the PACKET DOC (§R7.2, plus a cumulative section at close-out) and is named in the cold-audit brief. It does not go in the test-side am-37 class tables. The am-37 §15 mirror covers R26-1's fate row only.
6. **R7-6:** the A4 site set is a hidden constant, accepted as BOUNDED: 2 sites, written down, trigger packet 68. Stated escape: the empty-allowlist perimeter does NOT catch a direct `wait_exponential_jitter`/`wait_fixed` construction. Packet 68's instrument is a RUNTIME reach check: wrap `tenacity.BaseRetrying.__init__` in the targeted run; every wait observed under loremaster/loresigil frames must be factory-made, and the observed count must be ≥ the derived floor.
7. **(a) Q7 is acceptable as adjudicated-BY-INSTRUMENT** (q7_trace counts the calls). Riders for round 8: re-run on the final tree (batch 2's receipt is void, because it ran before item 4d), and add a RAISING mutation of `bare_record_key` for the five silent files (errors ⇒ shared; green ⇒ attach a per-hit sweep list).
   **(b)** ⊆ is acceptable for the DERIVED 360-candidate F-a closure only. R19's "=" binds the 33 declared pins, and that held. The receipt keeps the two separate.
   **(c) NOT a concern.** It is a pristine-baseline artefact: `lore.yaml` is gitignored, so it is absent from a git-archive tree. Method rider: copy `lore.yaml` into every pristine baseline, or have the diff script verify every pristine failure that cites `lore.yaml`.
   **(d)** fold `_FactoryMutation` into `_driver_sleeps` in round 8, after adversary 3.
Sequence: adversary round 3 grades round 7 now. Round 8 then carries: the F6 gate contract, the Q7 re-run plus the raising leg, the (d) fold, the cumulative inventory, and adversary 3's findings. The builder carries R7-2(a), F6 as step 0, and R7-1 as servicing commit 1.

## R28 — adversary round 3: INSUFFICIENT, one missing pin; round 8 routed (lead, 2026-11-08)
Full report: `docs/plans/v2/receipts/2026-11-08-sdk3/ADVERSARY3.md` (graded 150b85b, TREE 29c56751…).
- **Replays:** 17 of 18 round-1/round-2 wrong builds are KILLED. They include `wb_f18_abort` (MP-A closed) and `wb_r11_sleepdrift`, which R20-A3's distribution pin kills. `x18_double` still survives (idempotent close, NO ROUND).
- **Satisfiability spot-check HOLDS.**
- **MP-1 → contract round 8:** B3 refused-file naming (R4 rider 3 + R17) is pinned for the realtime sweep only; a batch-arm build that drops the bound passes. Fix: parametrise over the sweep shape, pair-proven per arm. A REPEAT CLASS of round-2 MP-A ("both sweep shapes"). Builder chokepoint: ONE helper for the two cloned `except SurrealStoreError` arms.
- **Residual R18 → round 8:** B-2 lacks a letter-led leg, so R26-3's rider is unmet.
- **Landmine 1, "tenacity in name only" (R18's operator concern), is BEHAVIOURALLY INVISIBLE:** a hand-rolled loop with the same laws passes 738/738. The adversary proved a one-line runtime instrument (narrow `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES` to `{"tenacity.asyncio"}`) and a fallback named cold-audit diff check. Neither reaches scout's ladder except the audit check. Round 8 STAGES the narrowing as a patch and writes the audit check. **Whether the narrowing lands is the OPERATOR's decision**; the sidecar is asked to classify it (ruling request 7).
- **Residuals R1–R17:** builder notes, recorded by round 8 in the packet doc; none reopens a round. The four packet-58 files reading `TXN_STATEMENT_HARD_CAP` are registered under packet-58's contract (lead-checked). **CORRECTED 2026-11-08 (lead):** true for the PYTEST leg only. The registry carries no typecheck allowance for these reads, so they surfaced as 16 attr-defined RED_ORPHANED errors in 5 packet-58 files after F12 deleted the constant. Routed as a cross-packet fork to sidecar RULING-12 (servicer proposal: lore_comms #19013).

## R29 — design sidecar ruling 7: the landmine-1 instrument is NOT reserved; ADOPT it with riders (design-sidecar-66; recorded by the lead; the operator may overturn)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-7.md`.
- **Classification.** Narrowing `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES` to `{"tenacity.asyncio"}` is a one-constant refinement of an EXISTING per-test runtime instrument. It reads no source and is not run-wide, so it is outside the operator-reserved class (source scanners; run-wide recorders and meta-suites).
  - It pins a mechanism the OPERATOR ruled: R11 *"if our retry is hand rolled use tenacity"*, and R18, from the operator's own question.
  - Of the three instruments that could pin it, runtime attribution is the one the instrument lesson prescribes. Pair-proven: 26 red on the hand loop, 0 over-fire.
- **ADOPT A**, landing WITH the build as a staged servicing patch. Riders:
  1. the threat model goes in the module docstring (honest developer; defeated by private `_portable_async_sleep`; reach = tenacity's default sleep);
  2. HEAD's reddened pins go into the F6 red_nodeids entry;
  3. REWRITE `NO_DRIVER_SLEEP_HINT` so it teaches "port it, never widen this set";
  4. close the scout sibling the same way, by attributing scout's injected `sleep=` caller to `tenacity.asyncio`, pair-proven.
- **Keep B,** the cold audit's named diff check, beside A. B alone would be "documented ≠ dealt with".
- **MP-1 routing CONFIRMED:** a round-8 pin over both sweep arms, plus the builder's ONE helper behind the two cloned except-arms. The same parametrisation covers the embed-failure arm. The B-2 letter-led leg goes into round 8.
- **Operator flag:** recorded for the operator's wake as OVERTURNABLE, never blocking. Routed into round 8 via WORKORDER-r8 Amendment 1.

## R30 — design sidecar ruling 8: `red_nodeids` sits on the FILE entry (design-sidecar-66; recorded by the lead)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-8.md`.
- **FORK-R8-1 CONFIRMED, per file:**
  - A PendingBound groups files that share one owner and one trigger. A PendingFile carries the claims about one file (`missing_symbols`, `unsymboled_codes`), and a node id is a third claim kind about one file.
  - On the bound, a pytest-only file would need either a claim-less PendingFile (which is refused) or no entry at all (and then `files:` would misstate the bound's coverage).
  - §R3.7(c)'s "on the bound" predates reading the schema.
  - **Rider (servicing author, in the commit that registers `packet66_entry.yaml` after F6 lands):** `--verify-registry` refuses an id whose path prefix names a DIFFERENT file than its entry. That is one validator line and one test. No new round.
- **FORK-R8-2:** the F6 contract in `scripts/` is GRANTED (agreed). It must stay in testpaths.
- **Round-8 D1:** a declaration error, not a weak pin. Record it as declared 2, observed 1; cause: the declaration; the owner leg is proven by `b2_owner`. Re-running with the corrected set would transcribe the declaration from the output, which is the tautology `mutation_proof.py` forbids.

## R31 — sidecar ruling 9 on adversary round 4's F6 findings; build sequencing (sidecar-66 ruling + lead sequencing)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-9.md`. Adversary report: `receipts/2026-11-08-sdk3/ADVERSARY4.md`. The verdict was INSUFFICIENT, with every finding in the F6 gate contract and 0 unsatisfiable pins. The product side (retry, index, record-id) held against every build.
- **MP-F6-4, reading (b), ruled within the sidecar's delegation:** a listed id is STALE only when its FILE was collected in this run and the id was not.
  - Reading (a) makes every scoped `wave_gate --wave` fail fleet-wide once the 302-id entry registers.
  - A deleted file is still caught by the typecheck leg's file-exists self-destruct, which runs full in wave mode. The residual case (file present but excluded, id renamed) is caught by the next full run, inside the one-wave orphan window currency already accepts. State this in the pin.
  - Leg 1: the stale line says "not collected in this run's <file>".
  - The reference implements (a) and is a REFERENCE BUG; a scope-aware variant passes 479/479.
- **MP-F6-1..3 CONFIRMED** as false clears on a SERVED gate verdict (R17), not hygiene. **The builder's requirement is the adversary's CLASS, verbatim:** the adjudication of a listed id depends ONLY on (the exact id) × (did the run collect its file) × (did it fail). It never depends on other outcomes in the run, other claims on the entry, or the id's ancestors.
  - Chokepoints: `pytest_self_destruct_findings` iterates the REGISTRY; matching is exact set membership in both the partition and the stale test; the typecheck self-destruct still applies to an entry's mypy claims when `red_nodeids` is present.
  - **Rider:** a listed id that is COLLECTED but SKIPPED or xfail adjudicates NEITHER way. Its registration is kept, and the render says so.
- **Routing (i), converting adversary 4's probes into F6 pins before the F6 code, plus adversary round 5 on that delta, is a contract round in substance. That is the OPERATOR's call under R25,** and it is flagged for the operator's wake with the sidecar's recommendation to GRANT. Route (ii), named residuals (R16), is in-grant.
- **Lead sequencing, until the operator rules:** BUILD starts now (operator: *"then go to build"*), with the F6 gate CODE moved to the END of the build order instead of step 0, so that no F6 code is written before its pins exist if (i) is granted.
  - **The 302-id entry does not register until the F6 pins exist or the operator rules (ii).** Registration is the step that touches the fleet.
  - The interim INDEX bound (2026-11-08) stays in force until then.
  - The builder brief carries (b), the class and the skip rider as NAMED requirements, and the probe file (`ADVERSARY4.md` §INSTRUMENTS) as the cold audit's instrument.

## R32 — F6 probes become pins before the F6 code: route (i) GRANTED (operator, 2026-11-08)
Operator, verbatim: *"You may run a contract author."* This answers R31's routing question in favour of (i).
- The standing contract author (`contract-sdk3-r7`, the F6 contract's own author and the R23 servicer) converts adversary 4's §INSTRUMENTS probes into F6 pins: MP-F6-1..3, the MP-F6-4 reading-(b) pin, and R31's skip/xfail rider.
- The pins are declared RED@HEAD, pair-proven against a reference F6 fixed to reading (b), and committed by explicit path, separate from the build.
- **Adversary round 5** (in budget, R25) then grades that delta. The builder writes no F6 code until both have happened; the channel is `build66/OPERATOR-F6.md`.
- The 302-id registration still follows F6 (R31).

## R33 — R29's landmine-1 narrowing is KEPT (operator, 2026-11-08)
The operator was asked whether to overturn R29 (sidecar RULING-7) and chose **keep**. The runtime check stands as committed in `d78baa3`: `_driver_sleeps.DRIVER_SLEEP_CALLER_MODULES` is narrowed to `{"tenacity.asyncio"}`, and scout's `sleep=` caller attribution stays with it. The cold audit's diff check B ("no loop around the attempt; `AsyncRetrying` IS the loop") stays beside it, and each covers the other's blind spot.

## R34 — FORK-B1: one shared required-datetime validator (sidecar ruling 11; adopted by the lead under the standing fork delegation)
Full text: `docs/plans/v2/receipts/2026-11-08-sdk3-sidecar/RULING-11.md`.
- **Reading B.** ONE shared validator pair in `_txn` that checks and never converts. R6 S2 forbade a seventh COERCER, not the required-column guard that the SDK's decoder cannot supply. Reading A would mint EIGHT clones, because `keeps` and `principal_keys` read stamps too.
- **Found defect, a builder work order (lore_comms #19029):** `memory/local._row_datetime` is still a private copy and has already DIVERGED, because it has no tz-aware check. Route it through the helper. `_parse_iso` is not a sibling (it parses ledger JSON); label it so in its docstring.
- **The refusal is a SERVED surface:** it names the ROW id in engine text, never `str(RecordID)`, and calls itself a store-integrity fault to report, with other rows unaffected. It must not read as a caller error.
- **Pin it like this:** a servicing request for the ∀-module naive / missing / string pins, with reach derived by grep (one declared red per caller module); the shared-helper mutation is run at the cold audit; a DRY-ledger row for the helper pair. (The repo has no helper registry; the builder's DRY ledger is the record.)

## R35 — adversary round 5: F6 delta INSUFFICIENT (0 unsatisfiable); pins plus a round-5 re-grade GRANTED (operator, 2026-11-08)
Report: `docs/plans/v2/receipts/2026-11-08-sdk3/ADVERSARY5.md` (graded `c01b114`). The reference passes 488/488, and HEAD is red on exactly the 29 F6 nodes for the right reason. 17 of 20 wrong gates were killed, including all of adversary 4's builds and the round-8 reference. Survivors and gaps:
- **MP5-1:** a mixed-claim entry is exempt from the pytest self-destruct, so a stale id renders as live. This is an R17 false clear, a repeat of R31's class ("other claims on the entry").
- **MP5-2:** the KEPT note is missing on a GREEN verdict and in `wave_gate`'s render.
- **MP5-3:** self-destruct reaches only the first 3 ids of an entry.
- **MP5-4:** a module skip, an importorskip or a collection error reads as "file collected", so every listed id in that file is falsely STALE.
The operator granted the route: the servicer pins MP5-1..4, pair-proven against the reference, and the same adversary (`adversary-sdk3-r5`, context loaded) re-grades ONLY that delta (survivors N8/N9/N12 plus the MP5-4 probe). This is one extra round beyond R25, granted by the operator. The builder writes no F6 code until it is SATISFIED (`build66/OPERATOR-F6.md`). **D2** (reading (b)'s granularity under a node-id `--wave <file>::<Class>`, servicer residual 1) goes to the design sidecar.
