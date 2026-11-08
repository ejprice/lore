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
